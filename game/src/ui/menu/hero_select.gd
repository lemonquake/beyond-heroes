class_name HeroSelect
extends Control
## Hero Selection. Centre: the chosen hero in 3D on a lit plinth (drag to rotate, wheel to zoom, idles play).
## Left: class cards (Knight, Mage, Ranger, Shadowblade). Right: class name and tagline, description, difficulty, major attributes, class resource,
## strengths, weaknesses, starting equipment (hover for item tooltips) and starting skills (hover for details).
## Bottom: hero name, game difficulty, save slot; Back / Begin. Emits begin(class_id, name, slot, difficulty).

signal begin(class_id: StringName, hero_name: String, slot: int, difficulty: int, look: Dictionary)
signal back

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
## Suggested hero names per class (replaced only while the player has not typed their own).
const DEFAULT_NAMES := {&"knight": "Aldric", &"mage": "Seraphine", &"ranger": "Tamsin", &"shadowblade": "Corvin"}

var class_id: StringName = &"knight"
var preview: CharacterPreview
## bh-023: the look made in the creator (HeroLook; empty = the plain hero). Kept while the player goes back and forth.
var look := {}
var creator: HeroCreator
var _cards := {}
var _title: Label
var _tagline: Label
var _desc: Label
var _stars: HBoxContainer
var _attrs: HBoxContainer
var _resource: Label
var _resource_desc: Label
var _strengths: VBoxContainer
var _weaknesses: VBoxContainer
var _gear: HBoxContainer
var _skills: HBoxContainer
var _name: LineEdit
var _difficulty: OptionButton
var _slot: OptionButton
var _slot_warn: Label
var _begin_btn: Button

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)

func _ready() -> void:
	theme = UITheme.theme()
	var bg := ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.02, 0.02, 0.03)
	add_child(bg)
	var backdrop := TextureRect.new()
	backdrop.texture = UIArt.tex("tree/tree_bg_knight.png")
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.modulate = Color(0.55, 0.55, 0.6)
	backdrop.name = "Backdrop"
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
	glow.offset_left = -330
	glow.offset_right = 330
	glow.offset_top = -330
	glow.offset_bottom = -150
	add_child(glow)
	preview = CharacterPreview.new(Vector2i(1200, 1800))
	preview.set_anchors_preset(Control.PRESET_CENTER)
	preview.offset_left = -330
	preview.offset_right = 330
	preview.offset_top = -470
	preview.offset_bottom = 400
	add_child(preview)
	var title := UITheme.title("Choose Your Hero", 40, UITheme.GOLD)
	title.set_anchors_preset(Control.PRESET_CENTER_TOP)
	title.offset_left = -400
	title.offset_right = 400
	title.offset_top = 26
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)
	_build_cards()
	_build_details()
	_build_footer()
	_select(&"knight")
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.5)

func _build_cards() -> void:
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	col.offset_left = 60
	col.offset_right = 400
	col.offset_top = -260
	col.offset_bottom = 200
	col.offset_top = -290
	col.offset_bottom = 230
	col.add_theme_constant_override("separation", 12)
	add_child(col)
	for id in CLASSES:
		var cls := DB.class_def(id)
		var card := Button.new()
		card.toggle_mode = true
		card.custom_minimum_size = Vector2(330, 112)
		card.text = ""
		var h := HBoxContainer.new()
		h.set_anchors_preset(Control.PRESET_FULL_RECT)
		h.offset_left = 26
		h.offset_right = -20
		h.add_theme_constant_override("separation", 16)
		h.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(h)
		var ic := TextureRect.new()
		ic.texture = UIArt.portrait(String(id))
		ic.custom_minimum_size = Vector2(84, 84)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(ic)
		var v := VBoxContainer.new()
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		h.add_child(v)
		var n := UITheme.title(cls.display_name, 28 if cls.display_name.length() <= 8 else 24, UITheme.PARCHMENT)
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(n)
		var t := UITheme.label(cls.class_resource_name, 16, UITheme.TEXT_DIM, UITheme.body_font())
		t.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(t)
		card.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			_select(id))
		card.mouse_entered.connect(func() -> void: Audio.play_ui(&"ui_hover"))
		col.add_child(card)
		_cards[id] = card

func _build_details() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	panel.offset_left = -640
	panel.offset_right = -50
	panel.offset_top = 100
	panel.offset_bottom = -200
	add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(v)
	_title = UITheme.title("", 40, UITheme.GOLD)
	v.add_child(_title)
	_tagline = UITheme.label("", 18, UITheme.PARCHMENT, UITheme.body_font())
	v.add_child(_tagline)
	_desc = UITheme.label("", 17, UITheme.TEXT, UITheme.body_font())
	_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(_desc)
	var dh := HBoxContainer.new()
	dh.add_theme_constant_override("separation", 10)
	v.add_child(dh)
	dh.add_child(UITheme.label("Difficulty", 17, UITheme.TEXT_DIM, UITheme.body_bold()))
	_stars = HBoxContainer.new()
	dh.add_child(_stars)
	var ah := HBoxContainer.new()
	ah.add_theme_constant_override("separation", 8)
	v.add_child(ah)
	ah.add_child(UITheme.label("Major attributes", 17, UITheme.TEXT_DIM, UITheme.body_bold()))
	_attrs = HBoxContainer.new()
	_attrs.add_theme_constant_override("separation", 12)
	ah.add_child(_attrs)
	v.add_child(UIWindow.section("Class Resource"))
	_resource = UITheme.label("", 19, Color(1.0, 0.7, 0.35), UITheme.body_bold())
	v.add_child(_resource)
	_resource_desc = UITheme.label("", 16, UITheme.TEXT, UITheme.body_font())
	_resource_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(_resource_desc)
	var sw := HBoxContainer.new()
	sw.add_theme_constant_override("separation", 18)
	v.add_child(sw)
	var sv := VBoxContainer.new()
	sv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sw.add_child(sv)
	sv.add_child(UIWindow.section("Strengths"))
	_strengths = VBoxContainer.new()
	sv.add_child(_strengths)
	var wv := VBoxContainer.new()
	wv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sw.add_child(wv)
	wv.add_child(UIWindow.section("Weaknesses"))
	_weaknesses = VBoxContainer.new()
	wv.add_child(_weaknesses)
	v.add_child(UIWindow.section("Starting Equipment"))
	_gear = HBoxContainer.new()
	_gear.add_theme_constant_override("separation", 6)
	v.add_child(_gear)
	v.add_child(UIWindow.section("Starting Skills"))
	_skills = HBoxContainer.new()
	_skills.add_theme_constant_override("separation", 6)
	v.add_child(_skills)

func _build_footer() -> void:
	var bar := PanelContainer.new()
	bar.theme_type_variation = &"GlassPanel"
	bar.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bar.offset_left = 60
	bar.offset_right = -50
	bar.offset_top = -160
	bar.offset_bottom = -40
	add_child(bar)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 18)
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.add_child(h)
	h.add_child(UIWindow.button("Back", func() -> void: back.emit(), &"", 170.0))
	var nv := VBoxContainer.new()
	h.add_child(nv)
	nv.add_child(UITheme.label("Hero name", 15, UITheme.TEXT_DIM, UITheme.body_bold()))
	_name = LineEdit.new()
	_name.max_length = 18
	_name.custom_minimum_size = Vector2(300, 48)
	_name.placeholder_text = "Name your hero"
	_name.text_changed.connect(func(_t): _validate())
	nv.add_child(_name)
	var dv := VBoxContainer.new()
	h.add_child(dv)
	dv.add_child(UITheme.label("Difficulty", 15, UITheme.TEXT_DIM, UITheme.body_bold()))
	_difficulty = OptionButton.new()
	for d in DataEnemies.DIFFICULTY:
		_difficulty.add_item(String(d.name))
	_difficulty.selected = 1
	_difficulty.custom_minimum_size = Vector2(220, 48)
	dv.add_child(_difficulty)
	TooltipLayer.attach(_difficulty, func() -> Control: return Tips.text(
		"Adventurer: forgiving. Veteran: the intended challenge. Heroic: tougher, smarter enemies and more elites. Mythic: relentless.\n\nHigher difficulty raises enemy health, damage, aggression, skill use, status resistance and elite frequency — not just health.", "Difficulty"))
	var slv := VBoxContainer.new()
	h.add_child(slv)
	slv.add_child(UITheme.label("Save slot", 15, UITheme.TEXT_DIM, UITheme.body_bold()))
	_slot = OptionButton.new()
	_slot.custom_minimum_size = Vector2(300, 48)
	for s in SaveSystem.SLOTS:
		var sum := _slot_summary(s)
		_slot.add_item("Slot %d — %s" % [s + 1, "Empty" if sum.is_empty() else "%s, level %d" % [sum["name"], sum["level"]]])
		if SaveSystem.scope == "official" and not sum.is_empty():
			_slot.set_item_disabled(s, true)
	_slot.selected = _first_empty_slot()
	_slot.item_selected.connect(func(_i): _validate())
	slv.add_child(_slot)
	_slot_warn = UITheme.label("", 14, Color(1.0, 0.6, 0.45), UITheme.body_font())
	slv.add_child(_slot_warn)
	_begin_btn = UIWindow.button("Next: Appearance", _open_creator, &"PrimaryButton", 270.0)
	_begin_btn.custom_minimum_size.y = 64
	h.add_child(_begin_btn)

static func _first_empty_slot() -> int:
	for s in SaveSystem.SLOTS:
		if _slot_summary(s).is_empty():
			return s
	return 0

static func _slot_summary(slot: int) -> Dictionary:
	return Official.slot_summary(slot) if SaveSystem.scope == "official" else SaveSystem.slot_summary(slot)

func _select(id: StringName) -> void:
	class_id = id
	for k in _cards:
		(_cards[k] as Button).button_pressed = k == id
	var cls := DB.class_def(id)
	preview.look = look
	preview.show_class(id)
	preview.play(StringName("idle_%s" % id))
	(get_node("Backdrop") as TextureRect).texture = UIArt.tex("tree/tree_bg_%s.png" % id)
	_title.text = cls.display_name
	_tagline.text = cls.tagline
	_desc.text = cls.description
	for c in _stars.get_children():
		c.queue_free()
	for i in 3:
		var st := TextureRect.new()
		st.texture = UIArt.ui_icon("crown")
		st.custom_minimum_size = Vector2(24, 24)
		st.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		st.modulate = UITheme.GOLD if i < cls.difficulty else Color(0.3, 0.28, 0.26)
		_stars.add_child(st)
	for c in _attrs.get_children():
		c.queue_free()
	for a in cls.major_attributes:
		var box := HBoxContainer.new()
		box.add_theme_constant_override("separation", 4)
		var ic := TextureRect.new()
		ic.texture = UIArt.attribute_icon(a)
		ic.custom_minimum_size = Vector2(26, 26)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		box.add_child(ic)
		box.add_child(UITheme.label(BH.ATTRIBUTE_NAMES[a], 16, UITheme.PARCHMENT, UITheme.body_font()))
		_attrs.add_child(box)
	_resource.text = cls.class_resource_name
	_resource_desc.text = cls.resource_desc
	for c in _strengths.get_children():
		c.queue_free()
	for c in _weaknesses.get_children():
		c.queue_free()
	for s in cls.strengths:
		_strengths.add_child(_bullet(s, UITheme.GOOD))
	for w in cls.weaknesses:
		_weaknesses.add_child(_bullet(w, Color(1.0, 0.6, 0.45)))
	for c in _gear.get_children():
		c.queue_free()
	for bid in cls.starting_items:
		var it := DB.make_item(bid, BH.Rarity.BEGINNER, 1, hash(String(bid)))
		if it == null:
			continue
		var slot := ItemSlot.new(ItemSlot.Kind.DISPLAY, 60.0)
		slot.set_item(it)
		slot.drag_enabled = false
		slot.hovered.connect(func(sl, inside): (TooltipLayer.show_for(sl, func() -> Control: return Tips.item(it, {"compare": false, "hero": null})) if inside else TooltipLayer.hide_for(sl)))
		_gear.add_child(slot)
	for c in _skills.get_children():
		c.queue_free()
	for sid in cls.starting_skills:
		var b := SkillButton.new(&"", 60.0)
		b.set_skill(sid)
		TooltipLayer.attach(b, func() -> Control: return Tips.skill(sid, null))
		_skills.add_child(b)
	if _name.text.strip_edges() == "" or _name.text in DEFAULT_NAMES.values():
		_name.text = DEFAULT_NAMES.get(id, "Hero")
	_validate()

func _bullet(t: String, col: Color) -> Control:
	var l := UITheme.label("•  " + t, 16, col.lerp(UITheme.TEXT, 0.35), UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(250, 0)
	return l

func _validate() -> void:
	var occupied := not _slot_summary(_slot.selected).is_empty()
	_slot_warn.text = "This will replace the saved hero in this slot." if occupied else ""
	_begin_btn.disabled = _name.text.strip_edges().length() < 2 or (SaveSystem.scope == "official" and occupied)

## The creator takes over the screen; Back returns here with the look kept, Begin Journey starts the game.
func _open_creator() -> void:
	creator = HeroCreator.new()
	creator.class_id = class_id
	creator.look = look
	creator.hero_name = _name.text.strip_edges()
	add_child(creator)
	preview.visible = false                 # (one plinth renders at a time)
	creator.back.connect(func() -> void:
		look = HeroLook.to_save(creator.look)
		preview.visible = true
		preview.look = look
		preview.set_look(look)
		creator.queue_free()
		creator = null)
	creator.done.connect(func(l: Dictionary) -> void:
		look = l
		_begin())

## Back from the phone's button or Escape: out of the creator first.
func go_back() -> void:
	if creator and is_instance_valid(creator):
		creator.back.emit()
	else:
		back.emit()

func _begin() -> void:
	var go := func() -> void: begin.emit(class_id, _name.text.strip_edges(), _slot.selected, _difficulty.selected, look)
	if SaveSystem.scope == "official" and not _slot_summary(_slot.selected).is_empty():
		_slot_warn.text = "Choose an empty official slot. Existing official characters are never overwritten."
		return
	if not _slot_summary(_slot.selected).is_empty():
		var dlg := ConfirmDialog.new()
		add_child(dlg)
		dlg.ask("Replace Save", "Slot %d already holds a hero. Replace it with a new %s?" % [_slot.selected + 1, DB.class_def(class_id).display_name],
			func() -> void:
				dlg.queue_free()
				go.call(), "Replace", true)
	else:
		go.call()
