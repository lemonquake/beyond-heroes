class_name DataVignettes
## Map-design pass (2026-10-03): small authored arrangements that explain what a place is for — a woodpile beside the
## forge, a cargo stack on the quay, a bench with a view, a burial bay. A map places one with MapBuilder.vignette();
## each piece is set relative to the group's origin and yaw and grounded on its own spot. Groups are asymmetric on
## purpose and stay compact (their `r` is the footprint radius checked against the map's walking lines).
##
## Piece: [kit name, Vector3 local offset (y is height above the ground at that spot), local yaw, scale, kind]
## kind: "k" kit piece with collision (under Props, baked into the navmesh) | "d" decoration without collision |
##       "b" batched decoration (MultiMesh; thinned on Low by MapBuilder.LITE_KEEP) | "o" optional detail: dropped on Low
## Optional pieces are the smallest storytelling details (a cup, a bottle); landmarks and colliders never vary by quality.

const V := {
	# ---- work and storage ---------------------------------------------------------------------------------------
	"woodpile": {"r": 2.2, "pieces": [
		["kd_log_stack", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_stump_cut", Vector3(1.6, 0, 0.7), 20.0, 1.0, "k"],
		["ph_wooden_axe", Vector3(1.55, 0.44, 0.75), 70.0, 1.0, "o"],
		["kd_log", Vector3(-0.5, 0, 1.5), 84.0, 0.8, "k"],
		["kd_grass", Vector3(-1.2, 0, -0.6), 0.0, 1.0, "b"]]},
	"supply_corner": {"r": 1.8, "pieces": [
		["kd_crate", Vector3(0, 0, 0), 4.0, 1.0, "k"],
		["kd_crate", Vector3(0.08, 0.69, 0.04), 16.0, 0.92, "k"],
		["kd_barrel", Vector3(1.25, 0, -0.15), 0.0, 1.0, "k"],
		["kd_shovel", Vector3(-0.72, 0, -0.35), 12.0, 1.0, "o"],
		["ph_wooden_bucket_01", Vector3(1.0, 0, 0.75), 0.0, 1.0, "o"]]},
	"cargo_stack": {"r": 2.4, "pieces": [
		["kd_crate", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_crate", Vector3(1.05, 0, 0.1), 6.0, 1.0, "k"],
		["kd_crate", Vector3(0.5, 0.69, 0.05), -10.0, 0.95, "k"],
		["kd_barrel", Vector3(-1.2, 0, 0.3), 0.0, 1.0, "k"],
		["kd_barrel", Vector3(-1.0, 0, 1.35), 40.0, 0.92, "k"],
		["kd_bottle_large", Vector3(1.9, 0, 0.9), 0.0, 1.0, "o"]]},
	"tavern_stock": {"r": 2.0, "pieces": [
		["kd_barrel", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_barrel", Vector3(1.05, 0, -0.1), 30.0, 1.0, "k"],
		["kd_barrel", Vector3(0.5, 0.95, -0.05), 10.0, 0.95, "k"],
		["kd_crate_bottles", Vector3(-1.2, 0, 0.35), -8.0, 1.0, "k"],
		["kd_bottle", Vector3(-1.3, 0, 1.15), 0.0, 1.0, "o"]]},
	"tool_corner": {"r": 2.0, "pieces": [
		["kd_crate", Vector3(0, 0, 0), 8.0, 1.0, "k"],
		["kd_log_stack", Vector3(-1.5, 0, 0.1), 90.0, 0.8, "k"],
		["kd_shovel", Vector3(0.75, 0, -0.3), -15.0, 1.0, "o"],
		["kd_barrel", Vector3(0.9, 0, 0.75), 0.0, 0.9, "k"]]},
	"salvage": {"r": 2.4, "pieces": [
		["kd_debris_wood", Vector3(0, 0, 0), 0.0, 1.2, "d"],
		["kd_crate", Vector3(1.3, 0, -0.4), 28.0, 1.0, "k"],
		["kd_barrel", Vector3(-1.3, 0, 0.5), 0.0, 0.95, "k"],
		["kd_debris_stone", Vector3(0.6, 0, 1.4), 120.0, 0.9, "d"],
		["kd_shovel", Vector3(1.9, 0, 0.6), 40.0, 1.0, "o"]]},
	"timber_store": {"r": 2.6, "pieces": [
		["kd_log_stack", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_log_stack", Vector3(0.1, 0.9, 0.15), 6.0, 0.85, "k"],
		["kd_log", Vector3(1.9, 0, 0.6), 4.0, 0.9, "k"],
		["kd_stump_cut", Vector3(-1.6, 0, 1.1), 0.0, 1.0, "k"],
		["ph_wooden_axe", Vector3(-1.55, 0.44, 1.15), 40.0, 1.0, "o"]]},
	"harvest_rest": {"r": 2.4, "pieces": [
		["kd_crate", Vector3(0, 0, 0), 10.0, 1.0, "k"],
		["kd_pumpkin", Vector3(1.0, 0, 0.4), 0.0, 1.0, "b"], ["kd_pumpkin", Vector3(1.5, 0, -0.3), 60.0, 0.9, "b"],
		["kd_pumpkin", Vector3(0.1, 0.69, 0.05), 20.0, 0.8, "b"],
		["ph_wicker_basket_02", Vector3(-1.1, 0, 0.6), 0.0, 1.0, "d"],
		["kd_carrots", Vector3(-1.1, 0.12, 0.6), 0.0, 0.8, "b"],
		["kd_shovel", Vector3(-1.4, 0, -0.6), 15.0, 1.0, "o"],
		["ph_wooden_bucket_01", Vector3(0.6, 0, 1.4), 0.0, 1.0, "o"]]},
	# ---- daily life ---------------------------------------------------------------------------------------------
	"covered_store": {"r": 2.4, "pieces": [
		["kd_canopy", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_crate", Vector3(-0.6, 0, -0.5), 6.0, 1.0, "k"],
		["kd_crate", Vector3(0.45, 0, -0.6), -10.0, 0.95, "k"],
		["kd_barrel", Vector3(0.4, 0, 0.6), 0.0, 0.9, "k"],
		["kd_bottle_large", Vector3(-0.8, 0, 0.7), 0.0, 1.0, "o"]]},
	"civic_record": {"r": 1.8, "pieces": [
		["kd_side_table", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_books", Vector3(-0.2, 0.86, 0.0), 20.0, 1.0, "o"],
		["kd_bench", Vector3(1.3, 0, 0.4), -90.0, 1.0, "k"],
		["kd_plant_tall", Vector3(-1.1, 0, -0.1), 0.0, 1.0, "d"]]},
	"bamboo_garden": {"r": 2.2, "pieces": [
		["kd_bamboo", Vector3(-0.8, 0, -0.4), 0.0, 1.0, "k"],
		["kd_bamboo", Vector3(0.6, 0, -0.7), 70.0, 0.85, "k"],
		["kd_pot_small", Vector3(1.3, 0, 0.5), 0.0, 1.0, "d"],
		["kd_plant_leafy", Vector3(-0.2, 0, 0.8), 0.0, 1.0, "b"]]},
	"tea_corner": {"r": 1.8, "pieces": [
		["kd_table_round", Vector3(0, 0, 0), 0.0, 0.7, "k"],
		["kd_stool_square", Vector3(-0.95, 0, 0.1), 90.0, 0.9, "k"],
		["kd_stool_square", Vector3(0.9, 0, -0.2), -90.0, 0.9, "k"],
		["kd_bottle_large", Vector3(0.1, 0.58, 0.05), 0.0, 0.7, "o"]]},
	"bench_view": {"r": 1.6, "pieces": [
		["kd_bench", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_bench", Vector3(1.05, 0, 0.15), -8.0, 1.0, "k"],
		["bush_a", Vector3(-1.0, 0, -0.35), 0.0, 1.0, "b"]]},
	"garden_bed": {"r": 1.5, "pieces": [
		["kd_planter", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_flower_yellow", Vector3(-0.25, 0.3, 0.1), 0.0, 0.9, "b"],
		["kd_flower_purple", Vector3(0.22, 0.3, -0.12), 40.0, 0.9, "b"],
		["bush_a", Vector3(0.95, 0, 0.4), 0.0, 0.8, "b"]]},
	"flower_border": {"r": 1.8, "pieces": [
		["bush_a", Vector3(0, 0, 0), 0.0, 1.0, "b"],
		["kd_flower_yellow", Vector3(0.7, 0, 0.25), 0.0, 1.0, "b"],
		["kd_flower_purple", Vector3(1.25, 0, -0.1), 0.0, 1.0, "b"],
		["kd_grass", Vector3(-0.8, 0, 0.3), 0.0, 1.0, "b"],
		["bush_a", Vector3(1.9, 0, 0.2), 60.0, 0.8, "b"]]},
	"kitchen_garden": {"r": 3.2, "pieces": [
		["kd_fence", Vector3(-1.3, 0, -1.8), 0.0, 1.0, "k"],
		["kd_fence_gate", Vector3(1.3, 0, -1.8), 0.0, 1.0, "d"],
		["kd_carrots", Vector3(-1.6, 0, -0.6), 0.0, 1.0, "b"], ["kd_carrots", Vector3(-1.0, 0, -0.6), 30.0, 1.0, "b"],
		["kd_carrots", Vector3(-0.4, 0, -0.6), 60.0, 1.0, "b"], ["kd_carrots", Vector3(-1.6, 0, 0.2), 10.0, 1.0, "b"],
		["kd_carrots", Vector3(-1.0, 0, 0.2), 50.0, 1.0, "b"],
		["kd_pumpkin", Vector3(0.6, 0, -0.4), 0.0, 1.0, "b"], ["kd_pumpkin", Vector3(1.2, 0, 0.3), 70.0, 0.9, "b"],
		["kd_shovel", Vector3(2.1, 0, -1.4), 10.0, 1.0, "o"],
		["ph_wooden_bucket_02", Vector3(1.9, 0, 0.6), 0.0, 1.0, "o"],
		["kd_tree_small", Vector3(-2.6, 0, -2.9), 0.0, 1.0, "k"]]},
	"produce_display": {"r": 1.8, "pieces": [
		["kd_crate", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_pumpkin", Vector3(0.05, 0.69, 0.1), 0.0, 0.85, "b"],
		["kd_pumpkin", Vector3(1.0, 0, 0.2), 45.0, 1.0, "b"],
		["ph_wicker_basket_01", Vector3(-0.95, 0, 0.25), 0.0, 1.0, "d"],
		["kd_carrots", Vector3(-0.95, 0.18, 0.25), 0.0, 0.8, "b"]]},
	"netmender": {"r": 2.6, "pieces": [
		["fishing_nets", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_paddle", Vector3(1.6, 0, -0.4), 20.0, 1.0, "d"],
		["kd_crate", Vector3(-1.5, 0, 0.3), -12.0, 1.0, "k"],
		["kd_bottle_large", Vector3(-1.55, 0.69, 0.3), 0.0, 1.0, "o"],
		["ph_wooden_stool_01", Vector3(0.6, 0, 1.2), 0.0, 1.0, "d"]]},
	"book_corner": {"r": 1.4, "pieces": [
		["kd_bench", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_books", Vector3(0.2, 0.47, 0.0), 30.0, 1.0, "o"],
		["kd_plant_pot_a", Vector3(-0.85, 0, 0.1), 0.0, 1.4, "d"],
		["kd_plant_tall", Vector3(0.95, 0, -0.1), 0.0, 1.0, "d"]]},
	"camp_seating": {"r": 2.8, "pieces": [
		["kd_fire_ring", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_log", Vector3(0, 0, -1.9), 90.0, 0.75, "k"],
		["kd_log", Vector3(1.85, 0, 0.5), 20.0, 0.75, "k"],
		["kd_stump_cut", Vector3(-1.7, 0, 0.8), 0.0, 1.0, "k"]]},
	"tent_pitch": {"r": 2.6, "pieces": [
		["kd_tent", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_crate", Vector3(1.7, 0, -0.6), 20.0, 0.85, "k"],
		["bedroll", Vector3(-1.6, 0, 0.9), 80.0, 1.0, "d"]]},
	"civic_planters": {"r": 2.0, "pieces": [
		["kd_plant_tall", Vector3(-1.1, 0, 0), 0.0, 1.0, "d"],
		["kd_planter", Vector3(0.2, 0, 0.1), 0.0, 1.0, "k"],
		["kd_bush", Vector3(0.2, 0.3, 0.1), 0.0, 0.6, "b"],
		["kd_plant_tall", Vector3(1.4, 0, -0.1), 30.0, 0.9, "d"]]},
	# ---- water's edge -----------------------------------------------------------------------------------------
	"boat_landing": {"r": 3.0, "pieces": [
		["kd_planks", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_paddle", Vector3(1.1, 0, -0.9), 70.0, 1.0, "d"],
		["kd_crate", Vector3(-1.2, 0, -0.9), 10.0, 0.9, "k"],
		["kd_barrel", Vector3(-1.1, 0, 0.3), 0.0, 0.9, "k"]]},
	"canoe_mooring": {"r": 2.4, "pieces": [
		["kd_canoe", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_paddle", Vector3(0.9, 0, 1.0), 80.0, 1.0, "d"],
		["kd_rock_flat", Vector3(-1.2, 0, -1.4), 0.0, 1.0, "b"]]},
	"herb_pots": {"r": 1.6, "pieces": [
		["kd_pot_small", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_plant_leafy", Vector3(0, 0.3, 0), 0.0, 0.5, "b"],
		["kd_plant_pot_b", Vector3(0.65, 0, 0.3), 0.0, 1.6, "d"],
		["kd_plant_pot_a", Vector3(-0.6, 0, 0.35), 30.0, 1.6, "d"],
		["kd_bottle_large", Vector3(0.9, 0, -0.45), 0.0, 1.0, "o"],
		["kd_flower_yellow", Vector3(-1.0, 0, -0.3), 0.0, 1.0, "b"]]},
	"moored_rowboat": {"r": 2.6, "pieces": [
		["kd_rowboat", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_paddle", Vector3(0.2, 0.35, 0.3), 90.0, 1.0, "d"],
		["kd_crate", Vector3(-0.4, 0.25, -0.5), 20.0, 0.6, "o"]]},
	"waiting_place": {"r": 2.2, "pieces": [
		["kd_bench", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_crate", Vector3(1.4, 0, -0.2), 12.0, 1.0, "k"],
		["kd_barrel", Vector3(1.5, 0, 0.9), 0.0, 0.9, "k"],
		["kd_lantern_candle", Vector3(-0.9, 0, 0.2), 0.0, 1.0, "d"]]},
	"shore_debris": {"r": 3.0, "pieces": [
		["kd_debris_wood", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_rock_small_a", Vector3(1.4, 0, 0.6), 0.0, 1.0, "b"],
		["kd_rock_flat", Vector3(-1.2, 0, 0.8), 40.0, 1.0, "b"],
		["kd_barrel", Vector3(2.2, 0, -0.5), 0.0, 0.85, "d"]]},
	# ---- nature -----------------------------------------------------------------------------------------------
	"rock_cluster_l": {"r": 3.2, "pieces": [
		["kd_rock_b", Vector3(0, -0.1, 0), 0.0, 1.0, "k"],
		["kd_rock_c", Vector3(-2.2, -0.1, -1.2), 60.0, 0.6, "k"],
		["kd_rock_small_a", Vector3(1.9, 0, 1.1), 30.0, 1.0, "b"],
		["kd_rock_flat", Vector3(-1.8, 0, 1.3), 10.0, 1.0, "b"],
		["kd_grass_large", Vector3(1.3, 0, -1.2), 0.0, 1.0, "b"],
		["kd_grass", Vector3(-1.2, 0, -1.4), 0.0, 1.0, "b"]]},
	"rock_cluster_m": {"r": 2.6, "pieces": [
		["kd_rock_a", Vector3(0, -0.1, 0), 0.0, 0.85, "k"],
		["kd_rock_small_b", Vector3(-1.6, 0, 0.7), 0.0, 1.0, "b"],
		["kd_grass", Vector3(1.2, 0, 0.9), 0.0, 1.0, "b"]]},
	"rock_tall": {"r": 2.4, "pieces": [
		["kd_rock_tall", Vector3(0, -0.1, 0), 0.0, 1.0, "k"],
		["kd_rock_small_a", Vector3(1.6, 0, 0.9), 0.0, 1.0, "b"],
		["kd_rock_flat", Vector3(-1.4, 0, 1.0), 60.0, 0.9, "b"]]},
	"lane_tree": {"r": 1.6, "pieces": [
		["kd_tree_thin", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["bush_a", Vector3(0.9, 0, 0.5), 0.0, 1.0, "b"],
		["kd_grass", Vector3(-0.7, 0, 0.6), 0.0, 1.0, "b"]]},
	"tree_group": {"r": 4.5, "pieces": [
		["kd_tree_oak", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_tree_broadleaf", Vector3(3.2, 0, 1.4), 70.0, 0.9, "k"],
		["kd_bush_large", Vector3(1.4, 0, 2.0), 0.0, 1.0, "b"],
		["kd_bush", Vector3(-1.8, 0, 1.2), 0.0, 1.0, "b"],
		["kd_grass_large", Vector3(2.4, 0, -1.4), 0.0, 1.0, "b"]]},
	"pine_group": {"r": 4.0, "pieces": [
		["kd_pine", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_pine_round", Vector3(2.8, 0, 1.2), 40.0, 1.0, "k"],
		["kd_pine_tall", Vector3(-1.4, 0, -2.4), 0.0, 1.0, "k"],
		["kd_rock_small_b", Vector3(1.2, 0, 2.2), 0.0, 1.0, "b"]]},
	"palm_group": {"r": 3.8, "pieces": [
		["kd_palm_tall", Vector3(-2.2, 0, -2.4), 30.0, 1.0, "k"],
		["kd_palm", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_palm_bend", Vector3(2.6, 0, 1.0), 200.0, 1.0, "k"],
		["kd_palm_short", Vector3(-1.4, 0, 1.6), 0.0, 1.0, "d"],
		["kd_plant_leafy", Vector3(1.0, 0, 2.2), 0.0, 1.0, "b"],
		["kd_ground_leaves", Vector3(-0.6, 0, -1.2), 0.0, 1.0, "b"]]},
	"palm_pair": {"r": 2.8, "pieces": [
		["kd_palm_bend", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_palm_short", Vector3(1.9, 0, 1.3), 40.0, 0.9, "d"],
		["kd_plant_leafy", Vector3(-1.0, 0, 1.4), 0.0, 1.0, "b"]]},
	"fallen_tree": {"r": 3.0, "pieces": [
		["kd_log", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["kd_stump_old", Vector3(0.5, 0, -1.9), 0.0, 1.0, "k"],
		["kd_mushrooms_pale", Vector3(0.6, 0, 0.6), 0.0, 1.0, "b"],
		["kd_mushrooms_pale", Vector3(-0.5, 0, -0.7), 90.0, 0.8, "b"],
		["kd_ground_leaves", Vector3(-0.8, 0, 1.0), 0.0, 1.0, "b"]]},
	# ---- burial and offering ----------------------------------------------------------------------------------
	"offering": {"r": 1.2, "pieces": [
		["kd_candles", Vector3(0, 0, 0), 0.0, 1.0, "d"],
		["kd_offering_bowl", Vector3(0.45, 0, 0.2), 0.0, 1.0, "d"],
		["kd_chalice", Vector3(-0.35, 0, 0.3), 0.0, 1.0, "o"]]},
	"grave_cluster": {"r": 2.6, "pieces": [
		["kd_grave_broken", Vector3(0, 0, 0), 0.0, 1.0, "k"],
		["gravestone_a", Vector3(1.6, 0, -0.3), -8.0, 1.0, "k"],
		["kd_candles", Vector3(0.6, 0, 0.8), 0.0, 1.0, "d"],
		["kd_grass", Vector3(-1.2, 0, 0.6), 0.0, 1.0, "b"]]},
	"jade_threshold": {"r": 3.0, "pieces": [
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
	"wreck": {"r": 7.0, "pieces": [
		["kd_wreck", Vector3(0, -0.6, 0), 0.0, 1.0, "d"],
		["kd_debris_wood", Vector3(4.2, 0, 3.0), 30.0, 1.2, "d"],
		["kd_barrel", Vector3(5.0, 0, 1.4), 0.0, 0.9, "d"],
		["kd_crate", Vector3(-4.0, 0, 3.6), 35.0, 0.9, "d"]]},
}

static func has(name: String) -> bool:
	return V.has(name)

static func get_def(name: String) -> Dictionary:
	return V.get(name, {})

## Every kit piece any vignette uses (tests check each exists).
static func pieces() -> Array:
	var out := {}
	for k in V:
		for p in V[k].pieces:
			out[p[0]] = true
	return out.keys()
