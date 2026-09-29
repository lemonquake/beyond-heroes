extends Node3D
## bh-021 look check of the legend models in the real renderer (textures, clips, auras), no game session.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_bh021_models.tscn -- --out=<dir>

var out := ""

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-021/evidence/models")))
	DirAccess.make_dir_recursive_absolute(out)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.02, 0.018, 0.03)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.35, 0.36, 0.45)
	e.ambient_light_energy = 0.6
	e.glow_enabled = true
	e.glow_intensity = 0.9
	e.glow_bloom = 0.15
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	e.fog_enabled = true
	e.fog_light_color = Color(0.08, 0.06, 0.1)
	e.fog_density = 0.02
	env.environment = e
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, -35, 0)
	sun.light_energy = 0.9
	sun.light_color = Color(0.75, 0.8, 1.0)
	sun.shadow_enabled = true
	add_child(sun)
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(40, 40)
	ground.mesh = pm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.09, 0.085, 0.09)
	gm.roughness = 0.6
	ground.material_override = gm
	add_child(ground)
	var cast := [
		["aljay", 1.14, "cs_aj_point", "dusk_piercer", Vector3(-3.6, 0, 0), "wrath"],
		["roydo", 1.17, "cs_ro_shoulder", "dawnmaul", Vector3(-1.2, 0, 0), "holy"],
		["paul_david", 1.03, "cs_pd_ready", "stormwake", Vector3(1.2, 0, 0), "storm"],
		["kethrax", 1.28, "cs_kx_pull", "kethrax_mace", Vector3(3.7, 0, 0), "soul"],
	]
	var actors := []
	for c in cast:
		var a := CutsceneActor.make(c[0], c[1])
		add_child(a)
		a.position = c[4]
		a.rotation.y = deg_to_rad(0.0)
		a.play(StringName(c[2]), 0.0)
		var w := a.attach(&"main", c[3])
		if c[0] == "paul_david":
			a.hide_surfaces("BH_Hilt")
		match c[5]:
			"wrath": a.add_child(LegendFX.wrath_aura(1.0))
			"holy": a.add_child(LegendFX.holy_aura(1.0))
			"storm":
				if OS.get_environment("BH_NO_STORM") == "1":
					continue
				var au := LegendFX.storm_aura(1.0)
				var f := a.follow("weapon.R")
				f.add_child(au)
				au.position = Vector3(0, 0.0, -0.5)
			"soul": a.add_child(LegendFX.soulfire(0.8))
		actors.append(a)
	var cam := Camera3D.new()
	cam.fov = 40
	add_child(cam)
	cam.make_current()
	for i in 40:
		await get_tree().process_frame
	cam.look_at_from_position(Vector3(0.0, 2.2, 9.5), Vector3(0, 1.2, 0))
	await _shot("lineup")
	var closes := [["aljay", Vector3(-3.6, 1.72, 0), 2.1], ["roydo", Vector3(-1.2, 1.8, 0), 2.2],
		["paul_david", Vector3(1.2, 1.55, 0), 1.5], ["kethrax", Vector3(3.7, 1.95, 0), 2.4]]
	for c in closes:
		var p: Vector3 = c[1]
		cam.look_at_from_position(p + Vector3(0.5, 0.1, float(c[2])), p)
		await _shot("close_" + c[0])
	get_tree().quit()

func _shot(label: String) -> void:
	for i in 12:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH021 SHOT ", label)
