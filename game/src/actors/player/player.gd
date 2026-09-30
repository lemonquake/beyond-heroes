class_name Player
extends Actor
## The hero in the world. Reads HeroData (the persistent model), owns runtime state (HP/mana pools, statuses, class
## resource, cooldowns, the current animation-driven action) and turns input into intents:
##
##   Move (WASD, camera-relative) · Aim (mouse) · Light attack chain (LMB, four steps, buffered, finisher recovery)
##   Heavy attack (RMB; hold to charge on charge weapons; branches from any chain step) · Dodge (Space, i-frames)
##   Guard (F hold; frontal block, parry window) · Skills 1–6 · Potions Q/E · Interact R
##
## All damage goes through DamagePipeline via Actor.receive_hit; weapon damage is applied only inside the hit windows
## of the playing animation (TimedAction), scaled by attack speed.

signal skill_used(skill_id: StringName)
signal cooldowns_changed
signal resource_changed(value: float, max_value: float)
signal interact_changed(target: Node)
signal combo_changed(step: int)
signal player_died
signal stats_changed

const INPUT_BUFFER := 0.35
const COMBAT_LINGER := 4.0
const FINISHER_LOCK := 0.3
const GUARD_MOVE_MULT := 0.45
const CHARGE_MOVE_MULT := 0.35
const POTION_COOLDOWN := 1.5
## Potion belt keys (Q / E): strongest draught first, the elixir last.
const POTION_ORDER := {
	&"heal": [&"superior_health_potion", &"greater_health_potion", &"health_potion", &"minor_health_potion", &"rejuvenation_elixir"],
	&"mana": [&"superior_mana_potion", &"greater_mana_potion", &"mana_potion", &"minor_mana_potion", &"rejuvenation_elixir"],
}
const LOW_HP := 0.3
const INTERACT_RANGE := 2.6
const INTERACT_HEIGHT := 1.6
const RIPOSTE_WINDOW := 2.0
const ACCEL := 45.0
const TURN_RATE := 14.0

var hero: HeroData
var resource: ClassResource
var runner: SkillRunner
var camera: PlayerCamera
var aim_point := Vector3.ZERO
var input_enabled := true
var aim_override := Vector3.INF        # automated playtests aim here instead of at the mouse
## Touch play (bh-008): while a skill button is dragged the on-screen controls aim here (world direction, metres).
var touch_aim_dir := Vector3.ZERO
var touch_aim_dist := 0.0
var auto_target: Actor                  # touch play: the enemy auto-aim has picked (kept while it stays in reach)

var action: TimedAction
var action_kind := &""                 # light, heavy, charge_release, skill, dodge, interact, potion
var chain_step := 0
var _chain_expire := 0.0
var _chain_lock := 0.0
var _queued := &""
var _queued_arg := &""
var _queued_t := 0.0
var charging := false
var _charge_t := 0.0
var guarding := false
var _guard_latched := false
var _guard_t := 0.0
var channel_skill := &""
var _channel_tick := 0.0
var _channel_params := {}
var _dash_vel := Vector3.ZERO
var _dash_t := 0.0
var _leap := {}
var cooldowns := {}                    # skill id -> remaining seconds
var cooldown_total := {}
var potion_cd := 0.0
var dodge_cd := 0.0
var shield_t := 0.0
var _combat_t := 99.0
var _attack_counter := 0
var class_passives := ClassPassives.new(self)
var _retaliation_cd := 0.0
var _still_t := 0.0
var _riposte_t := 0.0
var _last_element := -1
var _overload_hits := {}               # element -> time
var _heartbeat_t := 0.0
var _pulse_cd := 0.0
var _shockwave_cd := 0.0
var _haste_t := 0.0
var _footstep_acc := 0.0
var _interact_target: Node
var _interact_scan := 0.0
var _time := 0.0
var _last_move_dir := Vector3.FORWARD
var _hurt_sound_t := 0.0
var dead_since := -1.0
# bh-010: auras, Combo / Focus bookkeeping, passives
const AURA_PULSE := 1.0
const AURA_STATUS_TIME := 1.6
var _aura_t := 0.0
var _aura_ring: MeshInstance3D
var _second_wind_cd := 0.0
var _cast_serial := 0
var _combo_cast := -1

func _ready() -> void:
	super._ready()
	team = BH.Team.PLAYER
	add_to_group(&"player")
	collision_layer = BH.LAYER_PLAYER
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_ENEMY
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.4
	cap.height = 1.8
	cs.shape = cap
	cs.position.y = 0.9
	add_child(cs)
	body_radius = 0.4
	body_height = 1.8
	camera = PlayerCamera.new()
	camera.target = self
	add_child(camera)
	camera.make_current()
	runner = SkillRunner.new(self)
	Events.actor_died.connect(_on_actor_died)

## Bind a hero (new game / load) and build the visual.
func bind(h: HeroData) -> void:
	hero = h
	display_name = h.hero_name
	level = h.progress.level
	resource = ClassResource.new(h.cls.resource_kind)
	resource.changed.connect(func(v, m): resource_changed.emit(v, m))
	h.stats_dirty.connect(_on_hero_changed)
	h.inventory_changed.connect(_on_inventory_changed)
	h.progress.leveled_up.connect(_on_level_up)
	visual = CharacterVisual.new()
	visual.name = "Visual"
	add_child(visual)
	# bh-023: every class wears its gear on the hero's own body (the class models remain for spirits and townsfolk)
	visual.setup(HeroLook.MODEL if ResourceLoader.exists(HeroLook.MODEL) else h.cls.model_path, 1.0, h.cls.tint, h.cls.id)
	visual.set_look(h.look)
	refresh_equipment_visuals()
	mark_stats_dirty()
	ensure_stats()
	hp = max_hp()
	mana = max_mana()
	if stats.has_flag(&"valor_hold"):
		resource.gain(stats.flag(&"valor_hold"))
	if hero.active_aura != &"":
		_aura_visual(true)
	health_changed.emit(hp, max_hp())
	mana_changed.emit(mana, max_mana())
	Events.player_spawned.emit(self)

func _on_hero_changed() -> void:
	mark_stats_dirty()
	refresh_equipment_visuals()

## The bag's weight changes Load and so Movement Speed (no visual refresh needed).
func _on_inventory_changed() -> void:
	mark_stats_dirty()

func _on_level_up(new_level: int, gained: int) -> void:
	level = new_level
	mark_stats_dirty()
	ensure_stats()
	hp = max_hp()
	mana = max_mana()
	health_changed.emit(hp, max_hp())
	mana_changed.emit(mana, max_mana())
	Events.player_leveled.emit(new_level, gained)
	Audio.play_ui(&"level_up")
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.4, 0.9), 4.0, 0.9, 0.8), global_position)
	FX.spawn(VFXLib.beam_flash(Color(1.0, 0.85, 0.45), 6.0, 0.9, 1.4), global_position)
	FX.text_popup(center() + Vector3.UP * 0.8, "Level %d" % new_level, UITheme.GOLD, 1.5)

func refresh_equipment_visuals() -> void:
	if visual == null or hero == null:
		return
	visual.dress_equipment(hero.equipment)
	var lo := hero.equipment.loadout()
	var main := hero.equipment.get_item(&"main_weapon")
	# bh-023: a great axe's heavy attack is the player's own two-handed smash (same timing as the clip it replaces)
	visual.clip_alias = {&"gs_heavy": &"hero_axe_smash"} if lo.main_type != null and lo.main_type.id == &"greataxe" else {}
	var sub := hero.equipment.get_item(&"sub_weapon")
	visual.detach_weapon(&"main")
	visual.detach_weapon(&"off")
	if main != null and lo.main_type != null:
		visual.attach_weapon(&"main", _weapon_model(main, lo.main_type), lo.main_type.grip_offset)
	if sub != null:
		if sub.base.category == &"shield":
			visual.attach_weapon(&"off", sub.base.model_path())
		elif lo.off_type != null:
			visual.attach_weapon(&"off", _weapon_model(sub, lo.off_type), lo.off_type.grip_offset)
	# bh-022: crystals set in the held weapons glow along them
	for pair in [[&"main", main], [&"off", sub]]:
		var w: ItemInstance = pair[1]
		if w != null and w.sockets > 0 and visual.has_weapon(pair[0]):
			visual.set_weapon_infusion(pair[0], CrystalNames.color_for(w.gems), CrystalNames.power(w.gems),
				0.45 if w.base.category == &"shield" else 0.9)
	visual.set_stance(stance_idle())

## The model held in the hand: the item's own model (every base has one since bh-006); a random Aether-tier roll of a
## plain base shows the type's crystalline Aether variant instead.
static func weapon_model_for(item: ItemInstance, wt: WeaponTypeDef) -> String:
	if item.rarity == BH.Rarity.AETHER and item.base.unique_name == "" and not String(item.base.id).begins_with("artisan_"):
		var ae := "res://assets/weapons/%s_aether.glb" % wt.id
		if ResourceLoader.exists(ae):
			return ae
	var own := item.base.model_path()
	return own if own != "" else wt.model

func _weapon_model(item: ItemInstance, wt: WeaponTypeDef) -> String:
	return weapon_model_for(item, wt)

func stance_idle() -> StringName:
	var lo := stats.loadout if stats else hero.equipment.loadout()
	if lo.is_unarmed():
		return &"idle_1h"
	if lo.dual_wield:
		return &"idle_dual"
	if lo.has_shield:
		return &"idle_shield"
	return lo.main_type.idle_anim

# ---- Stats ---------------------------------------------------------------------------------------------------

func rebuild_stats() -> void:
	var mods := status.stat_modifiers()
	if resource:
		mods.append_array(resource.modifiers(40.0 if _has_hero_flag(&"resolute_40") else 50.0, _steady_at()))
	var reserve := aura_reserve()
	if reserve > 0.0:
		mods.append(StatModifier.more(&"max_mana", -reserve, "Reserved by %s" % DB.skill(hero.active_aura).display_name))
	if _haste_t > 0.0:
		mods.append(StatModifier.more(&"move_speed", stats.flag(&"dodge_haste") if stats else 0.2, "Windswift"))
	if stats and stats.has_flag(&"low_hp_dr") and hp < max_hp() * 0.35:
		mods.append(StatModifier.more(&"damage_taken", -stats.flag(&"low_hp_dr"), "Bastion"))
	stats = hero.compute_stats(mods)
	affinity = Elements.PHYSICAL
	level = hero.progress.level
	if resource:
		match resource.kind:
			&"arcane": resource.set_max(stats.get_stat(&"arcane_max", 5.0))
			&"combo":
				resource.set_max(stats.get_stat(&"combo_max", ClassResource.COMBO_MAX))
				resource.decay_delay_bonus = stats.flag(&"combo_linger")
			_: resource.set_max(100.0)
	if mana > max_mana():
		mana = max_mana()
		mana_changed.emit(mana, max_mana())
	stats_changed.emit()

func _steady_at() -> float:
	return 50.0 if stats != null and stats.has_flag(&"steady_50") else ClassResource.STEADY_AT

## Stealth (Smoke Veil): enemies cannot see the hero (Enemy._hidden).
func is_hidden() -> bool:
	return status.has(&"stealth")

func _has_hero_flag(f: StringName) -> bool:
	return stats != null and stats.has_flag(f)

func in_combat() -> bool:
	return _combat_t < COMBAT_LINGER

func is_low_hp() -> bool:
	return alive and hp < max_hp() * LOW_HP

# ---- Aim ----------------------------------------------------------------------------------------------------

func _update_aim() -> void:
	if camera == null or not is_inside_tree():
		return
	if aim_override.is_finite():
		aim_point = aim_override
		return
	if Settings.touch_mode:
		_update_touch_aim()
		return
	var vp := get_viewport()
	var mp := vp.get_mouse_position()
	var from := camera.project_ray_origin(mp)
	var dir := camera.project_ray_normal(mp)
	var plane := Plane(Vector3.UP, global_position.y + 0.9)
	var hit = plane.intersects_ray(from, dir)
	if hit != null:
		aim_point = Vector3(hit.x, global_position.y, hit.z)
	var terrain_query := PhysicsRayQueryParameters3D.create(from, from + dir * 200.0, BH.LAYER_WORLD | BH.LAYER_GROUND)
	var terrain := get_world_3d().direct_space_state.intersect_ray(terrain_query)
	if not terrain.is_empty() and terrain.normal.y > 0.5:
		aim_point = terrain.position
	var enemy := _enemy_under_cursor(from, dir)
	if enemy:
		aim_point = enemy.global_position
		Game.hover_target = enemy
	else:
		Game.hover_target = null
	Game.hover_ally = _ally_under_cursor(from, dir) if enemy == null and Net.is_active() else null

const AUTO_AIM_RANGE := 13.0

## Touch play has no cursor: a dragged skill button aims where it points; otherwise attacks and skills turn toward the
## nearest enemy (favouring the one ahead of the hero and the one already targeted), or straight ahead.
func _update_touch_aim() -> void:
	if touch_aim_dir.length() > 0.1:
		aim_point = global_position + touch_aim_dir.normalized() * maxf(1.0, touch_aim_dist)
		aim_point = CombatQuery.ground_at(get_world_3d(), aim_point)
		return
	var t := pick_auto_target() if Settings.touch_auto_aim else null
	auto_target = t
	Game.hover_target = t
	if t:
		aim_point = t.global_position
	else:
		var ahead := _move_input()
		if ahead.length() < 0.1:
			ahead = forward()
		aim_point = global_position + ahead.normalized() * 4.0

## What auto-aim and click targeting may pick: monsters, and the towns' practice dummies (bh-019).
func _aim_targets() -> Array:
	return get_tree().get_nodes_in_group(&"enemy") + get_tree().get_nodes_in_group(&"practice_target")

func pick_auto_target() -> Actor:
	var facing := _move_input()
	if facing.length() < 0.1:
		facing = forward()
	facing = facing.normalized()
	var best: Actor = null
	var best_score := INF
	for e in _aim_targets():
		var a := e as Actor
		if a == null or not a.alive or not a.visible:
			continue
		var d := a.global_position - global_position
		d.y = 0.0
		var dist := d.length()
		var reach := AUTO_AIM_RANGE * (1.2 if a == auto_target else 1.0)
		if dist > reach or absf(a.global_position.y - global_position.y) > 4.0:
			continue
		var ahead := facing.dot(d / maxf(dist, 0.01))
		var score := dist * (1.35 - 0.35 * ahead) * (0.7 if a == auto_target else 1.0)
		if score < best_score:
			best_score = score
			best = a
	return best

func _enemy_under_cursor(from: Vector3, dir: Vector3) -> Actor:
	var best: Actor = null
	var best_d := INF
	for e in _aim_targets():
		var a := e as Actor
		if a == null or not a.alive:
			continue
		var c := a.center()
		var t := (c - from).dot(dir)
		if t < 0.0:
			continue
		var d := (from + dir * t).distance_to(c)
		if d < a.body_radius + 0.35 and t < best_d:
			best_d = t
			best = a
	return best

## Another player's hero under the cursor (bh-016): clicking them offers a Trade Request.
func _ally_under_cursor(from: Vector3, dir: Vector3) -> Node:
	var best: Node = null
	var best_d := INF
	for n in get_tree().get_nodes_in_group(&"net_hero"):
		var a := n as NetAvatar
		if a == null or not is_instance_valid(a) or not a.is_visible_in_tree():
			continue
		var c := a.center()
		var t := (c - from).dot(dir)
		if t < 0.0:
			continue
		var d := (from + dir * t).distance_to(c)
		if d < a.body_radius + 0.45 and t < best_d:
			best_d = t
			best = a
	return best

func aim_dir() -> Vector3:
	var d := aim_point - global_position
	d.y = 0.0
	return d.normalized() if d.length() > 0.2 else forward()

func cast_point() -> Vector3:
	if visual and hero and hero.equipment.loadout().main_type != null and hero.equipment.loadout().main_type.ranged:
		var p := visual.weapon_point(&"main", 1.0, hero.equipment.loadout().main_type.length)
		if p.is_finite() and p.distance_to(global_position) < 3.0:
			return p
	return global_position + Vector3.UP * 1.3 + forward() * 0.6

## Projectile aim retains elevation; facing and melee continue to use horizontal aim_dir().
func projectile_dir() -> Vector3:
	var target := aim_point + Vector3.UP * 1.0
	if is_instance_valid(Game.hover_target) and Game.hover_target is Actor and aim_point.distance_squared_to(Game.hover_target.global_position) < 0.01:
		target = Game.hover_target.center()
	return (target - cast_point()).normalized()

# ---- Frame loop ---------------------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	if hero == null or not is_finite(delta) or delta <= 0.0:
		return
	_time += delta
	ensure_stats()
	status.tick(delta)
	if not alive:
		physics_move(delta, Vector3.ZERO)
		return
	_tick_timers(delta)
	_regen(delta)
	_update_aim()
	if input_enabled and not Game.ui_blocking and not status.is_disabled():
		_read_input(delta)
	elif status.is_disabled():
		_cancel_action(false)
	var step_ok := true
	if action:
		step_ok = action.step(delta)
		if not step_ok:
			_on_action_done()
	_update_channel(delta)
	var desired := _movement(delta)
	if not _leap.is_empty():
		_leap_step(delta)
	else:
		physics_move(delta, desired)
	_update_facing(delta, desired)
	_update_visual(delta)
	_update_interaction(delta)

func _tick_timers(delta: float) -> void:
	_retaliation_cd = maxf(0.0, _retaliation_cd - delta)
	class_passives.tick(delta)
	var changed := false
	for k in cooldowns.keys():
		cooldowns[k] = maxf(0.0, cooldowns[k] - delta)
		if cooldowns[k] <= 0.0:
			cooldowns.erase(k)
			changed = true
			Events.skill_ready.emit(k)
	if changed:
		cooldowns_changed.emit()
	potion_cd = maxf(0.0, potion_cd - delta)
	dodge_cd = maxf(0.0, dodge_cd - delta)
	_chain_lock = maxf(0.0, _chain_lock - delta)
	_riposte_t = maxf(0.0, _riposte_t - delta)
	_pulse_cd = maxf(0.0, _pulse_cd - delta)
	_shockwave_cd = maxf(0.0, _shockwave_cd - delta)
	_combat_t += delta
	if _haste_t > 0.0:
		_haste_t -= delta
		if _haste_t <= 0.0:
			mark_stats_dirty()
	if _heartbeat_t > 0.0:
		_heartbeat_t -= delta
	if shield_t > 0.0:
		shield_t -= delta
		if shield_t <= 0.0:
			shield_hp = 0.0
			status.remove(&"shielded")
	if _queued != &"" and _time - _queued_t > INPUT_BUFFER:
		_queued = &""
	_second_wind_cd = maxf(0.0, _second_wind_cd - delta)
	_aura_tick(delta)
	if resource and resource.kind == &"focus":
		resource.tick(delta, in_combat(), false, not _enemy_near(ClassResource.FOCUS_CALM_RANGE), _enemy_near(ClassResource.FOCUS_PRESSURE_RANGE),
			1.0 + stats.get_stat(&"focus_gain"))
		_sync_status(&"steady", resource.is_steady(_steady_at()))
	elif resource and resource.kind == &"combo":
		resource.tick(delta, in_combat())
		_sync_status(&"poised", resource.is_poised())
	elif resource:
		resource.tick(delta, _enemy_near(8.0), stats.has_flag(&"valor_hold"))
		var resolute := resource.is_resolute(40.0 if stats.has_flag(&"resolute_40") else 50.0)
		if resolute != status.has(&"resolute"):
			if resolute:
				status.apply(&"resolute", 0.0)
			else:
				status.remove(&"resolute")
		if resource.is_overcharged() != status.has(&"overcharged"):
			if resource.is_overcharged():
				status.apply(&"overcharged", 0.0)
			else:
				status.remove(&"overcharged")
	var low := is_low_hp()
	if low != status.has(&"badly_hurt"):
		if low:
			status.apply(&"badly_hurt", 0.0)
		else:
			status.remove(&"badly_hurt")
	_hurt_sound_t -= delta
	if low and _hurt_sound_t <= 0.0:
		_hurt_sound_t = 2.6
		Audio.play_ui(&"heartbeat")

func _sync_status(id: StringName, on: bool) -> void:
	if on != status.has(id):
		if on:
			status.apply(id, 0.0)
		else:
			status.remove(id)
		mark_stats_dirty()

func _regen(delta: float) -> void:
	var hr := stats.get_stat(&"hp_regen") + aura_regen() + class_passives.debuff_regen()
	var mr := stats.get_stat(&"mana_regen")
	if stats.has_flag(&"still_mana") and _still_t >= 1.0:
		mr *= 1.0 + stats.flag(&"still_mana")
		hr *= 1.5
	if status.has(&"regen"):
		hr += status.magnitude(&"regen")
	hr *= status.heal_taken_mult()
	if hp < max_hp():
		hp = minf(max_hp(), hp + hr * delta)
		health_changed.emit(hp, max_hp())
	if mana < max_mana():
		mana = minf(max_mana(), mana + mr * delta)
		mana_changed.emit(mana, max_mana())

func _enemy_near(r: float) -> bool:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e.alive and e.global_position.distance_squared_to(global_position) < r * r and e.is_aggressive():
			return true
	return false

func mark_combat() -> void:
	_combat_t = 0.0

# ---- Input --------------------------------------------------------------------------------------------------

func _mouse_blocked() -> bool:
	var h := get_viewport().gui_get_hovered_control()
	return h != null and h.mouse_filter == Control.MOUSE_FILTER_STOP

func _read_input(delta: float) -> void:
	if Input.is_action_just_pressed(&"dodge"):
		_request(&"dodge")
	var lmb := Input.is_action_pressed(&"primary") and not _mouse_blocked()
	if Input.is_action_just_pressed(&"primary") and not _mouse_blocked():
		if Game.hover_loot and is_instance_valid(Game.hover_loot):
			Game.hover_loot.request_pickup(self)
		elif Game.hover_ally and is_instance_valid(Game.hover_ally) and Game.hover_target == null:
			Net.trade_prompt((Game.hover_ally as NetAvatar).owner_peer)
		else:
			_request(&"light")
	elif lmb and Settings.attack_hold_repeat and (action == null or action_kind == &"light") and (_queued == &"" or _queued == &"light"):
		# holding attack keeps the chain going (finisher lock prevents endless spam); it never replaces an explicit
		# buffered intent (skill, heavy, dodge) that is waiting for the current swing's recovery
		_request(&"light")
	var wt := _main_type()
	if Input.is_action_just_pressed(&"secondary") and not _mouse_blocked():
		if wt != null and wt.charge_max > 0.0:
			_request(&"charge")
		else:
			_request(&"heavy")
	if charging and not Input.is_action_pressed(&"secondary"):
		_release_charge()
	if Settings.guard_toggle:
		if Input.is_action_just_pressed(&"guard"):
			_guard_latched = not _guard_latched
	else:
		_guard_latched = Input.is_action_pressed(&"guard")
	var want_guard := _guard_latched and _can_guard()
	if want_guard != guarding:
		_set_guard(want_guard)
	for i in HeroData.SKILL_BAR_SIZE:
		if Input.is_action_just_pressed(StringName("skill_%d" % (i + 1))):
			var sid: StringName = hero.skill_bar[i]
			if sid != &"":
				_request(&"skill", sid)
	if channel_skill != &"":
		var idx := hero.skill_bar.find(channel_skill)
		if idx < 0 or not Input.is_action_pressed(StringName("skill_%d" % (idx + 1))):
			_stop_channel()
	if Input.is_action_just_pressed(&"potion_health"):
		use_belt(0)
	if Input.is_action_just_pressed(&"potion_mana"):
		use_belt(1)
	if Input.is_action_just_pressed(&"interact"):
		interact()
	if Input.is_action_just_pressed(&"ping"):
		ping_here()
	if Input.is_action_just_pressed(&"summon_party") and Net.is_active():
		Net.open_team_portal()
	if Input.is_action_just_pressed(&"zoom_in"):
		camera.zoom(-1)
	elif Input.is_action_just_pressed(&"zoom_out"):
		camera.zoom(1)
	_try_queued()

func _main_type() -> WeaponTypeDef:
	return stats.loadout.main_type if stats and stats.loadout else null

func _request(kind: StringName, arg := &"") -> void:
	_queued = kind
	_queued_arg = arg
	_queued_t = _time
	_try_queued()

func _try_queued() -> void:
	if _queued == &"":
		return
	var kind := _queued
	var arg := _queued_arg
	if not _can_start(kind):
		return
	_queued = &""
	match kind:
		&"light": _start_light()
		&"heavy": _start_heavy(1.0, false)
		&"charge": _start_charge()
		&"dodge": _start_dodge()
		&"skill": _start_skill(arg)

## Whether a new intent may interrupt what is happening now.
func _can_start(kind: StringName) -> bool:
	if not alive or status.is_disabled():
		return false
	if kind == &"dodge":
		if dodge_cd > 0.0:
			return false
		if status.has(&"webbed"):
			Events.notify.emit("Webbed! You cannot dodge", &"locked")
			return false
		if is_overburdened():
			_overburden_notice()
			return false
		if action == null:
			return true
		# dodge-cancel: allowed during recovery, and during a light/heavy wind-up before the blow lands
		return action.can_cancel() or action_kind == &"potion" or ((action_kind == &"light" or action_kind == &"heavy") and action.elapsed < action.first_hit_time() * 0.6)
	if channel_skill != &"" and kind != &"skill":
		return false
	if charging:
		return false
	if kind == &"light" and _chain_lock > 0.0:
		return false
	if action == null:
		return true
	if action_kind == &"dodge":
		return action.can_cancel()
	if kind == &"heavy" and action_kind == &"light":
		return action.in_combo_window() and action.can_cancel()
	return action.can_cancel()

# ---- Light chain ----------------------------------------------------------------------------------------------

func _attack_rate(anims: Array) -> float:
	var wt := _main_type()
	var aps := stats.loadout.aps() * stats.get_stat(&"attack_speed", 1.0)
	var total := 0.0
	for n in anims:
		total += float(DB.anim(n).get("length", 0.6))
	var avg := total / maxf(1.0, anims.size())
	return clampf(aps * avg, StatCalculator.SPEED_MULT_MIN, StatCalculator.SPEED_MULT_MAX)

func _chain_anims() -> Array:
	var wt := _main_type()
	if wt == null:
		return [&"sword_1", &"sword_2", &"sword_3", &"sword_4"]
	if stats.loadout.dual_wield and not wt.dual_light_anims.is_empty():
		return wt.dual_light_anims
	return wt.light_anims

func _start_light() -> void:
	_cancel_action(true)
	if _time > _chain_expire:
		chain_step = 0
	var anims := _chain_anims()
	var step := chain_step % 4
	var anim: StringName = anims[mini(step, anims.size() - 1)]
	var a := TimedAction.from_anim(anim, _attack_rate(anims))
	a.data["step"] = step
	a.data["hand"] = stats.loadout.hand_for_step(step)
	_begin(a, &"light")
	var wt := _main_type()
	a.move_mult = wt.move_mult if wt else 0.3
	if wt != null and wt.ranged:
		a.on_release = func() -> void: _fire_weapon_projectile(a, false, 1.0)
	else:
		a.on_window = func(w: int, first: bool) -> void: _melee_window(a, w, first)
	visual.play_action(anim, a.rate)
	Audio.play_at(wt.swing_sound if wt else &"swing_light", global_position, -2.0 + step)
	chain_step = step + 1
	_chain_expire = _time + a.combo_close
	combo_changed.emit(chain_step)
	if chain_step >= 4:
		chain_step = 0
		a.data["finisher"] = true
	mark_combat()

func _begin(a: TimedAction, kind: StringName) -> void:
	action = a
	action_kind = kind
	visual.interrupt_fidget()
	_face_aim_now()

func _face_aim_now() -> void:
	var d := aim_dir()
	rotation.y = atan2(d.x, d.z)

func _weapon_request(a: TimedAction, heavy: bool, mult: float) -> DamageRequest:
	var wt := _main_type()
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = stats
	req.use_weapon = true
	req.hand = int(a.data.get("hand", 0))
	var step := int(a.data.get("step", 0))
	req.heavy = heavy
	req.label = "Heavy attack" if heavy else "Attack %d" % (step + 1)
	var chain_m := float(wt.chain_mults[step]) if wt and step < wt.chain_mults.size() else 1.0
	var chain_k := float(wt.chain_knock[step]) if wt and step < wt.chain_knock.size() else 1.0
	req.weapon_mult = (wt.heavy_multiplier * mult if heavy else chain_m) if wt else (1.8 * mult if heavy else chain_m)
	req.knockback = ((wt.heavy_knockback if wt else 8.0) * minf(mult, 1.6) if heavy else (wt.knockback if wt else 2.0) * chain_k)
	req.poise = (wt.poise_damage if wt else 8.0) * (2.2 * mult if heavy else chain_m)
	req.tags[&"weapon"] = true
	req.tags[&"attack_id"] = a.get_instance_id()
	decorate_request(req, null)
	return req

func _melee_window(a: TimedAction, w: int, first: bool) -> void:
	var wt := _main_type()
	var reach := wt.reach if wt else 1.8
	var arc := wt.arc_degrees if wt else 100.0
	var heavy := action_kind == &"heavy" or action_kind == &"charge_release"
	var finisher := bool(a.data.get("finisher", false))
	var big := heavy or finisher
	if heavy:
		reach *= 1.1
		arc = minf(arc * 1.2, 220.0)
	if first:
		visual.set_trail(true, wt.trail_color if wt else Color(1, 1, 1, 0.5), wt.length if wt else 1.0)
		var c := Color(1.0, 0.95, 0.85, 0.75)
		if stats.loadout.elem_share_for(int(a.data.get("hand", 0))) > 0.0:
			c = Elements.color(stats.loadout.element_for(int(a.data.get("hand", 0))))
			c.a = 0.8
		var cw := int(a.data.get("step", 0)) % 2 == 0
		FX.spawn_facing(VFXLib.slash_arc(c, reach * 0.95, arc, 1.05, 0.2 / maxf(a.rate, 0.5), 0.55, cw), global_position, forward())
		if big:
			_big_swing_fx(reach, arc, cw)
	var req := _weapon_request(a, heavy, float(a.data.get("charge_mult", 1.0)))
	if finisher:
		req.tags[&"finisher"] = true
	var hits := 0
	var first_hit: Actor = null
	for t: Actor in CombatQuery.actors_in_arc(get_world_3d(), global_position, forward(), reach, arc, BH.LAYER_ENEMY):
		if not a.mark_hit(w, t):
			continue
		if CombatQuery.blocked(get_world_3d(), center(), t.center()):
			continue
		var r := req.clone()
		r.tags[&"push_dir"] = (t.global_position - global_position).slide(Vector3.UP).normalized()
		if wt and (wt.id == &"dagger" or wt.id == &"claw") and t.forward().dot(forward()) > 0.5:
			r.positional_mult = 1.25 if wt.id == &"dagger" else 1.2   # backstab
		_apply_attack_powers(r, a)
		var res := t.receive_hit(r, self, t.center())
		_on_hit_dealt(t, res, r)
		hits += 1
		if first_hit == null and res != null and not res.evaded and not res.blocked:
			first_hit = t
	if hits > 0:
		Audio.play_at(wt.hit_sound if wt else &"hit_flesh", global_position + forward() * reach * 0.6)
	if first_hit != null and big and not a.data.get("big_fx", false):
		a.data["big_fx"] = true
		_big_impact_fx(first_hit)

## Knight colour for heavy blows: tempered gold, or the weapon's element when it carries one.
func _strike_color() -> Color:
	var el := stats.loadout.element_for(0)
	if stats.loadout.elem_share_for(0) > 0.0 and el != Elements.PHYSICAL:
		return Elements.color(el)
	return Color(1.0, 0.78, 0.35)

## Finisher / heavy swing: a second, wider blazing arc, a lunge of the body and a burst at the blade's path.
func _big_swing_fx(reach: float, arc: float, cw: bool) -> void:
	var c := _strike_color()
	FX.spawn_facing(VFXLib.slash_arc(Color(c.r, c.g, c.b, 0.95), reach * 1.2, minf(arc * 1.15, 240.0), 0.9, 0.3, 0.35, cw), global_position, forward())
	FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 1.0, 0.95, 0.7), reach * 0.8, arc, 1.2, 0.18, 0.25, not cw), global_position, forward())
	FX.spawn(VFXLib.light_flash(c, 3.0, 4.0, 0.2), global_position + forward() * reach * 0.5 + Vector3.UP)
	visual.play_pose([[0.07, {"pos": Vector3(0, -0.06, 0.32), "rot": Vector3(0.16, 0, 0)}], [0.22, {"pos": Vector3(0, -0.04, 0.28), "rot": Vector3(0.1, 0, 0)}]], 0.22)

## Where a finisher / heavy blow lands: ground cracks, shock ring, debris, a flash and a hard shake.
func _big_impact_fx(t: Actor) -> void:
	var c := _strike_color()
	var at := t.global_position
	FX.spawn(VFXLib.heavy_impact(c, 1.0), at)
	FX.spawn(VFXLib.impact_flash(c.lerp(Color.WHITE, 0.4), 3.2, 0.2, 8), t.center())
	FX.spawn(VFXLib.light_flash(c, 6.0, 6.0, 0.25), t.center())
	Events.camera_shake.emit(0.4)
	Events.impact.emit(at, 12.0, &"earth")
	FX.rumble(0.6, 0.9, 0.18)
	Audio.play_at(&"hit_heavy", at, 2.0)

## Every-fifth-attack stagger (Dawnbreaker) and the Riposte counter.
func _apply_attack_powers(r: DamageRequest, a: TimedAction) -> void:
	if a.data.get("counted", false) == false:
		a.data["counted"] = true
		_attack_counter += 1
		if stats.has_flag(&"fifth_stagger") and _attack_counter % 5 == 0:
			a.data["fifth"] = true
			_radiant_shockwave()
	if a.data.get("fifth", false):
		r.poise *= 4.0
		r.knockback *= 1.6
	if _riposte_t > 0.0:
		r.force_crit = true

func _radiant_shockwave() -> void:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = stats
	req.use_weapon = true
	req.weapon_mult = 0.8
	req.conversion = {Elements.LIGHT: 1.0}
	req.knockback = 10.0
	req.poise = 60.0
	req.label = "Dawnbreaker"
	AreaEffects.burst(self, global_position, 3.5, BH.LAYER_ENEMY, req, self)
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.9, 0.55, 0.95), 3.5, 0.45, 0.9), global_position)
	FX.spawn(VFXLib.light_flash(Color(1.0, 0.9, 0.6), 6.0, 7.0, 0.3), global_position + Vector3.UP)
	Events.camera_shake.emit(0.35)
	Audio.play_at(&"holy_strike", global_position, 2.0)

func _fire_weapon_projectile(a: TimedAction, heavy: bool, mult: float) -> void:
	var wt := _main_type()
	var req := _weapon_request(a, heavy, mult)
	req.tags[&"projectile"] = true
	_apply_attack_powers(req, a)
	var el := stats.loadout.element_for(int(a.data.get("hand", 0)))
	var look := "bolt" if wt.id == &"crossbow" else ("arrow" if wt.id == &"bow" else "orb")
	if wt.id == &"javelin":
		var main := hero.equipment.get_item(&"main_weapon")
		look = "model:" + (weapon_model_for(main, wt) if main else wt.model)
	var speed := wt.projectile_speed * (1.0 + stats.get_stat(&"projectile_speed")) * (1.3 if heavy else 1.0)
	var pr := Projectile.spawn(runner.parent(), cast_point(), projectile_dir(), speed, req, self, BH.LAYER_ENEMY, el, look)
	pr.max_range = wt.reach
	pr.radius = 0.3 if wt.id in [&"bow", &"crossbow", &"javelin"] else 0.35
	pr.hit_sound = wt.hit_sound
	if heavy and (wt.id in [&"bow", &"crossbow", &"javelin"]):
		pr.pierce = 2
	if stats.has_flag(&"pierce_chance") and randf() < stats.flag(&"pierce_chance"):
		pr.pierce += 1
	if (heavy and wt.id == &"staff") or (a.data.get("finisher", false) and wt.id == &"staff"):
		pr.explode_radius = 2.2
		pr.on_end = func(pt: Vector3, _w: bool) -> void:
			FX.spawn(VFXLib.ring_wave(Elements.color(el), 2.2, 0.35), pt)
	pr.on_hit = func(t: Actor, res: DamageResult, pt: Vector3) -> void:
		_on_hit_dealt(t, res, req)
	if wt.id in [&"bow", &"crossbow"]:
		class_passives.split_shot(pr)
	Audio.play_at(wt.swing_sound, global_position, -3.0)

# ---- Heavy / charge ---------------------------------------------------------------------------------------------

func _start_heavy(charge_frac: float, charged: bool) -> void:
	var branch := 0
	if action != null and action_kind == &"light":
		branch = int(action.data.get("step", 0)) + 1
	_cancel_action(true)
	var wt := _main_type()
	var anim: StringName
	if charged:
		anim = wt.heavy_anim if wt and wt.id in [&"bow", &"crossbow"] else &"charge_release"
	elif wt == null:
		anim = &"sword_heavy"
	elif stats.loadout.dual_wield and wt.dual_heavy_anim != &"":
		anim = wt.dual_heavy_anim
	else:
		anim = wt.heavy_anim
	var rate := clampf(stats.get_stat(&"attack_speed", 1.0), StatCalculator.SPEED_MULT_MIN, StatCalculator.SPEED_MULT_MAX)
	var a := TimedAction.from_anim(anim, rate)
	var mult := 1.0 + (wt.charge_bonus * charge_frac if wt and charged else 0.0) + 0.08 * branch
	a.data["charge_mult"] = mult
	a.data["step"] = 3 if branch >= 3 else 0
	_begin(a, &"charge_release" if charged else &"heavy")
	a.move_mult = 0.1
	if wt != null and wt.ranged:
		a.on_release = func() -> void: _fire_weapon_projectile(a, true, mult)
	else:
		a.on_window = func(w: int, first: bool) -> void: _melee_window(a, w, first)
	visual.play_action(anim, rate)
	Audio.play_at(wt.heavy_sound if wt else &"swing_heavy", global_position, 1.0)
	chain_step = 0
	_chain_lock = FINISHER_LOCK
	mark_combat()

func _start_charge() -> void:
	_cancel_action(true)
	charging = true
	_charge_t = 0.0
	var wt := _main_type()
	visual.hold_action(&"crossbow_aim" if wt and wt.id == &"crossbow" else (&"bow_draw_hold" if wt and wt.id == &"bow" else &"charge_hold"))
	Audio.play_at(&"bow_draw" if wt and wt.id == &"bow" else &"arcane_charge", global_position, -4.0)
	_face_aim_now()

func _release_charge() -> void:
	if not charging:
		return
	charging = false
	var wt := _main_type()
	var frac := clampf(_charge_t / maxf(wt.charge_max if wt else 1.0, 0.1), 0.0, 1.0)
	visual.stop_action()
	if frac < 0.15:
		_start_heavy(0.0, false)
	else:
		_start_heavy(frac, true)
		if frac >= 1.0:
			FX.spawn(VFXLib.light_flash(Color(1.0, 0.9, 0.6), 4.0, 4.0, 0.2), center())

# ---- Dodge ------------------------------------------------------------------------------------------------------

## Touch "Roll" button: the next dodge is a forward roll even with the stick at rest. The request outlives the tap and
## the input buffer (a roll pressed during a swing still comes out as a roll); the Dodge button cancels it.
var _roll_forward_until := 0

func request_roll_forward(on := true) -> void:
	_roll_forward_until = Time.get_ticks_msec() + 800 if on else 0

func _start_dodge() -> void:
	_cancel_action(true)
	var input := _move_input()
	var dir := input if input.length() > 0.1 else -aim_dir()
	var anim := &"dodge_roll" if input.length() > 0.1 else &"dodge_step"
	if Time.get_ticks_msec() < _roll_forward_until:
		_roll_forward_until = 0
		if input.length() <= 0.1:
			var fwd := global_transform.basis.z
			fwd.y = 0.0
			dir = fwd.normalized() if fwd.length() > 0.01 else -aim_dir()
		anim = &"dodge_roll"
	var a := TimedAction.from_anim(anim, 1.0)
	_begin(a, &"dodge")
	rotation.y = atan2(dir.x, dir.z) if anim == &"dodge_roll" else atan2(-dir.x, -dir.z)
	var travel := (a.travel if a.travel > 0.0 else 4.0) * (1.0 + stats.get_stat(&"dodge_distance"))
	var move_time := maxf(0.15, (a.iframes.y if a.iframes.y > 0.0 else a.duration * 0.65))
	dash(dir, travel / move_time, move_time)
	visual.play_action(anim, 1.0, 0.06)
	dodge_cd = stats.get_stat(&"dodge_cooldown", 1.0)
	Audio.play_at(&"dodge_roll", global_position)
	if stats.has_flag(&"dodge_trail"):
		lightning_trail(global_position, global_position + dir * travel)
	if stats.has_flag(&"dodge_haste"):
		_haste_t = 2.0
		mark_stats_dirty()
	chain_step = 0

# ---- Guard ------------------------------------------------------------------------------------------------------

func _can_guard() -> bool:
	if charging or channel_skill != &"":
		return false
	if action != null and not action.can_cancel():
		return false
	return true

func _set_guard(on: bool) -> void:
	guarding = on
	if on:
		_cancel_action(true)
		_guard_t = 0.0
		status.apply(&"guard", 0.0)
		visual.set_upper(&"block_loop")
	else:
		status.remove(&"guard")
		visual.set_upper(&"")

func _prepare_incoming(req: DamageRequest, attacker: Node) -> void:
	if guarding and req.blockable and attacker is Node3D and req.kind != DamageRequest.Kind.DOT:
		var to_att: Vector3 = (attacker as Node3D).global_position - global_position
		to_att.y = 0.0
		if to_att.length() < 0.01 or forward().angle_to(to_att.normalized()) < deg_to_rad(75.0):
			req.guarding = true
			req.perfect_block = _guard_t <= stats.get_stat(&"parry_window", 0.18)

# ---- Skills -----------------------------------------------------------------------------------------------------

func skill_rank(sid: StringName) -> int:
	var r := hero.skill_rank(sid)
	return r + int(stats.get_stat(&"skill_levels")) if r > 0 else 0

func skill_params(sid: StringName) -> Dictionary:
	var s := DB.skill(sid)
	return s.resolve(skill_rank(sid), hero.skill_upgrades(sid)) if s else {}

func mana_cost(sid: StringName) -> float:
	var s := DB.skill(sid)
	if s == null:
		return 0.0
	if resource and stats.has_flag(&"arcane_free") and resource.is_overcharged():
		return 0.0
	var c := s.mana_at(hero.skill_rank(sid)) * (1.0 - stats.get_stat(&"mana_cost_reduction"))
	if resource:
		c *= resource.mana_cost_mult()
	return maxf(0.0, c)

func skill_cooldown(sid: StringName) -> float:
	var s := DB.skill(sid)
	return s.cooldown * (1.0 - stats.get_stat(&"cdr")) if s else 0.0

## Why a skill cannot be used right now ("" = usable). The HUD shows this.
func skill_block_reason(sid: StringName) -> String:
	var s := DB.skill(sid)
	if s == null or hero.skill_rank(sid) <= 0:
		return "Not learned"
	if cooldowns.has(sid):
		return "Cooldown"
	if mana + 0.001 < mana_cost(sid):
		return "Not enough Mana"
	if s.valor_cost > 0.0 and (resource == null or resource.value < s.valor_cost):
		return "Requires %d Valor" % roundi(s.valor_cost)
	if s.is_aura() and hero.active_aura == sid:
		return ""                                 # switching an aura off is always allowed
	if s.requires == &"melee" and (_main_type() == null or _main_type().ranged):
		return "Requires a melee weapon"
	if s.requires == &"bow" and (_main_type() == null or not (_main_type().id in [&"bow", &"crossbow", &"javelin"])):
		return "Requires a bow, crossbow or javelin"
	if s.requires == &"shield" and not stats.loadout.has_shield:
		return "Requires a shield"
	if s.kind == DamageRequest.Kind.SPELL and status.is_silenced():
		return "Silenced"
	if (s.behavior == &"dash_strike" or s.behavior == &"leap") and is_overburdened():
		return "Overburdened: too heavy to dash"
	return ""

func _start_skill(sid: StringName) -> void:
	var s := DB.skill(sid)
	if s == null:
		return
	var why := skill_block_reason(sid)
	if why != "":
		Events.notify.emit(why, &"error")
		Audio.play_ui(&"ui_error")
		return
	if s.is_aura():
		toggle_aura(sid)
		return
	if s.behavior == &"spin":
		_start_channel(s)
		return
	_cast_serial += 1
	var p := skill_params(sid)
	_cancel_action(true)
	var rate := clampf(stats.get_stat(s.anim_speed_stat, 1.0), StatCalculator.SPEED_MULT_MIN, StatCalculator.SPEED_MULT_MAX)
	var clip := &"crossbow_heavy" if s.requires == &"bow" and _main_type() != null and _main_type().id == &"crossbow" else s.anim
	var a := TimedAction.from_anim(clip, rate)
	a.move_mult = 0.0
	_begin(a, &"skill")
	if not runner.setup(s, p, a):
		action = null
		return
	_pay_skill(s)
	visual.play_action(clip, rate)
	SkillFX.cast(self, s, a)
	if s.sound_cast != &"" and s.behavior in [&"melee_arc", &"dash_strike", &"leap", &"judgment"]:
		Audio.play_at(s.sound_cast, global_position)
	_after_cast(s)

func _pay_skill(s: SkillDef) -> void:
	var paid := mana_cost(s.id)
	if spend_mana(paid):
		class_passives.refund(s, paid)
	var cd := skill_cooldown(s.id)
	if cd > 0.0:
		cooldowns[s.id] = cd
		cooldown_total[s.id] = cd
		cooldowns_changed.emit()
	skill_used.emit(s.id)
	mark_combat()

func _after_cast(s: SkillDef) -> void:
	if resource and resource.kind == &"arcane" and s.kind == DamageRequest.Kind.SPELL and s.id != &"arcane_surge":
		resource.gain(1.0)
	if s.kind == DamageRequest.Kind.SPELL and s.element != Elements.PHYSICAL:
		if stats.has_flag(&"arcane_amp") and _last_element >= 0 and s.element != _last_element:
			status.apply(&"arcane_amp")
		_last_element = s.element
	if stats.has_flag(&"aether_heartbeat") and _heartbeat_t <= 0.0:
		_heartbeat_t = 10.0
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL if s.kind == DamageRequest.Kind.SPELL else DamageRequest.Kind.ATTACK
		req.attacker = stats
		req.use_weapon = req.kind == DamageRequest.Kind.ATTACK
		req.weapon_mult = stats.flag(&"aether_heartbeat")
		req.base_min = 12.0 * level * 0.5 + 10.0
		req.base_max = req.base_min * 1.3
		req.conversion = {Elements.LIGHT: 0.5, Elements.WIND: 0.5}
		req.knockback = 8.0
		req.label = "Aetherheart"
		AreaEffects.burst(self, global_position, 4.0, BH.LAYER_ENEMY, req, self)
		FX.spawn(VFXLib.ring_wave(Color(0.6, 0.98, 1.0, 0.95), 4.0, 0.5, 0.9), global_position)

func _start_channel(s: SkillDef) -> void:
	_cancel_action(true)
	channel_skill = s.id
	_channel_params = skill_params(s.id)
	_channel_tick = 0.0
	visual.hold_action(s.anim, clampf(stats.get_stat(&"attack_speed", 1.0), 0.6, 1.8))
	Audio.play_loop(&"whirlwind_loop", self)
	SkillFX.cast(self, s, null)
	skill_used.emit(s.id)
	mark_combat()

func _update_channel(delta: float) -> void:
	if channel_skill == &"":
		return
	var s := DB.skill(channel_skill)
	_channel_tick -= delta
	if _channel_tick <= 0.0:
		var cost := float(_channel_params.get("mana_per_tick", 2.0)) * (1.0 - stats.get_stat(&"mana_cost_reduction"))
		if not spend_mana(cost):
			_stop_channel()
			Events.notify.emit("Not enough Mana", &"error")
			return
		_channel_tick += float(_channel_params.get("tick", 0.3)) / clampf(stats.get_stat(&"attack_speed", 1.0), 0.6, 2.0)
		runner.spin_tick(s, _channel_params)
		mark_combat()

func _stop_channel() -> void:
	if channel_skill == &"":
		return
	channel_skill = &""
	visual.stop_action()
	Audio.stop_loop(self)

# ---- Auras (bh-010, Knight) ----------------------------------------------------------------------------------
# One aura at a time. While on, it reserves part of Maximum Mana and every second refreshes its status (and the stat
# modifiers it grants) on the Knight, their Tempos and co-op heroes in range; offensive auras also hurt enemies.

## Fraction of Maximum Mana the active aura reserves.
func aura_reserve() -> float:
	if hero == null or hero.active_aura == &"":
		return 0.0
	var s := DB.skill(hero.active_aura)
	if s == null:
		return 0.0
	return clampf(float(s.params.get("reserve", 0.15)) * (1.0 - stats.flag(&"aura_reserve_less") if stats else 1.0), 0.0, 0.6)

func toggle_aura(sid: StringName) -> void:
	var s := DB.skill(sid)
	if s == null or not s.is_aura():
		return
	if hero.active_aura == sid:
		hero.active_aura = &""
		status.remove(sid)
		_aura_visual(false)
		mark_stats_dirty()
		Events.notify.emit("%s ended" % s.display_name, &"info")
		Audio.play_ui(&"ui_close")
		skill_used.emit(sid)
		return
	if hero.active_aura != &"":
		status.remove(hero.active_aura)
	spend_mana(mana_cost(sid))
	hero.active_aura = sid
	_aura_t = 0.0
	mark_stats_dirty()
	_aura_visual(true)
	FX.spawn(VFXLib.ring_wave(_aura_color(s), float(skill_params(sid).get("radius", 10.0)), 0.6, 0.5), global_position)
	Audio.play_at(s.sound_cast if s.sound_cast != &"" else &"holy_chime", global_position)
	Events.notify.emit("%s active" % s.display_name, &"info")
	skill_used.emit(sid)
	mark_combat()

func _aura_color(s: SkillDef) -> Color:
	return Color(1.0, 0.62, 0.3) if s.aura_kind == &"offense" else Color(0.55, 0.78, 1.0)

## A soft glowing ring on the ground under the Knight while an aura is on.
func _aura_visual(on: bool) -> void:
	if _aura_ring and is_instance_valid(_aura_ring):
		_aura_ring.queue_free()
	_aura_ring = null
	if not on or hero == null or hero.active_aura == &"":
		return
	var s := DB.skill(hero.active_aura)
	var c := _aura_color(s)
	_aura_ring = MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 1.05
	tm.outer_radius = 1.2
	tm.rings = 40
	tm.ring_segments = 6
	_aura_ring.mesh = tm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = Color(c.r, c.g, c.b, 0.55)
	_aura_ring.material_override = m
	_aura_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_aura_ring.scale = Vector3(1, 0.08, 1)
	_aura_ring.position.y = 0.05
	add_child(_aura_ring)

## Everyone who shares the aura: this hero, local Tempos, and (through Net) other players' heroes and Tempos.
func _aura_tick(delta: float) -> void:
	if _aura_ring and is_instance_valid(_aura_ring):
		_aura_ring.rotation.y += delta * 0.7
	if hero == null or hero.active_aura == &"" or not alive:
		return
	_aura_t -= delta
	if _aura_t > 0.0:
		return
	_aura_t = AURA_PULSE
	var sid := hero.active_aura
	var s := DB.skill(sid)
	if s == null or hero.skill_rank(sid) <= 0:
		hero.active_aura = &""
		_aura_visual(false)
		mark_stats_dirty()
		return
	var p := skill_params(sid)
	var eff := 1.0 + stats.get_stat(&"aura_effect")
	var radius := float(p.get("radius", 10.0)) * (1.0 + stats.get_stat(&"aura_radius"))
	var mods := aura_mods(s, p, eff)
	var mag := float(p.get("magnitude", 0.0)) * eff
	status.apply(sid, AURA_STATUS_TIME, mag, 0.0, Elements.PHYSICAL, mods)
	for t in get_tree().get_nodes_in_group(&"tempo"):
		if t is Actor and t.alive and t.global_position.distance_to(global_position) <= radius:
			(t as Actor).status.apply(sid, AURA_STATUS_TIME, mag, 0.0, Elements.PHYSICAL, aura_mods(s, p, eff))
	if Net.is_active():
		for av in Net.avatars():
			if av.alive and av.global_position.distance_to(global_position) <= radius:
				Net.send_aura(av, sid, AURA_STATUS_TIME, mag, s.aura_mods, p, eff)
	# offensive pulses
	var pmin := float(p.get("pulse_min", 0.0))
	if pmin > 0.0 or p.has("pulse_chill"):
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = stats
		req.base_min = pmin * eff
		req.base_max = float(p.get("pulse_max", pmin)) * eff
		req.conversion = {s.element: 1.0}
		req.can_crit = false
		req.evadable = false
		req.knockback = 0.0
		req.label = s.display_name
		if p.has("pulse_chill"):
			req.direct_status[&"chilled"] = float(p.pulse_chill)
		var pr := float(p.get("pulse_radius", radius * 0.6))
		for h in AreaEffects.burst(self, global_position, pr, BH.LAYER_ENEMY, req, self):
			_on_hit_dealt(h[0], h[1], req, s)
		FX.spawn(VFXLib.ring_wave(Elements.color(s.element), pr, 0.45, 0.3), global_position)
	elif int(Time.get_ticks_msec() / 1000) % 3 == 0:
		FX.spawn(VFXLib.ring_wave(Color(_aura_color(s), 0.35), radius, 0.9, 0.12), global_position)

## Stat modifiers an aura grants at the current rank: [[stat, op, param, scale]].
static func aura_mods(s: SkillDef, p: Dictionary, eff: float) -> Array:
	var out: Array = []
	for m in s.aura_mods:
		out.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, float(p.get(String(m[2]), 0.0)) * float(m[3]) * eff, s.display_name))
	return out

# ---- Potions & interaction ------------------------------------------------------------------------------------

func use_potion(kind: StringName) -> bool:
	if potion_cd > 0.0 or not alive:
		return false
	# A misclick on the belt must not waste a draught: the belt only drinks for the pool it restores.
	if kind == &"heal" and hp >= max_hp() - 0.5:
		_refuse_consumable("Your health is already full")
		return false
	if kind == &"mana" and mana >= max_mana() - 0.5:
		_refuse_consumable("Your mana is already full")
		return false
	var item: ItemInstance = null
	var order: Array = POTION_ORDER[kind]
	for bid in order:
		for c in hero.inventory.cells:
			if c != null and c.base.id == bid:
				item = c
				break
		if item:
			break
	if item == null:
		Events.notify.emit("No %s potions" % ("health" if kind == &"heal" else "mana"), &"error")
		Audio.play_ui(&"ui_error")
		return false
	return consume_item(item)

var _ping_t := -99.0

## Mark the aimed spot for the party (G; the touch Ping button): the cursor on a PC, the auto-aim target or the spot
## ahead in touch play (bh-011). Rate-limited so nobody can flood the others' screens.
func ping_here() -> void:
	if _time - _ping_t < 1.0 or not is_inside_tree():
		return
	_ping_t = _time
	Net.ping(CombatQuery.ground_at(get_world_3d(), aim_point + Vector3.UP * 0.5))

## Drink (or use) what belt slot `slot` is bound to (HeroData.potion_belt): an auto slot drinks the strongest draught of
## its kind; a chosen consumable is used exactly like a right-click on it in the bag (bh-011).
func use_belt(slot: int) -> bool:
	if hero == null or slot < 0 or slot >= HeroData.BELT_SIZE or not alive:
		return false
	var id: StringName = hero.potion_belt[slot]
	if id == HeroData.BELT_AUTO_HEAL:
		return use_potion(&"heal")
	if id == HeroData.BELT_AUTO_MANA:
		return use_potion(&"mana")
	var item: ItemInstance = null
	for c in hero.inventory.cells:
		if c != null and c.base.id == id:
			item = c
			break
	if item == null:
		Events.notify.emit("No %s left" % HeroData.belt_label(id), &"error")
		Audio.play_ui(&"ui_error")
		return false
	if potion_cd > 0.0 and (item.base.consumable_effect.has("heal") or item.base.consumable_effect.has("mana")):
		return false
	return consume_item(item)

## Use a consumable (potion belt or inventory right-click).
func consume_item(item: ItemInstance) -> bool:
	if item == null or not item.base.is_consumable() or not alive:
		return false
	var fx: Dictionary = item.base.consumable_effect
	if (fx.has("return") or fx.has("portal")) and not Net.may_travel():
		return false                 # (never since bh-015: everyone explores on their own)
	if fx.has("learn_recipe"):
		var err := Crafting.learn(hero, StringName(fx["learn_recipe"]))
		if err != "":
			Events.notify.emit(err, &"error")
			return false
		hero.inventory.consume(item.base.id, 1)
		Audio.play_ui(&"level_up")
		Events.notify.emit("Recipe learned: %s. Make it at a %s." % [DataCrafting.recipe(StringName(fx["learn_recipe"])).name,
			DataCrafting.station_names(DataCrafting.recipe(StringName(fx["learn_recipe"])).stations)], &"info")
		return true
	if fx.has("cache"):
		# a Relic Cache (bh-012): opened with a reveal; the gear goes to the bag (or the floor when it is full)
		hero.inventory.consume(item.base.id, 1)
		RelicCache.open(hero, int(fx["cache"]), self)
		return true
	if fx.has("phoenix"):
		Events.notify.emit("The Phoenix Feather works on its own: it burns when a killing blow lands.", &"info")
		return false
	if fx.has("portal"):
		if not TownPortal.open_for(self):
			return false
		hero.inventory.consume(item.base.id, 1)
		return true
	if fx.has("throw"):
		if not _throw_consumable(item, fx["throw"]):
			return false
		hero.inventory.consume(item.base.id, 1)
		return true
	if fx.has("buff"):
		var sid := StringName(fx["buff"])
		status.apply(sid, float(fx.get("duration", StatusRules.base_duration(sid))))
		mark_stats_dirty()
		if fx.has("smoke"):
			FX.spawn(VFXLib.particles(Color(0.55, 0.55, 0.58, 0.55), 40, 1.6, true, 1.6, 2.2, 180.0, Vector3(0, 0.4, 0), 0.8, false), global_position + Vector3.UP * 0.6)
			Audio.play_at(&"wind_gust", global_position, -2.0)
		else:
			Audio.play_at(&"potion_drink", global_position)
			FX.spawn(VFXLib.particles(ItemModels.tint_of(item.base), 16, 0.9, true, 0.3, 2.0, 40.0, Vector3(0, 2, 0), 0.4), global_position + Vector3.UP)
		Events.notify.emit("%s: %s" % [StatusRules.name_of(sid), item.base.flavor], &"info")
		hero.inventory.consume(item.base.id, 1)
		return true
	var refusal := restore_refusal(fx)
	if refusal != "":
		_refuse_consumable(refusal)
		return false
	if fx.has("heal") or fx.has("mana"):
		if potion_cd > 0.0:
			return false
		potion_cd = POTION_COOLDOWN
	var potion := 1.0 + stats.get_stat(&"potion_power")
	var heal_mult := (1.0 + stats.get_stat(&"healing") + GuildRules.potion_healing_bonus(hero)) * potion
	if fx.get("instant", 0.0) > 0.0:
		heal(max_hp() * float(fx.get("heal", 0.0)) * heal_mult)
		restore_mana(max_mana() * float(fx.get("mana", 0.0)) * potion)
	else:
		if fx.has("heal"):
			status.apply(&"regen", 2.0, max_hp() * float(fx.heal) * heal_mult / 2.0)
		if fx.has("mana"):
			_mana_over_time(max_mana() * float(fx.mana) * potion, 2.0)
	if fx.has("cleanse"):
		status.cleanse(CLEANSABLE)
	if fx.has("return"):
		Game.return_to_town()
	hero.inventory.consume(item.base.id, 1)
	Audio.play_at(&"potion_drink", global_position)
	FX.spawn(VFXLib.particles(Color(1.0, 0.3, 0.3, 0.8) if fx.has("heal") else Color(0.3, 0.5, 1.0, 0.8), 14, 0.8, true, 0.3, 2.0, 40.0, Vector3(0, 2, 0), 0.4), global_position + Vector3.UP)
	return true

## Why a restorative consumable would be wasted right now ("" = drinking it does something). A draught is refused only
## when every pool it restores is already full and it has no other effect (cleanse, return) that would still apply.
func restore_refusal(fx: Dictionary) -> String:
	if fx.has("return"):
		return ""
	var heals := fx.has("heal") and float(fx.get("heal", 0.0)) > 0.0
	var mans := fx.has("mana") and float(fx.get("mana", 0.0)) > 0.0
	var cleanses := fx.has("cleanse")
	if not (heals or mans or cleanses):
		return ""
	var hp_full := hp >= max_hp() - 0.5
	var mana_full := mana >= max_mana() - 0.5
	var useful := (heals and not hp_full) or (mans and not mana_full)
	if cleanses and _has_cleansable():
		useful = true
	if useful:
		return ""
	if cleanses and not (heals or mans):
		return "Nothing to cleanse"
	if heals and mans:
		return "Your health and mana are already full"
	return "Your health is already full" if heals else "Your mana is already full"

const CLEANSABLE := [&"poisoned", &"burning", &"bleeding", &"cursed", &"chilled", &"slowed", &"weakened"]

func _has_cleansable() -> bool:
	for sid in CLEANSABLE:
		if status.has(sid):
			return true
	return false

func _refuse_consumable(msg: String) -> void:
	Events.notify.emit(msg, &"warning")
	Audio.play_ui(&"ui_error")

func _mana_over_time(total: float, dur: float) -> void:
	var tw := create_tween()
	var last := [0.0]
	tw.tween_method(func(v: float) -> void:
		restore_mana(v - last[0])
		last[0] = v, 0.0, total, dur)

## Distance used to reach an interactable: flat (XZ) distance, as long as it is not more than about a body height above
## or below the hero. (A 3D distance made drops on a slope or step out of reach although the hero stood on top of them.)
func interact_distance(n3: Node3D) -> float:
	var d := n3.global_position - global_position
	var flat := Vector2(d.x, d.z).length()
	return flat if absf(d.y) < INTERACT_HEIGHT else Vector3(d.x, absf(d.y) - INTERACT_HEIGHT, d.z).length() + INTERACT_HEIGHT

## Best interactable in reach. Loot counts as slightly closer than doors and people so picking up is never blocked by
## a townsperson or a door standing next to the drop.
func find_interact_target() -> Node3D:
	var best: Node3D = null
	var best_score := INF
	for n in get_tree().get_nodes_in_group(&"interactable"):
		var n3 := n as Node3D
		if n3 == null or not n3.is_visible_in_tree() or not n.call(&"can_interact", self):
			continue
		var r: float = n.get("interact_range") if n.get("interact_range") != null else INTERACT_RANGE
		var d := interact_distance(n3)
		if d > r:
			continue
		var score := d * (0.7 if n3.is_in_group(&"loot") else 1.0)
		if score < best_score:
			best_score = score
			best = n3
	return best

func _update_interaction(delta: float, force := false) -> void:
	_interact_scan -= delta
	if _interact_scan > 0.0 and not force:
		return
	_interact_scan = 0.1
	var best := find_interact_target()
	if best != _interact_target:
		_interact_target = best
		interact_changed.emit(best)
		Events.interact_prompt.emit(best.call(&"interact_text") if best else "")

func interact() -> void:
	_update_interaction(0.0, true)   # never act on a target picked up to 0.1 s ago (it may have moved, landed or gone)
	if _interact_target and is_instance_valid(_interact_target) and _interact_target.call(&"can_interact", self):
		_cancel_action(true)
		if _interact_target.has_method(&"interact_anim"):
			var an: StringName = _interact_target.call(&"interact_anim")
			if an != &"":
				visual.play_action(an, 1.0)
		var d: Vector3 = _interact_target.global_position - global_position
		d.y = 0.0
		if d.length() > 0.1:
			rotation.y = atan2(d.x, d.z)
		_interact_target.call(&"interact", self)

# ---- Movement & facing ----------------------------------------------------------------------------------------

func _move_input() -> Vector3:
	if not input_enabled or Game.ui_blocking:
		return Vector3.ZERO
	var v := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	if v.length() < 0.1:
		return Vector3.ZERO
	return (camera.ground_basis() * Vector3(v.x, 0, v.y)).normalized() * minf(v.length(), 1.0)

func _movement(delta: float) -> Vector3:
	var speed := stats.get_stat(&"move_speed", 5.0)
	if _dash_t > 0.0:
		_dash_t -= delta
		return _dash_vel
	var input := _move_input()
	var mult := 1.0
	if action != null:
		mult = action.move_mult
	if guarding:
		mult = minf(mult, GUARD_MOVE_MULT)
	if charging:
		mult = minf(mult, CHARGE_MOVE_MULT)
		_charge_t += delta
		var wt := _main_type()
		if wt and _charge_t >= wt.charge_max + 0.6:
			_release_charge()
	if channel_skill != &"":
		mult = float(_channel_params.get("move_mult", 0.6))
	if status.is_disabled():
		mult = 0.0
	var want := input * speed * mult
	if input.length() > 0.1:
		_last_move_dir = input.normalized()
		_still_t = 0.0
	else:
		_still_t += delta
	var cur := Vector3(velocity.x, 0, velocity.z) - Vector3(knock_velocity.x, 0, knock_velocity.z)
	return cur.move_toward(want, ACCEL * delta)

func dash(dir: Vector3, speed: float, duration: float) -> void:
	var d := Vector3(dir.x, 0, dir.z)
	_dash_vel = d.normalized() * speed if d.length() > 0.01 else forward() * speed
	_dash_t = duration

func stop_dash() -> void:
	_dash_t = 0.0

func leap_to(target: Vector3, duration: float) -> void:
	_leap = {"from": global_position, "to": target, "t": 0.0, "dur": duration}
	invulnerable = true
	var d := target - global_position
	d.y = 0.0
	if d.length() > 0.1:
		rotation.y = atan2(d.x, d.z)

func _leap_step(delta: float) -> void:
	_leap.t += delta
	var k := clampf(_leap.t / _leap.dur, 0.0, 1.0)
	var p: Vector3 = (_leap.from as Vector3).lerp(_leap.to, ease(k, 0.8))
	p.y += sin(k * PI) * 2.6
	global_position = p
	velocity = Vector3.ZERO
	if k >= 1.0:
		_leap = {}
		invulnerable = false

func teleport_to(p: Vector3) -> void:
	global_position = p + Vector3.UP * 0.05
	velocity = Vector3.ZERO
	knock_velocity = Vector3.ZERO

func _update_facing(delta: float, desired: Vector3) -> void:
	if action != null and action_kind != &"dodge" and not action.can_cancel():
		return
	var face_aim := in_combat() or guarding or charging or channel_skill != &"" or action_kind in [&"light", &"heavy", &"skill", &"charge_release"]
	var dir := Vector3.ZERO
	if face_aim:
		dir = aim_dir()
	elif desired.length() > 0.3:
		dir = desired.normalized()
	if dir.length() > 0.1 and action_kind != &"dodge":
		rotation.y = lerp_angle(rotation.y, atan2(dir.x, dir.z), clampf(TURN_RATE * delta, 0.0, 1.0))

func _update_visual(delta: float) -> void:
	if visual == null:
		return
	var hv := Vector3(velocity.x, 0, velocity.z)
	var local := global_transform.basis.inverse() * hv
	visual.update_locomotion(Vector2(local.x, local.z), in_combat() or guarding, 1.0 - clampf(hp / max_hp() / LOW_HP, 0.0, 1.0), delta)
	if hv.length() > 0.5 and is_on_floor():
		visual.interrupt_fidget()
		_footstep_acc += hv.length() * delta
		var stride := lerpf(0.8, 1.7, clampf((hv.length() - 1.6) / 3.4, 0.0, 1.0))
		if _footstep_acc >= stride:
			_footstep_acc = 0.0
			var surf: StringName = Game.current_map.def.footstep_surface if Game.current_map and Game.current_map.def else &"stone"
			Audio.play_at(StringName("footstep_%s" % surf), global_position, -8.0 if hv.length() < 3.0 else -4.0)

# ---- Action lifecycle ----------------------------------------------------------------------------------------

func _on_action_done() -> void:
	var kind := action_kind
	action = null
	action_kind = &""
	visual.set_trail(false)
	if kind == &"light" and _chain_expire > 0.0 and chain_step == 0:
		_chain_lock = FINISHER_LOCK
	_try_queued()

func _cancel_action(interrupting: bool) -> void:
	if action != null:
		if visual and action_kind == &"skill":
			visual.relax_pose()
		action.finish(false)
		action = null
		action_kind = &""
	if visual:
		visual.set_trail(false)
	_dash_t = 0.0
	if charging:
		charging = false
		if visual:
			visual.stop_action()
	if not interrupting:
		_stop_channel()
		if guarding:
			_set_guard(false)

# ---- Damage intake & reactions ----------------------------------------------------------------------------------

func receive_hit(req: DamageRequest, attacker: Node = null, hit_point := Vector3.INF) -> DamageResult:
	if action != null and action.in_iframes() and req.kind != DamageRequest.Kind.DOT:
		var r0 := DamageResult.new()
		r0.evaded = true
		Events.damage_dealt.emit(self, r0, center(), attacker)
		if stats.has_flag(&"evade_mana"):
			restore_mana(stats.flag(&"evade_mana"))
		return r0
	if Game.god_mode:
		req.base_min = 0.0
		req.base_max = 0.0
		req.use_weapon = false
		req.weapon_mult = 0.0
	var res := super.receive_hit(req, attacker, hit_point)
	if not res.evaded and req.kind != DamageRequest.Kind.DOT:
		mark_combat()
	return res

func _apply_result(result: DamageResult, req: DamageRequest, attacker: Node, hit_point: Vector3) -> void:
	# Mana Shield (Mage passive): part of the damage drains Mana instead (1.5 Mana per point).
	if stats.has_flag(&"mana_shield") and result.total > 0 and mana > 1.0 and not result.evaded:
		var share := minf(stats.flag(&"mana_shield"), 0.6)
		var absorb := mini(int(result.total * share), int(mana / 1.5))
		if absorb > 0:
			spend_mana(absorb * 1.5)
			result.total -= absorb
			FX.spawn(VFXLib.shield_dome(Color(0.45, 0.6, 1.0, 0.5), 1.1, 0.35), global_position)
	super._apply_result(result, req, attacker, hit_point)
	if alive and stats.has_flag(&"second_wind") and _second_wind_cd <= 0.0 and hp < max_hp() * 0.35:
		_second_wind_cd = 45.0
		status.apply(&"second_wind", 4.0, max_hp() * stats.flag(&"second_wind") / 4.0)
		FX.spawn(VFXLib.ring_wave(Color(0.6, 1.0, 0.7, 0.9), 2.5, 0.5), global_position)
		FX.text_popup(center() + Vector3.UP * 0.9, "Second Wind", Color(0.6, 1.0, 0.7), 1.0)
	class_passives.return_damage(attacker, req, result)
	if alive and result.blocked and not req.tags.has(&"proc") and not req.tags.has(&"thorns"):
		_on_blocked(result, attacker)
	if resource and resource.kind == &"valor" and result.total > 0:
		resource.gain(result.total / maxf(1.0, max_hp()) * 20.0, 1.0 + stats.get_stat(&"valor_gain"))
	if stats.has_flag(&"thorns_chill") and attacker is Actor and not result.evaded:
		(attacker as Actor).status.apply(&"chilled", 2.0, StatusController.CHILL_SLOW, 0.0, Elements.ICE,
			[StatModifier.more(&"move_speed", -StatusController.CHILL_SLOW), StatModifier.more(&"attack_speed", -StatusController.CHILL_SLOW)])
	if stats.has_flag(&"low_hp_dr"):
		mark_stats_dirty()

func _on_damaged(result: DamageResult, req: DamageRequest) -> void:
	if result.total <= 0 or result.blocked:
		return
	var heavy := result.total > max_hp() * 0.12 or result.knockback >= HEAVY_KNOCK
	if action != null and action_kind in [&"light", &"heavy", &"skill"] and heavy:
		_cancel_action(true)
	if heavy and knock_velocity.length() < KNOCKED_THRESHOLD:
		visual.play_reaction(&"hit_heavy")
	elif action == null and not guarding:
		visual.play_reaction(&"hit", _hit_direction(req))

func _hit_direction(req: DamageRequest) -> StringName:
	var d: Vector3 = req.tags.get(&"push_dir", Vector3.ZERO)
	if d == Vector3.ZERO:
		return &"front"
	var local := global_transform.basis.inverse() * (-d)
	if absf(local.x) > absf(local.z):
		return &"right" if local.x > 0.0 else &"left"
	return &"front" if local.z > 0.0 else &"back"

func _on_blocked(result: DamageResult, attacker: Node) -> void:
	var gain := 15.0 if result.perfect_block else 8.0
	if status.has(&"bulwark"):
		gain *= 2.0
	if resource and resource.kind == &"valor":
		resource.gain(gain, 1.0 + stats.get_stat(&"valor_gain"))
	visual.play_reaction(&"parry" if result.perfect_block else &"block")
	Audio.play_at(&"parry" if result.perfect_block else &"block", global_position)
	if stats.has_flag(&"block_mana"):
		restore_mana(stats.flag(&"block_mana"))
		heal(max_hp() * 0.02, false)
	if _retaliation_cd <= 0.0 and not is_disabled() and stats.has_flag(&"retaliation") and attacker is Actor and (attacker as Actor).alive and randf() < stats.flag(&"retaliation") \
			and (attacker as Node3D).global_position.distance_to(global_position) < 4.0 and not CombatQuery.blocked(get_world_3d(), center(), attacker.center()):
		_retaliation_cd = 2.0
		var rq := DamageRequest.new()
		rq.tags[&"proc"] = true
		rq.kind = DamageRequest.Kind.ATTACK
		rq.attacker = stats
		rq.use_weapon = true
		rq.weapon_mult = 1.2
		rq.knockback = 6.0
		rq.poise = 20.0
		rq.label = "Counter-attack"
		rq.tags[&"push_dir"] = ((attacker as Node3D).global_position - global_position).slide(Vector3.UP).normalized()
		decorate_request(rq, null)
		var rr := (attacker as Actor).receive_hit(rq, self, (attacker as Actor).center())
		_on_hit_dealt(attacker as Actor, rr, rq)
		FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 0.85, 0.5, 0.9), 2.4, 140.0, 1.1, 0.2, 0.5), global_position, forward())
		FX.text_popup(center() + Vector3.UP * 0.9, "Counter-attack", UITheme.GOLD, 0.8)
	if result.perfect_block:
		FX.hitstop(0.08)
		Events.camera_shake.emit(0.2)
		if attacker is Actor:
			(attacker as Actor).status.apply(&"staggered")
			(attacker as Actor).status.apply(&"stagger_window", 2.0)
		if stats.has_flag(&"counter"):
			_riposte_t = RIPOSTE_WINDOW
	if stats.has_flag(&"block_shockwave") and _shockwave_cd <= 0.0:
		_shockwave_cd = 1.0
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.ATTACK
		req.attacker = stats
		req.use_weapon = true
		req.weapon_mult = stats.flag(&"block_shockwave")
		req.knockback = 9.0
		req.poise = 25.0
		req.label = "Echoing shockwave"
		AreaEffects.burst(self, global_position, 3.0, BH.LAYER_ENEMY, req, self)
		FX.spawn(VFXLib.ring_wave(Color(0.9, 0.85, 0.7, 0.9), 3.0, 0.35), global_position)
	if stats.has_flag(&"aether_pulse") and _pulse_cd <= 0.0:
		_pulse_cd = 2.0
		add_shield(max_hp() * stats.flag(&"aether_pulse"), 4.0)
		for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), global_position, 4.0, BH.LAYER_ENEMY):
			var d := a.global_position - global_position
			d.y = 0.0
			a.apply_knockback(d.normalized(), 9.0, stats, self)
		FX.spawn(VFXLib.ring_wave(Color(0.55, 0.98, 1.0, 0.95), 4.0, 0.5, 0.9), global_position)
		Audio.play_at(&"arcane_surge", global_position)

func add_shield(amount: float, duration: float) -> void:
	shield_hp = maxf(shield_hp, amount)
	shield_t = maxf(shield_t, duration)
	status.apply(&"shielded", duration)
	health_changed.emit(hp, max_hp())

func _on_shield_broken() -> void:
	status.remove(&"shielded")
	shield_t = 0.0
	Audio.play_at(&"shatter_ice", global_position, -4.0)

func _on_staggered(broken: bool) -> void:
	if stats.has_flag(&"unstaggerable"):
		status.remove(&"staggered")
		return
	_cancel_action(false)
	visual.play_reaction(&"stagger")
	Audio.play_at(&"stagger", global_position)

func apply_knockback(dir: Vector3, speed: float, source: DerivedStats, source_node: Node, depth := 0, launch := 0.0) -> void:
	if not _leap.is_empty() or invulnerable:
		return
	super.apply_knockback(dir, speed, source, source_node, depth, launch)
	if speed >= KNOCKED_THRESHOLD:
		_cancel_action(false)

func _wall_impact(into: float, normal: Vector3, point: Vector3, surface: StringName) -> void:
	super._wall_impact(into, normal, point, surface)
	if visual and alive:
		visual.play_reaction(&"wall")

# ---- Offensive bookkeeping (hooks for talents, uniques, set bonuses) -------------------------------------------

## Adds the multiplicative bonuses that live on requests (class resource states, keystones, buffs).
func decorate_request(req: DamageRequest, skill: SkillDef) -> void:
	if status.has(&"resolute") and req.kind == DamageRequest.Kind.ATTACK:
		req.more.append(["Resolute", 1.10])
		req.knockback *= 1.10
	if resource and resource.kind == &"arcane" and req.kind == DamageRequest.Kind.SPELL and resource.value > 0.0:
		req.more.append(["Arcane Charge x%d" % roundi(resource.value), resource.spell_damage_more()])
	if req.kind == DamageRequest.Kind.SPELL:
		if status.has(&"arcane_amp"):
			req.more.append(["Arcane Amplification", 1.0 + stats.flag(&"arcane_amp", 0.08) * status.stacks(&"arcane_amp")])
		if stats.has_flag(&"archmage"):
			req.more.append(["Archmage", 1.0 + 0.01 * floorf(max_mana() / stats.flag(&"archmage"))])
		if status.has(&"overload"):
			req.more.append(["Elemental Overload", 1.0 + stats.flag(&"overload", 0.4)])
	if _riposte_t > 0.0 and req.kind == DamageRequest.Kind.ATTACK:
		req.force_crit = true
	if status.has(&"stealth") and req.kind != DamageRequest.Kind.DOT:
		req.more.append(["Ambush", 1.5 + stats.flag(&"ambush")])
		req.force_crit = true

func on_skill_hit(skill: SkillDef, target: Actor, res: DamageResult) -> void:
	_on_hit_dealt(target, res, null, skill)

func _on_hit_dealt(target: Actor, res: DamageResult, req: DamageRequest, skill: SkillDef = null) -> void:
	if res == null or res.evaded:
		return
	mark_combat()
	if _riposte_t > 0.0 and (req == null or req.kind == DamageRequest.Kind.ATTACK):
		_riposte_t = 0.0
	if status.has(&"stealth"):
		status.remove(&"stealth")                  # the ambush is spent
	if res.total <= 0:
		return
	if resource and resource.kind == &"valor":
		var g := float(skill.params.get("valor_gain", 3.0)) if skill else 3.0
		resource.gain(g, 1.0 + stats.get_stat(&"valor_gain"))
	elif resource and resource.kind == &"combo":
		if skill != null:
			var cg := float(skill.params.get("combo_gain", 0.0))
			if cg > 0.0 and _combo_cast != _cast_serial:
				_combo_cast = _cast_serial
				resource.gain(cg + (1.0 if res.is_crit else 0.0))
		elif req != null and req.tags.has(&"weapon") and action != null and not action.data.get("combo_given", false):
			action.data["combo_given"] = true
			resource.gain(1.0)
	elif resource and resource.kind == &"focus":
		var ranged := (req != null and req.tags.has(&"projectile")) or (skill != null and skill.projectile_look == "arrow")
		if ranged and target.global_position.distance_to(global_position) > ClassResource.FOCUS_CALM_RANGE:
			resource.gain(ClassResource.FOCUS_PER_RANGED_HIT, 1.0 + stats.get_stat(&"focus_gain"))
	var moh := stats.get_stat(&"mana_on_hit")
	if moh > 0.0:
		restore_mana(moh)
	if res.mana_leech > 0.0:
		restore_mana(res.mana_leech)
	if skill and skill.kind == DamageRequest.Kind.SPELL and stats.has_flag(&"mana_on_spell_hit"):
		restore_mana(stats.flag(&"mana_on_spell_hit"))
	if res.is_crit:
		if stats.has_flag(&"crit_cdr"):
			var cut := stats.flag(&"crit_cdr")
			for k in cooldowns.keys():
				cooldowns[k] = maxf(0.0, cooldowns[k] - cut)
			cooldowns_changed.emit()
		if stats.has_flag(&"crit_heal"):
			heal(max_hp() * stats.flag(&"crit_heal"))
		if stats.has_flag(&"crit_lightning") and (req == null or not req.tags.has(&"proc")):
			_crit_lightning(target, res)
	if stats.has_flag(&"hit_ignite") and rng.randf() < stats.flag(&"hit_ignite") and target.alive:
		target.status.apply(&"burning", -1.0, 0.0, maxf(1.0, res.total * 0.25), Elements.FIRE)
	if stats.has_flag(&"burn_spread") and res.components.get(Elements.FIRE, 0.0) > 0.0 and target.status.has(&"burning"):
		_spread_burning(target)
	if res.reactions.has(&"fan"):
		_spread_burning(target)
	# Elemental Overload: three different elements within 4 s.
	if stats.has_flag(&"overload"):
		for e in res.components:
			if e != Elements.PHYSICAL and res.components[e] > 0.0:
				_overload_hits[e] = _time
		var recent := 0
		for e in _overload_hits:
			if _time - _overload_hits[e] <= 4.0:
				recent += 1
		if recent >= 3 and not status.has(&"overload"):
			status.apply(&"overload")
			_overload_hits.clear()
	for rx in res.reactions:
		FX.text_popup(target.center() + Vector3.UP * 0.9, DamageResult.REACTION_NAMES.get(rx, String(rx)), Elements.color(res.dominant_element), 0.9)

func _crit_lightning(from_target: Actor, res: DamageResult) -> void:
	var n := 0
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), from_target.global_position, 7.0, BH.LAYER_ENEMY):
		if a == from_target or n >= 3:
			continue
		n += 1
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = stats
		req.base_min = res.total * stats.flag(&"crit_lightning")
		req.base_max = req.base_min
		req.conversion = {Elements.LIGHTNING: 1.0}
		req.can_crit = false
		req.evadable = false
		req.tags[&"proc"] = true
		req.label = "Riftborn lightning"
		FX.spawn(VFXLib.lightning_bolt(from_target.center(), a.center()), Vector3.ZERO)
		a.receive_hit(req, self, a.center())
	if n > 0:
		Audio.play_at(&"lightning_zap", from_target.global_position)

func _spread_burning(src: Actor) -> void:
	var inst = src.status.statuses.get(&"burning")
	if inst == null:
		return
	for a: Actor in CombatQuery.actors_in_radius(get_world_3d(), src.global_position, 4.0, BH.LAYER_ENEMY):
		if a == src or a.status.has(&"burning"):
			continue
		a.status.apply(&"burning", -1.0, 0.0, inst.dps * 0.8, Elements.FIRE)
		FX.spawn(VFXLib.particles(Color(1.0, 0.5, 0.1, 0.9), 10, 0.4, true, 0.3, 4.0, 30.0, Vector3.ZERO, 0.2), a.center())
		break

func lightning_trail(from: Vector3, to: Vector3) -> void:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = stats
	req.base_min = 4.0 + level * 1.5
	req.base_max = req.base_min * 1.5
	req.conversion = {Elements.LIGHTNING: 1.0}
	req.direct_status[&"shocked"] = 60.0
	req.label = "Stormstride"
	var d := to - from
	d.y = 0.0
	for a: Actor in CombatQuery.actors_in_line(get_world_3d(), from, d.normalized(), d.length(), 2.0, BH.LAYER_ENEMY):
		a.receive_hit(req.clone(), self, a.center())
	FX.spawn(VFXLib.lightning_bolt(from + Vector3.UP * 0.3, to + Vector3.UP * 0.3, Color(1.0, 0.95, 0.5)), Vector3.ZERO)

func _on_actor_died(victim: Node, killer: Node) -> void:
	if killer != self or not (victim is Actor):
		return
	var v := victim as Actor
	if stats.has_flag(&"kill_heal"):
		heal(max_hp() * stats.flag(&"kill_heal"))
	if stats.has_flag(&"frozen_explode") and v.get_meta(&"died_frozen", false):
		if true:
			var req := DamageRequest.new()
			req.kind = DamageRequest.Kind.SPELL
			req.attacker = stats
			req.base_min = v.max_hp() * stats.flag(&"frozen_explode")
			req.base_max = req.base_min
			req.conversion = {Elements.ICE: 1.0}
			req.direct_status[&"chilled"] = 60.0
			req.can_crit = false
			req.label = "Frozen explosion"
			req.tags[&"proc"] = true
			AreaEffects.burst(self, v.global_position, 3.5, BH.LAYER_ENEMY, req, self, [v])
			FX.spawn(VFXLib.ring_wave(Elements.color(Elements.ICE), 3.5, 0.4, 0.8), v.global_position)
			FX.spawn(VFXLib.particles(Color(0.7, 0.9, 1.0, 1.0), 30, 0.6, true, 0.3, 8.0, 180.0, Vector3(0, -9, 0), 0.4), v.center())
			Audio.play_at(&"shatter_ice", v.global_position, 2.0)

# ---- Weight ------------------------------------------------------------------------------------------------------

## Load >= 100%: no dodge rolls or steps (StatCalculator sets the flag).
func is_overburdened() -> bool:
	return stats != null and stats.has_flag(&"overburdened")

var _overburden_note_t := -10.0

func _overburden_notice() -> void:
	if _time - _overburden_note_t < 2.5:
		return
	_overburden_note_t = _time
	Events.notify.emit("Overburdened: too heavy to dodge. Drop or sell something.", &"error")
	Audio.play_ui(&"ui_error")

# ---- Throwables --------------------------------------------------------------------------------------------------

## Firebomb / Frost Flask: lobbed at the cursor (at most 12 m), bursting on landing.
func _throw_consumable(item: ItemInstance, spec: Dictionary) -> bool:
	if FX.world == null:
		return false
	var to := aim_point
	var flat := to - global_position
	flat.y = 0.0
	if flat.length() > 12.0:
		to = global_position + flat.normalized() * 12.0
	to = CombatQuery.ground_at(get_world_3d(), to)
	_face_aim_now()
	visual.play_action(&"cast_quick", 1.2)
	var from := global_position + Vector3.UP * 1.5 + forward() * 0.3
	var flight := clampf(from.distance_to(to) / 14.0, 0.35, 0.9)
	var body := ItemModels.instance(item.base, 1.4)
	var el := int(spec.get("element", Elements.FIRE))
	Lob.throw_node(FX.world, body, from, to, flight, Elements.color(el))
	Audio.play_at(&"swing_light", global_position, -2.0)
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = stats
	req.use_weapon = false
	var lv := float(hero.progress.level)
	var dmg := float(spec.get("base", 20.0)) + float(spec.get("per_level", 5.0)) * lv
	req.base_min = dmg * 0.85
	req.base_max = dmg * 1.15
	req.conversion = {el: 1.0}
	req.knockback = 5.0
	req.poise = 20.0
	req.evadable = false
	req.label = item.base.display_name
	var st := StringName(spec.get("status", &""))
	if st != &"":
		req.direct_status = {st: 120.0}
	var radius := float(spec.get("radius", 3.0))
	get_tree().create_timer(flight).timeout.connect(func() -> void:
		if not is_inside_tree():
			return
		AreaEffects.burst(self, to, radius, BH.LAYER_ENEMY, req, self)
		FX.spawn(VFXLib.ring_wave(Elements.color(el), radius, 0.4, 0.8), to)
		FX.spawn(VFXLib.particles(Elements.color(el), 40, 0.8, true, 0.45, 6.0, 180.0, Vector3(0, -4, 0), 0.5), to + Vector3.UP * 0.4)
		FX.spawn(VFXLib.light_flash(Elements.color(el), 6.0, radius * 2.0, 0.35), to + Vector3.UP)
		Audio.play_at(&"fire_explode" if el == Elements.FIRE else &"shatter_ice", to, 2.0)
		Events.camera_shake.emit(0.2))
	mark_combat()
	return true

# ---- Phoenix Feather ---------------------------------------------------------------------------------------------

## A killing blow burns a Phoenix Feather from the bag instead: rise at half HP with a short invulnerable flare.
func _try_phoenix() -> bool:
	if hero == null or hero.inventory.count_of(&"phoenix_feather") <= 0:
		return false
	hero.inventory.consume(&"phoenix_feather", 1)
	hp = max_hp() * 0.5
	health_changed.emit(hp, max_hp())
	status.cleanse([&"poisoned", &"burning", &"bleeding", &"cursed", &"chilled", &"slowed", &"weakened"])
	status.apply(&"fortified", 3.0, 0.0, 0.0, Elements.PHYSICAL, [StatModifier.more(&"damage_taken", -0.9)])
	FX.spawn(VFXLib.light_pillar(Color(1.0, 0.55, 0.15), 6.0, 1.2, 0.9), global_position)
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.6, 0.2, 0.95), 4.0, 0.6, 0.9), global_position)
	FX.spawn(VFXLib.particles(Color(1.0, 0.6, 0.15, 1.0), 60, 1.2, true, 0.4, 6.0, 60.0, Vector3(0, 3.0, 0), 0.6), global_position + Vector3.UP)
	Audio.play_at(&"fire_whoosh", global_position, 3.0)
	Audio.play_at(&"holy_chime", global_position, 0.0)
	Events.camera_shake.emit(0.3)
	Events.notify.emit("The Phoenix Feather burns — you rise again!", &"loot")
	return true

# ---- Death & respawn -------------------------------------------------------------------------------------------

func die(killer: Node) -> void:
	if not alive:
		return
	if _try_phoenix():
		return
	_cancel_action(false)
	super.die(killer)
	collision_layer = BH.LAYER_PLAYER
	dead_since = _time
	Audio.play_at(&"body_fall", global_position)
	player_died.emit()
	Events.player_died.emit()
	TownPortal.expire("Your Town Portal collapsed when you fell.")

func respawn() -> void:
	alive = true
	status.clear()
	collision_layer = BH.LAYER_PLAYER
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_ENEMY
	knock_velocity = Vector3.ZERO
	mark_stats_dirty()
	ensure_stats()
	hp = max_hp() * 0.6
	mana = max_mana() * 0.6
	health_changed.emit(hp, max_hp())
	mana_changed.emit(mana, max_mana())
	visual.revive()
	dead_since = -1.0
	_aura_t = 0.0

func on_teleported() -> void:
	_cancel_action(false)
	_leap = {}
	knock_velocity = Vector3.ZERO
	if camera:
		camera.clear_occlusion()
		camera.snap()

func _fell_out() -> void:
	# never lose the hero below the map: return to the current spawn with a small penalty
	if Game.current_map:
		Game.place_player(hero.current_spawn)
		hp = maxf(1.0, hp - max_hp() * 0.1)
		health_changed.emit(hp, max_hp())
