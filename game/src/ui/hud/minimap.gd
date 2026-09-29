class_name MiniMap
extends Control
## Circular minimap (bh-015 overhaul): an orthographic top-down render of the live world under the painted frame, with
## a vector icon layer drawn every frame so everything glides instead of stepping.
##
##   Zoom       three levels (ZOOMS), eased; mouse wheel over the map, the - / + buttons on the frame, or the Minimap
##              Zoom keys. Kept in Settings.minimap_zoom.
##   Quests     the current objective (QuestTarget): a gold marker on the spot, a gold trail along this map's roads
##              toward it, and a gold chevron on the rim with the distance when it is off the map.
##   Party      other players are arrows in their colour, facing where they face; fallen ones show a revive cross and
##              low ones a red pulse; off the map they sit on the rim with their name and distance. Their Tempos
##              are small diamonds in their colour. Pings ripple on the map (right-click the minimap to ping a spot).
##   Places     waypoints (dark until awakened), dungeon gates, stairs, doors, exits to other districts, the Town
##              Portal, bonfires, crafting stations, unopened chests, herbs, uncleared camps; townsfolk by trade
##              (merchant, smith, inn, healer, guild, Tempo-Caller, heroes). Hover any icon for its name.
##   Foes       red, larger and ringed when they are after you; elites gold, champions crowned, bosses a skull
##              that stays on the rim.
##   Route      a tracked route (Routes) as a flowing cyan line with a chevron at the rim.
##
## The top-down render covers the widest zoom plus MARGIN metres on every side; the disc slides across it as the hero
## walks (view_offset) and the world is rendered again only near its edge, when the map changes, or every REFRESH s
## (doors, bridges) — never every frame (bh-014: a full second render per frame used to cost ~6 ms).

const SHADER := """
shader_type canvas_item;
uniform sampler2D mask_tex : filter_linear;
uniform vec2 view_offset = vec2(0.0);
uniform float view_scale = 1.0;
uniform float fade = 1.0;
void fragment() {
	vec3 c = texture(TEXTURE, (UV - 0.5) * view_scale + 0.5 + view_offset).rgb;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, 0.82) * 1.16 + vec3(0.028, 0.024, 0.016);
	float r = length(UV - 0.5) * 2.0;
	c *= mix(1.0, 0.52, smoothstep(0.55, 1.0, r));
	c = mix(vec3(0.03, 0.035, 0.045), c, fade);
	COLOR = vec4(c, texture(mask_tex, UV).a);
}
"""
const ZOOMS := [16.0, 26.0, 42.0]    # metres from the centre to the rim
const MASK_R := 0.7625               # radius of minimap_mask.png's disc, as a fraction of the texture's half-width
const DISC := 0.376                  # visible disc radius / diameter: fills the frame's opening (its inner edge is 0.37)
const MARGIN := 12.0
const REFRESH := 4.0
const LITE_HZ := 12.0

const C_QUEST := Color(1.0, 0.8, 0.28)
const C_ROUTE := Color(0.5, 0.95, 1.0)
const C_FOE := Color(0.95, 0.25, 0.2)
const C_WAY := Color(0.5, 0.95, 1.0)
const C_DOOR := Color(1.0, 0.74, 0.45)
const C_DIM := Color(0.62, 0.6, 0.56)

var radius_m := 26.0                # current (eased) view radius
var diameter := 200.0
var _disc_r := 75.0                 # visible map radius in px (the markers layer is 2 x this, centred)
var _zoom_i := 1
var _vp: SubViewport
var _cam: Camera3D
var _view: TextureRect
var _markers: Control
var _frame: TextureRect
var _map_label: Label
var _sub_label: Label
var _btn_out: Button
var _btn_in: Button
var _update_t := 0.0
var _marker_t := 0.0
var _view_mat: ShaderMaterial
var _rendered_world: World3D
var _render_r := 54.0
var _center := Vector3.ZERO         # the hero, the middle of the disc
var _fade := 1.0
var _time := 0.0
var _quest := QuestTarget.new()
var _pois: Array = []               # static places on this map: {node, kind, text, col, rim}
var _poi_t := 0.0
var _sub_t := 0.0
var _hits: Array = []               # [screen pos, text] of icons drawn this frame (hover names)
var _hover := Vector2(-1, -1)
var _font: Font

func _init(p_diameter := 200.0) -> void:
	diameter = p_diameter
	custom_minimum_size = Vector2(diameter, diameter + 44.0)
	mouse_filter = Control.MOUSE_FILTER_STOP
	tooltip_text = ""

func _ready() -> void:
	_font = UITheme.body_bold()
	_zoom_i = clampi(Settings.minimap_zoom, 0, ZOOMS.size() - 1)
	radius_m = ZOOMS[_zoom_i]
	_render_r = float(ZOOMS[ZOOMS.size() - 1]) + MARGIN
	_disc_r = diameter * DISC
	var inner := _disc_r * 2.0 / MASK_R
	_vp = SubViewport.new()
	# ~6.5 px per metre across the whole render on a PC, ~4 in efficiency mode
	var px := int(ceil(_render_r * 2.0 * (4.0 if Perf.lite else 6.5) / 16.0)) * 16
	_vp.size = Vector2i(px, px)
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	_vp.msaa_3d = Viewport.MSAA_DISABLED
	_vp.positional_shadow_atlas_size = 0
	add_child(_vp)
	_cam = Camera3D.new()
	_cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	_cam.size = _render_r * 2.0
	_cam.far = 200.0
	_cam.rotation_degrees = Vector3(-90, 0, 0)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.03, 0.03, 0.04)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.85, 0.8, 0.72)
	env.ambient_light_energy = 1.6
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	_cam.environment = env
	_cam.cull_mask = 1   # world geometry only (no characters, and no lights: they live on Perf.LIGHT_LAYER)
	_vp.add_child(_cam)
	_view = TextureRect.new()
	_view.texture = _vp.get_texture()
	_view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_view.size = Vector2(inner, inner)
	_view.position = Vector2((diameter - inner) * 0.5, (diameter - inner) * 0.5)
	_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = SHADER
	mat.shader = sh
	mat.set_shader_parameter("mask_tex", UIArt.tex("hud/minimap_mask.png"))
	_view.material = mat
	_view_mat = mat
	_view.modulate = Color(0.8, 0.78, 0.74)
	add_child(_view)
	_markers = Control.new()
	_markers.position = Vector2.ONE * (diameter * 0.5 - _disc_r)
	_markers.size = Vector2.ONE * _disc_r * 2.0
	_markers.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_markers.draw.connect(_draw_markers)
	add_child(_markers)
	_frame = TextureRect.new()
	_frame.texture = UIArt.tex("hud/minimap_frame.png")
	_frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_frame.size = Vector2(diameter, diameter)
	_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_frame)
	var over := Control.new()          # compass letters, rim chevrons and the hover name sit above the frame
	over.size = Vector2(diameter, diameter)
	over.mouse_filter = Control.MOUSE_FILTER_IGNORE
	over.draw.connect(_draw_over)
	add_child(over)
	_markers.set_meta(&"over", over)
	_btn_out = _zoom_button("-", Vector2(diameter * 0.06, diameter * 0.8), func() -> void: set_zoom(_zoom_i + 1))
	_btn_in = _zoom_button("+", Vector2(diameter * 0.94 - 26.0, diameter * 0.8), func() -> void: set_zoom(_zoom_i - 1))
	_map_label = UITheme.label("", 16, UITheme.PARCHMENT, UITheme.title_font())
	_map_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_map_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_map_label.add_theme_constant_override("outline_size", 5)
	_map_label.position = Vector2(-60, diameter - 6)
	_map_label.size = Vector2(diameter + 80, 22)
	_map_label.clip_text = true
	_map_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_map_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_map_label)
	_sub_label = UITheme.label("", 14, UITheme.TEXT_DIM, UITheme.body_font())
	_sub_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_sub_label.add_theme_constant_override("outline_size", 4)
	_sub_label.position = Vector2(-60, diameter + 14)
	_sub_label.size = Vector2(diameter + 80, 20)
	_sub_label.clip_text = true
	_sub_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_sub_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_sub_label)
	Events.map_loaded.connect(func(_m: StringName) -> void:
		_quest.invalidate()
		_poi_t = 0.0
		_sub_t = 0.0)
	Events.world_flag_set.connect(func(_f: StringName, _v: Variant) -> void: _quest.invalidate())
	Settings.changed.connect(func() -> void: _zoom_i = clampi(Settings.minimap_zoom, 0, ZOOMS.size() - 1))

func _zoom_button(txt: String, pos: Vector2, cb: Callable) -> Button:
	var b := Button.new()
	var k := 34.0 if Settings.touch_mode else 26.0     # a finger needs a bigger target
	b.text = txt
	b.focus_mode = Control.FOCUS_NONE
	b.position = pos - Vector2(k - 26.0, 0) * (0.0 if txt == "-" else 1.0)
	b.size = Vector2(k, k)
	b.custom_minimum_size = Vector2(k, k)
	b.add_theme_font_size_override("font_size", 18)
	b.add_theme_font_override("font", UITheme.body_bold())
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = {"normal": Color(0.06, 0.07, 0.08, 0.92), "hover": Color(0.12, 0.2, 0.22, 0.95), "pressed": Color(0.2, 0.32, 0.34, 1.0),
			"disabled": Color(0.05, 0.05, 0.06, 0.6), "focus": Color(0, 0, 0, 0)}[st]
		sb.border_color = UITheme.GOLD.darkened(0.15) if st != "disabled" else Color(0.4, 0.36, 0.3, 0.6)
		sb.content_margin_left = 0
		sb.content_margin_right = 0
		sb.content_margin_top = 0
		sb.content_margin_bottom = 0
		sb.set_border_width_all(2)
		sb.set_corner_radius_all(17)
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_color_override("font_color", UITheme.PARCHMENT)
	b.add_theme_color_override("font_hover_color", Color(0.7, 1.0, 1.0))
	b.add_theme_color_override("font_disabled_color", Color(0.5, 0.47, 0.42, 0.7))
	b.pressed.connect(cb)
	b.tooltip_text = "Zoom out (%s)" % Settings.binding_text(&"minimap_zoom_out") if txt == "-" else "Zoom in (%s)" % Settings.binding_text(&"minimap_zoom_in")
	add_child(b)
	return b

## 0 = closest, ZOOMS.size() - 1 = widest. Remembered in Settings.
func set_zoom(i: int) -> void:
	i = clampi(i, 0, ZOOMS.size() - 1)
	if i == _zoom_i:
		return
	_zoom_i = i
	Settings.minimap_zoom = i
	Settings.save_file()

func zoom_index() -> int:
	return _zoom_i

## Only the disc (and the zoom buttons) take the mouse: the corners of the box stay click-through to the world.
func _has_point(point: Vector2) -> bool:
	return point.distance_to(Vector2(diameter, diameter) * 0.5) <= _disc_r

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_hover = event.position - _markers.position
	elif event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_WHEEL_UP:
				set_zoom(_zoom_i - 1)
			MOUSE_BUTTON_WHEEL_DOWN:
				set_zoom(_zoom_i + 1)
			MOUSE_BUTTON_LEFT:
				# touch play: the touch layer's own minimap button opens the map (a tap would open it twice)
				if not Settings.touch_mode and Game.ui_root and Game.ui_root.has_method(&"open"):
					Game.ui_root.open(&"world_map")
			MOUSE_BUTTON_RIGHT:
				# mark this spot for the party (offline: just for you)
				var w := _to_world(event.position - _markers.position)
				var p := Game.player as Node3D
				if p and is_instance_valid(p):
					Net.ping(CombatQuery.ground_at(p.get_world_3d(), w + Vector3.UP * 4.0))
		accept_event()

func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_EXIT:
		_hover = Vector2(-1, -1)

func _unhandled_input(event: InputEvent) -> void:
	if not visible or not (event is InputEventKey) or not event.pressed or event.echo:
		return
	if event.is_action(&"minimap_zoom_in"):
		set_zoom(_zoom_i - 1)
		get_viewport().set_input_as_handled()
	elif event.is_action(&"minimap_zoom_out"):
		set_zoom(_zoom_i + 1)
		get_viewport().set_input_as_handled()

func _process(delta: float) -> void:
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p) or not p.is_inside_tree() or not Settings.show_minimap:
		visible = Settings.show_minimap and p != null
		return
	visible = true
	_time += delta
	var world := p.get_world_3d()
	if _vp.world_3d != world:
		_vp.world_3d = world
	var def: MapDef = Game.current_map.def if Game.current_map and is_instance_valid(Game.current_map) else null
	_map_label.text = def.display_name if def else ""
	radius_m = lerpf(radius_m, float(ZOOMS[_zoom_i]), 1.0 - exp(-delta * 9.0))
	_update_t -= delta
	var hero := p.global_position
	var off := Vector2(hero.x - _cam.global_position.x, hero.z - _cam.global_position.z)
	# re-render when the disc is about to slide off the render, when the map changed, and now and then for doors
	var slack := _render_r - radius_m / MASK_R - 1.0
	var new_world := _rendered_world != _vp.world_3d
	var due := new_world or absf(off.x) > slack or absf(off.y) > slack \
		or _update_t <= 0.0 and off.length() > 0.5 or _update_t <= -REFRESH
	if due:
		_update_t = REFRESH * (2.0 if Perf.lite else 1.0)
		_rendered_world = _vp.world_3d
		_cam.global_position = hero + Vector3(0, 60, 0)
		_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		off = Vector2.ZERO
		if new_world:
			_fade = 0.0                 # a new map fades in instead of flashing the old one
	_fade = move_toward(_fade, 1.0, delta * 3.0)
	_center = hero
	_view_mat.set_shader_parameter("view_offset", off / (_render_r * 2.0))
	_view_mat.set_shader_parameter("view_scale", radius_m / MASK_R / _render_r)
	_view_mat.set_shader_parameter("fade", _fade)
	_quest.update(delta)
	_poi_t -= delta
	if _poi_t <= 0.0:
		_poi_t = 1.0
		_collect_pois()
	_sub_t -= delta
	if _sub_t <= 0.0:
		_sub_t = 0.5
		_sub_label.text = _sub_text(def)
	_marker_t -= delta
	if _marker_t <= 0.0 or not Perf.lite:
		_marker_t = 1.0 / LITE_HZ
		_markers.queue_redraw()
		(_markers.get_meta(&"over") as Control).queue_redraw()
	_btn_in.disabled = _zoom_i == 0
	_btn_out.disabled = _zoom_i == ZOOMS.size() - 1

## Under the map name: the nearest named place (within 24 m) and the zoom, or the objective's step.
func _sub_text(def: MapDef) -> String:
	if def == null:
		return ""
	var pos := Routes.hero_local()
	var best := ""
	var bd := 24.0
	for pl in DataIsland.all_places():
		if StringName(pl.map) != Game.current_map_id or not pl.has("pos") or pl.kind == "junction":
			continue
		if pl.get("name", "") == def.display_name or not Routes.is_known(Game.hero, pl):
			continue
		var d := pos.distance_to(pl.pos)
		if d < bd:
			bd = d
			best = String(pl.name)
	var zoom := "%d m" % int(ZOOMS[_zoom_i])
	return "%s  ·  %s" % [best, zoom] if best != "" else zoom

# ---- Static places ------------------------------------------------------------------------------------------------

func _collect_pois() -> void:
	_pois = []
	var map := Game.current_map
	if map == null or not is_instance_valid(map) or not map.is_inside_tree():
		return
	var tree := get_tree()
	for t in tree.get_nodes_in_group(&"teleporter"):
		if not map.is_ancestor_of(t):
			continue
		var tp := t as Teleporter
		if tp == null:
			continue
		if tp.dungeon_gate != &"":
			_pois.append({"node": tp, "kind": "gate", "text": "%s · %s" % [DataDungeons.get_def(tp.dungeon_gate).get("name", "Dungeon gate"), DataDungeons.recommended_levels(tp.dungeon_gate)],
				"col": tp.rune_tint.lightened(0.2), "rim": false})
		elif String(tp.destination_map).begins_with("dg_") or tp.has_meta(&"dungeon_up"):
			_pois.append({"node": tp, "kind": "stairs", "text": "Stairs", "col": tp.rune_tint.lightened(0.2), "rim": false})
		elif DataDungeons.map_recommendation(tp.destination_map) != "":
			_pois.append({"node": tp, "kind": "gate", "text": "%s · %s" % [tp.destination_name, DataDungeons.map_recommendation(tp.destination_map)], "col": tp.rune_tint.lightened(0.2), "rim": false})
		else:
			var lit := not tp.is_locked() and (not tp.is_network() or Game.hero == null or Game.hero.awakened_shrines.has(tp.teleporter_id))
			var nm := String(DataIsland.NETWORK.get(tp.teleporter_id, {}).get("name", "Waypoint")) if tp.is_network() else "Waypoint"
			_pois.append({"node": tp, "kind": "waypoint", "text": nm + ("" if lit else " (dormant)"), "col": C_WAY if lit else C_DIM, "rim": false})
	for d in tree.get_nodes_in_group(&"door"):
		if map.is_ancestor_of(d):
			_pois.append({"node": d, "kind": "door", "text": String(d.label) if d.label != "" else "Door", "col": C_DOOR, "rim": false})
	for e in tree.get_nodes_in_group(&"map_exit"):
		if map.is_ancestor_of(e):
			var open: bool = (e as MapExit).is_open()
			_pois.append({"node": e, "kind": "exit", "text": ("To %s" % e.label) + ("" if open else " (shut)"),
				"col": Color(0.85, 0.9, 1.0) if open else C_DIM, "rim": open})
	for n in tree.get_nodes_in_group(&"checkpoint"):
		if map.is_ancestor_of(n):
			_pois.append({"node": n, "kind": "fire", "text": String(n.get("camp_name")) + " bonfire", "col": Color(1.0, 0.62, 0.25), "rim": false})
	for n in tree.get_nodes_in_group(&"crafting_station"):
		if map.is_ancestor_of(n):
			_pois.append({"node": n, "kind": "craft", "text": String(n.label) if n.label != "" else "Workbench", "col": Color(1.0, 0.7, 0.4), "rim": false})
	# bh-019: the Hero's Vault and the practice dummy
	for n in tree.get_nodes_in_group(&"vault_point"):
		if map.is_ancestor_of(n):
			_pois.append({"node": n, "kind": "chest", "text": "The Hero's Vault", "col": Color(1.0, 0.86, 0.5), "rim": true})
	for n in tree.get_nodes_in_group(&"practice_target"):
		if map.is_ancestor_of(n):
			_pois.append({"node": n, "kind": "smith", "text": "Practice Dummy", "col": Color(0.95, 0.62, 0.42), "rim": false})
	for n in tree.get_nodes_in_group(&"treasure_chest"):
		if map.is_ancestor_of(n) and n.has_method(&"is_ready") and n.is_ready():
			_pois.append({"node": n, "kind": "chest", "text": "Treasure chest", "col": UITheme.GOLD, "rim": false})
	for n in tree.get_nodes_in_group(&"gather_node"):
		if map.is_ancestor_of(n) and n.has_method(&"is_ready") and n.is_ready():
			_pois.append({"node": n, "kind": "herb", "text": n.interact_text().trim_prefix("Gather "), "col": Color(0.5, 0.95, 0.5), "rim": false})
	for n in tree.get_nodes_in_group(&"town_portal"):
		if n is Node3D and n.is_inside_tree() and n.get_world_3d() == map.get_world_3d():
			_pois.append({"node": n, "kind": "portal", "text": "Town Portal", "col": Color(0.45, 0.7, 1.0), "rim": true})
	# uncleared camps
	var sp := Spawner.current()
	if sp:
		for zone in sp.camps:
			var alive := (sp.camps[zone] as Array).filter(func(x): return is_instance_valid(x) and x.alive)
			if alive.is_empty():
				continue
			var c := Vector3.ZERO
			for x in alive:
				c += (x as Node3D).global_position
			c /= float(alive.size())
			_pois.append({"node": null, "pos": c, "kind": "camp", "text": "Camp: %s (%d left)" % [String(zone).replace("_", " ").capitalize(), alive.size()],
				"col": C_FOE, "rim": false})
	# townsfolk by trade
	var quest_npc := StringName(Objectives.current(Game.hero).get("npc", &"")) if Game.hero else &""
	for n in tree.get_nodes_in_group(&"npc"):
		if not map.is_ancestor_of(n) or not ("def" in n) or n.def == null:
			continue
		var r := _npc_role(n.def)
		_pois.append({"node": n, "kind": r[0], "text": "%s — %s" % [n.def.display_name, n.def.title] if n.def.title != "" else n.def.display_name,
			"col": r[1], "rim": false, "quest": n.def.id == quest_npc})

## [icon kind, colour] for a townsperson.
static func _npc_role(d: NpcDef) -> Array:
	var t := d.title.to_lower()
	if d.services.has(&"lape_trade"):
		return ["shop", Color(0.78, 0.62, 1.0)]
	if d.services.has(&"socketing"):
		return ["shop", Color(0.62, 0.86, 1.0)]
	if d.services.has(&"tempo_hire"):
		return ["spirit", DataTempos.SPIRIT_TINT]
	if d.services.has(&"rest") or t.contains("innkeeper"):
		return ["inn", Color(1.0, 0.78, 0.5)]
	if d.services.has(&"mystic_heal") or t.contains("healer"):
		return ["heal", Color(0.55, 1.0, 0.7)]
	if d.services.has(&"join_swordfin") or d.services.has(&"join_lantern") or t.contains("registrar") or t.contains("master of"):
		return ["guild", Color(0.75, 0.85, 1.0)]
	if t.contains("smith") or String(d.shop).contains("forge") or String(d.shop).contains("arms"):
		return ["smith", Color(1.0, 0.6, 0.35)]
	if d.shop != &"":
		return ["shop", UITheme.GOLD]
	if d.is_hero():
		return ["hero", Color(0.8, 0.82, 0.9)]
	return ["person", UITheme.PARCHMENT]

# ---- Drawing ------------------------------------------------------------------------------------------------------

func _to_map(world: Vector3) -> Vector2:
	var d := Vector2(world.x - _center.x, world.z - _center.z) / (radius_m * 2.0)
	return _markers.size * 0.5 + d * _markers.size

func _to_world(q: Vector2) -> Vector3:
	var d := (q - _markers.size * 0.5) / _markers.size * (radius_m * 2.0)
	return Vector3(_center.x + d.x, _center.y, _center.z + d.y)

func _lim() -> float:
	return _markers.size.x * 0.5 * 0.93

func _draw_markers() -> void:
	_hits = []
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p) or not is_inside_tree():
		return
	var c := _markers
	var half := c.size * 0.5
	var lim := _lim()
	var tree := get_tree()
	var z := clampf(26.0 / radius_m, 0.7, 1.25)         # icons shrink a little when zoomed out
	# camps first (the ground under everything)
	for poi in _pois:
		if poi.kind == "camp":
			var q := _to_map(poi.pos)
			if (q - half).length() < lim + 10.0:
				var rr := 7.0 * z
				c.draw_circle(q, rr + 3.0, Color(C_FOE, 0.12))
				c.draw_arc(q, rr + 3.0, 0, TAU, 20, Color(C_FOE, 0.45), 1.2, true)
				_swords(q, 4.5 * z, Color(1.0, 0.55, 0.5))
				_hit(q, poi.text, lim)
	# the quest trail, then a tracked route over it
	_draw_trail(_quest.trail_world(), C_QUEST, lim, 0.85)
	_draw_route(lim)
	# places
	for poi in _pois:
		if poi.kind == "camp":
			continue
		var n: Node3D = poi.node
		if n == null or not is_instance_valid(n) or not n.is_inside_tree():
			continue
		var q := _to_map(n.global_position)
		var inside := (q - half).length() <= lim
		if not inside and not poi.rim:
			continue
		if not inside:
			continue                   # rim-pinned places draw in _draw_over
		_place_icon(poi.kind, q, poi.col, z)
		if poi.get("quest", false):
			_quest_badge(q + Vector2(0, -9.0 * z), z)
		_hit(q, poi.text, lim)
	# loot on the ground (the rarer, the bigger)
	for l in tree.get_nodes_in_group(&"loot"):
		if not (l is Node3D) or not l.is_inside_tree():
			continue
		var q := _to_map(l.global_position)
		if (q - half).length() > lim:
			continue
		var col := Color(0.9, 0.85, 0.5)
		var rar := 1
		if "item" in l and l.item != null:
			col = l.item.color()
			rar = l.item.rarity
		elif "gold" in l:
			col = UITheme.GOLD
		var s := (2.2 + minf(rar, 8) * 0.3) * z
		_diamond(q, s, col, Color(0, 0, 0, 0.75))
		if rar >= BH.Rarity.MYTHICAL:
			c.draw_arc(q, s + 2.5 + 1.5 * sin(_time * 5.0), 0, TAU, 14, Color(col, 0.7), 1.2, true)
	# monsters
	for e in tree.get_nodes_in_group(&"enemy"):
		if not e.alive or not (e is Node3D):
			continue
		var q := _to_map(e.global_position)
		var inside := (q - half).length() <= lim
		if e.is_boss:
			if inside:
				var pr := 8.5 * z + 1.5 * sin(_time * 4.0)
				c.draw_circle(q, pr + 3.0, Color(1.0, 0.1, 0.05, 0.25))
				_skull(q, 7.0 * z, Color(1.0, 0.25, 0.18))
				_hit(q, String(e.display_name) if "display_name" in e else "Boss", lim)
			continue
		if not inside:
			continue
		var hunting: bool = e.target != null and is_instance_valid(e.target) and (e.target == p or e.target.is_in_group(&"tempo"))
		if not e.miniboss.is_empty():
			_dot(q, 4.6 * z, Color(1.0, 0.55, 0.2))
			_crown(q + Vector2(0, -6.5 * z), 4.0 * z, UITheme.GOLD)
			_hit(q, "Champion: %s" % String(e.miniboss.get("name", e.display_name)), lim)
		elif e.is_elite:
			_dot(q, 3.8 * z, UITheme.GOLD)
			c.draw_arc(q, 5.6 * z, 0, TAU, 14, Color(UITheme.GOLD, 0.8), 1.2, true)
		else:
			_dot(q, (3.1 if hunting else 2.5) * z, C_FOE if hunting else Color(0.82, 0.24, 0.2))
		if hunting:
			c.draw_arc(q, (4.8 + sin(_time * 7.0)) * z, 0, TAU, 14, Color(1.0, 0.35, 0.3, 0.55), 1.0, true)
	# your Tempos
	for t in tree.get_nodes_in_group(&"tempo"):
		if t.alive and t is Node3D:
			var q := _to_map(t.global_position)
			if (q - half).length() <= lim:
				_diamond(q, 3.6 * z, DataTempos.SPIRIT_TINT, Color(0, 0, 0, 0.8))
				_hit(q, String(t.data.tempo_name) if "data" in t and t.data else "Tempo", lim)
	# other players' Tempos, then the players themselves
	for a in tree.get_nodes_in_group(&"net_ally"):
		if a.is_in_group(&"net_hero") or not a.alive:
			continue
		var q := _to_map(a.global_position)
		if (q - half).length() <= lim:
			_diamond(q, 3.2 * z, Net.player_color(a.owner_peer).lightened(0.2), Color(0, 0, 0, 0.8))
			_hit(q, String(a.display_name), lim)
	for h in tree.get_nodes_in_group(&"net_hero"):
		var q := _to_map(h.global_position)
		if (q - half).length() > lim:
			continue                       # on the rim: _draw_over
		var col := Net.player_color(h.owner_peer)
		if not h.alive:
			_revive_cross(q, 6.0 * z, col)
			_hit(q, "%s — fallen (stand beside them and Interact to revive)" % h.display_name, lim)
			continue
		var frac: float = float(h.hp) / maxf(1.0, float(h.get("_max_hp")))
		if frac < 0.35:
			c.draw_circle(q, (9.0 + 2.0 * sin(_time * 8.0)) * z, Color(1.0, 0.15, 0.1, 0.3))
		_markers.draw_arc(q, 9.5 * z, 0, TAU, 20, Color(col, 0.55), 1.4, true)
		_arrow(q, _yaw_of(h), 7.5 * z, col, Color.WHITE)
		_hit(q, "%s (%d%% HP)" % [h.display_name, int(round(frac * 100.0))], lim)
		# their name beside the arrow, so a party of four reads at a glance
		var tag := String(h.display_name).left(10)
		var tw := _font.get_string_size(tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
		var tp := q + Vector2(-tw * 0.5, 17.0 * z)
		_markers.draw_string_outline(_font, tp, tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, 4, Color(0, 0, 0, 0.9))
		_markers.draw_string(_font, tp, tag, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, col.lightened(0.3))
	# pings
	for g in tree.get_nodes_in_group(&"ping"):
		if not (g is PingMarker) or not g.is_inside_tree():
			continue
		var q := _to_map(g.global_position)
		if (q - half).length() > lim:
			continue
		var pc: Color = g.color()
		var a0: float = 1.0 - g.age()
		for k in 2:
			var ph := fmod(_time * 1.3 + k * 0.5, 1.0)
			c.draw_arc(q, 3.0 + ph * 14.0, 0, TAU, 20, Color(pc, (1.0 - ph) * a0), 2.0, true)
		_diamond(q, 4.0, pc, Color(0, 0, 0, 0.8 * a0))
		_hit(q, "Ping: %s" % g.who, lim)
	# the quest spot
	if _quest.has:
		var q := _to_map(_quest.world)
		if (q - half).length() <= lim:
			var pr2 := 7.0 + 2.5 * sin(_time * 3.5)
			c.draw_circle(q, pr2 + 4.0, Color(C_QUEST, 0.18))
			c.draw_arc(q, pr2 + 4.0, 0, TAU, 24, Color(C_QUEST, 0.7), 1.5, true)
			if _quest.final:
				_quest_badge(q, z * 1.25)
			else:
				_diamond(q, 5.0 * z, C_QUEST, Color(0.15, 0.1, 0, 0.9))
			_hit(q, "%s: %s" % [_quest.title, _quest.step] if _quest.final else "%s — the way on" % _quest.title, lim)
	# the hero: a soft view cone and an arrow
	var ang := _yaw_of(p)
	var cone := PackedVector2Array([half])
	var cols := PackedColorArray([Color(1, 1, 1, 0.22)])
	for i in 9:
		var a := ang - 0.55 + 1.1 * i / 8.0
		cone.append(half + Vector2(sin(a), cos(a)) * 30.0)
		cols.append(Color(1, 1, 1, 0.0))
	c.draw_polygon(cone, cols)
	_arrow(half, ang, 9.0, Color(1, 1, 1), Color(0, 0, 0, 0.85))

## Above the frame: compass letters, everything pinned to the rim, and the name under the mouse.
func _draw_over() -> void:
	var o: Control = _markers.get_meta(&"over")
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p):
		return
	var ctr := Vector2(diameter, diameter) * 0.5
	var off := _markers.position
	var half := _markers.size * 0.5
	var lim := _lim()
	var rim := _disc_r - 8.0
	# N E S W just inside the disc
	var r_c := _disc_r - 9.0
	for k in 4:
		var letter: String = ["N", "E", "S", "W"][k]
		var dir: Vector2 = [Vector2(0, -1), Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0)][k]
		var at := ctr + dir * r_c
		var fs := 15 if k == 0 else 12
		var col := UITheme.GOLD if k == 0 else Color(UITheme.PARCHMENT, 0.75)
		var w := _font.get_string_size(letter, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		o.draw_string_outline(_font, at + Vector2(-w * 0.5, fs * 0.36), letter, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(0, 0, 0, 0.9))
		o.draw_string(_font, at + Vector2(-w * 0.5, fs * 0.36), letter, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
	# rim pins: [world pos, colour, label, kind]
	var pins := []
	var tree := get_tree()
	if _quest.has:
		pins.append([_quest.world, C_QUEST, _quest.title, "quest"])
	for h in tree.get_nodes_in_group(&"net_hero"):
		pins.append([h.global_position, Net.player_color(h.owner_peer), String(h.display_name), "ally" if h.alive else "fallen"])
	for e in tree.get_nodes_in_group(&"enemy"):
		if e.alive and e.is_boss:
			pins.append([e.global_position, Color(1.0, 0.25, 0.18), "", "boss"])
	for g in tree.get_nodes_in_group(&"ping"):
		if g is PingMarker and g.is_inside_tree():
			pins.append([g.global_position, g.color(), "", "ping"])
	for poi in _pois:
		if poi.rim and poi.node and is_instance_valid(poi.node) and poi.node.is_inside_tree():
			pins.append([poi.node.global_position, poi.col, "", poi.kind])
	if Routes.active() and Routes.has_guide:
		pins.append([Routes.guide, C_ROUTE, "", "route"])
	var used := []                              # rim angles taken, so labels do not pile up
	for pin in pins:
		var q := _to_map(pin[0])
		var d: Vector2 = q - half
		if d.length() <= lim:
			continue
		var dir := d.normalized()
		var at := ctr + dir * rim
		var col: Color = pin[1]
		var kind: String = pin[3]
		var s := 7.0 if kind in ["quest", "ally", "fallen", "boss"] else 5.5
		var tip := at + dir * s
		o.draw_colored_polygon(PackedVector2Array([tip, at + dir.rotated(2.3) * s, at + dir * (s * 0.1), at + dir.rotated(-2.3) * s]), col)
		o.draw_polyline(PackedVector2Array([tip, at + dir.rotated(2.3) * s, at + dir * (s * 0.1), at + dir.rotated(-2.3) * s, tip]), Color(0, 0, 0, 0.8), 1.2, true)
		if kind == "quest":
			_badge_at(o, at - dir * 11.0, 0.95)
		elif kind == "boss":
			o.draw_circle(at - dir * 11.0, 4.0, Color(1.0, 0.2, 0.15, 0.8 + 0.2 * sin(_time * 6.0)))
		elif kind == "fallen":
			_fallen_at(o, at - dir * 11.0, 4.0, col)
		if pin[2] != "" and kind in ["quest", "ally", "fallen"]:
			var metres := Vector2(pin[0].x - _center.x, pin[0].z - _center.z).length()
			var txt := "%s  %s" % [pin[2], RoutePlanner.fmt_m(metres)] if kind != "quest" else RoutePlanner.fmt_m(metres)
			var a := atan2(dir.y, dir.x)
			var clash := used.any(func(u): return absf(angle_difference(u, a)) < 0.35)
			if clash:
				continue
			used.append(a)
			var fs := 13
			var w := _font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var lp := at - dir * (22.0 + w * 0.25)
			lp.x = clampf(lp.x - w * 0.5, 2.0, diameter - w - 2.0)
			lp.y = clampf(lp.y + 4.0, 12.0, diameter - 2.0)
			o.draw_string_outline(_font, lp, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(0, 0, 0, 0.95))
			o.draw_string(_font, lp, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col.lightened(0.25))
	# the name of whatever is under the mouse
	if _hover.x >= 0.0:
		var best := ""
		var bd := 9.0
		var bq := Vector2.ZERO
		for h in _hits:
			var dd: float = (h[0] as Vector2).distance_to(_hover)
			if dd < bd:
				bd = dd
				best = h[1]
				bq = h[0]
		if best != "":
			var fs2 := 14
			var w2 := _font.get_string_size(best, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2).x
			var at2 := off + bq + Vector2(-w2 * 0.5, -12.0)
			at2.x = clampf(at2.x, -60.0, diameter + 60.0 - w2)
			var box := Rect2(at2 + Vector2(-6, -fs2), Vector2(w2 + 12, fs2 + 8))
			o.draw_rect(box, Color(0.04, 0.05, 0.06, 0.92))
			o.draw_rect(box, Color(UITheme.GOLD, 0.6), false, 1.0)
			o.draw_string(_font, at2, best, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, UITheme.PARCHMENT)

func _hit(q: Vector2, text: String, lim: float) -> void:
	if (q - _markers.size * 0.5).length() <= lim + 2.0:
		_hits.append([q, text])

static func _yaw_of(n: Node3D) -> float:
	var f: Vector3 = n.global_transform.basis.z
	return atan2(f.x, f.z)

func _draw_trail(pts: PackedVector3Array, col: Color, lim: float, alpha: float) -> void:
	if pts.size() < 2:
		return
	var half := _markers.size * 0.5
	# dots marching along the road toward the goal
	var total := 0.0
	var seg := []
	for i in pts.size() - 1:
		var a := Vector2(pts[i].x, pts[i].z)
		var b := Vector2(pts[i + 1].x, pts[i + 1].z)
		seg.append([a, b, total])
		total += a.distance_to(b)
	# a faint gold line under the dots
	var prev := Vector2.INF
	for i in pts.size():
		var q0 := _to_map(pts[i])
		if prev != Vector2.INF and (q0 - half).length() < lim and (prev - half).length() < lim:
			_markers.draw_line(prev, q0, Color(0.1, 0.06, 0.0, 0.5 * alpha), 5.0, true)
			_markers.draw_line(prev, q0, Color(col, 0.35 * alpha), 2.5, true)
		prev = q0
	var gap := 2.4 * radius_m / 26.0
	var phase := fmod(_time * 3.0, gap)
	var d := phase
	var si := 0
	while d < total and si < seg.size():
		while si < seg.size() and d > seg[si][2] + (seg[si][0] as Vector2).distance_to(seg[si][1]):
			si += 1
		if si >= seg.size():
			break
		var a2: Vector2 = seg[si][0]
		var b2: Vector2 = seg[si][1]
		var t := (d - float(seg[si][2])) / maxf(0.001, a2.distance_to(b2))
		var w := a2.lerp(b2, t)
		var q := _to_map(Vector3(w.x, 0, w.y))
		if (q - half).length() < lim:
			_markers.draw_circle(q, 3.0, Color(0.1, 0.06, 0.0, 0.7 * alpha))
			_markers.draw_circle(q, 2.1, Color(col.lightened(0.15), alpha))
		d += gap

func _draw_route(lim: float) -> void:
	if not Routes.active() or Routes.path_here.size() < 2 or Game.current_map == null:
		return
	var mp := Game.current_map
	var half := _markers.size * 0.5
	var pts: Array = DataIsland.slice(Routes.path_here, Routes.along_here, DataIsland.polyline_length(Routes.path_here))
	var total := DataIsland.polyline_length(pts)
	var prev := Vector2.INF
	var along := 0.0
	var step := 1.5
	while along <= total:
		var p2 := DataIsland.point_at(pts, along)
		var q := _to_map(mp.to_global(Vector3(p2.x, 0, p2.y)))
		if (q - half).length() < lim and prev != Vector2.INF and (prev - half).length() < lim:
			_markers.draw_line(prev, q, Color(0.02, 0.15, 0.2, 0.9), 6.0, true)
			_markers.draw_line(prev, q, C_ROUTE, 3.0, true)
			# a bright pulse flowing along the line
			var k := fmod(along / 12.0 - _time * 0.8, 1.0)
			if k < 0.0:
				k += 1.0
			if k < 0.12:
				_markers.draw_line(prev, q, Color(1, 1, 1, 0.8), 3.0, true)
		prev = q
		along += step
	# the destination, when it is on this map
	var dp := DataIsland.place(Routes.dest)
	if not dp.is_empty() and StringName(dp.map) == Game.current_map_id and dp.has("pos"):
		var q2 := _to_map(mp.to_global(Vector3(dp.pos.x, 0, dp.pos.y)))
		if (q2 - half).length() < lim:
			_flag(q2, C_ROUTE)
			_hit(q2, String(dp.name), lim)

# ---- Icons (all vector, ~8–14 px) ---------------------------------------------------------------------------------

func _dot(q: Vector2, r: float, col: Color) -> void:
	_markers.draw_circle(q, r + 1.2, Color(0, 0, 0, 0.8))
	_markers.draw_circle(q, r, col)

func _diamond(q: Vector2, s: float, col: Color, edge: Color) -> void:
	var pts := PackedVector2Array([q + Vector2(0, -s), q + Vector2(s, 0), q + Vector2(0, s), q + Vector2(-s, 0)])
	_markers.draw_colored_polygon(pts, col)
	pts.append(pts[0])
	_markers.draw_polyline(pts, edge, 1.2, true)

func _arrow(q: Vector2, ang: float, s: float, fill: Color, edge: Color) -> void:
	var tip := q + Vector2(sin(ang), cos(ang)) * s
	var l := q + Vector2(sin(ang + 2.5), cos(ang + 2.5)) * s * 0.7
	var r := q + Vector2(sin(ang - 2.5), cos(ang - 2.5)) * s * 0.7
	var back := q - Vector2(sin(ang), cos(ang)) * s * 0.15
	_markers.draw_colored_polygon(PackedVector2Array([tip, l, back, r]), fill)
	_markers.draw_polyline(PackedVector2Array([tip, l, back, r, tip]), edge, 1.6, true)

func _swords(q: Vector2, s: float, col: Color) -> void:
	_markers.draw_line(q + Vector2(-s, -s), q + Vector2(s, s), Color(0, 0, 0, 0.8), 3.0, true)
	_markers.draw_line(q + Vector2(s, -s), q + Vector2(-s, s), Color(0, 0, 0, 0.8), 3.0, true)
	_markers.draw_line(q + Vector2(-s, -s), q + Vector2(s, s), col, 1.6, true)
	_markers.draw_line(q + Vector2(s, -s), q + Vector2(-s, s), col, 1.6, true)

func _skull(q: Vector2, s: float, col: Color) -> void:
	_markers.draw_circle(q + Vector2(0, -s * 0.15), s + 1.4, Color(0, 0, 0, 0.85))
	_markers.draw_circle(q + Vector2(0, -s * 0.15), s, col)
	_markers.draw_rect(Rect2(q + Vector2(-s * 0.5, s * 0.45), Vector2(s, s * 0.55)), col)
	_markers.draw_circle(q + Vector2(-s * 0.38, -s * 0.15), s * 0.26, Color(0.1, 0, 0))
	_markers.draw_circle(q + Vector2(s * 0.38, -s * 0.15), s * 0.26, Color(0.1, 0, 0))

func _crown(q: Vector2, s: float, col: Color) -> void:
	var pts := PackedVector2Array([q + Vector2(-s, s * 0.5), q + Vector2(-s, -s * 0.4), q + Vector2(-s * 0.5, s * 0.05),
		q + Vector2(0, -s * 0.7), q + Vector2(s * 0.5, s * 0.05), q + Vector2(s, -s * 0.4), q + Vector2(s, s * 0.5)])
	_markers.draw_colored_polygon(pts, col)
	pts.append(pts[0])
	_markers.draw_polyline(pts, Color(0, 0, 0, 0.85), 1.1, true)

func _flag(q: Vector2, col: Color) -> void:
	_markers.draw_line(q + Vector2(0, 5), q + Vector2(0, -9), Color(0, 0, 0, 0.9), 3.0)
	_markers.draw_line(q + Vector2(0, 5), q + Vector2(0, -9), Color(0.9, 0.9, 0.9), 1.4)
	_markers.draw_colored_polygon(PackedVector2Array([q + Vector2(0, -9), q + Vector2(9, -6), q + Vector2(0, -3)]), col)

## A fallen player: their colour ringing a dark disc with an X, and a slow "come here" pulse.
func _revive_cross(q: Vector2, s: float, col: Color) -> void:
	var pulse := fmod(_time * 0.9, 1.0)
	_markers.draw_arc(q, s + 2.0 + pulse * 9.0, 0, TAU, 22, Color(col, 0.75 * (1.0 - pulse)), 2.0, true)
	_fallen_at(_markers, q, s, col)

func _fallen_at(ci: CanvasItem, q: Vector2, s: float, col: Color) -> void:
	ci.draw_circle(q, s + 1.6, col)
	ci.draw_circle(q, s, Color(0.08, 0.05, 0.05))
	var k := s * 0.55
	ci.draw_line(q + Vector2(-k, -k), q + Vector2(k, k), Color(1.0, 0.35, 0.3), 2.0, true)
	ci.draw_line(q + Vector2(k, -k), q + Vector2(-k, k), Color(1.0, 0.35, 0.3), 2.0, true)

func _quest_badge(q: Vector2, z: float) -> void:
	_badge_at(_markers, q, z)

## A gold "!" shield: the objective (or the person to talk to).
func _badge_at(ci: CanvasItem, q: Vector2, z: float) -> void:
	var s := 6.5 * z
	var pts := PackedVector2Array([q + Vector2(-s, -s), q + Vector2(s, -s), q + Vector2(s, s * 0.35), q + Vector2(0, s * 1.15), q + Vector2(-s, s * 0.35)])
	ci.draw_colored_polygon(pts, C_QUEST)
	pts.append(pts[0])
	ci.draw_polyline(pts, Color(0.2, 0.12, 0, 0.95), 1.4, true)
	ci.draw_rect(Rect2(q + Vector2(-s * 0.16, -s * 0.72), Vector2(s * 0.32, s * 0.85)), Color(0.22, 0.12, 0.02))
	ci.draw_circle(q + Vector2(0, s * 0.5), s * 0.17, Color(0.22, 0.12, 0.02))

func _place_icon(kind: String, q: Vector2, col: Color, z: float) -> void:
	var c := _markers
	var s := 5.0 * z
	var ink := Color(0, 0, 0, 0.85)
	match kind:
		"waypoint":
			_diamond(q, s * 1.25, Color(col, 0.35), col)
			_diamond(q, s * 0.55, col, ink)
		"gate":
			c.draw_arc(q + Vector2(0, s * 0.3), s * 1.2, PI, TAU, 12, ink, 4.0, true)
			c.draw_arc(q + Vector2(0, s * 0.3), s * 1.2, PI, TAU, 12, col, 2.2, true)
			c.draw_line(q + Vector2(-s * 1.2, s * 0.3), q + Vector2(-s * 1.2, s * 1.2), col, 2.2)
			c.draw_line(q + Vector2(s * 1.2, s * 0.3), q + Vector2(s * 1.2, s * 1.2), col, 2.2)
			c.draw_circle(q + Vector2(0, s * 0.35), s * 0.55, col)
		"stairs":
			for i in 3:
				c.draw_rect(Rect2(q + Vector2(-s + i * s * 0.66, -s * 0.2 - i * s * 0.5), Vector2(s * 2.0 - i * s * 0.66, s * 0.45)), col)
		"door":
			c.draw_rect(Rect2(q + Vector2(-s * 0.65, -s * 0.5), Vector2(s * 1.3, s * 1.4)), ink)
			c.draw_circle(q + Vector2(0, -s * 0.45), s * 0.65 + 1.0, ink)
			c.draw_rect(Rect2(q + Vector2(-s * 0.5, -s * 0.45), Vector2(s, s * 1.2)), col)
			c.draw_circle(q + Vector2(0, -s * 0.45), s * 0.5, col)
		"exit":
			_arrow(q, PI, s * 1.2, col, ink)
			c.draw_arc(q, s * 1.5, 0, TAU, 16, Color(col, 0.5), 1.2, true)
		"fire":
			var pts := PackedVector2Array([q + Vector2(0, -s * 1.2), q + Vector2(s * 0.8, 0), q + Vector2(s * 0.5, s * 0.8), q + Vector2(-s * 0.5, s * 0.8), q + Vector2(-s * 0.8, 0)])
			c.draw_colored_polygon(pts, col)
			pts.append(pts[0])
			c.draw_polyline(pts, ink, 1.2, true)
			c.draw_circle(q + Vector2(0, s * 0.25), s * 0.35, Color(1.0, 0.95, 0.6))
		"craft", "smith":
			c.draw_rect(Rect2(q + Vector2(-s, -s * 0.35), Vector2(s * 2.0, s * 0.7)), ink)
			c.draw_rect(Rect2(q + Vector2(-s * 0.9, -s * 0.25), Vector2(s * 1.8, s * 0.5)), col)
			c.draw_rect(Rect2(q + Vector2(-s * 0.3, s * 0.2), Vector2(s * 0.6, s * 0.8)), col)
		"chest":
			c.draw_rect(Rect2(q + Vector2(-s, -s * 0.6), Vector2(s * 2.0, s * 1.3)), ink)
			c.draw_rect(Rect2(q + Vector2(-s * 0.85, -s * 0.45), Vector2(s * 1.7, s * 1.0)), col)
			c.draw_line(q + Vector2(-s * 0.85, -s * 0.05), q + Vector2(s * 0.85, -s * 0.05), Color(0.35, 0.2, 0.05), 1.2)
			c.draw_circle(q + Vector2(0, s * 0.05), s * 0.18, Color(0.35, 0.2, 0.05))
		"herb":
			var lf := PackedVector2Array([q + Vector2(0, -s), q + Vector2(s * 0.6, 0), q + Vector2(0, s * 0.8), q + Vector2(-s * 0.6, 0)])
			c.draw_colored_polygon(lf, col)
			c.draw_line(q + Vector2(0, -s * 0.7), q + Vector2(0, s * 0.8), Color(0.1, 0.3, 0.1), 1.0)
		"portal":
			var sw := fmod(_time * 2.0, TAU)
			c.draw_circle(q, s * 1.2, Color(0.1, 0.2, 0.5, 0.7))
			c.draw_arc(q, s * 1.2, sw, sw + 4.2, 14, col, 2.2, true)
			c.draw_arc(q, s * 0.6, -sw, -sw + 4.2, 10, Color(0.8, 0.9, 1.0), 1.6, true)
		"shop":
			c.draw_circle(q, s + 1.2, ink)
			c.draw_circle(q, s, col)
			c.draw_circle(q, s * 0.55, Color(0.45, 0.32, 0.05))
			c.draw_circle(q, s * 0.3, col)
		"inn":
			c.draw_rect(Rect2(q + Vector2(-s, -s * 0.1), Vector2(s * 2.0, s * 0.8)), ink)
			c.draw_rect(Rect2(q + Vector2(-s * 0.9, 0), Vector2(s * 1.8, s * 0.6)), col)
			c.draw_rect(Rect2(q + Vector2(-s * 0.9, -s * 0.7), Vector2(s * 0.55, s * 0.7)), col)
		"heal":
			c.draw_circle(q, s + 1.2, ink)
			c.draw_rect(Rect2(q + Vector2(-s * 0.25, -s * 0.8), Vector2(s * 0.5, s * 1.6)), col)
			c.draw_rect(Rect2(q + Vector2(-s * 0.8, -s * 0.25), Vector2(s * 1.6, s * 0.5)), col)
		"guild":
			var bn := PackedVector2Array([q + Vector2(-s * 0.8, -s), q + Vector2(s * 0.8, -s), q + Vector2(s * 0.8, s), q + Vector2(0, s * 0.5), q + Vector2(-s * 0.8, s)])
			c.draw_colored_polygon(bn, col)
			bn.append(bn[0])
			c.draw_polyline(bn, ink, 1.2, true)
		"spirit":
			var fl := PackedVector2Array([q + Vector2(0, -s * 1.3), q + Vector2(s * 0.8, 0), q + Vector2(0, s), q + Vector2(-s * 0.8, 0)])
			c.draw_colored_polygon(fl, Color(col, 0.9))
			fl.append(fl[0])
			c.draw_polyline(fl, Color(0.9, 1.0, 1.0), 1.2, true)
		"hero":
			var sh := PackedVector2Array([q + Vector2(-s * 0.8, -s * 0.8), q + Vector2(s * 0.8, -s * 0.8), q + Vector2(s * 0.8, s * 0.2), q + Vector2(0, s), q + Vector2(-s * 0.8, s * 0.2)])
			c.draw_colored_polygon(sh, col)
			sh.append(sh[0])
			c.draw_polyline(sh, ink, 1.2, true)
		_:
			_dot(q, s * 0.6, col)
