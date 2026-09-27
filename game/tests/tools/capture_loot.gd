extends Node
## bh-006 evidence run (real renderer, the real boot scene with the HUD): ground loot of every rarity sparkling on the
## forest floor, the Town Portal tearing open and fully open, the return portal in Malasugue, the HUD's Auto-Loot
## checkbox + load meter + portal chip, the inventory load bar and a new weapon's tooltip, and new weapons in hand.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_loot.tscn -- --class=knight --map=ruined_forest --out=<dir>

var args := {}
var out := ""
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/loot")))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 900:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	Game.god_mode = true
	await _run()
	print("LOOT CAPTURE DONE -> ", out)
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 6) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	print("LOOT SHOT ", label)

## Frame times over `n` rendered frames (real renderer; vsync / fps cap as configured in the user's settings).
func _perf(label: String, n := 240) -> void:
	var last := Time.get_ticks_usec()
	var times: Array[float] = []
	for i in n:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		times.append((now - last) / 1000.0)
		last = now
	times.sort()
	var avg := 0.0
	for t in times:
		avg += t
	avg /= times.size()
	var line := "PERF %s: frames %d avg %.2f ms  p95 %.2f ms  worst %.2f ms  loot nodes %d  vsync %s  fps_limit %d" % [label, n, avg,
		times[int(n * 0.95)], times[-1], get_tree().get_nodes_in_group(&"loot").size(), str(Settings.vsync), Settings.fps_limit]
	print(line)
	var f := FileAccess.open(out.path_join("perf.txt"), FileAccess.READ_WRITE if FileAccess.file_exists(out.path_join("perf.txt")) else FileAccess.WRITE)
	f.seek_end()
	f.store_line(line)
	f.close()

func _clear_enemies() -> void:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		e.queue_free()
	await _wait(3)

func _run() -> void:
	var h := Game.hero
	h.progress.add_xp(XpCurve.total_xp_for_level(34))
	for a in BH.ATTRIBUTES:
		h.progress.allocated[a] = 40
	h.set_tier(8)
	await _clear_enemies()
	p.input_enabled = false
	await _wait(240)          # let the level-up burst fade
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	# ---- A. on the lit town plaza: drops of every rarity, auto-loot, weapons, inventory ----
	var c := p.global_position
	var ids := [&"militia_shortsword", &"oak_cudgel", &"iron_talons", &"reed_javelin", &"hornbow", &"iron_helm", &"warden_plate",
		&"lumber_greataxe", &"silver_ring", &"worldsplitter"]
	for i in ids.size():
		var it := ItemGenerator.generate(DB.item_base(ids[i]), 30, i, rng)
		var spot := c + Vector3(-4.0 + 2.0 * float(i % 5), 0, -4.5 + 2.2 * float(i / 5))
		Loot.spawn_item(it, spot, 0.0, 0.05)
	var extra := [&"health_potion", &"town_portal", &"firebomb", &"phoenix_feather"]
	for k in extra.size():
		Loot.spawn_item(DB.make_item(extra[k], BH.Rarity.COMMON, 10, 1), c + Vector3(-3.0 + 2.0 * k, 0, 1.6), 0.0, 0.05)
	Loot.spawn_gold(c + Vector3(3.5, 0, 1.6), 240)
	p.global_position = c + Vector3(0, 0, 3.2)
	await _wait(90)
	await _shot("01_drops_all_rarities", 10)
	p.camera._dist_target = 6.5
	p.aim_override = c + Vector3(0, 0, -3.5)
	await _shot("02_drops_closeup", 60)
	p.aim_override = c + Vector3(0, 0, 1.0)
	await _shot("02b_drops_closeup_front", 40)
	await _perf("15 drops + gold on screen (close camera)")
	p.aim_override = Vector3.INF
	p.camera._dist_target = 16.0
	await _wait(30)
	Settings.auto_loot_enabled = true      # in memory only (no settings file write from an evidence run)
	await _shot("03_hud_autoloot_load", 20)
	# one drop flying into the hero mid-pickup
	var magnet_target: Node3D = null
	for d in get_tree().get_nodes_in_group(&"loot"):
		if is_instance_valid(d) and (d as LootDrop).item != null and (d as LootDrop).item.rarity >= BH.Rarity.MYTHICAL:
			magnet_target = d
			break
	if magnet_target:
		Settings.auto_loot_enabled = false
		p.camera._dist_target = 7.0
		p.global_position = magnet_target.global_position + Vector3(1.6, 0, 0.5)
		await _wait(40)
		Settings.auto_loot_enabled = true
		for i in 30:
			await get_tree().process_frame
			if not is_instance_valid(magnet_target) or (magnet_target as LootDrop)._collecting:
				break
		await _wait(5)
		await _shot("04a_autoloot_in_flight", 0)
		p.camera._dist_target = 16.0
	for d in get_tree().get_nodes_in_group(&"loot"):
		if not is_instance_valid(d):
			continue
		p.global_position = (d as Node3D).global_position + Vector3(0.3, 0, 0)
		await _wait(12)
	await _shot("04_after_autoloot", 20)
	Settings.auto_loot_enabled = false
	# new weapons in hand
	for id in [&"executioner_moon", &"tiger_claw", &"thunderhead_javelin", &"morning_star"]:
		var wi := DB.make_item(id, BH.Rarity.ELITE, 30, 3)
		h.inventory.add(wi)
		h.equip_from_inventory(wi, &"main_weapon")
		if id == &"tiger_claw":
			var off := DB.make_item(&"tiger_claw", BH.Rarity.ELITE, 30, 4)
			h.inventory.add(off)
			h.equip_from_inventory(off, &"sub_weapon")
		p.global_position = c
		await _wait(20)
		p.camera._dist_target = 5.5
		p.aim_override = p.global_position + Vector3(4, 0, 1.5)
		p._update_aim()
		p._face_aim_now()
		await _wait(40)
		await _shot("05a_weapon_idle_%s" % id, 0)
		p._start_light()
		await _wait(9 if id != &"thunderhead_javelin" else 14)
		await _shot("05b_weapon_attack_%s" % id, 0)
		p.camera._dist_target = 16.0
		p.aim_override = Vector3.INF
		await _wait(30)
	var ui: UIRoot = Game.ui_root
	for id in [&"superior_health_potion", &"featherweight_draught", &"firebomb"]:
		h.inventory.add(DB.make_item(id, BH.Rarity.COMMON, 30, 1))
	ui.open(&"inventory")
	await _wait(30)
	await _shot("06a_inventory_load_bar", 10)
	var inv := ui.window(&"inventory") as InventoryWindow
	for cell in inv.cells:
		if cell.item and cell.item.base.id == &"executioner_moon":
			TooltipLayer.show_for(cell, func() -> Control: return Tips.item(cell.item, {"hero": h}))
			break
	await _shot("06_inventory_load_tooltip", 30)
	TooltipLayer.hide_for(null)
	ui.window(&"inventory").close_window()
	await _wait(10)
	# character sheet: carried weight, capacity, load next to movement speed
	ui.open(&"character")
	await _wait(30)
	var cw := ui.window(&"character") as CharacterWindow
	TooltipLayer.show_for(cw._stats_box, func() -> Control: return Tips.stat(&"move_speed", cw._stats))
	await _shot("06c_character_load_movespeed", 30)
	TooltipLayer.hide_for(null)
	ui.window(&"character").close_window()
	await _wait(10)
	# ---- B. the forest glade: the Town Portal tears open, then back to town through it ----
	Game.load_map(&"ruined_forest", &"start")
	await _wait(60)
	await _clear_enemies()
	p.rotation.y = PI * 0.5      # face east, across the open glade
	var scroll := DB.make_item(&"town_portal", BH.Rarity.COMMON, 10, 1)
	scroll.count = 3
	h.inventory.add(scroll)
	await _wait(10)
	p.consume_item(scroll)
	await _shot("07_portal_tear", 14)
	await _shot("08_portal_opening", 22)
	await _shot("09_portal_open", 60)
	await _perf("Town Portal open")
	p.camera._dist_target = 8.0
	await _shot("10_portal_closeup", 50)
	p.camera._dist_target = 16.0
	await _wait(10)
	var tp: TownPortal = null
	for n in get_tree().get_nodes_in_group(&"town_portal"):
		tp = n
	if tp:
		p.global_position = tp.global_position + Vector3(-1.2, 0, 0)
		await _wait(10)
		tp.interact(p)
		for i in 600:
			await get_tree().process_frame
			if Game.current_map_id == &"sanctuary" and not Game.travelling:
				break
		await _wait(60)
		await _shot("11_town_return_portal", 20)
