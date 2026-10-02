p = 'game/src/world/maps/dungeon.gd'
s = open(p, encoding='utf-8').read()

# 1) the role dresser runs first; the old random clutter and corner props go (breakables and floor scatter stay)
old_start = '''func _light_and_dress() -> void:
	var cells: Array = height.keys()
	cells.sort()
	for c: Vector2i in cells:'''
new_start = '''func _light_and_dress() -> void:
	_dress_rooms()
	var cells: Array = height.keys()
	cells.sort()
	for c: Vector2i in cells:'''
assert old_start in s
s = s.replace(old_start, new_start)

a = s.index('		# clutter against a wall (room cells only: a corridor keeps its way clear)')
b = s.index('		# breakables against walls')
replacement = '''		# (map-design pass: walls and corners are dressed by room role in _dress_rooms; these are the leftovers)
		var vn := ch(c + SIDES.north) == "."
		var vw := ch(c + SIDES.west) == "."
		var ve := ch(c + SIDES.east) == "."
'''
s = s[:a] + replacement + s[b:]

s += '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): rooms with a purpose (DataDungeonRoles). A floor's rooms are its connected cells of one
# storey; each gets a role from the floor's own markers — the arrival room, the seal chamber (and the goal's room), the
# boss arena — and the others become work/storage, the theme's own function (burial, study, ritual, organic...) or a
# traversal room on a basin edge. A role dresses a few wall cells with its motifs. Never dressed: cells holding a
# marker, camp, chest or the arrival/goal, their neighbours, cells beside stairs or bridges, one-cell corridors and the
# south (camera) side. Deep floors swap a work motif for the theme's decay. Lights from motifs are capped and High only.

const ROLE_LIGHTS := 5
var _rooms: Array = []
var _role_lights := 0
var _room_rng := RandomNumberGenerator.new()

## Connected cells of one storey (bridges excluded): the floor's rooms.
func _regions() -> Array:
	var seen := {}
	var out: Array = []
	var cells: Array = height.keys()
	cells.sort()
	for c: Vector2i in cells:
		if seen.has(c) or is_bridge(c):
			continue
		var h: float = height[c]
		var reg: Array = [c]
		seen[c] = true
		var i := 0
		while i < reg.size():
			for d: Vector2i in SIDES.values():
				var nb: Vector2i = reg[i] + d
				if height.has(nb) and not is_bridge(nb) and not seen.has(nb) and absf(float(height[nb]) - h) < 0.1:
					seen[nb] = true
					reg.append(nb)
			i += 1
		out.append(reg)
	return out

## A cell next to something that must stay open (a marker cell, stairs, a bridge, a basin edge's stair head).
func _protected(c: Vector2i, keep: Dictionary) -> bool:
	for dx in [-1, 0, 1]:
		for dz in [-1, 0, 1]:
			var q := c + Vector2i(dx, dz)
			if keep.has(q) or is_stair(q) or is_bridge(q):
				return true
	return false

## Wall sides of a cell a motif can stand against (north first: the back wall faces the camera).
func _wall_sides(c: Vector2i) -> Array:
	var h: float = height[c]
	var out: Array = []
	for sd in ["north", "west", "east"]:
		var nb: Vector2i = c + SIDES[sd]
		if ch(nb) == "." or (height.has(nb) and float(height[nb]) > h + 0.5):
			out.append(sd)
	if out.has("west") and out.has("east"):
		return []            # a one-cell corridor keeps its way clear
	var open_n := 0
	for sd in SIDES:
		var nb: Vector2i = c + SIDES[sd]
		if height.has(nb) and absf(float(height[nb]) - h) < 0.1:
			open_n += 1
	return out if open_n >= 2 else []

func _dress_rooms() -> void:
	_room_rng.seed = hash(String(def.id) + "/rooms")
	var t := DataDungeonRoles.table(StringName(dd.theme), dungeon)
	var keep := {}
	for k in ["arrival", "descent", "exit", "seal", "boss", "miniboss"]:
		if fd.has(k):
			keep[fd[k]] = k
	for cp in fd.get("camps", []):
		keep[cp[0]] = "camp"
	for cp in fd.get("chests", []):
		keep[cp[0]] = "chest"
	var deep := floor_n >= 3 or floor_n > DataDungeons.floor_count(dungeon)
	var regs := _regions()
	regs.sort_custom(func(x, y): return x.size() > y.size())
	var n_free := 0
	for reg: Array in regs:
		var role := ""
		for c: Vector2i in reg:
			match String(keep.get(c, "")):
				"boss": role = "boss"
				"arrival": role = "arrival" if role != "boss" else role
				"seal", "miniboss", "descent", "exit":
					if role == "":
						role = "seal"
		var edge := reg.any(func(c): return SIDES.values().any(func(d): return is_basin(c + d) or is_bridge(c + d)))
		if role == "":
			if edge and reg.size() <= 8:
				role = "traversal"
			else:
				role = "function" if n_free % 2 == 0 else "work"
				n_free += 1
		var rec := {"role": role, "cells": reg.size(), "groups": []}
		if role == "boss":
			_boss_silhouettes(reg, t, rec)
		else:
			var want := 1 if role in ["arrival", "seal", "traversal"] else clampi(reg.size() / 5, 1, 3)
			var cands: Array = []
			for c: Vector2i in reg:
				if _used.has(c) or _protected(c, keep) or _wall_sides(c).is_empty():
					continue
				cands.append(c)
			# spread out: shuffle deterministically, then take cells at least two apart
			for i in range(cands.size() - 1, 0, -1):
				var j := _room_rng.randi_range(0, i)
				var tmp = cands[i]
				cands[i] = cands[j]
				cands[j] = tmp
			var taken: Array = []
			var list: Array = t.get(role, t.function)
			for c: Vector2i in cands:
				if taken.size() >= want:
					break
				if taken.any(func(q): return absi(q.x - c.x) + absi(q.y - c.y) < 2):
					continue
				var motif: String = list[(taken.size() + _room_rng.randi()) % list.size()]
				if role == "work" and deep and taken.size() == 0:
					motif = (t.decay as Array)[0]
				if _place_motif(motif, c):
					taken.append(c)
					_used[c] = true
					rec.groups.append({"motif": motif, "cell": [c.x, c.y]})
		_rooms.append(rec)
	_arrival_inlay()
	_parapet_details(t)
	root.set_meta(&"rooms", _rooms)
	root.set_meta(&"room_seed", hash(String(def.id) + "/rooms"))
	root.set_meta(&"room_keep", keep.keys().map(func(c): return [c.x, c.y]))

## One motif against a wall of cell c (or into its corner). False when the cell cannot take it.
func _place_motif(motif: String, c: Vector2i) -> bool:
	var m: Dictionary = DataDungeonRoles.M.get(motif, {})
	if m.is_empty():
		return false
	var sides := _wall_sides(c)
	var corner: bool = m.get("corner", false)
	var p0 := cell_pos(c)
	var origin: Vector3
	var ax: Vector3            # local x (along the wall / out from the side wall)
	var az: Vector3            # local z (out from the wall into the room)
	if corner:
		if not sides.has("north") or not (sides.has("west") or sides.has("east")):
			return false
		var side := "west" if sides.has("west") else "east"
		var dn := Vector3(0, 0, -1)
		var ds := Vector3(float(SIDES[side].x), 0, 0)
		origin = p0 + dn * 1.85 + ds * 1.85
		ax = -ds
		az = -dn
	else:
		var sd: String = sides[0] if sides[0] == "north" or sides.size() == 1 else sides[_room_rng.randi() % sides.size()]
		var d := Vector3(float(SIDES[sd].x), 0, float(SIDES[sd].y))
		origin = p0 + d * 1.85
		az = -d
		ax = Vector3.UP.cross(az)
	var face_yaw := rad_to_deg(atan2(az.x, az.z))
	for pc: Array in m.pieces:
		var nm: String = pc[0]
		var off: Vector3 = pc[1]
		var pos: Vector3 = origin + ax * off.x + az * off.z + Vector3(0, off.y, 0)
		var kind: String = pc[4]
		if nm == "@fire" or nm == "@glow":
			if Perf.lite or _role_lights >= ROLE_LIGHTS:
				continue
			_role_lights += 1
			if nm == "@fire":
				flame(pos, float(pc[3]))
				light(pos + Vector3(0, 0.5, 0), FIRE, 2.0, 7.0, false, true)
			else:
				light(pos, th.torch, 1.1, 5.5, false, false)
			continue
		if kind == "o" and Perf.lite:
			continue
		if not _has(nm):
			continue
		var n := kit(nm, pos, face_yaw + float(pc[2]), float(pc[3]), props if kind == "k" else deco)
		if kind != "k":
			for col in n.find_children("*", "CollisionObject3D", true, false):
				col.free()
		if pc.size() > 5:
			n.rotation.z = deg_to_rad(float(pc[5]))
	return true

## The arena keeps its middle empty: the theme's one silhouette in the two dressable cells farthest from the boss.
func _boss_silhouettes(reg: Array, t: Dictionary, rec: Dictionary) -> void:
	if not fd.has("boss"):
		return
	var bc: Vector2i = fd.boss
	var far: Array = reg.filter(func(c): return not _used.has(c) and not _wall_sides(c).is_empty() and not is_stair(c) \\
		and absi(c.x - bc.x) + absi(c.y - bc.y) >= 3)
	far.sort_custom(func(x, y): return (x - bc).length_squared() > (y - bc).length_squared())
	var placed: Array = []
	for c: Vector2i in far:
		if placed.size() >= 2:
			break
		if placed.any(func(q): return absi(q.x - c.x) + absi(q.y - c.y) < 3):
			continue
		var sides := _wall_sides(c)
		var p := cell_pos(c)
		var off := Vector3.ZERO
		for sd in sides:
			off += Vector3(float(SIDES[sd].x), 0, float(SIDES[sd].y)) * 1.0
		var nm: String = t.boss[0]
		if not _has(nm):
			return
		kit(nm, p + off, _room_rng.randf() * 360.0, float(t.boss[1]), props)
		_used[c] = true
		placed.append(c)
		rec.groups.append({"motif": "boss:" + nm, "cell": [c.x, c.y]})

## A threshold inlay on the arrival spawn's cell: the first thing under the hero's feet says where they are.
func _arrival_inlay() -> void:
	var arr: Vector2i = fd.arrival
	var p := cell_pos(arr)
	for d in [Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1)]:
		var nb: Vector2i = arr + d
		if height.has(nb) and absf(float(height[nb]) - p.y) < 0.1 and not is_bridge(nb):
			var q := cell_pos(nb)
			kit("kd_floor_inlay", Vector3(q.x, q.y + 0.012, q.z), 0.0, 0.85, deco)
			return

## Small single pieces along basin and gallery parapets (every other edge cell, at most six a floor), never colliding.
func _parapet_details(t: Dictionary) -> void:
	var n := 0
	var cells: Array = height.keys()
	cells.sort()
	var edge_list: Array = t.get("edge", [])
	if edge_list.is_empty():
		return
	for c: Vector2i in cells:
		if n >= 6 or _used.has(c) or is_bridge(c) or is_stair(c) or (c.x + c.y) % 2 == 1:
			continue
		for sd in ["south", "west", "east", "north"]:
			var nb: Vector2i = c + SIDES[sd]
			if not is_basin(nb):
				continue
			var d := Vector3(float(SIDES[sd].x), 0, float(SIDES[sd].y))
			var along := Vector3.UP.cross(d) * _room_rng.randf_range(-1.2, 1.2)
			var nm: String = edge_list[_room_rng.randi() % edge_list.size()]
			if _has(nm):
				var e := kit(nm, cell_pos(c) + d * 1.45 + along, _room_rng.randf() * 360.0, 1.0, deco)
				for col in e.find_children("*", "CollisionObject3D", true, false):
					col.free()
				n += 1
			break
'''
open(p, 'w', encoding='utf-8').write(s)
print("ok")
