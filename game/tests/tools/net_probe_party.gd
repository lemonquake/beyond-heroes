extends Node
## Two-machine party probe (bh-011). Run two copies on one PC:
##   godot --path game --resolution 1280x720 res://tests/tools/net_probe_party.tscn -- --role=host --class=knight --slot=94 --map=ruined_forest --out=<dir>
##   godot --path game --resolution 1280x720 res://tests/tools/net_probe_party.tscn -- --role=join --class=ranger --slot=93 --map=sanctuary --out=<dir>
## Checks, each printed as PARTY[role] ok/FAIL lines:
##   party frames on both HUDs; a ping reaches the other machine; the client falls and the host revives it with
##   Interact; the host falls and respawns without rebuilding the shared map (the client is not dragged through a
##   loading screen); the client takes a waypoint -> the host is asked -> Go -> both arrive; Regroup puts a separated
##   client beside the host; the host sends the client home.
## bh-015: clients now travel on their own, so the "asked to lead the party" step no longer happens; the new rules
## (independent exploring, Summon Party) are covered by net_probe_explore.gd.

var args := {}
var role := "host"
var out := ""
var fails: Array = []
var maps_loaded := 0

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/party")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.tscn").instantiate())
	Events.map_loaded.connect(func(_m: StringName) -> void: maps_loaded += 1)
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("PARTY[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

func _log(s: String) -> void:
	print("PARTY[%s] %s" % [role, s])

func _run() -> void:
	for i in 400:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await _wait(0.1)
	await _wait(1.0)
	Game.god_mode = false
	if role == "host":
		await _host()
	else:
		await _client()
	print("PARTY[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

# ---- host ---------------------------------------------------------------------------------------------------------

func _host() -> void:
	var p := Game.player as Player
	var err := Net.host_game()
	_check("hosted (%s)" % err, err == "")
	# a quiet spot: the arrival glade, monsters far away
	var joined := false
	for i in 400:
		if Net.player_count() >= 2 and Net.avatars().size() > 0:
			joined = true
			break
		await _wait(0.1)
	_check("the client joined and its hero appears", joined)
	var hud: Hud = Game.ui_root.hud
	await _wait(1.5)
	_check("host HUD shows a party frame for the client (%d rows)" % hud.party_frames._rows.size(), hud.party_frames._rows.size() == 1)
	Game.ui_root.open(&"multiplayer")
	await _wait(2.5)
	await _shot("host_multiplayer_window")
	Game.ui_root.close_all()
	var saw_ping := false
	var revived := false
	var died_done := false
	var travelled := false
	var revived_at := 0.0
	var t := 0.0
	var kicked := false
	while t < 150.0:
		await _wait(0.2)
		t += 0.2
		p = Game.player as Player
		if not saw_ping:
			for n in (FX.world.get_children() if FX.world else []):
				if n is PingMarker:
					saw_ping = true
					_log("saw the client's ping")
					await _shot("host_sees_ping")
		# the client's hero fell: walk over and revive it
		for av in Net.avatars():
			if av.is_hero and not av.alive and not revived:
				p.teleport_to(av.global_position + Vector3(1.0, 0.0, 0.0))
				await _wait(0.4)
				var target := p.find_interact_target()
				_check("standing beside the fallen friend, Interact offers '%s'" % (target.call(&"interact_text") if target else "nothing"), target == av)
				await _shot("host_revive_prompt")
				p.interact()
				revived = true
				revived_at = t
		# after the revive: the host falls and gets up (the shared map must stay)
		if revived and not died_done and t - revived_at > 6.0:
			died_done = true
			var map_before := Game.current_map
			var loads := maps_loaded
			p.die(null)
			await _wait(1.0)
			await Game.respawn_player()
			await _wait(0.5)
			_check("the host respawned without rebuilding the shared map", Game.current_map == map_before and maps_loaded == loads and (Game.player as Player).alive)
		# a travel request from the client: answer Go
		if Game.ui_root.confirm.visible and Game.ui_root.confirm._title.text == "Party Travel" and not travelled:
			_log("asked: %s" % Game.ui_root.confirm._text.text)
			await _shot("host_travel_request")
			Game.ui_root.confirm._confirm()
			travelled = true
		if travelled and not kicked and Game.current_map_id == &"sanctuary" and not Game.travelling:
			# give the client time to arrive and regroup, then send it home
			var cid := 0
			for id in Net.peers:
				if id != 1:
					cid = id
			if cid != 0 and String(Net.peers[cid].get("map", "")) == "sanctuary":
				await _wait(14.0)
				await _shot("host_in_town")
				Net.kick(cid)
				kicked = true
				await _wait(2.0)
				_check("the client was sent home (%d heroes left)" % Net.player_count(), Net.player_count() == 1)
				break
	_check("the host saw the client's ping", saw_ping)
	_check("the host revived the client", revived)
	_check("the host was asked to lead the party and went", travelled and Game.current_map_id == &"sanctuary")
	Net.leave()

# ---- client -------------------------------------------------------------------------------------------------------

func _client() -> void:
	await _wait(3.0)
	var err := Net.join_game(NetCodec.room_code("127.0.0.1", Net.PORT, Net.PORT))
	_check("join sent (%s)" % err, err == "")
	for i in 300:
		if Net.is_client() and not Net.connecting and not Net.following and Game.current_map_id == &"ruined_forest" and not Game.travelling:
			break
		await _wait(0.1)
	_check("followed the host to the Ruined Forest", Game.current_map_id == &"ruined_forest")
	await _wait(2.5)
	var hud: Hud = Game.ui_root.hud
	_check("client HUD shows the host's party frame (%d rows)" % hud.party_frames._rows.size(), hud.party_frames._rows.size() == 1)
	await _shot("client_party_frames")
	if Settings.touch_mode:
		var tc: TouchControls = Game.ui_root.touch
		_check("touch play shows Ping and Regroup in a party", tc.button(&"ping").is_visible_in_tree() and tc.button(&"regroup").is_visible_in_tree())
	Game.ui_root.open(&"multiplayer")
	await _wait(1.0)
	await _shot("client_multiplayer_window")
	Game.ui_root.close_all()
	await _wait(0.5)
	var p := Game.player as Player
	p.aim_override = p.global_position + p.forward() * 4.0      # a spot both cameras see (the probe's mouse is off-screen)
	await _wait(0.1)
	p.ping_here()
	p.aim_override = Vector3.INF
	await _wait(1.0)
	await _shot("client_ping")
	# fall, wait for the host to revive us
	p.die(null)
	await _wait(0.2)
	_check("the death screen tells you a friend can revive you", Game.ui_root.pause_menu.visible and Game.ui_root.pause_menu._sub.text.contains("revive"))
	await _shot("client_fallen")
	var up := false
	for i in 200:
		if (Game.player as Player).alive:
			up = true
			break
		await _wait(0.1)
	_check("revived by the host, where it fell", up)
	_check("the death screen closed", not Game.ui_root.pause_menu.visible)
	# the host falls and gets up now: this client must not be dragged through a reload
	var loads := maps_loaded
	var map_before := Game.current_map
	await _wait(12.0)
	_check("the host's respawn did not reload this client's map", maps_loaded == loads and Game.current_map == map_before)
	# ask the host to lead the party to town through the waypoint
	var dais := Game.current_map.teleporter(&"forest_waypoint")
	p = Game.player as Player
	p.teleport_to(dais.arrival_point())
	p.on_teleported()
	await _wait(0.6)
	p.interact()
	for i in 600:
		if Game.current_map_id == &"sanctuary" and not Game.travelling and not Net.following:
			break
		await _wait(0.1)
	_check("the party travelled to town after the host said Go (now %s)" % Game.current_map_id, Game.current_map_id == &"sanctuary")
	await _wait(2.0)
	# wander off, then Regroup
	Game.place_player(&"start")
	await _wait(1.0)
	var host_av := Net.avatar(1)
	var far := (Game.player as Node3D).global_position.distance_to(host_av.global_position) if host_av else -1.0
	Net.regroup()
	await _wait(2.0)
	host_av = Net.avatar(1)
	var near := (Game.player as Node3D).global_position.distance_to(host_av.global_position) if host_av else -1.0
	_check("Regroup: %.1f m -> %.1f m from the host" % [far, near], host_av != null and near < 4.0 and far > near)
	await _shot("client_regrouped")
	# wait to be sent home
	for i in 300:
		if not Net.is_active():
			break
		await _wait(0.1)
	_check("sent home by the host: '%s'" % Net.last_error, not Net.is_active() and Net.last_error.contains("sent you back"))

func _wait(t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("%s.png" % name))
