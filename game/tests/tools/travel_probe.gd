extends Node
## Waypoint travel probe (bh-011): boots the real game (optionally in touch mode), walks the hero onto each network
## shrine and presses Interact the way the chosen control mode does (touch: taps the on-screen Interact button;
## pc: an R key event), picks a destination in the waypoint dialog, and logs every monster death and every XP grant
## that happens while travelling. A hero who has fought nothing must gain no experience from travel.
##   godot --path game res://tests/tools/travel_probe.tscn -- --class=knight --slot=96 --touch=1 --lite=1 [--out=<dir>]
## Prints TRAVEL PASS / TRAVEL FAIL and exits 0 / 1.

var args := {}
var out := ""
var deaths: Array = []
var xp_events: Array = []
var fails: Array = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/travel")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.gd").new())
	Events.actor_died.connect(func(a: Node, k: Node) -> void:
		if a is Enemy:
			deaths.append({"map": String(Game.current_map_id), "enemy": String((a as Enemy).def.id), "y": snappedf((a as Node3D).global_position.y, 0.1),
				"killer": String(k.name) if k else "<none>", "travelling": Game.travelling,
				"home": str((a as Enemy).home), "zone": String((a as Enemy).zone.name) if (a as Enemy).zone else "", "name": String(a.name)}))
	Events.xp_gained.connect(func(x: int) -> void:
		xp_events.append({"map": String(Game.current_map_id), "xp": x, "travelling": Game.travelling}))
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print(("  ok   " if ok else "  FAIL ") + label)
	if not ok:
		fails.append(label)

func _run() -> void:
	for i in 900:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(1.0)
	var p := Game.player as Player
	Game.god_mode = true
	for id in DataIsland.NETWORK_SHRINES:
		Game.hero.awakened_shrines[id] = true
	var start_xp := Game.hero.progress.total_xp
	var start_lvl := Game.hero.progress.level
	# the legs: stand on the shrine of the current map, interact, choose the destination
	var legs := [[&"sanctuary_waypoint", &"ruined_forest"], [&"forest_waypoint", &"westreach"], [&"cove_shrine", &"olivar"],
		[&"olivar_shrine", &"wyman_outpost"], [&"wyman_shrine", &"sanctuary"], [&"sanctuary_waypoint", &"ruined_forest"],
		[&"forest_waypoint", &"sanctuary"]]
	var n := 0
	for leg in legs:
		n += 1
		var t: Teleporter = Game.current_map.teleporter(leg[0]) if Game.current_map else null
		_check("leg %d: shrine %s exists on %s" % [n, leg[0], Game.current_map_id], t != null)
		if t == null:
			break
		p.teleport_to(t.arrival_point())
		p.on_teleported()
		await _wait(0.6)
		var shown := _interact_visible()
		_check("leg %d: an Interact prompt is up on the dais" % n, shown)
		if n == 1:
			await _shot("01_on_dais")
		await _press_interact()
		await _wait(0.5)
		if n == 1:
			await _shot("02_waypoint_choice")
		var picked := _pick_destination(leg[1])
		_check("leg %d: waypoint dialog offered %s" % [n, leg[1]], picked)
		for i in 600:
			if Game.current_map_id == leg[1] and not Game.travelling:
				break
			await get_tree().process_frame
		_check("leg %d: arrived on %s (now %s)" % [n, leg[1], Game.current_map_id], Game.current_map_id == leg[1])
		await _wait(2.5)     # monsters settle; anything that falls through the world would die now
	var end_xp := Game.hero.progress.total_xp
	print("DEATHS %d  %s" % [deaths.size(), JSON.stringify(deaths)])
	print("XP EVENTS %d  %s" % [xp_events.size(), JSON.stringify(xp_events)])
	_check("no monster died while nobody fought (%d deaths)" % deaths.size(), deaths.is_empty())
	_check("travel gave no experience (level %d -> %d, xp %d -> %d)" % [start_lvl, Game.hero.progress.level, start_xp, end_xp],
		xp_events.is_empty() and Game.hero.progress.level == start_lvl)
	await _shot("03_final")
	var f := FileAccess.open(out.path_join("travel_report.json"), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({"deaths": deaths, "xp": xp_events, "fails": fails, "touch": Settings.touch_mode}, "  "))
	print("TRAVEL ", "PASS" if fails.is_empty() else "FAIL")
	get_tree().quit(0 if fails.is_empty() else 1)

func _interact_visible() -> bool:
	if Settings.touch_mode:
		var b: TouchButton = Game.ui_root.touch.button(&"interact")
		return b != null and b.is_visible_in_tree()
	return true

## Press Interact the way a player of this control mode does.
func _press_interact() -> void:
	if Settings.touch_mode:
		var b: TouchButton = Game.ui_root.touch.button(&"interact")
		var k := get_tree().root.get_final_transform().x.x
		var pos := b.center() * k
		for down in [true, false]:
			var e := InputEventScreenTouch.new()
			e.index = 3
			e.position = pos
			e.pressed = down
			Input.parse_input_event(e)
			await _wait(0.12)
	else:
		for down in [true, false]:
			var e := InputEventKey.new()
			e.keycode = KEY_R
			e.physical_keycode = KEY_R
			e.pressed = down
			Input.parse_input_event(e)
			await get_tree().process_frame

## The waypoint dialog: press the button that names the destination map's shrine.
func _pick_destination(map_id: StringName) -> bool:
	if Game.travelling:
		return true          # a single-destination dais went straight away
	var want := ""
	for id in DataIsland.NETWORK:
		if DataIsland.NETWORK[id].map == map_id:
			want = DataIsland.NETWORK[id].name
	var confirm: Node = Game.ui_root.get(&"confirm")
	if confirm == null or not confirm.visible:
		return false
	for b in confirm.find_children("*", "Button", true, false):
		if (b as Button).text.contains(want) and (b as Button).is_visible_in_tree():
			(b as Button).pressed.emit()
			return true
	return false

func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout

func _shot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
