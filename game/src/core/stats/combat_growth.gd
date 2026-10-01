class_name CombatGrowth
## Shared progression budgets. Levels 1-5 retain the original damage and health.
## Gear scales with its drop level, never the wearer's current level.

static func ramp(level: int) -> float:
	return clampf(float(level - 5) / 10.0, 0.0, 1.0)

static func weapon_factor(level: int) -> float:
	var x := float(clampi(level - 5, 0, 20))
	var late := float(maxi(0, level - 25))
	return 1.0 + 0.065 * x + 0.0015 * x * x + 0.06 * late + 0.0005 * late * late

static func health_factor(level: int) -> float:
	if level > 60:
		return health_factor(60) * weapon_factor(level) / weapon_factor(60)
	var x := float(maxi(0, level - 5))
	return 1.0 + 0.19 * x + 0.008 * x * x + 0.0001 * x * x * x

static func armor_factor(level: int) -> float:
	return 1.0 + 0.025 * float(maxi(0, level - 5))

static func physical_attack(strength: float, level: int) -> float:
	var x := maxf(0.0, strength - 15.0)
	return (0.5 * x + 0.0015 * x * x) * ramp(level)

static func spell_power(intelligence: float, wisdom: float, focus: float, level: int) -> float:
	var x := maxf(0.0, intelligence - 15.0)
	return (0.7 * x + 0.006 * x * x + maxf(0.0, wisdom - 10.0) * 0.2 + focus * 0.25) * ramp(level)

## bh-028: from level 30 monsters stay within CombatBudget.ENCOUNTER_GAP levels of the hero (the old floor jumped in
## 15-level steps). Bosses match the hero from the start.
static func encounter_level(authored: int, hero_level: int, boss := false) -> int:
	var floor_level := hero_level if boss else CombatBudget.encounter_floor(hero_level)
	return clampi(maxi(authored, floor_level), 1, BH.LEVEL_CAP)

static func milestone(level: int) -> int:
	return 1 + floori(float(level - 30) / 15.0) if level >= 30 else 0

## bh-028: one smooth curve through the old checkpoint values (CombatBudget).
static func enemy_health_bonus(level: int) -> float:
	return CombatBudget.enemy_health_bonus(level)

## bh-028: monster damage follows the reference hero's health (CombatBudget); the old milestone damage steps are gone.
static func enemy_damage_scale(level: int, per_level: float) -> float:
	return CombatBudget.enemy_damage_scale(level, per_level)

## Applicable increases share one budget; investment above +200% has
## diminishing returns. This limits multiplication without capping hit damage.
static func damage_increase(raw: float) -> float:
	var excess := maxf(0.0, raw - 2.0)
	return maxf(-0.9, raw) if excess == 0.0 else 2.0 + excess / (1.0 + excess / 3.0)

static func weapon_effectiveness(raw: float) -> float:
	var excess := maxf(0.0, raw - 2.0)
	return maxf(0.0, raw) if excess == 0.0 else 2.0 + excess / (1.0 + excess / 0.5)

## Boss burst protection follows progression, not an absolute late-game cap.
## Level 49 tops out at 12,000 per hit, and no hit removes more than 8% HP.
const BOSS_DAMAGE_TAKEN := 0.5
const BOSS_HIT_SHARE := 0.08

static func boss_hit_ceiling(level: int) -> float:
	var budget := (9.0 + 1.9 * level) * weapon_factor(level)
	var reference := (9.0 + 1.9 * 49.0) * weapon_factor(49)
	return 12000.0 * budget / reference
