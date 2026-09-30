extends SceneTree
## bh-023: what the imported hero.glb contains (mesh surfaces, blend shapes, clips, tracks of one clip).
func _initialize() -> void:
	var ps: PackedScene = load("res://assets/characters/hero.glb")
	var n := ps.instantiate()
	for c in n.find_children("*", "", true, false):
		if c is MeshInstance3D:
			var m: ArrayMesh = c.mesh
			print("MESH ", c.name, " surfaces=", m.get_surface_count(), " shapes=", m.get_blend_shape_count(), " mat=", m.surface_get_material(0).resource_name, " fmt=", m.surface_get_format(0), " verts=", m.surface_get_array_len(0))
			var names := []
			for i in m.get_blend_shape_count():
				names.append(m.get_blend_shape_name(i))
			print("SHAPES ", names)
			var arr := m.surface_get_arrays(0)
			print("HAS uv2=", arr[Mesh.ARRAY_TEX_UV2] != null, " color=", arr[Mesh.ARRAY_COLOR] != null)
			if arr[Mesh.ARRAY_TEX_UV2] != null:
				var mn := Vector2(9, 9); var mx := Vector2(-9, -9)
				for u in arr[Mesh.ARRAY_TEX_UV2]:
					mn = mn.min(u); mx = mx.max(u)
				print("UV2 range ", mn, mx)
			if arr[Mesh.ARRAY_COLOR] != null:
				var cmn := Color(9, 9, 9, 9); var cmx := Color(-9, -9, -9, -9)
				for col in arr[Mesh.ARRAY_COLOR]:
					cmn = Color(minf(cmn.r, col.r), minf(cmn.g, col.g), minf(cmn.b, col.b), minf(cmn.a, col.a))
					cmx = Color(maxf(cmx.r, col.r), maxf(cmx.g, col.g), maxf(cmx.b, col.b), maxf(cmx.a, col.a))
				print("COLOR range ", cmn, cmx)
		elif c is Skeleton3D:
			var bn := []
			for i in c.get_bone_count():
				bn.append(c.get_bone_name(i))
			print("BONES ", bn)
		elif c is AnimationPlayer:
			var l: PackedStringArray = c.get_animation_list()
			print("CLIPS ", l.size(), " ", l)
			var a: Animation = c.get_animation("hero_walk")
			var kinds := {}
			for t in a.get_track_count():
				kinds[a.track_get_type(t)] = int(kinds.get(a.track_get_type(t), 0)) + 1
			print("hero_walk tracks ", kinds, " len=", a.length)
	quit()
