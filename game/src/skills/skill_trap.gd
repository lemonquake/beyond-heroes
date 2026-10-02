class_name SkillTrap
extends Node3D
## A placed trap (Ranger's Snare Trap and Blast Trap, bh-010). Arms after `arm_time`, then springs when an actor of
## `mask` steps within `trigger` metres: one burst of `request` in `radius` (+ `on_hit` for statuses). Lasts
## `lifetime` seconds. A caster keeps at most `max_count` traps (the oldest is removed). `request == null`: a harmless
## copy for the other players' screens.

var source: Node
var request: DamageRequest
var mask := BH.LAYER_ENEMY
var style := "snare"                 # snare | blast
var radius := 2.5
var trigger := 1.4
var arm_time := 0.6
var lifetime := 20.0
var on_hit: Callable:
	set(v):
		on_hit = v
		_on_hit_owner = SafeCallable.owner_of(v)
var _on_hit_owner := 0
var _t := 0.0
var _armed := false
var _body: Node3D
var _blink: OmniLight3D

static func create(parent: Node, at: Vector3, p_style: String, req: DamageRequest, p_source: Node, p_mask: int, p_radius: float,
		max_count := 3) -> SkillTrap:
	var group := StringName("traps_%d" % (p_source.get_instance_id() if p_source else 0))
	var mine := parent.get_tree().get_nodes_in_group(group) if parent.is_inside_tree() else []
	while mine.size() >= maxi(1, max_count):
		var oldest: Node = mine.pop_front()
		if is_instance_valid(oldest):
			oldest.queue_free()
	var t := SkillTrap.new()
	t.style = p_style
	t.request = req
	t.source = p_source
	t.mask = p_mask
	t.radius = p_radius
	parent.add_child(t)
	t.global_position = at
	t.add_to_group(group)
	t.add_to_group(&"skill_trap")
	return t

func _ready() -> void:
	_body = Node3D.new()
	add_child(_body)
	var metal := StandardMaterial3D.new()
	metal.albedo_color = Color(0.32, 0.3, 0.28)
	metal.metallic = 0.9
	metal.roughness = 0.45
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.34
	tm.outer_radius = 0.44
	ring.mesh = tm
	ring.material_override = metal
	ring.scale = Vector3(1, 0.4, 1)
	ring.position.y = 0.05
	_body.add_child(ring)
	var accent := Color(0.6, 1.0, 0.5) if style == "snare" else Color(1.0, 0.45, 0.1)
	for i in 8:
		var sp := MeshInstance3D.new()
		var pm := PrismMesh.new()
		pm.size = Vector3(0.07, 0.16, 0.05)
		sp.mesh = pm
		sp.material_override = metal
		var a := TAU * i / 8.0
		sp.position = Vector3(cos(a) * 0.39, 0.13, sin(a) * 0.39)
		sp.rotation.y = -a
		_body.add_child(sp)
	var core := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.12
	sm.height = 0.18
	core.mesh = sm
	var cm := StandardMaterial3D.new()
	cm.albedo_color = accent
	cm.emission_enabled = true
	cm.emission = accent
	cm.emission_energy_multiplier = 2.0
	core.material_override = cm
	core.position.y = 0.08
	_body.add_child(core)
	_blink = OmniLight3D.new()
	_blink.light_color = accent
	_blink.light_energy = 0.0
	_blink.omni_range = 2.0
	_blink.position.y = 0.4
	_blink.shadow_enabled = false
	add_child(_blink)
	Audio.play_at(&"armor_rustle", global_position, -6.0)

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	if not _armed and _t >= arm_time:
		_armed = true
	if _blink:
		_blink.light_energy = (1.2 + sin(_t * 6.0)) if _armed else 0.0
	if _t >= lifetime:
		queue_free()
		return
	if not _armed or request == null or not is_inside_tree():
		return
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, trigger, mask):
		_spring()
		return

## Also called remotely (the host's trap sprang) so the copies go off at the same time.
func _spring() -> void:
	set_physics_process(false)
	var accent := Color(0.7, 1.0, 0.6) if style == "snare" else Color(1.0, 0.5, 0.15)
	if style == "snare":
		FX.spawn(VFXLib.ring_wave(Color(0.9, 1.0, 0.85, 0.9), radius, 0.45, 0.5), global_position)
		FX.spawn(VFXLib.particles(Color(0.92, 0.95, 0.9, 0.9), 40, 0.7, true, 0.22, 6.0, 80.0, Vector3(0, -6, 0), 0.3), global_position + Vector3.UP * 0.3)
		Audio.play_at(&"block", global_position)
	else:
		FX.spawn(VFXLib.ring_wave(accent, radius, 0.4, 0.9), global_position)
		FX.spawn(VFXLib.hit_burst(global_position + Vector3.UP * 0.5, Elements.FIRE, 1.4, false), global_position + Vector3.UP * 0.5)
		FX.spawn(VFXLib.light_flash(accent, 6.0, radius * 2.5, 0.3), global_position + Vector3.UP)
		FX.spawn(VFXLib.debris(0.8), global_position + Vector3.UP * 0.3)
		Events.camera_shake.emit(0.2)
		Audio.play_at(&"fire_explode", global_position, 2.0)
	if request != null and is_inside_tree():
		var src: Node = source if is_instance_valid(source) else null
		for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, radius, mask):
			var r := request.clone()
			r.tags[&"aoe"] = true
			r.tags[&"push_dir"] = (a.global_position - global_position).slide(Vector3.UP).normalized()
			var res := a.receive_hit(r, src, a.center())
			if SafeCallable.alive(on_hit, _on_hit_owner):
				on_hit.call(a, res)
	queue_free()
