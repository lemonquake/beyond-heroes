class_name StormArea
extends Node3D
## A persistent skill area (Blizzard, Arrow Rain, bh-010): every `tick` seconds for `duration` seconds it hits every
## actor of `mask` inside `radius` once, while shards or arrows rain down. With `request == null` it is a harmless
## copy drawn on the other players' screens (multiplayer).

var source: Node
var request: DamageRequest
var mask := BH.LAYER_ENEMY
var radius := 4.0
var duration := 3.0
var tick := 0.5
var style := "ice"                   # ice | arrows
var on_hit: Callable                 # func(actor, result)
var _t := 0.0
var _acc := 0.0
var _rain: GPUParticles3D
var _disc: Node3D

static func create(parent: Node, at: Vector3, p_radius: float, p_duration: float, p_tick: float, req: DamageRequest,
		p_source: Node, p_mask: int, p_style := "ice") -> StormArea:
	var s := StormArea.new()
	s.radius = p_radius
	s.duration = p_duration
	s.tick = maxf(0.1, p_tick)
	s.request = req
	s.source = p_source
	s.mask = p_mask
	s.style = p_style
	parent.add_child(s)
	s.global_position = at
	s.add_to_group(&"skill_area")
	return s

func _color() -> Color:
	return Color(0.7, 0.9, 1.0) if style == "ice" else Color(1.0, 0.9, 0.7)

func _ready() -> void:
	var c := _color()
	_disc = VFXLib.telegraph("circle", Vector2(radius, radius), 0.01, Color(c.r, c.g, c.b, 0.28))
	add_child(_disc)
	if style == "ice":
		_rain = VFXLib.particles(Color(0.8, 0.95, 1.0, 0.9), int(30 + radius * 10), 0.7, false, 0.22, 2.0, 8.0, Vector3(0, -26, 0), radius * 0.9)
		_rain.position.y = 9.0
		add_child(_rain)
		var mist := VFXLib.particles(Color(0.75, 0.9, 1.0, 0.35), int(10 + radius * 3), 1.4, false, 1.1, 0.6, 180.0, Vector3(0, 0.4, 0), radius * 0.8)
		mist.position.y = 0.4
		add_child(mist)

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	_acc += delta
	while _acc >= tick and _t <= duration + 0.001:
		_acc -= tick
		_pulse()
	if _t >= duration:
		set_physics_process(false)
		if _rain:
			_rain.emitting = false
		var tw := create_tween()
		tw.tween_property(_disc, "scale", Vector3(0.01, 1, 0.01), 0.35)
		get_tree().create_timer(0.9, false).timeout.connect(queue_free)

func _rand_point() -> Vector3:
	var a := randf() * TAU
	var r := sqrt(randf()) * radius
	return global_position + Vector3(cos(a) * r, 0.0, sin(a) * r)

func _pulse() -> void:
	# falling visuals: a few shards/arrows land at random points each tick
	var n := 3 if style == "ice" else 5
	for i in n:
		var at := _rand_point()
		var body: Node3D = VFXLib.arrow_body() if style == "arrows" else VFXLib.orb(Color(0.75, 0.95, 1.0), 0.14, false)
		get_parent().add_child(body)
		var from := at + Vector3(randf_range(-1.0, 1.0), 9.0, randf_range(-1.0, 1.0))
		body.global_position = from
		if style == "arrows":
			body.look_at_from_position(from, at, Vector3.FORWARD if absf((at - from).normalized().y) > 0.99 else Vector3.UP)
		var tw := body.create_tween()
		tw.tween_property(body, "global_position", at, 0.22).set_ease(Tween.EASE_IN)
		tw.tween_callback(func() -> void:
			if is_instance_valid(body):
				body.queue_free()
			FX.spawn(VFXLib.ring_wave(_color(), 0.5, 0.2, 0.25), at))
	if request == null or not is_inside_tree():
		return
	var src: Node = source if is_instance_valid(source) else null
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, radius, mask):
		var r := request.clone()
		r.tags[&"aoe"] = true
		r.tags[&"push_dir"] = (a.global_position - global_position).slide(Vector3.UP).normalized()
		var res := a.receive_hit(r, src, a.center())
		if on_hit.is_valid():
			on_hit.call(a, res)
	Audio.play_at(&"freeze" if style == "ice" else &"arrow_impact", global_position, -8.0)
