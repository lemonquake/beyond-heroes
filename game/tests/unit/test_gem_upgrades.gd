extends TestCase

func _init() -> void:
	strict = true

func _give(h: HeroData, id: StringName, count: int) -> ItemInstance:
	var it := DB.make_item(id, BH.Rarity.COMMON, 1, 1)
	it.count = count
	h.inventory.add(it)
	return it

func test_every_family_upgrades_one_tier_and_stops_at_orbital() -> void:
	eq(DataCrystals.upgrade_recipes().size(), DataCrystals.ORDER.size() * 3, "all twelve families have three upgrade recipes")
	for family in DataCrystals.ORDER:
		for grade in 3:
			var h := Game.new_hero(&"knight", "Gem test")
			var input := DataCrystals.id_of(family, grade)
			var output := DataCrystals.id_of(family, grade + 1)
			var r := DataCrafting.recipe(StringName("upgrade_" + String(input)))
			_give(h, input, 4)
			for station in [&"forge", &"alchemy", &"workbench"]:
				ok(Crafting.recipes_for(station).any(func(recipe): return recipe.id == r.id), "%s is available at %s" % [r.id, station])
				ok(Crafting.check(h, r, station) == "", "gem upgrades need no scroll, gold or extra levels")
			var made := Crafting.craft(h, r, &"workbench")
			ok(made.ok, "%s upgrades successfully" % input)
			eq(h.inventory.count_of(input), 0, "exactly four input gems consumed")
			eq(h.inventory.count_of(output), 1, "one matching next-tier gem received")
			eq(h.inventory.gold, 0, "no extra gold fee")
			var back := HeroData.from_dict(h.to_dict())
			eq(back.inventory.count_of(output), 1, "upgraded gem survives saving")
		ok(DataCrafting.recipe(StringName("upgrade_" + String(DataCrystals.id_of(family, 3)))).is_empty(), "Orbital cannot be upgraded")
	done()

func test_mixed_tiers_families_and_protected_gems_are_not_consumed() -> void:
	var h := Game.new_hero(&"knight", "Gem test")
	var r := DataCrafting.recipe(&"upgrade_ember_fragment")
	_give(h, &"ember_fragment", 3)
	_give(h, &"ember_shard", 4)
	_give(h, &"aqua_fragment", 4)
	var before := h.inventory.to_array()
	ok(not Crafting.craft(h, r, &"forge").ok, "three matching gems are insufficient")
	eq(h.inventory.to_array(), before, "failed upgrade preserves all gems")
	var protected := DB.make_item(&"ember_fragment", BH.Rarity.COMMON, 1, 1)
	protected.count = 4
	protected.locked = true
	h.inventory.cells[5] = protected
	eq(Crafting.max_craftable(h, r), 0, "locked gems do not count toward crafting")
	protected.locked = false
	protected.favorite = true
	eq(Crafting.max_craftable(h, r), 0, "favorite gems do not count toward crafting")
	_give(h, &"ember_fragment", 1)
	ok(Crafting.craft(h, r, &"alchemy").ok, "four unprotected gems can be upgraded")
	eq(protected.count, 4, "protected gems are retained")
	eq(h.inventory.count_of(&"aqua_fragment"), 4, "other family is retained")
	eq(h.inventory.count_of(&"ember_shard"), 5, "existing output stack receives one upgraded gem")
	done()

func test_batch_and_bag_space_are_atomic() -> void:
	var h := Game.new_hero(&"knight", "Gem test")
	h.inventory = Inventory.new(2)
	var r := DataCrafting.recipe(&"upgrade_ember_fragment")
	_give(h, &"ember_fragment", 9)
	_give(h, &"aqua_fragment", 1)
	var before := h.inventory.to_array()
	ok(not Crafting.craft(h, r, &"forge", 2).ok, "a full bag refuses outputs when inputs do not free a slot")
	eq(h.inventory.to_array(), before, "full-bag failure consumes nothing")
	h.inventory.cells[0].count = 8
	ok(Crafting.craft(h, r, &"forge", 2).ok, "consuming the input stack frees room for a batch")
	eq(h.inventory.count_of(&"ember_fragment"), 0, "batch consumes eight gems")
	eq(h.inventory.count_of(&"ember_shard"), 2, "batch produces two next-tier gems")
	var split := Game.new_hero(&"knight", "Gem test")
	var crystal := DB.make_item(&"ember_fragment", BH.Rarity.COMMON, 1, 1)
	crystal.count = 2
	split.inventory.cells[0] = crystal
	split.inventory.cells[1] = crystal.clone()
	ok(Crafting.craft(split, r, &"workbench").ok, "four gems can be consumed across separate stacks")
	eq(split.inventory.count_of(&"ember_shard"), 1, "split stacks still make one gem")
	done()
