class_name DataDungeonsAbyss
## bh-042: the five Abyss dungeons, levels 150-200, reached from the Delvers' Undercroft under Malasugue (interior
## int_delvers, docs/PLAN_bh-042.md phase 6-7). Same shape as DataDungeonsSpecial (DataDungeons merges this list), plus:
##   abyss      true: the darkest dungeons on Salmonan (few lit torches, no fill light, the hero carries a lantern —
##              DungeonRuntime), cracked walls hiding secret rooms (SecretWall), the Abyss loot table (Loot)
##   gatekeeper the boss holding floor 11 (its fall breaks that floor's seal)
##   wardens    named champions on floors 5, 10, 15 and 20 (DataDungeons.minibosses)
##   min_level  the gate turns away heroes below it
## Floor plans: DataDungeonPlansAbyss (tools/dungeon_gen/gen_abyss.py): 22 floors, storeys 0-3, secret rooms.
## Textures: Poly Haven CC0 sets (game/assets/textures/ph_*), props: Poly Haven (ph_*) and the project kit.
## Names are invented (no borrowed real-culture names — user rule).

const TIER := 7
const MIN_LEVEL := 140
## Monster health and damage on top of the difficulty (the Abyss rules already multiply damage x8 past level 90).
const POWER := {"hp": 1.5, "damage": 1.0}
## Lit torches a floor may carry (the bh-012 floors carry 30).
const MAX_TORCHES := 7

const _DARK_ENV := {"bg": Color(0.002, 0.002, 0.004), "ambient_energy": 0.62, "fog_density": 0.014, "fog_height": 1.2,
	"fog_height_density": 0.28, "sun_energy": 0.05, "sun_rot": Vector3(-66, 25, 0), "glow": 1.15, "exposure": 0.95,
	"contrast": 1.18, "saturation": 0.8}

static func _env(ambient: Color, fog: Color, sun: Color) -> Dictionary:
	var d := _DARK_ENV.duplicate()
	d["ambient"] = ambient
	d["fog"] = fog
	d["sun"] = sun
	return d

const THEMES_SRC := {
	&"hollow": {"ambient": Color(0.2, 0.21, 0.24), "fog": Color(0.02, 0.02, 0.025), "sun": Color(0.55, 0.58, 0.7),
		"stone": {"BH_Stone": ["ph_medieval_blocks_02", Color(0.62, 0.6, 0.58)], "BH_StoneDark": ["ph_castle_wall_slates", Color(0.36, 0.35, 0.36)]},
		"liquid": [Color(0.18, 0.2, 0.22), Color(0.0, 0.01, 0.01), 0.5], "mist": Color(0.4, 0.42, 0.48),
		"glow": Color(0.85, 0.75, 0.55), "torch": Color(1.0, 0.62, 0.3), "rune": Color(0.9, 0.82, 0.6)},
	&"sunless": {"ambient": Color(0.16, 0.22, 0.22), "fog": Color(0.01, 0.03, 0.03), "sun": Color(0.4, 0.6, 0.6),
		"stone": {"BH_Stone": ["ph_mossy_stone_wall", Color(0.55, 0.62, 0.58)], "BH_StoneDark": ["ph_seaworn_stone_tiles", Color(0.3, 0.36, 0.36)]},
		"liquid": [Color(0.03, 0.12, 0.11), Color(0.0, 0.02, 0.02), 0.85], "mist": Color(0.25, 0.45, 0.42),
		"glow": Color(0.25, 0.85, 0.75), "torch": Color(0.95, 0.6, 0.32), "rune": Color(0.3, 0.95, 0.85)},
	&"ashgrave": {"ambient": Color(0.24, 0.17, 0.14), "fog": Color(0.04, 0.015, 0.01), "sun": Color(0.8, 0.45, 0.3),
		"stone": {"BH_Stone": ["ph_castle_brick_07", Color(0.5, 0.42, 0.38)], "BH_StoneDark": ["ph_dark_rock", Color(0.3, 0.26, 0.24)]},
		"liquid": [Color(1.0, 0.32, 0.05), Color(0.2, 0.02, 0.0), 1.1], "mist": Color(0.6, 0.25, 0.08),
		"glow": Color(1.0, 0.4, 0.1), "torch": Color(1.0, 0.5, 0.2), "rune": Color(1.0, 0.45, 0.15)},
	&"weeping": {"ambient": Color(0.2, 0.23, 0.28), "fog": Color(0.03, 0.035, 0.05), "sun": Color(0.55, 0.65, 0.85),
		"stone": {"BH_Stone": ["ph_castle_brick_02_white", Color(0.6, 0.64, 0.7)], "BH_StoneDark": ["ph_rock_wall_08", Color(0.34, 0.37, 0.42)]},
		"liquid": [Color(0.4, 0.55, 0.7), Color(0.04, 0.08, 0.14), 0.4], "mist": Color(0.6, 0.7, 0.85),
		"glow": Color(0.6, 0.8, 1.0), "torch": Color(0.7, 0.82, 1.0), "rune": Color(0.6, 0.85, 1.0)},
	&"throne": {"ambient": Color(0.18, 0.15, 0.22), "fog": Color(0.02, 0.01, 0.03), "sun": Color(0.6, 0.45, 0.75),
		"stone": {"BH_Stone": ["ph_dark_rock_02", Color(0.42, 0.4, 0.44)], "BH_StoneDark": ["ph_rough_block_wall", Color(0.24, 0.22, 0.26)]},
		"liquid": [Color(0.35, 0.1, 0.6), Color(0.02, 0.0, 0.05), 1.2], "mist": Color(0.45, 0.25, 0.7),
		"glow": Color(0.7, 0.35, 1.0), "torch": Color(1.0, 0.45, 0.3), "rune": Color(0.75, 0.4, 1.0)},
}

static var _themes := {}

## The five themes in DataDungeons' shape (env, stone, liquid, mist, glow, torch, rune), all very dark.
static func themes() -> Dictionary:
	if _themes.is_empty():
		for id in THEMES_SRC:
			var s: Dictionary = THEMES_SRC[id]
			var t := s.duplicate()
			t["env"] = _env(s.ambient, s.fog, s.sun)
			t["dark"] = true
			t["max_torches"] = MAX_TORCHES
			_themes[id] = t
	return _themes

## Room dressing per theme (dungeon.gd DRESS keys). ph_* pieces are Poly Haven CC0 props.
const DRESS := {
	&"hollow": {"corner": ["sarcophagus", "ph_gothic_statue", "statue_knight", "coffin", "ph_marble_bust_01"],
		"floor": ["bones_scatter", "skull_pile", "candles_cluster", "rubble_spill"], "wall": ["chains_hanging", "cobweb", "banner_torn", "ph_lion_head"],
		"basin": ["coffin", "skull_pile", "statue_collapsed"], "breakable": "urn", "stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.0},
	&"sunless": {"corner": ["ph_rock_moss_set_01", "statue_collapsed", "kd_coffin_old", "ph_rock_07"],
		"floor": ["bones_scatter", "rubble_spill", "kd_hanging_moss"], "wall": ["chains_hanging", "ph_lion_head", "cobweb"],
		"basin": ["ph_rock_07", "kd_rowboat", "statue_collapsed", "pillar_broken"], "breakable": "urn", "stairs": "stairs", "pillar": "pillar_quoin",
		"floor_light": 0.0},
	&"ashgrave": {"corner": ["forge_furnace", "anvil", "ph_stone_fire_pit", "weapon_rack", "armor_stand"],
		"floor": ["weapons_discarded", "rubble_spill", "bones_scatter"], "wall": ["chains_hanging", "ph_kite_shield", "ph_ornate_medieval_mace"],
		"basin": ["rock_medium", "rubble_pile"], "breakable": "urn", "stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.0},
	&"weeping": {"corner": ["frozen_coffin", "ice_crystal_large", "statue_knight", "ph_gothic_statue", "armor_stand"],
		"floor": ["ice_crystal_small", "bones_scatter", "rubble_spill"], "wall": ["banner_torn", "chains_hanging", "ph_kite_shield"],
		"basin": ["ice_crystal_large", "ice_crystal_small"], "breakable": "urn", "stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.0},
	&"throne": {"corner": ["obelisk_corrupted", "ph_gothic_statue", "statue_knight", "throne", "sarcophagus"],
		"floor": ["bones_scatter", "skull_pile", "rubble_spill", "candles_cluster"], "wall": ["chains_hanging", "banner_torn", "ph_lion_head"],
		"basin": ["obelisk_corrupted", "statue_collapsed"], "breakable": "urn", "stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.0},
}
const CLUTTER := {
	&"hollow": ["coffin", "sarcophagus", "urn", "skull_pile", "candles_cluster", "lectern", "ph_brass_candleholders", "kd_coffin_old"],
	&"sunless": ["kd_crate", "kd_barrel", "urn", "ph_rock_07", "bones_scatter", "kd_debris_stone"],
	&"ashgrave": ["anvil", "weapon_rack", "kd_crate", "urn", "ph_stone_fire_pit", "weapons_discarded"],
	&"weeping": ["frozen_coffin", "armor_stand", "weapon_display", "urn", "ice_crystal_small", "kd_bench"],
	&"throne": ["obelisk_corrupted", "statue_small", "urn", "ph_brass_goblets", "kd_chalice", "candles_cluster"],
}
const GATE_DRESS := {
	&"hollow": ["ph_large_iron_gate", "ph_gothic_statue", "skull_pile"],
	&"sunless": ["ph_large_iron_gate", "ph_rock_moss_set_01", "kd_hanging_moss"],
	&"ashgrave": ["ph_large_iron_gate", "forge_furnace", "rubble_pile"],
	&"weeping": ["ph_large_iron_gate", "statue_knight", "ice_crystal_small"],
	&"throne": ["ph_large_iron_gate", "obelisk_corrupted", "skull_pile"],
}

## Where the five gates stand in the Delvers' Undercroft (int_delvers, map-local x/z and facing).
const GATES := {&"hollow_crown": [Vector2(-12.5, -4.5), 90.0], &"sunless_cistern": [Vector2(-12.5, 5.5), 90.0],
	&"ashgrave_foundry": [Vector2(0.0, -8.5), 0.0], &"weeping_bastion": [Vector2(12.5, -4.5), -90.0], &"throne_beneath": [Vector2(12.5, 5.5), -90.0]}

static func _warden(id: String, name: String, title: String, enemy: StringName, mods: Array, scale: float, lore: String) -> Dictionary:
	return {"id": StringName(id), "name": name, "title": title, "enemy": enemy, "mods": mods, "scale": scale, "hp": 3.4, "damage": 1.3,
		"level_bonus": 2, "lore": lore}

const LIST := {
	&"hollow_crown": {
		"name": "The Vaults of the Hollow Crown", "theme": &"hollow", "orb": &"luna", "material": &"shadow_silk", "span": [150, 162],
		"blurb": "Under Malasugue lie the kings who came before it. The Abyss opened beneath their crypt, and their court got up to meet it.",
		"pools": {"a": [&"hollow_soldier", &"forsaken_legionnaire", &"grave_archer", &"bonewarden"],
			"b": [&"necromancer", &"gravecaller", &"frost_revenant", &"forsaken_chainguard", &"ghoul_brute"],
			"seal": [&"forsaken_chainguard", &"necromancer", &"bonewarden", &"gravecaller", &"forsaken_legionnaire"]},
		"music": &"dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.85,
		"gatekeeper": &"flayed_archivist", "boss": &"morvhaal",
		"miniboss": {"id": &"crown_herald", "name": "The Herald of Bones", "title": "Champion of the Hollow Crown", "enemy": &"forsaken_chainguard",
			"mods": [&"armored", &"cursed"], "scale": 1.5, "hp": 3.6, "damage": 1.35, "level_bonus": 2,
			"lore": "He announced every king who came down these stairs. He is waiting to announce you."},
		"usurper": {"id": &"hollow_crown_usurper", "name": "The Pretender in Bone", "title": "Usurper of the Hollow Crown", "enemy": &"bonewarden",
			"mods": [&"armored", &"regenerating"], "scale": 1.6, "hp": 3.8, "damage": 1.35, "level_bonus": 2,
			"lore": "Morvhaal's crown fell; something with no right to it picked it up."},
		"wardens": [["crown_warden_5", "The Candle Warden", &"gravecaller", [&"cursed", &"aether_infused"], 1.4],
			["crown_warden_10", "Sir Hollowmail", &"forsaken_legionnaire", [&"armored", &"berserker"], 1.5],
			["crown_warden_15", "The Weeping Priest", &"necromancer", [&"vampiric", &"cursed"], 1.45],
			["crown_warden_20", "The Ossuary Hound", &"ghoul_brute", [&"swift", &"regenerating"], 1.5]],
	},
	&"sunless_cistern": {
		"name": "The Sunless Cistern", "theme": &"sunless", "orb": &"airah", "material": &"tide_pearl", "span": [158, 172],
		"blurb": "The old waterworks run under the whole island. Somewhere at the bottom the water stopped draining, and started climbing.",
		"pools": {"a": [&"drowned_deckhand", &"reef_crawler", &"shade_stalker", &"gloomwraith"],
			"b": [&"brinecaller", &"barnacle_hulk", &"bloodbinder", &"void_seer"],
			"seal": [&"barnacle_hulk", &"brinecaller", &"bloodbinder", &"drowned_deckhand", &"shade_stalker"]},
		"music": &"dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.9,
		"gatekeeper": &"ysolde", "boss": &"thalassor",
		"miniboss": {"id": &"cistern_keeper", "name": "The Sluice-Keeper", "title": "Champion of the Sunless Cistern", "enemy": &"barnacle_hulk",
			"mods": [&"armored", &"frozen"], "scale": 1.45, "hp": 3.6, "damage": 1.35, "level_bonus": 2,
			"lore": "It kept the gates of the lowest weir until the water closed over its head. It still works the wheel."},
		"usurper": {"id": &"sunless_cistern_usurper", "name": "The Silt Sovereign", "title": "Usurper of the Cistern", "enemy": &"brinecaller",
			"mods": [&"vampiric", &"storm"], "scale": 1.5, "hp": 3.8, "damage": 1.35, "level_bonus": 2,
			"lore": "What lived in Thalassor's reef found the basin empty, and settled in."},
		"wardens": [["cistern_warden_5", "The Drowned Bellman", &"drowned_deckhand", [&"swift", &"vampiric"], 1.5],
			["cistern_warden_10", "Mother of Eels", &"brinecaller", [&"storm", &"cursed"], 1.45],
			["cistern_warden_15", "The Reef Knight", &"barnacle_hulk", [&"armored", &"shielded"], 1.4],
			["cistern_warden_20", "The Blind Diver", &"shade_stalker", [&"swift", &"berserker"], 1.5]],
	},
	&"ashgrave_foundry": {
		"name": "The Ashgrave Foundry", "theme": &"ashgrave", "orb": &"sol", "material": &"ember_core", "span": [166, 182],
		"blurb": "A foundry dug below the world to cast weapons for a war no one remembers. The fires went out. Something lit them again.",
		"pools": {"a": [&"cinder_imp", &"slag_hound", &"forge_thrall", &"ashen_cultist"],
			"b": [&"magma_golem", &"ashen_acolyte", &"stoker_thrall", &"rune_golem"],
			"seal": [&"magma_golem", &"forge_thrall", &"stoker_thrall", &"ashen_acolyte", &"slag_hound"]},
		"music": &"fire_dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.6,
		"gatekeeper": &"gorehelm", "boss": &"kharzul",
		"miniboss": {"id": &"foundry_master", "name": "The Pour-Master", "title": "Champion of the Ashgrave Foundry", "enemy": &"magma_golem",
			"mods": [&"flaming", &"armored"], "scale": 1.5, "hp": 3.6, "damage": 1.35, "level_bonus": 2,
			"lore": "It was cast to run the crucibles. It runs them still, and the metal it pours is red with more than heat."},
		"usurper": {"id": &"ashgrave_foundry_usurper", "name": "The Cinder Heir", "title": "Usurper of the Foundry", "enemy": &"stoker_thrall",
			"mods": [&"flaming", &"berserker"], "scale": 1.6, "hp": 3.8, "damage": 1.35, "level_bonus": 2,
			"lore": "Kharzul's last pour cooled into a smaller tyrant with the same temper."},
		"wardens": [["foundry_warden_5", "The Bellows-Hound", &"slag_hound", [&"flaming", &"swift"], 1.6],
			["foundry_warden_10", "The Ash Deacon", &"ashen_acolyte", [&"cursed", &"flaming"], 1.45],
			["foundry_warden_15", "The Quench Golem", &"rune_golem", [&"armored", &"frozen"], 1.4],
			["foundry_warden_20", "Old Clinker", &"forge_thrall", [&"berserker", &"regenerating"], 1.5]],
	},
	&"weeping_bastion": {
		"name": "The Weeping Bastion", "theme": &"weeping", "orb": &"luna", "material": &"frost_crystal", "span": [174, 190],
		"blurb": "A fortress built to hold the cold back from the world. Its walls held. Its defenders did not.",
		"pools": {"a": [&"rime_husk", &"ice_wraith", &"barrow_jarl", &"gloomwraith"],
			"b": [&"frost_revenant", &"rime_weaver", &"mirror_knight", &"gravecaller"],
			"seal": [&"frost_revenant", &"barrow_jarl", &"mirror_knight", &"rime_weaver", &"rime_husk"]},
		"music": &"ice_dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.75,
		"gatekeeper": &"weeping_shroud", "boss": &"rimehorn",
		"miniboss": {"id": &"bastion_marshal", "name": "The Frost-Marshal", "title": "Champion of the Weeping Bastion", "enemy": &"barrow_jarl",
			"mods": [&"frozen", &"shielded"], "scale": 1.55, "hp": 3.6, "damage": 1.35, "level_bonus": 2,
			"lore": "He gave the last order: hold. Then the cold came through, and he held."},
		"usurper": {"id": &"weeping_bastion_usurper", "name": "The Snow-Crowned Gaoler", "title": "Usurper of the Bastion", "enemy": &"frost_revenant",
			"mods": [&"frozen", &"vampiric"], "scale": 1.55, "hp": 3.8, "damage": 1.35, "level_bonus": 2,
			"lore": "The bastion's gaoler kept Rimehorn's key. With the cell empty, he has taken the whole keep."},
		"wardens": [["bastion_warden_5", "The Widow-Watch", &"ice_wraith", [&"frozen", &"swift"], 1.5],
			["bastion_warden_10", "Sergeant Rimejaw", &"rime_husk", [&"armored", &"berserker"], 1.6],
			["bastion_warden_15", "The Mirror Sentry", &"mirror_knight", [&"shielded", &"aether_infused"], 1.4],
			["bastion_warden_20", "The Frost Chaplain", &"gravecaller", [&"frozen", &"cursed"], 1.45]],
	},
	&"throne_beneath": {
		"name": "The Throne Beneath", "theme": &"throne", "orb": &"sora", "material": &"aether_shard", "span": [186, 200],
		"blurb": "At the bottom of the Abyss stands a throne no one has ever been seen to sit on. A whole company went down to look. One came back up.",
		"pools": {"a": [&"shade_stalker", &"void_seer", &"soulbound_twin", &"astral_duelist"],
			"b": [&"riftcaller", &"mirage_weaver", &"chain_bearer", &"leash_knight", &"vein_knight"],
			"seal": [&"chain_bearer", &"leash_knight", &"vein_knight", &"riftcaller", &"void_seer"]},
		"music": &"dungeon_theme", "ambience": &"amb_arena", "footstep": &"stone", "reverb": 0.9,
		"gatekeeper": &"fallen_necro_knight", "boss": &"vaelgor",
		"miniboss": {"id": &"throne_herald", "name": "The Kneeling Herald", "title": "Champion of the Throne Beneath", "enemy": &"vein_knight",
			"mods": [&"cursed", &"vampiric"], "scale": 1.55, "hp": 3.6, "damage": 1.35, "level_bonus": 2,
			"lore": "It has knelt at the foot of the stair for so long that it has forgotten how to stand. It has not forgotten how to fight."},
		"usurper": {"id": &"throne_beneath_usurper", "name": "The One Who Sat", "title": "Usurper of the Throne", "enemy": &"chain_bearer",
			"mods": [&"aether_infused", &"armored"], "scale": 1.65, "hp": 3.8, "damage": 1.35, "level_bonus": 2,
			"lore": "Vaelgor is gone and the throne is empty. Someone always sits down."},
		"wardens": [["throne_warden_5", "The Oathless Squire", &"astral_duelist", [&"swift", &"cursed"], 1.4],
			["throne_warden_10", "The Mirror of Names", &"mirage_weaver", [&"aether_infused", &"vampiric"], 1.45],
			["throne_warden_15", "The Rift-Abbess", &"riftcaller", [&"storm", &"cursed"], 1.45],
			["throne_warden_20", "The Chain That Waits", &"chain_bearer", [&"armored", &"berserker"], 1.55]],
	},
}

const ORDER: Array[StringName] = [&"hollow_crown", &"sunless_cistern", &"ashgrave_foundry", &"weeping_bastion", &"throne_beneath"]
const WARDEN_FLOORS := [5, 10, 15, 20]
const GATEKEEPER_FLOOR := 11

static func is_abyss(id: StringName) -> bool:
	return LIST.has(id)

## The five dungeons with their generated floors, levels, gates and tier filled in.
static func list() -> Dictionary:
	var out := {}
	for id in ORDER:
		var d: Dictionary = (LIST[id] as Dictionary).duplicate(true)
		var floors: Array = DataDungeonPlansAbyss.PLANS.get(id, [])
		d["floors"] = floors
		d["levels"] = DataDungeonsSpecial.levels(d.span, floors.size())
		d["tier"] = TIER
		d["special"] = true
		d["abyss"] = true
		d["min_level"] = MIN_LEVEL
		d["power"] = POWER
		var g: Array = GATES[id]
		d["surface"] = {"map": &"int_delvers", "pos": g[0], "yaw": float(g[1]), "place": "delvers"}
		var w := []
		for row in d.wardens:
			w.append(_warden(row[0], row[1], "Warden of %s" % String(d.name).trim_prefix("The "), row[2], row[3], float(row[4]),
				"One of the things that keep %s. It does not let heroes pass for nothing." % String(d.name).to_lower()))
		d["wardens"] = w
		out[id] = d
	return out

## The warden standing on floor `n` (5, 10, 15, 20) of an Abyss dungeon, or {}.
static func warden_of(dd: Dictionary, n: int) -> Dictionary:
	var i := WARDEN_FLOORS.find(n)
	if i < 0 or not dd.has("wardens") or i >= (dd.wardens as Array).size():
		return {}
	return dd.wardens[i]
