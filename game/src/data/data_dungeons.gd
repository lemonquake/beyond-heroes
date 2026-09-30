class_name DataDungeons
## Dungeons (bh-012): five themed underground raids, four floors each, built by one shared builder
## (src/world/maps/dungeon.gd) from the floor plans below. Every floor is its own map `dg_<dungeon>_<n>`.
## bh-013: fifteen more (DataDungeonsX, generated plans in DataDungeonPlans) with 2-5 floors and a difficulty tier;
## defs() / order() cover all twenty. On an N-floor dungeon floors 1..N-2 have Seal Keepers, floor N-1 the champion
## and floor N the boss sanctum.
##
## A floor plan is a grid of 4 m cells, row 0 = north (far from the camera), one character per cell:
##   .  void (nothing: walls face it)          0 1 2  floor at storey 0 / 1 / 2 (y = 0, 4, 8 m)
##   ~  hazard basin (water, bog, lava, ice or void by theme; its liquid lies 2.4 m below storey 0)
##   =  bridge over the basin at storey 0      ^ v < >  a stair flight rising toward north / south / west / east
## Stairs rise 2 m per cell: two cells in a line climb one storey (4 m). The cell before a flight is its foot, the cell
## after it its head. Markers (arrival portal, descent portal, camps, chests, miniboss, boss) are given in cells
## (column, row); their height comes from the plan.
##
## Flow: the surface gate leads to floor 1. Each floor's descent portal is sealed until its Seal Keepers (an elite camp,
## or on floor 3 the dungeon's champion) fall; a broken seal stays broken. Floor 4 is the boss sanctum: the boss drops
## a Relic Cache and wakes the way home. The gate lets a hero go straight to any floor whose seal above is broken.
## Names are invented for Jre (no borrowed real-culture names — user rule).

const FLOORS := 4                     # floors of the bh-012 dungeons; bh-013 ones have 2-5 (floor_count)
## bh-013 raid recovery: once its boss falls a dungeon is raided; its camps stay empty for a recovery time rolled in
## [RECOVER_MIN, RECOVER_MAX] minutes (by tier), then replenish. The boss never returns for that hero; the sanctum
## is held by the dungeon's Usurper, a champion. Wall-clock time, so a dungeon also recovers while the game is closed.
const RECOVER_MIN := 30.0
const RECOVER_MAX := 120.0
const CHEST_RESPAWN := 1800.0         # a looted dungeon chest refills after this much play time

## Theme presentation: environment preset, stone tint overrides (MaterialLibrary), basin liquid and light colours.
const THEMES := {
	&"fungal": {
		"env": {"bg": Color(0.012, 0.016, 0.01), "ambient": Color(0.34, 0.36, 0.3), "ambient_energy": 1.35,
			"fog": Color(0.08, 0.11, 0.06), "fog_density": 0.004, "fog_height": 0.5, "fog_height_density": 0.12,
			"sun": Color(0.6, 0.75, 0.45), "sun_energy": 0.35, "sun_rot": Vector3(-60, 25, 0), "glow": 0.95,
			"exposure": 1.05, "contrast": 1.08, "saturation": 1.0},
		"stone": {"BH_Stone": ["fungal_stone", Color(0.85, 0.84, 0.74)], "BH_StoneDark": ["fungal_stone", Color(0.52, 0.5, 0.44)]},
		"liquid": [Color(0.32, 0.5, 0.1), Color(0.03, 0.06, 0.02), 0.8], "mist": Color(0.45, 0.6, 0.25),
		"glow": Color(0.75, 1.0, 0.3), "torch": Color(1.0, 0.7, 0.35), "rune": Color(0.7, 1.0, 0.35),
	},
	&"drowned": {
		"env": {"bg": Color(0.008, 0.014, 0.02), "ambient": Color(0.3, 0.34, 0.4), "ambient_energy": 1.4,
			"fog": Color(0.05, 0.1, 0.12), "fog_density": 0.003, "fog_height": 0.2, "fog_height_density": 0.1,
			"sun": Color(0.5, 0.65, 0.9), "sun_energy": 0.38, "sun_rot": Vector3(-62, 20, 0), "glow": 0.9,
			"exposure": 1.05, "contrast": 1.1, "saturation": 0.92},
		"stone": {"BH_Stone": ["stone_blocks", Color(0.62, 0.7, 0.68)], "BH_StoneDark": ["stone_blocks", Color(0.32, 0.4, 0.4)]},
		"liquid": [Color(0.08, 0.55, 0.55), Color(0.01, 0.06, 0.09), 0.75], "mist": Color(0.4, 0.75, 0.75),
		"glow": Color(0.2, 0.9, 0.82), "torch": Color(1.0, 0.64, 0.32), "rune": Color(0.35, 0.95, 0.9),
	},
	&"ember": {
		"env": {"bg": Color(0.02, 0.008, 0.004), "ambient": Color(0.4, 0.34, 0.32), "ambient_energy": 1.8,
			"fog": Color(0.12, 0.05, 0.03), "fog_density": 0.003, "fog_height": 0.4, "fog_height_density": 0.1,
			"sun": Color(1.0, 0.7, 0.5), "sun_energy": 0.5, "sun_rot": Vector3(-58, 30, 0), "glow": 1.0,
			"exposure": 1.0, "contrast": 1.12, "saturation": 1.0},
		"stone": {"BH_Stone": ["basalt", Color(0.95, 0.9, 0.86)], "BH_StoneDark": ["basalt", Color(0.62, 0.58, 0.56)]},
		"liquid": [Color(1.0, 0.38, 0.06), Color(0.22, 0.03, 0.0), 1.05], "mist": Color(0.8, 0.35, 0.1),
		"glow": Color(1.0, 0.45, 0.12), "torch": Color(1.0, 0.55, 0.25), "rune": Color(1.0, 0.55, 0.2),
	},
	&"rime": {
		"env": {"bg": Color(0.012, 0.016, 0.026), "ambient": Color(0.38, 0.42, 0.5), "ambient_energy": 1.35,
			"fog": Color(0.16, 0.2, 0.26), "fog_density": 0.004, "fog_height": 0.6, "fog_height_density": 0.12,
			"sun": Color(0.65, 0.78, 1.0), "sun_energy": 0.5, "sun_rot": Vector3(-60, 20, 0), "glow": 0.9,
			"exposure": 1.08, "contrast": 1.06, "saturation": 0.85},
		"stone": {"BH_Stone": ["stone_blocks", Color(0.8, 0.86, 0.95)], "BH_StoneDark": ["stone_blocks", Color(0.48, 0.54, 0.64)]},
		"liquid": [Color(0.55, 0.78, 0.95), Color(0.1, 0.2, 0.35), 0.45], "mist": Color(0.75, 0.85, 1.0),
		"glow": Color(0.5, 0.8, 1.0), "torch": Color(0.75, 0.88, 1.0), "rune": Color(0.55, 0.85, 1.0),
	},
	&"orrery": {
		"env": {"bg": Color(0.012, 0.008, 0.024), "ambient": Color(0.36, 0.34, 0.44), "ambient_energy": 1.35,
			"fog": Color(0.08, 0.05, 0.14), "fog_density": 0.003, "fog_height": 0.3, "fog_height_density": 0.1,
			"sun": Color(0.75, 0.65, 1.0), "sun_energy": 0.4, "sun_rot": Vector3(-60, 30, 0), "glow": 1.0,
			"exposure": 1.05, "contrast": 1.1, "saturation": 0.95},
		"stone": {"BH_Stone": ["marble", Color(0.86, 0.84, 0.82)], "BH_StoneDark": ["marble", Color(0.46, 0.44, 0.52)]},
		"liquid": [Color(0.45, 0.25, 0.85), Color(0.03, 0.01, 0.08), 1.4], "mist": Color(0.55, 0.4, 0.9),
		"glow": Color(0.72, 0.55, 1.0), "torch": Color(1.0, 0.78, 0.5), "rune": Color(0.75, 0.55, 1.0),
	},
}

## Dungeon list. `surface`: the entrance map, the gate's position (map-local x, z) and facing; `levels`: [min, max] per
## floor; `pools`: enemy lists the floor camps draw from ("a" lighter, "b" heavier, "seal" the Seal Keepers).
const LIST := {
	&"warren": {
		"name": "Hollowroot Warren", "theme": &"fungal", "material": &"glowcap_spore",
		"surface": {"map": &"westreach", "pos": Vector2(68.0, 77.0), "yaw": 0.0, "place": "wr_warren"},
		"blurb": "Something vast grows under Lantern Fields. The roots have started coming up through the Fen Road.",
		"levels": [[5, 7], [7, 9], [9, 10], [11, 11]],
		"pools": {"a": [&"sporeling", &"sporeling", &"rootback_boar", &"sporeling"],
			"b": [&"rootweaver", &"mycelid_hulk", &"sporeling", &"rootback_boar", &"broodmother"],
			"seal": [&"mycelid_hulk", &"rootweaver", &"rootback_boar", &"sporeling", &"sporeling"]},
		"music": &"dungeon_theme", "ambience": &"amb_forest", "footstep": &"dirt", "reverb": 0.35,
		"miniboss": {"id": &"gorrowmaw", "name": "Gorrowmaw the Sporefather", "title": "Champion of the Warren", "enemy": &"mycelid_hulk",
			"mods": [&"regenerating"], "scale": 1.25, "hp": 2.4, "damage": 1.25, "level_bonus": 1,
			"lore": "The oldest thing in the Warren that can still walk. Every sporeling there budded from its back."},
		"boss": &"rot_mother",
		"floors": [
			{"name": "The Rootways", "arrival": Vector2i(8, 12), "descent": Vector2i(14, 1), "seal": Vector2i(10, 1),
				"camps": [[Vector2i(4, 6), "a", 4, 0.15], [Vector2i(14, 3), "a", 4, 0.1], [Vector2i(9, 8), "b", 3, 0.15], [Vector2i(9, 11), "a", 3, 0.0], [Vector2i(4, 1), "b", 3, 0.2]],
				"chests": [[Vector2i(2, 10), 0], [Vector2i(2, 1), 1]],
				"plan": [
					"..................",
					"..111111111111111.",
					"..111111111111111.",
					"..^0000000000000..",
					"..^00~~~~==~~~~0..",
					"..000~~~~==~~~~0..",
					"..000~~~~==~~~~0..",
					"..000~~~~==~~~~0..",
					"..00000000000000..",
					"........00........",
					".000....00........",
					".000000000000.....",
					".000.00000000.....",
					".....00000000.....",
					"..................",
				]},
			{"name": "Glowcap Terraces", "arrival": Vector2i(11, 15), "descent": Vector2i(2, 2), "seal": Vector2i(4, 3),
				"camps": [[Vector2i(2, 8), "a", 4, 0.3], [Vector2i(14, 9), "b", 4, 0.3], [Vector2i(8, 12), "a", 5, 0.2], [Vector2i(10, 3), "b", 4, 0.3], [Vector2i(15, 2), "a", 4, 0.2]],
				"chests": [[Vector2i(16, 1), 1], [Vector2i(14, 12), 0]],
				"plan": [
					"..................",
					".22222.....111111.",
					".22222<<111111111.",
					".22222..111111111.",
					".22222..111111111.",
					".............^....",
					".............^....",
					".000000000000000..",
					".00~~~~~~~~~0000..",
					".00~~~~~~~~~0000..",
					".00=========0000..",
					".00~~~~~~~~~0000..",
					".000000000000000..",
					"...........00.....",
					".........000000...",
					".........000000...",
					"..................",
				]},
			{"name": "Heart of Roots", "arrival": Vector2i(8, 14), "descent": Vector2i(8, 1), "miniboss": Vector2i(9, 2),
				"camps": [[Vector2i(3, 5), "b", 4, 0.45], [Vector2i(14, 5), "b", 4, 0.45], [Vector2i(8, 10), "a", 5, 0.35], [Vector2i(4, 2), "a", 4, 0.35], [Vector2i(13, 2), "b", 3, 0.45]],
				"chests": [[Vector2i(6, 1), 1], [Vector2i(11, 1), 1]],
				"plan": [
					"..................",
					"......111111......",
					"..11111111111111..",
					"..11111111111111..",
					"..11000000000011..",
					"..1100~~~~~~0011..",
					"..1100~~~~~~0011..",
					"..1100~~~~~~0011..",
					"..^000~~~~~~000^..",
					"..^000000000000^..",
					"..00000000000000..",
					"........00........",
					"........00........",
					"......000000......",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "The Rot Mother's Bower", "arrival": Vector2i(8, 14), "exit": Vector2i(8, 1), "boss": Vector2i(8, 6),
				"camps": [], "chests": [[Vector2i(11, 1), 2]],
				"plan": [
					"..................",
					"....1111111111....",
					"....1111111111....",
					"...0^00000000^0...",
					"...0^00000000^0...",
					"..00000000000000..",
					"..00000000000000..",
					"..00000000000000..",
					"..00000000000000..",
					"..~~0000000000~~..",
					"..~~0000000000~~..",
					"....0000000000....",
					"........00........",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
		],
	},
	&"deeps": {
		"name": "Saltmouth Deeps", "theme": &"drowned", "material": &"tide_pearl",
		"surface": {"map": &"westreach", "pos": Vector2(-188.5, 70.0), "yaw": 90.0, "place": "wr_deeps"},
		"blurb": "The smugglers found a door at the back of Saltmouth Cave. Whatever they let out has been ringing a bell ever since.",
		"levels": [[7, 9], [9, 11], [11, 12], [13, 13]],
		"pools": {"a": [&"drowned_deckhand", &"drowned_deckhand", &"reef_crawler", &"drowned_deckhand"],
			"b": [&"brinecaller", &"barnacle_hulk", &"drowned_deckhand", &"reef_crawler"],
			"seal": [&"barnacle_hulk", &"brinecaller", &"reef_crawler", &"drowned_deckhand", &"drowned_deckhand"]},
		"music": &"dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.6,
		"miniboss": {"id": &"varroch", "name": "Keelbreaker Varroch", "title": "Champion of the Deeps", "enemy": &"barnacle_hulk",
			"mods": [&"armored"], "scale": 1.2, "hp": 2.4, "damage": 1.25, "level_bonus": 1,
			"lore": "It hauled three ships onto the rocks by their anchor chains. It still drags the chain behind it."},
		"boss": &"bell_warden",
		"floors": [
			{"name": "The Smugglers' Sluice", "arrival": Vector2i(8, 12), "descent": Vector2i(12, 1), "seal": Vector2i(2, 2),
				"camps": [[Vector2i(5, 6), "a", 4, 0.15], [Vector2i(13, 10), "a", 4, 0.15], [Vector2i(10, 2), "b", 3, 0.2], [Vector2i(1, 8), "a", 3, 0.1], [Vector2i(16, 8), "b", 3, 0.15]],
				"chests": [[Vector2i(4, 1), 1], [Vector2i(14, 3), 0]],
				"plan": [
					"..................",
					".1111....000000...",
					".1111....000000...",
					".1111....000000...",
					"..^.......00......",
					"..^.......00......",
					".0000000000000000.",
					".0~~~~~~~~=~~~~~0.",
					".0~~~~~~~~=~~~~~0.",
					".0~~~~~~~~=~~~~~0.",
					".0000000000000000.",
					".....00000000.....",
					".....00000000.....",
					".....00000000.....",
					"..................",
				]},
			{"name": "The Great Cistern", "arrival": Vector2i(8, 15), "descent": Vector2i(3, 1), "seal": Vector2i(6, 2),
				"camps": [[Vector2i(2, 10), "a", 4, 0.3], [Vector2i(15, 10), "a", 4, 0.3], [Vector2i(8, 4), "b", 5, 0.3], [Vector2i(15, 4), "b", 3, 0.3], [Vector2i(8, 7), "a", 4, 0.2], [Vector2i(12, 1), "b", 3, 0.3]],
				"chests": [[Vector2i(16, 2), 1], [Vector2i(1, 12), 0]],
				"plan": [
					"..................",
					".2222222222222222.",
					".22222222.2222222.",
					".111111111111^111.",
					".111111111111^111.",
					".1111111111111111.",
					".^000000000000000.",
					".^000000000000000.",
					".000~~~~~~~~~~000.",
					".000~~~~~~~~~~000.",
					".000==========000.",
					".000~~~~~~~~~~000.",
					".000~~~~~~~~~~000.",
					".0000000~~0000000.",
					".......000........",
					"......00000.......",
					"......00000.......",
					"..................",
				]},
			{"name": "Bellwright's Locks", "arrival": Vector2i(8, 13), "descent": Vector2i(9, 1), "miniboss": Vector2i(8, 8),
				"camps": [[Vector2i(2, 7), "b", 4, 0.45], [Vector2i(15, 7), "b", 4, 0.45], [Vector2i(8, 12), "a", 5, 0.35], [Vector2i(5, 2), "a", 4, 0.35], [Vector2i(13, 3), "b", 3, 0.45]],
				"chests": [[Vector2i(11, 6), 1], [Vector2i(4, 1), 1]],
				"plan": [
					"..................",
					"....0000000000....",
					"....0000000000....",
					"..00000000000000..",
					"..==~~~~~~~~~~==..",
					"..==~~~~~~~~~~==..",
					"..00..111111..00..",
					"..00>>111111<<00..",
					"..00..111111..00..",
					"..00..111111..00..",
					"..==~~~~~~~~~~==..",
					"..==~~~~~~~~~~==..",
					"..00000000000000..",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "The Drowned Bell", "arrival": Vector2i(8, 16), "exit": Vector2i(8, 1), "boss": Vector2i(8, 9),
				"camps": [], "chests": [[Vector2i(12, 1), 2]],
				"plan": [
					"..................",
					"..11111111111111..",
					"..11111111111111..",
					"..^000000000000^..",
					"..^000000000000^..",
					"..00000000000000..",
					"..0~~~~~==~~~~~0..",
					"..0~~~~~==~~~~~0..",
					"..0~~00000000~~0..",
					"..0==00000000==0..",
					"..0==00000000==0..",
					"..0~~00000000~~0..",
					"..0~~~~~==~~~~~0..",
					"..0~~~~~==~~~~~0..",
					"..00000000000000..",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
		],
	},
	&"ember": {
		"name": "Emberforge Depths", "theme": &"ember", "material": &"slag_ember",
		"surface": {"map": &"westreach", "pos": Vector2(52.0, -22.0), "yaw": 0.0, "place": "wr_ember"},
		"blurb": "Smoke rises from a crack in the hill above the Lake Shore Road. Olivar's smiths say the old forge-lords have gone back to work.",
		"levels": [[10, 12], [12, 14], [14, 15], [16, 16]],
		"pools": {"a": [&"cinder_imp", &"slag_hound", &"forge_thrall", &"slag_hound"],
			"b": [&"magma_golem", &"forge_thrall", &"cinder_imp", &"ashen_cultist", &"slag_hound"],
			"seal": [&"magma_golem", &"forge_thrall", &"forge_thrall", &"cinder_imp", &"slag_hound"]},
		"music": &"fire_dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.5,
		"miniboss": {"id": &"cindrax", "name": "Cindrax the Furnace-Heart", "title": "Champion of the Depths", "enemy": &"magma_golem",
			"mods": [&"berserker"], "scale": 1.2, "hp": 2.4, "damage": 1.25, "level_bonus": 1,
			"lore": "The first golem the Forgemaster ever poured. Its core has been burning for nine hundred years."},
		"boss": &"forgemaster",
		"floors": [
			{"name": "The Slag Gate", "arrival": Vector2i(12, 13), "descent": Vector2i(14, 1), "seal": Vector2i(3, 4),
				"camps": [[Vector2i(8, 8), "a", 4, 0.15], [Vector2i(4, 11), "a", 4, 0.15], [Vector2i(12, 2), "b", 3, 0.2], [Vector2i(11, 5), "a", 3, 0.1], [Vector2i(15, 11), "b", 3, 0.15]],
				"chests": [[Vector2i(6, 3), 1], [Vector2i(1, 11), 0]],
				"plan": [
					"..................",
					"..........0000000.",
					"..........0000000.",
					".111111...0000000.",
					".111111....00.....",
					".111111....00.....",
					"...^.......00.....",
					"...^.......00.....",
					".0000000000000000.",
					".0~~~=~~~~~~=~~~0.",
					".0~~~=~~~~~~=~~~0.",
					".0000000000000000.",
					".........0000000..",
					".........0000000..",
					".........0000000..",
					"..................",
				]},
			{"name": "The Great Foundry", "arrival": Vector2i(8, 15), "descent": Vector2i(7, 1), "seal": Vector2i(10, 2),
				"camps": [[Vector2i(4, 12), "a", 4, 0.3], [Vector2i(13, 12), "a", 4, 0.3], [Vector2i(1, 6), "b", 3, 0.3], [Vector2i(16, 6), "b", 3, 0.3], [Vector2i(8, 4), "b", 4, 0.3]],
				"chests": [[Vector2i(8, 7), 1], [Vector2i(12, 3), 1]],
				"plan": [
					"..................",
					".11..22222222..11.",
					".11>>22222222<<11.",
					".11..22222222..11.",
					".1111111111111111.",
					".11~~~~~~~~~~~~11.",
					".11~~~~~~~~~~~~11.",
					".11~~~~0000~~~~11.",
					".11~~~~0000~~~~11.",
					".11~~~~~==~~~~~11.",
					".^1~~~~~==~~~~~1^.",
					".^.~~~~~==~~~~~.^.",
					".0000000000000000.",
					".0000000000000000.",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "Anvil of the Deep", "arrival": Vector2i(8, 13), "descent": Vector2i(9, 1), "miniboss": Vector2i(8, 4),
				"camps": [[Vector2i(2, 8), "b", 4, 0.45], [Vector2i(15, 8), "b", 4, 0.45], [Vector2i(8, 8), "a", 5, 0.35], [Vector2i(6, 3), "a", 3, 0.35], [Vector2i(11, 3), "b", 3, 0.45]],
				"chests": [[Vector2i(5, 1), 1], [Vector2i(12, 1), 1]],
				"plan": [
					"..................",
					".....11222211.....",
					".....111^1111.....",
					".....111^1111.....",
					".....11111111.....",
					".0000^0~~~~0^0000.",
					".0000^0~~~~0^0000.",
					".0000000000000000.",
					".0000000000000000.",
					".0000000000000000.",
					".~~~0000000000~~~.",
					".~~~0000000000~~~.",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "Durnhelm's Throne-Forge", "arrival": Vector2i(8, 14), "exit": Vector2i(8, 1), "boss": Vector2i(8, 8),
				"camps": [], "chests": [[Vector2i(10, 1), 2]],
				"plan": [
					"..................",
					"......111111......",
					"......111111......",
					"..00000^00^00000..",
					"..00000^00^00000..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..0==00000000==0..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..00000000000000..",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
		],
	},
	&"barrow": {
		"name": "Rimeglass Barrow", "theme": &"rime", "material": &"rime_shard",
		"surface": {"map": &"ruined_forest", "pos": Vector2(-46.0, -31.0), "yaw": 0.0, "place": "rf_barrow"},
		"blurb": "The old kings of the forest were buried in ice under the north rim. This winter, the frost came down the hill.",
		"levels": [[13, 15], [15, 17], [17, 19], [20, 20]],
		"pools": {"a": [&"rime_husk", &"rime_husk", &"rime_weaver", &"ice_wraith"],
			"b": [&"barrow_jarl", &"ice_wraith", &"rime_husk", &"frost_revenant", &"rime_weaver"],
			"seal": [&"barrow_jarl", &"barrow_jarl", &"ice_wraith", &"rime_weaver", &"rime_husk"]},
		"music": &"ice_dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.65,
		"miniboss": {"id": &"hrimgard", "name": "Hrimgard of the Frozen Oath", "title": "Champion of the Barrow", "enemy": &"barrow_jarl",
			"mods": [&"frozen", &"shielded"], "scale": 1.3, "hp": 2.4, "damage": 1.25, "level_bonus": 1,
			"lore": "The queen's shield-sworn. He swore to hold her door until spring, and spring never came."},
		"boss": &"winter_crown",
		"floors": [
			{"name": "Frostgate Barrow", "arrival": Vector2i(8, 11), "descent": Vector2i(9, 1), "seal": Vector2i(2, 7),
				"camps": [[Vector2i(8, 7), "a", 5, 0.15], [Vector2i(15, 8), "b", 3, 0.15], [Vector2i(8, 2), "b", 3, 0.2], [Vector2i(13, 5), "a", 3, 0.1]],
				"chests": [[Vector2i(1, 5), 1], [Vector2i(16, 6), 0]],
				"plan": [
					"..................",
					".......0000.......",
					".......0000.......",
					".......0000.......",
					"........00........",
					".1111.00000000000.",
					".1111.000000~~~00.",
					".1111<<00000~~~00.",
					".1111.000000~~~00.",
					".1111.00000000000.",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "Hall of Frozen Kings", "arrival": Vector2i(8, 15), "descent": Vector2i(4, 1), "seal": Vector2i(8, 2),
				"camps": [[Vector2i(8, 5), "b", 4, 0.3], [Vector2i(13, 6), "a", 4, 0.3], [Vector2i(4, 9), "a", 4, 0.2], [Vector2i(13, 11), "b", 4, 0.3], [Vector2i(4, 6), "a", 3, 0.3]],
				"chests": [[Vector2i(13, 1), 1], [Vector2i(3, 12), 0]],
				"plan": [
					"..................",
					"..222222222222....",
					"..22222222222222..",
					"..22222222222222..",
					"..^1111111111111..",
					"..^1111111111111..",
					"..11111111111111..",
					"..11111111111111..",
					"..0000000000000^..",
					"..0000000000000^..",
					"..000~~~~~~~0000..",
					"..000~~~~~~~0000..",
					"..00000000000000..",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "Glacier Rift", "arrival": Vector2i(6, 14), "descent": Vector2i(15, 1), "miniboss": Vector2i(14, 4),
				"camps": [[Vector2i(3, 4), "b", 4, 0.45], [Vector2i(3, 10), "a", 5, 0.35], [Vector2i(10, 9), "b", 3, 0.45], [Vector2i(9, 12), "a", 4, 0.35], [Vector2i(14, 6), "b", 3, 0.45]],
				"chests": [[Vector2i(1, 1), 1], [Vector2i(12, 1), 1]],
				"plan": [
					"..................",
					".000000~~~.111111.",
					".000000~~~.111111.",
					".000000~~~0^11111.",
					".000000~~~0^11111.",
					".000000~~~0011111.",
					".000000===0011111.",
					".000000~~~0011111.",
					".000000~~~00......",
					".000000~~~00......",
					".000000===00......",
					".000000~~~00......",
					".000000000000.....",
					"....00000.........",
					"...0000000........",
					"...0000000........",
					"..................",
				]},
			{"name": "The Winter Throne", "arrival": Vector2i(8, 14), "exit": Vector2i(8, 1), "boss": Vector2i(8, 7),
				"camps": [], "chests": [[Vector2i(10, 1), 2]],
				"plan": [
					"..................",
					"......111111......",
					"....1111111111....",
					"....^00000000^....",
					"..00^00000000^00..",
					"..00000000000000..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..00000000000000..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..00000000000000..",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
		],
	},
	&"orrery": {
		"name": "The Shattered Orrery", "theme": &"orrery", "material": &"star_glass",
		"surface": {"map": &"wyman_outpost", "pos": Vector2(-28.0, -46.0), "yaw": 90.0, "place": "wy_orrery"},
		"blurb": "The Aether-watchers built their observatory under the marsh so the stars would hold still. Now the stars are loose.",
		"levels": [[17, 19], [19, 21], [21, 23], [25, 25]],
		"pools": {"a": [&"clockwork_sentry", &"star_mote", &"astral_duelist", &"star_mote"],
			"b": [&"void_seer", &"astral_duelist", &"clockwork_sentry", &"rune_golem", &"aether_wisp"],
			"seal": [&"void_seer", &"astral_duelist", &"astral_duelist", &"clockwork_sentry", &"star_mote"]},
		"music": &"dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.7,
		"miniboss": {"id": &"lumenar", "name": "Lumenar, the Last Astronomer", "title": "Champion of the Orrery", "enemy": &"void_seer",
			"mods": [&"aether_infused", &"swift"], "scale": 1.3, "hp": 2.6, "damage": 1.25, "level_bonus": 1,
			"lore": "He mapped every star over Jre, then went looking for the ones that were not there."},
		"boss": &"astrarch",
		"floors": [
			{"name": "The Lower Galleries", "arrival": Vector2i(8, 14), "descent": Vector2i(14, 1), "seal": Vector2i(3, 1),
				"camps": [[Vector2i(3, 9), "a", 4, 0.15], [Vector2i(14, 9), "a", 4, 0.15], [Vector2i(8, 6), "b", 3, 0.2], [Vector2i(12, 2), "b", 3, 0.2], [Vector2i(8, 12), "a", 3, 0.1]],
				"chests": [[Vector2i(1, 2), 1], [Vector2i(15, 6), 0]],
				"plan": [
					"..................",
					".111111....000000.",
					".111111....000000.",
					".111111.....00....",
					"...^........00....",
					"...^........00....",
					"..00000000000000..",
					"..00~~~~=~~~~~00..",
					"..00~~~~=~~~~~00..",
					"..00==========00..",
					"..00~~~~=~~~~~00..",
					"..00~~~~=~~~~~00..",
					"..00000000000000..",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "Tiers of the Star Map", "arrival": Vector2i(8, 14), "descent": Vector2i(7, 1), "seal": Vector2i(10, 2),
				"camps": [[Vector2i(4, 6), "a", 4, 0.3], [Vector2i(13, 10), "a", 4, 0.3], [Vector2i(8, 3), "b", 4, 0.3], [Vector2i(1, 6), "b", 3, 0.3], [Vector2i(16, 5), "a", 3, 0.3]],
				"chests": [[Vector2i(1, 10), 1], [Vector2i(16, 10), 1]],
				"plan": [
					"..................",
					".11>>22222222<<11.",
					".11..22222222..11.",
					".1111111111111111.",
					".1111111111111111.",
					".1100000000000011.",
					".11000~~~~~~00011.",
					".11000~~~~~~00011.",
					".11<<0~~~~~~0>>11.",
					".11000~~~~~~00011.",
					".11000~~~~~~00011.",
					"...000000000000...",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "The Lens Chamber", "arrival": Vector2i(8, 13), "descent": Vector2i(12, 1), "miniboss": Vector2i(8, 2),
				"camps": [[Vector2i(4, 5), "b", 4, 0.45], [Vector2i(13, 5), "b", 4, 0.45], [Vector2i(4, 10), "a", 4, 0.35], [Vector2i(13, 10), "a", 4, 0.35], [Vector2i(3, 1), "b", 3, 0.45]],
				"chests": [[Vector2i(15, 1), 1], [Vector2i(1, 10), 1]],
				"plan": [
					"..................",
					".1111111111111111.",
					".1111111111111111.",
					".^00000000000000^.",
					".^00000000000000^.",
					".0000000~~0000000.",
					".0000000~~0000000.",
					".0000000==0000000.",
					".0~~=~~~~~~~~=~~0.",
					".0000000==0000000.",
					".0000000~~0000000.",
					".0000000~~0000000.",
					"......000000......",
					"......000000......",
					"..................",
				]},
			{"name": "The Astrarch's Dome", "arrival": Vector2i(8, 15), "exit": Vector2i(9, 1), "boss": Vector2i(8, 9),
				"camps": [], "chests": [[Vector2i(12, 1), 2]],
				"plan": [
					"..................",
					"....1112222111....",
					"....1111^11111....",
					"....1111^11111....",
					"....1111111111....",
					"..00^00000000^00..",
					"..00^00000000^00..",
					"..00000000000000..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..00000000000000..",
					"..0~~00000000~~0..",
					"..0~~00000000~~0..",
					"..00000000000000..",
					"........00........",
					"......000000......",
					"......000000......",
					"..................",
				]},
		],
	},
}

const ORDER: Array[StringName] = [&"warren", &"deeps", &"ember", &"barrow", &"orrery"]

## Difficulty tiers of the bh-012 dungeons (DataDungeonsX.TIER_NAMES).
const TIER := {&"warren": 2, &"deeps": 2, &"ember": 3, &"barrow": 3, &"orrery": 4}

## The sanctum's new holder once a bh-012 dungeon's boss is gone (bh-013).
const USURPERS := {
	&"warren": {"id": &"warren_usurper", "name": "Sporeheart the Budded", "title": "Usurper of the Warren", "enemy": &"mycelid_hulk",
		"mods": [&"regenerating", &"vampiric"], "scale": 1.4, "hp": 2.6, "damage": 1.25, "level_bonus": 1,
		"lore": "The Rot Mother's last bud took root where she fell. It has her appetite already."},
	&"deeps": {"id": &"deeps_usurper", "name": "Captain Harrow Kelp", "title": "Usurper of the Deeps", "enemy": &"barnacle_hulk",
		"mods": [&"armored", &"swift"], "scale": 1.3, "hp": 2.6, "damage": 1.25, "level_bonus": 1,
		"lore": "He rang the bell once when Ossric fell, to see what would happen. Now he is the one who answers it."},
	&"ember": {"id": &"ember_usurper", "name": "Anvilgrim", "title": "Usurper of the Depths", "enemy": &"forge_thrall",
		"mods": [&"flaming", &"shielded"], "scale": 1.35, "hp": 2.6, "damage": 1.25, "level_bonus": 1,
		"lore": "The Forgemaster's favourite thrall picked up her hammer. It has not put it down since."},
	&"barrow": {"id": &"barrow_usurper", "name": "The Frostbitten Heir", "title": "Usurper of the Barrow", "enemy": &"barrow_jarl",
		"mods": [&"frozen", &"berserker"], "scale": 1.3, "hp": 2.6, "damage": 1.25, "level_bonus": 1,
		"lore": "Skaldra's grandson waited a thousand years for the throne. He is not giving it back."},
	&"orrery": {"id": &"orrery_usurper", "name": "The Loose Star", "title": "Usurper of the Orrery", "enemy": &"void_seer",
		"mods": [&"aether_infused", &"cursed"], "scale": 1.35, "hp": 2.6, "damage": 1.25, "level_bonus": 1,
		"lore": "One of the Astrarch's stars never went back into its ring. It sits in the dome and turns alone."},
}

static var _defs := {}
static var _order: Array[StringName] = []
## Wall-clock offset for tests (seconds added to the system clock).
static var clock_offset := 0.0

# ------------------------------------------------------------------------------------------------------------

## Every dungeon: the five of bh-012 and the fifteen of bh-013 (tier and usurper filled in).
static func defs() -> Dictionary:
	if _defs.is_empty():
		for id in ORDER:
			var d: Dictionary = (LIST[id] as Dictionary).duplicate()
			d["tier"] = TIER.get(id, 2)
			d["usurper"] = USURPERS[id]
			_defs[id] = d
		var x := DataDungeonsX.list()
		for id in x:
			_defs[id] = x[id]
	return _defs

## Every dungeon id, easiest (lowest first floor) first.
static func order() -> Array[StringName]:
	if _order.is_empty():
		var ids: Array[StringName] = []
		for id in defs():
			ids.append(id)
		ids.sort_custom(func(a, b): return int(defs()[a].levels[0][0]) < int(defs()[b].levels[0][0]))
		_order = ids
	return _order

static func get_def(id: StringName) -> Dictionary:
	return defs().get(id, {})

static func floor_count(id: StringName) -> int:
	return (get_def(id).get("floors", []) as Array).size()

## The floor that holds the dungeon's champion (the last sealed floor).
static func champion_floor(id: StringName) -> int:
	return floor_count(id) - 1

static func tier(id: StringName) -> int:
	return int(get_def(id).get("tier", 2))

static func tier_name(id: StringName) -> String:
	return DataDungeonsX.TIER_NAMES[clampi(tier(id), 1, 5)]

static func tier_stars(id: StringName) -> String:
	var t := clampi(tier(id), 1, 5)
	return "★".repeat(t) + "☆".repeat(5 - t)

static func level_range(id: StringName) -> Vector2i:
	if get_def(id).is_empty():
		return Vector2i.ONE
	var g := DungeonGrowth.for_hero(Game.hero, id)
	return Vector2i(DungeonGrowth.levels(id, 1, g).x, DungeonGrowth.levels(id, floor_count(id) + int(g.extra), g).y)

## Shared recommendation for entrances, maps and travel choices.
static func recommended_levels(id: StringName) -> String:
	var lv := level_range(id)
	return "Suggested Level %d–%d" % [lv.x, lv.y]

static func map_recommendation(map: StringName) -> String:
	var parsed := parse(map)
	if parsed[0] != &"":
		return recommended_levels(parsed[0])
	if map in [&"catacombs", &"forgotten_temple", &"boss_arena"]:
		var def := DB.map_def(map)
		return "Suggested Level %d–%d" % [def.level_min, def.level_max] if def.level_min != def.level_max else "Suggested Level %d" % def.level_min
	return ""

static func map_id(dungeon: StringName, floor_n: int) -> StringName:
	return StringName("dg_%s_%d" % [dungeon, floor_n])

## [dungeon id, floor number] for a dungeon floor map id, or [&"", 0].
static func parse(map: StringName) -> Array:
	var s := String(map)
	if not s.begins_with("dg_"):
		return [&"", 0]
	var parts := s.substr(3).rsplit("_", true, 1)
	if parts.size() != 2 or not defs().has(StringName(parts[0])):
		return [&"", 0]
	return [StringName(parts[0]), int(parts[1])]

static func floor_def(dungeon: StringName, floor_n: int) -> Dictionary:
	var d := get_def(dungeon)
	if d.is_empty() or floor_n < 1 or floor_n > floor_count(dungeon) + DungeonGrowth.MAX_EXTRA:
		return {}
	if floor_n > floor_count(dungeon):
		return DungeonGrowth.floor_plan(dungeon, floor_n)
	return d.floors[floor_n - 1]

static func theme(dungeon: StringName) -> Dictionary:
	var t: StringName = get_def(dungeon).get("theme", &"drowned")
	if THEMES.has(t):
		return THEMES[t]
	return DataDungeonsX.THEMES.get(t, THEMES[&"drowned"])

## World flag set when floor `n`'s seal breaks (its descent portal opens for good).
static func seal_flag(dungeon: StringName, floor_n: int) -> StringName:
	return StringName("dg_%s_%d_seal" % [dungeon, floor_n])

## World flag set the first time the dungeon's boss falls.
static func cleared_flag(dungeon: StringName) -> StringName:
	return StringName("dg_%s_cleared" % dungeon)

static func gate_id(dungeon: StringName) -> StringName:
	return StringName("dg_%s_gate" % dungeon)

## Dungeons whose gate stands on `map`.
static func gates_on(map: StringName) -> Array[StringName]:
	var out: Array[StringName] = []
	for id in order():
		if StringName(get_def(id).surface.map) == map:
			out.append(id)
	return out

## Floors the hero may enter straight from the surface gate: floor 1, and every floor whose seal above is broken.
static func reached_floors(hero: HeroData, dungeon: StringName) -> Array:
	var out := [1]
	for n in range(2, DungeonGrowth.total(hero, dungeon) + 1):
		var flag := cleared_flag(dungeon) if n == floor_count(dungeon) + 1 else seal_flag(dungeon, n - 1)
		if hero != null and bool(hero.world_flags.get(flag, false)):
			out.append(n)
		else:
			break
	return out

static func floor_title(dungeon: StringName, floor_n: int) -> String:
	return "%s — Floor %d" % [String(get_def(dungeon).get("name", "Dungeon")), floor_n]

## The Seal Keepers' camp name on the sealed floors (the Spawner reports its clearing).
const SEAL_ZONE := "seal_keepers"

# ---- raids and recovery (bh-013) -------------------------------------------------------------------------------

static func now() -> float:
	return Time.get_unix_time_from_system() + clock_offset

## The boss of this dungeon has fallen to this hero at least once: it never returns (its Usurper holds the sanctum).
static func boss_gone(hero: HeroData, dungeon: StringName) -> bool:
	return hero != null and (hero.dungeon_raids.has(String(dungeon)) or bool(hero.world_flags.get(cleared_flag(dungeon), false)))

## Minutes a raid on this dungeon takes to recover: 30–120, harder dungeons at the long end.
static func roll_recovery(dungeon: StringName, rng: RandomNumberGenerator = null) -> float:
	var r := rng
	if r == null:
		r = RandomNumberGenerator.new()
		r.randomize()
	var t := tier(dungeon)
	return clampf(30.0 + (t - 1) * 20.0 + r.randf_range(-5.0, 25.0), RECOVER_MIN, RECOVER_MAX)

## Record a raid (the boss just fell): the dungeon's camps stay empty for the rolled recovery time.
static func record_raid(hero: HeroData, dungeon: StringName, minutes := -1.0) -> Dictionary:
	if hero == null:
		return {}
	var m := minutes if minutes > 0.0 else roll_recovery(dungeon)
	var prev: Dictionary = hero.dungeon_raids.get(String(dungeon), {})
	var rec := {"at": now(), "until": now() + m * 60.0, "count": int(prev.get("count", 0)) + 1}
	hero.dungeon_raids[String(dungeon)] = rec
	hero.check_promotions()
	return rec

## Seconds until a raided dungeon's monsters return (0 when it is not recovering).
static func recover_left(hero: HeroData, dungeon: StringName) -> float:
	if hero == null or not hero.dungeon_raids.has(String(dungeon)):
		return 0.0
	return maxf(0.0, float(hero.dungeon_raids[String(dungeon)].get("until", 0.0)) - now())

static func recovering(hero: HeroData, dungeon: StringName) -> bool:
	return recover_left(hero, dungeon) > 0.0

## One line of state for the map and the guide.
static func status_text(hero: HeroData, dungeon: StringName) -> String:
	var n := DungeonGrowth.total(hero, dungeon)
	if recovering(hero, dungeon):
		return "Raided — its monsters return in %s" % fmt_minutes(recover_left(hero, dungeon))
	if boss_gone(hero, dungeon):
		return "Recovered — its lord is gone; %s holds the sanctum" % String(get_def(dungeon).usurper.name)
	var reached := reached_floors(hero, dungeon).size()
	if hero == null or (reached == 1 and not hero.discovered_maps.has(map_id(dungeon, 1))):
		return "Unexplored — %d floors. %s" % [n, DungeonGrowth.summary(hero, dungeon)]
	return "Floor %d of %d reached" % [reached, n]

## The same state, short enough for a row of the Underground list.
static func status_short(hero: HeroData, dungeon: StringName) -> String:
	if not recovering(hero, dungeon) and boss_gone(hero, dungeon):
		return "Recovered · held by %s" % String(get_def(dungeon).usurper.name)
	return status_text(hero, dungeon)

static func fmt_minutes(seconds: float) -> String:
	var m := ceili(seconds / 60.0)
	if m >= 60:
		return "%d h %02d min" % [m / 60, m % 60]
	return "%d min" % m

# ------------------------------------------------------------------------------------------------------------

## MapDefs for every dungeon floor.
static func map_defs() -> Array:
	var out := []
	for id in order():
		var d: Dictionary = get_def(id)
		var n_floors := floor_count(id)
		for n in range(1, n_floors + DungeonGrowth.MAX_EXTRA + 1):
			var f := floor_def(id, n)
			var m := MapDef.new()
			m.id = map_id(id, n)
			m.display_name = floor_title(id, n)
			m.subtitle = String(f.name)
			m.builder = "res://src/world/maps/dungeon.gd"
			var lv: Array = d.levels[mini(n, n_floors) - 1]
			m.level_min = int(lv[0])
			m.level_max = int(lv[1])
			m.music = StringName(d.music)      # the boss theme starts when the boss sees the hero (MusicDirector)
			m.ambience = StringName(d.ambience)
			m.footstep_surface = StringName(d.footstep)
			m.reverb = float(d.reverb)
			m.waypoint = false
			m.world_map_pos = Vector2(0.5, 0.5)
			m.loading_hint = _hint(id, n)
			out.append(m)
	return out

static func _hint(id: StringName, n: int) -> String:
	var d: Dictionary = get_def(id)
	if n > floor_count(id):
		return "These deeper halls open from Level %d. Clear the guardian's Seal Keeper pack to open its treasure and the next portal. Your dungeon strength stays fixed until you leave." % DungeonGrowth.STEPS[n - floor_count(id) - 1]
	if n == floor_count(id):
		return "The lord of %s waits below. Defeat it to wake the portal home and claim its Relic Cache. A raided dungeon recovers in 30 minutes to 2 hours; its lord does not." % d.name
	if n == champion_floor(id):
		return "%s guards the portal to the last floor. Beat the champion to break the seal." % d.miniboss.name
	if n == 1:
		return "%s The way down is sealed: defeat the Seal Keepers of each floor to open its descent portal." % d.blurb
	return "Upper storeys are reached by the stairs. Treasure chests hide on the high galleries; a looted chest refills in time."

## Minibosses of every dungeon (DataMinibosses reads these next to the surface champions): the champion of the last
## sealed floor, and the Usurper who holds the sanctum once the boss is gone (`raid_only`).
static func minibosses() -> Array:
	var out := []
	for id in order():
		var d: Dictionary = get_def(id)
		var cf := champion_floor(id)
		var f: Dictionary = d.floors[cf - 1]
		var m: Dictionary = (d.miniboss as Dictionary).duplicate()
		m["map"] = map_id(id, cf)
		m["pos"] = cell_xz(f.plan, f.miniboss)
		m["y"] = float(int(String(f.plan[f.miniboss.y])[f.miniboss.x])) * 4.0
		m["dungeon"] = id
		out.append(m)
		var last: Dictionary = d.floors[floor_count(id) - 1]
		var u: Dictionary = (d.usurper as Dictionary).duplicate()
		u["map"] = map_id(id, floor_count(id))
		u["pos"] = cell_xz(last.plan, last.boss)
		u["y"] = float(int(String(last.plan[last.boss.y])[last.boss.x])) * 4.0
		u["dungeon"] = id
		u["raid_only"] = id
		out.append(u)
	return out

## Map-local XZ of a plan cell's centre (the plan is centred on the origin).
static func cell_xz(plan: Array, cell: Vector2i) -> Vector2:
	var cols := String(plan[0]).length()
	var rows := plan.size()
	return Vector2((cell.x - cols * 0.5) * 4.0 + 2.0, (cell.y - rows * 0.5) * 4.0 + 2.0)

## Gate destinations offered by the surface dais (floor 1 first, then every reached floor).
static func gate_destinations(hero: HeroData, dungeon: StringName) -> Array:
	var out := []
	for n in reached_floors(hero, dungeon):
		out.append({"map": map_id(dungeon, n), "spawn": &"arrival", "name": "%s · %s" % [floor_title(dungeon, n), recommended_levels(dungeon)]})
	return out
