class_name TempoWindow
extends UIWindow
## Tempos (O): the hero's bound spirit companions. One tab per Tempo. Left: the spirit on its plinth with its 14
## equipment slots. Middle: live HP / mana, derived stats (half the hero's, plus its own gear), personality, skills
## with mana costs and cooldowns, and where it fell. Right: the hero's bag — right-click or drag an item onto a slot to
## give it to the Tempo; right-click an equipped piece to take it back. Tempos wear gear one tier below the hero's.

const SLOT_LAYOUT := {
	&"helm": [0, 0], &"inner_garment": [0, 1], &"armor": [0, 2], &"leggings": [0, 3], &"gloves_1": [0, 4], &"boots_1": [0, 5],
	&"accessory_1": [1, 0], &"accessory_2": [1, 1], &"accessory_3": [1, 2], &"accessory_4": [1, 3], &"gloves_2": [1, 4], &"boots_2": [1, 5],
}
const STAT_ROWS := [[&"max_hp", "Health"], [&"max_mana", "Mana"], [&"defense", "Defense"], [&"phys_res", "Physical Resist"],
	[&"evasion", "Evasion"], [&"accuracy", "Accuracy"], [&"crit_chance", "Critical Chance"], [&"crit_damage", "Critical Damage"],
	[&"attack_speed", "Attack Speed"], [&"move_speed", "Move Speed"], [&"phys_damage", "Physical Damage"], [&"hp_regen", "Health Regen"],
	[&"mana_regen", "Mana Regen"], [&"healing", "Healing Done"]]

var hero: HeroData
var current: TempoData
var preview: CharacterPreview
var equip_slots := {}
var cells: Array[ItemSlot] = []
var _tabs: TabBar
var _empty: Label
var _content: HBoxContainer
var _name: Label
var _class_line: Label
var _strength_head: Control
var _hp_bar: ArtBar
var _mp_bar: ArtBar
var _state: Label
var _stats_grid: GridContainer
var _skills_box: VBoxContainer
var _about: Label
var _cap_label: Label
var _weapon_label: Label
var _stats: DerivedStats
var _live_t := 0.0
var _doll_scroll: ScrollContainer
var _sheet_scroll: ScrollContainer
var _bag: Control
var _bag_scroll: ScrollContainer
var _bag_grid: GridContainer
var _bag_hint: Label
var _detail_tabs: TabContainer
var _compact := false
var _layout_viewport := Vector2.ZERO

func _init() -> void:
	super._init("Tempos", Vector2(1640, 900))

func _build() -> void:
	_tabs = TabBar.new()
	_tabs.tab_changed.connect(func(i: int) -> void:
		if hero and i >= 0 and i < hero.tempos.size():
			current = hero.tempos[i]
			refresh())
	body.add_child(_tabs)
	_empty = UITheme.label("", 20, UITheme.TEXT_DIM, UITheme.body_font())
	_empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty.custom_minimum_size = Vector2(0, 100)
	_empty.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(_empty)
	_content = hbox(18)
	_content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_content)
	_doll_scroll = _scroll_pane(_build_doll())
	_doll_scroll.custom_minimum_size.x = 420
	_doll_scroll.size_flags_horizontal = Control.SIZE_FILL
	_content.add_child(_doll_scroll)
	_sheet_scroll = _scroll_pane(_build_sheet())
	_sheet_scroll.size_flags_stretch_ratio = 1.15
	_content.add_child(_sheet_scroll)
	_bag = _build_bag()
	_content.add_child(_bag)
	_detail_tabs = TabContainer.new()
	_detail_tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_detail_tabs.visible = false
	_content.add_child(_detail_tabs)
	_apply_layout()
	Events.tempo_changed.connect(func(_u): if visible: refresh())

func _build_doll() -> Control:
	var col := vbox(8)
	col.custom_minimum_size = Vector2.ZERO
	var well := inset(Vector2(400, 560))
	col.add_child(well)
	var doll := Control.new()
	doll.custom_minimum_size = Vector2(370, 540)
	well.add_child(doll)
	preview = CharacterPreview.new(Vector2i(520, 800))
	preview.position = Vector2(70, 6)
	preview.size = Vector2(230, 400)
	preview.custom_minimum_size = Vector2(230, 400)
	doll.add_child(preview)
	for slot in SLOT_LAYOUT:
		var pos: Array = SLOT_LAYOUT[slot]
		var s := _equip_slot(slot)
		s.position = Vector2(14 if pos[0] == 0 else 290, 6 + pos[1] * 80)
		doll.add_child(s)
	var main := _equip_slot(&"main_weapon", 84.0)
	main.position = Vector2(95, 420)
	doll.add_child(main)
	var sub := _equip_slot(&"sub_weapon", 84.0)
	sub.position = Vector2(190, 420)
	doll.add_child(sub)
	_weapon_label = UITheme.label("", 14, UITheme.TEXT_DIM, UITheme.body_font())
	_weapon_label.position = Vector2(0, 508)
	_weapon_label.size = Vector2(370, 40)
	_weapon_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_weapon_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	doll.add_child(_weapon_label)
	_cap_label = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_cap_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_cap_label.custom_minimum_size = Vector2.ZERO
	col.add_child(_cap_label)
	var rel := button("Release this spirit", _release, &"", 240.0)
	rel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	col.add_child(rel)
	return col

func _equip_slot(slot: StringName, px := 68.0) -> ItemSlot:
	var s := ItemSlot.new(ItemSlot.Kind.EQUIPMENT, px)
	s.equip_slot = slot
	s.glyph = UIArt.tex("slots/glyph_%s.png" % InventoryWindow.GLYPH[slot])
	s.size = Vector2(px, px)
	s.clicked.connect(func(sl: ItemSlot, b: int, _s: bool, _c: bool) -> void:
		if b == MOUSE_BUTTON_RIGHT and sl.item:
			_unequip(sl.equip_slot))
	s.double_clicked.connect(func(sl: ItemSlot) -> void: _unequip(sl.equip_slot))
	s.dropped.connect(_on_drop)
	s.hovered.connect(_on_hover)
	equip_slots[slot] = s
	return s

func _build_sheet() -> Control:
	var col := vbox(6)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var head := vbox(4)
	col.add_child(head)
	_name = UITheme.title("", 25, UITheme.PARCHMENT)
	_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	head.add_child(_name)
	_state = UITheme.label("", 16, UITheme.GOOD, UITheme.body_bold())
	_state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	head.add_child(_state)
	_class_line = UITheme.label("", 17, UITheme.GOLD, UITheme.body_bold())
	_class_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(_class_line)
	_hp_bar = ArtBar.new("hud/bar_frame_target.png", Color(0.3, 0.85, 0.72), 30.0)
	_hp_bar.custom_minimum_size = Vector2(0, 30)
	col.add_child(_hp_bar)
	_mp_bar = ArtBar.new("hud/bar_frame_target.png", Color(0.25, 0.45, 0.95), 24.0)
	_mp_bar.custom_minimum_size = Vector2(0, 24)
	col.add_child(_mp_bar)
	_strength_head = section("Strength (half of yours, plus its gear)")
	(_strength_head.get_child(0) as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(_strength_head)
	var st := inset(Vector2.ZERO)
	col.add_child(st)
	_stats_grid = GridContainer.new()
	_stats_grid.columns = 4
	_stats_grid.add_theme_constant_override("h_separation", 14)
	_stats_grid.add_theme_constant_override("v_separation", 2)
	st.add_child(_stats_grid)
	col.add_child(section("Skills"))
	_skills_box = vbox(4)
	col.add_child(_skills_box)
	_about = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_about.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_about.custom_minimum_size = Vector2.ZERO
	col.add_child(_about)
	return col

func _build_bag() -> Control:
	var col := vbox(8)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(section("Your bag"))
	var hint := UITheme.label("Right-click an item (or drag it onto a slot) to give it to your Tempo. Right-click an equipped piece to take it back.", 14, UITheme.TEXT_DIM, UITheme.body_font())
	_bag_hint = hint
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size = Vector2.ZERO
	col.add_child(hint)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.custom_minimum_size = Vector2(0, 120)
	_bag_scroll = sc
	# SHOW_NEVER does not propagate the grid's old width into its parent while
	# the responsive column count settles after a viewport change.
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	col.add_child(sc)
	var grid := GridContainer.new()
	_bag_grid = grid
	grid.columns = 7
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	sc.add_child(grid)
	for i in Inventory.COLUMNS * Inventory.ROWS:
		var s := ItemSlot.new(ItemSlot.Kind.INVENTORY, 62.0)
		s.index = i
		s.clicked.connect(func(sl: ItemSlot, b: int, _s: bool, _c: bool) -> void:
			if b == MOUSE_BUTTON_RIGHT and sl.item:
				_equip(sl.item, &""))
		s.double_clicked.connect(func(sl: ItemSlot) -> void:
			if sl.item:
				_equip(sl.item, &""))
		s.dropped.connect(_on_drop)
		s.hovered.connect(_on_hover)
		grid.add_child(s)
		cells.append(s)
	return col

func _scroll_pane(child: Control) -> ScrollContainer:
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	sc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	child.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(child)
	return sc

func open() -> void:
	if _built:
		_apply_layout()
	super.open()

func _apply_layout() -> void:
	_layout_viewport = get_viewport_rect().size
	var compact := _layout_viewport.x < 1600 or Settings.touch_mode
	if compact != _compact:
		_compact = compact
		if compact:
			_sheet_scroll.reparent(_detail_tabs)
			_bag.reparent(_detail_tabs)
			_detail_tabs.set_tab_title(0, "Details")
			_detail_tabs.set_tab_title(1, "Your bag")
		else:
			_sheet_scroll.reparent(_content)
			_bag.reparent(_content)
			_content.move_child(_sheet_scroll, 1)
			_content.move_child(_bag, 2)
			_sheet_scroll.show()
			_bag.show()
	_detail_tabs.visible = compact
	_bag_hint.text = "Double-tap an item to equip it on your Tempo. Double-tap equipped gear to return it to your bag." if Settings.touch_mode else "Right-click or double-click an item to equip it on your Tempo. Drag it onto a slot to choose where it goes; right-click equipped gear to take it back."
	_sheet_scroll.custom_minimum_size.x = 0 if compact else 490
	_stats_grid.columns = 2 if compact else 4
	# Keep the actual frame and its title/close controls inside the same bounds.
	var next_size := Vector2(minf(1640, _layout_viewport.x - 48), minf(900, _layout_viewport.y - 160))
	next_size = next_size.max(Vector2(880, 460))
	var dx := next_size.x - window_size.x
	for child in _root.get_children():
		if child == _frame:
			continue
		child.position.x += dx if child is TextureButton else dx * 0.5
	window_size = next_size
	_root.offset_left = -window_size.x * 0.5
	_root.offset_right = window_size.x * 0.5
	_root.offset_top = -window_size.y * 0.5
	_root.offset_bottom = window_size.y * 0.5
	_root.pivot_offset = window_size * 0.5
	_frame.custom_minimum_size = window_size
	_frame.size = window_size
	_root.scale = Vector2.ONE * fit_scale()

# ---- Refresh -----------------------------------------------------------------------------------------------------------

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	if current == null or not hero.tempos.has(current):
		current = hero.tempos[0] if not hero.tempos.is_empty() else null
	# rebuilding the tabs emits tab_changed, whose handler calls refresh(): keep the bar quiet while it is rebuilt
	_tabs.set_block_signals(true)
	_tabs.clear_tabs()
	for t in hero.tempos:
		_tabs.add_tab("%s%s" % [t.tempo_name, "  (fallen)" if t.fallen else ""], DataTempos.class_icon(t.class_id))
		_tabs.set_tab_icon_max_width(_tabs.tab_count - 1, 28)
	_tabs.visible = not hero.tempos.is_empty()
	if current:
		_tabs.current_tab = hero.tempos.find(current)
	_tabs.set_block_signals(false)
	_content.visible = current != null
	_empty.visible = current == null
	_empty.text = "You have no Tempos.\n\nVeyra Ashgrave, the Tempo-Caller, keeps the Shrine of the Fallen east of the terrace stair in Malasugue. Spirits of warriors who died fighting monsters answer her call, and she will bind up to two of them to you."
	if current == null:
		return
	var t := current
	var lvl := hero.progress.level
	_stats = TempoRules.compute(t, TempoRules.hero_mirror(hero), lvl, hero.cls)
	preview.show_tempo(t, lvl)
	var td := t.class_def()
	_name.text = t.full_name()
	_class_line.text = "%s — %s  ·  %s  ·  %s spirit (%d%% of your strength)" % [td.name, td.role, t.trait_def().get("name", ""),
		t.grade_name(), roundi(t.mirror() * 100.0)]
	_class_line.add_theme_color_override("font_color", td.get("color", UITheme.GOLD))
	(_strength_head.get_child(0) as Label).text = "Strength (%d%% of yours, plus its gear)" % roundi(t.mirror() * 100.0)
	for s in equip_slots:
		var it := t.equipment.get_item(s)
		(equip_slots[s] as ItemSlot).set_item(it)
	var lo := TempoRules.loadout(t, lvl)
	_weapon_label.text = ("Fights with its ghost %s (equip a weapon to hit harder)" % lo.main_type.display_name.to_lower()) if t.equipment.get_item(&"main_weapon") == null and lo.main_type else \
		"Wields: %s" % ", ".join((td.weapons as Array).map(func(w): return DB.weapon_type(w).display_name if DB.weapon_type(w) else String(w)))
	_cap_label.text = "Gear limit: %s rarity (one tier below yours). Level requirements follow your level; spirits ignore attribute requirements." % BH.rarity_name(TempoRules.best_wearable_rarity(hero))
	_refresh_stats()
	_refresh_skills()
	_about.text = "%s\n\"%s\"  %s\nMonsters felled: %d" % [t.trait_def().get("desc", ""), t.origin, "" if t.fallen else "", t.kills]
	for c in cells:
		var it: ItemInstance = hero.inventory.cells[c.index] if c.index < hero.inventory.cells.size() else null
		var usable := it != null and it.is_equipment() and TempoRules.equip_error(hero, t, it) == ""
		c.set_item(it, it != null and it.is_equipment() and not usable)
		c.dim = it != null and not it.is_equipment()
	_update_live()

func _refresh_stats() -> void:
	for c in _stats_grid.get_children():
		c.queue_free()
	for row in STAT_ROWS:
		var k: StringName = row[0]
		var n := UITheme.label(row[1], 17, UITheme.TEXT_DIM, UITheme.body_font())
		n.mouse_filter = Control.MOUSE_FILTER_PASS
		var v := UITheme.label(StatDefs.format_value(k, _stats.get_stat(k)), 17, UITheme.PARCHMENT, UITheme.number_font())
		v.mouse_filter = Control.MOUSE_FILTER_PASS
		var d := _stats
		TooltipLayer.attach(n, func() -> Control: return Tips.stat(k, d))
		TooltipLayer.attach(v, func() -> Control: return Tips.stat(k, d))
		_stats_grid.add_child(n)
		_stats_grid.add_child(v)
	var wr := StatCalculator.weapon_range(_stats, 0)
	var dn := UITheme.label("Weapon Damage", 17, UITheme.TEXT_DIM, UITheme.body_font())
	_stats_grid.add_child(dn)
	_stats_grid.add_child(UITheme.label("%d–%d" % [roundi(wr.x), roundi(wr.y)], 17, UITheme.PARCHMENT, UITheme.number_font()))

func _refresh_skills() -> void:
	for c in _skills_box.get_children():
		c.queue_free()
	for sid in current.skills:
		var sk := DataTempos.skill(sid)
		var row := hbox(10)
		var ic := TextureRect.new()
		ic.texture = DataTempos.skill_icon(sid)
		ic.custom_minimum_size = Vector2(44, 44)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(ic)
		var v := vbox(0)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var heal := DataTempos.is_heal(sid)
		var skill_name := UITheme.label("%s%s" % [sk.name, "  (heals you)" if heal else ""], 17, UITheme.GOOD if heal else UITheme.PARCHMENT, UITheme.body_bold())
		skill_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(skill_name)
		v.add_child(UITheme.label("%d mana · %d s cooldown" % [roundi(float(sk.mana)), roundi(maxf(SkillDef.MIN_COOLDOWN, float(sk.cooldown)))], 15, UITheme.MANA.lightened(0.3), UITheme.number_font()))
		row.add_child(v)
		var desc := String(sk.desc)
		TooltipLayer.attach(row, func() -> Control: return Tips.text(desc, sk.name))
		_skills_box.add_child(row)

func _process(delta: float) -> void:
	if not visible:
		return
	if get_viewport_rect().size != _layout_viewport:
		_apply_layout()
	# Wrapped labels briefly report their pre-layout height when a page changes.
	# PanelContainer grows to that minimum but will not shrink itself afterward.
	if not _frame.size.is_equal_approx(window_size):
		_frame.size = window_size
	if _bag_scroll.size.x > 0:
		_bag_grid.columns = maxi(1, floori((_bag_scroll.size.x - 16.0) / 66.0))
	if _sheet_scroll.size.x > 0:
		_stats_grid.columns = 4 if _sheet_scroll.size.x >= 490 else 2
	_live_t -= delta
	if _live_t <= 0.0:
		_live_t = 0.1
		_update_live()

## HP / mana from the live spirit when it is in the world, else from its saved state.
func _update_live() -> void:
	if current == null or _stats == null:
		return
	var a := TempoParty.actor_for(current.uid)
	var mhp := _stats.get_stat(&"max_hp", 1.0)
	var mmp := _stats.get_stat(&"max_mana", 1.0)
	var hp := a.hp if a and a.alive else mhp * (0.0 if current.fallen else current.hp_frac)
	var mp := a.mana if a and a.alive else mmp * (0.0 if current.fallen else current.mana_frac)
	_hp_bar.set_ratio(hp / maxf(1.0, mhp))
	_hp_bar.text = "%d / %d" % [ceili(hp), roundi(mhp)]
	_mp_bar.set_ratio(mp / maxf(1.0, mmp))
	_mp_bar.text = "%d / %d" % [floori(mp), roundi(mmp)]
	if current.fallen:
		_state.text = "Fallen — Veyra Ashgrave can call it back"
		_state.add_theme_color_override("font_color", UITheme.BAD)
	elif a:
		_state.text = a.mode_name()
		_state.add_theme_color_override("font_color", UITheme.GOOD)
	else:
		_state.text = "Resting"
		_state.add_theme_color_override("font_color", UITheme.TEXT_DIM)

# ---- Actions -------------------------------------------------------------------------------------------------------------

func _equip(it: ItemInstance, slot: StringName) -> void:
	if current == null:
		return
	var err := TempoRules.equip_from_inventory(hero, current, it, slot)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Audio.play_ui(&"ui_equip")
	TooltipLayer.hide_for(null)
	refresh()

func _unequip(slot: StringName) -> void:
	if current == null:
		return
	var err := TempoRules.unequip_to_inventory(hero, current, slot)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Audio.play_ui(&"ui_unequip")
	TooltipLayer.hide_for(null)
	refresh()

func _on_drop(from: ItemSlot, to: ItemSlot) -> void:
	if from.item == null or current == null:
		return
	if from.kind == ItemSlot.Kind.INVENTORY and to.kind == ItemSlot.Kind.EQUIPMENT:
		_equip(from.item, to.equip_slot)
	elif from.kind == ItemSlot.Kind.EQUIPMENT and to.kind == ItemSlot.Kind.INVENTORY:
		_unequip(from.equip_slot)
	elif from.kind == ItemSlot.Kind.INVENTORY and to.kind == ItemSlot.Kind.INVENTORY:
		hero.inventory.move(from.index, to.index)
		refresh()

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside:
		TooltipLayer.hide_for(s)
		return
	if s.item == null:
		if s.kind == ItemSlot.Kind.EQUIPMENT:
			TooltipLayer.show_for(s, func() -> Control: return Tips.text("Empty. Drag an item here from your bag.", BH.SLOT_NAMES[s.equip_slot]))
		return
	var equipped := s.kind == ItemSlot.Kind.EQUIPMENT
	var hint := "Right-click to take it back" if equipped else ""
	if not equipped and s.item.is_equipment() and current:
		var err := TempoRules.equip_error(hero, current, s.item)
		hint = ("Right-click to give it to %s" % current.tempo_name) if err == "" else "%s cannot use this: %s" % [current.tempo_name, err]
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(s.item, {"hero": hero, "equipped": equipped, "compare": false, "hint": hint}))

func _release() -> void:
	if current == null:
		return
	var t := current
	Game.ui_root.ask("Release %s" % t.tempo_name, "Let %s's spirit go? It will not return, and its gear comes back to your bag." % t.tempo_name,
		func() -> void:
			var err := TempoRules.release(hero, t)
			if err != "":
				Events.notify.emit(err, &"error")
				return
			current = null
			TempoParty.refresh(hero)
			Events.notify.emit("%s's spirit is at rest." % t.tempo_name, &"info")
			refresh(), "Release", true)
