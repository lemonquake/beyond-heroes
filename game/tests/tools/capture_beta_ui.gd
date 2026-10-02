extends Node
## Beta readiness review captures (bh-032): the real game at a given window size and control mode, saving PNGs of the
## screens a new player meets first plus a JSON note of what was measured. Nothing is written to settings or real saves.
##   godot --path game --rendering-method forward_plus res://tests/tools/capture_beta_ui.tscn -- --class=knight --slot=95 \
##       --w=1280 --h=720 --touch=0 --out=<dir>
## --touch=1 plays with the on-screen controls (a PC window standing in for a phone: it is NOT a phone measurement).

var args := {}
var out := ""
var main: Node
var notes := {"shots": []}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/beta_ui")))
	DirAccess.make_dir_recursive_absolute(out)
	Game.save_slot = 95
	Settings.resolution = 0                 # run-only: Main re-applies Settings, which would otherwise restore the player's window size
	Settings.window_mode = 0
	if args.has("ui_override"):             # "before" captures: the interface as it was drawn before the automatic scale
		Settings.ui_auto = false
		Settings.ui_scale = float(args.ui_override)
	elif args.has("ui_scale"):              # a phone's first-launch Interface Scale (1.25)
		Settings.ui_scale = float(args.ui_scale)
	main = load("res://src/main.tscn").instantiate()
	add_child(main)
	_run.call_deferred()

func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds, true).timeout

func _shot(label: String) -> void:
	await _wait(0.6)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out.path_join(label + ".png")
	img.save_png(path)
	notes.shots.append({"name": label, "image_size": [img.get_width(), img.get_height()], "window": [get_window().size.x, get_window().size.y],
		"ui_scale": snappedf(get_viewport().content_scale_factor, 0.001)})
	print("SHOT ", label, " ", img.get_size(), " window ", get_window().size, " ui_scale ", get_viewport().content_scale_factor)

func _run() -> void:
	await _wait(2.0)
	for i in 300:
		if Game.in_session and Game.player is Player and (Game.player as Player).hero:
			break
		await _wait(0.1)
	await _wait(1.5)
	var size := Vector2i(int(args.get("w", "1280")), int(args.get("h", "720")))
	get_window().size = size
	await _wait(1.0)
	if args.has("ui_override"):
		notes["ui_override"] = float(args.ui_override)
	notes["engine"] = Engine.get_version_info().string
	notes["renderer"] = RenderingServer.get_current_rendering_method()
	notes["adapter"] = RenderingServer.get_video_adapter_name()
	notes["window"] = [get_window().size.x, get_window().size.y]
	notes["touch"] = Settings.touch_mode
	notes["quality"] = {"shadows": Settings.shadows_quality, "effects": Settings.effects_quality, "render_scale": Settings.render_scale, "efficiency": Settings.efficiency_mode}
	notes["interface_scale_setting"] = Settings.ui_scale
	notes["effective_ui_scale"] = Settings.effective_ui_scale()
	var ui: UIRoot = Game.ui_root
	var p := Game.player as Player
	await _shot("01_town_hud")
	ui.chat.open()
	ui.chat.add_line("[Anton] Welcome back, hero.", UITheme.PARCHMENT)
	ui.chat.add_line("Mind the road south: wolves have been seen.", UITheme.GOLD)
	await _shot("02_chat_open")
	ui.chat.close()
	ui.pause_menu.open()
	await _shot("03_pause")
	ui.pause_menu.close()
	await _wait(0.4)
	for window_name in ["inventory", "character", "skills", "multiplayer", "settings", "world_map"]:
		ui.open(StringName(window_name))
		await _shot("1_%s" % window_name)
		var w: Node = ui.window(StringName(window_name))
		if w:
			w.close_window()
		await _wait(0.4)
	if Settings.touch_mode and ui.touch:
		ui.touch.visible = true
	await _shot("20_back_to_play")
	var f := FileAccess.open(out.path_join("notes.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(notes, "  "))
	f.close()
	print("CAPTURE DONE")
	get_tree().quit()
