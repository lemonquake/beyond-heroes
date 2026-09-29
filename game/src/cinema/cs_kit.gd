class_name CSKit
## bh-021: staging helpers shared by the story's cutscenes — flashback sets, crowds, props, weather, materials.

const LEGION_EYES := Color(0.62, 0.3, 1.0)
const SEAL := Color(0.35, 0.85, 1.0)
const WRATH := Color(1.0, 0.12, 0.05)
const HOLY := Color(1.0, 0.8, 0.4)

static var _ghost_mat: ShaderMaterial

## A look-at point that puts `subject` on the right (side > 0) or left (side < 0) third of a shot from `cam`.
static func off(cam: Vector3, subject: Vector3, side: float) -> Vector3:
	var f := subject - cam
	f.y = 0.0
	var right := f.normalized().cross(Vector3.UP)
	return subject - right * side * f.length() * 0.28

## The Weeping Causeway three winters ago, at night in a storm: the boss map itself, darker and colder, rain on the
## camera. Built inside the flashback world.
static func causeway_set(root: Node3D) -> void:
	var map := Game.build_map(&"weeping_causeway")
	if map == null:
		return
	map.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(map)
	var we: WorldEnvironment = map.environment
	if we and we.environment:
		var e := we.environment
		e.fog_density *= 1.25
		e.ambient_light_energy *= 1.35
		e.ambient_light_color = Color(0.36, 0.4, 0.5)
		e.adjustment_enabled = true
		e.adjustment_saturation = 0.58
		e.adjustment_contrast = 1.22
		e.tonemap_exposure *= 0.95
		e.glow_enabled = true
		e.glow_intensity = 1.0
	if map.sun:
		map.sun.light_energy *= 1.3
		map.sun.light_color = Color(0.62, 0.7, 0.95)
	# a cold rim from behind the host and two torches' worth of warm fill on the causeway mouth
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-20, -100, 0)
	rim.light_energy = 0.9
	rim.light_color = Color(0.5, 0.62, 1.0)
	root.add_child(rim)
	for p: Vector3 in [Vector3(-10, 3.5, 5), Vector3(-10, 3.5, -5), Vector3(2, 4.0, 0)]:
		var l := OmniLight3D.new()
		l.light_color = Color(0.9, 0.7, 0.55)
		l.light_energy = 1.2
		l.omni_range = 14.0
		l.position = p
		root.add_child(l)
	var cam := _camera_of(root)
	if cam:
		cam.add_child(LegendFX.rain())

## A black void for visions: fog, a pale key light, a stone disc under the actor.
static func void_set(root: Node3D, tint := Color(0.08, 0.02, 0.04), fog := Color(0.12, 0.02, 0.05)) -> void:
	var we := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = tint
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.3, 0.22, 0.26)
	e.ambient_light_energy = 0.4
	e.glow_enabled = true
	e.glow_intensity = 1.1
	e.glow_bloom = 0.1
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.fog_enabled = true
	e.fog_light_color = fog
	e.fog_density = 0.05
	we.environment = e
	root.add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 150, 0)
	key.light_energy = 0.5
	key.light_color = Color(0.7, 0.72, 0.9)
	root.add_child(key)
	var disc := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 5.0
	cm.bottom_radius = 5.4
	cm.height = 0.6
	disc.mesh = cm
	disc.position.y = -0.3
	disc.material_override = MaterialLibrary.env("BH_StoneDark")
	root.add_child(disc)

## The Black Spire's cell: a void with a ring of chain pillars.
static func spire_set(root: Node3D) -> void:
	void_set(root, Color(0.02, 0.01, 0.03), Color(0.08, 0.03, 0.12))
	for i in 3:
		var a := TAU * i / 3.0 + 0.5
		var p: Node3D = MapBuilder.scene("pillar_quoin").instantiate()
		root.add_child(p)
		MaterialLibrary.apply_environment(p)
		p.position = Vector3(cos(a) * 4.2, 0, sin(a) * 4.2)
		p.scale = Vector3(1.0, 2.2, 1.0)
	var l := OmniLight3D.new()
	l.light_color = Color(0.55, 0.3, 1.0)
	l.light_energy = 1.4
	l.omni_range = 12.0
	l.position = Vector3(0, 5, 0)
	root.add_child(l)

static func _camera_of(root: Node) -> Camera3D:
	for c in root.get_children():
		if c is Camera3D:
			return c
	return null

## Rows of Legion soldiers (violet eyes, a few in soulfire) facing `yaw`. Returns the actors.
static func legion(cs: CutscenePlayer, origin: Vector3, rows: int, per_row: int, spacing: Vector2, yaw := -90.0,
		clip := &"idle", prefix := "legion") -> Array:
	var out := []
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(prefix)
	for r in rows:
		for i in per_row:
			var off := Vector3(r * spacing.y, 0, (i - (per_row - 1) * 0.5) * spacing.x + (0.5 if r % 2 else 0.0) * spacing.x)
			off = Basis(Vector3.UP, deg_to_rad(yaw + 90.0)) * off
			var key := StringName("%s_%d_%d" % [prefix, r, i])
			var model := "bonewarden" if (r + i) % 4 == 0 else "hollow_soldier"
			var a := cs.actor(key, model, 1.05, origin + off + Vector3(rng.randf_range(-0.3, 0.3), 0, rng.randf_range(-0.3, 0.3)),
				yaw + rng.randf_range(-8, 8))
			a.recolor_emission(LEGION_EYES, 5.0)
			a.play(clip, 0.0, rng.randf_range(0.85, 1.1), rng.randf() * 1.5)
			out.append(a)
	return out

## Accord sealers: knights of the Registry in white and blue with staves.
static func sealers(cs: CutscenePlayer, origin: Vector3, count: int, spacing: float, yaw: float) -> Array:
	var out := []
	var l := OmniLight3D.new()
	l.light_color = SEAL
	l.light_energy = 2.2
	l.omni_range = 9.0
	cs.fx(l, origin + Vector3(1.5, 3.0, 0))
	for i in count:
		var off := Basis(Vector3.UP, deg_to_rad(yaw + 90.0)) * Vector3(0, 0, (i - (count - 1) * 0.5) * spacing)
		var a := cs.actor(StringName("sealer_%d" % i), "res://assets/characters/mage.glb", 1.0, origin + off, yaw)
		MaterialLibrary.apply_character(a._meshes, Color(0.72, 0.78, 0.9))
		a.attach(&"main", "res://assets/weapons/staff.glb")
		a.play(&"idle_staff" if a.has_clip(&"idle_staff") else &"idle", 0.0)
		out.append(a)
	return out

## The Dusk-Piercer Shard in a hand (weapon.L by default), with its crimson glow.
static func shard_in_hand(a: CutsceneActor, bone := "weapon.L", glow := 1.0) -> Node3D:
	var xf := Transform3D(Basis(Vector3.RIGHT, deg_to_rad(-70.0)).scaled(Vector3.ONE * 0.55), Vector3(0.0, 0.05, 0.03))
	var w := a.attach(&"shard", "dusk_piercer_tip", bone, xf)
	if w:
		var l := OmniLight3D.new()
		l.light_color = WRATH
		l.light_energy = 0.22 * glow
		l.omni_range = 0.9
		l.process_mode = Node.PROCESS_MODE_ALWAYS
		w.add_child(l)
	return w

## A spirit made of pale light (Tobren coming through the waypoint).
static func ghost_material(c := Color(0.55, 0.85, 1.0)) -> ShaderMaterial:
	if _ghost_mat == null:
		_ghost_mat = ShaderMaterial.new()
		_ghost_mat.shader = Shader.new()
		_ghost_mat.shader.code = """
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled;
uniform vec4 col : source_color = vec4(0.55, 0.85, 1.0, 1.0);
uniform float power = 1.0;
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.2);
	float flick = 0.85 + 0.15 * sin(TIME * 7.0 + FRAGCOORD.y * 0.05);
	ALBEDO = col.rgb * (0.4 + rim * 2.2) * flick * power;
	ALPHA = clamp((0.3 + rim) * power, 0.0, 1.0);
}
"""
	var m := _ghost_mat.duplicate() as ShaderMaterial
	m.set_shader_parameter("col", c)
	return m

## Lightning over the set at these times (random strikes out on the water around `center`).
static func storm(cs: CutscenePlayer, times: Array, center: Vector3, radius := 30.0) -> void:
	for t in times:
		cs.at(float(t), func() -> void:
			var a := randf() * TAU
			var at := center + Vector3(cos(a), 0, sin(a)) * randf_range(radius * 0.4, radius)
			LegendFX.lightning_strike(cs.stage(), at)
			cs.flash(cs.t, Color(0.75, 0.8, 1.0, 1.0), 0.18)
			Audio.play(&"cast_lightning", -6.0, 0.1))

## Throw an actor back and down (a soldier struck by a charge): tween position and play a reaction.
static func blast(cs: CutscenePlayer, a: CutsceneActor, dir: Vector3, dist := 4.0, dur := 0.6) -> void:
	if not is_instance_valid(a):
		return
	a.play(&"knockback" if a.has_clip(&"knockback") else &"hit_heavy", 0.05)
	var tw := cs.tween(a)
	tw.tween_property(a, "position", a.position + dir.normalized() * dist, dur).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func() -> void:
		if is_instance_valid(a) and a.has_clip(&"death_back"):
			a.play(&"death_back", 0.1))
