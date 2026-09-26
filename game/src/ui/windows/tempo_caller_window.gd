class_name TempoCallerWindow
extends UIWindow
## Veyra Ashgrave's shrine (opened from her dialogue). "Spirits" lists the fallen warriors answering her call right now —
## class, personality, skills, how they died, the strength they would have bound to you, and the price of binding.
## "Your Tempos" lists the bound spirits; fallen ones can be called back for a fee, any can be released.

var hero: HeroData
var _tabs: TabBar
var _page := &"roster"
var _cards: HBoxContainer
var _mine: VBoxContainer
var _status: Label
var _gold: Label
var _clock_t := 0.0

func _init() -> void:
	super._init("The Shrine of the Fallen", Vector2(1600, 860))

func _build() -> void:
	var top := hbox(16)
	body.add_child(top)
	_tabs = TabBar.new()
	_tabs.add_tab("Spirits answering")
	_tabs.add_tab("Your Tempos")
	_tabs.tab_changed.connect(func(i: int) -> void:
		_page = &"roster" if i == 0 else &"fallen"
		refresh())
	_tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_tabs)
	_gold = UITheme.label("", 18, UITheme.GOLD, UITheme.number_font())
	top.add_child(_gold)
	_status = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	body.add_child(_status)
	_cards = hbox(14)
	_cards.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_cards)
	_mine = vbox(10)
	_mine.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_mine)
	Events.tempo_changed.connect(func(_u): if visible: refresh())

## Open on a page: &"roster" (bind) or &"fallen" (your Tempos).
func open_on(page: StringName) -> void:
	_page = page
	Game.ui_root.open(&"tempo_caller")
	_tabs.current_tab = 0 if page == &"roster" else 1

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	_gold.text = "%d gold" % hero.inventory.gold
	_cards.visible = _page == &"roster"
	_mine.visible = _page != &"roster"
	for c in _cards.get_children():
		c.queue_free()
	for c in _mine.get_children():
		c.queue_free()
	if _page == &"roster":
		_build_roster()
	else:
		_build_mine()
	_update_status()

func _update_status() -> void:
	var left := maxf(0.0, float(hero.tempo_roster.get("refresh_at", 0.0)) - hero.play_time)
	_status.text = "Bound Tempos: %d / %d    ·    New spirits answer in %d:%02d    ·    A Tempo mirrors half your strength and wears gear up to %s rarity." % [
		TempoRules.bound_count(hero), DataTempos.MAX_ACTIVE, int(left) / 60, int(left) % 60, BH.rarity_name(TempoRules.best_wearable_rarity(hero))]

func _process(delta: float) -> void:
	if not visible or hero == null:
		return
	_clock_t -= delta
	if _clock_t <= 0.0:
		_clock_t = 1.0
		if hero.play_time >= float(hero.tempo_roster.get("refresh_at", 0.0)) and _page == &"roster":
			refresh()
		else:
			_update_status()

func _build_roster() -> void:
	var offers := TempoRules.roster(hero)
	var mirror := TempoRules.hero_mirror(hero)
	for i in offers.size():
		_cards.add_child(_card(offers[i], i, mirror))

func _card(t: TempoData, index: int, mirror: DerivedStats) -> Control:
	var td := t.class_def()
	var p := inset(Vector2(378, 0))
	p.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var v := vbox(6)
	p.add_child(v)
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
	var tr := t.trait_def()
	var trl := UITheme.label("%s: %s" % [tr.get("name", ""), tr.get("desc", "")], 14, UITheme.TEXT, UITheme.body_font())
	trl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	trl.custom_minimum_size = Vector2(350, 0)
	v.add_child(trl)
	var org := UITheme.label("\"%s\"" % t.origin, 14, UITheme.TEXT_DIM, UITheme.body_font())
	org.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	org.custom_minimum_size = Vector2(350, 0)
	v.add_child(org)
	v.add_child(Tips.rule())
	for sid in t.skills:
		var sk := DataTempos.skill(sid)
		var row := hbox(8)
		var si := TextureRect.new()
		si.texture = DataTempos.skill_icon(sid)
		si.custom_minimum_size = Vector2(34, 34)
		si.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		si.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(si)
		var heal := DataTempos.is_heal(sid)
		var nl := UITheme.label(String(sk.name) + ("  (heals)" if heal else ""), 15, UITheme.GOOD if heal else UITheme.PARCHMENT, UITheme.body_bold())
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(nl)
		var desc := String(sk.desc)
		var title := String(sk.name)
		TooltipLayer.attach(row, func() -> Control: return Tips.text("%s\n%d mana · %d s cooldown" % [desc, roundi(float(sk.mana)), roundi(float(sk.cooldown))], title))
		v.add_child(row)
	v.add_child(Tips.rule())
	var d := TempoRules.compute(t, mirror, hero.progress.level, hero.cls)
	var g := GridContainer.new()
	g.columns = 4
	g.add_theme_constant_override("h_separation", 12)
	for row in [[&"max_hp", "Health"], [&"max_mana", "Mana"], [&"defense", "Defense"], [&"crit_chance", "Critical"]]:
		g.add_child(UITheme.label(row[1], 14, UITheme.TEXT_DIM, UITheme.body_font()))
		g.add_child(UITheme.label(StatDefs.format_value(row[0], d.get_stat(row[0])), 14, UITheme.PARCHMENT, UITheme.number_font()))
	v.add_child(g)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	v.add_child(spacer)
	var err := TempoRules.hire_error(hero, index)
	var b := button("Bind — %d gold" % t.price, func() -> void: _bind(index, t), &"PrimaryButton", 300.0)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.disabled = err != ""
	if err != "":
		TooltipLayer.attach(b, func() -> Control: return Tips.text(err))
	v.add_child(b)
	return p

func _bind(index: int, t: TempoData) -> void:
	Game.ui_root.ask("Bind %s" % t.tempo_name, "Bind the spirit of %s the %s to you for %d gold?\nIt will follow you until it falls, and fight with half your strength." % [
			t.tempo_name, t.class_name_text(), t.price],
		func() -> void:
			var bound := TempoRules.hire(hero, index)
			if bound == null:
				Events.notify.emit(TempoRules.hire_error(hero, index), &"error")
				return
			TempoParty.refresh(hero)
			Audio.play_ui(&"skill_unlock")
			Events.notify.emit("%s answers your call." % bound.tempo_name, &"info")
			refresh(), "Bind (%d gold)" % t.price)

func _build_mine() -> void:
	if hero.tempos.is_empty():
		var l := UITheme.label("No spirit walks with you yet. Choose one on the \"Spirits answering\" page.", 18, UITheme.TEXT_DIM, UITheme.body_font())
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
		v.add_child(UITheme.title("%s  —  %s" % [t.tempo_name, t.class_name_text()], 24, UITheme.PARCHMENT))
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
	Game.ui_root.ask("Release %s" % t.tempo_name, "Let %s's spirit go? It will not return; its gear comes back to your bag." % t.tempo_name,
		func() -> void:
			var err := TempoRules.release(hero, t)
			if err != "":
				Events.notify.emit(err, &"error")
				return
			TempoParty.refresh(hero)
			refresh(), "Release", true)
