class_name HotkeyCapture
extends Control
## bh-030: "press the new key" for one action, from anywhere (the belt's quick slots in the Inventory and on the HUD).
## A modifier held with a key binds the combination (Alt+Q); a modifier released on its own binds the modifier. Escape
## cancels. The binding is saved like a Settings rebind and moves the input off any action that used it.

signal finished(action: StringName, ok: bool)

var action: StringName
var _mod := 0
var _label: Label

static func start(a: StringName, _anchor: Control = null) -> HotkeyCapture:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	var c := HotkeyCapture.new()
	c.action = a
	var host: Node = Game.ui_root if Game.ui_root and is_instance_valid(Game.ui_root) else tree.root
	host.add_child(c)
	return c

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	theme = UITheme.theme()
	var shade := ColorRect.new()
	shade.color = Color(0, 0, 0, 0.55)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	var p := PanelContainer.new()
	p.theme_type_variation = &"TooltipFrame"
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.grow_horizontal = Control.GROW_DIRECTION_BOTH
	p.grow_vertical = Control.GROW_DIRECTION_BOTH
	add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	p.add_child(v)
	v.add_child(UITheme.title("Set a Key", 30, UITheme.GOLD))
	_label = UITheme.label("Press the key or combination (for example Alt+Q) for %s.\nNow: %s   ·   Esc cancels" % [
		SettingsWindow._action_name(action), _now()], 20, UITheme.PARCHMENT, UITheme.body_font())
	v.add_child(_label)
	var b := UIWindow.button("Cancel", func() -> void: _end(false), &"", 160.0)
	v.add_child(b)

func _now() -> String:
	var t := Settings.binding_text(action)
	return t if t != "" else "unbound"

func _input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		get_viewport().set_input_as_handled()
		if e.keycode == KEY_ESCAPE:
			_end(false)
			return
		if e.keycode in [KEY_ALT, KEY_CTRL, KEY_SHIFT, KEY_META]:
			_mod = e.keycode
			_label.text = "Hold it and press a key, or release it to bind it alone."
			return
		_bind(e)
	elif e is InputEventKey and not e.pressed and _mod != 0 and e.keycode == _mod:
		get_viewport().set_input_as_handled()
		var k := InputEventKey.new()
		k.physical_keycode = e.physical_keycode
		_bind(k)
	elif e is InputEventMouseButton and e.pressed:
		get_viewport().set_input_as_handled()

func _bind(e: InputEvent) -> void:
	var stolen := Settings.rebind(action, e)
	Events.notify.emit("%s: %s%s" % [SettingsWindow._action_name(action), Settings.binding_text(action),
		"" if stolen == &"" else " (taken from %s)" % SettingsWindow._action_name(stolen)], &"info")
	Audio.play_ui(&"ui_equip")
	_end(true)

func _end(ok: bool) -> void:
	finished.emit(action, ok)
	queue_free()
