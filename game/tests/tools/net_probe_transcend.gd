extends Node
## Class Transcendence across two real game processes (custom game). Run two copies on one PC (tools/net_probes.py
## "transcend" does it):
##   godot --path game --resolution 960x540 res://tests/tools/net_probe_transcend.tscn -- --role=host --class=knight --level=121 --slot=94 --map=sanctuary --out=<dir>
##   godot --path game --resolution 960x540 res://tests/tools/net_probe_transcend.tscn -- --role=join --class=ranger --level=121 --slot=93 --map=sanctuary --out=<dir>
## The host starts as a Royal Guard (first transcendence); the joiner as a plain Hunter. Checks (TRANSCEND[role]
## ok/FAIL lines), each from the other machine's view of the hero, in the existing class line under the name:
##   first arrival shows the right class; the joiner advances twice in the session (Tracker, then
##   Starstrider) and the host sees each step without a reload; the host advances (Dark General) and the joiner sees it;
##   forged profile claims (another family's path, extra label / colour keys) never show; a gear change re-dresses
##   the avatar and keeps the class; a map change and a reconnect rebuild the avatar with the right class. Each advanced hero
##   wears its class armour, and the other client must see it on their hero.
## Phases are synchronised over chat ("TC:<phase>"). Screenshots from both clients go to --out.

var args := {}
var role := "host"
var out := ""
var fails: Array = []
var phases := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence/net")))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.first_person = false
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("TRANSCEND[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

func _wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [role, label]))
	print("TRANSCEND[%s] shot %s" % [role, label])

func _say(phase: String) -> void:
	Net.send_chat("TC:" + phase)

func _on_chat(_peer: int, text: String) -> void:
	if text.begins_with("TC:"):
		phases[text.substr(3)] = true

func _await_phase(phase: String, limit := 90.0) -> bool:
	var t := 0.0
	while t < limit and not phases.has(phase):
		await _wait(0.1)
		t += 0.1
	return phases.has(phase)

## Poll until `pred` holds (or time runs out); returns whether it held.
func _until(pred: Callable, limit := 30.0) -> bool:
	var t := 0.0
	while t < limit:
		if pred.call():
			return true
		await _wait(0.1)
		t += 0.1
	return pred.call()

func _other() -> int:
	for id in Net.peers:
		if int(id) != Net.my_id():
			return int(id)
	return 0

func _av() -> NetAvatar:
	return Net.avatar(_other())

func _line() -> String:
	var av := _av()
	return av._sub.text if av and av._sub else ""

func _is_master() -> bool:
	var av := _av()
	return av != null and DataTranscendence.stage_of(av.class_id) >= 2

func _master_class() -> StringName:
	var av := _av()
	return av.class_id if av and DataTranscendence.stage_of(av.class_id) >= 2 else &""

## The armour the other player's hero is dressed in on this machine (from their shared appearance).
func _remote_armor() -> StringName:
	var app: Variant = Net._appearance_cache.get("%d:p" % _other(), {})
	var gear: Variant = (app as Dictionary).get("set_gear", {}) if app is Dictionary else {}
	return StringName(String((gear as Dictionary).get("armor", ""))) if gear is Dictionary else &""

## Put on this class's armour (it is shared with the other player like any gear change).
func _wear_class_armor(id: StringName) -> void:
	var it := DB.make_item(id, BH.Rarity.ELITE, 121, 9)
	Game.hero.inventory.add(it)
	_check("equipped %s (%s)" % [id, Game.hero.equip_from_inventory(it)], Game.hero.equipment.get_item(&"armor") == it)
	(Game.player as Player).refresh_equipment_visuals()
	Net.update_profile()

func _run() -> void:
	for i in 600:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await _wait(0.1)
	await _wait(1.0)
	Game.god_mode = true
	var p := Game.player as Player
	p.set_first_person(false)
	p.camera._dist_target = 10.0
	Net.chat_received.connect(_on_chat)
	if role == "host":
		ClassTranscendence.transcend(Game.hero, &"royal_guard")
		p.refresh_class_look()
		await _host()
	else:
		await _join()
	print("TRANSCEND[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

func _host() -> void:
	var err := Net.host_game(24697)
	_check("hosted (%s)" % err, err == "")
	_check("the joiner's avatar arrived", await _until(func() -> bool: return _av() != null and _av().visual != null, 90.0))
	_check("first arrival: the plain Hunter reads Hunter under the name (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Hunter"), 20.0))
	_check("a starting class is not a master class", not _is_master())
	await _wait(1.0)
	await _shot("01_sees_hunter")
	_say("host_ready")
	# the joiner advances twice while the host watches
	_check("same session: Tracker shows (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Tracker"), 60.0))
	_check("a first transcendence has its colour and is not a master class", not _is_master())
	_check("the class line takes the Tracker colour", _av()._sub.modulate.is_equal_approx(ClassTranscendence.label_color(&"tracker")))
	await _shot("02_sees_tracker")
	_check("same session: Starstrider shows (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Starstrider"), 60.0))
	_check("and the Starstrider identity arrives", await _until(func() -> bool: return _master_class() == &"starstrider", 10.0))
	_check("the joiner wears the Constellation Leathers on my screen", await _until(func() -> bool: return _remote_armor() == &"tc_constellation_leathers", 20.0))
	await _wait(1.5)
	await _shot("03_sees_starstrider_armor")
	# the host advances; the joiner watches
	var res := TranscendFlow.advance(&"dark_general")
	_check("host advanced to Dark General", res.ok)
	_wear_class_armor(&"tc_black_dominion_plate")
	_say("host_master")
	# forged claims from the joiner never show
	_check("forged claim sent", await _await_phase("forged", 60.0))
	await _wait(2.0)
	var cid := Net.peer_class_id(_other())
	_check("another family's path is never shown for the joiner (%s)" % cid, DataTranscendence.family_of(cid) == &"ranger")
	_check("no free-text label or colour keys survive", not Net.peers.get(_other(), {}).has("label") and not Net.peers.get(_other(), {}).has("glow"))
	_check("the forged class never shows as a Knight class", not [&"dark_general", &"grand_paladin"].has(_master_class()))
	_check("restored Starstrider after the real profile", await _until(func() -> bool: return _line().begins_with("Level 121 Starstrider"), 20.0))
	# gear change re-dresses and keeps the class
	var rev := _av().appearance_rev
	_check("gear changed", await _await_phase("gear", 60.0))
	_check("the avatar re-dressed after the gear change", await _until(func() -> bool: return _av() != null and _av().appearance_rev != rev, 30.0))
	_check("the class stayed through the re-dress", _master_class() == &"starstrider")
	# map change: the avatar leaves and comes back, rebuilt with the class line
	_check("the joiner went away and came back", await _await_phase("back", 120.0))
	_check("after the map change the class line is right (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Starstrider"), 40.0))
	_check("after the map change the class is back", await _until(func() -> bool: return _master_class() == &"starstrider", 20.0))
	# reconnect
	_check("the joiner reconnected", await _await_phase("rejoined", 120.0))
	_check("after reconnecting the class line is right (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Starstrider"), 40.0))
	_check("after reconnecting the class is back", await _until(func() -> bool: return _master_class() == &"starstrider", 20.0))
	await _wait(1.0)
	await _shot("04_after_reconnect")
	_say("host_done")
	await _await_phase("join_done", 60.0)
	await _wait(1.0)
	Net.leave(false)

func _join() -> void:
	await _wait(3.0)
	var err := Net.join_game("127.0.0.1", 24697)
	_check("joined (%s)" % err, err == "")
	_check("the host's avatar arrived", await _until(func() -> bool: return _av() != null and _av().visual != null, 90.0))
	_check("first arrival: Royal Guard under the host's name (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Royal Guard"), 20.0))
	_check("Royal Guard is not a master class", not _is_master())
	await _wait(1.0)
	await _shot("01_sees_royal_guard")
	await _await_phase("host_ready", 60.0)
	_check("advanced to Tracker", TranscendFlow.advance(&"tracker").ok)
	await _wait(4.0)
	_check("advanced to Starstrider", TranscendFlow.advance(&"starstrider").ok)
	_check("I am a Starstrider now", ClassTranscendence.current_class_id(Game.hero) == &"starstrider")
	_wear_class_armor(&"tc_constellation_leathers")
	# watch the host advance
	_check("host master phase", await _await_phase("host_master", 90.0))
	_check("the host now reads Dark General (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Dark General"), 30.0))
	_check("and is a Dark General", await _until(func() -> bool: return _master_class() == &"dark_general", 10.0))
	_check("the host wears the Black Dominion Plate on my screen", await _until(func() -> bool: return _remote_armor() == &"tc_black_dominion_plate", 20.0))
	await _wait(1.5)
	await _shot("02_sees_dark_general_armor")
	# forged profile claims (the host must clean them)
	var forged := Net._profile()
	forged["path"] = "royal_guard,dark_general"
	forged["label"] = "Emperor of Everything"
	forged["glow"] = "res://evil.gdshader"
	Net._profile_changed.rpc_id(1, forged)
	await _wait(0.6)
	_say("forged")
	await _wait(3.0)
	Net.update_profile()
	# gear change
	await _wait(3.0)
	var bow := DB.make_item(&"tc_starfall_crossbow", BH.Rarity.ELITE, 121, 5)
	Game.hero.inventory.add(bow)
	_check("equipped the Starfall Crossbow (%s)" % Game.hero.equip_from_inventory(bow), Game.hero.equipment.get_item(&"main_weapon") == bow)
	await _wait(1.0)
	_say("gear")
	await _wait(3.0)
	# map change: away and back
	Game.travel(&"ruined_forest", &"start")
	await _until(func() -> bool: return Game.current_map_id == &"ruined_forest" and not Game.travelling, 90.0)
	await _wait(3.0)
	Game.travel(&"sanctuary", &"waypoint")
	await _until(func() -> bool: return Game.current_map_id == &"sanctuary" and not Game.travelling, 90.0)
	await _wait(3.0)
	_check("back home: the host's class line is right (%s)" % _line(), await _until(func() -> bool: return _line().begins_with("Level 121 Dark General"), 40.0))
	_check("back home: the host's class is right", await _until(func() -> bool: return _master_class() == &"dark_general", 20.0))
	_say("back")
	# reconnect
	await _wait(3.0)
	Net.leave(false)
	await _wait(3.0)
	err = Net.join_game("127.0.0.1", 24697)
	_check("rejoined (%s)" % err, err == "")
	_check("after reconnecting the host's class line is right", await _until(func() -> bool: return _line().begins_with("Level 121 Dark General"), 60.0))
	_check("after reconnecting the host's class is right", await _until(func() -> bool: return _master_class() == &"dark_general", 20.0))
	_say("rejoined")
	await _wait(2.0)
	await _shot("03_after_reconnect")
	await _await_phase("host_done", 90.0)
	_say("join_done")
	await _wait(2.0)
	Net.leave(false)
