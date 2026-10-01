extends TestCase
## bh-013: twenty dungeons on the map (fifteen new, 2–5 floors, tiers 1–5), raid recovery (30 min – 2 h, the boss never
## returns, champions and Usurpers still come), and the twenty-one new monsters' signature mechanics, each driven by
## hand in a live map (the town plaza, same scaffolding as test_enemies2).

const X := preload("res://src/actors/enemy/enemy_traits_x.gd")
const NEW := [&"gravecaller", &"riftcaller", &"mirage_weaver", &"bloodbinder", &"aegis_acolyte", &"storm_herald",
	&"mirror_knight", &"warband_chieftain", &"soulbound_twin", &"briar_lasher", &"broodhost", &"goblin_sapper",
	&"treasure_gremlin", &"gloam_ooze", &"tunnel_maw", &"stonegaze_basilisk", &"shellback_grinder", &"hive_nest",
	&"hive_drone", &"gloomwraith", &"prism_sentinel"]
const DT := 1.0 / 60.0

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

func _hero() -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "Raider")
	h.init_new()
	return h

func _new_ids() -> Array:
	return DataDungeonsX.ORDER

# ---- data -------------------------------------------------------------------------------------------------------

func test_a_twenty_dungeons() -> void:
	var regular := DataDungeons.order().filter(func(id): return not DataDungeons.is_special(id))
	eq(regular.size(), 20, "twenty dungeons (besides bh-028's special ones, checked in test_bh028)")
	var tiers := {}
	for id in regular:
		var d := DataDungeons.get_def(id)
		var n := DataDungeons.floor_count(id)
		ok(n >= 2 and n <= 5, "%s has 2-5 floors (%d)" % [id, n])
		eq((d.levels as Array).size(), n, "%s has a level range per floor" % id)
		var t := DataDungeons.tier(id)
		ok(t >= 1 and t <= 5, "%s tier %d" % [id, t])
		tiers[t] = true
		ok(DB.enemy(d.boss) != null and DB.enemy(d.boss).archetype == &"boss", "%s boss %s is a boss" % [id, d.boss])
		for key in ["miniboss", "usurper"]:
			var m: Dictionary = d[key]
			ok(DB.enemy(m.enemy) != null, "%s %s uses a real monster" % [id, key])
			ok(not DataMinibosses.find(m.id).is_empty(), "%s %s is listed" % [id, key])
		eq(DataMinibosses.find(d.miniboss.id).map, DataDungeons.map_id(id, n - 1), "%s champion holds the last sealed floor" % id)
		eq(DataMinibosses.find(d.usurper.id).map, DataDungeons.map_id(id, n), "%s usurper holds the sanctum" % id)
		for pool in d.pools:
			for eid in d.pools[pool]:
				ok(DB.enemy(eid) != null, "%s pool %s: %s exists" % [id, pool, eid])
		ok(DB.map_def(d.surface.map) != null, "%s gate map exists" % id)
		ok(DB.map_def(DataDungeons.map_id(id, n)) != null, "%s sanctum map is registered" % id)
	eq(tiers.size(), 5, "every difficulty tier is used")
	done()

func test_b_gates_are_public_places_with_routes() -> void:
	var h := _hero()
	for id in _new_ids():
		var d := DataDungeons.get_def(id)
		var gate := DataIsland.place(String(d.surface.place))
		ok(not gate.is_empty(), "%s gate place exists" % id)
		if gate.is_empty():
			continue
		ok(bool(gate.get("public", false)) and bool(gate.get("listed", false)), "%s gate is public and listed" % id)
		eq(StringName(gate.map), StringName(d.surface.map), "%s gate is on its map" % id)
		var route := RoutePlanner.plan(h, &"sanctuary", Vector2(0, 38), String(d.surface.place))
		ok(route.ok, "%s gate is reachable from the South Gate (%s)" % [id, route.reason])
	done()

func test_c_new_floors_build() -> void:
	var holder := Node3D.new()
	host.add_child(holder)
	for id in _new_ids():
		var n := DataDungeons.floor_count(id)
		for f in range(1, n + 1):
			var mid := DataDungeons.map_id(id, f)
			var m := Game.build_map(mid)
			ok(m != null and m.def.id == mid, "%s builds" % mid)
			if m == null:
				continue
			holder.add_child(m)
			for s in [&"start", &"arrival"]:
				ok(m.spawns.has(s), "%s has spawn %s" % [mid, s])
			ok(m.spawns.has(&"descent") if f < n else m.spawns.has(&"exit"), "%s has its way on" % mid)
			if f == n:
				var bs := m.find_children("BossSpawn", "Marker3D", true, false)
				eq(bs.size(), 1, "%s sanctum has a boss spawn" % mid)
				if not bs.is_empty():
					eq(StringName(bs[0].get_meta(&"boss")), DataDungeons.get_def(id).boss, "%s boss spawn names its boss" % mid)
					eq(StringName(bs[0].get_meta(&"dungeon", "")), id, "%s boss spawn knows its dungeon" % mid)
			m.free()
	holder.free()
	await host.get_tree().physics_frame
	done()

# ---- raid recovery ------------------------------------------------------------------------------------------------

func test_d_recovery_times() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 13
	for id in DataDungeons.order():
		var lo := INF
		var hi := -INF
		for i in 200:
			var m := DataDungeons.roll_recovery(id, rng)
			lo = minf(lo, m)
			hi = maxf(hi, m)
		ok(lo >= 30.0 and hi <= 120.0, "%s recovers in 30-120 min (%.0f-%.0f)" % [id, lo, hi])
	var easy := DataDungeons.roll_recovery(&"cellars", rng)
	ok(easy <= 55.0, "a tier-1 dungeon recovers quickly (%.0f)" % easy)
	var hard := DataDungeons.roll_recovery(&"maw", rng)
	ok(hard >= 95.0, "a tier-5 dungeon takes long (%.0f)" % hard)
	var h := _hero()
	ok(not DataDungeons.recovering(h, &"hive"), "not recovering before a raid")
	ok(not DataDungeons.boss_gone(h, &"hive"), "the boss is there before a raid")
	var rec := DataDungeons.record_raid(h, &"hive")
	var mins := (float(rec.until) - float(rec.at)) / 60.0
	ok(mins >= 30.0 and mins <= 120.0, "a raid records 30-120 min (%.1f)" % mins)
	ok(DataDungeons.recovering(h, &"hive"), "recovering after the raid")
	ok(DataDungeons.boss_gone(h, &"hive"), "the boss is gone after the raid")
	ok(DataDungeons.status_text(h, &"hive").begins_with("Raided"), "status says raided")
	DataDungeons.clock_offset = mins * 60.0 + 5.0
	ok(not DataDungeons.recovering(h, &"hive"), "recovered after the rolled time")
	ok(DataDungeons.boss_gone(h, &"hive"), "the boss still never returns")
	ok(DataDungeons.status_text(h, &"hive").begins_with("Recovered"), "status says recovered")
	DataDungeons.clock_offset = 0.0
	# save round trip
	var d := h.to_dict()
	var h2 := HeroData.from_dict(d)
	ok(h2.dungeon_raids.has("hive"), "raids survive a save")
	done()

## Spawns on a floor with and without a raid in progress.
func _spawn_count(mid: StringName) -> Dictionary:
	var m := Game.build_map(mid)
	_holder.add_child(m)
	MapBuilder.bake_navigation(m)
	var s := Spawner.populate(m, 1)
	var out := {"camps": 0, "boss": 0, "mini": [], "total": s.spawned.size()}
	for e in s.spawned:
		if e.is_boss:
			out.boss += 1
		elif e.is_miniboss():
			out.mini.append(String(e.miniboss.get("id", "")))
		else:
			out.camps += 1
	for e in s.minibosses:
		if not out.mini.has(String(e.miniboss.get("id", ""))):
			out.mini.append(String(e.miniboss.get("id", "")))
	for e in _tree().get_nodes_in_group(&"enemy"):
		if is_instance_valid(e):
			e.free()
	m.free()
	return out

func test_e_raided_dungeon_spawns() -> void:
	_holder = Node3D.new()
	host.add_child(_holder)
	var saved := Game.hero
	Game.hero = _hero()
	var id := &"sump"
	var n := DataDungeons.floor_count(id)
	var d := DataDungeons.get_def(id)
	var f1 := _spawn_count(DataDungeons.map_id(id, 1))
	ok(f1.camps > 0, "floor 1 has monsters before a raid (%d)" % f1.camps)
	var last := _spawn_count(DataDungeons.map_id(id, n))
	eq(last.boss, 1, "the boss waits in the sanctum before a raid")
	ok(not last.mini.has(String(d.usurper.id)), "no usurper before a raid")
	DataDungeons.record_raid(Game.hero, id, 60.0)
	var q1 := _spawn_count(DataDungeons.map_id(id, 1))
	eq(q1.camps, 0, "a recovering floor stays empty")
	var qc := _spawn_count(DataDungeons.map_id(id, n - 1))
	ok(qc.mini.has(String(d.miniboss.id)), "the champion still comes while recovering")
	var ql := _spawn_count(DataDungeons.map_id(id, n))
	eq(ql.boss, 0, "the boss does not return")
	ok(ql.mini.has(String(d.usurper.id)), "the usurper holds the sanctum")
	DataDungeons.clock_offset = 61.0 * 60.0
	var r1 := _spawn_count(DataDungeons.map_id(id, 1))
	ok(r1.camps > 0, "after recovery the camps replenish (%d)" % r1.camps)
	var rl := _spawn_count(DataDungeons.map_id(id, n))
	eq(rl.boss, 0, "the boss never comes back after recovery")
	DataDungeons.clock_offset = 0.0
	Game.hero = saved
	_holder.free()
	await _frames(1)
	done()

# ---- monsters -----------------------------------------------------------------------------------------------------

func test_f_new_monsters_resolve() -> void:
	for id in NEW:
		var d := DB.enemy(id)
		ok(d != null, "%s registered" % id)
		if d == null:
			continue
		ok(d.lore != "", "%s has lore" % id)
		ok(X.wants_x(d) or not d.traits.is_empty() or not d.attacks.is_empty(), "%s has a mechanic" % id)
		for a in d.attacks:
			if a.has("summon"):
				ok(DB.enemy(a.summon) != null, "%s summons a real monster" % id)
	for id in [&"bone_thrall", &"void_rift", &"leechling", &"mirror_image"]:
		ok(DB.enemy(id) != null, "helper %s registered" % id)
	for b in [&"cellar_king", &"goblin_king", &"ossuarch", &"ironjaw", &"waxen_queen", &"sump_tyrant", &"thornmother",
			&"buried_sovereign", &"voltaric", &"hollow_dark", &"prism_colossus", &"hoard_maw", &"twin_regent", &"coiled_wyrm", &"oblivore"]:
		var d := DB.enemy(b)
		ok(d != null and d.archetype == &"boss" and d.phases.size() == 3, "boss %s has three phases" % b)
	done()

func _begin() -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "slot": Game.save_slot}
	Game.save_slot = 96
	_holder = Node3D.new()
	_holder.name = "Bh013World"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "BestiaryTest")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"start")
	_player.bind(Game.hero)
	Enemy._corpses.clear()
	var dir := CombatDirector.new()
	dir.name = "CombatDirector"
	dir.configure(DataEnemies.DIFFICULTY[1])
	Game.current_map.add_child(dir)
	await _frames(2)

func _end() -> void:
	for e in _tree().get_nodes_in_group(&"enemy") + _tree().get_nodes_in_group(&"corpse") + _tree().get_nodes_in_group(&"bh_minion") \
			+ _tree().get_nodes_in_group(&"sapper_mine"):
		if is_instance_valid(e):
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
	Game.save_slot = _saved.slot
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null
	Enemy._corpses.clear()

func _at(ahead: float, side := 0.0) -> Vector3:
	var p := _player.global_position + Vector3(side, 0, ahead)
	return CombatQuery.ground_at(_player.get_world_3d(), p)

func _spawn(id: StringName, pos: Vector3, lvl := 5) -> Enemy:
	var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(id), lvl, [], pos, DataEnemies.DIFFICULTY[1])
	e.patrol_radius = 0.0
	e.set_physics_process(false)
	return e

func _engage(e: Enemy, t: Actor) -> void:
	e.target = t
	e.brain.go(EnemyBrain.State.ALERT)
	e.brain.go(EnemyBrain.State.CHASE)
	e._dist = e.global_position.distance_to(t.global_position)
	e._has_los = true

func _tick(e: Enemy, seconds: float) -> void:
	for i in int(round(seconds / DT)):
		if is_instance_valid(e) and e.ext:
			e.ext.tick(DT)

func _hit(a: Actor, amount: float, element := Elements.PHYSICAL, attacker: Node = null) -> DamageResult:
	var r := DamageRequest.new()
	r.kind = DamageRequest.Kind.SPELL
	var st := TestCase.blank_stats(10)
	st.values[&"accuracy_chance"] = 1.0
	r.attacker = st
	r.base_min = amount
	r.base_max = amount
	r.can_crit = false
	r.evadable = false
	r.blockable = false
	r.knockback = 0.0
	if element != Elements.PHYSICAL:
		r.conversion = {element: 1.0}
	return a.receive_hit(r, attacker)

func _attack(d: EnemyDef, id: StringName) -> Dictionary:
	for a in d.attacks:
		if a.id == id:
			return a
	return {}

func _ability(d: EnemyDef, id: StringName) -> Dictionary:
	for a in d.abilities:
		if a.id == id:
			return a
	return {}

func test_g_summoners() -> void:
	await _begin()
	var g := _spawn(&"gravecaller", _at(9.0))
	_engage(g, _player)
	var a := _attack(g.def, &"bone_circle")
	g.ext.bone_circle(a)
	eq(g.ext.alive_minions(&"bone_thrall"), 0, "thralls wait for the circle to fill")
	_tick(g, 1.4)
	eq(g.ext.alive_minions(&"bone_thrall"), 3, "three bone thralls rise")
	for i in 4:
		g.ext.bone_circle(a)
		_tick(g, 1.4)
	ok(g.ext.alive_minions(&"bone_thrall") <= int(a.cap), "thralls are capped (%d)" % g.ext.alive_minions(&"bone_thrall"))
	var thralls: Array = g.ext.minions.filter(func(m): return is_instance_valid(m) and m.alive)
	g.die(_player)
	ok(thralls.all(func(m): return not is_instance_valid(m) or not m.alive), "bound thralls crumble with their caller")
	# riftcaller
	var r := _spawn(&"riftcaller", _at(10.0, 4.0))
	_engage(r, _player)
	r.ext.open_rift(_attack(r.def, &"tear"))
	_tick(r, 1.0)
	eq(r.ext.alive_minions(&"void_rift"), 1, "the riftcaller tears a rift open")
	var rift: Enemy = r.ext.minions.filter(func(m): return is_instance_valid(m) and m.def.id == &"void_rift").front()
	rift.set_physics_process(false)
	var shade: Enemy = rift.ext.rift_pulse()
	ok(shade != null and shade.def.id == &"shade_stalker", "the rift releases a shade")
	for i in 6:
		rift.ext.rift_pulse()
	ok(rift.ext.alive_minions(&"shade_stalker") <= 3, "rift shades are capped (%d)" % rift.ext.alive_minions(&"shade_stalker"))
	r.die(_player)
	ok(not rift.alive, "the rift closes when its caller dies")
	# hive
	var nest := _spawn(&"hive_nest", _at(-9.0))
	var drone: Enemy = nest.ext.hive_pulse()
	ok(drone != null and drone.def.id == &"hive_drone", "the hive releases a drone")
	for i in 8:
		nest.ext.hive_pulse()
	ok(nest.ext.alive_minions(&"hive_drone") <= 4, "drones are capped")
	# broodhost
	var bh := _spawn(&"broodhost", _at(-6.0, 5.0))
	_hit(bh, bh.max_hp() * 0.6)
	bh.ext.tick(DT)
	eq(bh.ext.alive_minions(&"leechling"), 2, "a badly hurt broodhost sheds two leechlings")
	bh.die(_player)
	eq(bh.ext.alive_minions(&"leechling"), 6, "its death releases four more")
	await _end()
	done()

func test_h_splitter_and_images() -> void:
	await _begin()
	var o := _spawn(&"gloam_ooze", _at(8.0))
	var kids: Array = o.ext.split()
	eq(kids.size(), 2, "an ooze splits in two")
	var k0: Enemy = kids[0]
	ok(k0.max_hp() < o.max_hp(), "the halves are weaker")
	var grand: Array = k0.ext.split()
	eq(grand.size(), 2, "a half splits again")
	var last: Array = (grand[0] as Enemy).ext.split()
	eq(last.size(), 0, "the third generation does not split")
	var w := _spawn(&"mirage_weaver", _at(6.0, -4.0))
	_engage(w, _player)
	var imgs: Array = w.ext.conjure_images(2)
	eq(imgs.size(), 2, "the weaver conjures two images")
	var before := w.global_position
	ok(w.ext._try_swap(), "struck, the weaver swaps with an image")
	ok(w.global_position.distance_to(before) > 0.5, "the weaver moved")
	var img: Enemy = imgs[0]
	_hit(img, 1.0)
	ok(not img.alive, "an image breaks at a touch")
	await _end()
	done()

func test_i_burrow_tether_link_storm() -> void:
	await _begin()
	var m := _spawn(&"tunnel_maw", _at(10.0))
	_engage(m, _player)
	m.ext.burrow()
	ok(m.invulnerable and not m.is_in_group(&"enemy"), "a burrowed maw is untargetable")
	m.ext.erupt()
	_tick(m, X.ERUPT_WARN + 0.1)
	ok(not m.invulnerable and m.is_in_group(&"enemy"), "it surfaces after erupting")
	# blood tether
	var b := _spawn(&"bloodbinder", _at(6.0, 3.0))
	_engage(b, _player)
	_hit(b, b.max_hp() * 0.5)
	var hp0 := b.hp
	var php := _player.hp
	b.ext.start_tether(_attack(b.def, &"tether"))
	ok(b.ext.tethering(), "the tether latches")
	_tick(b, 1.6)
	ok(_player.hp < php, "the tether drains the hero")
	ok(b.hp > hp0, "and heals the binder")
	_player.global_position = b.global_position + Vector3(0, 0, X.TETHER_RANGE + 4.0)
	_tick(b, 0.1)
	ok(not b.ext.tethering(), "distance breaks the tether")
	_player.global_position = _at(0.0)
	# aegis link
	var ac := _spawn(&"aegis_acolyte", _at(-6.0))
	var tank := _spawn(&"orc_reaver", _at(-6.0, 3.0))
	ac.ext.link(tank)
	ok(tank.status.has(&"aegis_link"), "the acolyte links an ally")
	var r1 := _hit(tank, 100.0).total
	ac.die(_player)
	ok(not tank.status.has(&"aegis_link"), "the link breaks when the acolyte falls")
	var r2 := _hit(tank, 100.0).total
	ok(r1 < r2 * 0.4, "linked it takes far less (%d vs %d)" % [r1, r2])
	# storm herald static
	var s := _spawn(&"storm_herald", _at(12.0, -5.0))
	for i in 2:
		s.ext.add_static(_player)
	ok(_player.status.has(&"static_charge") and not _player.status.has(&"stunned"), "two charges only charge")
	eq(s.ext.add_static(_player), X.STATIC_STACKS, "the third charge overloads")
	ok(_player.status.has(&"stunned"), "overcharged heroes are stunned")
	_player.status.remove(&"stunned")
	await _end()
	done()

func test_j_defences() -> void:
	await _begin()
	var mk := _spawn(&"mirror_knight", _at(4.0))
	mk.look_at(_player.global_position, Vector3.UP, true)
	mk.status.apply(&"mirror_guard", 3.0)
	var php := _player.hp
	var guarded := _hit(mk, 100.0, Elements.PHYSICAL, _player).total
	ok(_player.hp < php, "the mirror reflects damage back")
	mk.status.remove(&"mirror_guard")
	var open := _hit(mk, 100.0, Elements.PHYSICAL, _player).total
	ok(guarded < open, "the mirror guard reduces frontal damage (%d vs %d)" % [guarded, open])
	# briar thorns
	var br := _spawn(&"briar_lasher", _at(-4.0))
	ok(br.status.has(&"aura_thorns"), "the lasher's hide is thorned")
	# gloomwraith phase
	var gw := _spawn(&"gloomwraith", _at(8.0, 5.0))
	gw.ext.set_ethereal(true)
	eq(_hit(gw, 50.0).total, 0, "ethereal ignores physical blows")
	var fire := _hit(gw, 20.0, Elements.FIRE).total
	gw.ext.set_ethereal(false)
	var fire2 := _hit(gw, 20.0, Elements.FIRE).total
	ok(fire > fire2, "ethereal takes more from elements (%d vs %d)" % [fire, fire2])
	# shellback curl
	var sg := _spawn(&"shellback_grinder", _at(8.0, -5.0))
	var flat := _hit(sg, 100.0).total
	sg.ext.set_curled(true)
	var curled := _hit(sg, 100.0).total
	ok(curled < flat * 0.3, "curled it shrugs off blows (%d vs %d)" % [curled, flat])
	sg.ext.flip()
	ok(not sg.ext.curled and sg.status.has(&"stagger_window"), "a flipped grinder is exposed")
	await _end()
	done()

func test_k_twins_rally_gaze_beam_mines_gremlin() -> void:
	await _begin()
	var t1 := _spawn(&"soulbound_twin", _at(6.0))
	var t2 := _spawn(&"soulbound_twin", _at(6.0, 2.0))
	X.pair(t1, t2)
	t1.die(_player)
	_tick(t2, X.TWIN_REKINDLE + 0.2)
	ok(t1.alive, "a fallen twin is rekindled by the other")
	# chieftain
	var c := _spawn(&"warband_chieftain", _at(-8.0))
	var orc := _spawn(&"orc_reaver", _at(-8.0, 3.0))
	ok(c.ext.rally(8.0) >= 2, "the war cry rallies the band")
	ok(orc.status.has(&"haste") and orc.status.has(&"empowered"), "rallied orcs are hasted and empowered")
	c.die(_player)
	ok(orc.status.has(&"feared"), "the chieftain's death breaks its band")
	# basilisk
	var bs := _spawn(&"stonegaze_basilisk", _at(6.0, -4.0))
	var got := false
	for i in 8:
		got = bs.ext.petrify_buildup(_player, X.GAZE_BUILD) or got
	ok(got and _player.status.has(&"petrified"), "a held gaze petrifies")
	_player.status.remove(&"petrified")
	# prism beam
	var ps := _spawn(&"prism_sentinel", _at(10.0, 6.0))
	_engage(ps, _player)
	ps.ext.start_beam(_attack(ps.def, &"sweep"))
	var d0: Vector3 = ps.ext.beam_dir()
	_tick(ps, 1.5)
	ok(ps.ext.beam_dir().angle_to(d0) > deg_to_rad(30.0), "the beam sweeps")
	_tick(ps, 2.0)
	ok(ps.ext._beam.is_empty(), "the beam ends")
	# sapper
	var sp := _spawn(&"goblin_sapper", _at(-5.0, -5.0))
	_engage(sp, _player)
	var mine: Node3D = sp.ext.plant_mine(_attack(sp.def, &"mine"))
	ok(mine != null, "the sapper plants a mine")
	for i in 6:
		sp.ext.plant_mine(_attack(sp.def, &"mine"))
	ok(sp.ext.mines.size() <= 4, "mines are capped")
	# gremlin
	var gr := _spawn(&"treasure_gremlin", _at(5.0, 0.0))
	gr.ext._alerted_t = 0.0
	_tick(gr, X.GREMLIN_ESCAPE + 0.2)
	ok(gr.ext.escaped, "a gremlin left alone escapes")
	await _end()
	done()
