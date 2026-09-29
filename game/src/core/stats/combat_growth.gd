class_name CombatGrowth
## Shared progression budgets. Levels 1-5 retain the original damage and health.
## Gear scales with its drop level, never the wearer's current level.

static func ramp(level: int) -> float:
	return clampf(float(level - 5) / 10.0, 0.0, 1.0)

static func weapon_factor(level: int) -> float:
	var x := float(maxi(0, level - 5))
	return 1.0 + 0.065 * x + 0.0015 * x * x

static func health_factor(level: int) -> float:
	var x := float(maxi(0, level - 5))
	return 1.0 + 0.19 * x + 0.008 * x * x + 0.0001 * x * x * x

static func armor_factor(level: int) -> float:
	return 1.0 + 0.025 * float(maxi(0, level - 5))

static func physical_attack(strength: float, level: int) -> float:
	var x := maxf(0.0, strength - 15.0)
	return (0.5 * x + 0.004 * x * x) * ramp(level)

static func spell_power(intelligence: float, wisdom: float, focus: float, level: int) -> float:
	var x := maxf(0.0, intelligence - 15.0)
	return (0.7 * x + 0.006 * x * x + maxf(0.0, wisdom - 10.0) * 0.2 + focus * 0.25) * ramp(level)
