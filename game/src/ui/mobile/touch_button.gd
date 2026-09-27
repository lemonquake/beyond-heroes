class_name TouchButton
extends Control
## One on-screen button for touch play: a round glass disc with a bronze rim, an icon (or a drawn glyph), an optional
## caption, a radial cooldown sweep with the seconds left, a stack count, and a "held" glow. TouchControls owns the
## touches (several fingers at once), so this control only draws and answers hit tests.
##   style "round"  the normal button
##   style "badge"  the hit area is the whole disc (an orb) but only a small icon badge is drawn at `badge_offset`
##   style "area"   invisible hit area (the minimap)

var id: StringName = &""
var radius := 50.0
var icon: Texture2D
var glyph := ""                     # drawn when there is no icon: dodge, menu, pause, heavy
var caption := ""                   # small text under the disc
var inner_text := ""                # text inside the disc (no icon)
var style := &"round"
var badge_offset := Vector2.ZERO
var badge_radius := 26.0
var accent := Color(0.72, 0.55, 0.32)
var held := false
var dim := false                    # blocked: not enough mana, wrong weapon, no potions
var mana_short := false
var cd := 0.0
var cd_total := 0.0
var count := -1
var hit_scale := 1.15
var _flash := 0.0

func _init(p_id := &"", p_radius := 50.0) -> void:
	id = p_id
	radius = p_radius
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_resize()

func _resize() -> void:
	size = Vector2(radius, radius) * 2.0
	custom_minimum_size = size
	pivot_offset = size * 0.5

## Centre the disc on `c` (canvas coordinates of the parent).
func place(c: Vector2, r := -1.0) -> void:
	if r > 0.0 and r != radius:
		radius = r
		_resize()
	position = c - Vector2(radius, radius)
	queue_redraw()

func center() -> Vector2:
	return global_position + Vector2(radius, radius)

func hit(p: Vector2) -> bool:
	if not is_visible_in_tree():
		return false
	if (p - center()).length() <= radius * hit_scale:
		return true
	return style == &"badge" and (p - center() - badge_offset).length() <= badge_radius * 1.3

func set_held(on: bool) -> void:
	if held != on:
		held = on
		queue_redraw()

func set_state(p_cd: float, p_total: float, p_dim := false, p_count := -1, p_mana_short := false) -> void:
	if cd > 0.0 and p_cd <= 0.0:
		_flash = 1.0
	if absf(p_cd - cd) > 0.02 or (p_cd <= 0.0 and cd > 0.0) or p_total != cd_total or p_dim != dim or p_count != count or p_mana_short != mana_short:
		cd = p_cd
		cd_total = p_total
		dim = p_dim
		count = p_count
		mana_short = p_mana_short
		queue_redraw()

func set_icon(t: Texture2D) -> void:
	if t != icon:
		icon = t
		queue_redraw()

func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash = maxf(0.0, _flash - delta * 2.4)
		queue_redraw()

func _draw() -> void:
	match style:
		&"area":
			return
		&"badge":
			_draw_disc(Vector2(radius, radius) + badge_offset, badge_radius)
		_:
			_draw_disc(Vector2(radius, radius), radius)

func _draw_disc(c: Vector2, r: float) -> void:
	var a := 1.0 if held else 0.92
	# glass disc, darker rim, bronze ring
	draw_circle(c, r, Color(0.04, 0.035, 0.04, 0.62 * a))
	draw_circle(c, r * 0.9, Color(0.1, 0.085, 0.08, 0.35 * a))
	var content := Color(1, 1, 1, a)
	if dim or (count == 0):
		content = Color(0.45, 0.45, 0.45, 0.8)
	if mana_short:
		content = Color(0.5, 0.6, 1.0, 0.9)
	if icon:
		var side := r * 1.34
		var ir := Rect2(c - Vector2(side, side) * 0.5, Vector2(side, side))
		draw_texture_rect(icon, ir, false, content)
	elif glyph != "":
		_draw_glyph(c, r, content)
	if inner_text != "":
		var f := UITheme.body_bold()
		var fs := int(clampf(r * 0.36, 13.0, 30.0))
		var w := f.get_string_size(inner_text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var p := c + Vector2(-w * 0.5, fs * 0.36)
		draw_string_outline(f, p, inner_text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(0, 0, 0, 0.9))
		draw_string(f, p, inner_text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UITheme.PARCHMENT)
	# cooldown sweep
	if cd > 0.0 and cd_total > 0.0:
		var frac := clampf(cd / cd_total, 0.0, 1.0)
		var pts := PackedVector2Array([c])
		var steps := 36
		for i in steps + 1:
			var ang := -PI * 0.5 + TAU * (1.0 - frac) + TAU * frac * float(i) / float(steps)
			pts.append(c + Vector2(cos(ang), sin(ang)) * r * 0.97)
		draw_colored_polygon(pts, Color(0.0, 0.0, 0.03, 0.66))
		var nf := UITheme.number_font()
		var txt := ("%.1f" % cd) if cd < 3.0 else str(ceili(cd))
		var fs2 := int(r * 0.62)
		var tw := nf.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2).x
		var tp := c + Vector2(-tw * 0.5, fs2 * 0.36)
		draw_string_outline(nf, tp, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, 5, Color(0, 0, 0, 0.9))
		draw_string(nf, tp, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, UITheme.PARCHMENT)
	var ring := accent
	if held:
		ring = UITheme.GOLD
	draw_arc(c, r - 1.5, 0.0, TAU, 64, Color(0, 0, 0, 0.7), 5.0, true)
	draw_arc(c, r - 2.0, 0.0, TAU, 64, Color(ring, 0.95 if held else 0.8), 3.0 if not held else 4.0, true)
	if held:
		draw_circle(c, r, Color(1.0, 0.85, 0.5, 0.14))
	if _flash > 0.0:
		draw_arc(c, r + 3.0 + (1.0 - _flash) * 8.0, 0.0, TAU, 48, Color(0.6, 0.95, 1.0, _flash), 3.0, true)
	# stack count
	if count >= 0:
		var nf2 := UITheme.number_font()
		var ct := str(count)
		var fs3 := int(clampf(r * 0.5, 14.0, 26.0))
		var cw := nf2.get_string_size(ct, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3).x
		var cp := c + Vector2(r * 0.72 - cw * 0.5, r * 0.95)
		draw_string_outline(nf2, cp, ct, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3, 5, Color(0, 0, 0, 0.95))
		draw_string(nf2, cp, ct, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3, UITheme.PARCHMENT if count > 0 else UITheme.BAD)
	if caption != "":
		var bf := UITheme.body_bold()
		var fs4 := int(clampf(r * 0.32, 14.0, 22.0))
		var w4 := bf.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, fs4).x
		var p4 := c + Vector2(-w4 * 0.5, r + fs4 + 2.0)
		draw_string_outline(bf, p4, caption, HORIZONTAL_ALIGNMENT_LEFT, -1, fs4, 5, Color(0, 0, 0, 0.95))
		draw_string(bf, p4, caption, HORIZONTAL_ALIGNMENT_LEFT, -1, fs4, UITheme.PARCHMENT)

func _draw_glyph(c: Vector2, r: float, col: Color) -> void:
	var w := maxf(3.0, r * 0.11)
	var ink := Color(UITheme.PARCHMENT, col.a) * Color(col.r, col.g, col.b, 1.0)
	match glyph:
		"menu":
			for i in 3:
				var y := c.y + (i - 1) * r * 0.3
				draw_line(Vector2(c.x - r * 0.42, y), Vector2(c.x + r * 0.42, y), ink, w, true)
		"pause":
			draw_rect(Rect2(c + Vector2(-r * 0.3, -r * 0.38), Vector2(r * 0.2, r * 0.76)), ink)
			draw_rect(Rect2(c + Vector2(r * 0.1, -r * 0.38), Vector2(r * 0.2, r * 0.76)), ink)
		"dodge":
			# a rolling arc with an arrow head, and speed lines
			draw_arc(c + Vector2(0, r * 0.05), r * 0.42, PI * 0.95, PI * 2.25, 24, ink, w, true)
			var tip := c + Vector2(0, r * 0.05) + Vector2(cos(PI * 2.25), sin(PI * 2.25)) * r * 0.42
			draw_colored_polygon(PackedVector2Array([tip + Vector2(r * 0.2, -r * 0.02), tip + Vector2(-r * 0.12, -r * 0.2), tip + Vector2(-r * 0.06, r * 0.16)]), ink)
			for i in 3:
				var y := c.y - r * 0.2 + i * r * 0.2
				draw_line(Vector2(c.x - r * 0.72, y), Vector2(c.x - r * 0.5, y), Color(ink, ink.a * 0.7), w * 0.6, true)
		"roll":
			# a bold arrow pointing ahead with a tumbling arc behind it
			draw_arc(c + Vector2(0, r * 0.22), r * 0.3, PI * 0.15, PI * 1.85, 20, Color(ink, ink.a * 0.75), w * 0.8, true)
			draw_line(c + Vector2(0, r * 0.18), c + Vector2(0, -r * 0.38), ink, w * 1.2, true)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r * 0.62), c + Vector2(-r * 0.26, -r * 0.28), c + Vector2(r * 0.26, -r * 0.28)]), ink)
		"heavy":
			draw_arc(c, r * 0.5, 0.0, TAU, 32, Color(1.0, 0.65, 0.3, col.a), w, true)
		_:
			pass
