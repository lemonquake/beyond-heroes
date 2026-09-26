extends Node
## Automated combat playtest with the real Player, real enemies, real physics and the real input actions.
## A bot hero (knight or mage) is dropped into each combat map, walks to the nearest enemy group, aims with
## Player.aim_override and presses the same actions a person would (attack chain, heavy, dodge, guard, skills,
## potions). It records every damage event, kill, death, AI state visited and any script error text it can see.
##   godot --headless --path game res://tests/tools/combat_bot.tscn -- --class=knight --maps=ruined_forest --seconds=60
## Writes <out>/combat_<class>.json (default out: work/lemondev/bh-002/evidence/playtest).

var args := {}
var report := {"maps": {}, "ok": true}
var player: Player
var _press := {}          # action -> release time

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var cls := StringName(args.get("class", "knight"))
	var maps: Array = String(args.get("maps", "ruined_forest,catacombs,forgotten_temple")).split(",")
	var seconds := float(args.get("seconds", "60"))
	var out := String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-002/evidence/playtest")))
	DirAccess.make_dir_recursive_absolute(out)
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	Game.save_slot = 99
	Game.hero = Game.new_hero(cls, "Bot")
	Game.hero.progress.add_xp(int(args.get("xp", "4000")))
	await Game._begin_session(StringName(maps[0]), &"start")
	player = Game.player as Player
	player.input_enabled = true
	for m in maps:
		await _fight_map(StringName(m), seconds)
	report["class"] = String(cls)
	report["level"] = Game.hero.progress.level
	var f := FileAccess.open(out.path_join("combat_%s.json" % cls), FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	print("COMBAT BOT ", "PASS" if report.ok else "FAIL")
	for a in _press.keys():
		Input.action_release(a)
	Game.in_session = false
	get_tree().quit(0 if report.ok else 1)

func _fight_map(id: StringName, seconds: float) -> void:
	if Game.current_map_id != id:
		Game.load_map(id, &"start")
		await _frames(3)
	var r := {"damage_events": 0, "player_hits": 0, "enemy_hits": 0, "crits": 0, "kills": 0, "player_deaths": 0,
		"max_hit": 0.0, "states": {}, "enemies_at_start": get_tree().get_nodes_in_group(&"enemy").size(),
		"skills_cast": 0, "potions": 0, "stuck_s": 0.0, "hp_min_frac": 1.0, "mismatch": 0}
	var on_dmg := func(target: Node, res: DamageResult, _pos: Vector3, attacker: Node) -> void:
		r.damage_events += 1
		if attacker == player:
			r.player_hits += 1
			if res.is_crit:
				r.crits += 1
			r.max_hit = maxf(r.max_hit, float(res.total))
		elif target == player:
			r.enemy_hits += 1
	var on_die := func(actor: Node, _k: Node) -> void:
		if actor == player:
			r.player_deaths += 1
		else:
			r.kills += 1
	var on_skill := func(_s: StringName) -> void: r.skills_cast += 1
	Events.damage_dealt.connect(on_dmg)
	Events.actor_died.connect(on_die)
	player.skill_used.connect(on_skill)
	var t := 0.0
	var dt := 1.0 / Engine.physics_ticks_per_second
	var last := player.global_position
	var still := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	while t < seconds:
		await get_tree().physics_frame
		t += dt
		_release_expired(t)
		if not player.alive:
			await _frames(30)
			Game.god_mode = false
			player.respawn()
			continue
		r.hp_min_frac = minf(r.hp_min_frac, player.hp / player.max_hp())
		for e in get_tree().get_nodes_in_group(&"enemy"):
			if e is Enemy and e.alive:
				r.states[e.brain.state_name()] = int(r.states.get(e.brain.state_name(), 0)) + 1
		var target := _nearest_enemy()
		if target == null:
			_move_toward(Vector3.ZERO, t)
			continue
		var d := player.global_position.distance_to(target.global_position)
		player.aim_override = target.global_position
		var reach := 2.2 if not _ranged() else 9.0
		if d > reach:
			_move_toward(target.global_position, t)
		else:
			_stop_move()
			_tap(&"primary", t, 0.12)
			if rng.randf() < 0.01:
				_tap(&"secondary", t, 0.1)
			if rng.randf() < 0.02:
				var slot := rng.randi_range(1, 4)
				_tap(StringName("skill_%d" % slot), t, 0.1)
		if player.hp < player.max_hp() * 0.35 and rng.randf() < 0.05:
			_tap(&"potion_health", t, 0.05)
			r.potions += 1
		if rng.randf() < 0.004:
			_tap(&"dodge", t, 0.05)
		if player.global_position.distance_to(last) < 0.005 and d > reach:
			still += dt
		last = player.global_position
	r.stuck_s = snappedf(still, 0.1)
	Events.damage_dealt.disconnect(on_dmg)
	Events.actor_died.disconnect(on_die)
	player.skill_used.disconnect(on_skill)
	for a in _press.keys():
		Input.action_release(a)
	_press.clear()
	player.aim_override = Vector3.INF
	var ok: bool = r.player_hits > 0 and r.kills > 0
	r["ok"] = ok
	report.ok = report.ok and ok
	report.maps[String(id)] = r
	print("[%s] %s: %s" % ["OK" if ok else "FAIL", id, JSON.stringify(r)])

func _ranged() -> bool:
	var lo := player.hero.equipment.loadout()
	return lo.main_type != null and lo.main_type.ranged

func _nearest_enemy() -> Enemy:
	var best: Enemy = null
	var bd := INF
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.alive:
			var dd: float = e.global_position.distance_squared_to(player.global_position)
			if dd < bd:
				bd = dd
				best = e
	return best

## Movement goes through the real move actions: convert the world direction to camera-relative WASD.
func _move_toward(p: Vector3, t: float) -> void:
	var nm := player.get_world_3d().navigation_map
	var path := NavigationServer3D.map_get_path(nm, player.global_position, p, true)
	var goal := p
	for q in path:
		if Vector2(q.x - player.global_position.x, q.z - player.global_position.z).length() > 0.8:
			goal = q
			break
	var dir := goal - player.global_position
	dir.y = 0.0
	if dir.length() < 0.1:
		_stop_move()
		return
	dir = dir.normalized()
	var cam := player.camera.global_basis
	var right := Vector3(cam.x.x, 0, cam.x.z).normalized()
	var fwd := Vector3(-cam.z.x, 0, -cam.z.z).normalized()
	var x := dir.dot(right)
	var y := dir.dot(fwd)
	_hold(&"move_right", x > 0.3, t)
	_hold(&"move_left", x < -0.3, t)
	_hold(&"move_up", y > 0.3, t)
	_hold(&"move_down", y < -0.3, t)

func _stop_move() -> void:
	for a in [&"move_right", &"move_left", &"move_up", &"move_down"]:
		if _press.has(a):
			Input.action_release(a)
			_press.erase(a)

func _hold(a: StringName, on: bool, t: float) -> void:
	if on and not _press.has(a):
		Input.action_press(a)
		_press[a] = INF
	elif not on and _press.has(a):
		Input.action_release(a)
		_press.erase(a)

func _tap(a: StringName, t: float, dur: float) -> void:
	if _press.has(a):
		return
	Input.action_press(a)
	_press[a] = t + dur

func _release_expired(t: float) -> void:
	for a in _press.keys():
		if _press[a] <= t:
			Input.action_release(a)
			_press.erase(a)

func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame
