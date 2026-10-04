extends Node
## Class Transcendence on the official server: two real clients against the account service and the dedicated
## coordinator (server/integration_probe.py --stages transcend starts both and these two windows). Test accounts only.
##   --role=a  a Knight, level 121 (imported). Joins first, advances to Royal Guard and waits for the server's save
##             acknowledgement, then (after B has seen it) to Grand Paladin, then tries a forged sibling switch, which
##             the server must refuse.
##   --role=b  a Hunter, level 121. Joins late (after A's Royal Guard is saved), checks the class line under A's
##             name in every state, changes map, reconnects (release, new ticket), and logs when it first saw each class
##             so the stage can compare it with A's acknowledgement time.
## Synchronised through marker files in --out/marks. Prints TCO[role] ok/FAIL lines, ACK / SEEN timestamps (unix ms).

var args := {}
var role := "a"
var out := ""
var fails: Array = []

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--") and arg.contains("="):
			args[arg.substr(2).get_slice("=", 0)] = arg.get_slice("=", 1)
	role = String(args.get("role", "a"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence/official")))
	DirAccess.make_dir_recursive_absolute(out.path_join("marks"))
	Settings.first_person = false
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("TCO[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

static func _now() -> int:
	return int(Time.get_unix_time_from_system() * 1000.0)

func _mark(name: String) -> void:
	var fa := FileAccess.open(out.path_join("marks").path_join(name), FileAccess.WRITE)
	if fa:
		fa.store_string(str(_now()))

func _await_mark(name: String, limit := 120.0) -> bool:
	return await _until(func() -> bool: return FileAccess.file_exists(out.path_join("marks").path_join(name)), limit)

func _until(pred: Callable, limit := 30.0) -> bool:
	var deadline := Time.get_ticks_msec() + int(limit * 1000.0)
	while Time.get_ticks_msec() < deadline:
		if pred.call():
			return true
		await get_tree().create_timer(0.1, true).timeout
	return pred.call()

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("official_%s_%s.png" % [role, label]))
	print("TCO[%s] shot %s" % [role, label])

func _other() -> int:
	for id in Net.peers:
		if int(id) != Net.my_id():
			return int(id)
	return 0

func _line() -> String:
	var av := Net.avatar(_other())
	return av._sub.text if av and av._sub else ""

func _master_class() -> StringName:
	var av := Net.avatar(_other())
	return av.class_id if av and DataTranscendence.stage_of(av.class_id) >= 2 else &""

func _finish() -> void:
	print("TCO[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

func _run() -> void:
	Official.url = String(args.get("url", "https://127.0.0.1:18443"))
	Official.certificate_path = String(args.get("certificate", "res://server/official_ca.crt"))
	var user := String(args.get("userid", "tc_" + role))
	var result := await Official.authenticate("register", user, "test-only-long-password-2026")
	if result.has("error"):
		result = await Official.authenticate("login", user, "test-only-long-password-2026")
	_check("signed in (%s)" % result.get("error", ""), not result.has("error"))
	var hero := Game.new_hero(&"knight" if role == "a" else &"ranger", "Trans" + role.to_upper())
	hero.progress.add_xp(XpCurve.total_xp_for_level(121))
	TempoRules.grant_starter(hero)
	result = await Official.add_character(hero, 0, "tc-probe-import-" + user)
	_check("imported a level-121 character (%s)" % result.get("error", ""), not result.has("error"))
	var cid := String(result.get("character", {}).get("id", ""))
	_check("the account card shows the starting class", String(result.get("character", {}).get("current_class", "")) == ("knight" if role == "a" else "ranger"))
	if role == "b":
		_check("A's Royal Guard was saved before B joins", await _await_mark("a_rg_acked", 180.0))
	result = await Official.begin_character(cid)
	_check("play ticket (%s)" % result.get("error", ""), not result.has("error"))
	Game.hero = HeroData.from_dict(result.save.hero)
	Game.save_slot = -1
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	await Game._begin_session(&"sanctuary", &"waypoint")
	(Game.player as Player).set_first_person(false)
	(Game.player as Player).camera._dist_target = 10.0
	Game.god_mode = true
	var err := Net.join_game("127.0.0.1", int(result.get("game_port", 24690)))
	_check("joined the official game (%s)" % err, err == "")
	_check("handshake", await _until(func() -> bool: return Official.connected, 40.0))
	if role == "a":
		await _role_a()
	else:
		await _role_b()
	_finish()

func _role_a() -> void:
	var res := TranscendFlow.advance(&"royal_guard")
	_check("advanced to Royal Guard locally", res.ok)
	_check("the server acknowledged the Royal Guard save", await _until(func() -> bool: return TranscendFlow.pending == &"", 40.0))
	print("TCO[a] ACK royal_guard %d" % _now())
	_mark("a_rg_acked")
	_check("B joined and saw Royal Guard", await _await_mark("b_saw_rg", 240.0))
	await _until(func() -> bool: return Net.avatar(_other()) != null, 30.0)
	res = TranscendFlow.advance(&"grand_paladin")
	_check("advanced to Grand Paladin locally", res.ok)
	print("TCO[a] LOCAL grand_paladin %d" % _now())
	_check("the server acknowledged the Grand Paladin save", await _until(func() -> bool: return TranscendFlow.pending == &"", 40.0))
	print("TCO[a] ACK grand_paladin %d" % _now())
	_mark("a_gp_acked")
	await get_tree().create_timer(2.0, true).timeout
	await _shot("01_self_grand_paladin")
	_check("B finished its map change and reconnect", await _await_mark("b_done", 300.0))
	# a forged sibling switch: the server must refuse it, and nobody may see Dark General
	Game.hero.transcendence_path = [&"royal_guard", &"dark_general"] as Array[StringName]
	var refused := [false]
	Official.save_finished.connect(func(ok: bool) -> void:
		if not ok:
			refused[0] = true, CONNECT_ONE_SHOT)
	Official.queue_save(Game.hero)
	_check("the server refused the sibling switch (%s)" % Official.last_error, await _until(func() -> bool: return refused[0], 30.0))
	_check("the refusal names the rule", Official.last_error.contains("cannot be undone or changed"))
	_mark("a_forged")
	await get_tree().create_timer(3.0, true).timeout

func _role_b() -> void:
	_check("A's avatar arrived", await _until(func() -> bool: return Net.avatar(_other()) != null and Net.avatar(_other()).visual != null, 60.0))
	_check("late join: Royal Guard under A's name (%s)" % _line(), await _until(func() -> bool: return _line().contains("Royal Guard"), 30.0))
	_check("a first transcendence is not a master class", _master_class() == &"")
	await get_tree().create_timer(1.0, true).timeout
	await _shot("01_late_join_royal_guard")
	_mark("b_saw_rg")
	_check("Grand Paladin shows after A's save (%s)" % _line(), await _until(func() -> bool: return _line().contains("Grand Paladin"), 90.0))
	print("TCO[b] SEEN grand_paladin %d" % _now())
	_check("as a Grand Paladin", await _until(func() -> bool: return _master_class() == &"grand_paladin", 20.0))
	await get_tree().create_timer(1.5, true).timeout
	await _shot("02_sees_grand_paladin")
	# map change
	Game.travel(&"ruined_forest", &"start")
	await _until(func() -> bool: return Game.current_map_id == &"ruined_forest" and not Game.travelling, 90.0)
	await get_tree().create_timer(3.0, true).timeout
	Game.travel(&"sanctuary", &"waypoint")
	await _until(func() -> bool: return Game.current_map_id == &"sanctuary" and not Game.travelling, 90.0)
	_check("after a map change: Grand Paladin (%s)" % _line(), await _until(func() -> bool: return _line().contains("Grand Paladin"), 60.0))
	_check("after a map change: the class", await _until(func() -> bool: return _master_class() == &"grand_paladin", 30.0))
	# reconnect: save, release, new ticket, rejoin
	_check("saved before leaving", await Official.flush())
	var cid := Official.character_id
	await Game.end_session()
	var result := await Official.begin_character(cid)
	_check("a new play ticket after releasing (%s)" % result.get("error", ""), not result.has("error"))
	Game.hero = HeroData.from_dict(result.save.hero)
	Game.save_slot = -1
	await Game._begin_session(&"sanctuary", &"waypoint")
	(Game.player as Player).set_first_person(false)
	(Game.player as Player).camera._dist_target = 10.0
	var err := Net.join_game("127.0.0.1", int(result.get("game_port", 24690)))
	_check("rejoined (%s)" % err, err == "")
	_check("handshake again", await _until(func() -> bool: return Official.connected, 40.0))
	_check("after reconnecting: Grand Paladin at once (%s)" % _line(), await _until(func() -> bool: return _line().contains("Grand Paladin"), 60.0))
	_check("after reconnecting: the class", await _until(func() -> bool: return _master_class() == &"grand_paladin", 30.0))
	await get_tree().create_timer(1.0, true).timeout
	await _shot("03_after_reconnect")
	_mark("b_done")
	# A's forged switch never shows
	_check("A tried a forged switch", await _await_mark("a_forged", 90.0))
	await get_tree().create_timer(4.0, true).timeout
	_check("the refused switch never shows Dark General (%s)" % _line(), not _line().contains("Dark General") and _master_class() != &"dark_general")
	_check("final save", await Official.flush())
	await Game.end_session()
