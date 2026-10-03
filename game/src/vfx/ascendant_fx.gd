class_name AscendantFx
## bh-034: the moving light of the Ascendant tiers (DataAscendant), on the ground and on whoever wears them.
##   Cosmic      a drifting nebula inside the metal with twinkling stars; star motes; a ring of turning stars
##   Divine      a radiant sweep up the surface and a golden rim; rising golden motes; a sunburst of rays
##   Eternal     slow ripples of time over pearl and rose-gold; motes that spiral; a clock dial whose hands turn
##   Primordial  molten cracks that pulse in the obsidian; rising embers; cracked ground glowing like a forge
## overlay(): the surface shader, laid as a next pass on a piece's own materials (dress()). aura(): particles for a
## worn piece or a held weapon. sigil() and pillar(): the ground presentation of a dropped piece (LootDrop).

const OVERLAY_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, depth_draw_never, shadows_disabled, fog_disabled, cull_back;
uniform int mode = 0;
uniform vec4 c1 : source_color = vec4(1.0);
uniform vec4 c2 : source_color = vec4(1.0);
uniform float strength = 1.0;
uniform float scale = 9.0;
varying vec3 opos;
float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}
float noise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
void vertex() {
	opos = VERTEX;
}
void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.5);
	vec3 p = opos * scale;
	vec3 col = vec3(0.0);
	if (mode == 0) {
		// Cosmic: nebula drifting through the metal, stars that twinkle in it
		float n = noise(p * 0.6 + vec3(0.0, TIME * 0.15, TIME * 0.1));
		float n2 = noise(p * 1.3 - vec3(TIME * 0.2, 0.0, 0.0));
		vec3 neb = mix(c1.rgb, c2.rgb, n2) * smoothstep(0.55, 0.95, n) * 0.22;
		vec3 cell = floor(p * 3.0);
		float h = hash(cell);
		float tw = step(0.955, h) * (0.5 + 0.5 * sin(TIME * 3.0 + h * 40.0));
		float d = length(fract(p * 3.0) - 0.5);
		col = neb + vec3(tw * smoothstep(0.28, 0.0, d)) * 1.8 + c1.rgb * fres * 0.25;
	} else if (mode == 1) {
		// Divine: a band of light sweeping up the piece, a warm rim
		float band = fract(opos.y * 1.6 - TIME * 0.35);
		float sweep = smoothstep(0.0, 0.05, band) * smoothstep(0.16, 0.05, band);
		col = c1.rgb * (fres * 0.35 + sweep * 0.8);
	} else if (mode == 2) {
		// Eternal: slow ripples of time rising through the surface
		float r = length(opos.xz) * 12.0 + opos.y * 16.0 - TIME * 1.6;
		float ring = pow(0.5 + 0.5 * sin(r), 28.0) * 0.6;
		col = c1.rgb * (ring * 0.55 + fres * 0.25) + c2.rgb * ring * 0.2;
	} else {
		// Primordial: molten cracks breathing in the obsidian
		float n = noise(p * 1.1 + vec3(0.0, -TIME * 0.25, 0.0));
		float cracks = 1.0 - smoothstep(0.0, 0.03, abs(n - 0.5));
		float pulse = 0.65 + 0.35 * sin(TIME * 2.2 + n * 6.0);
		col = mix(c2.rgb, c1.rgb, n) * cracks * pulse * 1.2 + c1.rgb * fres * 0.12;
	}
	ALBEDO = col * strength;
}
"""

const SIGIL_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled, fog_disabled;
uniform int mode = 0;
uniform vec4 c1 : source_color = vec4(1.0);
uniform vec4 c2 : source_color = vec4(1.0);
uniform float strength = 1.0;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float a = atan(p.y, p.x);
	float fade = smoothstep(1.0, 0.82, r);
	float ring = exp(-pow((r - 0.86) * 28.0, 2.0)) + exp(-pow((r - 0.62) * 40.0, 2.0)) * 0.6;
	vec3 col = c1.rgb * ring;
	if (mode == 0) {
		// a ring of stars turning, a faint nebula in the middle
		float k = 12.0;
		float ang = fract((a + TIME * 0.35) / TAU * k);
		float star = smoothstep(0.18, 0.0, length(vec2((ang - 0.5) * 0.42, r - 0.74)));
		col += c2.rgb * star * 2.2 + c1.rgb * smoothstep(0.6, 0.0, r) * 0.25;
	} else if (mode == 1) {
		// a sunburst: rays turning slowly, a bright disc
		float rays = pow(0.5 + 0.5 * cos(a * 16.0 - TIME * 0.6), 6.0) * smoothstep(0.95, 0.2, r);
		col += c1.rgb * rays * 1.1 + c2.rgb * smoothstep(0.35, 0.0, r) * 0.6;
	} else if (mode == 2) {
		// a clock dial: twelve marks and two hands at their own speeds
		float marks = step(0.92, fract(a / TAU * 12.0 + 0.04)) * step(0.66, r) * step(r, 0.8);
		float h1 = smoothstep(0.03, 0.0, abs(sin(a - TIME * 0.5))) * step(r, 0.58) * step(0.0, cos(a - TIME * 0.5));
		float h2 = smoothstep(0.02, 0.0, abs(sin(a - TIME * 2.0))) * step(r, 0.74) * step(0.0, cos(a - TIME * 2.0));
		col += c2.rgb * (marks * 1.6 + h1 * 1.4 + h2 * 1.1) + c1.rgb * smoothstep(0.5, 0.0, r) * 0.2;
	} else {
		// cracked ground glowing like a forge
		vec2 g = p * 5.0;
		vec2 cell = floor(g);
		float best = 9.0;
		float second = 9.0;
		for (int y = -1; y <= 1; y++) {
			for (int x = -1; x <= 1; x++) {
				vec2 c = cell + vec2(float(x), float(y));
				vec2 o = vec2(hash(c), hash(c + 7.1));
				float d = length(g - c - o);
				if (d < best) { second = best; best = d; } else if (d < second) { second = d; }
			}
		}
		float crack = smoothstep(0.12, 0.0, second - best);
		float pulse = 0.7 + 0.3 * sin(TIME * 2.0 + r * 6.0);
		col += mix(c2.rgb, c1.rgb, crack) * crack * pulse * 1.6 * smoothstep(1.0, 0.1, r);
	}
	ALBEDO = col * fade * strength;
}
"""

## Per tier: mode, main colour, second colour.
const LOOK := {
	BH.Rarity.COSMIC: [0, Color(0.58, 0.5, 1.0), Color(0.75, 0.88, 1.0)],
	BH.Rarity.DIVINE: [1, Color(1.0, 0.86, 0.5), Color(1.0, 0.98, 0.85)],
	BH.Rarity.ETERNAL: [2, Color(1.0, 0.55, 0.78), Color(0.65, 1.0, 0.92)],
	BH.Rarity.PRIMORDIAL: [3, Color(1.0, 0.32, 0.08), Color(0.55, 0.05, 0.02)],
}

static var _shaders := {}
static var _overlays := {}
static var _dressed := {}

static func has_look(rarity: int) -> bool:
	return LOOK.has(rarity)

static func color(rarity: int) -> Color:
	return LOOK[rarity][1] if LOOK.has(rarity) else BH.rarity_color(rarity)

static func _shader(key: String, code: String) -> Shader:
	if not _shaders.has(key):
		var sh := Shader.new()
		sh.code = code
		_shaders[key] = sh
	return _shaders[key]

## The tier's surface shader (shared per tier and strength).
static func overlay(rarity: int, strength := 1.0) -> ShaderMaterial:
	var key := "%d/%.2f" % [rarity, strength]
	if not _overlays.has(key):
		var m := ShaderMaterial.new()
		m.shader = _shader("overlay", OVERLAY_SHADER)
		var look: Array = LOOK.get(rarity, LOOK[BH.Rarity.COSMIC])
		m.set_shader_parameter("mode", int(look[0]))
		m.set_shader_parameter("c1", look[1])
		m.set_shader_parameter("c2", look[2])
		m.set_shader_parameter("strength", strength)
		_overlays[key] = m
	return _overlays[key]

## Lay the tier's surface light over every mesh of `node` as a next pass of the mesh's own materials (the material
## overlay stays free for the hit flash and rim light of CharacterVisual).
static func dress(node: Node, rarity: int, strength := 0.6) -> void:
	if not LOOK.has(rarity) or node == null:
		return
	var ov := overlay(rarity, strength)
	var meshes: Array = node.find_children("*", "MeshInstance3D", true, false)
	if node is MeshInstance3D:
		meshes.append(node)
	for mi: MeshInstance3D in meshes:
		if mi.mesh == null:
			continue
		if mi.material_override:
			mi.material_override = _with_pass(mi.material_override, ov)
			continue
		for i in mi.mesh.get_surface_count():
			var m := mi.get_active_material(i)
			if m:
				mi.set_surface_override_material(i, _with_pass(m, ov))

static func _with_pass(m: Material, ov: Material) -> Material:
	if m == ov or m.next_pass == ov:
		return m
	var key := "%d/%d" % [m.get_instance_id(), ov.get_instance_id()]
	if not _dressed.has(key):
		var d := m.duplicate() as Material
		if d.next_pass == null:
			d.next_pass = ov
		_dressed[key] = d
		if _dressed.size() > 600:
			_dressed.clear()
	return _dressed[key]

## Particles around a worn piece or along a held weapon. `size`: the piece's radius (m); `length`: a weapon's reach
## along +Y (0 = a worn piece: a sphere of motes around it).
static func aura(rarity: int, size := 0.25, length := 0.0) -> Node3D:
	var root := Node3D.new()
	root.name = "AscendantAura"
	if not LOOK.has(rarity):
		return root
	var look: Array = LOOK[rarity]
	var c1: Color = look[1]
	var c2: Color = look[2]
	var mode := int(look[0])
	var amount := 7 if length <= 0.0 else 10
	var p: GPUParticles3D
	match mode:
		0:
			p = LootFx.small_particles(Color(c2, 0.95), amount, 1.6, 0.05, 0.12, 180.0, Vector3.ZERO, size)
		1:
			p = LootFx.small_particles(Color(c1, 0.9), amount, 1.4, 0.06, 0.25, 20.0, Vector3(0, 0.6, 0), size)
		2:
			p = LootFx.small_particles(Color(c1, 0.85), amount, 2.0, 0.05, 0.1, 180.0, Vector3(0, 0.15, 0), size)
			var spin := MoteSpinner.new()
			spin.speed = 1.4
			root.add_child(spin)
			spin.add_child(p)
		_:
			p = LootFx.small_particles(Color(c1, 0.95), amount + 2, 1.0, 0.045, 0.35, 25.0, Vector3(0, 1.4, 0), size)
	p.local_coords = mode == 2
	if length > 0.0:
		var pm := p.process_material as ParticleProcessMaterial
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
		pm.emission_box_extents = Vector3(0.03, length * 0.5, 0.03)
		p.position = Vector3(0, length * 0.55, 0)
	if p.get_parent() == null:
		root.add_child(p)
	return root

## The ground presentation of a dropped piece: a flat animated sigil of `radius` m.
static func sigil(rarity: int, radius: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = "AscendantSigil"
	var pm := PlaneMesh.new()
	pm.size = Vector2.ONE * radius * 2.0
	mi.mesh = pm
	var mat := ShaderMaterial.new()
	mat.shader = _shader("sigil", SIGIL_SHADER)
	var look: Array = LOOK.get(rarity, LOOK[BH.Rarity.COSMIC])
	mat.set_shader_parameter("mode", int(look[0]))
	mat.set_shader_parameter("c1", look[1])
	mat.set_shader_parameter("c2", look[2])
	mat.set_shader_parameter("strength", 0.9)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = 0.06
	# drawn over uneven ground instead of half buried in it (it is light, not a surface)
	mat.render_priority = -10
	return mi

## A soft column of the tier's light over a dropped piece, visible from across the map, with the tier's motes rising
## inside it.
static func pillar(rarity: int, height := 9.0) -> Node3D:
	var root := Node3D.new()
	root.name = "AscendantPillar"
	var c := color(rarity)
	var beam := VFXLib.beam(c, height, 0.2)
	(beam.material_override as ShaderMaterial).set_shader_parameter("alpha", 0.12)
	root.add_child(beam)
	var inner := VFXLib.beam(LOOK[rarity][2] if LOOK.has(rarity) else c, height * 0.85, 0.07)
	(inner.material_override as ShaderMaterial).set_shader_parameter("alpha", 0.18)
	root.add_child(inner)
	var motes := LootFx.small_particles(Color(c, 0.9), 18, 2.6, 0.07, 1.6, 8.0, Vector3(0, 1.2, 0), 0.25)
	motes.preprocess = 2.0
	root.add_child(motes)
	return root

## Turns its children round Y (the Eternal motes' spiral).
class MoteSpinner extends Node3D:
	var speed := 1.0
	func _process(delta: float) -> void:
		rotate_y(speed * delta)
