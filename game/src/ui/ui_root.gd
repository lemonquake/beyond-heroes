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
var chat: ChatBox
var touch: TouchControls
var _root: Control

const HOTKEYS := {&"inventory": &"inventory", &"character": &"character", &"skills": &"skills", &"talents": &"talents",
	&"world_map": &"world_map", &"tempos": &"tempos", &"guide": &"guide"}

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
	chat = ChatBox.new()        # under the windows: an open window covers the chat log
	_root.add_child(chat)
	touch = TouchControls.new() # touch play (bh-008); hides itself with keyboard + mouse
	touch.hud = hud
	_root.add_child(touch)
	_add_window(&"inventory", InventoryWindow.new())
	_add_window(&"character", CharacterWindow.new())
	_add_window(&"skills", SkillsWindow.new())
	_add_window(&"talents", TalentsWindow.new())
	_add_window(&"shop", ShopWindow.new())
	_add_window(&"world_map", WorldMapWindow.new())
	_add_window(&"settings", SettingsWindow.new())
	_add_window(&"tempos", TempoWindow.new())
	_add_window(&"tempo_caller", TempoCallerWindow.new())
	_add_window(&"guide", GuideWindow.new())
	_add_window(&"crafting", CraftingWindow.new())
	_add_window(&"hero_roster", HeroRosterWindow.new())
	_add_window(&"mobile_menu", MobileMenuWindow.new())
	_add_window(&"multiplayer", MultiplayerWindow.new())
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
	Events.world_flag_set.connect(_on_flag)

func _add_window(id: StringName, w: UIWindow) -> void:
	windows[id] = w
	w.process_mode = Node.PROCESS_MODE_ALWAYS
	_root.add_child(w)
	w.closed.connect(_update_blocking)
	w.visibility_changed.connect(_update_blocking)

func window(id: StringName) -> UIWindow:
	return windows.get(id)

## A crafting station (bh-007): the forge, an alchemy table or a workbench.
func open_crafting(station: StringName, label := "") -> void:
	var w := window(&"crafting") as CraftingWindow
	if w:
		w.open_station(station, label)

## The hero register board at a camp (bh-007): the heroes present with their level, tier and guild.
func open_roster(camp: StringName) -> void:
	var w := window(&"hero_roster") as HeroRosterWindow
	if w:
		w.open_camp(camp)

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
	return dialogue.visible or pause_menu.visible or confirm.visible or chat.is_open()

func close_all() -> bool:
	var closed_any := false
	if chat.is_open():
		chat.close()
		return true
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

## "Go back" (Escape, the phone's Back button, the on-screen Pause button): closes the topmost thing that is open —
## chat, a question, a conversation, a window — then toggles the pause menu. It never quits the game by itself.
func back() -> void:
	if not Game.in_session or Game.player == null:
		return
	if pause_menu.visible and pause_menu.is_death():
		return
	if confirm.visible:
		confirm.cancel()
	elif not close_all():
		pause_menu.toggle()
	_update_blocking()

func _unhandled_input(e: InputEvent) -> void:
	if not Game.in_session or Game.player == null:
		return
	if e.is_action_pressed(&"pause"):
		back()
		get_viewport().set_input_as_handled()
		return
	# the map pauses the world while it is open, so it must still close on its own key
	if e.is_action_pressed(&"world_map") and window(&"world_map") and window(&"world_map").visible:
		window(&"world_map").close_window()
		get_viewport().set_input_as_handled()
		return
	if get_tree().paused or dialogue.visible:
		return
	if e.is_action_pressed(&"chat") and not confirm.visible:
		chat.open()
		get_viewport().set_input_as_handled()
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

## The new-game guide: Tobren introduces himself, Tempos and the controls (DataGuide). Also replayed from the Field Guide.
func start_intro() -> void:
	close_all()
	dialogue.start_def(DataGuide.intro())

func _on_flag(flag: StringName, _v: Variant) -> void:
	if flag == DataGuide.DONE_FLAG:
		Events.notify.emit("Press %s any time to open the Field Guide." % Settings.binding_text(&"guide"), &"info")

func _on_player_died() -> void:
	close_all()
	pause_menu.show_death()

## A network waypoint with several awakened destinations: one button per shrine (the dais's own destination first).
func choose_waypoint(t: Teleporter, dests: Array) -> void:
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 8)
	for i in range(1, dests.size()):
		var d: Dictionary = dests[i]
		var b := UIWindow.button("Travel to %s" % d.name, func() -> void:
			confirm.cancel()
			t.travel_to(d.map, d.spawn), &"", 420.0)
		list.add_child(b)
	var first: Dictionary = dests[0]
	confirm.ask("Waypoint", "Choose an awakened shrine. You arrive beside its dais.", func() -> void: t.travel_to(first.map, first.spawn),
		"Travel to %s" % first.name, false, list)

## Ask a yes/no question. `on_yes` runs on confirmation.
func ask(title: String, text: String, on_yes: Callable, yes_text := "Confirm", danger := false) -> void:
	confirm.ask(title, text, on_yes, yes_text, danger)

## Fade to black with a caption, run `at_dark` while the screen is black, then fade back (inn rest, doors).
func fade_rest(caption: String, at_dark: Callable, hold := 0.9) -> void:
	var cover := ColorRect.new()
	cover.color = Color(0.01, 0.008, 0.012, 0.0)
	cover.set_anchors_preset(Control.PRESET_FULL_RECT)
	cover.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(cover)
	var l := UITheme.label(caption, 30, UITheme.PARCHMENT, UITheme.title_font())
	l.set_anchors_preset(Control.PRESET_CENTER)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.grow_horizontal = Control.GROW_DIRECTION_BOTH
	l.grow_vertical = Control.GROW_DIRECTION_BOTH
	l.modulate.a = 0.0
	cover.add_child(l)
	var tw := cover.create_tween()
	tw.tween_property(cover, "color:a", 1.0, 0.7)
	tw.parallel().tween_property(l, "modulate:a", 1.0, 0.7)
	tw.tween_callback(at_dark)
	tw.tween_interval(hold)
	tw.tween_property(l, "modulate:a", 0.0, 0.4)
	tw.tween_property(cover, "color:a", 0.0, 0.7)
	tw.tween_callback(cover.queue_free)

## Big centred emblem announcement after joining a guild or a promotion.
func show_tier_award(rank: int, heading: String) -> void:
	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	box.grow_vertical = Control.GROW_DIRECTION_BOTH
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", 6)
	var em := TextureRect.new()
	em.texture = UIArt.tex(DataGuilds.emblem_path(rank))
	em.custom_minimum_size = Vector2(160, 160)
	em.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	em.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	em.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(em)
	var h := UITheme.label(heading, 22, UITheme.PARCHMENT)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(h)
	var t := UITheme.title(DataGuilds.tier_name(rank), 38, DataGuilds.tier(rank).color)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(t)
	var gate := int(DataGuilds.tier(rank).gate)
	if gate >= 0:
		var u := UITheme.label("You may now equip %s items." % BH.rarity_name(gate), 20, BH.rarity_color(gate))
		u.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		box.add_child(u)
	_root.add_child(box)
	box.modulate.a = 0.0
	box.scale = Vector2.ONE * 0.8
	box.pivot_offset = Vector2(160, 140)
	Audio.play_ui(&"level_up")
	var tw := box.create_tween()
	tw.tween_property(box, "modulate:a", 1.0, 0.3)
	tw.parallel().tween_property(box, "scale", Vector2.ONE, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(3.2)
	tw.tween_property(box, "modulate:a", 0.0, 0.6)
	tw.tween_callback(box.queue_free)
