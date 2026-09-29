class_name SkillSentry
extends Node3D
## A summoned skill object (bh-010): the Mage's Flame Sentinel (a turret that throws fire bolts at the nearest enemy)
## and the Shadowblade's Blade Sentinel (a spinning blade that cuts everything around it). Untargetable; lives
## `lifetime` seconds. A caster keeps at most `max_count` of each kind (the oldest crumbles). With `request == null`
## it is a harmless copy for the other players' screens.

var source: Node
var request: DamageRequest
var mask := BH.LAYER_ENEMY
var mode := "turret"                 # turret | blades
var lifetime := 8.0
var interval := 0.8
var reach := 14.0                     # turret: target range; blades: damage radius
var element := Elements.FIRE
var look := "orb"
var speed := 22.0
var on_hit: Callable
var _t := 0.0
var _acc := 0.0
var _spin: Node3D
var _light: OmniLight3D

static func create(parent: Node, at: Vector3, p_mode: String, req: DamageRequest, p_source: Node, p_mask: int,
		p_lifetime: float, p_interval: float, p_reach: float, p_element: int, max_count := 1) -> SkillSentry:
	var group := StringName("sentry_%s_%d" % [p_mode, p_source.get_instance_id() if p_source else 0])
	var mine := parent.get_tree().get_nodes_in_group(group) if parent.is_inside_tree() else []
	while mine.size() >= maxi(1, max_count):
		var oldest: Node = mine.pop_front()
		if is_instance_valid(oldest):
			oldest.queue_free()
	var s := SkillSentry.new()
	s.mode = p_mode
	s.request = req
	s.source = p_source
	s.mask = p_mask
	s.lifetime = p_lifetime
	s.interval = maxf(0.15, p_interval)
	s.reach = p_reach
	s.element = p_element
	parent.add_child(s)
	s.global_position = at
	s.add_to_group(group)
	s.add_to_group(&"skill_sentry")
	return s

func _ready() -> void:
	var c := Elements.color(element) if element != Elements.PHYSICAL else Color(0.85, 0.8, 1.0)
	if mode == "turret":
		var base := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.18
		cyl.bottom_radius = 0.42
		cyl.height = 1.3
		base.mesh = cyl
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.16, 0.12, 0.1)
		m.emission_enabled = true
		m.emission = c * 0.35
		base.material_override = m
		base.position.y = 0.65
		add_child(base)
		_spin = VFXLib.orb(c, 0.32, false)
		_spin.position.y = 1.55
		add_child(_spin)
		var flame := VFXLib.particles(Color(c.r, c.g, c.b, 0.85), 18, 0.6, false, 0.35, 1.2, 25.0, Vector3(0, 2.5, 0), 0.15)
		flame.position.y = 1.5
		add_child(flame)
	else:
		_spin = Node3D.new()
		_spin.position.y = 0.9
		add_child(_spin)
		for i in 3:
			var blade := MeshInstance3D.new()
			var bm := PrismMesh.new()
			bm.size = Vector3(0.22, 1.05, 0.04)
			blade.mesh = bm
			var mat := StandardMaterial3D.new()
			mat.albedo_color = Color(0.75, 0.75, 0.82)
			mat.metallic = 1.0
			mat.roughness = 0.25
			mat.emission_enabled = true
			mat.emission = Color(0.5, 0.25, 0.8) * 0.6
			blade.material_override = mat
			blade.rotation = Vector3(PI * 0.5, TAU * i / 3.0, 0.0)
			blade.position = Vector3(cos(TAU * i / 3.0), 0, sin(TAU * i / 3.0)) * 0.45
			_spin.add_child(blade)
		var hub := MeshInstance3D.new()
		var hm := CylinderMesh.new()
		hm.top_radius = 0.16
		hm.bottom_radius = 0.16
		hm.height = 0.12
		hub.mesh = hm
		_spin.add_child(hub)
	_light = OmniLight3D.new()
	_light.light_color = c
	_light.light_energy = 1.4
	_light.omni_range = 3.5
	_light.position.y = 1.4
	_light.shadow_enabled = false
	add_child(_light)
	FX.spawn(VFXLib.ring_wave(c, 1.4, 0.35), global_position)

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	if _spin:
		_spin.rotation.y += delta * (14.0 if mode == "blades" else 2.0)
	if _t >= lifetime:
		set_physics_process(false)
		FX.spawn(VFXLib.particles(Color(0.5, 0.45, 0.4, 0.8), 16, 0.5, true, 0.3, 3.0, 180.0, Vector3(0, -4, 0), 0.4), global_position + Vector3.UP)
		queue_free()
		return
	_acc += delta
	if _acc < interval:
		return
	_acc = 0.0
	if mode == "turret":
		_shoot()
	else:
		_cut()

func _shoot() -> void:
	if not is_inside_tree():
		return
	var from := global_position + Vector3.UP * 1.55
	var best: Actor = null
	var bd := INF
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, reach, mask):
		var d := a.global_position.distance_squared_to(global_position)
		if d < bd and not CombatQuery.blocked(get_world_3d(), from, a.center()):
			bd = d
			best = a
	if best == null:
		return
	var dir := (best.center() - from)
	if request == null:
		return                           # the real sentinel's bolts are shared by Projectile.spawn
	var pr := Projectile.spawn(get_parent(), from, dir.normalized(), speed, request.clone(), source if is_instance_valid(source) else null, mask, element, look)
	pr.max_range = reach + 3.0
	pr.radius = 0.3
	if on_hit.is_valid():
		pr.on_hit = func(a: Actor, res: DamageResult, _pt: Vector3) -> void: on_hit.call(a, res)
	Audio.play_at(&"cast_fire" if element == Elements.FIRE else &"swing_light", from, -8.0)

func _cut() -> void:
	FX.spawn_facing(VFXLib.slash_arc(Color(0.8, 0.7, 1.0, 0.7), reach, 330.0, 0.9, 0.2, 0.4), global_position, Vector3.FORWARD.rotated(Vector3.UP, randf() * TAU))
	if request == null or not is_inside_tree():
		return
	var src: Node = source if is_instance_valid(source) else null
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, reach, mask):
		var r := request.clone()
		r.tags[&"aoe"] = true
		r.tags[&"push_dir"] = (a.global_position - global_position).slide(Vector3.UP).normalized()
		var res := a.receive_hit(r, src, a.center())
		if on_hit.is_valid():
			on_hit.call(a, res)
	Audio.play_at(&"swing_light", global_position, -10.0)
