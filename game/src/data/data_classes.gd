class_name DataClasses
## Hero classes: Knight, Mage and (bh-010) Ranger and Shadowblade.

static func build() -> Array:
	var knight := ClassDef.new()
	knight.id = &"knight"
	knight.display_name = "Knight"
	knight.description = "A durable melee fighter who builds Valor through attacks and blocks. Learn knockback resistance, counterattacks, damage return and extra regeneration for each debuff. Auras support nearby allies."
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
	knight.weapon_mastery = {&"sword": 0.10, &"greatsword": 0.10, &"axe": 0.10, &"greataxe": 0.10, &"spear": 0.10, &"club": 0.10, &"javelin": 0.05}
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
	mage.description = "A ranged spellcaster who combines elemental damage with gravity pulls, stuns and curses. Meteor Strike deals heavy area damage; Mana Siphon and Arcane Arts help manage expensive spells."
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
	var ranger := ClassDef.new()
	ranger.id = &"ranger"
	ranger.display_name = "Ranger"
	ranger.description = "A ranged fighter using bows, javelins and traps. Learn Knee Shot to stun enemies and Split Shot to fire additional arrows. Builds Focus at a distance and spends it on stronger shots."
	ranger.model_path = "res://assets/characters/ranger.glb"
	ranger.base_attributes = {&"str": 8, &"agi": 13, &"int": 6, &"wis": 8, &"spi": 7, &"dex": 14}
	ranger.growth_per_level = {&"str": 0.25, &"agi": 0.75, &"int": 0.0, &"wis": 0.5, &"spi": 0.25, &"dex": 1.25}
	ranger.base_hp = 95.0
	ranger.hp_per_level = 9.0
	ranger.base_mana = 50.0
	ranger.mana_per_level = 4.0
	ranger.mana_regen_mult = 1.0
	ranger.base_defense = 10.0
	ranger.base_move_speed = 5.4
	ranger.base_knockback_res = 0.05
	ranger.base_poise = 30.0
	ranger.dodge_cooldown = 1.0
	ranger.resource_kind = &"focus"
	ranger.class_modifiers = [
		StatModifier.inc(&"projectile_damage", 0.10, "Ranger: Fletching"),
		StatModifier.inc(&"evasion", 0.10, "Ranger: Woodcraft"),
	]
	ranger.weapon_mastery = {&"bow": 0.12, &"javelin": 0.10, &"spear": 0.05, &"dagger": 0.05}
	ranger.starting_items = [&"hunters_bow", &"padded_gambeson", &"linen_hood", &"soft_boot"]
	ranger.starting_skills = [&"power_shot"]
	ranger.skill_tree_id = &"ranger_skills"
	ranger.talent_tree_id = &"ranger_talents"
	ranger.tint = Color(0.3, 0.55, 0.28)
	ranger.tagline = "Hunter of the broken frontier"
	ranger.difficulty = 2
	ranger.class_resource_name = "Focus"
	ranger.resource_desc = "Builds while you fight from a distance: +6 per second in combat while no enemy is within 5 m, +3 per ranged hit. An enemy within 3 m drains it. At 60 Focus you are Steady: +10% Critical Chance. Deadeye spends it all."
	ranger.strengths = ["Deadly at range: arrows, javelins and piercing shots", "Traps and snares control the fight", "Fast and evasive; Vault escapes danger"]
	ranger.weaknesses = ["Loses Focus and damage when enemies close in", "Light armor and modest HP", "Needs room to kite"]
	ranger.major_attributes = [&"dex", &"agi", &"wis"]

	var shadow := ClassDef.new()
	shadow.id = &"shadowblade"
	shadow.display_name = "Shadowblade"
	shadow.description = "A fast melee fighter who builds Combo for finishers. Learn Double Attack, brief paralyzing slows, lifesteal on every second attack and Bloodcurse to reduce enemy healing."
	shadow.model_path = "res://assets/characters/shadowblade.glb"
	shadow.base_attributes = {&"str": 10, &"agi": 15, &"int": 7, &"wis": 6, &"spi": 6, &"dex": 12}
	shadow.growth_per_level = {&"str": 0.5, &"agi": 1.25, &"int": 0.0, &"wis": 0.25, &"spi": 0.25, &"dex": 0.75}
	shadow.base_hp = 90.0
	shadow.hp_per_level = 8.5
	shadow.base_mana = 55.0
	shadow.mana_per_level = 4.5
	shadow.mana_regen_mult = 1.0
	shadow.base_defense = 8.0
	shadow.base_move_speed = 5.6
	shadow.base_knockback_res = 0.0
	shadow.base_poise = 26.0
	shadow.dodge_cooldown = 0.9
	shadow.resource_kind = &"combo"
	shadow.class_modifiers = [
		StatModifier.flat(&"crit_chance", 0.03, "Shadowblade: Killer's Instinct"),
		StatModifier.inc(&"evasion", 0.10, "Shadowblade: Footwork"),
	]
	shadow.weapon_mastery = {&"dagger": 0.12, &"claw": 0.12, &"knuckles": 0.08, &"sword": 0.04}
	shadow.starting_items = [&"rondel_dagger", &"rondel_dagger", &"padded_gambeson", &"linen_hood", &"soft_boot"]
	shadow.starting_skills = [&"twin_fang"]
	shadow.skill_tree_id = &"shadowblade_skills"
	shadow.talent_tree_id = &"shadowblade_talents"
	shadow.tint = Color(0.45, 0.2, 0.6)
	shadow.tagline = "Blade that walks between the lights"
	shadow.difficulty = 3
	shadow.class_resource_name = "Combo"
	shadow.resource_desc = "Builders and basic hits add Combo pips (up to 5; a critical builder hit adds one more). Finishers spend them all and hit harder per pip. At full Combo you are Poised: the next finisher always crits. Pips fade after 5 s without landing a hit."
	shadow.strengths = ["Huge single-target bursts with finishers", "Stealth, Shadow Step and fear keep you untouchable", "Poison and bleeding wear down tough foes"]
	shadow.weaknesses = ["Fragile: low HP and armor", "Must build Combo before it bursts", "Demands timing and positioning"]
	shadow.major_attributes = [&"agi", &"dex", &"str"]
	return [knight, mage, ranger, shadow]
