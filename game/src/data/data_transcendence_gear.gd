class_name DataTranscendenceGear
## The thirty-six Class Transcendence gear bases: a signature weapon, an armor and an accessory for each advanced class
## (DataTranscendence). First-transcendence pieces ask for that class or either of its masters (lineage) from level 60;
## master pieces ask for exactly that master class from level 120. Nothing is handed out on advancing.
##
## Where they come from (both reachable the moment a hero can wear them):
##   1. The Grand Master's armory in every Guild House (DataShops `grand_master_armory`): every piece the hero's class
##      may wear, Elite rarity, for gold, restocked at once (infinite stock, the usual merchant prices and discounts).
##   2. Ordinary loot: monster, chest and Lape drops roll them like any base of their level (drop band 60 / 120; never
##      below it). Class-fit weighting offers a hero their own class's pieces; other branches' pieces can still drop and
##      be traded, sold or stored, but only their class can wear them.
## Weapons scale like every other weapon of their level (DataItems.roster_damage, then GearScaling with the item level);
## armor like every other armor (GearScaling). Each signature weapon carries one bounded class-skill bonus: +12%
## damage to one skill of its class (a `tskill_dmg_<skill>` flag, read by SkillRunner.make_request).

const SIGNATURE_BONUS := 0.12
const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC

## [id, name, identity, category, weapon type / weight, aps, element, element share, implicit [[stat, op, value]], skill bonus, icon]
const ROWS := [
	["tc_crownward_longsword", "Crownward Longsword", &"royal_guard", &"weapon", &"sword", 1.44, Elements.LIGHT, 0.15,
		[[&"block_strength", F, 0.05]], &"rg_bastion_rush", "sword_3"],
	["tc_royal_guard_cuirass", "Royal Guard Cuirass", &"royal_guard", &"armor", &"heavy", 0.0, 0, 0.0,
		[[&"block_chance", F, 0.04], [&"poise", I, 0.08]], &"", "armor_plate_3"],
	["tc_oathkeeper_seal", "Oathkeeper Seal", &"royal_guard", &"accessory", &"", 0.0, 0, 0.0,
		[[&"max_hp", I, 0.05], [&"valor_gain", I, 0.10]], &"", "ring_3"],
	["tc_dreadmarshal_greatsword", "Dreadmarshal Greatsword", &"dark_general", &"weapon", &"greatsword", 0.9, Elements.DARK, 0.25,
		[[&"dmg_dark", I, 0.10]], &"dg_dread_cleave", "greatsword_3"],
	["tc_black_dominion_plate", "Black Dominion Plate", &"dark_general", &"armor", &"heavy", 0.0, 0, 0.0,
		[[&"dmg_dark", I, 0.06], [&"knockback_res", F, 0.08]], &"", "armor_plate_3"],
	["tc_dread_command_signet", "Dread Command Signet", &"dark_general", &"accessory", &"", 0.0, 0, 0.0,
		[[&"crit_damage", F, 0.12], [&"valor_gain", I, 0.10]], &"", "ring_3"],
	["tc_dawnstar_longsword", "Dawnstar Longsword", &"grand_paladin", &"weapon", &"sword", 1.42, Elements.LIGHT, 0.25,
		[[&"healing", I, 0.08]], &"gp_dawn_verdict", "sword_3"],
	["tc_sanctified_plate", "Sanctified Plate", &"grand_paladin", &"armor", &"heavy", 0.0, 0, 0.0,
		[[&"res_light", F, 0.06], [&"res_dark", F, 0.06], [&"defense", I, 0.06]], &"", "armor_plate_3"],
	["tc_sunward_reliquary", "Sunward Reliquary", &"grand_paladin", &"accessory", &"", 0.0, 0, 0.0,
		[[&"healing", I, 0.10], [&"buff_effect", I, 0.08]], &"", "amulet_3"],
	["tc_trailkeeper_bow", "Trailkeeper Bow", &"tracker", &"weapon", &"bow", 1.05, 0, 0.0,
		[[&"accuracy", I, 0.08]], &"tr_trail_volley", "bow_3"],
	["tc_trackers_leathers", "Tracker's Leathers", &"tracker", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"evasion", I, 0.10], [&"focus_gain", I, 0.08]], &"", "armor_robe_3"],
	["tc_quarry_compass", "Quarry Compass", &"tracker", &"accessory", &"", 0.0, 0, 0.0,
		[[&"crit_chance", F, 0.02], [&"trap_damage", I, 0.10]], &"", "charm_2"],
	["tc_briarheart_bow", "Briarheart Bow", &"wildwarden", &"weapon", &"bow", 1.02, Elements.EARTH, 0.2,
		[[&"trap_damage", I, 0.10]], &"ww_living_thicket", "bow_3"],
	["tc_livingwood_leathers", "Livingwood Leathers", &"wildwarden", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"max_hp", I, 0.06], [&"status_res", F, 0.06]], &"", "armor_robe_3"],
	["tc_wildroot_pendant", "Wildroot Pendant", &"wildwarden", &"accessory", &"", 0.0, 0, 0.0,
		[[&"healing", I, 0.08], [&"max_hp", I, 0.04]], &"", "amulet_3"],
	["tc_starfall_crossbow", "Starfall Crossbow", &"starstrider", &"weapon", &"crossbow", 0.85, Elements.LIGHT, 0.2,
		[[&"projectile_damage", I, 0.08]], &"ss_astral_pierce", "bow_3"],
	["tc_constellation_leathers", "Constellation Leathers", &"starstrider", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"evasion", I, 0.08], [&"crit_damage", F, 0.08]], &"", "armor_robe_3"],
	["tc_comet_lens", "Comet Lens", &"starstrider", &"accessory", &"", 0.0, 0, 0.0,
		[[&"crit_chance", F, 0.025], [&"projectile_speed", I, 0.10]], &"", "charm_2"],
	["tc_runebound_staff", "Runebound Staff", &"arcanist", &"weapon", &"staff", 0.95, Elements.LIGHT, 1.0,
		[[&"magic_damage", I, 0.30]], &"ar_aether_lance", "staff_3"],
	["tc_arcanist_vestments", "Arcanist Vestments", &"arcanist", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"max_mana", I, 0.08], [&"mana_regen", I, 0.10]], &"", "armor_robe_3"],
	["tc_runic_focus", "Runic Focus", &"arcanist", &"accessory", &"", 0.0, 0, 0.0,
		[[&"mana_cost_reduction", F, 0.03], [&"cast_speed", I, 0.04]], &"", "charm_2"],
	["tc_prismatic_staff", "Prismatic Staff", &"archmage", &"weapon", &"staff", 0.98, Elements.LIGHTNING, 1.0,
		[[&"magic_damage", I, 0.40], [&"elemental_damage", I, 0.08]], &"am_prismatic_tempest", "staff_3"],
	["tc_archmage_robes", "Archmage Robes", &"archmage", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"elemental_damage", I, 0.06], [&"max_mana", I, 0.06]], &"", "armor_robe_3"],
	["tc_convergence_prism", "Convergence Prism", &"archmage", &"accessory", &"", 0.0, 0, 0.0,
		[[&"elemental_damage", I, 0.08], [&"cast_speed", I, 0.03]], &"", "amulet_3"],
	["tc_eventide_staff", "Eventide Staff", &"void_sovereign", &"weapon", &"staff", 0.95, Elements.DARK, 1.0,
		[[&"magic_damage", I, 0.40], [&"dmg_dark", I, 0.08]], &"vs_rift_collapse", "staff_3"],
	["tc_riftwoven_robes", "Riftwoven Robes", &"void_sovereign", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"dmg_dark", I, 0.06], [&"max_mana", I, 0.06]], &"", "armor_robe_3"],
	["tc_horizon_core", "Horizon Core", &"void_sovereign", &"accessory", &"", 0.0, 0, 0.0,
		[[&"pen_dark", F, 0.05], [&"mana_regen", I, 0.08]], &"", "charm_2"],
	["tc_gloamfang_dagger", "Gloamfang Dagger", &"nightstalker", &"weapon", &"dagger", 2.03, Elements.DARK, 0.2,
		[[&"crit_chance", F, 0.02]], &"ns_umbral_lunge", "dagger_3"],
	["tc_nightstalker_leathers", "Nightstalker Leathers", &"nightstalker", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"evasion", I, 0.10], [&"move_speed", I, 0.03]], &"", "armor_robe_3"],
	["tc_silent_trail_charm", "Silent Trail Charm", &"nightstalker", &"accessory", &"", 0.0, 0, 0.0,
		[[&"crit_damage", F, 0.10], [&"dodge_cooldown", F, -0.05]], &"", "charm_2"],
	["tc_wraithedge_dagger", "Wraithedge Dagger", &"phantom_reaper", &"weapon", &"dagger", 2.08, Elements.WIND, 0.15,
		[[&"crit_damage", F, 0.12]], &"pr_reapers_arc", "dagger_3"],
	["tc_afterimage_mantle", "Afterimage Mantle", &"phantom_reaper", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"evasion", I, 0.10], [&"dodge_cooldown", F, -0.05]], &"", "armor_robe_3"],
	["tc_reapers_glass", "Reaper's Glass", &"phantom_reaper", &"accessory", &"", 0.0, 0, 0.0,
		[[&"crit_chance", F, 0.025], [&"attack_speed", I, 0.04]], &"", "charm_2"],
	["tc_crimson_oath_dagger", "Crimson Oath Dagger", &"blood_sovereign", &"weapon", &"dagger", 1.96, 0, 0.0,
		[[&"life_leech", F, 0.02]], &"bs_crimson_rend", "dagger_3"],
	["tc_sanguine_leathers", "Sanguine Leathers", &"blood_sovereign", &"armor", &"cloth", 0.0, 0, 0.0,
		[[&"max_hp", I, 0.06], [&"healing", I, 0.05]], &"", "armor_robe_3"],
	["tc_bloodmoon_signet", "Bloodmoon Signet", &"blood_sovereign", &"accessory", &"", 0.0, 0, 0.0,
		[[&"dot_damage", I, 0.10], [&"life_leech", F, 0.01]], &"", "ring_3"],
]

const MAIN_ATTR := {&"knight": &"str", &"ranger": &"dex", &"mage": &"int", &"shadowblade": &"agi"}
## How often a base turns up in ordinary loot, next to the ~100 of an ordinary base (rare, not personal).
const DROP_WEIGHT := 25

static func bases() -> Array:
	var out := []
	for r in ROWS:
		var ident: StringName = r[2]
		var fam := DataTranscendence.family_of(ident)
		var stage := DataTranscendence.stage_of(ident)
		var level := DataTranscendence.level_for_stage(stage)
		var cat: StringName = r[3]
		var b := DataItems._b(StringName(r[0]), r[1], cat, String(r[10]), {
			"level_req": level, "drop_level": level, "class_hint": fam, "value": 300 + level * 12, "tier": 3,
			"drop_weight": DROP_WEIGHT, "requirements": {MAIN_ATTR[fam]: 12 + level} if cat != &"accessory" else {}})
		# the requirement: a first transcendence and both of its masters; a master class only itself
		b.class_req = {"kind": "lineage" if stage == 1 else "exact", "ids": [ident]}
		var mods: Array = []
		for m in r[8]:
			mods.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, float(m[2])))
		var skill: StringName = r[9]
		if skill != &"":
			mods.append(StatModifier.flat(StringName("flag_tskill_dmg_" + String(skill)), SIGNATURE_BONUS))
		b.implicit = mods
		match cat:
			&"weapon":
				b.weapon_type = StringName(r[4])
				b.attacks_per_second = float(r[5])
				var dmg := DataItems.roster_damage(b.weapon_type, level, b.attacks_per_second)
				b.damage_min = dmg.x * 1.06
				b.damage_max = dmg.y * 1.06
				b.element = int(r[6])
				b.element_share = float(r[7])
				b.weight = DataItems.default_weight(b)
				b.flavor = "%s signature weapon. +%d%% %s damage." % [DataTranscendence.name_of(ident), roundi(SIGNATURE_BONUS * 100.0), skill_title(skill)]
			&"armor":
				b.weight_class = StringName(r[4])
				b.defense = (12.0 + level * 1.5) * (1.0 if b.weight_class == &"heavy" else 0.6)
				b.weight = DataItems.default_weight(b)
				b.flavor = "Armor of the %s." % DataTranscendence.name_of(ident)
			_:
				b.flavor = "Worn by the %s." % DataTranscendence.name_of(ident)
		b.lore = String(DataTranscendence.info(ident).get("role", ""))
		# rendered icons: armours from their worn models (tools/blender/hero/hero_wear_icons.py), weapons and jewellery from
		# their item models (tools/blender/items/build_items.py, transcend_items.py)
		b.icon = DataItems.ICON3D % String(r[0])
		out.append(b)
	return out

## "Bastion Rush" for rg_bastion_rush (the database is still loading when bases are built).
static func skill_title(skill: StringName) -> String:
	return String(skill).substr(3).capitalize().replace("Reapers", "Reaper's")

## The Grand Master's armory stock: every piece, offered only to heroes whose class may wear it (Shop filters with
## ClassRequirements), Elite rarity, never sold out.
static func armory_fixed() -> Array:
	var out := []
	for r in ROWS:
		var stage := DataTranscendence.stage_of(r[2])
		out.append({"base": StringName(r[0]), "rarity": BH.Rarity.ELITE, "level_min": DataTranscendence.level_for_stage(stage),
			"infinite": true, "requires_class": true})
	return out

## Base ids of an identity's three pieces.
static func of_class(identity: StringName) -> Array:
	return (DataTranscendence.info(identity).get("gear", []) as Array).duplicate()

## Every documented source of a piece (machine-readable, for the gear manifest).
static func sources(base_id: StringName) -> Array:
	for r in ROWS:
		if StringName(r[0]) == base_id:
			var lvl := DataTranscendence.level_for_stage(DataTranscendence.stage_of(r[2]))
			return [{"kind": "shop", "id": "grand_master_armory", "npc": "grand_master_edran", "map": "int_guildhouse", "rarity": "Elite", "level": lvl},
				{"kind": "loot", "id": "ItemGenerator.random_base", "drop_level": lvl, "weight": DROP_WEIGHT,
					"note": "monster drops, dungeon chests, Lape's offers and relic caches roll it like any base of its level"}]
	return []
