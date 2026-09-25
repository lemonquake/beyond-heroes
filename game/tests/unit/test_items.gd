extends TestCase
## Item generation, inventory, save/load round trip, migrations.

func test_generation_rules_per_rarity() -> void:
	var r := rng(11)
	var base := DB.item_base(&"knights_arming_sword")
	for rarity in 6:
		for i in 60:
			var it := ItemGenerator.generate(base, 30, rarity, r)
			var rule: Array = ItemGenerator.RARITY_RULES[rarity]
			if it.affixes.size() < rule[0] or it.affixes.size() > rule[1]:
				ok(false, "rarity %d affix count %d" % [rarity, it.affixes.size()])
				return
			var groups := {}
			for a in it.affixes:
				var def := DB.affix(StringName(a.id))
				if groups.has(def.group):
					ok(false, "duplicate affix group %s" % def.group)
					return
				groups[def.group] = true
				if not def.allows(&"weapon"):
					ok(false, "affix %s not allowed on weapons" % a.id)
					return
				if int(def.tiers[a.tier][0]) > 30:
					ok(false, "tier above item level")
					return
			eq(it.powers.size(), rule[2], "powers for rarity %d" % rarity)
			ok(it.quality <= float(rule[5]) + 0.0001, "quality bounded")
	ok(true, "rarity rules hold")

func test_generation_deterministic() -> void:
	var base := DB.item_base(&"warden_plate")
	var a := ItemGenerator.generate(base, 20, BH.Rarity.EPIC, rng(5)).to_dict()
	var b := ItemGenerator.generate(base, 20, BH.Rarity.EPIC, rng(5)).to_dict()
	a.erase("seed"); b.erase("seed")
	eq(a, b, "same seed same item")

func test_rarity_distribution_and_magic_find() -> void:
	var r := rng(8)
	var counts := [0, 0, 0, 0, 0, 0]
	var counts_mf := [0, 0, 0, 0, 0, 0]
	for i in 20000:
		counts[ItemGenerator.roll_rarity(r, 0.0)] += 1
		counts_mf[ItemGenerator.roll_rarity(r, 1.0)] += 1
	ok(counts[0] > counts[1] and counts[1] > counts[2] and counts[2] > counts[3] and counts[3] > counts[4] and counts[4] > counts[5], "rarity strictly rarer: %s" % [counts])
	ok(counts_mf[4] + counts_mf[5] > counts[4] + counts[5], "magic find improves top rarities")

func test_rarity_does_not_explode_base_stats() -> void:
	var base := DB.item_base(&"iron_hauberk")
	var mythic := ItemGenerator.generate(base, 1, BH.Rarity.MYTHIC, rng(1))
	mythic.affixes = mythic.affixes.filter(func(a): return not String(a.id).begins_with("local_def"))
	ok(mythic.defense_value() <= base.defense * 1.2 + 0.001, "base defense within +20% quality")

func test_inventory_stacking_sort_filter() -> void:
	var inv := Inventory.new(10)
	var p1 := DB.make_item(&"health_potion", 0, 1, 1)
	p1.count = 15
	var p2 := DB.make_item(&"health_potion", 0, 1, 2)
	p2.count = 10
	inv.add(p1)
	inv.add(p2)
	eq(inv.count_of(&"health_potion"), 25, "stack total")
	eq(inv.free_cells(), 8, "two cells (20 + 5)")
	ok(inv.consume(&"health_potion", 21), "consume across stacks")
	eq(inv.count_of(&"health_potion"), 4, "remaining")
	var sword := DB.make_item(&"iron_longsword", BH.Rarity.RARE, 5, 3)
	var helm := DB.make_item(&"iron_helm", BH.Rarity.MAGIC, 5, 4)
	inv.add(helm)
	inv.add(sword)
	inv.sort("rarity")
	eq(inv.cells[0], sword, "rare first")
	ok(Inventory.matches_filter(sword, "weapons") and not Inventory.matches_filter(helm, "weapons"), "filters")
	var full := Inventory.new(1)
	full.add(DB.make_item(&"iron_helm", 0, 1, 1))
	eq(full.add(DB.make_item(&"iron_helm", 0, 1, 2)), 1, "overflow reported")

func test_save_round_trip_exact() -> void:
	var h := HeroData.new()
	h.setup(DB.class_def(&"mage"), "Ilyra")
	h.init_new()
	h.progress.add_xp(5000)
	h.progress.allocate(&"int", 2)
	h.progress.skill_points = 5
	h.spend_skill_point(&"frost_nova")
	h.progress.talent_points = 3
	h.spend_talent_point(&"m_int")
	var r := rng(77)
	for i in 8:
		var b := ItemGenerator.random_base(r, 15)
		h.inventory.add(ItemGenerator.generate(b, 15, ItemGenerator.roll_rarity(r, 2.0), r))
	h.inventory.gold = 1234
	h.discovered_maps[&"ruined_forest"] = true
	h.unlocked_teleporters[&"forest_gate"] = true
	h.world_flags[&"elite_forest"] = true
	h.current_map = &"ruined_forest"
	var d1 := SaveSystem.serialize(h)
	var json := JSON.stringify(d1)
	var parsed: Dictionary = JSON.parse_string(json)
	var h2 := HeroData.from_dict(SaveSystem.migrate(parsed)["hero"])
	eq(JSON.stringify(h2.to_dict()), JSON.stringify(h.to_dict()), "hero dict identical after JSON round trip")
	var s1 := h.compute_stats().values
	var s2 := h2.compute_stats().values
	for k in s1:
		near(float(s2.get(k, -999.0)), float(s1[k]), 0.00001, "stat %s reproduced" % k)

func test_save_migration_v1() -> void:
	var v1 := {"version": 1, "hero": {"class": "knight", "name": "Old", "hotbar": ["cleave", "", "", "", "", ""],
		"progress": {"level": 3}}}
	var m := SaveSystem.migrate(v1)
	eq(m.version, SaveSystem.CURRENT_VERSION, "migrated to current")
	ok(m.hero.has("skill_bar") and not m.hero.has("hotbar"), "hotbar renamed")
	var h := HeroData.from_dict(m.hero)
	eq(h.progress.level, 3, "level kept")
	eq(h.skill_bar[0], &"cleave", "bar kept")
