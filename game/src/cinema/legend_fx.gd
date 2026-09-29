class_name LegendFX
## bh-021: the legends' effects for cutscenes (and Paul David's plate in Olivar):
##   wrath_aura    Aljay: blood-red flames and black smoke boiling up round him, a crimson ground ring, a flickering light
##   holy_aura     Roydo: golden motes rising, a soft shaft of light from above, warm light
##   storm_aura    Paul David: azure sparks crawling on a node (his blade), now and then a small arc of lightning
##   soulfire      Kethrax / the Legion: violet flames licking up from the body
##   ChainFX       a chain of iron links from A to B that shoots out (extend 0..1): violet Legion chains, cyan sealing chains
##   rain / lightning_strike / ground_ring / light_shaft   weather and staging
## Every node is self-contained (particles, lights, meshes); `power` scales an aura live.

static var _ring_shader: Shader
static var _shaft_shader: Shader
static var _flame_tex: Texture2D
static var _flame_mats := {}

## A flame tongue sprite (64 x 128, white, alpha-shaped): wide soft base, ragged pointed tip.
static func flame_texture() -> Texture2D:
	if _flame_tex:
		return _flame_tex
	var w := 64
	var h := 128
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var nz := FastNoiseLite.new()
	nz.seed = 21
	nz.frequency = 0.09
	for y in h:
		var v := 1.0 - float(y) / float(h - 1)          # 0 bottom .. 1 top
		var width := pow(sin(PI * minf(v * 1.6 + 0.12, 1.0)), 0.6) * pow(1.0 - v, 0.55)
		for x in w:
			var u := absf(float(x) / float(w - 1) * 2.0 - 1.0)
			var n := nz.get_noise_2d(x * 1.0, y * 0.6) * 0.5 + 0.5
			var a := clampf((width * (0.75 + 0.5 * n) - u) / maxf(width * 0.55, 0.02), 0.0, 1.0)
			a *= smoothstep(0.0, 0.12, v)
			img.set_pixel(x, y, Color(1, 1, 1, a * a))
	_flame_tex = ImageTexture.create_from_image(img)
	return _flame_tex

## Soft aura sprites that fade out as the camera comes close (cutscene close-ups look through the flames, not into
## a wall of them).
static var _aura_mats := {}

static func aura_material(additive := true) -> StandardMaterial3D:
	if _aura_mats.has(additive):
		return _aura_mats[additive]
	var m := (VFXLib.particle_material(additive) as StandardMaterial3D).duplicate() as StandardMaterial3D
	m.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_ALPHA
	m.distance_fade_min_distance = 0.6
	m.distance_fade_max_distance = 2.6
	_aura_mats[additive] = m
	return m

static func flame_material(additive := true) -> StandardMaterial3D:
	if _flame_mats.has(additive):
		return _flame_mats[additive]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if additive else BaseMaterial3D.BLEND_MODE_MIX
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = flame_texture()
	m.disable_receive_shadows = true
	_flame_mats[additive] = m
	return m

static func _flames(color: Color, dark: Color, amount: int, lifetime: float, box: Vector3, rise: float, size: float,
		additive := true) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = Perf.particles(amount)
	p.lifetime = lifetime
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	p.process_mode = Node.PROCESS_MODE_ALWAYS
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = box
	pm.emission_shape_offset = Vector3(0, box.y, 0)
	pm.direction = Vector3.UP
	pm.spread = 18.0
	pm.initial_velocity_min = rise * 0.4
	pm.initial_velocity_max = rise
	pm.gravity = Vector3(0, rise * 0.9, 0)
	pm.damping_min = 0.5
	pm.damping_max = 1.5
	pm.scale_min = size * 0.55
	pm.scale_max = size
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 1.4
	pm.turbulence_noise_scale = 2.2
	pm.turbulence_influence_min = 0.05
	pm.turbulence_influence_max = 0.18
	var g := Gradient.new()
	g.set_color(0, Color(color.r, color.g, color.b, 0.0))
	g.add_point(0.12, Color(color.r, color.g, color.b, color.a * (0.6 if additive else 1.0)))
	g.add_point(0.55, Color(dark.r, dark.g, dark.b, dark.a))
	g.set_color(g.get_point_count() - 1, Color(dark.r, dark.g, dark.b, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	var cv := Curve.new()
	cv.add_point(Vector2(0, 0.4))
	cv.add_point(Vector2(0.3, 1.0))
	cv.add_point(Vector2(1, 0.15))
	var ct := CurveTexture.new()
	ct.curve = cv
	pm.scale_curve = ct
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.16, 0.5) if additive else Vector2(0.5, 0.5)
	q.material = aura_material(additive)
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-4, -1, -4), Vector3(8, 8, 8))
	return p

static func _light(c: Color, energy: float, rng: float, y := 1.2) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = c
	l.light_energy = energy
	l.omni_range = rng
	l.position.y = y
	l.shadow_enabled = false
	return l

## Ground ring: a flat additive disc with a swirling noisy rim (the aura's footprint).
static func ground_ring(c: Color, radius: float) -> MeshInstance3D:
	if _ring_shader == null:
		_ring_shader = Shader.new()
		_ring_shader.code = """
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 col : source_color = vec4(1.0, 0.1, 0.05, 1.0);
uniform float power = 1.0;
float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float n(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
void fragment() {
	vec2 uv = UV * 2.0 - 1.0;
	float r = length(uv);
	float a = atan(uv.y, uv.x);
	float sw = n(vec2(a * 3.0 + TIME * 0.9, r * 4.0 - TIME * 1.3)) * 0.6 + n(vec2(a * 7.0 - TIME * 1.7, r * 9.0)) * 0.4;
	float rim = smoothstep(1.0, 0.72, r) * smoothstep(0.25, 0.8, r);
	float core = smoothstep(0.8, 0.0, r) * 0.25;
	float v = (rim * (0.35 + 0.9 * sw) + core) * power;
	ALBEDO = col.rgb * v * 2.0;
	ALPHA = clamp(v, 0.0, 1.0);
}
"""
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2.ONE * radius * 2.0
	q.orientation = PlaneMesh.FACE_Y
	mi.mesh = q
	var m := ShaderMaterial.new()
	m.shader = _ring_shader
	m.set_shader_parameter("col", c)
	mi.material_override = m
	mi.position.y = 0.03
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi

## A soft cone of light from high above (god ray) standing on the node.
static func light_shaft(c: Color, height: float, top_r: float, bottom_r: float) -> MeshInstance3D:
	if _shaft_shader == null:
		_shaft_shader = Shader.new()
		_shaft_shader.code = """
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 col : source_color = vec4(1.0, 0.85, 0.5, 1.0);
uniform float power = 1.0;
void fragment() {
	float edge = pow(1.0 - abs(dot(NORMAL, normalize(VIEW))), 1.5);
	float fall = smoothstep(0.0, 0.25, UV.y) * smoothstep(1.0, 0.55, UV.y);
	float streak = 0.75 + 0.25 * sin(UV.x * 40.0 + TIME * 0.7) * sin(UV.x * 17.0 - TIME * 0.4);
	float v = (1.0 - edge) * fall * streak * 0.16 * power;
	ALBEDO = col.rgb * v;
	ALPHA = clamp(v, 0.0, 1.0);
}
"""
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = top_r
	cm.bottom_radius = bottom_r
	cm.height = height
	cm.cap_top = false
	cm.cap_bottom = false
	cm.radial_segments = 32
	mi.mesh = cm
	mi.position.y = height * 0.5
	var m := ShaderMaterial.new()
	m.shader = _shaft_shader
	m.set_shader_parameter("col", c)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi

## Aljay's wrath: flames, smoke, ring and light. power 0..2.
static func wrath_aura(power := 1.0) -> Aura:
	var a := Aura.new()
	a.name = "WrathAura"
	a.add_part(_flames(Color(1.0, 0.12, 0.04, 0.7), Color(0.35, 0.0, 0.0, 0.5), 140, 0.85, Vector3(0.4, 0.95, 0.34), 1.9, 0.36), 1.0)
	a.add_part(_flames(Color(0.08, 0.0, 0.0, 0.4), Color(0.0, 0.0, 0.0, 0.3), 36, 1.7, Vector3(0.5, 0.9, 0.45), 1.0, 0.8, false), 0.95)
	a.add_part(_flames(Color(1.0, 0.5, 0.25, 1.0), Color(1.0, 0.05, 0.02, 0.8), 60, 0.5, Vector3(0.3, 0.8, 0.25), 3.2, 0.1), 1.05)
	a.ring = ground_ring(Color(1.0, 0.08, 0.03), 1.8)
	a.add_child(a.ring)
	a.light = _light(Color(1.0, 0.15, 0.06), 2.6, 7.0)
	a.add_child(a.light)
	a.flicker = 0.35
	a.set_power(power)
	return a

## Roydo's holy light: golden motes, a shaft from the sky, warm light, a bright ring.
static func holy_aura(power := 1.0, shaft := true) -> Aura:
	var a := Aura.new()
	a.name = "HolyAura"
	a.add_part(_flames(Color(1.0, 0.85, 0.45, 0.9), Color(1.0, 0.6, 0.2, 0.5), 60, 1.6, Vector3(0.5, 1.0, 0.45), 0.8, 0.09), 1.0)
	a.add_part(_flames(Color(1.0, 0.85, 0.5, 0.3), Color(1.0, 0.7, 0.3, 0.1), 30, 1.2, Vector3(0.45, 0.9, 0.4), 1.2, 0.22), 1.0)
	a.ring = ground_ring(Color(1.0, 0.75, 0.3), 2.0)
	a.add_child(a.ring)
	if shaft:
		a.shaft = light_shaft(Color(1.0, 0.85, 0.55), 18.0, 0.5, 1.2)
		a.add_child(a.shaft)
	a.light = _light(Color(1.0, 0.82, 0.5), 2.2, 8.0, 1.6)
	a.add_child(a.light)
	a.flicker = 0.08
	a.set_power(power)
	return a

## Violet soulfire (Kethrax, the Legion).
static func soulfire(power := 1.0) -> Aura:
	var a := Aura.new()
	a.name = "Soulfire"
	a.add_part(_flames(Color(0.6, 0.3, 1.0, 0.65), Color(0.2, 0.05, 0.4, 0.45), 60, 1.0, Vector3(0.42, 0.9, 0.36), 1.2, 0.3), 1.0)
	a.add_part(_flames(Color(0.05, 0.0, 0.08, 0.5), Color(0.0, 0.0, 0.0, 0.4), 30, 1.6, Vector3(0.45, 0.9, 0.4), 0.8, 0.9, false), 1.0)
	a.light = _light(Color(0.6, 0.3, 1.0), 1.8, 6.0)
	a.add_child(a.light)
	a.flicker = 0.25
	a.set_power(power)
	return a

## Paul David's storm: azure sparks on a node (the blade), a small lightning arc now and then.
static func storm_aura(power := 1.0) -> Aura:
	var a := Aura.new()
	a.name = "StormAura"
	a.light = _light(Color(0.4, 0.75, 1.0), 1.4, 4.0, 0.4)
	a.add_child(a.light)
	a.flicker = 0.5
	a.arcs = 1.6
	a.arc_color = Color(0.6, 0.85, 1.0)
	a.set_power(power)
	return a

## A falling-rain box that follows its parent (put it on the camera rig).
static func rain(amount := 900, box := Vector3(14, 10, 14)) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = Perf.particles(amount)
	p.lifetime = 0.9
	p.local_coords = false
	p.process_mode = Node.PROCESS_MODE_ALWAYS
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = box * 0.5
	pm.direction = Vector3(0.12, -1, 0.05)
	pm.spread = 3.0
	pm.initial_velocity_min = 16.0
	pm.initial_velocity_max = 20.0
	pm.gravity = Vector3(0, -6, 0)
	pm.particle_flag_align_y = true
	pm.color = Color(0.6, 0.66, 0.78, 0.35)
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.018, 0.75)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.billboard_keep_scale = true
	m.vertex_color_use_as_albedo = true
	q.material = m
	p.draw_pass_1 = q
	p.position.y = box.y * 0.35
	p.visibility_aabb = AABB(-box, box * 2.0)
	return p

## A bolt from the sky onto `at` (world) with a flash light; add to the stage.
static func lightning_strike(parent: Node3D, at: Vector3, c := Color(0.8, 0.85, 1.0)) -> void:
	var top := at + Vector3(randf_range(-4, 4), 28.0, randf_range(-4, 4))
	var b := VFXLib.lightning_bolt(top, at, c, 0.28, 0.25)
	b.process_mode = Node.PROCESS_MODE_ALWAYS
	parent.add_child(b)
	var l := OmniLight3D.new()
	l.light_color = c
	l.light_energy = 9.0
	l.omni_range = 40.0
	l.process_mode = Node.PROCESS_MODE_ALWAYS
	parent.add_child(l)
	l.global_position = at + Vector3(0, 6, 0)
	var tw := l.create_tween()
	tw.tween_property(l, "light_energy", 0.0, 0.35)
	tw.tween_callback(l.queue_free)


## A short crackling arc of lightning between two nearby points (jitter scaled to its length).
static func arc(from: Vector3, to: Vector3, c: Color, duration := 0.12, width := 0.012) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var L := from.distance_to(to)
	var segs := 6
	var dir := to - from
	var side := dir.cross(Vector3.UP).normalized()
	if side.length_squared() < 0.01:
		side = Vector3.RIGHT
	var up2 := dir.cross(side).normalized()
	var pts: Array[Vector3] = [from]
	for i in range(1, segs):
		pts.append(from + dir * (float(i) / segs) + (side * randf_range(-1, 1) + up2 * randf_range(-1, 1)) * L * 0.12)
	pts.append(to)
	for i in pts.size() - 1:
		var a := pts[i]
		var b := pts[i + 1]
		for off in [side * width, up2 * width]:
			for v in [a - off, a + off, b + off, a - off, b + off, b - off]:
				st.set_normal(Vector3.UP)
				st.add_vertex(v)
	var mi := MeshInstance3D.new()
	mi.top_level = true
	mi.mesh = st.commit()
	var mat := VFXLib.glow_material(c, 2.5)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.process_mode = Node.PROCESS_MODE_ALWAYS
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("alpha", v), 1.0, 0.0, duration)
	tw.tween_callback(mi.queue_free)
	return mi


## An aura: a bundle of particle systems + a light + an optional ground ring / shaft, scaled by `power`.
class Aura extends Node3D:
	var parts: Array = []           # [GPUParticles3D, base amount_ratio]
	var light: OmniLight3D
	var ring: MeshInstance3D
	var shaft: MeshInstance3D
	var power := 1.0
	var flicker := 0.2
	var arcs := 0.0
	var arc_color := Color.WHITE
	var _base_energy := 1.0
	var _t := 0.0
	var _arc_t := 0.5

	func _init() -> void:
		process_mode = Node.PROCESS_MODE_ALWAYS

	func add_part(p: GPUParticles3D, ratio: float) -> void:
		parts.append([p, ratio])
		add_child(p)

	func set_power(v: float) -> void:
		power = maxf(0.0, v)
		for pr in parts:
			var p: GPUParticles3D = pr[0]
			p.amount_ratio = clampf(power * float(pr[1]), 0.0, 1.0)
			p.emitting = power > 0.01
			p.speed_scale = 0.7 + 0.3 * minf(power, 2.0)
			p.scale = Vector3.ONE * (0.8 + 0.2 * minf(power, 2.0))
		if light:
			if _base_energy == 1.0:
				_base_energy = light.light_energy
			light.visible = power > 0.01
		for m in [ring, shaft]:
			if m and m.material_override is ShaderMaterial:
				(m.material_override as ShaderMaterial).set_shader_parameter("power", power)
				m.visible = power > 0.01

	## Tween the power over `sec` seconds.
	func fade_to(v: float, sec := 1.0) -> void:
		var tw := create_tween()
		tw.tween_method(set_power, power, v, sec)

	func _process(delta: float) -> void:
		_t += delta
		if light and power > 0.01:
			var f := 1.0 + flicker * (sin(_t * 17.0) * 0.5 + sin(_t * 7.3 + 1.0) * 0.5)
			light.light_energy = _base_energy * power * f
		if arcs > 0.0 and power > 0.2:
			_arc_t -= delta
			if _arc_t <= 0.0:
				_arc_t = randf_range(0.15, 0.6) / arcs
				var a := global_position + Vector3(randf_range(-0.15, 0.15), randf_range(-0.4, 0.4), randf_range(-0.15, 0.15))
				var b := a + Vector3(randf_range(-0.25, 0.25), randf_range(-0.3, 0.3), randf_range(-0.25, 0.25))
				var bolt := LegendFX.arc(a, b, arc_color)
				get_parent().add_child(bolt)


## A chain of links shot from a start point toward an end point. extend 0..1 (tween it); both ends in world space.
class ChainFX extends Node3D:
	var from := Vector3.ZERO
	var to := Vector3.ZERO
	var extend := 0.0
	var sag := 0.25
	var link := 0.11
	var from_node: Node3D
	var to_node: Node3D
	var _mm: MultiMeshInstance3D
	var _glow: StandardMaterial3D

	func _init(glow := Color(0.6, 0.3, 1.0), thick := 0.022) -> void:
		process_mode = Node.PROCESS_MODE_ALWAYS
		top_level = true
		_mm = MultiMeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = link * 0.32
		tm.outer_radius = link * 0.32 + thick
		tm.rings = 12
		tm.ring_segments = 6
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.12, 0.11, 0.13)
		m.metallic = 0.85
		m.roughness = 0.45
		m.emission_enabled = true
		m.emission = glow
		m.emission_energy_multiplier = 1.6
		m.rim_enabled = true
		m.rim = 0.4
		_glow = m
		tm.material = m
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = tm
		mm.instance_count = 160
		mm.visible_instance_count = 0
		_mm.multimesh = mm
		_mm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_mm)

	func set_glow(e: float) -> void:
		_glow.emission_energy_multiplier = e

	func _process(_d: float) -> void:
		var a := from_node.global_position if from_node and is_instance_valid(from_node) else from
		var b := to_node.global_position if to_node and is_instance_valid(to_node) else to
		var end := a.lerp(b, clampf(extend, 0.0, 1.0))
		var length := a.distance_to(end)
		var n := mini(160, int(length / (link * 0.62)))
		var mm := _mm.multimesh
		mm.visible_instance_count = n
		if n <= 0:
			return
		var prev := a
		for i in n:
			var t := (i + 0.5) / float(n)
			var p := a.lerp(end, t) + Vector3.DOWN * sag * 4.0 * t * (1.0 - t) * extend
			var d := (p - prev).normalized() if i > 0 else (end - a).normalized()
			if d.length_squared() < 0.001:
				d = Vector3.FORWARD
			var up := Vector3.UP if absf(d.dot(Vector3.UP)) < 0.95 else Vector3.RIGHT
			var x := d.cross(up).normalized()
			var basis := Basis(x, d, x.cross(d)) if i % 2 == 0 else Basis(x.cross(d), d, -x)
			# a torus lies in its local XZ plane: stand it along the chain (local Y -> chain direction)
			mm.set_instance_transform(i, Transform3D(Basis(basis.x, basis.z, -basis.y * 1.45), p))
			prev = p
