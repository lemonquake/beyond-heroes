class_name Tempo
extends Actor
## A Tempo in the world: the spirit of a fallen warrior fighting beside the hero (docs/LORE.md §9). Reads its TempoData
## (who it is, what it wears) and mirrors half its hero's strength (TempoRules.compute).
##
## The spirit thinks every THINK seconds and reacts to danger every DANGER_SCAN seconds. Priorities, highest first:
##   1. Get out of harm's way — telegraphed blasts, boss swings and charges, lingering hazards, incoming projectiles:
##      a dodge roll (i-frames) when the blow is about to land, otherwise walking out of the marked area.
##   2. Mend — a Tempo with a healing skill heals the hero first (sooner when the hero is badly hurt), then the other
##      Tempo, then itself.
##   3. Fall back — below its personality's retreat threshold it disengages behind the hero, uses an escape skill if it
##      has one, and rests (regenerates quickly) until it is fit to fight, or until the hero is in mortal danger.
##   4. Defend — it picks the monster that matters most: whatever is hitting the hero, casters and healers, the wounded,
##      whatever it already fights (with hysteresis so it does not flicker between targets).
##   5. Fight by role (the class's `ai`) — vanguards (Swordsmen, Wardens) stand between the monster and the hero,
##      taunt crowds off the hero, cleave, charge and ward; marksmen and casters (Archers, Mystics) hold range with line
##      of sight, rain arrows or lightning on packs and vault away from melee; shadows (Thieves) flank for backstabs,
##      shadowstep onto whatever attacks the hero, poison and vanish in smoke when cornered.
##      Skills are data (DataTempos.SKILLS): each names a handler (`use`) — strike, charge, shot, bolt, chain, nova,
##      volley, trap, ward, rally, challenge, heal ... — and the AI picks one when its situation fits.
##   6. Follow — out of combat it walks at the hero's side and teleports back if it is left far behind or gets stuck.
## All damage goes through Actor.receive_hit / DamagePipeline; skills cost mana and have cooldowns.

signal decided(what: String)        # every notable decision (tests, the combat bot and the dev overlay listen)

enum Mode { FOLLOW, ENGAGE, RETREAT, EVADE }
const MODE_NAMES := ["Follow", "Engage", "Retreat", "Evade"]

const THINK := 0.15
const DANGER_SCAN := 0.08
const LEASH := 20.0                  # never fight a monster this far from the hero
const TELEPORT_DIST := 30.0          # left further behind than this: rejoin the hero at once
const AGGRO_ASSIST := 11.0           # idle monsters this close to the hero are engaged pre-emptively (when the hero fights)
const ACCEL := 38.0
const TURN_RATE := 12.0
const COMBAT_LINGER := 4.0
const HERO_HURT := 0.55              # heal the hero below this (sooner for Devoted spirits)
const HERO_CRITICAL := 0.3
const REST_REGEN := 0.045            # fraction of max HP per second while resting out of reach
const OOC_REGEN := 0.02

var data: TempoData
var hero: HeroData
var owner_player: Node3D
var slot_index := 0
var mode := Mode.FOLLOW
var target: Actor
var action: TimedAction
var action_kind := &""
var cooldowns := {}
var dodge_cd := 0.0
var agent: NavigationAgent3D
var tdef: Dictionary
var ai := "vanguard"                 # the class's fighting role (see DataTempos.CLASSES)
var personality: Dictionary
var last_skill := &""
var debug_log: Array = []            # recent decisions (tests and the dev overlay read these)

var _hero_stats: DerivedStats
var _think_t := 0.0
var _danger_t := 0.0
var _move_goal := Vector3.INF
var _dash_vel := Vector3.ZERO
var _dash_t := 0.0
var _chain := 0
var _chain_expire := 0.0
var _combat_t := 99.0
var _rest_t := 0.0
var _stuck_t := 0.0
var _last_pos := Vector3.ZERO
var _progress_t := 0.0
var _venom_t := 0.0
var _smoke_t := 0.0
var _evade_t := 0.0
var _evade_goal := Vector3.INF
var _time := 0.0
var _flank := 1.0
var _hero_hits := {}                 # enemy instance id -> time it last hurt the hero
var _plate: Label3D
var _bar: TempoBar
var _light: OmniLight3D
var _wisps: GPUParticles3D
var _dead_since := -1.0

func setup(p_data: TempoData, p_hero: HeroData, p_player: Node3D, p_slot := 0) -> Tempo:
	data = p_data
	hero = p_hero
	owner_player = p_player
	slot_index = p_slot
	tdef = data.class_def()
	ai = String(tdef.get("ai", "vanguard"))
	personality = data.trait_def()
	name = "Tempo_%d_%s" % [data.uid, data.tempo_name]
	display_name = data.tempo_name
	return self

func _ready() -> void:
	super._ready()
	team = BH.Team.PLAYER
	add_to_group(&"tempo")
	add_to_group(&"ally")
	collision_layer = BH.LAYER_PLAYER
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_ENEMY
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.38
	cap.height = 1.8
	cs.shape = cap
	cs.position.y = 0.9
	add_child(cs)
	body_radius = 0.38
	body_height = 1.8
	weight = 0.9
	agent = NavigationAgent3D.new()
	agent.path_desired_distance = 0.8
	agent.target_desired_distance = 0.5
	agent.path_height_offset = 0.3
	agent.radius = 0.4
	agent.avoidance_enabled = false
	add_child(agent)
	visual = CharacterVisual.new()
	visual.name = "Visual"
	add_child(visual)
	visual.setup(String(tdef.get("model", "res://assets/characters/knight.glb")), 1.0, data.tint, tdef.get("rig", &"knight"))
	_spirit_look()
	refresh_equipment_visuals()
	_rng_seed()
	_hero_stats = TempoRules.hero_mirror(hero)
	mark_stats_dirty()
	ensure_stats()
	hp = maxf(1.0, max_hp() * clampf(data.hp_frac, 0.05, 1.0))
	mana = max_mana() * clampf(data.mana_frac, 0.0, 1.0)
	health_changed.emit(hp, max_hp())
	mana_changed.emit(mana, max_mana())
	if hero:
		hero.stats_dirty.connect(_on_hero_changed)
	data.changed.connect(_on_gear_changed)
	Events.damage_dealt.connect(_on_damage_event)
	_plate = Label3D.new()
	_plate.text = data.tempo_name
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0007
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 7
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = tdef.get("color", DataTempos.SPIRIT_TINT)
	_plate.position.y = 2.35
	_plate.no_depth_test = true
	add_child(_plate)
	_bar = TempoBar.new()
	_bar.tempo = self
	_bar.position.y = 2.18
	add_child(_bar)
	_last_pos = global_position
	_flank = 1.0 if slot_index % 2 == 0 else -1.0
	visual.set_stance(_stance_idle())
	Events.tempo_spawned.emit(self)

func _rng_seed() -> void:
	rng.seed = hash("%d/%s" % [data.uid, data.tempo_name])

## Ghostly: a pale rim, slightly see-through (dithered), drifting motes and a cold light.
func _spirit_look() -> void:
	visual.set_rim(DataTempos.SPIRIT_TINT, 0.75)
	visual.set_opacity(0.84)
	_wisps = VFXLib.particles(Color(0.6, 0.95, 1.0, 0.55), 14, 1.6, false, 0.06, 0.35, 70.0, Vector3(0, 0.8, 0), 0.35)
	_wisps.position = Vector3(0, 0.9, 0)
	add_child(_wisps)
	_light = OmniLight3D.new()
	_light.light_color = DataTempos.SPIRIT_TINT
	_light.light_energy = 0.55
	_light.omni_range = 3.2
	_light.position = Vector3(0, 1.3, 0)
	add_child(_light)

func refresh_equipment_visuals() -> void:
	if visual == null:
		return
	var lo := TempoRules.loadout(data, _level())
	visual.detach_weapon(&"main")
	visual.detach_weapon(&"off")
	var main := data.equipment.get_item(&"main_weapon")
	if lo.main_type != null:
		visual.attach_weapon(&"main", Player.weapon_model_for(main, lo.main_type) if main else lo.main_type.model, lo.main_type.grip_offset)
	var sub := data.equipment.get_item(&"sub_weapon")
	if sub != null and sub.base.category == &"shield":
		visual.attach_weapon(&"off", sub.base.model_path())
	elif lo.off_type != null:
		visual.attach_weapon(&"off", Player.weapon_model_for(sub, lo.off_type) if sub else lo.off_type.model, lo.off_type.grip_offset)
	visual.set_stance(_stance_idle())
	visual.set_opacity(0.84)

func _stance_idle() -> StringName:
	var lo := stats.loadout if stats else TempoRules.loadout(data, _level())
	if lo.dual_wield:
		return &"idle_dual"
	if lo.has_shield:
		return &"idle_shield"
	return lo.main_type.idle_anim if lo.main_type else &"idle_1h"

func _level() -> int:
	return hero.progress.level if hero else 1

func _on_hero_changed() -> void:
	_hero_stats = TempoRules.hero_mirror(hero)
	mark_stats_dirty()

func _on_gear_changed() -> void:
	mark_stats_dirty()
	refresh_equipment_visuals()

func rebuild_stats() -> void:
	var mods := status.stat_modifiers()
	if _smoke_t > 0.0:
		mods.append(StatModifier.inc(&"evasion", 1.0, "Smoke"))
	stats = TempoRules.compute(data, _hero_stats, _level(), hero.cls if hero else null, mods)
	level = _level()

## Keep the persistent model in step (map changes, saves).
func sync_data() -> void:
	if data == null:
		return
	data.fallen = not alive
	data.hp_frac = clampf(hp / maxf(1.0, max_hp()), 0.0, 1.0) if alive else 0.0
	data.mana_frac = clampf(mana / maxf(1.0, max_mana()), 0.0, 1.0) if alive else 0.0

func in_combat() -> bool:
	return _combat_t < COMBAT_LINGER

func hp_frac() -> float:
	return hp / maxf(1.0, max_hp())

func mode_name() -> String:
	return MODE_NAMES[mode]

## Hidden in smoke: monsters look for someone else.
func is_hidden() -> bool:
	return _smoke_t > 0.0

# ---- Frame loop -----------------------------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	if data == null or not is_finite(delta) or delta <= 0.0:
		return
	_time += delta
	ensure_stats()
	status.tick(delta)
	if not alive:
		physics_move(delta, Vector3.ZERO)
		return
	if owner_player == null or not is_instance_valid(owner_player):
		owner_player = Game.player as Node3D
	_timers(delta)
	_regen(delta)
	if action:
		if not action.step(delta):
			_action_done()
	_danger_t -= delta
	if _danger_t <= 0.0:
		_danger_t = DANGER_SCAN
		_scan_danger()
	_think_t -= delta
	if _think_t <= 0.0:
		_think_t = THINK + rng.randf() * 0.03
		_think()
	var desired := _movement(delta)
	physics_move(delta, desired)
	_face(delta, desired)
	_track_progress(delta)
	if visual:
		var hv := Vector3(velocity.x, 0, velocity.z)
		visual.update_locomotion(Vector2((global_transform.basis.inverse() * hv).x, (global_transform.basis.inverse() * hv).z),
			in_combat(), 1.0 - clampf(hp_frac() / 0.3, 0.0, 1.0), delta)

func _timers(delta: float) -> void:
	for k in cooldowns.keys():
		cooldowns[k] -= delta
		if cooldowns[k] <= 0.0:
			cooldowns.erase(k)
	dodge_cd = maxf(0.0, dodge_cd - delta)
	_combat_t += delta
	_venom_t = maxf(0.0, _venom_t - delta)
	_evade_t = maxf(0.0, _evade_t - delta)
	if _smoke_t > 0.0:
		_smoke_t -= delta
		if _smoke_t <= 0.0:
			visual.set_opacity(0.84)
			mark_stats_dirty()

func _regen(delta: float) -> void:
	var hr := stats.get_stat(&"hp_regen") + aura_regen()
	var mr := stats.get_stat(&"mana_regen")
	if status.has(&"regen"):
		hr += status.magnitude(&"regen")
	var near := _nearest_enemy_dist()
	if mode == Mode.RETREAT and near > 6.0:
		_rest_t += delta
		if _rest_t > 0.6:
			hr += max_hp() * REST_REGEN
			if int(_rest_t * 2.0) != int((_rest_t - delta) * 2.0):
				FX.spawn(VFXLib.particles(Color(0.55, 1.0, 0.8, 0.8), 8, 0.7, true, 0.12, 1.4, 50.0, Vector3(0, 1.4, 0), 0.4), center())
	else:
		_rest_t = 0.0
	if not in_combat():
		hr += max_hp() * OOC_REGEN
		mr += max_mana() * 0.03
	if status.has(&"purged"):
		hr *= 0.5
	if hp < max_hp():
		hp = minf(max_hp(), hp + hr * delta)
		health_changed.emit(hp, max_hp())
	if mana < max_mana():
		mana = minf(max_mana(), mana + mr * delta)
		mana_changed.emit(mana, max_mana())

func _log(s: String) -> void:
	decided.emit(s)
	debug_log.append("%.1f %s" % [_time, s])
	if debug_log.size() > 40:
		debug_log.pop_front()

# ---- Thinking -------------------------------------------------------------------------------------------------------

func _think() -> void:
	var p := owner_player
	if p == null or not is_instance_valid(p):
		return
	var dp := _flat(p.global_position)
	if mode != Mode.EVADE and (dp > TELEPORT_DIST or (_stuck_t > 2.2 and dp > 5.0)):
		_rejoin_hero()
		return
	if mode == Mode.EVADE:
		if _evade_t > 0.0:
			return
		mode = Mode.ENGAGE if target else Mode.FOLLOW
	var busy := action != null and not action.can_cancel()
	if not busy and _try_heal():
		return
	if _retreat_logic():
		return
	target = _choose_target()
	if target == null:
		if mode != Mode.FOLLOW:
			_log("follow")
		mode = Mode.FOLLOW
		_move_goal = _formation_point()
		return
	mode = Mode.ENGAGE
	if busy:
		return
	if _try_skill():
		return
	_engage()

## Retreat: fall back behind the hero, away from the monsters, and rest until fit.
func _retreat_logic() -> bool:
	var p := owner_player
	var retreat_at := float(personality.get("retreat", 0.3))
	var near := _nearest_enemy_dist()
	var hero_dying := p is Actor and (p as Actor).alive and (p as Actor).hp / maxf(1.0, (p as Actor).max_hp()) < HERO_CRITICAL
	if mode == Mode.RETREAT:
		var healed := hp_frac() >= 0.72 or near > 14.0 and hp_frac() >= 0.5
		if healed or (hero_dying and hp_frac() > retreat_at * 0.8 and personality.get("name", "") != "Cautious"):
			_log("rejoin fight (hp %.0f%%)" % (hp_frac() * 100.0))
			mode = Mode.ENGAGE
			return false
		_move_goal = _retreat_point()
		if near < 4.5 and action == null:
			_try_escape()
		return true
	if hp_frac() < retreat_at and near < 8.0 and not (hero_dying and personality.get("name", "") == "Valiant"):
		_log("retreat (hp %.0f%%)" % (hp_frac() * 100.0))
		mode = Mode.RETREAT
		_cancel_action()
		_try_escape()
		_move_goal = _retreat_point()
		return true
	return false

func _retreat_point() -> Vector3:
	var p := owner_player.global_position
	var away := Vector3.ZERO
	for e in _enemies(14.0):
		var d: Vector3 = global_position - e.global_position
		d.y = 0.0
		away += d.normalized() / maxf(1.0, d.length())
	if away.length() < 0.01:
		away = (global_position - p).slide(Vector3.UP)
	var dir := away.normalized() if away.length() > 0.01 else Vector3.BACK
	# stay within a few steps of the hero, on the far side from the fight
	var goal := p + dir * 6.0
	return CombatQuery.reachable_point(get_world_3d(), p, goal, body_radius)

## Monster scoring — see the class comment.
func _choose_target() -> Actor:
	var p := owner_player
	var hero_fighting: bool = p.has_method(&"in_combat") and p.in_combat()
	var best: Actor = null
	var best_s := -INF
	for e in get_tree().get_nodes_in_group(&"enemy"):
		var en := e as Enemy
		if en == null or not en.alive:
			continue
		var dp := en.global_position.distance_to(p.global_position)
		if dp > LEASH:
			continue
		var threat: bool = en.is_aggressive() or _hero_hits.has(en.get_instance_id()) or en.last_attacker == self
		if not threat and not (hero_fighting and dp < AGGRO_ASSIST):
			continue
		var dt := _flat(en.global_position)
		var s := -dt * 0.35 - dp * 0.25
		if en.target == p and en.is_aggressive():
			s += 6.0
			if en.action != null:
				s += 4.0
		if _time - float(_hero_hits.get(en.get_instance_id(), -99.0)) < 3.0:
			s += 5.0
		if en.target == self:
			s += 3.0 if ai == "vanguard" else 2.0
		if en == target:
			s += 3.0
		var frac := en.hp / maxf(1.0, en.max_hp())
		s += (1.0 - frac) * (5.0 if data.trait_id == &"vengeful" else 2.5)
		if en.def.archetype in [&"caster", &"support"]:
			s += 1.5 if ai == "vanguard" else 3.5
		if en.is_boss:
			s += 2.0 if ai == "vanguard" else 1.0
		elif en.is_elite:
			s += 1.0
		if ai in ["marksman", "caster"] and CombatQuery.blocked(get_world_3d(), center(), en.center()):
			s -= 3.0
		if s > best_s:
			best_s = s
			best = en
	if best != target and best != null:
		_log("target %s" % best.display_name)
	return best

func _try_heal() -> bool:
	var sid := _heal_skill()
	if sid == &"":
		return false
	var sk := DataTempos.skill(sid)
	if cooldowns.has(sid) or mana < float(sk.mana):
		return false
	var who := _heal_target()
	if who == null:
		return false
	var rng_m := float(sk.range)
	if _flat(who.global_position) > rng_m:
		# walk into range (the hero first — this matters more than the fight)
		_move_goal = who.global_position
		mode = Mode.ENGAGE if mode != Mode.RETREAT else mode
		return who == owner_player
	_cast_heal(sid, who)
	return true

func _heal_skill() -> StringName:
	for s in data.skills:
		if DataTempos.is_heal(s):
			return s
	return &""

## Who needs mending most: the hero (sooner when critical), then the other Tempo, then itself.
func _heal_target() -> Actor:
	var p := owner_player as Actor
	var heal_at := float(personality.get("heal_at", HERO_HURT))
	if p and p.alive:
		var f := p.hp / maxf(1.0, p.max_hp())
		if f < HERO_CRITICAL or (f < heal_at and (p.has_method(&"in_combat") and p.call(&"in_combat") or f < 0.4)):
			return p
	for t in get_tree().get_nodes_in_group(&"tempo"):
		if t != self and t.alive and t.hp_frac() < 0.4 and _flat(t.global_position) < 14.0:
			return t
	if hp_frac() < 0.45:
		return self
	return null

func _try_escape() -> bool:
	for sid in data.skills:
		if String(DataTempos.skill(sid).get("kind", "")) == "escape" and _skill_ready(sid):
			return _use_skill(sid)
	# no escape skill: a plain dodge roll away from the nearest monster
	var e := _nearest_enemy()
	if e and dodge_cd <= 0.0 and _flat(e.global_position) < 3.5:
		_dodge((global_position - e.global_position).slide(Vector3.UP))
		return true
	return false

func _skill_ready(sid: StringName) -> bool:
	if not data.skills.has(sid) or cooldowns.has(sid):
		return false
	var sk := DataTempos.skill(sid)
	return mana + 0.001 >= float(sk.get("mana", 0.0)) and not (status.is_silenced() and sk.kind == "heal")

## Offensive / tactical skill choice for the current target.
func _try_skill() -> bool:
	if action != null or target == null:
		return false
	var d := _flat(target.global_position)
	var p := owner_player
	var hero_pressed := 0
	for e in _enemies(8.0, p.global_position):
		if (e as Enemy).target == p and e.is_aggressive():
			hero_pressed += 1
	var hero_a := p as Actor
	var hero_frac := hero_a.hp / maxf(1.0, hero_a.max_hp()) if hero_a and hero_a.alive else 1.0
	var hero_fighting: bool = hero_a != null and hero_a.alive and hero_a.has_method(&"in_combat") and hero_a.call(&"in_combat")
	var big: bool = target.is_elite or target.is_boss
	var executable := func(sk: Dictionary) -> bool:
		return sk.has("execute") and target.hp / maxf(1.0, target.max_hp()) < float(sk.execute)
	for sid in data.skills:
		if DataTempos.is_heal(sid) or not _skill_ready(sid):
			continue
		var sk := DataTempos.skill(sid)
		var ok := false
		match DataTempos.skill_use(sid):
			"cleave":
				if sk.has("execute"):
					ok = d <= float(sk.range) and (executable.call(sk) or big and rng.randf() < 0.3)
				else:
					ok = d <= float(sk.range) and (_enemies_in_front(float(sk.range), float(sk.arc)) >= 2 or big or rng.randf() < 0.35)
			"challenge":
				ok = hero_pressed >= 2 or (hero_pressed >= 1 and hero_frac < 0.5) or (_enemies(6.0).size() >= 3 and hp_frac() > 0.5)
				ok = ok and hp_frac() > 0.4
			"charge":
				ok = d >= float(sk.min_range) and d <= float(sk.range) and not CombatQuery.blocked(get_world_3d(), center(), target.center())
			"pierce":
				ok = d <= float(sk.range) and d > 2.5 and _has_los(target)
			"volley":
				ok = d <= float(sk.range) and (_enemies(float(sk.radius) + 0.5, target.global_position).size() >= 2 or big)
			"disengage":
				ok = d < float(sk.range) and (target as Enemy).def.preferred_range < 3.0
			"shadowstep":
				ok = d <= float(sk.range) and (d > 3.0 or (target as Enemy).target == p or executable.call(sk))
			"venom":
				ok = d <= 2.6 and _venom_t <= 0.0 and (big or target.hp > max_hp() * 0.8)
			"smoke":
				ok = _enemies(3.5).size() >= 3 or (hp_frac() < 0.5 and _enemies(3.0).size() >= 1)
			"nova":
				var r := float(sk.radius)
				ok = _enemies(r).size() >= int(sk.get("min_enemies", 2)) or (d <= r and big)
			"bolt":
				ok = d <= float(sk.range) and _has_los(target)
			"chain":
				ok = d <= float(sk.range) and _has_los(target) and (_enemies(7.0, target.global_position).size() >= 2 or big \
					or (sk.get("dash", false) and d > 3.0))
			"ward":
				var shielded: bool = hero_a != null and hero_a.status.has(&"shielded")
				ok = hero_fighting and not shielded and _flat(p.global_position) <= float(sk.range) \
					and (hero_frac < 0.75 or hero_pressed >= 2 or (big and (target as Enemy).target == p))
			"rally":
				ok = hero_fighting and (_enemies(10.0, p.global_position).size() >= 3 or big)
			"trap":
				ok = d <= float(sk.range) and (_enemies(float(sk.radius) + 1.0, target.global_position).size() >= 2
					or ((target as Enemy).def.preferred_range < 3.0 and d < 7.0))
		if ok:
			return _use_skill(sid)
	return false

# ---- Engaging -------------------------------------------------------------------------------------------------------

func _engage() -> void:
	var t := target
	var p := owner_player
	var d := _flat(t.global_position)
	var lo := stats.loadout
	var ranged := lo.main_type != null and lo.main_type.ranged
	var reach := (lo.main_type.reach if lo.main_type else 1.8)
	match ai:
		"vanguard":
			# between the monster and the hero when it hunts the hero; otherwise straight at it
			var goal := t.global_position
			if (t as Enemy).target == p:
				var side := (p.global_position - t.global_position).slide(Vector3.UP)
				goal = t.global_position + side.normalized() * minf(reach * 0.7, side.length())
			else:
				goal = t.global_position + (global_position - t.global_position).slide(Vector3.UP).normalized() * reach * 0.7
			_move_goal = goal
		"shadow":
			# the blind side: behind the monster, alternating flanks
			var back := -t.forward() * (reach * 0.6)
			_move_goal = t.global_position + back.rotated(Vector3.UP, 0.5 * _flank)
		_:
			var pref := float(tdef.get("preferred_range", 9.0))
			var away := (global_position - t.global_position).slide(Vector3.UP)
			if away.length() < 0.1:
				away = Vector3.BACK
			var goal := t.global_position + away.normalized() * pref
			# stay near the hero
			if goal.distance_to(p.global_position) > 11.0:
				goal = p.global_position + (goal - p.global_position).normalized() * 10.0
			if not _has_los(t):
				goal = goal.lerp(t.global_position, 0.4)
			_move_goal = goal
	if action == null:
		if ranged:
			if d <= reach * 0.95 and _has_los(t):
				_attack()
		elif d <= reach + t.body_radius * 0.6:
			_attack()

func _attack() -> void:
	var lo := stats.loadout
	var wt := lo.main_type
	if _time > _chain_expire:
		_chain = 0
	var anims: Array = wt.dual_light_anims if lo.dual_wield and wt and not wt.dual_light_anims.is_empty() else (wt.light_anims if wt else [&"sword_1"])
	var step := _chain % 4
	var anim: StringName = anims[mini(step, anims.size() - 1)]
	var aps := lo.aps() * stats.get_stat(&"attack_speed", 1.0)
	var rate := clampf(aps * float(DB.anim(anim).get("length", 0.6)), StatCalculator.SPEED_MULT_MIN, StatCalculator.SPEED_MULT_MAX)
	var a := TimedAction.from_anim(anim, rate)
	a.data["step"] = step
	a.data["hand"] = lo.hand_for_step(step)
	a.move_mult = wt.move_mult if wt else 0.3
	_face_now(target.global_position)
	if wt and wt.ranged:
		var tgt := target
		a.on_release = func() -> void: _shoot(a, tgt, 1.0, 0, false)
	else:
		a.on_window = func(w: int, first: bool) -> void: _melee_window(a, w, first, 1.0, wt.arc_degrees if wt else 100.0, 0.0)
	_begin(a, &"attack")
	visual.play_action(anim, rate)
	Audio.play_at(wt.swing_sound if wt else &"swing_light", global_position, -6.0)
	_chain = step + 1
	_chain_expire = _time + a.combo_close + 0.4
	if _chain >= 4:
		_chain = 0
	_combat_t = 0.0

func _begin(a: TimedAction, kind: StringName) -> void:
	action = a
	action_kind = kind
	visual.interrupt_fidget()

func _action_done() -> void:
	action = null
	action_kind = &""
	visual.set_trail(false)
	if ai == "shadow" and rng.randf() < 0.3:
		_flank = -_flank

func _cancel_action() -> void:
	if action != null:
		action.finish(false)
		action = null
		action_kind = &""
		visual.stop_action()
	visual.set_trail(false)
	_dash_t = 0.0

func _weapon_request(hand: int, mult: float, heavy := false, label := "Tempo strike") -> DamageRequest:
	var wt := stats.loadout.main_type
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = stats
	req.use_weapon = true
	req.hand = hand
	req.heavy = heavy
	req.weapon_mult = mult
	req.knockback = (wt.knockback if wt else 2.0) * (1.8 if heavy else 1.0)
	req.poise = (wt.poise_damage if wt else 8.0) * (2.0 if heavy else 1.0)
	req.label = "%s: %s" % [data.tempo_name, label]
	req.tags[&"weapon"] = true
	req.tags[&"tempo"] = true
	if _venom_t > 0.0:
		req.direct_status[&"poisoned"] = 45.0
	return req

func _melee_window(a: TimedAction, w: int, first: bool, mult: float, arc: float, crit_bonus: float, knock_mult := 1.0) -> void:
	var wt := stats.loadout.main_type
	var reach := (wt.reach if wt else 1.8) * (1.1 if a.data.get("heavy", false) else 1.0)
	if first:
		visual.set_trail(true, Color(0.6, 0.95, 1.0, 0.6), wt.length if wt else 1.0)
		FX.spawn_facing(VFXLib.slash_arc(Color(0.6, 0.95, 1.0, 0.6), reach * 0.95, arc, 1.05, 0.2 / maxf(a.rate, 0.5), 0.5, int(a.data.get("step", 0)) % 2 == 0), global_position, forward())
	var step := int(a.data.get("step", 0))
	var chain_m := float(wt.chain_mults[step]) if wt and step < wt.chain_mults.size() else 1.0
	var hits := 0
	for t: Actor in CombatQuery.actors_in_arc(get_world_3d(), global_position, forward(), reach, arc, BH.LAYER_ENEMY):
		if not a.mark_hit(w, t) or CombatQuery.blocked(get_world_3d(), center(), t.center()):
			continue
		var req := _weapon_request(int(a.data.get("hand", 0)), mult * chain_m, bool(a.data.get("heavy", false)), String(a.data.get("label", "strike")))
		req.knockback *= knock_mult
		req.crit_bonus = crit_bonus
		if a.data.has("sk"):
			_decorate(req, a.data.sk, t)
		req.tags[&"push_dir"] = (t.global_position - global_position).slide(Vector3.UP).normalized()
		if wt and wt.id == &"dagger" and t.forward().dot(forward()) > 0.5:
			req.positional_mult = 1.25
		var res := t.receive_hit(req, self, t.center())
		_on_hit_dealt(t, res)
		hits += 1
		# a killing stroke that resets (Nightfall): ready again at once
		if not t.alive and a.data.has("sk") and a.data.sk.get("reset_on_kill", false):
			cooldowns.erase(a.data.get("skill", &""))
			_log("reset %s" % a.data.get("skill", &""))
	if hits > 0:
		Audio.play_at(wt.hit_sound if wt else &"hit_flesh", global_position + forward() * reach * 0.6, -3.0)

func _shoot(a: TimedAction, t: Actor, mult: float, pierce: int, charged: bool, sk := {}) -> void:
	var wt := stats.loadout.main_type
	if wt == null:
		return
	var aim := (t.center() if t and is_instance_valid(t) and t.alive else global_position + forward() * 10.0)
	# lead a moving target a little
	if t and is_instance_valid(t):
		aim += t.velocity * clampf(global_position.distance_to(aim) / maxf(wt.projectile_speed, 1.0), 0.0, 0.6) * 0.6
	var from := center() + Vector3.UP * 0.3 + forward() * 0.5
	var dir := (aim - from)
	dir.y = 0.0
	var req := _weapon_request(int(a.data.get("hand", 0)), mult, charged, String(sk.get("name", "Piercing Arrow" if pierce > 0 else "arrow")))
	req.tags[&"projectile"] = true
	var el := stats.loadout.element_for(0)
	if not sk.is_empty():
		_decorate(req, sk, t)
		el = int(sk.get("element", el))
	var pr := Projectile.spawn(FX.world if FX.world else get_parent(), from, dir.normalized(), wt.projectile_speed * (1.25 if charged else 1.0),
		req, self, BH.LAYER_ENEMY, el, "arrow" if wt.id == &"bow" else ("model:" + wt.model if wt.id == &"javelin" else "orb"))
	pr.max_range = wt.reach + (6.0 if charged else 0.0)
	pr.radius = 0.3
	pr.pierce = pierce
	pr.hit_sound = wt.hit_sound
	pr.on_hit = _hit_relay(weakref(self))
	Audio.play_at(wt.swing_sound, global_position, -6.0)
	if charged:
		FX.spawn(VFXLib.light_flash(DataTempos.SPIRIT_TINT, 2.5, 4.0, 0.2), from)

func _on_hit_dealt(t: Actor, res: DamageResult) -> void:
	if res == null or res.evaded:
		return
	_combat_t = 0.0
	if t and not t.alive:
		data.kills += 1

# ---- Callbacks that outlive the spirit ------------------------------------------------------------------------------
# Projectiles and delayed blasts can land after this Tempo is gone (released mid-fight, fallen, a map change). A lambda
# made in an instance method holds this node by a raw pointer, and calling it after the node is freed reaches whatever
# object took its place. These are made in static functions and reach the Tempo only through a weak reference.

static func _hit_relay(me: WeakRef) -> Callable:
	return func(tt: Actor, res: DamageResult, _pt: Vector3) -> void:
		var t := me.get_ref() as Tempo
		if t:
			t._on_hit_dealt(tt, res)

static func _volley_relay(me: WeakRef, col: Color, radius: float) -> Callable:
	return func(pos: Vector3, hits: Array) -> void:
		FX.spawn(VFXLib.particles(Color(col.r, col.g, col.b, 0.9).lightened(0.2), 22, 0.35, true, 0.1, 9.0, 12.0, Vector3(0, -20, 0), radius * 0.8), pos + Vector3.UP * 3.5)
		Audio.play_at(&"arrow_impact", pos, -4.0)
		var t := me.get_ref() as Tempo
		if t:
			for h in hits:
				t._on_hit_dealt(h[0], h[1])

# ---- Skills ---------------------------------------------------------------------------------------------------------

func _pay(sid: StringName) -> void:
	var sk := DataTempos.skill(sid)
	spend_mana(float(sk.mana))
	cooldowns[sid] = float(sk.cooldown)
	last_skill = sid
	_combat_t = 0.0
	_log("skill %s" % sid)

func _use_skill(sid: StringName) -> bool:
	var sk := DataTempos.skill(sid)
	if sk.is_empty() or not _skill_ready(sid):
		return false
	var needs_target := DataTempos.skill_use(sid) not in ["challenge", "disengage", "smoke", "nova", "ward", "rally", "heal"]
	if needs_target and (target == null or not is_instance_valid(target) or not target.alive):
		return false
	match DataTempos.skill_use(sid):
		"cleave": return _sk_cleave(sid, sk)
		"challenge": return _sk_challenge(sid, sk)
		"charge": return _sk_charge(sid, sk)
		"pierce": return _sk_pierce(sid, sk)
		"volley": return _sk_volley(sid, sk)
		"disengage": return _sk_disengage(sid, sk)
		"shadowstep": return _sk_shadowstep(sid, sk)
		"venom": return _sk_venom(sid, sk)
		"smoke": return _sk_smoke(sid, sk)
		"nova": return _sk_nova(sid, sk)
		"bolt": return _sk_bolt(sid, sk)
		"chain": return _sk_chain(sid, sk)
		"ward": return _sk_ward(sid, sk)
		"rally": return _sk_rally(sid, sk)
		"trap": return _sk_trap(sid, sk)
	return false

## Handlers every skill `use` may name (the data tests check SKILLS against this list).
const HANDLERS := ["cleave", "challenge", "charge", "pierce", "volley", "disengage", "shadowstep", "venom", "smoke", "nova",
	"bolt", "chain", "ward", "rally", "trap", "heal"]

## A skill's own effects on a hit: element (the whole hit converts), status buildup, and the execute bonus against a
## badly hurt monster. `forces` also takes the skill's knockback / poise.
func _decorate(req: DamageRequest, sk: Dictionary, t: Actor, forces := false) -> void:
	if sk.has("element"):
		req.conversion = {int(sk.element): 1.0}
	var st: Dictionary = sk.get("status", {})
	for id in st:
		req.direct_status[id] = float(req.direct_status.get(id, 0.0)) + float(st[id])
	if sk.has("execute") and t != null and is_instance_valid(t) and t.hp / maxf(1.0, t.max_hp()) < float(sk.execute):
		req.more.append(["Execute", float(sk.get("execute_mult", 2.0))])
	if forces:
		req.knockback = float(sk.get("knockback", req.knockback))
		req.poise = float(sk.get("poise", req.poise))

func _skill_color(sk: Dictionary) -> Color:
	if sk.has("color"):
		return sk.color
	return Elements.color(int(sk.element)) if sk.has("element") else DataTempos.SPIRIT_TINT

func _element_sound(sk: Dictionary, fallback: StringName) -> StringName:
	match int(sk.get("element", -1)):
		Elements.FIRE: return &"cast_fire"
		Elements.ICE: return &"cast_ice"
		Elements.LIGHTNING: return &"cast_lightning"
		Elements.EARTH: return &"earth_quake"
		Elements.DARK: return &"dark_cast"
		Elements.LIGHT: return &"arcane_surge"
	return fallback

func _skill_action(sid: StringName, sk: Dictionary, rate := 1.0) -> TimedAction:
	_cancel_action()
	var a := TimedAction.from_anim(sk.anim, rate)
	a.move_mult = 0.0
	a.data["skill"] = sid
	_begin(a, &"skill")
	visual.play_action(sk.anim, rate)
	_pay(sid)
	return a

func _sk_cleave(sid: StringName, sk: Dictionary) -> bool:
	_face_now(target.global_position)
	var wt := stats.loadout.main_type
	var skd := sk.duplicate()
	if not sk.get("keep_anim", false):
		skd.anim = wt.heavy_anim if wt and not wt.ranged else &"sword_heavy"
	var a := _skill_action(sid, skd, clampf(stats.get_stat(&"attack_speed", 1.0), 0.7, 1.6))
	a.data["heavy"] = true
	a.data["label"] = sk.name
	a.data["sk"] = sk
	a.on_window = func(w: int, first: bool) -> void: _melee_window(a, w, first, float(sk.mult), float(sk.arc), float(sk.get("crit_bonus", 0.0)),
		float(sk.knockback) / 4.0)
	Audio.play_at(&"swing_heavy", global_position, -2.0)
	return true

func _sk_challenge(sid: StringName, sk: Dictionary) -> bool:
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		var n := 0
		for e in _enemies(float(sk.range)):
			(e as Enemy).taunt(self, float(sk.duration))
			n += 1
		status.apply(&"fortified", float(sk.duration))
		FX.spawn(VFXLib.ring_wave(Color(0.6, 0.9, 1.0, 0.9), float(sk.range), 0.5, 0.8), global_position)
		FX.text_popup(center() + Vector3.UP * 1.0, "%s!" % sk.name, Color(0.7, 0.92, 1.0), 1.0)
		Audio.play_at(&"war_cry", global_position, -2.0)
		_log("taunted %d" % n)
	if a.release_t < 0.0:
		a.release_t = 0.3
	return true

func _sk_charge(sid: StringName, sk: Dictionary) -> bool:
	var t := target
	var dir := (t.global_position - global_position).slide(Vector3.UP)
	var dist := minf(dir.length() + 0.5, float(sk.range))
	_face_now(t.global_position)
	var a := _skill_action(sid, sk)
	var hit := {}
	a.data["label"] = sk.name
	var dur := 0.35
	dash(dir, dist / dur, dur)
	var from := global_position
	a.on_release = func() -> void: pass
	var line := func() -> void:
		for e: Actor in CombatQuery.actors_in_line(get_world_3d(), from, dir.normalized(), dist, float(sk.width), BH.LAYER_ENEMY):
			if hit.has(e.get_instance_id()):
				continue
			hit[e.get_instance_id()] = true
			var req := _weapon_request(0, float(sk.mult), true, sk.name)
			req.knockback = float(sk.knockback)
			req.poise = float(sk.poise)
			req.tags[&"push_dir"] = dir.normalized()
			_on_hit_dealt(e, e.receive_hit(req, self, e.center()))
	get_tree().create_timer(dur, false).timeout.connect(func() -> void:
		if is_instance_valid(self) and alive:
			line.call()
			FX.spawn(VFXLib.dust_puff(0.8), global_position))
	FX.spawn(VFXLib.particles(Color(0.6, 0.95, 1.0, 0.8), 18, 0.5, true, 0.12, 2.0, 60.0, Vector3.ZERO, 0.4), center())
	Audio.play_at(&"boss_charge", global_position, -8.0)
	return true

func _sk_pierce(sid: StringName, sk: Dictionary) -> bool:
	var t := target
	_face_now(t.global_position)
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void: _shoot(a, t, float(sk.mult), int(sk.pierce), true, sk)
	return true

func _sk_volley(sid: StringName, sk: Dictionary) -> bool:
	var at := target.global_position
	_face_now(at)
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		for i in int(sk.waves):
			var off := Vector3(rng.randf_range(-1.2, 1.2), 0, rng.randf_range(-1.2, 1.2)) if i > 0 else Vector3.ZERO
			var req := _weapon_request(0, float(sk.mult), false, sk.name)
			req.evadable = false
			_decorate(req, sk, null)
			req.knockback = float(sk.knockback)
			req.poise = float(sk.poise)
			var col := _skill_color(sk) if sk.has("element") or sk.has("color") else Color(0.55, 0.95, 1.0)
			var b := AreaEffects.delayed(FX.world, CombatQuery.ground_at(get_world_3d(), at + off), float(sk.radius), 0.5 + 0.45 * i, req, self,
				BH.LAYER_ENEMY, Color(col.r, col.g, col.b, 0.35))
			b.on_blast = _volley_relay(weakref(self), col, float(sk.radius))
	return true

func _sk_disengage(sid: StringName, sk: Dictionary) -> bool:
	var e := _nearest_enemy()
	var away := (global_position - (e.global_position if e else owner_player.global_position)).slide(Vector3.UP)
	if away.length() < 0.1:
		away = -forward()
	var goal := CombatQuery.reachable_point(get_world_3d(), global_position, global_position + away.normalized() * float(sk.leap), body_radius)
	var snare_at := global_position
	var a := _skill_action(sid, sk)
	a.iframes = Vector2(0.0, 0.4)
	rotation.y = atan2(away.x, away.z)
	dash(goal - global_position, maxf(0.5, global_position.distance_to(goal)) / 0.4, 0.4)
	var h := AreaEffects.hazard(FX.world, snare_at, 2.2, 3.0, null, self, BH.LAYER_ENEMY, Color(0.55, 0.95, 1.0), 0.4)
	h.status_id = &"slowed"
	Audio.play_at(&"dodge_roll", global_position, -3.0)
	return true

func _sk_shadowstep(sid: StringName, sk: Dictionary) -> bool:
	var t := target
	var behind := t.global_position - t.forward() * (t.body_radius + 0.9)
	var spot := CombatQuery.reachable_point(get_world_3d(), t.global_position, behind, body_radius)
	FX.spawn(VFXLib.particles(Color(0.2, 0.1, 0.3, 0.8), 20, 0.6, true, 0.3, 2.0, 180.0, Vector3(0, 0.5, 0), 0.3, false), center())
	global_position = CombatQuery.ground_at(get_world_3d(), spot)
	velocity = Vector3.ZERO
	_face_now(t.global_position)
	FX.spawn(VFXLib.particles(Color(0.75, 0.55, 1.0, 0.9), 16, 0.5, true, 0.12, 3.0, 180.0, Vector3.ZERO, 0.3), center())
	Audio.play_at(&"blink", global_position, -2.0)
	var a := _skill_action(sid, sk, clampf(stats.get_stat(&"attack_speed", 1.0), 0.8, 1.6))
	a.data["heavy"] = true
	a.data["label"] = sk.name
	a.data["sk"] = sk
	a.on_window = func(w: int, first: bool) -> void: _melee_window(a, w, first, float(sk.mult), 90.0, float(sk.crit_bonus))
	return true

func _sk_venom(sid: StringName, sk: Dictionary) -> bool:
	_face_now(target.global_position)
	_venom_t = float(sk.duration)
	var a := _skill_action(sid, sk, 1.2)
	a.data["label"] = sk.name
	var t := target
	var flurry := func() -> void:
		for i in int(sk.hits):
			if t == null or not is_instance_valid(t) or not t.alive or _flat(t.global_position) > 3.2:
				return
			var req := _weapon_request(i % 2, float(sk.mult), false, sk.name)
			req.direct_status[&"poisoned"] = 80.0
			req.tags[&"push_dir"] = (t.global_position - global_position).slide(Vector3.UP).normalized()
			_on_hit_dealt(t, t.receive_hit(req, self, t.center()))
		FX.spawn(VFXLib.particles(Color(0.45, 0.9, 0.25, 0.9), 16, 0.5, true, 0.1, 2.0, 90.0, Vector3.ZERO, 0.3), t.center())
	a.on_release = flurry
	if a.release_t < 0.0:
		a.release_t = 0.25
	Audio.play_at(&"swing_dagger", global_position, -2.0)
	return true

func _sk_smoke(sid: StringName, sk: Dictionary) -> bool:
	var a := _skill_action(sid, sk, 1.3)
	a.on_release = func() -> void:
		for e in _enemies(float(sk.radius)):
			e.status.apply(&"slowed", float(sk.duration))
			e.status.apply(&"weakened", float(sk.duration))
			(e as Enemy).lose_target(self)
		_smoke_t = float(sk.duration)
		visual.set_opacity(0.25)
		mark_stats_dirty()
		FX.spawn(VFXLib.particles(Color(0.06, 0.05, 0.08, 0.85), 40, 2.2, true, 1.4, 1.6, 180.0, Vector3(0, 0.4, 0), float(sk.radius) * 0.6, false), global_position + Vector3.UP * 0.6)
		Audio.play_at(&"wind_gust", global_position, -2.0)
		mode = Mode.RETREAT
		_move_goal = _retreat_point()
	if a.release_t < 0.0:
		a.release_t = 0.2
	return true

func _cast_heal(sid: StringName, who: Actor) -> void:
	var sk := DataTempos.skill(sid)
	_face_now(who.global_position)
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		if who == null or not is_instance_valid(who) or not who.alive:
			return
		var mult := 1.0 + stats.get_stat(&"healing")
		# a mend with a radius reaches every ally around its target
		var all: Array = [who]
		if sk.has("radius"):
			for ally in [owner_player] + get_tree().get_nodes_in_group(&"tempo"):
				if ally is Actor and ally != who and ally.alive and ally.global_position.distance_to(who.global_position) <= float(sk.radius):
					all.append(ally)
			FX.spawn(VFXLib.ring_wave(Color(0.6, 1.0, 0.8, 0.9), float(sk.radius), 0.6, 0.6), who.global_position)
		var col := Color(0.55, 1.0, 0.75)
		for w: Actor in all:
			w.heal(w.max_hp() * float(sk.heal) * mult)
			w.status.apply(&"regen", 4.0, w.max_hp() * float(sk.regen) * mult / 4.0)
			if sk.get("cleanse", false):
				w.status.cleanse([&"poisoned", &"bleeding", &"burning"])
			if w != self:
				FX.spawn(VFXLib.lightning_bolt(center() + Vector3.UP * 0.3, w.center(), col, 0.3, 0.1), Vector3.ZERO)
			FX.spawn(VFXLib.beam_flash(col, 3.0, 0.6), w.global_position)
			FX.spawn(VFXLib.particles(Color(0.6, 1.0, 0.8, 0.9), 22, 0.9, true, 0.14, 2.0, 50.0, Vector3(0, 3, 0), 0.5), w.center())
		Audio.play_at(&"heal", who.global_position, -2.0)
		_log("healed %s%s" % [who.display_name if who != self else "self", " +%d" % (all.size() - 1) if all.size() > 1 else ""])
	if a.release_t < 0.0:
		a.release_t = 0.3

## Around itself: one burst that hits every monster within `radius` (whirlwinds, novas, quakes, knife fans).
func _sk_nova(sid: StringName, sk: Dictionary) -> bool:
	if target:
		_face_now(target.global_position)
	var a := _skill_action(sid, sk)
	a.data["label"] = sk.name
	var col := _skill_color(sk)
	a.on_release = func() -> void:
		if not alive:
			return
		var req := _weapon_request(0, float(sk.mult), true, String(sk.name))
		_decorate(req, sk, null, true)
		req.evadable = false
		var hits := AreaEffects.burst(self, global_position, float(sk.radius), BH.LAYER_ENEMY, req, self)
		for h in hits:
			_on_hit_dealt(h[0], h[1])
		FX.spawn(VFXLib.ring_wave(Color(col.r, col.g, col.b, 0.9), float(sk.radius), 0.45, 0.8), global_position)
		FX.spawn(VFXLib.particles(Color(col.r, col.g, col.b, 0.85), 30, 0.6, true, 0.14, 5.0, 180.0, Vector3(0, 1.0, 0), float(sk.radius) * 0.5),
			global_position + Vector3.UP * 0.5)
		if int(sk.get("element", -1)) == Elements.EARTH:
			FX.spawn(VFXLib.dust_puff(1.6), global_position)
		Audio.play_at(_element_sound(sk, &"swing_heavy"), global_position, -3.0)
		_log("nova %s hit %d" % [sid, hits.size()])
	return true

## A spell bolt of the skill's element.
func _sk_bolt(sid: StringName, sk: Dictionary) -> bool:
	var t := target
	_face_now(t.global_position)
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		if not alive:
			return
		var aim := t.center() if is_instance_valid(t) and t.alive else global_position + forward() * 10.0
		var from := center() + Vector3.UP * 0.3 + forward() * 0.5
		var dir := aim - from
		dir.y = 0.0
		var req := _weapon_request(0, float(sk.mult), true, String(sk.name))
		_decorate(req, sk, t, true)
		req.tags[&"projectile"] = true
		var pr := Projectile.spawn(FX.world if FX.world else get_parent(), from, dir.normalized(), float(sk.get("speed", 24.0)), req, self,
			BH.LAYER_ENEMY, int(sk.get("element", Elements.LIGHT)), "orb")
		pr.max_range = float(sk.range) + 4.0
		pr.radius = 0.35
		pr.pierce = int(sk.get("pierce", 0))
		pr.on_hit = _hit_relay(weakref(self))
		FX.spawn(VFXLib.light_flash(_skill_color(sk), 2.0, 4.0, 0.2), from)
		Audio.play_at(_element_sound(sk, &"arcane_surge"), global_position, -6.0)
	return true

## Lightning that leaps from monster to monster; `dash` rides it into the first one.
func _sk_chain(sid: StringName, sk: Dictionary) -> bool:
	var t := target
	_face_now(t.global_position)
	var col := _skill_color(sk)
	var a := _skill_action(sid, sk)
	if sk.get("dash", false):
		var dir := (t.global_position - global_position).slide(Vector3.UP)
		var goal := CombatQuery.reachable_point(get_world_3d(), global_position,
			t.global_position - dir.normalized() * (t.body_radius + 1.0), body_radius)
		var dist := global_position.distance_to(goal)
		if dist > 1.0:
			FX.spawn(VFXLib.lightning_bolt(center(), goal + Vector3.UP, col, 0.25, 0.16), Vector3.ZERO)
			dash(goal - global_position, dist / 0.22, 0.22)
	a.on_release = func() -> void: _chain_from(t, sk)
	return true

func _chain_from(first: Actor, sk: Dictionary) -> void:
	if not alive or first == null or not is_instance_valid(first) or not first.alive:
		return
	var col := _skill_color(sk)
	var hit := {}
	var cur: Actor = first
	var from := center() + Vector3.UP * 0.4
	var mult := float(sk.mult)
	for i in int(sk.get("jumps", 3)) + 1:
		hit[cur.get_instance_id()] = true
		var req := _weapon_request(0, mult, true, String(sk.name))
		_decorate(req, sk, cur, true)
		req.evadable = false
		FX.spawn(VFXLib.lightning_bolt(from, cur.center(), col, 0.24, 0.12), Vector3.ZERO)
		var at := cur.center()
		_on_hit_dealt(cur, cur.receive_hit(req, self, at))
		from = at
		mult *= float(sk.get("falloff", 0.85))
		var nxt: Actor = null
		var best := 7.5
		for e in _enemies(7.5, at):
			if hit.has(e.get_instance_id()) or not e.alive:
				continue
			var dd: float = e.global_position.distance_to(at)
			if dd < best and not CombatQuery.blocked(get_world_3d(), at, e.center()):
				best = dd
				nxt = e
		if nxt == null:
			break
		cur = nxt
	Audio.play_at(&"lightning_zap", first.global_position, -2.0)
	_log("chain hit %d" % hit.size())

## A barrier over the hero; `all` also fortifies every Tempo near it; `taunt` draws the monsters around onto itself.
func _sk_ward(sid: StringName, sk: Dictionary) -> bool:
	var p := owner_player
	if p:
		_face_now(p.global_position)
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		if not alive:
			return
		var dur := float(sk.duration)
		var mult := 1.0 + stats.get_stat(&"healing")
		var col := Color(0.62, 0.95, 1.0)
		if p is Player and (p as Player).alive and _flat(p.global_position) <= float(sk.range) + 2.0:
			(p as Player).add_shield((p as Player).max_hp() * float(sk.shield) * mult, dur)
			FX.spawn(VFXLib.lightning_bolt(center() + Vector3.UP * 0.3, (p as Player).center(), col, 0.3, 0.1), Vector3.ZERO)
			FX.spawn(VFXLib.ring_wave(col, 1.6, 0.5, 0.5), p.global_position)
		if sk.get("all", false):
			for t in get_tree().get_nodes_in_group(&"tempo"):
				if t.alive and _flat(t.global_position) <= float(sk.range):
					t.status.apply(&"fortified", dur)
					FX.spawn(VFXLib.ring_wave(col, 1.4, 0.5, 0.5), t.global_position)
		if sk.has("taunt"):
			var n := 0
			for e in _enemies(float(sk.taunt)):
				(e as Enemy).taunt(self, dur * 0.75)
				n += 1
			status.apply(&"fortified", dur)
			FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.5, 0.9), float(sk.taunt), 0.5, 0.8), global_position)
			_log("taunted %d" % n)
		FX.text_popup(center() + Vector3.UP * 1.0, String(sk.name), col, 1.0)
		Audio.play_at(&"arcane_charge", global_position, -3.0)
		_log("warded")
	return true

## A battle cry: the skill's statuses on the hero and every Tempo within `radius`.
func _sk_rally(sid: StringName, sk: Dictionary) -> bool:
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		if not alive:
			return
		var n := 0
		for who in [owner_player] + get_tree().get_nodes_in_group(&"tempo"):
			if who is Actor and who.alive and _flat(who.global_position) <= float(sk.radius):
				for st in sk.get("statuses", []):
					who.status.apply(StringName(st), float(sk.duration))
				n += 1
		FX.spawn(VFXLib.ring_wave(Color(1.0, 0.8, 0.45, 0.9), float(sk.radius) * 0.6, 0.6, 0.9), global_position)
		FX.text_popup(center() + Vector3.UP * 1.0, String(sk.name), Color(1.0, 0.85, 0.55), 1.0)
		Audio.play_at(&"war_cry", global_position, -2.0)
		_log("rallied %d" % n)
	if a.release_t < 0.0:
		a.release_t = 0.3
	return true

## A lingering snare under the target: hurts and hinders every monster that stays in it.
func _sk_trap(sid: StringName, sk: Dictionary) -> bool:
	var at := target.global_position
	_face_now(at)
	var col := _skill_color(sk)
	var a := _skill_action(sid, sk)
	a.on_release = func() -> void:
		if not alive:
			return
		var req := _weapon_request(0, float(sk.mult), false, String(sk.name))
		_decorate(req, sk, null)
		req.evadable = false
		req.knockback = 0.0
		req.poise = 2.0
		var h := AreaEffects.hazard(FX.world, CombatQuery.ground_at(get_world_3d(), at), float(sk.radius), float(sk.duration), req, self,
			BH.LAYER_ENEMY, col, 0.5)
		h.status_id = StringName(sk.get("status_id", &"slowed"))
		Audio.play_at(&"cast_earth", at, -4.0)
		_log("trap")
	return true

# ---- Danger ---------------------------------------------------------------------------------------------------------

## Look for anything about to hit this spirit and get out of its way. Returns true while evading.
func _scan_danger() -> bool:
	if _dash_t > 0.0 or (action != null and action.in_iframes()):
		return false
	var pos := global_position
	var escape := Vector3.ZERO
	var urgency := 99.0            # seconds until the worst threat lands
	var needed := 0.0
	# telegraphed blasts (enemy slams, fire-pots, boulders, meteors...)
	for b in get_tree().get_nodes_in_group(&"telegraph"):
		if not is_instance_valid(b) or not (b.mask & BH.LAYER_PLAYER) or not b.has_method(&"time_left"):
			continue
		var tl: float = b.time_left()
		if tl <= 0.0:
			continue
		var off: Vector3 = (pos - b.global_position).slide(Vector3.UP)
		var d := off.length()
		var r: float = b.radius + body_radius + 0.35
		if b.inner > 0.0 and d < b.inner - body_radius - 0.2:
			continue   # safe inside a ring blast
		if d < r:
			var dir := off.normalized() if d > 0.05 else Vector3(rng.randf_range(-1, 1), 0, rng.randf_range(-1, 1)).normalized()
			if b.inner > 0.0 and d < b.inner + 1.0:
				dir = -dir   # dive into the ring's calm centre
			escape += dir * (1.0 + (r - d))
			urgency = minf(urgency, tl)
			needed = maxf(needed, r - d + 0.6)
	# lingering hazards
	for h in get_tree().get_nodes_in_group(&"hazard"):
		if not is_instance_valid(h) or not (h.mask & BH.LAYER_PLAYER):
			continue
		var off2: Vector3 = (pos - h.global_position).slide(Vector3.UP)
		if off2.length() < h.radius + body_radius + 0.2:
			escape += (off2.normalized() if off2.length() > 0.05 else Vector3.BACK) * 1.5
			urgency = minf(urgency, 1.0)
			needed = maxf(needed, h.radius + body_radius + 0.6 - off2.length())
	# monsters winding up blows that will catch this spirit (bosses and elites first of all)
	for e in _enemies(12.0):
		var en := e as Enemy
		if en.action == null or en.current_attack.is_empty():
			continue
		var atk: Dictionary = en.current_attack
		var kind := String(atk.get("kind", ""))
		var tl2: float = en.action.first_hit_time() - en.action.elapsed
		if tl2 < -0.05:
			continue
		var to_me: Vector3 = (pos - en.global_position).slide(Vector3.UP)
		var dist := to_me.length()
		var rr := float(atk.get("range", 2.0)) + en.body_radius + body_radius
		var hits_me := false
		match kind:
			"melee", "dash":
				hits_me = en.target == self and dist < rr + 1.0 and (en.is_boss or en.is_elite or float(atk.get("mult", 1.0)) >= 1.5 or atk.has("windup"))
			"aoe":
				if String(atk.get("telegraph", "circle")) == "cone":
					var arc := deg_to_rad(float(atk.get("arc", 120.0))) * 0.5
					hits_me = dist < float(atk.get("radius", 3.0)) + body_radius and en.forward().angle_to(to_me.normalized()) < arc + 0.2
				elif atk.get("self_centered", false):
					hits_me = dist < float(atk.get("radius", 3.0)) + body_radius + 0.3
		if hits_me:
			var away := to_me.normalized() if dist > 0.05 else -forward()
			# roll sideways out of a frontal swing, straight back out of a slam
			var side := away.rotated(Vector3.UP, PI * 0.5 * (1.0 if rng.randf() < 0.5 else -1.0))
			escape += (side if kind in ["melee", "dash"] else away) * 2.0
			urgency = minf(urgency, maxf(tl2, 0.0))
			needed = maxf(needed, 3.0)
		# a charge lane
		var ch: Dictionary = en._charge
		if not ch.is_empty() and not ch.get("lunge", false):
			var cdir: Vector3 = ch.dir
			var along := to_me.dot(cdir)
			var lateral := absf(to_me.dot(cdir.cross(Vector3.UP)))
			if along > -1.0 and along < float(ch.speed) * (float(ch.left) + float(ch.get("delay", 0.0))) + 2.0 and lateral < float(atk.get("width", 2.5)) * 0.5 + body_radius + 0.6:
				var sgn := 1.0 if to_me.dot(cdir.cross(Vector3.UP)) >= 0.0 else -1.0
				escape += cdir.cross(Vector3.UP) * sgn * 2.5
				urgency = minf(urgency, float(ch.get("delay", 0.0)) + maxf(0.0, along) / maxf(float(ch.speed), 1.0))
				needed = maxf(needed, 3.5)
	# boss sweeps travelling across the floor
	for s in get_tree().get_nodes_in_group(&"sweep"):
		if not is_instance_valid(s) or not (s.mask & BH.LAYER_PLAYER):
			continue
		var rel: Vector3 = (pos - s.global_position).slide(Vector3.UP)
		var along2 := rel.dot(s.dir)
		var lat := rel.dot(s.dir.cross(Vector3.UP))
		if along2 > -0.5 and along2 < (s.length - s.travelled) + 1.0 and absf(lat) < s.width * 0.5 + body_radius + 0.5:
			escape += s.dir.cross(Vector3.UP) * (1.0 if lat >= 0.0 else -1.0) * 2.5
			urgency = minf(urgency, maxf(0.0, along2) / maxf(s.speed, 1.0))
			needed = maxf(needed, 3.0)
	# arrows, bolts and fire aimed at this spirit
	for pr in get_tree().get_nodes_in_group(&"projectile"):
		if not is_instance_valid(pr) or not (pr.target_mask & BH.LAYER_PLAYER) or pr.source == self:
			continue
		var v: Vector3 = pr.velocity.slide(Vector3.UP)
		if v.length() < 1.0:
			continue
		var rel2: Vector3 = (pos - pr.global_position).slide(Vector3.UP)
		var ahead := rel2.dot(v.normalized())
		if ahead <= 0.0 or ahead > 7.0:
			continue
		var miss := absf(rel2.dot(v.normalized().cross(Vector3.UP)))
		if miss < pr.radius + body_radius + 0.25:
			var sgn2 := 1.0 if rel2.dot(v.normalized().cross(Vector3.UP)) >= 0.0 else -1.0
			escape += v.normalized().cross(Vector3.UP) * sgn2 * 2.0
			urgency = minf(urgency, ahead / v.length())
			needed = maxf(needed, 2.0)
	if escape.length() < 0.01:
		return false
	var dir2 := escape.normalized()
	# dodge roll with invulnerability when the blow is about to land; otherwise walk out and keep the roll
	var committed := action != null and not action.can_cancel() and action_kind != &"attack"
	if urgency < 0.5 and dodge_cd <= 0.0 and not committed:
		_log("dodge (%.2fs)" % urgency)
		_dodge(dir2)
		return true
	if committed and action.elapsed < action.first_hit_time() * 0.7:
		_cancel_action()
		committed = false
	if not committed:
		mode = Mode.EVADE
		_evade_t = clampf(urgency, 0.35, 1.2)
		_evade_goal = CombatQuery.reachable_point(get_world_3d(), pos, pos + dir2 * maxf(needed, 2.0), body_radius)
		_move_goal = _evade_goal
	return true

func _dodge(dir: Vector3) -> void:
	_cancel_action()
	var d := dir.slide(Vector3.UP)
	if d.length() < 0.01:
		d = -forward()
	d = d.normalized()
	var a := TimedAction.from_anim(&"dodge_roll", 1.0)
	_begin(a, &"dodge")
	if a.iframes.x < 0.0:
		a.iframes = Vector2(0.02, 0.4)
	rotation.y = atan2(d.x, d.z)
	var travel := (a.travel if a.travel > 0.0 else 4.0)
	var goal := CombatQuery.reachable_point(get_world_3d(), global_position, global_position + d * travel, body_radius)
	var t := maxf(0.15, a.iframes.y if a.iframes.y > 0.0 else a.duration * 0.6)
	dash(goal - global_position, global_position.distance_to(goal) / t, t)
	visual.play_action(&"dodge_roll", 1.0, 0.06)
	dodge_cd = stats.get_stat(&"dodge_cooldown", float(tdef.get("dodge_cooldown", 2.0))) * (0.75 if data.trait_id == &"swift" else 1.0)
	Audio.play_at(&"dodge_roll", global_position, -6.0)
	mode = Mode.EVADE
	_evade_t = t + 0.1

# ---- Movement -------------------------------------------------------------------------------------------------------

func dash(dir: Vector3, speed: float, duration: float) -> void:
	var d := dir.slide(Vector3.UP)
	_dash_vel = d.normalized() * speed if d.length() > 0.01 else forward() * speed
	_dash_t = duration

func _movement(delta: float) -> Vector3:
	if _dash_t > 0.0:
		_dash_t -= delta
		return _dash_vel
	var cur := Vector3(velocity.x, 0, velocity.z) - Vector3(knock_velocity.x, 0, knock_velocity.z)
	if status.is_disabled():
		return cur.move_toward(Vector3.ZERO, ACCEL * delta)
	var mult := action.move_mult if action != null else 1.0
	var goal := _move_goal
	if goal == Vector3.INF or mult <= 0.0:
		return cur.move_toward(Vector3.ZERO, ACCEL * delta)
	var to := (goal - global_position).slide(Vector3.UP)
	var speed := stats.get_stat(&"move_speed", 5.0)
	var arrive := 0.6 if mode == Mode.EVADE else (1.0 if mode == Mode.FOLLOW else 0.45)
	match mode:
		Mode.FOLLOW:
			var dp := _flat(owner_player.global_position)
			speed *= 1.35 if dp > 6.0 else (1.0 if dp > 3.5 else 0.7)
		Mode.RETREAT:
			speed *= 1.1
		Mode.EVADE:
			speed *= 1.3
	var v := Vector3.ZERO
	if to.length() > arrive:
		agent.target_position = goal
		var nxt := agent.get_next_path_position()
		var d := (nxt - global_position).slide(Vector3.UP)
		if d.length() < 0.05 or agent.is_navigation_finished():
			d = to
		v = d.normalized() * speed * mult
	# personal space: never stack on the hero, the other spirit or a monster
	var sep := Vector3.ZERO
	for n in get_tree().get_nodes_in_group(&"ally"):
		if n != self and is_instance_valid(n):
			sep += _push(n.global_position, 1.3)
	if owner_player:
		sep += _push(owner_player.global_position, 1.2)
	v += sep * speed * 0.8
	return cur.move_toward(v.limit_length(speed * 1.4), ACCEL * delta)

func _push(from: Vector3, min_d: float) -> Vector3:
	var off := (global_position - from).slide(Vector3.UP)
	var l := off.length()
	if l < min_d and l > 0.001:
		return off / l * (min_d - l) / min_d
	return Vector3.ZERO

## Walking at the hero's side: slot 0 behind-left, slot 1 behind-right.
func _formation_point() -> Vector3:
	var p := owner_player
	var f: Vector3 = p.global_transform.basis.z.slide(Vector3.UP).normalized()
	if f.length() < 0.1:
		f = Vector3.BACK
	var side := f.cross(Vector3.UP) * (1.6 if slot_index % 2 == 0 else -1.6)
	return p.global_position - f * 2.0 + side

func _face(delta: float, desired: Vector3) -> void:
	if action_kind == &"dodge" or (action != null and action.elapsed > action.first_hit_time() - 0.05 and action.first_hit_time() >= 0.0):
		return
	var look := Vector3.ZERO
	if mode == Mode.ENGAGE and target and is_instance_valid(target):
		look = target.global_position - global_position
	elif desired.length() > 0.3:
		look = desired
	look.y = 0.0
	if look.length() > 0.1:
		rotation.y = lerp_angle(rotation.y, atan2(look.x, look.z), clampf(TURN_RATE * delta, 0.0, 1.0))

func _face_now(p: Vector3) -> void:
	var d := (p - global_position).slide(Vector3.UP)
	if d.length() > 0.05:
		rotation.y = atan2(d.x, d.z)

func _track_progress(delta: float) -> void:
	_progress_t += delta
	if _progress_t < 1.0:
		return
	var moved := global_position.distance_to(_last_pos)
	var wants := _move_goal != Vector3.INF and _flat(_move_goal) > 2.0 and action == null
	_stuck_t = _stuck_t + _progress_t if wants and moved < 0.4 else 0.0
	_last_pos = global_position
	_progress_t = 0.0

## Rejoin the hero at once: the dead walk where they please.
func _rejoin_hero() -> void:
	var p := owner_player
	var spot := _formation_point()
	spot = CombatQuery.reachable_point(get_world_3d(), p.global_position, spot, body_radius)
	FX.spawn(VFXLib.particles(Color(0.6, 0.95, 1.0, 0.8), 20, 0.6, true, 0.1, 2.4, 180.0, Vector3(0, 1.0, 0), 0.4), center())
	teleport_to(CombatQuery.ground_at(get_world_3d(), spot))
	FX.spawn(VFXLib.particles(Color(0.6, 0.95, 1.0, 0.8), 20, 0.6, true, 0.1, 2.4, 180.0, Vector3(0, 1.0, 0), 0.4), center())
	_stuck_t = 0.0
	_cancel_action()
	mode = Mode.FOLLOW
	_log("rejoined the hero")

func teleport_to(p: Vector3) -> void:
	global_position = p + Vector3.UP * 0.05
	velocity = Vector3.ZERO
	knock_velocity = Vector3.ZERO
	_last_pos = global_position

# ---- Queries --------------------------------------------------------------------------------------------------------

func _flat(p: Vector3) -> float:
	return Vector2(p.x - global_position.x, p.z - global_position.z).length()

func _enemies(r: float, around := Vector3.INF) -> Array:
	var c := global_position if around == Vector3.INF else around
	var out := []
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e.alive and Vector2(e.global_position.x - c.x, e.global_position.z - c.z).length() < r:
			out.append(e)
	return out

func _nearest_enemy() -> Enemy:
	var best: Enemy = null
	var bd := INF
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if not e.alive or not e.is_aggressive():
			continue
		var d := _flat(e.global_position)
		if d < bd:
			bd = d
			best = e
	return best

func _nearest_enemy_dist() -> float:
	var e := _nearest_enemy()
	return _flat(e.global_position) if e else INF

func _enemies_in_front(r: float, arc: float) -> int:
	return CombatQuery.actors_in_arc(get_world_3d(), global_position, forward(), r, arc, BH.LAYER_ENEMY).size()

func _has_los(t: Node3D) -> bool:
	return not CombatQuery.blocked(get_world_3d(), center(), (t as Actor).center() if t is Actor else t.global_position)

func _on_damage_event(victim: Node, r: DamageResult, _pos: Vector3, attacker: Node) -> void:
	if victim == owner_player and attacker is Enemy and r and not r.evaded:
		_hero_hits[attacker.get_instance_id()] = _time

# ---- Damage intake --------------------------------------------------------------------------------------------------

func receive_hit(req: DamageRequest, attacker: Node = null, hit_point := Vector3.INF) -> DamageResult:
	if action != null and action.in_iframes() and req.kind != DamageRequest.Kind.DOT:
		var r0 := DamageResult.new()
		r0.evaded = true
		Events.damage_dealt.emit(self, r0, center(), attacker)
		return r0
	var res := super.receive_hit(req, attacker, hit_point)
	if not res.evaded and req.kind != DamageRequest.Kind.DOT:
		_combat_t = 0.0
	return res

func _on_damaged(result: DamageResult, _req: DamageRequest) -> void:
	if result.total <= 0 or visual == null:
		return
	var heavy := result.total > max_hp() * 0.15 or result.knockback >= HEAVY_KNOCK
	if heavy and action != null and action_kind != &"dodge":
		_cancel_action()
	if action == null:
		visual.play_reaction(&"hit_heavy" if heavy else &"hit")

func _on_staggered(_broken: bool) -> void:
	_cancel_action()
	visual.play_reaction(&"stagger")

func apply_knockback(dir: Vector3, speed: float, source: DerivedStats, source_node: Node, depth := 0, launch := 0.0) -> void:
	if action != null and action.in_iframes():
		return
	super.apply_knockback(dir, speed, source, source_node, depth, launch)

func die(killer: Node) -> void:
	if not alive:
		return
	_cancel_action()
	super.die(killer)
	collision_layer = 0
	_dead_since = _time
	sync_data()
	remove_from_group(&"ally")
	Events.tempo_fallen.emit(self)
	Events.tempo_changed.emit(data.uid)
	Events.notify.emit("%s has fallen. Veyra Ashgrave can call the spirit back." % data.tempo_name, &"error")
	Audio.play_at(&"body_fall", global_position)
	if _bar:
		_bar.visible = false
	# the spirit loosens and drifts away
	var tw := create_tween()
	tw.tween_interval(1.4)
	tw.tween_callback(func() -> void:
		FX.spawn(VFXLib.particles(Color(0.6, 0.95, 1.0, 0.9), 40, 1.8, true, 0.12, 1.6, 40.0, Vector3(0, 2.5, 0), 0.6), center()))
	tw.tween_method(func(v: float) -> void: visual.set_opacity(v), 0.84, 0.0, 1.6)
	tw.parallel().tween_property(_light, "light_energy", 0.0, 1.6)
	tw.tween_callback(queue_free)

func _fell_out() -> void:
	_rejoin_hero()

func debug_text() -> String:
	return "%s %s %s  hp %d%%  mp %d  %s" % [data.tempo_name, data.class_name_text(), mode_name(), roundi(hp_frac() * 100.0), roundi(mana),
		("-> " + target.display_name) if target and is_instance_valid(target) else ""]
