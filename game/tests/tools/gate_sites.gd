extends Node
## bh-013: finds open ground for new dungeon gates on the surface maps. For each map: a 3 m grid over its bounds;
## a site is flat (ground within ±0.9 m over a 5 m ring), clear (no world/prop collider within 4.5 m), on the navmesh,
## 6–45 m from a road or trail, and away from places, camps, portals and spawns. Writes <map>__sites.png (navmesh,
## roads, existing features, candidate sites) and prints the candidates as "SITE map x z road_d".
##   godot --headless --path game res://tests/tools/gate_sites.tscn -- --maps=westreach --out=<dir>

func _ready() -> void:
	await get_tree().process_frame
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var ids: Array = String(args.get("maps", "westreach,ruined_forest,olivar,wyman_outpost")).split(",")
	var out := String(args.get("out", "."))
	var ppm := 3.0
	DirAccess.make_dir_recursive_absolute(out)
	for id in ids:
		var m := Game.build_map(StringName(id))
		add_child(m)
		MapBuilder.bake_navigation(m)
		for i in 3:
			await get_tree().physics_frame
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
		var roads := DataIsland.roads_on(StringName(id))
		for r in roads:
			var pts: Array = r.points
			for i in range(1, pts.size()):
				for t in 40:
					var p: Vector2 = pts[i - 1].lerp(pts[i], t / 40.0)
					_dot(img, b, ppm, Vector3(p.x, 0, p.y), Color(0.95, 0.8, 0.4) if r.type == "road" else Color(0.7, 0.55, 0.3), 1)
		var avoid: Array[Vector2] = []
		for p in DataIsland.all_places():
			if StringName(p.map) == StringName(id) and p.has("pos"):
				avoid.append(p.pos)
		for sid in m.spawns:
			var sp: Vector3 = m.spawns[sid].position
			avoid.append(Vector2(sp.x, sp.z))
		for t in m.teleporters():
			avoid.append(Vector2(t.position.x, t.position.z))
			_dot(img, b, ppm, t.global_position, Color(0.3, 0.9, 1.0), 4)
		for z in m.find_children("EnemyZone_*", "Marker3D", true, false):
			avoid.append(Vector2(z.global_position.x, z.global_position.z))
			_dot(img, b, ppm, z.global_position, Color(1.0, 0.25, 0.2), 3)
		for md in DataMinibosses.on_map(StringName(id)):
			avoid.append(md.pos)
		var space := m.get_world_3d().direct_space_state
		var nmap := m.nav_region.get_navigation_map()
		if args.has("check"):
			# --check=x,z;x,z : navmesh path from each named spawn to each point (length, or UNREACHABLE)
			for pt in String(args.check).split(";"):
				var xz := pt.split(",")
				var g := m.to_global(Vector3(float(xz[0]), 0, float(xz[1])))
				g.y = m.global_position.y + NpcDirectory.ground_height(m, Vector3(g.x, 20.0, g.z))
				var from: Vector3 = m.spawns[m.spawns.keys()[0]].global_position
				for sid in [&"start", &"arrival", &"west_gate", &"south_road"]:
					if m.spawns.has(sid):
						from = m.spawns[sid].global_position
						break
				var pa := NavigationServer3D.map_get_closest_point(nmap, from)
				var pb := NavigationServer3D.map_get_closest_point(nmap, g)
				var path := NavigationServer3D.map_get_path(nmap, pa, pb, true)
				var ok := not path.is_empty() and path[path.size() - 1].distance_to(pb) < 0.5 and Vector2(pb.x - g.x, pb.z - g.z).length() < 2.0
				var L := 0.0
				for i in range(1, path.size()):
					L += path[i - 1].distance_to(path[i])
				print("CHECK %s %s %s len=%.0f" % [id, pt, "OK" if ok else "UNREACHABLE", L])
			m.free()
			continue
		var n := 0
		var x := b.position.x + 8.0
		while x < b.end.x - 8.0:
			var z := b.position.z + 8.0
			while z < b.end.z - 8.0:
				var s := _site(m, space, nmap, x, z, roads, avoid)
				if s >= 0.0:
					n += 1
					print("SITE %s %.0f %.0f %.0f" % [id, x, z, s])
					_dot(img, b, ppm, Vector3(x, 0, z), Color(0.3, 1.0, 0.4), 2)
				z += 3.0
			x += 3.0
		img.save_png(out.path_join("%s__sites.png" % id))
		print("MAP ", id, " bounds ", m.bounds, " sites ", n)
		m.free()
	get_tree().quit()

func _site(m: MapRoot, space: PhysicsDirectSpaceState3D, nmap: RID, x: float, z: float, roads: Array, avoid: Array[Vector2]) -> float:
	var p := Vector2(x, z)
	for a in avoid:
		if p.distance_to(a) < 16.0:
			return -1.0
	var rd := INF
	for r in roads:
		rd = minf(rd, float(DataIsland.project(p, r.points).get("dist", INF)))
	if rd < 7.0 or rd > 45.0:
		return -1.0
	var y := NpcDirectory.ground_height(m, Vector3(x, 20.0, z))
	if y < -0.6:
		return -1.0
	for i in 8:
		var a := TAU * i / 8.0
		var yy := NpcDirectory.ground_height(m, Vector3(x + cos(a) * 5.0, 20.0, z + sin(a) * 5.0))
		if absf(yy - y) > 0.9:
			return -1.0
	var q := PhysicsShapeQueryParameters3D.new()
	var sh := SphereShape3D.new()
	sh.radius = 4.5
	q.shape = sh
	q.transform = Transform3D(Basis(), m.to_global(Vector3(x, y + 5.0, z)))
	q.collision_mask = BH.LAYER_WORLD | BH.LAYER_PROPS
	if not space.intersect_shape(q, 1).is_empty():
		return -1.0
	var g := m.to_global(Vector3(x, y, z))
	var c := NavigationServer3D.map_get_closest_point(nmap, g)
	if Vector2(c.x - g.x, c.z - g.z).length() > 1.5:
		return -1.0
	return rd

func _px(b: AABB, ppm: float, p: Vector3) -> Vector2:
	return Vector2((p.x - b.position.x) * ppm, (p.z - b.position.z) * ppm)

func _dot(img: Image, b: AABB, ppm: float, p: Vector3, c: Color, r: int) -> void:
	var q := _px(b, ppm, p)
	for dx in range(-r, r + 1):
		for dy in range(-r, r + 1):
			var xx := int(q.x) + dx
			var yy := int(q.y) + dy
			if xx >= 0 and yy >= 0 and xx < img.get_width() and yy < img.get_height():
				img.set_pixel(xx, yy, c)

func _tri(img: Image, b: AABB, ppm: float, a: Vector3, bb: Vector3, c: Vector3) -> void:
	var pa := _px(b, ppm, a)
	var pb := _px(b, ppm, bb)
	var pc := _px(b, ppm, c)
	var mn := Vector2(minf(pa.x, minf(pb.x, pc.x)), minf(pa.y, minf(pb.y, pc.y)))
	var mx := Vector2(maxf(pa.x, maxf(pb.x, pc.x)), maxf(pa.y, maxf(pb.y, pc.y)))
	var col := Color(0.2, 0.28, 0.3).lerp(Color(0.5, 0.6, 0.6), clampf((a.y + 4.0) / 16.0, 0.0, 1.0))
	for yy in range(int(mn.y), int(mx.y) + 1):
		for xx in range(int(mn.x), int(mx.x) + 1):
			if xx < 0 or yy < 0 or xx >= img.get_width() or yy >= img.get_height():
				continue
			var p := Vector2(xx + 0.5, yy + 0.5)
			var d1 := (p - pb).cross(pa - pb)
			var d2 := (p - pc).cross(pb - pc)
			var d3 := (p - pa).cross(pc - pa)
			if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
				img.set_pixel(xx, yy, col)
