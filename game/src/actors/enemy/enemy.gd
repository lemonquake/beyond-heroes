class_name Enemy
extends Actor
## A monster in the world: EnemyDef data + level + elite modifiers + the EnemyBrain state machine.
##
## Perception: distance, line of sight, vision cone, combat noise, damage taken, pack calls.
## Decisions ("think", every ~0.2 s, staggered): per archetype — grunts take ring slots and wait for an attack token,
## tanks guard casters and raise shields, ranged/casters keep distance and seek line of sight, assassins flank,
## brutes press in with telegraphed high-impact attacks, supports stay with allies and heal/empower them, bosses run
## phase patterns. Status (stagger, freeze, stun) and knockback interrupt everything.
## Attacks are animation-driven TimedActions; damage lands only in hit windows / release frames, through the pipeline.

signal state_changed(state: int)

const THINK_INTERVAL := 0.2
const LOS_INTERVAL := 0.3
const SEPARATION_RADIUS := 1.6
const TURN_RATE := 8.0
const RETURN_HEAL_RATE := 0.25

var def: EnemyDef
var brain := EnemyBrain.new()
var elite_mods: Array[StringName] = []
var is_elite := false
var is_boss := false
var difficulty := {}
var home := Vector3.ZERO
var patrol_radius := 5.0
var zone: Node3D
var agent: NavigationAgent3D
var target: Player
var bar: EnemyBar

var action: TimedAction
var current_attack := {}
var cooldowns := {}                  # attack/ability id -> seconds
var phase := 1
var enraged := false
var _think_t := 0.0
var _los_t := 0.0
var _has_los := false
var _dist := INF
var _move_target := Vector3.INF
var _strafe_dir := 1.0
var _strafe_t := 0.0
var _defend_t := 0.0
var _charge := {}                    # active charge: {dir, speed, left, hit}
var _pulse_t := 0.0
var _spark_cd := 0.0
var _regen_block := 0.0
var _elite_t := 0.0
var _last_hit_t := 99.0
var _idle_sound_t := 0.0
var _think_offset := 0.0
var _phase_lock := 0.0
var _anim_pref: StringName = &""

func setup(p_def: EnemyDef, p_level: int, mods: Array = [], p_difficulty := {}) -> Enemy:
	def = p_def
	level = maxi(1, p_level)
	difficulty = p_difficulty if not p_difficulty.is_empty() else DataEnemies.DIFFICULTY[1]
	for m in mods:
		elite_mods.append(StringName(m))
	is_elite = not elite_mods.is_empty()
	is_boss = def.archetype == &"boss"
	display_name = def.display_name
	if is_elite:
		var prefix := []
		for m in elite_mods:
			prefix.append(DB.elite_mods[m].name)
		display_name = "%s %s" % [" ".join(prefix), def.display_name]
	weight = def.weight * (1.2 if is_elite else 1.0)
	body_radius = def.body_radius
	body_height = def.body_height
	affinity = def.affinity
	return self

func _ready() -> void:
	super._ready()
	team = BH.Team.ENEMY
	add_to_group(&"enemy")
	if is_boss:
		add_to_group(&"boss")
	collision_layer = BH.LAYER_ENEMY
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_PLAYER | BH.LAYER_ENEMY
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = body_radius
	cap.height = maxf(body_height, body_radius * 2.0 + 0.1)
	cs.shape = cap
	cs.position.y = cap.height * 0.5
	add_child(cs)
	agent = NavigationAgent3D.new()
	agent.path_desired_distance = 0.9
	agent.target_desired_distance = 0.6
	agent.path_height_offset = 0.3
	agent.radius = body_radius
	agent.avoidance_enabled = false
	add_child(agent)
	visual = CharacterVisual.new()
	visual.name = "Visual"
	add_child(visual)
	var sc := def.model_scale * (1.12 if is_elite else 1.0)
	visual.setup(def.model, sc, def.tint, &"")
	if visual.fallback:
		_shape_fallback()
	visual.set_stance(_idle_anim())
	for sid in def.status_immune:
		status.immunities[StringName(sid)] = true
	status.grants_stagger_window = is_elite or is_boss
	mark_stats_dirty()
	ensure_stats()
	hp = max_hp()
	if is_elite:
		_apply_elite_visuals()
		if stats.has_flag(&"ward"):
			shield_hp = max_hp() * stats.flag(&"ward")
			status.apply(&"elite_shield", 0.0)
	home = global_position
	bar = EnemyBar.new()
	bar.setup(self)
	add_child(bar)
	_think_offset = rng.randf() * THINK_INTERVAL
	_think_t = _think_offset
	_strafe_dir = 1.0 if rng.randf() < 0.5 else -1.0
	brain.go(EnemyBrain.State.PATROL if patrol_radius > 0.5 and not is_boss else EnemyBrain.State.IDLE)

func _shape_fallback() -> void:
	match def.body_shape:
		&"quadruped":
			visual.model.rotation.x = -PI * 0.5
			visual.model.position = Vector3(0, 0.55, 0.6)
			visual.model.scale = Vector3(1.0, 0.8, 0.7)
		&"floating":
			visual.model.scale = Vector3.ONE * 0.6
			visual.model.position.y = 0.6
			visual.add_child(VFXLib.orb(def.tint, 0.35, true))

func _idle_anim() -> StringName:
	match def.archetype:
		&"shield": return &"idle_shield"
		&"ranged": return &"idle_bow"
		&"caster", &"support": return &"idle_staff"
		&"brute", &"boss": return &"idle_2h"
		&"assassin": return &"idle_dagger"
	return &"idle_1h"

# ---- Stats ---------------------------------------------------------------------------------------------------

func rebuild_stats() -> void:
	var mods := status.stat_modifiers()
	for m in elite_mods:
		var em: Dictionary = DB.elite_mods.get(m, {})
		for sm in em.get("mods", []):
			mods.append(sm)
		var fl: Dictionary = em.get("flags", {})
		for f in fl:
			mods.append(StatModifier.flat(StringName("flag_" + String(f)), float(fl[f]), em.name))
		var rs: Dictionary = em.get("res", {})
		for e in rs:
			mods.append(StatModifier.flat(Elements.res_key(int(e)), float(rs[e]), em.name))
	if stats and stats.has_flag(&"leech"):
		mods.append(StatModifier.flat(&"life_leech", stats.flag(&"leech")))
	if stats and stats.has_flag(&"berserk") and hp > 0.0:
		var missing := 1.0 - hp / max_hp()
		mods.append(StatModifier.more(&"outgoing_damage", stats.flag(&"berserk") * missing))
		mods.append(StatModifier.more(&"attack_speed", 0.3 * missing))
	if enraged:
		mods.append(StatModifier.more(&"attack_speed", 0.2))
		mods.append(StatModifier.more(&"move_speed", 0.15))
	stats = EnemyStats.build(def, level, difficulty, mods, is_elite, is_boss)

# ---- Main loop -----------------------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	ensure_stats()
	status.tick(delta)
	if not alive:
		physics_move(delta, Vector3.ZERO)
		return
	brain.tick(delta)
	_tick_cooldowns(delta)
	_elite_tick(delta)
	if target == null or not is_instance_valid(target):
		target = Game.player as Player
	_update_interrupts()
	if action:
		if not action.step(delta):
			_end_attack(true)
	_think_t -= delta
	if _think_t <= 0.0:
		_think_t += THINK_INTERVAL
		_think(THINK_INTERVAL)
	var desired := _steer(delta)
	if not _charge.is_empty():
		desired = _charge_step(delta)
	physics_move(delta, desired)
	_face(delta, desired)
	if visual:
		var hv := Vector3(velocity.x, 0, velocity.z)
		var local := global_transform.basis.inverse() * hv
		visual.update_locomotion(Vector2(local.x, local.z), brain.is_engaged(), 0.0, delta)
	_ambient_sound(delta)

func _tick_cooldowns(delta: float) -> void:
	for k in cooldowns.keys():
		cooldowns[k] -= delta
		if cooldowns[k] <= 0.0:
			cooldowns.erase(k)
	_last_hit_t += delta
	_regen_block = maxf(0.0, _regen_block - delta)
	_phase_lock = maxf(0.0, _phase_lock - delta)

func is_aggressive() -> bool:
	return brain.is_engaged()

## Stagger / knockback / disable interrupt any state.
func _update_interrupts() -> void:
	var S := EnemyBrain.State
	if status.is_disabled():
		if brain.state != S.STAGGER:
			_interrupt()
			brain.go(S.STAGGER)
		return
	if knock_velocity.length() > KNOCKED_THRESHOLD or _airborne_from_launch:
		if brain.state != S.KNOCKBACK:
			_interrupt()
			brain.go(S.KNOCKBACK)
		return
	if brain.state == S.STAGGER or brain.state == S.KNOCKBACK:
		if brain.time_in_state > 0.25 and (visual == null or not visual.is_busy()):
			brain.go(S.POSITION if target and target.alive else S.CHASE)

func _interrupt() -> void:
	if action:
		action.finish(false)
		action = null
	_charge = {}
	if CombatDirector.current:
		CombatDirector.current.release_token(self)
	current_attack = {}

# ---- Perception ----------------------------------------------------------------------------------------------

func _perceive(dt: float) -> void:
	if target == null or not target.alive:
		_dist = INF
		_has_los = false
		brain.perceive(false, INF, def.sight_range, dt)
		return
	_dist = global_position.distance_to(target.global_position)
	_los_t -= dt
	if _los_t <= 0.0:
		_los_t = LOS_INTERVAL
		_has_los = _dist < def.sight_range * 1.5 and not CombatQuery.blocked(get_world_3d(), center(), target.center())
	var sees := _has_los and _dist < def.sight_range
	if sees and not brain.is_engaged():
		var to := target.global_position - global_position
		to.y = 0.0
		sees = forward().angle_to(to.normalized()) < deg_to_rad(def.fov_degrees * 0.5) or _dist < 4.0
	var heard := target.in_combat() and _dist < def.hearing_range
	brain.perceive(sees, _dist, def.sight_range, dt, heard)
	if sees or heard:
		brain.last_known = target.global_position
	if _dist < def.aggro_range * 0.35 and _has_los:
		brain.awareness = 1.0

func alert_to(pos: Vector3) -> void:
	brain.awareness = 1.0
	brain.last_known = pos
	if not brain.is_engaged() and alive:
		_become_alert(false)

func _become_alert(call_pack := true) -> void:
	var S := EnemyBrain.State
	if brain.go(S.ALERT):
		visual.play_action(&"alert" if not is_boss else &"boss_roar", 1.0)
		Events.enemy_alerted.emit(self)
		if def.sounds.has("idle"):
			Audio.play_at(def.sounds.idle, global_position)
		if is_boss:
			Events.boss_engaged.emit(self)
		if call_pack and def.pack_call:
			for e in get_tree().get_nodes_in_group(&"enemy"):
				if e != self and e.alive and e.global_position.distance_to(global_position) < 11.0:
					e.alert_to(brain.last_known)

# ---- Thinking ------------------------------------------------------------------------------------------------

func _think(dt: float) -> void:
	_perceive(dt)
	var S := EnemyBrain.State
	match brain.state:
		S.IDLE, S.PATROL:
			if brain.awareness >= 1.0:
				_become_alert()
			elif brain.awareness > 0.35:
				brain.go(S.SUSPICIOUS)
			elif brain.state == S.PATROL:
				_patrol()
			elif brain.time_in_state > 4.0 and patrol_radius > 0.5:
				brain.go(S.PATROL)
		S.SUSPICIOUS:
			if brain.awareness >= 1.0:
				_become_alert()
			elif brain.awareness <= 0.05 or brain.time_in_state > 8.0:
				brain.go(S.PATROL)
				_move_target = home
			else:
				_move_target = brain.last_known
		S.ALERT:
			if brain.time_in_state > 0.55:
				brain.go(S.CHASE)
		S.CHASE, S.POSITION, S.RETREAT, S.DEFEND:
			_combat_think()
		S.ATTACK, S.SPECIAL, S.CAST:
			pass

func _patrol() -> void:
	if _move_target == Vector3.INF or global_position.distance_to(_move_target) < 1.0 or brain.time_in_state > 6.0:
		var ang := rng.randf() * TAU
		_move_target = home + Vector3(cos(ang), 0, sin(ang)) * rng.randf_range(0.5, patrol_radius)
		brain.time_in_state = 0.0

func _combat_think() -> void:
	var S := EnemyBrain.State
	if target == null or not target.alive:
		_release()
		brain.go(S.PATROL if brain.state != S.DEFEND else S.POSITION)
		if brain.state == S.POSITION:
			brain.go(S.PATROL)
		_move_target = home
		brain.awareness = 0.0
		return
	# Leash: lose interest far from home (bosses never leash).
	if not is_boss and global_position.distance_to(home) > def.leash_range:
		_release()
		brain.awareness = 0.0
		brain.go(S.PATROL)
		_move_target = home
		return
	if is_boss:
		_boss_phase_check()
	var arche := def.archetype
	# Support: heal/buff allies before anything else.
	if arche == &"support" and _try_ability():
		return
	if def.abilities.size() > 0 and arche != &"support" and _try_ability():
		return
	# Ranged / casters keep their distance.
	if arche in [&"ranged", &"caster", &"support"] and def.retreat_range > 0.0 and _dist < def.retreat_range:
		brain.go(S.RETREAT)
		_move_target = _retreat_point()
		if brain.time_in_state < 1.4:
			return
	# Shield bearers raise their guard when the hero is winding up nearby.
	if def.blocks_front and target.action != null and _dist < 4.0 and rng.randf() < 0.55 * float(difficulty.get("aggression", 1.0)):
		if brain.go(S.DEFEND):
			_defend_t = rng.randf_range(0.8, 1.6)
			visual.set_upper(&"block_loop")
			return
	if brain.state == S.DEFEND:
		_defend_t -= THINK_INTERVAL
		if _defend_t > 0.0 and target.action != null:
			return
		visual.set_upper(&"")
	var atk := _choose_attack()
	if not atk.is_empty():
		var kind: StringName = &"ranged" if atk.kind in ["projectile"] else &"melee"
		var forced: bool = is_boss or atk.kind in ["aoe", "summon", "pools"] and is_elite
		if _has_los and CombatDirector.current and CombatDirector.current.request_token(self, kind, forced):
			_start_attack(atk)
			return
	# No attack now: move into position.
	brain.go(S.POSITION if _dist < _engage_distance() else S.CHASE)
	_move_target = _position_goal()

func _engage_distance() -> float:
	return def.preferred_range + 3.5

func _release() -> void:
	if CombatDirector.current:
		CombatDirector.current.release_token(self)
		CombatDirector.current.release_slot(self)

func _position_goal() -> Vector3:
	var arche := def.archetype
	var pr := def.preferred_range
	if arche in [&"ranged", &"caster", &"support"]:
		# keep preferred distance with line of sight; supports stay behind their allies
		var to := global_position - target.global_position
		to.y = 0.0
		var goal := target.global_position + to.normalized() * pr
		if arche == &"support":
			var ally := _nearest_ally(14.0)
			if ally:
				var behind := ally.global_position + (ally.global_position - target.global_position).slide(Vector3.UP).normalized() * 3.0
				goal = behind
		if not _has_los:
			goal = goal.lerp(target.global_position, 0.35)
		return goal
	if CombatDirector.current == null:
		return target.global_position
	var guard: Node3D = null
	if arche == &"shield":
		guard = CombatDirector.caster_to_protect(self, get_tree().get_nodes_in_group(&"enemy"))
	var holds := CombatDirector.current.has_token(self)
	var radius := pr + (0.2 if holds else 1.4 + 0.6 * float(get_instance_id() % 3))
	return CombatDirector.current.slot_position(self, target, radius, def.flanker, guard)

func _retreat_point() -> Vector3:
	var away := global_position - target.global_position
	away.y = 0.0
	var dir := away.normalized() if away.length() > 0.1 else -forward()
	var p := global_position + dir.rotated(Vector3.UP, rng.randf_range(-0.6, 0.6)) * 5.0
	return CombatQuery.reachable_point(get_world_3d(), global_position, p, body_radius)

func _nearest_ally(r: float) -> Enemy:
	var best: Enemy = null
	var bd := r * r
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e == self or not e.alive or e.def.archetype in [&"support"]:
			continue
		var d: float = e.global_position.distance_squared_to(global_position)
		if d < bd:
			bd = d
			best = e
	return best

# ---- Attacks -------------------------------------------------------------------------------------------------

func _choose_attack() -> Dictionary:
	var candidates := []
	var total := 0.0
	for a in def.attacks:
		var id: StringName = a.id
		if cooldowns.has(id):
			continue
		if int(a.get("phase", 1)) > phase:
			continue
		var rng_m := float(a.get("range", 2.0)) + body_radius
		if _dist > rng_m or _dist < float(a.get("min_range", 0.0)):
			continue
		if a.kind in ["projectile", "aoe", "charge", "dash"] and not _has_los:
			continue
		var w := float(a.get("weight", 1.0))
		if a.kind in ["aoe", "charge", "pools", "summon"]:
			w *= 1.5
		candidates.append([a, w])
		total += w
	if candidates.is_empty():
		return {}
	# aggression makes enemies commit sooner; reaction delay makes them wait a moment after entering range
	if brain.time_in_state < float(difficulty.get("reaction", 0.25)) and brain.state == EnemyBrain.State.CHASE:
		return {}
	var r := rng.randf() * total
	for c in candidates:
		r -= c[1]
		if r <= 0.0:
			return c[0]
	return candidates[0][0]

func _attack_request(a: Dictionary) -> DamageRequest:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK if a.kind in ["melee", "dash", "charge"] else DamageRequest.Kind.SPELL
	req.attacker = stats
	req.use_weapon = false
	var rr := EnemyStats.attack_range(def, stats, float(a.get("mult", 1.0)))
	req.base_min = rr.x
	req.base_max = rr.y
	var el := int(a.get("element", Elements.PHYSICAL))
	if el != Elements.PHYSICAL:
		req.conversion = {el: 1.0}
		if req.kind == DamageRequest.Kind.ATTACK:
			req.conversion = {el: 0.6}
	req.knockback = float(a.get("knockback", 2.0))
	req.poise = float(a.get("poise", 8.0))
	req.label = "%s: %s" % [def.display_name, a.id]
	req.evadable = a.kind in ["melee", "dash", "projectile"]
	var st: Dictionary = a.get("status", {})
	for sid in st:
		req.direct_status[StringName(sid)] = float(st[sid])
	if stats.has_flag(&"burn_on_hit"):
		req.conversion[Elements.FIRE] = 0.3
		req.direct_status[&"burning"] = req.direct_status.get(&"burning", 0.0) + 40.0
	if stats.has_flag(&"armor_break_hit"):
		req.direct_status[&"armor_broken"] = 60.0
	if stats.has_flag(&"curse_on_hit"):
		req.direct_status[&"cursed"] = 50.0
		req.direct_status[&"weakened"] = 50.0
	if el == Elements.ICE or elite_mods.has(&"frozen"):
		req.direct_status[&"chilled"] = req.direct_status.get(&"chilled", 0.0) + 30.0
	return req

func _start_attack(a: Dictionary) -> void:
	var S := EnemyBrain.State
	var special: bool = a.kind in ["aoe", "charge", "pools", "summon", "dash"]
	var st: int = S.CAST if def.archetype in [&"caster", &"support"] and a.kind != "melee" else (S.SPECIAL if special else S.ATTACK)
	if not brain.go(st):
		return
	current_attack = a
	var cd := float(a.get("cooldown", 2.0)) / float(difficulty.get("skill_rate", 1.0))
	cooldowns[a.id] = cd * rng.randf_range(0.9, 1.15)
	_face_now(target.global_position)
	var rate := stats.get_stat(&"attack_speed", 1.0)
	var anim: StringName = a.get("anim", &"sword_1")
	var windup := float(a.get("windup", 0.0)) / rate
	var act := TimedAction.from_anim(anim, rate)
	# Telegraphed attacks: the whole animation is delayed by the windup, so the impact lands after the marker fills.
	if windup > 0.0:
		act.windows = act.windows.map(func(w): return [w[0] + windup, w[1] + windup])
		act.release_t = act.release_t + windup if act.release_t >= 0.0 else windup
		act.duration += windup
		visual.play_action(&"charge_hold" if a.kind in ["melee", "dash", "charge"] else &"cast_channel", 1.0)
		get_tree().create_timer(windup, false).timeout.connect(func() -> void:
			if alive and action == act:
				visual.play_action(anim, rate))
	else:
		visual.play_action(anim, rate)
	action = act
	act.move_mult = 0.0
	var aim_at := target.global_position
	match String(a.kind):
		"melee":
			act.on_window = func(w: int, first: bool) -> void: _melee_hit(a, act, w)
			if act.windows.is_empty():
				act.on_release = func() -> void: _melee_hit(a, act, 0)
		"projectile":
			act.on_release = func() -> void: _fire(a)
		"aoe":
			var center := global_position if a.get("self_centered", false) else aim_at
			if a.has("offset"):
				center = global_position + forward() * float(a.offset)
			var total_delay: float = act.release_t if act.release_t >= 0.0 else (act.windows[0][0] if not act.windows.is_empty() else 0.8)
			total_delay = maxf(total_delay, windup)
			_telegraph_aoe(a, center, total_delay)
		"dash":
			var dist := minf(float(a.get("dash", 5.0)), _dist)
			var t_hit := maxf(0.1, act.first_hit_time())
			_charge = {"dir": (aim_at - global_position).slide(Vector3.UP).normalized(), "speed": dist / maxf(t_hit - windup, 0.1), "left": t_hit - windup, "delay": windup, "hit": false, "a": a, "lunge": true}
			act.on_window = func(w: int, first: bool) -> void: _melee_hit(a, act, w)
		"charge":
			var dir := (aim_at - global_position).slide(Vector3.UP).normalized()
			var length := minf(float(a.get("range", 20.0)), _dist + 4.0)
			var tele := VFXLib.telegraph("line", Vector2(length, float(a.get("width", 2.5))), windup, Color(1.0, 0.25, 0.1, 0.75))
			FX.spawn(tele, global_position)
			tele.rotation.y = atan2(dir.x, dir.z)
			get_tree().create_timer(windup + 0.05, false).timeout.connect(tele.queue_free)
			if a.get("stationary", false):
				act.on_release = func() -> void:
					var sw := AreaEffects.sweep(FX.world, global_position + dir, dir, float(a.get("speed", 30.0)), length, float(a.get("width", 2.0)), _attack_request(a), self, BH.LAYER_PLAYER)
					sw.trail_fx = func(pos: Vector3) -> void: FX.spawn(VFXLib.light_flash(Elements.color(int(a.get("element", 0))), 2.0, 3.0, 0.2), pos + Vector3.UP)
			else:
				_charge = {"dir": dir, "speed": float(a.get("speed", 14.0)), "left": length / float(a.get("speed", 14.0)), "delay": windup, "hit": false, "a": a}
				visual.hold_action(&"boss_charge" if is_boss or def.archetype == &"brute" else &"run_combat")
		"pools":
			act.on_release = func() -> void: _pools(a)
		"summon":
			act.on_release = func() -> void: _summon(a)
	Audio.play_at(&"swing_heavy" if special else &"swing_light", global_position, -4.0)

func _melee_hit(a: Dictionary, act: TimedAction, w: int) -> void:
	if target == null or not target.alive:
		return
	var reach := float(a.get("range", 2.0)) + body_radius * 0.5
	var arc := float(a.get("arc", 100.0))
	if not act.mark_hit(w, target):
		return
	if target.global_position.distance_to(global_position) > reach + target.body_radius:
		return
	var to := target.global_position - global_position
	to.y = 0.0
	if forward().angle_to(to.normalized()) > deg_to_rad(arc * 0.5) + atan2(target.body_radius, maxf(to.length(), 0.1)):
		return
	var req := _attack_request(a)
	req.tags[&"push_dir"] = to.normalized()
	target.receive_hit(req, self, target.center())
	FX.spawn(VFXLib.slash_arc(Color(1.0, 0.5, 0.4, 0.6), reach, arc, 1.0, 0.2, 0.5), global_position)

func _fire(a: Dictionary) -> void:
	if target == null:
		return
	var count := int(a.get("count", 1))
	var spread := float(a.get("spread", 0.0))
	var speed := float(a.get("speed", 16.0))
	var from := center() + forward() * (body_radius + 0.3)
	# lead the target a little on higher difficulties
	var lead := float(difficulty.get("aggression", 1.0)) - 0.85
	var aim := target.center() + target.velocity * clampf(lead, 0.0, 0.6) * (from.distance_to(target.center()) / speed)
	var dir := (aim - from)
	dir.y = 0.0
	dir = dir.normalized()
	var el := int(a.get("element", Elements.PHYSICAL))
	var look := "arrow" if a.get("projectile", "") == "arrow" else "orb"
	for i in count:
		var ang := 0.0 if count == 1 else lerpf(-spread * 0.5, spread * 0.5, float(i) / float(count - 1))
		var pr := Projectile.spawn(FX.world, from, dir.rotated(Vector3.UP, deg_to_rad(ang)), speed, _attack_request(a), self, BH.LAYER_PLAYER, el, look)
		pr.max_range = float(a.get("range", 15.0)) + 4.0
		pr.radius = 0.3
		pr.hit_sound = &"arrow_impact" if look == "arrow" else Elements.SFX_HIT[el]

func _telegraph_aoe(a: Dictionary, at: Vector3, delay: float) -> void:
	var shape := String(a.get("telegraph", "circle"))
	var radius := float(a.get("radius", 3.0))
	var req := _attack_request(a)
	var el := int(a.get("element", Elements.PHYSICAL))
	if shape == "cone":
		var tele := VFXLib.telegraph("cone", Vector2(radius, radius), delay, Color(1.0, 0.25, 0.1, 0.75), float(a.get("arc", 120.0)))
		FX.spawn(tele, global_position)
		tele.rotation.y = rotation.y + PI
		var arc := float(a.get("arc", 120.0))
		get_tree().create_timer(delay, false).timeout.connect(func() -> void:
			tele.queue_free()
			if not alive or target == null:
				return
			for t: Actor in CombatQuery.actors_in_arc(get_world_3d(), global_position, forward(), radius, arc, BH.LAYER_PLAYER):
				var r := req.clone()
				r.tags[&"push_dir"] = (t.global_position - global_position).slide(Vector3.UP).normalized()
				t.receive_hit(r, self, t.center())
			FX.spawn(VFXLib.slash_arc(Color(1.0, 0.45, 0.3, 0.8), radius, arc, 1.2, 0.3, 0.7), global_position)
			Events.camera_shake.emit(0.3))
		return
	var blast := AreaEffects.delayed(FX.world, CombatQuery.ground_at(get_world_3d(), at), radius, delay, req, self, BH.LAYER_PLAYER,
		Color(1.0, 0.25, 0.1, 0.75), "ring" if shape == "ring" else "circle", float(a.get("inner_radius", 0.0)))
	blast.on_blast = func(pos: Vector3, _hits: Array) -> void:
		var c := Elements.color(el) if el != Elements.PHYSICAL else Color(0.85, 0.7, 0.5)
		FX.spawn(VFXLib.ring_wave(c, radius, 0.45, 0.8), pos)
		FX.spawn(VFXLib.dust_puff(1.0), pos)
		Events.camera_shake.emit(0.35 if is_boss else 0.2)
		Events.impact.emit(pos, 12.0, &"earth")
		Audio.play_at(&"boss_slam" if is_boss else &"earth_quake", pos)

func _pools(a: Dictionary) -> void:
	if target == null:
		return
	var count := int(a.get("count", 4))
	var req := _attack_request(a)
	req.kind = DamageRequest.Kind.SPELL
	req.base_min *= 0.3
	req.base_max *= 0.3
	req.knockback = 0.0
	for i in count:
		var off := Vector3(rng.randf_range(-5, 5), 0, rng.randf_range(-5, 5)) if i > 0 else Vector3.ZERO
		var at := CombatQuery.ground_at(get_world_3d(), target.global_position + off)
		var delay := float(a.get("windup", 1.0))
		var blast := AreaEffects.delayed(FX.world, at, float(a.get("radius", 2.5)), delay, null, self, BH.LAYER_PLAYER, Color(0.6, 0.2, 0.9, 0.7))
		blast.on_blast = func(pos: Vector3, _h: Array) -> void:
			AreaEffects.hazard(FX.world, pos, float(a.get("radius", 2.5)), float(a.get("duration", 6.0)), req, self, BH.LAYER_PLAYER, Color(0.55, 0.15, 0.85), 0.5)

func _summon(a: Dictionary) -> void:
	var edef := DB.enemy(a.get("summon", &"hollow_soldier"))
	if edef == null:
		return
	for i in int(a.get("count", 2)):
		var ang := TAU * float(i) / float(a.get("count", 2))
		var p := global_position + Vector3(cos(ang), 0, sin(ang)) * 4.0
		p = CombatQuery.reachable_point(get_world_3d(), global_position, p)
		var e := Spawner.spawn_enemy(get_parent(), edef, maxi(1, level - 2), [], CombatQuery.ground_at(get_world_3d(), p), difficulty)
		e.alert_to(target.global_position if target else global_position)
		FX.spawn(VFXLib.particles(Color(0.5, 0.2, 0.8, 0.8), 24, 0.8, true, 0.5, 3.0, 60.0, Vector3(0, 2, 0), 0.6), p)
	Audio.play_at(&"dark_cast", global_position)

func _end_attack(completed: bool) -> void:
	action = null
	current_attack = {}
	if CombatDirector.current:
		CombatDirector.current.release_token(self)
	var S := EnemyBrain.State
	if brain.is_busy():
		brain.go(S.POSITION)
	if completed and def.archetype == &"assassin" and target:
		# hit and run: back off after striking
		_move_target = _retreat_point()
		brain.go(S.RETREAT)

func _charge_step(delta: float) -> Vector3:
	if _charge.get("delay", 0.0) > 0.0:
		_charge.delay -= delta
		return Vector3.ZERO
	_charge.left -= delta
	var v: Vector3 = _charge.dir * float(_charge.speed)
	if not _charge.hit and target and target.alive and not _charge.get("lunge", false):
		if target.global_position.distance_to(global_position) < body_radius + target.body_radius + 0.8:
			_charge.hit = true
			var req := _attack_request(_charge.a)
			req.tags[&"push_dir"] = _charge.dir
			target.receive_hit(req, self, target.center())
	# A charging boss that slams into a wall or an impact pillar stuns itself.
	if not _charge.get("lunge", false):
		for i in get_slide_collision_count():
			var col := get_slide_collision(i)
			if col.get_normal().y < 0.5 and absf(col.get_normal().dot(_charge.dir)) > 0.6:
				var other := col.get_collider()
				_charge_crash(other, col.get_position())
				return Vector3.ZERO
	if _charge.left <= 0.0:
		_charge = {}
		visual.stop_action()
		return Vector3.ZERO
	return v

func _charge_crash(other: Object, point: Vector3) -> void:
	_charge = {}
	visual.stop_action()
	var pillar := other is Node and (other as Node).is_in_group(&"arena_pillar")
	if other != null and other.has_method(&"take_hit"):
		other.take_hit(200.0, forward() * 8.0)
	Events.camera_shake.emit(0.6)
	Events.impact.emit(point, 22.0, &"stone")
	Audio.play_at(&"wall_impact", point, 4.0)
	if is_boss and pillar:
		status.immunities.erase(&"stunned")
		status.apply(&"stunned", 3.0)
		status.apply(&"stagger_window", 5.0)
		status.immunities[&"stunned"] = true
		Events.notify.emit("The Warden is stunned!", &"info")
	else:
		status.apply(&"staggered", 1.2)

# ---- Support abilities --------------------------------------------------------------------------------------------

func _try_ability() -> bool:
	for ab in def.abilities:
		if cooldowns.has(ab.id):
			continue
		match String(ab.kind):
			"heal":
				var hurt: Enemy = null
				var worst := 0.7
				for e in get_tree().get_nodes_in_group(&"enemy"):
					if e.alive and e.global_position.distance_to(global_position) < float(ab.range) and e.hp / e.max_hp() < worst:
						worst = e.hp / e.max_hp()
						hurt = e
				if hurt:
					_cast_ability(ab, func() -> void:
						if is_instance_valid(hurt) and hurt.alive:
							hurt.heal(hurt.max_hp() * float(ab.amount))
							FX.spawn(VFXLib.beam(Color(1.0, 0.6, 0.3), 3.0, 0.6), hurt.global_position)
							FX.spawn(VFXLib.particles(Color(1.0, 0.7, 0.3, 0.9), 20, 0.8, true, 0.4, 2.0, 40.0, Vector3(0, 3, 0), 0.5), hurt.center()))
					return true
			"buff":
				var allies := []
				for e in get_tree().get_nodes_in_group(&"enemy"):
					if e != self and e.alive and e.brain.is_engaged() and e.global_position.distance_to(global_position) < float(ab.range):
						allies.append(e)
				if allies.size() >= 1:
					_cast_ability(ab, func() -> void:
						for e in allies:
							if is_instance_valid(e) and e.alive:
								e.status.apply(StringName(ab.status), float(ab.duration))
						FX.spawn(VFXLib.ring_wave(Color(1.0, 0.5, 0.2, 0.9), float(ab.range) * 0.5, 0.6), global_position))
					return true
			"teleport":
				if target and _dist < def.retreat_range + 1.0:
					cooldowns[ab.id] = float(ab.cooldown)
					var p := _retreat_point()
					FX.spawn(VFXLib.particles(def.tint, 20, 0.4, true, 0.35, 4.0, 180.0, Vector3.ZERO, 0.4), center())
					global_position = CombatQuery.ground_at(get_world_3d(), p)
					FX.spawn(VFXLib.particles(def.tint, 20, 0.4, true, 0.35, 4.0, 180.0, Vector3.ZERO, 0.4), center())
					Audio.play_at(&"blink", global_position)
					return true
	return false

func _cast_ability(ab: Dictionary, effect: Callable) -> void:
	var S := EnemyBrain.State
	if not brain.go(S.CAST):
		return
	cooldowns[ab.id] = float(ab.cooldown)
	var act := TimedAction.from_anim(ab.get("anim", &"cast_area"), 1.0)
	act.on_release = effect
	action = act
	visual.play_action(act.anim, 1.0)
	Audio.play_at(&"cultist_chant", global_position, -2.0)

# ---- Movement ------------------------------------------------------------------------------------------------

func _steer(delta: float) -> Vector3:
	var S := EnemyBrain.State
	if brain.state in [S.ATTACK, S.SPECIAL, S.CAST, S.STAGGER, S.KNOCKBACK, S.ALERT, S.DEAD, S.IDLE] or action != null:
		return Vector3.ZERO
	var speed := stats.get_stat(&"move_speed", 3.5) * float(difficulty.get("aggression", 1.0)) ** 0.3
	match brain.state:
		S.PATROL:
			speed *= 0.35
		S.SUSPICIOUS:
			speed *= 0.5
		S.DEFEND:
			speed *= 0.3
		S.RETREAT:
			speed *= 0.9
	if _move_target == Vector3.INF:
		return Vector3.ZERO
	var goal := _move_target
	var to_goal := goal - global_position
	to_goal.y = 0.0
	var v := Vector3.ZERO
	if to_goal.length() > 0.5:
		agent.target_position = goal
		var nxt := agent.get_next_path_position()
		var d := nxt - global_position
		d.y = 0.0
		if d.length() < 0.05 or agent.is_navigation_finished():
			d = to_goal
		v = d.normalized() * speed
	elif brain.state == S.POSITION and target:
		# waiting for a token: circle the hero at the slot radius
		_strafe_t -= delta
		if _strafe_t <= 0.0:
			_strafe_t = rng.randf_range(1.2, 2.6)
			_strafe_dir = -_strafe_dir if rng.randf() < 0.35 else _strafe_dir
		var r := global_position - target.global_position
		r.y = 0.0
		v = r.normalized().cross(Vector3.UP) * _strafe_dir * speed * 0.35
	# separation: avoid clipping through allies and stacking on the same spot
	var sep := Vector3.ZERO
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e == self or not e.alive:
			continue
		var off: Vector3 = global_position - e.global_position
		off.y = 0.0
		var min_d := SEPARATION_RADIUS + body_radius + e.body_radius - 0.9
		var l := off.length()
		if l < min_d and l > 0.001:
			sep += off / l * (min_d - l) / min_d
	if target and target.alive:
		var off2 := global_position - target.global_position
		off2.y = 0.0
		var min2 := body_radius + target.body_radius + 0.25
		if off2.length() < min2:
			sep += off2.normalized() * 1.5
	v += sep * speed * 0.9
	var cur := Vector3(velocity.x, 0, velocity.z) - Vector3(knock_velocity.x, 0, knock_velocity.z)
	return cur.move_toward(v.limit_length(speed * 1.1), 30.0 * delta)

func _face(delta: float, desired: Vector3) -> void:
	var S := EnemyBrain.State
	var look := Vector3.ZERO
	if brain.is_engaged() and target and brain.state != S.RETREAT and _charge.is_empty():
		if action != null and action.elapsed > action.first_hit_time() - 0.05:
			return   # committed: no tracking after the swing starts
		look = target.global_position - global_position
	elif desired.length() > 0.3:
		look = desired
	elif not _charge.is_empty():
		look = _charge.dir
	look.y = 0.0
	if look.length() > 0.1:
		rotation.y = lerp_angle(rotation.y, atan2(look.x, look.z), clampf(TURN_RATE * delta, 0.0, 1.0))

func _face_now(p: Vector3) -> void:
	var d := p - global_position
	d.y = 0.0
	if d.length() > 0.05:
		rotation.y = atan2(d.x, d.z)

# ---- Damage intake ------------------------------------------------------------------------------------------------

func _prepare_incoming(req: DamageRequest, attacker: Node) -> void:
	# Shield bearers block frontal hits while defending (and randomly otherwise); heavy/impact hits break the guard.
	if def.blocks_front and attacker is Node3D and req.blockable and req.kind != DamageRequest.Kind.DOT and req.kind != DamageRequest.Kind.IMPACT:
		var to: Vector3 = (attacker as Node3D).global_position - global_position
		to.y = 0.0
		var frontal := forward().angle_to(to.normalized()) < deg_to_rad(70.0)
		var S := EnemyBrain.State
		var defending := brain.state == S.DEFEND
		if frontal and (defending or (not brain.is_busy() and rng.randf() < 0.35)):
			if req.heavy and req.poise >= def.guard_break * 0.6:
				status.apply(&"staggered")
				FX.text_popup(center() + Vector3.UP, "Guard Break", UITheme.GOLD, 1.1)
			else:
				req.guarding = true
	if stats.has_flag(&"ward") and shield_hp > 0.0 and req.conversion.has(Elements.LIGHT):
		req.tags[&"ward_light"] = true

func _apply_result(result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if shield_hp > 0.0 and req.tags.get(&"ward_light", false):
		shield_hp = maxf(0.0, shield_hp - result.components.get(Elements.LIGHT, 0.0))
	super._apply_result(result, req, attacker, hit_point)
	if result.evaded:
		return
	_last_hit_t = 0.0
	_regen_block = 3.0 if result.components.get(Elements.FIRE, 0.0) > 0.0 else _regen_block
	if alive and attacker is Player:
		if not brain.is_engaged():
			alert_to(attacker.global_position)
		if stats.has_flag(&"sparks") and _spark_cd <= 0.0 and rng.randf() < 0.35:
			_spark_cd = 1.0
			_spark(attacker)
	if result.total > 0 and def.sounds.has("hurt"):
		Audio.play_at(def.sounds.hurt, global_position, -2.0)
	if bar:
		bar.touch()

func _on_damaged(result: DamageResult, req: DamageRequest) -> void:
	if result.total <= 0 or visual == null:
		return
	if knock_velocity.length() >= KNOCKED_THRESHOLD or status.is_disabled():
		return
	var heavy := result.poise_damage > stats.get_stat(&"poise", 30.0) * 0.4 or result.is_crit
	if action == null or heavy and not is_boss:
		visual.play_reaction(&"hit_heavy" if heavy else &"hit", &"front")

func _on_staggered(_broken: bool) -> void:
	_interrupt()
	if visual:
		visual.play_reaction(&"stagger_heavy" if is_elite or is_boss else &"stagger")
	Audio.play_at(&"stagger", global_position)
	if is_boss or is_elite:
		FX.text_popup(center() + Vector3.UP * 1.2, "Staggered!", UITheme.GOLD, 1.2)

func _on_shield_broken() -> void:
	status.remove(&"elite_shield")
	FX.text_popup(center() + Vector3.UP, "Ward Broken", Color(0.6, 0.7, 1.0), 1.1)
	Audio.play_at(&"shatter_ice", global_position)

func _spark(to: Node3D) -> void:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = stats
	var rr := EnemyStats.attack_range(def, stats, 0.4)
	req.base_min = rr.x
	req.base_max = rr.y
	req.conversion = {Elements.LIGHTNING: 1.0}
	req.label = "Storm sparks"
	var pr := Projectile.spawn(FX.world, center(), (to.global_position - global_position).slide(Vector3.UP).normalized().rotated(Vector3.UP, rng.randf_range(-1.2, 1.2)), 9.0, req, self, BH.LAYER_PLAYER, Elements.LIGHTNING, "orb_nolight")
	pr.homing = 2.5
	pr.homing_target = to
	pr.max_range = 16.0
	pr.radius = 0.25

func die(killer: Node) -> void:
	if not alive:
		return
	_interrupt()
	super.die(killer)
	brain.go(EnemyBrain.State.DEAD)
	if CombatDirector.current:
		CombatDirector.current.forget(self)
	if def.sounds.has("death"):
		Audio.play_at(def.sounds.death, global_position)
	if bar:
		bar.queue_free()
		bar = null
	remove_from_group(&"enemy")
	if stats.has_flag(&"death_fire"):
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = stats
		var rr := EnemyStats.attack_range(def, stats, 0.25)
		req.base_min = rr.x
		req.base_max = rr.y
		req.conversion = {Elements.FIRE: 1.0}
		req.label = "Burning ground"
		AreaEffects.hazard(FX.world, global_position, 2.6, 5.0, req, null, BH.LAYER_PLAYER, Color(1.0, 0.4, 0.1))
	if stats.has_flag(&"explode"):
		var req2 := DamageRequest.new()
		req2.kind = DamageRequest.Kind.SPELL
		req2.attacker = stats
		var r2 := EnemyStats.attack_range(def, stats, 2.0)
		req2.base_min = r2.x
		req2.base_max = r2.y
		req2.conversion = {Elements.FIRE: 0.5}
		req2.knockback = 12.0
		req2.label = "Volatile explosion"
		var b := AreaEffects.delayed(FX.world, global_position, 3.2, 1.2, req2, null, BH.LAYER_PLAYER)
		b.on_blast = func(pos: Vector3, _h: Array) -> void:
			FX.spawn(VFXLib.ring_wave(Color(1.0, 0.55, 0.2), 3.2, 0.4), pos)
			FX.spawn(VFXLib.light_flash(Color(1.0, 0.6, 0.3), 6.0, 8.0, 0.3), pos + Vector3.UP)
			Audio.play_at(&"explode", pos)
			Events.camera_shake.emit(0.35)
	if is_boss:
		Events.boss_defeated.emit(self)
	# fade the corpse after a while
	get_tree().create_timer(12.0 if not is_boss else 60.0, false).timeout.connect(_sink)

func _sink() -> void:
	if not is_instance_valid(self):
		return
	var tw := create_tween()
	tw.tween_property(self, "position:y", position.y - 1.5, 2.5)
	tw.tween_callback(queue_free)

# ---- Elites, bosses, ambience -------------------------------------------------------------------------------------

func _apply_elite_visuals() -> void:
	var c: Color = DB.elite_mods[elite_mods[0]].color
	visual.set_rim(c, 0.9)
	var aura := VFXLib.particles(Color(c.r, c.g, c.b, 0.7), 22, 1.1, false, 0.4, 0.9, 20.0, Vector3(0, 1.4, 0), body_radius + 0.2)
	aura.position.y = 0.1
	add_child(aura)
	var ring := VFXLib.telegraph("ring", Vector2(body_radius + 0.45, body_radius + 0.45), 0.01, Color(c.r, c.g, c.b, 0.6), 360.0, body_radius + 0.2)
	add_child(ring)
	Events.elite_spawned.emit(self)

func _elite_tick(delta: float) -> void:
	_spark_cd = maxf(0.0, _spark_cd - delta)
	if not is_elite or not brain.is_engaged():
		return
	_elite_t += delta
	if stats.has_flag(&"regen") and not status.has(&"purged") and _regen_block <= 0.0 and hp < max_hp():
		heal(max_hp() * stats.flag(&"regen") * delta, false)
	if stats.has_flag(&"berserk") and int(_elite_t * 2.0) != int((_elite_t - delta) * 2.0):
		mark_stats_dirty()
	if stats.has_flag(&"frost_pulse"):
		_pulse_t += delta
		if _pulse_t >= 6.0:
			_pulse_t = 0.0
			var req := DamageRequest.new()
			req.kind = DamageRequest.Kind.SPELL
			req.attacker = stats
			var rr := EnemyStats.attack_range(def, stats, 0.5)
			req.base_min = rr.x
			req.base_max = rr.y
			req.conversion = {Elements.ICE: 1.0}
			req.direct_status[&"chilled"] = 70.0
			req.label = "Frost pulse"
			AreaEffects.delayed(FX.world, global_position, 4.0, 0.8, req, self, BH.LAYER_PLAYER, Color(0.55, 0.85, 1.0, 0.7))
	if (stats.has_flag(&"aether_blink") or stats.has_flag(&"aether_bolts")) and target and action == null:
		if int(_elite_t) % 8 == 0 and int(_elite_t - delta) % 8 != 0 and stats.has_flag(&"aether_blink"):
			var side := target.global_position + target.global_transform.basis.x * (2.5 if rng.randf() < 0.5 else -2.5)
			side = CombatQuery.reachable_point(get_world_3d(), target.global_position, side, body_radius)
			FX.spawn(VFXLib.particles(Color(0.6, 0.98, 1.0, 0.9), 20, 0.4, true, 0.35, 4.0, 180.0, Vector3.ZERO, 0.4), center())
			global_position = CombatQuery.ground_at(get_world_3d(), side)
			Audio.play_at(&"blink", global_position)
		if int(_elite_t) % 6 == 3 and int(_elite_t - delta) % 6 != 3 and stats.has_flag(&"aether_bolts"):
			_fire({"id": &"aether_bolt", "mult": 0.6, "element": Elements.LIGHT, "count": 3, "spread": 30.0, "speed": 15.0, "range": 16.0, "projectile": "orb", "knockback": 1.0, "poise": 4.0})

func _boss_phase_check() -> void:
	if def.phases.is_empty() or _phase_lock > 0.0:
		return
	var frac := hp / max_hp()
	var want := 1
	for i in def.phases.size():
		if frac <= float(def.phases[i].hp) + 0.0001:
			want = i + 1
	if want > phase:
		phase = want
		_phase_lock = 2.5
		_interrupt()
		brain.go(EnemyBrain.State.POSITION)
		visual.play_action(&"boss_roar", 1.0)
		invulnerable = true
		get_tree().create_timer(1.6, false).timeout.connect(func() -> void: invulnerable = false)
		Events.boss_phase.emit(self, phase)
		Events.camera_shake.emit(0.5)
		Audio.play_at(&"boss_phase", global_position, 3.0)
		FX.spawn(VFXLib.ring_wave(Color(0.6, 0.2, 0.9), 8.0, 0.8, 1.0), global_position)
		if phase >= def.phases.size():
			enraged = true
			mark_stats_dirty()
		for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, 7.0, BH.LAYER_PLAYER):
			a.apply_knockback((a.global_position - global_position).slide(Vector3.UP).normalized(), 12.0, stats, self)

func phase_name() -> String:
	if def.phases.is_empty():
		return ""
	return String(def.phases[clampi(phase - 1, 0, def.phases.size() - 1)].get("name", ""))

func _ambient_sound(delta: float) -> void:
	_idle_sound_t -= delta
	if _idle_sound_t <= 0.0:
		_idle_sound_t = rng.randf_range(6.0, 14.0)
		if def.sounds.has("idle") and brain.state in [EnemyBrain.State.IDLE, EnemyBrain.State.PATROL] and target and global_position.distance_to(target.global_position) < 18.0:
			Audio.play_at(def.sounds.idle, global_position, -10.0)

func debug_text() -> String:
	return "%s L%d %s  aw %.2f  %s%s" % [def.id, level, brain.state_name(), brain.awareness,
		"TOKEN " if CombatDirector.current and CombatDirector.current.has_token(self) else "", "P%d" % phase if is_boss else ""]
