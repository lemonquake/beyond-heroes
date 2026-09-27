class_name DataTempos
## Tempos: spirits of warriors who died fighting the monsters of Jre, bound to a living hero by the Tempo-Caller
## (docs/LORE.md §9). Classes, skills, personality traits, the name pool and the tuning numbers live here; the rules
## are in TempoRules, the fighting spirit in the Tempo actor.

const MAX_ACTIVE := 2                  # a living heart carries two ghosts at most
const MIRROR := 0.5                    # a grade-1 Tempo's strength is half its hero's (see GRADES)
const ROSTER_SIZE := 4                 # spirits answering the Tempo-Caller at once
const ROSTER_REFRESH := 600.0          # seconds of play time before new spirits answer
const SPIRIT_TINT := Color(0.62, 0.95, 1.0)

## Grades of the spirits answering the Tempo-Caller. The strongest grade a hero has reached (by level, or by a deed —
## whichever comes first) is the grade of every spirit offered; when it rises, the weaker offers fade at once and
## stronger spirits take their place. `mirror` = share of the hero's strength, `extra` = [min, max] skills besides
## the signature, `price` = multiplier on the hire cost. Bound Tempos keep the grade they were bound at.
const GRADES := [
	{"name": "Restless", "mirror": 0.50, "extra": [1, 2], "price": 1.0, "level": 1, "flag": &"", "deed": "",
		"color": Color(0.62, 0.9, 1.0), "desc": "Newly dead and still angry. A signature skill and one or two more."},
	{"name": "Seasoned", "mirror": 0.55, "extra": [2, 2], "price": 1.6, "level": 4, "flag": &"", "deed": "",
		"color": Color(0.6, 1.0, 0.72), "desc": "Spirits that have walked with heroes before. Three skills; Mystics answer."},
	{"name": "Veteran", "mirror": 0.60, "extra": [2, 3], "price": 2.4, "level": 8, "flag": &"temple_seal_broken",
		"deed": "break the seal of the first oath", "color": Color(0.55, 0.75, 1.0),
		"desc": "Old soldiers of the Aether. Up to four skills, the rarer ones among them; Wardens answer."},
	{"name": "Exalted", "mirror": 0.65, "extra": [3, 3], "price": 3.5, "level": 12, "flag": &"boss_warden_defeated",
		"deed": "fell the Hollow Warden", "color": Color(0.8, 0.62, 1.0), "desc": "Spirits with a legend of their own. Four skills."},
	{"name": "Ascendant", "mirror": 0.70, "extra": [3, 4], "price": 5.0, "level": 20, "flag": &"", "deed": "",
		"color": Color(1.0, 0.82, 0.4), "desc": "The strongest of the nameless dead. Four or five skills."},
]
const RENOWNED := {"name": "Renowned", "mirror": 0.75, "color": Color(1.0, 0.72, 0.32)}

## Class shells. `weapons` = main-hand weapon types; `sub` = what the sub hand may hold (a category or weapon types);
## `spirit_weapon` = the weapon type of the ghostly blade a Tempo fights with when its hands are empty.
## `ai` = how it fights (vanguard: between the monster and the hero; shadow: flanks; marksman / caster: keeps range).
## `rig` = animation set of its model; `grade` = the lowest grade at which this class answers the Tempo-Caller.
const CLASSES := {
	&"swordsman": {
		"name": "Swordsman", "role": "Vanguard", "model": "res://assets/characters/knight.glb", "tint": Color(0.36, 0.55, 0.72),
		"color": Color(0.55, 0.78, 1.0), "icon": "swordsman", "ai": "vanguard", "rig": &"knight", "grade": 1,
		"desc": "Holds the line in front of you. Draws the monsters' attention, cleaves crowds and charges down whatever threatens you.",
		"weapons": [&"sword", &"axe", &"greatsword", &"greataxe", &"spear", &"club"], "sub": [&"shield", &"sword", &"axe", &"club"], "spirit_weapon": &"sword",
		"preferred_range": 1.6, "hp_mult": 1.0, "dodge_cooldown": 2.4,
		"mods": [["max_hp", "inc", 0.15], ["defense", "inc", 0.25], ["knockback_res", "flat", 0.1], ["poise", "inc", 0.3]],
		"skills": [&"sw_cleave", &"sw_challenge", &"sw_charge", &"sw_mend", &"sw_whirl", &"sw_rally"], "signature": &"sw_cleave",
	},
	&"archer": {
		"name": "Archer", "role": "Marksman", "model": "res://assets/characters/mage.glb", "tint": Color(0.3, 0.55, 0.4),
		"color": Color(0.6, 1.0, 0.7), "icon": "archer", "ai": "marksman", "rig": &"mage", "grade": 1,
		"desc": "Keeps its distance and its aim. Pierces lines of foes, rains arrows on crowds and falls back when anything gets too close.",
		"weapons": [&"bow", &"javelin"], "sub": [], "spirit_weapon": &"bow",
		"preferred_range": 9.0, "hp_mult": 0.9, "dodge_cooldown": 1.8,
		"mods": [["projectile_damage", "inc", 0.15], ["crit_chance", "flat", 0.03], ["evasion", "inc", 0.15]],
		"skills": [&"ar_pierce", &"ar_volley", &"ar_mend", &"ar_disengage", &"ar_frost", &"ar_trap"], "signature": &"ar_pierce",
	},
	&"thief": {
		"name": "Thief", "role": "Shadow", "model": "res://assets/characters/mage.glb", "tint": Color(0.22, 0.2, 0.3),
		"color": Color(0.82, 0.62, 1.0), "icon": "thief", "ai": "shadow", "rig": &"mage", "grade": 1,
		"desc": "Fights from the blind side. Steps through shadow behind whatever attacks you, poisons its blades and vanishes in smoke when cornered.",
		"weapons": [&"dagger", &"claw", &"knuckles"], "sub": [&"dagger", &"claw", &"knuckles"], "spirit_weapon": &"dagger",
		"preferred_range": 1.3, "hp_mult": 0.85, "dodge_cooldown": 1.3,
		"mods": [["crit_chance", "flat", 0.06], ["evasion", "inc", 0.3], ["crit_damage", "flat", 0.15]],
		"skills": [&"th_shadowstep", &"th_venom", &"th_smoke", &"th_remedy", &"th_fan", &"th_finish"], "signature": &"th_shadowstep",
	},
	&"mystic": {
		"name": "Mystic", "role": "Aether-Weaver", "model": "res://assets/characters/mage.glb", "tint": Color(0.34, 0.3, 0.62),
		"color": Color(0.74, 0.74, 1.0), "icon": "mystic", "ai": "caster", "rig": &"mage", "grade": 2,
		"desc": "Weaves loose Aether into bolts and wards. Keeps to the back, shields you from the worst blows and mends what gets through.",
		"weapons": [&"staff", &"wand"], "sub": [&"wand"], "spirit_weapon": &"staff",
		"preferred_range": 8.0, "hp_mult": 0.85, "dodge_cooldown": 2.0,
		"mods": [["elemental_damage", "inc", 0.2], ["max_mana", "inc", 0.3], ["healing", "inc", 0.1]],
		"skills": [&"my_bolt", &"my_ward", &"my_mend", &"my_chain", &"my_nova"], "signature": &"my_bolt",
	},
	&"warden": {
		"name": "Warden", "role": "Bulwark", "model": "res://assets/characters/knight.glb", "tint": Color(0.5, 0.46, 0.36),
		"color": Color(1.0, 0.86, 0.55), "icon": "warden", "ai": "vanguard", "rig": &"knight", "grade": 3,
		"desc": "A shield that died still standing. Takes the blows meant for you, wards you in a barrier and shakes the ground under packs.",
		"weapons": [&"sword", &"axe", &"spear", &"club", &"javelin"], "sub": [&"shield"], "spirit_weapon": &"sword",
		"preferred_range": 1.6, "hp_mult": 1.15, "dodge_cooldown": 3.0,
		"mods": [["max_hp", "inc", 0.3], ["defense", "inc", 0.4], ["knockback_res", "flat", 0.2], ["poise", "inc", 0.5]],
		"skills": [&"wd_bash", &"wd_oath", &"wd_aegis", &"wd_quake", &"wd_mend"], "signature": &"wd_bash",
	},
}

## Skills. kind: strike (melee damage), shot (ranged damage), area, heal, buff, escape, control.
## mana/cooldown are fixed costs; `mult` scales the Tempo's weapon damage; heals are fractions of the target's max HP.
## `use` = the Tempo actor's handler (defaults to the part of the id after the class prefix; heals always "heal");
## `grade` = lowest spirit grade that can know it (default 1); `unique` = a renowned spirit's own skill, never rolled.
## Optional effect keys: element (Elements.*, converts the hit), status ({status: buildup}), execute (HP fraction) +
## execute_mult, radius (group heal / nova / trap), statuses (rally), shield (ward: fraction of the ward-bearer's max HP).
const SKILLS := {
	# ---- Swordsman
	&"sw_cleave": {"name": "Vengeful Cleave", "class": &"swordsman", "kind": "strike", "mana": 8.0, "cooldown": 6.0, "range": 2.9,
		"arc": 190.0, "mult": 1.6, "knockback": 7.0, "poise": 30.0, "anim": &"sword_heavy", "icon": "cleave",
		"desc": "A wide, furious sweep that hits every monster in front of it."},
	&"sw_challenge": {"name": "Grave Challenge", "class": &"swordsman", "kind": "control", "mana": 12.0, "cooldown": 16.0, "range": 7.5,
		"duration": 5.0, "anim": &"war_cry", "icon": "war_cry",
		"desc": "Bellows at the monsters around it. They turn on the Tempo instead of you, and it takes 20% less damage for 5 s."},
	&"sw_charge": {"name": "Rending Charge", "class": &"swordsman", "kind": "strike", "mana": 9.0, "cooldown": 9.0, "range": 9.0, "min_range": 3.5,
		"width": 2.0, "mult": 1.3, "knockback": 9.0, "poise": 45.0, "anim": &"special_attack", "icon": "shield_bash",
		"desc": "Charges a distant monster, cutting through everything in the way and staggering it."},
	&"sw_mend": {"name": "Soul Mend", "class": &"swordsman", "kind": "heal", "mana": 16.0, "cooldown": 14.0, "range": 8.0,
		"heal": 0.2, "regen": 0.06, "anim": &"cast_quick", "icon": "radiant_ward",
		"desc": "Pours some of its own spirit into an ally: heals 20% of their maximum HP at once and more over 4 s."},
	&"sw_whirl": {"name": "Spectral Whirlwind", "class": &"swordsman", "kind": "area", "use": "nova", "grade": 3, "mana": 14.0, "cooldown": 11.0,
		"radius": 3.4, "mult": 1.3, "knockback": 6.0, "poise": 26.0, "anim": &"special_attack", "icon": "whirlwind", "color": Color(0.6, 0.95, 1.0),
		"desc": "Spins with its blade out and cuts every monster around it."},
	&"sw_rally": {"name": "Rally the Fallen", "class": &"swordsman", "kind": "buff", "use": "rally", "grade": 4, "mana": 18.0, "cooldown": 30.0,
		"radius": 12.0, "duration": 8.0, "statuses": [&"empowered"], "anim": &"war_cry", "icon": "war_cry",
		"desc": "A dead soldier's battle cry: you and your Tempos deal 20% more damage for 8 s."},
	# ---- Archer
	&"ar_pierce": {"name": "Piercing Arrow", "class": &"archer", "kind": "shot", "mana": 7.0, "cooldown": 5.0, "range": 20.0,
		"mult": 1.9, "pierce": 4, "knockback": 5.0, "poise": 20.0, "anim": &"bow_release", "icon": "stone_spear",
		"desc": "A spirit-charged arrow that passes through up to four monsters in a line."},
	&"ar_volley": {"name": "Rain of Ghost Arrows", "class": &"archer", "kind": "area", "mana": 13.0, "cooldown": 12.0, "range": 16.0,
		"radius": 3.4, "mult": 0.75, "waves": 3, "knockback": 1.5, "poise": 8.0, "anim": &"bow_release", "icon": "meteor",
		"desc": "Arrows fall on an area three times. Best against packs and slow giants."},
	&"ar_mend": {"name": "Mending Arrow", "class": &"archer", "kind": "heal", "mana": 15.0, "cooldown": 12.0, "range": 16.0,
		"heal": 0.18, "regen": 0.05, "anim": &"bow_release", "icon": "radiant_ward",
		"desc": "Looses an arrow of pale light at an ally: heals 18% of their maximum HP and more over 4 s. Never misses a friend."},
	&"ar_disengage": {"name": "Disengage", "class": &"archer", "kind": "escape", "mana": 6.0, "cooldown": 9.0, "range": 4.5,
		"leap": 6.5, "anim": &"dodge_roll", "icon": "blink",
		"desc": "Vaults away from a monster that got too close, leaving a snare that slows it."},
	&"ar_frost": {"name": "Rime Arrow", "class": &"archer", "kind": "shot", "use": "pierce", "grade": 2, "mana": 9.0, "cooldown": 8.0, "range": 20.0,
		"mult": 1.6, "pierce": 2, "element": Elements.ICE, "status": {&"chilled": 90.0}, "knockback": 3.0, "poise": 15.0,
		"anim": &"bow_release", "icon": "frost_nova",
		"desc": "An arrow of grave-cold. It chills everything it passes through; chill that builds up freezes."},
	&"ar_trap": {"name": "Thornsnare", "class": &"archer", "kind": "control", "use": "trap", "grade": 3, "mana": 12.0, "cooldown": 14.0,
		"range": 14.0, "radius": 2.6, "duration": 5.0, "mult": 0.3, "status_id": &"slowed", "anim": &"cast_quick", "icon": "ground_fissure",
		"color": Color(0.55, 0.95, 0.6),
		"desc": "Throws a snare of spirit-thorns under a pack: every monster in it is slowed and cut for 5 s."},
	# ---- Thief
	&"th_shadowstep": {"name": "Shadowstep", "class": &"thief", "kind": "strike", "mana": 10.0, "cooldown": 8.0, "range": 12.0,
		"mult": 2.2, "crit_bonus": 0.35, "knockback": 3.0, "poise": 25.0, "anim": &"dagger_heavy", "icon": "shadow_curse",
		"desc": "Steps through shadow behind a monster and drives both blades into its back."},
	&"th_venom": {"name": "Venom Blades", "class": &"thief", "kind": "buff", "mana": 9.0, "cooldown": 14.0, "range": 2.2,
		"duration": 8.0, "mult": 0.65, "hits": 3, "anim": &"dual_3", "icon": "firebolt",
		"desc": "A flurry of three poisoned cuts; for 8 s every strike poisons."},
	&"th_smoke": {"name": "Smoke Bomb", "class": &"thief", "kind": "escape", "mana": 10.0, "cooldown": 16.0, "range": 4.5,
		"radius": 4.0, "duration": 3.0, "anim": &"cast_quick", "icon": "gale_burst",
		"desc": "Vanishes in black smoke: nearby monsters are slowed and weakened, and the Tempo slips away unseen."},
	&"th_remedy": {"name": "Stolen Remedy", "class": &"thief", "kind": "heal", "mana": 13.0, "cooldown": 13.0, "range": 9.0,
		"heal": 0.15, "regen": 0.05, "cleanse": true, "anim": &"cast_quick", "icon": "radiant_ward",
		"desc": "Tosses an ally a draught lifted from someone who did not need it: heals 15%, more over 4 s, and cures poison and bleeding."},
	&"th_fan": {"name": "Fan of Knives", "class": &"thief", "kind": "area", "use": "nova", "grade": 2, "mana": 11.0, "cooldown": 10.0,
		"radius": 3.6, "mult": 0.9, "status": {&"bleeding": 70.0}, "knockback": 2.0, "poise": 8.0, "anim": &"dual_3", "icon": "whirlwind",
		"color": Color(0.82, 0.62, 1.0),
		"desc": "Throws a ring of ghost-knives. Every monster around it is cut and bleeds."},
	&"th_finish": {"name": "Final Cut", "class": &"thief", "kind": "strike", "use": "cleave", "grade": 4, "mana": 12.0, "cooldown": 9.0,
		"range": 2.4, "arc": 70.0, "mult": 1.4, "execute": 0.35, "execute_mult": 2.5, "crit_bonus": 0.2, "knockback": 3.0, "poise": 20.0,
		"anim": &"dagger_heavy", "icon": "shadow_curse",
		"desc": "A killing stroke: 2.5 times the damage against a monster below 35% health."},
	# ---- Mystic
	&"my_bolt": {"name": "Aether Bolt", "class": &"mystic", "kind": "shot", "use": "bolt", "grade": 2, "mana": 7.0, "cooldown": 4.0, "range": 18.0,
		"mult": 1.7, "element": Elements.LIGHT, "status": {&"purged": 40.0}, "speed": 26.0, "knockback": 3.0, "poise": 12.0,
		"anim": &"cast_quick", "icon": "arcane_surge",
		"desc": "A bolt of pale Aether that purges a monster's healing and wards."},
	&"my_ward": {"name": "Soul Ward", "class": &"mystic", "kind": "buff", "use": "ward", "grade": 2, "mana": 14.0, "cooldown": 18.0, "range": 12.0,
		"shield": 0.18, "duration": 8.0, "anim": &"cast_heavy", "icon": "radiant_ward",
		"desc": "Wraps you in a barrier that absorbs damage equal to 18% of your maximum HP for 8 s."},
	&"my_mend": {"name": "Aether Mend", "class": &"mystic", "kind": "heal", "grade": 2, "mana": 18.0, "cooldown": 14.0, "range": 12.0,
		"heal": 0.18, "regen": 0.06, "radius": 6.0, "anim": &"cast_area", "icon": "radiant_ward",
		"desc": "Mends you and every ally within 6 m: 18% of maximum HP at once and more over 4 s."},
	&"my_chain": {"name": "Arc of Storms", "class": &"mystic", "kind": "area", "use": "chain", "grade": 3, "mana": 15.0, "cooldown": 10.0,
		"range": 16.0, "mult": 1.3, "jumps": 4, "falloff": 0.85, "element": Elements.LIGHTNING, "status": {&"shocked": 60.0},
		"anim": &"cast_heavy", "icon": "chain_lightning",
		"desc": "Lightning that leaps from monster to monster, up to five of them, shocking each one."},
	&"my_nova": {"name": "Grave-Frost Nova", "class": &"mystic", "kind": "area", "use": "nova", "grade": 4, "mana": 17.0, "cooldown": 14.0,
		"radius": 4.2, "mult": 1.2, "element": Elements.ICE, "status": {&"chilled": 120.0}, "knockback": 5.0, "poise": 18.0,
		"anim": &"cast_area", "icon": "frost_nova", "color": Color(0.6, 0.9, 1.0),
		"desc": "A burst of grave-cold around the Mystic: every monster near it is chilled, and chill that builds up freezes."},
	# ---- Warden
	&"wd_bash": {"name": "Shield Crush", "class": &"warden", "kind": "strike", "use": "cleave", "grade": 3, "mana": 8.0, "cooldown": 6.0,
		"range": 2.6, "arc": 90.0, "mult": 1.5, "knockback": 9.0, "poise": 50.0, "status": {&"armor_broken": 60.0},
		"anim": &"shield_bash", "keep_anim": true, "icon": "shield_bash",
		"desc": "Drives its shield into a monster: heavy stagger, and its armor starts to crack."},
	&"wd_oath": {"name": "Iron Oath", "class": &"warden", "kind": "control", "use": "challenge", "grade": 3, "mana": 12.0, "cooldown": 15.0,
		"range": 9.0, "duration": 6.0, "anim": &"taunt", "icon": "iron_bulwark",
		"desc": "Swears to hold. Every monster within 9 m turns on the Warden, which takes 20% less damage for 6 s."},
	&"wd_aegis": {"name": "Guardian's Aegis", "class": &"warden", "kind": "buff", "use": "ward", "grade": 3, "mana": 14.0, "cooldown": 20.0,
		"range": 10.0, "shield": 0.22, "duration": 8.0, "anim": &"war_cry", "icon": "iron_bulwark",
		"desc": "Raises a ghostly shield over you that absorbs damage equal to 22% of your maximum HP for 8 s."},
	&"wd_quake": {"name": "Earthshaker", "class": &"warden", "kind": "area", "use": "nova", "grade": 3, "mana": 15.0, "cooldown": 13.0,
		"radius": 4.4, "mult": 1.1, "element": Elements.EARTH, "status": {&"armor_broken": 70.0}, "knockback": 8.0, "poise": 40.0,
		"anim": &"leap_slam", "keep_anim": true, "icon": "ground_fissure", "color": Color(0.9, 0.72, 0.4),
		"desc": "Slams the ground: every monster within 4 m is staggered and has its armor broken."},
	&"wd_mend": {"name": "Oathbound Mend", "class": &"warden", "kind": "heal", "grade": 3, "mana": 16.0, "cooldown": 15.0, "range": 8.0,
		"heal": 0.22, "regen": 0.05, "anim": &"cast_quick", "icon": "radiant_ward",
		"desc": "Keeps its oath to you: heals 22% of your maximum HP at once and more over 4 s."},
	# ---- Renowned spirits' own skills (never rolled for a nameless spirit)
	&"lg_bastion": {"name": "Unbroken Bastion", "class": &"warden", "kind": "buff", "use": "ward", "unique": &"hollan", "mana": 20.0, "cooldown": 26.0,
		"range": 12.0, "shield": 0.3, "duration": 8.0, "all": true, "taunt": 8.0, "anim": &"war_cry", "icon": "iron_bulwark",
		"desc": "Hollan's last stand at the Aubren gate: wards you and every Tempo near him (30% of maximum HP) and draws every monster within 8 m onto himself."},
	&"lg_stormbreak": {"name": "Stormbreak", "class": &"swordsman", "kind": "strike", "use": "chain", "unique": &"kavira", "mana": 16.0, "cooldown": 10.0,
		"range": 10.0, "mult": 1.6, "jumps": 5, "falloff": 0.88, "dash": true, "element": Elements.LIGHTNING, "status": {&"shocked": 80.0},
		"anim": &"special_attack", "icon": "chain_lightning",
		"desc": "Kavira rides the lightning into a monster and it arcs on through five more, shocking every one."},
	&"lg_sanctuary": {"name": "Lantern of Sanctuary", "class": &"mystic", "kind": "heal", "unique": &"maudra", "mana": 22.0, "cooldown": 16.0, "range": 12.0,
		"heal": 0.3, "regen": 0.08, "radius": 10.0, "cleanse": true, "anim": &"cast_area", "icon": "radiant_ward",
		"desc": "Maudra lifts her lantern: you and every ally within 10 m are healed 30% of maximum HP, more over 4 s, and cured of poison, bleeding and burning."},
	&"lg_dawn": {"name": "Radiant Dawn", "class": &"mystic", "kind": "area", "use": "nova", "unique": &"maudra", "mana": 16.0, "cooldown": 12.0,
		"radius": 5.0, "mult": 1.4, "element": Elements.LIGHT, "status": {&"purged": 90.0}, "knockback": 6.0, "poise": 20.0,
		"anim": &"cast_ultimate", "icon": "judgment", "color": Color(1.0, 0.95, 0.7),
		"desc": "A burst of lantern-light around Maudra. The dead and the cursed burn in it."},
	&"lg_cinderfall": {"name": "Cinderfall", "class": &"archer", "kind": "area", "use": "volley", "unique": &"cindrel", "mana": 18.0, "cooldown": 13.0,
		"range": 18.0, "radius": 4.2, "mult": 0.85, "waves": 5, "element": Elements.FIRE, "status": {&"burning": 70.0}, "knockback": 2.0,
		"poise": 10.0, "anim": &"bow_release", "icon": "meteor", "color": Color(1.0, 0.55, 0.2),
		"desc": "The volley that brought down a Tyrant: five waves of burning arrows over a wide area."},
	&"lg_nightfall": {"name": "Nightfall", "class": &"thief", "kind": "strike", "use": "shadowstep", "unique": &"vessik", "mana": 14.0, "cooldown": 11.0,
		"range": 14.0, "mult": 2.0, "crit_bonus": 0.4, "execute": 0.4, "execute_mult": 2.5, "reset_on_kill": true,
		"status": {&"cursed": 70.0}, "knockback": 3.0, "poise": 30.0, "anim": &"dagger_heavy", "icon": "shadow_curse",
		"desc": "Vessik steps out of the dark behind a monster and curses it. Deals 2.5 times the damage below 40% health, and if it kills, he is ready to strike again at once."},
}

## The five renowned spirits: warriors whose names are still sung. Each answers only a hero of their level, costs a
## small fortune, fights with more of its hero's strength (RENOWNED.mirror) and carries skills no one else has. They
## wait at the Shrine of the Fallen until bound; a released one returns there. `spirit` = the ghost weapon it
## carries instead of common steel ({weapon, element, share, power}); `kit` = real gear it arrives with.
const LEGENDS := {
	&"hollan": {"name": "Hollan Greywall", "title": "the Unbroken", "class": &"warden", "trait": &"cautious", "level": 5, "price": 1500,
		"skills": [&"wd_bash", &"lg_bastion", &"wd_quake", &"wd_mend"], "tint": Color(0.58, 0.55, 0.46), "kit": [&"warden_kite_shield"],
		"spirit": {"weapon": &"sword", "element": Elements.EARTH, "share": 0.3, "power": 1.35},
		"mods": [["max_hp", "inc", 0.25], ["block_chance", "flat", 0.1]],
		"origin": "Held the Registry gate at Aubren for three days against an orc war-host. The gate still bears the print of his shield.",
		"pitch": "Nothing gets past him to you. Nothing ever has."},
	&"kavira": {"name": "Kavira Vane", "title": "the Storm-Sworn", "class": &"swordsman", "trait": &"swift", "level": 8, "price": 3000,
		"skills": [&"sw_cleave", &"lg_stormbreak", &"sw_charge", &"sw_mend"], "tint": Color(0.42, 0.5, 0.8), "kit": [],
		"spirit": {"weapon": &"sword", "element": Elements.LIGHTNING, "share": 0.5, "power": 1.4},
		"mods": [["attack_speed", "more", 0.1], ["crit_chance", "flat", 0.04]],
		"origin": "A Corvessa duelist who called lightning down her own blade when something vast rose under her ship. The storm took them both.",
		"pitch": "Lightning in a sword-arm. She clears whole packs in one breath."},
	&"maudra": {"name": "Maudra Vell", "title": "the Lantern Saint", "class": &"mystic", "trait": &"devoted", "level": 11, "price": 5000,
		"skills": [&"my_bolt", &"lg_sanctuary", &"my_ward", &"lg_dawn"], "tint": Color(0.7, 0.62, 0.4), "kit": [],
		"spirit": {"weapon": &"staff", "element": Elements.LIGHT, "share": 1.0, "power": 1.4},
		"mods": [["healing", "inc", 0.25], ["max_mana", "inc", 0.2]],
		"origin": "Walked into the Catacombs with a lantern to bring out the forest garrison's wounded. She brought out eleven, and went back for the twelfth.",
		"pitch": "The finest healer the Shrine has ever called. Keeps a whole party standing."},
	&"cindrel": {"name": "Cindrel Ashreed", "title": "the Tyrant's Bane", "class": &"archer", "trait": &"vengeful", "level": 14, "price": 8000,
		"skills": [&"ar_pierce", &"lg_cinderfall", &"ar_trap", &"ar_mend"], "tint": Color(0.62, 0.34, 0.2), "kit": [],
		"spirit": {"weapon": &"bow", "element": Elements.FIRE, "share": 0.5, "power": 1.45},
		"mods": [["projectile_damage", "inc", 0.2], ["crit_damage", "flat", 0.25]],
		"origin": "Tracked a Tyrant across the cane fields of Emberhal for forty days and put an arrow through its eye before its fire found her.",
		"pitch": "Burns down anything big. Built for bosses and raids."},
	&"vessik": {"name": "Vessik Thorn", "title": "the Quiet End", "class": &"thief", "trait": &"valiant", "level": 18, "price": 12000,
		"skills": [&"th_shadowstep", &"lg_nightfall", &"th_venom", &"th_smoke", &"th_remedy"], "tint": Color(0.18, 0.14, 0.24), "kit": [],
		"spirit": {"weapon": &"dagger", "element": Elements.DARK, "share": 0.4, "power": 1.5},
		"mods": [["crit_chance", "flat", 0.06], ["crit_damage", "flat", 0.3]],
		"origin": "The Ashen Circle burned him on their altar for the names he would not give. He still has not given them.",
		"pitch": "Kills the wounded before they know he is there, then does it again."},
}

## The spirit that comes through the waypoint with every new hero: a town guard who died holding the Sanctuary
## Terrace so the townsfolk could reach the hearth wards. A plain grade-1 Swordsman with a mend.
const STARTER := {"name": "Tobren", "class": &"swordsman", "trait": &"devoted", "skills": [&"sw_cleave", &"sw_mend"],
	"tint": Color(0.36, 0.56, 0.74), "portrait": "tempo_tobren",
	"origin": "Fell on the Sanctuary Terrace holding the waypoint shrine while the townsfolk ran for the hearth wards."}

## Personality: how bravely it fights and what it is good at. retreat = HP fraction at which it falls back to heal.
const TRAITS := {
	&"valiant": {"name": "Valiant", "retreat": 0.22, "heal_at": 0.5, "desc": "Fights on when others would fall back. +8% damage.",
		"mods": [["outgoing_damage", "more", 0.08]]},
	&"cautious": {"name": "Cautious", "retreat": 0.45, "heal_at": 0.55, "desc": "Falls back early and lives to fight again. +15% Defense.",
		"mods": [["defense", "inc", 0.15]]},
	&"devoted": {"name": "Devoted", "retreat": 0.3, "heal_at": 0.7, "desc": "Never strays far from you and mends you sooner. +10% healing.",
		"mods": [["healing", "inc", 0.1]]},
	&"vengeful": {"name": "Vengeful", "retreat": 0.3, "heal_at": 0.5, "desc": "Hunts the wounded without mercy. +5% critical chance.",
		"mods": [["crit_chance", "flat", 0.05]]},
	&"swift": {"name": "Swift", "retreat": 0.35, "heal_at": 0.55, "desc": "Quick on its feet: 10% more attack speed, dodges more often.",
		"mods": [["attack_speed", "more", 0.1]]},
}

## Where they fell. Shown on the Tempo sheet; every spirit carries its death with it.
const ORIGINS := [
	"Fell with the forest garrison the night the village burned.",
	"Fell on the black sand of Emberhal, holding the line against the orc war-host.",
	"Drowned off the Corvessa reefs when something vast turned beneath the ship.",
	"Fell guarding the Registry gate at Aubren.",
	"Burned in a Tyrant's fire on the cane fields of Emberhal.",
	"Crushed beneath an ogre's club on the north road.",
	"Cut down by orc raiders while covering a caravan's escape.",
	"Lost in the Catacombs, and never stopped looking for the way out.",
	"Fell defending a fishing cove from the dead.",
	"Struck down by goblin fire-pots in a burning granary.",
	"Torn apart by dire wolves hunting in threes.",
	"Fell to the Hollow Warden's marching dead.",
	"Burned on an Ashen Circle altar for refusing to kneel.",
	"Followed the drowned bells into the sea and did not come back.",
	"Fell at the waypoint shrine, buying time for the townsfolk to flee.",
	"Died in the shadow of a Gigas that walked where a hill had been.",
	"Ambushed by shade stalkers on a moonless road.",
	"Fell to a ghoul brute in the winter the grave-moss grew.",
]

## 100 names, all invented for Jre (LORE §8: no names borrowed from real cultures or languages).
const NAMES := [
	"Arvenn", "Belisse", "Caedro", "Dunmar", "Eskarra", "Falder", "Garrow", "Hesmae", "Ivrenne", "Jorvell",
	"Kestran", "Lysmere", "Mordrin", "Nerevan", "Oswyth", "Pellam", "Quessa", "Rhovan", "Sarevin", "Tholl",
	"Ulvessa", "Varrick", "Wystrel", "Xandrel", "Yorvane", "Zelkin", "Ashryn", "Brenmor", "Calwen", "Draymund",
	"Emberlyn", "Fennor", "Galwyn", "Harrik", "Iolan", "Jessivar", "Korran", "Lathe", "Merrin", "Nyvette",
	"Orsolin", "Pelloran", "Quennic", "Rusk", "Selvarre", "Tamsk", "Ultren", "Vaskir", "Wendrik", "Yselle",
	"Zorvath", "Aubrec", "Bastrel", "Corvane", "Delmira", "Estrane", "Fayreth", "Gorvan", "Halcyne", "Irvaine",
	"Jaskel", "Kyrra", "Lodric", "Maurel", "Nesker", "Olvenna", "Prael", "Rovenne", "Sterran", "Tavric",
	"Ursel", "Veskar", "Wyldren", "Yarrowe", "Zaphine", "Arkell", "Brisane", "Cedrys", "Dorrin", "Evarran",
	"Florenne", "Grisk", "Hessik", "Ilvarro", "Jhoren", "Kalder", "Lirien", "Morvane", "Nalric", "Oskeld",
	"Pyrrel", "Rennick", "Saelith", "Thorne", "Umbrel", "Vesmarra", "Wrenna", "Yveric", "Zeverin", "Caskell",
]

static func tempo_class(id: StringName) -> Dictionary:
	return CLASSES.get(id, {})

static func skill(id: StringName) -> Dictionary:
	return SKILLS.get(id, {})

static func trait_def(id: StringName) -> Dictionary:
	return TRAITS.get(id, {})

static func class_ids() -> Array:
	return [&"swordsman", &"archer", &"thief", &"mystic", &"warden"]

## Classes that answer the Tempo-Caller at `grade` (in class_ids order).
static func classes_for_grade(grade: int) -> Array:
	return class_ids().filter(func(c): return int(tempo_class(c).get("grade", 1)) <= grade)

## Grade table entry (1..GRADES.size()).
static func grade_def(grade: int) -> Dictionary:
	return GRADES[clampi(grade, 1, GRADES.size()) - 1]

static func max_grade() -> int:
	return GRADES.size()

static func legend(id: StringName) -> Dictionary:
	return LEGENDS.get(id, {})

static func legend_ids() -> Array:
	return [&"hollan", &"kavira", &"maudra", &"cindrel", &"vessik"]

## The Tempo actor's handler for a skill (see SKILLS).
static func skill_use(id: StringName) -> String:
	var sk := skill(id)
	if sk.has("use"):
		return String(sk.use)
	if String(sk.get("kind", "")) == "heal":
		return "heal"
	return String(id).get_slice("_", 1)

static func skill_grade(id: StringName) -> int:
	return int(skill(id).get("grade", 1))

static func is_unique(id: StringName) -> bool:
	return skill(id).has("unique")

## Skills a nameless spirit of `class_id` may roll at `grade` besides its signature.
static func rollable_skills(class_id: StringName, grade: int) -> Array:
	var td := tempo_class(class_id)
	return (td.get("skills", []) as Array).filter(func(s): return s != td.signature and not is_unique(s) and skill_grade(s) <= grade)

static func is_heal(skill_id: StringName) -> bool:
	return String(skill(skill_id).get("kind", "")) == "heal"

## Stat modifiers from a [stat, op, value] table.
static func mods_from(table: Array, source: String) -> Array:
	var out := []
	for m in table:
		match String(m[1]):
			"flat": out.append(StatModifier.flat(StringName(m[0]), float(m[2]), source))
			"inc": out.append(StatModifier.inc(StringName(m[0]), float(m[2]), source))
			"more": out.append(StatModifier.more(StringName(m[0]), float(m[2]), source))
	return out

## Skill icon: a dedicated Tempo icon when one exists, else the kin skill icon it is drawn from.
static func skill_icon(id: StringName) -> Texture2D:
	var t := UIArt.icon("skills", "tempo_%s" % id)
	if t == null:
		t = UIArt.icon("skills", String(skill(id).get("icon", "cleave")))
	return t

static func class_icon(id: StringName) -> Texture2D:
	var t := UIArt.icon("classes", "tempo_%s" % id)
	if t == null:
		t = UIArt.icon("classes", String(tempo_class(id).get("rig", &"knight")))
	return t

## Portrait of a renowned spirit or the starter Tempo ("" = none; the UI falls back to the class crest).
static func portrait_path(key: String) -> String:
	var p := "res://assets/ui/portraits/%s.svg" % key
	return p if ResourceLoader.exists(p) else ""
