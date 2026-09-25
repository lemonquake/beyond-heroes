class_name Actor
extends CharacterBody3D
## Base for the player and enemies: HP/mana pools, statuses, damage intake through the DamagePipeline,
## knockback physics with wall/body impact damage, and hit reactions.

signal died(killer: Node)
signal health_changed(hp: float, max_hp: float)
signal mana_changed(mana: float, max_mana: float)
signal hit_taken(result: DamageResult)

const GRAVITY := 22.0
const KNOCK_FRICTION := 9.0          # m/s^2 horizontal deceleration while knocked back (plus velocity-proportional drag)
const KNOCK_DRAG := 2.2
const KNOCKED_THRESHOLD := 3.5       # above this knock speed the actor loses control
const HEAVY_KNOCK := 9.0             # above this the full knockback animation plays
const IMPACT_MIN_SPEED := 5.5        # m/s into a surface before an impact deals damage
const IMPACT_COOLDOWN := 0.3
const IMPACT_HP_CAP := 0.35          # impact damage never exceeds 35% of the victim's max HP per collision
const IMPACT_TRANSFER := 0.6         # share of momentum passed to a body we crash into
const MAX_CHAIN_DEPTH := 1           # a transferred knock cannot transfer again (no chain reactions)
const SURFACE_SEVERITY := {&"stone": 1.0, &"wood": 0.7, &"flesh": 0.55, &"metal": 1.1, &"earth": 0.8}

var team := BH.Team.ENEMY
var display_name := ""
var level := 1
var stats: DerivedStats
var status := StatusController.new()
var hp := 1.0
var mana := 0.0
var alive := true
var weight := 1.0
var body_radius := 0.45
var body_height := 1.8
var visual: CharacterVisual
var affinity := Elements.PHYSICAL

var knock_velocity := Vector3.ZERO
var knock_source: DerivedStats            # stats of whoever launched us (for impact damage scaling)
var knock_source_node: Node
var knock_depth := 0
var _impact_cd := 0.0
var _vertical := 0.0
var _airborne_from_launch := false
var shield_hp := 0.0                      # absorbs damage (Radiant Ward, elite ward)
var last_attacker: Node
var rng := RandomNumberGenerator.new()
var invulnerable := false                 # dodge i-frames, cutscenes
var _stats_dirty := true

func _ready() -> void:
	rng.seed = hash(get_instance_id())
	status.dot_tick.connect(_on_dot_tick)
	status.changed.connect(mark_stats_dirty)
	status.staggered.connect(_on_staggered)
	status.status_added.connect(_on_status_added)
	status.status_removed.connect(_on_status_removed)
	floor_max_angle = deg_to_rad(50.0)
	floor_snap_length = 0.4

func mark_stats_dirty() -> void:
	_stats_dirty = true

## Subclasses rebuild `stats` here (hero data or enemy def + runtime modifiers).
func rebuild_stats() -> void:
	pass

func ensure_stats() -> void:
	if _stats_dirty or stats == null:
		_stats_dirty = false
		var old_max := stats.get_stat(&"max_hp") if stats != null else 0.0
		var old_mana_max := stats.get_stat(&"max_mana") if stats != null else 0.0
		rebuild_stats()
		status.status_res = stats.get_stat(&"status_res")
		status.max_poise = stats.get_stat(&"poise", 30.0)
		var mx := stats.get_stat(&"max_hp")
		if old_max > 0.0 and mx != old_max:
			hp = clampf(hp * mx / old_max, 1.0 if alive else 0.0, mx)
		hp = minf(hp, mx)
		var mm := stats.get_stat(&"max_mana")
		if old_mana_max > 0.0 and mm != old_mana_max:
			mana = clampf(mana * mm / old_mana_max, 0.0, mm)
		mana = minf(mana, mm)
		health_changed.emit(hp, mx)
		mana_changed.emit(mana, mm)

func max_hp() -> float:
	return stats.get_stat(&"max_hp", 1.0) if stats else 1.0

func max_mana() -> float:
	return stats.get_stat(&"max_mana", 0.0) if stats else 0.0

func is_disabled() -> bool:
	return not alive or status.is_disabled() or knock_velocity.length() > KNOCKED_THRESHOLD

func forward() -> Vector3:
	return global_transform.basis.z

func face_toward(point: Vector3, weight_t := 1.0) -> void:
	var d := point - global_position
	d.y = 0.0
	if d.length_squared() < 0.0001:
		return
	var target_yaw := atan2(d.x, d.z)
	rotation.y = lerp_angle(rotation.y, target_yaw, clampf(weight_t, 0.0, 1.0))

func center() -> Vector3:
	return global_position + Vector3.UP * body_height * 0.55

# ---- Damage intake ---------------------------------------------------------------------------------------

## Resolve a hit through the single pipeline and apply exactly the number it returns.
func receive_hit(req: DamageRequest, attacker: Node = null, hit_point := Vector3.INF) -> DamageResult:
	ensure_stats()
	if not alive:
		return DamageResult.new()
	if invulnerable and req.kind != DamageRequest.Kind.DOT:
		var r0 := DamageResult.new()
		r0.evaded = true
		Events.damage_dealt.emit(self, r0, center(), attacker)
		return r0
	req.target = stats
	req.target_status = status
	req.target_weight = weight
	_prepare_incoming(req, attacker)
	var result := DamagePipeline.compute(req, rng)
	if attacker != null:
		last_attacker = attacker
	_apply_result(result, req, attacker, hit_point)
	return result

## Hook for subclasses: guard/parry state, weak points, elite wards...
func _prepare_incoming(_req: DamageRequest, _attacker: Node) -> void:
	pass

func _apply_result(result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	var pos := hit_point if hit_point != Vector3.INF else center()
	if result.evaded:
		Events.damage_dealt.emit(self, result, pos, attacker)
		_on_evaded(attacker)
		return
	var dmg := float(result.total)
	if shield_hp > 0.0 and dmg > 0.0:
		var absorbed := minf(shield_hp, dmg)
		shield_hp -= absorbed
		# The shown number stays the pipeline total; absorbed part is tracked for UI.
		dmg -= absorbed
		if shield_hp <= 0.0:
			_on_shield_broken()
	hp = maxf(0.0, hp - dmg)
	if result.healed > 0:
		hp = minf(max_hp(), hp + result.healed)
	status.receive_hit(result)
	health_changed.emit(hp, max_hp())
	hit_taken.emit(result)
	Events.damage_dealt.emit(self, result, pos, attacker)
	if attacker is Actor and result.leech > 0.0 and attacker.alive:
		attacker.heal(result.leech, false)
	if hp <= 0.0:
		die(attacker)
		# Corpses still fly: apply knockback after death for satisfying ragdoll-like throws.
		if result.knockback > 0.0 and attacker is Node3D:
			apply_knockback(_knock_dir(attacker, req), result.knockback * 1.2, req.attacker, attacker, 0, req.tags.get(&"launch", 0.0))
		return
	if result.knockback > 0.0 and attacker is Node3D:
		apply_knockback(_knock_dir(attacker, req), result.knockback, req.attacker, attacker, 0, req.tags.get(&"launch", 0.0))
	_on_damaged(result, req)

func _knock_dir(attacker: Node3D, req: DamageRequest) -> Vector3:
	var dir: Vector3 = req.tags.get(&"push_dir", Vector3.ZERO)
	if dir == Vector3.ZERO:
		dir = global_position - attacker.global_position
	dir.y = 0.0
	if dir.length_squared() < 0.0001:
		dir = -forward()
	return dir.normalized()

func _on_damaged(_result: DamageResult, _req: DamageRequest) -> void:
	pass

func _on_evaded(_attacker: Node) -> void:
	pass

func _on_shield_broken() -> void:
	pass

func _on_dot_tick(id: StringName, amount: float, element: int) -> void:
	if not alive:
		return
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.DOT
	req.base_min = amount
	req.base_max = amount
	req.conversion = {element: 1.0} if element != Elements.PHYSICAL else {}
	req.can_crit = false
	req.evadable = false
	req.blockable = false
	req.label = String(id)
	receive_hit(req, null)

func _on_staggered(_broken: bool) -> void:
	if visual:
		visual.play_reaction(&"stagger")

func _on_status_added(id: StringName) -> void:
	if visual:
		visual.set_status_visual(id, true)

func _on_status_removed(id: StringName) -> void:
	if visual:
		visual.set_status_visual(id, false)

func heal(amount: float, show := true) -> void:
	if not alive or amount <= 0.0:
		return
	if status.has(&"purged"):
		amount *= 0.5
	var before := hp
	hp = minf(max_hp(), hp + amount)
	health_changed.emit(hp, max_hp())
	if show and hp - before >= 1.0:
		FX.heal_number(center() + Vector3.UP * 0.4, roundi(hp - before))

func restore_mana(amount: float) -> void:
	mana = clampf(mana + amount, 0.0, max_mana())
	mana_changed.emit(mana, max_mana())

func spend_mana(amount: float) -> bool:
	if mana + 0.001 < amount:
		return false
	mana -= amount
	mana_changed.emit(mana, max_mana())
	return true

func die(killer: Node) -> void:
	if not alive:
		return
	alive = false
	hp = 0.0
	status.clear()
	if visual:
		visual.play_death()
	collision_layer = 0
	collision_mask = BH.LAYER_WORLD
	died.emit(killer)
	Events.actor_died.emit(self, killer)

# ---- Knockback & impact physics ---------------------------------------------------------------------------

func apply_knockback(dir: Vector3, speed: float, source: DerivedStats, source_node: Node, depth := 0, launch := 0.0) -> void:
	if not is_finite(speed) or speed <= 0.0:
		return
	if stats and stats.has_flag(&"unstaggerable"):
		speed *= 0.4
	var v := dir.normalized() * minf(speed, DamagePipeline.MAX_KNOCKBACK)
	# Replace rather than accumulate beyond the cap: the stronger push wins.
	var combined := knock_velocity + v
	if combined.length() > DamagePipeline.MAX_KNOCKBACK:
		combined = combined.normalized() * DamagePipeline.MAX_KNOCKBACK
	knock_velocity = combined
	knock_source = source
	knock_source_node = source_node
	knock_depth = depth
	if launch > 0.0 and weight < 4.0:
		_vertical = maxf(_vertical, launch / sqrt(maxf(weight, 0.5)))
		_airborne_from_launch = true
	if visual and alive:
		if speed >= HEAVY_KNOCK or launch > 0.0:
			visual.play_reaction(&"knockback")
		elif speed >= KNOCKED_THRESHOLD:
			visual.play_reaction(&"hit")

## Called every physics frame by subclasses with their intended (controlled) horizontal velocity.
func physics_move(delta: float, desired: Vector3) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_impact_cd = maxf(0.0, _impact_cd - delta)
	# Knockback decay: constant friction + drag, so strong hits travel far but settle predictably.
	var ks := knock_velocity.length()
	if ks > 0.0:
		var dec := (KNOCK_FRICTION + KNOCK_DRAG * ks) * delta
		knock_velocity = knock_velocity * maxf(0.0, ks - dec) / ks
		if knock_velocity.length() < 0.05:
			knock_velocity = Vector3.ZERO
	var control := 0.0 if knock_velocity.length() > KNOCKED_THRESHOLD else 1.0
	var horiz := desired * control + knock_velocity
	if is_on_floor() and _vertical <= 0.0:
		_vertical = -1.0
		if _airborne_from_launch:
			_airborne_from_launch = false
			_on_landed()
	else:
		_vertical -= GRAVITY * delta
	velocity = Vector3(horiz.x, _vertical, horiz.z)
	if not velocity.is_finite():
		velocity = Vector3.ZERO
		knock_velocity = Vector3.ZERO
		_vertical = 0.0
	var pre_knock := knock_velocity
	move_and_slide()
	if pre_knock.length() > 1.0:
		_process_impacts(pre_knock)
	if global_position.y < -40.0:
		_fell_out()

func _on_landed() -> void:
	if visual and alive:
		visual.play_reaction(&"land")
	Events.impact.emit(global_position, 0.4 * weight, &"earth")

func _fell_out() -> void:
	die(null)

func _process_impacts(pre_knock: Vector3) -> void:
	for i in get_slide_collision_count():
		var col := get_slide_collision(i)
		var n := col.get_normal()
		if n.y > 0.7:
			continue  # floor
		var into := -pre_knock.dot(n)
		if into <= 1.0:
			continue
		var other := col.get_collider()
		if other is Actor:
			_body_impact(other, pre_knock, into, n)
		elif other != null and other.has_method("take_impact"):
			other.take_impact(pre_knock, col.get_position(), knock_source)
			knock_velocity *= 0.55
		elif into >= IMPACT_MIN_SPEED and _impact_cd <= 0.0:
			var surface: StringName = other.get_meta(&"surface", &"stone") if other != null else &"stone"
			_wall_impact(into, n, col.get_position(), surface)
		# Remove the into-surface component; small bounce so bodies don't stick.
		knock_velocity += n * into * 1.25
		knock_velocity.y = 0.0

## Impact Damage = (knockback velocity into surface - threshold) x collision severity x attacker impact modifier
##               x target weight modifier x surface modifier, capped per collision.
static func impact_damage_amount(into_speed: float, surface_mod: float, source_level: int, weight_mod: float, impact_mult: float) -> float:
	var over := maxf(0.0, into_speed - IMPACT_MIN_SPEED)
	var severity := over * (3.0 + 1.2 * float(source_level))
	return severity * surface_mod * weight_mod * impact_mult

func _wall_impact(into: float, normal: Vector3, point: Vector3, surface: StringName) -> void:
	_impact_cd = IMPACT_COOLDOWN
	var src_level := knock_source.level if knock_source else level
	var impact_mult := knock_source.get_stat(&"impact_strength", 1.0) if knock_source else 1.0
	var weight_mod := sqrt(clampf(weight, 0.5, 9.0))
	var amt := impact_damage_amount(into, SURFACE_SEVERITY.get(surface, 1.0), src_level, weight_mod, impact_mult)
	if knock_source and status.has(&"frozen"):
		amt *= 1.0 + knock_source.flag(&"frozen_impact")
	amt = minf(amt, max_hp() * IMPACT_HP_CAP)
	Events.impact.emit(point, into, surface)
	Audio.play_at(&"wall_impact", point, lerpf(-6.0, 3.0, clampf(into / 20.0, 0.0, 1.0)))
	Events.camera_shake.emit(clampf(into / 40.0, 0.05, 0.35))
	if amt >= 1.0:
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.IMPACT
		req.attacker = knock_source
		req.base_min = amt
		req.base_max = amt
		req.poise = into * 3.0
		req.label = "Wall impact"
		receive_hit(req, knock_source_node, point)

func _body_impact(other: Actor, pre_knock: Vector3, into: float, normal: Vector3) -> void:
	if not other.alive:
		return
	if into < 3.0 or _impact_cd > 0.0:
		return
	_impact_cd = IMPACT_COOLDOWN
	# Momentum transfer weighted by mass ratio; a transferred push may not transfer again.
	if knock_depth < MAX_CHAIN_DEPTH and other.team == team:
		var transfer := IMPACT_TRANSFER
		if knock_source and knock_source.has_flag(&"full_transfer"):
			transfer = 1.0
		var mass_ratio := clampf(weight / maxf(other.weight, 0.25), 0.2, 2.0)
		var push := -normal * into * transfer * mass_ratio
		other.apply_knockback(push, push.length(), knock_source, knock_source_node, knock_depth + 1)
	if into >= IMPACT_MIN_SPEED:
		var src_level := knock_source.level if knock_source else level
		var impact_mult := knock_source.get_stat(&"impact_strength", 1.0) if knock_source else 1.0
		var amt := impact_damage_amount(into, SURFACE_SEVERITY[&"flesh"], src_level, sqrt(clampf(weight, 0.5, 9.0)), impact_mult) * 0.6
		for a in [self, other]:
			var capped := minf(amt, a.max_hp() * IMPACT_HP_CAP)
			if capped >= 1.0:
				var req := DamageRequest.new()
				req.kind = DamageRequest.Kind.IMPACT
				req.attacker = knock_source
				req.base_min = capped
				req.base_max = capped
				req.poise = into * 2.0
				req.label = "Body impact"
				a.receive_hit(req, knock_source_node, (global_position + other.global_position) * 0.5 + Vector3.UP)
		Audio.play_at(&"hit_heavy", global_position)
		Events.impact.emit((global_position + other.global_position) * 0.5, into, &"flesh")
