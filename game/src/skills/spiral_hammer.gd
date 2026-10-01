class_name SpiralHammer
extends Node3D
## The Knight's Hallowed Hammer (bh-010): a glowing hammer that spirals outward from where it was thrown, striking
## every enemy it passes (each enemy at most once every 0.45 s). `request == null`: a harmless copy for co-op players.

var source: Node
var request: DamageRequest
var mask := BH.LAYER_ENEMY
var duration := 2.2
var start_angle := 0.0
var turn_rate := 5.2                 # rad/s
var growth := 1.9                    # radius grows this many metres per second
var start_radius := 0.8
var hit_radius := 1.0
var on_hit: Callable
var _center := Vector3.ZERO
var _t := 0.0
var _last_hit := {}
var _head: Node3D

static func create(parent: Node, at: Vector3, angle: float, req: DamageRequest, p_source: Node, p_mask: int, p_duration := 2.2) -> SpiralHammer:
	var h := SpiralHammer.new()
	h.request = req
	h.source = p_source
	h.mask = p_mask
	h.start_angle = angle
	h.duration = p_duration
	Perf.mark_fx(h)
	parent.add_child(h)
	h._center = at
	h.global_position = at
	h.add_to_group(&"skill_area")
	return h

func _ready() -> void:
	_head = Node3D.new()
	add_child(_head)
	var gold := StandardMaterial3D.new()
	gold.albedo_color = Color(1.0, 0.85, 0.45)
	gold.emission_enabled = true
	gold.emission = Color(1.0, 0.82, 0.4)
	gold.emission_energy_multiplier = 2.4
	gold.metallic = 0.8
	var head := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.52, 0.28, 0.28)
	head.mesh = bm
	head.material_override = gold
	_head.add_child(head)
	var handle := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.045
	cm.bottom_radius = 0.045
	cm.height = 0.7
	handle.mesh = cm
	handle.material_override = gold
	handle.position = Vector3(0, -0.4, 0)
	_head.add_child(handle)
	var glow := VFXLib.orb(Color(1.0, 0.9, 0.55), 0.35, true)
	_head.add_child(glow)
	var trail := VFXLib.particles(Color(1.0, 0.88, 0.5, 0.8), 24, 0.4, false, 0.25, 0.3, 30.0, Vector3.ZERO, 0.1)
	_head.add_child(trail)
	_place()

func _place() -> void:
	var a := start_angle + turn_rate * _t
	var r := start_radius + growth * _t
	global_position = _center + Vector3(cos(a) * r, 1.0, sin(a) * r)
	if _head:
		_head.rotation = Vector3(_t * 14.0, -a, 0.0)

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	if _t >= duration:
		FX.spawn(VFXLib.particles(Color(1.0, 0.9, 0.55, 0.9), 18, 0.4, true, 0.3, 4.0, 180.0, Vector3.ZERO, 0.2), global_position)
		queue_free()
		return
	_place()
	if request == null or not is_inside_tree():
		return
	var now := _t
	var src: Node = source if is_instance_valid(source) else null
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position - Vector3.UP, hit_radius, mask):
		var id := a.get_instance_id()
		if now - float(_last_hit.get(id, -9.0)) < 0.45:
			continue
		_last_hit[id] = now
		var r := request.clone()
		r.tags[&"push_dir"] = (a.global_position - _center).slide(Vector3.UP).normalized()
		var res := a.receive_hit(r, src, a.center())
		FX.spawn(VFXLib.impact_flash(Color(1.0, 0.9, 0.55), 0.9, 0.14, 6), a.center())
		if on_hit.is_valid():
			on_hit.call(a, res)
		Audio.play_at(&"holy_strike", a.global_position, -6.0)
