class_name DebugWindow
extends UIWindow
## bh-030: the Debug console. Unlocked per hero by the `azrin azrael` cheat (a Debug button on the HUD, F2). Pages:
##   Cheats     every chat cheat code as a button (Cheats.DESCRIPTIONS)
##   Hero       set gold, level, experience, points, attributes, class rank, embers, Well Rested; restore, revive, resets
##   Items      the Item Summoner: filters, a full catalogue, any rarity forced exactly, item level, quality, sockets and
##              crystals, chosen enchantments and powers, Unbound, equip at once, a live preview (bh-039)
##   Tempos     the Tempo Summoner: nameless spirits by class and grade or renowned spirits, stars, resonance; and the
##              Unsummoner: rest, bind, revive or remove any bound or hall spirit
##   Combat     god mode, infinite Mana, no cooldowns, one-hit kills; damage, speed, XP, gold multipliers; drop rarity floor
##   World      spawn monsters (count, level, elite, champion mods), kill all, freeze monsters, travel, waypoints, story
##              flags, dungeon recovery and champion timers, the Quake Team
##   Technical  overlays, time scale, frame cap, VSync, physics rate, render debug views, first-person view and its
##              field of view, live engine counters, save / reload, stat dump
## Nothing here works on an official server (Official.active) or for a multiplayer guest (only the host).

const PAGES := [["cheats", "Cheats"], ["hero", "Hero"], ["items", "Items"], ["tempos", "Tempos"], ["combat", "Combat"],
	["world", "World"], ["tech", "Technical"]]

var page := "cheats"
var _tabs: HBoxContainer
var _page_box: VBoxContainer
var _log: RichTextLabel
var _live: Label
var _live_t := 0.0
# item summoner
var _search: LineEdit
var _base_ids: Array = []
var _ilvl: SpinBox
var _quality: SpinBox
var _sockets: SpinBox
var _count: SpinBox
var _perfect: CheckBox
const CATEGORIES := ["all", "weapon", "shield", "helm", "armor", "inner_garment", "leggings", "gloves", "boots", "accessory",
	"consumable", "material", "crystal"]
# tempo summoner
var _t_kind: OptionButton
var _t_class: OptionButton
var _t_legend: OptionButton
var _t_grade: OptionButton
var _t_stars: OptionButton
var _t_res: SpinBox
var _t_name: LineEdit
var _t_list: VBoxContainer
var _legend_ids: Array = []

func _init() -> void:
	super._init("Debug Console", Vector2(1500, 960))

func _build() -> void:
	_tabs = hbox(6)
	body.add_child(_tabs)
	for p in PAGES:
		var id: String = p[0]
		var b := button(p[1], func() -> void: show_page(id), &"", 150.0)
		b.toggle_mode = true
		b.set_meta(&"page", id)
		b.custom_minimum_size.y = 52 if Settings.touch_mode else 42
		_tabs.add_child(b)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)
	_page_box = vbox(10)
	_page_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_page_box)
	var lw := inset(Vector2(0, 120))
	body.add_child(lw)
	_log = RichTextLabel.new()
	_log.bbcode_enabled = true
	_log.scroll_following = true
	_log.custom_minimum_size = Vector2(0, 110)
	_log.add_theme_font_size_override("normal_font_size", 16)
	lw.add_child(_log)

func refresh() -> void:
	show_page(page)

func show_page(id: String) -> void:
	page = id
	for b in _tabs.get_children():
		(b as Button).set_pressed_no_signal(String(b.get_meta(&"page")) == id)
	for c in _page_box.get_children():
		_page_box.remove_child(c)
		c.queue_free()
	_live = null
	if not _allowed():
		_page_box.add_child(_text("The Debug console is unavailable here: %s" % _why()))
		return
	match id:
		"cheats": _page_cheats()
		"hero": _page_hero()
		"items": _page_items()
		"tempos": _page_tempos()
		"combat": _page_combat()
		"world": _page_world()
		"tech": _page_tech()

func _allowed() -> bool:
	return _why() == ""

func _why() -> String:
	if Official.active:
		return "official characters cannot use cheats."
	if Net.is_active() and not Net.is_host():
		return "only the host can use cheats in Multiplayer."
	if Game.hero == null:
		return "no hero."
	return ""

# ---- small builders ------------------------------------------------------------------------------------------------

func _text(t: String, size := 17, col := UITheme.TEXT) -> Label:
	var l := UITheme.label(t, size, col, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l

func _head(t: String) -> void:
	_page_box.add_child(section(t))

func _row(ctrls: Array) -> HBoxContainer:
	var h := hbox(8)
	for c in ctrls:
		h.add_child(c)
	_page_box.add_child(h)
	return h

func _b(t: String, cb: Callable, w := 0.0, variation := &"") -> Button:
	var b := button(t, cb, variation, w)
	b.custom_minimum_size.y = 52 if Settings.touch_mode else 40
	return b

func _spin(lo: float, hi: float, v: float, step := 1.0, w := 150.0) -> SpinBox:
	var s := SpinBox.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = v
	s.allow_greater = false
	s.custom_minimum_size = Vector2(w, 52 if Settings.touch_mode else 40)
	s.select_all_on_focus = true
	return s

func _check(t: String, on: bool, cb: Callable) -> CheckBox:
	var c := CheckBox.new()
	c.text = t
	c.button_pressed = on
	c.toggled.connect(cb)
	c.custom_minimum_size.y = 48 if Settings.touch_mode else 36
	return c

func _cap(t: String, w := 0.0) -> Label:
	var l := UITheme.label(t, 17, UITheme.PARCHMENT, UITheme.body_bold())
	l.custom_minimum_size.x = w
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return l

func _opt(items: Array, sel := 0, w := 220.0) -> OptionButton:
	var o := OptionButton.new()
	for it in items:
		o.add_item(String(it))
	o.selected = clampi(sel, 0, maxi(0, items.size() - 1))
	o.custom_minimum_size = Vector2(w, 52 if Settings.touch_mode else 40)
	o.fit_to_longest_item = false
	return o

func say(t: String, bad := false) -> void:
	if t == "":
		return
	_log.append_text("[color=%s]%s[/color]\n" % ["#e07060" if bad else "#e8d9a8", t.replace("[", "(")])
	Events.notify.emit(t, &"error" if bad else &"info")

func _hero() -> HeroData:
	return Game.hero

func _player() -> Player:
	return Game.player as Player

# ---- Cheats -------------------------------------------------------------------------------------------------------

func _page_cheats() -> void:
	_head("Every Cheat Code")
	_page_box.add_child(_text("The same codes you can type in chat. Hover a button for what it does.", 16, UITheme.TEXT_DIM))
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	_page_box.add_child(grid)
	for code in Cheats.CODES:
		if code == "azrin azrael":
			continue
		var c: String = code
		var b := _b(c, func() -> void: say(Cheats.apply(c, _hero(), _player())), 340.0)
		TooltipLayer.attach(b, func() -> Control: return Tips.text(String(Cheats.DESCRIPTIONS.get(c, "")), c))
		grid.add_child(b)

# ---- Hero ---------------------------------------------------------------------------------------------------------

func _page_hero() -> void:
	var h := _hero()
	var pr := h.progress
	_head("Gold and Experience")
	var gold := _spin(0, 2000000000, h.inventory.gold, 1, 220)
	_row([_cap("Gold", 160), gold, _b("Set", func() -> void:
		h.inventory.gold = int(gold.value)
		h.inventory.changed.emit()
		say("Gold set to %d." % h.inventory.gold)), _b("Add", func() -> void:
		h.inventory.gold += int(gold.value)
		h.inventory.changed.emit()
		say("Gold now %d." % h.inventory.gold))])
	var lvl := _spin(1, BH.LEVEL_CAP, pr.level)
	_row([_cap("Level", 160), lvl, _b("Set Level", func() -> void: say(_set_level(int(lvl.value))))])
	var xp := _spin(1, 1000000000, 10000, 1, 220)
	_row([_cap("Experience", 160), xp, _b("Give XP", func() -> void:
		var from := pr.level
		pr.add_xp(int(xp.value))
		say("+%d XP (level %d -> %d)." % [int(xp.value), from, pr.level]))])
	_head("Points")
	for pair in [["Stat points", "free_points"], ["Skill points", "skill_points"], ["Talent points", "talent_points"]]:
		var key: String = pair[1]
		var s := _spin(-100000, 100000, 10)
		var lbl: String = pair[0]
		_row([_cap(lbl, 160), s, _b("Add", func() -> void:
			pr.set(key, maxi(0, int(pr.get(key)) + int(s.value)))
			pr.points_changed.emit()
			say("%s: %d." % [lbl, int(pr.get(key))])), _cap("now %d" % int(pr.get(key)))])
	_head("Attributes (points you allocated)")
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 10)
	_page_box.add_child(grid)
	for a in BH.ATTRIBUTES:
		var attr: StringName = a
		var s2 := _spin(0, 100000, int(pr.allocated.get(attr, 0)))
		grid.add_child(_cap(String(attr).to_upper(), 120))
		grid.add_child(s2)
		grid.add_child(_b("Set", func() -> void:
			pr.allocated[attr] = int(s2.value)
			pr.points_changed.emit()
			h.stats_dirty.emit()
			say("%s allocated: %d." % [String(attr).to_upper(), int(s2.value)]), 90.0))
		grid.add_child(Control.new())
	_head("Rank, Embers and Rest")
	var names := []
	for r in DataGuilds.MAX_RANK + 1:
		names.append(DataGuilds.tier_name(r))
	var rank := _opt(names, h.tier, 260)
	_row([_cap("Class rank", 160), rank, _b("Set Rank", func() -> void:
		h.tier_cheat_level = pr.level
		h.set_tier(rank.selected)
		say("Class rank: %s." % DataGuilds.tier_name(h.tier)))])
	var emb := _spin(1, 100000, 100)
	_row([_cap("Soul Embers", 160), emb, _b("Add", func() -> void:
		TempoGacha.add_embers(h, int(emb.value))
		say("+%d Soul Embers (now %d)." % [int(emb.value), TempoGacha.embers(h)]))])
	var rest := _spin(1, 6000, 30)
	_row([_cap("Well Rested (min)", 160), rest, _b("Grant", func() -> void:
		h.rested_until = maxf(h.rested_until, h.play_time) + rest.value * 60.0
		h.stats_dirty.emit()
		say("Well Rested for %d more minutes." % int(rest.value)))])
	_head("Body")
	_row([_b("Full Restore", func() -> void: say(Cheats.apply("azrael", h, _player())), 200.0),
		_b("Revive Hero", _revive, 200.0),
		_b("Refund Stats", func() -> void:
			pr.reset_attributes()
			say("Allocated stat points refunded."), 200.0),
		_b("Reset Skills", _reset_skills, 200.0),
		_b("Reset Talents", func() -> void:
			pr.talent_points += h.talent_tree.reset()
			pr.points_changed.emit()
			say("Talents refunded."), 200.0)])
	var dmg := _spin(1, 10000000, 100, 1, 200)
	_row([_cap("Hurt yourself", 160), dmg, _b("Take Damage", func() -> void: _hurt(dmg.value))])

func _set_level(want: int) -> String:
	var pr := _hero().progress
	if want == pr.level:
		return "Already level %d." % want
	if want > pr.level:
		var from := pr.level
		pr.add_xp(XpCurve.total_xp_for_level(want) - XpCurve.total_xp_for_level(pr.level) - pr.xp)
		return "Level %d -> %d." % [from, pr.level]
	# lowering: the level and the experience go back; points already spent stay spent, unspent ones shrink with it
	var lost := pr.level - want
	pr.level = want
	pr.xp = 0
	pr.total_xp = XpCurve.total_xp_for_level(want)
	pr.free_points = maxi(0, pr.free_points - lost * 3)
	pr.skill_points = maxi(0, pr.skill_points - lost)
	pr.talent_points = maxi(0, pr.talent_points - lost)
	pr.xp_changed.emit()
	pr.points_changed.emit()
	_hero().stats_dirty.emit()
	return "Level lowered to %d." % want

func _revive() -> void:
	var p := _player()
	if p == null:
		return
	if p.alive:
		say("The hero is standing.")
		return
	if p.has_method(&"respawn"):
		p.call(&"respawn")
	elif Game.ui_root and Game.ui_root.pause_menu.has_method(&"respawn"):
		Game.ui_root.pause_menu.call(&"respawn")
	say("The hero stands again.")

func _reset_skills() -> void:
	var h := _hero()
	var pv := NpcServices.respec_preview(h)
	h.skill_tree.reset()
	for s in h.cls.starting_skills:
		h.skill_tree.ranks[s] = 1
	h.progress.skill_points += int(pv.skill_points)
	for i in h.skill_bar.size():
		if h.skill_bar[i] != &"" and h.skill_rank(h.skill_bar[i]) <= 0:
			h.skill_bar[i] = &""
	h.skill_tree.changed.emit()
	h.progress.points_changed.emit()
	h.skills_changed.emit()
	say("Skills refunded.")

func _hurt(v: float) -> void:
	var p := _player()
	if p == null:
		return
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.use_weapon = false
	req.base_min = v
	req.base_max = v
	req.can_crit = false
	req.evadable = false
	req.label = "Debug"
	var r := p.receive_hit(req, null)
	say("You took %d damage." % r.total)

# ---- Items: the Item Summoner ---------------------------------------------------------------------------------------
## bh-039: the summoner is a catalogue with filters (category, weapon type, source, class, element, native rarity, level
## range, a search), a full scrolling list with icons, and a forge: any rarity is exactly that rarity (a Primordial
## sword is a Primordial sword), item level, quality, sockets and their crystals, up to three chosen enchantments and
## three chosen powers, perfect rolls, Unbound (no requirements), equip at once, lock. A live preview card shows the
## exact item that will be summoned; Reroll draws another.

func _page_items() -> void:
	_head("Item Summoner")
	_search = LineEdit.new()
	_search.placeholder_text = "Search names, ids, powers or lore (e.g. serpent, fa_, primordial)"
	_search.custom_minimum_size = Vector2(760, 52 if Settings.touch_mode else 40)
	_search.clear_button_enabled = true
	_search.text_changed.connect(func(_t: String) -> void: _fill_bases())
	_row([_cap("Find", 110), _search, _b("Clear Filters", _clear_filters, 180.0)])
	_chip_rows.clear()
	_chip_row("category", "Category", CATEGORIES.map(func(c): return ["all", "All"] if c == "all" else [c, CAT_NAMES.get(c, String(c).capitalize())]))
	var wts := [["any", "Any"]]
	for id in WEAPON_TYPES:
		wts.append([String(id), DB.weapon_type(id).display_name if DB.weapon_type(id) else String(id).capitalize()])
	_chip_row("wtype", "Weapon", wts)
	_chip_row("source", "Source", SOURCES)
	var cls := ["Any class", "My class"] + CLASS_IDS.map(func(c): return String(c).capitalize())
	_class_opt = _opt(cls, int(_f.get("class", 0)), 200)
	_class_opt.item_selected.connect(func(i: int) -> void:
		_f["class"] = i
		_fill_bases())
	_elem_opt = _opt(["Any element"] + Array(Elements.NAMES), int(_f.get("element", 0)), 180)
	_elem_opt.item_selected.connect(func(i: int) -> void:
		_f["element"] = i
		_fill_bases())
	_native_opt = _opt(["Any native rarity"] + BH.RARITY_NAMES, int(_f.get("native", 0)), 220)
	_native_opt.item_selected.connect(func(i: int) -> void:
		_f["native"] = i
		_fill_bases())
	_lvl_lo = _spin(0, BH.LEVEL_CAP + 5, int(_f.get("lo", 0)), 1, 110)
	_lvl_hi = _spin(0, BH.LEVEL_CAP + 5, int(_f.get("hi", BH.LEVEL_CAP + 5)), 1, 110)
	_lvl_lo.value_changed.connect(func(v: float) -> void:
		_f["lo"] = int(v)
		_fill_bases())
	_lvl_hi.value_changed.connect(func(v: float) -> void:
		_f["hi"] = int(v)
		_fill_bases())
	_row([_cap("Also", 110), _class_opt, _elem_opt, _native_opt, _cap("Level", 70), _lvl_lo, _cap("to", 30), _lvl_hi])
	# catalogue (left) and forge (right)
	var cols := hbox(14)
	_page_box.add_child(cols)
	var left := vbox(6)
	left.custom_minimum_size.x = 560
	cols.add_child(left)
	_count_lbl = _text("", 15, UITheme.TEXT_DIM)
	left.add_child(_count_lbl)
	_list = ItemList.new()
	_list.custom_minimum_size = Vector2(560, 640)
	_list.fixed_icon_size = Vector2i(40, 40)
	_list.add_theme_font_size_override("font_size", 16)
	_list.item_selected.connect(func(i: int) -> void: _pick_base(i))
	_list.item_activated.connect(func(i: int) -> void:
		_pick_base(i)
		_summon_item())
	left.add_child(_list)
	var right := vbox(8)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	_build_forge(right)
	_fill_bases()

const CAT_NAMES := {"weapon": "Weapons", "shield": "Shields", "helm": "Helms", "armor": "Armour", "inner_garment": "Inner", "leggings": "Leggings",
	"gloves": "Gloves", "boots": "Boots", "accessory": "Jewellery", "consumable": "Consumables", "material": "Materials", "crystal": "Crystals"}
const WEAPON_TYPES := [&"sword", &"greatsword", &"axe", &"greataxe", &"spear", &"javelin", &"dagger", &"claw", &"knuckles", &"club", &"bow",
	&"crossbow", &"staff", &"wand"]
const SOURCES := [["any", "Any"], ["plain", "Ordinary"], ["unique", "Uniques"], ["set", "Set pieces"], ["ascendant", "Ascendant"],
	["fabled", "Fabled Arms"], ["story", "Story"]]
const CLASS_IDS := [&"knight", &"mage", &"ranger", &"shadowblade"]

var _f := {"category": "all", "wtype": "any", "source": "any"}
var _chip_rows := {}
var _class_opt: OptionButton
var _elem_opt: OptionButton
var _native_opt: OptionButton
var _lvl_lo: SpinBox
var _lvl_hi: SpinBox
var _list: ItemList
var _count_lbl: Label
var _rar_btns: Array = []
var _rarity_sel := BH.Rarity.LEGENDARY
var _unbound: CheckBox
var _equip_now: CheckBox
var _lock: CheckBox
var _gem_opt: OptionButton
var _gem_ids: Array = []
var _affix_opts: Array = []
var _affix_ids: Array = []
var _power_opts: Array = []
var _power_ids2: Array = []
var _preview_box: VBoxContainer
var _preview: ItemInstance
var _picked: StringName = &""
var _recent: Array = []
var _recent_box: HBoxContainer
var _seed := 0

func _chip_row(key: String, title: String, chips: Array) -> void:
	var h := hbox(4)
	h.add_child(_cap(title, 110))
	var flow := HFlowContainer.new()
	flow.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	flow.add_theme_constant_override("h_separation", 4)
	flow.add_theme_constant_override("v_separation", 4)
	h.add_child(flow)
	for c in chips:
		var val: String = c[0]
		var b := Button.new()
		b.text = c[1]
		b.toggle_mode = true
		b.button_pressed = String(_f.get(key, "")) == val
		b.custom_minimum_size = Vector2(0, 46 if Settings.touch_mode else 34)
		b.set_meta(&"val", val)
		b.pressed.connect(func() -> void:
			_set_chip(key, val)
			if key == "wtype" and val != "any":
				_set_chip("category", "weapon")
			_fill_bases())
		flow.add_child(b)
	_chip_rows[key] = flow
	_page_box.add_child(h)

func _set_chip(key: String, val: String) -> void:
	_f[key] = val
	if _chip_rows.has(key):
		for o in (_chip_rows[key] as Node).get_children():
			(o as Button).set_pressed_no_signal(String(o.get_meta(&"val")) == val)

func _clear_filters() -> void:
	_f = {"category": "all", "wtype": "any", "source": "any"}
	show_page("items")

func _build_forge(box: VBoxContainer) -> void:
	box.add_child(_cap("Rarity (always exactly this one)"))
	var grid := GridContainer.new()
	grid.columns = 7
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	box.add_child(grid)
	_rar_btns.clear()
	for r in BH.RARITY_COUNT:
		var rr: int = r
		var b := Button.new()
		b.text = BH.RARITY_NAMES[r]
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(118, 44 if Settings.touch_mode else 34)
		b.add_theme_color_override("font_color", BH.rarity_color(r))
		b.add_theme_color_override("font_pressed_color", Color.WHITE)
		b.pressed.connect(func() -> void: _set_rarity(rr))
		grid.add_child(b)
		_rar_btns.append(b)
	_set_rarity(_rarity_sel, false)
	_ilvl = _spin(1, BH.LEVEL_CAP + 5, _hero().progress.level, 1, 120)
	_ilvl.value_changed.connect(func(_v: float) -> void: _reroll())
	var mine := _b("My Level", func() -> void: _ilvl.value = _hero().progress.level, 120.0)
	var top := _b("Max", func() -> void: _ilvl.value = BH.LEVEL_CAP + 5, 80.0)
	_quality = _spin(0, 50, 20, 1, 100)
	_quality.value_changed.connect(func(_v: float) -> void: _reroll(false))
	box.add_child(_row_of([_cap("Item level", 100), _ilvl, mine, top, _cap("Quality %", 100), _quality]))
	_sockets = _spin(0, 7, 0, 1, 90)
	_sockets.value_changed.connect(func(_v: float) -> void: _reroll(false))
	_gem_ids = [""]
	var gnames := ["Empty sockets"]
	var crystals := DB.item_bases.values().filter(func(b): return b.category == &"crystal")
	crystals.sort_custom(func(a, b): return [a.fixed_rarity, String(a.display_name)] < [b.fixed_rarity, String(b.display_name)])
	for c in crystals:
		_gem_ids.append(String(c.id))
		gnames.append(c.display_name)
	_gem_opt = _opt(gnames, 0, 260)
	_gem_opt.item_selected.connect(func(_i: int) -> void: _reroll(false))
	_count = _spin(1, 9999, 1, 1, 100)
	box.add_child(_row_of([_cap("Sockets", 100), _sockets, _gem_opt, _cap("Count", 70), _count]))
	_affix_opts.clear()
	_power_opts.clear()
	var arow := hbox(6)
	arow.add_child(_cap("Enchant", 100))
	for i in 3:
		var o := _opt(["(random)"], 0, 200)
		o.item_selected.connect(func(_i: int) -> void: _reroll(false))
		_affix_opts.append(o)
		arow.add_child(o)
	box.add_child(arow)
	var prow := hbox(6)
	prow.add_child(_cap("Powers", 100))
	for i in 3:
		var o := _opt(["(none)"], 0, 200)
		o.item_selected.connect(func(_i: int) -> void: _reroll(false))
		_power_opts.append(o)
		prow.add_child(o)
	box.add_child(prow)
	_perfect = _check("Perfect rolls", false, func(_on: bool) -> void: _reroll(false))
	_unbound = _check("Unbound (no level or attribute needs; Class E)", false, func(_on: bool) -> void: _reroll(false))
	_equip_now = _check("Equip at once", false, func(_on: bool) -> void: pass)
	_lock = _check("Lock", false, func(_on: bool) -> void: _reroll(false))
	box.add_child(_row_of([_perfect, _unbound]))
	box.add_child(_row_of([_equip_now, _lock]))
	box.add_child(_row_of([_b("Summon", _summon_item, 170.0, &"PrimaryButton"), _b("Reroll", func() -> void: _reroll(), 110.0),
		_b("Strike Test", _strike_test, 140.0)]))
	box.add_child(_row_of([_b("Full Gear for My Class", _summon_full_set, 250.0), _b("Every Weapon Type", _summon_every_type, 220.0)]))
	box.add_child(_row_of([_b("Random Fabled Arm", func() -> void: _summon_fabled(false), 220.0), _b("All Fabled of This Rarity", func() -> void: _summon_fabled(true), 250.0)]))
	box.add_child(_row_of([_b("5 Random (this rarity)", func() -> void: _summon_random(5), 230.0), _b("Random Set Piece", func() -> void: _summon_special(true), 200.0),
		_b("Random Unique", func() -> void: _summon_special(false), 180.0)]))
	box.add_child(_cap("Recent"))
	_recent_box = hbox(4)
	box.add_child(_recent_box)
	_fill_recent()
	box.add_child(_cap("Preview (what Summon gives)"))
	_preview_box = vbox(4)
	box.add_child(_preview_box)

func _row_of(ctrls: Array) -> HBoxContainer:
	var h := hbox(8)
	for c in ctrls:
		h.add_child(c)
	return h

func _set_rarity(r: int, reroll := true) -> void:
	_rarity_sel = clampi(r, 0, BH.RARITY_COUNT - 1)
	for i in _rar_btns.size():
		(_rar_btns[i] as Button).set_pressed_no_signal(i == _rarity_sel)
	if reroll:
		_reroll()

## The base passes every filter and the search (every word must appear).
func _matches(b: ItemBaseDef, q: String) -> bool:
	var cat: String = _f.get("category", "all")
	if cat != "all":
		if cat == "material":
			if BH.CATEGORY_SLOTS.has(b.category) or b.category in [&"consumable", &"crystal"]:
				return false
		elif String(b.category) != cat:
			return false
	var wt: String = _f.get("wtype", "any")
	if wt != "any" and (not b.is_weapon() or String(b.weapon_type) != wt):
		return false
	match String(_f.get("source", "any")):
		"plain":
			if b.unique_name != "" or b.set_id != &"" or b.story:
				return false
		"unique":
			if b.unique_name == "" or DataFabled.is_fabled(b):
				return false
		"set":
			if b.set_id == &"" or DataAscendant.is_ascendant(b):
				return false
		"ascendant":
			if not DataAscendant.is_ascendant(b):
				return false
		"fabled":
			if not DataFabled.is_fabled(b):
				return false
		"story":
			if not b.story:
				return false
	var ci := int(_f.get("class", 0))
	if ci > 0 and BH.CATEGORY_SLOTS.has(b.category):
		var cid: StringName = _hero().cls.id if ci == 1 else CLASS_IDS[ci - 2]
		if not (ItemGenerator.class_fit(b, cid) or ItemGenerator.accessory_fits(b, cid)):
			return false
	var ei := int(_f.get("element", 0))
	if ei > 0 and (not b.is_weapon() or b.element != ei - 1):
		return false
	var ni := int(_f.get("native", 0))
	if ni > 0 and b.fixed_rarity != ni - 1:
		return false
	if b.level_req < int(_f.get("lo", 0)) or b.level_req > int(_f.get("hi", BH.LEVEL_CAP + 5)):
		return false
	if q != "":
		var hay := ("%s %s %s %s %s %s" % [b.display_name, b.unique_name, b.id, b.weapon_type, b.lore,
			BH.rarity_name(b.fixed_rarity) if b.fixed_rarity >= 0 else ""]).to_lower()
		for pid in b.fixed_powers:
			var p := DB.power(StringName(pid))
			if p:
				hay += " " + p.display_name.to_lower()
		for word in q.split(" ", false):
			if not hay.contains(word):
				return false
	return true

func _fill_bases() -> void:
	if _list == null:
		return
	var keep := _picked
	_list.clear()
	_base_ids.clear()
	var q := _search.text.strip_edges().to_lower() if _search else ""
	var bases := DB.item_bases.values().filter(func(b): return _matches(b, q))
	bases.sort_custom(func(a, b): return [String(a.category), a.level_req, String(a.unique_name if a.unique_name != "" else a.display_name)] \
		< [String(b.category), b.level_req, String(b.unique_name if b.unique_name != "" else b.display_name)])
	for b: ItemBaseDef in bases:
		_base_ids.append(b.id)
		var nm := b.unique_name if b.unique_name != "" else b.display_name
		var kind: String = String(b.weapon_type).capitalize() if b.is_weapon() else String(CAT_NAMES.get(String(b.category), String(b.category).capitalize()))
		var i := _list.add_item("%s   ·  %s · L%d%s" % [nm, kind, b.level_req, ("  · " + BH.rarity_name(b.fixed_rarity)) if b.fixed_rarity >= 0 else ""])
		var ip := b.icon_path()
		if ip != "" and ResourceLoader.exists(ip):
			_list.set_item_icon(i, load(ip))
		if b.fixed_rarity >= 0:
			_list.set_item_custom_fg_color(i, BH.rarity_color(b.fixed_rarity))
	if _count_lbl:
		_count_lbl.text = "%d items match. Click to preview; double-click to summon at once." % _base_ids.size()
	var idx := _base_ids.find(keep)
	var fresh := idx < 0
	if idx < 0 and not _base_ids.is_empty():
		idx = 0
	if idx >= 0:
		_list.select(idx)
		_list.ensure_current_is_visible()
		_pick_base(idx, fresh)
	else:
		_picked = &""
		_preview = null
		_show_preview()

## Select a base: the rarity jumps to the base's own when it has one (pick any other afterwards to force it); the
## enchantment and power pickers list what fits it.
func _pick_base(i: int, new_pick := true) -> void:
	if i < 0 or i >= _base_ids.size():
		return
	var b := DB.item_base(_base_ids[i])
	if b == null:
		return
	var changed := _picked != b.id
	_picked = b.id
	if changed and new_pick and b.fixed_rarity >= 0 and BH.CATEGORY_SLOTS.has(b.category):
		_set_rarity(b.fixed_rarity, false)
	if changed:
		_fill_pickers(b)
	_reroll()

func _select_base(id: StringName) -> bool:
	var idx := _base_ids.find(id)
	if idx < 0:
		_search.text = String(id)
		_fill_bases()
		idx = _base_ids.find(id)
	if idx < 0:
		return false
	_list.select(idx)
	_pick_base(idx)
	return true

func _fill_pickers(b: ItemBaseDef) -> void:
	_affix_ids = [&""]
	var an := ["(random)"]
	if BH.CATEGORY_SLOTS.has(b.category):
		for a: AffixDef in DB.affixes_for(b.category):
			if ItemGenerator.affix_fits(b, a) and not a.tiers.is_empty():
				_affix_ids.append(a.id)
				an.append(StatDefs.format_modifier(a.stat, a.op, float(a.tiers[-1][2])))
	for o: OptionButton in _affix_opts:
		o.clear()
		for n in an:
			o.add_item(String(n))
		o.selected = 0
	_power_ids2 = [&""]
	var pn := ["(none)"]
	if BH.CATEGORY_SLOTS.has(b.category):
		var plist: Array = DB.powers_for(b.category).filter(func(p): return p.tier != &"fabled" or p.id == DataFabled.sig_power_id(b.id))
		plist.sort_custom(func(x, y): return [String(x.tier), x.display_name] < [String(y.tier), y.display_name])
		for p in plist:
			_power_ids2.append(p.id)
			pn.append("%s (%s)" % [p.display_name, String(p.tier).capitalize()])
	for o: OptionButton in _power_opts:
		o.clear()
		for n in pn:
			o.add_item(String(n))
		o.selected = 0

## A new roll of the picked base with everything chosen (fresh=false keeps the seed: only the settings change).
func _reroll(fresh := true) -> void:
	if _picked == &"" or _ilvl == null:
		return
	if fresh or _seed == 0:
		_seed = randi()
	_preview = _make(DB.item_base(_picked), _seed)
	_show_preview()

func _make(base: ItemBaseDef, seed_value: int) -> ItemInstance:
	if base == null:
		return null
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	return _finish_item(ItemGenerator.generate(base, int(_ilvl.value), _rarity_sel, rng, true))

func _finish_item(it: ItemInstance) -> ItemInstance:
	if it == null:
		return null
	if it.is_equipment():
		it.quality = _quality.value / 100.0
		_force_affixes(it)
		if _perfect.button_pressed:
			for a in it.affixes:
				var def := DB.affix(StringName(a.id))
				if def:
					var tiers := def.allowed_tiers(it.ilvl)
					var top: int = tiers[-1] if not tiers.is_empty() else def.tiers.size() - 1
					a["tier"] = top
					a["value"] = roundf(float(def.tiers[top][2])) if def.integer else float(def.tiers[top][2])
		for o: OptionButton in _power_opts:
			var pid: StringName = _power_ids2[o.selected] if o.selected >= 0 and o.selected < _power_ids2.size() else &""
			if pid != &"" and not it.powers.has(String(pid)):
				it.powers.append(String(pid))
		var want := int(_sockets.value)
		if want > 0:
			it.sockets = want
			it.gems.clear()
			var gid: String = _gem_ids[_gem_opt.selected] if _gem_opt and _gem_opt.selected >= 0 and _gem_opt.selected < _gem_ids.size() else ""
			for i in it.sockets:
				it.gems.append(gid)
		it.unbound = _unbound != null and _unbound.button_pressed
		it.locked = _lock != null and _lock.button_pressed
	elif it.base.is_stackable():
		it.count = clampi(int(_count.value), 1, maxi(1, it.base.stack_max) * 20)
	return it

## The chosen enchantments replace random ones (from the last); a chosen one that already rolled stays.
func _force_affixes(it: ItemInstance) -> void:
	var chosen := []
	for o: OptionButton in _affix_opts:
		var aid: StringName = _affix_ids[o.selected] if o.selected >= 0 and o.selected < _affix_ids.size() else &""
		if aid != &"" and not chosen.has(aid):
			chosen.append(aid)
	if chosen.is_empty():
		return
	var groups := {}
	for aid in chosen:
		groups[DB.affix(aid).group] = true
	var keep := it.affixes.filter(func(a): return chosen.has(StringName(a.id)))
	var others := it.affixes.filter(func(a): return not chosen.has(StringName(a.id)) and DB.affix(StringName(a.id)) != null \
		and not groups.has(DB.affix(StringName(a.id)).group))
	for aid in chosen:
		if keep.any(func(a): return StringName(a.id) == aid):
			continue
		var def := DB.affix(aid)
		var tiers := def.allowed_tiers(it.ilvl)
		var top: int = tiers[-1] if not tiers.is_empty() else def.tiers.size() - 1
		var v := lerpf(float(def.tiers[top][1]), float(def.tiers[top][2]), randf_range(0.6, 1.0))
		keep.append({"id": String(aid), "tier": top, "value": roundf(v) if def.integer else snappedf(v, 0.001)})
	var room := maxi(0, it.affixes.size() - keep.size())
	it.affixes = keep + others.slice(0, room)

func _show_preview() -> void:
	if _preview_box == null:
		return
	for c in _preview_box.get_children():
		_preview_box.remove_child(c)
		c.queue_free()
	if _preview == null:
		_preview_box.add_child(_text("Pick an item from the list.", 15, UITheme.TEXT_DIM))
		return
	_preview_box.add_child(Tips.item(_preview, {"compare": false}))

func _give(it: ItemInstance) -> void:
	if it == null:
		say("That item could not be made.", true)
		return
	var name := it.display_name()
	var n := it.count
	var left := _hero().inventory.add(it)
	if left > 0:
		say("No room for %s (%d did not fit)." % [name, left], true)
		return
	Events.loot_picked.emit(it)
	var msg := "Summoned: %s%s (%s, item level %d)." % ["%d x " % n if n > 1 else "", name, BH.rarity_name(it.rarity), it.ilvl]
	if _equip_now != null and _equip_now.button_pressed and it.is_equipment():
		var err := _hero().equip_from_inventory(it)
		msg += " Equipped." if err == "" else " Not equipped: %s." % err
	say(msg)
	_remember(it.base.id)

func _remember(id: StringName) -> void:
	_recent.erase(id)
	_recent.push_front(id)
	_recent = _recent.slice(0, 8)
	_fill_recent()

func _fill_recent() -> void:
	if _recent_box == null:
		return
	for c in _recent_box.get_children():
		_recent_box.remove_child(c)
		c.queue_free()
	if _recent.is_empty():
		_recent_box.add_child(_text("Nothing summoned yet.", 14, UITheme.TEXT_DIM))
	for id in _recent:
		var b := DB.item_base(id)
		if b == null:
			continue
		var rid: StringName = id
		var btn := _b("", func() -> void: _select_base(rid), 52.0)
		var ip := b.icon_path()
		if ip != "" and ResourceLoader.exists(ip):
			btn.icon = load(ip)
			btn.expand_icon = true
		btn.tooltip_text = b.unique_name if b.unique_name != "" else b.display_name
		btn.custom_minimum_size = Vector2(52, 52)
		_recent_box.add_child(btn)

func _summon_item() -> void:
	if _picked == &"":
		return
	if _preview == null:
		_reroll()
	var it := _preview.clone()
	it.unbound = _preview.unbound
	it.locked = _preview.locked
	_give(it)
	var base := DB.item_base(_picked)
	if base and BH.CATEGORY_SLOTS.has(base.category):
		for i in range(1, int(_count.value)):
			_give(_make(base, randi()))
	_reroll()

func _summon_random(n: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	for i in n:
		var b := ItemGenerator.random_base(rng, int(_ilvl.value), [], _hero().cls.id)
		if b:
			_give(_make(b, rng.randi()))

func _summon_special(want_set: bool) -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var b := ItemGenerator.random_special(rng, BH.LEVEL_CAP, want_set, _hero().cls.id)
	if b == null:
		say("No such item in this build.", true)
		return
	_give(_make(b, rng.randi()))

## One piece for every slot the hero's class wears (and a weapon it masters), at the chosen rarity and level.
func _summon_full_set() -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var cid := _hero().cls.id
	for cat in [&"weapon", &"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots", &"accessory"]:
		var b := ItemGenerator.random_base(rng, int(_ilvl.value), [cat], cid, 1.0)
		if b:
			_give(_make(b, rng.randi()))
	if cid == &"knight" or DataTranscendence.family_of(cid) == &"knight":
		var s := ItemGenerator.random_base(rng, int(_ilvl.value), [&"shield"], cid, 1.0)
		if s:
			_give(_make(s, rng.randi()))

## The newest ordinary weapon of every type the item level allows.
func _summon_every_type() -> void:
	for wt in WEAPON_TYPES:
		var pool := DB.item_bases.values().filter(func(b): return b.is_weapon() and b.weapon_type == wt and b.unique_name == "" and b.set_id == &"" \
			and b.drop_weight > 0 and b.level_req <= int(_ilvl.value))
		if pool.is_empty():
			continue
		pool.sort_custom(func(a, b): return a.level_req > b.level_req)
		_give(_make(pool[0], randi()))

## A random Fabled arm, or every Fabled arm whose own rarity is the chosen one.
func _summon_fabled(all_of_rarity: bool) -> void:
	var ids := DataFabled.ids_of(_rarity_sel) if all_of_rarity else DataFabled.ids()
	if ids.is_empty():
		say("No Fabled arm is %s; pick Legendary to Primordial." % BH.rarity_name(_rarity_sel), true)
		return
	if not all_of_rarity:
		ids = [ids[randi() % ids.size()]]
	for id in ids:
		_give(_make(DB.item_base(id), randi()))

## Fire the picked Fabled arm's signature strike at the nearest monster without equipping it.
func _strike_test() -> void:
	var p := _player()
	if p == null or _picked == &"" or not DataFabled.is_fabled(DB.item_base(_picked)):
		say("Pick a Fabled arm first (Source: Fabled Arms).", true)
		return
	var near := CombatQuery.nearest(CombatQuery.actors_in_radius(p.get_world_3d(), p.global_position, 20.0, BH.LAYER_ENEMY), p.global_position)
	if near == null:
		say("No monster within 20 m. Spawn one on the World page.", true)
		return
	FabledProcs.strike(p, _picked, near, 50.0 + 10.0 * p.hero.progress.level)
	say("%s: %s." % [DB.item_base(_picked).unique_name, String(DataFabled.row(_picked)[8])])

# ---- Tempos: summoner and unsummoner ----------------------------------------------------------------------------------

func _page_tempos() -> void:
	_head("Tempo Summoner")
	_t_kind = _opt(["Nameless spirit (choose class and grade)", "Renowned spirit (choose by name)"], 0, 420)
	_row([_cap("Kind", 130), _t_kind])
	var classes := DataTempos.class_ids()
	_t_class = _opt(classes.map(func(c): return String(DataTempos.tempo_class(c).get("name", c))), 0, 260)
	_t_class.set_meta(&"ids", classes)
	var grades := []
	for g in DataTempos.GRADES.size():
		grades.append("%d · %s" % [g + 1, DataTempos.GRADES[g].name])
	_t_grade = _opt(grades, DataTempos.max_grade() - 1, 260)
	_row([_cap("Class", 130), _t_class, _cap("Grade", 90), _t_grade])
	_legend_ids = DataTempos.all_legend_ids()
	_legend_ids.sort_custom(func(a, b): return [DataTempos.legend_tier(a), String(a)] < [DataTempos.legend_tier(b), String(b)])
	_t_legend = _opt(_legend_ids.map(func(l): return "%s · %s" % [String(DataTempos.legend(l).get("name", l)), DataTempos.renowned_tier(DataTempos.legend_tier(l)).name]), 0, 520)
	_row([_cap("Renowned", 130), _t_legend])
	_t_stars = _opt(["3 stars", "4 stars", "5 stars"], 2, 160)
	_t_res = _spin(0, TempoGacha.MAX_RESONANCE, 0)
	_t_name = LineEdit.new()
	_t_name.placeholder_text = "Name (optional)"
	_t_name.custom_minimum_size = Vector2(260, 52 if Settings.touch_mode else 40)
	_row([_cap("Stars", 130), _t_stars, _cap("Resonance", 110), _t_res, _t_name])
	_row([_b("Summon to Spirit Hall", func() -> void: _summon_tempo(false), 280.0, &"PrimaryButton"), _b("Summon and Bind", func() -> void: _summon_tempo(true), 240.0)])
	_head("Tempo Unsummoner")
	_t_list = vbox(6)
	_page_box.add_child(_t_list)
	_fill_tempos()

func _summon_tempo(bind_now: bool) -> void:
	var h := _hero()
	var t: TempoData
	if _t_kind.selected == 1:
		var id: StringName = _legend_ids[_t_legend.selected]
		var have := TempoGacha.owned_legend(h, id)
		if have:
			have.resonance = int(_t_res.value)
			say("%s already answers you; resonance set to %d." % [have.full_name(), have.resonance])
			_fill_tempos()
			return
		t = TempoRules.legend_data(id)
		t.stars = 5
		t.resonance = int(_t_res.value)
	else:
		var ids: Array = _t_class.get_meta(&"ids")
		var taken := (h.tempos + h.spirit_hall).map(func(x): return x.tempo_name)
		t = TempoRules.generate(randi(), h.progress.level, ids[_t_class.selected], taken, _t_grade.selected + 1)
		t.stars = 3 + _t_stars.selected
	if _t_name.text.strip_edges() != "":
		t.tempo_name = _t_name.text.strip_edges().left(32)
	t.price = 0
	if h.spirit_hall.size() >= TempoGacha.HALL_CAP:
		say("The Spirit Hall is full (%d). Unsummon one first." % TempoGacha.HALL_CAP, true)
		return
	TempoGacha._to_hall(h, t)
	var msg := "Summoned %s to the Spirit Hall." % t.full_name()
	if bind_now:
		var err := TempoGacha.bind(h, t.uid)
		msg = "Summoned and bound %s." % t.full_name() if err == "" else msg + " (" + err + ")"
		if err == "" and h == Game.hero:
			TempoParty.refresh(h)
	Events.tempo_changed.emit(0)
	say(msg)
	_fill_tempos()

func _fill_tempos() -> void:
	if _t_list == null:
		return
	for c in _t_list.get_children():
		_t_list.remove_child(c)
		c.queue_free()
	var h := _hero()
	if h.tempos.is_empty() and h.spirit_hall.is_empty():
		_t_list.add_child(_text("No Tempos are bound or waiting in the hall.", 16, UITheme.TEXT_DIM))
	for t: TempoData in h.tempos + h.spirit_hall:
		var bound := h.tempos.has(t)
		var uid := t.uid
		var cls := String(DataTempos.tempo_class(t.class_id).get("name", t.class_id))
		var row := hbox(8)
		_t_list.add_child(row)
		var l := _cap("%s  ·  %s%s  ·  %s%s" % [t.full_name(), cls, "  ·  %d★" % t.stars if t.stars > 0 else "",
			"Bound" if bound else "In the hall", "  ·  fallen" if t.fallen else ""], 0.0)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(l)
		if bound:
			row.add_child(_b("Rest", func() -> void:
				say(TempoGacha.rest(h, uid) if TempoGacha.rest(h, uid) != "" else "Sent to the Spirit Hall.")
				TempoParty.refresh(h)
				_fill_tempos(), 110.0))
		else:
			row.add_child(_b("Bind", func() -> void:
				var e := TempoGacha.bind(h, uid)
				say(e if e != "" else "Bound.", e != "")
				TempoParty.refresh(h)
				_fill_tempos(), 110.0))
		row.add_child(_b("Revive", func() -> void:
			t.fallen = false
			t.hp_frac = 1.0
			t.mana_frac = 1.0
			TempoParty.refresh(h)
			Events.tempo_changed.emit(uid)
			say("%s stands again." % t.full_name()), 110.0))
		row.add_child(_b("Unsummon", func() -> void: _unsummon(t), 140.0))

## Remove a spirit entirely (no embers). Its gear goes to the bag; what does not fit is dropped at the hero's feet.
func _unsummon(t: TempoData) -> void:
	var h := _hero()
	for a in TempoParty.actors():
		if a is Tempo and (a as Tempo).data == t:
			a.queue_free()
	h._loading_equipment = true
	for s in BH.SLOTS:
		var it := t.equipment.get_item(s)
		if it != null:
			t.equipment.slots[s] = null
			if it.rarity > BH.Rarity.BEGINNER and h.inventory.add(it) > 0 and _player():
				Loot.spawn_item(it, _player().global_position)      # the bag is full: it lands at the hero's feet
	h._loading_equipment = false
	h.tempos.erase(t)
	h.spirit_hall.erase(t)
	Events.tempo_changed.emit(0)
	if h == Game.hero:
		TempoParty.refresh(h)
	say("%s is unsummoned." % t.full_name())
	_fill_tempos()

# ---- Combat -------------------------------------------------------------------------------------------------------

func _page_combat() -> void:
	_head("Switches")
	_row([_check("God Mode", Game.god_mode, func(on: bool) -> void: Game.god_mode = on),
		_check("Infinite Mana", Game.infinite_mana, func(on: bool) -> void: Game.infinite_mana = on),
		_check("No Cooldowns", Game.debug_no_cooldowns, func(on: bool) -> void: Game.debug_no_cooldowns = on),
		_check("One-Hit Kills", Game.debug_one_hit, func(on: bool) -> void: Game.debug_one_hit = on)])
	_head("Multipliers")
	for spec in [["Damage dealt", "debug_damage_mult", 0.0, 1000.0], ["Movement speed", "debug_speed_mult", 0.1, 10.0],
			["Experience", "debug_xp_mult", 0.0, 1000.0], ["Gold", "debug_gold_mult", 0.0, 1000.0]]:
		var key: String = spec[1]
		var s := _spin(float(spec[2]), float(spec[3]), float(Game.get(key)), 0.1)
		s.value_changed.connect(func(v: float) -> void: Game.set(key, v))
		_row([_cap(String(spec[0]) + " ×", 220), s, _b("Reset", func() -> void: s.value = 1.0, 100.0)])
	_head("Drops")
	var names := ["Normal drops"]
	for i in range(1, BH.RARITY_COUNT):
		names.append("At least %s" % BH.RARITY_NAMES[i])
	var floor_opt := _opt(names, maxi(0, Game.debug_min_drop), 300)
	floor_opt.item_selected.connect(func(i: int) -> void: Game.debug_min_drop = i if i > 0 else -1)
	_row([_cap("Equipment drops", 220), floor_opt])

# ---- World --------------------------------------------------------------------------------------------------------

func _page_world() -> void:
	_head("Monsters")
	var defs := DB.enemies.values()
	defs.sort_custom(func(a, b): return String(a.display_name) < String(b.display_name))
	var en := _opt(defs.map(func(d): return "%s (%s)" % [d.display_name, d.id]), 0, 420)
	var lvl := _spin(1, BH.LEVEL_CAP, _hero().progress.level)
	var cnt := _spin(1, 60, 1)
	_row([_cap("Monster", 110), en, _cap("Level", 70), lvl, _cap("Count", 70), cnt])
	var elite := _check("Elite", false, func(_on: bool) -> void: pass)
	_row([elite, _b("Spawn", func() -> void: _spawn(defs[en.selected], int(lvl.value), int(cnt.value), elite.button_pressed), 160.0, &"PrimaryButton"),
		_b("Kill All Monsters", _kill_all, 220.0),
		_check("Freeze Monsters", Game.debug_freeze_ai, func(on: bool) -> void: Game.debug_freeze_ai = on)])
	_head("Travel")
	var ids := DB.maps.keys()
	ids.sort_custom(func(a, b): return String(DB.maps[a].display_name) < String(DB.maps[b].display_name))
	var mp := _opt(ids.map(func(i): return DB.maps[i].display_name), maxi(0, ids.find(Game.current_map_id)), 360)
	_row([mp, _b("Travel", func() -> void: Game.travel(ids[mp.selected], &"start"), 140.0),
		_b("Discover Every Region", func() -> void:
			for id in DB.maps:
				_hero().discovered_maps[id] = true
			for t in get_tree().get_nodes_in_group(&"teleporter"):
				t.discover()
			say("Every region is discovered."), 280.0)])
	_head("Story and Dungeons")
	_row([_b("Set Ritual Seen", func() -> void: Game.set_world_flag(&"catacombs_ritual_seen"), 220.0),
		_b("Break the Temple Seal", func() -> void: Game.set_world_flag(&"temple_seal_broken"), 240.0),
		_b("Warden Defeated", func() -> void: Game.set_world_flag(&"boss_warden_defeated"), 220.0)])
	_row([_b("End Dungeon Recoveries", func() -> void:
			_hero().dungeon_raids.clear()
			say("Every raided dungeon is restocked."), 280.0),
		_b("Champions Return Now", func() -> void:
			_hero().miniboss_log.clear()
			say("Every champion can be fought again."), 260.0)])
	_head("Quake Team")
	_row([_b("Call an Ally", func() -> void: say(Cheats.apply("quake team", _hero(), _player())), 200.0),
		_b("Dismiss Last Ally", func() -> void: say(Cheats.apply("quake quake", _hero(), _player())), 220.0),
		_b("Dismiss All", func() -> void:
			while not _hero().quake_team.is_empty():
				QuakeTeam.dismiss(_hero())
			say("The Quake Team went home."), 180.0)])

func _spawn(def: EnemyDef, lvl: int, n: int, elite: bool) -> void:
	var p := _player()
	if Game.current_map == null or p == null:
		return
	var diff: Dictionary = DataEnemies.DIFFICULTY[clampi(Game.difficulty, 0, DataEnemies.DIFFICULTY.size() - 1)]
	for i in n:
		var mods := []
		if elite:
			var keys := DB.elite_mods.keys()
			keys.shuffle()
			mods = keys.slice(0, 2)
		var ang := TAU * float(i) / float(maxi(1, n))
		var at := p.global_position + p.forward() * 6.0 + Vector3(cos(ang), 0, sin(ang)) * (0.0 if n == 1 else 2.5)
		Spawner.spawn_enemy(Game.current_map, def, lvl, mods, at, diff)
	say("Spawned %d x %s (level %d%s)." % [n, def.display_name, lvl, ", elite" if elite else ""])

func _kill_all() -> void:
	var n := 0
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e.alive:
			e.die(Game.player)
			n += 1
	say("%d monsters slain." % n)

# ---- Technical ----------------------------------------------------------------------------------------------------

func _page_tech() -> void:
	_head("Live")
	_live = _text("", 16, UITheme.GOOD)
	_page_box.add_child(_live)
	_head("Overlays")
	_row([_check("FPS & profiling", Dev.show_fps, func(on: bool) -> void: Dev.show_fps = on),
		_check("Damage formula", Dev.show_formula, func(on: bool) -> void: Dev.show_formula = on),
		_check("Monster AI states", Dev.show_ai, func(on: bool) -> void: Dev.show_ai = on),
		_check("Hitboxes", Dev.show_hitboxes, func(on: bool) -> void: Dev.show_hitboxes = on),
		_check("Navigation mesh", Dev.show_navmesh, func(on: bool) -> void: Dev.set_navmesh(on))])
	_head("Engine")
	var ts := _spin(0.05, 5.0, Engine.time_scale, 0.05)
	ts.value_changed.connect(func(v: float) -> void: Engine.time_scale = v)
	var cap := _spin(0, 500, Engine.max_fps)
	cap.value_changed.connect(func(v: float) -> void: Engine.max_fps = int(v))
	var tps := _spin(30, 240, Engine.physics_ticks_per_second)
	tps.value_changed.connect(func(v: float) -> void: Engine.physics_ticks_per_second = int(v))
	_row([_cap("Time scale", 150), ts, _cap("Frame cap (0 = none)", 220), cap, _cap("Physics Hz", 130), tps])
	var vs := _check("VSync", DisplayServer.window_get_vsync_mode() != DisplayServer.VSYNC_DISABLED, func(on: bool) -> void:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if on else DisplayServer.VSYNC_DISABLED))
	var draw := _opt(["Normal", "Unshaded", "Lighting only", "Overdraw", "Wireframe"], 0, 220)
	draw.item_selected.connect(func(i: int) -> void:
		get_viewport().debug_draw = [Viewport.DEBUG_DRAW_DISABLED, Viewport.DEBUG_DRAW_UNSHADED, Viewport.DEBUG_DRAW_LIGHTING,
			Viewport.DEBUG_DRAW_OVERDRAW, Viewport.DEBUG_DRAW_WIREFRAME][i]
		if i == 4:
			RenderingServer.set_debug_generate_wireframes(true))
	_row([vs, _cap("Render view", 150), draw])
	_head("View")
	var p := _player()
	var fps := _check("First-person view (also %s)" % Settings.binding_text(&"view_toggle"), p != null and p.first_person, func(on: bool) -> void:
		if _player():
			_player().set_first_person(on))
	var fov := _spin(50, 120, Settings.fp_fov if Settings.get("fp_fov") != null else 80)
	fov.value_changed.connect(func(v: float) -> void:
		Settings.fp_fov = v
		if _player() and _player().camera:
			_player().camera.apply_fov())
	_row([fps, _cap("First-person FOV", 200), fov])
	_head("Data")
	_row([_b("Save Now", func() -> void:
			Game.save_now()
			say("Saved."), 160.0),
		_b("Reload Map", func() -> void: Game.travel(Game.current_map_id, &"start"), 180.0),
		_b("Dump Hero Stats", _dump_stats, 200.0),
		_b("Copy Save to Clipboard", func() -> void:
			DisplayServer.clipboard_set(JSON.stringify(_hero().to_dict()))
			say("The hero's save data is on the clipboard."), 280.0)])

func _dump_stats() -> void:
	var p := _player()
	var d: DerivedStats = p.stats if p and p.stats else _hero().compute_stats()
	var keys := d.values.keys()
	keys.sort()
	var parts := PackedStringArray()
	for k in keys:
		var v := float(d.values[k])
		if v != 0.0:
			parts.append("%s %s" % [k, str(snappedf(v, 0.001))])
	say("Stats: " + ", ".join(parts))

func _process(delta: float) -> void:
	if not visible or _live == null:
		return
	_live_t -= delta
	if _live_t > 0.0:
		return
	_live_t = 0.5
	var enemies := get_tree().get_nodes_in_group(&"enemy").filter(func(e): return e.alive).size()
	_live.text = "FPS %d · Process %.2f ms · Physics %.2f ms · Draw calls %d · Nodes %d · Orphans %d · Monsters %d · Static memory %.0f MB · Video memory %.0f MB · Map %s" % [
		Engine.get_frames_per_second(), Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT), enemies, Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0,
		Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, Game.current_map_id]
