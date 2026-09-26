extends Node
## Bounded review harness: real boot, Player physics/input, M hotkey and native viewport evidence.
var out := "A:/Python/beyond-heroes/work/map-concept-2026-09-27/evidence"
var report := {}

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	var main: Node = load("res://src/main.gd").new()
	add_child(main)
	for i in 1200:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _frames(90)
	var p := Game.player as Player
	if p == null:
		print("REVIEW ERROR no player")
		get_tree().quit(1)
		return
	await _shot("01-town-gameplay")
	var before := p.global_position
	Input.action_press(&"move_right")
	await _physics(120)
	Input.action_release(&"move_right")
	report["town_movement"] = {"action":"move_right", "physics_frames":120, "from":str(before), "to":str(p.global_position), "distance_m":before.distance_to(p.global_position)}
	await _shot("02-town-after-walking")
	var ev := InputEventKey.new()
	ev.physical_keycode = KEY_M
	ev.keycode = KEY_M
	ev.pressed = true
	Input.parse_input_event(ev)
	await _frames(5)
	ev = InputEventKey.new()
	ev.physical_keycode = KEY_M
	ev.keycode = KEY_M
	ev.pressed = false
	Input.parse_input_event(ev)
	await _shot("03-current-M-map")
	report["M_opened_world_map"] = Game.ui_root.window(&"world_map").visible
	Game.ui_root.window(&"world_map").close_window()
	await _overview("04-town-overview")
	Game.load_map(&"ruined_forest", &"start")
	await _frames(90)
	await _shot("05-forest-gameplay")
	before = p.global_position
	Input.action_press(&"move_up")
	await _physics(180)
	Input.action_release(&"move_up")
	report["forest_movement"] = {"action":"move_up", "physics_frames":180, "from":str(before), "to":str(p.global_position), "distance_m":before.distance_to(p.global_position), "hp":p.hp}
	await _shot("06-forest-after-walking")
	await _overview("07-forest-overview")
	var file := FileAccess.open(out.path_join("runtime-review.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  "))
	print("REVIEW DONE ", JSON.stringify(report))
	Game.in_session = false
	get_tree().quit()

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _physics(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _shot(label: String) -> void:
	await _frames(20)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var result := img.save_png(out.path_join(label + ".png"))
	print("REVIEW SHOT ", label, " ", img.get_size(), " status ", result)

func _overview(label: String) -> void:
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	var view: Dictionary = Game.current_map.views.get("overview", {})
	var target: Vector3 = view.get("target", Vector3.ZERO)
	var dist: float = view.get("dist", 105.0)
	var pitch: float = view.get("pitch", 60.0)
	var yaw: float = view.get("yaw", 0.0)
	cam.global_position = target + Vector3(0,0,1).rotated(Vector3.RIGHT,-deg_to_rad(pitch)).rotated(Vector3.UP,deg_to_rad(yaw)) * dist
	cam.look_at(target)
	cam.fov = view.get("fov",45.0)
	cam.far = 1000.0
	cam.make_current()
	Game.ui_root._root.visible = false
	await _shot(label)
	Game.ui_root._root.visible = true
	(Game.player as Player).camera.make_current()
	cam.queue_free()
