extends Node
## Beta readiness review captures of the menus a player meets before the game starts (bh-032): the main menu, the realm
## choice, sign-in and server settings, at a given window size and control mode. Reads (never writes) the player's settings
## and talks only to the configured official server's public /health endpoint.
##   godot --path game res://tests/tools/capture_beta_menus.tscn -- --w=1280 --h=720 --touch=0 --out=<dir> [--ui_override=1.0]

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/beta_menus")))
	DirAccess.make_dir_recursive_absolute(out)
	Game.save_slot = 95
	Settings.resolution = 0
	Settings.window_mode = 0
	Settings.control_mode = "mobile" if String(args.get("touch", "0")) == "1" else "pc"
	if args.has("ui_override"):
		Settings.ui_auto = false
		Settings.ui_scale = float(args.ui_override)
	elif args.has("ui_scale"):
		Settings.ui_scale = float(args.ui_scale)
	_run.call_deferred()

func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds, true).timeout

func _shot(label: String) -> void:
	await _wait(0.8)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("SHOT ", label, " window ", get_window().size, " ui_scale ", get_viewport().content_scale_factor)

func _title() -> void:
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	await _wait(6.0)
	await _shot("00_realm_choice")
	var m: MainMenu = main.menu
	if m._server_menu:
		m._server_menu.selected.emit("offline", {})
	await _wait(3.0)
	await _shot("00b_title_menu")
	m._show_settings()
	await _shot("01_settings_video")
	m._settings.close_window()
	await _wait(0.5)
	main._show_select()
	await _wait(2.5)
	await _shot("02_hero_select_knight")
	main.select._select(&"mage")
	await _shot("03_hero_select_mage")
	main.select._name.text = "Seraphine"
	main.select._open_creator()
	await _wait(3.0)
	await _shot("04_hero_creator")
	print("CAPTURE DONE")
	get_tree().quit()

func _run() -> void:
	get_window().size = Vector2i(int(args.get("w", "1280")), int(args.get("h", "720")))
	Settings.apply()
	await _wait(1.0)
	if String(args.get("mode", "")) == "title":
		await _title()
		return
	var menu := ServerMenu.new()
	add_child(menu)
	await _wait(1.5)
	await _shot("10_realm_choice")
	# the remaining pages print the server address: show a placeholder instead of the player's own endpoint (run-only, not saved)
	Official.url = "https://game.example.com"
	Official.certificate_path = ""
	menu._show_auth()
	await _shot("11_sign_in")
	menu._show_settings()
	await _shot("12_server_settings")
	menu.find_children("*", "Button", true, false).filter(func(b): return (b as Button).text.begins_with("Advanced")).map(func(b): (b as Button).pressed.emit())
	await _shot("13_server_settings_advanced")
	menu._show_custom()
	await _shot("14_custom_games")
	print("CAPTURE DONE")
	get_tree().quit()
