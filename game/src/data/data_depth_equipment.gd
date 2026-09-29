class_name DataDepthEquipment
## Generated catalog; edit tools/blender/items/depth_catalog.py and regenerate.
## 64 weapons and 16 armor pieces; eight named relics have guaranteed functional powers.
const ROWS := [
	["depth_copperleaf_backsword", "Copperleaf Backsword", "sword", "knight", 25, 1.305, 0, "stagger_power", 0.12, "", 2.82],
	["depth_saltglass_cutlass", "Saltglass Cutlass", "sword", "knight", 28, 1.363, 6, "crit_chance", 0.025, "", 3.0],
	["depth_rootguard_falchion", "Rootguard Falchion", "sword", "knight", 32, 1.421, 1, "status_power", 0.12, "", 3.18],
	["depth_lantern_rapier", "Lantern Rapier", "sword", "knight", 35, 1.479, 2, "pen_armor", 0.04, "", 3.36],
	["depth_cinderhook_saber", "Cinderhook Saber", "sword", "knight", 38, 1.537, 0, "stagger_power", 0.12, "", 3.54],
	["depth_frostbell_broadsword", "Frostbell Broadsword", "sword", "knight", 41, 1.595, 7, "crit_chance", 0.025, "", 3.72],
	["depth_hollowfin_estoc", "Hollowfin Estoc", "sword", "knight", 44, 1.305, 8, "status_power", 0.12, "", 3.9],
	["depth_moonwell_flamberge", "Moonwell Flamberge", "sword", "knight", 47, 1.363, 7, "pen_armor", 0.04, "", 4.08],
	["depth_starfall_spatha", "Starfall Spatha", "sword", "knight", 50, 1.421, 0, "stagger_power", 0.12, "", 4.26],
	["depth_deepwatch_messer", "Deepwatch Messer", "sword", "knight", 53, 1.479, 6, "crit_chance", 0.025, "", 4.44],
	["depth_sunken_oathblade", "Sunken Oathblade", "sword", "knight", 56, 1.537, 1, "status_power", 0.12, "", 4.62],
	["depth_crownless_longsword", "Crownless Longsword", "sword", "knight", 60, 1.595, 2, "pen_armor", 0.04, "", 4.8],
	["depth_basalt_zweihander", "Basalt Zweihander", "greatsword", "knight", 25, 0.828, 0, "stagger_power", 0.12, "", 7.05],
	["depth_briar_executioner", "Briar Executioner", "greatsword", "knight", 35, 0.865, 6, "crit_chance", 0.025, "", 7.51],
	["depth_astral_greatblade", "Astral Greatblade", "greatsword", "knight", 50, 0.902, 1, "status_power", 0.12, "", 7.96],
	["depth_vaultbreaker_claymore", "Vaultbreaker Claymore", "greatsword", "knight", 60, 0.938, 2, "pen_armor", 0.04, "", 8.41],
	["depth_glowcap_crook", "Glowcap Crook", "staff", "mage", 25, 0.9, 4, "stagger_power", 0.12, "", 2.99],
	["depth_tidal_forkstaff", "Tidal Forkstaff", "staff", "mage", 30, 0.94, 6, "crit_chance", 0.025, "", 3.18],
	["depth_cinder_lanternstaff", "Cinder Lanternstaff", "staff", "mage", 35, 0.98, 1, "status_power", 0.12, "", 3.37],
	["depth_rime_shardstaff", "Rime Shardstaff", "staff", "mage", 40, 1.02, 2, "pen_armor", 0.04, "", 3.56],
	["depth_thornseed_branchstaff", "Thornseed Branchstaff", "staff", "mage", 45, 1.06, 4, "stagger_power", 0.12, "", 3.75],
	["depth_orrery_starstaff", "Orrery Starstaff", "staff", "mage", 50, 1.1, 7, "crit_chance", 0.025, "", 3.94],
	["depth_voidcage_scepter", "Voidcage Scepter", "staff", "mage", 55, 0.9, 8, "status_power", 0.12, "", 4.13],
	["depth_dawnspire_staff", "Dawnspire Staff", "staff", "mage", 60, 0.94, 7, "pen_armor", 0.04, "", 4.32],
	["depth_sporebud_wand", "Sporebud Wand", "wand", "mage", 25, 1.44, 4, "stagger_power", 0.12, "", 0.83],
	["depth_shellsong_wand", "Shellsong Wand", "wand", "mage", 30, 1.504, 6, "crit_chance", 0.025, "", 0.88],
	["depth_embercrown_wand", "Embercrown Wand", "wand", "mage", 35, 1.568, 1, "status_power", 0.12, "", 0.94],
	["depth_icepetal_wand", "Icepetal Wand", "wand", "mage", 40, 1.632, 2, "pen_armor", 0.04, "", 0.99],
	["depth_gravebell_wand", "Gravebell Wand", "wand", "mage", 45, 1.696, 4, "stagger_power", 0.12, "", 1.04],
	["depth_moonhook_wand", "Moonhook Wand", "wand", "mage", 50, 1.76, 7, "crit_chance", 0.025, "", 1.09],
	["depth_prismcoil_wand", "Prismcoil Wand", "wand", "mage", 55, 1.44, 8, "status_power", 0.12, "", 1.15],
	["depth_sunwheel_wand", "Sunwheel Wand", "wand", "mage", 60, 1.504, 7, "pen_armor", 0.04, "", 1.2],
	["depth_rootbend_shortbow", "Rootbend Shortbow", "bow", "ranger", 25, 0.972, 0, "stagger_power", 0.12, "", 2.16],
	["depth_saltwind_recurve", "Saltwind Recurve", "bow", "ranger", 30, 1.015, 6, "crit_chance", 0.025, "", 2.3],
	["depth_cinderhorn_bow", "Cinderhorn Bow", "bow", "ranger", 35, 1.058, 1, "status_power", 0.12, "", 2.43],
	["depth_icebranch_longbow", "Icebranch Longbow", "bow", "ranger", 40, 1.102, 2, "pen_armor", 0.04, "", 2.57],
	["depth_thornwing_bow", "Thornwing Bow", "bow", "ranger", 45, 1.145, 0, "stagger_power", 0.12, "", 2.71],
	["depth_starbridge_bow", "Starbridge Bow", "bow", "ranger", 50, 1.188, 7, "crit_chance", 0.025, "", 2.85],
	["depth_nightglass_warbow", "Nightglass Warbow", "bow", "ranger", 55, 0.972, 8, "status_power", 0.12, "", 2.98],
	["depth_dawnfeather_bow", "Dawnfeather Bow", "bow", "ranger", 60, 1.015, 7, "pen_armor", 0.04, "", 3.12],
	["depth_sporeleaf_javelin", "Sporeleaf Javelin", "javelin", "ranger", 25, 1.062, 0, "stagger_power", 0.12, "", 1.91],
	["depth_keelspike_javelin", "Keelspike Javelin", "javelin", "ranger", 30, 1.109, 6, "crit_chance", 0.025, "", 2.03],
	["depth_furnace_barb", "Furnace Barb", "javelin", "ranger", 35, 1.156, 1, "status_power", 0.12, "", 2.15],
	["depth_rimefork_javelin", "Rimefork Javelin", "javelin", "ranger", 40, 1.204, 2, "pen_armor", 0.04, "", 2.27],
	["depth_briarfin_javelin", "Briarfin Javelin", "javelin", "ranger", 45, 1.251, 0, "stagger_power", 0.12, "", 2.4],
	["depth_starshard_javelin", "Starshard Javelin", "javelin", "ranger", 50, 1.298, 7, "crit_chance", 0.025, "", 2.52],
	["depth_gloomspear", "Gloomspear", "javelin", "ranger", 55, 1.062, 8, "status_power", 0.12, "", 2.64],
	["depth_suncrest_javelin", "Suncrest Javelin", "javelin", "ranger", 60, 1.109, 7, "pen_armor", 0.04, "", 2.76],
	["depth_rootfang_skinner", "Rootfang Skinner", "dagger", "shadowblade", 25, 1.8, 0, "stagger_power", 0.12, "", 1.0],
	["depth_keelhook_knife", "Keelhook Knife", "dagger", "shadowblade", 30, 1.88, 6, "crit_chance", 0.025, "", 1.06],
	["depth_emberwave_kris", "Emberwave Kris", "dagger", "shadowblade", 35, 1.96, 1, "status_power", 0.12, "", 1.12],
	["depth_iceglass_stiletto", "Iceglass Stiletto", "dagger", "shadowblade", 40, 2.04, 2, "pen_armor", 0.04, "", 1.19],
	["depth_briar_talon", "Briar Talon", "dagger", "shadowblade", 45, 2.12, 0, "stagger_power", 0.12, "", 1.25],
	["depth_moonfang_kukri", "Moonfang Kukri", "dagger", "shadowblade", 50, 2.2, 7, "crit_chance", 0.025, "", 1.31],
	["depth_voidpetal_dagger", "Voidpetal Dagger", "dagger", "shadowblade", 55, 1.8, 8, "status_power", 0.12, "", 1.38],
	["depth_dawnthorn_knife", "Dawnthorn Knife", "dagger", "shadowblade", 60, 1.88, 7, "pen_armor", 0.04, "", 1.44],
	["depth_rootrake_claws", "Rootrake Claws", "claw", "shadowblade", 25, 1.665, 0, "stagger_power", 0.12, "", 1.49],
	["depth_keelgrip_talons", "Keelgrip Talons", "claw", "shadowblade", 30, 1.739, 6, "crit_chance", 0.025, "", 1.59],
	["depth_furnace_knives", "Furnace Knives", "claw", "shadowblade", 35, 1.813, 1, "status_power", 0.12, "", 1.68],
	["depth_rimefang_claws", "Rimefang Claws", "claw", "shadowblade", 40, 1.887, 2, "pen_armor", 0.04, "", 1.78],
	["depth_briarhook_claws", "Briarhook Claws", "claw", "shadowblade", 45, 1.961, 0, "stagger_power", 0.12, "", 1.88],
	["depth_starweb_talons", "Starweb Talons", "claw", "shadowblade", 50, 2.035, 7, "crit_chance", 0.025, "", 1.97],
	["depth_voidreaver_claws", "Voidreaver Claws", "claw", "shadowblade", 55, 1.665, 8, "status_power", 0.12, "", 2.07],
	["depth_dawnrake_claws", "Dawnrake Claws", "claw", "shadowblade", 60, 1.739, 7, "pen_armor", 0.04, "", 2.16],
	["depth_deepwarden_coat", "Deepwarden Coat", "armor", "knight", 25, 0, 0, "max_hp", 35.0, "valorous", 0],
	["depth_deepwarden_crown", "Deepwarden Crown", "helm", "knight", 38, 0, 0, "max_hp", 35.0, "", 0],
	["depth_deepwarden_grips", "Deepwarden Grips", "gloves", "knight", 50, 0, 0, "max_hp", 35.0, "echoing_guard", 0],
	["depth_deepwarden_treads", "Deepwarden Treads", "boots", "knight", 60, 0, 0, "max_hp", 35.0, "", 0],
	["depth_prismkeeper_coat", "Prismkeeper Coat", "armor", "mage", 25, 0, 0, "max_mana", 24.0, "overflow", 0],
	["depth_prismkeeper_crown", "Prismkeeper Crown", "helm", "mage", 38, 0, 0, "max_mana", 24.0, "", 0],
	["depth_prismkeeper_grips", "Prismkeeper Grips", "gloves", "mage", 50, 0, 0, "max_mana", 24.0, "frostbite", 0],
	["depth_prismkeeper_treads", "Prismkeeper Treads", "boots", "mage", 60, 0, 0, "max_mana", 24.0, "", 0],
	["depth_vaultpath_coat", "Vaultpath Coat", "armor", "ranger", 25, 0, 0, "evasion", 20.0, "m_frostguard", 0],
	["depth_vaultpath_crown", "Vaultpath Crown", "helm", "ranger", 38, 0, 0, "evasion", 20.0, "", 0],
	["depth_vaultpath_grips", "Vaultpath Grips", "gloves", "ranger", 50, 0, 0, "evasion", 20.0, "a_crit_lightning", 0],
	["depth_vaultpath_treads", "Vaultpath Treads", "boots", "ranger", 60, 0, 0, "evasion", 20.0, "", 0],
	["depth_gloomthread_coat", "Gloomthread Coat", "armor", "shadowblade", 25, 0, 0, "move_speed", 0.12, "bloodthirst", 0],
	["depth_gloomthread_crown", "Gloomthread Crown", "helm", "shadowblade", 38, 0, 0, "move_speed", 0.12, "", 0],
	["depth_gloomthread_grips", "Gloomthread Grips", "gloves", "shadowblade", 50, 0, 0, "move_speed", 0.12, "relentless", 0],
	["depth_gloomthread_treads", "Gloomthread Treads", "boots", "shadowblade", 60, 0, 0, "move_speed", 0.12, "", 0]
]

static func bases() -> Array:
	var out := []
	for r in ROWS:
		var weapon: bool = r[2] in ["sword", "greatsword", "staff", "wand", "bow", "javelin", "dagger", "claw"]
		var cls := StringName(r[3])
		var level := int(r[4])
		var attr: StringName = &"str" if cls == &"knight" else (&"int" if cls == &"mage" else &"dex")
		var req := {attr: 12 + level}
		var b := DataItems._b(StringName(r[0]), r[1], &"weapon" if weapon else StringName(r[2]), "", {
			"level_req": level, "drop_level": level, "class_hint": cls, "requirements": req,
			"value": 40 + level * 5, "tier": 3, "weight_class": &"heavy" if cls == &"knight" else &"cloth"})
		b.icon = DataItems.ICON3D % b.id
		b.model = ItemBaseDef.ITEM_MODEL % b.id
		b.implicit = [StatModifier.inc(StringName(r[7]), float(r[8])) if r[7] in ["stagger_power", "status_power", "move_speed"] else StatModifier.flat(StringName(r[7]), float(r[8]))]
		if b.category == &"boots" and r[7] != "move_speed":
			b.implicit.append(StatModifier.inc(&"move_speed", 0.08))
		if weapon:
			b.weapon_type = StringName(r[2])
			b.attacks_per_second = float(r[5])
			if b.weapon_type == &"staff":
				b.implicit.append(StatModifier.inc(&"magic_damage", 0.10 + level * 0.0045))
			var damage := DataItems.roster_damage(b.weapon_type, level, b.attacks_per_second)
			b.damage_min = damage.x
			b.damage_max = damage.y
			b.element = int(r[6])
			b.element_share = (1.0 if cls == &"mage" else 0.25) if b.element != Elements.PHYSICAL else 0.0
		else:
			var factor := 1.0 if cls == &"knight" else 0.6
			b.defense = (12.0 + level * 1.5) * factor * (1.0 if b.category == &"armor" else 0.5)
		b.weight = float(r[10]) if weapon else DataItems.default_weight(b)
		b.flavor = "Recovered from the deeper halls. " + ("A fast weapon trades damage per strike for speed." if weapon and b.attacks_per_second > 1.5 else "Made for long journeys below the surface.")
		if r[9] != "":
			b.unique_name = b.display_name
			b.fixed_rarity = BH.Rarity.MYTHICAL if level < 50 else BH.Rarity.LEGENDARY
			b.fixed_powers = [StringName(r[9])]
			b.drop_weight = 0
		out.append(b)
	return out

## Guardians target the new relics for the receiving class, with exact level gates.
static func special(rng: RandomNumberGenerator, ilvl: int, cls: StringName) -> ItemBaseDef:
	var pool := []
	for r in ROWS:
		var b := DB.item_base(StringName(r[0]))
		if b and b.unique_name != "" and b.drop_level <= ilvl and b.class_hint == cls:
			pool.append(b)
	return pool[rng.randi_range(0, pool.size() - 1)] if not pool.is_empty() else null
