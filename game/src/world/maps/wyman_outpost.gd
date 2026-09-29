extends SettlementBuilder
## MAP — Wyman Outpost, the hero camp on a rise above Reedwater Marsh (bh-007; safe zone, provisional name set by the
## author). The Watch Road comes down from Olivar to its north gate; the Fen Road runs west over the Fen Bridge to
## Lantern Fields (Westreach).
##
## A round stockade around a great bonfire (the checkpoint: rest free, wake here after a fall). Around the fire: the
## heroes' tents with their guild banners, the commander's lodge, the Hero Register board, the quartermaster's stall,
## Greta Stonehand's field forge, a workbench, the healer's camp kettle, a training yard with dummies, a watchtower,
## the waypoint and, on the east side, the Marsh Overlook above the reeds and black water of Reedwater Marsh.

const R := 31.0                          # stockade radius
const BONFIRE := Vector2(-4, -2)
const MARSH_X := 36.0
const MARSH_Y := -1.35
const LODGE := Vector2(-6, -22)
const REGISTER := Vector2(-8, -9.4)
const QUARTER := Vector2(-4, 18.5)
const FORGE := Vector2(16, 11)
const BENCH := Vector2(12, -3.5)
const KETTLE := Vector2(-13, -1)
const YARD := Vector2(-11, 24)
const SHRINE := Vector2(-19.5, 15.5)
const TOWER := Vector2(-20, -20)
const OVERLOOK := Vector2(26, 0)
const TENTS := [Vector2(-19, -11), Vector2(-9, -26), Vector2(13, -21), Vector2(21, -10), Vector2(-24, 3), Vector2(20, 24)]
## Gate crossings on the stockade (angle in degrees, measured with atan2(z, x)).
var _north_gate := 0.0
var _west_gate := 0.0
var _marsh_gate := 0.0              # bh-021: the Marsh Gate to the Weeping Causeway (barred until mq_marsh_gate_open)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.02, 0.035, 0.07), "sky_horizon": Color(0.13, 0.16, 0.22),
		"ambient": Color(0.3, 0.35, 0.44), "ambient_energy": 0.78,
		"fog": Color(0.14, 0.18, 0.22), "fog_density": 0.008, "fog_height": -3.0, "fog_height_density": 0.08,
		"sun": Color(0.55, 0.66, 0.9), "sun_energy": 0.55, "sun_rot": Vector3(-48, -40, 0), "glow": 0.85,
		"exposure": 1.1, "contrast": 1.07, "saturation": 0.9,
	})
	prepare(-95.0, -72.0, 200, 140, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "grass", "moss": "forest_floor", "dirt": "dirt", "path": "cobblestone", "rock": "rock_cliff"}, Color(0.9, 0.94, 0.88))
	_north_gate = _gate_angle(DataIsland.road("wy_north_road").points)
	_west_gate = _gate_angle(DataIsland.road("wy_west_road").points)
	_marsh_gate = _gate_angle(DataIsland.road("wy_marsh_road").points)
	_marsh()
	_stockade()
	_fire_ring()
	_tents()
	_lodge_and_register()
	_trade_row()
	_training_yard()
	_tower_and_overlook()
	_shrine()
	_herbs()
	_wild_camps()
	var og: Dictionary = DataDungeons.get_def(&"orrery").surface
	dungeon_gate(&"orrery", og.pos, og.yaw)
	keep_clear(og.pos.x, og.pos.y, 8.0)
	_greenery()
	spawn(&"start", Vector3(0, 0, 9.0), 180.0, true)
	spawn(&"north_road", Vector3(7.5, 0, -47.0), 0.0, true)
	spawn(&"west_road", Vector3(-51.5, 0, 18.4), 100.0, true)
	set_bounds(AABB(Vector3(-66, -6, -62), Vector3(132, 24, 110)))
	view("overview", Vector3(0, 0, 0), 0.0, 62.0, 100.0, 45.0)
	view("topdown", Vector3(0, 0, -4), 0.0, 89.5, 118.0, 50.0)
	view("bonfire", Vector3(0, 1, -2), 0.0, 48.0, 22.0)
	view("forge", Vector3(4, 1, 20), 0.0, 50.0, 28.0)
	view("row_gate", Vector3(4, 1, 15), 0.0, 40.0, 22.0)
	view("yard", Vector3(-10, 1, 22), 20.0, 48.0, 20.0)
	view("overlook", Vector3(30, 0, 0), -60.0, 35.0, 30.0)

## bh-012: an orc band camped on the Brass path, between the Watch Road and the Orrery gate (the town stays safe).
func _wild_camps() -> void:
	wild_camp("brass_path_orcs", Vector2(-13, -51), 4.0, [&"orc_reaver", &"goblin_skulker", &"goblin_skulker", &"orc_shaman"], 4, Vector2i(4, 6), 0.15)

## Where a road leaving the camp crosses the stockade circle (degrees).
func _gate_angle(pts: Array) -> float:
	var total := DataIsland.polyline_length(pts)
	var along := 0.0
	while along <= total:
		var p := DataIsland.point_at(pts, along)
		if p.length() <= R:
			return rad_to_deg(atan2(p.y, p.x))
		along += 0.25
	return 0.0

# ------------------------------------------------------------------------------------------------------------
# landform

func _noise(x: float, z: float) -> float:
	return sin(x * 0.12) * cos(z * 0.1) * 0.6 + sin(x * 0.051 + z * 0.037) * 0.9

func _landform(x: float, z: float) -> float:
	var d := Vector2(x, z).length()
	var h := 1.2 * (1.0 - smoothstep(30.0, 44.0, d)) + _noise(x, z) * 0.35
	# the marsh to the east: the ground sinks under black water
	h = lerpf(h, -2.2, smoothstep(MARSH_X - 4.0, MARSH_X + 6.0, x))
	return h

func _shape(x: float, z: float, b: float, _rd: float, _rt: int) -> float:
	var d := Vector2(x, z).length()
	return b + _noise(x * 1.9, z * 1.9) * (0.1 if d < R else 0.5)

func _splat(x: float, z: float) -> Color:
	var k := _k(x, z)
	var n := sin(x * 0.37 + z * 0.23) * 0.5 + 0.5
	var road := (1.0 - smoothstep(2.4, 3.5, _rd[k])) if _rt[k] == 1 else 0.0
	var trail := (1.0 - smoothstep(1.1, 2.1, _rd[k])) if _rt[k] == 2 else 0.0
	var d := Vector2(x, z).length()
	var trodden := 1.0 - smoothstep(9.0, 26.0, d)
	var fire := 1.0 - smoothstep(4.5, 6.0, Vector2(x, z).distance_to(BONFIRE))
	var marsh := smoothstep(MARSH_X - 6.0, MARSH_X + 2.0, x)
	var r := clampf(maxf(maxf(trail, trodden * 0.7), fire) + n * 0.1, 0.0, 1.0)
	var g := clampf(marsh + n * 0.3 + (1.0 - trodden) * 0.35, 0.0, 1.0) * (1.0 - trail)
	var b := clampf(maxf(road * 0.8, DataTownRows.paved(&"wyman_outpost", x, z) * 0.85), 0.0, 1.0)
	return Color(r * (1.0 - b), g * (1.0 - b), b)

# ------------------------------------------------------------------------------------------------------------
# the marsh and the stockade

func _marsh() -> void:
	water(Rect2(MARSH_X + 1.0, -72, 105.0 - MARSH_X - 1.0, 140), MARSH_Y, Color(0.1, 0.2, 0.16), Color(0.02, 0.05, 0.04), 0.25, 2.0, 0.12)
	mist(Rect2(MARSH_X + 2.0, -72, 103.0 - MARSH_X, 140), MARSH_Y + 1.0, Color(0.2, 0.25, 0.25), 0.3)
	for i in 34:
		var x := MARSH_X + 4.0 + rng.randf() * 60.0
		var z := -68.0 + rng.randf() * 130.0
		decor("tree_dead_a" if i % 2 else "tree_dead_b", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.9, 1.4), true, true, 6.0)
	for i in 80:
		var x := MARSH_X - 1.0 + rng.randf() * 24.0
		var z := -55.0 + rng.randf() * 100.0
		decor("fern", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.6, 1.0))
	for i in 6:
		decor("pillar_broken", Vector3(MARSH_X + 8.0 + rng.randf() * 18.0, -0.6, -40.0 + i * 14.0), rng.randf() * 360.0, 0.7, true, true, 12.0)
	# will-o'-lights far out on the water
	for i in 3:
		var p := Vector3(MARSH_X + 14.0 + rng.randf() * 20.0, MARSH_Y + 1.2, -40.0 + rng.randf() * 80.0)
		light(p, Color(0.5, 1.0, 0.8), 1.6, 7.0, false, true)
	# bh-021: the marsh line stays closed except where the Marsh Gate's causeway leaves the camp
	boundary(Vector3(MARSH_X - 2.0, -4.0, -66.0), Vector3(MARSH_X - 2.0, -4.0, 2.6), 12.0)
	boundary(Vector3(MARSH_X - 2.0, -4.0, 11.8), Vector3(MARSH_X - 2.0, -4.0, 54.0), 12.0)

## bh-021: the Marsh Gate — an iron gate and a bar across the arch until Sir Aldric opens it (mq_marsh_gate_open), a
## short railed causeway of planks out over the reeds, and the boundary into the Weeping Causeway map.
func _marsh_gate_bar() -> void:
	var a := deg_to_rad(_marsh_gate)
	var c := Vector2(cos(a), sin(a)) * R
	var yaw := rad_to_deg(atan2(c.x, c.y))
	var y := ground(c.x, c.y)
	var sb := StaticBody3D.new()
	sb.name = "MarshGateBar"
	sb.collision_layer = BH.LAYER_WORLD
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(6.4, 4.0, 0.8)
	cs.shape = bs
	sb.add_child(cs)
	sb.position = Vector3(c.x, y + 2.0, c.y)
	sb.rotation.y = deg_to_rad(yaw)
	geo.add_child(sb)
	hide_when(sb, &"mq_marsh_gate_open")
	hide_when(kit("gate_iron", Vector3(c.x, y, c.y), yaw, 1.0, props), &"mq_marsh_gate_open")
	var out := Vector2(MARSH_X + 0.5, 7.2)
	corridor_rails([c, out], 3.6)
	boundary(Vector3(out.x + 1.2, -4.0, out.y - 4.0), Vector3(out.x + 1.2, -4.0, out.y + 4.0), 12.0)
	for i in 4:
		var p := c.lerp(out, (i + 0.5) / 4.0)
		kit("dock_planks", Vector3(p.x, ground(p.x, p.y) + 0.05, p.y), yaw + 90.0, 1.0, deco)
	exit_zone(&"wyman_marsh_gate", Vector3(out.x - 0.6, 0, out.y), Vector3(2.4, 4.0, 7.0), &"weeping_causeway", &"arrival",
		"The Weeping Causeway", &"mq_marsh_gate_open", "The Marsh Gate is barred. Sir Aldric holds the key.")
	spawn(&"marsh_gate", Vector3(c.x - 3.5, 0, c.y - 1.0), -95.0, true)

func _in_gap(deg: float) -> bool:
	return absf(wrapf(deg - _north_gate, -180.0, 180.0)) < 7.5 or absf(wrapf(deg - _west_gate, -180.0, 180.0)) < 7.5 		or absf(wrapf(deg - _marsh_gate, -180.0, 180.0)) < 7.5

func _stockade() -> void:
	var n := int(TAU * R / 4.0)
	for i in n:
		var a := TAU * (i + 0.5) / n
		var deg := rad_to_deg(a)
		if _in_gap(deg):
			continue
		var p := Vector2(cos(a), sin(a)) * R
		kit("palisade_fence", Vector3(p.x, 0, p.y), -deg + 90.0 + 180.0, 1.0, props, true)
	var m := 120
	for i in m:
		var a0 := TAU * i / m
		var a1 := TAU * (i + 1) / m
		if _in_gap(rad_to_deg((a0 + a1) * 0.5)) or _in_gap(rad_to_deg(a0)) or _in_gap(rad_to_deg(a1)):
			continue
		var p0 := Vector2(cos(a0), sin(a0)) * (R + 1.0)
		var p1 := Vector2(cos(a1), sin(a1)) * (R + 1.0)
		boundary(Vector3(p0.x, ground(p0.x, p0.y) - 1.0, p0.y), Vector3(p1.x, ground(p1.x, p1.y) - 1.0, p1.y), 8.0, 0.8)
	# gap edges: close the corners beside each gate
	for g: float in [_north_gate, _west_gate, _marsh_gate]:
		for side: float in [-1.0, 1.0]:
			var a := deg_to_rad(g + side * 7.5)
			var q0 := Vector2(cos(a), sin(a)) * (R - 1.0)
			var q1 := Vector2(cos(a), sin(a)) * (R + 3.5)
			boundary(Vector3(q0.x, ground(q0.x, q0.y) - 1.0, q0.y), Vector3(q1.x, ground(q1.x, q1.y) - 1.0, q1.y), 8.0, 0.6)
	for g: float in [_north_gate, _west_gate, _marsh_gate]:
		var a := deg_to_rad(g)
		var c := Vector2(cos(a), sin(a)) * R
		gatehouse(c, rad_to_deg(atan2(c.x, c.y)))
	_marsh_gate_bar()
	# corridors along the roads to the district boundaries
	var ng := Vector2(cos(deg_to_rad(_north_gate)), sin(deg_to_rad(_north_gate))) * (R + 1.0)
	var wg := Vector2(cos(deg_to_rad(_west_gate)), sin(deg_to_rad(_west_gate))) * (R + 1.0)
	corridor_rails([ng, Vector2(7.0, -44.0)], 4.6)
	# bh-012: the Watch Road's west rail opens onto the Brass path to the Orrery gate (its own corridor)
	boundary(Vector3(7.0 + 4.6, ground(7, -44) - 2.0, -44.0), Vector3(8.0 + 4.6, ground(8, -62) - 2.0, -62.0), 10.0, 0.6)
	boundary(Vector3(7.0 - 4.6, ground(7, -44) - 2.0, -44.0), Vector3(7.2 - 4.6, ground(7, -50) - 2.0, -50.5), 10.0, 0.6)
	boundary(Vector3(7.8 - 4.6, ground(8, -60) - 2.0, -59.5), Vector3(8.0 - 4.6, ground(8, -62) - 2.0, -62.0), 10.0, 0.6)
	corridor_rails([Vector2(3.2, -55.3), Vector2(-4.0, -54.0), Vector2(-16.0, -50.0), Vector2(-28.0, -46.0), Vector2(-34.0, -44.0)], 5.2)
	boundary(Vector3(-34.0, -2.0, -50.0), Vector3(-34.0, -2.0, -38.0), 12.0)
	boundary(Vector3(3.0, -2.0, -62.0), Vector3(13.0, -2.0, -62.0), 12.0)
	corridor_rails([wg, Vector2(-46.0, 17.0), Vector2(-66.0, 21.2)], 4.6)
	boundary(Vector3(-66.0, -2.0, 16.4), Vector3(-66.0, -2.0, 26.0), 12.0)
	exit_zone(&"wyman_watch_road", Vector3(8.0, 0, -57.5), Vector3(8.4, 4.0, 3.0), &"olivar", &"south_road", "Olivar")
	exit_zone(&"wyman_fen_road", Vector3(-61.5, 0, 20.3), Vector3(3.0, 4.0, 8.4), &"westreach", &"fen_road", "Westreach")
	signpost_bed(Vector2(12.0, -40.0), [["Olivar (Watch Road)", Vector2(0, -1)], ["Wyman Outpost", Vector2(0, 1)]])
	signpost_bed(Vector2(-44.0, 22.0), [["Lantern Fields (Fen Road)", Vector2(-1, 0.2)], ["Wyman Outpost", Vector2(1, -0.3)]])
	for p: Vector2 in [Vector2(2.2, -44.0), Vector2(12.4, -52.0), Vector2(-40.0, 11.5), Vector2(-54.0, 23.5)]:
		lamp_post(Vector3(p.x, 0, p.y), rng.randf() * 360.0)

# ------------------------------------------------------------------------------------------------------------
# the camp

func _fire_ring() -> void:
	bonfire("Wyman Outpost", Vector3(BONFIRE.x, 0, BONFIRE.y), &"bonfire", 0.0)
	keep_clear(BONFIRE.x, BONFIRE.y, 6.0)
	for i in 4:
		var a := TAU * i / 4.0 + PI / 4.0
		var p := BONFIRE + Vector2(cos(a), sin(a)) * 4.4
		if road_dist(p.x, p.y) < 3.8:
			continue
		kit("bench", Vector3(p.x, 0, p.y), rad_to_deg(atan2(-(p.x - BONFIRE.x), -(p.y - BONFIRE.y))), 1.0, props, true)
	for i in 5:
		var a := TAU * i / 5.0 + 0.4
		var lp := BONFIRE + Vector2(cos(a), sin(a)) * 6.4
		if road_dist(lp.x, lp.y) > 4.5:
			decor("log_fallen", Vector3(lp.x, 0, lp.y), rad_to_deg(a) + 90.0, 0.7, true, true)

func _tent_yaw(p: Vector2) -> float:
	var to := BONFIRE - p
	return rad_to_deg(atan2(to.x, to.y))

func _tents() -> void:
	for i in TENTS.size():
		var p: Vector2 = TENTS[i]
		var yaw := _tent_yaw(p)
		kit("tent_old", Vector3(p.x, 0, p.y), yaw, 1.15, props, true)
		keep_clear(p.x, p.y, 3.6)
		var fwd := Vector2(sin(deg_to_rad(yaw)), cos(deg_to_rad(yaw)))
		var side := Vector2(fwd.y, -fwd.x)
		var br := p + fwd * 2.2 + side * 1.2
		kit("bedroll", Vector3(br.x, 0, br.y), yaw + 90.0, 1.0, props, true)
		# a guild banner on a pole beside every other tent
		var pole := p + side * -2.9 + fwd * 0.8
		var y := height_at(pole.x, pole.y)
		var pm := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.05
		cm.bottom_radius = 0.07
		cm.height = 4.2
		pm.mesh = cm
		pm.material_override = MaterialLibrary.env("BH_WoodDark")
		pm.position = Vector3(pole.x, y + 2.1, pole.y)
		deco.add_child(pm)
		kit("guild_banner_swordfin" if i % 2 == 0 else "guild_banner_lantern", Vector3(pole.x, y + 4.0, pole.y) + Vector3(fwd.x, 0, fwd.y) * 0.1, yaw, 0.85, deco)
		if i % 3 == 0:
			var l := p + fwd * 2.6 - side * 1.8
			kit("lantern_stand", Vector3(l.x, 0, l.y), yaw, 1.0, props, true)
			light(Vector3(l.x + 0.4, height_at(l.x, l.y) + 1.8, l.y), Color(1.0, 0.72, 0.42), 2.0, 8.0, false, true)
		for c in [p - fwd * 1.6 + side * 2.2]:
			breakable("crate" if i % 2 else "barrel", Vector3(c.x, 0, c.y), rng.randf() * 360.0, 20.0, true)

func _lodge_and_register() -> void:
	var h := kit("house_intact", Vector3(LODGE.x, 0, LODGE.y), 0.0, 0.85, props, true)
	light(socket_pos(h, "door_light"), Color(1.0, 0.68, 0.35), 2.4, 8.0, false, true)
	keep_clear(LODGE.x, LODGE.y, 5.5)
	kit("map_table", Vector3(LODGE.x + 3.4, 0, LODGE.y + 6.2), 10.0, 1.0, props, true)
	candles(Vector3(LODGE.x + 3.4, 1.13 + height_at(LODGE.x + 3.4, LODGE.y + 6.2), LODGE.y + 6.2))
	kit("guild_banner_swordfin", Vector3(LODGE.x - 2.2, height_at(LODGE.x, LODGE.y) + 3.4, LODGE.y + 3.9), 0.0, 1.0, deco)
	kit("guild_banner_lantern", Vector3(LODGE.x + 2.2, height_at(LODGE.x, LODGE.y) + 3.4, LODGE.y + 3.9), 0.0, 1.0, deco)
	# the Hero Register: a notice board of signed cards, lit by a lantern
	kit("notice_board", Vector3(REGISTER.x, 0, REGISTER.y), 0.0, 1.0, props, true)
	var rb := RosterBoard.new()
	rb.name = "HeroRegister"
	rb.position = Vector3(REGISTER.x, height_at(REGISTER.x, REGISTER.y), REGISTER.y + 0.9)
	markers.add_child(rb)
	kit("lantern_stand", Vector3(REGISTER.x + 1.9, 0, REGISTER.y + 0.2), 0.0, 1.0, props, true)
	light(Vector3(REGISTER.x + 2.3, height_at(REGISTER.x, REGISTER.y) + 1.8, REGISTER.y + 0.2), Color(1.0, 0.75, 0.45), 2.2, 7.0, false, true)
	keep_clear(REGISTER.x, REGISTER.y, 2.5)

## bh-018: Quartermaster Row (DataTownRows) south of the bonfire: the quartermaster's tent, the field smith's campaign forge,
## the crystal prospector's cart, the camp kettle and the workbench.
func _trade_row() -> void:
	TownRowBuilder.build(self, def.id)

## A straw training dummy: post, crossbar and a stuffed sack (solid, so heroes and the player can swing at it).
func dummy(p: Vector2, yaw: float) -> void:
	var y := height_at(p.x, p.y)
	var root3 := Node3D.new()
	root3.name = "Dummy_%d" % props.get_child_count()
	root3.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(yaw)), Vector3(p.x, y, p.y))
	var wood := MaterialLibrary.env("BH_WoodDark")
	var straw := StandardMaterial3D.new()
	straw.albedo_color = Color(0.72, 0.6, 0.36)
	straw.roughness = 1.0
	var post := MeshInstance3D.new()
	var pm := CylinderMesh.new()
	pm.top_radius = 0.07
	pm.bottom_radius = 0.09
	pm.height = 2.0
	post.mesh = pm
	post.material_override = wood
	post.position.y = 1.0
	root3.add_child(post)
	var bar := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.2, 0.09, 0.09)
	bar.mesh = bm
	bar.material_override = wood
	bar.position.y = 1.55
	root3.add_child(bar)
	var sack := MeshInstance3D.new()
	var sm := CapsuleMesh.new()
	sm.radius = 0.26
	sm.height = 0.95
	sack.mesh = sm
	sack.material_override = straw
	sack.position.y = 1.35
	root3.add_child(sack)
	var head := MeshInstance3D.new()
	var hm := SphereMesh.new()
	hm.radius = 0.17
	hm.height = 0.34
	head.mesh = hm
	head.material_override = straw
	head.position.y = 1.95
	root3.add_child(head)
	var sb := StaticBody3D.new()
	sb.collision_layer = BH.LAYER_PROPS
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.3
	cap.height = 2.0
	cs.shape = cap
	cs.position.y = 1.0
	sb.add_child(cs)
	root3.add_child(sb)
	props.add_child(root3)

func _training_yard() -> void:
	var y := YARD
	for p in [[Vector2(-3.0, 0.0), 180.0], [Vector2(1.0, 1.4), 200.0], [Vector2(4.6, -0.6), 150.0]]:
		dummy(y + p[0], p[1])
	kit("weapon_rack", Vector3(y.x - 6.0, 0, y.y + 1.0), 80.0, 1.0, props, true)
	kit("weapon_rack", Vector3(y.x + 7.5, 0, y.y + 0.8), -80.0, 1.0, props, true)
	for i in 5:
		kit("wood_fence", Vector3(y.x - 6.0 + i * 3.3, 0, y.y + 3.6), 0.0, 0.9, props, true)
	torch_post(Vector2(y.x - 6.5, y.y - 2.5))
	torch_post(Vector2(y.x + 8.0, y.y - 2.5))
	keep_clear(y.x, y.y, 7.5)

func torch_post(p: Vector2) -> void:
	var y := height_at(p.x, p.y) + 2.3
	var pm := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.06
	cm.bottom_radius = 0.08
	cm.height = 2.3
	pm.mesh = cm
	pm.material_override = MaterialLibrary.env("BH_WoodDark")
	pm.position = Vector3(p.x, y - 1.15, p.y)
	deco.add_child(pm)
	flame(Vector3(p.x, y + 0.2, p.y), 1.0)
	light(Vector3(p.x, y + 0.6, p.y), FIRE, 2.6, 10.0, false, true)

func _tower_and_overlook() -> void:
	kit("scaffold_platform", Vector3(TOWER.x, 0, TOWER.y), 45.0, 1.0, props, true)
	kit("ladder", Vector3(TOWER.x + 0.9, 0, TOWER.y + 1.2), 45.0, 1.0, deco, true)
	light(Vector3(TOWER.x, height_at(TOWER.x, TOWER.y) + 5.4, TOWER.y), Color(1.0, 0.7, 0.4), 2.4, 10.0, false, true)
	keep_clear(TOWER.x, TOWER.y, 3.0)
	# the Marsh Overlook: two platforms and a brazier looking out over the reeds
	var o := OVERLOOK
	kit("scaffold_platform", Vector3(o.x, 0, o.y - 1.05), 0.0, 1.0, props, true)
	kit("scaffold_platform", Vector3(o.x, 0, o.y + 1.05), 0.0, 1.0, props, true)
	kit("ladder", Vector3(o.x - 1.2, 0, o.y + 0.4), -90.0, 1.0, deco, true)
	var top := height_at(o.x, o.y) + 4.0
	brazier(Vector3(o.x, top, o.y), 3.4, false, false)
	kit("banner_torn", Vector3(o.x - 1.0, top + 2.4, o.y - 2.0), -90.0, 1.0, deco)
	keep_clear(o.x, o.y, 3.5)
	signpost_bed(Vector2(o.x - 3.6, o.y + 3.2), [["Reedwater Marsh (no road yet)", Vector2(1, 0)], ["Bonfire", Vector2(-1, 0)]])

func _shrine() -> void:
	var s := SHRINE
	var sy := height_at(s.x, s.y) + 0.05
	apron(s, sy, 3.6)
	teleporter(&"wyman_shrine", Vector3(s.x, sy, s.y), &"sanctuary", &"waypoint", "Malasugue Town")
	spawn(&"wyman_shrine", Vector3(s.x + 3.2, 0, s.y - 1.6), 110.0, true)
	for a: float in [0.9, 2.5, 4.1]:
		decor("rock_medium", Vector3(s.x + cos(a) * 4.0, 0, s.y + sin(a) * 3.8), rng.randf() * 360.0, rng.randf_range(0.5, 0.7), true, true)
	keep_clear(s.x, s.y, 5.0)

func _herbs() -> void:
	for p: Vector2 in [Vector2(27.0, -12.0), Vector2(27.5, 10.0), Vector2(24.0, 18.0)]:
		herb_patch(&"mirebloom", Vector3(p.x, 0, p.y))
		keep_clear(p.x, p.y, 1.5)
	for p: Vector2 in [Vector2(-25.5, -7.0), Vector2(9.0, -27.0)]:
		herb_patch(&"silverleaf", Vector3(p.x, 0, p.y))
		keep_clear(p.x, p.y, 1.5)
	herb_patch(&"brightcap", Vector3(-17.0, 0, -24.5))
	keep_clear(-17.0, -24.5, 1.5)

func _greenery() -> void:
	var blocked := func(x: float, z: float) -> bool:
		if road_dist(x, z) < 5.5 or not is_clear(x, z, 0.8) or x > MARSH_X - 3.0:
			return true
		return Vector2(x, z).length() < R + 3.0
	var trees := scatter(["tree_pine", "tree_pine", "tree_oak_twisted", "tree_dead_a"], Rect2(-95, -72, MARSH_X + 95.0, 140), 190, 5.0,
		Vector2(0.85, 1.3), blocked, true, true)
	for t in trees:
		if road_dist(t.x, t.z) < 12.0:
			blocker(Vector3(t.x, height_at(t.x, t.z) + 2.0, t.z), Vector3(0.9, 4.0, 0.9))
	scatter(["bush_a", "bush_b", "fern", "rock_small", "stump"], Rect2(-95, -72, MARSH_X + 95.0, 140), 150, 3.0, Vector2(0.7, 1.2), blocked, true, true)
	var camp := func(x: float, z: float) -> bool:
		return road_dist(x, z) < 3.8 or not is_clear(x, z, 0.8) or Vector2(x, z).length() > R - 2.0 or Vector2(x, z).length() < 8.0
	scatter(["bush_a", "fern", "rock_small"], Rect2(-30, -30, 60, 60), 34, 3.0, Vector2(0.6, 0.9), camp, true, true)
	var placed := 0
	var tries := 0
	while placed < 800 and tries < 5000:
		tries += 1
		var x := -68.0 + rng.randf() * (MARSH_X + 60.0)
		var z := -64.0 + rng.randf() * 112.0
		if road_dist(x, z) < 3.2 or not is_clear(x, z) or Vector2(x, z).distance_to(BONFIRE) < 7.0:
			continue
		decor("grass_clump", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.8, 1.3))
		placed += 1
