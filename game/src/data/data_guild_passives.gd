class_name DataGuildPassives
## bh-027: what a guild of the hero's own can buy. Founding, member slots, the guild's level (renown), its passives and
## Guild War passives, the traits adventurers bring, and the Guildmaster's active skill, Call to Arms.
##
## Guild passives help every member all the time. Guild War passives grow with the number of guild members fighting
## beside you (Call to Arms fighters, and in multiplayer every guildmate on the same map) — made for a lot of members at
## once. Ranks cost gold and need a guild level (GuildRules / OwnGuild read this table).

const FOUND_FEE := 1000
const BASE_SLOTS := 6
## [slots after the upgrade, gold]
const SLOT_UPGRADES := [[9, 10000], [12, 15000], [15, 25000]]
const MAX_SLOTS := 15

const LEVEL_CAP := 20
## Renown to climb from level L to L + 1.
static func renown_for_level(level: int) -> float:
	return round(120.0 * pow(float(maxi(level, 1)), 1.35))

## Guild War passives count at most this many comrades.
const WAR_CAP := 12
const WAR_RANGE := 30.0

## Call to Arms: fighters stay 15 minutes; the call can be made again 30 minutes after it was made.
const SUMMON_DURATION := 900.0
const SUMMON_COOLDOWN := 1800.0
const SUMMON_MAX_RANK := 6
## Gold to reach rank index + 2 (rank 1 comes with the guild).
const SUMMON_COSTS := [3000, 7000, 12000, 20000, 32000]
## Guild level needed for rank index + 2.
const SUMMON_LEVELS := [3, 6, 9, 12, 15]

## Recruitment: an adventurer applies roughly every RECRUIT_BASE seconds of play while a slot is free.
const RECRUIT_BASE := 210.0
const RECRUIT_FIRST := 40.0
## Share of the hero's level below it that recruits may be (level 20 -> 13..20).
const RECRUIT_SPREAD := 0.35

## id -> {name, kind ("guild" | "war" | "special"), stat, op ("inc" | "flat"), per (value per rank; per comrade for war),
## max, cost (gold for rank 1; rank r costs cost * r^1.5), text (with {v} for the value at the next rank)}
const PASSIVES := {
	&"sharpened_steel": {"name": "Sharpened Steel", "kind": "guild", "stat": &"damage", "op": "inc", "per": 0.02, "max": 5, "cost": 1200,
		"icon": "attributes/strength", "text": "{v} Damage for every member."},
	&"iron_discipline": {"name": "Iron Discipline", "kind": "guild", "stat": &"max_hp", "op": "inc", "per": 0.025, "max": 5, "cost": 1200,
		"icon": "attributes/spirit", "text": "{v} Maximum HP for every member."},
	&"war_chest": {"name": "War Chest", "kind": "guild", "stat": &"gold_find", "op": "inc", "per": 0.04, "max": 5, "cost": 900,
		"icon": "ui/gold", "text": "{v} Gold Find, and members' tithes are {t} larger."},
	&"scholars_hall": {"name": "Scholars' Hall", "kind": "guild", "stat": &"xp_gain", "op": "inc", "per": 0.03, "max": 5, "cost": 1500,
		"icon": "ui/xp", "text": "{v} Experience gained by every member."},
	&"swift_banners": {"name": "Swift Banners", "kind": "guild", "stat": &"move_speed", "op": "inc", "per": 0.015, "max": 4, "cost": 1400,
		"icon": "attributes/agility", "text": "{v} Movement Speed for every member."},
	&"quartermaster": {"name": "Quartermaster", "kind": "guild", "stat": &"potion_power", "op": "inc", "per": 0.06, "max": 4, "cost": 1000,
		"icon": "ui/repair", "text": "{v} Potion Effectiveness for every member."},
	&"open_doors": {"name": "Open Doors", "kind": "special", "per": 0.18, "max": 3, "cost": 2000,
		"icon": "ui/talk", "text": "Adventurers apply {v} sooner."},
	&"veteran_training": {"name": "Veteran Training", "kind": "special", "per": 0.25, "max": 3, "cost": 2500,
		"icon": "ui/level", "text": "Recruits arrive closer to your level ({v} narrower range) and members train faster."},
	# ---- Guild War: per comrade fighting beside you (up to WAR_CAP) ---------------------------------------------
	&"rallying_cry": {"name": "Rallying Cry", "kind": "war", "stat": &"damage", "op": "inc", "per": 0.008, "max": 5, "cost": 2500,
		"icon": "ui/crown", "text": "{v} Damage for every guild member fighting beside you."},
	&"shield_wall": {"name": "Shield Wall", "kind": "war", "stat": &"defense", "op": "inc", "per": 0.015, "max": 5, "cost": 2500,
		"icon": "attributes/wisdom", "text": "{v} Defense for every guild member fighting beside you."},
	&"war_drums": {"name": "War Drums", "kind": "war", "stat": &"attack_speed", "op": "inc", "per": 0.005, "max": 5, "cost": 3000,
		"icon": "attributes/dexterity", "text": "{v} Attack Speed for every guild member fighting beside you."},
	&"blood_oath": {"name": "Blood Oath", "kind": "war", "stat": &"life_leech", "op": "flat", "per": 0.0015, "max": 5, "cost": 3500,
		"icon": "ui/skull", "text": "{v} Life Leech for every guild member fighting beside you."},
	&"siege_masters": {"name": "Siege Masters", "kind": "war", "stat": &"elite_damage", "op": "inc", "per": 0.012, "max": 5, "cost": 3000,
		"icon": "ui/warning", "text": "{v} Damage to Champions for every guild member fighting beside you."},
}

## The order passives are shown in.
const ORDER := [&"sharpened_steel", &"iron_discipline", &"war_chest", &"scholars_hall", &"swift_banners", &"quartermaster",
	&"open_doors", &"veteran_training", &"rallying_cry", &"shield_wall", &"war_drums", &"blood_oath", &"siege_masters"]

static func passive(id: StringName) -> Dictionary:
	return PASSIVES.get(id, {})

## Gold for rank `rank` (1-based) of a passive.
static func cost(id: StringName, rank: int) -> int:
	var p := passive(id)
	if p.is_empty():
		return 0
	return int(round(float(p.cost) * pow(float(maxi(rank, 1)), 1.5) / 50.0)) * 50

## Guild level needed for rank `rank` (1-based): guild passives from level 1 (then every 2 levels), war from level 4.
static func level_req(id: StringName, rank: int) -> int:
	var p := passive(id)
	var base := 4 if String(p.get("kind", "")) == "war" else 1
	return base + (maxi(rank, 1) - 1) * 2

## The words for a passive's value at `rank` ("+6%").
static func value_text(id: StringName, rank: int) -> String:
	var p := passive(id)
	var v := float(p.get("per", 0.0)) * float(maxi(rank, 0))
	if String(p.get("kind", "")) == "special":
		return "%d%%" % roundi(v * 100.0)
	if p.get("op", "inc") == "flat" and v < 0.1:
		return "+%.2f%%" % (v * 100.0)
	return "+%s%%" % (("%.1f" % (v * 100.0)).trim_suffix(".0"))

static func describe(id: StringName, rank: int) -> String:
	var p := passive(id)
	return String(p.get("text", "")).replace("{v}", value_text(id, rank)).replace("{t}", "%d%%" % roundi(float(p.get("per", 0.0)) * float(rank) * 100.0))

# ---- adventurers ---------------------------------------------------------------------------------------------------

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]

## Traits an adventurer arrives with. `mods` apply to them when they answer Call to Arms; `renown` / `tithe` scale what
## they bring the guild; `loyal` makes their loyalty grow faster.
const TRAITS := {
	&"stalwart": {"name": "Stalwart", "text": "+15% Maximum HP when called to arms.", "mods": [[&"max_hp", "inc", 0.15]]},
	&"keen": {"name": "Keen-Eyed", "text": "+5% Critical Chance when called to arms.", "mods": [[&"crit_chance", "flat", 0.05]]},
	&"swift": {"name": "Swift", "text": "+10% Movement and Attack Speed when called to arms.", "mods": [[&"move_speed", "inc", 0.1], [&"attack_speed", "inc", 0.1]]},
	&"brash": {"name": "Brash", "text": "+15% Damage, -10% Defense when called to arms.", "mods": [[&"damage", "inc", 0.15], [&"defense", "inc", -0.1]]},
	&"scholar": {"name": "Scholar", "text": "Earns the guild 50% more renown.", "mods": [], "renown": 1.5},
	&"merchant": {"name": "Merchant-Born", "text": "Pays twice the usual tithe.", "mods": [], "tithe": 2.0},
	&"loyal": {"name": "Loyal", "text": "Loyalty grows twice as fast.", "mods": [], "loyal": 2.0},
	&"veteran": {"name": "Veteran", "text": "Arrives one level higher and trains faster.", "mods": [[&"defense", "inc", 0.08]], "train": 2.0},
	&"healer": {"name": "Field Medic", "text": "+20% Healing Effectiveness when called to arms.", "mods": [[&"healing", "inc", 0.2], [&"hp_regen", "flat", 3.0]]},
	&"berserker": {"name": "Berserker", "text": "+3% Life Leech when called to arms.", "mods": [[&"life_leech", "flat", 0.03]]},
}

## A member's standing by loyalty and level: what the roster calls them.
static func rank_title(member: Dictionary) -> String:
	var loy := int(member.get("loyalty", 0))
	if String(member.get("kind", "npc")) == "player":
		return "Sworn Hero"
	if loy >= 90:
		return "Champion"
	if loy >= 65:
		return "Officer"
	if loy >= 35:
		return "Veteran"
	return "Recruit"

static func trait_mods(trait_id: StringName) -> Array:
	var out := []
	var t: Dictionary = TRAITS.get(trait_id, {})
	for m in t.get("mods", []):
		if String(m[1]) == "flat":
			out.append(StatModifier.flat(m[0], float(m[2]), String(t.name)))
		else:
			out.append(StatModifier.inc(m[0], float(m[2]), String(t.name)))
	return out
