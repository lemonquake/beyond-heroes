class_name WeaponUpgradePage
extends HBoxContainer
## One page of the crafting window for weapon upgrades (bh-017): Enchantment at the Alchemy Table or Fore-Tech at the
## Forge. Left: the weapons you can upgrade (hand slots first, then the bag). Right: the chosen weapon, the upgrades on
## offer with what the next rank does, the materials and fee, and the button. Rules live in WeaponUpgrades.

signal applied

var kind: StringName = WeaponUpgrades.ENCHANT
var station: StringName = &"alchemy"
var hero: HeroData
var _sel: ItemInstance
var _choice: StringName = &""
var _list: VBoxContainer
var _slot: ItemSlot
var _name: Label
var _state: Label
var _text: Label
var _options: GridContainer
var _detail: Label
var _ingredients: VBoxContainer
var _fee: Label
var _apply: Button
var _result: Label

func _init(p_kind: StringName) -> void:
	kind = p_kind
	station = WeaponUpgrades.station_for(kind)
	add_theme_constant_override("separation", 22)
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	_build()

func _verb() -> String:
	return "Etch the Rune" if kind == WeaponUpgrades.ENCHANT else "Refit the Weapon"

func _build() -> void:
	var left := UIWindow.vbox(8)
	left.custom_minimum_size = Vector2(560, 0)
	add_child(left)
	left.add_child(UIWindow.section("Your Weapons"))
	var lw := UIWindow.inset()
	lw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(lw)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	lw.add_child(scroll)
	_list = UIWindow.vbox(4)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)
	var right := UIWindow.vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(right)
	var top := UIWindow.hbox(18)
	right.add_child(top)
	_slot = ItemSlot.new(ItemSlot.Kind.DISPLAY, 96.0)
	_slot.drag_enabled = false
	_slot.hovered.connect(_on_slot_hover)
	top.add_child(_slot)
	var tv := UIWindow.vbox(3)
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	_name = UITheme.title("", 26, UITheme.GOLD)
	tv.add_child(_name)
	_state = UITheme.label("", 17, UITheme.PARCHMENT, UITheme.body_bold())
	_state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(_state)
	_text = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(_text)
	right.add_child(UIWindow.section("Choose %s" % ("an Enchantment" if kind == WeaponUpgrades.ENCHANT else "a Fore-Tech refit")))
	_options = GridContainer.new()
	_options.columns = 3
	_options.add_theme_constant_override("h_separation", 8)
	_options.add_theme_constant_override("v_separation", 8)
	right.add_child(_options)
	_detail = UITheme.label("", 17, UITheme.TEXT, UITheme.body_font())
	_detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_detail)
	var iw := UIWindow.inset()
	right.add_child(iw)
	_ingredients = UIWindow.vbox(4)
	iw.add_child(_ingredients)
	var act := UIWindow.hbox(12)
	right.add_child(act)
	_fee = UITheme.label("", 19, UITheme.GOLD, UITheme.body_bold())
	_fee.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	act.add_child(_fee)
	_apply = UIWindow.button(_verb(), _do_apply, &"PrimaryButton", 300.0)
	_apply.custom_minimum_size.y = 52
	act.add_child(_apply)
	_result = UITheme.label("", 18, UITheme.GOOD, UITheme.body_font())
	_result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_result)
	var how := ""
	if kind == WeaponUpgrades.ENCHANT:
		how = "Enchantment is magic: a rune turns part of the weapon's damage into an element and adds elemental gifts. One per weapon, rank I to III. Choosing a different rune starts over at rank I. Fore-Tech (at a Forge) is a separate upgrade that stacks with it."
	else:
		how = "Fore-Tech is craft: a mechanical refit that tempers the blade (+2% weapon damage per rank) and adds one kind of bonus, +1 to +5. One per weapon. Choosing a different refit starts over at +1. Enchantment (at an Alchemy Table) is a separate upgrade that stacks with it."
	var hl := UITheme.label(how, 15, UITheme.TEXT_MUTED, UITheme.body_font())
	hl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(hl)

func refresh(p_hero: HeroData) -> void:
	hero = p_hero
	if hero == null:
		return
	var ws := WeaponUpgrades.weapons(hero)
	if _sel == null or not ws.has(_sel):
		_sel = ws[0] if not ws.is_empty() else null
	_fill_list(ws)
	_fill_detail()

func _fill_list(ws: Array) -> void:
	for c in _list.get_children():
		_list.remove_child(c)
		c.queue_free()
	if ws.is_empty():
		_list.add_child(UITheme.label("You carry no weapon to upgrade. Equip one or put it in your bag.", 17, UITheme.TEXT_MUTED, UITheme.body_font()))
		return
	for it: ItemInstance in ws:
		_list.add_child(_row(it))

func _row(it: ItemInstance) -> Control:
	var b := Button.new()
	b.custom_minimum_size = Vector2(520, 66)
	b.toggle_mode = true
	b.button_pressed = it == _sel
	b.focus_mode = Control.FOCUS_ALL
	var h := UIWindow.hbox(12)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 8
	b.add_child(h)
	var slot := ItemSlot.new(ItemSlot.Kind.DISPLAY, 54.0)
	slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	slot.set_item(it)
	slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(slot)
	var v := UIWindow.vbox(0)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(v)
	var n := UITheme.label(it.display_name(), 19, it.color(), UITheme.body_bold())
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	n.clip_text = true
	n.custom_minimum_size.x = 400
	v.add_child(n)
	var parts: Array = []
	if WeaponUpgrades.is_equipped(hero, it):
		parts.append("Equipped")
	var mine := WeaponUpgrades.summary(it, kind)
	parts.append(mine if mine != "" else "No %s yet" % WeaponUpgrades.kind_name(kind).to_lower())
	var s := UITheme.label(" · ".join(parts), 15, UITheme.GOOD if mine != "" else UITheme.TEXT_DIM, UITheme.body_font())
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(s)
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		_sel = it
		_choice = &""
		_result.text = ""
		refresh(hero))
	return b

func _ids() -> Array:
	return DataUpgrades.enchant_ids() if kind == WeaponUpgrades.ENCHANT else DataUpgrades.tech_ids()

func _def(id: StringName) -> Dictionary:
	return DataUpgrades.enchant(id) if kind == WeaponUpgrades.ENCHANT else DataUpgrades.tech(id)

func _fill_detail() -> void:
	for c in _options.get_children():
		_options.remove_child(c)
		c.queue_free()
	for c in _ingredients.get_children():
		_ingredients.remove_child(c)
		c.queue_free()
	_slot.set_item(_sel)
	if _sel == null:
		_name.text = "No weapon"
		_state.text = ""
		_text.text = ""
		_detail.text = ""
		_fee.text = ""
		_apply.disabled = true
		return
	_name.text = _sel.display_name()
	_name.add_theme_color_override("font_color", _sel.color())
	var lines: Array = []
	var e := WeaponUpgrades.summary(_sel, WeaponUpgrades.ENCHANT)
	var t := WeaponUpgrades.summary(_sel, WeaponUpgrades.FORETECH)
	lines.append("Enchantment: %s" % (e if e != "" else "none"))
	lines.append("Fore-Tech: %s" % (t if t != "" else "none"))
	_state.text = "   ·   ".join(lines)
	_text.text = _sel.base.flavor
	var cur := WeaponUpgrades.current_id(_sel, kind)
	if _choice == &"" or not _ids().has(_choice):
		_choice = cur if cur != &"" else _ids()[0]
	for id in _ids():
		var d := _def(id)
		var ob := Button.new()
		ob.toggle_mode = true
		ob.button_pressed = id == _choice
		ob.custom_minimum_size = Vector2(228, 58)
		ob.focus_mode = Control.FOCUS_ALL
		var rk := WeaponUpgrades.current_rank(_sel, kind) if id == cur else 0
		ob.text = "%s%s%s" % ["▶ " if id == _choice else "", d.name, ("  (%s)" % (DataUpgrades.roman(rk) if kind == WeaponUpgrades.ENCHANT else "+%d" % rk)) if rk > 0 else ""]
		var oc: Color = (d.color as Color).lightened(0.4)
		ob.add_theme_color_override("font_color", oc)
		ob.add_theme_color_override("font_hover_color", oc.lightened(0.3))
		ob.add_theme_color_override("font_pressed_color", Color.WHITE)
		ob.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			_choice = id
			_result.text = ""
			_fill_detail())
		_options.add_child(ob)
	_show_choice()

func _show_choice() -> void:
	var d := _def(_choice)
	var rank := WeaponUpgrades.next_rank(_sel, kind, _choice)
	var full := WeaponUpgrades.current_id(_sel, kind) == _choice and WeaponUpgrades.current_rank(_sel, kind) >= WeaponUpgrades.max_rank(kind)
	var mods: Array = DataUpgrades.enchant_mods(_choice, rank) if kind == WeaponUpgrades.ENCHANT else DataUpgrades.tech_mods(_choice, rank)
	var eff: Array = []
	if kind == WeaponUpgrades.ENCHANT:
		eff.append("%d%% of the weapon's damage as %s" % [roundi(DataUpgrades.enchant_share(_choice, rank) * 100.0), Elements.NAMES[int(d.element)]])
	else:
		eff.append("+%d%% weapon damage (tempered)" % roundi(DataUpgrades.TEMPER_PER_RANK * rank * 100.0))
	for m in mods:
		eff.append(StatDefs.format_modifier(m.stat, m.op, m.value))
	var swap := WeaponUpgrades.current_id(_sel, kind) != &"" and WeaponUpgrades.current_id(_sel, kind) != _choice
	var head := "%s — %s\n" % [d.name, "at its highest rank" if full else ("rank %s" % (DataUpgrades.roman(rank) if kind == WeaponUpgrades.ENCHANT else "+%d" % rank))]
	if swap:
		head += "Replaces %s and starts over.\n" % WeaponUpgrades.summary(_sel, kind)
	var best := "" if kind == WeaponUpgrades.ENCHANT else "Best on: %s.\n" % d.best
	_detail.text = "%s%s%s\n%s" % [head, best, String(d.text), "\n".join(eff.map(func(x): return "  • " + x))]
	if full:
		_fee.text = ""
		_apply.disabled = true
		_apply.text = "Highest rank"
		return
	var c := WeaponUpgrades.cost(_sel, kind, _choice)
	for inp in c.inputs:
		var b := DB.item_base(inp[0])
		var have := hero.inventory.count_of(inp[0])
		var line := UIWindow.hbox(12)
		var sl := ItemSlot.new(ItemSlot.Kind.DISPLAY, 40.0)
		sl.drag_enabled = false
		var sample := DB.make_item(inp[0], BH.Rarity.COMMON, 1, 3)
		sl.set_item(sample)
		sl.hovered.connect(func(s2: ItemSlot, inside: bool) -> void:
			if inside:
				TooltipLayer.show_for(s2, func() -> Control: return Tips.item(sample, {"hero": hero}))
			else:
				TooltipLayer.hide_for(s2))
		line.add_child(sl)
		var nl := UITheme.label(b.display_name if b else String(inp[0]), 18, UITheme.TEXT, UITheme.body_font())
		nl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(nl)
		var cl := UITheme.label("%d / %d" % [have, int(inp[1])], 19, UITheme.GOOD if have >= int(inp[1]) else UITheme.BAD, UITheme.number_font())
		cl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(cl)
		_ingredients.add_child(line)
	_fee.text = "Level %d · Fee %d gold" % [int(c.level), int(c.gold)]
	var err := WeaponUpgrades.check(hero, _sel, kind, _choice, station)
	_apply.disabled = err != ""
	_apply.text = _verb()
	if err != "" and _result.text == "":
		_result.add_theme_color_override("font_color", UITheme.TEXT_DIM)
		_result.text = err

func _do_apply() -> void:
	if _sel == null:
		return
	var res := WeaponUpgrades.apply(hero, _sel, kind, _choice, station)
	if not res.ok:
		Events.notify.emit(String(res.error), &"error")
		Audio.play_ui(&"ui_error")
		return
	var d := _def(_choice)
	_result.add_theme_color_override("font_color", UITheme.GOOD)
	_result.text = "%s is now %s." % [_sel.display_name(), WeaponUpgrades.summary(_sel, kind)]
	Audio.play_ui(&"level_up")
	Events.notify.emit("%s: %s" % [WeaponUpgrades.kind_name(kind), _result.text], &"loot")
	if Game.player is Player:
		FX.spawn(VFXLib.particles(d.color, 26, 1.0, true, 0.35, 2.6, 50.0, Vector3(0, 2.0, 0), 0.5), (Game.player as Node3D).global_position + Vector3.UP)
	applied.emit()
	refresh(hero)

func _on_slot_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": hero}))
