extends TestCase
## Regression for the obstructed Tempo window: content must never grow its frame.

func _init() -> void:
	strict = true

func _frames(count := 15) -> void:
	for i in count:
		await host.get_tree().process_frame

func test_long_names_and_responsive_panes_remain_inside_frame() -> void:
	var saved_hero := Game.hero
	var saved_touch := Settings.control_mode
	Game.hero = Game.new_hero(&"knight", "Layout Test")
	Game.hero.tempos.append(TempoRules.legend_data(&"kavira"))
	Game.hero.tempos.append(TempoRules.legend_data(&"hollan"))
	Game.hero.tempos[0].fallen = true
	Settings.control_mode = "pc"
	var vp := SubViewport.new()
	vp.size = Vector2i(1920, 1080)
	host.add_child(vp)
	var window := TempoWindow.new()
	window.theme = UITheme.theme()
	vp.add_child(window)
	window.open()
	window._tw.kill()
	window._root.scale = Vector2.ONE
	await _frames()
	eq(window._frame.size, window.window_size, "fallen state keeps exact frame size")
	ok(Rect2(Vector2.ZERO, Vector2(vp.size)).encloses(window._frame.get_global_rect()), "desktop frame stays onscreen")
	ok(window._tabs.size.y < 80, "class icons do not inflate companion tabs")
	ok(window._bag_scroll.size.x >= window._bag_grid.size.x, "all bag columns fit")
	window._tabs.current_tab = 1
	await _frames()
	eq(window.current, Game.hero.tempos[1], "companion tabs change current spirit")
	Settings.control_mode = "mobile"
	vp.size = Vector2i(1280, 720)
	await _frames()
	ok(window._compact, "native narrow viewport uses compact layout")
	eq(window._frame.size, window.window_size, "compact content cannot inflate frame")
	window._detail_tabs.current_tab = 1
	await _frames()
	ok(window._bag.is_visible_in_tree(), "inventory remains accessible from Your bag")
	window._bag_scroll.scroll_vertical = 100000
	await _frames()
	ok(window._bag_scroll.get_global_rect().intersects(window.cells.back().get_global_rect()), "last bag row is reachable")
	Settings.control_mode = "pc"
	vp.size = Vector2i(1920, 1080)
	await _frames()
	ok(not window._compact, "resize restores desktop layout")
	ok(window._bag.is_visible_in_tree() and window._sheet_scroll.is_visible_in_tree(), "desktop shows inventory and stats together")
	eq(window._frame.size, window.window_size, "old inventory grid width cannot enlarge restored desktop frame")
	Game.hero.tempos.clear()
	window.refresh()
	await _frames()
	ok(window._empty.visible and not window._content.visible, "empty state replaces content")
	window.free()
	vp.free()
	Game.hero = saved_hero
	Settings.control_mode = saved_touch
	done()
