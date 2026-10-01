extends Node
## bh-029 Builder W2 evidence: the Bridge of Death and the Heart Citadel.
## Capture (real renderer): every named view of each map as a 1920x1080 PNG, plus <map>_stats.json (build ms, lights,
## shadowed lights, triangles drawn per view, navmesh polygons).
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh029_w2.tscn -- --out=<dir> [--maps=a,b] [--views=a,b]
## Walk check (headless): bakes each map's navmesh and asks NavigationServer3D for a path from the entry spawn to every
## DataIsland place of the map; on the bridge it also samples the deck every metre along three lines (x = -4, 0, 4) to
## prove the walkable surface is one continuous strip from the south rim to the north rim.
##   godot --headless --path game res://tests/tools/capture_bh029_w2.tscn -- --walk=1 --out=<dir>

const ENTRY := {&"bridge_of_death": &"barrens_road", &"zr_citadel": &"bridge_road"}

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-029/evidence/maps_w2")))
	DirAccess.make_dir_recursive_absolute(out)
	var ids: Array = String(args.get("maps", "bridge_of_death,zr_citadel")).split(",")
	if Game.hero == null:
		var h := HeroData.new()
		h.setup(DB.class_def(&"knight"), "Capture")
		h.init_new()
		Game.hero = h
	# one Vault cleared, so the captures show both ward states (the Jade pair gold, the others violet)
	Game.hero.world_flags[&"dg_jade_sepulchre_cleared"] = true
	if String(args.get("walk", "0")) == "1":
		var report := {}
		for id in ids:
			report[id] = await _walk(StringName(id))
		var f := FileAccess.open(out.path_join("walk_check.json"), FileAccess.WRITE)
		f.store_string(JSON.stringify(report, "  "))
		print("W2 WALK DONE -> ", out)
		get_tree().quit()
		return
	await _capture(ids)
	get_tree().quit()

# ------------------------------------------------------------------------------------------------------------
# captures

func _capture(ids: Array) -> void:
	var only: Array = String(args.get("views", "")).split(",", false)
	var frames := int(args.get("frames", "30"))
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	for id in ids:
		var t0 := Time.get_ticks_msec()
		var map := Game.load_map(StringName(id))
		var build_ms := Time.get_ticks_msec() - t0
		var cam := Camera3D.new()
		map.add_child(cam)
		cam.far = 900.0
		cam.make_current()
		var stats := _stats(map)
		stats["build_and_bake_ms"] = build_ms
		var drawn := {}
		for vname in map.views:
			if not only.is_empty() and not only.has(vname):
				continue
			var v: Dictionary = map.views[vname]
			var off := Vector3(0, 0, float(v.dist)).rotated(Vector3.RIGHT, -deg_to_rad(float(v.pitch))).rotated(Vector3.UP, deg_to_rad(float(v.yaw)))
			cam.fov = float(v.fov)
			cam.global_position = v.target + off
			cam.look_at(v.target, Vector3.UP if float(v.pitch) < 89.0 else Vector3.FORWARD)
			for i in frames:
				await get_tree().process_frame
			await RenderingServer.frame_post_draw
			drawn[vname] = {"primitives": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
				"draw_calls": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)}
			var img := get_viewport().get_texture().get_image()
			var path := out.path_join("%s__%s.png" % [id, vname])
			img.save_png(path)
			print("W2 CAPTURED ", path, " ", drawn[vname])
		stats["views"] = drawn
		var fa := FileAccess.open(out.path_join("%s_stats.json" % id), FileAccess.WRITE)
		fa.store_string(JSON.stringify(stats, "  "))
		print("W2 STATS ", id, " ", JSON.stringify(stats))
	if Game.current_map:
		Game.current_map.queue_free()
		Game.current_map = null
	await get_tree().process_frame
	await get_tree().process_frame

func _stats(map: MapRoot) -> Dictionary:
	var omni := 0
	var shadowed := 0
	var meshes := 0
	var where := {}
	for n in map.find_children("*", "", true, false):
		if n is MeshInstance3D or n is MultiMeshInstance3D:
			meshes += 1
		elif n is OmniLight3D:
			omni += 1
			var holder := String(n.get_parent().name)
			if n.get_parent() == map.get_node_or_null("Lights"):
				holder = "Lights"
			where[holder] = int(where.get(holder, 0)) + 1
			if (n as OmniLight3D).shadow_enabled:
				shadowed += 1
	var nm := map.nav_region.navigation_mesh
	return {"nodes": map.find_children("*", "", true, false).size(), "mesh_instances": meshes, "omni_lights": omni,
		"shadowed_omni": shadowed, "omni_by_parent": where, "nav_polygons": nm.get_polygon_count() if nm else 0,
		"spawns": map.spawns.keys().map(func(k): return String(k))}

# ------------------------------------------------------------------------------------------------------------
# walk check

func _walk(id: StringName) -> Dictionary:
	var t0 := Time.get_ticks_usec()
	var map := Game.build_map(id)
	var t1 := Time.get_ticks_usec()
	add_child(map)
	var rid := MapBuilder.isolate_navigation(map)
	MapBuilder.bake_navigation(map)
	var t2 := Time.get_ticks_usec()
	await get_tree().physics_frame
	var res := {"build_ms": (t1 - t0) / 1000.0, "bake_ms": (t2 - t1) / 1000.0,
		"nav_polygons": map.nav_region.navigation_mesh.get_polygon_count(), "places": {}, "problems": []}
	var entry: Vector3 = map.spawns[ENTRY[id]].global_position
	var from := NavigationServer3D.map_get_closest_point(rid, entry)
	res["entry"] = [ENTRY[id], _v(entry), _v(from)]
	for p in DataIsland.all_places():
		if StringName(p.get("map", "")) != id:
			continue
		var pos: Vector2 = p.pos
		var to := _closest(rid, pos)
		var path := NavigationServer3D.map_get_path(rid, from, to, true)
		var ok := path.size() > 0 and path[path.size() - 1].distance_to(to) < 1.0 and Vector2(to.x, to.z).distance_to(pos) < 3.0
		var length := 0.0
		for i in range(1, path.size()):
			length += path[i].distance_to(path[i - 1])
		res.places[p.id] = {"reachable": ok, "target": _v(Vector3(pos.x, 0, pos.y)), "nav_point": _v(to), "path_len": snappedf(length, 0.1)}
		print("W2 WALK %s %s reachable=%s path=%.1f m (nav point %s)" % [id, p.id, ok, length, _v(to)])
		if not ok:
			res.problems.append("unreachable %s" % p.id)
	for sid in map.spawns:
		var sp: Vector3 = map.spawns[sid].global_position
		var q := NavigationServer3D.map_get_closest_point(rid, sp)
		if Vector2(q.x, q.z).distance_to(Vector2(sp.x, sp.z)) > 1.0 or absf(q.y - sp.y) > 0.6:
			res.problems.append("spawn %s off the navmesh (%s -> %s)" % [sid, _v(sp), _v(q)])
	if id == &"bridge_of_death":
		res["deck"] = _deck_check(rid, map)
		res.problems.append_array(res.deck.problems)
	if id == &"zr_citadel":
		var e := DataZarael.HC_ENGINE
		var ar := DataZarael.HC_ARENA_R
		var blocked := 0
		for k in 48:
			var a := TAU * k / 48.0
			for r: float in [ar * 0.5, ar * 0.9]:
				var c := Vector2(0, -28) + Vector2(cos(a), sin(a)) * r
				if Vector2(c.x - e.x, c.y - e.z).length() < 10.5:
					continue
				var q := _closest(rid, c)
				if Vector2(q.x, q.z).distance_to(c) > 0.6:
					blocked += 1
		res["arena_samples_off_navmesh"] = blocked
	print("W2 WALK %s problems: %s" % [id, res.problems])
	map.queue_free()
	await get_tree().process_frame
	return res

## The bridge's walkable strip: every metre along x = -4, 0, 4 from the south edge to the north edge must have the navmesh
## right under it at deck/ledge height, and one path must run the whole way without detours.
func _deck_check(rid: RID, map: MapRoot) -> Dictionary:
	var gaps := []
	var z := 158.0
	while z >= -169.0:
		for x: float in [-4.0, 0.0, 4.0]:
			var q := NavigationServer3D.map_get_closest_point(rid, Vector3(x, 0.0, z))
			# Recast lays the polygons up to ~2 cells (0.5 m) over the colliders; anything more means a step or a hole
			if Vector2(q.x, q.z).distance_to(Vector2(x, z)) > 0.35 or absf(q.y) > 0.8:
				gaps.append("x=%.0f z=%.0f -> %s" % [x, z, _v(q)])
		z -= 1.0
	var a := NavigationServer3D.map_get_closest_point(rid, map.spawns[&"barrens_road"].global_position)
	var b := NavigationServer3D.map_get_closest_point(rid, map.spawns[&"citadel_road"].global_position)
	var path := NavigationServer3D.map_get_path(rid, a, b, true)
	var length := 0.0
	for i in range(1, path.size()):
		length += path[i].distance_to(path[i - 1])
	var straight := a.distance_to(b)
	var problems := []
	if not gaps.is_empty():
		problems.append("%d deck samples off the navmesh (first: %s)" % [gaps.size(), gaps[0]])
	if path.is_empty() or path[path.size() - 1].distance_to(b) > 1.0 or length > straight * 1.05:
		problems.append("south-north path broken or detours: %.1f m for %.1f m straight" % [length, straight])
	print("W2 DECK samples=%d gaps=%d south->north path %.1f m (straight %.1f m)" % [3 * 328, gaps.size(), length, straight])
	return {"samples": 3 * 328, "gaps": gaps.slice(0, 20), "gap_count": gaps.size(), "south_north_path_m": snappedf(length, 0.1),
		"straight_m": snappedf(straight, 0.1), "problems": problems}

## The navmesh point nearest a place, trying each walking height the maps use (ledges, deck, the Citadel's tiers).
func _closest(rid: RID, p: Vector2) -> Vector3:
	var best := Vector3.ZERO
	var bd := INF
	for y: float in [0.0, 4.0, 8.0, 12.0]:
		var q := NavigationServer3D.map_get_closest_point(rid, Vector3(p.x, y, p.y))
		var d := Vector2(q.x, q.z).distance_to(p) + absf(q.y - y) * 0.1
		if d < bd:
			bd = d
			best = q
	return best

func _v(p: Vector3) -> String:
	return "(%.1f, %.1f, %.1f)" % [p.x, p.y, p.z]
