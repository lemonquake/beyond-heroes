extends SettlementBuilder
## MAP — The Heart Citadel (bh-029; levels 46–52). "The Dawn Engine."
##
## The Wirewrights' temple-fortress beyond the Bridge of Death, built on a stepped rise: an outer court behind the south
## gate, a middle terrace 4 m up and the Engine Plaza 8 m up, each held by a row of carved retaining blocks
## (zr_terrace_4m) and climbed by triple stairs on the ceremonial avenue (zr_stair_4m) and single stairs at the sides.
## Citadel walls and towers ring it; the hills of the island's spine close round its back. The Dawn Engine stands at the
## north of the plaza inside the Leash-Abbot's arena (clear ground of HC_ARENA_R round DataZarael's arena centre), a
## ring of inlaid Heartwire marking its edge. The Kharvenn hold the place: a siege camp before the gate, tents in the
## courts, the Abbot's own camp behind the Engine with chain racks and rune-spikes (gone once the Heartwire is restored).
## Agdao's old wire lamps line the avenue, dark. Road bed: DataIsland `hc_road` (x = 0 from the gate to the Engine).
## Gameplay markers: spawns bridge_road / start, exit zone south (Bridge of Death), DawnEngine, boss_spawn (leash_abbot),
## summons_* zones, ten Kharvenn camps.

const X_WALL := 60.0                    # the side walls' centre line
const SOUTH_WALL_Z := 56.0              # the south wall and its gate
const NORTH_WALL_Z := -72.0
const GATE_TOWER_X := 11.6              # zr_citadel_tower (7 m) beside the gate arch (zr_gate_arch x 1.12: 18 m wide)
## Tiers: walking height and the z of the retaining row's south face (the row's blocks reach 8 m north of it).
const TIERS := [{"y": 0.0, "z1": 999.0}, {"y": 4.0, "z1": 30.0}, {"y": 8.0, "z1": 0.0}]
const STAIR_X := [-4.0, 0.0, 4.0, -40.0, 40.0]
const ARENA := Vector2(0.0, -28.0)       # the arena's centre (DataIsland hc_engine), radius DataZarael.HC_ARENA_R
const WARD := Color(1.0, 1.0, 1.0)
## Camps: [id, x, z, enemies, count, levels, elite chance]; levels climb from the gate to the Engine.
const CAMPS := [
	["siege_west", -20.0, 66.0, [&"chain_bearer", &"chain_priest", &"leash_knight"], 4, Vector2i(46, 47), 0.1],
	["siege_east", 21.0, 70.0, [&"leash_knight", &"chain_priest"], 3, Vector2i(46, 47), 0.1],
	["court_west", -42.0, 42.0, [&"gigas_spawn", &"chain_bearer", &"chain_priest"], 4, Vector2i(47, 48), 0.12],
	["court_east", 42.0, 40.0, [&"chain_bearer", &"chain_priest", &"heartwire_wraith"], 4, Vector2i(47, 48), 0.12],
	["terrace_west", -32.0, 14.0, [&"leash_knight", &"chain_priest", &"heartwire_wraith"], 4, Vector2i(48, 49), 0.15],
	["terrace_east", 32.0, 13.0, [&"gigas_spawn", &"chain_bearer", &"leash_knight"], 5, Vector2i(48, 49), 0.15],
	["plaza_west", -44.0, -16.0, [&"heartwire_wraith", &"chain_priest", &"leash_knight"], 5, Vector2i(49, 50), 0.18],
	["plaza_east", 44.0, -18.0, [&"leash_knight", &"chain_priest", &"gigas_spawn"], 5, Vector2i(49, 50), 0.18],
	["abbot_camp_west", -40.0, -58.0, [&"gigas_spawn", &"heartwire_wraith", &"leash_knight"], 5, Vector2i(50, 52), 0.22],
	["abbot_camp_east", 40.0, -58.0, [&"leash_knight", &"heartwire_wraith", &"chain_bearer"], 6, Vector2i(50, 52), 0.25],
]

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.026, 0.016, 0.029), "sky_horizon": Color(0.304, 0.17, 0.189),
		"ambient": Color(0.371, 0.325, 0.359), "ambient_energy": 0.85,
		"fog": Color(0.169, 0.109, 0.13), "fog_density": 0.006, "fog_height": -1.0, "fog_height_density": 0.08,
		"sun": Color(0.874, 0.668, 0.6), "sun_energy": 0.68, "sun_rot": Vector3(-42, 32, 0), "glow": 1.0,
		"exposure": 1.1, "contrast": 1.08, "saturation": 0.95,
	})
	prepare(-100.0, -85.0, 200, 170, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "red_clay", "moss": "blackwire_soil", "dirt": "cliff_ochre", "path": "terrace_paving", "rock": "cliff_ochre"},
		Color(0.92, 0.88, 0.86))
	_tiers()
	_plinth()
	_walls()
	_gate()
	_avenue()
	_engine()
	_siege_works()
	_hills()
	_camps()
	for gid in DataDungeons.gates_on(def.id):
		var gs: Dictionary = DataDungeons.get_def(gid).surface
		dungeon_gate(gid, gs.pos, gs.yaw)
	var s := DataZarael.HC_SOUTH
	spawn(&"bridge_road", Vector3(s.x, 0, s.z), 180.0, true)
	spawn(&"start", Vector3(s.x, 0, s.z), 180.0, true)
	exit_zone(&"citadel_south_road", Vector3(0, 0, 84.0), Vector3(16.0, 4.0, 2.0), &"bridge_of_death", &"citadel_road",
		"The Bridge of Death")
	# the approach is walled by its rock slopes; the map's south edge closes behind the exit
	for sx: float in [-1.0, 1.0]:
		boundary(Vector3(sx * 30.0, -1.0, SOUTH_WALL_Z + 2.0), Vector3(sx * 30.0, -1.0, 85.8), 10.0, 1.0)
	boundary(Vector3(-30.0, -1.0, 85.6), Vector3(30.0, -1.0, 85.6), 10.0, 1.0)
	set_bounds(AABB(Vector3(-100, -4, -85), Vector3(200, 50, 170)))
	view("overview", Vector3(0, 0, -2), 22.0, 40.0, 165.0, 45.0)
	view("topdown", Vector3(0, 0, 0), 0.0, 89.5, 150.0, 70.0)
	view("gate", Vector3(0, 3, 56), 0.0, 30.0, 48.0, 45.0)
	view("avenue", Vector3(0, 4, 20), 0.0, 34.0, 58.0, 45.0)
	view("engine", Vector3(0, 12, -38), 0.0, 28.0, 46.0, 45.0)
	view("arena", Vector3(0, 8, -28), 0.0, 60.0, 72.0, 45.0)
	view("siege_camp", Vector3(-16, 0, 66), -18.0, 44.0, 40.0, 45.0)
	view("abbot_camp", Vector3(0, 8, -60), 0.0, 48.0, 44.0, 45.0)
	view("game_gate", Vector3(0, 1.1, 62), 0.0, 54.0, 16.0, 40.0)
	view("game_stairs", Vector3(0, 5.1, 26), 0.0, 54.0, 18.0, 40.0)
	view("game_arena", Vector3(0, 9.1, -14), 0.0, 54.0, 20.0, 40.0)

# ------------------------------------------------------------------------------------------------------------
# landform

func tier_at(z: float) -> int:
	# the step up happens 1.6 m inside each retaining row, so the blocks' faces hide it
	for i in range(TIERS.size() - 1, -1, -1):
		if z + 1.6 < float(TIERS[i].z1):
			return i
	return 0

func tier_y(i: int) -> float:
	return float(TIERS[clampi(i, 0, TIERS.size() - 1)].y)

func _noise(x: float, z: float) -> float:
	return sin(x * 0.11 + z * 0.07) * 0.8 + cos(x * 0.05 - z * 0.13) * 1.0 + sin(x * 0.29 - z * 0.21) * 0.3

## How far (x, z) lies outside the rise's top: the walled precinct (|x| <= 62, z <= 58) and the approach ridge before
## the gate (|x| <= 30). 0 on top; the plinth of retaining blocks (PLINTH m wide) rings the top's edge.
const PLINTH := 8.0

func _edge_d(x: float, z: float) -> float:
	var ax := absf(x)
	var d_precinct := maxf(maxf(ax - (X_WALL + 2.0), z - (SOUTH_WALL_Z + 2.0)), 0.0)
	var d_ridge := maxf(ax - 30.0, 0.0) if z > SOUTH_WALL_Z + 2.0 else INF
	return minf(d_precinct, d_ridge)

## The Citadel crowns a stepped rise: flat tiers inside the walls, the approach ridge level with the gate, a ring of
## carved retaining blocks one step (4 m) down round the top's edge (_plinth), then the rock falls away into the haze.
## Behind the north wall the island's spine climbs as a mountain.
func _landform(x: float, z: float) -> float:
	if z < NORTH_WALL_Z - 2.0:
		var up := minf((NORTH_WALL_Z - 2.0 - z) * 1.4, 26.0)
		return tier_y(2) + up + _noise(x, z) * smoothstep(0.0, 6.0, up)
	var y := tier_y(tier_at(z))
	var d := _edge_d(x, z)
	if d <= 0.0:
		return y
	if d <= PLINTH:
		return y - 4.0                      # under the plinth blocks (their tops are the tier's floor)
	var fall := minf((d - PLINTH) * 1.5, 12.0) + minf(maxf(d - PLINTH - 8.0, 0.0) * 0.6, 14.0)
	return y - 4.0 - fall + _noise(x, z) * smoothstep(0.0, 6.0, fall)

func _shape(_x: float, _z: float, b: float, _rd: float, _rt: int) -> float:
	return b

func _inside(x: float, z: float) -> bool:
	return absf(x) < X_WALL - 1.8 and z < SOUTH_WALL_Z - 1.8 and z > NORTH_WALL_Z + 1.8

func _splat(x: float, z: float) -> Color:
	var n := sin(x * 0.27 + z * 0.19) * 0.5 + 0.5
	if _inside(x, z):
		# paved courts; Blackwire soil seeps out round the Engine and under the Kharvenn tents
		var e := Vector2(x, z).distance_to(Vector2(DataZarael.HC_ENGINE.x, DataZarael.HC_ENGINE.z))
		var seep := clampf((1.0 - smoothstep(9.0, 20.0, e)) * 0.7 + (n - 0.75) * 0.8, 0.0, 0.8)
		return Color(0.0, seep, 1.0 - seep * 0.6)
	var road := 1.0 - smoothstep(4.0, 7.0, absf(x)) if z > SOUTH_WALL_Z else 0.0
	var ochre := clampf(smoothstep(0.5, 5.0, absf(height_at(x, z) - tier_y(tier_at(z)))), 0.0, 1.0) * (1.0 - road)
	var soil := clampf(n * 0.5 - 0.1, 0.0, 1.0) * (1.0 - road) * (1.0 - ochre)
	return Color(ochre, soil, road * (0.75 + n * 0.25))

# ------------------------------------------------------------------------------------------------------------
# tiers, walls, the gate

## A piece whose own origin height is given (not set on the ground).
func _block(name: String, p: Vector3, yaw := 0.0, scale := 1.0) -> Node3D:
	return kit(name, p, yaw, scale, geo)

## Each upper tier's retaining row: 8 m blocks standing on the tier below (their tops are the upper tier's floor),
## end to end across the precinct and into the side walls; stairs climb their south faces.
func _tiers() -> void:
	for i in range(1, TIERS.size()):
		var lo := tier_y(i - 1)
		var z1: float = TIERS[i].z1
		var x := -X_WALL + 4.0
		while x <= X_WALL - 4.0 + 0.01:
			_block("zr_terrace_4m", Vector3(x, lo, z1 - 4.0))
			x += 8.0
		for sx: float in STAIR_X:
			# zr_stair_4m: bottom step at its origin, 4 m up over 7 m toward -Z, landing on the row's top edge
			_block("zr_stair_4m", Vector3(sx, lo, z1 + 7.0))
		for sx: float in [-1.0, 1.0]:
			# a tower either side of the grand stair, its back against the row: the guarded ascent to the next tier
			_block("zr_citadel_tower", Vector3(sx * 11.0, lo, z1 + 3.5), 0.0)
			# serpents at the stair's foot, a brazier beyond each tower
			kit("zr_serpent_statue", Vector3(sx * 7.6, lo, z1 + 8.3), 0.0, 0.9, props)
			_brazier(Vector3(sx * 16.5, lo, z1 + 7.0), 2.6)
			# one of the Wirewrights' lifts against the row, dead since the Dimming (its cage rests at the bottom)
			kit("zr_lift_platform", Vector3(sx * 24.0, lo, z1 + 2.8), 0.0, 1.0, props)

## The rise's stepped edge: a ring of retaining blocks one step below the top, round the precinct's sides, along the
## south wall and down both sides of the approach ridge. Each block's centre is placed so its ends meet the tier
## changes (z 28.4 and -1.6), where the plinth steps up 4 m with the tiers.
func _plinth() -> void:
	var sides := {0: [54.0, 46.0, 38.0, 32.4], 1: [24.4, 16.4, 8.4, 2.4], 2: [-5.6, -13.6, -21.6, -29.6, -37.6, -45.6, -53.6, -61.6, -69.6]}
	for sx: float in [-1.0, 1.0]:
		for t: int in sides:
			for z: float in sides[t]:
				_block("zr_terrace_4m", Vector3(sx * (X_WALL + 2.0 + PLINTH * 0.5), tier_y(t) - 4.0, z), 90.0 * sx)
		for x: float in [34.0, 42.0, 50.0, 58.0, 66.0]:
			_block("zr_terrace_4m", Vector3(sx * x, -4.0, SOUTH_WALL_Z + 2.0 + PLINTH * 0.5), 0.0)
		for z: float in [70.0, 78.0, 81.0]:
			_block("zr_terrace_4m", Vector3(sx * 34.0, -4.0, z), 90.0 * sx)

func _walls() -> void:
	# the south wall either side of the gate
	for sx: float in [-1.0, 1.0]:
		for i in 6:
			_block("zr_citadel_wall", Vector3(sx * (16.0 + 8.0 * i), 0.0, SOUTH_WALL_Z), 0.0)
	# the north wall behind the Engine
	for i in 15:
		_block("zr_citadel_wall", Vector3(-56.0 + 8.0 * i, tier_y(2), NORTH_WALL_Z), 0.0)
	# the side walls step up with the tiers; a tower stands at every step and at the corners
	for sx: float in [-1.0, 1.0]:
		var yaw := -90.0 * sx            # faces turned inward
		for zc: float in [48.5, 40.5, 32.5]:
			_block("zr_citadel_wall", Vector3(sx * X_WALL, tier_y(0), zc), yaw)
		for zc: float in [20.5, 12.5, 4.5]:
			_block("zr_citadel_wall", Vector3(sx * X_WALL, tier_y(1), zc), yaw)
		for k in 8:
			_block("zr_citadel_wall", Vector3(sx * X_WALL, tier_y(2), -9.5 - 8.0 * k), yaw)
		_block("zr_citadel_tower", Vector3(sx * X_WALL, tier_y(0), SOUTH_WALL_Z), 0.0)
		_block("zr_citadel_tower", Vector3(sx * X_WALL, tier_y(0), 28.0), yaw)
		_block("zr_citadel_tower", Vector3(sx * X_WALL, tier_y(1), -2.0), yaw)
		_block("zr_citadel_tower", Vector3(sx * X_WALL, tier_y(2), -36.0), yaw)
		_block("zr_citadel_tower", Vector3(sx * X_WALL, tier_y(2), NORTH_WALL_Z), 0.0)
		_block("zr_citadel_tower", Vector3(sx * 24.0, tier_y(2), NORTH_WALL_Z), 0.0)

func _gate() -> void:
	var arch_n := _block("zr_gate_arch", Vector3(0, 0, SOUTH_WALL_Z), 0.0, 1.12)
	for s in ["light_a", "light_b"]:
		light(socket_pos(arch_n, s), Color(1.0, 0.62, 0.32), 2.2, 9.0, false, true)
	for sx: float in [-1.0, 1.0]:
		_block("zr_citadel_tower", Vector3(sx * GATE_TOWER_X, 0.0, SOUTH_WALL_Z), 0.0)
	# the Kharvenn chained the gate's serpents and left their rune-spikes in the road
	for p: Vector2 in [Vector2(-7.5, 61.0), Vector2(7.8, 62.5)]:
		hide_when(kit("zr_chain_spike", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 1.0, props, true), DataZarael.F_RESTORED)

# ------------------------------------------------------------------------------------------------------------
# the ceremonial avenue and the Engine

func _avenue() -> void:
	# the Heartwire's channel inlaid down the avenue, from the gate to the stairs and on to the Engine
	for seg: Array in [[SOUTH_WALL_Z - 3.0, 38.0, 0], [21.0, 8.0, 1], [-2.0, -30.0, 2]]:
		var z: float = seg[0]
		var y := tier_y(seg[2]) + 0.05
		while z > float(seg[1]) + 1.9:
			decor("zr_wire_conduit_4m", Vector3(0, y, z - 2.0), 90.0, 1.0, false)
			z -= 4.0
	# glyph steles and Agdao's dark wire lamps line it on each tier
	for t: Array in [[0, [50.0, 43.0]], [1, [19.0, 11.0]]]:
		var y := tier_y(t[0])
		for z: float in t[1]:
			for sx: float in [-1.0, 1.0]:
				kit("zr_glyph_stele", Vector3(sx * 10.5, y, z), -90.0 * sx, 1.0, props)    # carved face toward the avenue
				kit("zr_wire_lamp", Vector3(sx * 6.5, y, z - 3.5), 0.0, 1.0, props)
		_brazier(Vector3(-10.5, y, float(t[1][0]) - 3.5), 2.4)
		_brazier(Vector3(10.5, y, float(t[1][0]) - 3.5), 2.4)
	# colonnades flanking the avenue (broken in the Kharvenn assault; each column's fallen twin lies beside it)
	for t: Array in [[0, [52.0, 45.5, 39.5]], [1, [21.0, 14.0]]]:
		for z: float in t[1]:
			for sx: float in [-1.0, 1.0]:
				kit("zr_ruin_column", Vector3(sx * 17.0, tier_y(t[0]), z), 90.0 + 90.0 * sx + rng.randf_range(-10.0, 10.0), 1.0, props)
	# the outer court's wire fountains (their water ran uphill while the Heartwire sang) and its dead relay masts
	for sx: float in [-1.0, 1.0]:
		var f := kit("zr_fountain_wire", Vector3(sx * 27.0, 0, 44.0), 0.0, 1.0, props)
		light(socket_pos(f, "light"), WARD, 1.6, 8.0, false, true)
		kit("zr_wire_pylon", Vector3(sx * 34.0, 0, 51.5), 0.0, 1.0, props)
	# relay pylons on the Engine Plaza, wrapped in Kharvenn rune-chains (gone once the Heartwire is restored)
	for sx: float in [-1.0, 1.0]:
		var p := Vector3(sx * 40.0, tier_y(2), -34.0)
		kit("zr_relay_pylon", p, 90.0 * sx, 1.0, props)
		hide_when(kit("zr_relay_chains", p, 90.0 * sx, 1.0, props), DataZarael.F_RESTORED)

func _engine() -> void:
	var y := tier_y(2)
	var e := DataZarael.HC_ENGINE
	var m := kit("zr_dawn_engine", Vector3(e.x, y, e.z), 0.0, 1.0, props)
	var de := DawnEngine.new().setup(m)
	de.position = Vector3(e.x, y, e.z)
	markers.add_child(de)
	# the arena's edge: an inlaid Heartwire ring on the plaza, braziers just outside it
	var r := DataZarael.HC_ARENA_R
	var n := 42
	for k in n:
		var a := TAU * (k + 0.5) / n
		decor("zr_wire_conduit_4m", Vector3(ARENA.x + cos(a) * r, y + 0.05, ARENA.y + sin(a) * r), rad_to_deg(-a) - 90.0, 1.0, false)
	for deg: float in [0.0, 50.0, 130.0, 180.0, 230.0, 310.0]:
		var a := deg_to_rad(deg)
		_brazier(Vector3(ARENA.x + cos(a) * (r + 2.2), y, ARENA.y + sin(a) * (r + 2.2)), 2.8, deg == 230.0)
	for deg: float in [25.0, 155.0, 205.0, 335.0]:
		var a := deg_to_rad(deg)
		var p := Vector2(ARENA.x + cos(a) * (r + 3.4), ARENA.y + sin(a) * (r + 3.4))
		kit("zr_glyph_stele", Vector3(p.x, y, p.y), rad_to_deg(atan2(-cos(a), -sin(a))), 1.1, props)
	# the Leash-Abbot and his adds
	var bm := Marker3D.new()
	bm.name = "BossSpawn"
	bm.position = Vector3(DataZarael.HC_ABBOT.x, y, DataZarael.HC_ABBOT.z)
	bm.set_meta(&"boss", &"leash_abbot")
	bm.set_meta(&"flag", DataZarael.F_ABBOT)
	bm.add_to_group(&"boss_spawn")
	markers.add_child(bm)
	enemy_zone("summons_w", Vector3(-12.0, y, -22.0), 3.5, [&"chain_priest", &"chain_bearer"], 3, 0.0)
	enemy_zone("summons_e", Vector3(12.0, y, -22.0), 3.5, [&"chain_priest", &"leash_knight"], 3, 0.0)

## Kharvenn tents, racks and rune-spikes: a siege camp before the gate, tents in the courts, and the Abbot's camp behind
## the Engine whose chains and spikes vanish once the Heartwire burns steady again.
func _siege_works() -> void:
	# before the gate
	for t: Array in [[Vector2(-21.0, 72.0), 25.0], [Vector2(-25.0, 62.5), 70.0], [Vector2(22.0, 75.0), -30.0], [Vector2(24.5, 64.0), -75.0]]:
		var p: Vector2 = t[0]
		kit("zr_kharvenn_tent", Vector3(p.x, 0, p.y), t[1], 1.0, props, true)
	for t: Array in [[Vector2(-13.0, 67.0), 80.0], [Vector2(14.0, 69.0), -70.0]]:
		var p: Vector2 = t[0]
		kit("zr_chain_rack", Vector3(p.x, 0, p.y), t[1], 1.0, props, true)
	_brazier(Vector3(-17.0, 0, 67.5), 2.6, false, true)
	_brazier(Vector3(18.0, 0, 70.0), 2.6, false, true)
	# in the outer court and on the middle terrace
	for t: Array in [[Vector3(-48.0, 0, 46.0), 30.0], [Vector3(-50.0, 0, 36.0), 70.0], [Vector3(48.0, 0, 46.5), -30.0],
			[Vector3(-49.0, 4, 11.0), 20.0], [Vector3(50.0, 4, 10.0), -15.0]]:
		kit("zr_kharvenn_tent", t[0], t[1], 1.0, props)
	for t: Array in [[Vector3(46.0, 0, 35.0), -90.0], [Vector3(-30.0, 4, 18.5), 0.0], [Vector3(30.0, 4, 18.0), 0.0]]:
		kit("zr_chain_rack", t[0], t[1], 1.0, props)
	_brazier(Vector3(-44.0, 0, 40.0), 2.4)
	_brazier(Vector3(44.0, 0, 40.5), 2.4)
	# the Abbot's camp behind the Engine (outside the arena)
	var y := tier_y(2)
	for t: Array in [[Vector3(-14.0, y, -63.0), 0.0], [Vector3(14.0, y, -63.0), 0.0], [Vector3(-36.0, y, -64.0), 15.0], [Vector3(38.0, y, -64.0), -15.0]]:
		kit("zr_kharvenn_tent", t[0], t[1], 1.0, props)
	for t: Array in [[Vector3(-4.5, y, -62.5), 0.0], [Vector3(4.5, y, -62.5), 0.0], [Vector3(-26.0, y, -58.0), 30.0], [Vector3(26.0, y, -58.0), -30.0]]:
		hide_when(kit("zr_chain_rack", t[0], t[1], 1.0, props), DataZarael.F_RESTORED)
	for k in 7:
		var a := deg_to_rad(205.0 + k * 21.5)
		var p := Vector2(DataZarael.HC_ENGINE.x + cos(a) * 17.5, DataZarael.HC_ENGINE.z + sin(a) * 17.5)
		if Vector2(p.x, p.y).distance_to(ARENA) < DataZarael.HC_ARENA_R + 1.0:
			continue
		hide_when(kit("zr_chain_spike", Vector3(p.x, y, p.y), rad_to_deg(-a), 1.0, props), DataZarael.F_RESTORED)
	for p: Vector2 in [Vector2(-31.0, -66.0), Vector2(31.0, -66.5), Vector2(-46.0, -48.0), Vector2(47.0, -46.0)]:
		hide_when(kit("zr_chain_spike", Vector3(p.x, y, p.y), rng.randf() * 360.0, 1.0, props), DataZarael.F_RESTORED)
	_brazier(Vector3(-9.0, y, -66.5), 2.6)
	_brazier(Vector3(9.0, y, -66.5), 2.6)
	scatter(["zr_glass_growth"], Rect2(-54, -70, 108, 18), 6, 8.0, Vector2(0.7, 1.1),
		func(x, z): return absf(x) < 20.0 or Vector2(x, z).distance_to(ARENA) < DataZarael.HC_ARENA_R + 3.0, true, true)

func _hills() -> void:
	# ochre outcrops on the falling slopes below the plinth and on the mountain behind the north wall
	var on_slope := func(x: float, z: float) -> bool:
		return z >= NORTH_WALL_Z - 4.0 and _edge_d(x, z) < PLINTH + 3.0
	scatter(["zr_rock_ochre_large", "zr_rock_ochre_medium"], Rect2(-100, -85, 200, 170), 80, 9.0, Vector2(1.0, 2.4), on_slope, true, true)
	scatter(["zr_glass_growth"], Rect2(-100, -85, 200, 170), 16, 14.0, Vector2(0.9, 1.5), on_slope, true, true)
	# agave and rocks along the approach ridge's edges
	scatter(["zr_rock_ochre_medium", "zr_agave"], Rect2(-30, 58, 60, 27), 16, 5.0, Vector2(0.7, 1.2),
		func(x, _z): return absf(x) < 12.0, true, false)
	# haze in the low ground round the rise
	mist(Rect2(-100, -85, 200, 170), -9.0, Color(0.42, 0.22, 0.32), 0.45)

func _camps() -> void:
	for c: Array in CAMPS:
		var m := enemy_zone(c[0], Vector3(c[1], 0, c[2]), 5.0, c[3], c[4], c[6], true)
		m.set_meta(&"levels", c[5])

func _brazier(p: Vector3, energy := 2.8, shadow := false, on_ground := false) -> void:
	var n := kit("zr_brazier_stone", p, rng.randf() * 360.0, 1.0, props, on_ground)
	var f := socket_pos(n, "flame")
	flame(f, 1.1)
	light(f + Vector3(0, 0.5, 0), FIRE, energy, 11.0, shadow, true)
