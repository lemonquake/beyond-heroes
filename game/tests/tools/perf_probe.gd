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
	if args.get("firsthit", "") == "cold":
		FX.warm_enabled = false
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
	if args.has("ablate") and not args.has("stress"):
		await _ablate(map)
		get_tree().quit()
		return
	if args.has("load_bench"):
		# map load time (bh-014): Game.load_map = build + navmesh bake + monsters + NPCs, what the loading screen waits on
		for id in String(args.load_bench).split(","):
			var t0 := Time.get_ticks_usec()
			Game.load_map(StringName(id), &"start")
			var ms := (Time.get_ticks_usec() - t0) / 1000.0
			await _wait(30)
			print("LOAD %s %.0f ms enemies=%d" % [id, ms, get_tree().get_nodes_in_group(&"enemy").size()])
		get_tree().quit()
		return
	if args.has("firsthit"):
		await _first_hit(map)
		get_tree().quit()
		return
	if args.has("spawn_bench"):
		Game.place_player(StringName(args.get("spawn", "start")))
		await _wait(30)
		for id in String(args.spawn_bench).split(","):
			var d := DB.enemy(StringName(id))
			for i in 2:
				var a0 := Time.get_ticks_usec()
				var ps: PackedScene = load(d.model)
				var a1 := Time.get_ticks_usec()
				var inst := ps.instantiate()
				var a2 := Time.get_ticks_usec()
				inst.free()
				var cv := CharacterVisual.new()
				map.add_child(cv)
				var a3 := Time.get_ticks_usec()
				cv.setup(d.model, 1.0, Color.WHITE)
				var a4 := Time.get_ticks_usec()
				cv.queue_free()
				var en := Enemy.new()
				en.setup(d, 5, [], {})
				var a5 := Time.get_ticks_usec()
				map.add_child(en)
				var a6 := Time.get_ticks_usec()
				en.queue_free()
				print("PIECES %s load %.1f inst %.1f visual.setup %.1f enemy.setup %.1f enemy.add_child %.1f" % [id, (a1-a0)/1000.0, (a2-a1)/1000.0, (a4-a3)/1000.0, (a5-a4)/1000.0, (a6-a5)/1000.0])
				await _wait(2)
			var ts: Array = []
			for i in 6:
				var t0 := Time.get_ticks_usec()
				var e := Spawner.spawn_enemy(map, d, 5, [], Game.player.global_position + Vector3(8, 0, 0), {})
				var t1 := Time.get_ticks_usec()
				await get_tree().process_frame
				var t2 := Time.get_ticks_usec()
				ts.append("%.1f+%.1f" % [(t1 - t0) / 1000.0, (t2 - t1) / 1000.0])
				e.queue_free()
				await _wait(3)
			print("SPAWN %s ms (spawn+next frame): %s" % [id, ", ".join(ts)])
		get_tree().quit()
		return
	if args.has("stress"):
		await _stress(map)
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

## First-hit hitch (bh-014): a single monster (AI off) in front of the hero, who swings at it a few times; reports the
## longest frames after the first swing. `--firsthit=warm` runs FX.warm_up() first (as a map load now does).
func _first_hit(map: MapRoot) -> void:
	Game.place_player(StringName(args.get("spawn", "start")))
	await _wait(60)
	var hero: Player = Game.player
	var def: EnemyDef = null
	for e: Enemy in get_tree().get_nodes_in_group(&"enemy"):
		if not e.is_boss:
			def = e.def
			break
	var e := Spawner.spawn_enemy(map, def, 1, [], hero.global_position + hero.forward() * 1.5, {})
	e.set_physics_process(false)
	if args.firsthit == "warm":
		FX.warm_up()
	await _wait(60)
	var times: Array = []
	var last := Time.get_ticks_usec()
	for f in 150:
		if f % 40 == 20 and e.alive:
			# a real blow from the hero through the damage pipeline (a swing aims at the mouse, which a tool can't)
			var req := DamageRequest.new()
			req.kind = DamageRequest.Kind.ATTACK
			req.attacker = hero.stats
			req.base_min = 3.0
			req.base_max = 4.0
			req.knockback = 2.0
			req.evadable = false
			var t0 := Time.get_ticks_usec()
			e.receive_hit(req, hero, e.center())
			if args.has("verbose"):
				print("HITCALL f=%d receive_hit %.1f ms" % [f, (Time.get_ticks_usec() - t0) / 1000.0])
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		times.append([(now - last) / 1000.0, f])
		last = now
	times.sort_custom(func(a, b): return a[0] > b[0])
	print("FIRSTHIT mode=%s worst=%s hp=%.0f/%.0f" % [args.firsthit, times.slice(0, 5).map(func(t): return "%.1fms@%d" % t), e.hp, e.max_hp()])

## Combat stress (bh-014): N monsters of the map's own kinds (plus every camp already there) spawn in a ring around
## the hero and fight them (god mode), while the hero swings every half second. Samples `--frames` (default 600)
## frames once the fight is on. With `--ablate`-style attribution off, this is the frame time of a big brawl.
##   ... perf_probe.tscn -- --class=knight --slot=97 --map=ruined_forest --stress=40 --out=<file.json>
func _stress(map: MapRoot) -> void:
	Game.place_player(StringName(args.get("spawn", "start")))
	await _wait(30)
	var hero: Player = Game.player
	var defs: Array = []
	for e: Enemy in get_tree().get_nodes_in_group(&"enemy"):
		if not e.is_boss and not defs.has(e.def):
			defs.append(e.def)
	var n := int(args.get("stress", "40"))
	var holder := Node3D.new()
	holder.name = "StressPack"
	map.add_child(holder)
	var rng := RandomNumberGenerator.new()
	rng.seed = 14
	var spawned: Array[Enemy] = []
	for i in n:
		var a := TAU * i / n
		var r := rng.randf_range(7.0, 13.0)
		var want := hero.global_position + Vector3(cos(a) * r, 0.0, sin(a) * r)
		var p := NavigationServer3D.map_get_closest_point(map.nav_region.get_navigation_map(), want)
		var e := Spawner.spawn_enemy(holder, defs[i % defs.size()], map.def.level_max, [], p, {})
		spawned.append(e)
	await _wait(5)
	for e in spawned:
		e.alert_to(hero.global_position)
	if args.has("no_pbs"):
		var nfree := 0
		for pbs in get_tree().root.find_children("*", "PhysicalBoneSimulator3D", true, false):
			pbs.free()
			nfree += 1
		print("freed %d PhysicalBoneSimulator3D" % nfree)
	if args.has("no_enemy_collide"):
		for e: Enemy in get_tree().get_nodes_in_group(&"enemy"):
			e.collision_mask &= ~BH.LAYER_ENEMY
	await _wait(90)
	if args.has("shot"):
		# a real frame of the brawl with the F3 overlay (frame rate, frame time) for the user (bh-014)
		Dev.show_fps = true
		for i in 150:
			if i % 30 == 0:
				hero.call(&"_request", &"light")
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		DirAccess.make_dir_recursive_absolute(String(args.shot).get_base_dir())
		get_viewport().get_texture().get_image().save_png(String(args.shot))
		print("SHOT ", args.shot, " fps=", Engine.get_frames_per_second())
		return
	if args.has("census"):
		var cls := {}
		for e: Enemy in get_tree().get_nodes_in_group(&"enemy"):
			for d in e.find_children("*", "", true, false):
				var k: String = d.get_class() + ("(" + d.get_script().resource_path.get_file() + ")" if d.get_script() else "")
				var flags := ("P" if d.is_processing() else "") + ("F" if d.is_physics_processing() else "") + ("p" if d.is_processing_internal() else "") + ("f" if d.is_physics_processing_internal() else "")
				k += " [" + flags + "]"
				cls[k] = cls.get(k, 0) + 1
		var ks: Array = cls.keys()
		ks.sort_custom(func(a, b): return cls[a] > cls[b])
		for k in ks:
			print("CENSUS %5d %s" % [cls[k], k])
		return
	if args.has("ablate_process"):
		await _ablate_process()
		return
	if args.has("ablate"):
		await _ablate(map, false)
		return
	var vp := get_viewport().get_viewport_rid()
	var frames := int(args.get("frames", "600"))
	var rows: Array[Dictionary] = []
	var last := Time.get_ticks_usec()
	var swing := 0.0
	var added := {}
	var on_add := func(n: Node) -> void:
		var k: String = n.get_class() + ("(" + n.get_script().resource_path.get_file() + ")" if n.get_script() else "")
		added[k] = added.get(k, 0) + 1
	if args.has("spikes"):
		get_tree().node_added.connect(on_add)
	for f in frames:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		var dt := (now - last) / 1000.0
		if args.has("spikes"):
			if dt > float(args.spikes):
				print("SPIKE f=%d %.1f ms added=%s" % [f, dt, added])
			added.clear()
		swing += dt
		if swing > 500.0:
			swing = 0.0
			hero.call(&"_request", &"light")
		rows.append({
			"frame": dt,
			"gpu": RenderingServer.viewport_get_measured_render_time_gpu(vp),
			"cpu_render": RenderingServer.viewport_get_measured_render_time_cpu(vp),
			"script": Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
			"physics": Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
			"nav": Performance.get_monitor(Performance.TIME_NAVIGATION_PROCESS) * 1000.0,
			"draws": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			"prims": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			"lights": 0,
		})
		last = now
	var engaged := 0
	for e: Enemy in get_tree().get_nodes_in_group(&"enemy"):
		if e.alive and e.brain.is_engaged():
			engaged += 1
	var report := {"map": String(Game.current_map_id), "renderer": RenderingServer.get_current_rendering_method(),
		"lite": Settings.lite, "stress": n, "engaged_at_end": engaged, "window": [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y],
		"total": _summary(rows)}
	print("STRESS ", JSON.stringify(report.total.frame), " gpu=", JSON.stringify(report.total.gpu), " process=", JSON.stringify(report.total.script),
		" physics=", JSON.stringify(report.total.physics), " nav=", JSON.stringify(report.total.nav), " engaged=", engaged, " map=", report.map, " lite=", report.lite)
	if args.has("out"):
		var fo := FileAccess.open(String(args.out), FileAccess.WRITE)
		fo.store_string(JSON.stringify(report, "  "))
		fo.close()

## Per-script attribution (bh-014): for each script (or engine class with internal processing), switch its per-frame
## callbacks off, take the median frame, switch them back on. The drop is that group's share of the frame.
func _ablate_process() -> void:
	var groups := {}
	for n in get_tree().root.find_children("*", "", true, false):
		if n == self:
			continue
		var key := ""
		if n.get_script() and (n.is_processing() or n.is_physics_processing()):
			key = "script:" + n.get_script().resource_path.get_file()
		elif n.is_processing_internal() or n.is_physics_processing_internal():
			key = "internal:" + n.get_class()
		if key != "":
			if not groups.has(key):
				groups[key] = []
			groups[key].append(n)
	var base := await _median()
	print("APROC all_on %.2f ms (%d groups)" % [base, groups.size()])
	var res := []
	for key in groups:
		var list: Array = groups[key]
		var saved := []
		for n in list:
			if not is_instance_valid(n):
				saved.append(null)
				continue
			saved.append([n.is_processing(), n.is_physics_processing(), n.is_processing_internal(), n.is_physics_processing_internal()])
			if String(key).begins_with("script:"):
				n.set_process(false)
				n.set_physics_process(false)
			else:
				n.set_process_internal(false)
				n.set_physics_process_internal(false)
		await _wait(5)
		var m := await _median()
		for i in list.size():
			var n = list[i]
			if saved[i] == null or not is_instance_valid(n):
				continue
			n.set_process(saved[i][0])
			n.set_physics_process(saved[i][1])
			n.set_process_internal(saved[i][2])
			n.set_physics_process_internal(saved[i][3])
		res.append([base - m, key, list.size()])
		await _wait(5)
	res.sort_custom(func(a, b): return a[0] > b[0])
	for r in res:
		print("APROC %6.2f ms  %-40s x%d" % [r[0], r[1], r[2]])

## Attribution: the frame time at one spot with each subsystem switched off in turn (cumulative), median of 150 frames.
func _ablate(map: MapRoot, place := true) -> void:
	if place:
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
		["nav_agents", func(): for n in get_tree().root.find_children("*", "NavigationAgent3D", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["enemies_all", func(): for n in get_tree().root.find_children("*", "Enemy", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["npcs", func(): for n in get_tree().root.find_children("*", "Npc", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["tempos", func(): for n in get_tree().root.find_children("*", "Tempo", true, false): n.process_mode = Node.PROCESS_MODE_DISABLED],
		["enemy_bars", func(): for n in get_tree().root.find_children("*", "EnemyBar", true, false): n.visible = false; n.process_mode = Node.PROCESS_MODE_DISABLED],
		["label3d", func(): for n in get_tree().root.find_children("*", "Label3D", true, false): n.visible = false],
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
	for k in ["frame", "gpu", "cpu_render", "script", "physics", "nav", "draws", "prims", "objects", "lights"]:
		if not rows.is_empty() and not rows[0].has(k):
			continue
		var v: Array[float] = []
		for r in rows:
			v.append(float(r[k]))
		v.sort()
		var sum := 0.0
		for x in v:
			sum += x
		out[k] = {"avg": snappedf(sum / maxf(1.0, v.size()), 0.01), "p95": snappedf(v[int(v.size() * 0.95)] if not v.is_empty() else 0.0, 0.01)}
		if k == "frame" and not v.is_empty():
			out[k]["p99"] = snappedf(v[int(v.size() * 0.99)], 0.01)
			out[k]["max"] = snappedf(v[-1], 0.01)
	return out

func _wait(frames: int) -> void:
	for i in frames:
		await get_tree().process_frame
