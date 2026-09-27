extends Node
## Boot scene and session flow: Main Menu (live Sanctuary backdrop) -> Hero Selection -> game, or Continue / Load
## Game -> game; Main Menu from the pause menu returns here. The in-game interface (UIRoot) exists only during a session.
## Quick start for testing: --class=knight|mage [--map=<id>] [--spawn=<id>] [--slot=<n>] [--level=<n>] skips the menus.
## A quick-started hero gets the starter Tempo like a new game (--starter=0 to skip); --intro=1 also opens the guide.

var world: Node3D
var ui: UIRoot
var menu: MainMenu
var select: HeroSelect
var menu_layer: CanvasLayer
var args := {}

func _ready() -> void:
	get_tree().root.theme = UITheme.theme()
	for a in OS.get_cmdline_user_args() + OS.get_cmdline_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	world = Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	menu_layer = CanvasLayer.new()
	menu_layer.layer = 10
	add_child(menu_layer)
	Game.session_ended.connect(_on_session_ended)
	_apply_cursor()
	if args.has("class"):
		_quick_start.call_deferred()
	else:
		show_menu()

func _apply_cursor() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var c := UIArt.tex("hud/cursor_default.png")
	if c:
		Input.set_custom_mouse_cursor(c, Input.CURSOR_ARROW, Vector2(4, 4))

# ---- Menus ------------------------------------------------------------------------------------------------------

func show_menu() -> void:
	_clear_menus()
	menu = MainMenu.new()
	menu_layer.add_child(menu)
	menu.build_backdrop(world)
	menu.new_game.connect(_show_select)
	menu.load_slot.connect(_load)

func _show_select() -> void:
	await menu.fade_out()
	menu.dispose_backdrop()
	menu.queue_free()
	menu = null
	select = HeroSelect.new()
	menu_layer.add_child(select)
	select.back.connect(show_menu)
	select.begin.connect(_start_new)

func _clear_menus() -> void:
	if menu and is_instance_valid(menu):
		menu.dispose_backdrop()
		menu.queue_free()
	if select and is_instance_valid(select):
		select.queue_free()
	menu = null
	select = null

# ---- Sessions ----------------------------------------------------------------------------------------------------

func _make_ui() -> void:
	if ui and is_instance_valid(ui):
		ui.queue_free()
	ui = UIRoot.new()
	add_child(ui)

func _start_new(class_id: StringName, hero_name: String, slot: int, difficulty: int) -> void:
	_clear_menus()
	_make_ui()
	await Game.start_new_game(class_id, hero_name, slot, difficulty)

func _load(slot: int) -> void:
	if menu:
		await menu.fade_out()
	_clear_menus()
	_make_ui()
	var ok: bool = await Game.continue_game(slot)
	if not ok:
		ui.queue_free()
		ui = null
		show_menu()

func _on_session_ended() -> void:
	if ui and is_instance_valid(ui):
		ui.queue_free()
	ui = null
	get_tree().paused = false
	show_menu()

func _quick_start() -> void:
	var cls := StringName(args.get("class", "knight"))
	var slot := int(args.get("slot", "2"))
	_make_ui()
	if args.has("load"):
		await Game.continue_game(slot)
		return
	Game.hero = Game.new_hero(cls, String(args.get("name", "Wanderer")))
	var lvl := int(args.get("level", "1"))
	if lvl > 1:
		Game.hero.progress.add_xp(XpCurve.total_xp_for_level(lvl))
	Game.hero.difficulty = int(args.get("difficulty", "1"))
	Game.difficulty = Game.hero.difficulty
	Game.save_slot = slot
	if String(args.get("starter", "1")) != "0":
		TempoRules.grant_starter(Game.hero)
	await Game._begin_session(StringName(args.get("map", "sanctuary")), StringName(args.get("spawn", "start")))
	if String(args.get("intro", "0")) == "1":
		Game.open_intro()
