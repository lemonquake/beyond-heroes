class_name ChatBox
extends Control
## The chat box, bottom-left. Enter (action `chat`) opens a text line; Enter again sends it, Escape or an empty send
## closes it. Messages stay in a short log that fades out a few seconds after the line closes. A message that is a
## cheat code (Cheats) is applied instead of said. While the line is open gameplay input is blocked.

const MAX_LINES := 60
const MAX_CHARS := 120
const FADE_AFTER := 8.0
const WIDTH := 520.0

var _log: VBoxContainer
var _line: LineEdit
var _row: HBoxContainer
var _touch_buttons: Array[Button] = []
var _touch_layout := false
var _idle := 0.0
var _open := false
var _scroll: ScrollContainer
var _suggestions: VBoxContainer
var _emoji_grid: GridContainer
var _completion := {}
var _ping: Label
var _ping_tween: Tween
var _heading: Label
var _pending_bubbles := {}

static func chat_font() -> Font:
	var font := FontVariation.new()
	font.base_font = UITheme.body_font()
	font.fallbacks = [preload("res://assets/fonts/NotoEmoji-Regular.ttf")]
	return font

func _init() -> void:
	name = "ChatBox"
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	offset_left = 24
	offset_right = 24 + WIDTH
	offset_top = -620
	offset_bottom = -230
	grow_vertical = Control.GROW_DIRECTION_BEGIN

func _ready() -> void:
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_FULL_RECT)
	col.alignment = BoxContainer.ALIGNMENT_END
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_theme_constant_override("separation", 6)
	add_child(col)
	_heading = UITheme.label("Party chat", 18, UITheme.GOLD)
	col.add_child(_heading)
	_ping = UITheme.label("", 20, UITheme.GOLD)
	_ping.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_ping.add_theme_font_override("font", chat_font())
	_ping.hide()
	col.add_child(_ping)
	_scroll = ScrollContainer.new()
	_scroll.custom_minimum_size.y = 170
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.add_theme_stylebox_override("panel", UITheme.panel_style(Color(0.025, 0.02, 0.015, 0.8), UITheme.BRONZE_DIM, 5, 1, 8))
	col.add_child(_scroll)
	_scroll.get_v_scroll_bar().changed.connect(func() -> void: _scroll.scroll_vertical = int(_scroll.get_v_scroll_bar().max_value))
	_log = VBoxContainer.new()
	_log.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_log.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_log.add_theme_constant_override("separation", 2)
	_scroll.add_child(_log)
	_suggestions = VBoxContainer.new()
	_suggestions.hide()
	col.add_child(_suggestions)
	_emoji_grid = GridContainer.new()
	_emoji_grid.columns = 6
	_emoji_grid.hide()
	for emoji: String in ChatText.EMOJIS:
		var b := UIWindow.button(emoji, func() -> void: _insert_emoji(emoji), &"", 54)
		b.add_theme_font_override("font", chat_font())
		b.add_theme_font_size_override("font_size", 26)
		b.focus_mode = Control.FOCUS_NONE
		_emoji_grid.add_child(b)
	col.add_child(_emoji_grid)
	_line = LineEdit.new()
	_line.placeholder_text = "Say something...  (Enter to send, Esc to close)"
	_line.max_length = MAX_CHARS
	_line.custom_minimum_size = Vector2(WIDTH, 34)
	_line.context_menu_enabled = false
	_line.add_theme_font_size_override("font_size", 16)
	_line.add_theme_font_override("font", chat_font())
	_line.add_theme_stylebox_override("normal", UITheme.panel_style(UITheme.BG_INSET, UITheme.BRONZE_DIM, 3, 1, 0))
	_line.add_theme_stylebox_override("focus", UITheme.panel_style(UITheme.BG_INSET, UITheme.BRONZE, 3, 1, 0))
	_line.text_submitted.connect(_on_submit)
	_line.text_changed.connect(func(_text: String) -> void: _update_completion())
	_line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# touch play: Send and Close buttons beside the line (a phone keyboard's Enter also sends)
	_row = HBoxContainer.new()
	_row.add_theme_constant_override("separation", 8)
	_row.visible = false
	_row.add_child(_line)
	var emojis := UIWindow.button("Emoji", func() -> void: _emoji_grid.visible = not _emoji_grid.visible, &"", 76)
	emojis.focus_mode = Control.FOCUS_NONE
	_row.add_child(emojis)
	for pair in [["Send", func() -> void: _on_submit(_line.text)], ["Close", close]]:
		var b := UIWindow.button(pair[0], pair[1], &"", 110.0)
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size.y = 56
		_row.add_child(b)
		_touch_buttons.append(b)
	col.add_child(_row)
	modulate.a = 0.0
	Settings.changed.connect(_apply_mode)
	Net.chat_received.connect(receive_message)
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
		_line.custom_minimum_size = Vector2(420, 56)
		_line.placeholder_text = "Say something..."
		_line.add_theme_font_size_override("font_size", 24)
	else:
		set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
		offset_left = 24
		offset_right = 24 + WIDTH
		offset_top = -620
		offset_bottom = -230
		_line.custom_minimum_size = Vector2(220, 40)
		_line.placeholder_text = "Message or @name (Enter to send)"
		_line.add_theme_font_size_override("font_size", 16)

func is_open() -> bool:
	return _open

func open() -> void:
	if _open:
		return
	_open = true
	_line.text = ""
	_completion = {}
	_suggestions.hide()
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
	_suggestions.hide()
	_emoji_grid.hide()
	_completion = {}
	_idle = 0.0

## bh-027: put text on the open line (the player menu's Whisper starts "/w <name> ").
func prefill(text: String) -> void:
	if not _open:
		open()
	_line.text = text
	_line.caret_column = text.length()
	_line.grab_focus()

## "/w <name> <message>" (or /whisper, /tell): [peer, message], or [0, why] when it is not one.
static func parse_whisper(t: String) -> Array:
	var lower := t.to_lower()
	var rest := ""
	for cmd in ["/w ", "/whisper ", "/tell "]:
		if lower.begins_with(cmd):
			rest = t.substr(cmd.length()).strip_edges()
	if rest == "":
		return [0, ""]
	var best := 0
	var best_len := -1
	for id in Net.peers:
		var n := String(Net.peers[id].get("name", ""))
		if n != "" and (rest.to_lower() == n.to_lower() or rest.to_lower().begins_with(n.to_lower() + " ")) and n.length() > best_len:
			best = int(id)
			best_len = n.length()
	if best == 0:
		return [0, "Nobody called that is here. Whisper with /w <name> <message>."]
	return [best, rest.substr(best_len).strip_edges()]

## Runs a message exactly as if the player had typed it and pressed Enter (also used by tests).
func submit(text: String) -> void:
	var t := ChatText.clean(text)
	if t.is_empty():
		return
	var hero: HeroData = Game.hero
	if t.begins_with("/w ") or t.begins_with("/whisper ") or t.begins_with("/tell ") or t.begins_with("/W "):
		var w := parse_whisper(t)
		if int(w[0]) == 0:
			add_line(String(w[1]) if String(w[1]) != "" else "Whisper with /w <name> <message>.", UITheme.BAD)
		else:
			var err := Net.whisper(int(w[0]), String(w[1]))
			if err != "":
				add_line(err, UITheme.BAD)
		return
	if Cheats.is_code(t):
		add_line(Cheats.apply(t, hero, Game.player), UITheme.GOLD)
	else:
		if Net.is_active():
			Net.send_chat(t)
		else:
			add_line("[%s] %s" % [hero.hero_name if hero else "You", t], UITheme.PARCHMENT)
			ChatBubble.say(Game.player as Node3D, t)

func receive_message(peer: int, text: String) -> void:
	var who := String(Net.peers.get(peer, {}).get("name", "Hero"))
	var message := "%s: %s" % [who, text]
	var mentioned := peer != Net.my_id() and (ChatText.has_mention(text, "everyone") or (Game.hero != null and ChatText.has_mention(text, Game.hero.hero_name)))
	add_line(message, UITheme.GOLD if mentioned else Net.player_color(peer).lightened(0.2))
	var actor: Node3D = Game.player as Node3D if peer == Net.my_id() else Net.avatar(peer)
	_pending_bubbles.erase(peer)
	ChatBubble.say(actor, text)
	if actor == null:
		_pending_bubbles[peer] = {"text": text, "expires": Time.get_ticks_msec() + 3000}
	if mentioned:
		Audio.play_ui(&"level_up", -6.0)
		_ping.text = "Mention from " + message
		_ping.show()
		if _ping_tween:
			_ping_tween.kill()
		_ping.modulate.a = 1.0
		_ping_tween = create_tween()
		for i in 3:
			_ping_tween.tween_property(_ping, "modulate:a", 0.4, 0.2)
			_ping_tween.tween_property(_ping, "modulate:a", 1.0, 0.2)
		_ping_tween.tween_interval(1.8)
		_ping_tween.tween_callback(_ping.hide)

func add_line(text: String, color := UITheme.TEXT) -> void:
	var l := UITheme.label(text, 22 if _touch_layout else 16, color)
	l.add_theme_font_override("font", chat_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 740.0 if _touch_layout else WIDTH - 24
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
	_scroll.set_deferred("scroll_vertical", int(_scroll.get_v_scroll_bar().max_value))

func lines() -> PackedStringArray:
	var out := PackedStringArray()
	for c in _log.get_children():
		out.append((c as Label).text)
	return out

func _on_submit(text: String) -> void:
	_update_completion()
	if not _completion.is_empty():
		_accept_completion(_completion.names[0])
		return
	submit(text)
	close()
	get_viewport().set_input_as_handled()

func _input(e: InputEvent) -> void:
	if _open and e is InputEventKey and e.pressed and not e.echo and e.keycode in [KEY_RIGHT, KEY_SPACE, KEY_ENTER, KEY_KP_ENTER]:
		_update_completion()
		if not _completion.is_empty():
			_accept_completion(_completion.names[0])
			get_viewport().set_input_as_handled()
			return
	# Escape closes the line before the pause menu sees it.
	if _open and e is InputEventKey and e.pressed and not e.echo and e.physical_keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()

func _process(delta: float) -> void:
	for peer: int in _pending_bubbles.keys():
		var pending: Dictionary = _pending_bubbles[peer]
		var left := (int(pending.expires) - Time.get_ticks_msec()) / 1000.0
		var actor := Net.avatar(peer)
		if left <= 0 or not Net.peers.has(peer):
			_pending_bubbles.erase(peer)
		elif actor:
			ChatBubble.say(actor, pending.text)
			(actor.get_node("ChatBubble") as ChatBubble).remaining = left
			_pending_bubbles.erase(peer)
	_heading.visible = Net.is_active()
	if _open or Net.is_active():
		modulate.a = 1.0
		return
	_idle += delta
	if _idle > FADE_AFTER:
		modulate.a = maxf(0.0, modulate.a - delta * 0.8)

func _update_completion() -> void:
	var names: Array = ["everyone"]
	for profile: Dictionary in Net.peers.values():
		names.append(String(profile.get("name", "Hero")))
	_completion = ChatText.completion(_line.text, _line.caret_column, names) if Net.is_active() else {}
	for child in _suggestions.get_children():
		_suggestions.remove_child(child)
		child.queue_free()
	_suggestions.visible = not _completion.is_empty()
	if _completion.is_empty():
		return
	for candidate: String in _completion.names.slice(0, 4):
		var b := UIWindow.button(ChatText.mention(candidate), func() -> void: _accept_completion(candidate), &"", 180)
		b.focus_mode = Control.FOCUS_NONE
		_suggestions.add_child(b)
	_suggestions.add_child(UITheme.label("Right / Space / Enter to complete; Enter again to send", 16, UITheme.TEXT))

func _accept_completion(candidate: String) -> void:
	if _completion.is_empty():
		return
	var insert := ChatText.mention(candidate) + " "
	var start := int(_completion.start)
	var end := int(_completion.end)
	var result := _line.text.left(start) + insert + _line.text.substr(end)
	if result.length() > MAX_CHARS:
		return
	_line.text = result
	_line.caret_column = start + insert.length()
	_completion = {}
	_suggestions.hide()
	_line.grab_focus()

func _insert_emoji(emoji: String) -> void:
	if _line.text.length() + emoji.length() <= MAX_CHARS:
		_line.insert_text_at_caret(emoji)
	_emoji_grid.hide()
	_line.grab_focus()
