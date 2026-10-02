class_name InventoryWindow
extends UIWindow
## Inventory + Equipment (I). Gear and Utility share 84 slots; consumables have 16 additional belt slots. Left: the hero in 3D on a plinth, the 14 equipment slots around it, a stat summary and
## active set bonuses. Right: category tabs, search, rarity filter, sorting, the bags and separate belt, gold, and an action bar
## for the selected item: Equip/Use, Split, Lock, Favorite, Mark to sell, Drop, Destroy (confirmed).
## Mouse: left select · right Equip/Use · Shift+left Split · drag to move, merge, equip or unequip · double-click Equip.
## Potion Belt row (bh-011): what Q / E (the HP / Mana orbs on a phone) use — click a slot to choose, drop a consumable on
## it, press "Put on Q/E" for the selected consumable, or hover a consumable and press Q or E.

const CELL := 62.0
const SLOT_LAYOUT := {
	# slot: [column (0 left / 1 right), row] — clothing down the left, jewellery down the right, the pairs side by side
	&"helm": [0, 0], &"inner_garment": [0, 1], &"armor": [0, 2], &"leggings": [0, 3], &"gloves_1": [0, 4], &"boots_1": [0, 5],
	&"accessory_1": [1, 0], &"accessory_2": [1, 1], &"accessory_3": [1, 2], &"accessory_4": [1, 3], &"gloves_2": [1, 4], &"boots_2": [1, 5],
}
const GLYPH := {&"main_weapon": "main_weapon", &"sub_weapon": "sub_weapon", &"helm": "helm", &"inner_garment": "inner_garment",
	&"armor": "armor", &"leggings": "leggings", &"gloves_1": "gloves", &"gloves_2": "gloves", &"boots_1": "boots", &"boots_2": "boots",
	&"accessory_1": "accessory", &"accessory_2": "accessory", &"accessory_3": "accessory", &"accessory_4": "accessory"}

var hero: HeroData
var preview: CharacterPreview
var equip_slots := {}             # slot -> ItemSlot
var cells: Array[ItemSlot] = []
var filter := "all"
var min_rarity := 0
var search := ""
var selected: ItemSlot
var _tabs: HFlowContainer
var _category_buttons: Dictionary = {}
var _bag_tabs: TabBar
var bag_view := "all"
var _bag_section: VBoxContainer
var _belt_section: VBoxContainer
var _bag_heading: Label
var _belt_heading: Label
var _empty: Label
var _results: Label
var _reverse: CheckButton
var _grid_scroll: ScrollContainer
var _search: LineEdit
var _rarity: OptionButton
var _sort: OptionButton
var _gold: Label
var _load_bar: ProgressBar
var _load_fill: StyleBoxFlat
var _load_text: Label
var _space: Label
var _summary: GridContainer
var _sets: VBoxContainer
var _actions: HFlowContainer
var _sel_name: Label
var _btn_use: Button
var _btn_split: Button
var _btn_lock: Button
var _btn_fav: Button
var _btn_junk: Button
var _btn_drop: Button
var _btn_destroy: Button
var _belt_slots: Array[SkillButton] = []
var _belt_names: Array[Label] = []
var _btn_belt: Array[Button] = []
var _belt_keys: Array[Button] = []
var _hover_slot: ItemSlot

func _init() -> void:
	super._init("Inventory", Vector2(1680, 1040))

func _build() -> void:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	row.add_child(_build_paper_doll())
	row.add_child(_build_bag())
	body.add_child(_build_belt_strip())

func _build_paper_doll() -> Control:
	var col := vbox(10)
	col.custom_minimum_size = Vector2(620, 0)
	var well := inset(Vector2(620, 600))
	col.add_child(well)
	var doll := Control.new()
	doll.custom_minimum_size = Vector2(590, 570)
	well.add_child(doll)
	preview = CharacterPreview.new(Vector2i(640, 900))
	preview.position = Vector2(150, 10)
	preview.size = Vector2(290, 440)
	preview.custom_minimum_size = Vector2(290, 440)
	doll.add_child(preview)
	for slot in SLOT_LAYOUT:
		var pos: Array = SLOT_LAYOUT[slot]
		var s := _equip_slot(slot)
		s.position = Vector2(20 if pos[0] == 0 else 490, 8 + pos[1] * 88)
		doll.add_child(s)
	var main := _equip_slot(&"main_weapon", 92.0)
	main.position = Vector2(170, 460)
	doll.add_child(main)
	var sub := _equip_slot(&"sub_weapon", 92.0)
	sub.position = Vector2(330, 460)
	doll.add_child(sub)
	for pair in [[main, "Main Weapon"], [sub, "Sub Weapon"]]:
		var l := UITheme.label(pair[1], 14, UITheme.TEXT_DIM, UITheme.body_font())
		l.position = pair[0].position + Vector2(-10, 94)
		l.size = Vector2(112, 20)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		doll.add_child(l)
	var info := hbox(14)
	col.add_child(info)
	var sum_box := inset(Vector2(330, 0))
	info.add_child(sum_box)
	_summary = GridContainer.new()
	_summary.columns = 2
	_summary.add_theme_constant_override("h_separation", 16)
	_summary.add_theme_constant_override("v_separation", 2)
	sum_box.add_child(_summary)
	var set_box := inset(Vector2(270, 0))
	info.add_child(set_box)
	_sets = vbox(2)
	set_box.add_child(_sets)
	return col

## bh-030: the Potion & Scroll Belt, always at the bottom of the window: its 16 cells and the six belt keys (Q, E and
## the quick keys Alt+Q / W / E / R). Click a key slot to choose what it uses (or drop a consumable on it); the small
## key button under each slot changes its key.
func _build_belt_strip() -> Control:
	var box := inset()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var row := hbox(16)
	box.add_child(row)
	var head := vbox(4)
	head.custom_minimum_size = Vector2(150, 0)
	head.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(head)
	head.add_child(UITheme.label("Potion &\nScroll Belt", 20, UITheme.GOLD, UITheme.title_font()))
	_belt_heading = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_belt_heading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	head.add_child(_belt_heading)
	_belt_section = vbox(0)
	_belt_section.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_belt_section)
	_add_grid(_belt_section, Inventory.BAG_CAPACITY, Inventory.BAG_CAPACITY + Inventory.BELT_CAPACITY, 8)
	row.add_child(VSeparator.new())
	var keys := vbox(4)
	keys.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(keys)
	keys.add_child(UITheme.label("Belt Keys" if not Settings.touch_mode else "Belt Slots", 18, UITheme.GOLD, UITheme.body_bold()))
	var slots := hbox(10)
	keys.add_child(slots)
	for i in HeroData.BELT_SIZE:
		var slot := i
		var colv := vbox(3)
		colv.custom_minimum_size = Vector2(104, 0)
		slots.add_child(colv)
		var b := SkillButton.new(HeroData.belt_action(i), 58.0)
		b.set_potion(HeroData.belt_default(i) if i >= HeroData.ORB_SLOTS else (&"health_potion" if i == 0 else &"mana_potion"))
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		b.activated.connect(func(sb: SkillButton) -> void: BeltPicker.open(sb, hero, slot))
		b.context.connect(func(sb: SkillButton) -> void: BeltPicker.open(sb, hero, slot))
		b.item_dropped.connect(func(_sb: SkillButton, it: ItemInstance) -> void: if it: BeltPicker.bind(hero, slot, it.base.id))
		TooltipLayer.attach(b, func() -> Control: return Tips.text("Click to choose what %s uses. You can also drag a consumable here%s." % [
			BeltPicker.slot_name(slot), "" if Settings.touch_mode else ", or hover one in the bag and press %s" % BeltPicker.slot_name(slot)], "Belt Key"))
		colv.add_child(b)
		_belt_slots.append(b)
		var n := UITheme.label("", 13, UITheme.PARCHMENT, UITheme.body_font())
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		n.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		n.custom_minimum_size = Vector2(104, 34)
		colv.add_child(n)
		_belt_names.append(n)
		if not Settings.touch_mode:
			var kb := button("Key: %s" % Settings.binding_text(HeroData.belt_action(i)), func() -> void:
				var c := HotkeyCapture.start(HeroData.belt_action(slot), b)
				if c:
					c.finished.connect(func(_a: StringName, _ok: bool) -> void: _refresh_belt()), &"", 0.0)
			kb.add_theme_font_size_override("font_size", 13)
			kb.custom_minimum_size = Vector2(104, 30)
			kb.set_meta(&"belt_key", i)
			colv.add_child(kb)
			_belt_keys.append(kb)
	return box

func _refresh_belt() -> void:
	for i in _belt_slots.size():
		var bp := hero.belt_preview(i)
		if bp.base != _belt_slots[i].potion_base:
			_belt_slots[i].set_potion(bp.base)
		_belt_slots[i].update_state(0.0, 0.0, "", int(bp.count) if bp.base != &"" else -1)
		_belt_names[i].text = HeroData.belt_label(hero.potion_belt[i])
		_belt_slots[i].queue_redraw()
	for kb in _belt_keys:
		kb.text = "Key: %s" % Settings.binding_text(HeroData.belt_action(int(kb.get_meta(&"belt_key"))))

func _equip_slot(slot: StringName, px := 76.0) -> ItemSlot:
	var s := ItemSlot.new(ItemSlot.Kind.EQUIPMENT, px)
	s.equip_slot = slot
	s.glyph = UIArt.tex("slots/glyph_%s.png" % GLYPH[slot])
	s.size = Vector2(px, px)
	s.clicked.connect(_on_equip_clicked)
	s.double_clicked.connect(func(sl): _unequip(sl.equip_slot))
	s.dropped.connect(_on_drop)
	s.hovered.connect(_on_hover)
	equip_slots[slot] = s
	return s

func _build_bag() -> Control:
	var col := vbox(10)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_bag_tabs = TabBar.new()
	for label in ["All Bags", "Gear Bag", "Utility Bag"]:
		_bag_tabs.add_tab(label)
	_bag_tabs.add_theme_font_size_override("font_size", 20)
	_bag_tabs.add_theme_font_override("font", UITheme.body_bold())
	_bag_tabs.tab_changed.connect(func(i: int) -> void:
		bag_view = ["all", "gear", "utility"][i]
		_select(null)
		_apply_filter())
	col.add_child(_bag_tabs)
	_tabs = HFlowContainer.new()
	_tabs.add_theme_constant_override("h_separation", 6)
	_tabs.add_theme_constant_override("v_separation", 6)
	var group := ButtonGroup.new()
	for k in Inventory.TABS:
		var key: String = k
		var tab := button(Inventory.FILTER_NAMES[k], func() -> void:
			filter = key
			_select(null)
			_apply_filter())
		tab.toggle_mode = true
		tab.button_group = group
		tab.button_pressed = key == "all"
		tab.custom_minimum_size.y = 38
		tab.add_theme_font_size_override("font_size", 18)
		tab.add_theme_font_override("font", UITheme.body_bold())
		for state in ["normal", "hover", "pressed", "focus"]:
			var style := UITheme.button_style(state)
			style.content_margin_left = 10
			style.content_margin_right = 10
			style.content_margin_top = 6
			style.content_margin_bottom = 6
			tab.add_theme_stylebox_override(state, style)
		tab.add_theme_color_override("font_pressed_color", UITheme.GOLD)
		_tabs.add_child(tab)
		_category_buttons[key] = tab
	col.add_child(_tabs)
	var tools := hbox(8)
	col.add_child(tools)
	_search = LineEdit.new()
	_search.placeholder_text = "Search name, rarity or enchantment"
	_search.custom_minimum_size = Vector2(260, 44)
	_search.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_search.clear_button_enabled = true
	_search.text_changed.connect(func(t: String) -> void:
		search = t
		_select(null)
		_apply_filter())
	tools.add_child(_search)
	_rarity = OptionButton.new()
	_rarity.add_item("Any rarity")
	for i in range(1, BH.RARITY_COUNT):
		_rarity.add_item("%s or better" % BH.RARITY_NAMES[i])
	_rarity.item_selected.connect(func(i: int) -> void:
		min_rarity = i
		_select(null)
		_apply_filter())
	_rarity.custom_minimum_size = Vector2(210, 44)
	tools.add_child(_rarity)
	tools.add_child(button("Clear", func() -> void:
		filter = "all"
		min_rarity = 0
		search = ""
		_search.text = ""
		_rarity.select(0)
		_category_buttons["all"].button_pressed = true
		_select(null)
		_apply_filter()))
	var sorting := hbox(10)
	col.add_child(sorting)
	_sort = OptionButton.new()
	for m in ["Rarity", "Category", "Item level", "Name", "Value", "Weight"]:
		_sort.add_item("Sort: " + m)
	_sort.custom_minimum_size = Vector2(210, 42)
	_sort.item_selected.connect(func(_i: int) -> void: _sort_bags())
	sorting.add_child(_sort)
	_reverse = CheckButton.new()
	_reverse.text = "Reverse order"
	_reverse.toggled.connect(func(_on: bool) -> void: _sort_bags())
	sorting.add_child(_reverse)
	sorting.add_child(button("Sort bags", _sort_bags))
	sorting.add_child(button("Auto-Loot Filters", func() -> void:
		if Game.ui_root: Game.ui_root.open(&"auto_loot")))
	_results = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	col.add_child(_results)
	_grid_scroll = ScrollContainer.new()
	_grid_scroll.custom_minimum_size.y = 310
	_grid_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_grid_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	col.add_child(_grid_scroll)
	var sections := vbox(12)
	sections.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_grid_scroll.add_child(sections)
	_bag_section = vbox(8)
	sections.add_child(_bag_section)
	_bag_heading = UITheme.label("Gear & Utility Bags · 84 shared slots", 19, UITheme.GOLD, UITheme.body_bold())
	_bag_section.add_child(_bag_heading)
	_add_grid(_bag_section, 0, Inventory.BAG_CAPACITY, 12)
	_empty = UITheme.label("No items match these filters.", 20, UITheme.TEXT_DIM, UITheme.body_font())
	sections.add_child(_empty)
	var status := hbox(10)
	col.add_child(status)
	var gi := TextureRect.new()
	gi.texture = UIArt.ui_icon("gold")
	gi.custom_minimum_size = Vector2(26, 26)
	gi.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	gi.modulate = UITheme.GOLD
	status.add_child(gi)
	_gold = UITheme.label("", 22, UITheme.GOLD, UITheme.number_font())
	status.add_child(_gold)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	status.add_child(sp)
	_space = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	status.add_child(_space)
	# carried load (bh-006): worn + bagged weight against capacity (Strength); slows you from 35%, 100% = no dodging
	var lrow := hbox(10)
	col.add_child(lrow)
	var lt := UITheme.label("Load", 16, UITheme.TEXT_DIM, UITheme.body_bold())
	lrow.add_child(lt)
	_load_bar = ProgressBar.new()
	_load_bar.show_percentage = false
	_load_bar.max_value = 1.0
	_load_bar.step = 0.001
	_load_bar.custom_minimum_size = Vector2(260, 14)
	_load_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var lbg := StyleBoxFlat.new()
	lbg.bg_color = Color(0, 0, 0, 0.5)
	lbg.set_corner_radius_all(3)
	_load_bar.add_theme_stylebox_override("background", lbg)
	_load_fill = StyleBoxFlat.new()
	_load_fill.set_corner_radius_all(3)
	_load_bar.add_theme_stylebox_override("fill", _load_fill)
	lrow.add_child(_load_bar)
	_load_text = UITheme.label("", 16, UITheme.PARCHMENT, UITheme.number_font())
	_load_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lrow.add_child(_load_text)
	TooltipLayer.attach(lrow, func() -> Control: return Tips.stat(&"load", hero.compute_stats()) if hero else null)
	# selected-item action bar
	var act := inset()
	col.add_child(act)
	var av := vbox(6)
	act.add_child(av)
	_sel_name = UITheme.label("Select an item", 19, UITheme.TEXT_DIM, UITheme.body_bold())
	_sel_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	av.add_child(_sel_name)
	_actions = HFlowContainer.new()
	_actions.add_theme_constant_override("h_separation", 6)
	_actions.add_theme_constant_override("v_separation", 6)
	av.add_child(_actions)
	_btn_use = button("Equip", func() -> void: _use(_sel_item()), &"PrimaryButton", 120.0)
	_btn_split = button("Split", func() -> void: _split_dialog(_sel_item()), &"", 96.0)
	_btn_lock = button("Lock", func() -> void: _toggle_flag("locked"), &"", 96.0)
	_btn_fav = button("Favorite", func() -> void: _toggle_flag("favorite"), &"", 120.0)
	_btn_junk = button("Mark to Sell", func() -> void: _toggle_flag("junk"), &"", 150.0)
	_btn_drop = button("Drop", func() -> void: _drop(_sel_item()), &"", 96.0)
	_btn_destroy = button("Destroy", func() -> void: _destroy(_sel_item()), &"", 120.0)
	for i in HeroData.ORB_SLOTS:
		var slot := i
		_btn_belt.append(button("Put on %s" % BeltPicker.slot_name(i), func() -> void:
			if _sel_item():
				BeltPicker.bind(hero, slot, _sel_item().base.id), &"", 150.0))
	# bh-030: the quick keys share one button: a menu of the four
	var quick_btn: Button
	quick_btn = button("Put on Quick Key", func() -> void:
		if _sel_item() == null:
			return
		var menu := PopupMenu.new()
		menu.add_theme_font_size_override("font_size", 22 if Settings.touch_mode else 17)
		for q in range(HeroData.ORB_SLOTS, HeroData.BELT_SIZE):
			menu.add_item("%s  (now: %s)" % [BeltPicker.slot_name(q), HeroData.belt_label(hero.potion_belt[q])], q)
		var base_id: StringName = _sel_item().base.id
		menu.id_pressed.connect(func(q: int) -> void: BeltPicker.bind(hero, q, base_id))
		menu.popup_hide.connect(menu.queue_free)
		get_tree().root.add_child(menu)
		var k := get_viewport().get_final_transform().x.x
		menu.reset_size()
		var at := quick_btn.get_global_rect().position - Vector2(0, menu.size.y / maxf(k, 0.01) + 6.0)
		menu.popup(Rect2i(Vector2i((at * k).round()), Vector2i.ZERO)), &"", 190.0)
	_btn_belt.append(quick_btn)
	for b in [_btn_use, _btn_split, _btn_lock, _btn_fav, _btn_junk, _btn_drop, _btn_destroy]:
		b.add_theme_font_override("font", UITheme.body_bold())
		b.custom_minimum_size.y = 46
		_actions.add_child(b)
	var belt_row := hbox(6)
	av.add_child(belt_row)
	for b in _btn_belt:
		b.add_theme_font_override("font", UITheme.body_bold())
		b.custom_minimum_size.y = 46
		belt_row.add_child(b)
	var hint := UITheme.label("Hold: equip or use · Drag onto a slot to equip · Double-tap an equipped item to remove it · Split with the Split button" if Settings.touch_mode else "Right-click: equip or use · Shift+click: split stack · Drag onto a slot to equip · Double-click an equipped item to remove it",
		14, UITheme.TEXT_MUTED, UITheme.body_font())
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(hint)
	return col

# ---- Refresh -------------------------------------------------------------------------------------------------------

func refresh() -> void:
	var h := Game.hero
	if h != hero:
		if hero:
			if hero.inventory_changed.is_connected(_refresh_items):
				hero.inventory_changed.disconnect(_refresh_items)
			if hero.stats_dirty.is_connected(_refresh_items):
				hero.stats_dirty.disconnect(_refresh_items)
		hero = h
		if hero:
			hero.inventory_changed.connect(_refresh_items)
			hero.stats_dirty.connect(_refresh_items)
	if hero == null:
		return
	preview.show_class(hero.cls.id, hero)
	_refresh_items()

func _refresh_items() -> void:
	if hero == null or not visible:
		return
	var lvl := hero.progress.level
	var attrs := hero.progress.base_attributes()
	for s in equip_slots:
		equip_slots[s].set_item(hero.equipment.get_item(s))
	for i in cells.size():
		var it: ItemInstance = hero.inventory.cells[i]
		var unusable := it != null and it.is_equipment() and hero.equipment.check(it, hero.equipment.auto_slot(it), lvl, attrs) != "" \
			and not hero.equipment.check(it, hero.equipment.auto_slot(it), lvl, attrs).begins_with("Equip a main")
		cells[i].set_item(it, unusable)
	_apply_filter()
	_gold.text = _fmt_gold(hero.inventory.gold)
	_space.text = "%d / 84 bag slots free · %d / 16 belt slots free" % [hero.inventory.free_cells(), hero.inventory.free_cells(true) - hero.inventory.free_cells()]
	_refresh_load()
	preview.dress(hero)
	_refresh_summary()
	_refresh_belt()
	_update_actions()

func _refresh_load() -> void:
	var p := Game.player as Player
	if p and p.hero == hero:
		p.ensure_stats()          # the bag just changed: recompute before reading (else one change behind the HUD)
	var d: DerivedStats = p.stats if p and p.hero == hero and p.stats else hero.compute_stats()
	var load := d.get_stat(&"load")
	_load_bar.value = clampf(load, 0.0, 1.0)
	var col := Color(0.45, 0.8, 0.4)
	var note := "no slowdown"
	var slow := 1.0 - StatCalculator.load_move_mult(load)
	if load >= 1.0:
		col = Color(0.95, 0.25, 0.2)
		note = "Overburdened: %d%% slower, cannot dodge" % roundi(slow * 100.0)
	elif slow > 0.0:
		col = Color(0.95, 0.7, 0.25)
		note = "%d%% slower" % roundi(slow * 100.0)
	_load_fill.bg_color = col
	_load_text.text = "%.1f / %.0f  (%d%%) · %s" % [d.get_stat(&"carry_weight"), d.get_stat(&"carry_capacity"), roundi(load * 100.0), note]

func _add_grid(parent: Control, start: int, end: int, columns: int) -> void:
	var well := inset()
	parent.add_child(well)
	var grid := GridContainer.new()
	grid.columns = columns
	grid.add_theme_constant_override("h_separation", 5)
	grid.add_theme_constant_override("v_separation", 5)
	well.add_child(grid)
	for i in range(start, end):
		var c := ItemSlot.new(ItemSlot.Kind.INVENTORY, CELL)
		c.index = i
		c.clicked.connect(_on_cell_clicked)
		c.double_clicked.connect(func(sl): _use(sl.item))
		c.dropped.connect(_on_drop)
		c.hovered.connect(_on_hover)
		grid.add_child(c)
		cells.append(c)

func _sort_bags() -> void:
	if hero == null:
		return
	_select(null)
	hero.inventory.sort(Inventory.SORT_MODES[_sort.selected], _reverse.button_pressed)

func _apply_filter() -> void:
	if hero == null:
		return
	var matches := 0
	var bag_visible := 0
	var filtering := filter != "all" or min_rarity > 0 or search.strip_edges() != ""
	for c in cells:
		var in_belt := c.index >= hero.inventory.bag_capacity
		if in_belt:
			# bh-030: the belt strip never hides a cell; filters only dim what does not match
			c.visible = true
			c.dim = filtering and (c.item == null or not Inventory.matches_filter(c.item, filter, min_rarity, search))
			if c.item and not c.dim:
				matches += 1
			c.queue_redraw()
			continue
		var in_view := bag_view == "all"
		if bag_view in ["gear", "utility"]:
			in_view = c.item == null or hero.inventory.bag_of(c.index) == bag_view
		c.visible = in_view and (Inventory.matches_filter(c.item, filter, min_rarity, search) if c.item else not filtering)
		c.dim = false
		if c.visible:
			bag_visible += 1
			if c.item: matches += 1
		c.queue_redraw()
	_bag_section.visible = bag_visible > 0
	_empty.visible = bag_visible == 0
	_bag_heading.text = "%s · %d / 84 shared slots free" % [{"all": "Gear & Utility Bags", "gear": "Gear Bag", "utility": "Utility Bag"}.get(bag_view, "Bags"), hero.inventory.free_cells()]
	_belt_heading.text = "%d / 16 slots free" % (hero.inventory.free_cells(true) - hero.inventory.free_cells())
	_results.text = "%d item stacks · Favorites first · Gear and Utility share space" % matches
	if selected and selected.kind == ItemSlot.Kind.INVENTORY and not selected.visible:
		_select(null)

func _refresh_summary() -> void:
	for c in _summary.get_children():
		c.queue_free()
	var d := hero.compute_stats()
	var rows := [["Damage", "%d – %d" % [roundi(d.get_stat(&"weapon_min")), roundi(d.get_stat(&"weapon_max"))], &"weapon_min"],
		["Defense", str(roundi(d.get_stat(&"defense"))), &"defense"], ["Maximum HP", str(roundi(d.get_stat(&"max_hp"))), &"max_hp"],
		["Maximum Mana", str(roundi(d.get_stat(&"max_mana"))), &"max_mana"], ["Critical Chance", StatDefs.format_value(&"crit_chance", d.get_stat(&"crit_chance")), &"crit_chance"],
		["Block Chance", StatDefs.format_value(&"block_chance", d.get_stat(&"block_chance")), &"block_chance"]]
	for r in rows:
		var n := UITheme.label(r[0], 16, UITheme.TEXT_DIM, UITheme.body_font())
		n.mouse_filter = Control.MOUSE_FILTER_PASS
		var key: StringName = r[2]
		TooltipLayer.attach(n, func() -> Control: return Tips.stat(key, d))
		_summary.add_child(n)
		_summary.add_child(UITheme.label(r[1], 16, UITheme.PARCHMENT, UITheme.number_font()))
	for c in _sets.get_children():
		c.queue_free()
	_sets.add_child(UITheme.label("Item Sets", 16, UITheme.GOLD, UITheme.title_font()))
	var counts := hero.equipment.set_counts()
	if counts.is_empty():
		_sets.add_child(UITheme.label("No set pieces equipped.", 14, UITheme.TEXT_MUTED, UITheme.body_font()))
	for sid in counts:
		var sd := DB.item_set(sid)
		if sd == null:
			continue
		_sets.add_child(UITheme.label("%s (%d/%d)" % [sd.display_name, counts[sid], sd.pieces.size()], 15, UITheme.PARCHMENT, UITheme.body_bold()))
		for n in sd.thresholds():
			var l := UITheme.label("(%d) %s" % [n, sd.bonuses[n].get("desc", "")], 13, Tips.SET_ON if counts[sid] >= int(n) else Tips.SET_OFF, UITheme.body_font())
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l.custom_minimum_size = Vector2(240, 0)
			_sets.add_child(l)

static func _fmt_gold(n: int) -> String:
	var s := str(n)
	var out := ""
	var c := 0
	for i in range(s.length() - 1, -1, -1):
		out = s[i] + out
		c += 1
		if c % 3 == 0 and i > 0:
			out = "," + out
	return out

# ---- Selection & actions -----------------------------------------------------------------------------------------

func _sel_item() -> ItemInstance:
	return selected.item if selected and is_instance_valid(selected) else null

func _select(s: ItemSlot) -> void:
	if selected and is_instance_valid(selected):
		selected.selected = false
		selected.queue_redraw()
	selected = s if s != null and s.item != null else null
	if selected:
		selected.selected = true
		selected.queue_redraw()
	_update_actions()

func _update_actions() -> void:
	var it := _sel_item()
	var has := it != null
	_sel_name.text = it.display_name() if has else "Select an item"
	_sel_name.add_theme_color_override("font_color", it.color() if has else UITheme.TEXT_DIM)
	var equipped := has and selected.kind == ItemSlot.Kind.EQUIPMENT
	_btn_use.disabled = not has or not (it.is_equipment() or it.base.is_consumable())
	_btn_use.text = "Unequip" if equipped else ("Use" if has and it.base.is_consumable() else "Equip")
	_btn_split.disabled = not has or equipped or it.count < 2
	_btn_lock.disabled = not has
	_btn_lock.text = "Unlock" if has and it.locked else "Lock"
	_btn_fav.disabled = not has
	_btn_fav.text = "Unfavorite" if has and it.favorite else "Favorite"
	_btn_junk.disabled = not has or not it.base.sellable or equipped
	_btn_junk.text = "Keep" if has and it.junk else "Mark to Sell"
	_btn_drop.disabled = not has or it.is_protected() or it.base.is_quest() or equipped
	_btn_destroy.disabled = not has or it.is_protected() or it.base.is_quest() or equipped
	# a consumable can go on the potion belt; the belt buttons replace Drop/Destroy's neighbours only while it is selected
	for i in _btn_belt.size():
		_btn_belt[i].visible = has and it.base.is_consumable() and not equipped
		_btn_belt[i].text = "Put on %s" % BeltPicker.slot_name(i)

func _on_cell_clicked(s: ItemSlot, button: int, shift: bool, _ctrl: bool) -> void:
	if s.item == null:
		_select(null)
		return
	if button == MOUSE_BUTTON_RIGHT:
		_use(s.item)
		return
	if shift and s.item.count > 1:
		_split_dialog(s.item)
		return
	_select(s)
	Audio.play_ui(&"ui_click")

func _on_equip_clicked(s: ItemSlot, button: int, _shift: bool, _ctrl: bool) -> void:
	if s.item == null:
		_select(null)
		return
	if button == MOUSE_BUTTON_RIGHT:
		_unequip(s.equip_slot)
		return
	_select(s)

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside:
		if _hover_slot == s:
			_hover_slot = null
		TooltipLayer.hide_for(s)
		return
	_hover_slot = s
	if s.item == null:
		if s.kind == ItemSlot.Kind.EQUIPMENT:
			TooltipLayer.show_for(s, func() -> Control: return Tips.text("Empty. Drag an item here to equip it.", BH.SLOT_NAMES[s.equip_slot]))
		return
	var equipped := s.kind == ItemSlot.Kind.EQUIPMENT
	var hint := "Right-click to unequip" if equipped else ("Right-click to use" if s.item.base.is_consumable() else ("Right-click to equip" if s.item.is_equipment() else ""))
	if not equipped and s.item.base.is_consumable() and not Settings.touch_mode:
		hint += " · %s / %s / %s...: put on that belt key" % [BeltPicker.slot_name(0), BeltPicker.slot_name(1), BeltPicker.slot_name(2)]
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(s.item, {"hero": hero, "equipped": equipped, "hint": hint}))

## Hover a consumable in the bag and press a belt key (Q / E): that key now uses it.
func _unhandled_input(e: InputEvent) -> void:
	if not visible or hero == null or _hover_slot == null or not is_instance_valid(_hover_slot) or _hover_slot.item == null:
		return
	if _hover_slot.kind != ItemSlot.Kind.INVENTORY or not _hover_slot.item.base.is_consumable():
		return
	# quick keys first: Alt+Q also matches Q
	for i in range(HeroData.BELT_SIZE - 1, -1, -1):
		if e.is_action_pressed(HeroData.belt_action(i)):
			BeltPicker.bind(hero, i, _hover_slot.item.base.id)
			get_viewport().set_input_as_handled()
			return

func _use(it: ItemInstance) -> void:
	if it == null:
		return
	if selected and selected.kind == ItemSlot.Kind.EQUIPMENT and selected.item == it:
		_unequip(selected.equip_slot)
		return
	if it.base.is_consumable():
		var p := Game.player as Player
		if p and p.consume_item(it):
			Audio.play_ui(&"ui_click")
		return
	if it.is_equipment():
		var err := hero.equip_from_inventory(it)
		if err != "":
			Events.notify.emit(err, &"error")
			Audio.play_ui(&"ui_error")
		else:
			Audio.play_ui(&"ui_equip")
			Events.item_equipped.emit(it, hero.equipment.slot_of(it))
			_select(null)
		TooltipLayer.hide_for(null)

func _unequip(slot: StringName) -> void:
	var err := hero.unequip_to_inventory(slot)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Audio.play_ui(&"ui_unequip")
		_select(null)
	TooltipLayer.hide_for(null)

func _on_drop(from: ItemSlot, to: ItemSlot) -> void:
	if from.item == null:
		return
	# bag -> bag: move / merge / swap
	if from.kind == ItemSlot.Kind.INVENTORY and to.kind == ItemSlot.Kind.INVENTORY:
		if not hero.inventory.accepts(to.index, from.item) or not hero.inventory.accepts(from.index, to.item):
			Events.notify.emit("The belt holds consumables, potions and scrolls", &"error")
			return
		hero.inventory.move(from.index, to.index)
		_select(null)
		return
	# bag -> equipment slot: equip into that exact slot
	if from.kind == ItemSlot.Kind.INVENTORY and to.kind == ItemSlot.Kind.EQUIPMENT:
		var err := hero.equip_from_inventory(from.item, to.equip_slot)
		if err != "":
			Events.notify.emit(err, &"error")
			Audio.play_ui(&"ui_error")
		else:
			Audio.play_ui(&"ui_equip")
		return
	# equipment -> bag: unequip (into that cell when it is empty)
	if from.kind == ItemSlot.Kind.EQUIPMENT and to.kind == ItemSlot.Kind.INVENTORY:
		if not hero.inventory.accepts(to.index, from.item):
			Events.notify.emit("Equipment belongs in the Gear Bag", &"error")
			return
		if to.item == null:
			var it := hero.equipment.get_item(from.equip_slot)
			var err := hero.unequip_to_inventory(from.equip_slot)
			if err == "":
				var at := hero.inventory.index_of(it)
				if at >= 0 and at != to.index and hero.inventory.cells[to.index] == null:
					hero.inventory.move(at, to.index)
				Audio.play_ui(&"ui_unequip")
			else:
				Events.notify.emit(err, &"error")
		else:
			# dropping an equipped item onto a bag item: equip the bag item into this slot (a swap)
			var err2 := hero.equip_from_inventory(to.item, from.equip_slot)
			if err2 != "":
				Events.notify.emit(err2, &"error")
		return
	# equipment -> equipment (two rings, two gloves): swap
	if from.kind == ItemSlot.Kind.EQUIPMENT and to.kind == ItemSlot.Kind.EQUIPMENT:
		var err3 := hero.swap_equipped(from.equip_slot, to.equip_slot)
		if err3 != "":
			Events.notify.emit(err3, &"error")

func _toggle_flag(flag: String) -> void:
	var it := _sel_item()
	if it == null:
		return
	it.set(flag, not bool(it.get(flag)))
	if flag == "junk" and it.junk:
		it.favorite = false
	hero.inventory.changed.emit()
	_update_actions()

func _drop(it: ItemInstance) -> void:
	if it == null or it.is_protected():
		return
	var p := Game.player as Node3D
	if not hero.inventory.remove_item(it):
		return
	if p and Game.current_map:
		Loot.spawn_item(it, p.global_position, randf() * TAU, 1.6)
	Audio.play_ui(&"loot_drop")
	_select(null)

func _destroy(it: ItemInstance) -> void:
	if it == null or it.is_protected():
		return
	Game.ui_root.ask("Destroy Item", "Destroy %s permanently? This cannot be undone." % it.display_name(), func() -> void:
		if hero.inventory.destroy(it):
			Audio.play_ui(&"break_pottery")
			_select(null), "Destroy", true)

func _split_dialog(it: ItemInstance) -> void:
	if it == null or it.count < 2:
		return
	var spin := SpinBox.new()
	spin.min_value = 1
	spin.max_value = it.count - 1
	spin.value = floori(it.count / 2.0)
	spin.custom_minimum_size = Vector2(160, 44)
	spin.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var idx := hero.inventory.index_of(it)
	Game.ui_root.confirm.ask("Split Stack", "How many %s to take off the stack of %d?" % [it.base.display_name, it.count], func() -> void:
		if hero.inventory.split(idx, int(spin.value)) == null:
			Events.notify.emit("No free slot to split into", &"error"), "Split", false, spin)
