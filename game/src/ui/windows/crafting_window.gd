class_name CraftingWindow
extends UIWindow
## Crafting at a station (bh-007): the forge, an alchemy table or a workbench. Left: the station's recipes grouped by
## kind, each marked "can make n", "missing materials", "requires level" or "not learned". Right: the chosen recipe —
## what it makes (hover for the full tooltip; gear shows an example roll), what kind of gear (variants), every
## ingredient with have / need, the fee, how many to make, and the craft button. The Salvage tab (forge and workbench)
## breaks weapons, armor and accessories from the bag down into materials.

const ROW_H := 64.0

var station: StringName = &"workbench"
var station_label := ""
var hero: HeroData
var _recipes: Array = []
var _sel := -1
var _only_makeable := false
var _variant_order: Array = []        # option index -> variant index
var _tabs: TabBar
var _recipes_page: Control
var _salvage_page: Control
var _enchant_page: WeaponUpgradePage      # bh-017: Enchantment (Alchemy Table)
var _tech_page: WeaponUpgradePage         # bh-017: Fore-Tech (Forge)
var _desc: Label
var _gold: Label
var _list: VBoxContainer
var _out_slot: ItemSlot
var _out_name: Label
var _out_text: Label
var _out_meta: Label
var _variant_row: Control
var _variant: OptionButton
var _ingredients: VBoxContainer
var _qty: SpinBox
var _craft_btn: Button
var _max_btn: Button
var _result: Label
var _salvage_bag: Array[ItemSlot] = []
var _salvage_info: Label
var _salvage_junk: Button
var _preview_cache := {}

func _init() -> void:
	super._init("Crafting", Vector2(1600, 900))

func open_station(p_station: StringName, p_label := "") -> void:
	station = p_station
	station_label = p_label if p_label != "" else String(DataCrafting.STATIONS.get(station, {}).get("name", "Crafting"))
	set_title(station_label)
	_sel = -1
	_preview_cache.clear()
	Game.ui_root.open(&"crafting")

func _build() -> void:
	var head := hbox(16)
	body.add_child(head)
	_desc = UITheme.label("", 18, UITheme.TEXT_DIM, UITheme.body_font())
	_desc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	head.add_child(_desc)
	var gi := TextureRect.new()
	gi.texture = UIArt.ui_icon("gold")
	gi.custom_minimum_size = Vector2(26, 26)
	gi.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	gi.modulate = UITheme.GOLD
	head.add_child(gi)
	_gold = UITheme.label("", 22, UITheme.GOLD, UITheme.number_font())
	head.add_child(_gold)
	_tabs = TabBar.new()
	_tabs.add_tab("Recipes")
	_tabs.add_tab("Salvage")
	_tabs.add_tab("Enchant Weapon")
	_tabs.add_tab("Fore-Tech Weapon")
	_tabs.tab_changed.connect(func(_i: int) -> void: _show_page())
	body.add_child(_tabs)
	_recipes_page = _build_recipes()
	body.add_child(_recipes_page)
	_salvage_page = _build_salvage()
	body.add_child(_salvage_page)
	_enchant_page = WeaponUpgradePage.new(WeaponUpgrades.ENCHANT)
	body.add_child(_enchant_page)
	_tech_page = WeaponUpgradePage.new(WeaponUpgrades.FORETECH)
	body.add_child(_tech_page)
	_enchant_page.applied.connect(func() -> void: _gold.text = InventoryWindow._fmt_gold(hero.inventory.gold))
	_tech_page.applied.connect(func() -> void: _gold.text = InventoryWindow._fmt_gold(hero.inventory.gold))

func _build_recipes() -> Control:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	# recipe list
	var left := vbox(8)
	left.custom_minimum_size = Vector2(640, 0)
	row.add_child(left)
	var filt := TabBar.new()
	filt.add_tab("All recipes")
	filt.add_tab("Can make now")
	filt.tab_changed.connect(func(i: int) -> void:
		_only_makeable = i == 1
		_refresh_list())
	left.add_child(filt)
	var lw := inset()
	lw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(lw)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	lw.add_child(scroll)
	_list = vbox(4)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)
	# the chosen recipe
	var right := vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(right)
	var top := hbox(18)
	right.add_child(top)
	_out_slot = ItemSlot.new(ItemSlot.Kind.DISPLAY, 104.0)
	_out_slot.drag_enabled = false
	_out_slot.hovered.connect(_on_out_hover)
	top.add_child(_out_slot)
	var tv := vbox(4)
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	_out_name = UITheme.title("", 28, UITheme.GOLD)
	tv.add_child(_out_name)
	_out_meta = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	tv.add_child(_out_meta)
	_out_text = UITheme.label("", 18, UITheme.TEXT, UITheme.body_font())
	_out_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(_out_text)
	_variant_row = hbox(12)
	right.add_child(_variant_row)
	_variant_row.add_child(UITheme.label("Make a", 19, UITheme.TEXT, UITheme.body_bold()))
	_variant = OptionButton.new()
	_variant.custom_minimum_size = Vector2(300, 44)
	_variant.item_selected.connect(func(_i: int) -> void:
		_preview_cache.clear()
		_refresh_detail())
	_variant_row.add_child(_variant)
	right.add_child(section("Ingredients"))
	var iw := inset()
	right.add_child(iw)
	_ingredients = vbox(6)
	iw.add_child(_ingredients)
	var act := hbox(12)
	right.add_child(act)
	act.add_child(UITheme.label("How many", 19, UITheme.TEXT, UITheme.body_bold()))
	_qty = SpinBox.new()
	_qty.min_value = 1
	_qty.max_value = Crafting.MAX_BATCH
	_qty.value = 1
	_qty.custom_minimum_size = Vector2(140, 44)
	_qty.value_changed.connect(func(_v: float) -> void: _refresh_detail())
	act.add_child(_qty)
	_max_btn = button("Max", func() -> void:
		var r := _current()
		if not r.is_empty():
			_qty.value = maxi(1, Crafting.max_craftable(hero, r)), &"", 90.0)
	act.add_child(_max_btn)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	act.add_child(sp)
	_craft_btn = button("Craft", _craft, &"PrimaryButton", 260.0)
	_craft_btn.custom_minimum_size.y = 52
	act.add_child(_craft_btn)
	_result = UITheme.label("", 18, UITheme.GOOD, UITheme.body_font())
	_result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_result)
	right.add_child(UITheme.label("Crafted gear is always of fine quality. Enchantments roll when you craft; hover the result for an example.", 15, UITheme.TEXT_MUTED, UITheme.body_font()))
	return row

func _build_salvage() -> Control:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var left := vbox(8)
	row.add_child(left)
	left.add_child(section("Your Inventory"))
	var bw := inset()
	left.add_child(bw)
	var grid := GridContainer.new()
	grid.columns = Inventory.COLUMNS
	grid.add_theme_constant_override("h_separation", 3)
	grid.add_theme_constant_override("v_separation", 3)
	var bag_scroll := ScrollContainer.new()
	bag_scroll.custom_minimum_size = Vector2(698, 420)
	bag_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bag_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	bw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bw.add_child(bag_scroll)
	bag_scroll.add_child(grid)
	for i in Inventory.COLUMNS * Inventory.ROWS:
		var c := ItemSlot.new(ItemSlot.Kind.INVENTORY, 64.0)
		c.index = i
		c.drag_enabled = false
		c.clicked.connect(_on_salvage_clicked)
		c.hovered.connect(_on_salvage_hover)
		grid.add_child(c)
		_salvage_bag.append(c)
	var right := vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(right)
	right.add_child(section("Salvage"))
	var t := UITheme.label("Right-click a weapon, armor piece or accessory to break it down. Heavy gear gives iron, light gear hide, cloth gives linen; Advanced and better also give Arcane Dust, Elite and better Wisp Motes. Locked and favorite items are never salvaged.", 18, UITheme.TEXT, UITheme.body_font())
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(t)
	_salvage_info = UITheme.label("", 19, UITheme.GOLD, UITheme.body_font())
	_salvage_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_salvage_info)
	_salvage_junk = button("Salvage Marked Items", _salvage_marked, &"", 280.0)
	right.add_child(_salvage_junk)
	return row

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	if not hero.inventory_changed.is_connected(_on_inv):
		hero.inventory_changed.connect(_on_inv)
	var sdef: Dictionary = DataCrafting.STATIONS.get(station, {})
	_desc.text = String(sdef.get("text", ""))
	var can_salvage := station in [&"forge", &"workbench"]
	_tabs.set_tab_hidden(1, not can_salvage)
	_tabs.set_tab_hidden(2, station != &"alchemy")
	_tabs.set_tab_hidden(3, station != &"forge")
	if _tabs.is_tab_hidden(_tabs.current_tab):
		_tabs.current_tab = 0
	_recipes = Crafting.recipes_for(station)
	if _sel < 0 or _sel >= _recipes.size():
		_sel = _first_makeable()
	_result.text = ""
	_show_page()

func _first_makeable() -> int:
	for i in _recipes.size():
		if Crafting.check(hero, _recipes[i], station, 1, 0) == "":
			return i
	return 0 if not _recipes.is_empty() else -1

func _on_inv() -> void:
	if visible:
		_preview_cache.clear()
		_show_page()

func _show_page() -> void:
	var tab := _tabs.current_tab
	var salvage := tab == 1
	_recipes_page.visible = tab == 0
	_salvage_page.visible = salvage
	_enchant_page.visible = tab == 2
	_tech_page.visible = tab == 3
	_gold.text = InventoryWindow._fmt_gold(hero.inventory.gold) if hero else ""
	if tab == 2:
		_enchant_page.refresh(hero)
	elif tab == 3:
		_tech_page.refresh(hero)
	elif salvage:
		_refresh_salvage()
	else:
		_refresh_list()
		_refresh_detail()

func _current() -> Dictionary:
	return _recipes[_sel] if _sel >= 0 and _sel < _recipes.size() else {}

# ---- recipe list ------------------------------------------------------------------------------------------------

func _status(r: Dictionary) -> Array:
	if not Crafting.is_known(hero, r):
		return ["Not learned: recipe scroll", UITheme.TEXT_MUTED]
	if hero.progress.level < int(r.get("level", 1)):
		return ["Requires level %d" % int(r.level), UITheme.BAD]
	var n := Crafting.max_craftable(hero, r)
	if n > 0:
		return ["Can make %d" % n, UITheme.GOOD]
	return ["Missing materials", UITheme.TEXT_DIM]

func _refresh_list() -> void:
	for c in _list.get_children():
		c.queue_free()
	var group := ""
	var shown := 0
	for i in _recipes.size():
		var r: Dictionary = _recipes[i]
		if _only_makeable and Crafting.max_craftable(hero, r) <= 0:
			continue
		if not Crafting.is_known(hero, r) and _only_makeable:
			continue
		if String(r.group) != group:
			group = String(r.group)
			var gl := UITheme.title(group, 19, UITheme.BRONZE)
			_list.add_child(gl)
		_list.add_child(_row(i, r))
		shown += 1
	if shown == 0:
		_list.add_child(UITheme.label("Nothing you can make right now. Monsters drop parts; herbs grow beside roads and fields.", 17, UITheme.TEXT_MUTED, UITheme.body_font()))

func _row(i: int, r: Dictionary) -> Control:
	var b := Button.new()
	b.custom_minimum_size = Vector2(600, ROW_H)
	b.toggle_mode = true
	b.button_pressed = i == _sel
	b.focus_mode = Control.FOCUS_ALL
	var h := hbox(12)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 8
	b.add_child(h)
	var slot := ItemSlot.new(ItemSlot.Kind.DISPLAY, 54.0)
	slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	slot.set_item(_preview(r))
	slot.dim = not Crafting.is_known(hero, r)
	slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(slot)
	var v := vbox(0)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(v)
	var st := _status(r)
	var nm := String(r.name)
	var out: Dictionary = r.out
	if out.has("count") and int(out.count) > 1:
		nm += "  ×%d" % int(out.count)
	var n := UITheme.label(nm, 19, UITheme.PARCHMENT if Crafting.is_known(hero, r) else UITheme.TEXT_DIM, UITheme.body_bold())
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(n)
	var s := UITheme.label(st[0], 16, st[1], UITheme.body_font())
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(s)
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		_sel = i
		_qty.value = 1
		_result.text = ""
		_preview_cache.clear()
		_refresh_list()
		_refresh_detail())
	return b

## What a recipe makes, for display: the stack for goods, an example roll for gear (cached per recipe + variant).
func _preview(r: Dictionary, variant := 0) -> ItemInstance:
	var key := "%s|%d" % [r.id, variant]
	if _preview_cache.has(key):
		return _preview_cache[key]
	var it: ItemInstance = null
	var out: Dictionary = r.out
	if out.has("base"):
		it = DB.make_item(out.base, BH.Rarity.COMMON, hero.progress.level, 7)
		if it:
			it.count = int(out.get("count", 1))
	else:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(key)
		var base := Crafting.pick_base(hero, r, variant, rng)
		if base:
			var g: Dictionary = out.gear
			it = ItemGenerator.generate(base, hero.progress.level + int(g.get("ilvl_bonus", 0)), int(g.rarity), rng)
			it.quality = float((g.get("quality", [0.1, 0.1]) as Array)[0])
			it.crafted = true
	_preview_cache[key] = it
	return it

# ---- detail -----------------------------------------------------------------------------------------------------

func _variant_index() -> int:
	var i := _variant.selected
	return _variant_order[i] if i >= 0 and i < _variant_order.size() else 0

func _refresh_detail() -> void:
	var r := _current()
	var has := not r.is_empty()
	_craft_btn.disabled = true
	for c in _ingredients.get_children():
		c.queue_free()
	if not has:
		_out_slot.set_item(null)
		_out_name.text = "No recipes here"
		_out_meta.text = ""
		_out_text.text = ""
		_variant_row.visible = false
		return
	var gear := Crafting.is_gear(r)
	_variant_row.visible = gear
	if gear:
		_fill_variants(r)
	var v := _variant_index() if gear else 0
	var it := _preview(r, v)
	_out_slot.set_item(it)
	_out_name.text = String(r.name)
	var verb := String(DataCrafting.STATIONS.get(station, {}).get("verb", "Craft"))
	var meta := [DataCrafting.station_names(r.stations), "Level %d" % int(r.get("level", 1))]
	if int(r.get("gold", 0)) > 0:
		meta.append("Fee %d gold" % int(r.gold))
	_out_meta.text = " · ".join(meta)
	var txt := String(r.get("text", ""))
	if txt == "" and it:
		txt = it.base.flavor
	if not Crafting.is_known(hero, r):
		var sc := Crafting.scroll_for(StringName(r.id))
		var src := ""
		for s in DataCrafting.SCROLLS:
			if s[0] == sc:
				src = s[3]
		txt = "You have not learned this recipe. Read a %s to learn it (found at: %s)." % [DB.item_base(sc).display_name if DB.item_base(sc) else "recipe scroll", src]
	_out_text.text = txt
	var times := int(_qty.value)
	for inp in r.inputs:
		var b := DB.item_base(inp[0])
		var need := int(inp[1]) * times
		var have := hero.inventory.count_of(inp[0])
		var line := hbox(12)
		var sl := ItemSlot.new(ItemSlot.Kind.DISPLAY, 48.0)
		sl.drag_enabled = false
		var sample := DB.make_item(inp[0], BH.Rarity.COMMON, 1, 3)
		sl.set_item(sample)
		sl.hovered.connect(func(s2: ItemSlot, inside: bool) -> void:
			if inside:
				TooltipLayer.show_for(s2, func() -> Control: return Tips.item(sample, {"hero": hero, "hint": _where(inp[0])}))
			else:
				TooltipLayer.hide_for(s2))
		line.add_child(sl)
		var nl := UITheme.label(b.display_name if b else String(inp[0]), 19, UITheme.TEXT, UITheme.body_font())
		nl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(nl)
		var cl := UITheme.label("%d / %d" % [have, need], 20, UITheme.GOOD if have >= need else UITheme.BAD, UITheme.number_font())
		cl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(cl)
		_ingredients.add_child(line)
	var err := Crafting.check(hero, r, station, times, v)
	_craft_btn.disabled = err != ""
	_craft_btn.text = ("%s ×%d" % [verb, times]) if times > 1 else verb
	if err != "" and _result.text == "":
		_result.add_theme_color_override("font_color", UITheme.TEXT_DIM)
		_result.text = err
	_max_btn.disabled = Crafting.max_craftable(hero, r) <= 1

## Where an ingredient comes from (tooltip hint).
func _where(id: StringName) -> String:
	if GatherNode.LOOK.has(id):
		return "Gathered from herb patches in the wild."
	var from := []
	for e: EnemyDef in DB.enemies.values():
		for l in e.loot:
			if l[0] == id and not from.has(e.display_name):
				from.append(e.display_name)
	if id == &"champion_essence":
		return "Dropped by minibosses and the Hollow Warden."
	for r in DataCrafting.all():
		if (r.out as Dictionary).get("base", &"") == id:
			from.append("crafted (%s)" % r.name)
	return ("Dropped by: " + ", ".join(from)) if not from.is_empty() else ""

func _fill_variants(r: Dictionary) -> void:
	var vs: Array = r.get("variants", [])
	var mastery: Dictionary = hero.cls.weapon_mastery
	var order := range(vs.size())
	order.sort_custom(func(a, b):
		var ma := _variant_mastered(vs[a], mastery)
		var mb := _variant_mastered(vs[b], mastery)
		return ma and not mb or (ma == mb and a < b))
	var keep := _variant_index() if _variant_order.size() == vs.size() else -1
	if _variant.item_count != vs.size() or _variant.get_meta(&"recipe", &"") != r.id:
		_variant.clear()
		_variant_order = order
		for i in order:
			var label := String(vs[i].label)
			if _variant_mastered(vs[i], mastery) and (vs[i].get("weapon_types", []) as Array).size() > 0:
				label += "  (your class)"
			_variant.add_item(label)
		_variant.set_meta(&"recipe", r.id)
		_variant.select(0)
	elif keep >= 0:
		_variant.select(_variant_order.find(keep))

static func _variant_mastered(v: Dictionary, mastery: Dictionary) -> bool:
	for w in v.get("weapon_types", []):
		if mastery.has(w):
			return true
	return false

func _on_out_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	var r := _current()
	var hint := "Example: enchantments roll when you craft." if Crafting.is_gear(r) else ""
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": hero, "hint": hint}))

func _craft() -> void:
	var r := _current()
	if r.is_empty():
		return
	var times := int(_qty.value)
	var res := Crafting.craft(hero, r, station, times, _variant_index() if Crafting.is_gear(r) else 0)
	if not res.ok:
		Events.notify.emit(String(res.error), &"error")
		Audio.play_ui(&"ui_error")
		return
	var names := []
	for it in res.items:
		names.append(it.display_name() + (" ×%d" % it.count if it.count > 1 else ""))
	_result.add_theme_color_override("font_color", UITheme.GOOD)
	_result.text = "Made: %s" % ", ".join(names)
	Audio.play_ui(&"level_up" if Crafting.is_gear(r) else (&"gold_pickup" if Audio.has_sound(&"gold_pickup") else &"ui_click"))
	Events.notify.emit("Crafted %s" % ", ".join(names), &"loot")
	if Game.player is Player:
		var c := Color(1.0, 0.6, 0.3) if station == &"forge" else (Color(0.5, 1.0, 0.7) if station == &"alchemy" else Color(1.0, 0.85, 0.5))
		FX.spawn(VFXLib.particles(c, 22, 1.0, true, 0.35, 2.4, 50.0, Vector3(0, 2.0, 0), 0.5), (Game.player as Node3D).global_position + Vector3.UP)
	_preview_cache.clear()
	_qty.value = 1
	_refresh_list()
	_refresh_detail()

# ---- salvage ----------------------------------------------------------------------------------------------------

func _refresh_salvage() -> void:
	for i in _salvage_bag.size():
		var it: ItemInstance = hero.inventory.cells[i]
		_salvage_bag[i].set_item(it)
		_salvage_bag[i].dim = it != null and (not it.is_equipment() or it.is_protected())
	var marked := _marked()
	_salvage_junk.disabled = marked.is_empty()
	_salvage_junk.text = "Salvage Marked Items (%d)" % marked.size() if not marked.is_empty() else "Salvage Marked Items"

func _marked() -> Array:
	return hero.inventory.junk_items().filter(func(it): return it.is_equipment() and not it.is_protected())

static func yield_text(it: ItemInstance) -> String:
	var parts := []
	for y in DataCrafting.salvage_yield(it):
		var b := DB.item_base(y[0])
		parts.append("%d %s" % [int(y[1]), b.display_name if b else String(y[0])])
	return ", ".join(parts)

func _on_salvage_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	var hint := ("Right-click to salvage: " + yield_text(it)) if it.is_equipment() and not it.is_protected() else ("Locked" if it.is_protected() else "Cannot be salvaged")
	_salvage_info.text = ("%s → %s" % [it.display_name(), yield_text(it)]) if it.is_equipment() else ""
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": hero, "hint": hint}))

func _on_salvage_clicked(s: ItemSlot, button: int, _shift: bool, ctrl: bool) -> void:
	if s.item == null or not (button == MOUSE_BUTTON_RIGHT or ctrl):
		return
	var it := s.item
	var go := func() -> void:
		var r := Crafting.salvage(hero, it)
		if r.ok:
			Audio.play_ui(&"ui_click")
			Events.notify.emit("Salvaged %s: %s" % [it.display_name(), ", ".join((r.items as Array).map(func(m): return "%d %s" % [m.count, m.base.display_name]))], &"loot")
		else:
			Events.notify.emit(String(r.error), &"error")
			Audio.play_ui(&"ui_error")
		TooltipLayer.hide_for(null)
	if it.rarity >= BH.Rarity.ELITE:
		Game.ui_root.ask("Salvage", "Break down %s for %s?" % [it.display_name(), yield_text(it)], go, "Salvage", true)
	else:
		go.call()

func _salvage_marked() -> void:
	var list := _marked()
	if list.is_empty():
		return
	Game.ui_root.ask("Salvage Marked Items", "Break down %d marked item%s?" % [list.size(), "" if list.size() == 1 else "s"], func() -> void:
		var n := 0
		for it in list:
			if Crafting.salvage(hero, it).ok:
				n += 1
		Events.notify.emit("Salvaged %d item%s" % [n, "" if n == 1 else "s"], &"loot"), "Salvage", true)
