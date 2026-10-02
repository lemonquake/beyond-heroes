p = 'game/src/data/data_vignettes.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''		["kd_shovel", Vector3(2.1, 0, -1.4), 10.0, 1.0, "o"],
		["ph_wooden_bucket_02", Vector3(1.9, 0, 0.6), 0.0, 1.0, "o"]]},''', '''		["kd_shovel", Vector3(2.1, 0, -1.4), 10.0, 1.0, "o"],
		["ph_wooden_bucket_02", Vector3(1.9, 0, 0.6), 0.0, 1.0, "o"],
		["kd_tree_small", Vector3(-2.6, 0, -2.9), 0.0, 1.0, "k"]]},''')
s = s.replace('''	"palm_group": {"r": 3.8, "pieces": [
		["kd_palm", Vector3(0, 0, 0), 0.0, 1.0, "k"],''', '''	"palm_group": {"r": 3.8, "pieces": [
		["kd_palm_tall", Vector3(-2.2, 0, -2.4), 30.0, 1.0, "k"],
		["kd_palm", Vector3(0, 0, 0), 0.0, 1.0, "k"],''')
s = s.replace('''	"bench_view": {''', '''	"bamboo_garden": {"r": 2.2, "pieces": [
		["kd_bamboo", Vector3(-0.8, 0, -0.4), 0.0, 1.0, "k"],
		["kd_bamboo", Vector3(0.6, 0, -0.7), 70.0, 0.85, "k"],
		["kd_pot_small", Vector3(1.3, 0, 0.5), 0.0, 1.0, "d"],
		["kd_plant_leafy", Vector3(-0.2, 0, 0.8), 0.0, 1.0, "b"]]},
	"tea_corner": {"r": 1.8, "pieces": [
		["kd_table_round", Vector3(0, 0, 0), 0.0, 0.7, "k"],
		["kd_stool_square", Vector3(-0.95, 0, 0.1), 90.0, 0.9, "k"],
		["kd_stool_square", Vector3(0.9, 0, -0.2), -90.0, 0.9, "k"],
		["kd_bottle_large", Vector3(0.1, 0.58, 0.05), 0.0, 0.7, "o"]]},
	"bench_view": {''')
open(p, 'w', encoding='utf-8').write(s)

p = 'game/src/data/data_dungeon_roles.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''	"bunks": {''', '''	"war_table": {"pieces": [["kd_table_cross", Vector3(0.0, 0, 0.6), 0.0, 1.0, "k"], ["kd_stool_square", Vector3(-0.6, 0, 1.45), 0.0, 1.0, "k"],
		["kd_stool_square", Vector3(0.7, 0, 1.4), 20.0, 1.0, "k"], ["kd_candles", Vector3(0.3, 0.78, 0.5), 0.0, 0.6, "o"]]},
	"sleep_corner": {"pieces": [["kd_bed_single", Vector3(-0.3, 0, 0.6), 90.0, 1.0, "k"], ["kd_side_table", Vector3(1.4, 0, 0.3), 0.0, 0.7, "k"],
		["kd_candles", Vector3(1.4, 0.6, 0.3), 0.0, 0.5, "o"]]},
	"bunks": {''')
s = s.replace('''	&"cellars": {"work": ["storage", "stash"], "function": ["stash", "mess_bench", "service_corner"], "boss": ["kd_crate_bottles", 1.2]},''',
              '''	&"cellars": {"work": ["storage", "stash"], "function": ["stash", "mess_bench", "sleep_corner"], "boss": ["kd_crate_bottles", 1.2]},''')
s = s.replace('''"function": ["mess_bench", "bunks", "forge_station"],
		"seal": ["war_supply"]''', '''"function": ["war_table", "bunks", "forge_station"],
		"seal": ["war_supply"]''')
s = s.replace('''"function": ["thorn_seam", "c_dead_tree", "fungal_stump"],''', '''"function": ["thorn_seam", "c_dead_tree", "altar_wood"],''')
open(p, 'w', encoding='utf-8').write(s)

p = 'game/src/world/maps/sanctuary.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''	vignette("rock_cluster_l", Vector3(-41.0, 0, 20.0), 30.0, {"check": false})''', '''	vignette("rock_cluster_l", Vector3(-41.0, 0, 20.0), 30.0, {"check": false})
	# one focal tree in the open lot between the Guild House and Swordfin Hall
	for c in [Vector3(18.0, 0, -6.0), Vector3(16.0, 0, -9.0), Vector3(-36.0, 0, 10.0)]:
		if _clear_spot(c, 1.6) and not touches_solid(c, 1.6):
			kit("kd_tree_detailed", c, rng.randf() * 360.0, 0.95, props, true)
			break''')
open(p, 'w', encoding='utf-8').write(s)

p = 'game/src/world/maps/agdao.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''	_on_tier(3, "garden_bed", Vector2(-24.0, -40.0), 6.0, 0.0)''', '''	_on_tier(3, "garden_bed", Vector2(-24.0, -40.0), 6.0, 0.0)
	_on_tier(3, "bamboo_garden", Vector2(-36.0, -41.0), 8.0, 0.0)
	_on_tier(2, "bamboo_garden", Vector2(40.0, -18.0), 8.0, 0.0)
	_on_tier(1, "tea_corner", Vector2(-30.0, 9.0), 8.0, 0.0)''')
open(p, 'w', encoding='utf-8').write(s)

p = 'game/src/world/maps/olivar.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''	place_near("boat_landing", Vector3(-20.0, 0, -41.0), Vector3(-20.0, 0, -40.0), 0.0, 5.0, 10.0)''', '''	place_near("boat_landing", Vector3(-20.0, 0, -41.0), Vector3(-20.0, 0, -40.0), 0.0, 5.0, 10.0)
	# a small mooring stage in the west bay beside the canoe (visual: it stands in the water, off the walkways)
	kit("kd_dock_small", Vector3(-11.5, LAKE_Y - 0.55, -46.6), 0.0, 1.0, deco)''')
open(p, 'w', encoding='utf-8').write(s)

p = 'game/src/world/maps/interior.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''	# a meeting at the war table: two chairs on its south side, facing Commander Rhea across it''', '''	kit("kd_rug_long", Vector3(-3.2, 0.006, 0.7), 0.0, 1.0, deco)
	# a meeting at the war table: two chairs on its south side, facing Commander Rhea across it''')
open(p, 'w', encoding='utf-8').write(s)
print("ok")
