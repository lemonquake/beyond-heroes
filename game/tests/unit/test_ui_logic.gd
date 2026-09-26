extends TestCase
## Logic behind the interface: item comparison (uses the real stat calculator, never mutates the hero), settings
## persistence and key rebinding, respec pricing, objectives, save v3 round trip through SaveSystem.

func _init() -> void:
	strict = true

func _hero(cls := &"knight") -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls), "UiTest")
	h.init_new()
	return h

func test_compare_matches_real_equip() -> void:
	var h := _hero()
	h.progress.add_xp(XpCurve.total_xp_for_level(10))
	var rng := rng(11)
	var checked := 0
	for i in 40:
		var b := ItemGenerator.random_base(rng, 10, [&"weapon", &"helm", &"armor", &"gloves", &"boots", &"accessory"], &"knight")
		var it := ItemGenerator.generate(b, 10, rng.randi_range(1, 7), rng)
		if h.equipment.check(it, h.equipment.auto_slot(it), 99, {&"str": 999, &"agi": 999, &"int": 999, &"wis": 999, &"spi": 999, &"dex": 999}) != "":
			continue
		var before := JSON.stringify(h.to_dict())
		var pv := ItemCompare.preview(h, it)
		eq(JSON.stringify(h.to_dict()), before, "preview never changes the hero")
		# equip for real on a copy and compare with the preview's "after"
		var copy := HeroData.from_dict(JSON.parse_string(before))
		copy.progress.allocated = {&"str": 300, &"agi": 300, &"int": 300, &"wis": 300, &"spi": 300, &"dex": 300}
		var h2 := HeroData.from_dict(JSON.parse_string(before))
		var slot := h2.equipment.auto_slot(it)
		var c2 := it.clone()
		h2.equipment.slots[slot] = c2
		if slot == &"main_weapon":
			var wt := h2.equipment.weapon_type_of(c2)
			var sub: ItemInstance = h2.equipment.slots[&"sub_weapon"]
			if sub != null and wt != null and (wt.two_handed or (sub.base.is_weapon() and not wt.dual_wieldable)):
				h2.equipment.slots[&"sub_weapon"] = null
		var real := h2.compute_stats()
		for k in [&"max_hp", &"defense", &"crit_chance", &"weapon_min", &"weapon_max", &"attack_speed", &"max_mana"]:
			near(pv.after.get_stat(k), real.get_stat(k), 0.0001, "%s preview = real (%s)" % [k, it.display_name()])
		checked += 1
	ok(checked >= 10, "compared %d items" % checked)
	done()

func test_compare_rows_only_changes() -> void:
	var h := _hero()
	var same := h.equipment.get_item(&"main_weapon").clone()
	eq(ItemCompare.preview(h, same).rows.size(), 0, "identical item: no rows")
	var better := DB.make_item(h.equipment.get_item(&"main_weapon").base.id, BH.Rarity.ELITE, 10, 5)
	var pv := ItemCompare.preview(h, better)
	ok(pv.rows.size() > 0, "a different item shows changes")
	for r in pv.rows:
		ok(absf(r.after - r.before) >= 0.0005, "row %s really changed" % r.name)
		eq(r.better, r.after > r.before, "%s better flag" % r.name)
	done()

func test_settings_round_trip_and_rebind() -> void:
	var saved := Settings.to_dict()
	Settings.from_dict({"master_volume": 0.3, "shadows_quality": 1, "auto_loot_mode": 3, "window_mode": 0, "render_scale": 0.75})
	eq(Settings.master_volume, 0.3, "volume applied")
	eq(Settings.auto_loot_rarity, BH.Rarity.BASIC, "auto loot mode 3 = Basic and above")
	ok(Settings.auto_loot, "auto loot on")
	var d := Settings.to_dict()
	Settings.from_dict(saved)
	Settings.from_dict(d)
	eq(Settings.render_scale, 0.75, "round trip")
	# legacy save with a boolean fullscreen
	Settings.from_dict({"fullscreen": true})
	eq(Settings.window_mode, 1, "legacy fullscreen -> borderless")
	# rebinding moves a key and unbinds its previous owner
	var k := InputEventKey.new()
	k.physical_keycode = KEY_G
	var stolen := Settings.rebind(&"interact", k)
	eq(Settings.binding_text(&"interact"), "G", "interact now on G")
	eq(stolen, &"", "G was free")
	var k2 := InputEventKey.new()
	k2.physical_keycode = KEY_G
	var stolen2 := Settings.rebind(&"guard", k2)
	eq(stolen2, &"interact", "binding G to guard takes it from interact")
	eq(Settings.binding_text(&"interact"), "", "interact unbound")
	# descriptor round trip
	var desc := Settings.event_to_desc(k)
	ok(Settings.event_to_desc(Settings.desc_to_event(desc)) == desc, "event descriptor round trip")
	Settings.reset_bindings()
	eq(Settings.binding_text(&"interact"), "R", "defaults restored")
	eq(Settings.binding_text(&"guard"), "F", "guard default restored")
	Settings.from_dict(saved)
	Settings.save_file()
	done()

func test_respec_cost_and_objectives() -> void:
	ok(NpcServices.respec_cost(1) >= 10 and NpcServices.respec_cost(1) <= 60, "cheap at level 1 (%d)" % NpcServices.respec_cost(1))
	ok(NpcServices.respec_cost(30) > NpcServices.respec_cost(10) * 3, "grows with level")
	var h := _hero()
	eq(Objectives.current(h).id, "forest", "first objective")
	h.world_flags[&"catacombs_ritual_seen"] = true
	eq(Objectives.current(h).id, "temple", "second")
	h.world_flags[&"temple_seal_broken"] = true
	eq(Objectives.current(h).id, "warden", "third")
	h.world_flags[&"boss_warden_defeated"] = true
	eq(Objectives.current(h).id, "after", "return to Maelis")
	h.mark_dialogue_visited(&"maelis", "warden_fallen")
	ok(Objectives.current(h).is_empty(), "all done")
	done()

func test_save_slot_round_trip() -> void:
	var slot := 97
	var h := _hero(&"mage")
	h.progress.add_xp(3456)
	h.world_flags[&"catacombs_ritual_seen"] = true
	h.mark_dialogue_visited(&"tovin", "first")
	h.add_relationship(&"tovin", 12)
	var shop := Shop.open(DB.shop(&"seris_arcana"), h)
	shop.sell(h.inventory.cells[0], h)
	h.skill_bar[3] = &"firebolt"
	h.skill_bar[0] = &""
	h.play_time = 1234.5
	ok(SaveSystem.save_hero(h, slot), "saved")
	var loaded := SaveSystem.load_hero(slot)
	ok(loaded != null, "loaded")
	eq(JSON.stringify(loaded.to_dict()), JSON.stringify(h.to_dict()), "exact round trip through the save file")
	var sum := SaveSystem.slot_summary(slot)
	eq(sum.class, "mage", "summary class")
	eq(int(sum.level), h.progress.level, "summary level")
	SaveSystem.delete_slot(slot)
	ok(SaveSystem.slot_summary(slot).is_empty(), "deleted")
	done()
