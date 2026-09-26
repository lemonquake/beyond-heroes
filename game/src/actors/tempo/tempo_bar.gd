class_name TempoBar
extends Node3D
## Floating HP (spirit teal) and mana (blue) bars over a Tempo. Always shown while it lives, so the hero can read a
## companion's state at a glance without looking away from the fight (the HUD party frames show the same numbers).

var tempo: Actor
var _quad: MeshInstance3D
var _mat: ShaderMaterial
var _shown_hp := 1.0
var _lag_hp := 1.0

static var _shader: Shader

func _ready() -> void:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled;
uniform float fill = 1.0;
uniform float lag = 1.0;
uniform float mana = 1.0;
uniform vec4 fill_color : source_color = vec4(0.35, 0.95, 0.8, 1.0);
void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
}
void fragment() {
	vec2 uv = UV;
	float border = step(uv.x, 0.012) + step(0.988, uv.x) + step(uv.y, 0.08) + step(0.92, uv.y) + step(0.62, uv.y) * step(uv.y, 0.68);
	vec3 c = vec3(0.03, 0.04, 0.05);
	if (uv.y < 0.62) {
		if (uv.x < lag) c = vec3(0.95, 0.85, 0.55);
		if (uv.x < fill) c = fill_color.rgb * (0.78 + 0.22 * (1.0 - uv.y / 0.62));
	} else if (uv.x < mana) {
		c = vec3(0.25, 0.5, 1.0);
	}
	c = mix(c, vec3(0.35, 0.55, 0.62), clamp(border, 0.0, 1.0));
	ALBEDO = c;
	ALPHA = 0.95;
}
"""
	_quad = MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(0.95, 0.15)
	_quad.mesh = q
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	_mat.render_priority = 5
	_quad.material_override = _mat
	_quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_quad)

func _process(delta: float) -> void:
	if tempo == null or not is_instance_valid(tempo) or _mat == null:
		return
	var f := clampf(tempo.hp / maxf(1.0, tempo.max_hp()), 0.0, 1.0)
	_shown_hp = f
	_lag_hp = move_toward(_lag_hp, f, delta * 0.6) if _lag_hp > f else f
	_mat.set_shader_parameter("fill", _shown_hp)
	_mat.set_shader_parameter("lag", _lag_hp)
	_mat.set_shader_parameter("mana", clampf(tempo.mana / maxf(1.0, tempo.max_mana()), 0.0, 1.0))
	_mat.set_shader_parameter("fill_color", Color(0.95, 0.35, 0.25) if f < 0.3 else Color(0.35, 0.95, 0.8))
