extends Node
## bh-018: can a hero walk onto every dungeon gate and waypoint dais? Boots the real game, stands the hero 7 m out in
## 8 directions and holds the move keys toward the dais centre for 3.5 s (real input, real physics, real collision).
## A direction passes when the hero ends within 1.3 m of the centre, standing on the dais. The direction straight
## behind a dungeon gate (its arch) is skipped.
##   godot --path game --resolution 1280x720 res://tests/tools/probe_dais_walk.tscn -- --class=knight --slot=97 [--only=burrows,...]

var main: Node
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--only="):
			only = a.substr(7).split(",", false)
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
	var sites := []
	for id in DataDungeons.order():
		var s: Dictionary = DataDungeons.get_def(id).surface
		sites.append({"name": String(id), "map": StringName(s.map), "tp": DataDungeons.gate_id(id), "yaw": float(s.yaw)})
	for t in [[&"olivar_shrine", &"olivar"], [&"wyman_shrine", &"wyman_outpost"], [&"cove_shrine", &"westreach"], [&"catacomb_gate", &"ruined_forest"]]:
		sites.append({"name": String(t[0]), "map": t[1], "tp": t[0], "yaw": 999.0})
	var fails := 0
	var total := 0
	for s in sites:
		if not only.is_empty() and not only.has(s.name):
			continue
		await _go(s.map)
		var tp: Teleporter = null
		for t in Game.current_map.teleporters():
			if t.teleporter_id == s.tp:
				tp = t
		if tp == null:
			print("DAIS %s: teleporter not found" % s.name)
			continue
		var c := tp.global_position
		var res := []
		for k in 8:
			var a := TAU * k / 8.0
			var dir := Vector3(cos(a), 0, sin(a))
			if s.yaw < 900.0:
				var fwd := Vector3(sin(deg_to_rad(s.yaw)), 0, cos(deg_to_rad(s.yaw)))
				if dir.dot(-fwd) > 0.8:
					res.append("skip")
					continue
			var ok := await _walk(c, dir)
			total += 1
			if not ok[0]:
				fails += 1
			res.append(("ok" if ok[0] else "FAIL") + "(%.1fm,%+.2f)" % [ok[1], ok[2]])
		print("DAIS %s %s" % [s.name, " ".join(res)])
	print("DAIS SUMMARY %d/%d approaches reached the dais" % [total - fails, total])
	get_tree().quit()

func _walk(c: Vector3, dir: Vector3) -> Array:
	var start := c + dir * 7.0
	var space := p.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(start + Vector3(0, 12, 0), start - Vector3(0, 20, 0), BH.LAYER_WORLD | BH.LAYER_GROUND)
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		start.y = hit.position.y
	p.teleport_to(start + Vector3.UP * 0.2)
	await _wait(10)
	# walk at the centre; when blocked (a standing stone, a prop), sidestep around it for a moment like a player would
	var last := p.global_position
	var stuck := 0
	var detour := 0
	var side := 1.0
	for i in 420:
		var d := c - p.global_position
		d.y = 0.0
		if d.length() < 0.6:
			break
		var to := d.normalized()
		if detour > 0:
			detour -= 1
			to = to.rotated(Vector3.UP, side * 1.25)
		_press(to)
		await get_tree().physics_frame
		if i % 15 == 14:
			if p.global_position.distance_to(last) < 0.25:
				stuck += 1
				detour = 40
				side = -side if stuck % 2 == 0 else side
			last = p.global_position
	_press(Vector3.ZERO)
	await _wait(5)
	var dd := p.global_position - c
	var flat := Vector2(dd.x, dd.z).length()
	return [flat < 1.3 and dd.y > -0.15, flat, dd.y]

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
