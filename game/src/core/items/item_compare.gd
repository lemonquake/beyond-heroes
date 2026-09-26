class_name ItemCompare
## "Current vs. new" comparison: equips a candidate on a copy of the hero's equipment and diffs the real derived stats
## (the same StatCalculator the game uses — no separate tooltip math). Also estimates weapon DPS.

## Stats shown in comparisons, in order. [key, lower_is_better]
const ROWS := [
	[&"weapon_dps", false], [&"weapon_avg", false], [&"attacks_per_second", false], [&"crit_chance", false],
	[&"crit_damage", false], [&"defense", false], [&"block_chance", false], [&"max_hp", false], [&"max_mana", false],
	[&"hp_regen", false], [&"mana_regen", false], [&"move_speed", false], [&"attack_speed", false], [&"cast_speed", false],
	[&"evasion", false], [&"accuracy", false], [&"phys_damage", false], [&"magic_damage", false], [&"elemental_damage", false],
	[&"cdr", false], [&"status_res", false], [&"life_leech", false],
	[&"str", false], [&"agi", false], [&"int", false], [&"wis", false], [&"spi", false], [&"dex", false],
]

## Which equipped item a candidate would replace (the slot auto-equip would use).
static func target_slot(hero: HeroData, item: ItemInstance) -> StringName:
	return hero.equipment.auto_slot(item) if item.is_equipment() else &""

static func equipped_for(hero: HeroData, item: ItemInstance) -> ItemInstance:
	var slot := target_slot(hero, item)
	return hero.equipment.get_item(slot) if slot != &"" else null

## Full derived stats with the equipment replaced by `equipment_slots` (slot -> item).
static func stats_with(hero: HeroData, equipment_slots: Dictionary) -> DerivedStats:
	var eq := Equipment.new()
	for k in equipment_slots:
		eq.slots[k] = equipment_slots[k]
	var mods := eq.modifiers()
	mods.append_array(hero.talent_tree.modifiers())
	var d := StatCalculator.compute(hero.cls, hero.progress.level, hero.progress.base_attributes(), mods, eq.loadout())
	_add_weapon_rows(d)
	return d

static func _add_weapon_rows(d: DerivedStats) -> void:
	var mn := d.get_stat(&"weapon_min")
	var mx := d.get_stat(&"weapon_max")
	var avg := (mn + mx) * 0.5
	d.values[&"weapon_avg"] = avg
	var aps := d.get_stat(&"attacks_per_second")
	var crit := clampf(d.get_stat(&"crit_chance"), 0.0, 1.0)
	d.values[&"weapon_dps"] = avg * aps * (1.0 + crit * (d.get_stat(&"crit_damage", 1.5) - 1.0))

## Comparison rows for equipping `item` into `slot` (default: auto slot). Only changed stats are returned.
## Each row: {key, name, before, after, delta, better, text_before, text_after}
static func preview(hero: HeroData, item: ItemInstance, slot: StringName = &"") -> Dictionary:
	if slot == &"":
		slot = target_slot(hero, item)
	var before_slots: Dictionary = hero.equipment.slots.duplicate()
	var after_slots: Dictionary = before_slots.duplicate()
	if slot != &"":
		after_slots[slot] = item
		# a two-handed main weapon removes the off-hand weapon/shield, exactly as Equipment.equip does
		if slot == &"main_weapon":
			var wt := hero.equipment.weapon_type_of(item)
			var sub: ItemInstance = after_slots.get(&"sub_weapon")
			if sub != null and wt != null and (wt.two_handed or (sub.base.is_weapon() and not wt.dual_wieldable)):
				after_slots[&"sub_weapon"] = null
	var b := stats_with(hero, before_slots)
	var a := stats_with(hero, after_slots)
	var rows := []
	for r in ROWS:
		var k: StringName = r[0]
		var vb := b.get_stat(k)
		var va := a.get_stat(k)
		if absf(va - vb) < 0.0005:
			continue
		var better := (va < vb) if r[1] else (va > vb)
		rows.append({"key": k, "name": _name(k), "before": vb, "after": va, "delta": va - vb, "better": better,
			"text_before": _fmt(k, vb), "text_after": _fmt(k, va)})
	for e in Elements.ELEMENTAL:
		var rk := Elements.res_key(e)
		var vb2 := b.get_stat(rk)
		var va2 := a.get_stat(rk)
		if absf(va2 - vb2) >= 0.0005:
			rows.append({"key": rk, "name": StatDefs.name_of(rk), "before": vb2, "after": va2, "delta": va2 - vb2,
				"better": va2 > vb2, "text_before": StatDefs.format_value(rk, vb2), "text_after": StatDefs.format_value(rk, va2)})
	return {"slot": slot, "replaced": before_slots.get(slot) if slot != &"" else null, "rows": rows, "before": b, "after": a}

static func _name(k: StringName) -> String:
	match k:
		&"weapon_dps": return "Damage per Second"
		&"weapon_avg": return "Damage per Hit"
		&"attacks_per_second": return "Attacks per Second"
	return StatDefs.name_of(k)

static func _fmt(k: StringName, v: float) -> String:
	match k:
		&"weapon_dps", &"weapon_avg": return "%.1f" % v
		&"attacks_per_second": return "%.2f" % v
	return StatDefs.format_value(k, v)
