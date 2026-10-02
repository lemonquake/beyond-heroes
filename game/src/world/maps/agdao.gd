extends SettlementBuilder
## MAP — Agdao, the terraced harbour town of Zarael (bh-029; "Agdao" and "Zarael" are the author's names). Safe zone.
##
## Five stone terraces climb from the harbour to the Crown of Steps: the Harbour (pier, quay, fish market, Mother
## Ysenne's ward), the Wire Market (shops round a wire-wound fountain, the waypoint), the Middle Terrace (houses, the
## council hall), the Upper Terrace (houses, the old lifts, the Coilwood Gate east) and the Crown (the great stepped
## pyramid, Wirekeeper Halvessa Orn at its top). Retaining walls of carved glyph-stone hold each terrace; stairs climb
## them on the town's axis and at its sides; footbridges join the roof terraces of the tall houses. The Heartwire runs
## through all of it in inlaid channels and pylons — dim white while Zarael is corrupted, bright white once the Dawn Engine
## wakes (MaterialLibrary.wire_restored). Every spot the quests and NPCs use comes from DataZarael; the road beds
## follow DataIsland's Zarael polylines.

## Terraces from the harbour up: walking height, south edge z (z1), north edge z (z0), west and east x.
const TIERS := [
	{"y": 1.6, "z0": 30.0, "z1": 50.0, "x0": -78.0, "x1": 62.0},
	{"y": 5.6, "z0": 6.0, "z1": 30.0, "x0": -72.0, "x1": 68.0},
	{"y": 9.6, "z0": -20.0, "z1": 6.0, "x0": -66.0, "x1": 72.0},
	{"y": 13.6, "z0": -44.0, "z1": -20.0, "x0": -58.0, "x1": 88.0},
	{"y": 17.6, "z0": -84.0, "z1": -44.0, "x0": -42.0, "x1": 42.0},
]
## Stairs up each terrace wall: [x, tier below]. Two side by side on the town's axis make the grand stairs.
const STAIRS := [[-22.0, 0], [-18.0, 0], [40.0, 0], [-2.0, 1], [2.0, 1], [-50.0, 1], [-2.0, 2], [2.0, 2], [40.0, 2],
	[-2.0, 3], [2.0, 3], [-28.0, 3]]
const SEA_Y := 0.0
const PYRAMID := Vector3(0, 0, -70)     # its stair's foot lands on the upper terrace's front edge (z -44)
const FOUNTAIN := Vector2(0, 20)
const LIFT_X := 52.0
const HALL := Vector2(-30, -14)
## Houses: [x, z, kind (a/b/c), yaw]. Two-storey "c" houses carry roof terraces joined by footbridges (BRIDGES).
const HOUSES := [
	# harbour
	[-62.0, 35.0, "a", 0.0], [-46.0, 34.5, "b", 0.0], [2.0, 34.5, "c", 0.0], [26.0, 34.5, "a", 0.0], [52.0, 35.0, "b", 0.0],
	# market terrace (back row against the middle terrace wall)
	[-62.0, 10.5, "b", 0.0], [-38.0, 10.5, "c", 0.0], [-26.0, 10.5, "a", 0.0], [24.0, 10.5, "c", 0.0], [36.0, 10.5, "b", 0.0], [58.0, 10.5, "a", 0.0],
	# middle terrace
	[-56.0, -15.0, "a", 0.0], [-12.0, -1.0, "c", 0.0], [12.0, -1.0, "c", 0.0], [26.0, -15.0, "b", 0.0], [62.0, -14.0, "a", 0.0],
	[-50.0, -1.0, "c", 0.0], [24.0, 0.0, "a", 0.0], [58.0, 0.0, "b", 0.0],
	# upper terrace
	[-48.0, -38.5, "b", 0.0], [-14.0, -27.0, "c", 0.0], [14.0, -27.0, "c", 0.0], [30.0, -39.0, "a", 0.0], [44.0, -39.0, "b", 0.0],
	[66.0, -38.0, "a", 0.0], [-40.0, -26.0, "a", 0.0],
]
## Footbridges between neighbouring two-storey houses' roof terraces: pairs of HOUSES indices.
const BRIDGES := [[12, 13], [20, 21]]
## Market stalls: [x, z, kind, yaw] (Dorrit's and Brisa's stand where their NPCs are, DataNpcsZarael).
const STALLS := [[-12.0, 24.0, "a", 0.0], [12.0, 24.0, "b", 0.0], [-24.0, 22.0, "b", 20.0], [20.0, 14.0, "a", -20.0],
	[10.0, 42.5, "b", 0.0], [20.0, 42.5, "a", 0.0]]

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.03, 0.03, 0.06), "sky_horizon": Color(0.3, 0.22, 0.22),
		"ambient": Color(0.42, 0.4, 0.44), "ambient_energy": 0.9,
		"fog": Color(0.2, 0.16, 0.16), "fog_density": 0.004, "fog_height": -2.0, "fog_height_density": 0.06,
		"sun": Color(1.0, 0.82, 0.68), "sun_energy": 0.75, "sun_rot": Vector3(-38, 30, 0), "glow": 0.95,
		"exposure": 1.1, "contrast": 1.08, "saturation": 0.95,
	})
	prepare(-110.0, -110.0, 220, 230, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "jungle_floor", "moss": "jungle_floor", "dirt": "red_clay", "path": "terrace_paving", "rock": "cliff_ochre"},
		Color(0.92, 0.9, 0.88))
	_sea()
	_terrace_walls()
	_stairs()
	_pier_and_ship()
	_harbour()
	_market()
	_houses()
	_council()
	_lifts()
	_crown()
	_gate()
	_heartwire()
	_hills()
	_map_design()
	spawn(&"pier", Vector3(DataZarael.AG_SPAWN.x, DataZarael.AG_DECK_Y, DataZarael.AG_SPAWN.z), 180.0)
	spawn(&"start", Vector3(-20.0, 0, 40.0), 180.0, true)
	spawn(&"coil_gate", DataZarael.AG_GATE_SPAWN, -90.0, true)
	set_bounds(AABB(Vector3(-92, -6, -96), Vector3(184, 60, 182)))
	view("overview", Vector3(0, 8, -10), 0.0, 55.0, 150.0, 45.0)
	view("topdown", Vector3(0, 0, -14), 0.0, 89.5, 175.0, 50.0)
	view("harbour", Vector3(-14, 2, 42), 0.0, 42.0, 32.0)
	view("market", Vector3(0, 6, 16), 0.0, 46.0, 34.0)
	view("terraces", Vector3(0, 10, -6), 20.0, 30.0, 60.0, 45.0)
	view("crown", Vector3(0, 20, -56), 0.0, 32.0, 48.0, 45.0)
	view("pyramid_top", Vector3(0, 34, -70), 0.0, 40.0, 20.0, 45.0)
	view("gate", Vector3(74, 14, -26), -50.0, 40.0, 26.0, 45.0)

# ------------------------------------------------------------------------------------------------------------
# landform

func tier_at(z: float) -> int:
	for i in TIERS.size():
		if z >= float(TIERS[i].z0):
			return i
	return TIERS.size() - 1

func tier_y(i: int) -> float:
	return float(TIERS[clampi(i, 0, TIERS.size() - 1)].y)

func _noise(x: float, z: float) -> float:
	return sin(x * 0.11 + z * 0.07) * 0.6 + cos(x * 0.05 - z * 0.13) * 0.8

func _landform(x: float, z: float) -> float:
	# the step to the next terrace up happens just inside its retaining wall, so the wall's face hides it
	var i := tier_at(z + 1.6)
	var t: Dictionary = TIERS[i]
	var y := float(t.y)
	# beyond a terrace's ends the hills climb steeply (jungle slopes, not walkable)
	var over := maxf(float(t.x0) - x, x - float(t.x1))
	if over > 0.0:
		y += minf(over * 1.5, 18.0) + _noise(x, z) * smoothstep(0.0, 8.0, over)
	# the harbour runs out to the quay; below it the sea floor
	if z > 50.5:
		var sea := -3.5 + _noise(x, z) * 0.3
		y = lerpf(y, sea, smoothstep(50.5, 53.0, z)) if over <= 0.0 else maxf(lerpf(y, sea, smoothstep(50.5, 62.0, z)), sea)
	# behind the crown, the mountain
	if z < -84.0:
		y += (-84.0 - z) * 1.2
	return y

func _shape(_x: float, _z: float, b: float, _rd: float, _rt: int) -> float:
	return b

func _splat(x: float, z: float) -> Color:
	var i := tier_at(z + 1.6)
	var t: Dictionary = TIERS[i]
	var over := maxf(float(t.x0) - x, x - float(t.x1))
	var n := sin(x * 0.31 + z * 0.19) * 0.5 + 0.5
	var paved := 1.0 - smoothstep(-2.0, 1.0, over)
	if z > 50.5 or z < -84.0:
		paved = 0.0
	var clay := clampf(smoothstep(0.0, 6.0, over) * 0.4 + n * 0.15, 0.0, 1.0) * (1.0 - paved)
	var jungle := clampf(smoothstep(2.0, 10.0, over), 0.0, 1.0) * (1.0 - paved)
	return Color(clay, jungle, paved * (0.85 + n * 0.15))

# ------------------------------------------------------------------------------------------------------------
# sea, walls, stairs

func _sea() -> void:
	water(Rect2(-220, 50, 440, 170), SEA_Y, Color(0.12, 0.42, 0.46), Color(0.02, 0.07, 0.1), 0.5, 3.0, 0.35)
	mist(Rect2(-220, 64, 440, 150), SEA_Y + 1.2, Color(0.32, 0.22, 0.32), 0.35)
	# the quay wall along the harbour's sea edge
	var t: Dictionary = TIERS[0]
	var x := float(t.x0) + 4.0
	while x < float(t.x1) - 2.0:
		if absf(x - DataZarael.AG_PIER_X) > 4.0:
			_block("zr_terrace_2m", Vector3(x, tier_y(0) - 2.0, 50.0 - 4.0))
		x += 8.0
	# rocks and a lighthouse-like wire pylon at the harbour mouth
	for p: Vector2 in [Vector2(-84, 56), Vector2(-74, 60), Vector2(66, 56), Vector2(76, 62), Vector2(-96, 52), Vector2(90, 54)]:
		kit("zr_rock_ochre_large", Vector3(p.x, -2.5, p.y), rng.randf() * 360.0, rng.randf_range(1.0, 1.6), deco)
	var beacon := kit("zr_wire_pylon", Vector3(70.0, 0.4, 58.0), 0.0, 1.3, props)
	light(socket_pos(beacon, "light"), Color(1.0, 1.0, 1.0), 3.2, 16.0, false, true)
	# fishing boats at anchor
	for b: Array in [[Vector3(-46, SEA_Y, 66), 20.0], [Vector3(-60, SEA_Y, 74), -40.0], [Vector3(28, SEA_Y, 70), 70.0], [Vector3(40, SEA_Y, 60), 10.0]]:
		decor("boat_rowing", b[0], b[1], 1.3, false, true)

## A terrace block, a stair or any other piece whose own origin height is given (not set on the ground).
func _block(name: String, p: Vector3, yaw := 0.0) -> Node3D:
	if not ResourceLoader.exists(ENV_DIR % name):
		return null
	return kit(name, p, yaw, 1.0, geo)

## Each terrace's south edge is a row of 8 m retaining blocks standing on the terrace below (their tops are the upper
## terrace's floor). Where the terrace below is narrower the hill hides the ends.
func _terrace_walls() -> void:
	for i in range(1, TIERS.size()):
		var up: Dictionary = TIERS[i]
		var lo: Dictionary = TIERS[i - 1]
		var x0 := maxf(float(up.x0), float(lo.x0) - 2.0)
		var x1 := minf(float(up.x1), float(lo.x1) + 2.0)
		var x := x0 + 4.0
		while x <= x1 - 4.0 + 0.01:
			_block("zr_terrace_4m", Vector3(x, float(lo.y), float(up.z1) - 4.0))
			x += 8.0

func _stairs() -> void:
	for s: Array in STAIRS:
		var x: float = s[0]
		var i: int = s[1]
		var lo: Dictionary = TIERS[i]
		var up: Dictionary = TIERS[i + 1]
		# zr_stair_4m: bottom step at its origin (+Z edge), 4 m up over 7 m toward -Z, landing on the wall's top
		_block("zr_stair_4m", Vector3(x, float(lo.y), float(up.z1) + 7.0))
		keep_clear(x, float(up.z1) + 4.0, 4.5)
	# serpent heads at the foot of the grand stairs
	for i in range(0, TIERS.size() - 1):
		var up: Dictionary = TIERS[i + 1]
		var lo: Dictionary = TIERS[i]
		var ax := -20.0 if i == 0 else 0.0
		for sx: float in [-5.6, 5.6]:
			kit("zr_serpent_statue", Vector3(ax + sx, float(lo.y), float(up.z1) + 7.6), 0.0, 0.8, props)

# ------------------------------------------------------------------------------------------------------------
# harbour

func _pier_and_ship() -> void:
	var px := DataZarael.AG_PIER_X
	var z := DataZarael.AG_PIER_Z.x + 2.0
	while z < DataZarael.AG_PIER_Z.y - 2.0:
		_block("zr_pier_4m", Vector3(px, DataZarael.AG_DECK_Y, z))
		z += 4.0
	_block("zr_pier_end", Vector3(px, DataZarael.AG_DECK_Y, z), 0.0)
	# rails along the pier: nobody walks off into the harbour
	var d := DataZarael.AG_DECK_Y
	boundary(Vector3(px - 2.7, d - 3.0, DataZarael.AG_PIER_Z.x + 4.0), Vector3(px - 2.7, d - 3.0, DataZarael.AG_PIER_Z.y + 2.0), 7.0, 0.4)
	boundary(Vector3(px + 2.7, d - 3.0, DataZarael.AG_PIER_Z.x + 4.0), Vector3(px + 2.7, d - 3.0, DataZarael.AG_SPAWN.z - 2.0), 7.0, 0.4)
	boundary(Vector3(px + 2.7, d - 3.0, DataZarael.AG_SPAWN.z + 2.0), Vector3(px + 2.7, d - 3.0, DataZarael.AG_PIER_Z.y + 2.0), 7.0, 0.4)
	boundary(Vector3(px - 2.7, d - 3.0, DataZarael.AG_PIER_Z.y + 2.2), Vector3(px + 2.7, d - 3.0, DataZarael.AG_PIER_Z.y + 2.2), 7.0, 0.4)
	# the Sunwake lies east of the pier, her gangplank on the pier at the arrival spot
	var s := DataZarael.AG_SHIP
	if ResourceLoader.exists(ENV_DIR % "zr_ship"):
		var ship := kit("zr_ship", Vector3(s.x, SEA_Y + 0.1, s.z), 0.0, 1.0, props)
		ship.add_to_group(&"zr_ship_model")
	kit("dock_planks", Vector3(px + 3.6, d + 0.25, DataZarael.AG_SPAWN.z), 90.0, 0.8, deco)
	boundary(Vector3(px + 4.6, d - 3.0, DataZarael.AG_SPAWN.z - 2.0), Vector3(px + 4.6, d - 3.0, DataZarael.AG_SPAWN.z + 2.0), 7.0, 0.4)
	for sz: float in [-1.0, 1.0]:
		light(Vector3(s.x, SEA_Y + 4.0, s.z + sz * 9.5), Color(1.0, 1.0, 1.0), 1.8, 8.0, false, true)
	# Terax's post at the pier head: two braziers either side of the harbour stair's foot
	for sx: float in [-4.4, 4.4]:
		brazier(Vector3(px + sx, tier_y(0), DataZarael.AG_TERAX.z - 2.0), 3.2, false, false)

func _harbour() -> void:
	var y := tier_y(0)
	# Mother Ysenne's ward: a lamp and benches before her house (the house itself is in HOUSES)
	kit("zr_wire_lamp", Vector3(-41.5, y, 39.5), 0.0, 1.0, props)
	decor("bench", Vector3(-50.0, y, 40.5), 0.0, 1.0, false, true)
	# the fish market by the quay
	for p: Vector2 in [Vector2(6, 46), Vector2(24, 46.5), Vector2(-4, 44)]:
		decor("barrel", Vector3(p.x, y, p.y), rng.randf() * 360.0, 1.0, false, true)
		decor("crate", Vector3(p.x + 1.4, y, p.y + 0.6), rng.randf() * 360.0, 0.9, false, true)
	for p: Vector2 in [Vector2(-34, 46), Vector2(36, 46), Vector2(-56, 46)]:
		decor("fishing_nets", Vector3(p.x, y, p.y), 0.0, 1.0, false, true)
	kit("zr_brazier_stone", Vector3(30.0, y, 40.0), 0.0, 1.0, props)
	flame(Vector3(30.0, y + 1.5, 40.0), 0.8)
	light(Vector3(30.0, y + 2.2, 40.0), Color(1.0, 0.6, 0.3), 2.6, 9.0, false, true)

# ------------------------------------------------------------------------------------------------------------
# the Wire Market

func _market() -> void:
	var y := tier_y(1)
	var fo := kit("zr_fountain_wire", Vector3(FOUNTAIN.x, y, FOUNTAIN.y), 0.0, 1.0, props)
	light(socket_pos(fo, "light"), Color(1.0, 1.0, 1.0), 3.0, 12.0, false, true)
	keep_clear(FOUNTAIN.x, FOUNTAIN.y, 4.0)
	for st: Array in STALLS:
		var sy := tier_y(tier_at(float(st[1]) + 1.6))
		var n := kit("zr_market_stall_%s" % st[2], Vector3(st[0], sy, st[1]), st[3], 1.0, props)
		if n and n.find_child("light", true, false):
			light(socket_pos(n, "light"), Color(1.0, 0.62, 0.32), 1.8, 7.0, false, true)
	# the waypoint at the market's east end
	var sp := DataZarael.AG_SHRINE
	apron(sp, y + 0.02, 3.4, "stone_floor")
	var tp := teleporter(&"agdao_shrine", Vector3(sp.x, y + 0.05, sp.y), &"wyman_outpost", &"wyman_shrine", "Wyman Outpost")
	tp.rune_tint = Color(0.95, 0.75, 0.4)
	spawn(&"agdao_shrine", Vector3(sp.x - 3.2, y, sp.y + 1.8), -110.0)
	for a: float in [0.6, 2.2, 3.8, 5.4]:
		kit("zr_glyph_stele", Vector3(sp.x + cos(a) * 4.6, y, sp.y + sin(a) * 4.6), rad_to_deg(-a) + 90.0, 0.55, props)
	# crafting, the vault and a practice post at the market's west end
	crafting_station(&"alchemy", Vector3(16.0, y, 22.0), "Brisa's Brewing Table", false)
	crafting_station(&"forge", Vector3(-30.0, y, 16.0), "Agdao Glass Forge", false)
	crafting_station(&"workbench", Vector3(-36.0, y, 20.0), "Wire-mender's Bench", false)
	kit("stand_vault", Vector3(48.0, y, 18.0), -90.0, 1.0, props)
	var vp := VaultPoint.new()
	vp.position = Vector3(45.8, y, 18.0)
	markers.add_child(vp)
	keep_clear(48.0, 18.0, 4.0)
	for p: Vector2 in [Vector2(-8, 28), Vector2(8, 28), Vector2(-30, 26), Vector2(30, 26), Vector2(-50, 24), Vector2(52, 24)]:
		_lamp(Vector3(p.x, y, p.y))
	signpost(Vector2(-5.0, 27.0), [["Harbour · the Sunwake", Vector2(-0.6, 1)], ["Crown of Steps", Vector2(0, -1)], ["Waypoint", Vector2(1, 0)]], y)

func _lamp(p: Vector3) -> void:
	var n := kit("zr_wire_lamp", p, 0.0, 1.0, props)
	if n and n.find_child("light", true, false):
		light(socket_pos(n, "light"), Color(1.0, 1.0, 1.0), 1.6, 7.5, false, false)

# ------------------------------------------------------------------------------------------------------------
# houses, the council hall, the lifts

func _houses() -> void:
	var placed := []
	for h: Array in HOUSES:
		var y := tier_y(tier_at(float(h[1]) + 1.6))
		var n := kit("zr_house_%s" % h[2], Vector3(h[0], y, h[1]), h[3], 1.0, geo)
		placed.append(n)
		keep_clear(h[0], h[1], 6.0)
		if n and n.find_child("door_light", true, false):
			light(socket_pos(n, "door_light"), Color(1.0, 0.62, 0.32), 1.4, 6.0, false, true)
	for b: Array in BRIDGES:
		var a: Node3D = placed[b[0]]
		var c: Node3D = placed[b[1]]
		if a == null or c == null or not a.find_child("roof", true, false) or not c.find_child("roof", true, false):
			continue
		var ra := socket_pos(a, "roof")
		var rc := socket_pos(c, "roof")
		var mid := (ra + rc) * 0.5
		var span := Vector2(ra.x, ra.z).distance_to(Vector2(rc.x, rc.z))
		var yaw := rad_to_deg(atan2(-(rc.z - ra.z), rc.x - ra.x))
		kit("zr_footbridge_8m", Vector3(mid.x, mid.y, mid.z), yaw, maxf(0.6, span / 8.0 * 0.5), geo)

func _council() -> void:
	var y := tier_y(2)
	var n := kit("zr_hall_council", Vector3(HALL.x, y, HALL.y), 0.0, 1.0, geo)
	keep_clear(HALL.x, HALL.y, 11.0)
	if n:
		for s in ["light_a", "light_b"]:
			if n.find_child(s, true, false):
				var p := socket_pos(n, s)
				flame(p, 0.8)
				light(p + Vector3(0, 0.6, 0), Color(1.0, 0.6, 0.3), 2.4, 8.0, false, true)
	for p: Vector2 in [Vector2(-14, -4), Vector2(14, -4), Vector2(-40, -4), Vector2(40, -4)]:
		_lamp(Vector3(p.x, y, p.y))

func _lifts() -> void:
	# the old lifts: one between the market and the middle terrace, one up to the upper terrace (still; they wait for the current)
	for l: Array in [[LIFT_X, 1], [LIFT_X, 2]]:
		var lo: Dictionary = TIERS[l[1]]
		var up: Dictionary = TIERS[l[1] + 1]
		var n := kit("zr_lift_platform", Vector3(l[0], float(lo.y), float(up.z1) + 2.2), 0.0, 1.0, props)
		keep_clear(l[0], float(up.z1) + 2.0, 4.0)
		if n and n.find_child("light", true, false):
			light(socket_pos(n, "light"), Color(1.0, 1.0, 1.0), 1.8, 7.0, false, true)

# ------------------------------------------------------------------------------------------------------------
# the Crown of Steps

func _crown() -> void:
	var y := tier_y(4)
	var py := kit("zr_step_pyramid", Vector3(PYRAMID.x, y, PYRAMID.z), 0.0, 1.0, geo)
	keep_clear(PYRAMID.x, PYRAMID.z, 20.0)
	if py and py.find_child("light", true, false):
		light(socket_pos(py, "light"), Color(1.0, 1.0, 1.0), 4.5, 24.0, true, true)
	# the avenue to the pyramid: steles, serpents, braziers and pylons
	for sx: float in [-1.0, 1.0]:
		for k in 2:
			kit("zr_glyph_stele", Vector3(sx * (8.0 + k * 6.0), y, -48.5 - k * 2.0), 0.0, 1.0, props)
		var pyl := kit("zr_wire_pylon", Vector3(sx * 24.0, y, -54.0), 0.0, 1.0, props)
		if pyl and pyl.find_child("light", true, false):
			light(socket_pos(pyl, "light"), Color(1.0, 1.0, 1.0), 2.6, 12.0, false, true)
		brazier(Vector3(sx * 6.0, y, -46.0), 3.2, false, false)
		kit("zr_planter", Vector3(sx * 30.0, y, -50.0), 0.0, 1.0, props)
	signpost(Vector2(6.5, -40.0), [["Crown of Steps", Vector2(0, -1)], ["Coilwood Gate", Vector2(1, 0)], ["Wire Market", Vector2(0, 1)]], tier_y(3))

func _gate() -> void:
	var y := tier_y(3)
	var g := DataZarael.AG_GATE
	var n := kit("zr_gate_arch", Vector3(g.x, y, g.y), 90.0, 1.0, geo)
	if n:
		for s in ["light_a", "light_b"]:
			if n.find_child(s, true, false):
				light(socket_pos(n, s), Color(1.0, 1.0, 1.0), 2.0, 8.0, false, true)
	# town wall north and south of the gate, closing the terrace's east end
	var t: Dictionary = TIERS[3]
	for zz in [float(t.z0) + 2.0, float(t.z0) + 6.0, float(t.z0) + 10.0]:
		kit("zr_wall_4m", Vector3(g.x, y, zz), 90.0, 1.0, geo)
	for zz in [-22.0, -18.0]:
		kit("zr_wall_4m", Vector3(g.x, y, zz), 90.0, 1.0, geo)
	exit_zone(&"agdao_coil_gate", Vector3(g.x + 5.0, 0, g.y), Vector3(3.0, 5.0, 9.0), &"zr_coilwood", &"agdao_road", "The Coilwood")
	corridor_rails([Vector2(g.x - 2.0, g.y), Vector2(g.x + 7.0, g.y)], 4.6)
	keep_clear(g.x, g.y, 7.0)

# ------------------------------------------------------------------------------------------------------------
# the Heartwire, the hills

func _heartwire() -> void:
	# conduits along the main stair axis and the terraces' front edges, pylons at the terrace corners
	for i in TIERS.size():
		var t: Dictionary = TIERS[i]
		var y := float(t.y) + 0.02
		var z := float(t.z1) - 1.0 if i > 0 else 48.0
		var x := float(t.x0) + 6.0
		while x < float(t.x1) - 6.0:
			var clear := true
			for s: Array in STAIRS:
				if (int(s[1]) == i - 1) and absf(x - float(s[0])) < 4.0:
					clear = false
			if clear and absf(x - DataZarael.AG_PIER_X) > 4.0:
				decor("zr_wire_conduit_4m", Vector3(x, y, z), 90.0, 1.0, false, false)
			x += 4.0
	for i in range(1, TIERS.size()):
		var t: Dictionary = TIERS[i]
		for xx: float in [float(t.x0) + 3.0, float(t.x1) - 3.0]:
			if xx > 80.0:
				continue
			var p := kit("zr_wire_pylon", Vector3(xx, float(t.y), float(t.z1) - 2.5), 0.0, 0.9, props)
			if p and p.find_child("light", true, false) and i % 2 == 0:
				light(socket_pos(p, "light"), Color(1.0, 1.0, 1.0), 2.0, 10.0, false, true)

func _hills() -> void:
	# jungle on the slopes either side of the town and the mountain behind the Crown
	# map-design pass: a lighter even scatter; _map_design() adds canopy and rock clusters that follow the grade
	scatter(["zr_tree_ceiba", "zr_palm", "zr_palm", "zr_fern_giant", "zr_bush_jungle"], Rect2(-110, -110, 220, 162), 200, 7.0,
		Vector2(0.8, 1.25), func(x, z):
			var i := tier_at(z + 1.6)
			var t: Dictionary = TIERS[i]
			return maxf(float(t.x0) - x, x - float(t.x1)) < 3.0 and z > -84.0)
	for i in 40:
		var side := -1.0 if i % 2 == 0 else 1.0
		var z := -84.0 + rng.randf() * 134.0
		var t: Dictionary = TIERS[tier_at(z + 1.6)]
		var x := (float(t.x0) - rng.randf_range(4.0, 20.0)) if side < 0.0 else (float(t.x1) + rng.randf_range(4.0, 20.0))
		decor("zr_rock_ochre_medium", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.8, 1.6), true, true)
	# keep the hero on the town: invisible walls where the terraces meet the slopes
	for i in TIERS.size():
		var t: Dictionary = TIERS[i]
		var y := float(t.y)
		boundary(Vector3(float(t.x0) - 0.5, y - 2.0, float(t.z0)), Vector3(float(t.x0) - 0.5, y - 2.0, float(t.z1)), 10.0)
		if i != 3:
			boundary(Vector3(float(t.x1) + 0.5, y - 2.0, float(t.z0)), Vector3(float(t.x1) + 0.5, y - 2.0, float(t.z1)), 10.0)
	var top: Dictionary = TIERS[4]
	boundary(Vector3(float(top.x0), tier_y(4) - 2.0, float(top.z0) + 0.5), Vector3(float(top.x1), tier_y(4) - 2.0, float(top.z0) + 0.5), 10.0)

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): each terrace dressed for what it does — cargo sorted on the quay with a repaired landing
# and boats moored off it, the Wire Market's stock under cover and seats at its margins, a civic porch at the council
# hall, maintenance stores by the old lifts, sparse stone and planting at the Crown's edges. Every group stands on its
# own terrace at that terrace's height (never grounded to the terrain under a raised surface), off the town's routes,
# stair landings, lifts, doors and the procession to the pyramid. Glow stays white: nothing here adds a light.

var _want_tier := 0

func _clear_here(x: float, z: float, r: float) -> bool:
	var i := tier_at(z + 1.6)
	if i != _want_tier:
		return false
	var t: Dictionary = TIERS[i]
	var south := float(t.z1) - (1.0 if i == 0 else 2.6)
	if x < float(t.x0) + r + 1.0 or x > float(t.x1) - r - 1.0 or z < float(t.z0) + r * 0.6 + 0.4 or z > south - r:
		return false
	if absf(x - DataZarael.AG_PIER_X) < r + 4.0 and i == 0 and z > 40.0:
		return false
	return road_dist(x, z) > r + 1.8 and is_clear(x, z, r * 0.6)

## A group on terrace `i`: the nearest clear spot to `prefer` within `reach`, standing at the terrace's height.
func _on_tier(i: int, vname: String, prefer: Vector2, reach: float, yaw: float, opts := {}) -> Node3D:
	_want_tier = i
	var y := tier_y(i)
	return place_near(vname, Vector3(prefer.x, y, prefer.y), Vector3(prefer.x, y, prefer.y), 0.0, reach, yaw, opts.merged({"on_ground": false}))

func _map_design() -> void:
	clear_fn = _clear_here
	# ---- the Harbour: a handling corner on the quay, a repaired landing, rowboats moored off it, sparse palms -----
	_on_tier(0, "cargo_stack", Vector2(-32.0, 44.0), 8.0, 0.0)
	_on_tier(0, "supply_corner", Vector2(-8.0, 41.5), 8.0, 10.0)
	# the repaired landing: new planks let into the old quay edge, a paddle left on them (flat: the quay stays walkable)
	for c in [[Vector3(-60.0, tier_y(0) - 0.32, 48.6), 0.0, "kd_planks"], [Vector3(-57.6, tier_y(0) + 0.06, 48.2), 80.0, "kd_paddle"]]:
		kit(c[2], c[0], c[1], 1.0, deco)
	vignette("moored_rowboat", Vector3(-55.0, SEA_Y + 0.05, 53.5), 80.0, {"on_ground": false, "check": false})
	vignette("moored_rowboat", Vector3(14.0, SEA_Y + 0.05, 54.0), 100.0, {"on_ground": false, "check": false})
	_on_tier(0, "palm_pair", Vector2(-72.0, 36.0), 5.0, 0.0)
	_on_tier(0, "palm_pair", Vector2(56.0, 40.0), 9.0, 180.0)
	_on_tier(0, "bench_view", Vector2(-52.0, 41.0), 8.0, 180.0)
	# ---- the Wire Market: stock under cover at the margins, seats facing the fountain, planter pockets ----------
	_on_tier(1, "covered_store", Vector2(-46.0, 12.5), 7.0, 0.0)
	_on_tier(1, "produce_display", Vector2(-15.5, 21.5), 4.0, 30.0)
	_on_tier(1, "herb_pots", Vector2(16.0, 26.0), 6.0, -20.0)
	_on_tier(1, "cargo_stack", Vector2(44.0, 12.0), 7.0, 0.0)
	# waiting seats on the market's north margin, looking south over the fountain and the harbour
	for q in [Vector2(-12.0, 9.0), Vector2(12.0, 9.0)]:
		_on_tier(1, "bench_view", q, 7.0, 0.0)
	for q in [Vector2(-34.0, 25.0), Vector2(36.0, 24.5), Vector2(-58.0, 22.0)]:
		_on_tier(1, "civic_planters", q, 8.0, 0.0)
	# ---- the Middle Terrace: the council porch, domestic courtyards and service corners -------------------------
	_on_tier(2, "civic_record", Vector2(HALL.x + 9.0, HALL.y + 9.5), 5.0, 0.0)
	_on_tier(2, "civic_planters", Vector2(HALL.x - 9.0, HALL.y + 10.0), 5.0, 0.0)
	_on_tier(2, "garden_bed", Vector2(-4.0, -7.0), 6.0, 0.0)
	_on_tier(2, "flower_border", Vector2(32.0, -6.0), 6.0, 0.0)
	_on_tier(2, "supply_corner", Vector2(50.0, -17.5), 6.0, 0.0)
	# ---- the Upper Terrace: stores for the lifts' upkeep, gardens that soften the stone -------------------------
	_on_tier(3, "tool_corner", Vector2(LIFT_X - 8.0, -24.0), 10.0, 0.0)
	_on_tier(1, "tool_corner", Vector2(LIFT_X - 6.0, 10.0), 8.0, 0.0)
	_on_tier(3, "timber_store", Vector2(LIFT_X + 9.0, -24.0), 7.0, 0.0)
	_on_tier(3, "garden_bed", Vector2(-24.0, -40.0), 6.0, 0.0)
	_on_tier(3, "bamboo_garden", Vector2(-36.0, -41.0), 8.0, 0.0)
	_on_tier(2, "bamboo_garden", Vector2(40.0, -18.0), 8.0, 0.0)
	_on_tier(1, "tea_corner", Vector2(-30.0, 9.0), 8.0, 0.0)
	_on_tier(3, "kitchen_garden", Vector2(-12.0, -41.0), 9.0, 0.0)
	# ---- the Crown: sparse stone and planting at the edges; the procession stays bare ---------------------------
	for q in [Vector2(-34.0, -62.0), Vector2(35.0, -66.0)]:
		_on_tier(4, "rock_cluster_m", q, 5.0, rng.randf() * 360.0)
	for q in [Vector2(-30.0, -78.0), Vector2(31.0, -79.0)]:
		_on_tier(4, "flower_border", q, 4.0, 0.0)
	# ---- each terrace's back wall: a rhythm of planting, seating and stores against the retaining stone, so the long
	# paving meets an edge with life on it (skipped wherever a house, stair, lift, stall or route is in the way)
	var rhythm := [["garden_bed", "bench_view", "civic_planters", "supply_corner", "bamboo_garden", "flower_border"],
		["civic_planters", "covered_store", "bench_view", "garden_bed", "tea_corner"],
		["garden_bed", "bench_view", "flower_border", "supply_corner", "civic_planters"],
		["flower_border", "garden_bed", "tool_corner", "bench_view", "bamboo_garden"]]
	for i in 4:
		var t: Dictionary = TIERS[i]
		var list: Array = rhythm[i]
		var k := 0
		var x := float(t.x0) + 8.0 + float(i) * 3.0
		while x < float(t.x1) - 8.0:
			var vn: String = list[k % list.size()]
			var r := float(DataVignettes.get_def(vn).r)
			var z := float(t.z0) + r * 0.7 + 0.6
			_want_tier = i
			if _clear_here(x, z, r) and not group_overlaps(Vector3(x, tier_y(i), z), r) and not touches_solid(Vector3(x, tier_y(i), z), r * 0.8):
				vignette(vn, Vector3(x, tier_y(i), z), 0.0, {"on_ground": false, "check": false, "near": true})
				k += 1
				x += 16.0
			else:
				x += 4.0
	# ---- the slopes: canopy and outcrops that follow the grade, so the town's edges read as hillside -------------
	for i in TIERS.size():
		var t: Dictionary = TIERS[i]
		var zc := (float(t.z0) + float(t.z1)) * 0.5
		for side in [-1.0, 1.0]:
			var x := (float(t.x0) - 9.0) if side < 0.0 else (float(t.x1) + 9.0)
			if i == 3 and side > 0.0:
				continue              # the Coilwood Gate road leaves here
			vignette("palm_group" if (i + int(side)) % 2 == 0 else "rock_cluster_l", Vector3(x, 0, zc), rng.randf() * 360.0, {"check": false})
	# ambient accents: the quay, the Wire Market's fountain, the harbour brazier
	for qx in [-34.0, 0.0, 26.0]:
		accent(Vector3(qx, tier_y(0), 49.0), &"water_wave", -18.0)
	accent(Vector3(FOUNTAIN.x, tier_y(1) + 0.8, FOUNTAIN.y), &"water_splash", -20.0)
	accent(Vector3(30.0, tier_y(0) + 1.2, 40.0), &"torch_crackle", -16.0)
