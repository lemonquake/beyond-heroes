class_name GachaRevealWindow
extends UIWindow
## The reveal (bh-012): Relic Caches and Tempo summons open here. Each result waits face-down as a sealed card glowing
## in its rarity colour; the cards turn over one by one (or all at once) with a burst, a sound and — for the best
## results — a golden flare and a banner. Opens on top of any other window.
##
## A card: {title, sub, lines: [String], color: Color, stars: int, icon: Texture2D or null, rank: 0..4 (flourish size),
## badge: String (e.g. "NEW", "Resonance II")}.

const FLIP_TIME := 0.32
const AUTO_GAP := 0.42
const RANK_SOUND := [&"ui_click", &"ui_click", &"loot_rare", &"loot_legendary", &"level_up"]

var _cards_box: HBoxContainer
var _flash: ColorRect
var _banner: Label
var _hint: Label
var _next_btn: Button
var _all_btn: Button
var _cards: Array = []        # [{panel, face, back, data, open}]
var _auto := false
var _on_done := Callable()
var _auto_t := 0.0

func _init() -> void:
	super._init("Revealed", Vector2(1640, 760))
	modal = true

func _build() -> void:
	_banner = UITheme.label("", 30, UITheme.GOLD, UITheme.title_font())
	_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(_banner)
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(0, 520)
	holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(holder)
	_flash = ColorRect.new()
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.color = Color(1, 1, 1, 0)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(_flash)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.add_child(center)
	_cards_box = hbox(14)
	center.add_child(_cards_box)
	var row := hbox(16)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(row)
	_hint = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	row.add_child(_hint)
	_next_btn = button("Reveal next", func() -> void: _reveal_next(), &"", 220.0)
	row.add_child(_next_btn)
	_all_btn = button("Reveal all", func() -> void: _auto = true, &"", 220.0)
	row.add_child(_all_btn)
	row.add_child(button("Done", func() -> void: close_window(), &"", 200.0))
	closed.connect(func() -> void:
		if _on_done.is_valid():
			var cb := _on_done
			_on_done = Callable()
			cb.call())

## Lay out face-down cards and open. `auto` turns them over by itself.
func show_cards(p_title: String, cards: Array, auto := false, on_done := Callable()) -> void:
	if not _built:
		_make_frame()
		_build()
		_built = true
	set_title(p_title)
	_on_done = on_done
	for c in _cards_box.get_children():
		c.queue_free()
	_cards.clear()
	_banner.text = ""
	var w := clampf(1500.0 / maxf(1.0, float(cards.size())) - 14.0, 118.0, 300.0)
	var h := 470.0 if cards.size() <= 5 else 360.0
	for d: Dictionary in cards:
		_cards.append(_make_card(d, Vector2(w, h)))
	_auto = auto
	_auto_t = 0.5
	_update_buttons()
	open()

func _make_card(d: Dictionary, sz: Vector2) -> Dictionary:
	var col: Color = d.get("color", UITheme.BRONZE)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = sz
	panel.pivot_offset = sz * 0.5
	panel.add_theme_stylebox_override("panel", UITheme.panel_style(UITheme.BG_INSET, col, 6, 3, 18))
	_cards_box.add_child(panel)
	# face-down: a sealed back glowing in the rarity colour (you can guess, but not read)
	var back := VBoxContainer.new()
	back.alignment = BoxContainer.ALIGNMENT_CENTER
	var sigil := UITheme.label("✦", int(sz.x * 0.4), col.lerp(Color.WHITE, 0.25), UITheme.title_font())
	sigil.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	back.add_child(sigil)
	var sealed := UITheme.label("Sealed", 16, UITheme.TEXT_DIM, UITheme.body_font())
	sealed.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	back.add_child(sealed)
	panel.add_child(back)
	var face := VBoxContainer.new()
	face.add_theme_constant_override("separation", 6)
	face.visible = false
	var tex: Texture2D = d.get("icon")
	if tex:
		var tr := TextureRect.new()
		tr.texture = tex
		tr.custom_minimum_size = Vector2(0, minf(sz.x * 0.6, 150.0))
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		face.add_child(tr)
	var small := sz.x < 180.0
	var t := UITheme.label(String(d.get("title", "")), 15 if small else 21, col.lerp(Color.WHITE, 0.15), UITheme.title_font())
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	face.add_child(t)
	if String(d.get("sub", "")) != "":
		var s := UITheme.label(String(d.sub), 12 if small else 15, UITheme.PARCHMENT, UITheme.body_font())
		s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		s.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		face.add_child(s)
	var st := int(d.get("stars", 0))
	if st > 0:
		var sl := UITheme.label(ItemNames.star_text(st), 18 if small else 24, ItemNames.star_color(st), UITheme.body_font())
		sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		face.add_child(sl)
	if String(d.get("badge", "")) != "":
		var b := UITheme.label(String(d.badge), 14, UITheme.GOOD, UITheme.body_bold())
		b.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		face.add_child(b)
	if not small:
		for line in d.get("lines", []):
			var l := UITheme.label(String(line), 13, UITheme.TEXT, UITheme.body_font())
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			face.add_child(l)
	panel.add_child(face)
	# face-down cards breathe
	var tw := panel.create_tween().set_loops()
	tw.tween_property(panel, "modulate", Color(1.12, 1.12, 1.12), 0.8)
	tw.tween_property(panel, "modulate", Color.WHITE, 0.8)
	return {"panel": panel, "face": face, "back": back, "data": d, "open": false, "breath": tw}

func _process(delta: float) -> void:
	if not visible or not _auto:
		return
	_auto_t -= delta
	if _auto_t <= 0.0:
		_auto_t = AUTO_GAP
		if not _reveal_next():
			_auto = false

## Turn over the next face-down card. False when every card is already face up.
func _reveal_next() -> bool:
	for c: Dictionary in _cards:
		if c.open:
			continue
		c.open = true
		var p: PanelContainer = c.panel
		(c.breath as Tween).kill()
		p.modulate = Color.WHITE
		var d: Dictionary = c.data
		var rank := int(d.get("rank", 0))
		var tw := p.create_tween()
		tw.tween_property(p, "scale", Vector2(0.02, 1.08), FLIP_TIME * 0.5).set_trans(Tween.TRANS_SINE)
		tw.tween_callback(func() -> void:
			(c.back as Control).visible = false
			(c.face as Control).visible = true)
		tw.tween_property(p, "scale", Vector2(1.0 + 0.06 * rank, 1.0 + 0.06 * rank), FLIP_TIME * 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(p, "scale", Vector2.ONE, 0.25)
		_burst(d.get("color", Color.WHITE), rank)
		if rank >= 3:
			_banner.text = String(d.get("banner", "A radiant find!" if rank == 3 else "Legendary!"))
			_banner.add_theme_color_override("font_color", d.get("color", UITheme.GOLD))
		Audio.play_ui(RANK_SOUND[clampi(rank, 0, RANK_SOUND.size() - 1)] if Audio.has_sound(RANK_SOUND[clampi(rank, 0, RANK_SOUND.size() - 1)]) else &"ui_click")
		_update_buttons()
		return true
	_update_buttons()
	return false

func _burst(col: Color, rank: int) -> void:
	_flash.color = Color(col.r, col.g, col.b, 0.12 + 0.12 * rank)
	var tw := _flash.create_tween()
	tw.tween_property(_flash, "color:a", 0.0, 0.35 + 0.15 * rank)

func _update_buttons() -> void:
	var left := _cards.filter(func(c): return not c.open).size()
	_next_btn.disabled = left == 0
	_all_btn.disabled = left == 0
	_hint.text = "%d sealed" % left if left > 0 else "All revealed"

## Cards for items (Relic Caches): the gacha name, rarity, stars and the first enchantments.
static func item_card(it: ItemInstance) -> Dictionary:
	var st := it.stars()
	var rank := 0
	if it.rarity >= BH.Rarity.LEGENDARY or st == 5:
		rank = 4
	elif it.rarity >= BH.Rarity.MYTHICAL:
		rank = 3
	elif it.rarity >= BH.Rarity.MASTER or st >= 4:
		rank = 2
	elif it.rarity >= BH.Rarity.ELITE:
		rank = 1
	var lines: Array = []
	for l in it.affix_lines().slice(0, 3):
		lines.append(l)
	for pid in it.powers:
		var p := DB.power(StringName(pid))
		if p:
			lines.append("%s: %s" % [p.display_name, p.description])
	var sub := "%s %s" % [it.rarity_name(), it.base.display_name]
	if it.epithet != "":
		sub = "%s\n%s" % [it.epithet, sub]
	return {"title": it.short_name(), "sub": sub, "lines": lines, "color": it.color(), "stars": st, "icon": it.icon(), "rank": rank,
		"badge": "PERFECT ROLLS" if it.is_perfect() else "", "banner": "%s!" % it.rarity_name() if rank >= 3 else ""}
