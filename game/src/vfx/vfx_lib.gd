class_name VFXLib
## Procedural visual effects: particles, arcs, rings, telegraphs, projectile bodies. All effects are readable,
## short-lived and budgeted (particle counts are small; lights are few and fade quickly).

static var _soft_tex: Texture2D
static var _spark_mat_cache := {}
static var _add_shader: Shader
static var _arc_shader: Shader
static var _ring_shader: Shader
static var _tele_shader: Shader

static func soft_texture() -> Texture2D:
	if _soft_tex:
		return _soft_tex
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.35, Color(1, 1, 1, 0.55))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 64
	t.height = 64
	_soft_tex = t
	return t

static func particle_material(additive := true) -> StandardMaterial3D:
	var key := additive
	if _spark_mat_cache.has(key):
		return _spark_mat_cache[key]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if additive else BaseMaterial3D.BLEND_MODE_MIX
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = soft_texture()
	m.disable_receive_shadows = true
	_spark_mat_cache[key] = m
	return m

static func _ramp(c: Color, fade_to := Color(0, 0, 0, 0)) -> GradientTexture1D:
	var g := Gradient.new()
	g.set_color(0, c)
	g.set_color(1, fade_to)
	g.add_point(0.15, Color(c.r * 1.3, c.g * 1.3, c.b * 1.3, c.a))
	var t := GradientTexture1D.new()
	t.gradient = g
	return t

## Generic particle system builder.
static func particles(color: Color, amount: int, lifetime: float, one_shot: bool, size: float, velocity: float,
		spread := 180.0, gravity := Vector3.ZERO, emission_radius := 0.0, additive := true) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = Perf.particles(amount)
	p.lifetime = lifetime
	p.one_shot = one_shot
	p.explosiveness = 0.9 if one_shot else 0.0
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if one_shot:
		# bh-037: a one-shot burst shares its material and quad with every identical burst (see shared())
		var key := "pp|%s|%.2f|%.2f|%.0f|%s|%.2f" % [color.to_html(), snappedf(size, 0.01), snappedf(velocity, 0.25), spread, gravity, emission_radius]
		p.process_material = shared(key, func() -> Resource: return _particle_pm(color, size, velocity, spread, gravity, emission_radius))
		p.draw_pass_1 = shared("quad|%s" % additive, func() -> Resource:
			var sq := QuadMesh.new()
			sq.size = Vector2.ONE * 0.5
			sq.material = particle_material(additive)
			return sq)
	else:
		p.process_material = _particle_pm(color, size, velocity, spread, gravity, emission_radius)
		var q := QuadMesh.new()
		q.size = Vector2.ONE * 0.5
		q.material = particle_material(additive)
		p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-6, -2, -6), Vector3(12, 10, 12))
	if one_shot:
		p.emitting = true
		p.finished.connect(p.queue_free)
		_autofree(p, lifetime + 0.5)       # bh-037: `finished` never fires here in Godot 4.7 (see _autofree)
	return p

static func _particle_pm(color: Color, size: float, velocity: float, spread: float, gravity: Vector3, emission_radius: float) -> ParticleProcessMaterial:
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3.UP
	pm.spread = spread
	pm.initial_velocity_min = velocity * 0.5
	pm.initial_velocity_max = velocity
	pm.gravity = gravity
	pm.damping_min = 1.0
	pm.damping_max = 3.0
	pm.scale_min = size * 0.6
	pm.scale_max = size
	pm.color_ramp = _ramp(color)
	var curve := CurveTexture.new()
	var cv := Curve.new()
	cv.add_point(Vector2(0, 1))
	cv.add_point(Vector2(1, 0.1))
	curve.curve = cv
	pm.scale_curve = curve
	if emission_radius > 0.0:
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		pm.emission_sphere_radius = emission_radius
	return pm

## bh-037: resources one-shot effects share. Every blow used to build each burst's ParticleProcessMaterial, colour-ramp and
## curve textures, quad (and for sparks a SurfaceTool mesh) from scratch: ~0.7 ms of building per hit plus ~0.6 ms of render
## setup the next frame, so a party's volley of 20 hits stalled a frame by ~25 ms. Identical bursts now share them (sizes
## and speeds keyed to a few significant digits, directions to 16 compass steps). Never mutate a material from here: callers
## that tweak one duplicate it first. Bounded: the cache is dropped and rebuilt past SHARED_MAX entries.
const SHARED_MAX := 768
static var _shared := {}

static func shared(key: String, build: Callable) -> Resource:
	var r: Resource = _shared.get(key)
	if r == null:
		if _shared.size() >= SHARED_MAX:
			_shared.clear()
		r = build.call()
		_shared[key] = r
	return r

## A direction rounded for shared() keys: 16 steps around, 9 of height.
static func qdir(d: Vector3) -> Vector3:
	if d.length() < 0.01:
		return Vector3.UP
	d = d.normalized()
	var yaw := snappedf(atan2(d.x, d.z), TAU / 16.0)
	var pitch := snappedf(asin(clampf(d.y, -1.0, 1.0)), PI / 8.0)
	return Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))

static func status_particles(element: int, height: float) -> GPUParticles3D:
	var c := Elements.color(element)
	var p: GPUParticles3D
	match element:
		Elements.FIRE: p = particles(Color(1.0, 0.55, 0.15, 0.9), 18, 0.7, false, 0.5, 1.6, 20.0, Vector3(0, 2.5, 0), height * 0.25)
		Elements.LIGHTNING: p = particles(Color(1.0, 0.95, 0.5, 1.0), 10, 0.18, false, 0.25, 4.0, 180.0, Vector3.ZERO, height * 0.3)
		Elements.DARK: p = particles(Color(0.5, 0.15, 0.8, 0.7), 12, 1.2, false, 0.6, 0.6, 60.0, Vector3(0, 0.8, 0), height * 0.3)
		Elements.ICE: p = particles(Color(0.7, 0.92, 1.0, 0.6), 8, 1.0, false, 0.25, 0.4, 180.0, Vector3(0, -0.5, 0), height * 0.3)
		Elements.WATER: p = particles(Color(0.3, 0.55, 1.0, 0.7), 8, 0.6, false, 0.18, 0.3, 30.0, Vector3(0, -6.0, 0), height * 0.25)
		_: p = particles(Color(0.7, 0.05, 0.05, 0.9), 8, 0.5, false, 0.2, 0.5, 30.0, Vector3(0, -6.0, 0), height * 0.2)
	p.position.y = height * 0.5
	return p

static func ice_block(h: float, s: float) -> Node3D:
	var mi := MeshInstance3D.new()
	var m := CylinderMesh.new()
	m.top_radius = 0.45 * s
	m.bottom_radius = 0.55 * s
	m.height = h * 1.05
	m.radial_segments = 7
	m.rings = 1
	mi.mesh = m
	mi.position.y = h * 0.5
	# bh-037: one shared material (FX.warm_up builds its shader): a fresh one per freeze rebuilt the shader, ~30 ms + ~30 ms
	mi.material_override = shared("ice_block", func() -> Resource:
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.65, 0.88, 1.0, 0.35)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.roughness = 0.05
		mat.metallic_specular = 1.0
		mat.rim_enabled = true
		mat.rim = 1.0
		mat.emission_enabled = true
		mat.emission = Color(0.3, 0.6, 0.9)
		mat.emission_energy_multiplier = 0.4
		return mat)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi

static func stun_stars(h: float) -> Node3D:
	var root := Node3D.new()
	root.position.y = h + 0.25
	for i in 3:
		var s := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		s.mesh = sm
		s.material_override = shared("stun_star", func() -> Resource:      # bh-037: shared (see ice_block)
			var mat := StandardMaterial3D.new()
			mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			mat.albedo_color = Color(1.0, 0.9, 0.4)
			return mat)
		var a := TAU * i / 3.0
		s.position = Vector3(cos(a), 0, sin(a)) * 0.35
		root.add_child(s)
	var tw := root.create_tween().set_loops()
	tw.tween_property(root, "rotation:y", TAU, 0.9).from(0.0)
	return root

static func add_shader() -> Shader:
	if _add_shader:
		return _add_shader
	_add_shader = Shader.new()
	_add_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(1.0);
uniform float energy = 2.0;
uniform float alpha = 1.0;
void fragment() {
	float fres = pow(clamp(dot(NORMAL, VIEW), 0.0, 1.0), 1.5);
	ALBEDO = color.rgb * energy * (0.4 + 0.6 * fres);
	ALPHA = alpha * color.a;
}
"""
	return _add_shader

static func glow_material(c: Color, energy := 2.0) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = add_shader()
	m.set_shader_parameter("color", c)
	m.set_shader_parameter("energy", energy)
	return m

## Swept weapon arc: a flat ring segment that sweeps and fades. Readable at isometric distance.
static func slash_arc(c: Color, radius: float, arc_deg: float, height := 1.1, duration := 0.22, thickness := 0.55, clockwise := true) -> MeshInstance3D:
	if _arc_shader == null:
		_arc_shader = Shader.new()
		_arc_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(1.0);
uniform float progress = 0.0;
uniform float energy = 3.0;
void fragment() {
	float along = UV.x;               // 0..1 along the arc
	float across = UV.y;              // 0 inner .. 1 outer
	float head = progress;
	float tail = progress - 0.55;
	float a = smoothstep(tail, head, along) * (1.0 - smoothstep(head, head + 0.05, along));
	a *= smoothstep(0.0, 0.35, across) * (1.0 - smoothstep(0.85, 1.0, across));
	float edge = smoothstep(0.6, 1.0, across);
	ALBEDO = mix(color.rgb, vec3(1.0), edge * 0.6) * energy;
	ALPHA = a * color.a * (1.0 - progress * 0.5);
}
"""
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var segs := 24
	var a0 := -deg_to_rad(arc_deg) * 0.5
	var a1 := deg_to_rad(arc_deg) * 0.5
	for i in segs:
		var t0 := float(i) / segs
		var t1 := float(i + 1) / segs
		var ang0 := lerpf(a0, a1, t0) if clockwise else lerpf(a1, a0, t0)
		var ang1 := lerpf(a0, a1, t1) if clockwise else lerpf(a1, a0, t1)
		var ri := radius * (1.0 - thickness)
		var p0i := Vector3(sin(ang0) * ri, 0, cos(ang0) * ri)
		var p0o := Vector3(sin(ang0) * radius, 0, cos(ang0) * radius)
		var p1i := Vector3(sin(ang1) * ri, 0, cos(ang1) * ri)
		var p1o := Vector3(sin(ang1) * radius, 0, cos(ang1) * radius)
		for v in [[p0i, Vector2(t0, 0)], [p0o, Vector2(t0, 1)], [p1o, Vector2(t1, 1)], [p0i, Vector2(t0, 0)], [p1o, Vector2(t1, 1)], [p1i, Vector2(t1, 0)]]:
			st.set_uv(v[1])
			st.set_normal(Vector3.UP)
			st.add_vertex(v[0])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = _arc_shader
	mat.set_shader_parameter("color", c)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = height
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("progress", v), 0.0, 1.5, duration)
	tw.tween_callback(mi.queue_free)
	return mi

## Expanding shockwave ring on the ground.
static func ring_wave(c: Color, radius: float, duration := 0.45, width := 0.35) -> MeshInstance3D:
	if _ring_shader == null:
		_ring_shader = Shader.new()
		_ring_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(1.0);
uniform float progress = 0.0;
uniform float width = 0.1;
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = length(p);
	float r = progress;
	float ring = smoothstep(r - width, r, d) * (1.0 - smoothstep(r, r + 0.02, d));
	float fill = (1.0 - smoothstep(0.0, r, d)) * 0.12;
	ALBEDO = color.rgb * 3.0;
	ALPHA = (ring + fill) * color.a * (1.0 - progress);
}
"""
	var mi := MeshInstance3D.new()
	var q := PlaneMesh.new()
	q.size = Vector2.ONE * radius * 2.0
	mi.mesh = q
	var mat := ShaderMaterial.new()
	mat.shader = _ring_shader
	mat.set_shader_parameter("color", c)
	mat.set_shader_parameter("width", clampf(width / radius, 0.03, 0.5))
	mi.material_override = mat
	mi.position.y = 0.06
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("progress", v), 0.05, 1.0, duration).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_callback(mi.queue_free)
	return mi

## Enemy/boss attack telegraph on the ground: fills up over `windup` seconds. shape: circle, ring, cone, line.
static func telegraph(shape: String, size: Vector2, windup: float, c := Color(1.0, 0.25, 0.1, 0.8), arc_deg := 360.0, inner := 0.0) -> MeshInstance3D:
	if _tele_shader == null:
		_tele_shader = Shader.new()
		_tele_shader.code = """
shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(1.0, 0.2, 0.1, 0.8);
uniform float fill = 0.0;
uniform int shape = 0;      // 0 circle, 1 cone, 2 line, 3 ring
uniform float arc = 6.2832;
uniform float inner = 0.0;
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float mask = 0.0;
	float prog = 0.0;
	if (shape == 0 || shape == 3) {
		float d = length(p);
		mask = step(d, 1.0) * step(inner, d);
		prog = (d - inner) / max(1.0 - inner, 0.001);
		float edge = smoothstep(0.93, 0.99, d) + (shape == 3 ? smoothstep(inner + 0.06, inner, d) * step(inner, d) : 0.0);
		float inside = step(prog, fill);
		ALBEDO = color.rgb;
		ALPHA = mask * (0.16 + 0.34 * inside + edge * 0.6) * color.a;
	} else if (shape == 1) {
		float d = length(p);
		float ang = abs(atan(p.x, -p.y));
		mask = step(d, 1.0) * step(ang, arc * 0.5);
		float edge = smoothstep(0.93, 0.99, d) + smoothstep(arc * 0.5 - 0.05, arc * 0.5, ang);
		float inside = step(d, fill);
		ALBEDO = color.rgb;
		ALPHA = mask * (0.16 + 0.34 * inside + edge * 0.6) * color.a;
	} else {
		float along = UV.y;
		float edge = smoothstep(0.9, 1.0, abs(p.x));
		float inside = step(1.0 - along, fill);
		ALBEDO = color.rgb;
		ALPHA = (0.16 + 0.34 * inside + edge * 0.6) * color.a;
	}
}
"""
	var mi := MeshInstance3D.new()
	var q := PlaneMesh.new()
	var mat := ShaderMaterial.new()
	mat.shader = _tele_shader
	mat.set_shader_parameter("color", c)
	match shape:
		"circle":
			q.size = Vector2.ONE * size.x * 2.0
			mat.set_shader_parameter("shape", 0)
		"ring":
			q.size = Vector2.ONE * size.x * 2.0
			mat.set_shader_parameter("shape", 3)
			mat.set_shader_parameter("inner", inner / size.x)
		"cone":
			q.size = Vector2.ONE * size.x * 2.0
			mat.set_shader_parameter("shape", 1)
			mat.set_shader_parameter("arc", deg_to_rad(arc_deg))
		"line":
			q.size = Vector2(size.y, size.x)
			q.center_offset = Vector3(0, 0, size.x * 0.5)
			mat.set_shader_parameter("shape", 2)
	mi.mesh = q
	mi.material_override = mat
	mi.position.y = 0.07
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("fill", v), 0.0, 1.0, windup)
	return mi

static func light_flash(c: Color, energy: float, rng_m: float, duration: float) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = c
	l.light_energy = energy
	l.omni_range = rng_m
	l.shadow_enabled = false
	l.visible = not Perf.lite   # efficiency mode: flashes are glow meshes and sparks only (every light is a pass on phones)
	var tw := l.create_tween()
	tw.tween_property(l, "light_energy", 0.0, duration).set_ease(Tween.EASE_OUT)
	tw.tween_callback(l.queue_free)
	return l

## Glowing orb projectile body with a trail.
static func orb(c: Color, radius: float, with_light := true) -> Node3D:
	var root := Node3D.new()
	var core := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	sm.radial_segments = 16
	sm.rings = 8
	core.mesh = sm
	core.material_override = glow_material(c.lerp(Color.WHITE, 0.35), 3.0)
	core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(core)
	var halo := MeshInstance3D.new()
	var hm := SphereMesh.new()
	hm.radius = radius * 2.2
	hm.height = radius * 4.4
	halo.mesh = hm
	var hmat := glow_material(c, 0.8)
	hmat.set_shader_parameter("alpha", 0.35)
	halo.material_override = hmat
	halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(halo)
	var trail := particles(Color(c.r, c.g, c.b, 0.8), 24, 0.35, false, radius * 2.4, 0.3, 180.0, Vector3.ZERO, radius * 0.5)
	root.add_child(trail)
	if with_light and not Perf.lite:
		var l := OmniLight3D.new()
		l.light_color = c
		l.light_energy = 1.6
		l.omni_range = 4.0
		root.add_child(l)
	return root

static func arrow_body() -> Node3D:
	var path := "res://assets/weapons/arrow.glb"
	if ResourceLoader.exists(path):
		var n: Node3D = load(path).instantiate()
		# Arrow model points +Y; projectiles fly along -Z.
		n.rotation.x = -PI / 2.0
		var root := Node3D.new()
		root.add_child(n)
		return root
	var root2 := Node3D.new()
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.04, 0.04, 0.8)
	mi.mesh = b
	root2.add_child(mi)
	return root2

## Jagged lightning bolt between two points (billboard-ish thin quads).
static func lightning_bolt(from: Vector3, to: Vector3, c := Color(0.85, 0.85, 1.0), duration := 0.18, width := 0.12) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts: Array[Vector3] = [from]
	var segs := maxi(4, int(from.distance_to(to) / 0.8))
	var dir := (to - from)
	var side := dir.cross(Vector3.UP).normalized()
	if side.length_squared() < 0.01:
		side = Vector3.RIGHT
	for i in range(1, segs):
		var t := float(i) / segs
		var jitter := side * randf_range(-0.45, 0.45) + Vector3.UP * randf_range(-0.3, 0.3)
		pts.append(from + dir * t + jitter)
	pts.append(to)
	for i in pts.size() - 1:
		var a := pts[i]
		var b := pts[i + 1]
		var up := Vector3.UP * width
		var sd := side * width
		for quad in [[a - up, a + up, b + up, b - up], [a - sd, a + sd, b + sd, b - sd]]:
			for idx in [0, 1, 2, 0, 2, 3]:
				st.set_normal(Vector3.UP)
				st.add_vertex(quad[idx])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var mat := glow_material(c, 4.0)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("alpha", v), 1.0, 0.0, duration)
	tw.tween_callback(mi.queue_free)
	return mi

## Impact burst (sparks + flash) sized by strength. Crits add a bright secondary burst.
static func hit_burst(pos: Vector3, element: int, strength: float, crit: bool) -> Node3D:
	var root := Node3D.new()
	var c := Elements.color(element)
	if element == Elements.PHYSICAL:
		c = Color(1.0, 0.85, 0.6)
	var n := int(clampf(6.0 + strength * 10.0, 6.0, 28.0))
	root.add_child(particles(Color(c.r, c.g, c.b, 1.0), n, 0.35, true, 0.22 + strength * 0.15, 4.0 + strength * 5.0, 70.0, Vector3(0, -9, 0)))
	if crit:
		root.add_child(particles(Color(1.0, 0.95, 0.8, 1.0), 10, 0.18, true, 0.9, 0.5, 180.0))
	if strength > 0.6 or crit:
		root.add_child(light_flash(c, 2.0 + strength * 3.0, 3.0 + strength * 2.0, 0.15))
	_autofree(root, 1.0)                    # the holder too: it used to stay in the map, empty, after every blow
	return root

static func dust_puff(strength := 1.0) -> GPUParticles3D:
	var p := particles(Color(0.55, 0.5, 0.42, 0.45), int(8 + strength * 8), 0.8, true, 0.9 + strength * 0.4, 1.5 + strength, 80.0, Vector3(0, 0.3, 0), 0.3, false)
	return p

static func debris(strength := 1.0, c := Color(0.45, 0.42, 0.38)) -> GPUParticles3D:
	var p := particles(Color(c.r, c.g, c.b, 1.0), int(6 + strength * 6), 0.9, true, 0.18, 5.0 + strength * 2.0, 50.0, Vector3(0, -14, 0), 0.2, false)
	return p

static func beam(c: Color, height: float, radius: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = radius * 0.4
	cm.bottom_radius = radius
	cm.height = height
	cm.cap_top = false
	cm.cap_bottom = false
	mi.mesh = cm
	mi.position.y = height * 0.5
	var mat := glow_material(c, 1.5)
	mat.set_shader_parameter("alpha", 0.35)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi

## A beam that fades out and frees itself — for one-off moments (level-up, heals) spawned with FX.spawn. A plain
## beam() never goes away on its own (it is meant to be parented to something that owns its lifetime).
static func beam_flash(c: Color, height: float, radius: float, duration := 1.1) -> MeshInstance3D:
	var mi := beam(c, height, radius)
	var mat := mi.material_override as ShaderMaterial
	mi.tree_entered.connect(func() -> void:
		var tw := mi.create_tween()
		tw.tween_method(func(a: float) -> void: mat.set_shader_parameter("alpha", a), 0.35, 0.0, duration).set_ease(Tween.EASE_IN)
		tw.tween_callback(mi.queue_free), CONNECT_ONE_SHOT)
	return mi

# ---- Impact, block and heavy-strike effects ---------------------------------------------------------------------

static var _star_shader: Shader
static var _crack_shader: Shader
static var _shield_shader: Shader
static var _streak_mat_cache := {}

## Frees `root` after `after` seconds. bh-037: one-shot GPUParticles3D never emit `finished` in Godot 4.7.2 (a probe spawned
## 40 hit bursts and dust puffs: all 40 were still in the map 4 s later, emitting=false, the signal never fired). Every blow
## left its particle systems behind, each still processed every physics step and drawn every frame: after half a minute of
## a dungeon fight ~500 had piled up and the physics step had grown past 10 ms. Every one-shot effect frees on a timer.
static func _autofree(root: Node3D, after: float) -> void:
	var t := Timer.new()
	t.wait_time = after
	t.one_shot = true
	t.autostart = true
	t.timeout.connect(root.queue_free)
	root.add_child(t)

## Billboarded star flash at the point of contact: bright core plus `rays` spikes that pop out and fade.
static func impact_flash(c: Color, size: float, duration := 0.16, rays := 4, spin := 0.0) -> MeshInstance3D:
	if _star_shader == null:
		_star_shader = Shader.new()
		_star_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled;
uniform vec4 color : source_color = vec4(1.0);
uniform float progress = 0.0;
uniform float rays = 4.0;
uniform float spin = 0.0;
void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0] * length(MODEL_MATRIX[0].xyz),
		INV_VIEW_MATRIX[1] * length(MODEL_MATRIX[1].xyz), INV_VIEW_MATRIX[2] * length(MODEL_MATRIX[2].xyz), MODEL_MATRIX[3]);
}
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = length(p);
	float a = atan(p.y, p.x) + spin;
	float grow = 0.35 + 0.65 * sqrt(progress);
	float core = exp(-d * d * 18.0 / (grow * grow));
	float ray = pow(abs(cos(a * rays * 0.5)), 40.0) * (1.0 - smoothstep(0.0, grow, d));
	float fade = 1.0 - smoothstep(0.35, 1.0, progress);
	vec3 col = mix(color.rgb, vec3(1.0), core * 0.8);
	ALBEDO = col * 3.0;
	ALPHA = clamp((core + ray * 0.9) * fade * color.a, 0.0, 1.0);
}
"""
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2.ONE * size
	mi.mesh = q
	var mat := ShaderMaterial.new()
	mat.shader = _star_shader
	mat.set_shader_parameter("color", c)
	mat.set_shader_parameter("rays", float(rays))
	mat.set_shader_parameter("spin", spin if spin != 0.0 else randf() * TAU)
	mat.render_priority = 5
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("progress", v), 0.0, 1.0, duration)
	tw.tween_callback(mi.queue_free)
	return mi

static func _streak_material() -> StandardMaterial3D:
	if _streak_mat_cache.has(true):
		return _streak_mat_cache[true]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = soft_texture()
	m.disable_receive_shadows = true
	_streak_mat_cache[true] = m
	return m

## Streaking sparks sprayed along `dir` (world). Each spark is a velocity-aligned cross of two thin quads.
static func spark_spray(dir: Vector3, c: Color, amount: int, speed: float, spread := 45.0, lifetime := 0.3, length := 0.45) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = maxi(1, amount)
	p.lifetime = lifetime
	p.one_shot = true
	p.explosiveness = 1.0
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var qd := qdir(dir)
	p.process_material = shared("spark|%s|%s|%.2f|%.0f" % [qd, c.to_html(), snappedf(speed, 0.25), spread], func() -> Resource:
		var pm := ParticleProcessMaterial.new()
		pm.direction = qd
		pm.spread = spread
		pm.initial_velocity_min = speed * 0.45
		pm.initial_velocity_max = speed
		pm.gravity = Vector3(0, -12, 0)
		pm.damping_min = 4.0
		pm.damping_max = 8.0
		pm.particle_flag_align_y = true
		pm.scale_min = 0.6
		pm.scale_max = 1.2
		pm.color_ramp = _ramp(c)
		var curve := CurveTexture.new()
		var cv := Curve.new()
		cv.add_point(Vector2(0, 1))
		cv.add_point(Vector2(1, 0.0))
		curve.curve = cv
		pm.scale_curve = curve
		return pm)
	p.draw_pass_1 = shared("spark_mesh|%.2f" % length, func() -> Resource:
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var w := 0.035
		for axis: Vector3 in [Vector3.RIGHT, Vector3.BACK]:
			var sv := axis * w
			var up := Vector3.UP * length
			var v := [[-sv, Vector2(0, 1)], [sv, Vector2(1, 1)], [sv + up, Vector2(1, 0)], [-sv + up, Vector2(0, 0)]]
			for idx in [0, 1, 2, 0, 2, 3]:
				st.set_uv(v[idx][1])
				st.set_color(Color.WHITE)
				st.add_vertex(v[idx][0] - up * 0.5)
		var mesh := st.commit()
		mesh.surface_set_material(0, _streak_material())
		return mesh)
	p.visibility_aabb = AABB(Vector3(-6, -3, -6), Vector3(12, 9, 12))
	p.emitting = true
	p.finished.connect(p.queue_free)
	_autofree(p, lifetime + 0.5)
	return p

## Standard contact effect for a landed blow: star flash, directional sparks, optional crit / heavy extras.
## `dir` is the direction the blow travelled (attacker -> target).
static func strike_impact(dir: Vector3, c: Color, strength: float, crit: bool, heavy := false) -> Node3D:
	var root := Node3D.new()
	var s := clampf(strength, 0.1, 1.5)
	var flash_c := c.lerp(Color.WHITE, 0.35)
	root.add_child(impact_flash(flash_c, 0.9 + s * 0.9 + (0.8 if crit else 0.0) + (0.9 if heavy else 0.0), 0.14 + (0.06 if heavy else 0.0), 6 if crit else 4))
	var out := dir.slide(Vector3.UP).normalized() if dir.slide(Vector3.UP).length() > 0.01 else Vector3.UP
	out = (out + Vector3.UP * 0.35).normalized()
	root.add_child(spark_spray(out, Color(c.r, c.g, c.b, 1.0), int(5 + s * 10 + (8 if crit else 0)), 6.0 + s * 6.0, 40.0, 0.26, 0.35 + s * 0.2))
	if crit:
		root.add_child(impact_flash(Color(1.0, 0.85, 0.4, 0.9), 2.6 + s, 0.22, 8))
		root.add_child(light_flash(Color(1.0, 0.85, 0.5), 4.0, 4.0, 0.18))
	if heavy:
		root.add_child(spark_spray(Vector3.UP, Color(1.0, 0.9, 0.7, 1.0), 14, 9.0, 80.0, 0.35, 0.5))
		root.add_child(light_flash(c.lerp(Color.WHITE, 0.4), 5.0, 5.0, 0.2))
	_autofree(root, 1.0)
	return root

## Guarded blow: metal sparks off the guard plus a hexagonal barrier flash turned toward the attacker.
## `to_attacker` is the world direction from the defender toward whoever struck. Parries are gold and larger.
static func block_impact(to_attacker: Vector3, perfect: bool) -> Node3D:
	if _shield_shader == null:
		_shield_shader = Shader.new()
		_shield_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(0.6, 0.8, 1.0, 1.0);
uniform float progress = 0.0;
float hex_d(vec2 p) {
	p = abs(p);
	return max(dot(p, normalize(vec2(1.0, 1.7320508))), p.x);
}
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = hex_d(p);
	float r = 0.45 + 0.5 * progress;
	float rim = smoothstep(r - 0.12, r, d) * (1.0 - smoothstep(r, r + 0.03, d));
	vec2 g = p * 4.0;
	vec2 cell = abs(fract(vec2(g.x, g.y + mod(floor(g.x), 2.0) * 0.5)) - 0.5);
	float grid = smoothstep(0.42, 0.5, max(cell.x, cell.y)) * (1.0 - smoothstep(0.0, r, d)) * 0.5;
	float core = exp(-dot(p, p) * 10.0) * (1.0 - progress);
	ALBEDO = mix(color.rgb, vec3(1.0), core) * 3.0;
	ALPHA = clamp((rim + grid + core) * (1.0 - progress) * color.a, 0.0, 1.0);
}
"""
	var root := Node3D.new()
	var c := Color(1.0, 0.85, 0.35, 1.0) if perfect else Color(0.6, 0.8, 1.0, 0.9)
	var flat := to_attacker.slide(Vector3.UP)
	var face := flat.normalized() if flat.length() > 0.01 else Vector3.FORWARD
	var shield := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2.ONE * (1.9 if perfect else 1.3)
	shield.mesh = q
	var mat := ShaderMaterial.new()
	mat.shader = _shield_shader
	mat.set_shader_parameter("color", c)
	shield.material_override = mat
	shield.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# QuadMesh faces +Z; looking_at points -Z at the target, so aim it away from the attacker to face them.
	shield.basis = Basis.looking_at(-face, Vector3.UP)
	shield.position = face * 0.05
	root.add_child(shield)
	var tw := shield.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("progress", v), 0.0, 1.0, 0.32 if perfect else 0.22).set_ease(Tween.EASE_OUT)
	var spark_dir := (face + Vector3.UP * 0.5).normalized()
	root.add_child(spark_spray(spark_dir, Color(1.0, 0.75, 0.35, 1.0), 22 if perfect else 12, 9.0 if perfect else 7.0, 55.0, 0.3, 0.4))
	root.add_child(impact_flash(c.lerp(Color.WHITE, 0.5), 1.6 if perfect else 1.0, 0.12, 4, PI * 0.25))
	root.add_child(light_flash(c, 3.5 if perfect else 1.8, 3.5, 0.15))
	if perfect:
		var ring := ring_wave(Color(1.0, 0.9, 0.5, 0.9), 2.4, 0.35, 0.5)
		ring.position.y = -1.0
		root.add_child(ring)
	_autofree(root, 1.0)
	return root

## Glowing radial ground cracks that burst open and cool down. For heavy slams and finishers.
static func ground_crack(c: Color, radius: float, duration := 1.2) -> MeshInstance3D:
	if _crack_shader == null:
		_crack_shader = Shader.new()
		_crack_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(1.0, 0.7, 0.3, 1.0);
uniform float progress = 0.0;
uniform float seed = 0.0;
float h(float x) { return fract(sin(x * 91.7 + seed) * 43758.5453); }
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = length(p);
	float a = atan(p.y, p.x);
	float n = 9.0;
	float sector = floor((a / 6.2831853 + 0.5) * n);
	float jag = (h(sector) - 0.5) * 0.35 + sin(d * 23.0 + sector * 3.1) * 0.05 + sin(d * 51.0 + sector) * 0.025;
	float local = fract((a / 6.2831853 + 0.5) * n) - 0.5 + jag;
	float len = 0.55 + 0.45 * h(sector + 7.0);
	float open = smoothstep(0.0, 0.25, progress);
	float line = (1.0 - smoothstep(0.0, 0.035 + 0.02 * (1.0 - d), abs(local) * d * 2.2)) * step(d, len * open);
	float core = (1.0 - smoothstep(0.0, 0.22, d)) * 0.6;
	float cool = 1.0 - smoothstep(0.2, 1.0, progress);
	ALBEDO = mix(color.rgb, vec3(1.0, 0.95, 0.85), cool * 0.4) * (1.5 + 2.0 * cool);
	ALPHA = clamp((line + core * cool) * (1.0 - smoothstep(0.7, 1.0, progress)) * color.a, 0.0, 1.0);
}
"""
	var mi := MeshInstance3D.new()
	var q := PlaneMesh.new()
	q.size = Vector2.ONE * radius * 2.0
	mi.mesh = q
	var mat := ShaderMaterial.new()
	mat.shader = _crack_shader
	mat.set_shader_parameter("color", c)
	mat.set_shader_parameter("seed", randf() * 100.0)
	mi.material_override = mat
	mi.position.y = 0.08
	mi.rotation.y = randf() * TAU
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var tw := mi.create_tween()
	tw.tween_method(func(v): mat.set_shader_parameter("progress", v), 0.0, 1.0, duration)
	tw.tween_callback(mi.queue_free)
	return mi

## Everything a finisher / heavy blow leaves at the target's feet: glowing cracks, shock ring, debris, dust.
static func heavy_impact(c: Color, strength := 1.0) -> Node3D:
	var root := Node3D.new()
	root.add_child(ground_crack(c, 1.6 + strength * 0.9, 1.1))
	root.add_child(ring_wave(c.lerp(Color.WHITE, 0.3), 2.2 + strength, 0.35, 0.6))
	var d := debris(0.8 + strength * 0.4)
	d.position.y = 0.3
	root.add_child(d)
	root.add_child(dust_puff(0.7 + strength * 0.4))
	_autofree(root, 1.4)
	return root

## A pillar of light that shoots up and fades (War Cry, Judgment, skill casts).
static func light_pillar(c: Color, height: float, radius: float, duration := 0.6) -> MeshInstance3D:
	var mi := beam(c, height, radius)
	var mat := mi.material_override as ShaderMaterial
	mat.set_shader_parameter("energy", 2.2)
	mi.scale = Vector3(0.2, 0.05, 0.2)
	var tw := mi.create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE, duration * 0.3).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_method(func(v): mat.set_shader_parameter("alpha", v), 0.6, 0.0, duration).set_delay(duration * 0.15)
	tw.chain().tween_callback(mi.queue_free)
	return mi

## A giant blade of light that drops from the sky and plants itself point-first (Judgment). Root sits on the ground.
static func light_sword(c: Color, length := 5.0, drop_time := 0.16, linger := 0.55) -> Node3D:
	var root := Node3D.new()
	var sword := Node3D.new()
	root.add_child(sword)
	var mat := glow_material(c.lerp(Color.WHITE, 0.3), 3.0)
	var blade := MeshInstance3D.new()
	var bm := PrismMesh.new()
	bm.size = Vector3(0.55, length, 0.12)
	blade.mesh = bm
	blade.rotation.z = PI            # prism apex points down into the ground
	blade.position.y = length * 0.5
	blade.material_override = mat
	sword.add_child(blade)
	var guard := MeshInstance3D.new()
	var gm := BoxMesh.new()
	gm.size = Vector3(1.8, 0.18, 0.2)
	guard.mesh = gm
	guard.position.y = length + 0.05
	guard.material_override = mat
	sword.add_child(guard)
	var grip := MeshInstance3D.new()
	var hm := CylinderMesh.new()
	hm.top_radius = 0.08
	hm.bottom_radius = 0.08
	hm.height = 1.0
	grip.mesh = hm
	grip.position.y = length + 0.6
	grip.material_override = mat
	sword.add_child(grip)
	for n: MeshInstance3D in [blade, guard, grip]:
		n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	sword.position.y = 9.0
	var tw := root.create_tween()
	tw.tween_property(sword, "position:y", -0.6, drop_time).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	tw.tween_interval(linger)
	tw.tween_method(func(v): mat.set_shader_parameter("alpha", v), 1.0, 0.0, 0.35)
	tw.tween_callback(root.queue_free)
	return root

## Translucent fresnel dome that snaps up around the caster (Iron Bulwark).
static func shield_dome(c: Color, radius: float, duration := 0.9) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	sm.is_hemisphere = true
	sm.radial_segments = 24
	sm.rings = 10
	mi.mesh = sm
	var mat := glow_material(c, 0.9)
	mat.set_shader_parameter("alpha", 0.0)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.scale = Vector3.ONE * 0.3
	var tw := mi.create_tween()
	tw.set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE, duration * 0.25).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_method(func(v): mat.set_shader_parameter("alpha", v), 0.0, 0.4, duration * 0.2)
	tw.chain().tween_method(func(v): mat.set_shader_parameter("alpha", v), 0.4, 0.0, duration * 0.75)
	tw.chain().tween_callback(mi.queue_free)
	return mi
