class_name EschatonReveal
extends Control
## bh-041: the draw of the last work. When Lape's offers hold an Eschaton piece, the table goes dark and an eclipse
## opens over it: a black sun in a white corona, blades of light turning round it and the spectrum turning the other
## way; the screen flashes white, the piece itself bursts out of the eclipse in a spray of star glints, and the word
## ESCHATON slams down letter by letter in chrome. A click (or seven seconds) sends it on to the table, where the
## offer card keeps a smaller shimmer of the same light. `taken` plays a shorter burst when the piece is chosen.
##   EschatonReveal.play(parent, item, func(): ...)       the draw
##   EschatonReveal.play(parent, item, cb, true)          the piece is taken

signal finished

const TITLE := "ESCHATON"
const DIM := 0.9

var item: ItemInstance
var taken := false
var _t := 0.0
var _done := false
var _shook := false
var _flashed := false
var _sparks: Array = []              # [pos, vel, life, size]
var _icon: Texture2D
var _rng := RandomNumberGenerator.new()
var _on_done: Callable

static func play(parent: Node, p_item: ItemInstance, on_done := Callable(), p_taken := false) -> EschatonReveal:
	var r := EschatonReveal.new()
	r.item = p_item
	r.taken = p_taken
	r._on_done = on_done
	parent.add_child(r)
	return r

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	process_mode = Node.PROCESS_MODE_ALWAYS
	z_index = 50

func _ready() -> void:
	_rng.seed = hash(item.base.id) if item else 41
	_icon = item.icon() if item else null
	Audio.play_ui(&"boss_charge" if not taken else &"teleport_whoosh", -4.0)

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed and _t > (1.2 if not taken else 0.4):
		_finish()
		accept_event()

func _unhandled_input(e: InputEvent) -> void:
	if (e.is_action_pressed(&"ui_accept") or e.is_action_pressed(&"ui_cancel")) and _t > 1.2:
		_finish()
		get_viewport().set_input_as_handled()

func _finish() -> void:
	if _done:
		return
	_done = true
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.35)
	tw.tween_callback(func() -> void:
		finished.emit()
		if _on_done.is_valid():
			_on_done.call()
		queue_free())

## When the eclipse bursts: the flash, the shake, the sound and the star glints.
func _burst() -> void:
	_flashed = true
	Audio.play_ui(&"thunder_strike", -6.0)
	Audio.play_ui(&"holy_chime", 0.0)
	Audio.play_ui(&"loot_drop_legendary", 0.0)
	for i in (90 if not taken else 50):
		var a := _rng.randf() * TAU
		var sp := _rng.randf_range(160.0, 760.0)
		_sparks.append([Vector2.ZERO, Vector2(cos(a), sin(a)) * sp, _rng.randf_range(0.7, 2.0), _rng.randf_range(3.0, 11.0)])

func _process(delta: float) -> void:
	_t += delta
	var burst_at := 1.4 if not taken else 0.35
	if not _flashed and _t >= burst_at:
		_burst()
	if not _shook and _t >= burst_at:
		_shook = true
		Events.camera_shake.emit(0.35 if not taken else 0.2)
	for s in _sparks:
		s[0] += s[1] * delta
		s[1] *= pow(0.12, delta)
		s[2] -= delta
	_sparks = _sparks.filter(func(s): return s[2] > 0.0)
	# a slow trickle of fresh glints once it is out
	if _flashed and not _done and _rng.randf() < delta * 14.0:
		var a := _rng.randf() * TAU
		_sparks.append([Vector2(cos(a), sin(a)) * _rng.randf_range(60.0, 220.0), Vector2(cos(a), sin(a)) * 30.0, 1.2, _rng.randf_range(3.0, 8.0)])
	if _t > (7.0 if not taken else 2.6) and not _done:
		_finish()
	queue_redraw()

func _spectrum(u: float) -> Color:
	return Color(0.5 + 0.5 * cos(TAU * u), 0.5 + 0.5 * cos(TAU * (u + 0.33)), 0.5 + 0.5 * cos(TAU * (u + 0.67)))

func _star(p: Vector2, s: float, col: Color) -> void:
	var w := maxf(1.0, s * 0.18)
	draw_colored_polygon(PackedVector2Array([p + Vector2(-s, 0), p + Vector2(-w, -w), p + Vector2(0, -s), p + Vector2(w, -w),
		p + Vector2(s, 0), p + Vector2(w, w), p + Vector2(0, s), p + Vector2(-w, w)]), col)
	draw_circle(p, w * 1.2, Color(col, col.a * 0.6))

func _draw() -> void:
	var vp := size
	var c := vp * Vector2(0.5, 0.42)
	var burst_at := 1.4 if not taken else 0.35
	var into := clampf(_t / 0.6, 0.0, 1.0)
	draw_rect(Rect2(Vector2.ZERO, vp), Color(0.0, 0.0, 0.02, DIM * into * (0.7 if taken else 1.0)))
	# the eclipse grows, then holds
	var grow := clampf((_t - 0.25) / (burst_at - 0.25), 0.0, 1.0)
	grow = 1.0 - pow(1.0 - grow, 3.0)
	var R := lerpf(10.0, 150.0 if not taken else 110.0, grow)
	if _flashed:
		R *= 1.0 + 0.04 * sin(_t * 3.0)
	# spectrum ring turning one way
	for i in 64:
		var a0 := TAU * float(i) / 64.0 - _t * 0.6
		var col := _spectrum(float(i) / 64.0 - _t * 0.1)
		col.a = 0.55 * grow
		draw_arc(c, R * 1.42, a0, a0 + TAU / 64.0 + 0.01, 3, col, maxf(2.0, R * 0.06))
	# blades of light turning the other way
	for i in 16:
		var a := TAU * float(i) / 16.0 + _t * 0.35
		var L := R * (2.4 if i % 2 == 0 else 1.75) * (1.0 + (0.12 * sin(_t * 4.0 + i) if _flashed else 0.0))
		var d := Vector2(cos(a), sin(a))
		var n := Vector2(-d.y, d.x)
		var base := c + d * R * 1.08
		draw_colored_polygon(PackedVector2Array([base + n * R * 0.07, c + d * L, base - n * R * 0.07]), Color(0.95, 0.97, 1.0, 0.75 * grow))
	# the corona, then the black sun
	for k in 6:
		draw_circle(c, R * (1.32 - k * 0.05), Color(0.85, 0.9, 1.0, 0.07 * grow))
	draw_arc(c, R * 1.04, 0.0, TAU, 96, Color(1, 1, 1, 0.95 * grow), maxf(2.0, R * 0.05), true)
	draw_circle(c, R, Color(0.01, 0.01, 0.02, 1.0 * grow))
	# the piece bursts out of the eclipse
	if _flashed and _icon:
		var k2 := clampf((_t - burst_at) / 0.55, 0.0, 1.0)
		var ov := 1.0 + 0.35 * sin(k2 * PI) if k2 < 1.0 else 1.0
		var isz := R * 1.35 * ov * (1.0 - pow(1.0 - k2, 3.0))
		for g in 5:
			draw_circle(c, isz * (0.5 - g * 0.07), Color(0.8, 0.86, 1.0, 0.09 * k2))
		draw_texture_rect(_icon, Rect2(c - Vector2(isz, isz) * 0.5, Vector2(isz, isz)), false)
	# star glints
	for s in _sparks:
		var f: float = clampf(float(s[2]), 0.0, 1.0)
		_star(c + s[0], float(s[3]) * (0.6 + 0.4 * f), Color(1, 1, 1, f))
	# the white flash
	if _flashed:
		var fl := clampf(1.0 - (_t - burst_at) / 0.55, 0.0, 1.0)
		if fl > 0.0:
			draw_rect(Rect2(Vector2.ZERO, vp), Color(1, 1, 1, fl * (0.9 if not taken else 0.6)))
	# the word, slammed down letter by letter in chrome
	var font := UITheme.title_font()
	if _flashed and font:
		var fs := 96 if not taken else 64
		var word := TITLE
		var total := font.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 14.0 * (word.length() - 1)
		var x := c.x - total * 0.5
		var y := c.y + R * 2.15 + fs * 0.5
		for i in word.length():
			var ch := word[i]
			var lt := clampf((_t - burst_at - 0.12 - i * 0.07) / 0.22, 0.0, 1.0)
			var cw := font.get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			if lt > 0.0:
				var sc := lerpf(2.4, 1.0, 1.0 - pow(1.0 - lt, 2.0))
				var col := Color(0.92, 0.95, 1.0).lerp(_spectrum(float(i) / word.length() + _t * 0.25), 0.28)
				col.a = lt
				var p := Vector2(x + cw * 0.5, y)
				draw_set_transform(p, 0.0, Vector2(sc, sc))
				draw_string_outline(font, Vector2(-cw * 0.5, 0), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 10, Color(0, 0, 0, 0.9 * lt))
				draw_string(font, Vector2(-cw * 0.5, 0), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
			x += cw + 14.0
		var sub := "The last work · %s" % (item.display_name() if item else "") if not taken else "%s is yours" % (item.display_name() if item else "")
		var st := clampf((_t - burst_at - 0.9) / 0.5, 0.0, 1.0)
		if st > 0.0:
			var sfs := 30 if not taken else 26
			var sw := UITheme.body_bold().get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, sfs).x
			var sp := Vector2(c.x - sw * 0.5, y + fs * 0.75)
			draw_string_outline(UITheme.body_bold(), sp, sub, HORIZONTAL_ALIGNMENT_LEFT, -1, sfs, 8, Color(0, 0, 0, 0.9 * st))
			draw_string(UITheme.body_bold(), sp, sub, HORIZONTAL_ALIGNMENT_LEFT, -1, sfs, Color(BH.rarity_color(BH.Rarity.ESCHATON), st))
			if not taken and _t > burst_at + 1.6:
				var hint := "Click to see it on Lape's table"
				var hp := Vector2(c.x - UITheme.body_font().get_string_size(hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 20).x * 0.5, sp.y + 52.0)
				draw_string(UITheme.body_font(), hp, hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1, 1, 1, 0.5 + 0.3 * sin(_t * 3.0)))
