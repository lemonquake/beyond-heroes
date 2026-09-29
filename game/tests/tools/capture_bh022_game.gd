extends Node
## bh-022 evidence in the real game (boot scene, HUD, real camera): socketed gear in the equipment and bag, the
## infused tooltip name, the glowing held weapon, the two new waypoints and their minimap marks, the waypoint list,
## and the Shrine of the Fallen at level 25 (Mythic) and 45 (Eternal), and the rebuilt boss collection worn in town.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh022_game.tscn -- --class=knight --slot=96 --out=<dir>
## Optional --only=sockets,waypoints,tempos,boss

var args := {}
var out := ""
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-022/evidence/shots")))
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
	if _want("sockets"):
		await _sockets()
	if _want("waypoints"):
		await _waypoints()
	if _want("tempos"):
		await _tempos()
	if _want("boss"):
		await _boss()
	print("BH022 GAME CAPTURE DONE -> ", out)
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
	print("BH022 SHOT ", label)

func _go(map_id: StringName, spawn: StringName = &"start") -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1500:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _rng(s: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = s
	return r

func _sockets() -> void:
	var h := Game.hero
	h.progress.level = 30
	h.set_tier(DataGuilds.MAX_RANK)
	var sword := ItemGenerator.generate(DB.item_base(&"iron_longsword"), 28, BH.Rarity.MYTHICAL, _rng(7))
	sword.sockets = 3
	sword.gems = ["nova_crystalline", "ember_shard", "ember_fragment"]
	h.inventory.add(sword)
	h.equip_from_inventory(sword, &"main_weapon")
	var armor := ItemGenerator.generate(DB.item_base(&"warden_plate"), 26, BH.Rarity.LEGENDARY, _rng(8))
	armor.sockets = 4
	armor.gems = ["aqua_orbital", "thundra_shard", "vipera_fragment", ""]
	h.inventory.add(armor)
	h.equip_from_inventory(armor, &"armor")
	var helm := ItemGenerator.generate(DB.item_base(&"visored_greathelm"), 26, BH.Rarity.ELITE, _rng(9))
	helm.sockets = 2
	helm.gems = ["", ""]
	h.inventory.add(helm)
	h.equip_from_inventory(helm, &"helm")
	var ring := ItemGenerator.generate(DB.item_base(&"sigil_ring"), 26, BH.Rarity.LEGENDARY, _rng(10))
	ring.sockets = 1
	ring.gems = ["aetherift_orbital"]
	h.inventory.add(ring)
	var boots := ItemGenerator.generate(DB.item_base(&"warden_greave"), 26, BH.Rarity.MYTHICAL, _rng(11))
	boots.sockets = 3
	boots.gems = ["bloodrift_shard", "essencerift_shard", "nova_fragment"]
	h.inventory.add(boots)
	p.refresh_equipment_visuals()
	await _wait(30)
	await _shot("infused_weapon_in_world", 30)
	Game.ui_root.open(&"inventory")
	var inv := Game.ui_root.window(&"inventory") as InventoryWindow
	inv.refresh()
	await _shot("inventory_socketed_gear", 30)
	var ms: ItemSlot = inv.equip_slots.get(&"main_weapon")
	if ms:
		TooltipLayer.show_for(ms, func() -> Control: return Tips.item(sword, {"hero": h}))
		await _shot("tooltip_nova_blast", 20)
		TooltipLayer.hide_for(null)
	var ars: ItemSlot = inv.equip_slots.get(&"armor")
	if ars:
		TooltipLayer.show_for(ars, func() -> Control: return Tips.item(armor, {"hero": h}))
		await _shot("tooltip_threefold_armor", 20)
		TooltipLayer.hide_for(null)
	Game.ui_root.close_all()

func _waypoints() -> void:
	for id in [&"mill_shrine", &"gate_shrine"]:
		await _go(&"westreach", id)
		Game.hero.awakened_shrines[id] = true
		await _wait(40)
		await _shot("waypoint_%s" % id, 20)
	Game.ui_root.open(&"world_map")
	await _shot("world_map_waypoints", 40)
	Game.ui_root.close_all()

func _tempos() -> void:
	var h := Game.hero
	h.inventory.gold = 2000000
	for lvl in [25, 45]:
		h.progress.level = lvl
		var w := Game.ui_root.window(&"tempo_caller") as TempoCallerWindow
		w.open_on(&"renowned")
		w.refresh()
		await _shot("shrine_renowned_level_%d" % lvl, 40)
		Game.ui_root.close_all()
	h.progress.level = 45
	var t := TempoRules.hire_legend(h, &"aurelis")
	if t:
		TempoParty.refresh(h)
		await _wait(60)
		await _shot("eternal_tempo_in_world", 30)

func _boss() -> void:
	var h := Game.hero
	h.progress.level = 60
	for slot in DataBossSets.slots_for_set(&"crimson_glory"):
		var it := DB.make_item(DataBossSets.piece_id(&"crimson_glory", slot), BH.Rarity.MASTER, 60, 5)
		h.inventory.add(it)
		h.equip_from_inventory(it, slot)
	p.refresh_equipment_visuals()
	await _go(&"sanctuary", &"waypoint")
	await _wait(60)
	await _shot("boss_set_worn_in_town", 30)
