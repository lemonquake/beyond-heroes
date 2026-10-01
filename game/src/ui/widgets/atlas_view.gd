class_name AtlasView
extends Control
## The island atlas canvas of the M map: the clean painted base (tools/ui_art/salmonan_atlas.py), a mist shader over
## uncharted land, and native layers drawn from DataIsland on top: roads and trails, the route, place markers (shape
## plus colour: triangle hero, circle shrine, arch dungeon, diamond objective), labels and the hero's true position.
## Wheel zooms about the cursor, drag pans, click selects a place. Coordinates are atlas pixels (DataIsland.ATLAS_SIZE).

signal place_clicked(place_id: String)

const MIN_ZOOM_FIT := 0.92          # zoom limits relative to "whole island fits"
const MAX_ZOOM_FIT := 7.0
const LOCAL_ZOOM_FIT := 3.2         # at or past this, town services, homes and street names appear
const PICK_PX := 20.0

const FOG_SHADER := """
shader_type canvas_item;
uniform sampler2D mist : repeat_enable, filter_linear;
uniform vec2 origin;
uniform float zoom = 1.0;
uniform vec2 view_size;
uniform vec4 areas[8];
uniform int count = 0;
uniform float time = 0.0;
void fragment() {
	vec2 a = origin + UV * view_size / zoom;
	float reveal = 0.0;
	for (int i = 0; i < 8; i++) {
		if (i >= count) { break; }
		vec2 d = (a - areas[i].xy) / areas[i].zw;
		reveal = max(reveal, 1.0 - smoothstep(0.72, 1.04, length(d)));
	}
	float m = texture(mist, a / 360.0 + vec2(time * 0.004, 0.0)).a;
	float m2 = texture(mist, a / 150.0 - vec2(0.0, time * 0.006)).a;
	float fog = (0.5 + 0.3 * m * m2 + 0.12 * m) * (1.0 - reveal);
	COLOR = vec4(vec3(0.1, 0.13, 0.17) + vec3(0.2, 0.22, 0.25) * m, clamp(fog, 0.0, 0.8));
}
"""

var hero: HeroData
var selected := ""
var hover := ""
var preview := {}                    # a RoutePlanner plan drawn in cyan (the tracked route when no preview)
var underground := false
var zoom := 1.0                      # screen px per atlas px
var center := DataIsland.ATLAS_SIZE * 0.5
var _base: Texture2D
var _fog: ColorRect
var _overlay: Control
var _t := 0.0
var _drag_from := Vector2.ZERO
var _drag_center := Vector2.ZERO
var _dragging := false
var _pressed := false

func _init() -> void:
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_ALL

func _ready() -> void:
	_load_base()
	_fog = ColorRect.new()
	_fog.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fog.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = FOG_SHADER
	mat.shader = sh
	if ResourceLoader.exists("res://assets/ui/atlas/atlas_mist.png"):
		mat.set_shader_parameter("mist", load("res://assets/ui/atlas/atlas_mist.png"))
	_fog.material = mat
	add_child(_fog)
	_overlay = Control.new()
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.draw.connect(_draw_overlay)
	add_child(_overlay)
	resized.connect(func() -> void: _clamp_view())

## bh-029: the painted base of the island the atlas shows (DataIsland.show_island).
var _base_path := ""

func _load_base() -> void:
	_base_path = DataIsland.ATLAS_ART
	_base = load(_base_path) if ResourceLoader.exists(_base_path) else null
	queue_redraw()

# ---- view --------------------------------------------------------------------------------------------------

func fit_zoom() -> float:
	if size.x < 10.0 or size.y < 10.0:
		return 1.0
	return minf(size.x / DataIsland.ATLAS_SIZE.x, size.y / DataIsland.ATLAS_SIZE.y) * 1.02

func zoom_fit_factor() -> float:
	return zoom / fit_zoom()

func fit_island() -> void:
	zoom = fit_zoom() * 1.05
	center = DataIsland.ATLAS_SIZE * 0.5 + Vector2(0, 10)
	_clamp_view()

func focus_on(atlas: Vector2, fit_factor := -1.0) -> void:
	if fit_factor > 0.0:
		zoom = fit_zoom() * fit_factor
	center = atlas
	_clamp_view()

## Frame a set of atlas points (a route) with a margin, never closer than MAX_ROUTE_FIT.
const MAX_ROUTE_FIT := 3.6

func fit_points(pts: Array) -> void:
	if pts.is_empty():
		return
	var r := Rect2(pts[0], Vector2.ZERO)
	for p in pts:
		r = r.expand(p)
	r = r.grow(40.0)
	zoom = minf(size.x / maxf(r.size.x, 1.0), size.y / maxf(r.size.y, 1.0))
	zoom = minf(zoom, fit_zoom() * MAX_ROUTE_FIT)
	center = r.get_center()
	_clamp_view()

## Atlas points of a plan: its walked legs and the places at each end of its links.
static func plan_points(plan: Dictionary) -> Array:
	var out := []
	for leg in plan.get("legs", []):
		var mid := StringName(leg.map)
		if leg.kind == "road" and DataIsland.MAP_ORIGIN.has(mid):
			for p in leg.points:
				out.append(DataIsland.to_atlas(mid, p))
		else:
			for id in [leg.from, leg.to]:
				var pl := DataIsland.place(String(id))
				if not pl.is_empty():
					out.append(DataIsland.place_atlas(pl))
	return out

func to_screen(a: Vector2) -> Vector2:
	return size * 0.5 + (a - center) * zoom

func to_atlas(s: Vector2) -> Vector2:
	return center + (s - size * 0.5) / zoom

func _clamp_view() -> void:
	zoom = clampf(zoom, fit_zoom() * MIN_ZOOM_FIT, fit_zoom() * MAX_ZOOM_FIT)
	var half := size * 0.5 / zoom
	var lo := half - Vector2(60, 60)
	var hi := DataIsland.ATLAS_SIZE - half + Vector2(60, 60)
	center.x = clampf(center.x, minf(lo.x, hi.x), maxf(lo.x, hi.x)) if lo.x < hi.x else DataIsland.ATLAS_SIZE.x * 0.5
	center.y = clampf(center.y, minf(lo.y, hi.y), maxf(lo.y, hi.y)) if lo.y < hi.y else DataIsland.ATLAS_SIZE.y * 0.5
	queue_redraw()

func zoom_by(f: float, about := Vector2(-1, -1)) -> void:
	var pivot := about if about.x >= 0.0 else size * 0.5
	var before := to_atlas(pivot)
	zoom *= f
	_clamp_view()
	center += before - to_atlas(pivot)
	_clamp_view()

func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	_t += delta
	var m := _fog.material as ShaderMaterial
	m.set_shader_parameter("origin", to_atlas(Vector2.ZERO))
	m.set_shader_parameter("zoom", zoom)
	m.set_shader_parameter("view_size", size)
	m.set_shader_parameter("time", _t)
	var areas := []
	for id in DataIsland.CHARTED_AREAS:
		if _charted(id):
			var a: Array = DataIsland.CHARTED_AREAS[id]
			areas.append(Vector4(a[0].x, a[0].y, a[1].x, a[1].y))
	m.set_shader_parameter("count", areas.size())
	while areas.size() < 8:
		areas.append(Vector4.ZERO)
	m.set_shader_parameter("areas", PackedVector4Array(areas))
	_overlay.queue_redraw()

## Charted on the atlas: the map has been visited, or (Westreach) its roads are open public geography.
func _charted(map_id: StringName) -> bool:
	if hero == null:
		return map_id == &"sanctuary"
	if hero.discovered_maps.has(map_id):
		return true
	return map_id == &"westreach" and bool(hero.world_flags.get(&"south_gate_open", false))

# ---- input -------------------------------------------------------------------------------------------------

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton:
		var mb := e as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom_by(1.15, mb.position)
			accept_event()
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom_by(1.0 / 1.15, mb.position)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_pressed = true
				_dragging = false
				_drag_from = mb.position
				_drag_center = center
				grab_focus()
			else:
				if _pressed and not _dragging:
					var id := pick(mb.position)
					if id != "":
						place_clicked.emit(id)
				_pressed = false
				_dragging = false
			accept_event()
	elif e is InputEventMouseMotion:
		var mm := e as InputEventMouseMotion
		if _pressed and (_dragging or mm.position.distance_to(_drag_from) > 5.0):
			_dragging = true
			center = _drag_center - (mm.position - _drag_from) / zoom
			_clamp_view()
		var h := pick(mm.position)
		if h != hover:
			hover = h
			mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if h != "" else Control.CURSOR_ARROW

## The visible place under a screen point (markers first, then labels).
func pick(p: Vector2) -> String:
	var best := ""
	var bd := PICK_PX
	if underground:
		for slot in _underground_slots():
			if Rect2(slot[1] - Vector2(20, 28), Vector2(slot[2], UG_ROW - 6)).has_point(p):
				return slot[0]
		return ""
	for pl in visible_places():
		var d := to_screen(DataIsland.place_atlas(pl)).distance_to(p)
		if d < bd:
			bd = d
			best = pl.id
	return best

## Places drawn at the current zoom: listed and known; services and homes only when zoomed in to street level.
func visible_places() -> Array:
	var out := []
	if underground:
		return out
	var local := zoom_fit_factor() >= LOCAL_ZOOM_FIT
	for p in DataIsland.PLACES:
		if not p.get("listed", false) or not Routes.is_known(hero, p) or not DataIsland.on_view(p):
			continue
		if p.kind == "dungeon":
			continue
		if (p.kind == "service" or p.kind == "home") and not local:
			continue
		out.append(p)
	return out

# ---- drawing -----------------------------------------------------------------------------------------------

func _draw() -> void:
	if _base_path != DataIsland.ATLAS_ART:
		_load_base()
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.02, 0.05, 0.07))
	if _base:
		draw_texture_rect(_base, Rect2(to_screen(Vector2.ZERO), DataIsland.ATLAS_SIZE * zoom), false)

func _draw_overlay() -> void:
	var c := _overlay
	var font := UITheme.title_font()
	var body := UITheme.body_font()
	var zf := zoom_fit_factor()
	var local := zf >= LOCAL_ZOOM_FIT
	if underground:
		c.draw_rect(Rect2(Vector2.ZERO, size), Color(0.02, 0.02, 0.04, 0.72))
	# roads: public geography of charted maps; faint where the land is still under mist
	var rw := clampf(zoom * 3.2, 2.5, 9.0)
	for r in DataIsland.ROADS:
		var mid := StringName(r.map)
		if not DataIsland.MAP_ORIGIN.has(mid) or underground:
			continue
		if mid == &"sanctuary" and not local and r.type == "trail":
			continue
		var pts := PackedVector2Array()
		for p in r.points:
			pts.append(to_screen(DataIsland.to_atlas(mid, p)))
		var a := 1.0 if _charted(mid) else 0.35
		var w := rw * (0.6 if r.type == "trail" else 1.0) * (0.75 if mid == &"sanctuary" else 1.0)
		c.draw_polyline(pts, Color(0.1, 0.07, 0.04, 0.8 * a), w + 3.0, true)
		if r.type == "trail":
			_dashed(c, pts, Color(0.86, 0.74, 0.5, 0.95 * a), w, 7.0, 6.0)
		else:
			c.draw_polyline(pts, Color(0.86, 0.74, 0.5, 0.95 * a), w, true)
	# road names at street level
	if zf >= 2.2 and not underground:
		for r in DataIsland.ROADS:
			var mid2 := StringName(r.map)
			if not DataIsland.MAP_ORIGIN.has(mid2) or not _charted(mid2) or (mid2 == &"sanctuary" and zf < 6.0):
				continue
			_road_label(c, r, UITheme.body_font())
	# the route: tracked (Routes) or previewed (sidebar Directions)
	var plan := preview if not preview.is_empty() else Routes.plan
	if plan.get("ok", false) and not underground:
		_draw_route(c, plan)
	# uncharted region names
	if not underground:
		for rg in DataIsland.REGIONS:
			var sp := to_screen(rg.pos)
			var tw := font.get_string_size(rg.name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22).x
			c.draw_string_outline(font, sp - Vector2(tw * 0.5, 0), rg.name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, 6, Color(0, 0, 0, 0.6))
			c.draw_string(font, sp - Vector2(tw * 0.5, 0), rg.name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(0.75, 0.8, 0.82, 0.7))
	# places: markers first, then labels by priority; a label that would overlap one already placed is skipped
	var obj := _objective_place()
	var shown := visible_places()
	shown.sort_custom(func(a, b): return _label_rank(a) < _label_rank(b))
	var taken: Array[Rect2] = []
	for p in shown:
		_draw_place(c, p, obj == p.id)
	for p in shown:
		_draw_label(c, p, taken)
	if underground:
		_draw_underground(c, font, body)
	if not underground:
		_draw_party(c)
		_draw_hero(c, font)
	_draw_compass_and_scale(c, body)

static func _dashed(c: Control, pts: PackedVector2Array, col: Color, w: float, dash: float, gap: float) -> void:
	var on := true
	var left := dash
	for i in pts.size() - 1:
		var a := pts[i]
		var b := pts[i + 1]
		var seg := a.distance_to(b)
		var pos := 0.0
		while pos < seg:
			var step := minf(left, seg - pos)
			if on:
				c.draw_line(a.lerp(b, pos / seg), a.lerp(b, (pos + step) / seg), col, w, true)
			pos += step
			left -= step
			if left <= 0.001:
				on = not on
				left = dash if on else gap

func _road_label(c: Control, r: Dictionary, font: Font) -> void:
	var pts: Array = r.points
	var total := DataIsland.polyline_length(pts)
	if total < 20.0:
		return
	var a := DataIsland.point_at(pts, total * 0.5 - 2.0)
	var b := DataIsland.point_at(pts, total * 0.5 + 2.0)
	var sa := to_screen(DataIsland.to_atlas(StringName(r.map), a))
	var sb := to_screen(DataIsland.to_atlas(StringName(r.map), b))
	var ang := (sb - sa).angle()
	if ang > PI * 0.5:
		ang -= PI
	elif ang < -PI * 0.5:
		ang += PI
	var fs := 18
	var tw := font.get_string_size(r.name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	c.draw_set_transform((sa + sb) * 0.5, ang, Vector2.ONE)
	c.draw_string_outline(font, Vector2(-tw * 0.5, -7), r.name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 5, Color(0.05, 0.03, 0.02, 0.85))
	c.draw_string(font, Vector2(-tw * 0.5, -7), r.name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0.95, 0.88, 0.7))
	c.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_route(c: Control, plan: Dictionary) -> void:
	var cyan := Color(0.5, 0.95, 1.0)
	var pulse := 0.75 + 0.25 * sin(_t * 3.0)
	for leg in plan.legs:
		var mid := StringName(leg.map)
		if leg.kind == "road" and DataIsland.MAP_ORIGIN.has(mid):
			var pts := PackedVector2Array()
			for p in leg.points:
				pts.append(to_screen(DataIsland.to_atlas(mid, p)))
			if pts.size() >= 2:
				c.draw_polyline(pts, Color(0.02, 0.15, 0.2, 0.9), 9.0, true)
				c.draw_polyline(pts, Color(cyan, 0.35 * pulse), 12.0, true)
				c.draw_polyline(pts, cyan, 4.5, true)
		elif leg.kind == "shrine" or leg.kind == "dungeon":
			var a := to_screen(DataIsland.place_atlas(DataIsland.place(leg.from)))
			var b := to_screen(DataIsland.place_atlas(DataIsland.place(leg.to)))
			if a.distance_to(b) > 6.0:
				var mid2 := (a + b) * 0.5 + (b - a).orthogonal().normalized() * minf(60.0, a.distance_to(b) * 0.2)
				var arc := PackedVector2Array()
				for i in 25:
					var t := i / 24.0
					arc.append(a.lerp(mid2, t).lerp(mid2.lerp(b, t), t))
				_dashed(c, arc, Color(cyan, 0.9), 3.5, 9.0, 8.0)
	# destination flag
	var d := DataIsland.place(plan.dest)
	if not d.is_empty():
		var sp := to_screen(DataIsland.place_atlas(d))
		c.draw_line(sp, sp + Vector2(0, -34), Color(0.1, 0.08, 0.05), 3.0)
		c.draw_colored_polygon(PackedVector2Array([sp + Vector2(0, -34), sp + Vector2(20, -28), sp + Vector2(0, -21)]), cyan)

func _objective_place() -> String:
	if hero == null:
		return ""
	var o := Objectives.current(hero)
	if o.is_empty():
		return ""
	return {&"sanctuary": "town", &"ruined_forest": "rf_gate", &"catacombs": "catacombs", &"forgotten_temple": "temple",
		&"boss_arena": "throne"}.get(o.map, "")

func _label_rank(p: Dictionary) -> int:
	if p.id == selected:
		return 0
	if p.id == hover:
		return 1
	if p.has("gate"):
		return 3
	return {"town": 2, "shrine": 3, "district": 3, "dungeon": 3, "landmark": 4, "junction": 5, "service": 6, "home": 7}.get(p.kind, 8)

func _draw_label(c: Control, p: Dictionary, taken: Array[Rect2]) -> void:
	var font := UITheme.body_bold()
	var sp := to_screen(DataIsland.place_atlas(p))
	var gate := p.has("gate")
	var fs := 24 if p.kind in ["town", "district", "shrine", "dungeon"] or gate else (21 if p.kind in ["landmark", "junction"] else 19)
	var sel: bool = p.id == selected or p.id == hover
	if sel:
		fs += 2
	var name: String = p.name
	if gate:
		name = String(DataDungeons.get_def(StringName(p.gate)).get("name", p.name))
	var tw := font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var r := 14.0 if p.kind == "town" else (7.0 if p.kind in ["service", "home"] else 11.0)
	var tp := sp + Vector2(-tw * 0.5, r + fs + 2)
	var box := Rect2(tp + Vector2(-4, -fs), Vector2(tw + 8, fs + 8 + (20 if gate else 0)))
	if not sel:
		for t in taken:
			if t.intersects(box):
				return
	taken.append(box)
	var charted: bool = _charted(StringName(p.map))
	var col := UITheme.GOLD if p.id == selected else (UITheme.PARCHMENT if charted else Color(0.82, 0.82, 0.8))
	c.draw_string_outline(font, tp, name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 7, Color(0.02, 0.02, 0.02, 0.92))
	c.draw_string(font, tp, name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
	if gate:
		# the level range and difficulty under a dungeon's name (bh-013)
		var did := StringName(p.gate)
		var lr := DataDungeons.level_range(did)
		var sub := "Lv %d–%d  %s" % [lr.x, lr.y, DataDungeons.tier_stars(did)]
		var body := UITheme.body_bold()
		var sw := body.get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 17).x
		var sp2 := sp + Vector2(-sw * 0.5, r + fs + 22)
		c.draw_string_outline(body, sp2, sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, 6, Color(0.02, 0.02, 0.02, 0.92))
		c.draw_string(body, sp2, sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, tier_color(did).lightened(0.35))

func _draw_place(c: Control, p: Dictionary, objective: bool) -> void:
	var sp := to_screen(DataIsland.place_atlas(p))
	var charted: bool = _charted(StringName(p.map)) or p.kind == "dungeon"
	var dim := 1.0 if charted else 0.6
	var sel: bool = p.id == selected
	var r := 11.0
	var ink := Color(0.08, 0.06, 0.04, 0.95)
	if sel:
		var pr := 22.0 + sin(_t * 4.0) * 2.5
		c.draw_arc(sp, pr, 0.0, TAU, 40, UITheme.GOLD, 3.0, true)
	if p.has("gate"):
		_draw_gate(c, sp, StringName(p.gate), dim)
		return
	# a crossroads with a waypoint shrine (bh-022) shows as a shrine
	match ("shrine" if p.has("shrine") and p.kind == "junction" else p.kind):
		"town":
			r = 14.0
			c.draw_circle(sp, r + 2.5, ink)
			c.draw_circle(sp, r, Color(0.86, 0.62, 0.32, dim))
			c.draw_rect(Rect2(sp - Vector2(5, 7), Vector2(10, 12)), ink)
			c.draw_colored_polygon(PackedVector2Array([sp + Vector2(-7, -6), sp + Vector2(0, -12), sp + Vector2(7, -6)]), ink)
		"shrine":
			var awake := hero != null and p.has("shrine") and hero.awakened_shrines.has(StringName(p.shrine))
			c.draw_circle(sp, r + 2.5, ink)
			c.draw_circle(sp, r, Color(0.5, 0.95, 1.0, dim) if awake else Color(0.45, 0.5, 0.52, dim))
			c.draw_colored_polygon(PackedVector2Array([sp + Vector2(0, -6), sp + Vector2(5, 0), sp + Vector2(0, 6), sp + Vector2(-5, 0)]), ink)
		"dungeon":
			var arch := PackedVector2Array([sp + Vector2(-10, 10), sp + Vector2(-10, -2)])
			for i in 9:
				var a := PI + PI * i / 8.0
				arch.append(sp + Vector2(cos(a), sin(a)) * 10.0 + Vector2(0, -2))
			arch.append(sp + Vector2(10, 10))
			var outer := arch.duplicate()
			c.draw_colored_polygon(outer, Color(0.55, 0.4, 0.75, dim))
			c.draw_polyline(arch + PackedVector2Array([arch[0]]), ink, 2.5, true)
			c.draw_rect(Rect2(sp + Vector2(-4, 0), Vector2(8, 10)), ink)
		"service", "home":
			r = 6.0 if p.kind == "service" else 4.5
			c.draw_circle(sp, r + 2.0, ink)
			c.draw_circle(sp, r, Color(0.96, 0.8, 0.46, dim) if p.kind == "service" else Color(0.8, 0.72, 0.6, dim))
		_:
			c.draw_colored_polygon(PackedVector2Array([sp + Vector2(0, -10), sp + Vector2(10, 0), sp + Vector2(0, 10), sp + Vector2(-10, 0)]), ink)
			c.draw_colored_polygon(PackedVector2Array([sp + Vector2(0, -7), sp + Vector2(7, 0), sp + Vector2(0, 7), sp + Vector2(-7, 0)]),
				Color(0.92, 0.86, 0.74, dim))
	if objective:
		var bob := sin(_t * 4.0) * 3.0
		var q := sp + Vector2(r + 8, -r - 12 + bob)
		c.draw_colored_polygon(PackedVector2Array([q + Vector2(0, -9), q + Vector2(9, 0), q + Vector2(0, 9), q + Vector2(-9, 0)]), ink)
		c.draw_colored_polygon(PackedVector2Array([q + Vector2(0, -6), q + Vector2(6, 0), q + Vector2(0, 6), q + Vector2(-6, 0)]), UITheme.GOLD)

## Dungeon colours by difficulty tier (1 Easy .. 5 Mythic): green, blue, violet, amber, red.
const TIER_COLORS := [Color(0.5, 0.5, 0.5), Color(0.42, 0.78, 0.4), Color(0.38, 0.62, 0.95), Color(0.66, 0.45, 0.9), Color(0.95, 0.6, 0.22), Color(0.95, 0.26, 0.24)]

static func tier_color(did: StringName) -> Color:
	return TIER_COLORS[clampi(DataDungeons.tier(did), 1, 5)]

## A dungeon gate: an arch filled with its difficulty colour; a raided (recovering) dungeon is greyed with a clock,
## a conquered one wears a small crown.
func _draw_gate(c: Control, sp: Vector2, did: StringName, dim: float) -> void:
	var ink := Color(0.08, 0.06, 0.04, 0.95)
	var col := tier_color(did)
	var raided := DataDungeons.recovering(hero, did)
	if raided:
		col = col.lerp(Color(0.4, 0.4, 0.42), 0.65)
	col.a = dim
	var arch := PackedVector2Array([sp + Vector2(-12, 12), sp + Vector2(-12, -2)])
	for i in 9:
		var a := PI + PI * i / 8.0
		arch.append(sp + Vector2(cos(a), sin(a)) * 12.0 + Vector2(0, -2))
	arch.append(sp + Vector2(12, 12))
	c.draw_colored_polygon(arch, col)
	c.draw_polyline(arch + PackedVector2Array([arch[0]]), ink, 3.0, true)
	c.draw_rect(Rect2(sp + Vector2(-5, 1), Vector2(10, 11)), ink)
	if raided:
		var q := sp + Vector2(12, -12)
		c.draw_circle(q, 8.0, ink)
		c.draw_circle(q, 6.0, Color(0.85, 0.85, 0.8))
		c.draw_line(q, q + Vector2(0, -4.5), ink, 1.6)
		c.draw_line(q, q + Vector2(3.5, 0), ink, 1.6)
	elif DataDungeons.boss_gone(hero, did):
		var q := sp + Vector2(12, -12)
		c.draw_colored_polygon(PackedVector2Array([q + Vector2(-6, 4), q + Vector2(-6, -3), q + Vector2(-3, 0), q + Vector2(0, -5), q + Vector2(3, 0),
			q + Vector2(6, -3), q + Vector2(6, 4)]), UITheme.GOLD)

## The hero's true position (projected from the current map) with heading; inside a building or dungeon, at its door.
func _draw_hero(c: Control, font: Font) -> void:
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p) or Game.current_map == null:
		return
	var mid := Game.current_map_id
	var ap := Vector2.ZERO
	var heading := 0.0
	if DataIsland.MAP_ORIGIN.has(mid):
		var l := Routes.hero_local()
		ap = DataIsland.to_atlas(mid, l)
		var f: Vector3 = p.global_transform.basis.z
		heading = atan2(f.x, f.z)
	else:
		var here := DataIsland.place(String(mid))
		if here.is_empty():
			for pl in DataIsland.PLACES:
				if StringName(pl.map) == mid:
					here = pl
					break
		if here.is_empty() or not DataIsland.on_view(here):
			return
		ap = DataIsland.place_atlas(here)
		heading = PI
	var sp := to_screen(ap)
	var pulse := 0.5 + 0.5 * sin(_t * 3.0)
	c.draw_circle(sp, 22.0 + pulse * 5.0, Color(0.5, 0.95, 1.0, 0.14 + 0.08 * pulse))
	var dir := Vector2(sin(heading), cos(heading))
	var tip := sp + dir * 15.0
	var lft := sp + dir.rotated(2.45) * 11.0
	var rgt := sp + dir.rotated(-2.45) * 11.0
	var back := sp - dir * 4.0
	var tri := PackedVector2Array([tip, lft, back, rgt])
	c.draw_colored_polygon(tri, Color(0.95, 1.0, 0.97))
	c.draw_polyline(tri + PackedVector2Array([tip]), Color(0.05, 0.2, 0.25), 2.5, true)
	var bf := UITheme.body_bold()
	var tw := bf.get_string_size("You", HORIZONTAL_ALIGNMENT_LEFT, -1, 21).x
	c.draw_string_outline(bf, sp + Vector2(-tw * 0.5, -24), "You", HORIZONTAL_ALIGNMENT_LEFT, -1, 21, 6, Color(0, 0, 0, 0.9))
	c.draw_string(bf, sp + Vector2(-tw * 0.5, -24), "You", HORIZONTAL_ALIGNMENT_LEFT, -1, 21, Color(0.8, 1.0, 1.0))

## bh-015: the other players, wherever they are on the island (Net.status): an arrow in their colour with their name;
## on a dungeon floor or indoors, at that place's gate. Fallen players show a red cross.
func _draw_party(c: Control) -> void:
	if not Net.is_active():
		return
	var bf := UITheme.body_bold()
	for pid in Net.status:
		if int(pid) == Net.my_id():
			continue
		var st: Dictionary = Net.status[pid]
		var mid := StringName(st.get("map", ""))
		var ap := Vector2.INF
		var heading := PI
		if DataIsland.MAP_ORIGIN.has(mid):
			var pos: Vector3 = st.get("pos", Vector3.ZERO)
			ap = DataIsland.to_atlas(mid, Vector2(pos.x, pos.z))
			heading = float(st.get("yaw", 0.0))
		else:
			var here := DataIsland.place(String(mid))
			if here.is_empty():
				for pl in DataIsland.PLACES:
					if StringName(pl.map) == mid:
						here = pl
						break
			if here.is_empty() or not DataIsland.on_view(here):
				continue
			ap = DataIsland.place_atlas(here)
		var sp := to_screen(ap)
		var col := Net.player_color(int(pid))
		var alive := bool(st.get("alive", true))
		var pulse := 0.5 + 0.5 * sin(_t * 3.0 + float(pid))
		c.draw_circle(sp, 15.0 + pulse * 4.0, Color(col, 0.16))
		if alive:
			var dir := Vector2(sin(heading), cos(heading))
			var tri := PackedVector2Array([sp + dir * 12.0, sp + dir.rotated(2.45) * 9.0, sp - dir * 3.0, sp + dir.rotated(-2.45) * 9.0])
			c.draw_colored_polygon(tri, col)
			c.draw_polyline(tri + PackedVector2Array([tri[0]]), Color(0.05, 0.03, 0.02), 2.0, true)
		else:
			c.draw_circle(sp, 9.0, col)
			c.draw_circle(sp, 7.0, Color(0.08, 0.05, 0.05))
			c.draw_line(sp + Vector2(-4, -4), sp + Vector2(4, 4), Color(1.0, 0.35, 0.3), 2.2, true)
			c.draw_line(sp + Vector2(4, -4), sp + Vector2(-4, 4), Color(1.0, 0.35, 0.3), 2.2, true)
		var nm := String(Net.peers.get(pid, {}).get("name", "Ally")) + ("" if alive else " (fallen)")
		var tw := bf.get_string_size(nm, HORIZONTAL_ALIGNMENT_LEFT, -1, 18).x
		c.draw_string_outline(bf, sp + Vector2(-tw * 0.5, -18), nm, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, 6, Color(0, 0, 0, 0.9))
		c.draw_string(bf, sp + Vector2(-tw * 0.5, -18), nm, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, col.lightened(0.3))

func _draw_compass_and_scale(c: Control, font: Font) -> void:
	var o := Vector2(size.x - 56, 64)
	c.draw_circle(o, 30.0, Color(0.05, 0.04, 0.03, 0.55))
	c.draw_arc(o, 30.0, 0.0, TAU, 32, UITheme.BRONZE, 2.0, true)
	c.draw_colored_polygon(PackedVector2Array([o + Vector2(0, -26), o + Vector2(7, 0), o + Vector2(-7, 0)]), UITheme.GOLD)
	c.draw_colored_polygon(PackedVector2Array([o + Vector2(0, 26), o + Vector2(7, 0), o + Vector2(-7, 0)]), UITheme.BRONZE_DIM)
	c.draw_string(font, o + Vector2(-7, -34), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, UITheme.PARCHMENT)
	# a true scale bar for the charted surface (every surface map shares one scale)
	var metres := 100.0 if zoom_fit_factor() < 2.5 else 25.0
	var w := metres / DataIsland.PX_M * zoom
	var b := Vector2(size.x - 40 - w, size.y - 34)
	c.draw_rect(Rect2(b + Vector2(-10, -26), Vector2(w + 20, 40)), Color(0.05, 0.04, 0.03, 0.6))
	c.draw_line(b, b + Vector2(w, 0), UITheme.PARCHMENT, 3.0)
	c.draw_line(b + Vector2(0, -6), b + Vector2(0, 6), UITheme.PARCHMENT, 2.0)
	c.draw_line(b + Vector2(w, -6), b + Vector2(w, 6), UITheme.PARCHMENT, 2.0)
	c.draw_string(font, b + Vector2(0, -9), "%d m" % int(metres), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UITheme.PARCHMENT)

const UNDERGROUND := [["catacombs", "Ancient Catacombs", ""], ["temple", "Forgotten Temple", "catacombs_ritual_seen"],
	["throne", "The Hollow Throne", "temple_seal_broken"]]
const UG_COLS := 3
const UG_ROW := 70.0

## Every dungeon (easiest first), then the temple sequence: [place id, name, lock flag or "", dungeon id or &""].
func _underground_rows() -> Array:
	var out := []
	for did in DataDungeons.order():
		out.append([String(did), String(DataDungeons.get_def(did).name), "", did])
	for u in UNDERGROUND:
		out.append([u[0], u[1], u[2], &""])
	return out

func _underground_box() -> Rect2:
	var rows := ceili(float(_underground_rows().size()) / UG_COLS)
	var w := minf(size.x - 40.0, 1320.0)
	return Rect2(Vector2((size.x - w) * 0.5, 76), Vector2(w, 104 + rows * UG_ROW))

## [place id, anchor point of the row's icon, row width] per row.
func _underground_slots() -> Array:
	var box := _underground_box()
	var rows := _underground_rows()
	var per := ceili(float(rows.size()) / UG_COLS)
	var cw := (box.size.x - 40.0) / UG_COLS
	var out := []
	for i in rows.size():
		var col := i / per
		var row := i % per
		out.append([rows[i][0], Vector2(box.position.x + 20 + col * cw + 22, box.position.y + 124 + row * UG_ROW), cw - 10.0])
	return out

## Underground: every dungeon beneath the island with its difficulty, levels, floors and raid state; then the temple
## sequence under the Ruined Forest with its locks. Clicking a row selects that dungeon.
func _draw_underground(c: Control, font: Font, body: Font) -> void:
	var box := _underground_box()
	c.draw_rect(box, Color(0.05, 0.04, 0.05, 0.93))
	c.draw_rect(box, UITheme.BRONZE_DIM, false, 2.0)
	c.draw_string(font, box.position + Vector2(24, 44), "Dungeons beneath Salmonan", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, UITheme.GOLD)
	c.draw_string(body, box.position + Vector2(24, 76), "Colour and stars show difficulty. A raided dungeon recovers in 30 min to 2 h; its lord never returns.",
		HORIZONTAL_ALIGNMENT_LEFT, box.size.x - 48, 18, UITheme.TEXT_DIM)
	var rows := _underground_rows()
	var slots := _underground_slots()
	for i in rows.size():
		var sp: Vector2 = slots[i][1]
		var cw: float = slots[i][2]
		var did: StringName = rows[i][3]
		var flag: String = rows[i][2]
		var open: bool = flag == "" or (hero != null and bool(hero.world_flags.get(StringName(flag), false)))
		var sel: bool = rows[i][0] == selected or rows[i][0] == hover
		if sel:
			c.draw_rect(Rect2(sp + Vector2(-20, -28), Vector2(cw, UG_ROW - 6)), Color(0.9, 0.75, 0.4, 0.12))
			c.draw_rect(Rect2(sp + Vector2(-20, -28), Vector2(cw, UG_ROW - 6)), UITheme.GOLD, false, 1.5)
		if did != &"":
			_draw_gate(c, sp + Vector2(0, -4), did, 1.0)
			var lr := DataDungeons.level_range(did)
			c.draw_string(font, sp + Vector2(24, -6), String(rows[i][1]), HORIZONTAL_ALIGNMENT_LEFT, cw - 60, 21, UITheme.PARCHMENT)
			var line := "%s  Lv %d–%d · %s · %d floors" % [DataDungeons.tier_stars(did), lr.x, lr.y, DataDungeons.tier_name(did), DungeonGrowth.total(Game.hero, did)]
			c.draw_string(body, sp + Vector2(24, 15), line, HORIZONTAL_ALIGNMENT_LEFT, cw - 60, 16, tier_color(did).lightened(0.35))
			var raided := DataDungeons.recovering(hero, did)
			c.draw_string(body, sp + Vector2(24, 33), DataDungeons.status_short(hero, did), HORIZONTAL_ALIGNMENT_LEFT, cw - 60, 15,
				Color(0.95, 0.7, 0.45) if raided else UITheme.TEXT_DIM)
		else:
			c.draw_circle(sp, 12.0, Color(0.55, 0.4, 0.75) if open else Color(0.3, 0.28, 0.3))
			c.draw_arc(sp, 12.0, 0.0, TAU, 24, Color(0.08, 0.06, 0.04), 3.0)
			c.draw_string(font, sp + Vector2(24, -6), String(rows[i][1]), HORIZONTAL_ALIGNMENT_LEFT, cw - 60, 21, UITheme.PARCHMENT if open else UITheme.TEXT_DIM)
			var pl := DataIsland.place(String(rows[i][0]))
			c.draw_string(body, sp + Vector2(24, 15), "%s · the temple sequence" % String(pl.get("levels", "")), HORIZONTAL_ALIGNMENT_LEFT, cw - 60, 16, UITheme.TEXT_DIM)
			if not open:
				c.draw_string(body, sp + Vector2(24, 33), "Locked", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, UITheme.BAD)
