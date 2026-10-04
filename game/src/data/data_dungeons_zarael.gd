class_name DataDungeonsZarael
## bh-029: the three Vaults of Zarael — the "impossible" dungeons where the Heartwire's great lines cross. Kharvenn
## chain-priests drove their rune-chains in here at the Dimming; Aljay and Terax cleared them two winters ago; they woke
## again last winter. Each Vault's lord relights one ward pylon on the Bridge of Death (DataZarael.VAULT_FLAGS).
## Same shape as DataDungeonsSpecial (DataDungeons merges this list): `special` (no DungeonGrowth: authored levels and
## pools at every hero level), `zarael` (Zarael's own texts), `power`, `span`, `orb`. Floor plans are generated
## offline: `python tools/dungeon_gen/gen_plans.py --zarael` (DataDungeonPlansZarael), 7 floors each.
## Names are invented (no borrowed real-culture names — user rule).

## Every glow and rune light in the Vaults is white, like everywhere on Zarael (the user's call); torches stay firelight.
const TIER := 5

const THEMES := {
	&"jade": {
		"env": {"bg": Color(0.006, 0.016, 0.012), "ambient": Color(0.36, 0.5, 0.42), "ambient_energy": 1.5,
			"fog": Color(0.04, 0.12, 0.08), "fog_density": 0.004, "fog_height": 0.5, "fog_height_density": 0.12,
			"sun": Color(0.75, 0.95, 0.7), "sun_energy": 0.45, "sun_rot": Vector3(-60, 25, 0), "glow": 1.1,
			"exposure": 1.06, "contrast": 1.1, "saturation": 0.88},
		"stone": {"BH_Stone": ["jade_stone", Color(0.78, 0.86, 0.78)], "BH_StoneDark": ["glyph_stone", Color(0.42, 0.5, 0.44)]},
		"liquid": [Color(0.3, 0.85, 0.55), Color(0.01, 0.08, 0.05), 1.2], "mist": Color(0.5, 0.9, 0.6),
		"glow": Color(1.0, 1.0, 1.0), "torch": Color(1.0, 0.92, 0.8), "rune": Color(1.0, 1.0, 1.0),
	},
	&"obsidian": {
		"env": {"bg": Color(0.012, 0.008, 0.006), "ambient": Color(0.46, 0.38, 0.34), "ambient_energy": 1.5,
			"fog": Color(0.12, 0.06, 0.03), "fog_density": 0.004, "fog_height": 0.5, "fog_height_density": 0.12,
			"sun": Color(1.0, 0.72, 0.45), "sun_energy": 0.5, "sun_rot": Vector3(-58, 30, 0), "glow": 1.15,
			"exposure": 1.08, "contrast": 1.12, "saturation": 0.92},
		"stone": {"BH_Stone": ["obsidian", Color(0.8, 0.78, 0.8)], "BH_StoneDark": ["obsidian", Color(0.62, 0.57, 0.58)]},
		"liquid": [Color(1.0, 0.45, 0.12), Color(0.12, 0.02, 0.0), 2.2], "mist": Color(1.0, 0.6, 0.35),
		"glow": Color(1.0, 1.0, 1.0), "torch": Color(1.0, 0.65, 0.35), "rune": Color(1.0, 1.0, 1.0),
	},
	&"vein": {
		"env": {"bg": Color(0.014, 0.004, 0.01), "ambient": Color(0.48, 0.34, 0.4), "ambient_energy": 1.5,
			"fog": Color(0.12, 0.03, 0.07), "fog_density": 0.005, "fog_height": 0.6, "fog_height_density": 0.14,
			"sun": Color(1.0, 0.6, 0.75), "sun_energy": 0.4, "sun_rot": Vector3(-62, 20, 0), "glow": 1.15,
			"exposure": 1.08, "contrast": 1.12, "saturation": 0.85},
		"stone": {"BH_Stone": ["glyph_stone", Color(0.62, 0.5, 0.5)], "BH_StoneDark": ["blackwire_soil", Color(0.5, 0.38, 0.4)]},
		"liquid": [Color(0.85, 0.15, 0.4), Color(0.08, 0.0, 0.03), 1.6], "mist": Color(0.9, 0.35, 0.6),
		"glow": Color(1.0, 1.0, 1.0), "torch": Color(1.0, 0.92, 0.85), "rune": Color(1.0, 1.0, 1.0),
	},
}

## Room dressing per theme (same keys as dungeon.gd DRESS / CLUTTER / MapBuilder GATE_DRESS). Kit pieces from the
## Zarael kits (K1/K2) mixed with the shared dungeon kit. `gate_frame` is the Vault's own entrance structure.
const DRESS := {
	&"jade": {"corner": ["zr_serpent_statue", "zr_glyph_stele", "sarcophagus", "statue_small"], "floor": ["skull_pile", "candles_cluster", "rubble_pile"],
		"wall": ["zr_vine_curtain", "cobweb", "chains_hanging"], "basin": ["zr_ruin_column", "kelp_strands", "pillar_broken"], "breakable": "urn",
		"stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.1},
	&"obsidian": {"corner": ["zr_glass_growth", "lava_crucible", "basalt_column", "zr_chain_rack"], "floor": ["rubble_pile", "rock_small", "anvil"],
		"wall": ["chains_hanging", "zr_chain_spike"], "basin": ["basalt_column", "lava_crucible"], "breakable": "barrel",
		"stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.06},
	&"vein": {"corner": ["zr_glass_growth", "bones_scatter", "obelisk_corrupted", "zr_chain_spike"], "floor": ["bones_scatter", "skull_pile", "rubble_pile"],
		"wall": ["chains_hanging", "zr_vine_curtain"], "basin": ["zr_glass_growth", "obelisk_corrupted"], "breakable": "urn",
		"stairs": "stairs", "pillar": "pillar_quoin", "floor_light": 0.04},
}
const CLUTTER := {
	&"jade": ["urn", "zr_glyph_stele", "statue_small", "candles_cluster", "sarcophagus", "zr_ruin_column"],
	&"obsidian": ["zr_glass_growth", "barrel", "crate", "anvil", "zr_chain_rack", "rock_medium"],
	&"vein": ["zr_glass_growth", "bones_scatter", "skull_pile", "zr_chain_spike", "rock_medium"],
}
const GATE_DRESS := {
	&"jade": ["zr_gate_jade", "zr_serpent_statue", "zr_fern_giant"],
	&"obsidian": ["zr_gate_obsidian", "zr_glass_growth", "zr_rock_ochre_medium"],
	&"vein": ["zr_gate_vein", "zr_chain_spike", "zr_glass_growth"],
}

const LIST := {
	&"jade_sepulchre": {
		"name": "The Jade Sepulchre", "theme": &"jade", "orb": &"sora", "material": &"aether_shard", "span": [73, 80],
		"blurb": "The Wirewright kings sleep here in jade, where the first of the Heartwire's great lines crosses. They did not sleep quietly before the chains came; now they do not sleep at all.",
		"pools": {"a": [&"jade_sleeper", &"serpent_oracle", &"sepulchre_beetle", &"jade_sleeper"],
			"b": [&"jade_guardian", &"glyphbound_warrior", &"coil_shaman", &"serpent_oracle"],
			"seal": [&"jade_guardian", &"serpent_oracle", &"sepulchre_beetle", &"jade_sleeper", &"glyphbound_warrior"]},
		"music": &"dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.75,
		"miniboss": {"id": &"green_fire_regent", "name": "The Green-Fire Regent", "title": "Champion of the Sepulchre", "enemy": &"serpent_oracle",
			"mods": [&"aether_infused", &"vampiric"], "scale": 1.35, "hp": 2.6, "damage": 1.3, "level_bonus": 1,
			"lore": "Quorrath's high priest, buried beside the throne so the king would never lack for counsel. The counsel has turned."},
		"boss": &"jade_king",
		"usurper": {"id": &"jade_usurper", "name": "The Hollow Crown", "title": "Usurper of the Sepulchre", "enemy": &"jade_guardian",
			"mods": [&"armored", &"regenerating"], "scale": 1.45, "hp": 3.0, "damage": 1.3, "level_bonus": 1,
			"lore": "The king's last guard picked up the crown when Quorrath fell. It does not fit. It wears it anyway."},
	},
	&"obsidian_engine": {
		"name": "The Obsidian Engine", "theme": &"obsidian", "orb": &"sol", "material": &"ember_core", "span": [79, 86],
		"blurb": "The machine halls where the Wirewrights spun the Heartwire's current up from the island's heat. The chain-priests stoked the furnaces until the glass ran.",
		"pools": {"a": [&"stoker_thrall", &"shardcaster", &"relay_mote", &"wiresick_husk"],
			"b": [&"obsidian_golem", &"arc_sentinel", &"chain_priest", &"shardcaster"],
			"seal": [&"obsidian_golem", &"stoker_thrall", &"shardcaster", &"arc_sentinel", &"chain_priest"]},
		"music": &"dungeon_theme", "ambience": &"amb_temple", "footstep": &"stone", "reverb": 0.6,
		"miniboss": {"id": &"slag_overseer", "name": "The Slag Overseer", "title": "Champion of the Engine", "enemy": &"obsidian_golem",
			"mods": [&"flaming", &"armored"], "scale": 1.35, "hp": 2.6, "damage": 1.3, "level_bonus": 1,
			"lore": "It kept the furnaces fed for a thousand years. When the stokers ran out, it began feeding them in."},
		"boss": &"engine_heart",
		"usurper": {"id": &"engine_usurper", "name": "The Cinder Foreman", "title": "Usurper of the Engine", "enemy": &"stoker_thrall",
			"mods": [&"flaming", &"swift"], "scale": 1.5, "hp": 3.0, "damage": 1.3, "level_bonus": 1,
			"lore": "Kalvex's last stoker climbed into the dead furnace to keep warm. Something in it caught."},
	},
	&"veinworks": {
		"name": "The Veinworks", "theme": &"vein", "orb": &"luna", "material": &"shadow_silk", "span": [85, 93],
		"blurb": "Where the Wirewrights' tunnels reach the giant itself. The Heartwire runs here through bone, and the chains were driven into something that still has a pulse.",
		"pools": {"a": [&"marrow_hound", &"gigas_spawn", &"heartwire_wraith", &"wiresick_husk"],
			"b": [&"vein_knight", &"chain_bearer", &"chain_priest", &"gigas_spawn"],
			"seal": [&"vein_knight", &"marrow_hound", &"gigas_spawn", &"heartwire_wraith", &"chain_bearer"]},
		"music": &"dungeon_theme", "ambience": &"amb_catacombs", "footstep": &"stone", "reverb": 0.7,
		"miniboss": {"id": &"pulse_warden", "name": "The Pulse Warden", "title": "Champion of the Veinworks", "enemy": &"vein_knight",
			"mods": [&"cursed", &"regenerating"], "scale": 1.3, "hp": 2.6, "damage": 1.3, "level_bonus": 1,
			"lore": "A Wirewright engineer who went down to mend a line and never came back up. The giant mended him instead."},
		"boss": &"vein_mother",
		"usurper": {"id": &"vein_usurper", "name": "The Clotted King", "title": "Usurper of the Veinworks", "enemy": &"gigas_spawn",
			"mods": [&"vampiric", &"armored"], "scale": 1.5, "hp": 3.0, "damage": 1.3, "level_bonus": 1,
			"lore": "Ysvharn's last beat, hardened into a shape. It still remembers how to bleed you."},
	},
}

const ORDER: Array[StringName] = [&"jade_sepulchre", &"obsidian_engine", &"veinworks"]

## Monster health and damage on top of the chosen difficulty: "the most impossible dungeons" on Zarael.
const POWER := {"hp": 1.25, "damage": 1.1}

## Where each Vault's gate stands (map, local XZ, facing yaw in degrees, the DataIsland place it sits at).
const GATES := {
	&"jade_sepulchre": {"map": &"zr_coilwood", "pos": Vector2(96, -58), "yaw": 200.0, "place": "zc_jade"},
	&"obsidian_engine": {"map": &"zr_barrens", "pos": Vector2(-70, -64), "yaw": 160.0, "place": "zb_obsidian"},
	&"veinworks": {"map": &"zr_barrens", "pos": Vector2(84, 40), "yaw": 250.0, "place": "zb_vein"},
}

## The three Vaults with their generated floors, levels, gates and tier filled in.
static func list() -> Dictionary:
	var out := {}
	for id in ORDER:
		var d: Dictionary = (LIST[id] as Dictionary).duplicate()
		var floors: Array = DataDungeonPlansZarael.PLANS.get(id, [])
		d["floors"] = floors
		d["levels"] = DataDungeonsSpecial.levels(d.span, floors.size())
		d["tier"] = TIER
		d["special"] = true
		d["zarael"] = true
		d["min_tier"] = 0
		d["power"] = POWER
		d["surface"] = (GATES[id] as Dictionary).duplicate()
		out[id] = d
	return out
