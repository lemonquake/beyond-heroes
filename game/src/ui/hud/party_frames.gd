class_name PartyFrames
extends VBoxContainer
## HUD frames for the other players in a multiplayer party (bh-011), under the Tempo frames: class portrait, name in
## their player colour, level and class, HP bar, their ping, and where they are ("Fallen · revive them", "In Olivar").
## Clicking the host's frame (as a client) regroups you at the host's side. Hidden when playing alone.

const W := 300.0

var _rows := {}        # peer id -> {root, name, sub, hp, por}
var _t := 0.0
var _summon_btn: Button

func _init() -> void:
	add_theme_constant_override("separation", 6)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	Net.peers_changed.connect(_rebuild)
	Net.state_changed.connect(_rebuild)
	_rebuild()

func _others() -> Array:
	var ids := []
	for id in Net.peers:
		if int(id) != Net.my_id():
			ids.append(int(id))
	ids.sort()
	return ids

func _rebuild() -> void:
	for c in get_children():
		c.queue_free()
	_rows.clear()
	_summon_btn = null
	if not Net.is_active():
		visible = false
		return
	visible = true
	var ids := _others()
	if ids.is_empty():
		var p := PanelContainer.new()
		p.theme_type_variation = &"GlassPanel"
		p.custom_minimum_size = Vector2(W, 0)
		var l := UITheme.label("Hosting · waiting for friends to join" if Net.is_host() else "Connecting…", 15, UITheme.TEXT_DIM, UITheme.body_font())
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		p.add_child(l)
		add_child(p)
		return
	for id in ids:
		add_child(_row(id))
	_summon_btn = null
	if Net.is_host():
		# bh-015: the host calls everyone who is away to their side; each player chooses Go or Stay
		_summon_btn = Button.new()
		_summon_btn.text = "Summon Party  (%s)" % Settings.binding_text(&"summon_party")
		_summon_btn.theme_type_variation = &"PrimaryButton"
		_summon_btn.custom_minimum_size = Vector2(W, 36)
		_summon_btn.focus_mode = Control.FOCUS_NONE
		_summon_btn.add_theme_font_size_override("font_size", 16)
		_summon_btn.pressed.connect(func() -> void: Net.summon_party())
		TooltipLayer.attach(_summon_btn, func() -> Control: return Tips.text("Ask everyone who is away to come to your side. Each of them chooses Go or Stay."))
		add_child(_summon_btn)

func _row(id: int) -> Control:
	var info: Dictionary = Net.peers.get(id, {})
	var col := Net.player_color(id)
	var p := PanelContainer.new()
	p.theme_type_variation = &"GlassPanel"
	p.custom_minimum_size = Vector2(W, 0)
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	p.add_child(h)
	var por := TextureRect.new()
	por.texture = UIArt.portrait(String(info.get("cls", "knight")))
	por.custom_minimum_size = Vector2(44, 44)
	por.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	por.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	h.add_child(por)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 1)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var nh := HBoxContainer.new()
	v.add_child(nh)
	var nm := UITheme.label("◆ %s%s" % [info.get("name", "Hero"), "  (Host)" if id == 1 else ""], 16, col.lightened(0.25), UITheme.body_bold())
	nm.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	nm.add_theme_constant_override("outline_size", 4)
	nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nm.clip_text = true
	nh.add_child(nm)
	var ping := UITheme.label("", 13, UITheme.TEXT_DIM, UITheme.number_font())
	ping.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	ping.add_theme_constant_override("outline_size", 3)
	nh.add_child(ping)
	var hp := ArtBar.new("hud/bar_frame_target.png", Color(0.3, 0.88, 0.4), 18.0)
	hp.custom_minimum_size = Vector2(W - 64.0, 18)
	hp.text_size = 11
	v.add_child(hp)
	var sub := UITheme.label("", 13, UITheme.TEXT_DIM, UITheme.body_font())
	sub.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	sub.add_theme_constant_override("outline_size", 3)
	v.add_child(sub)
	TooltipLayer.attach(p, func() -> Control: return _tip(id))
	p.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT and id == 1 and Net.is_client():
			Net.regroup())
	_rows[id] = {"root": p, "name": nm, "sub": sub, "hp": hp, "ping": ping}
	return p

func _tip(id: int) -> Control:
	var info: Dictionary = Net.peers.get(id, {})
	var cls := DB.class_def(StringName(info.get("cls", "knight")))
	var lines := ["Level %d %s · playing on %s" % [int(info.get("level", 1)), cls.display_name if cls else "Hero", info.get("device", "PC")]]
	var st: Dictionary = Net.status.get(id, {})
	if not st.is_empty():
		lines.append("In %s" % Net.place_name(StringName(st.map)))
	var av := Net.avatar(id)
	if av and not av.alive:
		lines.append("Fallen. Stand beside them and press %s to revive them." % Settings.binding_text(&"interact"))
	if id == 1 and Net.is_client():
		lines.append("Click to regroup at their side.")
	return Tips.text("\n".join(lines), String(info.get("name", "Hero")))

func _process(delta: float) -> void:
	_t -= delta
	if _t > 0.0 or not visible:
		return
	_t = 0.12
	if _others().size() != _rows.size() or not _rows.is_empty() and (_summon_btn == null) == Net.is_host():
		_rebuild()
		return
	var here := String(Game.current_map_id)
	for id in _rows:
		var r: Dictionary = _rows[id]
		var info: Dictionary = Net.peers.get(id, {})
		var cls := DB.class_def(StringName(info.get("cls", "knight")))
		var av := Net.avatar(id)
		var bar := r.hp as ArtBar
		var sub := r.sub as Label
		var root := r.root as Control
		var ms := Net.ping_ms(id)
		(r.ping as Label).text = ("%d ms" % ms) if ms > 0 else ""
		(r.ping as Label).add_theme_color_override("font_color", UITheme.BAD if ms > 250 else (Color(1.0, 0.8, 0.35) if ms > 120 else Color(0.55, 0.9, 0.55)))
		if av:
			var f := clampf(av.hp / maxf(1.0, av.max_hp()), 0.0, 1.0)
			bar.set_ratio(f if av.alive else 0.0)
			bar.text = "%d / %d" % [ceili(av.hp), roundi(av.max_hp())] if av.alive else ""
			bar.fill_color = Color(0.92, 0.32, 0.25) if f < 0.3 else Color(0.3, 0.88, 0.4)
			if av.alive:
				var d := (Game.player as Node3D).global_position.distance_to(av.global_position) if Game.player else 0.0
				sub.text = "Level %d %s · %d m away" % [av.level, cls.display_name if cls else "", roundi(d)]
				sub.add_theme_color_override("font_color", UITheme.TEXT_DIM)
				root.modulate = Color.WHITE
			else:
				sub.text = "Fallen · stand beside them and press %s" % Settings.binding_text(&"interact")
				sub.add_theme_color_override("font_color", UITheme.BAD)
				root.modulate = Color(1.0, 0.8, 0.8)
		else:
			# elsewhere on the island (bh-015): their last snapshot still carries HP and level
			var st: Dictionary = Net.status.get(id, {})
			var m := String(st.get("map", info.get("map", "")))
			if not st.is_empty():
				var f2 := clampf(float(st.hp) / maxf(1.0, float(st.mhp)), 0.0, 1.0)
				bar.set_ratio(f2 if st.alive else 0.0)
				bar.text = "%d / %d" % [ceili(float(st.hp)), roundi(float(st.mhp))] if st.alive else ""
				bar.fill_color = Color(0.92, 0.32, 0.25) if f2 < 0.3 else Color(0.3, 0.88, 0.4)
			else:
				bar.set_ratio(0.0)
				bar.text = ""
			var lv := int(st.get("lvl", info.get("level", 1)))
			if m == "" or m == here:
				sub.text = "Level %d %s · travelling…" % [lv, cls.display_name if cls else ""]
			else:
				sub.text = "Level %d · in %s%s" % [lv, Net.place_name(StringName(m)), "" if st.get("alive", true) else " · fallen"]
			sub.add_theme_color_override("font_color", UITheme.TEXT_DIM)
			root.modulate = Color(0.85, 0.85, 0.92)
	if _summon_btn:
		_summon_btn.visible = Net.is_host() and not _rows.is_empty()
