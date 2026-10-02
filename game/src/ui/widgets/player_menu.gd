class_name PlayerMenu
extends Control
## bh-027: what you can do with another player — click their hero (or their party frame) and pick: Whisper, Trade,
## Invite to Guild, Showcase or Ping. A click anywhere else (or Escape) closes it.

var peer := 0
var _panel: PanelContainer

static func open_for(parent: Control, p_peer: int, at: Vector2) -> PlayerMenu:
	for n in parent.get_children():
		if n is PlayerMenu:
			n.queue_free()
	var m := PlayerMenu.new()
	m.peer = p_peer
	parent.add_child(m)
	m._build(at)
	return m

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed:
		queue_free()
		accept_event()

func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed(&"pause"):
		queue_free()
		get_viewport().set_input_as_handled()

func _build(at: Vector2) -> void:
	var info: Dictionary = Net.peers.get(peer, {})
	_panel = PanelContainer.new()
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.07, 0.055, 0.045, 0.97)
	st.set_border_width_all(2)
	st.border_color = Net.player_color(peer).darkened(0.1)
	st.set_corner_radius_all(5)
	st.set_content_margin_all(12)
	st.shadow_color = Color(0, 0, 0, 0.6)
	st.shadow_size = 10
	_panel.add_theme_stylebox_override("panel", st)
	add_child(_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	_panel.add_child(v)
	var cls := DB.class_def(StringName(info.get("cls", "knight")))
	# bh-030: the player's own picture beside their name
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	v.add_child(head)
	var pic := TextureRect.new()
	pic.texture = ProfilePicture.peer_portrait(peer, String(info.get("cls", "knight")))
	pic.custom_minimum_size = Vector2(72, 72)
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	head.add_child(pic)
	var nv := VBoxContainer.new()
	nv.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(nv)
	nv.add_child(UITheme.label("◆ %s" % info.get("name", "Hero"), 22, Net.player_color(peer).lightened(0.3), UITheme.body_bold()))
	nv.add_child(UITheme.label("Level %d %s" % [int(info.get("level", 1)), cls.display_name if cls else "Hero"], 15, UITheme.TEXT_DIM, UITheme.body_font()))
	var g: Dictionary = info.get("guild", {})
	if not g.is_empty():
		v.add_child(UITheme.label("⚑ %s" % g.get("name", "Guild"), 15, Color(String(g.get("color", "c9a24a"))).lightened(0.3), UITheme.body_bold()))
	v.add_child(HSeparator.new())
	var h := Game.hero
	_entry(v, "Whisper", "Send a private message.", "", func() -> void:
		if Game.ui_root and Game.ui_root.chat:
			Game.ui_root.chat.open()
			Game.ui_root.chat.prefill("/w %s " % info.get("name", "")))
	_entry(v, "Trade", "Swap items and gold.", Net.trade_error(peer), func() -> void: Net.trade_prompt(peer))
	_entry(v, "Invite to Guild", "Ask them to join %s." % (h.own_guild.name if OwnGuild.has(h) else "your guild"), Net.guild_invite_error(peer),
		func() -> void: Net.guild_invite(peer))
	_entry(v, "Showcase", "Ask to see each other's equipped gear and weapons.", Net.showcase_error(peer), func() -> void: Net.request_showcase(peer))
	_entry(v, "Ping", "Mark where they stand for everyone.", "", func() -> void:
		var av := Net.avatar(peer)
		if av and is_instance_valid(av):
			Net.ping(av.global_position + Vector3.UP * 0.2))
	_panel.reset_size()
	var vp := get_viewport_rect().size
	var sz := _panel.get_combined_minimum_size()
	_panel.position = Vector2(clampf(at.x + 12.0, 8.0, vp.x - sz.x - 8.0), clampf(at.y - 20.0, 8.0, vp.y - sz.y - 8.0))
	Audio.play_ui(&"ui_open", -6.0)

func _entry(v: VBoxContainer, text: String, tip: String, err: String, cb: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.custom_minimum_size = Vector2(250, 56 if Settings.touch_mode else 38)
	b.add_theme_font_size_override("font_size", 19)
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = err if err != "" else tip
	if err != "":
		b.modulate = Color(1, 1, 1, 0.6)     # still clickable: the action itself says why it cannot happen now
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		queue_free()
		cb.call())
	v.add_child(b)
