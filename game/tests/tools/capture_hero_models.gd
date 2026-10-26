extends Node3D
## Same camera, lighting, equipped items and sampled moments for baseline and candidate.
## No new class APIs are statically referenced, so this harness also runs in the
## frozen baseline. --body=class|custom --out=<absolute path>

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
const LABELS := ["Knight", "Mage", "Hunter", "Shadowblade"]
const IDLES := [&"idle_shield", &"idle_staff", &"idle_bow", &"idle_dual"]
const STRIKES := [&"sword_2", &"staff_1", &"bow_1", &"dual_1"]
var visuals: Array = []
var labels: Array[Label3D] = []
var out := ""

func _ready() -> void:
	_run.call_deferred()

func _arg(key: String, fallback: String) -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--" + key + "="):
			return arg.substr(key.length() + 3)
	return fallback

func _run() -> void:
	out = _arg("out", ProjectSettings.globalize_path("res://../output/hero-models"))
	DirAccess.make_dir_recursive_absolute(out)
	get_window().size = Vector2i(1920, 1080)
	get_window().content_scale_size = Vector2i(1920, 1080)
	get_window().content_scale_factor = 1.0
	var env := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("202733")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("b0bdd1")
	environment.ambient_light_energy = 0.7
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.environment = environment
	add_child(env)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-36, -32, 0)
	key.light_energy = 1.3
	key.shadow_enabled = true
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-24, 155, 0)
	fill.light_energy = 0.6
	fill.light_color = Color("9db9e8")
	add_child(fill)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(30, 20)
	ground.mesh = plane
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("373f4b")
	material.roughness = 0.9
	ground.material_override = material
	add_child(ground)
	var visual_script = load("res://src/actors/character_visual.gd")
	for index in CLASSES.size():
		var class_id: StringName = CLASSES[index]
		var hero = Game.new_hero(class_id, "Preview")
		hero.look = {"body": _arg("body", "class")}
		var visual = visual_script.new()
		add_child(visual)
		visual.position.x = (float(index) - 1.5) * 2.7
		if visual.has_method("setup_hero"):
			visual.call("setup_hero", class_id, hero.look, hero.cls.tint)
		else:
			visual.setup(HeroLook.MODEL, 1.0, hero.cls.tint, class_id)
			visual.set_look({})
		visual.dress_equipment(hero.equipment)
		var loadout = hero.equipment.loadout()
		var weapon = hero.equipment.get_item(&"main_weapon")
		var offhand = hero.equipment.get_item(&"sub_weapon")
		if weapon != null:
			visual.attach_weapon(&"main", weapon.base.model_path(), loadout.main_type.grip_offset)
		if offhand != null:
			visual.attach_weapon(&"off", offhand.base.model_path(), loadout.off_type.grip_offset if loadout.off_type else Transform3D.IDENTITY)
		visual.set_process(false)
		visual.tree.active = false
		visual.anim_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		visuals.append(visual)
		var label := Label3D.new()
		label.text = LABELS[index]
		label.position = Vector3(visual.position.x, 0.04, 0.85)
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.font_size = 44
		label.pixel_size = 0.0035
		label.no_depth_test = true
		add_child(label)
		labels.append(label)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 6.7
	# Perf places lights and floating labels on their own layers. A gallery
	# camera must see those layers just as the real gameplay camera does.
	camera.cull_mask = (1 << 20) - 1
	add_child(camera)
	camera.make_current()
	camera.look_at_from_position(Vector3(0, 3.8, 9.5), Vector3(0, 1.1, 0))
	for frame in 40:
		await get_tree().process_frame
	_pose(IDLES, 0.4)
	await _shot("front_idle")
	for visual in visuals:
		visual.rotation.y = -0.7
	await _shot("side_idle")
	for visual in visuals:
		visual.rotation.y = 0.0
	for fraction in [0.0, 0.3, 0.65, 0.70, 0.95]:
		_pose(STRIKES, fraction)
		await _shot("attack_%03d" % int(fraction * 100.0))
	# A close side view exposes the draw, hand separation and release of the bow.
	for index in visuals.size():
		visuals[index].visible = index == 2
		labels[index].visible = index == 2
	visuals[2].rotation.y = -0.65
	camera.size = 3.5
	camera.look_at_from_position(Vector3(1.35, 2.2, 7), Vector3(1.35, 1.1, 0))
	for time in [0.0, 0.175, 0.33, 0.35, 0.40, 0.533]:
		_pose([&"idle", &"idle", &"bow_1", &"idle"], time / 0.533)
		await _shot("bow_%04d" % int(time * 1000.0))
	print("HERO_MODEL_CAPTURE_DONE ", out)
	get_tree().quit()

func _pose(clips: Array, fraction: float) -> void:
	for index in visuals.size():
		var visual = visuals[index]
		var clip: StringName = clips[index]
		if visual.has_anim(clip):
			visual.anim_player.play(clip)
			visual.anim_player.seek(visual.anim_player.get_animation(clip).length * fraction, true)
			visual.anim_player.advance(0.0)
			visual.skeleton.force_update_all_bone_transforms()

func _shot(label: String) -> void:
	for frame in 3:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("HERO_MODEL_SHOT ", label)
