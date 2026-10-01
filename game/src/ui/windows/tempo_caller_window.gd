class_name TempoCallerWindow
extends UIWindow
## Veyra Ashgrave's shrine (opened from her dialogue). "Spirits answering" lists the nameless warriors answering her
## call right now — grade, class, personality, skills, how they died, the strength they would have bound to you, and
## the price of binding. "Renowned" lists the five named spirits (level requirement, fixed high price, unique skills).
## "Your Tempos" lists the bound spirits; fallen ones can be called back for a fee, any can be released.

var hero: HeroData
var _tabs: TabBar
var _page := &"roster"
var _cards: HBoxContainer
var _mine: VBoxContainer
var _status: Label
var _gold: Label
var _clock_t := 0.0

const PAGES := [&"summon", &"roster", &"renowned", &"fallen", &"hall"]

func _init() -> void:
	super._init("The Shrine of the Fallen", Vector2(1600, 880))

func _build() -> void:
	var top := hbox(16)
	body.add_child(top)
	_tabs = TabBar.new()
	_tabs.add_tab("Summon")
	_tabs.add_tab("Spirits answering")
	_tabs.add_tab("Renowned")
	_tabs.add_tab("Your Tempos")
	_tabs.add_tab("Spirit Hall")
	_tabs.tab_changed.connect(func(i: int) -> void:
		_page = PAGES[clampi(i, 0, PAGES.size() - 1)]
		refresh())
	_tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_tabs)
	_gold = UITheme.label("", 18, UITheme.GOLD, UITheme.number_font())
	top.add_child(_gold)
	_status = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(_status)
	_cards = hbox(14)
	_cards.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_cards)
	_mine = vbox(10)
	_mine.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_mine)
	Events.tempo_changed.connect(func(_u): if visible: refresh())

## Open on a page: &"roster" (bind), &"renowned" or &"fallen" (your Tempos).
func open_on(page: StringName) -> void:
	_page = page if PAGES.has(page) else &"summon"
	Game.ui_root.open(&"tempo_caller")
	_tabs.current_tab = PAGES.find(_page)

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	if TempoGacha.ensure_welcome(hero):
		Events.notify.emit("Veyra Ashgrave presses %d Soul Embers into your hand: \"Your first call is on the shrine.\"" % TempoGacha.WELCOME_EMBERS, &"loot")
	_gold.text = "%d gold    ·    %d Soul Embers" % [hero.inventory.gold, TempoGacha.embers(hero)]
	var vertical := _page in [&"fallen", &"summon", &"hall"]
	_cards.visible = not vertical
	_mine.visible = vertical
	for c in _cards.get_children():
		c.queue_free()
	for c in _mine.get_children():
		c.queue_free()
	match _page:
		&"summon": _build_summon()
		&"roster": _build_roster()
		&"renowned": _build_renowned()
		&"hall": _build_hall()
		_: _build_mine()
	_update_status()

func _update_status() -> void:
	var bound := "Bound Tempos: %d / %d" % [TempoRules.bound_count(hero), DataTempos.MAX_ACTIVE]
	var gear := "Tempos wear gear up to %s rarity." % BH.rarity_name(TempoRules.best_wearable_rarity(hero))
	match _page:
		&"roster":
			var left := maxf(0.0, float(hero.tempo_roster.get("refresh_at", 0.0)) - hero.play_time)
			var gd := DataTempos.grade_def(TempoRules.current_grade(hero))
			var line := "%s    ·    %s spirits answer you (%d%% of your strength)" % [bound, gd.name, roundi(float(gd.mirror) * 100.0)]
			var nxt := TempoRules.next_grade(hero)
			if not nxt.is_empty():
				line += "; %s spirits answer when you %s" % [nxt.name, nxt.text]
			_status.text = "%s.    New spirits answer in %d:%02d.    %s" % [line, int(left) / 60, int(left) % 60, gear]
		&"summon":
			_status.text = "%s    ·    Summoned spirits wait in the Spirit Hall until you bind them (free). A renowned spirit called again grows stronger (Resonance, up to V)." % bound
		&"hall":
			_status.text = "%s    ·    Spirits in the hall: %d / %d. Bind one into an open place, swap it with a bound Tempo, or release it for Soul Embers." % [
				bound, hero.spirit_hall.size(), TempoGacha.HALL_CAP]
		&"renowned":
			var tier := DataTempos.renowned_tier(DataTempos.renowned_tier_for(hero.progress.level))
			var nxt_tier := DataTempos.renowned_tier_for(hero.progress.level) + 1
			var later := ("    %s spirits answer at level %d." % [DataTempos.renowned_tier(nxt_tier).name, int(DataTempos.renowned_tier(nxt_tier).level)]) 				if nxt_tier < DataTempos.RENOWNED_TIERS.size() else ""
			_status.text = "%s    ·    %s spirits carry %d%% of your strength and skills no other spirit knows. Each answers only a hero of its level.%s    %s" % [
				bound, tier.name, roundi(float(tier.mirror) * 100.0), later, gear]
		_:
			_status.text = "%s    ·    %s" % [bound, gear]

func _process(delta: float) -> void:
	if not visible or hero == null:
		return
	_clock_t -= delta
	if _clock_t <= 0.0:
		_clock_t = 1.0
		if _page == &"roster" and (hero.play_time >= float(hero.tempo_roster.get("refresh_at", 0.0)) \
				or int(hero.tempo_roster.get("grade", 1)) < TempoRules.current_grade(hero)):
			refresh()
		else:
			_update_status()

func _build_roster() -> void:
	var offers := TempoRules.roster(hero)
	var mirror := TempoRules.hero_mirror(hero)
	for i in offers.size():
		var t: TempoData = offers[i]
		var err := TempoRules.hire_error(hero, i)
		_cards.add_child(_card(t, mirror, 366.0, err, "Bind — %d gold" % t.price, func() -> void: _bind(i, t)))

func _build_renowned() -> void:
	var mirror := TempoRules.hero_mirror(hero)
	for id in DataTempos.legend_ids(hero.progress.level):
		var t := TempoRules.legend_data(id)
		var err := TempoRules.legend_error(hero, id)
		var label := "Walks with you" if TempoRules.legend_bound(hero, id) else "Bind — %s gold" % GuideWindow._thousands(t.price)
		_cards.add_child(_card(t, mirror, 296.0, err, label, func() -> void: _bind_legend(id, t)))

## One spirit: who it is, what it can do, what it would be with this hero, and the button that binds it.
func _card(t: TempoData, mirror: DerivedStats, w: float, err: String, bind_text: String, on_bind: Callable) -> Control:
	var td := t.class_def()
	var p := inset(Vector2(w, 0))
	p.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var v := vbox(6)
	p.add_child(v)
	var inner := w - 28.0
	if t.is_legend():
		var lg := t.legend_def()
		var pic := TextureRect.new()
		var pp := DataTempos.portrait_path("tempo_%s" % t.legend_id)
		pic.texture = UIArt.tex(pp) if pp != "" else DataTempos.class_icon(t.class_id)
		pic.custom_minimum_size = Vector2(0, 150)
		pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		if pp == "":
			pic.modulate = td.get("color", Color.WHITE)
		v.add_child(pic)
		var nm := UITheme.title(t.tempo_name, 24, UITheme.PARCHMENT)
		nm.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(nm)
		var tt := UITheme.label("%s  ·  %s" % [String(lg.title), t.grade_name()], 16, t.grade_color(), UITheme.body_bold())
		tt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(tt)
		var cl := UITheme.label("%s — %s  ·  level %d" % [td.name, td.role, int(lg.level)], 15, td.get("color", UITheme.GOLD), UITheme.body_bold())
		cl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(cl)
		v.add_child(_wrapped("%s" % lg.pitch, 14, UITheme.TEXT, inner))
	else:
		var head := hbox(10)
		v.add_child(head)
		var ic := TextureRect.new()
		ic.texture = DataTempos.class_icon(t.class_id)
		ic.custom_minimum_size = Vector2(52, 52)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ic.modulate = td.get("color", Color.WHITE)
		head.add_child(ic)
		var hv := vbox(0)
		head.add_child(hv)
		hv.add_child(UITheme.title(t.tempo_name, 26, UITheme.PARCHMENT))
		hv.add_child(UITheme.label("%s — %s" % [td.name, td.role], 16, td.get("color", UITheme.GOLD), UITheme.body_bold()))
		hv.add_child(UITheme.label("%s spirit" % t.grade_name(), 14, t.grade_color(), UITheme.body_bold()))
	var tr := t.trait_def()
	v.add_child(_wrapped("%s: %s" % [tr.get("name", ""), tr.get("desc", "")], 14, UITheme.TEXT, inner))
	v.add_child(_wrapped("\"%s\"" % t.origin, 14, UITheme.TEXT_DIM, inner))
	v.add_child(Tips.rule())
	for sid in t.skills:
		var sk := DataTempos.skill(sid)
		var row := hbox(8)
		var si := TextureRect.new()
		si.texture = DataTempos.skill_icon(sid)
		si.custom_minimum_size = Vector2(32, 32)
		si.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		si.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(si)
		var heal := DataTempos.is_heal(sid)
		var uniq := DataTempos.is_unique(sid)
		var col := t.grade_color() if uniq else (UITheme.GOOD if heal else UITheme.PARCHMENT)
		var nl := UITheme.label(String(sk.name) + ("  (heals)" if heal else "") + ("  ★" if uniq else ""), 15, col, UITheme.body_bold())
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(nl)
		var desc := String(sk.desc)
		var title := String(sk.name)
		TooltipLayer.attach(row, func() -> Control: return Tips.text("%s\n%d mana · %d s cooldown%s" % [desc, roundi(float(sk.mana)), roundi(maxf(SkillDef.MIN_COOLDOWN, float(sk.cooldown))),
			"\nOnly this spirit knows it." if uniq else ""], title))
		v.add_child(row)
	v.add_child(Tips.rule())
	var d := TempoRules.compute(t, mirror, hero.progress.level, hero.cls)
	var g := GridContainer.new()
	g.columns = 4
	g.add_theme_constant_override("h_separation", 12)
	for r in [[&"max_hp", "Health"], [&"max_mana", "Mana"], [&"defense", "Defense"], [&"crit_chance", "Critical"]]:
		g.add_child(UITheme.label(r[1], 14, UITheme.TEXT_DIM, UITheme.body_font()))
		g.add_child(UITheme.label(StatDefs.format_value(r[0], d.get_stat(r[0])), 14, UITheme.PARCHMENT, UITheme.number_font()))
	v.add_child(g)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(spacer)
	var b := button(bind_text, on_bind, &"PrimaryButton", minf(300.0, inner))
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.disabled = err != ""
	if err != "":
		TooltipLayer.attach(b, func() -> Control: return Tips.text(err))
		if t.is_legend() and not TempoRules.legend_bound(hero, t.legend_id):
			var why := UITheme.label(err, 13, UITheme.TEXT_MUTED, UITheme.body_font())
			why.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			why.custom_minimum_size = Vector2(inner, 0)
			v.add_child(why)
	v.add_child(b)
	return p

func _wrapped(text: String, size: int, color: Color, width: float) -> Label:
	var l := UITheme.label(text, size, color, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(width, 0)
	return l

func _bind(index: int, t: TempoData) -> void:
	Game.ui_root.ask("Bind %s" % t.tempo_name, "Bind the spirit of %s the %s to you for %d gold?\nIt will follow you until it falls, and fight with %d%% of your strength." % [
			t.tempo_name, t.class_name_text(), t.price, roundi(t.mirror() * 100.0)],
		func() -> void:
			var bound := TempoRules.hire(hero, index)
			if bound == null:
				Events.notify.emit(TempoRules.hire_error(hero, index), &"error")
				return
			_bound(bound), "Bind (%d gold)" % t.price)

func _bind_legend(id: StringName, t: TempoData) -> void:
	Game.ui_root.ask("Bind %s" % t.tempo_name, "Bind %s to you for %s gold?\nA renowned spirit fights with %d%% of your strength and skills no other spirit knows." % [
			t.full_name(), GuideWindow._thousands(t.price), roundi(t.mirror() * 100.0)],
		func() -> void:
			var bound := TempoRules.hire_legend(hero, id)
			if bound == null:
				Events.notify.emit(TempoRules.legend_error(hero, id), &"error")
				return
			_bound(bound), "Bind (%s gold)" % GuideWindow._thousands(t.price))

func _bound(t: TempoData) -> void:
	TempoParty.refresh(hero)
	Audio.play_ui(&"skill_unlock")
	Events.notify.emit("%s answers your call." % t.full_name(), &"info")
	refresh()

func _build_mine() -> void:
	if hero.tempos.is_empty():
		var l := UITheme.label("No spirit walks with you yet. Choose one on the \"Spirits answering\" or \"Renowned\" page.", 18, UITheme.TEXT_DIM, UITheme.body_font())
		_mine.add_child(l)
		return
	for t in hero.tempos:
		var row := inset(Vector2(1500, 0))
		var h := hbox(16)
		row.add_child(h)
		var ic := TextureRect.new()
		ic.texture = DataTempos.class_icon(t.class_id)
		ic.custom_minimum_size = Vector2(56, 56)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ic.modulate = t.class_def().get("color", Color.WHITE)
		h.add_child(ic)
		var v := vbox(2)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(v)
		v.add_child(UITheme.title("%s  —  %s" % [t.full_name(), t.class_name_text()], 24, UITheme.PARCHMENT))
		v.add_child(UITheme.label("%s spirit  ·  %d%% of your strength" % [t.grade_name(), roundi(t.mirror() * 100.0)], 15, t.grade_color(), UITheme.body_bold()))
		var state := "Fallen. Its token is cold in your pack." if t.fallen else "Standing at your side (%d%% health)." % roundi(t.hp_frac * 100.0)
		v.add_child(UITheme.label(state, 16, UITheme.BAD if t.fallen else UITheme.GOOD, UITheme.body_font()))
		if t.fallen:
			var cost := TempoRules.revive_cost(t, hero)
			var err := TempoRules.revive_error(hero, t)
			var b := button("Call back — %d gold" % cost, func() -> void: _revive(t), &"PrimaryButton", 260.0)
			b.disabled = err != ""
			b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			if err != "":
				TooltipLayer.attach(b, func() -> Control: return Tips.text(err))
			h.add_child(b)
		var rest := button("Rest in the Hall", func() -> void: _rest(t), &"", 200.0)
		rest.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(rest)
		var r := button("Release", func() -> void: _release(t), &"", 160.0)
		r.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(r)
		_mine.add_child(row)

func _revive(t: TempoData) -> void:
	var cost := TempoRules.revive_cost(t, hero)
	Game.ui_root.ask("Call Back %s" % t.tempo_name, "Veyra Ashgrave will call %s's spirit back for %d gold." % [t.tempo_name, cost],
		func() -> void:
			var err := TempoRules.revive(hero, t)
			if err != "":
				Events.notify.emit(err, &"error")
				return
			TempoParty.refresh(hero)
			Audio.play_ui(&"level_up")
			Events.notify.emit("%s walks with you again." % t.tempo_name, &"info")
			refresh(), "Call back (%d gold)" % cost)

func _release(t: TempoData) -> void:
	var back := " A renowned spirit returns to the shrine and can be bound again." if t.is_legend() else " It will not return."
	Game.ui_root.ask("Release %s" % t.tempo_name, "Let %s's spirit go?%s Its gear comes back to your bag." % [t.tempo_name, back],
		func() -> void:
			var err := TempoRules.release(hero, t)
			if err != "":
				Events.notify.emit(err, &"error")
				return
			TempoParty.refresh(hero)
			refresh(), "Release", true)

# ---- Summoning (bh-012) ----------------------------------------------------------------------------------------------

func _build_summon() -> void:
	var st := TempoGacha.state(hero)
	var feat := TempoGacha.featured(-1, hero.progress.level)
	var lg := DataTempos.legend(feat)
	var top := hbox(24)
	_mine.add_child(top)
	# the featured spirit
	var banner := inset(Vector2(760, 330))
	top.add_child(banner)
	var bv := vbox(6)
	banner.add_child(bv)
	bv.add_child(UITheme.label("Featured today", 16, UITheme.TEXT_DIM, UITheme.body_bold()))
	var bh := hbox(16)
	bv.add_child(bh)
	var pic := TextureRect.new()
	var pp := DataTempos.portrait_path("tempo_%s" % feat)
	pic.texture = UIArt.tex(pp) if pp != "" else DataTempos.class_icon(lg.get("class", &"swordsman"))
	pic.custom_minimum_size = Vector2(170, 170)
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	if pp == "":
		pic.modulate = TempoGacha.STAR_COLORS[5]
	bh.add_child(pic)
	var fv := vbox(4)
	fv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bh.add_child(fv)
	fv.add_child(UITheme.title(String(lg.get("name", "")), 30, TempoGacha.STAR_COLORS[5]))
	fv.add_child(UITheme.label("%s  ·  %s" % [lg.get("title", ""), DataTempos.tempo_class(lg.get("class", &"swordsman")).get("name", "")], 17, UITheme.PARCHMENT, UITheme.body_bold()))
	fv.add_child(UITheme.label(ItemNames.star_text(5), 26, TempoGacha.STAR_COLORS[5], UITheme.body_font()))
	fv.add_child(_wrapped(String(lg.get("pitch", "")), 15, UITheme.TEXT, 520))
	fv.add_child(_wrapped("\"%s\"" % lg.get("origin", ""), 13, UITheme.TEXT_DIM, 520))
	var owned := TempoGacha.owned_legend(hero, feat)
	if owned:
		fv.add_child(UITheme.label("Yours — Resonance %s" % (TempoGacha.roman(owned.resonance) if owned.resonance > 0 else "none yet"), 15, UITheme.GOOD, UITheme.body_bold()))
	# the calls
	var calls := inset(Vector2(660, 330))
	top.add_child(calls)
	var cv := vbox(10)
	calls.add_child(cv)
	cv.add_child(UITheme.title("Call the Fallen", 28, UITheme.GOLD))
	cv.add_child(UITheme.label("Soul Embers: %d" % TempoGacha.embers(hero), 22, UITheme.PARCHMENT, UITheme.number_font()))
	var row := hbox(12)
	cv.add_child(row)
	var e1 := TempoGacha.call_error(hero, 1)
	var b1 := button("Call once — %d Embers" % TempoGacha.COST_ONE, func() -> void: _summon(1), &"PrimaryButton", 300.0)
	b1.disabled = e1 != ""
	row.add_child(b1)
	var e10 := TempoGacha.call_error(hero, 10)
	var b10 := button("Call ten — %d Embers" % TempoGacha.COST_TEN, func() -> void: _summon(10), &"PrimaryButton", 300.0)
	b10.disabled = e10 != ""
	row.add_child(b10)
	if e1 != "":
		cv.add_child(_wrapped(e1, 14, UITheme.TEXT_MUTED, 600))
	var buy := button("Buy 10 Soul Embers — %d gold" % TempoGacha.ember_price(hero), func() -> void: _buy_embers(), &"", 420.0)
	buy.disabled = hero.inventory.gold < TempoGacha.ember_price(hero)
	cv.add_child(buy)
	cv.add_child(Tips.rule())
	var p5 := int(st.get("pity5", 0))
	var p4 := int(st.get("pity4", 0))
	cv.add_child(_wrapped("★★★★★ %.1f%% (half of them the featured spirit)   ·   ★★★★ %d%%   ·   ★★★ the rest" % [TempoGacha.RATE_5 * 100.0, roundi(TempoGacha.RATE_4 * 100.0)], 14, UITheme.TEXT, 620))
	cv.add_child(_wrapped("A ★★★★ or better within every %d calls: %d / %d.   A ★★★★★ by call %d: %d / %d%s." % [TempoGacha.FOUR_PITY, p4, TempoGacha.FOUR_PITY,
		TempoGacha.HARD_PITY, p5, TempoGacha.HARD_PITY, "   (the next ★★★★★ is the featured spirit)" if bool(st.get("lost_feature", false)) else ""], 14, UITheme.GOLD, 620))
	cv.add_child(_wrapped("Soul Embers come from monsters (far more in the dungeons), champions, bosses and treasure chests.", 13, UITheme.TEXT_DIM, 620))
	# the history
	var hist: Array = st.get("history", [])
	if not hist.is_empty():
		_mine.add_child(UITheme.label("Recent calls", 16, UITheme.TEXT_DIM, UITheme.body_bold()))
		var flow := HFlowContainer.new()
		flow.add_theme_constant_override("h_separation", 18)
		_mine.add_child(flow)
		for h in hist.slice(0, 16):
			var n := int(h.get("stars", 3))
			flow.add_child(UITheme.label("%s %s" % ["★".repeat(n), h.get("name", "")], 14, TempoGacha.STAR_COLORS.get(n, UITheme.TEXT), UITheme.body_font()))

func _buy_embers() -> void:
	var err := TempoGacha.buy_embers(hero)
	if err != "":
		Events.notify.emit(err, &"error")
	else:
		Audio.play_ui(&"ui_click")
	refresh()

func _summon(n: int) -> void:
	var res := TempoGacha.summon(hero, n)
	if res.is_empty():
		Events.notify.emit(TempoGacha.call_error(hero, n), &"error")
		return
	Audio.play_ui(&"skill_unlock")
	Game.ui_root.reveal("The Shrine answers" if n == 1 else "Ten spirits answer", res.map(func(r): return TempoGacha.card(r)), n > 1,
		func() -> void: refresh())
	refresh()

func _build_hall() -> void:
	if hero.spirit_hall.is_empty():
		_mine.add_child(UITheme.label("The hall is empty. Spirits you summon on the \"Summon\" page wait here.", 18, UITheme.TEXT_DIM, UITheme.body_font()))
		return
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(1520, 620)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_mine.add_child(scroll)
	var list := vbox(8)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)
	var sorted := hero.spirit_hall.duplicate()
	sorted.sort_custom(func(a, b): return a.stars > b.stars if a.stars != b.stars else a.uid < b.uid)
	for t: TempoData in sorted:
		list.add_child(_hall_row(t))

func _hall_row(t: TempoData) -> Control:
	var row := inset(Vector2(1490, 0))
	var h := hbox(14)
	row.add_child(h)
	var ic := TextureRect.new()
	ic.texture = DataTempos.class_icon(t.class_id)
	ic.custom_minimum_size = Vector2(48, 48)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.modulate = t.class_def().get("color", Color.WHITE)
	h.add_child(ic)
	var v := vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var sc: Color = TempoGacha.STAR_COLORS.get(t.stars, UITheme.PARCHMENT)
	v.add_child(UITheme.label("%s  %s" % [ItemNames.star_text(t.stars) if t.stars > 0 else "", t.full_name()], 20, sc, UITheme.title_font()))
	var skills := ", ".join(t.skills.map(func(sk): return String(DataTempos.skill(sk).get("name", sk))))
	var res := "  ·  Resonance %s" % TempoGacha.roman(t.resonance) if t.resonance > 0 else ""
	v.add_child(UITheme.label("%s  ·  %s spirit  ·  %d%% of your strength%s  ·  %s" % [t.class_name_text(), t.grade_name(), roundi(t.mirror() * 100.0),
		res, skills], 14, UITheme.TEXT, UITheme.body_font()))
	if TempoRules.bound_count(hero) < DataTempos.MAX_ACTIVE:
		h.add_child(button("Bind", func() -> void: _hall_act(TempoGacha.bind(hero, t.uid), t), &"PrimaryButton", 140.0))
	for b: TempoData in hero.tempos:
		h.add_child(button("Swap with %s" % b.tempo_name.get_slice(" ", 0), func() -> void: _hall_act(TempoGacha.swap(hero, b.uid, t.uid), t), &"", 220.0))
	var give: int = TempoGacha.RELEASE_EMBERS.get(maxi(3, t.stars), 2) + (t.resonance * 10 if t.stars == 5 else 0)
	h.add_child(button("Release (+%d Embers)" % give, func() -> void: _hall_release(t, give), &"", 220.0))
	return row

func _hall_release(t: TempoData, give: int) -> void:
	Game.ui_root.ask("Release %s" % t.tempo_name, "Let %s go? You receive %d Soul Embers; its gear returns to your bag." % [t.full_name(), give],
		func() -> void:
			if TempoGacha.release(hero, t.uid) < 0:
				Events.notify.emit("Your bag cannot hold its gear", &"error")
			refresh(), "Release", true)

func _hall_act(err: String, t: TempoData) -> void:
	if err != "":
		Events.notify.emit(err, &"error")
		return
	TempoParty.refresh(hero)
	Audio.play_ui(&"skill_unlock")
	Events.notify.emit("%s walks with you." % t.full_name(), &"info")
	refresh()

func _rest(t: TempoData) -> void:
	var err := TempoGacha.rest(hero, t.uid)
	if err != "":
		Events.notify.emit(err, &"error")
		return
	TempoParty.refresh(hero)
	refresh()
