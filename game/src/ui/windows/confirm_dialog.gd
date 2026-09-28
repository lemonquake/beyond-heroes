class_name ConfirmDialog
extends Control
## Modal yes/no question (destroy item, expensive purchase, respec, quit). Enter confirms, Escape cancels.

var _panel: PanelContainer
var _title: Label
var _text: Label
var _yes: Button
var _no: Button
var _on_yes: Callable
var _extra: Control

signal cancelled                     # Cancel / Back / Escape (bh-011: a party travel request answers "Stay")

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var c := CenterContainer.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(c)
	_panel = PanelContainer.new()
	_panel.custom_minimum_size = Vector2(620, 0)
	c.add_child(_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	_panel.add_child(v)
	_title = UITheme.title("", 28, UITheme.GOLD)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_title)
	v.add_child(HSeparator.new())
	_text = UITheme.label("", 19, UITheme.TEXT, UITheme.body_font())
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(_text)
	_extra = VBoxContainer.new()
	v.add_child(_extra)
	var h := HBoxContainer.new()
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("separation", 24)
	v.add_child(h)
	_no = UIWindow.button("Cancel", cancel, &"", 190.0)
	h.add_child(_no)
	_yes = UIWindow.button("Confirm", _confirm, &"PrimaryButton", 190.0)
	h.add_child(_yes)

func ask(title: String, text: String, on_yes: Callable, yes_text := "Confirm", danger := false, extra: Control = null, no_text := "Cancel") -> void:
	_title.text = title
	_no.text = no_text
	_text.text = text
	_yes.text = yes_text
	_yes.add_theme_color_override("font_color", Color(1.0, 0.6, 0.5) if danger else Color(1.0, 0.93, 0.78))
	_on_yes = on_yes
	for ch in _extra.get_children():
		ch.queue_free()
	if extra:
		_extra.add_child(extra)
	visible = true
	_panel.modulate.a = 0.0
	create_tween().tween_property(_panel, "modulate:a", 1.0, 0.12)
	_yes.grab_focus.call_deferred()

func _confirm() -> void:
	visible = false
	if _on_yes.is_valid():
		_on_yes.call()

func cancel() -> void:
	var was := visible
	visible = false
	if was:
		cancelled.emit()

func _unhandled_input(e: InputEvent) -> void:
	if not visible:
		return
	if e.is_action_pressed(&"ui_cancel"):
		cancel()
		get_viewport().set_input_as_handled()
