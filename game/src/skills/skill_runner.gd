class_name SkillRunner
extends RefCounted
## Executes active skills for a caster (the player). The one Skill Definition System: every skill is a SkillDef
## (data) whose `behavior` selects a parametric routine here; numbers come from `params` (+ ranks + upgrade nodes).
##
## Behaviours: melee_arc, dash_strike, leap, spin, buff, projectile, self_aoe, ground_aoe, chain, wave, blink,
## judgment. Timing: effects fire at the animation's hit window (weapon skills) or release frame (spells), taken from
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
	if caster.has_method(&"decorate_request"):
		caster.decorate_request(req, skill)
	return req

func _hit(skill: SkillDef, target: Actor, res: DamageResult) -> void:
	if caster.has_method(&"on_skill_hit"):
		caster.on_skill_hit(skill, target, res)

## Configure `action` so the skill's effects fire at the right moments. Returns false if the skill cannot start now.
func setup(skill: SkillDef, p: Dictionary, action: TimedAction) -> bool:
	var aim: Vector3 = caster.aim_point
	var dir: Vector3 = caster.aim_dir()
	action.data["skill"] = skill.id
	action.data["hits"] = {}
	match skill.behavior:
		&"melee_arc":
			action.on_window = func(w: int, first: bool) -> void:
				if first:
					_arc(skill, p, action)
		&"dash_strike":
			var dist := float(p.get("dash", 4.0))
			var t_hit := maxf(0.08, action.first_hit_time())
			caster.dash(dir, dist / t_hit, t_hit)
			action.on_window = func(w: int, first: bool) -> void:
				_front_strike(skill, p, action)
		&"leap":
			var target := _leap_target(aim, float(p.get("range", 10.0)))
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
		_:
			push_warning("Unknown skill behaviour %s" % skill.behavior)
			return false
	return true

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
	for a: Actor in CombatQuery.actors_in_arc(caster.get_world_3d(), caster.global_position, f, reach, arc, mask()):
		if not action.mark_hit(0, a):
			continue
		var r := req.clone()
		r.tags[&"push_dir"] = (a.global_position - caster.global_position).slide(Vector3.UP).normalized()
		_hit(skill, a, a.receive_hit(r, caster, a.center()))
	if caster.stats.has_flag(&"cleave_wave") and skill.id == &"cleave":
		var wreq := make_request(skill, p)
		wreq.weapon_mult *= caster.stats.flag(&"cleave_wave")
		wreq.conversion = {Elements.LIGHT: 1.0}
		var sw := AreaEffects.sweep(parent(), caster.global_position + f * 1.0, f, 16.0, 9.0, 2.6, wreq, caster, mask())
		sw.trail_fx = func(pos: Vector3) -> void:
			FX.spawn_facing(VFXLib.slash_arc(Color(0.6, 0.95, 1.0, 0.8), 1.6, 120.0, 0.6, 0.2, 0.5), pos, f)
	Audio.play_at(skill.sound_hit if skill.sound_hit != &"" else &"swing_heavy", caster.global_position)

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
			Events.camera_shake.emit(0.3)
		&"iron_bulwark":
			caster.status.apply(&"bulwark", dur, 1.0, 0.0, Elements.PHYSICAL,
				[StatModifier.flat(&"block_chance", float(p.block) / 100.0 * eff, "Iron Bulwark"),
				StatModifier.flat(&"knockback_res", float(p.kb_res) / 100.0 * eff, "Iron Bulwark")])
			FX.spawn(VFXLib.ring_wave(Color(0.75, 0.8, 0.95, 0.9), 2.5, 0.4), caster.global_position)
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
	var dir: Vector3 = caster.aim_dir()
	var from: Vector3 = caster.cast_point()
	var req := make_request(skill, p)
	if p.has("ignite"):
		req.direct_status[&"burning"] = float(p.ignite)
	for i in count:
		var ang := 0.0 if count == 1 else lerpf(-spread, spread, float(i) / float(count - 1))
		var d := dir.rotated(Vector3.UP, deg_to_rad(ang))
		var speed := float(p.get("speed", 24.0)) * (1.0 + caster.stats.get_stat(&"projectile_speed"))
		var look := "orb"
		var pr := Projectile.spawn(parent(), from, d, speed, req, caster, mask(), skill.element, look)
		pr.max_range = float(p.get("range", 20.0))
		pr.pierce = int(p.get("pierce", 0.0))
		pr.radius = float(p.get("width", 0.35)) * 0.5 if p.has("width") else 0.35
		pr.explode_radius = float(p.get("explode_radius", 0.0))
		pr.hit_sound = skill.sound_hit
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
		req.more.append(["Arcane Surge charges", 1.0 + float(p.get("per_charge", 30.0)) / 100.0 * charges])
		caster.restore_mana(float(p.get("mana_per_charge", 0.0)) * charges)
	if float(p.get("pull", 0.0)) > 0.0:
		for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), at, radius * 1.4, mask()):
			var d := at - a.global_position
			d.y = 0.0
			a.apply_knockback(d.normalized(), clampf(d.length() * 2.5, 2.0, 14.0), caster.stats, caster)
	for h in AreaEffects.burst(caster, at, radius, mask(), req, caster):
		_hit(skill, h[0], h[1])
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
	Events.camera_shake.emit(0.2)
	Audio.play_at(skill.sound_cast, caster.global_position)

func _blink(skill: SkillDef, p: Dictionary, aim: Vector3) -> void:
	var origin: Vector3 = caster.global_position
	var d := aim - origin
	d.y = 0.0
	var dist := minf(d.length(), float(p.get("range", 9.0)))
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
	FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 0.92, 0.8, 0.7), radius, 300.0, 1.0, 0.25, 0.5), caster.global_position, caster.forward())

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
