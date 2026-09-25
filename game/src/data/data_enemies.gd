class_name DataEnemies
## Enemy archetypes and elite modifiers.

const CHAR := "res://assets/characters/%s.glb"

static func _e(id: StringName, name: String, arche: StringName, d: Dictionary) -> EnemyDef:
	var e := EnemyDef.new()
	e.id = id
	e.display_name = name
	e.archetype = arche
	e.model = CHAR % id
	for k in d:
		e.set(k, d[k])
	return e

static func build() -> Array:
	return [
		_e(&"hollow_soldier", "Hollow Soldier", &"fodder", {"hp": 42.0, "damage_min": 4.0, "damage_max": 8.0, "defense": 12.0,
			"evasion": 8.0, "accuracy": 28.0, "move_speed": 3.8, "weight": 1.0, "poise": 18.0, "affinity": Elements.DARK,
			"resistances": {Elements.DARK: 0.25, Elements.ICE: 0.1}, "preferred_range": 1.7,
			"attacks": [{"id": &"slash", "anim": &"sword_light_1", "range": 2.2, "mult": 1.0, "knockback": 2.5, "poise": 10.0, "cooldown": 1.6, "kind": "melee", "arc": 100.0},
				{"id": &"overhead", "anim": &"sword_heavy", "range": 2.4, "mult": 1.6, "knockback": 6.0, "poise": 20.0, "cooldown": 5.0, "kind": "melee", "arc": 60.0, "windup_extra": 0.25}],
			"xp_mult": 1.0, "drop_chance": 0.3, "sounds": {"hurt": &"hit_bone", "death": &"skeleton_death", "idle": &"skeleton_rattle"}}),
		_e(&"bonewarden", "Bonewarden", &"shield", {"hp": 75.0, "damage_min": 6.0, "damage_max": 10.0, "defense": 40.0,
			"evasion": 4.0, "accuracy": 30.0, "move_speed": 3.0, "weight": 1.6, "poise": 40.0, "knockback_res": 0.3, "affinity": Elements.DARK,
			"resistances": {Elements.DARK: 0.25}, "preferred_range": 1.8, "blocks_front": true, "guard_break": 55.0,
			"attacks": [{"id": &"bash", "anim": &"shield_bash", "range": 2.0, "mult": 1.1, "knockback": 7.0, "poise": 20.0, "cooldown": 2.2, "kind": "melee", "arc": 80.0},
				{"id": &"chop", "anim": &"axe_light_1", "range": 2.3, "mult": 1.3, "knockback": 3.0, "poise": 12.0, "cooldown": 2.0, "kind": "melee", "arc": 90.0}],
			"xp_mult": 1.6, "drop_chance": 0.4, "sounds": {"hurt": &"hit_armor", "death": &"skeleton_death", "idle": &"skeleton_rattle"}}),
		_e(&"grave_archer", "Grave Archer", &"ranged", {"hp": 34.0, "damage_min": 5.0, "damage_max": 8.0, "defense": 6.0,
			"evasion": 16.0, "accuracy": 36.0, "move_speed": 3.6, "weight": 0.9, "poise": 14.0, "affinity": Elements.DARK,
			"resistances": {Elements.DARK: 0.25}, "preferred_range": 11.0, "retreat_range": 6.0,
			"attacks": [{"id": &"arrow", "anim": &"bow_release", "range": 16.0, "mult": 1.0, "knockback": 2.0, "poise": 6.0, "cooldown": 2.2, "kind": "projectile",
				"speed": 22.0, "projectile": "arrow"}],
			"xp_mult": 1.2, "drop_chance": 0.35, "sounds": {"hurt": &"hit_bone", "death": &"skeleton_death"}}),
		_e(&"ashen_cultist", "Ashen Cultist", &"caster", {"hp": 38.0, "damage_min": 7.0, "damage_max": 11.0, "defense": 5.0,
			"evasion": 10.0, "accuracy": 30.0, "move_speed": 3.4, "weight": 0.9, "poise": 16.0, "affinity": Elements.FIRE,
			"resistances": {Elements.FIRE: 0.4, Elements.WATER: -0.25}, "preferred_range": 10.0, "retreat_range": 5.0,
			"attacks": [{"id": &"ember", "anim": &"cast_short", "range": 15.0, "mult": 1.0, "element": Elements.FIRE, "knockback": 2.0, "poise": 6.0,
					"cooldown": 2.6, "kind": "projectile", "speed": 14.0, "projectile": "fire", "status": {&"burning": 40.0}},
				{"id": &"hex_circle", "anim": &"cast_aoe", "range": 12.0, "mult": 1.8, "element": Elements.DARK, "knockback": 4.0, "poise": 15.0,
					"cooldown": 8.0, "kind": "aoe", "radius": 2.6, "windup": 1.1, "telegraph": "circle"}],
			"xp_mult": 1.4, "drop_chance": 0.4, "sounds": {"hurt": &"hit_flesh", "death": &"cultist_death", "idle": &"cultist_chant"}}),
		_e(&"ghoul_brute", "Ghoul Brute", &"brute", {"hp": 160.0, "damage_min": 12.0, "damage_max": 20.0, "defense": 25.0,
			"evasion": 2.0, "accuracy": 34.0, "move_speed": 2.9, "weight": 3.2, "poise": 90.0, "knockback_res": 0.35, "affinity": Elements.EARTH,
			"resistances": {Elements.EARTH: 0.3, Elements.FIRE: -0.2}, "preferred_range": 2.4, "body_radius": 0.9, "body_height": 2.5,
			"attacks": [{"id": &"swipe", "anim": &"axe_light_2", "range": 3.0, "mult": 1.0, "knockback": 8.0, "poise": 25.0, "cooldown": 2.4, "kind": "melee", "arc": 140.0},
				{"id": &"ground_pound", "anim": &"boss_slam", "range": 3.6, "mult": 2.0, "knockback": 12.0, "poise": 50.0, "cooldown": 7.0, "kind": "aoe",
					"radius": 3.6, "windup": 1.0, "telegraph": "circle", "self_centered": true}],
			"xp_mult": 3.0, "drop_chance": 0.6, "gold": Vector2i(8, 20), "sounds": {"hurt": &"hit_flesh", "death": &"ghoul_death", "idle": &"ghoul_growl"}}),
		_e(&"shade_stalker", "Shade Stalker", &"assassin", {"hp": 36.0, "damage_min": 7.0, "damage_max": 12.0, "defense": 6.0,
			"evasion": 40.0, "accuracy": 44.0, "crit_chance": 0.12, "move_speed": 6.2, "weight": 0.8, "poise": 14.0, "affinity": Elements.DARK,
			"resistances": {Elements.DARK: 0.5, Elements.LIGHT: -0.3}, "preferred_range": 1.5,
			"attacks": [{"id": &"lunge", "anim": &"dagger_heavy", "range": 6.0, "mult": 1.4, "knockback": 3.0, "poise": 10.0, "cooldown": 3.5, "kind": "dash", "dash": 6.0, "arc": 70.0},
				{"id": &"stab", "anim": &"dagger_light_1", "range": 1.8, "mult": 0.8, "knockback": 1.0, "poise": 6.0, "cooldown": 0.9, "kind": "melee", "arc": 70.0}],
			"xp_mult": 1.5, "drop_chance": 0.4, "sounds": {"hurt": &"hit_flesh", "death": &"cultist_death", "idle": &"shade_hiss"}}),
		_e(&"boss_warden", "Morthar, the Hollow Warden", &"boss", {"hp": 2400.0, "damage_min": 18.0, "damage_max": 28.0, "defense": 60.0,
			"evasion": 5.0, "accuracy": 60.0, "move_speed": 3.6, "weight": 12.0, "poise": 260.0, "knockback_res": 0.7, "status_res": 0.3,
			"affinity": Elements.DARK, "resistances": {Elements.DARK: 0.5, Elements.FIRE: 0.2, Elements.LIGHT: -0.25},
			"preferred_range": 3.2, "body_radius": 1.4, "body_height": 4.2, "aggro_range": 40.0, "leash_range": 200.0, "can_be_elite": false,
			"attacks": [
				{"id": &"sweep", "anim": &"boss_sweep", "range": 5.0, "mult": 1.0, "knockback": 12.0, "poise": 40.0, "cooldown": 3.0, "kind": "aoe",
					"radius": 5.0, "arc": 200.0, "windup": 0.9, "telegraph": "cone", "self_centered": true},
				{"id": &"slam", "anim": &"boss_slam", "range": 6.0, "mult": 1.7, "knockback": 16.0, "poise": 60.0, "cooldown": 6.0, "kind": "aoe",
					"radius": 4.0, "windup": 1.2, "telegraph": "circle", "offset": 3.0, "element": Elements.EARTH},
				{"id": &"charge", "anim": &"boss_charge", "range": 22.0, "mult": 1.5, "knockback": 18.0, "poise": 50.0, "cooldown": 10.0, "kind": "charge",
					"width": 3.0, "windup": 1.3, "telegraph": "line", "speed": 16.0},
				{"id": &"dark_orbs", "anim": &"cast_long", "range": 24.0, "mult": 0.8, "element": Elements.DARK, "knockback": 3.0, "poise": 10.0,
					"cooldown": 7.0, "kind": "projectile", "speed": 11.0, "projectile": "dark", "count": 7, "spread": 70.0, "phase": 2},
				{"id": &"corruption", "anim": &"boss_roar", "range": 30.0, "mult": 0.5, "element": Elements.DARK, "cooldown": 14.0, "kind": "pools",
					"radius": 2.8, "count": 5, "windup": 1.0, "telegraph": "circle", "duration": 8.0, "phase": 2},
				{"id": &"summon", "anim": &"boss_summon", "range": 40.0, "cooldown": 20.0, "kind": "summon", "summon": &"hollow_soldier", "count": 3, "phase": 2},
				{"id": &"nova", "anim": &"boss_slam", "range": 9.0, "mult": 2.2, "element": Elements.FIRE, "knockback": 20.0, "poise": 80.0, "cooldown": 9.0,
					"kind": "aoe", "radius": 9.0, "windup": 1.6, "telegraph": "ring", "self_centered": true, "inner_radius": 3.5, "phase": 3},
			],
			"xp_mult": 25.0, "drop_chance": 1.0, "gold": Vector2i(150, 260), "sounds": {"hurt": &"hit_armor", "death": &"boss_roar", "idle": &"boss_roar"}}),
	]

## Elite modifiers: id -> {name, color, desc, mods (StatModifiers), flags}
static func elite_mods() -> Dictionary:
	return {
		&"flaming": {"name": "Flaming", "color": Color(1.0, 0.45, 0.1), "desc": "Attacks add Fire damage and ignite; leaves burning ground on death.",
			"element": Elements.FIRE, "flags": {&"burn_on_hit": 1.0, &"death_fire": 1.0}, "res": {Elements.FIRE: 0.5}},
		&"frozen": {"name": "Frozen", "color": Color(0.55, 0.9, 1.0), "desc": "Attacks Chill; periodically releases a frost pulse.",
			"element": Elements.ICE, "flags": {&"frost_pulse": 1.0}, "res": {Elements.ICE: 0.5}},
		&"lightning": {"name": "Stormcharged", "color": Color(0.95, 0.9, 0.35), "desc": "Being hit releases sparks that seek you.",
			"element": Elements.LIGHTNING, "flags": {&"sparks": 1.0}, "res": {Elements.LIGHTNING: 0.5}},
		&"armored": {"name": "Armored", "color": Color(0.7, 0.72, 0.78), "desc": "Greatly increased Defense and knockback resistance.",
			"mods": [StatModifier.inc(&"defense", 1.0), StatModifier.flat(&"knockback_res", 0.3)]},
		&"regenerating": {"name": "Regenerating", "color": Color(0.4, 0.95, 0.45), "desc": "Regenerates 3% of HP per second unless Purged or recently burned.",
			"flags": {&"regen": 0.03}},
		&"vampiric": {"name": "Vampiric", "color": Color(0.85, 0.1, 0.2), "desc": "Heals for 40% of damage dealt.", "flags": {&"leech": 0.4}},
		&"fast": {"name": "Swift", "color": Color(0.8, 1.0, 0.8), "desc": "Moves and attacks much faster.",
			"mods": [StatModifier.more(&"move_speed", 0.35), StatModifier.more(&"attack_speed", 0.3)]},
		&"explosive": {"name": "Volatile", "color": Color(1.0, 0.6, 0.2), "desc": "Explodes shortly after death.", "flags": {&"explode": 1.0}},
		&"shielded": {"name": "Warded", "color": Color(0.55, 0.65, 1.0), "desc": "A ward absorbs damage equal to 50% of its HP; Light damage breaks it twice as fast.",
			"flags": {&"ward": 0.5}},
	}
