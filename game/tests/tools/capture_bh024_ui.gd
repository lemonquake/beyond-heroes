extends Node
## bh-024 evidence: the Inventory window's paper doll with the Leggings slot, a leggings tooltip and Brannoc's rack.
##   godot --path game res://tests/tools/capture_bh024_ui.tscn   -> work/lemondev/bh-024/evidence/ui/*.png

func _ready() -> void:
	get_tree().root.theme = UITheme.theme()
	Game.hero = HeroData.new()
	Game.hero.setup(DB.class_def(&"knight"), "Leggings Preview")
	Game.hero.init_new()
	Game.hero.progress.add_xp(XpCurve.total_xp_for_level(20))
	Game.hero.inventory.gold = 12480
	for id in [&"warden_cuisses", &"u_oathbound_cuisses", &"guardian_cuisses", &"riveted_legplates", &"mail_chausses", &"iron_hauberk"]:
		Game.hero.inventory.add(DB.make_item(id, BH.Rarity.ELITE if id == &"warden_cuisses" else BH.Rarity.COMMON, 20, 42))
	var bg := ColorRect.new()
	bg.color = Color("111719")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var ui := UIRoot.new()     # the game's own UI root: windows, tooltip layer
	add_child(ui)
	await get_tree().process_frame
	ui.hud.hide()
	ui.chat.hide()
	ui.touch.hide()
	ui.open(&"inventory")
	var window := ui.window(&"inventory") as InventoryWindow
	window.refresh()
	await _shot("inventory")
	var slot: ItemSlot = window.equip_slots[&"leggings"]
	TooltipLayer.show_for(slot, func() -> Control: return Tips.item(slot.item, {"hero": Game.hero}))
	await _shot("inventory_tooltip")
	TooltipLayer.hide_for(null)
	var bag_item: ItemInstance = null
	for it in Game.hero.inventory.cells:
		if it != null and it.base.id == &"u_oathbound_cuisses":
			bag_item = it
	for c in window.find_children("*", "ItemSlot", true, false):
		if (c as ItemSlot).item == bag_item and bag_item != null:
			TooltipLayer.show_for(c, func() -> Control: return Tips.item(bag_item, {"hero": Game.hero}))
			break
	await _shot("inventory_unique_tooltip")
	TooltipLayer.hide_for(null)
	ui.close_all()
	(ui.window(&"shop") as ShopWindow).open_shop(&"brannoc_forge")
	await _shot("shop_brannoc")
	print("BH024_UI_DONE")
	get_tree().quit()

func _shot(name: String) -> void:
	for f in 20:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var dir := ProjectSettings.globalize_path("res://../work/lemondev/bh-024/evidence/ui")
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir.path_join(name + ".png"))
	print("SHOT ", name)
