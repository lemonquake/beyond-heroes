extends Node
## bh-029 probe: Agdao's navmesh between the terraces (paths and the surfaces under given points).
##   godot --headless --path game res://tests/tools/probe_bh029_nav.tscn

func _ready() -> void:
	var root := get_tree().root
	await get_tree().process_frame
	var holder := Node3D.new()
	root.add_child(holder)
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "Probe")
	h.init_new()
	Game.hero = h
	var m: MapRoot = Game.build_map(&"agdao")
	holder.add_child(m)
	MapBuilder.isolate_navigation(m)
	m.apply_flag_visuals()
	MapBuilder.bake_navigation(m)
	var nm := m.nav_region.get_navigation_map()
	for pt in [Vector2(0, -8), Vector2(0, -13), Vector2(0, -16), Vector2(0, -20), Vector2(0, -26), Vector2(0, -30), Vector2(0, -42),
			Vector2(0, -44), Vector2(0, -46), Vector2(0, -50), Vector2(0, -56), Vector2(0, -62), Vector2(0, -66), Vector2(0, -70), Vector2(72, -26), Vector2(-46, 41)]:
		var hits := []
		var space := m.get_world_3d().direct_space_state
		var q := PhysicsRayQueryParameters3D.create(Vector3(pt.x, 60, pt.y), Vector3(pt.x, -60, pt.y), BH.LAYER_GROUND | BH.LAYER_WORLD)
		var ex: Array[RID] = []
		for i in 8:
			q.exclude = ex
			var hit := space.intersect_ray(q)
			if hit.is_empty():
				break
			hits.append("%.1f:%s" % [hit.position.y, (hit.collider as Node).name])
			ex.append(hit.rid)
		var c := NavigationServer3D.map_get_closest_point(nm, Vector3(pt.x, 30, pt.y))
		print("PT %s hits=%s nav_from_above=%s" % [pt, hits, c])
	for pair in [[Vector3(0, 9.6, -8), Vector3(0, 13.6, -30)], [Vector3(0, 13.6, -30), Vector3(0, 17.6, -46)], [Vector3(0, 18.8, -44), Vector3(0, 33.8, -68)]]:
		var a := NavigationServer3D.map_get_closest_point(nm, pair[0])
		var b := NavigationServer3D.map_get_closest_point(nm, pair[1])
		var path := NavigationServer3D.map_get_path(nm, a, b, true)
		var s := ""
		for p in path:
			s += "(%.0f,%.1f,%.0f) " % [p.x, p.y, p.z]
		print("PATH %s -> %s : %s" % [a, b, s])
	get_tree().quit()
