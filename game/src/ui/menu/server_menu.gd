class_name ServerMenu
extends Control
## First menu: Official Server, Offline Play, and discovered player-hosted games.
signal selected(mode: String, room: Dictionary)
signal official_play(character: String)
signal official_new

var _body: VBoxContainer
var _status: Label
var _list: VBoxContainer
var _busy := false
var _checking := false
var _view := "servers"
var _refresh_t := 0.0
var _directory: Array = []
var _dialog: ConfirmDialog

func _ready() -> void:
	theme = UITheme.theme()
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	size = get_viewport_rect().size
	get_viewport().size_changed.connect(func() -> void: size = get_viewport_rect().size)
	var shade := ColorRect.new()
	shade.color = Color(0.015, 0.02, 0.035, 0.94)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 90)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 45)
	add_child(margin)
	var panel := PanelContainer.new()
	panel.theme_type_variation = &"GlassPanel"
	margin.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	_body = VBoxContainer.new()
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation", 14)
	scroll.add_child(_body)
	_dialog = ConfirmDialog.new()
	add_child(_dialog)
	Net.lan_games_changed.connect(_fill_games)
	Net.start_discovery()
	_show_servers()
	_refresh_directory()

func _exit_tree() -> void:
	if not Net.is_active():
		Net.stop_discovery()

func _clear(title: String) -> void:
	for child in _body.get_children():
		_body.remove_child(child)
		child.queue_free()
	_list = null
	_body.add_child(UITheme.title(title, 36, UITheme.GOLD))
	_status = _text("")
	_body.add_child(_status)

func _text(value: String) -> Label:
	var label := UITheme.label(value, 21, UITheme.PARCHMENT, UITheme.body_font())
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label

func _button(label: String, callback: Callable, parent: Node = null) -> Button:
	var button := UIWindow.button(label, callback, &"PrimaryButton", 280.0)
	button.custom_minimum_size.y = 56
	(parent if parent else _body).add_child(button)
	return button

func _field(label: String, placeholder: String, secret := false) -> LineEdit:
	_body.add_child(_text(label))
	var field := LineEdit.new()
	field.placeholder_text = placeholder
	field.secret = secret
	field.custom_minimum_size.y = 52
	field.add_theme_font_size_override("font_size", 22)
	_body.add_child(field)
	return field

func _show_servers() -> void:
	_view = "servers"
	_clear("Choose How to Play")
	_body.add_child(_text("Official progress is saved on the server. Offline characters stay on this device. Custom games use separate characters and start fresh."))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	_body.add_child(row)
	var official := VBoxContainer.new()
	official.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(official)
	official.add_child(UITheme.title("Official Beyond Heroes", 28, UITheme.GOLD))
	official.add_child(_text("Up to 12 players. Register or sign in to use your official characters. You can import existing offline progress once for each character."))
	_button("Official Server", _official_warning, official)
	var offline := VBoxContainer.new()
	offline.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(offline)
	offline.add_child(UITheme.title("Offline Play", 28, UITheme.GOLD))
	offline.add_child(_text("Play without internet or an account. Continue your existing characters or create a new one. Saves stay on this device."))
	_button("Play Offline", func() -> void: selected.emit("offline", {}), offline)
	_body.add_child(HSeparator.new())
	_body.add_child(UITheme.title("Custom Games", 28, UITheme.GOLD))
	_body.add_child(_text("Host a fresh game for up to 12 players or join one below. Characters are saved locally for that room. These rewards do not change official or offline characters."))
	var name_field := _field("New custom game name", "My friends' game")
	name_field.text = "Friends' Game"
	name_field.max_length = 48
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 16)
	_body.add_child(actions)
	_button("Create Custom Game", func() -> void:
		var game_name := name_field.text.strip_edges()
		if game_name.length() < 2:
			_status.text = "Enter a game name with at least two characters."
			return
		_custom_warning({"room": Crypto.new().generate_random_bytes(16).hex_encode(), "name": game_name, "host": true}), actions)
	_button("Refresh Server List", _refresh_directory, actions)
	_button("Server Settings", _show_settings, actions)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 10)
	_body.add_child(_list)
	_fill_games()
	var saved_rooms := SaveSystem.saved_custom_rooms()
	if not saved_rooms.is_empty():
		_body.add_child(UITheme.title("Saved Custom Games on This Device", 26, UITheme.GOLD))
		for saved: Dictionary in saved_rooms:
			var room := saved.duplicate(true)
			if room.get("host", false):
				_button("Host Again: " + String(room.get("name", "Custom Game")), func() -> void: selected.emit("custom", room))
	_button("Back to Main Menu", func() -> void: selected.emit("back", {}))

func _official_warning() -> void:
	_dialog.ask("Official Server", "Only official characters are saved on this server. You need an account and a connection while playing. Importing copies your offline progress; the offline original remains on your device and evolves separately.", func() -> void:
		if Official.token == "":
			_show_auth()
		else:
			_show_characters(), "Continue")

func _custom_warning(room: Dictionary) -> void:
	_dialog.ask("Custom Game", "This custom game starts with new characters. Existing offline and official characters cannot enter it. Its characters are saved on your device for this room, and their rewards do not transfer to the official server.", func() -> void: selected.emit("custom", room), "Continue")

func _refresh_directory() -> void:
	if _checking:
		return
	_checking = true
	if _view == "servers":
		_status.text = "Checking the official server and looking for custom games…"
	var health := await Official.check_server()
	if not is_instance_valid(self):
		return
	var result := await Official.request("/custom/list", {}, HTTPClient.METHOD_GET, false)
	if not is_instance_valid(self):
		return
	_checking = false
	_directory = result.get("games", [])
	if _view != "servers":
		return
	_status.text = String(health.error) + " Offline Play and LAN custom games remain available." if health.has("error") else \
		"Official server: %s · %d / 12 players" % ["Online" if health.get("game_online", false) else "Game server offline; saved characters remain stored", int(health.get("players", 0))]
	_fill_games()

func _fill_games() -> void:
	if _view != "servers" or _list == null:
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
			games[String(game.room)] = game # LAN route takes precedence over an internet route.
	for game: Dictionary in games.values():
		var card := HBoxContainer.new()
		var description := _text("%s · %d / %d players · %s" % [game.get("name", "Custom Game"), int(game.get("players", 1)), int(game.get("max", 12)), game.get("address", "")])
		description.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.add_child(description)
		_list.add_child(card)
		var room := game.duplicate(true)
		var full := int(game.get("players", 1)) >= int(game.get("max", 12))
		var button := _button("Full" if full else "Join", func() -> void: _custom_warning(room), card)
		button.disabled = full or int(game.get("bh", 0)) != Net.PROTOCOL
	if games.is_empty():
		_list.add_child(_text("No custom games found yet. Games on your network appear automatically. Internet hosts appear while the official service is reachable; their game port must also be reachable."))

func _show_settings() -> void:
	_view = "settings"
	_clear("Official Server Settings")
	_body.add_child(_text("Use the address and public certificate supplied by the server owner. Account connections always verify encryption. Never share the server's private key."))
	var address := _field("Server address", "https://192.168.1.20:8443")
	address.text = Official.url
	var certificate := _field("Public certificate file (blank for a public certificate authority)", "res://server/official_ca.crt")
	certificate.text = Official.certificate_path
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
		dialog.popup_centered_ratio(0.75))
	_button("Save Settings", func() -> void:
		var error := Official.configure(address.text, certificate.text)
		if error == "":
			_show_servers()
			_refresh_directory()
		else:
			_status.text = error)
	_button("Back", _show_servers)

func _show_auth() -> void:
	_view = "auth"
	_clear("Official Server Account")
	_body.add_child(_text("Choose a UserID and a password of 12 to 128 characters. The server stores a salted password hash. Passwords are never saved by this game."))
	var action := OptionButton.new()
	for label in ["Sign In", "Register Account", "Recover Account"]:
		action.add_item(label)
	action.custom_minimum_size.y = 52
	_body.add_child(action)
	var user := _field("UserID", "3–32 letters, numbers or underscores")
	user.max_length = 32
	var password := _field("Password (new password when recovering)", "At least 12 characters", true)
	var password_label := _body.get_child(password.get_index() - 1) as Label
	password_label.text = "Password"
	password.max_length = 128
	var confirmation := _field("Confirm password when registering or recovering", "Repeat your password", true)
	confirmation.max_length = 128
	var recovery := _field("Recovery code (account recovery only)", "Keep this code private", true)
	var confirmation_label := _body.get_child(confirmation.get_index() - 1) as Label
	var recovery_label := _body.get_child(recovery.get_index() - 1) as Label
	confirmation.visible = false
	confirmation_label.visible = false
	recovery.visible = false
	recovery_label.visible = false
	action.item_selected.connect(func(index: int) -> void:
		password_label.text = "New Password" if index == 2 else "Password"
		confirmation.visible = index != 0
		confirmation_label.visible = index != 0
		recovery.visible = index == 2
		recovery_label.visible = index == 2)
	var submit := _button("Continue", func() -> void:
		if _busy:
			return
		if action.selected != 0 and password.text != confirmation.text:
			_status.text = "The passwords do not match."
			return
		_busy = true
		_status.text = "Connecting securely…"
		var result := await Official.authenticate(["login", "register", "recover"][action.selected], user.text, password.text, recovery.text)
		_busy = false
		if not is_instance_valid(password):
			return
		password.text = ""
		confirmation.text = ""
		recovery.text = ""
		if result.has("error"):
			_status.text = String(result.error)
		elif result.has("recovery_code"):
			_show_recovery(String(result.recovery_code))
		else:
			_show_characters())
	password.text_submitted.connect(func(_value: String) -> void: submit.pressed.emit())
	_button("Back to Servers", _show_servers)

func _show_recovery(code: String) -> void:
	_view = "recovery"
	_clear("Save Your Recovery Code")
	_body.add_child(_text("Write down this private code. It lets you reset a forgotten password. It is shown once and changes after recovery. The server owner cannot read your password."))
	var field := _field("Recovery code", "")
	field.text = code
	field.editable = false
	_button("Copy Recovery Code", func() -> void: DisplayServer.clipboard_set(code))
	_button("I Have Saved My Code", func() -> void:
		_show_characters()
		_dialog.ask("Import Existing Progress", "Would you like to copy an existing offline character to your official account? Its original save stays available in Offline Play.", _show_import, "Choose a Character"))

func _show_characters() -> void:
	_view = "characters"
	_clear("Official Characters · " + Official.userid)
	_body.add_child(_text("These characters are stored on the official server. Playing alone on that server still saves your progress. They cannot enter Offline Play or Custom Games."))
	if not Official.characters.is_empty():
		for character: Dictionary in Official.characters:
			var id := String(character.id)
			var row := HBoxContainer.new()
			_body.add_child(row)
			var label := _text("%s · Level %d %s · %s" % [character.name, int(character.level), character["class"], character.map])
			label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(label)
			_button("Play", func() -> void: official_play.emit(id), row)
	else:
		_body.add_child(_text("You have no official characters yet. Create one or import your existing offline progress."))
	if Official.characters.size() < SaveSystem.SLOTS:
		_button("Create Official Character", func() -> void: official_new.emit())
		_button("Import Existing Progress", _show_import)
	_button("Refresh Characters", func() -> void:
		if _busy:
			return
		_busy = true
		var result := await Official.refresh_characters()
		_busy = false
		if result.has("error"):
			_status.text = String(result.error)
		else:
			_show_characters())
	_button("Sign Out", func() -> void:
		await Official.logout()
		_show_servers())
	_button("Back to Servers", _show_servers)

func _show_import() -> void:
	_view = "import"
	_clear("Import an Offline Character")
	_body.add_child(_text("Import is a one-time copy for each character. Future offline changes will not replace official progress. Your original local save is kept. Custom-game characters cannot be imported."))
	var found := false
	for slot in SaveSystem.SLOTS:
		var data := SaveSystem.read_legacy_slot(slot)
		if data.is_empty():
			continue
		found = true
		var local_slot := slot
		var hero: Dictionary = data.hero
		_button("Import %s · Level %d %s" % [hero.get("name", "Hero"), int(hero.get("progress", {}).get("level", 1)), hero.get("class", "")], func() -> void:
			_dialog.ask("Import Character", "Copy this offline character into an empty official slot? The original stays on your device.", func() -> void: _import_slot(local_slot), "Import"))
	if not found:
		_body.add_child(_text("No existing offline characters were found on this device."))
	_button("Back to Official Characters", _show_characters)

func _import_slot(slot: int) -> void:
	if _busy:
		return
	var target := -1
	for candidate in SaveSystem.SLOTS:
		if Official.slot_summary(candidate).is_empty():
			target = candidate
			break
	if target < 0:
		_status.text = "All eight official slots are occupied."
		return
	var data := SaveSystem.read_legacy_slot(slot)
	var hero := HeroData.from_dict(data.get("hero", {}))
	if hero == null:
		_status.text = "This local character could not be read."
		return
	_busy = true
	_status.text = "Copying the character to the server…"
	var result := await Official.add_character(hero, target, SaveSystem.legacy_identity(slot, hero))
	_busy = false
	if result.has("error"):
		_status.text = String(result.error)
	else:
		_show_characters()
		_status.text = "This character was already imported. Its official progress was kept." if result.get("already_imported", false) else "Import complete. Your original offline save is still on this device."

func show_error(message: String) -> void:
	_status.text = message

func go_back() -> void:
	if _dialog.visible:
		_dialog.cancel()
	elif _view == "servers":
		selected.emit("back", {})
	else:
		_show_servers()

func _process(delta: float) -> void:
	if _view != "servers":
		return
	_refresh_t += delta
	if _refresh_t >= 20.0:
		_refresh_t = 0.0
		_refresh_directory()
