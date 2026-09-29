extends Node
## Standalone visual check: no player saves, map loading or gameplay mutation.

func _ready() -> void:
	get_tree().root.theme = UITheme.theme()
	Game.hero = HeroData.new()
	Game.hero.setup(DB.class_def(&"knight"), "Inventory Preview")
	Game.hero.init_new()
	Game.hero.inventory.gold = 2480
	for id in [&"iron_helm", &"iron_longsword", &"copper_ring", &"iron_hauberk", &"silverleaf", &"iron_shard", &"quest_seal_key", &"town_portal", &"return_scroll", &"recipe_berserker", &"swiftfoot_tonic", &"rejuvenation_elixir"]:
		var item := DB.make_item(id, BH.Rarity.COMMON, 1, 42)
		if item.base.is_stackable(): item.count = 4
		Game.hero.inventory.add(item)
	var bg := ColorRect.new()
	bg.color = Color("111719")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var window := InventoryWindow.new()
	window.theme = UITheme.theme()
	add_child(window)
	window.open()
	await _shot("all")
	window._bag_tabs.current_tab = 1
	await _shot("gear")
	window._bag_tabs.current_tab = 2
	await _shot("utility")
	window._bag_tabs.current_tab = 3
	await _shot("belt")
	window._category_buttons["scrolls"].pressed.emit()
	window._category_buttons["scrolls"].button_pressed = true
	await _shot("scrolls")
	window._search.text = "No matching item"
	window._search.text_changed.emit(window._search.text)
	await _shot("empty")
	print("FRAME ", window._frame.size, " TARGET ", window.window_size)
	window.hide()
	var filters := AutoLootWindow.new()
	filters.theme = UITheme.theme()
	add_child(filters)
	filters.open()
	await _shot("auto-loot")
	(filters.body.get_child(0) as ScrollContainer).scroll_vertical = 1000
	await _shot("auto-loot-advanced")
	print("FILTER FRAME ", filters._frame.size, " TARGET ", filters.window_size)
	get_tree().quit()

func _shot(name: String) -> void:
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	var dir := ProjectSettings.globalize_path("res://../output/inventory-overhaul")
	DirAccess.make_dir_recursive_absolute(dir)
	get_viewport().get_texture().get_image().save_png(dir.path_join(name + ".png"))
	print("SHOT ", name)
