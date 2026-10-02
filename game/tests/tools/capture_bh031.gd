extends Node
## bh-031 evidence: the female body, NPCs and monsters on the hero body, and the ID portraits, in the game's renderer.
##   --mode=female   the female figure bare and in kits, front and back           -> female_front.png, female_back.png
##   --mode=walk     female clips frame by frame (fem_idle, fem_walk, fem_run)     -> female_<clip>.png
##   --out=<dir>     (default work/lemondev/bh-031/evidence)
var previews: Array[CharacterPreview] = []

func _ready() -> void:
	Game.save_slot = 97
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

func _dress(h: HeroData, ids: Array) -> void:
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	for id in ids:
		var it := DB.make_item(StringName(id), BH.Rarity.COMMON, 1, 7)
		if it == null:
			continue
		var slot := h.equipment.auto_slot(it)
		h.equipment.slots[slot] = it
		if it.base.category in [&"gloves", &"boots"]:
			var other := StringName(String(slot).trim_suffix("_1") + "_2") if String(slot).ends_with("_1") else slot
			h.equipment.slots[other] = DB.make_item(StringName(id), BH.Rarity.COMMON, 1, 7)

func _run() -> void:
	var out := ProjectSettings.globalize_path(_arg("out", "res://../work/lemondev/bh-031/evidence"))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	var mode := _arg("mode", "female")
	if mode == "female":
		var plain_f := HeroLook.defaults()
		HeroLook.feminize(plain_f)
		plain_f["hair"] = "long"
		var rows := [
			["Male, plain", HeroLook.defaults(), &"knight", []],
			["Female, plain", plain_f, &"knight", []],
			["Shieldmaiden", HeroLook.preset("shieldmaiden"), &"knight", []],
			["Huntress", HeroLook.preset("huntress"), &"ranger", []],
			["Matron", HeroLook.preset("matron"), &"mage", []],
			["Knight kit", HeroLook.preset("shieldmaiden"), &"knight", ["start"]],
			["Plate", HeroLook.preset("shieldmaiden"), &"knight", ["iron_helm", "iron_hauberk", "padded_gambeson", "iron_cuisses", "iron_gauntlet", "iron_sabaton"]],
			["Robes", HeroLook.preset("huntress"), &"mage", ["sage_robe", "sage_leggings", "sage_gloves", "sage_boots", "silk_undershirt"]],
			["Ranger", HeroLook.preset("huntress"), &"ranger", ["traveler_coat", "hide_leggings", "wayfarer_boot", "silk_glove"]],
			["Crimson Glory", HeroLook.preset("shieldmaiden"), &"knight", ["set:crimson_glory"]],
		]
		var cell := Vector2(440, 640)
		var grid := _grid(5, cell, rows.size())
		for r in rows:
			var p := _cell(grid, cell, r[0])
			var h := Game.new_hero(r[2], "F")
			h.look = r[1]
			var ids: Array = r[3]
			if ids.is_empty():
				_dress(h, [])
			elif String(ids[0]).begins_with("set:"):
				var sid := String(ids[0]).substr(4)
				for slot in h.equipment.slots:
					var base := DB.item_base(StringName("boss_%s_%s" % [sid, slot]))
					h.equipment.slots[slot] = DB.make_item(base.id, BH.Rarity.MASTER, 30, 345) if base else null
			elif ids[0] != "start":
				_dress(h, ids)
			p.show_class(r[2], h)
			p._yaw = -0.3
			p.zoom = 0.9
			p._place_camera()
		await _shot(out.path_join("female_front.png"))
		for p in previews:
			p._yaw = 2.5
		await _shot(out.path_join("female_back.png"), 20)
		for p in previews:
			p._yaw = -1.45
		await _shot(out.path_join("female_side.png"), 20)
	elif mode == "walk":
		var clips := ["fem_idle", "fem_walk", "fem_run", "hero_walk"]
		var frames := 6
		var cell := Vector2(300, 520)
		var grid := _grid(frames, cell, frames * clips.size())
		var cells := []
		for c in clips:
			for f in frames:
				var p := _cell(grid, cell, "%s %d" % [c, f])
				var h := Game.new_hero(&"ranger", "W")
				h.look = HeroLook.preset("huntress") if c != "hero_walk" else HeroLook.preset("veteran")
				_dress(h, ["traveler_coat", "hide_leggings", "wayfarer_boot"])
				p.show_class(&"ranger", h)
				p._yaw = -1.2
				p.zoom = 0.95
				p._place_camera()
				cells.append([p, c, f])
		for f in 30:
			await get_tree().process_frame
		for e in cells:
			var v: CharacterVisual = e[0].visual
			v.set_process(false)
			if v.tree:
				v.tree.active = false
			var ap := v.anim_player
			ap.play(StringName(e[1]))
			ap.seek(ap.current_animation_length * float(e[2]) / frames, true)
			ap.pause()
		await _shot(out.path_join("female_walk.png"), 10)
	print("BH031_CAPTURE_DONE")
	get_tree().quit()
