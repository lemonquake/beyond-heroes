class_name HudOrb
extends Control
## HP / Mana orb: animated liquid (swirl noise, wavy surface, meniscus glint) in a painted frame with glass on top.
## A pale "lag" layer shows recent loss draining after a moment; the value is written under the orb.

const SHADER := """
shader_type canvas_item;
uniform float fill : hint_range(0.0, 1.0) = 1.0;
uniform float lag : hint_range(0.0, 1.0) = 1.0;
uniform vec4 deep : source_color = vec4(0.35, 0.02, 0.02, 1.0);
uniform vec4 bright : source_color = vec4(0.95, 0.18, 0.12, 1.0);
uniform vec4 lag_color : source_color = vec4(1.0, 0.85, 0.6, 0.8);
uniform sampler2D noise : repeat_enable, filter_linear;
uniform float pulse = 0.0;
void fragment() {
	vec2 p = UV - vec2(0.5);
	float r = length(p);
	float mask = 1.0 - smoothstep(0.485, 0.5, r);
	float t = TIME;
	float wave = sin(UV.x * 11.0 + t * 2.2) * 0.012 + sin(UV.x * 23.0 - t * 3.1) * 0.006;
	float level = 1.0 - fill + wave;
	float lag_level = 1.0 - lag + wave;
	vec2 nuv = UV * 1.4 + vec2(t * 0.03, -t * 0.05);
	float n = texture(noise, nuv).r * 0.6 + texture(noise, UV * 2.3 - vec2(t * 0.05, t * 0.02)).r * 0.4;
	float depth = clamp((UV.y - level) / max(0.001, fill), 0.0, 1.0);
	vec3 liquid = mix(bright.rgb, deep.rgb, depth * 0.85) * (0.75 + n * 0.55);
	liquid += bright.rgb * pulse * 0.35;
	float meniscus = smoothstep(0.035, 0.0, abs(UV.y - level)) * 0.55;
	vec4 col = vec4(0.03, 0.025, 0.03, 0.85);
	if (UV.y > lag_level && UV.y <= level) { col = vec4(lag_color.rgb * 0.8, lag_color.a); }
	if (UV.y > level) { col = vec4(liquid + meniscus, 1.0); }
	float edge = smoothstep(0.30, 0.5, r);
	col.rgb *= 1.0 - edge * 0.45;
	COLOR = vec4(col.rgb, col.a * mask);
}
"""

static var _shader: Shader

var kind := &"hp"
var value := 1.0
var max_value := 1.0
var _shown := 1.0
var _lag := 1.0
var _lag_hold := 0.0
var _liquid: ColorRect
var _mat: ShaderMaterial
var _label: Label
var _pulse := 0.0
var diameter := 150.0

func _init(p_kind := &"hp", p_diameter := 150.0) -> void:
	kind = p_kind
	diameter = p_diameter
	custom_minimum_size = Vector2(diameter, diameter + 24.0)
	mouse_filter = Control.MOUSE_FILTER_PASS

func _ready() -> void:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = SHADER
	var frame_path := "hud/orb_frame_hp.png" if kind == &"hp" else "hud/orb_frame_mana.png"
	var m := UIArt.meta(frame_path)
	var tex_size := 320.0
	var r_in: float = float(m.get("orb_radius", 112)) / tex_size * diameter
	var c: Array = m.get("orb_center", [160, 160])
	var center := Vector2(float(c[0]), float(c[1])) / tex_size * diameter
	_liquid = ColorRect.new()
	_liquid.position = center - Vector2(r_in, r_in)
	_liquid.size = Vector2(r_in, r_in) * 2.0
	_liquid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	_mat.set_shader_parameter("noise", UIArt.tex("hud/orb_liquid_noise.png"))
	if kind == &"hp":
		_mat.set_shader_parameter("deep", Color(0.28, 0.01, 0.02))
		_mat.set_shader_parameter("bright", Color(0.92, 0.14, 0.1))
		_mat.set_shader_parameter("lag_color", Color(1.0, 0.85, 0.6, 0.85))
	else:
		_mat.set_shader_parameter("deep", Color(0.02, 0.06, 0.3))
		_mat.set_shader_parameter("bright", Color(0.25, 0.55, 1.0))
		_mat.set_shader_parameter("lag_color", Color(0.75, 0.9, 1.0, 0.7))
	_liquid.material = _mat
	add_child(_liquid)
	var glass := TextureRect.new()
	glass.texture = UIArt.tex("hud/orb_glass.png")
	glass.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	glass.position = _liquid.position
	glass.size = _liquid.size
	glass.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(glass)
	var fr := TextureRect.new()
	fr.texture = UIArt.tex(frame_path)
	fr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	fr.size = Vector2(diameter, diameter)
	fr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(fr)
	_label = UITheme.label("", 17, UITheme.PARCHMENT, UITheme.number_font())
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	_label.add_theme_constant_override("outline_size", 5)
	_label.position = Vector2(0, center.y - 12.0)
	_label.size = Vector2(diameter, 24)
	add_child(_label)

func set_value(v: float, m: float) -> void:
	var nf := clampf(v / maxf(1.0, m), 0.0, 1.0)
	var of := value / maxf(1.0, max_value)
	if nf < of - 0.001:
		_lag_hold = 0.45
		if of - nf > 0.08:
			_pulse = 1.0
	value = v
	max_value = m
	_label.text = "%d / %d" % [ceili(v), roundi(m)]

func _process(delta: float) -> void:
	var target := clampf(value / maxf(1.0, max_value), 0.0, 1.0)
	_shown = lerpf(_shown, target, 1.0 - exp(-14.0 * delta))
	if _lag_hold > 0.0:
		_lag_hold -= delta
	else:
		_lag = lerpf(_lag, _shown, 1.0 - exp(-3.5 * delta))
	if _lag < _shown:
		_lag = _shown
	_pulse = maxf(0.0, _pulse - delta * 2.5)
	_mat.set_shader_parameter("fill", _shown)
	_mat.set_shader_parameter("lag", _lag)
	_mat.set_shader_parameter("pulse", _pulse)
