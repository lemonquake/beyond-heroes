extends Node

func _ready() -> void:
	_run.call_deferred()

func _shot(label: String) -> void:
	for frame in 45:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://../output/official-menu-%s.png" % label)
	print("CAPTURE ", label)

func _run() -> void:
	Settings.control_mode = "pc"
	var menu := ServerMenu.new()
	add_child(menu)
	await _shot("servers")
	menu._show_auth()
	await _shot("account")
	menu._show_settings()
	await _shot("settings")
	get_tree().quit()
