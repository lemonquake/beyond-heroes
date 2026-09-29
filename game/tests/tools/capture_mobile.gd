extends Node
## Touch play review captures (bh-008): boots the real game in touch mode and drives it with simulated screen touches
## (several fingers at once), saving PNGs of each screen. Nothing is written to the player's settings file.
##   godot --path game --resolution 1920x864 res://tests/tools/capture_mobile.tscn -- --class=knight --touch=1 \
##       --map=ruined_forest --out=<dir> [--ui_scale=1.25]
## 1920x864 is a 20:9 phone; with Interface Scale 1.25 the canvas matches a 2400x1080 phone at its default scale.

var out := ""
var main: Node
var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/mobile")))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.tscn").instantiate()
	add_child(main)
	_run.call_deferred()

func _run() -> void:
	await _wait(2.0)
	for i in 200:
		if Game.in_session and Game.player is Player and (Game.player as Player).hero:
			break
		await _wait(0.1)
	await _wait(1.5)
	var w := int(args.get("w", "1920"))
	var h := int(args.get("h", "864"))
	get_window().size = Vector2i(w, h)
	get_tree().root.content_scale_factor = float(args.get("ui_scale", "1.25"))
	await _wait(1.0)
	var ui: UIRoot = Game.ui_root
	var tc: TouchControls = ui.touch
	var p := Game.player as Player
	p.hero.inventory.add(DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 7))
	await _shot("01_hud_idle")
	# left thumb on the stick, right thumb dragging Skill 1 to aim
	var k := _scale()
	var stick_at := Vector2(230, h - 230) * 1.0
	_touch(0, stick_at, true)
	await _frames(2)
	_drag(0, stick_at + Vector2(70, -40))
	var s1 := tc.button(&"skill_1").center() * k
	_touch(1, s1, true)
	await _frames(2)
	_drag(1, s1 + Vector2(-110, -90))
	await _wait(0.6)
	await _shot("02_move_and_aim_skill")
	_touch(1, s1 + Vector2(-110, -90), false)
	await _wait(0.5)
	_touch(0, stick_at + Vector2(70, -40), false)
	# attack held
	var atk := tc.button(&"attack").center() * k
	_touch(2, atk, true)
	await _wait(0.5)
	await _shot("03_attack_held")
	_touch(2, atk, false)
	await _wait(0.6)
	# full health: tapping the HP orb must not waste a draught
	var before := p.hero.inventory.count_of(&"health_potion")
	var hp_btn := tc.button(&"potion_health")
	_touch(3, hp_btn.center() * k, true)
	await _frames(3)
	_touch(3, hp_btn.center() * k, false)
	await _wait(0.4)
	print("POTION_AT_FULL_HP before=%d after=%d" % [before, p.hero.inventory.count_of(&"health_potion")])
	p.hp = p.max_hp() * 0.4
	_touch(3, hp_btn.center() * k, true)
	await _frames(3)
	_touch(3, hp_btn.center() * k, false)
	await _wait(0.4)
	print("POTION_AT_40_HP before=%d after=%d" % [before, p.hero.inventory.count_of(&"health_potion")])
	await _shot("04_after_potion")
	# the Menu hub
	await _tap(tc.button(&"menu").center() * k)
	await _wait(0.5)
	await _shot("05_menu")
	main._on_back()

	await _wait(0.4)
	await _tap(tc.button(&"bag").center() * k)
	await _wait(0.5)
	await _shot("06_inventory")
	main._on_back()
	await _wait(0.8)
	await _tap(tc.button(&"chat").center() * k)
	await _wait(0.4)
	ui.chat.add_line("[Anton] Welcome back, hero.", UITheme.PARCHMENT)
	await _shot("07_chat")
	main._on_back()
	await _wait(0.3)
	main._on_back()              # the phone's Back button: pause
	await _wait(0.5)
	await _shot("08_pause_from_back")
	ui.pause_menu._quit()
	await _wait(0.4)
	await _shot("09_quit_question")
	ui.confirm.cancel()
	main._on_back()              # Back again resumes
	await _wait(0.4)
	print("PAUSED_AFTER_SECOND_BACK=", get_tree().paused)
	ui.open(&"settings")
	await _wait(0.4)
	var sw: SettingsWindow = ui.window(&"settings")
	sw._tabs.current_tab = 2
	await _wait(0.3)
	await _shot("10_settings_controls")
	sw.close_window()
	await _wait(0.3)
	var layer := CanvasLayer.new()
	layer.layer = 100
	add_child(layer)
	var pp := PlatformPrompt.new()
	layer.add_child(pp)
	await _wait(0.8)
	await _shot("11_platform_prompt")
	get_tree().quit()

func _scale() -> float:
	return get_tree().root.get_final_transform().x.x    # canvas units -> window pixels

func _touch(i: int, pos: Vector2, down: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = i
	e.position = pos
	e.pressed = down
	Input.parse_input_event(e)

func _drag(i: int, pos: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = i
	e.position = pos
	Input.parse_input_event(e)

func _tap(pos: Vector2) -> void:
	_touch(7, pos, true)
	await _frames(3)
	_touch(7, pos, false)

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _wait(t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := out.path_join(name + ".png")
	img.save_png(path)
	print("CAPTURED ", path)
