class_name LapeWindow
extends UIWindow
## bh-019: Lape the Ancient's trading table. Top: Lape (portrait) and what he says. Middle left: three brass dishes
## — click an item in your bag (below) to lay it in the first free dish, click a dish to take it back. "Ask Lape to
## Appraise" gives his remarks on each item, the facts he identifies, what each is worth, and then his offer on the
## right: three special-crafted, licensed pieces with their requirements spelled out, or the gold. Rules: LapeTrade.
## bh-041: three to five offers of several kinds (crafted, reforged, set-mending, Fabled, Ascendant, crystal hoards),
## each card naming its kind; the chance of the last work for the lot laid down; "Ask Lape to Look Again" (paid) draws
## a new set from the same lot; an Eschaton piece among the offers is revealed with EschatonReveal and keeps a chrome
## shimmer on its card.

const DISH_PX := 118.0
const BAG_PX := 58.0

var hero: HeroData
var dishes: Array = []            # ItemInstance or null, LapeTrade.MAX_ITEMS long
var appraisal := {}
var _dish_slots: Array = []
var _dish_vals: Array = []
var _speech: RichTextLabel
var _speech_scroll: ScrollContainer
var _bag: GridContainer
var _offers: VBoxContainer
var _appraise_btn: Button
var _total: Label
var _gold: Label
var _said_hello := false
var _chance: Label
var _redraw_btn: Button
var _animate := false               # the next _fill_offers deals the cards in one by one

func _init() -> void:
	super._init("Lape the Ancient — Relic Appraiser", Vector2(1640, 980))

func open_for(npc_name := "Lape the Ancient") -> void:
	set_title("%s — Relic Appraiser" % npc_name)
	dishes = []
	dishes.resize(LapeTrade.MAX_ITEMS)
	appraisal = {}
	_said_hello = false
	Game.ui_root.open(&"lape")

func _build() -> void:
	if dishes.is_empty():
		dishes.resize(LapeTrade.MAX_ITEMS)
	var cols := hbox(22)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	# ---------------------------------------------------------------- left: Lape, the dishes, your bag
	var left := vbox(10)
	left.custom_minimum_size = Vector2(790, 0)
	cols.add_child(left)
	var top := hbox(16)
	left.add_child(top)
	var por := TextureRect.new()
	por.custom_minimum_size = Vector2(170, 170)
	por.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	por.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	var lape := DB.npc(&"lape")
	if lape and lape.portrait != "" and ResourceLoader.exists(lape.portrait):
		por.texture = UIArt.tex(lape.portrait)
	elif ResourceLoader.exists("res://assets/ui/portraits/lape.svg"):
		por.texture = load("res://assets/ui/portraits/lape.svg")
	top.add_child(por)
	var sp := inset(Vector2(0, 250))
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(sp)
	_speech_scroll = ScrollContainer.new()
	_speech_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_speech_scroll.custom_minimum_size = Vector2(0, 240)
	sp.add_child(_speech_scroll)
	_speech = RichTextLabel.new()
	_speech.bbcode_enabled = true
	_speech.fit_content = true
	_speech.scroll_active = false
	_speech.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_speech.add_theme_font_override("normal_font", UITheme.body_font())
	_speech.add_theme_font_override("bold_font", UITheme.body_bold())
	_speech.add_theme_font_size_override("normal_font_size", 18)
	_speech.add_theme_font_size_override("bold_font_size", 18)
	_speech.add_theme_color_override("default_color", UITheme.PARCHMENT)
	_speech_scroll.add_child(_speech)
	left.add_child(section("The Brass Dishes"))
	var dr := hbox(26)
	dr.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(dr)
	for i in LapeTrade.MAX_ITEMS:
		var col := vbox(4)
		col.alignment = BoxContainer.ALIGNMENT_CENTER
		dr.add_child(col)
		var dish := BrassDish.new()
		dish.custom_minimum_size = Vector2(DISH_PX + 34, DISH_PX + 34)
		col.add_child(dish)
		var s := ItemSlot.new(ItemSlot.Kind.DISPLAY, DISH_PX)
		s.drag_enabled = false
		s.index = i
		s.position = Vector2(17, 17)
		s.clicked.connect(func(sl: ItemSlot, _b: int, _s: bool, _c: bool) -> void: _take_back(sl.index))
		s.hovered.connect(_on_hover)
		s.dropped.connect(func(from: ItemSlot, _to: ItemSlot) -> void:
			if from.kind == ItemSlot.Kind.INVENTORY and from.item:
				_lay(from.item, i))
		dish.add_child(s)
		_dish_slots.append(s)
		var vl := UITheme.label("empty", 16, UITheme.TEXT_MUTED, UITheme.number_font())
		vl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vl.custom_minimum_size.x = DISH_PX + 34
		col.add_child(vl)
		_dish_vals.append(vl)
	var br := hbox(14)
	br.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(br)
	_appraise_btn = button("Ask Lape to Appraise", _appraise, &"PrimaryButton", 320.0)
	_appraise_btn.custom_minimum_size.y = 52
	br.add_child(_appraise_btn)
	var clr := button("Take Everything Back", _clear, &"", 260.0)
	clr.custom_minimum_size.y = 52
	br.add_child(clr)
	_chance = UITheme.label("", 17, BH.rarity_color(BH.Rarity.ESCHATON), UITheme.body_bold())
	_chance.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_chance.visible = false
	left.add_child(_chance)
	left.add_child(section("Your Bag  (click an item to lay it in a dish)"))
	var bw := inset()
	bw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(bw)
	var bs := ScrollContainer.new()
	bs.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	bw.add_child(bs)
	_bag = GridContainer.new()
	_bag.columns = 11
	_bag.add_theme_constant_override("h_separation", 6)
	_bag.add_theme_constant_override("v_separation", 6)
	bs.add_child(_bag)
	# ---------------------------------------------------------------- right: the offer
	var right := vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	right.add_child(section("Lape's Offer"))
	var ow := inset()
	ow.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(ow)
	var os := ScrollContainer.new()
	os.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	ow.add_child(os)
	_offers = vbox(10)
	_offers.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	os.add_child(_offers)
	var foot := hbox(12)
	right.add_child(foot)
	_total = UITheme.label("", 20, UITheme.PARCHMENT, UITheme.body_bold())
	_total.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(_total)
	_gold = UITheme.label("", 20, UITheme.GOLD, UITheme.number_font())
	foot.add_child(_gold)
	_redraw_btn = button("Ask Lape to Look Again", _redraw, &"", 360.0)
	_redraw_btn.custom_minimum_size.y = 48
	_redraw_btn.visible = false
	right.add_child(_redraw_btn)

func refresh() -> void:
	hero = Game.hero
	if hero == null or _bag == null:
		return
	if dishes.size() != LapeTrade.MAX_ITEMS:
		dishes.resize(LapeTrade.MAX_ITEMS)
	# an item that left the bag (sold, dropped, equipped) leaves its dish too
	for i in dishes.size():
		if dishes[i] != null and hero.inventory.index_of(dishes[i]) < 0:
			dishes[i] = null
			appraisal = {}
	if not _said_hello:
		_said_hello = true
		_speech.clear()
		var rng := RandomNumberGenerator.new()
		rng.randomize()
		_say([DataLapeLines.fill(DataLapeLines.pick(DataLapeLines.IDLE, rng), null, hero.hero_name)])
	_fill_dishes()
	_fill_bag()
	_fill_offers()
	_gold.text = "%s gold" % SocketWindow._thousands(hero.inventory.gold)

func _laid() -> Array:
	return dishes.filter(func(x): return x != null)

func _fill_dishes() -> void:
	var per := {}
	if not appraisal.is_empty():
		for e in appraisal.items:
			per[e.item] = int(e.value)
	for i in dishes.size():
		var s: ItemSlot = _dish_slots[i]
		s.set_item(dishes[i])
		var vl: Label = _dish_vals[i]
		if dishes[i] == null:
			vl.text = "empty"
			vl.add_theme_color_override("font_color", UITheme.TEXT_MUTED)
		elif per.has(dishes[i]):
			vl.text = "%s gold" % SocketWindow._thousands(per[dishes[i]])
			vl.add_theme_color_override("font_color", UITheme.GOLD)
		else:
			vl.text = "not yet appraised"
			vl.add_theme_color_override("font_color", UITheme.TEXT_DIM)
	_appraise_btn.disabled = _laid().is_empty()
	var ch := LapeTrade.eschaton_chance(_laid())
	_chance.visible = ch > 0.0
	_chance.text = "The last work (Eschaton): %d%% each time Lape looks at this lot" % roundi(ch * 100.0)

func _fill_bag() -> void:
	for c in _bag.get_children():
		_bag.remove_child(c)
		c.queue_free()
	for i in hero.inventory.cells.size():
		var it: ItemInstance = hero.inventory.cells[i]
		var s := ItemSlot.new(ItemSlot.Kind.INVENTORY, BAG_PX)
		s.index = i
		s.drag_enabled = it != null
		s.set_item(it)
		if it != null:
			s.dim = dishes.has(it) or LapeTrade.refuse_reason(it) != ""
			s.selected = dishes.has(it)
		s.clicked.connect(func(sl: ItemSlot, _b: int, _s: bool, _c: bool) -> void:
			if sl.item:
				_lay(sl.item, -1))
		s.hovered.connect(_on_hover)
		_bag.add_child(s)

func _lay(it: ItemInstance, at: int) -> void:
	if dishes.has(it):
		_take_back(dishes.find(it))
		return
	var why := LapeTrade.refuse_reason(it)
	if why != "":
		_say([why], UITheme.BAD)
		Audio.play_ui(&"ui_error")
		return
	var idx := at if at >= 0 and dishes[at] == null else dishes.find(null)
	if idx < 0:
		_say(["Three dishes, three things. Take one back first."], UITheme.BAD)
		Audio.play_ui(&"ui_error")
		return
	dishes[idx] = it
	appraisal = {}
	Audio.play_ui(&"ui_click")
	refresh()

func _take_back(i: int) -> void:
	if i < 0 or i >= dishes.size() or dishes[i] == null:
		return
	dishes[i] = null
	appraisal = {}
	Audio.play_ui(&"ui_click")
	refresh()

func _clear() -> void:
	for i in dishes.size():
		dishes[i] = null
	appraisal = {}
	refresh()

func _appraise() -> void:
	var lot := _laid()
	if lot.is_empty():
		return
	appraisal = LapeTrade.appraise(hero, lot)
	_animate = true
	_speech.clear()
	for e in appraisal.items:
		var it: ItemInstance = e.item
		_speech.push_color(it.color())
		_speech.push_font(UITheme.body_bold())
		_speech.add_text(it.display_name())
		_speech.pop()
		_speech.pop()
		_speech.add_text("\n")
		for l in e.lines:
			_speech.add_text("“%s”  " % l)
		_speech.add_text("\n")
		_speech.push_color(UITheme.TEXT_DIM)
		for f in e.facts:
			_speech.add_text("Identified: %s\n" % f)
		_speech.pop()
		_speech.push_color(UITheme.GOLD)
		_speech.add_text("Worth %s gold to Lape.\n\n" % SocketWindow._thousands(int(e.value)))
		_speech.pop()
	for l in appraisal.summary:
		_speech.push_font(UITheme.body_bold())
		_speech.add_text("“%s”\n" % l)
		_speech.pop()
	_speech_scroll.scroll_vertical = 0
	Audio.play_ui(&"ui_craft" if Audio.has_sound(&"ui_craft") else &"ui_open")
	refresh()
	_reveal_last_work()

## bh-041: the draw holds an Eschaton piece: the eclipse opens over the table.
func _reveal_last_work() -> void:
	if not appraisal.get("eschaton", false):
		return
	var kinds: Array = appraisal.get("kinds", [])
	var at := kinds.find(&"eschaton")
	if at >= 0:
		EschatonReveal.play(self, appraisal.offers[at], func() -> void:
			# back at the table: the last work's card is brought into view
			if at < _offers.get_child_count():
				var card := _offers.get_child(at) as Control
				var sc := _offers.get_parent() as ScrollContainer
				if card and sc:
					sc.ensure_control_visible(card))

## bh-041: pay Lape to draw again from the same lot.
func _redraw() -> void:
	var lot := _laid()
	if lot.is_empty() or appraisal.is_empty():
		return
	var r := LapeTrade.redraw(hero, lot, appraisal)
	if not r.ok:
		_say([String(r.error)], UITheme.BAD)
		Audio.play_ui(&"ui_error")
		return
	appraisal = r.appraisal
	_animate = true
	_speech.clear()
	_speech.push_color(UITheme.GOLD)
	_speech.add_text("You pay Lape %s gold to look again.\n" % SocketWindow._thousands(int(r.cost)))
	_speech.pop()
	for l in appraisal.summary:
		_speech.push_font(UITheme.body_bold())
		_speech.add_text("“%s”\n" % l)
		_speech.pop()
	Audio.play_ui(&"ui_buy" if Audio.has_sound(&"ui_buy") else &"ui_click")
	refresh()
	_reveal_last_work()

func _say(lines: Array, col := UITheme.PARCHMENT) -> void:
	_speech.push_color(col)
	for l in lines:
		_speech.add_text("“%s”\n" % l)
	_speech.pop()
	_scroll_down.call_deferred()

func _scroll_down() -> void:
	if is_instance_valid(_speech_scroll):
		_speech_scroll.scroll_vertical = int(_speech_scroll.get_v_scroll_bar().max_value)

func _fill_offers() -> void:
	for c in _offers.get_children():
		_offers.remove_child(c)
		c.queue_free()
	if appraisal.is_empty():
		_redraw_btn.visible = false
		var t := UITheme.label("Lay up to three items from your bag in the brass dishes, then ask Lape to appraise them.\n\nHe will tell you what each one really is and what it is worth, then offer you three to five pieces, or the gold. What you lay down steers what he makes: kinds of gear, elements and crystals, sets he can mend, Fabled and Ascendant work. Lay down the highest tiers there are and he may make the last work of all: Eschaton.\n\nNot taken with his offer? Pay him to look at the same lot again.",
			18, UITheme.TEXT_DIM, UITheme.body_font())
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size.x = 640
		_offers.add_child(t)
		_total.text = ""
		return
	_total.text = "The lot is worth %s gold" % SocketWindow._thousands(int(appraisal.value))
	_redraw_btn.visible = bool(appraisal.craft)
	if appraisal.craft:
		var cost := LapeTrade.redraw_cost(appraisal, int(appraisal.get("draw", 0)) + 1)
		_redraw_btn.text = "Ask Lape to Look Again — %s gold" % SocketWindow._thousands(cost)
		_redraw_btn.disabled = hero.inventory.gold < cost
		var n := 0
		var kinds: Array = appraisal.get("kinds", [])
		for it: ItemInstance in appraisal.offers:
			var card := _offer_card(it, n, kinds[n] if n < kinds.size() else &"crafted")
			_offers.add_child(card)
			if _animate:
				card.modulate.a = 0.0
				var tw := card.create_tween()
				tw.tween_interval(0.12 * n)
				tw.tween_property(card, "modulate:a", 1.0, 0.25)
			n += 1
	else:
		var t := UITheme.label("Lape will craft for a lot worth at least %s gold (at your level). For this one he offers coin." % SocketWindow._thousands(LapeTrade.craft_floor(hero.progress.level)),
			17, UITheme.TEXT_DIM, UITheme.body_font())
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		t.custom_minimum_size.x = 640
		_offers.add_child(t)
	_offers.add_child(_gold_card())
	_animate = false

func _offer_card(it: ItemInstance, n: int, kind: StringName = &"crafted") -> Control:
	var card := PanelContainer.new()
	var last_work := kind == &"eschaton"
	card.add_theme_stylebox_override("panel", UITheme.panel_style(Color(0.03, 0.03, 0.05, 0.97) if last_work else Color(0.06, 0.05, 0.06, 0.95),
		it.color() if last_work else it.color().darkened(0.35), 4, 3 if last_work else 2, 0))
	var h := hbox(14)
	card.add_child(h)
	var s := ItemSlot.new(ItemSlot.Kind.DISPLAY, 88.0)
	s.drag_enabled = false
	s.set_item(it)
	s.hovered.connect(_on_hover)
	s.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(s)
	var v := vbox(3)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var nl := UITheme.label(it.display_name(), 20, it.color(), UITheme.body_bold())
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	nl.custom_minimum_size.x = 380
	v.add_child(nl)
	var kl := UITheme.label(String(DataLapeLines.OFFER_KIND.get(kind, "")), 16 if last_work else 15,
		it.color() if last_work else UITheme.GOLD, UITheme.body_bold())
	v.add_child(kl)
	v.add_child(UITheme.label("%s %s · item level %d" % [it.rarity_name(), it.base.display_name, it.ilvl] if it.is_equipment() else "%d x %s" % [it.count, it.base.display_name],
		15, UITheme.TEXT_DIM, UITheme.body_font()))
	for r in LapeTrade.requirements(hero, it):
		var ok: Variant = r[1]
		var l := UITheme.label(("• " if ok == null else ("✓ " if ok else "✗ ")) + String(r[0]), 15,
			UITheme.PARCHMENT if ok == null else (UITheme.GOOD if ok else UITheme.BAD), UITheme.body_font())
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size.x = 380
		v.add_child(l)
	var b := button("Choose", func() -> void: _choose(n), &"PrimaryButton", 130.0)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.custom_minimum_size.y = 50
	h.add_child(b)
	if last_work:
		var shine := ChromeShine.new()
		shine.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(shine)
	return card

func _gold_card() -> Control:
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", UITheme.panel_style(Color(0.07, 0.06, 0.04, 0.95), UITheme.BRONZE, 4, 2, 0))
	var h := hbox(14)
	card.add_child(h)
	var l := UITheme.label("Or take the gold: %s" % SocketWindow._thousands(int(appraisal.value)), 20, UITheme.GOLD, UITheme.body_bold())
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(l)
	var b := button("Take the Gold", func() -> void: _choose(-1), &"", 200.0)
	b.custom_minimum_size.y = 50
	h.add_child(b)
	return card

func _choose(n: int) -> void:
	var lot := _laid()
	if lot.is_empty() or appraisal.is_empty():
		return
	var names := PackedStringArray()
	for it: ItemInstance in lot:
		names.append(it.display_name())
	var what: String = "%s gold" % SocketWindow._thousands(int(appraisal.value)) if n < 0 else (appraisal.offers[n] as ItemInstance).display_name()
	Game.ui_root.ask("Trade with Lape", "Give Lape %s\nand take %s?\nThe trade cannot be undone." % [", ".join(names), what], func() -> void:
		var r := LapeTrade.accept(hero, lot, appraisal, n)
		if not r.ok:
			_say([String(r.error)], UITheme.BAD)
			Audio.play_ui(&"ui_error")
			return
		for i in dishes.size():
			dishes[i] = null
		appraisal = {}
		_speech.clear()
		_say([String(r.line)])
		if r.item and r.kind == &"eschaton":
			# the last work leaves the table: the eclipse once more, and its light over the hero
			EschatonReveal.play(self, r.item, Callable(), true)
			var p := Game.player as Node3D
			if p and FX.world:
				FX.spawn(AscendantFx.pillar(BH.Rarity.ESCHATON, 16.0), p.global_position)
			Events.notify.emit("Lape made the last work for you: %s" % (r.item as ItemInstance).display_name(), &"loot")
		elif r.item:
			Events.notify.emit("Lape crafted %s for you" % (r.item as ItemInstance).display_name(), &"loot")
		else:
			Events.notify.emit("+%s gold from Lape" % SocketWindow._thousands(int(r.gold)), &"gold")
		Audio.play_ui(&"ui_buy" if Audio.has_sound(&"ui_buy") else &"ui_click")
		refresh(), "Trade")

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	var h := hero
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": h}))


## bh-041: the chrome shimmer over an Eschaton offer card: a white sheen sweeping across it and the spectrum running
## round its edge.
class ChromeShine extends Control:
	var _t := 0.0
	func _process(delta: float) -> void:
		_t += delta
		queue_redraw()
	func _draw() -> void:
		var w := size.x
		var h := size.y
		var u := fmod(_t * 0.35, 1.5) - 0.25
		var x := u * (w + h)
		for i in 9:
			var f := 1.0 - absf(float(i) - 4.0) / 5.0
			var o := x + i * 5.0
			draw_line(Vector2(o, 0), Vector2(o - h, h), Color(1, 1, 1, 0.07 * f), 4.0)
		var n := 72
		for i in n:
			var k := float(i) / n
			var col := Color(0.5 + 0.5 * cos(TAU * (k - _t * 0.2)), 0.5 + 0.5 * cos(TAU * (k - _t * 0.2 + 0.33)), 0.5 + 0.5 * cos(TAU * (k - _t * 0.2 + 0.67)), 0.85)
			var p0 := _edge(k)
			var p1 := _edge(k + 1.0 / n)
			draw_line(p0, p1, col, 2.5)
	func _edge(k: float) -> Vector2:
		var w := size.x
		var h := size.y
		var d := fposmod(k, 1.0) * 2.0 * (w + h)
		if d < w:
			return Vector2(d, 1)
		d -= w
		if d < h:
			return Vector2(w - 1, d)
		d -= h
		if d < w:
			return Vector2(w - d, h - 1)
		return Vector2(1, h - (d - w))

## A brass offering dish: a shallow bowl with a bright rim and a dark velvet bed, behind the item slot.
class BrassDish extends Control:
	func _draw() -> void:
		var c := size * 0.5
		var r := minf(size.x, size.y) * 0.5 - 2.0
		draw_circle(c + Vector2(0, 5), r, Color(0, 0, 0, 0.45))
		draw_circle(c, r, Color(0.36, 0.25, 0.1))
		draw_circle(c, r - 5.0, Color(0.62, 0.46, 0.2))
		draw_circle(c, r - 11.0, Color(0.1, 0.03, 0.05))
		for k in 3:
			draw_circle(c, (r - 13.0) * (1.0 - k * 0.12), Color(0.35, 0.08, 0.14, 0.12))
		draw_arc(c, r - 1.5, PI * 1.05, PI * 1.7, 24, Color(1.0, 0.9, 0.6, 0.55), 2.5, true)
		draw_arc(c, r - 8.0, 0, TAU, 64, Color(0.25, 0.16, 0.06), 2.0, true)
