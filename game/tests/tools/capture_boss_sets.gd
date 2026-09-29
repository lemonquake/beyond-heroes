extends Node
const Art = preload("res://src/actors/boss_set_visuals.gd")
var previews: Array[CharacterPreview] = []

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	var out := "res://../work/lemondev/tempo-armory/evidence/boss-sets"
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="): out = arg.substr(6)
		if arg.begins_with("--theme="): only = arg.substr(8)
	out = ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	get_window().size = Vector2i(3840,2160) if only.is_empty() else Vector2i(1280,1440)
	get_window().content_scale_size = get_window().size
	get_window().content_scale_factor = 1.0
	var bg := ColorRect.new()
	bg.color = Color("15191f")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var grid := GridContainer.new()
	grid.columns = 5 if only.is_empty() else 1
	grid.add_theme_constant_override("h_separation",0)
	grid.add_theme_constant_override("v_separation",0)
	add_child(grid)
	for id in Art.THEMES:
		if not only.is_empty() and id != only: continue
		var h := Game.new_hero(StringName(Art.THEMES[id][5]),"Boss Set Preview")
		for slot in h.equipment.slots:
			var base_id := StringName("boss_%s_%s" % [id,slot])
			var base := DB.item_base(base_id)
			h.equipment.slots[slot] = DB.make_item(base_id,BH.Rarity.MASTER,30,345) if base else null
		var col := VBoxContainer.new()
		grid.add_child(col)
		var p := CharacterPreview.new()
		p.custom_minimum_size = Vector2(760,632) if only.is_empty() else Vector2(1260,1310)
		col.add_child(p)
		p.zoom = 0.83
		p._place_camera()
		p.show_class(h.cls.id,h)
		p._fidget_t = 10000
		p._yaw = -0.18
		previews.append(p)
		var label := UITheme.label(Art.THEMES[id][0],30 if only.is_empty() else 42,Color("e8d8ae"),UITheme.body_bold())
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(label)
		print("DRESSED ",id," attachments=",p.visual._set_nodes.size())
	for frame in 90: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("all-15-front.png" if only.is_empty() else only + "-front.png"))
	for p in previews: p._yaw = 2.85
	for frame in 15: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("all-15-back.png" if only.is_empty() else only + "-back.png"))
	print("BOSS_SET_CAPTURE_DONE")
	get_tree().quit()
