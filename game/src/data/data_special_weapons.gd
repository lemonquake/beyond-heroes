class_name DataSpecialWeapons
## bh-024 / bh-026: Legendary story equipment made from the sculpts in models/special_weapons/ — the Ember Dragon set,
## forged at the Dragonforge: the last Legendary set Aljay wore while he was still human, in his last battle as a man
## (the Night of Black Wings, docs/LORE.md §10). Three pieces: the Ember Dragonslayer (sword), the Aegis of Fragnir
## (shield) and the Ember Dragonhide (cuirass). Models and icons: tools/blender/items/special_set.py; the cuirass fitted
## to the hero: tools/blender/hero/hero_wear_special.py.
##
## Only knights wear it: the Knight among heroes, and the knight-type Tempos (Swordsman, Warden). The pieces are story
## pieces: never loot, stock or crafts. The "alj" code (Cheats) hands the hero the whole set as Unbound copies: no level
## or attribute requirement, wearable from Class E (instead of the Legendary gate, Class B), with four sockets open.
## docs/SPECIAL_WEAPONS.md.

const SET_ID := &"ember_dragon"
const SET_NAME := "Ember Dragon"
## Hero class ids and Tempo class ids that may wear the set.
const WEARERS: Array[StringName] = [&"knight", &"swordsman", &"warden"]
const LEVEL := 30
## Unbound copies (ItemInstance.unbound): the lowest hero tier that may wear them (1 = Class E) and their open sockets.
const UNBOUND_RANK := 1
const UNBOUND_SOCKETS := 4

## [id, name, category, weapon type, lore]
const ROWS := [
	[&"ember_dragonslayer", "Ember Dragonslayer", &"weapon", &"sword",
		"Forged at the Dragonforge for Aljay of Malasugue. It hung at his side beside the Dusk-Piercer on the Night of Black Wings, his last battle as a man; the ember in its blade has never cooled."],
	[&"aegis_of_fragnir", "Aegis of Fragnir", &"shield", &"",
		"Two ember drakes coil on its face. It turned the Dusk Tyrant's fire on the Night of Black Wings, the last night the man who held it was only a man."],
	[&"ember_dragonhide", "Ember Dragonhide", &"armor", &"",
		"The last Legendary armour Aljay wore while he was still human. When Vharzul's blood poured into him, black scales grew over the ember plates, and this was lost beneath them."],
]

const MODEL := "res://assets/items/%s.glb"

static func bases() -> Array:
	var out := []
	for r in ROWS:
		var cat: StringName = r[2]
		var b := DataItems._b(StringName(r[0]), "", cat, "", {"unique_name": r[1], "fixed_rarity": BH.Rarity.LEGENDARY,
			"set_id": SET_ID, "class_hint": &"knight", "wearers": WEARERS.duplicate(), "story": true,
			"level_req": LEVEL, "drop_level": LEVEL, "requirements": {&"str": 40}, "value": 400 + LEVEL * 8,
			"drop_weight": 0, "tier": 3, "weight_class": &"heavy", "lore": r[4]})
		match cat:
			&"weapon":
				var aps := 1.35
				var dmg := DataItems.roster_damage(StringName(r[3]), LEVEL, aps)
				b.weapon_type = StringName(r[3])
				b.attacks_per_second = aps
				b.damage_min = dmg.x * 1.15
				b.damage_max = dmg.y * 1.15
				b.element = Elements.FIRE
				b.element_share = 0.35
				b.display_name = "Sword"
			&"shield":
				b.defense = 46.0
				b.block_chance = 0.20
				b.block_strength = 0.35
				b.implicit = [StatModifier.flat(Elements.res_key(Elements.FIRE), 0.10)]
				b.display_name = "Shield"
			_:
				b.defense = 66.0
				b.implicit = [StatModifier.flat(Elements.res_key(Elements.FIRE), 0.10), StatModifier.inc(&"max_hp", 0.05)]
				b.display_name = "Cuirass"
		b.model = MODEL % r[0]
		b.icon = DataItems.ICON3D % r[0]
		b.weight = DataItems.default_weight(b)
		out.append(b)
	return out

static func sets() -> Array:
	var s := SetDef.new()
	s.id = SET_ID
	s.display_name = SET_NAME
	s.class_hint = &"knight"
	s.pieces = ids()
	s.bonuses = {
		2: {"desc": "+10% Defense and +8% maximum health.", "mods": [StatModifier.inc(&"defense", 0.10), StatModifier.inc(&"max_hp", 0.08)]},
		3: {"desc": "+15% Fire damage and +10% Fire resistance; hits have a 15% chance to ignite enemies.",
			"mods": [StatModifier.inc(Elements.dmg_key(Elements.FIRE), 0.15), StatModifier.flat(Elements.res_key(Elements.FIRE), 0.10)],
			"flags": {&"hit_ignite": 0.15}},
	}
	s.lore = "Aljay's regalia from the Dragonforge, worn in his last battle as a man. Knights only."
	return [s]

static func ids() -> Array:
	return ROWS.map(func(r): return StringName(r[0]))

static func is_special(base: ItemBaseDef) -> bool:
	return base != null and base.set_id == SET_ID

## Whether a hero class or Tempo class may wear a base (bases without `wearers` fit everyone).
static func can_wear(base: ItemBaseDef, class_id: StringName) -> bool:
	return base == null or base.wearers.is_empty() or base.wearers.has(class_id)

## "Knights only (Tempos: Swordsman, Warden)" for the tooltip and the refusals.
static func wearers_text(base: ItemBaseDef) -> String:
	var heroes: Array[String] = []
	var tempos: Array[String] = []
	for w in base.wearers:
		var cd := DB.class_def(StringName(w))
		if cd != null:
			heroes.append(cd.display_name + "s")
		elif DataTempos.CLASSES.has(StringName(w)):
			tempos.append(String(DataTempos.CLASSES[StringName(w)].name))
	var t := " and ".join(heroes) + " only"
	if not tempos.is_empty():
		t += " (Tempos: %s)" % ", ".join(tempos)
	return t

## An Unbound copy of a special piece (or of any equipment base), at the hero's level, with its sockets open.
static func unbound(base_id: StringName, level: int) -> ItemInstance:
	var it := DB.make_item(base_id, BH.Rarity.LEGENDARY, maxi(1, level), hash("alj%s" % base_id))
	if it:
		it.unbound = true
		it.sockets = mini(UNBOUND_SOCKETS, Sockets.max_sockets(it))
		it.gems = []
		for i in it.sockets:
			it.gems.append("")
	return it
