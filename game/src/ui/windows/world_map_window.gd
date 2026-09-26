class_name WorldMapWindow
extends UIWindow
## The M map: Salmonan as an island atlas (AtlasView) with a destination sidebar. Find a place by name or click it;
## the sidebar shows what it is, the recommended level, whether it is awakened, discovered or locked, and why.
## Directions previews a route (Roads / Shortest walk / Waypoints) with its walking distance, a walking estimate and
## numbered steps; Set route tracks it on the HUD (Routes); Clear route removes it. A click never teleports the hero.
## Island / Local / Underground change the view; the world is paused while the map is open (single player).

const KIND_NAMES := {"town": "Town", "service": "Town service", "home": "Home", "shrine": "Waypoint shrine", "junction": "Crossroads",
	"landmark": "Landmark", "district": "Farmland", "dungeon": "Dungeon", "interior": "Building"}

var hero: HeroData
var atlas: AtlasView
var _search: LineEdit
var _results_panel: PanelContainer
var _results: VBoxContainer
var _tabs := {}
var _title: Label
var _sub: Label
var _levels: Label
var _status: Label
var _desc: Label
var _mode_btns: Array[Button] = []
var _dir_btn: Button
var _set_btn: Button
var _clear_btn: Button
var _summary: Label
var _steps: VBoxContainer
var _obj_title: Label
var _obj_text: Label
var _mode := 0
var _selected := ""
var _paused_by_map := false
var _view := "island"
var _legend: Control

func _init() -> void:
	super._init("Map of Salmonan", Vector2(1800, 990))

func _build() -> void:
	var row := hbox(14)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	# ---- the atlas, with its search box and view tabs floating on top
	var frame := inset()
	frame.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	frame.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(frame)
	var holder := Control.new()
	holder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	holder.mouse_filter = Control.MOUSE_FILTER_PASS
	frame.add_child(holder)
	atlas = AtlasView.new()
	atlas.set_anchors_preset(Control.PRESET_FULL_RECT)
	atlas.place_clicked.connect(select)
	holder.add_child(atlas)
	var top := hbox(10)
	top.position = Vector2(14, 12)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(top)
	_search = LineEdit.new()
	_search.placeholder_text = "Find a place (F)"
	_search.custom_minimum_size = Vector2(380, 46)
	_search.add_theme_font_size_override("font_size", 21)
	_search.clear_button_enabled = true
	_search.text_changed.connect(_on_search)
	_search.text_submitted.connect(_on_search_submit)
	top.add_child(_search)
	for v in [["island", "Island"], ["local", "Local"], ["underground", "Underground"]]:
		var b := button(v[1], _set_view.bind(v[0]), &"", 150.0)
		b.toggle_mode = true
		b.custom_minimum_size.y = 46
		b.add_theme_font_size_override("font_size", 20)
		_tabs[v[0]] = b
		top.add_child(b)
	_results_panel = PanelContainer.new()
	_results_panel.theme_type_variation = &"GlassPanel"
	_results_panel.position = Vector2(14, 64)
	_results_panel.custom_minimum_size = Vector2(380, 0)
	_results_panel.visible = false
	holder.add_child(_results_panel)
	_results = vbox(4)
	_results_panel.add_child(_results)
	var zoom_row := hbox(8)
	zoom_row.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	zoom_row.position = Vector2(14, -70)
	zoom_row.grow_vertical = Control.GROW_DIRECTION_BEGIN
	holder.add_child(zoom_row)
	for z in [["+", func() -> void: atlas.zoom_by(1.3)], ["−", func() -> void: atlas.zoom_by(1.0 / 1.3)], ["Center on you", center_on_hero],
			["Whole island", func() -> void: _set_view("island")]]:
		var zb := button(z[0], z[1], &"", 56.0 if String(z[0]).length() < 3 else 0.0)
		zb.custom_minimum_size.y = 44
		zb.add_theme_font_size_override("font_size", 20)
		zoom_row.add_child(zb)
	holder.resized.connect(func() -> void: zoom_row.position = Vector2(14, holder.size.y - 58))
	var legend := MapLegend.new()
	legend.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	legend.position = Vector2(-10, 110)
	legend.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(legend)
	holder.resized.connect(func() -> void: legend.position = Vector2(holder.size.x - legend.custom_minimum_size.x - 12, 108))
	_legend = legend
	# ---- the destination sidebar
	var side_frame := inset(Vector2(470, 0))
	row.add_child(side_frame)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	side_frame.add_child(scroll)
	var side := vbox(10)
	side.custom_minimum_size = Vector2(440, 0)
	side.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(side)
	_title = UITheme.title("", 34, UITheme.GOLD)
	_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	side.add_child(_title)
	_sub = _para(side, 20, UITheme.TEXT_DIM)
	_levels = _para(side, 24, UITheme.GOLD)
	_status = _para(side, 24, Color(0.62, 0.92, 0.95))
	_desc = _para(side, 21, UITheme.TEXT)
	side.add_child(HSeparator.new())
	side.add_child(UITheme.label("Route preference", 21, UITheme.PARCHMENT, UITheme.body_bold()))
	var modes := hbox(6)
	side.add_child(modes)
	var group := ButtonGroup.new()
	for i in RoutePlanner.MODE_NAMES.size():
		var mb := button(RoutePlanner.MODE_NAMES[i], _set_mode.bind(i), &"", 140.0)
		mb.toggle_mode = true
		mb.button_group = group
		mb.custom_minimum_size.y = 44
		mb.add_theme_font_size_override("font_size", 19)
		modes.add_child(mb)
		_mode_btns.append(mb)
	var mode_help := _para(side, 18, UITheme.TEXT_DIM)
	mode_help.text = "Roads keeps to maintained roads. Shortest walk also takes trails. Waypoints may add a jump between awakened shrines."
	var acts := hbox(8)
	side.add_child(acts)
	_dir_btn = button("Directions", _directions, &"", 210.0)
	_set_btn = button("Set route", _set_route, &"PrimaryButton", 210.0)
	for b in [_dir_btn, _set_btn]:
		b.custom_minimum_size.y = 50
		b.add_theme_font_size_override("font_size", 22)
		acts.add_child(b)
	_clear_btn = button("Clear route", _clear_route, &"", 428.0)
	_clear_btn.custom_minimum_size.y = 46
	_clear_btn.add_theme_font_size_override("font_size", 21)
	side.add_child(_clear_btn)
	_summary = _para(side, 24, Color(0.62, 0.92, 0.95))
	_steps = vbox(6)
	side.add_child(_steps)
	side.add_child(HSeparator.new())
	side.add_child(section("Current objective"))
	_obj_title = _para(side, 21, UITheme.GOLD)
	_obj_text = _para(side, 20, UITheme.TEXT)
	# ---- key hints
	var hints := UITheme.label("M or Esc  Close    ·    Mouse wheel  Zoom    ·    Drag  Pan    ·    C  Center on you    ·    F  Find a place",
		19, UITheme.TEXT_DIM, UITheme.body_font())
	hints.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(hints)

func _para(parent: Control, fs: int, col: Color) -> Label:
	var l := UITheme.label("", fs, col, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(430, 0)
	parent.add_child(l)
	return l

# ---- open / close (the world pauses while planning) ---------------------------------------------------------

func open() -> void:
	super.open()
	if Game.in_session and not get_tree().paused:
		get_tree().paused = true
		_paused_by_map = true

func close_window() -> void:
	if visible and _paused_by_map:
		get_tree().paused = false
		_paused_by_map = false
	_search.release_focus()
	super.close_window()

func refresh() -> void:
	hero = Game.hero
	atlas.hero = hero
	_mode = Routes.mode if Routes.active() else (hero.route.get("mode", 0) if hero else 0)
	_mode_btns[_mode].button_pressed = true
	_search.text = ""
	_results_panel.visible = false
	atlas.preview = {}
	await get_tree().process_frame
	_set_view("local" if not DataIsland.MAP_ORIGIN.has(Game.current_map_id) or Game.current_map_id == &"sanctuary" else "island", false)
	var first := Routes.dest if Routes.active() else _default_selection()
	select(first)
	_refresh_objective()

func _default_selection() -> String:
	var o := atlas._objective_place()
	if o != "" and Game.current_map_id == &"sanctuary" and hero and not bool(hero.world_flags.get(&"south_gate_open", false)):
		return "town_gate"
	if o != "":
		return o
	return RoutePlanner.here(Game.current_map_id, Routes.hero_local())

func _refresh_objective() -> void:
	var o := Objectives.current(hero)
	_obj_title.text = o.get("title", "Free to explore")
	_obj_text.text = o.get("step", "Every road on the map is yours to walk.")

# ---- views -------------------------------------------------------------------------------------------------

func _set_view(v: String, animate := true) -> void:
	_view = v
	for k in _tabs:
		_tabs[k].set_pressed_no_signal(k == v)
	atlas.underground = v == "underground"
	if _legend:
		_legend.visible = v != "underground"
	match v:
		"island", "underground":
			atlas.fit_island()
		"local":
			var mid := Game.current_map_id
			if not DataIsland.MAP_ORIGIN.has(mid):
				var here := DataIsland.place(String(mid))
				mid = StringName(DataIsland.place(here.get("anchor", "town")).get("map", "sanctuary")) if not here.is_empty() else &"sanctuary"
			var area: Array = DataIsland.CHARTED_AREAS.get(mid, [DataIsland.MAP_ORIGIN.get(mid, Vector2(500, 425)), Vector2(120, 90)])
			var fit := minf(atlas.size.x / (area[1].x * 2.2), atlas.size.y / (area[1].y * 2.2)) / atlas.fit_zoom()
			atlas.focus_on(area[0], clampf(fit, 1.5, AtlasView.MAX_ZOOM_FIT))
	atlas.queue_redraw()

func center_on_hero() -> void:
	var mid := Game.current_map_id
	if DataIsland.MAP_ORIGIN.has(mid):
		atlas.focus_on(DataIsland.to_atlas(mid, Routes.hero_local()))
	else:
		var here := DataIsland.place(String(mid))
		if not here.is_empty():
			atlas.focus_on(DataIsland.place_atlas(here))

# ---- search ------------------------------------------------------------------------------------------------

func _matches(q: String) -> Array:
	var out := []
	q = q.strip_edges().to_lower()
	if q == "":
		return out
	for p in DataIsland.PLACES:
		if not p.get("listed", false) or not Routes.is_known(hero, p):
			continue
		var hay := ("%s %s %s" % [p.name, KIND_NAMES.get(p.kind, ""), "waypoint shrine" if p.has("shrine") else ""]).to_lower()
		if q in hay:
			out.append(p)
	return out

func _on_search(t: String) -> void:
	for ch in _results.get_children():
		ch.queue_free()
	var found := _matches(t)
	_results_panel.visible = t.strip_edges() != ""
	if found.is_empty() and _results_panel.visible:
		_results.add_child(UITheme.label("No matching places you know.", 20, UITheme.TEXT_DIM, UITheme.body_font()))
		return
	for p in found.slice(0, 7):
		var b := button("%s  ·  %s" % [p.name, KIND_NAMES.get(p.kind, "")], _pick_result.bind(p.id), &"", 370.0)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.add_theme_font_size_override("font_size", 19)
		_results.add_child(b)

func _on_search_submit(t: String) -> void:
	var found := _matches(t)
	if not found.is_empty():
		_pick_result(found[0].id)

func _pick_result(id: String) -> void:
	_search.text = ""
	_results_panel.visible = false
	_search.release_focus()
	select(id)
	var p := DataIsland.place(id)
	if p.kind == "dungeon":
		_set_view("underground")
	else:
		if _view == "underground":
			_set_view("island")
		atlas.focus_on(DataIsland.place_atlas(p), AtlasView.LOCAL_ZOOM_FIT if p.kind in ["service", "home"] else 2.0)

func _unhandled_key_input(e: InputEvent) -> void:
	if not visible or _search.has_focus():
		return
	var k := e as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	match k.keycode:
		KEY_F:
			_search.grab_focus()
		KEY_C:
			center_on_hero()
		KEY_EQUAL, KEY_KP_ADD:
			atlas.zoom_by(1.3)
		KEY_MINUS, KEY_KP_SUBTRACT:
			atlas.zoom_by(1.0 / 1.3)
		_:
			return
	get_viewport().set_input_as_handled()

# ---- selection and routes ----------------------------------------------------------------------------------

func select(id: String) -> void:
	var p := DataIsland.place(id)
	if p.is_empty():
		return
	_selected = id
	atlas.selected = id
	if not (Routes.active() and Routes.dest == id):
		atlas.preview = {}
	var map_def := DB.map_def(StringName(p.map))
	_title.text = p.name
	_sub.text = "%s · %s" % [KIND_NAMES.get(p.kind, "Place"), map_def.display_name if map_def and p.kind != "dungeon" else "Underground"]
	var lv := String(p.get("levels", ""))
	_levels.text = ("Recommended level: %s" % lv.trim_prefix("Level ")) if lv.begins_with("Level") else ("Safe haven: no enemies" if lv.begins_with("Safe") else lv)
	_status.text = _status_text(p)
	_desc.text = p.get("text", "")
	if Routes.active() and Routes.dest == id:
		_show_plan(Routes.plan, true)
	else:
		_summary.text = "Choose Directions to preview a route from where you stand."
		_clear_steps()
	_clear_btn.disabled = not Routes.active()

func _status_text(p: Dictionary) -> String:
	var parts := []
	if StringName(p.map) == Game.current_map_id and (not p.has("pos") or Routes.hero_local().distance_to(p.pos) < 12.0):
		parts.append("You are here.")
	if p.has("shrine"):
		var awake := hero != null and hero.awakened_shrines.has(StringName(p.shrine))
		parts.append("Awakened waypoint: travel here from any awakened shrine." if awake else "Waypoint not yet awakened. Stand on its dais once to awaken it.")
	if p.kind != "dungeon" and not atlas._charted(StringName(p.map)):
		if p.map == "westreach":
			parts.append("Beyond the South Gate. Captain Hald keeps the gate barred until you ask him about the road.")
		else:
			parts.append("Known from the townsfolk; you have not been there yet.")
	if Routes.active() and Routes.dest == p.id:
		parts.append("Route set: follow the directions under the minimap.")
	return " ".join(parts)

func _set_mode(i: int) -> void:
	_mode = i
	if not atlas.preview.is_empty():
		_directions()
	elif Routes.active() and Routes.dest == _selected:
		Routes.set_route(_selected, _mode)
		_show_plan(Routes.plan, true)

func _directions() -> void:
	if _selected == "":
		return
	var plan := RoutePlanner.plan(hero, Game.current_map_id, Routes.hero_local(), _selected, _mode)
	atlas.preview = plan
	_show_plan(plan, false)
	if plan.get("ok", false) and not atlas.underground:
		atlas.fit_points(AtlasView.plan_points(plan))

func _set_route() -> void:
	if _selected == "":
		return
	Routes.set_route(_selected, _mode)
	atlas.preview = {}
	_show_plan(Routes.plan, true)
	_status.text = _status_text(DataIsland.place(_selected))
	_clear_btn.disabled = false
	if Routes.plan.get("ok", false):
		Events.notify.emit("Route set: %s" % DataIsland.place(_selected).name, &"info")

func _clear_route() -> void:
	Routes.clear_route()
	atlas.preview = {}
	_summary.text = "Route cleared."
	_clear_steps()
	_clear_btn.disabled = true
	_status.text = _status_text(DataIsland.place(_selected))

func _clear_steps() -> void:
	for ch in _steps.get_children():
		ch.queue_free()

func _show_plan(plan: Dictionary, tracked: bool) -> void:
	_clear_steps()
	if plan.is_empty():
		return
	_summary.text = RoutePlanner.summary(plan)
	_summary.add_theme_color_override("font_color", Color(0.62, 0.92, 0.95) if plan.get("ok", false) else UITheme.BAD)
	if not plan.get("ok", false):
		return
	var n := 1
	for s in plan.steps:
		var line := hbox(10)
		var num := UITheme.label("%d." % n, 24, UITheme.GOLD, UITheme.body_bold())
		num.custom_minimum_size = Vector2(30, 0)
		line.add_child(num)
		var col := vbox(0)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var t := UITheme.label(s.text, 24, UITheme.PARCHMENT, UITheme.body_font())
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size = Vector2(390, 0)
		col.add_child(t)
		if s.note != "":
			var nt := UITheme.label(s.note, 18, UITheme.TEXT_DIM, UITheme.body_font())
			nt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			nt.custom_minimum_size = Vector2(390, 0)
			col.add_child(nt)
		line.add_child(col)
		_steps.add_child(line)
		n += 1
	if tracked:
		_steps.add_child(UITheme.label("Tracking: the next step shows under the minimap.", 18, Color(0.62, 0.92, 0.95), UITheme.body_font()))

## The legend: shape and colour for every marker (shape carries the meaning, not colour alone).
class MapLegend:
	extends Control
	const ROWS := [["hero", "You"], ["shrine", "Waypoint shrine"], ["dungeon", "Dungeon"], ["objective", "Objective"],
		["road", "Road"], ["trail", "Trail"], ["route", "Your route"]]

	func _init() -> void:
		custom_minimum_size = Vector2(250, 30 + ROWS.size() * 34)

	func _draw() -> void:
		var f := UITheme.body_font()
		draw_rect(Rect2(Vector2.ZERO, custom_minimum_size), Color(0.04, 0.035, 0.03, 0.78))
		draw_rect(Rect2(Vector2.ZERO, custom_minimum_size), UITheme.BRONZE_DIM, false, 2.0)
		var ink := Color(0.08, 0.06, 0.04)
		for i in ROWS.size():
			var c := Vector2(30, 32 + i * 34)
			match ROWS[i][0]:
				"hero":
					draw_colored_polygon(PackedVector2Array([c + Vector2(0, -11), c + Vector2(8, 8), c + Vector2(0, 4), c + Vector2(-8, 8)]), Color(0.95, 1.0, 0.97))
				"shrine":
					draw_circle(c, 11.0, ink)
					draw_circle(c, 9.0, Color(0.5, 0.95, 1.0))
					draw_colored_polygon(PackedVector2Array([c + Vector2(0, -5), c + Vector2(4, 0), c + Vector2(0, 5), c + Vector2(-4, 0)]), ink)
				"dungeon":
					draw_rect(Rect2(c - Vector2(9, 4), Vector2(18, 14)), Color(0.55, 0.4, 0.75))
					draw_circle(c + Vector2(0, -3), 9.0, Color(0.55, 0.4, 0.75))
					draw_rect(Rect2(c - Vector2(3, 0), Vector2(6, 10)), ink)
				"objective":
					draw_colored_polygon(PackedVector2Array([c + Vector2(0, -10), c + Vector2(10, 0), c + Vector2(0, 10), c + Vector2(-10, 0)]), UITheme.GOLD)
				"road":
					draw_line(c - Vector2(14, 0), c + Vector2(14, 0), Color(0.86, 0.74, 0.5), 5.0)
				"trail":
					for k in 3:
						draw_line(c + Vector2(-14 + k * 11, 0), c + Vector2(-8 + k * 11, 0), Color(0.86, 0.74, 0.5), 3.5)
				"route":
					draw_line(c - Vector2(14, 0), c + Vector2(14, 0), Color(0.5, 0.95, 1.0), 5.0)
			draw_string(f, c + Vector2(26, 7), ROWS[i][1], HORIZONTAL_ALIGNMENT_LEFT, -1, 19, UITheme.PARCHMENT)
