extends Node
## Runs the real boot scene and saves screenshots of every interface for visual review.
##   tools/render.sh --resolution 1920x1080 res://tests/tools/capture_ui.tscn -- --mode=menu --out=<dir>
##   tools/render.sh --resolution 1920x1080 res://tests/tools/capture_ui.tscn -- --mode=game --class=knight --out=<dir>
## mode=menu: main menu, load panel, credits, settings, hero selection (both classes).
## mode=game: HUD (idle, combat, low HP), inventory, character, skills, talents, world map, settings, dialogue, shop,
## pause, dev panel. --tempos=1 adds the chat box, the Tempo window, the Tempo-Caller window and Tempos in the forest. The hero is given levels, gear and statuses first so every panel has real content.

var args := {}
var out := ""
var main: Node

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", "/tmp/ui_shots"))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	if String(args.get("mode", "menu")) == "menu":
		await _menu_flow()
	else:
		await _game_flow()
	print("CAPTURE DONE")
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(name: String, frames := 12) -> void:
	await _wait(frames)
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
	print("SHOT ", name, " ", img.get_size())

func _menu_flow() -> void:
	await _wait(90)
	await _shot("01_main_menu", 30)
	var m: MainMenu = main.menu
	m._show_credits()
	await _shot("02_credits")
	m._credits.visible = false
	m._show_settings()
	await _shot("03_settings_video")
	m._settings._tabs.current_tab = 2
	await _shot("04_settings_controls")
	m._settings.close_window()
	await _wait(10)
	main._show_select()
	await _wait(60)
	await _shot("05_hero_select_knight", 40)
	main.select._select(&"mage")
	await _shot("06_hero_select_mage", 40)

func _game_flow() -> void:
	# wait for the session
	for i in 600:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	var p := Game.player as Player
	var h := Game.hero
	# give the hero something to show
	h.progress.add_xp(XpCurve.total_xp_for_level(9))
	h.inventory.gold = 2480
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	for r in [BH.Rarity.COMMON, BH.Rarity.BASIC, BH.Rarity.ADVANCED, BH.Rarity.LICENSED, BH.Rarity.ELITE, BH.Rarity.MASTER, BH.Rarity.MYTHICAL, BH.Rarity.LEGENDARY, BH.Rarity.AETHER]:
		var b := ItemGenerator.random_base(rng, 9, [], h.cls.id)
		h.inventory.add(ItemGenerator.generate(b, 9, r, rng))
	for bid in [&"guardian_helm", &"sage_hood", &"u_riftblade", &"iron_shard", &"quest_tablet"]:
		var it := DB.make_item(bid, BH.Rarity.MASTER, 9, 7)
		if it:
			if it.base.is_stackable():
				it.count = 23
			h.inventory.add(it)
	for n in h.skill_tree.tree.nodes:
		if h.progress.skill_points > 1:
			h.spend_skill_point(n.id)
	for n in h.talent_tree.tree.nodes:
		if h.progress.talent_points > 2:
			h.spend_talent_point(n.id)
	h.inventory.cells[2].junk = true if h.inventory.cells[2] else false
	await _wait(20)
	await _shot("10_hud_town")
	# statuses and low HP
	p.status.apply(&"burning", 8.0, 0.0, 2.0, Elements.FIRE)
	p.status.apply(&"chilled", 6.0)
	p.status.apply(&"regen", 10.0, 3.0)
	p.hp = p.max_hp() * 0.22
	p.mana = p.max_mana() * 0.1
	p.cooldowns[h.skill_bar[0]] = 3.2
	p.cooldown_total[h.skill_bar[0]] = 6.0
	await _shot("11_hud_low_hp_statuses", 30)
	p.hp = p.max_hp()
	p.mana = p.max_mana()
	p.status.clear()
	var ui: UIRoot = Game.ui_root
	for w in ["inventory", "character", "skills", "talents", "world_map", "settings"]:
		ui.open(StringName(w))
		await _shot("2%d_%s" % [["inventory", "character", "skills", "talents", "world_map", "settings"].find(w), w], 30)
		# hover the first interesting element for a tooltip shot
		if w == "inventory":
			var inv := ui.window(&"inventory") as InventoryWindow
			for c in inv.cells:
				if c.item and c.item.rarity >= BH.Rarity.LEGENDARY:
					TooltipLayer.show_for(c, func() -> Control: return Tips.item(c.item, {"hero": h}))
					break
			await _shot("20b_inventory_tooltip_compare", 20)
			TooltipLayer.hide_for(null)
		if w == "character":
			var cw := ui.window(&"character") as CharacterWindow
			TooltipLayer.show_for(cw._stats_box, func() -> Control: return Tips.stat(&"crit_chance", cw._stats))
			await _shot("21b_character_stat_tooltip", 20)
			TooltipLayer.hide_for(null)
		ui.window(StringName(w)).close_window()
		await _wait(15)
	if args.has("tempos"):
		await _tempo_flow(h, ui)
	# dialogue + shop
	var tovin := NpcDirectory.find(&"tovin")
	if tovin:
		p.global_position = tovin.global_position + tovin.global_transform.basis.z * 2.0
		await _wait(10)
		tovin.interact(p)
		await _shot("30_dialogue", 90)
		ui.dialogue._advance()
		ui.dialogue.session.choose(0)
		await _shot("31_shop", 40)
		ui.window(&"shop").close_window()
		await _wait(10)
	ui.pause_menu.open()
	await _shot("40_pause", 20)
	ui.pause_menu.close()
	if Dev.enabled:
		ui.dev_panel.toggle()
		await _shot("41_dev_panel", 20)
		ui.dev_panel.toggle()
	# combat HUD in a dungeon with a boss
	if args.has("combat"):
		Game.load_map(&"boss_arena", &"arrival")
		await _wait(60)
		var boss := get_tree().get_first_node_in_group(&"boss") as Enemy
		if boss:
			p.global_position = boss.global_position + Vector3(0, 0, 8)
			Events.boss_engaged.emit(boss)
			boss.hp = boss.max_hp() * 0.58
		await _shot("50_boss_hud", 60)

func _tempo_flow(h: HeroData, ui: UIRoot) -> void:
	h.inventory.gold += 5000
	TempoRules.roster(h)
	TempoRules.hire(h, 0)
	TempoRules.hire(h, 1)
	TempoParty.refresh(h)
	await _wait(30)
	ui.chat.open()
	ui.chat.submit("Anyone seen the Tempo-Caller tonight?")
	ui.chat.submit("lemonq")
	ui.chat.submit("azrael")
	ui.chat._line.text = "azrin"
	await _shot("12_chat_open", 20)
	ui.chat.close()
	ui.open(&"tempos")
	await _shot("13_tempo_window", 40)
	ui.window(&"tempos").close_window()
	ui.open(&"tempo_caller")
	await _shot("14_tempo_caller", 40)
	ui.window(&"tempo_caller").close_window()
	Game.load_map(&"ruined_forest", &"start")
	await _wait(120)
	await _shot("15_tempos_forest", 30)
	Game.load_map(&"sanctuary", &"start")
	await _wait(60)
