class_name GuildWindow
extends UIWindow
## bh-027: the Guild window (Z). For a Guildmaster: the guild's banner and hall (Overview), its roster of adventurers
## and fellow players (Members: dismiss, applicants, levels), its passives and Guild War passives (upgrade with gold and
## guild level), Call to Arms (summon members to fight beside you for 15 minutes) and every guild the hero knows.
## A hero in another guild sees that guild and may leave it; a hero without a guild of their own can found one here
## (name it — or roll a name — write its motto and Guild Info, and design its banner).

const PAGES := [["overview", "Overview"], ["members", "Members"], ["passives", "Passives"], ["war", "Guild War"],
	["summon", "Call to Arms"], ["guilds", "All Guilds"], ["found", "Found a Guild"]]
const GOLDEN := Color(0.96, 0.8, 0.42)

var page := "overview"
var _nav: VBoxContainer
var _content: VBoxContainer
var _scroll: ScrollContainer
var _nav_buttons := {}
var _tick := 0.0
# the founding form keeps what was typed while the page is rebuilt
var _form := {"name": "", "motto": "", "info": "", "style": {}}

func _init() -> void:
	super._init("Guild", Vector2(1640, 980))

func open_on(p_page := "") -> void:
	if p_page != "":
		page = p_page
	if Game.ui_root:
		Game.ui_root.open(&"guild")

func _build() -> void:
	Events.guild_changed.connect(_on_changed)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _on_changed())
	Events.guild_customised.connect(_on_changed)
	var cols := hbox(18)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	var nav_panel := inset(Vector2(250, 0))
	cols.add_child(nav_panel)
	_nav = vbox(8)
	nav_panel.add_child(_nav)
	_scroll = ScrollContainer.new()
	_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	cols.add_child(_scroll)
	_content = vbox(14)
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_content)

func _on_changed() -> void:
	if visible and not _typing():
		refresh()

func _typing() -> bool:
	var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	return f != null and (f is LineEdit or f is TextEdit) and is_ancestor_of(f)

func _process(delta: float) -> void:
	if not visible:
		return
	_tick += delta
	if _tick >= 1.0:
		_tick = 0.0
		if page in ["summon", "members", "war", "overview"] and not _typing():
			refresh()

func _pages(hero: HeroData) -> Array:
	var out := []
	var master := OwnGuild.is_master(hero)
	var member := hero.guild != &""
	for p in PAGES:
		match p[0]:
			"overview":
				if member:
					out.append(p)
			"members", "summon":
				if master:
					out.append(p)
			"passives", "war":
				if master or hero.guild == GuildRegistry.REMOTE:
					out.append(p)
			"found":
				if not OwnGuild.has(hero):
					out.append(p)
			_:
				out.append(p)
	return out

func refresh() -> void:
	var hero := Game.hero
	if hero == null:
		return
	var pages := _pages(hero)
	if not pages.any(func(p): return p[0] == page):
		page = String(pages[0][0])
	for c in _nav.get_children():
		_nav.remove_child(c)
		c.queue_free()
	var g := GuildRegistry.info(hero, hero.guild)
	var crest := TextureRect.new()
	crest.texture = GuildRegistry.banner(hero, hero.guild) if hero.guild != &"" else GuildBannerArt.texture(_form_style())
	crest.custom_minimum_size = Vector2(150, 225)
	crest.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	crest.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	crest.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_nav.add_child(crest)
	var gn := UITheme.title(GuildRules.display_name(hero) if hero.guild != &"" else "No guild", 20, GOLDEN)
	gn.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_nav.add_child(gn)
	if not g.is_empty():
		var sub := UITheme.label("Guild level %d · %s" % [int(g.level), "Guildmaster" if OwnGuild.is_master(hero) else DataGuilds.tier_name(hero.tier)], 14, UITheme.TEXT_DIM, UITheme.body_font())
		sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_nav.add_child(sub)
	_nav.add_child(HSeparator.new())
	_nav_buttons.clear()
	for p in pages:
		var id := String(p[0])
		var b := Button.new()
		b.text = String(p[1])
		b.toggle_mode = true
		b.button_pressed = id == page
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(230, 54 if Settings.touch_mode else 44)
		b.add_theme_font_size_override("font_size", 20)
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			page = id
			refresh())
		_nav.add_child(b)
		_nav_buttons[id] = b
	for c in _content.get_children():
		_content.remove_child(c)
		c.queue_free()
	match page:
		"overview": _overview(hero)
		"members": _members(hero)
		"passives": _passives(hero, ["guild", "special"])
		"war": _passives(hero, ["war"])
		"summon": _summon(hero)
		"guilds": _guilds(hero)
		"found": _found(hero)

# ---- helpers ------------------------------------------------------------------------------------------------------

func _card(accent: Color) -> Array:
	var p := PanelContainer.new()
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.11, 0.085, 0.065, 0.94)
	st.set_corner_radius_all(6)
	st.set_border_width_all(2)
	st.border_color = accent
	st.set_content_margin_all(14)
	st.shadow_color = Color(0, 0, 0, 0.45)
	st.shadow_size = 6
	p.add_theme_stylebox_override("panel", st)
	var v := vbox(6)
	p.add_child(v)
	return [p, v]

func _hero_title(text: String, size := 34) -> Label:
	var l := UITheme.title(text, size, GOLDEN)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_color_override("font_outline_color", Color(0.05, 0.03, 0.02, 0.9))
	l.add_theme_constant_override("outline_size", 6)
	return l

func _text(text: String, size := 17, col := UITheme.TEXT, font: Font = null) -> Label:
	var l := UITheme.label(text, size, col, font if font else UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l

## A one-line label for a row (wrapping labels collapse to one letter wide inside an HBox).
func _line(text: String, size := 17, col := UITheme.TEXT, font: Font = null) -> Label:
	return UITheme.label(text, size, col, font if font else UITheme.body_font())

func _bar(have: float, need: float, col: Color) -> ProgressBar:
	var b := ProgressBar.new()
	b.max_value = maxf(1.0, need)
	b.value = clampf(have, 0.0, b.max_value)
	b.show_percentage = false
	b.custom_minimum_size = Vector2(0, 18)
	var fill := StyleBoxFlat.new()
	fill.bg_color = col
	fill.set_corner_radius_all(3)
	b.add_theme_stylebox_override("fill", fill)
	return b

func _btn(text: String, cb: Callable, variation := &"", min_w := 0.0, err := "") -> Button:
	var b := button(text, cb, variation, min_w)
	if Settings.touch_mode:
		b.custom_minimum_size.y = 56.0
	if err != "":
		b.disabled = true
		b.tooltip_text = err
	return b

func _say(err: String, ok_text := "") -> void:
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	elif ok_text != "":
		Events.notify.emit(ok_text, &"info")
		Audio.play_ui(&"ui_open")

# ---- overview -----------------------------------------------------------------------------------------------------

func _overview(hero: HeroData) -> void:
	var g := GuildRegistry.info(hero, hero.guild)
	if g.is_empty():
		return
	var master := OwnGuild.is_master(hero)
	var top := hbox(26)
	_content.add_child(top)
	var bf := PanelContainer.new()
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.06, 0.045, 0.035, 1.0)
	st.set_border_width_all(5)
	st.border_color = (g.color as Color)
	st.set_content_margin_all(8)
	st.shadow_color = Color(g.color as Color, 0.4)
	st.shadow_size = 16
	bf.add_theme_stylebox_override("panel", st)
	bf.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	top.add_child(bf)
	var big := TextureRect.new()
	big.texture = GuildRegistry.banner(hero, hero.guild)
	big.custom_minimum_size = Vector2(300, 450)
	big.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	big.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	bf.add_child(big)
	var right := vbox(10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(right)
	right.add_child(_hero_title(GuildRules.display_name(hero), 40))
	if String(g.motto) != "":
		right.add_child(_text("“%s”" % g.motto, 21, UITheme.PARCHMENT))
	right.add_child(_text("Guildmaster: %s   ·   Guild level %d   ·   %d members" % [g.master, int(g.level), int(g.members)], 18, UITheme.TEXT, UITheme.body_bold()))
	if master:
		var lp := OwnGuild.level_progress(hero)
		if float(lp[1]) > 0.0:
			right.add_child(_text("Renown: %d / %d to guild level %d" % [int(lp[0]), int(lp[1]), OwnGuild.level(hero) + 1], 16, UITheme.TEXT_DIM))
			right.add_child(_bar(float(lp[0]), float(lp[1]), GOLDEN))
		else:
			right.add_child(_text("Renown: the guild stands at its highest level.", 16, UITheme.GOLD))
		var row := hbox(12)
		right.add_child(row)
		var tr := int(hero.own_guild.get("treasury", 0.0))
		row.add_child(_line("Treasury: %d / %d gold (members' tithes)" % [tr, int(OwnGuild.treasury_cap(hero))], 18, UITheme.GOOD, UITheme.number_font()))
		row.add_child(_btn("Collect", func() -> void:
			var n := OwnGuild.collect_treasury(hero)
			_say("" if n > 0 else "The treasury is empty", "Collected %d gold from the treasury" % n), &"PrimaryButton", 140.0, "" if tr > 0 else "Nothing to collect yet"))
		var slot_row := hbox(12)
		right.add_child(slot_row)
		slot_row.add_child(_line("Member slots: %d / %d" % [OwnGuild.members(hero).size(), OwnGuild.slots(hero)], 18, UITheme.TEXT, UITheme.body_bold()))
		var nu := OwnGuild.next_slot_upgrade(hero)
		if not nu.is_empty():
			var err := "" if hero.inventory.gold >= int(nu[1]) else "Needs %d gold" % nu[1]
			slot_row.add_child(_btn("Expand to %d slots (%d gold)" % [nu[0], nu[1]], func() -> void:
				Game.ui_root.ask("Expand the guild", "Expand %s to %d member slots for %d gold?" % [hero.own_guild.name, nu[0], nu[1]],
					func() -> void: _say(OwnGuild.buy_slots(hero), "The guild hall now holds %d members" % nu[0]), "Expand"), &"PrimaryButton", 360.0, err))
	var info_card := _card((g.color as Color).darkened(0.1))
	_content.add_child(info_card[0])
	var iv: VBoxContainer = info_card[1]
	iv.add_child(section("Guild Info"))
	if master:
		var motto := LineEdit.new()
		motto.text = String(hero.own_guild.get("motto", ""))
		motto.placeholder_text = "Motto"
		motto.max_length = OwnGuild.MOTTO_MAX
		motto.custom_minimum_size = Vector2(0, 44)
		iv.add_child(motto)
		var info := TextEdit.new()
		info.text = String(hero.own_guild.get("info", ""))
		info.placeholder_text = "What is your guild about? Who may join, what you hunt, where you meet... (other players see this)"
		info.custom_minimum_size = Vector2(0, 130)
		info.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
		iv.add_child(info)
		var r := hbox(10)
		iv.add_child(r)
		r.add_child(_btn("Save Motto & Info", func() -> void:
			_say(OwnGuild.set_details(hero, motto.text, info.text), "Guild info saved"), &"PrimaryButton", 260.0))
		r.add_child(_btn("Rename & Upload Banner...", func() -> void: Game.ui_root.open(&"guild_custom"), &"", 300.0))
		r.add_child(_btn("Banner Design...", func() -> void:
			_form.style = hero.own_guild.style.duplicate()
			page = "found"
			refresh(), &"", 220.0))
	else:
		iv.add_child(_text(String(g.get("info", "")) if String(g.get("info", "")) != "" else "No guild info yet.", 18))
		var grants := PackedStringArray()
		for t in g.get("perk_text", []):
			grants.append("%s per tier" % t)
		grants.append_array(g.get("features", []))
		if not grants.is_empty():
			iv.add_child(_text("Grants: " + " · ".join(grants), 16, UITheme.TEXT_DIM))
	var foot := hbox(12)
	_content.add_child(foot)
	if master:
		foot.add_child(_btn("Disband Guild", func() -> void:
			Game.ui_root.ask("Disband %s" % hero.own_guild.name, "Every member leaves and the guild is gone for good. The treasury (%d gold) comes to you and your tier stays yours." % int(hero.own_guild.treasury),
				func() -> void:
					OwnGuild.disband(hero)
					_say("", "The guild was disbanded"), "Disband", true), &"", 220.0))
	else:
		foot.add_child(_btn("Leave Guild", func() -> void:
			Game.ui_root.ask("Leave %s" % GuildRules.display_name(hero), "Leave the guild? Your Class %s tier stays yours." % DataGuilds.letter(hero.tier),
				func() -> void: _say(GuildRules.leave(hero)), "Leave", true), &"", 200.0))
		if not OwnGuild.has(hero):
			foot.add_child(_btn("Found Your Own Guild...", func() -> void:
				page = "found"
				refresh(), &"PrimaryButton", 300.0))

# ---- members ------------------------------------------------------------------------------------------------------

func _members(hero: HeroData) -> void:
	var og := hero.own_guild
	_content.add_child(_hero_title("Members of %s" % og.name, 32))
	var r := OwnGuild.recruit_range(hero)
	var next := OwnGuild.recruit_in(hero)
	_content.add_child(_text("%d of %d slots filled.  %s  Recruits arrive at level %d–%d (your level shapes who applies)." % [OwnGuild.members(hero).size(),
		OwnGuild.slots(hero), ("Next adventurer in about %s." % GuildSummons.clock(next)) if next < INF else "The guild is full.", r.x, r.y], 17, UITheme.TEXT_DIM))
	var me := _card(GOLDEN)
	_content.add_child(me[0])
	(me[1] as VBoxContainer).add_child(_member_row({"name": hero.hero_name, "cls": String(hero.cls.id), "level": hero.progress.level, "trait": "",
		"loyalty": 100.0, "kind": "master", "renown": 0.0}, hero, false))
	var list: Array = OwnGuild.members(hero).duplicate()
	list.sort_custom(func(a, b): return int(a.level) > int(b.level))
	if list.is_empty():
		_content.add_child(_text("No one has joined yet. Adventurers apply from time to time while a slot is free — keep adventuring.", 18, UITheme.TEXT_DIM))
	for m in list:
		var c := _card(Color(0.45, 0.36, 0.25) if String(m.kind) == "npc" else Color(0.45, 0.65, 1.0))
		_content.add_child(c[0])
		(c[1] as VBoxContainer).add_child(_member_row(m, hero, true))

func _member_row(m: Dictionary, hero: HeroData, can_kick: bool) -> Control:
	var row := hbox(14)
	var ic := TextureRect.new()
	ic.texture = UIArt.icon("classes", String(m.cls))
	ic.custom_minimum_size = Vector2(52, 52)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	row.add_child(ic)
	var mid := vbox(2)
	mid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(mid)
	var cd := DB.class_def(StringName(m.cls))
	var title := "Guildmaster" if String(m.kind) == "master" else DataGuildPassives.rank_title(m)
	mid.add_child(UITheme.label("%s  ·  %s" % [m.name, title], 20, GOLDEN if String(m.kind) == "master" else UITheme.PARCHMENT, UITheme.body_bold()))
	var tr: Dictionary = DataGuildPassives.TRAITS.get(StringName(String(m.get("trait", ""))), {})
	var sub := "Level %d %s" % [int(m.level), cd.display_name if cd else String(m.cls)]
	if String(m.kind) == "player":
		sub += "  ·  a fellow player"
	elif not tr.is_empty():
		sub += "  ·  %s: %s" % [tr.name, tr.text]
	mid.add_child(_text(sub, 15, UITheme.TEXT_DIM))
	if String(m.kind) == "npc":
		var lb := hbox(8)
		mid.add_child(lb)
		lb.add_child(UITheme.label("Loyalty", 14, UITheme.TEXT_DIM, UITheme.body_font()))
		var bar := _bar(float(m.loyalty), 100.0, Color(0.4, 0.75, 0.45))
		bar.custom_minimum_size = Vector2(220, 12)
		lb.add_child(bar)
		lb.add_child(UITheme.label("Renown earned: %d" % int(m.renown), 14, UITheme.TEXT_DIM, UITheme.number_font()))
		if GuildSummons.active(hero) and (GuildSummons.state(hero).get("called", []) as Array).has(int(m.id)):
			lb.add_child(UITheme.label("⚔ fighting beside you", 14, UITheme.GOOD, UITheme.body_bold()))
	if can_kick and OwnGuild.is_master(hero):
		var mid_id := int(m.id)
		row.add_child(_btn("Dismiss", func() -> void:
			Game.ui_root.ask("Dismiss %s" % m.name, "Send %s away from %s? Their slot opens for a new adventurer." % [m.name, hero.own_guild.name],
				func() -> void: _say(OwnGuild.kick(hero, mid_id)), "Dismiss", true), &"", 140.0))
	return row

# ---- passives -----------------------------------------------------------------------------------------------------

func _passives(hero: HeroData, kinds: Array) -> void:
	var war := kinds.has("war")
	var master := OwnGuild.is_master(hero)
	var ranks := GuildRules.passive_ranks(hero)
	_content.add_child(_hero_title("Guild War Passives" if war else "Guild Passives", 32))
	if war:
		var n := (Game.player as Player).guild_comrades if Game.player is Player else 0
		_content.add_child(_text("Made for many members at once: every rank grows with each guild member fighting beside you within %d m (Call to Arms fighters, and in multiplayer every guildmate on the map), up to %d. Fighting beside you now: %d." % [
			int(DataGuildPassives.WAR_RANGE), DataGuildPassives.WAR_CAP, n], 17, UITheme.TEXT_DIM))
	else:
		_content.add_child(_text("Every member of the guild — you included — gains these all the time. Ranks cost gold and need the guild to reach a level.", 17, UITheme.TEXT_DIM))
	if not master:
		_content.add_child(_text("Your Guildmaster, %s, chooses these. What they have trained so far:" % hero.remote_guild.get("master", "the Guildmaster"), 17, UITheme.GOLD))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	_content.add_child(grid)
	for id in DataGuildPassives.ORDER:
		var p := DataGuildPassives.passive(id)
		if not kinds.has(String(p.kind)):
			continue
		var r := int(ranks.get(String(id), 0))
		var c := _card(Color(0.85, 0.35, 0.3) if war else Color(0.62, 0.5, 0.3))
		(c[0] as Control).custom_minimum_size = Vector2(590, 0)
		grid.add_child(c[0])
		var v: VBoxContainer = c[1]
		var head := hbox(10)
		v.add_child(head)
		var ic := TextureRect.new()
		var parts := String(p.icon).split("/")
		ic.texture = UIArt.icon(parts[0], parts[1]) if parts.size() == 2 else null
		ic.custom_minimum_size = Vector2(40, 40)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		head.add_child(ic)
		var nm := UITheme.label(String(p.name), 22, GOLDEN, UITheme.body_bold())
		nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		head.add_child(nm)
		head.add_child(UITheme.label("Rank %d / %d" % [r, int(p.max)], 17, UITheme.GOOD if r > 0 else UITheme.TEXT_DIM, UITheme.number_font()))
		v.add_child(_text("Now: %s" % (DataGuildPassives.describe(id, r) if r > 0 else "not trained"), 16, UITheme.TEXT))
		if r < int(p.max):
			v.add_child(_text("Rank %d: %s" % [r + 1, DataGuildPassives.describe(id, r + 1)], 15, UITheme.TEXT_DIM))
			if master:
				var err := OwnGuild.upgrade_error(hero, id)
				var pid: StringName = id
				v.add_child(_btn("Train rank %d — %d gold (guild level %d)" % [r + 1, DataGuildPassives.cost(id, r + 1), DataGuildPassives.level_req(id, r + 1)],
					func() -> void: _say(OwnGuild.upgrade(hero, pid), "%s trained to rank %d" % [p.name, r + 1]), &"PrimaryButton", 0.0, err))

# ---- Call to Arms -------------------------------------------------------------------------------------------------

func _summon(hero: HeroData) -> void:
	_content.add_child(_hero_title("Call to Arms", 36))
	_content.add_child(_text("The Guildmaster's active skill: the strongest members of your guild march to your side and fight with you for %s, wherever you go. It can be called again %s after the call. Rank %d calls %d member%s; train it to call more." % [
		GuildSummons.clock(DataGuildPassives.SUMMON_DURATION), GuildSummons.clock(DataGuildPassives.SUMMON_COOLDOWN), GuildSummons.rank(hero),
		GuildSummons.rank(hero), "" if GuildSummons.rank(hero) == 1 else "s"], 18, UITheme.TEXT))
	var c := _card(Color(0.85, 0.35, 0.3))
	_content.add_child(c[0])
	var v: VBoxContainer = c[1]
	if GuildSummons.active(hero):
		v.add_child(UITheme.label("Your guild fights beside you: %s left" % GuildSummons.clock(GuildSummons.time_left(hero)), 24, UITheme.GOOD, UITheme.body_bold()))
		v.add_child(_bar(GuildSummons.time_left(hero), DataGuildPassives.SUMMON_DURATION, UITheme.GOOD))
	elif GuildSummons.cooldown_left(hero) > 0.0:
		v.add_child(UITheme.label("Ready again in %s" % GuildSummons.clock(GuildSummons.cooldown_left(hero)), 24, UITheme.TEXT_DIM, UITheme.body_bold()))
		v.add_child(_bar(DataGuildPassives.SUMMON_COOLDOWN - GuildSummons.cooldown_left(hero), DataGuildPassives.SUMMON_COOLDOWN, Color(0.6, 0.5, 0.35)))
	else:
		v.add_child(UITheme.label("Ready", 24, GOLDEN, UITheme.body_bold()))
	var who := GuildSummons.answering(hero)
	v.add_child(_text("Would answer now: %s" % (", ".join(who.map(func(m): return "%s (Lv %d %s)" % [m.name, m.level, DB.class_def(StringName(m.cls)).display_name])) if not who.is_empty() else "nobody yet"), 17, UITheme.PARCHMENT))
	var row := hbox(12)
	v.add_child(row)
	var err := GuildSummons.call_error(hero)
	row.add_child(_btn("Call to Arms!", func() -> void:
		var res := GuildSummons.call_to_arms(hero, Game.player as Node3D)
		_say("" if res.ok else String(res.text), String(res.text) if res.ok else "")
		if res.ok:
			close_window(), &"PrimaryButton", 300.0, err))
	var r := GuildSummons.rank(hero)
	if r < DataGuildPassives.SUMMON_MAX_RANK:
		var uerr := GuildSummons.upgrade_error(hero)
		row.add_child(_btn("Train to rank %d (%d members) — %d gold, guild level %d" % [r + 1, r + 1, GuildSummons.upgrade_cost(hero), int(DataGuildPassives.SUMMON_LEVELS[r - 1])],
			func() -> void: _say(GuildSummons.upgrade(hero), "Call to Arms is now rank %d" % (r + 1)), &"", 0.0, uerr))
	else:
		row.add_child(UITheme.label("Highest rank: %d members answer." % r, 17, UITheme.GOLD, UITheme.body_bold()))

# ---- all guilds ---------------------------------------------------------------------------------------------------

func _guilds(hero: HeroData) -> void:
	_content.add_child(_hero_title("The Guilds of Salmonan", 32))
	_content.add_child(_text("Every guild you know of, from the old houses of Malasugue to the guilds of heroes you met in multiplayer. Click one for its banner and info.", 17, UITheme.TEXT_DIM))
	var grid := GridContainer.new()
	grid.columns = 5
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	_content.add_child(grid)
	for gid in GuildRegistry.all_ids(hero):
		var g := GuildRegistry.info(hero, gid)
		if g.is_empty():
			continue
		var tex := GuildRegistry.banner(hero, gid)
		var b := Button.new()
		b.custom_minimum_size = Vector2(230, 330)
		b.focus_mode = Control.FOCUS_NONE
		b.tooltip_text = "%s\n%s" % [g.name, g.motto]
		var v := vbox(4)
		v.set_anchors_preset(Control.PRESET_FULL_RECT)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		b.add_child(v)
		var t := TextureRect.new()
		t.texture = tex
		t.custom_minimum_size = Vector2(150, 225)
		t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		t.mouse_filter = Control.MOUSE_FILTER_IGNORE
		t.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(t)
		var l := UITheme.label(String(g.name), 16, (g.color as Color).lightened(0.35), UITheme.body_bold())
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(l)
		var kind: String = {"own": "Your guild", "remote": "Your guild", "imported": "A fellow hero's", "canon": "Of Malasugue", "npc": "Guild House"}.get(String(g.kind), "")
		var k := UITheme.label("%s%s" % [kind, "  ·  member" if gid == hero.guild else ""], 13, UITheme.TEXT_DIM, UITheme.body_font())
		k.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		k.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(k)
		b.pressed.connect(func() -> void:
			var w := Game.ui_root.window(&"guild_detail") as GuildDetailWindow
			if w:
				w.show_guild(g, tex))
		grid.add_child(b)

# ---- founding -----------------------------------------------------------------------------------------------------

func _form_style() -> Dictionary:
	if (_form.style as Dictionary).is_empty():
		_form.style = GuildBannerArt.style_for(String(_form.name), randi())
	return GuildBannerArt.sanitize(_form.style)

func _found(hero: HeroData) -> void:
	var editing := OwnGuild.has(hero)
	_content.add_child(_hero_title("Banner Design" if editing else "Found a Guild", 36))
	if not editing:
		_content.add_child(_text("Register a guild of your own with the town's charter (%d gold). You become its Guildmaster: adventurers of every class will come to join it, you can upgrade its passives, call its members to arms, and invite fellow players. The guilds of Malasugue will hang your banner in the Guild House." % DataGuildPassives.FOUND_FEE, 18))
	var cols := hbox(26)
	_content.add_child(cols)
	var left := vbox(10)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(left)
	var preview := TextureRect.new()
	if not editing:
		left.add_child(section("Name"))
		var nrow := hbox(10)
		left.add_child(nrow)
		var name_edit := LineEdit.new()
		name_edit.text = String(_form.name)
		name_edit.placeholder_text = "Your guild's name"
		name_edit.max_length = GuildRules.ALIAS_MAX
		name_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_edit.custom_minimum_size = Vector2(0, 48)
		name_edit.add_theme_font_size_override("font_size", 22)
		name_edit.text_changed.connect(func(t: String) -> void: _form.name = t)
		nrow.add_child(name_edit)
		nrow.add_child(_btn("Roll a Name", func() -> void:
			var rng := RandomNumberGenerator.new()
			rng.randomize()
			var taken := GuildRegistry.all_ids(hero).map(func(id): return String(GuildRegistry.info(hero, id).get("name", "")))
			_form.name = GuildNames.roll_name(rng, taken)
			name_edit.text = String(_form.name), &"", 180.0))
		left.add_child(section("Motto"))
		var mrow := hbox(10)
		left.add_child(mrow)
		var motto := LineEdit.new()
		motto.text = String(_form.motto)
		motto.placeholder_text = "A line for the banner"
		motto.max_length = OwnGuild.MOTTO_MAX
		motto.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		motto.custom_minimum_size = Vector2(0, 44)
		motto.text_changed.connect(func(t: String) -> void: _form.motto = t)
		mrow.add_child(motto)
		mrow.add_child(_btn("Roll", func() -> void:
			var rng := RandomNumberGenerator.new()
			rng.randomize()
			_form.motto = GuildNames.motto(rng)
			motto.text = String(_form.motto), &"", 100.0))
		left.add_child(section("Guild Info"))
		var info := TextEdit.new()
		info.text = String(_form.info)
		info.placeholder_text = "Tell other heroes about your guild: who you are, what you hunt, who may join. (Shown on your guild's page and in Showcases.)"
		info.custom_minimum_size = Vector2(0, 120)
		info.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
		info.text_changed.connect(func() -> void: _form.info = info.text)
		left.add_child(info)
	left.add_child(section("Banner"))
	var st := _form_style()
	var swatches := hbox(6)
	left.add_child(swatches)
	for c in GuildBannerArt.FIELDS:
		var sw := Button.new()
		sw.custom_minimum_size = Vector2(36, 36)
		sw.focus_mode = Control.FOCUS_NONE
		var sbx := StyleBoxFlat.new()
		sbx.bg_color = c
		sbx.set_corner_radius_all(4)
		sbx.set_border_width_all(3 if (c as Color).to_html(false) == String(st.field) else 1)
		sbx.border_color = GOLDEN if (c as Color).to_html(false) == String(st.field) else Color(0, 0, 0, 0.6)
		for k in ["normal", "hover", "pressed"]:
			sw.add_theme_stylebox_override(k, sbx)
		var col: Color = c
		sw.pressed.connect(func() -> void:
			_form.style["field"] = col.to_html(false)
			_apply_style(hero, editing))
		swatches.add_child(sw)
	var opts := hbox(10)
	left.add_child(opts)
	opts.add_child(_cycle("Crest: %s" % String(st.crest).capitalize(), func() -> void: _cycle_key("crest", GuildBannerArt.CRESTS, hero, editing)))
	opts.add_child(_cycle("Pattern: %s" % String(st.division).capitalize(), func() -> void: _cycle_key("division", GuildBannerArt.DIVISIONS, hero, editing)))
	opts.add_child(_cycle("Trim: %s" % ("Gold" if int(st.metal) == 0 else "Silver"), func() -> void:
		_form.style["metal"] = 1 - int(_form_style().metal)
		_apply_style(hero, editing)))
	left.add_child(_text("You can also upload a picture of your own for the banner after founding (Overview > Rename & Upload Banner).", 15, UITheme.TEXT_DIM))
	var right := vbox(10)
	cols.add_child(right)
	preview.texture = GuildBannerArt.texture(st)
	preview.custom_minimum_size = Vector2(280, 420)
	preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	right.add_child(preview)
	var row := hbox(12)
	_content.add_child(row)
	if editing:
		row.add_child(_btn("Save Banner Design", func() -> void:
			_say(OwnGuild.set_details(hero, String(hero.own_guild.motto), String(hero.own_guild.get("info", "")), _form_style()), "Banner design saved")
			page = "overview"
			refresh(), &"PrimaryButton", 280.0))
		row.add_child(_btn("Back", func() -> void:
			page = "overview"
			refresh(), &"", 140.0))
	else:
		row.add_child(_btn("Found the Guild (%d gold)" % DataGuildPassives.FOUND_FEE, func() -> void:
			var err := OwnGuild.found_error(hero, String(_form.name))
			if err != "":
				_say(err)
				return
			Game.ui_root.ask("Found %s" % GuildRules.clean_alias(String(_form.name)), "Pay %d gold for the charter and become the Guildmaster of %s?%s" % [DataGuildPassives.FOUND_FEE,
					GuildRules.clean_alias(String(_form.name)), ("\nYou will leave %s (your tier stays yours)." % GuildRules.display_name(hero)) if hero.guild != &"" else ""],
				func() -> void:
					var e2 := OwnGuild.found(hero, String(_form.name), String(_form.motto), String(_form.info), _form_style())
					if e2 != "":
						_say(e2)
						return
					page = "overview"
					_form = {"name": "", "motto": "", "info": "", "style": {}}
					Game.ui_root.show_tier_award(hero.tier, "You founded %s" % hero.own_guild.name)
					refresh(), "Found the Guild"), &"PrimaryButton", 360.0, "" if hero.inventory.gold >= DataGuildPassives.FOUND_FEE else "The charter costs %d gold" % DataGuildPassives.FOUND_FEE))

func _cycle(text: String, cb: Callable) -> Button:
	var b := _btn(text, cb, &"", 200.0)
	return b

func _cycle_key(key: String, values: Array, hero: HeroData, editing: bool) -> void:
	var st := _form_style()
	var i := values.find(String(st[key]))
	_form.style[key] = values[(i + 1) % values.size()]
	_apply_style(hero, editing)

func _apply_style(_hero: HeroData, _editing: bool) -> void:
	Audio.play_ui(&"ui_click")
	refresh()
