extends TestCase

func _init() -> void:
	strict = true

func _item(id: StringName, count := 1) -> ItemInstance:
	var it := DB.make_item(id, BH.Rarity.COMMON, 1, 42)
	it.count = count
	return it

func test_capacity_and_reserved_belt() -> void:
	var inv := Inventory.new()
	eq(inv.capacity(), 100, "84 shared slots plus 16 reserved slots")
	for i in 84:
		eq(inv.add(_item(&"iron_helm")), 0, "equipment fits general bag")
	eq(inv.free_cells(), 0, "general bag full")
	ok(not inv.can_fit(_item(&"iron_helm")), "belt cannot hold gear")
	eq(inv.add(_item(&"iron_helm")), 1, "overflow returned")
	var potion := _item(&"health_potion", 320)
	ok(inv.can_fit(potion), "16 potion stacks fit reserved belt")
	eq(inv.add(potion), 0, "full belt accepted")
	eq(inv.count_of(&"health_potion"), 320, "all potions retained")
	ok(not inv.can_fit(_item(&"town_portal")), "both bags full")
	inv.take(0)
	eq(inv.add(_item(&"town_portal")), 0, "consumable overflow uses utility space")
	inv.move(1, 84)
	eq(inv.cells[1].base.id, &"iron_helm", "invalid swap leaves gear intact")
	eq(inv.cells[84].base.id, &"health_potion", "invalid swap leaves potion intact")
	done()

func test_partial_stacks_split_sort_and_save() -> void:
	var inv := Inventory.new()
	var potion := _item(&"health_potion", 15)
	inv.add(potion)
	var split := inv.split(inv.index_of(potion), 5)
	ok(inv.index_of(split) >= 84, "split uses belt")
	inv.add(_item(&"town_portal", 4))
	inv.add(_item(&"iron_helm"))
	inv.add(_item(&"iron_longsword"))
	potion.favorite = true
	for mode in Inventory.SORT_MODES:
		for reverse in [false, true]:
			inv.sort(mode, reverse)
			eq(inv.count_of(&"health_potion"), 15, "sort preserves total")
			for i in range(84, 100):
				ok(inv.cells[i] == null or inv.cells[i].base.is_consumable(), "sorting respects reserved cells")
	var restored := Inventory.new()
	restored.from_array(inv.to_array())
	eq(restored.to_array(), inv.to_array(), "save roundtrip preserves all cells and flags")
	near(restored.weight(), inv.weight(), 0.001, "all bags count toward load")
	ok(restored.consume(&"town_portal", 3), "belt scrolls can be consumed")
	eq(restored.count_of(&"town_portal"), 1, "correct remaining count")
	var small := Inventory.new(1)
	ok(not small.can_fit(_item(&"health_potion", 21)), "can_fit checks whole stack")
	done()

func test_legacy_save_migration_and_categories() -> void:
	var legacy := Inventory.new(60)
	legacy.add(_item(&"iron_helm"))
	legacy.add(_item(&"health_potion", 17))
	legacy.add(_item(&"town_portal", 7))
	legacy.add(_item(&"quest_seal_key"))
	var inv := Inventory.new()
	inv.from_array(legacy.to_array())
	eq(inv.count_of(&"health_potion"), 17, "legacy potions retained")
	eq(inv.cells[0].base.id, &"iron_helm", "gear slot preserved")
	eq(inv.cells[84].base.id, &"health_potion", "legacy potions moved to belt")
	ok(Inventory.matches_filter(_item(&"town_portal"), "scrolls"), "portal is a scroll")
	ok(Inventory.matches_filter(_item(&"recipe_berserker"), "scrolls"), "recipe is a scroll")
	ok(not Inventory.matches_filter(_item(&"town_portal"), "potions"), "scroll excluded from potions")
	ok(Inventory.matches_filter(_item(&"health_potion"), "potions"), "potion tab")
	ok(Inventory.matches_filter(_item(&"quest_seal_key"), "keys"), "keys tab")
	ok(Inventory.matches_filter(_item(&"silverleaf"), "materials"), "ingredients tab")
	done()

## Melee weapons scale with Strength; bows, crossbows and javelins scale with Dexterity (docs/EQUIPMENT_AND_BOSS_BALANCE_AUDIT.md, the
## in-game Guide and StatCalculator all say so). Dexterity always improves accuracy and critical chance.
const RANGED_WEAPONS := [&"bow", &"crossbow", &"javelin"]
const WEAPON_STATS := [&"physical_attack", &"phys_damage", &"weapon_min", &"weapon_max"]

func test_strength_and_dexterity_for_every_weapon() -> void:
	var cls := DB.class_def(&"knight")
	for type in DB.weapon_types.values():
		var lo := WeaponLoadout.new()
		lo.main_type = type
		lo.has_shield = true
		lo.shield_block = 0.2
		var base := StatCalculator.compute(cls, 10, {&"str": 10, &"dex": 10}, [], lo)
		var dex := StatCalculator.compute(cls, 10, {&"str": 10, &"dex": 40}, [], lo)
		var strength := StatCalculator.compute(cls, 10, {&"str": 40, &"dex": 10}, [], lo)
		var ranged: bool = type.id in RANGED_WEAPONS
		if ranged:
			ok(dex.get_stat(&"phys_damage") > base.get_stat(&"phys_damage"), "Dexterity increases physical damage: %s" % type.id)
			near(strength.get_stat(&"phys_damage"), base.get_stat(&"phys_damage"), 0.00001, "Strength does not add to %s damage" % type.id)
		else:
			ok(strength.get_stat(&"phys_damage") > base.get_stat(&"phys_damage"), "Strength increases physical damage: %s" % type.id)
		ok(dex.get_stat(&"accuracy") > base.get_stat(&"accuracy"), "Dexterity improves accuracy")
		ok(dex.get_stat(&"crit_chance") > base.get_stat(&"crit_chance"), "Dexterity improves critical chance")
		for stat in base.values:
			if stat in [&"dex", &"accuracy", &"crit_chance", &"accuracy_chance"] or (ranged and stat in WEAPON_STATS):
				continue
			near(dex.get_stat(stat), base.get_stat(stat), 0.00001, "Dexterity does not change %s on %s" % [stat, type.id])
		near(base.get_stat(&"carry_capacity"), 2.0 * (110.0 + 10.0 * 3.2), 0.001, "weight limit doubled")
	done()

func test_every_dungeon_displays_recommendation() -> void:
	for id in DataDungeons.order():
		var range := DataDungeons.level_range(id)
		var label := DataDungeons.recommended_levels(id)
		ok(str(range.x) in label and str(range.y) in label, "recommendation uses dungeon range")
		var gate := Teleporter.new()
		gate.dungeon_gate = id
		ok(label in gate.interact_text(), "entrance prompt shows recommendation")
		ok(label in DataDungeons.gate_destinations(null, id)[0].name, "travel choice shows recommendation")
		gate.free()
	for map in [&"catacombs", &"forgotten_temple", &"boss_arena"]:
		var gate := Teleporter.new()
		gate.destination_map = map
		gate.destination_name = DB.map_def(map).display_name
		ok(DataDungeons.map_recommendation(map) in gate.interact_text(), "story dungeon prompt includes levels")
		gate.free()
	done()

func test_full_bag_trade_and_two_handed_swap_are_atomic() -> void:
	var hero := HeroData.new()
	hero.setup(DB.class_def(&"knight"), "Full Bag Test")
	hero.init_new()
	hero.progress.allocated[&"str"] = 100
	var claymore := _item(&"rusted_claymore")
	hero.inventory.add(claymore)
	while hero.inventory.free_cells() > 0:
		hero.inventory.add(_item(&"iron_helm"))
	var before := hero.inventory.to_array()
	var main := hero.equipment.get_item(&"main_weapon")
	var sub := hero.equipment.get_item(&"sub_weapon")
	ok(hero.equip_from_inventory(claymore, &"main_weapon") != "", "two displaced items cannot fit one free general cell")
	eq(hero.inventory.to_array(), before, "failed equip leaves bag unchanged")
	eq(hero.equipment.get_item(&"main_weapon"), main, "main hand unchanged")
	eq(hero.equipment.get_item(&"sub_weapon"), sub, "off hand unchanged")
	var pot := _item(&"town_portal")
	hero.inventory.add(pot)
	# Starter scrolls may have absorbed this stack; offer the actual carried item.
	for item in hero.inventory.cells:
		if item != null and item.base.id == &"town_portal":
			pot = item
			break
	var mine := {"gold": 0, "items": [pot]}
	var theirs := {"gold": 0, "items": [_item(&"iron_helm")]}
	ok(TradeRules.swap(hero, mine, theirs) != "", "giving a belt item cannot free equipment space")
	ok(hero.inventory.index_of(pot) >= 0, "refused trade retains offered item")
	done()
