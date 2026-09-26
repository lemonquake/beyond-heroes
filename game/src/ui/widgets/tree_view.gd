class_name TreeView
extends Control
## Skill / talent tree canvas. Painted class backdrop, branch captions, connectors (dim when locked, bronze when
## reachable, glowing when both ends are learned), node art per kind and state, rank pips, and an unlock burst.
## Left-click learns a rank, right-click refunds one (respec-ready). Nodes explain themselves on hover.

signal node_selected(node: Dictionary)
signal ranks_changed

const UNIT := Vector2(104, 112)
const MARGIN := Vector2(70, 96)
const ART := {"skill": ["node_skill", 72.0], "upgrade": ["node_upgrade", 56.0], "minor": ["node_minor", 50.0],
	"major": ["node_major", 64.0], "keystone": ["node_keystone", 92.0]}

var hero: HeroData
var tree_state: TreeState
var is_talent := false
var selected_id: StringName = &""
var _bursts := []            # [{pos, t}]
var _hover_id: StringName = &""
var _bg: Texture2D

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE

func bind(p_hero: HeroData, talents: bool) -> void:
	hero = p_hero
	is_talent = talents
	tree_state = hero.talent_tree if talents else hero.skill_tree
	_bg = UIArt.tex("tree/tree_bg_%s.png" % hero.cls.id)
	var max_p := Vector2.ZERO
	for n in tree_state.tree.nodes:
		max_p = max_p.max(n.pos)
	custom_minimum_size = MARGIN * 2.0 + max_p * UNIT + Vector2(40, 40)
	queue_redraw()

func _points() -> int:
	return hero.progress.talent_points if is_talent else hero.progress.skill_points

func node_center(n: Dictionary) -> Vector2:
	return MARGIN + Vector2(n.pos) * UNIT + Vector2(40, 30)

func state_of(n: Dictionary) -> String:
	if tree_state.rank(n.id) > 0:
		return "allocated"
	var why := tree_state.can_rank_up(n.id, 999, hero.progress.level)
	return "available" if why == "" else "locked"

func _process(delta: float) -> void:
	if _bursts.is_empty():
		return
	for b in _bursts:
		b.t += delta
	_bursts = _bursts.filter(func(b): return b.t < 0.9)
	queue_redraw()

func _draw() -> void:
	if hero == null:
		return
	var r := Rect2(Vector2.ZERO, size)
	if _bg:
		draw_texture_rect(_bg, r, false, Color(0.85, 0.85, 0.85))
	else:
		draw_rect(r, Color(0.05, 0.04, 0.05))
	var font := UITheme.title_font()
	for b in tree_state.tree.branches:
		var x := MARGIN.x + float(b.x) * UNIT.x + 40.0
		var t := String(b.name).to_upper()
		var fs := 20
		var w := font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		draw_string_outline(font, Vector2(x - w * 0.5, 44), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 6, Color(0, 0, 0, 0.85))
		draw_string(font, Vector2(x - w * 0.5, 44), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(b.color).lerp(UITheme.PARCHMENT, 0.3))
	# connectors
	var ctex := UIArt.tex("tree/connector.png")
	for n in tree_state.tree.nodes:
		for req in n.get("requires", []) + n.get("requires_all", []):
			var m := tree_state.tree.node(req)
			if m.is_empty():
				continue
			var a := node_center(m)
			var bpt := node_center(n)
			var both := tree_state.rank(req) > 0 and tree_state.rank(n.id) > 0
			var reach := tree_state.rank(req) > 0
			var col := Color(0.55, 0.98, 1.0) if both else (UITheme.GOLD if reach else Color(0.5, 0.46, 0.42, 0.85))
			var width := 10.0 if both else 7.0
			_line(a, bpt, col, width, ctex)
	# nodes
	for n in tree_state.tree.nodes:
		_draw_node(n)
	for b in _bursts:
		var k: float = b.t / 0.9
		draw_arc(b.pos, 30.0 + 60.0 * k, 0.0, TAU, 48, Color(0.6, 0.97, 1.0, 1.0 - k), 4.0 * (1.0 - k) + 1.0)
		draw_circle(b.pos, 30.0 * (1.0 - k), Color(0.8, 0.98, 1.0, 0.35 * (1.0 - k)))

func _line(a: Vector2, b: Vector2, col: Color, width: float, tex: Texture2D) -> void:
	# solid core so links read at any zoom, the engraved texture on top
	draw_line(a, b, Color(col, col.a * 0.55), width * 0.45, true)
	if tex:
		var d := b - a
		var len := d.length()
		draw_set_transform(a, d.angle())
		draw_texture_rect(tex, Rect2(Vector2(0, -width * 0.5), Vector2(len, width)), true, col)
		draw_set_transform(Vector2.ZERO)
	else:
		draw_line(a, b, col, width * 0.5, true)

func _draw_node(n: Dictionary) -> void:
	var kind := String(n.get("kind", "minor"))
	var art: Array = ART.get(kind, ART.minor)
	var st := state_of(n)
	var sz: float = art[1]
	var c := node_center(n)
	var rect := Rect2(c - Vector2(sz, sz) * 0.5, Vector2(sz, sz))
	var icon := UIArt.node_icon(n)
	var inner := rect.grow(-sz * (0.2 if kind != "skill" else 0.14))
	if icon:
		var mod := Color(1, 1, 1) if st == "allocated" else (Color(0.8, 0.8, 0.8) if st == "available" else Color(0.35, 0.35, 0.38))
		draw_texture_rect(icon, inner, false, mod)
	var frame := UIArt.tex("tree/%s_%s.png" % [art[0], st])
	if frame:
		draw_texture_rect(frame, rect, false)
	if n.id == selected_id or n.id == _hover_id:
		draw_arc(c, sz * 0.62, 0.0, TAU, 40, Color(1.0, 0.9, 0.6, 0.9 if n.id == selected_id else 0.5), 2.0)
	# rank pips / text
	var mr := int(n.get("max_rank", 1))
	if mr > 1:
		var font := UITheme.number_font()
		var t := "%d/%d" % [tree_state.rank(n.id), mr]
		var w := font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x
		var p := Vector2(c.x - w * 0.5, rect.end.y + 15)
		draw_string_outline(font, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, 5, Color(0, 0, 0, 0.9))
		draw_string(font, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, UITheme.GOLD if tree_state.rank(n.id) > 0 else UITheme.TEXT_DIM)

func _node_at(p: Vector2) -> Dictionary:
	for n in tree_state.tree.nodes:
		var sz: float = (ART.get(String(n.get("kind", "minor")), ART.minor) as Array)[1]
		if p.distance_to(node_center(n)) < sz * 0.55:
			return n
	return {}

func _gui_input(e: InputEvent) -> void:
	if hero == null:
		return
	if e is InputEventMouseMotion:
		var n := _node_at(e.position)
		var id: StringName = n.get("id", &"")
		if id != _hover_id:
			_hover_id = id
			queue_redraw()
			if id == &"":
				TooltipLayer.hide_for(self)
			else:
				TooltipLayer.show_for(self, func() -> Control: return _tip(n))
	elif e is InputEventMouseButton and e.pressed:
		var n := _node_at(e.position)
		if n.is_empty():
			return
		selected_id = n.id
		node_selected.emit(n)
		if e.button_index == MOUSE_BUTTON_LEFT:
			_learn(n)
		elif e.button_index == MOUSE_BUTTON_RIGHT:
			_refund(n)
		queue_redraw()
		TooltipLayer.refresh()
		accept_event()

func _learn(n: Dictionary) -> void:
	var err := hero.spend_talent_point(n.id) if is_talent else hero.spend_skill_point(n.id)
	if err != "":
		if err != "Maximum rank":
			Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
		return
	_bursts.append({"pos": node_center(n), "t": 0.0})
	Audio.play_ui(&"talent_unlock" if is_talent else &"skill_unlock")
	ranks_changed.emit()

func _refund(n: Dictionary) -> void:
	var err := hero.refund_talent_point(n.id) if is_talent else hero.refund_skill_point(n.id)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
		return
	Audio.play_ui(&"ui_click")
	ranks_changed.emit()

func _tip(n: Dictionary) -> Control:
	if n.get("kind") == "skill":
		var tip := Tips.skill(n.skill, hero, Game.player as Player, true)
		_append_requirements(tip.get_child(0) as VBoxContainer, n)
		return tip
	var f := Tips.frame(360.0)
	var v: VBoxContainer = f[1]
	var kind_name: String = {"upgrade": "Skill Upgrade", "minor": "Minor Talent", "major": "Major Talent", "keystone": "Keystone"}.get(String(n.get("kind", "")), "Talent")
	v.add_child(Tips.lbl(String(n.name), 20, UITheme.GOLD if n.get("kind") != "keystone" else Color(0.6, 0.97, 1.0), UITheme.title_font()))
	v.add_child(Tips.lbl("%s · Rank %d / %d" % [kind_name, tree_state.rank(n.id), int(n.get("max_rank", 1))], 14, UITheme.TEXT_DIM))
	v.add_child(Tips.rule(UITheme.BRONZE))
	if n.has("desc"):
		v.add_child(Tips.lbl(String(n.desc), 16, UITheme.TEXT))
	if n.get("kind") == "upgrade" and n.has("skill"):
		var sd := DB.skill(n.skill)
		if sd:
			v.add_child(Tips.lbl("Upgrades %s" % sd.display_name, 14, UITheme.TEXT_DIM))
	var mods: Array = n.get("mods", [])
	var r := maxi(1, tree_state.rank(n.id))
	for m in mods:
		v.add_child(Tips.lbl(StatDefs.format_modifier(StringName(m[0]), int(m[1]), float(m[2]) * r) + ("" if tree_state.rank(n.id) > 0 else "  (at rank 1)"), 15, Tips.AFFIX))
	_append_requirements(v, n)
	return f[0]

func _append_requirements(v: VBoxContainer, n: Dictionary) -> void:
	v.add_child(Tips.rule())
	var why := tree_state.can_rank_up(n.id, _points(), hero.progress.level)
	if why == "":
		v.add_child(Tips.lbl("Click to learn (%d point%s)" % [int(n.get("cost", 1)), "s" if int(n.get("cost", 1)) > 1 else ""], 14, UITheme.GOOD))
	elif why != "Maximum rank":
		v.add_child(Tips.lbl(why, 14, UITheme.BAD))
	if tree_state.rank(n.id) > 0:
		v.add_child(Tips.lbl("Right-click to refund a rank", 13, UITheme.TEXT_MUTED))
