class_name InventoryWindow
extends UIWindow
## Inventory + Equipment (I). Left: the hero in 3D on a plinth, the 13 equipment slots around it, a stat summary and
## active set bonuses. Right: category tabs, search, rarity filter, sorting, the 60-cell bag, gold, and an action bar
## for the selected item: Equip/Use, Split, Lock, Favorite, Mark to sell, Drop, Destroy (confirmed).
## Mouse: left select · right Equip/Use · Shift+left Split · drag to move, merge, equip or unequip · double-click Equip.
## Potion Belt row (bh-011): what Q / E (the HP / Mana orbs on a phone) use — click a slot to choose, drop a consumable on
## it, press "Put on Q/E" for the selected consumable, or hover a consumable and press Q or E.

const CELL := 62.0
const SLOT_LAYOUT := {
	# slot: [column (0 left / 1 right), row]
	&"helm": [0, 0], &"inner_garment": [0, 1], &"armor": [0, 2], &"gloves_1": [0, 3], &"boots_1": [0, 4],
	&"accessory_1": [1, 0], &"accessory_2": [1, 1], &"gloves_2": [1, 2], &"boots_2": [1, 3], &"accessory_3": [1, 4],
}
const GLYPH := {&"main_weapon": "main_weapon", &"sub_weapon": "sub_weapon", &"helm": "helm", &"inner_garment": "inner_garment",
	&"armor": "armor", &"gloves_1": "gloves", &"gloves_2": "gloves", &"boots_1": "boots", &"boots_2": "boots",
	&"accessory_1": "accessory", &"accessory_2": "accessory", &"accessory_3": "accessory", &"accessory_4": "accessory"}

var hero: HeroData
var preview: CharacterPreview
var equip_slots := {}             # slot -> ItemSlot
var cells: Array[ItemSlot] = []
var filter := "all"
var min_rarity := 0
var search := ""
var selected: ItemSlot
var _tabs: TabBar
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
var _actions: HBoxContainer
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
var _hover_slot: ItemSlot

func _init() -> void:
	super._init("Inventory", Vector2(1560, 900))

func _build() -> void:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	row.add_child(_build_paper_doll())
	row.add_child(_build_bag())

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
	var acc4 := _equip_slot(&"accessory_4")
	acc4.position = Vector2(490, 8 + 5 * 88)
	doll.add_child(acc4)
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
	col.add_child(_build_belt())
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

func _build_belt() -> Control:
	var box := inset(Vector2(620, 0))
	var row := hbox(12)
	box.add_child(row)
	var t := UITheme.label("Potion Belt", 18, UITheme.GOLD, UITheme.title_font())
	t.custom_minimum_size = Vector2(118, 0)
	t.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(t)
	for i in HeroData.BELT_SIZE:
		var b := SkillButton.new(&"potion_health" if i == 0 else &"potion_mana", 54.0)
		b.set_potion(&"health_potion" if i == 0 else &"mana_potion")
		b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var slot := i
		b.activated.connect(func(sb: SkillButton) -> void: BeltPicker.open(sb, hero, slot))
		b.context.connect(func(sb: SkillButton) -> void: BeltPicker.open(sb, hero, slot))
		b.item_dropped.connect(func(_sb: SkillButton, it: ItemInstance) -> void: if it: BeltPicker.bind(hero, slot, it.base.id))
		TooltipLayer.attach(b, func() -> Control: return Tips.text("Click to choose what %s uses. You can also drag a consumable here%s." % [
			BeltPicker.slot_name(slot), "" if Settings.touch_mode else ", or hover one in the bag and press %s" % BeltPicker.slot_name(slot)], "Potion Belt"))
		row.add_child(b)
		_belt_slots.append(b)
		var n := UITheme.label("", 15, UITheme.PARCHMENT, UITheme.body_font())
		n.custom_minimum_size = Vector2(180, 0)
		n.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		n.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(n)
		_belt_names.append(n)
	return box

func _refresh_belt() -> void:
	for i in _belt_slots.size():
		var bp := hero.belt_preview(i)
		if bp.base != _belt_slots[i].potion_base:
			_belt_slots[i].set_potion(bp.base)
		_belt_slots[i].update_state(0.0, 0.0, "", int(bp.count))
		_belt_names[i].text = HeroData.belt_label(hero.potion_belt[i])

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
	_tabs = TabBar.new()
	for k in Inventory.FILTERS:
		_tabs.add_tab(Inventory.FILTER_NAMES[k])
	_tabs.tab_changed.connect(func(i: int) -> void:
		filter = Inventory.FILTERS.keys()[i]
		_apply_filter())
	col.add_child(_tabs)
	var tools := hbox(8)
	col.add_child(tools)
	_search = LineEdit.new()
	_search.placeholder_text = "Search items"
	_search.right_icon = UIArt.ui_icon("search")
	_search.custom_minimum_size = Vector2(260, 44)
	_search.clear_button_enabled = true
	_search.text_changed.connect(func(t: String) -> void:
		search = t
		_apply_filter())
	tools.add_child(_search)
	_rarity = OptionButton.new()
	_rarity.add_item("Any rarity")
	for i in range(1, BH.RARITY_COUNT):
		_rarity.add_item("%s or better" % BH.RARITY_NAMES[i])
	_rarity.item_selected.connect(func(i: int) -> void:
		min_rarity = i
		_apply_filter())
	_rarity.custom_minimum_size = Vector2(210, 44)
	tools.add_child(_rarity)
	_sort = OptionButton.new()
	for m in ["Rarity", "Type", "Level", "Name", "Value"]:
		_sort.add_item("Sort: " + m)
	_sort.custom_minimum_size = Vector2(170, 44)
	tools.add_child(_sort)
	tools.add_child(button("Sort", func() -> void:
		hero.inventory.sort(Inventory.SORT_MODES[_sort.selected])
		_select(null)))
	var grid_well := inset()
	col.add_child(grid_well)
	var grid := GridContainer.new()
	grid.columns = Inventory.COLUMNS
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	grid_well.add_child(grid)
	for i in Inventory.COLUMNS * Inventory.ROWS:
		var c := ItemSlot.new(ItemSlot.Kind.INVENTORY, CELL)
		c.index = i
		c.clicked.connect(_on_cell_clicked)
		c.double_clicked.connect(func(sl): _use(sl.item))
		c.dropped.connect(_on_drop)
		c.hovered.connect(_on_hover)
		grid.add_child(c)
		cells.append(c)
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
	_sel_name = UITheme.label("Select an item", 17, UITheme.TEXT_DIM, UITheme.body_bold())
	av.add_child(_sel_name)
	_actions = hbox(6)
	av.add_child(_actions)
	_btn_use = button("Equip", func() -> void: _use(_sel_item()), &"PrimaryButton", 120.0)
	_btn_split = button("Split", func() -> void: _split_dialog(_sel_item()), &"", 96.0)
	_btn_lock = button("Lock", func() -> void: _toggle_flag("locked"), &"", 96.0)
	_btn_fav = button("Favorite", func() -> void: _toggle_flag("favorite"), &"", 120.0)
	_btn_junk = button("Mark to Sell", func() -> void: _toggle_flag("junk"), &"", 150.0)
	_btn_drop = button("Drop", func() -> void: _drop(_sel_item()), &"", 96.0)
	_btn_destroy = button("Destroy", func() -> void: _destroy(_sel_item()), &"", 120.0)
	for i in HeroData.BELT_SIZE:
		var slot := i
		_btn_belt.append(button("Put on %s" % BeltPicker.slot_name(i), func() -> void:
			if _sel_item():
				BeltPicker.bind(hero, slot, _sel_item().base.id), &"", 150.0))
	for b in [_btn_use, _btn_split, _btn_lock, _btn_fav, _btn_junk, _btn_drop, _btn_destroy]:
		b.custom_minimum_size.y = 46
		_actions.add_child(b)
	var belt_row := hbox(6)
	av.add_child(belt_row)
	for b in _btn_belt:
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
	_space.text = "%d / %d slots free" % [hero.inventory.free_cells(), hero.inventory.capacity()]
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

func _apply_filter() -> void:
	for c in cells:
		c.dim = c.item != null and not Inventory.matches_filter(c.item, filter, min_rarity, search)
		c.queue_redraw()

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
		hint += " · %s / %s: put on the belt" % [BeltPicker.slot_name(0), BeltPicker.slot_name(1)]
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(s.item, {"hero": hero, "equipped": equipped, "hint": hint}))

## Hover a consumable in the bag and press a belt key (Q / E): that key now uses it.
func _unhandled_input(e: InputEvent) -> void:
	if not visible or hero == null or _hover_slot == null or not is_instance_valid(_hover_slot) or _hover_slot.item == null:
		return
	if _hover_slot.kind != ItemSlot.Kind.INVENTORY or not _hover_slot.item.base.is_consumable():
		return
	for i in HeroData.BELT_SIZE:
		if e.is_action_pressed(&"potion_health" if i == 0 else &"potion_mana"):
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
