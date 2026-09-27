class_name SkillFX
extends RefCounted
## Presentation of skill casts: the floating skill-name banner, a cast flourish for every skill, and the Knight's
## signature choreography — a body-motion layer (CharacterVisual.play_pose) timed to each skill's hit/release frame,
## plus the effects that land with it. Purely cosmetic: gameplay timing stays in SkillRunner / TimedAction.

const KNIGHT_GOLD := Color(1.0, 0.78, 0.35)
const HOLY := Color(1.0, 0.9, 0.55)
const STEEL := Color(0.4, 0.62, 1.0)
const EMBER := Color(1.0, 0.5, 0.2)

static func color_for(skill: SkillDef) -> Color:
	var e := skill.element
	if not skill.conversion.is_empty():
		var best := -1.0
		for k in skill.conversion:
			if float(skill.conversion[k]) > best:
				best = float(skill.conversion[k])
				e = int(k)
	if e == Elements.PHYSICAL:
		return KNIGHT_GOLD
	return Elements.color(e)

static func _later(node: Node, t: float, fn: Callable) -> void:
	if t <= 0.0:
		fn.call()
		return
	if not is_instance_valid(node) or not node.is_inside_tree():
		return
	node.get_tree().create_timer(t, false).timeout.connect(func() -> void:
		if is_instance_valid(node):
			fn.call())

## Called when a skill starts (after it was paid). `a` is null for channels (Whirlwind).
static func cast(caster: Actor, skill: SkillDef, a: TimedAction) -> void:
	var c := color_for(skill)
	FX.skill_banner(caster, skill.display_name, c)
	# Cast flourish: an aura ring snaps out at the feet, motes rise, a brief glow.
	FX.spawn(VFXLib.ring_wave(Color(c.r, c.g, c.b, 0.85), 1.6, 0.35, 0.5), caster.global_position)
	FX.spawn(VFXLib.particles(Color(c.r, c.g, c.b, 0.9), 18, 0.6, true, 0.25, 3.0, 25.0, Vector3(0, 2.0, 0), 0.5), caster.global_position + Vector3.UP * 0.2)
	FX.spawn(VFXLib.light_flash(c, 2.5, 3.5, 0.3), caster.center())
	if caster.visual:
		caster.visual.flash(c, 0.35, 0.25)
	if skill.class_id != &"knight" or caster.visual == null:
		return
	if skill.kind == DamageRequest.Kind.ATTACK:
		caster.visual.set_trail(true, Color(c.r, c.g, c.b, 0.75), 1.2)
	var v := caster.visual
	var t := a.first_hit_time() if a != null else 0.0
	match skill.id:
		&"cleave":
			# coil the torso back, then unwind into a lunging sweep
			v.play_pose([
				[t * 0.75, {"pos": Vector3(0, -0.1, -0.08), "rot": Vector3(-0.05, -0.55, 0), "scale": Vector3(1.04, 0.93, 1.04)}],
				[t, {"pos": Vector3(0, -0.04, 0.38), "rot": Vector3(0.14, 0.4, 0), "trans": Tween.TRANS_EXPO, "ease": Tween.EASE_IN}],
				[t + 0.22, {"pos": Vector3(0, -0.04, 0.34), "rot": Vector3(0.1, 0.45, 0)}]], 0.25)
		&"shield_bash":
			# drop the shoulder and drive through
			v.play_pose([
				[0.08, {"pos": Vector3(0, -0.1, 0), "rot": Vector3(0.28, 0.25, 0), "scale": Vector3(1.05, 0.9, 1.08)}],
				[t, {"pos": Vector3(0, -0.06, 0.2), "rot": Vector3(0.38, 0.3, 0), "scale": Vector3(0.96, 1.0, 1.12)}],
				[t + 0.18, {"pos": Vector3(0, -0.06, 0.2), "rot": Vector3(0.3, 0.2, 0)}]], 0.2)
			FX.spawn(VFXLib.dust_puff(0.6), caster.global_position)
		&"leap_slam":
			# crouch, spring, a full forward somersault through the air, then crash down
			v.play_pose([
				[0.12, {"pos": Vector3(0, -0.14, 0), "scale": Vector3(1.12, 0.8, 1.12)}],
				[0.2, {"scale": Vector3(0.9, 1.15, 0.9), "pivot": 0.95}],
				[t * 0.88, {"rot": Vector3(TAU, 0, 0), "pivot": 0.95, "trans": Tween.TRANS_QUAD, "ease": Tween.EASE_IN_OUT}],
				[t * 0.88, {"instant": true}],
				[t, {"rot": Vector3(0.25, 0, 0), "pivot": 0.95}],
				[t + 0.06, {"pos": Vector3(0, -0.12, 0.1), "rot": Vector3(0.3, 0, 0), "scale": Vector3(1.15, 0.82, 1.15), "trans": Tween.TRANS_EXPO}],
				[t + 0.3, {"pos": Vector3(0, -0.1, 0.1), "rot": Vector3(0.25, 0, 0), "scale": Vector3(1.08, 0.9, 1.08)}]], 0.3)
			FX.spawn(VFXLib.dust_puff(0.9), caster.global_position)
			FX.spawn(VFXLib.ring_wave(Color(0.85, 0.7, 0.45, 0.8), 2.0, 0.3), caster.global_position)
		&"war_cry":
			var rel := a.release_t if a != null else 0.4
			# gather in, then throw the chest open and roar
			v.play_pose([
				[rel * 0.7, {"pos": Vector3(0, -0.14, -0.05), "rot": Vector3(0.22, 0, 0), "scale": Vector3(1.06, 0.9, 1.06)}],
				[rel, {"pos": Vector3(0, 0.1, 0), "rot": Vector3(-0.32, 0, 0), "scale": Vector3(1.1, 1.08, 1.1), "trans": Tween.TRANS_BACK}],
				[rel + 0.45, {"pos": Vector3(0, 0.08, 0), "rot": Vector3(-0.28, 0, 0), "scale": Vector3(1.08, 1.06, 1.08)}]], 0.3)
			FX.spawn(VFXLib.particles(Color(EMBER.r, EMBER.g, EMBER.b, 0.9), 16, 0.5, true, 0.3, 1.5, 180.0, Vector3(0, -1.0, 0), 1.2), caster.center())
		&"judgment":
			# rise on a column of light with the blade lifted high, then bring it down like a verdict
			v.play_pose([
				[t * 0.65, {"pos": Vector3(0, 0.38, -0.1), "rot": Vector3(-0.3, 0, 0), "scale": Vector3(1.05, 1.08, 1.05)}],
				[t * 0.85, {"pos": Vector3(0, 0.42, -0.1), "rot": Vector3(-0.36, 0, 0), "scale": Vector3(1.05, 1.1, 1.05)}],
				[t, {"pos": Vector3(0, -0.08, 0.3), "rot": Vector3(0.38, 0, 0), "scale": Vector3(1.1, 0.9, 1.1), "trans": Tween.TRANS_EXPO, "ease": Tween.EASE_IN}],
				[t + 0.3, {"pos": Vector3(0, -0.06, 0.28), "rot": Vector3(0.32, 0, 0)}]], 0.3)
			FX.spawn(VFXLib.light_pillar(HOLY, 6.0, 0.9, maxf(0.5, t)), caster.global_position)
			FX.spawn(VFXLib.particles(Color(1.0, 0.92, 0.6, 0.9), 26, 0.9, true, 0.3, 2.0, 20.0, Vector3(0, 3.0, 0), 0.8), caster.global_position + Vector3.UP * 0.2)
		&"ground_fissure":
			# heave the weapon overhead and split the earth
			v.play_pose([
				[t * 0.7, {"pos": Vector3(0, 0.12, -0.08), "rot": Vector3(-0.28, 0, 0), "scale": Vector3(0.98, 1.06, 0.98)}],
				[t, {"pos": Vector3(0, -0.14, 0.18), "rot": Vector3(0.42, 0, 0), "scale": Vector3(1.12, 0.86, 1.12), "trans": Tween.TRANS_EXPO, "ease": Tween.EASE_IN}],
				[t + 0.28, {"pos": Vector3(0, -0.12, 0.16), "rot": Vector3(0.36, 0, 0), "scale": Vector3(1.08, 0.9, 1.08)}]], 0.28)
		&"iron_bulwark":
			# plant the feet and brace behind the shield
			v.play_pose([
				[0.1, {"pos": Vector3(0, -0.12, 0), "rot": Vector3(0.12, 0, 0), "scale": Vector3(1.12, 0.88, 1.12), "trans": Tween.TRANS_BACK}],
				[0.55, {"pos": Vector3(0, -0.1, 0), "rot": Vector3(0.1, 0, 0), "scale": Vector3(1.1, 0.9, 1.1)}]], 0.25)
			v.flash(STEEL, 0.7, 0.4)
		&"whirlwind":
			FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.55, 0.9), 3.0, 0.4, 0.6), caster.global_position)
			FX.spawn(VFXLib.dust_puff(0.8), caster.global_position)

# ---- Knight hit moments (called by SkillRunner when the effect lands) -----------------------------------------------

## Cleave: a blazing crescent over the regular arc and a spray of sparks along the sweep.
static func cleave(caster: Actor, f: Vector3, reach: float, arc: float) -> void:
	var p := caster.global_position
	FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 0.8, 0.4, 0.95), reach * 1.15, arc + 20.0, 0.8, 0.32, 0.3), p, f)
	FX.spawn_facing(VFXLib.slash_arc(Color(1.0, 1.0, 0.92, 0.8), reach * 0.75, arc - 10.0, 1.35, 0.22, 0.25, false), p, f)
	for i in 3:
		var d := f.rotated(Vector3.UP, deg_to_rad(lerpf(-arc * 0.4, arc * 0.4, i / 2.0)))
		FX.spawn(VFXLib.spark_spray(d + Vector3.UP * 0.3, Color(1.0, 0.8, 0.45, 1.0), 8, 9.0, 25.0, 0.3, 0.5), p + d * reach * 0.8 + Vector3.UP)
	FX.spawn(VFXLib.light_flash(KNIGHT_GOLD, 4.0, 5.0, 0.2), p + f * reach * 0.5 + Vector3.UP)
	Events.camera_shake.emit(0.22)

## Shield Bash contact: a flat shock cone out of the shield and a steel flash.
static func shield_bash(caster: Actor, at: Vector3) -> void:
	var f := caster.forward()
	FX.spawn(VFXLib.impact_flash(Color(0.85, 0.92, 1.0, 1.0), 3.0, 0.2, 6), at)
	FX.spawn(VFXLib.spark_spray(f + Vector3.UP * 0.2, Color(1.0, 0.85, 0.5, 1.0), 20, 11.0, 35.0, 0.3, 0.5), at)
	FX.spawn_facing(VFXLib.slash_arc(Color(0.75, 0.88, 1.0, 0.9), 2.6, 90.0, 1.0, 0.25, 0.8), caster.global_position, f)
	FX.hitstop(0.08)

## Leap Slam landing: the ground shatters in glowing cracks under a pillar of dust and light.
static func leap_land(caster: Actor, at: Vector3, radius: float) -> void:
	FX.spawn(VFXLib.ground_crack(Color(1.0, 0.6, 0.25, 1.0), radius * 1.1, 1.6), at)
	FX.spawn(VFXLib.impact_flash(Color(1.0, 0.85, 0.55, 1.0), 4.5, 0.25, 8), at + Vector3.UP * 0.6)
	FX.spawn(VFXLib.light_pillar(Color(1.0, 0.75, 0.4), 4.0, 1.2, 0.45), at)
	FX.spawn(VFXLib.spark_spray(Vector3.UP, Color(1.0, 0.7, 0.35, 1.0), 26, 12.0, 70.0, 0.4, 0.5), at + Vector3.UP * 0.3)
	_later(caster, 0.12, func() -> void: FX.spawn(VFXLib.ring_wave(Color(1.0, 0.8, 0.5, 0.8), radius * 1.4, 0.55, 0.4), at))
	FX.hitstop(0.1)
	FX.rumble(0.8, 1.0, 0.25)

## War Cry release: sound-wave rings burst from the chest, shock rings roll across the ground, an ember column.
static func war_cry(caster: Actor, radius: float) -> void:
	var f := caster.forward()
	var chest := caster.center() + Vector3.UP * 0.2
	for i in 3:
		_later(caster, 0.09 * i, func() -> void:
			var rw := VFXLib.ring_wave(Color(1.0, 0.6, 0.3, 0.85), 1.6 + i * 0.9, 0.4, 0.35)
			FX.spawn(rw, chest + f * (0.5 + i * 0.55))
			if is_instance_valid(rw) and rw.is_inside_tree():
				# stand the ring up so it faces where the knight is roaring
				rw.global_basis = Basis.looking_at(-f, Vector3.UP) * Basis(Vector3.RIGHT, PI * 0.5)
			if i == 1:
				FX.spawn(VFXLib.ring_wave(Color(1.0, 0.55, 0.25, 0.8), radius * 0.6, 0.5, 0.5), caster.global_position))
	FX.spawn(VFXLib.light_pillar(EMBER, 5.0, 1.0, 0.7), caster.global_position)
	FX.spawn(VFXLib.particles(Color(1.0, 0.55, 0.2, 0.95), 40, 1.0, true, 0.3, 5.0, 60.0, Vector3(0, 1.5, 0), 0.8), caster.global_position + Vector3.UP * 0.3)
	FX.spawn(VFXLib.light_flash(EMBER, 6.0, radius * 1.5, 0.45), chest)
	FX.rumble(0.5, 0.6, 0.3)

## Iron Bulwark: a steel dome snaps around the knight and a hex barrier flashes in front.
static func bulwark(caster: Actor) -> void:
	FX.spawn(VFXLib.shield_dome(STEEL, 1.6, 1.1), caster.global_position)
	FX.spawn(VFXLib.light_pillar(STEEL, 3.0, 1.1, 0.5), caster.global_position)
	FX.spawn(VFXLib.spark_spray(Vector3.UP, Color(0.75, 0.88, 1.0, 1.0), 18, 6.0, 80.0, 0.35, 0.4), caster.center())
	FX.spawn(VFXLib.block_impact(caster.forward(), false), caster.center() + caster.forward() * 0.6)
	FX.spawn(VFXLib.light_flash(STEEL, 3.0, 4.0, 0.35), caster.center())

## Judgment: blades of light fall one after another along the verdict line, the ground splits beneath each.
static func judgment(caster: Actor, f: Vector3, length: float) -> void:
	var origin := caster.global_position
	for i in 3:
		var k := 0.3 + 0.35 * i
		var at := CombatQuery.ground_at(caster.get_world_3d(), origin + f * length * k)
		_later(caster, 0.07 * i, func() -> void:
			var sw := VFXLib.light_sword(HOLY, 3.6 + i * 0.9, 0.12, 0.45 + 0.1 * (2 - i))
			FX.spawn(sw, at)
			if is_instance_valid(sw) and sw.is_inside_tree():
				sw.global_rotation = Vector3(0, atan2(f.x, f.z), 0)
			_later(caster, 0.12, func() -> void:
				FX.spawn(VFXLib.ground_crack(HOLY, 1.6 + i * 0.4, 1.2), at)
				FX.spawn(VFXLib.impact_flash(Color(1.0, 0.95, 0.75, 1.0), 3.5, 0.2, 8), at + Vector3.UP * 0.5)
				FX.spawn(VFXLib.spark_spray(Vector3.UP, Color(1.0, 0.9, 0.6, 1.0), 16, 10.0, 60.0, 0.35, 0.5), at + Vector3.UP * 0.2)
				Events.camera_shake.emit(0.2 + 0.08 * i)))
	FX.hitstop(0.09)
	FX.rumble(0.7, 0.9, 0.3)

## Ground Fissure: the first rupture at the knight's feet.
static func fissure(caster: Actor, dir: Vector3) -> void:
	var at := caster.global_position + dir * 1.2
	FX.spawn(VFXLib.ground_crack(Color(0.95, 0.55, 0.25, 1.0), 2.2, 1.3), at)
	FX.spawn(VFXLib.impact_flash(Color(1.0, 0.8, 0.5, 1.0), 2.5, 0.2, 6), at + Vector3.UP * 0.4)
	FX.spawn(VFXLib.debris(1.0, Color(0.5, 0.38, 0.25)), at + Vector3.UP * 0.3)
	FX.hitstop(0.06)
