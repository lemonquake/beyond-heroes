class_name Equipment
extends RefCounted
## The hero's 13 equipment slots (exact spec layout) and the rules for filling them.

signal changed

var slots := {}              # slot StringName -> ItemInstance or null

func _init() -> void:
	for s in BH.SLOTS:
		slots[s] = null

func get_item(slot: StringName) -> ItemInstance:
	return slots.get(slot)

func weapon_type_of(item: ItemInstance) -> WeaponTypeDef:
	if item == null or not item.base.is_weapon():
		return null
	return DB.weapon_type(item.base.weapon_type)

## Why an item cannot go into a slot ("" when it can). attrs/level are the wearer's base values.
func check(item: ItemInstance, slot: StringName, level: int, attrs: Dictionary) -> String:
	if item == null or not item.is_equipment():
		return "Cannot be equipped"
	var allowed: Array = BH.CATEGORY_SLOTS.get(item.base.category, [])
	if not allowed.has(slot):
		return "Does not fit in %s" % BH.SLOT_NAMES[slot]
	if level < item.base.level_req:
		return "Requires level %d" % item.base.level_req
	for a in item.base.requirements:
		if int(attrs.get(a, 0)) < int(item.base.requirements[a]):
			return "Requires %d %s" % [item.base.requirements[a], BH.ATTRIBUTE_NAMES[a]]
	if slot == &"sub_weapon" and item.base.is_weapon():
		var wt := weapon_type_of(item)
		if wt == null or not wt.dual_wieldable or wt.two_handed:
			return "Only one-handed weapons can be held in the sub hand"
		var main_wt := weapon_type_of(slots[&"main_weapon"])
		if main_wt == null:
			return "Equip a main weapon first"
		if not main_wt.dual_wieldable:
			return "%s cannot be dual wielded" % main_wt.display_name
	return ""

## Best slot for an item: first empty accepted slot, otherwise the first accepted slot.
func auto_slot(item: ItemInstance) -> StringName:
	var allowed: Array = BH.CATEGORY_SLOTS.get(item.base.category, [])
	if allowed.is_empty():
		return &""
	if item.base.is_weapon():
		var wt := weapon_type_of(item)
		var main_wt := weapon_type_of(slots[&"main_weapon"])
		if slots[&"main_weapon"] != null and slots[&"sub_weapon"] == null and wt != null and wt.dual_wieldable \
				and main_wt != null and main_wt.dual_wieldable:
			return &"sub_weapon"
		return &"main_weapon"
	for s in allowed:
		if slots[s] == null:
			return s
	return allowed[0]

## Equip into a slot. Returns the displaced items (to return to the inventory). Empty array + error on failure.
func equip(item: ItemInstance, slot: StringName, level: int, attrs: Dictionary) -> Dictionary:
	var err := check(item, slot, level, attrs)
	if err != "":
		return {"ok": false, "error": err, "displaced": []}
	var displaced: Array = []
	if slots[slot] != null:
		displaced.append(slots[slot])
	slots[slot] = item
	if slot == &"main_weapon":
		var wt := weapon_type_of(item)
		var sub: ItemInstance = slots[&"sub_weapon"]
		if sub != null and wt != null:
			var sub_is_weapon := sub.base.is_weapon()
			if wt.two_handed or (sub_is_weapon and not wt.dual_wieldable):
				displaced.append(sub)
				slots[&"sub_weapon"] = null
	changed.emit()
	return {"ok": true, "error": "", "displaced": displaced}

func unequip(slot: StringName) -> ItemInstance:
	var it: ItemInstance = slots.get(slot)
	if it == null:
		return null
	slots[slot] = null
	# A sub-hand weapon without a main weapon is not allowed.
	changed.emit()
	return it

## Items that must be removed after the main weapon is unequipped (orphaned off-hand weapon).
func orphaned_sub() -> ItemInstance:
	var sub: ItemInstance = slots[&"sub_weapon"]
	if sub != null and sub.base.is_weapon() and slots[&"main_weapon"] == null:
		return sub
	return null

func modifiers() -> Array:
	var out: Array = []
	for s in BH.SLOTS:
		var it: ItemInstance = slots[s]
		if it != null:
			out.append_array(it.modifiers())
	return out

func loadout() -> WeaponLoadout:
	var lo := WeaponLoadout.new()
	var main: ItemInstance = slots[&"main_weapon"]
	var sub: ItemInstance = slots[&"sub_weapon"]
	if main != null:
		lo.main_type = weapon_type_of(main)
		var r := main.damage_range()
		lo.main_min = r.x
		lo.main_max = r.y
		lo.main_crit = lo.main_type.crit_chance if lo.main_type != null else 0.05
		lo.main_element = main.base.element
		lo.main_elem_share = main.base.element_share
	if sub != null:
		if sub.base.category == &"shield":
			lo.has_shield = true
			lo.shield_block = sub.base.block_chance
			lo.shield_block_strength = sub.base.block_strength
		elif sub.base.is_weapon() and main != null:
			lo.off_type = weapon_type_of(sub)
			var r2 := sub.damage_range()
			lo.off_min = r2.x
			lo.off_max = r2.y
			lo.off_element = sub.base.element
			lo.off_elem_share = sub.base.element_share
			lo.dual_wield = lo.main_type != null and lo.off_type != null and lo.main_type.dual_wieldable and lo.off_type.dual_wieldable
	return lo

func to_dict() -> Dictionary:
	var d := {}
	for s in BH.SLOTS:
		d[String(s)] = slots[s].to_dict() if slots[s] != null else null
	return d

func from_dict(d: Dictionary) -> void:
	for s in BH.SLOTS:
		var v = d.get(String(s))
		slots[s] = ItemInstance.from_dict(v) if v is Dictionary else null
	changed.emit()
