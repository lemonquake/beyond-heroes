extends Node
## Evidence run for the Salmonan map milestone. Boots the real game (knight, save slot 97), checks the barred South Gate
## on the M map, opens the gate, searches and routes on the map, then walks the tracked route with real movement input
## (steering toward Routes.guide) through the gate into Westreach, along the Field Road to Lantern Fields, and along
## the Coast Road to Tideglass Cove; takes a deliberate wrong turn to check replanning; captures native screenshots and
## writes report.json.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_salmonan.tscn -- --class=knight --slot=97 --out=<dir>

var out := ""
var report := {"shots": [], "legs": []}
var main: Node
var _t0 := 0
var _frames_by_map := {}           # map id -> [frame delta ms] while walking
var _recording := false
var _short := false

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/salmonan-map/evidence/run")))
	_short = args.get("short", "0") == "1"
	DirAccess.make_dir_recursive_absolute(out)
	_t0 = Time.get_ticks_msec()
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	if not (Game.player is Player):
		print("SALMONAN ERROR no player")
		get_tree().quit(1)
		return
	Game.god_mode = true
	for i in 3:
		(Game.player as Player).camera.zoom(1)
	await _frames(60)
	if _short:
		await _run_short()
	else:
		await _run()
	report["frame_times_ms"] = _frame_stats()
	var f := FileAccess.open(out.path_join("report.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	print("SALMONAN DONE ", JSON.stringify(report.get("summary", {})))
	get_tree().quit()

## Only the map, for checking readability at another window size.
func _run_short() -> void:
	var want := "1280x720"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--win="):
			want = a.substr(6)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(int(want.get_slice("x", 0)), int(want.get_slice("x", 1))))
	await _frames(30)
	Game.set_world_flag(&"south_gate_open")
	await _frames(20)
	var map_w: WorldMapWindow = Game.ui_root.window(&"world_map")
	await _key(KEY_M)
	await _frames(20)
	map_w._set_view("island")
	map_w.select("wr_fields")
	map_w._directions()
	await _shot("map-island-%dx%d" % [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y])
	map_w._set_view("local")
	await _shot("map-local-%dx%d" % [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y])

func _process(delta: float) -> void:
	if _recording and not Game.travelling and Game.current_map_id != &"":
		(_frames_by_map.get_or_add(String(Game.current_map_id), []) as Array).append(delta * 1000.0)

func _frame_stats() -> Dictionary:
	var outd := {}
	for m in _frames_by_map:
		var a: Array = _frames_by_map[m].duplicate()
		a.sort()
		if a.size() < 10:
			continue
		var sum := 0.0
		for v in a:
			sum += v
		outd[m] = {"frames": a.size(), "avg_ms": snappedf(sum / a.size(), 0.01), "p95_ms": snappedf(a[int(a.size() * 0.95)], 0.01),
			"worst_ms": snappedf(a[a.size() - 1], 0.01)}
	return outd

func _run() -> void:
	var map_w: WorldMapWindow = Game.ui_root.window(&"world_map")
	await _shot("01-town-start")
	# 1) the map before the gate opens: Westreach is under mist and the route explains the lock
	await _key(KEY_M)
	await _frames(20)
	map_w.select("wr_fields")
	map_w._directions()
	await _frames(10)
	report["locked_plan"] = {"ok": map_w.atlas.preview.get("ok"), "reason": map_w.atlas.preview.get("reason")}
	await _shot("02-map-gate-barred")
	await _key(KEY_M)
	await _frames(10)
	report["map_closed_by_M"] = not map_w.visible
	report["unpaused_after_close"] = not get_tree().paused
	# 2) Captain Hald opens the gate (the same action his dialogue runs)
	var hald: NpcDef = DB.npcs.get(&"hald")
	report["hald_has_road_node"] = hald != null and hald.graph.nodes.has("road") and hald.graph.nodes.has("road_opened")
	Game.set_world_flag(&"south_gate_open")
	Game.place_player(&"gate")
	var pl := Game.player as Player
	pl.global_position = Vector3(0, pl.global_position.y, 34.0)
	await _frames(70)
	await _shot("03-south-gate-open")
	# 3) find Lantern Fields by name, preview directions, set the route
	await _key(KEY_M)
	await _frames(20)
	map_w._search.text = "lantern"
	map_w._on_search("lantern")
	await _frames(6)
	await _shot("04-map-search")
	map_w._pick_result("wr_fields")
	map_w._directions()
	await _frames(8)
	await _shot("05-map-directions-fields")
	report["fields_plan"] = _plan_summary(map_w.atlas.preview)
	map_w._set_route()
	await _frames(4)
	await _key(KEY_M)
	await _frames(20)
	await _shot("06-hud-route-in-town")
	# 4) walk it: through the South Gate (a real map boundary) and along the Field Road
	var leg := await _walk_route(70.0, ["07-westreach-gate-fork", "08-field-road"], [2.0, 14.0])
	report.legs.append(leg)
	await _frames(30)
	await _shot("09-arrived-fields")
	# 5) Tideglass Cove by the Coast Road, walking
	Routes.set_route("wr_cove", RoutePlanner.Mode.ROADS)
	report["cove_plan"] = _plan_summary(Routes.plan)
	await _frames(10)
	leg = await _walk_route(80.0, ["10-coast-road", "11-coast-road-late"], [12.0, 30.0])
	report.legs.append(leg)
	await _frames(20)
	await _shot("12-tideglass-cove")
	# 6) the map in Westreach: local view and the underground view
	await _key(KEY_M)
	await _frames(20)
	map_w.select("wr_mill")
	map_w._set_view("local")
	map_w._directions()
	await _frames(10)
	await _shot("13-map-local-westreach")
	map_w._set_view("underground")
	map_w.select("temple")
	map_w._directions()
	await _frames(10)
	report["temple_plan"] = {"ok": map_w.atlas.preview.get("ok"), "reason": map_w.atlas.preview.get("reason")}
	await _shot("14-map-underground")
	map_w._set_view("island")
	map_w._set_mode(RoutePlanner.Mode.WAYPOINTS)
	map_w.select("rf_village")
	map_w._directions()
	await _frames(10)
	report["village_waypoints_plan"] = _plan_summary(map_w.atlas.preview)
	await _shot("15-map-waypoints-to-village")
	await _key(KEY_M)
	await _frames(10)
	# 7) a wrong turn: at Lantern Fields, route to the Old Mill (Mill Lane, north), then walk west along the Coast Road
	# instead; after straying more than 10 m for a second the route must replan once, not flicker
	var p := Game.player as Player
	p.global_position = Vector3(33.0, -1.5, 111.0)       # just above the fields; the hero drops onto the road
	await _frames(30)
	Routes.set_route("wr_mill", RoutePlanner.Mode.ROADS)
	await _frames(10)
	var r0 := Routes.replans
	var first := String(Routes.plan.steps[0].text) if Routes.plan.get("ok", false) else ""
	var wrong: Array = DataIsland.road("wr_coast_road").points.duplicate()
	wrong.reverse()
	var instr_seen := {}
	for i in 360:
		var pr := DataIsland.project(Routes.hero_local(), wrong)
		var tgt := DataIsland.point_at(wrong, pr.along + 6.0)
		_steer(Vector3(tgt.x, p.global_position.y, tgt.y))
		instr_seen[Routes.instruction] = true
		await get_tree().physics_frame
	_release()
	await _frames(20)
	report["wrong_turn_instructions_seen"] = instr_seen.keys()
	report["wrong_turn"] = {"replans_during": Routes.replans - r0, "first_step_before": first,
		"first_step_after": String(Routes.plan.steps[0].text) if Routes.plan.get("ok", false) else Routes.plan.get("reason", ""),
		"remaining_m": Routes.remaining_m}
	await _shot("16-after-wrong-turn")
	Routes.clear_route()
	report["summary"] = {"shots": report.shots.size(), "fields_walk_m": report.fields_plan.get("walk_m"), "cove_walk_m": report.cove_plan.get("walk_m"),
		"legs": report.legs, "elapsed_s": (Time.get_ticks_msec() - _t0) / 1000.0}

## Steer toward the route's guide point until the route is cleared (arrival) or `limit` seconds pass. Screenshots
## are taken at the given elapsed times. Map changes (the South Gate) happen by walking into the boundary.
func _walk_route(limit: float, shots: Array, at: Array) -> Dictionary:
	var p := Game.player as Player
	var t := 0.0
	var next := 0
	var start_map := Game.current_map_id
	var dist := 0.0
	var last := p.global_position
	var maps := [String(start_map)]
	var dest := Routes.dest
	_recording = true
	var travel_ms := []
	var travel_t0 := -1
	while t < limit and Routes.active():
		if Game.travelling:
			if travel_t0 < 0:
				travel_t0 = Time.get_ticks_msec()
			_release()
			await get_tree().process_frame
			last = p.global_position
			continue
		if travel_t0 >= 0:
			travel_ms.append(Time.get_ticks_msec() - travel_t0)
			travel_t0 = -1
		if String(Game.current_map_id) != maps[maps.size() - 1]:
			maps.append(String(Game.current_map_id))
			last = p.global_position
		if Routes.has_guide:
			_steer(Routes.guide)
		else:
			_release()
		await get_tree().physics_frame
		var d := p.global_position.distance_to(last)
		if d < 3.0:
			dist += d
		last = p.global_position
		t += 1.0 / Engine.physics_ticks_per_second
		if next < shots.size() and t >= at[next]:
			_release()
			await _shot(shots[next])
			next += 1
	_release()
	_recording = false
	return {"dest": dest, "arrived": not Routes.active(), "travel_ms": travel_ms, "seconds": snappedf(t, 0.1), "walked_m": snappedf(dist, 0.1), "maps": maps,
		"end": str(p.global_position.snapped(Vector3.ONE * 0.1)), "replans": Routes.replans}

func _steer(target: Vector3) -> void:
	var p := Game.player as Player
	var d := target - p.global_position
	d.y = 0.0
	if d.length() < 0.3:
		_release()
		return
	var v := p.camera.ground_basis().inverse() * d.normalized()
	Input.action_press(&"move_right", maxf(v.x, 0.0))
	Input.action_press(&"move_left", maxf(-v.x, 0.0))
	Input.action_press(&"move_down", maxf(v.z, 0.0))
	Input.action_press(&"move_up", maxf(-v.z, 0.0))

func _release() -> void:
	for a in [&"move_right", &"move_left", &"move_down", &"move_up"]:
		Input.action_release(a)

func _plan_summary(p: Dictionary) -> Dictionary:
	if p.is_empty():
		return {}
	return {"ok": p.get("ok"), "reason": p.get("reason"), "walk_m": snappedf(float(p.get("walk_m", 0.0)), 0.1),
		"est_s": snappedf(float(p.get("est_s", 0.0)), 0.1), "steps": (p.get("steps", []) as Array).map(func(s): return s.text)}

func _key(k: Key) -> void:
	for pressed in [true, false]:
		var ev := InputEventKey.new()
		ev.keycode = k
		ev.physical_keycode = k
		ev.pressed = pressed
		Input.parse_input_event(ev)
		await _frames(3)

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _shot(label: String) -> void:
	await _frames(12)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	report.shots.append(label)
	print("SALMONAN SHOT ", label, " map=", Game.current_map_id, " route=", Routes.dest, " instr=", Routes.instruction)
