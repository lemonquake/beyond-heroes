class_name SnareLine
extends Node3D
## Snareline (Tracker): a bounded line of snares laid toward the aim. The line stops at the first wall. Each enemy is
## caught at most once per cast, by whichever snare it steps on first: one weapon hit and a root (bosses and
## root-immune enemies are slowed instead, TranscendZone.root). The snares vanish after `duration` seconds.

var runner: SkillRunner
var skill: SkillDef
var caster: Actor
var points: Array = []          # Vector3 snare positions
var trigger := 1.1
var duration := 12.0
var root_time := 1.6
var visual_only := false
var _req: DamageRequest
var _caught := {}
var _t := 0.0
var _scan := 0.0
var _marks: Array = []

static func lay(p_runner: SkillRunner, p_skill: SkillDef, p: Dictionary, dir: Vector3) -> SnareLine:
	var c := p_runner.caster
	var s := SnareLine.new()
	Perf.mark_fx(s)
	s.runner = p_runner
	s.skill = p_skill
	s.caster = c
	s.trigger = float(p.get("trigger", 1.1))
	s.duration = float(p.get("duration", 12.0))
	s.root_time = float(p.get("root", 1.6))
	s._req = p_runner.make_request(p_skill, p)
	s._req.more.append(["Trap mastery", 1.0 + c.stats.get_stat(&"trap_damage")])
	var world: World3D = c.get_world_3d()
	var d := dir.slide(Vector3.UP).normalized()
	if d.length() < 0.1:
		d = c.forward()
	var prev: Vector3 = c.global_position + Vector3.UP * 0.6
	var n := clampi(int(p.get("count", 5.0)), 1, 8)
	var spacing := clampf(float(p.get("spacing", 1.6)), 0.8, 3.0)
	for i in n:
		var pt: Vector3 = c.global_position + d * (1.6 + spacing * i)
		if CombatQuery.blocked(world, prev, pt + Vector3.UP * 0.6):
			break
		pt = CombatQuery.ground_at(world, pt)
		s.points.append(pt)
		prev = pt + Vector3.UP * 0.6
	p_runner.parent().add_child(s)
	s.global_position = c.global_position
	s._draw()
	var flat := []
	for q in s.points:
		flat.append(q)
	Net.share_skill_fx("tsnare", c.global_position, Vector3.ZERO, {"pts": flat, "d": s.duration, "t": s.trigger})
	Audio.play_at(p_skill.sound_cast, c.global_position)
	return s

## A harmless copy for another player's screen.
static func remote(parent: Node, pts: Array, d: float, t: float) -> SnareLine:
	var s := SnareLine.new()
	Perf.mark_fx(s)
	s.visual_only = true
	s.duration = clampf(d, 0.5, 20.0)
	s.trigger = clampf(t, 0.3, 2.0)
	for q in pts.slice(0, 8):
		if q is Vector3 and (q as Vector3).is_finite():
			s.points.append(q)
	parent.add_child(s)
	s._draw()
	return s

func _draw() -> void:
	var col := Color(0.85, 0.75, 0.45, 0.8)
	for pt in points:
		var m := VFXLib.telegraph("ring", Vector2(trigger, trigger), 0.25, col, 360.0, trigger * 0.55)
		add_child(m)
		m.global_position = pt + Vector3.UP * 0.02
		_marks.append(m)

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	if _t >= duration or (not visual_only and (not is_instance_valid(caster) or not caster.is_inside_tree())):
		set_physics_process(false)
		queue_free()
		return
	if visual_only:
		return
	_scan -= delta
	if _scan > 0.0:
		return
	_scan = 0.1
	var world := get_world_3d()
	for i in points.size():
		var pt: Vector3 = points[i]
		for a: Actor in CombatQuery.actors_in_radius(world, pt, trigger, runner.mask()):
			var k := a.get_instance_id()
			if _caught.has(k) or not a.alive:
				continue
			_caught[k] = true
			var r := _req.clone()
			r.tags[&"aoe"] = true
			r.evadable = false
			r.label = skill.display_name
			var res := a.receive_hit(r, caster, a.center())
			runner._hit(skill, a, res)
			if a.alive and not res.evaded:
				TranscendZone.root(a, root_time, caster)
			FX.spawn(VFXLib.ring_wave(Color(0.9, 0.8, 0.45, 0.9), 1.2, 0.3), pt)
			Audio.play_at(skill.sound_hit, pt, -3.0)
