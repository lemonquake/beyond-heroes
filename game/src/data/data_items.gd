class_name DataItems
## Item bases, affix pool, and legendary powers.

const ICON := "res://assets/ui/icons/items/%s.svg"

static func _b(id: StringName, name: String, cat: StringName, icon: String, d: Dictionary) -> ItemBaseDef:
	var b := ItemBaseDef.new()
	b.id = id
	b.display_name = name
	b.category = cat
	b.icon = ICON % icon
	for k in d:
		b.set(k, d[k])
	if b.drop_level <= 1 and b.level_req > 1:
		b.drop_level = b.level_req
	return b

static func bases() -> Array:
	var out := []
	# ---- Weapons: [id, name, type, level, min, max, req, extra] ----
	var weapons := [
		[&"iron_longsword", "Iron Longsword", &"sword", 1, 5, 9, {&"str": 10}, {}],
		[&"knights_arming_sword", "Arming Sword", &"sword", 10, 14, 22, {&"str": 22, &"dex": 14}, {}],
		[&"runed_sword", "Runed Blade", &"sword", 22, 26, 40, {&"str": 40, &"dex": 25}, {"element": Elements.LIGHT, "element_share": 0.2}],
		[&"rusted_claymore", "Rusted Claymore", &"greatsword", 1, 9, 17, {&"str": 14}, {}],
		[&"executioner_blade", "Executioner's Blade", &"greatsword", 12, 26, 44, {&"str": 34}, {}],
		[&"hand_axe", "Hand Axe", &"axe", 1, 6, 10, {&"str": 10}, {}],
		[&"bearded_axe", "Bearded Axe", &"axe", 14, 17, 27, {&"str": 30, &"agi": 12}, {}],
		[&"ash_spear", "Ash Spear", &"spear", 1, 7, 13, {&"str": 10, &"agi": 8}, {}],
		[&"winged_spear", "Winged Spear", &"spear", 15, 20, 34, {&"str": 26, &"agi": 20}, {}],
		[&"rondel_dagger", "Rondel Dagger", &"dagger", 1, 3, 7, {&"dex": 9}, {}],
		[&"shadow_kris", "Shadow Kris", &"dagger", 13, 9, 19, {&"dex": 26, &"agi": 20}, {"element": Elements.DARK, "element_share": 0.25}],
		[&"hunters_bow", "Hunter's Bow", &"bow", 1, 5, 10, {&"dex": 10}, {}],
		[&"composite_bow", "Composite Bow", &"bow", 14, 15, 29, {&"dex": 30}, {}],
		[&"ashwood_staff", "Ashwood Staff", &"staff", 1, 6, 11, {&"int": 12}, {"element": Elements.FIRE, "element_share": 1.0,
			"implicit": [StatModifier.inc(&"magic_damage", 0.10)]}],
		[&"storm_staff", "Stormcaller Staff", &"staff", 12, 16, 28, {&"int": 30}, {"element": Elements.LIGHTNING, "element_share": 1.0,
			"implicit": [StatModifier.inc(&"magic_damage", 0.20)]}],
		[&"frost_staff", "Rimeheart Staff", &"staff", 18, 20, 34, {&"int": 38, &"wis": 20}, {"element": Elements.ICE, "element_share": 1.0,
			"implicit": [StatModifier.inc(&"magic_damage", 0.25)]}],
		[&"bone_wand", "Bone Wand", &"wand", 1, 3, 6, {&"int": 10}, {"element": Elements.DARK, "element_share": 1.0,
			"implicit": [StatModifier.flat(&"crit_chance", 0.02)]}],
		[&"tide_wand", "Tidecaller Wand", &"wand", 10, 8, 15, {&"int": 22}, {"element": Elements.WATER, "element_share": 1.0,
			"implicit": [StatModifier.flat(&"crit_chance", 0.03)]}],
	]
	for w in weapons:
		var extra: Dictionary = w[7]
		var d := {"weapon_type": w[2], "level_req": w[3], "damage_min": float(w[4]), "damage_max": float(w[5]),
			"requirements": w[6], "value": 12 + w[3] * 4}
		d.merge(extra, true)
		out.append(_b(w[0], w[1], &"weapon", String(w[2]), d))
	# ---- Shields ----
	out.append(_b(&"warden_kite_shield", "Warden Kite Shield", &"shield", "shield", {"level_req": 1, "defense": 12.0,
		"block_chance": 0.25, "block_strength": 0.6, "requirements": {&"str": 12}, "value": 15}))
	out.append(_b(&"tower_shield", "Bastion Tower Shield", &"shield", "shield", {"level_req": 12, "defense": 34.0,
		"block_chance": 0.32, "block_strength": 0.7, "requirements": {&"str": 30}, "value": 40, "implicit": [StatModifier.flat(&"move_speed", -0.15)]}))
	out.append(_b(&"sigil_buckler", "Sigil Buckler", &"shield", "shield", {"level_req": 8, "defense": 16.0,
		"block_chance": 0.20, "block_strength": 0.5, "requirements": {&"str": 14, &"dex": 16}, "value": 30,
		"implicit": [StatModifier.flat(&"res_all", 0.05)]}))
	# ---- Armor: [id, name, cat, icon, level, defense, weight, req, implicit] ----
	var armor := [
		[&"iron_helm", "Iron Helm", &"helm", "helm_plate", 1, 8, &"heavy", {&"str": 10}, []],
		[&"visored_greathelm", "Visored Greathelm", &"helm", "helm_plate", 14, 24, &"heavy", {&"str": 28}, []],
		[&"linen_hood", "Linen Hood", &"helm", "helm_hood", 1, 3, &"cloth", {}, [StatModifier.flat(&"max_mana", 10)]],
		[&"arcanist_cowl", "Arcanist Cowl", &"helm", "helm_hood", 12, 9, &"cloth", {&"int": 24}, [StatModifier.flat(&"max_mana", 25)]],
		[&"padded_gambeson", "Padded Gambeson", &"inner_garment", "inner_garment", 1, 6, &"heavy", {}, [StatModifier.flat(&"max_hp", 10)]],
		[&"silk_undershirt", "Silk Undershirt", &"inner_garment", "inner_garment", 1, 2, &"cloth", {}, [StatModifier.flat(&"mana_regen", 0.3)]],
		[&"chain_shirt", "Chain Shirt", &"inner_garment", "inner_garment", 10, 14, &"heavy", {&"str": 20}, [StatModifier.flat(&"max_hp", 20)]],
		[&"iron_hauberk", "Iron Hauberk", &"armor", "armor_plate", 1, 18, &"heavy", {&"str": 12}, []],
		[&"warden_plate", "Warden Plate", &"armor", "armor_plate", 12, 48, &"heavy", {&"str": 32}, []],
		[&"apprentice_robe", "Apprentice Robe", &"armor", "armor_robe", 1, 6, &"cloth", {}, [StatModifier.flat(&"max_mana", 15)]],
		[&"magister_robe", "Magister Robe", &"armor", "armor_robe", 12, 18, &"cloth", {&"int": 26}, [StatModifier.inc(&"magic_damage", 0.08)]],
		[&"iron_gauntlet", "Iron Gauntlet", &"gloves", "gloves_plate", 1, 4, &"heavy", {&"str": 10}, []],
		[&"spiked_gauntlet", "Spiked Gauntlet", &"gloves", "gloves_plate", 12, 12, &"heavy", {&"str": 26}, [StatModifier.flat(&"added_physical", 3)]],
		[&"silk_glove", "Silk Glove", &"gloves", "gloves_cloth", 1, 2, &"cloth", {}, [StatModifier.flat(&"cast_speed", 0.03)]],
		[&"runed_glove", "Runed Glove", &"gloves", "gloves_cloth", 12, 6, &"cloth", {&"int": 22}, [StatModifier.flat(&"cast_speed", 0.06)]],
		[&"iron_sabaton", "Iron Sabaton", &"boots", "boots_plate", 1, 4, &"heavy", {&"str": 10}, []],
		[&"warden_greave", "Warden Greave", &"boots", "boots_plate", 12, 12, &"heavy", {&"str": 26}, [StatModifier.flat(&"knockback_res", 0.05)]],
		[&"soft_boot", "Soft Boot", &"boots", "boots_cloth", 1, 2, &"cloth", {}, [StatModifier.inc(&"move_speed", 0.02)]],
		[&"wayfarer_boot", "Wayfarer Boot", &"boots", "boots_cloth", 12, 6, &"cloth", {&"agi": 18}, [StatModifier.inc(&"move_speed", 0.04)]],
	]
	for a in armor:
		out.append(_b(a[0], a[1], a[2], a[3], {"level_req": a[4], "defense": float(a[5]), "weight_class": a[6],
			"requirements": a[7], "implicit": a[8], "value": 8 + a[4] * 3}))
	# ---- Accessories ----
	out.append(_b(&"copper_ring", "Copper Ring", &"accessory", "ring", {"level_req": 1, "value": 20}))
	out.append(_b(&"silver_ring", "Silver Ring", &"accessory", "ring", {"level_req": 10, "value": 40, "implicit": [StatModifier.flat(&"res_all", 0.03)]}))
	out.append(_b(&"bone_amulet", "Bone Amulet", &"accessory", "amulet", {"level_req": 1, "value": 25, "implicit": [StatModifier.flat(&"max_hp", 8)]}))
	out.append(_b(&"gold_amulet", "Gilded Amulet", &"accessory", "amulet", {"level_req": 12, "value": 60, "implicit": [StatModifier.flat(&"crit_damage", 0.1)]}))
	out.append(_b(&"rune_charm", "Rune Charm", &"accessory", "charm", {"level_req": 5, "value": 30, "implicit": [StatModifier.flat(&"elemental_damage", 0.05)]}))
	# ---- Stackables ----
	out.append(_b(&"iron_shard", "Iron Shard", &"material", "mat_iron_shard", {"stack_max": 99, "value": 2, "flavor": "Salvaged metal. Used for reforging."}))
	out.append(_b(&"arcane_dust", "Arcane Dust", &"material", "mat_arcane_dust", {"stack_max": 99, "value": 4, "flavor": "Residue of broken enchantments."}))
	out.append(_b(&"ember_core", "Ember Core", &"material", "mat_ember_core", {"stack_max": 50, "value": 10, "flavor": "A still-warm heart of cinders."}))
	out.append(_b(&"bone_fragment", "Bone Fragment", &"material", "mat_bone_fragment", {"stack_max": 99, "value": 1, "flavor": "Remains of the restless dead."}))
	out.append(_b(&"health_potion", "Health Draught", &"consumable", "potion_health", {"stack_max": 20, "value": 8,
		"consumable_effect": {"heal": 0.4}, "flavor": "Restores 40% of Maximum HP over 2 seconds."}))
	out.append(_b(&"mana_potion", "Mana Draught", &"consumable", "potion_mana", {"stack_max": 20, "value": 8,
		"consumable_effect": {"mana": 0.5}, "flavor": "Restores 50% of Maximum Mana over 2 seconds."}))
	return out

static func _a(id: StringName, label: String, prefix: bool, stat: StringName, op: int, tiers: Array, cats: Array, group: StringName, weight := 100, integer := false) -> AffixDef:
	var a := AffixDef.new()
	a.id = id
	a.label = label
	a.is_prefix = prefix
	a.stat = stat
	a.op = op
	a.tiers = tiers
	a.categories = cats
	a.group = group
	a.weight = weight
	a.integer = integer
	return a

static func affixes() -> Array:
	var F := StatModifier.Op.FLAT
	var I := StatModifier.Op.INC
	var WEAP := [&"weapon"]
	var ARM := [&"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"shield"]
	var JEW := [&"accessory"]
	var ANY := []
	var out := [
		# Weapon prefixes
		_a(&"local_phys", "Keen", true, &"local_phys", I, [[1, 0.15, 0.30], [10, 0.30, 0.50], [20, 0.50, 0.75], [35, 0.75, 1.0]], WEAP, &"local_phys"),
		_a(&"added_fire", "Smoldering", true, &"added_fire", F, [[1, 2, 4], [12, 5, 9], [25, 10, 16]], WEAP + JEW, &"added_fire", 70, true),
		_a(&"added_ice", "Frigid", true, &"added_ice", F, [[1, 2, 4], [12, 5, 9], [25, 10, 16]], WEAP + JEW, &"added_ice", 70, true),
		_a(&"added_lightning", "Crackling", true, &"added_lightning", F, [[1, 1, 6], [12, 2, 13], [25, 3, 24]], WEAP + JEW, &"added_lightning", 70, true),
		_a(&"added_dark", "Umbral", true, &"added_dark", F, [[5, 2, 4], [15, 5, 9], [28, 10, 16]], WEAP + JEW, &"added_dark", 50, true),
		_a(&"weapon_damage", "Brutal", true, &"weapon_damage", I, [[1, 0.06, 0.10], [15, 0.11, 0.18], [30, 0.19, 0.28]], WEAP + [&"gloves"], &"weapon_damage"),
		_a(&"magic_damage", "Arcane", true, &"magic_damage", I, [[1, 0.08, 0.14], [12, 0.15, 0.24], [25, 0.25, 0.36]], [&"weapon", &"helm", &"accessory", &"armor"], &"magic_damage"),
		_a(&"elemental_damage", "Prismatic", true, &"elemental_damage", I, [[5, 0.06, 0.10], [18, 0.11, 0.18], [30, 0.19, 0.26]], WEAP + JEW, &"elemental_damage"),
		_a(&"dmg_fire", "Pyric", true, &"dmg_fire", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW + [&"helm"], &"dmg_fire", 60),
		_a(&"dmg_ice", "Glacial", true, &"dmg_ice", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW + [&"helm"], &"dmg_ice", 60),
		_a(&"dmg_lightning", "Stormforged", true, &"dmg_lightning", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW + [&"helm"], &"dmg_lightning", 60),
		_a(&"dmg_water", "Tidal", true, &"dmg_water", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW, &"dmg_water", 50),
		_a(&"dmg_earth", "Quaking", true, &"dmg_earth", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW, &"dmg_earth", 50),
		_a(&"dmg_light", "Hallowed", true, &"dmg_light", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW, &"dmg_light", 50),
		# Armor prefixes
		_a(&"local_def", "Sturdy", true, &"local_def", I, [[1, 0.15, 0.30], [10, 0.30, 0.50], [22, 0.50, 0.75]], ARM, &"local_def"),
		_a(&"local_def_flat", "Reinforced", true, &"local_def_flat", F, [[1, 4, 10], [10, 11, 24], [22, 25, 45]], ARM, &"local_def_flat", 100, true),
		_a(&"max_hp", "Stalwart", true, &"max_hp", F, [[1, 8, 15], [10, 16, 30], [20, 31, 50], [35, 51, 75]], ARM + JEW, &"max_hp", 120, true),
		_a(&"max_mana", "Scholar's", true, &"max_mana", F, [[1, 8, 15], [10, 16, 30], [20, 31, 50]], ARM + JEW + WEAP, &"max_mana", 90, true),
		# Suffixes — attributes
		_a(&"str", "of the Ox", false, &"str", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"str", 100, true),
		_a(&"agi", "of the Lynx", false, &"agi", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"agi", 100, true),
		_a(&"int", "of the Sage", false, &"int", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"int", 100, true),
		_a(&"wis", "of the Owl", false, &"wis", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"wis", 100, true),
		_a(&"spi", "of the Monk", false, &"spi", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"spi", 100, true),
		_a(&"dex", "of the Falcon", false, &"dex", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"dex", 100, true),
		# Suffixes — defenses
		_a(&"res_fire", "of Embers", false, &"res_fire", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_fire"),
		_a(&"res_ice", "of Winter", false, &"res_ice", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_ice"),
		_a(&"res_lightning", "of Grounding", false, &"res_lightning", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_lightning"),
		_a(&"res_dark", "of the Vigil", false, &"res_dark", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_dark"),
		_a(&"res_all", "of the Prism", false, &"res_all", F, [[8, 0.03, 0.06], [20, 0.07, 0.10], [35, 0.11, 0.15]], ARM + JEW, &"res_all", 40),
		_a(&"block_chance", "of Warding", false, &"block_chance", F, [[1, 0.03, 0.05], [15, 0.06, 0.09]], [&"shield"], &"block_chance"),
		_a(&"hp_regen", "of Mending", false, &"hp_regen", F, [[1, 0.5, 1.0], [12, 1.1, 2.2], [25, 2.3, 4.0]], ARM + JEW, &"hp_regen"),
		_a(&"mana_regen", "of Clarity", false, &"mana_regen", F, [[1, 0.4, 0.8], [12, 0.9, 1.6], [25, 1.7, 2.8]], ARM + JEW + WEAP, &"mana_regen"),
		# Suffixes — offense/utility
		_a(&"crit_chance", "of Precision", false, &"crit_chance", F, [[1, 0.01, 0.02], [12, 0.025, 0.04], [25, 0.045, 0.06]], WEAP + JEW + [&"gloves", &"helm"], &"crit_chance"),
		_a(&"crit_damage", "of Ruin", false, &"crit_damage", F, [[5, 0.08, 0.15], [15, 0.16, 0.25], [30, 0.26, 0.40]], WEAP + JEW, &"crit_damage", 70),
		_a(&"attack_speed", "of Fury", false, &"attack_speed", I, [[1, 0.04, 0.07], [12, 0.08, 0.12], [25, 0.13, 0.18]], WEAP + [&"gloves"] + JEW, &"attack_speed", 80),
		_a(&"cast_speed", "of Incantation", false, &"cast_speed", I, [[1, 0.04, 0.07], [12, 0.08, 0.12], [25, 0.13, 0.18]], WEAP + [&"gloves", &"helm"] + JEW, &"cast_speed", 80),
		_a(&"move_speed", "of Haste", false, &"move_speed", I, [[1, 0.04, 0.06], [12, 0.07, 0.10], [25, 0.11, 0.14]], [&"boots"], &"move_speed", 120),
		_a(&"cdr", "of Recurrence", false, &"cdr", F, [[10, 0.03, 0.05], [25, 0.06, 0.09]], [&"helm", &"accessory", &"gloves"], &"cdr", 50),
		_a(&"life_leech", "of the Leech", false, &"life_leech", F, [[5, 0.01, 0.02], [18, 0.025, 0.04]], WEAP + JEW + [&"gloves"], &"life_leech", 50),
		_a(&"impact_strength", "of Thunderous Blows", false, &"impact_strength", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + [&"gloves", &"boots"], &"impact_strength", 60),
		_a(&"knockback_res", "of the Anchor", false, &"knockback_res", F, [[1, 0.05, 0.08], [15, 0.09, 0.14]], [&"boots", &"armor"], &"knockback_res", 60),
		_a(&"status_res", "of Resolve", false, &"status_res", F, [[1, 0.05, 0.08], [15, 0.09, 0.15]], ARM + JEW, &"status_res", 60),
		_a(&"magic_find", "of Fortune", false, &"magic_find", F, [[1, 0.06, 0.12], [15, 0.13, 0.22]], JEW + [&"helm", &"boots"], &"magic_find", 40),
		_a(&"pen_fire", "of Searing", false, &"pen_fire", F, [[12, 0.05, 0.08], [28, 0.09, 0.14]], WEAP + JEW, &"pen_fire", 30),
		_a(&"pen_armor", "of Sundering", false, &"pen_armor", F, [[12, 0.05, 0.08], [28, 0.09, 0.14]], WEAP + JEW, &"pen_armor", 30),
	]
	return out

static func _p(id: StringName, name: String, desc: String, flag: StringName, mag: float, cats: Array, cls := &"", mods := []) -> LegendaryPowerDef:
	var p := LegendaryPowerDef.new()
	p.id = id
	p.display_name = name
	p.description = desc
	p.flag = flag
	p.magnitude = mag
	p.categories = cats
	p.class_hint = cls
	p.modifiers = mods
	return p

static func powers() -> Array:
	return [
		_p(&"wallbreaker", "Wallbreaker's", "Impact damage from knockback collisions is doubled.", &"impact_double", 1.0, [], &"knight",
			[StatModifier.inc(&"impact_damage", 1.0)]),
		_p(&"echoing_guard", "Echoing", "Blocking releases a shockwave dealing 60% weapon damage around you (1 s cooldown).", &"block_shockwave", 0.6, [&"shield", &"armor", &"gloves"], &"knight"),
		_p(&"relentless", "Relentless", "Critical hits reduce all skill cooldowns by 0.5 seconds.", &"crit_cdr", 0.5, [&"weapon", &"accessory", &"gloves"]),
		_p(&"pyre", "Pyrelord's", "Burning spreads to one nearby enemy every second.", &"burn_spread", 1.0, [&"weapon", &"helm", &"accessory"], &"mage"),
		_p(&"frostbite", "Frostbitten", "Frozen enemies take 40% more impact damage and shatter on death, chilling nearby foes.", &"frozen_impact", 0.4, [&"weapon", &"gloves", &"accessory"]),
		_p(&"conductor", "Conductor's", "Chain Lightning chains 3 additional times against Wet targets.", &"wet_chains", 3.0, [&"weapon", &"helm"], &"mage"),
		_p(&"bloodthirst", "Bloodthirsty", "Kills restore 4% of Maximum HP.", &"kill_heal", 0.04, [], &""),
		_p(&"stormstride", "Stormstriding", "Dodging or blinking leaves a crackling trail that Shocks enemies.", &"dodge_trail", 1.0, [&"boots"]),
		_p(&"valorous", "Valorous", "Valor never decays and you start fights with 30 Valor.", &"valor_hold", 30.0, [&"armor", &"helm", &"accessory"], &"knight"),
		_p(&"overflow", "Overflowing", "At maximum Arcane Charge your spells cost no Mana.", &"arcane_free", 1.0, [&"weapon", &"armor", &"accessory"], &"mage"),
	]
