extends Node
## Finds geometry drawn twice in the same place (it flickers: both copies fight for the same depth). Builds a map the
## way the game does and lists every mesh — a MeshInstance3D or a MultiMesh instance — that appears more than once at
## the same transform.
##   godot --headless --path game res://tests/tools/dup_mesh_audit.tscn -- --map=agdao

func _ready() -> void:
	var map_id := &"agdao"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--map="):
			map_id = StringName(a.substr(6))
	await get_tree().process_frame
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "Probe")
	h.init_new()
	Game.hero = h
	var holder := Node3D.new()
	get_tree().root.add_child(holder)
	var m: MapRoot = Game.build_map(map_id)
	holder.add_child(m)
	await get_tree().process_frame
	var seen := {}
	var total := 0
	for n in m.find_children("*", "GeometryInstance3D", true, false):
		var entries: Array = []
		if n is MeshInstance3D and (n as MeshInstance3D).mesh:
			entries.append([(n as MeshInstance3D).mesh, (n as Node3D).global_transform, String(n.get_path())])
		elif n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh:
			var mm := (n as MultiMeshInstance3D).multimesh
			for i in mm.instance_count:
				entries.append([mm.mesh, (n as Node3D).global_transform * mm.get_instance_transform(i), String(n.name) + "#" + str(i)])
		for e in entries:
			total += 1
			var xf: Transform3D = e[1]
			var key := "%d|%s|%s" % [(e[0] as Mesh).get_rid().get_id(), (xf.origin * 100.0).round(), (xf.basis.x * 100.0).round()]
			if not seen.has(key):
				seen[key] = []
			(seen[key] as Array).append(e[2])
	var dups := 0
	var by_name := {}
	for k in seen:
		var l: Array = seen[k]
		if l.size() > 1:
			dups += 1
			var nm := String(l[0]).get_file()
			by_name[nm] = int(by_name.get(nm, 0)) + 1
	print("AUDIT %s: %d meshes, %d drawn more than once" % [map_id, total, dups])
	var names := by_name.keys()
	names.sort_custom(func(a, b): return by_name[a] > by_name[b])
	for nm in names.slice(0, 40):
		print("  DUP %s x%d" % [nm, by_name[nm]])
	get_tree().quit()
