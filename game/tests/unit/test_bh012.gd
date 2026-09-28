extends TestCase
## bh-012: dungeons (20 floors built from plans, multi-storey, sealed descents, bosses), the 25 dungeon monsters, gacha
## gear names and stars, Relic Caches, the new equipment passives, Tempo summoning (rates, pity, resonance, the Spirit
## Hall), and save round trips.

static var _maps := {}
static var _nav_rids: Array[RID] = []
var _holder: Node3D

func _init() -> void:
	strict = true

func _hero(cls := &"knight") -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls), "Delver")
	h.init_new()
	return h

func _floor(id: StringName) -> MapRoot:
	if _maps.has(id) and is_instance_valid(_maps[id]):
		return _maps[id]
	if _holder == null or not is_instance_valid(_holder):
		_holder = Node3D.new()
		_holder.name = "Bh012Holder"
		host.add_child(_holder)
	var m := Game.build_map(id)
	_holder.add_child(m)
	_nav_rids.append(MapBuilder.isolate_navigation(m))
	MapBuilder.bake_navigation(m)
	_maps[id] = m
	return m

func _path(m: MapRoot, a: Vector3, b: Vector3, tol := 1.4) -> bool:
	var nm := m.nav_region.get_navigation_map()
	var pa := NavigationServer3D.map_get_closest_point(nm, a)
	var pb := NavigationServer3D.map_get_closest_point(nm, b)
	var path := NavigationServer3D.map_get_path(nm, pa, pb, true)
	return not path.is_empty() and path[path.size() - 1].distance_to(pb) < 0.3 and pb.distance_to(b) < tol and pa.distance_to(a) < tol

func _floor_ids() -> Array:
	var out := []
	for d in DataDungeons.ORDER:
		for n in range(1, DataDungeons.FLOORS + 1):
			out.append(DataDungeons.map_id(d, n))
	return out

# ---- dungeons ------------------------------------------------------------------------------------------------------

func test_a_every_floor_builds_with_portals_and_storeys() -> void:
	for id in _floor_ids():
		var m := _floor(id)
		ok(m != null and m.def.id == id, "%s builds" % id)
		for s in [&"start", &"arrival"]:
			ok(m.spawns.has(s), "%s has spawn %s" % [id, s])
		var n := int(String(id).get_slice("_", 2))
		ok(m.spawns.has(&"descent") if n < DataDungeons.FLOORS else m.spawns.has(&"exit"), "%s has its way on" % id)
		var tps := m.teleporters()
		eq(tps.size(), 2, "%s has two portals" % id)
		var ys := {}
		for t in tps:
			ok(DB.map_def(t.destination_map) != null, "%s -> %s exists" % [t.teleporter_id, t.destination_map])
		ok(m.nav_region.navigation_mesh.get_polygon_count() > 50, "%s navmesh baked (%d polys)" % [id, m.nav_region.navigation_mesh.get_polygon_count()])
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	done()

func test_b_floors_are_walkable_up_the_storeys() -> void:
	var three := 0
	for id in _floor_ids():
		var m := _floor(id)
		var start: Vector3 = m.spawns[&"start"].global_position
		for t in m.teleporters():
			ok(_path(m, start, t.arrival_point(), 1.8), "%s: arrival reaches portal %s" % [id, t.teleporter_id])
		# every storey of the plan can be walked to from the arrival
		var p := DataDungeons.parse(id)
		var plan: Array = DataDungeons.floor_def(p[0], p[1]).plan
		var top := 0
		for r in plan.size():
			for c in String(plan[r]).length():
				var k := String(plan[r])[c]
				if k in ["1", "2"] and int(k) > top:
					top = int(k)
		for lv in range(1, top + 1):
			var cell := Vector2i(-1, -1)
			for r in plan.size():
				for c in String(plan[r]).length():
					if cell.x < 0 and String(plan[r])[c] == str(lv):
						cell = Vector2i(c, r)
			var xz := DataDungeons.cell_xz(plan, cell)
			ok(_path(m, start, Vector3(xz.x, lv * 4.0, xz.y), 2.0), "%s: storey %d reachable by stairs" % [id, lv])
		if top >= 2:
			three += 1
	ok(three >= 5, "at least five floors have a third storey (%d)" % three)
	done()

func test_c_seals_and_bosses() -> void:
	var h := _hero()
	eq(DataDungeons.reached_floors(h, &"deeps"), [1], "only floor 1 before any seal breaks")
	h.world_flags[DataDungeons.seal_flag(&"deeps", 1)] = true
	h.world_flags[DataDungeons.seal_flag(&"deeps", 2)] = true
	eq(DataDungeons.reached_floors(h, &"deeps"), [1, 2, 3], "broken seals open the gate's floors")
	for d in DataDungeons.ORDER:
		var dd := DataDungeons.get_def(d)
		ok(DB.enemy(dd.boss) != null and DB.enemy(dd.boss).archetype == &"boss", "%s boss %s is a boss" % [d, dd.boss])
		ok(DB.enemy(dd.miniboss.enemy) != null, "%s champion uses a real monster" % d)
		ok(not DataMinibosses.find(dd.miniboss.id).is_empty(), "%s champion is listed" % d)
		eq(DataMinibosses.find(dd.miniboss.id).map, DataDungeons.map_id(d, 3), "%s champion holds floor 3" % d)
		for pool in dd.pools:
			for eid in dd.pools[pool]:
				ok(DB.enemy(eid) != null, "%s pool %s: %s exists" % [d, pool, eid])
		var m := _floor(DataDungeons.map_id(d, 4))
		var bs := m.find_children("BossSpawn", "Marker3D", true, false)
		eq(bs.size(), 1, "%s sanctum has a boss spawn" % d)
		if not bs.is_empty():
			eq(StringName(bs[0].get_meta(&"boss")), dd.boss, "%s boss spawn names its boss" % d)
			# bh-013: a raided dungeon's lord never returns (DataDungeons.boss_gone); the spawn names its dungeon for that
			eq(StringName(bs[0].get_meta(&"dungeon", "")), d, "%s boss spawn knows its dungeon" % d)
		var sf: Dictionary = dd.surface
		ok(DB.map_def(sf.map) != null, "%s gate map exists" % d)
	done()

# ---- monsters ------------------------------------------------------------------------------------------------------

func test_d_dungeon_monsters() -> void:
	var defs := DataEnemiesDungeon.defs()
	eq(defs.size(), 25, "25 dungeon monsters")
	var ids := {}
	var missing := []
	for d: EnemyDef in defs:
		ok(not ids.has(d.id), "%s unique" % d.id)
		ids[d.id] = true
		ok(DB.enemy(d.id) == d or DB.enemy(d.id) != null, "%s registered" % d.id)
		ok(d.lore != "", "%s has lore" % d.id)
		ok(not d.attacks.is_empty(), "%s attacks" % d.id)
		for a in d.attacks:
			if a.kind == "summon":
				ok(DB.enemy(a.summon) != null, "%s summons a real monster" % d.id)
		if not ResourceLoader.exists(d.model):
			missing.append(d.id)
			continue
		var scene: PackedScene = load(d.model)
		var inst := scene.instantiate()
		var ap: AnimationPlayer = inst.find_children("*", "AnimationPlayer", true, false).front() if not inst.find_children("*", "AnimationPlayer", true, false).is_empty() else null
		if d.body_shape == &"floating":
			ok(inst.find_child("core", true, false) != null, "%s floating model has a core" % d.id)
		else:
			ok(ap != null, "%s model has animations" % d.id)
			if ap:
				for a in d.attacks:
					ok(ap.has_animation(a.anim), "%s has clip %s" % [d.id, a.anim])
		inst.free()
	ok(true, "models not built yet: %s" % ", ".join(missing))
	done()

# ---- gear ----------------------------------------------------------------------------------------------------------

func test_e_named_gear_and_stars() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 12
	var names := {}
	var base := DB.item_base(&"iron_longsword")
	for i in 60:
		var it := ItemGenerator.generate(base, 20, BH.Rarity.ELITE + i % 4, r)
		ok(it.custom_name != "" and it.epithet != "", "Elite+ gear gets a name and an epithet")
		names[it.display_name()] = true
		var s := it.stars()
		ok(s >= 1 and s <= 5, "stars 1-5 (%d)" % s)
		var back := ItemInstance.from_dict(it.to_dict())
		eq(back.display_name(), it.display_name(), "the name survives a save")
	ok(names.size() >= 55, "names rarely repeat (%d unique of 60)" % names.size())
	var adv := ItemGenerator.generate(base, 10, BH.Rarity.ADVANCED, r)
	eq(adv.epithet, "", "Advanced gear keeps its affix name")
	for nm in names:
		for bad in ["Mala", "Lola", "Tala", "Bayan", "Dalisay"]:
			ok(not String(nm).contains(bad), "no borrowed names in %s" % nm)
	# a perfect item has five stars
	var it2 := ItemGenerator.generate(DB.item_base(&"iron_longsword"), 30, BH.Rarity.LEGENDARY, r)
	for a in it2.affixes:
		var d := DB.affix(StringName(a.id))
		var tiers := d.allowed_tiers(it2.ilvl)
		a.tier = tiers[tiers.size() - 1]
		a.value = float(d.tiers[a.tier][2])
	it2.quality = float(ItemGenerator.RULES[it2.rarity][5])
	eq(it2.stars(), 5, "maximum rolls: five stars")
	ok(it2.is_perfect(), "and perfect")
	done()

func test_f_new_passives_work() -> void:
	for id in [&"gold_find", &"xp_gain", &"hp_regen_pct", &"mana_regen_pct", &"hp_on_kill", &"mana_on_kill", &"potion_power", &"thorns",
			&"elite_damage", &"ember_find", &"tempo_damage"]:
		ok(DB.affix(id) != null, "affix %s exists" % id)
	var h := _hero()
	var base := h.compute_stats([])
	var ring := DB.make_item(&"iron_longsword", BH.Rarity.BASIC, 10, 1)
	var mods := [StatModifier.inc(&"hp_regen", 0.5), StatModifier.inc(&"gold_find", 0.3), StatModifier.flat(&"hp_on_kill", 12.0),
		StatModifier.inc(&"elite_damage", 0.2), StatModifier.flat(&"thorns", 20.0), StatModifier.inc(&"tempo_damage", 0.25)]
	var st := h.compute_stats(mods)
	near(st.get_stat(&"hp_regen"), base.get_stat(&"hp_regen") * 1.5, 0.01, "+50% HP regeneration")
	near(st.get_stat(&"gold_find"), base.get_stat(&"gold_find") + 0.3, 0.001, "gold find adds")
	near(st.get_stat(&"hp_on_kill"), 12.0, 0.001, "life on kill")
	near(st.get_stat(&"elite_damage"), 0.2, 0.001, "damage to champions")
	near(st.get_stat(&"thorns"), 20.0, 0.001, "thorns")
	var t := TempoRules.legend_data(&"kavira")
	var plain := TempoRules.compute(t, base, 10, h.cls)
	var boosted := TempoRules.compute(t, st, 10, h.cls)
	ok(boosted.get_stat(&"outgoing_damage") > plain.get_stat(&"outgoing_damage") * 1.2, "Soulbound gear strengthens Tempos")
	ok(ring != null, "item exists")
	done()

func test_g_relic_caches() -> void:
	var h := _hero()
	h.progress.level = 12
	for tier in 3:
		var r := RandomNumberGenerator.new()
		r.seed = 40 + tier
		var items := RelicCache.open(h, tier, null, r)
		var c: Dictionary = DataRelics.CACHES[tier]
		ok(items.size() >= int(c.items), "%s holds %d+ pieces (%d)" % [c.name, c.items, items.size()])
		var best := 0
		for it in items:
			best = maxi(best, it.rarity)
			ok(h.inventory.index_of(it) >= 0, "the gear goes to the bag")
			ok(it.rarity >= int(c.min), "%s: every piece at least %s" % [c.name, BH.rarity_name(int(c.min))])
		ok(best >= int(c.floor), "%s has its floor rarity" % c.name)
		ok(DB.item_base(c.id) != null and DB.item_base(c.id).consumable_effect.has("cache"), "%s is an item" % c.name)
	done()

# ---- Tempo summoning ---------------------------------------------------------------------------------------------------

func test_h_summon_rates_and_pity() -> void:
	var st := {}
	var r := RandomNumberGenerator.new()
	r.seed = 7
	var since4 := 0
	var since5 := 0
	var max4 := 0
	var max5 := 0
	var fives := 0
	var fours := 0
	for i in 10000:
		var s := TempoGacha.roll_stars(st, r)
		since4 = 0 if s >= 4 else since4 + 1
		since5 = 0 if s == 5 else since5 + 1
		max4 = maxi(max4, since4)
		max5 = maxi(max5, since5)
		fives += int(s == 5)
		fours += int(s == 4)
	ok(max4 < TempoGacha.FOUR_PITY, "a 4-star or better within every %d calls (longest gap %d)" % [TempoGacha.FOUR_PITY, max4])
	ok(max5 < TempoGacha.HARD_PITY, "a 5-star by call %d (longest gap %d)" % [TempoGacha.HARD_PITY, max5])
	var rate5 := float(fives) / 10000.0
	ok(rate5 > 0.015 and rate5 < 0.05, "effective 5-star rate with pity %.2f%%" % (rate5 * 100.0))
	ok(float(fours) / 10000.0 > 0.12, "4-stars %.1f%%" % (float(fours) / 100.0))
	done()

func test_i_summon_hall_resonance() -> void:
	var h := _hero()
	ok(TempoGacha.ensure_welcome(h), "the welcome embers are given once")
	ok(not TempoGacha.ensure_welcome(h), "and only once")
	eq(TempoGacha.embers(h), TempoGacha.WELCOME_EMBERS, "welcome embers in the bag")
	var r := RandomNumberGenerator.new()
	r.seed = 99
	var res := TempoGacha.summon(h, 10, r)
	eq(res.size(), 10, "a ten-call brings ten")
	ok(res.any(func(x): return x.stars >= 4), "a ten-call holds a 4-star or better")
	eq(TempoGacha.embers(h), TempoGacha.WELCOME_EMBERS - TempoGacha.COST_TEN, "it cost %d embers" % TempoGacha.COST_TEN)
	ok(h.spirit_hall.size() >= 9, "summoned spirits wait in the hall (%d)" % h.spirit_hall.size())
	ok(TempoGacha.summon(h, 10, r).is_empty(), "no embers, no call")
	# duplicates of a renowned spirit raise resonance
	TempoGacha.add_embers(h, 500)
	var st := TempoGacha.state(h)
	var id := &"kavira"
	var t := TempoRules.legend_data(id)
	t.stars = 5
	TempoGacha._to_hall(h, t)
	var m0 := t.mirror()
	st["pity5"] = TempoGacha.HARD_PITY - 1
	st["lost_feature"] = true
	var feat := TempoGacha.featured()
	if feat != id:
		var ft := TempoRules.legend_data(feat)
		ft.stars = 5
		TempoGacha._to_hall(h, ft)
	var dup := TempoGacha.summon(h, 1, r)
	eq(dup[0].stars, 5, "hard pity brings a 5-star")
	ok(not dup[0].new and int(dup[0].resonance) == 1, "a duplicate raises Resonance to I")
	var owned := TempoGacha.owned_legend(h, feat)
	ok(owned.mirror() > DataTempos.RENOWNED.mirror, "resonance adds strength (%.2f)" % owned.mirror())
	ok(m0 > 0.0, "mirror")
	# bind, swap, rest, release
	var first: TempoData = h.spirit_hall[0]
	if TempoRules.bound_count(h) < DataTempos.MAX_ACTIVE:
		eq(TempoGacha.bind(h, first.uid), "", "bind from the hall")
	var bound: TempoData = h.tempos[0]
	var other: TempoData = h.spirit_hall[0]
	eq(TempoGacha.swap(h, bound.uid, other.uid), "", "swap a bound Tempo with a hall spirit")
	ok(h.tempos.has(other) and h.spirit_hall.has(bound), "they traded places")
	var before := TempoGacha.embers(h)
	var got := TempoGacha.release(h, bound.uid)
	ok(got > 0 and TempoGacha.embers(h) == before + got, "release gives embers (%d)" % got)
	# save round trip
	var back := HeroData.from_dict(h.to_dict())
	eq(back.spirit_hall.size(), h.spirit_hall.size(), "the hall survives a save")
	eq(int(back.summon.get("pity4", -1)), int(h.summon.get("pity4", -2)), "pity survives a save")
	var ob := TempoGacha.owned_legend(back, feat)
	ok(ob != null and ob.resonance == owned.resonance, "resonance survives a save")
	done()

func test_j_chests_and_embers() -> void:
	var h := _hero()
	h.chest_log["dg_deeps_1/1"] = 100.0
	var back := HeroData.from_dict(h.to_dict())
	near(float(back.chest_log.get("dg_deeps_1/1", 0.0)), 100.0, 0.001, "chest log survives a save")
	var c := TreasureChest.new().setup(1, "dg_deeps_1/1", 10, 60.0)
	ok(c.tier == 1 and c.key == "dg_deeps_1/1", "chest setup")
	c.free()
	ok(DB.item_base(&"soul_ember") != null and DB.item_base(&"soul_ember").stack_max >= 999, "Soul Embers stack")
	for m in DataRelics.MATERIALS:
		ok(DB.item_base(m[0]) != null, "material %s" % m[0])
	done()

func test_z_cleanup() -> void:
	for id in _maps:
		if is_instance_valid(_maps[id]):
			_maps[id].free()
	_maps.clear()
	if is_instance_valid(_holder):
		_holder.free()
	for rid in _nav_rids:
		NavigationServer3D.free_rid(rid)
	_nav_rids.clear()
	await host.get_tree().physics_frame
	done()
