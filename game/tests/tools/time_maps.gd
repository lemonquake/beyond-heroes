extends Node
## Measures build + navmesh bake time per map (headless is fine). Usage:
##   godot --headless --path game res://tests/tools/time_maps.tscn -- --maps=sanctuary,ruined_forest --out=<file.json>
## Prints one line per map and optionally writes a JSON report (milliseconds, navmesh polygons, node count).

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	if String(args.get("lite", "0")) == "1":     # efficiency mode builds (bh-009)
		Settings._efficiency_preset()
	var ids: Array = String(args.get("maps", "sanctuary,ruined_forest,catacombs,forgotten_temple,boss_arena")).split(",")
	var report := {}
	for id in ids:
		var t0 := Time.get_ticks_usec()
		var m := Game.build_map(StringName(id))
		var t1 := Time.get_ticks_usec()
		add_child(m)
		MapBuilder.isolate_navigation(m)
		MapBuilder.bake_navigation(m)
		var t2 := Time.get_ticks_usec()
		var r := {"build_ms": (t1 - t0) / 1000.0, "bake_ms": (t2 - t1) / 1000.0,
			"nav_polys": m.nav_region.navigation_mesh.get_polygon_count(), "nodes": m.find_children("*", "", true, false).size(),
			"bounds": str(m.bounds.size)}
		report[id] = r
		print("TIME %s build %.0f ms, bake %.0f ms, %d polys, %d nodes" % [id, r.build_ms, r.bake_ms, r.nav_polys, r.nodes])
		m.free()
	if args.has("out"):
		var f := FileAccess.open(String(args["out"]), FileAccess.WRITE)
		f.store_string(JSON.stringify(report, "  "))
	get_tree().quit()
