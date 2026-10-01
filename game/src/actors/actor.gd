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
var _enemy_retaliation_cd := 0.0
const ENEMY_RETALIATION_HP_CAP := 0.08
const ENEMY_RETALIATION_COOLDOWN := 0.5
var _vertical := 0.0
var _airborne_from_launch := false
var shield_hp := 0.0                      # absorbs damage (Radiant Ward, elite ward)
var last_attacker: Node
var rng := RandomNumberGenerator.new()
var invulnerable := false                 # dodge i-frames, cutscenes
var _stats_dirty := true
## Physics LOD (bh-014): a body standing on the floor with nowhere to go skips its capsule sweep, re-checking the floor
## every REST_CHECK steps (staggered). In a brawl half the monsters are swinging or waiting their turn in place, and
## each sweep cost as much as a moving one. Monsters opt in; the hero always sweeps.
var rest_skip := false
const REST_CHECK := 6
var _rest_n := 0

func _resting(horiz: Vector3) -> bool:
	if horiz.x * horiz.x + horiz.z * horiz.z > 0.0025 or _vertical > -0.5 or not is_on_floor() or _airborne_from_launch:
		_rest_n = 0
		return false
	_rest_n += 1
	if _rest_n % REST_CHECK == get_instance_id() % REST_CHECK:
		return false
	velocity = Vector3.ZERO
	return true

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

## Fighting recently (the hero and Tempos override this; monsters read it to hear combat).
func in_combat() -> bool:
	return false

## The animation-driven action in progress, if any (Player, Enemy and Tempo each keep one in `action`).
func current_action() -> TimedAction:
	return get(&"action") as TimedAction

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
	var enemy_retaliation: bool = team != BH.Team.ENEMY and attacker is Actor and attacker.team == BH.Team.ENEMY and req.tags.has(&"thorns")
	if enemy_retaliation:
		# One shared window per victim, so cleaving a pack cannot stack lethal returns.
		if _enemy_retaliation_cd > 0.0:
			return DamageResult.new()
		req.tags[&"retaliation_limit"] = maxf(1.0, floorf(max_hp() * ENEMY_RETALIATION_HP_CAP))
	if req.graze and team == BH.Team.ENEMY:
		req.evadable = false        # bh-028: grazing area hits is the heroes' (and their allies') art, not the monsters'
	_positional_bonuses(req, attacker)
	_prepare_incoming(req, attacker)
	_threat_guard(req)
	if attacker is Player:
		attacker.class_passives.before_hit(req)
	var result := DamagePipeline.compute(req, rng)
	if enemy_retaliation and result.total > 0:
		_enemy_retaliation_cd = ENEMY_RETALIATION_COOLDOWN
	if attacker != null:
		last_attacker = attacker
	_apply_result(result, req, attacker, hit_point)
	if is_instance_valid(attacker) and attacker is Player:
		attacker.class_passives.after_hit(self, req, result)
	return result

## Attacker passives that depend on this target (bh-010): Ruthless (low-HP targets) and Opportunist (from behind).
func _positional_bonuses(req: DamageRequest, attacker: Node) -> void:
	var st := req.attacker
	if st == null or req.kind == DamageRequest.Kind.DOT:
		return
	# Champion-slaying gear (bh-012): more damage against elites, champions and bosses
	var ed := st.get_stat(&"elite_damage")
	if ed > 0.0 and (get(&"is_elite") == true or get(&"is_boss") == true or (has_method(&"is_miniboss") and call(&"is_miniboss"))):
		req.more.append(["Champion-slaying", 1.0 + ed])
	if st.has_flag(&"execute") and hp < max_hp() * 0.35:
		req.more.append(["Ruthless", 1.0 + st.flag(&"execute")])
	if st.has_flag(&"backstab") and attacker is Node3D:
		var to_att := (attacker as Node3D).global_position - global_position
		to_att.y = 0.0
		if to_att.length() > 0.05 and forward().dot(to_att.normalized()) < -0.3:
			req.more.append(["Opportunist", 1.0 + st.flag(&"backstab")])

## bh-028: hero-against-hero scaling and the lethal-blow guard (CombatBudget). Heroes, their companions and arena
## combatants are guarded; monsters are not.
func _threat_guard(req: DamageRequest) -> void:
	req.tags.erase(&"blow_cap")
	var atk := req.attacker
	if atk == null or req.kind == DamageRequest.Kind.DOT:
		return
	var monster := team == BH.Team.ENEMY and not is_arena_hero()
	if monster:
		return
	if atk.get_stat(&"hero_source") > 0.0:
		# a hero's blow on another hero (or an arena adventurer)
		if not req.tags.has(&"pvp_scaled"):
			req.tags[&"pvp_scaled"] = true
			req.more.append(["Arena", CombatBudget.pvp_mult(atk.level)])
		req.tags[&"blow_cap"] = maxf(1.0, max_hp() * CombatBudget.PVP_BLOW_CAP)
	else:
		req.tags[&"blow_cap"] = maxf(1.0, max_hp() * CombatBudget.blow_cap(int(atk.get_stat(&"threat_rank"))))

## True for a hero fighting in the Sand Arena (bh-028): blows between such heroes are scaled and capped.
func is_arena_hero() -> bool:
	return false

## HP per second from auras and passives (Aura of Mending, Second Wind); regeneration code adds it.
func aura_regen() -> float:
	return max_hp() * status.magnitude(&"aura_mending") + status.magnitude(&"second_wind")

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
		hp = minf(max_hp(), hp + result.healed * status.heal_taken_mult())
	status.receive_hit(result)
	health_changed.emit(hp, max_hp())
	hit_taken.emit(result)
	Events.damage_dealt.emit(self, result, pos, attacker)
	if attacker is Actor and result.leech > 0.0 and attacker.alive:
		attacker.heal(result.leech, false)
	# Aura of Thorns and Thorns gear (bh-012): melee attackers take damage back (never from projectiles, spells or
	# reflections).
	var thorn_flat := stats.get_stat(&"thorns") if stats else 0.0
	if (status.has(&"aura_thorns") or thorn_flat > 0.0) and attacker is Actor and attacker != self and attacker.alive and result.total > 0 			and req.kind == DamageRequest.Kind.ATTACK and not req.tags.has(&"projectile") and not req.tags.has(&"thorns"):
		var tr := DamageRequest.new()
		tr.kind = DamageRequest.Kind.SPELL
		tr.attacker = stats
		tr.base_min = float(result.total) * (status.magnitude(&"aura_thorns") if status.has(&"aura_thorns") else 0.0) + thorn_flat
		tr.base_max = tr.base_min
		tr.can_crit = false
		tr.evadable = false
		tr.blockable = false
		tr.label = "Thorns"
		tr.tags[&"thorns"] = true
		(attacker as Actor).receive_hit(tr, self, (attacker as Actor).center())
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
	amount *= status.heal_taken_mult()
	if amount <= 0.0:
		return
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

## Which death animation to play (enemies choose one from the killing blow).
func death_clip() -> StringName:
	return &"death"

func die(killer: Node) -> void:
	if not alive:
		return
	alive = false
	hp = 0.0
	set_meta(&"died_frozen", status.has(&"frozen"))
	set_meta(&"died_burning", status.has(&"burning"))
	status.clear()
	if visual:
		visual.play_death(death_clip())
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
	_enemy_retaliation_cd = maxf(0.0, _enemy_retaliation_cd - delta)
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
	if rest_skip and _resting(horiz):
		return
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
