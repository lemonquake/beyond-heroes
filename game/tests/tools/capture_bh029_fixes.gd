extends Node
## bh-029 evidence for the user's fix list (real renderer, real boot scene with HUD).
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh029_fixes.tscn -- --class=knight --slot=94 --part=<p> --out=<dir>
## parts (comma-separated): jetty

var args := {}
var out := ""
var parts: PackedStringArray
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-029/evidence/fixes")))
	parts = String(args.get("part", "jetty")).split(",")
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
	var h := Game.hero
	var lvl := int(args.get("level", "40"))
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(lvl) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2029
	GuildSummons._gear_up(h, lvl, rng)
	for f in [&"south_gate_open", &"mq_maelis_orders", &"mq_shard_taken", &"mq_three_told", &"mq_marsh_gate_open", &"boss_kethrax_defeated",
			&"mq_kethrax_reported", &"chain_breaks_seen"]:
		h.world_flags[f] = true
	h.tier = 5
	h.stats_dirty.emit()
	Game.ui_root.close_all()
	p.invulnerable = true
	if "dump" in parts:
		await _go(&"wyman_outpost", &"jetty")
		var seen := {}
		for n in get_tree().root.find_children("*", "", true, false):
			if n is VisualInstance3D or n is GPUParticles3D or n is CPUParticles3D:
				var gp: Vector3 = (n as Node3D).global_position
				var lp := Game.current_map.to_local(gp)
				if lp.x > 40.0 and lp.x < 100.0 and lp.z > -40.0 and lp.z < 60.0:
					var key := "%s|%s|%s" % [n.get_class(), n.name.rstrip("0123456789_"), String(n.get_parent().name).rstrip("0123456789_")]
					seen[key] = int(seen.get(key, 0)) + 1
		for k in seen:
			print("BH029F DUMP ", k, " x", seen[k])
	if "blobs" in parts:
		await _go(&"wyman_outpost", &"jetty")
		var groups := {"water": [], "mist": [], "multimesh": [], "lights": [], "particles": []}
		for n in Game.current_map.find_children("*", "", true, false):
			if n is MeshInstance3D and String(n.name).begins_with("Water"):
				groups.water.append(n)
			elif n is MeshInstance3D and (n as MeshInstance3D).mesh is PlaneMesh:
				groups.mist.append(n)
			elif n is MultiMeshInstance3D:
				groups.multimesh.append(n)
			elif n is OmniLight3D or n is SpotLight3D:
				groups.lights.append(n)
			elif n is GPUParticles3D or n is CPUParticles3D:
				groups.particles.append(n)
		await _orbit("blob_base", Vector3(60, 0, 10), 0.0, 80.0, 60.0)
		for w in groups.water:
			print("BH029F water mat ", w.material_override, " foam=", w.material_override.get_shader_parameter("foam"), " rough=", w.material_override.get_shader_parameter("rough"))
			w.material_override.set_shader_parameter("foam", 0.0)
		await _orbit("blob_foam0", Vector3(60, 0, 10), 0.0, 80.0, 60.0)
		for w in groups.water:
			w.material_override.set_shader_parameter("glow", 0.0)
		await _orbit("blob_glow0", Vector3(60, 0, 10), 0.0, 80.0, 60.0)
		for g in groups:
			for n in groups[g]:
				if is_instance_valid(n): n.visible = false
			await _orbit("blob_no_" + g, Vector3(60, 0, 10), 0.0, 80.0, 60.0)
			for n in groups[g]:
				if is_instance_valid(n): n.visible = true
	if "jetty" in parts:
		await _jetty()
	print("BH029F CAPTURE DONE -> ", out)
	get_tree().quit()

func _jetty() -> void:
	await _go(&"wyman_outpost", &"jetty")
	var cam := p.get_node_or_null("../PlayerCamera")
	for c in get_tree().root.find_children("*", "Camera3D", true, false):
		if c.has_method("zoom"):
			cam = c
	_place(Game.current_map.to_global(Vector3(45.0, 0.0, 26.0)), Game.current_map.to_global(Vector3(30.0, 0.0, 20.0)))
	await _shot("jetty_01_play", 40)
	if cam:
		cam.zoom(40.0)
		await _shot("jetty_02_play_far", 90)
		cam.zoom(-40.0)
	_place(Game.current_map.to_global(Vector3(28.5, 0.0, 20.5)), Game.current_map.to_global(Vector3(40.0, 0.0, 26.0)))
	await _shot("jetty_03_gate", 40)
	await _orbit("jetty_04_top", Vector3(44, 0, 26), 0.0, 80.0, 46.0)
	await _orbit("jetty_05_side", Vector3(44, 0, 26), 160.0, 28.0, 34.0)
	await _orbit("jetty_06_gangplank", Vector3(56, 0.5, 26), 220.0, 30.0, 14.0)

func _wait(frames: int) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 8) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH029F SHOT ", label)

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

func _place(at: Vector3, look: Vector3) -> void:
	var spot := CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0)
	var d := (look - at).slide(Vector3.UP)
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()

func _orbit(label: String, target_local: Vector3, yaw: float, pitch: float, dist: float) -> void:
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	cam.fov = 45.0
	var t := Game.current_map.to_global(target_local)
	var off := Vector3(0, sin(deg_to_rad(pitch)), cos(deg_to_rad(pitch))) * dist
	cam.global_position = t + off.rotated(Vector3.UP, deg_to_rad(yaw))
	cam.look_at(t)
	var prev := get_viewport().get_camera_3d()
	cam.make_current()
	await _shot(label, 20)
	if prev:
		prev.make_current()
	cam.queue_free()
