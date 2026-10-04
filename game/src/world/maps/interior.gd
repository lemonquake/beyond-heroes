extends MapBuilder
## The walk-in interiors of Malasugue: the Salted Marlin, the Guild House, the two guild halls and five homes. One builder for all of
## them; `compose()` switches on the map id. Rooms sit on the 4 m grid, centred on the origin:
##
##   north (-Z) and east/west walls are full height; the south wall is a low cutaway (the camera looks from +Z) with a
##   4 m gap for the way out. A DoorPortal in the gap leads back to the `door_<id>` spawn outside, and the `start`
##   spawn stands just inside, facing into the room (death respawn in towns uses it).
##
## Kit notes (work/lemondev/bh-003/evidence/architecture/README.md): walls are 4 m long, 0.3 m thick, 3.6 m tall
## (0.9 m low) with the room side at local +Z; `int_floor_planks` is 0.1 m thick with its origin at the bottom, so the
## tiles sit at y = -0.1 and furniture stands at y = 0. Wall-standing furniture has its back at local -Z.

const HALF_WALL := 0.15
const PLASTER := {"full": "int_wall_plaster", "window": "int_wall_plaster_window", "low": "int_wall_plaster_low"}
const STONE := {"full": "int_wall_stone", "window": "int_wall_stone", "low": "int_wall_stone_low"}
const WARM := Color(1.0, 0.66, 0.36)

var x0 := -8.0
var x1 := 8.0
var z0 := -6.0
var z1 := 6.0
var exit_x := 0.0

func compose() -> void:
	match def.id:
		&"int_tavern": _tavern()
		&"int_guildhouse": _guildhouse()
		&"int_swordfin": _swordfin()
		&"int_lantern": _lantern()
		&"int_netmender": _netmender()
		&"int_cartographer": _cartographer()
		&"int_widow": _widow()
		&"int_keeper": _keeper()
		&"int_refugee": _refugee()
		_:
			push_error("interior.gd has no room for %s" % def.id)
			_room(8.0, 8.0, PLASTER, 0, {})
	_map_design()

# ------------------------------------------------------------------------------------------------------------
# room shell

## Floor, walls, the way out, spawns, bounds and camera views. `windows` = {side: [segment indices]} (north/east/west).
func _room(w: float, d: float, walls: Dictionary, exit_seg: int, windows: Dictionary, stone_floor := false,
		ambient := Color(0.62, 0.46, 0.34), ambient_energy := 0.42) -> void:
	x0 = -w * 0.5
	x1 = w * 0.5
	z0 = -d * 0.5
	z1 = d * 0.5
	exit_x = x0 + WALL * (exit_seg + 0.5)
	environment({
		"sky": false, "bg": Color(0.018, 0.014, 0.012), "ambient": ambient, "ambient_energy": ambient_energy,
		"fog": Color(0.1, 0.07, 0.05), "fog_density": 0.002, "fog_height": -10.0, "fog_height_density": 0.0,
		"sun": Color(1.0, 0.82, 0.62), "sun_energy": 0.22, "sun_rot": Vector3(-62, 25, 0), "glow": 0.9,
		"exposure": 1.15, "contrast": 1.05, "saturation": 0.98,
	})
	# floor: kit tiles with a walkable slab under them (the navmesh and the NPC ground rays read the slab)
	var nx := int(round(w / WALL))
	var nz := int(round(d / WALL))
	if stone_floor:
		floor_tiles(Rect2(x0, z0, w, d), 0.0)
	else:
		for i in nx:
			for j in nz:
				arch("int_floor_planks", Vector3(x0 + WALL * (i + 0.5), -0.1, z0 + WALL * (j + 0.5)), 0.0)
	walk_slab(Vector3(0, 0, 0), Vector3(w, 0.5, d))
	# walls: fronts face the room
	for i in nx:
		var nwin: Array = windows.get("north", [])
		arch(walls.window if i in nwin else walls.full, Vector3(x0 + WALL * (i + 0.5), 0, z0), 0.0)
		if i != exit_seg:
			arch(walls.low, Vector3(x0 + WALL * (i + 0.5), 0, z1), 180.0)
	for j in nz:
		arch(walls.window if j in windows.get("west", []) else walls.full, Vector3(x0, 0, z0 + WALL * (j + 0.5)), 90.0)
		arch(walls.window if j in windows.get("east", []) else walls.full, Vector3(x1, 0, z0 + WALL * (j + 0.5)), -90.0)
	# the way out: a porch slab past the gap, fenced by invisible walls so nobody steps into the dark
	walk_slab(Vector3(exit_x, 0, z1 + 0.9), Vector3(WALL, 0.5, 1.8))
	boundary(Vector3(exit_x - 2.0, 0, z1 + 1.6), Vector3(exit_x + 2.0, 0, z1 + 1.6), 4.0, 0.4)
	boundary(Vector3(exit_x - 2.1, 0, z1), Vector3(exit_x - 2.1, 0, z1 + 1.6), 4.0, 0.4)
	boundary(Vector3(exit_x + 2.1, 0, z1), Vector3(exit_x + 2.1, 0, z1 + 1.6), 4.0, 0.4)
	kit("rug", Vector3(exit_x, 0.004, z1 - 1.2), 0.0, 0.8, deco)
	var parent: StringName = def.parent_map if def.parent_map != &"" else &"sanctuary"
	var portal := DoorPortal.new().setup(parent, StringName("door_%s" % def.id), "Malasugue", false)
	portal.position = Vector3(exit_x, 0, z1 + 0.5)
	markers.add_child(portal)
	spawn(&"start", Vector3(exit_x, 0, z1 - 1.6), 180.0)
	set_bounds(AABB(Vector3(x0 - 1.0, -1.0, z0 - 1.0), Vector3(w + 2.0, 6.0, d + 3.0)))
	var span := maxf(w, d)
	view("room", Vector3(0, 0, 0.5), 0.0, 55.0, span * 1.35, 45.0)
	view("overview", Vector3(0, 0, 0), 0.0, 70.0, span * 1.5, 45.0)
	view("entrance", Vector3(exit_x, 0, z1 - 2.0), 0.0, 45.0, 10.0, 45.0)

## A piece standing against a wall. `along` runs west->east on the north wall and north->south on east/west walls;
## `back` is the distance from the piece's origin to its back face (its local -Z extent).
func against(piece: String, side: String, along: float, back: float, y := 0.0, parent: Node3D = null, scale := 1.0) -> Node3D:
	var gap := HALF_WALL + back * scale + 0.02
	match side:
		"north": return kit(piece, Vector3(along, y, z0 + gap), 0.0, scale, parent)
		"west": return kit(piece, Vector3(x0 + gap, y, along), 90.0, scale, parent)
		"east": return kit(piece, Vector3(x1 - gap, y, along), -90.0, scale, parent)
	push_error("against(): no wall '%s'" % side)
	return kit(piece, Vector3(along, y, 0), 0.0, scale, parent)

func item(piece: String, pos: Vector3, yaw := 0.0) -> Node3D:
	return kit(piece, pos, yaw, 1.0, props)

## Fire in a hearth or fireplace: flames at its `flame` socket and a flickering light at `light`.
func hearth(n: Node3D, energy := 3.2, size := 1.2) -> void:
	flame(socket_pos(n, "flame"), size)
	light(socket_pos(n, "light") + Vector3(0, 0.3, 0), FIRE, energy, 9.0, true, true)

func lamp(n: Node3D, c := WARM, energy := 1.8, range_m := 7.0) -> void:
	light(socket_pos(n, "light"), c, energy, range_m, false, true)

## A guild banner hung flat on the north wall (origin at the rod, the cloth hangs ~2.5 m down).
func banner(piece: String, x: float) -> void:
	kit(piece, Vector3(x, 3.3, z0 + HALF_WALL + 0.1), 0.0, 1.0, deco)

# ------------------------------------------------------------------------------------------------------------
# The Salted Marlin — Hesta behind the bar, Fennick by the fire, Old Marrow at a table, Venna Kail by the hearth

func _tavern() -> void:
	_room(16.0, 12.0, PLASTER, 2, {"north": [0, 1], "west": [0, 2], "east": [0]})
	# the bar along the north-east wall
	against("bar_back_shelf", "north", 4.0, 0.25)
	against("keg_rack", "north", 6.7, 0.35)
	var counter := item("bar_counter", Vector3(4.2, 0, -3.3))
	for x in [2.9, 4.2, 5.5]:
		item("stool", Vector3(x, 0, -2.2), randf_seeded(x) * 40.0)
	# the hearth on the west wall with a rug for the bard
	var fire := against("fireplace", "west", 0.0, 0.45)
	hearth(fire, 3.6, 1.4)
	kit("rug_round", Vector3(-5.2, 0.005, 0.0), 0.0, 1.0, deco)
	# long table and benches under the north windows
	var long_table := item("table_long", Vector3(-2.2, 0, -4.4))
	item("bench", Vector3(-2.2, 0, -5.2))
	item("bench", Vector3(-2.2, 0, -3.55), 180.0)
	candles(Vector3(-2.0, 1.0, -4.4), 0.9)
	# round tables in the room
	var rounds := []
	for t in [Vector3(-1.2, 0, 2.6), Vector3(4.0, 0, 1.4)]:
		rounds.append(item("table_round", t))
		for k in 3:
			var a := TAU * k / 3.0 + 0.4
			var at: Vector3 = t + Vector3(cos(a), 0, sin(a)) * (0.95 if t.x < 0.0 else 1.05)
			if t.x < 0.0:
				item("stool", at, rad_to_deg(a))
			else:
				# map-design pass: this table's party sits on chairs turned to face it (kd_chair, front +Z)
				item("kd_chair", at, rad_to_deg(atan2(t.x - at.x, t.z - at.z)))
	# rooms upstairs behind a curtain; supplies in the corner
	against("curtain", "east", 3.0, 0.0, 0.0, deco)
	item("barrel", Vector3(7.1, 0, -1.4))
	item("crate", Vector3(7.0, 0, -0.3), 20.0)
	for lp in [Vector3(-1.5, 0, -0.8), Vector3(3.2, 0, -0.2)]:
		lamp(kit("hanging_lantern", lp, 0.0, 1.0, deco), WARM, 2.2, 8.0)
	_tavern_bh033(long_table, rounds, counter)

## bh-033: the Salted Marlin's evening (Poly Haven CC0 props): supper on the tables, wine casks by the kegs, the pot on
## the hearth. Tableware sits on each surface's measured top; nothing new blocks the bar, the hearth rug or a stool.
func _tavern_bh033(long_table: Node3D, rounds: Array, counter: Node3D) -> void:
	var lt := _top(long_table)
	for d in [[-3.6, "ph_carved_wooden_plate", 0.0], [-2.9, "ph_wooden_bowl_01", 20.0], [-1.3, "ph_carved_wooden_plate", 40.0], [-0.6, "ph_wooden_bowl_01", -15.0]]:
		kit(d[1], Vector3(float(d[0]), lt, -4.4 + (0.18 if int(d[0] * 10) % 2 == 0 else -0.18)), d[2], 1.0, deco)
	for t in rounds:
		var top := _top(t)
		kit("ph_carved_wooden_plate", t.position + Vector3(0.18, top, 0.1), 0.0, 1.0, deco)
		kit("ph_wooden_bowl_01", t.position + Vector3(-0.22, top, -0.12), 30.0, 1.0, deco)
	var ct := _top(counter)
	kit("ph_wooden_cutting_board", counter.position + Vector3(-0.7, ct, 0.0), 10.0, 1.0, deco)
	kit("ph_wicker_basket_02", counter.position + Vector3(0.9, ct, 0.05), 0.0, 1.0, deco)
	# casks beside the keg rack, a bucket and the stew pot by the fire, baskets of bread by the curtain
	item("ph_wine_barrel_01", Vector3(7.2, 0, -2.7), 15.0)
	kit("ph_ceramic_pot", Vector3(-6.7, 0, 1.4), 0.0, 1.0, deco)
	kit("ph_wooden_bucket_01", Vector3(-6.6, 0, -1.5), 0.0, 1.0, deco)
	kit("ph_wicker_basket_01", Vector3(-5.6, 0, 5.0), 70.0, 1.0, deco)
	item("ph_wooden_crate_02", Vector3(-6.7, 0, 4.4), 90.0)

## Height of the top of a placed piece (its visible meshes), relative to its own origin.
func _top(n: Node3D) -> float:
	var top := 0.0
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		var b := n.global_transform.affine_inverse() * mi.global_transform * mi.get_aabb() if n.is_inside_tree() else mi.transform * mi.get_aabb()
		top = maxf(top, b.end.y)
	return top

# ------------------------------------------------------------------------------------------------------------
# The Guild House (bh-016; rebuilt bh-027) — a long hall where every guild of Malasugue keeps a counter. Steward Hollis at
# the reception table under the featured banner (the hero's own guild once they found one), Bram Ostler at the Swordfin
# counter (west) and Sabeth Wynn at the Lantern counter (east), the four newer guilds' banners down the side walls,
# fellow heroes' banners on the north wall, and the one Guild Quest Board in the middle for everyone.

func _guildhouse() -> void:
	_room(28.0, 16.0, STONE, 3, {}, true, Color(0.52, 0.48, 0.58), 0.5)
	# the old houses' banners at the far corners
	banner("guild_banner_swordfin", -12.0)
	banner("guild_banner_swordfin", -9.6)
	banner("guild_banner_lantern", 9.6)
	banner("guild_banner_lantern", 12.0)
	# reception: a long table across the middle of the north side, the steward behind it
	item("table_long", Vector3(0, 0, -2.3))
	candles(Vector3(-0.8, 1.0, -2.3), 0.9)
	candles(Vector3(0.9, 1.0, -2.3), 0.8)
	kit("rug", Vector3(0, 0.004, 0.6), 0.0, 1.8, deco)
	torch(Vector3(-2.2, 2.3, z0 + HALF_WALL + 0.02), 0.0, 2.8)
	torch(Vector3(2.2, 2.3, z0 + HALF_WALL + 0.02), 0.0, 2.8)
	# Swordfin side: counter, racks, armor
	item("desk_writing", Vector3(-6.4, 0, -2.2), 180.0)
	candles(Vector3(-6.9, 1.0, -2.1), 0.8)
	against("weapon_display", "north", -12.9, 0.08)
	item("armor_stand", Vector3(-13.0, 0, -6.9))
	item("weapon_rack", Vector3(-13.3, 0, 6.4), 90.0)
	item("chest", Vector3(-8.6, 0, -6.9), 0.0)
	lamp(item("lantern_stand", Vector3(-4.2, 0, -6.9)), WARM, 1.6)
	# Lantern side: counter, shelves
	item("desk_writing", Vector3(6.4, 0, -2.2), 180.0)
	candles(Vector3(5.9, 1.0, -2.1), 0.8)
	against("bookshelf_full", "east", -6.0, 0.25)
	item("lectern", Vector3(12.6, 0, -6.8))
	item("trunk", Vector3(8.6, 0, -6.9), 0.0)
	lamp(item("lantern_stand", Vector3(4.2, 0, -6.9), 180.0), Color(1.0, 0.78, 0.45), 1.8)
	light(Vector3(6.4, 2.8, -2.6), Color(0.7, 0.5, 1.0), 0.9, 6.0, false, true)
	light(Vector3(-6.4, 2.8, -2.6), Color(0.55, 0.7, 1.0), 0.9, 6.0, false, true)
	# the newer guilds: a counter and a banner stand each, down the side walls
	var spots := [[Vector3(x0 + 1.3, 0, -0.6), 90.0], [Vector3(x0 + 1.3, 0, 4.6), 90.0], [Vector3(x1 - 1.3, 0, -0.6), -90.0], [Vector3(x1 - 1.3, 0, 4.6), -90.0]]
	for i in spots.size():
		var at: Vector3 = spots[i][0]
		var yaw: float = spots[i][1]
		var gc := GuildCounter.new()
		gc.slot = "npc_%d" % i
		gc.position = at
		gc.rotation.y = deg_to_rad(yaw)
		markers.add_child(gc)
		var inward := Vector3(1, 0, 0) if yaw > 0.0 else Vector3(-1, 0, 0)
		item("desk_writing", at + inward * 1.6, yaw + 180.0)
		candles(at + inward * 1.6 + Vector3(0, 1.0, 0.3), 0.7)
	# the two old houses get a banner stand of their own by their counters
	for side in [["swordfin", Vector3(-9.2, 0, -3.4), 0.0], ["lantern", Vector3(9.2, 0, -3.4), 0.0]]:
		var gc2 := GuildCounter.new()
		gc2.slot = side[0]
		gc2.position = side[1]
		gc2.rotation.y = deg_to_rad(side[2])
		markers.add_child(gc2)
	# fellow heroes' guilds met in multiplayer hang on the north wall, between the old houses and the reception
	for i in 4:
		var wx: float = [-7.0, -4.6, 4.6, 7.0][i]
		var fg := GuildCounter.new()
		fg.slot = "imported:%d" % i
		fg.on_wall = true
		fg.position = Vector3(wx, 2.4, z0 + HALF_WALL + 0.06)
		markers.add_child(fg)
	# Class Transcendence: the Grand Master's lectern by the west wall (DataNpcsGuildHouse.GRAND_MASTER_SPOT)
	item("lectern", Vector3(-9.8, 0, 1.7), 90.0)
	candles(Vector3(-9.8, 1.15, 1.7), 0.6)
	# waiting benches and hanging lanterns
	item("bench", Vector3(-4.2, 0, 5.6))
	item("bench", Vector3(4.2, 0, 5.6))
	for lp in [Vector3(-5.0, 0, 1.6), Vector3(5.0, 0, 1.6), Vector3(0, 0, 5.2)]:
		lamp(kit("hanging_lantern", lp, 0.0, 1.0, deco), WARM, 2.0, 8.0)
	# the hero's own guild banner (bh-017), centred on the north wall above the reception: featured once they found one
	var gb := GuildBannerDisplay.new()
	gb.position = Vector3(0, 2.6, z0 + HALF_WALL + 0.05)
	markers.add_child(gb)
	# the one Guild Quest Board, in the middle of the hall facing the door
	var board := kit("notice_board", Vector3(0, 0, 2.4), 0.0, 1.25, props)
	lamp(kit("hanging_lantern", Vector3(0, 0, 3.4), 0.0, 1.0, deco), Color(1.0, 0.8, 0.5), 2.2, 7.0)
	var jb := GuildJobBoard.new()
	jb.guild = GuildJobs.CENTRAL
	jb.position = Vector3(0, 0, 2.6)
	markers.add_child(jb)
	if board == null:
		push_warning("Guild House: no notice_board kit piece")

# ------------------------------------------------------------------------------------------------------------
# Swordfin Hall — Commander Rhea at the war table, Quartermaster Dax at the register desk

func _swordfin() -> void:
	_room(16.0, 12.0, STONE, 2, {}, true, Color(0.5, 0.52, 0.6), 0.45)
	banner("guild_banner_swordfin", -4.0)
	banner("guild_banner_swordfin", 4.0)
	against("weapon_display", "north", 0.0, 0.08)
	item("armor_stand", Vector3(-6.6, 0, -4.9))
	item("armor_stand", Vector3(6.6, 0, -4.9))
	against("notice_board", "east", -1.0, 0.32)
	item("map_table", Vector3(-3.2, 0, 0.6))
	item("desk_writing", Vector3(3.6, 0, -1.6), 180.0)
	candles(Vector3(3.2, 1.0, -1.5), 0.8)
	item("weapon_rack", Vector3(-6.9, 0, -1.8), 90.0)
	item("bench", Vector3(-7.3, 0, 2.6), 90.0)
	item("chest", Vector3(6.8, 0, 3.4), -90.0)
	torch(Vector3(-2.0, 2.3, z0 + HALF_WALL + 0.02), 0.0, 2.6)
	torch(Vector3(2.0, 2.3, z0 + HALF_WALL + 0.02), 0.0, 2.6)
	lamp(item("lantern_stand", Vector3(-6.9, 0, 4.7)), WARM, 1.6)
	lamp(item("lantern_stand", Vector3(6.4, 0, 4.7), 180.0), WARM, 1.6)

# ------------------------------------------------------------------------------------------------------------
# Lantern House — Archivist Oren at the lectern, Scribe Lio at the register desk

func _lantern() -> void:
	_room(12.0, 12.0, STONE, 1, {}, true, Color(0.5, 0.44, 0.62), 0.42)
	banner("guild_banner_lantern", -4.0)
	banner("guild_banner_lantern", 4.0)
	against("bookshelf_full", "west", -3.4, 0.25)
	against("bookshelf_full", "west", 0.8, 0.25)
	against("bookshelf_full", "east", -3.4, 0.25)
	item("lectern", Vector3(0, 0, -3.2))
	lamp(item("lantern_stand", Vector3(-2.6, 0, -4.9)), Color(1.0, 0.78, 0.45), 1.8)
	lamp(item("lantern_stand", Vector3(2.6, 0, -4.9), 180.0), Color(1.0, 0.78, 0.45), 1.8)
	item("desk_writing", Vector3(3.3, 0, 1.6), 180.0)
	candles(Vector3(2.9, 1.0, 1.7), 0.8)
	kit("rug_round", Vector3(0, 0.005, 0.6), 0.0, 1.0, deco)
	candles(Vector3(-4.8, 0, 4.0), 1.0)
	item("trunk", Vector3(4.9, 0, 4.2), -90.0)
	# the covenant's violet lamp over the lectern
	light(Vector3(0, 2.8, -3.0), Color(0.7, 0.5, 1.0), 1.0, 6.0, false, true)

# ------------------------------------------------------------------------------------------------------------
# Homes (8 x 8 m)

func _netmender() -> void:
	_room(8.0, 8.0, PLASTER, 1, {"north": [1], "west": [1]})
	against("fishing_nets", "north", -1.4, 0.05)
	item("fish_rack", Vector3(-2.6, 0, 1.8), 90.0)
	hearth(item("cooking_hearth", Vector3(2.3, 0, -2.2)), 2.6, 1.0)
	item("bed", Vector3(-2.8, 0, -1.4), 90.0)
	item("table", Vector3(0.4, 0, 0.6))
	item("chair", Vector3(0.4, 0, 1.4), 180.0)
	item("trunk", Vector3(3.1, 0, 0.6), -90.0)
	candles(Vector3(0.1, 0.92, 0.6), 0.8)

func _cartographer() -> void:
	_room(8.0, 8.0, PLASTER, 0, {"north": [0], "east": [1]})
	kit("rug_round", Vector3(0.4, 0.005, -0.4), 0.0, 1.0, deco)
	item("map_table", Vector3(0.4, 0, -0.4))
	against("desk_writing", "north", 2.2, 0.35)
	against("bookshelf_full", "west", -1.8, 0.25)
	item("bed", Vector3(2.9, 0, 2.2), 90.0)
	item("chest", Vector3(-3.2, 0, 3.0), 90.0)
	candles(Vector3(2.5, 1.0, -3.3), 0.9)
	lamp(item("lantern_stand", Vector3(-3.3, 0, 1.4)), WARM, 1.8)

func _widow() -> void:
	_room(8.0, 8.0, PLASTER, 1, {"north": [0], "east": [0]})
	item("bed_double", Vector3(-2.7, 0, -2.3), 180.0)
	item("crib", Vector3(-0.3, 0, -3.1))
	against("washstand", "north", 1.4, 0.23)
	against("cabinet", "east", -2.0, 0.27)
	against("shrine_small", "west", 1.8, 0.3)
	candles(Vector3(-3.2, 0, 0.5), 1.1)
	item("table", Vector3(0.8, 0, 1.0))
	item("chair", Vector3(0.8, 0, 1.8), 180.0)
	candles(Vector3(1.1, 0.92, 1.0), 0.7)

func _keeper() -> void:
	_room(8.0, 8.0, PLASTER, 0, {"north": [0], "east": [1]}, false, Color(0.55, 0.45, 0.4), 0.38)
	lamp(against("shrine_small", "north", 1.6, 0.3), Color(0.6, 0.95, 1.0), 1.4, 5.0)
	against("bookshelf_full", "east", -1.2, 0.25)
	item("lectern", Vector3(0.4, 0, -0.6))
	candles(Vector3(2.8, 0, -3.2), 1.0)
	candles(Vector3(0.1, 0, -3.3), 0.8)
	item("bedroll", Vector3(-2.8, 0, -2.4), 90.0)
	item("trunk", Vector3(3.0, 0, 2.8), -90.0)
	item("urn", Vector3(-3.3, 0, 0.6))

func _refugee() -> void:
	_room(8.0, 8.0, PLASTER, 1, {"north": [0], "west": [1]}, false, Color(0.55, 0.44, 0.36), 0.36)
	item("bedroll", Vector3(-2.6, 0, -2.8))
	item("trunk", Vector3(-3.1, 0, 0.2), 90.0)
	item("table", Vector3(0.2, 0, -0.8))
	item("chair", Vector3(0.2, 0, 0.0), 180.0)
	hearth(item("cooking_hearth", Vector3(-2.4, 0, 2.4)), 2.4, 0.9)
	item("crate", Vector3(3.1, 0, -3.1), 15.0)
	item("barrel", Vector3(2.2, 0, -3.2))
	candles(Vector3(-0.1, 0.92, -0.8), 0.7)

## Deterministic per-position jitter (stools, clutter) without touching the builder's shared RNG sequence.
func randf_seeded(v: float) -> float:
	return fposmod(sin(v * 12.9898) * 43758.5453, 1.0) - 0.5

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): each room furnished for what it is used for, with the prepared Kenney pieces (kd_*).
# Backs to the walls, legs on the floor, books and bottles on the surfaces they sit on (their measured tops). Nothing
# new stands on an NPC's spot, in the door lane or before a story object; no room gains a light (one lighting idea each).

func _map_design() -> void:
	match def.id:
		&"int_tavern": _md_tavern()
		&"int_guildhouse": _md_guildhouse()
		&"int_swordfin": _md_swordfin()
		&"int_lantern": _md_lantern()
		&"int_netmender": _md_netmender()
		&"int_cartographer": _md_cartographer()
		&"int_widow": _md_widow()
		&"int_keeper": _md_keeper()
		&"int_refugee": _md_refugee()

## Something set on a placed piece's top surface (books on a desk, bottles on the bar).
func _on_top(n: Node3D, piece: String, off: Vector2, yaw := 0.0, scale := 1.0) -> Node3D:
	if n == null:
		return null
	return kit(piece, n.position + Vector3(off.x, _top(n), off.y), yaw, scale, deco)

func _md_tavern() -> void:
	# coats by the door and a bench to wait on, against the low south wall east of the way in
	item("kd_coat_rack", Vector3(4.9, 0, 5.3), 200.0)
	item("kd_bench", Vector3(6.5, 0, 5.35), 180.0)
	# the bottle stock in the dry north-west corner, a couple of bottles at the bar's end (not on every table)
	item("kd_crate_bottles", Vector3(-7.15, 0, -5.0), 8.0)
	var bar: Node3D = props.find_child("bar_counter_*", false, false)
	if bar:
		_on_top(bar, "kd_bottle", Vector2(1.45, 0.05), 0.0)
		_on_top(bar, "kd_bottle_large", Vector2(1.7, -0.12), 20.0, 0.8)

func _md_netmender() -> void:
	# the work side by the window: stock and the oars that go with the nets; the sleeping corner keeps a bedside table
	item("kd_crate", Vector3(-3.2, 0, 3.1), 12.0)
	against("kd_paddle", "north", 0.15, 0.08, 0.0, deco)
	kit("ph_wooden_bucket_02", Vector3(-1.5, 0, 2.9), 0.0, 1.0, deco)
	var st := against("kd_side_table", "north", -3.2, 0.25)
	_on_top(st, "kd_candles", Vector2(0.25, 0.0), 0.0, 0.7)
	_on_top(st, "kd_bottle_large", Vector2(-0.3, 0.05), 0.0, 0.8)

func _md_cartographer() -> void:
	# books on the desk, a low shelf of rolled charts within reach, a stool to read on, a bedside table
	var desk: Node3D = props.find_child("desk_writing_*", false, false)
	if desk:
		_on_top(desk, "kd_books", Vector2(-0.5, 0.0), 15.0)
	var low := against("kd_bookcase_low", "west", 1.4, 0.28)
	_on_top(low, "kd_books", Vector2(0.0, 0.2), 90.0)
	_on_top(low, "kd_plant_pot_b", Vector2(0.0, -0.25), 0.0, 1.4)
	kit("ph_folding_wooden_stool", Vector3(-2.3, 0, -0.9), 30.0, 1.0, props)
	var bt := against("kd_side_table", "east", 0.7, 0.25, 0.0, null, 0.8)
	_on_top(bt, "kd_candles", Vector2(0.0, 0.0), 0.0, 0.6)

func _md_widow() -> void:
	# a second chair at the table (the house still eats together), stored household goods by the cabinet
	item("kd_chair", Vector3(1.75, 0, 1.0), -90.0)
	kit("kd_pot_small", Vector3(3.35, 0, -0.4), 0.0, 0.8, deco)
	kit("ph_wicker_basket_01", Vector3(3.3, 0, 0.5), 0.0, 1.0, deco)
	var t: Node3D = props.find_child("table_*", false, false)
	if t:
		_on_top(t, "kd_plant_pot_a", Vector2(-0.35, -0.1), 0.0, 1.5)

func _md_keeper() -> void:
	# the keeper's records shelved on the west wall, spare lamps housed on a side table, books by the lectern
	against("kd_bookcase_closed", "west", 1.6, 0.28)
	var st := against("kd_side_table", "north", -1.4, 0.25)
	_on_top(st, "kd_lantern_candle", Vector2(-0.3, 0.0), 0.0, 0.8)
	_on_top(st, "kd_lantern_candle", Vector2(0.3, 0.05), 30.0, 0.8)
	kit("kd_books", Vector3(1.4, 0, -0.9), 40.0, 1.2, deco)

func _md_refugee() -> void:
	# a family in one room: a bunk against the east wall, possessions in baskets, the crate as a second table
	against("kd_bed_bunk", "east", 0.8, 0.55)
	kit("ph_wicker_basket_02", Vector3(-3.2, 0, 1.5), 0.0, 1.0, deco)
	kit("kd_pot_small", Vector3(-1.6, 0, 3.2), 0.0, 0.8, deco)
	var cr: Node3D = props.find_child("crate_*", false, false)
	if cr:
		_on_top(cr, "kd_bottle", Vector2(0.1, 0.1), 0.0)

func _md_guildhouse() -> void:
	# reception: plants either side of the steward's table, a coat rack by the door
	for sx in [-1.0, 1.0]:
		kit("kd_plant_tall", Vector3(sx * 2.9, 0, -3.6), 0.0, 1.0, deco)
	item("kd_coat_rack", Vector3(-2.9, 0, 7.2), 160.0)
	# the archive wall: low shelves under the fellow guilds' banners, records stacked on them (north wall, east half)
	for x in [5.6, 7.4]:
		var sh := against("kd_bookcase_low", "north", x, 0.28)
		_on_top(sh, "kd_books", Vector2(0.15, 0.0), 10.0 + x * 7.0)
	# the Swordfin side keeps its papers in drawers
	var dr := against("kd_drawers", "north", -6.4, 0.25)
	_on_top(dr, "kd_books", Vector2(-0.3, 0.0), 0.0)

func _md_swordfin() -> void:
	kit("kd_rug_long", Vector3(-3.2, 0.006, 0.7), 0.0, 1.0, deco)
	# a meeting at the war table: two chairs on its south side, facing Commander Rhea across it
	for dx in [-0.75, 0.75]:
		item("kd_chair_round", Vector3(-3.2 + dx, 0, 1.95), 180.0)
	# training records kept in drawers by the notice board
	var dr := against("kd_drawers", "east", 1.6, 0.25)
	_on_top(dr, "kd_books", Vector2(0.0, 0.0), 0.0)

func _md_lantern() -> void:
	# a reading corner: a chair turned to the shelves, a side table with books, the floor candles beside it
	item("kd_chair_round", Vector3(-3.0, 0, 2.7), -40.0)
	var st := item("kd_side_table", Vector3(-4.6, 0, 2.6), 90.0)
	_on_top(st, "kd_books", Vector2(0.0, 0.0), 30.0)
	var desk: Node3D = props.find_child("desk_writing_*", false, false)
	if desk:
		_on_top(desk, "kd_books", Vector2(0.45, 0.05), -20.0)
