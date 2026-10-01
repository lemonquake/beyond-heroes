class_name CombatBudget
## bh-028: the threat budget that ties hero and monster numbers together (docs/COMBAT_SCALING.md).
##
## Before bh-028, monster damage, monster health and hero health each grew by its own formula, plus step bonuses at
## levels 30, 45, 60 ... Monster hits were sized for heroes who put points into Strength or Wisdom. A hero who put every
## point into Intelligence or Dexterity had about a third of that health. At the level-45 step, an elite champion's
## heavy critical took 80-95% of such a hero's health, so on Mythic it killed them in one blow.
##
## The budget fixes the relation instead of the numbers:
##   1. The reference hero. `hero_hp_ref(L)` is the health of an average hero of level L: the four classes' base and
##      per-level health, a share of each level's points in Strength or Wisdom, and gear of that level.
##   2. Monster damage follows the reference hero. After level 5, a monster's damage grows exactly as fast as
##      `hero_hp_ref`. So a monster blow takes the same share of an average hero's health at level 10, 50 or 300. There
##      are no step bonuses, so there are no spikes.
##   3. Vitality. Every hero gains VITALITY_PER_LEVEL health per level after 5, whatever their build. Monster damage
##      does not follow it. Vitality is the margin that keeps an all-offense build alive.
##   4. Rank budget. Elites, champions and bosses multiply a blow a known amount. A boss's heaviest attacks are
##      compressed, so its biggest critical takes at most about 20% of an average hero's health: five hits.
##   5. The lethal-blow guard. No single hit from a monster or another hero can take more than a fixed share of a
##      hero's maximum health. This is a floor for under-geared heroes, not the normal case.
## Levels 1-5 keep their original numbers.

# ---- the reference hero ---------------------------------------------------------------------------------------------
## Average class base health (96) plus base attributes and starting gear.
const REF_HP_BASE := 300.0
## Average class health per level (9.1) + 3 of the 10 points in STR/WIS (~15) + gear growth (~16).
const REF_HP_PER_LEVEL := 40.0
## Health every hero gains per level above 5. Monster damage ignores it.
const VITALITY_PER_LEVEL := 16.0
const VITALITY_FROM := 5

# ---- monster ranks ---------------------------------------------------------------------------------------------------
enum Rank { NORMAL, ELITE, CHAMPION, BOSS }
## Boss attack multipliers above this knee count at half rate (a 4.2x slam hits like a 2.9x one).
const BOSS_MULT_KNEE := 1.6
const BOSS_MULT_SLOPE := 0.5
## Boss blows overall (their basic strikes already outclass a normal monster's through authored damage).
const BOSS_DAMAGE := 0.8

# ---- the lethal-blow guard -------------------------------------------------------------------------------------------
## Most of a hero's maximum health one hit can take, by the attacker's rank.
const BLOW_CAP := {Rank.NORMAL: 0.35, Rank.ELITE: 0.35, Rank.CHAMPION: 0.35, Rank.BOSS: 0.25}
## Hero against hero (the Sand Arena): no hit takes more than this share.
const PVP_BLOW_CAP := 0.2

# ---- hero against hero -----------------------------------------------------------------------------------------------
## Heroes are tuned to kill monsters with many times a hero's health, and their offense grows faster than any health
## curve (attribute and weapon growth compound). Between heroes, every blow is scaled so the plain weapon hit of the
## reference hero (`ref_hit`) takes PVP_HIT_SHARE of the reference hero's health, before armour. Better gear, skills
## and crits keep their edge; the level stops mattering: a duel lasts about as long at level 10 as at level 300.
const PVP_HIT_SHARE := 0.07

# ---- encounters ------------------------------------------------------------------------------------------------------
## From level 30, monsters are never more than this many levels below the hero. Before bh-028 the floor rose in
## 15-level steps, so every monster jumped from 30 to 45 on the hero's 45th level.
const ENCOUNTER_FROM := 30
const ENCOUNTER_GAP := 2

static func hero_hp_ref(level: int) -> float:
	return REF_HP_BASE + REF_HP_PER_LEVEL * float(maxi(level, 1) - 1)

static func vitality(level: int) -> float:
	return VITALITY_PER_LEVEL * float(maxi(0, level - VITALITY_FROM))

## Monster damage multiplier against level 1. Levels 1-5 keep the authored per-level growth; after that, damage follows
## the reference hero's health.
static func enemy_damage_scale(level: int, per_level: float) -> float:
	var early := 1.0 + per_level * float(clampi(level, 1, 5) - 1)
	if level <= 5:
		return early
	return early * hero_hp_ref(level) / hero_hp_ref(5)

## Monster health on top of CombatGrowth.health_factor: the old +20% at level 30 and +10% steps every 15 levels, as one
## smooth curve that passes through the old values at each checkpoint.
static func enemy_health_bonus(level: int) -> float:
	var entry := 0.2 * smoothstep(20.0, 30.0, float(level))
	var steps := maxf(0.0, float(level - 30) / 15.0)
	return 1.0 + entry + 0.10 * steps / (1.0 + 0.15 * steps)

## The rank a monster's stats were built with.
static func rank_of(elite: bool, champion: bool, boss: bool) -> int:
	if boss:
		return Rank.BOSS
	if champion:
		return Rank.CHAMPION
	return Rank.ELITE if elite else Rank.NORMAL

## A boss attack multiplier after compression of the heaviest attacks.
static func boss_attack_mult(mult: float) -> float:
	var m := mult if mult <= BOSS_MULT_KNEE else BOSS_MULT_KNEE + (mult - BOSS_MULT_KNEE) * BOSS_MULT_SLOPE
	return m * BOSS_DAMAGE

static func blow_cap(rank: int) -> float:
	return float(BLOW_CAP.get(rank, BLOW_CAP[Rank.NORMAL]))

static var _ref_hits := {}

## The plain weapon hit of the reference hero of a level: a Knight whose points follow the class build, wielding the
## best ordinary sword of that level at Advanced rarity (deterministic). Measured once per level and kept.
static func ref_hit(level: int) -> float:
	level = clampi(level, 1, BH.LEVEL_CAP)
	if _ref_hits.has(level):
		return _ref_hits[level]
	var h := Game.new_hero(&"knight", "Reference")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	h.progress.allocate_along_build(h.progress.free_points)
	var best: ItemBaseDef = null
	for b: ItemBaseDef in DB.item_bases.values():
		if b.weapon_type == &"sword" and b.level_req <= level and b.drop_weight > 0 and b.unique_name == "" and b.set_id == &"":
			if best == null or b.level_req > best.level_req or (b.level_req == best.level_req and String(b.id) < String(best.id)):
				best = b
	if best != null:
		h.equipment.slots[&"main_weapon"] = DB.make_item(best.id, BH.Rarity.ADVANCED, level, 493)
	var v := maxf(1.0, ItemCompare.basic_hit(h.compute_stats()))
	_ref_hits[level] = v
	return v

## Hero-against-hero damage multiplier (players and arena adventurers), by the attacker's level.
static func pvp_mult(level: int) -> float:
	return clampf(PVP_HIT_SHARE * hero_hp_ref(level) / ref_hit(level), 0.001, 1.0)

## The lowest level a monster spawns at for a hero (bosses always match the hero).
static func encounter_floor(hero_level: int) -> int:
	return hero_level - ENCOUNTER_GAP if hero_level >= ENCOUNTER_FROM else 1
