class_name ChatBubble
extends CanvasLayer
## A screen-sized speech panel following a hero. Owned by the actor so map changes clean it up.

const LIFETIME := 3.0
var actor: Node3D
var remaining := LIFETIME
var panel: PanelContainer

static func say(target: Node3D, text: String) -> void:
	if not is_instance_valid(target) or not target.is_inside_tree():
		return
	var old := target.get_node_or_null("ChatBubble")
	if old:
		target.remove_child(old)
		old.queue_free()
	var bubble := ChatBubble.new()
	bubble.name = "ChatBubble"
	bubble.actor = target
	target.add_child(bubble)
	var label := UITheme.label(text, 22, UITheme.TEXT)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size.x = 320
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_override("font", ChatBox.chat_font())
	bubble.panel.add_child(label)

func _ready() -> void:
	layer = 6
	add_to_group(&"chat_bubbles")
	process_mode = Node.PROCESS_MODE_ALWAYS
	panel = PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel", UITheme.panel_style(UITheme.BG_INSET, UITheme.BRONZE, 8, 2, 10))
	add_child(panel)
	panel.hide()

func _process(delta: float) -> void:
	remaining -= delta
	if remaining <= 0.0 or not is_instance_valid(actor):
		queue_free()
		return
	var camera := get_viewport().get_camera_3d()
	if camera == null:
		return
	var point := actor.global_position + Vector3(0, 3.2, 0)
	panel.visible = not camera.is_position_behind(point)
	if panel.visible:
		var screen := camera.unproject_position(point)
		panel.position = screen - Vector2(panel.size.x * 0.5, panel.size.y + 14)
		panel.position = panel.position.clamp(Vector2.ZERO, (get_viewport().get_visible_rect().size - panel.size).max(Vector2.ZERO))
		# Nearby party members often stand together. Stack newer bubbles above earlier ones.
		for other in get_tree().get_nodes_in_group(&"chat_bubbles"):
			if other != self and other.get_instance_id() < get_instance_id() and other.panel.visible:
				if Rect2(panel.position, panel.size).intersects(Rect2(other.panel.position, other.panel.size)):
					panel.position.y = maxf(0.0, other.panel.position.y - panel.size.y - 8)
