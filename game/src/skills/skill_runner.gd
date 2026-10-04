class_name SkillRunner
extends RefCounted
## Executes active skills for a caster (the player). The one Skill Definition System: every skill is a SkillDef
## (data) whose `behavior` selects a parametric routine here; numbers come from `params` (+ ranks + upgrade nodes).
##
## Behaviours: melee_arc, dash_strike, leap, spin, buff, projectile, self_aoe, ground_aoe, chain, wave, blink,
## judgment; (bh-010) flurry, spiral, storm, sentry, orb, trap, vault, shadow_step, veil, mark. Auras are toggled by
## the Player itself (Player.toggle_aura), not run here. Timing: effects fire at the animation's hit window (weapon skills) or release frame (spells), taken from
## the animation metadata and scaled by attack/cast speed.

var caster: Actor        # the Player (duck-typed helpers: aim_point, resource, hero, on_skill_hit, dash, leap_to ...)

func _init(p_caster: Actor) -> void:
	caster = p_caster

func mask() -> int:
	return BH.LAYER_ENEMY

func parent() -> Node:
	return FX.world if FX.world and is_instance_valid(FX.world) else caster.get_parent()

## Build the damage request of a skill hit.
func make_request(skill: SkillDef, p: Dictionary) -> DamageRequest:
	var req := DamageRequest.new()
	req.attacker = caster.stats
	req.kind = skill.kind
	req.label = skill.display_name
	if skill.kind == DamageRequest.Kind.ATTACK:
		req.use_weapon = true
		req.weapon_mult = float(p.get("weapon_pct", 100.0)) / 100.0
		req.heavy = true
		req.conversion = skill.conversion.duplicate()
	else:
		req.use_weapon = false
		req.base_min = float(p.get("damage_min", 0.0))
		req.base_max = float(p.get("damage_max", req.base_min))
		req.conversion = skill.conversion.duplicate() if not skill.conversion.is_empty() else {skill.element: 1.0}
		req.evadable = false
	req.knockback = float(p.get("knockback", 0.0))
	req.poise = float(p.get("poise", 0.0))
	req.status_power = float(p.get("status_power", 1.0))
	req.tags[&"skill"] = skill.id
	if p.has("launch"):
		req.tags[&"launch"] = float(p.launch)
	# bh-010: synergies, finishers (Combo), Focus shots, Spell Echo copies
	if float(p.get("syn_pct", 0.0)) > 0.0:
		req.bonus_inc += float(p.syn_pct) / 100.0
	if p.has("_pips"):
		var pips := float(p._pips)
		req.tags[&"finisher"] = true
		if float(p.get("pip_more", 0.0)) > 0.0:
			# Class Transcendence finishers: each pip is a share of more damage (see the Valor note below)
			req.more.append(["Combo x%d" % roundi(pips), 1.0 + float(p.pip_more) / 100.0 * pips])
		elif req.kind == DamageRequest.Kind.ATTACK:
			req.weapon_mult += float(p.get("per_pip", 0.0)) / 100.0 * pips
		else:
			req.more.append(["Combo x%d" % roundi(pips), 1.0 + float(p.get("per_pip", 0.0)) / 100.0 * pips])
		if bool(p.get("_poised", false)):
			req.force_crit = true
	if p.has("_focus"):
		var focus := float(p._focus)
		if float(p.get("focus_more", 0.0)) > 0.0:
			req.more.append(["Focus x%d" % roundi(focus), 1.0 + float(p.get("per_focus", 0.0)) / 100.0 * focus])
		else:
			req.weapon_mult += float(p.get("per_focus", 0.0)) / 100.0 * focus
		if focus >= float(p.get("crit_focus", 999.0)):
			req.force_crit = true
	if bool(p.get("_echo", false)):
		req.skill_mult *= float(p.get("echo_mult", 0.5))
		req.label = "%s (Echo)" % skill.display_name
	# Class Transcendence: Valor / Arcane Charge spent once at cast (_consume), extra penetration, Spellweave repeats
	# spent Valor is a multiplier of its own (weapon effectiveness above 200% has steep diminishing returns, so a
	# weapon bonus would barely register on these heavy blows)
	if p.has("_valor") and float(p._valor) > 0.0:
		req.more.append(["Valor x%d" % roundi(float(p._valor)), 1.0 + float(p.get("per_valor", 0.0)) / 100.0 * float(p._valor)])
	if p.has("_charges") and not bool(p.get("_weave", false)):
		var ch := float(p._charges)
		if ch > 0.0:
			req.more.append(["Arcane Charge spent x%d" % roundi(ch), 1.0 + float(p.get("per_charge", 0.0)) / 100.0 * ch])
	if float(p.get("pen_extra", 0.0)) > 0.0:
		req.pen_extra = clampf(float(p.pen_extra), 0.0, 0.5)
	if bool(p.get("_weave", false)):
		req.skill_mult *= clampf(float(p.get("_weave_mult", 0.55)), 0.0, 0.7)
		req.label = "%s (Spellweave)" % skill.display_name
	# a class signature weapon's bonus to one of its class's skills (DataTranscendenceGear; two copies at most +25%)
	if caster.stats and caster.stats.has_flag(StringName("tskill_dmg_" + String(skill.id))):
		req.more.append(["Signature weapon", 1.0 + minf(0.25, caster.stats.flag(StringName("tskill_dmg_" + String(skill.id))))])
	if req.tags.get(&"finisher", false) and caster.stats and caster.stats.has_flag(&"pr_finisher"):
		req.more.append(["Reaping Edge", 1.0 + DataTranscendence.cap(&"pr_finisher", caster.stats.flag(&"pr_finisher"))])
	if caster.has_method(&"decorate_request"):
		caster.decorate_request(req, skill)
	return req

func _hit(skill: SkillDef, target: Actor, res: DamageResult) -> void:
	# bh-030: a delayed blast or a stray bolt can land after its caster or its target is gone
	if not is_instance_valid(caster) or not is_instance_valid(target):
		return
	if res != null and not res.evaded and target != null and target.alive and not skill.on_hit_status.is_empty():
		_apply_statuses(skill, target, caster.skill_params(skill.id) if caster.has_method(&"skill_params") else skill.resolve(1))
	if caster.has_method(&"on_skill_hit"):
		caster.on_skill_hit(skill, target, res)

## Put the skill's on_hit_status on `target` ({status: [duration, magnitude]}; numbers or param names).
func _apply_statuses(skill: SkillDef, target: Actor, p: Dictionary) -> void:
	for sid in skill.on_hit_status:
		var spec: Array = skill.on_hit_status[sid]
		var dur := _num(spec[0], p) if spec.size() > 0 else -1.0
		var mag := _num(spec[1], p) if spec.size() > 1 else 0.0
		var mods: Array = []
		if sid == &"marked":
			mods = [StatModifier.more(&"damage_taken", mag / 100.0, skill.display_name)]
		target.status.apply(StringName(sid), dur, mag, 0.0, Elements.PHYSICAL, mods)

static func _num(v, p: Dictionary) -> float:
	if v is String or v is StringName:
		return float(p.get(String(v), 0.0))
	return float(v)

## Spend the class resource a finisher / focus shot consumes, once per cast (stored in `p` for make_request).
func _consume(p: Dictionary) -> void:
	var res = caster.get(&"resource")
	if res == null:
		return
	if float(p.get("consume_combo", 0.0)) > 0.0 and res.kind == &"combo":
		p["_poised"] = res.is_poised()
		p["_pips"] = res.spend_all()
	if float(p.get("consume_focus", 0.0)) > 0.0 and res.kind == &"focus":
		p["_focus"] = res.spend_all()
	if float(p.get("consume_valor", 0.0)) > 0.0 and res.kind == &"valor":
		p["_valor"] = res.spend_all()
		if caster.has_method(&"on_valor_spent"):
			caster.on_valor_spent(float(p._valor))
	if float(p.get("spend_charge", 0.0)) > 0.0 and res.kind == &"arcane":
		p["_charges"] = res.spend_all()
		if caster.has_method(&"on_charge_spent"):
			caster.on_charge_spent(float(p._charges))

## Configure `action` so the skill's effects fire at the right moments. Returns false if the skill cannot start now.
func setup(skill: SkillDef, p: Dictionary, action: TimedAction) -> bool:
	var aim: Vector3 = caster.aim_point
	var dir: Vector3 = caster.aim_dir()
	# Class Transcendence: an advanced class's skill runs only for a hero on that lineage (never a sibling master's or
	# another family's, whatever ranks were forged)
	var owner_hero = caster.get(&"hero")
	if owner_hero is HeroData and DataTranscendence.owner_of(skill.id) != &"" and not ClassTranscendence.skill_allowed(owner_hero, skill.id):
		return false
	if skill.behavior == &"ground_aoe" and float(p.get("visible", 0.0)) > 0.0:
		aim = TranscendSkills._visible_point(self, _ground_target(aim, float(p.get("range", 18.0))))
	action.data["skill"] = skill.id
	action.data["hits"] = {}
	_consume(p)
	match skill.behavior:
		&"gravity_pull", &"spike_tentacle", &"mana_siphon", &"dark_arts":
			action.on_release = func() -> void:
				ClassSpells.cast(self, skill, p, aim)
		&"melee_arc":
			action.on_window = func(w: int, first: bool) -> void:
				if first:
					_arc(skill, p, action)
		&"dash_strike":
			var dist := skill.movement_distance(p)
			var t_hit := maxf(0.08, action.first_hit_time())
			caster.dash(dir, dist / t_hit, t_hit)
			action.on_window = func(w: int, first: bool) -> void:
				_front_strike(skill, p, action)
		&"leap":
			var target := _leap_target(aim, skill.movement_distance(p))
			var t_land := maxf(0.2, action.first_hit_time())
			caster.leap_to(target, t_land)
			action.on_window = func(w: int, first: bool) -> void:
				if first:
					_leap_land(skill, p)
		&"buff":
			action.on_release = func() -> void:
				_buff(skill, p)
		&"projectile":
			action.on_release = func() -> void:
				_projectiles(skill, p)
		&"self_aoe":
			action.on_release = func() -> void:
				_self_aoe(skill, p)
		&"ground_aoe":
			var at := _ground_target(aim, float(p.get("range", 18.0)))
			action.on_release = func() -> void:
				_ground_aoe(skill, p, at)
		&"chain":
			action.on_release = func() -> void:
				_chain(skill, p, aim)
		&"wave":
			action.on_release = func() -> void:
				_wave(skill, p, caster.aim_dir())
			if skill.kind == DamageRequest.Kind.ATTACK and not action.windows.is_empty():
				action.on_release = Callable()
				action.on_window = func(w: int, first: bool) -> void:
					if first:
						_wave(skill, p, caster.aim_dir())
		&"blink":
			action.on_release = func() -> void:
				_blink(skill, p, aim)
		&"judgment":
			action.on_window = func(w: int, first: bool) -> void:
				if first:
					_judgment(skill, p)
		&"spin":
			pass   # channelled by the player (tick())
		&"flurry":
			_flurry(skill, p, action)
		&"spiral":
			action.on_release = func() -> void:
				_spiral(skill, p)
		&"storm":
			var at_s := _ground_target(aim, float(p.get("range", 18.0)))
			action.on_release = func() -> void:
				_storm(skill, p, at_s)
		&"sentry":
			var at_t: Vector3 = caster.global_position if float(p.get("at_feet", 0.0)) > 0.0 else _ground_target(aim, float(p.get("range", 10.0)))
			action.on_release = func() -> void:
				_sentry(skill, p, at_t)
		&"orb":
			action.on_release = func() -> void:
				_orb(skill, p)
		&"trap":
			var at_trap: Vector3 = caster.global_position if float(p.get("at_feet", 0.0)) > 0.0 else _ground_target(aim, float(p.get("range", 12.0)))
			action.on_release = func() -> void:
				_trap(skill, p, at_trap)
		&"vault":
			_vault(skill, p, aim, action)
		&"shadow_step":
			var tgt := _step_target(aim, skill.movement_distance(p))
			if tgt == null:
				Events.notify.emit("No enemy to step to", &"error")
				return false
			_shadow_step(tgt, skill.movement_distance(p))
			action.on_window = func(w: int, first: bool) -> void:
				if first:
					_arc(skill, p, action)
			if action.windows.is_empty():
				action.on_release = func() -> void:
					_arc(skill, p, action)
		&"veil":
			action.on_release = func() -> void:
				_veil(skill, p)
		&"mark":
			var at_m: Vector3 = caster.global_position if float(p.get("self", 0.0)) > 0.0 else _ground_target(aim, float(p.get("range", 16.0)))
			action.on_release = func() -> void:
				_mark(skill, p, at_m)
		_:
			if TranscendSkills.handles(skill.behavior):
				if not TranscendSkills.setup(self, skill, p, action, aim):
					return false
			else:
				push_warning("Unknown skill behaviour %s" % skill.behavior)
				return false
	# Clips without a release frame or hit window (Iron Bulwark's block_impact) would never fire on_release.
	if action.on_release.is_valid() and action.release_t < 0.0:
		action.release_t = minf(0.12, action.duration * 0.3)
	var unwrapped_release := action.on_release
	# Spell Echo (Mage passive): damaging spells may repeat themselves at half strength.
	if skill.kind == DamageRequest.Kind.SPELL and action.on_release.is_valid() and caster.stats.has_flag(&"spell_echo") \
			and skill.behavior in [&"projectile", &"ground_aoe", &"self_aoe", &"chain", &"wave", &"storm", &"orb"]:
		var first_release := action.on_release
		action.on_release = func() -> void:
			first_release.call()
			if randf() < caster.stats.flag(&"spell_echo"):
				caster.get_tree().create_timer(0.28, false).timeout.connect(func() -> void:
					if not is_instance_valid(caster) or not caster.alive:
						return
					p["_echo"] = true
					first_release.call()
					p.erase("_echo")
					FX.text_popup(caster.center() + Vector3.UP * 1.0, "Echo", Color(0.75, 0.6, 1.0), 0.8))
	# Spellweave (Archmage): the next paid damaging spell repeats once, weaker. The repeat runs the raw release (no Echo),
	# costs and refunds nothing, and cannot weave again.
	if skill.kind == DamageRequest.Kind.SPELL and unwrapped_release.is_valid() and caster.status.has(&"spellweave") \
			and skill.behavior in WEAVE_BEHAVIOURS and skill.mana_cost > 0.0:
		var weave_mult := caster.status.magnitude(&"spellweave", 0.55)
		caster.status.remove(&"spellweave")
		var raw_release := unwrapped_release
		var woven := action.on_release
		action.on_release = func() -> void:
			woven.call()
			TranscendSkills.later(caster, 0.35, func() -> void:
				if not caster.alive:
					return
				p["_weave"] = true
				p["_weave_mult"] = weave_mult
				raw_release.call()
				p.erase("_weave")
				FX.text_popup(caster.center() + Vector3.UP * 1.0, "Spellweave", Color(0.6, 0.8, 1.0), 0.8))
	# a short buff on the caster as the skill starts (Warbound Advance, Gloom Veil, Phantom Crossing)
	if p.has("self_status") and p.has("self_mods"):
		var mods: Array = []
		for m in p.self_mods:
			mods.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, float(m[2]), skill.display_name))
		caster.status.apply(StringName(p.self_status), float(p.get("self_dur", 2.0)), 1.0, 0.0, Elements.PHYSICAL, mods)
	return true

## Spells a Spellweave can repeat: one-shot damage (persistent areas, sentries and buffs would only replace themselves).
const WEAVE_BEHAVIOURS := [&"projectile", &"ground_aoe", &"self_aoe", &"chain", &"wave", &"orb", &"gravity_pull", &"spike_tentacle", &"dark_arts"]

# ---- Behaviours ---------------------------------------------------------------------------------------------

func _arc(skill: SkillDef, p: Dictionary, action: TimedAction) -> void:
	var reach := float(p.get("range", 3.0))
	var arc := float(p.get("arc", 150.0))
	var req := make_request(skill, p)
	if p.has("bleed"):
		req.direct_status[&"bleeding"] = float(p.bleed)
	var f: Vector3 = caster.forward()
	var c := _elem_color(skill)
	FX.spawn_facing(VFXLib.slash_arc(c, reach, arc, 1.0, 0.24, 0.6), caster.global_position, f)
	if skill.id == &"cleave":
		SkillFX.cleave(caster, f, reach, arc)
	var victims: Array = CombatQuery.actors_in_arc(caster.get_world_3d(), caster.global_position, f, reach, arc, mask())
	if float(p.get("max_targets", 0.0)) > 0.0:
		victims.sort_custom(func(x, y): return x.global_position.distance_squared_to(caster.global_position) < y.global_position.distance_squared_to(caster.global_position))
		victims = victims.slice(0, int(p.max_targets))
	var secondary := float(p.get("secondary_mult", 1.0))
	if secondary < 1.0:
		victims.sort_custom(func(x, y): return x.global_position.distance_squared_to(caster.global_position) < y.global_position.distance_squared_to(caster.global_position))
	var n_hit := 0
	for a: Actor in victims:
		if not action.mark_hit(0, a):
			continue
		var r := req.clone()
		r.tags[&"push_dir"] = (a.global_position - caster.global_position).slide(Vector3.UP).normalized()
		if n_hit > 0 and secondary < 1.0:
			r.skill_mult *= secondary
		target_bonuses(r, a, p)
		n_hit += 1
		_hit(skill, a, a.receive_hit(r, caster, a.center()))
	if caster.stats.has_flag(&"cleave_wave") and skill.id == &"cleave":
		var wreq := make_request(skill, p)
		wreq.weapon_mult *= caster.stats.flag(&"cleave_wave")
		wreq.conversion = {Elements.LIGHT: 1.0}
		var sw := AreaEffects.sweep(parent(), caster.global_position + f * 1.0, f, 16.0, 9.0, 2.6, wreq, caster, mask())
		sw.trail_fx = func(pos: Vector3) -> void:
			FX.spawn_facing(VFXLib.slash_arc(Color(0.6, 0.95, 1.0, 0.8), 1.6, 120.0, 0.6, 0.2, 0.5), pos, f)
	Audio.play_at(skill.sound_hit if skill.sound_hit != &"" else &"swing_heavy", caster.global_position)

## Class Transcendence bonuses that depend on the target: Marked (or Quarry-marked) and Bleeding enemies.
func target_bonuses(r: DamageRequest, a: Actor, p: Dictionary) -> void:
	if float(p.get("vs_marked_pct", 0.0)) > 0.0 and (a.status.has(&"marked") or a.status.has(&"quarry")):
		r.more.append(["Marked", 1.0 + float(p.vs_marked_pct) / 100.0])
	if float(p.get("vs_bleeding_pct", 0.0)) > 0.0 and a.status.has(&"bleeding"):
		r.more.append(["Bleeding", 1.0 + float(p.vs_bleeding_pct) / 100.0])

func _front_strike(skill: SkillDef, p: Dictionary, action: TimedAction) -> void:
	var radius := float(p.get("radius", 1.6))
	var center: Vector3 = caster.global_position + caster.forward() * (radius * 0.8)
	var req := make_request(skill, p)
	var has_shield: bool = caster.stats.loadout.has_shield
	var stun := float(p.get("stun", 0.0)) * (1.0 if has_shield else 0.5)
	if stun > 0.0:
		req.direct_status[&"stunned"] = stun
	for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), center, radius, mask()):
		if not action.mark_hit(0, a):
			continue
		var r := req.clone()
		r.tags[&"push_dir"] = caster.forward()
		var res := a.receive_hit(r, caster, a.center())
		_hit(skill, a, res)
		caster.stop_dash()
		FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.5, 0.9), 2.2, 0.3), a.global_position)
		if not action.data.get("bash_fx", false):
			action.data["bash_fx"] = true
			SkillFX.shield_bash(caster, a.center() - caster.forward() * a.body_radius)
		Events.camera_shake.emit(0.25)

func _leap_target(aim: Vector3, rng_m: float) -> Vector3:
	var from: Vector3 = caster.global_position
	var to := aim
	var d := to - from
	d.y = 0.0
	if d.length() > rng_m:
		to = from + d.normalized() * rng_m
	to = CombatQuery.reachable_point(caster.get_world_3d(), from, to)
	return CombatQuery.ground_at(caster.get_world_3d(), to)

func _ground_target(aim: Vector3, rng_m: float) -> Vector3:
	var from: Vector3 = caster.global_position
	var d := aim - from
	d.y = 0.0
	var to := aim
	if d.length() > rng_m:
		to = from + d.normalized() * rng_m
	return CombatQuery.ground_at(caster.get_world_3d(), to)

func _leap_land(skill: SkillDef, p: Dictionary) -> void:
	var radius := float(p.get("radius", 3.5))
	var at: Vector3 = caster.global_position
	var req := make_request(skill, p)
	for h in AreaEffects.burst(caster, at, radius, mask(), req, caster):
		_hit(skill, h[0], h[1])
	FX.spawn(VFXLib.ring_wave(Color(0.85, 0.6, 0.3, 0.9), radius, 0.5, 0.6), at)
	FX.spawn(VFXLib.dust_puff(1.4), at)
	FX.spawn(VFXLib.debris(1.3), at + Vector3.UP * 0.3)
	Events.camera_shake.emit(0.45)
	Events.impact.emit(at, 16.0, &"earth")
	SkillFX.leap_land(caster, at, radius)
	Audio.play_at(skill.sound_hit, at, 2.0)

func _buff(skill: SkillDef, p: Dictionary) -> void:
	var dur := float(p.get("duration", 8.0)) * (1.0 + caster.stats.get_stat(&"buff_effect"))
	var eff := 1.0 + caster.stats.get_stat(&"buff_effect")
	match skill.id:
		&"war_cry":
			caster.status.apply(&"war_cry", dur, 1.0, 0.0, Elements.PHYSICAL,
				[StatModifier.inc(&"defense", float(p.defense_inc) / 100.0 * eff, "War Cry"), StatModifier.inc(&"valor_gain", float(p.valor_inc) / 100.0 * eff, "War Cry")])
			if float(p.get("haste", 0.0)) > 0.0:
				caster.status.apply(&"haste", dur)
			var req := make_request(skill, p)
			req.base_min = 0.0
			req.base_max = 0.0
			req.use_weapon = false
			req.kind = DamageRequest.Kind.SPELL
			req.conversion = {Elements.PHYSICAL: 1.0}
			for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), caster.global_position, float(p.get("radius", 6.0)), mask()):
				var r := req.clone()
				a.receive_hit(r, caster, a.center())
			FX.spawn(VFXLib.ring_wave(Color(1.0, 0.55, 0.25, 0.9), float(p.get("radius", 6.0)), 0.5, 0.8), caster.global_position)
			SkillFX.war_cry(caster, float(p.get("radius", 6.0)))
			Events.camera_shake.emit(0.3)
		&"iron_bulwark":
			caster.status.apply(&"bulwark", dur, 1.0, 0.0, Elements.PHYSICAL,
				[StatModifier.flat(&"block_chance", float(p.block) / 100.0 * eff, "Iron Bulwark"),
				StatModifier.flat(&"knockback_res", float(p.kb_res) / 100.0 * eff, "Iron Bulwark")])
			FX.spawn(VFXLib.ring_wave(Color(0.75, 0.8, 0.95, 0.9), 2.5, 0.4), caster.global_position)
			SkillFX.bulwark(caster)
		&"radiant_ward":
			var mx: float = caster.max_hp()
			caster.add_shield(mx * float(p.absorb) / 100.0 * eff, dur)
			caster.heal(mx * float(p.heal) / 100.0 * (1.0 + caster.stats.get_stat(&"healing")))
			FX.spawn(VFXLib.ring_wave(Color(1.0, 0.95, 0.6, 0.9), float(p.get("radius", 4.0)), 0.6, 0.6), caster.global_position)
		_:
			# Generic data-driven buff: {"status": id, "mods": [[stat, op, value], ...]}
			var sid := StringName(p.get("status", String(skill.id)))
			var mods: Array = []
			for m in p.get("mods", []):
				mods.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, float(m[2]) * eff, skill.display_name))
			caster.status.apply(sid, dur, 1.0, 0.0, Elements.PHYSICAL, mods)
			if p.has("heal"):
				caster.heal(caster.max_hp() * float(p.heal) / 100.0 * (1.0 + caster.stats.get_stat(&"healing")))
			FX.spawn(VFXLib.ring_wave(_elem_color(skill), 3.0, 0.5), caster.global_position)
	Audio.play_at(skill.sound_cast, caster.global_position)

func _projectiles(skill: SkillDef, p: Dictionary) -> void:
	var count := int(p.get("count", 1.0))
	var spread := float(p.get("spread", 10.0))
	if skill.id == &"firebolt" and (caster.stats.has_flag(&"firebolt_split") or (caster.resource != null and caster.resource.value >= float(p.get("charge_split", 99.0)))):
		count = maxi(count, 3)
		spread = maxf(spread, 14.0)
	var dir: Vector3 = caster.projectile_dir() if caster.has_method(&"projectile_dir") else caster.aim_dir()
	var from: Vector3 = caster.cast_point()
	var req := make_request(skill, p)
	req.tags[&"projectile"] = true
	if caster.has_method(&"take_comet"):
		var comet: float = caster.take_comet()
		if comet > 0.0:
			req.more.append(["Comet Step", 1.0 + comet])
	var volley = {} if float(p.get("shared_hits", 0.0)) > 0.0 else null
	if float(p.get("patch_radius", 0.0)) > 0.0:
		_briar_patch(skill, p, _ground_target(caster.aim_point, float(p.get("range", 20.0))))
	if p.has("ignite"):
		req.direct_status[&"burning"] = float(p.ignite)
	var st_keys := {"chill": &"chilled", "bleed": &"bleeding", "poison": &"poisoned", "shock_buildup": &"shocked"}
	for st in st_keys:
		if p.has(st):
			req.direct_status[st_keys[st]] = float(p[st])
	var radial := float(p.get("radial", 0.0)) > 0.0
	var el := skill.element
	if not skill.conversion.is_empty():
		var best := -1.0
		for k in skill.conversion:
			if float(skill.conversion[k]) > best:
				best = float(skill.conversion[k])
				el = int(k)
	for i in count:
		var ang := 0.0 if count == 1 else lerpf(-spread, spread, float(i) / float(count - 1))
		if radial:
			ang = 360.0 * float(i) / float(count)
		var d := dir.rotated(Vector3.UP, deg_to_rad(ang))
		var speed := float(p.get("speed", 24.0)) * (1.0 + caster.stats.get_stat(&"projectile_speed"))
		var look := skill.projectile_look
		if look == "arrow" and caster.stats.loadout.main_type != null and caster.stats.loadout.main_type.id == &"crossbow":
			look = "bolt"
		var pr := Projectile.spawn(parent(), from, d, speed, req, caster, mask(), el, look)
		pr.max_range = float(p.get("range", 20.0))
		pr.pierce = int(p.get("pierce", 0.0))
		if caster.stats.has_flag(&"pierce_chance") and randf() < caster.stats.flag(&"pierce_chance"):
			pr.pierce += 1
		pr.radius = float(p.get("width", 0.35)) * 0.5 if p.has("width") else 0.35
		pr.explode_radius = float(p.get("explode_radius", 0.0))
		pr.hit_sound = skill.sound_hit
		if volley != null:
			pr.volley_hits = volley
		pr.pierce_falloff = clampf(float(p.get("pierce_falloff", 1.0)), 0.0, 1.0)
		pr.on_hit = func(a: Actor, res: DamageResult, pt: Vector3) -> void:
			_hit(skill, a, res)
		if pr.explode_radius > 0.0:
			pr.on_end = func(pt: Vector3, _w: bool) -> void:
				FX.spawn(VFXLib.ring_wave(_elem_color(skill), pr.explode_radius, 0.35), pt)
				FX.spawn(VFXLib.hit_burst(pt, skill.element, 0.9, false), pt)
				Audio.play_at(&"fire_explode", pt)
		if float(p.get("deflect", 0.0)) > 0.0:
			_deflect_path(from, d, pr.max_range, float(p.get("width", 1.6)))
	Audio.play_at(skill.sound_cast, from)

## Briar Volley: a slowing patch at the aim. It slows only (no damage), so overlapping patches never add damage.
func _briar_patch(skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var h := AreaEffects.hazard(parent(), at, float(p.get("patch_radius", 3.0)), float(p.get("patch_dur", 4.0)), null, caster, mask(),
		Color(0.4, 0.62, 0.32), 0.5)
	h.status_id = &"slowed"
	Net.share_skill_fx("tpatch", at, Vector3.ZERO, {"r": h.radius, "d": h.duration})

## Gale Burst destroys enemy projectiles along its path.
func _deflect_path(from: Vector3, dir: Vector3, length: float, width: float) -> void:
	for pr in caster.get_tree().get_nodes_in_group(&"projectile"):
		if not is_instance_valid(pr) or pr.source == caster or pr.target_mask != BH.LAYER_PLAYER:
			continue
		var to: Vector3 = pr.global_position - from
		to.y = 0.0
		var along := to.dot(dir)
		if along > 0.0 and along < length and absf(to.dot(dir.cross(Vector3.UP))) < width:
			pr.deflect()

func _self_aoe(skill: SkillDef, p: Dictionary) -> void:
	var radius := float(p.get("radius", 5.0))
	var at: Vector3 = caster.global_position
	var req := make_request(skill, p)
	if p.has("chill_direct"):
		req.direct_status[&"chilled"] = float(p.chill_direct)
	if float(p.get("consume_charge", 0.0)) > 0.0 and caster.resource != null:
		var charges: float = caster.resource.spend_all()
		if caster.has_method(&"on_charge_spent"):
			caster.on_charge_spent(charges)
		req.more.append(["Arcane Surge charges", 1.0 + float(p.get("per_charge", 30.0)) / 100.0 * charges])
		caster.restore_mana(float(p.get("mana_per_charge", 0.0)) * charges)
	if float(p.get("pull", 0.0)) > 0.0:
		for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), at, radius * 1.4, mask()):
			var d := at - a.global_position
			d.y = 0.0
			a.apply_knockback(d.normalized(), clampf(d.length() * 2.5, 2.0, 14.0), caster.stats, caster)
	var dealt := 0
	for h in AreaEffects.burst(caster, at, radius, mask(), req, caster, [], func(a: Actor, r: DamageRequest) -> void: target_bonuses(r, a, p)):
		_hit(skill, h[0], h[1])
		if h[1] != null and not (h[1] as DamageResult).evaded:
			dealt += (h[1] as DamageResult).total
	# Blood Eclipse: heal from the damage actually dealt, at most heal_cap of Maximum HP per cast
	if float(p.get("heal_from_damage", 0.0)) > 0.0 and dealt > 0:
		caster.heal(minf(float(dealt) * float(p.heal_from_damage), caster.max_hp() * clampf(float(p.get("heal_cap", 0.12)), 0.0, 0.25)))
	FX.spawn(VFXLib.ring_wave(_elem_color(skill), radius, 0.5, 0.9), at)
	FX.spawn(VFXLib.particles(_elem_color(skill), 40, 0.6, true, 0.5, 9.0, 90.0, Vector3.ZERO, 0.5), at + Vector3.UP * 0.6)
	FX.spawn(VFXLib.light_flash(_elem_color(skill), 4.0, radius * 1.5, 0.3), at + Vector3.UP)
	Events.camera_shake.emit(0.25)
	Audio.play_at(skill.sound_cast, at)

func _ground_aoe(skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var radius := float(p.get("radius", 4.0))
	var delay := float(p.get("delay", 0.8))
	var req := make_request(skill, p)
	if p.has("curse"):
		req.direct_status[&"cursed"] = float(p.curse)
	var blast := AreaEffects.delayed(parent(), at, radius, delay, req, caster, mask(), Color(_elem_color(skill), 0.65))
	var extra := int(p.get("extra_meteors", 0.0))
	blast.on_blast = func(pos: Vector3, hits: Array) -> void:
		for h in hits:
			_hit(skill, h[0], h[1])
		_ground_fx(skill, p, pos, radius)
		if float(p.get("sky_bolt", 0.0)) > 0.0:
			FX.spawn(VFXLib.lightning_bolt(pos + Vector3(0.6, 16.0, -0.4), pos + Vector3.UP * 0.2, Color(1.0, 0.95, 0.7), 0.3, 0.3), Vector3.ZERO)
			FX.spawn(VFXLib.light_pillar(Color(1.0, 0.92, 0.6), 10.0, radius * 0.6, 0.5), pos)
			Audio.play_at(&"thunder_strike", pos, 2.0)
		var bolts := int(p.get("radial_bolts", 0.0))
		if bolts > 0:
			var breq := req.clone()
			breq.skill_mult *= float(p.get("bolt_pct", 50.0)) / 100.0
			breq.tags[&"projectile"] = true
			for i in bolts:
				var d := Vector3.FORWARD.rotated(Vector3.UP, TAU * float(i) / float(bolts))
				var pr := Projectile.spawn(parent(), pos + Vector3.UP * 0.9, d, 18.0, breq.clone(), caster, mask(), Elements.LIGHT, "orb")
				pr.max_range = float(p.get("bolt_range", 9.0))
				pr.radius = 0.35
				pr.pierce = 99
				pr.on_hit = func(a: Actor, res: DamageResult, _pt: Vector3) -> void:
					_hit(skill, a, res)
	if skill.id == &"meteor":
		_meteor_fall(at, delay)
		for i in extra:
			var off := Vector3(cos(TAU * i / maxf(extra, 1)), 0, sin(TAU * i / maxf(extra, 1))) * (radius + 1.0)
			var sub := req.clone()
			sub.base_min *= 0.5
			sub.base_max *= 0.5
			var b2 := AreaEffects.delayed(parent(), at + off, radius * 0.6, delay + 0.35 + 0.2 * i, sub, caster, mask(), Color(_elem_color(skill), 0.5))
			b2.on_blast = func(pos: Vector3, hits: Array) -> void:
				for h in hits:
					_hit(skill, h[0], h[1])
				_ground_fx(skill, p, pos, radius * 0.6)
			_meteor_fall(at + off, delay + 0.35 + 0.2 * i)
	Audio.play_at(skill.sound_cast, caster.global_position)

func _meteor_fall(at: Vector3, delay: float) -> void:
	var rock := VFXLib.orb(Color(1.0, 0.45, 0.1), 0.6, true)
	parent().add_child(rock)
	rock.global_position = at + Vector3(-4, 18, 4)
	var tw := rock.create_tween()
	tw.tween_property(rock, "global_position", at, delay).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	tw.tween_callback(rock.queue_free)

func _ground_fx(skill: SkillDef, p: Dictionary, pos: Vector3, radius: float) -> void:
	var c := _elem_color(skill)
	FX.spawn(VFXLib.ring_wave(c, radius, 0.55, 0.9), pos)
	FX.spawn(VFXLib.particles(c, 36, 0.8, true, 0.6, 8.0, 70.0, Vector3(0, -6, 0), radius * 0.4), pos + Vector3.UP * 0.4)
	FX.spawn(VFXLib.light_flash(c, 6.0, radius * 2.0, 0.35), pos + Vector3.UP)
	if skill.id == &"meteor":
		FX.spawn(VFXLib.debris(1.4, Color(0.4, 0.3, 0.25)), pos + Vector3.UP * 0.3)
		Events.camera_shake.emit(0.5)
		Events.impact.emit(pos, 18.0, &"earth")
		if float(p.get("burn_ground", 0.0)) > 0.0:
			var breq := DamageRequest.new()
			breq.kind = DamageRequest.Kind.SPELL
			breq.attacker = caster.stats
			breq.base_min = float(p.damage_min) * 0.08
			breq.base_max = float(p.damage_max) * 0.08
			breq.conversion = {Elements.FIRE: 1.0}
			breq.can_crit = false
			breq.label = "Burning ground"
			AreaEffects.hazard(parent(), pos, radius * 0.8, float(p.burn_ground), breq, caster, mask(), Color(1.0, 0.4, 0.1))
	Audio.play_at(skill.sound_hit, pos, 2.0)

func _chain(skill: SkillDef, p: Dictionary, aim: Vector3) -> void:
	var chains := int(p.get("chains", 4.0)) + int(caster.stats.flag(&"conduit"))
	var rng_m := float(p.get("range", 18.0))
	var hop := float(p.get("chain_range", 8.0))
	var world: World3D = caster.get_world_3d()
	var candidates := CombatQuery.actors_in_radius(world, caster.global_position, rng_m, mask())
	candidates = candidates.filter(func(a): return not CombatQuery.blocked(world, caster.center(), a.center()))
	var first := CombatQuery.nearest(candidates, aim)
	var from_pt: Vector3 = caster.cast_point()
	if first == null:
		FX.spawn(VFXLib.lightning_bolt(from_pt, from_pt + caster.aim_dir() * minf(rng_m, from_pt.distance_to(aim))), Vector3.ZERO)
		return
	var hit := {}
	var cur: Actor = first
	var mult := 1.0
	var n := 0
	var req := make_request(skill, p)
	while cur != null and n <= chains:
		hit[cur.get_instance_id()] = true
		FX.spawn(VFXLib.lightning_bolt(from_pt, cur.center()), Vector3.ZERO)
		var r := req.clone()
		r.skill_mult *= mult
		var res := cur.receive_hit(r, caster, cur.center())
		_hit(skill, cur, res)
		if caster.stats.has_flag(&"wet_chains") and cur.status.has(&"wet") and n == 0:
			chains += int(caster.stats.flag(&"wet_chains"))
		from_pt = cur.center()
		mult *= 0.9
		n += 1
		var next: Actor = null
		var best := INF
		for a: Actor in CombatQuery.actors_in_radius(world, cur.global_position, hop, mask()):
			if hit.has(a.get_instance_id()):
				continue
			var dd := a.global_position.distance_squared_to(cur.global_position)
			if dd < best:
				best = dd
				next = a
		cur = next
	Audio.play_at(skill.sound_hit, first.global_position)

func _wave(skill: SkillDef, p: Dictionary, dir: Vector3) -> void:
	var count := int(p.get("count", 1.0))
	var req := make_request(skill, p)
	var c := _elem_color(skill)
	for i in count:
		var ang := 0.0 if count == 1 else lerpf(-20.0, 20.0, float(i) / float(count - 1))
		var d := dir.rotated(Vector3.UP, deg_to_rad(ang))
		var sw := AreaEffects.sweep(parent(), caster.global_position + d * 0.8, d, float(p.get("speed", 14.0)),
			float(p.get("length", 10.0)), float(p.get("width", 2.4)), req, caster, mask())
		sw.push_along = float(p.get("push_along", 0.0)) > 0.0
		sw.on_hit = func(a: Actor, res: DamageResult) -> void:
			_hit(skill, a, res)
		sw.trail_fx = func(pos: Vector3) -> void:
			if skill.element == Elements.WATER:
				FX.spawn(VFXLib.particles(Color(0.35, 0.6, 1.0, 0.85), 16, 0.5, true, 0.5, 5.0, 40.0, Vector3(0, -9, 0), 0.8), pos + Vector3.UP * 0.4)
			else:
				FX.spawn(VFXLib.debris(0.6, Color(0.5, 0.38, 0.25)), pos + Vector3.UP * 0.2)
				FX.spawn(VFXLib.dust_puff(0.5), pos)
		sw.trail_every = 1.0
	FX.spawn(VFXLib.ring_wave(c, 2.0, 0.3), caster.global_position)
	if skill.id == &"ground_fissure":
		SkillFX.fissure(caster, dir)
	Events.camera_shake.emit(0.2)
	Audio.play_at(skill.sound_cast, caster.global_position)

func _blink(skill: SkillDef, p: Dictionary, aim: Vector3) -> void:
	var origin: Vector3 = caster.global_position
	var d := aim - origin
	d.y = 0.0
	var dist := minf(d.length(), skill.movement_distance(p))
	var target := origin + (d.normalized() if d.length() > 0.1 else caster.forward()) * dist
	target = CombatQuery.reachable_point(caster.get_world_3d(), origin, target)
	target = CombatQuery.ground_at(caster.get_world_3d(), target)
	FX.spawn(VFXLib.particles(Color(0.6, 0.5, 1.0, 0.9), 30, 0.5, true, 0.4, 4.0, 180.0, Vector3.ZERO, 0.6), origin + Vector3.UP)
	caster.teleport_to(target)
	FX.spawn(VFXLib.particles(Color(0.6, 0.5, 1.0, 0.9), 30, 0.5, true, 0.4, 4.0, 180.0, Vector3.ZERO, 0.6), target + Vector3.UP)
	var req := make_request(skill, p)
	req.kind = DamageRequest.Kind.SPELL
	req.use_weapon = false
	req.base_min = 0.0
	req.base_max = 0.0
	req.conversion = {Elements.PHYSICAL: 1.0}
	AreaEffects.burst(caster, origin, float(p.get("radius", 2.5)), mask(), req, caster)
	FX.spawn(VFXLib.ring_wave(Color(0.6, 0.5, 1.0, 0.9), float(p.get("radius", 2.5)), 0.35), origin)
	if caster.stats.has_flag(&"blink_nova"):
		var nova := DB.skill(&"frost_nova")
		if nova:
			var np: Dictionary = caster.hero.resolved_skill(&"frost_nova") if caster.hero.skill_rank(&"frost_nova") > 0 else nova.resolve(1)
			var nreq := make_request(nova, np)
			nreq.direct_status[&"chilled"] = float(np.get("chill_direct", 60.0))
			AreaEffects.burst(caster, origin, float(np.get("radius", 5.0)), mask(), nreq, caster)
			FX.spawn(VFXLib.ring_wave(Elements.color(Elements.ICE), float(np.get("radius", 5.0)), 0.5, 0.9), origin)
	if caster.stats.has_flag(&"dodge_trail"):
		caster.lightning_trail(origin, target)
	Audio.play_at(skill.sound_cast, target)

func _judgment(skill: SkillDef, p: Dictionary) -> void:
	var valor := 0.0
	if caster.resource != null:
		valor = caster.resource.spend_all()
		if caster.has_method(&"on_valor_spent"):
			caster.on_valor_spent(valor)
	var req := make_request(skill, p)
	req.weapon_mult += float(p.get("per_valor", 3.0)) / 100.0 * valor
	var f: Vector3 = caster.forward()
	var length := float(p.get("length", 7.0))
	var width := float(p.get("width", 2.4))
	var total := 0
	for a: Actor in CombatQuery.actors_in_line(caster.get_world_3d(), caster.global_position, f, length, width, mask()):
		var r := req.clone()
		r.tags[&"push_dir"] = f
		var res := a.receive_hit(r, caster, a.center())
		total += res.total
		_hit(skill, a, res)
	if total > 0:
		caster.heal(total * float(p.get("heal_pct", 0.05)))
	var beam_pos: Vector3 = caster.global_position + f * length * 0.5
	for i in 6:
		FX.spawn(VFXLib.light_flash(Color(1.0, 0.92, 0.6), 3.0, 4.0, 0.4), caster.global_position + f * (length * float(i) / 5.0) + Vector3.UP)
		FX.spawn(VFXLib.particles(Color(1.0, 0.9, 0.55, 0.9), 12, 0.5, true, 0.5, 4.0, 60.0, Vector3(0, 3, 0), 0.4), caster.global_position + f * (length * float(i) / 5.0) + Vector3.UP * 0.3)
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.9, 0.55, 0.9), 3.0, 0.4), beam_pos)
	SkillFX.judgment(caster, f, length)
	Events.camera_shake.emit(0.45)
	Audio.play_at(skill.sound_hit, beam_pos, 2.0)

## Whirlwind-style channel tick (called by the player every `tick` seconds while channelling).
func spin_tick(skill: SkillDef, p: Dictionary) -> void:
	var radius := float(p.get("radius", 2.8))
	var req := make_request(skill, p)
	req.heavy = false
	var pull := float(p.get("pull", 0.0)) > 0.0
	for h in AreaEffects.burst(caster, caster.global_position, radius, mask(), req, caster, [], func(a: Actor, r: DamageRequest) -> void:
			if pull:
				r.tags[&"push_dir"] = (caster.global_position - a.global_position).slide(Vector3.UP).normalized()):
		_hit(skill, h[0], h[1])
	FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 0.92, 0.8, 0.7), radius, 300.0, 1.0, 0.25, 0.5), caster.global_position, caster.forward().rotated(Vector3.UP, randf() * TAU))

# ---- bh-010 behaviours ---------------------------------------------------------------------------------------

## Several quick strikes spread over the animation (Zeal, Twin Fang): each is a small arc hit.
func _flurry(skill: SkillDef, p: Dictionary, action: TimedAction) -> void:
	var n := maxi(1, int(p.get("strikes", 3.0)))
	var t0 := maxf(0.06, action.first_hit_time()) if not action.windows.is_empty() else maxf(0.06, action.duration * 0.25)
	var span := maxf(0.12, action.duration * 0.8 - t0)
	for i in n:
		var t := t0 + span * float(i) / float(maxi(1, n - 1)) if n > 1 else t0
		caster.get_tree().create_timer(t, false).timeout.connect(func() -> void:
			if not is_instance_valid(caster) or caster.get(&"action") != action:
				return
			_flurry_strike(skill, p, i))

func _flurry_strike(skill: SkillDef, p: Dictionary, i: int) -> void:
	var reach := float(p.get("range", 2.6))
	var arc := float(p.get("arc", 110.0))
	var req := make_request(skill, p)
	req.heavy = i == int(p.get("strikes", 3.0)) - 1
	if p.has("bleed"):
		req.direct_status[&"bleeding"] = float(p.bleed)
	if p.has("poison"):
		req.direct_status[&"poisoned"] = float(p.poison)
	var f: Vector3 = caster.forward()
	FX.spawn_facing(VFXLib.slash_arc(_elem_color(skill), reach, arc, 0.9 + 0.3 * (i % 2), 0.18, 0.45, i % 2 == 0), caster.global_position, f)
	var victims: Array = CombatQuery.actors_in_arc(caster.get_world_3d(), caster.global_position, f, reach, arc, mask())
	if float(p.get("max_targets", 0.0)) > 0.0:
		victims.sort_custom(func(x, y): return x.global_position.distance_squared_to(caster.global_position) < y.global_position.distance_squared_to(caster.global_position))
		victims = victims.slice(0, int(p.max_targets))
	for a: Actor in victims:
		var r := req.clone()
		r.tags[&"push_dir"] = (a.global_position - caster.global_position).slide(Vector3.UP).normalized()
		_hit(skill, a, a.receive_hit(r, caster, a.center()))
	Audio.play_at(&"swing_dagger" if skill.class_id == &"shadowblade" else &"swing_light", caster.global_position, -2.0)

## Hallowed Hammer: one (or more) hammers spiral outward from the Knight.
func _spiral(skill: SkillDef, p: Dictionary) -> void:
	var req := make_request(skill, p)
	var n := maxi(1, int(p.get("count", 1.0)))
	var base_a := atan2(caster.forward().z, caster.forward().x)
	for i in n:
		var h := SpiralHammer.create(parent(), caster.global_position, base_a + TAU * float(i) / float(n), req, caster, mask(), float(p.get("duration", 2.2)))
		h.growth = float(p.get("growth", 1.9))
		h.on_hit = func(a: Actor, res: DamageResult) -> void:
			_hit(skill, a, res)
		Net.share_skill_fx("spiral", caster.global_position, Vector3(cos(h.start_angle), 0, sin(h.start_angle)), {"d": h.duration, "g": h.growth})
	Audio.play_at(skill.sound_cast, caster.global_position)

## Blizzard / Arrow Rain: a persistent area at the target.
func _storm(skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var req := make_request(skill, p)
	if p.has("chill"):
		req.direct_status[&"chilled"] = float(p.chill)
	var style := "arrows" if skill.projectile_look == "arrow" else "ice"
	var s := StormArea.create(parent(), at, float(p.get("radius", 4.0)), float(p.get("duration", 3.0)), float(p.get("tick", 0.5)), req, caster, mask(), style)
	s.on_hit = func(a: Actor, res: DamageResult) -> void:
		_hit(skill, a, res)
	Net.share_skill_fx("storm", at, Vector3.ZERO, {"r": s.radius, "d": s.duration, "t": s.tick, "s": style})
	Audio.play_at(skill.sound_cast, at)

## Flame Sentinel (turret) / Blade Sentinel (spinning blades).
func _sentry(skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var req := make_request(skill, p)
	req.more.append(["Sentinel", 1.0 + caster.stats.get_stat(&"summon_damage")])
	if p.has("bleed"):
		req.direct_status[&"bleeding"] = float(p.bleed)
	if p.has("ignite"):
		req.direct_status[&"burning"] = float(p.ignite)
	var mode := "blades" if skill.class_id == &"shadowblade" else "turret"
	var el := skill.element
	if mode == "turret":
		req.tags[&"projectile"] = true
	else:
		req.more.append(["Trap mastery", 1.0 + caster.stats.get_stat(&"trap_damage")])
	var s := SkillSentry.create(parent(), at, mode, req, caster, mask(), float(p.get("duration", 8.0)), float(p.get("interval", 0.8)),
		float(p.get("reach", 14.0)), el, int(p.get("max_count", 1.0)))
	s.look = skill.projectile_look
	s.on_hit = func(a: Actor, res: DamageResult) -> void:
		_hit(skill, a, res)
	Net.share_skill_fx("sentry", at, Vector3.ZERO, {"m": mode, "l": s.lifetime, "i": s.interval, "r": s.reach, "e": el})
	Audio.play_at(skill.sound_cast, at)

## Frost Orb.
func _orb(skill: SkillDef, p: Dictionary) -> void:
	var req := make_request(skill, p)
	req.direct_status[&"chilled"] = float(p.get("chill", 20.0))
	var dir: Vector3 = caster.projectile_dir() if caster.has_method(&"projectile_dir") else caster.aim_dir()
	var o := FrostOrb.create(parent(), caster.cast_point(), dir, req, caster, mask(), float(p.get("range", 14.0)))
	o.on_hit = func(a: Actor, res: DamageResult) -> void:
		_hit(skill, a, res)
	Audio.play_at(skill.sound_cast, caster.global_position)

## Snare / Blast Trap.
func _trap(skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var req := make_request(skill, p)
	req.more.append(["Trap mastery", 1.0 + caster.stats.get_stat(&"trap_damage")])
	if p.has("ignite"):
		req.direct_status[&"burning"] = float(p.ignite)
	var style := "blast" if skill.element == Elements.FIRE or not skill.conversion.is_empty() else "snare"
	var max_n := int(p.get("max_traps", 3.0)) + int(caster.stats.flag(&"trap_max"))
	var t := SkillTrap.create(parent(), at, style, req, caster, mask(), float(p.get("radius", 2.5)), max_n)
	t.on_hit = func(a: Actor, res: DamageResult) -> void:
		_hit(skill, a, res)
	Net.share_skill_fx("trap", at, Vector3.ZERO, {"s": style, "r": t.radius})
	FX.spawn(VFXLib.ring_wave(Color(0.8, 0.95, 0.7, 0.7), 1.0, 0.3), at)

## Vault: leap away from the aim point (i-frames while airborne) and leave caltrops where you stood.
func _vault(skill: SkillDef, p: Dictionary, aim: Vector3, _action: TimedAction) -> void:
	var origin: Vector3 = caster.global_position
	var away := origin - aim
	away.y = 0.0
	if away.length() < 0.2:
		away = -caster.forward()
	var travel := skill.movement_distance(p)
	var target := _leap_target(origin + away.normalized() * travel, travel)
	caster.leap_to(target, 0.42)
	var req := make_request(skill, p)
	req.direct_status[&"slowed"] = 60.0
	req.label = "Caltrops"
	AreaEffects.hazard(parent(), origin, float(p.get("radius", 2.4)), float(p.get("duration", 4.0)), req, caster, mask(), Color(0.7, 0.65, 0.55), 0.5)
	FX.spawn(VFXLib.dust_puff(0.8), origin)
	Audio.play_at(&"dodge_roll", origin)

## The enemy nearest the aim point within `rng_m` of the caster.
func _step_target(aim: Vector3, rng_m: float) -> Actor:
	var world: World3D = caster.get_world_3d()
	var cands := CombatQuery.actors_in_radius(world, caster.global_position, rng_m, mask())
	cands = cands.filter(func(a): return a.alive and not CombatQuery.blocked(world, caster.center(), a.center()))
	return CombatQuery.nearest(cands, aim)

## Shadow Step: appear behind the target, facing it.
func _shadow_step(t: Actor, max_distance := 12.0) -> void:
	var origin: Vector3 = caster.global_position
	var behind: Vector3 = t.global_position - t.forward() * (t.body_radius + 0.9)
	var offset := (behind - origin).slide(Vector3.UP)
	behind = origin + offset.limit_length(minf(max_distance, float(SkillDef.MOVEMENT_LIMITS[&"shadow_step"])))
	behind = CombatQuery.reachable_point(caster.get_world_3d(), origin, behind)
	behind = CombatQuery.ground_at(caster.get_world_3d(), behind)
	FX.spawn(VFXLib.particles(Color(0.35, 0.2, 0.5, 0.9), 26, 0.5, true, 0.45, 3.0, 180.0, Vector3.ZERO, 0.5), origin + Vector3.UP)
	caster.teleport_to(behind)
	caster.face_toward(t.global_position)
	FX.spawn(VFXLib.particles(Color(0.35, 0.2, 0.5, 0.9), 26, 0.5, true, 0.45, 3.0, 180.0, Vector3.ZERO, 0.5), behind + Vector3.UP)
	Audio.play_at(&"blink", behind, -2.0)

## Smoke Veil: enemies around lose you and you slip into Stealth.
func _veil(_skill: SkillDef, p: Dictionary) -> void:
	var at: Vector3 = caster.global_position
	var radius := float(p.get("radius", 6.0))
	for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), at, radius, mask()):
		if a.has_method(&"lose_target"):
			a.lose_target(caster)
		if float(p.get("blind", 0.0)) > 0.0:
			a.status.apply(&"weakened", float(p.get("duration", 4.0)))
	caster.status.apply(&"stealth", float(p.get("duration", 4.0)))
	FX.spawn(VFXLib.particles(Color(0.35, 0.33, 0.38, 0.75), 70, 2.2, true, 1.6, 2.5, 180.0, Vector3(0, 0.4, 0), radius * 0.5, false), at + Vector3.UP * 0.6)
	FX.spawn(VFXLib.ring_wave(Color(0.5, 0.4, 0.65, 0.7), radius, 0.5), at)
	Net.share_skill_fx("veil", at, Vector3.ZERO, {"r": radius})
	Audio.play_at(&"shade_hiss", at)

## Hunter's Mark / Dread Mark: statuses on every enemy in an area, no damage.
func _mark(skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var radius := float(p.get("radius", 4.0))
	for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), at, radius, mask()):
		_apply_statuses(skill, a, p)
		FX.spawn(VFXLib.impact_flash(_elem_color(skill), 1.0, 0.25, 5), a.center() + Vector3.UP * 0.8)
	FX.spawn(VFXLib.ring_wave(_elem_color(skill), radius, 0.5, 0.6), at)
	FX.spawn(VFXLib.ground_crack(_elem_color(skill), radius * 0.8, 1.0), at)
	Net.share_telegraph(at, radius, 0.25, _elem_color(skill), "circle", 0.0, caster)
	Audio.play_at(skill.sound_cast, at)

func _elem_color(skill: SkillDef) -> Color:
	var e := skill.element
	if not skill.conversion.is_empty():
		var best := -1.0
		for k in skill.conversion:
			if float(skill.conversion[k]) > best:
				best = float(skill.conversion[k])
				e = int(k)
	if e == Elements.PHYSICAL:
		return Color(1.0, 0.92, 0.8, 0.9)
	var c := Elements.color(e)
	return Color(c.r, c.g, c.b, 0.9)
