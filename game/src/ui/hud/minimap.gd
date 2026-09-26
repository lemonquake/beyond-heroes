class_name MiniMap
extends Control
## Circular minimap: an orthographic top-down camera into the live world (updated a few times a second, with its own
## bright environment so night maps stay readable), masked to a disc under the painted frame. Markers: the hero
## (arrow), enemies (red; elites gold, bosses large), NPCs (gold), waypoints (cyan), dropped loot (rarity colour).

const SHADER := """
shader_type canvas_item;
uniform sampler2D mask_tex : filter_linear;
void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float m = texture(mask_tex, UV).a;
	COLOR = vec4(c.rgb * 1.08, m);
}
"""

var radius_m := 26.0
var diameter := 200.0
var _vp: SubViewport
var _cam: Camera3D
var _view: TextureRect
var _markers: Control
var _frame: TextureRect
var _map_label: Label
var _update_t := 0.0

func _init(p_diameter := 200.0) -> void:
	diameter = p_diameter
	custom_minimum_size = Vector2(diameter, diameter + 26.0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	var m := UIArt.meta("hud/minimap_frame.png")
	var inner := diameter * 0.78
	_vp = SubViewport.new()
	_vp.size = Vector2i(256, 256)
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	_vp.msaa_3d = Viewport.MSAA_DISABLED
	_vp.positional_shadow_atlas_size = 0
	add_child(_vp)
	_cam = Camera3D.new()
	_cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	_cam.size = radius_m * 2.0
	_cam.far = 200.0
	_cam.rotation_degrees = Vector3(-90, 0, 0)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.03, 0.03, 0.04)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.85, 0.8, 0.72)
	env.ambient_light_energy = 1.6
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	_cam.environment = env
	_cam.cull_mask = 1   # world geometry only
	_vp.add_child(_cam)
	_view = TextureRect.new()
	_view.texture = _vp.get_texture()
	_view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_view.size = Vector2(inner, inner)
	_view.position = Vector2((diameter - inner) * 0.5, (diameter - inner) * 0.5)
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = SHADER
	mat.shader = sh
	mat.set_shader_parameter("mask_tex", UIArt.tex("hud/minimap_mask.png"))
	_view.material = mat
	_view.modulate = Color(0.78, 0.76, 0.72)
	add_child(_view)
	_markers = Control.new()
	_markers.position = _view.position
	_markers.size = _view.size
	_markers.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_markers.draw.connect(_draw_markers)
	add_child(_markers)
	_frame = TextureRect.new()
	_frame.texture = UIArt.tex("hud/minimap_frame.png")
	_frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_frame.size = Vector2(diameter, diameter)
	_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_frame)
	_map_label = UITheme.label("", 16, UITheme.PARCHMENT, UITheme.title_font())
	_map_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_map_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_map_label.add_theme_constant_override("outline_size", 5)
	_map_label.position = Vector2(-40, diameter - 4)
	_map_label.size = Vector2(diameter + 80, 24)
	add_child(_map_label)

func _process(delta: float) -> void:
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p) or not p.is_inside_tree() or not Settings.show_minimap:
		visible = Settings.show_minimap and p != null
		return
	visible = true
	if _vp.world_3d != p.get_world_3d():
		_vp.world_3d = p.get_world_3d()
	_map_label.text = Game.current_map.def.display_name if Game.current_map and Game.current_map.def else ""
	_update_t -= delta
	if _update_t <= 0.0:
		_update_t = 0.2
		_cam.global_position = p.global_position + Vector3(0, 60, 0)
		_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	_markers.queue_redraw()

func _to_map(world: Vector3, center: Vector3) -> Vector2:
	var d := Vector2(world.x - center.x, world.z - center.z) / (radius_m * 2.0)
	return _markers.size * 0.5 + d * _markers.size

func _draw_markers() -> void:
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p):
		return
	var c := _cam.global_position
	var half := _markers.size * 0.5
	var lim := half.x * 0.94
	var tree := get_tree()
	for t in tree.get_nodes_in_group(&"teleporter"):
		_dot(t.global_position, c, Color(0.5, 0.95, 1.0), 5.0, true, lim)
	for n in tree.get_nodes_in_group(&"npc"):
		_dot(n.global_position, c, UITheme.GOLD, 4.5, true, lim)
	for t in tree.get_nodes_in_group(&"tempo"):
		if t.alive:
			_dot(t.global_position, c, DataTempos.SPIRIT_TINT, 3.5, true, lim)
	for l in tree.get_nodes_in_group(&"loot"):
		var col := Color(0.9, 0.85, 0.5)
		if "item" in l and l.item != null:
			col = l.item.color()
		_dot(l.global_position, c, col, 2.5, false, lim)
	for e in tree.get_nodes_in_group(&"enemy"):
		if not e.alive:
			continue
		var col2 := Color(0.95, 0.25, 0.2)
		var r := 3.0
		if e.is_boss:
			col2 = Color(1.0, 0.1, 0.05)
			r = 7.0
		elif e.is_elite:
			col2 = UITheme.GOLD
			r = 4.5
		_dot(e.global_position, c, col2, r, e.is_boss, lim)
	# the hero: an arrow pointing where they face
	var f: Vector3 = p.global_transform.basis.z
	var ang := atan2(f.x, f.z)
	var tip := half + Vector2(sin(ang), cos(ang)) * 9.0
	var l2 := half + Vector2(sin(ang + 2.5), cos(ang + 2.5)) * 6.0
	var r2 := half + Vector2(sin(ang - 2.5), cos(ang - 2.5)) * 6.0
	_markers.draw_colored_polygon(PackedVector2Array([tip, l2, half, r2]), Color(1, 1, 1))
	_markers.draw_polyline(PackedVector2Array([tip, l2, half, r2, tip]), Color(0, 0, 0, 0.8), 1.5)

func _dot(world: Vector3, center: Vector3, col: Color, r: float, clamp_edge: bool, lim: float) -> void:
	var half := _markers.size * 0.5
	var q := _to_map(world, center)
	var off := q - half
	if off.length() > lim:
		if not clamp_edge:
			return
		q = half + off.normalized() * lim
	_markers.draw_circle(q, r + 1.2, Color(0, 0, 0, 0.8))
	_markers.draw_circle(q, r, col)
