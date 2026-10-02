p = 'game/src/world/maps/interior.gd'
s = open(p, encoding='utf-8').read()

# tavern: the second round table gets chairs that face it (a different eating group from the stools)
old = '''	for t in [Vector3(-1.2, 0, 2.6), Vector3(4.0, 0, 1.4)]:
		rounds.append(item("table_round", t))
		for k in 3:
			var a := TAU * k / 3.0 + 0.4
			item("stool", t + Vector3(cos(a), 0, sin(a)) * 0.95, rad_to_deg(a))'''
new = '''	for t in [Vector3(-1.2, 0, 2.6), Vector3(4.0, 0, 1.4)]:
		rounds.append(item("table_round", t))
		for k in 3:
			var a := TAU * k / 3.0 + 0.4
			var at: Vector3 = t + Vector3(cos(a), 0, sin(a)) * (0.95 if t.x < 0.0 else 1.05)
			if t.x < 0.0:
				item("stool", at, rad_to_deg(a))
			else:
				# map-design pass: this table's party sits on chairs turned to face it (kd_chair, front +Z)
				item("kd_chair", at, rad_to_deg(atan2(t.x - at.x, t.z - at.z)))'''
assert old in s
s = s.replace(old, new)

s = s.replace('''			push_error("interior.gd has no room for %s" % def.id)
			_room(8.0, 8.0, PLASTER, 0, {})''', '''			push_error("interior.gd has no room for %s" % def.id)
			_room(8.0, 8.0, PLASTER, 0, {})
	_map_design()''')

s += '''
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
'''
open(p, 'w', encoding='utf-8').write(s)
print("ok")
