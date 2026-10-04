extends MapBuilder
## MAP — The Bridge of Death (bh-029; levels 62–66). "Three hundred paces over nothing."
##
## The Wirewrights' great span over the gorge between the Glasswire Barrens and the Heart Citadel. A cliff ledge in the
## south (the Bridge Road from the Barrens) ends at the south gatehouse; from there 29 deck segments run end to end,
## 232 m over a gorge with no floor anyone has seen, to the far platform (32 x 32 m of stepped stone blocks hung over
## the gorge on an inverted stepped base and a pier), then one more segment to the north gatehouse and the landing on
## the north ledge. Three pairs of ward pylons stand off the deck's sides on cantilevered corbels; each pair is fed by
## one of the three Vaults (WardPylon) and throws lightning while its Vault's lord lives. Varrogh, the Deathspan
## Colossus, holds the far platform; the north gatehouse is sealed by a Blackwire ward lattice until he falls.
##
## Geometry (map-local metres, +Z south): zr_bridge_span_8m is 8 m long (Z) x 12 m wide with its deck top at its origin,
## so the segments sit at z = 131 - 8 (i + 0.5) and touch end to end with no gap; the gatehouse passages are 10 m long
## with their floors at y = 0 too (south 131..141, north -141..-151), and the platform's blocks (zr_terrace_4m, 8 x 8 x
## 4 m) have their tops at y = 0. Everything walkable is one surface at y = 0 from the south rim to the north rim.
## Gameplay markers: spawns barrens_road / citadel_road / start, exit zones south (Barrens) and north (Citadel, gated by
## boss_deathspan_defeated), boss_spawn (deathspan_colossus), summons_* zones, three WardPylon nodes.

const SEG := 8.0                                  # zr_bridge_span_8m length along Z
const SPAN_Z0 := 131.0                            # north mouth of the south gatehouse = south end of the span
const SPAN_N := 29                                # 29 x 8 m = 232 m: 131 .. -101
const PLAT_Z0 := -101.0                           # the far platform: z -101 .. -133, x -16 .. 16
const PLAT_Z1 := -133.0
const PLAT_HX := 16.0
const LINK_Z := -137.0                            # one more segment: -133 .. -141
const SOUTH_GATE_Z := 136.0                       # gatehouse centres (10 m passages)
const NORTH_GATE_Z := DataZarael.BR_GATE_N        # -146
const RIM_S := 129.0                              # where the ledges' ground ends over the gorge
const RIM_N := -141.0
const GROUND_Y := -0.12                           # the ledges sit a hair under the deck so the paving never z-fights
const RAIL := 5.6                                 # the parapets' inner faces are at 5.3; boundaries just outside
const LEDGE_HALF := 10.3                          # the approach and landing are walled by rock to +-10.3
const PYLON_X := 8.1                              # zr_bridge_pylon: foundation 4.4 wide, its inner edge in the deck's side
const PIERS := [2, 7, 12, 17, 22, 27]             # span segments with a pier hung under them
const WARD := Color(1.0, 1.0, 1.0)
const GLYPH := Color(0.3, 0.95, 0.85)
## Camps on the span: [id, z, enemies, count, levels, elite chance] (the road near the south gate stays quiet).
const CAMPS := [
	["span_south", 102.0, [&"span_warden", &"wire_leaper"], 3, Vector2i(62, 63), 0.1],
	["span_first_ward", 62.0, [&"ward_eye", &"span_warden", &"wire_leaper"], 4, Vector2i(63, 64), 0.12],
	["span_middle", 24.0, [&"wire_leaper", &"wire_leaper", &"ward_eye"], 4, Vector2i(64, 65), 0.15],
	["span_second_ward", -22.0, [&"span_warden", &"ward_eye", &"span_warden"], 5, Vector2i(64, 65), 0.18],
	["span_north", -54.0, [&"span_warden", &"wire_leaper", &"ward_eye"], 5, Vector2i(65, 66), 0.2],
	["span_last", -88.0, [&"ward_eye", &"ward_eye", &"wire_leaper"], 4, Vector2i(65, 66), 0.22],
]

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.023, 0.016, 0.031), "sky_horizon": Color(0.275, 0.157, 0.191),
		"ambient": Color(0.356, 0.316, 0.364), "ambient_energy": 0.85,
		"fog": Color(0.137, 0.088, 0.124), "fog_density": 0.007, "fog_height": -6.0, "fog_height_density": 0.22,
		"sun": Color(0.849, 0.65, 0.606), "sun_energy": 0.65, "sun_rot": Vector3(-40, 28, 0), "glow": 1.0,
		"exposure": 1.12, "contrast": 1.08, "saturation": 0.95,
	})
	# each ledge's terrain reaches 34 m out over the gorge so its rim can curve away from the bridge; past the rim it
	# falls away steeply under the cliff faces
	terrain(Vector2i(240, 68), Vector3(0, 0, RIM_S), _terrain_h, _splat, _textures(), Color(0.92, 0.88, 0.86))
	terrain(Vector2i(240, 68), Vector3(0, 0, RIM_N), _terrain_h, _splat, _textures(), Color(0.92, 0.88, 0.86))
	height_fn = _ground
	_span()
	_platform()
	_gatehouses()
	_seal()
	_pylons()
	_rims()
	_gorge()
	_ledge_dressing()
	_map_design()
	_wind()
	_camps()
	_boss()
	for gid in DataDungeons.gates_on(def.id):
		var gs: Dictionary = DataDungeons.get_def(gid).surface
		dungeon_gate(gid, gs.pos, gs.yaw)
	var south := DataZarael.BR_SOUTH
	var north := DataZarael.BR_NORTH
	spawn(&"barrens_road", Vector3(south.x, 0, south.z), 180.0, true)
	spawn(&"start", Vector3(south.x, 0, south.z), 180.0, true)
	spawn(&"citadel_road", Vector3(north.x, 0, north.z), 0.0, true)
	exit_zone(&"bridge_south_road", Vector3(0, 0, 159.4), Vector3(LEDGE_HALF * 2.0, 4.0, 2.0), &"zr_barrens", &"bridge_road",
		"The Glasswire Barrens")
	exit_zone(&"bridge_north_road", Vector3(0, 0, -169.4), Vector3(LEDGE_HALF * 2.0, 4.0, 2.0), &"zr_citadel", &"bridge_road",
		"The Heart Citadel", DataZarael.F_BRIDGE, "The north gatehouse stays sealed while Varrogh holds the span.")
	_rails()
	set_bounds(AABB(Vector3(-40, -60, -172), Vector3(80, 90, 334)))
	view("overview", Vector3(0, -8, -4), 32.0, 30.0, 250.0, 45.0)
	view("topdown", Vector3(0, 0, -6), 0.0, 89.5, 235.0, 72.0)
	view("south_gate", Vector3(0, 4, 138), 0.0, 34.0, 44.0, 45.0)
	view("span", Vector3(0, -4, 72), 38.0, 22.0, 70.0, 45.0)
	view("ward_pylons", Vector3(0, 6, 4), 0.0, 38.0, 36.0, 45.0)
	view("platform", Vector3(0, 0, -118), 0.0, 52.0, 62.0, 45.0)
	view("north_gate", Vector3(0, 4, -146), 0.0, 36.0, 36.0, 45.0)
	view("gorge", Vector3(0, -22, 30), 90.0, 6.0, 120.0, 45.0)
	view("game_south", Vector3(0, 1.1, 146), 0.0, 54.0, 16.0, 40.0)
	view("game_span", Vector3(0, 1.1, 40), 0.0, 54.0, 16.0, 40.0)
	view("game_pylon", Vector3(0, 1.1, 8), 0.0, 54.0, 20.0, 40.0)
	view("game_platform", Vector3(0, 1.1, -110), 0.0, 54.0, 20.0, 40.0)

# ------------------------------------------------------------------------------------------------------------
# ground: two ledges over the gorge, the deck everywhere between

func _textures() -> Dictionary:
	return {"grass": "red_clay", "moss": "blackwire_soil", "dirt": "cliff_ochre", "path": "terrace_paving", "rock": "cliff_ochre"}

func _noise(x: float, z: float) -> float:
	return sin(x * 0.13 + z * 0.07) * 0.7 + cos(x * 0.05 - z * 0.11) * 0.9 + sin(x * 0.31 - z * 0.23) * 0.25

## How far a rim swings back from the straight line the bridge leaves from: straight for 22 m either side of the
## road, then curving away over the gorge (the gorge widens out of sight to the east and west).
func _bend(x: float) -> float:
	var ax := absf(x)
	return maxf(0.0, ax - 22.0) * 0.32 + (sin(x * 0.09) + 1.0) * 1.6 * smoothstep(22.0, 40.0, ax)

func _rim_s(x: float) -> float:
	return RIM_S - _bend(x)

func _rim_n(x: float) -> float:
	return RIM_N + _bend(x)

## The ledges' ground. On a ledge the road runs between rock slopes that rise from |x| 12 m, flattened toward the rim
## so the cliff faces under it meet one level edge; past the rim the ground drops away under the cliffs.
func _terrain_h(x: float, z: float) -> float:
	var inward := z - _rim_s(x) if z > 0.0 else _rim_n(x) - z
	if inward < 0.0:
		return GROUND_Y - minf(-inward, 3.0) * 4.0 - maxf(0.0, -inward - 3.0) * 14.0
	var over := absf(x) - 12.0
	if over <= 0.0:
		return GROUND_Y
	var rise := minf(over * 1.3, 24.0) + _noise(x, z) * minf(over * 0.25, 2.2)
	return GROUND_Y + maxf(0.0, rise) * smoothstep(1.0, 14.0, inward)

## Walking height (MapBuilder.ground): the deck (0) between the rims, the ledges beyond them.
func _ground(x: float, z: float) -> float:
	if z < RIM_S and z > RIM_N and absf(x) < 16.5:
		return 0.0
	return _terrain_h(x, z)

func _splat(x: float, z: float) -> Color:
	var n := sin(x * 0.27 + z * 0.19) * 0.5 + 0.5
	var road := 1.0 - smoothstep(4.0, 7.0, absf(x))
	var soil := clampf(n * 0.6 - 0.15, 0.0, 1.0) * (1.0 - road)
	var ochre := clampf(smoothstep(10.0, 16.0, absf(x)) * 0.8, 0.0, 1.0) * (1.0 - road)
	return Color(ochre, soil, road * (0.8 + n * 0.2))

# ------------------------------------------------------------------------------------------------------------
# the span

func _seg_z(i: int) -> float:
	return SPAN_Z0 - SEG * (i + 0.5)

func _span() -> void:
	for i in SPAN_N:
		arch("zr_bridge_span_8m", Vector3(0, 0, _seg_z(i)), 0.0)
	arch("zr_bridge_span_8m", Vector3(0, 0, LINK_Z), 0.0)
	# piers hang under every fifth segment: their capitals (y = 0 at the pier's origin) catch the girders' lowest step
	# (its underside is 5.02 m under the deck), and their feet stand on rock 45 m further down, lost in the mist
	for i: int in PIERS:
		kit("zr_bridge_pier", Vector3(0, -4.98, _seg_z(i)), 0.0, 1.0, deco)
	# soft white light pooled on the deck every 48 m (the deck's own inlaid wires do the rest)
	for i in 6:
		var z := SPAN_Z0 - 20.0 - i * 44.0
		light(Vector3(4.2 * (1.0 if i % 2 == 0 else -1.0), 2.6, z), WARD, 1.3, 13.0, false, false)
	# what the span kept of those who tried to cross while the wards burned
	var spots := [[Vector2(-3.0, 117), "bones_scatter"], [Vector2(2.6, 90), "weapons_discarded"], [Vector2(-2.2, 47), "bones_scatter"],
		[Vector2(3.1, 11), "bones_scatter"], [Vector2(-3.4, -38), "weapons_discarded"], [Vector2(2.4, -70), "bones_scatter"],
		[Vector2(-1.5, -95), "skull_pile"]]
	for s: Array in spots:
		var p: Vector2 = s[0]
		decor(s[1], Vector3(p.x, 0.02, p.y), rng.randf() * 360.0, 0.9, false)

func _platform() -> void:
	# 4 x 4 terrace blocks, tops at y = 0, joined edge to edge (8 m grid); the decorated face of the edge blocks looks out
	for ix in 4:
		for iz in 4:
			var x := -PLAT_HX + 4.0 + 8.0 * ix
			var z := PLAT_Z0 - 4.0 - 8.0 * iz
			var yaw := 0.0
			if iz == 3:
				yaw = 180.0
			elif ix == 0:
				yaw = -90.0
			elif ix == 3:
				yaw = 90.0
			arch("zr_terrace_4m", Vector3(x, -4.0, z), yaw)
			# the same block turned upside down under it: the platform's underside steps in like an inverted pyramid
			_flipped("zr_terrace_4m", Vector3(x, -4.0, z), yaw)
	for ix in 2:
		for iz in 2:
			_flipped("zr_terrace_4m", Vector3(-4.0 + 8.0 * ix, -8.0, PLAT_Z0 - 12.0 - 8.0 * iz), 90.0 * (ix + iz * 2))
	kit("zr_bridge_pier", Vector3(0, -11.98, (PLAT_Z0 + PLAT_Z1) * 0.5), 0.0, 1.25, deco)
	var c := (PLAT_Z0 + PLAT_Z1) * 0.5
	# one paved floor laid over the sixteen blocks (their tops meet at y = 0 but their cornices draw a grid of seams);
	# inset 0.8 m so the blocks' own carved rim shows round the edge. Visual only: the blocks' tops are the collision.
	var floor_mi := MeshInstance3D.new()
	floor_mi.name = "PlatformPaving"
	var fm := BoxMesh.new()
	fm.size = Vector3(PLAT_HX * 2.0 - 1.6, 0.3, PLAT_Z0 - PLAT_Z1 - 1.6)
	floor_mi.mesh = fm
	floor_mi.material_override = MaterialLibrary.env("BH_TerracePave")
	floor_mi.position = Vector3(0, -0.11, c)
	geo.add_child(floor_mi)
	# the deck's two Heartwire channels run on across the platform into the guardian's ring
	for sx: float in [-2.7, 2.7]:
		for z: float in [PLAT_Z0 - 2.0, PLAT_Z0 - 6.0, PLAT_Z1 + 2.0, PLAT_Z1 + 6.0]:
			decor("zr_wire_conduit_4m", Vector3(sx, 0.05, z), 90.0, 1.0, false)
	# braziers at the corners, glyph steles along the sides, broken columns and walls at the corners
	for sx: float in [-1.0, 1.0]:
		for z: float in [PLAT_Z0 - 4.0, PLAT_Z1 + 4.0]:
			_brazier(Vector3(sx * 12.5, 0, z), 3.0, sx < 0.0 and z > c)
		for z: float in [c + 7.0, c - 7.0]:
			kit("zr_glyph_stele", Vector3(sx * 14.6, 0, z), -90.0 * sx, 1.0, props)
		kit("zr_glyph_stele", Vector3(sx * 9.5, 0, PLAT_Z1 + 1.4), 0.0, 0.9, props)
		kit("zr_ruin_column", Vector3(sx * 14.4, 0, PLAT_Z1 + 2.2), 90.0 + 30.0 * sx, 1.0, props)
		kit("zr_ruin_wall", Vector3(sx * 15.0, 0, PLAT_Z0 - 2.6), 90.0, 0.8, props)
	# the guardian's floor: an inlaid Heartwire ring round the spot where Varrogh stands
	var bc := DataZarael.BR_BOSS
	var n := 16
	for k in n:
		var a := TAU * (k + 0.5) / n
		var p := Vector3(bc.x + cos(a) * 9.2, 0.05, bc.z + sin(a) * 9.2)
		decor("zr_wire_conduit_4m", p, rad_to_deg(-a) - 90.0, 0.92, false)
	for p: Vector2 in [Vector2(-5, -110), Vector2(6, -124), Vector2(-9, -126), Vector2(10, -106)]:
		decor("bones_scatter", Vector3(p.x, 0.02, p.y), rng.randf() * 360.0, 1.0, false)
	decor("weapons_discarded", Vector3(3.5, 0.02, -112.5), 40.0, 1.0, false)

## A kit piece turned upside down about its own origin (used for the platform's underside; no collision needed).
func _flipped(name: String, p: Vector3, yaw: float) -> Node3D:
	var n := kit(name, p, yaw, 1.0, deco)
	n.transform = Transform3D(Basis(Vector3.RIGHT, PI) * Basis(Vector3.UP, deg_to_rad(yaw)), p)
	for b in n.find_children("*", "CollisionObject3D", true, false):
		(b as CollisionObject3D).collision_layer = 0
	return n

func _gatehouses() -> void:
	for z: float in [SOUTH_GATE_Z, NORTH_GATE_Z]:
		var g := arch("zr_bridge_gatehouse", Vector3(0, 0, z), 0.0)
		for s in ["light_a", "light_b"]:
			light(socket_pos(g, s) + Vector3(0, 0, 0.4), WARD, 1.8, 9.0, false, true)
		# braziers before the passage mouth on the ledge side (south of the south gate, north of the north gate)
		var bz := z + 8.6 if z > 0.0 else z - 8.6
		for sx: float in [-1.0, 1.0]:
			_brazier(Vector3(sx * 8.2, _ground(sx * 8.2, bz), bz), 2.4, false)

## The north gatehouse's Blackwire ward: a lattice of glowing bars in a bronze frame over a faint ward membrane. It
## blocks the passage until Varrogh falls (hide_when releases its collision). It lives under Markers, not under the
## navigation region, so the navmesh stays whole and needs no rebake when the seal lifts.
func _seal() -> void:
	var seal := StaticBody3D.new()
	seal.name = "NorthSeal"
	seal.collision_layer = BH.LAYER_WORLD
	seal.collision_mask = 0
	seal.position = Vector3(0, 0, NORTH_GATE_Z)
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(10.4, 8.4, 0.9)
	cs.shape = bs
	cs.position = Vector3(0, 4.2, 0)
	seal.add_child(cs)
	var wire := MaterialLibrary.env("BH_Blackwire")
	var brass := MaterialLibrary.env("BH_Brass")
	var x := -4.5
	while x <= 4.51:
		_bar(seal, Vector3(x, 4.1, 0), Vector3(0.13, 8.2, 0.13), wire)
		x += 0.75
	for y: float in [0.25, 2.9, 5.6, 8.05]:
		_bar(seal, Vector3(0, y, 0), Vector3(10.0, 0.24, 0.3), brass)
	# crossed braces in every 2 m bay between the bands: a diamond ward-lattice, not a plain grate
	var ang := atan2(2.0, 2.4)
	for row in 3:
		var y0 := 0.25 + row * 2.65 + 1.32
		for k in 5:
			var bx := -4.0 + k * 2.0
			for sgn: float in [-1.0, 1.0]:
				var bar := _bar(seal, Vector3(bx, y0, 0.06), Vector3(0.09, 3.1, 0.09), wire)
				bar.rotation.z = ang * sgn
	var membrane := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(10.0, 8.0)
	membrane.mesh = qm
	var sm := VFXLib.glow_material(Color(1.0, 1.0, 1.0), 1.1)
	sm.set_shader_parameter("alpha", 0.28)
	membrane.material_override = sm
	membrane.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	membrane.position = Vector3(0, 4.1, -0.12)
	seal.add_child(membrane)
	markers.add_child(seal)
	hide_when(seal, DataZarael.F_BRIDGE)
	var glow := light(Vector3(0, 3.4, NORTH_GATE_Z + 1.6), WARD, 2.6, 11.0, false, true)
	hide_when(glow, DataZarael.F_BRIDGE)

func _bar(parent: Node3D, p: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = mat
	mi.position = p
	parent.add_child(mi)
	return mi

## Three ward pylon pairs, one per Vault, standing off the deck's sides on their corbels (outside the parapets).
func _pylons() -> void:
	for vault: StringName in DataZarael.BR_PYLONS:
		var z: float = DataZarael.BR_PYLONS[vault]
		var left := kit("zr_bridge_pylon", Vector3(-PYLON_X, 0, z), 90.0, 1.0, deco)
		var right := kit("zr_bridge_pylon", Vector3(PYLON_X, 0, z), -90.0, 1.0, deco)
		var wp := WardPylon.new().setup(vault, [left, right], [socket_pos(left, "arc"), socket_pos(right, "arc")])
		wp.position = Vector3(0, 0, z)
		markers.add_child(wp)

# ------------------------------------------------------------------------------------------------------------
# the gorge

## The rims: three courses of ochre cliff (zr_cliff_ochre, 12 m wide and 10 m tall, face on its +Z, top bed reaching
## 3.6 m behind its origin) under each ledge's edge, following the curved rim with their faces out over the gorge;
## the top course's top sits 0.2 m under the ledge so the ground covers its back half (no sheet edge, no step).
func _rims() -> void:
	for south: bool in [true, false]:
		var x := -120.0
		while x < 121.0:
			var rz := _rim_s(x) if south else _rim_n(x)
			var slope := (_rim_s(x + 1.0) - _rim_s(x - 1.0)) * 0.5 if south else (_rim_n(x + 1.0) - _rim_n(x - 1.0)) * 0.5
			var n := Vector2(slope, -1.0).normalized() if south else Vector2(-slope, 1.0).normalized()    # out over the gorge
			var yaw := rad_to_deg(atan2(n.x, n.y))
			var top := -0.3
			for layer in 3:
				var s := rng.randf_range(1.45, 1.85)
				var o := Vector2(x, rz) + n * (layer * 1.8 + rng.randf() * 1.6 - 0.8)
				decor("zr_cliff_ochre", Vector3(o.x + rng.randf_range(-1.5, 1.5), top - 10.0 * s, o.y), yaw + rng.randf_range(-9.0, 9.0),
					s, false, layer == 0)
				top -= 10.0 * s - rng.randf_range(1.0, 2.6)
			x += 15.5
		# boulders along the lip, away from the road
		for k in 18:
			var bx := rng.randf_range(-112.0, 112.0)
			if absf(bx) < 14.0:
				continue
			var bz := _rim_s(bx) + rng.randf_range(1.5, 5.0) if south else _rim_n(bx) - rng.randf_range(1.5, 5.0)
			decor("zr_rock_ochre_medium" if k % 3 else "zr_rock_ochre_large", Vector3(bx, -0.3, bz), rng.randf() * 360.0,
				rng.randf_range(0.8, 1.6), true, k % 3 == 0)

## Stacks of layered rock rising out of the dark far to the sides, rock under every pier's foot, mist banks deep
## down and a Blackwire glow at the bottom nobody has reached.
func _gorge() -> void:
	for k in 12:
		var side := -1.0 if k % 2 == 0 else 1.0
		var x := side * rng.randf_range(34.0, 96.0)
		var z := rng.randf_range(-100.0, 100.0)
		if side > 0.0 and absf(z - 30.0) < 48.0:
			z = 30.0 + signf(z - 30.0 + 0.01) * rng.randf_range(48.0, 70.0)     # keep the east-side sight line of the "gorge" view open
		var top := rng.randf_range(-26.0, -8.0)
		var r := rng.randf_range(4.5, 7.0)
		var y := top
		for layer in 4:
			var cs := rng.randf_range(1.5, 2.0)
			var twist := rng.randf() * TAU
			for f in 3:
				var a := TAU * f / 3.0 + twist
				decor("zr_cliff_ochre", Vector3(x + cos(a) * r, y - 10.0 * cs, z + sin(a) * r), rad_to_deg(atan2(cos(a), sin(a))), cs,
					false, false)
			y -= 10.0 * cs - 1.5
			r += 1.2
		decor("zr_rock_ochre_medium", Vector3(x, top - 0.6, z), rng.randf() * 360.0, rng.randf_range(1.6, 2.4), false, false)
	# the piers' feet stand on rock (lost in the dark long before anyone could see it)
	var feet: Array = []
	for i: int in PIERS:
		feet.append(_seg_z(i))
	feet.append((PLAT_Z0 + PLAT_Z1) * 0.5)
	for z: float in feet:
		for f in 3:
			var a := TAU * f / 3.0 + rng.randf()
			decor("zr_cliff_ochre", Vector3(cos(a) * 5.0, -50.5 - 18.0, z + sin(a) * 5.0), rad_to_deg(atan2(cos(a), sin(a))), 1.8,
				false, false)
	mist(Rect2(-180, -200, 360, 400), -20.0, Color(0.34, 0.18, 0.32), 0.45)
	mist(Rect2(-180, -200, 360, 400), -38.0, Color(0.24, 0.1, 0.22), 0.8)
	for z: float in [100.0, 30.0, -40.0, -110.0]:
		light(Vector3(rng.randf_range(-24.0, 24.0), -44.0, z), Color(0.85, 0.16, 0.5), 3.4, 48.0, false, false)

## Wind over the span: pale motes and ash blown east across the deck.
func _wind() -> void:
	var z := SPAN_Z0 - 10.0
	while z > PLAT_Z1:
		var p := VFXLib.particles(Color(0.82, 0.74, 0.86, 0.22), 10, 7.0, false, 0.5, 1.2, 25.0, Vector3(3.2, 0.2, 0.0), 9.0, false)
		p.position = Vector3(-14.0, rng.randf_range(-1.0, 3.0), z)
		p.visibility_aabb = AABB(Vector3(-10, -10, -12), Vector3(50, 20, 24))
		deco.add_child(p)
		z -= 34.0

func _ledge_dressing() -> void:
	for rim: Array in [[SOUTH_GATE_Z + 14.0, 1.0], [NORTH_GATE_Z - 14.0, -1.0]]:
		var zc: float = rim[0]
		var dir: float = rim[1]          # away from the gorge
		for sx: float in [-1.0, 1.0]:
			kit("zr_glyph_stele", Vector3(sx * 7.6, GROUND_Y, zc), 0.0 if dir > 0.0 else 180.0, 1.0, props)
			kit("zr_wire_lamp", Vector3(sx * 7.8, GROUND_Y, zc + dir * 7.0), 0.0, 1.0, props)
			kit("zr_rock_ochre_large", Vector3(sx * 13.0, 0, zc + dir * rng.randf_range(-2.0, 6.0)), rng.randf() * 360.0, 1.3, props, true)
		scatter(["zr_rock_ochre_medium", "zr_rock_ochre_large"], Rect2(-60, zc - 16.0, 120, 32), 22, 6.0, Vector2(0.7, 1.5),
			func(x, _z): return absf(x) < 14.0, true, true)
		scatter(["zr_glass_growth"], Rect2(-40, zc - 14.0, 80, 28), 7, 8.0, Vector2(0.8, 1.3),
			func(x, _z): return absf(x) < 15.0, true, true)
	# the Kharvenn left their mark on the north landing: rune-spikes driven in beside the road
	for p: Vector2 in [Vector2(-8.6, -158.0), Vector2(8.8, -163.0), Vector2(-8.9, -166.5)]:
		kit("zr_chain_spike", Vector3(p.x, GROUND_Y, p.y), rng.randf() * 360.0, 1.0, props)

## Rails along the deck and walls of rock round the ledges: the hero leaves only by the gatehouses' roads.
func _rails() -> void:
	for sx: float in [-1.0, 1.0]:
		boundary(Vector3(sx * RAIL, -2.0, SPAN_Z0 + 0.5), Vector3(sx * RAIL, -2.0, PLAT_Z0), 10.0, 0.6)
		boundary(Vector3(sx * RAIL, -2.0, PLAT_Z1), Vector3(sx * RAIL, -2.0, LINK_Z - 4.5), 10.0, 0.6)
		var px := sx * (PLAT_HX + 0.4)
		boundary(Vector3(sx * RAIL, -2.0, PLAT_Z0 + 0.3), Vector3(px, -2.0, PLAT_Z0 + 0.3), 10.0, 0.6)
		boundary(Vector3(px, -2.0, PLAT_Z0 + 0.3), Vector3(px, -2.0, PLAT_Z1 - 0.3), 10.0, 0.6)
		boundary(Vector3(px, -2.0, PLAT_Z1 - 0.3), Vector3(sx * RAIL, -2.0, PLAT_Z1 - 0.3), 10.0, 0.6)
		boundary(Vector3(sx * LEDGE_HALF, -2.0, RIM_S - 1.0), Vector3(sx * LEDGE_HALF, -2.0, 161.5), 12.0, 1.0)
		boundary(Vector3(sx * LEDGE_HALF, -2.0, RIM_N + 2.0), Vector3(sx * LEDGE_HALF, -2.0, -171.5), 12.0, 1.0)
	boundary(Vector3(-LEDGE_HALF, -2.0, 161.0), Vector3(LEDGE_HALF, -2.0, 161.0), 12.0, 1.0)
	boundary(Vector3(-LEDGE_HALF, -2.0, -171.0), Vector3(LEDGE_HALF, -2.0, -171.0), 12.0, 1.0)

# ------------------------------------------------------------------------------------------------------------
# monsters and the guardian

func _camps() -> void:
	for c: Array in CAMPS:
		var m := enemy_zone(c[0], Vector3(0, 0, c[1]), 4.0, c[2], c[3], c[5])
		m.set_meta(&"levels", c[4])

func _boss() -> void:
	var bm := Marker3D.new()
	bm.name = "BossSpawn"
	bm.position = DataZarael.BR_BOSS
	bm.set_meta(&"boss", &"deathspan_colossus")
	bm.set_meta(&"flag", DataZarael.F_BRIDGE)
	bm.add_to_group(&"boss_spawn")
	markers.add_child(bm)
	enemy_zone("summons_w", Vector3(-8.0, 0, DataZarael.BR_BOSS.z + 5.0), 3.5, [&"span_warden"], 2, 0.0)
	enemy_zone("summons_e", Vector3(8.0, 0, DataZarael.BR_BOSS.z + 5.0), 3.5, [&"span_warden"], 2, 0.0)

func _brazier(p: Vector3, energy := 2.8, shadow := false) -> void:
	var n := kit("zr_brazier_stone", p, rng.randf() * 360.0, 1.0, props)
	var f := socket_pos(n, "flame")
	flame(f, 1.1)
	light(f + Vector3(0, 0.5, 0), FIRE, energy, 11.0, shadow, true)

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the span's history on its safe margins — a few repaired plank patches let into the deck
# beside the parapets (flat, walkable, never across the lanes or under a ward pylon) and fallen masonry on the ledges.
# One silhouette, few unique pieces: no repeated railing props.

func _map_design() -> void:
	for k in [3, 9, 16, 24]:
		var z: float = SPAN_Z0 - SEG * (k + 0.5)
		var sx: float = -1.0 if k % 2 == 0 else 1.0
		kit("kd_planks", Vector3(sx * 4.0, -0.4, z + 1.0), 90.0 + k * 7.0, 0.9, deco)
	for c in [[Vector3(-8.5, GROUND_Y, SOUTH_GATE_Z + 7.0), 20.0], [Vector3(8.8, GROUND_Y, SOUTH_GATE_Z + 9.5), 160.0],
			[Vector3(-8.2, GROUND_Y, NORTH_GATE_Z - 8.0), 80.0], [Vector3(8.6, GROUND_Y, NORTH_GATE_Z - 11.0), 250.0]]:
		kit("kd_debris_stone", c[0], c[1], 1.4, deco)
	# ambient accents: wind across the span (rare and quiet: the fights carry their own sound)
	for z in [100.0, 30.0, -50.0]:
		accent(Vector3(0, 2.0, z), &"wind_gust", -18.0)
