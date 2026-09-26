class_name DataClasses
## Knight and Mage definitions.

static func build() -> Array:
	var knight := ClassDef.new()
	knight.id = &"knight"
	knight.display_name = "Knight"
	knight.description = "A martial champion of steel and resolve. Blocks, staggers and hurls foes into the walls. Builds Valor by fighting up close and spends it on devastating strikes."
	knight.model_path = "res://assets/characters/knight.glb"
	knight.base_attributes = {&"str": 14, &"agi": 9, &"int": 5, &"wis": 6, &"spi": 9, &"dex": 10}
	knight.growth_per_level = {&"str": 1.5, &"agi": 0.5, &"int": 0.0, &"wis": 0.25, &"spi": 0.5, &"dex": 0.5}
	knight.base_hp = 120.0
	knight.hp_per_level = 12.0
	knight.base_mana = 30.0
	knight.mana_per_level = 2.0
	knight.mana_regen_mult = 0.8
	knight.base_defense = 20.0
	knight.base_move_speed = 5.2
	knight.base_knockback_res = 0.15
	knight.base_poise = 45.0
	knight.dodge_cooldown = 1.4
	knight.resource_kind = &"valor"
	knight.class_modifiers = [
		StatModifier.inc(&"defense", 0.10, "Knight: Plate Training"),
		StatModifier.flat(&"block_strength", 0.10, "Knight: Shield Discipline"),
		StatModifier.inc(&"impact_strength", 0.15, "Knight: Heavy Hands"),
	]
	knight.weapon_mastery = {&"sword": 0.10, &"greatsword": 0.10, &"axe": 0.10, &"spear": 0.10}
	knight.starting_items = [&"iron_longsword", &"warden_kite_shield", &"padded_gambeson", &"iron_hauberk", &"iron_helm"]
	knight.starting_skills = [&"cleave"]
	knight.skill_tree_id = &"knight_skills"
	knight.talent_tree_id = &"knight_talents"
	knight.tint = Color(0.75, 0.18, 0.16)
	knight.tagline = "Ancient-tech warrior of the Dawn"
	knight.difficulty = 1
	knight.class_resource_name = "Valor"
	knight.resource_desc = "Builds as you land hits, block, parry and hold your ground near enemies; fades out of combat. At 50 Valor you are Resolute: 10% more physical damage and harder knockback. Judgment spends it all."
	knight.strengths = ["Heavy armor and a shield that blocks and parries", "Knocks enemies into walls for impact damage", "Staggers and breaks guards", "Forgiving: high HP and poise"]
	knight.weaknesses = ["Short reach; must close the distance", "Low Mana: few spells", "Slow against fast, ranged enemies"]
	knight.major_attributes = [&"str", &"dex", &"spi"]

	var mage := ClassDef.new()
	mage.id = &"mage"
	mage.display_name = "Mage"
	mage.description = "A scholar of the eight elements. Fragile but devastating: combines Wet, Chill and Shock, blinks out of danger, and builds Arcane Charge to push spells beyond their limits — at a price."
	mage.model_path = "res://assets/characters/mage.glb"
	mage.base_attributes = {&"str": 5, &"agi": 8, &"int": 15, &"wis": 11, &"spi": 7, &"dex": 7}
	mage.growth_per_level = {&"str": 0.25, &"agi": 0.5, &"int": 1.5, &"wis": 0.75, &"spi": 0.5, &"dex": 0.25}
	mage.base_hp = 80.0
	mage.hp_per_level = 7.0
	mage.base_mana = 80.0
	mage.mana_per_level = 6.0
	mage.mana_regen_mult = 1.25
	mage.base_defense = 5.0
	mage.base_move_speed = 5.0
	mage.base_knockback_res = 0.0
	mage.base_poise = 25.0
	mage.dodge_cooldown = 1.0
	mage.resource_kind = &"arcane"
	mage.class_modifiers = [
		StatModifier.inc(&"elemental_damage", 0.10, "Mage: Elemental Attunement"),
		StatModifier.flat(&"mana_cost_reduction", 0.05, "Mage: Efficient Channeling"),
	]
	mage.weapon_mastery = {&"staff": 0.10, &"wand": 0.10}
	mage.starting_items = [&"ashwood_staff", &"silk_undershirt", &"apprentice_robe", &"linen_hood"]
	mage.starting_skills = [&"firebolt"]
	mage.skill_tree_id = &"mage_skills"
	mage.talent_tree_id = &"mage_talents"
	mage.tint = Color(0.32, 0.26, 0.78)
	mage.tagline = "Arcane traveler of the eight elements"
	mage.difficulty = 2
	mage.class_resource_name = "Arcane Charge"
	mage.resource_desc = "Every spell adds a charge (up to 5): each charge gives 6% more spell damage and 8% higher Mana cost, and at 3+ some spells change shape. At full charge you are Overcharged and take 15% more damage. Charges fade after 4 s without casting."
	mage.strengths = ["Devastating elemental combinations (Wet + Shock, Chill + Freeze)", "Blink escapes and area control", "Strikes from range"]
	mage.weaknesses = ["Fragile: low HP and armor", "Mana-hungry; potions and positioning matter", "Weak when surrounded"]
	mage.major_attributes = [&"int", &"wis", &"spi"]
	return [knight, mage]
