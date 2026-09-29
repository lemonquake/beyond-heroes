class_name DataIsland
## Salmonan as one connected geography: named places, the roads between them (authored walkable polylines in each
## map's local XZ metres) and the transitions that join maps (the South Gate road, doors, waypoint shrines, dungeon
## gates). The map builders flatten their road beds and plant their signposts from these same polylines; the island
## atlas (M) and the directions HUD read them through RoutePlanner. New place names are provisional (docs/LORE.md §6b).
##
## The runtime is a set of bounded districts with loading boundaries; the atlas draws them as one continuous island.
## Every charted map sits on the atlas at one uniform scale (PX_M metres per atlas pixel), so a road's drawn length and
## its walked length agree. Dungeon floors are not surface geography: they draw on the Underground view.

const PX_M := 0.7                                   # metres per atlas pixel for every charted surface map
const ATLAS_SIZE := Vector2(1000, 850)              # atlas coordinate space (the base art is 2x this)
const ATLAS_ART := "res://assets/ui/atlas/salmonan_atlas.png"
const WALK_SPEED := 5.0                             # m/s used by the walking estimate when no hero is bound

## Atlas pixel of each surface map's local origin (local x/z metres map to +x/+y pixels at PX_M).
const MAP_ORIGIN := {
	&"sanctuary": Vector2(240, 527),
	&"westreach": Vector2(400, 544),
	&"ruined_forest": Vector2(366, 402),
	&"olivar": Vector2(601.5, 514.0),
	&"wyman_outpost": Vector2(618.7, 681.0),
	&"weeping_causeway": Vector2(760.0, 691.0),
}

## Surface areas revealed on the atlas once their map is discovered (atlas px ellipses: centre, radii).
const CHARTED_AREAS := {
	&"sanctuary": [Vector2(240, 527), Vector2(80, 76)],
	&"westreach": [Vector2(300, 640), Vector2(215, 150)],
	&"ruined_forest": [Vector2(366, 402), Vector2(130, 92)],
	&"olivar": [Vector2(601, 512), Vector2(100, 86)],
	&"wyman_outpost": [Vector2(619, 676), Vector2(92, 78)],
	&"weeping_causeway": [Vector2(735, 691), Vector2(70, 40)],
}

## Uncharted regions: painted on the base atlas, named here, not routable in this milestone.
const REGIONS := [
	{"name": "Stillwater Lake", "pos": Vector2(575, 392)},
	{"name": "Northern Heights", "pos": Vector2(470, 200)},
	{"name": "Reedwater Marsh", "pos": Vector2(735, 640)},
	{"name": "Eastern Shore", "pos": Vector2(845, 430)},
]

## kind: town, service, home, shrine, junction, landmark, district, dungeon. listed: shown as a destination (search, the
## sidebar list, labels). public: known from the start (charted public geography); others are found by walking near
## them. shrine: the teleporter id of the waypoint standing here. Dungeon/interior places have no surface position.
const PLACES := [
	# --- Malasugue Town (sanctuary) ---
	{"id": "town", "name": "Malasugue Town", "kind": "town", "map": "sanctuary", "pos": Vector2(0, 10.5), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The last lit hearth on Salmonan. Fountain plaza, guild halls, market and the Sanctuary Terrace."},
	{"id": "town_terrace", "name": "Sanctuary Terrace", "kind": "shrine", "map": "sanctuary", "pos": Vector2(0, -20), "listed": true, "public": true,
		"shrine": "sanctuary_waypoint", "levels": "Safe haven", "text": "The waypoint guarded by two knight statues. It connects every shrine you have awakened."},
	{"id": "town_gate", "name": "South Gate", "kind": "landmark", "map": "sanctuary", "pos": Vector2(0, 38), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Captain Hald's post. For three winters the gate stayed barred; the road beyond leads to the mill, the fields and the cove."},
	{"id": "town_tavern", "name": "The Salted Marlin", "kind": "service", "map": "sanctuary", "pos": Vector2(-23.5, 13.5), "listed": true, "public": true,
		"door": "int_tavern", "levels": "Safe haven", "text": "Tavern and inn. Rest here to recover fully."},
	{"id": "town_swordfin", "name": "Swordfin Hall", "kind": "service", "map": "sanctuary", "pos": Vector2(26.4, -4.8), "listed": true, "public": true,
		"door": "int_swordfin", "levels": "Safe haven", "text": "The Swordfin Company. Join, register and request promotion."},
	{"id": "town_lantern", "name": "Lantern House", "kind": "service", "map": "sanctuary", "pos": Vector2(-24.9, -9.5), "listed": true, "public": true,
		"door": "int_lantern", "levels": "Safe haven", "text": "The Lantern Covenant. Join, register and request promotion."},
	{"id": "town_guildhouse", "name": "The Guild House", "kind": "service", "map": "sanctuary", "pos": Vector2(-11, -4.4), "listed": true, "public": true,
		"door": "int_guildhouse", "levels": "Safe haven", "text": "Both guilds keep a counter here. Pick a guild and take paid odd jobs from its board."},
	{"id": "town_market", "name": "Merchant Quarter", "kind": "service", "map": "sanctuary", "pos": Vector2(15.0, 21.0), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The cobbled square off the plaza's south-east corner: Anton's Provisions, Seris' Arcana, Marr's Lapidary (sockets and crystals), Brannoc's Smithy and forge, the Stranger's Wagon, the Shrine of the Fallen, the Alchemy Table and the Workbench."},
	{"id": "town_forge", "name": "Brannoc's Smithy", "kind": "service", "map": "sanctuary", "pos": Vector2(21.2, 22.4), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Brannoc's smithy on the east side of the Merchant Quarter: weapons and armour, the forge, salvage and Fore-Tech weapon refits."},
	{"id": "town_lapidary", "name": "Marr's Lapidary", "kind": "service", "map": "sanctuary", "pos": Vector2(21.3, 15.0), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Ysolde Marr, Socket Specialist: opens sockets in your gear, sets crystals, purges and crystallizes, and sells crystals."},
	{"id": "town_lape", "name": "Lape's Reliquary", "kind": "service", "map": "sanctuary", "pos": Vector2(27.6, 15.6), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Lape the Ancient appraises up to three of your items and offers one of three special-crafted, licensed pieces for them, or gold."},
	{"id": "town_hero_vault", "name": "The Hero's Vault", "kind": "service", "map": "sanctuary", "pos": Vector2(28.0, 22.6), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Storage shared by all of your heroes, with a practice dummy beside it for trying your damage."},
	{"id": "town_fallen", "name": "Shrine of the Fallen", "kind": "service", "map": "sanctuary", "pos": Vector2(8.9, 28.8), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Veyra Ashgrave calls Tempos here, at the quiet end of the Merchant Quarter: the spirits of fallen warriors."},
	{"id": "town_netmender", "name": "Tessaly's house", "kind": "home", "map": "sanctuary", "pos": Vector2(-20.6, 2), "listed": true, "public": true,
		"door": "int_netmender", "levels": "Safe haven", "text": "The net-mender's house."},
	{"id": "town_cartographer", "name": "The Cartographer's House", "kind": "home", "map": "sanctuary", "pos": Vector2(20.6, 6), "listed": true, "public": true,
		"door": "int_cartographer", "levels": "Safe haven", "text": "Aurand Quell draws the four islands and never finishes."},
	{"id": "town_widow", "name": "The Hald House", "kind": "home", "map": "sanctuary", "pos": Vector2(-15, 19.5), "listed": true, "public": true,
		"door": "int_widow", "levels": "Safe haven", "text": "Home of Ilvena Hald."},
	{"id": "town_keeper", "name": "The Keeper's House", "kind": "home", "map": "sanctuary", "pos": Vector2(19.5, -12), "listed": true, "public": true,
		"door": "int_keeper", "levels": "Safe haven", "text": "Keeper Thadric Moll writes down what nobody alive has seen."},
	{"id": "town_refugee", "name": "Zerin's house", "kind": "home", "map": "sanctuary", "pos": Vector2(-17.7, -16.7), "listed": true, "public": true,
		"door": "int_refugee", "levels": "Safe haven", "text": "Zerin Ven fled Emberhal."},
	# --- Westreach: the district below the South Gate ---
	{"id": "wr_gate", "name": "South Gate road", "kind": "junction", "map": "westreach", "pos": Vector2(-112, 40), "listed": false, "public": true,
		"levels": "Level 1–4", "text": "Three roads leave the gate: to the mill, the fields and down the steps to the cove."},
	{"id": "wr_mill", "name": "Old Mill Crossroads", "kind": "junction", "map": "westreach", "pos": Vector2(0, 0), "listed": true, "public": true,
		"provisional": true, "levels": "Low danger", "text": "A watermill where four roads meet: Malasugue to the west, the Ruined Forest to the north, Lantern Fields to the south and the Lake Shore Road east to Olivar."},
	{"id": "wr_fields", "name": "Lantern Fields", "kind": "district", "map": "westreach", "pos": Vector2(35, 110), "listed": true, "public": true,
		"provisional": true, "levels": "Level 1–4", "text": "Working farms that feed Malasugue. Goblins have been stealing from the stores."},
	{"id": "wr_cove", "name": "Tideglass Cove", "kind": "shrine", "map": "westreach", "pos": Vector2(-178, 92), "listed": true, "public": true,
		"provisional": true, "shrine": "cove_shrine", "levels": "Level 1–3", "text": "The fishing beach below the western cliffs: piers, net racks and an old waypoint shrine."},
	{"id": "wr_cave", "name": "Saltmouth Cave", "kind": "landmark", "map": "westreach", "pos": Vector2(-190, 74), "listed": true, "public": false,
		"provisional": true, "levels": "Level 2–4", "text": "Smugglers use the sea cave. The missing shipment from the cove was last seen here."},
	{"id": "wr_lake_end", "name": "Lake Shore Road", "kind": "junction", "map": "westreach", "pos": Vector2(78, -9), "listed": false, "public": true,
		"provisional": true, "levels": "Low danger", "text": "Olivar's traders planked over the spring washout. The road runs on east along the lake to their town."},
	{"id": "wr_fen_exit", "name": "Fen Road", "kind": "junction", "map": "westreach", "pos": Vector2(78, 95), "listed": false, "public": true,
		"provisional": true, "levels": "Low danger", "text": "The Fen Road crosses the millstream on the Fen Bridge and runs east to Wyman Outpost."},
	{"id": "wr_forest_exit", "name": "Forest Road", "kind": "junction", "map": "westreach", "pos": Vector2(-54, -51), "listed": false, "public": true,
		"levels": "Level 1–4", "text": "The Forest Road climbs north toward the Ruined Forest."},
	# --- Olivar: the lake-trade town east of the mill (bh-007) ---
	{"id": "olv_town", "name": "Olivar", "kind": "town", "map": "olivar", "pos": Vector2(0, 4), "listed": true, "public": true,
		"levels": "Safe haven", "text": "A walled trading town on the south shore of Stillwater Lake. Its merchants sell advanced arms, jewels and draughts at a premium, and restock whenever heroes bring word of a cleared stage or a fallen champion."},
	{"id": "olv_west", "name": "Olivar West Gate", "kind": "junction", "map": "olivar", "pos": Vector2(-62, 12), "listed": false, "public": true,
		"levels": "Safe haven", "text": "Where the Lake Shore Road from the Old Mill reaches Olivar's palisade."},
	{"id": "olv_south", "name": "Olivar South Gate", "kind": "junction", "map": "olivar", "pos": Vector2(20, 56), "listed": false, "public": true,
		"levels": "Safe haven", "text": "The Watch Road leaves south for Wyman Outpost."},
	{"id": "olv_shrine", "name": "Olivar Lake Terrace", "kind": "shrine", "map": "olivar", "pos": Vector2(-22, -30), "listed": true, "public": true,
		"shrine": "olivar_shrine", "levels": "Safe haven", "text": "A waypoint on the terrace above the docks, where the lake mist rolls in each evening."},
	{"id": "olv_paul", "name": "The Lakeside Bench", "kind": "landmark", "map": "olivar", "pos": Vector2(24.6, -30.2), "listed": true, "public": true,
		"levels": "Safe haven", "text": "A bench above the water on the east shore, where an old swordsman sits most evenings: Paul David."},
	{"id": "olv_docks", "name": "Olivar Docks", "kind": "landmark", "map": "olivar", "pos": Vector2(4, -40), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Barges carry grain, timber and news across Stillwater Lake. Wren Talbot keeps the tally."},
	{"id": "olv_arms", "name": "Taicho's Arms Exchange", "kind": "service", "map": "olivar", "pos": Vector2(23, -2), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Taicho's warehouse and counting-house on the east side. His sales stand is on Market Row: advanced weapons and armor at a premium, with new stock after every cleared stage or champion."},
	{"id": "olv_row", "name": "Market Row", "kind": "service", "map": "olivar", "pos": Vector2(-5.2, 16.0), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The market south-west of the plaza: Crane's Fine Settings, Angkol Les' Apothecary, Taicho's Arms Exchange, Cray's Cutting Room (sockets and crystals), the Alchemy Table (Enchanting), the Workbench and the Forge (Fore-Tech)."},
	{"id": "olv_gemcutter", "name": "Cray's Cutting Room", "kind": "service", "map": "olivar", "pos": Vector2(-5.0, 28.4), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Anselm Cray, Socket Specialist: opens sockets in your gear, sets crystals, purges and crystallizes, and sells crystals."},
	{"id": "olv_hero_vault", "name": "Olivar Hero's Vault", "kind": "service", "map": "olivar", "pos": Vector2(-17.4, 29.2), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The Hero's Vault on the west green: storage shared by all of your heroes. A practice dummy stands to the north."},
	{"id": "olv_apothecary", "name": "Angkol Les' Apothecary", "kind": "service", "map": "olivar", "pos": Vector2(-9.4, 23.0), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Angkol Les's stand on Market Row, beside the alchemy table: herbs, draughts and recipe scrolls."},
	{"id": "olv_jeweller", "name": "Crane's Fine Settings", "kind": "service", "map": "olivar", "pos": Vector2(-11.4, 17.2), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Elsbeth Crane's stand on Market Row: rings, amulets and charms, none of them cheap."},
	# --- Wyman Outpost: the hero camp on the marsh edge (bh-007) ---
	{"id": "wy_camp", "name": "Wyman Outpost", "kind": "town", "map": "wyman_outpost", "pos": Vector2(0, 6), "listed": true, "public": true,
		"levels": "Safe haven", "text": "A hero camp on a rise above Reedwater Marsh. Rest at the bonfire to set your checkpoint, read the Hero Register, restock at the quartermaster and craft at the field forge, workbench and camp kettle."},
	{"id": "wy_north", "name": "Wyman North Gate", "kind": "junction", "map": "wyman_outpost", "pos": Vector2(8, -56), "listed": false, "public": true,
		"levels": "Safe haven", "text": "The Watch Road north to Olivar."},
	{"id": "wy_west", "name": "Wyman West Gate", "kind": "junction", "map": "wyman_outpost", "pos": Vector2(-60, 20), "listed": false, "public": true,
		"levels": "Safe haven", "text": "The Fen Road west to Lantern Fields."},
	{"id": "wy_shrine", "name": "Wyman Waypoint", "kind": "shrine", "map": "wyman_outpost", "pos": Vector2(-15.5, 12.5), "listed": true, "public": true,
		"shrine": "wyman_shrine", "levels": "Safe haven", "text": "The camp's waypoint. Heroes come and go through it at all hours."},
	{"id": "wy_register", "name": "Hero Register", "kind": "service", "map": "wyman_outpost", "pos": Vector2(-8, -6), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The board where every hero in camp signs in: level, tier and guild."},
	{"id": "wy_forge", "name": "Quartermaster Row", "kind": "service", "map": "wyman_outpost", "pos": Vector2(3.0, 20), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The camp's trade south of the bonfire: the quartermaster's tent, Greta Stonehand's field kit and field forge (Fore-Tech), Dagna Flint's crystal cart (sockets and crystals), the camp kettle (Enchanting) and the workbench."},
	{"id": "wy_prospector", "name": "Flint's Crystal Cart", "kind": "service", "map": "wyman_outpost", "pos": Vector2(8.4, 15.2), "listed": true, "public": true,
		"levels": "Safe haven", "text": "Dagna Flint, Socket Specialist: opens sockets in your gear, sets crystals, purges and crystallizes, and sells crystals."},
	{"id": "wy_hero_vault", "name": "Wyman Hero's Vault", "kind": "service", "map": "wyman_outpost", "pos": Vector2(14.4, 15.2), "listed": true, "public": true,
		"levels": "Safe haven", "text": "The Hero's Vault on the east side of the camp: storage shared by all of your heroes, with a practice dummy nearby."},
	{"id": "wy_marsh_gate", "name": "Marsh Gate", "kind": "junction", "map": "wyman_outpost", "pos": Vector2(36.0, 7.2), "listed": false, "public": true,
		"levels": "Safe haven", "text": "The east gate of the stockade, out over the reeds to the Weeping Causeway. Barred until Sir Aldric opens it."},
	{"id": "wy_overlook", "name": "Marsh Overlook", "kind": "landmark", "map": "wyman_outpost", "pos": Vector2(22, 0), "listed": true, "public": true,
		"levels": "Safe haven", "text": "A watch platform over Reedwater Marsh, where the heroes of the outpost keep a lamp lit all night."},
	# --- The Weeping Causeway (bh-021) ---
	{"id": "wc_arrival", "name": "Causeway West End", "kind": "junction", "map": "weeping_causeway", "pos": Vector2(-62, 0), "listed": false, "public": true,
		"levels": "Levels 5–7", "text": "Where the planks from Wyman's Marsh Gate meet the old stone causeway."},
	{"id": "wc_tollhouse", "name": "The Drowned Tollhouse", "kind": "landmark", "map": "weeping_causeway", "pos": Vector2(0, 0), "listed": true, "public": false,
		"levels": "Levels 5–7", "text": "A ruined toll-fort at the end of the Weeping Causeway. Three winters ago the Dawnbreakers were betrayed here. Kethrax holds it now."},
	# --- Ruined Forest ---
	{"id": "rf_glade", "name": "Ruined Forest", "kind": "shrine", "map": "ruined_forest", "pos": Vector2(-60, 10.875), "listed": true, "public": true,
		"shrine": "forest_waypoint", "levels": "Level 1–5", "text": "The waypoint glade at the forest's west end. The fallen village lies just beyond."},
	{"id": "rf_village", "name": "Burnt Village", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(-34, 6), "listed": true, "public": true,
		"levels": "Level 1–5", "text": "The village that fell three winters ago, and its graveyard."},
	{"id": "rf_south", "name": "Forest Road", "kind": "junction", "map": "ruined_forest", "pos": Vector2(-30, 46), "listed": false, "public": true,
		"levels": "Level 1–5", "text": "The Forest Road leaves the village south toward the Old Mill."},
	{"id": "rf_bridge", "name": "Ravine Bridge", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(0, 4), "listed": true, "public": true,
		"levels": "Level 1–5", "text": "The only crossing over the misty ravine."},
	{"id": "rf_fork", "name": "Camp fork", "kind": "junction", "map": "ruined_forest", "pos": Vector2(18, 0), "listed": false, "public": true,
		"levels": "Level 1–5", "text": ""},
	{"id": "rf_camp", "name": "Survivors' Camp", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(20, -10), "listed": true, "public": false,
		"levels": "Level 2–5", "text": "A fire that is still warm. The people who lit it are not friendly."},
	{"id": "rf_tower", "name": "Collapsed Watchtower", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(30, 17), "listed": true, "public": true,
		"levels": "Level 3–5", "text": "The landmark seen from the bridge. Orc scouts camp on its hill."},
	{"id": "rf_gate", "name": "Sunken Catacomb Gate", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(60, -3.3), "listed": true, "public": true,
		"levels": "Level 3–5", "text": "A corrupted grove around the arch that leads down into the Ancient Catacombs."},
	# --- bh-012: dungeon gates on the surface (the floors below are Underground places) ---
	{"id": "wr_warren", "name": "Hollowroot Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(68, 77), "listed": true, "public": true, "gate": "warren",
		"levels": "Level 5–11", "text": "Roots as thick as a man heave out of a sinkhole east of the Fen Road. Something glows down there."},
	{"id": "wr_deeps", "name": "Saltmouth Deeps Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-188.5, 70), "listed": true, "public": true, "gate": "deeps",
		"levels": "Level 7–13", "text": "A door at the back of the smugglers' sea cave, and a bell ringing somewhere under the sea."},
	{"id": "wr_ember", "name": "Emberforge Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(52, -22), "listed": true, "public": true, "gate": "ember",
		"levels": "Level 10–16", "text": "Smoke from a crack in the hill above the Lake Shore Road. The old forge-lords are working again."},
	{"id": "rf_barrow", "name": "Rimeglass Gate", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(-46, -31), "listed": true, "public": true, "gate": "barrow",
		"levels": "Level 13–20", "text": "Frost creeps down the north rim from a barrow door sealed with ice."},
	{"id": "wy_orrery", "name": "Orrery Gate", "kind": "landmark", "map": "wyman_outpost", "pos": Vector2(-28, -46), "listed": true, "public": true, "gate": "orrery",
		"levels": "Level 17–25", "text": "A brass door in the marsh bank north of the stockade. At night, stars move behind its windows."},
	{"id": "warren", "name": "Hollowroot Warren", "kind": "dungeon", "map": "dg_warren_1", "listed": true, "public": true, "anchor": "wr_warren",
		"levels": "Level 5–11", "text": "A fungal warren four floors deep. The Rot Mother waits at the bottom."},
	{"id": "deeps", "name": "Saltmouth Deeps", "kind": "dungeon", "map": "dg_deeps_1", "listed": true, "public": true, "anchor": "wr_deeps",
		"levels": "Level 7–13", "text": "A drowned vault under the sea cave. Ossric Vael, the Drowned Bell, keeps its lowest lock."},
	{"id": "ember", "name": "Emberforge Depths", "kind": "dungeon", "map": "dg_ember_1", "listed": true, "public": true, "anchor": "wr_ember",
		"levels": "Level 10–16", "text": "The forge-halls of the old smith-lords, and Brakka Durnhelm at the last anvil."},
	{"id": "barrow", "name": "Rimeglass Barrow", "kind": "dungeon", "map": "dg_barrow_1", "listed": true, "public": true, "anchor": "rf_barrow",
		"levels": "Level 13–20", "text": "The frozen barrow of the forest kings. Skaldra, the Winter Crown, holds its throne."},
	{"id": "orrery", "name": "The Shattered Orrery", "kind": "dungeon", "map": "dg_orrery_1", "listed": true, "public": true, "anchor": "wy_orrery",
		"levels": "Level 17–25", "text": "A ruined Aether observatory under the marsh. The Astrarch turns the broken stars."},
	# --- bh-013: fifteen more dungeon gates (known from the start) and the junctions where their trails leave the roads ---
	{"id": "rf_burrow_turn", "name": "Burrow turn-off", "kind": "junction", "map": "ruined_forest", "pos": Vector2(-31.1, 40.2), "listed": false, "public": true, "on_road": "rf_south_road",
		"levels": "", "text": ""},
	{"id": "wr_briar_turn", "name": "Briar turn-off", "kind": "junction", "map": "westreach", "pos": Vector2(21.0, 67.6), "listed": false, "public": true, "on_road": "wr_mill_lane",
		"levels": "", "text": ""},
	{"id": "olv_tomb_turn", "name": "Tomb stair turn", "kind": "junction", "map": "olivar", "pos": Vector2(-24.4, 7.6), "listed": false, "public": true, "on_road": "olv_west_road",
		"levels": "", "text": ""},
	{"id": "wr_crypt_fork", "name": "Crypt fork", "kind": "junction", "map": "westreach", "pos": Vector2(-38.8, -35.0), "listed": false, "public": true, "on_road": "wr_forest_road",
		"levels": "", "text": ""},
	{"id": "wr_geode_turn", "name": "Geode turn-off", "kind": "junction", "map": "westreach", "pos": Vector2(-108.8, 121.5), "listed": false, "public": true, "on_road": "wr_coast_road",
		"levels": "", "text": ""},
	{"id": "wr_wyrm_turn", "name": "Coil turn-off", "kind": "junction", "map": "westreach", "pos": Vector2(-134.8, 114.1), "listed": false, "public": true, "on_road": "wr_coast_road",
		"levels": "", "text": ""},
	{"id": "wr_cellars", "name": "Cutpurse Cellars Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-156, 51), "listed": true, "public": true, "gate": "cellars",
		"levels": "Level 2–4", "text": "A trapdoor under a collapsed farmhouse, and fresh cart tracks leading to it."},
	{"id": "cellars", "name": "Cutpurse Cellars", "kind": "dungeon", "map": "dg_cellars_1", "listed": true, "public": true, "anchor": "wr_cellars",
		"levels": "Level 2–4", "text": "A smugglers' cellar two floors deep. Rask Coinwhisper counts the stolen grain at the bottom."},
	{"id": "rf_burrows", "name": "Gnashgut Burrows Gate", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(-14, 37), "listed": true, "public": true, "gate": "burrows",
		"levels": "Level 4–7", "text": "A goblin hole east of the Forest Road, ringed with stolen pots."},
	{"id": "burrows", "name": "Gnashgut Burrows", "kind": "dungeon", "map": "dg_burrows_1", "listed": true, "public": true, "anchor": "rf_burrows",
		"levels": "Level 4–7", "text": "Goblin tunnels three floors deep. Gnashgut the Goblin King sits on a heap of loot."},
	{"id": "rf_ossuary", "name": "Blackvault Gate", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(58, 22), "listed": true, "public": true, "gate": "ossuary",
		"levels": "Level 6–10", "text": "A black door in the bank south of the grove, cold to the touch."},
	{"id": "ossuary", "name": "Blackvault Ossuary", "kind": "dungeon", "map": "dg_ossuary_1", "listed": true, "public": true, "anchor": "rf_ossuary",
		"levels": "Level 6–10", "text": "The Burnt Village's bone vault, three floors deep. Ossuarch Veyl rules the dead there."},
	{"id": "wr_warcamp", "name": "Ironjaw Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-72, -51), "listed": true, "public": true, "gate": "warcamp",
		"levels": "Level 9–13", "text": "A palisaded tunnel mouth beside the Forest Road, hung with orc banners."},
	{"id": "warcamp", "name": "Ironjaw Warcamp", "kind": "dungeon", "map": "dg_warcamp_1", "listed": true, "public": true, "anchor": "wr_warcamp",
		"levels": "Level 9–13", "text": "The warband's dug-out camp, three floors deep. Grukhar Ironjaw holds the war hall."},
	{"id": "wr_hive", "name": "Waxen Hive Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(33, -48), "listed": true, "public": true, "gate": "hive",
		"levels": "Level 12–16", "text": "Amber wax oozes out of a crack in the hill. The air hums."},
	{"id": "hive", "name": "The Waxen Hive", "kind": "dungeon", "map": "dg_hive_1", "listed": true, "public": true, "anchor": "wr_hive",
		"levels": "Level 12–16", "text": "A hive of giant wax-comb, three floors deep. Ambrexa, the Waxen Queen, broods at its heart."},
	{"id": "wr_sump", "name": "Blackwater Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(75, 111), "listed": true, "public": true, "gate": "sump",
		"levels": "Level 15–19", "text": "A drain-mouth below the Fen Road, breathing out marsh stink."},
	{"id": "sump", "name": "Blackwater Sump", "kind": "dungeon", "map": "dg_sump_1", "listed": true, "public": true, "anchor": "wr_sump",
		"levels": "Level 15–19", "text": "A sunken sump four floors deep. Grolmuck, the Sump Tyrant, wallows in the lowest cistern."},
	{"id": "wr_briar", "name": "Briarheart Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(36, 63), "listed": true, "public": true, "gate": "briar",
		"levels": "Level 18–22", "text": "A thicket of red thorns over an old cellar door off Mill Lane."},
	{"id": "briar", "name": "Briarheart Hollow", "kind": "dungeon", "map": "dg_briar_1", "listed": true, "public": true, "anchor": "wr_briar",
		"levels": "Level 18–22", "text": "A thorn-choked hollow four floors deep. Vyrelle of the Thousand Thorns grows at its heart."},
	{"id": "olv_dunemourn", "name": "Dunemourn Gate", "kind": "landmark", "map": "olivar", "pos": Vector2(-20, 25), "listed": true, "public": true, "gate": "dunemourn",
		"levels": "Level 21–25", "text": "A sunken stair between the market houses, half full of sand."},
	{"id": "dunemourn", "name": "Dunemourn Tomb", "kind": "dungeon", "map": "dg_dunemourn_1", "listed": true, "public": true, "anchor": "olv_dunemourn",
		"levels": "Level 21–25", "text": "A buried tomb four floors deep under Olivar. Ozrenith, the Buried Sovereign, still holds court."},
	{"id": "rf_thunderwell", "name": "Thunderwell Gate", "kind": "landmark", "map": "ruined_forest", "pos": Vector2(58, -23), "listed": true, "public": true, "gate": "thunderwell",
		"levels": "Level 24–28", "text": "A ring of copper rods on the grove's north bank, humming before every storm."},
	{"id": "thunderwell", "name": "Thunderwell Spire", "kind": "dungeon", "map": "dg_thunderwell_1", "listed": true, "public": true, "anchor": "rf_thunderwell",
		"levels": "Level 24–28", "text": "A lightning well four floors deep. Voltaric, Eye of the Storm, waits in the shaft."},
	{"id": "wr_undercroft", "name": "Undercroft Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-27, -45), "listed": true, "public": true, "gate": "undercroft",
		"levels": "Level 28–32", "text": "A stair beside the Forest Road that goes down further than the hill is tall."},
	{"id": "undercroft", "name": "The Umbral Undercroft", "kind": "dungeon", "map": "dg_undercroft_1", "listed": true, "public": true, "anchor": "wr_undercroft",
		"levels": "Level 28–32", "text": "A lightless undercroft four floors deep. Nyxarre, the Hollow Dark, speaks from the bottom."},
	{"id": "wr_geode", "name": "Prismdeep Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-105, 105), "listed": true, "public": true, "gate": "geode",
		"levels": "Level 32–36", "text": "A split in the cove cliff that glitters from the inside."},
	{"id": "geode", "name": "Prismdeep Geode", "kind": "dungeon", "map": "dg_geode_1", "listed": true, "public": true, "anchor": "wr_geode",
		"levels": "Level 32–36", "text": "A crystal geode four floors deep. The Prism Colossus stands in its lens chamber."},
	{"id": "olv_vault", "name": "Gilded Vault Gate", "kind": "landmark", "map": "olivar", "pos": Vector2(34, -14), "listed": true, "public": true, "gate": "vault",
		"levels": "Level 36–40", "text": "The old counting-house cellar door behind Taicho's. It is supposed to be bricked up."},
	{"id": "vault", "name": "The Gilded Vault", "kind": "dungeon", "map": "dg_vault_1", "listed": true, "public": true, "anchor": "olv_vault",
		"levels": "Level 36–40", "text": "A treasure vault four floors deep. Aurelax, the Hoard-Maw, lies on the gold."},
	{"id": "wr_reliquary", "name": "Twinspire Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-54, -24), "listed": true, "public": true, "gate": "reliquary",
		"levels": "Level 40–46", "text": "Two broken spires over a sealed door west of the Forest Road."},
	{"id": "reliquary", "name": "Twinspire Reliquary", "kind": "dungeon", "map": "dg_reliquary_1", "listed": true, "public": true, "anchor": "wr_reliquary",
		"levels": "Level 40–46", "text": "The twin regents' reliquary, five floors deep. Ardan, the Oathbound Regent, keeps the crypt."},
	{"id": "wr_wyrmcoil", "name": "Wyrmcoil Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(-138, 123), "listed": true, "public": true, "gate": "wyrmcoil",
		"levels": "Level 45–51", "text": "A round tunnel in the coast bank, big enough to ride a cart through."},
	{"id": "wyrmcoil", "name": "Wyrmcoil Caverns", "kind": "dungeon", "map": "dg_wyrmcoil_1", "listed": true, "public": true, "anchor": "wr_wyrmcoil",
		"levels": "Level 45–51", "text": "Coiling caverns five floors deep. Vorgrath, the Coiled Wyrm, sleeps at the bottom."},
	{"id": "wr_maw", "name": "Maw Beneath Gate", "kind": "landmark", "map": "westreach", "pos": Vector2(75, -42), "listed": true, "public": true, "gate": "maw",
		"levels": "Level 52–58", "text": "A hole beyond the Lake Shore Road that no rope has reached the bottom of."},
	{"id": "maw", "name": "The Maw Beneath", "kind": "dungeon", "map": "dg_maw_1", "listed": true, "public": true, "anchor": "wr_maw",
		"levels": "Level 52–58", "text": "The island's deepest dark, five floors down. Oblivore waits in the Maw."},
	# --- Underground and the temple sequence (no surface position; they anchor to their entrance) ---
	{"id": "catacombs", "name": "Ancient Catacombs", "kind": "dungeon", "map": "catacombs", "listed": true, "public": true, "anchor": "rf_gate",
		"levels": "Level 4–8", "text": "Beneath the drowned chapel. Entered through the sunken gate at the Ruined Forest's east end."},
	{"id": "temple", "name": "Forgotten Temple", "kind": "dungeon", "map": "forgotten_temple", "listed": true, "public": true, "atlas": Vector2(772, 206),
		"levels": "Level 7–10", "text": "Halls of the first oath, high in the eastern mountains. Reached through the Catacombs."},
	{"id": "throne", "name": "The Hollow Throne", "kind": "dungeon", "map": "boss_arena", "listed": true, "public": true, "anchor": "temple",
		"levels": "Level 10", "text": "Morthar waits beyond the temple's sealed door."},
]

## Enterable buildings: interior place id -> the interior map (added to PLACES at load; distance inside is not counted).
const INTERIORS := {
	"int_tavern": "The Salted Marlin", "int_guildhouse": "The Guild House", "int_swordfin": "Swordfin Hall", "int_lantern": "Lantern House",
	"int_netmender": "The Net-mender's House", "int_cartographer": "The Cartographer's House", "int_widow": "The Hald House",
	"int_keeper": "The Keeper's House", "int_refugee": "The Refugee's House",
}

## Walkable roads. `points` run from `a` to `b` in the map's local XZ metres and must start/end on those places.
## type: road (maintained, 5-7 m) or trail (2.5-3.5 m). Road names repeat across maps where one road crosses a boundary.
const ROADS := [
	# Malasugue streets
	{"id": "tn_gate_street", "name": "Gate Street", "type": "road", "map": "sanctuary", "a": "town", "b": "town_gate",
		"points": [Vector2(0, 10.5), Vector2(0, 14), Vector2(0, 38)]},
	{"id": "tn_terrace_stair", "name": "Terrace Stair", "type": "road", "map": "sanctuary", "a": "town", "b": "town_terrace",
		"points": [Vector2(0, 10.5), Vector2(-6.5, 6.5), Vector2(-5.5, -2.5), Vector2(0, -8), Vector2(0, -20)]},
	{"id": "tn_tavern", "name": "Harbor Lane", "type": "road", "map": "sanctuary", "a": "town", "b": "town_tavern",
		"points": [Vector2(0, 10.5), Vector2(-9.5, 13.8), Vector2(-23.5, 13.5)]},
	{"id": "tn_swordfin", "name": "Hall Lane", "type": "road", "map": "sanctuary", "a": "town", "b": "town_swordfin",
		"points": [Vector2(0, 10.5), Vector2(7, 6.5), Vector2(13, -0.5), Vector2(26.4, -4.8)]},
	{"id": "tn_lantern", "name": "Covenant Lane", "type": "road", "map": "sanctuary", "a": "town", "b": "town_lantern",
		"points": [Vector2(0, 10.5), Vector2(-6.5, 6.5), Vector2(-12, -3), Vector2(-24.9, -9.5)]},
	{"id": "tn_guildhouse", "name": "Guild Row", "type": "road", "map": "sanctuary", "a": "town", "b": "town_guildhouse",
		"points": [Vector2(0, 10.5), Vector2(-6.5, 6.5), Vector2(-9, 0), Vector2(-11, -4.4)]},
	{"id": "tn_market", "name": "Market Lane", "type": "road", "map": "sanctuary", "a": "town", "b": "town_market",
		"points": [Vector2(0, 10.5), Vector2(8, 11.6), Vector2(12.5, 16.5), Vector2(15.0, 21.0)]},
	{"id": "tn_forge", "name": "Forge Yard", "type": "road", "map": "sanctuary", "a": "town_market", "b": "town_forge",
		"points": [Vector2(15.0, 21.0), Vector2(17.4, 22.2), Vector2(21.2, 22.4)]},
	{"id": "tn_fallen", "name": "Shrine Walk", "type": "road", "map": "sanctuary", "a": "town", "b": "town_fallen",
		"points": [Vector2(0, 10.5), Vector2(8, 11.6), Vector2(12.5, 16.5), Vector2(12.4, 26.0), Vector2(8.9, 28.8)]},
	{"id": "tn_netmender", "name": "West Row", "type": "trail", "map": "sanctuary", "a": "town", "b": "town_netmender",
		"points": [Vector2(0, 10.5), Vector2(-7.5, 5.5), Vector2(-20.6, 2)]},
	{"id": "tn_cartographer", "name": "East Row", "type": "trail", "map": "sanctuary", "a": "town", "b": "town_cartographer",
		"points": [Vector2(0, 10.5), Vector2(7.5, 6.5), Vector2(20.6, 6)]},
	{"id": "tn_widow", "name": "Widow's Lane", "type": "trail", "map": "sanctuary", "a": "town", "b": "town_widow",
		"points": [Vector2(0, 10.5), Vector2(-15, 19.5)]},
	{"id": "tn_keeper", "name": "Keeper's Lane", "type": "trail", "map": "sanctuary", "a": "town", "b": "town_keeper",
		"points": [Vector2(0, 10.5), Vector2(7, 6.5), Vector2(13, -0.5), Vector2(19.5, -12)]},
	{"id": "tn_refugee", "name": "North Row", "type": "trail", "map": "sanctuary", "a": "town", "b": "town_refugee",
		"points": [Vector2(0, 10.5), Vector2(-6.5, 6.5), Vector2(-5.5, -2.5), Vector2(-17.7, -16.7)]},
	# Westreach
	{"id": "wr_mill_road", "name": "Mill Road", "type": "road", "map": "westreach", "a": "wr_gate", "b": "wr_mill",
		"points": [Vector2(-112, 40), Vector2(-100, 48), Vector2(-80, 50), Vector2(-62, 44), Vector2(-44, 30), Vector2(-28, 16), Vector2(-12, 6), Vector2(0, 0)]},
	{"id": "wr_forest_road", "name": "Forest Road", "type": "road", "map": "westreach", "a": "wr_mill", "b": "wr_forest_exit",
		"points": [Vector2(0, 0), Vector2(-10, -10), Vector2(-24, -22), Vector2(-38, -34), Vector2(-54, -51)]},
	{"id": "wr_mill_lane", "name": "Mill Lane", "type": "road", "map": "westreach", "a": "wr_mill", "b": "wr_fields",
		"points": [Vector2(0, 0), Vector2(4, 16), Vector2(10, 36), Vector2(18, 58), Vector2(26, 84), Vector2(35, 110)]},
	{"id": "wr_field_road", "name": "Field Road", "type": "road", "map": "westreach", "a": "wr_gate", "b": "wr_fields",
		"points": [Vector2(-112, 40), Vector2(-102, 58), Vector2(-84, 72), Vector2(-60, 78), Vector2(-38, 78), Vector2(-16, 86), Vector2(8, 98), Vector2(35, 110)]},
	{"id": "wr_coast_road", "name": "Coast Road", "type": "road", "map": "westreach", "a": "wr_cove", "b": "wr_fields",
		"points": [Vector2(-178, 92), Vector2(-164, 100), Vector2(-146, 110), Vector2(-124, 118), Vector2(-98, 124), Vector2(-70, 126),
			Vector2(-42, 126), Vector2(-14, 122), Vector2(12, 116), Vector2(35, 110)]},
	{"id": "wr_cove_steps", "name": "Cove Steps", "type": "trail", "map": "westreach", "a": "wr_gate", "b": "wr_cove",
		"points": [Vector2(-112, 40), Vector2(-122, 50), Vector2(-140, 54), Vector2(-152, 60), Vector2(-140, 69), Vector2(-152, 79), Vector2(-166, 86), Vector2(-178, 92)]},
	{"id": "wr_lake_road", "name": "Lake Shore Road", "type": "road", "map": "westreach", "a": "wr_mill", "b": "wr_lake_end",
		"points": [Vector2(0, 0), Vector2(12, 1), Vector2(20, 2), Vector2(30, 1), Vector2(44, -3), Vector2(56, -8), Vector2(66, -10), Vector2(78, -9)]},
	{"id": "wr_fen_road", "name": "Fen Road", "type": "road", "map": "westreach", "a": "wr_fields", "b": "wr_fen_exit",
		"points": [Vector2(35, 110), Vector2(44, 105), Vector2(52, 99), Vector2(59, 97), Vector2(66, 96), Vector2(78, 95)]},
	{"id": "wr_cave_path", "name": "Cave path", "type": "trail", "map": "westreach", "a": "wr_cove", "b": "wr_cave",
		"points": [Vector2(-178, 92), Vector2(-186, 84), Vector2(-190, 74)]},
	# Olivar
	{"id": "olv_west_road", "name": "Lake Shore Road", "type": "road", "map": "olivar", "a": "olv_west", "b": "olv_town",
		"points": [Vector2(-62, 12), Vector2(-48, 12), Vector2(-34, 10), Vector2(-18, 6), Vector2(0, 4)]},
	{"id": "olv_south_road", "name": "Watch Road", "type": "road", "map": "olivar", "a": "olv_town", "b": "olv_south",
		"points": [Vector2(0, 4), Vector2(8, 12), Vector2(15, 24), Vector2(19, 38), Vector2(20, 56)]},
	{"id": "olv_lake_path", "name": "Lakeside path", "type": "trail", "map": "olivar", "a": "olv_town", "b": "olv_paul",
		"points": [Vector2(0, 4), Vector2(1, -8), Vector2(2, -24), Vector2(12, -27.5), Vector2(24.6, -30.2)]},
	{"id": "olv_dock_walk", "name": "Dock Walk", "type": "road", "map": "olivar", "a": "olv_town", "b": "olv_docks",
		"points": [Vector2(0, 4), Vector2(1, -8), Vector2(2, -24), Vector2(4, -40)]},
	{"id": "olv_terrace_steps", "name": "Terrace Steps", "type": "trail", "map": "olivar", "a": "olv_town", "b": "olv_shrine",
		"points": [Vector2(0, 4), Vector2(-6, -6), Vector2(-15, -19), Vector2(-22, -30)]},
	{"id": "olv_exchange_row", "name": "Exchange Row", "type": "road", "map": "olivar", "a": "olv_town", "b": "olv_arms",
		"points": [Vector2(0, 4), Vector2(12, 1), Vector2(23, -2)]},
	{"id": "olv_row_road", "name": "Market Row", "type": "road", "map": "olivar", "a": "olv_town", "b": "olv_row",
		"points": [Vector2(0, 4), Vector2(-3, 10), Vector2(-5.2, 16.0)]},
	{"id": "olv_apothecary_lane", "name": "Apothecary Lane", "type": "trail", "map": "olivar", "a": "olv_town", "b": "olv_apothecary",
		"points": [Vector2(0, 4), Vector2(-6, 12), Vector2(-9.4, 23.0)]},
	{"id": "olv_market_row", "name": "Market Row", "type": "trail", "map": "olivar", "a": "olv_town", "b": "olv_jeweller",
		"points": [Vector2(0, 4), Vector2(-6, 12), Vector2(-11.4, 17.2)]},
	# Wyman Outpost
	{"id": "wy_north_road", "name": "Watch Road", "type": "road", "map": "wyman_outpost", "a": "wy_north", "b": "wy_camp",
		"points": [Vector2(8, -56), Vector2(7, -44), Vector2(5, -31), Vector2(4, -18), Vector2(6, -8), Vector2(4, 2), Vector2(0, 6)]},
	{"id": "wy_west_road", "name": "Fen Road", "type": "road", "map": "wyman_outpost", "a": "wy_west", "b": "wy_camp",
		"points": [Vector2(-60, 20), Vector2(-46, 17), Vector2(-31, 12), Vector2(-16, 8), Vector2(0, 6)]},
	{"id": "wy_shrine_path", "name": "Shrine path", "type": "trail", "map": "wyman_outpost", "a": "wy_camp", "b": "wy_shrine",
		"points": [Vector2(0, 6), Vector2(-8, 10), Vector2(-15.5, 12.5)]},
	{"id": "wy_register_path", "name": "Register path", "type": "trail", "map": "wyman_outpost", "a": "wy_camp", "b": "wy_register",
		"points": [Vector2(0, 6), Vector2(-5, 1), Vector2(-8, -6)]},
	{"id": "wy_forge_path", "name": "Forge path", "type": "trail", "map": "wyman_outpost", "a": "wy_camp", "b": "wy_forge",
		"points": [Vector2(0, 6), Vector2(3.5, 12.0), Vector2(3.0, 20.0)]},
	{"id": "wy_marsh_road", "name": "Marsh Gate path", "type": "trail", "map": "wyman_outpost", "a": "wy_marsh_gate", "b": "wy_camp",
		"points": [Vector2(36.0, 7.2), Vector2(30.5, 7.0), Vector2(24.0, 5.5), Vector2(18.0, 3.5), Vector2(8.0, 3.0), Vector2(0, 6)]},
	{"id": "wc_causeway_road", "name": "The Weeping Causeway", "type": "road", "map": "weeping_causeway", "a": "wc_arrival", "b": "wc_tollhouse",
		"points": [Vector2(-62, 0), Vector2(-40, 0), Vector2(-16, 0), Vector2(0, 0)]},
	{"id": "wy_overlook_path", "name": "Overlook path", "type": "trail", "map": "wyman_outpost", "a": "wy_camp", "b": "wy_overlook",
		"points": [Vector2(0, 6), Vector2(10, 3), Vector2(22, 0)]},
	# bh-012: trails to the dungeon gates
	{"id": "wr_warren_trail", "name": "Rootway trail", "type": "trail", "map": "westreach", "a": "wr_fen_exit", "b": "wr_warren",
		"points": [Vector2(78, 95), Vector2(74, 88), Vector2(70, 82), Vector2(68, 77)]},
	{"id": "wr_deeps_trail", "name": "Cave mouth", "type": "trail", "map": "westreach", "a": "wr_cave", "b": "wr_deeps",
		"points": [Vector2(-190, 74), Vector2(-188.5, 70)]},
	{"id": "wr_ember_trail", "name": "Smoke trail", "type": "trail", "map": "westreach", "a": "wr_lake_end", "b": "wr_ember",
		"points": [Vector2(78, -9), Vector2(70, -14), Vector2(61, -18), Vector2(52, -22)]},
	{"id": "rf_barrow_path", "name": "Rime path", "type": "trail", "map": "ruined_forest", "a": "rf_village", "b": "rf_barrow",
		"points": [Vector2(-34, 6), Vector2(-37, -6), Vector2(-42, -18), Vector2(-46, -31)]},
	{"id": "wy_orrery_path", "name": "Brass path", "type": "trail", "map": "wyman_outpost", "a": "wy_north", "b": "wy_orrery",
		"points": [Vector2(8, -56), Vector2(-4, -54), Vector2(-16, -50), Vector2(-28, -46)]},
	# bh-013: trails to the fifteen new gates
	{"id": "cellars_trail", "name": "Farmhouse track", "type": "trail", "map": "westreach", "a": "wr_gate", "b": "wr_cellars",
		"points": [Vector2(-112, 40), Vector2(-134, 46), Vector2(-156, 51)]},
	{"id": "burrows_trail", "name": "Burrow path", "type": "trail", "map": "ruined_forest", "a": "rf_burrow_turn", "b": "rf_burrows",
		"points": [Vector2(-31.1, 40.2), Vector2(-22, 39), Vector2(-14, 37)]},
	{"id": "ossuary_trail", "name": "Bone path", "type": "trail", "map": "ruined_forest", "a": "rf_gate", "b": "rf_ossuary",
		"points": [Vector2(60, -3.3), Vector2(59, 9), Vector2(58, 22)]},
	{"id": "warcamp_trail", "name": "Warband track", "type": "trail", "map": "westreach", "a": "wr_forest_exit", "b": "wr_warcamp",
		"points": [Vector2(-54, -51), Vector2(-63, -52), Vector2(-72, -51)]},
	{"id": "hive_trail", "name": "Humming trail", "type": "trail", "map": "westreach", "a": "wr_mill", "b": "wr_hive",
		"points": [Vector2(0, 0), Vector2(9, -15), Vector2(9, -25), Vector2(18, -36), Vector2(27, -44), Vector2(33, -48)]},
	{"id": "sump_trail", "name": "Drain path", "type": "trail", "map": "westreach", "a": "wr_fen_exit", "b": "wr_sump",
		"points": [Vector2(78, 95), Vector2(76, 103), Vector2(75, 111)]},
	{"id": "briar_trail", "name": "Thorn path", "type": "trail", "map": "westreach", "a": "wr_briar_turn", "b": "wr_briar",
		"points": [Vector2(21.0, 67.6), Vector2(29, 65), Vector2(36, 63)]},
	{"id": "dunemourn_trail", "name": "Sunken stair", "type": "trail", "map": "olivar", "a": "olv_tomb_turn", "b": "olv_dunemourn",
		"points": [Vector2(-24.4, 7.6), Vector2(-22, 16), Vector2(-20, 25)]},
	{"id": "thunderwell_trail", "name": "Copper path", "type": "trail", "map": "ruined_forest", "a": "rf_gate", "b": "rf_thunderwell",
		"points": [Vector2(60, -3.3), Vector2(59, -13), Vector2(58, -23)]},
	{"id": "undercroft_trail", "name": "Lightless stair", "type": "trail", "map": "westreach", "a": "wr_crypt_fork", "b": "wr_undercroft",
		"points": [Vector2(-38.8, -35.0), Vector2(-33, -40), Vector2(-27, -45)]},
	{"id": "geode_trail", "name": "Glitter path", "type": "trail", "map": "westreach", "a": "wr_geode_turn", "b": "wr_geode",
		"points": [Vector2(-108.8, 121.5), Vector2(-106, 113), Vector2(-105, 105)]},
	{"id": "vault_trail", "name": "Counting-house yard", "type": "trail", "map": "olivar", "a": "olv_arms", "b": "olv_vault",
		"points": [Vector2(23, -2), Vector2(29, -8), Vector2(34, -14)]},
	{"id": "reliquary_trail", "name": "Spire path", "type": "trail", "map": "westreach", "a": "wr_crypt_fork", "b": "wr_reliquary",
		"points": [Vector2(-38.8, -35.0), Vector2(-47, -30), Vector2(-54, -24)]},
	{"id": "wyrmcoil_trail", "name": "Coil path", "type": "trail", "map": "westreach", "a": "wr_wyrm_turn", "b": "wr_wyrmcoil",
		"points": [Vector2(-134.8, 114.1), Vector2(-136, 117), Vector2(-138, 123)]},
	{"id": "maw_trail", "name": "Edge path", "type": "trail", "map": "westreach", "a": "wr_lake_end", "b": "wr_maw",
		"points": [Vector2(78, -9), Vector2(78, -25), Vector2(75, -42)]},
	# Ruined Forest
	{"id": "rf_village_road", "name": "Village Road", "type": "road", "map": "ruined_forest", "a": "rf_glade", "b": "rf_village",
		"points": [Vector2(-60, 10.875), Vector2(-50, 9), Vector2(-34, 6)]},
	{"id": "rf_south_road", "name": "Forest Road", "type": "road", "map": "ruined_forest", "a": "rf_village", "b": "rf_south",
		"points": [Vector2(-34, 6), Vector2(-33.5, 15), Vector2(-33, 26.5), Vector2(-31.5, 38), Vector2(-30, 46)]},
	{"id": "rf_bridge_road", "name": "Bridge Road", "type": "road", "map": "ruined_forest", "a": "rf_village", "b": "rf_bridge",
		"points": [Vector2(-34, 6), Vector2(-18, 5), Vector2(-7.5, 4), Vector2(0, 4)]},
	{"id": "rf_east_road", "name": "Bridge Road", "type": "road", "map": "ruined_forest", "a": "rf_bridge", "b": "rf_fork",
		"points": [Vector2(0, 4), Vector2(7.5, 4), Vector2(18, 0)]},
	{"id": "rf_camp_path", "name": "Camp path", "type": "trail", "map": "ruined_forest", "a": "rf_fork", "b": "rf_camp",
		"points": [Vector2(18, 0), Vector2(20, -1), Vector2(20, -10)]},
	{"id": "rf_tower_path", "name": "Watchtower path", "type": "trail", "map": "ruined_forest", "a": "rf_fork", "b": "rf_tower",
		"points": [Vector2(18, 0), Vector2(24, -2), Vector2(27, 8), Vector2(30, 17)]},
	{"id": "rf_grove_road", "name": "Grove Road", "type": "road", "map": "ruined_forest", "a": "rf_fork", "b": "rf_gate",
		"points": [Vector2(18, 0), Vector2(30, -4), Vector2(44, -4), Vector2(57, -3), Vector2(60, -3.3)]},
]

## Transitions between places that are not walked on a road. mode: boundary (walk-through map exit, no distance),
## door (building), shrine (waypoint teleporter), dungeon (a dungeon gate; the distance inside is not counted).
## `flag` must be set on the hero for the link to be usable; `why` explains the lock. `oneway` links only go a -> b.
## `legacy` marks the original paired waypoint that works before any shrine is awakened.
const LINKS := [
	{"id": "south_gate", "mode": "boundary", "a": "town_gate", "b": "wr_gate", "flag": "south_gate_open",
		"why": "The South Gate is barred. Ask Captain Hald about the road.", "text": "Leave Malasugue through the South Gate", "back": "Enter Malasugue through the South Gate"},
	{"id": "forest_road_boundary", "mode": "boundary", "a": "wr_forest_exit", "b": "rf_south",
		"text": "Follow the Forest Road into the Ruined Forest", "back": "Follow the Forest Road down to Westreach"},
	{"id": "lake_road_boundary", "mode": "boundary", "a": "wr_lake_end", "b": "olv_west",
		"text": "Follow the Lake Shore Road east to Olivar", "back": "Follow the Lake Shore Road west to the Old Mill"},
	{"id": "watch_road_boundary", "mode": "boundary", "a": "olv_south", "b": "wy_north",
		"text": "Take the Watch Road south to Wyman Outpost", "back": "Take the Watch Road north to Olivar"},
	{"id": "fen_road_boundary", "mode": "boundary", "a": "wr_fen_exit", "b": "wy_west",
		"text": "Follow the Fen Road east to Wyman Outpost", "back": "Follow the Fen Road west to Lantern Fields"},
	{"id": "marsh_gate_boundary", "mode": "boundary", "a": "wy_marsh_gate", "b": "wc_arrival", "flag": "mq_marsh_gate_open",
		"why": "The Marsh Gate is barred. Sir Aldric Vane holds the key.", "text": "Cross the Marsh Gate onto the Weeping Causeway",
		"back": "Follow the causeway back to Wyman Outpost"},
	{"id": "waypoint_town_forest", "mode": "shrine", "a": "town_terrace", "b": "rf_glade", "legacy": true},
	{"id": "warren_gate", "mode": "dungeon", "a": "wr_warren", "b": "warren", "text": "Take the gate down into the Hollowroot Warren", "back": "Climb out of the Warren"},
	{"id": "deeps_gate", "mode": "dungeon", "a": "wr_deeps", "b": "deeps", "text": "Take the gate down into the Saltmouth Deeps", "back": "Climb out of the Deeps"},
	{"id": "ember_gate", "mode": "dungeon", "a": "wr_ember", "b": "ember", "text": "Take the gate down into the Emberforge Depths", "back": "Climb out of the Depths"},
	{"id": "barrow_gate", "mode": "dungeon", "a": "rf_barrow", "b": "barrow", "text": "Take the gate down into the Rimeglass Barrow", "back": "Climb out of the Barrow"},
	{"id": "orrery_gate", "mode": "dungeon", "a": "wy_orrery", "b": "orrery", "text": "Take the gate down into the Shattered Orrery", "back": "Climb out of the Orrery"},
	{"id": "cellars_gate", "mode": "dungeon", "a": "wr_cellars", "b": "cellars", "text": "Take the gate down into the Cutpurse Cellars", "back": "Climb out of the Cutpurse Cellars"},
	{"id": "burrows_gate", "mode": "dungeon", "a": "rf_burrows", "b": "burrows", "text": "Take the gate down into the Gnashgut Burrows", "back": "Climb out of the Gnashgut Burrows"},
	{"id": "ossuary_gate", "mode": "dungeon", "a": "rf_ossuary", "b": "ossuary", "text": "Take the gate down into the Blackvault Ossuary", "back": "Climb out of the Blackvault Ossuary"},
	{"id": "warcamp_gate", "mode": "dungeon", "a": "wr_warcamp", "b": "warcamp", "text": "Take the gate down into the Ironjaw Warcamp", "back": "Climb out of the Ironjaw Warcamp"},
	{"id": "hive_gate", "mode": "dungeon", "a": "wr_hive", "b": "hive", "text": "Take the gate down into the Waxen Hive", "back": "Climb out of the Waxen Hive"},
	{"id": "sump_gate", "mode": "dungeon", "a": "wr_sump", "b": "sump", "text": "Take the gate down into the Blackwater Sump", "back": "Climb out of the Blackwater Sump"},
	{"id": "briar_gate", "mode": "dungeon", "a": "wr_briar", "b": "briar", "text": "Take the gate down into the Briarheart Hollow", "back": "Climb out of the Briarheart Hollow"},
	{"id": "dunemourn_gate", "mode": "dungeon", "a": "olv_dunemourn", "b": "dunemourn", "text": "Take the gate down into the Dunemourn Tomb", "back": "Climb out of the Dunemourn Tomb"},
	{"id": "thunderwell_gate", "mode": "dungeon", "a": "rf_thunderwell", "b": "thunderwell", "text": "Take the gate down into the Thunderwell Spire", "back": "Climb out of the Thunderwell Spire"},
	{"id": "undercroft_gate", "mode": "dungeon", "a": "wr_undercroft", "b": "undercroft", "text": "Take the gate down into the Umbral Undercroft", "back": "Climb out of the Umbral Undercroft"},
	{"id": "geode_gate", "mode": "dungeon", "a": "wr_geode", "b": "geode", "text": "Take the gate down into the Prismdeep Geode", "back": "Climb out of the Prismdeep Geode"},
	{"id": "vault_gate", "mode": "dungeon", "a": "olv_vault", "b": "vault", "text": "Take the gate down into the Gilded Vault", "back": "Climb out of the Gilded Vault"},
	{"id": "reliquary_gate", "mode": "dungeon", "a": "wr_reliquary", "b": "reliquary", "text": "Take the gate down into the Twinspire Reliquary", "back": "Climb out of the Twinspire Reliquary"},
	{"id": "wyrmcoil_gate", "mode": "dungeon", "a": "wr_wyrmcoil", "b": "wyrmcoil", "text": "Take the gate down into the Wyrmcoil Caverns", "back": "Climb out of the Wyrmcoil Caverns"},
	{"id": "maw_gate", "mode": "dungeon", "a": "wr_maw", "b": "maw", "text": "Take the gate down into the Maw Beneath", "back": "Climb out of the Maw Beneath"},
	{"id": "catacomb_gate", "mode": "dungeon", "a": "rf_gate", "b": "catacombs", "text": "Take the gate down into the Ancient Catacombs",
		"back": "Climb out of the Catacombs to the Ruined Forest"},
	{"id": "catacombs_to_temple", "mode": "dungeon", "a": "catacombs", "b": "temple", "flag": "catacombs_ritual_seen", "oneway": true,
		"why": "The way to the temple opens once you find the ritual chamber in the Catacombs.", "text": "Cross the Catacombs to the temple waypoint"},
	{"id": "temple_to_catacombs", "mode": "dungeon", "a": "temple", "b": "catacombs", "oneway": true, "text": "Take the waypoint back down to the Catacombs"},
	{"id": "temple_seal", "mode": "dungeon", "a": "temple", "b": "throne", "flag": "temple_seal_broken", "oneway": true,
		"why": "Break the seal on the temple sanctum before entering.", "text": "Go through the throne gate in the temple sanctum"},
	{"id": "throne_return", "mode": "dungeon", "a": "throne", "b": "town_terrace", "flag": "boss_warden_defeated", "oneway": true,
		"why": "The return waypoint wakes when the Hollow Warden falls.", "text": "Take the return waypoint to Malasugue"},
]

## Waypoint shrines that form the travel network: any awakened one can reach any other awakened one. Each lands on a
## named spawn beside its dais. (The temple/catacomb/arena daises are paired dungeon gates, not part of the network.)
const NETWORK := {
	&"sanctuary_waypoint": {"map": &"sanctuary", "spawn": &"waypoint", "place": "town_terrace", "name": "Malasugue Town"},
	&"forest_waypoint": {"map": &"ruined_forest", "spawn": &"arrival", "place": "rf_glade", "name": "Ruined Forest"},
	&"cove_shrine": {"map": &"westreach", "spawn": &"cove_shrine", "place": "wr_cove", "name": "Tideglass Cove"},
	&"olivar_shrine": {"map": &"olivar", "spawn": &"olivar_shrine", "place": "olv_shrine", "name": "Olivar"},
	&"wyman_shrine": {"map": &"wyman_outpost", "spawn": &"wyman_shrine", "place": "wy_shrine", "name": "Wyman Outpost"},
}
const NETWORK_SHRINES := [&"sanctuary_waypoint", &"forest_waypoint", &"cove_shrine", &"olivar_shrine", &"wyman_shrine"]

# ------------------------------------------------------------------------------------------------------------

static func road(id: String) -> Dictionary:
	for r in ROADS:
		if r.id == id:
			return r
	return {}

static func roads_on(map_id: StringName) -> Array:
	return ROADS.filter(func(r): return StringName(r.map) == map_id)

static func place(id: String) -> Dictionary:
	for p in PLACES:
		if p.id == id:
			return p
	if INTERIORS.has(id):
		return interior_place(id)
	return {}

static func interior_place(id: String) -> Dictionary:
	var outside := ""
	for p in PLACES:
		if p.get("door", "") == id:
			outside = p.id
	return {"id": id, "name": INTERIORS[id], "kind": "interior", "map": id, "listed": false, "public": true, "anchor": outside,
		"levels": "Safe haven", "text": ""}

## Every place including building interiors.
static func all_places() -> Array:
	var out := PLACES.duplicate()
	for id in INTERIORS:
		out.append(interior_place(id))
	return out

## Door links between each enterable building and its interior.
static func door_links() -> Array:
	var out := []
	for p in PLACES:
		if p.has("door"):
			out.append({"id": "door_%s" % p.door, "mode": "door", "a": p.id, "b": p.door,
				"text": "Enter %s" % INTERIORS[p.door], "back": "Leave %s" % INTERIORS[p.door]})
	return out

static func all_links() -> Array:
	return LINKS + door_links()

## Local XZ -> atlas px for a surface map (null-safe: unknown maps return the atlas centre).
static func to_atlas(map_id: StringName, local: Vector2) -> Vector2:
	if MAP_ORIGIN.has(map_id):
		return MAP_ORIGIN[map_id] + local / PX_M
	return ATLAS_SIZE * 0.5

static func from_atlas(map_id: StringName, atlas: Vector2) -> Vector2:
	return (atlas - MAP_ORIGIN.get(map_id, Vector2.ZERO)) * PX_M

## Where a place draws on the atlas: its surface position, its explicit atlas point, or its anchor's.
static func place_atlas(p: Dictionary) -> Vector2:
	if p.has("atlas"):
		return p.atlas
	if p.has("pos") and MAP_ORIGIN.has(StringName(p.map)):
		return to_atlas(StringName(p.map), p.pos)
	if p.has("anchor") and p.anchor != "":
		return place_atlas(place(p.anchor))
	return ATLAS_SIZE * 0.5

static func polyline_length(pts: Array) -> float:
	var d := 0.0
	for i in pts.size() - 1:
		d += (pts[i] as Vector2).distance_to(pts[i + 1])
	return d

## Distance from p to a polyline, the closest point and the distance along the polyline to it.
static func project(p: Vector2, pts: Array) -> Dictionary:
	var best := {"dist": INF, "point": Vector2.ZERO, "along": 0.0, "seg": 0}
	var run := 0.0
	for i in pts.size() - 1:
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var ab := b - a
		var l2 := ab.length_squared()
		var t := 0.0 if l2 < 0.0001 else clampf((p - a).dot(ab) / l2, 0.0, 1.0)
		var q := a + ab * t
		var d := p.distance_to(q)
		if d < best.dist:
			best = {"dist": d, "point": q, "along": run + sqrt(l2) * t, "seg": i}
		run += sqrt(l2)
	return best

## The part of a polyline between two distances along it (in that order; `from` may exceed `to` to walk it backwards).
static func slice(pts: Array, from: float, to: float) -> Array:
	var rev := from > to
	var src := pts.duplicate()
	var total := polyline_length(src)
	if rev:
		src.reverse()
		from = total - from
		to = total - to
	var out := [point_at(src, from)]
	var run := 0.0
	for i in src.size() - 1:
		var seg := (src[i] as Vector2).distance_to(src[i + 1])
		run += seg
		if run > from + 0.01 and run < to - 0.01:
			out.append(src[i + 1])
	out.append(point_at(src, to))
	return out

static func point_at(pts: Array, along: float) -> Vector2:
	var run := 0.0
	for i in pts.size() - 1:
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		var seg := a.distance_to(b)
		if run + seg >= along:
			return a.lerp(b, clampf((along - run) / maxf(seg, 0.0001), 0.0, 1.0))
		run += seg
	return pts[pts.size() - 1]
