extends Node
## Touch "Roll" button check (bh-009): boots the real game in touch mode, taps Roll with the stick at rest and with
## the stick held sideways, and reports how far and which way the hero travelled (plus a screenshot of the controls).
##   godot --path game --resolution 1920x864 res://tests/tools/check_roll.tscn -- --class=knight --slot=97 --touch=1 \
##       --map=ruined_forest --out=<dir>

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/roll")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _run() -> void:
	for i in 600:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(5.0)
	var p := Game.player as Player
	Game.god_mode = true
	var tc: TouchControls = Game.ui_root.touch
	var k := get_tree().root.get_final_transform().x.x
	var roll := tc.button(&"roll")
	print("ROLL button exists=%s visible=%s at=%s" % [roll != null, roll.is_visible_in_tree() if roll else false, roll.center() if roll else Vector2.ZERO])
	await _shot("roll_button")
	# 1) stick at rest: roll the way the hero faces
	var fwd := p.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var a := p.global_position
	await _tap(roll.center() * k)
	for f in 8:
		await get_tree().process_frame
		print("  after roll tap f%d action=%s kind=%s tc.player=%s" % [f, p.visual.current_action(), p.action_kind, tc.player != null])
	await _wait(0.9)
	var d := p.global_position - a
	d.y = 0.0
	print("ROLL still: moved %.2f m, along facing %.2f m" % [d.length(), d.dot(fwd)])
	await _wait(1.5)
	# 2) the old Dodge button with the stick at rest: still the backstep
	fwd = p.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	a = p.global_position
	await _tap(tc.button(&"dodge").center() * k)
	for f in 8:
		await get_tree().process_frame
		print("  after dodge tap f%d action=%s kind=%s" % [f, p.visual.current_action(), p.action_kind])
	await _wait(0.9)
	d = p.global_position - a
	d.y = 0.0
	print("DODGE still: moved %.2f m, along facing %.2f m (negative = backstep)" % [d.length(), d.dot(fwd)])
	get_tree().quit()

func _tap(pos: Vector2) -> void:
	var e := InputEventScreenTouch.new()
	e.index = 7
	e.position = pos
	e.pressed = true
	Input.parse_input_event(e)
	for i in 3:
		await get_tree().process_frame
	var r := InputEventScreenTouch.new()
	r.index = 7
	r.position = pos
	r.pressed = false
	Input.parse_input_event(r)

func _wait(t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
