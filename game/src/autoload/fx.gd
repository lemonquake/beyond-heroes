extends Node
## Combat feedback (autoload `FX`): damage numbers, hitstop, camera shake routing, impact effects, rumble.
## The numbers shown come straight from DamageResult.total — the same value subtracted from HP.

const NUMBER_POOL := 48
const MAX_STAINS := 72               # ground blood / ichor stains alive at once (oldest fades first)
const STAIN_LIFE := 45.0
var world: Node3D                    # current map root; set by Game on map load
var _numbers: Array[Label3D] = []
var _next := 0
var _hitstop_until := 0
var _font: Font
var _stains: Array[Decal] = []

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	Events.damage_dealt.connect(_on_damage)
	Events.impact.connect(_on_impact)
	Events.hitstop.connect(hitstop)
	_font = UITheme.number_font()

func _ensure_pool() -> void:
	if not _numbers.is_empty() and is_instance_valid(_numbers[0]) and _numbers[0].get_parent() == world:
		return
	_numbers.clear()
	if world == null:
		return
	for i in NUMBER_POOL:
		var l := Label3D.new()
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.no_depth_test = true
		l.fixed_size = true
		l.pixel_size = 0.0011
		l.font = _font
		l.font_size = 30
		l.outline_size = 10
		l.outline_modulate = Color(0.05, 0.02, 0.02, 0.95)
		l.visible = false
		l.render_priority = 10
		l.outline_render_priority = 9
		world.add_child(l)
		_numbers.append(l)

func spawn(node: Node3D, pos: Vector3) -> void:
	if world == null or not is_instance_valid(world):
		node.queue_free()
		return
	world.add_child(node)
	node.global_position = pos

## Spawn a directional effect at `pos` turned toward `dir` (world). Directional meshes (slash arcs) are built
## along local +Z, the same axis as Actor.forward(), so they need the attacker's facing, not the world default.
func spawn_facing(node: Node3D, pos: Vector3, dir: Vector3) -> void:
	spawn(node, pos)
	var d := dir.slide(Vector3.UP)
	if d.length_squared() > 0.0001 and is_instance_valid(node) and node.is_inside_tree():
		node.global_rotation = Vector3(0.0, atan2(d.x, d.z), 0.0)

## Number styles: plain attacks, skill damage (tinted glow outline, swings aside), critical hits (huge gold slam
## with a tremble) and critical skill hits (both).
enum NumStyle { NORMAL, SKILL, CRIT, SKILL_CRIT }
const NUM_OUTLINE := Color(0.05, 0.02, 0.02, 0.95)
const CRIT_OUTLINE := Color(0.5, 0.05, 0.0, 1.0)

func _number(pos: Vector3, text: String, color: Color, scale := 1.0, rise := 1.2, style := NumStyle.NORMAL, outline := NUM_OUTLINE) -> void:
	if not Settings.damage_numbers:
		return
	_ensure_pool()
	if _numbers.is_empty():
		return
	var l := _numbers[_next]
	_next = (_next + 1) % _numbers.size()
	var tw_old: Tween = l.get_meta(&"tw") if l.has_meta(&"tw") else null
	if tw_old and tw_old.is_valid():
		tw_old.kill()
	l.text = text
	l.modulate = color
	l.outline_modulate = outline
	l.font_size = 30
	l.outline_size = 10
	match style:
		NumStyle.SKILL:
			l.font_size = 34
			l.outline_size = 14
		NumStyle.CRIT, NumStyle.SKILL_CRIT:
			l.font_size = 40
			l.outline_size = 16
	l.visible = true
	var jitter := Vector3(randf_range(-0.35, 0.35), 0, randf_range(-0.2, 0.2))
	var base := pos + jitter
	l.global_position = base
	var side := Vector3.RIGHT
	var cam := get_viewport().get_camera_3d() if get_viewport() else null
	if cam:
		side = cam.global_basis.x.slide(Vector3.UP).normalized()
	side *= 1.0 if randf() < 0.5 else -1.0
	var dur := 0.95 if style == NumStyle.NORMAL else 1.2
	var tw := l.create_tween()
	l.set_meta(&"tw", tw)
	tw.tween_method(func(t: float) -> void: _animate_number(l, base, side, t, style, scale, rise), 0.0, 1.0, dur)
	tw.tween_callback(func(): l.visible = false)

func _animate_number(l: Label3D, base: Vector3, side: Vector3, t: float, style: int, scale: float, rise: float) -> void:
	var s := 1.0
	var off := Vector3.UP * rise * (1.0 - pow(1.0 - t, 3.0))
	match style:
		NumStyle.NORMAL:
			var k := clampf(t / 0.13, 0.0, 1.0)
			s = lerpf(0.4, 1.0, k) + sin(k * PI) * 0.18
		NumStyle.SKILL:
			var k := clampf(t / 0.16, 0.0, 1.0)
			s = lerpf(1.8, 1.0, 1.0 - pow(1.0 - k, 3.0)) + sin(k * PI) * 0.12
			off += side * 0.55 * sin(clampf(t * 1.4, 0.0, 1.0) * PI * 0.5)
		NumStyle.CRIT, NumStyle.SKILL_CRIT:
			var k := clampf(t / 0.16, 0.0, 1.0)
			s = lerpf(2.6, 1.0, 1.0 - pow(1.0 - k, 4.0))
			var shake := 1.0 - clampf(t / 0.35, 0.0, 1.0)
			off += Vector3(sin(t * 110.0), cos(t * 93.0) * 0.6, 0.0) * 0.07 * shake
			off.y = rise * 0.8 * pow(clampf((t - 0.25) / 0.75, 0.0, 1.0), 0.6) # hang, then rise
			if style == NumStyle.SKILL_CRIT:
				off += side * 0.4 * sin(clampf(t * 1.4, 0.0, 1.0) * PI * 0.5)
	l.scale = Vector3.ONE * scale * s
	l.global_position = base + off
	l.modulate.a = 1.0 - smoothstep(0.72, 1.0, t)

## The skill's name flares above the caster's head, then floats up and fades.
func skill_banner(actor: Node3D, text: String, color: Color) -> void:
	if world == null or not is_instance_valid(world) or not is_instance_valid(actor):
		return
	# Parented to the caster so it rides along through leaps and dashes (labels billboard, so its turning is moot).
	var root := Node3D.new()
	actor.add_child(root)
	var h: float = actor.get(&"body_height") if actor.get(&"body_height") != null else 1.8
	root.position = Vector3.UP * (h + 1.5)
	var glow := _banner_label(text.to_upper(), Color(color.r, color.g, color.b, 0.0), Color(color.r, color.g, color.b, 0.45), 30)
	var front := _banner_label(text.to_upper(), color.lerp(Color.WHITE, 0.6), Color(0.08, 0.05, 0.02, 0.95), 10)
	# below the damage numbers (priority 9-10): the numbers matter more mid-fight
	glow.render_priority = 6
	glow.outline_render_priority = 5
	front.render_priority = 8
	front.outline_render_priority = 7
	root.add_child(glow)
	root.add_child(front)
	root.scale = Vector3.ONE * 0.5
	var tw := root.create_tween()
	tw.tween_property(root, "scale", Vector3.ONE * 1.12, 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(root, "scale", Vector3.ONE, 0.1)
	tw.tween_interval(0.55)
	tw.set_parallel(true)
	tw.tween_property(root, "position", root.position + Vector3.UP * 0.7, 0.5).set_ease(Tween.EASE_IN)
	tw.tween_method(func(a: float) -> void:
		front.modulate.a = a
		glow.outline_modulate.a = a * 0.45, 1.0, 0.0, 0.5)
	tw.chain().tween_callback(root.queue_free)

func _banner_label(text: String, col: Color, outline: Color, outline_size: int) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.fixed_size = true
	l.pixel_size = 0.0011
	l.font = UITheme.title_font()
	l.font_size = 38
	l.outline_size = outline_size
	l.modulate = col
	l.outline_modulate = outline
	return l

func _on_damage(target: Node, r: DamageResult, pos: Vector3, attacker: Node) -> void:
	var is_player_target: bool = target is Actor and target.team == BH.Team.PLAYER
	var is_hero: bool = target is Player
	var tempo_hit: bool = attacker is Tempo
	var dir := Vector3.ZERO
	if attacker is Node3D and is_instance_valid(attacker) and target is Node3D:
		dir = (target as Node3D).global_position - (attacker as Node3D).global_position
	if r.evaded:
		_number(pos + Vector3.UP * 0.3, "Evade" if not is_player_target else "Dodged", Color(0.8, 0.85, 0.9), 0.8)
		return
	if r.perfect_block:
		_number(pos + Vector3.UP * 0.4, "Parry!", Color(1.0, 0.95, 0.6), 1.3, 1.2, NumStyle.CRIT, Color(0.35, 0.2, 0.0, 1.0))
	elif r.blocked:
		_number(pos + Vector3.UP * 0.4, "Blocked", Color(0.75, 0.85, 1.0), 0.9, 1.2, NumStyle.NORMAL, Color(0.05, 0.08, 0.18, 0.95))
	if r.blocked or r.perfect_block:
		_block_feedback(target, r, pos, dir, attacker)
	if r.immune:
		_number(pos, "Immune", Color(0.7, 0.7, 0.7), 0.8)
		return
	if r.total <= 0:
		return
	var c := Elements.color(r.dominant_element)
	if r.dominant_element == Elements.PHYSICAL:
		c = Color(1.0, 0.97, 0.9)
	var skill_hit := r.skill != &"" and not is_player_target
	var style := NumStyle.NORMAL
	var outline := NUM_OUTLINE
	if is_player_target:
		c = Color(1.0, 0.35, 0.3) if is_hero else Color(1.0, 0.62, 0.45)
	elif tempo_hit:
		c = c.lerp(Color(0.62, 0.95, 1.0), 0.45)
	var s := 1.0 if is_hero or not is_player_target else 0.78
	if tempo_hit:
		s = 0.85
	var txt := str(r.total)
	if skill_hit:
		style = NumStyle.SKILL
		var sc := skill_color(r)
		c = sc.lerp(Color.WHITE, 0.15)
		outline = Color(0.09, 0.03, 0.12, 1.0)
		s = 1.2
	if r.is_crit:
		txt = "%d!" % r.total
		if skill_hit:
			style = NumStyle.SKILL_CRIT
			c = Color(1.0, 0.97, 0.82)
			outline = skill_color(r).darkened(0.35)
			s = 1.65
		else:
			style = NumStyle.CRIT
			s = 1.5
			if not is_player_target:
				c = c.lerp(Color(1.0, 0.8, 0.2), 0.65)
				outline = CRIT_OUTLINE
	elif r.finisher and not is_player_target:
		s *= 1.15
	if r.shattered:
		txt = "Shatter %d" % r.total
	_number(pos, txt, c, s, 1.2, style, outline)
	# Feedback strength scales with hit size relative to target HP.
	if target is Actor:
		var rel := clampf(float(r.total) / maxf(1.0, target.max_hp()) * 4.0, 0.0, 1.0)
		var strength := clampf(rel + (0.35 if r.is_crit else 0.0) + r.knockback / 30.0, 0.0, 1.2)
		var mat := hit_material(target)
		if r.dominant_element != Elements.PHYSICAL or mat[0] == &"":
			spawn(VFXLib.hit_burst(pos, r.dominant_element, strength, r.is_crit), pos)
		if mat[0] != &"":
			spawn(Gore.hit(pos, dir, mat[0], mat[1], strength, r.is_crit), pos)
			if Gore.bleeds(mat[0]) and (strength > 0.18 or r.is_crit):
				var d2 := dir.slide(Vector3.UP).normalized()
				stain(target.global_position + d2 * randf_range(0.4, 1.4), mat[1], randf_range(0.7, 1.3) * (1.4 if r.is_crit else 1.0), atan2(d2.x, d2.z) - PI * 0.5)
		var big := r.heavy or r.finisher
		if attacker != null and dir != Vector3.ZERO:
			var ic := c if r.dominant_element != Elements.PHYSICAL and not is_player_target else Color(1.0, 0.88, 0.65)
			if is_player_target:
				ic = Color(1.0, 0.55, 0.4)
			spawn(VFXLib.strike_impact(dir, ic, strength + (0.3 if big else 0.0), r.is_crit, big and not is_player_target), pos)
		if target.visual:
			target.visual.flash(Color(1, 1, 1) if not is_player_target else Color(1, 0.3, 0.2), 0.9 if r.is_crit else 0.6)
			var fl := 0.3 + strength * 0.7 + (0.35 if r.is_crit else 0.0) + (0.3 if big else 0.0)
			fl /= sqrt(clampf((target as Actor).weight, 0.6, 9.0))
			if target is Enemy and (target as Enemy).is_boss:
				fl *= 0.45
			if is_hero:
				fl *= 0.6
			target.visual.flinch(dir if dir != Vector3.ZERO else -(target as Actor).forward(), fl)
		if attacker is Player:
			if r.is_crit or r.knockback >= Actor.HEAVY_KNOCK or r.shattered or r.finisher:
				hitstop(0.085 if r.is_crit or r.finisher else 0.055)
				Events.camera_shake.emit(0.22 + strength * 0.15 + (0.1 if r.finisher else 0.0))
				rumble(0.4, 0.6, 0.12)
			elif strength > 0.3 or r.heavy:
				hitstop(0.04)
				Events.camera_shake.emit(0.12)
			else:
				hitstop(0.018)
		elif is_hero:
			Events.camera_shake.emit(clampf(rel * 0.6, 0.08, 0.35))
			rumble(0.6, 0.3, 0.15)

## Colour of a skill's damage: its dominant element, gold for physical (Knight) skills.
func skill_color(r: DamageResult) -> Color:
	if r.dominant_element == Elements.PHYSICAL:
		return Color(1.0, 0.55, 0.12)
	return Elements.color(r.dominant_element)

## Guarded hits: barrier flash toward the attacker, metal sparks, a recoil and (for monsters) the clang.
## The hero's own guard sound and resource gain live in Player._on_blocked.
func _block_feedback(target: Node, r: DamageResult, pos: Vector3, dir: Vector3, attacker: Node) -> void:
	if not (target is Actor):
		return
	var t := target as Actor
	var at := pos
	if dir != Vector3.ZERO:
		at = t.center() - dir.slide(Vector3.UP).normalized() * (t.body_radius + 0.15)
	spawn(VFXLib.block_impact(-dir if dir != Vector3.ZERO else t.forward(), r.perfect_block), at)
	if t.visual:
		t.visual.flash(Color(0.55, 0.75, 1.0) if not r.perfect_block else Color(1.0, 0.85, 0.4), 0.7, 0.12)
		t.visual.flinch(dir if dir != Vector3.ZERO else -t.forward(), 0.35 if r.perfect_block else 0.22)
	if not (target is Player):
		Audio.play_at(&"parry" if r.perfect_block else &"block", at)
		if attacker is Player:
			hitstop(0.05)
			Events.camera_shake.emit(0.12)
			rumble(0.3, 0.2, 0.08)
			if attacker.visual:
				# the attacker's weapon rebounds off the guard
				attacker.visual.flinch(-dir, 0.35)

## [material, liquid colour] of what a target bleeds: enemies from their definition, the hero is flesh.
func hit_material(target: Node) -> Array:
	if target is Enemy and (target as Enemy).def:
		var d := (target as Enemy).def
		return [d.hit_material, d.blood]
	if target is Tempo:
		return [Gore.AETHER, DataTempos.SPIRIT_TINT]   # spirits shed light, not blood
	if target is Actor:
		return [Gore.FLESH, Color(0.42, 0.02, 0.02)]
	return [&"", Color.BLACK]

## Leave a stain on the ground at `at` (world). Bounded: the oldest stain fades out when the budget is full.
func stain(at: Vector3, c: Color, size: float, yaw := 0.0) -> Decal:
	if world == null or not is_instance_valid(world) or not Settings.blood:
		return null
	_stains = _stains.filter(func(d): return is_instance_valid(d))
	while _stains.size() >= MAX_STAINS:
		var old: Decal = _stains.pop_front()
		old.queue_free()
	var d := Gore.stain(c, size, randi(), yaw)
	world.add_child(d)
	d.global_position = at + Vector3.UP * 0.15
	_stains.append(d)
	d.modulate.a = 0.0
	var tw := d.create_tween()
	tw.tween_property(d, "modulate:a", c.a, 0.15)
	tw.tween_interval(STAIN_LIFE)
	tw.tween_property(d, "modulate:a", 0.0, 6.0)
	tw.tween_callback(d.queue_free)
	return d

## A pool that spreads under a body over `grow` seconds. The caller (corpse) owns and frees it; it counts toward
## the stain budget so pools and splatters share one bound.
func pool(at: Vector3, c: Color, size: float, grow := 6.0) -> Decal:
	if world == null or not is_instance_valid(world) or not Settings.blood:
		return null
	_stains = _stains.filter(func(d): return is_instance_valid(d))
	while _stains.size() >= MAX_STAINS:
		(_stains.pop_front() as Decal).queue_free()
	var d := Gore.stain(c.darkened(0.15), 0.3, randi(), randf() * TAU)
	world.add_child(d)
	d.global_position = at + Vector3.UP * 0.15
	_stains.append(d)
	d.create_tween().tween_property(d, "size", Vector3(size, 1.2, size), grow).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	return d

func stain_count() -> int:
	_stains = _stains.filter(func(d): return is_instance_valid(d))
	return _stains.size()

func heal_number(pos: Vector3, amount: int) -> void:
	_number(pos, "+%d" % amount, Color(0.45, 1.0, 0.5), 0.9, 1.0)

func text_popup(pos: Vector3, text: String, color: Color, scale := 1.0) -> void:
	_number(pos, text, color, scale, 1.6)

## Brief global slow-down that sells heavy impacts. Uses real time so it always recovers.
func hitstop(duration: float) -> void:
	if Settings.reduced_motion or get_tree().paused:
		return
	var until := Time.get_ticks_msec() + int(duration * 1000.0)
	if until <= _hitstop_until:
		return
	_hitstop_until = until
	Engine.time_scale = 0.06
	await get_tree().create_timer(duration, true, false, true).timeout
	if Time.get_ticks_msec() >= _hitstop_until - 2:
		Engine.time_scale = 1.0

func _process(_d: float) -> void:
	if Engine.time_scale < 1.0 and Time.get_ticks_msec() > _hitstop_until + 50:
		Engine.time_scale = 1.0   # safety net

func _on_impact(pos: Vector3, strength: float, surface: StringName) -> void:
	var s := clampf(strength / 15.0, 0.1, 1.2)
	spawn(VFXLib.dust_puff(s), pos)
	if surface == &"stone" or surface == &"earth":
		spawn(VFXLib.debris(s), pos + Vector3.UP * 0.5)

## Controller rumble architecture (no-op without a joypad).
func rumble(weak: float, strong: float, duration: float) -> void:
	for id in Input.get_connected_joypads():
		Input.start_joy_vibration(id, weak, strong, duration)
