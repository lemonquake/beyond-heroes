extends Node
## Triangle census (bh-009): builds maps and lists what their triangles are made of (per multimesh batch, per kit
## piece name, terrain), largest first. Headless is fine.
##   godot --headless --path game res://tests/tools/mesh_census.tscn -- --maps=westreach,sanctuary [--lite=1]

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	if String(args.get("lite", "0")) == "1":
		Settings._efficiency_preset()
	for id in String(args.get("maps", "westreach")).split(","):
		var m := Game.build_map(StringName(id))
		var by := {}
		var total := 0
		for n in m.find_children("*", "GeometryInstance3D", true, false):
			var tris := 0
			var key := ""
			if n is MultiMeshInstance3D and n.multimesh and n.multimesh.mesh:
				tris = _tris(n.multimesh.mesh) * n.multimesh.visible_instance_count if n.multimesh.visible_instance_count >= 0 else _tris(n.multimesh.mesh) * n.multimesh.instance_count
				key = "MM " + String(n.name)
			elif n is MeshInstance3D and n.mesh:
				tris = _tris(n.mesh)
				key = String(n.name).rstrip("0123456789_")
				var p := n.get_parent()
				while p and p != m and not (p.name in ["Props", "Geometry", "Decoration", "Lights", "Markers"]):
					key = String(p.name).rstrip("0123456789_") + "/" + key.get_file()
					p = p.get_parent()
			else:
				continue
			if not by.has(key):
				by[key] = [0, 0]
			by[key][0] += tris
			by[key][1] += 1
			total += tris
		var keys := by.keys()
		keys.sort_custom(func(a, b): return by[a][0] > by[b][0])
		print("CENSUS %s total %d tris" % [id, total])
		for k in keys.slice(0, 25):
			print("  %9d tris  x%-5d %s" % [by[k][0], by[k][1], k])
		m.free()
	get_tree().quit()

static func _tris(mesh: Mesh) -> int:
	var t := 0
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
		t += idx.size() / 3 if idx.size() > 0 else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
	return t
