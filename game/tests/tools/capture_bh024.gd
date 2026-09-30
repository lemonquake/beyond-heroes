extends Node
## bh-024 evidence: the Leggings on heroes in the game's renderer.
##   --mode=legs      every leggings base alone on a hero (the belt shows: nothing is worn over it) -> legs_front/back.png
##   --mode=outfits   named outfits "Title=id,id,..;Title=..." (--outfits) with their leggings        -> <name>_front/back.png
##   --mode=sets      the boss collections, Legguards included (--theme=<set> for one)                  -> sets_front/back.png
##   --out=<dir>      (default work/lemondev/bh-024/evidence/shots)
var previews: Array[CharacterPreview] = []

func _ready() -> void:
	_run.call_deferred()

func _arg(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name):
			return a.substr(name.length() + 3)
	return def

func _grid(cols: int, cell: Vector2, count: int) -> GridContainer:
	var rows := int(ceil(float(count) / cols))
	get_window().size = Vector2i(int(cell.x) * cols, int(cell.y + 30) * rows)
	get_window().content_scale_size = get_window().size
	get_window().content_scale_factor = 1.0
	var bg := ColorRect.new()
	bg.color = Color("15191f")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var grid := GridContainer.new()
	grid.columns = cols
	grid.add_theme_constant_override("h_separation", 0)
	grid.add_theme_constant_override("v_separation", 0)
	add_child(grid)
	return grid

func _cell(grid: GridContainer, cell: Vector2, title: String) -> CharacterPreview:
	var col := VBoxContainer.new()
	col.custom_minimum_size = Vector2(cell.x, 0)
	grid.add_child(col)
	var p := CharacterPreview.new()
	p.custom_minimum_size = cell
	col.add_child(p)
	p._fidget_t = 10000
	previews.append(p)
	var label := UITheme.label(title, 18, Color("e8d8ae"), UITheme.body_bold())
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.clip_text = true
	label.custom_minimum_size = Vector2(cell.x, 0)
	col.add_child(label)
	return p

func _shot(path: String, frames := 60) -> void:
	for f in frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	print("SAVED ", path)

func _dress(cls: StringName, ids: Array) -> HeroData:
	var h := Game.new_hero(cls, "Legs")
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	for id in ids:
		var it := DB.make_item(StringName(id), BH.Rarity.COMMON, 1, 7)
		if it == null:
			continue
		var slot := h.equipment.auto_slot(it)
		h.equipment.slots[slot] = it
		if it.base.category == &"boots":        # a pair: the same boot on both feet
			h.equipment.slots[&"boots_2"] = DB.make_item(StringName(id), BH.Rarity.COMMON, 1, 8)
	return h

func _both(out: String, tag: String, yaw_front := -0.3, yaw_back := 2.7) -> void:
	for p in previews:
		p._yaw = yaw_front
		p._place_camera()
	await _shot(out.path_join(tag + "_front.png"))
	for p in previews:
		p._yaw = yaw_back
	await _shot(out.path_join(tag + "_back.png"), 20)

func _run() -> void:
	var out := ProjectSettings.globalize_path(_arg("out", "res://../work/lemondev/bh-024/evidence/shots"))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	var mode := _arg("mode", "legs")
	if mode == "legs":
		var ids: Array = []
		for b: ItemBaseDef in DB.item_bases.values():
			if b.category == &"leggings" and not b.boss_exclusive:
				ids.append(b)
		var from := int(_arg("from", "0"))
		var count := int(_arg("count", "18"))
		ids = ids.slice(from, from + count)
		var cell := Vector2(250, 440)
		var grid := _grid(int(_arg("cols", "9")), cell, ids.size())
		for b: ItemBaseDef in ids:
			var cls: StringName = b.class_hint if b.class_hint != &"" else &"knight"
			var p := _cell(grid, cell, b.unique_name if b.unique_name != "" else b.display_name)
			p.show_class(cls, _dress(cls, [b.id]))
			p.zoom = 0.62
			p.focus(0.62, 1.55, 0.0)
		await _both(out, _arg("name", "legs"), -0.35, 2.8)
	elif mode == "outfits":
		var kits := _arg("outfits", "").split(";", false)
		var cell := Vector2(420, 640)
		var grid := _grid(mini(kits.size(), 5), cell, kits.size())
		for k in kits:
			var parts := String(k).split("=")
			var ids: Array = Array(parts[1].split(",", false))
			var first := DB.item_base(StringName(ids[0]))
			var cls: StringName = first.class_hint if first and first.class_hint != &"" else &"knight"
			var p := _cell(grid, cell, parts[0])
			p.show_class(cls, _dress(cls, ids))
			p.zoom = 0.9
		await _both(out, _arg("name", "outfits"))
	elif mode == "sets":
		var ids: Array = BossSetVisuals.THEMES.keys()
		var only := _arg("theme", "")
		if only != "":
			ids = [only]
		var cell := Vector2(440, 620) if only == "" else Vector2(900, 1200)
		var grid := _grid(5 if only == "" else 1, cell, ids.size())
		for id in ids:
			var cls := StringName(BossSetVisuals.THEMES[id][5])
			var p := _cell(grid, cell, BossSetVisuals.THEMES[id][0])
			var h := Game.new_hero(cls, "Set")
			for slot in h.equipment.slots:
				var base := DB.item_base(StringName("boss_%s_%s" % [id, slot]))
				h.equipment.slots[slot] = DB.make_item(base.id, BH.Rarity.MASTER, 30, 345) if base else null
			p.show_class(cls, h)
			p.zoom = 0.85
		await _both(out, "sets" if only == "" else only, -0.25, 2.85)
	print("BH024_CAPTURE_DONE")
	get_tree().quit()
