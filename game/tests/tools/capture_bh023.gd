extends Node
## bh-023 evidence: heroes on plinths in the game's renderer.
##   --mode=looks   the creator's presets, whole body and face        -> looks_body.png, looks_face.png
##   --mode=gear    each class's starting kit and a few outfits        -> gear.png
##   --mode=sets    the fifteen boss collections on the hero body      -> sets.png
##   --out=<dir>    (default work/lemondev/bh-023/evidence/shots)
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
	get_window().size = Vector2i(int(cell.x) * cols, int(cell.y + 44) * rows)
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
	grid.add_child(col)
	var p := CharacterPreview.new()
	p.custom_minimum_size = cell
	col.add_child(p)
	p._fidget_t = 10000
	previews.append(p)
	var label := UITheme.label(title, 26, Color("e8d8ae"), UITheme.body_bold())
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(label)
	return p

func _shot(path: String, frames := 60) -> void:
	for f in frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	print("SAVED ", path)

func _run() -> void:
	var out := ProjectSettings.globalize_path(_arg("out", "res://../work/lemondev/bh-023/evidence/shots"))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	var mode := _arg("mode", "looks")
	if mode == "looks":
		var cell := Vector2(480, 640)
		var grid := _grid(5, cell, HeroLook.PRESETS.size())
		for pr in HeroLook.PRESETS:
			var p := _cell(grid, cell, pr[1])
			var h := Game.new_hero(&"knight", "Look")
			h.look = HeroLook.preset(pr[0])
			for s in h.equipment.slots:
				h.equipment.slots[s] = null
			p.show_class(&"knight", h)
			p._yaw = -0.35
			p.zoom = 0.9
			p._place_camera()
		await _shot(out.path_join("looks_body.png"))
		for p in previews:
			p._yaw = -0.45
			p.zoom = 1.0
			p.focus(1.66 * float(p.visual.hero.look["height"]), 1.35, 0.0)
		await _shot(out.path_join("looks_face.png"), 20)
		for p in previews:
			p._yaw = 0.0
		await _shot(out.path_join("looks_front.png"), 20)
	elif mode == "gear":
		var cell := Vector2(560, 760)
		var kits := []
		for c in [&"knight", &"mage", &"ranger", &"shadowblade"]:
			kits.append([DB.class_def(c).display_name + " starting kit", c, []])
		for extra in _arg("items", "").split(";", false):
			kits.append([extra, &"knight", extra.split(",", false)])
		var grid := _grid(4, cell, kits.size())
		for k in kits:
			var p := _cell(grid, cell, k[0])
			var h := Game.new_hero(k[1], "Gear")
			if not (k[2] as Array).is_empty():
				for s in h.equipment.slots:
					h.equipment.slots[s] = null
				for id in k[2]:
					var it := DB.make_item(StringName(id), BH.Rarity.COMMON, 1, 7)
					if it:
						var slot := h.equipment.auto_slot(it)
						h.equipment.slots[slot] = it
			p.show_class(k[1], h)
			p._yaw = -0.3
			p.zoom = 0.9
			p._place_camera()
		await _shot(out.path_join(_arg("name", "gear") + "_front.png"))
		for p in previews:
			p._yaw = 2.7
		await _shot(out.path_join(_arg("name", "gear") + "_back.png"), 20)
	elif mode == "sets":
		var cell := Vector2(560, 700)
		var ids: Array = BossSetVisuals.THEMES.keys()
		var only := _arg("theme", "")
		if only != "":
			ids = [only]
			cell = Vector2(1100, 1300)
		var grid := _grid(5 if only == "" else 1, cell, ids.size())
		for id in ids:
			var p := _cell(grid, cell, BossSetVisuals.THEMES[id][0])
			var h := Game.new_hero(StringName(BossSetVisuals.THEMES[id][5]), "Set")
			for slot in h.equipment.slots:
				var base := DB.item_base(StringName("boss_%s_%s" % [id, slot]))
				h.equipment.slots[slot] = DB.make_item(base.id, BH.Rarity.MASTER, 30, 345) if base else null
			p.show_class(h.cls.id, h)
			p._yaw = -0.25
			p.zoom = 0.85
			p._place_camera()
		await _shot(out.path_join("sets_front.png" if only == "" else only + "_front.png"))
		for p in previews:
			p._yaw = 2.85
		await _shot(out.path_join("sets_back.png" if only == "" else only + "_back.png"), 20)
	elif mode == "creator":
		var res := _arg("res", "1920x1080").split("x")
		get_window().size = Vector2i(int(res[0]), int(res[1]))
		if _arg("touch", "0") == "1":
			Settings.control_mode = "mobile"
		var c := HeroCreator.new()
		c.class_id = StringName(_arg("class", "knight"))
		c.look = HeroLook.preset(_arg("look", "veteran"))
		c.hero_name = "Aldric"
		add_child(c)
		var tag := _arg("name", "creator")
		for f in 40:
			await get_tree().process_frame
		for page in _arg("pages", "0,1,2,4,9").split(","):
			c._show_page(int(page))
			await _shot(out.path_join("%s_%s.png" % [tag, HeroCreator.PAGES[int(page)][0]]), 45)
			print("CAM ", page, " ", c.preview.camera.position, " fh=", c.preview.focus_height, " fd=", c.preview.focus_dist, " zoom=", c.preview.zoom, " vis=", c.preview.visual.position, c.preview.visual.rotation, c.preview.visual.model.scale, " vp=", c.preview.viewport.size)
		c._gear_btn.button_pressed = false
		c._toggle_gear()
		c._show_page(1)
		c._set_look(HeroLook.preset("goblin"), "x")
		await _shot(out.path_join("%s_goblin_bare.png" % tag), 45)
	print("BH023_CAPTURE_DONE")
	get_tree().quit()
