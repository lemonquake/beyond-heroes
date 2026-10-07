class_name ItemInstance
extends RefCounted
## A concrete item: base + rarity + rolled affixes + powers (+ license, set membership, player flags).

static var _uid_counter := 0

const SELL_MULT := [0.5, 1.0, 1.6, 2.4, 3.4, 5.0, 7.5, 11.0, 16.0, 26.0, 40.0, 60.0, 90.0, 140.0, 240.0]   # per rarity tier

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
# bh-015: forged name parts of a Common..Advanced weapon (NameForge), used where no enchantment names that side:
# "Saltworn Shortbow", "Flaming Recurve Bow of the Grey Ferry"
var name_prefix := ""
var name_suffix := ""
var seed_value := 0
# Player-controlled flags (persisted).
var locked := false                        # cannot be sold, dropped or destroyed
var favorite := false                      # sorted first, protected like locked
var junk := false                          # marked for "sell junk" at merchants
var crafted := false                       # made at a crafting station (bh-007): shown in the tooltip
# bh-017: a weapon can carry one Enchantment (Alchemy Table, rank I..III) and one Fore-Tech refit (Forge, +1..+5): DataUpgrades
var enchant: StringName = &""
var enchant_rank := 0
var foretech: StringName = &""
var foretech_rank := 0
# bh-018: sockets opened by a Socket Specialist (Sockets) and the crystal set in each ("" = empty): gems.size() == sockets
var sockets := 0
var gems: Array = []
# bh-024: an Unbound variant (the "alj" special weapons, Cheats) has no level, attribute or class-rank requirement
var unbound := false

func _init() -> void:
	_uid_counter += 1
	uid = _uid_counter

func display_name() -> String:
	# bh-022: crystals set in the sockets name the piece ("Iron Longsword of the Nova Blast", CrystalNames)
	var cs := CrystalNames.suffix(self)
	var cx := (" " + cs) if cs != "" else ""
	if custom_name != "" and epithet != "":
		return "%s%s, %s%s" % [custom_name, cx, epithet, _tech_tag()]
	if custom_name != "":
		return custom_name + cx + _tech_tag()
	if base.unique_name != "":
		return base.unique_name + cx + _tech_tag()
	if rarity >= BH.Rarity.BASIC and rarity <= BH.Rarity.LICENSED and not affixes.is_empty() or name_prefix != "" or name_suffix != "":
		# "Flaming Sword of Precision": first prefix + base + first suffix; a weapon's forged parts fill an empty side.
		# The crystals' name takes the suffix's place ("Flaming Sword of the Nova Blast").
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
		if pre == "" and name_prefix != "":
			pre = name_prefix + " "
		if suf == "" and name_suffix != "":
			suf = " " + name_suffix
		if cx != "":
			suf = cx
		return pre + base.display_name + suf + _tech_tag()
	return base.display_name + cx + _tech_tag()

## bh-017: " +3" after the name of a weapon with a Fore-Tech refit.
func _tech_tag() -> String:
	return " +%d" % foretech_rank if foretech_rank > 0 and foretech != &"" else ""

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
			t += affix_value(a)
	return t

## bh-030: a rolled enchantment's value on this item: flat sizes (Health, attributes, Defense, added damage) grow with
## the item level past their affix's top tier (GearScaling); percentages are exactly as rolled.
func affix_value(a: Dictionary) -> float:
	var v := float(a.get("value", 0.0))
	var def := DB.affix(StringName(a.get("id", "")))
	if def == null:
		return v
	var m := GearScaling.affix_mult(def, equipment_level())
	return v if m == 1.0 else (roundf(v * m) if def.integer else snappedf(v * m, 0.001))

## bh-030: a flat implicit of the base, grown from the base's own level to the item's (percentages unchanged).
func implicit_value(m: StatModifier) -> float:
	if m.op != StatModifier.Op.FLAT:
		return m.value
	var mult := GearScaling.flat_mult(m.stat, base.level_req, equipment_level())
	return m.value if mult == 1.0 else snappedf(m.value * mult, 0.01)

## Carried weight of this stack (unit weight x count).
func weight() -> float:
	return maxf(0.0, base.weight) * float(maxi(count, 1))

func damage_range() -> Vector2:
	var q := 1.0 + quality + DataUpgrades.TEMPER_PER_RANK * float(foretech_rank if foretech != &"" else 0)
	var level := equipment_level()
	var damage := Vector2(base.damage_min, base.damage_max)
	if level > 5:
		var aps := base.weapon_aps()
		var budget := DataItems.roster_damage(base.weapon_type, level, aps)
		var authored_avg := maxf(1.0, (damage.x + damage.y) * 0.5)
		damage *= (budget.x + budget.y) * 0.5 / authored_avg
	# Quality, tempering and the local damage affix add, rather than multiply.
	return damage * CombatGrowth.weapon_factor(level) * (q + _local(&"local_phys")) * DataAscendant.mult(rarity)

func equipment_level() -> int:
	return maxi(base.level_req, clampi(ilvl, 1, BH.LEVEL_CAP + 5)) if rarity != BH.Rarity.BEGINNER else base.level_req

func required_level() -> int:
	return maxi(base.level_req, mini(BH.LEVEL_CAP, equipment_level() - 3)) if is_equipment() else base.level_req

func defense_value() -> float:
	return (GearScaling.defense(base, equipment_level()) * (1.0 + quality) * DataAscendant.mult(rarity) + _local(&"local_def_flat")) * (1.0 + _local(&"local_def"))

## bh-017: the element the weapon deals (an Enchantment replaces the blade's own) and the share of its damage that is elemental.
func weapon_element() -> int:
	if enchant != &"" and enchant_rank > 0:
		return int(DataUpgrades.enchant(enchant).get("element", base.element))
	return base.element

func weapon_element_share() -> float:
	if enchant != &"" and enchant_rank > 0:
		var sh := DataUpgrades.enchant_share(enchant, enchant_rank)
		return maxf(sh, base.element_share) if weapon_element() == base.element else sh
	return base.element_share

func is_upgraded() -> bool:
	return (enchant != &"" and enchant_rank > 0) or (foretech != &"" and foretech_rank > 0)

func block_chance() -> float:
	return base.block_chance

## All stat modifiers this item grants when equipped (local modifiers are folded into base values instead).
func modifiers() -> Array:
	var out: Array = []
	var src := display_name()
	for m in base.implicit:
		out.append(StatModifier.new(m.stat, m.op, implicit_value(m), src))
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
		out.append(StatModifier.new(def.stat, def.op, affix_value(a), src))
	if enchant != &"" and enchant_rank > 0:
		out.append_array(DataUpgrades.enchant_mods(enchant, enchant_rank, "%s %s" % [DataUpgrades.enchant(enchant).get("name", "Enchantment"), DataUpgrades.roman(enchant_rank)]))
	if foretech != &"" and foretech_rank > 0:
		out.append_array(DataUpgrades.tech_mods(foretech, foretech_rank, "%s +%d" % [DataUpgrades.tech(foretech).get("name", "Fore-Tech"), foretech_rank]))
	if license != &"":
		for m in license_modifiers():
			out.append(m)
	for g in gems:
		if String(g) != "":
			out.append_array(DataCrystals.mods(StringName(g), base.category))
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
	if base.category == &"crystal":
		return float(base.value)
	var affix_bonus := 1.0 + 0.12 * float(affixes.size()) + 0.35 * float(powers.size()) + 0.18 * float(enchant_rank) + 0.1 * float(foretech_rank)
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
			line = "+%d Defense" % roundi(affix_value(a))
		else:
			line = StatDefs.format_modifier(def.stat, def.op, affix_value(a))
		if a.get("mw", false):
			line += "  (Masterwork)"
		out.append(line)
	return out

func to_dict() -> Dictionary:
	var d := {"base": String(base.id), "rarity": rarity, "ilvl": ilvl, "quality": quality, "affixes": affixes.duplicate(true),
		"powers": powers.duplicate(), "count": count, "name": custom_name, "seed": seed_value, "balance_version": ItemGenerator.BALANCE_VERSION}
	if epithet != "":
		d["epithet"] = epithet
	if name_prefix != "":
		d["np"] = name_prefix
	if name_suffix != "":
		d["ns"] = name_suffix
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
	if enchant != &"" and enchant_rank > 0:
		d["ench"] = [String(enchant), enchant_rank]
	if foretech != &"" and foretech_rank > 0:
		d["tech"] = [String(foretech), foretech_rank]
	if sockets > 0:
		d["sk"] = sockets
		d["gems"] = gems.duplicate()
	if unbound:
		d["ub"] = true
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
	it.name_prefix = String(d.get("np", ""))
	it.name_suffix = String(d.get("ns", ""))
	it.seed_value = int(d.get("seed", 0))
	it.locked = bool(d.get("locked", false))
	it.favorite = bool(d.get("favorite", false))
	it.junk = bool(d.get("junk", false))
	it.crafted = bool(d.get("crafted", false))
	it.unbound = bool(d.get("ub", false))
	var en = d.get("ench", [])
	if en is Array and (en as Array).size() == 2 and DataUpgrades.ENCHANTS.has(StringName(en[0])) and b.is_weapon():
		it.enchant = StringName(en[0])
		it.enchant_rank = clampi(int(en[1]), 1, DataUpgrades.ENCHANT_MAX)
	var te = d.get("tech", [])
	if te is Array and (te as Array).size() == 2 and DataUpgrades.TECHS.has(StringName(te[0])) and b.is_weapon():
		it.foretech = StringName(te[0])
		it.foretech_rank = clampi(int(te[1]), 1, DataUpgrades.TECH_MAX)
	# bh-018 (optional keys): sockets and their crystals; unknown crystals become empty sockets
	if b.category in BH.CATEGORY_SLOTS:
		it.sockets = clampi(int(d.get("sk", 0)), 0, 8)      # bh-041: Divine and above take eight (was cut to seven on loading)
		var gs = d.get("gems", [])
		for i in it.sockets:
			var gid := String(gs[i]) if gs is Array and i < (gs as Array).size() else ""
			it.gems.append(gid if gid != "" and DataCrystals.is_crystal(StringName(gid)) and DB.item_base(StringName(gid)) != null else "")
	ItemGenerator.migrate_balance(it, int(d.get("balance_version", 0)))
	return it

func clone() -> ItemInstance:
	return ItemInstance.from_dict(to_dict())

## Same item kind for stacking purposes.
func stacks_with(other: ItemInstance) -> bool:
	return other != null and other.base == base and base.is_stackable() and other.rarity == rarity
