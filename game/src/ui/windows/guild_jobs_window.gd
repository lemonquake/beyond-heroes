class_name GuildJobsWindow
extends UIWindow
## The Guild House board (bh-016): pick between the two guilds of Malasugue (join or transfer at the counter), read that
## guild's job postings and take up to GuildJobs.ACTIVE_MAX miniquests; hand finished ones in for gold. Postings are
## only open to registered members of the guild that posted them.

var guild: StringName = &"swordfin"
var _tabs := {}
var _info: VBoxContainer
var _board: VBoxContainer
var _mine: VBoxContainer
var _foot: Label

func _init() -> void:
	super._init("Guild House", Vector2(1300, 940))

## Open the window on one guild's board (`gid` empty = the hero's own guild, else Swordfin).
func open_on(gid: StringName = &"") -> void:
	var hero := Game.hero
	if gid == &"" or not DataGuilds.GUILDS.has(gid):
		gid = hero.guild if hero and hero.guild != &"" else &"swordfin"
	guild = gid
	Game.ui_root.open(&"guild_jobs")

func _build() -> void:
	Events.guild_jobs_changed.connect(_on_changed)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _on_changed())
	# the two guilds
	var tabs := hbox(16)
	tabs.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(tabs)
	for gid in [&"swordfin", &"lantern"]:
		var g := DataGuilds.guild(gid)
		var b := Button.new()
		b.toggle_mode = true
		b.text = "  %s" % g.name
		b.icon = UIArt.tex(g.crest)
		b.expand_icon = true
		b.custom_minimum_size = Vector2(430, 62)
		b.add_theme_font_size_override("font_size", 22)
		b.add_theme_constant_override("icon_max_width", 44)
		b.focus_mode = Control.FOCUS_ALL
		b.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			guild = gid
			refresh())
		tabs.add_child(b)
		_tabs[gid] = b
	var info_panel := inset()
	body.add_child(info_panel)
	_info = vbox(4)
	info_panel.add_child(_info)
	# job board (left) and carried jobs (right)
	var cols := hbox(20)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	var left := vbox(6)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_stretch_ratio = 1.15
	cols.add_child(left)
	left.add_child(section("Job Board"))
	var ls := ScrollContainer.new()
	ls.size_flags_vertical = Control.SIZE_EXPAND_FILL
	ls.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	left.add_child(ls)
	_board = vbox(8)
	_board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ls.add_child(_board)
	var right := vbox(6)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	right.add_child(section("Your Jobs"))
	var rs := ScrollContainer.new()
	rs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rs.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(rs)
	_mine = vbox(8)
	_mine.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rs.add_child(_mine)
	var foot := MarginContainer.new()
	foot.add_theme_constant_override("margin_left", 22)
	foot.add_theme_constant_override("margin_right", 22)
	body.add_child(foot)
	_foot = UITheme.label("", 18, UITheme.GOLD, UITheme.body_bold())
	foot.add_child(_foot)

## A window button, taller on a phone so a thumb can hit it.
func _btn(text: String, cb: Callable, variation := &"", min_w := 0.0) -> Button:
	var b := button(text, cb, variation, min_w)
	if Settings.touch_mode:
		b.custom_minimum_size.y = 56.0
	return b

func _on_changed() -> void:
	if visible:
		refresh()

func refresh() -> void:
	var hero := Game.hero
	if hero == null:
		return
	for gid in _tabs:
		(_tabs[gid] as Button).set_pressed_no_signal(gid == guild)
	_fill_info(hero)
	_fill_board(hero)
	_fill_mine(hero)
	var s := GuildJobs.state(hero)
	_foot.text = "Jobs finished: %d   ·   Earned from jobs: %d gold   ·   Your gold: %d" % [s.done, s.earned, hero.inventory.gold]

func _clear(c: Control) -> void:
	for n in c.get_children():
		c.remove_child(n)
		n.queue_free()

func _fill_info(hero: HeroData) -> void:
	_clear(_info)
	var g := DataGuilds.guild(guild)
	var head := hbox(12)
	_info.add_child(head)
	var gname := UITheme.title(String(g.name), 24, (g.color as Color).lightened(0.3))
	gname.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(gname)
	if hero.guild == guild:
		head.add_child(UITheme.label("You are registered: %s" % DataGuilds.tier_name(hero.tier), 19, UITheme.GOOD, UITheme.body_bold()))
	else:
		var fee := GuildRules.join_fee(hero, guild)
		var verb := "Register with %s" % g.short if hero.guild == &"" else "Transfer to %s" % g.short
		var b := _btn("%s (%d gold)" % [verb, fee], func() -> void: _join(guild), &"PrimaryButton", 380.0)
		b.disabled = hero.inventory.gold < fee
		head.add_child(b)
	var mo := UITheme.label("“%s”  —  %s" % [g.motto, g.master], 16, UITheme.TEXT_DIM, UITheme.body_font())
	_info.add_child(mo)
	var pk := UITheme.label("Seal perks per tier: %s.  %s." % [", ".join(g.perk_text), ".  ".join(g.features)], 16, UITheme.TEXT, UITheme.body_font())
	pk.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_info.add_child(pk)
	var tip := "Jobs pay %d%% extra for your Class %s tier." % [roundi((GuildJobs.tier_multiplier(hero) - 1.0) * 100.0), DataGuilds.letter(hero.tier)] \
		if hero.guild == guild and hero.tier > 0 else "Only registered members of a guild may take its jobs. Your tier stays with you if you change guild."
	_info.add_child(UITheme.label(tip, 16, UITheme.GOLD, UITheme.body_font()))

func _join(gid: StringName) -> void:
	var h := Game.hero
	var g := DataGuilds.guild(gid)
	var fee := GuildRules.join_fee(h, gid)
	var what := "Register as a Class E hero of %s" % g.name if h.guild == &"" else "Transfer to %s (you keep your Class %s tier)" % [g.name, DataGuilds.letter(h.tier)]
	Game.ui_root.ask(String(g.name), "%s for %d gold?" % [what, fee],
		func() -> void:
			var err := GuildRules.join(h, gid)
			if err != "":
				Events.notify.emit(err, &"error")
			else:
				Game.ui_root.show_tier_award(h.tier, "You joined %s" % g.name),
		"Join (%d gold)" % fee)

func _card(accent: Color) -> Array:
	var p := PanelContainer.new()
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.13, 0.1, 0.075, 0.92)
	st.set_corner_radius_all(4)
	st.set_border_width_all(2)
	st.border_color = accent
	st.content_margin_left = 14
	st.content_margin_right = 14
	st.content_margin_top = 8
	st.content_margin_bottom = 10
	p.add_theme_stylebox_override("panel", st)
	var v := vbox(4)
	p.add_child(v)
	return [p, v]

func _fill_board(hero: HeroData) -> void:
	_clear(_board)
	var g := DataGuilds.guild(guild)
	var jobs := GuildJobs.refresh_board(hero, guild)
	if jobs.is_empty():
		_board.add_child(UITheme.label("Nothing is posted for your level right now.", 18, UITheme.TEXT_DIM, UITheme.body_font()))
	for j in jobs:
		var c := _card((g.color as Color).darkened(0.1))
		var v: VBoxContainer = c[1]
		var top := hbox(8)
		v.add_child(top)
		var t := UITheme.label(String(j.title), 21, UITheme.GOLD, UITheme.body_bold())
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(t)
		top.add_child(UITheme.label(String(DataGuildJobs.KINDS.get(j.kind, "")), 15, UITheme.TEXT_DIM, UITheme.body_font()))
		var tx := UITheme.label(String(j.text), 16, UITheme.TEXT, UITheme.body_font())
		tx.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(tx)
		var bot := hbox(10)
		v.add_child(bot)
		var pay := UITheme.label("Pays %d gold" % GuildJobs.payout(hero, j), 18, UITheme.GOOD, UITheme.number_font())
		pay.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bot.add_child(pay)
		var id := int(j.id)
		var err := GuildJobs.accept_error(hero, guild, id)
		var b := _btn("Accept", func() -> void: _accept(id), &"PrimaryButton", 150.0)
		b.disabled = err != ""
		if err != "":
			b.tooltip_text = err
		bot.add_child(b)
		_board.add_child(c[0])
	if hero.guild != guild:
		var l := UITheme.label("Register with %s to accept these jobs." % g.short, 16, UITheme.BAD, UITheme.body_font())
		_board.add_child(l)

func _accept(id: int) -> void:
	var err := GuildJobs.accept(Game.hero, guild, id)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Events.notify.emit("Job accepted", &"info")

func _fill_mine(hero: HeroData) -> void:
	_clear(_mine)
	var act := GuildJobs.active(hero)
	_mine.add_child(UITheme.label("Carrying %d of %d jobs" % [act.size(), GuildJobs.ACTIVE_MAX], 16, UITheme.TEXT_DIM, UITheme.body_font()))
	if act.is_empty():
		var e := UITheme.label("You carry no jobs. Accept one from the board and come back when it is done.", 17, UITheme.TEXT_DIM, UITheme.body_font())
		e.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_mine.add_child(e)
	for j in act:
		var done := GuildJobs.is_done(j)
		var g := DataGuilds.guild(StringName(j.guild))
		var c := _card(UITheme.GOOD if done else (g.get("color", UITheme.BRONZE_DIM) as Color).darkened(0.1))
		var v: VBoxContainer = c[1]
		var top := hbox(8)
		v.add_child(top)
		var t := UITheme.label(String(j.title), 20, UITheme.GOLD, UITheme.body_bold())
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(t)
		top.add_child(UITheme.label(String(g.get("short", "")), 15, (g.get("color", UITheme.TEXT_DIM) as Color).lightened(0.3), UITheme.body_bold()))
		var tx := UITheme.label(String(j.text), 15, UITheme.TEXT_DIM, UITheme.body_font())
		tx.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(tx)
		var bar := ProgressBar.new()
		bar.min_value = 0
		bar.max_value = int(j.goal)
		bar.value = int(j.progress)
		bar.show_percentage = false
		bar.custom_minimum_size = Vector2(0, 16)
		v.add_child(bar)
		var bot := hbox(8)
		v.add_child(bot)
		var pl := UITheme.label("%d / %d   ·   %d gold" % [j.progress, j.goal, GuildJobs.payout(hero, j)], 17, UITheme.GOOD if done else UITheme.TEXT, UITheme.number_font())
		pl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bot.add_child(pl)
		var id := int(j.id)
		if done:
			bot.add_child(_btn("Hand In", func() -> void: _claim(id), &"PrimaryButton", 130.0))
		else:
			bot.add_child(_btn("Drop", func() -> void: _drop(id), &"", 100.0))
		_mine.add_child(c[0])

func _claim(id: int) -> void:
	var err := GuildJobs.claim(Game.hero, id)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Audio.play_ui(&"level_up")

func _drop(id: int) -> void:
	var j := GuildJobs.find_active(Game.hero, id)
	if j.is_empty():
		return
	Game.ui_root.ask("Drop job", "Give up “%s”? Your progress is lost." % j.title, func() -> void: GuildJobs.abandon(Game.hero, id), "Drop it", true)
