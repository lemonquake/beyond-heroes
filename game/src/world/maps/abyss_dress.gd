class_name AbyssDress
## bh-042: the dressing of an Abyss floor (dungeon.gd calls dress() instead of the fill lights of the other dungeons).
## The Abyss is dark on purpose: a handful of torches (DataDungeonsAbyss.MAX_TORCHES), the portals' braziers and a few
## pools of light the floor is built round — a candle-lit chandelier over the largest hall, candles on an altar or a
## table, a fire pit in the foundry — and the hero's own lantern (DungeonRuntime). Everything else is shape in the dark:
## Poly Haven CC0 statues, iron gates and doors on the dead-end walls, lion-head fountains, busts, mossy rock.

const POOLS_OF_LIGHT := 3

## Theme -> the pieces it is dressed with (ph_* are Poly Haven props; the others the project kit).
const PIECES := {
	&"hollow": {"statue": ["ph_gothic_statue", "statue_knight", "ph_marble_bust_01"], "door": ["ph_large_castle_door", "ph_large_iron_gate"],
		"wall": ["ph_lion_head"], "table": ["ph_brass_candleholders", "ph_wooden_candlestick", "candles_cluster"], "rock": ["rubble_pile"],
		"hang": ["ph_chandelier_02", "ph_lantern_chandelier_01"]},
	&"sunless": {"statue": ["statue_collapsed", "ph_gothic_statue"], "door": ["ph_large_iron_gate"],
		"wall": ["ph_lion_head"], "table": ["ph_vintage_oil_lamp", "ph_lantern_01"], "rock": ["ph_rock_moss_set_01", "ph_rock_07"],
		"hang": ["ph_lantern_chandelier_01"]},
	&"ashgrave": {"statue": ["statue_knight", "armor_stand"], "door": ["ph_large_iron_gate", "ph_large_castle_door"],
		"wall": ["ph_kite_shield", "ph_ornate_medieval_mace"], "table": ["ph_stone_fire_pit"], "rock": ["rubble_pile", "ph_rock_07"],
		"hang": ["ph_lantern_chandelier_01"]},
	&"weeping": {"statue": ["ph_gothic_statue", "statue_knight", "armor_stand"], "door": ["ph_large_castle_door", "ph_large_iron_gate"],
		"wall": ["ph_kite_shield", "ph_lion_head"], "table": ["ph_brass_candleholders", "candles_cluster"], "rock": ["ice_crystal_large"],
		"hang": ["ph_chandelier_02"]},
	&"throne": {"statue": ["ph_gothic_statue", "obelisk_corrupted", "ph_marble_bust_01"], "door": ["ph_large_iron_gate"],
		"wall": ["ph_lion_head", "ph_ornate_medieval_dagger"], "table": ["ph_brass_goblets", "ph_brass_candleholders"], "rock": ["rubble_pile"],
		"hang": ["ph_chandelier_02"]},
}

## Poly Haven props come at their real size; these are scaled to read at the game's distance (a 17 cm stone becomes a
## boulder, a 0.7 m chandelier a hall's).
const SCALE := {"ph_rock_07": 9.0, "ph_chandelier_02": 2.4, "ph_lantern_chandelier_01": 2.2, "ph_lion_head": 2.2, "ph_kite_shield": 1.3,
	"ph_ornate_medieval_mace": 1.8, "ph_ornate_medieval_dagger": 2.2, "ph_marble_bust_01": 1.6, "ph_brass_candleholders": 1.0,
	"ph_wooden_candlestick": 1.6, "ph_vintage_oil_lamp": 1.4, "ph_lantern_01": 2.0, "ph_brass_goblets": 1.4, "ph_gothic_statue": 1.25,
	"ph_large_castle_door": 1.25, "ph_large_iron_gate": 1.2, "ph_rock_moss_set_01": 0.55, "ph_stone_fire_pit": 1.2}

static func sc(name: String, base := 1.0) -> float:
	return base * float(SCALE.get(name, 1.0))

static func dress(b) -> void:
	var tid := StringName(b.dd.get("theme", &"hollow"))
	var set: Dictionary = PIECES.get(tid, PIECES[&"hollow"])
	var cells: Array = b.height.keys()
	cells.sort()
	var lit := 0
	# 1. the largest open hall gets a chandelier (and one of the floor's pools of light)
	var hall := _largest_open(b, cells)
	if not hall.is_empty():
		var hc: Vector2i = hall.center
		var hp: Vector3 = b.cell_pos(hc)
		var hang := _pick(b, set.hang)
		if hang != "":
			b.kit(hang, hp + Vector3(0, 3.2, 0), b.rng.randf() * 360.0, sc(hang), b.deco)
			b.light(hp + Vector3(0, 3.2, 0), b.th.torch, 1.8, 11.0, false, true)
			_motes(b, hp + Vector3(0, 3.0, 0), b.th.torch)
			lit += 1
	# 2. statues at the corners of rooms, doors and gates on dead-end north walls, trophies on the walls
	for c: Vector2i in cells:
		if b._used.has(c) or b.is_bridge(c) or b.is_secret(c):
			continue
		var p: Vector3 = b.cell_pos(c)
		var vn: bool = b.ch(c + Vector2i(0, -1)) == "."
		var vw: bool = b.ch(c + Vector2i(-1, 0)) == "."
		var ve: bool = b.ch(c + Vector2i(1, 0)) == "."
		var h := hash(c)
		if vn and (vw or ve) and h % 3 == 0:
			var st := _pick(b, set.statue)
			if st != "":
				b.kit(st, p + Vector3(-1.2 if vw else 1.2, 0, -1.2), 180.0 + (35.0 if vw else -35.0), sc(st))
				b._used[c] = true
				continue
		if vn and not vw and not ve and h % 9 == 1:
			var dr := _pick(b, set.door)
			if dr != "":
				b.kit(dr, Vector3(p.x, p.y, p.z - 1.75), 0.0, sc(dr))
				b._used[c] = true
				continue
		if vn and h % 7 == 2:
			var wp := _pick(b, set.wall)
			if wp != "":
				b.kit(wp, Vector3(p.x + b.rng.randf_range(-0.8, 0.8), p.y + 2.0, p.z - 1.68), 0.0, sc(wp), b.deco)
		if (vw or ve) and h % 11 == 3:
			var rk := _pick(b, set.rock)
			if rk != "":
				b.kit(rk, p + Vector3(-1.3 if vw else 1.3, 0, b.rng.randf_range(-1, 1)), b.rng.randf() * 360.0, sc(rk, 0.8), b.deco)
	# 3. a couple more small pools of light: candles on a table or an altar, a fire pit in the foundry
	for c: Vector2i in cells:
		if lit >= POOLS_OF_LIGHT:
			break
		if b._used.has(c) or b.is_bridge(c) or b.is_secret(c) or hash(c) % 13 != 4:
			continue
		var p: Vector3 = b.cell_pos(c)
		var tp := _pick(b, set.table)
		if tp == "":
			continue
		var fire := tp == "ph_stone_fire_pit"
		if not fire and b._has("kd_table"):
			b.kit("kd_table", p, b.rng.randf() * 360.0, 1.0)
			b.kit(tp, p + Vector3(0, 0.95, 0), b.rng.randf() * 360.0, sc(tp), b.deco)
		else:
			b.kit(tp, p, b.rng.randf() * 360.0, sc(tp))
		if fire:
			b.flame(p + Vector3(0, 0.5, 0), 1.2)
		b.light(p + Vector3(0, 1.6, 0), b.th.torch, 1.0 if not fire else 1.6, 6.0 if not fire else 8.0, false, true)
		b._used[c] = true
		lit += 1

static func _pick(b, list: Array) -> String:
	var ok := list.filter(func(n): return b._has(n))
	if ok.is_empty():
		return ""
	return String(ok[b.rng.randi() % ok.size()])

## The biggest block of ground-height cells with open cells all round (a hall's middle), or {}.
static func _largest_open(b, cells: Array) -> Dictionary:
	var best := {}
	var best_n := 0
	for c: Vector2i in cells:
		if b._used.has(c) or b.is_bridge(c):
			continue
		var h: float = b.height[c]
		var n := 0
		for dx in range(-1, 2):
			for dy in range(-1, 2):
				var q := c + Vector2i(dx, dy)
				if b.height.has(q) and absf(float(b.height[q]) - h) < 0.1 and not b.is_bridge(q):
					n += 1
		if n == 9 and (best.is_empty() or hash(c) % 5 == 0 or n > best_n):
			best = {"center": c}
			best_n = n
	return best

static func _motes(b, at: Vector3, c: Color) -> void:
	var p := VFXLib.particles(Color(c.r, c.g, c.b, 0.5), 10, 3.0, false, 0.06, 0.15, 60.0, Vector3(0, -0.05, 0), 2.0)
	p.position = at
	b.deco.add_child(p)
