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

const PAGES := [&"roster", &"renowned", &"fallen"]

func _init() -> void:
	super._init("The Shrine of the Fallen", Vector2(1600, 880))

func _build() -> void:
	var top := hbox(16)
	body.add_child(top)
	_tabs = TabBar.new()
	_tabs.add_tab("Spirits answering")
	_tabs.add_tab("Renowned")
	_tabs.add_tab("Your Tempos")
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
	_page = page if PAGES.has(page) else &"roster"
	Game.ui_root.open(&"tempo_caller")
	_tabs.current_tab = PAGES.find(_page)

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	_gold.text = "%d gold" % hero.inventory.gold
	_cards.visible = _page != &"fallen"
	_mine.visible = _page == &"fallen"
	for c in _cards.get_children():
		c.queue_free()
	for c in _mine.get_children():
		c.queue_free()
	match _page:
		&"roster": _build_roster()
		&"renowned": _build_renowned()
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
		&"renowned":
			_status.text = "%s    ·    Renowned spirits carry %d%% of your strength and skills no other spirit knows. Each answers only a hero of its level.    %s" % [
				bound, roundi(float(DataTempos.RENOWNED.mirror) * 100.0), gear]
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
	for id in DataTempos.legend_ids():
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
		var tt := UITheme.label(String(lg.title), 16, DataTempos.RENOWNED.color, UITheme.body_bold())
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
		var col := DataTempos.RENOWNED.color if uniq else (UITheme.GOOD if heal else UITheme.PARCHMENT)
		var nl := UITheme.label(String(sk.name) + ("  (heals)" if heal else "") + ("  ★" if uniq else ""), 15, col, UITheme.body_bold())
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(nl)
		var desc := String(sk.desc)
		var title := String(sk.name)
		TooltipLayer.attach(row, func() -> Control: return Tips.text("%s\n%d mana · %d s cooldown%s" % [desc, roundi(float(sk.mana)), roundi(float(sk.cooldown)),
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
