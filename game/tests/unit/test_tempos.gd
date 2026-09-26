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
		ok(DataTempos.tempo_class(sk["class"]).skills.has(sid), "%s belongs to its class" % sid)
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
