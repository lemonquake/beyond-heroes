class_name DataAscendant
## bh-034: the Ascendant tiers above Legendary and Aether — Cosmic, Divine, Eternal and Primordial — the rarest
## equipment in the game. They drop only from dungeon bosses of level 70 or higher (Loot.equipment_for), each tier
## from a higher level, at a few percent per kill at best.
##
## Every tier has ten collections (three knight, three mage, two ranger, two shadowblade) of nine pieces: helm,
## armour, inner garment, leggings, gauntlets, boots, a jewel, a shield and the collection's signature weapon. So
## every tier has ten pieces of every equipment type. The models and icons are built by
## tools/blender/items/ascendant_regalia.py (same collection ids); BossSetVisuals wears them on the hero's bones and
## AscendantFx gives each tier its moving light (overlay shader and particles).
##
## What makes them worth the hunt:
##   * the piece's base damage or Defense is multiplied by its tier (TIER.mult) on top of the item level scaling;
##   * six or seven top-tier enchantments, a random Legendary and Aether power, high quality;
##   * the tier's signature power on every piece (Starfall, Judgement, Echo, Eruption) — it grows with every piece of
##     that tier worn (Player._ascendant_procs);
##   * each collection is a set: 2, 4 and 6 pieces unlock damage and health, a class power and a stronger signature.

const MIN_LEVEL := 70

## Per tier (by rarity): key, title, drop gate (boss level), base chance per boss kill, base stat multiplier, signature
## power id and flag, signature name, guild rank to wear (DataGuilds), the level the pieces are authored at.
const TIER := {
	BH.Rarity.COSMIC: {"key": &"cosmic", "level": 70, "chance": 0.05, "mult": 1.25, "power": &"asc_starfall", "flag": &"asc_starfall",
		"sig": "Starfall", "item_level": 70, "dmg": 0.10, "hp": 0.06},
	BH.Rarity.DIVINE: {"key": &"divine", "level": 80, "chance": 0.025, "mult": 1.4, "power": &"asc_judgement", "flag": &"asc_judgement",
		"sig": "Judgement", "item_level": 80, "dmg": 0.13, "hp": 0.08},
	BH.Rarity.ETERNAL: {"key": &"eternal", "level": 90, "chance": 0.012, "mult": 1.6, "power": &"asc_echo", "flag": &"asc_echo",
		"sig": "Echo", "item_level": 90, "dmg": 0.16, "hp": 0.10},
	BH.Rarity.PRIMORDIAL: {"key": &"primordial", "level": 100, "chance": 0.005, "mult": 1.85, "power": &"asc_eruption", "flag": &"asc_eruption",
		"sig": "Eruption", "item_level": 100, "dmg": 0.20, "hp": 0.12},
	# bh-041: Eschaton never drops (chance 0): Lape the Ancient makes it (DataEschaton, LapeTrade)
	BH.Rarity.ESCHATON: {"key": &"eschaton", "level": 110, "chance": 0.0, "mult": 2.3, "power": &"esc_unmaking", "flag": &"esc_unmaking",
		"sig": "Unmaking", "item_level": 120, "dmg": 0.26, "hp": 0.16},     # = DataEschaton.SET_DMG / SET_HP
}
const C := BH.Rarity.COSMIC
const D := BH.Rarity.DIVINE
const E := BH.Rarity.ETERNAL
const P := BH.Rarity.PRIMORDIAL

## [id, tier, title, class, weapon type, helm style, torso, jewel, shield shape, element, 4-piece flag, magnitude, 4-piece text]
## (styles match tools/blender/items/ascendant_regalia.py COLLECTIONS, which builds the look from the same ids)
const COLLECTIONS := [
	["starfall_vanguard", C, "Starfall Vanguard", &"knight", &"sword", "great", "plate", "ring", "heater", Elements.LIGHT,
		&"block_shockwave", 1.0, "Blocking releases a shockwave of 100% weapon damage (1 s cooldown)."],
	["nebula_warlord", C, "Nebula Warlord", &"knight", &"greatsword", "great", "plate", "ring", "tower", Elements.DARK,
		&"fifth_stagger", 1.0, "Every fifth attack staggers hard and releases a radiant shockwave."],
	["orbit_sentinel", C, "Orbit Sentinel", &"knight", &"spear", "sallet", "plate", "ring", "kite", Elements.LIGHTNING,
		&"low_hp_dr", 0.25, "Take 25% less damage while below 35% health."],
	["astral_magister", C, "Astral Magister", &"mage", &"staff", "hood", "mantle", "ring", "round", Elements.LIGHT,
		&"aether_heartbeat", 1.8, "Every 10 s your next skill releases a pulse of 180% spell damage around you."],
	["voidweaver", C, "Voidweaver", &"mage", &"wand", "crown", "mantle", "pendant", "round", Elements.DARK,
		&"arcane_free", 1.0, "At maximum Arcane Charge your spells cost no Mana."],
	["eclipse_oracle", C, "Eclipse Oracle", &"mage", &"staff", "mitre", "mantle", "pendant", "kite", Elements.LIGHTNING,
		&"wet_chains", 4.0, "Chain Lightning chains 4 more times against Wet targets."],
	["comet_strider", C, "Comet Strider", &"ranger", &"bow", "sallet", "brigandine", "pendant", "round", Elements.LIGHTNING,
		&"crit_lightning", 0.7, "Critical hits chain 70% of their damage as lightning to 3 enemies."],
	["meteor_marksman", C, "Meteor Marksman", &"ranger", &"crossbow", "wrap", "brigandine", "brooch", "round", Elements.FIRE,
		&"hit_ignite", 0.25, "Hits have a 25% chance to ignite."],
	["nightsky_reaver", C, "Nightsky Reaver", &"shadowblade", &"dagger", "hood", "harness", "brooch", "round", Elements.DARK,
		&"crit_heal", 0.04, "Critical hits restore 4% of maximum health."],
	["starless_stalker", C, "Starless Stalker", &"shadowblade", &"claw", "cobra", "harness", "brooch", "round", Elements.DARK,
		&"dodge_trail", 1.0, "Dodging leaves a crackling trail that Shocks enemies."],
	["seraph_paladin", D, "Seraph Paladin", &"knight", &"sword", "great", "plate", "ring", "heater", Elements.LIGHT,
		&"valor_hold", 40.0, "Valor never decays and you start every fight with 40 Valor."],
	["archon_crusader", D, "Archon Crusader", &"knight", &"greataxe", "great", "plate", "ring", "tower", Elements.LIGHT,
		&"cleave_wave", 1.2, "Cleave releases a travelling wave of 120% of its damage as Light."],
	["dawnward_templar", D, "Dawnward Templar", &"knight", &"club", "sallet", "plate", "ring", "kite", Elements.FIRE,
		&"kill_heal", 0.06, "Kills restore 6% of maximum health."],
	["hierophant", D, "Hierophant", &"mage", &"staff", "mitre", "mantle", "ring", "round", Elements.LIGHT,
		&"mana_on_spell_hit", 3.0, "Spell hits restore 3 Mana."],
	["lightbinder", D, "Lightbinder", &"mage", &"wand", "crown", "mantle", "pendant", "round", Elements.LIGHT,
		&"firebolt_split", 1.0, "Firebolt always splits into three projectiles."],
	["cantor_of_dawn", D, "Cantor of Dawn", &"mage", &"staff", "hood", "mantle", "pendant", "kite", Elements.FIRE,
		&"burn_spread", 1.0, "Burning spreads to a nearby enemy every second."],
	["zenith_archer", D, "Zenith Archer", &"ranger", &"bow", "circlet", "brigandine", "pendant", "round", Elements.LIGHT,
		&"crit_sunflare", 0.6, "Critical hits flare 60% of their damage as Light onto enemies within 5 m."],
	["verdict_arbalist", D, "Verdict Arbalist", &"ranger", &"crossbow", "sallet", "brigandine", "brooch", "round", Elements.LIGHTNING,
		&"crit_cdr", 0.5, "Critical hits reduce every skill cooldown by 0.5 seconds."],
	["sanctified_shade", D, "Sanctified Shade", &"shadowblade", &"dagger", "hood", "harness", "brooch", "round", Elements.LIGHT,
		&"crit_heal", 0.05, "Critical hits restore 5% of maximum health."],
	["penitent_talon", D, "Penitent Talon", &"shadowblade", &"claw", "circlet", "harness", "brooch", "round", Elements.FIRE,
		&"dodge_haste", 0.3, "Dodging grants 30% more movement speed for 2 seconds."],
	["chronoguard", E, "Chronoguard", &"knight", &"greatsword", "great", "plate", "ring", "tower", Elements.WATER,
		&"crit_cdr", 0.6, "Critical hits reduce every skill cooldown by 0.6 seconds."],
	["everlasting_bulwark", E, "Everlasting Bulwark", &"knight", &"sword", "great", "plate", "ring", "heater", Elements.ICE,
		&"block_shockwave", 1.4, "Blocking releases a shockwave of 140% weapon damage (1 s cooldown)."],
	["aeonbreaker", E, "Aeonbreaker", &"knight", &"axe", "sallet", "plate", "ring", "kite", Elements.WIND,
		&"low_hp_dr", 0.3, "Take 30% less damage while below 35% health."],
	["timeweaver", E, "Timeweaver", &"mage", &"staff", "crown", "mantle", "ring", "round", Elements.WATER,
		&"still_mana", 3.0, "Standing still for 1 s quadruples Mana regeneration."],
	["hourglass_sage", E, "Hourglass Sage", &"mage", &"wand", "hood", "mantle", "pendant", "round", Elements.ICE,
		&"frozen_explode", 0.5, "Frozen enemies explode on death for 50% of their maximum health as Ice."],
	["undying_seer", E, "Undying Seer", &"mage", &"staff", "mitre", "mantle", "pendant", "kite", Elements.DARK,
		&"aether_heartbeat", 2.4, "Every 10 s your next skill releases a pulse of 240% spell damage around you."],
	["evertide_hunter", E, "Evertide Hunter", &"ranger", &"bow", "circlet", "brigandine", "pendant", "round", Elements.WATER,
		&"kill_heal", 0.06, "Kills restore 6% of maximum health."],
	["endless_volley", E, "Endless Volley", &"ranger", &"crossbow", "wrap", "brigandine", "brooch", "round", Elements.WIND,
		&"crit_lightning", 0.9, "Critical hits chain 90% of their damage as lightning to 3 enemies."],
	["stillhour_assassin", E, "Stillhour Assassin", &"shadowblade", &"dagger", "hood", "harness", "brooch", "round", Elements.ICE,
		&"frozen_explode", 0.5, "Frozen enemies explode on death for 50% of their maximum health as Ice."],
	["ouroboros_fang", E, "Ouroboros Fang", &"shadowblade", &"claw", "cobra", "harness", "brooch", "round", Elements.WATER,
		&"crit_heal", 0.06, "Critical hits restore 6% of maximum health."],
	["worldforger", P, "Worldforger", &"knight", &"greatsword", "great", "plate", "ring", "tower", Elements.FIRE,
		&"fifth_stagger", 1.0, "Every fifth attack staggers hard and releases a radiant shockwave."],
	["titanblood_champion", P, "Titanblood Champion", &"knight", &"sword", "great", "plate", "ring", "heater", Elements.FIRE,
		&"kill_heal", 0.08, "Kills restore 8% of maximum health."],
	["firstflame_warlord", P, "Firstflame Warlord", &"knight", &"greataxe", "sallet", "plate", "ring", "kite", Elements.EARTH,
		&"cleave_wave", 1.6, "Cleave releases a travelling wave of 160% of its damage as Light."],
	["ashborn_archmage", P, "Ashborn Archmage", &"mage", &"staff", "mitre", "mantle", "ring", "round", Elements.FIRE,
		&"burn_spread", 1.0, "Burning spreads to a nearby enemy every second."],
	["primeval_shaman", P, "Primeval Shaman", &"mage", &"wand", "hood", "mantle", "pendant", "round", Elements.EARTH,
		&"aether_heartbeat", 3.0, "Every 10 s your next skill releases a pulse of 300% spell damage around you."],
	["magma_oracle", P, "Magma Oracle", &"mage", &"staff", "crown", "mantle", "pendant", "kite", Elements.FIRE,
		&"arcane_free", 1.0, "At maximum Arcane Charge your spells cost no Mana."],
	["wildroot_hunter", P, "Wildroot Hunter", &"ranger", &"bow", "circlet", "brigandine", "pendant", "round", Elements.EARTH,
		&"hit_ignite", 0.35, "Hits have a 35% chance to ignite."],
	["cinderbolt_ballista", P, "Cinderbolt Ballista", &"ranger", &"crossbow", "sallet", "brigandine", "brooch", "round", Elements.FIRE,
		&"crit_sunflare", 0.9, "Critical hits flare 90% of their damage as Light onto enemies within 5 m."],
	["abyssal_fang", P, "Abyssal Fang", &"shadowblade", &"dagger", "cobra", "harness", "brooch", "round", Elements.DARK,
		&"crit_heal", 0.07, "Critical hits restore 7% of maximum health."],
	["elder_wyrm_talon", P, "Elder Wyrm Talon", &"shadowblade", &"claw", "hood", "harness", "brooch", "round", Elements.FIRE,
		&"dodge_trail", 1.0, "Dodging leaves a crackling trail that Shocks enemies."],
]
const PIECES := ["helm", "armor", "inner", "leggings", "gloves", "boots", "accessory", "shield", "weapon"]
const PIECE_CATEGORY := {"helm": &"helm", "armor": &"armor", "inner": &"inner_garment", "leggings": &"leggings", "gloves": &"gloves",
	"boots": &"boots", "accessory": &"accessory", "shield": &"shield", "weapon": &"weapon"}
const JEWEL_SLOTS := {"ring": [&"accessory_1", &"accessory_2"], "pendant": [&"accessory_3"], "brooch": [&"accessory_4"]}
const HELM_NOUN := {"great": "Greathelm", "sallet": "Visor", "hood": "Cowl", "mitre": "Mitre", "crown": "Diadem", "circlet": "Circlet",
	"wrap": "Veil", "cobra": "Hood"}
const ARMOR_NOUN := {"plate": "Cuirass", "brigandine": "Brigandine", "mantle": "Vestments", "harness": "Harness"}
const CLASS_NOUNS := {
	&"knight": {"inner": "Surcoat", "leggings": "Legplates", "gloves": "Gauntlets", "boots": "Sabatons"},
	&"mage": {"inner": "Robe", "leggings": "Leggings", "gloves": "Gloves", "boots": "Boots"},
	&"ranger": {"inner": "Jerkin", "leggings": "Chausses", "gloves": "Bracers", "boots": "Treads"},
	&"shadowblade": {"inner": "Undercoat", "leggings": "Legwraps", "gloves": "Grips", "boots": "Striders"},
}
const JEWEL_NOUN := {"ring": "Signet", "pendant": "Pendant", "brooch": "Brooch"}
const SHIELD_NOUN := {"heater": "Aegis", "tower": "Bulwark", "kite": "Ward", "round": "Buckler"}
const WEAPON_NOUN := {&"sword": "Blade", &"greatsword": "Greatsword", &"spear": "Lance", &"axe": "Axe", &"greataxe": "Greataxe",
	&"club": "Mace", &"staff": "Staff", &"wand": "Wand", &"bow": "Longbow", &"crossbow": "Arbalest", &"dagger": "Fang", &"claw": "Talons"}
const APS := {&"sword": 1.45, &"greatsword": 0.95, &"spear": 1.2, &"axe": 1.25, &"greataxe": 0.9, &"club": 1.1, &"staff": 1.0,
	&"wand": 1.6, &"bow": 1.1, &"crossbow": 0.82, &"dagger": 2.0, &"claw": 1.8}
const ARMOR_BUDGET := {&"armor": 74.0, &"helm": 37.0, &"inner_garment": 24.0, &"leggings": 31.0, &"gloves": 18.0, &"boots": 22.0, &"shield": 52.0}
const LORE := {
	&"cosmic": "Forged where the night sky touches the world's edge. Starlight still moves in it.",
	&"divine": "Blessed in a temple that no map remembers. It hums like a held note.",
	&"eternal": "Its maker stopped every clock in the forge. Time passes around it, never through it.",
	&"primordial": "Older than the first kings and the first fires. The world was still soft when this was made.",
	&"eschaton": "The last thing its maker ever made. It was finished on the day the forge went out for good, and it remembers that day.",
}

static func row(collection: StringName) -> Array:
	for r in COLLECTIONS:
		if StringName(r[0]) == collection:
			return r
	return []

static func piece_id(collection: StringName, piece: String) -> StringName:
	return StringName("asc_%s_%s" % [collection, piece])

static func is_ascendant_rarity(rarity: int) -> bool:
	return rarity >= BH.Rarity.COSMIC

static func is_ascendant(base: ItemBaseDef) -> bool:
	return base != null and (String(base.id).begins_with("asc_") or DataEschaton.is_eschaton(base)) and base.fixed_rarity >= BH.Rarity.COSMIC

## The tier key (&"cosmic" ...) of a rarity, &"" below Cosmic.
static func tier_key(rarity: int) -> StringName:
	return StringName(TIER[rarity].key) if TIER.has(rarity) else &""

## Base damage / Defense multiplier of a piece of `rarity` (1 below Cosmic).
static func mult(rarity: int) -> float:
	return float(TIER[rarity].mult) if TIER.has(rarity) else 1.0

## The collection id of an Ascendant base (its set id).
static func collection_of(base: ItemBaseDef) -> StringName:
	return base.set_id if is_ascendant(base) else &""

static func _noun(r: Array, piece: String) -> String:
	match piece:
		"helm": return HELM_NOUN.get(r[5], "Helm")
		"armor": return ARMOR_NOUN.get(r[6], "Armour")
		"accessory": return JEWEL_NOUN.get(r[7], "Signet")
		"shield": return SHIELD_NOUN.get(r[8], "Shield")
		"weapon": return WEAPON_NOUN.get(r[4], "Weapon")
	return String((CLASS_NOUNS[r[3]] as Dictionary).get(piece, piece.capitalize()))

static func bases() -> Array:
	var out := []
	for r in COLLECTIONS:
		var rarity: int = r[1]
		var info: Dictionary = TIER[rarity]
		var lvl: int = int(info.item_level)
		var cls: StringName = r[3]
		var attr: StringName = &"str" if cls == &"knight" else (&"int" if cls == &"mage" else &"dex")
		var heavy := cls == &"knight"
		for piece: String in PIECES:
			var category: StringName = PIECE_CATEGORY[piece]
			var id := piece_id(StringName(r[0]), piece)
			var b := DataItems._b(id, "%s %s" % [r[2], _noun(r, piece)], category, "", {
				"set_id": StringName(r[0]), "class_hint": cls if category != &"accessory" else &"", "level_req": lvl, "drop_level": lvl,
				"fixed_rarity": rarity, "drop_weight": 0, "boss_exclusive": true, "requirements": {attr: int(lvl * 0.9)},
				"value": 1500 + 900 * (rarity - BH.Rarity.COSMIC), "tier": 3, "weight_class": &"heavy" if heavy else &"cloth",
				"fixed_powers": [info.power], "lore": LORE[info.key]})
			b.model = ItemBaseDef.ITEM_MODEL % b.id
			b.icon = DataItems.ICON3D % b.id
			var step := float(rarity - BH.Rarity.COSMIC)
			match category:
				&"weapon":
					b.weapon_type = r[4]
					b.attacks_per_second = float(APS.get(r[4], 1.2))
					var dmg := DataItems.roster_damage(r[4], lvl, b.attacks_per_second)
					b.damage_min = dmg.x
					b.damage_max = dmg.y
					b.element = int(r[9])
					b.element_share = 1.0 if cls == &"mage" else 0.35
					b.implicit = [StatModifier.inc(&"magic_damage", 0.22 + 0.04 * step)] if cls == &"mage" else [StatModifier.flat(&"crit_chance", 0.03 + 0.01 * step)]
				&"accessory":
					b.equip_slots = JEWEL_SLOTS[r[7]]
					match String(r[7]):
						"ring": b.implicit = [StatModifier.inc(&"damage", 0.06 + 0.02 * step)]
						"pendant": b.implicit = [StatModifier.inc(&"max_hp", 0.05 + 0.015 * step)]
						_: b.implicit = [StatModifier.flat(&"res_all", 0.05 + 0.015 * step)]
				_:
					b.defense = float(ARMOR_BUDGET.get(category, 0.0)) * (1.0 if heavy else 0.6)
					if category == &"shield":
						b.block_chance = 0.2 + 0.02 * step
						b.block_strength = 0.36 + 0.03 * step
						b.class_hint = &"knight"
					elif category == &"boots":
						b.implicit = [StatModifier.inc(&"move_speed", 0.06 + 0.01 * step)]
					elif category == &"helm":
						b.implicit = [StatModifier.flat(&"crit_damage", 0.10 + 0.04 * step)]
					elif category == &"armor":
						b.implicit = [StatModifier.inc(&"max_hp", 0.06 + 0.02 * step)]
			b.weight = DataItems.default_weight(b)
			if category == &"weapon":
				# its own heft: no two weapons of a family share an attack rate and a weight (test_loot roster rule)
				b.weight += 0.07 + COLLECTIONS.find(r) * 0.03
				b.attacks_per_second += 0.01 * float(COLLECTIONS.find(r) % 4)
			out.append(b)
	return out

static func sets() -> Array:
	var out := []
	for r in COLLECTIONS:
		var info: Dictionary = TIER[int(r[1])]
		var s := SetDef.new()
		s.id = StringName(r[0])
		s.display_name = r[2]
		s.class_hint = r[3]
		for piece in PIECES:
			s.pieces.append(piece_id(s.id, piece))
		var el: int = r[9]
		var d: float = info.dmg
		var h: float = info.hp
		s.bonuses = {
			2: {"desc": "+%d%% damage and +%d%% maximum health." % [roundi(d * 100.0), roundi(h * 100.0)],
				"mods": [StatModifier.inc(&"damage", d), StatModifier.inc(&"max_hp", h)]},
			4: {"desc": String(r[12]), "flags": {StringName(r[10]): float(r[11])}},
			6: {"desc": "%s answers twice as often; +%d%% %s damage and +%d%% critical damage." % [info.sig, roundi(d * 200.0),
				Elements.NAMES[el], roundi(d * 300.0)],
				"flags": {StringName(info.flag): 2.0},
				"mods": [StatModifier.inc(Elements.dmg_key(el), d * 2.0), StatModifier.flat(&"crit_damage", d * 3.0)]},
		}
		s.lore = "A %s collection: %s" % [BH.rarity_name(int(r[1])), LORE[info.key]]
		out.append(s)
	return out

## The four signature powers (tier "ascendant": never rolled at random; every piece carries its tier's). Each worn
## piece adds 1 to the flag, a 6-piece set 2 more; Player._ascendant_procs turns the count into chance and strength.
static func powers() -> Array:
	return [
		DataItems._p(&"asc_starfall", "Starfall", "Hits may call down a falling star on the target: Light damage to every enemy within 3 m. Every Cosmic piece you wear makes it more frequent and stronger.",
			&"asc_starfall", 1.0, [], &"", [], &"ascendant"),
		DataItems._p(&"asc_judgement", "Judgement", "Hits may bring down a pillar of holy light: Light damage around the target and a heal of your maximum health. Every Divine piece you wear makes it more frequent and stronger.",
			&"asc_judgement", 1.0, [], &"", [], &"ascendant"),
		DataItems._p(&"asc_echo", "Echo", "Hits may echo through time: the blow lands again and your skills cool down faster. Every Eternal piece you wear makes it more frequent and stronger.",
			&"asc_echo", 1.0, [], &"", [], &"ascendant"),
		DataItems._p(&"asc_eruption", "Eruption", "Hits may split the ground: Fire and Earth erupt around the target and set it burning. Every Primordial piece you wear makes it more frequent and stronger.",
			&"asc_eruption", 1.0, [], &"", [], &"ascendant"),
	]

## Chance and strength of a signature proc from the summed flag `n` (pieces worn, +2 for a full set).
static func proc_chance(flag: StringName, n: float) -> float:
	if n <= 0.0:
		return 0.0
	match flag:
		&"asc_starfall": return minf(0.04 + 0.04 * n, 0.4)
		&"asc_judgement": return minf(0.04 + 0.04 * n, 0.4)
		&"asc_echo": return minf(0.05 + 0.05 * n, 0.45)
		&"asc_eruption": return minf(0.03 + 0.035 * n, 0.35)
		&"esc_unmaking": return minf(0.05 + 0.035 * n, 0.45)
	return 0.0

static func proc_power(flag: StringName, n: float) -> float:
	match flag:
		&"asc_starfall": return minf(0.8 + 0.1 * n, 1.8)
		&"asc_judgement": return minf(0.7 + 0.08 * n, 1.5)
		&"asc_echo": return minf(0.5 + 0.06 * n, 1.1)
		&"asc_eruption": return minf(1.0 + 0.12 * n, 2.2)
		&"esc_unmaking": return minf(1.4 + 0.15 * n, 3.2)
	return 0.0

# ---- drops ----------------------------------------------------------------------------------------------------------

## A dungeon boss of level 70+ may leave one Ascendant piece (null otherwise). Tiers are tried from the top; magic
## find raises the odds a little (at most x1.5). The collection favours the hero's class three to one, and the piece is
## usable gear for that class where possible (a shield only for knights).
static func roll_drop(level: int, is_dungeon_boss: bool, class_id: StringName, magic_find: float, rng: RandomNumberGenerator,
		force_rarity := -1) -> ItemInstance:
	if not is_dungeon_boss and force_rarity < 0:
		return null
	if force_rarity == BH.Rarity.ESCHATON:
		return DataEschaton.roll(class_id, rng, maxi(level + 2, DataEschaton.ITEM_LEVEL))
	var rarity := force_rarity
	if rarity < 0:
		if level < MIN_LEVEL:
			return null
		var boost := 1.0 + clampf(magic_find, 0.0, 2.0) * 0.25
		for r in [P, E, D, C]:
			if level >= int(TIER[r].level) and rng.randf() < float(TIER[r].chance) * boost:
				rarity = r
				break
		if rarity < 0:
			return null
	var pool := []
	var weights := []
	for row_ in COLLECTIONS:
		if int(row_[1]) != rarity:
			continue
		pool.append(row_)
		weights.append(3.0 if StringName(row_[3]) == class_id else 1.0)
	if pool.is_empty():
		return null
	var picked: Array = pool[_weighted(weights, rng)]
	var pieces := PIECES.duplicate()
	if class_id != &"knight":
		pieces.erase("shield")
	if class_id != &"" and StringName(picked[3]) != class_id:
		pieces.erase("weapon")          # another class's weapon is no reward
	var piece: String = pieces[rng.randi_range(0, pieces.size() - 1)]
	# bh-039: half the time a weapon is one of the tier's Fabled arms instead (one the hero's class uses, if any)
	if piece == "weapon" and rng.randf() < 0.5:
		var arms := DataFabled.ids_of(rarity).filter(func(id): return class_id == &"" or ItemGenerator.class_fit(DB.item_base(id), class_id))
		if not arms.is_empty():
			return DB.make_item(arms[rng.randi_range(0, arms.size() - 1)], rarity, maxi(level + 2, int(TIER[rarity].item_level)), rng.randi())
	return DB.make_item(piece_id(StringName(picked[0]), piece), rarity, maxi(level + 2, int(TIER[rarity].item_level)), rng.randi())

static func _weighted(weights: Array, rng: RandomNumberGenerator) -> int:
	var total := 0.0
	for w in weights:
		total += float(w)
	var cur := rng.randf() * total
	for i in weights.size():
		cur -= float(weights[i])
		if cur < 0.0:
			return i
	return weights.size() - 1
