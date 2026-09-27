class_name PlatformPrompt
extends Control
## First launch only: "How are you playing?" — PC (keyboard and mouse) or Mobile (touch controls). The answer is
## saved in Settings.control_mode; Settings > Controls > Control Mode changes it later. Emits `chosen` when done.

signal chosen(mode: String)

var _cards: Array[Button] = []

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

func _ready() -> void:
	theme = UITheme.theme()
	var bg := ColorRect.new()
	bg.color = Color(0.025, 0.02, 0.028)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var vig := TextureRect.new()
	vig.texture = UIArt.tex("menu/vignette_menu.png")
	vig.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vig.stretch_mode = TextureRect.STRETCH_SCALE
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vig)
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(c)
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 22)
	c.add_child(v)
	var logo := UIArt.image("menu/title_logo.png")
	logo.custom_minimum_size *= 0.62
	logo.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(logo)
	var h := UITheme.title("How are you playing?", 44, UITheme.GOLD)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(h)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 40)
	v.add_child(row)
	var phone := Settings.is_mobile_device()
	row.add_child(_card("pc", "PC", "Keyboard and mouse.\nWASD to move, the mouse to aim and attack, number keys for skills.", not phone))
	row.add_child(_card("mobile", "Mobile", "Touch controls and Efficiency Mode.\nA stick for your left thumb, attack and skill buttons for your right. Tuned to run smoothly on low-end phones.", phone))
	var note := UITheme.label("You can change this any time in Settings, under Controls.", 22, UITheme.TEXT_DIM, UITheme.body_font())
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(note)
	_cards[1 if phone else 0].grab_focus.call_deferred()
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.5)

func _card(mode: String, title: String, desc: String, suggested: bool) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(500, 430)
	b.focus_mode = Control.FOCUS_ALL
	b.pressed.connect(func() -> void: _choose(mode))
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.offset_left = 28
	v.offset_right = -28
	v.offset_top = 24
	v.offset_bottom = -24
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 12)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(v)
	var art := DeviceGlyph.new(mode)
	art.custom_minimum_size = Vector2(0, 170)
	v.add_child(art)
	var t := UITheme.title(title, 40, UITheme.PARCHMENT)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(t)
	var d := UITheme.label(desc, 21, UITheme.TEXT, UITheme.body_font())
	d.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(d)
	if suggested:
		var s := UITheme.label("Suggested for this device", 19, UITheme.GOOD, UITheme.body_bold())
		s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		s.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(s)
	_cards.append(b)
	return b

func _choose(mode: String) -> void:
	Audio.play_ui(&"ui_click")
	Settings.set_control_mode(mode)
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.3)
	tw.tween_callback(func() -> void:
		chosen.emit(mode)
		queue_free())

## Line drawings for the two cards: a monitor with keyboard and mouse; a phone held sideways with a stick and buttons.
class DeviceGlyph extends Control:
	var mode := "pc"

	func _init(m: String) -> void:
		mode = m
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var c := size * 0.5
		var ink := UITheme.PARCHMENT
		var acc := UITheme.GOLD
		var w := 4.0
		if mode == "pc":
			var scr := Rect2(c + Vector2(-110, -82), Vector2(220, 124))
			draw_rect(scr, Color(0.08, 0.07, 0.07), true)
			draw_rect(scr, ink, false, w)
			draw_line(c + Vector2(0, 42), c + Vector2(0, 58), ink, w)
			draw_line(c + Vector2(-34, 58), c + Vector2(34, 58), ink, w)
			var kb := Rect2(c + Vector2(-130, 66), Vector2(200, 24))
			draw_rect(kb, ink, false, w * 0.75)
			for i in 9:
				draw_line(kb.position + Vector2(14 + i * 21, 7), kb.position + Vector2(20 + i * 21, 7), acc, 3.0)
			draw_circle(c + Vector2(110, 78), 14.0, Color(0.08, 0.07, 0.07))
			draw_arc(c + Vector2(110, 78), 14.0, 0.0, TAU, 24, ink, w * 0.75)
			draw_line(c + Vector2(110, 64), c + Vector2(110, 76), ink, 3.0)
		else:
			var ph := Rect2(c + Vector2(-150, -70), Vector2(300, 150))
			draw_style_box(_rounded(Color(0.08, 0.07, 0.07), ink), ph)
			draw_circle(c + Vector2(-85, 25), 30.0, Color(acc, 0.18))
			draw_arc(c + Vector2(-85, 25), 30.0, 0.0, TAU, 32, acc, 3.0)
			draw_circle(c + Vector2(-80, 20), 12.0, acc)
			draw_circle(c + Vector2(95, 30), 24.0, Color(ink, 0.2))
			draw_arc(c + Vector2(95, 30), 24.0, 0.0, TAU, 32, ink, 3.0)
			for p in [Vector2(50, 22), Vector2(62, -10), Vector2(94, -24)]:
				draw_arc(c + p, 11.0, 0.0, TAU, 20, ink, 3.0)

	static func _rounded(bg: Color, border: Color) -> StyleBoxFlat:
		var sb := StyleBoxFlat.new()
		sb.bg_color = bg
		sb.border_color = border
		sb.set_border_width_all(4)
		sb.set_corner_radius_all(22)
		return sb
