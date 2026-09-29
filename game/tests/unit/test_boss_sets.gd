extends TestCase

const BossSets = preload("res://src/data/data_boss_sets.gd")

func _init() -> void:
	strict = true

func _hero(cls := &"knight") -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls), "Boss collection checks")
	h.progress.level = 60
	h.guild = &"swordfin"
	h.set_tier(2)
	for attr in BH.ATTRIBUTES:
		h.progress.allocated[attr] = 100
	return h

func _enemy(level: int, kind := "lord") -> Enemy:
	var def := EnemyDef.new()
	def.archetype = &"boss" if kind == "lord" else &"melee"
	def.display_name = "Test boss"
	var e := Enemy.new().setup(def, level)
	if kind in ["usurper", "guardian", "miniboss"]:
		e.make_miniboss({"id": &"boss_set_test", "name": "Test champion"})
	if kind == "usurper":
		e.miniboss["raid_only"] = &"warren"
	if kind == "guardian":
		e.set_meta(&"depth_guardian", true)
	if kind == "elite":
		e.is_elite = true
	return e

func _piece(set_id: StringName, slot: StringName, level := 32) -> ItemInstance:
	return DB.make_item(BossSets.piece_id(set_id, slot), BH.Rarity.MASTER, level, 42)

func test_fifteen_complete_sets_exact_slots_and_all_bonuses() -> void:
	eq(BossSets.ROWS.size(), 15, "15 special boss sets")
	for name in ["Dragonforge", "Truth of Raikuru", "Crimson Glory", "Grievance of the Fairy", "Wailing Mistress"]:
		ok(BossSets.ROWS.any(func(r): return r[1] == name), "requested name retained: %s" % name)
	var ids := {}
	var pieces := 0
	var effects := {}
	for entry in BossSets.ROWS:
		var set_id := StringName(entry[0])
		var sd := DB.item_set(set_id)
		var h := _hero(StringName(entry[2]))
		var slots := BossSets.slots_for_set(set_id)
		eq(sd.thresholds(), [3, 6, slots.size()], "3, 6, full bonuses: %s" % set_id)
		eq(slots.size(), 12 if entry[3] in BossSets.TWO_HANDED else 13, "complete legal loadout")
		for slot in slots:
			var it := _piece(set_id, slot)
			ok(it != null and it.base.boss_exclusive, "catalog piece exists and is boss-only")
			ok(not ids.has(it.base.id), "distinct item ID")
			ids[it.base.id] = true
			pieces += 1
			eq(it.base.level_req, 30, "all sets available from level 30")
			eq(it.base.drop_level, 30, "drop minimum 30")
			eq(it.base.equipment_slots(), [slot], "piece has one exact slot")
			eq(it.rarity, BH.Rarity.MASTER, "Master quality")
			eq(h.equipment.auto_slot(it), slot, "automatic equip targets correct hand/foot/accessory")
			ok(h.equipment.equip(it, slot, 60, TempoRules.NO_ATTR).ok, "all pieces can be worn together")
		eq(h.equipment.set_counts()[set_id], slots.size(), "full set counts every distinct piece")
		var stats := h.compute_stats()
		var effect := StringName(entry[5])
		ok(not effects.has(effect), "each full-set combat effect is different")
		effects[effect] = true
		ok(stats.has_flag(effect), "full bonus enters actual stat calculation")
		for value in stats.values.values():
			ok(is_finite(float(value)), "full set yields finite stats")
		h.equipment.unequip(&"accessory_4")
		ok(not h.compute_stats().has_flag(effect), "removing one piece removes full bonus")
		ok(not sd.modifiers_for(5).is_empty(), "3-piece bonus survives before six")
		eq(sd.modifiers_for(2).size(), 0, "no bonus below three pieces")
		eq(sd.modifiers_for(6).size(), 4, "3 and 6 bonuses accumulate")
	eq(pieces, 187, "187 distinct pieces across 15 full sets")
	done()

func test_slot_restrictions_master_rank_and_save_roundtrip() -> void:
	var h := _hero()
	var left := _piece(&"dragonforge", &"gloves_1")
	var right := _piece(&"dragonforge", &"gloves_2")
	ok(h.equipment.check(left, &"gloves_2", 60, TempoRules.NO_ATTR) != "", "left gauntlet cannot occupy right slot")
	h.equipment.equip(left, &"gloves_1", 60, TempoRules.NO_ATTR)
	h.equipment.equip(right, &"gloves_2", 60, TempoRules.NO_ATTR)
	ok(h.swap_equipped(&"gloves_1", &"gloves_2") != "", "drag swapping cannot bypass exact slots")
	eq(h.equipment.set_counts()[&"dragonforge"], 2, "distinct gauntlets count individually")
	var loaded := HeroData.from_dict(h.to_dict())
	eq(loaded.equipment.get_item(&"gloves_1").base.id, left.base.id, "piece identity survives saving")
	eq(loaded.equipment.get_item(&"gloves_2").base.id, right.base.id, "paired piece survives saving")
	loaded.equipment.tier_rank = 1
	ok(loaded.equipment.check(left, &"gloves_1", 60, TempoRules.NO_ATTR).contains("Class D"), "Master gear preserves Class D gate")
	ok(loaded.equipment.check(left, &"gloves_1", 29, TempoRules.NO_ATTR).contains("level 30"), "cannot equip before level 30")
	done()

func test_eligibility_exact_actual_level_and_repeatable_bosses() -> void:
	var h := _hero()
	var r := rng(171)
	for kind in ["lord", "usurper", "guardian", "normal", "elite", "miniboss"]:
		for level in [28, 29, 30, 60]:
			var e := _enemy(level, kind)
			var expected: bool = level >= 30 and kind in ["lord", "usurper", "guardian"]
			eq(BossSets.eligible(e), expected, "%s actual level %d gate" % [kind, level])
			var item := BossSets.roll(e, h, r)
			eq(item != null, expected, "only an eligible encounter produces set piece")
			if item:
				eq(item.ilvl, level + 2, "gear scales to boss drop level")
			e.free()
	var fake := _enemy(60, "normal")
	fake.is_boss = true
	ok(not BossSets.eligible(fake), "a rank bit on an ordinary enemy is insufficient")
	fake.free()
	done()

func test_exactly_one_set_piece_per_eligible_reward_bundle() -> void:
	var saved_rng := Loot.rng.state
	Loot.rng.seed = 91031
	var p := Player.new()
	p.hero = _hero(&"ranger")
	p.stats = p.hero.compute_stats()
	for kind in ["lord", "usurper", "guardian", "elite", "miniboss"]:
		for level in [29, 30, 60]:
			var e := _enemy(level, kind)
			for iteration in 40:
				var drops := Loot.equipment_for(e, p)
				var special := drops.filter(func(it): return it.base.boss_exclusive)
				eq(special.size(), 1 if BossSets.eligible(e) else 0, "exactly one new set item on eligible encounters")
				if BossSets.eligible(e):
					eq(drops.filter(func(it): return it.base.set_id != &"").size(), 1, "no second set piece from generic set roll")
					ok(drops.size() >= 4, "ordinary reward bundle remains")
			e.free()
	p.free()
	Loot.rng.state = saved_rng
	done()

func test_bag_worn_companions_hall_and_injected_vault_count_once() -> void:
	var h := _hero()
	var slots := BossSets.slots_for_set(&"dragonforge")
	var inventory_piece := _piece(&"dragonforge", slots[0])
	h.inventory.add(inventory_piece)
	h.inventory.add(inventory_piece.clone())
	h.equipment.slots[slots[1]] = _piece(&"dragonforge", slots[1])
	var tempo := TempoData.new()
	tempo.equipment.slots[slots[2]] = _piece(&"dragonforge", slots[2])
	h.tempos.append(tempo)
	var hall := TempoData.new()
	hall.equipment.slots[slots[3]] = _piece(&"dragonforge", slots[3])
	h.spirit_hall.append(hall)
	h.equipment.recovered_items.append(_piece(&"dragonforge", slots[4]))
	var vault := [_piece(&"dragonforge", slots[5]), inventory_piece]
	var owned := BossSets.owned_pieces(h, vault)
	eq(owned.size(), 6, "six unique IDs across current ownership; duplicate copies add no weight")
	for i in 6:
		ok(owned.has(BossSets.piece_id(&"dragonforge", slots[i])), "all ownership sources recognized")
	done()

func test_weighted_collection_stays_random_and_missing_pieces_are_favored() -> void:
	var h := _hero(&"knight")
	var target_set := &"truth_of_raikuru" # Cross-class collection must still receive its ownership boost.
	var sd := DB.item_set(target_set)
	var owned: Array = []
	for id in sd.pieces.slice(0, 6):
		owned.append(DB.make_item(id, BH.Rarity.MASTER, 32, 11))
	var owned_ids := BossSets.owned_pieces(h, owned)
	near(BossSets.set_weight(BossSets.row(target_set), {}, &"knight"), 1.0, 0.001, "cross-class empty set keeps a nonzero chance")
	near(BossSets.set_weight(BossSets.row(target_set), owned_ids, &"knight"), 4.0, 0.001, "partially owned cross-class set is four times as likely")
	near(BossSets.set_weight(BossSets.row(&"dragonforge"), {}, &"knight"), 2.0, 0.001, "class affinity doubles chance")
	var r := rng(303015)
	var e := _enemy(30)
	var totals := {}
	var missing := 0
	var duplicate := 0
	for i in 10000:
		var it := BossSets.roll(e, h, r, owned)
		totals[it.base.set_id] = int(totals.get(it.base.set_id, 0)) + 1
		if it.base.set_id == target_set:
			if owned_ids.has(it.base.id):
				duplicate += 1
			else:
				missing += 1
	eq(totals.size(), 15, "all 15 random sets still appear for the same hero")
	ok(totals[target_set] > totals[&"wailing_mistress"] * 2.8, "ownership materially increases actual follow-up drops")
	ok(totals[&"dragonforge"] > totals[&"wailing_mistress"] * 1.4, "class affinity is measurable without excluding other sets")
	ok(missing > duplicate * 4.5 and missing < duplicate * 8.0, "six missing pieces outweigh six owned pieces by approximately 6x")
	ok(duplicate > 0, "ownership weighting never becomes guaranteed duplicate protection")
	print("BOSS_SET_WEIGHTS seed=303015 samples=10000 sets=%s target_missing=%d target_owned=%d" % [JSON.stringify(totals), missing, duplicate])
	e.free()
	done()

func test_boss_items_do_not_leak_into_generic_rewards_shops_or_crafting() -> void:
	var r := rng(6543)
	var h := _hero()
	for i in 300:
		for want_set in [false, true]:
			var special := ItemGenerator.random_special(r, 65, want_set)
			ok(special == null or not special.boss_exclusive, "generic special pool excludes boss pieces")
		var normal := ItemGenerator.random_base(r, 65)
		ok(normal == null or not normal.boss_exclusive, "generic equipment pool excludes boss pieces")
	for i in 40:
		for item: ItemInstance in ItemGenerator.relic_items(2, 60, r):
			ok(not item.base.boss_exclusive, "relic caches cannot create boss pieces")
	for shop_def: ShopDef in DB.shops.values():
		var shop := Shop.new()
		shop.def = shop_def
		shop.generate(h)
		for stock in shop.stock:
			ok(not stock.item.base.boss_exclusive, "merchant generation excludes boss pieces")
	var recipe := {"variants": [{"categories": BH.CATEGORY_SLOTS.keys()}]}
	for i in 100:
		var base := Crafting.pick_base(h, recipe, 0, r)
		ok(base == null or not base.boss_exclusive, "crafting excludes boss pieces")
	done()
