extends Node
## Render the reported character/skills layouts without loading or modifying a saved hero.

func _ready() -> void:
	_run.call_deferred()

func _shot(label: String) -> void:
	for i in 30:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://../output/ui-layout-%s.png" % label)
	print("CAPTURE ", label)

func _run() -> void:
	Settings.control_mode = "pc"
	Game.hero = Game.new_hero(&"mage", "Hehe")
	var h := Game.hero
	h.progress.level = 31
	h.progress.free_points = 20
	h.progress.skill_points = 19
	h.tier = 5
	h.guild = &"swordfin"
	for n in h.skill_tree.tree.nodes:
		h.skill_tree.ranks[n.id] = 1
	h._skills_changed()
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.025, 0.03)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var character := CharacterWindow.new()
	character.theme = UITheme.theme()
	add_child(character)
	character.open()
	await _shot("character")
	character._promotion_scroll.scroll_vertical = 100000
	(character._stats_box.get_parent() as ScrollContainer).scroll_vertical = 100000
	await _shot("character-bottom")
	character.hide()
	var skills := SkillsWindow.new()
	skills.theme = UITheme.theme()
	add_child(skills)
	skills.open()
	for page in h.skill_tree.tree.page_count():
		skills.tree.set_page(page)
		skills._build_tabs()
		await _shot("mage-page-%d" % page)
		if page == 0:
			(skills.tree.get_parent() as ScrollContainer).scroll_vertical = 100000
			await _shot("mage-tree-bottom")
			(skills.tree.get_parent() as ScrollContainer).scroll_vertical = 0
	skills._learned_scroll.scroll_vertical = 100000
	var last := skills._learned.get_child(skills._learned.get_child_count() - 1) as SkillButton
	last.activated.emit(last)
	await _shot("learned-bottom")
	get_tree().quit()
