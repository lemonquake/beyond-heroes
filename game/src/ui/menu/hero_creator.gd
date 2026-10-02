class_name HeroCreator
extends Control
## bh-023: the hero creator. Centre: the hero on the plinth (drag to turn, wheel to zoom; Face / Body views; poses).
## Left: the pages (Looks, Body, Skin, Face, Eyes, Brows, Nose, Mouth, Ears, Hair, Beard). Right: that page's styles,
## colours and sliders; every slider runs from one named extreme to the other, and the far end is meant to be silly.
## Bottom: Back, Undo, Start Over, and the way forward. The look is a HeroLook Dictionary; nothing else is touched.
##
## Used twice: after Hero Selection for a new hero (`class_id` set, shows the class's starting kit) and from the
## Character window for a living hero (`hero` set: their own gear, "Done" instead of "Begin").

signal done(look: Dictionary)
signal back

## [page id, label, camera ("body" | "face"), controls]. Controls: ["choice", key, title], ["color", key, title,
## tones, follow label], ["slider", key, label, low word, high word], ["flag", key, label], ["presets"], ["tools"].
const PAGES := [
	["looks", "Looks", "body", [["presets"], ["tools"]]],
	["body", "Body", "body", [
		["slider", "female", "Figure", "Masculine", "Feminine"],
		["slider", "height", "Height", "Short", "Towering"], ["slider", "build", "Build", "Lean", "Stout"],
		["slider", "muscle", "Muscle", "Wiry", "Mighty"], ["slider", "belly", "Belly", "Flat", "Round"],
		["slider", "rear", "Rear", "Flat", "Ample"], ["slider", "head", "Head", "Small", "Enormous"],
		["slider", "hands", "Hands", "Dainty", "Shovels"], ["slider", "feet", "Feet", "Small", "Flippers"],
		["color", "underwear", "Smallclothes", "CLOTH_TONES", ""]]],
	["skin", "Skin", "body", [
		["color", "skin", "Skin tone", "SKIN_TONES", ""], ["choice", "pattern", "Pattern"],
		["color", "pattern_color", "Pattern colour", "MARK_TONES", ""],
		["slider", "pattern_amount", "Pattern strength", "Faint", "Bold"], ["slider", "pattern_scale", "Pattern size", "Fine", "Broad"]]],
	["face", "Face", "face", [
		["slider", "jaw_wide", "Jaw", "Narrow", "Square"], ["slider", "chin_long", "Chin", "Short", "Endless"],
		["slider", "cheeks", "Cheeks", "Gaunt", "Full"], ["slider", "brow_heavy", "Brow ridge", "Smooth", "Heavy"],
		["choice", "marking", "Marks"], ["color", "marking_color", "Mark colour", "MARK_TONES", ""]]],
	["eyes", "Eyes", "face", [
		["choice", "eye", "Shape"], ["color", "eye_color", "Eye colour", "EYE_TONES", ""],
		["slider", "eye_size", "Size", "Beady", "Saucers"], ["slider", "eye_spacing", "Spacing", "Close", "Wide"],
		["slider", "eye_height", "Height", "Low", "High"], ["slider", "eye_tilt", "Tilt", "Drooping", "Slanted"],
		["slider", "eyes_pop", "Depth", "Sunken", "Bulging"], ["slider", "eye_glow", "Glow", "None", "Blazing"]]],
	["brows", "Brows", "face", [
		["choice", "brow", "Shape"], ["color", "brow_color", "Brow colour", "HAIR_TONES", "Match hair"],
		["slider", "brow_thick", "Thickness", "Fine", "Shaggy"], ["slider", "brow_tilt", "Tilt", "Worried", "Furious"],
		["slider", "brow_height", "Height", "Low", "Raised"]]],
	["nose", "Nose", "face", [
		["slider", "nose_size", "Size", "Button", "Boulder"], ["slider", "nose_long", "Length", "Snub", "Beak"],
		["slider", "nose_wide", "Width", "Narrow", "Broad"], ["slider", "nose_up", "Tip", "Hooked", "Upturned"]]],
	["mouth", "Mouth", "face", [
		["slider", "lips_full", "Lips", "Thin", "Plush"], ["slider", "mouth_wide", "Width", "Small", "Wide"],
		["slider", "mouth_smile", "Mood", "Scowl", "Grin"], ["color", "lip_color", "Lip colour", "LIP_TONES", ""],
		["slider", "lip_amount", "Lip paint", "Bare", "Painted"]]],
	["ears", "Ears", "face", [
		["slider", "ears_size", "Size", "Tiny", "Sails"], ["slider", "ears_point", "Tips", "Round", "Pointed"],
		["slider", "ears_out", "Angle", "Flat", "Jug"]]],
	["hair", "Hair", "face", [
		["choice", "hair", "Style"], ["color", "hair_color", "Hair colour", "HAIR_TONES", ""],
		["slider", "hair_length", "Length", "Trimmed", "To the floor"], ["flag", "show_helm", "Show the helm when one is worn"]]],
	["beard", "Beard", "face", [
		["choice", "beard", "Style"], ["color", "beard_color", "Beard colour", "HAIR_TONES", "Match hair"],
		["slider", "beard_length", "Length", "Trimmed", "To the knees"], ["slider", "stubble", "Stubble", "Clean", "Rough"]]],
]
const TONES := {"SKIN_TONES": HeroLook.SKIN_TONES, "HAIR_TONES": HeroLook.HAIR_TONES, "EYE_TONES": HeroLook.EYE_TONES,
	"LIP_TONES": HeroLook.LIP_TONES, "MARK_TONES": HeroLook.MARK_TONES, "CLOTH_TONES": HeroLook.CLOTH_TONES}
const CODE_PREFIX := "BH1:"
const STRIKES := {&"knight": &"sword_2", &"mage": &"staff_1", &"ranger": &"bow_1", &"shadowblade": &"dagger_2"}

var class_id: StringName = &"knight"
var hero: HeroData                      # set to restyle a living hero
var hero_name := ""
var look := {}
var preview: CharacterPreview
var _page := 0
var _rail := {}
var _content: VBoxContainer
var _page_title: Label
var _undo: Array = []
var _undo_key := ""
var _undo_btn: Button
var _gear_btn: Button
var _face_btn: Button
var _body_btn: Button
var _note: Label
var _mixer: PopupPanel
var _mixer_target := ""
var _mix_sliders: Array[HSlider] = []
var _mix_swatch: ColorRect
var _posing := false
var _face_view := false
var _track: StyleBoxFlat
var _fill: StyleBoxFlat

func _enter_tree() -> void:
	Settings.hold_design_scale(true)

func _exit_tree() -> void:
	Settings.hold_design_scale(false)

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)

func _ready() -> void:
	theme = UITheme.theme()
	look = HeroLook.sanitize(look)
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.02, 0.03)
	add_child(bg)
	var backdrop := TextureRect.new()
	backdrop.texture = UIArt.tex("tree/tree_bg_%s.png" % _class())
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.modulate = Color(0.42, 0.42, 0.48)
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(backdrop)
	var vig := TextureRect.new()
	vig.texture = UIArt.tex("menu/vignette_menu.png")
	vig.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	vig.stretch_mode = TextureRect.STRETCH_SCALE
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vig)
	var glow := UIArt.image("menu/class_plinth_glow.png")
	glow.stretch_mode = TextureRect.STRETCH_SCALE
	glow.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	glow.offset_left = -360
	glow.offset_right = 360
	glow.offset_top = -360
	glow.offset_bottom = -170
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(glow)
	preview = CharacterPreview.new(Vector2i(1300, 1700))
	preview.set_anchors_preset(Control.PRESET_FULL_RECT)
	preview.offset_left = 330
	preview.offset_right = -650
	preview.offset_top = 70
	preview.offset_bottom = -150
	preview.look = look
	add_child(preview)
	var title := UITheme.title("Shape Your Hero" if hero == null else "Change Your Look", 38, UITheme.GOLD)
	title.set_anchors_preset(Control.PRESET_TOP_WIDE)
	title.offset_left = 330
	title.offset_right = -650
	title.offset_top = 22
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(title)
	_build_rail()
	_build_panel()
	_build_stage_bar()
	_build_footer()
	_build_mixer()
	preview.show_class(_class(), hero)
	preview.set_look(look)
	_show_page(0)
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.35)

func _class() -> StringName:
	return hero.cls.id if hero else class_id

# ---- Layout -----------------------------------------------------------------------------------------------------

func _build_rail() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	panel.offset_left = 36
	panel.offset_right = 316
	panel.offset_top = 70
	panel.offset_bottom = -150
	add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 5)
	scroll.add_child(v)
	for i in PAGES.size():
		var b := Button.new()
		b.toggle_mode = true
		b.text = "      " + String(PAGES[i][1])
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 58)
		b.add_theme_font_size_override("font_size", 22)
		var glyph := Glyph.new(String(PAGES[i][0]))
		glyph.position = Vector2(14, 11)
		b.add_child(glyph)
		b.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			_show_page(i))
		b.mouse_entered.connect(func() -> void: Audio.play_ui(&"ui_hover"))
		v.add_child(b)
		_rail[i] = b

func _build_panel() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	panel.offset_left = -636
	panel.offset_right = -36
	panel.offset_top = 70
	panel.offset_bottom = -150
	add_child(panel)
	var pad := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, 12)
	panel.add_child(pad)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	pad.add_child(v)
	var head := HBoxContainer.new()
	v.add_child(head)
	_page_title = UITheme.title("", 30, UITheme.GOLD)
	_page_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(_page_title)
	var shuffle := UIWindow.button("Shuffle page", _shuffle_page, &"", 170.0)
	TooltipLayer.attach(shuffle, func() -> Control: return Tips.text("Roll new values for this page only. Hold Shift for the wild end of every slider."))
	head.add_child(shuffle)
	v.add_child(HSeparator.new())
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(scroll)
	_content = VBoxContainer.new()
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_content.add_theme_constant_override("separation", 10)
	scroll.add_child(_content)

## Under the plinth: the two views, the poses, gear on or off.
func _build_stage_bar() -> void:
	var bar := HBoxContainer.new()
	bar.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bar.offset_left = 330
	bar.offset_right = -650
	bar.offset_top = -208
	bar.offset_bottom = -158
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.add_theme_constant_override("separation", 8)
	add_child(bar)
	_face_btn = _toggle("Face", func() -> void: _focus("face"))
	_body_btn = _toggle("Body", func() -> void: _focus("body"))
	bar.add_child(_face_btn)
	bar.add_child(_body_btn)
	bar.add_child(VSeparator.new())
	for pose in [["Stand", &""], ["Walk", &"hero_walk"], ["Run", &"hero_run"], ["Strike", &"strike"], ["Cheer", &"taunt"]]:
		bar.add_child(UIWindow.button(pose[0], func() -> void: _pose(pose[1]), &"", 96.0))
	bar.add_child(VSeparator.new())
	_gear_btn = _toggle("Gear", _toggle_gear)
	_gear_btn.button_pressed = true
	TooltipLayer.attach(_gear_btn, func() -> Control: return Tips.text("Show the hero in their gear, or in their smallclothes to see the body."))
	bar.add_child(_gear_btn)

func _toggle(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.toggle_mode = true
	b.text = text
	b.custom_minimum_size = Vector2(96, 0)
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		cb.call())
	return b

func _build_footer() -> void:
	var bar := PanelContainer.new()
	bar.theme_type_variation = &"GlassPanel"
	bar.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bar.offset_left = 36
	bar.offset_right = -36
	bar.offset_top = -134
	bar.offset_bottom = -30
	add_child(bar)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	bar.add_child(h)
	h.add_child(UIWindow.button("Back", func() -> void: back.emit(), &"", 170.0))
	_undo_btn = UIWindow.button("Undo", _undo_last, &"", 130.0)
	_undo_btn.disabled = true
	h.add_child(_undo_btn)
	h.add_child(UIWindow.button("Start Over", func() -> void: _set_look(HeroLook.defaults(), "reset"), &"", 170.0))
	_note = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_note.text = ("%s the %s" % [hero_name, DB.class_def(_class()).display_name]) if hero_name != "" else \
		"Drag the hero to turn them. Every slider's far end is there to be abused."
	h.add_child(_note)
	var go := UIWindow.button("Begin Journey" if hero == null else "Done", func() -> void: done.emit(HeroLook.to_save(look)), &"PrimaryButton", 260.0)
	go.custom_minimum_size.y = 64
	h.add_child(go)

# ---- Pages ------------------------------------------------------------------------------------------------------

func _show_page(i: int) -> void:
	_page = i
	for k in _rail:
		(_rail[k] as Button).button_pressed = k == i
	_page_title.text = String(PAGES[i][1])
	_focus(String(PAGES[i][2]))
	_fill_page()

func _fill_page() -> void:
	for c in _content.get_children():
		c.queue_free()
	for ctl in PAGES[_page][3]:
		match String(ctl[0]):
			"presets": _add_presets()
			"tools": _add_tools()
			"choice": _add_choice(ctl[1], ctl[2])
			"color": _add_color(ctl[1], ctl[2], TONES[ctl[3]], ctl[4])
			"slider": _add_slider(ctl[1], ctl[2], ctl[3], ctl[4])
			"flag": _add_flag(ctl[1], ctl[2])

func _heading(text: String) -> void:
	_content.add_child(UITheme.label(text, 19, UITheme.BRONZE, UITheme.body_bold()))

func _add_presets() -> void:
	_heading("Ready-made looks")
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 8)
	flow.add_theme_constant_override("v_separation", 8)
	_content.add_child(flow)
	for p in HeroLook.PRESETS:
		flow.add_child(UIWindow.button(p[1], func() -> void: _set_look(HeroLook.preset(p[0]), "preset"), &"", 176.0))

func _add_tools() -> void:
	_heading("Roll the dice")
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	row.add_theme_constant_override("v_separation", 8)
	_content.add_child(row)
	row.add_child(UIWindow.button("Surprise Me", func() -> void: _random(0.15), &"PrimaryButton", 270.0))
	row.add_child(UIWindow.button("Go Wild", func() -> void: _random(1.0), &"", 270.0))
	_heading("Share a look")
	var row2 := HFlowContainer.new()
	row2.add_theme_constant_override("h_separation", 8)
	_content.add_child(row2)
	row2.add_child(UIWindow.button("Copy Look Code", _copy_code, &"", 270.0))
	row2.add_child(UIWindow.button("Paste Look Code", _paste_code, &"", 270.0))
	var tip := UITheme.label("A look code holds the whole look. Copy it to keep a look for another hero, or to hand it to a friend.", 16,
		UITheme.TEXT_DIM, UITheme.body_font())
	tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content.add_child(tip)

func _add_choice(key: String, title: String) -> void:
	_heading(title)
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 6)
	flow.add_theme_constant_override("v_separation", 6)
	_content.add_child(flow)
	var group := ButtonGroup.new()
	for c in HeroLook.CHOICES[key]:
		var id: String = c[0]
		if (key == "hair" and id not in ["shaved", "bald"] and not ResourceLoader.exists(HeroLook.HAIR_MODEL % id)) \
				or (key == "beard" and id != "none" and not ResourceLoader.exists(HeroLook.BEARD_MODEL % id)):
			continue
		var b := Button.new()
		b.toggle_mode = true
		b.button_group = group
		b.text = c[1]
		b.custom_minimum_size = Vector2(136, 46)
		b.add_theme_font_size_override("font_size", 17)
		b.button_pressed = look[key] == id
		b.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			_change(key, id))
		flow.add_child(b)

func _add_color(key: String, title: String, tones: Array, follow: String) -> void:
	_heading(title)
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 6)
	flow.add_theme_constant_override("v_separation", 6)
	_content.add_child(flow)
	var cur := String(look[key])
	if follow != "":
		var fb := Button.new()
		fb.toggle_mode = true
		fb.text = follow
		fb.button_pressed = cur == ""
		fb.custom_minimum_size = Vector2(140, 44)
		fb.add_theme_font_size_override("font_size", 16)
		fb.pressed.connect(func() -> void:
			_change(key, "")
			_fill_page.call_deferred())
		flow.add_child(fb)
	var listed := false
	for t in tones:
		var sw := Swatch.new(Color.html(t), cur == t)
		sw.picked.connect(func() -> void:
			_change(key, t)
			_fill_page.call_deferred())
		flow.add_child(sw)
		listed = listed or cur == t
	# a colour mixed by hand sits at the end of the row, next to the mixer
	if cur != "" and not listed:
		flow.add_child(Swatch.new(Color.html(cur), true))
	flow.add_child(UIWindow.button("Mix", func() -> void: _open_mixer(key), &"", 84.0))

func _add_slider(key: String, label: String, low: String, high: String) -> void:
	var spec: Array = HeroLook.SLIDERS[key]
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 0)
	_content.add_child(box)
	var top := HBoxContainer.new()
	box.add_child(top)
	var name_l := UITheme.label(label, 19, UITheme.PARCHMENT, UITheme.body_bold())
	name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(name_l)
	var val := UITheme.label("", 17, UITheme.GOLD, UITheme.number_font())
	top.add_child(val)
	var reset := UIWindow.button("Reset", func() -> void: pass, &"FlatButton", 0.0)
	reset.add_theme_font_size_override("font_size", 15)
	top.add_child(reset)
	var s := HSlider.new()
	s.min_value = spec[1]
	s.max_value = spec[2]
	s.step = (float(spec[2]) - float(spec[1])) / 240.0
	s.value = float(look[key])
	s.custom_minimum_size = Vector2(0, 34)
	_style_slider(s)
	box.add_child(s)
	var ends := HBoxContainer.new()
	box.add_child(ends)
	var lo := UITheme.label(low, 14, UITheme.TEXT_MUTED, UITheme.body_font())
	lo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ends.add_child(lo)
	ends.add_child(UITheme.label(high, 14, UITheme.TEXT_MUTED, UITheme.body_font()))
	val.text = _percent(key, s.value)
	s.value_changed.connect(func(x: float) -> void:
		val.text = _percent(key, x)
		_change(key, x))
	reset.pressed.connect(func() -> void: s.value = spec[0])

## A track the eye can follow: a dark groove with a bronze rim, filled gold up to the grabber.
func _style_slider(s: HSlider) -> void:
	if _track == null:
		_track = StyleBoxFlat.new()
		_track.bg_color = Color(0.03, 0.025, 0.025, 0.95)
		_track.border_color = UITheme.BRONZE_DIM
		_track.set_border_width_all(1)
		_track.set_corner_radius_all(4)
		_track.content_margin_top = 4
		_track.content_margin_bottom = 4
		_fill = StyleBoxFlat.new()
		_fill.bg_color = UITheme.BRONZE
		_fill.set_corner_radius_all(4)
		_fill.content_margin_top = 4
		_fill.content_margin_bottom = 4
	s.add_theme_stylebox_override("slider", _track)
	s.add_theme_stylebox_override("grabber_area", _fill)
	s.add_theme_stylebox_override("grabber_area_highlight", _fill)

## How far a slider sits from its usual value, toward either end: -100 .. +100.
static func _percent(key: String, v: float) -> String:
	var s: Array = HeroLook.SLIDERS[key]
	var d := float(s[0])
	var p := 0.0
	if v >= d and float(s[2]) > d:
		p = (v - d) / (float(s[2]) - d) * 100.0
	elif v < d and d > float(s[1]):
		p = -(d - v) / (d - float(s[1])) * 100.0
	return "%+d" % int(round(p)) if absf(p) >= 0.5 else "0"

func _add_flag(key: String, label: String) -> void:
	var c := CheckBox.new()
	c.text = label
	c.button_pressed = bool(look[key])
	c.toggled.connect(func(on: bool) -> void: _change(key, on))
	_content.add_child(c)

# ---- Changes ----------------------------------------------------------------------------------------------------

func _change(key: String, value: Variant) -> void:
	if look.get(key) == value:
		return
	_remember(key)
	look[key] = value
	preview.set_look(look)

func _set_look(new_look: Dictionary, why: String) -> void:
	_remember(why + str(Time.get_ticks_msec()))
	look = HeroLook.sanitize(new_look)
	preview.set_look(look)
	_fill_page()

## One undo step per control touched (dragging a slider is one step, not a hundred).
func _remember(key: String) -> void:
	if key == _undo_key:
		return
	_undo_key = key
	_undo.append(look.duplicate(true))
	if _undo.size() > 60:
		_undo.pop_front()
	_undo_btn.disabled = false

func _undo_last() -> void:
	if _undo.is_empty():
		return
	look = _undo.pop_back()
	_undo_key = ""
	_undo_btn.disabled = _undo.is_empty()
	preview.set_look(look)
	_fill_page()

func _random(silly: float) -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var r := HeroLook.random(rng, silly)
	r["show_helm"] = look["show_helm"]
	_set_look(r, "random")

## New values for this page's controls only.
func _shuffle_page() -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var r := HeroLook.random(rng, 1.0 if Input.is_key_pressed(KEY_SHIFT) else 0.35)
	var next := look.duplicate(true)
	var any := false
	for ctl in PAGES[_page][3]:
		if ctl.size() > 1 and String(ctl[0]) != "flag" and r.has(ctl[1]):
			next[ctl[1]] = r[ctl[1]]
			any = true
	if not any:
		next = r
		next["show_helm"] = look["show_helm"]
	_set_look(next, "shuffle")

func _copy_code() -> void:
	DisplayServer.clipboard_set(CODE_PREFIX + Marshalls.utf8_to_base64(JSON.stringify(HeroLook.to_save(look))))
	_note.text = "Look code copied."

func _paste_code() -> void:
	var parsed: Variant = decode(DisplayServer.clipboard_get())
	if parsed == null:
		_note.text = "That is not a look code."
		return
	_set_look(parsed, "paste")
	_note.text = "Look pasted."

## A look from a look code, or null.
static func decode(text: String) -> Variant:
	var t := text.strip_edges()
	if not t.begins_with(CODE_PREFIX):
		return null
	var parsed = JSON.parse_string(Marshalls.base64_to_utf8(t.substr(CODE_PREFIX.length())))
	return HeroLook.sanitize(parsed) if parsed is Dictionary else null

# ---- Stage ------------------------------------------------------------------------------------------------------

func _focus(view: String) -> void:
	_face_btn.button_pressed = view == "face"
	_body_btn.button_pressed = view == "body"
	var hgt := float(look.get("height", 1.0))
	_face_view = view == "face"
	# close up, the hero keeps their head still (the idle fidgets look down and away)
	preview.hold_fidgets = _face_view or _posing
	if preview.no_helm != _face_view:
		preview.no_helm = _face_view
		preview.dress(hero)
	if _face_view:
		if preview.visual and not _posing:
			preview.visual.interrupt_fidget()
		preview.focus(1.64 * hgt, 1.75)
	else:
		preview.focus(1.02, 5.2)

func _pose(anim: StringName) -> void:
	var v := preview.visual
	if v == null:
		return
	v.stop_action()
	_posing = anim == &"hero_walk" or anim == &"hero_run"
	preview.hold_fidgets = _posing or _face_view
	if anim == &"strike":
		preview.play(STRIKES.get(_class(), &"sword_2"))
	elif anim == &"taunt":
		preview.play(&"taunt")
	elif anim != &"" and v.has_anim(anim):
		v.hold_action(anim, 1.0, 0.25)

func _toggle_gear() -> void:
	preview.bare = not _gear_btn.button_pressed
	preview.dress(hero)

# ---- Colour mixer -----------------------------------------------------------------------------------------------

func _build_mixer() -> void:
	_mixer = PopupPanel.new()
	add_child(_mixer)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(420, 0)
	v.add_theme_constant_override("separation", 8)
	_mixer.add_child(v)
	v.add_child(UITheme.title("Mix a colour", 24, UITheme.GOLD))
	_mix_swatch = ColorRect.new()
	_mix_swatch.custom_minimum_size = Vector2(0, 54)
	v.add_child(_mix_swatch)
	for n in ["Hue", "Richness", "Brightness"]:
		v.add_child(UITheme.label(n, 17, UITheme.PARCHMENT, UITheme.body_bold()))
		var s := HSlider.new()
		s.min_value = 0.0
		s.max_value = 1.0
		s.step = 0.004
		s.custom_minimum_size = Vector2(0, 34)
		_style_slider(s)
		s.value_changed.connect(func(_x: float) -> void: _mixed())
		v.add_child(s)
		_mix_sliders.append(s)
	var done_b := UIWindow.button("Use This Colour", func() -> void:
		_mixer.hide()
		_fill_page(), &"PrimaryButton", 0.0)
	v.add_child(done_b)

func _open_mixer(key: String) -> void:
	_mixer_target = ""
	var c := HeroLook.color(look, key)
	_mix_sliders[0].value = c.h
	_mix_sliders[1].value = c.s
	_mix_sliders[2].value = c.v
	_mix_swatch.color = c
	_mixer_target = key
	_mixer.popup_centered()

func _mixed() -> void:
	var c := Color.from_hsv(_mix_sliders[0].value, _mix_sliders[1].value, _mix_sliders[2].value)
	_mix_swatch.color = c
	if _mixer_target != "":
		_change(_mixer_target, c.to_html(false))

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and e.keycode == KEY_Z and e.ctrl_pressed:
		_undo_last()
		get_viewport().set_input_as_handled()

# ---- Small widgets ----------------------------------------------------------------------------------------------

## A round colour swatch.
class Swatch extends Control:
	signal picked
	var color := Color.WHITE
	var chosen := false
	var _hover := false

	func _init(c: Color, is_chosen: bool) -> void:
		color = c
		chosen = is_chosen
		custom_minimum_size = Vector2(44, 44)
		mouse_filter = Control.MOUSE_FILTER_STOP
		mouse_entered.connect(func() -> void:
			_hover = true
			queue_redraw())
		mouse_exited.connect(func() -> void:
			_hover = false
			queue_redraw())

	func _draw() -> void:
		var c := size * 0.5
		var r := minf(size.x, size.y) * 0.5 - 3.0
		draw_circle(c, r + 2.0, UITheme.GOLD if chosen else (UITheme.BRONZE if _hover else UITheme.BRONZE_DIM))
		draw_circle(c, r - (1.5 if chosen else 0.0), Color(0.03, 0.025, 0.025))
		draw_circle(c, r - (3.0 if chosen else 1.5), color)

	func _gui_input(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			Audio.play_ui(&"ui_click")
			picked.emit()

## The little drawing beside each page's name.
class Glyph extends Control:
	var kind := ""

	func _init(k: String) -> void:
		kind = k
		custom_minimum_size = Vector2(36, 36)
		size = Vector2(36, 36)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _arc(c: Vector2, r: float, a0: float, a1: float, col: Color, w := 2.0) -> void:
		draw_arc(c, r, deg_to_rad(a0), deg_to_rad(a1), 20, col, w, true)

	func _draw() -> void:
		var g := UITheme.GOLD
		var b := UITheme.BRONZE
		var c := Vector2(18, 18)
		match kind:
			"looks":
				draw_rect(Rect2(6, 6, 24, 24), b, false, 2.0)
				for p in [Vector2(12, 12), Vector2(24, 12), Vector2(18, 18), Vector2(12, 24), Vector2(24, 24)]:
					draw_circle(p, 2.2, g)
			"body":
				draw_circle(Vector2(18, 7), 4.0, g)
				draw_line(Vector2(18, 11), Vector2(18, 23), b, 2.5)
				draw_line(Vector2(8, 15), Vector2(28, 15), b, 2.5)
				draw_line(Vector2(18, 23), Vector2(11, 33), b, 2.5)
				draw_line(Vector2(18, 23), Vector2(25, 33), b, 2.5)
			"skin":
				draw_colored_polygon(PackedVector2Array([Vector2(18, 3), Vector2(28, 21), Vector2(18, 33), Vector2(8, 21)]), b)
				draw_circle(Vector2(18, 22), 7.0, g)
			"face":
				draw_set_transform(c, 0.0, Vector2(0.8, 1.0))
				draw_arc(Vector2.ZERO, 14.0, 0.0, TAU, 28, b, 2.5, true)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
				draw_circle(Vector2(13, 15), 1.8, g)
				draw_circle(Vector2(23, 15), 1.8, g)
				_arc(Vector2(18, 20), 6.0, 30, 150, g)
			"eyes":
				_arc(Vector2(18, 26), 15.0, 215, 325, b, 2.5)
				_arc(Vector2(18, 10), 15.0, 35, 145, b, 2.5)
				draw_circle(c, 5.0, g)
				draw_circle(c, 2.0, Color(0.05, 0.04, 0.04))
			"brows":
				_arc(Vector2(10, 24), 10.0, 215, 320, g, 3.5)
				_arc(Vector2(26, 24), 10.0, 220, 325, g, 3.5)
				draw_circle(Vector2(10, 24), 2.0, b)
				draw_circle(Vector2(26, 24), 2.0, b)
			"nose":
				draw_polyline(PackedVector2Array([Vector2(20, 5), Vector2(15, 24), Vector2(11, 28), Vector2(20, 31), Vector2(25, 28)]), g, 2.5, true)
			"mouth":
				_arc(Vector2(18, 8), 16.0, 50, 130, g, 3.0)
				_arc(Vector2(18, 28), 16.0, 230, 310, b, 2.5)
			"ears":
				_arc(Vector2(17, 16), 10.0, 150, 400, g, 2.8)
				_arc(Vector2(17, 18), 5.0, 170, 380, b, 2.0)
				draw_line(Vector2(15, 25), Vector2(17, 32), g, 2.8)
			"hair":
				for i in 5:
					_arc(Vector2(8 + i * 5, 34), 26.0 - i * 1.5, 250, 292, g if i % 2 == 0 else b, 2.4)
			"beard":
				draw_colored_polygon(PackedVector2Array([Vector2(7, 9), Vector2(29, 9), Vector2(26, 23), Vector2(18, 33), Vector2(10, 23)]), b)
				_arc(Vector2(18, 9), 6.0, 20, 160, Color(0.05, 0.04, 0.04), 3.0)
				draw_line(Vector2(18, 20), Vector2(18, 30), g, 1.5)
