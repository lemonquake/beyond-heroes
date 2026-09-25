class_name ItemInstance
extends RefCounted
## A concrete item: base + rarity + rolled affixes + legendary powers.

static var _uid_counter := 0

var uid := 0
var base: ItemBaseDef
var rarity := BH.Rarity.COMMON
var ilvl := 1
var quality := 0.0                         # +% to base damage/defense (0..0.2)
var affixes: Array = []                    # [{id, tier, value}]
var powers: Array = []                     # [power id]
var count := 1
var custom_name := ""
var seed_value := 0

func _init() -> void:
	_uid_counter += 1
	uid = _uid_counter

func display_name() -> String:
	if custom_name != "":
		return custom_name
	if rarity == BH.Rarity.MAGIC and not affixes.is_empty():
		var pre := ""
		var suf := ""
		for a in affixes:
			var def := DB.affix(StringName(a.id))
			if def == null:
				continue
			if def.is_prefix and pre == "":
				pre = def.label + " "
			elif not def.is_prefix and suf == "":
				suf = " " + def.label
		return pre + base.display_name + suf
	return base.display_name

func color() -> Color:
	return BH.rarity_color(rarity)

func category() -> StringName:
	return base.category

func is_equipment() -> bool:
	return BH.CATEGORY_SLOTS.has(base.category)

func damage_range() -> Vector2:
	var q := 1.0 + quality
	var local_inc := 0.0
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def != null and def.stat == &"local_phys" :
			local_inc += float(a.value)
	return Vector2(base.damage_min, base.damage_max) * q * (1.0 + local_inc)

func defense_value() -> float:
	var local_inc := 0.0
	var local_flat := 0.0
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def == null:
			continue
		if def.stat == &"local_def":
			local_inc += float(a.value)
		elif def.stat == &"local_def_flat":
			local_flat += float(a.value)
	return (base.defense * (1.0 + quality) + local_flat) * (1.0 + local_inc)

## All stat modifiers this item grants when equipped (local modifiers are folded into base values instead).
func modifiers() -> Array:
	var out: Array = []
	var src := display_name()
	for m in base.implicit:
		out.append(StatModifier.new(m.stat, m.op, m.value, src))
	if base.category != &"weapon" and base.category != &"shield":
		var dv := defense_value()
		if dv > 0.0:
			out.append(StatModifier.flat(&"defense", dv, src))
	elif base.category == &"shield":
		var dv2 := defense_value()
		if dv2 > 0.0:
			out.append(StatModifier.flat(&"defense", dv2, src))
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def == null or String(def.stat).begins_with("local_"):
			continue
		out.append(StatModifier.new(def.stat, def.op, float(a.value), src))
	for pid in powers:
		var p := DB.power(StringName(pid))
		if p == null:
			continue
		out.append(StatModifier.flat(StringName("flag_" + String(p.flag)), p.magnitude, src))
		for m in p.modifiers:
			out.append(StatModifier.new(m.stat, m.op, m.value, src))
	return out

func sell_value() -> int:
	var mult: float = [1.0, 2.0, 4.0, 7.0, 15.0, 30.0][rarity]
	return int(round(float(base.value) * mult * (1.0 + float(ilvl) * 0.05))) * count

func affix_lines() -> PackedStringArray:
	var out := PackedStringArray()
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def == null:
			continue
		if def.stat == &"local_phys":
			out.append("%d%% increased Physical Damage (local)" % roundi(float(a.value) * 100.0))
		elif def.stat == &"local_def":
			out.append("%d%% increased Defense (local)" % roundi(float(a.value) * 100.0))
		elif def.stat == &"local_def_flat":
			out.append("+%d Defense (local)" % roundi(float(a.value)))
		else:
			out.append(StatDefs.format_modifier(def.stat, def.op, float(a.value)))
	return out

func to_dict() -> Dictionary:
	return {"base": String(base.id), "rarity": rarity, "ilvl": ilvl, "quality": quality, "affixes": affixes.duplicate(true),
		"powers": powers.duplicate(), "count": count, "name": custom_name, "seed": seed_value}

static func from_dict(d: Dictionary) -> ItemInstance:
	var b := DB.item_base(StringName(d.get("base", "")))
	if b == null:
		push_warning("Unknown item base in save: %s" % d.get("base", ""))
		return null
	var it := ItemInstance.new()
	it.base = b
	it.rarity = clampi(int(d.get("rarity", 0)), 0, BH.Rarity.MYTHIC)
	it.ilvl = int(d.get("ilvl", 1))
	it.quality = float(d.get("quality", 0.0))
	it.affixes = []
	for a in d.get("affixes", []):
		it.affixes.append({"id": String(a.get("id", "")), "tier": int(a.get("tier", 0)), "value": float(a.get("value", 0.0))})
	it.powers = []
	for p in d.get("powers", []):
		it.powers.append(String(p))
	it.count = maxi(1, int(d.get("count", 1)))
	it.custom_name = String(d.get("name", ""))
	it.seed_value = int(d.get("seed", 0))
	return it

func clone() -> ItemInstance:
	return ItemInstance.from_dict(to_dict())
