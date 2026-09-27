class_name SettingsWindow
extends UIWindow
## Settings: VIDEO (resolution, window mode, VSync, frame cap, shadows, textures, effects, anti-aliasing, render scale),
## AUDIO (master, music, effects, voice, ambience, interface), CONTROLS (rebind every action, mouse sensitivity,
## hold/toggle guard, hold-to-attack), GAMEPLAY (damage numbers, screen shake, auto loot, enemy bars, loot labels,
## camera distance, reduced motion, UI scale, minimap). Changes apply at once and are saved.

const ACTION_NAMES := [
	["move_up", "Move Up"], ["move_down", "Move Down"], ["move_left", "Move Left"], ["move_right", "Move Right"],
	["primary", "Attack / Interact"], ["secondary", "Heavy Attack"], ["dodge", "Dodge"], ["guard", "Guard / Block"],
	["skill_1", "Skill 1"], ["skill_2", "Skill 2"], ["skill_3", "Skill 3"], ["skill_4", "Skill 4"], ["skill_5", "Skill 5"],
	["skill_6", "Skill 6"], ["potion_health", "Health Potion"], ["potion_mana", "Mana Potion"], ["interact", "Interact"],
	["attack_in_place", "Attack in Place"], ["inventory", "Inventory"], ["character", "Character"], ["skills", "Skills"],
	["talents", "Talents"], ["world_map", "World Map"], ["tempos", "Tempos"], ["guide", "Field Guide"], ["chat", "Chat"], ["show_loot", "Show Loot Labels"], ["pause", "Pause"],
]

var _tabs: TabContainer
var _capture_action: StringName = &""
var _capture_button: Button
var _bind_buttons := {}

func _init() -> void:
	super._init("Settings", Vector2(1180, 860))
	modal = true

func _build() -> void:
	_tabs = TabContainer.new()
	_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_tabs)
	_tabs.add_child(_page("Video", _video))
	_tabs.add_child(_page("Audio", _audio))
	_tabs.add_child(_page("Controls", _controls))
	_tabs.add_child(_page("Gameplay", _gameplay))
	var foot := hbox(12)
	foot.alignment = BoxContainer.ALIGNMENT_END
	body.add_child(foot)
	foot.add_child(button("Restore Defaults", func() -> void:
		var group: String = ["video", "audio", "controls", "gameplay"][_tabs.current_tab]
		Game.ui_root.ask("Restore Defaults", "Reset every %s setting to its default?" % group, func() -> void:
			if group == "controls":
				Settings.reset_bindings()
			Settings.reset_group(group)
			_rebuild_pages(), "Restore"), &"", 220.0))
	foot.add_child(button("Done", close_window, &"PrimaryButton", 180.0))

func _rebuild_pages() -> void:
	var cur := _tabs.current_tab
	for c in _tabs.get_children():
		c.queue_free()
	await get_tree().process_frame
	_tabs.add_child(_page("Video", _video))
	_tabs.add_child(_page("Audio", _audio))
	_tabs.add_child(_page("Controls", _controls))
	_tabs.add_child(_page("Gameplay", _gameplay))
	_tabs.current_tab = cur

func _page(name: String, filler: Callable) -> Control:
	var scroll := ScrollContainer.new()
	scroll.name = name
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	var v := vbox(8)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(v)
	filler.call(v)
	return scroll

func _row(v: VBoxContainer, label: String, ctrl: Control, tip := "") -> void:
	var h := hbox(16)
	var l := UITheme.label(label, 18, UITheme.TEXT, UITheme.body_font())
	l.custom_minimum_size = Vector2(360, 0)
	l.mouse_filter = Control.MOUSE_FILTER_PASS
	h.add_child(l)
	ctrl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(ctrl)
	if tip != "":
		TooltipLayer.attach(l, func() -> Control: return Tips.text(tip, label))
	v.add_child(h)

func _option(v: VBoxContainer, label: String, key: String, names: Array, tip := "") -> void:
	var o := OptionButton.new()
	for n in names:
		o.add_item(String(n))
	o.selected = clampi(int(Settings.get(key)), 0, names.size() - 1)
	o.item_selected.connect(func(i: int) -> void: Settings.set_value(key, i))
	o.custom_minimum_size.y = 44
	_row(v, label, o, tip)

func _check(v: VBoxContainer, label: String, key: String, tip := "") -> void:
	var c := CheckBox.new()
	c.button_pressed = bool(Settings.get(key))
	c.text = "On" if c.button_pressed else "Off"
	c.toggled.connect(func(on: bool) -> void:
		c.text = "On" if on else "Off"
		Settings.set_value(key, on))
	_row(v, label, c, tip)

func _slider(v: VBoxContainer, label: String, key: String, lo: float, hi: float, step: float, fmt := "%d%%", mult := 100.0, tip := "") -> void:
	var h := hbox(12)
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = float(Settings.get(key))
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	s.custom_minimum_size = Vector2(300, 30)
	h.add_child(s)
	var val := UITheme.label(fmt % (s.value * mult), 17, UITheme.PARCHMENT, UITheme.number_font())
	val.custom_minimum_size = Vector2(80, 0)
	h.add_child(val)
	s.value_changed.connect(func(x: float) -> void:
		val.text = fmt % (x * mult)
		Settings.set_value(key, x))
	_row(v, label, h, tip)

func _video(v: VBoxContainer) -> void:
	v.add_child(section("Display"))
	var res := []
	for r in Settings.RESOLUTIONS:
		res.append("%d × %d" % [r.x, r.y])
	_option(v, "Resolution", "resolution", res, "Window size in windowed mode. Fullscreen uses your monitor's resolution.")
	_option(v, "Window Mode", "window_mode", Settings.WINDOW_MODES)
	_check(v, "Vertical Sync", "vsync", "Prevents tearing; caps the frame rate to the monitor's refresh rate.")
	_option(v, "Frame Rate Limit", "fps_limit_index", ["Unlimited", "30", "60", "120", "144"])
	v.add_child(section("Quality"))
	_option(v, "Shadow Quality", "shadows_quality", Settings.QUALITY_NAMES, "Low disables torch and lamp shadows.")
	_option(v, "Texture Quality", "texture_quality", Settings.QUALITY_NAMES, "Texture filtering (anisotropy) and sharpness.")
	_option(v, "Effects Quality", "effects_quality", Settings.QUALITY_NAMES, "Ambient occlusion, glow, volumetric fog and detail.")
	_option(v, "Anti-Aliasing", "anti_aliasing", Settings.AA_NAMES)
	_slider(v, "Render Scale", "render_scale", 0.5, 1.0, 0.05, "%d%%", 100.0, "Renders the 3D world at a lower resolution and upscales it (FSR). Lower is faster.")

func _audio(v: VBoxContainer) -> void:
	v.add_child(section("Volume"))
	for pair in [["Master", "master_volume"], ["Music", "music_volume"], ["Effects", "sfx_volume"], ["Voice", "voice_volume"],
			["Ambience", "ambience_volume"], ["Interface", "ui_volume"]]:
		_slider(v, pair[0], pair[1], 0.0, 1.0, 0.05)

func _controls(v: VBoxContainer) -> void:
	v.add_child(section("Mouse"))
	_slider(v, "Mouse Sensitivity", "mouse_sensitivity", 0.3, 2.0, 0.05, "%.2f×", 1.0)
	_check(v, "Guard: Toggle Instead of Hold", "guard_toggle")
	_check(v, "Hold Attack to Keep Swinging", "attack_hold_repeat")
	v.add_child(section("Key Bindings"))
	var note := UITheme.label("Click a binding, then press the new key or mouse button. Escape cancels. A key used elsewhere moves here. Controller buttons are kept.",
		15, UITheme.TEXT_MUTED, UITheme.body_font())
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(note)
	_bind_buttons.clear()
	for pair in ACTION_NAMES:
		var action := StringName(pair[0])
		var b := Button.new()
		b.text = Settings.binding_text(action) if Settings.binding_text(action) != "" else "Unbound"
		b.custom_minimum_size = Vector2(220, 42)
		b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		b.pressed.connect(func() -> void: _begin_capture(action, b))
		_bind_buttons[action] = b
		_row(v, pair[1], b)

func _gameplay(v: VBoxContainer) -> void:
	v.add_child(section("Combat"))
	_check(v, "Damage Numbers", "damage_numbers")
	_check(v, "Blood Effects", "blood")
	_slider(v, "Screen Shake", "screen_shake", 0.0, 1.5, 0.05)
	_check(v, "Enemy Health Bars", "show_enemy_bars")
	_check(v, "Reduced Motion", "reduced_motion", "Removes screen shake and softens flashes.")
	v.add_child(section("Loot"))
	_check(v, "Auto Loot", "auto_loot_enabled", "Walking near a drop picks it up automatically (also the checkbox beside the HP orb).")
	_option(v, "Auto Loot Picks Up", "auto_loot_mode", Settings.AUTO_LOOT_NAMES, "Which drops Auto Loot takes. Gold is always collected on contact.")
	_check(v, "Always Show Loot Labels", "loot_labels_always", "Off: labels appear only while the Show Loot key is held.")
	v.add_child(section("Interface"))
	_slider(v, "Camera Distance", "camera_zoom", 0.7, 1.4, 0.05, "%.2f×", 1.0)
	_slider(v, "Interface Scale", "ui_scale", 0.75, 1.5, 0.05, "%d%%", 100.0)
	_check(v, "Minimap", "show_minimap")

func _begin_capture(action: StringName, b: Button) -> void:
	_capture_action = action
	_capture_button = b
	b.text = "Press a key..."

func _input(e: InputEvent) -> void:
	if _capture_action == &"" or not visible:
		return
	if e is InputEventKey and e.pressed and not e.echo:
		get_viewport().set_input_as_handled()
		if e.keycode == KEY_ESCAPE:
			_end_capture()
			return
		_finish_capture(e)
	elif e is InputEventMouseButton and e.pressed:
		get_viewport().set_input_as_handled()
		_finish_capture(e)

func _finish_capture(e: InputEvent) -> void:
	var stolen := Settings.rebind(_capture_action, e)
	if stolen != &"":
		Events.notify.emit("That key was moved from %s" % _action_name(stolen), &"info")
	_end_capture()

func _end_capture() -> void:
	_capture_action = &""
	for a in _bind_buttons:
		var t := Settings.binding_text(a)
		(_bind_buttons[a] as Button).text = t if t != "" else "Unbound"

static func _action_name(a: StringName) -> String:
	for pair in ACTION_NAMES:
		if StringName(pair[0]) == a:
			return pair[1]
	return String(a)
