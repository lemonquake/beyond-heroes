extends Node
## bh-018 evidence in the real game (boot scene, HUD, real camera): the three trade quarters from where a hero walks, the
## Socket Specialists, the socket window, socketed-item and crystal tooltips, the crystal shop, and a dungeon gate.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh018_game.tscn -- --class=knight --slot=97 --out=<dir>
## Optional --only=quarters,sockets,gates

var args := {}
var out := ""
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-018/evidence/shots")))
	only = String(args.get("only", "")).split(",", false)
	DirAccess.make_dir_recursive_absolute(out)
	var main: Node = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	Game.god_mode = true
	if _want("quarters"):
		await _quarters()
	if _want("sockets"):
		await _sockets()
	if _want("gates"):
		await _gates()
	print("BH018 GAME CAPTURE DONE -> ", out)
	get_tree().quit()

func _want(k: String) -> bool:
	return only.is_empty() or only.has(k)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 10) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH018 SHOT ", label)

func _go(map_id: StringName, spawn: StringName = &"start") -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _at(x: float, z: float, face := 180.0) -> void:
	p.teleport_to(Game.current_map.to_global(Vector3(x, 0.3, z)))
	p.rotation.y = deg_to_rad(face)

func _quarters() -> void:
	var views := {
		&"sanctuary": [["entry", 11.0, 12.0], ["square", 15.0, 21.5], ["east", 17.5, 19.0], ["south", 14.5, 27.5]],
		&"olivar": [["entry", -5.0, 15.0], ["square", -5.2, 22.0], ["south", -5.0, 26.0]],
		&"wyman_outpost": [["entry", 3.5, 13.5], ["square", 4.0, 20.0]],
	}
	for m in views:
		await _go(m)
		for v in views[m]:
			_at(float(v[1]), float(v[2]))
			await _wait(45)
			await _shot("quarter_%s_%s" % [m, v[0]], 15)
		# each shopkeeper at their stand, from the customer spot
		for s in DataTownRows.row(m).stands:
			var c := DataTownRows.customer_spot(s)
			_at(c.x, c.z + 0.6)
			await _wait(30)
			await _shot("stand_%s_%s" % [m, s.id], 10)

func _hero_kit() -> void:
	var h := Game.hero
	h.progress.level = 30
	h.set_tier(DataGuilds.MAX_RANK)
	h.inventory.gold = 500000
	var sword := ItemGenerator.generate(DB.item_base(&"sunsteel_blade") if DB.item_base(&"sunsteel_blade") else DB.item_base(&"iron_longsword"), 28, BH.Rarity.MYTHICAL, _rng(7))
	sword.sockets = 4
	sword.gems = ["ember_crystalline", "thundra_shard", "", ""]
	h.inventory.add(sword)
	h.equip_from_inventory(sword, &"main_weapon")
	var helm := ItemGenerator.generate(DB.item_base(&"visored_greathelm"), 26, BH.Rarity.ELITE, _rng(8))
	helm.sockets = 2
	helm.gems = ["aqua_shard", ""]
	h.inventory.add(helm)
	for pair in [[&"vipera_shard", 2], [&"bloodrift_fragment", 1], [&"nova_orbital", 1], [&"aetherift_fragment", 1], [&"essencerift_crystalline", 1], [&"ember_fragment", 3]]:
		var c := DB.make_item(pair[0], BH.Rarity.COMMON, 1, 3)
		c.count = int(pair[1])
		h.inventory.add(c)
	var ring := ItemGenerator.generate(DB.item_base(&"sigil_ring"), 26, BH.Rarity.LEGENDARY, _rng(9))
	h.inventory.add(ring)

func _rng(s: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = s
	return r

func _sockets() -> void:
	_hero_kit()
	await _go(&"sanctuary")
	var st := DataTownRows.stand_of_npc(&"ysolde")
	var c := DataTownRows.customer_spot(st)
	_at(c.x, c.z)
	await _wait(40)
	# talk to Ysolde
	var ysolde: Npc = null
	for n in get_tree().get_nodes_in_group(&"npc"):
		if n is Npc and (n as Npc).def.id == &"ysolde":
			ysolde = n
	if ysolde:
		Events.talk_requested.emit(ysolde)
		await _wait(80)
		await _shot("socket_dialogue", 10)
		# Exercise the real conversation handoff, including its deferred service.
		var dialogue: DialogueBox = Game.ui_root.dialogue
		for i in 10:
			if dialogue.session == null or not dialogue.session.choices.is_empty():
				break
			dialogue._finish_typing()
			dialogue.session.advance()
		dialogue._finish_typing()
		dialogue.session.choose(0)
		await _wait(10)
	else:
		push_error("Socket capture requires Ysolde in the world")
		get_tree().quit(1)
		return
	await _wait(10)
	var w := Game.ui_root.window(&"socketing") as SocketWindow
	for it in Sockets.pieces(Game.hero):
		if it.sockets == 4:
			w._sel = it
	w.refresh()
	await _shot("socket_window_sword", 20)
	# set the Vipera Shard into the sword
	for cr in Sockets.crystals_for(Game.hero, w._sel):
		if cr.base.id == &"vipera_shard":
			w._crystal = cr
	w._do_set()
	await _wait(20)
	await _shot("socket_window_after_set", 10)
	# the sword's tooltip
	TooltipLayer.show_for(w._slot, func() -> Control: return Tips.item(w._sel, {"hero": Game.hero}))
	await _shot("socket_tooltip_sword", 20)
	TooltipLayer.hide_for(null)
	# a crystal's own tooltip
	var orb: ItemInstance = null
	for it in Game.hero.inventory.cells:
		if it != null and it.base.id == &"nova_orbital":
			orb = it
	if orb:
		TooltipLayer.show_for(w._slot, func() -> Control: return Tips.item(orb, {"hero": Game.hero}))
		await _shot("crystal_tooltip_nova_orbital", 20)
		TooltipLayer.hide_for(null)
	# the helm: purge dialog
	for it in Sockets.pieces(Game.hero):
		if it.base.id == &"visored_greathelm":
			w._sel = it
	w.refresh()
	await _shot("socket_window_helm", 15)
	w._do_service(Sockets.PURGE)
	await _shot("socket_purge_confirm", 20)
	Game.ui_root.close_all()
	await _wait(10)
	var shop := Game.ui_root.window(&"shop") as ShopWindow
	w._open_shop()
	await _shot("crystal_shop", 30)
	var slot := shop._stock_grid.get_child(0) as ItemSlot
	shop._on_stock_clicked(slot, MOUSE_BUTTON_LEFT, false, false)
	await _shot("crystal_purchase_confirm", 20)
	Game.ui_root.confirm._confirm()
	await _shot("crystal_purchased", 20)
	Game.ui_root.close_all()

func _gates() -> void:
	for pair in [[&"ruined_forest", &"burrows"], [&"olivar", &"vault"], [&"olivar", &"dunemourn"]]:
		await _go(pair[0], DataDungeons.gate_id(pair[1]))
		await _wait(40)
		await _shot("gate_%s_arrival" % pair[1], 15)
		# walk up onto the dais
		var tp: Teleporter = null
		for t in Game.current_map.teleporters():
			if t.teleporter_id == DataDungeons.gate_id(pair[1]):
				tp = t
		if tp:
			p.teleport_to(tp.global_position + Vector3(0, 0.6, 0))
			await _wait(40)
			await _shot("gate_%s_on_dais" % pair[1], 10)
