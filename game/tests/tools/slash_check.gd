extends Node3D
## Visual + numeric check that directional VFX follow the attacker's facing: four knights facing N/E/S/W each swing
## a slash (and one gets a cone telegraph). Saves a top-down-ish capture and prints the angle error of each arc.
func _ready() -> void:
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.12, 0.1, 0.09)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.8, 0.8, 0.8)
	add_child(env)
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(30, 30)
	ground.mesh = pm
	add_child(ground)
	FX.world = self
	var cls := DB.class_def(&"knight")
	var dirs := {"N": Vector3(0, 0, -1), "E": Vector3(1, 0, 0), "S": Vector3(0, 0, 1), "W": Vector3(-1, 0, 0)}
	var spots := {"N": Vector3(-5, 0, -3), "E": Vector3(5, 0, -3), "S": Vector3(-5, 0, 4), "W": Vector3(5, 0, 4)}
	var arcs := []
	for k in dirs:
		var body := Node3D.new()
		add_child(body)
		body.global_position = spots[k]
		body.rotation.y = atan2(dirs[k].x, dirs[k].z)
		var v := CharacterVisual.new()
		body.add_child(v)
		v.setup(cls.model_path, 1.0, cls.tint, cls.id)
		var fwd: Vector3 = body.global_transform.basis.z
		var arc := VFXLib.slash_arc(Color(1, 0.9, 0.6, 1), 2.6, 120.0, 1.05, 30.0, 0.55)
		FX.spawn_facing(arc, body.global_position, fwd)
		arc.process_mode = Node.PROCESS_MODE_DISABLED   # freeze the sweep tween; show the full swept arc
		(arc.material_override as ShaderMaterial).set_shader_parameter("progress", 1.05)
		arcs.append([k, arc, dirs[k]])
		var lbl := Label3D.new()
		lbl.text = k
		lbl.font_size = 96
		lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		lbl.position = body.global_position + Vector3(0, 2.8, 0)
		add_child(lbl)
	# enemy-style cone telegraph facing east from the east knight
	var tele := VFXLib.telegraph("cone", Vector2(3, 3), 30.0, Color(1.0, 0.25, 0.1, 0.8), 90.0)
	FX.spawn(tele, spots["E"] + Vector3(0, 0, 0))
	tele.process_mode = Node.PROCESS_MODE_DISABLED
	(tele.material_override as ShaderMaterial).set_shader_parameter("fill", 0.6)
	tele.rotation.y = atan2(1.0, 0.0) + PI
	var cam := Camera3D.new()
	add_child(cam)
	cam.position = Vector3(0, 14, 7)
	cam.look_at(Vector3(0, 0, 0.5))
	cam.make_current()
	for i in 20:
		await get_tree().process_frame
	# numeric check: the arc's centre of mass must lie along the facing
	var worst := 0.0
	for a in arcs:
		var mi: MeshInstance3D = a[1]
		var c: Vector3 = mi.global_transform * mi.mesh.get_aabb().get_center() - mi.global_position
		c.y = 0
		var err := rad_to_deg(c.normalized().angle_to(a[2]))
		worst = maxf(worst, err)
		print("SLASH %s error %.1f deg" % [a[0], err])
	print("SLASH_WORST %.1f" % worst)
	await get_tree().create_timer(0.8).timeout
	get_viewport().get_texture().get_image().save_png(String(OS.get_cmdline_user_args()[0]) if not OS.get_cmdline_user_args().is_empty() else "/tmp/slash.png")
	get_tree().quit()
