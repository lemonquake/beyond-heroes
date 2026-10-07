class_name LootFx
## Ground-loot presentation (bh-006): rarity-coloured twinkling sparkles, a soft pulsing ground glow and a moving glint
## over the item's own model. Replaces the old light beams: higher tiers sparkle more, bigger and brighter; Aether
## sparkles cycle through a prism of colours.

const SPARKLE_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform float prism = 0.0;       // 1 = hue-cycling Aether sparkles
uniform float boost = 2.4;
varying vec4 pcol;
varying float seed;
vec3 hue(float h) {
	return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}
void vertex() {
	mat4 mw = mat4(normalize(INV_VIEW_MATRIX[0]), normalize(INV_VIEW_MATRIX[1]), normalize(INV_VIEW_MATRIX[2]), MODEL_MATRIX[3]);
	float a = INSTANCE_CUSTOM.x;
	mw = mw * mat4(vec4(cos(a), -sin(a), 0.0, 0.0), vec4(sin(a), cos(a), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_MATRIX = VIEW_MATRIX * mw;
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
		vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	pcol = COLOR;
	seed = INSTANCE_CUSTOM.w + float(INSTANCE_ID) * 0.137;
}
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	// four-point star: two thin crossed streaks, a hot core and a soft halo
	float sx = max(0.0, 1.0 - abs(p.y) * 16.0) * pow(max(0.0, 1.0 - abs(p.x)), 1.6);
	float sy = max(0.0, 1.0 - abs(p.x) * 16.0) * pow(max(0.0, 1.0 - abs(p.y)), 1.6);
	float core = exp(-r * r * 40.0);
	float halo = exp(-r * r * 7.0) * 0.28;
	float a = clamp(sx + sy + core * 1.4 + halo, 0.0, 2.0) * pcol.a;
	vec3 c = pcol.rgb;
	if (prism > 0.5) {
		c = mix(c, hue(fract(TIME * 0.35 + seed)), 0.75);
	}
	ALBEDO = mix(c, vec3(1.0), clamp(core * 0.8, 0.0, 1.0)) * a * boost;
}
"""

const GLOW_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform vec4 color : source_color = vec4(1.0);
uniform float strength = 0.5;
uniform float pulse = 0.3;
uniform float prism = 0.0;
vec3 hue(float h) {
	return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float g = smoothstep(1.0, 0.0, r);
	g = g * g;
	float ring = exp(-pow((r - 0.72 - 0.05 * sin(TIME * 2.0)) * 9.0, 2.0)) * 0.45;
	float k = strength * (1.0 - pulse * 0.5 + pulse * 0.5 * sin(TIME * 2.6));
	vec3 c = color.rgb;
	if (prism > 0.5) {
		c = mix(c, hue(fract(TIME * 0.2 + atan(p.y, p.x) / 6.2832)), 0.6);
	}
	ALBEDO = c * (g + ring) * k;
}
"""

const GLINT_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, depth_draw_never, shadows_disabled, fog_disabled;
uniform vec4 color : source_color = vec4(1.0);
uniform float strength = 0.5;
uniform float speed = 0.55;
void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.4);
	vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float band = fract((wp.x * 0.8 + wp.y * 1.2 + wp.z * 0.5) * 0.85 - TIME * speed);
	float glint = smoothstep(0.0, 0.035, band) * smoothstep(0.09, 0.035, band);
	ALBEDO = mix(color.rgb, vec3(1.0), glint * 0.6) * (fres * 0.7 + glint * 1.6) * strength;
}
"""

# Per rarity tier (Beginner .. Aether, then the four Ascendant tiers, which add AscendantFx on top)
const SPARKLE_COUNT := [3, 4, 6, 8, 10, 13, 16, 20, 26, 34, 38, 42, 46, 52, 72]
const SPARKLE_SIZE := [0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.18, 0.2, 0.22, 0.23, 0.24, 0.24, 0.26, 0.3]
const SPARKLE_ALPHA := [0.35, 0.45, 0.6, 0.7, 0.75, 0.85, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
const GLOW_STRENGTH := [0.06, 0.09, 0.13, 0.17, 0.2, 0.25, 0.3, 0.36, 0.42, 0.5, 0.55, 0.6, 0.62, 0.68, 0.8]
const GLINT_STRENGTH := [0.12, 0.18, 0.28, 0.36, 0.42, 0.5, 0.6, 0.7, 0.8, 0.95, 1.0, 1.05, 1.05, 1.1, 1.35]

static var _shaders := {}

static func _shader(key: String, code: String) -> Shader:
	if not _shaders.has(key):
		var sh := Shader.new()
		sh.code = code
		_shaders[key] = sh
	return _shaders[key]

## Low tiers sparkle in a pale version of their colour so plain loot still twinkles without shouting.
static func sparkle_color(rarity: int) -> Color:
	var c := BH.rarity_color(rarity)
	if rarity <= BH.Rarity.COMMON:
		c = c.lerp(Color(1.0, 0.97, 0.9), 0.4)
	return c

## Twinkling four-point stars scattered over and around the item (footprint radius `radius`, up to `height`).
static func sparkles(rarity: int, radius: float, height := 0.5) -> GPUParticles3D:
	var r := clampi(rarity, 0, BH.RARITY_COUNT - 1)
	var c := sparkle_color(r)
	var p := GPUParticles3D.new()
	p.amount = Perf.particles(SPARKLE_COUNT[r])
	p.lifetime = 1.1 if r < BH.Rarity.MYTHICAL else 0.9
	p.randomness = 0.6
	p.preprocess = 1.0
	p.local_coords = true
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(radius, height * 0.5, radius)
	pm.direction = Vector3.UP
	pm.spread = 25.0
	pm.initial_velocity_min = 0.05
	pm.initial_velocity_max = 0.25 + 0.03 * r
	pm.gravity = Vector3.ZERO
	pm.angle_min = 0.0
	pm.angle_max = 90.0
	pm.angular_velocity_min = -40.0
	pm.angular_velocity_max = 40.0
	pm.scale_min = 0.55
	pm.scale_max = 1.0
	var curve := Curve.new()
	curve.add_point(Vector2(0.0, 0.0))
	curve.add_point(Vector2(0.25, 1.0))
	curve.add_point(Vector2(0.5, 0.35))
	curve.add_point(Vector2(0.7, 0.8))
	curve.add_point(Vector2(1.0, 0.0))
	var ct := CurveTexture.new()
	ct.curve = curve
	pm.scale_curve = ct
	var g := Gradient.new()
	g.set_color(0, Color(c.r, c.g, c.b, SPARKLE_ALPHA[r]))
	g.set_color(1, Color(c.r, c.g, c.b, SPARKLE_ALPHA[r] * 0.6))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2.ONE * SPARKLE_SIZE[r] * 2.0
	var mat := ShaderMaterial.new()
	mat.shader = _shader("sparkle", SPARKLE_SHADER)
	mat.set_shader_parameter("prism", 1.0 if r == BH.Rarity.AETHER else 0.0)
	mat.set_shader_parameter("boost", 2.0 + 0.12 * r)
	q.material = mat
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-2, -1, -2), Vector3(4, 4, 4))
	p.position.y = height * 0.5
	return p

## Soft additive particles that KEEP their per-particle scale (VFXLib.particle_material drops it: 0.5 m puffs).
static var _soft_mat: StandardMaterial3D

static func soft_material() -> StandardMaterial3D:
	if _soft_mat == null:
		_soft_mat = VFXLib.particle_material(true).duplicate()
		_soft_mat.billboard_keep_scale = true
	return _soft_mat

## Small soft particles of a real size (m). Same parameters as VFXLib.particles.
static func small_particles(color: Color, amount: int, lifetime: float, size: float, velocity: float, spread: float,
		gravity: Vector3, emission_radius: float) -> GPUParticles3D:
	var p := VFXLib.particles(color, amount, lifetime, false, 1.0, velocity, spread, gravity, emission_radius)
	var pm := p.process_material as ParticleProcessMaterial
	pm.scale_min = 0.6
	pm.scale_max = 1.0
	var q := QuadMesh.new()
	q.size = Vector2.ONE * size
	q.material = soft_material()
	p.draw_pass_1 = q
	return p

## Slow motes drifting upward (Mythical and above): the item "breathes" light instead of firing a beam.
static func motes(rarity: int, radius: float) -> GPUParticles3D:
	var c := BH.rarity_color(rarity)
	var p := small_particles(Color(c.r, c.g, c.b, 0.85), 8 + 3 * (rarity - BH.Rarity.MYTHICAL), 1.8, 0.07, 0.35, 12.0,
		Vector3(0, 0.25, 0), radius)
	p.preprocess = 1.5
	return p

static func ground_glow(rarity: int, radius: float) -> MeshInstance3D:
	var r := clampi(rarity, 0, BH.RARITY_COUNT - 1)
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2.ONE * radius * 2.0
	mi.mesh = pm
	var mat := ShaderMaterial.new()
	mat.shader = _shader("glow", GLOW_SHADER)
	mat.set_shader_parameter("color", sparkle_color(r))
	mat.set_shader_parameter("strength", GLOW_STRENGTH[r])
	mat.set_shader_parameter("pulse", 0.25 + 0.04 * r)
	mat.set_shader_parameter("prism", 1.0 if r == BH.Rarity.AETHER else 0.0)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = 0.025
	return mi

static func glint_material(rarity: int) -> ShaderMaterial:
	var r := clampi(rarity, 0, BH.RARITY_COUNT - 1)
	var mat := ShaderMaterial.new()
	mat.shader = _shader("glint", GLINT_SHADER)
	mat.set_shader_parameter("color", sparkle_color(r))
	mat.set_shader_parameter("strength", GLINT_STRENGTH[r])
	mat.set_shader_parameter("speed", 0.45 + 0.04 * r)
	return mat

## Apply the glint overlay to every mesh of a model.
static func add_glint(model: Node, rarity: int) -> void:
	var mat := glint_material(rarity)
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_overlay = mat
