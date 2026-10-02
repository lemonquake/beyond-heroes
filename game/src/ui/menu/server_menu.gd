class_name ServerMenu
extends Control
## First menu (bh-030 remake): choose a realm — the Official Server, Offline Play or a Custom Game — from three large
## cards, with the custom games around you as clickable cards below. Every card and button is sized for a thumb on a
## phone (Settings.touch_mode) and the layout re-flows with the screen width (one, two or three columns).
## Views: servers (home), custom (all custom games + hosting), auth (a large sign-in page with remembered accounts),
## recovery, characters, import and settings. Signing in can remember the UserID and, when asked, the password
## (SavedAccounts, encrypted on this device); a new account is confirmed with a notice.
signal selected(mode: String, room: Dictionary)
signal official_play(character: String)
signal official_new

const OFFICIAL_COLOR := Color(0.96, 0.78, 0.4)
const OFFLINE_COLOR := Color(0.5, 0.8, 0.5)
const CUSTOM_COLOR := Color(0.5, 0.68, 0.98)

var _body: VBoxContainer
var _scroll: ScrollContainer
var _status: Label
var _list: Control
var _busy := false
var _checking := false
var _view := "servers"
var _refresh_t := 0.0
var _directory: Array = []
var _dialog: ConfirmDialog
var _health := {}
var _status_pill: Label
var _toast: PanelContainer
var _toast_label: Label
var _toast_tw: Tween
var _last_width := 0.0
var _relayout_t := -1.0
var _auth_mode := 0               # 0 sign in, 1 create account, 2 recover

func _ready() -> void:
	theme = UITheme.theme()
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	size = get_viewport_rect().size
	get_viewport().size_changed.connect(func() -> void:
		size = get_viewport_rect().size
		_relayout_t = 0.25)
	var shade := ColorRect.new()
	shade.color = Color(0.012, 0.012, 0.022, 0.86)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	var glow := TextureRect.new()
	var grad := Gradient.new()
	grad.set_color(0, Color(0.35, 0.22, 0.08, 0.22))
	grad.set_color(1, Color(0, 0, 0, 0))
	var gt := GradientTexture2D.new()
	gt.gradient = grad
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.0)
	gt.fill_to = Vector2(0.5, 0.9)
	glow.texture = gt
	glow.set_anchors_preset(Control.PRESET_FULL_RECT)
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(glow)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	var m := 18 if _mobile() else 48
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, m)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 14 if _mobile() else 30)
	add_child(margin)
	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 14)
	margin.add_child(outer)
	outer.add_child(_header())
	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	outer.add_child(_scroll)
	_body = VBoxContainer.new()
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation", 18)
	_scroll.add_child(_body)
	_build_toast()
	_dialog = ConfirmDialog.new()
	add_child(_dialog)
	Net.lan_games_changed.connect(_fill_games)
	Net.start_discovery()
	_show_servers()
	_refresh_directory()

func _exit_tree() -> void:
	if not Net.is_active():
		Net.stop_discovery()

# ---- sizes ------------------------------------------------------------------------------------------------------------

func _mobile() -> bool:
	return Settings.touch_mode

func _fs(desktop: int) -> int:
	return int(round(desktop * (1.25 if _mobile() else 1.0)))

func _btn_h() -> float:
	return 78.0 if _mobile() else 56.0

func _width() -> float:
	return maxf(320.0, size.x - (36.0 if _mobile() else 96.0))

## Columns for cards at least `min_w` wide.
func _cols(min_w: float, most := 3) -> int:
	return clampi(int(_width() / min_w), 1, most)

# ---- header, toast ----------------------------------------------------------------------------------------------------

func _header() -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	var crest := TextureRect.new()
	crest.texture = UIArt.ui_icon("crown")
	crest.custom_minimum_size = Vector2(54, 54)
	crest.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	crest.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	crest.modulate = UITheme.GOLD
	h.add_child(crest)
	var tv := VBoxContainer.new()
	tv.add_theme_constant_override("separation", 0)
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(tv)
	tv.add_child(UITheme.title("Beyond Heroes", _fs(40), UITheme.GOLD))
	var sub := UITheme.label("Choose where your story is kept", _fs(18), UITheme.TEXT_DIM, UITheme.body_font())
	sub.name = "Subtitle"
	tv.add_child(sub)
	_status_pill = UITheme.label("Checking the official server…", _fs(17), UITheme.TEXT_DIM, UITheme.body_bold())
	_status_pill.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if not _mobile() or size.x > 900:
		h.add_child(_status_pill)
	h.add_child(_icon_btn("settings", "Server Settings", _show_settings))
	h.add_child(_icon_btn("back", "Back", go_back))
	return h

func _icon_btn(icon: String, tip: String, cb: Callable) -> Button:
	var b := Button.new()
	b.icon = UIArt.ui_icon(icon)
	b.expand_icon = true
	b.tooltip_text = tip
	b.focus_mode = Control.FOCUS_NONE
	var s := 72.0 if _mobile() else 54.0
	b.custom_minimum_size = Vector2(s, s)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.pressed.connect(cb)
	return b

func _build_toast() -> void:
	_toast = PanelContainer.new()
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.09, 0.07, 0.05, 0.97)
	st.set_border_width_all(2)
	st.border_color = UITheme.GOOD
	st.set_corner_radius_all(10)
	st.set_content_margin_all(18)
	st.shadow_color = Color(0, 0, 0, 0.6)
	st.shadow_size = 14
	_toast.add_theme_stylebox_override("panel", st)
	_toast.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_toast.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_toast.offset_top = 110
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast_label = UITheme.label("", _fs(22), UITheme.PARCHMENT, UITheme.body_bold())
	_toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.add_child(_toast_label)
	_toast.modulate.a = 0.0
	add_child(_toast)

## A notice at the top of the screen (green = done, red = a problem).
func notify(text: String, good := true) -> void:
	_toast_label.text = text
	(_toast.get_theme_stylebox("panel") as StyleBoxFlat).border_color = UITheme.GOOD if good else UITheme.BAD
	_toast_label.add_theme_color_override("font_color", UITheme.PARCHMENT if good else Color(1.0, 0.8, 0.75))
	_toast.reset_size()
	_toast.offset_left = -_toast.size.x * 0.5
	_toast.offset_right = _toast.size.x * 0.5
	if _toast_tw:
		_toast_tw.kill()
	_toast_tw = create_tween()
	_toast_tw.tween_property(_toast, "modulate:a", 1.0, 0.2)
	_toast_tw.tween_interval(4.0)
	_toast_tw.tween_property(_toast, "modulate:a", 0.0, 0.6)
	Audio.play_ui(&"level_up" if good else &"ui_error")

# ---- building blocks --------------------------------------------------------------------------------------------------

func _clear(title: String, subtitle := "") -> void:
	for child in _body.get_children():
		_body.remove_child(child)
		child.queue_free()
	_list = null
	_scroll.scroll_vertical = 0
	var sub := find_child("Subtitle", true, false) as Label
	if sub:
		sub.text = title if subtitle == "" else "%s · %s" % [title, subtitle]
	_status = _text("", _fs(19), UITheme.GOLD)
	_body.add_child(_status)

func _text(value: String, fs := -1, col := UITheme.PARCHMENT) -> Label:
	var label := UITheme.label(value, fs if fs > 0 else _fs(19), col, UITheme.body_font())
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label

func _heading(t: String) -> Label:
	return UITheme.title(t, _fs(28), UITheme.GOLD)

func _button(label: String, callback: Callable, parent: Node = null, primary := true, w := 260.0) -> Button:
	var button := UIWindow.button(label, callback, &"PrimaryButton" if primary else &"", w)
	button.custom_minimum_size.y = _btn_h()
	button.add_theme_font_size_override("font_size", _fs(20))
	(parent if parent else _body).add_child(button)
	return button

func _field(parent: Node, label: String, placeholder: String, secret := false) -> LineEdit:
	parent.add_child(UITheme.label(label, _fs(18), UITheme.TEXT_DIM, UITheme.body_bold()))
	var field := LineEdit.new()
	field.placeholder_text = placeholder
	field.secret = secret
	field.custom_minimum_size.y = 74.0 if _mobile() else 56.0
	field.add_theme_font_size_override("font_size", _fs(22))
	field.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(field)
	return field

## A clickable box: hover lights its border, a click or a tap runs `on_click`.
func _card(accent: Color, on_click: Callable, min_h := 0.0) -> Array:
	var p := PanelContainer.new()
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.075, 0.06, 0.05, 0.93)
	st.set_border_width_all(2)
	st.border_color = accent.darkened(0.35)
	st.set_corner_radius_all(12)
	st.set_content_margin_all(22 if _mobile() else 18)
	st.shadow_color = Color(0, 0, 0, 0.5)
	st.shadow_size = 8
	p.add_theme_stylebox_override("panel", st)
	p.custom_minimum_size.y = min_h
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(v)
	if on_click.is_valid():
		p.mouse_filter = Control.MOUSE_FILTER_STOP
		p.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		p.mouse_entered.connect(func() -> void:
			st.border_color = accent
			st.bg_color = Color(0.11, 0.085, 0.06, 0.96))
		p.mouse_exited.connect(func() -> void:
			st.border_color = accent.darkened(0.35)
			st.bg_color = Color(0.075, 0.06, 0.05, 0.93))
		p.gui_input.connect(func(e: InputEvent) -> void:
			if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT and not e.pressed and p.get_rect().has_point(p.position + e.position):
				Audio.play_ui(&"ui_open")
				on_click.call())
	return [p, v]

func _icon(name: String, s: float, tint: Color) -> TextureRect:
	var t := TextureRect.new()
	t.texture = UIArt.ui_icon(name)
	t.custom_minimum_size = Vector2(s, s)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.modulate = tint
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t

func _grid(cols: int) -> GridContainer:
	var g := GridContainer.new()
	g.columns = cols
	g.add_theme_constant_override("h_separation", 16)
	g.add_theme_constant_override("v_separation", 16)
	g.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return g

# ---- home: the three realms and the games nearby ------------------------------------------------------------------------

func _show_servers() -> void:
	_view = "servers"
	_clear("Choose How to Play")
	var cols := _cols(420.0)
	var row := _grid(cols)
	_body.add_child(row)
	var saved := SavedAccounts.for_server(Official.url)
	var official_note := "Signed in as %s" % Official.userid if Official.token != "" else ("%d saved account%s on this device" % [saved.size(), "" if saved.size() == 1 else "s"] if not saved.is_empty() else "Create an account or sign in")
	row.add_child(_mode_card("crown", OFFICIAL_COLOR, "Official Server", _official_status_text(),
		"Up to 12 players. Your characters are saved on the server and follow you to any device. Existing offline progress can be imported once.",
		official_note, "Enter the Realm", _official_warning))
	row.add_child(_mode_card("save", OFFLINE_COLOR, "Offline Play", "Always available",
		"No internet, no account. Continue your heroes on this device or start a new one.",
		"Saves stay on this device", "Play Offline", func() -> void: selected.emit("offline", {})))
	var n := _game_count()
	row.add_child(_mode_card("teleport", CUSTOM_COLOR, "Custom Games", "%d game%s found" % [n, "" if n == 1 else "s"],
		"Host a fresh game for your friends or join one nearby. Custom characters belong to that game only.",
		"LAN games appear by themselves", "Browse Games", _show_custom))
	# the custom games around you, as cards
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 12)
	_body.add_child(head)
	var hl := _heading("Custom Games Near You")
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hl)
	_button("Refresh", _refresh_directory, head, false, 180.0)
	_button("See All & Host", _show_custom, head, true, 240.0)
	_list = _grid(_cols(380.0))
	_body.add_child(_list)
	_fill_games()

func _official_status_text() -> String:
	if _checking and _health.is_empty():
		return "Checking…"
	if _health.has("error"):
		return "Unreachable right now"
	if _health.is_empty():
		return "Not checked yet"
	return "%s · %d / 12 players" % ["Online" if _health.get("game_online", false) else "Accounts online", int(_health.get("players", 0))]

func _mode_card(icon: String, accent: Color, title: String, status: String, desc: String, note: String, action: String, cb: Callable) -> Control:
	var c := _card(accent, cb, 300.0 if not _mobile() else 0.0)
	var v: VBoxContainer = c[1]
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 14)
	v.add_child(top)
	top.add_child(_icon(icon, 64.0 if not _mobile() else 72.0, accent))
	var tv := VBoxContainer.new()
	tv.add_theme_constant_override("separation", 2)
	top.add_child(tv)
	tv.add_child(UITheme.title(title, _fs(30), accent.lightened(0.15)))
	var good := status.begins_with("Online") or status.begins_with("Accounts") or status == "Always available" or (status.ends_with("found") and not status.begins_with("0"))
	var badge := UITheme.label("● " + status, _fs(17), UITheme.GOOD if good else (UITheme.BAD if status.begins_with("Unreachable") else UITheme.TEXT_DIM), UITheme.body_bold())
	tv.add_child(badge)
	v.add_child(_text(desc, _fs(18), UITheme.TEXT))
	var sp := Control.new()
	sp.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(sp)
	v.add_child(UITheme.label(note, _fs(16), UITheme.TEXT_DIM, UITheme.body_font()))
	var go := UITheme.label("%s  ›" % action, _fs(22), accent, UITheme.body_bold())
	go.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	v.add_child(go)
	return _ignore_mouse_inside(c[0])

func _ignore_mouse_inside(p: PanelContainer) -> Control:
	for n in p.find_children("*", "Control", true, false):
		if not (n is BaseButton) and not (n is LineEdit):
			(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	return p

func _official_warning() -> void:
	_dialog.ask("Official Server", "Only official characters are saved on this server. You need an account and a connection while playing. Importing copies your offline progress; the offline original remains on your device and evolves separately.", func() -> void:
		if Official.token == "":
			_show_auth()
		else:
			_show_characters(), "Continue")

func _custom_warning(room: Dictionary) -> void:
	_dialog.ask("Custom Game", "This custom game starts with new characters. Existing offline and official characters cannot enter it. Its characters are saved on your device for this room, and their rewards do not transfer to the official server.", func() -> void: selected.emit("custom", room), "Continue")

# ---- custom games -------------------------------------------------------------------------------------------------------

func _show_custom() -> void:
	_view = "custom"
	_clear("Custom Games", "host or join")
	var cols := 2 if _width() > 1100 else 1
	var split := _grid(cols)
	_body.add_child(split)
	# host a game
	var hc := _card(CUSTOM_COLOR, Callable())
	var hv: VBoxContainer = hc[1]
	split.add_child(hc[0])
	hv.add_child(_heading("Host a New Game"))
	hv.add_child(_text("Up to 12 players. Friends on your network see it at once; internet friends need your game port open.", _fs(17), UITheme.TEXT_DIM))
	var name_field := _field(hv, "Game name", "My friends' game")
	name_field.text = "Friends' Game"
	name_field.max_length = 48
	_button("Create Custom Game", func() -> void:
		var game_name := name_field.text.strip_edges()
		if game_name.length() < 2:
			notify("Enter a game name with at least two characters.", false)
			return
		_custom_warning({"room": Crypto.new().generate_random_bytes(16).hex_encode(), "name": game_name, "host": true}), hv, true, 320.0)
	var saved_rooms := SaveSystem.saved_custom_rooms().filter(func(r): return r.get("host", false))
	if not saved_rooms.is_empty():
		hv.add_child(UITheme.label("Your games on this device", _fs(19), UITheme.GOLD, UITheme.body_bold()))
		for saved: Dictionary in saved_rooms:
			var room := saved.duplicate(true)
			_button("Host Again: " + String(room.get("name", "Custom Game")), func() -> void: selected.emit("custom", room), hv, false, 320.0)
	# the games out there
	var right := VBoxContainer.new()
	right.add_theme_constant_override("separation", 12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	split.add_child(right)
	var head := HBoxContainer.new()
	right.add_child(head)
	var hl := _heading("Games You Can Join")
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hl)
	_button("Refresh", _refresh_directory, head, false, 170.0)
	_list = _grid(1 if cols == 2 and _width() < 1700 else (2 if cols == 2 else _cols(380.0, 2)))
	right.add_child(_list)
	_fill_games()
	_button("Back to Realms", _show_servers, null, false, 260.0)

func _game_count() -> int:
	var rooms := {}
	for game: Dictionary in _directory:
		rooms[String(game.get("room", ""))] = true
	for ip in Net.lan_games:
		rooms[String(Net.lan_games[ip].get("room", ip))] = true
	rooms.erase("")
	return rooms.size()

func _refresh_directory() -> void:
	if _checking:
		return
	_checking = true
	if _view == "servers":
		_status.text = "Checking the official server and looking for custom games…"
	var health := await Official.check_server()
	if not is_instance_valid(self):
		return
	_health = health
	var result := await Official.request("/custom/list", {}, HTTPClient.METHOD_GET, false)
	if not is_instance_valid(self):
		return
	_checking = false
	_directory = result.get("games", [])
	_status_pill.text = "Official: " + _official_status_text()
	_status_pill.add_theme_color_override("font_color", UITheme.BAD if health.has("error") else UITheme.GOOD)
	if _view == "servers":
		_show_servers()
		_status.text = String(health.error) + " Offline Play and LAN custom games remain available." if health.has("error") else ""
	elif _view == "custom":
		_fill_games()

func _fill_games() -> void:
	if not (_view in ["servers", "custom"]) or _list == null or not is_instance_valid(_list):
		return
	for child in _list.get_children():
		_list.remove_child(child)
		child.queue_free()
	var games := {}
	for game: Dictionary in _directory:
		games[String(game.get("room", ""))] = game
	for ip in Net.lan_games:
		var game: Dictionary = Net.lan_games[ip].duplicate()
		if String(game.get("room", "")) != "":
			game["address"] = ip
			game["lan"] = true
			games[String(game.room)] = game # LAN route takes precedence over an internet route.
	var shown := 0
	for game: Dictionary in games.values():
		if _view == "servers" and shown >= 6:
			break
		_list.add_child(_game_card(game))
		shown += 1
	if games.is_empty():
		var c := _card(CUSTOM_COLOR.darkened(0.3), Callable())
		(c[1] as VBoxContainer).add_child(_text("No custom games found yet. Games on your network appear here by themselves; internet games appear while the official service is reachable. Or host your own!", _fs(18), UITheme.TEXT_DIM))
		_list.add_child(c[0])

func _game_card(game: Dictionary) -> Control:
	var room := game.duplicate(true)
	var players := int(game.get("players", 1))
	var most := int(game.get("max", 12))
	var full := players >= most
	var other_version := int(game.get("bh", Net.PROTOCOL)) != Net.PROTOCOL
	var can := not full and not other_version
	var c := _card(CUSTOM_COLOR if can else UITheme.TEXT_MUTED, (func() -> void: _custom_warning(room)) if can else Callable())
	var v: VBoxContainer = c[1]
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 10)
	v.add_child(top)
	top.add_child(_icon("teleport", 40.0, CUSTOM_COLOR))
	var name := UITheme.label(String(game.get("name", "Custom Game")), _fs(23), UITheme.PARCHMENT, UITheme.body_bold())
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name.clip_text = true
	top.add_child(name)
	top.add_child(UITheme.label("LAN" if game.get("lan", false) else "Internet", _fs(15), UITheme.GOOD if game.get("lan", false) else CUSTOM_COLOR, UITheme.body_bold()))
	var bar := ProgressBar.new()
	bar.max_value = most
	bar.value = players
	bar.show_percentage = false
	bar.custom_minimum_size.y = 10
	v.add_child(bar)
	var info := "%d / %d players" % [players, most]
	if full:
		info += " · Full"
	elif other_version:
		info += " · Different game version"
	v.add_child(UITheme.label(info, _fs(17), UITheme.BAD if not can else UITheme.TEXT, UITheme.body_font()))
	if String(game.get("address", "")) != "":
		v.add_child(UITheme.label(String(game.address), _fs(15), UITheme.TEXT_DIM, UITheme.number_font()))
	if can:
		var go := UITheme.label("Join  ›", _fs(21), CUSTOM_COLOR, UITheme.body_bold())
		go.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		v.add_child(go)
	return _ignore_mouse_inside(c[0])

# ---- settings ----------------------------------------------------------------------------------------------------------

func _show_settings() -> void:
	_view = "settings"
	_clear("Official Server Settings")
	var c := _centered_card(1000.0)
	c.add_child(_heading("Server Address"))
	c.add_child(_text("Use the address and public certificate supplied by the server owner. Account connections always verify encryption. Never share the server's private key.", _fs(17), UITheme.TEXT_DIM))
	var address := _field(c, "Server address", "https://192.168.1.20:8443")
	address.text = Official.url
	var certificate := _field(c, "Public certificate file (blank for a public certificate authority)", "res://server/official_ca.crt")
	certificate.text = Official.certificate_path
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	c.add_child(row)
	_button("Choose Certificate File", func() -> void:
		var dialog := FileDialog.new()
		dialog.access = FileDialog.ACCESS_FILESYSTEM
		dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
		dialog.filters = PackedStringArray(["*.crt,*.pem ; Public certificates"])
		add_child(dialog)
		dialog.file_selected.connect(func(path: String) -> void:
			certificate.text = path
			dialog.queue_free())
		dialog.canceled.connect(dialog.queue_free)
		dialog.popup_centered_ratio(0.75), row, false, 300.0)
	_button("Save Settings", func() -> void:
		var error := Official.configure(address.text, certificate.text)
		if error == "":
			notify("Server settings saved.")
			_health = {}
			_show_servers()
			_refresh_directory()
		else:
			notify(error, false), row, true, 240.0)
	_button("Back", _show_servers, row, false, 160.0)

## A panel centred on the page, at most `w` wide (full width on a phone). Returns its content box.
func _centered_card(w: float) -> VBoxContainer:
	var center := CenterContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_child(center)
	var c := _card(UITheme.BRONZE, Callable())
	(c[0] as Control).custom_minimum_size.x = minf(w, _width())
	center.add_child(c[0])
	return c[1]

# ---- sign in -------------------------------------------------------------------------------------------------------------

func _show_auth(mode := -1) -> void:
	_view = "auth"
	if mode >= 0:
		_auth_mode = mode
	_clear("Official Server Account", Official.url.trim_prefix("https://"))
	var wide := _width() > 1150
	var center := CenterContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_child(center)
	var page := _grid(2 if wide else 1)
	page.custom_minimum_size.x = minf(1480.0, _width())
	page.add_theme_constant_override("h_separation", 22)
	center.add_child(page)
	var form_card := _card(OFFICIAL_COLOR, Callable(), 640.0 if wide else 0.0)
	var accounts_card := _card(UITheme.BRONZE, Callable(), 640.0 if wide else 0.0)
	if wide:
		page.add_child(accounts_card[0])
		page.add_child(form_card[0])
		(accounts_card[0] as Control).custom_minimum_size.x = 560.0
	else:
		page.add_child(form_card[0])
		page.add_child(accounts_card[0])
	_build_accounts(accounts_card[1])
	_build_form(form_card[1])

func _build_accounts(v: VBoxContainer) -> void:
	v.add_child(_heading("Saved Accounts"))
	var saved := SavedAccounts.for_server(Official.url)
	if saved.is_empty():
		v.add_child(_text("Accounts you sign in with are remembered here on this device, so next time it is one click. Tick \"Remember my UserID\" when you sign in.", _fs(17), UITheme.TEXT_DIM))
		return
	v.add_child(_text("Choose an account. With a saved password it signs you in at once.", _fs(17), UITheme.TEXT_DIM))
	for acc: Dictionary in saved:
		var a := acc.duplicate()
		var c := _card(OFFICIAL_COLOR, func() -> void: _use_account(a))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 14)
		(c[1] as VBoxContainer).add_child(row)
		var badge := PanelContainer.new()
		var bs := StyleBoxFlat.new()
		bs.bg_color = Color.from_hsv(float(absi(hash(String(a.userid))) % 360) / 360.0, 0.45, 0.42)
		bs.set_corner_radius_all(40)
		badge.add_theme_stylebox_override("panel", bs)
		badge.custom_minimum_size = Vector2(60, 60)
		var ini := UITheme.title(String(a.userid).left(1).to_upper(), _fs(28), UITheme.PARCHMENT)
		ini.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ini.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		badge.add_child(ini)
		row.add_child(badge)
		var tv := VBoxContainer.new()
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(tv)
		tv.add_child(UITheme.label(String(a.userid), _fs(23), UITheme.PARCHMENT, UITheme.body_bold()))
		tv.add_child(UITheme.label("Password saved · one-click sign in" if a.remember_password else "Enter your password", _fs(15),
			UITheme.GOOD if a.remember_password else UITheme.TEXT_DIM, UITheme.body_font()))
		_ignore_mouse_inside(c[0])
		var forget := _icon_btn("trash", "Forget this account on this device", func() -> void:
			SavedAccounts.forget(Official.url, String(a.userid))
			notify("%s is no longer saved on this device." % a.userid)
			_show_auth())
		row.add_child(forget)
		v.add_child(c[0])

var _user: LineEdit
var _pass: LineEdit
var _confirm: LineEdit
var _recovery: LineEdit
var _remember_id: CheckBox
var _remember_pw: CheckBox

func _build_form(v: VBoxContainer) -> void:
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 8)
	v.add_child(tabs)
	var group := ButtonGroup.new()
	for i in 3:
		var mode := i
		var b := UIWindow.button(["Sign In", "Create Account", "Recover"][i], func() -> void: _show_auth(mode), &"", 0.0)
		b.toggle_mode = true
		b.button_group = group
		b.button_pressed = i == _auth_mode
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size.y = _btn_h()
		b.add_theme_font_size_override("font_size", _fs(20))
		b.add_theme_color_override("font_pressed_color", UITheme.GOLD)
		tabs.add_child(b)
	v.add_child(_text(["Welcome back. Sign in to reach your official characters.",
		"Choose a UserID (3–32 letters, numbers or underscores) and a password of 12 to 128 characters. The server keeps only a salted hash of it.",
		"Lost your password? Your recovery code sets a new one."][_auth_mode], _fs(17), UITheme.TEXT_DIM))
	_user = _field(v, "UserID", "3–32 letters, numbers or underscores")
	_user.max_length = 32
	_pass = _field(v, "New Password" if _auth_mode == 2 else "Password", "At least 12 characters", true)
	_pass.max_length = 128
	var show := CheckBox.new()
	show.text = "Show password"
	show.add_theme_font_size_override("font_size", _fs(17))
	show.toggled.connect(func(on: bool) -> void:
		_pass.secret = not on
		if _confirm:
			_confirm.secret = not on)
	v.add_child(show)
	_confirm = null
	_recovery = null
	if _auth_mode != 0:
		_confirm = _field(v, "Confirm password", "Repeat your password", true)
		_confirm.max_length = 128
	if _auth_mode == 2:
		_recovery = _field(v, "Recovery code", "Keep this code private", true)
	var rem := HFlowContainer.new()
	rem.add_theme_constant_override("h_separation", 24)
	v.add_child(rem)
	_remember_id = CheckBox.new()
	_remember_id.text = "Remember my UserID"
	_remember_id.button_pressed = true
	_remember_pw = CheckBox.new()
	_remember_pw.text = "Remember my password"
	for cb in [_remember_id, _remember_pw]:
		cb.add_theme_font_size_override("font_size", _fs(18))
		cb.custom_minimum_size.y = 56.0 if _mobile() else 40.0
		rem.add_child(cb)
	_remember_pw.toggled.connect(func(on: bool) -> void: if on: _remember_id.button_pressed = true)
	_remember_id.toggled.connect(func(on: bool) -> void: if not on: _remember_pw.button_pressed = false)
	v.add_child(_text("A remembered password is kept only on this device, encrypted. Leave it unticked on a shared computer.", _fs(15), UITheme.TEXT_MUTED))
	var saved := SavedAccounts.for_server(Official.url)
	if _auth_mode == 0 and not saved.is_empty():
		_user.text = String(saved[0].userid)
		_remember_pw.button_pressed = bool(saved[0].remember_password)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	v.add_child(row)
	var submit := _button(["Sign In", "Create Account", "Set New Password"][_auth_mode], _submit_auth, row, true, 300.0)
	submit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_button("Back", _show_servers, row, false, 160.0)
	var last := _recovery if _recovery else (_confirm if _confirm else _pass)
	last.text_submitted.connect(func(_value: String) -> void: _submit_auth())
	_user.text_submitted.connect(func(_value: String) -> void: _pass.grab_focus())
	if not _mobile():
		(_pass if _user.text != "" else _user).grab_focus.call_deferred()

func _use_account(a: Dictionary) -> void:
	_auth_mode = 0
	_show_auth()
	_user.text = String(a.userid)
	_remember_id.button_pressed = true
	if a.remember_password and String(a.password) != "":
		_remember_pw.button_pressed = true
		_pass.text = String(a.password)
		_submit_auth()
	else:
		_pass.grab_focus()

func _submit_auth() -> void:
	if _busy or _user == null:
		return
	var user := _user.text.strip_edges()
	var pw := _pass.text
	if user.length() < 3:
		notify("Enter your UserID (at least 3 characters).", false)
		return
	if _auth_mode != 0 and _confirm and pw != _confirm.text:
		notify("The passwords do not match.", false)
		return
	_busy = true
	_status.text = "Connecting securely…"
	var action: String = ["login", "register", "recover"][_auth_mode]
	var result := await Official.authenticate(action, user, pw, _recovery.text if _recovery else "")
	_busy = false
	if not is_instance_valid(self):
		return
	var remember_id := _remember_id.button_pressed if is_instance_valid(_remember_id) else false
	var remember_pw := _remember_pw.button_pressed if is_instance_valid(_remember_pw) else false
	if result.has("error"):
		_status.text = String(result.error)
		notify(String(result.error), false)
		if is_instance_valid(_pass):
			_pass.text = ""
		return
	var userid := Official.userid if Official.userid != "" else user
	if remember_id:
		SavedAccounts.remember(Official.url, userid, pw, remember_pw)
	else:
		SavedAccounts.forget(Official.url, userid)
	match action:
		"register":
			notify("Account created successfully! Welcome to Beyond Heroes, %s." % userid)
		"recover":
			notify("Your new password is set, %s." % userid)
		_:
			notify("Signed in as %s." % userid)
	if result.has("recovery_code"):
		_show_recovery(String(result.recovery_code), action == "register")
	else:
		_show_characters()

func _show_recovery(code: String, created := false) -> void:
	_view = "recovery"
	_clear("Save Your Recovery Code")
	var c := _centered_card(1000.0)
	if created:
		var ok_row := HBoxContainer.new()
		ok_row.add_theme_constant_override("separation", 12)
		c.add_child(ok_row)
		ok_row.add_child(_icon("check", 48.0, UITheme.GOOD))
		ok_row.add_child(UITheme.title("Account created successfully", _fs(30), UITheme.GOOD))
	c.add_child(_heading("Your Recovery Code"))
	c.add_child(_text("Write down this private code. It lets you reset a forgotten password. It is shown once and changes after recovery. The server owner cannot read your password.", _fs(18), UITheme.TEXT))
	var field := _field(c, "Recovery code", "")
	field.text = code
	field.editable = false
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	c.add_child(row)
	_button("Copy Recovery Code", func() -> void:
		DisplayServer.clipboard_set(code)
		notify("Recovery code copied."), row, false, 300.0)
	_button("I Have Saved My Code", func() -> void:
		_show_characters()
		_dialog.ask("Import Existing Progress", "Would you like to copy an existing offline character to your official account? Its original save stays available in Offline Play.", _show_import, "Choose a Character"), row, true, 320.0)

# ---- official characters ---------------------------------------------------------------------------------------------

func _show_characters() -> void:
	_view = "characters"
	_clear("Official Characters", Official.userid)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 12)
	_body.add_child(top)
	var hl := _heading("Your Heroes on the Official Server")
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(hl)
	_button("Refresh", func() -> void:
		if _busy:
			return
		_busy = true
		var result := await Official.refresh_characters()
		_busy = false
		if result.has("error"):
			notify(String(result.error), false)
		else:
			_show_characters(), top, false, 170.0)
	_button("Sign Out", func() -> void:
		await Official.logout()
		notify("Signed out.")
		_show_servers(), top, false, 170.0)
	_body.add_child(_text("Stored on the official server. Playing alone on that server still saves your progress. They cannot enter Offline Play or Custom Games.", _fs(17), UITheme.TEXT_DIM))
	var grid := _grid(_cols(400.0))
	_body.add_child(grid)
	for character: Dictionary in Official.characters:
		var id := String(character.id)
		var c := _card(OFFICIAL_COLOR, func() -> void: official_play.emit(id))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 16)
		(c[1] as VBoxContainer).add_child(row)
		var por := TextureRect.new()
		MainMenu.hero_picture(por, character, String(character.get("class", "knight")).to_lower())      # bh-031: their own picture
		por.custom_minimum_size = Vector2(96, 96)
		por.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		por.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		row.add_child(por)
		var tv := VBoxContainer.new()
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(tv)
		tv.add_child(UITheme.label(String(character.get("name", "Hero")), _fs(26), UITheme.PARCHMENT, UITheme.body_bold()))
		tv.add_child(UITheme.label("Level %d %s" % [int(character.get("level", 1)), String(character.get("class", "")).capitalize()], _fs(18), UITheme.GOLD, UITheme.body_font()))
		tv.add_child(UITheme.label(String(character.get("map", "")).capitalize(), _fs(16), UITheme.TEXT_DIM, UITheme.body_font()))
		var go := UITheme.label("Play  ›", _fs(22), OFFICIAL_COLOR, UITheme.body_bold())
		go.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		(c[1] as VBoxContainer).add_child(go)
		grid.add_child(_ignore_mouse_inside(c[0]))
	if Official.characters.size() < SaveSystem.SLOTS:
		grid.add_child(_action_card("plus", "Create a New Character", "Start a new official hero.", func() -> void: official_new.emit()))
		grid.add_child(_action_card("load", "Import Offline Progress", "Copy an offline hero here once.", _show_import))
	if Official.characters.is_empty():
		_status.text = "You have no official characters yet. Create one or import your existing offline progress."
	_button("Back to Realms", _show_servers, null, false, 260.0)

func _action_card(icon: String, title: String, desc: String, cb: Callable) -> Control:
	var c := _card(UITheme.BRONZE, cb, 150.0)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	(c[1] as VBoxContainer).add_child(row)
	row.add_child(_icon(icon, 64.0, UITheme.GOLD))
	var tv := VBoxContainer.new()
	row.add_child(tv)
	tv.add_child(UITheme.label(title, _fs(24), UITheme.GOLD, UITheme.body_bold()))
	tv.add_child(UITheme.label(desc, _fs(16), UITheme.TEXT_DIM, UITheme.body_font()))
	return _ignore_mouse_inside(c[0])

func _show_import() -> void:
	_view = "import"
	_clear("Import an Offline Character")
	_body.add_child(_text("Import is a one-time copy for each character. Future offline changes will not replace official progress. Your original local save is kept. Custom-game characters cannot be imported.", _fs(17), UITheme.TEXT_DIM))
	var grid := _grid(_cols(400.0))
	_body.add_child(grid)
	var found := false
	for slot in SaveSystem.SLOTS:
		var data := SaveSystem.read_legacy_slot(slot)
		if data.is_empty():
			continue
		found = true
		var local_slot := slot
		var hero: Dictionary = data.hero
		var cls := String(hero.get("class", "knight"))
		var c := _card(OFFLINE_COLOR, func() -> void:
			_dialog.ask("Import Character", "Copy this offline character into an empty official slot? The original stays on your device.", func() -> void: _import_slot(local_slot), "Import"))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 16)
		(c[1] as VBoxContainer).add_child(row)
		var por := TextureRect.new()
		MainMenu.hero_picture(por, hero, cls)      # bh-031: their own picture
		por.custom_minimum_size = Vector2(80, 80)
		por.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		por.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		row.add_child(por)
		var tv := VBoxContainer.new()
		row.add_child(tv)
		tv.add_child(UITheme.label(String(hero.get("name", "Hero")), _fs(24), UITheme.PARCHMENT, UITheme.body_bold()))
		tv.add_child(UITheme.label("Level %d %s · Slot %d" % [int(hero.get("progress", {}).get("level", 1)), cls.capitalize(), slot + 1], _fs(17), UITheme.TEXT_DIM, UITheme.body_font()))
		grid.add_child(_ignore_mouse_inside(c[0]))
	if not found:
		_body.add_child(_text("No existing offline characters were found on this device.", _fs(18), UITheme.TEXT_DIM))
	_button("Back to Official Characters", _show_characters, null, false, 340.0)

func _import_slot(slot: int) -> void:
	if _busy:
		return
	var target := -1
	for candidate in SaveSystem.SLOTS:
		if Official.slot_summary(candidate).is_empty():
			target = candidate
			break
	if target < 0:
		notify("All eight official slots are occupied.", false)
		return
	var data := SaveSystem.read_legacy_slot(slot)
	var hero := HeroData.from_dict(data.get("hero", {}))
	if hero == null:
		notify("This local character could not be read.", false)
		return
	_busy = true
	_status.text = "Copying the character to the server…"
	var result := await Official.add_character(hero, target, SaveSystem.legacy_identity(slot, hero))
	_busy = false
	if result.has("error"):
		notify(String(result.error), false)
	else:
		_show_characters()
		notify("This character was already imported. Its official progress was kept." if result.get("already_imported", false) else "Import complete. Your original offline save is still on this device.")

# ---- outside calls ---------------------------------------------------------------------------------------------------

func show_error(message: String) -> void:
	if _status:
		_status.text = message
	notify(message, false)

func go_back() -> void:
	if _dialog.visible:
		_dialog.cancel()
	elif _view == "servers":
		selected.emit("back", {})
	elif _view in ["import", "recovery"] and Official.token != "":
		_show_characters()
	else:
		_show_servers()

func _rebuild_view() -> void:
	match _view:
		"servers": _show_servers()
		"custom": _show_custom()
		"auth": _show_auth()
		"characters": _show_characters()
		"import": _show_import()
		"settings": _show_settings()

func _process(delta: float) -> void:
	if _relayout_t >= 0.0:
		_relayout_t -= delta
		if _relayout_t < 0.0 and absf(size.x - _last_width) > 40.0 and _view != "auth" and _view != "recovery":
			_last_width = size.x
			_rebuild_view()
	if _view != "servers" and _view != "custom":
		return
	_refresh_t += delta
	if _refresh_t >= 20.0:
		_refresh_t = 0.0
		_refresh_directory()
