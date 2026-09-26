class_name WeaponTrail
extends MeshInstance3D
## Ribbon trail swept by the main-hand weapon between its inner blade point and its tip. Samples world positions
## every frame while active, keeps a short history and fades it out; drawn additively in world space.

const MAX_SAMPLES := 18
const LIFETIME := 0.16

var _visual: CharacterVisual
var _samples: Array = []          # [base: Vector3, tip: Vector3, age: float]
var _active := false
var _color := Color(1, 0.95, 0.85, 0.6)
var _length := 1.0
var _im := ImmediateMesh.new()
var _mat: StandardMaterial3D

func _ready() -> void:
	top_level = true
	global_transform = Transform3D.IDENTITY
	mesh = _im
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mat = StandardMaterial3D.new()
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mat.vertex_color_use_as_albedo = true
	_mat.no_depth_test = false
	material_override = _mat

func begin(visual: CharacterVisual, color: Color, length: float) -> void:
	_visual = visual
	_color = color
	_length = length
	_active = true

func end() -> void:
	_active = false

func tick(delta: float) -> void:
	for s in _samples:
		s[2] += delta
	while not _samples.is_empty() and _samples[0][2] > LIFETIME:
		_samples.pop_front()
	if _active and _visual and is_instance_valid(_visual):
		var b := _visual.weapon_point(&"main", 0.35, _length)
		var t := _visual.weapon_point(&"main", 1.0, _length)
		if b.is_finite() and t.is_finite():
			_samples.append([b, t, 0.0])
			if _samples.size() > MAX_SAMPLES:
				_samples.pop_front()
	_rebuild()

func _rebuild() -> void:
	_im.clear_surfaces()
	if _samples.size() < 2:
		return
	_im.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP, _mat)
	for s in _samples:
		var a := clampf(1.0 - float(s[2]) / LIFETIME, 0.0, 1.0)
		var c := Color(_color.r, _color.g, _color.b, _color.a * a * a)
		_im.surface_set_color(Color(c.r, c.g, c.b, 0.0))
		_im.surface_add_vertex(s[0])
		_im.surface_set_color(c)
		_im.surface_add_vertex(s[1])
	_im.surface_end()
