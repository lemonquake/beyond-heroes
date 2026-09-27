class_name WorldShaders
## Environment shaders and materials shared by every map: luminous water, light shafts, ground mist, skies.

static var _water_shader: Shader
static var _shaft_shader: Shader
static var _mist_shader: Shader
static var _water_normal: Texture2D
static var _mist_noise: Texture2D

static func _normal_tex() -> Texture2D:
	if _water_normal:
		return _water_normal
	var n := FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = 0.02
	n.fractal_octaves = 3
	n.seed = 7
	var t := NoiseTexture2D.new()
	t.width = 256
	t.height = 256
	t.seamless = true
	t.as_normal_map = true
	t.bump_strength = 6.0
	t.noise = n
	_water_normal = t
	return t

static func _mist_tex() -> Texture2D:
	if _mist_noise:
		return _mist_noise
	var n := FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = 0.012
	n.fractal_octaves = 4
	n.seed = 11
	var t := NoiseTexture2D.new()
	t.width = 256
	t.height = 256
	t.seamless = true
	t.noise = n
	_mist_noise = t
	return t

## Luminous water (the teal cistern water of the reference): depth-faded colour, animated normals, self-glow that
## lights the scene through glow bloom, brighter foam line where the surface meets geometry.
static func water_material(shallow := Color(0.12, 0.62, 0.62), deep := Color(0.02, 0.12, 0.16), glow := 0.9,
		depth_fade := 2.5) -> ShaderMaterial:
	if _water_shader == null:
		_water_shader = Shader.new()
		_water_shader.code = """
shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_always, specular_schlick_ggx;
uniform vec4 shallow : source_color = vec4(0.12, 0.62, 0.62, 1.0);
uniform vec4 deep : source_color = vec4(0.02, 0.12, 0.16, 1.0);
uniform float glow = 0.9;
uniform float depth_fade = 2.5;
uniform float foam = 0.35;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	vec2 uv = wpos.xz * 0.06;
	vec3 n1 = texture(normal_tex, uv + vec2(TIME * 0.012, TIME * 0.008)).rgb;
	vec3 n2 = texture(normal_tex, uv * 1.7 - vec2(TIME * 0.01, -TIME * 0.014)).rgb;
	NORMAL_MAP = normalize(mix(n1, n2, 0.5));
	NORMAL_MAP_DEPTH = 0.6;
	float d = texture(depth_tex, SCREEN_UV).r;
	vec4 wp = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	wp.xyz /= wp.w;
	float diff = clamp((VERTEX.z - wp.z) / depth_fade, 0.0, 1.0);
	vec3 col = mix(shallow.rgb, deep.rgb, diff);
	float edge = 1.0 - smoothstep(0.0, 0.18, VERTEX.z - wp.z);
	ALBEDO = col + vec3(edge * foam);
	EMISSION = shallow.rgb * glow * (1.0 - diff * 0.7) + vec3(edge * foam * 0.6);
	ROUGHNESS = 0.06;
	SPECULAR = 0.6;
	ALPHA = mix(0.55, 0.93, diff);
}
"""
	var m := ShaderMaterial.new()
	m.shader = _water_shader
	m.set_shader_parameter("shallow", shallow)
	m.set_shader_parameter("deep", deep)
	m.set_shader_parameter("glow", glow)
	m.set_shader_parameter("depth_fade", depth_fade)
	m.set_shader_parameter("normal_tex", _normal_tex())
	return m

static var _water_lite_shader: Shader

## Efficiency-mode water (bh-009): the same colours without the depth-buffer read, the normal maps or lighting. A slow
## two-wave shimmer keeps it alive; unshaded, so a phone draws it once however many lights are near.
static func water_lite_material(shallow := Color(0.12, 0.62, 0.62), deep := Color(0.02, 0.12, 0.16), glow := 0.9) -> ShaderMaterial:
	if _water_lite_shader == null:
		_water_lite_shader = Shader.new()
		_water_lite_shader.code = """
shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_never, unshaded, shadows_disabled;
uniform vec4 shallow : source_color = vec4(0.12, 0.62, 0.62, 1.0);
uniform vec4 deep : source_color = vec4(0.02, 0.12, 0.16, 1.0);
uniform float glow = 0.9;
varying vec2 wxz;
void vertex() {
	wxz = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz;
}
void fragment() {
	float w = sin(wxz.x * 0.35 + TIME * 0.6) * sin(wxz.y * 0.28 - TIME * 0.45);
	float sparkle = smoothstep(0.82, 1.0, w);
	vec3 col = mix(deep.rgb, shallow.rgb, 0.45 + 0.12 * w);
	ALBEDO = col * (0.75 + 0.35 * glow) + vec3(sparkle * 0.25);
	ALPHA = 0.86;
}
"""
	var m := ShaderMaterial.new()
	m.shader = _water_lite_shader
	m.set_shader_parameter("shallow", shallow)
	m.set_shader_parameter("deep", deep)
	m.set_shader_parameter("glow", glow)
	return m

## Soft additive light shaft (moonlight through a broken roof, sun through trees). Fades at the ends and when
## viewed edge-on so it never becomes a hard slab.
static func shaft_material(c: Color, intensity := 0.35) -> ShaderMaterial:
	if _shaft_shader == null:
		_shaft_shader = Shader.new()
		_shaft_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(0.6, 0.7, 1.0, 1.0);
uniform float intensity = 0.35;
uniform sampler2D mist : filter_linear_mipmap, repeat_enable;
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	float v = UV.y;
	float ends = smoothstep(0.0, 0.25, v) * smoothstep(1.0, 0.55, v);
	float side = smoothstep(0.0, 0.3, UV.x) * smoothstep(1.0, 0.7, UV.x);
	float fres = pow(abs(dot(NORMAL, VIEW)), 2.0);
	float n = texture(mist, wpos.xz * 0.05 + vec2(TIME * 0.01, 0.0)).r;
	ALBEDO = color.rgb * intensity * ends * side * fres * (0.6 + 0.8 * n);
}
"""
	var m := ShaderMaterial.new()
	m.shader = _shaft_shader
	m.set_shader_parameter("color", c)
	m.set_shader_parameter("intensity", intensity)
	m.set_shader_parameter("mist", _mist_tex())
	return m

## Low drifting ground mist plane (alpha-blended noise), used in the forest hollows and the cistern.
static func mist_material(c := Color(0.55, 0.65, 0.75, 1.0), density := 0.35) -> ShaderMaterial:
	if _mist_shader == null:
		_mist_shader = Shader.new()
		_mist_shader.code = """
shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(0.55, 0.65, 0.75, 1.0);
uniform float density = 0.35;
uniform sampler2D mist : filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	float a = texture(mist, wpos.xz * 0.02 + vec2(TIME * 0.006, TIME * 0.004)).r;
	float b = texture(mist, wpos.xz * 0.045 - vec2(TIME * 0.009, 0.0)).r;
	float d = texture(depth_tex, SCREEN_UV).r;
	vec4 wp = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	wp.xyz /= wp.w;
	float soft = clamp((VERTEX.z - wp.z) / 1.5, 0.0, 1.0);
	float edge = smoothstep(0.0, 0.2, UV.x) * smoothstep(1.0, 0.8, UV.x) * smoothstep(0.0, 0.2, UV.y) * smoothstep(1.0, 0.8, UV.y);
	ALBEDO = color.rgb;
	ALPHA = clamp((a * 0.7 + b * 0.5 - 0.35) * 2.0, 0.0, 1.0) * density * soft * edge;
}
"""
	var m := ShaderMaterial.new()
	m.shader = _mist_shader
	m.set_shader_parameter("color", c)
	m.set_shader_parameter("density", density)
	m.set_shader_parameter("mist", _mist_tex())
	return m

static func night_sky(top := Color(0.03, 0.05, 0.1), horizon := Color(0.16, 0.18, 0.26), ground := Color(0.02, 0.02, 0.03)) -> Sky:
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = top
	sm.sky_horizon_color = horizon
	sm.ground_bottom_color = ground
	sm.ground_horizon_color = horizon.darkened(0.3)
	sm.sun_angle_max = 8.0
	sm.sky_energy_multiplier = 1.0
	var s := Sky.new()
	s.sky_material = sm
	s.radiance_size = Sky.RADIANCE_SIZE_64
	return s
