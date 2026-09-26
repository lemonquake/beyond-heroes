extends Node
## Rasterises each map's baked navmesh to a top-down PNG (walkable area coloured by height; spawns white,
## teleporters cyan, enemy zones red) so walkability can be reviewed at a glance.
##   godot --headless --path game res://tests/tools/nav_maps.tscn -- --maps=catacombs --out=<dir> [--ppm=4]

func _ready() -> void:
	await get_tree().process_frame
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var ids: Array = String(args.get("maps", "sanctuary,ruined_forest,catacombs,forgotten_temple,boss_arena")).split(",")
	var out := String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-001/evidence/maps")))
	var ppm := float(args.get("ppm", "4"))
	DirAccess.make_dir_recursive_absolute(out)
	for id in ids:
		var m := Game.build_map(StringName(id))
		add_child(m)
		MapBuilder.bake_navigation(m)
		var nm := m.nav_region.navigation_mesh
		var verts := nm.get_vertices()
		var b := m.bounds.grow(4.0)
		var w := int(b.size.x * ppm)
		var h := int(b.size.z * ppm)
		var img := Image.create(w, h, false, Image.FORMAT_RGB8)
		img.fill(Color(0.06, 0.06, 0.08))
		for pi in nm.get_polygon_count():
			var poly := nm.get_polygon(pi)
			for k in range(1, poly.size() - 1):
				_tri(img, b, ppm, verts[poly[0]], verts[poly[k]], verts[poly[k + 1]])
		for sid in m.spawns:
			_dot(img, b, ppm, m.spawns[sid].global_position, Color.WHITE, 3)
		for t in m.teleporters():
			_dot(img, b, ppm, t.global_position, Color(0.3, 0.9, 1.0), 5)
		for z in m.find_children("EnemyZone_*", "Marker3D", true, false):
			_dot(img, b, ppm, z.global_position, Color(1.0, 0.25, 0.2), 2)
		img.save_png(out.path_join("%s__navmesh.png" % id))
		print("NAV ", id, " polys=", nm.get_polygon_count(), " -> ", out.path_join("%s__navmesh.png" % id))
		m.free()
	get_tree().quit()

func _px(b: AABB, ppm: float, p: Vector3) -> Vector2:
	return Vector2((p.x - b.position.x) * ppm, (p.z - b.position.z) * ppm)

func _tri(img: Image, b: AABB, ppm: float, a: Vector3, c: Vector3, d: Vector3) -> void:
	var pa := _px(b, ppm, a)
	var pc := _px(b, ppm, c)
	var pd := _px(b, ppm, d)
	var mn := Vector2(minf(pa.x, minf(pc.x, pd.x)), minf(pa.y, minf(pc.y, pd.y))).floor()
	var mx := Vector2(maxf(pa.x, maxf(pc.x, pd.x)), maxf(pa.y, maxf(pc.y, pd.y))).ceil()
	var hgt := (a.y + c.y + d.y) / 3.0
	var col := Color.from_hsv(clampf(0.33 - hgt * 0.04, 0.0, 0.75), 0.55, 0.85)
	for y in range(maxi(int(mn.y), 0), mini(int(mx.y), img.get_height())):
		for x in range(maxi(int(mn.x), 0), mini(int(mx.x), img.get_width())):
			var p := Vector2(x + 0.5, y + 0.5)
			if Geometry2D.point_is_inside_triangle(p, pa, pc, pd):
				img.set_pixel(x, y, col)

func _dot(img: Image, b: AABB, ppm: float, p: Vector3, c: Color, r: int) -> void:
	var q := _px(b, ppm, p)
	for y in range(-r, r + 1):
		for x in range(-r, r + 1):
			var px := int(q.x) + x
			var py := int(q.y) + y
			if x * x + y * y <= r * r and px >= 0 and py >= 0 and px < img.get_width() and py < img.get_height():
				img.set_pixel(px, py, c)
