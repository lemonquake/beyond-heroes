class_name DataTalentsExt
## bh-010: talent trees of the Ranger and the Shadowblade. Same shape as the Knight/Mage trees: minor nodes are small
## stat steps, majors change mechanics, keystones are exclusive build-defining trade-offs (one per hero).

const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC
const M := StatModifier.Op.MORE

static func _n(id: StringName, name: String, kind: String, icon: String, pos: Vector2, max_rank: int, requires: Array, desc: String, extra := {}) -> Dictionary:
	return DataTalents._n(id, name, kind, icon, pos, max_rank, requires, desc, extra)

static func ranger() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"ranger_talents"
	t.display_name = "Ranger Talents"
	t.points_kind = &"talent"
	t.branches = [{"name": "Hawkeye", "x": 1.0, "color": Color(0.9, 0.85, 0.5)}, {"name": "Pathfinder", "x": 4.0, "color": Color(0.55, 0.85, 0.45)},
		{"name": "Trapwright", "x": 7.0, "color": Color(0.95, 0.55, 0.3)}]
	t.nodes = [
		# Hawkeye
		_n(&"r_dex", "Steady Hands", "minor", "r_dex", Vector2(1, 0), 3, [], "+3 Dexterity per rank.", {"mods": [[&"dex", F, 3]]}),
		_n(&"r_bow", "Bowyer", "minor", "r_bow", Vector2(0, 1), 3, [&"r_dex"], "Bow, crossbow and javelin attacks deal 6% increased damage per rank.",
			{"mods": [[&"dmg_wt_bow", I, 0.06], [&"dmg_wt_crossbow", I, 0.06], [&"dmg_wt_javelin", I, 0.06]]}),
		_n(&"r_crit", "Eagle Eye", "minor", "r_crit", Vector2(2, 1), 3, [&"r_dex"], "+1.5% Critical Chance per rank.", {"mods": [[&"crit_chance", F, 0.015]]}),
		_n(&"r_projdmg", "Fletcher", "minor", "r_bow", Vector2(1, 2), 2, [&"r_bow", &"r_crit"], "+10% projectile damage per rank.",
			{"mods": [[&"projectile_damage", I, 0.10]]}),
		_n(&"r_focus_major", "Hunter's Calm", "major", "r_focus", Vector2(0, 3), 1, [&"r_projdmg"], "+30% Focus gain. Focus no longer fades out of combat.",
			{"mods": [[&"focus_gain", I, 0.3]], "flags": {&"focus_hold": 1.0}, "req_tree_points": 5}),
		_n(&"r_crit_cd", "Quick Draw", "major", "crit_cooldown", Vector2(2, 3), 1, [&"r_projdmg"], "Critical hits reduce all skill cooldowns by 0.3 s.",
			{"flags": {&"crit_cdr": 0.3}, "req_tree_points": 5}),
		_n(&"keystone_sniper", "Sniper's Creed", "keystone", "keystone_sniper", Vector2(1, 5), 1, [&"r_focus_major", &"r_crit_cd"],
			"Your hits deal 30% more damage to enemies more than 10 m away and 20% less to enemies within 5 m.",
			{"flags": {&"sniper": 1.0}, "req_tree_points": 10, "exclusive": "ranger_keystone"}),
		# Pathfinder
		_n(&"r_agi", "Nimble", "minor", "minor_agi", Vector2(4, 0), 3, [], "+3 Agility per rank.", {"mods": [[&"agi", F, 3]]}),
		_n(&"r_evasion", "Elusive", "minor", "r_evasion", Vector2(3, 1), 3, [&"r_agi"], "+8% increased Evasion per rank.", {"mods": [[&"evasion", I, 0.08]]}),
		_n(&"r_vit", "Trail Rations", "minor", "vitality", Vector2(5, 1), 3, [&"r_agi"], "+5% Maximum HP per rank.", {"mods": [[&"max_hp", I, 0.05]]}),
		_n(&"r_speed", "Wayfinder", "minor", "r_speed", Vector2(4, 2), 2, [&"r_evasion", &"r_vit"], "+3% increased Movement Speed per rank.",
			{"mods": [[&"move_speed", I, 0.03]]}),
		_n(&"r_evade_mana", "Second Nature", "major", "block_mana", Vector2(3, 3), 1, [&"r_speed"], "Evading an attack restores 5 Mana.",
			{"flags": {&"evade_mana": 5.0}, "req_tree_points": 5}),
		_n(&"r_dodge_haste", "Windswift", "major", "r_speed", Vector2(5, 3), 1, [&"r_speed"], "Dodging grants 20% more Movement Speed for 2 s.",
			{"flags": {&"dodge_haste": 0.2}, "req_tree_points": 5}),
		_n(&"keystone_windrunner", "Windrunner", "keystone", "keystone_windrunner", Vector2(4, 5), 1, [&"r_evade_mana", &"r_dodge_haste"],
			"Moving builds Focus as if you stood calm, and 20% more Evasion. 15% less Maximum HP.",
			{"mods": [[&"evasion", M, 0.2], [&"max_hp", M, -0.15]], "flags": {&"windrunner": 1.0}, "req_tree_points": 10, "exclusive": "ranger_keystone"}),
		# Trapwright
		_n(&"r_wis", "Cunning", "minor", "minor_wis", Vector2(7, 0), 3, [], "+3 Wisdom per rank.", {"mods": [[&"wis", F, 3]]}),
		_n(&"r_traps", "Sharp Jaws", "minor", "r_traps", Vector2(6, 1), 3, [&"r_wis"], "+12% trap damage per rank.", {"mods": [[&"trap_damage", I, 0.12]]}),
		_n(&"r_elem", "Alchemist's Tips", "minor", "r_elemental_arrows", Vector2(8, 1), 3, [&"r_wis"], "+10% Fire and Ice damage per rank.",
			{"mods": [[&"dmg_fire", I, 0.10], [&"dmg_ice", I, 0.10]]}),
		_n(&"r_status", "Envenomed Heads", "minor", "r_elemental_arrows", Vector2(7, 2), 2, [&"r_traps", &"r_elem"], "+12% Status Chance per rank.",
			{"mods": [[&"status_power", I, 0.12]]}),
		_n(&"r_trap_count", "Minefield", "major", "r_traps", Vector2(8, 3), 1, [&"r_status"], "You may keep one more trap.",
			{"flags": {&"trap_max": 1.0}, "req_tree_points": 5}),
		_n(&"keystone_traplord", "Trap Lord", "keystone", "keystone_traplord", Vector2(7, 5), 1, [&"r_trap_count"],
			"Traps deal 35% more damage and you may keep two more. Your bow attacks deal 15% less damage.",
			{"mods": [[&"trap_damage", I, 0.35]], "flags": {&"trap_max": 2.0, &"traplord": 1.0}, "req_tree_points": 10, "exclusive": "ranger_keystone"}),
	]
	return t

static func shadowblade() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"shadowblade_talents"
	t.display_name = "Shadowblade Talents"
	t.points_kind = &"talent"
	t.branches = [{"name": "Assassin", "x": 1.0, "color": Color(0.9, 0.3, 0.35)}, {"name": "Phantom", "x": 4.0, "color": Color(0.6, 0.45, 0.9)},
		{"name": "Venomist", "x": 7.0, "color": Color(0.5, 0.9, 0.4)}]
	t.nodes = [
		# Assassin
		_n(&"s_agi", "Swiftness", "minor", "s_agi", Vector2(1, 0), 3, [], "+3 Agility per rank.", {"mods": [[&"agi", F, 3]]}),
		_n(&"s_dagger", "Knife Work", "minor", "s_dagger", Vector2(0, 1), 3, [&"s_agi"], "Daggers and claws deal 6% increased damage per rank.",
			{"mods": [[&"dmg_wt_dagger", I, 0.06], [&"dmg_wt_claw", I, 0.06]]}),
		_n(&"s_crit", "Weak Spots", "minor", "s_crit", Vector2(2, 1), 3, [&"s_agi"], "+1.5% Critical Chance per rank.", {"mods": [[&"crit_chance", F, 0.015]]}),
		_n(&"s_critdmg", "Cutthroat", "minor", "s_crit", Vector2(1, 2), 2, [&"s_dagger", &"s_crit"], "+10% Critical Damage per rank.",
			{"mods": [[&"crit_damage", F, 0.10]]}),
		_n(&"s_combo_major", "Flow", "major", "s_combo", Vector2(0, 3), 1, [&"s_critdmg"], "Critical hits with builders add one more Combo. Combo lingers 2 s longer.",
			{"flags": {&"combo_linger": 2.0}, "req_tree_points": 5}),
		_n(&"s_kill_heal", "Blood Price", "major", "crit", Vector2(2, 3), 1, [&"s_critdmg"], "Killing an enemy heals 4% of Maximum HP.",
			{"flags": {&"kill_heal": 0.04}, "req_tree_points": 5}),
		_n(&"keystone_deathmark", "Death Mark", "keystone", "keystone_deathmark", Vector2(1, 5), 1, [&"s_combo_major", &"s_kill_heal"],
			"Finishers spent at full Combo deal 40% more damage. Your builders deal 15% less damage.",
			{"flags": {&"deathmark": 0.4}, "req_tree_points": 10, "exclusive": "shadowblade_keystone"}),
		# Phantom
		_n(&"s_dex", "Poise", "minor", "minor_dex", Vector2(4, 0), 3, [], "+3 Dexterity per rank.", {"mods": [[&"dex", F, 3]]}),
		_n(&"s_evasion", "Blur", "minor", "s_evasion", Vector2(3, 1), 3, [&"s_dex"], "+8% increased Evasion per rank.", {"mods": [[&"evasion", I, 0.08]]}),
		_n(&"s_vit", "Hardened", "minor", "vitality", Vector2(5, 1), 3, [&"s_dex"], "+5% Maximum HP per rank.", {"mods": [[&"max_hp", I, 0.05]]}),
		_n(&"s_stealth", "Shadow Walker", "minor", "s_stealth", Vector2(4, 2), 2, [&"s_evasion", &"s_vit"], "Hits from Stealth deal +15% more damage per rank.",
			{"flags": {&"ambush": 0.15}}),
		_n(&"s_evade_mana", "Slip", "major", "block_mana", Vector2(3, 3), 1, [&"s_stealth"], "Evading an attack restores 5 Mana.",
			{"flags": {&"evade_mana": 5.0}, "req_tree_points": 5}),
		_n(&"s_dodge_haste", "Afterimage", "major", "s_evasion", Vector2(5, 3), 1, [&"s_stealth"], "Dodging grants 20% more Movement Speed for 2 s.",
			{"flags": {&"dodge_haste": 0.2}, "req_tree_points": 5}),
		_n(&"keystone_phantom", "Phantom Veil", "keystone", "keystone_phantom", Vector2(4, 5), 1, [&"s_evade_mana", &"s_dodge_haste"],
			"Dodging cloaks you in Stealth for 1.5 s. 15% less Maximum HP.",
			{"mods": [[&"max_hp", M, -0.15]], "flags": {&"dodge_stealth": 1.5}, "req_tree_points": 10, "exclusive": "shadowblade_keystone"}),
		# Venomist
		_n(&"s_spi", "Iron Gut", "minor", "minor_spi", Vector2(7, 0), 3, [], "+3 Spirit per rank.", {"mods": [[&"spi", F, 3]]}),
		_n(&"s_poison", "Toxicology", "minor", "s_poison", Vector2(6, 1), 3, [&"s_spi"], "+12% Damage over Time per rank.", {"mods": [[&"dot_damage", I, 0.12]]}),
		_n(&"s_bleed", "Serrated Edges", "minor", "s_bleed", Vector2(8, 1), 3, [&"s_spi"], "+10% Status Chance per rank.", {"mods": [[&"status_power", I, 0.10]]}),
		_n(&"s_trap", "Clockwork", "minor", "s_poison", Vector2(7, 2), 2, [&"s_poison", &"s_bleed"], "+12% trap and sentinel damage per rank.",
			{"mods": [[&"trap_damage", I, 0.12]]}),
		_n(&"s_poison_res", "Mithridate", "major", "s_poison", Vector2(8, 3), 1, [&"s_trap"], "+20% Status Resistance.",
			{"mods": [[&"status_res", F, 0.2]], "req_tree_points": 5}),
		_n(&"keystone_plague", "Plaguebringer", "keystone", "keystone_plague", Vector2(7, 5), 1, [&"s_poison_res"],
			"Your Damage over Time is 50% stronger and spreads to one nearby enemy when a poisoned enemy dies. 20% less critical chance.",
			{"mods": [[&"dot_damage", I, 0.5], [&"crit_chance", M, -0.2]], "flags": {&"plague": 1.0}, "req_tree_points": 10, "exclusive": "shadowblade_keystone"}),
	]
	return t
