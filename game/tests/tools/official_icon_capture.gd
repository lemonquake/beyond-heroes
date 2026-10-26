extends Node
## Render a real 1080p/4K viewport regardless of the host monitor's window-size limit.

func _ready() -> void:
	var target := Vector2i(1920, 1080)
	for arg in OS.get_cmdline_user_args():
		if arg == "--4k":
			target = Vector2i(3840, 2160)
	var viewport := SubViewport.new()
	viewport.size = target
	viewport.size_2d_override = Vector2i(1920, 1080)
	viewport.size_2d_override_stretch = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	viewport.add_child(load("res://tests/tools/official_icon_gallery.tscn").instantiate())
