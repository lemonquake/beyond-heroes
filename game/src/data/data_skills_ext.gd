class_name DataSkillsExt
## bh-010 skill expansion. New active skills, the Knight's auras, every class's passive skills, and the skill trees of
## the two new classes (Ranger, Shadowblade). Knight and Mage trees gain pages built from the nodes below
## (DataSkills.knight_tree / mage_tree).
##
## Passive node mods: [stat, op, base, per_rank] (value at rank r = base + per_rank * (r - 1)); flags: {flag: [base, per_rank]}.
## Synergies (skill nodes): [[node, pct per rank]] -> +pct% damage per learned rank of that node.

const ICON := "res://assets/ui/icons/skills/%s.svg"
const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC
const M := StatModifier.Op.MORE

static func _s(id: StringName, name: String, cls: StringName, behavior: StringName, d: Dictionary) -> SkillDef:
	return DataSkills._s(id, name, cls, behavior, d)

static func skills() -> Array:
	return knight() + mage() + ranger() + shadowblade() + DataClassRework.skills()

# ================================================================================================= KNIGHT
static func knight() -> Array:
	var ATK := DamageRequest.Kind.ATTACK
	var SPL := DamageRequest.Kind.SPELL
	return [
		_s(&"zeal", "Zeal", &"knight", &"flurry", {"kind": ATK, "anim": &"special_attack", "anim_speed_stat": &"attack_speed",
			"mana_cost": 5.0, "mana_per_rank": 0.5, "cooldown": 0.0, "requires": &"melee",
			"description": "A burst of {strikes} rapid strikes, each dealing {weapon_pct}% weapon damage to enemies in front of you.",
			"params": {"weapon_pct": 52.0, "strikes": 4.0, "range": 2.7, "arc": 100.0, "knockback": 2.0, "poise": 8.0, "valor_gain": 2.0},
			"per_rank": {"weapon_pct": 6.0}, "sound_cast": &"swing_light", "sound_hit": &"hit_flesh", "vfx": &"zeal"}),
		_s(&"blessed_hammer", "Hallowed Hammer", &"knight", &"spiral", {"kind": SPL, "element": Elements.LIGHT, "anim": &"cast_weapon",
			"mana_cost": 7.0, "mana_per_rank": 0.6, "cooldown": 0.0,
			"description": "Hurl a hammer of light that spirals outward for {duration} s, striking every enemy it passes for {damage_min}-{damage_max} Light damage.",
			"params": {"damage_min": 9.0, "damage_max": 13.0, "duration": 2.2, "growth": 1.9, "count": 1.0, "knockback": 3.0, "poise": 10.0},
			"per_rank": {"damage_min": 3.0, "damage_max": 4.2}, "sound_cast": &"holy_chime", "sound_hit": &"holy_strike", "vfx": &"hammer"}),
		_s(&"heavens_fist", "Heaven's Fist", &"knight", &"ground_aoe", {"kind": SPL, "conversion": {Elements.LIGHTNING: 0.5, Elements.LIGHT: 0.5},
			"anim": &"cast_heavy", "mana_cost": 14.0, "mana_per_rank": 1.0, "cooldown": 5.0,
			"description": "Call down a bolt of holy lightning on the target: {damage_min}-{damage_max} Lightning and Light damage in {radius} m, and {radial_bolts} holy bolts burst outward ({bolt_pct}% damage each).",
			"params": {"damage_min": 18.0, "damage_max": 26.0, "radius": 2.6, "delay": 0.35, "range": 16.0, "knockback": 6.0, "poise": 30.0,
				"sky_bolt": 1.0, "radial_bolts": 6.0, "bolt_pct": 40.0, "bolt_range": 9.0, "status_power": 1.2},
			"per_rank": {"damage_min": 5.0, "damage_max": 7.0}, "sound_cast": &"cast_lightning", "sound_hit": &"thunder_strike", "vfx": &"heavens_fist"}),
		# ---- Auras (toggle; reserve Mana; one at a time; pulse every second to allies in radius)
		_aura(&"aura_might", "Aura of Might", &"offense", Elements.PHYSICAL, "Allies within {radius} m deal {dmg}% more damage.",
			{"dmg": 10.0}, {"dmg": 3.0}, [[&"outgoing_damage", M, "dmg", 0.01]], 0.18),
		_aura(&"aura_cinders", "Aura of Cinders", &"offense", Elements.FIRE, "Allies within {radius} m deal {fire}% increased Fire damage. Every second, enemies within {pulse_radius} m take {pulse_min}-{pulse_max} Fire damage.",
			{"fire": 15.0, "pulse_min": 4.0, "pulse_max": 7.0, "pulse_radius": 6.0}, {"fire": 5.0, "pulse_min": 2.0, "pulse_max": 3.0}, [[&"dmg_fire", I, "fire", 0.01]], 0.16),
		_aura(&"aura_winter", "Aura of Winter", &"offense", Elements.ICE, "Allies within {radius} m gain {ice_res}% Ice Resistance. Every second, enemies within {pulse_radius} m take {pulse_min}-{pulse_max} Ice damage and build Chill ({pulse_chill}).",
			{"ice_res": 15.0, "pulse_min": 2.0, "pulse_max": 4.0, "pulse_radius": 6.0, "pulse_chill": 30.0}, {"ice_res": 3.0, "pulse_min": 1.0, "pulse_max": 2.0, "pulse_chill": 8.0},
			[[&"res_ice", F, "ice_res", 0.01]], 0.16),
		_aura(&"aura_fervor", "Aura of Fervor", &"offense", Elements.PHYSICAL, "Allies within {radius} m attack and cast {speed}% faster.",
			{"speed": 8.0}, {"speed": 3.0}, [[&"attack_speed", M, "speed", 0.01], [&"cast_speed", M, "speed", 0.01]], 0.18),
		_aura(&"aura_mending", "Aura of Mending", &"defense", Elements.LIGHT, "Allies within {radius} m restore {heal_pct}% of their Maximum HP every second.",
			{"heal_pct": 0.8, "magnitude": 0.008}, {"heal_pct": 0.3, "magnitude": 0.003}, [], 0.2),
		_aura(&"aura_defiance", "Aura of Defiance", &"defense", Elements.PHYSICAL, "Allies within {radius} m gain {def}% increased Defense.",
			{"def": 25.0}, {"def": 8.0}, [[&"defense", I, "def", 0.01]], 0.14),
		_aura(&"aura_thorns", "Aura of Thorns", &"defense", Elements.PHYSICAL, "Melee attackers of allies within {radius} m take {reflect}% of the damage they deal.",
			{"reflect": 30.0, "magnitude": 0.30}, {"reflect": 12.0, "magnitude": 0.12}, [], 0.14),
		_aura(&"aura_clarity", "Aura of Clarity", &"defense", Elements.WATER, "Allies within {radius} m regenerate Mana {mana}% faster.",
			{"mana": 25.0}, {"mana": 10.0}, [[&"mana_regen", I, "mana", 0.01]], 0.10),
	]

static func _aura(id: StringName, name: String, akind: StringName, el: int, desc: String, params: Dictionary, per: Dictionary, mods: Array, reserve: float) -> SkillDef:
	var p := params.duplicate()
	p["radius"] = 10.0
	p["reserve"] = reserve
	var pr := per.duplicate()
	pr["radius"] = 0.5
	var s := _s(id, name, &"knight", &"aura", {"kind": DamageRequest.Kind.SPELL, "element": el, "anim": &"cast_area",
		"mana_cost": 10.0, "mana_per_rank": 0.0, "cooldown": 0.0, "aura_kind": akind, "aura_mods": mods,
		"description": "Aura (toggle). " + desc + " Reserves {reserve_pct}% of Maximum Mana while active. Only one aura at a time.",
		"params": p, "per_rank": pr, "sound_cast": &"holy_chime", "vfx": &"aura"})
	s.params["reserve_pct"] = roundf(reserve * 100.0)
	return s

# ================================================================================================= MAGE
static func mage() -> Array:
	var SPL := DamageRequest.Kind.SPELL
	return [
		_s(&"blizzard", "Blizzard", &"mage", &"storm", {"kind": SPL, "element": Elements.ICE, "anim": &"cast_area", "mana_cost": 18.0,
			"mana_per_rank": 1.2, "cooldown": 4.0,
			"description": "Summon a storm of ice over the target for {duration} s: every {tick} s, {damage_min}-{damage_max} Ice damage to enemies within {radius} m and heavy Chill.",
			"params": {"damage_min": 6.0, "damage_max": 9.0, "radius": 4.0, "duration": 3.5, "tick": 0.5, "range": 18.0, "chill": 22.0, "knockback": 0.0, "poise": 3.0},
			"per_rank": {"damage_min": 1.8, "damage_max": 2.6}, "sound_cast": &"blizzard_cast", "sound_hit": &"freeze", "vfx": &"blizzard"}),
		_s(&"flame_sentinel", "Flame Sentinel", &"mage", &"sentry", {"kind": SPL, "element": Elements.FIRE, "anim": &"cast_heavy", "mana_cost": 16.0,
			"mana_per_rank": 1.0, "cooldown": 6.0,
			"description": "Raise a pillar of living flame for {duration} s that hurls a fire bolt at the nearest enemy every {interval} s ({damage_min}-{damage_max} Fire damage). Up to {max_count} at once.",
			"params": {"damage_min": 7.0, "damage_max": 11.0, "duration": 8.0, "interval": 0.8, "reach": 14.0, "range": 12.0, "max_count": 2.0, "ignite": 30.0,
				"knockback": 1.5, "poise": 5.0},
			"per_rank": {"damage_min": 2.0, "damage_max": 3.0}, "sound_cast": &"cast_fire", "sound_hit": &"fire_explode", "vfx": &"sentinel"}),
		_s(&"frost_orb", "Frost Orb", &"mage", &"orb", {"kind": SPL, "element": Elements.ICE, "anim": &"cast_quick", "mana_cost": 15.0,
			"mana_per_rank": 1.0, "cooldown": 2.5,
			"description": "Launch a slow orb of frost that sheds whirling ice shards as it flies and bursts into a ring of shards: {damage_min}-{damage_max} Ice damage per shard and Chill.",
			"params": {"damage_min": 4.0, "damage_max": 6.0, "range": 14.0, "chill": 18.0, "knockback": 1.0, "poise": 3.0},
			"per_rank": {"damage_min": 1.2, "damage_max": 1.8}, "sound_cast": &"cast_ice", "sound_hit": &"shatter_ice", "vfx": &"frost_orb"}),
	]

# ================================================================================================= RANGER
static func ranger() -> Array:
	var ATK := DamageRequest.Kind.ATTACK
	var SPL := DamageRequest.Kind.SPELL
	return [
		_s(&"power_shot", "Power Shot", &"ranger", &"projectile", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 3.0, "mana_per_rank": 0.4, "cooldown": 0.0, "requires": &"bow", "projectile_look": "arrow",
			"description": "A heavy, drawn arrow for {weapon_pct}% weapon damage that pierces {pierce} enemy and hurls targets back.",
			"params": {"weapon_pct": 165.0, "speed": 40.0, "count": 1.0, "spread": 0.0, "pierce": 1.0, "range": 24.0, "knockback": 8.0, "poise": 18.0},
			"per_rank": {"weapon_pct": 18.0}, "sound_cast": &"bow_release", "sound_hit": &"arrow_impact", "vfx": &"power_shot"}),
		_s(&"multishot", "Multishot", &"ranger", &"projectile", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 6.0, "mana_per_rank": 0.6, "cooldown": 0.0, "requires": &"bow", "projectile_look": "arrow",
			"description": "Loose a fan of {count} arrows, each dealing {weapon_pct}% weapon damage.",
			"params": {"weapon_pct": 58.0, "speed": 34.0, "count": 5.0, "spread": 26.0, "pierce": 0.0, "range": 20.0, "knockback": 2.5, "poise": 6.0},
			"per_rank": {"weapon_pct": 5.0, "count": 0.5}, "sound_cast": &"bow_release", "sound_hit": &"arrow_impact", "vfx": &"multishot"}),
		_s(&"frost_arrow", "Frost Arrow", &"ranger", &"projectile", {"kind": ATK, "anim": &"bow_1", "anim_speed_stat": &"attack_speed",
			"mana_cost": 5.0, "mana_per_rank": 0.5, "cooldown": 0.0, "requires": &"bow", "projectile_look": "arrow", "conversion": {Elements.ICE: 0.6},
			"description": "An arrow of rime: {weapon_pct}% weapon damage, 60% of it as Ice, with heavy Chill.",
			"params": {"weapon_pct": 125.0, "speed": 36.0, "count": 1.0, "spread": 0.0, "pierce": 0.0, "range": 22.0, "chill": 55.0, "knockback": 3.0, "poise": 8.0},
			"per_rank": {"weapon_pct": 14.0, "chill": 6.0}, "sound_cast": &"bow_release", "sound_hit": &"freeze", "vfx": &"frost_arrow"}),
		_s(&"blast_arrow", "Blast Arrow", &"ranger", &"projectile", {"kind": ATK, "anim": &"bow_1", "anim_speed_stat": &"attack_speed",
			"mana_cost": 7.0, "mana_per_rank": 0.6, "cooldown": 1.5, "requires": &"bow", "projectile_look": "arrow", "conversion": {Elements.FIRE: 0.5},
			"description": "An arrow packed with black powder: {weapon_pct}% weapon damage, half as Fire, exploding in {explode_radius} m. Ignites.",
			"params": {"weapon_pct": 130.0, "speed": 32.0, "count": 1.0, "spread": 0.0, "pierce": 0.0, "range": 20.0, "explode_radius": 2.6, "ignite": 60.0,
				"knockback": 7.0, "poise": 16.0},
			"per_rank": {"weapon_pct": 15.0, "explode_radius": 0.1}, "sound_cast": &"bow_release", "sound_hit": &"fire_explode", "vfx": &"blast_arrow"}),
		_s(&"arrow_rain", "Arrow Rain", &"ranger", &"storm", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 14.0, "mana_per_rank": 1.0, "cooldown": 6.0, "requires": &"bow", "projectile_look": "arrow",
			"description": "Arrows fall on the target area for {duration} s: every {tick} s, {weapon_pct}% weapon damage to enemies within {radius} m.",
			"params": {"weapon_pct": 34.0, "radius": 4.2, "duration": 2.5, "tick": 0.35, "range": 20.0, "knockback": 0.5, "poise": 3.0},
			"per_rank": {"weapon_pct": 4.0}, "sound_cast": &"bow_release", "sound_hit": &"arrow_impact", "vfx": &"arrow_rain"}),
		_s(&"deadeye", "Deadeye", &"ranger", &"projectile", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 8.0, "mana_per_rank": 0.5, "cooldown": 4.0, "requires": &"bow", "projectile_look": "arrow",
			"description": "Spend all Focus on one perfect shot: {weapon_pct}% weapon damage +{per_focus}% per Focus spent, piercing every enemy in its path. At {crit_focus}+ Focus it always crits.",
			"params": {"weapon_pct": 150.0, "per_focus": 2.2, "crit_focus": 80.0, "consume_focus": 1.0, "speed": 60.0, "count": 1.0, "spread": 0.0,
				"pierce": 99.0, "range": 30.0, "knockback": 10.0, "poise": 30.0},
			"per_rank": {"weapon_pct": 20.0}, "sound_cast": &"bow_release", "sound_hit": &"crit_hit", "vfx": &"deadeye"}),
		_s(&"storm_javelin", "Storm Javelin", &"ranger", &"chain", {"kind": ATK, "anim": &"cast_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 9.0, "mana_per_rank": 0.8, "cooldown": 2.0, "conversion": {Elements.LIGHTNING: 0.7},
			"description": "Hurl a conjured javelin of lightning: {weapon_pct}% weapon damage (70% Lightning) that arcs to {chains} more enemies, losing 10% per jump.",
			"params": {"weapon_pct": 115.0, "chains": 3.0, "chain_range": 7.0, "range": 18.0, "knockback": 2.0, "poise": 8.0},
			"per_rank": {"weapon_pct": 13.0, "chains": 0.5}, "sound_cast": &"cast_lightning", "sound_hit": &"lightning_zap", "vfx": &"lightning"}),
		_s(&"snare_trap", "Snare Trap", &"ranger", &"trap", {"kind": ATK, "anim": &"cast_quick", "mana_cost": 6.0, "mana_per_rank": 0.4, "cooldown": 1.0,
			"description": "Set a trap (up to {max_traps}) that springs when an enemy steps near: {weapon_pct}% weapon damage in {radius} m and Webbed for {web_dur} s.",
			"on_hit_status": {&"webbed": ["web_dur", 0.0]},
			"params": {"weapon_pct": 90.0, "radius": 2.6, "range": 12.0, "max_traps": 3.0, "web_dur": 2.0, "knockback": 0.0, "poise": 20.0},
			"per_rank": {"weapon_pct": 10.0, "web_dur": 0.25}, "sound_cast": &"armor_rustle", "sound_hit": &"block", "vfx": &"trap"}),
		_s(&"blast_trap", "Blast Trap", &"ranger", &"trap", {"kind": ATK, "anim": &"cast_quick", "mana_cost": 9.0, "mana_per_rank": 0.6, "cooldown": 1.5,
			"conversion": {Elements.FIRE: 0.6},
			"description": "Set a powder trap (shared limit with Snare Trap) that explodes when an enemy comes near: {weapon_pct}% weapon damage in {radius} m, 60% as Fire. Ignites.",
			"params": {"weapon_pct": 180.0, "radius": 3.2, "range": 12.0, "max_traps": 3.0, "ignite": 70.0, "knockback": 10.0, "poise": 30.0, "launch": 3.0},
			"per_rank": {"weapon_pct": 22.0}, "sound_cast": &"armor_rustle", "sound_hit": &"fire_explode", "vfx": &"trap"}),
		_s(&"vault", "Vault", &"ranger", &"vault", {"kind": ATK, "anim": &"dodge_step", "mana_cost": 6.0, "mana_per_rank": 0.0, "cooldown": 5.0,
			"description": "Vault {range} m away from where you aim (untouchable in the air), scattering caltrops that deal {weapon_pct}% weapon damage per half-second and slow for {duration} s.",
			"params": {"weapon_pct": 18.0, "range": 7.0, "radius": 2.4, "duration": 4.0, "knockback": 0.0, "poise": 2.0},
			"per_rank": {"range": 0.4, "weapon_pct": 3.0}, "sound_cast": &"dodge_roll", "vfx": &"vault"}),
		_s(&"hunters_mark", "Hunter's Mark", &"ranger", &"mark", {"kind": SPL, "anim": &"cast_quick", "mana_cost": 8.0, "mana_per_rank": 0.0, "cooldown": 8.0,
			"element": Elements.LIGHT, "on_hit_status": {&"marked": ["mark_dur", "mark_pct"]},
			"description": "Mark every enemy within {radius} m of the target for {mark_dur} s: they take {mark_pct}% more damage and cannot hide.",
			"params": {"radius": 4.5, "range": 18.0, "mark_dur": 8.0, "mark_pct": 12.0},
			"per_rank": {"mark_pct": 3.0, "radius": 0.3}, "sound_cast": &"dark_cast", "vfx": &"mark"}),
	]

# ================================================================================================= SHADOWBLADE
static func shadowblade() -> Array:
	var ATK := DamageRequest.Kind.ATTACK
	var SPL := DamageRequest.Kind.SPELL
	return [
		_s(&"twin_fang", "Twin Fang", &"shadowblade", &"flurry", {"kind": ATK, "anim": &"dual_4", "anim_speed_stat": &"attack_speed",
			"mana_cost": 3.0, "mana_per_rank": 0.3, "cooldown": 0.0, "requires": &"melee",
			"description": "Builder. Two quick cuts, each {weapon_pct}% weapon damage. +{combo_gain} Combo (a critical hit adds one more).",
			"params": {"weapon_pct": 72.0, "strikes": 2.0, "range": 2.2, "arc": 90.0, "combo_gain": 1.0, "knockback": 1.0, "poise": 5.0},
			"per_rank": {"weapon_pct": 8.0}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"twin_fang"}),
		_s(&"venom_strike", "Venom Strike", &"shadowblade", &"melee_arc", {"kind": ATK, "anim": &"dagger_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 5.0, "mana_per_rank": 0.4, "cooldown": 0.0, "requires": &"melee",
			"description": "Builder. A poisoned thrust: {weapon_pct}% weapon damage and heavy Poison ({poison_buildup}). +{combo_gain} Combo.",
			"params": {"weapon_pct": 110.0, "arc": 70.0, "range": 2.4, "combo_gain": 1.0, "poison_buildup": 90.0, "knockback": 2.0, "poise": 8.0},
			"per_rank": {"weapon_pct": 12.0, "poison_buildup": 8.0}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"venom"}),
		_s(&"shadow_step", "Shadow Step", &"shadowblade", &"shadow_step", {"kind": ATK, "anim": &"dagger_2", "anim_speed_stat": &"attack_speed",
			"mana_cost": 7.0, "mana_per_rank": 0.0, "cooldown": 4.0, "requires": &"melee",
			"description": "Step through the shadows to appear behind the enemy nearest your aim (up to {range} m) and strike for {weapon_pct}% weapon damage. +{combo_gain} Combo.",
			"params": {"weapon_pct": 130.0, "range": 10.0, "arc": 80.0, "combo_gain": 1.0, "knockback": 3.0, "poise": 10.0},
			"per_rank": {"weapon_pct": 14.0, "range": 0.5}, "sound_cast": &"blink", "sound_hit": &"hit_flesh", "vfx": &"shadow_step"}),
		_s(&"fan_of_knives", "Fan of Knives", &"shadowblade", &"projectile", {"kind": ATK, "anim": &"cast_weapon", "anim_speed_stat": &"attack_speed",
			"mana_cost": 8.0, "mana_per_rank": 0.6, "cooldown": 0.0, "projectile_look": "arrow",
			"description": "Builder. Throw {count} knives in every direction, each {weapon_pct}% weapon damage with Bleeding. +{combo_gain} Combo.",
			"params": {"weapon_pct": 45.0, "count": 12.0, "radial": 1.0, "speed": 26.0, "range": 9.0, "pierce": 0.0, "bleed": 25.0, "combo_gain": 1.0,
				"knockback": 1.0, "poise": 3.0},
			"per_rank": {"weapon_pct": 5.0}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"knives"}),
		_s(&"crippling_star", "Crippling Star", &"shadowblade", &"projectile", {"kind": ATK, "anim": &"cast_quick", "anim_speed_stat": &"attack_speed",
			"mana_cost": 5.0, "mana_per_rank": 0.4, "cooldown": 1.5, "projectile_look": "arrow", "on_hit_status": {&"slowed": [3.0, 0.0], &"dazzled": [3.0, 0.0]},
			"description": "Builder. Hurl {count} throwing stars: {weapon_pct}% weapon damage each, Bleeding, Slowed and Dazzled. +{combo_gain} Combo.",
			"params": {"weapon_pct": 70.0, "count": 3.0, "spread": 12.0, "speed": 30.0, "range": 16.0, "pierce": 0.0, "bleed": 40.0, "combo_gain": 1.0,
				"knockback": 1.5, "poise": 4.0},
			"per_rank": {"weapon_pct": 8.0}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"shuriken"}),
		_s(&"eviscerate", "Eviscerate", &"shadowblade", &"melee_arc", {"kind": ATK, "anim": &"dual_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 6.0, "mana_per_rank": 0.4, "cooldown": 0.0, "requires": &"melee", "on_hit_status": {&"grievous": [6.0, 0.0]},
			"description": "Finisher. Spend all Combo on one brutal strike against a single enemy: {weapon_pct}% weapon damage +{per_pip}% per pip. The wound is Grievous (healing received -25%). Poised (full Combo): always a critical hit.",
			"params": {"weapon_pct": 110.0, "per_pip": 65.0, "consume_combo": 1.0, "max_targets": 1.0, "arc": 80.0, "range": 2.4, "knockback": 8.0, "poise": 30.0},
			"per_rank": {"weapon_pct": 12.0, "per_pip": 5.0}, "sound_cast": &"swing_heavy", "sound_hit": &"crit_hit", "vfx": &"eviscerate"}),
		_s(&"death_blossom", "Death Blossom", &"shadowblade", &"flurry", {"kind": ATK, "anim": &"whirlwind", "anim_speed_stat": &"attack_speed",
			"mana_cost": 10.0, "mana_per_rank": 0.6, "cooldown": 3.0, "requires": &"melee",
			"description": "Finisher. Spend all Combo and whirl through everything within {range} m: {strikes} cuts of {weapon_pct}% weapon damage +{per_pip}% per pip, with Bleeding.",
			"params": {"weapon_pct": 45.0, "per_pip": 18.0, "consume_combo": 1.0, "strikes": 3.0, "arc": 360.0, "range": 3.6, "bleed": 30.0, "knockback": 3.0, "poise": 8.0},
			"per_rank": {"weapon_pct": 5.0}, "sound_cast": &"whirlwind_loop", "sound_hit": &"hit_flesh", "vfx": &"blossom"}),
		_s(&"smoke_veil", "Smoke Veil", &"shadowblade", &"veil", {"kind": SPL, "anim": &"cast_quick", "mana_cost": 10.0, "mana_per_rank": 0.0, "cooldown": 14.0,
			"description": "Burst into smoke: enemies within {radius} m lose you and you gain Stealth for {duration} s. Your next hit from Stealth deals 50% more damage and always crits.",
			"params": {"radius": 6.0, "duration": 3.0},
			"per_rank": {"duration": 0.4}, "sound_cast": &"shade_hiss", "vfx": &"smoke"}),
		_s(&"blade_sentinel", "Blade Sentinel", &"shadowblade", &"sentry", {"kind": ATK, "anim": &"cast_weapon", "mana_cost": 12.0, "mana_per_rank": 0.8, "cooldown": 6.0,
			"description": "Set a whirling blade trap (up to {max_count}) for {duration} s: every {interval} s it cuts enemies within {reach} m for {weapon_pct}% weapon damage with Bleeding.",
			"params": {"weapon_pct": 30.0, "duration": 7.0, "interval": 0.5, "reach": 2.6, "range": 10.0, "max_count": 2.0, "bleed": 20.0, "knockback": 1.0, "poise": 3.0},
			"per_rank": {"weapon_pct": 4.0}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"sentinel"}),
		_s(&"dread_mark", "Dread Mark", &"shadowblade", &"mark", {"kind": SPL, "anim": &"cast_area", "mana_cost": 12.0, "mana_per_rank": 0.0, "cooldown": 16.0,
			"element": Elements.DARK, "on_hit_status": {&"feared": ["fear_dur", 0.0], &"marked": ["fear_dur", "mark_pct"]},
			"description": "Brand every enemy within {radius} m with dread: they flee in terror for {fear_dur} s and take {mark_pct}% more damage.",
			"params": {"self": 1.0, "radius": 5.0, "fear_dur": 2.5, "mark_pct": 10.0},
			"per_rank": {"fear_dur": 0.25, "mark_pct": 2.0}, "sound_cast": &"dark_curse", "vfx": &"dread"}),
		_s(&"quickstep", "Quickstep", &"shadowblade", &"buff", {"kind": SPL, "anim": &"cast_quick", "mana_cost": 8.0, "mana_per_rank": 0.0, "cooldown": 12.0,
			"description": "Move {speed}% faster and attack {atk}% faster for {duration} s. Your dodge is ready at once.",
			"params": {"status": "quickstep", "duration": 5.0, "speed": 30.0, "atk": 15.0, "reset_dodge": 1.0,
				"mods": [[&"move_speed", M, 0.30], [&"attack_speed", M, 0.15]]},
			"per_rank": {"duration": 0.5}, "sound_cast": &"wind_gust", "vfx": &"haste"}),
	]

# ================================================================================================= PASSIVE NODES
static func _pas(id: StringName, name: String, pos: Vector2, page: int, req: Array, lvl: int, desc: String, mods: Array, flags := {}) -> Dictionary:
	return {"id": id, "name": name, "kind": "passive", "icon": ICON % id, "pos": pos, "page": page, "max_rank": 5, "cost": 1,
		"requires": req, "req_level": lvl, "mods": mods, "flags": flags, "desc": desc}

static var _names := {}

static func _name_of(id: StringName) -> String:
	if _names.is_empty():
		for s in DataSkills.skills():
			_names[s.id] = s.display_name
	return _names.get(id, String(id).capitalize())

static func _sk(id: StringName, pos: Vector2, page: int, req: Array, lvl: int, syn := []) -> Dictionary:
	return {"id": id, "name": _name_of(id), "kind": "skill", "skill": id, "icon": ICON % id, "pos": pos,
		"page": page, "max_rank": 5, "cost": 1, "requires": req, "req_level": lvl, "synergies": syn}

static func _up(id: StringName, name: String, skill: StringName, pos: Vector2, page: int, req: Array, lvl: int, cost: int, max_rank: int, params: Dictionary, desc: String) -> Dictionary:
	return {"id": id, "name": name, "kind": "upgrade", "skill": skill, "icon": ICON % skill, "pos": pos, "page": page, "max_rank": max_rank,
		"cost": cost, "requires": req, "req_level": lvl, "params": params, "desc": desc}

## Extra Knight nodes: new Combat skills (page 0), Auras (page 1), Disciplines (page 2).
static func knight_nodes() -> Array:
	return [
		_sk(&"zeal", Vector2(2, 3), 0, [&"whirlwind"], 8, [[&"aura_fervor", 6.0], [&"arms_mastery", 4.0]]),
		_up(&"zeal_fervent", "Fervent Zeal", &"zeal", Vector2(0, 5), 0, [&"zeal"], 16, 2, 1, {"strikes": 1.0}, "Zeal strikes one more time."),
		_sk(&"blessed_hammer", Vector2(3, 3), 0, [&"iron_bulwark"], 10, [[&"aura_clarity", 8.0], [&"shield_mastery", 5.0]]),
		_up(&"hammer_twin", "Twin Hammers", &"blessed_hammer", Vector2(3, 5), 0, [&"blessed_hammer"], 18, 2, 1, {"count": 1.0}, "Hallowed Hammer throws a second hammer."),
		_sk(&"heavens_fist", Vector2(7, 4), 0, [&"ground_fissure"], 14, [[&"aura_might", 5.0], [&"judgment", 8.0]]),
		_up(&"fist_wrath", "Wrath of Heaven", &"heavens_fist", Vector2(6, 5), 0, [&"heavens_fist"], 20, 2, 1, {"radial_bolts": 4.0, "radius": 0.8}, "Four more holy bolts and a wider strike."),
		# Auras
		_sk(&"aura_might", Vector2(1, 0), 1, [], 2),
		_sk(&"aura_cinders", Vector2(0, 2), 1, [&"aura_might"], 6),
		_sk(&"aura_winter", Vector2(2, 2), 1, [&"aura_might"], 8),
		_sk(&"aura_fervor", Vector2(1, 4), 1, [&"aura_cinders", &"aura_winter"], 12),
		_sk(&"aura_mending", Vector2(5, 0), 1, [], 2),
		_sk(&"aura_defiance", Vector2(4, 2), 1, [&"aura_mending"], 6),
		_sk(&"aura_thorns", Vector2(6, 2), 1, [&"aura_mending"], 8),
		_sk(&"aura_clarity", Vector2(5, 4), 1, [&"aura_defiance", &"aura_thorns"], 12),
		# Disciplines (passives)
		_pas(&"arms_mastery", "Arms Mastery", Vector2(1, 0), 2, [], 1, "+{0}% increased weapon damage and +{1}% Critical Chance.",
			[[&"weapon_damage", I, 0.06, 0.03], [&"crit_chance", F, 0.01, 0.005]]),
		_pas(&"retaliation", "Counter-attack", Vector2(1, 2), 2, [&"arms_mastery"], 6, "Blocking has a {f0}% chance to counterattack for 120% weapon damage. 2 s cooldown. Cannot counter another passive hit.",
			[], {&"retaliation": [0.2, 0.06]}),
		_pas(&"crusader_resolve", "Crusader's Resolve", Vector2(1, 4), 2, [&"retaliation"], 12, "+{0}% Valor generation and +{1}% Physical Damage.",
			[[&"valor_gain", I, 0.15, 0.05], [&"phys_damage", F, 0.03, 0.02]]),
		_pas(&"shield_mastery", "Shield Mastery", Vector2(4, 0), 2, [], 1, "+{0}% Block Chance and +{1}% Block Strength.",
			[[&"block_chance", F, 0.03, 0.01], [&"block_strength", F, 0.04, 0.02]]),
		_pas(&"oathbound", "Oathbound Resilience", Vector2(4, 2), 2, [&"shield_mastery"], 6, "+{0}% to all elemental Resistances.",
			[[&"res_all", F, 0.05, 0.02]]),
		_pas(&"second_wind", "Second Wind", Vector2(4, 4), 2, [&"oathbound"], 14, "Dropping below 35% HP restores {f0}% of Maximum HP over 4 s (once every 45 s).",
			[], {&"second_wind": [0.2, 0.05]}),
		_pas(&"toughness", "Toughness", Vector2(7, 0), 2, [], 1, "+{0}% Maximum HP and +{1} Poise.",
			[[&"max_hp", I, 0.06, 0.03], [&"poise", F, 4.0, 2.0]]),
		_pas(&"iron_skin", "Iron Skin", Vector2(7, 2), 2, [&"toughness"], 4, "+{0}% increased Defense.",
			[[&"defense", I, 0.12, 0.06]]),
	] + DataClassRework.nodes(&"knight")

## Extra Mage nodes: new spells (page 0) and Mastery (page 1).
static func mage_nodes() -> Array:
	return [
		_sk(&"blizzard", Vector2(5, 3), 0, [&"tidal_wave", &"frost_nova"], 11, [[&"frost_nova", 6.0], [&"frost_orb", 6.0]]),
		_up(&"blizzard_deep", "Endless Winter", &"blizzard", Vector2(5, 5), 0, [&"blizzard"], 18, 2, 1, {"duration": 1.5, "radius": 0.8}, "Blizzard lasts 1.5 s longer and covers more ground."),
		_sk(&"flame_sentinel", Vector2(1, 3), 0, [&"chain_lightning", &"firebolt_explode"], 9, [[&"firebolt", 6.0]]),
		_sk(&"frost_orb", Vector2(3, 5), 0, [&"stone_spear", &"tidal_wave"], 14, [[&"blizzard", 6.0], [&"frost_nova", 4.0]]),
		# Mastery (passives)
		_pas(&"pyre_mastery", "Pyre Mastery", Vector2(1, 0), 1, [], 2, "+{0}% increased Fire damage and +{1}% Fire Penetration.",
			[[&"dmg_fire", I, 0.10, 0.04], [&"pen_fire", F, 0.03, 0.01]]),
		_pas(&"storm_mastery", "Storm Mastery", Vector2(1, 2), 1, [&"pyre_mastery"], 6, "+{0}% increased Lightning damage and +{1}% Lightning Penetration.",
			[[&"dmg_lightning", I, 0.10, 0.04], [&"pen_lightning", F, 0.03, 0.01]]),
		_pas(&"frost_mastery", "Frost Mastery", Vector2(4, 0), 1, [], 2, "+{0}% increased Ice damage and +{1}% Ice Penetration.",
			[[&"dmg_ice", I, 0.10, 0.04], [&"pen_ice", F, 0.03, 0.01]]),
		_pas(&"tide_stone_mastery", "Tide & Stone Mastery", Vector2(4, 2), 1, [&"frost_mastery"], 6, "+{0}% increased Water, Earth and Wind damage.",
			[[&"dmg_water", I, 0.08, 0.03], [&"dmg_earth", I, 0.08, 0.03], [&"dmg_wind", I, 0.08, 0.03]]),
		_pas(&"inner_fire", "Inner Fire", Vector2(7, 0), 1, [], 1, "+{0}% increased Mana Regeneration.",
			[[&"mana_regen", I, 0.15, 0.06]]),
		_pas(&"arcane_precision", "Arcane Precision", Vector2(7, 2), 1, [&"inner_fire"], 6, "+{0}% Critical Chance and +{1}% Critical Damage.",
			[[&"crit_chance", F, 0.015, 0.005], [&"crit_damage", F, 0.06, 0.03]]),
		_pas(&"mana_shield", "Mana Shield", Vector2(6, 4), 1, [&"arcane_precision"], 12, "{f0}% of damage taken drains Mana instead (1.5 Mana per point).",
			[], {&"mana_shield": [0.15, 0.05]}),
		_pas(&"spell_echo", "Spell Echo", Vector2(8, 4), 1, [&"arcane_precision"], 14, "Damaging spells have a {f0}% chance to cast again at half strength.",
			[], {&"spell_echo": [0.08, 0.02]}),
	] + DataClassRework.nodes(&"mage")

static func ranger_tree() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"ranger_skills"
	t.display_name = "Ranger Skills"
	t.points_kind = &"skill"
	t.pages = [{"name": "Techniques", "desc": "Bow shots, traps and tricks."}, {"name": "Instincts", "desc": "Passive skills: always on."}]
	t.branches = [{"name": "Marksman", "x": 1.0, "color": Color(0.55, 0.85, 0.45)}, {"name": "Wildcraft", "x": 4.0, "color": Color(0.9, 0.6, 0.3)},
		{"name": "Survival", "x": 7.0, "color": Color(0.6, 0.8, 0.95)},
		{"name": "Hawk", "x": 1.0, "color": Color(0.9, 0.85, 0.5), "page": 1}, {"name": "Wolf", "x": 4.0, "color": Color(0.7, 0.75, 0.7), "page": 1},
		{"name": "Fox", "x": 7.0, "color": Color(0.95, 0.55, 0.35), "page": 1}]
	t.nodes = [
		_sk(&"power_shot", Vector2(1, 0), 0, [], 1, [[&"deadeye", 5.0]]),
		_up(&"power_pierce", "Punch Through", &"power_shot", Vector2(0, 1), 0, [&"power_shot"], 4, 1, 2, {"pierce": 1.0, "knockback": 1.0}, "+1 pierce and +1 knockback per rank. Knockback is capped at 12 m/s."),
		_sk(&"multishot", Vector2(2, 1), 0, [&"power_shot"], 3, [[&"arrow_rain", 5.0]]),
		_sk(&"frost_arrow", Vector2(0, 2), 0, [&"power_shot"], 5, [[&"multishot", 4.0]]),
		_sk(&"arrow_rain", Vector2(2, 3), 0, [&"multishot"], 9, [[&"multishot", 5.0]]),
		_up(&"rain_deluge", "Deluge", &"arrow_rain", Vector2(2, 5), 0, [&"arrow_rain"], 16, 2, 1, {"duration": 1.2, "radius": 0.8}, "Arrow Rain lasts longer and covers more ground."),
		_sk(&"deadeye", Vector2(1, 4), 0, [&"frost_arrow", &"multishot"], 12, [[&"power_shot", 6.0]]),
		_sk(&"snare_trap", Vector2(4, 0), 0, [], 2),
		_sk(&"blast_arrow", Vector2(3, 1), 0, [&"snare_trap"], 4, [[&"blast_trap", 5.0]]),
		_sk(&"blast_trap", Vector2(5, 2), 0, [&"snare_trap"], 6, [[&"snare_trap", 6.0], [&"blast_arrow", 4.0]]),
		_up(&"trap_cluster", "Cluster Charges", &"blast_trap", Vector2(5, 4), 0, [&"blast_trap"], 14, 2, 1, {"radius": 0.6, "launch": 1.0}, "Blast Trap gains +0.6 m radius and +1 launch speed. Throws are capped at 6 m/s and 1 m upward travel."),
		_sk(&"storm_javelin", Vector2(3, 3), 0, [&"blast_arrow"], 8, [[&"power_shot", 4.0]]),
		_sk(&"vault", Vector2(7, 0), 0, [], 3),
		_sk(&"hunters_mark", Vector2(7, 2), 0, [&"vault"], 7),
		_up(&"mark_wide", "Pack Hunt", &"hunters_mark", Vector2(8, 3), 0, [&"hunters_mark"], 12, 1, 2, {"radius": 1.2, "mark_dur": 2.0}, "Wider, longer marks."),
		# Instincts (passives)
		_pas(&"keen_eye", "Keen Eye", Vector2(1, 0), 1, [], 1, "+{0}% Critical Chance and +{1} Accuracy.",
			[[&"crit_chance", F, 0.02, 0.008], [&"accuracy", F, 10.0, 5.0]]),
		_pas(&"deadly_aim", "Deadly Aim", Vector2(1, 2), 1, [&"keen_eye"], 6, "+{0}% Critical Damage.",
			[[&"crit_damage", F, 0.08, 0.04]]),
		_pas(&"piercing_arrows", "Piercing Arrows", Vector2(1, 4), 1, [&"deadly_aim"], 12, "Your arrows have a {f0}% chance to pierce one more enemy; +{0}% projectile damage.",
			[[&"projectile_damage", I, 0.04, 0.02]], {&"pierce_chance": [0.12, 0.05]}),
		_pas(&"survivalist", "Survivalist", Vector2(4, 0), 1, [], 1, "+{0}% Maximum HP and +{1}% Status Resistance.",
			[[&"max_hp", I, 0.05, 0.025], [&"status_res", F, 0.04, 0.02]]),
		_pas(&"patient_hunter", "Patient Hunter", Vector2(4, 2), 1, [&"survivalist"], 6, "+{0}% Focus gain. You are Steady from 50 Focus instead of 60.",
			[[&"focus_gain", I, 0.15, 0.07]], {&"steady_50": [1.0, 0.0]}),
		_pas(&"trapmaster", "Trapmaster", Vector2(4, 4), 1, [&"patient_hunter"], 10, "+{0}% trap damage. At rank 5 you may keep one more trap.",
			[[&"trap_damage", I, 0.12, 0.06]], {&"trap_max": [0.0, 0.25]}),
		_pas(&"light_feet", "Light Feet", Vector2(7, 0), 1, [], 1, "+{0}% increased Evasion and {1} s faster dodge recovery.",
			[[&"evasion", I, 0.12, 0.05], [&"dodge_cooldown", F, -0.05, -0.03]]),
		_pas(&"fleet_foot", "Fleet Foot", Vector2(7, 2), 1, [&"light_feet"], 6, "+{0}% increased Movement Speed.",
			[[&"move_speed", I, 0.04, 0.015]]),
	] + DataClassRework.nodes(&"ranger")
	return t

static func shadowblade_tree() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"shadowblade_skills"
	t.display_name = "Shadowblade Skills"
	t.points_kind = &"skill"
	t.pages = [{"name": "Techniques", "desc": "Builders, finishers and shadow tricks."}, {"name": "Disciplines", "desc": "Passive skills: always on."}]
	t.branches = [{"name": "Assassination", "x": 1.0, "color": Color(0.9, 0.3, 0.35)}, {"name": "Shadow Arts", "x": 4.0, "color": Color(0.6, 0.45, 0.9)},
		{"name": "Venom & Traps", "x": 7.0, "color": Color(0.5, 0.9, 0.4)},
		{"name": "Blade", "x": 1.0, "color": Color(0.9, 0.4, 0.4), "page": 1}, {"name": "Shade", "x": 4.0, "color": Color(0.65, 0.5, 0.95), "page": 1},
		{"name": "Fang", "x": 7.0, "color": Color(0.55, 0.9, 0.45), "page": 1}]
	t.nodes = [
		_sk(&"twin_fang", Vector2(1, 0), 0, [], 1),
		_sk(&"eviscerate", Vector2(1, 2), 0, [&"twin_fang"], 3, [[&"twin_fang", 6.0], [&"venom_strike", 6.0]]),
		_up(&"evis_rend", "Rend", &"eviscerate", Vector2(0, 3), 0, [&"eviscerate"], 8, 1, 2, {"per_pip": 8.0}, "+8% damage per Combo pip per rank."),
		_sk(&"crippling_star", Vector2(2, 3), 0, [&"eviscerate"], 6, [[&"fan_of_knives", 5.0]]),
		_sk(&"death_blossom", Vector2(1, 4), 0, [&"eviscerate"], 12, [[&"fan_of_knives", 6.0]]),
		_up(&"blossom_wide", "Crimson Bloom", &"death_blossom", Vector2(1, 5), 0, [&"death_blossom"], 18, 2, 1, {"strikes": 1.0, "range": 0.8}, "One more whirl and a wider reach."),
		_sk(&"shadow_step", Vector2(4, 0), 0, [], 2),
		_sk(&"smoke_veil", Vector2(3, 2), 0, [&"shadow_step"], 5),
		_up(&"veil_blind", "Choking Smoke", &"smoke_veil", Vector2(3, 4), 0, [&"smoke_veil"], 12, 1, 1, {"blind": 1.0}, "Enemies in the smoke are Weakened for its duration."),
		_sk(&"quickstep", Vector2(5, 2), 0, [&"shadow_step"], 7),
		_sk(&"dread_mark", Vector2(4, 4), 0, [&"smoke_veil", &"quickstep"], 14),
		_sk(&"venom_strike", Vector2(7, 0), 0, [], 2),
		_sk(&"fan_of_knives", Vector2(6, 1), 0, [&"venom_strike"], 4, [[&"crippling_star", 5.0]]),
		_sk(&"blade_sentinel", Vector2(8, 2), 0, [&"venom_strike"], 8, [[&"fan_of_knives", 5.0]]),
		_up(&"sentinel_pair", "Twin Sentinels", &"blade_sentinel", Vector2(8, 4), 0, [&"blade_sentinel"], 16, 2, 1, {"max_count": 1.0, "reach": 0.4}, "Keep one more Blade Sentinel; they cut wider."),
		# Disciplines (passives)
		_pas(&"blade_mastery", "Blade Mastery", Vector2(1, 0), 1, [], 1, "Daggers, claws and knuckles deal +{0}% increased damage; +{3}% Attack Speed.",
			[[&"dmg_wt_dagger", I, 0.08, 0.03], [&"dmg_wt_claw", I, 0.08, 0.03], [&"dmg_wt_knuckles", I, 0.08, 0.03], [&"attack_speed", I, 0.02, 0.01]]),
		_pas(&"lethality", "Lethality", Vector2(1, 2), 1, [&"blade_mastery"], 6, "+{0}% Critical Damage.",
			[[&"crit_damage", F, 0.10, 0.04]]),
		_pas(&"ruthless", "Ruthless", Vector2(1, 4), 1, [&"lethality"], 12, "Enemies below 35% HP take {f0}% more damage from you.",
			[], {&"execute": [0.12, 0.04]}),
		_pas(&"evasion", "Evasion", Vector2(4, 0), 1, [], 1, "+{0}% increased Evasion.",
			[[&"evasion", I, 0.15, 0.05]]),
		_pas(&"shadow_discipline", "Shadow Discipline", Vector2(4, 2), 1, [&"evasion"], 6, "Combo lingers {f0} s longer. At rank 5: +1 maximum Combo.",
			[[&"combo_max", F, 0.0, 0.25]], {&"combo_linger": [1.0, 0.5]}),
		_pas(&"opportunist", "Opportunist", Vector2(4, 4), 1, [&"shadow_discipline"], 12, "Hits from behind deal {f0}% more damage.",
			[], {&"backstab": [0.10, 0.04]}),
		_pas(&"venomcraft", "Venomcraft", Vector2(7, 0), 1, [], 2, "+{0}% Damage over Time (Bleeding, Poison) and +{1}% Status Chance.",
			[[&"dot_damage", I, 0.15, 0.06], [&"status_power", I, 0.05, 0.03]]),
		_pas(&"fleet_step", "Fleet Step", Vector2(7, 2), 1, [&"venomcraft"], 6, "+{0}% Movement Speed and {1} s faster dodge recovery.",
			[[&"move_speed", I, 0.03, 0.01], [&"dodge_cooldown", F, -0.05, -0.02]]),
	] + DataClassRework.nodes(&"shadowblade")
	return t

## Description of a passive node at a rank: {0}, {1}... = mod values (percent for fractions), {f0}... = flag values.
static func passive_text(n: Dictionary, rank: int) -> String:
	var r := TreeDef.rank_power(clampi(rank, 1, int(n.get("max_rank", TreeDef.LEVEL_MAX))), int(n.get("base_rank", n.get("max_rank", 1))))
	var text := String(n.get("desc", ""))
	var mods: Array = n.get("mods", [])
	for i in mods.size():
		var v := TreeState.passive_value(mods[i], r)
		var st := StringName(mods[i][0])
		var shown := ""
		if StatDefs.fmt_of(st) in [StatDefs.Fmt.PCT, StatDefs.Fmt.MULT] or int(mods[i][1]) != StatModifier.Op.FLAT:
			shown = StatDefs._num(absf(v) * 100.0)
		elif StatDefs.fmt_of(st) == StatDefs.Fmt.SECONDS:
			shown = "%.2f" % absf(v)
		else:
			shown = StatDefs._num(absf(v))
		text = text.replace("{%d}" % i, shown)
	var fl: Dictionary = n.get("flags", {})
	var i := 0
	for f in fl:
		var v := minf(TreeState.passive_value([f, 0, fl[f][0], fl[f][1]], r), float(DataClassRework.CAPS.get(f, INF)))
		text = text.replace("{f%d}" % i, StatDefs._num(v * 100.0) if (v < 1.0 and f != &"combo_linger") or DataClassRework.CAPS.has(f) else StatDefs._num(v))
		if f == &"split_shot":
			text = text.replace("3-8 arrows (by level)", "%d arrows" % ClassPassives.split_count(v))
		i += 1
	return text
