class_name TalentsWindow
extends UIWindow
## Talents (T): the class talent tree. Minor nodes (stat steps), major nodes (mechanics), keystones (build-defining,
## mutually exclusive), prerequisites, ranks, refunds; a summary of what the invested talents grant.

var hero: HeroData
var tree: TreeView
var _points: Label
var _summary: VBoxContainer
## Class Transcendence: a tab per page (Talents, then one per advancement) and locked previews of the next one
var _tabs: HBoxContainer
var _page_desc: Label

func _init() -> void:
	super._init("Talents", Vector2(1620, 920))

func _build() -> void:
	var top := hbox(12)
	body.add_child(top)
	_points = UITheme.label("", 20, UITheme.GOLD, UITheme.body_bold())
	_points.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_points)
	top.add_child(UITheme.label("Left-click: learn · Right-click: refund · Keystones exclude each other", 15, UITheme.TEXT_MUTED, UITheme.body_font()))
	var pages := hbox(12)
	body.add_child(pages)
	_tabs = hbox(6)
	pages.add_child(_tabs)
	_page_desc = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_page_desc.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pages.add_child(_page_desc)
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
	scroll.resized.connect(func() -> void: tree.fit_to(scroll.size.x - 16.0))
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
	_build_tabs()
	_points.text = "%d talent point%s available · %d invested" % [hero.progress.talent_points, "" if hero.progress.talent_points == 1 else "s",
		hero.talent_tree.points_spent()]
	for c in _summary.get_children():
		c.queue_free()
	_add_traits()
	var any := false
	for n in hero.talent_tree.tree.nodes:
		var r := hero.talent_tree.rank(n.id)
		if r <= 0:
			continue
		any = true
		var col := Color(0.6, 0.97, 1.0) if n.get("kind") == "keystone" else (UITheme.GOLD if n.get("kind") == "major" else UITheme.PARCHMENT)
		_summary.add_child(UITheme.label("%s  %d/%d" % [n.name, r, int(n.get("max_rank", 1))], 16, col, UITheme.body_bold()))
		var pw := hero.talent_tree.tree.power_of(n.id, r)
		for m in n.get("mods", []):
			var l := UITheme.label("  " + StatDefs.format_modifier(StringName(m[0]), int(m[1]), float(m[2]) * pw), 14, Tips.AFFIX, UITheme.body_font())
			_summary.add_child(l)
		if n.has("flags") and n.has("desc"):
			var desc := DataTranscendence.talent_text(n.id, r) if n.get("transcend_talent", false) else String(n.desc)
			var d := UITheme.label("  " + desc, 14, UITheme.TEXT_DIM, UITheme.body_font())
			d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			d.custom_minimum_size = Vector2(330, 0)
			_summary.add_child(d)
	if not any:
		var l := UITheme.label("No talents yet. You earn a talent point every level.", 15, UITheme.TEXT_MUTED, UITheme.body_font())
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_summary.add_child(l)

func _build_tabs() -> void:
	for c in _tabs.get_children():
		_tabs.remove_child(c)
		c.queue_free()
	var t := hero.talent_tree.tree
	var previews := TranscendPages.preview_ids(hero)
	_tabs.get_parent().visible = t.page_count() > 1 or not previews.is_empty()
	for i in t.page_count():
		var idx := i
		var learned := 0
		for n in t.nodes_on_page(i):
			learned += hero.talent_tree.rank(n.id)
		var label := String(t.pages[i].name if not t.pages.is_empty() else "Talents") + ("  (%d)" % learned if learned > 0 else "")
		_tabs.add_child(button(label, func() -> void:
			Audio.play_ui(&"ui_click")
			tree.set_page(idx)
			_build_tabs(), &"PrimaryButton" if tree.page == i and not tree.preview else &"", 190.0))
	for id in previews:
		var pid: StringName = id
		_tabs.add_child(button("%s (preview)" % DataTranscendence.name_of(pid), func() -> void:
			Audio.play_ui(&"ui_click")
			tree.bind_preview(hero, true, pid)
			_build_tabs(), &"PrimaryButton" if tree.preview and tree.preview_class == pid else &"", 220.0))
	if tree.preview:
		_page_desc.text = "Locked preview. %s" % TranscendPages.preview_hint(hero, tree.preview_class)
	elif not t.pages.is_empty():
		_page_desc.text = String(t.pages[tree.page].get("desc", ""))
	else:
		_page_desc.text = ""

## Class Transcendence: the signature traits the hero's class line has, above the learned talents.
func _add_traits() -> void:
	var line := ClassTranscendence.lineage(hero)
	var shown := false
	for id in line:
		if not DataTranscendence.SIGNATURES.has(id):
			continue
		if not shown:
			_summary.add_child(UITheme.label("Class traits", 17, UITheme.GOLD, UITheme.body_bold()))
			shown = true
		var sg: Dictionary = DataTranscendence.SIGNATURES[id]
		_summary.add_child(UITheme.label("%s  (%s)" % [String(sg.name), DataTranscendence.name_of(id)], 16, ClassTranscendence.label_color(id), UITheme.body_bold()))
		var d := UITheme.label("  " + DataTranscendence.signature_text(id), 14, UITheme.TEXT_DIM, UITheme.body_font())
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		d.custom_minimum_size = Vector2(330, 0)
		_summary.add_child(d)
	if shown:
		var gap := Control.new()
		gap.custom_minimum_size.y = 8
		_summary.add_child(gap)
