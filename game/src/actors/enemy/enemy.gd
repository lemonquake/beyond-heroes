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
## bh-028: attack kinds Evasion meets at full odds; every other attack kind is an area hit that can only be grazed.
const DIRECT_KINDS := ["melee", "dash", "charge", "projectile", "chain", "tongue"]

var def: EnemyDef
var brain := EnemyBrain.new()
var elite_mods: Array[StringName] = []
var is_elite := false
var is_boss := false
var encounter_hp_mult := 1.0
## A named champion holding a camp (DataMinibosses entry) or empty (bh-007).
var miniboss: Dictionary = {}
var difficulty := {}
var home := Vector3.ZERO
var patrol_radius := 5.0
var zone: Node3D
var agent: NavigationAgent3D
var target: Actor                    # the hero or one of the hero's Tempos (threat decides; taunts override)
var bar: EnemyBar

var action: TimedAction
var current_attack := {}
var cooldowns := {}                  # attack/ability id -> seconds
## bh-028: attacks this monster has on top of its def (the level 40+ hex, DataEnemies.hex_attack).
var extra_attacks: Array = []
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
var _falls := 0                     # times it fell out of the world on its own (see _fell_out)
var _idle_sound_t := 0.0
var _think_offset := 0.0
var _phase_lock := 0.0
var _anim_pref: StringName = &""
# bh-003: deaths, corpses and signature traits
const MAX_CORPSES := 24
static var _corpses: Array = []           # oldest first; beyond MAX_CORPSES the oldest decays at once
var _last_res: DamageResult
var _last_req: DamageRequest
var _reassembled := false
var _reassembling := false
var _decaying := false
var _pool: Decal
var _devour_cd := 0.0
var _devour_target: Enemy
var _stealth := 1.0
var _stealth_reveal := 0.0
var _stolen_gold := 0
var _enrage_done := false
# bh-004: who to fight — the hero or a Tempo
const THREAT_DECAY := 0.12            # fraction of threat forgotten per second
const HERO_BIAS := 1.25               # the hero is the monsters' first choice
var _threat := {}                     # attacker instance id -> threat (damage dealt, decaying)
var _taunt_by: Actor
var _taunt_t := 0.0
var _retarget_t := 0.0
## Networking (bh-008): on a client every monster is a replica of the host's — no AI, moved and animated by the host's
## snapshots; blows on it are resolved here and applied by the host; it dies when the host says so.
var net_replica := false
var _net_pos := Vector3.ZERO
var _net_yaw := 0.0
var _net_vel := Vector3.ZERO
var _net_serial := -1
var _net_engaged := false
var _net_age := 0.0                 # seconds since the last snapshot (dead reckoning between snapshots, bh-035)
## bh-010: the new monsters' signature mechanics live in a helper (null for the older roster).
const TraitsExt := preload("res://src/actors/enemy/enemy_traits_ext.gd")
## bh-013: the twenty-one new monsters' mechanics extend that helper (one `ext` serves both).
const TraitsX := preload("res://src/actors/enemy/enemy_traits_x.gd")
var ext: TraitsX
var risen := false                    # raised by a Necromancer: a weaker Hollow Soldier that cannot rise again
var summoner: Node                    # who raised / summoned / planted it (null for camp monsters)
var _bone_ward := 0.0                 # part of shield_hp that is a Necromancer's Bone Ward

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
	extra_attacks = DataEnemies.extra_attacks(def, level)
	return self

## Turn this (elite) enemy into a named miniboss before it enters the tree: its name, size and weight.
func make_miniboss(md: Dictionary) -> Enemy:
	miniboss = md
	display_name = String(md.name)
	var sc := float(md.get("scale", 1.2))
	body_radius = def.body_radius * minf(sc, 1.3)
	body_height = def.body_height * sc
	weight *= sc * 1.5
	return self

func is_miniboss() -> bool:
	return not miniboss.is_empty()

func _ready() -> void:
	super._ready()
	var size_mult := float(get_meta(&"size_mult", 1.0))
	if size_mult != 1.0:
		body_radius *= size_mult
		body_height *= size_mult
		weight *= size_mult
	team = BH.Team.ENEMY
	add_to_group(&"enemy")
	if is_boss:
		add_to_group(&"boss")
	collision_layer = BH.LAYER_ENEMY
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_PLAYER | BH.LAYER_ENEMY
	rest_skip = true
	_sep_phase = get_instance_id() % SEP_EVERY      # staggered: a third of the pack refreshes each step
	_lod_skip = (hash(get_instance_id()) & 1) == 1     # half the crowd thinks on even steps, half on odd
	# a jammed pack pushes into itself every step: 3 slide iterations instead of 6 halve that worst case, and nothing
	# a monster walks along needs more (bh-014)
	max_slides = 3
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
	visual.full_sync = is_boss or is_miniboss()
	visual.crowd_lod = not visual.full_sync      # bh-035: an ordinary monster may animate at a coarser rate in a crowd
	add_child(visual)
	var sc := def.model_scale * (1.12 if is_elite else 1.0) * float(miniboss.get("scale", 1.0)) * size_mult
	# bh-031: humanoid monsters are the hero's own body in their family's look and gear (DataPersonas)
	var persona := Persona.for_enemy(def)
	if not persona.is_empty():
		visual.setup(Persona.MODEL, sc * float(persona.get("size", 1.0)), def.tint, &"")
		Persona.apply(visual, persona)
	else:
		visual.setup(CreatureSwaps.model(def.model), sc, def.tint, &"")
		visual.clip_alias = CreatureSwaps.aliases(def.model)
	if def.weapon != "":
		visual.attach_weapon(&"main", def.weapon)
	visual.float_hover = float(def.anim_map.get("hover", 1.2))
	visual.float_core_spin = float(def.anim_map.get("core_spin", 0.0))
	if visual.fallback:
		_shape_fallback()
	visual.set_stance(_idle_anim())
	for sid in def.status_immune:
		status.immunities[StringName(sid)] = true
	if is_boss:
		status.immunities[&"feared"] = true
	if TraitsExt.wants(def) or TraitsX.wants_x(def):
		ext = TraitsX.new(self)
	# bh-042: the Abyss bosses carry a dim light of their own (their floors are nearly dark)
	if DataEnemiesAbyss.NAMES.has(def.id):
		AbyssMoves.presence(self)
	# bh-042: every other boss met at level 90 or deeper learns the Abyss's moves (Curse of Stillness, Armour Rip and a
	# bullet pattern of its own), from its second phase
	elif is_boss and level >= Abyss.FULL and not net_replica:
		extra_attacks.append_array(AbyssMoves.overhaul(def))
		if ext == null:
			ext = TraitsX.new(self)
	status.grants_stagger_window = is_elite or is_boss
	mark_stats_dirty()
	ensure_stats()
	hp = max_hp()
	mana = max_mana()
	if is_elite:
		_apply_elite_visuals()
		if stats.has_flag(&"ward"):
			shield_hp = max_hp() * stats.flag(&"ward")
			status.apply(&"elite_shield", 0.0)
	home = global_position
	if risen and visual:
		visual.set_rim(Color(0.4, 1.0, 0.55), 0.7)
	_think_offset = rng.randf() * THINK_INTERVAL
	_think_t = _think_offset
	_strafe_dir = 1.0 if rng.randf() < 0.5 else -1.0
	brain.go(EnemyBrain.State.PATROL if patrol_radius > 0.5 and not is_boss else EnemyBrain.State.IDLE)
	if ext:
		ext.setup()
	if ext == null or not ext.dormant:
		make_bar()

## The floating health bar (a dormant Mimic has none until it wakes).
func make_bar() -> void:
	if bar != null and is_instance_valid(bar):
		return
	bar = EnemyBar.new()
	bar.setup(self)
	add_child(bar)

func has_trait(t: StringName) -> bool:
	return def != null and def.traits.has(t)

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
		&"spider", &"mimic", &"totem":
			# bh-010 creatures before their models exist: a readable stand-in shape instead of a person
			for c in visual.model.get_children():
				if c is MeshInstance3D:
					c.visible = false
			var mat := StandardMaterial3D.new()
			mat.albedo_color = def.tint
			mat.roughness = 0.7
			var mi := MeshInstance3D.new()
			match def.body_shape:
				&"spider":
					var s := SphereMesh.new()
					s.radius = 0.6
					s.height = 0.7
					mi.mesh = s
					mi.position = Vector3(0, 0.55, -0.2)
					for i in 8:
						var leg := MeshInstance3D.new()
						var bx := BoxMesh.new()
						bx.size = Vector3(1.3, 0.08, 0.08)
						leg.mesh = bx
						leg.material_override = mat
						var side := -1.0 if i < 4 else 1.0
						leg.position = Vector3(side * 0.7, 0.45, -0.5 + float(i % 4) * 0.3)
						leg.rotation.z = side * 0.5
						visual.model.add_child(leg)
				&"mimic":
					var b := BoxMesh.new()
					b.size = Vector3(1.1, 0.75, 0.7)
					mi.mesh = b
					mi.position.y = 0.38
					mat.albedo_color = Color(0.45, 0.3, 0.16)
				&"totem":
					var cy := CylinderMesh.new()
					cy.top_radius = 0.22
					cy.bottom_radius = 0.3
					cy.height = 2.2
					mi.mesh = cy
					mi.position.y = 1.1
			mi.material_override = mat
			visual.model.add_child(mi)

func _idle_anim() -> StringName:
	if def.body_shape != &"humanoid":
		return &"idle"
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
	if is_miniboss():
		mods.append(StatModifier.more(&"max_hp", float(miniboss.get("hp", 2.0)) - 1.0, "Champion"))
		mods.append(StatModifier.more(&"outgoing_damage", float(miniboss.get("damage", 1.2)) - 1.0, "Champion"))
		mods.append(StatModifier.more(&"poise", 0.8, "Champion"))
		mods.append(StatModifier.flat(&"knockback_res", 0.25, "Champion"))
		mods.append(StatModifier.flat(&"threat_rank", float(CombatBudget.Rank.CHAMPION)))
	if risen:
		mods.append(StatModifier.more(&"max_hp", TraitsExt.RISEN_HP - 1.0, "Risen"))
		mods.append(StatModifier.more(&"outgoing_damage", TraitsExt.RISEN_DAMAGE - 1.0, "Risen"))
	if ext:
		ext.stat_mods(mods)
	if encounter_hp_mult != 1.0:
		mods.append(StatModifier.more(&"max_hp", encounter_hp_mult - 1.0, "Encounter health"))
	stats = EnemyStats.build(def, level, difficulty, mods, is_elite, is_boss)
	if ext:
		ext.post_stats(stats)

# ---- Main loop -----------------------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	if net_replica:
		_net_step(delta)
		return
	ensure_stats()
	if Game.debug_freeze_ai and alive:
		velocity = Vector3.ZERO      # bh-030: the Debug console froze every monster in place
		return
	if _sim_sleep(delta):
		return
	var step := delta                         # the physics step: what moves the body
	if _crowd_half():
		_lod_skip = not _lod_skip              # each monster alternates on its own (tests step monsters by hand)
		if _lod_skip:
			_lod_acc += delta
			_coast(delta)
			return
		delta += _lod_acc                     # the thinking catches up with the step it skipped
	_lod_acc = 0.0
	status.tick(delta)
	if not alive:
		physics_move(step, Vector3.ZERO)
		return
	if ext and ext.pre_tick(delta):
		physics_move(step, Vector3.ZERO)       # a dormant Mimic, a War Totem: no AI this frame
		return
	brain.tick(delta)
	_tick_cooldowns(delta)
	_elite_tick(delta)
	_trait_tick(delta)
	_select_target(delta)
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
	physics_move(step, desired)
	_face(delta, desired)
	if visual:
		var hv := Vector3(velocity.x, 0, velocity.z)
		var local := global_transform.basis.inverse() * hv
		visual.update_locomotion(Vector2(local.x, local.z), brain.is_engaged(), 0.0, delta)
	_ambient_sound(delta)

## Crowd LOD (bh-035). In a big fight most of the pack is waiting for one of the CombatDirector's few attack tokens:
## circling at its slot, closing in, backing off. Those monsters think, steer and collide on every other physics step (each
## half of the crowd on its own step, so the cost is spread evenly) and coast along their velocity in between. A monster that
## attacks, casts, charges, is staggered, knocked back or airborne, holds a token, or is a boss always runs every step, and
## small fights (CROWD_LOD_FROM awake monsters or fewer; half that in efficiency mode) are never thinned. A 40-monster brawl spent ~9 ms per physics step,
## which pushed frames past 16.7 ms and made the engine run two steps per frame.
const CROWD_LOD_FROM := 14
var _lod_acc := 0.0
var _lod_skip := false

func _crowd_half() -> bool:
	if _awake_n <= (CROWD_LOD_FROM if not Perf.lite else CROWD_LOD_FROM / 2) or not alive or is_boss or net_replica or not miniboss.is_empty() or action != null or not _charge.is_empty():
		return false
	if knock_velocity != Vector3.ZERO or _airborne_from_launch or not is_on_floor():
		return false
	var S := EnemyBrain.State
	if brain.state in [S.ATTACK, S.SPECIAL, S.CAST, S.STAGGER, S.KNOCKBACK, S.DEAD]:
		return false
	if ext and (ext.fuse_lit or not ext.jobs.is_empty()):
		return false
	return CombatDirector.current == null or not CombatDirector.current.has_token(self)

## The skipped step of a thinned monster: keep walking along the current velocity and keep turning, no collision test
## (one step is a few centimetres; the next full step's move_and_slide resolves any overlap).
func _coast(delta: float) -> void:
	var hv := Vector3(velocity.x, 0.0, velocity.z)
	if hv.length_squared() > 0.0025:
		global_position += hv * delta
	_face(delta, hv)

## Simulation LOD (bh-009 efficiency mode; every platform since bh-014): a calm monster far beyond sight of every hero
## dozes — standing on the ground, nothing to fight, nothing burning — and only checks twice a second whether a hero
## has come near. The whole simulation (perception, steering, physics, animation blending) resumes the moment it wakes,
## well outside its sight range and off screen, so nobody ever sees it happen. Like the "active zone" of Diablo-style
## ARPGs: a map of 50 monsters only pays for the handful around the heroes.
var _asleep := false
var _sleep_check := 0.0

func _sim_sleep(delta: float) -> bool:
	if _asleep:
		_sleep_check -= delta
		if _sleep_check > 0.0:
			return true
		_sleep_check = 0.5
		if _should_sleep():
			return true
		_asleep = false
		agent.process_mode = Node.PROCESS_MODE_INHERIT
		if visual:
			visual.set_process(true)
		return false
	_sleep_check -= delta
	if _sleep_check > 0.0:
		return false
	_sleep_check = 0.5 + rng.randf() * 0.05     # spread the checks so a map of monsters never checks on one frame
	if not _should_sleep():
		return false
	_asleep = true
	velocity = Vector3.ZERO
	agent.process_mode = Node.PROCESS_MODE_DISABLED
	if visual:
		visual.set_process(false)
	return true

func _should_sleep() -> bool:
	if not alive or is_boss or brain.is_engaged() or not is_on_floor() or knock_velocity != Vector3.ZERO:
		return false
	for id in status.statuses:
		if not status.statuses[id].infinite:       # standing markers (Troll Blood, Rune Shift) do not keep it awake
			return false
	if ext and (ext.fuse_lit or not ext.jobs.is_empty()):
		return false
	var hero := Game.player as Node3D
	if hero == null or not is_instance_valid(hero) or not hero.is_inside_tree():
		return false
	var wake := maxf(48.0, def.sight_range * 1.5 + 8.0)
	if global_position.distance_squared_to(hero.global_position) <= wake * wake:
		return false
	# the host simulates every monster: another player's hero keeps the ones around them awake (bh-008 multiplayer)
	for h: Node3D in get_tree().get_nodes_in_group(&"net_hero"):
		if h.is_inside_tree() and global_position.distance_squared_to(h.global_position) <= wake * wake:
			return false
	return true

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
	if status.has(&"feared") and (action != null or brain.is_busy()):
		_interrupt()                               # terror breaks off any attack or cast
		brain.go(S.POSITION)
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
		# bh-040: in the Descent a playing hit reaction no longer holds a monster down past STAGGER_HOLD_MAX
		var held := brain.time_in_state > Descent.STAGGER_HOLD_MAX and Descent.active(level)
		if brain.time_in_state > 0.25 and (visual == null or not visual.is_busy() or held):
			brain.go(S.POSITION if target and target.alive else S.CHASE)

func _interrupt() -> void:
	if action:
		action.finish(false)
		action = null
	if visual and visual.current_action() == &"devour":
		visual.stop_action()
	_charge = {}
	if CombatDirector.current:
		CombatDirector.current.release_token(self)
	current_attack = {}

# ---- Targets: the hero or a Tempo ----------------------------------------------------------------------------

## Pick whom to fight. A taunt wins while it lasts; otherwise threat (damage taken from each of them, decaying), with a
## bias toward the hero, a pull toward whoever is close, and stickiness so the monster does not flicker between foes.
func _select_target(delta: float) -> void:
	for k in _threat.keys():
		_threat[k] *= maxf(0.0, 1.0 - THREAT_DECAY * delta)
		if _threat[k] < 0.5:
			_threat.erase(k)
	if _taunt_t > 0.0:
		_taunt_t -= delta
		if _taunt_by and is_instance_valid(_taunt_by) and _taunt_by.alive:
			target = _taunt_by
			return
		_taunt_t = 0.0
	var hero := Game.player as Actor
	var valid := target != null and is_instance_valid(target) and target.alive and not _hidden(target)
	_retarget_t -= delta
	if valid and _retarget_t > 0.0:
		return
	_retarget_t = 2.5 if is_boss else 1.0
	# a hero in Stealth (Smoke Veil) is not a candidate at all: the monster loses them until they show again
	var best: Actor = hero if hero and is_instance_valid(hero) and not _hidden(hero) else null
	var best_s := _target_score(best) if best else -INF
	# other players' heroes are targets only where the host resolves their hits (bh-015: in a client's own world they
	# are visitors the monsters cannot hurt, so they are not chased either)
	var others: Array = get_tree().get_nodes_in_group(&"net_ally") if Net.is_world_authority() else []
	for t in get_tree().get_nodes_in_group(&"tempo") + others:
		if not t.alive or _hidden(t):
			continue
		var sc := _target_score(t)
		if sc > best_s:
			best_s = sc
			best = t
	if best == null:
		target = hero if hero and is_instance_valid(hero) and not _hidden(hero) else null
	elif valid and best != target and best_s < _target_score(target) * 1.15 + 2.0:
		return   # not worth switching
	else:
		target = best

func _target_score(a: Actor) -> float:
	if a == null or not is_instance_valid(a) or not a.alive:
		return -INF
	var threat := float(_threat.get(a.get_instance_id(), 0.0))
	var d := global_position.distance_to(a.global_position)
	var hero := a is Player or a.is_in_group(&"net_hero")     # another player's hero counts as a hero (bh-008)
	var sc := threat * (HERO_BIAS if hero else 1.0) - d * 1.5
	if hero:
		sc += 6.0
	if a == target:
		sc += 3.0
	return sc

## The foe is swinging or casting right now (shield bearers raise their guard).
func _target_winding_up() -> bool:
	return target != null and is_instance_valid(target) and target.current_action() != null

func _hidden(a: Actor) -> bool:
	return a.has_method(&"is_hidden") and a.call(&"is_hidden")

## A Tempo's Grave Challenge: fight me instead (bosses shrug it off twice as fast).
func taunt(by: Actor, duration: float) -> void:
	if not alive or by == null:
		return
	_taunt_by = by
	_taunt_t = duration * (0.5 if is_boss else 1.0)
	target = by
	_threat[by.get_instance_id()] = float(_threat.get(by.get_instance_id(), 0.0)) + max_hp() * 0.1
	if not brain.is_engaged():
		alert_to(by.global_position)
	FX.text_popup(center() + Vector3.UP * 0.8, "Taunted", Color(0.7, 0.9, 1.0), 0.8)

## Lose sight of `who` (smoke): pick someone else at once.
func lose_target(who: Actor) -> void:
	if who and _threat.has(who.get_instance_id()):
		_threat[who.get_instance_id()] *= 0.3
	if _taunt_by == who:
		_taunt_t = 0.0
	if target == who:
		var hero := Game.player as Actor
		target = hero if hero and is_instance_valid(hero) and hero != who and not _hidden(hero) else null
		_retarget_t = 1.5 if target else 0.0

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
		if is_boss or is_miniboss():
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
	# Feared (Shadowblade / Ranger skills): run from whoever scared it, no attacks while it lasts.
	if status.has(&"feared"):
		brain.go(S.RETREAT)
		var from: Node3D = last_attacker as Node3D if last_attacker is Node3D and is_instance_valid(last_attacker) else target
		var away := (global_position - from.global_position).slide(Vector3.UP)
		if away.length() < 0.1:
			away = -forward()
		_move_target = CombatQuery.reachable_point(get_world_3d(), global_position, global_position + away.normalized() * 5.0, body_radius)
		return
	if ext and ext.think():
		return
	if _try_devour():
		return
	# Cowards flee when hurt and alone.
	if has_trait(&"cowardly") and hp < max_hp() * 0.35 and _nearest_ally(8.0) == null:
		brain.go(S.RETREAT)
		if brain.time_in_state < 0.3 or _move_target == Vector3.INF or global_position.distance_to(_move_target) < 1.0:
			_move_target = _retreat_point()
		return
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
	if def.blocks_front and _target_winding_up() and _dist < 4.0 and rng.randf() < 0.55 * float(difficulty.get("aggression", 1.0)):
		if brain.go(S.DEFEND):
			_defend_t = rng.randf_range(0.8, 1.6)
			visual.set_upper(&"block_loop")
			return
	if brain.state == S.DEFEND:
		_defend_t -= THINK_INTERVAL
		if _defend_t > 0.0 and _target_winding_up():
			return
		visual.set_upper(&"")
	var atk := _choose_attack()
	if not atk.is_empty():
		var kind: StringName = &"ranged" if atk.kind in ["projectile", "chain", "tongue"] else &"melee"
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
	for a in def.attacks + extra_attacks:
		var id: StringName = a.id
		if cooldowns.has(id):
			continue
		if int(a.get("phase", 1)) > phase:
			continue
		var rng_m := float(a.get("range", 2.0)) + body_radius
		if _dist > rng_m or _dist < float(a.get("min_range", 0.0)):
			continue
		if a.kind in ["projectile", "aoe", "charge", "dash", "chain", "tongue", "tether", "gaze", "beam", "strikes", "barrage", "armor_rip"] and not _has_los:
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
	req.kind = DamageRequest.Kind.ATTACK if String(a.get("kind", "")) in ["melee", "dash", "charge"] else DamageRequest.Kind.SPELL
	req.attacker = stats
	req.use_weapon = false
	var rr := EnemyStats.attack_range(def, stats, float(a.get("mult", 1.0)))
	req.base_min = rr.x
	req.base_max = rr.y
	var el := _atk_element(a)
	if el != Elements.PHYSICAL:
		req.conversion = {el: 1.0}
		if req.kind == DamageRequest.Kind.ATTACK:
			req.conversion = {el: 0.6}
	req.knockback = float(a.get("knockback", 2.0))
	req.poise = float(a.get("poise", 8.0))
	req.label = "%s: %s" % [def.display_name, a.id]
	# bh-028: aimed blows are evaded at full odds; everything else (blasts, pools, strikes, beams) can be grazed
	req.evadable = true
	req.graze = not a.kind in DIRECT_KINDS
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

## The element an attack deals (the Rune Golem's follow its core).
func _atk_element(a: Dictionary) -> int:
	return ext.attack_element(a) if ext else int(a.get("element", Elements.PHYSICAL))

func _start_attack(a: Dictionary) -> void:
	var S := EnemyBrain.State
	var special: bool = a.kind in ["aoe", "charge", "pools", "summon", "bud", "dash", "tongue", "bone_circle", "rift", "tether", "strikes", "mines", "gaze", "beam", "barrage", "curse_zone", "armor_rip"]
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
	_ensure_timing(act, a.kind == "melee" or a.kind == "dash")
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
			if has_trait(&"aim_line") and windup > 0.0 and target:
				var ad := (target.global_position - global_position).slide(Vector3.UP)
				var tl := VFXLib.telegraph("line", Vector2(minf(ad.length() + 2.0, float(a.get("range", 15.0))), 0.22), windup, Color(1.0, 0.2, 0.15, 0.55))
				FX.spawn(tl, global_position)
				tl.rotation.y = atan2(ad.x, ad.z)
				get_tree().create_timer(windup + 0.05, false).timeout.connect(tl.queue_free)
		"aoe":
			var center := global_position if a.get("self_centered", false) else aim_at
			if a.has("offset"):
				center = global_position + forward() * float(a.offset)
			var total_delay: float = act.release_t if act.release_t >= 0.0 else (act.windows[0][0] if not act.windows.is_empty() else 0.8)
			total_delay = maxf(total_delay, windup)
			if a.has("lob"):
				# thrown: the missile leaves the hand at the release frame and lands when the circle fills; a fused
				# bomb (bh-010) lands early and lies sparking for `fuse` seconds before the circle fills
				var land := CombatQuery.ground_at(get_world_3d(), center)
				var throw_at := act.release_t if act.release_t >= 0.0 else windup
				total_delay = maxf(total_delay, throw_at + 0.55)
				var fuse := float(a.get("fuse", 0.0))
				var flight := total_delay - throw_at
				total_delay += fuse
				get_tree().create_timer(maxf(throw_at, 0.01), false).timeout.connect(func() -> void:
					if not alive:
						return
					var from := visual.weapon_point(&"main", 0.2) if visual else center()
					if String(a.lob) == "bomb":
						Lob.throw_node(FX.world, TraitsExt.fuse_bomb_body(), from, land, flight, Color(1.0, 0.7, 0.3))
						if fuse > 0.0:
							get_tree().create_timer(flight, false).timeout.connect(func() -> void:
								var lying := TraitsExt.fuse_bomb_body()
								FX.spawn(lying, land + Vector3.UP * 0.2)
								if is_instance_valid(lying) and lying.is_inside_tree():
									lying.get_tree().create_timer(fuse, false).timeout.connect(lying.queue_free))
					else:
						Lob.throw(FX.world, String(a.lob), from, land, flight))
			_telegraph_aoe(a, center, total_delay)
		"dash":
			var dist := minf(float(a.get("dash", 5.0)), _dist)
			var t_hit := maxf(0.1, act.first_hit_time())
			_charge = {"dir": (aim_at - global_position).slide(Vector3.UP).normalized(), "speed": dist / maxf(t_hit - windup, 0.1), "left": t_hit - windup, "delay": windup, "hit": false, "a": a, "lunge": true}
			act.on_window = func(w: int, first: bool) -> void: _melee_hit(a, act, w)
		"charge":
			var dir := (aim_at - global_position).slide(Vector3.UP).normalized()
			var length := minf(float(a.get("range", 20.0)), _dist + 4.0)
			# bh-033: a standing impact pillar just behind the baiting hero is where the charge ends (the warning line
			# shows it), so standing in front of a pillar always works as bait
			if is_boss:
				var all := ArenaState.pillars(Game.current_map)
				var gone := ArenaState.broken(Game.current_map)
				for i in all.size():
					if gone.has(i):
						continue
					var off: Vector3 = ((all[i] as Node3D).global_position - global_position).slide(Vector3.UP)
					var along := off.dot(dir)
					if along > _dist and along < float(a.get("range", 20.0)) + 8.0 and (off - dir * along).length() < body_radius + 1.0:
						length = maxf(length, along)
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
				visual.hold_action(StringName(a.get("hold_anim", &"boss_charge" if is_boss or def.archetype == &"brute" else &"run_combat")))
		"pools":
			act.on_release = func() -> void: _pools(a)
		"bud":
			act.on_release = func() -> void: _plant_buds(a)
		"summon":
			act.on_release = func() -> void: _summon(a)
		"chain":
			act.on_release = func() -> void:
				if ext:
					ext.chain(a)
		"tongue":
			act.on_release = func() -> void:
				if ext:
					ext.tongue(a)
		_:
			if ext:
				ext.start_special(a, act)
	Audio.play_at(&"swing_heavy" if special else &"swing_light", global_position, -4.0)
	if ext:
		ext.attack_started(a)

## Clips without timing metadata (a creature model that has not been delivered yet) still hit: a release at mid-clip and,
## for melee, a short window around it.
func _ensure_timing(act: TimedAction, melee: bool) -> void:
	if melee and act.windows.is_empty():
		act.windows.append([act.duration * 0.4, act.duration * 0.55])
	if act.release_t < 0.0:
		act.release_t = act.windows[0][0] if not act.windows.is_empty() else act.duration * 0.5

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
	var res := target.receive_hit(req, self, target.center())
	if has_trait(&"pickpocket") and res and not res.evaded and target is Player and (target as Player).hero and (target as Player).hero.inventory.gold > 0:
		var inv: Inventory = (target as Player).hero.inventory
		var take := mini(inv.gold, clampi(int(inv.gold * 0.04) + 1, 1, 25))
		inv.gold -= take
		inv.changed.emit()
		_stolen_gold += take
		FX.text_popup(target.center() + Vector3.UP * 0.8, "-%d gold" % take, Color(1.0, 0.8, 0.3), 0.9)
	FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 0.5, 0.4, 0.6), reach, arc, 1.0, 0.2, 0.5), global_position, forward())

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
	var el := _atk_element(a)
	var look := "arrow" if a.get("projectile", "") == "arrow" else "orb"
	var on_hit_status: Dictionary = a.get("on_hit_status", {})
	for i in count:
		var ang := 0.0 if count == 1 else lerpf(-spread * 0.5, spread * 0.5, float(i) / float(count - 1))
		var pr := Projectile.spawn(FX.world, from, dir.rotated(Vector3.UP, deg_to_rad(ang)), speed, _attack_request(a), self, BH.LAYER_PLAYER, el, look)
		pr.max_range = float(a.get("range", 15.0)) + 4.0
		pr.radius = 0.3
		pr.hit_sound = &"arrow_impact" if look == "arrow" else Elements.SFX_HIT[el]
		if not on_hit_status.is_empty():
			pr.on_hit = func(t, res, _p) -> void: apply_hit_statuses(t, res, on_hit_status)

## Web / mud / jinx: statuses a connecting blow applies outright ({id: seconds}), not through buildup.
func apply_hit_statuses(t: Node, res: DamageResult, sts: Dictionary) -> void:
	if not (t is Actor) or res == null or res.evaded or not (t as Actor).alive:
		return
	for sid in sts:
		(t as Actor).status.apply(StringName(sid), float(sts[sid]))

func _telegraph_aoe(a: Dictionary, at: Vector3, delay: float) -> void:
	var shape := String(a.get("telegraph", "circle"))
	var radius := float(a.get("radius", 3.0))
	var req := _attack_request(a)
	var el := _atk_element(a)
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
			FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 0.45, 0.3, 0.8), radius, arc, 1.2, 0.3, 0.7), global_position, forward())
			Events.camera_shake.emit(0.3))
		return
	var blast := AreaEffects.delayed(FX.world, CombatQuery.ground_at(get_world_3d(), at), radius, delay, req, self, BH.LAYER_PLAYER,
		a.get("tele_color", Color(1.0, 0.25, 0.1, 0.75)), "ring" if shape == "ring" else "circle", float(a.get("inner_radius", 0.0)))
	if a.get("hex", false):
		# bh-028: a curse sigil, not a slam — no shake, a violet burst and a word over whoever it caught
		blast.on_blast = func(pos: Vector3, hits: Array) -> void:
			FX.spawn(VFXLib.ring_wave(Color(0.7, 0.3, 1.0), radius, 0.5, 0.9), pos)
			FX.spawn(VFXLib.light_flash(Color(0.6, 0.2, 1.0), 4.0, 5.0, 0.25), pos + Vector3.UP)
			Audio.play_at(&"dark_cast", pos)
			for h in hits:
				if h is Actor and (h as Actor).status.has(&"hex_frailty"):
					FX.text_popup((h as Actor).center() + Vector3.UP, "Hexed!", Color(0.8, 0.45, 1.0), 1.0)
		return
	blast.on_blast = func(pos: Vector3, _hits: Array) -> void:
		var c := Elements.color(el) if el != Elements.PHYSICAL else Color(0.85, 0.7, 0.5)
		FX.spawn(VFXLib.ring_wave(c, radius, 0.45, 0.8), pos)
		FX.spawn(VFXLib.dust_puff(1.0), pos)
		Events.camera_shake.emit(0.35 if is_boss else 0.2)
		Events.impact.emit(pos, 12.0, &"earth")
		Audio.play_at(&"boss_slam" if is_boss else &"earth_quake", pos)
		# a Starmote spends itself in the blast (bh-012)
		if a.get("self_destruct", false) and alive:
			die(null)

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
		var el := _atk_element(a)
		var hc: Color = a.get("hazard_color", Elements.color(el) if el != Elements.PHYSICAL else Color(0.55, 0.15, 0.85))
		var blast := AreaEffects.delayed(FX.world, at, float(a.get("radius", 2.5)), delay, null, self, BH.LAYER_PLAYER, Color(hc.r, hc.g, hc.b, 0.7))
		blast.on_blast = func(pos: Vector3, _h: Array) -> void:
			AreaEffects.hazard(FX.world, pos, float(a.get("radius", 2.5)), float(a.get("duration", 6.0)), req, self, BH.LAYER_PLAYER, hc, 0.5)

## bh-033 (Verdigast): rot buds on open ground around her, away from each other and from rot already there. At most
## `max_alive` buds at once; `count` is per phase. Each bud warns where it will rot (ArenaState-style shared warning).
func _plant_buds(a: Dictionary) -> void:
	var bdef := DB.enemy(&"rot_bud")
	if bdef == null:
		return
	var alive := get_tree().get_nodes_in_group(&"rot_bud").filter(func(b): return is_instance_valid(b) and (b as Enemy).alive)
	var counts: Array = a.get("count_by_phase", [int(a.get("count", 2))])
	var want := mini(int(counts[clampi(phase - 1, 0, counts.size() - 1)]), int(a.get("max_alive", 3)) - alive.size() - int(_slot_pending.get(&"rot_bud", 0)))
	var spots := []
	var tries := 0
	while spots.size() < want and tries < 40:
		tries += 1
		var ang := rng.randf() * TAU
		var p := global_position + Vector3(cos(ang), 0, sin(ang)) * rng.randf_range(6.0, 12.0)
		p = CombatQuery.reachable_point(get_world_3d(), global_position, p)
		if p.distance_to(global_position) < 4.5 or spots.any(func(q): return q.distance_to(p) < 6.0):
			continue
		if alive.any(func(b): return (b as Node3D).global_position.distance_to(p) < 6.0):
			continue
		if get_tree().get_nodes_in_group(&"rot_patch").any(func(h): return (h as Node3D).global_position.distance_to(p) < 5.0):
			continue
		spots.append(p)
	for sp in spots:                            # bh-037: each bud in its own spawn slot
		_in_spawn_slot(&"rot_bud", _bud_one.bind(bdef, CombatQuery.ground_at(get_world_3d(), sp), a))
	if not spots.is_empty():
		Audio.play_at(&"dark_cast", global_position)

func _summon(a: Dictionary) -> void:
	var edef := DB.enemy(a.get("summon", &"hollow_soldier"))
	if edef == null:
		return
	for i in int(a.get("count", 2)):
		var ang := TAU * float(i) / float(a.get("count", 2))
		var p := global_position + Vector3(cos(ang), 0, sin(ang)) * 4.0
		p = CombatQuery.reachable_point(get_world_3d(), global_position, p)
		p = CombatQuery.ground_at(get_world_3d(), p)
		_in_spawn_slot(edef.id, _summon_one.bind(edef, p))
	Audio.play_at(&"dark_cast", global_position)

## bh-037: monsters called into a fight come one per spawn slot, SUMMON_STAGGER apart, across every caller (a weaver's
## images, two weavers casting together, a nest and a rift...). A spawn costs ~7 ms on this thread (its body, outfit and
## bar) plus a few ms in its first frames; a group in one frame stacked into 40-70 ms hitches. No spawn waits longer than
## SPAWN_WAIT_MAX.
const SUMMON_STAGGER := 0.06
const SPAWN_WAIT_MAX := 0.5
static var _spawn_slot_ms := 0

## How long the next spawn waits for its slot (0 = now); takes the slot.
static func spawn_wait() -> float:
	var now := Time.get_ticks_msec()
	var wait := mini(maxi(0, _spawn_slot_ms - now), int(SPAWN_WAIT_MAX * 1000.0))
	_spawn_slot_ms = now + wait + int(SUMMON_STAGGER * 1000.0)
	return wait / 1000.0

var _slot_pending := {}               # kind -> spawns of this monster waiting for their slot (count toward its caps)

func _in_spawn_slot(id: StringName, fn: Callable) -> void:
	var w := spawn_wait()
	if w <= 0.0:
		fn.call()
		return
	_slot_pending[id] = int(_slot_pending.get(id, 0)) + 1
	get_tree().create_timer(w, false).timeout.connect(func() -> void:
		_slot_pending[id] = maxi(0, int(_slot_pending.get(id, 0)) - 1)
		fn.call())

func _bud_one(bdef: EnemyDef, p: Vector3, a: Dictionary) -> void:
	if not alive or not is_inside_tree():
		return
	var b := Spawner.spawn_enemy(get_parent(), bdef, maxi(1, level - 2), [], p, difficulty)
	b.add_to_group(&"rot_bud")
	b.set_meta(&"bud_req", _attack_request(a))
	b.set_meta(&"bud_mother", self)
	FX.spawn(VFXLib.particles(Color(0.55, 0.85, 0.2, 0.8), 24, 0.8, true, 0.5, 3.0, 60.0, Vector3(0, 2, 0), 0.6), p)

func _summon_one(edef: EnemyDef, p: Vector3) -> void:
	if not alive or not is_inside_tree():
		return
	var e := Spawner.spawn_enemy(get_parent(), edef, maxi(1, level - 2), [], p, difficulty)
	e.alert_to(target.global_position if target and is_instance_valid(target) else global_position)
	FX.spawn(VFXLib.particles(Color(0.5, 0.2, 0.8, 0.8), 24, 0.8, true, 0.5, 3.0, 60.0, Vector3(0, 2, 0), 0.6), p)

func _end_attack(completed: bool) -> void:
	if visual and visual.current_action() == &"devour":
		visual.stop_action()
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
	_charge_trail()
	if not _charge.hit and target and target.alive and not _charge.get("lunge", false):
		if target.global_position.distance_to(global_position) < body_radius + target.body_radius + 0.8:
			_charge.hit = true
			var req := _attack_request(_charge.a)
			req.tags[&"push_dir"] = _charge.dir
			target.receive_hit(req, self, target.center())
	# bh-033: a charging boss that reaches a standing impact pillar ahead of him crashes into it, even at a corner
	# (the pillars are turned boxes: the slide normal alone missed glancing hits and he slid past)
	if is_boss and not _charge.get("lunge", false) and not net_replica:
		var map := Game.current_map
		var all := ArenaState.pillars(map)
		var gone := ArenaState.broken(map)
		for i in all.size():
			if gone.has(i):
				continue
			var off: Vector3 = ((all[i] as Node3D).global_position - global_position).slide(Vector3.UP)
			if off.length() < body_radius + 1.1 and off.dot(_charge.dir) > 0.0:
				_charge_crash(_pillar_collider(all[i]), (all[i] as Node3D).global_position)
				return Vector3.ZERO
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

## bh-033: a charge's trail (attack key "trail": {phase, every, radius, duration, max}) — burning ground left behind
## along the line, a few patches at most, each warned for every player before it burns. The line stays crossable.
func _charge_trail() -> void:
	var tr: Dictionary = (_charge.get("a", {}) as Dictionary).get("trail", {})
	if tr.is_empty() or phase < int(tr.get("phase", 1)) or net_replica:
		return
	var last: Vector3 = _charge.get("trail_at", global_position)
	var n := int(_charge.get("trail_n", 0))
	if not _charge.has("trail_at"):
		_charge["trail_at"] = global_position
		return
	if n >= int(tr.get("max", 5)) or last.distance_to(global_position) < float(tr.get("every", 3.0)):
		return
	_charge["trail_at"] = global_position
	_charge["trail_n"] = n + 1
	var a: Dictionary = _charge.a
	var req := _attack_request(a)
	req.kind = DamageRequest.Kind.SPELL
	req.base_min *= 0.25
	req.base_max *= 0.25
	req.knockback = 0.0
	var at := CombatQuery.ground_at(get_world_3d(), global_position)
	var hc := Color(0.55, 0.15, 0.85)
	var r := float(tr.get("radius", 1.5))
	var blast := AreaEffects.delayed(FX.world, at, r, 0.6, null, self, BH.LAYER_PLAYER, Color(hc.r, hc.g, hc.b, 0.7))
	Net.share_telegraph(at, r, 0.6, Color(hc.r, hc.g, hc.b, 0.7), "circle", 0.0, self)
	blast.on_blast = func(pos: Vector3, _h: Array) -> void:
		AreaEffects.hazard(FX.world, pos, r, float(tr.get("duration", 5.0)), req, self, BH.LAYER_PLAYER, hc, 0.5)

## bh-033: an arena-control boss takes her ground hazards and growing buds with her (no leftovers after a kill).
func _clear_arena_hazards() -> void:
	for n in get_tree().get_nodes_in_group(&"rot_patch") + get_tree().get_nodes_in_group(&"rot_bud"):
		if is_instance_valid(n) and n != self:
			if n is Enemy:
				(n as Enemy).remove_from_group(&"enemy")
			n.queue_free()

static func _pillar_collider(p: Node) -> Node:
	var bodies := p.find_children("*", "StaticBody3D", true, false)
	return bodies[0] if not bodies.is_empty() else p

func _charge_crash(other: Object, point: Vector3) -> void:
	_charge = {}
	visual.stop_action()
	# the collider is the pillar kit's StaticBody child; the group sits on the kit root (bh-033: this never matched)
	var pillar_node: Node = other as Node
	while pillar_node != null and not pillar_node.is_in_group(&"arena_pillar") and not (pillar_node is MapRoot):
		pillar_node = pillar_node.get_parent()
	var pillar := pillar_node != null and pillar_node.is_in_group(&"arena_pillar")
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
		# bh-033: the pillar does not survive it — cover shrinks as the fight goes on (shared with every player)
		var map := Game.current_map
		var idx := ArenaState.index_of(map, pillar_node)
		if not net_replica and ArenaState.break_pillar(map, idx):
			Net.arena_event(&"pillar", idx)
		var left := ArenaState.intact_count(map)
		Events.notify.emit("The Warden is stunned! The pillar shatters — %s." % ("%d left" % left if left > 0 else "none left; the walls will still stop him"), &"info")
	elif is_boss and ArenaState.has_pillars(Game.current_map) and ArenaState.intact_count(Game.current_map) == 0:
		# bh-033 fallback once every pillar is down: a wall still stops him, briefly
		status.immunities.erase(&"stunned")
		status.apply(&"stunned", 1.6)
		status.apply(&"stagger_window", 3.0)
		status.immunities[&"stunned"] = true
		Events.notify.emit("The Warden reels against the wall!", &"info")
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
							FX.spawn(VFXLib.beam_flash(Color(1.0, 0.6, 0.3), 3.0, 0.6), hurt.global_position)
							FX.spawn(VFXLib.particles(Color(1.0, 0.7, 0.3, 0.9), 20, 0.8, true, 0.4, 2.0, 40.0, Vector3(0, 3, 0), 0.5), hurt.center()))
					return true
			"buff":
				var allies := []
				for e in get_tree().get_nodes_in_group(&"enemy"):
					if e != self and e.alive and e.brain.is_engaged() and e.global_position.distance_to(global_position) < float(ab.range):
						allies.append(e)
				if ab.get("self", false):
					allies.append(self)
				if allies.size() >= 1 and (not ab.get("self", false) or _dist < float(ab.range)):
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
			_:
				if ext and ext.try_ability(ab):
					return true
	return false

## Start a support/utility cast; `effect` runs at the clip's release frame. False when the monster cannot cast now.
func _cast_ability(ab: Dictionary, effect: Callable) -> bool:
	var S := EnemyBrain.State
	if not brain.go(S.CAST):
		return false
	cooldowns[ab.id] = float(ab.cooldown)
	var act := TimedAction.from_anim(ab.get("anim", &"cast_area"), 1.0)
	_ensure_timing(act, false)
	if effect.is_valid():
		act.on_release = effect
	action = act
	if visual:
		visual.play_action(act.anim, 1.0)
	Audio.play_at(&"cultist_chant", global_position, -2.0)
	return true

## A Necromancer's Bone Ward: absorbs `amount` damage for `duration` seconds (on top of any elite ward).
func apply_bone_ward(amount: float, duration: float) -> void:
	if not alive or amount <= 0.0:
		return
	var add := maxf(0.0, amount - _bone_ward)
	_bone_ward += add
	shield_hp += add
	status.apply(&"bone_ward", duration, amount)
	FX.spawn(VFXLib.particles(Color(0.9, 0.88, 0.8, 0.9), 24, 0.8, true, 0.16, 2.2, 180.0, Vector3(0, 0.5, 0), body_radius + 0.3), center())
	FX.spawn(VFXLib.ring_wave(Color(0.85, 0.85, 0.75, 0.8), body_radius + 1.0, 0.5), global_position)
	if bar:
		bar.touch()

func _on_status_removed(id: StringName) -> void:
	super._on_status_removed(id)
	if id == &"bone_ward" and _bone_ward > 0.0:
		shield_hp = maxf(0.0, shield_hp - minf(shield_hp, _bone_ward))
		_bone_ward = 0.0

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
		_nav_to(goal, delta)
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
	# separation: avoid clipping through allies and stacking on the same spot. Only the monsters in the grid cells
	# around this one count (a map-wide loop made every monster pay for every other one, every physics step), and the
	# push is a soft force, so it is refreshed at 20 Hz (staggered per monster) and held in between (bh-014).
	_sep_phase += 1
	if _sep_phase % SEP_EVERY == 0:
		_sep = _separation()
	var sep := _sep
	if target and target.alive:
		var off2 := global_position - target.global_position
		off2.y = 0.0
		var min2 := body_radius + target.body_radius + 0.25
		if off2.length() < min2:
			sep += off2.normalized() * 1.5
	v += sep * speed * 0.9
	var cur := Vector3(velocity.x, 0, velocity.z) - Vector3(knock_velocity.x, 0, knock_velocity.z)
	return cur.move_toward(v.limit_length(speed * 1.1), 30.0 * delta)

## Path requests (bh-014). Assigning NavigationAgent3D.target_position always runs a fresh A* query on the next
## get_next_path_position(), even for the same point (the engine never compares), so steering every physics step
## searched the whole map's navmesh 60 times a second per monster. Now: a new goal far from the last one paths at
## once; one that drifts (a hero walking away) re-paths at most every REPATH_INTERVAL. The agent still follows
## (and re-plans on its own if pushed off) the current path in between.
const REPATH_INTERVAL := 0.3
const REPATH_DRIFT := 0.6            # metres the goal may move before a timed re-path
const REPATH_JUMP := 4.0             # metres: a goal this far from the last one is a new errand, path now
var _nav_goal := Vector3.INF
var _nav_t := 0.0

func _nav_to(goal: Vector3, delta: float) -> void:
	_nav_t -= delta
	var moved := INF if _nav_goal == Vector3.INF else goal.distance_squared_to(_nav_goal)
	if moved > REPATH_JUMP * REPATH_JUMP or (_nav_t <= 0.0 and moved > REPATH_DRIFT * REPATH_DRIFT):
		agent.target_position = goal
		_nav_goal = goal
		_nav_t = REPATH_INTERVAL

## Neighbour grid for separation, rebuilt once per physics step and shared by every monster (bh-014).
const SEP_CELL := 6.0
const SEP_EVERY := 3
var _sep := Vector3.ZERO
var _sep_phase := 0

func _separation() -> Vector3:
	_neighbours_grid()
	var sep := Vector3.ZERO
	var gp := global_position
	var c := Vector2i(floori(gp.x / SEP_CELL), floori(gp.z / SEP_CELL))
	var r := 1 + int((SEPARATION_RADIUS + body_radius * 2.0) / SEP_CELL)   # a giant's reach can span more than one cell
	for dx in range(-r, r + 1):
		for dz in range(-r, r + 1):
			var cell = _grid.get(c + Vector2i(dx, dz))
			if cell == null:
				continue
			for e in cell:
				if e == self or not is_instance_valid(e) or not e.alive:
					continue
				var off: Vector3 = gp - e.global_position
				off.y = 0.0
				var min_d: float = SEPARATION_RADIUS + body_radius + e.body_radius - 0.9
				var l := off.length()
				if l < min_d and l > 0.001:
					sep += off / l * (min_d - l) / min_d
	return sep

static var _grid := {}
static var _grid_frame := -1
static var _grid_gen := 0
static var _grid_tree: SceneTree
static var _awake_n := 0                 # awake monsters at the last grid build (crowd LOD)
var _grid_seen := -1

## Rebuilt at most once per physics step, and whenever a monster asks twice from the same build (tests step monsters
## by hand, many times inside one engine frame).
func _neighbours_grid() -> void:
	var tree := get_tree()
	var f := Engine.get_physics_frames()
	if f == _grid_frame and tree == _grid_tree and _grid_seen != _grid_gen:
		_grid_seen = _grid_gen
		return
	_grid_frame = f
	_grid_tree = tree
	_grid_gen += 1
	_grid_seen = _grid_gen
	_grid.clear()
	_awake_n = 0
	for e: Enemy in tree.get_nodes_in_group(&"enemy"):
		if e.alive and e.is_inside_tree() and not e._asleep:
			_awake_n += 1
			var k := Vector2i(floori(e.global_position.x / SEP_CELL), floori(e.global_position.z / SEP_CELL))
			if _grid.has(k):
				(_grid[k] as Array).append(e)
			else:
				_grid[k] = [e]

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
				if has_trait(&"coffin_shield"):
					# the coffin-lid shield splinters
					FX.spawn(VFXLib.debris(1.0, Color(0.32, 0.22, 0.14)), center() + forward() * 0.5)
					Audio.play_at(&"break_wood", global_position)
			else:
				req.guarding = true
	if stats.has_flag(&"ward") and shield_hp > 0.0 and req.conversion.has(Elements.LIGHT):
		req.tags[&"ward_light"] = true
	# bh-013: an Aegis Acolyte's link, and the new monsters' own defences (ethereal, curled, mirror guard)
	if status.has(&"aegis_link") and req.kind != DamageRequest.Kind.DOT:
		req.more.append(["Aegis Link", TraitsX.LINK_TAKEN])
	if ext:
		ext.prepare_incoming(req, attacker)

func _apply_result(result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	if net_replica:
		_net_hit(result, req, attacker, hit_point)
		return
	_last_res = result
	_last_req = req
	if not result.evaded:
		_stealth_reveal = maxf(_stealth_reveal, 2.0)
	if shield_hp > 0.0 and req.tags.get(&"ward_light", false):
		shield_hp = maxf(0.0, shield_hp - result.components.get(Elements.LIGHT, 0.0))
	super._apply_result(result, req, attacker, hit_point)
	_bone_ward = minf(_bone_ward, shield_hp)
	if ext and alive:
		ext.on_hit(result, req, attacker)
	if result.evaded:
		return
	_last_hit_t = 0.0
	_regen_block = 3.0 if result.components.get(Elements.FIRE, 0.0) > 0.0 else _regen_block
	if alive and attacker is Actor and attacker.team == BH.Team.PLAYER:
		if result.total > 0:
			var id := attacker.get_instance_id()
			_threat[id] = float(_threat.get(id, 0.0)) + float(result.total)
		if not brain.is_engaged():
			alert_to(attacker.global_position)
		if stats.has_flag(&"sparks") and _spark_cd <= 0.0 and rng.randf() < 0.35:
			_spark_cd = 1.0
			_spark(attacker)
	if result.total > 0 and def.sounds.has("hurt"):
		Audio.play_at(def.sounds.hurt, global_position, -2.0)
	if bar:
		bar.touch()

## bh-040: a monster of the Descent is harder to shove around, whatever pushes it (Descent.knock_taken).
func apply_knockback(dir: Vector3, speed: float, source: DerivedStats, source_node: Node, depth := 0, launch := 0.0) -> void:
	var k := Descent.knock_taken(level, int(stats.get_stat(&"threat_rank")) if stats else CombatBudget.Rank.NORMAL)
	super.apply_knockback(dir, speed * k, source, source_node, depth, launch * k)

func _on_damaged(result: DamageResult, req: DamageRequest) -> void:
	if result.total <= 0 or visual == null:
		return
	if knock_velocity.length() >= KNOCKED_THRESHOLD or status.is_disabled():
		return
	# bh-040: hit recovery. In the Descent only a blow that takes a real share of its health makes a monster flinch
	if float(result.total) < max_hp() * Descent.flinch_share(level, int(stats.get_stat(&"threat_rank"))):
		return
	var heavy := result.poise_damage > stats.get_stat(&"poise", 30.0) * 0.4 or result.is_crit
	if action == null or heavy and not is_boss:
		visual.play_reaction(&"hit_heavy" if heavy else &"hit", _hit_side(last_attacker))

## Which side a blow came from, for hit_front / hit_back / hit_left / hit_right reactions.
func _hit_side(from: Node) -> StringName:
	if not (from is Node3D) or not is_instance_valid(from):
		return &"front"
	var to := ((from as Node3D).global_position - global_position).slide(Vector3.UP)
	if to.length() < 0.05:
		return &"front"
	var f := forward().dot(to.normalized())
	var r := global_transform.basis.x.dot(to.normalized())
	if f > 0.5:
		return &"front"
	if f < -0.5:
		return &"back"
	return &"left" if r > 0.0 else &"right"

func _on_staggered(_broken: bool) -> void:
	_interrupt()
	if visual:
		visual.play_reaction(&"stagger_heavy" if is_elite or is_boss else &"stagger")
		visual.shudder(1.0)
	Audio.play_at(&"stagger", global_position)
	if is_boss or is_elite:
		FX.text_popup(center() + Vector3.UP * 1.2, "Staggered!", UITheme.GOLD, 1.2)

func _on_shield_broken() -> void:
	_bone_ward = 0.0
	status.remove(&"bone_ward")
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

## Below the world. Knocked off a ledge by someone in the last few seconds: that someone gets the kill. Fallen on its
## own (a bad spawn, a physics hiccup): it quietly returns to its camp — a fall is never a free kill paying the hero
## experience and loot (bh-011: monsters spawned inside the Ruined Forest's tower mound did exactly that on arrival).
func _fell_out() -> void:
	if _last_hit_t < 6.0 and last_attacker and is_instance_valid(last_attacker):
		die(last_attacker)
		return
	_falls += 1
	if _falls > 3:
		# it keeps falling from its own camp: take it out of the world without a death (no reward, no camp credit)
		alive = false
		remove_from_group(&"enemy")
		if bar:
			bar.queue_free()
			bar = null
		queue_free()
		return
	var spot := home
	var nm := get_world_3d().navigation_map
	if NavigationServer3D.map_get_iteration_id(nm) > 0:
		var q := NavigationServer3D.map_get_closest_point(nm, home)
		if q.is_finite() and q != Vector3.ZERO:
			spot = q
	global_position = spot + Vector3.UP * 0.3
	velocity = Vector3.ZERO
	knock_velocity = Vector3.ZERO
	_vertical = 0.0

func die(killer: Node) -> void:
	if not alive:
		return
	_interrupt()
	if is_boss and def.attacks.any(func(at): return String(at.get("kind", "")) == "bud"):
		_clear_arena_hazards()
	_death_clip = _choose_death_clip(killer)
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
	if not net_replica and stats.has_flag(&"death_fire"):
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = stats
		var rr := EnemyStats.attack_range(def, stats, 0.25)
		req.base_min = rr.x
		req.base_max = rr.y
		req.conversion = {Elements.FIRE: 1.0}
		req.label = "Burning ground"
		AreaEffects.hazard(FX.world, global_position, 2.6, 5.0, req, null, BH.LAYER_PLAYER, Color(1.0, 0.4, 0.1))
	if not net_replica and stats.has_flag(&"explode"):
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
	if _stolen_gold > 0:
		Loot.spawn_gold(global_position, _stolen_gold)
		_stolen_gold = 0
	if not net_replica and has_trait(&"core_overload"):
		_core_overload()
	if not net_replica and ext:
		ext.on_death(killer)
	_begin_corpse()

# ---- Network replica (bh-008) ---------------------------------------------------------------------------------

func net_snap(p: Vector3, yaw: float) -> void:
	_net_pos = p
	_net_yaw = yaw

## One host snapshot: [id, pos, yaw, vel, hp, max_hp, action, serial, rate, loop, engaged, shield]
func net_apply(s: Array) -> void:
	_net_pos = s[1]
	_net_yaw = s[2]
	_net_vel = s[3]
	_net_age = 0.0
	hp = s[4]
	shield_hp = s[11]
	_net_engaged = s[10]
	health_changed.emit(hp, max_hp())
	if visual:
		var serial := int(s[7])
		var act := StringName(s[6])
		if serial != _net_serial:
			_net_serial = serial
			if act != &"":
				if bool(s[9]):
					visual.hold_action(act, float(s[8]))
				else:
					visual.play_action(act, float(s[8]))
		elif act == &"" and visual.current_action() != &"":
			visual.stop_action()

func _net_step(delta: float) -> void:
	if not alive:
		physics_move(delta, Vector3.ZERO)
		return
	# calm monsters arrive at a few snapshots a second (bh-035): keep walking along the last known velocity in between
	if _net_age < 0.5:
		_net_pos += Vector3(_net_vel.x, 0.0, _net_vel.z) * delta
	_net_age += delta
	var k := 1.0 - exp(-12.0 * delta)
	if global_position.distance_to(_net_pos) > 6.0:
		global_position = _net_pos
	else:
		global_position = global_position.lerp(_net_pos + _net_vel * 0.05, k)
	rotation.y = lerp_angle(rotation.y, _net_yaw, k)
	if visual:
		var local := global_transform.basis.inverse() * Vector3(_net_vel.x, 0, _net_vel.z)
		visual.update_locomotion(Vector2(local.x, local.z), _net_engaged, 0.0, delta)

## A blow from this machine's hero or Tempo: feedback now, numbers to the host (it owns the HP).
func _net_hit(result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	Net.replica_hit(self, result, req, attacker, hit_point)
	var pos := hit_point if hit_point != Vector3.INF else center()
	Events.damage_dealt.emit(self, result, pos, attacker)
	if result.evaded:
		return
	hp = maxf(1.0, hp - float(result.total))          # a guess until the host answers; never dies on its own
	health_changed.emit(hp, max_hp())
	if attacker is Actor and result.leech > 0.0 and attacker.alive:
		attacker.heal(attacker.leech_allowance(result.leech), false)
	_on_damaged(result, req)
	if bar:
		bar.touch()

func net_die(killer: Node, _clip: StringName) -> void:
	hp = 0.0
	die(killer)

# ---- Deaths and corpses ---------------------------------------------------------------------------------------

var _death_clip: StringName = &"death"

## The killing blow decides the fall: blown back by heavy knockback, pitched forward by crits and backstabs.
## Skeletons and constructs fold down where they stand.
func _choose_death_clip(killer: Node) -> StringName:
	if def.death_style in [&"crumple", &"collapse"]:
		return &"death_crumple"
	var kb := _last_res.knockback if _last_res else 0.0
	var launched: bool = _last_req != null and float(_last_req.tags.get(&"launch", 0.0)) > 0.0
	if kb >= HEAVY_KNOCK or launched:
		return &"death_back"
	if (_last_res and _last_res.is_crit) or _hit_side(killer) == &"back":
		return &"death_fwd"
	var r := rng.randf()
	return &"death" if r < 0.5 else (&"death_back" if r < 0.75 else &"death_fwd")

func death_clip() -> StringName:
	return _death_clip

func _begin_corpse() -> void:
	match def.death_style:
		&"implode":
			_implode()
			return
		&"smoke":
			_smoke_out()
			return
		&"ash":
			_ash_burn()
			return
		&"collapse":
			FX.spawn(VFXLib.debris(1.4, Color(0.5, 0.48, 0.44)), center())
			FX.spawn(VFXLib.particles(Color(1.0, 0.8, 0.45, 1.0), 26, 0.4, true, 0.14, 8.0, 80.0, Vector3(0, -12, 0)), center())
			if visual:
				visual.set_decay(0.6, Color(0.3, 0.3, 0.3))   # the core light goes out
		&"crumple":
			FX.spawn(VFXLib.particles(Color(0.7, 0.68, 0.6, 0.5), 12, 1.0, true, 0.9, 1.2, 80.0, Vector3(0, 0.3, 0), 0.4, false), global_position + Vector3.UP * 0.3)
	add_to_group(&"corpse")
	_corpses.append(self)
	while _corpses.size() > MAX_CORPSES:
		var old = _corpses.pop_front()
		if is_instance_valid(old) and old != self:
			old._dissolve(1.2)
	if Gore.bleeds(def.hit_material):
		# the pool starts once the body has hit the ground
		get_tree().create_timer(0.7, false).timeout.connect(func() -> void:
			if is_instance_valid(self) and not _decaying and not alive:
				_pool = FX.pool(global_position, def.blood, clampf(body_radius * 3.2, 1.2, 4.5), 7.0))
	if has_trait(&"reassemble") and not _reassembled and not risen and _can_reassemble():
		_reassembling = true
		get_tree().create_timer(3.5, false).timeout.connect(_reassemble)
		return
	get_tree().create_timer(def.corpse_time, false).timeout.connect(_decay)

## Stage 2: the body darkens and greys over several seconds (flesh draws flies), then dissolves.
func _decay() -> void:
	if not is_instance_valid(self) or alive or _decaying:
		return
	_decaying = true
	if Gore.bleeds(def.hit_material):
		var flies := VFXLib.particles(Color(0.05, 0.05, 0.04, 0.9), 8, 1.6, false, 0.05, 0.8, 180.0, Vector3.ZERO, 0.5, false)
		flies.position = Vector3.UP * 0.4
		add_child(flies)
	if visual:
		var tw := create_tween()
		tw.tween_method(visual.set_decay, 0.0, 1.0, 8.0)
	get_tree().create_timer(8.0, false).timeout.connect(_dissolve.bind(3.0))

## Stage 3: dithered fade and a slow sink into the ground; the pool dries and fades; then the node is freed.
func _dissolve(dur: float) -> void:
	if not is_instance_valid(self) or alive or has_meta(&"dissolving"):
		return
	set_meta(&"dissolving", true)
	_decaying = true
	_reassembling = false
	remove_from_group(&"corpse")
	_corpses.erase(self)
	var tw := create_tween()
	if visual:
		tw.tween_method(visual.set_opacity, 1.0, 0.0, dur)
	tw.parallel().tween_property(self, "position:y", position.y - 0.5, dur)
	if _pool and is_instance_valid(_pool):
		var pl := _pool
		tw.parallel().tween_property(pl, "modulate:a", 0.0, dur)
		tw.tween_callback(pl.queue_free)
	tw.tween_callback(queue_free)

func is_fresh_corpse() -> bool:
	return not alive and not _decaying and not _reassembling and not risen and is_in_group(&"corpse")

## Consumed by a ghoul: the body is torn apart.
func consume() -> void:
	if not is_fresh_corpse():
		return
	if Settings.blood:
		FX.spawn(Gore.hit(center(), Vector3.UP, def.hit_material, def.blood, 1.1, true), center())
	FX.spawn(VFXLib.debris(0.8, def.blood.lightened(0.1)), center())
	_dissolve(0.6)

func _implode() -> void:
	FX.spawn(VFXLib.light_flash(Color(0.55, 0.97, 1.0), 6.0, 7.0, 0.35), center())
	FX.spawn(VFXLib.ring_wave(Color(0.55, 0.97, 1.0, 0.9), 2.4, 0.4, 0.5), global_position)
	FX.spawn(VFXLib.particles(Color(0.6, 1.0, 1.0, 1.0), 36, 0.7, true, 0.18, 6.0, 180.0, Vector3(0, 0.5, 0), 0.3), center())
	get_tree().create_timer(0.9, false).timeout.connect(queue_free)

func _smoke_out() -> void:
	FX.spawn(VFXLib.particles(Color(0.03, 0.02, 0.05, 0.8), 30, 1.4, true, 1.1, 1.4, 120.0, Vector3(0, 0.7, 0), 0.5, false), center())
	FX.spawn(VFXLib.particles(Color(0.7, 0.35, 1.0, 1.0), 16, 0.6, true, 0.14, 3.0, 180.0), center())
	if visual:
		create_tween().tween_method(visual.set_opacity, 1.0, 0.0, 1.4)
	get_tree().create_timer(1.6, false).timeout.connect(queue_free)

## Ashen Circle: the body burns from within, crumbles to ash, and leaves a grey smear.
func _ash_burn() -> void:
	var embers := VFXLib.particles(Color(1.0, 0.45, 0.1, 1.0), 40, 1.2, false, 0.14, 1.6, 40.0, Vector3(0, 2.0, 0), 0.5)
	embers.position = Vector3.UP * 0.4
	add_child(embers)
	FX.spawn(VFXLib.light_flash(Color(1.0, 0.5, 0.15), 3.0, 4.0, 1.2), center())
	var tw := create_tween()
	if visual:
		tw.tween_interval(0.8)
		tw.tween_method(func(v: float) -> void: visual.set_decay(v, Color(0.05, 0.04, 0.035)), 0.0, 1.0, 1.6)
		tw.tween_callback(func() -> void:
			embers.emitting = false
			FX.spawn(VFXLib.particles(Color(0.35, 0.33, 0.3, 0.7), 24, 1.6, true, 0.6, 1.4, 90.0, Vector3(0, 0.6, 0), 0.5, false), center())
			FX.stain(global_position, Color(0.12, 0.11, 0.1, 0.8), 1.8))
		tw.tween_method(visual.set_opacity, 1.0, 0.0, 1.5)
	tw.tween_callback(queue_free)

## Temple constructs: the Aether core overloads a moment after the body falls.
func _core_overload() -> void:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = stats
	var rr := EnemyStats.attack_range(def, stats, 0.8)
	req.base_min = rr.x
	req.base_max = rr.y
	req.conversion = {Elements.LIGHT: 1.0}
	req.knockback = 8.0
	req.label = "Core overload"
	var b := AreaEffects.delayed(FX.world, global_position, 3.0, 1.4, req, null, BH.LAYER_PLAYER, Color(0.55, 0.95, 1.0, 0.7))
	b.on_blast = func(pos: Vector3, _h: Array) -> void:
		FX.spawn(VFXLib.ring_wave(Color(0.55, 0.97, 1.0), 3.0, 0.4), pos)
		FX.spawn(VFXLib.light_flash(Color(0.55, 0.97, 1.0), 6.0, 8.0, 0.3), pos + Vector3.UP)
		Audio.play_at(&"arcane_surge", pos)
		Events.camera_shake.emit(0.25)

## Hollow soldiers pull themselves back together once, unless fire, light or a crushing blow ended them.
func _can_reassemble() -> bool:
	if _last_res == null:
		return rng.randf() < 0.4
	for el in [Elements.FIRE, Elements.LIGHT]:
		if float(_last_res.components.get(el, 0.0)) > 0.0:
			return false
	if _last_res.shattered or _last_res.knockback >= HEAVY_KNOCK or _last_res.total >= max_hp() * 0.8:
		return false
	return rng.randf() < 0.4

func _reassemble() -> void:
	if not is_instance_valid(self) or alive or not _reassembling:
		return
	_reassembling = false
	_reassembled = true
	remove_from_group(&"corpse")
	_corpses.erase(self)
	alive = true
	hp = max_hp() * 0.4
	brain = EnemyBrain.new()
	collision_layer = BH.LAYER_ENEMY
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_PLAYER | BH.LAYER_ENEMY
	add_to_group(&"enemy")
	if _pool and is_instance_valid(_pool):
		_pool.queue_free()
	if visual:
		visual.revive()
	FX.spawn(VFXLib.particles(Color(0.45, 1.0, 0.85, 0.9), 30, 1.0, true, 0.2, 2.5, 180.0, Vector3(0, 1.5, 0), 0.5), center())
	FX.text_popup(center() + Vector3.UP, "Reassembles!", Color(0.55, 1.0, 0.85), 1.1)
	Audio.play_at(&"skeleton_rattle", global_position, 2.0)
	bar = EnemyBar.new()
	bar.setup(self)
	add_child(bar)
	health_changed.emit(hp, max_hp())
	get_tree().create_timer(1.4, false).timeout.connect(func() -> void:
		if is_instance_valid(self) and alive:
			alert_to(target.global_position if target and is_instance_valid(target) else global_position))

# ---- Signature traits (per frame) --------------------------------------------------------------------------------

func _trait_tick(delta: float) -> void:
	if ext:
		ext.tick(delta)
		if not alive:
			return
	_devour_cd = maxf(0.0, _devour_cd - delta)
	_stealth_reveal = maxf(0.0, _stealth_reveal - delta)
	if has_trait(&"stealth") and visual:
		# almost invisible while stalking; revealed while striking, when hit, or when disabled
		var want := 0.14 if action == null and _stealth_reveal <= 0.0 and not status.is_disabled() else 1.0
		_stealth = move_toward(_stealth, want, delta * (4.0 if want > _stealth else 1.2))
		visual.set_opacity(_stealth)
		if bar:
			bar.visible = _stealth > 0.6 or Game.hover_target == self
	if has_trait(&"enrage") and not _enrage_done and hp < max_hp() * 0.4:
		_enrage_done = true
		enraged = true
		mark_stats_dirty()
		status.apply(&"enraged", 0.0)
		_interrupt()
		visual.play_action(&"boss_roar", 1.0)
		FX.text_popup(center() + Vector3.UP * 1.5, "Enraged!", Color(1.0, 0.35, 0.2), 1.2)
		Audio.play_at(&"boss_roar", global_position)
		Events.camera_shake.emit(0.25)

## Ghoul brutes feed on the fallen mid-fight to heal. Returns true when it took over this think.
func _try_devour() -> bool:
	var S := EnemyBrain.State
	if not has_trait(&"devour") or _devour_cd > 0.0 or hp > max_hp() * 0.65 or action != null:
		return false
	if _devour_target == null or not is_instance_valid(_devour_target) or not _devour_target.is_fresh_corpse():
		_devour_target = null
		var best := 64.0
		for c in get_tree().get_nodes_in_group(&"corpse"):
			if c is Enemy and c != self and c.is_fresh_corpse():
				var d: float = c.global_position.distance_squared_to(global_position)
				if d < best:
					best = d
					_devour_target = c
		if _devour_target == null:
			_devour_cd = 2.0
			return false
	if global_position.distance_to(_devour_target.global_position) > 1.8:
		brain.go(S.CHASE)
		_move_target = _devour_target.global_position
		return true
	if not brain.go(S.CAST):
		return false
	var corpse := _devour_target
	var act := TimedAction.from_anim(&"devour", 1.0)
	act.duration = 3.0
	act.release_t = 2.6
	act.on_release = func() -> void:
		if alive and is_instance_valid(corpse) and corpse.is_fresh_corpse():
			corpse.consume()
			heal(max_hp() * 0.3)
			FX.text_popup(center() + Vector3.UP, "Devours!", Color(0.6, 1.0, 0.4), 1.1)
	action = act
	visual.hold_action(&"devour")
	_face_now(corpse.global_position)
	Audio.play_at(&"ghoul_growl", global_position)
	_devour_cd = 12.0
	return true

# ---- Elites, bosses, ambience -------------------------------------------------------------------------------------

func _apply_elite_visuals() -> void:
	var c: Color = DB.elite_mods[elite_mods[0]].color
	visual.set_rim(c, 0.9)
	var aura := VFXLib.particles(Color(c.r, c.g, c.b, 0.7), 22, 1.1, false, 0.4, 0.9, 20.0, Vector3(0, 1.4, 0), body_radius + 0.2)
	aura.position.y = 0.1
	add_child(aura)
	var ring := VFXLib.telegraph("ring", Vector2(body_radius + 0.45, body_radius + 0.45), 0.01, Color(c.r, c.g, c.b, 0.6), 360.0, body_radius + 0.2)
	add_child(ring)
	if is_miniboss():
		_apply_champion_visuals()
	Events.elite_spawned.emit(self)

## Champions (minibosses) read apart from elites at a glance: a gold rim, a wide gold ring and a crown of embers at
## their feet, and a warm light of their own.
func _apply_champion_visuals() -> void:
	var gold := Color(1.0, 0.72, 0.28)
	visual.set_rim(gold, 1.3)
	var ring := VFXLib.telegraph("ring", Vector2(body_radius + 1.25, body_radius + 1.25), 0.02, Color(gold.r, gold.g, gold.b, 0.75), 360.0, body_radius + 0.9)
	add_child(ring)
	var embers := VFXLib.particles(Color(1.0, 0.6, 0.2, 0.85), 26, 1.4, false, 0.18, 1.6, 25.0, Vector3(0, 2.0, 0), body_radius + 0.8)
	embers.position.y = 0.1
	add_child(embers)
	var l := OmniLight3D.new()
	l.light_color = gold
	l.light_energy = 1.4
	l.omni_range = 5.0
	l.position.y = body_height * 0.6
	add_child(l)

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
			_fire({"id": &"aether_bolt", "kind": "projectile", "mult": 0.6, "element": Elements.LIGHT, "count": 3, "spread": 30.0, "speed": 15.0, "range": 16.0, "projectile": "orb", "knockback": 1.0, "poise": 4.0})

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
	if is_miniboss():
		return String(miniboss.get("title", "Champion"))
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
