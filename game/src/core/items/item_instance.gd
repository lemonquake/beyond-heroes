class_name ItemInstance
extends RefCounted
## A concrete item: base + rarity + rolled affixes + powers (+ license, set membership, player flags).

static var _uid_counter := 0

const SELL_MULT := [0.5, 1.0, 1.6, 2.4, 3.4, 5.0, 7.5, 11.0, 16.0, 26.0]   # per rarity tier

var uid := 0
var base: ItemBaseDef
var rarity := BH.Rarity.COMMON
var ilvl := 1
var quality := 0.0                         # +% to base damage/defense (0..0.2)
var affixes: Array = []                    # [{id, tier, value, mw?}]  mw = masterwork (perfected) affix
var powers: Array = []                     # [power id]
var license: StringName = &""              # Licensed tier: faction license id
var count := 1
var custom_name := ""
var epithet := ""                          # bh-012: the second half of a gacha name ("Oath of the Last Flame")
var seed_value := 0
# Player-controlled flags (persisted).
var locked := false                        # cannot be sold, dropped or destroyed
var favorite := false                      # sorted first, protected like locked
var junk := false                          # marked for "sell junk" at merchants
var crafted := false                       # made at a crafting station (bh-007): shown in the tooltip

func _init() -> void:
	_uid_counter += 1
	uid = _uid_counter

func display_name() -> String:
	if custom_name != "" and epithet != "":
		return "%s, %s" % [custom_name, epithet]
	if custom_name != "":
		return custom_name
	if base.unique_name != "":
		return base.unique_name
	if rarity >= BH.Rarity.BASIC and rarity <= BH.Rarity.LICENSED and not affixes.is_empty():
		# "Flaming Sword of Precision": first prefix + base + first suffix.
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

## The proper name alone (loot labels): "Vornhald", or the full display name.
func short_name() -> String:
	return custom_name if custom_name != "" else display_name()

## Gear stars 1–5 from how close the rolls came to perfect (0 for non-gear and plain pieces).
func stars() -> int:
	return ItemNames.stars(self)

func is_perfect() -> bool:
	return ItemNames.is_perfect(self)

func color() -> Color:
	return BH.rarity_color(rarity)

func rarity_name() -> String:
	return BH.rarity_name(rarity)

func category() -> StringName:
	return base.category

func is_equipment() -> bool:
	return BH.CATEGORY_SLOTS.has(base.category)

func is_protected() -> bool:
	return locked or favorite

func set_def() -> SetDef:
	return DB.item_set(base.set_id) if base.set_id != &"" else null

## Cached: a texture loaded only for one draw call is freed before the frame renders (it would draw blank/white).
static var _icons := {}

func icon() -> Texture2D:
	var p := base.icon_path()
	if not _icons.has(p):
		_icons[p] = load(p) if p != "" and ResourceLoader.exists(p) else null
	return _icons[p]

func _local(stat: StringName) -> float:
	var t := 0.0
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def != null and def.stat == stat:
			t += float(a.value)
	return t

## Carried weight of this stack (unit weight x count).
func weight() -> float:
	return maxf(0.0, base.weight) * float(maxi(count, 1))

func damage_range() -> Vector2:
	var q := 1.0 + quality
	return Vector2(base.damage_min, base.damage_max) * q * (1.0 + _local(&"local_phys"))

func defense_value() -> float:
	return (base.defense * (1.0 + quality) + _local(&"local_def_flat")) * (1.0 + _local(&"local_def"))

func block_chance() -> float:
	return base.block_chance

## All stat modifiers this item grants when equipped (local modifiers are folded into base values instead).
func modifiers() -> Array:
	var out: Array = []
	var src := display_name()
	for m in base.implicit:
		out.append(StatModifier.new(m.stat, m.op, m.value, src))
	for m in base.fixed_mods:
		out.append(StatModifier.new(m.stat, m.op, m.value, src))
	if base.category != &"weapon":
		var dv := defense_value()
		if dv > 0.0:
			out.append(StatModifier.flat(&"defense", dv, src))
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def == null or String(def.stat).begins_with("local_"):
			continue
		out.append(StatModifier.new(def.stat, def.op, float(a.value), src))
	if license != &"":
		for m in license_modifiers():
			out.append(m)
	for pid in powers:
		var p := DB.power(StringName(pid))
		if p == null:
			continue
		out.append(StatModifier.flat(StringName("flag_" + String(p.flag)), p.magnitude, src))
		for m in p.modifiers:
			out.append(StatModifier.new(m.stat, m.op, m.value, src))
	return out

## License bonus: fixed specialization modifiers that scale with item level.
func license_modifiers() -> Array:
	var out: Array = []
	var lic: Dictionary = DB.licenses.get(license, {})
	if lic.is_empty():
		return out
	var src := "%s license" % lic.get("name", "")
	for m in lic.get("mods", []):
		var v := float(m[2]) + float(m[3]) * float(ilvl - 1)
		out.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, v, src))
	return out

## Merchant buy price of one unit before merchant markup (ShopPricing applies markup/reputation).
func base_value() -> float:
	var affix_bonus := 1.0 + 0.12 * float(affixes.size()) + 0.35 * float(powers.size())
	return float(base.value) * SELL_MULT[clampi(rarity, 0, SELL_MULT.size() - 1)] * (1.0 + float(ilvl) * 0.06) * affix_bonus * (1.0 + quality)

func sell_value() -> int:
	if not base.sellable:
		return 0
	return maxi(1, int(round(base_value() * 0.25))) * count

func affix_lines() -> PackedStringArray:
	var out := PackedStringArray()
	for a in affixes:
		var def := DB.affix(StringName(a.id))
		if def == null:
			continue
		var line: String
		if def.stat == &"local_phys":
			line = "%d%% increased Physical Damage" % roundi(float(a.value) * 100.0)
		elif def.stat == &"local_def":
			line = "%d%% increased Defense" % roundi(float(a.value) * 100.0)
		elif def.stat == &"local_def_flat":
			line = "+%d Defense" % roundi(float(a.value))
		else:
			line = StatDefs.format_modifier(def.stat, def.op, float(a.value))
		if a.get("mw", false):
			line += "  (Masterwork)"
		out.append(line)
	return out

func to_dict() -> Dictionary:
	var d := {"base": String(base.id), "rarity": rarity, "ilvl": ilvl, "quality": quality, "affixes": affixes.duplicate(true),
		"powers": powers.duplicate(), "count": count, "name": custom_name, "seed": seed_value}
	if epithet != "":
		d["epithet"] = epithet
	if license != &"":
		d["license"] = String(license)
	if locked:
		d["locked"] = true
	if favorite:
		d["favorite"] = true
	if junk:
		d["junk"] = true
	if crafted:
		d["crafted"] = true
	return d

static func from_dict(d: Dictionary) -> ItemInstance:
	var b := DB.item_base(StringName(d.get("base", "")))
	if b == null:
		push_warning("Unknown item base in save: %s" % d.get("base", ""))
		return null
	var it := ItemInstance.new()
	it.base = b
	it.rarity = clampi(int(d.get("rarity", 0)), 0, BH.RARITY_COUNT - 1)
	it.ilvl = int(d.get("ilvl", 1))
	it.quality = float(d.get("quality", 0.0))
	it.affixes = []
	for a in d.get("affixes", []):
		var e := {"id": String(a.get("id", "")), "tier": int(a.get("tier", 0)), "value": float(a.get("value", 0.0))}
		if a.get("mw", false):
			e["mw"] = true
		it.affixes.append(e)
	it.powers = []
	for p in d.get("powers", []):
		it.powers.append(String(p))
	it.license = StringName(d.get("license", ""))
	it.count = maxi(1, int(d.get("count", 1)))
	it.custom_name = String(d.get("name", ""))
	it.epithet = String(d.get("epithet", ""))
	it.seed_value = int(d.get("seed", 0))
	it.locked = bool(d.get("locked", false))
	it.favorite = bool(d.get("favorite", false))
	it.junk = bool(d.get("junk", false))
	it.crafted = bool(d.get("crafted", false))
	return it

func clone() -> ItemInstance:
	return ItemInstance.from_dict(to_dict())

## Same item kind for stacking purposes.
func stacks_with(other: ItemInstance) -> bool:
	return other != null and other.base == base and base.is_stackable() and other.rarity == rarity
