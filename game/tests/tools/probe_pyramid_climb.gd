extends Node
## Agdao's Crown of Steps: can a hero climb the great stair from the upper terrace to the top platform? Boots the real
## game, stands the hero at the stair's foot at a few lateral offsets and holds "move up" (real input, real physics,
## real collision). Reports where each climb ended and saves a screenshot of every stop.
##   godot --path game --resolution 1280x720 res://tests/tools/probe_pyramid_climb.tscn -- --class=knight --slot=97 [--out=<dir>]

const TOP_Y := 33.4              # the top platform (17.6 + 16 m), less a little
var main: Node
var p: Player
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(30)
	p = Game.player as Player
	Game.god_mode = true
	await _go(&"agdao")
	for e in get_tree().get_nodes_in_group(&"enemy"):
		(e as Node).queue_free()
	var fails := 0
	var runs := 0
	for x in [0.0, -1.8, 1.8, -2.6, 2.6]:
		runs += 1
		var r := await _climb(Vector3(x, 0, -40.0))
		if not r[0]:
			fails += 1
		print("CLIMB x=%+.1f %s end=(%.2f, %.2f, %.2f) %s" % [x, "ok" if r[0] else "STUCK", r[1].x, r[1].y, r[1].z, r[2]])
		if out != "":
			await _shot("climb_x%+.1f" % x)
	# and back down (either half of the grand stair, and its middle)
	var dfails := 0
	for x in [-1.8, 1.8, 0.0]:
		var d := await _descend(x)
		if not d[0]:
			dfails += 1
		print("DESCEND x=%+.1f %s end=(%.2f, %.2f, %.2f)" % [x, "ok" if d[0] else "STUCK", d[1].x, d[1].y, d[1].z])
		if out != "" and not d[0]:
			await _shot("descend_x%+.1f" % x)
	print("CLIMB SUMMARY %d/%d climbs reached the top, %d/3 descents reached the terrace" % [runs - fails, runs, 3 - dfails])
	get_tree().quit()

func _ground(at: Vector3) -> Vector3:
	var space := p.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(at + Vector3(0, 40, 0), at - Vector3(0, 40, 0), BH.LAYER_WORLD | BH.LAYER_GROUND)
	var hit := space.intersect_ray(q)
	return (hit.position as Vector3) if not hit.is_empty() else at

func _skip_scenes() -> void:
	for k in 20:
		if not CutscenePlayer.is_playing():
			return
		CutscenePlayer.active.skip_all()
		await _wait(30)

func _climb(start: Vector3) -> Array:
	await _skip_scenes()
	var s := _ground(Vector3(start.x, 18.0, start.z))
	p.teleport_to(s + Vector3.UP * 0.2)
	await _wait(10)
	var trace := []
	var last := p.global_position
	var still := 0
	for i in 900:
		_press(Vector3(0, 0, -1))
		await get_tree().physics_frame
		if p.global_position.y >= TOP_Y and p.global_position.z < -67.0:
			break
		if i % 30 == 29:
			trace.append("%.1f/%.1f" % [p.global_position.z, p.global_position.y])
			if p.global_position.distance_to(last) < 0.2:
				still += 1
				if still >= 3:
					break
			else:
				still = 0
			last = p.global_position
	_press(Vector3.ZERO)
	await _wait(5)
	return [p.global_position.y >= TOP_Y, p.global_position, " ".join(trace)]

func _descend(x: float) -> Array:
	await _skip_scenes()
	p.teleport_to(_ground(Vector3(x, 40.0, -69.0)) + Vector3.UP * 0.2)
	await _wait(10)
	for i in 900:
		_press(Vector3(0, 0, 1))
		await get_tree().physics_frame
		if p.global_position.z > -42.0:
			break
	_press(Vector3.ZERO)
	await _wait(5)
	return [p.global_position.z > -42.0 and p.global_position.y < 19.0, p.global_position]

func _press(v: Vector3) -> void:
	for a in [&"move_left", &"move_right", &"move_up", &"move_down"]:
		Input.action_release(a)
	if v.length() < 0.01:
		return
	if v.x > 0.0:
		Input.action_press(&"move_right", v.x)
	elif v.x < 0.0:
		Input.action_press(&"move_left", -v.x)
	if v.z > 0.0:
		Input.action_press(&"move_down", v.z)
	elif v.z < 0.0:
		Input.action_press(&"move_up", -v.z)

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(out)
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _go(map_id: StringName) -> void:
	if Game.current_map_id == map_id:
		return
	Game.travel(map_id, &"start")
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(40)
