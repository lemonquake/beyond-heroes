class_name FrostOrb
extends Node3D
## The Mage's Frost Orb (bh-010): a slow orb that sheds ice shards in a whirling pattern as it travels, then bursts
## into a ring of shards. The orb itself does not hit; its shards do (each a normal Projectile, so co-op players see
## them). `request == null`: a harmless copy.

var source: Node
var request: DamageRequest
var mask := BH.LAYER_ENEMY
var dir := Vector3.FORWARD
var speed := 7.0
var reach := 14.0
var shard_every := 0.09
var shard_speed := 16.0
var shard_range := 7.0
var burst_count := 12
var on_hit: Callable
var _travelled := 0.0
var _acc := 0.0
var _spin := 0.0
var _body: Node3D

static func create(parent: Node, from: Vector3, p_dir: Vector3, req: DamageRequest, p_source: Node, p_mask: int, p_reach := 14.0) -> FrostOrb:
	var o := FrostOrb.new()
	o.request = req
	o.source = p_source
	o.mask = p_mask
	o.dir = p_dir.normalized()
	o.reach = p_reach
	Perf.mark_fx(o)
	parent.add_child(o)
	o.global_position = from
	o.add_to_group(&"skill_area")
	return o

func _ready() -> void:
	_body = VFXLib.orb(Color(0.6, 0.9, 1.0), 0.45, true)
	add_child(_body)
	var frost := VFXLib.particles(Color(0.8, 0.95, 1.0, 0.8), 30, 0.5, false, 0.2, 1.5, 180.0, Vector3.ZERO, 0.4)
	add_child(frost)

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	var step := dir * speed * delta
	var next := global_position + step
	if is_inside_tree() and CombatQuery.blocked(get_world_3d(), global_position, next):
		_burst()
		return
	global_position = next
	_travelled += step.length()
	_spin += delta * 9.0
	if _body:
		_body.rotation.y = _spin
	_acc += delta
	while _acc >= shard_every:
		_acc -= shard_every
		_shard(dir.rotated(Vector3.UP, _spin))
	if _travelled >= reach:
		_burst()

func _shard(d: Vector3) -> void:
	if request == null:
		return
	var pr := Projectile.spawn(get_parent(), global_position, d, shard_speed, request.clone(), source if is_instance_valid(source) else null, mask, Elements.ICE, "orb_nolight")
	pr.max_range = shard_range
	pr.radius = 0.25
	pr.request.tags[&"projectile"] = true
	if on_hit.is_valid():
		pr.on_hit = func(a: Actor, res: DamageResult, _pt: Vector3) -> void: on_hit.call(a, res)

func _burst() -> void:
	set_physics_process(false)
	for i in burst_count:
		_shard(dir.rotated(Vector3.UP, TAU * i / float(burst_count)))
	FX.spawn(VFXLib.ring_wave(Color(0.7, 0.92, 1.0, 0.9), 3.0, 0.4, 0.6), global_position)
	Audio.play_at(&"shatter_ice", global_position, -2.0)
	queue_free()
