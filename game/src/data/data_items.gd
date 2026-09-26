class_name DataItems
## Item bases, affix pool, faction licenses, powers (mythical / legendary / aether), item sets and named uniques.

const ICON := "res://assets/ui/icons/items/%s.svg"
const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC
const M := StatModifier.Op.MORE

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
	# ---- Weapons: [id, name, type, level, min, max, req, tier, extra] ----
	var weapons := [
		[&"iron_longsword", "Iron Longsword", &"sword", 1, 5, 9, {&"str": 10}, 1, {}],
		[&"knights_arming_sword", "Arming Sword", &"sword", 9, 13, 21, {&"str": 20, &"dex": 13}, 2, {}],
		[&"runed_sword", "Runed Blade", &"sword", 18, 24, 37, {&"str": 34, &"dex": 22}, 3, {"element": Elements.LIGHT, "element_share": 0.2}],
		[&"rusted_claymore", "Rusted Claymore", &"greatsword", 1, 9, 17, {&"str": 14}, 1, {}],
		[&"executioner_blade", "Executioner's Blade", &"greatsword", 10, 24, 40, {&"str": 30}, 2, {}],
		[&"titan_greatsword", "Titan's Edge", &"greatsword", 19, 40, 64, {&"str": 44}, 3, {"implicit": [StatModifier.inc(&"stagger_power", 0.15)]}],
		[&"hand_axe", "Hand Axe", &"axe", 1, 6, 10, {&"str": 10}, 1, {}],
		[&"bearded_axe", "Bearded Axe", &"axe", 10, 16, 26, {&"str": 26, &"agi": 11}, 2, {}],
		[&"rune_cleaver", "Rune Cleaver", &"axe", 19, 27, 43, {&"str": 38, &"agi": 18}, 3, {"element": Elements.EARTH, "element_share": 0.2}],
		[&"ash_spear", "Ash Spear", &"spear", 1, 7, 13, {&"str": 10, &"agi": 8}, 1, {}],
		[&"winged_spear", "Winged Spear", &"spear", 11, 19, 32, {&"str": 24, &"agi": 18}, 2, {}],
		[&"storm_lance", "Storm Lance", &"spear", 20, 30, 50, {&"str": 34, &"agi": 28}, 3, {"element": Elements.LIGHTNING, "element_share": 0.25}],
		[&"rondel_dagger", "Rondel Dagger", &"dagger", 1, 3, 7, {&"dex": 9}, 1, {}],
		[&"shadow_kris", "Shadow Kris", &"dagger", 10, 9, 18, {&"dex": 22, &"agi": 18}, 2, {"element": Elements.DARK, "element_share": 0.25}],
		[&"aether_stiletto", "Glass Stiletto", &"dagger", 19, 15, 29, {&"dex": 36, &"agi": 28}, 3, {"implicit": [StatModifier.flat(&"crit_damage", 0.15)]}],
		[&"hunters_bow", "Hunter's Bow", &"bow", 1, 5, 10, {&"dex": 10}, 1, {}],
		[&"composite_bow", "Composite Bow", &"bow", 10, 14, 27, {&"dex": 26}, 2, {}],
		[&"warden_longbow", "Warden Longbow", &"bow", 19, 23, 44, {&"dex": 40}, 3, {"implicit": [StatModifier.inc(&"projectile_speed", 0.15)]}],
		[&"ashwood_staff", "Ashwood Staff", &"staff", 1, 6, 11, {&"int": 12}, 1, {"element": Elements.FIRE, "element_share": 1.0,
			"implicit": [StatModifier.inc(&"magic_damage", 0.10)]}],
		[&"storm_staff", "Stormcaller Staff", &"staff", 10, 15, 26, {&"int": 26}, 2, {"element": Elements.LIGHTNING, "element_share": 1.0,
			"implicit": [StatModifier.inc(&"magic_damage", 0.18)]}],
		[&"frost_staff", "Rimeheart Staff", &"staff", 18, 21, 35, {&"int": 36, &"wis": 18}, 3, {"element": Elements.ICE, "element_share": 1.0,
			"implicit": [StatModifier.inc(&"magic_damage", 0.25)]}],
		[&"bone_wand", "Bone Wand", &"wand", 1, 3, 6, {&"int": 10}, 1, {"element": Elements.DARK, "element_share": 1.0,
			"implicit": [StatModifier.flat(&"crit_chance", 0.02)]}],
		[&"tide_wand", "Tidecaller Wand", &"wand", 9, 8, 15, {&"int": 20}, 2, {"element": Elements.WATER, "element_share": 1.0,
			"implicit": [StatModifier.flat(&"crit_chance", 0.03)]}],
		[&"sunfire_wand", "Sunfire Wand", &"wand", 18, 13, 24, {&"int": 32}, 3, {"element": Elements.LIGHT, "element_share": 1.0,
			"implicit": [StatModifier.flat(&"crit_chance", 0.04)]}],
	]
	for w in weapons:
		var tier: int = w[7]
		var d := {"weapon_type": w[2], "level_req": w[3], "damage_min": float(w[4]), "damage_max": float(w[5]),
			"requirements": w[6], "value": 12 + w[3] * 4, "tier": tier,
			"class_hint": &"mage" if w[2] in [&"staff", &"wand"] else &"knight"}
		d.merge(w[8], true)
		var icon := String(w[2]) if tier == 1 else "%s_%d" % [w[2], tier]
		out.append(_b(w[0], w[1], &"weapon", icon, d))
	# ---- Shields ----
	out.append(_b(&"warden_kite_shield", "Warden Kite Shield", &"shield", "shield", {"level_req": 1, "defense": 12.0,
		"block_chance": 0.25, "block_strength": 0.6, "requirements": {&"str": 12}, "value": 15, "class_hint": &"knight"}))
	out.append(_b(&"sigil_buckler", "Sigil Buckler", &"shield", "shield_3", {"level_req": 7, "defense": 16.0, "tier": 2,
		"block_chance": 0.20, "block_strength": 0.5, "requirements": {&"str": 14, &"dex": 16}, "value": 30,
		"implicit": [StatModifier.flat(&"res_all", 0.05)]}))
	out.append(_b(&"tower_shield", "Bastion Tower Shield", &"shield", "shield_2", {"level_req": 12, "defense": 34.0, "tier": 3,
		"block_chance": 0.32, "block_strength": 0.7, "requirements": {&"str": 30}, "value": 40, "class_hint": &"knight",
		"implicit": [StatModifier.flat(&"move_speed", -0.15)]}))
	# ---- Armor: [id, name, cat, icon, level, defense, weight, req, implicit] ----
	var armor := [
		[&"iron_helm", "Iron Helm", &"helm", "helm_plate", 1, 8, &"heavy", {&"str": 10}, []],
		[&"barbute_helm", "Barbute", &"helm", "helm_plate_2", 8, 16, &"heavy", {&"str": 20}, []],
		[&"visored_greathelm", "Visored Greathelm", &"helm", "helm_plate_3", 16, 28, &"heavy", {&"str": 32}, [StatModifier.flat(&"status_res", 0.05)]],
		[&"linen_hood", "Linen Hood", &"helm", "helm_hood", 1, 3, &"cloth", {}, [StatModifier.flat(&"max_mana", 10)]],
		[&"arcanist_cowl", "Arcanist Cowl", &"helm", "helm_hood_2", 9, 8, &"cloth", {&"int": 20}, [StatModifier.flat(&"max_mana", 22)]],
		[&"seers_circlet", "Seer's Veil", &"helm", "helm_hood_3", 17, 13, &"cloth", {&"int": 32}, [StatModifier.flat(&"max_mana", 36)]],
		[&"padded_gambeson", "Padded Gambeson", &"inner_garment", "inner_garment", 1, 6, &"heavy", {}, [StatModifier.flat(&"max_hp", 10)]],
		[&"silk_undershirt", "Silk Undershirt", &"inner_garment", "inner_silk", 1, 2, &"cloth", {}, [StatModifier.flat(&"mana_regen", 0.3)]],
		[&"chain_shirt", "Chain Shirt", &"inner_garment", "inner_chain", 10, 14, &"heavy", {&"str": 20}, [StatModifier.flat(&"max_hp", 20)]],
		[&"runeweave_vest", "Runeweave Vest", &"inner_garment", "inner_silk", 10, 6, &"cloth", {&"int": 20}, [StatModifier.flat(&"mana_regen", 0.8)]],
		[&"iron_hauberk", "Iron Hauberk", &"armor", "armor_plate", 1, 18, &"heavy", {&"str": 12}, []],
		[&"brigandine", "Brigandine", &"armor", "armor_plate_2", 8, 32, &"heavy", {&"str": 22}, []],
		[&"warden_plate", "Warden Plate", &"armor", "armor_plate_3", 16, 52, &"heavy", {&"str": 34}, [StatModifier.flat(&"knockback_res", 0.05)]],
		[&"apprentice_robe", "Apprentice Robe", &"armor", "armor_robe", 1, 6, &"cloth", {}, [StatModifier.flat(&"max_mana", 15)]],
		[&"traveler_coat", "Traveler's Coat", &"armor", "armor_robe_2", 8, 12, &"cloth", {&"int": 18}, [StatModifier.inc(&"magic_damage", 0.05)]],
		[&"magister_robe", "Magister Robe", &"armor", "armor_robe_3", 16, 20, &"cloth", {&"int": 30}, [StatModifier.inc(&"magic_damage", 0.10)]],
		[&"iron_gauntlet", "Iron Gauntlet", &"gloves", "gloves_plate", 1, 4, &"heavy", {&"str": 10}, []],
		[&"spiked_gauntlet", "Spiked Gauntlet", &"gloves", "gloves_plate_2", 11, 11, &"heavy", {&"str": 24}, [StatModifier.flat(&"added_physical", 3)]],
		[&"silk_glove", "Silk Glove", &"gloves", "gloves_cloth", 1, 2, &"cloth", {}, [StatModifier.inc(&"cast_speed", 0.03)]],
		[&"runed_glove", "Runed Glove", &"gloves", "gloves_cloth_2", 11, 6, &"cloth", {&"int": 22}, [StatModifier.inc(&"cast_speed", 0.06)]],
		[&"iron_sabaton", "Iron Sabaton", &"boots", "boots_plate", 1, 4, &"heavy", {&"str": 10}, []],
		[&"warden_greave", "Warden Greave", &"boots", "boots_plate_2", 11, 12, &"heavy", {&"str": 24}, [StatModifier.flat(&"knockback_res", 0.05)]],
		[&"soft_boot", "Soft Boot", &"boots", "boots_cloth", 1, 2, &"cloth", {}, [StatModifier.inc(&"move_speed", 0.02)]],
		[&"wayfarer_boot", "Wayfarer Boot", &"boots", "boots_cloth_2", 11, 6, &"cloth", {&"agi": 16}, [StatModifier.inc(&"move_speed", 0.04)]],
	]
	for a in armor:
		out.append(_b(a[0], a[1], a[2], a[3], {"level_req": a[4], "defense": float(a[5]), "weight_class": a[6],
			"requirements": a[7], "implicit": a[8], "value": 8 + a[4] * 3,
			"class_hint": &"knight" if a[6] == &"heavy" else &"mage"}))
	# ---- Accessories ----
	out.append(_b(&"copper_ring", "Copper Ring", &"accessory", "ring", {"level_req": 1, "value": 20}))
	out.append(_b(&"silver_ring", "Silver Ring", &"accessory", "ring_2", {"level_req": 8, "value": 40, "implicit": [StatModifier.flat(&"res_all", 0.03)]}))
	out.append(_b(&"sigil_ring", "Sigil Ring", &"accessory", "ring_3", {"level_req": 16, "value": 70, "implicit": [StatModifier.flat(&"crit_chance", 0.02)]}))
	out.append(_b(&"bone_amulet", "Bone Amulet", &"accessory", "amulet", {"level_req": 1, "value": 25, "implicit": [StatModifier.flat(&"max_hp", 8)]}))
	out.append(_b(&"gold_amulet", "Gilded Amulet", &"accessory", "amulet_2", {"level_req": 10, "value": 60, "implicit": [StatModifier.flat(&"crit_damage", 0.1)]}))
	out.append(_b(&"star_pendant", "Star Pendant", &"accessory", "amulet_3", {"level_req": 18, "value": 90, "implicit": [StatModifier.inc(&"elemental_damage", 0.08)]}))
	out.append(_b(&"rune_charm", "Rune Charm", &"accessory", "charm", {"level_req": 4, "value": 30, "implicit": [StatModifier.inc(&"elemental_damage", 0.05)]}))
	out.append(_b(&"war_talisman", "War Talisman", &"accessory", "charm_2", {"level_req": 12, "value": 55, "implicit": [StatModifier.inc(&"impact_strength", 0.08)]}))

	_sets_and_uniques(out)

	# ---- Stackables: consumables, materials, currency, quest items ----
	out.append(_b(&"health_potion", "Health Draught", &"consumable", "potion_health", {"stack_max": 20, "value": 8,
		"consumable_effect": {"heal": 0.4}, "flavor": "Restores 40% of Maximum HP over 2 seconds."}))
	out.append(_b(&"greater_health_potion", "Greater Health Draught", &"consumable", "potion_health_large", {"stack_max": 20, "value": 22,
		"level_req": 8, "consumable_effect": {"heal": 0.65}, "flavor": "Restores 65% of Maximum HP over 2 seconds."}))
	out.append(_b(&"mana_potion", "Mana Draught", &"consumable", "potion_mana", {"stack_max": 20, "value": 8,
		"consumable_effect": {"mana": 0.5}, "flavor": "Restores 50% of Maximum Mana over 2 seconds."}))
	out.append(_b(&"greater_mana_potion", "Greater Mana Draught", &"consumable", "potion_mana_large", {"stack_max": 20, "value": 22,
		"level_req": 8, "consumable_effect": {"mana": 0.8}, "flavor": "Restores 80% of Maximum Mana over 2 seconds."}))
	out.append(_b(&"rejuvenation_elixir", "Rejuvenation Elixir", &"consumable", "elixir_rejuvenation", {"stack_max": 10, "value": 45,
		"level_req": 5, "consumable_effect": {"heal": 0.35, "mana": 0.35, "instant": 1.0}, "flavor": "Instantly restores 35% of HP and Mana."}))
	out.append(_b(&"antidote", "Purifying Salts", &"consumable", "antidote", {"stack_max": 10, "value": 15,
		"consumable_effect": {"cleanse": 1.0}, "flavor": "Removes Poison, Burning, Bleeding, Curse and Chill."}))
	out.append(_b(&"return_scroll", "Scroll of Return", &"consumable", "scroll_return", {"stack_max": 10, "value": 30,
		"consumable_effect": {"return": 1.0}, "flavor": "Opens a path back to the Hero Sanctuary waypoint."}))
	out.append(_b(&"iron_shard", "Iron Shard", &"material", "mat_iron_shard", {"stack_max": 99, "value": 2, "flavor": "Salvaged metal. Used for reforging."}))
	out.append(_b(&"arcane_dust", "Arcane Dust", &"material", "mat_arcane_dust", {"stack_max": 99, "value": 4, "flavor": "Residue of broken enchantments."}))
	out.append(_b(&"ember_core", "Ember Core", &"material", "mat_ember_core", {"stack_max": 50, "value": 10, "flavor": "A still-warm heart of cinders."}))
	out.append(_b(&"bone_fragment", "Bone Fragment", &"material", "mat_bone_fragment", {"stack_max": 99, "value": 1, "flavor": "Remains of the restless dead."}))
	out.append(_b(&"frost_crystal", "Frost Crystal", &"material", "frost_crystal", {"stack_max": 50, "value": 8, "flavor": "Never melts, even in the forge."}))
	out.append(_b(&"storm_essence", "Storm Essence", &"material", "storm_essence", {"stack_max": 50, "value": 9, "flavor": "A captured crackle of a spent thunderhead."}))
	out.append(_b(&"shadow_silk", "Shadow Silk", &"material", "shadow_silk", {"stack_max": 50, "value": 7, "flavor": "Woven by things that hunt in the catacombs."}))
	out.append(_b(&"beast_hide", "Beast Hide", &"material", "beast_hide", {"stack_max": 50, "value": 3, "flavor": "Tough hide from the corrupted beasts of the forest."}))
	out.append(_b(&"aether_shard", "Aether Shard", &"material", "aether_shard", {"stack_max": 999, "value": 40,
		"flavor": "Crystallized Aether. Merchants of rare goods accept nothing else."}))
	out.append(_b(&"quest_seal_key", "Seal of the First Oath", &"quest", "quest_seal_key", {"sellable": false, "value": 0,
		"flavor": "A heavy bronze seal, warm to the touch. It once kept the Hollow Throne shut."}))
	out.append(_b(&"quest_tablet", "Ritual Tablet", &"quest", "quest_tablet", {"sellable": false, "value": 0,
		"flavor": "Ash-stained stone covered in the Ashen Circle's cipher."}))
	out.append(_b(&"quest_crown_fragment", "Hollow Crown Fragment", &"quest", "quest_crown_fragment", {"sellable": false, "value": 0,
		"flavor": "A shard of Morthar's broken crown. It hums with stolen Aether."}))
	return out

## Set pieces (Master tier minimum) and named Aether uniques.
static func _sets_and_uniques(out: Array) -> void:
	# Aether Guardian — knight
	out.append(_b(&"guardian_helm", "Aether Guardian Helm", &"helm", "set_guardian_helm", {"level_req": 8, "defense": 20.0,
		"weight_class": &"heavy", "requirements": {&"str": 20}, "value": 60, "set_id": &"aether_guardian", "class_hint": &"knight", "drop_weight": 0}))
	out.append(_b(&"guardian_plate", "Aether Guardian Plate", &"armor", "set_guardian_armor", {"level_req": 9, "defense": 40.0,
		"weight_class": &"heavy", "requirements": {&"str": 22}, "value": 80, "set_id": &"aether_guardian", "class_hint": &"knight", "drop_weight": 0}))
	out.append(_b(&"guardian_gauntlets", "Aether Guardian Gauntlets", &"gloves", "set_guardian_gloves", {"level_req": 8, "defense": 10.0,
		"weight_class": &"heavy", "requirements": {&"str": 20}, "value": 50, "set_id": &"aether_guardian", "class_hint": &"knight", "drop_weight": 0}))
	out.append(_b(&"guardian_greaves", "Aether Guardian Greaves", &"boots", "set_guardian_boots", {"level_req": 8, "defense": 10.0,
		"weight_class": &"heavy", "requirements": {&"str": 20}, "value": 50, "set_id": &"aether_guardian", "class_hint": &"knight", "drop_weight": 0}))
	out.append(_b(&"guardian_aegis", "Aether Guardian Aegis", &"shield", "set_guardian_shield", {"level_req": 10, "defense": 26.0,
		"block_chance": 0.28, "block_strength": 0.68, "requirements": {&"str": 24}, "value": 90, "set_id": &"aether_guardian",
		"class_hint": &"knight", "drop_weight": 0}))
	# Starbound Sage — mage
	out.append(_b(&"sage_hood", "Starbound Sage Hood", &"helm", "set_sage_hood", {"level_req": 8, "defense": 7.0,
		"weight_class": &"cloth", "requirements": {&"int": 20}, "value": 60, "set_id": &"starbound_sage", "class_hint": &"mage", "drop_weight": 0}))
	out.append(_b(&"sage_robe", "Starbound Sage Robe", &"armor", "set_sage_robe", {"level_req": 9, "defense": 14.0,
		"weight_class": &"cloth", "requirements": {&"int": 22}, "value": 80, "set_id": &"starbound_sage", "class_hint": &"mage", "drop_weight": 0}))
	out.append(_b(&"sage_gloves", "Starbound Sage Gloves", &"gloves", "set_sage_gloves", {"level_req": 8, "defense": 4.0,
		"weight_class": &"cloth", "requirements": {&"int": 20}, "value": 50, "set_id": &"starbound_sage", "class_hint": &"mage", "drop_weight": 0}))
	out.append(_b(&"sage_boots", "Starbound Sage Boots", &"boots", "set_sage_boots", {"level_req": 8, "defense": 4.0,
		"weight_class": &"cloth", "requirements": {&"int": 20}, "value": 50, "set_id": &"starbound_sage", "class_hint": &"mage", "drop_weight": 0}))
	out.append(_b(&"sage_staff", "Starbound Sage Staff", &"weapon", "set_sage_staff", {"level_req": 10, "weapon_type": &"staff",
		"damage_min": 13.0, "damage_max": 22.0, "element": Elements.LIGHT, "element_share": 1.0, "requirements": {&"int": 24},
		"implicit": [StatModifier.inc(&"magic_damage", 0.18)], "value": 90, "set_id": &"starbound_sage", "class_hint": &"mage", "drop_weight": 0}))
	# Named Aether uniques
	var A := BH.Rarity.AETHER
	out.append(_b(&"u_dawnbreaker", "Greatsword", &"weapon", "aether_greatsword", {"unique_name": "Dawnbreaker", "fixed_rarity": A,
		"level_req": 9, "weapon_type": &"greatsword", "damage_min": 22.0, "damage_max": 38.0, "element": Elements.LIGHT, "element_share": 0.3,
		"requirements": {&"str": 26}, "fixed_powers": [&"a_fifth_stagger"], "value": 150, "class_hint": &"knight", "drop_weight": 0, "tier": 3,
		"lore": "Forged at first light by the Order of the Dawn. Every fifth blow lands like a falling sun."}))
	out.append(_b(&"u_riftblade", "Sword", &"weapon", "aether_sword", {"unique_name": "Riftblade", "fixed_rarity": A,
		"level_req": 8, "weapon_type": &"sword", "damage_min": 12.0, "damage_max": 21.0, "element": Elements.LIGHTNING, "element_share": 0.25,
		"requirements": {&"str": 18, &"dex": 14}, "fixed_powers": [&"a_crit_lightning"], "value": 140, "class_hint": &"knight", "drop_weight": 0, "tier": 3,
		"lore": "Its edge cuts a thin line in the air that takes a moment to close."}))
	out.append(_b(&"u_starwhisper", "Staff", &"weapon", "aether_staff", {"unique_name": "Starwhisper", "fixed_rarity": A,
		"level_req": 8, "weapon_type": &"staff", "damage_min": 14.0, "damage_max": 24.0, "element": Elements.FIRE, "element_share": 1.0,
		"requirements": {&"int": 22}, "implicit": [StatModifier.inc(&"magic_damage", 0.2)], "fixed_powers": [&"a_firebolt_split"],
		"value": 150, "class_hint": &"mage", "drop_weight": 0, "tier": 3,
		"lore": "The stars it was carved to point at no longer exist. It remembers them anyway."}))
	out.append(_b(&"u_winters_heart", "Wand", &"weapon", "aether_wand", {"unique_name": "Winter's Heart", "fixed_rarity": A,
		"level_req": 8, "weapon_type": &"wand", "damage_min": 8.0, "damage_max": 14.0, "element": Elements.ICE, "element_share": 1.0,
		"requirements": {&"int": 20}, "fixed_powers": [&"a_frozen_explode"], "value": 140, "class_hint": &"mage", "drop_weight": 0, "tier": 3,
		"lore": "Cold enough to make the dead shatter."}))
	out.append(_b(&"u_band_of_stillness", "Ring", &"accessory", "aether_ring", {"unique_name": "Band of Stillness", "fixed_rarity": A,
		"level_req": 6, "fixed_powers": [&"a_still_mana"], "value": 120, "drop_weight": 0,
		"lore": "Worn by the monks of the drowned chapel, who believed Aether pools where nothing moves."}))
	out.append(_b(&"u_heart_of_aether", "Amulet", &"accessory", "aether_amulet", {"unique_name": "Heart of the Aether", "fixed_rarity": A,
		"level_req": 10, "fixed_powers": [&"a_overflow_pulse"], "value": 160, "drop_weight": 0,
		"lore": "A drop of the world's first light, caged in silver."}))

## Item sets: pieces + cumulative bonuses.
static func sets() -> Array:
	var guardian := SetDef.new()
	guardian.id = &"aether_guardian"
	guardian.display_name = "Aether Guardian"
	guardian.class_hint = &"knight"
	guardian.pieces = [&"guardian_helm", &"guardian_plate", &"guardian_gauntlets", &"guardian_greaves", &"guardian_aegis"]
	guardian.bonuses = {
		2: {"desc": "+40 Defense and 10% increased Defense", "mods": [StatModifier.flat(&"defense", 40.0), StatModifier.inc(&"defense", 0.10)]},
		3: {"desc": "+8% Block Chance and +10% Block Strength", "mods": [StatModifier.flat(&"block_chance", 0.08), StatModifier.flat(&"block_strength", 0.10)]},
		5: {"desc": "Blocking releases a protective Aether pulse: knocks nearby enemies back and grants a ward of 6% of Maximum HP (2 s cooldown).",
			"flags": {&"aether_pulse": 0.06}},
	}
	guardian.lore = "Worn by the wardens who held the Sanctuary gate on the night the Aether broke."
	var sage := SetDef.new()
	sage.id = &"starbound_sage"
	sage.display_name = "Starbound Sage"
	sage.class_hint = &"mage"
	sage.pieces = [&"sage_hood", &"sage_robe", &"sage_gloves", &"sage_boots", &"sage_staff"]
	sage.bonuses = {
		2: {"desc": "+50 Maximum Mana", "mods": [StatModifier.flat(&"max_mana", 50.0)]},
		3: {"desc": "+20% increased Elemental Damage", "mods": [StatModifier.inc(&"elemental_damage", 0.20)]},
		5: {"desc": "Casting a spell of a different element than your last grants Arcane Amplification: 8% more spell damage per stack (max 5, 6 s).",
			"flags": {&"arcane_amp": 0.08}},
	}
	sage.lore = "The robes of the observatory-keepers, stitched with the paths of stars that fell into the sea."
	return [guardian, sage]

## Faction licenses for Licensed-tier items: fixed specialization bonus [stat, op, base, per item level].
static func licenses() -> Dictionary:
	return {
		&"dawn_order": {"name": "Order of the Dawn", "desc": "Licensed smiths of the knightly Order.",
			"categories": [&"weapon", &"shield", &"armor", &"helm", &"gloves"],
			"mods": [[&"block_chance", F, 0.02, 0.0005], [&"valor_gain", I, 0.08, 0.002]]},
		&"arcanum": {"name": "Circle of the Arcanum", "desc": "Enchantments certified by the mage circle.",
			"categories": [&"weapon", &"helm", &"armor", &"gloves", &"accessory"],
			"mods": [[&"cast_speed", I, 0.04, 0.001], [&"mana_regen", F, 0.4, 0.05]]},
		&"wardens_guild": {"name": "Wardens' Guild", "desc": "Gear of the Sanctuary's gate-wardens.",
			"categories": [&"armor", &"inner_garment", &"boots", &"shield", &"helm"],
			"mods": [[&"max_hp", F, 10.0, 1.5], [&"knockback_res", F, 0.04, 0.001]]},
		&"hunters_lodge": {"name": "Hunters' Lodge", "desc": "Precision work from the forest lodge.",
			"categories": [&"weapon", &"gloves", &"boots", &"accessory"],
			"mods": [[&"crit_chance", F, 0.015, 0.0004], [&"accuracy", F, 10.0, 1.5]]},
		&"merchant_league": {"name": "Merchant League", "desc": "Certified trade goods, fairly priced.",
			"categories": [&"accessory", &"helm", &"boots"],
			"mods": [[&"gold_find", I, 0.12, 0.004], [&"magic_find", F, 0.05, 0.002]]},
	}

static func _a(id: StringName, label: String, prefix: bool, stat: StringName, op: int, tiers: Array, cats: Array, group: StringName, weight := 100, integer := false, min_rarity := 0) -> AffixDef:
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
	a.min_rarity = min_rarity
	return a

static func affixes() -> Array:
	var WEAP := [&"weapon"]
	var ARM := [&"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"shield"]
	var JEW := [&"accessory"]
	var ANY := []
	var ELITE := BH.Rarity.ELITE
	var out := [
		# Weapon prefixes
		_a(&"local_phys", "Keen", true, &"local_phys", I, [[1, 0.15, 0.30], [10, 0.30, 0.50], [20, 0.50, 0.75], [35, 0.75, 1.0]], WEAP, &"local_phys"),
		_a(&"added_fire", "Flaming", true, &"added_fire", F, [[1, 2, 4], [12, 5, 9], [25, 10, 16]], WEAP + JEW, &"added_fire", 70, true),
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
		_a(&"dmg_wind", "Gale-touched", true, &"dmg_wind", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW, &"dmg_wind", 40),
		_a(&"dmg_light", "Hallowed", true, &"dmg_light", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW, &"dmg_light", 50),
		_a(&"dmg_dark", "Accursed", true, &"dmg_dark", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + JEW, &"dmg_dark", 40),
		_a(&"stagger_power", "Crushing", true, &"stagger_power", I, [[1, 0.10, 0.18], [14, 0.19, 0.30]], WEAP + [&"gloves"], &"stagger_power", 60),
		_a(&"projectile_damage", "Fletched", true, &"projectile_damage", I, [[1, 0.08, 0.14], [14, 0.15, 0.25]], WEAP + [&"gloves", &"accessory"], &"projectile_damage", 40),
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
		_a(&"dex", "of Precision", false, &"dex", F, [[1, 2, 4], [10, 5, 8], [20, 9, 13], [35, 14, 20]], ANY, &"dex", 100, true),
		# Suffixes — defenses
		_a(&"res_fire", "of Embers", false, &"res_fire", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_fire"),
		_a(&"res_ice", "of Winter", false, &"res_ice", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_ice"),
		_a(&"res_lightning", "of Grounding", false, &"res_lightning", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_lightning"),
		_a(&"res_earth", "of the Mountain", false, &"res_earth", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_earth", 60),
		_a(&"res_water", "of the Shore", false, &"res_water", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_water", 60),
		_a(&"res_wind", "of Stillness", false, &"res_wind", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_wind", 50),
		_a(&"res_dark", "of the Vigil", false, &"res_dark", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_dark"),
		_a(&"res_light", "of Shadows", false, &"res_light", F, [[1, 0.06, 0.12], [12, 0.13, 0.20], [25, 0.21, 0.30]], ARM + JEW, &"res_light", 40),
		_a(&"res_all", "of the Prism", false, &"res_all", F, [[8, 0.03, 0.06], [20, 0.07, 0.10], [35, 0.11, 0.15]], ARM + JEW, &"res_all", 40),
		_a(&"block_chance", "of Warding", false, &"block_chance", F, [[1, 0.03, 0.05], [15, 0.06, 0.09]], [&"shield"], &"block_chance"),
		_a(&"hp_regen", "of Mending", false, &"hp_regen", F, [[1, 0.5, 1.0], [12, 1.1, 2.2], [25, 2.3, 4.0]], ARM + JEW, &"hp_regen"),
		_a(&"mana_regen", "of Clarity", false, &"mana_regen", F, [[1, 0.4, 0.8], [12, 0.9, 1.6], [25, 1.7, 2.8]], ARM + JEW + WEAP, &"mana_regen"),
		_a(&"evasion", "of Shadows' Step", false, &"evasion", F, [[1, 6, 14], [12, 15, 30], [25, 31, 55]], [&"boots", &"gloves", &"armor", &"inner_garment"], &"evasion", 60, true),
		# Suffixes — offense/utility
		_a(&"crit_chance", "of the Hawk", false, &"crit_chance", F, [[1, 0.01, 0.02], [12, 0.025, 0.04], [25, 0.045, 0.06]], WEAP + JEW + [&"gloves", &"helm"], &"crit_chance"),
		_a(&"crit_damage", "of Ruin", false, &"crit_damage", F, [[5, 0.08, 0.15], [15, 0.16, 0.25], [30, 0.26, 0.40]], WEAP + JEW, &"crit_damage", 70),
		_a(&"attack_speed", "of Fury", false, &"attack_speed", I, [[1, 0.04, 0.07], [12, 0.08, 0.12], [25, 0.13, 0.18]], WEAP + [&"gloves"] + JEW, &"attack_speed", 80),
		_a(&"cast_speed", "of Incantation", false, &"cast_speed", I, [[1, 0.04, 0.07], [12, 0.08, 0.12], [25, 0.13, 0.18]], WEAP + [&"gloves", &"helm"] + JEW, &"cast_speed", 80),
		_a(&"move_speed", "of Haste", false, &"move_speed", I, [[1, 0.04, 0.06], [12, 0.07, 0.10], [25, 0.11, 0.14]], [&"boots"], &"move_speed", 120),
		_a(&"cdr", "of Recurrence", false, &"cdr", F, [[10, 0.03, 0.05], [25, 0.06, 0.09]], [&"helm", &"accessory", &"gloves"], &"cdr", 50),
		_a(&"life_leech", "of the Leech", false, &"life_leech", F, [[5, 0.01, 0.02], [18, 0.025, 0.04]], WEAP + JEW + [&"gloves"], &"life_leech", 50),
		_a(&"mana_leech", "of the Siphon", false, &"mana_leech", F, [[5, 0.01, 0.02], [18, 0.025, 0.04]], WEAP + JEW, &"mana_leech", 40),
		_a(&"impact_strength", "of Thunderous Blows", false, &"impact_strength", I, [[1, 0.08, 0.14], [15, 0.15, 0.25]], WEAP + [&"gloves", &"boots"], &"impact_strength", 60),
		_a(&"knockback_res", "of the Anchor", false, &"knockback_res", F, [[1, 0.05, 0.08], [15, 0.09, 0.14]], [&"boots", &"armor"], &"knockback_res", 60),
		_a(&"status_res", "of Resolve", false, &"status_res", F, [[1, 0.05, 0.08], [15, 0.09, 0.15]], ARM + JEW, &"status_res", 60),
		_a(&"status_power", "of Affliction", false, &"status_power", I, [[1, 0.10, 0.18], [15, 0.19, 0.30]], WEAP + JEW + [&"gloves"], &"status_power", 60),
		_a(&"healing", "of Renewal", false, &"healing", I, [[1, 0.06, 0.12], [15, 0.13, 0.22]], ARM + JEW, &"healing", 40),
		_a(&"magic_find", "of Fortune", false, &"magic_find", F, [[1, 0.06, 0.12], [15, 0.13, 0.22]], JEW + [&"helm", &"boots"], &"magic_find", 40),
		_a(&"pen_fire", "of Searing", false, &"pen_fire", F, [[12, 0.05, 0.08], [28, 0.09, 0.14]], WEAP + JEW, &"pen_fire", 30),
		_a(&"pen_elemental", "of Piercing", false, &"pen_elemental", F, [[10, 0.04, 0.06], [25, 0.07, 0.10]], WEAP + JEW, &"pen_elemental", 30),
		_a(&"pen_armor", "of Sundering", false, &"pen_armor", F, [[12, 0.05, 0.08], [28, 0.09, 0.14]], WEAP + JEW, &"pen_armor", 30),
		_a(&"skill_levels", "of Mastery", false, &"skill_levels", F, [[8, 1, 1], [24, 2, 2]], WEAP + [&"helm", &"accessory"], &"skill_levels", 25, true, ELITE),
	]
	return out

static func _p(id: StringName, name: String, desc: String, flag: StringName, mag: float, cats: Array, cls := &"", mods := [], tier := &"legendary") -> LegendaryPowerDef:
	var p := LegendaryPowerDef.new()
	p.id = id
	p.display_name = name
	p.description = desc
	p.flag = flag
	p.magnitude = mag
	p.categories = cats
	p.class_hint = cls
	p.modifiers = mods
	p.tier = tier
	return p

static func powers() -> Array:
	return [
		# ---- Mythical: rare magical properties ----
		_p(&"m_embersoul", "Embersoul", "Your hits have a 10% chance to ignite (strong Burning buildup).", &"hit_ignite", 0.10, [&"weapon", &"gloves", &"accessory"], &"", [], &"mythical"),
		_p(&"m_frostguard", "Frostguard", "Enemies that hit you are Chilled.", &"thorns_chill", 1.0, [&"armor", &"shield", &"inner_garment"], &"", [], &"mythical"),
		_p(&"m_vampiric", "Vampiric", "Critical hits heal you for 3% of Maximum HP.", &"crit_heal", 0.03, [&"weapon", &"accessory"], &"", [], &"mythical"),
		_p(&"m_swiftness", "Windswift", "After dodging, gain 20% more Movement Speed for 2 s.", &"dodge_haste", 0.2, [&"boots", &"gloves"], &"", [], &"mythical"),
		_p(&"m_bastion", "Bastion", "While below 35% HP you take 15% less damage.", &"low_hp_dr", 0.15, [&"armor", &"helm", &"shield"], &"", [], &"mythical"),
		_p(&"m_aetherwell", "Aetherwell", "+1 maximum Arcane Charge and spells restore 1 Mana on hit.", &"mana_on_spell_hit", 1.0, [&"weapon", &"helm", &"accessory"], &"mage",
			[StatModifier.flat(&"arcane_max", 1.0)], &"mythical"),
		# ---- Legendary: build-defining powers ----
		_p(&"wallbreaker", "Wallbreaker's", "Impact damage from knockback collisions is doubled.", &"impact_double", 1.0, [], &"knight",
			[StatModifier.inc(&"impact_damage", 1.0)]),
		_p(&"echoing_guard", "Echoing", "Blocking creates a shockwave dealing 60% weapon damage around you (1 s cooldown).", &"block_shockwave", 0.6, [&"shield", &"armor", &"gloves"], &"knight"),
		_p(&"relentless", "Relentless", "Critical hits reduce all skill cooldowns by 0.5 seconds.", &"crit_cdr", 0.5, [&"weapon", &"accessory", &"gloves"]),
		_p(&"pyre", "Pyrelord's", "Burning spreads to one nearby enemy every second.", &"burn_spread", 1.0, [&"weapon", &"helm", &"accessory"], &"mage"),
		_p(&"frostbite", "Frostbitten", "Frozen enemies take 40% more impact damage and shatter on death, chilling nearby foes.", &"frozen_impact", 0.4, [&"weapon", &"gloves", &"accessory"]),
		_p(&"conductor", "Conductor's", "Chain Lightning chains 3 additional times against Wet targets.", &"wet_chains", 3.0, [&"weapon", &"helm"], &"mage"),
		_p(&"bloodthirst", "Bloodthirsty", "Kills restore 4% of Maximum HP.", &"kill_heal", 0.04, [], &""),
		_p(&"stormstride", "Stormstriding", "Dodging or blinking leaves a crackling trail that Shocks enemies.", &"dodge_trail", 1.0, [&"boots"]),
		_p(&"valorous", "Valorous", "Valor never decays and you start fights with 30 Valor.", &"valor_hold", 30.0, [&"armor", &"helm", &"accessory"], &"knight"),
		_p(&"overflow", "Overflowing", "At maximum Arcane Charge your spells cost no Mana.", &"arcane_free", 1.0, [&"weapon", &"armor", &"accessory"], &"mage"),
		_p(&"stillwater", "Stillwater", "Mana regeneration is tripled while you stand still.", &"still_mana", 2.0, [&"armor", &"inner_garment", &"accessory"], &"mage"),
		# ---- Aether: altered abilities ----
		_p(&"a_fifth_stagger", "Dawnbreaker", "Every fifth attack deals massive stagger and releases a radiant shockwave.", &"fifth_stagger", 1.0, [&"weapon"], &"knight", [], &"aether"),
		_p(&"a_crit_lightning", "Riftborn", "Critical attacks release chain lightning at up to 3 nearby enemies (50% of the hit as Lightning).", &"crit_lightning", 0.5, [&"weapon", &"gloves", &"accessory"], &"", [], &"aether"),
		_p(&"a_firebolt_split", "Starwhisper", "Firebolt always splits into three projectiles.", &"firebolt_split", 1.0, [&"weapon", &"helm"], &"mage", [], &"aether"),
		_p(&"a_frozen_explode", "Winter's", "Frozen enemies explode when killed, dealing 30% of their Maximum HP as Ice damage around them.", &"frozen_explode", 0.3, [&"weapon", &"gloves", &"accessory"], &"", [], &"aether"),
		_p(&"a_still_mana", "Stillness", "Standing still for 1 s increases Mana regeneration by 150% and HP regeneration by 50%.", &"still_mana", 1.5, [&"accessory", &"armor"], &"", [], &"aether"),
		_p(&"a_cleave_wave", "Aether-edged", "Cleave releases a travelling Aether wave (80% of Cleave's damage as Light).", &"cleave_wave", 0.8, [&"weapon", &"gloves"], &"knight", [], &"aether"),
		_p(&"a_blink_nova", "Riftwalker's", "Blink leaves a Frost Nova at the point you left.", &"blink_nova", 1.0, [&"boots", &"helm", &"accessory"], &"mage", [], &"aether"),
		_p(&"a_overflow_pulse", "Aetherheart", "Every 10 s, your next skill releases an Aether pulse dealing 120% weapon or spell damage around you.", &"aether_heartbeat", 1.2, [&"accessory", &"armor"], &"", [], &"aether"),
	]
