class_name Gore
## Hit materials and gore: what a creature is made of decides what flies out when it is struck and what it leaves on
## the ground. Every effect is short-lived and bounded (decals are budgeted by FX). Blood can be turned off in
## Settings (`Settings.blood`); then flesh hits fall back to a neutral dust/impact puff and no pools are left.
##
## Materials: flesh (red blood), ichor (dark corrupted blood), bone (chips + grave dust), stone (sparks + stone chips),
## aether (cyan motes), shadow (black smoke with violet sparks).

const FLESH := &"flesh"
const ICHOR := &"ichor"
const BONE := &"bone"
const STONE := &"stone"
const AETHER := &"aether"
const SHADOW := &"shadow"

const SPLAT_VARIANTS := 6
static var _splats: Array[Texture2D] = []
static var _pool_tex: Texture2D
static var _drop_mat: StandardMaterial3D
static var _chip_mat: StandardMaterial3D

## True when this material leaves liquid on the ground (and Settings allow it).
static func bleeds(material: StringName) -> bool:
	return (material == FLESH or material == ICHOR) and Settings.blood

# ---- Hit bursts -------------------------------------------------------------------------------------------------

## Burst at `pos`, flying mostly along `dir` (attacker -> target), sized by strength (0..1.2).
static func hit(pos: Vector3, dir: Vector3, material: StringName, liquid: Color, strength: float, crit: bool) -> Node3D:
	var root := Node3D.new()
	var s := clampf(strength, 0.15, 1.2)
	dir = dir.slide(Vector3.UP).normalized() if dir.slide(Vector3.UP).length() > 0.01 else Vector3.FORWARD
	var spray_dir := (dir + Vector3.UP * 0.55).normalized()
	match material:
		FLESH, ICHOR:
			if Settings.blood:
				root.add_child(_spray(liquid, int(10 + s * 26 + (12 if crit else 0)), spray_dir, 32.0, 3.5 + s * 4.0, 0.07 + s * 0.05))
				root.add_child(_mist(liquid.lerp(Color.BLACK, 0.2), s))
				if crit or s > 0.8:
					root.add_child(_spray(liquid.darkened(0.25), 10, (spray_dir + Vector3.UP * 0.6).normalized(), 55.0, 5.5, 0.1))
			else:
				root.add_child(VFXLib.particles(Color(0.85, 0.8, 0.7, 0.55), int(6 + s * 8), 0.35, true, 0.3, 3.0, 60.0, Vector3(0, -6, 0), 0.0, false))
		BONE:
			root.add_child(_chips(Color(0.86, 0.82, 0.7), int(6 + s * 14), spray_dir, 5.0 + s * 3.0, 0.06 + s * 0.03))
			root.add_child(VFXLib.particles(Color(0.7, 0.68, 0.6, 0.45), int(5 + s * 8), 0.9, true, 0.7, 1.2, 80.0, Vector3(0, 0.4, 0), 0.2, false))
			if crit:
				root.add_child(VFXLib.particles(Color(0.45, 1.0, 0.85, 0.9), 10, 0.5, true, 0.25, 3.0, 180.0))   # grave-light escaping
		STONE:
			root.add_child(VFXLib.particles(Color(1.0, 0.8, 0.45, 1.0), int(8 + s * 16), 0.3, true, 0.12, 7.0 + s * 4.0, 45.0, Vector3(0, -12, 0)))
			root.add_child(_chips(Color(0.5, 0.48, 0.44), int(4 + s * 10), spray_dir, 4.0 + s * 3.0, 0.08 + s * 0.04))
			root.add_child(VFXLib.particles(Color(0.55, 0.52, 0.48, 0.4), 6, 0.8, true, 0.8, 1.0, 80.0, Vector3(0, 0.3, 0), 0.2, false))
		AETHER:
			root.add_child(VFXLib.particles(Color(0.55, 0.97, 1.0, 1.0), int(12 + s * 20), 0.6, true, 0.2, 4.0 + s * 3.0, 180.0, Vector3(0, 1.5, 0), 0.15))
			root.add_child(VFXLib.light_flash(Color(0.5, 0.95, 1.0), 1.5 + s * 2.0, 3.0, 0.14))
		SHADOW:
			root.add_child(VFXLib.particles(Color(0.04, 0.02, 0.06, 0.75), int(8 + s * 10), 0.9, true, 0.9, 1.6, 120.0, Vector3(0, 0.8, 0), 0.25, false))
			root.add_child(VFXLib.particles(Color(0.7, 0.35, 1.0, 1.0), int(6 + s * 8), 0.35, true, 0.15, 5.0, 60.0, Vector3(0, -6, 0)))
		_:
			root.add_child(VFXLib.particles(Color(1.0, 0.85, 0.6, 1.0), int(6 + s * 10), 0.35, true, 0.2, 5.0, 70.0, Vector3(0, -9, 0)))
	# free the holder once its one-shot children are gone
	var t := Timer.new()
	t.wait_time = 2.5
	t.one_shot = true
	t.autostart = true
	t.timeout.connect(root.queue_free)
	root.add_child(t)
	return root

## Liquid droplets: mix-blended, falling under gravity, thrown in a cone along `dir`.
static func _spray(c: Color, amount: int, dir: Vector3, spread: float, speed: float, size: float) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = maxi(4, amount)
	p.lifetime = 0.7
	p.one_shot = true
	p.explosiveness = 0.95
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.direction = dir
	pm.spread = spread
	pm.initial_velocity_min = speed * 0.45
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, -18.0, 0)
	pm.scale_min = size * 0.5
	pm.scale_max = size * 1.4
	var g := Gradient.new()
	g.set_color(0, Color(c.r * 1.2, c.g * 1.2, c.b * 1.2, 1.0))
	g.set_color(1, Color(c.r * 0.6, c.g * 0.6, c.b * 0.6, 0.0))
	g.add_point(0.75, Color(c.r, c.g, c.b, 0.95))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := SphereMesh.new()
	q.radius = 0.5
	q.height = 1.0
	q.radial_segments = 6
	q.rings = 3
	q.material = _drop_material()
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-5, -3, -5), Vector3(10, 8, 10))
	p.emitting = true
	p.finished.connect(p.queue_free)
	return p

static func _mist(c: Color, s: float) -> GPUParticles3D:
	return VFXLib.particles(Color(c.r, c.g, c.b, 0.55), int(4 + s * 6), 0.45, true, 0.55 + s * 0.3, 1.2, 90.0, Vector3(0, -1.0, 0), 0.1, false)

## Solid chips (bone, stone): small tumbling boxes that bounce off nothing and fade.
static func _chips(c: Color, amount: int, dir: Vector3, speed: float, size: float) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = maxi(3, amount)
	p.lifetime = 0.9
	p.one_shot = true
	p.explosiveness = 0.95
	p.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = dir
	pm.spread = 50.0
	pm.initial_velocity_min = speed * 0.4
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, -16.0, 0)
	pm.angular_velocity_min = -540.0
	pm.angular_velocity_max = 540.0
	pm.scale_min = size * 0.5
	pm.scale_max = size * 1.3
	pm.color = c
	p.process_material = pm
	var b := BoxMesh.new()
	b.size = Vector3(1.0, 0.6, 1.4)
	b.material = _chip_material()
	p.draw_pass_1 = b
	p.visibility_aabb = AABB(Vector3(-5, -3, -5), Vector3(10, 8, 10))
	p.emitting = true
	p.finished.connect(p.queue_free)
	return p

static func _drop_material() -> StandardMaterial3D:
	if _drop_mat == null:
		_drop_mat = StandardMaterial3D.new()
		_drop_mat.vertex_color_use_as_albedo = true
		_drop_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_drop_mat.roughness = 0.15
		_drop_mat.metallic_specular = 0.8
	return _drop_mat

static func _chip_material() -> StandardMaterial3D:
	if _chip_mat == null:
		_chip_mat = StandardMaterial3D.new()
		_chip_mat.vertex_color_use_as_albedo = true
		_chip_mat.roughness = 0.8
	return _chip_mat

# ---- Ground stains (decals) -------------------------------------------------------------------------------------

## Procedural splatter masks (white on transparent; tinted by the decal's modulate). Deterministic per variant.
static func splat_texture(variant: int) -> Texture2D:
	if _splats.is_empty():
		for v in SPLAT_VARIANTS:
			_splats.append(_make_splat(v))
	return _splats[posmod(variant, SPLAT_VARIANTS)]

static func _make_splat(v: int) -> Texture2D:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	img.fill(Color(1, 1, 1, 0))
	var r := RandomNumberGenerator.new()
	r.seed = 9173 + v * 131
	var blobs: Array = []
	# main body, a few lobes, satellite drops, and a directional streak (+X) for sprays
	blobs.append([Vector2(n * 0.45, n * 0.5), n * r.randf_range(0.16, 0.22)])
	for i in r.randi_range(3, 6):
		var a := r.randf() * TAU
		blobs.append([Vector2(n * 0.45, n * 0.5) + Vector2(cos(a), sin(a)) * n * r.randf_range(0.08, 0.18), n * r.randf_range(0.06, 0.12)])
	for i in r.randi_range(8, 16):
		var a := r.randf_range(-0.6, 0.6) if i % 2 == 0 else r.randf() * TAU
		var d := n * r.randf_range(0.22, 0.46)
		blobs.append([Vector2(n * 0.45, n * 0.5) + Vector2(cos(a), sin(a)) * d, n * r.randf_range(0.012, 0.035)])
	for y in n:
		for x in n:
			var p := Vector2(x, y)
			var f := 0.0
			for b in blobs:
				var dd: float = p.distance_to(b[0]) / float(b[1])
				f += 1.0 / maxf(dd * dd, 0.0001)
			var a2 := clampf((f - 1.0) * 2.5, 0.0, 1.0)
			if a2 > 0.0:
				# darker rim, lighter thin centre: reads as a liquid stain
				var rim := clampf((f - 1.0) / 3.0, 0.0, 1.0)
				img.set_pixel(x, y, Color(1.0 - 0.25 * (1.0 - rim), 1.0 - 0.25 * (1.0 - rim), 1.0 - 0.25 * (1.0 - rim), a2 * (0.82 + 0.18 * rim)))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)

## A single stain decal projecting down onto whatever is below (terrain, floors, stairs).
static func stain(c: Color, size: float, variant: int, yaw: float) -> Decal:
	var d := Decal.new()
	d.texture_albedo = splat_texture(variant)
	d.modulate = c
	d.albedo_mix = 1.0
	d.size = Vector3(size, 1.2, size)
	d.rotation.y = yaw
	# the decal is centred just above the ground (FX places it), so the surface sits in the unfaded middle band
	d.upper_fade = 0.15
	d.lower_fade = 0.15
	d.normal_fade = 0.4
	d.cull_mask = 1   # world / props render layer only (not characters)
	return d
