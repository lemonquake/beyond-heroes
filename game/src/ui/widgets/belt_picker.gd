class_name BeltPicker
extends RefCounted
## The potion belt chooser (bh-011): a menu of what a belt key (Q / E; the HP / Mana orb on a phone) should use —
## "Strongest health draught", "Strongest mana draught", or any consumable the bag holds (draughts, elixirs, tonics,
## wards, salts, flasks, scrolls). Opened from the HUD belt slots (right-click) and the Inventory's belt row.

## Slot names as the player knows them: the bound key on a PC, the orb on a phone.
static func slot_name(slot: int) -> String:
	if Settings.touch_mode:
		return "HP orb" if slot == 0 else ("Mana orb" if slot == 1 else "Quick slot %d" % (slot - 1))
	var key := Settings.binding_text(HeroData.belt_action(slot))
	return key if key != "" else "Quick slot %d" % (slot - 1)

## Bind and tell the player.
static func bind(hero: HeroData, slot: int, id: StringName) -> void:
	if hero == null:
		return
	hero.set_belt(slot, id)
	Audio.play_ui(&"ui_equip")
	if hero.potion_belt[slot] == &"":
		Events.notify.emit("%s is empty now" % slot_name(slot), &"info")
	else:
		Events.notify.emit("%s now uses: %s" % [slot_name(slot), HeroData.belt_label(hero.potion_belt[slot])], &"info")
	hero.inventory.changed.emit()

## The menu entries: [id, label, icon] — the two automatic choices, then each distinct consumable in the bag.
static func choices(hero: HeroData) -> Array:
	var out := [[HeroData.BELT_AUTO_HEAL, "Strongest health draught (auto)", _icon(&"health_potion")],
		[HeroData.BELT_AUTO_MANA, "Strongest mana draught (auto)", _icon(&"mana_potion")]]
	var seen := {}
	for c in hero.inventory.cells:
		if c == null or not c.base.is_consumable() or seen.has(c.base.id):
			continue
		seen[c.base.id] = true
		out.append([c.base.id, "%s  ×%d" % [c.base.display_name, hero.inventory.count_of(c.base.id)], c.icon()])
	return out

static func _icon(base_id: StringName) -> Texture2D:
	var b := DB.item_base(base_id)
	return load(b.icon_path()) if b and ResourceLoader.exists(b.icon_path()) else null

## Pop the chooser up next to `anchor` (a HUD slot or the inventory belt row).
static func open(anchor: Control, hero: HeroData, slot: int) -> PopupMenu:
	if hero == null or anchor == null or not anchor.is_inside_tree():
		return null
	var menu := PopupMenu.new()
	menu.add_theme_constant_override("icon_max_width", 34)
	menu.add_theme_font_size_override("font_size", 22 if Settings.touch_mode else 17)
	menu.add_theme_constant_override("v_separation", 14 if Settings.touch_mode else 6)
	var cur: StringName = hero.potion_belt[slot]
	var list := choices(hero)
	menu.add_separator("%s uses…" % slot_name(slot))
	for i in list.size():
		var e: Array = list[i]
		menu.add_icon_radio_check_item(e[2], e[1], i)
		menu.set_item_checked(menu.get_item_index(i), e[0] == cur)
		if i == 1 and list.size() > 2:
			menu.add_separator("From your bag")
	if list.size() <= 2:
		menu.add_separator("No other consumables in your bag")
	if slot >= HeroData.ORB_SLOTS:
		menu.add_separator()
		menu.add_item("Clear this slot", 9999)
		if not Settings.touch_mode:
			menu.add_item("Change key (%s)…" % slot_name(slot), 9998)
	menu.id_pressed.connect(func(id: int) -> void:
		if id == 9999:
			bind(hero, slot, &"")
		elif id == 9998:
			HotkeyCapture.start(HeroData.belt_action(slot), anchor)
		else:
			bind(hero, slot, list[id][0]))
	menu.popup_hide.connect(menu.queue_free)
	anchor.get_tree().root.add_child(menu)
	var r := anchor.get_global_rect()
	var k := anchor.get_viewport().get_final_transform().x.x if anchor.get_viewport() else 1.0
	menu.reset_size()
	var at := Vector2(r.position.x, r.position.y - menu.size.y / maxf(k, 0.01) - 8.0)
	if at.y < 8.0:
		at.y = r.end.y + 8.0
	menu.popup(Rect2i(Vector2i((at * k).round()), Vector2i.ZERO))
	return menu
