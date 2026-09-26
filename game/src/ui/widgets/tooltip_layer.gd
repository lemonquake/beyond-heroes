class_name TooltipLayer
extends CanvasLayer
## The one tooltip surface. Controls call TooltipLayer.show_for(anchor, builder) on hover and hide_for(anchor) on exit;
## the builder returns the content Control. The tooltip sits beside the anchor (right, else left, else above) and is
## clamped to the screen. Holding Shift while hovering an item keeps the comparison; content can be rebuilt live.

static var instance: TooltipLayer

var _panel: Control
var _anchor: Control
var _builder: Callable
var _fade: Tween

func _init() -> void:
	layer = 80
	process_mode = Node.PROCESS_MODE_ALWAYS

func _enter_tree() -> void:
	instance = self

func _exit_tree() -> void:
	if instance == self:
		instance = null

static func show_for(anchor: Control, builder: Callable) -> void:
	if instance:
		instance._show(anchor, builder)

static func hide_for(anchor: Control) -> void:
	if instance and (anchor == null or instance._anchor == anchor):
		instance._clear()

static func refresh() -> void:
	if instance and instance._anchor and is_instance_valid(instance._anchor):
		instance._show(instance._anchor, instance._builder)

func _show(anchor: Control, builder: Callable) -> void:
	_clear()
	if anchor == null or not is_instance_valid(anchor) or not anchor.is_visible_in_tree():
		return
	var content: Control = builder.call()
	if content == null:
		return
	_anchor = anchor
	_builder = builder
	_panel = content
	_panel.theme = UITheme.theme()
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for c in _panel.find_children("*", "Control", true, false):
		(c as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_panel)
	_panel.modulate.a = 0.0
	_panel.reset_size()
	_place.call_deferred()

func _place() -> void:
	if _panel == null or not is_instance_valid(_panel) or _anchor == null or not is_instance_valid(_anchor):
		return
	_panel.reset_size()
	var vp := _panel.get_viewport_rect().size
	var a := _anchor.get_global_rect()
	var s := _panel.size
	var p := Vector2(a.end.x + 10.0, a.position.y)
	if p.x + s.x > vp.x - 8.0:
		p.x = a.position.x - s.x - 10.0
	if p.x < 8.0:
		p = Vector2(clampf(a.get_center().x - s.x * 0.5, 8.0, vp.x - s.x - 8.0), a.position.y - s.y - 10.0)
		if p.y < 8.0:
			p.y = a.end.y + 10.0
	p.y = clampf(p.y, 8.0, maxf(8.0, vp.y - s.y - 8.0))
	_panel.position = p.round()
	_fade = _panel.create_tween()
	_fade.tween_property(_panel, "modulate:a", 1.0, 0.08)

func _clear() -> void:
	if _panel and is_instance_valid(_panel):
		_panel.queue_free()
	_panel = null
	_anchor = null

func _process(_d: float) -> void:
	if _anchor != null and (not is_instance_valid(_anchor) or not _anchor.is_visible_in_tree()):
		_clear()

## Attach a hover tooltip to any control.
static func attach(c: Control, builder: Callable) -> void:
	c.mouse_entered.connect(func() -> void: TooltipLayer.show_for(c, builder))
	c.mouse_exited.connect(func() -> void: TooltipLayer.hide_for(c))
