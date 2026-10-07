class_name TempoFrames
extends VBoxContainer
## HUD party frames for the hero's Tempos, under the hero's portrait: class crest, name, what the spirit is doing,
## HP and mana bars, and "Fallen" when it is down. Always visible while any Tempo is bound (hover for details;
## click to open the Tempo window).

const W := 300.0

var _rows := {}        # uid -> {root, name, state, hp, mp, icon}
var _t := 0.0

func _init() -> void:
	add_theme_constant_override("separation", 6)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	Events.tempo_changed.connect(func(_u): _rebuild())
	Events.tempo_spawned.connect(func(_a): _rebuild())
	Events.map_loaded.connect(func(_m): _rebuild())
	_rebuild()

func _rebuild() -> void:
	for c in get_children():
		c.queue_free()
	_rows.clear()
	var hero := Game.hero
	if hero == null:
		return
	if not hero.tempos.is_empty():
		add_child(TempoCommandBar.make(true))      # bh-041: Aggro / Defend / Passive
	for t in hero.tempos:
		add_child(_row(t))

func _row(t: TempoData) -> Control:
	var p := PanelContainer.new()
	p.theme_type_variation = &"GlassPanel"
	p.custom_minimum_size = Vector2(W, 0)
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	p.add_child(h)
	var ic := TextureRect.new()
	ic.texture = DataTempos.class_icon(t.class_id)
	ic.custom_minimum_size = Vector2(40, 40)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.modulate = t.class_def().get("color", Color.WHITE)
	h.add_child(ic)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 1)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var nh := HBoxContainer.new()
	v.add_child(nh)
	var nm := UITheme.label(t.tempo_name, 16, UITheme.PARCHMENT, UITheme.body_bold())
	nm.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	nm.add_theme_constant_override("outline_size", 4)
	nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nh.add_child(nm)
	var st := UITheme.label("", 13, UITheme.TEXT_DIM, UITheme.body_font())
	st.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	st.add_theme_constant_override("outline_size", 3)
	nh.add_child(st)
	var hp := ArtBar.new("hud/bar_frame_target.png", Color(0.3, 0.88, 0.74), 20.0)
	hp.custom_minimum_size = Vector2(W - 60.0, 20)
	hp.text_size = 12
	v.add_child(hp)
	var mp := ArtBar.new("hud/bar_frame_target.png", Color(0.25, 0.48, 0.98), 14.0)
	mp.custom_minimum_size = Vector2(W - 60.0, 14)
	mp.text_size = 10
	v.add_child(mp)
	var uid := t.uid
	TooltipLayer.attach(p, func() -> Control: return _tip(uid))
	p.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT and Game.ui_root:
			var w := Game.ui_root.window(&"tempos") as TempoWindow
			if w:
				w.current = TempoRules.find(Game.hero, uid)
			Game.ui_root.open(&"tempos"))
	_rows[t.uid] = {"root": p, "state": st, "hp": hp, "mp": mp, "icon": ic, "name": nm}
	return p

func _tip(uid: int) -> Control:
	var t := TempoRules.find(Game.hero, uid) if Game.hero else null
	if t == null:
		return null
	var skills: Array = t.skills.map(func(s): return String(DataTempos.skill(s).get("name", s)))
	return Tips.text("%s — %s, %s spirit (%s)\nSkills: %s\n%s" % [t.full_name(), t.class_name_text(), t.grade_name(), t.trait_def().get("name", ""), ", ".join(skills),
		"Fallen. Veyra Ashgrave at the Shrine of the Fallen can call it back." if t.fallen else "Click to open the Tempo window (%s)." % Settings.binding_text(&"tempos")])

func _process(delta: float) -> void:
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.08
	var hero := Game.hero
	if hero == null:
		return
	if hero.tempos.size() != _rows.size():
		_rebuild()
		return
	for t in hero.tempos:
		var r: Dictionary = _rows.get(t.uid, {})
		if r.is_empty():
			_rebuild()
			return
		var a := TempoParty.actor_for(t.uid)
		var fh := 0.0
		var fm := 0.0
		var hp_txt := ""
		var mp_txt := ""
		if a and a.alive:
			fh = a.hp / maxf(1.0, a.max_hp())
			fm = a.mana / maxf(1.0, a.max_mana())
			hp_txt = "%d / %d" % [ceili(a.hp), roundi(a.max_hp())]
			mp_txt = "%d / %d" % [floori(a.mana), roundi(a.max_mana())]
			(r.state as Label).text = a.mode_name()
			(r.state as Label).add_theme_color_override("font_color", Color(1.0, 0.55, 0.4) if a.mode == Tempo.Mode.RETREAT else UITheme.TEXT_DIM)
		elif t.fallen:
			(r.state as Label).text = "Fallen"
			(r.state as Label).add_theme_color_override("font_color", UITheme.BAD)
		else:
			fh = t.hp_frac
			fm = t.mana_frac
			(r.state as Label).text = ""
		(r.hp as ArtBar).set_ratio(fh)
		(r.hp as ArtBar).text = hp_txt
		(r.hp as ArtBar).fill_color = Color(0.92, 0.32, 0.25) if fh < 0.3 else Color(0.3, 0.88, 0.74)
		(r.mp as ArtBar).set_ratio(fm)
		(r.mp as ArtBar).text = mp_txt
		(r.root as Control).modulate = Color(0.55, 0.55, 0.6) if t.fallen else Color.WHITE
