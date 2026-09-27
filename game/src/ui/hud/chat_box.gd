class_name ChatBox
extends Control
## The chat box, bottom-left. Enter (action `chat`) opens a text line; Enter again sends it, Escape or an empty send
## closes it. Messages stay in a short log that fades out a few seconds after the line closes. A message that is a
## cheat code (Cheats) is applied instead of said. While the line is open gameplay input is blocked.

const MAX_LINES := 8
const MAX_CHARS := 120
const FADE_AFTER := 8.0
const WIDTH := 400.0

var _log: VBoxContainer
var _line: LineEdit
var _row: HBoxContainer
var _touch_buttons: Array[Button] = []
var _touch_layout := false
var _idle := 0.0
var _open := false

func _init() -> void:
	name = "ChatBox"
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	offset_left = 24
	offset_right = 24 + WIDTH
	offset_top = -330
	offset_bottom = -40
	grow_vertical = Control.GROW_DIRECTION_BEGIN

func _ready() -> void:
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_FULL_RECT)
	col.alignment = BoxContainer.ALIGNMENT_END
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_theme_constant_override("separation", 6)
	add_child(col)
	_log = VBoxContainer.new()
	_log.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_log.add_theme_constant_override("separation", 2)
	col.add_child(_log)
	_line = LineEdit.new()
	_line.placeholder_text = "Say something...  (Enter to send, Esc to close)"
	_line.max_length = MAX_CHARS
	_line.custom_minimum_size = Vector2(WIDTH, 34)
	_line.context_menu_enabled = false
	_line.add_theme_font_size_override("font_size", 16)
	_line.add_theme_stylebox_override("normal", UITheme.panel_style(UITheme.BG_INSET, UITheme.BRONZE_DIM, 3, 1, 0))
	_line.add_theme_stylebox_override("focus", UITheme.panel_style(UITheme.BG_INSET, UITheme.BRONZE, 3, 1, 0))
	_line.text_submitted.connect(_on_submit)
	_line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# touch play: Send and Close buttons beside the line (a phone keyboard's Enter also sends)
	_row = HBoxContainer.new()
	_row.add_theme_constant_override("separation", 8)
	_row.visible = false
	_row.add_child(_line)
	for pair in [["Send", func() -> void: _on_submit(_line.text)], ["Close", close]]:
		var b := UIWindow.button(pair[0], pair[1], &"", 110.0)
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size.y = 56
		_row.add_child(b)
		_touch_buttons.append(b)
	col.add_child(_row)
	modulate.a = 0.0
	Settings.changed.connect(_apply_mode)
	_apply_mode()

## Keyboard + mouse: bottom left. Touch play: top centre, above where a phone keyboard slides up, with larger text.
func _apply_mode() -> void:
	var m := Settings.touch_mode
	_touch_layout = m
	for b in _touch_buttons:
		b.visible = m
	if m:
		set_anchors_preset(Control.PRESET_CENTER_TOP)
		offset_left = -430
		offset_right = 430
		offset_top = 96
		offset_bottom = 400
		_line.custom_minimum_size = Vector2(560, 56)
		_line.placeholder_text = "Say something..."
		_line.add_theme_font_size_override("font_size", 24)
	else:
		set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
		offset_left = 24
		offset_right = 24 + WIDTH
		offset_top = -330
		offset_bottom = -40
		_line.custom_minimum_size = Vector2(WIDTH, 34)
		_line.placeholder_text = "Say something...  (Enter to send, Esc to close)"
		_line.add_theme_font_size_override("font_size", 16)

func is_open() -> bool:
	return _open

func open() -> void:
	if _open:
		return
	_open = true
	_line.text = ""
	_row.visible = true
	_line.grab_focus()
	_idle = 0.0
	modulate.a = 1.0

func close() -> void:
	if not _open:
		return
	_open = false
	_line.release_focus()
	_row.visible = false
	_idle = 0.0

## Runs a message exactly as if the player had typed it and pressed Enter (also used by tests).
func submit(text: String) -> void:
	var t := text.strip_edges()
	if t.is_empty():
		return
	var hero: HeroData = Game.hero
	if Cheats.is_code(t):
		add_line(Cheats.apply(t, hero, Game.player), UITheme.GOLD)
	else:
		if Net.is_active():     # your own line in your player colour, like the others see it
			add_line("◆ %s: %s" % [hero.hero_name if hero else "You", t], Net.player_color(Net.my_id()).lightened(0.2))
		else:
			add_line("[%s] %s" % [hero.hero_name if hero else "You", t], UITheme.PARCHMENT)
		Net.send_chat(t)          # everyone in the party reads it (bh-008)

func add_line(text: String, color := UITheme.TEXT) -> void:
	var l := UITheme.label(text, 22 if _touch_layout else 16, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 740.0 if _touch_layout else WIDTH
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("outline_size", 4)
	_log.add_child(l)
	while _log.get_child_count() > MAX_LINES:
		var old := _log.get_child(0)
		_log.remove_child(old)
		old.queue_free()
	_idle = 0.0
	modulate.a = 1.0

func lines() -> PackedStringArray:
	var out := PackedStringArray()
	for c in _log.get_children():
		out.append((c as Label).text)
	return out

func _on_submit(text: String) -> void:
	submit(text)
	close()
	get_viewport().set_input_as_handled()

func _input(e: InputEvent) -> void:
	# Escape closes the line before the pause menu sees it.
	if _open and e is InputEventKey and e.pressed and not e.echo and e.physical_keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()

func _process(delta: float) -> void:
	if _open:
		modulate.a = 1.0
		return
	_idle += delta
	if _idle > FADE_AFTER:
		modulate.a = maxf(0.0, modulate.a - delta * 0.8)
