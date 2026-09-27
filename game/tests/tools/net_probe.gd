extends Node
## Two-machine multiplayer probe (bh-008). Run two copies on one PC:
##   godot --path game --resolution 960x540 res://tests/tools/net_probe.tscn -- --role=host --class=knight --slot=94 --map=ruined_forest --out=<dir>
##   godot --path game --resolution 960x540 res://tests/tools/net_probe.tscn -- --role=join --class=mage --slot=93 --map=sanctuary --out=<dir>
## The host opens its world and walks up to a camp; the client joins over 127.0.0.1, follows the host's map, and
## attacks the nearest replica. Both print NET lines (peers, avatars, replicas, kills, HP) and save screenshots.
## bh-010 (--bh10=1): the client joins with the host's ROOM CODE; a Knight host switches on Aura of Might and the client
## logs whether its own hero carries it; the host plants a Goblin Summoner whose summons must appear on the client;
## both log ping. A third copy with --role=join --proto=1 must be refused with a clear message.

var args := {}
var role := "host"
var out := ""
var kills := 0
var hits_taken := 0

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/net")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.tscn").instantiate())
	Events.actor_died.connect(func(a: Node, _k: Node) -> void:
		if a is Enemy:
			kills += 1)
	_run.call_deferred()

func _run() -> void:
	for i in 300:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await _wait(0.1)
	await _wait(1.0)
	var p := Game.player as Player
	p.hit_taken.connect(func(_r) -> void: hits_taken += 1)
	Game.god_mode = false
	if role == "host":
		var err := Net.host_game()
		_log("hosted err='%s'" % err)
		if args.get("bh10", "") == "1" and Game.hero.cls.id == &"knight":
			Game.hero.skill_tree.ranks[&"aura_might"] = 3
			Game.hero._skills_changed()
			p.toggle_aura(&"aura_might")
			_log("aura on: %s" % Game.hero.active_aura)
		# stand a few metres from the nearest monster so the client has something to fight
		var e := _nearest_enemy(p)
		if e:
			var dir := (p.global_position - e.global_position).slide(Vector3.UP).normalized()
			p.global_position = e.global_position + dir * 9.0
			_log("host moved near %s" % e.name)
		for t in 45:
			await _wait(1.0)
			if t % 5 == 0:
				_status()
				for av in Net.avatars():
					_log("avatar %s key=%s model=%s ping=%d" % [av.display_name, av.key, String(av.visual.appearance.get("model", "")) if av.visual else "", Net.ping_ms(av.owner_peer)])
			if t == 12 and args.get("bh10", "") == "1" and DB.enemy(&"goblin_summoner") != null:
				var sp := p.global_position + p.forward() * 7.0
				var gs := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"goblin_summoner"), Game.hero.progress.level, [], sp, DataEnemies.DIFFICULTY[1])
				_log("planted goblin_summoner %s" % (gs.name if gs else "FAILED"))
			if t == 20:
				await _shot("host_t20")
		await _shot("host_end")
	else:
		await _wait(3.0)
		var addr := "127.0.0.1"
		if args.get("bh10", "") == "1":
			addr = NetCodec.room_code("127.0.0.1", Net.PORT, Net.PORT)
		if args.has("proto"):
			Net.protocol_override = int(args.proto)
		var err := Net.join_game(addr)
		_log("join via '%s' err='%s'" % [addr, err])
		if args.has("proto"):
			await _wait(4.0)
			_log("old-version join: mode=%s last_error='%s'" % [Net.mode, Net.last_error])
			print("NET_DONE ", role)
			get_tree().quit()
			return
		for i in 150:
			if Net.is_client() and not Net.connecting and not Net.following and Game.current_map_id == &"ruined_forest" and not Game.travelling:
				break
			await _wait(0.1)
		await _wait(2.5)
		_status()
		_log("aura on client hero: %s · ping to host %d ms" % [p.status.has(&"aura_might"), Net.ping_ms(1)])
		await _shot("client_joined")
		# fight: aim at the nearest replica and hold attack
		var hp0 := 0.0
		var target: Enemy = null
		for t in 30:
			p = Game.player as Player
			target = _nearest_enemy(p)
			if target:
				if hp0 == 0.0:
					hp0 = target.hp
				if p.global_position.distance_to(target.global_position) > 2.2:
					p.global_position = target.global_position + (p.global_position - target.global_position).slide(Vector3.UP).normalized() * 1.8
				p.aim_override = target.global_position
				Input.action_press(&"primary")
			await _wait(0.5)
			if t % 4 == 0:
				_status()
				var defs := {}
				for e in Net._replicas.values():
					if is_instance_valid(e):
						defs[String(e.def.id)] = int(defs.get(String(e.def.id), 0)) + 1
				_log("replicas by kind %s" % str(defs))
				if target and is_instance_valid(target):
					_log("target %s hp %.0f (start %.0f) alive=%s" % [target.name, target.hp, hp0, target.alive])
			if t == 8:
				await _shot("client_fighting")
		Input.action_release(&"primary")
		await _shot("client_end")
		# the client tries to take a waypoint: refused while in the party
		Game.travel(&"sanctuary", &"start")
		await _wait(0.5)
		_log("after travel attempt map=%s" % Game.current_map_id)
		Net.leave()
		await _wait(4.0)
		_log("left: mode=%s map=%s enemies=%d" % [Net.mode, Game.current_map_id, get_tree().get_nodes_in_group(&"enemy").size()])
	_status()
	print("NET_DONE ", role)
	get_tree().quit()

func _nearest_enemy(p: Node3D) -> Enemy:
	var best: Enemy = null
	var bd := INF
	for e in get_tree().get_nodes_in_group(&"enemy"):
		var d: float = e.global_position.distance_to(p.global_position)
		if e.alive and d < bd:
			bd = d
			best = e
	return best

func _status() -> void:
	var p := Game.player as Player
	_log("mode=%d peers=%d avatars=%d replicas=%d enemies=%d kills=%d hits_taken=%d hp=%.0f/%.0f map=%s xp=%d" % [
		Net.mode, Net.peers.size(), Net.avatars().size(), Net._replicas.size(), get_tree().get_nodes_in_group(&"enemy").size(),
		kills, hits_taken, p.hp if p else 0.0, p.max_hp() if p else 0.0, Game.current_map_id, Game.hero.progress.total_xp if Game.hero else 0])

func _log(s: String) -> void:
	print("NET[%s] %s" % [role, s])

func _wait(t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
