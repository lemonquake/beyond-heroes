class_name DataDungeonsSpecial
## bh-028: the five special dungeons behind Kethrax. Their gates stand on The Sundered Reach (sundered_reach.gd), a
## shard of broken land reached through the rift on Malasugue's waypoint terrace once Kethrax has fallen. Same shape as
## DataDungeonsX (DataDungeons merges this list), plus:
##   special  — no DungeonGrowth: no extra floors, the authored levels and pools at every hero level
##   min_tier — the hero tier a gate asks for (5 = Class A, DataGuilds.TIERS)
##   orb      — the celestial orb family the dungeon favours (DataCrystals); its lord always drops one (Loot)
##   power    — multipliers on the difficulty's monster health and damage ("very strong")
##   span     — [first, last] monster level; list() spreads it over the floors (the last floor is [last, last])
## Floor plans are generated offline (DataDungeonPlansSpecial, tools/dungeon_gen/gen_plans.py --special): 10-15 floors.
## Names are invented (no borrowed real-culture names — user rule).

const TIER := 6
const MIN_TIER := 5

const THEMES := {
	&"prism": {
		"env": {"bg": Color(0.01, 0.014, 0.022), "ambient": Color(0.46, 0.5, 0.58), "ambient_energy": 1.55,
			"fog": Color(0.08, 0.12, 0.18), "fog_density": 0.003, "fog_height": 0.4, "fog_height_density": 0.1,
			"sun": Color(0.8, 0.92, 1.0), "sun_energy": 0.55, "sun_rot": Vector3(-60, 25, 0), "glow": 1.15,
			"exposure": 1.06, "contrast": 1.1, "saturation": 0.82},
		"stone": {"BH_Stone": ["crystal_facet", Color(0.66, 0.7, 0.78)], "BH_StoneDark": ["crystal_facet", Color(0.4, 0.42, 0.5)]},
		"liquid": [Color(0.45, 0.85, 1.0), Color(0.03, 0.08, 0.14), 1.4], "mist": Color(0.6, 0.85, 1.0),
		"glow": Color(0.6, 0.9, 1.0), "torch": Color(0.82, 0.92, 1.0), "rune": Color(0.55, 0.9, 1.0),
	},
	&"underworld": {
		"env": {"bg": Color(0.004, 0.01, 0.012), "ambient": Color(0.3, 0.4, 0.42), "ambient_energy": 1.45,
			"fog": Color(0.03, 0.08, 0.09), "fog_density": 0.005, "fog_height": 0.6, "fog_height_density": 0.14,
			"sun": Color(0.5, 0.85, 0.85), "sun_energy": 0.35, "sun_rot": Vector3(-62, 20, 0), "glow": 1.05,
			"exposure": 1.08, "contrast": 1.12, "saturation": 0.72},
		"stone": {"BH_Stone": ["obsidian_soul", Color(0.56, 0.6, 0.6)], "BH_StoneDark": ["obsidian_soul", Color(0.4, 0.43, 0.44)]},
		"liquid": [Color(0.2, 0.8, 0.75), Color(0.0, 0.06, 0.07), 1.3], "mist": Color(0.35, 0.8, 0.78),
		"glow": Color(0.3, 1.0, 0.9), "torch": Color(0.45, 0.95, 0.9), "rune": Color(0.35, 1.0, 0.9),
	},
	&"aether": {
		"env": {"bg": Color(0.012, 0.012, 0.024), "ambient": Color(0.46, 0.46, 0.58), "ambient_energy": 1.55,
			"fog": Color(0.1, 0.1, 0.18), "fog_density": 0.003, "fog_height": 0.4, "fog_height_density": 0.1,
			"sun": Color(0.85, 0.8, 1.0), "sun_energy": 0.55, "sun_rot": Vector3(-58, 30, 0), "glow": 1.1,
			"exposure": 1.08, "contrast": 1.08, "saturation": 1.05},
		"stone": {"BH_Stone": ["aether_opal", Color(1.0, 1.0, 1.0)], "BH_StoneDark": ["aether_opal", Color(0.58, 0.56, 0.68)]},
		"liquid": [Color(0.6, 0.55, 1.0), Color(0.05, 0.03, 0.14), 1.3], "mist": Color(0.75, 0.7, 1.0),
		"glow": Color(0.75, 0.7, 1.0), "torch": Color(0.88, 0.85, 1.0), "rune": Color(0.7, 0.65, 1.0),
	},
	&"eclipse": {
		"env": {"bg": Color(0.006, 0.006, 0.012), "ambient": Color(0.4, 0.4, 0.48), "ambient_energy": 1.5,
			"fog": Color(0.05, 0.05, 0.09), "fog_density": 0.004, "fog_height": 0.4, "fog_height_density": 0.12,
			"sun": Color(0.78, 0.78, 0.92), "sun_energy": 0.45, "sun_rot": Vector3(-60, 30, 0), "glow": 1.1,
			"exposure": 1.1, "contrast": 1.14, "saturation": 0.8},
		"stone": {"BH_Stone": ["moonstone", Color(0.96, 0.96, 1.0)], "BH_StoneDark": ["moonstone", Color(0.5, 0.5, 0.58)]},
		"liquid": [Color(0.22, 0.2, 0.32), Color(0.01, 0.01, 0.03), 0.9], "mist": Color(0.6, 0.6, 0.75),
		"glow": Color(0.82, 0.82, 1.0), "torch": Color(0.8, 0.78, 0.95), "rune": Color(0.85, 0.85, 1.0),
	},
	&"solar": {
		"env": {"bg": Color(0.02, 0.014, 0.008), "ambient": Color(0.5, 0.44, 0.36), "ambient_energy": 1.6,
			"fog": Color(0.16, 0.1, 0.04), "fog_density": 0.003, "fog_height": 0.5, "fog_height_density": 0.1,
			"sun": Color(1.0, 0.82, 0.55), "sun_energy": 0.65, "sun_rot": Vector3(-58, 30, 0), "glow": 1.15,
			"exposure": 1.06, "contrast": 1.1, "saturation": 1.08},
		"stone": {"BH_Stone": ["sunstone", Color(1.0, 0.98, 0.94)], "BH_StoneDark": ["sunstone", Color(0.62, 0.52, 0.4)]},
		"liquid": [Color(0.2, 0.55, 0.6), Color(0.02, 0.07, 0.08), 1.1], "mist": Color(1.0, 0.8, 0.5),
		"glow": Color(1.0, 0.78, 0.35), "torch": Color(1.0, 0.75, 0.4), "rune": Color(1.0, 0.8, 0.4),
	},
}

## Room dressing per theme (same keys as dungeon.gd DRESS / CLUTTER / MapBuilder GATE_DRESS).
const DRESS := {
	&"prism": {"corner": ["crystal_pylon", "ice_crystal_large", "crystal_pylon", "statue_small"], "floor": ["ice_crystal_small", "rock_small", "candles_cluster"],
		"wall": ["icicles_hanging"], "basin": ["ice_crystal_large", "crystal_pylon"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.14},
	&"underworld": {"corner": ["sarcophagus", "obelisk_corrupted", "statue_collapsed", "coffin"], "floor": ["bones_scatter", "skull_pile", "candles_cluster"],
		"wall": ["chains_hanging", "banner_torn", "cobweb"], "basin": ["coffin", "skull_pile", "obelisk_corrupted"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.0},
	&"aether": {"corner": ["crystal_pylon", "armillary_sphere", "statue_small", "brass_telescope"], "floor": ["rock_small", "rubble_pile", "candles_cluster"],
		"wall": ["chains_hanging", "banner_torn"], "basin": ["floating_rock", "crystal_pylon"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.08},
	&"eclipse": {"corner": ["obelisk_corrupted", "statue_knight", "candles_cluster", "pillar_broken"], "floor": ["candles_cluster", "bones_scatter", "rubble_pile"],
		"wall": ["banner_torn", "chains_hanging"], "basin": ["floating_rock", "obelisk_corrupted"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.0},
	&"solar": {"corner": ["statue_knight", "pillar_broken", "urn", "statue_small"], "floor": ["rubble_pile", "rock_small", "bones_scatter"],
		"wall": ["banner_torn", "chains_hanging"], "basin": ["kelp_strands", "boat_rowing", "pillar_broken"], "breakable": "urn", "stairs": "stairs",
		"pillar": "pillar_quoin", "floor_light": 0.06},
}
const CLUTTER := {
	&"prism": ["ice_crystal_small", "rock_medium", "crystal_pylon", "rock_small", "statue_small"],
	&"underworld": ["coffin", "sarcophagus", "urn", "skull_pile", "candles_cluster", "gravestone_a", "gravestone_b"],
	&"aether": ["crystal_pylon", "brass_telescope", "lantern_stand", "lectern", "rock_medium"],
	&"eclipse": ["candles_cluster", "statue_small", "lectern", "urn", "ritual_circle"],
	&"solar": ["urn", "statue_small", "chest", "pillar_broken", "barrel", "crate"],
}
const GATE_DRESS := {
	&"prism": ["arch_quoin", "crystal_pylon", "ice_crystal_small"],
	&"underworld": ["arch_quoin", "obelisk_corrupted", "skull_pile"],
	&"aether": ["arch_quoin", "crystal_pylon", "rubble_pile"],
	&"eclipse": ["arch_quoin", "statue_knight", "candles_cluster"],
	&"solar": ["arch_quoin", "statue_small", "rubble_pile"],
}

## Where the five gates stand on The Sundered Reach: a half ring round the central plaza, each facing its middle.
const GATE_RING := 22.0
const GATE_ANGLES := {&"prismheart": 198.0, &"underworld": 234.0, &"aetherreach": 270.0, &"eclipse": 306.0, &"solarium": 342.0}

const LIST := {
	&"prismheart": {
		"name": "The Prismheart Hollows", "theme": &"prism", "orb": &"sora", "material": &"frost_crystal", "span": [80, 89],
		"blurb": "A cavern grown from a single crystal, older than Salmonan. Every facet holds a little of the sky it fell from.",
		"pools": {"a": [&"prism_sentinel", &"star_mote", &"mirror_knight", &"aether_wisp"],
			"b": [&"rune_golem", &"shellback_grinder", &"aegis_acolyte", &"astral_duelist"],
			"seal": [&"prism_sentinel", &"mirror_knight", &"aegis_acolyte", &"astral_duelist", &"star_mote"]},
		"music": &"ice_dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.75,
		"miniboss": {"id": &"facet_warden", "name": "The Facet Warden", "title": "Champion of the Hollows", "enemy": &"mirror_knight",
			"mods": [&"shielded", &"aether_infused"], "scale": 1.35, "hp": 2.8, "damage": 1.35, "level_bonus": 1,
			"lore": "It holds a mirror up to every hero who reaches it, and fights them with what it sees."},
		"boss": &"seraphel",
		"usurper": {"id": &"prismheart_usurper", "name": "The Refracted King", "title": "Usurper of the Hollows", "enemy": &"prism_sentinel",
			"mods": [&"aether_infused", &"armored"], "scale": 1.5, "hp": 3.0, "damage": 1.35, "level_bonus": 1,
			"lore": "A splinter of Seraphel's light, caught in the cavern's heart. It wears the colours of everything it broke."},
	},
	&"underworld": {
		"name": "The Underworld of Mourning", "theme": &"underworld", "orb": &"luna", "material": &"shadow_silk", "span": [86, 97],
		"blurb": "Below the rift runs a river of the dead. The drowned come up out of it singing, and the song never ends.",
		"pools": {"a": [&"forsaken_legionnaire", &"hollow_soldier", &"gloomwraith", &"shade_stalker"],
			"b": [&"forsaken_chainguard", &"necromancer", &"gravecaller", &"bloodbinder", &"ghoul_brute"],
			"seal": [&"forsaken_chainguard", &"necromancer", &"gloomwraith", &"forsaken_legionnaire", &"gravecaller"]},
		"music": &"dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.8,
		"miniboss": {"id": &"mourncaller", "name": "Mourncaller Veyth", "title": "Champion of the Underworld", "enemy": &"gravecaller",
			"mods": [&"cursed", &"vampiric"], "scale": 1.4, "hp": 2.8, "damage": 1.35, "level_bonus": 1,
			"lore": "Keeps the ferry-roll of the river. Every name on it is still owed a crossing."},
		"boss": &"morrowgaunt",
		"usurper": {"id": &"underworld_usurper", "name": "The Pale Ferryman", "title": "Usurper of the Underworld", "enemy": &"forsaken_chainguard",
			"mods": [&"regenerating", &"armored"], "scale": 1.4, "hp": 3.0, "damage": 1.35, "level_bonus": 1,
			"lore": "He poled the dead across for Morrowgaunt. Now he keeps the fare for himself."},
	},
	&"aetherreach": {
		"name": "The Aether Reach", "theme": &"aether", "orb": &"airah", "material": &"aether_shard", "span": [92, 104],
		"blurb": "Islands of stone drift in a sea of raw Aether, tied together by old bridges and the wind that never stops.",
		"pools": {"a": [&"aether_wisp", &"aether_sentinel", &"storm_herald", &"astral_duelist"],
			"b": [&"riftcaller", &"clockwork_sentry", &"aegis_acolyte", &"rune_golem"],
			"seal": [&"aether_sentinel", &"storm_herald", &"riftcaller", &"aegis_acolyte", &"astral_duelist"]},
		"music": &"dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.55,
		"miniboss": {"id": &"galecoil", "name": "The Galecoil Sentinel", "title": "Champion of the Reach", "enemy": &"aether_sentinel",
			"mods": [&"storm", &"armored"], "scale": 1.4, "hp": 2.8, "damage": 1.35, "level_bonus": 1,
			"lore": "Built to hold the bridges together. It decided long ago that the bridges are better off empty."},
		"boss": &"zephyrion",
		"usurper": {"id": &"aetherreach_usurper", "name": "The Unbound Gale", "title": "Usurper of the Reach", "enemy": &"storm_herald",
			"mods": [&"storm", &"swift"], "scale": 1.45, "hp": 3.0, "damage": 1.35, "level_bonus": 1,
			"lore": "Zephyrion's last breath, still blowing. It has found a shape and it likes it."},
	},
	&"eclipse": {
		"name": "The Eclipse Vault", "theme": &"eclipse", "orb": &"luna", "material": &"shadow_silk", "span": [100, 112],
		"blurb": "A vault built to hold a moon. Its keepers sealed the doors from the inside, and the dark has been patient.",
		"pools": {"a": [&"shade_stalker", &"mirage_weaver", &"gloomwraith", &"astral_duelist"],
			"b": [&"void_seer", &"mirror_knight", &"riftcaller", &"soulbound_twin"],
			"seal": [&"void_seer", &"mirage_weaver", &"soulbound_twin", &"shade_stalker", &"riftcaller"]},
		"music": &"dungeon_theme", "ambience": &"amb_arena", "footstep": &"stone", "reverb": 0.8,
		"miniboss": {"id": &"umbral_duelist", "name": "Seren of the Long Night", "title": "Champion of the Vault", "enemy": &"astral_duelist",
			"mods": [&"swift", &"cursed"], "scale": 1.3, "hp": 2.8, "damage": 1.35, "level_bonus": 1,
			"lore": "The last keeper still standing. She has not seen the sun in four hundred years and does not miss it."},
		"boss": &"nocthea",
		"usurper": {"id": &"eclipse_usurper", "name": "The Light Thief", "title": "Usurper of the Vault", "enemy": &"void_seer",
			"mods": [&"aether_infused", &"vampiric"], "scale": 1.45, "hp": 3.0, "damage": 1.35, "level_bonus": 1,
			"lore": "It drank the silver off Nocthea's rim as she fell. It is still thirsty."},
	},
	&"solarium": {
		"name": "The Drowned Solarium", "theme": &"solar", "orb": &"sol", "material": &"ember_core", "span": [106, 120],
		"blurb": "A sun-temple that sank into the sea and kept burning. Its halls are warm, flooded and full of light.",
		"pools": {"a": [&"cinder_imp", &"ashen_cultist", &"drowned_deckhand", &"slag_hound"],
			"b": [&"magma_golem", &"brinecaller", &"forge_thrall", &"ashen_acolyte", &"barnacle_hulk"],
			"seal": [&"magma_golem", &"brinecaller", &"forge_thrall", &"barnacle_hulk", &"slag_hound"]},
		"music": &"dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.6,
		"miniboss": {"id": &"brineforged", "name": "The Brineforged Colossus", "title": "Champion of the Solarium", "enemy": &"barnacle_hulk",
			"mods": [&"flaming", &"armored"], "scale": 1.3, "hp": 2.8, "damage": 1.35, "level_bonus": 1,
			"lore": "Half coral, half slag. It was a temple guard before the sea came in, and it still guards the stairs."},
		"boss": &"solmara",
		"usurper": {"id": &"solarium_usurper", "name": "The Tide-Burned Heir", "title": "Usurper of the Solarium", "enemy": &"magma_golem",
			"mods": [&"flaming", &"regenerating"], "scale": 1.5, "hp": 3.0, "damage": 1.35, "level_bonus": 1,
			"lore": "Solmara's ember, cooled by the sea into something that hates both."},
	},
}

const ORDER: Array[StringName] = [&"prismheart", &"underworld", &"aetherreach", &"eclipse", &"solarium"]

## Monster health and damage on top of the chosen difficulty.
const POWER := {"hp": 1.5, "damage": 1.3}

## Monster levels per floor: `span` spread evenly; each floor covers two levels, the sanctum is the last level only.
static func levels(span: Array, floors: int) -> Array:
	var lo := int(span[0])
	var hi := int(span[1])
	var out := []
	for i in floors:
		if i == floors - 1:
			out.append([hi, hi])
			continue
		var a := lo + roundi(float(i) * float(hi - lo) / float(maxi(1, floors - 1)))
		out.append([a, mini(a + 1, hi)])
	return out

## Gate position and facing on The Sundered Reach.
static func gate_spot(id: StringName) -> Dictionary:
	var a := deg_to_rad(float(GATE_ANGLES.get(id, 270.0)))
	var p := Vector2(cos(a), sin(a)) * GATE_RING
	return {"pos": p, "yaw": rad_to_deg(atan2(-p.x, -p.y))}

## The five dungeons with their generated floors, levels, gates and tier filled in.
static func list() -> Dictionary:
	var out := {}
	for id in ORDER:
		var d: Dictionary = (LIST[id] as Dictionary).duplicate()
		var floors: Array = DataDungeonPlansSpecial.PLANS.get(id, [])
		d["floors"] = floors
		d["levels"] = levels(d.span, floors.size())
		d["tier"] = TIER
		d["special"] = true
		d["min_tier"] = MIN_TIER
		d["power"] = POWER
		var g := gate_spot(id)
		d["surface"] = {"map": &"sundered_reach", "pos": g.pos, "yaw": g.yaw, "place": "sr_landing"}
		out[id] = d
	return out
