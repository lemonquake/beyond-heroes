p = 'game/src/data/data_vignettes.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''	"wreck": {''', '''	"jade_threshold": {"r": 3.0, "pieces": [
		["kd_urn_square", Vector3(-1.6, 0, 0.2), 0.0, 1.0, "k"],
		["kd_urn_round", Vector3(-1.0, 0, 1.1), 30.0, 0.9, "k"],
		["kd_urn_square", Vector3(1.7, 0, 0.0), 12.0, 1.0, "k"],
		["kd_offering_bowl", Vector3(1.0, 0, 0.9), 0.0, 1.0, "d"],
		["kd_ground_leaves", Vector3(2.3, 0, 1.3), 0.0, 1.2, "b"],
		["kd_ground_leaves", Vector3(-2.4, 0, 1.0), 70.0, 1.0, "b"],
		["kd_mushrooms_pale", Vector3(-2.0, 0, -0.6), 0.0, 1.0, "b"],
		["kd_rock_flat", Vector3(0.3, 0, 1.8), 20.0, 1.0, "b"]]},
	"excavation": {"r": 3.0, "pieces": [
		["kd_debris_stone", Vector3(0, 0, 0), 0.0, 1.4, "d"],
		["kd_debris_stone", Vector3(1.8, 0, 1.2), 90.0, 1.0, "d"],
		["kd_shovel", Vector3(-1.2, 0, 0.8), 20.0, 1.0, "o"],
		["kd_crate", Vector3(-1.9, 0, -0.6), 8.0, 0.9, "k"],
		["kd_planks", Vector3(0.6, 0.0, -1.8), 70.0, 0.7, "d"]]},
	"wreck": {''')
open(p, 'w', encoding='utf-8').write(s)


def add(path, call_after, body):
    s = open(path, encoding='utf-8').read()
    assert call_after in s, (path, call_after)
    s = s.replace(call_after, call_after.rstrip('\n') + '\n\t_map_design()\n', 1)
    s += body
    open(path, 'w', encoding='utf-8').write(s)


add('game/src/world/maps/zr_coilwood.gd', '\t_greenery()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the jungle's groups and transitions — moss and rock where the ground breaks, fallen
# trunks under the canopy, the aqueduct's fallen stones beside the road it once crossed, an offering at the shrine's
# foot and a threshold of memorial urns before the Jade Sepulchre. The shrine and relay pylons stay clear of the trail
# view; nothing glows (all relay light stays the island's white).

func _clear_here(x: float, z: float, r: float) -> bool:
	return not _blocked(x, z, r + 3.0, r + 2.0) and not _in_field(x, z, r)

func _map_design() -> void:
	clear_fn = _clear_here
	var sh := Vector3(SHRINE.x, 0, SHRINE.y)
	place_near("offering", sh + Vector3(4.5, 0, 6.0), sh, 5.0, 9.0, 0.0)
	var jade: Vector2 = DataDungeons.get_def(&"jade_sepulchre").surface.pos
	place_near("jade_threshold", Vector3(jade.x - 2.0, 0, jade.y + 7.0), Vector3(jade.x, 0, jade.y), 5.0, 10.0, 200.0)
	# the aqueduct's fallen spans: stones and a toppled column on the verges either side of the gap the road uses
	for c in [[Vector3(AQ_X - 5.5, 0, 9.0), 0.0], [Vector3(AQ_X + 5.8, 0, 19.0), 120.0], [Vector3(AQ_X - 5.0, 0, -20.0), 60.0]]:
		kit("kd_debris_stone", c[0], c[1], 1.5, deco, true)
	var col := kit("kd_column", Vector3(AQ_X + 6.5, 0.5, 12.0), 15.0, 0.9, deco, true)
	col.rotation = Vector3(0, deg_to_rad(15.0), deg_to_rad(84.0))
	for q in [Vector3(-40.0, 0, 30.0), Vector3(40.0, 0, -6.0), Vector3(-20.0, 0, -60.0)]:
		place_near("fallen_tree", q, q, 0.0, 12.0, rng.randf() * 360.0)
	for q in [Vector3(-70.0, 0, 34.0), Vector3(10.0, 0, 24.0), Vector3(60.0, 0, 30.0), Vector3(-30.0, 0, -30.0)]:
		place_near("rock_cluster_m", q, q, 0.0, 12.0, rng.randf() * 360.0)
	for q in [Vector3(-60.0, 0, 10.0), Vector3(30.0, 0, 10.0)]:
		place_near("palm_group", q, q, 0.0, 14.0, rng.randf() * 360.0)
''')

add('game/src/world/maps/zr_barrens.gd', '\t_scrub()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): scraps of salvage and labour where people work — round the survivors' camp, at the
# fallen colossus being picked over, and at the two Vault mouths, which differ: the Obsidian Engine keeps a service
# entrance (a fire basket, stacked stores), the Veinworks an abandoned extraction (spoil, tipped barrels, a shovel).
# Bare shattered rock (no moss, no grass): the barrens stay barren.

func _clear_here(x: float, z: float, r: float) -> bool:
	var p := Vector2(x, z)
	for c in CAMPS:
		if p.distance_to(c[1]) < float(c[2]) + r + 3.0:
			return false
	return not _near_route(x, z, r + 3.0, r + 2.0) and is_clear(x, z, r * 0.5)

func _map_design() -> void:
	clear_fn = _clear_here
	var camp := Vector3(-40.0, 0, 30.0)
	for c in [["salvage", Vector3(-58.0, 0, 30.0)], ["tool_corner", Vector3(-40.0, 0, 50.0)], ["supply_corner", Vector3(-24.0, 0, 42.0)]]:
		place_near(c[0], c[1], camp, 15.0, 24.0, rng.randf() * 360.0, {"check": false})
	place_near("excavation", COLOSSUS + Vector3(-12.0, 0, 10.0), COLOSSUS, 10.0, 20.0, 30.0)
	place_near("salvage", COLOSSUS + Vector3(14.0, 0, 6.0), COLOSSUS, 10.0, 20.0, -40.0)
	var ob: Vector2 = DataDungeons.get_def(&"obsidian_engine").surface.pos
	var basket := Vector3(ob.x + 6.5, 0, ob.y + 7.0)
	if not touches_solid(Vector3(basket.x, height_at(basket.x, basket.z), basket.z), 1.0):
		kit("kd_fire_basket", basket, 0.0, 1.0, props, true)
		flame(Vector3(basket.x, height_at(basket.x, basket.z) + 0.45, basket.z), 0.9)
		light(Vector3(basket.x, height_at(basket.x, basket.z) + 1.4, basket.z), FIRE, 2.0, 8.0, false, true)
	place_near("cargo_stack", Vector3(ob.x - 7.0, 0, ob.y + 7.0), Vector3(ob.x, 0, ob.y), 6.0, 12.0, 160.0)
	var vn: Vector2 = DataDungeons.get_def(&"veinworks").surface.pos
	place_near("excavation", Vector3(vn.x - 7.0, 0, vn.y - 5.0), Vector3(vn.x, 0, vn.y), 6.0, 12.0, 250.0)
	for c in [Vector3(vn.x - 5.0, 0, vn.y + 6.5), Vector3(vn.x + 6.0, 0, vn.y - 7.0)]:
		if not touches_solid(Vector3(c.x, height_at(c.x, c.z), c.z), 0.8):
			kit("kd_barrel", c + Vector3(0, 0.45, 0), rng.randf() * 360.0, 0.9, deco, true).rotation.z = deg_to_rad(84.0)
	for q in [[Vector3(-80.0, 0, 20.0), "kd_shore_rocks_a"], [Vector3(-10.0, 0, 30.0), "kd_shore_rocks_c"], [Vector3(30.0, 0, -10.0), "kd_shore_rocks_b"],
			[Vector3(-60.0, 0, -40.0), "kd_shore_rocks_c"], [Vector3(60.0, 0, 20.0), "kd_shore_rocks_a"]]:
		var p: Vector3 = q[0]
		if _clear_here(p.x, p.z, 3.5) and not touches_solid(Vector3(p.x, height_at(p.x, p.z), p.z), 3.0):
			kit(q[1], p - Vector3(0, 0.4, 0), rng.randf() * 360.0, rng.randf_range(0.8, 1.1), props, true)
''')

add('game/src/world/maps/bridge_of_death.gd', '\t_ledge_dressing()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the span's history on its safe margins — a few repaired plank patches let into the deck
# beside the parapets (flat, walkable, never across the lanes or under a ward pylon) and fallen masonry on the ledges.
# One silhouette, few unique pieces: no repeated railing props.

func _map_design() -> void:
	for k in [3, 9, 16, 24]:
		var z := SPAN_Z0 - SEG * (k + 0.5)
		var sx := -1.0 if k % 2 == 0 else 1.0
		kit("kd_planks", Vector3(sx * 4.0, -0.4, z + 1.0), 90.0 + k * 7.0, 0.9, deco)
	for c in [[Vector3(-8.5, GROUND_Y, SOUTH_GATE_Z + 7.0), 20.0], [Vector3(8.8, GROUND_Y, SOUTH_GATE_Z + 9.5), 160.0],
			[Vector3(-8.2, GROUND_Y, NORTH_GATE_Z - 8.0), 80.0], [Vector3(8.6, GROUND_Y, NORTH_GATE_Z - 11.0), 250.0]]:
		kit("kd_debris_stone", c[0], c[1], 1.4, deco)
''')

add('game/src/world/maps/zr_citadel.gd', '\t_camps()\n', '''
# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): a siege camp that keeps stores and works on its gear before the gate; broken storage and
# fallen masonry along the civic avenue's sides; green reclaiming the side courts against the walls. The avenue's
# middle, the stairs, the arena round the Dawn Engine and every camp ring stay clear.

func _clear_here(x: float, z: float, r: float) -> bool:
	var p := Vector2(x, z)
	for c in CAMPS:
		if p.distance_to(Vector2(c[1], c[2])) < r + 7.0:
			return false
	if absf(x) < r + 6.0 or p.distance_to(ARENA) < DataZarael.HC_ARENA_R + r + 3.0:
		return false
	if absf(z - 30.0) < r + 6.0 or absf(z) < r + 6.0:
		return false              # the retaining rows and their stairs
	return road_dist(x, z) > r + 2.0 and is_clear(x, z, r * 0.5) and absf(x) < X_WALL - 3.0 - r

func _map_design() -> void:
	clear_fn = _clear_here
	# the siege camp before the gate (on the approach ridge)
	for c in [["supply_corner", Vector3(-27.0, 0, 70.0)], ["cargo_stack", Vector3(27.0, 0, 69.0)], ["tool_corner", Vector3(-10.0, 0, 76.0)]]:
		place_near(c[0], c[1], c[1], 0.0, 7.0, rng.randf() * 360.0)
	# the damaged avenue: fallen masonry and broken stores along its sides, the middle kept clear
	for c in [Vector3(-11.0, 0, 44.0), Vector3(12.0, 0, 40.0), Vector3(-12.0, 0, 14.0), Vector3(11.5, 0, 18.0)]:
		place_near("salvage" if c.z > 30.0 else "excavation", c, c, 0.0, 5.0, rng.randf() * 360.0)
	# green reclaiming the side courts
	for c in [Vector3(-52.0, 0, 22.0), Vector3(53.0, 0, 24.0), Vector3(-53.0, 0, -36.0), Vector3(52.0, 0, -32.0), Vector3(-30.0, 0, 48.0)]:
		place_near("flower_border" if c.z > 0.0 else "fallen_tree", c, c, 0.0, 6.0, rng.randf() * 360.0)
	for c in [Vector3(-50.0, 0, 50.0), Vector3(50.0, 0, 8.0)]:
		place_near("palm_pair", c, c, 0.0, 6.0, rng.randf() * 360.0)
''')
print("ok")
