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
		_title_font = _sys(PackedStringArray(["Felix Titling", "Engravers MT", "Book Antiqua", "Palatino Linotype", "Georgia", "DejaVu Serif", "serif"]))
	return _title_font

static func body_font() -> Font:
	if _body_font == null:
		_body_font = _sys(PackedStringArray(["Book Antiqua", "Palatino Linotype", "Georgia", "DejaVu Serif", "serif"]))
	return _body_font

static func body_bold() -> Font:
	if _body_bold == null:
		_body_bold = _sys(PackedStringArray(["Book Antiqua", "Palatino Linotype", "Georgia", "DejaVu Serif", "serif"]), 700)
	return _body_bold

static func number_font() -> Font:
	if _number_font == null:
		_number_font = _sys(PackedStringArray(["Palatino Linotype", "Book Antiqua", "Georgia", "DejaVu Serif", "serif"]), 700)
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
	t.set_font("normal_font", "RichTextLabel", body_font())
	t.set_font("bold_font", "RichTextLabel", body_bold())
	t.set_color("default_color", "RichTextLabel", TEXT)
	# Buttons: painted bronze by default; PrimaryButton (gold/crimson) and MenuButton (wide banner) variations.
	_button_type(t, "Button", "frames/button_%s.png")
	t.set_font("font", "Button", title_font())
	t.set_font_size("font_size", "Button", 19)
	t.set_color("font_color", "Button", PARCHMENT)
	t.set_color("font_hover_color", "Button", GOLD)
	t.set_color("font_pressed_color", "Button", BRONZE)
	t.set_color("font_hover_pressed_color", "Button", GOLD)
	t.set_color("font_disabled_color", "Button", TEXT_MUTED)
	t.set_color("font_focus_color", "Button", GOLD)
	t.set_constant("h_separation", "Button", 8)
	t.set_type_variation("PrimaryButton", "Button")
	_button_type(t, "PrimaryButton", "frames/button_primary_%s.png")
	t.set_font_size("font_size", "PrimaryButton", 20)
	t.set_color("font_color", "PrimaryButton", Color(1.0, 0.93, 0.78))
	t.set_type_variation("BannerButton", "Button")
	_button_type(t, "BannerButton", "frames/button_menu_%s.png")
	t.set_font_size("font_size", "BannerButton", 24)
	t.set_color("font_color", "BannerButton", PARCHMENT)
	t.set_color("font_hover_color", "BannerButton", Color(0.85, 0.99, 1.0))
	t.set_type_variation("IconButton", "Button")
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		t.set_stylebox(st, "IconButton", UIArt.style("frames/button_%s.png" % st, [6, 5, 6, 5]))
	t.set_stylebox("hover_pressed", "IconButton", UIArt.style("frames/button_pressed.png", [6, 5, 6, 5]))
	t.set_type_variation("FlatButton", "Button")
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		var e := StyleBoxEmpty.new()
		e.set_content_margin_all(4)
		t.set_stylebox(st, "FlatButton", e)
	t.set_font("font", "FlatButton", body_font())
	t.set_font_size("font_size", "FlatButton", 17)
	# Panels
	t.set_stylebox("panel", "PanelContainer", UIArt.style("frames/panel_main.png"))
	t.set_stylebox("panel", "Panel", UIArt.style("frames/panel_main.png"))
	for v in [["InsetPanel", "frames/panel_inset.png"], ["GlassPanel", "frames/panel_glass.png"], ["HeaderPanel", "frames/panel_header.png"],
			["DialoguePanel", "frames/panel_dialogue.png"], ["TooltipFrame", "frames/panel_tooltip.png"]]:
		t.set_type_variation(v[0], "PanelContainer")
		t.set_stylebox("panel", v[0], UIArt.style(v[1]))
	t.set_type_variation("ClearPanel", "PanelContainer")
	t.set_stylebox("panel", "ClearPanel", StyleBoxEmpty.new())
	t.set_stylebox("panel", "TooltipPanel", UIArt.style("frames/panel_tooltip.png"))
	t.set_color("font_color", "TooltipLabel", TEXT)
	t.set_font_size("font_size", "TooltipLabel", 16)
	t.set_stylebox("panel", "PopupMenu", UIArt.style("frames/panel_tooltip.png"))
	t.set_stylebox("hover", "PopupMenu", UIArt.style("frames/button_hover.png", [10, 4, 10, 4]))
	t.set_color("font_color", "PopupMenu", TEXT)
	t.set_color("font_hover_color", "PopupMenu", GOLD)
	t.set_stylebox("panel", "PopupPanel", UIArt.style("frames/panel_tooltip.png"))
	# Tabs
	for pair in [["tab_unselected", "tab_normal"], ["tab_hovered", "tab_hover"], ["tab_selected", "tab_selected"], ["tab_focus", "tab_hover"],
			["tab_disabled", "tab_normal"]]:
		t.set_stylebox(pair[0], "TabBar", UIArt.style("frames/%s.png" % pair[1]))
		t.set_stylebox(pair[0], "TabContainer", UIArt.style("frames/%s.png" % pair[1]))
	t.set_stylebox("panel", "TabContainer", UIArt.style("frames/panel_inset.png"))
	t.set_font("font", "TabBar", title_font())
	t.set_font("font", "TabContainer", title_font())
	t.set_font_size("font_size", "TabBar", 17)
	t.set_font_size("font_size", "TabContainer", 17)
	for tp in ["TabBar", "TabContainer"]:
		t.set_color("font_selected_color", tp, GOLD)
		t.set_color("font_unselected_color", tp, TEXT_DIM)
		t.set_color("font_hovered_color", tp, PARCHMENT)
	# Check boxes
	for tp in ["CheckBox", "CheckButton"]:
		t.set_icon("checked", tp, _scaled_icon("frames/checkbox_on.png"))
		t.set_icon("unchecked", tp, _scaled_icon("frames/checkbox_off.png"))
		t.set_icon("checked_disabled", tp, _scaled_icon("frames/checkbox_on.png"))
		t.set_icon("unchecked_disabled", tp, _scaled_icon("frames/checkbox_off.png"))
		for st in ["normal", "hover", "pressed", "disabled", "focus", "hover_pressed"]:
			var e := StyleBoxEmpty.new()
			e.set_content_margin_all(2)
			t.set_stylebox(st, tp, e)
		t.set_font("font", tp, body_font())
		t.set_color("font_color", tp, TEXT)
		t.set_color("font_hover_color", tp, GOLD)
		t.set_color("font_pressed_color", tp, PARCHMENT)
	# Sliders
	t.set_stylebox("slider", "HSlider", UIArt.style("frames/slider_track.png", [0, 0, 0, 0]))
	t.set_stylebox("grabber_area", "HSlider", UIArt.style("frames/slider_fill.png", [0, 0, 0, 0]))
	t.set_stylebox("grabber_area_highlight", "HSlider", UIArt.style("frames/slider_fill.png", [0, 0, 0, 0]))
	t.set_icon("grabber", "HSlider", _scaled_icon("frames/slider_grabber.png"))
	t.set_icon("grabber_highlight", "HSlider", _scaled_icon("frames/slider_grabber_hover.png"))
	t.set_icon("grabber_disabled", "HSlider", _scaled_icon("frames/slider_grabber.png"))
	# Scrollbars
	# Nonzero style margins give vertical scrollbars a visible, draggable width.
	t.set_stylebox("scroll", "VScrollBar", UIArt.style("frames/scroll_track.png", [7, 8, 7, 8]))
	t.set_stylebox("scroll_focus", "VScrollBar", UIArt.style("frames/scroll_track.png", [7, 8, 7, 8]))
	for st in ["grabber", "grabber_highlight", "grabber_pressed"]:
		t.set_stylebox(st, "VScrollBar", UIArt.style("frames/scroll_grabber.png", [7, 8, 7, 8], Color(1, 1, 1) if st == "grabber" else Color(1.25, 1.15, 0.95)))
	var hs := StyleBoxFlat.new()
	hs.bg_color = Color(0.05, 0.04, 0.035, 0.7)
	hs.set_corner_radius_all(4)
	hs.content_margin_top = 6
	t.set_stylebox("scroll", "HScrollBar", hs)
	var hg := StyleBoxFlat.new()
	hg.bg_color = BRONZE_DIM
	hg.set_corner_radius_all(4)
	t.set_stylebox("grabber", "HScrollBar", hg)
	# Text fields
	t.set_stylebox("normal", "LineEdit", UIArt.style("frames/lineedit.png", [12, 8, 12, 8]))
	t.set_stylebox("focus", "LineEdit", UIArt.style("frames/lineedit_focus.png", [12, 8, 12, 8]))
	t.set_stylebox("read_only", "LineEdit", UIArt.style("frames/lineedit.png", [12, 8, 12, 8]))
	t.set_color("font_color", "LineEdit", PARCHMENT)
	t.set_color("font_placeholder_color", "LineEdit", TEXT_MUTED)
	t.set_color("caret_color", "LineEdit", GOLD)
	t.set_font_size("font_size", "LineEdit", 18)
	# Dropdowns
	_button_type(t, "OptionButton", "frames/button_%s.png")
	t.set_icon("arrow", "OptionButton", _scaled_icon("frames/dropdown_arrow.png"))
	t.set_font("font", "OptionButton", body_font())
	t.set_font_size("font_size", "OptionButton", 17)
	t.set_color("font_color", "OptionButton", PARCHMENT)
	t.set_color("font_hover_color", "OptionButton", GOLD)
	t.set_constant("arrow_margin", "OptionButton", 10)
	# Separators
	t.set_stylebox("separator", "HSeparator", UIArt.style("frames/separator_h.png", [0, 0, 0, 0]))
	t.set_constant("separation", "HSeparator", 16)
	var vsep := StyleBoxLine.new()
	vsep.color = BRONZE_DIM
	vsep.vertical = true
	vsep.thickness = 2
	t.set_stylebox("separator", "VSeparator", vsep)
	# Progress bars (plain; HUD bars use their own art)
	var pb_bg := StyleBoxFlat.new()
	pb_bg.bg_color = Color(0.03, 0.025, 0.025, 0.9)
	pb_bg.border_color = BRONZE_DIM
	pb_bg.set_border_width_all(1)
	pb_bg.set_corner_radius_all(3)
	var pb_fill := StyleBoxFlat.new()
	pb_fill.bg_color = GOLD
	pb_fill.set_corner_radius_all(3)
	t.set_stylebox("background", "ProgressBar", pb_bg)
	t.set_stylebox("fill", "ProgressBar", pb_fill)
	t.set_font_size("font_size", "ProgressBar", 13)
	_theme = t
	return t

static func _button_type(t: Theme, type: String, pattern: String) -> void:
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		t.set_stylebox(st, type, UIArt.style(pattern % st))
	t.set_stylebox("hover_pressed", type, UIArt.style(pattern % "pressed"))

## A texture drawn at its logical (half) size, for theme icons (checkboxes, grabbers, arrows).
static func _scaled_icon(path: String) -> Texture2D:
	var src := UIArt.tex(path)
	if src == null:
		return null
	var img := src.get_image()
	if img == null:
		return src
	if img.is_compressed():
		img.decompress()
	var sz := UIArt.size_of(path)
	var ui := maxf(1.0, Settings.ui_scale if Settings else 1.0)
	img.resize(maxi(1, int(sz.x * ui)), maxi(1, int(sz.y * ui)), Image.INTERPOLATE_LANCZOS)
	return ImageTexture.create_from_image(img)

static func label(text: String, size := 18, color := TEXT, font: Font = null) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if font:
		l.add_theme_font_override("font", font)
	return l

## A one-line label that never widens its container: text longer than the space it is given ends in "…" (the full
## text stays in the tooltip).
static func fit_line(l: Label) -> Label:
	l.clip_text = true
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
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
