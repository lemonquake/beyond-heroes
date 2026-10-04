class_name TranscendZone
extends Node3D
## A persistent area of a Class Transcendence skill (Bulwark Standard, Black Dominion, Sanctified Ground, Living Thicket,
## Warden's Refuge, Runic Circle, Prismatic Tempest, Event Horizon). It lives in the map's world (freed on a map change),
## pulses every `interval` seconds for `duration` seconds and ends early when its caster dies.
##
## Modes: hostile (damage pulses), ally (statuses / barriers on the caster and allies), both (damage and healing),
## self (a buff on the caster while inside). One zone per caster per skill: casting again replaces the old one.
## Stacking: allies inside several zones of the same skill (or several players' zones) get that skill's status once —
## re-applying refreshes it and keeps the stronger value; it never adds up. Barriers are given once per ally per cast;
## healing per ally is capped per cast; damage per enemy can be capped per cast (`hit_cap`).
## On other machines a zone is only drawn (no requests, no statuses): `visual_only`.

var caster: Actor
var runner: SkillRunner
var skill: SkillDef
var p: Dictionary = {}
var mode := "hostile"
var zone := ""
var radius := 4.0
var duration := 5.0
var interval := 0.5
var visual_only := false
var color := Color.WHITE
var _t := 0.0
var _tick := 0.0
var _pulse := 0
var _req: DamageRequest
var _hits := {}               # enemy instance id -> times struck this cast
var _rooted := {}             # enemy instance id -> true (thicket: first touch roots)
var _barriered := {}          # ally key -> true (refuge: one barrier per ally per cast)
var _healed := {}             # ally key -> share of Maximum HP healed this cast
var _decal: Node3D
var _spin: Node3D
var _ending := false

static var _live := {}        # "caster id:skill id" -> instance id of the live zone

const TEMPEST_ELEMENTS := [Elements.FIRE, Elements.WATER, Elements.LIGHTNING]

static func open(p_runner: SkillRunner, p_skill: SkillDef, params: Dictionary, at: Vector3) -> TranscendZone:
	var c := p_runner.caster
	var key := "%d:%s" % [c.get_instance_id(), p_skill.id]
	var old_id := int(_live.get(key, 0))
	if old_id != 0:
		var old := instance_from_id(old_id)
		if old != null and is_instance_valid(old) and old is TranscendZone:
			(old as TranscendZone).finish()
	var z := TranscendZone.new()
	Perf.mark_fx(z)
	z.caster = c
	z.runner = p_runner
	z.skill = p_skill
	z.p = params
	z.mode = String(params.get("mode", "hostile"))
	z.zone = String(params.get("zone", ""))
	z.radius = float(params.get("radius", 4.0))
	if p_skill.class_id == &"void_sovereign" and c.stats:
		z.radius *= 1.0 + DataTranscendence.cap(&"vs_area", c.stats.flag(&"vs_area"))
	z.duration = maxf(0.5, float(params.get("duration", 5.0)))
	z.interval = clampf(float(params.get("interval", 0.5)), 0.2, 2.0)
	z.color = TranscendSkills.theme_color(p_skill)
	p_runner.parent().add_child(z)
	z.global_position = at
	_live[key] = z.get_instance_id()
	z._build_visual()
	z._start()
	Net.share_skill_fx("tzone", at, Vector3.ZERO, {"z": z.zone, "r": z.radius, "d": z.duration, "c": String(p_skill.class_id)})
	Audio.play_at(p_skill.sound_cast, at)
	return z

## A harmless copy for another player's screen (Net._remote_skill_fx).
static func remote(parent: Node, at: Vector3, zone_kind: String, r: float, d: float, class_id: StringName) -> TranscendZone:
	var z := TranscendZone.new()
	Perf.mark_fx(z)
	z.visual_only = true
	z.zone = zone_kind
	z.radius = clampf(r, 0.5, 10.0)
	z.duration = clampf(d, 0.5, 15.0)
	var th := ClassTranscendence.class_theme(class_id)
	var col: Color = th.primary if (th.primary as Color).get_luminance() > 0.3 else th.accent
	z.color = Color(col.r, col.g, col.b, 0.9)
	parent.add_child(z)
	z.global_position = at
	z._build_visual()
	return z

func _build_visual() -> void:
	var fill := 0.32 if mode != "self" else 0.22
	_decal = VFXLib.telegraph("circle", Vector2(radius, radius), 0.01, Color(color.r, color.g, color.b, fill))
	add_child(_decal)
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = radius - 0.12
	tm.outer_radius = radius
	tm.rings = 48
	tm.ring_segments = 4
	ring.mesh = tm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(color.r, color.g, color.b, 0.75)
	ring.material_override = m
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	ring.scale = Vector3(1, 0.05, 1)
	ring.position.y = 0.06
	add_child(ring)
	_spin = ring
	match zone:
		"standard":
			# a banner pole: the standard the allies rally to
			var pole := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.05
			cm.bottom_radius = 0.06
			cm.height = 2.8
			pole.mesh = cm
			var pm := StandardMaterial3D.new()
			pm.albedo_color = Color(0.55, 0.45, 0.3)
			pole.material_override = pm
			pole.position.y = 1.4
			add_child(pole)
			var flag := MeshInstance3D.new()
			var qm := QuadMesh.new()
			qm.size = Vector2(0.9, 1.1)
			flag.mesh = qm
			var fm := StandardMaterial3D.new()
			fm.albedo_color = color
			fm.cull_mode = BaseMaterial3D.CULL_DISABLED
			fm.emission_enabled = true
			fm.emission = color
			fm.emission_energy_multiplier = 0.3
			flag.material_override = fm
			flag.position = Vector3(0.48, 2.2, 0)
			add_child(flag)
		"refuge", "runic":
			var dome := VFXLib.shield_dome(Color(color.r, color.g, color.b, 0.18 if zone == "refuge" else 0.1), radius, duration)
			add_child(dome)
	var parts := VFXLib.particles(Color(color.r, color.g, color.b, 0.7), int(8 + radius * 4), 1.0, false, 0.5, 1.0, 30.0, Vector3(0, 1.2, 0), radius * 0.8)
	parts.position.y = 0.2
	add_child(parts)

func _start() -> void:
	if zone == "dominion":
		# the landing strike: the Valor spent at cast strengthens this hit only, once
		var q := p.duplicate()
		q["weapon_pct"] = float(p.get("initial_pct", 180.0))
		var req := runner.make_request(skill, q)
		req.graze = true
		for h in AreaEffects.burst(caster, global_position, radius, runner.mask(), req, caster):
			runner._hit(skill, h[0], h[1])
		FX.spawn(VFXLib.ring_wave(color, radius, 0.5, 0.9), global_position)
		FX.spawn(VFXLib.light_pillar(color, 4.0, radius * 0.4, 0.5), global_position)
		Events.camera_shake.emit(0.3)
	if mode == "hostile" or mode == "both":
		var q2 := p.duplicate()
		q2.erase("_valor")
		_req = runner.make_request(skill, q2)
		if zone == "thicket" and caster.stats:
			_req.more.append(["Thorncraft", 1.0 + DataTranscendence.cap(&"ww_area", caster.stats.flag(&"ww_area"))])
	_tick = interval     # the first pulse comes at once

func finish() -> void:
	if _ending:
		return
	_ending = true
	set_physics_process(false)
	for c in get_children():
		if c is GPUParticles3D:
			c.emitting = false
	if _decal:
		var tw := _decal.create_tween()
		tw.tween_property(_decal, "scale", Vector3(0.01, 1, 0.01), 0.35)
	get_tree().create_timer(0.5).timeout.connect(queue_free)

func _process(delta: float) -> void:
	if _spin:
		_spin.rotation.y += delta * (1.4 if zone == "horizon" else 0.5)

func _physics_process(delta: float) -> void:
	if _ending or not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	if visual_only:
		if _t >= duration:
			finish()
		return
	if not is_instance_valid(caster) or not caster.alive or not caster.is_inside_tree():
		finish()
		return
	_tick += delta
	while _tick >= interval and not _ending:
		_tick -= interval
		_pulse_once()
	if _t >= duration:
		finish()

func _pulse_once() -> void:
	_pulse += 1
	match mode:
		"hostile":
			_hostile_pulse()
		"ally":
			_ally_pulse()
		"both":
			_hostile_pulse()
			_ally_pulse()
		"self":
			if caster.global_position.distance_to(global_position) <= radius:
				caster.status.apply(&"runic_circle", interval * 2.5, clampf(float(p.get("spell_pct", 15.0)) / 100.0, 0.0, 0.25))
	# Rootbound Guard: one bonus while standing in your own thicket or refuge
	if zone in ["thicket", "refuge"] and caster.stats and caster.stats.has_flag(&"ww_rootbound") \
			and caster.global_position.distance_to(global_position) <= radius:
		var v := DataTranscendence.cap(&"ww_rootbound", caster.stats.flag(&"ww_rootbound"))
		caster.status.apply(&"rootbound", interval * 2.5, v, 0.0, Elements.PHYSICAL, [StatModifier.more(&"defense", v, "Rootbound Guard")])

func _hostile_pulse() -> void:
	if _req == null:
		return
	var world := get_world_3d()
	var cap := int(p.get("hit_cap", 0.0))
	var req := _req
	if zone == "tempest":
		req = _req.clone()
		var el: int = TEMPEST_ELEMENTS[(_pulse - 1) % TEMPEST_ELEMENTS.size()]
		req.conversion = {el: 1.0}
		if el == Elements.FIRE:
			req.direct_status[&"burning"] = float(p.get("ignite", 40.0))
		FX.spawn(VFXLib.ring_wave(Elements.color(el), radius, 0.35, 0.5), global_position)
		if el == Elements.LIGHTNING:
			FX.spawn(VFXLib.lightning_bolt(global_position + Vector3(0.4, 12.0, -0.3), global_position + Vector3.UP * 0.2, Elements.color(el), 0.25, 0.25), Vector3.ZERO)
	for a: Actor in CombatQuery.actors_in_radius(world, global_position, radius, runner.mask()):
		if not a.alive or CombatQuery.blocked(world, global_position + Vector3.UP, a.center()):
			continue
		var k := a.get_instance_id()
		if cap > 0 and int(_hits.get(k, 0)) >= cap:
			continue
		_hits[k] = int(_hits.get(k, 0)) + 1
		if zone == "horizon":
			_pull(a)
		var r := req.clone()
		r.tags[&"aoe"] = true
		r.graze = true
		r.evadable = false
		r.blockable = false
		r.tags[&"push_dir"] = (a.global_position - global_position).slide(Vector3.UP).normalized()
		var res := a.receive_hit(r, caster, a.center())
		runner._hit(skill, a, res)
		if zone == "tempest" and r.conversion.has(Elements.WATER) and a.alive and not res.evaded:
			a.status.apply(&"wet", 3.0)
		if zone == "thicket" and a.alive and not res.evaded:
			if not _rooted.has(k):
				_rooted[k] = true
				root(a, float(p.get("root", 0.8)), caster)
			else:
				a.status.apply(&"slowed", interval * 2.5)

## Root `a` for `dur` seconds; bosses and root-immune enemies are slowed instead (Fieldcraft lengthens it, capped).
static func root(a: Actor, dur: float, by: Actor) -> void:
	if by != null and by.stats:
		dur *= 1.0 + DataTranscendence.cap(&"tr_trap_dur", by.stats.flag(&"tr_trap_dur"))
	if a.get(&"is_boss") == true or a.status.is_immune(&"rooted"):
		a.status.apply(&"slowed", dur * 1.5)
		return
	a.status.apply(&"rooted", dur)

## Event Horizon: pull toward the center, through the body's own collision (walls and terrain stop it), shortened by
## Knockback Resistance. Bosses are never pulled.
func _pull(a: Actor) -> void:
	if a.get(&"is_boss") == true:
		return
	a.ensure_stats()
	var offset := (a.global_position - global_position).slide(Vector3.UP)
	var dist := minf(maxf(0.0, offset.length() - a.body_radius - 0.6), float(p.get("pull", 1.6)))
	dist *= 1.0 - clampf(a.stats.get_stat(&"knockback_res"), 0.0, 1.0)
	if dist > 0.05:
		a.move_and_collide(-offset.normalized() * dist)

func _ally_pulse() -> void:
	var sid := skill.id
	var allies := TranscendSkills.allies_near(caster, global_position, radius)
	if zone == "standard" or zone == "refuge":
		var vals := []
		var mods: Array = []
		for m in skill.aura_mods:
			var v := float(p.get(String(m[2]), 0.0)) * float(m[3])
			vals.append(v)
			mods.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, v, skill.display_name))
		for a in allies:
			if a is NetAvatar:
				var extra := {"time": interval * 2.5, "vals": vals}
				if zone == "refuge" and not _barriered.has(a.name):
					_barriered[a.name] = true
					extra["barrier_pct"] = float(p.get("barrier", 10.0)) / 100.0 * TranscendSkills.barrier_mult(caster)
					extra["time_b"] = duration
				Net.send_support(a, sid, extra)
				continue
			(a as Actor).status.apply(sid, interval * 2.5, 1.0, 0.0, Elements.PHYSICAL, mods.duplicate())
			if zone == "refuge" and not _barriered.has(a.get_instance_id()):
				_barriered[a.get_instance_id()] = true
				TranscendSkills.give_barrier(a, a.max_hp() * float(p.get("barrier", 10.0)) / 100.0 * TranscendSkills.barrier_mult(caster), duration, skill)
	if zone == "sanctified":
		var share := clampf(float(p.get("heal_pct", 1.2)) / 100.0, 0.0, 0.03)
		var cap := clampf(float(p.get("heal_cap", 8.0)) / 100.0, 0.0, 0.15)
		var heal_mult := 1.0 + (caster.stats.get_stat(&"healing") if caster.stats else 0.0)
		for a in allies:
			var key: Variant = a.name if a is NetAvatar else a.get_instance_id()
			var done := float(_healed.get(key, 0.0))
			var give := minf(share * heal_mult, cap - done)
			if give <= 0.0:
				continue
			_healed[key] = done + give
			if a is NetAvatar:
				Net.send_support(a, sid, {"heal_pct": give, "time": 0.0})
			else:
				(a as Actor).heal((a as Actor).max_hp() * give)
		if _pulse % 2 == 1:
			FX.spawn(VFXLib.ring_wave(color, radius * 0.7, 0.5, 0.35), global_position)
