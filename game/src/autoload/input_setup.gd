extends Node
## Registers the input map in code (autoload `InputSetup`) so bindings are data-driven and rebindable.

const BINDINGS := {
	"move_up": [KEY_W], "move_down": [KEY_S], "move_left": [KEY_A], "move_right": [KEY_D],
	"primary": [MOUSE_BUTTON_LEFT], "secondary": [MOUSE_BUTTON_RIGHT],
	"attack_in_place": [KEY_SHIFT],
	"skill_1": [KEY_1], "skill_2": [KEY_2], "skill_3": [KEY_3], "skill_4": [KEY_4], "skill_5": [KEY_5], "skill_6": [KEY_6],
	"dodge": [KEY_SPACE], "guard": [KEY_F],
	"potion_health": [KEY_Q], "potion_mana": [KEY_E],
	"interact": [KEY_R], "ping": [KEY_G], "summon_party": [KEY_P],
	"inventory": [KEY_I, KEY_B], "character": [KEY_C], "skills": [KEY_K], "talents": [KEY_T], "world_map": [KEY_M, KEY_TAB], "tempos": [KEY_O], "guide": [KEY_H], "chat": [KEY_ENTER, KEY_KP_ENTER],
	"pause": [KEY_ESCAPE],
	"zoom_in": [MOUSE_BUTTON_WHEEL_UP], "zoom_out": [MOUSE_BUTTON_WHEEL_DOWN],
	"show_loot": [KEY_ALT],
	"minimap_zoom_in": [KEY_EQUAL, KEY_KP_ADD], "minimap_zoom_out": [KEY_MINUS, KEY_KP_SUBTRACT],
	"dev_panel": [KEY_F1], "dev_fps": [KEY_F3],
}

func _enter_tree() -> void:
	install_defaults()
	Settings._apply_bindings()

## The default bindings (keyboard/mouse + controller). Settings.bindings overrides them per action.
func install_defaults() -> void:
	for action in BINDINGS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.2)
		InputMap.action_erase_events(action)
		for code in BINDINGS[action]:
			var ev: InputEvent
			if action in ["primary", "secondary", "zoom_in", "zoom_out"]:
				var mb := InputEventMouseButton.new()
				mb.button_index = code
				ev = mb
			else:
				var k := InputEventKey.new()
				k.physical_keycode = code
				ev = k
			InputMap.action_add_event(action, ev)
	# Controller support (movement + face buttons) — rumble architecture lives in FX.
	_joy("move_left", JOY_AXIS_LEFT_X, -1.0)
	_joy("move_right", JOY_AXIS_LEFT_X, 1.0)
	_joy("move_up", JOY_AXIS_LEFT_Y, -1.0)
	_joy("move_down", JOY_AXIS_LEFT_Y, 1.0)
	_joyb("primary", JOY_BUTTON_X)
	_joyb("secondary", JOY_BUTTON_Y)
	_joyb("dodge", JOY_BUTTON_B)
	_joyb("guard", JOY_BUTTON_LEFT_SHOULDER)
	_joyb("pause", JOY_BUTTON_START)
	_joyb("skill_1", JOY_BUTTON_A)
	_joyb("skill_2", JOY_BUTTON_RIGHT_SHOULDER)

func _joy(action: String, axis: int, dir: float) -> void:
	var e := InputEventJoypadMotion.new()
	e.axis = axis
	e.axis_value = dir
	InputMap.action_add_event(action, e)

func _joyb(action: String, b: int) -> void:
	var e := InputEventJoypadButton.new()
	e.button_index = b
	InputMap.action_add_event(action, e)

func key_label(action: String) -> String:
	for e in InputMap.action_get_events(action):
		if e is InputEventKey:
			return OS.get_keycode_string(e.physical_keycode)
		if e is InputEventMouseButton:
			return ["", "LMB", "RMB", "MMB"][clampi(e.button_index, 0, 3)]
	return ""
