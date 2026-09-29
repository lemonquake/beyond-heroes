class_name SocketWindow
extends UIWindow
## bh-018: a Socket Specialist's bench. Left: every piece of your gear (worn first, then the bag) with its sockets.
## Right: the chosen piece — its sockets as rings (empty or holding a crystal), the crystals in your bag that fit it with
## what each would give in this kind of gear, and the Specialist's services: Set Crystal (free), Add Socket, Remove
## Socket, Purge (crystals destroyed, piece kept) and Crystallization (piece destroyed, crystals kept). Rules: Sockets.

var specialist := "Socket Specialist"
var shop_id: StringName = &""
var hero: HeroData
var _sel: ItemInstance
var _crystal: ItemInstance
var _socket := -1
var _list: VBoxContainer
var _slot: ItemSlot
var _name: Label
var _state: Label
var _sockets: HBoxContainer
var _socket_note: Label
var _crystals: GridContainer
var _preview: Label
var _set_btn: Button
var _svc := {}
var _svc_fee := {}
var _result: Label
var _gold: Label

const SOCKET_PX := 78.0

func _init() -> void:
	super._init("Sockets and Crystals", Vector2(1480, 940))

func open_for(p_specialist: String, p_shop: StringName = &"") -> void:
	specialist = p_specialist
	shop_id = p_shop
	set_title("%s — Sockets and Crystals" % specialist)
	Game.ui_root.open(&"socketing")

func _build() -> void:
	var cols := hbox(22)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	# ---- left: your gear
	var left := vbox(8)
	left.custom_minimum_size = Vector2(540, 0)
	cols.add_child(left)
	left.add_child(section("Your Gear"))
	var lw := inset()
	lw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(lw)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	lw.add_child(scroll)
	_list = vbox(4)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)
	# ---- right: the chosen piece
	var right := vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	var top := hbox(18)
	right.add_child(top)
	_slot = ItemSlot.new(ItemSlot.Kind.DISPLAY, 96.0)
	_slot.drag_enabled = false
	_slot.hovered.connect(_on_hover)
	top.add_child(_slot)
	var tv := vbox(3)
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	_name = UITheme.title("", 26, UITheme.GOLD)
	tv.add_child(_name)
	_state = UITheme.label("", 17, UITheme.PARCHMENT, UITheme.body_bold())
	_state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(_state)
	right.add_child(section("Sockets"))
	var sw := inset()
	right.add_child(sw)
	var sv := vbox(6)
	sw.add_child(sv)
	_sockets = hbox(12)
	_sockets.alignment = BoxContainer.ALIGNMENT_CENTER
	_sockets.custom_minimum_size = Vector2(0, SOCKET_PX + 8.0)
	sv.add_child(_sockets)
	_socket_note = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_socket_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_socket_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sv.add_child(_socket_note)
	right.add_child(section("Crystals in Your Bag"))
	var cw := inset(Vector2(0, 150))
	right.add_child(cw)
	var cv := vbox(8)
	cw.add_child(cv)
	_crystals = GridContainer.new()
	_crystals.columns = 9
	_crystals.add_theme_constant_override("h_separation", 8)
	_crystals.add_theme_constant_override("v_separation", 8)
	cv.add_child(_crystals)
	var prow := hbox(12)
	cv.add_child(prow)
	_preview = UITheme.label("", 16, UITheme.TEXT, UITheme.body_font())
	_preview.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_preview.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	prow.add_child(_preview)
	_set_btn = button("Set Crystal (free)", _do_set, &"PrimaryButton", 260.0)
	_set_btn.custom_minimum_size.y = 50
	prow.add_child(_set_btn)
	right.add_child(section("Services"))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 8)
	right.add_child(grid)
	for pair in [[Sockets.ADD, "Add Socket", "Opens one more socket, up to the tier maximum."],
			[Sockets.REMOVE, "Remove Socket", "Closes an empty socket."],
			[Sockets.PURGE, "Purge", "Breaks every crystal out. The crystals are destroyed; the piece keeps its sockets."],
			[Sockets.CRYSTALLIZE, "Crystallization", "Destroys the piece. Every crystal set in it comes back to you."]]:
		var svc: StringName = pair[0]
		var box := hbox(10)
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_child(box)
		var b := button(String(pair[1]), func() -> void: _do_service(svc), &"", 210.0)
		b.custom_minimum_size.y = 46
		TooltipLayer.attach(b, func() -> Control: return Tips.text(String(pair[2]), String(pair[1])))
		box.add_child(b)
		var fl := UITheme.label("", 16, UITheme.GOLD, UITheme.number_font())
		fl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		fl.custom_minimum_size.x = 250
		box.add_child(fl)
		_svc[svc] = b
		_svc_fee[svc] = fl
	_result = UITheme.label("", 17, UITheme.GOOD, UITheme.body_font())
	_result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_result)
	var foot := hbox(12)
	right.add_child(foot)
	_gold = UITheme.label("", 20, UITheme.GOLD, UITheme.number_font())
	_gold.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(_gold)
	foot.add_child(button("Buy Crystals", _open_shop, &"", 220.0))

func refresh() -> void:
	hero = Game.hero
	if hero == null or _list == null:
		return
	var ps := Sockets.pieces(hero)
	if _sel == null or not ps.has(_sel):
		_sel = ps[0] if not ps.is_empty() else null
		_socket = -1
	_fill_list(ps)
	_fill_detail()
	_gold.text = "%s gold" % _thousands(hero.inventory.gold)

static func _thousands(n: int) -> String:
	var s := str(absi(n))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if n < 0 else "") + s + out

func _fill_list(ps: Array) -> void:
	for c in _list.get_children():
		_list.remove_child(c)
		c.queue_free()
	if ps.is_empty():
		_list.add_child(UITheme.label("You carry no equipment. Wear or bag a piece to work on it.", 17, UITheme.TEXT_MUTED, UITheme.body_font()))
		return
	for it: ItemInstance in ps:
		_list.add_child(_row(it))

func _row(it: ItemInstance) -> Control:
	var b := Button.new()
	b.custom_minimum_size = Vector2(510, 70)
	b.toggle_mode = true
	b.button_pressed = it == _sel
	b.focus_mode = Control.FOCUS_ALL
	var h := hbox(12)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 8
	b.add_child(h)
	var slot := ItemSlot.new(ItemSlot.Kind.DISPLAY, 56.0)
	slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	slot.set_item(it)
	slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(slot)
	var v := vbox(2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_child(v)
	var nl := UITheme.label(it.display_name(), 17, it.color(), UITheme.body_bold())
	nl.clip_text = true
	nl.custom_minimum_size.x = 330
	nl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(nl)
	var worn := hero.equipment.slot_of(it)
	var where: String = String(BH.SLOT_NAMES.get(worn, "")) if worn != &"" else "In the bag"
	var sub := UITheme.label("%s · %s" % [where, it.rarity_name()], 14, UITheme.TEXT_DIM, UITheme.body_font())
	sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(sub)
	var pips := SocketPips.new()
	pips.item = it
	pips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pips.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(pips)
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		_sel = it
		_socket = -1
		_crystal = null
		_result.text = ""
		refresh())
	return b

func _fill_detail() -> void:
	_slot.set_item(_sel)
	for c in _sockets.get_children():
		_sockets.remove_child(c)
		c.queue_free()
	for c in _crystals.get_children():
		_crystals.remove_child(c)
		c.queue_free()
	if _sel == null:
		_name.text = "Nothing to work on"
		_state.text = ""
		_socket_note.text = ""
		_preview.text = ""
		_set_btn.disabled = true
		for k in _svc:
			_svc[k].disabled = true
			_svc_fee[k].text = ""
		return
	_name.text = _sel.display_name()
	_name.add_theme_color_override("font_color", _sel.color())
	var mx := Sockets.max_sockets(_sel)
	var grp := DataCrystals.group_for(_sel.base.category)
	_state.text = "%s · %d of %d socket%s open · crystals here give their %s gifts" % [_sel.rarity_name(), _sel.sockets, mx,
		"" if mx == 1 else "s", {DataCrystals.WEAPON: "weapon", DataCrystals.ARMOR: "armour", DataCrystals.JEWEL: "jewellery"}.get(grp, "")]
	# socket rings: open ones (empty or holding a crystal), then the ones that could still be opened, greyed
	for i in mx:
		_sockets.add_child(_socket_ring(i))
	if _socket >= _sel.sockets or (_socket >= 0 and String(_sel.gems[_socket]) != ""):
		_socket = -1
	if _sel.sockets == 0:
		_socket_note.text = "No socket is open yet. Add Socket opens the first."
	else:
		var lines := PackedStringArray()
		for g in _sel.gems:
			if String(g) != "":
				lines.append("%s: %s" % [DB.item_base(StringName(g)).display_name, "; ".join(DataCrystals.lines(StringName(g), grp))])
		_socket_note.text = "\n".join(lines) if not lines.is_empty() else "Every open socket is empty. Choose a crystal below and set it."
	# crystals that fit
	var fits := Sockets.crystals_for(hero, _sel)
	if _crystal != null and not fits.has(_crystal):
		_crystal = null
	if _crystal == null and not fits.is_empty():
		_crystal = fits[0]
	if fits.is_empty():
		var none := UITheme.label("No crystal in your bag fits this piece. Buy one, or win one from a boss or a champion.", 16, UITheme.TEXT_MUTED, UITheme.body_font())
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		none.custom_minimum_size.x = 820
		_crystals.add_child(none)
	for c: ItemInstance in fits:
		_crystals.add_child(_crystal_button(c))
	if _crystal != null:
		_preview.text = "%s in this %s: %s" % [_crystal.base.display_name, "weapon" if grp == DataCrystals.WEAPON else ("jewellery" if grp == DataCrystals.JEWEL else "armour"),
			"; ".join(DataCrystals.lines(_crystal.base.id, grp))]
	else:
		_preview.text = ""
	var empty := Sockets.first_empty(_sel)
	_set_btn.disabled = _crystal == null or empty < 0
	_set_btn.tooltip_text = "" if not _set_btn.disabled else ("Open a socket first" if empty < 0 else "Choose a crystal")
	for k in _svc:
		var err := Sockets.check(hero, _sel, k)
		_svc[k].disabled = err != ""
		var fee := Sockets.fee(_sel, k)
		_svc_fee[k].text = "%s gold" % _thousands(fee) if err == "" or err.begins_with("Not enough gold") else err
		_svc_fee[k].add_theme_color_override("font_color", UITheme.GOLD if err == "" else (UITheme.BAD if err.begins_with("Not enough") else UITheme.TEXT_MUTED))

func _socket_ring(i: int) -> Control:
	var ring := SocketRing.new()
	ring.custom_minimum_size = Vector2(SOCKET_PX, SOCKET_PX)
	ring.open = i < _sel.sockets
	ring.crystal = StringName(_sel.gems[i]) if ring.open else &""
	ring.selected = i == _socket or (_socket < 0 and ring.open and ring.crystal == &"" and i == Sockets.first_empty(_sel))
	if ring.crystal != &"":
		var cid := ring.crystal
		var grp := DataCrystals.group_for(_sel.base.category)
		TooltipLayer.attach(ring, func() -> Control:
			return Tips.text("\n".join(DataCrystals.lines(cid, grp)), DB.item_base(cid).display_name))
	elif ring.open:
		TooltipLayer.attach(ring, func() -> Control: return Tips.text("An empty socket. Choose a crystal and press Set Crystal.", "Socket %d" % (i + 1)))
		ring.gui_input.connect(func(e: InputEvent) -> void:
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				_socket = i
				_fill_detail())
	else:
		TooltipLayer.attach(ring, func() -> Control: return Tips.text("Not open yet. Add Socket opens it.", "Socket %d" % (i + 1)))
	return ring

func _crystal_button(c: ItemInstance) -> Control:
	var b := Button.new()
	b.toggle_mode = true
	b.button_pressed = c == _crystal
	b.custom_minimum_size = Vector2(84, 84)
	b.icon = c.icon()
	b.expand_icon = true
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.add_theme_constant_override("icon_max_width", 64)
	b.focus_mode = Control.FOCUS_ALL
	var n := Label.new()
	n.text = "x%d" % c.count
	n.add_theme_font_override("font", UITheme.number_font())
	n.add_theme_font_size_override("font_size", 15)
	n.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	n.add_theme_constant_override("outline_size", 4)
	n.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	n.offset_left = -34
	n.offset_top = -24
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(n)
	var h := hero
	TooltipLayer.attach(b, func() -> Control: return Tips.item(c, {"hero": h}))
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		_crystal = c
		_fill_detail())
	return b

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	var h := hero
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": h}))

func _do_set() -> void:
	if _sel == null or _crystal == null:
		return
	var nm := _crystal.base.display_name
	var r := Sockets.set_crystal(hero, _sel, _crystal, _socket)
	if r.ok:
		Audio.play_ui(&"ui_craft" if Audio.has_sound(&"ui_craft") else &"ui_click")
		_show_result("%s is set. It stays until you purge or crystallize this piece." % nm, true)
		_socket = -1
		_crystal = null
	else:
		_show_result(String(r.error), false)
	refresh()

func _do_service(svc: StringName) -> void:
	if _sel == null:
		return
	var err := Sockets.check(hero, _sel, svc)
	if err != "":
		_show_result(err, false)
		return
	var fee := Sockets.fee(_sel, svc)
	var it := _sel
	var go := func() -> void:
		var r := Sockets.apply(hero, it, svc)
		if not r.ok:
			_show_result(String(r.error), false)
		else:
			_show_result(_done_text(svc, it, r), true)
			if svc == Sockets.CRYSTALLIZE:
				_sel = null
		refresh()
	match svc:
		Sockets.PURGE:
			var names := PackedStringArray()
			for g in it.gems:
				if String(g) != "":
					names.append(DB.item_base(StringName(g)).display_name)
			Game.ui_root.ask("Purge %s" % it.display_name(), "Break every crystal out of it for %s gold?\nThese crystals will be DESTROYED: %s.\nThe piece keeps its sockets, empty." % [
				_thousands(fee), ", ".join(names)], go, "Purge (%s gold)" % _thousands(fee), true)
		Sockets.CRYSTALLIZE:
			Game.ui_root.ask("Crystallize %s" % it.display_name(), "Grind this piece to dust for %s gold?\nThe piece is DESTROYED. Every crystal set in it comes back to your bag." % _thousands(fee),
				go, "Crystallize (%s gold)" % _thousands(fee), true)
		_:
			if fee >= 1000:
				Game.ui_root.ask("%s" % ("Add a Socket" if svc == Sockets.ADD else "Remove a Socket"), "%s for %s gold?" % [
					"Open one more socket in %s" % it.display_name() if svc == Sockets.ADD else "Close an empty socket of %s" % it.display_name(), _thousands(fee)],
					go, "Pay %s gold" % _thousands(fee))
			else:
				go.call()

func _done_text(svc: StringName, it: ItemInstance, r: Dictionary) -> String:
	match svc:
		Sockets.ADD: return "A new socket is open: %d of %d." % [it.sockets, Sockets.max_sockets(it)]
		Sockets.REMOVE: return "A socket is closed: %d left." % it.sockets
		Sockets.PURGE: return "Purged: %d crystal%s shattered." % [r.crystals.size(), "" if r.crystals.size() == 1 else "s"]
		Sockets.CRYSTALLIZE: return "Crystallized: %d crystal%s back in your bag." % [r.crystals.size(), "" if r.crystals.size() == 1 else "s"]
	return ""

func _show_result(t: String, ok: bool) -> void:
	_result.text = t
	_result.add_theme_color_override("font_color", UITheme.GOOD if ok else UITheme.BAD)
	if not ok:
		Audio.play_ui(&"ui_error")

func _open_shop() -> void:
	if shop_id == &"":
		return
	close_window()
	var w := Game.ui_root.window(&"shop") as ShopWindow
	if w:
		w.open_shop(shop_id)


## A socket ring: a bronze rim; inside, a dark cup (empty), the crystal's icon (filled) or nothing (not yet open).
class SocketRing extends Control:
	var open := false
	var crystal: StringName = &""
	var selected := false
	var _tex: Texture2D

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		if crystal != &"":
			var b := DB.item_base(crystal)
			if b and ResourceLoader.exists(b.icon_path()):
				_tex = load(b.icon_path())

	func _draw() -> void:
		var c := size * 0.5
		var r := minf(size.x, size.y) * 0.5 - 3.0
		if not open:
			draw_arc(c, r, 0, TAU, 48, Color(0.5, 0.44, 0.36, 0.35), 2.0, true)
			draw_arc(c, r - 7.0, 0, TAU, 48, Color(0.5, 0.44, 0.36, 0.18), 1.5, true)
			return
		var fam := DataCrystals.family_of(crystal)
		var glow: Color = DataCrystals.FAMILIES[fam].color if fam != &"" else Color(0.4, 0.5, 0.6)
		draw_circle(c, r, Color(0.035, 0.03, 0.03, 0.95))
		if crystal != &"":
			for k in 4:
				draw_circle(c, r * (0.95 - k * 0.12), Color(glow, 0.1 + 0.05 * k))
		if _tex:
			var s := r * 1.75
			draw_texture_rect(_tex, Rect2(c - Vector2(s, s) * 0.5, Vector2(s, s)), false)
		else:
			draw_circle(c, r * 0.55, Color(0, 0, 0, 0.6))
			draw_arc(c, r * 0.55, PI * 1.1, PI * 1.6, 16, Color(1, 1, 1, 0.12), 2.0, true)
		draw_arc(c, r, 0, TAU, 56, Color(0.2, 0.14, 0.08), 7.0, true)
		draw_arc(c, r, 0, TAU, 56, UITheme.GOLD.darkened(0.25) if not selected else UITheme.GOLD, 3.5, true)
		if selected and crystal == &"":
			draw_arc(c, r + 3.0, 0, TAU, 56, Color(UITheme.GOLD, 0.55), 2.0, true)


## Small socket pips for list rows: one dot per socket the piece could hold (filled in the crystal's colour).
class SocketPips extends Control:
	var item: ItemInstance

	func _ready() -> void:
		custom_minimum_size = Vector2(104, 20)

	func _draw() -> void:
		if item == null:
			return
		var mx := Sockets.max_sockets(item)
		for i in mx:
			var p := Vector2(8.0 + i * 14.0, size.y * 0.5)
			if i >= item.sockets:
				draw_arc(p, 4.5, 0, TAU, 16, Color(0.5, 0.45, 0.38, 0.35), 1.2, true)
				continue
			var g := StringName(item.gems[i])
			if g == &"":
				draw_circle(p, 5.0, Color(0.05, 0.04, 0.04))
				draw_arc(p, 5.0, 0, TAU, 16, UITheme.GOLD.darkened(0.3), 1.6, true)
			else:
				var col: Color = DataCrystals.FAMILIES[DataCrystals.family_of(g)].color
				draw_circle(p, 5.5, col)
				draw_circle(p + Vector2(-1.5, -1.5), 1.8, Color(1, 1, 1, 0.7))
				draw_arc(p, 5.5, 0, TAU, 16, Color(0.1, 0.07, 0.04), 1.4, true)
