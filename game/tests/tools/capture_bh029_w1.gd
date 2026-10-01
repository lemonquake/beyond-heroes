extends Node
## bh-029 Builder W1 evidence: The Coilwood and The Glasswire Barrens. Loads each map (no hero is booted; no save slot is
## touched), renders every named view plus game-camera shots at the landmarks (PlayerCamera pitch/fov), writes
## <map>_stats.json, and runs the walk check: navmesh paths from the entry spawn to every DataIsland place on the map,
## every spawn, and every road sampled along its polyline.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh029_w1.tscn -- --maps=zr_coilwood,zr_barrens --out=<dir>
##   godot --headless --path game res://tests/tools/capture_bh029_w1.tscn -- --walk_only=1 --out=<dir>

const ENTRY := {&"zr_coilwood": &"agdao_road", &"zr_barrens": &"coil_road"}
## Game-camera shots: [label, target x, z] (PlayerCamera: pitch 54, fov 40, zoomed out to 24 m).
const GAME_SHOTS := {
	&"zr_coilwood": [["g_west_entry", -128.0, 28.0], ["g_shrine", -108.0, 15.0], ["g_aqueduct_road", -84.0, 15.0],
		["g_fork", -60.0, 8.0], ["g_relay_west", -58.0, -38.0], ["g_lines", 10.0, 2.0], ["g_relay_south", 18.0, 56.0],
		["g_camp", 28.0, -54.0], ["g_relay_east", 64.0, -24.0], ["g_jade", 94.0, -52.0], ["g_east_exit", 130.0, 8.0]],
	&"zr_barrens": [["g_west_entry", -120.0, 12.0], ["g_camp", -40.0, 34.0], ["g_camp_gate", -58.0, 27.0],
		["g_crossroads", 0.0, 12.0], ["g_colossus", 46.0, -30.0], ["g_obsidian", -68.0, -58.0], ["g_vein", 80.0, 42.0],
		["g_bridge_road", 26.0, -70.0], ["g_north_exit", 30.0, -90.0]],
}

var out := ""
var lines: PackedStringArray = []

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var ids: Array = String(args.get("maps", "zr_coilwood,zr_barrens")).split(",")
	var only_views: Array = String(args.get("views", "")).split(",", false)
	var walk_only := String(args.get("walk_only", "0")) == "1"
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-029/evidence/maps_w1")))
	DirAccess.make_dir_recursive_absolute(out)
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	if Game.hero == null:
		var h := HeroData.new()
		h.setup(DB.class_def(&"knight"), "Capture")
		h.init_new()
		Game.hero = h
	for id in ids:
		var t0 := Time.get_ticks_msec()
		var map := Game.load_map(StringName(id))
		var ms := Time.get_ticks_msec() - t0
		print("W1 LOADED %s in %d ms (build + bake)" % [id, ms])
		for i in 4:
			await get_tree().physics_frame
		_walk_check(map, StringName(id))
		var stats := _stats(map)
		stats["load_ms"] = ms
		var fa := FileAccess.open(out.path_join("%s_stats.json" % id), FileAccess.WRITE)
		fa.store_string(JSON.stringify(stats, "  "))
		print("W1 STATS ", id, " ", JSON.stringify(stats))
		if walk_only:
			continue
		var cam := Camera3D.new()
		map.add_child(cam)
		cam.far = 600.0
		cam.make_current()
		for vname in map.views:
			if not only_views.is_empty() and not only_views.has(vname):
				continue
			var v: Dictionary = map.views[vname]
			var off := Vector3(0, 0, float(v.dist)).rotated(Vector3.RIGHT, -deg_to_rad(float(v.pitch))).rotated(Vector3.UP, deg_to_rad(float(v.yaw)))
			cam.fov = float(v.fov)
			cam.global_position = v.target + off
			cam.look_at(v.target, Vector3.UP if float(v.pitch) < 89.0 else Vector3.FORWARD)
			await _shot("%s__%s" % [id, vname])
		for g in GAME_SHOTS.get(StringName(id), []):
			if not only_views.is_empty() and not only_views.has(g[0]):
				continue
			var gy := _ground_y(map, Vector2(g[1], g[2]))
			var target := Vector3(g[1], gy + 1.1, g[2])
			cam.fov = 40.0
			cam.global_position = target + Vector3(0, 0, 24.0).rotated(Vector3.RIGHT, -deg_to_rad(54.0))
			cam.look_at(target, Vector3.UP)
			await _shot("%s__%s" % [id, g[0]])
	var f := FileAccess.open(out.path_join("walk_check.txt"), FileAccess.WRITE)
	f.store_string("\n".join(lines) + "\n")
	if Game.current_map:
		Game.current_map.queue_free()
		Game.current_map = null
	await get_tree().process_frame
	get_tree().quit()

func _shot(label: String) -> void:
	for i in 24:
		await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	print("W1 CAPTURED ", label)

func _log(s: String) -> void:
	lines.append(s)
	print("W1 WALK ", s)

## Height of the walkable surface of this map at a point (the highest collider with navmesh close to it).
func _ground_y(m: MapRoot, p: Vector2) -> float:
	var space := m.get_world_3d().direct_space_state
	var nm := m.nav_region.get_navigation_map()
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 80, p.y), Vector3(p.x, -60, p.y), BH.LAYER_GROUND | BH.LAYER_WORLD)
	var exclude: Array[RID] = []
	var best_y := 0.0
	var best := INF
	for i in 16:
		q.exclude = exclude
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			break
		exclude.append(hit.rid)
		if (hit.normal as Vector3).y < 0.6:
			continue
		var c := NavigationServer3D.map_get_closest_point(nm, hit.position)
		var d := c.distance_to(hit.position)
		if d < 0.6:
			return hit.position.y
		if d < best:
			best = d
			best_y = hit.position.y
	return best_y

func _path(nm: RID, a: Vector3, b: Vector3) -> Dictionary:
	var path := NavigationServer3D.map_get_path(nm, a, b, true)
	var walked := 0.0
	for i in path.size() - 1:
		walked += path[i].distance_to(path[i + 1])
	var end_d := path[path.size() - 1].distance_to(b) if not path.is_empty() else INF
	return {"ok": end_d < 0.8, "end": end_d, "len": walked}

func _walk_check(m: MapRoot, id: StringName) -> void:
	var nm := m.nav_region.get_navigation_map()
	_log("== %s: navmesh %d polygons" % [id, m.nav_region.navigation_mesh.get_polygon_count()])
	var sp := m.spawn_transform(ENTRY[id]).origin
	var from := NavigationServer3D.map_get_closest_point(nm, sp)
	_log("entry %s at %s -> navmesh %.2f m away" % [ENTRY[id], sp, from.distance_to(sp)])
	var bad := 0
	for p in DataIsland.PLACES:
		if StringName(p.map) != id:
			continue
		var pos: Vector2 = p.pos
		var want := Vector3(pos.x, _ground_y(m, pos), pos.y)
		var to := NavigationServer3D.map_get_closest_point(nm, want)
		var snap := Vector2(to.x, to.z).distance_to(pos)
		var r := _path(nm, from, to)
		var good: bool = r.ok and snap < 3.5
		if not good:
			bad += 1
		_log("%s place %-12s %s: navmesh %.2f m from the spot, path %s (%.0f m, end %.2f)" % ["OK " if good else "BAD", p.id, pos, snap,
			"reaches" if r.ok else "DOES NOT REACH", r.len, r.end])
	for s in m.spawns:
		var so: Vector3 = m.spawn_transform(s).origin
		var to := NavigationServer3D.map_get_closest_point(nm, so)
		var r := _path(nm, from, to)
		var good: bool = r.ok and to.distance_to(so) < 2.0
		if not good:
			bad += 1
		_log("%s spawn %-16s navmesh %.2f m, path %s (%.0f m)" % ["OK " if good else "BAD", s, to.distance_to(so), "reaches" if r.ok else "DOES NOT REACH", r.len])
	for t in m.teleporters():
		var to := NavigationServer3D.map_get_closest_point(nm, t.global_position + Vector3(0, 0.47, 0))
		var r := _path(nm, from, to)
		var off := to.distance_to(t.global_position + Vector3(0, 0.47, 0))
		var good: bool = r.ok and off < 2.0
		if not good:
			bad += 1
		_log("%s dais %-22s navmesh %.2f m, path %s" % ["OK " if good else "BAD", t.teleporter_id, off, "reaches" if r.ok else "DOES NOT REACH"])
	for r in DataIsland.roads_on(id):
		var pts: Array = r.points
		var total := DataIsland.polyline_length(pts)
		var worst := 0.0
		var worst_at := Vector2.ZERO
		var along := 0.0
		while along <= total:
			var p := DataIsland.point_at(pts, along)
			var q := NavigationServer3D.map_get_closest_point(nm, Vector3(p.x, _ground_y(m, p), p.y))
			var d := Vector2(q.x, q.z).distance_to(p)
			if d > worst:
				worst = d
				worst_at = p
			along += 5.0
		var a: Vector2 = pts[0]
		var b: Vector2 = pts[pts.size() - 1]
		var pa := NavigationServer3D.map_get_closest_point(nm, Vector3(a.x, _ground_y(m, a), a.y))
		var pb := NavigationServer3D.map_get_closest_point(nm, Vector3(b.x, _ground_y(m, b), b.y))
		var res := _path(nm, pa, pb)
		var good: bool = worst < 2.2 and res.ok and res.len < total * 1.35 + 6.0
		if not good:
			bad += 1
		_log("%s road %-18s worst %.2f m off at %s, ends joined: %s, walked %.0f of %.0f m" % ["OK " if good else "BAD", r.id, worst, worst_at,
			res.ok, res.len, total])
	for e in m.find_children("Exit_*", "MapExit", true, false):
		var ep := (e as Node3D).global_position
		var to := NavigationServer3D.map_get_closest_point(nm, ep)
		var res := _path(nm, from, to)
		var good: bool = res.ok and Vector2(to.x, to.z).distance_to(Vector2(ep.x, ep.z)) < 2.5
		if not good:
			bad += 1
		_log("%s exit %s -> %s/%s, path %s" % ["OK " if good else "BAD", (e as MapExit).exit_id, (e as MapExit).destination_map,
			(e as MapExit).destination_spawn, "reaches" if res.ok else "DOES NOT REACH"])
	_log("== %s: %d problem(s)" % [id, bad])

func _stats(map: MapRoot) -> Dictionary:
	var meshes := 0
	var omni := 0
	var shadowed := 0
	var tris := 0
	var by := {}
	for n in map.find_children("*", "", true, false):
		if n is MeshInstance3D and n.mesh:
			meshes += 1
			tris += _tris(n.mesh)
		elif n is MultiMeshInstance3D and n.multimesh and n.multimesh.mesh:
			meshes += 1
			var t: int = _tris(n.multimesh.mesh) * n.multimesh.instance_count
			tris += t
			var bn := String(n.name).trim_prefix("Batch_").rsplit("_", true, 2)[0]
			by[bn] = int(by.get(bn, 0)) + t
		elif n is OmniLight3D:
			omni += 1
			if n.shadow_enabled or n.get_meta(&"wants_shadow", false):
				shadowed += 1
	return {"nodes": map.find_children("*", "", true, false).size(), "mesh_instances": meshes, "triangles_total": tris,
		"omni_lights": omni, "shadow_lights_requested": shadowed, "nav_polygons": map.nav_region.navigation_mesh.get_polygon_count(),
		"teleporters": map.teleporters().size(), "spawns": map.spawns.keys().map(func(k): return String(k)),
		"enemy_zones": map.find_children("EnemyZone_*", "Marker3D", true, false).size(), "decor_triangles": by}

static var _tri_cache := {}
func _tris(mesh: Mesh) -> int:
	if _tri_cache.has(mesh):
		return _tri_cache[mesh]
	var t := 0
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		t += idx.size() / 3 if idx.size() > 0 else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
	_tri_cache[mesh] = t
	return t
