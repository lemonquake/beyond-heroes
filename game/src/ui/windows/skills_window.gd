class_name SkillsWindow
extends UIWindow
## Skills (K): the class skill tree (learn / upgrade / refund) beside a detail panel for the selected skill: icon,
## rank, Mana, cooldown, element, damage, scaling, range, statuses and next-rank changes, plus hotbar assignment
## (buttons 1-6 or drag the icon onto the HUD bar). Learned skills are listed for quick access.
## Trees with pages (Knight: Combat / Auras / Disciplines ...) get a tab per page above the tree.

var hero: HeroData
var tree: TreeView
var _points: Label
var _detail: VBoxContainer
var _learned: HBoxContainer
var _sel_skill: StringName = &""
var _tabs: HBoxContainer
var _page_desc: Label

func _init() -> void:
	super._init("Skills", Vector2(1620, 920))

func _build() -> void:
	var top := hbox(12)
	body.add_child(top)
	_points = UITheme.label("", 20, UITheme.GOLD, UITheme.body_bold())
	_points.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_points)
	top.add_child(UITheme.label("Left-click: learn · Right-click: refund", 15, UITheme.TEXT_MUTED, UITheme.body_font()))
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
	tree.node_selected.connect(_on_node)
	tree.ranks_changed.connect(refresh)
	scroll.add_child(tree)
	var side := vbox(10)
	side.custom_minimum_size = Vector2(430, 0)
	row.add_child(side)
	side.add_child(section("Learned Skills"))
	_learned = hbox(6)
	side.add_child(_learned)
	side.add_child(section("Details"))
	var dw := inset()
	dw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	side.add_child(dw)
	var ds := ScrollContainer.new()
	ds.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	dw.add_child(ds)
	_detail = vbox(6)
	_detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ds.add_child(_detail)

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	tree.bind(hero, false)
	_build_tabs()
	_points.text = "%d skill point%s available" % [hero.progress.skill_points, "" if hero.progress.skill_points == 1 else "s"]
	for c in _learned.get_children():
		c.queue_free()
	for sid in hero.learned_skills():
		var b := SkillButton.new(&"", 60.0)
		b.set_skill(sid)
		b.activated.connect(func(_s): _show(sid))
		TooltipLayer.attach(b, func() -> Control: return Tips.skill(sid, hero, Game.player as Player))
		_learned.add_child(b)
	if _sel_skill == &"" and not hero.learned_skills().is_empty():
		_sel_skill = hero.learned_skills()[0]
	_show(_sel_skill)

func _build_tabs() -> void:
	for c in _tabs.get_children():
		c.queue_free()
	var t := hero.skill_tree.tree
	_tabs.get_parent().visible = t.page_count() > 1
	if t.page_count() <= 1:
		return
	for i in t.page_count():
		var idx := i
		var learned := 0
		for n in t.nodes_on_page(i):
			learned += hero.skill_tree.rank(n.id)
		var label := String(t.pages[i].name) + ("  (%d)" % learned if learned > 0 else "")
		_tabs.add_child(button(label, func() -> void:
			Audio.play_ui(&"ui_click")
			tree.set_page(idx)
			_build_tabs(), &"PrimaryButton" if tree.page == i else &"", 190.0))
	_page_desc.text = String(t.pages[tree.page].get("desc", ""))

func _on_node(n: Dictionary) -> void:
	if n.has("skill"):
		_show(n.skill)

func _show(sid: StringName) -> void:
	_sel_skill = sid
	for c in _detail.get_children():
		c.queue_free()
	if sid == &"":
		_detail.add_child(UITheme.label("Select a skill in the tree.", 16, UITheme.TEXT_DIM, UITheme.body_font()))
		return
	var tip := Tips.skill(sid, hero, Game.player as Player, true)
	# reuse the tooltip content inline (without its frame)
	var content := tip.get_child(0) as VBoxContainer
	tip.remove_child(content)
	tip.queue_free()
	_detail.add_child(content)
	if hero.skill_rank(sid) <= 0:
		return
	_detail.add_child(Tips.gap(6))
	_detail.add_child(UITheme.label("Hotbar", 17, UITheme.GOLD, UITheme.title_font()))
	var slots := hbox(4)
	_detail.add_child(slots)
	for i in HeroData.SKILL_BAR_SIZE:
		var idx := i
		var on_bar: bool = hero.skill_bar[i] == sid
		var b := button(Settings.binding_text(StringName("skill_%d" % (i + 1))), func() -> void: _assign(sid, idx), &"PrimaryButton" if on_bar else &"", 58.0)
		slots.add_child(b)
	var hint := UITheme.label("Click a key to put the skill there, or drag its icon onto the hotbar.", 14, UITheme.TEXT_MUTED, UITheme.body_font())
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_detail.add_child(hint)

func _assign(sid: StringName, idx: int) -> void:
	var bar := hero.skill_bar
	var from := bar.find(sid)
	if from >= 0:
		bar[from] = bar[idx]
	bar[idx] = sid
	hero.skills_changed.emit()
	Audio.play_ui(&"ui_click")
	_show(sid)
