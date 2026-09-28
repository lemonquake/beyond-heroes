extends SettlementBuilder
## MAP — Olivar, a walled trading town on the south shore of Stillwater Lake (bh-007; safe zone, provisional name set by
## the author). Reached by the Lake Shore Road east from the Old Mill (Westreach); the Watch Road leaves its south gate
## for Wyman Outpost.
##
## A palisade on three sides, the lake on the fourth. The Lake Shore Road enters by the west gate and runs to a cobbled
## plaza with a well and market stalls; Exchange Row leads east to Ashby's Arms Exchange (a trading house with racks of
## arms and armor outside), Apothecary Lane west to Pell's garden and alchemy table, Market Row to Crane's jewel stall,
## the Dock Walk north down to the piers, and the Terrace Steps to the waypoint above the water. The road polylines are
## DataIsland.ROADS (terrain beds, the atlas and the route planner share them).

const PLAZA := Vector2(0, 4)
const LAKE_Y := -2.3
const WALL_W := -46.0
const WALL_E := 46.0
const WALL_S := 42.0
const WALL_N := -36.0
const SHRINE := Vector2(-24, -33)
const EXCHANGE := Vector2(31, -2)
const APOTHECARY := Vector2(-31, -9)
const ALCHEMY := Vector2(-21.5, -13.0)
const JEWELS := Vector2(-12, 17)
const PIER_X := 4.0
## Houses: (x, z, yaw). Not enterable; lit windows and yards.
const HOUSES := [[-30.0, 22.0, 90.0], [-33.0, 34.5, 60.0], [30.0, 22.0, -90.0], [33.0, 34.0, -120.0], [-5.0, 32.0, 180.0],
	[31.0, -24.0, -45.0], [-36.0, -23.0, 45.0], [7.0, 32.5, 190.0]]

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.025, 0.04, 0.085), "sky_horizon": Color(0.15, 0.16, 0.26),
		"ambient": Color(0.32, 0.36, 0.5), "ambient_energy": 0.8,
		"fog": Color(0.15, 0.18, 0.27), "fog_density": 0.006, "fog_height": -4.0, "fog_height_density": 0.06,
		"sun": Color(0.58, 0.66, 0.95), "sun_energy": 0.6, "sun_rot": Vector3(-46, -25, 0), "glow": 0.8,
		"exposure": 1.12, "contrast": 1.06, "saturation": 0.94,
	})
	prepare(-100.0, -80.0, 200, 170, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "grass", "moss": "forest_floor", "dirt": "dirt", "path": "cobblestone", "rock": "rock_cliff"}, Color(0.95, 0.96, 0.92))
	_lake()
	_walls()
	_plaza()
	_exchange()
	_apothecary()
	_market()
	_houses()
	_docks_and_terrace()
	# bh-013: the sunken tomb stair by the market and the counting-house cellar behind Ashby's
	for gid in DataDungeons.gates_on(def.id):
		var gs: Dictionary = DataDungeons.get_def(gid).surface
		dungeon_gate(gid, gs.pos, gs.yaw)
	_herbs()
	_greenery()
	spawn(&"start", Vector3(0, 0, 9.0), 180.0, true)
	spawn(&"west_road", Vector3(-54, 0, 12), 90.0, true)
	spawn(&"south_road", Vector3(20, 0, 49), 180.0, true)
	set_bounds(AABB(Vector3(-66, -8, -60), Vector3(132, 30, 124)))
	view("overview", Vector3(0, 0, 0), 0.0, 62.0, 120.0, 45.0)
	view("topdown", Vector3(0, 0, 2), 0.0, 89.5, 125.0, 50.0)
	view("plaza", Vector3(0, 0, 4), 0.0, 50.0, 30.0)
	view("exchange", Vector3(24, 0, -2), -30.0, 45.0, 22.0)
	view("apothecary", Vector3(-22, 0, -10), 25.0, 45.0, 20.0)
	view("docks", Vector3(2, -1, -38), 0.0, 48.0, 30.0)
	view("west_gate", Vector3(-46, 0, 12), 60.0, 45.0, 26.0)

# ------------------------------------------------------------------------------------------------------------
# landform

func _noise(x: float, z: float) -> float:
	return sin(x * 0.13) * cos(z * 0.11) * 0.6 + sin(x * 0.047 + z * 0.063) * 0.8

func _landform(x: float, z: float) -> float:
	var h := _noise(x, z) * 0.25
	# hills outside the palisade (the roads climb them to the boundaries)
	var out := maxf(maxf(absf(x) - 50.0, z - 46.0), 0.0)
	h += 3.2 * smoothstep(0.0, 16.0, out)
	# the lake shore: the town falls to a beach and the water
	h = lerpf(h, -3.0, smoothstep(-33.0, -43.0, z))
	h = lerpf(h, -6.5, smoothstep(-44.0, -52.0, z))
	# the waypoint terrace above the docks
	h = lerpf(h, -0.9, 1.0 - smoothstep(5.0, 8.0, Vector2(x, z).distance_to(SHRINE)))
	return h

func _shape(x: float, z: float, b: float, _rd: float, _rt: int) -> float:
	var inside := x > WALL_W and x < WALL_E and z < WALL_S and z > -44.0
	return b + _noise(x * 1.7, z * 1.7) * (0.12 if inside else 0.6)

func _splat(x: float, z: float) -> Color:
	var k := _k(x, z)
	var n := sin(x * 0.37 + z * 0.23) * 0.5 + 0.5
	var road := (1.0 - smoothstep(2.4, 3.5, _rd[k])) if _rt[k] == 1 else 0.0
	var trail := (1.0 - smoothstep(1.1, 2.1, _rd[k])) if _rt[k] == 2 else 0.0
	var plaza := 1.0 - smoothstep(10.0, 11.5, Vector2(x, z).distance_to(PLAZA))
	var sand := smoothstep(-34.0, -40.0, z)
	var outside := 1.0 if (x < WALL_W - 2.0 or x > WALL_E + 2.0 or z > WALL_S + 2.0) else 0.0
	var b := clampf(maxf(road, plaza), 0.0, 1.0) * (1.0 - sand)
	var r := clampf(maxf(trail, sand) + n * 0.08, 0.0, 1.0)
	var g := clampf(outside * 0.6 + n * 0.25, 0.0, 1.0) * (1.0 - trail)
	return Color(r * (1.0 - b), g * (1.0 - b), b)

# ------------------------------------------------------------------------------------------------------------
# water, walls, gates

func _lake() -> void:
	water(Rect2(-160, -200, 320, 156), LAKE_Y, Color(0.1, 0.34, 0.4), Color(0.02, 0.06, 0.1), 0.45, 3.0, 0.35)
	mist(Rect2(-160, -200, 320, 140), LAKE_Y + 1.4, Color(0.26, 0.32, 0.44), 0.4)
	# far shore silhouettes across the lake
	for i in 7:
		var x := -80.0 + i * 26.0 + rng.randf_range(-6, 6)
		decor("rock_large", Vector3(x, LAKE_Y - 1.0, -120.0 + rng.randf_range(-10, 10)), rng.randf() * 360.0, rng.randf_range(3.0, 4.5), false)
		decor("tree_pine", Vector3(x + 6.0, LAKE_Y + 1.5, -118.0 + rng.randf_range(-8, 8)), rng.randf() * 360.0, rng.randf_range(1.6, 2.2), false)

func _walls() -> void:
	# palisade: west (gate at z 12), south (gate at x 20), east; the lake closes the north
	palisade_run(Vector2(WALL_W, WALL_N), Vector2(WALL_W, WALL_S), [[12.0 - WALL_N, 4.2]])
	palisade_run(Vector2(WALL_W, WALL_S), Vector2(WALL_E, WALL_S), [[20.0 - WALL_W, 4.2]])
	palisade_run(Vector2(WALL_E, WALL_S), Vector2(WALL_E, WALL_N))
	# the palisade ends run down into the water; the shoreline is the edge of the walkable town
	for sx: float in [WALL_W, WALL_E]:
		boundary(Vector3(sx, -8.0, WALL_N), Vector3(sx, -8.0, -47.0), 14.0)
	boundary(Vector3(WALL_W, -8.0, -45.5), Vector3(PIER_X - 2.4, -8.0, -45.5), 14.0)
	boundary(Vector3(PIER_X + 2.4, -8.0, -45.5), Vector3(WALL_E, -8.0, -45.5), 14.0)
	gatehouse(Vector2(WALL_W, 12.0), 90.0)
	gatehouse(Vector2(20.0, WALL_S), 0.0)
	# corridors to the district boundaries
	corridor_rails([Vector2(WALL_W - 0.5, 12.0), Vector2(-67.0, 12.0)], 4.6)
	boundary(Vector3(-67.0, -2.0, 7.0), Vector3(-67.0, -2.0, 17.0), 12.0)
	corridor_rails([Vector2(20.0, WALL_S + 0.5), Vector2(20.0, 63.0)], 4.6)
	boundary(Vector3(15.0, -2.0, 63.0), Vector3(25.0, -2.0, 63.0), 12.0)
	exit_zone(&"olivar_west_road", Vector3(-63.0, 0, 12.0), Vector3(3.0, 4.0, 8.4), &"westreach", &"olivar_road", "Westreach")
	exit_zone(&"olivar_watch_road", Vector3(20.0, 0, 58.5), Vector3(8.4, 4.0, 3.0), &"wyman_outpost", &"north_road", "Wyman Outpost")
	signpost_bed(Vector2(-39.5, 17.0), [["Old Mill (Lake Shore Road)", Vector2(-1, 0)], ["Olivar Plaza", Vector2(1, -0.2)]])
	signpost_bed(Vector2(24.5, 36.5), [["Wyman Outpost (Watch Road)", Vector2(0, 1)], ["Olivar Plaza", Vector2(-0.6, -1)]])
	signpost_bed(Vector2(-58.0, 16.8), [["Olivar", Vector2(1, 0)], ["Old Mill", Vector2(-1, 0)]])
	signpost_bed(Vector2(24.8, 54.0), [["Wyman Outpost", Vector2(0, 1)], ["Olivar", Vector2(0, -1)]])
	for p: Vector2 in [Vector2(-50.0, 7.0), Vector2(-60.0, 17.0), Vector2(15.0, 52.0), Vector2(25.0, 46.0)]:
		lamp_post(Vector3(p.x, 0, p.y), rng.randf() * 360.0)

# ------------------------------------------------------------------------------------------------------------
# places

func _plaza() -> void:
	floor_disc(Vector3(PLAZA.x, 0, PLAZA.y), 9.5, height_at(PLAZA.x, PLAZA.y) + 0.04)
	keep_clear(PLAZA.x, PLAZA.y, 11.0)
	# the Founder's statue: a knight on a raised dais (a low step, still walkable), braziers at its feet, lit from below
	var py := height_at(PLAZA.x, PLAZA.y)
	floor_disc(Vector3(PLAZA.x, 0, PLAZA.y), 2.4, py + 0.26)
	kit("statue_knight", Vector3(PLAZA.x, py + 0.26, PLAZA.y - 0.2), 180.0, 0.9, props)
	for sx: float in [-2.9, 2.9]:
		brazier(Vector3(PLAZA.x + sx, 0, PLAZA.y + 1.2), 3.2, false, true)
	light(Vector3(PLAZA.x, py + 1.0, PLAZA.y + 2.4), Color(1.0, 0.78, 0.5), 2.2, 7.0)
	# the well of Olivar and a trader's scale beside it
	kit("well", Vector3(7.5, 0, -4.0), -30.0, 1.0, props, true)
	keep_clear(7.5, -4.0, 3.0)
	kit("statue_small", Vector3(-6.5, 0, -3.5), 150.0, 1.1, props, true)
	kit("winch", Vector3(12.5, 0, -8.8), -60.0, 0.9, props, true)
	for i in 6:
		var a := TAU * i / 6.0 + 0.35
		var p := PLAZA + Vector2(cos(a), sin(a)) * 11.2
		if road_dist(p.x, p.y) > 3.6:
			lamp_post(Vector3(p.x, 0, p.y), rad_to_deg(-a) + 90.0)
	kit("notice_board", Vector3(-3.5, 0, -6.8), 20.0, 1.0, props, true)
	kit("bench", Vector3(5.5, 0, -8.0), 200.0, 1.0, props, true)
	kit("bench", Vector3(-9.0, 0, 8.5), 60.0, 1.0, props, true)
	for p: Vector3 in [Vector3(9.8, 0, -6.2), Vector3(10.4, 0, -5.2), Vector3(-9.6, 0, -6.4)]:
		breakable("barrel" if p.x > 0.0 else "crate", p, rng.randf() * 360.0, 20.0, true)
	signpost_bed(Vector2(3.8, 10.8), [["Wyman Outpost", Vector2(0.5, 1)], ["Docks", Vector2(0, -1)], ["Old Mill", Vector2(-1, 0.15)]])
	# the plaza's trade: crates and sacks by the stalls, flower tubs, banners of the town's colours
	for c in [[Vector2(-7.5, -1.5), 30.0], [Vector2(8.0, 3.2), -40.0]]:
		kit("table", Vector3(c[0].x, 0, c[0].y), c[1], 1.0, props, true)
		candles(Vector3(c[0].x, 0.92 + height_at(c[0].x, c[0].y), c[0].y))
	for p: Vector2 in [Vector2(-8.8, 1.2), Vector2(-9.4, 2.3), Vector2(9.6, 5.2), Vector2(-1.0, -9.6), Vector2(1.3, -9.9)]:
		breakable("crate" if p.x < 0.0 else "barrel", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 20.0, true)
	for i in 4:
		var a := TAU * i / 4.0 + PI * 0.25
		var bp := PLAZA + Vector2(cos(a), sin(a)) * 9.2
		if road_dist(bp.x, bp.y) < 3.4:
			continue
		var pole := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.06
		cm.bottom_radius = 0.08
		cm.height = 4.6
		pole.mesh = cm
		pole.material_override = MaterialLibrary.env("BH_WoodDark")
		pole.position = Vector3(bp.x, height_at(bp.x, bp.y) + 2.3, bp.y)
		deco.add_child(pole)
		kit("banner_torn", Vector3(bp.x, height_at(bp.x, bp.y) + 4.4, bp.y + 0.1), rad_to_deg(a) + 90.0, 0.9, deco)
		decor("bush_b", Vector3(bp.x + 0.6, 0, bp.y + 0.6), rng.randf() * 360.0, 0.7, true, true)

func _exchange() -> void:
	# a trading house (the tavern kit) with its goods set out under the eaves: racks of arms and armor on stands
	var c := EXCHANGE
	var b := kit("tavern_exterior", Vector3(c.x, 0, c.y), -90.0, 1.0, props, true)
	light(socket_pos(b, "door_light"), Color(1.0, 0.72, 0.4), 2.8, 9.0, false, true)
	light(socket_pos(b, "sign_light"), Color(1.0, 0.7, 0.4), 2.0, 7.0, false, true)
	keep_clear(c.x, c.y, 8.5)
	for z: float in [-6.8, -5.0]:
		kit("armor_stand", Vector3(24.6, 0, z), -90.0, 1.0, props, true)
	for z: float in [2.4, 4.4]:
		kit("weapon_rack", Vector3(24.9, 0, z), -90.0, 1.0, props, true)
	kit("table", Vector3(23.6, 0, -8.8), -90.0, 1.0, props, true)
	candles(Vector3(23.6, 0.92 + height_at(23.6, -8.8), -8.8))
	kit("chest", Vector3(25.8, 0, 6.3), -120.0, 1.0, props, true)
	lamp_post(Vector3(21.5, 0, -7.5), 90.0)
	lamp_post(Vector3(21.5, 0, 4.8), 90.0)

func _apothecary() -> void:
	var c := APOTHECARY
	var h := kit("house_intact", Vector3(c.x, 0, c.y), 90.0, 1.0, props, true)
	light(socket_pos(h, "door_light"), Color(0.7, 1.0, 0.75), 2.2, 7.0, false, true)
	keep_clear(c.x, c.y, 6.0)
	# the alchemy table in the herb garden: a long table, the kettle on its hearth, shelves of jars
	var a := ALCHEMY
	kit("table_long", Vector3(a.x, 0, a.y), 0.0, 1.0, props, true)
	var hearth := kit("cooking_hearth", Vector3(a.x + 3.0, 0, a.y - 0.4), 0.0, 1.0, props, true)
	flame(socket_pos(hearth, "flame"), 0.8)
	light(socket_pos(hearth, "light"), Color(0.6, 1.0, 0.7), 2.2, 7.0, false, true)
	kit("bookshelf_full", Vector3(a.x - 0.5, 0, a.y - 1.4), 0.0, 0.8, props, true)
	candles(Vector3(a.x - 0.9, 1.08 + height_at(a.x, a.y), a.y))
	crafting_station(&"alchemy", Vector3(a.x + 0.3, 0, a.y + 1.1), "Pell's Alchemy Table")
	keep_clear(a.x, a.y, 4.0)
	# the garden beds
	for i in 5:
		var p := Vector2(-26.0 + i * 1.6, -2.2 + (i % 2) * 0.8)
		decor("fern", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 0.7)
	kit("wood_fence", Vector3(-24.0, 0, -0.4), 0.0, 1.0, props, true)

func _market() -> void:
	var j := kit("market_stall", Vector3(JEWELS.x, 0, JEWELS.y), 150.0, 1.0, props, true)
	light(socket_pos(j, "light"), Color(1.0, 0.85, 0.55), 2.2, 7.0, false, true)
	keep_clear(JEWELS.x, JEWELS.y, 3.5)
	for s in [[Vector2(-17.0, 12.0), 60.0], [Vector2(14.5, 5.5), -110.0], [Vector2(-5.0, 22.0), 175.0]]:
		var st := kit("market_stall", Vector3(s[0].x, 0, s[0].y), s[1], 1.0, props, true)
		light(socket_pos(st, "light"), Color(1.0, 0.72, 0.42), 1.6, 6.0, false, true)
		keep_clear(s[0].x, s[0].y, 3.5)
	kit("cart_hay", Vector3(-19.5, 0, 16.5), 30.0, 1.0, props, true)
	for p: Vector3 in [Vector3(-15.5, 0, 15.2), Vector3(16.8, 0, 8.4), Vector3(-2.5, 0, 24.4)]:
		breakable("crate", p, rng.randf() * 90.0, 20.0, true)

func _houses() -> void:
	for hd in HOUSES:
		var p := Vector3(hd[0], 0, hd[1])
		var yaw: float = hd[2]
		var h := kit("house_intact", p, yaw, 1.0, props, true)
		light(socket_pos(h, "door_light"), Color(1.0, 0.68, 0.35), 2.0, 7.0, false, true)
		var fwd := Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(yaw))
		light(p + Vector3(0, 1.6 + height_at(p.x, p.z), 0) + fwd * 3.6, Color(1.0, 0.62, 0.3), 1.0, 5.0)
		var side := fwd.cross(Vector3.UP)
		breakable("barrel", p + side * 4.9 + fwd * 2.0, rng.randf() * 360.0, 20.0, true)
		decor("bush_a", p + side * -5.0 - fwd * 2.0, rng.randf() * 360.0, 0.9, true, true)
		keep_clear(p.x, p.z, 6.0)

func _docks_and_terrace() -> void:
	# the piers out into the lake
	for i in 3:
		kit("dock_planks", Vector3(PIER_X, LAKE_Y + 0.55, -45.5 - i * 5.8), 90.0, 1.0, geo)
	walk_slab(Vector3(PIER_X, LAKE_Y + 0.9, -51.2), Vector3(4.0, 0.4, 17.4))
	for sx: float in [-2.3, 2.3]:
		boundary(Vector3(PIER_X + sx, -8.0, -45.0), Vector3(PIER_X + sx, -8.0, -60.2), 14.0, 0.4)
	boundary(Vector3(PIER_X - 2.3, -8.0, -60.2), Vector3(PIER_X + 2.3, -8.0, -60.2), 14.0, 0.4)
	kit("boat_rowing", Vector3(PIER_X + 3.8, LAKE_Y + 0.05, -52.0), 80.0, 1.0, deco)
	kit("boat_rowing", Vector3(PIER_X - 3.9, LAKE_Y + 0.05, -56.5), 100.0, 1.0, deco)
	kit("boat_rowing", Vector3(-12.0, 0, -41.0), 20.0, 1.0, props, true)
	for p in [[Vector2(12.0, -38.0), 15.0], [Vector2(-6.0, -39.0), -20.0], [Vector2(18.0, -36.5), 70.0]]:
		kit("fish_rack", Vector3(p[0].x, 0, p[0].y), p[1], 1.0, props, true)
	kit("fishing_nets", Vector3(9.0, 0, -37.0), 0.0, 1.0, props, true)
	for p: Vector2 in [Vector2(-1.5, -41.5), Vector2(9.5, -41.8), Vector2(PIER_X + 1.6, -60.0)]:
		var y := LAKE_Y + 0.95 if p.y < -45.0 else height_at(p.x, p.y)
		kit("lantern_stand", Vector3(p.x, y, p.y), rng.randf() * 360.0, 1.0, props)
		light(Vector3(p.x + 0.45, y + 1.8, p.y), Color(1.0, 0.72, 0.42), 2.4, 10.0, false, true)
	for p: Vector3 in [Vector3(13.5, 0, -40.2), Vector3(14.4, 0, -39.4), Vector3(-4.0, 0, -41.2)]:
		breakable("barrel", p, rng.randf() * 360.0, 20.0, true)
	keep_clear(PIER_X, -40.0, 5.0)
	# the waypoint terrace: a stone disc above the water, standing stones, lanterns
	var s := SHRINE
	var sy := height_at(s.x, s.y) + 0.05
	floor_disc(Vector3(s.x, 0, s.y), 4.2, sy)
	teleporter(&"olivar_shrine", Vector3(s.x, sy, s.y), &"sanctuary", &"waypoint", "Malasugue Town")
	spawn(&"olivar_shrine", Vector3(s.x + 3.0, 0, s.y + 2.4), 150.0, true)
	for a: float in [0.6, 2.2, 3.9, 5.3]:
		decor("rock_medium", Vector3(s.x + cos(a) * 5.6, 0, s.y + sin(a) * 5.0), rng.randf() * 360.0, rng.randf_range(0.6, 0.9), true, true)
	for p: Vector2 in [Vector2(s.x - 4.4, s.y + 3.0), Vector2(s.x + 5.0, s.y - 1.5)]:
		kit("lantern_stand", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 1.0, props, true)
		light(Vector3(p.x + 0.45, height_at(p.x, p.y) + 1.8, p.y), Color(0.6, 0.85, 1.0), 2.2, 9.0, false, true)
	keep_clear(s.x, s.y, 7.0)

func _herbs() -> void:
	for p: Vector2 in [Vector2(-26.5, -1.2), Vector2(-17.5, -16.5), Vector2(-38.0, 6.0)]:
		herb_patch(&"silverleaf", Vector3(p.x, 0, p.y))
		keep_clear(p.x, p.y, 1.5)
	for p: Vector2 in [Vector2(-12.0, -37.0), Vector2(22.0, -35.5), Vector2(-30.0, -36.0)]:
		herb_patch(&"mirebloom", Vector3(p.x, 0, p.y))
		keep_clear(p.x, p.y, 1.5)
	herb_patch(&"emberroot", Vector3(38.0, 0, 12.0))
	keep_clear(38.0, 12.0, 1.5)

func _greenery() -> void:
	var inside := func(x: float, z: float) -> bool:
		return x > WALL_W - 3.0 and x < WALL_E + 3.0 and z < WALL_S + 3.0
	var blocked := func(x: float, z: float) -> bool:
		if road_dist(x, z) < 5.5 or z < -33.0 or not is_clear(x, z, 1.0):
			return true
		# corridors outside the gates stay open
		if absf(z - 12.0) < 7.0 and x < WALL_W:
			return true
		if absf(x - 20.0) < 7.0 and z > WALL_S:
			return true
		return false
	# a wood outside the palisade
	var outer := func(x: float, z: float) -> bool: return blocked.call(x, z) or inside.call(x, z) or z < -30.0
	var trees := scatter(["tree_pine", "tree_pine", "tree_oak_twisted", "tree_pine"], Rect2(-100, -32, 200, 122), 230, 4.8, Vector2(0.85, 1.3), outer, true, true)
	for t in trees:
		if road_dist(t.x, t.z) < 12.0:
			blocker(Vector3(t.x, height_at(t.x, t.z) + 2.0, t.z), Vector3(0.9, 4.0, 0.9))
	# a few shade trees and gardens inside the walls
	var town := func(x: float, z: float) -> bool: return blocked.call(x, z) or not inside.call(x, z) or x < WALL_W + 3.0 or x > WALL_E - 3.0 \
		or z > WALL_S - 3.0 or Vector2(x, z).distance_to(PLAZA) < 18.0
	scatter(["tree_oak_twisted"], Rect2(-44, -30, 88, 70), 9, 12.0, Vector2(0.8, 1.0), town, false)
	scatter(["bush_a", "bush_b", "fern"], Rect2(-44, -32, 88, 72), 70, 2.6, Vector2(0.7, 1.1), town, true, true)
	scatter(["bush_a", "bush_b", "fern", "rock_small", "stump"], Rect2(-100, -32, 200, 122), 160, 3.0, Vector2(0.7, 1.2), outer, true, true)
	var placed := 0
	var tries := 0
	while placed < 900 and tries < 5000:
		tries += 1
		var x := -68.0 + rng.randf() * 136.0
		var z := -34.0 + rng.randf() * 100.0
		if road_dist(x, z) < 3.2 or not is_clear(x, z) or z < -34.0:
			continue
		decor("grass_clump", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.8, 1.3))
		placed += 1
	# reeds along the beach
	for i in 40:
		var x := -44.0 + rng.randf() * 88.0
		if absf(x - PIER_X) < 4.0:
			continue
		decor("fern", Vector3(x, 0, -41.5 - rng.randf() * 2.5), rng.randf() * 360.0, rng.randf_range(0.6, 0.9))
