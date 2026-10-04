extends Node
## Walk probe (bh-037): boots the real game on one map with the player's own video settings and walks the hero, with real
## movement input, along navmesh paths through every spawn point and named place of the map. Every frame is logged; a
## frame over `--spike` ms (default 20) prints what happened in it: physics steps, script time, render-pipeline (shader)
## compilations, nodes added, a minimap re-render, light-budget changes, occlusion fades. The summary gives the FPS, the
## 1 % low and how many frames missed a 60 Hz refresh. Nothing is saved (hidden slot; settings applied for the run only).
##   godot --path game res://tests/tools/walk_probe.tscn -- --class=knight --slot=97 --map=agdao [--uncap=1]
##       [--spike=20] [--seconds=150] [--out=<file.json>] [--windowed=1920x1080]
## `--uncap=1` turns vsync and the frame cap off (headroom); without it the run shows what the player sees.

var args := {}
var main: Node
var _added := {}
var _origins: Array = []
var _rows: Array = []
var _spikes: Array = []
var _marks: Array = []              # [tag, usec] for this frame: physics steps, process, pre/post draw
var _mm_frames := 0
var _nodes0 := 0
var _parts0 := 0

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	# a script error stops this coroutine but not the engine: always quit in the end (a hung window can't be closed from a shell)
	get_tree().create_timer(float(args.get("seconds", "150")) + 240.0, true, false, true).timeout.connect(func() -> void:
		print("WALKABORT watchdog")
		get_tree().quit(2))
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 3000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	Game.god_mode = true
	if args.has("uncap"):
		Settings.vsync = false
		Settings.fps_limit = 0
	if args.has("windowed"):
		Settings.window_mode = 0
	for k in ["efficiency_mode", "shadows_quality", "effects_quality", "anti_aliasing", "render_scale", "minimap_zoom"]:
		if args.has(k):
			Settings.set(k, type_convert(args[k], typeof(Settings.get(k))))
	Settings.apply()
	if args.has("windowed"):
		var wh := String(args.windowed).split("x")
		DisplayServer.window_set_size(Vector2i(int(wh[0]), int(wh[1])))
	RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(), true)
	await _wait(240)
	for i in 3000:                          # a skipped cutscene can end in a short travel: wait for the hero again
		if Game.in_session and Game.player is Player and not Game.travelling and Game.current_map:
			break
		await _wait(1)
	print("WALKINFO hero=%s level=%d map=%s tempos=%d" % [Game.hero.hero_name, Game.hero.progress.level, Game.current_map_id,
		get_tree().get_nodes_in_group(&"tempo").size()])
	if args.has("shot"):                    # a screenshot at --spawn (or where the hero stands) after the map settles
		if args.has("spawn_at"):
			Game.place_player(StringName(args.spawn_at))
		await _wait(int(args.get("shot_wait", "90")))
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(String(args.shot))
		print("SHOT ", args.shot)
		get_tree().quit()
		return
	if args.has("fade_all"):
		await _fade_all(Game.current_map, Game.player)
		get_tree().quit()
		return
	if args.has("ablate"):
		await _ablate_scripts()
		get_tree().quit()
		return
	if args.has("fx_bench"):
		await _fx_bench()
		get_tree().quit()
		return
	if args.has("hull_bench"):
		for f in DirAccess.get_files_at("res://assets/environment/"):
			if f.ends_with("_fragments.glb"):
				var fr: Node3D = (load("res://assets/environment/" + f) as PackedScene).instantiate()
				var pieces := fr.find_children("frag_*", "MeshInstance3D", true, false)
				var t0 := Time.get_ticks_usec()
				for pc: MeshInstance3D in pieces:
					pc.mesh.create_convex_shape(true, true)
				var t1 := Time.get_ticks_usec()
				for pc: MeshInstance3D in pieces:
					pc.mesh.create_convex_shape(true, false)
				var t2 := Time.get_ticks_usec()
				print("HULL %s pieces=%d simplify %.1f ms, plain %.1f ms" % [f, pieces.size(), (t1 - t0) / 1000.0, (t2 - t1) / 1000.0])
				fr.free()
		get_tree().quit()
		return
	if args.has("fx_leak"):
		await _fx_leak()
		get_tree().quit()
		return
	if args.has("spawn_bench"):
		await _spawn_bench()
		get_tree().quit()
		return
	if args.has("status_bench"):
		await _status_bench()
		get_tree().quit()
		return
	if args.has("save_bench"):
		_save_bench()
		get_tree().quit()
		return
	var map: MapRoot = Game.current_map
	var hero: Player = Game.player
	var stops := _stops(map, hero.global_position)
	for e in map.find_children("*", "MapExit", true, false):    # walking past a gate must not leave the map mid-run
		(e as Area3D).set_deferred(&"monitoring", false)
	print("WALK map=%s stops=%d refresh=%.0f Hz window=%s vsync=%s cap=%d lite=%s shadows=%d effects=%d aa=%d scale=%.2f renderer=%s" % [
		Game.current_map_id, stops.size(), DisplayServer.screen_get_refresh_rate(), DisplayServer.window_get_size(), Settings.vsync,
		Settings.fps_limit, Settings.lite, Settings.shadows_quality, Settings.effects_quality, Settings.anti_aliasing, Settings.render_scale,
		RenderingServer.get_current_rendering_method()])
	get_tree().node_added.connect(func(n: Node) -> void:
		var k: String = n.get_class() + ("(" + n.get_script().resource_path.get_file() + ")" if n.get_script() else "")
		if n is Enemy and (n as Enemy).def:
			k += ":" + String((n as Enemy).def.id)
		if (n is GPUParticles3D or n is Control) and _origins.size() < 3:
			# who made it: the game's script frames (a debug build keeps the stack), for spikes that compile pipelines
			var fr := get_stack().filter(func(f): return not String(f.source).contains("walk_probe"))
			var o := " < ".join(fr.slice(0, 4).map(func(f): return "%s:%d %s" % [String(f.source).get_file(), f.line, f.function]))
			if o != "" and not _origins.has(o):
				_origins.append(o)
		_added[k] = int(_added.get(k, 0)) + 1)
	for pair in [[get_tree().physics_frame, "phys"], [get_tree().process_frame, "proc"], [RenderingServer.frame_pre_draw, "pre"], [RenderingServer.frame_post_draw, "post"]]:
		var tag: String = pair[1]
		(pair[0] as Signal).connect(func() -> void: _marks.append([tag, Time.get_ticks_usec()]))
	if args.has("autosave_soon"):           # an autosave ~5 s into the walk (its frame shows as a spike if it costs one)
		var grace: float = float((Game.get_script() as GDScript).get_script_constant_map().get("AUTOSAVE_GRACE", 0.0))
		Game._autosave_t = Game.AUTOSAVE_INTERVAL + grace - 5.0      # past any wait for a still moment: measure the save itself
	await _walk(map, hero, stops)
	if args.has("cost_after"):              # walked `--seconds` into the fight; now time every actor's physics callback by hand
		_rows.pop_back()
		_press(Vector2.ZERO)
		await _physics_costs()
		get_tree().quit()
		return
	if args.has("anim_after"):              # walked into the fight; time every AnimationTree's advance by owner type
		_rows.pop_back()
		_press(Vector2.ZERO)
		await _anim_costs()
		get_tree().quit()
		return
	if args.has("toggle_after"):            # walked into the fight; now A/B a few engine-side suspects, alternating
		_rows.pop_back()
		_press(Vector2.ZERO)
		await _toggles()
		get_tree().quit()
		return
	if args.has("ablate_after"):            # walked `--seconds` to stir the monsters up; now attribute the frame where it stopped
		_rows.pop_back()
		_press(Vector2.ZERO)
		await _ablate_scripts(false)
		get_tree().quit()
		return
	_report()
	get_tree().quit()

## Spawn points and the map's named places, ordered greedily nearest-first from the hero.
func _stops(map: MapRoot, from: Vector3) -> Array:
	var nav := map.nav_region.get_navigation_map()
	var pts: Array = []
	for id in map.spawns:
		pts.append([String(id), (map.spawns[id] as Node3D).global_position])
	for p: Dictionary in DataIsland.PLACES:
		if StringName(p.get("map", "")) == Game.current_map_id and p.get("pos") is Vector2:
			var v: Vector2 = p.pos
			pts.append([String(p.id), Vector3(v.x, 50.0, v.y)])
	# small maps (interiors, an arena) have one or two named spots: add random reachable points so there is a walk to sample
	var rng := RandomNumberGenerator.new()
	rng.seed = 37
	var extra := maxi(0, 8 - pts.size())
	for i in extra:
		var rp := NavigationServer3D.map_get_random_point(nav, 1, false)
		pts.append(["random_%d" % i, rp])
	var out: Array = []
	var cur := from
	while not pts.is_empty():
		var best := 0
		var bd := INF
		for i in pts.size():
			var d := cur.distance_to(pts[i][1] as Vector3)
			if d < bd:
				bd = d
				best = i
		var p: Array = pts.pop_at(best)
		p[1] = NavigationServer3D.map_get_closest_point(nav, p[1])
		out.append(p)
		cur = p[1]
	return out

func _walk(map: MapRoot, hero: Player, stops: Array) -> void:
	var nav := map.nav_region.get_navigation_map()
	var vp := get_viewport().get_viewport_rid()
	var limit := float(args.get("seconds", "150")) * 1000.0
	var spike := float(args.get("spike", "20"))
	var mm: MiniMap = null
	var mms := Game.ui_root.find_children("*", "MiniMap", true, false)
	if not mms.is_empty():
		mm = mms[0]
	var cam: PlayerCamera = hero.camera
	var t_start := Time.get_ticks_msec()
	_nodes0 = get_tree().get_node_count()
	_parts0 = get_tree().root.find_children("*", "GPUParticles3D", true, false).size()
	var last := Time.get_ticks_usec()
	var pf := Engine.get_physics_frames()
	var pipes := _pipelines()
	var lights_on := int(Perf.stats.lights_on)
	var lights_set := _lit_set()
	var faded := cam._faded.size()
	var stuck := 0
	var mm_drawn := false                # the minimap asked for a render last frame: it was drawn inside this frame's window
	var still_frames := 0
	var moving_frames := 0
	var prev_pos := hero.global_position
	var prev_vis := hero.visual.global_position if hero.visual else Vector3.ZERO
	var vis_still := 0
	var vis_steps: Array[float] = []           # drawn movement per frame while walking (m), for a smoothness figure
	# the route again (backwards) while time is left: a small map is still walked for the whole sample
	var route := stops.duplicate()
	for pass_i in 3:
		if pass_i > 0:
			stops.reverse()
			route.append_array(stops)
	for s in route:
		if Time.get_ticks_msec() - t_start > limit or Game.current_map != map or Game.player != hero:
			break
		var path := NavigationServer3D.map_get_path(nav, hero.global_position, s[1], true)
		var k := 0
		var best_d := INF
		var since_best := 0.0
		while k < path.size():
			var to: Vector3 = path[k]
			var d := Vector2(to.x - hero.global_position.x, to.z - hero.global_position.z)
			if d.length() < 0.9:
				k += 1
				best_d = INF
				continue
			if _skip_cutscene():
				await _wait(30)
				last = Time.get_ticks_usec()
				pf = Engine.get_physics_frames()
				pipes = _pipelines()
				_added.clear()
				continue
			var dir := d.normalized()
			_press(dir)
			var mm_at: Vector3 = mm._cam.global_position if mm else Vector3.ZERO
			_marks.clear()
			await get_tree().process_frame
			# the minimap moves its top-down camera exactly when it asks for a re-render (drawn in this frame)
			var mm_due := mm != null and mm._cam.global_position != mm_at
			if mm_due:
				_mm_frames += 1
			var seg := _marks.duplicate()       # the previous frame's draw, then this frame's physics steps and process
			var now := Time.get_ticks_usec()
			var dt := (now - last) / 1000.0
			last = now
			var steps := Engine.get_physics_frames() - pf
			pf = Engine.get_physics_frames()
			var moved := hero.global_position.distance_to(prev_pos)
			prev_pos = hero.global_position
			if moved < 0.0005:
				still_frames += 1
			else:
				moving_frames += 1
			if hero.visual:
				var vm := hero.visual.global_position.distance_to(prev_vis)
				prev_vis = hero.visual.global_position
				if hero.velocity.length() > 2.0 and dt < 40.0:
					if vm < 0.0005:
						vis_still += 1
					vis_steps.append(vm / maxf(dt, 0.1))
			var p2 := _pipelines()
			var comp := p2 - pipes
			pipes = p2
			var lit := _lit_set()
			var lchg := 0
			for l in lit:
				if not lights_set.has(l):
					lchg += 1
			lights_set = lit
			var row := {"t": snappedf((now / 1000.0 - t_start), 1.0), "frame": dt, "steps": steps,
				"proc": Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
				"phys": Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
				"gpu": RenderingServer.viewport_get_measured_render_time_gpu(vp),
				"cpu_render": RenderingServer.viewport_get_measured_render_time_cpu(vp),
				"draws": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
				"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
				"pipelines": comp, "awake": Enemy._awake_n}
			_rows.append(row)
			if dt > spike:
				var ev := {"t_ms": Time.get_ticks_msec() - t_start, "frame": snappedf(dt, 0.1), "steps": steps,
					"proc": snappedf(row.proc, 0.1), "phys": snappedf(row.phys, 0.1), "gpu": snappedf(row.gpu, 0.1),
					"cpu_render": snappedf(row.cpu_render, 0.1), "pipelines": comp, "added": _added.duplicate(), "awake": Enemy._awake_n,
					"minimap": mm_drawn, "phases": _phases(seg), "origins": _origins.duplicate(), "lights_switched": lchg, "fades": cam._faded.size() - faded, "stop": s[0],
					"pos": "%.0f,%.1f,%.0f" % [hero.global_position.x, hero.global_position.y, hero.global_position.z]}
				_spikes.append(ev)
				print("SPIKE ", JSON.stringify(ev))
			_added.clear()
			_origins.clear()
			mm_drawn = mm_due
			faded = cam._faded.size()
			# stuck: no closer to this path point for 3 s -> skip ahead (counted; a real player would walk round)
			var dd := d.length()
			if dd < best_d - 0.05:
				best_d = dd
				since_best = 0.0
			else:
				since_best += dt / 1000.0
				if since_best > 3.0:
					stuck += 1
					print("STUCK near %s heading for %s: hop to the next path point" % [hero.global_position, s[0]])
					hero.global_position = to + Vector3.UP * 0.3
					k += 1
					best_d = INF
					since_best = 0.0
			if Time.get_ticks_msec() - t_start > limit or Game.current_map != map or Game.player != hero:
				print("WALKNOTE left the map or time is up")
				break
	_press(Vector2.ZERO)
	# smoothness: how unevenly the drawn hero advances per millisecond while walking (coefficient of variation, 0 = even)
	var cv := 0.0
	if vis_steps.size() > 10:
		var mean := 0.0
		for v in vis_steps:
			mean += v
		mean /= vis_steps.size()
		var var_ := 0.0
		for v in vis_steps:
			var_ += (v - mean) * (v - mean)
		cv = sqrt(var_ / vis_steps.size()) / maxf(mean, 0.000001)
	_rows.append({"stuck": stuck, "still": still_frames, "moving": moving_frames, "vis_still": vis_still,
		"vis_frames": vis_steps.size(), "vis_cv": cv})

## Gaps between the frame's engine signals (ms): e.g. "post>phys" is what ran between the last draw and the first physics
## step (input, timers), "proc>pre" the idle-time scripts and deferred calls, "pre>post" the render.
func _phases(seg: Array) -> String:
	var parts := []
	for i in range(1, seg.size()):
		var ms: float = (seg[i][1] - seg[i - 1][1]) / 1000.0
		if ms >= 1.0:
			parts.append("%s>%s %.1f" % [seg[i - 1][0], seg[i][0], ms])
	return ", ".join(parts)

func _press(dir: Vector2) -> void:
	for a in [&"move_left", &"move_right", &"move_up", &"move_down"]:
		Input.action_release(a)
	if dir == Vector2.ZERO:
		return
	if dir.x > 0.01:
		Input.action_press(&"move_right", dir.x)
	elif dir.x < -0.01:
		Input.action_press(&"move_left", -dir.x)
	if dir.y > 0.01:
		Input.action_press(&"move_down", dir.y)
	elif dir.y < -0.01:
		Input.action_press(&"move_up", -dir.y)

func _pipelines() -> int:
	return int(Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_CANVAS) + Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_MESH)
		+ Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_SURFACE) + Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_DRAW)
		+ Performance.get_monitor(Performance.PIPELINE_COMPILATIONS_SPECIALIZATION))

func _lit_set() -> Dictionary:
	var d := {}
	for l in Perf._lights:
		if is_instance_valid(l) and not Perf._off_lights.has(l):
			d[l] = true
	return d

func _report() -> void:
	var meta: Dictionary = _rows.pop_back()
	var ft: Array[float] = []
	var sums := {"proc": 0.0, "phys": 0.0, "gpu": 0.0, "cpu_render": 0.0, "draws": 0.0, "objects": 0.0, "steps": 0.0, "awake": 0.0}
	var total := 0.0
	var zero_steps := 0
	var multi_steps := 0
	for r: Dictionary in _rows:
		ft.append(float(r.frame))
		total += float(r.frame)
		for k in sums:
			sums[k] += float(r[k])
		if int(r.steps) == 0:
			zero_steps += 1
		elif int(r.steps) > 1:
			multi_steps += 1
	if ft.is_empty():
		ft.append(0.0)
	var n := maxi(1, ft.size())
	var sorted := ft.duplicate()
	sorted.sort()
	var worst1 := sorted.slice(int(n * 0.99))
	var w1 := 0.0
	for x in worst1:
		w1 += x
	var over := func(ms: float) -> int: return ft.filter(func(x): return x > ms).size()
	var rep := {"map": String(Game.current_map_id), "frames": n, "seconds": snappedf(total / 1000.0, 0.1),
		"avg_fps": snappedf(1000.0 * n / maxf(1.0, total), 0.1), "low1_fps": snappedf(1000.0 / maxf(0.01, w1 / maxf(1, worst1.size())), 0.1),
		"median_ms": snappedf(sorted[n / 2], 0.01), "p99_ms": snappedf(sorted[int(n * 0.99)], 0.01), "max_ms": snappedf(sorted[-1], 0.1),
		"over_17ms": over.call(17.5), "over_25ms": over.call(25.0), "over_33ms": over.call(34.0), "over_50ms": over.call(50.0),
		"zero_step_frames": zero_steps, "multi_step_frames": multi_steps, "stuck": meta.stuck, "minimap_renders": _mm_frames, "drawn_still_while_walking": meta.vis_still,
		"walking_frames": meta.vis_frames, "drawn_speed_unevenness": snappedf(meta.vis_cv, 0.001),
		"hero_still_frames": meta.still, "hero_moving_frames": meta.moving, "vsync": Settings.vsync, "lite": Settings.lite}
	for k in sums:
		rep["avg_" + k] = snappedf(sums[k] / n, 0.01)
	rep["nodes_start"] = _nodes0
	rep["nodes_end"] = get_tree().get_node_count()
	rep["particles_start"] = _parts0
	rep["particles_end"] = get_tree().root.find_children("*", "GPUParticles3D", true, false).size()
	rep["spikes"] = _spikes
	# spike causes, counted
	var causes := {"pipelines": 0, "minimap": 0, "lights": 0, "fades": 0, "multi_step": 0, "nodes_added": 0}
	for e: Dictionary in _spikes:
		if int(e.pipelines) > 0: causes.pipelines += 1
		if e.minimap: causes.minimap += 1
		if int(e.lights_switched) > 0: causes.lights += 1
		if int(e.fades) != 0: causes.fades += 1
		if int(e.steps) > 1: causes.multi_step += 1
		if not (e.added as Dictionary).is_empty(): causes.nodes_added += 1
	rep["spike_causes"] = causes
	var brief := rep.duplicate()
	brief.erase("spikes")
	print("WALKSUM ", JSON.stringify(brief))
	if args.has("out"):
		var f := FileAccess.open(String(args.out), FileAccess.WRITE)
		f.store_string(JSON.stringify(rep, "  "))
		f.close()

func _wait(frames: int) -> void:
	for i in frames:
		await get_tree().process_frame
		_skip_cutscene()

## A fresh probe hero meets first-landing cutscenes (Terax on Agdao's pier): skip them, they are not the map.
func _skip_cutscene() -> bool:
	if CutscenePlayer.is_playing() and CutscenePlayer.active:
		CutscenePlayer.active.skip_all()
		return true
	return false

## What a save costs on the main thread, step by step (bh-037), for the loaded hero.
func _save_bench() -> void:
	var h: HeroData = Game.hero
	var ms := func(f: Callable, n := 5) -> float:
		var t0 := Time.get_ticks_usec()
		for i in n:
			f.call()
		return (Time.get_ticks_usec() - t0) / 1000.0 / n
	var d: Dictionary = SaveSystem.serialize(h)
	var txt := JSON.stringify(d, "  ")
	print("SAVEBENCH sync_all %.1f ms, serialize %.1f ms, duplicate %.1f ms, stringify %.1f ms, parse %.1f ms, bytes %d" % [
		ms.call(func(): TempoParty.sync_all()), ms.call(func(): SaveSystem.serialize(h)), ms.call(func(): d.duplicate(true)),
		ms.call(func(): JSON.stringify(d, "  ")), ms.call(func(): JSON.parse_string(txt)), txt.length()])
	print("SAVEPARTS quake %.1f, guild_jobs %.1f, guild_world %.1f, own_guild %.1f, tempos %.1f, equipment %.1f, inventory %.1f, shops %.1f, look %.1f, settings %.1f, pics %.1f" % [
		ms.call(func(): h.quake_team.map(func(m): return m.to_dict())), ms.call(func(): GuildJobs.to_dict(h)),
		ms.call(func(): GuildRegistry.world_to_plain(h)), ms.call(func(): OwnGuild.to_plain(h.own_guild)),
		ms.call(func(): h.tempos.map(func(t): return t.to_dict())), ms.call(func(): h.equipment.to_dict()),
		ms.call(func(): h.inventory.to_array()), ms.call(func(): HeroData._keyed_out(h.shops)),
		ms.call(func(): HeroLook.to_save(HeroLook.sanitize(h.look))), ms.call(func(): Settings.to_dict()),
		ms.call(func(): Marshalls.raw_to_base64(h.profile_pic) + Marshalls.raw_to_base64(h.id_pic))])
	print("SAVEPARTS2 to_dict %.1f, progress %.1f, skills %.1f, talents %.1f, flags %.1f, dialogue %.1f, npcs %.1f, miniboss %.1f, transcend %.1f, banner %.1f, remote %.1f, spirit %.1f, stages %.1f" % [
		ms.call(func(): h.to_dict()), ms.call(func(): h.progress.to_dict()), ms.call(func(): h.skill_tree.to_dict()),
		ms.call(func(): h.talent_tree.to_dict()), ms.call(func(): h._flags_out()), ms.call(func(): h._dialogue_out()),
		ms.call(func(): HeroData._keyed_out(h.npc_state)), ms.call(func(): HeroData._keyed_out(h.miniboss_log)),
		ms.call(func(): ClassTranscendence.to_save(h)), ms.call(func(): Marshalls.raw_to_base64(h.guild_banner)),
		ms.call(func(): GuildRegistry.remote_to_plain(h.remote_guild) if not h.remote_guild.is_empty() else {}),
		ms.call(func(): h.spirit_hall.map(func(t): return t.to_dict())), ms.call(func(): HeroData._keyed_plain(h.stages_cleared))])
	var b := var_to_bytes(d)
	print("SAVEPARTS3 var_to_bytes %.1f, bytes_to_var %.1f, compact stringify %.1f, duplicate %.1f, to_dict %.1f, serialize %.1f" % [
		ms.call(func(): var_to_bytes(d), 10), ms.call(func(): bytes_to_var(b), 10), ms.call(func(): JSON.stringify(d), 10),
		ms.call(func(): d.duplicate(true), 10), ms.call(func(): h.to_dict(), 10), ms.call(func(): SaveSystem.serialize(h), 10)])

## Every architecture piece the follow camera could fade (children of Geometry/Props with meshes), faded in turn right in
## front of the camera for a frame, as PlayerCamera does: the worst frame and the pipeline compilations it costs (bh-037).
func _fade_all(map: MapRoot, hero: Player) -> void:
	var roots: Array = []
	for g in map.find_children("Geometry", "Node3D", true, false) + map.find_children("Props", "Node3D", true, false):
		for c in g.get_children():
			if c is Node3D and not (c as Node).find_children("*", "MeshInstance3D", true, false).is_empty():
				roots.append(c)
	var cam: PlayerCamera = hero.camera
	var worst := 0.0
	var total_pipes := 0
	var slow := 0
	var p0 := _pipelines()
	var last := Time.get_ticks_usec()
	for r: Node3D in roots:
		var meshes := r.find_children("*", "MeshInstance3D", true, false)
		var saved := []
		for mi: MeshInstance3D in meshes:
			var orig := {}
			for si in mi.mesh.get_surface_count():
				orig[si] = mi.get_surface_override_material(si)
				mi.set_surface_override_material(si, MaterialLibrary.see_through(mi.get_active_material(si)))
			saved.append([mi, orig])
		# stand the hero just south of the piece so the camera sees it, as when it hides the hero
		hero.global_position = r.global_position + Vector3(0, 0.5, 4.0)
		cam.snap()
		await get_tree().process_frame
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		var dt := (now - last) / 2000.0
		last = now
		var p := _pipelines()
		total_pipes += p - p0
		p0 = p
		worst = maxf(worst, dt)
		if dt > 20.0:
			slow += 1
		for sv in saved:
			for si in sv[1]:
				(sv[0] as MeshInstance3D).set_surface_override_material(si, sv[1][si])
	print("FADEALL roots=%d pipelines=%d worst_pair_ms=%.1f slow_pairs=%d" % [roots.size(), total_pipes, worst, slow])

## Per-script attribution with the hero standing at `--spawn` (default start) and the party around: each script's (or engine
## class's internal) per-frame callbacks off in turn, median frame of 150 measured against all-on (bh-037; perf_probe's
## _ablate_process for a walk-probe session, which can load a real save).
func _ablate_scripts(place := true) -> void:
	if place:
		Game.place_player(StringName(args.get("spawn", "start")))
		await _wait(120)
	print("ABL awake monsters %d, enemies in tree %d" % [Enemy._awake_n, get_tree().get_nodes_in_group(&"enemy").size()])
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
	var base := await _median_frame()
	print("ABL all_on %.2f ms (%d groups) physics %.2f ms/step" % [base, groups.size(), Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0])
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
		var m := await _median_frame()
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
	for r in res.slice(0, 25):
		print("ABL %6.2f ms  %-44s x%d" % [r[0], r[1], r[2]])

func _median_frame() -> float:
	var t: Array[float] = []
	var last := Time.get_ticks_usec()
	for i in 150:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		t.append((now - last) / 1000.0)
		last = now
	t.sort()
	return t[t.size() / 2]

## Physics-step attribution (bh-037): every node with a script _physics_process is taken off the engine's list and stepped by
## this probe instead, timed per script, for `--cost_frames` steps (default 180). The engine's own step (Jolt, navigation,
## internal processing) is the rest of TIME_PHYSICS_PROCESS. Gameplay goes on (the same callbacks run, in another order).
var _cost_nodes: Array = []
var _cost_us := {}
var _cost_n := {}
var _detached: Array = []
var _keep_v: Node = null
var _cost_on := false
var _cost_steps := 0

func _physics_process(delta: float) -> void:
	if not _cost_on:
		return
	_cost_steps += 1
	for n in _cost_nodes:
		if not is_instance_valid(n) or not n.is_inside_tree():
			continue
		var k: String = n.get_script().resource_path.get_file()
		var t0 := Time.get_ticks_usec()
		n._physics_process(delta)
		_cost_us[k] = int(_cost_us.get(k, 0)) + (Time.get_ticks_usec() - t0)

func _physics_costs() -> void:
	var frames := int(args.get("cost_frames", "180"))
	_cost_nodes.clear()
	for n in get_tree().root.find_children("*", "", true, false):
		if n != self and n.get_script() and n.is_physics_processing() and n.has_method(&"_physics_process"):
			_cost_nodes.append(n)
			var k: String = n.get_script().resource_path.get_file()
			_cost_n[k] = int(_cost_n.get(k, 0)) + 1
	var tot := 0.0
	var nav := 0.0
	var samples := 0
	for n in _cost_nodes:
		n.set_physics_process(false)
	process_physics_priority = -1000           # step them before anything else, roughly where the engine would
	_cost_on = true
	for i in frames:
		await get_tree().physics_frame
		tot += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0
		nav += Performance.get_monitor(Performance.TIME_NAVIGATION_PROCESS) * 1000.0
		samples += 1
	_cost_on = false
	for n in _cost_nodes:
		if is_instance_valid(n):
			n.set_physics_process(true)
	var steps := maxi(1, _cost_steps)
	var keys := _cost_us.keys()
	keys.sort_custom(func(a, b): return _cost_us[a] > _cost_us[b])
	var scripts := 0.0
	print("COST awake=%d enemies=%d steps=%d physics_step_avg=%.2f ms nav=%.2f ms" % [Enemy._awake_n, get_tree().get_nodes_in_group(&"enemy").size(),
		steps, tot / maxf(1, samples), nav / maxf(1, samples)])
	for k in keys:
		var ms := float(_cost_us[k]) / 1000.0 / steps
		scripts += ms
		print("COST %7.3f ms/step  %-34s x%d (%.0f us each)" % [ms, k, _cost_n.get(k, 0), ms * 1000.0 / maxf(1, _cost_n.get(k, 1))])
	print("COST scripts %.2f ms/step, engine rest %.2f ms/step" % [scripts, tot / maxf(1, samples) - scripts])
	var census := {}
	var internal := {}
	for n in get_tree().root.find_children("*", "", true, false):
		for cls in ["RigidBody3D", "PhysicalBone3D", "PhysicalBoneSimulator3D", "Area3D", "CharacterBody3D", "StaticBody3D", "AnimatableBody3D",
				"RayCast3D", "ShapeCast3D", "NavigationAgent3D", "VehicleBody3D", "SoftBody3D", "GPUParticles3D", "CollisionShape3D"]:
			if n.is_class(cls):
				census[cls] = int(census.get(cls, 0)) + 1
		if n is Area3D and (n as Area3D).monitoring:
			census["Area3D_monitoring"] = int(census.get("Area3D_monitoring", 0)) + 1
		if n is RigidBody3D and not (n as RigidBody3D).sleeping and not (n as RigidBody3D).freeze:
			census["RigidBody3D_awake"] = int(census.get("RigidBody3D_awake", 0)) + 1
		if n is PhysicalBoneSimulator3D and (n as PhysicalBoneSimulator3D).is_simulating_physics():
			census["ragdolls_simulating"] = int(census.get("ragdolls_simulating", 0)) + 1
		if n.is_physics_processing_internal():
			internal[n.get_class()] = int(internal.get(n.get_class(), 0)) + 1
	print("COST census ", census)
	print("COST physics-internal nodes ", internal)
	# the engine's share by class: internal physics callbacks off in turn, average step over 90 steps
	var avg_step := func() -> float:
		var v: Array[float] = []
		for i in 90:
			await get_tree().physics_frame
			v.append(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0)
		v.sort()
		return v[45]
	# where the particle systems live: the nearest named ancestor with a script, else the parent's name
	var owners := {}
	for gp in get_tree().root.find_children("*", "GPUParticles3D", true, false):
		var a: Node = gp.get_parent()
		var label := ""
		for i in 8:
			if a == null:
				break
			if a.get_script():
				label = a.get_script().resource_path.get_file()
				break
			a = a.get_parent()
		if label == "":
			label = "parent:" + String(gp.get_parent().name).left(18)
		label += (" emitting" if gp.emitting else " idle") + (" visible" if gp.is_visible_in_tree() else " hidden")
		owners[label] = int(owners.get(label, 0)) + 1
	var ok_ := owners.keys()
	ok_.sort_custom(func(a, b): return owners[a] > owners[b])
	var idle := {}
	for gp: GPUParticles3D in get_tree().root.find_children("*", "GPUParticles3D", true, false):
		if not gp.emitting:
			var chain := "%s<%s<%s one_shot=%s amount=%d" % [gp.name, gp.get_parent().name, gp.get_parent().get_parent().name if gp.get_parent().get_parent() else "-", gp.one_shot, gp.amount]
			chain = chain.replace("@", "")
			for d in "0123456789":
				chain = chain.replace(d, "")
			idle[chain] = int(idle.get(chain, 0)) + 1
	var ik := idle.keys()
	ik.sort_custom(func(a, b): return idle[a] > idle[b])
	print("COST idle particles ", ", ".join(ik.slice(0, 12).map(func(k): return "%s x%d" % [k, idle[k]])))
	print("COST particles by owner ", ", ".join(ok_.slice(0, 14).map(func(k): return "%s=%d" % [k, owners[k]])))
	var base: float = await avg_step.call()
	print("COST experiment base step median %.2f ms" % base)
	for cls in ["GPUParticles3D", "NavigationAgent3D", "AudioStreamPlayer3D"]:
		var nodes := get_tree().root.find_children("*", cls, true, false).filter(func(n): return n.is_physics_processing_internal())
		for n in nodes:
			n.set_physics_process_internal(false)
		var m: float = await avg_step.call()
		for n in nodes:
			if is_instance_valid(n):
				n.set_physics_process_internal(true)
		var b2: float = await avg_step.call()
		print("COST without %s internal physics (%d): median %.2f ms (base again %.2f)" % [cls, nodes.size(), m, b2])
	print("COST server: active=%d pairs=%d islands=%d" % [Performance.get_monitor(Performance.PHYSICS_3D_ACTIVE_OBJECTS),
		Performance.get_monitor(Performance.PHYSICS_3D_COLLISION_PAIRS), Performance.get_monitor(Performance.PHYSICS_3D_ISLAND_COUNT)])

## Do one-shot effects free themselves (bh-037)? 20 hit bursts and 20 dust puffs at the hero, then count what is left.
func _fx_leak() -> void:
	var hero: Node3D = Game.player
	var before := get_tree().root.find_children("*", "GPUParticles3D", true, false).size()
	var probes: Array = []
	for i in 20:
		var a := VFXLib.hit_burst(hero.global_position, 0, 0.5, false)
		FX.spawn(a, hero.global_position + Vector3(i * 0.2, 1, 0))
		var b := VFXLib.dust_puff()
		FX.spawn(b, hero.global_position + Vector3(i * 0.2, 1, 1))
		probes.append(a)
		probes.append(b)
	var first: GPUParticles3D = (probes[0] as Node).get_child(0)
	var fin := [0]
	first.finished.connect(func(): fin[0] += 1)
	for i in 240:
		await get_tree().process_frame
	var alive := probes.filter(func(n): return is_instance_valid(n)).size()
	var after := get_tree().root.find_children("*", "GPUParticles3D", true, false).size()
	print("FXLEAK spawned 40 effects; holders/puffs still alive after 4 s: %d; particle systems before %d after %d; finished fired %d; first emitting=%s" % [
		alive, before, after, fin[0], str(first.emitting) if is_instance_valid(first) else "freed"])

func _toggles() -> void:
	var med := func() -> Array:
		var t: Array[float] = []
		var pf := Engine.get_physics_frames()
		var last := Time.get_ticks_usec()
		for i in 200:
			await get_tree().process_frame
			var now := Time.get_ticks_usec()
			t.append((now - last) / 1000.0)
			last = now
		t.sort()
		return [t[100], float(Engine.get_physics_frames() - pf) / 200.0]
	var phys_med := func() -> float:
		var v: Array[float] = []
		for i in 120:
			await get_tree().physics_frame
			v.append(Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0)
		v.sort()
		return v[60]
	var set_mode := func(mode: String, off: bool) -> void:
		match mode:
			"particles_internal":
				for n in get_tree().root.find_children("*", "GPUParticles3D", true, false):
					n.set_physics_process_internal(not off)
					n.set_process_internal(not off)
			"nav_agents":
				for n in get_tree().root.find_children("*", "NavigationAgent3D", true, false):
					n.process_mode = Node.PROCESS_MODE_DISABLED if off else Node.PROCESS_MODE_INHERIT
			"audio3d":
				for n in get_tree().root.find_children("*", "AudioStreamPlayer3D", true, false):
					n.set_physics_process_internal(not off)
			"anim":
				for n in get_tree().root.find_children("*", "AnimationTree", true, false):
					n.active = not off
			"bars":
				for n in get_tree().root.find_children("*", "EnemyBar", true, false):
					n.process_mode = Node.PROCESS_MODE_DISABLED if off else Node.PROCESS_MODE_INHERIT
					n.visible = not off
			"bone_sims":
				for n in get_tree().root.find_children("*", "PhysicalBoneSimulator3D", true, false):
					(n as SkeletonModifier3D).active = not off
			"bone_sims_detach":                 # out of the skeleton altogether (a modifier child may keep it updating)
				if off:
					_detached.clear()
					for n in get_tree().root.find_children("*", "PhysicalBoneSimulator3D", true, false):
						var sk: Node = n.get_parent()
						sk.remove_child(n)
						_detached.append([sk, n])
				else:
					for pair in _detached:
						if is_instance_valid(pair[0]):
							(pair[0] as Node).add_child(pair[1], false, Node.INTERNAL_MODE_BACK)
					_detached.clear()
			"attachments":
				for n in get_tree().root.find_children("*", "BoneAttachment3D", true, false):
					n.process_mode = Node.PROCESS_MODE_DISABLED if off else Node.PROCESS_MODE_INHERIT
					(n as BoneAttachment3D).set_notify_transform(not off)
			"physics_server":
				PhysicsServer3D.set_active(not off)
			"nav_server":
				NavigationServer3D.set_active(not off)
			"particles_hidden":
				for n in get_tree().root.find_children("*", "GPUParticles3D", true, false):
					n.visible = not off
	print("TOGGLE census skeletons=%d bone_sims=%d active_sims=%d attachments=%d meshes_under_skeletons=%d" % [
		get_tree().root.find_children("*", "Skeleton3D", true, false).size(),
		get_tree().root.find_children("*", "PhysicalBoneSimulator3D", true, false).size(),
		get_tree().root.find_children("*", "PhysicalBoneSimulator3D", true, false).filter(func(n): return n.active).size(),
		get_tree().root.find_children("*", "BoneAttachment3D", true, false).size(),
		get_tree().root.find_children("*", "Skeleton3D", true, false).reduce(func(acc, sk): return acc + sk.find_children("*", "MeshInstance3D", true, false).size(), 0)])
	var modes: Array = String(args.get("modes", "particles_internal,particles_hidden,nav_agents,audio3d,anim,bars")).split(",")
	for mode in modes:
		var on_v: Array[float] = []
		var off_v: Array[float] = []
		for r in 3:
			var a: Array = await med.call()
			on_v.append(a[0])
			set_mode.call(mode, true)
			await _wait(5)
			var b: Array = await med.call()
			off_v.append(b[0])
			set_mode.call(mode, false)
			await _wait(5)
		on_v.sort()
		off_v.sort()
		set_mode.call(mode, true)
		await _wait(5)
		var p_off: float = await phys_med.call()
		set_mode.call(mode, false)
		await _wait(5)
		var p_on: float = await phys_med.call()
		print("TOGGLE %-20s on %.2f ms  off %.2f ms  (saves %.2f) runs on=%s off=%s | physics step median on %.2f off %.2f" % [mode, on_v[1], off_v[1], on_v[1] - off_v[1], on_v, off_v, p_on, p_off])

## What a monster spawned mid-fight costs (bh-037): every kind on this map and every kind they can call, built near the hero
## a few times, one at a time. Times: Enemy.new + setup, add_child (its _ready: shape, agent, visual, bar), and the next
## two frames (its first pose, skeleton and draw). The visual alone (CharacterVisual.setup + Persona.apply + weapon) is
## timed on a loose copy too.
func _spawn_bench() -> void:
	var map: MapRoot = Game.current_map
	var at: Vector3 = (Game.player as Node3D).global_position + Vector3(6, 0, 0)
	var kinds := {}
	for e in get_tree().get_nodes_in_group(&"enemy"):
		kinds[(e as Enemy).def.id] = true
	for id in kinds.keys():
		var d := DB.enemy(id)
		for a in d.attacks + d.abilities:
			if a is Dictionary and a.has("summon"):
				kinds[StringName(a.summon)] = true
	if args.has("kinds"):
		kinds.clear()
		for k in String(args.kinds).split(","):
			kinds[StringName(k)] = true
	var diff: Dictionary = Spawner.current().difficulty if Spawner.current() else {}
	var reps := int(args.get("reps", "3"))
	for id in kinds:
		var d := DB.enemy(id)
		if d == null:
			continue
		var t_new := 0.0
		var t_add := 0.0
		var t_vis := 0.0
		var t_f := 0.0
		var t_apply := 0.0
		var t_anim := 0.0
		var t_skel := 0.0
		var t_op := 0.0
		for r in reps:
			await _wait(20)
			var v0 := Time.get_ticks_usec()
			var v := CharacterVisual.new()
			add_child(v)
			var persona := Persona.for_enemy(d)
			if not persona.is_empty():
				v.setup(Persona.MODEL, d.model_scale, d.tint, &"")
				var va := Time.get_ticks_usec()
				Persona.apply(v, persona)
				t_apply += (Time.get_ticks_usec() - va) / 1000.0
			else:
				v.setup(CreatureSwaps.model(d.model), d.model_scale, d.tint, &"")
			if d.weapon != "":
				v.attach_weapon(&"main", d.weapon)
			t_vis += (Time.get_ticks_usec() - v0) / 1000.0
			if r == 0:
				var info := []
				for m in v._meshes:
					if not is_instance_valid(m) or m.mesh == null:
						continue
					for si in m.mesh.get_surface_count():
						var src: Material = m.get_surface_override_material(si)
						if src == null:
							src = m.mesh.surface_get_material(si)
						info.append("%s:%s%s%s" % [m.name, src.get_class() if src else "null", " ovr" if m.material_override else "",
							" cached" if src and MaterialLibrary._faded.has(src) else ""])
				print("SPAWNMATS %s %s" % [id, ", ".join(info)])
			if r == 0:
				var per := []
				for m in v._meshes:
					if not is_instance_valid(m) or m.mesh == null or m.material_override is ShaderMaterial:
						continue
					for si in m.mesh.get_surface_count():
						var src: Material = m.get_surface_override_material(si)
						if src == null:
							src = m.mesh.surface_get_material(si)
						if not (src is BaseMaterial3D):
							continue
						var d0 := Time.get_ticks_usec()
						var c: BaseMaterial3D = src.duplicate()
						var d1 := Time.get_ticks_usec()
						c.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
						var d2 := Time.get_ticks_usec()
						per.append("%s/%d %s dup %.2f hash %.2f (tex %s, nm %s, emis %s, shading %d, next %s)" % [m.name, si, src.resource_name, (d1 - d0) / 1000.0, (d2 - d1) / 1000.0,
							src.albedo_texture != null, src.normal_enabled, src.emission_enabled, src.shading_mode, src.next_pass != null])
				print("SPAWNPER %s
  %s" % [id, "
  ".join(per)])
			var ve := Time.get_ticks_usec()
			v._ensure_local_materials()
			var ve2 := Time.get_ticks_usec()
			if v.hero:
				v.hero.set_opacity(0.7)
			var ve3 := Time.get_ticks_usec()
			print("SPAWNOP2 %s ensure_local %.2f ms, hero.set_opacity %.2f ms" % [id, (ve2 - ve) / 1000.0, (ve3 - ve2) / 1000.0])
			var vo := Time.get_ticks_usec()
			v.set_opacity(0.7)
			var op_ms := (Time.get_ticks_usec() - vo) / 1000.0
			t_op += op_ms
			print("SPAWNOP %s rep %d set_opacity %.2f ms (%d local materials, previous copy %s)" % [id, r, op_ms,
				v._local_mats.values().reduce(func(acc, arr): return acc + arr.size(), 0), "alive" if _keep_v != null else "none"])
			if _keep_v != null and args.has("keep_prev"):
				_keep_v.queue_free()
			if args.has("keep_prev"):
				_keep_v = v
			else:
				v.queue_free()
			await _wait(20)
			var t0 := Time.get_ticks_usec()
			var e := Enemy.new()
			e.setup(d, 1, [], diff)
			var t1 := Time.get_ticks_usec()
			map.add_child(e)
			e.global_position = at + Vector3(r * 2.0, 0.1, 0)
			var t2 := Time.get_ticks_usec()
			if e.visual and e.visual.tree:
				var ta := Time.get_ticks_usec()
				e.visual.tree.advance(0.016)
				t_anim += (Time.get_ticks_usec() - ta) / 1000.0
				var sk := e.visual.find_children("*", "Skeleton3D", true, false)
				ta = Time.get_ticks_usec()
				for s3 in sk:
					(s3 as Skeleton3D).force_update_all_bone_transforms()
				t_skel += (Time.get_ticks_usec() - ta) / 1000.0
			t2 = Time.get_ticks_usec()
			await get_tree().process_frame
			await get_tree().process_frame
			var t3 := Time.get_ticks_usec()
			t_new += (t1 - t0) / 1000.0
			t_add += (t2 - t1) / 1000.0
			t_f += (t3 - t2) / 1000.0
			e.queue_free()
		print("SPAWN %-22s persona=%-5s new %.2f  add/_ready %.2f  first anim advance %.2f  skeleton %.2f  next 2 frames %.1f ms | visual alone %.2f (outfit %.2f) set_opacity %.2f" % [
			id, str(not Persona.for_enemy(d).is_empty()), t_new / reps, t_add / reps, t_anim / reps, t_skel / reps, t_f / reps, t_vis / reps, t_apply / reps, t_op / reps])
	var b0 := Time.get_ticks_usec()
	for i in 4:
		await get_tree().process_frame
	print("SPAWN baseline 2 frames %.1f ms" % ((Time.get_ticks_usec() - b0) / 2000.0))

## What a status landing on the hero costs (bh-037): each one applied (timed: the call, the visual alone), then the next
## two frames (HUD icon, first draw), then removed. Run twice per status: the second shows what stays cold.
func _status_bench() -> void:
	var hero: Player = Game.player
	var ids := [&"burning", &"shocked", &"cursed", &"chilled", &"wet", &"poisoned", &"armor_broken", &"windswept", &"purged",
		&"frozen", &"stunned", &"staggered", &"bleeding", &"haste", &"empowered", &"slowed", &"hex_frailty", &"feared"]
	for pass_i in 2:
		for id in ids:
			await _wait(20)
			var b0 := Time.get_ticks_usec()
			await get_tree().process_frame
			await get_tree().process_frame
			var base := (Time.get_ticks_usec() - b0) / 1000.0
			var t0 := Time.get_ticks_usec()
			hero.status.apply(id, 3.0, 0.3, 0.0)
			var t1 := Time.get_ticks_usec()
			await get_tree().process_frame
			await get_tree().process_frame
			var t2 := Time.get_ticks_usec()
			print("STATUS pass %d %-14s apply %.2f ms  next 2 frames %.1f ms (2 frames before %.1f)" % [pass_i, id, (t1 - t0) / 1000.0,
				(t2 - t1) / 1000.0, base])
			hero.status.remove(id)
			await _wait(10)

## What building and showing a hit's effects costs on the main thread (bh-037): 100 of each, built and added at the hero.
func _fx_bench() -> void:
	var at: Vector3 = (Game.player as Node3D).global_position + Vector3.UP
	var cases := {
		"particles": func(): return VFXLib.particles(Color(1, 0.8, 0.5), 12, 0.35, true, 0.3, 5.0, 70.0, Vector3(0, -9, 0)),
		"hit_burst": func(): return VFXLib.hit_burst(at, 0, 0.8, true),
		"gore_flesh": func(): return Gore.hit(at, Vector3.FORWARD, Gore.FLESH, Color(0.5, 0.05, 0.03), 0.8, true),
		"spark_spray": func(): return VFXLib.spark_spray(Vector3.FORWARD, Color.WHITE, 10, 6.0),
		"light_flash": func(): return VFXLib.light_flash(Color.WHITE, 2.0, 3.0, 0.15),
	}
	for k in cases:
		await _wait(30)
		var t0 := Time.get_ticks_usec()
		for i in 100:
			FX.spawn(cases[k].call(), at + Vector3(randf() * 2.0, 0, randf() * 2.0))
		var t1 := Time.get_ticks_usec()
		var f0 := Time.get_ticks_usec()
		await get_tree().process_frame
		await get_tree().process_frame
		print("FXBENCH %-12s build+add %.3f ms each; next two frames %.1f ms" % [k, (t1 - t0) / 100000.0, (Time.get_ticks_usec() - f0) / 1000.0])

## Animation cost by owner (bh-037): every active AnimationTree switched to manual and advanced by hand, timed per owner
## script (enemy, tempo, quake ally, player...), for 90 frames; also the skeleton/attachment work that follows each advance.
func _anim_costs() -> void:
	var trees: Array = []
	for t: AnimationTree in get_tree().root.find_children("*", "AnimationTree", true, false):
		if t.active and t.callback_mode_process != AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL:
			var owner_n: Node = t.get_parent()
			var label := "?"
			for i in 6:
				if owner_n == null:
					break
				if owner_n.get_script() and not (owner_n is CharacterVisual):
					label = owner_n.get_script().resource_path.get_file()
					break
				owner_n = owner_n.get_parent()
			trees.append([t, label])
			t.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var us := {}
	var n := {}
	for tr in trees:
		n[tr[1]] = int(n.get(tr[1], 0)) + 1
	for f in 90:
		await get_tree().process_frame
		for tr in trees:
			if not is_instance_valid(tr[0]):
				continue
			var t0 := Time.get_ticks_usec()
			(tr[0] as AnimationTree).advance(get_process_delta_time())
			us[tr[1]] = int(us.get(tr[1], 0)) + (Time.get_ticks_usec() - t0)
	for tr in trees:
		if is_instance_valid(tr[0]):
			(tr[0] as AnimationTree).callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE
	var total := 0.0
	for k in us:
		var ms := float(us[k]) / 1000.0 / 90.0
		total += ms
		print("ANIM %6.2f ms/frame  %-26s x%d (%.0f us each)" % [ms, k, n[k], ms * 1000.0 / maxf(1, n[k])])
	print("ANIM total %.2f ms/frame over %d active trees (strided crowd trees not counted)" % [total, trees.size()])
