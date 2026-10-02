p = 'game/src/world/map_builder.gd'
s = open(p, encoding='utf-8').read()

# 1) batches keyed "name" or "name~s" (solid: never thinned on Low); the mesh is the name before "~"
old = '''	for name in _batches:
		var mesh := library_mesh(name)
		if mesh == null:
			continue
		var tr: Array = _batches[name].transforms
		if Perf.lite and LITE_KEEP.has(name):'''
new = '''	for name in _batches:
		var mesh := library_mesh(String(name).get_slice("~", 0))
		if mesh == null:
			continue
		var tr: Array = _batches[name].transforms
		if Perf.lite and LITE_KEEP.has(name):'''
assert old in s
s = s.replace(old, new)

# 2) solid(): batched visual + its own collision under Props
old = '''func breakable(kind: String, pos: Vector3, yaw_deg := 0.0, hp := 20.0, on_ground := false) -> Breakable:'''
new = '''## Map-design pass: a colliding kit piece drawn through the batches (one MultiMesh per piece kind per 24 m cell instead
## of a node and its draw calls per piece). Its collision is the piece's own shapes, scaled and placed on a StaticBody3D
## under Props, so the navmesh carves round it exactly as round a kit() piece. Solids are never thinned on Low.
func solid(name: String, xf: Transform3D, shadows := true) -> void:
	var key := name + "~s"
	if not _batches.has(key):
		_batches[key] = {"transforms": [], "shadows": shadows}
	_batches[key].transforms.append(xf)
	var sc := xf.basis.get_scale().x
	var shapes := _solid_shapes(name, sc)
	if not shapes.is_empty():
		var sb := StaticBody3D.new()
		sb.name = "%s_solid_%d" % [name, props.get_child_count()]
		sb.transform = Transform3D(xf.basis.orthonormalized(), xf.origin)
		sb.collision_layer = shapes[0][1]
		sb.collision_mask = shapes[0][2]
		for sh in shapes:
			var cs := CollisionShape3D.new()
			cs.shape = sh[0]
			sb.add_child(cs)
		props.add_child(sb)
	var box := _local_box_of(name)
	if box.size.y >= 0.35 and box.size.x * box.size.z >= 0.04:
		_solids.append([xf.affine_inverse(), Rect2(box.position.x, box.position.z, box.size.x, box.size.z), xf.origin.y + box.position.y * sc,
			xf.origin.y + box.end.y * sc])

static var _shape_cache := {}

## A piece's collision shapes baked to one scale, in the piece root's space: [shape, layer, mask] (cached).
static func _solid_shapes(name: String, sc: float) -> Array:
	var ck := "%s@%.3f" % [name, sc]
	if _shape_cache.has(ck):
		return _shape_cache[ck]
	var out: Array = []
	var inst := scene(name).instantiate()
	for b in inst.find_children("*", "CollisionObject3D", true, false):
		var co := b as CollisionObject3D
		var bt := Transform3D.IDENTITY
		var q: Node = co
		while q != null and q != inst:
			if q is Node3D:
				bt = (q as Node3D).transform * bt
			q = q.get_parent()
		for c in co.find_children("*", "CollisionShape3D", true, false):
			var cs := c as CollisionShape3D
			var t := Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * sc), Vector3.ZERO) * bt * cs.transform
			var shape: Shape3D = null
			if cs.shape is ConcavePolygonShape3D:
				var faces := (cs.shape as ConcavePolygonShape3D).get_faces()
				for i in faces.size():
					faces[i] = t * faces[i]
				var cp := ConcavePolygonShape3D.new()
				cp.set_faces(faces)
				shape = cp
			elif cs.shape is ConvexPolygonShape3D:
				var pts := (cs.shape as ConvexPolygonShape3D).points
				for i in pts.size():
					pts[i] = t * pts[i]
				var cv := ConvexPolygonShape3D.new()
				cv.points = pts
				shape = cv
			elif cs.shape is BoxShape3D:
				# boxes stay boxes: fold the transform into a convex hull of the eight corners
				var bs := cs.shape as BoxShape3D
				var h := bs.size * 0.5
				var pts := PackedVector3Array()
				for x in [-1, 1]:
					for y in [-1, 1]:
						for z in [-1, 1]:
							pts.append(t * Vector3(h.x * x, h.y * y, h.z * z))
				var cv := ConvexPolygonShape3D.new()
				cv.points = pts
				shape = cv
			if shape:
				out.append([shape, co.collision_layer, co.collision_mask])
	inst.free()
	_shape_cache[ck] = out
	return out

static func _local_box_of(name: String) -> AABB:
	if _piece_box.has(name):
		return _piece_box[name]
	var inst := scene(name).instantiate() as Node3D
	var b := _local_box(name, inst)
	inst.free()
	return b

## Decoration batched with a full transform (a tilted barrel, a fallen column), like decor() otherwise.
func decor_xf(name: String, xf: Transform3D, shadows := false) -> void:
	if not _batches.has(name):
		_batches[name] = {"transforms": [], "shadows": shadows}
	_batches[name].transforms.append(xf)

func breakable(kind: String, pos: Vector3, yaw_deg := 0.0, hp := 20.0, on_ground := false) -> Breakable:'''
assert old in s
s = s.replace(old, new)

# 3) vignettes: colliding pieces become batched solids, decoration is batched (no node per piece)
old = '''		match kind:
			"k":
				var n := kit(p[0], pos, pyaw, float(p[3]) * s, props)
				if anchor == null:
					anchor = n
			"b":
				decor(p[0], pos, pyaw, float(p[3]) * s, false)
			_:
				var n := kit(p[0], pos, pyaw, float(p[3]) * s, deco)
				for c in n.find_children("*", "CollisionObject3D", true, false):
					c.free()
				if anchor == null:
					anchor = n'''
new = '''		var xf := Transform3D(Basis(Vector3.UP, deg_to_rad(pyaw)).scaled(Vector3.ONE * float(p[3]) * s), pos)
		match kind:
			"k":
				solid(p[0], xf)
			"b":
				decor(p[0], pos, pyaw, float(p[3]) * s, false)
			_:
				decor_xf(p[0], xf, true)'''
assert old in s
s = s.replace(old, new)
s = s.replace('''	_vignettes.append({"name": vname, "origin": origin, "yaw": yaw, "r": r, "checked": bool(opts.get("check", true)) or bool(opts.get("near", false))})
	return anchor''', '''	_vignettes.append({"name": vname, "origin": origin, "yaw": yaw, "r": r, "checked": bool(opts.get("check", true)) or bool(opts.get("near", false))})
	return root''')
s = s.replace('''	var skip: Array = opts.get("skip", [])
	var anchor: Node3D = null
	for i in (d.pieces as Array).size():''', '''	var skip: Array = opts.get("skip", [])
	for i in (d.pieces as Array).size():''')
open(p, 'w', encoding='utf-8').write(s)

# 4) dungeon motifs: same — batched solids and batched decoration
p = 'game/src/world/maps/dungeon.gd'
s = open(p, encoding='utf-8').read()
old = '''		var n := kit(nm, pos, face_yaw + float(pc[2]), float(pc[3]), props if kind == "k" else deco)
		if kind != "k":
			for col in n.find_children("*", "CollisionObject3D", true, false):
				col.free()
		if pc.size() > 5:
			n.rotation.z = deg_to_rad(float(pc[5]))'''
new = '''		var b := Basis(Vector3.UP, deg_to_rad(face_yaw + float(pc[2])))
		if pc.size() > 5:
			b = b * Basis(Vector3(0, 0, 1), deg_to_rad(float(pc[5])))
		var xf := Transform3D(b.scaled(Vector3.ONE * float(pc[3])), pos)
		if kind == "k":
			solid(nm, xf)
		else:
			decor_xf(nm, xf, false)'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)

# 5) the probe's census understands solid batches
p = 'game/tests/tools/map_design_probe.gd'
s = open(p, encoding='utf-8').read()
s = s.replace('''				var k := b.trim_prefix("Batch_").rsplit("_", true, 2)[0]''', '''				var k := b.trim_prefix("Batch_").rsplit("_", true, 2)[0].get_slice("~", 0)''')
open(p, 'w', encoding='utf-8').write(s)
print("ok")
