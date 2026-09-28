class_name SkillButton
extends Control
## One hotbar slot: painted bezel, skill (or potion) icon, radial cooldown sweep with the seconds left, a flash when it
## becomes ready, a keybind plaque, and a clear "why not" state: blue wash + mana cost in red when Mana is short,
## grey when the weapon requirement is not met. Also used for potions (kind = &"potion"). An aura that is switched on
## wears a slowly turning halo (warm = offense, cool = defense).

signal activated(slot: SkillButton)
signal skill_dropped(slot: SkillButton, skill_id: StringName)
signal context(slot: SkillButton)                       # right-click (a belt slot opens its picker)
signal item_dropped(slot: SkillButton, item: ItemInstance)  # a bag item dropped on a belt slot

var action: StringName = &""        # input action shown on the plaque
var skill_id: StringName = &""
var kind := &"skill"                # skill | potion
var potion_base: StringName = &""
var index := 0
var _cd := 0.0
var _cd_total := 0.0
var _block := ""
var _count := -1
var _flash := 0.0
var _hover := false
var _mana_cost := 0.0
var _icon: Texture2D
var _aura: SkillDef                 # set when the slot holds an aura
var _aura_on := false

func _init(p_action := &"", size_px := 64.0) -> void:
	action = p_action
	custom_minimum_size = Vector2(size_px, size_px)
	mouse_filter = Control.MOUSE_FILTER_STOP

func _ready() -> void:
	mouse_entered.connect(func() -> void:
		_hover = true
		queue_redraw())
	mouse_exited.connect(func() -> void:
		_hover = false
		queue_redraw())

func set_skill(sid: StringName) -> void:
	skill_id = sid
	_icon = UIArt.skill_icon(sid) if sid != &"" else null
	var s := DB.skill(sid) if sid != &"" else null
	_aura = s if s and s.is_aura() else null
	queue_redraw()

func set_potion(base_id: StringName) -> void:
	kind = &"potion"
	potion_base = base_id
	var b := DB.item_base(base_id)
	_icon = load(b.icon_path()) if b and ResourceLoader.exists(b.icon_path()) else null
	queue_redraw()

func update_state(cd: float, cd_total: float, block := "", count := -1, mana_cost := 0.0) -> void:
	var was_cd := _cd > 0.0
	if was_cd and cd <= 0.0:
		_flash = 1.0
	if absf(cd - _cd) > 0.01 or cd_total != _cd_total or block != _block or count != _count:
		_cd = cd
		_cd_total = cd_total
		_block = block
		_count = count
		_mana_cost = mana_cost
		queue_redraw()

func _process(delta: float) -> void:
	if _aura:
		var on := Game.hero != null and Game.hero.active_aura == skill_id
		if on != _aura_on or on:
			_aura_on = on
			queue_redraw()
	if _flash > 0.0:
		_flash = maxf(0.0, _flash - delta * 2.2)
		queue_redraw()

func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	var m := UIArt.meta("slots/skill_slot.png")
	var ir_px: Array = m.get("icon_rect", [16, 16, 96, 96])
	var k := size.x / 128.0
	var ir := Rect2(Vector2(ir_px[0], ir_px[1]) * k, Vector2(ir_px[2], ir_px[3]) * k)
	var empty := (_icon == null)
	if not empty:
		var mod := Color(1, 1, 1)
		if kind == &"potion" and _count == 0:
			mod = Color(0.35, 0.35, 0.35)
		elif _block == "Not enough Mana":
			mod = Color(0.45, 0.55, 0.95)
		elif _block != "" and _block != "Cooldown":
			mod = Color(0.45, 0.45, 0.45)
		draw_texture_rect(_icon, ir, false, mod)
	var bez := UIArt.tex("slots/skill_slot_empty.png" if empty else "slots/skill_slot.png")
	if bez:
		draw_texture_rect(bez, r, false)
	if _aura and _aura_on:
		var hc := Color(1.0, 0.62, 0.3) if _aura.aura_kind == &"offense" else Color(0.55, 0.78, 1.0)
		var a0 := Time.get_ticks_msec() * 0.0015
		draw_arc(ir.get_center(), ir.size.x * 0.6, a0, a0 + TAU * 0.8, 40, Color(hc, 0.95), 3.0, true)
		draw_rect(ir, Color(hc, 0.12))
	# cooldown sweep: dark pie over the remaining fraction, clockwise from 12 o'clock
	if _cd > 0.0 and _cd_total > 0.0:
		var frac := clampf(_cd / _cd_total, 0.0, 1.0)
		var c := ir.get_center()
		var rad := ir.size.x * 0.72
		var pts := PackedVector2Array([c])
		var steps := 40
		for i in steps + 1:
			var a := -PI * 0.5 + TAU * (1.0 - frac) + TAU * frac * float(i) / float(steps)
			pts.append(c + Vector2(cos(a), sin(a)) * rad)
		var rect_poly := PackedVector2Array([ir.position, Vector2(ir.end.x, ir.position.y), ir.end, Vector2(ir.position.x, ir.end.y)])
		for poly in Geometry2D.intersect_polygons(pts, rect_poly):
			draw_colored_polygon(poly, Color(0.0, 0.0, 0.02, 0.68))
		var font := UITheme.number_font()
		var txt := ("%.1f" % _cd) if _cd < 3.0 else str(ceili(_cd))
		var fs := int(size.x * 0.3)
		var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var p2 := Vector2(c.x - w * 0.5, c.y + fs * 0.35)
		draw_string_outline(font, p2, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 5, Color(0, 0, 0, 0.9))
		draw_string(font, p2, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UITheme.PARCHMENT)
	if _flash > 0.0:
		draw_rect(ir, Color(0.75, 0.97, 1.0, _flash * 0.55))
		draw_rect(ir.grow(2.0 + (1.0 - _flash) * 6.0), Color(0.6, 0.95, 1.0, _flash), false, 2.0)
	if _hover and not empty:
		draw_rect(ir, Color(1.0, 0.9, 0.6, 0.12))
	var font2 := UITheme.number_font()
	# mana cost in red when unaffordable
	if _block == "Not enough Mana":
		var mt := str(roundi(_mana_cost))
		var fs3 := int(size.x * 0.22)
		draw_string_outline(font2, Vector2(ir.position.x + 3, ir.end.y - 4), mt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3, 4, Color(0, 0, 0, 0.9))
		draw_string(font2, Vector2(ir.position.x + 3, ir.end.y - 4), mt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs3, Color(0.55, 0.7, 1.0))
	if kind == &"potion" and _count >= 0:
		var ct := str(_count)
		var fs4 := int(size.x * 0.24)
		var cw := font2.get_string_size(ct, HORIZONTAL_ALIGNMENT_LEFT, -1, fs4).x
		var cp := Vector2(ir.end.x - cw - 2, ir.end.y - 3)
		draw_string_outline(font2, cp, ct, HORIZONTAL_ALIGNMENT_LEFT, -1, fs4, 4, Color(0, 0, 0, 0.9))
		draw_string(font2, cp, ct, HORIZONTAL_ALIGNMENT_LEFT, -1, fs4, UITheme.PARCHMENT)
	# keybind plaque
	var key := Settings.binding_text(action) if action != &"" else ""
	if key != "":
		var fs5 := int(size.x * 0.2)
		var kw := maxf(font2.get_string_size(key, HORIZONTAL_ALIGNMENT_LEFT, -1, fs5).x + 12.0, size.x * 0.36)
		var kr := Rect2(Vector2((size.x - kw) * 0.5, size.y - size.x * 0.16), Vector2(kw, size.x * 0.28))
		var badge := UIArt.style("slots/keybind_badge.png", [0, 0, 0, 0])
		draw_style_box(badge, kr)
		draw_string(font2, Vector2(kr.position.x + (kw - font2.get_string_size(key, HORIZONTAL_ALIGNMENT_LEFT, -1, fs5).x) * 0.5, kr.end.y - kr.size.y * 0.28),
			key, HORIZONTAL_ALIGNMENT_LEFT, -1, fs5, UITheme.PARCHMENT)

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
		activated.emit(self)
		accept_event()
	elif e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_RIGHT:
		context.emit(self)
		accept_event()

func _can_drop_data(_at: Vector2, data: Variant) -> bool:
	if kind == &"potion":
		return data is Dictionary and data.has("bh_item_slot") and data.bh_item_slot.item != null and data.bh_item_slot.item.base.is_consumable()
	return kind == &"skill" and data is Dictionary and data.has("bh_skill")

func _drop_data(_at: Vector2, data: Variant) -> void:
	if kind == &"potion":
		item_dropped.emit(self, data.bh_item_slot.item)
		return
	skill_dropped.emit(self, StringName(data.bh_skill))

func _get_drag_data(_at: Vector2) -> Variant:
	if kind != &"skill" or skill_id == &"":
		return null
	var t := TextureRect.new()
	t.texture = _icon
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.size = size * 0.8
	t.position = -size * 0.4
	var h := Control.new()
	h.add_child(t)
	set_drag_preview(h)
	return {"bh_skill": skill_id, "from_bar": index}
