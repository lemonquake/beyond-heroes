class_name UITheme
## Beyond Heroes visual language: palette, fonts, ornate panel styles, and the global Theme.
## Dark iron-and-parchment fantasy: charcoal panels with warm bronze filigree borders and ember accents.

const BG_DEEP := Color(0.035, 0.03, 0.035, 0.96)
const BG_PANEL := Color(0.075, 0.062, 0.058, 0.94)
const BG_PANEL_2 := Color(0.11, 0.09, 0.08, 0.95)
const BG_INSET := Color(0.03, 0.025, 0.025, 0.9)
const BRONZE := Color(0.72, 0.55, 0.32)
const BRONZE_DIM := Color(0.42, 0.32, 0.2)
const GOLD := Color(0.96, 0.8, 0.46)
const PARCHMENT := Color(0.92, 0.86, 0.74)
const TEXT := Color(0.88, 0.84, 0.76)
const TEXT_DIM := Color(0.6, 0.56, 0.5)
const TEXT_MUTED := Color(0.42, 0.39, 0.36)
const EMBER := Color(0.95, 0.45, 0.15)
const BLOOD := Color(0.72, 0.1, 0.1)
const MANA := Color(0.2, 0.45, 0.95)
const GOOD := Color(0.45, 0.9, 0.45)
const BAD := Color(0.95, 0.35, 0.3)
const ARCANE := Color(0.62, 0.45, 1.0)

static var _title_font: Font
static var _body_font: Font
static var _body_bold: Font
static var _number_font: Font
static var _theme: Theme

static func _sys(names: PackedStringArray, weight := 400, italic := false) -> SystemFont:
	var f := SystemFont.new()
	f.font_names = names
	f.font_weight = weight
	f.font_italic = italic
	f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	f.hinting = TextServer.HINTING_LIGHT
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_AUTO
	f.multichannel_signed_distance_field = false
	return f

static func title_font() -> Font:
	if _title_font == null:
		_title_font = _sys(PackedStringArray(["Felix Titling", "Engravers MT", "Book Antiqua", "Palatino Linotype", "Georgia", "serif"]))
	return _title_font

static func body_font() -> Font:
	if _body_font == null:
		_body_font = _sys(PackedStringArray(["Book Antiqua", "Palatino Linotype", "Georgia", "serif"]))
	return _body_font

static func body_bold() -> Font:
	if _body_bold == null:
		_body_bold = _sys(PackedStringArray(["Book Antiqua", "Palatino Linotype", "Georgia", "serif"]), 700)
	return _body_bold

static func number_font() -> Font:
	if _number_font == null:
		_number_font = _sys(PackedStringArray(["Palatino Linotype", "Book Antiqua", "Georgia", "serif"]), 700)
	return _number_font

## Ornate framed panel: dark gradient body, double bronze border, soft drop shadow.
static func panel_style(bg := BG_PANEL, border := BRONZE_DIM, radius := 3, border_w := 2, shadow := 12) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(border_w)
	s.set_corner_radius_all(radius)
	s.shadow_color = Color(0, 0, 0, 0.55)
	s.shadow_size = shadow
	s.set_content_margin_all(12)
	s.anti_aliasing = true
	return s

static func slot_style(border: Color, bg := BG_INSET, w := 2) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(w)
	s.set_corner_radius_all(2)
	s.set_content_margin_all(4)
	return s

static func button_style(state: String) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	match state:
		"normal":
			s.bg_color = Color(0.12, 0.095, 0.08, 0.95)
			s.border_color = BRONZE_DIM
		"hover":
			s.bg_color = Color(0.2, 0.14, 0.09, 0.98)
			s.border_color = GOLD
		"pressed":
			s.bg_color = Color(0.08, 0.06, 0.05, 1.0)
			s.border_color = BRONZE
		"disabled":
			s.bg_color = Color(0.07, 0.065, 0.06, 0.8)
			s.border_color = Color(0.25, 0.22, 0.2)
		"focus":
			s.bg_color = Color(0, 0, 0, 0)
			s.border_color = GOLD
			s.draw_center = false
	s.set_border_width_all(2)
	s.border_width_bottom = 3
	s.set_corner_radius_all(3)
	s.content_margin_left = 18
	s.content_margin_right = 18
	s.content_margin_top = 8
	s.content_margin_bottom = 8
	s.shadow_color = Color(0, 0, 0, 0.4)
	s.shadow_size = 4 if state != "pressed" else 1
	return s

static func theme() -> Theme:
	if _theme:
		return _theme
	var t := Theme.new()
	t.default_font = body_font()
	t.default_font_size = 18
	t.set_color("font_color", "Label", TEXT)
	t.set_color("font_outline_color", "Label", Color(0, 0, 0, 0.85))
	t.set_constant("outline_size", "Label", 0)
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		t.set_stylebox(st, "Button", button_style(st))
	t.set_font("font", "Button", title_font())
	t.set_font_size("font_size", "Button", 19)
	t.set_color("font_color", "Button", PARCHMENT)
	t.set_color("font_hover_color", "Button", GOLD)
	t.set_color("font_pressed_color", "Button", BRONZE)
	t.set_color("font_disabled_color", "Button", TEXT_MUTED)
	t.set_color("font_focus_color", "Button", GOLD)
	t.set_stylebox("panel", "PanelContainer", panel_style())
	t.set_stylebox("panel", "Panel", panel_style())
	var tt := panel_style(Color(0.05, 0.04, 0.04, 0.97), BRONZE, 3, 2, 10)
	t.set_stylebox("panel", "TooltipPanel", tt)
	t.set_color("font_color", "TooltipLabel", TEXT)
	var sl_bg := StyleBoxFlat.new()
	sl_bg.bg_color = Color(0.05, 0.04, 0.04)
	sl_bg.border_color = BRONZE_DIM
	sl_bg.set_border_width_all(1)
	sl_bg.set_corner_radius_all(3)
	sl_bg.content_margin_top = 4
	sl_bg.content_margin_bottom = 4
	t.set_stylebox("slider", "HSlider", sl_bg)
	var fill := StyleBoxFlat.new()
	fill.bg_color = BRONZE
	fill.set_corner_radius_all(3)
	t.set_stylebox("grabber_area", "HSlider", fill)
	t.set_stylebox("grabber_area_highlight", "HSlider", fill)
	var cb := StyleBoxFlat.new()
	cb.bg_color = Color(0.1, 0.08, 0.07)
	cb.border_color = BRONZE_DIM
	cb.set_border_width_all(1)
	t.set_stylebox("normal", "OptionButton", button_style("normal"))
	t.set_stylebox("hover", "OptionButton", button_style("hover"))
	t.set_stylebox("pressed", "OptionButton", button_style("pressed"))
	t.set_font("font", "OptionButton", body_font())
	var le := StyleBoxFlat.new()
	le.bg_color = Color(0.04, 0.035, 0.035)
	le.border_color = BRONZE_DIM
	le.set_border_width_all(2)
	le.set_content_margin_all(10)
	t.set_stylebox("normal", "LineEdit", le)
	var le_f := le.duplicate()
	le_f.border_color = GOLD
	t.set_stylebox("focus", "LineEdit", le_f)
	t.set_color("font_color", "LineEdit", PARCHMENT)
	t.set_font_size("font_size", "LineEdit", 22)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.2, 0.16, 0.12)
	sb.set_corner_radius_all(4)
	t.set_stylebox("grabber", "VScrollBar", sb)
	var sbh := sb.duplicate()
	sbh.bg_color = BRONZE
	t.set_stylebox("grabber_highlight", "VScrollBar", sbh)
	var sbs := StyleBoxFlat.new()
	sbs.bg_color = Color(0.04, 0.035, 0.035, 0.6)
	sbs.set_corner_radius_all(4)
	t.set_stylebox("scroll", "VScrollBar", sbs)
	_theme = t
	return t

static func label(text: String, size := 18, color := TEXT, font: Font = null) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if font:
		l.add_theme_font_override("font", font)
	return l

static func title(text: String, size := 30, color := GOLD) -> Label:
	var l := label(text, size, color, title_font())
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("outline_size", 6)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	l.add_theme_constant_override("shadow_offset_y", 2)
	return l

static func icon(path: String) -> Texture2D:
	if path != "" and ResourceLoader.exists(path):
		return load(path)
	return null
