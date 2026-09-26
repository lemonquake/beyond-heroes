class_name StatDefs
## Display metadata for every stat key. Percent-type stats are stored as fractions (0.05 == 5%).

enum Fmt { INT, DEC1, PCT, MULT, SPEED, SECONDS }

# key: [display name, format, short description]
const DEFS := {
	&"str": ["Strength", Fmt.INT, "Physical weapon damage, heavy weapons, Defense, knockback, Maximum HP."],
	&"agi": ["Agility", Fmt.INT, "Movement speed, Evasion, Attack Speed, light weapons, dodge."],
	&"int": ["Intelligence", Fmt.INT, "Magic damage, spell scaling, Maximum Mana."],
	&"wis": ["Wisdom", Fmt.INT, "Mana efficiency and regeneration, resistances, cooldowns."],
	&"spi": ["Spirit", Fmt.INT, "HP/Mana regeneration, healing, buff effect, status resistance."],
	&"dex": ["Dexterity", Fmt.INT, "Accuracy, Critical Chance, projectiles, blocking."],
	&"max_hp": ["Maximum HP", Fmt.INT, ""],
	&"max_mana": ["Maximum Mana", Fmt.INT, ""],
	&"hp_regen": ["HP Regeneration", Fmt.DEC1, "per second"],
	&"mana_regen": ["Mana Regeneration", Fmt.DEC1, "per second"],
	&"defense": ["Defense", Fmt.INT, "Armor rating. Converted to Physical Resistance against an attacker of your level."],
	&"phys_res": ["Physical Resistance", Fmt.PCT, ""],
	&"evasion": ["Evasion", Fmt.INT, "Chance to evade attacks depends on the attacker's Accuracy."],
	&"accuracy": ["Accuracy", Fmt.INT, "Chance to hit depends on the target's Evasion."],
	&"crit_chance": ["Critical Chance", Fmt.PCT, ""],
	&"crit_damage": ["Critical Damage", Fmt.MULT, "Damage multiplier on critical hits (base x1.50)."],
	&"move_speed": ["Movement Speed", Fmt.SPEED, ""],
	&"attack_speed": ["Attack Speed", Fmt.MULT, "Multiplier on weapon attack rate."],
	&"cast_speed": ["Cast Speed", Fmt.MULT, "Multiplier on casting animations."],
	&"block_chance": ["Block Chance", Fmt.PCT, ""],
	&"block_strength": ["Block Strength", Fmt.PCT, "Share of a blocked hit's damage that is prevented."],
	&"cdr": ["Cooldown Reduction", Fmt.PCT, ""],
	&"mana_cost_reduction": ["Mana Efficiency", Fmt.PCT, "Reduces the Mana cost of skills."],
	&"status_res": ["Status Resistance", Fmt.PCT, "Reduces status buildup and duration."],
	&"knockback_res": ["Knockback Resistance", Fmt.PCT, ""],
	&"impact_strength": ["Impact Strength", Fmt.MULT, "Multiplier on knockback you inflict and on impact damage."],
	&"phys_damage": ["Physical Damage", Fmt.PCT, "Increased physical damage."],
	&"magic_damage": ["Magic Damage", Fmt.PCT, "Increased spell damage."],
	&"elemental_damage": ["Elemental Damage", Fmt.PCT, "Increased damage of all eight elements."],
	&"damage": ["Damage", Fmt.PCT, "Increased damage of every kind."],
	&"pen_armor": ["Armor Penetration", Fmt.PCT, ""],
	&"healing": ["Healing Effectiveness", Fmt.PCT, ""],
	&"buff_effect": ["Buff Effect", Fmt.PCT, ""],
	&"life_leech": ["Life Leech", Fmt.PCT, "Share of damage dealt returned as HP."],
	&"mana_on_hit": ["Mana on Hit", Fmt.DEC1, ""],
	&"projectile_speed": ["Projectile Speed", Fmt.PCT, ""],
	&"dodge_cooldown": ["Dodge Cooldown", Fmt.SECONDS, ""],
	&"poise": ["Poise", Fmt.INT, "Stagger threshold."],
	&"valor_gain": ["Valor Gain", Fmt.PCT, ""],
	&"arcane_max": ["Maximum Arcane Charge", Fmt.INT, ""],
	&"xp_gain": ["Experience Gain", Fmt.PCT, ""],
	&"magic_find": ["Magic Find", Fmt.PCT, "Better rarity on drops."],
	&"gold_find": ["Gold Find", Fmt.PCT, ""],
	&"weapon_damage": ["Weapon Damage", Fmt.PCT, "Increased damage with weapon attacks."],
	&"heavy_damage": ["Heavy Attack Damage", Fmt.PCT, ""],
	&"impact_damage": ["Impact Damage", Fmt.PCT, "Increased damage from collisions caused by knockback."],
	&"burn_damage": ["Burning Damage", Fmt.PCT, ""],
	&"stagger_power": ["Stagger Strength", Fmt.PCT, "Increased poise damage (stagger) your hits deal."],
	&"projectile_damage": ["Projectile Damage", Fmt.PCT, "Increased damage of arrows, bolts and other projectiles."],
	&"status_power": ["Status Chance", Fmt.PCT, "Increased buildup of Burning, Chill, Shock, Curse and other statuses you inflict."],
	&"mana_leech": ["Mana Steal", Fmt.PCT, "Share of damage dealt returned as Mana."],
	&"pen_elemental": ["Elemental Penetration", Fmt.PCT, "Ignores this much of the target's resistance to all eight elements."],
	&"skill_levels": ["Skill Levels", Fmt.INT, "Added to the rank of every skill you have learned."],
	&"outgoing_damage": ["Damage Dealt", Fmt.MULT, "Multiplier on all damage you deal (Weakened, Empowered)."],
	&"damage_taken": ["Damage Taken", Fmt.MULT, "Multiplier on all damage you take (Overcharged, Fortified)."],
	&"parry_window": ["Parry Window", Fmt.SECONDS, "Raising your guard this soon before a hit parries it: no damage and a counter opening."],
	&"dodge_distance": ["Dodge Distance", Fmt.PCT, "Increased distance of your dodge roll."],
	&"accuracy_chance": ["Hit Chance", Fmt.PCT, "Chance to hit a same-level enemy with average Evasion."],
	&"evade_chance": ["Evade Chance", Fmt.PCT, "Chance to evade a same-level enemy's attack (cap 50%)."],
	&"physical_armor_dr": ["Armor Reduction", Fmt.PCT, "Physical damage prevented by Defense against a same-level attacker."],
	&"res_cap": ["Resistance Cap", Fmt.PCT, ""],
	&"accuracy_flat": ["Accuracy", Fmt.INT, ""],
}

static func name_of(stat: StringName) -> String:
	if DEFS.has(stat):
		return DEFS[stat][0]
	var s := String(stat)
	for prefix in ["res_", "dmg_", "pen_", "added_", "status_"]:
		if s.begins_with(prefix):
			var el := Elements.from_key(StringName(s.substr(prefix.length())))
			var en := Elements.NAMES[el]
			match prefix:
				"res_": return "%s Resistance" % en
				"dmg_": return "%s Damage" % en
				"pen_": return "%s Penetration" % en
				"added_": return "Added %s Damage" % en
				"status_": return "%s Buildup" % en
	return s.capitalize()

static func fmt_of(stat: StringName) -> int:
	if DEFS.has(stat):
		return DEFS[stat][1]
	var s := String(stat)
	if s.begins_with("added_"):
		return Fmt.INT
	return Fmt.PCT

static func desc_of(stat: StringName) -> String:
	return DEFS[stat][2] if DEFS.has(stat) else ""

static func format_value(stat: StringName, v: float) -> String:
	match fmt_of(stat):
		Fmt.INT: return str(roundi(v))
		Fmt.DEC1: return "%.1f" % v
		Fmt.PCT: return "%s%%" % _num(v * 100.0)
		Fmt.MULT: return "x%.2f" % v
		Fmt.SPEED: return "%.2f m/s" % v
		Fmt.SECONDS: return "%.1f s" % v
	return str(v)

static func _num(x: float) -> String:
	if absf(x - roundf(x)) < 0.05:
		return str(roundi(x))
	return "%.1f" % x

## Human-readable modifier line for tooltips.
static func format_modifier(stat: StringName, op: int, v: float) -> String:
	var n := name_of(stat)
	var sgn := "+" if v >= 0.0 else "-"
	var av := absf(v)
	match op:
		StatModifier.Op.FLAT:
			match fmt_of(stat):
				Fmt.INT: return "%s%d %s" % [sgn, roundi(av), n]
				Fmt.DEC1: return "%s%.1f %s" % [sgn, av, n]
				Fmt.PCT: return "%s%s%% %s" % [sgn, _num(av * 100.0), n]
				Fmt.MULT: return "%s%s%% %s" % [sgn, _num(av * 100.0), n]
				Fmt.SPEED: return "%s%.2f %s" % [sgn, av, n]
				Fmt.SECONDS: return "%s%.1fs %s" % [sgn, av, n]
		StatModifier.Op.INC:
			return "%s%% %s %s" % [_num(av * 100.0), "increased" if v >= 0.0 else "reduced", n]
		StatModifier.Op.MORE:
			return "%s%% %s %s" % [_num(av * 100.0), "more" if v >= 0.0 else "less", n]
	return "%s %s" % [n, v]
