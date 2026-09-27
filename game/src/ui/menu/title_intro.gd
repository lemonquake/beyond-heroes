class_name TitleIntro
extends Control
## Boot title sequence (bh-009), played once per launch before the title screen appears:
##   0.00  charge   — streaks of aether rush into a growing core of light, the ground rumbles
##   0.85  release  — the core bursts: flash, shockwave
##   0.90  BEYOND   — six letters slam down one after another, each with sparks and a jolt
##   1.42  HEROES   — the second word crashes in from above the camera: white flash, double shockwave, lightning,
##                    a storm of sparks, heavy shake, god rays wake behind the wordmark
##   1.95  the ornament line draws outward from the gem, 2.55 a gold sheen sweeps the letters
##   3.15  "by Aljay Leodones" — a blade-slash cuts across and reveals the byline
##   4.70  the wordmark and byline fly to their places on the title screen while the black lifts off the live menu
## Any key, click or tap skips to the hand-off. Pure 2D (one additive draw layer + a handful of textures), so a phone
## in efficiency mode plays it at full speed. Emits `finished` when the menu owns the screen.

signal finished

const LOGO := "menu/title_logo.png"
## Column cuts of the 1600 x 420 wordmark between its letters (midpoints of the gaps): B E Y O N D | H E R O E S.
const CUTS := [0, 213, 311, 423, 548, 667, 820, 976, 1073, 1192, 1318, 1417, 1600]
const BAND_H := 262.0               # letter band of the image; the ornament line sits below it
const IMG := Vector2(1600, 420)
const GOLD := Color(1.0, 0.72, 0.28)
const AETHER := Color(0.45, 0.9, 1.0)
const T_OUTRO := 4.9
const OUTRO_LEN := 0.85

## Where the title screen shows the wordmark and byline (canvas coordinates), set before `start()`.
var target_logo := Rect2(70, 70, 800, 210)
var target_byline := Vector2(80, 282)
var byline_scale := 1.0 / 3.0       # final Label scale (the menu byline is 20 px, this label is drawn at 60)

var _t := 0.0
var _running := false
var _outro := false
var _done := false
var _k := 1.0                       # screen px per image px while the wordmark is centre stage
var _origin := Vector2.ZERO         # top-left of the centred wordmark
var _center := Vector2.ZERO         # centre of the letter band
var _events: Array = []             # [time, Callable], fired in order as the clock passes them
var _tweens: Array[Tween] = []

var _bg: ColorRect
var _vig: TextureRect
var _stage: Control                 # everything that shakes: letters, ornament, full wordmark, byline
var _fx: Control                    # additive effects layer
var _flash: ColorRect
var _letters: Array[TextureRect] = []
var _heroes_group: Control
var _orn_clip: Control
var _orn: TextureRect
var _logo: TextureRect              # the whole wordmark (after the letters have landed), carries the sheen
var _sheen: ShaderMaterial
var _by_clip: Control
var _byline: Label
var _glow: Texture2D

# effects state
var _shake := 0.0
var _shake_off := Vector2.ZERO
var _core := 0.0                    # charge core radius (0 = off)
var _charging := false
var _rays := 0.0                    # god-ray strength
var _ray_rot := 0.0
var _halo := 0.0                    # warm glow behind the wordmark
var _streaks: Array = []            # [pos, vel, len, col]
var _sparks: Array = []             # [pos, vel, life, max_life, col, width]
var _rings: Array = []              # [pos, age, dur, max_r, width, col]
var _bolts: Array = []              # [points, age, dur]
var _embers: Array = []             # [pos, vel, life, max_life, r]
var _slash := -1.0                  # byline slash progress 0..1 (-1 off)
var _rng := RandomNumberGenerator.new()

## Flying letters draw only their solid metal (the soft halo around the wordmark would show the cut lines between
## slices) and can burn white-hot on impact; the whole wordmark with its halo cross-fades in once they have landed.
const LETTER := """
shader_type canvas_item;
uniform float hot = 0.0;
void fragment() {
	vec4 c = COLOR;
	float solid = smoothstep(0.45, 0.8, c.a);
	c.rgb = mix(c.rgb, vec3(1.0, 0.97, 0.9), hot * solid);
	c.a *= solid;
	COLOR = c;
}
"""

const SHEEN := """
shader_type canvas_item;
uniform float sweep = -0.4;
uniform float strength = 0.0;
void fragment() {
	vec4 c = COLOR;
	float x = UV.x + (1.0 - UV.y) * 0.18;
	float band = smoothstep(0.07, 0.0, abs(x - sweep));
	float solid = smoothstep(0.6, 0.95, c.a);
	c.rgb += vec3(1.0, 0.93, 0.75) * band * strength * solid;
	COLOR = c;
}
"""

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_rng.seed = 20260928

func _ready() -> void:
	var vp := get_viewport_rect().size
	_bg = ColorRect.new()
	_bg.color = Color(0.012, 0.009, 0.014)
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)
	_vig = TextureRect.new()
	_vig.texture = UIArt.tex("menu/vignette_menu.png")
	_vig.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_vig.stretch_mode = TextureRect.STRETCH_SCALE
	_vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_vig)
	_glow = _make_glow()
	var tex := UIArt.tex(LOGO)
	_k = minf(vp.x * 0.8, 1500.0) / IMG.x
	_origin = Vector2((vp.x - IMG.x * _k) * 0.5, vp.y * 0.42 - BAND_H * 0.5 * _k)
	_center = _origin + Vector2(IMG.x * 0.5, BAND_H * 0.55) * _k
	# additive effects under the wordmark
	_fx = Control.new()
	_fx.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var add := CanvasItemMaterial.new()
	add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_fx.material = add
	_fx.draw.connect(_draw_fx)
	add_child(_fx)
	_stage = Control.new()
	_stage.set_anchors_preset(Control.PRESET_FULL_RECT)
	_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stage)
	# the ornament line, revealed from the gem outward
	_orn_clip = Control.new()
	_orn_clip.clip_contents = true
	_orn_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_orn_clip.position = _origin + Vector2(IMG.x * 0.5, BAND_H) * _k
	_orn_clip.size = Vector2(0, (IMG.y - BAND_H) * _k)
	_stage.add_child(_orn_clip)
	_orn = _slice(tex, Rect2(0, BAND_H, IMG.x, IMG.y - BAND_H))
	_orn.position = Vector2(-IMG.x * 0.5 * _k, 0)
	_orn_clip.add_child(_orn)
	# the twelve letters; HEROES lives in a group so the word can crash in as one
	var letter_shader := Shader.new()
	letter_shader.code = LETTER
	_heroes_group = Control.new()
	_heroes_group.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_heroes_group.position = _origin + Vector2(CUTS[6], 0) * _k
	_heroes_group.size = Vector2(CUTS[12] - CUTS[6], BAND_H) * _k
	_heroes_group.pivot_offset = _heroes_group.size * 0.5
	for i in 12:
		var r := Rect2(CUTS[i], 0, CUTS[i + 1] - CUTS[i], BAND_H)
		var l := _slice(tex, r)
		if i < 6:
			l.position = _origin + r.position * _k
			_stage.add_child(l)
		else:
			l.position = (r.position - Vector2(CUTS[6], 0)) * _k
			_heroes_group.add_child(l)
		l.pivot_offset = l.size * 0.5
		l.modulate.a = 0.0
		var lm := ShaderMaterial.new()
		lm.shader = letter_shader
		l.material = lm
		_letters.append(l)
	_stage.add_child(_heroes_group)
	# the whole wordmark with the sheen, swapped in once every piece has landed (it looks identical)
	_logo = TextureRect.new()
	_logo.texture = tex
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_SCALE
	_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_logo.position = _origin
	_logo.size = IMG * _k
	_sheen = ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = SHEEN
	_sheen.shader = sh
	_logo.material = _sheen
	_logo.visible = false
	_stage.add_child(_logo)
	# byline, revealed by the slash
	_byline = UITheme.label("by Aljay Leodones", 60, UITheme.PARCHMENT, UITheme.body_font())
	_byline.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_byline.add_theme_constant_override("outline_size", 15)
	_byline.add_theme_constant_override("shadow_offset_y", 4)
	_byline.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	_byline.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_by_clip = Control.new()
	_by_clip.clip_contents = true
	_by_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_by_clip.add_child(_byline)
	_stage.add_child(_by_clip)
	_byline.reset_size()                # measured inside the tree, with its theme and font size
	var bs := _by_scale()
	_byline.scale = Vector2.ONE * bs
	_byline.position = BY_PAD * bs
	_by_clip.size = Vector2(0, _by_full(bs).y)
	_by_clip.position = Vector2(vp.x * 0.5 - _by_full(bs).x * 0.5, _origin.y + IMG.y * 0.76 * _k)
	_flash = ColorRect.new()
	_flash.color = Color(1.0, 0.97, 0.9)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_flash.modulate.a = 0.0
	add_child(_flash)

## Room around the byline inside its clip (outline, shadow), in label pixels.
const BY_PAD := Vector2(16, 10)

## The byline clip's full size at label scale `s`.
func _by_full(s: float) -> Vector2:
	return (_byline.size + BY_PAD * 2.0) * s

## Byline size while centre stage: in proportion to the wordmark.
func _by_scale() -> float:
	return clampf(_k, 0.5, 1.0)

func _slice(tex: Texture2D, region: Rect2) -> TextureRect:
	var at := AtlasTexture.new()
	at.atlas = tex
	at.region = region
	var r := TextureRect.new()
	r.texture = at
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.size = region.size * _k
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r

static func _make_glow() -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.25, Color(1, 1, 1, 0.55))
	g.add_point(0.6, Color(1, 1, 1, 0.12))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(1.0, 0.5)
	t.width = 128
	t.height = 128
	return t

# ---- timeline ------------------------------------------------------------------------------------------------------

func start() -> void:
	_events = [
		[0.0, _begin_charge],
		[0.85, _release],
		[0.9, _slam.bind(0)], [0.97, _slam.bind(1)], [1.04, _slam.bind(2)],
		[1.11, _slam.bind(3)], [1.18, _slam.bind(4)], [1.25, _slam.bind(5)],
		[1.42, _heroes_crash],
		[1.56, _heroes_impact],
		[1.95, _ornament],
		[2.5, _crossfade],
		[2.85, _sweep],
		[3.3, _byline_slash],
		[T_OUTRO, _begin_outro],
	]
	_running = true

func _process(delta: float) -> void:
	if not _running:
		return
	delta = minf(delta, 0.1)           # a hitch (first frame, shader compile) must not skip half the show; a slow phone still finishes
	_t += delta
	while not _events.is_empty() and _t >= float(_events[0][0]):
		var ev: Array = _events.pop_front()
		(ev[1] as Callable).call()
	_step_fx(delta)
	_shake = maxf(0.0, _shake - delta * 55.0)
	_shake_off = Vector2(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1)) * _shake * (0.0 if Settings.reduced_motion else 1.0)
	_stage.position = _shake_off
	_fx.queue_redraw()

func _gui_input(e: InputEvent) -> void:
	if _skip_event(e):
		skip()
		accept_event()

func _unhandled_input(e: InputEvent) -> void:
	if _skip_event(e):
		skip()
		get_viewport().set_input_as_handled()

static func _skip_event(e: InputEvent) -> bool:
	return (e is InputEventKey and e.pressed and not e.echo) or (e is InputEventMouseButton and e.pressed) \
		or (e is InputEventScreenTouch and e.pressed) or (e is InputEventJoypadButton and e.pressed)

## Jump to the finished wordmark and hand over to the menu at once.
func skip() -> void:
	if _outro or _done or not _running:
		return
	for tw in _tweens:
		if tw and tw.is_valid():
			tw.kill()
	_tweens.clear()
	_events.clear()
	for l in _letters:
		l.visible = false
	_orn_clip.visible = false
	_logo.visible = true
	_logo.modulate = Color.WHITE
	_by_clip.size.x = _by_full(_by_scale()).x
	_byline.modulate = Color.WHITE
	_flash.modulate.a = 0.0
	_charging = false
	_core = 0.0
	_streaks.clear()
	_halo = maxf(_halo, 0.5)
	_rays = maxf(_rays, 0.5)
	_begin_outro(0.5)

func _tw() -> Tween:
	var tw := create_tween()
	_tweens.append(tw)
	return tw

func _sfx(name: StringName, db := 0.0) -> void:
	Audio.play(name, db, 0.03)

# ---- beats ---------------------------------------------------------------------------------------------------------

func _begin_charge() -> void:
	_charging = true
	_sfx(&"earth_quake", -9.0)
	_sfx(&"arcane_charge", -3.0)
	_sfx(&"meteor_fall", -8.0)

func _release() -> void:
	_charging = false
	_streaks.clear()
	_core = 0.0
	_flash_to(0.55, 0.3)
	_ring(_center, 0.45, 520.0 * _k, 10.0, AETHER)
	_burst(_center, 50, 900.0, AETHER.lerp(Color.WHITE, 0.4), 0.5)
	_shake = 10.0
	_sfx(&"thunder_strike", -2.0)

func _slam(i: int) -> void:
	var l := _letters[i]
	l.scale = Vector2.ONE * 2.3
	l.rotation = deg_to_rad(_rng.randf_range(-9.0, 9.0))
	l.modulate.a = 0.0
	_hot(l, 1.0, 0.0)
	var tw := _tw().set_parallel()
	tw.tween_property(l, "scale", Vector2.ONE, 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_property(l, "rotation", 0.0, 0.12).set_ease(Tween.EASE_IN)
	tw.tween_property(l, "modulate:a", 1.0, 0.07)
	tw.chain().tween_callback(func() -> void:
		var foot := l.global_position + Vector2(l.size.x * 0.5, l.size.y * 0.86)
		_burst(foot, 16, 520.0, GOLD, 0.35, Vector2.UP)
		_ring(foot, 0.3, 90.0 * _k, 4.0, GOLD)
		_shake = maxf(_shake, 9.0)
		_sfx(&"hit_heavy", -9.0))
	tw.chain().tween_method(func(h: float) -> void: _hot(l, h, 0.0), 1.0, 0.0, 0.35)

func _heroes_crash() -> void:
	for i in range(6, 12):
		_letters[i].modulate.a = 1.0
		_hot(_letters[i], 1.0, 0.0)
		_letters[i].scale = Vector2.ONE
	_heroes_group.scale = Vector2.ONE * 3.6
	_heroes_group.modulate.a = 0.0
	var tw := _tw().set_parallel()
	tw.tween_property(_heroes_group, "scale", Vector2.ONE, 0.14).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_IN)
	tw.tween_property(_heroes_group, "modulate:a", 1.0, 0.08)
	_sfx(&"fire_whoosh", -4.0)

func _heroes_impact() -> void:
	_flash_to(1.0, 0.5)
	_shake = 26.0
	var hc := _heroes_group.global_position + _heroes_group.size * 0.5
	_ring(hc, 0.55, 900.0 * _k, 16.0, Color(1, 0.9, 0.7))
	_ring(_center, 0.8, 1300.0 * _k, 8.0, AETHER)
	_burst(hc, 110, 1400.0, GOLD, 0.8)
	_burst(_center, 60, 1000.0, AETHER, 0.7)
	for i in 7:
		var a := -PI * 0.5 + (i - 3) * 0.55 + _rng.randf_range(-0.15, 0.15)
		var from := _center + Vector2(cos(a), sin(a)) * Vector2(IMG.x * 0.36, BAND_H * 0.45) * _k
		_bolt(from, a, _rng.randf_range(260.0, 480.0) * _k)
	for i in range(6, 12):
		var li := _letters[i]
		_tw().tween_method(func(h: float) -> void: _hot(li, h, 0.0), 1.0, 0.0, 0.5)
	# the word settles with a small recoil
	var tw := _tw()
	tw.tween_property(_heroes_group, "scale", Vector2.ONE * 1.035, 0.07)
	tw.tween_property(_heroes_group, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_tw().tween_property(self, "_rays", 1.0, 0.6)
	_tw().tween_property(self, "_halo", 1.0, 0.25)
	_sfx(&"boss_slam", 0.0)
	_sfx(&"meteor_impact", -3.0)
	_sfx(&"crit_hit", -4.0)

func _ornament() -> void:
	var full := IMG.x * _k
	var left := _origin.x + full * 0.5
	var tw := _tw()
	tw.tween_method(func(f: float) -> void:
		_orn_clip.position.x = left - full * 0.5 * f
		_orn_clip.size.x = full * f
		_orn.position.x = -(_orn_clip.position.x - _origin.x), 0.0, 1.0, 0.55).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	var gem := _origin + Vector2(IMG.x * 0.5, 283) * _k
	_burst(gem, 30, 600.0, AETHER, 0.5)
	_ring(gem, 0.4, 160.0 * _k, 5.0, AETHER)
	_sfx(&"holy_chime", -4.0)
	_tw().tween_property(self, "_halo", 0.55, 1.2)

func _hot(l: TextureRect, h: float, _unused: float) -> void:
	(l.material as ShaderMaterial).set_shader_parameter("hot", h)

## The whole wordmark (with its glow halo and the drawn ornament) fades in over the landed pieces.
func _crossfade() -> void:
	_logo.visible = true
	_logo.modulate.a = 0.0
	var tw := _tw()
	tw.tween_property(_logo, "modulate:a", 1.0, 0.3)
	tw.tween_callback(func() -> void:
		for l in _letters:
			l.visible = false
		_orn_clip.visible = false)

func _sweep() -> void:
	_sheen.set_shader_parameter("strength", 1.6)
	var tw := _tw()
	tw.tween_method(func(x: float) -> void: _sheen.set_shader_parameter("sweep", x), -0.3, 1.35, 0.75).set_trans(Tween.TRANS_SINE)
	_sfx(&"blink", -8.0)

func _byline_slash() -> void:
	_slash = 0.0
	var w := _by_full(_by_scale()).x
	var tw := _tw()
	tw.tween_method(func(f: float) -> void:
		_slash = f
		_by_clip.size.x = w * f, 0.0, 1.0, 0.22).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		_slash = -1.0
		var end := _by_clip.global_position + Vector2(w, _by_clip.size.y * 0.5)
		_burst(end, 22, 520.0, Color(1, 0.95, 0.85), 0.35)
		_shake = maxf(_shake, 5.0))
	_byline.modulate = Color(2.2, 2.2, 2.2)
	tw.tween_property(_byline, "modulate", Color.WHITE, 0.5)
	_sfx(&"swing_light", -2.0)

## Hand-off: the wordmark and byline glide to the title screen's own and the black lifts off the live menu.
func _begin_outro(dur := OUTRO_LEN) -> void:
	if _outro:
		return
	_outro = true
	var tw := _tw().set_parallel()
	tw.tween_property(_logo, "position", target_logo.position, dur).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_logo, "size", target_logo.size, dur).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_by_clip, "position", target_byline - BY_PAD * byline_scale, dur).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(s: float) -> void:
		_byline.scale = Vector2.ONE * s
		_byline.position = BY_PAD * s
		_by_clip.size = _by_full(s), _by_scale(), byline_scale, dur).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(_bg, "modulate:a", 0.0, dur).set_delay(dur * 0.25)
	tw.tween_property(_vig, "modulate:a", 0.0, dur).set_delay(dur * 0.25)
	tw.tween_property(self, "_rays", 0.0, dur * 0.7)
	tw.tween_property(self, "_halo", 0.0, dur * 0.8)
	tw.chain().tween_callback(_finish)

func _finish() -> void:
	if _done:
		return
	_done = true
	_running = false
	finished.emit()
	queue_free()

# ---- effects -------------------------------------------------------------------------------------------------------

func _flash_to(a: float, dur: float) -> void:
	_flash.modulate.a = a if not Settings.reduced_motion else a * 0.4
	_tw().tween_property(_flash, "modulate:a", 0.0, dur).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)

func _burst(at: Vector2, n: int, speed: float, col: Color, life: float, bias := Vector2.ZERO) -> void:
	for i in n:
		var a := _rng.randf() * TAU
		var dir := Vector2(cos(a), sin(a))
		if bias != Vector2.ZERO:
			dir = (dir + bias * 1.2).normalized()
		var v := dir * speed * _rng.randf_range(0.25, 1.0) * _k
		var c := col.lerp(Color.WHITE, _rng.randf() * 0.5)
		_sparks.append([at, v, life * _rng.randf_range(0.5, 1.0), life, c, _rng.randf_range(1.5, 3.5)])

func _ring(at: Vector2, dur: float, max_r: float, width: float, col: Color) -> void:
	_rings.append([at, 0.0, dur, max_r, width, col])

func _bolt(from: Vector2, ang: float, length: float) -> void:
	var pts := PackedVector2Array([from])
	var p := from
	var n := 9
	for i in n:
		var a := ang + _rng.randf_range(-0.7, 0.7)
		p += Vector2(cos(a), sin(a)) * length / n
		pts.append(p)
	_bolts.append([pts, 0.0, 0.32])
	if length > 200.0 * _k:     # one fork
		var mid := pts[4]
		var fork := PackedVector2Array([mid])
		var q := mid
		for i in 4:
			var a2 := ang + 0.8 * (1 if _rng.randf() < 0.5 else -1) + _rng.randf_range(-0.5, 0.5)
			q += Vector2(cos(a2), sin(a2)) * length * 0.35 / 4
			fork.append(q)
		_bolts.append([fork, 0.0, 0.26])

func _step_fx(dt: float) -> void:
	var vp := get_viewport_rect().size
	if _charging:
		_core = minf(_core + dt * 190.0 * _k, 150.0 * _k)
		for i in 7:
			var a := _rng.randf() * TAU
			var r := vp.length() * 0.55
			var pos := _center + Vector2(cos(a), sin(a)) * r
			var col := GOLD if _rng.randf() < 0.55 else AETHER
			_streaks.append([pos, -Vector2(cos(a), sin(a)) * _rng.randf_range(700.0, 1100.0), _rng.randf_range(50.0, 170.0), col])
	var i := 0
	while i < _streaks.size():
		var s: Array = _streaks[i]
		s[1] = (s[1] as Vector2) * (1.0 + dt * 3.2)       # accelerate into the core
		s[0] = (s[0] as Vector2) + (s[1] as Vector2) * dt
		if (s[0] as Vector2).distance_to(_center) < 26.0 or ((s[0] as Vector2) - _center).dot(s[1]) > 0.0:
			_streaks.remove_at(i)
			continue
		i += 1
	i = 0
	while i < _sparks.size():
		var sp: Array = _sparks[i]
		sp[2] = float(sp[2]) - dt
		if float(sp[2]) <= 0.0:
			_sparks.remove_at(i)
			continue
		sp[1] = (sp[1] as Vector2) * maxf(0.0, 1.0 - dt * 2.2) + Vector2(0, 700.0 * _k) * dt
		sp[0] = (sp[0] as Vector2) + (sp[1] as Vector2) * dt
		i += 1
	i = 0
	while i < _rings.size():
		_rings[i][1] = float(_rings[i][1]) + dt
		if float(_rings[i][1]) >= float(_rings[i][2]):
			_rings.remove_at(i)
			continue
		i += 1
	i = 0
	while i < _bolts.size():
		_bolts[i][1] = float(_bolts[i][1]) + dt
		if float(_bolts[i][1]) >= float(_bolts[i][2]):
			_bolts.remove_at(i)
			continue
		i += 1
	# embers rise once the wordmark has landed
	if _halo > 0.05 and _embers.size() < 70 and _rng.randf() < dt * 40.0:
		_embers.append([Vector2(_rng.randf() * vp.x, vp.y + 10.0), Vector2(_rng.randf_range(-20, 20), -_rng.randf_range(60, 150)),
			0.0, _rng.randf_range(2.5, 5.0), _rng.randf_range(1.2, 3.0)])
	i = 0
	while i < _embers.size():
		var e: Array = _embers[i]
		e[2] = float(e[2]) + dt
		if float(e[2]) >= float(e[3]):
			_embers.remove_at(i)
			continue
		e[0] = (e[0] as Vector2) + ((e[1] as Vector2) + Vector2(sin(_t * 2.0 + i) * 25.0, 0)) * dt
		i += 1
	_ray_rot += dt * 0.08

func _draw_fx() -> void:
	_fx.draw_set_transform(_shake_off)
	var c := _center
	# god rays behind the wordmark
	if _rays > 0.01:
		var n := 16
		var reach := get_viewport_rect().size.x * 0.75
		for k in n:
			var a := _ray_rot + TAU * k / n + sin(k * 7.3) * 0.2
			var wdt := 0.04 + 0.05 * absf(sin(k * 3.1))
			var col := GOLD if k % 3 else AETHER
			var p0 := c
			var p1 := c + Vector2(cos(a - wdt), sin(a - wdt)) * reach
			var p2 := c + Vector2(cos(a + wdt), sin(a + wdt)) * reach
			_fx.draw_polygon(PackedVector2Array([p0, p1, p2]),
				PackedColorArray([Color(col, 0.16 * _rays), Color(col, 0.0), Color(col, 0.0)]))
	# warm halo behind the letters
	if _halo > 0.01:
		var hs := Vector2(IMG.x * 1.15, BAND_H * 2.6) * _k
		_fx.draw_texture_rect(_glow, Rect2(c - hs * 0.5, hs), false, Color(GOLD, 0.35 * _halo))
		var hs2 := Vector2(IMG.x * 0.7, BAND_H * 1.2) * _k
		_fx.draw_texture_rect(_glow, Rect2(c - hs2 * 0.5, hs2), false, Color(AETHER, 0.18 * _halo))
	# charge core
	if _core > 0.0:
		var flick := 1.0 + 0.12 * sin(_t * 60.0)
		var r := _core * flick
		_fx.draw_texture_rect(_glow, Rect2(c - Vector2(r, r) * 2.0, Vector2(r, r) * 4.0), false, Color(AETHER, 0.5))
		_fx.draw_texture_rect(_glow, Rect2(c - Vector2(r, r), Vector2(r, r) * 2.0), false, Color(1, 0.95, 0.85, 0.95))
	for s in _streaks:
		var p: Vector2 = s[0]
		var dir: Vector2 = (s[1] as Vector2).normalized()
		_fx.draw_line(p, p - dir * float(s[2]), Color(s[3], 0.85), 2.5)
		_fx.draw_line(p, p - dir * float(s[2]) * 0.4, Color(1, 1, 1, 0.7), 1.2)
	for rg in _rings:
		var f := float(rg[1]) / float(rg[2])
		var r := float(rg[3]) * (1.0 - pow(1.0 - f, 3.0))
		var col: Color = rg[5]
		_fx.draw_arc(rg[0], r, 0.0, TAU, 72, Color(col, (1.0 - f) * 0.9), float(rg[4]) * (1.0 - f * 0.6), true)
	for b in _bolts:
		var f2 := float(b[1]) / float(b[2])
		var a2 := (1.0 - f2) * (0.6 + 0.4 * _rng.randf())
		_fx.draw_polyline(b[0], Color(AETHER, a2 * 0.5), 9.0 * _k + 3.0, true)
		_fx.draw_polyline(b[0], Color(1, 1, 1, a2), 2.5, true)
	for sp in _sparks:
		var p3: Vector2 = sp[0]
		var v: Vector2 = sp[1]
		var life := clampf(float(sp[2]) / float(sp[3]), 0.0, 1.0)
		var col3: Color = sp[4]
		_fx.draw_line(p3, p3 - v * 0.035, Color(col3, life), float(sp[5]) * (0.5 + life))
	for e in _embers:
		var lf := float(e[2]) / float(e[3])
		var a3 := sin(lf * PI) * 0.8
		_fx.draw_circle(e[0], float(e[4]), Color(1.0, 0.55, 0.2, a3))
	# the byline slash: a white-hot blade line racing left to right with a fading trail
	if _slash >= 0.0:
		var y := _by_clip.global_position.y + _by_clip.size.y * 0.55
		var x0 := _by_clip.global_position.x - 60.0
		var w := _by_full(_by_scale()).x + 120.0
		var head := x0 + w * _slash
		_fx.draw_line(Vector2(x0, y), Vector2(head, y), Color(GOLD, 0.35), 6.0)
		_fx.draw_line(Vector2(maxf(x0, head - 220.0), y), Vector2(head, y), Color(1, 1, 1, 0.95), 3.0)
		_fx.draw_texture_rect(_glow, Rect2(Vector2(head - 40, y - 40), Vector2(80, 80)), false, Color(1, 0.95, 0.8, 0.9))
