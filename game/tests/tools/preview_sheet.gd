extends Node
## bh-033 preview sheets: render a labelled grid of 3D models with the real renderer. Models outside the project (the
## downloaded sources in assets_src/) load at runtime through GLTFDocument, so nothing is imported into the game.
##   godot --path game res://tests/tools/preview_sheet.tscn -- --list=<json> --out=<png> [--cols=6] [--tile=300]
## The list: [{"path": "A:/.../model.gltf" or "res://...glb", "label": "...", "anim": "Walk" (optional), "t": 0.4 (anim time
## fraction), "yaw": 30}]. A model is framed by its bounds; floor grid and light are shared.

var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	_run.call_deferred()

func _load_model(path: String) -> Node3D:
	if path.begins_with("res://"):
		var ps := load(path) as PackedScene
		return ps.instantiate() as Node3D if ps else null
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(path, st) != OK:
		return null
	return doc.generate_scene(st) as Node3D

func _bounds(n: Node) -> AABB:
	var box := AABB()
	var first := true
	for m in n.find_children("*", "VisualInstance3D", true, false):
		var vi := m as VisualInstance3D
		var b := vi.global_transform * vi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box

func _tile(entry: Dictionary, size: int, grid: Control) -> void:
	var box := VBoxContainer.new()
	grid.add_child(box)
	var svc := SubViewportContainer.new()
	svc.stretch = true
	svc.custom_minimum_size = Vector2(size, size)
	var sv := SubViewport.new()
	sv.size = Vector2i(size, size)
	sv.own_world_3d = true
	sv.msaa_3d = Viewport.MSAA_4X
	svc.add_child(sv)
	box.add_child(svc)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.16, 0.15, 0.14)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.6, 0.58, 0.55)
	e.ambient_light_energy = 0.7
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	sv.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 35, 0)
	sun.light_energy = 1.4
	sun.shadow_enabled = true
	sv.add_child(sun)
	var floor_mesh := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(40, 40)
	floor_mesh.mesh = pm
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color(0.25, 0.24, 0.22)
	floor_mesh.material_override = fm
	sv.add_child(floor_mesh)
	var model := _load_model(String(entry.path))
	var label := String(entry.get("label", String(entry.path).get_file()))
	if model == null:
		label += " (failed)"
	else:
		sv.add_child(model)
		model.rotation_degrees.y = float(entry.get("yaw", 25.0))
		var ap := model.find_children("*", "AnimationPlayer", true, false)
		if not ap.is_empty():
			var p := ap[0] as AnimationPlayer
			var want := String(entry.get("anim", ""))
			var names := p.get_animation_list()
			var pick := ""
			for nm in names:
				if want != "" and String(nm).to_lower().contains(want.to_lower()):
					pick = nm
					break
			if pick == "" and not names.is_empty():
				for nm in names:
					if String(nm).to_lower().contains("idle"):
						pick = nm
						break
			if pick != "":
				p.play(pick)
				p.seek(p.current_animation_length * float(entry.get("t", 0.3)), true)
				p.pause()
		var b := _bounds(model)
		model.position.y -= b.position.y
		b = _bounds(model)
		var c := b.get_center()
		var r := maxf(b.size.length() * 0.5, 0.05)
		var cam := Camera3D.new()
		cam.fov = 35.0
		var dist := r / tan(deg_to_rad(cam.fov * 0.5)) * 1.05
		cam.position = c + Vector3(0, r * 0.45, dist)
		sv.add_child(cam)
		cam.look_at(c, Vector3.UP)
		cam.current = true
		label += "  %.2f m" % b.size.y
	var l := UITheme.label(label, 15, UITheme.TEXT, UITheme.body_font())
	l.custom_minimum_size = Vector2(size, 0)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(l)

func _run() -> void:
	var list: Array = JSON.parse_string(FileAccess.get_file_as_string(String(args.list)))
	var cols := int(args.get("cols", "6"))
	var size := int(args.get("tile", "300"))
	var bg := ColorRect.new()
	bg.color = Color(0.09, 0.085, 0.08)
	add_child(bg)
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 12)
	add_child(margin)
	var v := VBoxContainer.new()
	margin.add_child(v)
	if args.has("title"):
		v.add_child(UITheme.label(String(args.title).replace("_", " "), 22, UITheme.GOLD, UITheme.title_font()))
	var grid := GridContainer.new()
	grid.columns = cols
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	v.add_child(grid)
	for entry in list:
		_tile(entry, size, grid)
	var rows := ceili(float(list.size()) / cols)
	var win := Vector2i(cols * (size + 8) + 24, rows * (size + 44) + 70)
	get_window().size = win
	bg.size = Vector2(win)
	for i in 30:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(String(args.out))
	print("SHEET ", args.out, " ", img.get_size(), " models ", list.size())
	get_tree().quit()
