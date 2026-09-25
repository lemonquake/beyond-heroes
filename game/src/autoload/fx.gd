extends Node
## Combat feedback (autoload `FX`): damage numbers, hitstop, camera shake routing, impact effects, rumble.
## The numbers shown come straight from DamageResult.total — the same value subtracted from HP.

const NUMBER_POOL := 48
var world: Node3D                    # current map root; set by Game on map load
var _numbers: Array[Label3D] = []
var _next := 0
var _hitstop_until := 0
var _font: Font

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

func _number(pos: Vector3, text: String, color: Color, scale := 1.0, rise := 1.2) -> void:
	if not Settings.damage_numbers:
		return
	_ensure_pool()
	if _numbers.is_empty():
		return
	var l := _numbers[_next]
	_next = (_next + 1) % _numbers.size()
	var tw_old: Tween = l.get_meta(&"tw", null)
	if tw_old and tw_old.is_valid():
		tw_old.kill()
	l.text = text
	l.modulate = color
	l.visible = true
	var jitter := Vector3(randf_range(-0.35, 0.35), 0, randf_range(-0.2, 0.2))
	l.global_position = pos + jitter
	l.scale = Vector3.ONE * scale * 0.4
	var tw := l.create_tween()
	l.set_meta(&"tw", tw)
	tw.set_parallel(true)
	tw.tween_property(l, "scale", Vector3.ONE * scale, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "global_position", l.global_position + Vector3.UP * rise, 0.9).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.chain().tween_property(l, "modulate:a", 0.0, 0.25)
	tw.chain().tween_callback(func(): l.visible = false)

func _on_damage(target: Node, r: DamageResult, pos: Vector3, attacker: Node) -> void:
	var is_player_target := target is Actor and target.team == BH.Team.PLAYER
	if r.evaded:
		_number(pos + Vector3.UP * 0.3, "Evade" if not is_player_target else "Dodged", Color(0.8, 0.85, 0.9), 0.8)
		return
	if r.perfect_block:
		_number(pos + Vector3.UP * 0.4, "Parry!", Color(1.0, 0.95, 0.6), 1.2)
	elif r.blocked:
		_number(pos + Vector3.UP * 0.4, "Blocked", Color(0.75, 0.8, 0.9), 0.8)
	if r.immune:
		_number(pos, "Immune", Color(0.7, 0.7, 0.7), 0.8)
		return
	if r.total <= 0:
		return
	var c := Elements.color(r.dominant_element)
	if r.dominant_element == Elements.PHYSICAL:
		c = Color(1.0, 0.97, 0.9)
	if is_player_target:
		c = Color(1.0, 0.35, 0.3)
	var s := 1.0
	var txt := str(r.total)
	if r.is_crit:
		s = 1.45
		txt = "%d!" % r.total
		c = c.lerp(Color(1.0, 0.8, 0.2), 0.5) if not is_player_target else c
	if r.shattered:
		txt = "Shatter %d" % r.total
	_number(pos, txt, c, s)
	# Feedback strength scales with hit size relative to target HP.
	if target is Actor:
		var rel := clampf(float(r.total) / maxf(1.0, target.max_hp()) * 4.0, 0.0, 1.0)
		var strength := clampf(rel + (0.35 if r.is_crit else 0.0) + r.knockback / 30.0, 0.0, 1.2)
		spawn(VFXLib.hit_burst(pos, r.dominant_element, strength, r.is_crit), pos)
		if target.visual:
			target.visual.flash(Color(1, 1, 1) if not is_player_target else Color(1, 0.3, 0.2), 0.9 if r.is_crit else 0.6)
		if attacker is Actor and attacker.team == BH.Team.PLAYER:
			if r.is_crit or r.knockback >= Actor.HEAVY_KNOCK or r.shattered:
				hitstop(0.075 if r.is_crit else 0.055)
				Events.camera_shake.emit(0.22 + strength * 0.15)
				rumble(0.4, 0.6, 0.12)
			elif strength > 0.3:
				hitstop(0.03)
				Events.camera_shake.emit(0.1)
		elif is_player_target:
			Events.camera_shake.emit(clampf(rel * 0.6, 0.08, 0.35))
			rumble(0.6, 0.3, 0.15)

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
