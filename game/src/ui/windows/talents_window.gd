class_name TalentsWindow
extends UIWindow
## Talents (T): the class talent tree. Minor nodes (stat steps), major nodes (mechanics), keystones (build-defining,
## mutually exclusive), prerequisites, ranks, refunds; a summary of what the invested talents grant.

var hero: HeroData
var tree: TreeView
var _points: Label
var _summary: VBoxContainer

func _init() -> void:
	super._init("Talents", Vector2(1620, 920))

func _build() -> void:
	var top := hbox(12)
	body.add_child(top)
	_points = UITheme.label("", 20, UITheme.GOLD, UITheme.body_bold())
	_points.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_points)
	top.add_child(UITheme.label("Left-click: learn · Right-click: refund · Keystones exclude each other", 15, UITheme.TEXT_MUTED, UITheme.body_font()))
	var row := hbox(16)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	var tw := inset()
	tw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(tw)
	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tw.add_child(scroll)
	tree = TreeView.new()
	tree.ranks_changed.connect(refresh)
	scroll.add_child(tree)
	var side := vbox(10)
	side.custom_minimum_size = Vector2(380, 0)
	row.add_child(side)
	side.add_child(section("Your Talents"))
	var sw := inset()
	sw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	side.add_child(sw)
	var ss := ScrollContainer.new()
	ss.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sw.add_child(ss)
	_summary = vbox(4)
	_summary.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ss.add_child(_summary)

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	tree.bind(hero, true)
	_points.text = "%d talent point%s available · %d invested" % [hero.progress.talent_points, "" if hero.progress.talent_points == 1 else "s",
		hero.talent_tree.points_spent()]
	for c in _summary.get_children():
		c.queue_free()
	var any := false
	for n in hero.talent_tree.tree.nodes:
		var r := hero.talent_tree.rank(n.id)
		if r <= 0:
			continue
		any = true
		var col := Color(0.6, 0.97, 1.0) if n.get("kind") == "keystone" else (UITheme.GOLD if n.get("kind") == "major" else UITheme.PARCHMENT)
		_summary.add_child(UITheme.label("%s  %d/%d" % [n.name, r, int(n.get("max_rank", 1))], 16, col, UITheme.body_bold()))
		for m in n.get("mods", []):
			var l := UITheme.label("  " + StatDefs.format_modifier(StringName(m[0]), int(m[1]), float(m[2]) * r), 14, Tips.AFFIX, UITheme.body_font())
			_summary.add_child(l)
		if n.has("flags") and n.has("desc"):
			var d := UITheme.label("  " + String(n.desc), 14, UITheme.TEXT_DIM, UITheme.body_font())
			d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			d.custom_minimum_size = Vector2(330, 0)
			_summary.add_child(d)
	if not any:
		var l := UITheme.label("No talents yet. You earn a talent point every level.", 15, UITheme.TEXT_MUTED, UITheme.body_font())
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_summary.add_child(l)
