class_name DataTempos
## Tempos: spirits of warriors who died fighting the monsters of Jre, bound to a living hero by the Tempo-Caller
## (docs/LORE.md §9). Classes, skills, personality traits, the name pool and the tuning numbers live here; the rules
## are in TempoRules, the fighting spirit in the Tempo actor.

const MAX_ACTIVE := 2                  # a living heart carries two ghosts at most
const MIRROR := 0.5                    # a Tempo's strength is half its hero's
const ROSTER_SIZE := 4                 # spirits answering the Tempo-Caller at once
const ROSTER_REFRESH := 600.0          # seconds of play time before new spirits answer
const SPIRIT_TINT := Color(0.62, 0.95, 1.0)

## Class shells. `weapons` = main-hand weapon types; `sub` = what the sub hand may hold (a category or weapon types);
## `spirit_weapon` = the weapon type of the ghostly blade a Tempo fights with when its hands are empty.
const CLASSES := {
	&"swordsman": {
		"name": "Swordsman", "role": "Vanguard", "model": "res://assets/characters/knight.glb", "tint": Color(0.36, 0.55, 0.72),
		"color": Color(0.55, 0.78, 1.0), "icon": "swordsman",
		"desc": "Holds the line in front of you. Draws the monsters' attention, cleaves crowds and charges down whatever threatens you.",
		"weapons": [&"sword", &"axe", &"greatsword", &"spear"], "sub": [&"shield", &"sword", &"axe"], "spirit_weapon": &"sword",
		"preferred_range": 1.6, "hp_mult": 1.0, "dodge_cooldown": 2.4,
		"mods": [["max_hp", "inc", 0.15], ["defense", "inc", 0.25], ["knockback_res", "flat", 0.1], ["poise", "inc", 0.3]],
		"skills": [&"sw_cleave", &"sw_challenge", &"sw_charge", &"sw_mend"], "signature": &"sw_cleave",
	},
	&"archer": {
		"name": "Archer", "role": "Marksman", "model": "res://assets/characters/mage.glb", "tint": Color(0.3, 0.55, 0.4),
		"color": Color(0.6, 1.0, 0.7), "icon": "archer",
		"desc": "Keeps its distance and its aim. Pierces lines of foes, rains arrows on crowds and falls back when anything gets too close.",
		"weapons": [&"bow"], "sub": [], "spirit_weapon": &"bow",
		"preferred_range": 9.0, "hp_mult": 0.9, "dodge_cooldown": 1.8,
		"mods": [["projectile_damage", "inc", 0.15], ["crit_chance", "flat", 0.03], ["evasion", "inc", 0.15]],
		"skills": [&"ar_pierce", &"ar_volley", &"ar_mend", &"ar_disengage"], "signature": &"ar_pierce",
	},
	&"thief": {
		"name": "Thief", "role": "Shadow", "model": "res://assets/characters/mage.glb", "tint": Color(0.22, 0.2, 0.3),
		"color": Color(0.82, 0.62, 1.0), "icon": "thief",
		"desc": "Fights from the blind side. Steps through shadow behind whatever attacks you, poisons its blades and vanishes in smoke when cornered.",
		"weapons": [&"dagger"], "sub": [&"dagger"], "spirit_weapon": &"dagger",
		"preferred_range": 1.3, "hp_mult": 0.85, "dodge_cooldown": 1.3,
		"mods": [["crit_chance", "flat", 0.06], ["evasion", "inc", 0.3], ["crit_damage", "flat", 0.15]],
		"skills": [&"th_shadowstep", &"th_venom", &"th_smoke", &"th_remedy"], "signature": &"th_shadowstep",
	},
}

## Skills. kind: strike (melee damage), shot (ranged damage), area, heal, buff, escape, control.
## mana/cooldown are fixed costs; `mult` scales the Tempo's weapon damage; heals are fractions of the target's max HP.
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
}

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
	return [&"swordsman", &"archer", &"thief"]

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
		t = UIArt.icon("classes", "knight" if id == &"swordsman" else "mage")
	return t
