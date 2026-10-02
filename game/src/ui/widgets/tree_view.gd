class_name TreeView
extends Control
## Skill / talent tree canvas. Painted class backdrop, branch captions, connectors (dim when locked, bronze when
## reachable, glowing when both ends are learned), node art per kind and state, rank pips, and an unlock burst.
## Left-click learns a rank, right-click refunds one (respec-ready). Nodes explain themselves on hover.
## Trees with pages (Combat / Auras / Disciplines ...) show one page at a time (`page`); passives are round medallions.

signal node_selected(node: Dictionary)
signal ranks_changed

const UNIT := Vector2(104, 112)
const MARGIN := Vector2(70, 96)
const ART := {"skill": ["node_skill", 72.0], "upgrade": ["node_upgrade", 56.0], "minor": ["node_minor", 50.0],
	"major": ["node_major", 64.0], "keystone": ["node_keystone", 92.0], "passive": ["node_major", 66.0]}

var hero: HeroData
var tree_state: TreeState
var is_talent := false
var selected_id: StringName = &""
var page := 0
var _bursts := []            # [{pos, t}]
var _hover_id: StringName = &""
var _bg: Texture2D
## bh-029: wide trees (the Mage's eight elements) shrink to the width their owner gives them (`fit_to`) instead of
## hiding columns behind a horizontal scroll bar. Drawing and hit-testing happen in unzoomed tree space.
var zoom := 1.0
var _content := Vector2.ZERO
var _fit_width := 0.0

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE

func bind(p_hero: HeroData, talents: bool) -> void:
	hero = p_hero
	is_talent = talents
	tree_state = hero.talent_tree if talents else hero.skill_tree
	_bg = UIArt.tex("tree/tree_bg_%s.png" % hero.cls.id)
	page = clampi(page, 0, tree_state.tree.page_count() - 1)
	var max_p := Vector2.ZERO
	for n in _nodes():
		max_p = max_p.max(n.pos)
	_content = MARGIN * 2.0 + max_p * UNIT + Vector2(40, 40)
	_apply_zoom()

## Fit the tree to `w` pixels of width (0 = natural size). Never smaller than 55 %, never larger than 100 %.
func fit_to(w: float) -> void:
	_fit_width = w
	_apply_zoom()

func _apply_zoom() -> void:
	zoom = clampf(_fit_width / _content.x, 0.55, 1.0) if _fit_width > 0.0 and _content.x > 0.0 else 1.0
	custom_minimum_size = _content * zoom
	queue_redraw()

## Show another page of the tree.
func set_page(p: int) -> void:
	page = p
	_hover_id = &""
	if hero:
		bind(hero, is_talent)

## Nodes on the current page.
func _nodes() -> Array:
	return tree_state.tree.nodes_on_page(page) if tree_state.tree.page_count() > 1 else tree_state.tree.nodes

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
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * zoom)
	var r := Rect2(Vector2.ZERO, size / zoom)
	if _bg:
		draw_texture_rect(_bg, r, false, Color(0.85, 0.85, 0.85))
	else:
		draw_rect(r, Color(0.05, 0.04, 0.05))
	var font := UITheme.title_font()
	for b in tree_state.tree.branches:
		if int(b.get("page", 0)) != page and tree_state.tree.page_count() > 1:
			continue
		var x := MARGIN.x + float(b.x) * UNIT.x + 40.0
		var t := String(b.name).to_upper()
		var fs := 20
		var w := font.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		draw_string_outline(font, Vector2(x - w * 0.5, 44), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 6, Color(0, 0, 0, 0.85))
		draw_string(font, Vector2(x - w * 0.5, 44), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(b.color).lerp(UITheme.PARCHMENT, 0.3))
	# connectors
	var ctex := UIArt.tex("tree/connector.png")
	for n in _nodes():
		for req in n.get("requires", []) + n.get("requires_all", []):
			var m := tree_state.tree.node(req)
			if m.is_empty() or int(m.get("page", 0)) != int(n.get("page", 0)):
				continue
			var a := node_center(m)
			var bpt := node_center(n)
			var both := tree_state.rank(req) > 0 and tree_state.rank(n.id) > 0
			var reach := tree_state.rank(req) > 0
			var col := Color(0.55, 0.98, 1.0) if both else (UITheme.GOLD if reach else Color(0.5, 0.46, 0.42, 0.85))
			var width := 10.0 if both else 7.0
			_line(a, bpt, col, width, ctex)
	# nodes
	for n in _nodes():
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
		draw_set_transform(a * zoom, d.angle(), Vector2.ONE * zoom)
		draw_texture_rect(tex, Rect2(Vector2(0, -width * 0.5), Vector2(len, width)), true, col)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE * zoom)
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
	if kind == "passive":
		inner = rect.grow(-sz * 0.08)            # the passive icon is its own round medallion
	var mod := Color(1, 1, 1) if st == "allocated" else (Color(0.8, 0.8, 0.8) if st == "available" else Color(0.35, 0.35, 0.38))
	if icon:
		draw_texture_rect(icon, inner, false, mod)
	var sd: SkillDef = DB.skill(n.skill) if kind == "skill" and n.has("skill") else null
	if kind == "passive":
		draw_arc(c, sz * 0.5, 0.0, TAU, 48, Color(UITheme.GOLD, 0.95) if st == "allocated" else Color(0.55, 0.5, 0.45, 0.9), 3.0, true)
	else:
		var frame := UIArt.tex("tree/%s_%s.png" % [art[0], st])
		if frame:
			draw_texture_rect(frame, rect, false)
	if sd and sd.is_aura():
		# auras wear a halo: warm for offense, cool for defense; brighter while it is the active aura
		var hc := Color(1.0, 0.62, 0.3) if sd.aura_kind == &"offense" else Color(0.55, 0.78, 1.0)
		var on := hero.active_aura == sd.id
		draw_arc(c, sz * 0.68, 0.0, TAU, 48, Color(hc, 0.95 if on else 0.45), 4.0 if on else 2.0, true)
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

var _touch_down_id: StringName = &""
var _touch_down_t := 0

func _node_at(p: Vector2) -> Dictionary:
	for n in _nodes():
		var sz: float = (ART.get(String(n.get("kind", "minor")), ART.minor) as Array)[1]
		if p.distance_to(node_center(n)) < sz * 0.55:
			return n
	return {}

func _gui_input(e: InputEvent) -> void:
	if hero == null:
		return
	if e is InputEventMouseMotion:
		var n := _node_at(e.position / zoom)
		var id: StringName = n.get("id", &"")
		if id != _hover_id:
			_hover_id = id
			queue_redraw()
			if id == &"":
				TooltipLayer.hide_for(self)
			else:
				TooltipLayer.show_for(self, func() -> Control: return _tip(n))
	elif e is InputEventMouseButton and not e.pressed and e.button_index == MOUSE_BUTTON_LEFT and Settings.touch_mode:
		# touch play: a quick tap learns; a long press is a right-click (TouchControls) and refunds instead
		var n := _node_at(e.position / zoom)
		if not n.is_empty() and n.id == _touch_down_id and Time.get_ticks_msec() - _touch_down_t < 450:
			_learn(n)
			queue_redraw()
			TooltipLayer.refresh()
		_touch_down_id = &""
		accept_event()
	elif e is InputEventMouseButton and e.pressed:
		var n := _node_at(e.position / zoom)
		if n.is_empty():
			return
		selected_id = n.id
		node_selected.emit(n)
		if e.button_index == MOUSE_BUTTON_LEFT and Settings.touch_mode:
			_touch_down_id = n.id
			_touch_down_t = Time.get_ticks_msec()
		elif e.button_index == MOUSE_BUTTON_LEFT:
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
		_append_synergies(tip.get_child(0) as VBoxContainer, n)
		_append_requirements(tip.get_child(0) as VBoxContainer, n)
		return tip
	var f := Tips.frame(360.0)
	var v: VBoxContainer = f[1]
	if n.get("kind") == "passive":
		var rk := tree_state.rank(n.id)
		v.add_child(Tips.lbl(String(n.name), 20, UITheme.GOLD, UITheme.title_font()))
		v.add_child(Tips.lbl("Passive skill · always on · Level %d / %d" % [rk, int(n.get("max_rank", 1))], 14, UITheme.TEXT_DIM))
		v.add_child(Tips.rule(UITheme.BRONZE))
		v.add_child(Tips.lbl(DataSkillsExt.passive_text(n, maxi(rk, 1)), 16, UITheme.TEXT))
		if rk > 0 and rk < int(n.get("max_rank", 1)):
			v.add_child(Tips.lbl("Next level: " + DataSkillsExt.passive_text(n, rk + 1), 15, Tips.AFFIX))
		elif rk == 0:
			v.add_child(Tips.lbl("(values at level 1)", 13, UITheme.TEXT_MUTED))
		_append_requirements(v, n)
		return f[0]
	var kind_name: String = {"upgrade": "Skill Upgrade", "minor": "Minor Talent", "major": "Major Talent", "keystone": "Keystone"}.get(String(n.get("kind", "")), "Talent")
	v.add_child(Tips.lbl(String(n.name), 20, UITheme.GOLD if n.get("kind") != "keystone" else Color(0.6, 0.97, 1.0), UITheme.title_font()))
	v.add_child(Tips.lbl("%s · Level %d / %d" % [kind_name, tree_state.rank(n.id), int(n.get("max_rank", 1))], 14, UITheme.TEXT_DIM))
	v.add_child(Tips.rule(UITheme.BRONZE))
	if n.has("desc"):
		v.add_child(Tips.lbl(String(n.desc), 16, UITheme.TEXT))
	if n.get("kind") == "upgrade" and n.has("skill"):
		var sd := DB.skill(n.skill)
		if sd:
			v.add_child(Tips.lbl("Upgrades %s" % sd.display_name, 14, UITheme.TEXT_DIM))
	var mods: Array = n.get("mods", [])
	var r := tree_state.tree.power_of(n.id, maxi(1, tree_state.rank(n.id)))
	for m in mods:
		v.add_child(Tips.lbl(StatDefs.format_modifier(StringName(m[0]), int(m[1]), float(m[2]) * r) + ("" if tree_state.rank(n.id) > 0 else "  (at level 1)"), 15, Tips.AFFIX))
	_append_requirements(v, n)
	return f[0]

## Diablo II style synergies: which other skills raise this one's damage, and by how much right now.
func _append_synergies(v: VBoxContainer, n: Dictionary) -> void:
	var syn: Array = n.get("synergies", [])
	if syn.is_empty() or is_talent:
		return
	v.add_child(Tips.rule())
	v.add_child(Tips.lbl("Synergies", 15, UITheme.GOLD, UITheme.body_bold()))
	for s in syn:
		var other := tree_state.tree.node(StringName(s[0]))
		var rk := tree_state.rank(StringName(s[0]))
		v.add_child(Tips.lbl("+%s%% damage per level of %s (now +%s%%)" % [StatDefs._num(float(s[1])), String(other.get("name", s[0])),
			StatDefs._num(float(s[1]) * tree_state.tree.power_of(StringName(s[0]), rk))], 14, Tips.AFFIX if rk > 0 else UITheme.TEXT_DIM))

func _append_requirements(v: VBoxContainer, n: Dictionary) -> void:
	v.add_child(Tips.rule())
	var why := tree_state.can_rank_up(n.id, _points(), hero.progress.level)
	if why == "":
		v.add_child(Tips.lbl("Click to learn (%d point%s)" % [int(n.get("cost", 1)), "s" if int(n.get("cost", 1)) > 1 else ""], 14, UITheme.GOOD))
	elif why != "Maximum rank":
		v.add_child(Tips.lbl(why, 14, UITheme.BAD))
	if tree_state.rank(n.id) > 0:
		v.add_child(Tips.lbl("Right-click to refund a level", 13, UITheme.TEXT_MUTED))
