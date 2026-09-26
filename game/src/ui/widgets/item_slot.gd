class_name ItemSlot
extends Control
## One item cell (inventory, equipment, shop, buyback, loot). Painted well + icon + rarity frame and glow (Elite and
## above pulse), stack count, lock/favorite/junk badges, red wash when the hero cannot use it, drag and drop.
## The owner decides what clicks and drops mean; the slot only reports them.

signal clicked(slot: ItemSlot, button: int, shift: bool, ctrl: bool)
signal double_clicked(slot: ItemSlot)
signal dropped(from: ItemSlot, to: ItemSlot)
signal hovered(slot: ItemSlot, inside: bool)

enum Kind { INVENTORY, EQUIPMENT, SHOP, BUYBACK, DISPLAY }

var kind := Kind.INVENTORY
var index := -1                    # inventory cell / stock index
var equip_slot: StringName = &""   # for EQUIPMENT slots
var item: ItemInstance
var glyph: Texture2D               # empty equipment slot silhouette
var selected := false
var disabled := false
var locked_cell := false
var unusable := false
var dim := false                   # filtered out by search / category
var price := -1                    # shop label under the icon (-1 = none)
var price_ok := true
var drag_enabled := true
var _hover := false
var _t := 0.0

const BADGE := 18.0

func _init(p_kind := Kind.INVENTORY, size_px := 64.0) -> void:
	kind = p_kind
	custom_minimum_size = Vector2(size_px, size_px)
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE

func _ready() -> void:
	mouse_entered.connect(func() -> void:
		_hover = true
		hovered.emit(self, true)
		queue_redraw())
	mouse_exited.connect(func() -> void:
		_hover = false
		hovered.emit(self, false)
		queue_redraw())

func set_item(it: ItemInstance, p_unusable := false) -> void:
	item = it
	unusable = p_unusable
	queue_redraw()

func _process(delta: float) -> void:
	if item != null and item.rarity >= BH.Rarity.ELITE and is_visible_in_tree():
		_t += delta
		queue_redraw()

func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	var bg := "slots/slot.png"
	if kind == Kind.EQUIPMENT:
		bg = "slots/equip_slot.png"
	elif locked_cell:
		bg = "slots/slot_locked.png"
	elif disabled:
		bg = "slots/slot_disabled.png"
	elif selected:
		bg = "slots/slot_selected.png"
	elif _hover:
		bg = "slots/slot_hover.png"
	var bt := UIArt.tex(bg)
	if bt:
		draw_texture_rect(bt, r, false, Color(1, 1, 1, 0.45 if dim else 1.0))
	if kind == Kind.EQUIPMENT and (_hover or selected):
		var hv := UIArt.tex("slots/slot_hover.png")
		if hv:
			draw_texture_rect(hv, r.grow(-size.x * 0.08), false, Color(1, 1, 1, 0.55))
	var inset := size.x * (0.16 if kind == Kind.EQUIPMENT else 0.12)
	var ir := r.grow(-inset)
	if item == null:
		if glyph:
			draw_texture_rect(glyph, r.grow(-size.x * 0.14), false, Color(1, 1, 1, 0.55))
		return
	var a := 0.4 if dim else 1.0
	# rarity glow under the icon (pulsing for the high tiers)
	var gl := UIArt.rarity_glow(item.rarity)
	if gl:
		var pulse := 0.65 + 0.35 * sin(_t * (2.2 + 0.3 * float(item.rarity - 5)))
		draw_texture_rect(gl, r, false, Color(1, 1, 1, pulse * a))
	var ic := item.icon()
	if ic:
		draw_texture_rect(ic, ir, false, Color(1, 1, 1, a))
	if unusable:
		draw_rect(ir, Color(0.75, 0.08, 0.05, 0.32 * a))
	var fr := UIArt.rarity_frame(item.rarity)
	if fr and item.is_equipment():
		draw_texture_rect(fr, r, false, Color(1, 1, 1, a))
	elif item.rarity >= BH.Rarity.BASIC:
		draw_rect(r.grow(-3), Color(item.color(), 0.6 * a), false, 2.0)
	# stack count
	var font := UITheme.number_font()
	if item.count > 1:
		var txt := str(item.count)
		var fs := int(size.x * 0.24)
		var w := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var p := Vector2(size.x - w - size.x * 0.1, size.y - size.y * 0.1)
		draw_string_outline(font, p, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(0, 0, 0, 0.9))
		draw_string(font, p, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UITheme.PARCHMENT)
	# badges
	var bx := 3.0
	for b in [["lock", item.locked, UITheme.GOLD], ["favorite", item.favorite, Color(1.0, 0.8, 0.3)], ["junk", item.junk, Color(0.8, 0.7, 0.6)]]:
		if b[1]:
			var t := UIArt.ui_icon(b[0])
			if t:
				draw_texture_rect(t, Rect2(Vector2(bx, 3.0), Vector2(BADGE, BADGE)), false, b[2])
				bx += BADGE - 2.0
	if price >= 0:
		var pt := str(price)
		var fs2 := int(size.x * 0.2)
		var pw := font.get_string_size(pt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2).x
		var pp := Vector2((size.x - pw) * 0.5 + 6.0, size.y + fs2 + 2.0)
		var gi := UIArt.ui_icon("gold")
		if gi:
			draw_texture_rect(gi, Rect2(pp + Vector2(-fs2 - 2.0, -fs2 + 2.0), Vector2(fs2, fs2)), false, UITheme.GOLD)
		draw_string_outline(font, pp, pt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, 4, Color(0, 0, 0, 0.9))
		draw_string(font, pp, pt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, UITheme.GOLD if price_ok else UITheme.BAD)

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed:
		if e.double_click and e.button_index == MOUSE_BUTTON_LEFT:
			double_clicked.emit(self)
		else:
			clicked.emit(self, e.button_index, e.shift_pressed, e.ctrl_pressed or e.meta_pressed)
		accept_event()

func _get_drag_data(_at: Vector2) -> Variant:
	if item == null or not drag_enabled:
		return null
	var prev := TextureRect.new()
	prev.texture = item.icon()
	prev.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	prev.size = size * 0.9
	prev.position = -size * 0.45
	prev.modulate = Color(1, 1, 1, 0.85)
	var holder := Control.new()
	holder.add_child(prev)
	set_drag_preview(holder)
	return {"bh_item_slot": self}

func _can_drop_data(_at: Vector2, data: Variant) -> bool:
	return data is Dictionary and data.has("bh_item_slot") and data.bh_item_slot != self and not locked_cell

func _drop_data(_at: Vector2, data: Variant) -> void:
	dropped.emit(data.bh_item_slot, self)
