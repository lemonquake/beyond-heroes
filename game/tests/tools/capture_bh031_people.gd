extends Node
## bh-031 evidence: everyone on the hero body. Real Npc / Enemy nodes are not needed: each cell is a CharacterVisual
## dressed with Persona.apply exactly as Npc._ready and Enemy.setup do.
##   --mode=npcs      every townsperson                       -> npcs_<page>.png
##   --mode=enemies   every humanoid monster                  -> enemies_<page>.png
##   --per=<n>        cells per sheet (default 20)
var cells: Array = []

func _ready() -> void:
	Game.save_slot = 97
	_run.call_deferred()

func _arg(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name):
			return a.substr(name.length() + 3)
	return def

func _cell(parent: Control, size: Vector2, title: String, persona: Dictionary, scale_f: float) -> void:
	var col := VBoxContainer.new()
	parent.add_child(col)
	var svc := SubViewportContainer.new()
	svc.custom_minimum_size = size
	svc.stretch = true
	col.add_child(svc)
	var vp := SubViewport.new()
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_4X
	svc.add_child(vp)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color("1b2028")
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.55, 0.58, 0.65)
	e.ambient_light_energy = 0.7
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	vp.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, -30, 0)
	sun.light_energy = 1.25
	vp.add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-15, 150, 0)
	fill.light_energy = 0.45
	vp.add_child(fill)
	var v := CharacterVisual.new()
	vp.add_child(v)
	v.setup(Persona.MODEL, scale_f, Color.WHITE, &"")
	Persona.apply(v, persona)
	v.rotation_degrees.y = 20.0
	var h := 1.8 * scale_f * float(Persona.look_of(persona).get("height", 1.0))
	var cam := Camera3D.new()
	cam.fov = 30.0
	vp.add_child(cam)
	var dist := h * 2.2 + 0.6
	cam.position = Vector3(0, h * 0.55, dist)
	cam.look_at(Vector3(0, h * 0.5, 0))
	var l := UITheme.label(title, 18, Color("e8d8ae"), UITheme.body_bold())
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.custom_minimum_size.x = size.x
	l.autowrap_mode = TextServer.AUTOWRAP_WORD
	col.add_child(l)
	cells.append(v)

func _run() -> void:
	var out := ProjectSettings.globalize_path(_arg("out", "res://../work/lemondev/bh-031/evidence"))
	DirAccess.make_dir_recursive_absolute(out)
	var mode := _arg("mode", "npcs")
	var per := int(_arg("per", "20"))
	var list := []
	if mode == "npcs":
		for d: NpcDef in DB.npcs.values():
			var p := Persona.for_npc(d)
			if not p.is_empty():
				list.append([d.display_name, p, float(p.get("size", 1.0))])
	else:
		for e: EnemyDef in DB.enemies.values():
			var p := Persona.for_enemy(e)
			if not p.is_empty():
				list.append([e.display_name, p, float(p.get("size", 1.0)) * e.model_scale])
	var cols := 10
	var size := Vector2(240, 380)
	var page := 0
	var i := 0
	while i < list.size():
		for c in get_children():
			c.queue_free()
		cells.clear()
		await get_tree().process_frame
		var n := mini(per, list.size() - i)
		var rows := int(ceil(float(n) / cols))
		get_window().size = Vector2i(int(size.x) * cols, int(size.y + 50) * rows)
		var bg := ColorRect.new()
		bg.color = Color("15191f")
		bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		add_child(bg)
		var grid := GridContainer.new()
		grid.columns = cols
		add_child(grid)
		for k in n:
			var it: Array = list[i + k]
			_cell(grid, size, it[0], it[1], it[2])
		for f in 45:
			await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var path := out.path_join("%s_%d.png" % [mode, page])
		get_viewport().get_texture().get_image().save_png(path)
		print("SAVED ", path)
		i += n
		page += 1
	print("BH031_PEOPLE_DONE ", list.size())
	get_tree().quit()
