extends Node3D
## Actual Efficiency-menu renders; no save is created or changed.

var args := {}

func _ready() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			args[argument.substr(2).get_slice("=", 0)] = argument.get_slice("=", 1)
	_run.call_deferred()

func _run() -> void:
	var out := String(args.get("out", ProjectSettings.globalize_path("res://../output/menu-budget")))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "mobile"
	Settings._efficiency_preset()
	Settings.window_mode = 0
	Settings.vsync = false
	Settings.apply()
	var layer := CanvasLayer.new()
	add_child(layer)
	var menu := MainMenu.new()
	layer.add_child(menu)
	var started := Time.get_ticks_usec()
	menu.build_backdrop(self)
	var construction_ms := float(Time.get_ticks_usec() - started) / 1000.0
	for index in 60:
		await get_tree().process_frame
	var notes := {"engine": Engine.get_version_info().string, "adapter": RenderingServer.get_video_adapter_name(),
		"construction_ms": construction_ms, "characters": menu._heroes.size(), "lite": menu._backdrop_lite,
		"physical_android": OS.has_feature("android")}
	for pair in [["1080", Vector2i(1920, 1080)], ["phone", Vector2i(1920, 864)]]:
		get_window().size = pair[1]
		for index in 80:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out.path_join("servers-" + pair[0] + ".png"))
	# Inspect the stage behind the normal title column as well as the first realm page.
	menu._server_menu.queue_free()
	menu._server_menu = null
	menu._sync_design_hold()
	menu._byline.text = "Offline Play · local saves"
	for pair in [["1080", Vector2i(1920, 1080)], ["phone", Vector2i(1920, 864)]]:
		get_window().size = pair[1]
		for index in 80:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out.path_join("menu-" + pair[0] + ".png"))
	var file := FileAccess.open(out.path_join("notes.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(notes, "  "))
	print("MENU_BUDGET_CAPTURE_DONE ", JSON.stringify(notes))
	menu.dispose_backdrop()
	get_tree().quit()
