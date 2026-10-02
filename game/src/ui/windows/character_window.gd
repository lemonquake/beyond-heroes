class_name CharacterWindow
extends UIWindow
## Character (C). The hero in 3D, class, level and experience; the six attributes with point allocation (preview the
## gain before committing); every derived statistic grouped into Offense / Defense / Resistances / Utility. Hovering any
## number explains what it does and where its value comes from (DerivedStats.explain, the same data the game uses).

const GROUPS := [
	["Offense", [&"weapon_damage_range", &"attacks_per_second", &"attack_speed", &"cast_speed", &"crit_chance", &"crit_damage",
		&"accuracy", &"accuracy_chance", &"physical_attack", &"spell_power", &"phys_damage", &"magic_damage", &"elemental_damage", &"pen_armor", &"pen_elemental",
		&"impact_strength", &"stagger_power", &"status_power", &"life_leech", &"mana_leech", &"skill_levels"]],
	["Defense", [&"max_hp", &"hp_regen", &"defense", &"physical_armor_dr", &"evasion", &"evade_chance", &"graze_chance", &"block_chance",
		&"block_strength", &"parry_window", &"poise", &"knockback_res", &"status_res", &"damage_taken"]],
	["Resistances", []],
	["Magic & Utility", [&"max_mana", &"mana_regen", &"mana_cost_reduction", &"cdr", &"healing", &"buff_effect", &"move_speed",
		&"carry_weight", &"carry_capacity", &"load", &"dodge_cooldown", &"dodge_distance", &"projectile_speed", &"magic_find", &"gold_find", &"xp_gain",
		&"ember_find", &"potion_power", &"hp_on_kill", &"mana_on_kill", &"thorns", &"elite_damage", &"tempo_damage"]],
]

var hero: HeroData
var preview: CharacterPreview
var _class_label: Label
var _level_label: Label
var _xp_bar: ArtBar
var _xp_text: Label
var _tier_emblem: TextureRect
var _tier_text: Label
var _guild_text: Label
var _guild_crest: TextureRect
var _promotion_text: Label
var _promotion_scroll: ScrollContainer
var _track_btn: Button
var _points: Label
var _attr_rows := {}              # attr -> {value: Label, plus: Button, pending: Label}
var _pending := {}                # attr -> points not yet committed
var _apply: Button
var _reset: Button
var _stats_box: VBoxContainer
var _stats: DerivedStats
var _held_attr: StringName = &""
var _hold_wait := 0.0

func _init() -> void:
	super._init("Character", Vector2(1560, 900))

var _pic: TextureRect
var _pic_clear: Button
var _pic_dialog: FileDialog

## bh-030: choose a picture file (any PNG, JPG, WebP, BMP or TGA; dropping a file on the window works too).
func _pick_picture() -> void:
	if _pic_dialog == null:
		_pic_dialog = FileDialog.new()
		_pic_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
		_pic_dialog.access = FileDialog.ACCESS_FILESYSTEM
		_pic_dialog.use_native_dialog = true
		_pic_dialog.title = "Choose a profile picture"
		_pic_dialog.filters = PackedStringArray(GuildCustomWindow.PICTURE_FILTERS)
		_pic_dialog.file_selected.connect(_on_picture_picked)
		add_child(_pic_dialog)
	_pic_dialog.popup_centered_ratio(0.7)

func _on_picture_picked(path: String) -> void:
	if hero == null:
		return
	var img := GuildCustomWindow.load_picture(path)
	var err := ProfilePicture.set_picture(hero, img) if img != null else "That file could not be read as a picture."
	Events.notify.emit(err if err != "" else "Profile picture updated.", &"error" if err != "" else &"info")
	refresh()

func _build() -> void:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	# left: portrait column
	var left := vbox(10)
	left.custom_minimum_size = Vector2(380, 0)
	row.add_child(left)
	var pw := inset(Vector2(380, 470))
	left.add_child(pw)
	preview = CharacterPreview.new(Vector2i(720, 1040))
	preview.custom_minimum_size = Vector2(320, 450)
	pw.add_child(preview)
	_class_label = UITheme.title("", 26, UITheme.GOLD)
	_class_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	left.add_child(_class_label)
	_level_label = UITheme.label("", 18, UITheme.PARCHMENT, UITheme.body_bold())
	_level_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	left.add_child(_level_label)
	_xp_bar = ArtBar.new("hud/bar_frame_xp.png", Color(0.95, 0.75, 0.3), 20.0)
	left.add_child(_xp_bar)
	_xp_text = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.number_font())
	_xp_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	left.add_child(_xp_text)
	# bh-023: the hero's look can be changed at any time; bh-030: and their profile picture
	var prow := hbox(10)
	prow.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(prow)
	var pframe := PanelContainer.new()
	pframe.theme_type_variation = &"GlassPanel"
	prow.add_child(pframe)
	_pic = TextureRect.new()
	_pic.custom_minimum_size = Vector2(64, 64)
	_pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	pframe.add_child(_pic)
	TooltipLayer.attach(pframe, func() -> Control: return Tips.text("Your profile picture: on your HUD, and in multiplayer on every player's party frames and menus.", "Profile Picture"))
	var pbtns := vbox(4)
	prow.add_child(pbtns)
	var restyle := button("Change Look", func() -> void: Game.ui_root.open_creator(), &"", 200.0)
	TooltipLayer.attach(restyle, func() -> Control: return Tips.text(
		"Reshape your hero: face, hair, skin, build and more. It costs nothing and changes no statistics.", "Change Look"))
	pbtns.add_child(restyle)
	var ph := hbox(4)
	pbtns.add_child(ph)
	ph.add_child(button("Picture...", _pick_picture, &"", 120.0))
	_pic_clear = button("Remove", func() -> void:
		ProfilePicture.clear(hero)
		refresh(), &"", 76.0)
	ph.add_child(_pic_clear)
	Events.profile_picture_changed.connect(func(peer: int) -> void: if peer == 0 and visible: refresh())
	var win := get_window()
	if win:
		win.files_dropped.connect(func(files: PackedStringArray) -> void:
			if visible and not files.is_empty():
				_on_picture_picked(files[0]))
	# hero tier and guild (docs/LORE.md §5)
	var tr := hbox(10)
	tr.alignment = BoxContainer.ALIGNMENT_CENTER
	left.add_child(tr)
	_tier_emblem = TextureRect.new()
	_tier_emblem.custom_minimum_size = Vector2(64, 64)
	_tier_emblem.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tier_emblem.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.add_child(_tier_emblem)
	var tv := vbox(0)
	tr.add_child(tv)
	_tier_text = UITheme.label("", 19, UITheme.GOLD, UITheme.body_bold())
	tv.add_child(_tier_text)
	_guild_text = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	tv.add_child(_guild_text)
	_guild_crest = TextureRect.new()
	_guild_crest.custom_minimum_size = Vector2(48, 48)
	_guild_crest.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_guild_crest.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.add_child(_guild_crest)
	TooltipLayer.attach(tr, func() -> Control: return Tips.text(_guild_tip(), "Tier and guild") if hero else null)
	tr.mouse_filter = Control.MOUSE_FILTER_STOP
	tr.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	tr.gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT and GuildRules.can_customise(hero):
			Game.ui_root.open(&"guild_custom")
		elif ev is InputEventScreenTouch and ev.pressed and GuildRules.can_customise(hero):
			Game.ui_root.open(&"guild_custom"))
	# middle: attributes
	var mid := vbox(8)
	mid.custom_minimum_size = Vector2(500, 0)
	row.add_child(mid)
	mid.add_child(section("Attributes"))
	_points = UITheme.label("", 17, UITheme.GOLD, UITheme.body_bold())
	mid.add_child(_points)
	for a in BH.ATTRIBUTES:
		mid.add_child(_attr_row(a))
	var ab := hbox(10)
	mid.add_child(ab)
	_reset = button("Clear", func() -> void:
		_pending.clear()
		refresh(), &"", 140.0)
	ab.add_child(_reset)
	_apply = button("Apply Points", _commit, &"PrimaryButton", 200.0)
	ab.add_child(_apply)
	var note := UITheme.label("Hold + to keep adding points. All assigns remaining points to that attribute. Apply Points saves your choices.", 16, UITheme.TEXT_MUTED, UITheme.body_font())
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mid.add_child(note)
	mid.add_child(section("Next Class Rank"))
	# Long promotion checklists must scroll instead of increasing the window's minimum height.
	_promotion_scroll = ScrollContainer.new()
	_promotion_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_promotion_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_promotion_scroll.custom_minimum_size.y = 80
	mid.add_child(_promotion_scroll)
	_promotion_text = UITheme.label("", 17, UITheme.TEXT, UITheme.body_font())
	_promotion_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_promotion_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_promotion_scroll.add_child(_promotion_text)
	# bh-033: the optional HUD checklist for the next rank (the player's choice is kept per hero)
	_track_btn = button("Track Rank Up", func() -> void:
		if hero:
			hero.rank_tracker = "expanded" if hero.rank_tracker == "hidden" else "hidden"
			Events.rank_tracker_changed.emit()
			refresh(), &"", 240.0)
	mid.add_child(_track_btn)
	# right: derived stats (scrolling)
	var right := vbox(6)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(right)
	right.add_child(section("Statistics"))
	var sw := inset()
	sw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(sw)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sw.add_child(scroll)
	_stats_box = vbox(2)
	_stats_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_stats_box)

func _attr_row(a: StringName) -> Control:
	var p := PanelContainer.new()
	p.theme_type_variation = &"InsetPanel"
	var h := hbox(10)
	p.add_child(h)
	var ic := TextureRect.new()
	ic.texture = UIArt.attribute_icon(a)
	ic.custom_minimum_size = Vector2(38, 38)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	h.add_child(ic)
	var n := UITheme.label(BH.ATTRIBUTE_NAMES[a], 19, UITheme.PARCHMENT, UITheme.title_font())
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(n)
	var pend := UITheme.label("", 17, UITheme.GOOD, UITheme.number_font())
	h.add_child(pend)
	var v := UITheme.label("", 22, UITheme.GOLD, UITheme.number_font())
	v.custom_minimum_size = Vector2(54, 0)
	v.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	h.add_child(v)
	var minus := icon_button("minus", "", func() -> void: _change(a, -1), 20.0)
	h.add_child(minus)
	var plus := icon_button("plus", "", func() -> void: _change(a, 1), 20.0)
	plus.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	plus.button_down.connect(func() -> void:
		_held_attr = a
		_hold_wait = 0.4)
	plus.button_up.connect(_stop_hold)
	plus.mouse_exited.connect(_stop_hold)
	h.add_child(plus)
	var all := button("All", func() -> void: _allocate_all(a), &"", 64.0)
	all.tooltip_text = "Assign all remaining points to %s" % BH.ATTRIBUTE_NAMES[a]
	h.add_child(all)
	p.mouse_filter = Control.MOUSE_FILTER_PASS
	TooltipLayer.attach(p, func() -> Control: return _attr_tip(a))
	_attr_rows[a] = {"value": v, "plus": plus, "minus": minus, "all": all, "pending": pend}
	return p

func _attr_tip(a: StringName) -> Control:
	var f := Tips.frame(380.0)
	var v: VBoxContainer = f[1]
	v.add_child(Tips.lbl("%s  %d" % [BH.ATTRIBUTE_NAMES[a], roundi(_stats.get_stat(a)) if _stats else 0], 20, UITheme.GOLD, UITheme.title_font()))
	v.add_child(Tips.lbl(StatDefs.desc_of(a), 15, UITheme.TEXT))
	var lines: PackedStringArray = _stats.explain.get(a, PackedStringArray()) if _stats else PackedStringArray()
	if not lines.is_empty():
		v.add_child(Tips.rule())
		for l in lines:
			v.add_child(Tips.lbl(l, 14, UITheme.TEXT_DIM))
	# what one more point would change, measured with the real calculator
	if hero:
		var base := hero.progress.base_attributes()
		base[a] = int(base[a]) + 1
		var more := StatCalculator.compute(hero.cls, hero.progress.level, base, hero.persistent_modifiers(), hero.equipment.loadout())
		var now := hero.compute_stats()
		var diffs := []
		for k in now.values:
			if k in BH.ATTRIBUTES:
				continue
			var d: float = more.get_stat(k) - now.get_stat(k)
			if absf(d) > 0.0001 and StatDefs.DEFS.has(k):
				diffs.append([k, d])
		if not diffs.is_empty():
			v.add_child(Tips.rule())
			v.add_child(Tips.lbl("One more point:", 14, UITheme.TEXT_MUTED, UITheme.body_bold()))
			for dd in diffs.slice(0, 9):
				var k: StringName = dd[0]
				var txt := StatDefs.format_value(k, dd[1])
				v.add_child(Tips.lbl("  +%s %s" % [txt.trim_prefix("x"), StatDefs.name_of(k)], 14, UITheme.GOOD))
	return f[0]

func _change(a: StringName, d: int) -> void:
	if hero == null:
		return
	var total := 0
	for k in _pending:
		total += int(_pending[k])
	var cur := int(_pending.get(a, 0))
	if d > 0 and total >= hero.progress.free_points:
		return
	if d < 0 and cur <= 0:
		return
	_pending[a] = cur + clampi(d, -cur, maxi(0, hero.progress.free_points - total))
	Audio.play_ui(&"ui_click")
	_refresh_attrs()

func _allocate_all(a: StringName) -> void:
	_stop_hold()
	if hero:
		_change(a, hero.progress.free_points)

func _stop_hold() -> void:
	_held_attr = &""

func _process(delta: float) -> void:
	if _held_attr == &"":
		return
	if not is_visible_in_tree() or not get_window().has_focus() or hero == null:
		_stop_hold()
		return
	var plus: Button = _attr_rows[_held_attr].plus
	if plus.disabled or not plus.is_pressed():
		_stop_hold()
		return
	_hold_wait -= delta
	if _hold_wait <= 0.0:
		_hold_wait = 0.08
		_change(_held_attr, 1)

func _commit() -> void:
	_stop_hold()
	for a in _pending:
		if int(_pending[a]) > 0:
			hero.progress.allocate(a, int(_pending[a]))
	_pending.clear()
	Audio.play_ui(&"level_up")
	refresh()

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	if not hero.stats_dirty.is_connected(_on_dirty):
		hero.stats_dirty.connect(_on_dirty)
	preview.show_class(hero.cls.id, hero)
	_pic.texture = ProfilePicture.portrait(hero)
	_pic_clear.disabled = hero.profile_pic.is_empty()
	_class_label.text = "%s — %s" % [hero.hero_name, hero.cls.display_name]
	_level_label.text = "Level %d" % hero.progress.level
	var need := XpCurve.xp_to_next(hero.progress.level)
	_xp_bar.set_ratio(float(hero.progress.xp) / float(maxi(1, need)) if need > 0 else 1.0, true)
	_xp_text.text = "%d / %d experience" % [hero.progress.xp, need] if need > 0 else "Maximum level"
	_tier_emblem.texture = UIArt.tex(DataGuilds.emblem_path(hero.tier))
	_tier_text.text = DataGuilds.tier_name(hero.tier)
	_tier_text.add_theme_color_override("font_color", DataGuilds.tier(hero.tier).color)
	var g := GuildRegistry.info(hero, hero.guild)
	_guild_text.text = GuildRules.display_name(hero) if not g.is_empty() else "No guild"
	_guild_crest.texture = (UIArt.tex(String(g.crest)) if g.has("crest") else GuildRegistry.banner(hero, hero.guild)) if not g.is_empty() else null
	# bh-033: one rank ahead, from the same rules that promote (no future ladder, no story spoilers)
	var guide := GuildRules.rank_guide(hero)
	var pl := PackedStringArray()
	if guide.state == "max":
		pl.append("You hold the highest rank.")
	else:
		pl.append("%s  ->  %s" % [DataGuilds.tier_name(hero.tier), String(guide.title)])
		pl.append("Ready to rank up: promotion happens automatically." if guide.ready else "Next: %s. %s" % [String(guide.next_action), String(guide.next_hint)])
		for st in guide.steps:
			var cnt := ""
			if int(st.need) > 1:
				cnt = " (%d / %d)" % [int(st.have) if st.key == "fee" else mini(int(st.have), int(st.need)), int(st.need)]
			pl.append("%s %s%s" % ["✓" if st.done else "○", String(st.label), cnt])
		pl.append(String(guide.note))
	_promotion_text.text = "\n".join(pl)
	_track_btn.text = "Track Rank Up" if hero.rank_tracker == "hidden" else "Stop Tracking"
	_track_btn.visible = guide.state != "max"
	_refresh_attrs()

func _guild_tip() -> String:
	var lines := PackedStringArray()
	if hero.guild == &"":
		lines.append("You are not registered with a guild. Join one at the Guild House in Malasugue, or found your own (%s), to become a Class E hero and equip Licensed gear." % Settings.binding_text(&"guild"))
	else:
		var g := GuildRegistry.info(hero, hero.guild)
		lines.append("%s — \"%s\"" % [GuildRules.display_name(hero), g.get("motto", "")])
		lines.append("Click the guild to rename it or change its banner." if GuildRules.can_customise(hero) else "Your Guildmaster names the guild and flies its banner.")
		for t in g.get("perk_text", []):
			lines.append("%s per tier step (now x%d)" % [t, hero.tier])
		for f in g.get("features", []):
			lines.append(f)
	lines.append("")
	for r in range(1, DataGuilds.MAX_RANK + 1):
		var t := DataGuilds.tier(r)
		var gate := int(t.gate)
		lines.append("%s Class %s — %s: level %d%s%s" % ["▶" if r == hero.tier else " ", t.letter, t.title, t.level,
			(", " + GuildRules.requirements_text(hero, r)) if r > 1 else "", (" · equips %s" % BH.rarity_name(gate)) if gate >= 0 else ""])
	return "\n".join(lines)

func _on_dirty() -> void:
	if visible:
		refresh()

func _live_stats() -> DerivedStats:
	var p := Game.player as Player
	if p and p.hero == hero and p.stats:
		p.ensure_stats()
		return p.stats
	return hero.compute_stats()

func _refresh_attrs() -> void:
	_stats = _live_stats()
	var total := 0
	for k in _pending:
		total += int(_pending[k])
	var free := hero.progress.free_points - total
	_points.text = "%d attribute points to spend" % free if hero.progress.free_points > 0 else "No attribute points to spend"
	for a in BH.ATTRIBUTES:
		var r: Dictionary = _attr_rows[a]
		var pend := int(_pending.get(a, 0))
		(r.value as Label).text = str(roundi(_stats.get_stat(a)) + pend)
		(r.pending as Label).text = "+%d" % pend if pend > 0 else ""
		(r.plus as Button).disabled = free <= 0
		(r.all as Button).disabled = free <= 0
		(r.minus as Button).disabled = pend <= 0
		(r.plus as Button).visible = hero.progress.free_points > 0
		(r.minus as Button).visible = hero.progress.free_points > 0
	_apply.disabled = total <= 0
	_reset.disabled = total <= 0
	_refresh_stats()

func _refresh_stats() -> void:
	for c in _stats_box.get_children():
		c.queue_free()
	var d := _stats
	for g in GROUPS:
		var title := UITheme.label(g[0], 18, UITheme.GOLD, UITheme.title_font())
		_stats_box.add_child(title)
		var keys: Array = g[1]
		if g[0] == "Resistances":
			keys = [&"phys_res"]
			for e in Elements.ELEMENTAL:
				keys.append(Elements.res_key(e))
		var grid := GridContainer.new()
		grid.columns = 2
		grid.add_theme_constant_override("h_separation", 12)
		grid.add_theme_constant_override("v_separation", 0)
		_stats_box.add_child(grid)
		for k in keys:
			var name := StatDefs.name_of(k)
			var val := ""
			if k == &"weapon_damage_range":
				name = "Weapon Damage"
				val = "%d – %d" % [roundi(d.get_stat(&"weapon_min")), roundi(d.get_stat(&"weapon_max"))]
			elif k == &"attacks_per_second":
				name = "Attacks per Second"
				val = "%.2f" % d.get_stat(k)
			elif not d.values.has(k):
				continue
			else:
				val = StatDefs.format_value(k, d.get_stat(k))
			var n := UITheme.label(name, 16, UITheme.TEXT, UITheme.body_font())
			n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			n.mouse_filter = Control.MOUSE_FILTER_PASS
			var col := UITheme.PARCHMENT
			if String(k).begins_with("res_") or k == &"phys_res":
				var e := Elements.from_key(StringName(String(k).substr(4))) if k != &"phys_res" else Elements.PHYSICAL
				col = Elements.color(e).lerp(UITheme.PARCHMENT, 0.35)
			var vl := UITheme.label(val, 16, col, UITheme.number_font())
			vl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			var key: StringName = k if k != &"weapon_damage_range" else &"weapon_min"
			var shown := val
			TooltipLayer.attach(n, func() -> Control: return Tips.stat(key, d, shown))
			grid.add_child(n)
			grid.add_child(vl)
		_stats_box.add_child(Tips.gap(6))
