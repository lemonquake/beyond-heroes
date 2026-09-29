class_name DataBossSets
## Complete equipment collections found only on actual bosses of level 30 or higher.
## All sets remain possible. Current ownership increases collection odds without guaranteeing the next piece.

const MIN_LEVEL := 30
const CLASS_WEIGHT := 2.0
const PARTIAL_SET_WEIGHT := 4.0
const MISSING_PIECE_WEIGHT := 6.0
const ROWS := [
	["dragonforge", "Dragonforge", "knight", "axe", Elements.FIRE, "hit_ignite", 0.15, "Hits have a 15% chance to ignite enemies."],
	["truth_of_raikuru", "Truth of Raikuru", "ranger", "crossbow", Elements.LIGHTNING, "crit_lightning", 0.30, "Critical hits chain 30% of their damage as lightning."],
	["crimson_glory", "Crimson Glory", "knight", "sword", Elements.FIRE, "block_shockwave", 0.60, "Blocks release a 60% weapon-damage shockwave (1 s cooldown)."],
	["grievance_of_the_fairy", "Grievance of the Fairy", "ranger", "bow", Elements.EARTH, "kill_heal", 0.025, "Kills restore 2.5% of maximum health."],
	["wailing_mistress", "Wailing Mistress", "mage", "staff", Elements.DARK, "mana_on_spell_hit", 1.5, "Spell hits restore 1.5 Mana."],
	["winter_court", "Winter Court", "mage", "wand", Elements.ICE, "thorns_chill", 1.0, "Enemies that hit you are Chilled."],
	["sunken_crown", "Sunken Crown", "knight", "spear", Elements.WATER, "low_hp_dr", 0.15, "Take 15% less damage while below 35% health."],
	["thunder_abbot", "Thunder Abbot", "mage", "staff", Elements.LIGHTNING, "wet_chains", 2.0, "Chain Lightning gains 2 extra jumps against Wet targets."],
	["ashfall_pilgrim", "Ashfall Pilgrim", "mage", "wand", Elements.FIRE, "burn_spread", 1.0, "Fire hits spread Burning from burning targets to nearby foes."],
	["starfall_hunter", "Starfall Hunter", "ranger", "crossbow", Elements.LIGHT, "crit_cdr", 0.25, "Critical hits reduce skill cooldowns by 0.25 seconds."],
	["gale_nomad", "Gale Nomad", "ranger", "bow", Elements.WIND, "dodge_haste", 0.18, "Dodging grants 18% more movement speed for 2 seconds."],
	["obsidian_oath", "Obsidian Oath", "knight", "greatsword", Elements.DARK, "fifth_stagger", 1.0, "Every fifth attack releases a staggering radiant shockwave."],
	["pale_requiem", "Pale Requiem", "shadowblade", "dagger", Elements.ICE, "crit_heal", 0.025, "Critical hits restore 2.5% of maximum health."],
	["serpent_veil", "Serpent Veil", "shadowblade", "claw", Elements.EARTH, "evade_mana", 4.0, "Evading an attack restores 4 Mana."],
	["eclipse_dancer", "Eclipse Dancer", "shadowblade", "dagger", Elements.DARK, "dodge_trail", 1.0, "Dodging leaves a lightning trail that Shocks enemies."],
]
const TWO_HANDED := ["bow", "crossbow", "staff", "spear", "greatsword"]
const SLOT_LABELS := {
	&"main_weapon": "Weapon", &"sub_weapon": "Shield", &"helm": "Crown", &"inner_garment": "Vestment", &"armor": "Armor",
	&"gloves_1": "Left Gauntlet", &"gloves_2": "Right Gauntlet", &"boots_1": "Left Greave", &"boots_2": "Right Greave",
	&"accessory_1": "Signet", &"accessory_2": "Seal", &"accessory_3": "Pendant", &"accessory_4": "Brooch",
}

static func row(set_id: StringName) -> Array:
	for entry in ROWS:
		if StringName(entry[0]) == set_id:
			return entry
	return []

static func slots_for_set(set_id: StringName) -> Array[StringName]:
	var entry := row(set_id)
	var slots: Array[StringName] = BH.SLOTS.duplicate()
	if entry.is_empty():
		return []
	if entry[3] in TWO_HANDED:
		slots.erase(&"sub_weapon")
	return slots

static func piece_id(set_id: StringName, slot: StringName) -> StringName:
	return StringName("boss_%s_%s" % [set_id, slot])

static func bases() -> Array:
	var out := []
	for entry in ROWS:
		var set_id := StringName(entry[0])
		var cls := StringName(entry[2])
		var weapon := StringName(entry[3])
		for slot in slots_for_set(set_id):
			var category: StringName = &"weapon" if slot == &"main_weapon" else (&"shield" if slot == &"sub_weapon" else slot)
			if String(slot).begins_with("gloves_"):
				category = &"gloves"
			elif String(slot).begins_with("boots_"):
				category = &"boots"
			elif String(slot).begins_with("accessory_"):
				category = &"accessory"
			var attr: StringName = &"str" if cls == &"knight" else (&"int" if cls == &"mage" else &"dex")
			var b := DataItems._b(piece_id(set_id, slot), "%s %s" % [entry[1], SLOT_LABELS[slot]], category, "", {
				"set_id": set_id, "class_hint": cls, "level_req": MIN_LEVEL, "drop_level": MIN_LEVEL,
				"fixed_rarity": BH.Rarity.MASTER, "drop_weight": 0, "boss_exclusive": true,
				"equip_slots": [slot], "requirements": {attr: 32}, "value": 200, "tier": 3,
				"weight_class": &"heavy" if cls == &"knight" else &"cloth",
				"lore": "A piece of %s, found only on bosses of level 30 or higher." % entry[1]})
			b.model = ItemBaseDef.ITEM_MODEL % b.id
			b.icon = DataItems.ICON3D % b.id
			if category == &"weapon":
				b.weapon_type = weapon
				b.display_name = "%s %s" % [entry[1], String(weapon).capitalize()]
				b.attacks_per_second = float({&"sword": 1.45, &"axe": 1.25, &"spear": 1.2, &"greatsword": 0.95,
					&"bow": 1.1, &"crossbow": 0.82, &"staff": 1.0, &"wand": 1.6, &"dagger": 2.0, &"claw": 1.8}.get(weapon, 1.2))
				var damage := DataItems.roster_damage(weapon, MIN_LEVEL, b.attacks_per_second)
				b.damage_min = damage.x
				b.damage_max = damage.y
				b.element = int(entry[4])
				b.element_share = 1.0 if cls == &"mage" else 0.30
				if cls == &"mage":
					b.implicit = [StatModifier.inc(&"magic_damage", 0.18)]
			elif category != &"accessory":
				var armor_budget: float = {&"armor": 57.0, &"helm": 28.5, &"inner_garment": 18.0,
					&"gloves": 14.0, &"boots": 17.0, &"shield": 40.0}.get(category, 0.0)
				b.defense = armor_budget * (1.0 if cls == &"knight" else 0.6)
				if category == &"shield":
					b.block_chance = 0.16
					b.block_strength = 0.30
			elif slot == &"accessory_1":
				b.implicit = [StatModifier.flat(attr, 3.0)]
			elif slot == &"accessory_2":
				b.implicit = [StatModifier.flat(&"max_hp", 30.0)]
			elif slot == &"accessory_3":
				b.implicit = [StatModifier.flat(&"max_mana", 20.0)]
			else:
				b.implicit = [StatModifier.flat(&"status_res", 0.04)]
			b.weight = DataItems.default_weight(b)
			if category == &"weapon":
				b.weight += 0.05 + ROWS.find(entry) * 0.02
			if category == &"boots":
				b.implicit.append(StatModifier.inc(&"move_speed", 0.04 if cls == &"knight" else 0.06))
			out.append(b)
	return out

static func sets() -> Array:
	var out := []
	for entry in ROWS:
		var s := SetDef.new()
		s.id = StringName(entry[0])
		s.display_name = entry[1]
		s.class_hint = StringName(entry[2])
		for slot in slots_for_set(s.id):
			s.pieces.append(piece_id(s.id, slot))
		var first := _first_bonus(s.class_hint)
		var element := int(entry[4])
		s.bonuses = {
			3: first,
			6: {"desc": "+12%% %s damage and +6%% %s resistance." % [Elements.NAMES[element], Elements.NAMES[element]],
				"mods": [StatModifier.inc(Elements.dmg_key(element), 0.12), StatModifier.flat(Elements.res_key(element), 0.06)]},
			s.pieces.size(): {"desc": entry[7], "flags": {StringName(entry[5]): float(entry[6])}},
		}
		s.lore = "Complete %s with trophies from bosses of level 30 or higher." % s.display_name
		out.append(s)
	return out

static func _first_bonus(cls: StringName) -> Dictionary:
	match cls:
		&"knight": return {"desc": "+10% Defense and +8% maximum health.", "mods": [StatModifier.inc(&"defense", 0.10), StatModifier.inc(&"max_hp", 0.08)]}
		&"ranger": return {"desc": "+12% projectile damage and +25 Accuracy.", "mods": [StatModifier.inc(&"projectile_damage", 0.12), StatModifier.flat(&"accuracy", 25.0)]}
		&"mage": return {"desc": "+10% maximum Mana and +8% cast speed.", "mods": [StatModifier.inc(&"max_mana", 0.10), StatModifier.inc(&"cast_speed", 0.08)]}
	return {"desc": "+8% attack speed and +12% Evasion.", "mods": [StatModifier.inc(&"attack_speed", 0.08), StatModifier.inc(&"evasion", 0.12)]}

## Bag, worn gear, companions and pending legacy recovery are current ownership; duplicates count only once.
static func owned_pieces(hero: HeroData, extra_items: Array = []) -> Dictionary:
	var owned := {}
	if hero == null:
		return owned
	var items: Array = hero.inventory.cells + hero.equipment.equipped_items() + hero.equipment.recovered_items + extra_items
	for t in hero.tempos + hero.spirit_hall:
		items.append_array(t.equipment.equipped_items())
		items.append_array(t.equipment.recovered_items)
	for item: ItemInstance in items:
		if item != null and item.base.boss_exclusive:
			owned[item.base.id] = true
	return owned

static func set_weight(entry: Array, owned: Dictionary, class_id: StringName) -> float:
	var s := DB.item_set(StringName(entry[0]))
	var count := 0
	for id in s.pieces:
		if owned.has(id):
			count += 1
	var weight := CLASS_WEIGHT if StringName(entry[2]) == class_id else 1.0
	return weight * (PARTIAL_SET_WEIGHT if count > 0 and count < s.pieces.size() else 1.0)

static func eligible(enemy: Enemy) -> bool:
	if enemy == null or enemy.def == null or enemy.level < MIN_LEVEL:
		return false
	# Dungeon lords do not respawn: their Usurpers and named depth guardians keep these sets farmable.
	return (enemy.is_boss and enemy.def.archetype == &"boss") or enemy.miniboss.has("raid_only") or (enemy.is_miniboss() and bool(enemy.get_meta(&"depth_guardian", false)))

## Exactly one boss-set item. No other equipment generator calls this path.
static func roll(enemy: Enemy, hero: HeroData, rng: RandomNumberGenerator, extra_items: Array = []) -> ItemInstance:
	if not eligible(enemy):
		return null
	var owned := owned_pieces(hero, extra_items)
	var cls: StringName = hero.cls.id if hero != null and hero.cls != null else &""
	var weights := []
	for entry in ROWS:
		weights.append(set_weight(entry, owned, cls))
	var picked: Array = ROWS[_weighted_index(weights, rng)]
	var set_def := DB.item_set(StringName(picked[0]))
	weights.clear()
	for id in set_def.pieces:
		weights.append(1.0 if owned.has(id) else MISSING_PIECE_WEIGHT)
	var id: StringName = set_def.pieces[_weighted_index(weights, rng)]
	return DB.make_item(id, BH.Rarity.MASTER, clampi(enemy.level + 2, MIN_LEVEL, BH.LEVEL_CAP + 5), rng.randi())

static func _weighted_index(weights: Array, rng: RandomNumberGenerator) -> int:
	var total := 0.0
	for weight in weights:
		total += float(weight)
	var cursor := rng.randf() * total
	for i in weights.size():
		cursor -= float(weights[i])
		if cursor < 0.0:
			return i
	return weights.size() - 1
