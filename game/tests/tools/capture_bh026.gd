extends Node
## bh-026 evidence: the Ember Dragon set in the game's renderer.
##   hero_set.png     a Knight wearing the set: front, side, back
##   hero_action.png  the same hero mid-swing, running, and blocking
##   tempos.png       the knight-type Tempos (Swordsman, Warden) wearing it
##   --out=<dir>      (default work/lemondev/bh-026/evidence/shots)
var previews: Array[CharacterPreview] = []

func _ready() -> void:
	_run.call_deferred()

func _arg(name: String, def: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name):
			return a.substr(name.length() + 3)
	return def

func _grid(cols: int, cell: Vector2, count: int) -> GridContainer:
	for c in get_children():
		c.queue_free()
	previews.clear()
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
	p.hold_fidgets = true
	previews.append(p)
	var label := UITheme.label(title, 18, Color("e8d8ae"), UITheme.body_bold())
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.custom_minimum_size = Vector2(cell.x, 0)
	col.add_child(label)
	return p

func _shot(path: String, frames := 60) -> void:
	for f in frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	print("SAVED ", path)

func _knight() -> HeroData:
	var h := Game.new_hero(&"knight", "Ember")
	for s in h.equipment.slots:
		h.equipment.slots[s] = null
	h.guild = &"swordfin"
	h.set_tier(1)
	Cheats.apply("alj", h)
	for c in h.inventory.cells.duplicate():
		if c != null and DataSpecialWeapons.is_special(c.base):
			h.equip_from_inventory(c)
	return h

func _run() -> void:
	var out := ProjectSettings.globalize_path(_arg("out", "res://../work/lemondev/bh-026/evidence/shots"))
	DirAccess.make_dir_recursive_absolute(out)
	Settings.control_mode = "pc"
	var cell := Vector2(460, 660)
	# the hero, three sides
	var grid := _grid(3, cell, 3)
	var views := [["Front", -0.35], ["Side", -1.45], ["Back", 2.8]]
	for v in views:
		var p := _cell(grid, cell, "Ember Dragon set — %s" % v[0])
		p.show_class(&"knight", _knight())
		p.zoom = 0.85
		p._yaw = v[1]
		p._place_camera()
	await _shot(out.path_join("hero_set.png"))
	# in action
	grid = _grid(3, cell, 3)
	var acts := [["Swing", &"sword_2", 14], ["Run", &"run", 10], ["Heavy", &"sword_heavy", 18]]
	for a in acts:
		var p := _cell(grid, cell, a[0])
		p.show_class(&"knight", _knight())
		p.zoom = 0.85
		p._yaw = -0.6
		p._place_camera()
	for f in 40:
		await get_tree().process_frame
	for i in acts.size():
		var p := previews[i]
		var anim: StringName = acts[i][1]
		if not p.visual.has_anim(anim):
			for alt in [&"sword_1", &"attack_1h_1", &"slash", &"run_1h"]:
				if p.visual.has_anim(alt):
					anim = alt
					break
		p.visual.play_action(anim, 0.35)
	await _shot(out.path_join("hero_action.png"), 18)
	# the knight-type Tempos
	grid = _grid(4, cell, 4)
	var hero := _knight()
	for tc in [&"swordsman", &"warden"]:
		for yaw in [-0.35, 2.8]:
			var t := TempoData.new()
			t.class_id = tc
			for id in DataSpecialWeapons.ids():
				var it := DataSpecialWeapons.unbound(id, 30)
				var slot := TempoRules.auto_slot(t, it)
				if TempoRules.equip_error(hero, t, it, slot) == "":
					t.equipment.slots[slot] = it
			var p := _cell(grid, cell, "%s Tempo" % String(tc).capitalize())
			p.show_tempo(t, 30)
			p.zoom = 0.85
			p._yaw = yaw
			p._place_camera()
	await _shot(out.path_join("tempos.png"))
	print("BH026_CAPTURE_DONE")
	get_tree().quit()
