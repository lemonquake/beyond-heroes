class_name MultiplayerWindow
extends UIWindow
## Multiplayer (bh-008): open your running world to others (Host), join someone on the same network from the list or
## by room code or address (Join), see who is in the party (with each player's ping), and leave. PC and phones play
## together. Hosting shows a big room code ("K7QM-2XF") that the others type to join (bh-010).
## bh-011: Rejoin the last room with one press, Regroup (clients: back to the host's side), Send Home (host: remove a
## player), and a short "playing together" guide (travel requests, revive, ping).

var _status: Label
var _host_btn: Button
var _leave_btn: Button
var _addr_info: Label
var _lan_list: VBoxContainer
var _address: LineEdit
var _party: VBoxContainer
var _join_box: Control
var _code: Label
var _rejoin: Button
var _regroup: Button
var _tips: Label

func _init() -> void:
	super._init("Multiplayer", Vector2(1180, 820))
	modal = true

func _build() -> void:
	var touch := Settings.touch_mode
	_status = UITheme.label("", 24 if touch else 20, UITheme.PARCHMENT, UITheme.body_bold())
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(_status)
	var cols := hbox(28)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	# left: host + party
	var left := vbox(12)
	left.custom_minimum_size = Vector2(520, 0)
	cols.add_child(left)
	left.add_child(section("Host"))
	var hdesc := _text("Open this world: friends join your game, fight your monsters and follow you from map to map. Each hero keeps their own gear and loot.")
	left.add_child(hdesc)
	_host_btn = button("Host Game", _on_host, &"PrimaryButton", 300.0)
	_host_btn.custom_minimum_size.y = 64 if touch else 52
	_host_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	left.add_child(_host_btn)
	_code = UITheme.title("", 44 if touch else 38, UITheme.GOLD)
	_code.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	left.add_child(_code)
	_addr_info = _text("")
	left.add_child(_addr_info)
	left.add_child(section("Party"))
	_party = vbox(6)
	left.add_child(_party)
	var lrow := hbox(12)
	lrow.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(lrow)
	_regroup = button("Regroup", func() -> void:
		Net.regroup()
		close_window(), &"", 220.0)
	_regroup.custom_minimum_size.y = 60 if touch else 48
	TooltipLayer.attach(_regroup, func() -> Control: return Tips.text("Jump back to the host's side (after respawning at the entrance, or when you wandered off)."))
	lrow.add_child(_regroup)
	_leave_btn = button("Leave", _on_leave, &"", 220.0)
	_leave_btn.custom_minimum_size.y = 60 if touch else 48
	lrow.add_child(_leave_btn)
	_tips = _text("")
	left.add_child(_tips)
	# right: join
	var right := vbox(12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	_join_box = right
	right.add_child(section("Join"))
	right.add_child(_text("Games on your network appear here. PC and phone players can join each other."))
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 250)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(scroll)
	_lan_list = vbox(8)
	_lan_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_lan_list)
	right.add_child(section("Join with a Room Code"))
	right.add_child(_text("Type the room code the host sees on their screen (an address like 192.168.1.20 works too). Over the internet, both of you join the same LAN VPN first, or the host forwards port %d (UDP)." % Net.PORT))
	var row := hbox(10)
	right.add_child(row)
	_address = LineEdit.new()
	_address.placeholder_text = "Room code, like K7QM-2XF"
	_address.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_address.custom_minimum_size.y = 60 if touch else 46
	_address.add_theme_font_size_override("font_size", 24 if touch else 19)
	_address.text_submitted.connect(func(_t: String) -> void: _on_join(_address.text))
	row.add_child(_address)
	var jb := button("Join", func() -> void: _on_join(_address.text), &"PrimaryButton", 160.0)
	jb.custom_minimum_size.y = _address.custom_minimum_size.y
	row.add_child(jb)
	_rejoin = button("", func() -> void: _on_join(Net.last_room), &"", 360.0)
	_rejoin.custom_minimum_size.y = 58 if touch else 44
	_rejoin.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	right.add_child(_rejoin)
	Net.state_changed.connect(refresh)
	Net.peers_changed.connect(refresh)
	Net.lan_games_changed.connect(_fill_lan)

func _text(t: String) -> Label:
	var l := UITheme.label(t, 20 if Settings.touch_mode else 17, UITheme.TEXT_DIM, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l

func open() -> void:
	super.open()
	Net.start_discovery()
	if _address and _address.text == "" and Net.last_room != "":
		_address.text = Net.last_room

func close_window() -> void:
	if not Net.is_active() or Net.is_host():
		Net.stop_discovery()
	super.close_window()

func refresh() -> void:
	if _status == null:
		return
	match Net.mode:
		Net.Mode.OFFLINE:
			_status.text = "Playing alone."
		Net.Mode.HOST:
			_status.text = "Hosting · %d / %d heroes" % [Net.player_count(), Net.MAX_CLIENTS + 1]
		Net.Mode.CLIENT:
			_status.text = "Connecting..." if Net.connecting else "In %s's world · %d heroes" % [Net.peers.get(1, {}).get("name", "the host"), Net.player_count()]
	if Net.last_error != "" and not Net.is_active():
		_status.text += "  " + Net.last_error
	_host_btn.disabled = Net.is_active()
	_leave_btn.visible = Net.is_active()
	_leave_btn.text = "Close World" if Net.is_host() else "Leave"
	_regroup.visible = Net.is_client() and not Net.connecting
	_rejoin.visible = Net.last_room != "" and not Net.is_active()
	_rejoin.text = "Rejoin %s" % Net.last_room
	_tips.visible = Net.is_active()
	var lead := "You lead: everyone follows you through waypoints and doors. When a friend takes one, you are asked Go / Stay." \
		if Net.is_host() else "The host leads. Take a waypoint or door to ask them to go there. Regroup jumps back to their side."
	var interact := "Interact" if Settings.touch_mode else Settings.binding_text(&"interact")
	var ping := "The Ping button" if Settings.touch_mode else Settings.binding_text(&"ping")
	_tips.text = "Playing together:\n• %s\n• A fallen friend: stand beside them and press %s to revive them.\n• %s marks a spot for everyone. Each hero keeps their own loot and gets the experience." % [lead, interact, ping]
	_join_box.modulate.a = 0.45 if Net.is_active() else 1.0
	var codes := Net.room_codes()
	if codes.is_empty():
		_code.text = ""
		_addr_info.text = "No network connection found."
	else:
		_code.text = ("Room code: %s" % codes[0][1]) if Net.is_host() else ""
		var lines := []
		for c in codes:
			lines.append("%s: code %s (address %s)" % [c[0], c[1], c[2]])
		_addr_info.text = ("Tell your friends the room code. " if Net.is_host() else "When you host, friends join with your room code.
") + "
".join(lines)
	_fill_party()
	_fill_lan()

func _fill_party() -> void:
	for c in _party.get_children():
		c.queue_free()
	if not Net.is_active():
		_party.add_child(_text("Nobody else yet."))
		return
	var ids := Net.peers.keys()
	ids.sort()
	for id in ids:
		var p: Dictionary = Net.peers[id]
		var cls := DB.class_def(StringName(p.get("cls", "knight")))
		var map := DB.map_def(StringName(p.get("map", "")))
		var h := hbox(10)
		var por := TextureRect.new()
		por.texture = UIArt.portrait(String(p.get("cls", "knight")))
		por.custom_minimum_size = Vector2(44, 44)
		por.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		h.add_child(por)
		var you := " (you)" if id == Net.my_id() else ""
		var host := " · Host" if id == 1 else ""
		h.add_child(UITheme.label("◆ %s%s — Level %d %s%s" % [p.get("name", "Hero"), you, int(p.get("level", 1)), cls.display_name if cls else "", host],
			20 if Settings.touch_mode else 17, Net.player_color(id).lightened(0.2), UITheme.body_bold()))
		var ping := Net.ping_ms(id) if id != Net.my_id() else -1
		var ping_txt := (" · %d ms" % ping) if ping >= 0 else ""
		var sub := UITheme.label("%s · %s%s" % [p.get("device", "PC"), map.display_name if map else "travelling", ping_txt], 16,
			(UITheme.BAD if ping > 250 else UITheme.TEXT_DIM), UITheme.body_font())
		sub.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(sub)
		if Net.is_host() and id != 1:
			var pid: int = id
			var kb := button("Send Home", func() -> void:
				Game.ui_root.ask("Send Home", "Send %s back to their own world?" % p.get("name", "this hero"), func() -> void: Net.kick(pid), "Send Home", true), &"", 150.0)
			kb.custom_minimum_size.y = 52 if Settings.touch_mode else 38
			h.add_child(kb)
		_party.add_child(h)

func _fill_lan() -> void:
	if _lan_list == null:
		return
	for c in _lan_list.get_children():
		c.queue_free()
	if Net.lan_games.is_empty():
		var l := _text("Looking for games on this network..." if not Net.is_active() else "")
		_lan_list.add_child(l)
		return
	for ip in Net.lan_games:
		var g: Dictionary = Net.lan_games[ip]
		var card := PanelContainer.new()
		card.theme_type_variation = &"InsetPanel"
		var h := hbox(14)
		card.add_child(h)
		var v := vbox(2)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(v)
		v.add_child(UITheme.label("%s's world — Level %d" % [g.get("host", "Host"), int(g.get("level", 1))], 21 if Settings.touch_mode else 18, UITheme.PARCHMENT, UITheme.title_font()))
		v.add_child(UITheme.label("%s · %d / %d heroes · %s" % [g.get("map", ""), int(g.get("players", 1)), int(g.get("max", 4)), ip], 16, UITheme.TEXT_DIM, UITheme.body_font()))
		var full := int(g.get("players", 1)) >= int(g.get("max", 4))
		var jb := button("Full" if full else "Join", func() -> void: _on_join(ip), &"PrimaryButton", 140.0)
		jb.disabled = full or Net.is_active() or int(g.get("bh", 0)) != Net.PROTOCOL
		jb.custom_minimum_size.y = 58 if Settings.touch_mode else 44
		h.add_child(jb)
		_lan_list.add_child(card)

func _on_host() -> void:
	var err := Net.host_game()
	if err != "":
		Events.notify.emit(err, &"error")
	refresh()

func _on_join(address: String) -> void:
	var err := Net.join_game(address)
	if err != "":
		Events.notify.emit(err, &"error")
	refresh()

func _on_leave() -> void:
	Game.ui_root.ask("Close World" if Net.is_host() else "Leave", "Close your world? The others go back to their own games." if Net.is_host()
		else "Leave the party and go back to your own world?", func() -> void:
			Net.leave()
			refresh(), "Close World" if Net.is_host() else "Leave")

var _ping_t := 0.0

func _process(delta: float) -> void:
	if not visible or not Net.is_active():
		return
	_ping_t -= delta
	if _ping_t <= 0.0:
		_ping_t = 2.0                          # pings change slowly: redraw the party list every 2 s
		_fill_party()
