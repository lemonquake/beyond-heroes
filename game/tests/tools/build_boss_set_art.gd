extends Node
## Reproducible procedural boss armor export and real GPU icon rendering.
## -- --phase=gear exports non-weapons; --phase=weapons renders imported weapon GLBs.
const Art = preload("res://src/actors/boss_set_visuals.gd")
var vp: SubViewport
var scene: Node3D
var camera: Camera3D

func _ready() -> void:
	_run.call_deferred()

func _bounds(root: Node3D) -> AABB:
	var result := AABB()
	var first := true
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var box: AABB = root.global_transform.affine_inverse() * n.global_transform * n.get_aabb()
		result = box if first else result.merge(box)
		first = false
	return result

func _run() -> void:
	# bh-022: the collections are now built and iconised in Blender (tools/blender/items/boss_regalia.py -- models icons);
	# this exporter would overwrite those models and icons with the old procedural regalia.
	if not "--legacy" in OS.get_cmdline_user_args():
		print("BOSS_ART superseded by tools/blender/items/boss_regalia.py (pass --legacy to run the old exporter)")
		get_tree().quit()
		return
	var phase := "gear"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--phase="): phase = arg.substr(8)
	vp = SubViewport.new()
	vp.size = Vector2i(256,256)
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.msaa_3d = Viewport.MSAA_4X
	add_child(vp)
	scene = Node3D.new()
	vp.add_child(scene)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.55,0.62,0.8)
	e.ambient_light_energy = 0.65
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	e.glow_enabled = true
	env.environment = e
	scene.add_child(env)
	for pair in [[Vector3(-25,-30,0),1.6,Color(1.0,.91,.8)],[Vector3(-20,140,0),1.1,Color(.55,.75,1.0)]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = pair[0]
		light.light_energy = pair[1]
		light.light_color = pair[2]
		scene.add_child(light)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	scene.add_child(camera)
	camera.make_current()
	var count := 0
	for id in Art.THEMES:
		var slots: Array = Art.SLOTS.duplicate()
		if Art.THEMES[id][4] in ["axe","sword","wand","dagger","claw"]: slots.append("sub_weapon")
		for slot in slots:
			var weapon: bool = slot in ["main_weapon","sub_weapon"]
			if weapon != (phase=="weapons"): continue
			var item_id := "boss_%s_%s" % [id,slot]
			var model_path := "res://assets/items/%s.glb" % item_id
			var root: Node3D
			if weapon:
				var document := GLTFDocument.new()
				var state := GLTFState.new()
				var err := document.append_from_file(model_path,state)
				if err != OK:
					push_error("Missing boss weapon " + model_path)
					get_tree().quit(1)
					return
				root = document.generate_scene(state)
			else:
				root = Art.create_piece(id,slot)
				var document := GLTFDocument.new()
				var state := GLTFState.new()
				document.append_from_scene(root,state)
				var err := document.write_to_filesystem(state,model_path)
				if err != OK:
					push_error("Failed export " + item_id)
					get_tree().quit(1)
					return
			scene.add_child(root)
			var box := _bounds(root)
			var center := box.get_center()
			camera.size = maxf(box.size.x,maxf(box.size.y,box.size.z)) * 1.40
			camera.position = center + Vector3(0.4,0.3,2.4) * maxf(camera.size,1.0)
			camera.look_at(center)
			for frame in 3: await get_tree().process_frame
			await RenderingServer.frame_post_draw
			var image := vp.get_texture().get_image()
			image.save_png("res://assets/ui/icons/items3d/%s.png" % item_id)
			scene.remove_child(root)
			root.free()
			count += 1
		print("BOSS_ART ",id," exported")
	print("BOSS_ART_DONE ",phase," ",count)
	get_tree().quit()
