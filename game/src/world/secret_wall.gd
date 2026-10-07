class_name SecretWall
extends Actor
## bh-042: a cracked wall closing a secret room in the Abyss dungeons (plan cell '#', DataDungeonPlansAbyss). It looks
## like the masonry round it, with faint seams of light in its cracks and grit trickling from them. Like the practice
## dummy it sits on the enemy layer, so every blow, spell, shot and blast lands on it; it counts blows, not damage
## (a level-200 hit and a level-150 hit break it alike), cracks wider with each one and falls after BLOWS. A broken wall
## stays broken for that hero (world flag `flag`). It is not a monster: not in the "enemy" group, no AI, no threat.

const BLOWS := 5
const BLOW_GAP := 0.18                 # one swing's several hit windows count once
const WIDTH := 4.0
const HEIGHT := 3.8
const THICK := 0.9

var flag: StringName = &""
var across_x := true                   # the wall spans the X axis (a secret room north of it), else the Z axis
var tint := Color(1.0, 0.6, 0.3)
var blows := 0
var _gap := 0.0
var _visual: Node3D
var _seams: Array[MeshInstance3D] = []
var _grit: GPUParticles3D
var _seam_mat: StandardMaterial3D
var _broken := false

func _init() -> void:
	display_name = "Cracked Wall"
	team = BH.Team.ENEMY
	weight = 999.0
	body_radius = 1.0
	body_height = HEIGHT

func _ready() -> void:
	if flag != &"" and Game.has_flag(flag):
		_rubble_only()
		return
	super._ready()
	name = "SecretWall"
	add_to_group(&"secret_wall")
	collision_layer = BH.LAYER_ENEMY | BH.LAYER_PROPS
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(WIDTH, HEIGHT, THICK) if across_x else Vector3(THICK, HEIGHT, WIDTH)
	cs.shape = box
	cs.position.y = HEIGHT * 0.5
	add_child(cs)
	_build_look()

func rebuild_stats() -> void:
	var d := DerivedStats.new()
	d.set_stat(&"max_hp", 1.0e9)
	d.set_stat(&"poise", 1.0e9)
	d.set_stat(&"knockback_res", 1.0)
	stats = d

func is_aggressive() -> bool:
	return false

func in_combat() -> bool:
	return false

func apply_knockback(_dir: Vector3, _speed: float, _source: DerivedStats, _source_node: Node, _depth := 0, _launch := 0.0) -> void:
	pass

func die(_killer: Node) -> void:
	pass

## The dungeon builder dresses the wall with its themed masonry piece (built while the theme's stone is active).
func adopt(n: Node3D) -> void:
	if n == null:
		return
	_visual = n
	var gt := n.global_transform
	n.get_parent().remove_child(n)
	add_child(n)
	n.global_transform = gt

func _build_look() -> void:
	_seam_mat = StandardMaterial3D.new()
	_seam_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_seam_mat.albedo_color = Color(tint.r, tint.g, tint.b)
	_seam_mat.emission_enabled = true
	_seam_mat.emission = tint
	_seam_mat.emission_energy_multiplier = 1.4
	var rng2 := RandomNumberGenerator.new()
	rng2.seed = hash(String(flag))
	# a jagged crack running down both faces: short segments, each turned a little from the last
	for face in [-1.0, 1.0]:
		var p := Vector2(rng2.randf_range(-0.6, 0.6), HEIGHT * 0.92)
		for i in 9:
			var ang := rng2.randf_range(-0.7, 0.7) - PI * 0.5
			var ln := rng2.randf_range(0.28, 0.5)
			var q := p + Vector2(cos(ang), sin(ang)) * ln
			_seam(p, q, face, rng2.randf_range(0.03, 0.06))
			if rng2.randf() < 0.35:
				var b := q + Vector2(cos(ang + 1.2), sin(ang + 1.2)) * ln * 0.6
				_seam(q, b, face, 0.03)
			p = q
	_grit = VFXLib.particles(Color(0.55, 0.5, 0.45, 0.7), 10, 1.4, false, 0.05, 0.3, 15.0, Vector3(0, -6.0, 0), 0.6, false)
	_grit.position = Vector3(0, HEIGHT * 0.85, 0)
	add_child(_grit)

func _seam(a: Vector2, b: Vector2, face: float, w: float) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	var d := b - a
	bm.size = Vector3(w, d.length(), 0.02)
	mi.mesh = bm
	mi.material_override = _seam_mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mid := (a + b) * 0.5
	var off := face * (THICK * 0.5 + 0.03)
	if across_x:
		mi.position = Vector3(mid.x, mid.y, off)
		mi.rotation.z = atan2(d.y, d.x) - PI * 0.5
	else:
		mi.position = Vector3(off, mid.y, mid.x)
		mi.rotation = Vector3(atan2(d.y, d.x) - PI * 0.5, 0, 0)
	add_child(mi)
	_seams.append(mi)

func _physics_process(delta: float) -> void:
	_gap = maxf(0.0, _gap - delta)

## Every blow counts (any damage, any element), at most one per BLOW_GAP.
func receive_hit(req: DamageRequest, attacker: Node = null, hit_point := Vector3.INF) -> DamageResult:
	var r := DamageResult.new()
	if _broken or req == null or req.kind == DamageRequest.Kind.DOT:
		return r
	if attacker is Actor and (attacker as Actor).team == BH.Team.ENEMY:
		return r
	if _gap > 0.0:
		return r
	_gap = BLOW_GAP
	blows += 1
	var at := hit_point if hit_point != Vector3.INF else center()
	FX.spawn(VFXLib.dust_puff(0.6), at)
	Audio.play_at(&"break_stone", global_position, -8.0 + 2.0 * blows)
	Events.camera_shake.emit(0.08 * blows)
	_seam_mat.emission_energy_multiplier = 1.4 + 1.1 * blows
	for s in _seams:
		s.scale.x = 1.0 + 0.6 * blows
	if _visual:
		var tw := _visual.create_tween()
		tw.tween_property(_visual, "position", Vector3(randf_range(-0.06, 0.06), 0, randf_range(-0.06, 0.06)), 0.05)
		tw.tween_property(_visual, "position", Vector3.ZERO, 0.08)
	if blows >= BLOWS:
		shatter(attacker)
	else:
		FX.text_popup(at + Vector3.UP * 0.6, "Crack!" if blows < BLOWS - 1 else "It gives…", Color(0.9, 0.8, 0.6), 0.7)
	return r

func shatter(by: Node = null) -> void:
	if _broken:
		return
	_broken = true
	if flag != &"":
		Game.set_world_flag(flag, true)
	var center_p := global_position + Vector3.UP * HEIGHT * 0.5
	var push := Vector3.ZERO
	if by is Node3D:
		push = (center_p - (by as Node3D).global_position).slide(Vector3.UP).normalized()
	var stone := MaterialLibrary.env("BH_StoneDark")
	for i in 14:
		var body := RigidBody3D.new()
		body.collision_layer = BH.LAYER_DEBRIS
		body.collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND
		body.mass = 8.0
		var sz := Vector3(randf_range(0.35, 0.8), randf_range(0.25, 0.6), randf_range(0.3, 0.7))
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = sz
		mi.mesh = bm
		mi.material_override = stone
		var cs := CollisionShape3D.new()
		var sh := BoxShape3D.new()
		sh.size = sz
		cs.shape = sh
		body.add_child(mi)
		body.add_child(cs)
		get_parent().add_child(body)
		var lat := randf_range(-WIDTH * 0.45, WIDTH * 0.45)
		body.global_position = global_position + (Vector3(lat, 0, 0) if across_x else Vector3(0, 0, lat)) + Vector3.UP * randf_range(0.4, HEIGHT - 0.4)
		body.linear_velocity = (push * randf_range(3.0, 7.0) + Vector3.UP * randf_range(1.0, 3.5)).limit_length(9.0)
		body.angular_velocity = Vector3(randf_range(-6, 6), randf_range(-6, 6), randf_range(-6, 6))
		var tw := body.create_tween()
		tw.tween_interval(6.0)
		tw.tween_property(mi, "scale", Vector3.ONE * 0.01, 0.8)
		tw.tween_callback(body.queue_free)
	FX.spawn(VFXLib.dust_puff(2.4), center_p)
	FX.spawn(VFXLib.light_flash(tint, 3.0, 8.0, 0.4), center_p)
	Audio.play_at(&"break_stone", global_position, 2.0)
	Events.camera_shake.emit(0.5)
	Events.notify.emit("The cracked wall gives way: a hidden room lies behind it.", &"discovery")
	_rubble_only()
	queue_free()

## What a broken wall leaves on the floor (also what a hero sees on returning).
func _rubble_only() -> void:
	var path := MapBuilder.ENV_DIR % "rubble_spill"
	var parent := get_parent()
	if parent and ResourceLoader.exists(path):
		var n: Node3D = (load(path) as PackedScene).instantiate()
		PracticeDummy._strip_collision(n)
		parent.add_child.call_deferred(n)
		n.position = position
		n.rotation.y = 0.0 if across_x else PI * 0.5
		MaterialLibrary.apply_environment(n)
	if not _broken:
		queue_free()
