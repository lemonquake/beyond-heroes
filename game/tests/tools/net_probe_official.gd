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
		if String(args.get("trade", "")) in ["items", "cancel"]:
			_give_items(hero, user)
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
		if String(args.get("trade", "")) in ["items", "cancel"]:
			add_child(UIRoot.new())         # the trade table and the request box
			await get_tree().process_frame
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
	if String(args.get("trade", "")) in ["items", "cancel"]:
		if not await _real_trade(user, String(args.trade)):
			return
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

# ---- bh-041: a real trade through the trade table, with equipment ---------------------------------------------------
## --trade=items: the two players (userids ending in a / b) trade through the real request, offer and accept steps.
## Player b is "late": it carries an unsaved change when it accepts, so its save reaches the server while a's
## approval is already pending (the race that used to disconnect players). --trade=cancel: a withdraws while the
## exchange is being confirmed; both must end in the same state (both traded or neither) and stay connected.

func _give_items(hero: HeroData, user: String) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(user)
	var n := 0
	for r in [BH.Rarity.ADVANCED, BH.Rarity.MYTHICAL, BH.Rarity.LEGENDARY]:
		var b := ItemGenerator.random_base(rng, 30, [&"weapon", &"armor", &"helm", &"gloves"], &"knight", 1.0)
		if b:
			var it := ItemGenerator.generate(b, 30, r, rng)
			it.custom_name = "%s gift %d" % [user, n]
			hero.inventory.add(it)
			n += 1

func _gifts(user: String) -> Array:
	var out := []
	for c in Game.hero.inventory.cells:
		if c != null and c.custom_name.begins_with(user + " gift"):
			out.append(c)
	return out

func _real_trade(user: String, mode: String) -> bool:
	var first := user.ends_with("a")
	var other := 0
	for id in Net.peers:
		if id != Net.my_id():
			other = int(id)
	var mine_items: Array = _gifts(user)
	if mine_items.size() < 2:
		_fail("trade probe items missing (%d)" % mine_items.size())
		return false
	var give: Array = mine_items.slice(0, 2) if first else mine_items.slice(0, 1)
	var my_gold := 25 if first else 5
	var their_gold := 5 if first else 25
	var start_gold := Game.hero.inventory.gold
	var friend := user.left(user.length() - 1) + ("b" if first else "a")
	if first:
		await get_tree().create_timer(1.0, true).timeout
		var err := Net.request_trade(other)
		if err != "":
			_fail("trade request: " + err)
			return false
	else:
		if not await _wait_until(func() -> bool: return Game.ui_root and Game.ui_root.request_box.visible, 20.0):
			_fail("the Trade Request never arrived")
			return false
		Game.ui_root.request_box._confirm()
	if not await _wait_until(func() -> bool: return Net.in_trade() and Net.trade.phase == "open", 20.0):
		_fail("the trade table did not open")
		return false
	var err2 := Net.trade_set_offer(my_gold, give)
	if err2 != "":
		_fail("offer: " + err2)
		return false
	var want := 1 if first else 2
	if not await _wait_until(func() -> bool: return Net.in_trade() and int(Net.trade.theirs.gold) == their_gold and Net.trade.theirs.items.size() == want, 20.0):
		_fail("the other offer never showed")
		return false
	if first:
		Net.trade_accept(true)
	else:
		# the late player: something unsaved (a kill's experience) when it accepts, a moment after the other did
		await _wait_until(func() -> bool: return Net.in_trade() and Net.trade.their_ok, 20.0)
		await get_tree().create_timer(0.8, true).timeout
		Game.hero.progress.add_xp(7)
		Official._pending = {"version": SaveSystem.CURRENT_VERSION, "hero": Game.hero.to_dict()}
		Official.probe_latency = 1.5            # a friend far away: its save reaches the server after a's approval
		Net.trade_accept(true)
	if mode == "cancel" and first:
		# withdraw as soon as this side is confirming with the server
		await _wait_until(func() -> bool: return not Net.in_trade() or Net.trade.has("trade_id"), 20.0)
		if Net.in_trade():
			Net.trade_cancel("The probe withdrew.")
	if not await _wait_until(func() -> bool: return not Net.in_trade(), 70.0):
		_fail("the trade never finished")
		return false
	await get_tree().create_timer(1.5, true).timeout
	Official.probe_latency = 0.0
	if not Official.connected or Official._fatal:
		_fail("the trade disconnected this player: " + Official.last_error)
		return false
	var traded := Game.hero.inventory.gold == start_gold - my_gold + their_gold
	var unchanged := Game.hero.inventory.gold == start_gold
	if not traded and not unchanged:
		_fail("gold is neither traded nor unchanged: %d (was %d)" % [Game.hero.inventory.gold, start_gold])
		return false
	var got := _gifts(friend).size()
	var kept := _gifts(user).size()
	if traded and (got != (2 if not first else 1) or kept != mine_items.size() - give.size()):
		_fail("items did not move with the gold: received %d, kept %d" % [got, kept])
		return false
	if unchanged and (got != 0 or kept != mine_items.size()):
		_fail("items moved without the gold")
		return false
	if mode == "items" and not traded:
		_fail("the trade did not complete")
		return false
	print("OFFICIAL_PROBE TRADE_OUTCOME %s %s" % [user, "committed" if traded else "cancelled"])
	# keep playing: a normal save must go through after the trade
	Game.hero.progress.add_xp(3)
	if not await Official.flush():
		_fail("saving after the trade failed: " + Official.last_error)
		return false
	print("OFFICIAL_PROBE TRADE PASS ", user)
	return true

