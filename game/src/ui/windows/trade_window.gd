class_name TradeWindow
extends UIWindow
## The trade table (bh-016): your bag on the left; on the right the items and gold you offer and the other hero's offer.
## Click a bag item to put it on the table, click an offered item to take it back. Both players must press Accept on the
## same two offers; any change to either offer clears both acceptances. The exchange itself is Net / TradeRules.

const CELL := 56.0
const OFFER_COLS := 5

var _bag: Array[ItemSlot] = []
var _mine: Array[ItemSlot] = []
var _theirs: Array[ItemSlot] = []
var _gold: SpinBox
var _their_gold: Label
var _my_state: Label
var _their_state: Label
var _summary: Label
var _accept: Button
var _cancel: Button
var _busy := false

func _init() -> void:
	super._init("Trade", Vector2(1500, 880))
	modal = true

func _build() -> void:
	Net.trade_changed.connect(_on_trade_changed)
	var cols := hbox(24)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	# your bag
	var left := vbox(8)
	cols.add_child(left)
	left.add_child(section("Your Bag"))
	var bw := inset()
	left.add_child(bw)
	var grid := GridContainer.new()
	grid.columns = Inventory.COLUMNS
	grid.add_theme_constant_override("h_separation", 3)
	grid.add_theme_constant_override("v_separation", 3)
	var bag_scroll := ScrollContainer.new()
	bag_scroll.custom_minimum_size = Vector2(618, 420)
	bag_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bag_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	bw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bw.add_child(bag_scroll)
	bag_scroll.add_child(grid)
	for i in Inventory.COLUMNS * Inventory.ROWS:
		var c := ItemSlot.new(ItemSlot.Kind.INVENTORY, CELL)
		c.index = i
		c.drag_enabled = false
		c.clicked.connect(_on_bag_clicked)
		c.hovered.connect(_on_hover)
		grid.add_child(c)
		_bag.append(c)
	var hint := UITheme.label("Click an item to offer it. Locked and favorite items and quest items cannot be traded.", 15, UITheme.TEXT_MUTED, UITheme.body_font())
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size.x = Inventory.COLUMNS * (CELL + 3)
	left.add_child(hint)
	# the table
	var right := vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	right.add_child(section("Your Offer"))
	right.add_child(_offer_panel(_mine, true))
	var gr := hbox(10)
	right.add_child(gr)
	var gi := TextureRect.new()
	gi.texture = UIArt.ui_icon("gold")
	gi.custom_minimum_size = Vector2(26, 26)
	gi.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	gi.modulate = UITheme.GOLD
	gr.add_child(gi)
	gr.add_child(UITheme.label("Gold", 19, UITheme.GOLD, UITheme.body_bold()))
	_gold = SpinBox.new()
	_gold.min_value = 0
	_gold.max_value = 0
	_gold.step = 1
	_gold.rounded = true
	_gold.custom_minimum_size = Vector2(220, 40 if not Settings.touch_mode else 56)
	_gold.value_changed.connect(_on_gold_changed)
	gr.add_child(_gold)
	gr.add_child(button("All", func() -> void: _gold.value = _gold.max_value, &"", 80.0))
	_my_state = UITheme.label("", 18, UITheme.TEXT_DIM, UITheme.body_bold())
	right.add_child(_my_state)
	right.add_child(section("Their Offer"))
	right.add_child(_offer_panel(_theirs, false))
	_their_gold = UITheme.label("", 21, UITheme.GOLD, UITheme.number_font())
	right.add_child(_their_gold)
	_their_state = UITheme.label("", 18, UITheme.TEXT_DIM, UITheme.body_bold())
	right.add_child(_their_state)
	# actions
	var foot := MarginContainer.new()
	foot.add_theme_constant_override("margin_left", 22)
	foot.add_theme_constant_override("margin_right", 22)
	body.add_child(foot)
	var fv := vbox(8)
	foot.add_child(fv)
	_summary = UITheme.label("", 18, UITheme.TEXT, UITheme.body_font())
	_summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fv.add_child(_summary)
	var br := hbox(20)
	br.alignment = BoxContainer.ALIGNMENT_CENTER
	fv.add_child(br)
	_accept = button("Accept Trade", _on_accept, &"PrimaryButton", 340.0)
	_accept.custom_minimum_size.y = 60 if Settings.touch_mode else 50
	br.add_child(_accept)
	_cancel = button("Cancel Trade", func() -> void: close_window(), &"", 260.0)
	_cancel.custom_minimum_size.y = _accept.custom_minimum_size.y
	br.add_child(_cancel)

func _offer_panel(into: Array[ItemSlot], editable: bool) -> Control:
	var p := inset()
	var grid := GridContainer.new()
	grid.columns = OFFER_COLS
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	p.add_child(grid)
	for i in TradeRules.MAX_ITEMS:
		var c := ItemSlot.new(ItemSlot.Kind.DISPLAY, 64.0)
		c.index = i
		c.drag_enabled = false
		c.hovered.connect(_on_hover)
		if editable:
			c.clicked.connect(_on_offer_clicked)
		grid.add_child(c)
		into.append(c)
	return p

func open() -> void:
	super.open()

func close_window() -> void:
	# bh-041: both players accepted and the exchange is being made (on the official server this takes a moment): it can no
	# longer be called off from one side, and the window closes by itself when it is done
	if Net.in_trade() and bool(Net.trade.get("committing", false)):
		Events.notify.emit("Both of you accepted: the trade is being completed.", &"info")
		return
	if Net.in_trade():
		Net.trade_cancel("You closed the trade.")
	super.close_window()

func _on_trade_changed() -> void:
	if not Net.in_trade():
		if visible:
			super.close_window()
		return
	if Net.trade.phase == "open" and visible:
		refresh()

func refresh() -> void:
	if not Net.in_trade() or _bag.is_empty():
		return
	var hero := Game.hero
	var t: Dictionary = Net.trade
	set_title("Trade with %s" % t.name)
	var mine_items: Array = t.mine.items
	for i in _bag.size():
		var it: ItemInstance = hero.inventory.cells[i]
		_bag[i].set_item(it)
		_bag[i].dim = it != null and (TradeRules.item_error(it) != "" or mine_items.has(it))
		_bag[i].selected = it != null and mine_items.has(it)
	for i in _mine.size():
		_mine[i].set_item(mine_items[i] if i < mine_items.size() else null)
	var their_items: Array = t.theirs.items
	for i in _theirs.size():
		_theirs[i].set_item(their_items[i] if i < their_items.size() else null)
	_busy = true
	_gold.max_value = hero.inventory.gold
	_gold.value = mini(int(t.mine.gold), hero.inventory.gold)
	_busy = false
	_gold.editable = not t.committing
	_their_gold.text = "%d gold" % int(t.theirs.gold)
	_my_state.text = "You have accepted." if t.my_ok else "You have not accepted."
	_my_state.add_theme_color_override("font_color", UITheme.GOOD if t.my_ok else UITheme.TEXT_DIM)
	_their_state.text = "%s has accepted." % t.name if t.their_ok else "%s has not accepted." % t.name
	_their_state.add_theme_color_override("font_color", UITheme.GOOD if t.their_ok else UITheme.TEXT_DIM)
	var err := TradeRules.swap_error(hero, t.mine, t.theirs)
	_summary.text = "You give %s and receive %s." % [TradeRules.describe(t.mine), TradeRules.describe(t.theirs)]
	if err != "":
		_summary.text += "  " + err + "."
	_summary.add_theme_color_override("font_color", UITheme.BAD if err != "" else UITheme.TEXT)
	_accept.text = "Accepted — click to undo" if t.my_ok else "Accept Trade"
	_accept.disabled = bool(t.committing) or (err != "" and not t.my_ok)
	_cancel.disabled = bool(t.committing)
	if bool(t.committing):
		_accept.text = "Completing the trade…"
		_summary.text = ("Both accepted. Confirming the exchange with the official server…" if Official.active else "Both accepted. Exchanging…") 			+ "  You give %s and receive %s." % [TradeRules.describe(t.mine), TradeRules.describe(t.theirs)]
		_summary.add_theme_color_override("font_color", UITheme.GOOD)

func _on_bag_clicked(s: ItemSlot, button_index: int, _shift: bool, _ctrl: bool) -> void:
	if s.item == null or not Net.in_trade():
		return
	var items: Array = (Net.trade.mine.items as Array).duplicate()
	if items.has(s.item):
		items.erase(s.item)
	else:
		var err := TradeRules.item_error(s.item)
		if err == "" and items.size() >= TradeRules.MAX_ITEMS:
			err = "A trade holds at most %d items" % TradeRules.MAX_ITEMS
		if err != "":
			Events.notify.emit(err, &"error")
			Audio.play_ui(&"ui_error")
			return
		items.append(s.item)
	_set_offer(int(Net.trade.mine.gold), items)

func _on_offer_clicked(s: ItemSlot, _button: int, _shift: bool, _ctrl: bool) -> void:
	if s.item == null or not Net.in_trade():
		return
	var items: Array = (Net.trade.mine.items as Array).duplicate()
	items.erase(s.item)
	_set_offer(int(Net.trade.mine.gold), items)

func _on_gold_changed(v: float) -> void:
	if _busy or not Net.in_trade():
		return
	_set_offer(int(v), (Net.trade.mine.items as Array).duplicate())

func _set_offer(gold: int, items: Array) -> void:
	TooltipLayer.hide_for(null)
	var err := Net.trade_set_offer(gold, items)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
		refresh()

func _on_accept() -> void:
	if Net.in_trade():
		Net.trade_accept(not bool(Net.trade.my_ok))

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": Game.hero, "hint": ""}))
