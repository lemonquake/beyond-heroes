class_name RankTracker
extends PanelContainer
## bh-033: the optional next-rank checklist under the quest objective (moves with the quest panels in touch play).
## Expanded: the next rank, each step with its count and the one immediate action spelled out; completed steps fold
## into one line that opens on request. Minimized: one short progress line. Hidden: not shown (the Character screen's
## "Track Rank Up" brings it back). The choice is the hero's own (HeroData.rank_tracker). Content comes from
## GuildRules.rank_guide, the same rules that promote; it is rebuilt on progress events, never per frame.

var _box: VBoxContainer
var _show_done := false
var _queued := false

func _init() -> void:
	theme_type_variation = &"GlassPanel"
	custom_minimum_size = Vector2(300, 0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 3)
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_box)
	visible = false

func _ready() -> void:
	for sig in [Events.player_spawned, Events.map_loaded, Events.player_leveled, Events.world_flag_set, Events.tier_changed, Events.guild_joined, Events.guild_jobs_changed,
			Events.miniboss_defeated, Events.gold_picked, Events.item_sold, Events.item_bought, Events.stage_cleared, Events.rank_tracker_changed]:
		sig.connect(func(_a = null, _b = null) -> void: queue_refresh())
	Settings.changed.connect(queue_refresh)
	queue_refresh()

## Coalesce bursts of events (a kill can level up, drop gold and set a flag in one frame) into one rebuild.
func queue_refresh() -> void:
	if _queued:
		return
	_queued = true
	_refresh.call_deferred()

func _hero() -> HeroData:
	return Game.hero

func _refresh() -> void:
	_queued = false
	var hero := _hero()
	if hero != null and not hero.inventory_changed.is_connected(queue_refresh):
		hero.inventory_changed.connect(queue_refresh)
	for c in _box.get_children():
		_box.remove_child(c)
		c.queue_free()
	if hero == null or hero.rank_tracker == "hidden":
		visible = false
		return
	visible = true
	var g := GuildRules.rank_guide(hero)
	var touch := Settings.touch_mode
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 6)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.add_child(head)
	var minimized := hero.rank_tracker == "minimized"
	var t: Dictionary = DataGuilds.tier(int(g.get("rank", hero.tier)))
	var title := ("Class %s next" if touch else "Rank up: Class %s") % String(t.letter) if g.state != "max" else "Class %s" % String(t.letter)
	var tl := UITheme.label(title, 16, UITheme.GOLD, UITheme.title_font())
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UITheme.fit_line(tl)
	head.add_child(tl)
	head.add_child(_button("+" if minimized else "–", "Expand" if minimized else "Minimize", touch,
		func() -> void: _set_mode("expanded" if minimized else "minimized")))
	head.add_child(_button("×", "Hide (Character screen: Track Rank Up)", touch, func() -> void: _set_mode("hidden")))
	if g.state == "max":
		_box.add_child(_line("You hold the highest rank. Nothing is left to track.", 14, UITheme.TEXT_DIM))
		return
	if not minimized:
		_box.add_child(_line(String(t.title), 13, UITheme.TEXT_DIM))
	if minimized:
		var short := "Ready: promotion is automatic" if g.ready else "%d / %d · %s" % [int(g.done), int(g.total), String(g.next_action)]
		_box.add_child(_line(short, 14, UITheme.GOOD if g.ready else UITheme.TEXT))
		return
	if g.ready:
		_box.add_child(_line("Ready to rank up. Promotion happens automatically.", 15, UITheme.GOOD))
		return
	var done_steps := []
	var first := true
	var shown := 0
	var more := 0
	# touch play keeps the left column short (the movement stick sits below it): two open steps, the rest folded
	var room := 2 if touch and not _show_done else 99
	for s in g.steps:
		if s.done:
			done_steps.append(s)
			continue
		if shown >= room:
			more += 1
			continue
		shown += 1
		_box.add_child(_step_row(s, false))
		if first:
			first = false
			if String(s.hint) != "":
				_box.add_child(_line("Next: " + String(s.hint), 13, UITheme.TEXT_DIM, 18))
	if not done_steps.is_empty() or more > 0:
		var fold := ("%d more" % more) if more > 0 else ""
		if not done_steps.is_empty():
			fold += (", " if fold != "" else "") + "%d done" % done_steps.size()
		var tog := _button("Show less" if _show_done else "%s (show)" % fold, "", touch, func() -> void:
			_show_done = not _show_done
			queue_refresh(), true)
		_box.add_child(tog)
		if _show_done:
			for s in done_steps:
				_box.add_child(_step_row(s, true))
	if not touch or _show_done:
		_box.add_child(_line(String(g.note), 12, UITheme.TEXT_MUTED))

func _set_mode(mode: String) -> void:
	var hero := _hero()
	if hero == null:
		return
	hero.rank_tracker = mode
	Events.rank_tracker_changed.emit()

func _step_row(s: Dictionary, done: bool) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mark := UITheme.label("✓" if done else "○", 15, UITheme.GOOD if done else UITheme.GOLD, UITheme.body_bold())
	mark.custom_minimum_size = Vector2(16, 0)
	row.add_child(mark)
	var label := String(s.label)
	if done and String(s.get("detail", "")) != "" and bool(s.get("story", false)):
		label += ": " + String(s.detail)          # finished story steps may name themselves; open ones never spoil
	var l := UITheme.label(label, 15, UITheme.TEXT_DIM if done else UITheme.TEXT, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	if int(s.need) > 1:
		row.add_child(UITheme.label("%d / %d" % [mini(int(s.have), int(s.need)) if s.key != "fee" else int(s.have), int(s.need)], 14,
			UITheme.GOOD if done else UITheme.TEXT_DIM, UITheme.number_font()))
	return row

func _line(text: String, size: int, color: Color, indent := 0) -> Control:
	var l := UITheme.label(text, size, color, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(270 - indent, 0)
	if indent <= 0:
		return l
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", indent)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.add_child(l)
	return m

func _button(text: String, tip: String, touch: bool, on_press: Callable, wide := false) -> Button:
	var b := Button.new()
	b.text = text
	b.tooltip_text = tip
	b.theme_type_variation = &"FlatButton"
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 15 if wide else 18)
	b.custom_minimum_size = Vector2(0 if wide else (48 if touch else 26), 44 if touch else 24)
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	b.pressed.connect(on_press)
	if wide:
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	return b
