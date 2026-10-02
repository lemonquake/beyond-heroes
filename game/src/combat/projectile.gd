class_name Projectile
extends Node3D
## A moving hit volume shared by the player and enemies (arrows, bolts, spells).
##
## Movement is integrated in fixed physics steps and tested as a swept segment each step: world geometry with a ray
## (so thin walls stop it — no tunneling at any speed) and actors with a segment-vs-capsule distance test against every
## living actor near the segment. Each target is hit at most once; `pierce` counts extra targets.
## Damage goes through `DamagePipeline` via `Actor.receive_hit` with a per-target clone of `request`.

signal hit_actor(target: Actor, result: DamageResult, point: Vector3)
signal expired(point: Vector3, by_wall: bool)

var source: Node                   # Actor that fired it (may be freed mid-flight)
var request: DamageRequest
var target_mask := BH.LAYER_ENEMY
var velocity := Vector3.ZERO
var gravity := 0.0
var max_range := 20.0
var radius := 0.3
var pierce := 0
var element := Elements.PHYSICAL
var explode_radius := 0.0          # >0: area burst at the end point (hits everyone in radius once)
var homing := 0.0                  # turn rate (rad/s) toward `homing_target`
var homing_target: Node3D
var deflectable := true            # can be destroyed by Gale Burst / parries
var on_hit: Callable:               # func(target, result, point)
	set(v):
		on_hit = v
		_on_hit_owner = SafeCallable.owner_of(v)
var _on_hit_owner := 0
var on_end: Callable:               # func(point, by_wall)
	set(v):
		on_end = v
		_on_end_owner = SafeCallable.owner_of(v)
var _on_end_owner := 0
var hit_sound := &""
var body: Node3D
var projectile_look := "orb"

var _travelled := 0.0
var _hit := {}
var volley_hits: Dictionary = {}    # shared only by a Split Shot volley
var _done := false

const MAX_LIFETIME := 8.0
var _age := 0.0

static func spawn(parent: Node, from: Vector3, dir: Vector3, speed: float, p_request: DamageRequest, p_source: Node, mask: int,
		p_element := Elements.PHYSICAL, look := "orb") -> Projectile:
	var p := Projectile.new()
	p.request = p_request
	p.source = p_source
	p.target_mask = mask
	p.element = p_element
	p.velocity = dir.normalized() * speed
	Perf.mark_fx(p)
	parent.add_child(p)
	p.global_position = from
	p._build_body(look)
	p.add_to_group(&"projectile")
	if p_request != null:
		Net.share_projectile(p, from, dir, speed, p_element, look)   # other players see a harmless copy (bh-008)
	return p

func _build_body(look: String) -> void:
	projectile_look = look
	var c := Elements.color(element)
	if look.begins_with("model:"):
		body = _model_body(look.substr(6), c)
	else:
		match look:
			"arrow":
				body = VFXLib.arrow_body()
			"bolt":
				body = VFXLib.arrow_body()
				body.scale = Vector3(1.35, 1.35, 0.60)
			"none":
				body = Node3D.new()
			_:
				body = VFXLib.orb(c if element != Elements.PHYSICAL else Color(1.0, 0.9, 0.7), clampf(radius * 0.8, 0.12, 0.6), look != "orb_nolight")
	add_child(body)
	_face()

## A thrown weapon (javelin): the weapon's own model flying point first, trailing a faint streak.
func _model_body(path: String, c: Color) -> Node3D:
	var b := Node3D.new()
	if ResourceLoader.exists(path):
		var m: Node3D = load(path).instantiate()
		m.rotation.x = -PI * 0.5          # model +Y (blade / tip) -> -Z (the flight direction after look_at)
		m.position.z = 0.7
		b.add_child(m)
		var ms: Array[MeshInstance3D] = []
		for n in m.find_children("*", "MeshInstance3D", true, false):
			ms.append(n)
		MaterialLibrary.apply_character(ms, Color(0.6, 0.2, 0.2))
	var tc := Color(c.r, c.g, c.b, 0.5) if element != Elements.PHYSICAL else Color(1.0, 0.95, 0.85, 0.35)
	b.add_child(VFXLib.particles(tc, 14, 0.25, false, 0.12, 0.2, 10.0, Vector3.ZERO, 0.05))
	return b

func _face() -> void:
	if velocity.length_squared() > 0.0001 and body:
		body.look_at(global_position + velocity, Vector3.UP if absf(velocity.normalized().y) < 0.95 else Vector3.FORWARD)

func _physics_process(delta: float) -> void:
	if _done or not is_finite(delta) or delta <= 0.0:
		return
	_age += delta
	if _age > MAX_LIFETIME:
		_finish(global_position, false)
		return
	if homing > 0.0 and homing_target and is_instance_valid(homing_target):
		var want := (homing_target.global_position + Vector3.UP * 1.0 - global_position).normalized() * velocity.length()
		velocity = velocity.slerp(want, clampf(homing * delta, 0.0, 1.0))
	velocity.y -= gravity * delta
	var from := global_position
	var step := velocity * delta
	var to := from + step
	var world := get_world_3d()
	if world == null:
		return
	# World: thin-wall safe ray along the whole step.
	var q := PhysicsRayQueryParameters3D.create(from, to, BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS)
	var wall := world.direct_space_state.intersect_ray(q)
	var seg_end := to
	if wall:
		seg_end = wall.position
	# Actors: segment vs vertical capsule (body radius), each target once.
	var hits := _actors_on_segment(world, from, seg_end)
	for h in hits:
		var a: Actor = h[0]
		if _hit.has(a.get_instance_id()) or volley_hits.has(a.get_instance_id()):
			continue
		_hit[a.get_instance_id()] = true
		volley_hits[a.get_instance_id()] = true
		_hit_target(a, h[1])
		if _done:
			return
		if pierce <= 0:
			_finish(h[1], false)
			return
		pierce -= 1
	if wall:
		var col = wall.collider
		if col != null and col.has_method("take_hit"):
			col.take_hit(maxf(1.0, request.base_max if request else 5.0), velocity.normalized() * 3.0)
		_finish(wall.position - step.normalized() * 0.05, true)
		return
	global_position = to
	_travelled += step.length()
	_face()
	if _travelled >= max_range:
		_finish(global_position, false)

func _actors_on_segment(world: World3D, a: Vector3, b: Vector3) -> Array:
	var mid := (a + b) * 0.5
	var half := a.distance_to(b) * 0.5
	var out := []
	for act: Actor in CombatQuery.actors_in_radius(world, mid, half + radius + 1.0, target_mask):
		if act == source:
			continue
		# closest point on the segment to the actor's vertical axis (horizontal distance) + height overlap
		var ab := Vector2(b.x - a.x, b.z - a.z)
		var ap := Vector2(act.global_position.x - a.x, act.global_position.z - a.z)
		var t := clampf(ap.dot(ab) / maxf(ab.length_squared(), 0.000001), 0.0, 1.0)
		var closest := a.lerp(b, t)
		var dh := Vector2(act.global_position.x - closest.x, act.global_position.z - closest.z).length()
		var y0 := act.global_position.y - 0.2
		var y1 := act.global_position.y + act.body_height + 0.2
		if dh <= radius + act.body_radius and closest.y >= y0 - radius and closest.y <= y1 + radius:
			out.append([act, closest, t])
	out.sort_custom(func(x, y): return x[2] < y[2])
	return out

func _hit_target(a: Actor, point: Vector3) -> void:
	if request == null:
		return
	var req := request.clone()
	req.tags[&"projectile"] = true
	req.tags[&"push_dir"] = Vector3(velocity.x, 0, velocity.z).normalized()
	var src: Node = source if is_instance_valid(source) else null
	var r := a.receive_hit(req, src, point)
	if hit_sound != &"":
		Audio.play_at(hit_sound, point)
	hit_actor.emit(a, r, point)
	if SafeCallable.alive(on_hit, _on_hit_owner):
		on_hit.call(a, r, point)

func _finish(point: Vector3, by_wall: bool) -> void:
	if _done:
		return
	_done = true
	if explode_radius > 0.0 and request != null:
		var world := get_world_3d()
		if world:
			for a: Actor in CombatQuery.actors_in_radius(world, point, explode_radius, target_mask):
				if a == source or _hit.has(a.get_instance_id()):
					continue
				_hit[a.get_instance_id()] = true
				var req := request.clone()
				req.tags[&"aoe"] = true
				req.graze = true
				req.evadable = is_instance_valid(source) and source is Actor and (source as Actor).team == BH.Team.ENEMY
				var r := a.receive_hit(req, source if is_instance_valid(source) else null, a.center())
				if SafeCallable.alive(on_hit, _on_hit_owner):
					on_hit.call(a, r, a.center())
	if SafeCallable.alive(on_end, _on_end_owner):
		on_end.call(point, by_wall)
	expired.emit(point, by_wall)
	# let trail particles fade before freeing
	if body:
		for c in body.get_children():
			if c is GPUParticles3D:
				c.emitting = false
			elif c is MeshInstance3D or c is OmniLight3D:
				c.visible = false
	set_physics_process(false)
	get_tree().create_timer(0.5).timeout.connect(queue_free)

## Destroyed by a deflecting effect (Gale Burst, parry). Returns true if it was removed.
func deflect() -> bool:
	if not deflectable or _done:
		return false
	_done = true
	FX.spawn(VFXLib.hit_burst(global_position, element, 0.3, false), global_position)
	queue_free()
	return true
