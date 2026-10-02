extends TestCase
## bh-010 monsters: the ten new enemies and two helpers load and resolve, stay inside the balance band of the existing
## roster, carry every clip they play, and each signature mechanic works headlessly in a live map (the town plaza):
## raise, summon caps, the War Totem pulse, the chill aura, the bloater's burst (hurts heroes and monsters), the
## bombardier's fuse charge, troll regeneration vs fire, rune-shift immunity, web root, the Mimic ambush, plus the hero
## statuses the new skills rely on (feared, marked, stealth). Ends with a 10,000-step churn of spawns, summons and
## deaths that must stay bounded and finite.

const Ext := preload("res://src/actors/enemy/enemy_traits_ext.gd")
const NEW := [&"necromancer", &"goblin_summoner", &"orc_shaman", &"frost_revenant", &"plague_bloater", &"bandit_bombardier",
	&"mire_troll", &"rune_golem", &"broodmother", &"treasure_mimic", &"spiderling", &"war_totem"]
## The existing monster each new one is balanced against (same family or role): hp and damage may not exceed it by >25%.
const REFERENCE := {&"necromancer": &"ashen_cultist", &"goblin_summoner": &"goblin_skulker", &"orc_shaman": &"orc_reaver",
	&"frost_revenant": &"orc_reaver", &"plague_bloater": &"ghoul_brute", &"bandit_bombardier": &"bandit_marksman",
	&"mire_troll": &"ghoul_brute", &"rune_golem": &"aether_sentinel", &"broodmother": &"ghoul_brute",
	&"treasure_mimic": &"orc_reaver", &"spiderling": &"goblin_skulker", &"war_totem": &"goblin_skulker"}
const MATERIALS := [&"flesh", &"ichor", &"bone", &"stone", &"aether", &"shadow"]
const STYLES := [&"fall", &"crumple", &"ash", &"collapse", &"implode", &"smoke"]
const KINDS := ["melee", "projectile", "aoe", "dash", "charge", "pools", "summon", "chain", "tongue"]
const ABILITY_KINDS := ["heal", "buff", "shield", "teleport", "raise", "summon", "totem", "ward"]
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

# ---- Live-map scaffolding (same pattern as test_tempos) -----------------------------------------------------------

func _begin() -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "slot": Game.save_slot}
	Game.save_slot = 96                      # never a real save slot (0-2)
	_holder = Node3D.new()
	_holder.name = "Enemies2World"
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
	var dir := CombatDirector.new()          # towns have none; the attack-token logic must be live for these tests
	dir.name = "CombatDirector"
	dir.configure(DataEnemies.DIFFICULTY[1])
	Game.current_map.add_child(dir)
	await _frames(2)

func _end() -> void:
	for e in _tree().get_nodes_in_group(&"enemy") + _tree().get_nodes_in_group(&"corpse") + _tree().get_nodes_in_group(&"bh_minion"):
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

## A point `ahead` metres from the hero (towards -Z, where the plaza is open: a wall stands within 3 m of the start point
## towards +Z, so a monster placed there has no line of sight and its ranged and chain attacks never connect) and `side`
## metres to the side, on the ground.
func _at(ahead: float, side := 0.0) -> Vector3:
	var p := _player.global_position + Vector3(side, 0, -ahead)
	return CombatQuery.ground_at(_player.get_world_3d(), p)

func _spawn(id: StringName, pos: Vector3, lvl := 5, frozen := true) -> Enemy:
	var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(id), lvl, [], pos, DataEnemies.DIFFICULTY[1])
	e.patrol_radius = 0.0
	if frozen:
		e.set_physics_process(false)     # the test drives it by hand
	return e

func _engage(e: Enemy, t: Actor) -> void:
	e.target = t
	e.brain.go(EnemyBrain.State.ALERT)
	e.brain.go(EnemyBrain.State.CHASE)
	e._dist = e.global_position.distance_to(t.global_position)
	e._has_los = true

func _step(list: Array, seconds: float) -> void:
	for i in int(round(seconds / DT)):
		for e in list:
			if is_instance_valid(e):
				e._physics_process(DT)

func _hit(a: Actor, amount: float, element := Elements.PHYSICAL) -> DamageResult:
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
	return a.receive_hit(r, null)

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

# ---- Data -------------------------------------------------------------------------------------------------------

func test_defs_load_and_resolve() -> void:
	for id in NEW:
		var d: EnemyDef = DB.enemy(id)
		ok(d != null, "%s defined" % id)
		if d == null:
			continue
		ok(d.display_name != "" and d.lore != "" and d.role_name != "", "%s has a name, role and lore" % id)
		ok(MATERIALS.has(d.hit_material), "%s hit material %s" % [id, d.hit_material])
		ok(STYLES.has(d.death_style), "%s death style %s" % [id, d.death_style])
		ok(d.model.ends_with(".glb"), "%s model path %s" % [id, d.model])
		for t in d.traits:
			ok(Ext.NEW_TRAITS.has(t) or [&"cowardly"].has(t), "%s trait %s is implemented" % [id, t])
		for a in d.attacks:
			ok(KINDS.has(String(a.kind)), "%s: attack %s kind %s is known" % [id, a.id, a.kind])
			ok(not DB.anim(a.anim).is_empty(), "%s: timing metadata for %s" % [id, a.anim])
			if a.kind in ["melee", "dash"]:
				ok(not DB.anim(a.anim).get("hits", []).is_empty(), "%s: %s has hit windows" % [id, a.anim])
			if a.has("summon"):
				ok(DB.enemy(a.summon) != null, "%s summons a known monster" % id)
		for ab in d.abilities:
			ok(ABILITY_KINDS.has(String(ab.kind)), "%s: ability %s kind %s is known" % [id, ab.id, ab.kind])
			if ab.has("summon"):
				ok(DB.enemy(ab.summon) != null, "%s: %s summons a known monster" % [id, ab.id])
			if ab.has("status"):
				ok(StatusRules.DEFS.has(StringName(ab.status)), "%s: %s applies a defined status" % [id, ab.id])
		for l in d.loot:
			ok(DB.item_base(l[0]) != null, "%s drops a real item %s" % [id, l[0]])
		ok(DataGuide.bestiary_entry(id).size() == 3, "%s has a bestiary entry" % id)
	eq(DB.enemy(&"treasure_mimic").display_name, "Mimic", "the Mimic's name")
	ok(DB.enemy(&"spiderling").model.ends_with("broodmother.glb") and is_equal_approx(DB.enemy(&"spiderling").model_scale, 0.42), "spiderlings reuse the broodmother model at 0.42")
	for h in [&"spiderling", &"war_totem", &"treasure_mimic"]:
		ok(not DB.enemy(h).can_be_elite, "%s never rolls elite" % h)
	for id in [&"frost_revenant", &"mire_troll", &"rune_golem", &"necromancer"]:
		ok(DB.enemy(id).can_be_elite, "%s can be an elite / champion" % id)
	done()

func test_balance_against_the_roster() -> void:
	for id in NEW:
		var d: EnemyDef = DB.enemy(id)
		var r: EnemyDef = DB.enemy(REFERENCE[id])
		if d.damage_max <= 0.0:
			# a totem is an objective, not a fighter: it never attacks, so the fighter band for health and defence does not apply
			ok(d.move_speed <= 0.0, "%s deals no damage and does not move" % id)
			continue
		ok(d.hp <= r.hp * 1.25 + 0.01, "%s HP %.0f within 125%% of %s (%.0f)" % [id, d.hp, r.id, r.hp])
		ok(d.damage_max <= r.damage_max * 1.25 + 0.01, "%s damage %.0f within 125%% of %s (%.0f)" % [id, d.damage_max, r.id, r.damage_max])
		ok(d.defense <= maxf(r.defense * 1.25, r.defense + 8.0), "%s defense %.0f near %s (%.0f)" % [id, d.defense, r.id, r.defense])
		var best := 0.0
		for a in d.attacks:
			best = maxf(best, float(a.get("mult", 1.0)) * float(a.get("count", 1)) * (0.7 if int(a.get("count", 1)) > 1 else 1.0))
		ok(best <= 2.2, "%s: no single attack beyond 2.2x its damage (%.2f)" % [id, best])
	done()

## Every model exists and has the clips the game asks it to play (creatures: their own prefixed clips).
func test_models_have_every_clip() -> void:
	for id in NEW:
		var d: EnemyDef = DB.enemy(id)
		ok(ResourceLoader.exists(d.model), "%s model %s exists" % [id, d.model])
		if not ResourceLoader.exists(d.model):
			continue
		var inst: Node = (load(d.model) as PackedScene).instantiate()
		var ap := inst.find_children("*", "AnimationPlayer", true, false)
		ok(not ap.is_empty(), "%s has an AnimationPlayer" % id)
		if ap.is_empty():
			inst.free()
			continue
		var player: AnimationPlayer = ap[0]
		var need := [&"idle", &"hit_light", &"death"]
		if d.body_shape == &"humanoid":
			need.append_array([&"walk", &"run", &"death_back", &"death_fwd", &"death_crumple", &"hit_front", &"hit_back", &"stagger_small", &"knockback", &"alert"])
		elif d.body_shape != &"totem":
			need.append_array([&"walk", &"run"])
		for a in d.attacks:
			need.append(a.anim)
		for ab in d.abilities:
			if ab.has("anim"):
				need.append(ab.anim)
		if d.traits.has(&"mimic"):
			need.append_array([&"mimic_dormant", &"mimic_wake"])
		if d.traits.has(&"totem"):
			need.append_array([&"totem_pulse", &"alert"])
		for n in need:
			ok(player.has_animation(n), "%s model has clip %s" % [id, n])
		inst.free()
	done()

# ---- Mechanics ----------------------------------------------------------------------------------------------------

func test_raise_dead_makes_capped_risen() -> void:
	await _begin()
	var n := _spawn(&"necromancer", _at(8.0))
	ok(n.ext != null, "the necromancer has trait code")
	var bodies: Array = []
	for i in 5:
		var b := _spawn(&"bandit_cutthroat", _at(6.0, -4.0 + i * 2.0))
		bodies.append(b)
	await _frames(1)
	for b in bodies:
		b.die(null)
	ok((bodies[0] as Enemy).is_fresh_corpse(), "a fresh corpse")
	ok(n.ext.fresh_corpse(12.0) != null, "the necromancer finds a fresh body nearby")
	var r: Enemy = n.ext.raise(bodies[0])
	ok(r != null and r.risen and r.display_name == "Risen", "a corpse becomes a Risen")
	if r:
		var fresh := _spawn(&"hollow_soldier", _at(12.0), r.level)
		fresh.ensure_stats()
		r.ensure_stats()
		ok(r.max_hp() < fresh.max_hp(), "Risen are weaker than a hollow soldier (%.0f < %.0f)" % [r.max_hp(), fresh.max_hp()])
		ok(r.def.id == &"hollow_soldier" and r.is_in_group(&"enemy"), "the Risen reuses the hollow soldier and fights")
		ok(not (bodies[0] as Enemy).is_fresh_corpse(), "the raised body is used up")
		fresh.free()
	for b in bodies.slice(1):
		n.ext.raise(b)
	ok(n.ext.alive_minions(&"hollow_soldier") <= 3, "raising is capped at 3 (%d)" % n.ext.alive_minions(&"hollow_soldier"))
	eq(n.ext.alive_minions(&"hollow_soldier"), 3, "the cap is reached with bodies to spare")
	# a dead Risen stays dead: it is not a fresh corpse and never reassembles
	if r:
		r.die(null)
		ok(not r.is_fresh_corpse() and not r._reassembling, "a Risen cannot be raised or reassemble again")
	# the real ability path: telegraph, cast, rise on the release frame
	var m2 := _spawn(&"necromancer", _at(-8.0))
	var body := _spawn(&"bandit_cutthroat", _at(-6.0))
	await _frames(1)
	body.die(null)
	_engage(m2, _player)
	ok(m2.ext.try_ability(_ability(m2.def, &"raise")), "the raise ability starts a cast")
	ok(m2.action != null and body.has_meta(&"raising"), "the body is marked while the spell is cast")
	for i in 180:
		if m2.action and not m2.action.step(DT):
			m2._end_attack(true)
	eq(m2.ext.alive_minions(&"hollow_soldier"), 1, "the Risen stands up when the cast releases")
	await _end()
	done()

func test_summon_is_telegraphed_and_capped() -> void:
	await _begin()
	var g := _spawn(&"goblin_summoner", _at(9.0))
	_engage(g, _player)
	var ab := _ability(g.def, &"burrow")
	ok(g.ext.try_ability(ab), "the burrow ability starts")
	eq(g.ext.alive_minions(), 0, "nothing comes out before the burrow telegraph ends")
	for i in int(1.5 / DT):
		g.ext.tick(DT)
	eq(g.ext.alive_minions(&"goblin_skulker"), 2, "two skulkers climb out of the burrow")
	for k in 4:
		g.action = null
		g.cooldowns.clear()
		g.brain.go(EnemyBrain.State.POSITION)
		g.ext.try_ability(ab)
		for i in int(1.5 / DT):
			g.ext.tick(DT)
	ok(g.ext.alive_minions(&"goblin_skulker") <= 3, "summoned skulkers are capped at 3 (%d)" % g.ext.alive_minions(&"goblin_skulker"))
	# the broodmother's eggs
	var b := _spawn(&"broodmother", _at(-9.0))
	_engage(b, _player)
	ok(b.ext.try_ability(_ability(b.def, &"lay_brood")), "the broodmother lays eggs")
	for i in int(1.4 / DT):
		b.ext.tick(DT)
	var n: int = b.ext.alive_minions(&"spiderling")
	ok(n >= 2 and n <= 4, "2-4 spiderlings hatch (%d)" % n)
	await _end()
	done()

func test_war_totem_pulses_until_destroyed() -> void:
	await _begin()
	var s := _spawn(&"orc_shaman", _at(10.0))
	var orc := _spawn(&"orc_reaver", _at(10.0, 3.0))
	_engage(s, _player)
	var totem: Enemy = s.ext.plant_totem(_at(10.0, 1.5))
	ok(totem != null and totem.def.id == &"war_totem", "the shaman plants a War Totem")
	await _frames(1)
	ok(totem.is_in_group(&"enemy"), "the totem is a target")
	totem.set_physics_process(false)
	orc.status.remove(&"empowered")
	_step([totem], Ext.PULSE + 0.2)
	ok(orc.status.has(&"empowered"), "the totem's pulse Empowers orcs nearby")
	var start := totem.global_position
	for i in 20:
		totem.apply_knockback(Vector3.FORWARD, 12.0, null, null)
		_step([totem], 0.05)
	ok(totem.global_position.distance_to(start) < 0.3, "the totem does not move")
	totem.die(_player)
	orc.status.remove(&"empowered")
	_step([totem], Ext.PULSE * 2.0)
	ok(not orc.status.has(&"empowered"), "a destroyed totem pulses no more")
	eq(s.ext.alive_minions(&"war_totem"), 0, "the shaman may plant another")
	await _end()
	done()

func test_chill_aura_and_shatter() -> void:
	await _begin()
	var r := _spawn(&"frost_revenant", _at(2.5))
	_player.status.remove(&"chilled")
	eq(r.ext.chill_pulse(), 1, "the aura reaches the hero within 4 m")
	ok(_player.status.has(&"chilled"), "the hero is Chilled")
	_player.status.remove(&"chilled")
	r.global_position = _at(10.0)
	eq(r.ext.chill_pulse(), 0, "nothing beyond the aura")
	ok(not _player.status.has(&"chilled"), "far away the hero stays warm")
	r.global_position = _at(2.5)
	_step([r], 1.2)
	ok(_player.status.has(&"chilled"), "the aura works through the normal tick")
	var before := _tree().get_nodes_in_group(&"telegraph").size()
	r.die(_player)
	ok(_tree().get_nodes_in_group(&"telegraph").size() > before, "it shatters with a telegraphed ice burst")
	await _end()
	done()

func test_bloater_burst_hurts_heroes_and_monsters() -> void:
	await _begin()
	var b := _spawn(&"plague_bloater", _at(3.0))
	var orc := _spawn(&"orc_reaver", _at(4.5, 1.0))
	b.hp = b.max_hp() * 0.3
	b.ext.tick(DT)
	ok(b.ext.swollen, "a badly hurt bloater swells first (the warning)")
	var hurt := [0]       # hits that reached the hero (HP cannot be compared: the kill levels the hero up, which heals and raises it)
	_player.hit_taken.connect(func(_r: DamageResult) -> void: hurt[0] += 1)
	orc.ensure_stats()
	var orc_hp := orc.hp
	b.die(_player)
	ok(_tree().get_nodes_in_group(&"telegraph").size() > 0, "its burst is telegraphed")
	await _tree().create_timer(Ext.BURST_DELAY + 0.4).timeout
	ok(hurt[0] > 0, "the burst hurts the hero (%d hit%s landed)" % [hurt[0], "" if hurt[0] == 1 else "s"])
	ok(orc.hp < orc_hp, "and the monster beside it (%.0f -> %.0f)" % [orc_hp, orc.hp])
	var clouds := _tree().get_nodes_in_group(&"hazard").filter(func(h): return h.mask & BH.LAYER_ENEMY != 0)
	ok(not clouds.is_empty(), "it leaves a toxic cloud that also poisons monsters")
	await _end()
	done()

func test_bombardier_lights_its_keg() -> void:
	await _begin()
	var b := _spawn(&"bandit_bombardier", _at(12.0))
	_engage(b, _player)
	b.ext.tick(DT)
	ok(not b.ext.fuse_lit, "no fuse while healthy")
	b.hp = b.max_hp() * 0.25
	b.ext.tick(DT)
	ok(b.ext.fuse_lit and b.status.has(&"lit_fuse"), "below 30%% HP it lights the powder keg")
	b.ensure_stats()
	ok(b.stats.get_stat(&"move_speed") > b.def.move_speed * 1.3, "and runs faster")
	ok(b.ext.think(), "the lit keg takes over its decisions")
	eq(b.brain.state, EnemyBrain.State.CHASE, "it charges the hero")
	for i in int((Ext.KEG_FUSE + 0.2) / DT):
		if b.alive:
			b.ext.tick(DT)
	ok(not b.alive, "when the fuse burns down the keg explodes and kills it")
	# on contact
	var c := _spawn(&"bandit_bombardier", _at(1.2))
	_engage(c, _player)
	var hurt := [0]       # the kill levels the hero up (a full heal), so count hits instead of comparing HP
	_player.hit_taken.connect(func(_r: DamageResult) -> void: hurt[0] += 1)
	c.hp = c.max_hp() * 0.2
	c.ext.tick(DT)
	c.ext.tick(DT)
	ok(not c.alive, "touching the hero sets it off at once")
	ok(hurt[0] > 0, "the blast hurts the hero (%d hit%s landed)" % [hurt[0], "" if hurt[0] == 1 else "s"])
	await _end()
	done()

func test_troll_regen_stops_after_fire() -> void:
	await _begin()
	var t := _spawn(&"mire_troll", _at(12.0))
	t.ensure_stats()
	ok(t.status.has(&"troll_regen"), "Troll Blood shows as a status")
	t.hp = t.max_hp() * 0.5
	var h0 := t.hp
	for i in 60:
		t.ext.tick(DT)
	ok(t.hp > h0 + t.max_hp() * 0.01, "it regenerates (%.1f -> %.1f)" % [h0, t.hp])
	_hit(t, 10.0, Elements.FIRE)
	ok(not t.status.has(&"troll_regen") and t.ext.bar_note().size() == 2, "fire stops it, visibly")
	var h1 := t.hp
	for i in int(3.6 / DT):
		t.ext.tick(DT)
	ok(t.hp <= h1 + 0.001, "no regeneration for ~4 s after fire (%.1f -> %.1f)" % [h1, t.hp])
	for i in int(1.0 / DT):
		t.ext.tick(DT)
	ok(t.hp > h1 and t.status.has(&"troll_regen"), "regeneration resumes afterwards")
	await _end()
	done()

func test_rune_shift_immunity_and_weakness() -> void:
	await _begin()
	var g := _spawn(&"rune_golem", _at(12.0))
	for step in 3:
		var el: int = g.ext.rune_element()
		eq(el, Ext.RUNE_CYCLE[step], "rune %d is %s" % [step, Elements.NAMES[Ext.RUNE_CYCLE[step]]])
		ok(g.status.has(&"rune_immune"), "the Rune Shift status shows")
		g.ensure_stats()
		g.hp = g.max_hp()
		var imm := _hit(g, 60.0, el)
		eq(imm.total, 0, "immune to %s" % Elements.NAMES[el])
		g.hp = g.max_hp()
		var weak := _hit(g, 60.0, Ext.RUNE_OPPOSITE[el])
		g.hp = g.max_hp()
		var plain := _hit(g, 60.0, Elements.WIND)
		ok(weak.total > plain.total, "weak to %s (%d > %d)" % [Elements.NAMES[Ext.RUNE_OPPOSITE[el]], weak.total, plain.total])
		ok(String(g.ext.bar_note()[0]).contains(Elements.NAMES[el]), "the bar names the current element")
		eq(g._atk_element(_attack(g.def, &"rune_fist")), el, "its blows carry the rune's element")
		if not g.ext._emissive.is_empty():
			var s: Array = g.ext._emissive[0]
			var m := (s[0] as MeshInstance3D).get_surface_override_material(int(s[1])) as StandardMaterial3D
			ok(m != null and m.emission.is_equal_approx(Elements.color(el)), "the BH_Emissive core glows %s" % Elements.NAMES[el])
		g.ext.shift_rune()
	eq(g.ext.rune_element(), Elements.FIRE, "the cycle wraps back to Fire")
	# it shifts on its own while fighting, with a warning first
	_engage(g, _player)
	g.ext.rune_t = 0.0
	for i in int((Ext.RUNE_PERIOD + 0.1) / DT):
		g.ext.tick(DT)
	eq(g.ext.rune_element(), Elements.ICE, "after one period the core has shifted")
	await _end()
	done()

func test_web_spit_roots_the_hero() -> void:
	await _begin()
	var b := _spawn(&"broodmother", _at(6.0))
	b.ensure_stats()
	_engage(b, _player)
	b._face_now(_player.global_position)
	var web := _attack(b.def, &"web_spit")
	_player.status.remove(&"webbed")
	var webbed := false
	for shot in 6:
		b._fire(web)
		await _frames(30)
		if _player.status.has(&"webbed"):
			webbed = true
			break
	ok(webbed, "a web spit that connects applies Webbed")
	_player.status.remove(&"webbed")
	var res := DamageResult.new()
	b.apply_hit_statuses(_player, res, {&"webbed": 2.0})
	ok(_player.status.has(&"webbed"), "Webbed is applied directly, not through buildup")
	res.evaded = true
	_player.status.remove(&"webbed")
	b.apply_hit_statuses(_player, res, {&"webbed": 2.0})
	ok(not _player.status.has(&"webbed"), "a dodged web does nothing")
	await _end()
	done()

func test_mimic_sleeps_then_ambushes() -> void:
	await _begin()
	var m := _spawn(&"treasure_mimic", _at(6.0))
	await _frames(1)
	ok(m.ext.dormant, "a Mimic starts dormant")
	ok(not m.is_in_group(&"enemy"), "dormant: not an enemy for auto-target, the minimap or Tempos")
	ok(m.bar == null, "dormant: no health bar or name plate")
	ok(_player.pick_auto_target() != m, "auto-target ignores it")
	_step([m], 0.5)
	ok(m.ext.dormant, "still asleep at 6 m")
	m.global_position = _at(3.0)
	_step([m], 0.3)
	ok(not m.ext.dormant, "it wakes when the hero comes within 3.5 m")
	ok(m.is_in_group(&"enemy") and m.bar != null and m.brain.is_engaged(), "awake it is a normal, engaged enemy with a bar")
	var m2 := _spawn(&"treasure_mimic", _at(-9.0))
	await _frames(1)
	_hit(m2, 5.0)
	ok(not m2.ext.dormant, "hitting a Mimic wakes it too")
	# tongue pull: the hero is dragged toward the mouth
	m.global_position = _at(5.0)
	m.ensure_stats()
	_engage(m, _player)
	var pulled := false
	for i in 12:
		_player.knock_velocity = Vector3.ZERO
		m._face_now(_player.global_position)
		if m.ext.tongue(_attack(m.def, &"tongue")):
			var toward := (m.global_position - _player.global_position).slide(Vector3.UP).normalized()
			pulled = _player.knock_velocity.normalized().dot(toward) > 0.9 and _player.knock_velocity.length() > 3.0
			break
	ok(pulled, "the tongue pulls the hero toward the Mimic")
	ok(DB.enemy(&"treasure_mimic").gold.x >= 30 and DB.enemy(&"treasure_mimic").drop_chance >= 1.0, "Mimics carry rich loot")
	await _end()
	done()

func test_bone_ward_absorbs() -> void:
	await _begin()
	var o := _spawn(&"orc_reaver", _at(10.0))
	o.ensure_stats()
	o.hp = o.max_hp()
	o.apply_bone_ward(30.0, 8.0)
	ok(o.status.has(&"bone_ward") and is_equal_approx(o.shield_hp, 30.0), "Bone Ward adds a 30-point shield")
	var hp0 := o.hp
	_hit(o, 20.0, Elements.LIGHTNING)
	ok(is_equal_approx(o.hp, hp0), "the ward absorbs the blow")
	ok(o.shield_hp < 30.0 and o.shield_hp > 0.0, "and is worn down (%.1f left)" % o.shield_hp)
	o.status.remove(&"bone_ward")
	ok(is_zero_approx(o.shield_hp), "when it expires the rest of the ward is gone")
	# the necromancer's ability puts it on an engaged ally
	var n := _spawn(&"necromancer", _at(10.0, 2.0))
	_engage(n, _player)
	_engage(o, _player)
	o.hp = o.max_hp() * 0.5
	ok(n.ext.try_ability(_ability(n.def, &"bone_ward")), "the necromancer casts Bone Ward")
	for i in 120:
		if n.action and not n.action.step(DT):
			n._end_attack(true)
	ok(o.status.has(&"bone_ward"), "on the most hurt ally")
	await _end()
	done()

func test_chain_lightning_strikes() -> void:
	await _begin()
	var s := _spawn(&"orc_shaman", _at(8.0))
	s.ensure_stats()
	_engage(s, _player)
	s._face_now(_player.global_position)
	var hp0 := _player.hp
	var hits := 0
	for i in 8:
		hits = maxi(hits, s.ext.chain(_attack(s.def, &"chain_lightning")))
		if _player.hp < hp0:
			break
	ok(hits >= 1, "chain lightning reaches the hero")
	ok(_player.hp < hp0, "and hurts (%.0f -> %.0f)" % [hp0, _player.hp])
	s.global_position = _at(40.0)
	eq(s.ext.chain(_attack(s.def, &"chain_lightning")), 0, "out of range it fizzles")
	await _end()
	done()

# ---- Hero statuses on monsters ----------------------------------------------------------------------------------

func test_feared_enemy_flees_and_does_not_attack() -> void:
	await _begin()
	var o := _spawn(&"orc_reaver", _at(2.0))
	o.ensure_stats()
	_engage(o, _player)
	o.status.apply(&"feared", 2.5)
	var d0 := o.global_position.distance_to(_player.global_position)
	var attacked := false
	for i in int(1.5 / DT):
		o._physics_process(DT)
		if o.action != null or not o.current_attack.is_empty():
			attacked = true
	ok(not attacked, "a feared monster never starts an attack")
	eq(o.brain.state, EnemyBrain.State.RETREAT, "it retreats")
	ok(o.global_position.distance_to(_player.global_position) > d0 + 1.0, "and runs away (%.1f -> %.1f m)" % [d0, o.global_position.distance_to(_player.global_position)])
	# control: without fear the same monster does attack
	var o2 := _spawn(&"orc_reaver", _at(-2.0))
	o2.ensure_stats()
	_engage(o2, _player)
	var attacked2 := false
	for i in int(2.5 / DT):
		o2._physics_process(DT)
		if o2.action != null:
			attacked2 = true
			break
	ok(attacked2, "control: an unafraid orc does attack")
	var boss := _spawn(&"boss_warden", _at(-14.0))
	boss.status.apply(&"feared", 3.0)
	ok(not boss.status.has(&"feared"), "bosses are immune to fear")
	await _end()
	done()

func test_marked_enemy_takes_more_damage() -> void:
	await _begin()
	var o := _spawn(&"orc_reaver", _at(10.0))
	o.ensure_stats()
	o.hp = o.max_hp()
	var plain := _hit(o, 40.0, Elements.WIND).total
	o.hp = o.max_hp()
	o.status.apply(&"marked", 8.0, 25.0, 0.0, Elements.PHYSICAL, [StatModifier.more(&"damage_taken", 0.25, "Mark")])
	o.ensure_stats()
	var marked := _hit(o, 40.0, Elements.WIND).total
	ok(marked >= int(plain * 1.2), "Marked adds damage taken (%d -> %d)" % [plain, marked])
	await _end()
	done()

func test_stealth_loses_the_monster_within_a_second() -> void:
	await _begin()
	var o := _spawn(&"orc_reaver", _at(6.0))
	o.ensure_stats()
	_engage(o, _player)
	o._select_target(DT)
	eq(o.target, _player, "it hunts the hero")
	_player.status.apply(&"stealth", 4.0)
	var lost_at := -1.0
	for i in 60:
		o._physics_process(DT)
		if o.target != _player:
			lost_at = i * DT
			break
	ok(lost_at >= 0.0 and lost_at <= 1.0, "stealth loses the hero within 1 s (%.2f s)" % lost_at)
	_player.status.remove(&"stealth")
	o._retarget_t = 0.0
	o._select_target(DT)
	eq(o.target, _player, "out of stealth the hero is found again")
	await _end()
	done()

# ---- Churn --------------------------------------------------------------------------------------------------------

## 10,000 steps at 60 Hz: casters summon and raise, minions and summoners die and respawn, corpses pile up and decay.
## Positions stay finite and every cap holds.
func test_churn_spawn_summon_despawn() -> void:
	await _begin()
	_player.invulnerable = true
	var ids := [&"necromancer", &"goblin_summoner", &"broodmother", &"orc_shaman"]
	var casters := {}
	for i in ids.size():
		casters[ids[i]] = _spawn(ids[i], _at(9.0, -6.0 + i * 4.0), 5, false)
	var bad_pos := 0
	var worst_enemies := 0
	var worst_minions := 0
	var cap_broken := 0
	var respawns := 0
	var summons := 0
	for step in 10000:
		# summoners act on a fixed rhythm (on top of their own AI)
		if step % 45 == 0:
			for id in ids:
				var c: Enemy = casters[id]
				if not is_instance_valid(c) or not c.alive:
					casters[id] = _spawn(id, _at(9.0, -6.0 + ids.find(id) * 4.0), 5, false)
					respawns += 1
					continue
				c.target = _player
				c.brain.go(EnemyBrain.State.CHASE)
				match id:
					&"necromancer":
						var corpse: Enemy = c.ext.fresh_corpse(40.0)
						if corpse and c.ext.raise(corpse):
							summons += 1
					&"goblin_summoner":
						if c.ext.alive_minions(&"goblin_skulker") < 3:
							c.ext.summon_at(_at(7.0, -4.0), &"goblin_skulker", 3 - c.ext.alive_minions(&"goblin_skulker"), 0.4, "burrow", 3)
							summons += 1
					&"broodmother":
						if c.ext.alive_minions(&"spiderling") < 4:
							c.ext.summon_at(_at(7.0, 3.0), &"spiderling", 4 - c.ext.alive_minions(&"spiderling"), 0.4, "eggs", 4)
							summons += 1
					&"orc_shaman":
						if c.ext.alive_minions(&"war_totem") < 1:
							c.ext.plant_totem(_at(11.0, 6.0))
							summons += 1
		# deaths: a minion every 20 steps, a summoner every 1,500
		if step % 20 == 10:
			var mins := _tree().get_nodes_in_group(&"bh_minion").filter(func(m): return is_instance_valid(m) and m.alive)
			if not mins.is_empty():
				(mins[step % mins.size()] as Enemy).die(_player)
		if step % 1500 == 1499:
			var c2: Enemy = casters[ids[(step / 1500) % ids.size()]]
			if is_instance_valid(c2) and c2.alive:
				c2.die(_player)
		for e in _tree().get_nodes_in_group(&"enemy"):
			if is_instance_valid(e):
				e._physics_process(DT)
		if step % 60 == 0:
			_player.hp = _player.max_hp()
		if step % 100 == 0:
			var alive_e := 0
			for e in Game.current_map.find_children("*", "", true, false):
				if e is Enemy and is_instance_valid(e):
					if not (e as Enemy).global_position.is_finite():
						bad_pos += 1
					if (e as Enemy).alive:
						alive_e += 1
			worst_enemies = maxi(worst_enemies, alive_e)
			worst_minions = maxi(worst_minions, Ext.global_minions(_tree()))
			for id in ids:
				var c3: Enemy = casters[id]
				if is_instance_valid(c3) and c3.alive:
					if c3.ext.alive_minions(&"hollow_soldier") > 3 or c3.ext.alive_minions(&"goblin_skulker") > 3 \
							or c3.ext.alive_minions(&"spiderling") > 4 or c3.ext.alive_minions(&"war_totem") > 1:
						cap_broken += 1
			await _tree().process_frame           # let freed bodies and effects go
	eq(bad_pos, 0, "every monster position stays finite")
	eq(cap_broken, 0, "no caster ever exceeds its cap")
	ok(worst_minions <= Ext.GLOBAL_MINION_CAP, "summoned monsters stay under the global cap (max %d)" % worst_minions)
	ok(worst_enemies <= ids.size() + Ext.GLOBAL_MINION_CAP, "living monsters stay bounded (max %d)" % worst_enemies)
	ok(summons > 50, "the churn really summoned (%d summons, %d caster respawns)" % [summons, respawns])
	ok(_tree().get_nodes_in_group(&"corpse").size() <= Enemy.MAX_CORPSES, "corpses stay bounded (%d)" % _tree().get_nodes_in_group(&"corpse").size())
	_player.invulnerable = false
	await _end()
	done()
