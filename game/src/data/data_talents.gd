class_name DataTalents
## Passive talent trees. Minor nodes = small stat steps; major nodes = mechanics; keystones = build-defining trade-offs.

const ICON := "res://assets/ui/icons/talents/%s.svg"
const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC
const M := StatModifier.Op.MORE

static func _n(id: StringName, name: String, kind: String, icon: String, pos: Vector2, max_rank: int, requires: Array, desc: String, extra := {}) -> Dictionary:
	var d := {"id": id, "name": name, "kind": kind, "icon": ICON % icon, "pos": pos, "max_rank": max_rank,
		"cost": 1, "requires": requires, "desc": desc}
	d.merge(extra, true)
	return d

static func knight() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"knight_talents"
	t.display_name = "Knight Talents"
	t.points_kind = &"talent"
	t.branches = [{"name": "Warlord", "x": 1.0, "color": Color(0.9, 0.35, 0.25)}, {"name": "Guardian", "x": 4.0, "color": Color(0.75, 0.78, 0.9)},
		{"name": "Juggernaut", "x": 7.0, "color": Color(0.85, 0.6, 0.3)}]
	t.nodes = [
		# Warlord
		_n(&"k_str", "Might", "minor", "minor_str", Vector2(1, 0), 3, [], "+3 Strength per rank.", {"mods": [[&"str", F, 3]]}),
		_n(&"k_sword", "Blade Mastery", "minor", "sword_mastery", Vector2(0, 1), 3, [&"k_str"], "Sword and Greatsword attacks deal 6% increased damage per rank.",
			{"mods": [[&"dmg_wt_sword", I, 0.06], [&"dmg_wt_greatsword", I, 0.06]]}),
		_n(&"k_crit", "Killing Blow", "minor", "crit", Vector2(2, 1), 3, [&"k_str"], "+1.5% Critical Chance per rank.", {"mods": [[&"crit_chance", F, 0.015]]}),
		_n(&"k_heavy", "Heavy Hands", "minor", "heavy_hands", Vector2(1, 2), 2, [&"k_sword", &"k_crit"], "Heavy attacks deal 15% increased damage per rank.",
			{"mods": [[&"heavy_damage", I, 0.15]]}),
		_n(&"k_crit_cd", "Relentless Assault", "major", "crit_cooldown", Vector2(0, 3), 1, [&"k_heavy"], "Critical hits reduce all skill cooldowns by 0.3 s.",
			{"flags": {&"crit_cdr": 0.3}, "req_tree_points": 5}),
		_n(&"k_valor", "Valiant Heart", "major", "valor", Vector2(2, 3), 1, [&"k_heavy"], "+30% Valor generation. Resolute begins at 40 Valor instead of 50.",
			{"mods": [[&"valor_gain", I, 0.3]], "flags": {&"resolute_40": 1.0}, "req_tree_points": 5}),
		_n(&"k_critdmg", "Executioner", "minor", "crit", Vector2(1, 4), 3, [&"k_crit_cd", &"k_valor"], "+10% Critical Damage per rank.", {"mods": [[&"crit_damage", F, 0.10]]}),
		# Guardian
		_n(&"k_vit", "Vitality", "minor", "vitality", Vector2(4, 0), 3, [], "+6% Maximum HP per rank.", {"mods": [[&"max_hp", I, 0.06]]}),
		_n(&"k_armor", "Tempered Steel", "minor", "armor", Vector2(3, 1), 3, [&"k_vit"], "+10% Defense per rank.", {"mods": [[&"defense", I, 0.10]]}),
		_n(&"k_fire_res", "Flameward", "minor", "fire_res", Vector2(5, 1), 2, [&"k_vit"], "+8% Fire Resistance per rank.", {"mods": [[&"res_fire", F, 0.08]]}),
		_n(&"k_block", "Bulwark", "minor", "bulwark", Vector2(4, 2), 3, [&"k_armor", &"k_fire_res"], "+3% Block Chance per rank.", {"mods": [[&"block_chance", F, 0.03]]}),
		_n(&"k_block_mana", "Disciplined Guard", "major", "block_mana", Vector2(3, 3), 1, [&"k_block"], "Blocking restores 4 Mana and 2% of Maximum HP.",
			{"flags": {&"block_mana": 4.0}, "req_tree_points": 5}),
		_n(&"k_counter", "Riposte", "major", "counter", Vector2(5, 3), 1, [&"k_block"], "After a perfect block, your next attack within 2 s is a guaranteed critical hit.",
			{"flags": {&"counter": 1.0}, "req_tree_points": 5}),
		_n(&"k_unbreakable", "Unbreakable", "keystone", "keystone_unbreakable", Vector2(4, 5), 1, [&"k_block_mana", &"k_counter"],
			"You cannot be staggered and take 60% less knockback. +15% Block Strength. 10% less Movement Speed.",
			{"mods": [[&"knockback_res", F, 0.6], [&"block_strength", F, 0.15], [&"move_speed", M, -0.10]], "flags": {&"unstaggerable": 1.0},
			"req_tree_points": 10, "exclusive": "knight_keystone"}),
		# Juggernaut
		_n(&"k_spi", "Iron Will", "minor", "minor_spi", Vector2(7, 0), 3, [], "+3 Spirit per rank.", {"mods": [[&"spi", F, 3]]}),
		_n(&"k_momentum", "Momentum", "minor", "momentum", Vector2(6, 1), 3, [&"k_spi"], "+10% Impact Strength per rank.", {"mods": [[&"impact_strength", I, 0.10]]}),
		_n(&"k_impact", "Crushing Walls", "minor", "heavy_hands", Vector2(8, 1), 3, [&"k_spi"], "+20% Impact Damage per rank.", {"mods": [[&"impact_damage", I, 0.20]]}),
		_n(&"k_earth", "Earthbound", "minor", "minor_str", Vector2(7, 2), 2, [&"k_momentum", &"k_impact"], "+12% Earth Damage and +4% Knockback Resistance per rank.",
			{"mods": [[&"dmg_earth", I, 0.12], [&"knockback_res", F, 0.04]]}),
		_n(&"k_frozen", "Shatterpoint", "major", "frozen_impact", Vector2(8, 3), 1, [&"k_earth"], "Frozen enemies take 40% more impact damage from collisions.",
			{"flags": {&"frozen_impact": 0.4}, "req_tree_points": 5}),
		_n(&"k_juggernaut", "Juggernaut", "keystone", "keystone_juggernaut", Vector2(7, 5), 1, [&"k_frozen", &"k_earth"],
			"Impact damage is doubled and enemies thrown into other enemies pass on all their momentum. 15% less Attack Speed.",
			{"mods": [[&"impact_damage", M, 1.0], [&"attack_speed", M, -0.15]], "flags": {&"full_transfer": 1.0}, "req_tree_points": 10, "exclusive": "knight_keystone"}),
	]
	return t

static func mage() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"mage_talents"
	t.display_name = "Mage Talents"
	t.points_kind = &"talent"
	t.branches = [{"name": "Pyre & Storm", "x": 1.0, "color": Color(1.0, 0.5, 0.2)}, {"name": "Frost & Tide", "x": 4.0, "color": Color(0.45, 0.8, 1.0)},
		{"name": "Arcana", "x": 7.0, "color": Color(0.7, 0.5, 1.0)}]
	t.nodes = [
		# Pyre & Storm
		_n(&"m_int", "Brilliance", "minor", "minor_int", Vector2(1, 0), 3, [], "+3 Intelligence per rank.", {"mods": [[&"int", F, 3]]}),
		_n(&"m_fire", "Pyromancy", "minor", "pyromancy", Vector2(0, 1), 3, [&"m_int"], "+10% Fire Damage per rank.", {"mods": [[&"dmg_fire", I, 0.10]]}),
		_n(&"m_storm", "Stormcaller", "minor", "storm", Vector2(2, 1), 3, [&"m_int"], "+10% Lightning Damage per rank.", {"mods": [[&"dmg_lightning", I, 0.10]]}),
		_n(&"m_burn_spread", "Wildfire", "major", "burning_spread", Vector2(0, 3), 1, [&"m_fire"], "Fire spells spread Burning to one enemy within 4 m of each target they ignite.",
			{"flags": {&"burn_spread": 1.0}, "req_tree_points": 4}),
		_n(&"m_conduit", "Conduit", "major", "conduit", Vector2(2, 3), 1, [&"m_storm"], "Chain Lightning chains 2 more times. Shock you apply is 5% stronger.",
			{"flags": {&"conduit": 2.0}, "req_tree_points": 4}),
		_n(&"m_crit", "Focused Mind", "minor", "crit", Vector2(1, 4), 3, [&"m_burn_spread", &"m_conduit"], "+1.5% Critical Chance per rank.", {"mods": [[&"crit_chance", F, 0.015]]}),
		# Frost & Tide
		_n(&"m_wis", "Insight", "minor", "minor_wis", Vector2(4, 0), 3, [], "+3 Wisdom per rank.", {"mods": [[&"wis", F, 3]]}),
		_n(&"m_ice", "Permafrost", "minor", "permafrost", Vector2(3, 1), 3, [&"m_wis"], "+10% Ice Damage per rank.", {"mods": [[&"dmg_ice", I, 0.10]]}),
		_n(&"m_water", "Tidecaller", "minor", "tides", Vector2(5, 1), 3, [&"m_wis"], "+10% Water Damage per rank.", {"mods": [[&"dmg_water", I, 0.10]]}),
		_n(&"m_frozen_impact", "Brittle Bones", "major", "frozen_impact", Vector2(3, 3), 1, [&"m_ice"], "Frozen enemies take 40% more physical impact damage.",
			{"flags": {&"frozen_impact": 0.4}, "req_tree_points": 4}),
		_n(&"m_fire_res", "Emberskin", "minor", "fire_res", Vector2(5, 3), 2, [&"m_water"], "+8% Fire Resistance and +4% Ice Resistance per rank.",
			{"mods": [[&"res_fire", F, 0.08], [&"res_ice", F, 0.04]]}),
		_n(&"m_elem", "Elemental Focus", "minor", "elemental_focus", Vector2(4, 4), 3, [&"m_frozen_impact", &"m_fire_res"], "+4% penetration of Fire, Ice, Lightning and Water per rank.",
			{"mods": [[&"pen_fire", F, 0.04], [&"pen_ice", F, 0.04], [&"pen_lightning", F, 0.04], [&"pen_water", F, 0.04]]}),
		_n(&"m_overload", "Elemental Overload", "keystone", "keystone_elemental_overload", Vector2(4, 5), 1, [&"m_elem"],
			"Hitting an enemy with three different elements within 4 s grants 40% more Elemental Damage for 5 s. Your Mana regeneration is 20% lower.",
			{"mods": [[&"mana_regen", M, -0.2]], "flags": {&"overload": 0.4}, "req_tree_points": 10, "exclusive": "mage_keystone"}),
		# Arcana
		_n(&"m_spi", "Serenity", "minor", "minor_spi", Vector2(7, 0), 3, [], "+3 Spirit per rank.", {"mods": [[&"spi", F, 3]]}),
		_n(&"m_mana", "Arcane Mind", "minor", "arcane_mind", Vector2(6, 1), 3, [&"m_spi"], "+8% Maximum Mana per rank.", {"mods": [[&"max_mana", I, 0.08]]}),
		_n(&"m_regen", "Mana Flow", "minor", "mana_flow", Vector2(8, 1), 3, [&"m_spi"], "+12% Mana Regeneration per rank.", {"mods": [[&"mana_regen", I, 0.12]]}),
		_n(&"m_block_mana", "Spellguard", "major", "block_mana", Vector2(6, 3), 1, [&"m_mana"], "Blocking or evading restores 6 Mana.",
			{"flags": {&"block_mana": 6.0, &"evade_mana": 6.0}, "req_tree_points": 4}),
		_n(&"m_crit_cd", "Temporal Flux", "major", "crit_cooldown", Vector2(8, 3), 1, [&"m_regen"], "Critical hits reduce all skill cooldowns by 0.3 s.",
			{"flags": {&"crit_cdr": 0.3}, "req_tree_points": 4}),
		_n(&"m_archmage", "Archmage", "keystone", "keystone_archmage", Vector2(7, 5), 1, [&"m_block_mana", &"m_crit_cd"],
			"+30% Maximum Mana and +1 maximum Arcane Charge. Spells deal 1% more damage per 25 Maximum Mana (at most 50% more). Spells cost 15% more.",
			{"mods": [[&"max_mana", I, 0.30], [&"arcane_max", F, 1.0], [&"mana_cost_reduction", F, -0.15]], "flags": {&"archmage": 25.0},
			"req_tree_points": 10, "exclusive": "mage_keystone"}),
	]
	return t
