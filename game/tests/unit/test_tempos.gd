extends TestCase
## Tempos (spirit companions, LORE §9): data, the 50% stat mirror, gear gating, binding / calling back / releasing,
## saving, and the fighting spirit's behaviour in a live map (heal, dodge, retreat, aggro, taunt, follow).

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _tree() -> SceneTree:
	return host.get_tree()

func _frames(n := 2) -> void:
	for i in n:
		await _tree().physics_frame

func _hero(cls := &"knight", lvl := 1) -> HeroData:
	var h := Game.new_hero(cls, "TempoTest")
	if lvl > 1:
		h.progress.add_xp(XpCurve.total_xp_for_level(lvl))
	return h

func _tempo(class_id: StringName, skills: Array = [], trait_id := &"valiant", uid := 1) -> TempoData:
	var t := TempoData.new()
	t.uid = uid
	t.tempo_name = "Test%d" % uid
	t.class_id = class_id
	t.trait_id = trait_id
	t.skills = skills if not skills.is_empty() else [DataTempos.tempo_class(class_id).signature]
	return t

# ---- Live-map scaffolding ------------------------------------------------------------------------------------

func _begin(lvl := 6) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "TempoTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = _hero(&"knight", lvl)
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"start")
	_player.bind(Game.hero)
	await _frames(2)

func _end() -> void:
	for t in TempoParty.actors(_tree()):
		t.free()
	for e in _tree().get_nodes_in_group(&"enemy"):
		e.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

## Bind a hand-made spirit and let it appear beside the player.
func _bind(t: TempoData) -> Tempo:
	Game.hero.tempos.append(t)
	Game.hero.tempo_serial = maxi(Game.hero.tempo_serial, t.uid)
	TempoParty.refresh(Game.hero)
	await _frames(2)
	return TempoParty.actor_for(t.uid)

func _enemy(id: StringName, pos: Vector3) -> Enemy:
	var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(id), Game.hero.progress.level, [], pos, DataEnemies.DIFFICULTY[1])
	return e

func _hit(target: Actor, amount: float, by: Actor) -> void:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ENVIRONMENT
	req.base_min = amount
	req.base_max = amount
	req.use_weapon = false
	req.can_crit = false
	req.evadable = false
	req.blockable = false
	target.receive_hit(req, by)

## Run physics until `cond` holds (or `seconds` pass). Returns whether it held.
func _until(cond: Callable, seconds: float) -> bool:
	var t := 0.0
	while t < seconds:
		if cond.call():
			return true
		await _tree().physics_frame
		t += 1.0 / Engine.physics_ticks_per_second
	return cond.call()

func _decisions(a: Tempo) -> Array:
	var log := []
	a.decided.connect(func(s): log.append(s))
	return log

func _any(log: Array, prefix: String) -> bool:
	return log.any(func(s): return String(s).begins_with(prefix))

# ------------------------------------------------------------------------------------------------------------ data

func test_data_is_consistent() -> void:
	var names := {}
	for n in DataTempos.NAMES:
		ok(not names.has(n), "name %s is unique" % n)
		names[n] = true
	eq(DataTempos.NAMES.size(), 100, "100 names")
	for n in DB.npcs.values():
		ok(not names.has(n.display_name.get_slice(" ", 0)), "no Tempo shares a townsperson's first name (%s)" % n.display_name)
	for cid in DataTempos.class_ids():
		var c := DataTempos.tempo_class(cid)
		ok(not c.is_empty(), "%s exists" % cid)
		ok(ResourceLoader.exists(c.model), "%s model exists" % cid)
		ok((c.skills as Array).has(c.signature), "%s signature is one of its skills" % cid)
		eq((c.skills as Array).filter(func(s): return DataTempos.is_heal(s)).size(), 1, "%s has exactly one heal" % cid)
		for w in c.weapons:
			ok(DB.weapon_type(w) != null, "%s weapon type %s exists" % [cid, w])
		for bid in TempoRules.starter_kit(cid):
			var it := DB.make_item(bid, BH.Rarity.BEGINNER, 1, 1)
			ok(it != null and (c.weapons as Array).has(it.base.weapon_type), "%s starter %s is a class weapon" % [cid, bid])
		ok(DataTempos.class_icon(cid) != null, "%s crest" % cid)
	for sid in DataTempos.SKILLS:
		var sk := DataTempos.skill(sid)
		if DataTempos.is_unique(sid):
			var lg := DataTempos.legend(sk.unique)
			ok((lg.get("skills", []) as Array).has(sid) and lg["class"] == sk["class"], "%s belongs to its renowned spirit" % sid)
		else:
			ok(DataTempos.tempo_class(sk["class"]).skills.has(sid), "%s belongs to its class" % sid)
		ok(Tempo.HANDLERS.has(DataTempos.skill_use(sid)), "%s has a handler (%s)" % [sid, DataTempos.skill_use(sid)])
		ok(DataTempos.skill_icon(sid) != null, "%s icon" % sid)
		ok(float(sk.mana) > 0.0 and float(sk.cooldown) > 0.0, "%s has a cost and a cooldown" % sid)
	for tid in DataTempos.TRAITS:
		var tr := DataTempos.trait_def(tid)
		ok(float(tr.retreat) > 0.0 and float(tr.retreat) < 0.6, "%s retreat threshold sane" % tid)
	# every generated spirit is valid
	for i in 60:
		var t := TempoRules.generate(i * 7919, 5)
		ok(names.has(t.tempo_name), "generated name from the pool")
		ok(t.skills[0] == t.class_def().signature and t.skills.size() >= 2 and t.skills.size() <= 3, "generated skills (%s)" % [t.skills])
		ok(DataTempos.ORIGINS.has(t.origin), "generated origin")
		ok(t.price == TempoRules.hire_cost(t, 5), "generated price = hire cost")
	done()

# ------------------------------------------------------------------------------------------------------------ stats

func test_stats_mirror_half_the_hero() -> void:
	var h := _hero(&"knight", 5)
	var hs := TempoRules.hero_mirror(h)
	var t := _tempo(&"thief", [], &"swift")
	var d := TempoRules.compute(t, hs, h.progress.level, h.cls)
	near(d.get_stat(&"max_hp"), floorf(hs.get_stat(&"max_hp") * 0.5), 1.0, "thief max HP = half the hero's")
	near(d.get_stat(&"max_mana"), floorf(hs.get_stat(&"max_mana") * 0.5), 1.0, "thief max mana = half the hero's")
	ok(d.get_stat(&"move_speed") >= hs.get_stat(&"move_speed") * 1.05 - 0.001, "keeps pace with the hero")
	ok(TempoRules.loadout(t, 5).main_type != null, "empty hands fight with a spirit blade")
	# the swordsman's class bonus applies on top of the mirror
	var sw := TempoRules.compute(_tempo(&"swordsman", [], &"swift"), hs, 5, h.cls)
	near(sw.get_stat(&"max_hp"), floorf(hs.get_stat(&"max_hp") * 0.5 * 1.15), 2.0, "swordsman +15% HP over the mirror")
	# growth: the spirit grows with its hero
	var hp5 := d.get_stat(&"max_hp")
	h.progress.add_xp(XpCurve.total_xp_for_level(10) - XpCurve.total_xp_for_level(h.progress.level) - h.progress.xp)
	var hs10 := TempoRules.hero_mirror(h)
	var d10 := TempoRules.compute(t, hs10, h.progress.level, h.cls)
	ok(d10.get_stat(&"max_hp") > hp5, "grows when the hero levels (%.0f -> %.0f)" % [hp5, d10.get_stat(&"max_hp")])
	near(d10.get_stat(&"max_hp"), floorf(hs10.get_stat(&"max_hp") * 0.5), 1.0, "still exactly half after levelling")
	done()

# ------------------------------------------------------------------------------------------------------------ gear

func test_gear_gating() -> void:
	var h := _hero(&"knight", 10)
	# Unranked hero: Tempos up to Advanced; E: Licensed; D: Elite
	eq(TempoRules.best_wearable_rarity(h), BH.Rarity.ADVANCED, "Unranked -> Advanced")
	h.set_tier(1)
	eq(TempoRules.best_wearable_rarity(h), BH.Rarity.LICENSED, "Class E -> Licensed")
	h.set_tier(2)
	eq(TempoRules.best_wearable_rarity(h), BH.Rarity.ELITE, "Class D -> Elite")
	h.set_tier(0)
	var sw := _tempo(&"swordsman")
	var ar := _tempo(&"archer", [], &"valiant", 2)
	var th := _tempo(&"thief", [], &"valiant", 3)
	var sword := DB.make_item(&"iron_longsword", BH.Rarity.ADVANCED, 5, 11)
	var bow := DB.make_item(&"hunters_bow", BH.Rarity.COMMON, 5, 12)
	var shield := DB.make_item(&"warden_kite_shield", BH.Rarity.COMMON, 5, 13)
	eq(TempoRules.equip_error(h, sw, sword), "", "swordsman takes an Advanced sword while Unranked")
	var elite := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 5, 14)
	ok(TempoRules.equip_error(h, sw, elite) != "", "Elite refused for an Unranked hero's Tempo")
	var lic := DB.make_item(&"iron_longsword", BH.Rarity.LICENSED, 5, 15)
	ok(TempoRules.equip_error(h, sw, lic) != "", "Licensed refused while Unranked")
	h.set_tier(1)
	eq(TempoRules.equip_error(h, sw, lic), "", "Licensed allowed at Class E")
	ok(TempoRules.equip_error(h, sw, elite) != "", "Elite still refused at Class E")
	h.set_tier(0)
	ok(TempoRules.equip_error(h, ar, sword) != "", "an archer cannot wield a sword")
	eq(TempoRules.equip_error(h, ar, bow), "", "an archer takes a bow")
	ok(TempoRules.equip_error(h, th, bow) != "", "a thief cannot wield a bow")
	eq(TempoRules.equip_error(h, sw, shield, &"sub_weapon"), "", "a swordsman takes a shield")
	ok(TempoRules.equip_error(h, ar, shield, &"sub_weapon") != "", "an archer does not")
	var high := DB.make_item(&"tower_shield", BH.Rarity.COMMON, 12, 16)
	ok(TempoRules.equip_error(_hero(&"knight", 3), sw, high, &"sub_weapon").begins_with("Requires level"), "hero level requirement applies")
	done()

func test_equip_unequip_release_move_items_exactly() -> void:
	var h := _hero(&"knight", 5)
	var t := _tempo(&"swordsman")
	h.tempos.append(t)
	var sword := DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 5, 21)
	var shield := DB.make_item(&"warden_kite_shield", BH.Rarity.COMMON, 5, 22)
	h.inventory.add(sword)
	h.inventory.add(shield)
	var free0 := h.inventory.free_cells()
	eq(TempoRules.equip_from_inventory(h, t, sword), "", "sword equipped")
	eq(TempoRules.equip_from_inventory(h, t, shield), "", "shield equipped")
	ok(t.equipment.get_item(&"main_weapon") == sword and t.equipment.get_item(&"sub_weapon") == shield, "on the Tempo")
	eq(h.inventory.index_of(sword), -1, "sword left the bag")
	eq(h.inventory.free_cells(), free0 + 2, "two cells freed")
	var sword2 := DB.make_item(&"iron_longsword", BH.Rarity.BASIC, 5, 23)
	h.inventory.add(sword2)
	eq(TempoRules.equip_from_inventory(h, t, sword2, &"main_weapon"), "", "swap in a better sword")
	ok(h.inventory.index_of(sword) >= 0, "the displaced sword went back to the bag")
	eq(TempoRules.unequip_to_inventory(h, t, &"sub_weapon"), "", "shield taken off")
	ok(h.inventory.index_of(shield) >= 0, "shield back in the bag")
	var gear := t.equipment.equipped_items().size()
	var free1 := h.inventory.free_cells()
	eq(TempoRules.release(h, t), "", "released")
	ok(not h.tempos.has(t), "gone from the party")
	eq(h.inventory.free_cells(), free1 - gear, "its gear came back to the bag")
	ok(h.inventory.index_of(sword2) >= 0, "including the sword it wore")
	done()

# ------------------------------------------------------------------------------------------------------------ bind

func test_hire_revive_release_rules() -> void:
	var h := _hero(&"knight", 4)
	h.inventory.gold = 5000
	var r1 := TempoRules.roster(h).map(func(t): return t.tempo_name)
	var h2 := _hero(&"knight", 4)
	var r2 := TempoRules.roster(h2).map(func(t): return t.tempo_name)
	eq(r1, r2, "the roster is deterministic")
	eq(r1.size(), DataTempos.ROSTER_SIZE, "roster size")
	var offer0 := TempoRules.roster(h)[0] as TempoData
	var g0 := h.inventory.gold
	var a := TempoRules.hire(h, 0)
	ok(a != null, "first bound")
	eq(h.inventory.gold, g0 - offer0.price, "paid exactly the price")
	eq(a.uid, 1, "uid 1")
	ok(a.equipment.get_item(&"main_weapon") != null, "arrives with its starter weapon")
	ok(TempoRules.roster(h)[0].tempo_name != offer0.tempo_name, "a new spirit takes its place in the roster")
	ok(TempoRules.hire(h, 1) != null, "second bound")
	var g1 := h.inventory.gold
	ok(TempoRules.hire_error(h, 2) != "", "a third is refused")
	ok(TempoRules.hire(h, 2) == null and h.inventory.gold == g1, "and costs nothing")
	# roster refreshes with play time
	var before := TempoRules.roster(h).map(func(t): return t.tempo_name)
	h.play_time += DataTempos.ROSTER_REFRESH + 1.0
	ok(TempoRules.roster(h).map(func(t): return t.tempo_name) != before, "the roster refreshes over time")
	# falling and calling back
	a.fallen = true
	a.hp_frac = 0.0
	eq(TempoRules.bound_count(h), 2, "the fallen still count")
	ok(TempoRules.has_fallen(h), "has a fallen Tempo")
	eq(TempoRules.active(h).size(), 1, "one standing")
	var cost := TempoRules.revive_cost(a, h)
	eq(cost, int(snappedf(25.0 + 12.0 * 4.0 + a.price * 0.2, 5.0)), "revive cost formula")
	h.inventory.gold = cost - 1
	ok(TempoRules.revive(h, a) != "", "cannot afford: refused")
	ok(a.fallen, "still fallen")
	h.inventory.gold = cost + 10
	eq(TempoRules.revive(h, a), "", "called back")
	ok(not a.fallen and a.hp_frac == 1.0, "standing and whole")
	eq(h.inventory.gold, 10, "paid exactly")
	ok(TempoRules.revive(h, a) != "", "a standing Tempo cannot be called back")
	# resting restores every standing Tempo
	a.hp_frac = 0.2
	TempoRules.restore_all(h)
	eq(a.hp_frac, 1.0, "rest restores")
	eq(TempoRules.release(h, a), "", "released")
	eq(TempoRules.bound_count(h), 1, "room for another")
	done()

func test_save_round_trip() -> void:
	var h := _hero(&"mage", 6)
	h.inventory.gold = 9000
	TempoRules.roster(h)
	var a := TempoRules.hire(h, 0)
	TempoRules.hire(h, 1)
	a.fallen = true
	a.hp_frac = 0.0
	a.kills = 17
	a.equipment.equip(DB.make_item(&"padded_gambeson", BH.Rarity.BASIC, 3, 5), &"inner_garment", 6, TempoRules.NO_ATTR)
	var json := JSON.stringify(h.to_dict())
	var back := HeroData.from_dict(JSON.parse_string(json))
	eq(back.tempos.size(), 2, "two Tempos saved")
	eq(JSON.stringify(back.to_dict()), json, "hero JSON round trip is exact")
	eq(back.tempos[0].kills, 17, "kills kept")
	ok(back.tempos[0].fallen, "fallen kept")
	eq(back.tempo_serial, h.tempo_serial, "serial kept")
	var legacy := h.to_dict()
	legacy.erase("tempos")
	legacy.erase("tempo_roster")
	legacy.erase("tempo_serial")
	var old := HeroData.from_dict(legacy)
	eq(old.tempos.size(), 0, "an older save loads with no Tempos")
	done()

# ------------------------------------------------------------------------------------------------------------ live AI

func test_ai_heals_the_hero() -> void:
	await _begin()
	var a := await _bind(_tempo(&"archer", [&"ar_pierce", &"ar_mend"], &"devoted", 1))
	ok(a != null, "archer spawned")
	if a:
		var log := _decisions(a)
		_player.hp = _player.max_hp() * 0.25
		var healed := await _until(func(): return _player.hp > _player.max_hp() * 0.35, 3.0)
		ok(healed, "the hero at 25%% HP is healed (now %.0f%%)" % (_player.hp / _player.max_hp() * 100.0))
		ok(_any(log, "healed %s" % _player.display_name), "decided to heal the hero (%s)" % [log])
	_end()
	done()

func test_ai_dodges_a_telegraphed_blast() -> void:
	await _begin()
	var a := await _bind(_tempo(&"swordsman", [&"sw_cleave"], &"valiant", 1))
	ok(a != null, "spirit spawned")
	if a:
		var log := _decisions(a)
		a.teleport_to(_player.global_position + Vector3(5, 0, 0))
		await _frames(1)
		var at := a.global_position
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.IMPACT
		req.base_min = 99999.0
		req.base_max = 99999.0
		req.use_weapon = false
		req.evadable = false
		req.blockable = false
		var hp0 := a.hp
		AreaEffects.delayed(Game.current_map, at, 1.8, 0.45, req, null, BH.LAYER_PLAYER)
		await _until(func(): return false, 0.8)
		ok(a.alive and a.hp >= hp0 - 0.5, "the Tempo was not caught by the blast")
		ok(a.global_position.distance_to(at) > 1.8 + 0.3 or _any(log, "dodge"), "it left the blast area (%.1f m)" % a.global_position.distance_to(at))
		ok(_any(log, "dodge"), "it decided to dodge (%s)" % [log])
	_end()
	done()

func test_ai_retreats_when_hurt() -> void:
	await _begin()
	var a := await _bind(_tempo(&"swordsman", [&"sw_cleave", &"sw_charge"], &"cautious", 1))
	ok(a != null, "spirit spawned")
	if a:
		var log := _decisions(a)
		var e := _enemy(&"hollow_soldier", a.global_position + Vector3(3, 0, 0))
		e.alert_to(a.global_position)
		await _frames(2)
		a.hp = a.max_hp() * 0.3
		var fled := await _until(func(): return a.mode == Tempo.Mode.RETREAT, 1.0)
		ok(fled, "falls back below its threshold (mode %s)" % a.mode_name())
		ok(_any(log, "retreat"), "decided to retreat (%s)" % [log])
	_end()
	done()

func test_enemies_turn_on_a_tempo_that_hurts_them_more() -> void:
	await _begin()
	var a := await _bind(_tempo(&"swordsman", [&"sw_cleave"], &"valiant", 1))
	ok(a != null, "spirit spawned")
	if a:
		var e := _enemy(&"ogre_crusher", _player.global_position + Vector3(4, 0, 4))
		e.alert_to(_player.global_position)
		await _frames(3)
		_hit(e, 1.0, _player)
		await _frames(2)
		for i in 4:
			_hit(e, e.max_hp() * 0.08, a)
		var switched := await _until(func(): return e.target == a, 2.0)
		ok(switched, "the monster turns on the spirit that out-damages the hero")
		# a taunt forces the target even without threat
		a.teleport_to(_player.global_position + Vector3(-6, 0, 0))
		var e2 := _enemy(&"hollow_soldier", _player.global_position + Vector3(2, 0, -2))
		e2.alert_to(_player.global_position)
		await _frames(3)
		e2.taunt(a, 5.0)
		await _until(func(): return false, 0.6)
		ok(e2.target == a, "a taunted monster fights the spirit")
	_end()
	done()

func test_ai_follows_and_rejoins() -> void:
	await _begin()
	var a := await _bind(_tempo(&"archer", [&"ar_pierce"], &"swift", 1))
	ok(a != null, "spirit spawned")
	if a:
		var log := _decisions(a)
		_player.global_position += Vector3(6, 0, 0)
		var near_ok := await _until(func(): return a.global_position.distance_to(_player.global_position) < 4.0, 4.0)
		ok(near_ok, "follows the hero (%.1f m)" % a.global_position.distance_to(_player.global_position))
		# leave it far behind: it rejoins at once
		Game.place_player(&"waypoint")
		await _frames(2)
		var far := a.global_position.distance_to(_player.global_position)
		a.teleport_to(_player.global_position + Vector3(0, 0, 45))
		var back := await _until(func(): return a.global_position.distance_to(_player.global_position) < 5.0, 1.0)
		ok(back, "teleports back when left %.0f m behind" % 45.0)
		ok(_any(log, "rejoined"), "decided to rejoin (%s, regroup gap %.1f)" % [log, far])
	_end()
	done()

# ------------------------------------------------------------------------------------------------------------ bh-005

func test_starter_tempo() -> void:
	var h := _hero(&"knight", 1)
	eq(h.tempos.size(), 0, "Game.new_hero alone binds nothing")
	var t := TempoRules.grant_starter(h)
	ok(t != null, "the starter is granted")
	eq(h.tempos.size(), 1, "one Tempo")
	eq(t.tempo_name, String(DataTempos.STARTER.name), "named %s" % DataTempos.STARTER.name)
	eq(t.class_id, &"swordsman", "a Swordsman")
	eq(t.grade, 1, "grade 1")
	eq(t.skills, [&"sw_cleave", &"sw_mend"], "Cleave and Soul Mend")
	eq(t.price, 0, "free")
	eq(t.uid, 1, "uid 1")
	ok(not t.is_legend(), "not renowned")
	ok(t.equipment.get_item(&"main_weapon") != null, "arrives holding a sword")
	ok(not DataTempos.NAMES.has(t.tempo_name), "his name is not in the random pool")
	ok(TempoRules.grant_starter(h) == null and h.tempos.size() == 1, "granting twice does nothing")
	eq(TempoRules.revive_cost(t, h), int(snappedf(25.0 + 12.0, 5.0)), "calling him back costs the base fee")
	# room for exactly one more
	h.inventory.gold = 99999
	TempoRules.roster(h)
	ok(TempoRules.hire(h, 0) != null, "a second Tempo can be bound")
	ok(TempoRules.hire_error(h, 1) != "", "a third is refused")
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(back.tempos[0].tempo_name, t.tempo_name, "the starter survives saving")
	done()

func test_grades_and_roster_upgrades() -> void:
	var cases := [[1, {}, 1], [3, {}, 1], [4, {}, 2], [7, {}, 2], [8, {}, 3], [6, {&"temple_seal_broken": true}, 3],
		[10, {&"boss_warden_defeated": true}, 4], [12, {}, 4], [19, {}, 4], [20, {}, 5]]
	for c in cases:
		var h := _hero(&"knight", c[0])
		for k in c[1]:
			h.world_flags[k] = c[1][k]
		eq(TempoRules.current_grade(h), c[2], "level %d %s -> grade %d" % [c[0], c[1].keys(), c[2]])
	for i in DataTempos.max_grade() - 1:
		ok(float(DataTempos.grade_def(i + 2).mirror) > float(DataTempos.grade_def(i + 1).mirror), "grade %d carries more strength" % (i + 2))
		ok(float(DataTempos.grade_def(i + 2).price) > float(DataTempos.grade_def(i + 1).price), "grade %d costs more" % (i + 2))
	eq(DataTempos.classes_for_grade(1), [&"swordsman", &"archer", &"thief"], "grade 1: the three first classes")
	ok(DataTempos.classes_for_grade(2).has(&"mystic") and not DataTempos.classes_for_grade(2).has(&"warden"), "Mystics answer from grade 2")
	ok(DataTempos.classes_for_grade(3).has(&"warden"), "Wardens answer from grade 3")
	# every generated spirit obeys its grade
	var seen_skills := {}
	for g in range(1, DataTempos.max_grade() + 1):
		var gd := DataTempos.grade_def(g)
		for i in 50:
			var t := TempoRules.generate(i * 104729 + g * 7, 10, &"", [], g)
			var td := t.class_def()
			ok(t.grade == g and int(td.grade) <= g, "g%d: class %s may answer" % [g, t.class_id])
			ok(t.skills[0] == td.signature, "g%d: signature first" % g)
			var extra := t.skills.size() - 1
			var pool := DataTempos.rollable_skills(t.class_id, g).size()
			ok(extra <= int(gd.extra[1]) and extra >= mini(int(gd.extra[0]), pool), "g%d: %d extra skills (%s)" % [g, extra, t.skills])
			var heals := 0
			for s in t.skills:
				ok(not DataTempos.is_unique(s) and DataTempos.skill_grade(s) <= g, "g%d: %s may be known" % [g, s])
				heals += 1 if DataTempos.is_heal(s) else 0
				seen_skills[s] = true
			ok(heals <= 1, "g%d: one mend at most" % g)
			eq(t.price, TempoRules.hire_cost(t, 10), "g%d: price = hire cost" % g)
			ok(is_equal_approx(t.mirror(), float(gd.mirror)), "g%d: mirror %.2f" % [g, t.mirror()])
	for sid in DataTempos.SKILLS:
		if not DataTempos.is_unique(sid):
			ok(seen_skills.has(sid), "%s is rolled by some spirit" % sid)
	# the same spirit bound at a higher grade is stronger and dearer
	var hs := _hero(&"knight", 12)
	var low := _tempo(&"swordsman", [&"sw_cleave", &"sw_mend"])
	var high := _tempo(&"swordsman", [&"sw_cleave", &"sw_mend"])
	high.grade = 4
	var m := TempoRules.hero_mirror(hs)
	ok(TempoRules.compute(high, m, 12, hs.cls).get_stat(&"max_hp") > TempoRules.compute(low, m, 12, hs.cls).get_stat(&"max_hp"), "grade 4 carries more of the hero")
	ok(TempoRules.hire_cost(high, 12) > TempoRules.hire_cost(low, 12), "and costs more")
	# the roster upgrades the moment the grade rises
	var h2 := _hero(&"knight", 3)
	var before := TempoRules.roster(h2).map(func(t): return t.tempo_name)
	ok(TempoRules.roster(h2).all(func(t): return t.grade == 1), "level 3: Restless spirits")
	eq(TempoRules.check_grade(h2), 0, "nothing to upgrade yet")
	h2.progress.add_xp(XpCurve.total_xp_for_level(4) - h2.progress.total_xp)
	eq(h2.progress.level, 4, "level 4")
	eq(TempoRules.check_grade(h2), 2, "the grade rises to Seasoned")
	var after := TempoRules.roster(h2)
	ok(after.all(func(t): return t.grade == 2), "every offer is Seasoned now")
	ok(after.map(func(t): return t.tempo_name) != before, "the weaker spirits faded")
	ok(after.any(func(t): return t.class_id == &"mystic"), "a Mystic answers")
	eq(TempoRules.check_grade(h2), 0, "and only once")
	# a hired replacement keeps the roster's grade
	h2.inventory.gold = 99999
	TempoRules.hire(h2, 0)
	ok(TempoRules.roster(h2).all(func(t): return t.grade == 2), "the replacement offer is Seasoned too")
	# a deed raises it without levels
	var h3 := _hero(&"knight", 6)
	TempoRules.roster(h3)
	h3.world_flags[&"temple_seal_broken"] = true
	eq(TempoRules.check_grade(h3), 3, "breaking the seal brings Veteran spirits")
	ok(TempoRules.roster(h3).any(func(t): return t.class_id == &"warden") or DataTempos.ROSTER_SIZE < 5, "Wardens can answer")
	done()

func test_renowned_spirits() -> void:
	eq(DataTempos.legend_ids().size(), 5, "five renowned spirits")
	eq(DataTempos.LEGENDS.size(), 5, "and no more")
	var names := {}
	var prices := []
	for id in DataTempos.legend_ids():
		var lg := DataTempos.legend(id)
		var first := String(lg.name).get_slice(" ", 0)
		ok(not names.has(first), "%s has a unique name" % lg.name)
		names[first] = true
		ok(not DataTempos.NAMES.has(first), "%s is not in the random pool" % first)
		for n in DB.npcs.values():
			ok(n.display_name.get_slice(" ", 0) != first, "%s does not share a townsperson's name" % first)
		ok(DataTempos.CLASSES.has(lg["class"]) and DataTempos.TRAITS.has(lg.trait), "%s class and trait exist" % id)
		var uniques := (lg.skills as Array).filter(func(s): return DataTempos.is_unique(s))
		ok(uniques.size() >= 1, "%s has a skill of its own" % id)
		for s in lg.skills:
			ok(DataTempos.SKILLS.has(s), "%s skill %s exists" % [id, s])
			ok(DataTempos.skill(s)["class"] == lg["class"], "%s skill %s fits its class" % [id, s])
		ok((lg.skills as Array).filter(func(s): return DataTempos.is_heal(s)).size() <= 1, "%s knows one mend at most" % id)
		ok(int(lg.price) >= 1500, "%s is expensive (%d)" % [id, int(lg.price)])
		ok(DataTempos.portrait_path("tempo_%s" % id) != "", "%s portrait" % id)
		prices.append(int(lg.price))
	var sorted := prices.duplicate()
	sorted.sort()
	eq(prices, sorted, "listed from the cheapest to the dearest")
	ok(prices[0] > TempoRules.hire_cost(TempoRules.generate(1, 5, &"", [], 2), 5) * 2, "far above a nameless spirit")
	ok(DataTempos.portrait_path("tempo_tobren") != "", "Tobren's portrait")
	# binding rules
	var h := _hero(&"knight", 4)
	h.inventory.gold = 1000
	ok(TempoRules.legend_error(h, &"hollan").contains("level 5"), "locked below its level")
	h.progress.add_xp(XpCurve.total_xp_for_level(5) - h.progress.total_xp)
	ok(TempoRules.legend_error(h, &"hollan").contains("gold"), "refused without the gold")
	ok(TempoRules.hire_legend(h, &"hollan") == null and h.inventory.gold == 1000, "and nothing changes")
	h.inventory.gold = 1600
	var t := TempoRules.hire_legend(h, &"hollan")
	ok(t != null and t.is_legend(), "Hollan bound")
	eq(h.inventory.gold, 100, "paid exactly 1500")
	eq(t.full_name(), "Hollan Greywall, the Unbroken", "full name")
	ok(t.equipment.get_item(&"sub_weapon") != null, "arrives with his shield")
	ok(is_equal_approx(t.mirror(), 0.75), "carries 75% of the hero")
	ok(TempoRules.legend_error(h, &"hollan").contains("already"), "cannot be bound twice")
	var m := TempoRules.hero_mirror(h)
	var plain := TempoRules.legend_data(&"hollan")
	plain.legend_id = &""
	plain.grade = 1
	ok(TempoRules.compute(t, m, 5, h.cls).get_stat(&"max_hp") > TempoRules.compute(plain, m, 5, h.cls).get_stat(&"max_hp"), "stronger than the same spirit unnamed")
	var lo := TempoRules.spirit_loadout(&"thief", 10, &"vessik")
	ok(lo.dual_wield and lo.main_element == Elements.DARK and lo.main_max > TempoRules.spirit_loadout(&"thief", 10).main_max, "Vessik's ghost blades are dark and stronger")
	var json := JSON.stringify(h.to_dict())
	var back := HeroData.from_dict(JSON.parse_string(json))
	eq(back.tempos[0].legend_id, &"hollan", "renowned identity saved")
	eq(JSON.stringify(back.to_dict()), json, "exact round trip")
	eq(TempoRules.release(h, t), "", "released")
	h.inventory.gold = 2000
	eq(TempoRules.legend_error(h, &"hollan"), "", "a released renowned spirit returns to the shrine")
	done()

## Every skill of every class (and every renowned spirit's own) does what it says in a live fight.
func test_every_skill_works_live() -> void:
	await _begin(10)
	var uid := 1
	for cid in DataTempos.class_ids():
		var skills: Array = (DataTempos.tempo_class(cid).skills as Array).duplicate()
		for sid in DataTempos.SKILLS:
			if DataTempos.is_unique(sid) and DataTempos.skill(sid)["class"] == cid:
				skills.append(sid)
		for sid in skills:
			var t := _tempo(cid, [DataTempos.tempo_class(cid).signature, sid], &"valiant", uid)
			uid += 1
			var a := await _bind(t)
			ok(a != null, "%s spawned for %s" % [cid, sid])
			if a == null:
				continue
			a.teleport_to(_player.global_position + Vector3(-3, 0, 0))
			await _frames(1)
			var foes := []
			for off in [Vector3(0, 0, 3.0), Vector3(1.4, 0, 3.4), Vector3(-1.4, 0, 3.4)]:
				var e := _enemy(&"hollow_soldier", a.global_position + off)
				e.alert_to(_player.global_position)
				foes.append(e)
			await _frames(2)
			var hp0 := 0.0
			for e in foes:
				hp0 += e.hp
			a.cooldowns.clear()
			a.mana = a.max_mana()
			a._cancel_action()
			a.target = foes[0]
			var use := DataTempos.skill_use(sid)
			var log := _decisions(a)
			if use == "heal":
				_player.hp = _player.max_hp() * 0.4
				var h0 := _player.hp
				a._cast_heal(sid, _player)
				ok(await _until(func(): return _player.hp > h0 + 1.0, 1.5), "%s heals the hero" % sid)
			else:
				ok(a._use_skill(sid), "%s fires" % sid)
				match use:
					"challenge":
						ok(await _until(func(): return foes.any(func(e): return is_instance_valid(e) and e.target == a), 1.5), "%s draws the monsters" % sid)
					"ward":
						ok(await _until(func(): return _player.status.has(&"shielded"), 1.5), "%s wards the hero" % sid)
						if DataTempos.skill(sid).has("taunt"):
							ok(foes.any(func(e): return is_instance_valid(e) and e.target == a), "%s also draws the monsters" % sid)
					"rally":
						ok(await _until(func(): return _player.status.has(&"empowered"), 1.5), "%s empowers the hero" % sid)
					"disengage":
						var from := a.global_position
						ok(await _until(func(): return a.global_position.distance_to(from) > 2.0, 1.5), "%s vaults away" % sid)
					"smoke":
						ok(await _until(func(): return a.is_hidden(), 1.5), "%s hides it" % sid)
					_:
						var hurt := func() -> bool:
							var now := 0.0
							for e in foes:
								now += e.hp if is_instance_valid(e) and e.alive else 0.0
							return now < hp0 - 0.5
						ok(await _until(hurt, 3.0), "%s damages the monsters (%s)" % [sid, log])
				if use == "chain":
					var n := foes.filter(func(e): return is_instance_valid(e) and (not e.alive or e.hp < e.max_hp() - 0.5)).size()
					ok(n >= 2, "%s leaps between monsters (%d hit)" % [sid, n])
			for e in foes:
				if is_instance_valid(e):
					e.free()
			Game.hero.tempos.erase(t)
			a.free()
			_player.status.remove(&"shielded")
			_player.status.remove(&"empowered")
			_player.hp = _player.max_hp()
	_end()
	done()

# ------------------------------------------------------------------------------------------------------------ UI

## Opening the Tempo window with bound spirits used to recurse forever (tab rebuild -> tab_changed -> refresh).
func test_windows_open_with_tempos() -> void:
	var prev := Game.hero
	Game.hero = _hero(&"knight", 5)
	Game.hero.inventory.gold = 9000
	TempoRules.roster(Game.hero)
	TempoRules.hire(Game.hero, 0)
	TempoRules.hire(Game.hero, 1)
	var w := TempoWindow.new()
	host.add_child(w)
	w.open()
	ok(w.visible, "Tempo window opens")
	eq(w._tabs.tab_count, 2, "one tab per Tempo")
	ok(w.current == Game.hero.tempos[0], "first Tempo selected")
	w._tabs.current_tab = 1
	ok(w.current == Game.hero.tempos[1], "switching tabs selects the second")
	Events.tempo_changed.emit(0)
	ok(w.current == Game.hero.tempos[1], "a refresh keeps the selection")
	w.close_window()
	w.free()
	var c := TempoCallerWindow.new()
	host.add_child(c)
	c.open()
	ok(c.visible, "Tempo-Caller window opens")
	c._tabs.current_tab = 1
	c._tabs.current_tab = 0
	c.close_window()
	c.free()
	Game.hero = prev
	done()
