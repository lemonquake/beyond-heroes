extends Node
## Map-exit thresholds + the Delvers' Undercroft entrance (real renderer, real boot scene with HUD).
##   godot --path game --resolution 1600x900 res://tests/tools/capture_exits.tscn -- --class=knight --slot=97 --out=<dir> [--tag=before]
## --audit=1 prints, for every road out of every overworld map, how far the nearest arrival spot stands from it;
## --debug=1 shoots Olivar's west road with the band, the veil and the light each hidden in turn.

var args := {}
var out := ""
var tag := "shot"
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/exits-20261007")))
	tag = String(args.get("tag", "shot"))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	Game.ui_root.close_all()
	p.invulnerable = true
	Game.hero.world_flags[&"south_gate_open"] = true      # the barred South Gate shows nothing until Hald opens it
	if args.has("audit"):
		# every road's arrival spot and how far it stands from the threshold that leads back
		for m in [&"sanctuary", &"westreach", &"olivar", &"wyman_outpost", &"ruined_forest", &"weeping_causeway", &"agdao",
				&"zr_coilwood", &"zr_barrens", &"bridge_of_death", &"zr_citadel"]:
			await _go(m, &"start" if Game.current_map.spawns.has(&"start") else &"arrival")
			if Game.current_map_id != m:
				print("AUDIT could not reach ", m)
				continue
			for e in get_tree().get_nodes_in_group(&"map_exit"):
				var x := e as MapExit
				var best := INF
				var best_id := &""
				for id in Game.current_map.spawns:
					var d: float = (Game.current_map.spawns[id] as Node3D).global_position.distance_to(x.global_position)
					if d < best:
						best = d
						best_id = id
				print("AUDIT %s exit %s -> %s/%s | nearest spawn here %s at %.1f m" % [m, x.exit_id, x.destination_map, x.destination_spawn, best_id, best])
		get_tree().quit()
		return
	if args.has("debug"):
		await _go(&"olivar", &"west_road")
		for e in get_tree().get_nodes_in_group(&"map_exit"):
			var x := e as MapExit
			if x.exit_id != &"olivar_west_road":
				continue
			for d in [14.0, 7.0]:
				_place(x.global_position + _inward(x) * d, x.global_position)
				await _shot("dbg_%02d" % int(d), 30)
			_place(x.global_position + _inward(x) * 2.5, x.global_position)
			await _shot("dbg_all", 30)
			for n in ["ThresholdBand", "ThresholdVeil"]:
				x.get_node(n).visible = false
				await _shot("dbg_no_" + n, 10)
				x.get_node(n).visible = true
			for c in x.get_children():
				if c is OmniLight3D:
					c.visible = false
			await _shot("dbg_no_light", 10)
		get_tree().quit()
		return
	# the Undercroft entrance, from where a hero walks up to it
	await _go(&"sanctuary", &"door_int_delvers")
	await _shot("01_undercroft_door", 40)
	var door := _door(&"int_delvers")
	if door:
		_place(door.global_position + (door.global_basis.z * 5.0), door.global_position)
		await _shot("02_undercroft_approach", 40)
		await _orbit("03_undercroft_ground", door.global_position, 5.5, 62.0, 0.0)
	# every road exit of these maps: from 12 m, 6 m and 2 m inside the map
	for m in [&"sanctuary", &"westreach", &"olivar"]:
		if Game.current_map_id != m:
			await _go(m, &"gate" if m == &"sanctuary" else &"town_gate" if m == &"westreach" else &"west_road")
		for e in get_tree().get_nodes_in_group(&"map_exit"):
			var x := e as MapExit
			var inward := _inward(x)
			for d in [12.0, 6.0, 2.5]:
				_place(x.global_position + inward * d, x.global_position - inward * 4.0)
				await _shot("%s_%s_%02d" % [tag, x.exit_id, int(d)], 30)
	# arriving in Westreach from Malasugue: the way back glows right behind the hero
	await _go(&"westreach", &"town_gate")
	await _shot("%s_arrival_westreach_from_malasugue" % tag, 30)
	for e in get_tree().get_nodes_in_group(&"map_exit"):
		var x := e as MapExit
		print("EXIT %s at %s hero %s near %.2f built %s" % [x.exit_id, x.global_position, p.global_position, x._near, not x._mats.is_empty()])
	print("EXITS CAPTURE DONE -> ", out)
	get_tree().quit()

func _door(map_id: StringName) -> DoorPortal:
	for d in get_tree().get_nodes_in_group(&"door"):
		if d is DoorPortal and (d as DoorPortal).destination_map == map_id:
			return d
	return null

## Points from the exit back into the map: along the box's thin axis, toward the side with the nearest spawn point.
func _inward(x: MapExit) -> Vector3:
	var s := Vector3(4, 4, 2)
	for c in x.get_children():
		if c is CollisionShape3D:
			s = ((c as CollisionShape3D).shape as BoxShape3D).size
	var ax := Vector3(1, 0, 0) if s.x < s.z else Vector3(0, 0, 1)
	var best := INF
	var dir := ax
	for sp in get_tree().get_nodes_in_group(&"spawn_point"):
		var q := (sp as Node3D).global_position
		for sgn in [-1.0, 1.0]:
			var d := q.distance_to(x.global_position + ax * sgn * 6.0)
			if d < best:
				best = d
				dir = ax * sgn
	return dir

func _orbit(label: String, target: Vector3, dist: float, pitch_deg: float, yaw_deg: float) -> void:
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = 50.0
	var pitch := deg_to_rad(pitch_deg)
	cam.global_position = target + Vector3(0, sin(pitch), cos(pitch)).rotated(Vector3.UP, deg_to_rad(yaw_deg)) * dist
	cam.look_at(target, Vector3.UP)
	var prev := get_viewport().get_camera_3d()
	cam.make_current()
	await _shot(label, 20)
	if prev:
		prev.make_current()
	cam.queue_free()

func _place(at: Vector3, look: Vector3) -> void:
	var spot := CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0)
	var d := (look - at).slide(Vector3.UP)
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 8) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("EXITS SHOT ", label)

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	p = Game.player as Player
	p.invulnerable = true
	await _wait(60)
