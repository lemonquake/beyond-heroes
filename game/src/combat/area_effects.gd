class_name AreaEffects
## Reusable area-of-effect building blocks shared by skills, enemies, elites and bosses. Every damaging effect resolves
## through `Actor.receive_hit` (the single damage pipeline); these helpers only decide WHO is hit and WHEN.

## Hit every actor of `mask` within `radius` of `center` once. Returns the actors hit.
static func burst(world_node: Node3D, center: Vector3, radius: float, mask: int, req: DamageRequest, source: Node,
		exclude: Array = [], per_target: Callable = Callable()) -> Array:
	var out := []
	if world_node == null or not world_node.is_inside_tree():
		return out
	for a: Actor in CombatQuery.actors_in_radius(world_node.get_world_3d(), center, radius, mask):
		if exclude.has(a) or a == source:
			continue
		var r := req.clone()
		r.tags[&"aoe"] = true
		var push := a.global_position - center
		push.y = 0.0
		r.tags[&"push_dir"] = push.normalized() if push.length() > 0.05 else Vector3.FORWARD
		if per_target.is_valid():
			per_target.call(a, r)
		var res := a.receive_hit(r, source, a.center())
		out.append([a, res])
	return out


## A line/area that travels along a direction and hits each actor it touches once (waves, fissures, charges).
class Sweeper:
	extends Node3D
	var source: Node
	var request: DamageRequest
	var mask := BH.LAYER_ENEMY
	var dir := Vector3.FORWARD
	var speed := 14.0
	var length := 10.0
	var width := 2.0
	var push_along := false          # knock targets along the sweep direction (tidal wave)
	var on_hit: Callable:
		set(v):
			on_hit = v
			_on_hit_owner = SafeCallable.owner_of(v)
	var _on_hit_owner := 0
	var hit_ids := {}
	var travelled := 0.0
	var visual: Node3D
	var trail_every := 1.2
	var trail_fx: Callable           # func(position) spawns per-step visuals
	var _next_trail := 0.0

	func _physics_process(delta: float) -> void:
		if not is_finite(delta) or delta <= 0.0:
			return
		var step := minf(speed * delta, length - travelled)
		var from := global_position
		var to := from + dir * step
		if CombatQuery.blocked(get_world_3d(), from + Vector3.UP * 0.6, to + Vector3.UP * 0.6):
			queue_free()
			return
		for a: Actor in CombatQuery.actors_in_line(get_world_3d(), from - dir * 0.5, dir, step + 1.0, width, mask):
			if a == source or hit_ids.has(a.get_instance_id()):
				continue
			hit_ids[a.get_instance_id()] = true
			var r := request.clone()
			r.tags[&"aoe"] = true
			r.tags[&"push_dir"] = dir if push_along else (a.global_position - global_position).slide(Vector3.UP).normalized()
			var res := a.receive_hit(r, source if is_instance_valid(source) else null, a.center())
			if SafeCallable.alive(on_hit, _on_hit_owner):
				on_hit.call(a, res)
		global_position = to
		travelled += step
		_next_trail -= step
		if _next_trail <= 0.0 and trail_fx.is_valid():
			_next_trail = trail_every
			trail_fx.call(global_position)
		if travelled >= length - 0.001:
			if visual:
				for c in visual.get_children():
					if c is GPUParticles3D:
						c.emitting = false
			set_physics_process(false)
			get_tree().create_timer(0.4).timeout.connect(queue_free)

static func sweep(parent: Node, from: Vector3, dir: Vector3, speed: float, length: float, width: float, req: DamageRequest,
		source: Node, mask: int) -> Sweeper:
	var s := Sweeper.new()
	Perf.mark_fx(s)
	s.source = source
	s.request = req
	s.mask = mask
	s.dir = Vector3(dir.x, 0, dir.z).normalized()
	s.speed = speed
	s.length = length
	s.width = width
	parent.add_child(s)
	s.global_position = from
	s.add_to_group(&"sweep")          # Tempos read these to get out of the way
	return s


## A lingering ground hazard that damages actors inside it every `interval` seconds (burning ground, corruption).
class Hazard:
	extends Node3D
	var source: Node
	var request: DamageRequest
	var mask := BH.LAYER_PLAYER
	var radius := 2.5
	var duration := 5.0
	var interval := 0.5
	var status_id := &""             # applied (refreshed) to everyone inside each tick
	var _t := 0.0
	var _tick := 0.0
	var decal: Node3D

	func _physics_process(delta: float) -> void:
		if not is_finite(delta) or delta <= 0.0:
			return
		_t += delta
		_tick += delta
		if _tick >= interval:
			_tick -= interval
			for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, radius, mask):
				if a == source:
					continue
				if request:
					var r := request.clone()
					r.tags[&"aoe"] = true
					# bh-028: a monster's pool can be grazed by an evasive hero; heroes' pools always land
					r.graze = true
					r.evadable = is_instance_valid(source) and source is Actor and (source as Actor).team == BH.Team.ENEMY
					r.blockable = false
					a.receive_hit(r, source if is_instance_valid(source) else null, a.center())
				if status_id != &"":
					a.status.apply(status_id)
		if _t >= duration:
			set_physics_process(false)
			if decal:
				var tw := decal.create_tween()
				tw.tween_property(decal, "scale", Vector3(0.01, 1, 0.01), 0.4)
			for c in get_children():
				if c is GPUParticles3D:
					c.emitting = false
			get_tree().create_timer(0.6).timeout.connect(queue_free)

static func hazard(parent: Node, at: Vector3, radius: float, duration: float, req: DamageRequest, source: Node, mask: int,
		color: Color, interval := 0.5) -> Hazard:
	var h := Hazard.new()
	Perf.mark_fx(h)
	h.source = source
	h.request = req
	h.mask = mask
	h.radius = radius
	h.duration = duration
	h.interval = interval
	parent.add_child(h)
	h.global_position = at
	h.add_to_group(&"hazard")
	var disc := VFXLib.telegraph("circle", Vector2(radius, radius), 0.01, Color(color.r, color.g, color.b, 0.55))
	h.add_child(disc)
	h.decal = disc
	var p := VFXLib.particles(Color(color.r, color.g, color.b, 0.8), int(10 + radius * 6), 0.9, false, 0.45, 1.2, 25.0, Vector3(0, 1.5, 0), radius * 0.8)
	p.position.y = 0.2
	h.add_child(p)
	return h


## A telegraphed delayed blast: ground marker fills over `delay`, then one burst (meteors, slams, boss novas).
class DelayedBlast:
	extends Node3D
	var source: Node
	var request: DamageRequest
	var mask := BH.LAYER_PLAYER
	var radius := 3.0
	var inner := 0.0                 # ring blasts spare the inside
	var delay := 1.0
	var on_blast: Callable:           # func(position, hits)
		set(v):
			on_blast = v
			_on_blast_owner = SafeCallable.owner_of(v)
	var _on_blast_owner := 0
	var _t := 0.0

	func time_left() -> float:
		return delay - _t
	var marker: Node3D

	func _physics_process(delta: float) -> void:
		if not is_finite(delta) or delta <= 0.0:
			return
		_t += delta
		if _t < delay:
			return
		set_physics_process(false)
		if marker:
			marker.queue_free()
		var hits := []
		if request:
			var excl := []
			if inner > 0.0:
				for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, inner, mask):
					excl.append(a)
			hits = AreaEffects.burst(self, global_position, radius, mask, request, source if is_instance_valid(source) else null, excl)
		if SafeCallable.alive(on_blast, _on_blast_owner):
			on_blast.call(global_position, hits)
		queue_free()

static func delayed(parent: Node, at: Vector3, radius: float, delay: float, req: DamageRequest, source: Node, mask: int,
		color := Color(1.0, 0.25, 0.1, 0.8), shape := "circle", inner := 0.0) -> DelayedBlast:
	var b := DelayedBlast.new()
	Perf.mark_fx(b)
	b.source = source
	b.request = req
	b.mask = mask
	b.radius = radius
	b.delay = delay
	b.inner = inner
	parent.add_child(b)
	b.global_position = at
	b.add_to_group(&"telegraph")      # Tempos read these to dodge (time left = delay - _t)
	var m := VFXLib.telegraph(shape, Vector2(radius, radius), delay, color, 360.0, inner)
	b.add_child(m)
	b.marker = m
	if req != null:
		Net.share_telegraph(at, radius, delay, color, shape, inner, source)   # the warning shows for every player (bh-008)
	return b
