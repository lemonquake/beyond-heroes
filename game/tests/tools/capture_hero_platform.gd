extends Node
## Capture actual game UI and exercise a routed inventory hold, without touching player saves.

var args := {}
var out := ""
var notes := {}

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--") and "=" in arg:
			args[arg.substr(2).get_slice("=", 0)] = arg.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://../output/hero-platform")))
	DirAccess.make_dir_recursive_absolute(out)
	Game.save_slot = 96
	get_tree().root.gui_embed_subwindows = true # Android embeds context windows in the game viewport.
	Settings.resolution = 2
	Settings.vsync = false
	Settings.fps_limit = 120
	var main: Node = load("res://src/main.tscn").instantiate()
	add_child(main)
	_run.call_deferred()

func _run() -> void:
	var ready := false
	for i in 12000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling and not Game._loading.visible:
			ready = true
			break
	if not ready:
		push_error("Game did not finish loading before the platform capture")
		get_tree().quit(1)
		return
	get_window().size = Vector2i(int(args.get("w", "1920")), int(args.get("h", "1080")))
	await _wait(1.0)
	Game.god_mode = true
	var ui := Game.ui_root as UIRoot
	var item := DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 1, 642)
	Game.hero.inventory.add(item)
	notes = {"engine": Engine.get_version_info().string, "renderer": RenderingServer.get_current_rendering_method(),
		"adapter": RenderingServer.get_video_adapter_name(), "window": [get_window().size.x, get_window().size.y],
		"body": Game.hero.look.get("body", "custom"), "touch": Settings.touch_mode,
		"user_data": OS.get_user_data_dir(), "physical_android": OS.has_feature("android")}
	await _shot("01_game")
	ui.open(&"inventory")
	await _wait(0.7)
	var inventory := ui.window(&"inventory") as InventoryWindow
	await _shot("02_inventory")
	var slot := inventory.cells[Game.hero.inventory.index_of(item)]
	var position := slot.get_global_transform_with_canvas() * (slot.size * 0.5)
	if args.has("wait_focus"):
		print("PLATFORM_WAITING_FOR_FOCUS")
		for i in 12000:
			if ui.touch._focused:
				break
			await get_tree().process_frame
	notes["actual_input_focused"] = ui.touch._focused
	if args.has("simulate_focus"):
		# A background desktop QA window cannot receive an OS focus event. This
		# explicit fixture exercises the same in-game focus/resume path while
		# keeping that limitation visible in the evidence; it is not manual play.
		ui.touch.notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	notes["simulated_focus"] = args.has("simulate_focus")
	notes["input_focused"] = ui.touch._focused
	notes["touch_visible"] = ui.touch.is_visible_in_tree()
	_touch(position, true)
	notes["contacts_after_down"] = TouchGesture._contacts.size()
	notes["owns_item_after_down"] = TouchGesture._control() == slot
	await _wait(0.65)
	notes["hold_keeps_item"] = Game.hero.inventory.index_of(item) >= 0
	await _shot("03_inventory_options")
	notes["hold_opens_options"] = is_instance_valid(inventory._touch_menu) and inventory._touch_menu.visible
	_touch(position, false)
	await _wait(0.2)
	notes["options_survive_release"] = is_instance_valid(inventory._touch_menu) and inventory._touch_menu.visible
	inventory.close_window()
	ui.open(&"settings")
	await _wait(0.6)
	await _shot("04_video_settings")
	ui.close_all()
	ui.open(&"skills")
	await _wait(0.6)
	await _shot("05_skills")
	ui.close_all()
	ui.pause_menu.open()
	await _wait(0.4)
	await _shot("06_pause")
	ui.pause_menu.close()
	notes["resumed"] = not get_tree().paused
	ui.open_creator()
	await _wait(1.0)
	await _shot("07_appearance")
	ui._close_creator()
	var file := FileAccess.open(out.path_join("notes.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(notes, "  "))
	print("HERO_PLATFORM_CAPTURE_DONE ", JSON.stringify(notes))
	get_tree().quit()

func _touch(at: Vector2, pressed: bool) -> void:
	var raw := InputEventScreenTouch.new()
	raw.index = 0
	raw.position = at
	raw.pressed = pressed
	var mouse := InputEventMouseButton.new()
	mouse.position = at
	mouse.global_position = at
	mouse.device = InputEvent.DEVICE_ID_EMULATION
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
	mouse.pressed = pressed
	# Godot synthesizes this mouse event before delivering its original raw contact.
	get_viewport().push_input(mouse, true)
	get_viewport().push_input(raw, true)

func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds, true, false, true).timeout

func _shot(label: String) -> void:
	# First-use shader work can consume wall time before UI tweens have advanced.
	# Capture settled rendered frames, including the appearance preview, rather
	# than treating an elapsed wall-clock timer as proof that a fade finished.
	for i in 60:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var picture := get_viewport().get_texture().get_image()
	picture.save_png(out.path_join(label + ".png"))
	print("PLATFORM_SHOT ", label, " ", picture.get_size())
