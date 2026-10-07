extends Node
## bh-033 creature conversion inside Godot: a downloaded glTF (left untouched in assets_src/) becomes a self-contained
## runtime scene with the game's clip names, scale and palette.
##   godot --headless --path game res://tests/tools/convert_creature.tscn -- --spec=<json>
## spec: {"src": gltf, "out": "res://assets/characters/bh033/<id>.scn", "height": m, "clips": {"game": "Source", ...},
##        "tint": [r,g,b], "saturation": 0..1, "value": 0..1 (darkening), "rough": 0..1}
## The root is a plain Node3D (CharacterVisual scales it); the model sits under it at the measured scale.

func _ready() -> void:
	var spec_path := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--spec="):
			spec_path = a.substr(7)
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(spec_path))
	var err := convert_model(spec)
	print("CONVERT ", spec.out, " -> ", "OK" if err == "" else err)
	get_tree().quit()

static func _aabb(n: Node) -> AABB:
	var box := AABB()
	var first := true
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		var b := mi.global_transform * mi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box

func convert_model(spec: Dictionary) -> String:
	var fbx := String(spec.src).to_lower().ends_with(".fbx")
	var doc: GLTFDocument = FBXDocument.new() if fbx else GLTFDocument.new()
	var st: GLTFState = FBXState.new() if fbx else GLTFState.new()
	if doc.append_from_file(String(spec.src), st) != OK:
		return "cannot read source"
	var model := doc.generate_scene(st) as Node3D
	var root := Node3D.new()
	root.name = String(spec.out).get_file().get_basename()
	add_child(root)
	root.add_child(model)
	model.name = "Model"
	# ---- clips ----------------------------------------------------------------------------------------------------
	var ap := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	var src_lib := ap.get_animation_library(&"")
	print("SOURCE CLIPS ", src_lib.get_animation_list())
	if spec.get("list_only", false):
		return "listed"
	var lib := AnimationLibrary.new()
	var report := {}
	# bh-042: a model already carrying the game's clip names (rigged on the hero skeleton) keeps all of them
	if spec.get("all_clips", false):
		var ident := {}
		for n in src_lib.get_animation_list():
			ident[String(n)] = String(n)
		spec["clips"] = ident
	for game in spec.clips:
		var source := String(spec.clips[game])
		if not src_lib.has_animation(source):
			return "missing clip %s" % source
		var a := src_lib.get_animation(source).duplicate(true) as Animation
		a.loop_mode = Animation.LOOP_LINEAR if game in ["idle", "idle_look", "walk", "run", "run_combat"] or game in spec.get("loops", []) else Animation.LOOP_NONE
		lib.add_animation(StringName(game), a)
		report[game] = [source, snappedf(a.length, 0.01)]
	# poses the source lacks: a copy of a source clip with a whole-body tilt keyed on the model root (hit recoil, lunge)
	for game in spec.get("synth", {}):
		var sy: Dictionary = spec.synth[game]
		var base_clip := String(sy.base)
		if not src_lib.has_animation(base_clip):
			return "missing synth base %s" % base_clip
		var a2 := src_lib.get_animation(base_clip).duplicate(true) as Animation
		var ln := float(sy.get("length", 0.4))
		a2.length = ln
		a2.loop_mode = Animation.LOOP_NONE
		var tr := a2.add_track(Animation.TYPE_ROTATION_3D)
		a2.track_set_path(tr, NodePath("."))
		var q := Quaternion(Vector3.RIGHT, float(sy.get("tilt", -0.4)))
		a2.rotation_track_insert_key(tr, 0.0, Quaternion.IDENTITY)
		a2.rotation_track_insert_key(tr, ln * float(sy.get("peak", 0.3)), q)
		a2.rotation_track_insert_key(tr, ln, Quaternion.IDENTITY)
		lib.add_animation(StringName(game), a2)
		report[game] = ["synth:" + base_clip, ln]
	ap.remove_animation_library(&"")
	ap.add_animation_library(&"", lib)
	# bh-042: helper meshes the source ships (Quaternius' hidden Icosphere) are dropped
	for m in model.find_children("*", "MeshInstance3D", true, false):
		for d in spec.get("drop", []):
			if String(m.name).begins_with(String(d)):
				m.get_parent().remove_child(m)
				m.free()
				break
	# ---- scale: idle pose height ----------------------------------------------------------------------------------
	ap.play(&"idle")
	ap.seek(0.0, true)
	var h := _aabb(model).size.y
	var s := float(spec.height) / h if h > 0.0 else 1.0
	model.scale = Vector3.ONE * s
	var b := _aabb(model)
	model.position.y -= b.position.y
	ap.stop()
	# ---- palette ----------------------------------------------------------------------------------------------------
	var tint := Color(spec.tint[0], spec.tint[1], spec.tint[2]) if spec.has("tint") else Color.WHITE
	var done := {}
	for m in model.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		for si in mi.mesh.get_surface_count():
			var mat := mi.get_active_material(si) as StandardMaterial3D
			if mat == null:
				continue
			if not done.has(mat):
				var nm := mat.duplicate() as StandardMaterial3D
				if nm.albedo_texture:
					var img := nm.albedo_texture.get_image()
					if img.is_compressed():
						img.decompress()
					for y in img.get_height():
						for x in img.get_width():
							var c := img.get_pixel(x, y)
							var hsv_s := c.s * float(spec.get("saturation", 0.7))
							var hsv_v := c.v * (1.0 - float(spec.get("value", 0.25)))
							var hue := c.h
							for hm in spec.get("hue_map", []):   # [from_lo, from_hi, to]: recolour one swatch family only
								if c.s > 0.15 and hue >= float(hm[0]) and hue <= float(hm[1]):
									hue = float(hm[2])
									break
							var o := Color.from_hsv(hue, hsv_s, hsv_v, c.a)
							img.set_pixel(x, y, Color(o.r * tint.r, o.g * tint.g, o.b * tint.b, o.a))
					_fit(img, int(spec.get("max_tex", 1024)))
					img.generate_mipmaps()
					nm.albedo_texture = ImageTexture.create_from_image(img)
				else:
					nm.albedo_color = nm.albedo_color * tint
				# bh-042: downloaded normal maps arrive at 2-4k; the game draws these at a few hundred pixels
				for slot in ["normal_texture", "roughness_texture", "metallic_texture", "ao_texture", "emission_texture"]:
					var t: Texture2D = nm.get(slot)
					if t:
						var ti := t.get_image()
						if ti:
							if ti.is_compressed():
								ti.decompress()
							_fit(ti, int(spec.get("max_tex", 1024)))
							ti.generate_mipmaps()
							nm.set(slot, ImageTexture.create_from_image(ti))
				nm.roughness = float(spec.get("rough", 0.85))
				nm.metallic = 0.0
				done[mat] = nm
			var use: StandardMaterial3D = done[mat]
			# bh-042: glowing parts (eyes, runes) by mesh name: {"match": "Eyes", "color": [r, g, b], "energy": 4}; a
			# glowing part gets its own material (the source often shares one atlas material across every part)
			for g in spec.get("glow", []):
				if String(mi.name).contains(String(g.match)) or String(mat.resource_name).contains(String(g.match)):
					use = use.duplicate() as StandardMaterial3D
					use.emission_enabled = true
					use.emission = Color(g.color[0], g.color[1], g.color[2])
					use.emission_energy_multiplier = float(g.get("energy", 3.0))
					use.albedo_color = Color(g.color[0], g.color[1], g.color[2])
					use.albedo_texture = null
					break
			# bh-042: a shader skin over the whole model (the lava golem's basalt and molten seams) except glowing parts
			if spec.has("shader") and not use.emission_enabled:
				var sm := ShaderMaterial.new()
				sm.shader = load(String(spec.shader))
				for k in spec.get("params", {}):
					var v: Variant = spec.params[k]
					sm.set_shader_parameter(k, Color(v[0], v[1], v[2]) if v is Array and v.size() == 3 else v)
				if use.albedo_texture and sm.shader.get_shader_uniform_list().any(func(u): return u.name == "albedo_tex"):
					sm.set_shader_parameter("albedo_tex", use.albedo_texture)
				mi.set_surface_override_material(si, sm)
				continue
			mi.set_surface_override_material(si, use)
	# ---- save ---------------------------------------------------------------------------------------------------------
	_own(root, root)
	var ps := PackedScene.new()
	ps.pack(root)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(String(spec.out).get_base_dir()))
	var e := ResourceSaver.save(ps, String(spec.out))
	print("CLIPS ", JSON.stringify(report), " height_src ", snappedf(h, 0.01), " scale ", snappedf(s, 0.0001))
	return "" if e == OK else "save failed %d" % e

static func _fit(img: Image, most: int) -> void:
	var big := maxi(img.get_width(), img.get_height())
	if big > most:
		var f := float(most) / float(big)
		img.resize(maxi(1, int(img.get_width() * f)), maxi(1, int(img.get_height() * f)), Image.INTERPOLATE_LANCZOS)

static func _own(n: Node, owner: Node) -> void:
	for c in n.get_children():
		c.owner = owner
		_own(c, owner)
