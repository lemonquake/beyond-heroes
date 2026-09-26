class_name UIRoot
extends CanvasLayer
## Owns every in-game interface: HUD, windows (inventory, character, skills, talents, shop, dialogue, settings, world
## map), the pause menu, dialogs, the dev panel and the tooltip layer. Routes the UI hotkeys and blocks gameplay input
## while a window that needs the mouse is open.

var hud: Hud
var windows := {}                    # id -> UIWindow
var dialogue: DialogueBox
var pause_menu: PauseMenu
var dev_panel: DevPanel
var confirm: ConfirmDialog
var tooltips: TooltipLayer
var _root: Control

const HOTKEYS := {&"inventory": &"inventory", &"character": &"character", &"skills": &"skills", &"talents": &"talents",
	&"world_map": &"world_map"}

func _init() -> void:
	layer = 20
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	Game.ui_root = self
	get_tree().root.theme = UITheme.theme()   # also themes the tooltip layer and drag previews
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = UITheme.theme()
	add_child(_root)
	hud = Hud.new()
	hud.process_mode = Node.PROCESS_MODE_PAUSABLE
	_root.add_child(hud)
	_add_window(&"inventory", InventoryWindow.new())
	_add_window(&"character", CharacterWindow.new())
	_add_window(&"skills", SkillsWindow.new())
	_add_window(&"talents", TalentsWindow.new())
	_add_window(&"shop", ShopWindow.new())
	_add_window(&"world_map", WorldMapWindow.new())
	_add_window(&"settings", SettingsWindow.new())
	dialogue = DialogueBox.new()
	_root.add_child(dialogue)
	pause_menu = PauseMenu.new()
	_root.add_child(pause_menu)
	confirm = ConfirmDialog.new()
	_root.add_child(confirm)
	dev_panel = DevPanel.new()
	_root.add_child(dev_panel)
	tooltips = TooltipLayer.new()
	add_child(tooltips)
	(tooltips as CanvasLayer).layer = layer + 5
	Events.talk_requested.connect(_on_talk)
	Events.player_died.connect(_on_player_died)

func _add_window(id: StringName, w: UIWindow) -> void:
	windows[id] = w
	w.process_mode = Node.PROCESS_MODE_ALWAYS
	_root.add_child(w)
	w.closed.connect(_update_blocking)
	w.visibility_changed.connect(_update_blocking)

func window(id: StringName) -> UIWindow:
	return windows.get(id)

func open(id: StringName) -> void:
	var w := window(id)
	if w == null:
		return
	# only one large window at a time, except inventory + shop / character side by side handled by the shop itself
	for k in windows:
		if k != id and windows[k].visible and not (id == &"shop" and k == &"inventory"):
			windows[k].close_window()
	w.open()
	_update_blocking()

func toggle(id: StringName) -> void:
	var w := window(id)
	if w and w.visible:
		w.close_window()
	else:
		open(id)

func any_window_open() -> bool:
	for w in windows.values():
		if w.visible:
			return true
	return dialogue.visible or pause_menu.visible or confirm.visible

func close_all() -> bool:
	var closed_any := false
	if confirm.visible:
		confirm.cancel()
		return true
	if dialogue.visible:
		dialogue.close()
		return true
	for w in windows.values():
		if w.visible:
			w.close_window()
			closed_any = true
	return closed_any

func _update_blocking() -> void:
	Game.ui_blocking = any_window_open()

func _unhandled_input(e: InputEvent) -> void:
	if not Game.in_session or Game.player == null:
		return
	if e.is_action_pressed(&"pause"):
		if not close_all():
			pause_menu.toggle()
		_update_blocking()
		get_viewport().set_input_as_handled()
		return
	if get_tree().paused or dialogue.visible:
		return
	for action in HOTKEYS:
		if e.is_action_pressed(action):
			toggle(HOTKEYS[action])
			get_viewport().set_input_as_handled()
			return
	if e.is_action_pressed(&"dev_panel") and Dev.enabled:
		dev_panel.toggle()
		get_viewport().set_input_as_handled()

func _process(_d: float) -> void:
	_update_blocking()

func _on_talk(npc: Node) -> void:
	var n := npc as Npc
	if n == null:
		return
	close_all()
	dialogue.start(n)

func _on_player_died() -> void:
	close_all()
	pause_menu.show_death()

## Ask a yes/no question. `on_yes` runs on confirmation.
func ask(title: String, text: String, on_yes: Callable, yes_text := "Confirm", danger := false) -> void:
	confirm.ask(title, text, on_yes, yes_text, danger)
