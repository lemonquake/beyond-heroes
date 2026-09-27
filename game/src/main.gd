extends Node
## Boot scene and session flow: Main Menu (live Sanctuary backdrop) -> Hero Selection -> game, or Continue / Load
## Game -> game; Main Menu from the pause menu returns here. The in-game interface (UIRoot) exists only during a session.
## Quick start for testing: --class=knight|mage [--map=<id>] [--spawn=<id>] [--slot=<n>] [--level=<n>] skips the menus.
## A quick-started hero gets the starter Tempo like a new game (--starter=0 to skip); --intro=1 also opens the guide.

var world: Node3D
var ui: UIRoot
var menu: MainMenu
var select: HeroSelect
var prompt: PlatformPrompt
var title_intro: TitleIntro
var menu_layer: CanvasLayer
var args := {}

func _ready() -> void:
	get_tree().root.theme = UITheme.theme()
	get_tree().quit_on_go_back = false      # the phone's Back button goes back through menus; it never quits by itself
	for a in OS.get_cmdline_user_args() + OS.get_cmdline_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	if args.has("touch"):                   # --touch=1 / 0: this run only, not saved (tests, captures)
		Settings.control_mode = "mobile" if String(args.touch) == "1" else "pc"
		Settings.apply()
	if args.has("lite"):                    # --lite=1 / 0: efficiency mode for this run only (perf probes, captures)
		if String(args.lite) == "1":
			Settings._efficiency_preset()
		else:
			Settings._desktop_preset()
		Settings.apply()
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
	elif Settings.control_mode == "":
		_ask_platform()
	else:
		show_menu(_intro_wanted())

## First launch: PC or Mobile? (asked once; Settings > Controls changes it later)
func _ask_platform() -> void:
	prompt = PlatformPrompt.new()
	menu_layer.add_child(prompt)
	prompt.chosen.connect(func(_m: String) -> void:
		prompt = null
		show_menu(_intro_wanted()))

func _notification(what: int) -> void:
	match what:
		NOTIFICATION_WM_GO_BACK_REQUEST:
			_back_pressed()
		NOTIFICATION_APPLICATION_PAUSED:
			# a phone may close a backgrounded game without warning: keep the progress
			if Game.in_session and Game.hero and Game.player and is_instance_valid(Game.player):
				Game.save_now()

## Android reports Back as a window request and/or as a KEY_BACK key press, depending on the device: take either,
## once per press.
var _back_t := 0

func _input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and e.keycode == KEY_BACK:
		_back_pressed()
		get_viewport().set_input_as_handled()

func _back_pressed() -> void:
	var now := Time.get_ticks_msec()
	if now - _back_t < 250:
		return
	_back_t = now
	_on_back()

## The phone's Back button: one step back through whatever is on screen. In a session: close the topmost window,
## else open (or close) the pause menu. Hero selection goes back to the title; the title asks before exiting.
func _on_back() -> void:
	if prompt and is_instance_valid(prompt):
		return
	if title_intro and is_instance_valid(title_intro):
		title_intro.skip()
		return
	if Game.in_session and ui and is_instance_valid(ui):
		ui.back()
	elif select and is_instance_valid(select):
		select.back.emit()
	elif menu and is_instance_valid(menu):
		menu.go_back()

func _apply_cursor() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var c := UIArt.tex("hud/cursor_default.png")
	if c:
		Input.set_custom_mouse_cursor(c, Input.CURSOR_ARROW, Vector2(4, 4))

# ---- Menus ------------------------------------------------------------------------------------------------------

## The title sequence plays once per launch (not when a session returns to the menu); --title_intro=0 skips it
## (captures, probes), and a headless run never shows it.
func _intro_wanted() -> bool:
	return String(args.get("title_intro", "1")) != "0" and DisplayServer.get_name() != "headless"

func show_menu(with_intro := false) -> void:
	_clear_menus()
	var intro: TitleIntro = null
	if with_intro:
		# the black intro frame goes up first, so building the backdrop behind it is never seen
		intro = TitleIntro.new()
		title_intro = intro
		menu_layer.add_child(intro)
		await get_tree().process_frame
		await get_tree().process_frame
	menu = MainMenu.new()
	menu.wait_intro = with_intro
	menu_layer.add_child(menu)
	menu.build_backdrop(world)
	menu.new_game.connect(_show_select)
	menu.load_slot.connect(_load)
	if intro:
		menu_layer.move_child(intro, -1)
		intro.target_logo = menu.logo_rect()
		intro.target_byline = menu.byline_pos()
		intro.byline_scale = menu.byline_font_scale()
		var m := menu
		intro.finished.connect(func() -> void:
			if is_instance_valid(m):
				m.reveal())
		await get_tree().process_frame      # the backdrop's first frame (shader compiles) lands before the clock starts
		intro.start()

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
	var slot := int(args.get("slot", "95"))   # a scratch slot the menus never show: quick starts never clobber a real save
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
