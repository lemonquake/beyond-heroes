class_name DataClassRework
## Signature mechanics scale linearly from level 1 to 25; runtime caps also cover bonus skill levels.

const CAPS := {&"damage_return": 0.40, &"debuff_regen": 0.005, &"double_attack": 0.65,
	&"paralyzing_attack": 0.85, &"bloodsucker": 0.35, &"bloodcurse": 0.70, &"knee_shot": 0.40,
	&"split_shot": 0.75, &"arcane_arts": 0.50, &"retaliation": 1.0}

static func passive(id: StringName, name: String, icon: String, pos: Vector2, page: int, req: Array, desc: String, flags: Dictionary, mods: Array = []) -> Dictionary:
	var n := DataSkillsExt._pas(id, name, pos, page, req, 2, desc, mods, flags)
	n.max_rank = 25
	n.icon = DataSkillsExt.ICON % icon
	return n

static func nodes(cls: StringName) -> Array:
	match cls:
		&"knight":
			return [
				passive(&"steadfast", "Steadfast", "toughness", Vector2(7, 4), 2, [&"iron_skin"], "+{0}% Knockback Resistance and +{1}% Block Chance.", {}, [[&"knockback_res", 0, 0.15, 0.45 / 24.0], [&"block_chance", 0, 0.03, 0.12 / 24.0]]),
				passive(&"damage_return", "Damage Return", "aura_thorns", Vector2(7, 6), 2, [&"steadfast"], "Return {f0}% of direct hit damage to the attacker. Cannot trigger another return or counterattack.", {&"damage_return": [0.10, 0.30 / 24.0]}),
				passive(&"debuff_regen", "Enduring Recovery", "second_wind", Vector2(4, 6), 2, [&"second_wind"], "Each distinct active debuff restores an extra {f0}% of Maximum HP per second. Healing reductions still apply.", {&"debuff_regen": [0.001, 0.004 / 24.0]}),
			]
		&"shadowblade":
			return [
				passive(&"double_attack", "Double Attack", "twin_fang", Vector2(1, 6), 1, [&"ruthless"], "Basic melee hits repeat after 0.12 s for {f0}% weapon damage. 1.2 s cooldown. The repeat cannot trigger attack passives.", {&"double_attack": [0.35, 0.30 / 24.0]}),
				passive(&"paralyzing_attack", "Paralyzing Attack", "crippling_star", Vector2(4, 6), 1, [&"opportunist"], "Basic melee hits slow movement by {f0}% for 0.1 s.", {&"paralyzing_attack": [0.30, 0.55 / 24.0]}),
				passive(&"bloodsucker", "Bloodsucker", "venom_strike", Vector2(7, 4), 1, [&"fleet_step"], "Every second successful basic melee attack heals you for {f0}% of its first target's damage.", {&"bloodsucker": [0.10, 0.25 / 24.0]}),
				passive(&"bloodcurse", "Bloodcurse", "dread_mark", Vector2(7, 6), 1, [&"bloodsucker"], "Basic melee hits reduce all target HP restoration by {f0}% for 4 s.", {&"bloodcurse": [0.20, 0.50 / 24.0]}),
			]
		&"ranger":
			return [
				passive(&"knee_shot", "Knee Shot", "power_shot", Vector2(1, 6), 1, [&"piercing_arrows"], "Basic arrows have a 25% chance to deal {f0}% additional damage and stun for 0.4 s. Respects stun immunity.", {&"knee_shot": [0.10, 0.30 / 24.0]}),
				passive(&"split_shot", "Split Shot", "multishot", Vector2(4, 6), 1, [&"trapmaster"], "Basic bow shots have a 30% chance to split into 3-8 arrows (by level), each dealing {f0}% damage. One hit per enemy per split volley.", {&"split_shot": [0.50, 0.25 / 24.0]}),
			]
		&"mage":
			return [
				passive(&"arcane_arts", "Arcane Arts", "inner_fire", Vector2(4, 4), 1, [&"tide_stone_mastery"], "Paid spells have a 30% chance to refund {f0}% of their actual Mana cost. Echoes do not refund Mana.", {&"arcane_arts": [0.10, 0.40 / 24.0]}),
				spell_node(&"gravity_pull", "arcane_surge", Vector2(1, 0), []),
				spell_node(&"spike_tentacle", "stone_spear", Vector2(1, 2), [&"gravity_pull"]),
				spell_node(&"mana_siphon", "radiant_ward", Vector2(4, 0), []),
				spell_node(&"dark_arts", "shadow_curse", Vector2(4, 2), [&"mana_siphon"]),
			]
	return []

static func spell_node(id: StringName, icon: String, pos: Vector2, req: Array) -> Dictionary:
	var n := DataSkillsExt._sk(id, pos, 2, req, 4 if req.is_empty() else 8)
	n.icon = DataSkillsExt.ICON % icon
	n.max_rank = 25
	return n

static func skills() -> Array:
	return [
		DataSkills._s(&"gravity_pull", "Gravity Pull", &"mage", &"gravity_pull", {"icon": DataSkills.ICON % "arcane_surge", "element": Elements.DARK, "anim": &"cast_area", "max_rank": 25, "mana_cost": 18.0, "mana_per_rank": 0.8, "cooldown": 9.0,
			"description": "Instantly pull nearby enemies toward the selected center, then deal {damage_min}-{damage_max} Dark damage within {radius} m. Walls and knockback resistance limit the pull.",
			"params": {"damage_min": 18.0, "damage_max": 26.0, "radius": 6.0, "range": 16.0}, "per_rank": {"damage_min": 4.0, "damage_max": 6.0}, "sound_cast": &"arcane_surge"}),
		DataSkills._s(&"spike_tentacle", "Spike Tentacle", &"mage", &"spike_tentacle", {"icon": DataSkills.ICON % "stone_spear", "element": Elements.DARK, "anim": &"cast_heavy", "max_rank": 25, "mana_cost": 14.0, "mana_per_rank": 0.6, "cooldown": 6.0,
			"description": "Spikes erupt in a {length} m line, dealing {damage_min}-{damage_max} Dark damage and stunning for {stun_duration} s (maximum 1.6 s).",
			"params": {"damage_min": 15.0, "damage_max": 22.0, "length": 12.0, "width": 2.0, "stun_duration": 0.2}, "per_rank": {"damage_min": 3.0, "damage_max": 4.0, "stun_duration": 1.4 / 24.0}, "sound_cast": &"cast_earth"}),
		DataSkills._s(&"mana_siphon", "Mana Siphon", &"mage", &"mana_siphon", {"icon": DataSkills.ICON % "radiant_ward", "element": Elements.DARK, "anim": &"cast_area", "max_rank": 25, "mana_cost": 0.0, "mana_per_rank": 0.0, "cooldown": 12.0,
			"description": "Drain up to {drain} Mana from each enemy within {radius} m and recover only the Mana actually drained. Cannot drain through walls or from empty pools.",
			"params": {"drain": 8.0, "radius": 7.0}, "per_rank": {"drain": 1.5}, "sound_cast": &"dark_cast"}),
		DataSkills._s(&"dark_arts", "Dark Arts", &"mage", &"dark_arts", {"icon": DataSkills.ICON % "shadow_curse", "element": Elements.DARK, "anim": &"cast_quick", "max_rank": 25, "mana_cost": 12.0, "mana_per_rank": 0.5, "cooldown": 4.0,
			"description": "Deal {damage_min}-{damage_max} Dark magic damage to the enemy nearest your aim and apply one random curse: Weakened, Armor Broken, Silenced, or Bloodcurse (35% less healing), for {duration} s.",
			"params": {"damage_min": 16.0, "damage_max": 24.0, "range": 18.0, "duration": 3.0}, "per_rank": {"damage_min": 3.5, "damage_max": 5.0, "duration": 0.1}, "sound_cast": &"dark_cast"}),
	]
