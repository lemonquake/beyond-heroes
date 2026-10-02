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
	for game in spec.clips:
		var source := String(spec.clips[game])
		if not src_lib.has_animation(source):
			return "missing clip %s" % source
		var a := src_lib.get_animation(source).duplicate(true) as Animation
		a.loop_mode = Animation.LOOP_LINEAR if game in ["idle", "idle_look", "walk", "run", "run_combat"] else Animation.LOOP_NONE
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
					img.generate_mipmaps()
					nm.albedo_texture = ImageTexture.create_from_image(img)
				else:
					nm.albedo_color = nm.albedo_color * tint
				nm.roughness = float(spec.get("rough", 0.85))
				nm.metallic = 0.0
				done[mat] = nm
			mi.set_surface_override_material(si, done[mat])
	# ---- save ---------------------------------------------------------------------------------------------------------
	_own(root, root)
	var ps := PackedScene.new()
	ps.pack(root)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(String(spec.out).get_base_dir()))
	var e := ResourceSaver.save(ps, String(spec.out))
	print("CLIPS ", JSON.stringify(report), " height_src ", snappedf(h, 0.01), " scale ", snappedf(s, 0.0001))
	return "" if e == OK else "save failed %d" % e

static func _own(n: Node, owner: Node) -> void:
	for c in n.get_children():
		c.owner = owner
		_own(c, owner)
