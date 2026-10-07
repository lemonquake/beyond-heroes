class_name DataDungeonRoles
## Map-design pass (2026-10-03): what each dungeon's rooms were for, by theme. The dungeon builder (maps/dungeon.gd,
## _dress_rooms) splits a floor into rooms (connected cells of one storey), gives each a role — arrival, work/storage,
## the theme's own function (burial, study, ritual, organic...), traversal (rooms on a basin or gallery edge), the seal
## chamber and the boss approach — and dresses a few of its wall cells with that role's motifs. The plans, storeys,
## basins, bridges, stairs, seals, chests, camps, bosses and portals are never touched; motifs stand in a 1.6 m band
## against a wall (or in a corner), so a 4 m cell always keeps 2.4 m of floor to walk through.
##
## Motif piece: [kit name, Vector3(along the wall, height, out from the wall face), yaw (0: front faces the room), scale,
## kind] — kind "k" collides (Props), "d" decoration, "o" optional detail (dropped on Low). Two pseudo-pieces ask for
## light: "@fire" a flame with a warm light (an actual fire: braziers, fire baskets), "@glow" a small warm pool with no
## flame. Both are capped per floor by the builder and give no light on Low. Corner motifs ("corner": true) are set
## from the corner point with x along one wall and z along the other.

const M := {
	# ---- storage and work ---------------------------------------------------------------------------------------
	"storage": {"pieces": [["kd_crate", Vector3(-0.9, 0, 0.55), 90.0, 1.0, "k"], ["kd_crate", Vector3(-0.85, 0.69, 0.55), 80.0, 0.9, "k"],
		["kd_barrel", Vector3(0.4, 0, 0.6), 0.0, 1.0, "k"], ["kd_bottle_large", Vector3(1.2, 0, 0.35), 0.0, 1.0, "o"]]},
	"storage_wet": {"pieces": [["kd_barrel", Vector3(-1.0, 0, 0.6), 0.0, 1.0, "k"], ["kd_crate", Vector3(0.3, 0, 0.55), 80.0, 1.0, "k"],
		["kd_debris_wood", Vector3(1.1, 0, 0.7), 30.0, 0.9, "d"], ["kd_hanging_moss", Vector3(0.6, 1.3, 0.05), 0.0, 1.0, "o"]]},
	"cargo_spill": {"pieces": [["kd_crate", Vector3(-1.1, 0, 0.6), 70.0, 1.0, "k"], ["kd_barrel", Vector3(0.2, 0.45, 0.7), 0.0, 0.9, "d", 84.0],
		["kd_debris_wood", Vector3(1.0, 0, 0.6), 110.0, 1.0, "d"]]},
	"tool_store": {"pieces": [["kd_crate", Vector3(-0.8, 0, 0.55), 90.0, 1.0, "k"], ["kd_shovel", Vector3(0.05, 0, 0.2), 10.0, 1.0, "o"],
		["kd_log_stack", Vector3(1.0, 0, 0.5), 0.0, 0.7, "k"]]},
	"forge_station": {"pieces": [["kd_fire_basket", Vector3(-0.9, 0, 0.65), 0.0, 1.0, "k"], ["@fire", Vector3(-0.9, 0.42, 0.65), 0.0, 0.8, "o"],
		["anvil", Vector3(0.5, 0, 0.6), 0.0, 1.0, "k"], ["kd_shovel", Vector3(1.3, 0, 0.2), -10.0, 1.0, "o"]]},
	"fuel_store": {"pieces": [["kd_log_stack", Vector3(-0.7, 0, 0.6), 0.0, 1.0, "k"], ["kd_crate", Vector3(0.9, 0, 0.55), 90.0, 0.9, "k"]]},
	"ore_haul": {"pieces": [["ore_cart", Vector3(-0.4, 0, 0.75), 0.0, 1.0, "k"], ["kd_debris_stone", Vector3(1.2, 0, 0.6), 40.0, 0.9, "d"],
		["kd_shovel", Vector3(-1.5, 0, 0.2), 15.0, 1.0, "o"]]},
	"mine_props": {"pieces": [["kd_log", Vector3(0.0, 0, 0.45), 90.0, 0.8, "k"], ["kd_planks", Vector3(0.2, 0.62, 0.45), 90.0, 0.5, "d"],
		["kd_debris_stone", Vector3(-1.1, 0, 1.0), 0.0, 0.8, "d"]]},
	"service_corner": {"pieces": [["kd_crate", Vector3(-1.0, 0, 0.55), 90.0, 1.0, "k"], ["kd_lantern_candle", Vector3(0.0, 0, 0.3), 0.0, 1.0, "d"],
		["kd_barrel", Vector3(0.9, 0, 0.6), 0.0, 0.95, "k"], ["@glow", Vector3(0.0, 1.0, 0.6), 0.0, 1.0, "o"]]},
	# ---- living ------------------------------------------------------------------------------------------------
	"mess_bench": {"pieces": [["kd_table", Vector3(0.0, 0, 0.6), 0.0, 1.0, "k"], ["kd_chair", Vector3(-0.5, 0, 1.45), 180.0, 1.0, "k"],
		["kd_bottle", Vector3(0.3, 0.74, 0.55), 0.0, 1.0, "o"], ["kd_candles", Vector3(-0.4, 0.74, 0.5), 0.0, 0.6, "o"]]},
	"war_table": {"pieces": [["kd_table_cross", Vector3(0.0, 0, 0.6), 0.0, 1.0, "k"], ["kd_stool_square", Vector3(-0.6, 0, 1.45), 0.0, 1.0, "k"],
		["kd_stool_square", Vector3(0.7, 0, 1.4), 20.0, 1.0, "k"], ["kd_candles", Vector3(0.3, 0.78, 0.5), 0.0, 0.6, "o"]]},
	"sleep_corner": {"pieces": [["kd_bed_single", Vector3(-0.3, 0, 0.6), 90.0, 1.0, "k"], ["kd_side_table", Vector3(1.4, 0, 0.3), 0.0, 0.7, "k"],
		["kd_candles", Vector3(1.4, 0.6, 0.3), 0.0, 0.5, "o"]]},
	"bunks": {"pieces": [["kd_bed_bunk", Vector3(-0.4, 0, 0.6), 90.0, 1.0, "k"], ["kd_crate", Vector3(1.3, 0, 0.55), 90.0, 0.8, "k"]]},
	"rough_shelter": {"pieces": [["bedroll", Vector3(-0.6, 0, 0.5), 0.0, 1.0, "d"], ["kd_debris_wood", Vector3(1.0, 0, 0.6), 60.0, 1.0, "d"],
		["kd_log", Vector3(0.3, 0, 1.25), 90.0, 0.6, "k"]]},
	"bone_midden": {"pieces": [["bones_scatter", Vector3(-0.3, 0, 0.9), 30.0, 0.8, "d"], ["skull_pile", Vector3(1.0, 0, 0.6), 0.0, 0.7, "d"],
		["kd_debris_wood", Vector3(-1.2, 0, 0.6), 20.0, 0.9, "d"]]},
	"stash": {"pieces": [["kd_chest", Vector3(-0.9, 0, 0.45), 0.0, 1.0, "k"], ["kd_crate_bottles", Vector3(0.3, 0, 0.6), 90.0, 0.9, "k"],
		["kd_crate", Vector3(1.3, 0, 0.55), 90.0, 0.8, "k"], ["kd_lantern_candle", Vector3(-0.2, 0, 0.25), 0.0, 1.0, "d"]]},
	"war_supply": {"pieces": [["weapon_rack", Vector3(-0.7, 0, 0.3), 0.0, 1.0, "k"], ["kd_crate", Vector3(0.8, 0, 0.55), 90.0, 1.0, "k"],
		["kd_barrel", Vector3(1.5, 0, 1.2), 0.0, 0.85, "k"]]},
	# ---- burial -------------------------------------------------------------------------------------------------
	"coffin_bay": {"pieces": [["kd_coffin", Vector3(-0.3, 0, 0.72), 90.0, 1.0, "k"], ["kd_candles", Vector3(1.25, 0, 0.35), 0.0, 1.0, "d"],
		["kd_urn_round", Vector3(-1.5, 0, 0.35), 0.0, 0.8, "k"]]},
	"coffin_old": {"pieces": [["kd_coffin_old", Vector3(-0.2, 0, 0.72), 90.0, 1.0, "k"], ["kd_urn_square", Vector3(1.3, 0, 0.35), 0.0, 0.85, "k"],
		["kd_debris_stone", Vector3(-1.3, 0, 0.9), 30.0, 0.6, "d"]]},
	"urn_niche": {"pieces": [["kd_urn_round", Vector3(-0.8, 0, 0.32), 0.0, 1.0, "k"], ["kd_urn_square", Vector3(0.0, 0, 0.32), 0.0, 1.0, "k"],
		["kd_urn_round", Vector3(0.75, 0, 0.32), 40.0, 0.8, "k"], ["kd_candles", Vector3(0.0, 0, 0.85), 0.0, 0.8, "d"]]},
	"memorial": {"pieces": [["kd_grave_broken", Vector3(-0.6, 0, 0.45), 0.0, 1.0, "k"], ["kd_urn_round", Vector3(0.7, 0, 0.32), 0.0, 0.9, "k"],
		["kd_candles", Vector3(0.1, 0, 0.9), 0.0, 0.8, "d"], ["kd_offering_bowl", Vector3(0.9, 0, 0.9), 0.0, 1.0, "o"]]},
	"sarcophagus_bay": {"pieces": [["sarcophagus", Vector3(0.0, 0, 0.7), 0.0, 1.0, "k"], ["kd_candles", Vector3(1.55, 0, 0.35), 0.0, 0.8, "d"]]},
	"frost_burial": {"pieces": [["frozen_coffin", Vector3(-0.2, 0, 0.6), 0.0, 1.0, "k"], ["kd_urn_round", Vector3(1.45, 0, 0.35), 0.0, 0.8, "k"],
		["snow_drift", Vector3(-1.0, 0, 1.1), 20.0, 0.5, "d"]]},
	# ---- ritual and offering ------------------------------------------------------------------------------------
	"altar": {"pieces": [["kd_altar_stone", Vector3(0.0, 0, 0.7), 0.0, 1.0, "k"], ["kd_candles", Vector3(-1.4, 0, 0.4), 0.0, 1.0, "d"],
		["kd_offering_bowl", Vector3(0.3, 0.98, 0.65), 0.0, 1.0, "o"], ["kd_chalice", Vector3(-0.35, 0.98, 0.7), 0.0, 1.0, "o"],
		["@glow", Vector3(-1.4, 0.8, 0.6), 0.0, 1.0, "o"]]},
	"altar_wood": {"pieces": [["kd_altar_wood", Vector3(0.0, 0, 0.7), 0.0, 1.0, "k"], ["kd_candles", Vector3(1.45, 0, 0.4), 0.0, 0.9, "d"]]},
	"altar_broken": {"pieces": [["kd_altar_stone", Vector3(-0.3, 0, 0.7), 8.0, 1.0, "k"], ["kd_debris_stone", Vector3(1.2, 0, 0.8), 70.0, 0.9, "d"],
		["kd_urn_round", Vector3(-1.6, 0, 0.35), 0.0, 0.8, "k"]]},
	"plinth": {"pieces": [["kd_dais", Vector3(0.0, -0.8, 0.8), 0.0, 0.5, "k"], ["kd_candles", Vector3(0.0, 0.33, 0.8), 0.0, 0.8, "d"],
		["kd_candles", Vector3(1.2, 0, 0.35), 0.0, 0.6, "o"]]},
	"offering_row": {"pieces": [["kd_offering_bowl", Vector3(-0.8, 0, 0.3), 0.0, 1.2, "d"], ["kd_urn_square", Vector3(0.0, 0, 0.32), 0.0, 0.9, "k"],
		["kd_offering_bowl", Vector3(0.8, 0, 0.3), 30.0, 1.2, "d"], ["kd_chalice", Vector3(0.4, 0, 0.75), 0.0, 1.0, "o"]]},
	"candle_niche": {"pieces": [["kd_candles", Vector3(-0.5, 0, 0.35), 0.0, 1.0, "d"], ["kd_candles", Vector3(0.45, 0, 0.3), 40.0, 0.8, "d"],
		["kd_lantern_candle", Vector3(1.2, 0, 0.3), 0.0, 1.0, "d"], ["@glow", Vector3(0.0, 0.7, 0.5), 0.0, 1.0, "o"]]},
	"knight_niche": {"pieces": [["statue_knight", Vector3(0.0, 0, 0.9), 0.0, 0.8, "k"], ["kd_candles", Vector3(-1.3, 0, 0.4), 0.0, 0.8, "d"],
		["kd_candles", Vector3(1.3, 0, 0.4), 0.0, 0.8, "d"]]},
	"cell_bars": {"pieces": [["kd_bars_gate", Vector3(0.0, 0, 0.62), 0.0, 1.0, "k"], ["bones_scatter", Vector3(0.6, 0, 1.0), 0.0, 0.5, "o"]]},
	# ---- study --------------------------------------------------------------------------------------------------
	"study_desk": {"pieces": [["kd_desk", Vector3(0.0, 0, 0.5), 0.0, 1.0, "k"], ["kd_books", Vector3(-0.4, 0.87, 0.45), 15.0, 1.0, "o"],
		["kd_chair_round", Vector3(0.1, 0, 1.35), 180.0, 1.0, "k"], ["kd_candles", Vector3(0.55, 0.87, 0.4), 0.0, 0.6, "o"],
		["@glow", Vector3(0.4, 1.2, 0.6), 0.0, 1.0, "o"]]},
	"archive": {"pieces": [["kd_bookcase_closed", Vector3(-1.0, 0, 0.3), 0.0, 1.0, "k"], ["kd_bookcase_open", Vector3(0.1, 0, 0.3), 0.0, 1.0, "k"],
		["kd_books", Vector3(1.1, 0, 0.4), 30.0, 1.2, "o"]]},
	"archive_wide": {"pieces": [["kd_bookcase_wide", Vector3(-0.4, 0, 0.3), 0.0, 1.0, "k"], ["kd_books", Vector3(1.1, 0, 0.45), 60.0, 1.2, "o"]]},
	"instrument_bench": {"pieces": [["brass_telescope", Vector3(-0.6, 0, 0.95), 20.0, 0.8, "k"], ["kd_books", Vector3(1.1, 0, 0.45), 0.0, 1.0, "o"],
		["kd_debris_stone", Vector3(1.2, 0, 1.1), 0.0, 0.6, "d"]]},
	"lectern_corner": {"pieces": [["lectern", Vector3(-0.6, 0, 0.45), 0.0, 1.0, "k"], ["kd_bookcase_open", Vector3(0.6, 0, 0.3), 0.0, 1.0, "k"]]},
	# ---- organic and natural ------------------------------------------------------------------------------------
	"fungal_log": {"pieces": [["kd_log", Vector3(0.0, 0, 0.55), 90.0, 0.85, "k"], ["kd_mushrooms_pale", Vector3(-0.8, 0, 1.15), 0.0, 1.0, "d"],
		["kd_mushrooms_pale", Vector3(0.6, 0.55, 0.5), 60.0, 0.7, "d"], ["mushroom_glow_cluster", Vector3(1.4, 0, 1.0), 0.0, 0.8, "d"]]},
	"fungal_stump": {"pieces": [["kd_stump_old", Vector3(-0.6, 0, 0.6), 0.0, 1.0, "k"], ["kd_mushrooms_pale", Vector3(0.4, 0, 0.6), 0.0, 1.0, "d"],
		["kd_hanging_moss", Vector3(-1.2, 1.3, 0.05), 0.0, 1.0, "o"], ["kd_ground_leaves", Vector3(1.2, 0, 0.9), 0.0, 1.0, "o"]]},
	"pod_cluster": {"pieces": [["spore_pod", Vector3(-0.6, 0, 0.85), 0.0, 0.8, "k"], ["spore_pod", Vector3(0.9, 0, 0.7), 60.0, 0.6, "k"],
		["kd_mushrooms_pale", Vector3(0.1, 0, 1.3), 0.0, 0.9, "d"]]},
	"wet_timber": {"pieces": [["kd_log", Vector3(0.2, 0, 0.5), 92.0, 0.8, "k"], ["kd_hanging_moss", Vector3(-0.9, 1.3, 0.05), 0.0, 1.0, "d"],
		["kd_grass_large", Vector3(1.4, 0, 0.9), 0.0, 1.0, "d"], ["kd_barrel", Vector3(-1.4, 0, 1.0), 0.0, 0.8, "o"]]},
	"thorn_seam": {"pieces": [["roots", Vector3(0.0, 0, 0.9), 0.0, 0.7, "d"], ["kd_stump_old", Vector3(-1.1, 0, 0.55), 0.0, 1.0, "k"],
		["kd_log", Vector3(0.7, 0, 0.5), 88.0, 0.6, "k"], ["kd_ground_leaves", Vector3(1.5, 0, 1.1), 0.0, 1.0, "o"]]},
	"sea_growth": {"pieces": [["coral_cluster", Vector3(-0.7, 0, 0.55), 0.0, 1.0, "d"], ["kelp_strands", Vector3(0.5, 0, 0.35), 0.0, 0.8, "d"],
		["kd_debris_wood", Vector3(1.2, 0, 0.9), 50.0, 0.9, "d"]]},
	"wreck_rib": {"pieces": [["kd_rowboat", Vector3(0.0, 0.2, 1.0), 4.0, 0.62, "k"], ["kd_paddle", Vector3(1.5, 0, 0.2), 10.0, 1.0, "o"]]},
	"crystal_shelf": {"pieces": [["ice_crystal_small", Vector3(-0.8, 0, 0.4), 0.0, 1.0, "d"], ["ice_crystal_small", Vector3(0.1, 0, 0.35), 50.0, 0.7, "d"],
		["kd_debris_stone", Vector3(0.9, 0, 0.7), 0.0, 0.8, "d"]]},
	"expedition": {"pieces": [["bedroll", Vector3(-0.7, 0, 0.5), 0.0, 0.9, "d"], ["kd_crate", Vector3(0.9, 0, 0.55), 90.0, 0.85, "k"],
		["kd_lantern_candle", Vector3(1.6, 0, 0.3), 0.0, 1.0, "d"], ["kd_shovel", Vector3(0.2, 0, 0.2), 10.0, 1.0, "o"]]},
	"rubble_fall": {"pieces": [["kd_debris_stone", Vector3(-0.6, 0, 0.7), 0.0, 1.2, "d"], ["kd_debris_stone", Vector3(0.9, 0, 0.6), 120.0, 0.9, "d"],
		["kd_column", Vector3(0.0, 0.48, 1.0), 0.0, 0.85, "d", 84.0]]},
	"timber_fall": {"pieces": [["kd_debris_wood", Vector3(-0.6, 0, 0.65), 0.0, 1.2, "d"], ["kd_log", Vector3(0.6, 0, 0.5), 80.0, 0.6, "d"],
		["kd_planks", Vector3(1.0, 0.05, 1.1), 30.0, 0.5, "o"]]},
	"column_pair": {"pieces": [["kd_column", Vector3(-1.1, 0, 0.55), 0.0, 0.9, "k"], ["kd_column", Vector3(1.1, 0, 0.55), 0.0, 0.9, "k"]]},
	"obelisk_pair": {"pieces": [["kd_obelisk", Vector3(-1.1, 0, 0.55), 0.0, 1.0, "k"], ["kd_obelisk", Vector3(1.1, 0, 0.55), 0.0, 1.0, "k"]]},
	"display": {"pieces": [["armor_stand", Vector3(-1.0, 0, 0.45), 0.0, 1.0, "k"], ["kd_table_cloth", Vector3(0.6, 0, 0.6), 0.0, 0.8, "k"],
		["kd_chalice", Vector3(0.4, 0.6, 0.55), 0.0, 1.0, "o"], ["kd_chest", Vector3(1.5, 0, 1.3), -30.0, 0.8, "o"]]},
	"vault_store": {"pieces": [["kd_chest", Vector3(-1.0, 0, 0.45), 0.0, 1.0, "k"], ["kd_bookcase_wide", Vector3(0.6, 0, 0.3), 0.0, 1.0, "k"]]},
	"jade_memorial": {"pieces": [["kd_urn_square", Vector3(-1.2, 0, 0.35), 0.0, 1.0, "k"], ["kd_altar_stone", Vector3(0.2, 0, 0.7), 0.0, 0.9, "k"],
		["kd_offering_bowl", Vector3(0.2, 0.88, 0.65), 0.0, 1.0, "o"], ["kd_urn_round", Vector3(1.5, 0, 0.4), 0.0, 0.9, "k"]]},
	"jade_roots": {"pieces": [["roots", Vector3(0.0, 0, 0.9), 90.0, 0.7, "d"], ["kd_ground_leaves", Vector3(-1.0, 0, 0.6), 0.0, 1.2, "d"],
		["kd_mushrooms_pale", Vector3(1.0, 0, 0.7), 0.0, 1.0, "d"]]},
	"chain_service": {"pieces": [["kd_fire_basket", Vector3(-1.0, 0, 0.65), 0.0, 1.0, "k"], ["@fire", Vector3(-1.0, 0.42, 0.65), 0.0, 0.8, "o"],
		["kd_crate", Vector3(0.4, 0, 0.55), 90.0, 1.0, "k"], ["kd_crate", Vector3(1.4, 0, 0.55), 70.0, 0.85, "k"]]},
	"vein_maintenance": {"pieces": [["kd_debris_wood", Vector3(-0.9, 0, 0.7), 0.0, 1.1, "d"], ["kd_crate", Vector3(0.5, 0, 0.55), 75.0, 0.9, "k"],
		["kd_barrel", Vector3(1.4, 0.45, 0.8), 0.0, 0.85, "d", 84.0]]},
	# ---- corner landmarks (existing bespoke pieces; at most one per room) -----------------------------------------
	"c_mushroom": {"corner": true, "pieces": [["mushroom_giant", Vector3(1.4, 0, 1.4), 0.0, 0.7, "k"], ["@glow", Vector3(1.6, 2.2, 1.6), 0.0, 1.0, "o"]]},
	"c_furnace": {"corner": true, "pieces": [["forge_furnace", Vector3(1.6, 0, 1.5), 0.0, 0.8, "k"], ["@fire", Vector3(1.6, 1.0, 2.6), 0.0, 1.1, "o"]]},
	"c_crucible": {"corner": true, "pieces": [["lava_crucible", Vector3(1.1, 0, 1.1), 0.0, 1.0, "k"], ["@glow", Vector3(1.1, 1.8, 1.1), 0.0, 1.0, "o"]]},
	"c_crystal": {"corner": true, "pieces": [["ice_crystal_large", Vector3(1.2, 0, 1.2), 0.0, 0.8, "k"]]},
	"c_pylon": {"corner": true, "pieces": [["crystal_pylon", Vector3(1.0, 0, 1.0), 0.0, 1.0, "k"]]},
	"c_statue": {"corner": true, "pieces": [["statue_knight", Vector3(1.0, 0, 1.0), 45.0, 0.9, "k"]]},
	"c_obelisk": {"corner": true, "pieces": [["obelisk_corrupted", Vector3(1.3, 0, 1.3), 0.0, 0.7, "k"]]},
	"c_rock": {"corner": true, "pieces": [["kd_shore_rocks_c", Vector3(1.2, -0.3, 1.2), 0.0, 0.5, "k"]]},
	"c_dead_tree": {"corner": true, "pieces": [["tree_dead_a", Vector3(1.2, 0, 1.2), 0.0, 0.7, "k"]]},
	"c_glass": {"corner": true, "pieces": [["zr_glass_growth", Vector3(1.4, 0, 1.4), 0.0, 0.6, "k"]]},
	"c_serpent": {"corner": true, "pieces": [["zr_serpent_statue", Vector3(1.4, 0, 1.3), 45.0, 0.7, "k"]]},
	"c_telescope": {"corner": true, "pieces": [["brass_telescope", Vector3(1.1, 0, 1.1), 45.0, 1.0, "k"]]},
	"c_sarcophagus": {"corner": true, "pieces": [["sarcophagus", Vector3(1.4, 0, 0.8), 0.0, 1.0, "k"]]},
}

## Role -> motif names, per theme. "boss": the arena's one silhouette (placed in its two farthest corners, nothing else);
## "edge": small single pieces along basin/gallery parapets; "decay": what replaces a work motif on deep floors.
const T := {
	&"fungal": {"arrival": ["fungal_log", "c_mushroom", "fungal_stump"], "work": ["storage", "timber_fall", "fungal_stump"], "function": ["fungal_log", "pod_cluster", "c_mushroom"],
		"traversal": ["fungal_stump"], "seal": ["fungal_log"], "boss": ["mushroom_giant", 0.6], "edge": ["kd_mushrooms_pale", "kd_ground_leaves"],
		"decay": ["timber_fall"]},
	&"drowned": {"arrival": ["wreck_rib", "service_corner"], "work": ["storage", "storage_wet"], "function": ["coffin_old", "wreck_rib", "sea_growth"],
		"traversal": ["cargo_spill", "sea_growth"], "seal": ["coffin_old"], "boss": ["barnacle_pillar", 0.7], "edge": ["kd_lantern_candle", "kd_debris_wood"],
		"decay": ["cargo_spill"]},
	&"ember": {"arrival": ["forge_station", "c_furnace", "service_corner"], "work": ["tool_store", "fuel_store", "ore_haul"], "function": ["forge_station", "c_furnace", "c_crucible"],
		"traversal": ["ore_haul"], "seal": ["tool_store"], "boss": ["basalt_column", 0.6], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"rime": {"arrival": ["frost_burial", "candle_niche"], "work": ["storage", "urn_niche"], "function": ["frost_burial", "sarcophagus_bay", "c_crystal"],
		"traversal": ["urn_niche"], "seal": ["candle_niche"], "boss": ["ice_crystal_large", 0.9], "edge": ["kd_candles", "kd_urn_round"],
		"decay": ["rubble_fall"]},
	&"orrery": {"arrival": ["c_telescope", "lectern_corner"], "work": ["archive", "archive_wide"], "function": ["study_desk", "instrument_bench", "c_telescope"],
		"traversal": ["instrument_bench"], "seal": ["study_desk"], "boss": ["crystal_pylon", 1.0], "edge": ["kd_books", "kd_candles"],
		"decay": ["rubble_fall"]},
	&"hideout": {"arrival": ["stash", "service_corner"], "work": ["storage", "stash"], "function": ["mess_bench", "bunks", "stash"],
		"traversal": ["cargo_spill"], "seal": ["storage"], "boss": ["kd_log_stack", 1.2], "edge": ["kd_crate", "kd_barrel"], "decay": ["timber_fall"]},
	&"crypt": {"arrival": ["knight_niche", "sarcophagus_bay", "candle_niche"], "work": ["urn_niche", "storage"], "function": ["coffin_bay", "sarcophagus_bay", "memorial", "altar"],
		"traversal": ["urn_niche"], "seal": ["candle_niche"], "boss": ["kd_obelisk", 1.3], "edge": ["kd_candles", "kd_urn_round"], "decay": ["rubble_fall"]},
	&"hive": {"arrival": ["c_mushroom", "pod_cluster"], "work": ["fungal_stump", "timber_fall"], "function": ["pod_cluster", "c_mushroom", "fungal_log"],
		"traversal": ["pod_cluster"], "seal": ["fungal_stump"], "boss": ["spore_pod", 1.6], "edge": ["kd_mushrooms_pale"], "decay": ["timber_fall"]},
	&"mire": {"arrival": ["c_dead_tree", "wet_timber", "service_corner"], "work": ["storage_wet", "wet_timber"], "function": ["wet_timber", "fungal_stump", "c_dead_tree"],
		"traversal": ["wet_timber"], "seal": ["storage_wet"], "boss": ["tree_dead_a", 0.8], "edge": ["kd_grass_large", "kd_mushrooms_pale"], "decay": ["timber_fall"]},
	&"thorn": {"arrival": ["c_dead_tree", "thorn_seam"], "work": ["timber_fall", "fuel_store"], "function": ["thorn_seam", "c_dead_tree", "altar_wood"],
		"traversal": ["thorn_seam"], "seal": ["thorn_seam"], "boss": ["tree_dead_a", 0.9], "edge": ["kd_ground_leaves", "kd_stump_old"],
		"decay": ["timber_fall"]},
	&"sandtomb": {"arrival": ["column_pair", "offering_row"], "work": ["urn_niche", "storage"], "function": ["altar", "sarcophagus_bay", "offering_row"],
		"traversal": ["rubble_fall"], "seal": ["offering_row"], "boss": ["kd_column", 1.4], "edge": ["kd_offering_bowl", "kd_urn_square"],
		"decay": ["rubble_fall"]},
	&"storm": {"arrival": ["c_pylon", "service_corner"], "work": ["tool_store", "storage"], "function": ["instrument_bench", "c_pylon", "c_telescope"],
		"traversal": ["service_corner"], "seal": ["tool_store"], "boss": ["crystal_pylon", 1.2], "edge": ["kd_lantern_candle", "kd_debris_stone"],
		"decay": ["rubble_fall"]},
	&"umbral": {"arrival": ["c_obelisk", "candle_niche"], "work": ["urn_niche", "rubble_fall"], "function": ["altar_broken", "c_obelisk", "plinth"],
		"traversal": ["urn_niche"], "seal": ["candle_niche"], "boss": ["obelisk_corrupted", 0.7], "edge": ["kd_candles", "kd_urn_round"],
		"decay": ["rubble_fall"]},
	&"crystal": {"arrival": ["c_crystal", "expedition"], "work": ["crystal_shelf", "rubble_fall"], "function": ["c_crystal", "c_pylon", "crystal_shelf"],
		"traversal": ["crystal_shelf"], "seal": ["crystal_shelf"], "boss": ["ice_crystal_large", 1.0], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"gilded": {"arrival": ["knight_niche", "display"], "work": ["vault_store", "archive_wide"], "function": ["display", "vault_store", "c_statue"],
		"traversal": ["column_pair"], "seal": ["knight_niche"], "boss": ["statue_knight", 1.0], "edge": ["kd_chalice", "kd_candles"], "decay": ["rubble_fall"]},
	&"cavern": {"arrival": ["ore_haul", "expedition"], "work": ["ore_haul", "mine_props"], "function": ["mine_props", "c_rock", "ore_haul"],
		"traversal": ["mine_props"], "seal": ["tool_store"], "boss": ["kd_shore_rocks_a", 0.6], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"abyss": {"arrival": ["obelisk_pair", "candle_niche"], "work": ["rubble_fall", "bone_midden"], "function": ["c_obelisk", "memorial", "bone_midden"],
		"traversal": ["rubble_fall"], "seal": ["memorial"], "boss": ["obelisk_corrupted", 0.8], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"prism": {"arrival": ["c_pylon", "expedition"], "work": ["crystal_shelf"], "function": ["c_pylon", "c_crystal", "column_pair"],
		"traversal": ["crystal_shelf"], "seal": ["column_pair"], "boss": ["crystal_pylon", 1.4], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"underworld": {"arrival": ["c_sarcophagus", "candle_niche"], "work": ["urn_niche", "offering_row"], "function": ["coffin_old", "memorial", "c_sarcophagus"],
		"traversal": ["urn_niche"], "seal": ["memorial"], "boss": ["obelisk_corrupted", 0.8], "edge": ["kd_candles", "kd_urn_round"],
		"decay": ["rubble_fall"]},
	&"aether": {"arrival": ["c_telescope", "lectern_corner"], "work": ["archive_wide", "rubble_fall"], "function": ["instrument_bench", "study_desk", "c_telescope"],
		"traversal": ["rubble_fall"], "seal": ["instrument_bench"], "boss": ["crystal_pylon", 1.2], "edge": ["kd_books", "kd_debris_stone"],
		"decay": ["rubble_fall"]},
	&"eclipse": {"arrival": ["knight_niche", "candle_niche"], "work": ["candle_niche", "urn_niche"], "function": ["altar", "knight_niche", "c_obelisk"],
		"traversal": ["candle_niche"], "seal": ["altar"], "boss": ["statue_knight", 1.1], "edge": ["kd_candles"], "decay": ["rubble_fall"]},
	&"solar": {"arrival": ["column_pair", "offering_row"], "work": ["urn_niche", "storage_wet"], "function": ["offering_row", "column_pair", "altar"],
		"traversal": ["rubble_fall"], "seal": ["offering_row"], "boss": ["kd_column", 1.5], "edge": ["kd_offering_bowl", "kd_urn_round"],
		"decay": ["rubble_fall"]},
	&"jade": {"arrival": ["c_serpent", "jade_memorial"], "work": ["urn_niche", "jade_roots"], "function": ["jade_memorial", "sarcophagus_bay", "c_serpent"],
		"traversal": ["jade_roots"], "seal": ["jade_memorial"], "boss": ["zr_glyph_stele", 1.0], "edge": ["kd_urn_square", "kd_ground_leaves"],
		"decay": ["jade_roots"]},
	&"obsidian": {"arrival": ["c_crucible", "chain_service"], "work": ["chain_service", "storage"], "function": ["c_crucible", "c_glass", "tool_store"],
		"traversal": ["rubble_fall"], "seal": ["chain_service"], "boss": ["basalt_column", 0.6], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"vein": {"arrival": ["c_glass", "vein_maintenance"], "work": ["vein_maintenance", "tool_store"], "function": ["c_glass", "rubble_fall", "bone_midden"],
		"traversal": ["vein_maintenance"], "seal": ["vein_maintenance"], "boss": ["zr_glass_growth", 0.7], "edge": ["kd_debris_wood", "kd_debris_stone"],
		"decay": ["rubble_fall"]},
	# bh-042: the five Abyss themes (DataDungeonsAbyss)
	&"hollow": {"arrival": ["knight_niche", "candle_niche"], "work": ["urn_niche", "bone_midden"], "function": ["coffin_bay", "sarcophagus_bay", "memorial", "altar"],
		"traversal": ["urn_niche"], "seal": ["memorial"], "boss": ["obelisk_corrupted", 1.0], "edge": ["kd_candles", "kd_urn_round"], "decay": ["rubble_fall"]},
	&"sunless": {"arrival": ["wreck_rib", "candle_niche"], "work": ["storage_wet", "cargo_spill"], "function": ["coffin_old", "sea_growth", "memorial"],
		"traversal": ["cargo_spill"], "seal": ["coffin_old"], "boss": ["statue_collapsed", 1.0], "edge": ["kd_debris_stone", "kd_lantern_candle"], "decay": ["rubble_fall"]},
	&"ashgrave": {"arrival": ["forge_station", "chain_service"], "work": ["tool_store", "fuel_store", "ore_haul"], "function": ["forge_station", "c_furnace", "c_crucible"],
		"traversal": ["ore_haul"], "seal": ["tool_store"], "boss": ["basalt_column", 0.7], "edge": ["kd_debris_stone"], "decay": ["rubble_fall"]},
	&"weeping": {"arrival": ["knight_niche", "frost_burial"], "work": ["urn_niche", "storage"], "function": ["frost_burial", "sarcophagus_bay", "knight_niche"],
		"traversal": ["urn_niche"], "seal": ["candle_niche"], "boss": ["ice_crystal_large", 1.0], "edge": ["kd_candles", "kd_urn_round"], "decay": ["rubble_fall"]},
	&"throne": {"arrival": ["obelisk_pair", "knight_niche"], "work": ["bone_midden", "rubble_fall"], "function": ["altar", "c_obelisk", "memorial", "plinth"],
		"traversal": ["rubble_fall"], "seal": ["altar"], "boss": ["obelisk_corrupted", 1.2], "edge": ["kd_candles", "kd_chalice"], "decay": ["rubble_fall"]},
}

## Dungeons that share a theme but must not be copies of each other.
const BY_DUNGEON := {
	# Cutpurse Cellars: stolen cargo sorted into caches, a mess bench, an identifiable stash corner
	&"cellars": {"work": ["storage", "stash"], "function": ["stash", "mess_bench", "sleep_corner"], "boss": ["kd_crate_bottles", 1.2]},
	# Gnashgut Burrows: rough shelter, scavenged timber, bones; no orderly tables
	&"burrows": {"arrival": ["rough_shelter"], "work": ["timber_fall", "bone_midden"], "function": ["rough_shelter", "bone_midden", "c_rock"],
		"traversal": ["bone_midden"], "seal": ["rough_shelter"], "boss": ["skull_pile", 1.4], "edge": ["kd_debris_wood"]},
	# Ironjaw Warcamp: deliberate supplies, repair and eating; weapons on racks, fuel stacked
	&"warcamp": {"arrival": ["war_supply"], "work": ["war_supply", "fuel_store", "tool_store"], "function": ["war_table", "bunks", "forge_station"],
		"seal": ["war_supply"], "boss": ["weapon_rack", 1.2]},
	# Blackvault Ossuary: ordered burial bays, local collapse
	&"ossuary": {"work": ["urn_niche", "rubble_fall"], "function": ["coffin_bay", "coffin_old", "memorial", "cell_bars"]},
	# Twinspire Reliquary: paired, formal, vertical — columns and niches, precious ceremonial storage
	&"reliquary": {"arrival": ["column_pair"], "work": ["vault_store", "offering_row"], "function": ["column_pair", "sarcophagus_bay", "altar", "knight_niche"],
		"traversal": ["column_pair"], "boss": ["kd_column", 1.6]},
}

static func table(theme: StringName, dungeon: StringName) -> Dictionary:
	var t: Dictionary = (T.get(theme, T[&"drowned"]) as Dictionary).duplicate()
	if BY_DUNGEON.has(dungeon):
		t.merge(BY_DUNGEON[dungeon], true)
	return t

## Every kit piece any motif or boss silhouette uses (tests check each exists).
static func pieces() -> Array:
	var out := {}
	for k in M:
		for p in M[k].pieces:
			if not String(p[0]).begins_with("@"):
				out[p[0]] = true
	for th in T:
		out[T[th].boss[0]] = true
		for e in T[th].edge:
			out[e] = true
	for d in BY_DUNGEON:
		if BY_DUNGEON[d].has("boss"):
			out[BY_DUNGEON[d].boss[0]] = true
	return out.keys()
