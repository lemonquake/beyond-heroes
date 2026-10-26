class_name FramedIcon
extends Control
## Non-interactive icon presentation for detail panes and upgrade choices.

var texture: Texture2D:
	set(value):
		texture = value
		queue_redraw()

func _init(icon: Texture2D = null, side := 48.0) -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	texture = icon
	custom_minimum_size = Vector2.ONE * side
	size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	Settings.changed.connect(queue_redraw)

func _draw() -> void:
	var bounds := Rect2(Vector2.ZERO, size)
	if texture:
		draw_texture_rect(texture, IconBorders.content_rect(bounds), false)
	IconBorders.draw_frame(self, bounds)
