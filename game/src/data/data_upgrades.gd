class_name DataUpgrades
## Weapon upgrades (bh-017): two different ways to improve a weapon you already own.
##
## ENCHANTMENT (Alchemy Table) is magic: it etches a rune that turns part of the weapon's damage into an element and adds
## elemental gifts. One enchantment per weapon, rank I to III; changing it starts over at rank I.
## FORE-TECH (Forge) is craft: a mechanical refit, rank +1 to +5, that tempers the blade (+2% weapon damage per rank) and
## adds one kind of mechanical bonus. One refit per weapon; changing it starts over at +1.
## A weapon can carry one of each. Both are kept when the weapon is traded, sold or stored.

const ENCHANT_MAX := 3
const TECH_MAX := 5
const TEMPER_PER_RANK := 0.02          # Fore-Tech: weapon damage per rank, on top of the refit's own bonus

const FLAT := StatModifier.Op.FLAT
const INC := StatModifier.Op.INC

## id: {name, element, share [per rank], mods [[stat, op, [per rank]]], mat, color, text, best}
const ENCHANTS := {
	&"flame": {"name": "Flame Etching", "element": Elements.FIRE, "share": [0.20, 0.30, 0.40], "color": Color(1.0, 0.55, 0.22), "mat": &"ember_core",
		"mods": [[&"added_fire", FLAT, [4.0, 8.0, 13.0]], [&"burn_damage", INC, [0.10, 0.20, 0.32]]],
		"text": "A rune of cinders. Part of every hit burns, and Burning hurts more."},
	&"frost": {"name": "Frost Etching", "element": Elements.ICE, "share": [0.20, 0.30, 0.40], "color": Color(0.55, 0.85, 1.0), "mat": &"frost_crystal",
		"mods": [[&"added_ice", FLAT, [4.0, 8.0, 13.0]], [&"status_power", INC, [0.10, 0.18, 0.28]]],
		"text": "A rune of rime. Part of every hit is ice, and Chill builds toward Freeze faster."},
	&"storm": {"name": "Storm Etching", "element": Elements.LIGHTNING, "share": [0.20, 0.30, 0.40], "color": Color(0.95, 0.9, 0.4), "mat": &"storm_essence",
		"mods": [[&"added_lightning", FLAT, [4.0, 8.0, 13.0]], [&"attack_speed", INC, [0.03, 0.06, 0.09]]],
		"text": "A rune of thunder. Part of every hit is lightning, and the weapon moves quicker."},
	&"stone": {"name": "Stone Etching", "element": Elements.EARTH, "share": [0.20, 0.30, 0.40], "color": Color(0.75, 0.6, 0.35), "mat": &"rune_plate",
		"mods": [[&"pen_armor", FLAT, [0.05, 0.09, 0.14]], [&"stagger_power", INC, [0.10, 0.20, 0.30]]],
		"text": "A rune of the deep. Part of every hit is earth; armor gives way and poise breaks sooner."},
	&"radiance": {"name": "Radiant Etching", "element": Elements.LIGHT, "share": [0.20, 0.30, 0.40], "color": Color(1.0, 0.95, 0.7), "mat": &"wisp_mote",
		"mods": [[&"added_light", FLAT, [4.0, 8.0, 13.0]], [&"healing", INC, [0.06, 0.12, 0.20]]],
		"text": "A rune of dawn. Part of every hit is light, and healing you give or receive is stronger."},
	&"umbral": {"name": "Umbral Etching", "element": Elements.DARK, "share": [0.20, 0.30, 0.40], "color": Color(0.7, 0.45, 0.95), "mat": &"grave_dust",
		"mods": [[&"added_dark", FLAT, [4.0, 8.0, 13.0]], [&"life_leech", FLAT, [0.015, 0.03, 0.05]]],
		"text": "A rune of dusk. Part of every hit is shadow, and a share of the damage returns as life."},
}

## id: {name, mods [[stat, op, per rank]], color, text, best}
const TECHS := {
	&"whet": {"name": "Whetted Edge", "color": Color(0.85, 0.85, 0.9), "best": "any weapon",
		"mods": [[&"phys_damage", INC, 0.06]],
		"text": "Grind and re-hone: more Physical Damage."},
	&"balance": {"name": "Balanced Grip", "color": Color(0.6, 0.9, 0.7), "best": "fast weapons",
		"mods": [[&"attack_speed", INC, 0.03], [&"crit_chance", FLAT, 0.005]],
		"text": "Rebalance the weight: swings come faster and find weak spots."},
	&"serrate": {"name": "Serrated Teeth", "color": Color(0.95, 0.5, 0.45), "best": "daggers, claws, axes",
		"mods": [[&"crit_damage", FLAT, 0.08], [&"dot_damage", INC, 0.06]],
		"text": "Cut a row of teeth: critical hits hit harder and bleeding bites deeper."},
	&"weight": {"name": "Weighted Head", "color": Color(0.9, 0.7, 0.4), "best": "hammers, great axes, clubs",
		"mods": [[&"stagger_power", INC, 0.08], [&"impact_damage", INC, 0.10]],
		"text": "Cast in a heavy cap: bigger stagger and harder collisions."},
	&"pierce": {"name": "Piercing Point", "color": Color(0.7, 0.8, 1.0), "best": "spears, swords, arrows",
		"mods": [[&"pen_armor", FLAT, 0.04]],
		"text": "Narrow the tip: ignores part of the target's armor."},
	&"sights": {"name": "Fine Sights", "color": Color(1.0, 0.85, 0.5), "best": "bows and javelins",
		"mods": [[&"crit_chance", FLAT, 0.012], [&"projectile_damage", INC, 0.04], [&"projectile_speed", INC, 0.05]],
		"text": "Fit a sighting notch and true the shaft: straighter, faster, deadlier shots."},
}

static func enchant(id: StringName) -> Dictionary:
	return ENCHANTS.get(id, {})

static func tech(id: StringName) -> Dictionary:
	return TECHS.get(id, {})

static func enchant_ids() -> Array:
	return ENCHANTS.keys()

static func tech_ids() -> Array:
	return TECHS.keys()

## The value of one per-rank entry at `rank` (1-based): a list is indexed by rank, a number scales with it.
static func _at(v, rank: int) -> float:
	if v is Array:
		return float(v[clampi(rank, 1, (v as Array).size()) - 1])
	return float(v) * float(rank)

static func enchant_mods(id: StringName, rank: int, src := "") -> Array:
	var out: Array = []
	var d := enchant(id)
	if d.is_empty() or rank < 1:
		return out
	for m in d.mods:
		out.append(StatModifier.new(m[0], int(m[1]) as StatModifier.Op, _at(m[2], rank), src))
	return out

static func tech_mods(id: StringName, rank: int, src := "") -> Array:
	var out: Array = []
	var d := tech(id)
	if d.is_empty() or rank < 1:
		return out
	for m in d.mods:
		out.append(StatModifier.new(m[0], int(m[1]) as StatModifier.Op, _at(m[2], rank), src))
	return out

static func enchant_share(id: StringName, rank: int) -> float:
	var d := enchant(id)
	return _at(d.share, rank) if not d.is_empty() and rank >= 1 else 0.0

## What upgrading to `rank` costs: {inputs [[base id, n]], gold, level}.
static func enchant_cost(id: StringName, rank: int) -> Dictionary:
	var d := enchant(id)
	var r := clampi(rank, 1, ENCHANT_MAX)
	var inputs: Array = [[d.get("mat", &"arcane_dust"), 2 * r], [&"arcane_dust", 2 + 2 * r]]
	if r >= 2:
		inputs.append([&"wisp_mote", r])
	if r >= 3:
		inputs.append([&"champion_essence", 1])
	return {"inputs": inputs, "gold": 60 * r * r, "level": [4, 9, 14][r - 1]}

static func tech_cost(rank: int) -> Dictionary:
	var r := clampi(rank, 1, TECH_MAX)
	var inputs: Array = [[&"iron_shard", 4 * r], [&"steel_ingot", r]]
	if r >= 3:
		inputs.append([&"orc_tusk", r - 1])
	if r >= 4:
		inputs.append([&"ogre_sinew", 1])
	if r >= 5:
		inputs.append([&"rune_plate", 2])
		inputs.append([&"champion_essence", 1])
	return {"inputs": inputs, "gold": 30 * r * r, "level": [2, 5, 8, 12, 16][r - 1]}

static func roman(n: int) -> String:
	return ["", "I", "II", "III", "IV", "V"][clampi(n, 0, 5)]
