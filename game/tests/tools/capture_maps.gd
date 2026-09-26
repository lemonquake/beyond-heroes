extends Node
## Renders every named view of each map with the real renderer and saves PNGs (map review evidence).
##   godot --path game --resolution 1600x900 res://tests/tools/capture_maps.tscn -- --maps=catacombs,sanctuary --out=<dir>
## Also writes <out>/<map>_stats.json with build time, node/light counts and navmesh size.

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var ids: Array = String(args.get("maps", "sanctuary,ruined_forest,catacombs,forgotten_temple,boss_arena")).split(",")
	var only_views: Array = String(args.get("views", "")).split(",", false)
	var out := String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-001/evidence/maps")))
	var frames := int(args.get("frames", "24"))
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
		var build_ms := Time.get_ticks_msec() - t0
		var cam := Camera3D.new()
		map.add_child(cam)
		cam.far = 500.0
		cam.make_current()
		var stats := _stats(map)
		stats["build_ms"] = build_ms
		for vname in map.views:
			if not only_views.is_empty() and not only_views.has(vname):
				continue
			var v: Dictionary = map.views[vname]
			var off := Vector3(0, 0, float(v.dist)).rotated(Vector3.RIGHT, -deg_to_rad(float(v.pitch))).rotated(Vector3.UP, deg_to_rad(float(v.yaw)))
			cam.fov = float(v.fov)
			cam.global_position = v.target + off
			cam.look_at(v.target, Vector3.UP if float(v.pitch) < 89.0 else Vector3.FORWARD)
			for i in frames:
				await get_tree().process_frame
			var img := get_viewport().get_texture().get_image()
			var path := out.path_join("%s__%s.png" % [id, vname])
			img.save_png(path)
			print("CAPTURED ", path)
		var fa := FileAccess.open(out.path_join("%s_stats.json" % id), FileAccess.WRITE)
		fa.store_string(JSON.stringify(stats, "  "))
		print("STATS ", id, " ", JSON.stringify(stats))
	if Game.current_map:
		Game.current_map.queue_free()
		Game.current_map = null
	await get_tree().process_frame
	await get_tree().process_frame
	get_tree().quit()

func _stats(map: MapRoot) -> Dictionary:
	var meshes := 0
	var tris := 0
	var omni := 0
	var shadowed := 0
	for n in map.find_children("*", "", true, false):
		if n is MeshInstance3D and n.mesh:
			meshes += 1
		elif n is MultiMeshInstance3D:
			meshes += 1
		elif n is OmniLight3D:
			omni += 1
			if n.shadow_enabled:
				shadowed += 1
	var nm := map.nav_region.navigation_mesh
	return {"nodes": map.find_children("*", "", true, false).size(), "mesh_instances": meshes, "omni_lights": omni,
		"shadowed_omni": shadowed, "nav_polygons": nm.get_polygon_count() if nm else 0,
		"teleporters": map.teleporters().size(), "spawns": map.spawns.keys().map(func(k): return String(k))}
