class_name CharacterWindow
extends UIWindow
## Character (C). The hero in 3D, class, level and experience; the six attributes with point allocation (preview the
## gain before committing); every derived statistic grouped into Offense / Defense / Resistances / Utility. Hovering any
## number explains what it does and where its value comes from (DerivedStats.explain, the same data the game uses).

const GROUPS := [
	["Offense", [&"weapon_damage_range", &"attacks_per_second", &"attack_speed", &"cast_speed", &"crit_chance", &"crit_damage",
		&"accuracy", &"accuracy_chance", &"phys_damage", &"magic_damage", &"elemental_damage", &"pen_armor", &"pen_elemental",
		&"impact_strength", &"stagger_power", &"status_power", &"life_leech", &"mana_leech", &"skill_levels"]],
	["Defense", [&"max_hp", &"hp_regen", &"defense", &"physical_armor_dr", &"evasion", &"evade_chance", &"block_chance",
		&"block_strength", &"parry_window", &"poise", &"knockback_res", &"status_res", &"damage_taken"]],
	["Resistances", []],
	["Magic & Utility", [&"max_mana", &"mana_regen", &"mana_cost_reduction", &"cdr", &"healing", &"buff_effect", &"move_speed",
		&"dodge_cooldown", &"dodge_distance", &"projectile_speed", &"magic_find", &"gold_find", &"xp_gain"]],
]

var hero: HeroData
var preview: CharacterPreview
var _class_label: Label
var _level_label: Label
var _xp_bar: ArtBar
var _xp_text: Label
var _points: Label
var _attr_rows := {}              # attr -> {value: Label, plus: Button, pending: Label}
var _pending := {}                # attr -> points not yet committed
var _apply: Button
var _reset: Button
var _stats_box: VBoxContainer
var _stats: DerivedStats

func _init() -> void:
	super._init("Character", Vector2(1560, 900))

func _build() -> void:
	var row := hbox(22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(row)
	# left: portrait column
	var left := vbox(10)
	left.custom_minimum_size = Vector2(380, 0)
	row.add_child(left)
	var pw := inset(Vector2(380, 540))
	left.add_child(pw)
	preview = CharacterPreview.new(Vector2i(720, 1040))
	preview.custom_minimum_size = Vector2(350, 520)
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
	# middle: attributes
	var mid := vbox(8)
	mid.custom_minimum_size = Vector2(420, 0)
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
	var note := UITheme.label("Hover an attribute to see what it improves. Points are only spent when you apply them.", 14, UITheme.TEXT_MUTED, UITheme.body_font())
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mid.add_child(note)
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
	h.add_child(plus)
	p.mouse_filter = Control.MOUSE_FILTER_PASS
	TooltipLayer.attach(p, func() -> Control: return _attr_tip(a))
	_attr_rows[a] = {"value": v, "plus": plus, "minus": minus, "pending": pend}
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
	var total := 0
	for k in _pending:
		total += int(_pending[k])
	var cur := int(_pending.get(a, 0))
	if d > 0 and total >= hero.progress.free_points:
		return
	if d < 0 and cur <= 0:
		return
	_pending[a] = cur + d
	Audio.play_ui(&"ui_click")
	_refresh_attrs()

func _commit() -> void:
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
	_class_label.text = "%s — %s" % [hero.hero_name, hero.cls.display_name]
	_level_label.text = "Level %d" % hero.progress.level
	var need := XpCurve.xp_to_next(hero.progress.level)
	_xp_bar.set_ratio(float(hero.progress.xp) / float(maxi(1, need)) if need > 0 else 1.0, true)
	_xp_text.text = "%d / %d experience" % [hero.progress.xp, need] if need > 0 else "Maximum level"
	_refresh_attrs()

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
