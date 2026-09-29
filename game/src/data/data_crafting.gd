class_name DataCrafting
## Crafting (bh-007): ingredients (monster parts, herbs, refined stock, champion essence), recipe scrolls, the recipes
## themselves and what salvaging gear gives back. The rules live in Crafting (src/core/crafting/crafting.gd).
##
## Stations: forge (Brannoc's anvil in Malasugue, the field forge at Wyman Outpost), alchemy (Olivar's alchemist, the
## camp kettle at Wyman Outpost) and workbench (Wyman Outpost). A recipe lists every station that can make it.
##
## Recipe keys:
##   id, name, stations, group (list heading), level (hero level needed), gold (fee), inputs [[base id, count], ...],
##   out: {"base": id, "count": n}  or  {"gear": {"rarity": r, "quality": [min, max], "ilvl_bonus": n}}
##   variants: gear recipes only — [{"label", "categories", "weapon_types"?}] the hero picks one when crafting
##   known: true when every hero starts with it; otherwise it is learned from a recipe scroll (`scroll` lists where)
##   text: one line shown under the recipe

const R := BH.Rarity
const ICON3D := "res://assets/ui/icons/items3d/%s.png"

const STATIONS := {
	&"forge": {"name": "Forge", "verb": "Forge", "text": "Metalwork: ingots, whetstones, weapons and armor. Salvage gear for its metal. Refit a weapon: Fore-Tech."},
	&"alchemy": {"name": "Alchemy Table", "verb": "Brew", "text": "Draughts, tonics, wards and elixirs from herbs and monster parts. Etch a rune on a weapon: Enchantment."},
	&"workbench": {"name": "Workbench", "verb": "Make", "text": "Leather, bombs, scrolls and charms. Salvage gear for hide and cloth."},
}

## [id, name, value, stack, drop weight, flavor]. Monster parts drop from their family (DataEnemies loot tables), herbs
## are gathered in the world (GatherNode), refined stock is crafted, champion essence comes from minibosses.
const MATERIALS := [
	# monster parts
	[&"wolf_fang", "Wolf Fang", 4, 99, "A curved fang from a dire wolf. Alchemists grind it into swiftness tonics; smiths set it in blades."],
	[&"goblin_resin", "Fire-pot Resin", 3, 99, "Sticky black pitch scraped out of a goblin fire-pot. It burns hot and long."],
	[&"orc_tusk", "Orc Tusk", 7, 99, "Heavy yellow ivory. Ground into Ironskin Brew, or bound into armor."],
	[&"ogre_sinew", "Ogre Sinew", 12, 50, "A cord of muscle as thick as a rope and twice as strong."],
	[&"grave_dust", "Grave Dust", 3, 99, "What the restless dead leave behind. Useful in salts and smoke."],
	[&"ghoul_bile", "Ghoul Bile", 6, 50, "Foul and caustic. Alchemists wear gloves."],
	[&"ash_sigil", "Ash Sigil", 8, 50, "A cultist's scorched cloth badge. The stitching still holds a little heat."],
	[&"wisp_mote", "Wisp Mote", 9, 50, "A drifting speck of Aether left when a wisp burns out."],
	[&"stolen_linen", "Bolt of Linen", 4, 99, "Good cloth from the cove's missing shipment. Nobody is asking for it back."],
	[&"rune_plate", "Rune Plate", 14, 50, "A carved plate from an Aether Sentinel's shell. The runes still glow faintly."],
	# herbs (gathered)
	[&"silverleaf", "Silverleaf", 2, 99, "A pale healing herb that grows beside roads and field walls."],
	[&"mirebloom", "Mirebloom", 3, 99, "A blue marsh flower. Brewed, it restores Mana."],
	[&"emberroot", "Emberroot", 5, 99, "A red root that stays warm in the hand. The base of every fire ward."],
	[&"brightcap", "Brightcap", 4, 99, "A mushroom that glows in deep shade. Sharpens the mind."],
	# refined stock (crafted)
	[&"steel_ingot", "Steel Ingot", 18, 50, "Forged from salvaged iron. Every weapon and armor recipe starts here."],
	[&"cured_leather", "Cured Leather", 10, 50, "Beast hide scraped, cured and oiled."],
	# minibosses
	[&"champion_essence", "Champion Essence", 60, 50, "The distilled will of a champion monster. Needed for Elite and Master work."],
]

## Recipe scrolls: consumables that teach a recipe once (value, source note).
const SCROLLS := [
	[&"recipe_berserker", &"berserker_draught", 90, "Olivar's alchemist, minibosses"],
	[&"recipe_sage", &"sages_infusion", 90, "Olivar's alchemist, minibosses"],
	[&"recipe_fortune", &"fortune_elixir", 220, "Olivar's alchemist, minibosses"],
	[&"recipe_phoenix", &"phoenix_feather", 420, "Olivar's alchemist"],
	[&"recipe_champion_weapon", &"champion_weapon", 260, "Olivar's arms exchange, minibosses"],
	[&"recipe_champion_armor", &"champion_armor", 240, "Olivar's arms exchange, minibosses"],
	[&"recipe_champion_trinket", &"champion_trinket", 240, "Olivar's jeweller, minibosses"],
	[&"recipe_aetherforged", &"aetherforged_weapon", 900, "Olivar's arms exchange (rare)"],
]

static func materials(out: Array) -> void:
	for m in MATERIALS:
		var b := ItemBaseDef.new()
		b.id = m[0]
		b.display_name = m[1]
		b.category = &"material"
		b.icon = ICON3D % m[0]
		b.value = m[2]
		b.stack_max = m[3]
		b.flavor = m[4]
		b.weight = 0.1
		b.drop_weight = 0
		out.append(b)
	for s in SCROLLS:
		var r := recipe(s[1])
		var b := ItemBaseDef.new()
		b.id = s[0]
		b.display_name = "Recipe: %s" % r.get("name", s[1])
		b.category = &"consumable"
		b.icon = ICON3D % s[0]
		b.value = s[2]
		b.stack_max = 5
		b.weight = 0.1
		b.drop_weight = 0
		b.level_req = int(r.get("level", 1))
		b.consumable_effect = {"learn_recipe": String(s[1])}
		b.flavor = "Use to learn the recipe for %s (%s). Found at: %s." % [r.get("name", s[1]), station_names(r.get("stations", [])), s[3]]
		out.append(b)

static func station_names(ids: Array) -> String:
	var names := []
	for s in ids:
		names.append(STATIONS.get(StringName(s), {}).get("name", String(s)))
	return " or ".join(names)

## Every weapon type a crafter can choose (the window shows only those the hero's class can wield first).
const WEAPON_VARIANTS := [
	["Sword", &"sword"], ["Greatsword", &"greatsword"], ["Axe", &"axe"], ["Great Axe", &"greataxe"], ["Spear", &"spear"],
	["Javelin", &"javelin"], ["Club", &"club"], ["Dagger", &"dagger"], ["Claw", &"claw"], ["Knuckles", &"knuckles"],
	["Bow", &"bow"], ["Crossbow", &"crossbow"], ["Staff", &"staff"], ["Wand", &"wand"],
]
const ARMOR_VARIANTS := [
	["Helm", [&"helm"]], ["Body Armor", [&"armor"]], ["Inner Garment", [&"inner_garment"]], ["Gloves", [&"gloves"]],
	["Boots", [&"boots"]], ["Shield", [&"shield"]],
]

static func _weapon_variants() -> Array:
	return WEAPON_VARIANTS.map(func(v): return {"label": v[0], "categories": [&"weapon"], "weapon_types": [v[1]]})

static func _armor_variants() -> Array:
	return ARMOR_VARIANTS.map(func(v): return {"label": v[0], "categories": v[1]})

static func recipes() -> Array:
	var A := [&"alchemy"]
	var AW := [&"alchemy", &"workbench"]
	var W := [&"workbench"]
	var F := [&"forge"]
	return [
		# ---- draughts (alchemy; the basics also on the camp workbench) ----
		{"id": &"health_potion", "name": "Health Draught", "stations": AW, "group": "Draughts", "level": 1, "gold": 2, "known": true,
			"inputs": [[&"silverleaf", 2]], "out": {"base": &"health_potion", "count": 2}},
		{"id": &"mana_potion", "name": "Mana Draught", "stations": AW, "group": "Draughts", "level": 1, "gold": 2, "known": true,
			"inputs": [[&"mirebloom", 2]], "out": {"base": &"mana_potion", "count": 2}},
		{"id": &"antidote", "name": "Purifying Salts", "stations": AW, "group": "Draughts", "level": 1, "gold": 3, "known": true,
			"inputs": [[&"silverleaf", 1], [&"grave_dust", 2]], "out": {"base": &"antidote", "count": 2}},
		{"id": &"greater_health_potion", "name": "Greater Health Draught", "stations": A, "group": "Draughts", "level": 6, "gold": 8, "known": true,
			"inputs": [[&"silverleaf", 3], [&"wolf_fang", 1]], "out": {"base": &"greater_health_potion", "count": 1}},
		{"id": &"greater_mana_potion", "name": "Greater Mana Draught", "stations": A, "group": "Draughts", "level": 6, "gold": 8, "known": true,
			"inputs": [[&"mirebloom", 3], [&"wisp_mote", 1]], "out": {"base": &"greater_mana_potion", "count": 1}},
		{"id": &"rejuvenation_elixir", "name": "Rejuvenation Elixir", "stations": A, "group": "Draughts", "level": 5, "gold": 10, "known": true,
			"inputs": [[&"silverleaf", 2], [&"mirebloom", 2], [&"brightcap", 1]], "out": {"base": &"rejuvenation_elixir", "count": 1}},
		# ---- tonics and wards ----
		{"id": &"scholars_tea", "name": "Scholar's Tea", "stations": A, "group": "Tonics and Wards", "level": 3, "gold": 6, "known": true,
			"inputs": [[&"brightcap", 2], [&"silverleaf", 1]], "out": {"base": &"scholars_tea", "count": 1}},
		{"id": &"swiftfoot_tonic", "name": "Swiftfoot Tonic", "stations": A, "group": "Tonics and Wards", "level": 4, "gold": 6, "known": true,
			"inputs": [[&"wolf_fang", 2], [&"mirebloom", 1]], "out": {"base": &"swiftfoot_tonic", "count": 1}},
		{"id": &"ironskin_brew", "name": "Ironskin Brew", "stations": A, "group": "Tonics and Wards", "level": 5, "gold": 8, "known": true,
			"inputs": [[&"orc_tusk", 1], [&"silverleaf", 2]], "out": {"base": &"ironskin_brew", "count": 1}},
		{"id": &"emberward_potion", "name": "Emberward Potion", "stations": A, "group": "Tonics and Wards", "level": 6, "gold": 8, "known": true,
			"inputs": [[&"emberroot", 2], [&"ash_sigil", 1]], "out": {"base": &"emberward_potion", "count": 1}},
		{"id": &"frostward_potion", "name": "Frostward Potion", "stations": A, "group": "Tonics and Wards", "level": 6, "gold": 8, "known": true,
			"inputs": [[&"emberroot", 1], [&"frost_crystal", 1], [&"silverleaf", 1]], "out": {"base": &"frostward_potion", "count": 1}},
		{"id": &"stormward_potion", "name": "Stormward Potion", "stations": A, "group": "Tonics and Wards", "level": 6, "gold": 8, "known": true,
			"inputs": [[&"storm_essence", 1], [&"brightcap", 2]], "out": {"base": &"stormward_potion", "count": 1}},
		{"id": &"berserker_draught", "name": "Berserker's Draught", "stations": A, "group": "Tonics and Wards", "level": 8, "gold": 14,
			"inputs": [[&"ogre_sinew", 1], [&"emberroot", 2], [&"ghoul_bile", 1]], "out": {"base": &"berserker_draught", "count": 1}},
		{"id": &"sages_infusion", "name": "Sage's Infusion", "stations": A, "group": "Tonics and Wards", "level": 8, "gold": 14,
			"inputs": [[&"wisp_mote", 2], [&"mirebloom", 2], [&"brightcap", 1]], "out": {"base": &"sages_infusion", "count": 1}},
		{"id": &"fortune_elixir", "name": "Elixir of Fortune", "stations": A, "group": "Tonics and Wards", "level": 10, "gold": 40,
			"inputs": [[&"champion_essence", 1], [&"brightcap", 3], [&"arcane_dust", 2]], "out": {"base": &"fortune_elixir", "count": 1}},
		# ---- bh-017: elixirs of the five new buffs ----
		{"id": &"vigor_draught", "name": "Draught of Vigor", "stations": A, "group": "Tonics and Wards", "level": 6, "gold": 10, "known": true,
			"inputs": [[&"silverleaf", 3], [&"beast_hide", 1], [&"brightcap", 1]], "out": {"base": &"vigor_draught", "count": 1}},
		{"id": &"keen_tonic", "name": "Keen-Eye Tonic", "stations": A, "group": "Tonics and Wards", "level": 7, "gold": 12, "known": true,
			"inputs": [[&"wolf_fang", 2], [&"brightcap", 2], [&"arcane_dust", 1]], "out": {"base": &"keen_tonic", "count": 1}},
		{"id": &"windstep_tonic", "name": "Windstep Tonic", "stations": A, "group": "Tonics and Wards", "level": 6, "gold": 10, "known": true,
			"inputs": [[&"wisp_mote", 2], [&"mirebloom", 1], [&"wolf_fang", 1]], "out": {"base": &"windstep_tonic", "count": 1}},
		{"id": &"titan_brew", "name": "Titan's Brew", "stations": A, "group": "Tonics and Wards", "level": 10, "gold": 24, "known": true,
			"inputs": [[&"ogre_sinew", 2], [&"orc_tusk", 2], [&"emberroot", 2]], "out": {"base": &"titan_brew", "count": 1}},
		{"id": &"spirit_ward_draught", "name": "Spirit Ward Draught", "stations": A, "group": "Tonics and Wards", "level": 8, "gold": 16, "known": true,
			"inputs": [[&"ash_sigil", 1], [&"storm_essence", 1], [&"silverleaf", 2]], "out": {"base": &"spirit_ward_draught", "count": 1}},
		{"id": &"phoenix_feather", "name": "Phoenix Feather", "stations": A, "group": "Tonics and Wards", "level": 12, "gold": 120,
			"inputs": [[&"champion_essence", 2], [&"ember_core", 3], [&"emberroot", 4]], "out": {"base": &"phoenix_feather", "count": 1},
			"text": "Burns by itself when a killing blow lands and you rise with half your HP."},
		# ---- bombs, scrolls and leather (workbench) ----
		{"id": &"cured_leather", "name": "Cured Leather", "stations": W, "group": "Refined Stock", "level": 1, "gold": 3, "known": true,
			"inputs": [[&"beast_hide", 2]], "out": {"base": &"cured_leather", "count": 1}},
		{"id": &"firebomb", "name": "Firebomb", "stations": W, "group": "Bombs and Scrolls", "level": 4, "gold": 4, "known": true,
			"inputs": [[&"goblin_resin", 2], [&"stolen_linen", 1]], "out": {"base": &"firebomb", "count": 2}},
		{"id": &"frost_flask", "name": "Frost Flask", "stations": W, "group": "Bombs and Scrolls", "level": 6, "gold": 5, "known": true,
			"inputs": [[&"frost_crystal", 1], [&"goblin_resin", 1]], "out": {"base": &"frost_flask", "count": 2}},
		{"id": &"smoke_pellet", "name": "Smoke Pellet", "stations": W, "group": "Bombs and Scrolls", "level": 5, "gold": 4, "known": true,
			"inputs": [[&"grave_dust", 2], [&"stolen_linen", 1]], "out": {"base": &"smoke_pellet", "count": 2}},
		{"id": &"blinding_flask", "name": "Blinding Flask", "stations": W, "group": "Bombs and Scrolls", "level": 5, "gold": 5, "known": true,
			"inputs": [[&"wisp_mote", 1], [&"goblin_resin", 1]], "out": {"base": &"blinding_flask", "count": 2}},
		{"id": &"festering_bomb", "name": "Festering Bomb", "stations": W, "group": "Bombs and Scrolls", "level": 7, "gold": 6, "known": true,
			"inputs": [[&"ghoul_bile", 1], [&"grave_dust", 1], [&"stolen_linen", 1]], "out": {"base": &"festering_bomb", "count": 2}},
		{"id": &"town_portal", "name": "Town Portal Scroll", "stations": W, "group": "Bombs and Scrolls", "level": 2, "gold": 6, "known": true,
			"inputs": [[&"stolen_linen", 1], [&"wisp_mote", 1]], "out": {"base": &"town_portal", "count": 1}},
		{"id": &"hunters_charm", "name": "Hunter's Charm", "stations": W, "group": "Charms", "level": 3, "gold": 20, "known": true,
			"inputs": [[&"wolf_fang", 3], [&"cured_leather", 1], [&"iron_shard", 2]],
			"out": {"gear": {"rarity": R.ADVANCED, "quality": [0.08, 0.14], "ilvl_bonus": 0}},
			"variants": [{"label": "Ring, amulet or charm", "categories": [&"accessory"]}],
			"text": "An Advanced accessory of your level, fine quality."},
		{"id": &"champion_trinket", "name": "Champion's Trinket", "stations": W, "group": "Charms", "level": 8, "gold": 90,
			"inputs": [[&"champion_essence", 1], [&"wisp_mote", 2], [&"arcane_dust", 3], [&"cured_leather", 1]],
			"out": {"gear": {"rarity": R.ELITE, "quality": [0.12, 0.2], "ilvl_bonus": 1}},
			"variants": [{"label": "Ring, amulet or charm", "categories": [&"accessory"]}],
			"text": "An Elite accessory, one level above yours."},
		# ---- forge ----
		{"id": &"steel_ingot", "name": "Steel Ingot", "stations": F, "group": "Refined Stock", "level": 1, "gold": 4, "known": true,
			"inputs": [[&"iron_shard", 5]], "out": {"base": &"steel_ingot", "count": 1}},
		{"id": &"whetstone", "name": "Whetstone", "stations": F, "group": "Refined Stock", "level": 3, "gold": 3, "known": true,
			"inputs": [[&"iron_shard", 3], [&"orc_tusk", 1]], "out": {"base": &"whetstone", "count": 2}},
		{"id": &"tempered_weapon", "name": "Tempered Weapon", "stations": F, "group": "Weapons", "level": 2, "gold": 25, "known": true,
			"inputs": [[&"steel_ingot", 2], [&"cured_leather", 1], [&"wolf_fang", 2]],
			"out": {"gear": {"rarity": R.ADVANCED, "quality": [0.08, 0.14], "ilvl_bonus": 0}}, "variants": _weapon_variants(),
			"text": "An Advanced weapon of your level, fine quality."},
		{"id": &"tempered_armor", "name": "Tempered Armor", "stations": F, "group": "Armor", "level": 2, "gold": 22, "known": true,
			"inputs": [[&"steel_ingot", 1], [&"cured_leather", 2], [&"beast_hide", 2]],
			"out": {"gear": {"rarity": R.ADVANCED, "quality": [0.08, 0.14], "ilvl_bonus": 0}}, "variants": _armor_variants(),
			"text": "An Advanced armor piece of your level, fine quality."},
		{"id": &"champion_weapon", "name": "Champion's Weapon", "stations": F, "group": "Weapons", "level": 8, "gold": 120,
			"inputs": [[&"steel_ingot", 4], [&"champion_essence", 1], [&"ogre_sinew", 1], [&"orc_tusk", 2]],
			"out": {"gear": {"rarity": R.ELITE, "quality": [0.12, 0.2], "ilvl_bonus": 1}}, "variants": _weapon_variants(),
			"text": "An Elite weapon, one level above yours."},
		{"id": &"champion_armor", "name": "Champion's Armor", "stations": F, "group": "Armor", "level": 8, "gold": 110,
			"inputs": [[&"steel_ingot", 3], [&"cured_leather", 3], [&"champion_essence", 1], [&"orc_tusk", 2]],
			"out": {"gear": {"rarity": R.ELITE, "quality": [0.12, 0.2], "ilvl_bonus": 1}}, "variants": _armor_variants(),
			"text": "An Elite armor piece, one level above yours."},
		{"id": &"aetherforged_weapon", "name": "Aetherforged Weapon", "stations": F, "group": "Weapons", "level": 14, "gold": 400,
			"inputs": [[&"steel_ingot", 5], [&"champion_essence", 3], [&"rune_plate", 2], [&"aether_shard", 5]],
			"out": {"gear": {"rarity": R.MASTER, "quality": [0.16, 0.2], "ilvl_bonus": 2}}, "variants": _weapon_variants(),
			"text": "A Master weapon, two levels above yours."},
	]

static var _by_id := {}

static func recipe(id: StringName) -> Dictionary:
	if _by_id.is_empty():
		for r in recipes():
			_by_id[r.id] = r
	return _by_id.get(StringName(id), {})

static func all() -> Array:
	recipe(&"")
	return _by_id.values()

## What salvaging gives back: metal from heavy gear and weapons, hide and cloth from light gear, dust from anything
## magical. Amounts grow with rarity. Returns [[base id, count], ...].
static func salvage_yield(it: ItemInstance) -> Array:
	if it == null or not it.is_equipment():
		return []
	var tier := clampi(it.rarity, 0, BH.RARITY_COUNT - 1)
	var bulk := 1 + int(tier / 2) + int(it.ilvl / 10)
	var out := []
	var b := it.base
	match b.category:
		&"weapon":
			if b.weapon_type in [&"bow", &"crossbow", &"staff", &"wand"]:
				out.append([&"beast_hide" if b.weapon_type in [&"bow", &"crossbow"] else &"stolen_linen", bulk])
				out.append([&"iron_shard", maxi(1, bulk - 1)])
			else:
				out.append([&"iron_shard", bulk + 1])
		&"shield":
			out.append([&"iron_shard", bulk + 1])
		&"accessory":
			out.append([&"iron_shard", maxi(1, bulk - 1)])
		_:
			if b.weight_class == &"heavy":
				out.append([&"iron_shard", bulk + 1])
			elif b.weight_class == &"cloth":
				out.append([&"stolen_linen", bulk])
			else:
				out.append([&"beast_hide", bulk])
	if tier >= R.ADVANCED:
		out.append([&"arcane_dust", tier - 1])
	if tier >= R.ELITE:
		out.append([&"wisp_mote", 1 + int(tier >= R.MASTER)])
	if tier >= R.MYTHICAL:
		out.append([&"champion_essence", 1])
	return out
