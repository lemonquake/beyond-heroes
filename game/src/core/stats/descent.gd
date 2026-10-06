class_name Descent
## bh-040: the Descent. Past level 80 the world stops keeping pace with the hero and starts pulling ahead
## (docs/THE_DESCENT.md). Every late-game curve lives here; nothing below FROM changes.
##
## What was wrong at level 141 (measured with a real level-141 Archmage, tests/tools/descent_probe.tscn):
##   * every normal monster and every elite died to one spell (a 12.4-million Meteor against 295,000 HP)
##   * a plain monster blow took 0.04-0.5% of the hero's health, and only two monsters were allowed to swing at once
##   * a level took 44 seconds of play, because kills per level barely grew past 80 (42 at 80, 51 at 141, 63 at 250)
##   * the 3.9-million-HP boss died in 27 s and dealt 5 damage
## The Descent fixes the relation from level 80 on, smoothly and without steps:
##   1. Monster health and damage grow faster than the hero (`health_mult`, `damage_mult`), by the monster's level.
##   2. Elites and champions cannot be felled by one blow (`hit_share`); bosses already have their burst limit.
##   3. The lethal-blow guard loosens (`guard_bonus`): deep down, two heavy blows can kill a careless hero.
##   4. Monsters fight harder: more of them swing at once, they act sooner and use skills more often (`fight`), and
##      elites carry more affixes (`extra_affixes`).
##   5. Experience slows: each level needs more (`xp_requirement_mult`), monsters give less to a hero past 90
##      (`kill_xp_mult`), and a fall costs part of the current level (`death_xp_share`).
## Depth is shown to the player as a Circle every 20 levels (a name only: the numbers never step).

## The Descent begins after this level.
const FROM := 80
## Monster experience starts to fall off after this hero level (the request: "past level 90 monsters give less").
const XP_FROM := 90
const CIRCLE_SPAN := 20

const CIRCLES := ["", "The Threshold", "The Ashen Stair", "The Ember Halls", "The Weeping Deep", "The Iron Gaol",
	"The Bone Orchard", "The Drowned Choir", "The Starless Vault", "The Broken Throne", "The Last Furnace",
	"The Bottom of the World"]

# ---- monsters --------------------------------------------------------------------------------------------------------
## health_mult(L) = 1 + HP_A * depth^HP_P    (depth = monster level - FROM)
const HP_A := 0.022
const HP_P := 1.1
## damage_mult(L) = 1 + DMG_A * depth^2 / (depth + DMG_ONSET): eases in over the first levels (a straight line jumped 8%
## from 80 to 81), then grows by about DMG_A per level.
const DMG_A := 0.085
const DMG_ONSET := 10.0
## Bosses: CombatBudget compresses their heaviest attacks (slope 0.5 above the knee, x0.8 overall). The Descent takes
## the compression away over BOSS_RAMP levels of depth: the slope reaches BOSS_SLOPE_TO and the overall factor
## BOSS_DAMAGE_TO.
const BOSS_SLOPE_TO := 1.0
const BOSS_DAMAGE_TO := 1.1
const BOSS_RAMP := 60.0
## The most of an elite's (champion's) maximum health one hit can take, once the Descent is fully in (20 levels deep).
const ELITE_HIT_SHARE := 0.15
const CHAMPION_HIT_SHARE := 0.06
const HIT_SHARE_RAMP := 20.0
## Deep down nothing falls to a single blow: a normal monster loses at most NORMAL_HIT_SHARE of its health to one hit,
## reached NORMAL_HIT_DEPTH levels deep (from no limit at NORMAL_HIT_FROM levels deep).
const NORMAL_HIT_SHARE := 0.34
const NORMAL_HIT_FROM := 20.0
const NORMAL_HIT_DEPTH := 60.0
## Leech-rate cap (Path of Exile's rule; Diablo II also cut leech in Hell): in the Descent life leech restores at most
## LEECH_CAP of Maximum HP per second, phased in over LEECH_DEPTH levels (no cap at the start of the Descent).
const LEECH_CAP := 0.06
const LEECH_DEPTH := 40.0
## Lethal-blow guard: how much higher the cap rises at full depth (GUARD_DEPTH levels in), by rank.
const GUARD_RISE := {CombatBudget.Rank.NORMAL: 0.10, CombatBudget.Rank.ELITE: 0.10, CombatBudget.Rank.CHAMPION: 0.12,
	CombatBudget.Rank.BOSS: 0.20}
const GUARD_DEPTH := 120.0
## The resistance penalty (Diablo II's Hell): a monster of the Descent takes this much off a hero's armour reduction and
## every resistance, after the 75% caps, reaching RES_PENALTY_MAX RES_PENALTY_DEPTH levels deep. A hero at the caps
## (75% -> 40%: 2.4 times the damage) takes the most from it; one with little armour the least (0% -> -35%: 1.35 times).
const RES_PENALTY_MAX := 0.35
const RES_PENALTY_DEPTH := 70.0
## Adaptive boss health (EnemyStats.boss_health) covers this many more seconds of the hero's damage per level of depth.
const BOSS_TIME_PER_DEPTH := 0.02

## Hit recovery (Diablo II's rule): in the Descent a blow only makes a monster flinch when it takes at least this share
## of its maximum health. Before bh-040 every hit replayed a hit reaction, and a monster could not leave its stagger
## while one played: a hero landing several blows a second held a boss helpless 73% of a fight (it dealt 5 damage in
## 27 s). Bosses never flinch from damage alone; a poise break still staggers everyone. Ramps in over FLINCH_RAMP levels.
const FLINCH_SHARE := {CombatBudget.Rank.NORMAL: 0.08, CombatBudget.Rank.ELITE: 0.16, CombatBudget.Rank.CHAMPION: 0.25,
	CombatBudget.Rank.BOSS: 2.0}
const FLINCH_RAMP := 20.0
## A Descent monster leaves a stagger or a knock-back after at most this long, whatever its animation is doing.
const STAGGER_HOLD_MAX := 1.2
## Pushes (blows, pulls, pulses, collisions) move a Descent monster this much less, by rank, once fully in (same ramp).
## Pulls and pulses skip Knockback Resistance, so this is applied to every push (Enemy.apply_knockback).
const KNOCK_RESIST := {CombatBudget.Rank.NORMAL: 0.2, CombatBudget.Rank.ELITE: 0.5, CombatBudget.Rank.CHAMPION: 0.6,
	CombatBudget.Rank.BOSS: 0.8}

# ---- how monsters fight -----------------------------------------------------------------------------------------------
## One more monster may swing at the hero at once every TOKEN_EVERY levels of depth, up to TOKENS_MAX more.
const TOKEN_EVERY := 25
const TOKENS_MAX := 4
const SKILL_RATE_PER_DEPTH := 0.004       # attack and skill cooldowns: up to SKILL_RATE_MAX times faster
const SKILL_RATE_MAX := 1.6
const AGGRESSION_PER_DEPTH := 0.003
const AGGRESSION_MAX := 1.5
const REACTION_PER_DEPTH := 0.006         # hesitation before a chase turns into a swing (shorter)
const REACTION_MIN_MULT := 0.35
const ELITE_CHANCE_PER_DEPTH := 0.01
const ELITE_CHANCE_MAX := 2.5
## Elites carry one more affix from this depth, and another from AFFIX_TWO.
const AFFIX_ONE := 40
const AFFIX_TWO := 100

# ---- experience ------------------------------------------------------------------------------------------------------
## Experience to the next level: x (1 + depth / XP_REQ_SPAN).
const XP_REQ_SPAN := 25.0
## Experience from monsters for a hero past XP_FROM: x 1 / (1 + (level - XP_FROM) / XP_KILL_SPAN).
const XP_KILL_SPAN := 30.0
## A fall (respawning, not a friend's revive) costs this share of the current level's requirement, from the
## progress inside the level only: DEATH_XP_MIN at the start of the Descent, rising to DEATH_XP_MAX DEATH_XP_DEPTH
## levels in.
const DEATH_XP_MIN := 0.02
const DEATH_XP_MAX := 0.10
const DEATH_XP_DEPTH := 60.0

## Measurement switch (tests/tools/descent_probe.tscn --descent=off): false restores the game as it was before bh-040,
## the Archmage bound included, so before and after can be measured on one build. Never saved; always true in play.
static var enabled := true

static func depth(level: int) -> float:
	return float(maxi(0, level - FROM)) if enabled else 0.0

static func active(level: int) -> bool:
	return enabled and level > FROM

# ---- monsters --------------------------------------------------------------------------------------------------------

static func health_mult(level: int) -> float:
	var d := depth(level)
	return 1.0 + HP_A * pow(d, HP_P) if d > 0.0 else 1.0

static func damage_mult(level: int) -> float:
	var d := depth(level)
	return 1.0 + DMG_A * d * d / (d + DMG_ONSET) if d > 0.0 else 1.0

## The most of its maximum health one hit can take from an elite (or champion) of `level` (1.0 = no limit).
static func hit_share(level: int, rank: int) -> float:
	var s := clampf(depth(level) / HIT_SHARE_RAMP, 0.0, 1.0)
	if s <= 0.0:
		return 1.0
	match rank:
		CombatBudget.Rank.CHAMPION: return lerpf(1.0, CHAMPION_HIT_SHARE, s)
		CombatBudget.Rank.ELITE: return lerpf(1.0, ELITE_HIT_SHARE, s)
		CombatBudget.Rank.NORMAL:
			return lerpf(1.0, NORMAL_HIT_SHARE, clampf((depth(level) - NORMAL_HIT_FROM) / (NORMAL_HIT_DEPTH - NORMAL_HIT_FROM), 0.0, 1.0))
	return 1.0

## The most of its Maximum HP a hero regains from life leech per second (0 = no cap: above the Descent).
static func leech_cap(level: int) -> float:
	var d := depth(level)
	if d <= 0.0:
		return 0.0
	return lerpf(1.0, LEECH_CAP, smoothstep(0.0, LEECH_DEPTH, d))

static func res_penalty(level: int) -> float:
	return RES_PENALTY_MAX * smoothstep(0.0, RES_PENALTY_DEPTH, depth(level))

## How much the lethal-blow guard rises for an attacker of `level` and `rank`.
static func guard_bonus(level: int, rank: int) -> float:
	return float(GUARD_RISE.get(rank, 0.0)) * smoothstep(0.0, GUARD_DEPTH, depth(level))

## How far the boss compression has been taken away (0 above the Descent, 1 at BOSS_RAMP levels deep).
static func boss_ramp(level: int) -> float:
	return smoothstep(0.0, BOSS_RAMP, depth(level))

## Adaptive boss health: the share of seconds the boss lasts, x this.
static func boss_time_mult(level: int) -> float:
	return 1.0 + BOSS_TIME_PER_DEPTH * depth(level)

# ---- how monsters fight -----------------------------------------------------------------------------------------------

## The least share of its maximum health a blow must take to make a monster of `level` and `rank` flinch (0 = any).
static func flinch_share(level: int, rank: int) -> float:
	return float(FLINCH_SHARE.get(rank, 0.0)) * clampf(depth(level) / FLINCH_RAMP, 0.0, 1.0)

## The share of a push a monster of `level` and `rank` still takes (1 above the Descent).
static func knock_taken(level: int, rank: int) -> float:
	return 1.0 - float(KNOCK_RESIST.get(rank, 0.0)) * clampf(depth(level) / FLINCH_RAMP, 0.0, 1.0)

## The difficulty a map's monsters fight with at `level` (Spawner): the base difficulty with the Descent's tokens,
## skill rate, aggression, reaction and elite chance on top. Health and damage stay in EnemyStats (by monster level).
static func fight(base: Dictionary, level: int) -> Dictionary:
	var d := depth(level)
	if d <= 0.0:
		return base
	var out := base.duplicate()
	out["tokens"] = int(base.get("tokens", 2)) + extra_tokens(level)
	out["skill_rate"] = float(base.get("skill_rate", 1.0)) * minf(SKILL_RATE_MAX, 1.0 + SKILL_RATE_PER_DEPTH * d)
	out["aggression"] = float(base.get("aggression", 1.0)) * minf(AGGRESSION_MAX, 1.0 + AGGRESSION_PER_DEPTH * d)
	out["reaction"] = float(base.get("reaction", 0.25)) * maxf(REACTION_MIN_MULT, 1.0 - REACTION_PER_DEPTH * d)
	out["elite"] = float(base.get("elite", 1.0)) * minf(ELITE_CHANCE_MAX, 1.0 + ELITE_CHANCE_PER_DEPTH * d)
	out["descent"] = level
	return out

static func extra_tokens(level: int) -> int:
	return mini(TOKENS_MAX, floori(depth(level) / float(TOKEN_EVERY)))

static func extra_affixes(level: int) -> int:
	var d := depth(level)
	return (1 if d >= AFFIX_ONE else 0) + (1 if d >= AFFIX_TWO else 0)

# ---- experience ------------------------------------------------------------------------------------------------------

static func xp_requirement_mult(level: int) -> float:
	return 1.0 + depth(level) / XP_REQ_SPAN

## Experience from monsters (and stage clears) for a hero of `hero_level`.
static func kill_xp_mult(hero_level: int) -> float:
	var over := float(maxi(0, hero_level - XP_FROM)) if enabled else 0.0
	return 1.0 / (1.0 + over / XP_KILL_SPAN)

## The share of the level requirement a fall costs at `level` (0 outside the Descent).
static func death_xp_share(level: int) -> float:
	if not active(level):
		return 0.0
	return lerpf(DEATH_XP_MIN, DEATH_XP_MAX, clampf(depth(level) / DEATH_XP_DEPTH, 0.0, 1.0))

## The experience a fall costs the hero now: never more than their progress inside the level (no level is lost).
static func death_xp_loss(hero: HeroData) -> int:
	if hero == null:
		return 0
	var lvl := hero.progress.level
	if lvl >= BH.LEVEL_CAP:
		return 0
	return mini(hero.progress.xp, int(floor(death_xp_share(lvl) * float(XpCurve.xp_to_next(lvl)))))

# ---- what the player sees ---------------------------------------------------------------------------------------------

## 0 above the Descent, then 1 (The Threshold) at FROM+1 ... one more every CIRCLE_SPAN levels.
static func circle(level: int) -> int:
	if not active(level):
		return 0
	return mini(CIRCLES.size() - 1, 1 + floori(float(level - FROM - 1) / float(CIRCLE_SPAN)))

static func circle_name(level: int) -> String:
	return String(CIRCLES[circle(level)])

static func roman(n: int) -> String:
	var vals := [[10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]]
	var s := ""
	for v in vals:
		while n >= int(v[0]):
			s += String(v[1])
			n -= int(v[0])
	return s

## One line for the HUD: "Descent · Circle III · The Ember Halls".
static func badge(level: int) -> String:
	if not active(level):
		return ""
	return "Descent · Circle %s · %s" % [roman(circle(level)), circle_name(level)]

## The full picture for a tooltip or the character sheet, for a hero of `level` (monsters of that level).
static func summary(level: int) -> String:
	if not active(level):
		return "The Descent begins after level %d. From then on every level makes the world harder than it makes you." % FROM
	var lines := PackedStringArray()
	lines.append("%s (level %d, %d levels deep)" % [badge(level), level, roundi(depth(level))])
	lines.append("Monsters of your level: %s health, %s damage." % [_x(health_mult(level)), _x(damage_mult(level))])
	if extra_tokens(level) > 0:
		lines.append("%d more monsters may attack you at once; they strike sooner and use skills more often." % extra_tokens(level))
	if res_penalty(level) > 0.005:
		lines.append("Their blows strip %d%% from your armour reduction and resistances." % roundi(100.0 * res_penalty(level)))
	if hit_share(level, CombatBudget.Rank.ELITE) < 1.0:
		lines.append("One hit takes at most %s%d%% of an elite's health, %d%% of a champion's." % [
			("%d%% of a monster's health, " % roundi(100.0 * hit_share(level, CombatBudget.Rank.NORMAL))) if hit_share(level, CombatBudget.Rank.NORMAL) < 1.0 else "",
			roundi(100.0 * hit_share(level, CombatBudget.Rank.ELITE)), roundi(100.0 * hit_share(level, CombatBudget.Rank.CHAMPION))])
	if leech_cap(level) > 0.0 and leech_cap(level) < 0.99:
		lines.append("Life leech restores at most %d%% of your Maximum HP per second." % roundi(100.0 * leech_cap(level)))
	if extra_affixes(level) > 0:
		lines.append("Elites carry %d more affix%s." % [extra_affixes(level), "" if extra_affixes(level) == 1 else "es"])
	lines.append("Experience to the next level %s; monsters give %d%% experience." % [_x(xp_requirement_mult(level)),
		roundi(100.0 * kill_xp_mult(level))])
	lines.append("A fall costs %d%% of this level's experience (never a level). A friend's revive costs nothing." % roundi(100.0 * death_xp_share(level)))
	return "\n".join(lines)

static func _x(v: float) -> String:
	return "x%.1f" % v if v < 10.0 else "x%d" % roundi(v)

## A notice when a level-up crosses into the Descent or into a new Circle.
static func level_notice(level: int, gained: int) -> String:
	var before := circle(level - gained)
	var now := circle(level)
	if now <= before:
		return ""
	if before == 0:
		return "You have begun the Descent. From here every level makes the world harder than it makes you: monsters grow tougher and deadlier, experience comes slower, and a fall costs experience."
	return "Circle %s of the Descent: %s. Monsters hit harder and fight harder." % [roman(now), circle_name(level)]
