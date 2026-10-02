class_name GearScaling
## bh-030: equipment keeps pace with its own level. Before bh-030 a piece's armour was its base's authored Defense times
## a gentle level factor, and the authored bases stop at level 16-17. A level 53 drop of a level 1 base (Iron Gauntlet,
## 4 Defense) came out at 9 Defense, and even the best authored base fell behind monster damage, which follows the
## reference hero's level. Flat enchantments (+Health, +Strength, +Defense, added damage) also stopped growing at their
## last tier (level 35 at most) while the level cap is 300.
##
## The rules (levels 1-5 keep their authored numbers):
##   Defense   every armour slot has a reference curve: the best ordinary base of that slot and weight class at each
##             level (interpolated between the authored tiers), carried past the last tier so a full kit keeps the same
##             share of physical damage reduction against a monster of its own level (StatCalculator.armor_reduction).
##             A piece reaches the reference of its own item level, times its base's character (a sturdier-than-average
##             base keeps its edge, 0.85x-1.3x). It never drops below the old formula.
##   Flat      flat enchantments and flat implicits that are sizes (Health, Mana, attributes, regeneration, Defense,
##             added damage, Evasion) grow past their top tier with the stat they are measured against. Percentages,
##             chances and skill levels never scale: they stay exactly as rolled.

const FROM := 5
const IDENTITY_MIN := 0.85
const IDENTITY_MAX := 1.3
## Every slot is worth at least this share of a chest piece of the same level (the authored gloves and boots were
## a fifth of a chest, so a level 53 gauntlet read weaker than a level 25 helm).
const SHARE := {&"armor": 1.0, &"helm": 0.6, &"leggings": 0.55, &"inner_garment": 0.5, &"gloves": 0.5, &"boots": 0.5, &"shield": 0.7}
## Cloth wears this share of plate.
const CLOTH := 0.55
## Past the last authored tier, gear outgrows monsters a little: up to +40% over LATE_SPAN levels.
const LATE_BONUS := 0.4
const LATE_SPAN := 40.0
## Levels over which the slot floor fades in after FROM (no jump at level 6).
const FLOOR_RAMP := 11.0

## Flat stats that are sizes, and the curve each one follows.
const HEALTH_LIKE := [&"max_hp", &"max_mana", &"str", &"agi", &"int", &"wis", &"spi", &"dex", &"hp_regen", &"mana_regen",
	&"hp_on_kill", &"mana_on_kill"]
const ARMOR_LIKE := [&"local_def_flat", &"defense", &"evasion"]
const DAMAGE_LIKE := [&"added_physical", &"added_fire", &"added_ice", &"added_lightning", &"added_dark", &"added_light",
	&"added_water", &"added_earth", &"added_wind"]

static var _curves := {}

# ---- defense ---------------------------------------------------------------------------------------------------------

## The armour constant of an attacker of `level` (physical reduction = defense / (defense + k)).
static func armor_k(level: int) -> float:
	return StatCalculator.ARMOR_K_BASE + StatCalculator.ARMOR_K_LEVEL * float(maxi(level, 1))

static func _key(category: StringName, weight: StringName) -> String:
	return "%s/%s" % [category, weight]

## [[level, defense], ...] ascending: the best ordinary base of a slot and weight class at each authored level.
static func curve(category: StringName, weight: StringName) -> Array:
	var k := _key(category, weight)
	if _curves.has(k):
		return _curves[k]
	var best := {}
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category != category or b.defense <= 0.0 or b.set_id != &"" or b.unique_name != "" or b.drop_weight <= 0:
			continue
		if weight != &"*" and b.weight_class != weight:
			continue
		best[b.level_req] = maxf(float(best.get(b.level_req, 0.0)), b.defense)
	var levels := best.keys()
	levels.sort()
	var out := []
	var top := 0.0
	for l in levels:
		top = maxf(top, float(best[l]))       # an envelope: a later tier never reads weaker than an earlier one
		out.append([int(l), top])
	if out.is_empty() and weight != &"*":
		out = curve(category, &"*")
	_curves[k] = out
	return out

## The authored reference Defense of a slot at a level (before any level factor), clamped to the authored range.
static func authored(category: StringName, weight: StringName, level: int) -> float:
	var c := curve(category, weight)
	if c.is_empty():
		return 0.0
	if level <= int(c[0][0]):
		return float(c[0][1])
	for i in range(1, c.size()):
		if level <= int(c[i][0]):
			var a: Array = c[i - 1]
			var b: Array = c[i]
			return lerpf(float(a[1]), float(b[1]), float(level - int(a[0])) / float(maxi(1, int(b[0]) - int(a[0]))))
	return float(c[-1][1])

## The slot's own authored curve carried forward (before the slot floor).
static func _own_curve(category: StringName, weight: StringName, level: int) -> float:
	var c := curve(category, weight)
	if c.is_empty():
		return 0.0
	var last := int(c[-1][0])
	if level <= last:
		return authored(category, weight, level) * CombatGrowth.armor_factor(level)
	var late := 1.0 + LATE_BONUS * minf(1.0, float(level - last) / LATE_SPAN)
	return float(c[-1][1]) * CombatGrowth.armor_factor(last) * armor_k(level) / armor_k(last) * late

## A plate chest piece of `level`: what every slot's floor is measured against.
static func chest(level: int) -> float:
	return _own_curve(&"armor", &"heavy", level)

## The final Defense of the slot's reference base at `level`.
static func slot_defense(category: StringName, weight: StringName, level: int) -> float:
	var own := _own_curve(category, weight, level)
	if level <= FROM:
		return own
	var floor_v := float(SHARE.get(category, 0.5)) * chest(level) * (CLOTH if weight == &"cloth" else 1.0)
	var ramp := clampf(float(level - FROM) / FLOOR_RAMP, 0.0, 1.0)
	return maxf(own, lerpf(own, floor_v, ramp))

## The Defense of `base` at equipment level `level`, before quality and enchantments.
static func defense(base: ItemBaseDef, level: int) -> float:
	var own := base.defense * CombatGrowth.armor_factor(level)
	if level <= FROM or base.defense <= 0.0:
		return own
	var ref_own := authored(base.category, base.weight_class, base.level_req)
	if ref_own <= 0.0:
		return own
	var identity := clampf(base.defense / ref_own, IDENTITY_MIN, IDENTITY_MAX)
	return maxf(own, slot_defense(base.category, base.weight_class, level) * identity)

# ---- flat bonuses ------------------------------------------------------------------------------------------------------

## The size a flat bonus of `stat` is measured against at `level` (0 = the stat does not scale).
static func measure(stat: StringName, level: int) -> float:
	if HEALTH_LIKE.has(stat):
		return CombatBudget.hero_hp_ref(level)
	if ARMOR_LIKE.has(stat):
		return armor_k(level)
	if DAMAGE_LIKE.has(stat):
		return CombatGrowth.weapon_factor(level)
	return 0.0

static func scales(stat: StringName) -> bool:
	return HEALTH_LIKE.has(stat) or ARMOR_LIKE.has(stat) or DAMAGE_LIKE.has(stat)

## Multiplier for a flat bonus authored for level `from`, on an item of level `level` (1 when it does not scale).
static func flat_mult(stat: StringName, from: int, level: int) -> float:
	if level <= maxi(from, FROM) or not scales(stat):
		return 1.0
	var a := measure(stat, maxi(from, 1))
	return maxf(1.0, measure(stat, level) / a) if a > 0.0 else 1.0

## Multiplier for a rolled enchantment: it grows from the level of its affix's top tier.
static func affix_mult(def: AffixDef, ilvl: int) -> float:
	if def == null or def.op != StatModifier.Op.FLAT or def.tiers.is_empty():
		return 1.0
	return flat_mult(def.stat, int(def.tiers[-1][0]), ilvl)
