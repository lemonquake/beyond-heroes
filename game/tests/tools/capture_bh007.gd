extends Node
## bh-007 evidence run (real renderer, the real boot scene with HUD, NPCs and windows): Olivar (plaza, arms exchange,
## premium shop before and after a clear), crafting at Pell's alchemy table, Wyman Outpost (bonfire, heroes with level
## and tier plates, the Hero Register, the checkpoint), crafting and salvage at the field forge, a miniboss with its HUD
## bar and the stage tracker in Westreach, a stage clear, the death screen offering the checkpoint, and the island map.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh007.tscn -- --class=knight --slot=96 --map=olivar --level=8 --out=<dir>

var args := {}
var out := ""
var main: Node
var p: Player
var report := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-007/evidence/captures")))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1200:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	# the window size is restored from the player's settings at boot: force the requested one (--win=1280x720)
	if args.has("win"):
		var want := String(args.win)
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(Vector2i(int(want.get_slice("x", 0)), int(want.get_slice("x", 1))))
		await _wait(40)
	report["window"] = [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]
	report["viewport"] = [get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y]
	p = Game.player as Player
	Game.god_mode = true
	await _run()
	var f := FileAccess.open(out.path_join("report.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("BH007 CAPTURE DONE -> ", out)
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 6) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	print("BH007 SHOT ", label)

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
	report["perf_" + label] = {"frames": n, "avg_ms": snappedf(avg, 0.01), "p95_ms": snappedf(times[int(n * 0.95)], 0.01), "worst_ms": snappedf(times[-1], 0.01),
		"vsync": Settings.vsync, "fps_limit": Settings.fps_limit}
	print("BH007 PERF ", label, " ", report["perf_" + label])

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 900:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)
	p = Game.player as Player

func _stand(local: Vector3, yaw_deg := 0.0) -> void:
	var m := Game.current_map
	var g := m.to_global(Vector3(local.x, 0, local.z))
	g.y = m.global_position.y + NpcDirectory.ground_height(m, Vector3(local.x, 0, local.z))
	p.global_position = g + Vector3.UP * 0.05
	p.velocity = Vector3.ZERO
	p.rotation.y = deg_to_rad(yaw_deg)
	TempoParty.regroup(p)
	await _wait(20)

func _close_windows() -> void:
	Game.ui_root.close_all()
	await _wait(10)

func _give(id: StringName, n: int) -> void:
	var it := DB.make_item(id, BH.Rarity.COMMON, 1, 1)
	it.count = n
	Game.hero.inventory.add(it)

func _run() -> void:
	var h := Game.hero
	h.inventory.gold = 12000
	p.input_enabled = false
	await _wait(200)                       # level-up burst fades
	Settings.loot_labels_always = true     # in memory only (no settings file write from an evidence run)
	if args.has("ui_only"):
		# the new windows at the launch resolution (use --resolution 1280x720 for the small-screen check)
		for pair in [[&"steel_ingot", 3], [&"cured_leather", 2], [&"wolf_fang", 3], [&"beast_hide", 3], [&"silverleaf", 6], [&"mirebloom", 4]]:
			_give(pair[0], pair[1])
		await _go(&"wyman_outpost", &"north_road")
		await _stand(Vector3(12.5, 0, 8.0), -60.0)
		Game.ui_root.open_crafting(&"forge", "Field Forge")
		var cwu := Game.ui_root.window(&"crafting") as CraftingWindow
		for i in cwu._recipes.size():
			if cwu._recipes[i].id == &"tempered_weapon":
				cwu._sel = i
		cwu._refresh_list()
		cwu._refresh_detail()
		await _shot("ui_crafting_forge", 20)
		await _close_windows()
		Game.ui_root.open_crafting(&"alchemy", "Camp Kettle")
		await _shot("ui_crafting_kettle", 20)
		await _close_windows()
		(Game.ui_root.window(&"shop") as ShopWindow).open_shop(&"wyman_supplies")
		await _shot("ui_wyman_quartermaster", 20)
		await _close_windows()
		(Game.ui_root.window(&"shop") as ShopWindow).open_shop(&"wyman_outfitter")
		await _shot("ui_wyman_outfitter", 20)
		await _close_windows()
		Game.ui_root.open_roster(&"wyman_outpost")
		await _shot("ui_hero_register", 20)
		await _close_windows()
		return
	if args.has("perf_only"):
		# frame times only: the same standing view on each town, the existing town first
		for m in [[&"sanctuary", &"start", Vector3(0, 0, 12)], [&"olivar", &"west_road", Vector3(0, 0, 12)], [&"wyman_outpost", &"north_road", Vector3(2, 0, 8)]]:
			await _go(m[0], m[1])
			await _stand(m[2], 180.0)
			p.camera._dist_target = 17.0
			await _wait(90)
			await _perf(String(m[0]) + "_standing")
		return
	# ---- Olivar ----
	await _stand(Vector3(0, 0, 12), 180.0)
	p.camera._dist_target = 17.0
	await _shot("01_olivar_plaza", 40)
	await _perf("olivar_plaza")
	await _stand(Vector3(19.5, 0, 3.0), -90.0)
	p.camera._dist_target = 11.0
	await _shot("02_olivar_arms_exchange", 40)
	var shop_w := Game.ui_root.window(&"shop") as ShopWindow
	shop_w.open_shop(&"olivar_arms")
	await _shot("03_olivar_arms_stock", 20)
	var before := (shop_w.shop.stock as Array).map(func(e): return e.item.display_name())
	await _close_windows()
	h.add_clear()                          # as a stage clear or a champion kill does
	shop_w.open_shop(&"olivar_arms")
	await _shot("04_olivar_arms_restocked", 20)
	var after := (shop_w.shop.stock as Array).map(func(e): return e.item.display_name())
	report["olivar_restock"] = {"before": before, "after": after, "changed": before != after}
	await _close_windows()
	shop_w.open_shop(&"olivar_jewels")
	await _shot("05_olivar_jeweller", 20)
	await _close_windows()
	# crafting at Pell's alchemy table
	for pair in [[&"silverleaf", 9], [&"mirebloom", 6], [&"wolf_fang", 5], [&"brightcap", 3], [&"orc_tusk", 2], [&"grave_dust", 4]]:
		_give(pair[0], pair[1])
	await _stand(Vector3(-20.5, 0, -9.0), 200.0)
	p.camera._dist_target = 10.0
	await _shot("06_olivar_alchemy_table", 30)
	Game.ui_root.open_crafting(&"alchemy", "Pell's Alchemy Table")
	await _shot("07_crafting_alchemy", 20)
	var cw := Game.ui_root.window(&"crafting") as CraftingWindow
	cw._qty.value = 2
	cw._craft()
	await _shot("08_crafted_draughts", 10)
	await _close_windows()
	# ---- Wyman Outpost ----
	await _go(&"wyman_outpost", &"north_road")
	await _stand(Vector3(2.0, 0, 8.0), 180.0)
	p.camera._dist_target = 18.0
	await _shot("09_wyman_bonfire", 40)
	await _perf("wyman_bonfire")
	await _stand(Vector3(-9.0, 0, 20.5), 180.0)
	p.camera._dist_target = 12.0
	await _shot("10_wyman_training_yard", 90)
	Game.ui_root.open_roster(&"wyman_outpost")
	await _shot("11_hero_register", 20)
	await _close_windows()
	var fire := get_tree().get_nodes_in_group(&"checkpoint")[0] as CampBonfire
	await _stand(Vector3(-4.0, 0, 2.2), 180.0)
	fire.interact(p)
	await _wait(120)
	await _shot("12_checkpoint_set", 10)
	report["checkpoint"] = h.checkpoint.duplicate()
	for pair in [[&"steel_ingot", 3], [&"cured_leather", 2], [&"wolf_fang", 3], [&"beast_hide", 3]]:
		_give(pair[0], pair[1])
	for i in 3:
		h.inventory.add(ItemGenerator.generate(DB.item_base(&"iron_longsword"), 6, BH.Rarity.ADVANCED + (i % 2), RandomNumberGenerator.new()))
	await _stand(Vector3(12.5, 0, 8.0), -60.0)
	Game.ui_root.open_crafting(&"forge", "Field Forge")
	cw = Game.ui_root.window(&"crafting") as CraftingWindow
	for i in cw._recipes.size():
		if cw._recipes[i].id == &"tempered_weapon":
			cw._sel = i
	cw._refresh_list()
	cw._refresh_detail()
	await _shot("13_crafting_forge_weapon", 20)
	cw._craft()
	await _wait(10)
	# hover the crafted result: show its tooltip
	var made: ItemInstance = null
	for c in h.inventory.cells:
		if c != null and c.crafted:
			made = c
	if made:
		report["crafted_weapon"] = {"name": made.display_name(), "rarity": made.rarity_name(), "quality": made.quality, "base": String(made.base.id)}
	await _shot("14_crafted_weapon", 10)
	cw._tabs.current_tab = 1
	await _shot("15_salvage_tab", 20)
	await _close_windows()
	# ---- Westreach: champions and a stage clear ----
	await _go(&"westreach", &"fen_road")
	var sp := Spawner.current()
	var snag: Enemy = null
	for e in sp.minibosses:
		if e.miniboss.id == &"snagtooth":
			snag = e
	var loot_at := Vector3.ZERO
	if snag:
		# stand south of the champion so the camera frames it in the upper middle of the screen, clear of the HUD
		var sl := Game.current_map.to_local(snag.global_position)
		await _stand(Vector3(sl.x + 0.5, 0, sl.z + 5.0), 180.0)
		p.camera._dist_target = 10.0
		await _wait(30)
		await _shot("16_miniboss_snagtooth", 5)
		snag.alert_to(p.global_position)
		await _wait(25)
		await _shot("16b_miniboss_engaged", 0)
		loot_at = snag.global_position
		snag.die(p)
		await _wait(100)
		p.global_position = loot_at + Vector3(0.5, 0.05, 3.2)
		p.velocity = Vector3.ZERO
		await _wait(40)
		await _shot("17_champion_loot", 5)
		var names := []
		for n in get_tree().get_nodes_in_group(&"loot"):
			if n is LootDrop and n.item != null and (n as Node3D).global_position.distance_to(loot_at) < 7.0:
				names.append("%s [%s]" % [n.item.display_name(), n.item.rarity_name()])
		report["champion_loot"] = names
	# an ordinary enemy kill: dire wolves until one drops a Wolf Fang (a 45% drop)
	var fang := false
	var wolves := 0
	for tries in 10:
		var w := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"dire_wolf"), 3, [], p.global_position + Vector3(4.5, 0, -3.0), sp.difficulty)
		wolves += 1
		await _wait(8)
		var wat := w.global_position
		w.die(p)
		await _wait(60)
		for n in get_tree().get_nodes_in_group(&"loot"):
			if n is LootDrop and n.item != null and n.item.base.id == &"wolf_fang" and (n as Node3D).global_position.distance_to(wat) < 6.0:
				fang = true
		if fang:
			break
	report["wolf_kills_until_fang"] = wolves
	report["wolf_fang_dropped"] = fang
	await _shot("17b_enemy_ingredient_drop", 5)
	for e in sp.minibosses:
		if is_instance_valid(e) and e.alive:
			e.die(p)
			await _wait(20)
	await _shot("17c_champions_defeated", 30)
	for zone in sp.camps:
		for e in sp.camps[zone]:
			if is_instance_valid(e) and e.alive:
				e.die(p)
		await _wait(8)
	await _wait(20)
	await _shot("18_stage_cleared", 10)
	report["clear_count"] = h.clear_count
	report["stages_cleared"] = h.stages_cleared.duplicate()
	await _wait(200)
	await _shot("19_stage_tracker_after", 10)
	# ---- death: the checkpoint offer ----
	Game.god_mode = false
	p.die(null)
	await _wait(200)
	await _shot("20_death_checkpoint_offer", 10)
	Game.ui_root.pause_menu._respawn_checkpoint()
	for i in 900:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == &"wyman_outpost" and p.alive:
			break
	await _wait(80)
	report["woke_at"] = String(Game.current_map_id)
	await _shot("21_woke_at_bonfire", 20)
	# ---- the island map ----
	var map_w: WorldMapWindow = Game.ui_root.window(&"world_map")
	Game.ui_root.open(&"world_map")
	await _wait(20)
	map_w._set_view("island")
	map_w.select("olv_town")
	map_w._directions()
	await _shot("22_map_olivar_route", 20)
	map_w.select("wy_camp")
	map_w._directions()
	await _shot("23_map_wyman", 20)
	await _close_windows()
	# baseline: the same measurement in Malasugue (the existing town)
	await _go(&"sanctuary", &"start")
	p.camera._dist_target = 17.0
	await _wait(60)
	await _perf("malasugue_plaza_baseline")
	await _go(&"olivar", &"west_road")
	await _stand(Vector3(0, 0, 12), 180.0)
	p.camera._dist_target = 17.0
	await _wait(60)
	await _perf("olivar_plaza_second_visit")
	await _shot("24_olivar_plaza_revisit", 5)
