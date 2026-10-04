class_name TranscendSkills
## The new behaviours of the Class Transcendence skills (DataTranscendenceSkills), run by SkillRunner like every other
## skill: damage goes through make_request / receive_hit, statuses through StatusController, movement through the
## caster's collision-safe dash / leap / teleport. Persistent areas are TranscendZone nodes in the map's world, so a map
## change frees them; they end early when their caster dies.
##
## Support effects reach other players' heroes through Net.send_support (status values, a capped heal share and a
## capped barrier); the owner's machine checks the skill id and clamps every number before applying them.

const BEHAVIOURS := [&"t_challenge", &"t_zone", &"t_mercy", &"t_mark_one", &"t_snareline", &"t_comet_step", &"t_constellation",
	&"t_mana_ward", &"t_spellweave", &"t_pact", &"t_afterimage"]

## Harmful ailments Oath of Mercy may lift, worst first.
const CLEANSE_ORDER := [&"stunned", &"silenced", &"rooted", &"webbed", &"feared", &"poisoned", &"burning", &"bleeding", &"cursed",
	&"hex_frailty", &"weakened", &"enfeebled", &"sundered", &"armor_broken", &"grievous", &"bloodcurse", &"purged", &"demoralized",
	&"dazzled", &"blinded", &"slowed", &"chilled", &"dazed", &"windswept"]

## Most damage taken a challenge can remove (Sovereign's Challenge at any rank).
const CHALLENGE_DR_CAP := 0.35
## A barrier from these skills never exceeds this share of the receiver's own Maximum HP.
const BARRIER_CAP := 0.25

## Run `cb` after `t` seconds on a Timer owned by `owner`: if the owner is freed first (death, map change), the timer
## goes with it and `cb` never runs (no callbacks on freed heroes or monsters). Respects the game's pause.
static func later(owner: Node, t: float, cb: Callable) -> void:
	if owner == null or not owner.is_inside_tree():
		return
	var tm := Timer.new()
	tm.one_shot = true
	tm.wait_time = maxf(0.01, t)
	tm.timeout.connect(func() -> void:
		cb.call()
		tm.queue_free())
	owner.add_child(tm)
	tm.start()

static func handles(behavior: StringName) -> bool:
	return BEHAVIOURS.has(behavior)

## Configure `action` for a t_* skill. False when it cannot start (no target ...).
static func setup(runner: SkillRunner, skill: SkillDef, p: Dictionary, action: TimedAction, aim: Vector3) -> bool:
	var caster := runner.caster
	match skill.behavior:
		&"t_challenge":
			action.on_release = func() -> void: _challenge(runner, skill, p)
		&"t_zone":
			var at: Vector3 = caster.global_position if float(p.get("at_feet", 0.0)) > 0.0 else runner._ground_target(aim, float(p.get("range", 12.0)))
			action.on_release = func() -> void: TranscendZone.open(runner, skill, p, at)
		&"t_mercy":
			action.on_release = func() -> void: _mercy(runner, skill, p)
		&"t_mark_one":
			var tgt := runner._step_target(aim, float(p.get("range", 24.0)))
			if tgt == null:
				Events.notify.emit("No visible enemy to mark", &"error")
				return false
			action.on_release = func() -> void: _mark_one(runner, skill, p, tgt)
		&"t_snareline":
			var dir: Vector3 = caster.aim_dir()
			action.on_release = func() -> void: SnareLine.lay(runner, skill, p, dir)
		&"t_comet_step":
			_comet_step(runner, skill, p, aim)
		&"t_constellation":
			var at_c := runner._ground_target(aim, float(p.get("range", 22.0)))
			at_c = _visible_point(runner, at_c)
			action.on_release = func() -> void: _constellation(runner, skill, p, at_c)
		&"t_mana_ward":
			action.on_release = func() -> void: _mana_ward(runner, skill, p)
		&"t_spellweave":
			action.on_release = func() -> void:
				caster.status.apply(&"spellweave", float(p.get("duration", 10.0)), clampf(float(p.get("weave_pct", 55.0)) / 100.0, 0.0, 0.7))
				FX.spawn(VFXLib.ring_wave(theme_color(skill), 2.4, 0.5, 0.6), caster.global_position)
				Audio.play_at(skill.sound_cast, caster.global_position)
		&"t_pact":
			action.on_release = func() -> void: _pact(runner, skill, p)
		&"t_afterimage":
			_afterimage(runner, skill, p, action)
		_:
			return false
	return true

static func theme_color(skill: SkillDef) -> Color:
	var th := ClassTranscendence.class_theme(skill.class_id)
	var c: Color = th.primary if (th.primary as Color).get_luminance() > 0.3 else th.accent
	return Color(c.r, c.g, c.b, 0.9)

## The nearest point toward `at` the caster can see (a rift or a star shower never lands behind a wall).
static func _visible_point(runner: SkillRunner, at: Vector3) -> Vector3:
	var caster := runner.caster
	var world: World3D = caster.get_world_3d()
	if not CombatQuery.blocked(world, caster.center(), at + Vector3.UP):
		return at
	return CombatQuery.ground_at(world, CombatQuery.reachable_point(world, caster.global_position, at))

# ---- Allies -------------------------------------------------------------------------------------------------------

## Allies of the caster within `radius` of `at`: [actor, net avatar or null]. The caster, their Tempos and their
## Quake Team on this machine, and other players' heroes (NetAvatars, reached through Net.send_support).
static func allies_near(caster: Actor, at: Vector3, radius: float) -> Array:
	var out := []
	var r2 := radius * radius
	if caster.alive and caster.global_position.distance_squared_to(at) <= r2:
		out.append(caster)
	var tree := caster.get_tree()
	for t in tree.get_nodes_in_group(&"tempo"):
		if t is Actor and t != caster and (t as Actor).alive and (t as Actor).team == caster.team and (t as Node3D).global_position.distance_squared_to(at) <= r2:
			out.append(t)
	if Net.is_active():
		for av in Net.avatars():
			if av is NetAvatar and av.alive and not av.arena_hostile() and not av.arena_fighter and av.global_position.distance_squared_to(at) <= r2:
				out.append(av)
	return out

## Give `a` a barrier of `amount` HP for `duration` s (never more than BARRIER_CAP of its own Maximum HP). Another
## player's hero gets it on its owner's machine.
static func give_barrier(a: Actor, amount: float, duration: float, skill: SkillDef) -> void:
	if a is NetAvatar:
		Net.send_support(a, skill.id, {"barrier_pct": amount / maxf(1.0, a.max_hp()), "time": duration})
		return
	amount = minf(amount, a.max_hp() * BARRIER_CAP)
	if amount <= 0.0:
		return
	if a.has_method(&"add_shield"):
		a.add_shield(amount, duration)
	else:
		a.shield_hp = maxf(a.shield_hp, amount)
		a.status.apply(&"shielded", duration)
		var who := a
		later(a, duration + 0.05, func() -> void:
			if not who.status.has(&"shielded"):
				who.shield_hp = 0.0)
	FX.spawn(VFXLib.shield_dome(Color(1.0, 0.92, 0.65, 0.45), 1.1, 0.4), a.global_position)

## The strength multiplier on barriers from the caster's talents (Merciful Oath, at most +25%).
static func barrier_mult(caster: Actor) -> float:
	return 1.0 + DataTranscendence.cap(&"gp_barrier", caster.stats.flag(&"gp_barrier")) if caster.stats else 1.0

# ---- Behaviours ---------------------------------------------------------------------------------------------------

static func _challenge(runner: SkillRunner, skill: SkillDef, p: Dictionary) -> void:
	var caster := runner.caster
	var world: World3D = caster.get_world_3d()
	var radius := float(p.get("radius", 7.0))
	var taunted := 0
	for a: Actor in CombatQuery.actors_in_radius(world, caster.global_position, radius, runner.mask()):
		if CombatQuery.blocked(world, caster.center(), a.center()):
			continue
		# bosses resist forced targeting; the caster still gets the protection
		if a.get(&"is_boss") == true or not a.has_method(&"taunt"):
			continue
		a.taunt(caster, float(p.get("taunt", 4.0)))
		taunted += 1
	var dr := clampf(float(p.get("dr", 20.0)) / 100.0, 0.0, CHALLENGE_DR_CAP)
	caster.status.apply(&"sovereign_challenge", float(p.get("duration", 5.0)), dr, 0.0, Elements.PHYSICAL,
		[StatModifier.more(&"damage_taken", -dr, skill.display_name)])
	if caster.get(&"resource") != null and caster.resource.kind == &"valor":
		caster.resource.gain(float(p.get("valor_gain", 12.0)), 1.0 + caster.stats.get_stat(&"valor_gain"))
	var c := theme_color(skill)
	FX.spawn(VFXLib.ring_wave(c, radius, 0.5, 0.8), caster.global_position)
	FX.spawn(VFXLib.light_flash(c, 4.0, radius, 0.3), caster.global_position + Vector3.UP)
	SkillFX.war_cry(caster, radius)
	Net.share_skill_fx("tring", caster.global_position, Vector3.ZERO, {"r": radius, "c": String(skill.class_id)})
	Events.camera_shake.emit(0.25)
	Audio.play_at(skill.sound_cast, caster.global_position)
	if taunted > 0:
		FX.text_popup(caster.center() + Vector3.UP * 0.9, "Challenge", c, 0.9)

static func _mercy(runner: SkillRunner, skill: SkillDef, p: Dictionary) -> void:
	var caster := runner.caster
	var radius := float(p.get("radius", 8.0))
	var amount := caster.max_hp() * float(p.get("barrier", 12.0)) / 100.0 * barrier_mult(caster) * (1.0 + caster.stats.get_stat(&"buff_effect"))
	var dur := float(p.get("duration", 6.0))
	for a in allies_near(caster, caster.global_position, radius):
		if a is NetAvatar:
			Net.send_support(a, skill.id, {"barrier_pct": amount / maxf(1.0, a.max_hp()), "time": dur, "cleanse": 1})
			continue
		cleanse_one(a)
		give_barrier(a, amount, dur, skill)
	var c := theme_color(skill)
	FX.spawn(VFXLib.ring_wave(c, radius, 0.6, 0.7), caster.global_position)
	FX.spawn(VFXLib.light_pillar(c, 5.0, 0.8, 0.6), caster.global_position)
	Net.share_skill_fx("tring", caster.global_position, Vector3.ZERO, {"r": radius, "c": String(skill.class_id)})
	Audio.play_at(skill.sound_cast, caster.global_position)

## Remove the worst harmful ailment `a` carries (one). Returns its id or &"".
static func cleanse_one(a: Actor) -> StringName:
	for id in CLEANSE_ORDER:
		if a.status.has(id):
			a.status.remove(id)
			FX.text_popup(a.center() + Vector3.UP * 0.7, "Cleansed", Color(1.0, 0.95, 0.75), 0.7)
			return id
	return &""

static func _mark_one(runner: SkillRunner, skill: SkillDef, p: Dictionary, tgt: Actor) -> void:
	var caster := runner.caster
	if not is_instance_valid(tgt) or not tgt.alive:
		return
	var mag := clampf(float(p.get("mark_pct", 12.0)) / 100.0, 0.0, 0.20)
	tgt.status.apply(&"quarry", float(p.get("duration", 10.0)), mag)
	tgt.set_meta(&"quarry_by", caster.get_instance_id())
	var c := theme_color(skill)
	FX.spawn(VFXLib.ring_wave(c, 1.6, 0.4, 0.6), tgt.global_position)
	FX.spawn(VFXLib.impact_flash(c, 1.0, 0.25, 5), tgt.center() + Vector3.UP * 0.8)
	Audio.play_at(skill.sound_cast, tgt.global_position)

static func _comet_step(runner: SkillRunner, skill: SkillDef, p: Dictionary, aim: Vector3) -> void:
	var caster := runner.caster
	var origin: Vector3 = caster.global_position
	var away := origin - aim
	away.y = 0.0
	if away.length() < 0.2:
		away = -caster.forward()
	var travel := minf(float(p.get("range", 7.0)), 10.0)
	var target := runner._leap_target(origin + away.normalized() * travel, travel)
	caster.leap_to(target, 0.42)
	caster.status.apply(&"comet_ready", float(p.get("window", 5.0)), clampf(float(p.get("bonus", 45.0)) / 100.0, 0.0, 0.8))
	var c := theme_color(skill)
	FX.spawn(VFXLib.particles(c, 24, 0.5, true, 0.4, 3.5, 180.0, Vector3.ZERO, 0.5), origin + Vector3.UP)
	FX.spawn(VFXLib.ring_wave(c, 1.8, 0.35), origin)
	Audio.play_at(&"dodge_roll", origin)

static func _constellation(runner: SkillRunner, skill: SkillDef, p: Dictionary, at: Vector3) -> void:
	var caster := runner.caster
	var n := clampi(int(p.get("impacts", 12.0)), 1, 30)
	var span := maxf(0.2, float(p.get("duration", 2.4)))
	var radius := float(p.get("radius", 5.0))
	var ir := float(p.get("impact_radius", 1.6))
	var cap := maxi(1, int(p.get("hit_cap", 3.0)))
	var req := runner.make_request(skill, p)
	req.tags[&"projectile"] = true
	var hits := {}
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(at) ^ Time.get_ticks_usec()
	var c := theme_color(skill)
	AreaEffects.delayed(runner.parent(), at, radius, span, null, null, 0, Color(c, 0.35))      # the area, drawn here
	Net.share_telegraph(at, radius, span, Color(c, 0.35), "circle", 0.0, caster)            # and for everyone else
	# the first star falls on the aimed point, the rest spread evenly over the area (a sunflower spiral, turned at random)
	var turn := rng.randf() * TAU
	for i in n:
		var ang := turn + float(i) * 2.39996
		var dist := sqrt(float(i) / float(n)) * radius
		var pt := CombatQuery.ground_at(caster.get_world_3d(), at + Vector3(cos(ang), 0, sin(ang)) * dist)
		later(caster, span * float(i) / float(n), func() -> void:
			if not caster.alive:
				return
			FX.spawn(VFXLib.beam_flash(Color(0.85, 0.9, 1.0), 8.0, 0.14, 0.3), pt)
			FX.spawn(VFXLib.ring_wave(c, ir, 0.3, 0.5), pt + Vector3.UP * 0.05)
			for a: Actor in CombatQuery.actors_in_radius(caster.get_world_3d(), pt, ir, runner.mask()):
				var k := a.get_instance_id()
				if int(hits.get(k, 0)) >= cap:
					continue
				hits[k] = int(hits.get(k, 0)) + 1
				var r := req.clone()
				r.tags[&"aoe"] = true
				r.graze = true
				r.evadable = false
				r.tags[&"push_dir"] = (a.global_position - pt).slide(Vector3.UP).normalized()
				runner._hit(skill, a, a.receive_hit(r, caster, a.center()))
			Audio.play_at(skill.sound_hit, pt, -6.0))
	Audio.play_at(skill.sound_cast, caster.global_position)

static func _mana_ward(runner: SkillRunner, skill: SkillDef, p: Dictionary) -> void:
	var caster := runner.caster
	# the Mana was paid when the skill started (Player._pay_skill); the ward is sized from what was actually paid
	var paid := float(caster.get_meta(&"last_paid_mana", 0.0)) if caster.has_meta(&"last_paid_mana") else 0.0
	var amount := minf(paid * float(p.get("per_mana", 3.0)) * barrier_mult(caster), caster.max_hp() * clampf(float(p.get("cap", 30.0)) / 100.0, 0.0, 0.40))
	if amount > 0.0 and caster.has_method(&"add_shield"):
		caster.add_shield(amount, float(p.get("duration", 8.0)))
	var c := theme_color(skill)
	FX.spawn(VFXLib.shield_dome(Color(c.r, c.g, c.b, 0.45), 1.3, 0.6), caster.global_position)
	FX.spawn(VFXLib.ring_wave(c, 2.5, 0.45), caster.global_position)
	Audio.play_at(skill.sound_cast, caster.global_position)

static func _pact(runner: SkillRunner, skill: SkillDef, p: Dictionary) -> void:
	var caster := runner.caster
	# never the last point of HP: the price can not kill or drop below 1
	var cost := minf(caster.hp * clampf(float(p.get("hp_cost", 12.0)) / 100.0, 0.0, 0.5), maxf(0.0, caster.hp - 1.0))
	if cost > 0.0:
		caster.hp = maxf(1.0, caster.hp - cost)
		caster.health_changed.emit(caster.hp, caster.max_hp())
	var dmg := clampf(float(p.get("dmg", 12.0)) / 100.0, 0.0, 0.25)
	caster.status.apply(&"sanguine_pact", float(p.get("duration", 8.0)), dmg, 0.0, Elements.PHYSICAL,
		[StatModifier.more(&"outgoing_damage", dmg, skill.display_name)])
	caster.set_meta(&"pact_heal", [clampf(float(p.get("heal_hit", 0.5)) / 100.0, 0.0, 0.01), clampf(float(p.get("heal_sec", 4.0)) / 100.0, 0.0, 0.05)])
	var c := theme_color(skill)
	FX.spawn(VFXLib.particles(c, 30, 0.6, true, 0.4, 3.0, 180.0, Vector3(0, 2, 0), 0.4), caster.global_position + Vector3.UP)
	FX.spawn(VFXLib.ring_wave(c, 2.0, 0.4), caster.global_position)
	FX.text_popup(caster.center() + Vector3.UP * 0.9, "-%d HP" % roundi(cost), c, 0.8)
	Audio.play_at(skill.sound_cast, caster.global_position)

static func _afterimage(runner: SkillRunner, skill: SkillDef, p: Dictionary, action: TimedAction) -> void:
	var caster := runner.caster
	var n := clampi(int(p.get("strikes", 5.0)), 1, 8)
	var span := maxf(0.2, float(p.get("span", 1.0)))
	var reach := float(p.get("reach", 4.5))
	var origin: Vector3 = caster.global_position
	var c := theme_color(skill)
	for i in n:
		later(caster, 0.12 + span * float(i) / float(n), func() -> void:
			if not caster.alive:
				return
			var world: World3D = caster.get_world_3d()
			var cands := CombatQuery.actors_in_radius(world, origin, reach, runner.mask())
			cands = cands.filter(func(a): return a.alive and not CombatQuery.blocked(world, origin + Vector3.UP, a.center()))
			var t := CombatQuery.nearest(cands, origin)
			if t == null:
				return
			var req := runner.make_request(skill, p)
			req.tags[&"proc"] = true          # afterimage hits never trigger Double Attack or other repeats
			req.heavy = false
			req.tags[&"push_dir"] = (t.global_position - origin).slide(Vector3.UP).normalized()
			runner._hit(skill, t, t.receive_hit(req, caster, t.center()))
			var f := (t.global_position - origin).slide(Vector3.UP).normalized()
			FX.spawn_facing(VFXLib.slash_arc(c, 2.2, 110.0, 1.0, 0.18, 0.45, i % 2 == 0), origin, f if f.length() > 0.1 else caster.forward())
			FX.spawn(VFXLib.particles(Color(c, 0.6), 12, 0.35, true, 0.3, 1.5, 180.0, Vector3.ZERO, 0.3), origin + Vector3.UP)
			Audio.play_at(skill.sound_hit, t.global_position, -4.0))
	Audio.play_at(skill.sound_cast, caster.global_position)
