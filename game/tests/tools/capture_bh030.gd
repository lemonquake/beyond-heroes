extends Node
## bh-030 captures: the bottom belt strip and quick keys, the Debug console, first-person view, dynamic Guild Quests,
## profile pictures and the new server menu.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh030.tscn -- --class=knight --slot=97 --phase=belt [--out=<dir>]
## Phases: belt, debug, fps, guild, profile, server (server does not boot a hero).

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-030/evidence")))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "mobile" if args.get("touch", "0") == "1" else "pc"
	if String(args.get("phase", "belt")) == "server":
		_server.call_deferred()
		return
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _run() -> void:
	for i in 900:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(2.0)
	match String(args.get("phase", "belt")):
		"belt": await _belt()
		"debug": await _debug()
		"fps": await _fps()
		"guild": await _guild()
		"profile": await _profile()
	get_tree().quit()

func _belt() -> void:
	var h := Game.hero
	h.progress.add_xp(XpCurve.total_xp_for_level(53))
	for pair in [[&"swiftfoot_tonic", 3], [&"frost_flask", 5], [&"rejuvenation_elixir", 2], [&"antidote", 2], [&"town_portal", 6]]:
		var it := DB.make_item(pair[0], BH.Rarity.COMMON, 1, hash(String(pair[0])))
		it.count = pair[1]
		h.inventory.add(it)
	BeltPicker.bind(h, 2, &"rejuvenation_elixir")
	BeltPicker.bind(h, 3, &"town_portal")
	BeltPicker.bind(h, 4, &"frost_flask")
	var rng := RandomNumberGenerator.new()
	rng.seed = 30
	for b in [&"iron_gauntlet", &"warden_plate", &"visored_greathelm"]:
		h.inventory.add(ItemGenerator.generate(DB.item_base(b), 53, BH.Rarity.ELITE, rng))
	await _wait(0.5)
	await _shot(("touch_" if Settings.touch_mode else "") + "hud_quick_belt")
	Game.ui_root.toggle(&"inventory")
	await _wait(0.8)
	var inv: InventoryWindow = Game.ui_root.window(&"inventory")
	for c in inv.cells:
		if c.item and c.item.base.id == &"iron_gauntlet":
			inv._select(c)
			TooltipLayer.show_for(c, func() -> Control: return Tips.item(c.item, {"hero": h}))
	await _wait(0.6)
	await _shot("inventory_belt_strip")

func _debug() -> void:
	Cheats.apply("azrin azrael", Game.hero, Game.player)
	await _wait(0.6)
	await _shot("debug_button")
	Game.ui_root.open(&"debug")
	await _wait(0.8)
	await _shot("debug_console")
	var w: Variant = Game.ui_root.window(&"debug")
	for page in ["items", "tempos", "hero", "world", "tech"]:
		if w and w.has_method(&"show_page"):
			w.show_page(page)
			await _wait(0.5)
			await _shot("debug_" + page)

func _fps() -> void:
	Game.player.call(&"set_first_person", true)
	await _wait(1.5)
	await _shot("fps_view")
	Game.player.rotation.y += PI * 0.6
	await _wait(1.0)
	await _shot("fps_view_turned")

func _guild() -> void:
	Game.hero.progress.add_xp(XpCurve.total_xp_for_level(53))
	GuildJobs.refresh_board(Game.hero, GuildJobs.CENTRAL)
	Game.ui_root.open_guild_jobs()
	await _wait(0.8)
	await _shot("guild_quests_l53")

func _profile() -> void:
	var img := Image.create(256, 256, false, Image.FORMAT_RGBA8)
	for y in 256:
		for x in 256:
			img.set_pixel(x, y, Color.from_hsv(float(x + y) / 512.0, 0.7, 0.9))
	load("res://src/core/profile_picture.gd").set_picture(Game.hero, img)
	Game.ui_root.open(&"character")
	await _wait(0.8)
	await _shot("profile_character")

func _server() -> void:
	var tag := ""
	if args.get("touch", "0") == "1":
		Settings.control_mode = "mobile"
		tag = "mobile_"
	# never the player's own remembered accounts
	SavedAccounts.path = "user://probe_accounts_bh030.dat"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SavedAccounts.path))
	SavedAccounts.remember(Official.url, "Aljay_Knight", "correct horse battery", true)
	SavedAccounts.remember(Official.url, "lemon_mage", "", false)
	Net.lan_games["192.168.1.40"] = {"name": "Lemon's Friday Raid", "room": "aa11", "players": 5, "max": 12, "bh": Net.PROTOCOL, "t": 1e12}
	Net.lan_games["192.168.1.52"] = {"name": "Zarael Speedrun", "room": "bb22", "players": 12, "max": 12, "bh": Net.PROTOCOL, "t": 1e12}
	Net.lan_games["192.168.1.77"] = {"name": "Old Version Hangout", "room": "cc33", "players": 2, "max": 12, "bh": Net.PROTOCOL - 1, "t": 1e12}
	var sm := ServerMenu.new()
	add_child(sm)
	await _wait(2.5)
	sm._fill_games()
	await _shot(tag + "server_home")
	sm._show_custom()
	await _wait(0.6)
	await _shot(tag + "server_custom")
	sm._show_auth(0)
	await _wait(0.6)
	sm.notify("Account created successfully! Welcome to Beyond Heroes, Aljay_Knight.")
	await _wait(0.4)
	await _shot(tag + "server_login")
	Official.userid = "Aljay_Knight"
	Official.characters = [{"id": "c1", "name": "Wanderer", "level": 53, "class": "knight", "map": "malasugue", "slot": 0},
		{"id": "c2", "name": "Hehe", "level": 31, "class": "mage", "map": "olivar", "slot": 1}]
	sm._show_characters()
	await _wait(0.6)
	await _shot(tag + "server_characters")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SavedAccounts.path))
	get_tree().quit()

func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("SHOT ", name)
