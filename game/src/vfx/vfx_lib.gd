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
	p.amount = amount
	p.lifetime = lifetime
	p.one_shot = one_shot
	p.explosiveness = 0.9 if one_shot else 0.0
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2.ONE * 0.5
	q.material = particle_material(additive)
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-6, -2, -6), Vector3(12, 10, 12))
	if one_shot:
		p.emitting = true
		p.finished.connect(p.queue_free)
	return p

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
	mi.material_override = mat
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
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(1.0, 0.9, 0.4)
		s.material_override = mat
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
	if with_light:
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
