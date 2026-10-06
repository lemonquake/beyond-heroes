extends TestCase
## bh-039: the Fabled Arms (DataFabled: 54 named weapons, Legendary .. Primordial, models, icons, signature strikes) and
## the rebuilt Item Summoner (a forced rarity is exactly that rarity; filters; chosen enchantments and powers).

func test_fifty_four_fabled_arms() -> void:
	var ids := DataFabled.ids()
	ok(ids.size() >= 50, "at least fifty Fabled arms (%d)" % ids.size())
	var per := {}
	var names := {}
	for id in ids:
		var b := DB.item_base(id)
		ok(b != null, "%s is a base" % id)
		if b == null:
			continue
		var r := DataFabled.row(id)
		per[b.fixed_rarity] = int(per.get(b.fixed_rarity, 0)) + 1
		ok(b.fixed_rarity >= BH.Rarity.LEGENDARY, "%s is Legendary or better" % id)
		ok(not names.has(b.unique_name), "%s has a name of its own" % b.unique_name)
		names[b.unique_name] = true
		ok(b.is_weapon() and DB.weapon_type(b.weapon_type) != null, "%s is a weapon of a known type" % id)
		ok(ResourceLoader.exists(b.model), "%s has its model" % id)
		ok(ResourceLoader.exists(b.icon), "%s has its icon" % id)
		ok(FabledProcs.KINDS.has(StringName(r[5])), "%s strike %s exists" % [id, r[5]])
		ok(DB.power(DataFabled.sig_power_id(id)) != null, "%s has its signature power" % id)
		var it := DB.make_item(id, BH.Rarity.COMMON, 60, 7)
		eq(it.rarity, b.fixed_rarity, "%s drops at its own rarity" % id)
		ok(it.powers.has(String(DataFabled.sig_power_id(id))), "%s carries its signature" % id)
	for r in [BH.Rarity.LEGENDARY, BH.Rarity.AETHER, BH.Rarity.COSMIC, BH.Rarity.DIVINE, BH.Rarity.ETERNAL, BH.Rarity.PRIMORDIAL]:
		ok(int(per.get(r, 0)) >= 8, "%s has at least eight arms" % BH.rarity_name(r))
	# Divine and Primordial strikes are each their own
	var seen := {}
	for row in DataFabled.ROWS:
		if int(row[2]) in [BH.Rarity.DIVINE, BH.Rarity.PRIMORDIAL]:
			ok(not seen.has(row[5]), "%s has a strike no other Divine/Primordial arm shares" % row[1])
			seen[row[5]] = true
	done()

func test_forced_rarity_is_exact() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var b := DB.item_base(&"iron_longsword")
	var normal := ItemGenerator.generate(b, 60, BH.Rarity.PRIMORDIAL, rng)
	eq(normal.rarity, BH.Rarity.AETHER, "a drop never makes a Primordial plain sword")
	var forced := ItemGenerator.generate(b, 60, BH.Rarity.PRIMORDIAL, rng, true)
	eq(forced.rarity, BH.Rarity.PRIMORDIAL, "the summoner's Primordial sword is Primordial")
	ok(forced.powers.has("asc_eruption"), "with the Primordial signature power")
	var fab := ItemGenerator.generate(DB.item_base(&"fa_genesis"), 60, BH.Rarity.COSMIC, rng, true)
	eq(fab.rarity, BH.Rarity.COSMIC, "a fixed-rarity base takes the forced rarity too")
	done()

func test_summoner_filters_and_forge() -> void:
	var old := Game.hero
	Game.hero = Game.new_hero(&"knight", "Forge")
	Game.hero.set_tier(1)
	Game.hero.debug_unlocked = true
	var vp := SubViewport.new()
	vp.size = Vector2i(1920, 1080)
	host.add_child(vp)
	var w := DebugWindow.new()
	w.theme = UITheme.theme()
	vp.add_child(w)
	w.open()
	w.show_page("items")
	await host.get_tree().process_frame
	w._set_chip("wtype", "greataxe")
	w._set_chip("category", "weapon")
	w._fill_bases()
	ok(not w._base_ids.is_empty(), "great axes are listed")
	ok(w._base_ids.all(func(id): return DB.item_base(id).weapon_type == &"greataxe"), "only great axes")
	w._set_chip("source", "fabled")
	w._fill_bases()
	ok(w._base_ids.all(func(id): return DataFabled.is_fabled(DB.item_base(id))), "only Fabled great axes")
	w._clear_filters()
	ok(w._select_base(&"iron_longsword"), "the sword is found")
	w._set_rarity(BH.Rarity.PRIMORDIAL)
	w._affix_opts[0].selected = 1
	w._reroll(false)
	var chosen: StringName = w._affix_ids[1]
	ok(w._preview.rarity == BH.Rarity.PRIMORDIAL, "the preview is Primordial")
	ok(w._preview.affixes.any(func(a): return StringName(a.id) == chosen), "the chosen enchantment is on it")
	w._unbound.button_pressed = true
	w._equip_now.button_pressed = true
	w._summon_item()
	var main := Game.hero.equipment.get_item(&"main_weapon")
	ok(main != null and main.base.id == &"iron_longsword" and main.rarity == BH.Rarity.PRIMORDIAL and main.unbound, "summoned, Unbound and equipped")
	w._equip_now.button_pressed = false
	w._set_rarity(BH.Rarity.DIVINE)
	var n := Game.hero.inventory.free_cells()
	w._summon_fabled(true)
	eq(n - Game.hero.inventory.free_cells(), DataFabled.ids_of(BH.Rarity.DIVINE).size(), "every Divine arm summoned")
	w.queue_free()
	vp.queue_free()
	Game.hero = old
	done()
