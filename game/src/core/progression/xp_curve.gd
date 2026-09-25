class_name XpCurve
## Experience requirements and rewards.
## xp_to_next(L) = floor(80 * L^1.75 + 120 * L): 200 at L1, ~5.7k at L10, ~17.5k at L20, ~81k at L50.
## Monster XP grows ~ L^1.35 so kills-per-level rises gently (about 16 at L1, ~40 at L20, ~60 at L50 for fodder).

const A := 80.0
const P := 1.75
const B := 120.0

static func xp_to_next(level: int) -> int:
	if level >= BH.LEVEL_CAP:
		return 0
	var l := float(maxi(level, 1))
	return int(floor(A * pow(l, P) + B * l))

static func total_xp_for_level(level: int) -> int:
	var t := 0
	for l in range(1, clampi(level, 1, BH.LEVEL_CAP)):
		t += xp_to_next(l)
	return t

## Base XP for killing a monster of `monster_level`; rank multiplier for elites/bosses.
static func monster_xp(monster_level: int, rank_mult := 1.0) -> int:
	return int(round(12.0 * pow(float(maxi(monster_level, 1)), 1.35) * rank_mult))

## Level-difference scaling applied to kill XP: full within 3 levels, falling off beyond.
static func level_diff_mult(player_level: int, monster_level: int) -> float:
	var diff := monster_level - player_level
	if diff >= -3 and diff <= 3:
		return 1.0
	if diff > 3:
		return maxf(0.5, 1.0 - 0.1 * float(diff - 3))
	return maxf(0.05, 1.0 - 0.15 * float(-diff - 3))
