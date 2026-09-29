extends Node
## Real rendered Tempo layout regression. Does not start a session or write a save.
## godot --path game res://tests/tools/capture_tempo_layout.tscn -- --out=<directory>

var failures: Array[String] = []
var out := "res://../output/tempo-layout"
var win: TempoWindow
var checks := 0

func _ready() -> void:
	_run.call_deferred()

func _frames(count := 12) -> void:
	for i in count:
		await get_tree().process_frame

func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _shot(label: String) -> void:
	await _frames(12)
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		var im := get_viewport().get_texture().get_image()
		im.save_png(out.path_join(label + ".png"))
		print("TEMPO_CAPTURE ", label, " ", im.get_size())
	var vp := get_viewport().get_visible_rect()
	var bounds := win._frame.get_global_rect()
	_check(vp.encloses(bounds), label + ": frame fits viewport " + str(bounds))
	_check(win._frame.size.is_equal_approx(win.window_size), label + ": content cannot expand frame")
	_check(win._tabs.size.y < 80, label + ": companion tabs have bounded height")
	if win._bag.is_visible_in_tree():
		_check(win._bag_scroll.size.x >= win._bag_grid.size.x, label + ": all bag columns are reachable")
	if win._sheet_scroll.is_visible_in_tree():
		_check(win._sheet_scroll.size.x >= win._stats_grid.size.x, label + ": stat values fit their pane")

func _run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			out = arg.substr(6)
	out = ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(out)
	if DB.item_base(&"iron_longsword") == null or DB.trees.is_empty():
		push_error("Tempo capture requires a fully imported, valid game database")
		get_tree().quit(1)
		return
	Game.save_slot = 98
	Game.hero = Game.new_hero(&"knight", "Tempo Layout")
	Game.hero.progress.add_xp(XpCurve.total_xp_for_level(22))
	Game.hero.tempos.append(TempoRules.legend_data(&"kavira"))
	Game.hero.tempos.append(TempoRules.legend_data(&"hollan"))
	Game.hero.tempos[0].uid = 1
	Game.hero.tempos[1].uid = 2
	Game.hero.tempos[0].fallen = true
	var rng := RandomNumberGenerator.new()
	rng.seed = 101
	for i in 35:
		var base := ItemGenerator.random_base(rng, 22, [], &"knight")
		Game.hero.inventory.add(ItemGenerator.generate(base, 22, i % 6, rng))
	get_window().theme = UITheme.theme()
	get_window().content_scale_factor = 1.0
	get_window().content_scale_size = Vector2i(1920, 1080)
	get_window().size = Vector2i(1920, 1080)
	Settings.control_mode = "pc"
	win = TempoWindow.new()
	win.theme = UITheme.theme()
	add_child(win)
	win.open()
	await _shot("1920x1080-fallen")
	win._tabs.current_tab = 1
	await _frames()
	_check(win.current == Game.hero.tempos[1], "selecting second Tempo updates companion")
	await _shot("1920x1080-resting")
	get_window().size = Vector2i(3840, 2160)
	await _shot("3840x2160-resting")
	# Native 1280 logical canvas exercises the responsive breakpoint separately
	# from the game's normal 1920 canvas scaling at 1280 physical resolution.
	get_window().content_scale_size = Vector2i(1280, 720)
	get_window().size = Vector2i(1280, 720)
	Settings.control_mode = "mobile"
	await _shot("1280x720-touch-details")
	_check(win._compact, "narrow/touch layout uses Details and Your bag tabs")
	_check(win._bag_hint.text.begins_with("Double-tap"), "mobile instructions describe touch input")
	win._sheet_scroll.scroll_vertical = 100000
	win._doll_scroll.scroll_vertical = 100000
	await _frames()
	_check(win._sheet_scroll.get_global_rect().intersects(win._about.get_global_rect()), "details can scroll to origin and kills")
	_check(win._doll_scroll.get_global_rect().intersects(win.equip_slots[&"main_weapon"].get_global_rect()), "weapon slots reachable in compact layout")
	await _shot("1280x720-touch-details-bottom")
	win._doll_scroll.scroll_vertical = 0
	win._detail_tabs.current_tab = 1
	await _shot("1280x720-touch-bag")
	_check(win._bag.is_visible_in_tree(), "Your bag tab opens inventory")
	var test_weapon := DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 1, 777)
	Game.hero.inventory.cells[0] = test_weapon
	win.refresh()
	await _frames()
	Input.emulate_mouse_from_touch = true
	var tap := InputEventScreenTouch.new()
	tap.index = 0
	tap.pressed = true
	tap.double_tap = true
	tap.position = win.cells[0].get_global_rect().get_center()
	Input.parse_input_event(tap)
	await _frames()
	tap = InputEventScreenTouch.new()
	tap.index = 0
	tap.pressed = false
	tap.position = win.cells[0].get_global_rect().get_center()
	Input.parse_input_event(tap)
	await _frames()
	_check(win.current.equipment.get_item(&"main_weapon") == test_weapon, "double-tap equips an inventory weapon through actual input")
	win._bag_scroll.scroll_vertical = 100000
	await _frames()
	var last: ItemSlot = win.cells.back()
	_check(win._bag_scroll.get_global_rect().intersects(last.get_global_rect()), "last bag row reachable by scrolling")
	await _shot("1280x720-touch-bag-bottom")
	Settings.control_mode = "pc"
	get_window().content_scale_size = Vector2i(1920, 1080)
	get_window().size = Vector2i(1920, 1080)
	await _shot("1920x1080-after-resize")
	_check(not win._compact and win._sheet_scroll.is_visible_in_tree() and win._bag.is_visible_in_tree(), "returning to desktop restores all panes")
	Settings.control_mode = "mobile"
	get_window().content_scale_size = Vector2i(1280, 720)
	get_window().size = Vector2i(1280, 720)
	Game.hero.tempos.clear()
	win.refresh()
	await _shot("1280x720-empty")
	_check(win._empty.visible and not win._content.visible, "empty state replaces companion panes")
	for i in 3:
		win.close_window()
		await get_tree().create_timer(0.15).timeout
		win.open()
		await get_tree().create_timer(0.2).timeout
	_check(win.is_open(), "repeat close/open retains window")
	var report := {"checks": checks, "failures": failures, "engine": Engine.get_version_info().string}
	FileAccess.open(out.path_join("report.json"), FileAccess.WRITE).store_string(JSON.stringify(report, "  "))
	print("TEMPO_LAYOUT: %d checks, %d failures" % [checks, failures.size()])
	get_tree().quit(0 if failures.is_empty() else 1)
