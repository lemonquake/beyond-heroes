extends TestCase
## bh-028: Evasion consistency (graze, evade-triggered passives), +50 HP per level, level 40+ hexes, celestial orbs and
## the special dungeons behind Kethrax. Plan and findings: docs/PLAN_bh-028.md.

func _init() -> void:
	strict = true

# ---- Evasion ------------------------------------------------------------------------------------------------------

func test_graze_odds_and_caps() -> void:
	eq(DamagePipeline.evade_chance(1000.0, 10.0), DamagePipeline.EVADE_CAP, "direct hits cap at 65%")
	eq(DamagePipeline.evade_chance(1000.0, 10.0, true), DamagePipeline.GRAZE_CAP, "area hits cap at 45%")
	near(DamagePipeline.evade_chance(100.0, 100.0, true), 100.0 / 500.0, 0.0001, "graze meets 4x the Accuracy")
	ok(DamagePipeline.evade_chance(400.0, 100.0, true) > DamagePipeline.evade_chance(200.0, 100.0, true),
		"Evasion past the direct cap still raises the graze chance")
	eq(DamagePipeline.evade_chance(0.0, 50.0, true), 0.0, "no Evasion, no graze")
	done()

func test_area_hits_can_be_grazed_in_the_pipeline() -> void:
	var cls := DB.class_def(&"ranger")
	var target := StatCalculator.compute(cls, 60, {&"agi": 400}, [], WeaponLoadout.new())
	var foe := EnemyStats.build(DB.enemy(&"hollow_soldier"), 60, {}, [])
	var random := rng(28)
	var grazed := 0
	for i in 2000:
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = foe
		req.target = target
		req.base_min = 50.0
		req.base_max = 50.0
		req.graze = true
		if DamagePipeline.compute(req, random).evaded:
			grazed += 1
	var expect := DamagePipeline.evade_chance(target.get_stat(&"evasion"), foe.get_stat(&"accuracy"), true)
	near(grazed / 2000.0, expect, 0.04, "area hits are grazed at the graze odds")
	ok(expect > 0.2, "an agile level-60 hero grazes area hits often (%.0f%%)" % (expect * 100.0))
	near(target.get_stat(&"graze_chance"), DamagePipeline.evade_chance(target.get_stat(&"evasion"), 30.0 + 4.0 * 59.0, true), 0.0001,
		"the character sheet shows the graze chance")
	done()

func test_monster_attacks_are_all_evadable_area_ones_as_graze() -> void:
	var e := Enemy.new().setup(DB.enemy(&"storm_herald"), 40)
	host.add_child(e)
	var direct := 0
	var area := 0
	for a in e.def.attacks:
		var req: DamageRequest = e._attack_request(a)
		ok(req.evadable, "%s can be evaded or grazed" % a.id)
		if a.kind in Enemy.DIRECT_KINDS:
			ok(not req.graze, "%s is an aimed blow" % a.id)
			direct += 1
		else:
			ok(req.graze, "%s (%s) is grazed" % [a.id, a.kind])
			area += 1
	ok(direct > 0 and area > 0, "the storm herald has both kinds")
	var ext_req: DamageRequest = load("res://src/actors/enemy/enemy_traits_ext.gd").new(e)._req(1.0, Elements.FIRE, 1.0, 2.0, "test")
	ok(ext_req.evadable and ext_req.graze, "trait blasts can be grazed too")
	var round_trip := NetCodec.decode_request(NetCodec.encode_request(ext_req))
	ok(round_trip.graze, "graze crosses the network")
	e.free()
	done()

func test_evading_passives_fire_on_evasion_rolls() -> void:
	var saved_hero := Game.hero
	Game.hero = Game.new_hero(&"ranger", "Evader")
	var p := Player.new()
	host.add_child(p)
	p.bind(Game.hero)
	p.stats.flags[&"evade_mana"] = 5.0
	p.mana = 0.0
	p._on_evaded(null)
	eq(p.mana, 5.0, "Second Nature restores Mana on an Evasion roll, not only on a dodge")
	p.stats.flags[&"evade_heal"] = 0.05
	p.hp = 10.0
	p._on_evaded(null)
	near(p.hp, 10.0 + p.max_hp() * 0.05, 0.01, "Moonveil heals on an Evasion roll")
	p.free()
	Game.hero = saved_hero
	done()

func test_hunter_focus_passives() -> void:
	var r := ClassResource.new(&"focus")
	r.value = 50.0
	r.tick(30.0, false, false)
	ok(r.value < 50.0, "Focus fades out of combat without Hunter's Calm")
	r.value = 50.0
	r.tick(30.0, false, true)
	eq(r.value, 50.0, "Hunter's Calm holds Focus")
	done()

# ---- +50 HP per level -------------------------------------------------------------------------------------------

func test_fifty_hp_per_level_for_every_save() -> void:
	var cls := DB.class_def(&"knight").duplicate() as ClassDef
	cls.class_modifiers = []
	cls.hp_per_level = 0.0
	cls.vitality = false
	var l1 := StatCalculator.compute(cls, 1, {}, [], WeaponLoadout.new()).get_stat(&"max_hp")
	var l40 := StatCalculator.compute(cls, 40, {}, [], WeaponLoadout.new()).get_stat(&"max_hp")
	eq(l40 - l1, 39 * 50.0, "39 level-ups give 1,950 bonus HP")
	var lines: PackedStringArray = StatCalculator.compute(cls, 40, {}, [], WeaponLoadout.new()).explain.get(&"max_hp", PackedStringArray())
	ok(Array(lines).any(func(l): return String(l).contains("Level-up bonus")), "the sheet explains the bonus")
	# an old save (written before bh-028, and before the survival rebalance) gets it on load
	var h := Game.new_hero(&"mage", "Old save")
	var data := h.to_dict()
	data.progress.erase("point_rules_version")
	data.progress.level = 40
	var loaded := HeroData.from_dict(data)
	var fresh := Game.new_hero(&"mage", "New save")
	fresh.progress.add_xp(XpCurve.total_xp_for_level(40))
	ok(loaded.compute_stats().get_stat(&"max_hp") >= 39 * 50.0, "the old hero has the bonus")
	var cls_m := DB.class_def(&"mage")
	var no_bonus := cls_m.base_hp + cls_m.hp_per_level * 39.0
	ok(fresh.compute_stats().get_stat(&"max_hp") > no_bonus + 39 * 50.0 - 1.0, "a new hero earns it by levelling")
	done()

# ---- Level 40+ hexes ------------------------------------------------------------------------------------------

func test_monsters_hex_from_level_forty() -> void:
	var def := DB.enemy(&"hollow_soldier")
	eq(DataEnemies.extra_attacks(def, 39).size(), 0, "no hex below level 40")
	var hex: Array = DataEnemies.extra_attacks(def, 40)
	eq(hex.size(), 1, "a level-40 monster can hex")
	var e := Enemy.new().setup(def, 45)
	ok(e.extra_attacks.any(func(a): return a.id == &"hex_frailty"), "the hex joins its attack choices")
	host.add_child(e)
	var req: DamageRequest = e._attack_request(hex[0])
	ok(req.graze and req.evadable, "the hex is an area hit: it can be grazed")
	ok(float(req.direct_status.get(&"hex_frailty", 0.0)) >= StatusRules.THRESHOLD, "one hit lays the hex")
	e.free()
	ok(DataEnemies.extra_attacks(DB.enemy(&"war_totem"), 60).is_empty() if DB.enemy(&"war_totem") else true, "harmless monsters do not hex")
	done()

func test_hex_lowers_resistances_and_evasion_for_five_seconds() -> void:
	var h := Game.new_hero(&"ranger", "Hexed")
	h.progress.add_xp(XpCurve.total_xp_for_level(60))
	h.progress.allocate(&"agi", 100)
	h.progress.allocate(&"wis", 100)
	var sc := StatusController.new()
	sc.status_res = 0.6
	var before := StatCalculator.compute(h.cls, 60, h.progress.base_attributes(), [], WeaponLoadout.new())
	sc.apply(&"hex_frailty")
	near(sc.remaining(&"hex_frailty"), 5.0, 0.001, "five seconds, whatever the Status Resistance")
	var after := StatCalculator.compute(h.cls, 60, h.progress.base_attributes(), sc.stat_modifiers(), WeaponLoadout.new())
	near(after.get_stat(&"evasion"), before.get_stat(&"evasion") * 0.6, 1.0, "40% less Evasion")
	near(after.get_stat(&"res_fire"), before.get_stat(&"res_fire") - 0.2, 0.0001, "20% lower elemental resistance")
	ok(after.get_stat(&"evade_chance") < before.get_stat(&"evade_chance") or before.get_stat(&"evade_chance") >= DamagePipeline.EVADE_CAP,
		"the evade chance drops or was capped")
	sc.tick(5.1)
	ok(not sc.has(&"hex_frailty"), "and it wears off")
	done()

# ---- Celestial orbs -----------------------------------------------------------------------------------------------

func test_celestial_orbs_exist_with_their_effects() -> void:
	for f in DataCrystals.CELESTIAL:
		for g in 4:
			var id := DataCrystals.id_of(f, g)
			var b := DB.item_base(id)
			ok(b != null, "%s exists" % id)
			if b == null:
				continue
			ok(ResourceLoader.exists(b.icon), "%s has its own icon" % id)
			ok(DataCrystals.price(id) > DataCrystals.price(DataCrystals.id_of(&"ember", g)), "%s is dearer than a common crystal" % id)
			ok(CrystalNames.SINGLE.has(f) and CrystalNames.EPITHET.has(f), "%s names its gear" % f)
	var stats_of := func(id: StringName, cat: StringName) -> Dictionary:
		var out := {}
		for m in DataCrystals.mods(id, cat):
			out[m.stat] = m.value
		return out
	var sora_w: Dictionary = stats_of.call(&"sora_orbital", &"weapon")
	ok(sora_w.get(&"accuracy", 0.0) > 0.0 and sora_w.get(&"impact_strength", 0.0) > 0.0, "Sora: Hit Rate and Knockback on weapons")
	ok(float(stats_of.call(&"sora_shard", &"armor").get(&"res_all", 0.0)) > 0.0, "Sora: resistance on armour")
	ok(float(stats_of.call(&"sora_shard", &"accessory").get(&"res_all", 0.0)) > 0.0, "Sora: resistance on accessories")
	ok(stats_of.call(&"luna_orbital", &"armor").has(&"flag_evade_heal"), "Luna: Moonveil on armour")
	ok(stats_of.call(&"sol_orbital", &"weapon").has(&"flag_crit_sunflare"), "Sol: Sunflare on weapons")
	ok(stats_of.call(&"airah_orbital", &"accessory").has(&"flag_dodge_haste"), "Airah: Tailwind on jewellery")
	eq(CrystalNames.suffix_for([&"sol_orbital", &"luna_orbital"]), "of the Eternal Eclipse Crown", "Sol + Luna name a piece")
	done()

func test_celestial_orbs_drop_from_level_forty_bosses() -> void:
	var r := rng(4028)
	var low := 0
	var high := 0
	var favoured := 0
	for i in 3000:
		if DataCrystals.is_celestial(DataCrystals.family_of(DataCrystals.roll_drop(r, 30, true))):
			low += 1
		if DataCrystals.is_celestial(DataCrystals.family_of(DataCrystals.roll_drop(r, 60, true))):
			high += 1
		var fav := DataCrystals.roll_drop(r, 90, true, &"luna")
		if DataCrystals.is_celestial(DataCrystals.family_of(fav)):
			ok(DataCrystals.family_of(fav) == &"luna", "a favoured dungeon rolls its own orb")
			favoured += 1
	eq(low, 0, "no celestial orb below level 40")
	ok(high > 150 and high < 350, "about 8%% of level-60 boss crystals are celestial (%d / 3000)" % high)
	ok(favoured > high, "a special dungeon favours its orb (%d)" % favoured)
	var stock := DataShops.crystal_stock([1, 10, 99, 99], 30)
	ok(stock.any(func(s): return s.base == &"sora_fragment" and s.level_min == 40), "specialists sell Sora Fragments from level 40")
	done()

# ---- Special dungeons ---------------------------------------------------------------------------------------------

func test_special_dungeons_data() -> void:
	# bh-042: the Abyss dungeons are special too (fixed levels, no growth) but have their own suite (test_bh042)
	var ids: Array = DataDungeons.order().filter(func(id): return DataDungeons.is_special(id) and not DataDungeons.is_zarael(id) and not DataDungeons.is_abyss(id))
	eq(ids.size(), 5, "five special dungeons")
	eq(DataDungeons.gates_on(&"sundered_reach").size(), 5, "all five gates stand on The Sundered Reach")
	var lords := {}
	for id in ids:
		var d := DataDungeons.get_def(id)
		var n := DataDungeons.floor_count(id)
		ok(n >= 10 and n <= 15, "%s has 10-15 floors (%d)" % [id, n])
		eq((d.levels as Array).size(), n, "%s has a level range per floor" % id)
		var prev := 0
		for lv in d.levels:
			ok(int(lv[0]) >= 80 and int(lv[1]) <= 120 and int(lv[0]) <= int(lv[1]), "%s floor levels within 80-120 (%s)" % [id, lv])
			ok(int(lv[0]) >= prev, "%s gets harder floor by floor" % id)
			prev = int(lv[0])
		eq(DataDungeons.tier(id), 6, "%s is tier 6" % id)
		eq(DataDungeons.tier_name(id), "Ascendant", "%s is Ascendant" % id)
		eq(DataDungeons.min_tier(id), 5, "%s asks for Class A" % id)
		ok(DataCrystals.is_celestial(StringName(d.orb)), "%s favours a celestial orb (%s)" % [id, d.orb])
		eq(DataDungeons.max_extra(id), 0, "%s grows no deeper floors" % id)
		ok(DB.map_def(DataDungeons.map_id(id, n)) != null, "%s sanctum is registered" % id)
		ok(DB.map_def(DataDungeons.map_id(id, n + 1)) == null, "%s has nothing below its sanctum" % id)
		var boss := DB.enemy(d.boss)
		ok(boss != null and boss.archetype == &"boss", "%s lord %s is a boss" % [id, d.boss])
		lords[d.boss] = true
		for key in ["miniboss", "usurper"]:
			ok(DB.enemy(d[key].enemy) != null, "%s %s uses a real monster" % [id, key])
			ok(not DataMinibosses.find(d[key].id).is_empty(), "%s %s is listed" % [id, key])
		for pool in d.pools:
			for eid in d.pools[pool]:
				ok(DB.enemy(eid) != null, "%s pool %s: %s exists" % [id, pool, eid])
		# no DungeonGrowth: a level-150 hero meets the authored levels and pools, and no extra floors
		var g := DungeonGrowth.profile(150)
		g.extra = DungeonGrowth.for_hero(null, id).extra
		eq(int(g.extra), 0, "%s: no extra floors" % id)
		eq(DungeonGrowth.levels(id, 1, g), Vector2i(d.levels[0][0], d.levels[0][1]), "%s keeps its authored levels" % id)
		eq(DungeonGrowth.pool(id, d.pools.a, g, 7), d.pools.a, "%s keeps its authored pool" % id)
		ok(not DataIsland.place(String(id)).is_empty(), "%s is on the Underground list" % id)
		ok(DataIsland.all_links().any(func(l): return l.id == "%s_gate" % id), "%s has a route from the Reach" % id)
	eq(lords.size(), 5, "five different lords")
	var seraphel := DB.enemy(&"seraphel")
	near(seraphel.hp, DB.enemy(&"prism_colossus").hp * DataEnemiesSpecial.HP, 0.01, "a lord is tougher than the boss it was cast from")
	var rift: Array = DataIsland.all_links().filter(func(l): return l.id == "sundered_rift")
	ok(rift.size() == 1 and rift[0].flag == "boss_kethrax_defeated", "the rift route opens with Kethrax's fall")
	done()

func _built(id: StringName, hero: HeroData) -> MapRoot:
	var prev := Game.hero
	Game.hero = hero
	var m := Game.build_map(id)
	host.add_child(m)
	Game.hero = prev
	return m

func test_the_reach_its_gates_and_the_rift() -> void:
	var h := Game.new_hero(&"knight", "Rift")
	var prev := Game.hero
	Game.hero = h
	# the rift on the Sanctuary Terrace stays shut until Kethrax falls (read live, so old saves open at once)
	var town := _built(&"sanctuary", h)
	var rift := town.teleporter(&"sanctuary_rift")
	ok(rift != null and rift.destination_map == &"sundered_reach", "a rift on the terrace leads to The Sundered Reach")
	if rift:
		ok(rift.is_locked(), "sealed before Kethrax falls")
		h.world_flags[&"boss_kethrax_defeated"] = true
		ok(not rift.is_locked(), "open once he has")
	town.free()
	var reach := _built(&"sundered_reach", h)
	ok(reach.spawns.has(&"arrival"), "the Reach has its arrival")
	var back := reach.teleporter(&"reach_return")
	ok(back != null and back.destination_map == &"sanctuary" and not back.is_locked(), "a dais leads home")
	var gates := reach.find_children("Teleporter_*", "Teleporter", true, false).filter(func(t): return t.dungeon_gate != &"")
	eq(gates.size(), 5, "five dungeon gates on the Reach")
	for t: Teleporter in gates:
		eq(t.min_tier, 5, "%s asks for Class A" % t.dungeon_gate)
		ok(reach.spawns.has(DataDungeons.gate_id(t.dungeon_gate)), "%s has its return spawn" % t.dungeon_gate)
		h.tier = 4
		ok(t.is_locked() and t.lock_text().contains("Class A"), "%s turns away a Class B hero" % t.dungeon_gate)
		h.tier = 5
		ok(not t.is_locked(), "%s lets a Class A hero through" % t.dungeon_gate)
	reach.free()
	Game.hero = prev
	done()

func test_special_floors_build_and_hit_hard() -> void:
	var h := Game.new_hero(&"knight", "Delver")
	h.progress.add_xp(XpCurve.total_xp_for_level(90))
	for id in DataDungeonsSpecial.ORDER:
		var n := DataDungeons.floor_count(id)
		for f in [1, n]:
			var m := _built(DataDungeons.map_id(id, f), h)
			ok(m != null and m.spawns.has(&"arrival"), "%s floor %d builds" % [id, f])
			if f == n:
				var bs := m.find_children("BossSpawn", "Marker3D", true, false)
				ok(bs.size() == 1 and StringName(bs[0].get_meta(&"boss")) == DataDungeons.get_def(id).boss, "%s sanctum holds its lord" % id)
			m.free()
	# the spawner makes their monsters very strong on every difficulty
	var prev := Game.hero
	Game.hero = h
	var floor1 := _built(DataDungeons.map_id(&"prismheart", 1), h)
	var sp := Spawner.populate(floor1, 1)
	near(float(sp.difficulty.hp), 1.0 * DataDungeonsSpecial.POWER.hp, 0.0001, "monster health x%.1f" % DataDungeonsSpecial.POWER.hp)
	near(float(sp.difficulty.damage), 1.0 * DataDungeonsSpecial.POWER.damage, 0.0001, "monster damage x%.1f" % DataDungeonsSpecial.POWER.damage)
	eq(float(DataEnemies.DIFFICULTY[1].hp), 1.0, "the shared difficulty table is untouched")
	floor1.free()
	Game.hero = prev
	await host.get_tree().physics_frame
	done()
