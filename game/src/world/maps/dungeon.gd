extends MapBuilder
## Every dungeon floor (bh-012), built from its plan in DataDungeons. One builder for all twenty floors; the map id
## (`dg_<dungeon>_<n>`) picks the dungeon, its theme and the floor.
##
## Direction (the user's reference, references/bh012_dungeon_reference.jpg): a cutaway diorama seen from the south —
## a luminous basin at the bottom with arches standing in it, torch-lit storeys stepping up toward the back, joined by
## stairs, galleries with low parapets looking down into the halls below. Higher storeys sit north (away from the
## camera) so the tall retaining walls read as the back walls of the rooms in front of them.
##
## Geometry rules per 4 m cell (DataDungeons documents the plan characters):
##   floor cells get a floor tile at their storey height; a neighbour that is void gets a full wall (north, east,
##   west) or a low cutaway wall (south); a lower neighbour or a basin gets a low parapet; a raised cell shows
##   masonry on every visible face down to its neighbour (south, east and west: the camera never sees north faces);
##   basin cells sink to BASIN_FLOOR with retaining walls and a liquid surface; bridges are floor tiles over the basin
##   carried on arches; stair cells hold one 2 m flight each. Pillars cap the corners where walls turn.

const STOREY := 4.0
const BASIN_FLOOR := -4.1
const LIQUID_Y := -2.4
const STAIR_DIR := {"^": Vector2i(0, -1), "v": Vector2i(0, 1), "<": Vector2i(-1, 0), ">": Vector2i(1, 0)}
const STAIR_YAW := {"^": 0.0, "v": 180.0, "<": 90.0, ">": -90.0}
const SIDES := {"north": Vector2i(0, -1), "south": Vector2i(0, 1), "west": Vector2i(-1, 0), "east": Vector2i(1, 0)}
## Wall yaw per side (the room() convention: pieces face into the cell whose edge they close).
const SIDE_YAW := {"north": 0.0, "south": 180.0, "west": -90.0, "east": 90.0}
const MAX_TORCHES := 30
## Lived-in clutter set against the walls of rooms (never on corridor cells): kit pieces per theme.
const CLUTTER := {
	&"fungal": ["log_fallen", "stump", "urn", "spore_pod", "mushroom_glow_cluster", "cart_hay", "wagon_broken"],
	&"drowned": ["barrel", "crate", "fishing_nets", "bedroll", "table", "chair", "trunk", "keg_rack", "scaffold_platform", "fish_rack"],
	&"ember": ["anvil", "weapon_rack", "crate", "barrel", "ore_cart", "table_long", "armor_stand", "weapon_display"],
	&"rime": ["sarcophagus", "coffin", "statue_knight", "urn", "skull_pile", "gravestone_a", "gravestone_b", "frozen_coffin"],
	&"orrery": ["bookshelf_full", "desk_writing", "lectern", "map_table", "table_round", "candles_cluster", "statue_small", "brass_telescope"],
}

## Theme dressing: colliding props for corners, floor decor, wall-hung pieces (on north walls), basin pieces, pillars.
const DRESS := {
	&"fungal": {"corner": ["mushroom_giant", "spore_pod", "mushroom_giant", "stump"], "floor": ["mushroom_glow_cluster", "mushrooms", "roots", "bones_scatter"],
		"wall": ["fungus_shelf"], "basin": ["mushroom_glow_cluster", "roots", "log_fallen"], "breakable": "urn", "stairs": "stairs_wood",
		"pillar": "pillar_quoin", "floor_light": 0.16},
	&"drowned": {"corner": ["anchor_giant", "sunken_bell", "barrel", "crate"], "floor": ["bones_scatter", "fishing_nets", "coral_cluster"],
		"wall": ["banner_torn", "chains_hanging"], "basin": ["kelp_strands", "coral_cluster", "coffin", "boat_rowing"], "breakable": "barrel",
		"stairs": "stairs_wood", "pillar": "barnacle_pillar", "floor_light": 0.0},
	&"ember": {"corner": ["forge_furnace", "lava_crucible", "ore_cart", "anvil", "basalt_column"], "floor": ["rock_small", "weapons_discarded", "bones_scatter"],
		"wall": ["chain_hoist", "chains_hanging"], "basin": ["basalt_column", "rock_medium"], "breakable": "crate", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.0},
	&"rime": {"corner": ["ice_crystal_large", "frozen_coffin", "sarcophagus", "statue_knight"], "floor": ["snow_drift", "ice_crystal_small", "bones_scatter", "skull_pile"],
		"wall": ["icicles_hanging", "banner_torn"], "basin": ["ice_crystal_large", "ice_crystal_small"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.0},
	&"orrery": {"corner": ["crystal_pylon", "brass_telescope", "bookshelf_full", "lectern"], "floor": ["candles_cluster", "bones_scatter"],
		"wall": ["banner_torn"], "basin": ["floating_rock", "crystal_pylon"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.0},
}

var growth: Dictionary
var dungeon: StringName
var floor_n := 1
var dd: Dictionary
var fd: Dictionary
var th: Dictionary
var dress: Dictionary
var plan: Array
var cols := 0
var rows := 0
var height := {}            # Vector2i -> float: walking height of floors and bridges
var stair := {}             # Vector2i -> [dir char, base height]
var _joints := {}           # vertex key -> {x: n, z: n, low: bool, y: float, p: Vector3}
var _torches := 0
var _used := {}             # cells holding a gameplay marker or a big prop

func compose() -> void:
	var p := DataDungeons.parse(def.id)
	dungeon = p[0]
	floor_n = p[1]
	dd = DataDungeons.get_def(dungeon)
	growth = def.get_meta(&"dungeon_growth", DungeonGrowth.for_hero(Game.hero, dungeon))
	fd = DataDungeons.floor_def(dungeon, floor_n).duplicate(true)
	if floor_n > DataDungeons.floor_count(dungeon) and floor_n == DataDungeons.floor_count(dungeon) + int(growth.extra):
		fd["exit"] = fd.descent
		fd.erase("descent")
	th = DataDungeons.theme(dungeon)
	var tid := StringName(dd.get("theme", &"drowned"))
	dress = DRESS.get(tid, DataDungeons.theme_table("DRESS", tid, DRESS[&"drowned"]))
	plan = fd.get("plan", [])
	rows = plan.size()
	cols = String(plan[0]).length() if rows > 0 else 0
	MaterialLibrary.push_theme(String(dd.theme), th.stone)
	environment(th.env)
	_read()
	_floors()
	_basins()
	_stairs()
	_edges()
	_plinths()
	_pillars()
	_gameplay()
	_light_and_dress()
	_flush_batches()
	MaterialLibrary.pop_theme()
	var w := cols * WALL
	var d := rows * WALL
	set_bounds(AABB(Vector3(-w * 0.5, -6, -d * 0.5), Vector3(w, 22, d)))
	view("overview", Vector3(0, 0, 0), 0.0, 62.0, maxf(w, d) * 1.35, 45.0)
	view("topdown", Vector3(0, 0, 0), 0.0, 89.0, maxf(w, d) * 1.5, 50.0)
	var arr: Vector3 = cell_pos(fd.arrival)
	view("arrival", arr, 0.0, 52.0, 26.0)
	var goal: Vector2i = fd.get("descent", fd.get("exit", fd.arrival))
	view("goal", cell_pos(goal), 0.0, 52.0, 28.0)

# ------------------------------------------------------------------------------------------------------------
# plan reading

func ch(c: Vector2i) -> String:
	if c.y < 0 or c.y >= rows or c.x < 0 or c.x >= cols:
		return "."
	return String(plan[c.y])[c.x]

func is_floor(c: Vector2i) -> bool:
	return ch(c) in ["0", "1", "2"]

func is_stair(c: Vector2i) -> bool:
	return STAIR_DIR.has(ch(c))

func is_basin(c: Vector2i) -> bool:
	return ch(c) == "~"

func is_bridge(c: Vector2i) -> bool:
	return ch(c) == "="

func walkable(c: Vector2i) -> bool:
	return is_floor(c) or is_bridge(c) or is_stair(c)

## Map-local centre of a cell at its walking height (a stair: its foot).
func cell_pos(c: Vector2i) -> Vector3:
	var xz := DataDungeons.cell_xz(plan, c)
	var y: float = height.get(c, stair.get(c, [null, 0.0])[1])
	return Vector3(xz.x, y, xz.y)

func _read() -> void:
	for r in rows:
		for cc in cols:
			var c := Vector2i(cc, r)
			var k := ch(c)
			if k in ["0", "1", "2"]:
				height[c] = float(int(k)) * STOREY
			elif k == "=":
				height[c] = 0.0
	for r in rows:
		for cc in cols:
			var c := Vector2i(cc, r)
			var k := ch(c)
			if not STAIR_DIR.has(k):
				continue
			var dir: Vector2i = STAIR_DIR[k]
			var n := 0
			var q := c
			while ch(q) == k:
				q -= dir
				n += 1
			stair[c] = [k, float(height.get(q, 0.0)) + float(n - 1) * 2.0]

## Height a neighbour presents at the shared edge (void and basins count as the floor of storey 0 for masonry).
func _edge_height(c: Vector2i) -> float:
	if height.has(c):
		return height[c]
	if stair.has(c):
		return stair[c][1]
	return 0.0

# ------------------------------------------------------------------------------------------------------------
# floors, basins, stairs

func _floors() -> void:
	for c: Vector2i in height:
		var p := cell_pos(c)
		arch("floor_tile_4m", Vector3(p.x, p.y - 0.3, p.z), 90.0 * ((c.x * 7 + c.y * 3) % 4))
		if is_bridge(c):
			# the bridge rides on arches standing in the basin (the reference's arches in the water)
			var ew := is_basin(c + Vector2i(0, -1)) or is_basin(c + Vector2i(0, 1))
			arch("arch_quoin", Vector3(p.x, BASIN_FLOOR, p.z), 0.0 if ew else 90.0)
			for s in SIDES:
				if is_basin(c + SIDES[s]):
					_wall(c, s, 0.0, "wall_low", true)

func _basins() -> void:
	var liquid: Array = th.liquid
	# one liquid strip per run of basin/bridge cells in a row
	for r in rows:
		var start := -1
		for cc in cols + 1:
			var inside := cc < cols and (is_basin(Vector2i(cc, r)) or is_bridge(Vector2i(cc, r)))
			if inside and start < 0:
				start = cc
			elif not inside and start >= 0:
				var a := DataDungeons.cell_xz(plan, Vector2i(start, r)) - Vector2(2, 2)
				var rect := Rect2(a.x - 0.2, a.y - 0.2, (cc - start) * WALL + 0.4, WALL + 0.4)
				var wmi := water(rect, LIQUID_Y, liquid[0], liquid[1], float(liquid[2]), 1.6, 0.25)
				wmi.name = "Liquid_%d_%d" % [r, start]
				if r % 2 == 0:
					mist(rect.grow(-0.6), LIQUID_Y + 0.35, th.mist, 0.18)
				start = -1
	var n := 0
	for r in rows:
		for cc in cols:
			var c := Vector2i(cc, r)
			if not (is_basin(c) or is_bridge(c)):
				continue
			var p := cell_pos(c)
			arch("floor_tile_4m", Vector3(p.x, BASIN_FLOOR - 0.3, p.z), 90.0 * ((cc + r) % 4))
			for s in SIDES:
				var nb: Vector2i = c + SIDES[s]
				if not (is_basin(nb) or is_bridge(nb)):
					_wall(c, s, BASIN_FLOOR, "wall_stone_capped", false, false)
			if is_basin(c):
				n += 1
				if n % 3 == 0:
					light(Vector3(p.x, LIQUID_Y + 1.4, p.z), th.glow, 3.0, 12.0, false, false)
				# arches standing in the water, away from the bridges (the reference's cistern)
				if n % 5 == 2 and not _near_bridge(c) and _has("arch_quoin"):
					arch("arch_quoin", Vector3(p.x, BASIN_FLOOR, p.z), 0.0 if (c.x + c.y) % 2 == 0 else 90.0)

func _near_bridge(c: Vector2i) -> bool:
	for d in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
		if is_bridge(c + d) or walkable(c + d):
			return true
	return false

func _stairs() -> void:
	var piece: String = dress.stairs if _has(dress.stairs) else "stairs"
	for c: Vector2i in stair:
		var k: String = stair[c][0]
		var base: float = stair[c][1]
		var p := cell_pos(c)
		arch(piece, Vector3(p.x, base, p.z), STAIR_YAW[k])
		if base > 0.1:
			_block(Vector3(p.x, base * 0.5, p.z), Vector3(3.3 if k in ["^", "v"] else 4.0, base, 4.0 if k in ["^", "v"] else 3.3))

## A plain masonry block (the core under an upper stair flight).
func _block(center: Vector3, size: Vector3) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = MaterialLibrary.env("BH_StoneDark")
	mi.position = center
	geo.add_child(mi)

# ------------------------------------------------------------------------------------------------------------
# walls

## Place a wall piece on side `s` of cell `c` at height `y`. Records wall joints for the corner pillars.
func _wall(c: Vector2i, s: String, y: float, piece: String, low: bool, joints := true) -> void:
	var p := cell_pos(c)
	var off: Vector2i = SIDES[s]
	var mid := Vector3(p.x + off.x * 2.0, y, p.z + off.y * 2.0)
	var yaw: float = SIDE_YAW[s]
	arch(piece if _has(piece) else "wall_stone_capped", mid, yaw)
	if not joints:
		return
	var along_x := s == "north" or s == "south"
	for e in [-1.0, 1.0]:
		var v := mid + (Vector3(e * 2.0, 0, 0) if along_x else Vector3(0, 0, e * 2.0))
		var key := "%d,%d,%d" % [roundi(v.x), roundi(v.z), roundi(y)]
		var j: Dictionary = _joints.get_or_add(key, {"x": 0, "z": 0, "low": true, "p": v})
		j[&"x" if along_x else &"z"] = int(j.get(&"x" if along_x else &"z", 0)) + 1
		if not low:
			j["low"] = false

func _edges() -> void:
	for c: Vector2i in height:
		if is_bridge(c):
			continue
		var h: float = height[c]
		for s in SIDES:
			var nb: Vector2i = c + SIDES[s]
			var k := ch(nb)
			if k == ".":
				if s == "south":
					_wall(c, s, h, "wall_low", true)
				else:
					_wall(c, s, h, _full_piece(c, s, h), false)
			elif k == "~":
				_wall(c, s, h, "wall_low", true)
			elif is_stair(nb):
				var sk: String = stair[nb][0]
				var dir: Vector2i = STAIR_DIR[sk]
				var connects := nb - dir == c or nb + dir == c
				if not connects and h > float(stair[nb][1]) + 0.5:
					_wall(c, s, h, "wall_low", true)
			else:
				var hn := _edge_height(nb)
				if hn < h - 0.5:
					_wall(c, s, h, "gallery_railing" if _has("gallery_railing") else "wall_low", true)

## Full wall variety: windows on the upper storeys, the odd broken wall below.
func _full_piece(c: Vector2i, s: String, h: float) -> String:
	var r := hash(c) % 100
	if s == "north" and h > 0.0 and r < 22:
		return "wall_window"
	if s == "north" and h == 0.0 and r < 10:
		return "wall_window"
	if r > 94:
		return "wall_broken"
	return "wall_stone_capped"

## Masonry on every visible face of a raised cell (or an upper stair flight) down to what lies beside it.
func _plinths() -> void:
	var raised := {}
	for c: Vector2i in height:
		if height[c] > 0.1:
			raised[c] = height[c]
	for c: Vector2i in stair:
		if stair[c][1] > 0.1:
			raised[c] = stair[c][1]
	for c: Vector2i in raised:
		var h: float = raised[c]
		for s in ["south", "east", "west"]:
			var nb: Vector2i = c + SIDES[s]
			if is_stair(c) and is_stair(nb):
				continue
			if _stair_links(nb, c) or _stair_links(c, nb):
				continue           # a flight lands here: the way stays open
			var hn := _edge_height(nb) if walkable(nb) else 0.0
			var y := h - STOREY
			while y + STOREY > hn + 0.01:
				_wall(c, s, y, "wall_stone_capped", false, false)
				y -= STOREY

## True when stair cell `st` runs into cell `c` (c is its foot or its head).
func _stair_links(st: Vector2i, c: Vector2i) -> bool:
	if not stair.has(st):
		return false
	var dir: Vector2i = STAIR_DIR[stair[st][0]]
	return st + dir == c or st - dir == c

func _pillars() -> void:
	var piece: String = dress.pillar if _has(dress.pillar) else "pillar_quoin"
	for key in _joints:
		var j: Dictionary = _joints[key]
		var nx := int(j.get(&"x", 0))
		var nz := int(j.get(&"z", 0))
		# a straight run (two pieces in line) needs no pillar; ends and corners do
		if (nx == 2 and nz == 0) or (nz == 2 and nx == 0):
			continue
		var p: Vector3 = j.p
		if j.low:
			arch("pillar", p).scale = Vector3(1, 0.36, 1)
		else:
			arch(piece, p).scale = Vector3(1, 1.02, 1)

# ------------------------------------------------------------------------------------------------------------
# gameplay

func _gameplay() -> void:
	var surface: Dictionary = dd.surface
	var arr: Vector2i = fd.arrival
	var ap := cell_pos(arr)
	_used[arr] = true
	var up_map: StringName
	var up_spawn: StringName
	var up_name: String
	if floor_n == 1:
		up_map = surface.map
		up_spawn = DataDungeons.gate_id(dungeon)
		up_name = DB.map_def(up_map).display_name if DB.map_def(up_map) else String(up_map)
	else:
		up_map = DataDungeons.map_id(dungeon, floor_n - 1)
		up_spawn = &"descent"
		up_name = DataDungeons.floor_title(dungeon, floor_n - 1)
	var t := teleporter(StringName("dg_%s_%d_up" % [dungeon, floor_n]), ap, up_map, up_spawn, up_name, 0.0)
	t.rune_tint = th.rune
	t.set_meta(&"dungeon_up", dungeon)
	var sp := _beside(arr)
	spawn(&"arrival", sp, 180.0)
	spawn(&"start", sp, 180.0)
	brazier_pair(ap)
	var goal_key := "descent" if fd.has("descent") else "exit"
	var gc: Vector2i = fd[goal_key]
	var gp := cell_pos(gc)
	_used[gc] = true
	if goal_key == "descent":
		var flag := DataDungeons.seal_flag(dungeon, floor_n)
		var hint := "Sealed. Defeat the Seal Keepers of this floor to open the way down." if floor_n != DataDungeons.champion_floor(dungeon) else \
			"Sealed. %s holds the seal." % dd.miniboss.name
		var dt := teleporter(StringName("dg_%s_%d_down" % [dungeon, floor_n]), gp, DataDungeons.map_id(dungeon, floor_n + 1), &"arrival",
			DataDungeons.floor_title(dungeon, floor_n + 1), 0.0, true, flag, hint)
		dt.rune_tint = th.rune
		spawn(&"descent", _beside(gc), 180.0)
		_seal_ward(gp, flag)
	else:
		var flag := DataDungeons.seal_flag(dungeon, floor_n) if floor_n > DataDungeons.floor_count(dungeon) else DataDungeons.cleared_flag(dungeon)
		var et := teleporter(StringName("dg_%s_%d_exit" % [dungeon, floor_n]), gp, surface.map, DataDungeons.gate_id(dungeon),
			DB.map_def(surface.map).display_name if DB.map_def(surface.map) else String(surface.map), 0.0, true, flag,
			"Defeat the Seal Keepers to open the way home." if floor_n > DataDungeons.floor_count(dungeon) else "The way home wakes when the lord of this place falls.")
		et.rune_tint = th.rune
		spawn(&"exit", _beside(gc), 180.0)
		_seal_ward(gp, flag)
	brazier_pair(gp)
	# The original sanctum retains its exit and boss; deeper halls branch from the cleared arena.
	if floor_n == DataDungeons.floor_count(dungeon) and int(growth.extra) > 0:
		var deep_pos := cell_pos(fd.boss)
		var dt := teleporter(StringName("dg_%s_depths" % dungeon), deep_pos, DataDungeons.map_id(dungeon, floor_n + 1), &"arrival",
			"Enter the deeper halls", 0.0, true, DataDungeons.cleared_flag(dungeon), "Defeat the dungeon lord to enter the deeper halls.")
		dt.rune_tint = th.rune
		spawn(&"descent", _beside(fd.boss), 180.0)
	# camps
	var pools: Dictionary = dd.pools
	var i := 0
	for cp in fd.get("camps", []):
		var cell: Vector2i = cp[0]
		_used[cell] = true
		enemy_zone("camp_%d" % i, cell_pos(cell), 4.5, pools.get(cp[1], pools.a), int(cp[2]), float(cp[3]))
		i += 1
	if fd.has("seal"):
		var sc: Vector2i = fd.seal
		_used[sc] = true
		enemy_zone(DataDungeons.SEAL_ZONE, cell_pos(sc), 4.0, pools.seal, 5, 1.0)
	if fd.has("boss"):
		var bc: Vector2i = fd.boss
		_used[bc] = true
		var m := Marker3D.new()
		m.name = "BossSpawn"
		m.position = cell_pos(bc)
		m.add_to_group(&"boss_spawn")
		m.set_meta(&"boss", String(dd.boss))
		m.set_meta(&"flag", String(DataDungeons.cleared_flag(dungeon)))
		m.set_meta(&"dungeon", String(dungeon))
		markers.add_child(m)
	if fd.has("miniboss"):
		_used[fd.miniboss] = true
	# treasure
	var n := 0
	for cp in fd.get("chests", []):
		var cell: Vector2i = cp[0]
		_used[cell] = true
		n += 1
		var chest := TreasureChest.new().setup(int(cp[1]), "%s/%d" % [def.id, n], def.level_max, DataDungeons.CHEST_RESPAWN)
		if floor_n > DataDungeons.floor_count(dungeon):
			chest.guardian_zone = DataDungeons.SEAL_ZONE
		var p := cell_pos(cell)
		# against the nearest wall so it never blocks a passage
		var push := Vector3.ZERO
		for s in ["north", "west", "east"]:
			if not walkable(cell + SIDES[s]):
				push = Vector3(SIDES[s].x, 0, SIDES[s].y) * 1.0
				break
		chest.position = p + push
		chest.rotation.y = atan2(-push.x, -push.z) if push != Vector3.ZERO else 0.0
		props.add_child(chest)
	var rt := DungeonRuntime.new()
	rt.name = "DungeonRuntime"
	rt.dungeon = dungeon
	rt.floor_n = floor_n
	root.add_child(rt)

## A spawn spot beside a marker cell: the cell to the south if it is walkable at the same height, else another side.
func _beside(c: Vector2i) -> Vector3:
	var p := cell_pos(c)
	for d in [Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1)]:
		var nb: Vector2i = c + d
		if height.has(nb) and absf(height[nb] - p.y) < 0.1 and not is_bridge(nb):
			return p + Vector3(d.x, 0, d.y) * 3.0
	return p + Vector3(0, 0, 1.6)

func brazier_pair(p: Vector3) -> void:
	for sx in [-1.0, 1.0]:
		var q := p + Vector3(sx * 1.55, 0, 1.2)
		var n := kit("brazier", q, 0.0, 0.8)
		var f := socket_pos(n, "flame")
		flame(f, 1.0)
	light(p + Vector3(0, 2.4, 1.0), th.torch, 2.6, 9.0, false, true)

## The violet membrane over a sealed portal: vanishes (MapBuilder.hide_when) once its flag is set.
func _seal_ward(p: Vector3, flag: StringName) -> void:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 1.6
	cm.bottom_radius = 1.7
	cm.height = 3.2
	cm.cap_top = false
	cm.cap_bottom = false
	mi.mesh = cm
	mi.material_override = WorldShaders.shaft_material(Color(0.65, 0.35, 1.0), 0.55) if not Perf.lite else VFXLib.glow_material(Color(0.6, 0.3, 1.0), 0.6)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = p + Vector3(0, 1.6, 0)
	mi.name = "SealWard"
	deco.add_child(mi)
	hide_when(mi, flag)

# ------------------------------------------------------------------------------------------------------------
# light and dressing

func _light_and_dress() -> void:
	var cells: Array = height.keys()
	cells.sort()
	for c: Vector2i in cells:
		if is_bridge(c):
			continue
		var h: float = height[c]
		var p := cell_pos(c)
		var north_void := ch(c + SIDES.north) == "."
		# torches on north walls (every other cell of a run), themed wall pieces between them
		if north_void:
			var wall_z := p.z - 2.0 + 0.42
			if (c.x + c.y) % 2 == 0 and _torches < MAX_TORCHES:
				_torches += 1
				_sconce(Vector3(p.x, h + 2.7, wall_z))
			elif rng.randf() < 0.55:
				var wp: String = dress.wall[rng.randi() % (dress.wall as Array).size()]
				if _has(wp):
					var hang := wp in ["chain_hoist", "icicles_hanging"]
					kit(wp, Vector3(p.x + rng.randf_range(-0.8, 0.8), h + (4.0 if hang else 2.4), wall_z - 0.05), 0.0, 1.0, deco)
		# the tall back wall of a lower room: a raised terrace to the north
		var nb_n: Vector2i = c + SIDES.north
		if height.has(nb_n) and height[nb_n] > h + 0.5 and (c.x + c.y) % 2 == 1 and _torches < MAX_TORCHES:
			_torches += 1
			_sconce(Vector3(p.x, h + 2.6, p.z - 2.0 + 0.42))
		for side in ["west", "east"]:
			if ch(c + SIDES[side]) == "." and c.y % 3 == 0 and _torches < MAX_TORCHES:
				_torches += 1
				var sx := -1.0 if side == "west" else 1.0
				_sconce_side(Vector3(p.x + sx * (2.0 - 0.42), h + 2.7, p.z), sx)
		if _used.has(c):
			continue
		# clutter against a wall (room cells only: a corridor keeps its way clear)
		var walls := []
		for sd in ["north", "west", "east"]:
			if ch(c + SIDES[sd]) == "." or (height.has(c + SIDES[sd]) and height[c + SIDES[sd]] > h + 0.5):
				walls.append(sd)
		var open_n := 0
		for sd in SIDES:
			if height.has(c + SIDES[sd]) and absf(height[c + SIDES[sd]] - h) < 0.1:
				open_n += 1
		if not walls.is_empty() and open_n >= 2 and rng.randf() < 0.42:
			var list: Array = CLUTTER.get(StringName(dd.theme), DataDungeons.theme_table("CLUTTER", StringName(dd.theme), []))
			var sd: String = walls[rng.randi() % walls.size()]
			var dir: Vector2i = SIDES[sd]
			var n_items := rng.randi_range(1, 3)
			for k in n_items:
				var pc2: String = list[rng.randi() % list.size()] if not list.is_empty() else ""
				if pc2 == "" or not _has(pc2):
					continue
				var along := Vector3(dir.y, 0, dir.x) * rng.randf_range(-1.3, 1.3)
				var pos := p + Vector3(dir.x, 0, dir.y) * 1.25 + along
				var yaw := rad_to_deg(atan2(-float(dir.x), -float(dir.y))) + rng.randf_range(-12, 12)
				if pc2 in ["barrel", "crate", "urn"]:
					breakable(pc2, pos, rng.randf() * 360.0, 12.0 if pc2 == "urn" else 20.0)
				else:
					kit(pc2, pos, yaw, 1.0)
			_used[c] = true
			continue
		# a big prop in corners (two perpendicular void sides)
		var vn := ch(c + SIDES.north) == "."
		var vw := ch(c + SIDES.west) == "."
		var ve := ch(c + SIDES.east) == "."
		if vn and (vw or ve) and rng.randf() < 0.75:
			var pc: String = dress.corner[rng.randi() % (dress.corner as Array).size()]
			if _has(pc):
				var off := Vector3(-1.1 if vw else 1.1, 0, -1.1)
				var big := pc in ["mushroom_giant", "forge_furnace", "armillary_sphere"]
				kit(pc, p + off * (0.6 if big else 1.0), rng.randf_range(-20, 20) + (0.0 if not big else 0.0), 1.0 if not big else 0.85)
				if pc in ["forge_furnace", "lava_crucible", "crystal_pylon", "mushroom_giant"]:
					light(p + off + Vector3(0, 2.2, 0.6), th.glow, 2.0, 8.0, false, true)
				_used[c] = true
				continue
		# breakables against walls
		if (vn or vw or ve) and rng.randf() < 0.14:
			breakable(String(dress.breakable), p + Vector3((-1.3 if vw else (1.3 if ve else rng.randf_range(-1, 1))), 0, -1.3 if vn else 0.0),
				rng.randf() * 360.0, 12.0 if dress.breakable == "urn" else 20.0)
		# floor scatter (non-colliding)
		if rng.randf() < 0.22:
			var fp: String = dress.floor[rng.randi() % (dress.floor as Array).size()]
			if _has(fp):
				decor(fp, p + Vector3(rng.randf_range(-1.5, 1.5), 0, rng.randf_range(-1.5, 1.5)), rng.randf() * 360.0, rng.randf_range(0.7, 1.1), false)
	# the basin's own dressing
	var bn := 0
	var basin_cells: Array = []
	for r in rows:
		for cc in cols:
			if is_basin(Vector2i(cc, r)):
				basin_cells.append(Vector2i(cc, r))
	for c: Vector2i in basin_cells:
		bn += 1
		if bn % 3 != 1:
			continue
		var bp: String = dress.basin[rng.randi() % (dress.basin as Array).size()]
		if not _has(bp):
			continue
		var p := cell_pos(c)
		var y := BASIN_FLOOR
		if bp in ["boat_rowing", "coffin"]:
			y = LIQUID_Y - 0.3
		elif bp == "floating_rock":
			y = LIQUID_Y + 1.2
		kit(bp, Vector3(p.x + rng.randf_range(-1, 1), y, p.z + rng.randf_range(-1, 1)), rng.randf() * 360.0, rng.randf_range(0.9, 1.3), deco)
	# the Orrery's star-map floors: an armillary rising out of the void well
	if dd.theme == &"orrery" and not basin_cells.is_empty() and _has("armillary_sphere"):
		var sum := Vector3.ZERO
		for c: Vector2i in basin_cells:
			sum += cell_pos(c)
		var ctr := sum / float(basin_cells.size())
		var arm := kit("armillary_sphere", Vector3(ctr.x, BASIN_FLOOR, ctr.z), 0.0, 1.5, deco)
		for rn in ["ring_a", "ring_b", "ring_c"]:
			var ring := arm.find_child(rn, true, false) as Node3D
			if ring:
				# spin each ring about the sphere's centre (its own origin) in its own plane
				var sp := Spinner.new()
				sp.axis = Vector3.UP
				sp.speed = {"ring_a": 0.35, "ring_b": -0.5, "ring_c": 0.7}[rn]
				sp.transform = ring.transform
				var par := ring.get_parent()
				par.add_child(sp)
				par.remove_child(ring)
				sp.add_child(ring)
				ring.transform = Transform3D.IDENTITY
		light(Vector3(ctr.x, 1.5, ctr.z), th.glow, 3.0, 14.0, false, true)
	if DataDungeons.is_special(dungeon):
		_special_centrepiece(basin_cells)
	# a little theme light floating over each storey so the upper galleries never sink into darkness
	for c: Vector2i in cells:
		if height[c] > 0.1 and (c.x * 3 + c.y * 5) % 7 == 0:
			light(cell_pos(c) + Vector3(0, 3.0, 0), th.torch, 1.2, 9.0, false, false)

## bh-028: each special dungeon's centrepiece. Pieces that grow out of water (crystals, soul-fire, the island ring)
## stand in the floor's largest basin, on the basin cell nearest its middle (over a split basin the mean of all cells
## lands on solid floor), and need a pool of four cells or more. The sun and the moon hang over that pool, or over the
## middle of the ground floor when there is none (the sanctums).
func _special_centrepiece(basin_cells: Array) -> void:
	var left := {}
	for c: Vector2i in basin_cells:
		left[c] = true
	var best: Array = []
	while not left.is_empty():
		var seed_cell: Vector2i = left.keys()[0]
		left.erase(seed_cell)
		var pool := [seed_cell]
		var i := 0
		while i < pool.size():
			for d in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
				var nb: Vector2i = pool[i] + d
				if left.has(nb):
					left.erase(nb)
					pool.append(nb)
			i += 1
		if pool.size() > best.size():
			best = pool
	var has_pool := best.size() >= 4
	var ctr := Vector3.ZERO
	if has_pool:
		var mean := Vector3.ZERO
		for c: Vector2i in best:
			mean += cell_pos(c)
		mean /= float(best.size())
		ctr = cell_pos(best[0])
		for c: Vector2i in best:
			if cell_pos(c).distance_squared_to(mean) < ctr.distance_squared_to(mean):
				ctr = cell_pos(c)
	else:
		var n := 0
		for c: Vector2i in height:
			if height[c] < 0.1:
				ctr += cell_pos(c)
				n += 1
		if n == 0:
			return
		ctr /= float(n)
	ctr.y = 0.0
	if not has_pool and not StringName(dd.theme) in [&"eclipse", &"solar"]:
		return
	match StringName(dd.theme):
		&"prism":
			# a cluster of giant crystals growing out of the pool
			if _has("ice_crystal_large"):
				kit("ice_crystal_large", Vector3(ctr.x, BASIN_FLOOR, ctr.z), rng.randf() * 360.0, 2.4, deco)
			for k in 5:
				var a := TAU * k / 5.0 + 0.4
				var p := ctr + Vector3(cos(a), 0, sin(a)) * 2.6
				if _has("crystal_pylon"):
					kit("crystal_pylon", Vector3(p.x, BASIN_FLOOR, p.z), rad_to_deg(a), rng.randf_range(1.3, 1.8), deco)
			light(Vector3(ctr.x, 2.0, ctr.z), th.glow, 3.4, 16.0, false, true)
		&"underworld":
			# four columns of soul-fire standing on the ghost river
			for k in 4:
				var a := TAU * k / 4.0 + 0.78
				var p := ctr + Vector3(cos(a), 0, sin(a)) * 3.2
				if _has("obelisk_corrupted"):
					kit("obelisk_corrupted", Vector3(p.x, BASIN_FLOOR, p.z), rad_to_deg(a), 1.4, deco)
				for h in [0.0, 1.4, 2.8]:
					flame(Vector3(p.x, LIQUID_Y + 1.0 + h, p.z), 1.1 - h * 0.15)
				light(Vector3(p.x, LIQUID_Y + 2.4, p.z), th.glow, 2.4, 10.0, false, true)
		&"aether":
			# a ring of islands turning slowly round a crystal spire
			if _has("crystal_pylon"):
				kit("crystal_pylon", Vector3(ctr.x, BASIN_FLOOR, ctr.z), 0.0, 2.2, deco)
			var spin := Spinner.new()
			spin.axis = Vector3.UP
			spin.speed = 0.12
			spin.position = ctr
			deco.add_child(spin)
			for k in 5:
				var a := TAU * k / 5.0
				if _has("floating_rock"):
					kit("floating_rock", Vector3(cos(a) * 3.6, LIQUID_Y + 2.2 + (k % 2) * 1.4, sin(a) * 3.6), rad_to_deg(a), rng.randf_range(1.1, 1.6), spin)
			light(Vector3(ctr.x, 2.4, ctr.z), th.glow, 3.0, 16.0, false, true)
		&"eclipse":
			# a black moon with a silver rim hanging over the basin
			var moon := _orb(0.0, Color(0.02, 0.02, 0.03), 0.0, 1.9)
			moon.position = ctr + Vector3(0, 5.6, 0)
			var rim := MeshInstance3D.new()
			var tm := TorusMesh.new()
			tm.inner_radius = 2.0
			tm.outer_radius = 2.25
			tm.rings = 48
			rim.mesh = tm
			rim.material_override = _glow_mat(Color(0.85, 0.85, 1.0), 3.0)
			rim.rotation_degrees = Vector3(90, 0, 0)
			var turn := Spinner.new()
			turn.axis = Vector3.UP
			turn.speed = 0.08
			turn.position = moon.position
			deco.add_child(turn)
			turn.add_child(rim)
			light(moon.position + Vector3(0, -2.4, 0), th.glow, 2.6, 14.0, false, false)
		&"solar":
			# the drowned sun: a burning orb above the water
			var sun := _orb(1.0, Color(1.0, 0.72, 0.3), 5.0, 1.6)
			sun.position = ctr + Vector3(0, 5.4, 0)
			var corona := _orb(1.0, Color(1.0, 0.55, 0.15), 1.6, 2.1)
			corona.position = sun.position
			(corona.material_override as StandardMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			(corona.material_override as StandardMaterial3D).albedo_color.a = 0.25
			light(sun.position, Color(1.0, 0.75, 0.4), 4.5, 22.0, false, true)

## An unlit glowing material (energy 0: plain matte).
func _glow_mat(c: Color, energy: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	if energy > 0.0:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = energy
	m.roughness = 0.35
	return m

## A sphere for the special centrepieces (no collision; `alpha` 1 = opaque).
func _orb(alpha: float, c: Color, energy: float, radius: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	mi.mesh = sm
	var m := _glow_mat(Color(c.r, c.g, c.b, alpha), energy)
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if energy > 0.0 else BaseMaterial3D.SHADING_MODE_PER_PIXEL
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	deco.add_child(mi)
	return mi

## A torch on a west (sx -1) or east (sx 1) wall, facing into the room.
func _sconce_side(pos: Vector3, sx: float) -> void:
	var n := kit("torch_sconce", pos, 90.0 if sx < 0 else -90.0, 1.0, deco)
	var f := socket_pos(n, "flame")
	flame(f, 0.8)
	light(f + Vector3(-sx * 0.35, 0.25, 0), th.torch, 2.6, 10.0, false, true)

## A wall torch in the theme's flame colour.
func _sconce(pos: Vector3) -> void:
	var n := kit("torch_sconce", pos, 0.0, 1.0, deco)
	var f := socket_pos(n, "flame")
	flame(f, 0.8)
	light(f + Vector3(0, 0.25, 0.35), th.torch, 2.8, 10.0, false, true)

static var _exists := {}

func _has(asset: String) -> bool:
	if not _exists.has(asset):
		_exists[asset] = ResourceLoader.exists(ENV_DIR % asset)
	return _exists[asset]
