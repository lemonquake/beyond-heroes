extends SceneTree
## Read-only reference render of the original WOA resources in the same rig as
## capture_hero_models.gd. Run with --path A:/Python/woa -s <absolute script path>.
## No source-project files are created or edited by this script.

const SCENES := ["res://assets/characters/heroes17/emelrich.glb", "res://assets/characters/heroes17/azrin.glb",
	"res://assets/characters/hero/hero.glb", "res://assets/characters/heroes17/caziel.glb"]
const IDLES := [&"idle_shield", &"idle_staff", &"bow_idle", &"idle_dual"]
const STRIKES := [&"sword_2", &"staff_1", &"bow_shoot", &"dual_1"]
var models: Array = []
var labels: Array[Label3D] = []
var appearances: Array = []
var stage: Node3D
var out := ""

func _init() -> void:
	_run.call_deferred()

func _arg(key: String, fallback: String) -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--" + key + "="):
			return arg.substr(key.length() + 3)
	return fallback

func _run() -> void:
	out = _arg("out", "A:/Python/beyond-heroes/output/hero-models-source")
	DirAccess.make_dir_recursive_absolute(out)
	root.size = Vector2i(1920, 1080)
	root.content_scale_size = Vector2i(1920, 1080)
	root.content_scale_factor = 1.0
	stage = Node3D.new()
	root.add_child(stage)
	var env := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("202733")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("b0bdd1")
	environment.ambient_light_energy = 0.7
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.environment = environment
	stage.add_child(env)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-36, -32, 0)
	key.light_energy = 1.3
	key.shadow_enabled = true
	stage.add_child(key)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-24, 155, 0)
	fill.light_energy = 0.6
	fill.light_color = Color("9db9e8")
	stage.add_child(fill)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(30, 20)
	ground.mesh = plane
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("373f4b")
	material.roughness = 0.9
	ground.material_override = material
	stage.add_child(ground)
	var repair = load("res://src/game/repaired_clips.gd")
	for index in SCENES.size():
		var holder := Node3D.new()
		stage.add_child(holder)
		holder.position.x = (float(index) - 1.5) * 2.7
		var model := (load(SCENES[index]) as PackedScene).instantiate() as Node3D
		holder.add_child(model)
		repair.patch(model)
		if index == 2:
			var appearance = load("res://src/hero/hero_appearance.gd").new(model)
			var source = load("res://src/core/game_settings.gd").default_look("blood_ranger")
			appearance.apply(source.look)
			appearance.dress(source.outfit, source.dyes)
			appearances.append(appearance)
		var sk := model.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
		var ap := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
		ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		for pair in ([["R", "iron_longsword"], ["L", "warden_kite_shield"]] if index == 0 else
			([["R", "ashwood_staff"]] if index == 1 else ([["L", "hunters_bow"]] if index == 2 else
			[["R", "rondel_dagger"], ["L", "rondel_dagger"]]))):
			var attachment := BoneAttachment3D.new()
			attachment.bone_name = "weapon." + pair[0]
			sk.add_child(attachment)
			# WOA does not carry BH's dropped-item directory. Read the actual
			# equipped BH weapon GLB directly, without writing/importing in WOA.
			var weapon_path := String(get_script().resource_path).get_base_dir().path_join("../../assets/items/" + pair[1] + ".glb").simplify_path()
			var document := GLTFDocument.new()
			var state := GLTFState.new()
			var error := document.append_from_file(weapon_path, state)
			if error == OK:
				attachment.add_child(document.generate_scene(state))
			else:
				push_error("Cannot read matching equipped weapon: " + weapon_path)
		models.append({"holder": holder, "ap": ap, "sk": sk})
		var label := Label3D.new()
		label.text = ["Knight", "Mage", "Hunter", "Shadowblade"][index]
		label.position = Vector3(holder.position.x, 0.04, 0.85)
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.font_size = 44
		label.pixel_size = 0.0035
		label.no_depth_test = true
		stage.add_child(label)
		labels.append(label)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 6.7
	camera.cull_mask = 3
	stage.add_child(camera)
	camera.make_current()
	camera.look_at_from_position(Vector3(0, 3.8, 9.5), Vector3(0, 1.1, 0))
	for frame in 40:
		await process_frame
	_pose(IDLES, 0.4)
	await _shot("front_idle")
	for model in models:
		model.holder.rotation.y = -0.7
	await _shot("side_idle")
	for model in models:
		model.holder.rotation.y = 0.0
	for fraction in [0.0, 0.3, 0.65, 0.70, 0.95]:
		_pose(STRIKES, fraction)
		await _shot("attack_%03d" % int(fraction * 100.0))
	for index in models.size():
		models[index].holder.visible = index == 2
		labels[index].visible = index == 2
	models[2].holder.rotation.y = -0.65
	camera.size = 3.5
	camera.look_at_from_position(Vector3(1.35, 2.2, 7), Vector3(1.35, 1.1, 0))
	for time in [0.0, 0.175, 0.33, 0.35, 0.40, 0.533]:
		_pose([&"idle", &"idle", &"bow_shoot", &"idle"], time / 0.533)
		await _shot("bow_%04d" % int(time * 1000.0))
	print("HERO_SOURCE_CAPTURE_DONE ", out)
	quit()

func _pose(clips: Array, fraction: float) -> void:
	for index in models.size():
		var ap: AnimationPlayer = models[index].ap
		var clip: StringName = clips[index]
		if ap.has_animation(clip):
			var time := ap.get_animation(clip).length * fraction
			if clip == &"bow_shoot":
				var target := 0.533 * fraction
				time = target * 0.8 / 0.35 if target <= 0.35 else 0.8 + (target - 0.35) * (ap.get_animation(clip).length - 0.8) / (0.533 - 0.35)
			ap.play(clip)
			ap.seek(time, true)
			ap.advance(0.0)
			(models[index].sk as Skeleton3D).force_update_all_bone_transforms()

func _shot(label: String) -> void:
	for frame in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("HERO_SOURCE_SHOT ", label)
