class_name StatusIcon
extends Control
## A buff/debuff badge: painted border (green-gold buff / barbed red debuff), the status icon, a draining edge for the
## remaining duration, the stack count and a tooltip explaining the effect and time left.

var controller: StatusController
var status_id: StringName

func _init(p_controller: StatusController, p_id: StringName, size_px := 34.0) -> void:
	controller = p_controller
	status_id = p_id
	custom_minimum_size = Vector2(size_px, size_px + 12.0)
	mouse_filter = Control.MOUSE_FILTER_STOP

func _ready() -> void:
	TooltipLayer.attach(self, func() -> Control:
		var inst = controller.statuses.get(status_id)
		return Tips.status(inst) if inst else null)

func _process(_d: float) -> void:
	queue_redraw()

func _draw() -> void:
	var inst = controller.statuses.get(status_id)
	if inst == null:
		return
	var s := size.x
	var r := Rect2(Vector2.ZERO, Vector2(s, s))
	var bad := StatusRules.is_debuff(status_id)
	var ic := UIArt.status_icon(status_id)
	if ic:
		draw_texture_rect(ic, r.grow(-s * 0.1), false)
	# remaining duration: a dark curtain rising from the bottom
	if not inst.infinite and inst.duration > 0.0:
		var frac := clampf(1.0 - inst.remaining / inst.duration, 0.0, 1.0)
		draw_rect(Rect2(Vector2(s * 0.1, s * 0.1), Vector2(s * 0.8, s * 0.8 * frac)), Color(0, 0, 0, 0.55))
	var fr := UIArt.tex("hud/debuff_frame.png" if bad else "hud/buff_frame.png")
	if fr:
		draw_texture_rect(fr, r, false)
	var font := UITheme.number_font()
	if inst.stacks > 1:
		var t := str(inst.stacks)
		draw_string_outline(font, Vector2(s - 11, s - 2), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, 4, Color(0, 0, 0, 0.9))
		draw_string(font, Vector2(s - 11, s - 2), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, UITheme.PARCHMENT)
	if not inst.infinite:
		var tt := "%d" % ceili(inst.remaining) if inst.remaining >= 1.0 else "%.1f" % inst.remaining
		var w := font.get_string_size(tt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		draw_string_outline(font, Vector2((s - w) * 0.5, s + 11), tt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color(0, 0, 0, 0.9))
		draw_string(font, Vector2((s - w) * 0.5, s + 11), tt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, UITheme.TEXT)
