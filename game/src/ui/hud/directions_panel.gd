class_name DirectionsPanel
extends PanelContainer
## Directions while a route is tracked (Routes): an arrow toward the road ahead, the next instruction, and the
## remaining walking distance to the destination. Hidden when no route is set. Guidance only: it never moves the hero.

var _arrow: Control
var _text: Label
var _dist: Label
var _note: Label

func _init() -> void:
	theme_type_variation = &"GlassPanel"
	custom_minimum_size = Vector2(300, 0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false

func _ready() -> void:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	add_child(h)
	_arrow = Control.new()
	_arrow.custom_minimum_size = Vector2(44, 44)
	_arrow.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	_arrow.draw.connect(_draw_arrow)
	h.add_child(_arrow)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 1)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	_text = UITheme.label("", 24, UITheme.PARCHMENT, UITheme.body_bold())
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(236, 0)
	v.add_child(_text)
	_dist = UITheme.label("", 23, Color(0.62, 0.92, 0.95), UITheme.body_font())
	v.add_child(_dist)
	_note = UITheme.label("", 18, UITheme.TEXT_DIM, UITheme.body_font())
	_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_note.custom_minimum_size = Vector2(236, 0)
	v.add_child(_note)

func _process(_d: float) -> void:
	visible = Routes.active() and Game.in_session
	if not visible:
		return
	_text.text = Routes.instruction
	var d := DataIsland.place(Routes.dest)
	if Routes.plan.get("ok", false):
		_dist.text = "%s to %s" % [RoutePlanner.fmt_m(Routes.remaining_m), d.get("name", "")]
	else:
		_dist.text = "No route to %s" % d.get("name", "")
	_note.text = Routes.note if Routes.note != "" else "M: change or clear the route"
	_arrow.queue_redraw()

## Screen direction from the hero to the guide point (the camera decides which way is "up").
func _screen_dir() -> Vector2:
	var p := Game.player as Node3D
	var cam := get_viewport().get_camera_3d()
	if p == null or cam == null or not Routes.has_guide:
		return Vector2.ZERO
	var a := cam.unproject_position(p.global_position)
	var b := cam.unproject_position(Routes.guide)
	return (b - a).normalized() if a.distance_to(b) > 2.0 else Vector2.ZERO

func _draw_arrow() -> void:
	var c := _arrow.size * 0.5
	_arrow.draw_circle(c, 21.0, Color(0.02, 0.12, 0.15, 0.85))
	_arrow.draw_arc(c, 21.0, 0.0, TAU, 32, Color(0.5, 0.95, 1.0, 0.8), 2.0, true)
	var d := _screen_dir()
	if d == Vector2.ZERO:
		_arrow.draw_circle(c, 6.0, Color(0.5, 0.95, 1.0))
		return
	var tip := c + d * 15.0
	var l := c + d.rotated(2.5) * 11.0
	var r := c + d.rotated(-2.5) * 11.0
	_arrow.draw_colored_polygon(PackedVector2Array([tip, l, c - d * 3.0, r]), Color(0.6, 0.97, 1.0))
