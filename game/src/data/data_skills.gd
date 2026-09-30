class_name DataSkills
## Active skills for both classes and their skill trees (skills + upgrade nodes).

const ICON := "res://assets/ui/icons/skills/%s.svg"

static func _s(id: StringName, name: String, cls: StringName, behavior: StringName, d: Dictionary) -> SkillDef:
	var s := SkillDef.new()
	s.id = id
	s.display_name = name
	s.class_id = cls
	s.behavior = behavior
	s.icon = ICON % id
	for k in d:
		s.set(k, d[k])
	return s

static func skills() -> Array:
	var ATK := DamageRequest.Kind.ATTACK
	var SPL := DamageRequest.Kind.SPELL
	return [
		# ------------------------------------------------------------------ KNIGHT
		_s(&"cleave", "Cleave", &"knight", &"melee_arc", {"kind": ATK, "anim": &"sword_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 4.0, "mana_per_rank": 0.5, "cooldown": 0.0, "requires": &"melee",
			"description": "A wide, heavy sweep dealing {weapon_pct}% weapon damage to all enemies in a {arc}° arc and knocking them back.",
			"params": {"weapon_pct": 150.0, "arc": 170.0, "range": 3.0, "knockback": 9.0, "poise": 22.0, "valor_gain": 4.0},
			"per_rank": {"weapon_pct": 18.0}, "sound_cast": &"cleave", "sound_hit": &"hit_heavy", "vfx": &"slash_wide"}),
		_s(&"shield_bash", "Shield Bash", &"knight", &"dash_strike", {"kind": ATK, "anim": &"shield_bash", "anim_speed_stat": &"attack_speed",
			"mana_cost": 6.0, "cooldown": 5.0, "requires": &"", "on_hit_status": {&"sundered": [5.0, 0.0]},
			"description": "Charge {dash} m and slam your shield into the first enemy: {weapon_pct}% weapon damage, stun and a violent knockback. Sunders the target (25% less Defense). Without a shield, uses the pommel for half the stun.",
			"params": {"weapon_pct": 120.0, "dash": 4.0, "radius": 1.6, "knockback": 17.0, "poise": 45.0, "stun": 100.0, "valor_gain": 8.0},
			"per_rank": {"weapon_pct": 20.0}, "sound_cast": &"dodge_roll", "sound_hit": &"block", "vfx": &"impact_ring"}),
		_s(&"leap_slam", "Leap Slam", &"knight", &"leap", {"kind": ATK, "anim": &"leap_slam", "anim_speed_stat": &"attack_speed",
			"mana_cost": 10.0, "cooldown": 7.0, "requires": &"melee", "conversion": {Elements.EARTH: 0.4},
			"description": "Leap to a location up to {range} m away and crash down for {weapon_pct}% weapon damage as Physical and Earth in a {radius} m radius, launching enemies.",
			"params": {"weapon_pct": 190.0, "range": 11.0, "radius": 3.6, "knockback": 12.0, "poise": 40.0, "launch": 6.0, "valor_gain": 6.0},
			"per_rank": {"weapon_pct": 25.0}, "sound_cast": &"swing_heavy", "sound_hit": &"earth_quake", "vfx": &"ground_slam"}),
		_s(&"whirlwind", "Whirlwind", &"knight", &"spin", {"kind": ATK, "anim": &"whirlwind", "anim_speed_stat": &"attack_speed",
			"mana_cost": 3.0, "cooldown": 0.0, "requires": &"melee",
			"description": "Channel a spinning storm of steel, hitting everything within {radius} m for {weapon_pct}% weapon damage every {tick} s. Costs {mana_per_tick} Mana per tick; you move at reduced speed.",
			"params": {"weapon_pct": 55.0, "radius": 2.8, "tick": 0.3, "mana_per_tick": 2.0, "knockback": 3.0, "poise": 6.0, "move_mult": 0.6, "valor_gain": 1.0},
			"per_rank": {"weapon_pct": 7.0}, "sound_cast": &"whirlwind_loop", "sound_hit": &"hit_flesh", "vfx": &"spin"}),
		_s(&"war_cry", "War Cry", &"knight", &"buff", {"kind": SPL, "anim": &"war_cry", "mana_cost": 12.0, "cooldown": 18.0,
			"description": "A thunderous cry: +{defense_inc}% Defense and +{valor_inc}% Valor generation for {duration} s, staggering nearby enemies.",
			"params": {"duration": 10.0, "defense_inc": 30.0, "valor_inc": 50.0, "radius": 6.0, "poise": 30.0},
			"per_rank": {"defense_inc": 6.0, "duration": 1.0}, "sound_cast": &"war_cry", "vfx": &"war_cry"}),
		_s(&"judgment", "Judgment", &"knight", &"judgment", {"kind": ATK, "anim": &"gs_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 8.0, "valor_cost": 30.0, "cooldown": 6.0, "requires": &"melee", "conversion": {Elements.LIGHT: 0.5}, "on_hit_status": {&"demoralized": [5.0, 0.0]},
			"description": "Spend all Valor (min {valor_min}) on a radiant overhead strike: {weapon_pct}% weapon damage +{per_valor}% per Valor spent as Physical and Light in a line. Heals 5% of damage dealt and Demoralizes the foe.",
			"params": {"weapon_pct": 200.0, "per_valor": 3.0, "valor_min": 30.0, "length": 7.0, "width": 2.4, "knockback": 14.0, "poise": 60.0, "heal_pct": 0.05},
			"per_rank": {"weapon_pct": 30.0}, "sound_cast": &"holy_chime", "sound_hit": &"holy_strike", "vfx": &"judgment"}),
		_s(&"ground_fissure", "Ground Fissure", &"knight", &"wave", {"kind": ATK, "anim": &"axe_heavy", "anim_speed_stat": &"attack_speed",
			"mana_cost": 9.0, "cooldown": 4.0, "requires": &"melee", "conversion": {Elements.EARTH: 1.0},
			"description": "Split the earth in a {length} m line: {weapon_pct}% weapon damage as Earth. Heavily staggers and ignores part of armor.",
			"params": {"weapon_pct": 140.0, "length": 10.0, "width": 2.2, "speed": 18.0, "knockback": 6.0, "poise": 50.0, "launch": 3.0, "valor_gain": 5.0},
			"per_rank": {"weapon_pct": 18.0}, "sound_cast": &"earth_quake", "sound_hit": &"rock_impact", "vfx": &"fissure"}),
		_s(&"iron_bulwark", "Iron Bulwark", &"knight", &"buff", {"kind": SPL, "anim": &"block_impact", "mana_cost": 10.0, "cooldown": 14.0,
			"description": "Brace behind your guard for {duration} s: +{block}% Block Chance and +{kb_res}% Knockback Resistance. Blocks during Bulwark grant double Valor.",
			"params": {"duration": 6.0, "block": 25.0, "kb_res": 40.0},
			"per_rank": {"block": 3.0, "duration": 0.5}, "sound_cast": &"block", "vfx": &"guard"}),
		# ------------------------------------------------------------------ MAGE
		_s(&"firebolt", "Firebolt", &"mage", &"projectile", {"element": Elements.FIRE, "anim": &"cast_quick", "mana_cost": 5.0, "mana_per_rank": 0.6,
			"description": "Hurl a bolt of fire for {damage_min}-{damage_max} Fire damage that always ignites. At 3+ Arcane Charge it splits into three.",
			"params": {"damage_min": 9.0, "damage_max": 14.0, "speed": 24.0, "count": 1.0, "spread": 12.0, "pierce": 0.0, "range": 22.0,
				"knockback": 2.0, "poise": 6.0, "ignite": 100.0, "explode_radius": 0.0, "charge_split": 3.0},
			"per_rank": {"damage_min": 3.0, "damage_max": 4.5}, "sound_cast": &"fireball_cast", "sound_hit": &"fireball_hit", "vfx": &"fire_bolt"}),
		_s(&"frost_nova", "Frost Nova", &"mage", &"self_aoe", {"element": Elements.ICE, "anim": &"cast_area", "mana_cost": 12.0, "cooldown": 6.0,
			"description": "Release a ring of frost: {damage_min}-{damage_max} Ice damage within {radius} m and heavy Chill buildup. Wet enemies freeze instantly.",
			"params": {"damage_min": 12.0, "damage_max": 18.0, "radius": 5.5, "knockback": 3.0, "poise": 10.0, "status_power": 3.0, "chill_direct": 60.0},
			"per_rank": {"damage_min": 4.0, "damage_max": 6.0, "radius": 0.2}, "sound_cast": &"ice_nova", "sound_hit": &"freeze", "vfx": &"frost_nova"}),
		_s(&"chain_lightning", "Chain Lightning", &"mage", &"chain", {"element": Elements.LIGHTNING, "anim": &"cast_quick", "mana_cost": 9.0, "cooldown": 0.0,
			"description": "A bolt that arcs between up to {chains} enemies for {damage_min}-{damage_max} Lightning damage each, losing 10% per jump.",
			"params": {"damage_min": 4.0, "damage_max": 24.0, "chains": 4.0, "chain_range": 8.0, "range": 18.0, "knockback": 1.0, "poise": 4.0},
			"per_rank": {"damage_min": 1.0, "damage_max": 7.0, "chains": 0.5}, "sound_cast": &"chain_lightning", "sound_hit": &"lightning_zap", "vfx": &"lightning"}),
		_s(&"blink", "Blink", &"mage", &"blink", {"element": Elements.PHYSICAL, "anim": &"blink", "mana_cost": 8.0, "cooldown": 3.0,
			"description": "Teleport up to {range} m toward the cursor, leaving an arcane burst that pushes nearby enemies away.",
			"params": {"range": 9.0, "radius": 2.5, "knockback": 8.0},
			"per_rank": {"range": 0.5}, "sound_cast": &"blink", "vfx": &"blink"}),
		_s(&"meteor", "Meteor Strike", &"mage", &"ground_aoe", {"element": Elements.FIRE, "conversion": {Elements.FIRE: 0.6, Elements.EARTH: 0.4}, "anim": &"cast_heavy",
			"mana_cost": 45.0, "mana_per_rank": 2.0, "cooldown": 24.0,
			"description": "Call a meteor onto the target area after {delay} s: {damage_min}-{damage_max} Fire and Earth damage in {radius} m, burning ground, massive impact.",
			"params": {"damage_min": 90.0, "damage_max": 130.0, "radius": 7.0, "delay": 1.1, "range": 20.0, "knockback": 13.0, "poise": 60.0,
				"launch": 7.0, "burn_ground": 4.0, "status_power": 1.5},
			"per_rank": {"damage_min": 22.0, "damage_max": 32.0}, "sound_cast": &"meteor_cast", "sound_hit": &"meteor_hit", "vfx": &"meteor"}),
		_s(&"tidal_wave", "Tidal Wave", &"mage", &"wave", {"element": Elements.WATER, "anim": &"cast_heavy", "mana_cost": 14.0, "cooldown": 5.0,
			"description": "A crashing wave in a {length} m line: {damage_min}-{damage_max} Water damage, soaks enemies (Wet) and sweeps them away.",
			"params": {"damage_min": 14.0, "damage_max": 20.0, "length": 12.0, "width": 3.6, "speed": 14.0, "knockback": 12.0, "poise": 18.0, "push_along": 1.0},
			"per_rank": {"damage_min": 4.0, "damage_max": 6.0}, "sound_cast": &"water_wave", "sound_hit": &"water_splash", "vfx": &"wave"}),
		_s(&"gale_burst", "Gale Burst", &"mage", &"projectile", {"element": Elements.WIND, "anim": &"cast_quick", "mana_cost": 8.0, "cooldown": 2.0,
			"description": "A piercing blast of wind: {damage_min}-{damage_max} Wind damage, huge knockback, destroys enemy projectiles in its path and fans Burning.",
			"params": {"damage_min": 8.0, "damage_max": 12.0, "speed": 30.0, "count": 1.0, "spread": 0.0, "pierce": 99.0, "range": 16.0,
				"knockback": 16.0, "poise": 14.0, "width": 1.6, "deflect": 1.0},
			"per_rank": {"damage_min": 2.5, "damage_max": 3.5}, "sound_cast": &"wind_gust", "sound_hit": &"wind_gust", "vfx": &"gale"}),
		_s(&"stone_spear", "Stone Spear", &"mage", &"projectile", {"element": Elements.EARTH, "anim": &"cast_heavy", "mana_cost": 11.0, "cooldown": 3.0,
			"description": "Launch a jagged spear of stone: {damage_min}-{damage_max} Earth damage, massive stagger; pins enemies against walls for extra impact.",
			"params": {"damage_min": 22.0, "damage_max": 30.0, "speed": 28.0, "count": 1.0, "spread": 0.0, "pierce": 1.0, "range": 20.0,
				"knockback": 14.0, "poise": 55.0},
			"per_rank": {"damage_min": 6.0, "damage_max": 8.0}, "sound_cast": &"cast_earth", "sound_hit": &"rock_impact", "vfx": &"stone_spear"}),
		_s(&"arcane_surge", "Arcane Surge", &"mage", &"self_aoe", {"element": Elements.LIGHT, "conversion": {Elements.LIGHT: 0.5, Elements.DARK: 0.5},
			"anim": &"cast_area", "mana_cost": 15.0, "cooldown": 10.0,
			"description": "Detonate all Arcane Charge: {damage_min}-{damage_max} damage (Light and Dark) +{per_charge}% per charge in {radius} m. Restores {mana_per_charge} Mana per charge.",
			"params": {"damage_min": 20.0, "damage_max": 28.0, "radius": 5.0, "per_charge": 35.0, "mana_per_charge": 6.0, "knockback": 10.0, "poise": 30.0, "consume_charge": 1.0},
			"per_rank": {"damage_min": 6.0, "damage_max": 8.0}, "sound_cast": &"arcane_surge", "sound_hit": &"holy_strike", "vfx": &"arcane_surge"}),
		_s(&"shadow_curse", "Shadow Curse", &"mage", &"ground_aoe", {"element": Elements.DARK, "anim": &"cast_quick", "mana_cost": 10.0, "cooldown": 6.0,
			"description": "Curse all enemies in {radius} m: {damage_min}-{damage_max} Dark damage (drains life), and they take 15% more damage for {duration} s.",
			"params": {"damage_min": 6.0, "damage_max": 10.0, "radius": 4.0, "delay": 0.25, "range": 18.0, "curse": 100.0, "duration": 6.0, "knockback": 0.0, "poise": 4.0},
			"per_rank": {"damage_min": 2.0, "damage_max": 3.0, "radius": 0.2}, "sound_cast": &"dark_cast", "sound_hit": &"dark_curse", "vfx": &"curse"}),
		_s(&"radiant_ward", "Radiant Ward", &"mage", &"buff", {"element": Elements.LIGHT, "anim": &"cast_area", "mana_cost": 18.0, "cooldown": 15.0,
			"description": "Wrap yourself in light: a ward absorbing {absorb}% of Maximum HP for {duration} s and healing {heal}% of Maximum HP.",
			"params": {"duration": 8.0, "absorb": 30.0, "heal": 15.0, "radius": 4.0},
			"per_rank": {"absorb": 4.0, "heal": 2.0}, "sound_cast": &"heal", "vfx": &"ward"}),
	] + DataSkillsExt.skills()

static func knight_tree() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"knight_skills"
	t.display_name = "Knight Skills"
	t.points_kind = &"skill"
	t.pages = [{"name": "Combat", "desc": "Weapon techniques and holy strikes."}, {"name": "Auras", "desc": "Toggle one aura at a time; it empowers you, your Tempos and your party."},
		{"name": "Disciplines", "desc": "Passive skills: always on."}]
	t.branches = [{"name": "Vanguard", "x": 1.0, "color": Color(0.85, 0.3, 0.25)}, {"name": "Bulwark", "x": 4.0, "color": Color(0.7, 0.72, 0.8)},
		{"name": "Earthshaker", "x": 7.0, "color": Color(0.8, 0.6, 0.3)},
		{"name": "Offensive Auras", "x": 1.0, "color": Color(1.0, 0.55, 0.3), "page": 1}, {"name": "Defensive Auras", "x": 5.0, "color": Color(0.55, 0.78, 1.0), "page": 1},
		{"name": "Arms", "x": 1.0, "color": Color(0.9, 0.4, 0.3), "page": 2}, {"name": "Oath", "x": 4.0, "color": Color(1.0, 0.85, 0.45), "page": 2},
		{"name": "Endurance", "x": 7.0, "color": Color(0.7, 0.72, 0.8), "page": 2}]
	t.nodes = [
		{"id": &"cleave", "name": "Cleave", "kind": "skill", "skill": &"cleave", "icon": ICON % "cleave", "pos": Vector2(1, 0), "max_rank": 5, "cost": 1, "requires": []},
		{"id": &"cleave_bleed", "name": "Rending Arc", "kind": "upgrade", "skill": &"cleave", "icon": ICON % "cleave", "pos": Vector2(0, 1), "max_rank": 1, "cost": 1,
			"requires": [&"cleave"], "req_level": 4, "params": {"bleed": 60.0}, "desc": "Cleave builds Bleeding (physical damage over time)."},
		{"id": &"cleave_wide", "name": "Great Arc", "kind": "upgrade", "skill": &"cleave", "icon": ICON % "cleave", "pos": Vector2(2, 1), "max_rank": 2, "cost": 1,
			"requires": [&"cleave"], "req_level": 3, "params": {"arc": 25.0, "range": 0.4}, "desc": "+25° arc and +0.4 m reach per rank."},
		{"id": &"whirlwind", "name": "Whirlwind", "kind": "skill", "skill": &"whirlwind", "icon": ICON % "whirlwind", "pos": Vector2(1, 2), "max_rank": 5, "cost": 1,
			"requires": [&"cleave_bleed", &"cleave_wide"], "req_level": 6},
		{"id": &"whirlwind_pull", "name": "Vortex", "kind": "upgrade", "skill": &"whirlwind", "icon": ICON % "whirlwind", "pos": Vector2(0, 3), "max_rank": 1, "cost": 2,
			"requires": [&"whirlwind"], "req_level": 10, "params": {"pull": 1.0}, "desc": "Whirlwind pulls nearby enemies inward instead of pushing them."},
		{"id": &"judgment", "name": "Judgment", "kind": "skill", "skill": &"judgment", "icon": ICON % "judgment", "pos": Vector2(1, 4), "max_rank": 5, "cost": 1,
			"requires": [&"whirlwind"], "req_level": 12},
		{"id": &"judgment_quake", "name": "Final Verdict", "kind": "upgrade", "skill": &"judgment", "icon": ICON % "judgment", "pos": Vector2(2, 5), "max_rank": 1, "cost": 2,
			"requires": [&"judgment"], "req_level": 16, "params": {"length": 4.0, "width": 1.0}, "desc": "Judgment's line is 4 m longer and 1 m wider."},
		{"id": &"shield_bash", "name": "Shield Bash", "kind": "skill", "skill": &"shield_bash", "icon": ICON % "shield_bash", "pos": Vector2(4, 0), "max_rank": 5, "cost": 1, "requires": [], "req_level": 2},
		{"id": &"bash_chain", "name": "Battering Ram", "kind": "upgrade", "skill": &"shield_bash", "icon": ICON % "shield_bash", "pos": Vector2(5, 1), "max_rank": 2, "cost": 1,
			"requires": [&"shield_bash"], "req_level": 5, "params": {"knockback": 4.0, "dash": 1.5}, "desc": "+4 knockback and +1.5 m charge per rank."},
		{"id": &"iron_bulwark", "name": "Iron Bulwark", "kind": "skill", "skill": &"iron_bulwark", "icon": ICON % "iron_bulwark", "pos": Vector2(4, 2), "max_rank": 5, "cost": 1,
			"requires": [&"shield_bash"], "req_level": 5},
		{"id": &"war_cry", "name": "War Cry", "kind": "skill", "skill": &"war_cry", "icon": ICON % "war_cry", "pos": Vector2(4, 4), "max_rank": 5, "cost": 1,
			"requires": [&"iron_bulwark"], "req_level": 9},
		{"id": &"war_cry_haste", "name": "Rallying Cry", "kind": "upgrade", "skill": &"war_cry", "icon": ICON % "war_cry", "pos": Vector2(5, 5), "max_rank": 1, "cost": 2,
			"requires": [&"war_cry"], "req_level": 14, "params": {"haste": 1.0}, "desc": "War Cry also grants Haste (15% more move and attack speed)."},
		{"id": &"leap_slam", "name": "Leap Slam", "kind": "skill", "skill": &"leap_slam", "icon": ICON % "leap_slam", "pos": Vector2(7, 0), "max_rank": 5, "cost": 1, "requires": [], "req_level": 3},
		{"id": &"leap_launch", "name": "Skybreaker", "kind": "upgrade", "skill": &"leap_slam", "icon": ICON % "leap_slam", "pos": Vector2(8, 1), "max_rank": 2, "cost": 1,
			"requires": [&"leap_slam"], "req_level": 6, "params": {"launch": 3.0, "radius": 0.6}, "desc": "Enemies are launched higher; +0.6 m radius per rank."},
		{"id": &"ground_fissure", "name": "Ground Fissure", "kind": "skill", "skill": &"ground_fissure", "icon": ICON % "ground_fissure", "pos": Vector2(7, 2), "max_rank": 5, "cost": 1,
			"requires": [&"leap_slam"], "req_level": 7},
		{"id": &"fissure_twin", "name": "Twin Faults", "kind": "upgrade", "skill": &"ground_fissure", "icon": ICON % "ground_fissure", "pos": Vector2(8, 3), "max_rank": 1, "cost": 2,
			"requires": [&"ground_fissure"], "req_level": 12, "params": {"count": 2.0}, "desc": "Fissure splits into three diverging lines."},
	] + DataSkillsExt.knight_nodes()
	# Diablo II style synergies on the original skills
	_syn(t, &"cleave", [[&"arms_mastery", 4.0]])
	_syn(t, &"whirlwind", [[&"arms_mastery", 4.0], [&"zeal", 3.0]])
	_syn(t, &"judgment", [[&"aura_might", 6.0], [&"crusader_resolve", 5.0]])
	_syn(t, &"shield_bash", [[&"shield_mastery", 6.0]])
	_syn(t, &"ground_fissure", [[&"leap_slam", 5.0]])
	return t

static func _syn(t: TreeDef, id: StringName, syn: Array) -> void:
	for n in t.nodes:
		if n.id == id:
			n["synergies"] = syn

static func mage_tree() -> TreeDef:
	var t := TreeDef.new()
	t.id = &"mage_skills"
	t.display_name = "Mage Skills"
	t.points_kind = &"skill"
	t.pages = [{"name": "Spells", "desc": "The eight elements."}, {"name": "Mastery", "desc": "Passive skills: always on."}, {"name": "Gravity & Dark Arts", "desc": "Pulls, stuns, curses and Mana drain."}]
	t.branches = [{"name": "Pyre & Storm", "x": 1.0, "color": Color(1.0, 0.5, 0.2)}, {"name": "Frost & Tide", "x": 4.0, "color": Color(0.45, 0.8, 1.0)},
		{"name": "Arcana", "x": 7.0, "color": Color(0.7, 0.5, 1.0)},
		{"name": "Fire & Storm", "x": 1.0, "color": Color(1.0, 0.5, 0.2), "page": 1}, {"name": "Frost & Tide", "x": 4.0, "color": Color(0.45, 0.8, 1.0), "page": 1},
		{"name": "Mind", "x": 7.0, "color": Color(0.7, 0.5, 1.0), "page": 1}]
	t.nodes = [
		{"id": &"firebolt", "name": "Firebolt", "kind": "skill", "skill": &"firebolt", "icon": ICON % "firebolt", "pos": Vector2(1, 0), "max_rank": 5, "cost": 1, "requires": []},
		{"id": &"firebolt_explode", "name": "Combustion", "kind": "upgrade", "skill": &"firebolt", "icon": ICON % "firebolt", "pos": Vector2(0, 1), "max_rank": 1, "cost": 1,
			"requires": [&"firebolt"], "req_level": 3, "params": {"explode_radius": 2.2}, "desc": "Firebolt explodes on impact (2.2 m)."},
		{"id": &"chain_lightning", "name": "Chain Lightning", "kind": "skill", "skill": &"chain_lightning", "icon": ICON % "chain_lightning", "pos": Vector2(2, 1), "max_rank": 5, "cost": 1,
			"requires": [&"firebolt"], "req_level": 3},
		{"id": &"chain_fork", "name": "Forked Storm", "kind": "upgrade", "skill": &"chain_lightning", "icon": ICON % "chain_lightning", "pos": Vector2(2, 2), "max_rank": 2, "cost": 1,
			"requires": [&"chain_lightning"], "req_level": 7, "params": {"chains": 2.0}, "desc": "+2 chains per rank."},
		{"id": &"meteor", "name": "Meteor", "kind": "skill", "skill": &"meteor", "icon": ICON % "meteor", "pos": Vector2(0, 3), "max_rank": 5, "cost": 1,
			"requires": [&"firebolt_explode"], "req_level": 10},
		{"id": &"meteor_shower", "name": "Starfall", "kind": "upgrade", "skill": &"meteor", "icon": ICON % "meteor", "pos": Vector2(0, 5), "max_rank": 1, "cost": 2,
			"requires": [&"meteor"], "req_level": 16, "params": {"extra_meteors": 2.0}, "desc": "Two smaller meteors strike around the target."},
		{"id": &"frost_nova", "name": "Frost Nova", "kind": "skill", "skill": &"frost_nova", "icon": ICON % "frost_nova", "pos": Vector2(4, 0), "max_rank": 5, "cost": 1, "requires": [], "req_level": 2},
		{"id": &"nova_shatter", "name": "Deep Freeze", "kind": "upgrade", "skill": &"frost_nova", "icon": ICON % "frost_nova", "pos": Vector2(5, 1), "max_rank": 2, "cost": 1,
			"requires": [&"frost_nova"], "req_level": 5, "params": {"chill_direct": 25.0, "radius": 0.5}, "desc": "More Chill buildup and +0.5 m radius per rank."},
		{"id": &"tidal_wave", "name": "Tidal Wave", "kind": "skill", "skill": &"tidal_wave", "icon": ICON % "tidal_wave", "pos": Vector2(4, 2), "max_rank": 5, "cost": 1,
			"requires": [&"frost_nova"], "req_level": 5},
		{"id": &"wave_undertow", "name": "Undertow", "kind": "upgrade", "skill": &"tidal_wave", "icon": ICON % "tidal_wave", "pos": Vector2(3, 3), "max_rank": 1, "cost": 2,
			"requires": [&"tidal_wave"], "req_level": 10, "params": {"width": 1.5, "length": 3.0}, "desc": "The wave is 1.5 m wider and travels 3 m further."},
		{"id": &"stone_spear", "name": "Stone Spear", "kind": "skill", "skill": &"stone_spear", "icon": ICON % "stone_spear", "pos": Vector2(4, 4), "max_rank": 5, "cost": 1,
			"requires": [&"tidal_wave"], "req_level": 9},
		{"id": &"blink", "name": "Blink", "kind": "skill", "skill": &"blink", "icon": ICON % "blink", "pos": Vector2(7, 0), "max_rank": 5, "cost": 1, "requires": [], "req_level": 2},
		{"id": &"gale_burst", "name": "Gale Burst", "kind": "skill", "skill": &"gale_burst", "icon": ICON % "gale_burst", "pos": Vector2(8, 1), "max_rank": 5, "cost": 1,
			"requires": [&"blink"], "req_level": 4},
		{"id": &"shadow_curse", "name": "Shadow Curse", "kind": "skill", "skill": &"shadow_curse", "icon": ICON % "shadow_curse", "pos": Vector2(6, 2), "max_rank": 5, "cost": 1,
			"requires": [&"blink"], "req_level": 6},
		{"id": &"radiant_ward", "name": "Radiant Ward", "kind": "skill", "skill": &"radiant_ward", "icon": ICON % "radiant_ward", "pos": Vector2(8, 3), "max_rank": 5, "cost": 1,
			"requires": [&"gale_burst"], "req_level": 8},
		{"id": &"arcane_surge", "name": "Arcane Surge", "kind": "skill", "skill": &"arcane_surge", "icon": ICON % "arcane_surge", "pos": Vector2(7, 4), "max_rank": 5, "cost": 1,
			"requires": [&"shadow_curse", &"radiant_ward"], "req_level": 12},
		{"id": &"surge_overload", "name": "Singularity", "kind": "upgrade", "skill": &"arcane_surge", "icon": ICON % "arcane_surge", "pos": Vector2(7, 5), "max_rank": 1, "cost": 2,
			"requires": [&"arcane_surge"], "req_level": 16, "params": {"pull": 1.0, "radius": 1.5}, "desc": "Arcane Surge pulls enemies in before detonating; +1.5 m radius."},
	] + DataSkillsExt.mage_nodes()
	_syn(t, &"firebolt", [[&"meteor", 6.0], [&"flame_sentinel", 4.0]])
	_syn(t, &"meteor", [[&"firebolt", 6.0]])
	_syn(t, &"frost_nova", [[&"blizzard", 5.0]])
	_syn(t, &"chain_lightning", [[&"gale_burst", 5.0]])
	return t
