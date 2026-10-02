def add(path, call_after, body):
    s = open(path, encoding='utf-8').read()
    assert call_after in s, (path, call_after)
    s = s.replace(call_after, call_after.rstrip('\n') + '\n\t_map_design()\n', 1)
    s += body
    open(path, 'w', encoding='utf-8').write(s)


add('game/src/world/maps/catacombs.gd', '\t_cistern()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): each room's own function, sharper — a holding cell at the back of the guard hall, urn
# niches in the burial hall, a bunk in the barracks, cargo and fuel in the storeroom, old coffins and a broken marker
# in the ossuary, offerings left on the ritual altar, and in the cistern amber lanterns on the ledges against the teal
# water, moss down its wet walls, timber drifting in the pool. The ritual flag, chests, camps and every door stay clear.

func _on(n: Node3D, nm: String, piece: String, off: Vector3, yaw := 0.0, scale := 1.0) -> Node3D:
	if n == null:
		return null
	var top := MapBuilder._local_box(nm, n).end.y * n.scale.y
	return kit(piece, n.position + Vector3(off.x, top + off.y, off.z), yaw, scale, deco)

func _map_design() -> void:
	kit("kd_floor_inlay", Vector3(0, 0.012, 19.4), 0.0, 0.9, deco)
	# guard hall: the cell where the watch held what it caught; a lantern on the duty table
	kit("kd_bars_gate", Vector3(-1.0, 0, -4.0 + 0.15 + 0.5), 0.0, 0.75, props)
	kit("kd_lantern_candle", Vector3(-6.5, 0.92, 3.0), 0.0, 1.0, deco)
	# burial hall: urns in niches along the side walls (clear of the aisle and the torches)
	for c in [[Vector3(-9.4, 0, -12.0), 90.0], [Vector3(9.4, 0, -20.0), -90.0]]:
		var p: Vector3 = c[0]
		var ax := Vector3(0, 0, 1)
		kit("kd_urn_round", p - ax * 0.7, c[1], 1.0, props)
		kit("kd_urn_square", p, c[1], 1.0, props)
		kit("kd_urn_round", p + ax * 0.65, c[1] + 30.0, 0.8, props)
		kit("kd_candles", p + Vector3(0.5 if c[1] > 0.0 else -0.5, 0, 0.0), 0.0, 0.7, deco)
	# barracks: one more sleeper's bunk against the north wall, between the beds and the table
	kit("kd_bed_bunk", Vector3(-29.0, 0, -8.0 + 0.15 + 0.58), 90.0, 1.0, props)
	# storage: bottles in their crate, fuel stacked, a shovel left against the wall
	kit("kd_crate_bottles", Vector3(-28.6, 0, -23.25), 0.0, 1.0, props)
	kit("kd_log_stack", Vector3(-33.25, 0, -18.4), 90.0, 0.9, props)
	kit("kd_shovel", Vector3(-22.55, 0, -19.2), -90.0, 1.0, deco)
	# ossuary: an old coffin on the west wall, an urn niche on the north
	kit("kd_coffin_old", Vector3(-28.95, 0, -26.0), 90.0, 1.0, props)
	kit("kd_urn_square", Vector3(-25.0, 0, -35.1), 0.0, 1.0, props)
	kit("kd_urn_round", Vector3(-24.3, 0, -35.15), 20.0, 0.85, props)
	kit("kd_grave_broken", Vector3(-15.6, 0, -29.6), -80.0, 0.9, props)
	# ritual chamber: what the cult left on the altar
	var alt: Node3D = props.find_child("altar_*", false, false)
	_on(alt, "altar", "kd_offering_bowl", Vector3(-0.45, 0, 0.05))
	_on(alt, "altar", "kd_chalice", Vector3(0.4, 0, 0.0))
	# the cistern: amber lanterns on the ledges, moss down the pool walls, timber drifting
	for p in [Vector3(25.2, 0, -2.0), Vector3(39.0, 0, -15.6), Vector3(39.2, 0, 4.0)]:
		kit("kd_lantern_candle", p, 0.0, 1.0, deco)
	for x in [28.6, 33.0, 35.6]:
		kit("kd_hanging_moss", Vector3(x, WATER_Y + 0.6, POOL.position.y + 0.12), 0.0, 1.4, deco)
	for c in [[Vector3(33.0, WATER_Y - 0.06, 2.4), 40.0], [Vector3(30.0, WATER_Y - 0.06, -12.6), 110.0]]:
		kit("kd_debris_wood", c[0], c[1], 1.1, deco)
	kit("kd_planks", Vector3(23.0, -0.38, -16.0), 90.0, 0.6, deco)
''')

add('game/src/world/maps/forgotten_temple.gd', '\t_surroundings()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the four parts read apart — the colonnade's fallen drum and masonry, the library's
# books spilled from a toppled case, the flooded chapel's drift and a half-sunk urn, the sanctum's offerings on the
# altar of the first oath and a threshold before it. The seal altar, the throne gate and the nave's aisle stay clear.

func _map_design() -> void:
	# colonnade: a fallen column drum along the west aisle, masonry by the broken pillar
	var col := kit("kd_column", Vector3(-7.6, 0.45, -5.0), 0.0, 0.85, deco)
	col.rotation = Vector3(deg_to_rad(84.0), deg_to_rad(6.0), 0.0)
	kit("kd_debris_stone", Vector3(6.9, 0, -5.8), 30.0, 1.1, deco)
	# library: a toppled case and its books across the floor by the fallen wall
	var case := kit("kd_bookcase_open", Vector3(19.0, 0.28, -12.6), 0.0, 1.0, deco)
	case.rotation = Vector3(deg_to_rad(-84.0), deg_to_rad(20.0), 0.0)
	for c in [[Vector3(17.2, 0, -11.2), 30.0], [Vector3(13.4, 0, -10.2), 110.0], [Vector3(18.6, 0, -15.4), 250.0]]:
		kit("kd_books", c[0], c[1], 1.1, deco)
	# flooded chapel: timber drifting, an urn half sunk, moss at the waterline
	kit("kd_debris_wood", Vector3(-13.4, 0.1, -3.4), 50.0, 1.0, deco)
	kit("kd_urn_round", Vector3(-12.6, -0.25, -10.6), 20.0, 0.9, deco).rotation.z = deg_to_rad(18.0)
	kit("kd_hanging_moss", Vector3(-17.5, 1.2, WEST_CHAPEL.position.y + 0.15), 0.0, 1.2, deco)
	# sanctum: offerings on the altar of the first oath, a threshold where the oath was taken
	var alt: Node3D = props.find_child("altar_*", false, false)
	if alt:
		var top := MapBuilder._local_box("altar", alt).end.y
		kit("kd_offering_bowl", alt.position + Vector3(-0.5, top, 0.05), 0.0, 1.0, deco)
		kit("kd_chalice", alt.position + Vector3(0.45, top, 0.0), 0.0, 1.0, deco)
	kit("kd_floor_inlay", Vector3(0, SY + 0.012, -29.4), 0.0, 0.9, deco)
''')

add('game/src/world/maps/boss_arena.gd', '\t_abyss()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the approach stays quiet — a threshold under the arrival and two pieces of fallen
# masonry at the ledge's far corners. Nothing enters the ring, the charge lanes or the space round the eight pillars.

func _map_design() -> void:
	kit("kd_floor_inlay", Vector3(0, 0.012, 32.0), 0.0, 0.8, deco)
	for c in [[Vector3(-6.6, 0, 38.8), 20.0], [Vector3(6.7, 0, 30.9), 200.0]]:
		kit("kd_debris_stone", c[0], c[1], 1.0, deco)
''')
print("ok")
