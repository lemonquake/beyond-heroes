extends Node
## bh-038: builds a map (no hero, no play) and lists every material its visible geometry draws with, grouped by the
## material and the scene piece it sits on, flagging the suspicious ones:
##   DARK    albedo (colour x texture-less) almost black and no glow: renders as a black hole in the scene
##   NOTEX   an env material whose texture set is named but did not load
##   NOMAT   a surface with no material at all
##   GLOW    a pure-white emissive surface (Zarael's glow rule)
##   godot --headless --path game res://tests/tools/map_material_audit.tscn -- --map=zr_barrens [--all]

var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
		elif a.begins_with("--"):
			args[a.substr(2)] = "1"
	await get_tree().process_frame
	for map_id in String(args.get("map", "zr_barrens")).split(",", false):
		var map := Game.build_map(StringName(map_id))
		if map == null:
			print("AUDIT %s: no such map" % map_id)
			continue
		add_child(map)
		await get_tree().process_frame
		var rows := {}
		for n in map.find_children("*", "GeometryInstance3D", true, false):
			_audit(n as GeometryInstance3D, map, rows)
		var keys := rows.keys()
		keys.sort_custom(func(a, b): return int(rows[a].n) > int(rows[b].n))
		print("AUDIT %s: %d material/piece pairs" % [map_id, keys.size()])
		for k in keys:
			var r: Dictionary = rows[k]
			if r.flags.is_empty() and not args.has("all"):
				continue
			print("  %-28s x%-4d %s  [%s]" % [", ".join(r.flags), r.n, k, r.where])
		map.queue_free()
		await get_tree().process_frame
	get_tree().quit()

func _audit(g: GeometryInstance3D, map: Node, rows: Dictionary) -> void:
	if not g.visible or not g.is_visible_in_tree():
		return
	var mesh: Mesh = null
	if g is MeshInstance3D:
		mesh = (g as MeshInstance3D).mesh
	elif g is MultiMeshInstance3D and (g as MultiMeshInstance3D).multimesh:
		mesh = (g as MultiMeshInstance3D).multimesh.mesh
	if mesh == null:
		return
	var piece := _piece(g, map)
	for i in mesh.get_surface_count():
		var m: Material = g.material_override
		if m == null and g is MeshInstance3D:
			m = (g as MeshInstance3D).get_surface_override_material(i)
		if m == null:
			m = mesh.surface_get_material(i)
		var flags := _flags(m, mesh, i)
		var key := "%s @ %s" % [_mname(m), piece]
		if not rows.has(key):
			rows[key] = {"n": 0, "flags": flags, "where": ""}
		rows[key].n += 1
		if rows[key].where == "":
			var p := (g as Node3D).global_position
			rows[key].where = "%.0f,%.1f,%.0f %s" % [p.x, p.y, p.z, String(g.name)]

func _flags(m: Material, mesh: Mesh, surf: int) -> Array:
	var f := []
	if m == null:
		f.append("NOMAT")
		return f
	if m is BaseMaterial3D:
		var b := m as BaseMaterial3D
		var glow := b.emission_enabled and b.emission_energy_multiplier > 0.2 and b.emission.get_luminance() > 0.05
		var lum := b.albedo_color.get_luminance()
		if b.albedo_texture == null and lum < 0.06 and not glow and b.shading_mode != BaseMaterial3D.SHADING_MODE_UNSHADED:
			f.append("DARK(%.3f)" % lum)
		elif b.albedo_texture != null and lum < 0.03 and not glow:
			f.append("DARKTINT(%.3f)" % lum)
		var key := String(b.resource_name).get_slice(".", 0)
		if MaterialLibrary.ENV.has(key) and String(MaterialLibrary.ENV[key][0]) != "" and b.albedo_texture == null and key != "BH_Leaves" and key != "BH_Grass":
			f.append("NOTEX")
		if glow and b.emission.r > 0.95 and b.emission.g > 0.95 and b.emission.b > 0.95:
			f.append("GLOW")
	elif m is ShaderMaterial:
		var sm := m as ShaderMaterial
		if sm.shader == null:
			f.append("NOSHADER")
		else:
			for u in sm.shader.get_shader_uniform_list():
				if int(u.type) == TYPE_OBJECT and sm.get_shader_parameter(u.name) == null:
					f.append("NULLTEX:%s" % u.name)
	return f

func _mname(m: Material) -> String:
	if m == null:
		return "<none>"
	var s := String(m.resource_name)
	if s == "" and m is ShaderMaterial and (m as ShaderMaterial).shader:
		s = "shader:" + (m as ShaderMaterial).shader.resource_path.get_file()
	if s == "":
		s = m.get_class()
	return s

## The scene the geometry came from (its GLB) or, for built geometry, its nearest named ancestor.
func _piece(g: Node, map: Node) -> String:
	var n := g
	while n != null and n != map:
		if n.scene_file_path != "":
			return n.scene_file_path.get_file().get_basename()
		n = n.get_parent()
	var p := g.get_parent()
	return "%s/%s" % [String(p.name) if p else "", String(g.name).rstrip("0123456789")]
