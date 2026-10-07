class_name CurseZone
extends Node3D
## bh-042: Curse of Stillness, the Abyss bosses' anti-magic sigil (docs/PLAN_bh-042.md, phase 2). A ground circle fills
## for `delay` seconds; then for `duration` seconds no hero or Tempo standing in it can cast a spell (`stilled`,
## refreshed every tick while they stand inside; weapon skills still work). The moment it wakes it also bursts once
## (`request`). A copy made on another machine (multiplayer, `request` null) still stills that machine's own hero, so a
## guest is cursed by what they see; hits stay with the boss's owner.

const TICK := 0.2
const COLOR := Color(0.2, 0.95, 0.85)
const DARK := Color(0.05, 0.25, 0.3)

var source: Node
var request: DamageRequest
var mask := BH.LAYER_PLAYER
var radius := 6.0
var delay := 1.0
var duration := 6.0
var local_only := false
var _t := 0.0
var _tick := 0.0
var _woke := false
var _told := {}
var _sigil: MeshInstance3D
var _pulse := 0.0

static func cast(parent: Node, at: Vector3, p_radius: float, p_delay: float, p_duration: float, req: DamageRequest, src: Node,
		p_mask := BH.LAYER_PLAYER, p_local_only := false) -> CurseZone:
	var z := CurseZone.new()
	Perf.mark_fx(z)
	z.radius = p_radius
	z.delay = p_delay
	z.duration = p_duration
	z.request = req
	z.source = src
	z.mask = p_mask
	z.local_only = p_local_only
	parent.add_child(z)
	z.global_position = at
	z.add_to_group(&"curse_zone")
	var tele := VFXLib.telegraph("circle", Vector2(p_radius, p_radius), p_delay, Color(COLOR.r, COLOR.g, COLOR.b, 0.6))
	z.add_child(tele)
	z.get_tree().create_timer(p_delay + 0.05, false).timeout.connect(tele.queue_free)
	return z

## True while the sigil is awake and `p` stands inside it.
func covers(p: Vector3) -> bool:
	return _woke and _t < delay + duration and Vector2(p.x - global_position.x, p.z - global_position.z).length() <= radius

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	if not _woke:
		if _t < delay:
			return
		_wake()
	if _t >= delay + duration:
		_fade()
		return
	_pulse -= delta
	if _pulse <= 0.0:
		_pulse = 0.9
		FX.spawn(VFXLib.ring_wave(Color(COLOR.r, COLOR.g, COLOR.b, 0.55), radius, 0.9, 0.3), global_position)
	if _sigil:
		_sigil.rotate_y(delta * 0.6)
	_tick -= delta
	if _tick > 0.0:
		return
	_tick = TICK
	for a in _victims():
		a.status.apply(&"stilled", 0.6)
		var id: int = a.get_instance_id()
		if not _told.has(id):
			_told[id] = true
			FX.text_popup(a.center() + Vector3.UP * 0.9, "Silenced!", COLOR, 1.0)

func _victims() -> Array:
	var out := []
	if local_only:
		var p := Game.player as Actor
		if p and is_instance_valid(p) and p.alive and covers(p.global_position):
			out.append(p)
		return out
	var world := get_world_3d()
	if world == null:
		return out
	for a: Actor in CombatQuery.actors_in_radius(world, global_position, radius, mask):
		if a == source or not a.alive or a is NetAvatar:
			continue                         # a guest is stilled by their own copy of the sigil
		if covers(a.global_position):
			out.append(a)
	return out

func _wake() -> void:
	_woke = true
	_sigil = VFXLib.telegraph("ring", Vector2(radius, radius), 0.01, Color(COLOR.r, COLOR.g, COLOR.b, 0.42), 360.0, 0.9)
	_sigil.position.y = 0.05
	add_child(_sigil)
	var inner := VFXLib.telegraph("circle", Vector2(radius, radius), 0.01, Color(DARK.r, DARK.g, DARK.b, 0.35))
	inner.position.y = 0.03
	add_child(inner)
	var motes := VFXLib.particles(Color(COLOR.r, COLOR.g, COLOR.b, 0.85), int(14 + radius * 5), 1.6, false, 0.18, 1.1, 20.0, Vector3(0, 1.2, 0), radius * 0.85)
	motes.position.y = 0.15
	add_child(motes)
	FX.spawn(VFXLib.light_flash(COLOR, 4.0, radius + 2.0, 0.35), global_position + Vector3.UP)
	Audio.play_at(&"dark_cast", global_position)
	if request != null and not local_only:
		AreaEffects.burst(self, global_position, radius, mask, request, source if is_instance_valid(source) else null)

func _fade() -> void:
	set_physics_process(false)
	for c in get_children():
		if c is GPUParticles3D:
			(c as GPUParticles3D).emitting = false
		elif c is MeshInstance3D:
			var tw := (c as MeshInstance3D).create_tween()
			tw.tween_property(c, "scale", Vector3(0.01, 1.0, 0.01), 0.4)
	get_tree().create_timer(0.7, false).timeout.connect(queue_free)
