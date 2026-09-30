class_name DataGuilds
## Hero tiers (E..SSS) and the two guilds of Malasugue. Canon and provisional status: docs/LORE.md §5.
## Tier rank 0 = Unranked (not in a guild); ranks 1..8 = E, D, C, B, A, S, SS, SSS.

const EMBLEM := "res://assets/ui/tiers/tier_%s.svg"

## rank -> {letter, title, level, flag (deed world flag or ""), deed (text), fee, gate (rarity unlocked or -1), color}
const TIERS := [
	{"letter": "", "title": "Unranked", "level": 0, "flag": "", "deed": "", "jobs": 0, "dungeons": 0, "champions": 0, "dungeon_tier": 0, "fee": 0, "gate": -1, "color": Color(0.62, 0.6, 0.58), "key": "unranked"},
	{"letter": "E", "title": "Iron Initiate", "level": 1, "flag": "", "deed": "", "jobs": 0, "dungeons": 0, "champions": 0, "dungeon_tier": 0, "fee": 50, "gate": BH.Rarity.LICENSED, "color": Color(0.62, 0.62, 0.64), "key": "e"},
	{"letter": "D", "title": "Bronze Warden", "level": 2, "flag": "mq_three_told", "deed": "Complete the opening errands for Maelis, Hald, Aldric and Paul David", "jobs": 0, "dungeons": 0, "champions": 0, "dungeon_tier": 0, "fee": 0, "gate": BH.Rarity.MASTER, "color": Color(0.8, 0.52, 0.28), "key": "d"},
	{"letter": "C", "title": "Silver Crest", "level": 12, "flag": "catacombs_ritual_seen", "deed": "Witness the Catacombs ritual", "jobs": 5, "dungeons": 1, "champions": 1, "dungeon_tier": 0, "fee": 400, "gate": BH.Rarity.MYTHICAL, "color": Color(0.82, 0.85, 0.9), "key": "c"},
	{"letter": "B", "title": "Gold Laurel", "level": 20, "flag": "boss_kethrax_defeated", "deed": "Defeat Kethrax", "jobs": 10, "dungeons": 2, "champions": 3, "dungeon_tier": 0, "fee": 900, "gate": BH.Rarity.LEGENDARY, "color": Color(1.0, 0.8, 0.3), "key": "b"},
	{"letter": "A", "title": "Azure Star", "level": 32, "flag": "boss_warden_defeated", "deed": "Defeat Morthar, the Hollow Warden", "jobs": 20, "dungeons": 4, "champions": 5, "dungeon_tier": 0, "fee": 1800, "gate": BH.Rarity.AETHER, "color": Color(0.35, 0.65, 1.0), "key": "a"},
	{"letter": "S", "title": "Crimson Sun", "level": 45, "flag": "boss_warden_defeated", "deed": "Complete the story and conquer a tier 4 dungeon", "jobs": 40, "dungeons": 8, "champions": 8, "dungeon_tier": 4, "fee": 4000, "gate": -1, "color": Color(1.0, 0.3, 0.25), "key": "s"},
	{"letter": "SS", "title": "Twin Moon", "level": 55, "flag": "boss_warden_defeated", "deed": "Conquer a tier 5 dungeon", "jobs": 75, "dungeons": 12, "champions": 12, "dungeon_tier": 5, "fee": 9000, "gate": -1, "color": Color(0.8, 0.65, 1.0), "key": "ss"},
	{"letter": "SSS", "title": "Aether Crown", "level": 60, "flag": "boss_warden_defeated", "deed": "Clear all twenty dungeons", "jobs": 120, "dungeons": 20, "champions": 16, "dungeon_tier": 5, "fee": 20000, "gate": -1, "color": Color(0.6, 0.98, 1.0), "key": "sss"},
]
const MAX_RANK := 8

## Accord bonus per tier step (every guild): +2% Maximum HP and +1% Damage.
const ACCORD_HP := 0.02
const ACCORD_DAMAGE := 0.01

## Changing guild keeps the tier (it belongs to the hero) but costs a transfer fee.
const TRANSFER_FEE := 300

const GUILDS := {
	&"swordfin": {
		"name": "The Swordfin Company", "short": "Swordfin", "hall": "Swordfin Hall", "motto": "Strike first. Strike true.",
		"color": Color(0.25, 0.48, 0.85), "banner": "res://assets/ui/guilds/swordfin_banner.svg", "crest": "res://assets/ui/guilds/swordfin_crest.svg",
		"master": "Commander Rhea Talvanne", "registrar": &"dax",
		# per tier step
		"perks": [[&"phys_damage", 0.02], [&"impact_damage", 0.03], [&"knockback_res", 0.01]],
		"perk_text": ["+2% Physical Damage", "+3% Impact Damage", "+1% Knockback Resistance"],
		"shop_discount": {&"brannoc_forge": 0.15},
		"inn_discount": 0.0, "elite_gold": 0.10, "potion_healing": 0.0,
		"features": ["15% off at Brannoc's forge", "Bounty pay: +10% gold from elites and bosses"],
	},
	&"lantern": {
		"name": "The Lantern Covenant", "short": "Lantern", "hall": "Lantern House", "motto": "We keep the light between things.",
		"color": Color(0.72, 0.5, 0.95), "banner": "res://assets/ui/guilds/lantern_banner.svg", "crest": "res://assets/ui/guilds/lantern_crest.svg",
		"master": "Archivist Oren Vale", "registrar": &"lio",
		"perks": [[&"magic_damage", 0.02], [&"max_mana", 0.02], [&"status_res", 0.01]],
		"perk_text": ["+2% Magic Damage", "+2% Maximum Mana", "+1% Status Resistance"],
		"shop_discount": {&"seris_arcana": 0.15},
		"inn_discount": 0.25, "elite_gold": 0.0, "potion_healing": 0.10,
		"features": ["15% off Seris's arcana", "25% off rest at the Salted Marlin", "Potions heal 10% more"],
	},
}

static func tier(rank: int) -> Dictionary:
	return TIERS[clampi(rank, 0, MAX_RANK)]

static func letter(rank: int) -> String:
	return String(tier(rank).letter)

static func tier_name(rank: int) -> String:
	var t := tier(rank)
	return "Unranked" if rank <= 0 else "Class %s — %s" % [t.letter, t.title]

static func emblem_path(rank: int) -> String:
	return EMBLEM % tier(rank).key

static func guild(id: StringName) -> Dictionary:
	return GUILDS.get(id, {})

## Lowest tier rank that may equip an item of `rarity` (0 = anyone).
static func rank_for_rarity(rarity: int) -> int:
	for r in range(1, MAX_RANK + 1):
		if int(TIERS[r].gate) == rarity:
			return r
	return 0
