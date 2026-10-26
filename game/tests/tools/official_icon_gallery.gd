extends Control
## Runtime presentation evidence. --gallery=<absolute PNG path> --scenario=gallery|skills|upgrades

var _capture := ""
var _scenario := "gallery"
var _status := StatusController.new()

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--gallery="):
			_capture = arg.trim_prefix("--gallery=")
		elif arg.begins_with("--scenario="):
			_scenario = arg.trim_prefix("--scenario=")
	theme = UITheme.theme()
	Settings.icon_border_style = "aether_forged"
	Settings.control_mode = "pc"
	Game.hero = Game.new_hero(&"knight", "Icon Preview")
	Game.hero.progress.level = 120
	var background := ColorRect.new()
	background.color = Color(0.035, 0.03, 0.045)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	if _scenario == "skills":
		var window := SkillsWindow.new()
		add_child(window)
		window.open()
		window.refresh()
	elif _scenario == "upgrades":
		Game.hero.inventory.add(DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 40, 8))
		var margin := MarginContainer.new()
		margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		for edge in ["left", "top", "right", "bottom"]:
			margin.add_theme_constant_override("margin_" + edge, 48)
		add_child(margin)
		var page := WeaponUpgradePage.new(WeaponUpgrades.ENCHANT)
		margin.add_child(page)
		page.refresh(Game.hero)
	else:
		_build_gallery()
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	if _capture != "":
		DirAccess.make_dir_recursive_absolute(_capture.get_base_dir())
		var error := get_viewport().get_texture().get_image().save_png(_capture)
		print("ICON_GALLERY_CAPTURE ", _scenario, " ", _capture, " error=", error)
		get_tree().quit(0 if error == OK else 1)

func _build_gallery() -> void:
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for edge in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + edge, 32)
	add_child(margin)
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 14)
	margin.add_child(content)
	content.add_child(UITheme.title("Beyond Heroes · Official icons", 30, UITheme.GOLD))
	content.add_child(UITheme.label("Separate artwork and transparent frame · live rarity, cooldown, count and status indicators", 19, UITheme.TEXT, UITheme.body_font()))
	for side in [32.0, 44.0, 64.0]:
		var line := HBoxContainer.new()
		line.add_theme_constant_override("separation", 14)
		content.add_child(line)
		var caption := UITheme.label("%d px" % int(side), 18, UITheme.TEXT, UITheme.body_font())
		caption.custom_minimum_size.x = 80
		line.add_child(caption)
		for id in [&"iron_longsword", &"health_potion", &"ember_core"]:
			var slot := ItemSlot.new(ItemSlot.Kind.DISPLAY, side)
			slot.set_item(DB.make_item(id, BH.Rarity.ELITE if id == &"iron_longsword" else BH.Rarity.COMMON, 1, 3))
			line.add_child(slot)
		for i in 3:
			var button := SkillButton.new(&"", side)
			button.set_skill(&"cleave")
			if i == 1:
				button.update_state(3.2, 6.0, "Cooldown")
			elif i == 2:
				button.update_state(0, 0, "Not enough Mana", -1, 20)
			line.add_child(button)
		for i in 2:
			var touch := TouchButton.new(&"gallery_skill", side * 0.5)
			touch.set_icon(UIArt.skill_icon(&"firebolt"))
			if i == 1:
				touch.set_state(2.5, 5.0)
			line.add_child(touch)
		for id in [&"burning", &"regen"]:
			_status.apply(id, 8.0)
			_status.statuses[id].remaining = 4.0
			line.add_child(StatusIcon.new(_status, id, side))
		for id in ["enchant_flame", "tech_whet"]:
			line.add_child(FramedIcon.new(UIArt.icon("upgrades", id), side))
	content.add_child(UITheme.label("Artwork families", 22, UITheme.GOLD, UITheme.body_bold()))
	var grid := GridContainer.new()
	grid.columns = 12
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 12)
	content.add_child(grid)
	var entries := []
	for id in [&"cleave", &"firebolt", &"frost_nova", &"chain_lightning", &"blink", &"radiant_ward"]:
		entries.append([String(id).capitalize(), UIArt.skill_icon(id)])
	for id in ["sword", "potion_health", "mat_ember_core", "shield"]:
		entries.append([id.capitalize(), UIArt.icon("items", id)])
	for id in ["enchant_flame", "enchant_frost", "enchant_storm", "tech_whet", "tech_balance", "tech_serrate"]:
		entries.append([id.capitalize(), UIArt.icon("upgrades", id)])
	for id in ["burning", "frozen", "regen", "guard"]:
		entries.append([id.capitalize(), UIArt.status_icon(StringName(id))])
	for id in ["fire", "water", "dark", "light"]:
		entries.append([id.capitalize(), UIArt.icon("elements", id)])
	for entry in entries:
		var cell := VBoxContainer.new()
		grid.add_child(cell)
		cell.add_child(FramedIcon.new(entry[1], 120.0))
		var label := UITheme.label(entry[0], 16, UITheme.TEXT, UITheme.body_font())
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		label.custom_minimum_size.x = 120
		cell.add_child(label)
