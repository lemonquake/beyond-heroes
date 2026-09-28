extends Node
## Walk lengths between candidate points on a surface map's navmesh.
##   godot --headless --path game res://tests/tools/probe_paths.tscn -- --map=westreach --pairs=x1,z1,x2,z2;...
func _ready() -> void:
	await get_tree().process_frame
	var args := {}
	for a in OS.get_cmdline_user_args():
		if "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var holder := Node3D.new()
	add_child(holder)
	var m: MapRoot = Game.build_map(StringName(args.get("map", "westreach")))
	holder.add_child(m)
	MapBuilder.isolate_navigation(m)
	MapBuilder.bake_navigation(m)
	for i in 4:
		await get_tree().physics_frame
	var nm := m.nav_region.get_navigation_map()
	for pr in String(args.pairs).split(";"):
		var v := pr.split(",")
		var a := Vector3(float(v[0]), 0, float(v[1]))
		var b := Vector3(float(v[2]), 0, float(v[3]))
		var fa := NavigationServer3D.map_get_closest_point(nm, a + Vector3.UP * 0.3)
		var fb := NavigationServer3D.map_get_closest_point(nm, b + Vector3.UP * 0.3)
		var path := NavigationServer3D.map_get_path(nm, fa, fb, true)
		var w := 0.0
		for k in path.size() - 1:
			w += Vector2(path[k].x, path[k].z).distance_to(Vector2(path[k + 1].x, path[k + 1].z))
		var pp := []
		for k in range(0, path.size(), maxi(1, path.size() / 12)):
			pp.append("(%.0f,%.0f)" % [path[k].x, path[k].z])
		print("  VIA ", " ".join(pp))
		print("PATH %s -> walked %.1f straight %.1f snapA %s snapB %s" % [pr, w, Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z)), fa, fb])
	get_tree().quit()
