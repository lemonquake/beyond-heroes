class_name DataSpecialWeapons
## bh-024: Legendary special weapons made from the models in models/special_weapon/ (each converted to
## res://assets/weapons/special/<id>.glb, its icon to res://assets/ui/icons/items3d/<id>.png). They drop and sell as
## ordinary Legendary pieces; the "alj" cheat (Cheats) hands the hero every one of them as an Unbound variant, which has
## no level, attribute or class-rank requirement (ItemInstance.unbound, Equipment.check).
##
## The models were not in the repository when the slot and the cheat were written, so the table is empty: add one row
## per model, then drop the GLB and icon in place (docs/SPECIAL_WEAPONS.md).
##   [id, name, weapon type, level, attacks per second, element, power id, requirements, lore]
const ROWS := []

const MODEL_DIR := "res://assets/weapons/special/%s.glb"

static func bases() -> Array:
	var out := []
	for r in ROWS:
		var aps := float(r[4])
		var dmg := DataItems.roster_damage(StringName(r[2]), int(r[3]), aps)
		var b := DataItems._b(StringName(r[0]), "", &"weapon", "", {"unique_name": r[1], "fixed_rarity": BH.Rarity.LEGENDARY,
			"weapon_type": StringName(r[2]), "level_req": int(r[3]), "attacks_per_second": aps, "damage_min": dmg.x * 1.15,
			"damage_max": dmg.y * 1.15, "element": int(r[5]), "element_share": 0.35 if int(r[5]) != Elements.PHYSICAL else 0.0,
			"fixed_powers": [StringName(r[6])] if String(r[6]) != "" else [], "requirements": r[7], "lore": r[8],
			"value": 400 + int(r[3]) * 8, "drop_weight": 0, "tier": 3})
		b.display_name = String(StringName(r[2])).capitalize()
		b.model = MODEL_DIR % r[0]
		b.icon = DataItems.ICON3D % r[0]
		out.append(b)
	return out

static func ids() -> Array:
	return ROWS.map(func(r): return StringName(r[0]))

## An Unbound copy of a special weapon (or of any equipment base), at the hero's level.
static func unbound(base_id: StringName, level: int) -> ItemInstance:
	var it := DB.make_item(base_id, BH.Rarity.LEGENDARY, maxi(1, level), hash("alj%s" % base_id))
	if it:
		it.unbound = true
	return it
