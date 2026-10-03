extends TestCase
## Item generation (ten rarity tiers), licenses, masterwork, powers, sets, uniques, inventory tools, save/load, migrations.

func test_exact_rarity_tiers() -> void:
	# the ten tiers of the design spec, then (bh-034) the four Ascendant tiers that only the Ascendant collections carry
	eq(BH.RARITY_COUNT, 14, "ten tiers and four Ascendant ones")
	eq(BH.RARITY_NAMES, ["Beginner", "Common", "Basic", "Advanced", "Licensed", "Elite", "Master", "Mythical", "Legendary", "Aether",
		"Cosmic", "Divine", "Eternal", "Primordial"], "exact names in order")
	eq(BH.Rarity.AETHER, 9, "Aether is the highest rolled tier")
	eq(BH.Rarity.PRIMORDIAL, 13, "Primordial is the highest")
	eq(ItemGenerator.RULES.size(), 14, "one rule per tier")
	eq(ItemGenerator.WEIGHTS.size(), 14, "one weight per tier")
	eq(BH.RARITY_COLORS.size(), 14, "one color per tier")
	var seen := {}
	for c in BH.RARITY_COLORS:
		seen[c.to_html()] = true
	eq(seen.size(), 14, "every tier has a distinct color")

func test_generation_rules_per_rarity() -> void:
	var r := rng(11)
	var base := DB.item_base(&"knights_arming_sword")
	for rarity in range(BH.Rarity.COSMIC, BH.RARITY_COUNT):
		eq(ItemGenerator.generate(base, 30, rarity, r).rarity, BH.Rarity.AETHER, "a plain base never takes an Ascendant rarity")
	for rarity in BH.Rarity.AETHER + 1:
		for i in 40:
			var it := ItemGenerator.generate(base, 30, rarity, r)
			var rule: Array = ItemGenerator.RULES[rarity]
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
				if not def.allows(&"weapon") or rarity < def.min_rarity:
					ok(false, "affix %s not allowed here" % a.id)
					return
				if int(def.tiers[a.tier][0]) > 30:
					ok(false, "tier above item level")
					return
			var expected_powers := {BH.Rarity.MYTHICAL: 1, BH.Rarity.LEGENDARY: 1, BH.Rarity.AETHER: 2}
			# bh-012: Licensed-or-better pieces may also carry one relic passive (a utility stat bundle) on top
			var relic := it.powers.filter(func(pid): return DB.power(StringName(pid)) != null and DB.power(StringName(pid)).tier == &"relic").size()
			ok(relic <= 1 and (relic == 0 or rarity >= BH.Rarity.LICENSED), "at most one relic passive, Licensed+ only (rarity %d)" % rarity)
			eq(it.powers.size() - relic, expected_powers.get(rarity, 0), "powers for rarity %d" % rarity)
			ok(it.quality <= float(rule[5]) + 0.0001 and it.quality >= float(rule[4]) - 0.0001, "quality bounded")
			eq(it.license != &"", rarity == BH.Rarity.LICENSED, "license only on Licensed (%d)" % rarity)
			var mw := it.affixes.filter(func(a): return a.get("mw", false)).size()
			eq(mw, 1 if rarity == BH.Rarity.MASTER else 0, "one masterwork affix only on Master")
	ok(true, "rarity rules hold")

func test_power_tiers_match_rarity() -> void:
	var r := rng(4)
	var base := DB.item_base(&"storm_staff")
	for i in 30:
		var myth := ItemGenerator.generate(base, 20, BH.Rarity.MYTHICAL, r)
		eq(DB.power(StringName(myth.powers[0])).tier, &"mythical", "mythical power on Mythical")
		var leg := ItemGenerator.generate(base, 20, BH.Rarity.LEGENDARY, r)
		eq(DB.power(StringName(leg.powers[0])).tier, &"legendary", "legendary power on Legendary")
		var ae := ItemGenerator.generate(base, 20, BH.Rarity.AETHER, r)
		var tiers := ae.powers.map(func(p): return DB.power(StringName(p)).tier)
		ok(tiers.has(&"aether") and tiers.has(&"legendary"), "Aether has a legendary + an aether power: %s" % [tiers])
		ok(ae.display_name() != base.display_name, "Aether item has a special name")

func test_masterwork_affix_is_perfect() -> void:
	var r := rng(21)
	var base := DB.item_base(&"brigandine")
	for i in 30:
		var it := ItemGenerator.generate(base, 25, BH.Rarity.MASTER, r)
		for a in it.affixes:
			if a.get("mw", false):
				var def := DB.affix(StringName(a.id))
				var tiers := def.allowed_tiers(25)
				var top: Array = def.tiers[tiers[tiers.size() - 1]]
				near(float(a.value), float(top[2]), 0.0011, "masterwork value is the best tier maximum")

func test_license_bonus_applies_and_scales() -> void:
	var it := DB.make_item(&"iron_hauberk", BH.Rarity.LICENSED, 10, 99)
	ok(it.license != &"", "licensed item has a license")
	var lic: Dictionary = DB.licenses[it.license]
	var mods := it.license_modifiers()
	eq(mods.size(), lic.mods.size(), "one modifier per license line")
	near(mods[0].value, float(lic.mods[0][2]) + float(lic.mods[0][3]) * 9.0, 0.0001, "license value scales with item level")
	var all := it.modifiers()
	ok(all.any(func(m): return m.source.ends_with("license")), "license modifiers are part of the item's modifiers")

func test_generation_deterministic() -> void:
	var base := DB.item_base(&"warden_plate")
	for rarity in [BH.Rarity.ELITE, BH.Rarity.AETHER, BH.Rarity.LICENSED]:
		var a := ItemGenerator.generate(base, 20, rarity, rng(5)).to_dict()
		var b := ItemGenerator.generate(base, 20, rarity, rng(5)).to_dict()
		eq(a, b, "same seed same item (rarity %d)" % rarity)

func test_rarity_distribution_and_magic_find() -> void:
	var r := rng(8)
	var counts := []
	var counts_mf := []
	counts.resize(10); counts.fill(0)
	counts_mf.resize(10); counts_mf.fill(0)
	for i in 60000:
		counts[ItemGenerator.roll_rarity(r, 0.0, 0.0, 30)] += 1
		counts_mf[ItemGenerator.roll_rarity(r, 1.0, 0.0, 30)] += 1
	eq(counts[0], 0, "Beginner never drops")
	var strictly := true
	for i in range(1, 9):
		if counts[i] <= counts[i + 1]:
			strictly = false
	ok(strictly, "each tier rarer than the one below: %s" % [counts])
	ok(counts_mf[8] + counts_mf[9] > counts[8] + counts[9], "magic find improves top rarities")
	var low := [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	for i in 20000:
		low[ItemGenerator.roll_rarity(r, 5.0, 2.0, 1)] += 1
	eq(low[9] + low[8] + low[7], 0, "item level gates the top tiers")

func test_rarity_does_not_explode_base_stats() -> void:
	var base := DB.item_base(&"iron_hauberk")
	for rarity in BH.RARITY_COUNT:
		var it := ItemGenerator.generate(base, 1, rarity, rng(1 + rarity))
		it.affixes = it.affixes.filter(func(a): return not String(a.id).begins_with("local_def"))
		ok(it.defense_value() <= base.defense * 1.2 + 0.001, "base defense within +20%% quality at tier %d" % rarity)

func test_sets_and_bonuses() -> void:
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "Set Tester")
	h.progress.add_xp(XpCurve.total_xp_for_level(12))
	for a in BH.ATTRIBUTES:
		h.progress.allocated[a] = 30
	h.set_tier(2)   # Master-rarity set pieces need a Class D hero (tier gating, docs/LORE.md §5)
	var pieces := []
	for id in DB.item_set(&"aether_guardian").pieces:
		var it := DB.make_item(id, BH.Rarity.MASTER, 12, hash(String(id)))
		eq(it.rarity, BH.Rarity.MASTER, "set piece rarity")
		eq(it.display_name(), it.base.display_name, "set pieces keep their set name")
		pieces.append(it)
		h.inventory.add(it)
	var base_stats := h.compute_stats()   # pieces carried in the bag: same weight as when worn
	h.equip_from_inventory(pieces[0])
	eq(h.equipment.set_counts().get(&"aether_guardian", 0), 1, "one piece counted")
	var one := h.compute_stats()
	h.equip_from_inventory(pieces[1])
	var two := h.compute_stats()
	var expected_two_pieces: float = (one.get_stat(&"defense") + pieces[1].defense_value())
	ok(two.get_stat(&"defense") > expected_two_pieces + 39.0, "2-piece bonus adds Defense")
	for i in range(2, 5):
		h.equip_from_inventory(pieces[i])
	var five := h.compute_stats()
	eq(h.equipment.set_counts().get(&"aether_guardian", 0), 5, "five pieces")
	ok(five.has_flag(&"aether_pulse"), "5-piece flag active")
	# Remove everything -> exact return to the original snapshot.
	for s in BH.SLOTS:
		h.unequip_to_inventory(s)
	var after := h.compute_stats()
	for k in base_stats.values:
		near(float(after.values.get(k, -999.0)), float(base_stats.values[k]), 0.00001, "stat %s restored after removing the set" % k)
	ok(not after.has_flag(&"aether_pulse"), "flag removed")

func test_uniques_fixed() -> void:
	var it := DB.make_item(&"u_dawnbreaker", BH.Rarity.COMMON, 10, 1)
	eq(it.rarity, BH.Rarity.AETHER, "unique forces its rarity")
	eq(it.display_name(), "Dawnbreaker", "unique name")
	ok(it.powers.has("a_fifth_stagger"), "fixed power present")
	var flags := it.modifiers().filter(func(m): return String(m.stat) == "flag_fifth_stagger")
	eq(flags.size(), 1, "unique power flag granted once")

func test_item_naming() -> void:
	var r := rng(3)
	var base := DB.item_base(&"iron_longsword")
	var found := false
	for i in 40:
		var it := ItemGenerator.generate(base, 10, BH.Rarity.ADVANCED, r)
		var n := it.display_name()
		if n.contains("Iron Longsword") and n.contains(" of ") and n != "Iron Longsword":
			found = true
			break
	ok(found, "Advanced items read like 'Flaming Iron Longsword of the Ox'")

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
	var sword := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 5, 3)
	var helm := DB.make_item(&"iron_helm", BH.Rarity.BASIC, 5, 4)
	inv.add(helm)
	inv.add(sword)
	inv.sort("rarity")
	eq(inv.cells[0], sword, "elite first")
	helm.favorite = true
	inv.sort("rarity")
	eq(inv.cells[0], helm, "favorites always first")
	ok(Inventory.matches_filter(sword, "weapons") and not Inventory.matches_filter(helm, "weapons"), "category filter")
	ok(Inventory.matches_filter(sword, "all", BH.Rarity.ELITE) and not Inventory.matches_filter(helm, "all", BH.Rarity.ELITE), "rarity filter")
	ok(Inventory.matches_filter(sword, "all", 0, "longsword") and not Inventory.matches_filter(helm, "all", 0, "longsword"), "search")
	var full := Inventory.new(1)
	full.add(DB.make_item(&"iron_helm", 0, 1, 1))
	eq(full.add(DB.make_item(&"iron_helm", 0, 1, 2)), 1, "overflow reported")

func test_split_move_destroy_junk() -> void:
	var inv := Inventory.new(6)
	var p := DB.make_item(&"mana_potion", 0, 1, 1)
	p.count = 12
	inv.add(p)
	var part := inv.split(0, 5)
	ok(part != null, "split creates a stack")
	eq(p.count, 7, "source reduced")
	eq(part.count, 5, "new stack size")
	eq(inv.count_of(&"mana_potion"), 12, "split preserves total")
	ok(inv.split(0, 7) == null, "cannot split a whole stack")
	ok(inv.split(0, 0) == null, "cannot split zero")
	inv.move(inv.index_of(part), 0)
	eq(inv.cells[0].count, 12, "moving onto the same kind merges")
	eq(inv.count_of(&"mana_potion"), 12, "merge preserves total")
	var junk := DB.make_item(&"copper_ring", BH.Rarity.COMMON, 1, 7)
	inv.add(junk)
	junk.junk = true
	eq(inv.junk_items(), [junk], "junk listed")
	junk.locked = true
	eq(inv.junk_items(), [], "locked items never count as junk")
	ok(not inv.destroy(junk), "locked item cannot be destroyed")
	junk.locked = false
	ok(inv.destroy(junk), "unlocked destroy")
	eq(inv.index_of(junk), -1, "destroyed item gone")

func test_prices_rise_with_rarity() -> void:
	var prev := -1.0
	for rarity in BH.RARITY_COUNT:
		var it := ItemInstance.new()
		it.base = DB.item_base(&"iron_hauberk")
		it.rarity = rarity
		it.ilvl = 10
		ok(it.base_value() > prev, "tier %d worth more than tier %d" % [rarity, rarity - 1])
		prev = it.base_value()
	var q := DB.make_item(&"quest_tablet", 0, 1, 1)
	eq(q.sell_value(), 0, "quest items cannot be sold")

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
	for rarity in [BH.Rarity.LICENSED, BH.Rarity.MASTER, BH.Rarity.AETHER]:
		var it := ItemGenerator.generate(DB.item_base(&"storm_staff"), 15, rarity, r)
		it.locked = rarity == BH.Rarity.AETHER
		it.favorite = rarity == BH.Rarity.MASTER
		it.junk = rarity == BH.Rarity.LICENSED
		h.inventory.add(it)
	h.inventory.add(DB.make_item(&"sage_robe", BH.Rarity.MASTER, 12, 5))
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

func test_save_migration_v2_rarity_remap() -> void:
	# v2 stored six rarities (Common..Mythic). They map onto the ten-tier scale.
	var v2 := {"version": 2, "hero": {"class": "knight", "name": "Old", "progress": {"level": 5},
		"inventory": [{"base": "iron_helm", "rarity": 0}, {"base": "iron_helm", "rarity": 2}, {"base": "iron_helm", "rarity": 5}]}}
	var m := SaveSystem.migrate(v2)
	var inv: Array = m.hero.inventory
	eq(int(inv[0].rarity), BH.Rarity.COMMON, "old Common -> Common")
	eq(int(inv[1].rarity), BH.Rarity.ELITE, "old Rare -> Elite")
	eq(int(inv[2].rarity), BH.Rarity.AETHER, "old Mythic -> Aether")
