extends Node
## Class Transcendence evidence: every new skill and talent icon with its name, grouped by class (one sheet each).
##   godot --path game res://tests/tools/capture_transcend_icons.tscn -- --out=<dir>

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	var out := ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence/screens")
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.substr(6)
	DirAccess.make_dir_recursive_absolute(out)
	get_window().size = Vector2i(1800, 1100)
	var bg := ColorRect.new()
	bg.color = Color("121418")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var grid := GridContainer.new()
	grid.columns = 6
	grid.position = Vector2(20, 20)
	grid.add_theme_constant_override("h_separation", 18)
	grid.add_theme_constant_override("v_separation", 10)
	add_child(grid)
	for id in DataTranscendence.CLASSES:
		var d: Dictionary = DataTranscendence.CLASSES[id]
		for sid in d.skills:
			grid.add_child(_cell(UIArt.skill_icon(sid), "%s\n%s" % [DB.skill(sid).display_name, d.name], ClassTranscendence.label_color(id)))
		for tid in d.talents:
			var p := DataTranscendence.TALENT_ICON % tid
			grid.add_child(_cell(load(p) if ResourceLoader.exists(p) else null, "%s\n%s talent" % [DataTranscendence.TALENTS[tid].name, d.name], ClassTranscendence.label_color(id)))
		if grid.get_child_count() >= 36:
			await _sheet(out, grid)
	get_tree().quit()

var _n := 0

func _sheet(out: String, grid: GridContainer) -> void:
	for i in 20:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	_n += 1
	get_viewport().get_texture().get_image().save_png(out.path_join("icons_sheet_%d.png" % _n))
	print("SHOT icons_sheet_%d" % _n)
	for c in grid.get_children():
		c.free()

func _cell(tex: Texture2D, text: String, col: Color) -> Control:
	var h := HBoxContainer.new()
	h.custom_minimum_size = Vector2(280, 100)
	var t := TextureRect.new()
	t.texture = tex
	t.custom_minimum_size = Vector2(96, 96)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	h.add_child(t)
	var l := UITheme.label(text, 16, col, UITheme.body_bold())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(170, 0)
	h.add_child(l)
	return h
