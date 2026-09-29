extends Node3D
## Real CharacterVisual hand sockets and weapon stances under repeatable lighting.
## Does not load or save a player slot. Root integration captures in-town play separately.
var out := ""
var camera: Camera3D
var actors: Array[CharacterVisual] = []
var labels: Array[Label3D] = []

func _ready() -> void:
	out = ProjectSettings.globalize_path("res://../work/lemondev/tempo-armory/evidence/weapons/runtime")
	DirAccess.make_dir_recursive_absolute(out)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.025, 0.031, 0.045)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.58, 0.65, 0.8)
	e.ambient_light_energy = 0.6
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.environment = e
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, -30, 0)
	sun.light_energy = 1.4
	sun.light_color = Color(1, 0.87, 0.72)
	add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-22, 140, 0)
	fill.light_energy = 0.8
	fill.light_color = Color(0.55, 0.74, 1)
	add_child(fill)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(30, 30)
	ground.mesh = plane
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.055, 0.065, 0.085)
	ground.material_override = mat
	add_child(ground)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 5.9
	add_child(camera)
	camera.make_current()
	for family in ["bow", "crossbow", "dagger", "sword", "axe"]:
		var rows := DataArtisanWeapons.ROWS.filter(func(r): return r[2] == family)
		for batch in 2:
			_clear()
			for k in 5:
				var row: Array = rows[batch * 5 + k]
				var base := DB.item_base(StringName(row[0]))
				var cls := DB.class_def(base.class_hint)
				var visual := CharacterVisual.new()
				add_child(visual)
				visual.position.x = (k - 2) * 1.8
				visual.rotation.y = deg_to_rad(-16)
				visual.setup(cls.model_path, 1, cls.tint, cls.id)
				var wt := DB.weapon_type(base.weapon_type)
				var it := ItemInstance.new()
				it.base = base
				visual.attach_weapon(&"main", Player.weapon_model_for(it, wt), wt.grip_offset)
				visual.set_stance(wt.idle_anim)
				visual.update_locomotion(Vector2.ZERO, true)
				actors.append(visual)
				var label := Label3D.new()
				label.text = base.display_name
				label.font_size = 34
				label.pixel_size = 0.0022
				label.position = Vector3(visual.position.x, .05, .35)
				label.no_depth_test = true
				label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
				add_child(label)
				labels.append(label)
			camera.look_at_from_position(Vector3(0, 2.0, 10), Vector3(0, 1.05, 0))
			await _shot("%s_%d" % [family, batch])
			if family == "crossbow":
				for a in actors:
					a.play_action(&"crossbow_fire", 1, 0)
				await _shot("crossbow_action_%d" % batch, 8)
	print("ARTISAN_RUNTIME_CAPTURE_DONE")
	get_tree().quit()

func _clear() -> void:
	for actor in actors:
		actor.free()
	actors.clear()
	for label in labels:
		label.free()
	labels.clear()

func _shot(name: String, frames := 30) -> void:
	for i in frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	if name.begins_with("crossbow"):
		var v := actors[0]
		print("POSE_AXIS ",name," ",(v.weapon_point(&"main",1)-v.weapon_point(&"main",0)).normalized()," combat ",v._combat," action ",v.current_action())
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("ARTISAN_SHOT ", name)
