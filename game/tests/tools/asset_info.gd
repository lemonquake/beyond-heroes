extends SceneTree
## Prints each environment asset's bounds (Godot space) and its socket nodes. Usage:
##   godot --headless --path game -s res://tests/tools/asset_info.gd -- name1 name2 ...
func _initialize() -> void:
	for n in OS.get_cmdline_user_args():
		var p := "res://assets/environment/%s.glb" % n
		if not ResourceLoader.exists(p):
			print(n, " MISSING")
			continue
		var inst: Node3D = load(p).instantiate()
		var ab := AABB()
		var first := true
		var socks := []
		for c in inst.find_children("*", "", true, false):
			if c is MeshInstance3D and c.mesh and not String(c.name).ends_with("-colonly"):
				var a: AABB = (c as MeshInstance3D).global_transform * c.mesh.get_aabb() if c.is_inside_tree() else _xf(c, inst) * c.mesh.get_aabb()
				ab = a if first else ab.merge(a)
				first = false
			elif c.get_class() == "Node3D" and c.get_child_count() == 0:
				socks.append("%s@%s" % [c.name, _xf(c, inst).origin.snapped(Vector3.ONE * 0.01)])
		print("%-24s pos=%s size=%s sockets=%s" % [n, ab.position.snapped(Vector3.ONE * 0.01), ab.size.snapped(Vector3.ONE * 0.01), socks])
		inst.free()
	quit()

func _xf(n: Node, root: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	var c := n
	while c and c != root:
		t = (c as Node3D).transform * t
		c = c.get_parent()
	return t
