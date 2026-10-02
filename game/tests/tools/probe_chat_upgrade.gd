extends Node
## Run --role=host / --role=client with --class=knight --slot=98/97 --name=Host/Client.
var role := "host"
var messages: Array = []
var failures: Array = []
var client_ready := false

@rpc("any_peer", "reliable")
func ready_for_chat() -> void:
	client_ready = true

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--role="):
			role = arg.substr(7)
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func check(condition: bool, label: String) -> void:
	print("CHAT_CHECK ", role, " ", label, ": ", condition)
	if not condition:
		failures.append(label)

func wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout

func shot(label: String) -> void:
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://../output/chat-%s-%s.png" % [role, label])

func _run() -> void:
	for i in 300:
		if Game.in_session and not Game.travelling:
			break
		await wait(0.1)
	Game.god_mode = true
	Net.chat_received.connect(func(peer: int, text: String) -> void: messages.append([peer, text]))
	check((Net.host_game(24820) if role == "host" else Net.join_game("127.0.0.1", 24820)) == "", "connection started")
	for i in 200:
		if Net.peers.size() == 2 and not Net.connecting and not Game.travelling:
			break
		await wait(0.1)
	check(Net.peers.size() == 2, "two peers connected")
	if role == "client":
		for i in 150:
			if Net.avatar(1) != null and not Net.following:
				break
			await wait(0.1)
		ready_for_chat.rpc_id(1)
	else:
		for i in 200:
			if client_ready:
				break
			await wait(0.1)
	var chat: ChatBox = Game.ui_root.chat
	var skills := Game.hero.progress.skill_points
	chat.submit("qwe")
	check(Game.hero.progress.skill_points == skills + (30 if role == "host" else 0), "host-only cheat")
	check(Game.player.get_node_or_null("ChatBubble") == null, "cheat has no bubble")
	if role == "host":
		await wait(0.3)
		chat.submit("Hello @everyone 😀")
	else:
		for i in 100:
			if not messages.is_empty():
				break
			await wait(0.05)
		check(chat._ping.visible, "everyone flashes sender message")
		check(Net.avatar(1) != null and Net.avatar(1).get_node_or_null("ChatBubble") != null, "remote hero bubble")
		await shot("everyone")
		chat.open()
		chat._line.text = "Hi @Ho"
		chat._line.caret_column = chat._line.text.length()
		chat._update_completion()
		check(not chat._completion.is_empty(), "roster autocomplete")
		var key := InputEventKey.new()
		key.keycode = KEY_RIGHT
		key.pressed = true
		chat._input(key)
		check(chat._line.text == "Hi @Host ", "Right completes name")
		chat._insert_emoji("👍")
		chat._on_submit(chat._line.text)
	for i in 150:
		if messages.size() >= 2:
			break
		await wait(0.05)
	check(messages.size() == 2, "exactly two visible messages, no cheats")
	check(Game.player.get_node_or_null("ChatBubble") != null, "local speech bubble")
	if role == "host":
		check(chat._ping.visible, "targeted mention flashes sender message")
	await shot("messages")
	await wait(3.2)
	check(Game.player.get_node_or_null("ChatBubble") == null, "local bubble expires at three seconds")
	for actor in Net.avatars():
		check(actor.get_node_or_null("ChatBubble") == null, "remote bubble expires")
	chat._process(20)
	check(not chat.visible and chat.modulate.a == 0.0, "multiplayer log fades when idle")
	if role == "host":
		chat.open()
		chat._line.text = "@Cl"
		chat._line.caret_column = 3
		chat._update_completion()
		await shot("completion")
		chat._suggestions.hide()
		chat._emoji_grid.show()
		await shot("emoji")
		chat.close()
		Game.ui_root.open(&"character")
		Game.hero.progress.free_points += 30
		var win: CharacterWindow = Game.ui_root.windows[&"character"]
		win.refresh()
		await wait(0.3)
		var plus: Button = win._attr_rows[&"str"].plus
		# Feed actual GUI mouse events so press, repeat and release use the same path as play.
		var pos := plus.get_global_rect().get_center()
		var down := InputEventMouseButton.new()
		down.position = pos
		down.button_index = MOUSE_BUTTON_LEFT
		down.pressed = true
		Input.parse_input_event(down)
		await wait(0.75)
		var up := down.duplicate() as InputEventMouseButton
		up.pressed = false
		Input.parse_input_event(up)
		var spent := int(win._pending.get(&"str", 0))
		check(spent >= 3, "hold plus repeats")
		await wait(0.3)
		check(int(win._pending.get(&"str", 0)) == spent, "release stops repeat")
		win._allocate_all(&"dex")
		await shot("stats")
		win.close_window()
		await wait(0.2)
		Settings.control_mode = "mobile"
		Settings.changed.emit()
		chat.open()
		chat._emoji_grid.show()
		await wait(0.2)
		await shot("touch")
	print("CHAT_PROBE_DONE ", role, " failures=", failures)
	# Keep the client present while the host finishes its UI checks.
	if role == "client":
		await wait(5.0)
	Net.leave(false)
	get_tree().quit(0 if failures.is_empty() else 1)
