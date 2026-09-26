extends MapBuilder
## MAP 2 — Ruined Forest, "Where the village fell" (outdoor, levels 1–5).
##
## West → east along one winding road: the arrival waypoint glade (and the shattered old waypoint nobody repaired),
## the burnt village with its graveyard and chapel ruin, a stone bridge over a misty ravine, a survivors' camp whose
## fire is still warm, the collapsed watchtower on its hill (the landmark seen from the bridge), and a corrupted
## grove around a violet-veined obelisk that marks the sunken gate to the Ancient Catacombs.
## The playable area is framed by rising ground, cliffs and dense pines — never by invisible walls on flat grass.

const W := 160
const D := 110
const ROAD := [Vector2(-66, 12), Vector2(-50, 9), Vector2(-34, 6), Vector2(-18, 5), Vector2(-7.5, 4), Vector2(7.5, 4),
	Vector2(18, 0), Vector2(30, -4), Vector2(44, -4), Vector2(57, -3), Vector2(66, -4)]
const TOWER_PATH := [Vector2(24, -2), Vector2(27, 8), Vector2(30, 17)]
const CAMP_PATH := [Vector2(20, -1), Vector2(20, -10)]
const BRIDGE_Z := 4.0
const TOWER := Vector3(31, 0, 24)
const CAMP := Vector3(20, 0, -15)
const GATE := Vector3(68, 0, -4)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.02, 0.04, 0.07), "sky_horizon": Color(0.1, 0.14, 0.18),
		"ambient": Color(0.28, 0.34, 0.42), "ambient_energy": 0.8,
		"fog": Color(0.13, 0.17, 0.2), "fog_density": 0.01, "fog_height": -2.0, "fog_height_density": 0.1,
		"sun": Color(0.55, 0.68, 0.9), "sun_energy": 0.55, "sun_rot": Vector3(-42, 55, 0), "glow": 0.8,
		"exposure": 1.1, "contrast": 1.08, "saturation": 0.88,
	})
	terrain(Vector2i(W, D), Vector3.ZERO, _height, _splat, {"grass": "grass", "moss": "forest_floor", "dirt": "mud",
		"path": "sand_path", "rock": "rock_cliff"}, Color(0.9, 0.95, 0.9))
	_edges()
	_arrival()
	_village()
	_ravine()
	_camp()
	_tower()
	_grove_and_gate()
	_forest()
	set_bounds(AABB(Vector3(-72, -8, -48), Vector3(144, 20, 96)))
	view("overview", Vector3(0, 0, 0), 0.0, 70.0, 150.0, 50.0)
	view("arrival", Vector3(-60, 0, 10), 0.0, 48.0, 26.0)
	view("village", Vector3(-30, 0, 6), 0.0, 50.0, 34.0)
	view("bridge", Vector3(0, 0, 4), 0.0, 44.0, 30.0)
	view("camp", CAMP + Vector3(0, 0, 2), 0.0, 48.0, 22.0)
	view("tower", TOWER + Vector3(0, 3, -4), 0.0, 42.0, 34.0)
	view("gate", GATE + Vector3(-8, 0, 0), 0.0, 45.0, 28.0)

# ------------------------------------------------------------------------------------------------------------
# terrain

static func _seg_dist(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return p.distance_to(a + ab * t)

static func _poly_dist(p: Vector2, pts: Array) -> float:
	var d := INF
	for i in pts.size() - 1:
		d = minf(d, _seg_dist(p, pts[i], pts[i + 1]))
	return d

func _ravine_x(z: float) -> float:
	return 1.2 * sin(z * 0.07)

func _base(x: float, z: float) -> float:
	var h := sin(x * 0.055) * cos(z * 0.07) * 1.6 + sin(x * 0.13 + z * 0.09) * 0.6 + cos(z * 0.21 - x * 0.05) * 0.35
	# tower hill
	h += 4.5 * (1.0 - smoothstep(6.0, 20.0, Vector2(x - TOWER.x, z - TOWER.z).length()))
	# the grove sinks into a hollow around the gate hillside, which rises behind it
	h += 8.0 * smoothstep(68.5, 72.0, x)
	# rising rims on every edge (natural bounds)
	var ex := smoothstep(W * 0.5 - 16.0, W * 0.5 - 2.0, absf(x))
	var ez := smoothstep(D * 0.5 - 14.0, D * 0.5 - 2.0, absf(z))
	h += maxf(ex, ez) * 12.0
	return h

func _height(x: float, z: float) -> float:
	var p := Vector2(x, z)
	var h := _base(x, z)
	# flatten the road into a gently graded bed
	var rd := minf(_poly_dist(p, ROAD), minf(_poly_dist(p, TOWER_PATH), _poly_dist(p, CAMP_PATH)))
	var road_h := _base(x, z) * 0.35
	h = lerpf(road_h, h, smoothstep(2.0, 6.0, rd))
	# flat clearings
	for c in [[Vector2(-60, 11), 10.0], [Vector2(-30, 8), 17.0], [Vector2(CAMP.x, CAMP.z), 9.0], [Vector2(GATE.x - 8, GATE.z), 9.0]]:
		var k := 1.0 - smoothstep(float(c[1]) * 0.6, float(c[1]), p.distance_to(c[0]))
		h = lerpf(h, road_h, k)
	# the ravine
	var rv := absf(x - _ravine_x(z))
	h -= 7.5 * (1.0 - smoothstep(2.5, 7.0, rv))
	# keep the bridge approaches level with the deck
	if absf(z - BRIDGE_Z) < 4.0 and absf(x) < 12.0:
		h = lerpf(h, 0.0, (1.0 - smoothstep(2.5, 4.0, absf(z - BRIDGE_Z))) * smoothstep(5.0, 6.0, absf(x)))
	return h

func _splat(x: float, z: float) -> Color:
	var p := Vector2(x, z)
	var rd := _poly_dist(p, ROAD)
	var side := minf(_poly_dist(p, TOWER_PATH), _poly_dist(p, CAMP_PATH))
	var path := 1.0 - smoothstep(1.6, 3.2, rd)
	path = maxf(path, (1.0 - smoothstep(1.0, 2.2, side)) * 0.8)
	var n := sin(x * 0.31 + z * 0.17) * 0.5 + 0.5
	var village := 1.0 - smoothstep(10.0, 18.0, p.distance_to(Vector2(-30, 8)))
	var forest := clampf(0.55 + n * 0.45 - village * 0.4, 0.0, 1.0)
	var mud := clampf(village * 0.6 + (1.0 - smoothstep(4.0, 8.0, absf(x - _ravine_x(z)))) * 0.8, 0.0, 1.0)
	return Color(clampf(maxf(mud, path * 0.3), 0, 1), forest * (1.0 - path), path)

# ------------------------------------------------------------------------------------------------------------
func _edges() -> void:
	# cliffs along the north and south rims and the east hillside; boundary just inside them
	for i in 14:
		var x := -70.0 + i * 11.0 + rng.randf_range(-2, 2)
		decor("cliff_b" if i % 2 else "cliff_a", Vector3(x, _base(x, -50) - 7.0, -51.0), 180.0 + rng.randf_range(-15, 15), 1.5, false, true)
		decor("cliff_a" if i % 2 else "cliff_b", Vector3(x, _base(x, 50) - 7.0, 51.0), rng.randf_range(-15, 15), 1.5, false, true)
	for i in 8:
		var z := -44.0 + i * 12.0
		decor("cliff_b", Vector3(77.0, _base(76, z) - 8.0, z), 90.0 + rng.randf_range(-10, 10), 1.6, false, true)
		decor("cliff_a", Vector3(-77.0, _base(-76, z) - 7.0, z), -90.0 + rng.randf_range(-10, 10), 1.5, false, true)
	var bx := W * 0.5 - 8.0
	var bz := D * 0.5 - 8.0
	boundary(Vector3(-bx, 0, -bz), Vector3(bx, 0, -bz), 30.0)
	boundary(Vector3(-bx, 0, bz), Vector3(bx, 0, bz), 30.0)
	boundary(Vector3(-bx, 0, -bz), Vector3(-bx, 0, bz), 30.0)
	boundary(Vector3(bx, 0, -bz), Vector3(bx, 0, bz), 30.0)

func _arrival() -> void:
	var c := Vector3(-62, 0, 12)
	teleporter(&"forest_waypoint", c + Vector3(0, ground(c.x, c.z), 0), &"sanctuary", &"waypoint", "Hero Sanctuary")
	spawn(&"arrival", Vector3(-58.0, 0, 12.4), 90.0, true)
	spawn(&"start", Vector3(-58.0, 0, 12.4), 90.0, true)
	for a in [0.4, 1.9, 3.6, 5.0]:
		decor("rock_medium", c + Vector3(cos(a) * 6.5, 0, sin(a) * 6.0), rng.randf() * 360.0, rng.randf_range(0.7, 1.0), true, true)
	kit("lamp_post", c + Vector3(3.5, 0, 3.6), 0.0, 1.0, props, true)
	light(c + Vector3(4.05, 2.8 + ground(c.x + 4, c.z + 3.6), 3.6), Color(1.0, 0.7, 0.4), 2.6, 10.0, false, true)
	# the old waypoint — shattered, rune-dead, corruption creeping from the cracks
	var old := Vector3(-49, 0, -13)
	kit("teleporter_destroyed", old, 25.0, 1.0, props, true)
	light(old + Vector3(0, 1.2 + ground(old.x, old.z), 0), Color(0.6, 0.2, 1.0), 1.6, 7.0, false, true)
	decor("bones_scatter", old + Vector3(3.5, 0, 2.0), 30.0)
	decor("weapons_discarded", old + Vector3(-3.0, 0, 3.0), 110.0)
	enemy_zone("old_waypoint", old, 6.0, [&"dire_wolf"], 3, 0.0, true)

func _village() -> void:
	var houses := [[Vector3(-38, 0, -4), 15.0], [Vector3(-22, 0, -6), -10.0], [Vector3(-40, 0, 20), 170.0], [Vector3(-20, 0, 19), 195.0]]
	for h in houses:
		kit("house_destroyed", h[0], h[1], 1.0, props, true)
	# the road through the village: wreckage, dead defenders, a banner still standing
	kit("wagon_broken", Vector3(-29, 0, 9.5), 70.0, 1.0, props, true)
	decor("weapons_discarded", Vector3(-27, 0, 3.0), 10.0)
	decor("weapons_discarded", Vector3(-33.5, 0, 12.0), 200.0)
	for p in [Vector3(-31, 0, 4.5), Vector3(-24.5, 0, 11.5), Vector3(-36, 0, 8.0)]:
		decor("bones_scatter", p, rng.randf() * 360.0)
	for x in [-35.0, -25.0]:
		var pole := Vector3(x, 0, 1.4)
		kit("wood_fence", pole, 0.0, 1.0, props, true)
	var bp := Vector3(-30.0, 0, 0.5)
	kit("lamp_post", bp, 0.0, 1.0, props, true)  # unlit; a banner hangs from its arm
	kit("banner_torn", bp + Vector3(0.55, 3.0 + ground(bp.x, bp.z), 0), 0.0, 0.6, deco)
	kit("well", Vector3(-28, 0, 16), 30.0, 1.0, props, true)
	kit("cart_hay", Vector3(-17, 0, 10.5), -30.0, 1.0, props, true)
	for p in [Vector3(-35.5, 0, -8.5), Vector3(-34.2, 0, -9.3), Vector3(-19.4, 0, 13.4), Vector3(-43.5, 0, 16.0)]:
		breakable("barrel" if rng.randf() < 0.5 else "crate", p, rng.randf() * 360.0, 20.0, true)
	for i in 5:
		kit("wood_fence", Vector3(-46.0 + i * 4.2, 0, 26.5), rng.randf_range(-8, 8), 1.0, props, true)
	# graveyard and chapel ruin south-west of the village
	var g := Vector3(-48, 0, 28)
	for i in 9:
		var p := g + Vector3((i % 3) * 3.2 + rng.randf_range(-0.4, 0.4), 0, (i / 3) * 3.0 + rng.randf_range(-0.3, 0.3))
		kit("gravestone_a" if rng.randf() < 0.55 else "gravestone_b", p, rng.randf_range(-15, 15), 1.0, props, true)
	for i in 3:
		kit("wall_broken", g + Vector3(-5.0, 0, -1.0 + i * 4.0), 90.0, 1.0, geo, true)
	kit("statue_collapsed", g + Vector3(10.0, 0, 5.0), 200.0, 1.0, props, true)
	candles(g + Vector3(3.2, ground(g.x + 3.2, g.z + 3.0), 3.0), 1.4)
	# embers still smouldering in the largest ruin
	var ember := Vector3(-38, 0, -4)
	light(ember + Vector3(0, 1.2 + ground(ember.x, ember.z), 0), Color(1.0, 0.4, 0.15), 1.5, 8.0, true, true)
	flame(ember + Vector3(0.8, 0.3 + ground(ember.x, ember.z), 0.5), 0.9)
	var smoke := VFXLib.particles(Color(0.25, 0.25, 0.27, 0.22), 14, 4.0, false, 1.6, 0.7, 12.0, Vector3(0.3, 0.7, 0), 1.0, false)
	smoke.position = ember + Vector3(0, 1.5 + ground(ember.x, ember.z), 0)
	deco.add_child(smoke)
	# more wreckage: rubble from the collapsed walls, a toppled tree across the lane, abandoned loads
	for p in [Vector3(-33, 0, -1.5), Vector3(-17.5, 0, -2.0), Vector3(-43.5, 0, 22.0), Vector3(-24.0, 0, 23.5)]:
		decor("rubble_pile", p, rng.randf() * 360.0, rng.randf_range(0.8, 1.2), true, true)
	kit("log_fallen", Vector3(-45.0, 0, 3.0), 75.0, 1.0, props, true)
	kit("tree_dead_b", Vector3(-46.5, 0, -2.0), 30.0, 1.0, props, true)
	kit("cart_hay", Vector3(-41.0, 0, 11.0), 120.0, 1.0, props, true)
	for p in [Vector3(-26.0, 0, 13.4), Vector3(-25.2, 0, 14.2), Vector3(-37.5, 0, 14.0)]:
		breakable("crate", p, rng.randf() * 90.0, 20.0, true)
	decor("skull_pile", Vector3(-22.5, 0, 1.5), 40.0, 0.7)
	enemy_zone("village_road", Vector3(-30, 0, 7), 9.0, [&"hollow_soldier", &"grave_archer"], 7, 0.0, true)
	enemy_zone("graveyard", g + Vector3(3, 0, 3), 5.0, [&"hollow_soldier", &"bonewarden"], 4, 0.15, true)

func _ravine() -> void:
	arch("bridge_stone", Vector3(0, 0, BRIDGE_Z))
	water(Rect2(-5, -D * 0.5, 10, D), -6.2, Color(0.1, 0.3, 0.34), Color(0.02, 0.06, 0.08), 0.3, 2.0, 0.06)
	mist(Rect2(-8, -D * 0.5, 16, D), -4.6, Color(0.2, 0.26, 0.31), 0.35)
	# rocks tumbling into the ravine and along its lips
	for i in 26:
		var z := -D * 0.5 + 6.0 + i * 3.8 + rng.randf_range(-1, 1)
		if absf(z - BRIDGE_Z) < 4.5:
			continue
		var sgn := -1.0 if i % 2 else 1.0
		var x := _ravine_x(z) + sgn * rng.randf_range(4.0, 6.5)
		decor("rock_large" if i % 3 == 0 else "rock_medium", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.7, 1.2), true, true, 15.0)
	# guard rails: the ravine lips are sheer; keep the player on the bridge crossing
	for sgn in [-1.0, 1.0]:
		boundary(Vector3(sgn * 7.2, 0, -D * 0.5 + 8.0), Vector3(sgn * 7.2, 0, BRIDGE_Z - 2.4), 6.0, 0.6)
		boundary(Vector3(sgn * 7.2, 0, BRIDGE_Z + 2.4), Vector3(sgn * 7.2, 0, D * 0.5 - 8.0), 6.0, 0.6)
	for sx in [-8.2, 8.2]:
		for dz in [-2.6, 2.6]:
			kit("pillar_broken" if sx > 0 and dz > 0 else "pillar", Vector3(sx, 0, BRIDGE_Z + dz), 0.0, 0.55, geo, true)
	torch_post(Vector3(-8.2, 0, BRIDGE_Z - 2.6))
	enemy_zone("bridge", Vector3(0, 0, BRIDGE_Z), 4.0, [&"bonewarden", &"grave_archer"], 3, 0.6)

## A fire bowl burning on top of a pillar (outdoor spots without walls to hang torches on).
func torch_post(p: Vector3) -> void:
	var y := ground(p.x, p.z) + 2.3
	flame(Vector3(p.x, y + 0.2, p.z), 1.0)
	light(Vector3(p.x, y + 0.6, p.z), FIRE, 2.8, 10.0, false, true)

func _camp() -> void:
	campfire(CAMP)
	kit("tent_old", CAMP + Vector3(-4.5, 0, -3.5), 25.0, 1.0, props, true)
	kit("tent_old", CAMP + Vector3(4.2, 0, -4.2), -35.0, 1.0, props, true)
	for p in [[Vector3(-2.2, 0, 1.8), 70.0], [Vector3(2.4, 0, 2.2), -60.0]]:
		kit("bedroll", CAMP + p[0], p[1], 1.0, deco, true)
	kit("log_fallen", CAMP + Vector3(0.5, 0, -2.6), 5.0, 0.5, props, true)
	kit("stump", CAMP + Vector3(2.4, 0, -0.2), 0.0, 0.35, props, true)
	kit("weapon_rack", CAMP + Vector3(6.5, 0, 0.5), -80.0, 1.0, props, true)
	kit("chest", CAMP + Vector3(-6.2, 0, 1.0), 60.0, 1.0, props, true)
	for p in [Vector3(-7.0, 0, -1.2), Vector3(7.2, 0, -2.8), Vector3(6.4, 0, -3.8)]:
		breakable("crate" if rng.randf() < 0.5 else "barrel", CAMP + p, rng.randf() * 360.0, 20.0, true)
	decor("bones_scatter", CAMP + Vector3(5.5, 0, 4.5), 60.0)
	enemy_zone("camp", CAMP, 7.0, [&"bandit_cutthroat", &"bandit_marksman", &"bandit_cutthroat"], 6, 0.25, true)

func _tower() -> void:
	kit("ruin_tower", TOWER, 20.0, 1.0, geo, true)
	var y := ground(TOWER.x, TOWER.z)
	light(TOWER + Vector3(0, y + 3.0, 0), Color(1.0, 0.55, 0.25), 2.0, 10.0, true, true)
	flame(TOWER + Vector3(0.5, y + 0.3, 0.8), 1.4)
	for i in 4:
		var a := TAU * i / 4.0 + 0.6
		decor("rubble_pile", TOWER + Vector3(cos(a) * 9.0, 0, sin(a) * 8.0), rng.randf() * 360.0, rng.randf_range(0.8, 1.2), true, true)
	decor("skull_pile", TOWER + Vector3(-2.0, 0, 1.5), 0.0, 0.9)
	kit("banner_torn", TOWER + Vector3(-1.0, y + 9.6, 3.4), 20.0, 1.0, deco)
	enemy_zone("tower", TOWER + Vector3(0, 0, -7), 7.0, [&"grave_archer", &"ashen_cultist"], 5, 0.3, true)

func _grove_and_gate() -> void:
	var ob := Vector3(52, 0, 6)
	kit("obelisk_corrupted", ob, 15.0, 1.0, props, true)
	light(ob + Vector3(0, 2.8 + ground(ob.x, ob.z), 0), Color(0.62, 0.22, 1.0), 3.6, 14.0, true, true)
	for i in 6:
		var a := TAU * i / 6.0 + 0.2
		kit("tree_dead_a" if i % 2 else "tree_dead_b", ob + Vector3(cos(a) * 9.0, 0, sin(a) * 8.0), rng.randf() * 360.0, rng.randf_range(0.8, 1.1), props, true)
	decor("skull_pile", ob + Vector3(2.5, 0, -2.5), 30.0)
	decor("bones_scatter", ob + Vector3(-3.0, 0, 3.0), 30.0)
	# sunken catacomb gate: an arch set into the hillside, stairs down behind a waypoint dais
	var g := GATE
	var gy := ground(g.x - 8.0, g.z)
	arch("arch_quoin", Vector3(g.x, gy, g.z), 90.0)
	arch("pillar_quoin", Vector3(g.x, gy, g.z - 2.6))
	arch("pillar_quoin", Vector3(g.x, gy, g.z + 2.6))
	for dz in [-6.6, 6.6]:
		arch("wall_stone_capped", Vector3(g.x + 0.2, gy, g.z + dz * 0.8), 90.0)
	kit("gate_iron", Vector3(g.x + 0.3, gy, g.z), 90.0)
	var dark := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(3.6, 3.8)
	dark.mesh = qm
	var dm := StandardMaterial3D.new()
	dm.albedo_color = Color(0.0, 0.0, 0.0)
	dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	dark.material_override = dm
	dark.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(-90)), Vector3(g.x + 0.8, gy + 1.9, g.z))
	deco.add_child(dark)
	for dz in [-9.0, 0.0, 9.0]:
		decor("cliff_b", Vector3(g.x + 6.5, gy - 1.0, g.z + dz), 90.0 + rng.randf_range(-12, 12), 1.25, false, true)
	teleporter(&"catacomb_gate", Vector3(g.x - 6.0, gy, g.z), &"catacombs", &"entrance", "Ancient Catacombs")
	spawn(&"catacomb_gate", Vector3(g.x - 10.0, 0, g.z), -90.0, true)
	kit("statue_collapsed", Vector3(g.x - 4.0, 0, g.z + 8.0), 110.0, 1.0, props, true)
	kit("statue_knight", Vector3(g.x - 3.0, 0, g.z - 7.0), 90.0, 1.0, props, true)
	brazier(Vector3(g.x - 3.2, 0, g.z - 3.4), 3.2, true, true)
	brazier(Vector3(g.x - 3.2, 0, g.z + 3.4), 3.2, false, true)
	for i in 7:
		var p := Vector3(g.x - 18.0 + rng.randf_range(-6, 6), 0, g.z + rng.randf_range(-10, 10))
		cylinder_shard(p)
	enemy_zone("grove", ob, 8.0, [&"shade_stalker", &"ashen_cultist", &"ghoul_brute", &"dire_wolf"], 6, 0.4, true)

## Violet corruption crystals erupting from the ground.
func cylinder_shard(p: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.0
	cm.bottom_radius = rng.randf_range(0.12, 0.22)
	cm.height = rng.randf_range(0.6, 1.4)
	cm.radial_segments = 5
	cm.rings = 1
	mi.mesh = cm
	mi.material_override = MaterialLibrary.env("BH_Corruption")
	mi.transform = Transform3D(Basis.from_euler(Vector3(rng.randf_range(-0.4, 0.4), rng.randf() * TAU, rng.randf_range(-0.4, 0.4))),
		p + Vector3(0, ground(p.x, p.z) + cm.height * 0.35, 0))
	deco.add_child(mi)
	return mi

func _forest() -> void:
	var clear := func(x: float, z: float) -> bool:
		var p := Vector2(x, z)
		if _poly_dist(p, ROAD) < 5.5 or _poly_dist(p, TOWER_PATH) < 3.5 or _poly_dist(p, CAMP_PATH) < 3.5:
			return true
		if absf(x - _ravine_x(z)) < 8.0:
			return true
		for c in [[Vector2(-60, 11), 10.0], [Vector2(-30, 8), 17.0], [Vector2(-48, -13), 7.0], [Vector2(-44, 31), 10.0],
				[Vector2(CAMP.x, CAMP.z), 10.0], [Vector2(TOWER.x, TOWER.z), 11.0], [Vector2(52, 6), 11.0], [Vector2(GATE.x - 6, GATE.z), 11.0]]:
			if p.distance_to(c[0]) < float(c[1]):
				return true
		return absf(x) > W * 0.5 - 6.0 or absf(z) > D * 0.5 - 6.0
	var trees := scatter(["tree_pine", "tree_pine", "tree_oak_twisted", "tree_dead_a", "tree_dead_b"], Rect2(-74, -50, 148, 100),
		190, 4.6, Vector2(0.75, 1.3), clear, true, true)
	# trees near the walkable area get real collision (the rest are background batches)
	for t in trees:
		if _poly_dist(Vector2(t.x, t.z), ROAD) < 16.0 or Vector2(t.x, t.z).distance_to(Vector2(CAMP.x, CAMP.z)) < 16.0 \
				or Vector2(t.x, t.z).distance_to(Vector2(TOWER.x, TOWER.z)) < 16.0:
			blocker(Vector3(t.x, ground(t.x, t.z) + 2.0, t.z), Vector3(0.9, 4.0, 0.9))
	scatter(["bush_a", "bush_b", "fern", "fern"], Rect2(-74, -50, 148, 100), 160, 2.4, Vector2(0.7, 1.2), clear, true, true)
	scatter(["grass_clump"], Rect2(-74, -50, 148, 100), 900, 1.0, Vector2(0.8, 1.4), func(x, z): return absf(x - _ravine_x(z)) < 6.0 or _poly_dist(Vector2(x, z), ROAD) < 2.2)
	scatter(["mushrooms", "roots", "rock_small", "rock_small"], Rect2(-74, -50, 148, 100), 120, 3.0, Vector2(0.7, 1.2), clear, true, true)
	scatter(["log_fallen", "stump", "rock_medium"], Rect2(-74, -50, 148, 100), 40, 6.0, Vector2(0.7, 1.1), clear, false)
