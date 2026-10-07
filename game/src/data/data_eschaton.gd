class_name DataEschaton
## bh-041: Eschaton — the tier past Primordial (BH.Rarity.ESCHATON). Primordial is the oldest thing in the world;
## Eschaton is the last. No monster carries it: only Lape the Ancient makes it, and only when the lot laid in his
## dishes is made of the highest tiers (LapeTrade.eschaton_chance). The Debug console's summoner can also make one.
##
## Catalogue (models and icons: tools/blender/items/eschaton_regalia.py, same ids):
##   * forty collections, ten per class; each is a set of helm, armour, inner garment, leggings, gauntlets, boots and a
##     jewel, and the knights' collections a shield as well:            esc_<collection>_<piece>
##   * ten weapons of every weapon type each class masters, made for that class (knight 7 types, mage 2, ranger 5,
##     shadowblade 4: 180 weapons):                                      esc_w_<class>_<type>_<0..9>
## So every class has ten Eschaton pieces of every equipment slot it wears and ten of every weapon it can wield.
##
## Strength: the base damage / Defense multiplier is x2.3 (Primordial x1.85, DataAscendant.TIER); eight top-tier
## enchantments, two Legendary and two Aether powers, high quality, eight sockets; every piece carries Unmaking, which
## grows with every Eschaton piece worn (Player._ascendant_procs); a collection's 2/4/6 pieces add damage and health,
## a class power, and a stronger Unmaking. They wear the Ascendant regalia pipeline (BossSetVisuals) and AscendantFx
## gives them their chrome light.

const R := BH.Rarity.ESCHATON
const LEVEL := 110                   # level to wear one (and Class SSS: DataGuilds.rank_for_rarity)
const ITEM_LEVEL := 120              # the level the pieces are authored at (Lape makes them at the hero's level if higher)

## [id, title, class, helm style, torso, jewel, element, 4-piece flag, magnitude, 4-piece text]
## (styles match tools/blender/items/eschaton_regalia.py COLLECTIONS)
const COLLECTIONS := [
	["doomsday_paragon", "Doomsday Paragon", &"knight", "great", "plate", "ring", Elements.LIGHT,
		&"block_shockwave", 2.0, "Blocking releases a shockwave of 200% weapon damage (1 s cooldown)."],
	["worldsend_bulwark", "Worldsend Bulwark", &"knight", "great", "plate", "ring", Elements.FIRE,
		&"low_hp_dr", 0.4, "Take 40% less damage while below 35% health."],
	["endbringer_sovereign", "Endbringer Sovereign", &"knight", "sallet", "plate", "ring", Elements.DARK,
		&"fifth_stagger", 1.0, "Every fifth attack staggers hard and releases a radiant shockwave."],
	["last_crown_marshal", "Last Crown Marshal", &"knight", "great", "plate", "ring", Elements.LIGHTNING,
		&"valor_hold", 60.0, "Valor never decays and you start every fight with 60 Valor."],
	["ruinmarch_herald", "Ruinmarch Herald", &"knight", "sallet", "plate", "ring", Elements.FIRE,
		&"cleave_wave", 2.0, "Cleave releases a travelling wave of 200% of its damage as Light."],
	["oblivion_warden", "Oblivion Warden", &"knight", "great", "plate", "ring", Elements.DARK,
		&"kill_heal", 0.1, "Kills restore 10% of maximum health."],
	["final_dawn_executor", "Final Dawn Executor", &"knight", "great", "plate", "ring", Elements.LIGHT,
		&"crit_cdr", 0.8, "Critical hits reduce every skill cooldown by 0.8 seconds."],
	["starless_throne", "Starless Throne", &"knight", "sallet", "plate", "ring", Elements.ICE,
		&"block_shockwave", 1.8, "Blocking releases a shockwave of 180% weapon damage (1 s cooldown)."],
	["ashen_apocalypse", "Ashen Apocalypse", &"knight", "great", "plate", "ring", Elements.WIND,
		&"low_hp_dr", 0.35, "Take 35% less damage while below 35% health."],
	["unmaker_vanguard", "Unmaker Vanguard", &"knight", "sallet", "plate", "ring", Elements.EARTH,
		&"kill_heal", 0.09, "Kills restore 9% of maximum health."],
	["void_unwritten", "Void Unwritten", &"mage", "hood", "mantle", "ring", Elements.DARK,
		&"arcane_free", 1.0, "At maximum Arcane Charge your spells cost no Mana."],
	["last_word_archon", "Last Word Archon", &"mage", "mitre", "mantle", "pendant", Elements.LIGHT,
		&"aether_heartbeat", 4.0, "Every 10 s your next skill releases a pulse of 400% spell damage around you."],
	["entropy_magus", "Entropy Magus", &"mage", "crown", "mantle", "ring", Elements.DARK,
		&"burn_spread", 1.0, "Burning spreads to a nearby enemy every second."],
	["null_choir", "Null Choir", &"mage", "circlet", "mantle", "pendant", Elements.WATER,
		&"wet_chains", 6.0, "Chain Lightning chains 6 more times against Wet targets."],
	["unmade_sky_sage", "Unmade Sky Sage", &"mage", "hood", "mantle", "ring", Elements.LIGHTNING,
		&"mana_on_spell_hit", 5.0, "Spell hits restore 5 Mana."],
	["silent_star_conclave", "Silent Star Conclave", &"mage", "mitre", "mantle", "pendant", Elements.LIGHT,
		&"firebolt_split", 1.0, "Firebolt always splits into three projectiles."],
	["ender_of_tomes", "Ender of Tomes", &"mage", "crown", "mantle", "ring", Elements.FIRE,
		&"aether_heartbeat", 3.6, "Every 10 s your next skill releases a pulse of 360% spell damage around you."],
	["mirrorless_oracle", "Mirrorless Oracle", &"mage", "circlet", "mantle", "pendant", Elements.ICE,
		&"frozen_explode", 0.7, "Frozen enemies explode on death for 70% of their maximum health as Ice."],
	["final_equation", "Final Equation", &"mage", "hood", "mantle", "ring", Elements.LIGHTNING,
		&"still_mana", 4.0, "Standing still for 1 s quadruples Mana regeneration."],
	["eclipse_sovereign", "Eclipse Sovereign", &"mage", "crown", "mantle", "pendant", Elements.DARK,
		&"arcane_free", 1.0, "At maximum Arcane Charge your spells cost no Mana."],
	["endtime_stalker", "Endtime Stalker", &"ranger", "sallet", "brigandine", "pendant", Elements.WIND,
		&"crit_lightning", 1.2, "Critical hits chain 120% of their damage as lightning to 3 enemies."],
	["last_arrow", "Last Arrow", &"ranger", "wrap", "brigandine", "brooch", Elements.FIRE,
		&"hit_ignite", 0.45, "Hits have a 45% chance to ignite."],
	["horizon_breaker", "Horizon Breaker", &"ranger", "circlet", "brigandine", "pendant", Elements.WATER,
		&"crit_sunflare", 1.2, "Critical hits flare 120% of their damage as Light onto enemies within 5 m."],
	["doomwind_hunter", "Doomwind Hunter", &"ranger", "hood", "brigandine", "brooch", Elements.WIND,
		&"kill_heal", 0.08, "Kills restore 8% of maximum health."],
	["extinction_volley", "Extinction Volley", &"ranger", "sallet", "brigandine", "pendant", Elements.DARK,
		&"crit_cdr", 0.8, "Critical hits reduce every skill cooldown by 0.8 seconds."],
	["skys_end_warden", "Sky's End Warden", &"ranger", "circlet", "brigandine", "brooch", Elements.LIGHT,
		&"crit_sunflare", 1.1, "Critical hits flare 110% of their damage as Light onto enemies within 5 m."],
	["ashfall_pathfinder", "Ashfall Pathfinder", &"ranger", "wrap", "brigandine", "pendant", Elements.FIRE,
		&"hit_ignite", 0.4, "Hits have a 40% chance to ignite."],
	["requiem_marksman", "Requiem Marksman", &"ranger", "hood", "brigandine", "brooch", Elements.ICE,
		&"crit_lightning", 1.1, "Critical hits chain 110% of their damage as lightning to 3 enemies."],
	["final_twilight", "Final Twilight", &"ranger", "sallet", "brigandine", "pendant", Elements.DARK,
		&"kill_heal", 0.09, "Kills restore 9% of maximum health."],
	["worldscar_tracker", "Worldscar Tracker", &"ranger", "wrap", "brigandine", "brooch", Elements.EARTH,
		&"crit_cdr", 0.7, "Critical hits reduce every skill cooldown by 0.7 seconds."],
	["nihil_fang", "Nihil Fang", &"shadowblade", "cobra", "harness", "brooch", Elements.DARK,
		&"crit_heal", 0.09, "Critical hits restore 9% of maximum health."],
	["last_breath", "Last Breath", &"shadowblade", "hood", "harness", "brooch", Elements.WATER,
		&"dodge_trail", 1.0, "Dodging leaves a crackling trail that Shocks enemies."],
	["mirror_death", "Mirror Death", &"shadowblade", "circlet", "harness", "brooch", Elements.LIGHT,
		&"dodge_haste", 0.5, "Dodging grants 50% more movement speed for 2 seconds."],
	["void_silhouette", "Void Silhouette", &"shadowblade", "wrap", "harness", "brooch", Elements.DARK,
		&"crit_heal", 0.08, "Critical hits restore 8% of maximum health."],
	["ending_whisper", "Ending Whisper", &"shadowblade", "cobra", "harness", "brooch", Elements.WIND,
		&"dodge_haste", 0.45, "Dodging grants 45% more movement speed for 2 seconds."],
	["hollow_eclipse", "Hollow Eclipse", &"shadowblade", "hood", "harness", "brooch", Elements.DARK,
		&"crit_lightning", 1.0, "Critical hits chain 100% of their damage as lightning to 3 enemies."],
	["severance", "Severance", &"shadowblade", "circlet", "harness", "brooch", Elements.FIRE,
		&"crit_heal", 0.1, "Critical hits restore 10% of maximum health."],
	["quietus", "Quietus", &"shadowblade", "wrap", "harness", "brooch", Elements.ICE,
		&"frozen_explode", 0.6, "Frozen enemies explode on death for 60% of their maximum health as Ice."],
	["null_reaper", "Null Reaper", &"shadowblade", "cobra", "harness", "brooch", Elements.EARTH,
		&"dodge_trail", 1.0, "Dodging leaves a crackling trail that Shocks enemies."],
	["shroud_of_last_night", "Shroud of the Last Night", &"shadowblade", "hood", "harness", "brooch", Elements.DARK,
		&"crit_cdr", 0.7, "Critical hits reduce every skill cooldown by 0.7 seconds."],
]
const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
## The weapon types each class masters (DataClasses weapon_mastery); ten Eschaton weapons of each, made for that class.
const WEAPONS := {&"knight": [&"sword", &"greatsword", &"axe", &"greataxe", &"spear", &"club", &"javelin"],
	&"mage": [&"staff", &"wand"], &"ranger": [&"bow", &"crossbow", &"javelin", &"spear", &"dagger"],
	&"shadowblade": [&"dagger", &"claw", &"knuckles", &"sword"]}
## Weapon i of a class carries this name before its noun (from collection i of the class).
const WEAPON_PREFIX := {
	&"knight": ["Doomsday", "Worldsend", "Endbringer", "Last Crown", "Ruinmarch", "Oblivion", "Final Dawn", "Starless", "Ashen", "Unmaker's"],
	&"mage": ["Unwritten", "Last Word", "Entropy", "Null", "Unmade Sky", "Silent Star", "Tome-Ender", "Mirrorless", "Final Equation", "Eclipse"],
	&"ranger": ["Endtime", "Last Arrow", "Horizon-Breaker", "Doomwind", "Extinction", "Sky's End", "Ashfall", "Requiem", "Last Twilight", "Worldscar"],
	&"shadowblade": ["Nihil", "Last Breath", "Mirror-Death", "Voidborn", "Ending", "Hollow Eclipse", "Severance", "Quietus", "Null Reaper", "Last Night"],
}
const WEAPON_NOUN := {&"sword": "Blade", &"greatsword": "Greatsword", &"axe": "Axe", &"greataxe": "Greataxe", &"spear": "Lance",
	&"club": "Mace", &"javelin": "Javelin", &"staff": "Staff", &"wand": "Wand", &"bow": "Longbow", &"crossbow": "Arbalest",
	&"dagger": "Fang", &"claw": "Talons", &"knuckles": "Knuckles"}
const APS := {&"sword": 1.45, &"greatsword": 0.95, &"spear": 1.2, &"axe": 1.25, &"greataxe": 0.9, &"club": 1.1, &"javelin": 1.15,
	&"staff": 1.0, &"wand": 1.6, &"bow": 1.1, &"crossbow": 0.82, &"dagger": 2.0, &"claw": 1.8, &"knuckles": 1.9}
const ARMOUR := ["helm", "armor", "inner", "leggings", "gloves", "boots", "accessory"]
const LORE := "The last thing its maker ever made. It was finished on the day the forge went out for good, and it remembers that day."
## Set bonuses of every collection (above Primordial's 0.20 damage / 0.12 health).
const SET_DMG := 0.26
const SET_HP := 0.16

static var _pieces_of := {}          # class -> [base id] (every Eschaton piece that class can use)

static func piece_id(collection: StringName, piece: String) -> StringName:
	return StringName("esc_%s_%s" % [collection, piece])

static func weapon_id(cls: StringName, wtype: StringName, i: int) -> StringName:
	return StringName("esc_w_%s_%s_%d" % [cls, wtype, i])

static func is_eschaton(base: ItemBaseDef) -> bool:
	return base != null and String(base.id).begins_with("esc_") and base.fixed_rarity == R

static func row(collection: StringName) -> Array:
	for r in COLLECTIONS:
		if StringName(r[0]) == collection:
			return r
	return []

static func pieces_of(r: Array) -> Array:
	return ARMOUR + (["shield"] if StringName(r[2]) == &"knight" else [])

static func _attr(cls: StringName) -> StringName:
	return &"str" if cls == &"knight" else (&"int" if cls == &"mage" else &"dex")

static func bases() -> Array:
	var out := []
	var asc := DataAscendant
	for ci in COLLECTIONS.size():
		var r: Array = COLLECTIONS[ci]
		var cls: StringName = r[2]
		var heavy := cls == &"knight"
		for piece: String in pieces_of(r):
			var category: StringName = asc.PIECE_CATEGORY[piece]
			var id := piece_id(StringName(r[0]), piece)
			var noun := _noun(r, piece)
			var b := DataItems._b(id, "%s %s" % [r[1], noun], category, "", {
				"set_id": StringName(r[0]), "class_hint": cls if category != &"accessory" else &"", "level_req": LEVEL, "drop_level": LEVEL,
				"fixed_rarity": R, "drop_weight": 0, "boss_exclusive": true, "requirements": {_attr(cls): int(LEVEL * 0.9)},
				"value": 6000, "tier": 3, "weight_class": &"heavy" if heavy else &"cloth", "fixed_powers": [&"esc_unmaking"], "lore": LORE})
			b.model = ItemBaseDef.ITEM_MODEL % b.id
			b.icon = DataItems.ICON3D % b.id
			match category:
				&"accessory":
					b.equip_slots = asc.JEWEL_SLOTS[r[5]]
					match String(r[5]):
						"ring": b.implicit = [StatModifier.inc(&"damage", 0.16)]
						"pendant": b.implicit = [StatModifier.inc(&"max_hp", 0.12)]
						_: b.implicit = [StatModifier.flat(&"res_all", 0.12)]
				_:
					b.defense = float(asc.ARMOR_BUDGET.get(category, 0.0)) * (1.0 if heavy else 0.6)
					if category == &"shield":
						b.block_chance = 0.3
						b.block_strength = 0.5
						b.class_hint = &"knight"
					elif category == &"boots":
						b.implicit = [StatModifier.inc(&"move_speed", 0.12)]
					elif category == &"helm":
						b.implicit = [StatModifier.flat(&"crit_damage", 0.3)]
					elif category == &"armor":
						b.implicit = [StatModifier.inc(&"max_hp", 0.14)]
			b.weight = DataItems.default_weight(b)
			out.append(b)
	# the weapons: ten of every type a class masters
	var k := 0
	for cls: StringName in CLASSES:
		for wt: StringName in WEAPONS[cls]:
			for i in 10:
				var id := weapon_id(cls, wt, i)
				var r: Array = _class_rows(cls)[i]
				var b := DataItems._b(id, "%s %s" % [WEAPON_PREFIX[cls][i], WEAPON_NOUN[wt]], &"weapon", "", {
					"class_hint": cls, "level_req": LEVEL, "drop_level": LEVEL, "fixed_rarity": R, "drop_weight": 0, "boss_exclusive": true,
					"requirements": {_attr(cls): int(LEVEL * 0.9)}, "value": 7000, "tier": 3, "fixed_powers": [&"esc_unmaking"], "lore": LORE})
				b.model = ItemBaseDef.ITEM_MODEL % b.id
				b.icon = DataItems.ICON3D % b.id
				b.weapon_type = wt
				# its own heft: no two weapons of a family share an attack rate and a weight (test_loot roster rule)
				b.attacks_per_second = float(APS[wt]) + 0.0037 * float(k % 37 + 1)
				var dmg := DataItems.roster_damage(wt, ITEM_LEVEL, b.attacks_per_second)
				b.damage_min = dmg.x
				b.damage_max = dmg.y
				b.element = int(r[6])
				b.element_share = 1.0 if cls == &"mage" else 0.4
				b.implicit = [StatModifier.inc(&"magic_damage", 0.4)] if cls == &"mage" else [StatModifier.flat(&"crit_chance", 0.07)]
				b.weight = DataItems.default_weight(b) + 0.061 + 0.0133 * float(k % 53)
				out.append(b)
				k += 1
	return out

## The ten collections of a class, in order (weapon i wears collection i's colours and name).
static func _class_rows(cls: StringName) -> Array:
	return COLLECTIONS.filter(func(r): return StringName(r[2]) == cls)

static func _noun(r: Array, piece: String) -> String:
	var asc := DataAscendant
	match piece:
		"helm": return asc.HELM_NOUN.get(r[3], "Helm")
		"armor": return asc.ARMOR_NOUN.get(r[4], "Armour")
		"accessory": return asc.JEWEL_NOUN.get(r[5], "Signet")
		"shield": return "Aegis"
	return String((asc.CLASS_NOUNS[r[2]] as Dictionary).get(piece, piece.capitalize()))

static func sets() -> Array:
	var out := []
	for r in COLLECTIONS:
		var s := SetDef.new()
		s.id = StringName(r[0])
		s.display_name = r[1]
		s.class_hint = r[2]
		for piece in pieces_of(r):
			s.pieces.append(piece_id(s.id, piece))
		var el: int = r[6]
		s.bonuses = {
			2: {"desc": "+%d%% damage and +%d%% maximum health." % [roundi(SET_DMG * 100.0), roundi(SET_HP * 100.0)],
				"mods": [StatModifier.inc(&"damage", SET_DMG), StatModifier.inc(&"max_hp", SET_HP)]},
			4: {"desc": String(r[9]), "flags": {StringName(r[7]): float(r[8])}},
			6: {"desc": "Unmaking answers twice as often; +%d%% %s damage and +%d%% critical damage." % [roundi(SET_DMG * 200.0),
				Elements.NAMES[el], roundi(SET_DMG * 300.0)],
				"flags": {&"esc_unmaking": 2.0},
				"mods": [StatModifier.inc(Elements.dmg_key(el), SET_DMG * 2.0), StatModifier.flat(&"crit_damage", SET_DMG * 3.0)]},
		}
		s.lore = "An Eschaton collection: %s" % LORE
		out.append(s)
	return out

## The signature power (never rolled at random). Each worn piece adds 1 to the flag, a 6-piece set 2 more.
static func powers() -> Array:
	return [DataItems._p(&"esc_unmaking", "Unmaking", "Hits may Unmake the target: a chrome rift opens and implodes, dealing every element at once to all enemies within 4.5 m and breaking their armour. Every Eschaton piece you wear makes it more frequent and stronger.",
		&"esc_unmaking", 1.0, [], &"", [], &"ascendant")]

## Every Eschaton base id `cls` can use (its collections' pieces and its weapons; jewels of any collection).
static func usable_ids(cls: StringName) -> Array:
	var fam := DataTranscendence.family_of(cls) if DataTranscendence.is_advanced(cls) else cls
	if _pieces_of.has(fam):
		return _pieces_of[fam]
	var out := []
	for r in COLLECTIONS:
		if StringName(r[2]) != fam:
			continue
		for piece in pieces_of(r):
			out.append(piece_id(StringName(r[0]), piece))
	for wt in WEAPONS.get(fam, []):
		for i in 10:
			out.append(weapon_id(fam, wt, i))
	_pieces_of[fam] = out
	return out

## One Eschaton piece for a hero of `cls` (any class when ""), favouring `categories` when given (a lot of blades
## makes a blade more likely). Item level: the hero's level or ITEM_LEVEL, whichever is higher.
static func roll(cls: StringName, rng: RandomNumberGenerator, level := ITEM_LEVEL, categories := {}) -> ItemInstance:
	var ids: Array = usable_ids(cls) if cls != &"" else []
	if ids.is_empty():
		ids = usable_ids(CLASSES[rng.randi_range(0, CLASSES.size() - 1)])
	var weights := []
	for id in ids:
		var b := DB.item_base(id)
		var cat: StringName = b.category if b else &""
		var w := 1.0
		if cat == &"weapon":
			w = 7.0 / float(maxi(1, WEAPONS.get(b.class_hint, [1]).size()))   # weapons as often as any one armour slot
		w *= 1.0 + 2.0 * float(categories.get(cat, 0))
		weights.append(w)
	var id: StringName = ids[DataAscendant._weighted(weights, rng)]
	return DB.make_item(id, R, maxi(level, ITEM_LEVEL), rng.randi())
