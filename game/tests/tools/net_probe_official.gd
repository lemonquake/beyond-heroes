extends Node
## Real HTTPS + ENet integration client. Test accounts only; no local player saves are read/written.

var args := {}

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--") and arg.contains("="):
			args[arg.substr(2).get_slice("=", 0)] = arg.get_slice("=", 1)
	_run.call_deferred()

func _fail(message: String) -> void:
	print("OFFICIAL_PROBE FAIL ", message)
	get_tree().quit(1)

func _wait_until(predicate: Callable, seconds := 30.0) -> bool:
	var deadline := Time.get_ticks_msec() + int(seconds * 1000)
	while Time.get_ticks_msec() < deadline:
		if predicate.call():
			return true
		await get_tree().create_timer(0.1, true).timeout
	return false

func _run() -> void:
	Official.url = String(args.get("url", "https://127.0.0.1:18443"))
	Official.certificate_path = String(args.get("certificate", "res://server/official_ca.crt"))
	var user := String(args.get("userid", "probe_player"))
	var result := await Official.authenticate("login" if args.get("resume", "0") == "1" else "register", user, "test-only-long-password-2026")
	if result.has("error"):
		_fail(String(result.error))
		return
	var cid := ""
	if args.get("resume", "0") == "1":
		if Official.characters.is_empty():
			_fail("Saved character missing after server restart")
			return
		cid = String(Official.characters[0].id)
	else:
		var hero := Game.new_hero(&"knight", "Probe" + user.right(2))
		TempoRules.grant_starter(hero)
		result = await Official.add_character(hero, 0)
		if result.has("error"):
			_fail(String(result.error))
			return
		cid = String(result.character.id)
	result = await Official.begin_character(cid)
	if result.has("error"):
		_fail(String(result.error))
		return
	Game.hero = HeroData.from_dict(result.save.hero)
	Game.save_slot = -1
	if args.get("resume", "0") == "1" and Game.hero.inventory.gold != 321:
		_fail("Committed progress did not survive restart")
		return
	if args.get("full", "0") == "1":
		var world := Node3D.new()
		add_child(world)
		Game.world_parent = world
		await Game._begin_session(&"sanctuary", &"waypoint")
	else:
		Game.current_map_id = &"sanctuary"
		Game.in_session = true
	var error := Net.join_game("127.0.0.1", int(result.get("game_port", 24690)))
	if error != "":
		_fail(error)
		return
	if not await _wait_until(func() -> bool: return Official.connected):
		_fail("Dedicated game handshake timed out: " + Net.last_error)
		return
	var expected := int(args.get("expected", "1"))
	if not await _wait_until(func() -> bool: return Net.player_count() == expected):
		_fail("Roster contains %d players; expected %d" % [Net.player_count(), expected])
		return
	if Net.peers.has(1):
		_fail("Coordinator was counted as a player")
		return
	if args.get("full", "0") == "1" and expected > 1:
		if not await _wait_until(func() -> bool:
			for id in Net.peers:
				if id != Net.my_id() and Net.avatar(id) == null:
					return false
			return true):
			_fail("Reliable appearance and movement did not create the other player's avatar")
			return
	Game.hero.inventory.gold = 321
	Game.hero.progress.add_xp(50)
	if not await Official.flush():
		_fail("Progress was not acknowledged: " + Official.last_error)
		return
	print("OFFICIAL_PROBE READY ", user, " roster=", Net.player_count(), " revision=", Official.revision)
	if args.get("trade", "0") == "1":
		var other := 0
		for id in Net.peers:
			if id != Net.my_id():
				other = int(id)
		var my_gold := 25 if user.ends_with("00") else 5
		var their_gold := 5 if user.ends_with("00") else 25
		var mine := {"gold": my_gold, "items": []}
		Net.trade = {"peer": other, "name": "Probe friend", "phase": "open", "mine": mine,
			"theirs": {"gold": their_gold, "items": []}, "rev": 0, "their_rev": 0, "my_ok": true,
			"their_ok": true, "committing": false, "their_ready": false, "sent": TradeRules.to_wire(mine)}
		Net._trade_check()
		var deadline := Time.get_ticks_msec() + 40000
		while Net.in_trade() and Time.get_ticks_msec() < deadline:
			if Net.trade.has("server_nonce"):
				Net._trade_ready.rpc_id(other, String(Net.trade.server_nonce))
			await get_tree().create_timer(0.2, true).timeout
		if Net.in_trade() or Game.hero.inventory.gold != 321-my_gold+their_gold:
			_fail("Atomic official trade did not settle both inventories: " + Official.last_error)
			return
		print("OFFICIAL_PROBE TRADE PASS ", user)
	var hold := float(args.get("hold", "5"))
	await get_tree().create_timer(hold, true).timeout
	if not await Official.flush():
		_fail("Final save failed")
		return
	if args.get("full", "0") == "1":
		await Game.end_session()
		if Game.in_session or Official.active:
			_fail("Official session did not save and close cleanly")
			return
	else:
		await Official.release_character()
		Net.leave(false)
	print("OFFICIAL_PROBE PASS ", user)
	get_tree().quit()
