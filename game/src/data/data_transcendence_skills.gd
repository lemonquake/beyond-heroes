class_name DataTranscendenceSkills
## The 36 active skills of Class Transcendence (three per advanced identity, DataTranscendence). Each is an ordinary
## SkillDef: existing behaviours (dash_strike, melee_arc, projectile, ground_aoe, self_aoe, veil, shadow_step) where they
## fit, and the new `t_*` behaviours in TranscendSkills for zones, challenges, wards and the rest.
##
## Numbers are rank-1 values for a hero of the identity's level (60 or 120); `per_rank` grows them through rank 5 at
## full value and through rank 25 at half value (SkillDef.power), plus up to +5 from items. Weapon skills scale with the
## weapon, spells with Spell Power (Intelligence, Wisdom and the staff), like every other skill.
##
## Generic parameters added for these skills (SkillRunner / TranscendSkills):
##   consume_valor + per_valor       spend all Valor once at cast for +per_valor% weapon damage per point
##   spend_charge + per_charge       spend all Arcane Charge once for per_charge% more damage per charge
##   self_status/self_mods/self_dur  a short buff on the caster when the skill starts
##   vs_marked_pct / vs_bleeding_pct more damage against Marked / Bleeding targets
##   secondary_mult                  damage of every target after the nearest (wide finishers)
##   shared_hits                     one hit per enemy for the whole volley
##   pierce_falloff                  damage share after the first enemy a projectile pierces
##   pen_extra                       extra armor and resistance penetration for this skill (existing caps)
##   heal_from_damage + heal_cap     heal a share of the damage actually dealt, at most heal_cap of Maximum HP per cast

const ICON := "res://assets/ui/icons/skills/%s.svg"

static func _s(id: StringName, name: String, cls: StringName, behavior: StringName, d: Dictionary) -> SkillDef:
	var s := DataSkills._s(id, name, cls, behavior, d)
	s.max_rank = 5
	return s

static func skills() -> Array:
	var ATK := DamageRequest.Kind.ATTACK
	var SPL := DamageRequest.Kind.SPELL
	var F := StatModifier.Op.FLAT
	var I := StatModifier.Op.INC
	var M := StatModifier.Op.MORE
	return [
		# ============================================================================================ ROYAL GUARD
		_s(&"rg_bastion_rush", "Bastion Rush", &"royal_guard", &"dash_strike", {"kind": ATK, "anim": &"shield_bash", "anim_speed_stat": &"attack_speed",
			"mana_cost": 14.0, "mana_per_rank": 0.8, "cooldown": 10.0, "requires": &"shield", "on_hit_status": {&"staggered": [0.6, 0.0]},
			"description": "Charge {dash} m behind your shield and slam everything at the end of the charge: {weapon_pct}% weapon damage, a heavy knockback, and a stagger. The charge stops at walls. Requires a shield.",
			"params": {"weapon_pct": 290.0, "dash": 6.5, "radius": 2.0, "knockback": 11.0, "poise": 90.0, "valor_gain": 10.0},
			"per_rank": {"weapon_pct": 29.0}, "sound_cast": &"dodge_roll", "sound_hit": &"block", "vfx": &"impact_ring"}),
		_s(&"rg_sovereigns_challenge", "Sovereign's Challenge", &"royal_guard", &"t_challenge", {"kind": SPL, "anim": &"war_cry",
			"mana_cost": 16.0, "mana_per_rank": 0.6, "cooldown": 18.0,
			"description": "Challenge every enemy within {radius} m: for {taunt} s they attack you instead of your allies, and you take {dr}% less damage for {duration} s. Bosses ignore the challenge but you keep the protection.",
			"params": {"radius": 7.0, "taunt": 4.0, "dr": 20.0, "duration": 5.0, "valor_gain": 12.0},
			"per_rank": {"dr": 1.0, "duration": 0.2}, "sound_cast": &"war_cry", "vfx": &"war_cry"}),
		_s(&"rg_bulwark_standard", "Bulwark Standard", &"royal_guard", &"t_zone", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 20.0, "mana_per_rank": 1.0, "cooldown": 24.0,
			"aura_mods": [[&"block_chance", F, "block", 0.01], [&"knockback_res", F, "kb", 0.01], [&"poise", I, "poise_inc", 0.01]],
			"description": "Plant a standard at the target for {duration} s. You and every ally within {radius} m gain +{block}% Block Chance, +{kb}% Knockback Resistance and +{poise_inc}% Poise. No shield needed. One standard at a time; several Royal Guards' standards do not stack.",
			"params": {"range": 10.0, "radius": 5.0, "duration": 8.0, "interval": 0.5, "block": 15.0, "kb": 25.0, "poise_inc": 30.0, "mode": "ally", "zone": "standard"},
			"per_rank": {"block": 0.6, "duration": 0.2}, "sound_cast": &"holy_chime", "vfx": &"aura"}),
		# ============================================================================================ DARK GENERAL
		_s(&"dg_dread_cleave", "Dread Cleave", &"dark_general", &"melee_arc", {"kind": ATK, "anim": &"sword_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 10.0, "mana_per_rank": 0.6, "cooldown": 9.0, "requires": &"melee", "conversion": {Elements.DARK: 0.4},
			"on_hit_status": {&"weakened": [3.0, 0.0]},
			"description": "A wide sweep of {arc}° and {range} m: {weapon_pct}% weapon damage, 40% of it as Dark, and every enemy struck is Weakened (20% less damage) for 3 s.",
			"params": {"weapon_pct": 330.0, "arc": 200.0, "range": 3.6, "knockback": 7.0, "poise": 30.0, "valor_gain": 6.0},
			"per_rank": {"weapon_pct": 33.0}, "sound_cast": &"cleave", "sound_hit": &"hit_heavy", "vfx": &"slash_wide"}),
		_s(&"dg_warbound_advance", "Warbound Advance", &"dark_general", &"dash_strike", {"kind": ATK, "anim": &"axe_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 12.0, "mana_per_rank": 0.6, "cooldown": 14.0, "requires": &"melee", "conversion": {Elements.DARK: 0.25},
			"description": "Advance {dash} m and bring down a heavy blow around the end of the advance: {weapon_pct}% weapon damage. For {self_dur} s you gain +50% Knockback Resistance and 50% more Poise.",
			"params": {"weapon_pct": 380.0, "dash": 7.0, "radius": 2.6, "knockback": 12.0, "poise": 70.0, "valor_gain": 10.0,
				"self_status": "warbound", "self_dur": 3.0, "self_mods": [[&"knockback_res", F, 0.5], [&"poise", M, 0.5]]},
			"per_rank": {"weapon_pct": 38.0}, "sound_cast": &"swing_heavy", "sound_hit": &"hit_heavy", "vfx": &"impact_ring"}),
		_s(&"dg_black_dominion", "Black Dominion", &"dark_general", &"t_zone", {"kind": ATK, "anim": &"cast_weapon",
			"mana_cost": 18.0, "mana_per_rank": 1.0, "cooldown": 30.0, "conversion": {Elements.DARK: 0.7},
			"description": "Darken the ground at the target ({radius} m) for {duration} s. It strikes once on landing for {initial_pct}% weapon damage, {per_valor}% more per Valor (all Valor is spent once), then pulses every {interval} s for {weapon_pct}% weapon damage, 70% as Dark.",
			"params": {"range": 12.0, "radius": 4.5, "duration": 3.0, "interval": 0.5, "weapon_pct": 80.0, "initial_pct": 260.0, "consume_valor": 1.0,
				"per_valor": 0.5, "mode": "hostile", "zone": "dominion", "knockback": 0.0, "poise": 8.0},
			"per_rank": {"weapon_pct": 8.0, "initial_pct": 26.0}, "sound_cast": &"dark_cast", "sound_hit": &"dark_curse", "vfx": &"curse"}),
		# ============================================================================================ GRAND PALADIN
		_s(&"gp_dawn_verdict", "Dawn Verdict", &"grand_paladin", &"melee_arc", {"kind": ATK, "anim": &"gs_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 12.0, "mana_per_rank": 0.6, "cooldown": 10.0, "requires": &"melee", "conversion": {Elements.LIGHT: 0.5},
			"description": "A heavy radiant blow ({arc}°, {range} m): {weapon_pct}% weapon damage, half as Light, and {per_valor}% more damage per Valor spent (all Valor is spent once).",
			"params": {"weapon_pct": 300.0, "arc": 70.0, "range": 3.2, "knockback": 10.0, "poise": 50.0, "consume_valor": 1.0, "per_valor": 0.6},
			"per_rank": {"weapon_pct": 30.0}, "sound_cast": &"holy_chime", "sound_hit": &"holy_strike", "vfx": &"judgment"}),
		_s(&"gp_sanctified_ground", "Sanctified Ground", &"grand_paladin", &"t_zone", {"kind": ATK, "anim": &"cast_area",
			"mana_cost": 22.0, "mana_per_rank": 1.0, "cooldown": 24.0, "conversion": {Elements.LIGHT: 1.0},
			"description": "Sanctify {radius} m of ground at the target for {duration} s. Every {interval} s enemies inside take {weapon_pct}% weapon damage as Light, and you and your allies inside recover {heal_pct}% of Maximum HP (each ally at most {heal_cap}% per cast).",
			"params": {"range": 10.0, "radius": 4.5, "duration": 6.0, "interval": 1.0, "weapon_pct": 40.0, "heal_pct": 1.2, "heal_cap": 8.0,
				"mode": "both", "zone": "sanctified", "knockback": 0.0, "poise": 4.0},
			"per_rank": {"weapon_pct": 4.0, "heal_pct": 0.05}, "sound_cast": &"heal", "sound_hit": &"holy_strike", "vfx": &"aura"}),
		_s(&"gp_oath_of_mercy", "Oath of Mercy", &"grand_paladin", &"t_mercy", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 25.0, "mana_per_rank": 1.0, "cooldown": 28.0, "element": Elements.LIGHT,
			"description": "Speak the oath: you and every ally within {radius} m lose one harmful ailment (the worst first) and gain a barrier of {barrier}% of your Maximum HP for {duration} s (at most a quarter of their own Maximum HP).",
			"params": {"radius": 8.0, "barrier": 12.0, "duration": 6.0},
			"per_rank": {"barrier": 0.5}, "sound_cast": &"heal", "vfx": &"ward"}),
		# ============================================================================================ TRACKER
		_s(&"tr_quarry_mark", "Quarry Mark", &"tracker", &"t_mark_one", {"kind": SPL, "anim": &"cast_quick",
			"mana_cost": 8.0, "mana_per_rank": 0.0, "cooldown": 12.0, "element": Elements.LIGHT,
			"description": "Mark the visible enemy nearest your aim (within {range} m) as your quarry for {duration} s: your own arrows, bolts and javelins deal {mark_pct}% more damage to it. Other players' hits are unaffected.",
			"params": {"range": 24.0, "duration": 10.0, "mark_pct": 12.0},
			"per_rank": {"mark_pct": 0.5}, "sound_cast": &"dark_cast", "vfx": &"mark"}),
		_s(&"tr_snareline", "Snareline", &"tracker", &"t_snareline", {"kind": ATK, "anim": &"cast_quick",
			"mana_cost": 12.0, "mana_per_rank": 0.6, "cooldown": 16.0,
			"description": "Lay {count} snares in a line toward your aim. The first time each enemy steps on one it takes {weapon_pct}% weapon damage and is rooted for {root} s (bosses and root-immune enemies are slowed instead). Snares last {duration} s.",
			"params": {"count": 5.0, "spacing": 1.6, "trigger": 1.1, "root": 1.6, "duration": 12.0, "weapon_pct": 130.0, "knockback": 0.0, "poise": 15.0},
			"per_rank": {"weapon_pct": 13.0, "root": 0.03}, "sound_cast": &"armor_rustle", "sound_hit": &"block", "vfx": &"trap"}),
		_s(&"tr_trail_volley", "Trail Volley", &"tracker", &"projectile", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 10.0, "mana_per_rank": 0.6, "cooldown": 10.0, "requires": &"bow", "projectile_look": "arrow",
			"description": "Loose a fan of {count} shots, each {weapon_pct}% weapon damage. Each enemy can be struck by only one shot of the fan.",
			"params": {"weapon_pct": 150.0, "count": 7.0, "spread": 30.0, "speed": 40.0, "range": 24.0, "pierce": 0.0, "shared_hits": 1.0, "knockback": 3.0, "poise": 8.0},
			"per_rank": {"weapon_pct": 15.0}, "sound_cast": &"bow_release", "sound_hit": &"arrow_impact", "vfx": &"multishot"}),
		# ============================================================================================ WILDWARDEN
		_s(&"ww_briar_volley", "Briar Volley", &"wildwarden", &"projectile", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 12.0, "mana_per_rank": 0.6, "cooldown": 12.0, "requires": &"bow", "projectile_look": "arrow", "conversion": {Elements.EARTH: 0.3},
			"description": "Loose {count} briar shots ({weapon_pct}% weapon damage each, 30% Earth; one per enemy) and seed a {patch_radius} m briar patch at your aim that Slows enemies for {patch_dur} s. Overlapping patches slow but never add damage.",
			"params": {"weapon_pct": 140.0, "count": 5.0, "spread": 22.0, "speed": 38.0, "range": 22.0, "pierce": 0.0, "shared_hits": 1.0,
				"patch_radius": 3.0, "patch_dur": 4.0, "knockback": 2.0, "poise": 6.0},
			"per_rank": {"weapon_pct": 14.0, "patch_dur": 0.1}, "sound_cast": &"bow_release", "sound_hit": &"arrow_impact", "vfx": &"multishot"}),
		_s(&"ww_living_thicket", "Living Thicket", &"wildwarden", &"t_zone", {"kind": ATK, "anim": &"cast_area",
			"mana_cost": 18.0, "mana_per_rank": 1.0, "cooldown": 24.0, "conversion": {Elements.EARTH: 1.0},
			"description": "Raise a thicket ({radius} m) at the target for {duration} s. Every {interval} s it deals {weapon_pct}% weapon damage as Earth and Slows enemies inside; the first touch of each cast roots them for {root} s (bosses are only slowed).",
			"params": {"range": 14.0, "radius": 4.0, "duration": 7.0, "interval": 1.0, "weapon_pct": 55.0, "root": 0.8, "mode": "hostile", "zone": "thicket",
				"knockback": 0.0, "poise": 4.0},
			"per_rank": {"weapon_pct": 5.5, "duration": 0.1}, "sound_cast": &"cast_earth", "sound_hit": &"rock_impact", "vfx": &"trap"}),
		_s(&"ww_wardens_refuge", "Warden's Refuge", &"wildwarden", &"t_zone", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 20.0, "mana_per_rank": 1.0, "cooldown": 28.0,
			"aura_mods": [[&"status_res", F, "slow_res", 0.01]],
			"description": "Grow a refuge around you ({radius} m) for {duration} s. You and each ally inside gain a barrier of {barrier}% of their Maximum HP (once per cast) and +{slow_res}% Status Resistance against Slows, Chill and Roots while inside.",
			"params": {"radius": 4.5, "duration": 6.0, "interval": 0.5, "barrier": 10.0, "slow_res": 30.0, "mode": "ally", "zone": "refuge", "at_feet": 1.0},
			"per_rank": {"barrier": 0.4, "slow_res": 1.0}, "sound_cast": &"heal", "vfx": &"ward"}),
		# ============================================================================================ STARSTRIDER
		_s(&"ss_astral_pierce", "Astral Pierce", &"starstrider", &"projectile", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 12.0, "mana_per_rank": 0.6, "cooldown": 12.0, "requires": &"bow", "projectile_look": "arrow", "conversion": {Elements.LIGHT: 0.4},
			"description": "A narrow starlit shot that pierces every enemy in line: {weapon_pct}% weapon damage (40% Light), {per_focus}% more per Focus spent (all Focus is spent once). Enemies after the first take {falloff_pct}%.",
			"params": {"weapon_pct": 260.0, "per_focus": 0.5, "focus_more": 1.0, "consume_focus": 1.0, "speed": 70.0, "count": 1.0, "spread": 0.0, "pierce": 99.0, "range": 34.0,
				"width": 0.6, "pierce_falloff": 0.6, "falloff_pct": 60.0, "knockback": 6.0, "poise": 20.0},
			"per_rank": {"weapon_pct": 26.0}, "sound_cast": &"bow_release", "sound_hit": &"crit_hit", "vfx": &"deadeye"}),
		_s(&"ss_comet_step", "Comet Step", &"starstrider", &"t_comet_step", {"kind": ATK, "anim": &"dodge_step",
			"mana_cost": 10.0, "mana_per_rank": 0.0, "cooldown": 18.0,
			"description": "Vault {range} m away from your aim (you cannot be hit while in the air). For {window} s your next arrow, bolt or javelin deals {bonus}% more damage.",
			"params": {"range": 7.0, "window": 5.0, "bonus": 45.0},
			"per_rank": {"bonus": 1.5}, "sound_cast": &"dodge_roll", "vfx": &"vault"}),
		_s(&"ss_constellation_rain", "Constellation Rain", &"starstrider", &"t_constellation", {"kind": ATK, "anim": &"bow_release", "anim_speed_stat": &"attack_speed",
			"mana_cost": 22.0, "mana_per_rank": 1.0, "cooldown": 30.0, "requires": &"bow", "projectile_look": "arrow", "conversion": {Elements.LIGHT: 0.3},
			"description": "{impacts} starlit shots fall over {duration} s in a {radius} m area at a visible point: each deals {weapon_pct}% weapon damage (30% Light) within {impact_radius} m. One enemy is struck at most {hit_cap} times.",
			"params": {"range": 22.0, "radius": 5.0, "impacts": 12.0, "duration": 2.4, "impact_radius": 1.6, "weapon_pct": 100.0, "hit_cap": 4.0, "knockback": 1.0, "poise": 6.0},
			"per_rank": {"weapon_pct": 10.0}, "sound_cast": &"bow_release", "sound_hit": &"arrow_impact", "vfx": &"arrow_rain"}),
		# ============================================================================================ ARCANIST
		_s(&"ar_aether_lance", "Aether Lance", &"arcanist", &"projectile", {"kind": SPL, "anim": &"cast_heavy",
			"mana_cost": 16.0, "mana_per_rank": 1.0, "cooldown": 8.0, "conversion": {Elements.LIGHT: 0.6, Elements.DARK: 0.4},
			"description": "An aimed lance of Aether that pierces every enemy in line: {damage_min}-{damage_max} damage, 60% Light and 40% Dark.",
			"params": {"damage_min": 40.0, "damage_max": 55.0, "speed": 46.0, "count": 1.0, "spread": 0.0, "pierce": 99.0, "range": 28.0, "width": 1.0,
				"knockback": 4.0, "poise": 16.0},
			"per_rank": {"damage_min": 6.5, "damage_max": 8.5}, "sound_cast": &"arcane_surge", "sound_hit": &"holy_strike", "vfx": &"arcane_surge"}),
		_s(&"ar_runic_circle", "Runic Circle", &"arcanist", &"t_zone", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 20.0, "mana_per_rank": 1.0, "cooldown": 22.0,
			"description": "Draw a runic circle ({radius} m) at your feet for {duration} s. While you stand in it, spells you pay Mana for deal {spell_pct}% more damage. One circle at a time; it never stacks with itself.",
			"params": {"radius": 4.0, "duration": 10.0, "interval": 0.25, "spell_pct": 10.0, "mode": "self", "zone": "runic", "at_feet": 1.0},
			"per_rank": {"spell_pct": 0.4}, "sound_cast": &"arcane_surge", "vfx": &"aura"}),
		_s(&"ar_mana_ward", "Mana Ward", &"arcanist", &"t_mana_ward", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 30.0, "mana_per_rank": 2.0, "cooldown": 24.0, "element": Elements.LIGHT,
			"description": "Pour Mana into a ward: it absorbs {per_mana} damage for each point of Mana paid, at most {cap}% of your Maximum HP, for {duration} s. The ward never drains more Mana after it forms.",
			"params": {"per_mana": 3.0, "cap": 30.0, "duration": 8.0},
			"per_rank": {"per_mana": 0.15, "cap": 0.4}, "sound_cast": &"heal", "vfx": &"ward"}),
		# ============================================================================================ ARCHMAGE
		_s(&"am_prismatic_tempest", "Prismatic Tempest", &"archmage", &"t_zone", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 30.0, "mana_per_rank": 1.5, "cooldown": 30.0, "element": Elements.LIGHTNING,
			"description": "A tempest ({radius} m) at the target for {duration} s. Every {interval} s it strikes with Fire, then Water, then Lightning: {damage_min}-{damage_max} damage. Water leaves enemies Wet, so the next Lightning pulse conducts (+25%) and Fire is dampened. One enemy is struck at most {hit_cap} times.",
			"params": {"range": 18.0, "radius": 5.0, "duration": 4.0, "interval": 0.5, "damage_min": 7.0, "damage_max": 10.0, "hit_cap": 6.0,
				"mode": "hostile", "zone": "tempest", "knockback": 0.0, "poise": 4.0, "ignite": 40.0},
			"per_rank": {"damage_min": 1.0, "damage_max": 1.3}, "sound_cast": &"chain_lightning", "sound_hit": &"lightning_zap", "vfx": &"lightning"}),
		_s(&"am_grand_convergence", "Grand Convergence", &"archmage", &"ground_aoe", {"kind": SPL, "anim": &"cast_heavy",
			"mana_cost": 28.0, "mana_per_rank": 1.5, "cooldown": 24.0,
			"conversion": {Elements.FIRE: 0.34, Elements.ICE: 0.33, Elements.LIGHTNING: 0.33},
			"description": "Fire, Ice and Lightning converge on the target after {delay} s: {damage_min}-{damage_max} damage within {radius} m, {per_charge}% more per Arcane Charge (all charge is spent once).",
			"params": {"damage_min": 34.0, "damage_max": 46.0, "radius": 4.5, "delay": 0.5, "range": 20.0, "spend_charge": 1.0, "per_charge": 18.0,
				"knockback": 8.0, "poise": 40.0, "status_power": 1.2},
			"per_rank": {"damage_min": 4.7, "damage_max": 6.1}, "sound_cast": &"meteor_cast", "sound_hit": &"meteor_hit", "vfx": &"meteor"}),
		_s(&"am_spellweave", "Spellweave", &"archmage", &"t_spellweave", {"kind": SPL, "anim": &"cast_quick",
			"mana_cost": 18.0, "mana_per_rank": 0.8, "cooldown": 28.0,
			"description": "Weave the next damaging spell you pay Mana for within {duration} s: it repeats once at {weave_pct}% strength. The repeat costs nothing, refunds nothing and cannot repeat or echo again.",
			"params": {"duration": 10.0, "weave_pct": 55.0},
			"per_rank": {"weave_pct": 0.8}, "sound_cast": &"arcane_surge", "vfx": &"arcane_surge"}),
		# ============================================================================================ VOID SOVEREIGN
		_s(&"vs_event_horizon", "Event Horizon", &"void_sovereign", &"t_zone", {"kind": SPL, "anim": &"cast_area",
			"mana_cost": 28.0, "mana_per_rank": 1.5, "cooldown": 28.0, "element": Elements.DARK,
			"description": "Open a gravity well ({radius} m) at the target for {duration} s. Every {interval} s it pulls enemies toward its center (walls stop the pull; Knockback Resistance shortens it; bosses are not pulled) and deals {damage_min}-{damage_max} Dark damage.",
			"params": {"range": 16.0, "radius": 5.5, "duration": 4.0, "interval": 0.5, "damage_min": 12.0, "damage_max": 16.0, "pull": 1.6,
				"mode": "hostile", "zone": "horizon", "knockback": 0.0, "poise": 6.0},
			"per_rank": {"damage_min": 1.6, "damage_max": 2.2}, "sound_cast": &"arcane_surge", "sound_hit": &"dark_curse", "vfx": &"curse"}),
		_s(&"vs_null_lance", "Null Lance", &"void_sovereign", &"projectile", {"kind": SPL, "anim": &"cast_heavy",
			"mana_cost": 18.0, "mana_per_rank": 1.0, "cooldown": 12.0, "element": Elements.DARK, "projectile_look": "dark",
			"description": "A lance of nothing that pierces every enemy in line: {damage_min}-{damage_max} Dark damage that ignores {pen_pct}% more of their armor and Dark Resistance (penetration limits still apply).",
			"params": {"damage_min": 60.0, "damage_max": 82.0, "speed": 44.0, "count": 1.0, "spread": 0.0, "pierce": 99.0, "range": 26.0, "width": 0.9,
				"pen_extra": 0.15, "pen_pct": 15.0, "knockback": 3.0, "poise": 14.0},
			"per_rank": {"damage_min": 9.0, "damage_max": 12.0}, "sound_cast": &"dark_cast", "sound_hit": &"dark_curse", "vfx": &"curse"}),
		_s(&"vs_rift_collapse", "Rift Collapse", &"void_sovereign", &"ground_aoe", {"kind": SPL, "anim": &"cast_heavy",
			"mana_cost": 32.0, "mana_per_rank": 1.5, "cooldown": 30.0, "element": Elements.DARK,
			"description": "Tear a rift at a visible point. After a clear {delay} s warning it collapses: {damage_min}-{damage_max} Dark damage within {radius} m, {per_charge}% more per Arcane Charge (all charge is spent once).",
			"params": {"damage_min": 84.0, "damage_max": 116.0, "radius": 5.0, "delay": 1.6, "range": 22.0, "spend_charge": 1.0, "per_charge": 20.0,
				"knockback": 10.0, "poise": 50.0, "visible": 1.0},
			"per_rank": {"damage_min": 11.5, "damage_max": 16.0}, "sound_cast": &"dark_cast", "sound_hit": &"dark_curse", "vfx": &"curse"}),
		# ============================================================================================ NIGHTSTALKER
		_s(&"ns_umbral_lunge", "Umbral Lunge", &"nightstalker", &"dash_strike", {"kind": ATK, "anim": &"dagger_2", "anim_speed_stat": &"attack_speed",
			"mana_cost": 10.0, "mana_per_rank": 0.5, "cooldown": 10.0, "requires": &"melee", "conversion": {Elements.DARK: 0.3},
			"description": "Lunge {dash} m through the shadows and strike: {weapon_pct}% weapon damage, 30% as Dark. A cast that lands adds {combo_gain} Combo once, however many enemies it strikes.",
			"params": {"weapon_pct": 230.0, "dash": 7.0, "radius": 1.8, "combo_gain": 1.0, "knockback": 4.0, "poise": 14.0},
			"per_rank": {"weapon_pct": 23.0}, "sound_cast": &"blink", "sound_hit": &"hit_flesh", "vfx": &"shadow_step"}),
		_s(&"ns_gloom_veil", "Gloom Veil", &"nightstalker", &"veil", {"kind": SPL, "anim": &"cast_quick",
			"mana_cost": 14.0, "mana_per_rank": 0.0, "cooldown": 22.0,
			"description": "Wrap yourself in gloom: enemies within {radius} m lose you, and you gain Stealth and {evasion}% more Evasion for {duration} s. Attacking ends both.",
			"params": {"radius": 5.0, "duration": 2.5, "evasion": 50.0, "self_status": "gloom_veil", "self_dur": 2.5, "self_mods": [[&"evasion", M, 0.5]]},
			"per_rank": {"duration": 0.05}, "sound_cast": &"shade_hiss", "vfx": &"smoke"}),
		_s(&"ns_marked_execution", "Marked Execution", &"nightstalker", &"melee_arc", {"kind": ATK, "anim": &"dual_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 12.0, "mana_per_rank": 0.6, "cooldown": 16.0, "requires": &"melee",
			"description": "Finisher. Spend all Combo on one enemy: {weapon_pct}% weapon damage, {pip_more}% more per pip, and {vs_marked_pct}% more against a Marked or Quarry-marked enemy. Poised: always a critical hit.",
			"params": {"weapon_pct": 220.0, "pip_more": 18.0, "consume_combo": 1.0, "max_targets": 1.0, "vs_marked_pct": 25.0, "arc": 80.0, "range": 2.6,
				"knockback": 8.0, "poise": 30.0},
			"per_rank": {"weapon_pct": 20.0, "pip_more": 0.6}, "sound_cast": &"swing_heavy", "sound_hit": &"crit_hit", "vfx": &"eviscerate"}),
		# ============================================================================================ PHANTOM REAPER
		_s(&"pr_phantom_crossing", "Phantom Crossing", &"phantom_reaper", &"shadow_step", {"kind": ATK, "anim": &"dagger_2", "anim_speed_stat": &"attack_speed",
			"mana_cost": 12.0, "mana_per_rank": 0.0, "cooldown": 18.0, "requires": &"melee",
			"description": "Cross to the far side of the enemy nearest your aim (up to {range} m; walls stop you) and strike for {weapon_pct}% weapon damage. For {self_dur} s afterwards you have 60% more Evasion. +{combo_gain} Combo.",
			"params": {"weapon_pct": 220.0, "range": 9.0, "arc": 90.0, "combo_gain": 1.0, "knockback": 3.0, "poise": 12.0,
				"self_status": "phantom_evade", "self_dur": 1.0, "self_mods": [[&"evasion", M, 0.6]]},
			"per_rank": {"weapon_pct": 22.0}, "sound_cast": &"blink", "sound_hit": &"hit_flesh", "vfx": &"shadow_step"}),
		_s(&"pr_reapers_arc", "Reaper's Arc", &"phantom_reaper", &"melee_arc", {"kind": ATK, "anim": &"whirlwind", "anim_speed_stat": &"attack_speed",
			"mana_cost": 14.0, "mana_per_rank": 0.6, "cooldown": 20.0, "requires": &"melee",
			"description": "Finisher. Spend all Combo on a {arc}° reaping arc ({range} m): {weapon_pct}% weapon damage, {pip_more}% more per pip, to the nearest enemy and {secondary_pct}% of that to the others.",
			"params": {"weapon_pct": 220.0, "pip_more": 12.0, "consume_combo": 1.0, "arc": 240.0, "range": 3.6, "secondary_mult": 0.55, "secondary_pct": 55.0,
				"knockback": 6.0, "poise": 20.0},
			"per_rank": {"weapon_pct": 22.0, "pip_more": 0.4}, "sound_cast": &"whirlwind_loop", "sound_hit": &"crit_hit", "vfx": &"blossom"}),
		_s(&"pr_afterimage_flurry", "Afterimage Flurry", &"phantom_reaper", &"t_afterimage", {"kind": ATK, "anim": &"dual_4", "anim_speed_stat": &"attack_speed",
			"mana_cost": 16.0, "mana_per_rank": 0.8, "cooldown": 28.0, "requires": &"melee",
			"description": "Leave {strikes} afterimages that strike from where you stand over {span} s: each hits the nearest enemy within {reach} m for {weapon_pct}% weapon damage. Afterimage hits cannot trigger Double Attack or other repeat attacks.",
			"params": {"strikes": 5.0, "span": 1.0, "reach": 4.5, "weapon_pct": 95.0, "knockback": 1.0, "poise": 5.0},
			"per_rank": {"weapon_pct": 9.5}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"twin_fang"}),
		# ============================================================================================ BLOOD SOVEREIGN
		_s(&"bs_crimson_rend", "Crimson Rend", &"blood_sovereign", &"melee_arc", {"kind": ATK, "anim": &"dagger_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 10.0, "mana_per_rank": 0.5, "cooldown": 10.0, "requires": &"melee",
			"description": "A rending cut ({arc}°, {range} m): {weapon_pct}% weapon damage and heavy Bleeding ({bleed}). +{combo_gain} Combo.",
			"params": {"weapon_pct": 210.0, "arc": 120.0, "range": 2.8, "bleed": 160.0, "combo_gain": 1.0, "knockback": 3.0, "poise": 10.0},
			"per_rank": {"weapon_pct": 21.0, "bleed": 6.0}, "sound_cast": &"swing_dagger", "sound_hit": &"hit_flesh", "vfx": &"venom"}),
		_s(&"bs_sanguine_pact", "Sanguine Pact", &"blood_sovereign", &"t_pact", {"kind": SPL, "anim": &"cast_quick",
			"mana_cost": 0.0, "mana_per_rank": 0.0, "cooldown": 26.0,
			"description": "Pay {hp_cost}% of your current HP (never your last point of HP) to deal {dmg}% more damage for {duration} s. While the pact lasts each hit you land heals {heal_hit}% of your Maximum HP, at most {heal_sec}% a second.",
			"params": {"hp_cost": 12.0, "dmg": 12.0, "heal_hit": 0.5, "heal_sec": 4.0, "duration": 8.0},
			"per_rank": {"dmg": 0.4, "duration": 0.1}, "sound_cast": &"dark_curse", "vfx": &"blossom"}),
		_s(&"bs_blood_eclipse", "Blood Eclipse", &"blood_sovereign", &"self_aoe", {"kind": ATK, "anim": &"whirlwind", "anim_speed_stat": &"attack_speed",
			"mana_cost": 16.0, "mana_per_rank": 0.8, "cooldown": 30.0, "requires": &"melee",
			"description": "Finisher. Spend all Combo in an eclipse of blood around you ({radius} m): {weapon_pct}% weapon damage, {pip_more}% more per pip, and {vs_bleeding_pct}% more to Bleeding enemies. You heal {heal_pct}% of the damage actually dealt, at most {heal_cap_pct}% of your Maximum HP per cast.",
			"params": {"weapon_pct": 170.0, "pip_more": 12.0, "consume_combo": 1.0, "radius": 4.5, "vs_bleeding_pct": 35.0, "heal_from_damage": 0.10, "heal_pct": 10.0,
				"heal_cap": 0.12, "heal_cap_pct": 12.0, "knockback": 6.0, "poise": 20.0},
			"per_rank": {"weapon_pct": 17.0, "pip_more": 0.4}, "sound_cast": &"dark_curse", "sound_hit": &"hit_flesh", "vfx": &"blossom"}),
	]

## Page captions and colours for the composed trees (ClassTranscendence.compose_tree).
static func page_of(identity: StringName) -> Dictionary:
	var d := DataTranscendence.info(identity)
	var stage := DataTranscendence.stage_of(identity)
	return {"name": String(d.get("name", "")), "desc": "%s. Granted at level %d." % [String(d.get("role", "")), DataTranscendence.level_for_stage(stage)],
		"identity": identity}

## The three skill nodes of an identity on tree page `page`.
static func skill_nodes(identity: StringName, page: int) -> Array:
	var d := DataTranscendence.info(identity)
	var lvl := DataTranscendence.level_for_stage(DataTranscendence.stage_of(identity))
	var out := []
	var xs := [1, 4, 7]
	var i := 0
	for sid in d.get("skills", []):
		var sd := DB.skill(sid)
		out.append({"id": sid, "name": sd.display_name if sd else String(sid), "kind": "skill", "skill": sid, "icon": ICON % sid,
			"pos": Vector2(xs[i], 1), "page": page, "max_rank": 5, "cost": 1, "requires": [], "req_level": lvl, "granted_by": identity})
		i += 1
	return out

## The three talent nodes of an identity on talent page `page`.
static func talent_nodes(identity: StringName, page: int) -> Array:
	var d := DataTranscendence.info(identity)
	var lvl := DataTranscendence.level_for_stage(DataTranscendence.stage_of(identity))
	var out := []
	var xs := [1, 4, 7]
	var i := 0
	for tid in d.get("talents", []):
		var t: Dictionary = DataTranscendence.TALENTS[tid]
		var n := {"id": tid, "name": String(t.name), "kind": String(t.kind), "icon": DataTranscendence.TALENT_ICON % tid, "pos": Vector2(xs[i], 1),
			"page": page, "max_rank": 1 if t.kind == "major" else 5, "cost": 1, "requires": [], "req_level": lvl, "desc": DataTranscendence.talent_text(tid, 1),
			"granted_by": identity, "tail": DataTranscendence.TAIL, "base_rank": 1, "transcend_talent": true}
		var mods: Array = []
		for m in t.get("mods", []):
			mods.append([m[0], m[1], m[2]])
		if not mods.is_empty():
			n["mods"] = mods
		if t.has("flags"):
			n["flags"] = (t.flags as Dictionary).duplicate()
		out.append(n)
		i += 1
	return out
