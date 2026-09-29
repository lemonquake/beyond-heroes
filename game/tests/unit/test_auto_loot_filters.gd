extends TestCase

func _init() -> void:
	strict = true

func _hero() -> HeroData:
	var hero := HeroData.new()
	hero.setup(DB.class_def(&"knight"), "Loot Test")
	return hero

func _item(id: StringName, count := 1) -> ItemInstance:
	var item := DB.make_item(id, BH.Rarity.COMMON, 1, 77)
	item.count = count
	return item

func test_categories_presets_and_names() -> void:
	var hero := _hero()
	var pot := _item(&"health_potion")
	var sword := _item(&"iron_longsword")
	var supplies := AutoLootRules.preset(2)
	eq(AutoLootRules.item_reason(_item(&"silverleaf"), hero, supplies), "", "crafting preset accepts ingredients")
	ok(AutoLootRules.item_reason(sword, hero, supplies) != "", "crafting preset excludes weapons")
	eq(AutoLootRules.item_reason(pot, hero, AutoLootRules.preset(3)), "", "consumable preset accepts potion")
	eq(AutoLootRules.category(_item(&"town_portal")), "scrolls", "portal category")
	eq(AutoLootRules.category(_item(&"recipe_berserker")), "scrolls", "recipe scroll category")
	eq(AutoLootRules.item_reason(sword, hero, {"include": "SILVER, longsword"}), "", "any name term matches case-insensitively")
	ok(AutoLootRules.item_reason(pot, hero, {"include": "longsword"}) != "", "inclusion skips unrelated item")
	ok(AutoLootRules.item_reason(sword, hero, {"include": "longsword", "exclude": "IRON"}) != "", "exclusion wins")
	var none := {"categories": {}}
	for key in AutoLootRules.CATEGORIES: none.categories[key] = false
	ok(AutoLootRules.item_reason(pot, hero, none) != "", "clear all takes nothing")
	var key := _item(&"quest_seal_key")
	none["always_quest"] = true
	eq(AutoLootRules.item_reason(key, hero, none), "", "explicit quest exception bypasses categories")
	none["exclude"] = "seal"
	ok(AutoLootRules.item_reason(key, hero, none) != "", "quest exception respects exclusions")
	done()

func test_equipment_and_value_rules() -> void:
	var hero := _hero()
	var sword := _item(&"iron_longsword")
	ok(AutoLootRules.item_reason(sword, hero, {"min_rarity": BH.Rarity.ELITE}) != "", "rarity threshold")
	ok(AutoLootRules.item_reason(sword, hero, {"min_level": 50}) != "", "item level threshold")
	ok(AutoLootRules.item_reason(sword, hero, {"min_sockets": 1}) != "", "socket threshold")
	ok(AutoLootRules.item_reason(sword, hero, {"weapon_types": {"sword": false}}) != "", "weapon type selection")
	ok(AutoLootRules.item_reason(sword, hero, {"min_value": 1000000}) != "", "minimum value")
	ok(AutoLootRules.item_reason(sword, hero, {"max_weight": 0.01}) != "", "drop weight limit")
	ok(AutoLootRules.item_reason(sword, hero, {"min_value_weight": 100000}) != "", "value per weight threshold")
	var high := _item(&"warden_plate")
	ok(AutoLootRules.item_reason(high, hero, {"usable_only": true}) != "", "high level gear rejected")
	var potion := _item(&"health_potion")
	eq(AutoLootRules.item_reason(potion, hero, {"min_level": 90, "min_sockets": 6, "usable_only": true}), "", "equipment-only rules spare supplies")
	done()

func test_capacity_reservations_limits_and_persistence() -> void:
	var hero := _hero()
	var pot := _item(&"health_potion", 5)
	hero.inventory.add(_item(&"health_potion", 18))
	ok(AutoLootRules.pickup_reason(pot, hero, hero.compute_stats(), {"consumable_cap": 20}) != "", "cap leaves entire drop on ground")
	eq(AutoLootRules.pickup_reason(pot, hero, hero.compute_stats(), {"consumable_cap": 25}), "", "below cap accepted")
	eq(hero.inventory.count_of(&"health_potion"), 18, "preflight never consumes items")
	var sword := _item(&"iron_longsword")
	ok(AutoLootRules.pickup_reason(sword, hero, hero.compute_stats(), {"reserve_slots": 84}) != "", "reserve protects general slots")
	eq(AutoLootRules.pickup_reason(pot, hero, hero.compute_stats(), {"reserve_slots": 84}), "", "belt stacking does not use reserve")
	var stats := hero.compute_stats()
	stats.set_stat(&"carry_weight", stats.get_stat(&"carry_capacity") * 0.5)
	ok(AutoLootRules.pickup_reason(pot, hero, stats, {"max_load": 50}) != "", "custom load limit")
	stats.set_stat(&"carry_weight", stats.get_stat(&"carry_capacity"))
	ok(AutoLootRules.pickup_reason(_item(&"quest_seal_key"), hero, stats, {"always_quest": true}) != "", "exceptions still obey load limit")
	var original := Settings.auto_loot_rules.duplicate(true)
	Settings.auto_loot_rules = {"categories": {"weapons": false}, "exclude": "rusted", "max_load": 70.0}
	var saved: Dictionary = JSON.parse_string(JSON.stringify(Settings.to_dict()))
	var copy := preload("res://src/autoload/settings.gd").new()
	copy.from_dict(saved)
	eq(copy.auto_loot_rules, Settings.auto_loot_rules, "rules survive settings/save serialization")
	copy.free()
	Settings.auto_loot_rules = original
	done()

func test_magnet_rechecks_load_before_pickup() -> void:
	var original_rules := Settings.auto_loot_rules.duplicate(true)
	var original_enabled := Settings.auto_loot_enabled
	var original_mode := Settings.auto_loot_mode
	Settings.auto_loot_mode = 1
	Settings.auto_loot_rules = {}
	Settings.auto_loot_enabled = true
	var player := Player.new()
	player.hero = _hero()
	player.stats = player.hero.compute_stats()
	var drop := LootDrop.new()
	drop.item = _item(&"iron_longsword")
	ok(drop.wants_auto_loot(player), "matching item can auto-loot")
	Settings.auto_loot_rules = {"categories": {"weapons": false}}
	ok(not drop.wants_auto_loot(player), "changed filters reject an in-flight drop")
	drop.free()
	player.free()
	Settings.auto_loot_rules = original_rules
	Settings.auto_loot_enabled = original_enabled
	Settings.auto_loot_mode = original_mode
	done()
