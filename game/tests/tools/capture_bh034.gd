extends Node
## bh-034 evidence: the forty Ascendant collections worn by heroes of their class (one sheet per tier, front and back,
## with the tier's moving light), rendered by the game's own CharacterPreview.
##   godot --path game res://tests/tools/capture_bh034.tscn -- --out=<dir> [--tier=cosmic]
var previews: Array[CharacterPreview] = []

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	var out := "res://../work/lemondev/bh-034/evidence/sets"
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="): out = arg.substr(6)
		if arg.begins_with("--tier="): only = arg.substr(7)
	out = ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	get_window().size = Vector2i(3800, 1400)
	get_window().content_scale_size = get_window().size
	get_window().content_scale_factor = 1.0
	for r in DataAscendant.TIER:
		var key := String(DataAscendant.TIER[r].key)
		if only != "" and key != only:
			continue
		for c in get_children():
			c.free()
		previews.clear()
		var bg := ColorRect.new()
		bg.color = Color("121418")
		bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		add_child(bg)
		var grid := GridContainer.new()
		grid.columns = 5
		grid.add_theme_constant_override("h_separation", 0)
		grid.add_theme_constant_override("v_separation", 0)
		add_child(grid)
		for row in DataAscendant.COLLECTIONS:
			if int(row[1]) != r:
				continue
			var h := Game.new_hero(StringName(row[3]), "Ascendant Preview")
			var map := {&"helm": "helm", &"armor": "armor", &"inner_garment": "inner", &"leggings": "leggings", &"gloves_1": "gloves",
				&"gloves_2": "gloves", &"boots_1": "boots", &"boots_2": "boots", &"main_weapon": "weapon"}
			var jewel: Array = DataAscendant.JEWEL_SLOTS[row[7]]
			map[jewel[0]] = "accessory"
			if row[3] == &"knight" and not (row[4] in [&"greatsword", &"greataxe", &"spear"]):
				map[&"sub_weapon"] = "shield"
			for slot in h.equipment.slots:
				h.equipment.slots[slot] = DB.make_item(DataAscendant.piece_id(StringName(row[0]), map[slot]), BH.Rarity.COMMON, 110, 345) if map.has(slot) else null
			var col := VBoxContainer.new()
			grid.add_child(col)
			var p := CharacterPreview.new()
			p.custom_minimum_size = Vector2(760, 640)
			col.add_child(p)
			p.zoom = 1.25
			p._place_camera()
			p.show_class(h.cls.id, h)
			p._fidget_t = 10000
			p._yaw = -0.25
			previews.append(p)
			var label := UITheme.label("%s  ·  %s" % [row[2], BH.rarity_name(r)], 28, BH.rarity_color(r), UITheme.body_bold())
			label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			col.add_child(label)
		for frame in 120: await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out.path_join("%s-front.png" % key))
		for p in previews: p._yaw = 2.8
		for frame in 30: await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(out.path_join("%s-back.png" % key))
		print("ASCENDANT_SHEET ", key)
	get_tree().quit()
