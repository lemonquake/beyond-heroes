import re

# --- dungeon: protect only marker cells, the spawn cells beside them and stair/bridge neighbours; more groups per room
p = 'game/src/world/maps/dungeon.gd'
s = open(p, encoding='utf-8').read()
old = '''## A cell next to something that must stay open (a marker cell, stairs, a bridge, a basin edge's stair head).
func _protected(c: Vector2i, keep: Dictionary) -> bool:
	for dx in [-1, 0, 1]:
		for dz in [-1, 0, 1]:
			var q := c + Vector2i(dx, dz)
			if keep.has(q) or is_stair(q) or is_bridge(q):
				return true
	return false'''
new = '''## A cell that must stay open: a marker cell (portal, seal, boss, camp, chest), the spawn cell beside a portal, or a
## cell next to stairs or a bridge (their approaches). A motif in a marker's other neighbours stands against that cell's
## far wall, 2 m or more from anything on the marker cell.
func _protected(c: Vector2i, keep: Dictionary, spawns: Dictionary) -> bool:
	if keep.has(c) or spawns.has(c):
		return true
	for dx in [-1, 0, 1]:
		for dz in [-1, 0, 1]:
			var q := c + Vector2i(dx, dz)
			if is_stair(q) or is_bridge(q):
				return true
	return false

## The cell a portal's spawn stands on (MapBuilder spawns sit 3 m into the neighbour _beside() picks).
func _spawn_cell(c: Vector2i) -> Vector2i:
	var p := cell_pos(c)
	for d in [Vector2i(0, 1), Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1)]:
		var nb: Vector2i = c + d
		if height.has(nb) and absf(float(height[nb]) - p.y) < 0.1 and not is_bridge(nb):
			return nb
	return c'''
assert old in s
s = s.replace(old, new)
old = '''	var deep := floor_n >= 3 or floor_n > DataDungeons.floor_count(dungeon)'''
new = '''	var spawns := {}
	for k in ["arrival", "descent", "exit"]:
		if fd.has(k):
			spawns[_spawn_cell(fd[k])] = true
	var deep := floor_n >= 3 or floor_n > DataDungeons.floor_count(dungeon)'''
assert old in s
s = s.replace(old, new)
s = s.replace('''				if _used.has(c) or _protected(c, keep) or _wall_sides(c).is_empty():''',
              '''				if _used.has(c) or _protected(c, keep, spawns) or _wall_sides(c).is_empty():''')
old = '''			var want := 1 if role in ["arrival", "seal", "traversal"] else clampi(reg.size() / 6, 1, 2)'''
new = '''			var want := clampi(reg.size() / 4, 1, 2) if role in ["arrival", "seal", "traversal"] else clampi(reg.size() / 3, 1, 3)'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)

# the test: motifs keep off marker cells and stair/bridge approaches (not every marker neighbour)
p = 'game/tests/unit/test_map_design.gd'
s = open(p, encoding='utf-8').read()
old = '''				var c := Vector2i(g.cell[0], g.cell[1])
				for dx in [-1, 0, 1]:
					for dz in [-1, 0, 1]:
						ok(not keep.has(c + Vector2i(dx, dz)) or String(g.motif).begins_with("boss:"),
							"%s: %s at %s stays off markers and their neighbours" % [mid, g.motif, c])'''
new = '''				var c := Vector2i(g.cell[0], g.cell[1])
				ok(not keep.has(c), "%s: %s at %s stays off marker cells" % [mid, g.motif, c])'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)

# --- bushes: the 8-triangle small bush reads as a flat star from the gameplay camera; use the kit's own bush there
p = 'game/src/data/data_vignettes.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('"kd_bush_small"', '"bush_a"')
open(p, 'w', encoding='utf-8').write(s)
for p in ['game/src/world/maps/sanctuary.gd']:
    s = open(p, encoding='utf-8').read()
    s = s.replace('decor("kd_bush_small", Vector3(sx * 1.6 + 0.3, TERRACE_Y + 0.35, -18.7), 30.0, 0.6, false)',
                  'decor("bush_a", Vector3(sx * 1.6 + 0.3, TERRACE_Y + 0.35, -18.7), 30.0, 0.45, false)')
    open(p, 'w', encoding='utf-8').write(s)

# --- produce: less saturated
p = 'game/src/world/material_library.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('"BH_Produce": ["", Color(0.74, 0.4, 0.14), 0.7,', '"BH_Produce": ["", Color(0.58, 0.36, 0.17), 0.8,')
open(p, 'w', encoding='utf-8').write(s)

# --- capture: skip any cutscene a map load starts
p = 'game/tests/tools/capture_map_design.gd'
s = open(p, encoding='utf-8').read()
old = '''	if Game.current_map_id != mid:
		Game.load_map(mid, &"start")
		await _wait(2.0)'''
new = '''	if Game.current_map_id != mid:
		Game.load_map(mid, &"start")
		await _wait(2.0)
	for k in 20:
		if not CutscenePlayer.is_playing():
			break
		CutscenePlayer.active.skip_all()
		await _wait(0.5)'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
