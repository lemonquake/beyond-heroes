class_name ShopWindow
extends UIWindow
## Merchant (opened from dialogue). Left: the merchant, their stock (Buy) or what you sold (Buyback), category filter,
## sorting, prices under every item (red when unaffordable). Right: your inventory; right-click or Ctrl+click sells.
## Buying: click, tap or right-click buys one; Shift+click asks for a quantity; expensive purchases ask for confirmation.
## Tooltips compare every item with what you wear.

const CELL := 64.0

var shop: Shop
var hero: HeroData
var mode := "buy"
var filter := "all"
var sort_mode := 0
var _portrait: TextureRect
var _name: Label
var _kind: Label
var _refresh_label: Label
var _stock_grid: GridContainer
var _bag: Array[ItemSlot] = []
var _gold: Label
var _mode_tabs: TabBar
var _filter_tabs: TabBar
var _sort: OptionButton
var _junk_btn: Button

func _init() -> void:
	super._init("Merchant", Vector2(1600, 900))

func open_shop(shop_id: StringName) -> void:
	var def := DB.shop(shop_id)
	if def == null or Game.hero == null:
		return
	shop = Shop.open(def, Game.hero)
	# A category or Buyback tab from the previous merchant must not hide this stock.
	mode = "buy"
	filter = "all"
	if _mode_tabs:
		_mode_tabs.set_block_signals(true)
		_mode_tabs.current_tab = 0
		_mode_tabs.set_block_signals(false)
	if _filter_tabs:
		_filter_tabs.set_block_signals(true)
		_filter_tabs.current_tab = 0
		_filter_tabs.set_block_signals(false)
	set_title(def.display_name)
	Events.shop_opened.emit(shop_id)
	Game.ui_root.open(&"shop")

func close_window() -> void:
	if visible and shop:
		Events.shop_closed.emit(shop.def.id)
	super.close_window()

func _build() -> void:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	# merchant side
	var left := vbox(8)
	left.custom_minimum_size = Vector2(800, 0)
	row.add_child(left)
	var head := hbox(14)
	left.add_child(head)
	_portrait = TextureRect.new()
	_portrait.custom_minimum_size = Vector2(96, 96)
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	head.add_child(_portrait)
	var hv := vbox(2)
	hv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hv)
	_name = UITheme.title("", 26, UITheme.GOLD)
	hv.add_child(_name)
	_kind = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	hv.add_child(_kind)
	_refresh_label = UITheme.label("", 14, UITheme.TEXT_MUTED, UITheme.body_font())
	hv.add_child(_refresh_label)
	_mode_tabs = TabBar.new()
	_mode_tabs.add_tab("Buy")
	_mode_tabs.add_tab("Buyback")
	_mode_tabs.tab_changed.connect(func(i: int) -> void:
		mode = "buy" if i == 0 else "buyback"
		_refresh_stock())
	left.add_child(_mode_tabs)
	var tools := hbox(8)
	left.add_child(tools)
	_filter_tabs = TabBar.new()
	for k in ["all", "weapons", "armor", "accessories", "consumables", "materials"]:
		_filter_tabs.add_tab(Inventory.FILTER_NAMES[k])
	_filter_tabs.tab_changed.connect(func(i: int) -> void:
		filter = ["all", "weapons", "armor", "accessories", "consumables", "materials"][i]
		_refresh_stock())
	_filter_tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tools.add_child(_filter_tabs)
	_sort = OptionButton.new()
	for m in ["Default order", "Price: low to high", "Price: high to low", "Rarity", "Type"]:
		_sort.add_item(m)
	_sort.item_selected.connect(func(i: int) -> void:
		sort_mode = i
		_refresh_stock())
	tools.add_child(_sort)
	var sw := inset()
	sw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(sw)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sw.add_child(scroll)
	_stock_grid = GridContainer.new()
	_stock_grid.columns = 10
	_stock_grid.add_theme_constant_override("h_separation", 10)
	_stock_grid.add_theme_constant_override("v_separation", 30)
	scroll.add_child(_stock_grid)
	var hint_m := MarginContainer.new()
	hint_m.add_theme_constant_override("margin_left", 18)
	left.add_child(hint_m)
	hint_m.add_child(UITheme.label("Click or tap: buy one · Shift+click: choose quantity · Hover to compare with your gear", 14, UITheme.TEXT_MUTED, UITheme.body_font()))
	# player side
	var right := vbox(8)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(right)
	right.add_child(section("Your Inventory"))
	var bw := inset()
	right.add_child(bw)
	var grid := GridContainer.new()
	grid.columns = Inventory.COLUMNS
	grid.add_theme_constant_override("h_separation", 3)
	grid.add_theme_constant_override("v_separation", 3)
	bw.add_child(grid)
	for i in Inventory.COLUMNS * Inventory.ROWS:
		var c := ItemSlot.new(ItemSlot.Kind.INVENTORY, 60.0)
		c.index = i
		c.drag_enabled = false
		c.clicked.connect(_on_bag_clicked)
		c.hovered.connect(_on_bag_hover)
		grid.add_child(c)
		_bag.append(c)
	var foot := hbox(12)
	right.add_child(foot)
	var gi := TextureRect.new()
	gi.texture = UIArt.ui_icon("gold")
	gi.custom_minimum_size = Vector2(26, 26)
	gi.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	gi.modulate = UITheme.GOLD
	foot.add_child(gi)
	_gold = UITheme.label("", 22, UITheme.GOLD, UITheme.number_font())
	_gold.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(_gold)
	_junk_btn = button("Sell Marked Items", _sell_junk, &"", 230.0)
	foot.add_child(_junk_btn)
	right.add_child(UITheme.label("Right-click or Ctrl+click an item to sell it. Locked and favorite items are never sold.", 14, UITheme.TEXT_MUTED, UITheme.body_font()))

func refresh() -> void:
	hero = Game.hero
	if shop == null or hero == null:
		return
	var npc := DB.npc(shop.def.npc)
	_portrait.texture = UIArt.tex(npc.portrait) if npc else null
	_name.text = npc.display_name if npc else shop.def.display_name
	var rel := hero.relationship(shop.def.npc)
	var rep := ""
	if rel >= 20:
		rep = " · Friendly prices"
	elif rel <= -20:
		rep = " · Unfriendly prices"
	_kind.text = "%s%s" % [{&"consumables": "Provisions and draughts", &"weapons": "Weapons and armor", &"magic": "Arcane goods",
		&"rare": "Rare goods", &"premium": "Advanced arms and armor", &"jewels": "Rings, amulets and charms", &"alchemy": "Herbs, draughts and recipes",
		&"supplies": "Camp supplies", &"outfitter": "Field gear", &"crystals": "Socket crystals"}.get(shop.def.kind, "Goods"), rep]
	if not shop.changed.is_connected(_on_shop_changed):
		shop.changed.connect(_on_shop_changed)
	if not hero.inventory_changed.is_connected(_on_shop_changed):
		hero.inventory_changed.connect(_on_shop_changed)
	_refresh_stock()
	_refresh_bag()

func _on_shop_changed() -> void:
	if visible:
		_refresh_stock()
		_refresh_bag()

func _process(_d: float) -> void:
	if visible and shop and hero:
		if shop.def.kind == &"crystals":
			_refresh_label.text = "Crystals stay in stock. Higher grades unlock as you level."
			return
		if shop.def.restock_on_clears:
			_refresh_label.text = "New stock after your next stage clear or miniboss · Clears so far: %d" % hero.clear_count
			return
		var s := int(shop.seconds_to_refresh(hero))
		_refresh_label.text = "New stock in %d:%02d" % [s / 60, s % 60]

func _entries() -> Array:
	var out := []
	if mode == "buy":
		for i in shop.stock.size():
			var it: ItemInstance = shop.stock[i].item
			if Inventory.matches_filter(it, filter):
				out.append({"index": i, "item": it, "price": shop.buy_price(i, hero), "special": shop.stock[i].special != ""})
	else:
		for i in shop.buyback.size():
			var it2: ItemInstance = shop.buyback[i].item
			if Inventory.matches_filter(it2, filter):
				out.append({"index": i, "item": it2, "price": int(shop.buyback[i].price), "special": false})
	match sort_mode:
		1: out.sort_custom(func(a, b): return a.price < b.price)
		2: out.sort_custom(func(a, b): return a.price > b.price)
		3: out.sort_custom(func(a, b): return a.item.rarity > b.item.rarity)
		4: out.sort_custom(func(a, b): return Inventory.CATEGORY_ORDER.find(a.item.base.category) < Inventory.CATEGORY_ORDER.find(b.item.base.category))
	return out

func _refresh_stock() -> void:
	for c in _stock_grid.get_children():
		c.queue_free()
	var entries := _entries()
	if entries.is_empty():
		var l := UITheme.label("Nothing here." if mode == "buy" else "Items you sell appear here and can be bought back for the same price.", 16, UITheme.TEXT_MUTED, UITheme.body_font())
		_stock_grid.add_child(l)
		return
	var lvl := hero.progress.level
	var attrs := hero.progress.base_attributes()
	for e in entries:
		var s := ItemSlot.new(ItemSlot.Kind.SHOP if mode == "buy" else ItemSlot.Kind.BUYBACK, CELL)
		var it: ItemInstance = e.item
		var unusable := it.is_equipment() and hero.equipment.check(it, hero.equipment.auto_slot(it), lvl, attrs).begins_with("Requires")
		s.set_item(it, unusable)
		s.index = e.index
		s.price = e.price
		s.price_ok = hero.inventory.gold >= e.price
		s.drag_enabled = false
		s.clicked.connect(_on_stock_clicked)
		s.hovered.connect(func(sl: ItemSlot, inside: bool) -> void:
			if inside:
				var hint := "Click or tap to buy" + (" · Shift+click to choose quantity" if it.base.is_stackable() else "")
				if e.special:
					hint = "One of a kind. " + hint
				TooltipLayer.show_for(sl, func() -> Control: return Tips.item(it, {"hero": hero, "price": e.price, "hint": hint if mode == "buy" else "Click or tap to buy back"}))
			else:
				TooltipLayer.hide_for(sl))
		_stock_grid.add_child(s)

func _refresh_bag() -> void:
	for i in _bag.size():
		var it: ItemInstance = hero.inventory.cells[i]
		_bag[i].set_item(it)
		_bag[i].dim = it != null and (it.is_protected() or not it.base.sellable)
	_gold.text = InventoryWindow._fmt_gold(hero.inventory.gold)
	_junk_btn.disabled = hero.inventory.junk_items().is_empty()

func _on_stock_clicked(s: ItemSlot, button: int, shift: bool, _ctrl: bool) -> void:
	if s.item == null:
		return
	if mode == "buyback":
		if button == MOUSE_BUTTON_RIGHT or button == MOUSE_BUTTON_LEFT:
			_report(shop.buy_back(s.index, hero), "Bought back")
		return
	if shift and s.item.base.is_stackable():
		_quantity_dialog(s.index)
		return
	if button == MOUSE_BUTTON_RIGHT or button == MOUSE_BUTTON_LEFT:
		_buy(s.index, 1)

func _buy(index: int, count: int) -> void:
	var price := shop.buy_price(index, hero, count)
	var it: ItemInstance = shop.stock[index].item
	var go := func() -> void: _report(shop.buy(index, hero, count), "Bought")
	if ShopPricing.needs_confirmation(price, hero.inventory.gold) and hero.inventory.gold >= price:
		Game.ui_root.ask("Confirm Purchase", "Buy %s%s for %d gold?" % [it.display_name(), " x%d" % count if count > 1 else "", price], go, "Buy (%d gold)" % price)
	else:
		go.call()

func _report(r: Dictionary, verb: String) -> void:
	if r.get("ok", false):
		Audio.play_ui(&"gold_pickup" if Audio.has_sound(&"gold_pickup") else &"ui_click")
		var it: ItemInstance = r.get("item")
		if it:
			Events.notify.emit("%s %s" % [verb, it.display_name()], &"loot")
	else:
		Events.notify.emit(String(r.get("error", "Cannot do that")), &"error")
		Audio.play_ui(&"ui_error")

func _quantity_dialog(index: int) -> void:
	var it: ItemInstance = shop.stock[index].item
	var unit := shop.buy_price(index, hero, 1)
	var max_n := maxi(1, mini(it.base.stack_max, hero.inventory.gold / maxi(1, unit)))
	if not shop.stock[index].infinite:
		max_n = mini(max_n, it.count)
	var box := VBoxContainer.new()
	var spin := SpinBox.new()
	spin.min_value = 1
	spin.max_value = max_n
	spin.value = mini(5, max_n)
	spin.custom_minimum_size = Vector2(160, 44)
	spin.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(spin)
	var total := UITheme.label("", 18, UITheme.GOLD, UITheme.number_font())
	total.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(total)
	var upd := func(v: float) -> void: total.text = "Total: %d gold" % (unit * int(v))
	spin.value_changed.connect(upd)
	upd.call(spin.value)
	Game.ui_root.confirm.ask("Quantity", "How many %s? (%d gold each)" % [it.base.display_name, unit], func() -> void:
		_report(shop.buy(index, hero, int(spin.value)), "Bought"), "Buy", false, box)

func _on_bag_clicked(s: ItemSlot, button: int, _shift: bool, ctrl: bool) -> void:
	if s.item == null:
		return
	if button == MOUSE_BUTTON_RIGHT or ctrl:
		var it := s.item
		var r := shop.sell(it, hero)
		if r.ok:
			Audio.play_ui(&"gold_pickup" if Audio.has_sound(&"gold_pickup") else &"ui_click")
			Events.notify.emit("Sold %s for %d gold" % [it.display_name(), r.gold], &"loot")
		else:
			Events.notify.emit(r.error, &"error")
			Audio.play_ui(&"ui_error")
		TooltipLayer.hide_for(null)

func _on_bag_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	var sell := shop.sell_price(it, hero)
	var hint := "Right-click to sell" if not it.is_protected() and it.base.sellable else ("Locked" if it.is_protected() else "")
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": hero, "sell": sell, "hint": hint}))

func _sell_junk() -> void:
	var n := hero.inventory.junk_items().size()
	var total := 0
	for it in hero.inventory.junk_items():
		total += shop.sell_price(it, hero)
	Game.ui_root.ask("Sell Marked Items", "Sell %d marked item%s for %d gold?" % [n, "" if n == 1 else "s", total], func() -> void:
		var g := shop.sell_junk(hero)
		Events.notify.emit("Sold marked items for %d gold" % g, &"loot"), "Sell")
