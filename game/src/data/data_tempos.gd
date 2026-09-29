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
## bh-022: as a hero grows, greater dead answer the Shrine of the Fallen. From level 25 the Mythic spirits replace the
## Renowned (at the shrine and in 5-star summons), from level 45 the Eternal replace the Mythic. Each tier carries more
## of its hero's strength, a stronger ghost weapon, a skill no one else knows, and a far higher price. Spirits already
## bound keep walking with the hero whatever tier answers now.
const RENOWNED_TIERS := [
	{"name": "Renowned", "level": 1, "mirror": 0.75, "color": Color(1.0, 0.72, 0.32),
		"desc": "Warriors whose names are still sung."},
	{"name": "Mythic", "level": 25, "mirror": 0.85, "color": Color(1.0, 0.46, 0.34),
		"desc": "Heroes of the old wars, whose deeds became songs and the songs became oaths."},
	{"name": "Eternal", "level": 45, "mirror": 0.95, "color": Color(0.74, 0.62, 1.0),
		"desc": "The first dead of Jre, who never let go of the world. They answer only the greatest heroes."},
]

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
		"weapons": [&"bow", &"crossbow", &"javelin"], "sub": [], "spirit_weapon": &"bow",
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
	# ---- bh-022: the Mythic spirits' own skills (level 25+)
	&"lg_rampart": {"name": "The Last Rampart", "class": &"warden", "kind": "buff", "use": "ward", "unique": &"branthor", "mana": 22.0, "cooldown": 24.0,
		"range": 14.0, "shield": 0.42, "duration": 10.0, "all": true, "taunt": 10.0, "anim": &"war_cry", "icon": "iron_bulwark",
		"desc": "Branthor plants himself like a wall: you and every Tempo near him are warded for 42% of maximum HP for 10 s, and every monster within 10 m turns on him."},
	&"lg_rimecleave": {"name": "Rimecleave", "class": &"swordsman", "kind": "strike", "use": "cleave", "unique": &"ysmera", "mana": 16.0, "cooldown": 8.0,
		"range": 3.4, "arc": 170.0, "mult": 2.6, "element": Elements.ICE, "status": {&"chilled": 140.0}, "knockback": 7.0, "poise": 45.0,
		"anim": &"special_attack", "icon": "blizzard",
		"desc": "A frost-white arc that splits the air in front of Ysmera: 2.6 times weapon damage as Ice, and chill that freezes whole packs."},
	&"lg_astral_lance": {"name": "Astral Lance", "class": &"mystic", "kind": "shot", "use": "bolt", "unique": &"aldevar", "mana": 14.0, "cooldown": 6.0,
		"range": 22.0, "mult": 3.2, "speed": 34.0, "element": Elements.LIGHT, "status": {&"purged": 120.0}, "knockback": 6.0, "poise": 30.0,
		"anim": &"cast_heavy", "icon": "heavens_fist",
		"desc": "A spear of starlight: 3.2 times spell damage as Light, and the target's healing and wards are burned away."},
	&"lg_galestorm": {"name": "Galestorm Volley", "class": &"archer", "kind": "area", "use": "volley", "unique": &"sabeline", "mana": 20.0, "cooldown": 12.0,
		"range": 20.0, "radius": 5.0, "mult": 0.95, "waves": 7, "element": Elements.WIND, "status": {&"windswept": 90.0}, "knockback": 5.0,
		"poise": 14.0, "anim": &"bow_release", "icon": "arrow_rain", "color": Color(0.62, 0.95, 0.66),
		"desc": "Seven waves of arrows riding a gale: every monster under them is torn and thrown about."},
	&"lg_thousand_cuts": {"name": "A Thousand Cuts", "class": &"thief", "kind": "strike", "use": "shadowstep", "unique": &"mireth", "mana": 15.0, "cooldown": 9.0,
		"range": 16.0, "mult": 2.8, "crit_bonus": 0.5, "execute": 0.5, "execute_mult": 2.8, "reset_on_kill": true,
		"status": {&"bleeding": 110.0}, "knockback": 3.0, "poise": 35.0, "anim": &"dagger_heavy", "icon": "death_blossom",
		"desc": "Mireth is behind a monster before it sees her: 2.8 times damage, far more below half health, and every kill readies the next cut."},
	&"lg_gravewall": {"name": "Gravewall", "class": &"warden", "kind": "area", "use": "nova", "unique": &"thraxen", "mana": 17.0, "cooldown": 12.0,
		"radius": 5.5, "mult": 1.9, "element": Elements.EARTH, "status": {&"armor_broken": 120.0}, "knockback": 10.0, "poise": 60.0,
		"anim": &"leap_slam", "keep_anim": true, "icon": "ground_fissure", "color": Color(0.8, 0.66, 0.42),
		"desc": "Thraxen brings a barrow's weight down around him: everything within 5.5 m is crushed and its armor broken."},
	&"lg_thousand_blades": {"name": "Thousand-Blade Dance", "class": &"swordsman", "kind": "strike", "use": "chain", "unique": &"caelith", "mana": 16.0, "cooldown": 9.0,
		"range": 11.0, "mult": 1.9, "jumps": 6, "falloff": 0.9, "dash": true, "status": {&"bleeding": 90.0}, "knockback": 4.0,
		"anim": &"special_attack", "icon": "blade_sentinel",
		"desc": "Caelith flickers from monster to monster, seven cuts in a breath, and every one bleeds."},
	&"lg_last_arrow": {"name": "The Last Arrow", "class": &"archer", "kind": "shot", "use": "pierce", "unique": &"wynter", "mana": 14.0, "cooldown": 7.0,
		"range": 26.0, "mult": 3.4, "pierce": 6, "element": Elements.ICE, "status": {&"chilled": 130.0}, "knockback": 6.0, "poise": 30.0,
		"anim": &"bow_release", "icon": "frost_arrow",
		"desc": "The arrow Wynter saved for the end: it passes through six monsters, freezing each one."},
	&"lg_laughing_knife": {"name": "Laughing Knives", "class": &"thief", "kind": "area", "use": "nova", "unique": &"sable", "mana": 13.0, "cooldown": 8.0,
		"radius": 4.6, "mult": 1.6, "status": {&"bleeding": 120.0}, "knockback": 3.0, "poise": 14.0, "anim": &"dual_3", "icon": "fan_of_knives",
		"color": Color(0.9, 0.5, 0.62),
		"desc": "A storm of thrown knives and a laugh no one forgets: every monster around Sable is cut and bleeds hard."},
	&"lg_stormhymn": {"name": "Stormhymn", "class": &"mystic", "kind": "area", "use": "chain", "unique": &"orrin", "mana": 17.0, "cooldown": 9.0,
		"range": 18.0, "mult": 1.9, "jumps": 7, "falloff": 0.9, "element": Elements.LIGHTNING, "status": {&"shocked": 110.0},
		"anim": &"cast_heavy", "icon": "chain_lightning",
		"desc": "Orrin sings and the sky answers: lightning leaps through eight monsters, shocking every one."},
	# ---- bh-022: the Eternal spirits' own skills (level 45+)
	&"lg_mountain": {"name": "The Mountain Walks", "class": &"warden", "kind": "area", "use": "nova", "unique": &"gorran", "mana": 20.0, "cooldown": 11.0,
		"radius": 7.0, "mult": 2.8, "element": Elements.EARTH, "status": {&"armor_broken": 160.0}, "knockback": 14.0, "poise": 90.0,
		"anim": &"leap_slam", "keep_anim": true, "icon": "ground_fissure", "color": Color(0.85, 0.7, 0.45),
		"desc": "Gorran strides and the ground breaks for 7 m around him: 2.8 times weapon damage as Earth, and no armor survives it."},
	&"lg_sunsworn": {"name": "Sunsworn Judgment", "class": &"swordsman", "kind": "strike", "use": "cleave", "unique": &"aurelis", "mana": 18.0, "cooldown": 8.0,
		"range": 4.0, "arc": 200.0, "mult": 3.4, "element": Elements.LIGHT, "status": {&"purged": 160.0}, "execute": 0.3, "execute_mult": 2.0,
		"knockback": 9.0, "poise": 60.0, "anim": &"special_attack", "icon": "judgment",
		"desc": "A blade of noon light swept in a wide ring: 3.4 times weapon damage as Light, doubled against the badly hurt."},
	&"lg_tidecall": {"name": "Tidecall", "class": &"mystic", "kind": "heal", "unique": &"ilyra", "mana": 24.0, "cooldown": 14.0, "range": 14.0,
		"heal": 0.45, "regen": 0.12, "radius": 14.0, "cleanse": true, "anim": &"cast_area", "icon": "tidal_wave",
		"desc": "The moon-tide rises around Ilyra: you and every ally within 14 m are healed 45% of maximum HP, more over 4 s, and cleansed."},
	&"lg_skyburner": {"name": "Skyburner", "class": &"archer", "kind": "area", "use": "volley", "unique": &"kaedric", "mana": 22.0, "cooldown": 11.0,
		"range": 22.0, "radius": 5.6, "mult": 1.2, "waves": 8, "element": Elements.FIRE, "status": {&"burning": 140.0}, "knockback": 3.0,
		"poise": 16.0, "anim": &"bow_release", "icon": "meteor", "color": Color(1.0, 0.5, 0.18),
		"desc": "Eight waves of arrows that fall like burning stars over a wide field."},
	&"lg_unseen_crown": {"name": "The Unseen Crown", "class": &"thief", "kind": "strike", "use": "shadowstep", "unique": &"veyl", "mana": 16.0, "cooldown": 8.0,
		"range": 18.0, "mult": 3.6, "crit_bonus": 0.6, "execute": 0.5, "execute_mult": 3.0, "reset_on_kill": true,
		"status": {&"cursed": 150.0}, "knockback": 4.0, "poise": 45.0, "anim": &"dagger_heavy", "icon": "shadow_step",
		"desc": "Veyl wears the dark like a crown: 3.6 times damage from behind, triple below half health, and every kill readies the next."},
	&"lg_unfallen": {"name": "Unfallen", "class": &"warden", "kind": "buff", "use": "ward", "unique": &"bramwold", "mana": 22.0, "cooldown": 22.0,
		"range": 14.0, "shield": 0.5, "duration": 10.0, "all": true, "taunt": 12.0, "anim": &"war_cry", "icon": "oathbound",
		"desc": "Bramwold's heart never stopped: you and every Tempo near him are warded for half of maximum HP, and every monster within 12 m turns on him."},
	&"lg_dawnheir": {"name": "Dawnbreakers' Oath", "class": &"swordsman", "kind": "strike", "use": "chain", "unique": &"estrid", "mana": 18.0, "cooldown": 8.0,
		"range": 12.0, "mult": 2.4, "jumps": 7, "falloff": 0.92, "dash": true, "element": Elements.FIRE, "status": {&"burning": 130.0},
		"knockback": 5.0, "anim": &"special_attack", "icon": "aura_cinders",
		"desc": "Estrid carries the Dawnbreakers' fire: she dashes through eight monsters and sets every one of them burning."},
	&"lg_comet": {"name": "Comet Shot", "class": &"archer", "kind": "shot", "use": "pierce", "unique": &"quillon", "mana": 16.0, "cooldown": 6.0,
		"range": 30.0, "mult": 4.2, "pierce": 8, "element": Elements.LIGHT, "status": {&"purged": 140.0}, "knockback": 8.0, "poise": 40.0,
		"anim": &"bow_release", "icon": "power_shot",
		"desc": "An arrow with a comet's tail: 4.2 times damage through eight monsters in a line."},
	&"lg_whisper": {"name": "Whisper of Knives", "class": &"thief", "kind": "area", "use": "nova", "unique": &"mourne", "mana": 15.0, "cooldown": 7.0,
		"radius": 5.2, "mult": 2.2, "element": Elements.DARK, "status": {&"cursed": 140.0}, "knockback": 3.0, "poise": 20.0, "anim": &"dual_3",
		"icon": "dread_mark", "color": Color(0.66, 0.4, 0.95),
		"desc": "A hush, then knives from nowhere: every monster within 5 m is cut as Dark and cursed."},
	&"lg_worldsong": {"name": "Worldsong", "class": &"mystic", "kind": "area", "use": "nova", "unique": &"ethra", "mana": 20.0, "cooldown": 10.0,
		"radius": 7.0, "mult": 2.5, "element": Elements.LIGHT, "status": {&"purged": 160.0}, "knockback": 8.0, "poise": 30.0,
		"anim": &"cast_ultimate", "icon": "judgment", "color": Color(0.85, 0.8, 1.0),
		"desc": "Ethra sings the song the world was made with: a burst of light 7 m wide that unmakes wards and healing."},
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

## bh-012: five more renowned spirits who answer only a summoning at the shrine (TempoGacha, 5-star). They fight with
## the class skills of their kind, a stronger ghost weapon and gifts of their own. Names invented for Jre.
const SUMMON_LEGENDS := {
	&"durek": {"name": "Durek Hollowmere", "title": "the Anvil", "class": &"warden", "trait": &"cautious", "level": 1, "price": 0,
		"skills": [&"wd_bash", &"wd_aegis", &"wd_quake", &"wd_oath"], "tint": Color(0.55, 0.46, 0.36), "kit": [&"warden_kite_shield"],
		"spirit": {"weapon": &"club", "element": Elements.EARTH, "share": 0.4, "power": 1.4},
		"mods": [["max_hp", "inc", 0.3], ["knockback_res", "flat", 0.15], ["defense", "inc", 0.2]], "summon_only": true,
		"origin": "A forge-lord's shield-bearer who stood in the Emberforge gate while the lava rose. It rose over him and he did not move.",
		"pitch": "An unmovable wall that shakes the ground under every pack."},
	&"seraphine": {"name": "Seraphine Ardel", "title": "the Dawnspear", "class": &"swordsman", "trait": &"valiant", "level": 1, "price": 0,
		"skills": [&"sw_charge", &"sw_cleave", &"sw_whirl", &"sw_rally"], "tint": Color(0.85, 0.78, 0.5),
		"spirit": {"weapon": &"spear", "element": Elements.LIGHT, "share": 0.5, "power": 1.45},
		"mods": [["crit_chance", "flat", 0.05], ["attack_speed", "more", 0.08]], "summon_only": true,
		"origin": "Led the last charge down the Watch Road before Wyman Outpost had a stockade. The road is named for the ones who watched her go.",
		"pitch": "A charging lance of light: rallies you and cuts whole lines apart."},
	&"talwyn": {"name": "Talwyn Rookshade", "title": "the Grey Fletch", "class": &"archer", "trait": &"swift", "level": 1, "price": 0,
		"skills": [&"ar_pierce", &"ar_frost", &"ar_volley", &"ar_trap"], "tint": Color(0.45, 0.52, 0.6),
		"spirit": {"weapon": &"bow", "element": Elements.ICE, "share": 0.5, "power": 1.45},
		"mods": [["projectile_damage", "inc", 0.25], ["evasion", "inc", 0.2]], "summon_only": true,
		"origin": "Held the Rimeglass stair alone with a quiver of frost-tipped arrows until the barrow door closed behind the last of her company.",
		"pitch": "Freezes packs in place, then pins them there."},
	&"nyssa": {"name": "Nyssa Kaldor", "title": "the Silent Knife", "class": &"thief", "trait": &"vengeful", "level": 1, "price": 0,
		"skills": [&"th_shadowstep", &"th_venom", &"th_fan", &"th_finish"], "tint": Color(0.22, 0.3, 0.22),
		"spirit": {"weapon": &"dagger", "element": Elements.EARTH, "share": 0.35, "power": 1.5},
		"mods": [["crit_damage", "flat", 0.35], ["crit_chance", "flat", 0.05]], "summon_only": true,
		"origin": "Poisoned a whole war-camp of the Ashen Circle in one night, then walked back into their fire to be sure.",
		"pitch": "Poison, then the quiet finish. Nothing wounded lives long near her."},
	&"eldric": {"name": "Eldric Sunmarrow", "title": "the Starweaver", "class": &"mystic", "trait": &"devoted", "level": 1, "price": 0,
		"skills": [&"my_bolt", &"my_chain", &"my_nova", &"my_mend"], "tint": Color(0.5, 0.45, 0.85),
		"spirit": {"weapon": &"staff", "element": Elements.LIGHTNING, "share": 1.0, "power": 1.45},
		"mods": [["elemental_damage", "inc", 0.25], ["max_mana", "inc", 0.25]], "summon_only": true,
		"origin": "The last Aether-watcher to leave the Orrery. He did not leave by the door.",
		"pitch": "Storms that leap from foe to foe, and a mend when you need it."},
}

## bh-022: the Mythic renowned (level 25+). They replace the five of the shrine once a hero reaches level 25.
const MYTHIC_LEGENDS := {
	&"branthor": {"name": "Branthor Veyle", "title": "the Last Rampart", "class": &"warden", "trait": &"cautious", "level": 25, "price": 45000, "tier": 1,
		"skills": [&"wd_bash", &"lg_rampart", &"wd_quake", &"wd_oath", &"wd_mend"], "tint": Color(0.5, 0.52, 0.58), "kit": [&"warden_kite_shield"],
		"spirit": {"weapon": &"club", "element": Elements.EARTH, "share": 0.45, "power": 1.7},
		"mods": [["max_hp", "inc", 0.4], ["block_chance", "flat", 0.15], ["defense", "inc", 0.3], ["knockback_res", "flat", 0.2]],
		"origin": "Held the breach at Harrowmere for a winter and a day while the whole north walked south behind him. The breach closed with him in it.",
		"pitch": "A wall that shields the whole party and holds every monster's eye."},
	&"ysmera": {"name": "Ysmera Coldbrand", "title": "the Frostblade", "class": &"swordsman", "trait": &"valiant", "level": 27, "price": 60000, "tier": 1,
		"skills": [&"sw_cleave", &"lg_rimecleave", &"sw_charge", &"sw_whirl", &"sw_mend"], "tint": Color(0.55, 0.72, 0.88), "kit": [],
		"spirit": {"weapon": &"greatsword", "element": Elements.ICE, "share": 0.55, "power": 1.7},
		"mods": [["attack_speed", "more", 0.14], ["crit_chance", "flat", 0.06], ["crit_damage", "flat", 0.3]],
		"origin": "Walked into the Rimeglass barrows with a blade forged in their own cold, and froze the thing at their heart where it stood.",
		"pitch": "Freezes whole packs with every swing, then shatters them."},
	&"aldevar": {"name": "Aldevar Quennt", "title": "the Starwarden", "class": &"mystic", "trait": &"devoted", "level": 29, "price": 75000, "tier": 1,
		"skills": [&"my_bolt", &"lg_astral_lance", &"my_mend", &"my_ward", &"my_chain"], "tint": Color(0.55, 0.52, 0.85), "kit": [],
		"spirit": {"weapon": &"staff", "element": Elements.LIGHT, "share": 1.0, "power": 1.7},
		"mods": [["healing", "inc", 0.35], ["max_mana", "inc", 0.3], ["elemental_damage", "inc", 0.25]],
		"origin": "Kept the Orrery's great lens turned on the sky for forty years, and read in it the night the dead would rise. No one listened until he stood alone at its door.",
		"pitch": "Lances of starlight, storms that leap between foes, and a mend for the whole party."},
	&"sabeline": {"name": "Sabeline Harrowgale", "title": "the Windpiercer", "class": &"archer", "trait": &"swift", "level": 31, "price": 90000, "tier": 1,
		"skills": [&"ar_pierce", &"lg_galestorm", &"ar_volley", &"ar_trap", &"ar_mend"], "tint": Color(0.46, 0.62, 0.5), "kit": [],
		"spirit": {"weapon": &"bow", "element": Elements.WIND, "share": 0.55, "power": 1.75},
		"mods": [["projectile_damage", "inc", 0.3], ["crit_damage", "flat", 0.35], ["evasion", "inc", 0.25]],
		"origin": "Shot the Gigas of Stormcrag through the eye from the far side of a gale. The wind has carried her name ever since.",
		"pitch": "Storms of arrows that scatter whole war-hosts."},
	&"mireth": {"name": "Mireth Dusk", "title": "the Velvet Death", "class": &"thief", "trait": &"vengeful", "level": 33, "price": 110000, "tier": 1,
		"skills": [&"th_shadowstep", &"lg_thousand_cuts", &"th_venom", &"th_fan", &"th_smoke"], "tint": Color(0.3, 0.16, 0.26), "kit": [],
		"spirit": {"weapon": &"dagger", "element": Elements.DARK, "share": 0.45, "power": 1.75},
		"mods": [["crit_chance", "flat", 0.08], ["crit_damage", "flat", 0.4], ["attack_speed", "more", 0.1]],
		"origin": "Danced at the Tyrant-king's feast, and he was dead before the music stopped. So were his seven captains.",
		"pitch": "Kills the strongest monster in reach, then the next, then the next."},
}

## bh-022: the Eternal renowned (level 45+). They replace the Mythic once a hero reaches level 45.
const ETERNAL_LEGENDS := {
	&"gorran": {"name": "Gorran Stoneveil", "title": "the Mountain That Walks", "class": &"warden", "trait": &"cautious", "level": 45, "price": 180000, "tier": 2,
		"skills": [&"wd_bash", &"lg_mountain", &"wd_aegis", &"wd_oath", &"wd_mend"], "tint": Color(0.52, 0.46, 0.38), "kit": [&"warden_kite_shield"],
		"spirit": {"weapon": &"club", "element": Elements.EARTH, "share": 0.55, "power": 1.95},
		"mods": [["max_hp", "inc", 0.55], ["block_chance", "flat", 0.2], ["defense", "inc", 0.45], ["knockback_res", "flat", 0.3]],
		"origin": "Before the towns, before the roads, a giant of a man stood between the first hearth and the dark. The hill behind Malasugue is said to be his shadow.",
		"pitch": "The ground breaks where he walks. Nothing reaches you past him."},
	&"aurelis": {"name": "Aurelis Dawnmantle", "title": "the Sunsworn", "class": &"swordsman", "trait": &"valiant", "level": 47, "price": 240000, "tier": 2,
		"skills": [&"sw_cleave", &"lg_sunsworn", &"sw_charge", &"sw_whirl", &"sw_rally"], "tint": Color(0.9, 0.78, 0.45), "kit": [],
		"spirit": {"weapon": &"greatsword", "element": Elements.LIGHT, "share": 0.6, "power": 2.0},
		"mods": [["attack_speed", "more", 0.18], ["crit_chance", "flat", 0.08], ["crit_damage", "flat", 0.45], ["outgoing_damage", "more", 0.1]],
		"origin": "Swore to the sun on the first morning of the world that no night would last forever. Every dawn since has been hers.",
		"pitch": "Rings of noon light that end fights before they begin."},
	&"ilyra": {"name": "Ilyra Moonwhisper", "title": "the Tidecaller", "class": &"mystic", "trait": &"devoted", "level": 49, "price": 300000, "tier": 2,
		"skills": [&"my_chain", &"lg_tidecall", &"my_bolt", &"my_ward", &"my_nova"], "tint": Color(0.42, 0.6, 0.82), "kit": [],
		"spirit": {"weapon": &"staff", "element": Elements.WATER, "share": 1.0, "power": 2.0},
		"mods": [["healing", "inc", 0.5], ["max_mana", "inc", 0.4], ["elemental_damage", "inc", 0.35]],
		"origin": "Called the sea up over the drowned kingdom so its dead would sleep. She still hears them in every tide.",
		"pitch": "Heals the whole party at once, and the tide takes what she points at."},
	&"kaedric": {"name": "Kaedric Emberline", "title": "the Skyburner", "class": &"archer", "trait": &"vengeful", "level": 51, "price": 380000, "tier": 2,
		"skills": [&"ar_pierce", &"lg_skyburner", &"ar_volley", &"ar_trap", &"ar_mend"], "tint": Color(0.7, 0.36, 0.2), "kit": [],
		"spirit": {"weapon": &"crossbow", "element": Elements.FIRE, "share": 0.6, "power": 2.0},
		"mods": [["projectile_damage", "inc", 0.4], ["crit_damage", "flat", 0.5], ["crit_chance", "flat", 0.06]],
		"origin": "Set the sky itself alight to turn back the dragon-flight over Emberhal. The clouds there still glow at night.",
		"pitch": "Rains fire over whole fields; bosses melt under it."},
	&"veyl": {"name": "Veyl Ashenmourn", "title": "the Unseen Crown", "class": &"thief", "trait": &"valiant", "level": 53, "price": 450000, "tier": 2,
		"skills": [&"th_shadowstep", &"lg_unseen_crown", &"th_finish", &"th_fan", &"th_remedy"], "tint": Color(0.16, 0.12, 0.22), "kit": [],
		"spirit": {"weapon": &"dagger", "element": Elements.DARK, "share": 0.5, "power": 2.05},
		"mods": [["crit_chance", "flat", 0.1], ["crit_damage", "flat", 0.55], ["attack_speed", "more", 0.14]],
		"origin": "Wore a crown no one could see and ruled the night roads of Jre for a hundred years. The Ashen Circle still will not say the name.",
		"pitch": "The deadliest spirit ever called. Nothing hurt survives near him."},
}

## bh-022: the Mythic and Eternal who answer only a summoning (5-star), each with a skill of its own.
const MYTHIC_SUMMON := {
	&"thraxen": {"name": "Thraxen Oldbarrow", "title": "the Gravewall", "class": &"warden", "trait": &"cautious", "level": 1, "price": 0, "tier": 1,
		"skills": [&"wd_bash", &"lg_gravewall", &"wd_aegis", &"wd_oath"], "tint": Color(0.42, 0.44, 0.4), "kit": [&"warden_kite_shield"],
		"spirit": {"weapon": &"club", "element": Elements.EARTH, "share": 0.5, "power": 1.7},
		"mods": [["max_hp", "inc", 0.45], ["defense", "inc", 0.3], ["knockback_res", "flat", 0.2]], "summon_only": true,
		"origin": "Buried himself in the barrow door so the dead inside could not follow the living out.",
		"pitch": "Crushes packs flat and breaks their armor."},
	&"caelith": {"name": "Caelith Varr", "title": "the Thousand-Blade", "class": &"swordsman", "trait": &"swift", "level": 1, "price": 0, "tier": 1,
		"skills": [&"sw_cleave", &"lg_thousand_blades", &"sw_whirl", &"sw_rally"], "tint": Color(0.62, 0.6, 0.66),
		"spirit": {"weapon": &"sword", "element": Elements.WIND, "share": 0.5, "power": 1.7},
		"mods": [["attack_speed", "more", 0.16], ["crit_chance", "flat", 0.06]], "summon_only": true,
		"origin": "Fought the orc war-host alone at the Bell Pass and was seen in seven places at once.",
		"pitch": "Seven cuts in a breath, all of them bleeding."},
	&"wynter": {"name": "Wynter Ashfeather", "title": "the Last Arrow", "class": &"archer", "trait": &"vengeful", "level": 1, "price": 0, "tier": 1,
		"skills": [&"ar_pierce", &"lg_last_arrow", &"ar_frost", &"ar_volley"], "tint": Color(0.58, 0.64, 0.72),
		"spirit": {"weapon": &"bow", "element": Elements.ICE, "share": 0.55, "power": 1.75},
		"mods": [["projectile_damage", "inc", 0.32], ["crit_damage", "flat", 0.3]], "summon_only": true,
		"origin": "Kept one arrow for forty years for the thing that burned her village. She found it.",
		"pitch": "One arrow through a whole line of monsters, frozen solid."},
	&"sable": {"name": "Sable Myrrow", "title": "the Laughing Knife", "class": &"thief", "trait": &"swift", "level": 1, "price": 0, "tier": 1,
		"skills": [&"th_shadowstep", &"lg_laughing_knife", &"th_venom", &"th_finish"], "tint": Color(0.4, 0.18, 0.24),
		"spirit": {"weapon": &"dagger", "element": Elements.DARK, "share": 0.45, "power": 1.75},
		"mods": [["crit_damage", "flat", 0.4], ["crit_chance", "flat", 0.07]], "summon_only": true,
		"origin": "Laughed at the headsman, at the king and at the dead. She is laughing still.",
		"pitch": "Knives in every direction, and everything bleeds."},
	&"orrin": {"name": "Orrin Galesong", "title": "the Stormhymn", "class": &"mystic", "trait": &"devoted", "level": 1, "price": 0, "tier": 1,
		"skills": [&"my_bolt", &"lg_stormhymn", &"my_mend", &"my_ward"], "tint": Color(0.46, 0.5, 0.86),
		"spirit": {"weapon": &"staff", "element": Elements.LIGHTNING, "share": 1.0, "power": 1.75},
		"mods": [["elemental_damage", "inc", 0.32], ["max_mana", "inc", 0.3]], "summon_only": true,
		"origin": "Sang on the cliffs of Corvessa until the storm he called drowned the fleet that came for them.",
		"pitch": "Lightning that leaps through whole packs."},
}
const ETERNAL_SUMMON := {
	&"bramwold": {"name": "Bramwold Ironheart", "title": "the Unfallen", "class": &"warden", "trait": &"cautious", "level": 1, "price": 0, "tier": 2,
		"skills": [&"wd_bash", &"lg_unfallen", &"wd_quake", &"wd_mend"], "tint": Color(0.44, 0.42, 0.46), "kit": [&"warden_kite_shield"],
		"spirit": {"weapon": &"club", "element": Elements.EARTH, "share": 0.55, "power": 1.95},
		"mods": [["max_hp", "inc", 0.6], ["defense", "inc", 0.4], ["block_chance", "flat", 0.15]], "summon_only": true,
		"origin": "Took a hundred wounds at the founding of Aubren and would not fall until the gate was hung.",
		"pitch": "Wards the whole party and never goes down."},
	&"estrid": {"name": "Estrid Flamecrown", "title": "the Dawnbreakers' Heir", "class": &"swordsman", "trait": &"valiant", "level": 1, "price": 0, "tier": 2,
		"skills": [&"sw_cleave", &"lg_dawnheir", &"sw_charge", &"sw_rally"], "tint": Color(0.82, 0.46, 0.28),
		"spirit": {"weapon": &"sword", "element": Elements.FIRE, "share": 0.6, "power": 2.0},
		"mods": [["attack_speed", "more", 0.16], ["crit_chance", "flat", 0.08], ["outgoing_damage", "more", 0.08]], "summon_only": true,
		"origin": "The first to wear the Dawnbreakers' crown of fire, long before the betrayal on the causeway.",
		"pitch": "Dashes through whole packs and leaves them burning."},
	&"quillon": {"name": "Quillon Starwatch", "title": "the Comet", "class": &"archer", "trait": &"swift", "level": 1, "price": 0, "tier": 2,
		"skills": [&"ar_pierce", &"lg_comet", &"ar_volley", &"ar_trap"], "tint": Color(0.72, 0.7, 0.5),
		"spirit": {"weapon": &"bow", "element": Elements.LIGHT, "share": 0.6, "power": 2.0},
		"mods": [["projectile_damage", "inc", 0.4], ["crit_chance", "flat", 0.06]], "summon_only": true,
		"origin": "Shot a falling star back into the sky, the old songs say, and it has not come down since.",
		"pitch": "Arrows that cross the whole field and everything in the way."},
	&"mourne": {"name": "Mourne Velvetshade", "title": "the Whisper of Knives", "class": &"thief", "trait": &"vengeful", "level": 1, "price": 0, "tier": 2,
		"skills": [&"th_shadowstep", &"lg_whisper", &"th_fan", &"th_finish"], "tint": Color(0.24, 0.16, 0.32),
		"spirit": {"weapon": &"dagger", "element": Elements.DARK, "share": 0.5, "power": 2.05},
		"mods": [["crit_damage", "flat", 0.5], ["crit_chance", "flat", 0.09]], "summon_only": true,
		"origin": "No one ever heard Mourne coming. The last thing anyone heard was a whisper.",
		"pitch": "Curses and cuts every monster around at once."},
	&"ethra": {"name": "Ethra Lumenveil", "title": "the Worldsinger", "class": &"mystic", "trait": &"devoted", "level": 1, "price": 0, "tier": 2,
		"skills": [&"my_chain", &"lg_worldsong", &"my_mend", &"my_ward"], "tint": Color(0.7, 0.66, 0.92),
		"spirit": {"weapon": &"staff", "element": Elements.LIGHT, "share": 1.0, "power": 2.0},
		"mods": [["elemental_damage", "inc", 0.4], ["max_mana", "inc", 0.4], ["healing", "inc", 0.3]], "summon_only": true,
		"origin": "Sang with the Aether before there were words for it. Some say she taught the waypoints to wake.",
		"pitch": "Light that unmakes everything around her, and a mend when you need it."},
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
	for table in [LEGENDS, SUMMON_LEGENDS, MYTHIC_LEGENDS, MYTHIC_SUMMON, ETERNAL_LEGENDS, ETERNAL_SUMMON]:
		if table.has(id):
			return table[id]
	return {}

## bh-022: which renowned tier answers a hero of `level` (0 Renowned, 1 Mythic, 2 Eternal).
static func renowned_tier_for(level: int) -> int:
	var t := 0
	for i in RENOWNED_TIERS.size():
		if level >= int(RENOWNED_TIERS[i].level):
			t = i
	return t

static func renowned_tier(tier: int) -> Dictionary:
	return RENOWNED_TIERS[clampi(tier, 0, RENOWNED_TIERS.size() - 1)]

## The tier of a renowned spirit (0 for the first ten).
static func legend_tier(id: StringName) -> int:
	return int(legend(id).get("tier", 0))

## Every renowned spirit a 5-star summon may bring to a hero of `level` (the shrine's five of that tier and the five
## of that tier who answer only a summoning). No level (-1): the first tier.
static func summon_legend_ids(level := -1) -> Array:
	match renowned_tier_for(level) if level >= 0 else 0:
		1: return legend_ids(level) + MYTHIC_SUMMON.keys()
		2: return legend_ids(level) + ETERNAL_SUMMON.keys()
	return legend_ids() + [&"durek", &"seraphine", &"talwyn", &"nyssa", &"eldric"]

## The five renowned spirits waiting at the shrine for a hero of `level` (no level: the first five).
static func legend_ids(level := -1) -> Array:
	match renowned_tier_for(level) if level >= 0 else 0:
		1: return MYTHIC_LEGENDS.keys()
		2: return ETERNAL_LEGENDS.keys()
	return [&"hollan", &"kavira", &"maudra", &"cindrel", &"vessik"]

## Every renowned spirit of every tier.
static func all_legend_ids() -> Array:
	var out: Array = []
	for table in [LEGENDS, SUMMON_LEGENDS, MYTHIC_LEGENDS, MYTHIC_SUMMON, ETERNAL_LEGENDS, ETERNAL_SUMMON]:
		out.append_array(table.keys())
	return out

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
