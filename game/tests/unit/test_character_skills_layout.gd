extends TestCase
## Regressions for offscreen character content and learned skills squeezing the tree.

func _init() -> void:
	strict = true

func _frames() -> void:
	for i in 15:
		await host.get_tree().process_frame

func _open(window: UIWindow, vp: SubViewport) -> void:
	window.theme = UITheme.theme()
	vp.add_child(window)
	window.open()
	window._tw.kill()
	window._root.scale = Vector2.ONE * window.fit_scale()

func test_character_checklist_and_statistics_are_reachable() -> void:
	var old := Game.hero
	Game.hero = Game.new_hero(&"mage", "Character Layout")
	Game.hero.tier = 5
	Game.hero.guild = &"swordfin"
	Game.hero.progress.level = 31
	Game.hero.progress.free_points = 20
	var vp := SubViewport.new()
	vp.size = Vector2i(1920, 1080)
	host.add_child(vp)
	var window := CharacterWindow.new()
	_open(window, vp)
	await _frames()
	# Also cover future ranks with longer requirements than the current checklist.
	window._promotion_text.text += "\n" + "Another rank requirement\n".repeat(25)
	for resolution in [Vector2i(1920, 1080), Vector2i(1600, 900), Vector2i(1280, 720)]:
		vp.size = resolution
		await _frames()
		eq(window._frame.size, window.window_size, "character content preserves frame at %s" % resolution)
		ok(Rect2(Vector2.ZERO, Vector2(resolution)).encloses(window._frame.get_global_rect()), "character frame fits %s" % resolution)
		ok(window._frame.get_global_rect().encloses(window._apply.get_global_rect()), "Apply Points remains inside frame")
		window._promotion_scroll.scroll_vertical = 100000
		var stats_scroll := window._stats_box.get_parent() as ScrollContainer
		stats_scroll.scroll_vertical = 100000
		await _frames()
		ok(window._promotion_scroll.get_v_scroll_bar().size.x >= 14, "rank requirements have a draggable scrollbar")
		ok(stats_scroll.get_v_scroll_bar().size.x >= 14, "statistics have a draggable scrollbar")
		var promotion_bottom := window._promotion_text.get_global_rect().end.y
		near(promotion_bottom, window._promotion_scroll.get_global_rect().end.y, 2.0, "last rank requirement is reachable")
		ok(stats_scroll.get_global_rect().intersects(window._stats_box.get_child(window._stats_box.get_child_count() - 2).get_global_rect()), "last statistic group is reachable")
	window.free()
	vp.free()
	Game.hero = old
	done()

func test_all_learned_skills_keep_tree_and_details_in_frame() -> void:
	var old := Game.hero
	var vp := SubViewport.new()
	vp.size = Vector2i(1920, 1080)
	host.add_child(vp)
	for cls in [&"mage", &"knight", &"ranger", &"shadowblade"]:
		Game.hero = Game.new_hero(cls, "Skills Layout")
		Game.hero.progress.level = 31
		for n in Game.hero.skill_tree.tree.nodes:
			Game.hero.skill_tree.ranks[n.id] = 1
		Game.hero._skills_changed()
		var window := SkillsWindow.new()
		_open(window, vp)
		await _frames()
		var learned := Game.hero.learned_skills()
		eq(window._learned.get_child_count(), learned.size(), "%s lists every learned skill" % cls)
		ok(window._learned.size.x <= window._learned_scroll.size.x, "%s learned skills fit sidebar width" % cls)
		ok(window._learned_scroll.get_v_scroll_bar().size.x >= 14, "%s learned skills have a draggable scrollbar" % cls)
		ok(window.tree.get_parent().size.x >= 1000, "%s tree retains most of the window width" % cls)
		window._learned_scroll.scroll_vertical = 100000
		await _frames()
		ok(window._learned_scroll.get_global_rect().intersects(window._learned.get_child(learned.size() - 1).get_global_rect()), "%s last learned skill is reachable" % cls)
		for sid in learned:
			window._show(sid)
			await _frames()
			eq(window._frame.size, window.window_size, "%s detail fits frame" % sid)
		for page in Game.hero.skill_tree.tree.page_count():
			window.tree.set_page(page)
			window._build_tabs()
			await _frames()
			var scroll := window.tree.get_parent() as ScrollContainer
			ok(window.tree.custom_minimum_size.x <= scroll.size.x, "%s page %d fits tree width" % [cls, page])
			for n in window.tree._nodes():
				var center := window.tree.node_center(n) * window.tree.zoom
				eq(window.tree._node_at(center / window.tree.zoom).get("id"), n.id, "scaled node remains selectable")
			scroll.scroll_vertical = 100000
			await _frames()
			var last_node: Dictionary = window.tree._nodes().back()
			var last_center := window.tree.get_global_transform() * (window.tree.node_center(last_node) * window.tree.zoom)
			ok(scroll.get_global_rect().has_point(last_center), "%s page %d bottom node is reachable" % [cls, page])
		# Refreshes can occur repeatedly during learning in one frame.
		window.refresh()
		window.refresh()
		eq(window._learned.get_child_count(), learned.size(), "refresh does not temporarily duplicate icons")
		vp.size = Vector2i(1280, 720)
		await _frames()
		ok(Rect2(Vector2.ZERO, Vector2(vp.size)).encloses(window._frame.get_global_rect()), "%s skills frame fits smaller viewport" % cls)
		window.free()
		vp.size = Vector2i(1920, 1080)
	vp.free()
	Game.hero = old
	done()
