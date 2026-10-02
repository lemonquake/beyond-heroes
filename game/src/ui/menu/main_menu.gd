class_name MainMenu
extends Control
## Title screen. Backdrop: Malasugue Town at night seen by a slowly orbiting camera, both heroes standing by the
## fountain, drifting embers and aether motes. Foreground: the wordmark, the ornate menu column (Continue, New Game,
## Load Game, Settings, Credits, Exit) with hover glow and sounds, and the Load Game / Credits panels.
## Emits `new_game`, `load_slot(slot)`; the boot scene handles the flow.

signal new_game
signal load_slot(slot: int)
signal server_selected(mode: String, room: Dictionary)
signal official_play(character: String)

var backdrop: Node3D
var _cam: Camera3D
var _orbit := 0.0
var _menu: VBoxContainer
var _load_panel: PanelContainer
var _credits: PanelContainer
var _settings: SettingsWindow
var _confirm: ConfirmDialog
var _fade: ColorRect
var _buttons: Array[Button] = []
var _heroes: Array[CharacterVisual] = []
var _logo: TextureRect
var _byline: Label
var _server_menu: ServerMenu
## Set before adding: the boot title sequence (TitleIntro) plays over this menu and hands the wordmark to it; the
## wordmark, byline, buttons and music wait for `reveal()`.
var wait_intro := false

const CENTER := Vector3(0, 1.4, 4.0)
const MENU_LOOKS := {&"knight": "veteran", &"mage": "scholar", &"ranger": "huntress", &"shadowblade": "shade"}   # bh-031: the huntress is a woman

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	theme = UITheme.theme()
	var vig := TextureRect.new()
	vig.texture = UIArt.tex("menu/vignette_menu.png")
	vig.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vig.stretch_mode = TextureRect.STRETCH_SCALE
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vig)
	var shade := ColorRect.new()
	shade.color = Color(0.0, 0.0, 0.02, 0.35)
	shade.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	shade.offset_right = 760
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	var logo := UIArt.image("menu/title_logo.png")
	_logo = logo
	logo.position = Vector2(70, 70)
	logo.size = logo.custom_minimum_size
	add_child(logo)
	var byline := UITheme.label("by Aljay Leodones", 20, UITheme.PARCHMENT, UITheme.body_font())
	_byline = byline
	byline.position = Vector2(80, 70 + logo.size.y + 2)
	byline.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	byline.add_theme_constant_override("outline_size", 5)
	add_child(byline)
	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIArt.style("menu/menu_frame.png"))
	frame.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	frame.offset_left = 150
	frame.offset_right = 150 + 400
	frame.offset_top = 330
	frame.offset_bottom = -60
	# a short canvas (phone at a larger Interface Scale): smaller wordmark, the column starts higher
	var short := get_viewport_rect().size.y < 1000.0
	if short:
		logo.scale = Vector2.ONE * 0.72
		byline.position.y = 70 + logo.size.y * 0.72 + 2
		frame.offset_top = 70 + logo.size.y * 0.72 + 44
		frame.offset_bottom = -16
	add_child(frame)
	_menu = VBoxContainer.new()
	_menu.alignment = BoxContainer.ALIGNMENT_CENTER
	_menu.add_theme_constant_override("separation", 10 if get_viewport_rect().size.y >= 1000.0 else 4)
	frame.add_child(_menu)
	_add(&"continue", "Continue", _continue, true)
	_add(&"new", "New Game", func() -> void: new_game.emit(), true)
	_add(&"load", "Load Game", _show_load, true)
	_add(&"servers", "Choose Server / Mode", show_servers)
	_add(&"settings", "Settings", _show_settings)
	_add(&"credits", "Credits", _show_credits)
	_add(&"exit", "Exit", _ask_exit)
	var ver := UITheme.label("Development build · %s" % ProjectSettings.get_setting("application/config/name"), 14, UITheme.TEXT_MUTED, UITheme.body_font())
	ver.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	ver.offset_left = -420
	ver.offset_top = -40
	ver.offset_right = -24
	ver.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(ver)
	_load_panel = _build_load()
	add_child(_load_panel)
	_credits = _build_credits()
	add_child(_credits)
	_settings = SettingsWindow.new()
	add_child(_settings)
	_confirm = ConfirmDialog.new()
	add_child(_confirm)
	_fade = ColorRect.new()
	_fade.color = Color(0.01, 0.01, 0.015)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_fade)
	show_servers()
	if wait_intro:
		_fade.modulate.a = 0.0
		_logo.visible = false
		_byline.visible = false
		for b in _buttons:
			b.modulate.a = 0.0
		return
	create_tween().tween_property(_fade, "modulate:a", 0.0, 1.6).set_delay(0.2)
	reveal()

## Buttons in, focus, music (straight away, or when the title sequence hands over).
func reveal() -> void:
	_logo.visible = true
	_byline.visible = true
	_buttons[3].grab_focus.call_deferred()
	Audio.play_music(&"main_theme")
	Audio.play_ambience(&"amb_town")
	_animate_in()
	if _server_menu:
		_server_menu.move_to_front()

func show_servers() -> void:
	if _server_menu and is_instance_valid(_server_menu):
		return
	_server_menu = ServerMenu.new()
	add_child(_server_menu)
	_server_menu.official_play.connect(official_play.emit)
	_server_menu.official_new.connect(func() -> void:
		SaveSystem.scope = "official"
		server_selected.emit("official", {})
		new_game.emit())
	_server_menu.selected.connect(func(mode: String, room: Dictionary) -> void:
		if mode == "back":
			_server_menu.queue_free()
			_server_menu = null
			return
		if mode == "offline":
			SaveSystem.scope = "legacy"
		elif mode == "custom":
			if not SaveSystem.choose_custom_room(String(room.get("room", ""))):
				_server_menu.show_error("This custom room has an invalid identity.")
				return
			SaveSystem.remember_custom_room(room)
		server_selected.emit(mode, room)
		_server_menu.queue_free()
		_server_menu = null
		var has_save := _latest_slot() >= 0
		for button in _buttons:
			if button.name in ["continue", "load"]:
				button.disabled = not has_save
			if button.name == "new":
				button.disabled = false
				button.text = "New Offline Character" if mode == "offline" else "New Custom Character"
		_byline.text = "Offline Play · local saves" if mode == "offline" else "Custom Game · " + String(room.get("name", "Friends' Game")))

## Where the wordmark and byline sit on this screen (canvas coordinates), for the title sequence's hand-off.
func logo_rect() -> Rect2:
	return Rect2(_logo.global_position, _logo.size * _logo.scale)

func byline_pos() -> Vector2:
	return _byline.global_position

func byline_font_scale() -> float:
	return _byline.scale.x * 20.0 / 60.0

func _add(id: StringName, text: String, cb: Callable, disabled := false) -> void:
	var b := UIWindow.button(text, cb, &"BannerButton", 330.0)
	b.name = String(id)
	b.custom_minimum_size.y = 66 if get_viewport_rect().size.y >= 1000.0 else 60
	b.disabled = disabled
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.pivot_offset = Vector2(165, 33)
	b.mouse_entered.connect(func() -> void:
		if not b.disabled:
			b.create_tween().tween_property(b, "scale", Vector2(1.04, 1.04), 0.12).set_trans(Tween.TRANS_BACK))
	b.mouse_exited.connect(func() -> void: b.create_tween().tween_property(b, "scale", Vector2.ONE, 0.12))
	b.focus_entered.connect(func() -> void: Audio.play_ui(&"ui_hover"))
	_menu.add_child(b)
	_buttons.append(b)

func _animate_in() -> void:
	var i := 0
	for b in _buttons:
		b.modulate.a = 0.0
		var tw := b.create_tween()
		tw.tween_interval(0.5 + i * 0.08)
		tw.tween_property(b, "modulate:a", 1.0, 0.35)
		i += 1

## The 3D backdrop is built by the boot scene into the world (so the same map can host the game later).
func build_backdrop(world: Node3D) -> void:
	backdrop = Node3D.new()
	backdrop.name = "MenuBackdrop"
	world.add_child(backdrop)
	var map := Game.build_map(&"sanctuary")
	backdrop.add_child(map)
	# the heroes by the fountain, facing the camera's orbit centre (a class joins once its model is built)
	for pair in [[&"knight", Vector3(-1.6, 0, 8.6), 200.0], [&"mage", Vector3(1.7, 0, 8.4), 160.0],
			[&"ranger", Vector3(-3.7, 0, 7.5), 215.0], [&"shadowblade", Vector3(3.8, 0, 7.3), 145.0]]:
		var cls := DB.class_def(pair[0])
		if cls == null or not ResourceLoader.exists(cls.model_path):
			continue
		var v := CharacterVisual.new()
		backdrop.add_child(v)
		# bh-023: the four by the fountain are heroes like the player's: one body, a face each, their starting kit
		v.setup(HeroLook.MODEL if ResourceLoader.exists(HeroLook.MODEL) else cls.model_path, 1.0, cls.tint, cls.id)
		v.set_look(HeroLook.preset(MENU_LOOKS.get(pair[0], "plain")))
		v.position = pair[1]
		v.rotation_degrees.y = pair[2]
		var eq := Equipment.new()
		for bid in cls.starting_items:
			var it := DB.make_item(bid, BH.Rarity.BEGINNER, 1, 1)
			if it and not it.base.is_weapon() and it.base.category != &"shield":
				eq.slots[eq.auto_slot(it)] = it
			if it and it.base.is_weapon():
				var wt := DB.weapon_type(it.base.weapon_type)
				if wt:
					v.attach_weapon(&"main", wt.model, wt.grip_offset)
					v.set_stance(wt.idle_anim if v.has_anim(wt.idle_anim) else &"idle")
			elif it and it.base.category == &"shield":
				v.attach_weapon(&"off", "res://assets/weapons/shield.glb")
				v.set_stance(&"idle_shield" if v.has_anim(&"idle_shield") else &"idle")
		v.dress_equipment(eq)
		_heroes.append(v)
	# drifting embers and aether motes
	backdrop.add_child(_particles(UIArt.tex("hud/ember.png"), Color(1.0, 0.65, 0.3), 90, Vector3(0, 0.6, 0), 0.16))
	backdrop.add_child(_particles(UIArt.tex("hud/mote.png"), Color(0.55, 0.95, 1.0), 60, Vector3(0, 0.25, 0), 0.1))
	_cam = Camera3D.new()
	_cam.fov = 42.0
	_cam.far = 400.0
	backdrop.add_child(_cam)
	_cam.make_current()
	_place_cam()

func _particles(tex: Texture2D, col: Color, n: int, vel: Vector3, size: float) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = Perf.particles(n)
	p.lifetime = 9.0
	p.preprocess = 9.0
	p.visibility_aabb = AABB(Vector3(-40, -5, -40), Vector3(80, 30, 80))
	p.position = CENTER + Vector3(0, -1.0, 0)
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(18, 2, 14)
	pm.direction = Vector3(0.2, 1, 0)
	pm.spread = 25.0
	pm.initial_velocity_min = 0.2
	pm.initial_velocity_max = 0.7
	pm.gravity = vel
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 0.6
	pm.scale_min = 0.5
	pm.scale_max = 1.2
	var grad := Gradient.new()
	grad.set_color(0, Color(col, 0.0))
	grad.add_point(0.15, Color(col, 1.0))
	grad.add_point(0.8, Color(col, 0.8))
	grad.set_color(grad.get_point_count() - 1, Color(col, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = grad
	pm.color_ramp = gt
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = tex
	quad.material = m
	p.draw_pass_1 = quad
	return p

func _place_cam() -> void:
	var a := _orbit
	_cam.global_position = CENTER + Vector3(sin(a) * 15.0, 5.5 + sin(a * 0.7) * 0.6, cos(a) * 15.0)
	_cam.look_at(CENTER + Vector3(0, 0.2, 0))

func _process(delta: float) -> void:
	if _cam and is_instance_valid(_cam):
		_orbit += delta * 0.045
		_place_cam()
	for v in _heroes:
		if is_instance_valid(v):
			v.update_locomotion(Vector2.ZERO, false, 0.0, delta)

func dispose_backdrop() -> void:
	if backdrop and is_instance_valid(backdrop):
		backdrop.queue_free()
	backdrop = null
	_cam = null
	_heroes.clear()

# ---- Load / Credits / Settings ----------------------------------------------------------------------------------

static func _latest_slot() -> int:
	var best := -1
	var t := -1
	for s in SaveSystem.SLOTS:
		var sum := SaveSystem.slot_summary(s)
		if not sum.is_empty() and int(sum.saved_at) > t:
			t = int(sum.saved_at)
			best = s
	return best

func _continue() -> void:
	var s := _latest_slot()
	if s >= 0:
		load_slot.emit(s)

func _panel(title: String, w := 760.0) -> Array:
	var p := PanelContainer.new()
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.offset_left = -w * 0.5 + 200
	p.offset_right = w * 0.5 + 200
	p.offset_top = -330
	p.offset_bottom = 330
	p.visible = false
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	p.add_child(v)
	var t := UITheme.title(title, 30, UITheme.GOLD)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	v.add_child(HSeparator.new())
	return [p, v]

func _build_load() -> PanelContainer:
	var pv := _panel("Load Game")
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pv[1].add_child(scroll)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)
	var back := UIWindow.button("Back", func() -> void: _load_panel.visible = false, &"", 200.0)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	pv[1].add_child(back)
	return pv[0]

func _show_load() -> void:
	_credits.visible = false
	var list: VBoxContainer = _load_panel.get_child(0).get_child(2).get_child(0)
	for c in list.get_children():
		c.queue_free()
	for s in SaveSystem.SLOTS:
		list.add_child(slot_card(s, func(slot): load_slot.emit(slot), func(slot):
			SaveSystem.delete_slot(slot)
			_show_load()))
	_load_panel.visible = true

## A save slot card: class portrait, name, class and level, location, play time, date; Load / Delete.
static func slot_card(s: int, on_load: Callable, on_delete: Callable, action_text := "Load") -> Control:
	var sum := SaveSystem.slot_summary(s)
	var p := PanelContainer.new()
	p.theme_type_variation = &"InsetPanel"
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	p.add_child(h)
	var por := TextureRect.new()
	por.custom_minimum_size = Vector2(72, 72)
	por.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	por.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if not sum.is_empty():
		hero_picture(por, sum.get("hero", {}), String(sum.get("class", "")))
	h.add_child(por)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	if sum.is_empty():
		v.add_child(UITheme.label("Slot %d — Empty" % (s + 1), 20, UITheme.TEXT_MUTED, UITheme.title_font()))
	else:
		var cls := DB.class_def(StringName(sum["class"]))
		var md := DB.map_def(StringName(sum["map"]))
		v.add_child(UITheme.label("%s — Level %d %s" % [sum["name"], sum["level"], cls.display_name if cls else sum["class"]], 20, UITheme.PARCHMENT, UITheme.title_font()))
		var when := Time.get_datetime_string_from_unix_time(int(sum["saved_at"]), true)
		v.add_child(UITheme.label("%s · %s · saved %s" % [md.display_name if md else sum["map"], PauseMenu._time(float(sum["play_time"])), when],
			15, UITheme.TEXT_DIM, UITheme.body_font()))
	if not sum.is_empty() or action_text != "Load":
		h.add_child(UIWindow.button(action_text, func() -> void: on_load.call(s), &"PrimaryButton", 130.0))
	if not sum.is_empty() and on_delete.is_valid():
		h.add_child(UIWindow.button("Delete", func() -> void:
			var root := p.get_tree().root
			var dlg := ConfirmDialog.new()
			root.add_child(dlg)
			dlg.theme = UITheme.theme()
			dlg.ask("Delete Save", "Delete slot %d permanently?" % (s + 1), func() -> void:
				on_delete.call(s)
				dlg.queue_free(), "Delete", true), &"", 110.0))
	return p

func _build_credits() -> PanelContainer:
	var pv := _panel("Credits", 820.0)
	var t := RichTextLabel.new()
	t.bbcode_enabled = true
	t.fit_content = false
	t.size_flags_vertical = Control.SIZE_EXPAND_FILL
	t.add_theme_font_size_override("normal_font_size", 19)
	t.add_theme_font_size_override("bold_font_size", 21)
	t.text = "[center][b][color=#f5cc75]BEYOND HEROES[/color][/b]\nby Aljay Leodones\n\n" \
		+ "[b][color=#ebdcbd]Design & Direction[/color][/b]\nAljay Leodones\n\n" \
		+ "[b][color=#ebdcbd]Engine[/color][/b]\nGodot Engine (MIT licence)\n\n" \
		+ "[b][color=#ebdcbd]Art, Audio & Code[/color][/b]\nAll models, textures, interface art, icons, sound effects and music are produced for this project by its own generation scripts (Blender, Python).\nSee ASSET_CREDITS.md for the full record.\n\n" \
		+ "[b][color=#ebdcbd]Fonts[/color][/b]\nSystem fonts of the host operating system.\n\n" \
		+ "[color=#9a8f80]Thank you for playing.[/color][/center]"
	pv[1].add_child(t)
	var back := UIWindow.button("Back", func() -> void: _credits.visible = false, &"", 200.0)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	pv[1].add_child(back)
	return pv[0]

func _show_credits() -> void:
	_load_panel.visible = false
	_credits.visible = true

func _show_settings() -> void:
	_load_panel.visible = false
	_credits.visible = false
	_settings.open()

## Back (the phone's button): close the open panel, or ask before leaving the game.
func go_back() -> void:
	if _server_menu and is_instance_valid(_server_menu):
		_server_menu.go_back()
	elif _confirm.visible:
		_confirm.cancel()
	elif _settings.visible:
		_settings.close_window()
	elif _load_panel.visible:
		_load_panel.visible = false
	elif _credits.visible:
		_credits.visible = false
	else:
		_ask_exit()

func _ask_exit() -> void:
	_confirm.ask("Exit Beyond Heroes", "Close the game? Your heroes are saved.", func() -> void: get_tree().quit(), "Exit", true)

func fade_out() -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "modulate:a", 1.0, 0.5)
	await tw.finished

## bh-031: a hero card's picture: their profile picture, else the ID shot of their model (taken now, once, for an
## older save that has none yet; the class portrait shows meanwhile).
static var _card_shots := {}

static func hero_picture(por: TextureRect, hero: Dictionary, cls: String) -> void:
	var t := ProfilePicture.texture_of(ProfilePicture.bytes_of_save(hero))
	por.texture = t if t else UIArt.portrait(cls)
	if t != null or not hero.has("progress"):      # a server summary carries no look to shoot
		return
	var key := hash([hero.get("look", {}), hero.get("equipment", {})])
	if _card_shots.has(key):
		por.texture = _card_shots[key]
		return
	_shoot_card(por, hero, key)

static func _shoot_card(por: TextureRect, hero: Dictionary, key: int) -> void:
	var eq := Equipment.new()
	eq.from_dict(hero.get("equipment", {}))
	var lk = hero.get("look", {})
	var img := await PortraitStudio.render_hero(lk if lk is Dictionary else {}, eq, ProfilePicture.SIZE)
	if img == null:
		return
	var tex := ImageTexture.create_from_image(img)
	_card_shots[key] = tex
	if is_instance_valid(por):
		por.texture = tex
