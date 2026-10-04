class_name ClassSignature
extends Node3D
## Signature traits of the advanced classes (DataTranscendence.SIGNATURES): one always-on mechanic per identity. A
## master keeps its first transcendence's trait, so a Grand Paladin has Royal Aegis and Dawnbringer.
##
## The hero's own machine runs the mechanics (Player calls the on_* hooks; every number is bounded in SIGNATURES and
## every proc is tagged so it cannot trigger itself or other procs). Other machines draw the bursts only: the owner
## shares a small event when one happens (Net.share_class_sig), and the receiver accepts it only when that player's
## validated class line includes the trait (Net._remote_class_sig).
##
## Look: no aura or icons on the hero. A trait shows itself only when it acts: a small particle spray where a Royal
## Retort, Dawnbringer, Collapse, Blood Price ... lands (VFXLib, the game's ordinary effects).

## Burst kinds -> the identity that owns them (also the network whitelist).
const KIND_OWNER := {
	&"crest": &"royal_guard", &"retort": &"royal_guard",
	&"dread": &"dark_general",
	&"sun": &"grand_paladin", &"dawn": &"grand_paladin",
	&"opening": &"tracker",
	&"roots": &"wildwarden",
	&"star": &"starstrider", &"shoot": &"starstrider",
	&"rune": &"arcanist",
	&"attune": &"archmage", &"abolt": &"archmage",
	&"collapse": &"void_sovereign",
	&"shade": &"nightstalker",
	&"soul": &"phantom_reaper",
	&"blood": &"blood_sovereign",
}
## True when a player whose current class is `class_id` may show the mark `kind` (the network check).
static func allowed(class_id: StringName, kind: StringName) -> bool:
	var owner_id: StringName = KIND_OWNER.get(kind, &"")
	return owner_id != &"" and DataTranscendence.ancestry(class_id).has(owner_id)

## Trait charges the hero's machine keeps (Royal Aegis crests, Dread, ...); they are not drawn.
const COUNTED := {&"crest": [3], &"dread": [5], &"sun": [5], &"star": [5], &"rune": [3], &"attune": [2], &"shade": [2]}
## Attunement order (Archmage).
const ATTUNE := [Elements.FIRE, Elements.ICE, Elements.LIGHTNING]
var actor: Actor
var ids: Array = []                 # identities whose trait this hero has (first transcendence, master)
var remote := false                 # another player's hero: marks only
var _counts := {}                   # kind -> drawn count

# local mechanics
var _time := 0.0
var _dawn_hits := 0
var _dawn_t := -99.0
var _collapse_t := -99.0
var _soul_t := -99.0
var _blood_t := -99.0
var _still := 0.0
var _attune := 0
var _attune_cast := -1
var _shadow_attack := -1

## Keep exactly the right signature node under `parent` for the class line `line` ([family, stage 1, master]).
static func sync(parent: Node3D, line: Array, is_remote: bool) -> ClassSignature:
	var want: Array = []
	for id in line:
		if DataTranscendence.SIGNATURES.has(StringName(id)):
			want.append(StringName(id))
	var old := parent.get_node_or_null(^"ClassSignature") as ClassSignature
	if old != null and old.ids == want and old.remote == is_remote:
		return old
	if old != null:
		parent.remove_child(old)
		old.queue_free()
	if want.is_empty():
		return null
	var s := ClassSignature.new()
	s.name = "ClassSignature"
	s.ids = want
	s.remote = is_remote
	s.actor = parent as Actor
	parent.add_child(s)
	return s

func has(id: StringName) -> bool:
	return ids.has(id)

func _ready() -> void:
	set_process(not remote)

func _process(delta: float) -> void:
	_time += delta
	_tick(delta)

## Kept for callers: the traits draw nothing on the hero, so there is nothing to fade.
func set_presence(_v: float) -> void:
	pass

# ---- Marks ------------------------------------------------------------------------------------------------------------

## Record the trait charge `kind` (a count, the attuned element for "attune", 0/1 for "roots"). Not drawn, not sent.
func show_count(kind: StringName, n: int) -> void:
	if KIND_OWNER.has(kind) and has(KIND_OWNER[kind]):
		_counts[kind] = n

func count(kind: StringName) -> int:
	return int(_counts.get(kind, 0))

## A one-off mark at a place (and, on the hero's machine, the same mark for everyone else). `at` and `to` are world
## positions: the burst's centre, and where a bolt or soul travels.
func burst(kind: StringName, at: Vector3, to := Vector3.ZERO) -> void:
	if not KIND_OWNER.has(kind) or not has(KIND_OWNER[kind]) or not at.is_finite() or not to.is_finite():
		return
	if FX.world == null:
		return
	var th := ClassTranscendence.class_theme(KIND_OWNER[kind])
	var c: Color = _bright(th.primary, th.accent)
	var c2: Color = Color(th.accent, 0.9)
	match kind:
		&"retort":
			var f := (to - at).slide(Vector3.UP).normalized()
			if f.length() < 0.1:
				f = Vector3.FORWARD
			FX.spawn(VFXLib.spark_spray(f, Color(c, 1.0), 26, 9.0, 35.0, 0.35, 0.4), at + Vector3.UP * 1.0 + f * 0.6)
			FX.spawn(VFXLib.particles(Color(c2, 0.8), 24, 0.5, true, 0.06, 4.0, 40.0, Vector3.ZERO, 0.4), at + Vector3.UP + f * 1.5)
			Audio.play_at(&"block", at, 2.0)
		&"dawn":
			var r := DataTranscendence.sig(&"grand_paladin", "radius")
			FX.spawn(VFXLib.particles(Color(c, 1.0), 48, 0.9, true, 0.07, r * 1.6, 90.0, Vector3(0, 1.2, 0), 0.4), at + Vector3.UP * 0.6)
			FX.spawn(VFXLib.particles(Color(1.0, 0.96, 0.8, 0.9), 20, 1.2, true, 0.06, 1.2, 15.0, Vector3(0, 2.0, 0), r * 0.5), at + Vector3.UP * 0.2)
			Audio.play_at(&"holy_chime", at, -2.0)
		&"opening":
			FX.spawn(VFXLib.particles(Color(c, 1.0), 24, 0.45, true, 0.05, 4.0, 180.0, Vector3.ZERO, 0.15), at)
			Audio.play_at(&"crit_hit", at, -6.0)
		&"shoot":
			FX.spawn(VFXLib.spark_spray((to - at).normalized(), Color(c, 1.0), 20, 12.0, 10.0, 0.4, 0.6), at)
			Audio.play_at(&"crit_hit", at, -3.0)
		&"abolt":
			var ec := Elements.color(ATTUNE[clampi(count(&"attune"), 0, 2)])
			FX.spawn(VFXLib.lightning_bolt(at, to, ec, 0.16, 0.06), Vector3.ZERO)
			FX.spawn(VFXLib.particles(Color(ec, 1.0), 16, 0.35, true, 0.05, 3.0, 180.0, Vector3.ZERO, 0.1), to)
		&"collapse":
			var r2 := DataTranscendence.sig(&"void_sovereign", "radius")
			var pc := VFXLib.particles(Color(c, 1.0), 40, 0.6, true, 0.08, 0.2, 180.0, Vector3.ZERO, r2 * 0.8)
			(pc.process_material as ParticleProcessMaterial).radial_accel_min = -14.0
			(pc.process_material as ParticleProcessMaterial).radial_accel_max = -10.0
			FX.spawn(pc, at + Vector3.UP * 0.9)
			Audio.play_at(&"dark_curse", at, -2.0)
		&"soul":
			_soul_travel(at, c, c2)
		&"blood":
			FX.spawn(VFXLib.particles(Color(c, 1.0), 36, 0.7, true, 0.05, 5.0, 70.0, Vector3(0, -9, 0), 0.3, false), at + Vector3.UP * 0.9)
			Audio.play_at(&"hit_flesh", at, 0.0)
	if not remote:
		Net.share_class_sig(String(kind), 0, at, to)

## Phantom Reaper: a pale soul (a small orb trailing mist) drifts from the fallen enemy into the hero.
func _soul_travel(from: Vector3, c: Color, c2: Color) -> void:
	var o := VFXLib.orb(Color(c, 0.9), 0.1, false)
	o.add_child(VFXLib.particles(Color(c, 0.7), 14, 0.5, false, 0.1, 0.1, 180.0, Vector3.ZERO, 0.05))
	FX.spawn(o, from + Vector3.UP * 1.0)
	var tw := o.create_tween()
	var dest := actor.global_position + Vector3.UP * 1.1 if is_instance_valid(actor) else from
	tw.tween_property(o, "global_position", dest, 0.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		if is_instance_valid(o):
			FX.spawn(VFXLib.particles(Color(c2, 0.8), 18, 0.4, true, 0.05, 2.5, 180.0, Vector3.ZERO, 0.2), dest)
			o.queue_free())

# ---- Mechanics (the hero's own machine) ----------------------------------------------------------------------------

func _player() -> Player:
	return actor as Player

func _stacks(id: StringName) -> int:
	return actor.status.stacks(id) if actor.status.has(id) else 0

## Every frame: Rooted Stance, and the drawn counts follow the statuses as they fade.
func _tick(delta: float) -> void:
	var p := _player()
	if p == null or p.stats == null:
		return
	if has(&"royal_guard"):
		show_count(&"crest", _stacks(&"royal_crest"))
	if has(&"dark_general"):
		show_count(&"dread", _stacks(&"dread"))
	if has(&"starstrider"):
		show_count(&"star", _stacks(&"star_chart"))
	if has(&"arcanist"):
		show_count(&"rune", _stacks(&"runescript"))
	if has(&"nightstalker"):
		show_count(&"shade", 2 if p.status.has(&"shadow_strike") else 0)
	if has(&"grand_paladin"):
		show_count(&"sun", _dawn_hits)
	if has(&"archmage"):
		show_count(&"attune", _attune)
	if has(&"wildwarden"):
		var moving := Vector2(p.velocity.x, p.velocity.z).length() > 0.35
		if p.alive and not moving and p.in_combat() and not p.is_dodging():
			_still += delta
		else:
			_still = 0.0
		var hold := _still >= DataTranscendence.sig(&"wildwarden", "delay")
		if hold != p.status.has(&"rooted_stance"):
			if hold:
				var d := DataTranscendence.sig(&"wildwarden", "def") / 100.0
				var kb := DataTranscendence.sig(&"wildwarden", "kb") / 100.0
				p.status.apply(&"rooted_stance", 0.0, 1.0, 0.0, Elements.PHYSICAL,
					[StatModifier.new(&"defense", StatModifier.Op.INC, d, "Rooted Stance"), StatModifier.flat(&"knockback_res", kb, "Rooted Stance")])
			else:
				p.status.remove(&"rooted_stance")
		show_count(&"roots", 1 if hold else 0)

## A block (Royal Aegis).
func on_block() -> void:
	if has(&"royal_guard"):
		actor.status.apply(&"royal_crest", DataTranscendence.sig(&"royal_guard", "fade"))

## A dodge (From the Shadows).
func on_dodge() -> void:
	if has(&"nightstalker"):
		actor.status.apply(&"shadow_strike", DataTranscendence.sig(&"nightstalker", "window"))

## A weapon attack's request (each hit window of a swing, or a shot). Decides once per attack which ready trait it
## spends, then adds the bonus to every request of that attack.
func weapon_request(req: DamageRequest, a: TimedAction, ranged: bool) -> void:
	var p := _player()
	if p == null or a == null:
		return
	if not a.data.has("sig"):
		var s := {}
		if has(&"royal_guard") and _stacks(&"royal_crest") >= int(DataTranscendence.sig(&"royal_guard", "max")):
			s["retort"] = true
			p.status.remove(&"royal_crest")
			_retort(req)
		if has(&"nightstalker") and p.status.has(&"shadow_strike"):
			s["shadow"] = true
			p.status.remove(&"shadow_strike")
		if ranged and has(&"starstrider") and _stacks(&"star_chart") >= int(DataTranscendence.sig(&"starstrider", "max")):
			s["shoot"] = true
			p.status.remove(&"star_chart")
		a.data["sig"] = s
	var on: Dictionary = a.data["sig"]
	if on.has("retort"):
		req.more.append(["Royal Retort", 1.0 + DataTranscendence.sig(&"royal_guard", "bonus") / 100.0])
	if on.has("shadow"):
		req.more.append(["From the Shadows", 1.0 + DataTranscendence.sig(&"nightstalker", "bonus") / 100.0])
		req.tags[&"sig_shadow"] = true
	if on.has("shoot"):
		req.more.append(["Shooting Star", 1.0 + DataTranscendence.sig(&"starstrider", "bonus") / 100.0])
		req.tags[&"sig_shoot"] = true

## The shot a Shooting Star rides on: pierces every enemy in line with the usual falloff, and leaves its streak.
func shooting_star(pr: Projectile, from: Vector3, dir: Vector3, reach: float) -> void:
	pr.pierce = 99
	pr.pierce_falloff = DataTranscendence.sig(&"starstrider", "falloff") / 100.0
	burst(&"shoot", from, from + dir.normalized() * minf(reach, 30.0))

## Royal Retort's shield wave: weapon damage and a stagger to the enemies just ahead (a proc: it triggers nothing).
func _retort(base: DamageRequest) -> void:
	var p := _player()
	var reach := DataTranscendence.sig(&"royal_guard", "reach")
	var world := p.get_world_3d()
	var wave := base.clone()
	wave.more.append(["Royal Retort wave", DataTranscendence.sig(&"royal_guard", "wave") / 100.0])
	wave.tags[&"proc"] = true
	wave.tags[&"aoe"] = true
	wave.label = "Royal Retort"
	wave.tags[&"skill"] = &"sig_royal_guard"
	wave.poise = maxf(wave.poise, 40.0)
	for t: Actor in CombatQuery.actors_in_arc(world, p.global_position, p.forward(), reach, 80.0, BH.LAYER_ENEMY):
		if not t.alive or CombatQuery.blocked(world, p.center(), t.center()):
			continue
		var r := wave.clone()
		r.tags[&"push_dir"] = (t.global_position - p.global_position).slide(Vector3.UP).normalized()
		var res := t.receive_hit(r, p, t.center())
		if res != null and not res.evaded and res.total > 0 and t.alive:
			t.status.apply(&"staggered", 0.6)
		p.on_proc_hit(t, res, r)
	burst(&"retort", p.global_position, p.global_position + p.forward() * reach)

## Called by the target while a projectile's request is being resolved (Hunter's Opening needs the target's health).
func opening(target: Actor, req: DamageRequest) -> void:
	if not has(&"tracker") or req.tags.has(&"proc") or target.get_meta(&"sig_opened", false):
		return
	if target.hp < target.max_hp() * 0.999:
		return
	target.set_meta(&"sig_opened", true)
	req.force_crit = true
	req.more.append(["Hunter's Opening", 1.0 + DataTranscendence.sig(&"tracker", "bonus") / 100.0])
	burst(&"opening", target.center() + Vector3.UP * 0.4)

## A hit this hero landed (after damage). `req` is null for skill hits, `skill` null for weapon attacks.
func on_hit_dealt(target: Actor, res: DamageResult, req: DamageRequest, skill: SkillDef) -> void:
	var p := _player()
	if p == null or res == null or res.evaded or res.total <= 0:
		return
	var proc := req != null and req.tags.has(&"proc")
	var weapon := req != null and req.tags.has(&"weapon") and not proc
	var shot := req != null and req.tags.has(&"projectile") and not proc
	if has(&"grand_paladin") and weapon:
		_dawn_hits = mini(_dawn_hits + 1, int(DataTranscendence.sig(&"grand_paladin", "hits")))
		if _dawn_hits >= int(DataTranscendence.sig(&"grand_paladin", "hits")) and _time - _dawn_t >= DataTranscendence.sig(&"grand_paladin", "icd"):
			_dawn_t = _time
			_dawn_hits = 0
			_dawnbreak()
	if has(&"wildwarden") and shot and p.status.has(&"rooted_stance") and target.alive:
		target.status.apply(&"slowed", DataTranscendence.sig(&"wildwarden", "slow"))
	if has(&"starstrider") and shot and not req.tags.has(&"sig_shoot") \
			and target.global_position.distance_to(p.global_position) > DataTranscendence.sig(&"starstrider", "far"):
		p.status.apply(&"star_chart", DataTranscendence.sig(&"starstrider", "fade"))
	if has(&"nightstalker") and req != null and req.tags.has(&"sig_shadow") and p.resource and p.resource.kind == &"combo":
		var aid := int(req.tags.get(&"attack_id", 0))
		if aid != _shadow_attack:
			_shadow_attack = aid
			p.resource.gain(DataTranscendence.sig(&"nightstalker", "combo"))
	var spell := skill != null and skill.kind == DamageRequest.Kind.SPELL and not proc
	if has(&"archmage") and spell and skill.mana_cost > 0.0 and _attune_cast != p.cast_serial() and target.alive:
		_attune_cast = p.cast_serial()
		_attuned_bolt(target, res)
	if has(&"void_sovereign") and spell and not target.alive and _time - _collapse_t >= DataTranscendence.sig(&"void_sovereign", "icd"):
		_collapse_t = _time
		_collapse(target.global_position, res)

## A skill was paid for (Runescript; Elemental Attunement turns).
func on_spell_paid(skill: SkillDef, paid: float) -> void:
	if skill == null or skill.kind != DamageRequest.Kind.SPELL or paid <= 0.0:
		return
	if has(&"arcanist"):
		actor.status.apply(&"runescript", DataTranscendence.sig(&"arcanist", "dur"))
	if has(&"archmage") and _damaging(skill):
		_attune = (_attune + 1) % ATTUNE.size()

static func _damaging(s: SkillDef) -> bool:
	return s.params.has("damage_min") or s.params.has("weapon_pct")

## Spells decorated with Runescript.
func decorate(req: DamageRequest) -> void:
	if has(&"arcanist") and req.kind == DamageRequest.Kind.SPELL and not req.tags.has(&"proc"):
		var n := mini(_stacks(&"runescript"), int(DataTranscendence.sig(&"arcanist", "max")))
		if n > 0:
			req.more.append(["Runescript x%d" % n, 1.0 + n * DataTranscendence.sig(&"arcanist", "per") / 100.0])

## Valor was spent on a skill (Conqueror's Dread).
func on_valor_spent(amount: float) -> void:
	if has(&"dark_general") and amount > 0.0:
		_add_dread()

func _add_dread() -> void:
	actor.status.apply(&"dread", DataTranscendence.sig(&"dark_general", "dur"))

## This hero defeated `v`.
func on_kill(v: Actor) -> void:
	var p := _player()
	if p == null:
		return
	if has(&"dark_general"):
		_add_dread()
	if has(&"phantom_reaper") and _time - _soul_t >= DataTranscendence.sig(&"phantom_reaper", "icd"):
		_soul_t = _time
		if p.resource and p.resource.kind == &"combo":
			p.resource.gain(DataTranscendence.sig(&"phantom_reaper", "combo"))
		if p.cooldowns.has(&"pr_phantom_crossing"):
			p.cooldowns[&"pr_phantom_crossing"] = maxf(0.0, p.cooldowns[&"pr_phantom_crossing"] - DataTranscendence.sig(&"phantom_reaper", "cd"))
			p.cooldowns_changed.emit()
		burst(&"soul", v.global_position)
	if has(&"blood_sovereign") and _bleed_of(v)[0] > 0.0 and _time - _blood_t >= DataTranscendence.sig(&"blood_sovereign", "icd"):
		_blood_t = _time
		_blood_price(v)

func _dawnbreak() -> void:
	var p := _player()
	var r := DataTranscendence.sig(&"grand_paladin", "radius")
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = p.stats
	req.use_weapon = true
	req.weapon_mult = DataTranscendence.sig(&"grand_paladin", "pct") / 100.0
	req.conversion = {Elements.LIGHT: 1.0}
	req.knockback = 3.0
	req.poise = 10.0
	req.graze = true
	req.tags[&"proc"] = true
	req.tags[&"aoe"] = true
	req.label = "Dawnbringer"
	req.tags[&"skill"] = &"sig_grand_paladin"
	var world := p.get_world_3d()
	for t: Actor in CombatQuery.actors_in_radius(world, p.global_position, r, BH.LAYER_ENEMY):
		if not t.alive or CombatQuery.blocked(world, p.center(), t.center()):
			continue
		var rq := req.clone()
		rq.tags[&"push_dir"] = (t.global_position - p.global_position).slide(Vector3.UP).normalized()
		p.on_proc_hit(t, t.receive_hit(rq, p, t.center()), rq)
	var heal := DataTranscendence.sig(&"grand_paladin", "heal") / 100.0
	for a in TranscendSkills.allies_near(p, p.global_position, r):
		if a is NetAvatar:
			Net.send_support(a, &"sig_dawn", {"heal_pct": heal})
		elif (a as Actor).alive:
			(a as Actor).heal((a as Actor).max_hp() * heal)
	burst(&"dawn", p.global_position)

func _attuned_bolt(target: Actor, res: DamageResult) -> void:
	var p := _player()
	var el: int = ATTUNE[_attune]
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = p.stats
	req.use_weapon = false
	req.base_min = res.total * DataTranscendence.sig(&"archmage", "pct") / 100.0
	req.base_max = req.base_min
	req.conversion = {el: 1.0}
	req.can_crit = false
	req.evadable = false
	req.tags[&"proc"] = true
	req.label = "Attuned bolt"
	req.tags[&"skill"] = &"sig_archmage"
	var from := p.global_position + Vector3.UP * 1.6
	burst(&"abolt", from, target.center())
	target.receive_hit(req, p, target.center())

func _collapse(at: Vector3, res: DamageResult) -> void:
	var p := _player()
	var world := p.get_world_3d()
	var r := DataTranscendence.sig(&"void_sovereign", "radius")
	var pull := DataTranscendence.sig(&"void_sovereign", "pull")
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = p.stats
	req.use_weapon = false
	req.base_min = res.total * DataTranscendence.sig(&"void_sovereign", "pct") / 100.0
	req.base_max = req.base_min
	req.conversion = {Elements.DARK: 1.0}
	req.can_crit = false
	req.graze = true
	req.tags[&"proc"] = true
	req.tags[&"aoe"] = true
	req.label = "Collapse"
	req.tags[&"skill"] = &"sig_void_sovereign"
	for t: Actor in CombatQuery.actors_in_radius(world, at, r, BH.LAYER_ENEMY):
		if not t.alive or CombatQuery.blocked(world, at + Vector3.UP, t.center()):
			continue
		if t.get(&"is_boss") != true:
			t.ensure_stats()
			var off := (t.global_position - at).slide(Vector3.UP)
			var d := minf(maxf(0.0, off.length() - t.body_radius - 0.5), pull) * (1.0 - clampf(t.stats.get_stat(&"knockback_res"), 0.0, 1.0))
			if d > 0.05:
				t.move_and_collide(-off.normalized() * d)
		t.receive_hit(req.clone(), p, t.center())
	burst(&"collapse", at)

## [damage per second, time left] of the bleed `v` carries, or carried when it died; [0, 0] when none.
static func _bleed_of(v: Actor) -> Array:
	var inst = v.status.statuses.get(&"bleeding")
	if inst != null:
		return [float(inst.dps), float(inst.remaining)]
	var m: Variant = v.get_meta(&"died_bleed", []) if not v.alive else []
	return [float(m[0]), float(m[1])] if m is Array and (m as Array).size() == 2 else [0.0, 0.0]

func _blood_price(v: Actor) -> void:
	var p := _player()
	var b := _bleed_of(v)
	var dps: float = b[0]
	var rem: float = b[1] if b[1] > 0.0 else 3.0
	var share := DataTranscendence.sig(&"blood_sovereign", "share") / 100.0
	if dps > 0.0:
		var world := p.get_world_3d()
		for t: Actor in CombatQuery.actors_in_radius(world, v.global_position, DataTranscendence.sig(&"blood_sovereign", "radius"), BH.LAYER_ENEMY):
			if t == v or not t.alive or CombatQuery.blocked(world, v.center(), t.center()):
				continue
			t.status.apply(&"bleeding", clampf(rem, 1.0, 6.0), 0.0, dps * share, Elements.PHYSICAL)
			t.last_attacker = p
	p.heal(p.max_hp() * DataTranscendence.sig(&"blood_sovereign", "heal") / 100.0)
	burst(&"blood", v.global_position)

# ---- Look --------------------------------------------------------------------------------------------------------------

static func _bright(prim: Color, acc: Color) -> Color:
	return prim if prim.get_luminance() > 0.3 else acc

## The swing colour of an advanced class (weapon trails and slash arcs read as the class).
static func swing_color(line: Array) -> Color:
	var id: StringName = line.back() if not line.is_empty() else &""
	if DataTranscendence.stage_of(id) < 1:
		return Color(0, 0, 0, 0)
	var th := ClassTranscendence.class_theme(id)
	return Color(_bright(th.primary, th.accent).lerp(th.accent, 0.35), 0.8)
