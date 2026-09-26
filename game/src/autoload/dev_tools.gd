extends Node
## Development tools (autoload `Dev`). Enabled in debug builds (running from the editor) or with --dev; never in a
## release build without the flag. The panel (F1) lives in the UI (DevPanel); this node owns the debug overlays so
## they work even with the panel closed: FPS/profiling (F3), AI state labels, hitboxes, navmesh, damage formula.

var enabled := false
var show_fps := false
var show_ai := false
var show_hitboxes := false
var show_navmesh := false
var show_formula := false
var last_formula := PackedStringArray()
var _overlay: CanvasLayer
var _fps_label: Label
var _formula_label: Label
var _hitbox_mesh: MeshInstance3D
var _ai_labels := {}

func _ready() -> void:
	enabled = OS.is_debug_build() or "--dev" in OS.get_cmdline_user_args() or "--dev" in OS.get_cmdline_args()
	process_mode = Node.PROCESS_MODE_ALWAYS
	_overlay = CanvasLayer.new()
	_overlay.layer = 95
	add_child(_overlay)
	_fps_label = Label.new()
	_fps_label.position = Vector2(12, 1080 - 150)
	_fps_label.add_theme_font_size_override("font_size", 15)
	_fps_label.add_theme_color_override("font_color", Color(0.75, 1.0, 0.8))
	_fps_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	_fps_label.add_theme_constant_override("outline_size", 4)
	_fps_label.visible = false
	_overlay.add_child(_fps_label)
	_formula_label = Label.new()
	_formula_label.position = Vector2(12, 300)
	_formula_label.add_theme_font_size_override("font_size", 14)
	_formula_label.add_theme_color_override("font_color", Color(1.0, 0.95, 0.75))
	_formula_label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	_formula_label.add_theme_constant_override("outline_size", 4)
	_formula_label.visible = false
	_overlay.add_child(_formula_label)
	Events.damage_dealt.connect(_on_damage)

func _unhandled_input(e: InputEvent) -> void:
	if enabled and e.is_action_pressed(&"dev_fps"):
		show_fps = not show_fps

func set_navmesh(on: bool) -> void:
	show_navmesh = on
	NavigationServer3D.set_debug_enabled(on)
	if get_tree():
		get_tree().debug_navigation_hint = on

func _on_damage(_t: Node, r: DamageResult, _p: Vector3, attacker: Node) -> void:
	if show_formula and r != null and not r.steps.is_empty():
		last_formula = r.steps
		_formula_label.text = "Last hit%s:\n%s" % [" (by you)" if attacker == Game.player else "", "\n".join(r.steps)]

func _process(_d: float) -> void:
	_fps_label.visible = show_fps
	if show_fps:
		_fps_label.text = "FPS %d  (%.2f ms)\nProcess %.2f ms · Physics %.2f ms\nDraw calls %d · Objects %d · Primitives %dk\nNodes %d · Static memory %.0f MB · Video memory %.0f MB" % [
			Engine.get_frames_per_second(), 1000.0 / maxf(1.0, Engine.get_frames_per_second()),
			Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME) / 1000.0, Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
			Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0]
	_formula_label.visible = show_formula and not last_formula.is_empty()
	_update_ai_labels()
	_update_hitboxes()

func _update_ai_labels() -> void:
	for e in _ai_labels.keys():
		if not is_instance_valid(e) or not show_ai:
			if is_instance_valid(_ai_labels[e]):
				_ai_labels[e].queue_free()
			_ai_labels.erase(e)
	if not show_ai or get_tree() == null:
		return
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if not _ai_labels.has(e):
			var l := Label3D.new()
			l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			l.no_depth_test = true
			l.fixed_size = true
			l.pixel_size = 0.0008
			l.font_size = 22
			l.outline_size = 6
			l.modulate = Color(0.7, 1.0, 0.8)
			l.position = Vector3(0, float(e.body_height) + 0.9, 0)
			e.add_child(l)
			_ai_labels[e] = l
		(_ai_labels[e] as Label3D).text = e.debug_text()

func _update_hitboxes() -> void:
	if not show_hitboxes:
		if _hitbox_mesh and is_instance_valid(_hitbox_mesh):
			_hitbox_mesh.queue_free()
		_hitbox_mesh = null
		return
	var map: Node = Game.current_map
	if map == null or not is_instance_valid(map):
		return
	if _hitbox_mesh == null or not is_instance_valid(_hitbox_mesh):
		_hitbox_mesh = MeshInstance3D.new()
		_hitbox_mesh.mesh = ImmediateMesh.new()
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.vertex_color_use_as_albedo = true
		mat.no_depth_test = true
		_hitbox_mesh.material_override = mat
		map.add_child(_hitbox_mesh)
	var im := _hitbox_mesh.mesh as ImmediateMesh
	im.clear_surfaces()
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	for a in get_tree().get_nodes_in_group(&"enemy") + get_tree().get_nodes_in_group(&"player"):
		if not (a is Actor) or not a.alive:
			continue
		var col := Color(1.0, 0.3, 0.25) if a.is_in_group(&"enemy") else Color(0.35, 1.0, 0.45)
		var r: float = a.body_radius
		var h: float = a.body_height
		var c: Vector3 = a.global_position
		for y in [0.05, h]:
			for i in 16:
				var a0 := TAU * i / 16.0
				var a1 := TAU * (i + 1) / 16.0
				im.surface_set_color(col)
				im.surface_add_vertex(c + Vector3(cos(a0) * r, y, sin(a0) * r))
				im.surface_set_color(col)
				im.surface_add_vertex(c + Vector3(cos(a1) * r, y, sin(a1) * r))
		for i in 4:
			var ang := TAU * i / 4.0
			var o := Vector3(cos(ang) * r, 0, sin(ang) * r)
			im.surface_set_color(col)
			im.surface_add_vertex(c + o + Vector3(0, 0.05, 0))
			im.surface_set_color(col)
			im.surface_add_vertex(c + o + Vector3(0, h, 0))
	im.surface_end()
