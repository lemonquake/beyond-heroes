class_name DataEnemiesLegend
## bh-021: the Forsaken Legion on the Weeping Causeway (docs/LORE.md §10) — Kethrax, Chain-Marshal of the Forsaken
## (boss), and the Legion's rank and file. The Legion are knights who forsook the oath of the Binding for the Pact of
## Wrath's Rekindling; the broken oath hollowed them. They reuse the garrison's bodies (hollow_soldier, bonewarden)
## tinted in Legion iron and violet.

const CHAR := "res://assets/characters/%s.glb"

static func defs() -> Array:
	return [
		DataEnemies._e(&"forsaken_legionnaire", "Forsaken Legionnaire", &"fodder", {"family": &"undead", "role_name": "Legion blade",
			"model": CHAR % "hollow_soldier", "tint": Color(0.3, 0.26, 0.36), "model_scale": 1.05,
			"hp": 52.0, "damage_min": 5.0, "damage_max": 9.0, "defense": 16.0,
			"evasion": 8.0, "accuracy": 32.0, "move_speed": 3.9, "weight": 1.1, "poise": 22.0, "affinity": Elements.DARK,
			"resistances": {Elements.DARK: 0.3, Elements.LIGHT: -0.25}, "preferred_range": 1.7,
			"attacks": [{"id": &"slash", "anim": &"sword_1", "range": 2.2, "mult": 1.0, "knockback": 2.5, "poise": 10.0, "cooldown": 1.6, "kind": "melee", "arc": 100.0},
				{"id": &"combo", "anim": &"sword_2", "range": 2.2, "mult": 1.15, "knockback": 3.0, "poise": 12.0, "cooldown": 3.0, "kind": "melee", "arc": 110.0},
				{"id": &"oathbreak", "anim": &"sword_heavy", "range": 2.4, "mult": 1.7, "knockback": 6.0, "poise": 22.0, "cooldown": 5.5, "kind": "melee",
					"arc": 60.0, "windup": 0.3, "element": Elements.DARK}],
			"xp_mult": 1.3, "drop_chance": 0.35, "loot": [[&"iron_shard", 0.45, 1, 3], [&"grave_dust", 0.3, 1, 2]],
			"sounds": {"hurt": &"hit_armor", "death": &"skeleton_death", "idle": &"skeleton_rattle"},
			"lore": "A knight of the Forsaken Legion. It swore the Rekindling's oath and the oath hollowed it out; the violet light in its helm is all that is left."}),
		DataEnemies._e(&"forsaken_chainguard", "Forsaken Chainguard", &"shield", {"family": &"undead", "role_name": "Legion shield",
			"model": CHAR % "bonewarden", "tint": Color(0.26, 0.24, 0.32), "model_scale": 1.08,
			"hp": 88.0, "damage_min": 6.0, "damage_max": 11.0, "defense": 44.0, "stagger_resist": 1.6,
			"evasion": 4.0, "accuracy": 32.0, "move_speed": 3.1, "weight": 1.7, "poise": 44.0, "knockback_res": 0.35, "affinity": Elements.DARK,
			"resistances": {Elements.DARK: 0.3, Elements.LIGHT: -0.25}, "preferred_range": 1.8, "blocks_front": true, "guard_break": 60.0,
			"attacks": [{"id": &"bash", "anim": &"shield_bash", "range": 2.0, "mult": 1.1, "knockback": 7.0, "poise": 20.0, "cooldown": 2.2, "kind": "melee", "arc": 80.0},
				{"id": &"hook", "anim": &"axe_1", "range": 6.0, "min_range": 2.6, "mult": 0.6, "knockback": 0.0, "poise": 4.0, "cooldown": 7.0,
					"kind": "tongue", "pull": 5.0, "windup": 0.45}],
			"xp_mult": 1.8, "drop_chance": 0.4, "loot": [[&"iron_shard", 0.5, 2, 4], [&"grave_dust", 0.4, 1, 2]],
			"sounds": {"hurt": &"hit_armor", "death": &"skeleton_death", "idle": &"skeleton_rattle"},
			"lore": "Legion shield-bearers carry a hooked chain. Keep your distance and they will drag you in; close in and break the guard."}),
		# ------------------------------------------------------------------ BOSS
		DataEnemies._e(&"kethrax", "Kethrax, Chain-Marshal of the Forsaken", &"boss", {"family": &"undead", "role_name": "Boss",
			"tint": Color(1, 1, 1), "weapon": "res://assets/weapons/legend/kethrax_mace.glb",
			"hp": 1900.0, "damage_min": 15.0, "damage_max": 24.0, "defense": 55.0,
			"evasion": 5.0, "accuracy": 58.0, "move_speed": 3.7, "weight": 12.0, "poise": 240.0, "knockback_res": 0.7, "status_res": 0.3,
			"affinity": Elements.DARK, "resistances": {Elements.DARK: 0.5, Elements.ICE: 0.2, Elements.LIGHT: -0.3},
			"preferred_range": 3.0, "body_radius": 1.2, "body_height": 3.6, "model_scale": 1.55, "aggro_range": 34.0, "leash_range": 200.0,
			"can_be_elite": false, "status_immune": [&"frozen", &"stunned"], "sight_range": 34.0,
			"phases": [{"hp": 1.0, "name": "Chain-Marshal"}, {"hp": 0.66, "name": "The Legion Answers"}, {"hp": 0.33, "name": "Stolen Wrath"}],
			"attacks": [
				{"id": &"mace_sweep", "anim": &"boss_sweep", "range": 5.0, "mult": 1.0, "knockback": 12.0, "poise": 40.0, "cooldown": 3.2, "kind": "aoe",
					"radius": 5.0, "arc": 220.0, "windup": 0.85, "telegraph": "cone", "self_centered": true},
				{"id": &"mace_slam", "anim": &"boss_slam", "range": 6.0, "mult": 1.7, "knockback": 16.0, "poise": 60.0, "cooldown": 6.0, "kind": "aoe",
					"radius": 3.8, "windup": 1.15, "telegraph": "circle", "offset": 3.0, "element": Elements.EARTH},
				{"id": &"chain_lash", "anim": &"cast_heavy", "range": 14.0, "min_range": 5.0, "mult": 0.7, "knockback": 0.0, "poise": 8.0,
					"cooldown": 8.0, "kind": "tongue", "pull": 10.0, "windup": 0.6, "element": Elements.DARK},
				{"id": &"charge", "anim": &"boss_charge", "range": 22.0, "min_range": 7.0, "mult": 1.5, "knockback": 18.0, "poise": 50.0, "cooldown": 11.0,
					"kind": "charge", "width": 3.0, "windup": 1.2, "telegraph": "line", "speed": 15.0},
				{"id": &"binding_chains", "anim": &"boss_roar", "range": 30.0, "mult": 0.55, "element": Elements.DARK, "cooldown": 13.0, "kind": "pools",
					"radius": 2.6, "count": 5, "windup": 1.0, "telegraph": "circle", "duration": 7.0, "phase": 2, "status": {&"slowed": 100.0}},
				{"id": &"call_legion", "anim": &"boss_summon", "range": 40.0, "cooldown": 22.0, "kind": "summon", "summon": &"forsaken_legionnaire", "count": 2, "phase": 2},
				{"id": &"stolen_wrath", "anim": &"boss_slam", "range": 9.0, "mult": 2.1, "element": Elements.FIRE, "knockback": 20.0, "poise": 80.0, "cooldown": 9.0,
					"kind": "aoe", "radius": 9.0, "windup": 1.5, "telegraph": "ring", "self_centered": true, "inner_radius": 3.5, "phase": 3},
			],
			"xp_mult": 22.0, "drop_chance": 1.0, "gold": Vector2i(140, 240),
			"loot": [[&"quest_chain_seal", 1.0, 1, 1], [&"aether_shard", 1.0, 2, 3], [&"champion_essence", 1.0, 2, 3]],
			"sounds": {"hurt": &"hit_armor", "death": &"boss_roar", "idle": &"boss_roar"},
			"hit_material": &"bone", "blood": Color(0.4, 0.15, 0.6), "death_style": &"fall", "corpse_time": 60.0,
			"lore": "The Chain-Marshal of the Forsaken Legion. Three winters ago he bound Aljay in Tyrant-chains on this causeway; Aljay broke his lance in Kethrax's chest, and the wound still burns with the wrath it stole."}),
	]
