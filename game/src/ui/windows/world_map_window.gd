class_name WorldMapWindow
extends UIWindow
## World map (M / Tab): the valley drawn as an illuminated chart. Discovered regions glow with their level range;
## undiscovered ones are hidden in fog; the hero's region pulses; awakened waypoints are marked; the current objective
## is pinned. Hover a region for details.

var hero: HeroData
var _canvas: Control
var _legend: VBoxContainer
var _t := 0.0
var _hover: StringName = &""

const ORDER: Array[StringName] = [&"sanctuary", &"ruined_forest", &"catacombs", &"forgotten_temple", &"boss_arena"]

func _init() -> void:
	super._init("World Map", Vector2(1500, 880))

func _build() -> void:
	var row := hbox(16)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	var cw := inset()
	cw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(cw)
	_canvas = Control.new()
	_canvas.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_canvas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_canvas.mouse_filter = Control.MOUSE_FILTER_STOP
	_canvas.draw.connect(_draw_map)
	_canvas.gui_input.connect(_on_input)
	cw.add_child(_canvas)
	var side := vbox(8)
	side.custom_minimum_size = Vector2(340, 0)
	row.add_child(side)
	side.add_child(section("Regions"))
	_legend = vbox(6)
	side.add_child(_legend)

func refresh() -> void:
	hero = Game.hero
	for c in _legend.get_children():
		c.queue_free()
	if hero == null:
		return
	for id in ORDER:
		var d := DB.map_def(id)
		var known := hero.discovered_maps.has(id)
		var l := UITheme.label(d.display_name if known else "Unexplored", 18, UITheme.PARCHMENT if known else UITheme.TEXT_MUTED, UITheme.title_font())
		_legend.add_child(l)
		if known:
			_legend.add_child(UITheme.label("   " + _levels(d), 14, UITheme.TEXT_DIM, UITheme.body_font()))
	var o := Objectives.current(hero)
	if not o.is_empty():
		_legend.add_child(Tips.gap(10))
		_legend.add_child(section("Objective"))
		_legend.add_child(UITheme.label(o.title, 17, UITheme.GOLD, UITheme.body_bold()))
		var t := UITheme.label(o.text, 15, UITheme.TEXT, UITheme.body_font())
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size = Vector2(320, 0)
		_legend.add_child(t)
	_canvas.queue_redraw()

static func _levels(d: MapDef) -> String:
	if d.is_town:
		return "Safe haven"
	return "Level %d" % d.level_min if d.level_min == d.level_max else "Level %d – %d" % [d.level_min, d.level_max]

func _process(delta: float) -> void:
	if visible:
		_t += delta
		_canvas.queue_redraw()

func _pos(d: MapDef) -> Vector2:
	return Vector2(d.world_map_pos) * _canvas.size

func _draw_map() -> void:
	var r := Rect2(Vector2.ZERO, _canvas.size)
	_canvas.draw_rect(r, Color(0.09, 0.075, 0.06))
	# faint topography: concentric contour rings around each region
	for id in ORDER:
		var d := DB.map_def(id)
		var p := _pos(d)
		for k in 5:
			_canvas.draw_arc(p, 40.0 + k * 34.0, 0.0, TAU, 64, Color(0.55, 0.42, 0.26, 0.07), 1.5)
	if hero == null:
		return
	var font := UITheme.title_font()
	# roads between consecutive regions
	for i in ORDER.size() - 1:
		var a := DB.map_def(ORDER[i])
		var b := DB.map_def(ORDER[i + 1])
		var known := hero.discovered_maps.has(a.id) and hero.discovered_maps.has(b.id)
		var pa := _pos(a)
		var pb := _pos(b)
		var n := 22
		for s in n:
			if s % 2 == 0:
				_canvas.draw_line(pa.lerp(pb, float(s) / n), pa.lerp(pb, float(s + 1) / n), Color(0.85, 0.7, 0.45, 0.8) if known else Color(0.4, 0.35, 0.3, 0.4), 3.0)
	var o := Objectives.current(hero)
	for id in ORDER:
		var d := DB.map_def(id)
		var p := _pos(d)
		var known := hero.discovered_maps.has(id)
		var here := Game.current_map_id == id
		var rad := 26.0 if not d.is_town else 30.0
		if here:
			var pulse := 0.5 + 0.5 * sin(_t * 3.0)
			_canvas.draw_circle(p, rad + 14.0 + pulse * 6.0, Color(0.5, 0.95, 1.0, 0.12 + 0.1 * pulse))
		_canvas.draw_circle(p, rad + 3.0, Color(0, 0, 0, 0.7))
		_canvas.draw_circle(p, rad, (Color(0.75, 0.55, 0.3) if known else Color(0.25, 0.22, 0.2)).lerp(Color(0.5, 0.95, 1.0), 0.5 if here else 0.0))
		_canvas.draw_arc(p, rad, 0.0, TAU, 48, UITheme.GOLD if known else UITheme.BRONZE_DIM, 3.0)
		var icon := UIArt.ui_icon("teleport" if d.waypoint else "skull")
		if icon and known:
			_canvas.draw_texture_rect(icon, Rect2(p - Vector2(14, 14), Vector2(28, 28)), false, Color(0.1, 0.07, 0.05))
		var name := d.display_name if known else "?"
		var fs := 22 if id == _hover else 20
		var w := font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var tp := p + Vector2(-w * 0.5, rad + 30)
		_canvas.draw_string_outline(font, tp, name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 6, Color(0, 0, 0, 0.9))
		_canvas.draw_string(font, tp, name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UITheme.GOLD if here else (UITheme.PARCHMENT if known else UITheme.TEXT_MUTED))
		if known:
			var sub := _levels(d)
			var sw := UITheme.body_font().get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x
			_canvas.draw_string(UITheme.body_font(), p + Vector2(-sw * 0.5, rad + 50), sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, UITheme.TEXT_DIM)
		if not o.is_empty() and o.map == id:
			var qi := UIArt.ui_icon("quest")
			if qi:
				var bob := sin(_t * 4.0) * 4.0
				_canvas.draw_texture_rect(qi, Rect2(p + Vector2(rad - 4, -rad - 30 + bob), Vector2(30, 30)), false, UITheme.GOLD)

func _on_input(e: InputEvent) -> void:
	if e is InputEventMouseMotion and hero:
		var best: StringName = &""
		for id in ORDER:
			if e.position.distance_to(_pos(DB.map_def(id))) < 40.0:
				best = id
		if best != _hover:
			_hover = best
			if best == &"" or not hero.discovered_maps.has(best):
				TooltipLayer.hide_for(_canvas)
			else:
				var d := DB.map_def(best)
				TooltipLayer.show_for(_canvas, func() -> Control: return Tips.text("%s\n%s\n\n%s" % [d.subtitle, _levels(d), d.loading_hint], d.display_name))
