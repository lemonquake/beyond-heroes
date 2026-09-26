class_name ArtBar
extends Control
## A painted bar: 9-slice frame from the UI art with the fill drawn inside the frame's transparent window. Smooth fill,
## a pale lag segment for recent losses, optional segment ticks and centred text.

var frame_path := "hud/bar_frame_target.png"
var fill_color := Color(0.85, 0.15, 0.12)
var lag_color := Color(1.0, 0.85, 0.6, 0.85)
var ratio := 1.0
var text := ""
var text_size := 15
var ticks := 0                       # draw N-1 dividers (e.g. boss phases)
var tick_marks: Array = []           # explicit tick fractions
var _shown := 1.0
var _lag := 1.0
var _hold := 0.0

func _init(p_frame := "hud/bar_frame_target.png", p_color := Color(0.85, 0.15, 0.12), height := 32.0) -> void:
	frame_path = p_frame
	fill_color = p_color
	custom_minimum_size = Vector2(0, height)
	mouse_filter = Control.MOUSE_FILTER_PASS

func set_ratio(r: float, instant := false) -> void:
	r = clampf(r, 0.0, 1.0)
	if r < ratio - 0.001:
		_hold = 0.4
	ratio = r
	if instant:
		_shown = r
		_lag = r
	queue_redraw()

func _process(delta: float) -> void:
	var prev := _shown
	_shown = lerpf(_shown, ratio, 1.0 - exp(-16.0 * delta))
	if _hold > 0.0:
		_hold -= delta
	else:
		_lag = lerpf(_lag, _shown, 1.0 - exp(-4.0 * delta))
	if _lag < _shown:
		_lag = _shown
	if absf(prev - _shown) > 0.0001 or absf(_lag - _shown) > 0.0001:
		queue_redraw()

func _window() -> Rect2:
	# the fill window in logical px: manifest window scaled to the drawn height; x inset scaled likewise
	var m := UIArt.meta(frame_path)
	var ts: Array = m.get("size", [512, 64])
	var w: Array = m.get("window", [0, 0, ts[0], ts[1]])
	var k := size.y / float(ts[1])
	var left := float(w[0]) * k
	var right := (float(ts[0]) - float(w[2])) * k
	return Rect2(Vector2(left, float(w[1]) * k), Vector2(size.x - left - right, (float(w[3]) - float(w[1])) * k))

func _draw() -> void:
	var win := _window()
	draw_rect(win, Color(0.03, 0.02, 0.02, 0.9))
	var fill_tex := UIArt.tex("hud/bar_fill.png")
	if _lag > _shown:
		draw_rect(Rect2(win.position + Vector2(win.size.x * _shown, 0), Vector2(win.size.x * (_lag - _shown), win.size.y)), lag_color)
	var fr := Rect2(win.position, Vector2(win.size.x * _shown, win.size.y))
	if fill_tex:
		draw_texture_rect(fill_tex, fr, false, fill_color)
	else:
		draw_rect(fr, fill_color)
	var marks := tick_marks.duplicate()
	if marks.is_empty() and ticks > 1:
		for i in range(1, ticks):
			marks.append(float(i) / float(ticks))
	for t in marks:
		var x := win.position.x + win.size.x * float(t)
		draw_line(Vector2(x, win.position.y), Vector2(x, win.end.y), Color(0, 0, 0, 0.7), 2.0)
	# frame: height matches the control; drawn with the frame's own vertical proportions
	var m := UIArt.meta(frame_path)
	var ts: Array = m.get("size", [512, 64])
	var sb := UIArt.style(frame_path, [0, 0, 0, 0])
	var s0 := sb.draw_scale
	sb.draw_scale = size.y / float(ts[1])
	draw_style_box(sb, Rect2(Vector2.ZERO, size))
	sb.draw_scale = s0
	if text != "":
		var font := UITheme.number_font()
		var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size).x
		var p := Vector2((size.x - tw) * 0.5, win.get_center().y + text_size * 0.36)
		draw_string_outline(font, p, text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size, 4, Color(0, 0, 0, 0.95))
		draw_string(font, p, text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size, UITheme.PARCHMENT)
