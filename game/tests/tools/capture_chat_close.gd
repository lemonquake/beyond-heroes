extends Node
## Rendered regression: click the X with real GUI input in desktop and touch layouts.

var failures: Array[String] = []

func _ready() -> void:
	_run.call_deferred()

func _frames() -> void:
	for i in 6:
		await get_tree().process_frame

func _check(condition: bool, label: String) -> void:
	print("CHAT_CLOSE ", label, ": ", condition)
	if not condition:
		failures.append(label)

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://../output/chat-close-" + label + ".png")

func _run() -> void:
	get_window().theme = UITheme.theme()
	get_window().content_scale_size = Vector2i(1920, 1080)
	get_window().size = Vector2i(1920, 1080)
	var chat := ChatBox.new()
	add_child(chat)
	Net.mode = Net.Mode.HOST
	for touch in [false, true]:
		Settings.control_mode = "mobile" if touch else "pc"
		chat._apply_mode()
		chat.open()
		chat.add_line("Message history remains available when chat is reopened.")
		await _frames()
		var layout := "touch" if touch else "desktop"
		_check(chat._touch_layout == touch, layout + " control layout applied")
		_check(get_viewport().get_visible_rect().encloses(chat._close_button.get_global_rect()), layout + " X fits viewport")
		await _shot(layout + "-open")
		var click := InputEventMouseButton.new()
		click.position = chat._close_button.get_global_rect().get_center()
		click.global_position = click.position
		click.button_index = MOUSE_BUTTON_LEFT
		click.pressed = true
		Input.parse_input_event(click)
		await _frames()
		click = click.duplicate() as InputEventMouseButton
		click.pressed = false
		Input.parse_input_event(click)
		await _frames()
		_check(not chat.visible and not chat.is_open(), layout + " mouse click closes box")
		_check(not chat._line.has_focus(), layout + " keyboard focus released")
		await _shot(layout + "-closed")
	Net.mode = Net.Mode.OFFLINE
	chat.free()
	print("CHAT_CLOSE failures: ", failures)
	get_tree().quit(0 if failures.is_empty() else 1)
