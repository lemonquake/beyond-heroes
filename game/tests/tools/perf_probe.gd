extends Node
## Frame-cost probe (bh-009): boots the real game (HUD, NPCs, enemies) on one map and walks the hero through every
## spawn point of the map, sampling each spot for a while. Reports frame time, GPU time, CPU render time, script
## (process + physics) time, draw calls, primitives, visible objects and active lights. vsync is off and the frame
## rate unlimited for the run (nothing is saved), so the numbers are headroom, not a capped 60/30.
##   godot --path game --resolution 1600x900 res://tests/tools/perf_probe.tscn -- --class=knight --slot=97 \
##       --map=westreach --lite=1 --out=<file.json> [--spots=8] [--frames=90]
## Add `--rendering-method gl_compatibility` (before `--`) to measure the renderer phones use.

var args := {}
var main: Node

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 3000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	Game.god_mode = true
	Settings.vsync = false
	Settings.fps_limit = 0
	Settings.apply()
	var vp := get_viewport().get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp, true)
	await _wait(90)
	var map: MapRoot = Game.current_map
	if args.has("ablate_hud"):
		Game.place_player(StringName(args.get("spawn", "start")))
		await _wait(60)
		var hud: Node = Game.ui_root.find_children("*", "HUD", true, false)[0] if not Game.ui_root.find_children("*", "HUD", true, false).is_empty() else null
		print("ABLATE all_on %.2f ms" % await _median())
		var roots := [(Game.ui_root.find_children("*", "Hud", true, false) + [Game.ui_root])[0]]
		if args.has("hud_under"):     # descend into the subtree holding this script (e.g. minimap.gd)
			for d in Game.ui_root.find_children("*", "", true, false):
				if d.get_script() and d.get_script().resource_path.get_file() == String(args.hud_under):
					roots = [d.get_parent(), d]
					d.set_process(false)
					await _wait(10)
					print("ABLATE %s process off %.2f ms" % [args.hud_under, await _median()])
					break
		for root in roots:
			for c in root.get_children():
				if c is CanvasItem and (c as CanvasItem).visible:
					var pm: int = c.process_mode
					c.visible = false
					c.process_mode = Node.PROCESS_MODE_DISABLED
					await _wait(10)
					var scripts := {}
					for d in [c] + c.find_children("*", "", true, false):
						if d.get_script():
							scripts[String(d.get_script().resource_path.get_file())] = true
					print("ABLATE ui/%s (%s) %.2f ms %s" % [c.name, c.get_class(), await _median(), scripts.keys()])
		get_tree().quit()
		return
	if args.has("ablate"):
		await _ablate(map)
		get_tree().quit()
		return
	var ids: Array = map.spawns.keys()
	ids.sort()
	if args.has("spot_ids"):              # exact spawn ids (captures): comma separated
		ids = Array(String(args.spot_ids).split(",")).map(func(x): return StringName(x))
	var n_spots := mini(int(args.get("spots", "8")), ids.size())
	var frames := int(args.get("frames", "90"))
	var all: Array[Dictionary] = []
	var spots := {}
	for s in n_spots:
		var id: StringName = ids[int(float(s) * ids.size() / n_spots)]
		Game.place_player(id)
		await _wait(40)
		if args.has("shots") and s < int(args.get("max_shots", "3")):
			DirAccess.make_dir_recursive_absolute(String(args.shots))
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(String(args.shots).path_join("%s_%s_%s.png" % [Game.current_map_id, "lite" if Settings.lite else "full", id]))
		var lights: int = Perf.stats.lights_on if Settings.lite else _active_lights()
		if args.has("debug_lights") and Settings.lite:
			var pp: Vector3 = Game.player.global_position
			for l: Light3D in Perf._lights:
				if is_instance_valid(l) and l.is_inside_tree() and l.global_position.distance_to(pp) < 30.0:
					print("LIGHT %s d=%.1f range=%.1f energy=%.2f on=%s parent=%s" % [l.name, l.global_position.distance_to(pp),
						(l as OmniLight3D).omni_range if l is OmniLight3D else 0.0, l.light_energy, not Perf._off_lights.has(l), l.get_parent().name])
		var rows: Array[Dictionary] = []
		var last := Time.get_ticks_usec()
		for f in frames:
			await get_tree().process_frame
			var now := Time.get_ticks_usec()
			rows.append({
				"frame": (now - last) / 1000.0,
				"gpu": RenderingServer.viewport_get_measured_render_time_gpu(vp),
				"cpu_render": RenderingServer.viewport_get_measured_render_time_cpu(vp),
				"script": (Performance.get_monitor(Performance.TIME_PROCESS) + Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)) * 1000.0,
				"draws": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
				"prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
				"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
				"lights": lights,
			})
			last = now
		spots[String(id)] = _summary(rows)
		all.append_array(rows)
	var report := {
		"map": String(Game.current_map_id),
		"renderer": RenderingServer.get_current_rendering_method(),
		"lite": Settings.lite,
		"window": [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y],
		"render_scale": get_viewport().scaling_3d_scale,
		"nodes": get_tree().get_node_count(),
		"lights_in_map": map.find_children("*", "Light3D", true, false).size(),
		"video_mem_mb": snappedf(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, 0.1),
		"total": _summary(all),
		"spots": spots,
	}
	print("PERF ", JSON.stringify(report["total"]), " renderer=", report.renderer, " lite=", report.lite, " map=", report.map,
		" lights_in_map=", report.lights_in_map, " vmem=", report.video_mem_mb)
	if args.has("out"):
		var f := FileAccess.open(String(args.out), FileAccess.WRITE)
		f.store_string(JSON.stringify(report, "  "))
		f.close()
	get_tree().quit()

## Attribution: the frame time at one spot with each subsystem switched off in turn (cumulative), median of 150 frames.
func _ablate(map: MapRoot) -> void:
	Game.place_player(StringName(args.get("spawn", "start")))
	await _wait(60)
	var counts := {}
	for cls in ["Enemy", "Npc", "Tempo", "CharacterVisual", "AnimationTree", "GPUParticles3D", "Light3D", "MultiMeshInstance3D", "MeshInstance3D"]:
		counts[cls] = get_tree().root.find_children("*", cls, true, false).size()
	print("ABLATE counts ", counts)
	print("ABLATE all_on %.2f ms" % await _median())
	var steps := [
		["anim_nosync", func(): for n in get_tree().root.find_children("*", "AnimationTree", true, false):
			for bs in ["relaxed_bs", "combat_bs", "hurt_bs"]:
				var node = (n.tree_root as AnimationNodeBlendTree).get_node(bs) if n.tree_root is AnimationNodeBlendTree and (n.tree_root as AnimationNodeBlendTree).has_node(bs) else null
				if node: node.sync = false],
		["anim_offscreen", func():
			var cam := get_viewport().get_camera_3d()
			for n in get_tree().root.find_children("*", "CharacterVisual", true, false):
				if n.tree and not cam.is_position_in_frustum(n.global_position): n.tree.active = false],
		["anim_trees", func(): for n in get_tree().root.find_children("*", "AnimationTree", true, false): n.active = false],
		["visual_process", func(): for n in get_tree().root.find_children("*", "CharacterVisual", true, false): n.set_process(false)],
		["enemy_physics", func(): for n in get_tree().root.find_children("*", "Enemy", true, false): n.set_physics_process(false)],
		["enemies_all", func(): for n in get_tree().root.find_children("*", "Enemy", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["npcs", func(): for n in get_tree().root.find_children("*", "Npc", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["tempos", func(): for n in get_tree().root.find_children("*", "Tempo", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["hud", func(): for n in get_tree().root.find_children("*", "CanvasLayer", true, false): n.visible = false; n.process_mode = Node.PROCESS_MODE_DISABLED],
		["particles", func(): for n in get_tree().root.find_children("*", "GPUParticles3D", true, false): n.visible = false],
		["lights", func(): for n in get_tree().root.find_children("*", "Light3D", true, false): if not n is DirectionalLight3D: n.visible = false],
		["decor", func(): for n in map.find_children("*", "MultiMeshInstance3D", true, false): n.visible = false],
	]
	for st in steps:
		st[1].call()
		await _wait(20)
		print("ABLATE -%s %.2f ms" % [st[0], await _median()])

func _median() -> float:
	var t: Array[float] = []
	var last := Time.get_ticks_usec()
	for i in 150:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		t.append((now - last) / 1000.0)
		last = now
	t.sort()
	return t[t.size() / 2]

func _active_lights() -> int:
	var n := 0
	for l: Light3D in get_tree().root.find_children("*", "Light3D", true, false):
		if l.is_visible_in_tree() and l.light_energy > 0.0 and not (l is DirectionalLight3D):
			n += 1
	return n

func _summary(rows: Array[Dictionary]) -> Dictionary:
	var out := {}
	for k in ["frame", "gpu", "cpu_render", "script", "draws", "prims", "objects", "lights"]:
		var v: Array[float] = []
		for r in rows:
			v.append(float(r[k]))
		v.sort()
		var sum := 0.0
		for x in v:
			sum += x
		out[k] = {"avg": snappedf(sum / maxf(1.0, v.size()), 0.01), "p95": snappedf(v[int(v.size() * 0.95)] if not v.is_empty() else 0.0, 0.01)}
	return out

func _wait(frames: int) -> void:
	for i in frames:
		await get_tree().process_frame
