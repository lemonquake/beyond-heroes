class_name Abyss
## bh-042: the Abyss. From level 90 the climb turns steep (docs/PLAN_bh-042.md). These rules sit on top of the Descent
## (descent.gd): the Descent's curves still apply, and every monster of level 90 or more also gets
##   * +50% Defense and 8 times the damage (`defense_mult`, `damage_mult`), eased in over levels FROM..FULL so a hero of
##     89 does not walk into a wall between one map and the next;
##   * health that keeps growing with its level (`health_mult`), bosses included (a level-200 Abyss lord carries about
##     300 million);
## and a hero of level 90 or more gets less and less experience per kill as they level (`kill_xp_mult`, replacing the
## Descent's gentler fall-off).
## Nothing below level FROM changes. Every rule reads the monster's level (the hero's for experience), so host and guests
## agree in multiplayer.

## The ease-in begins after this level and is complete at FULL.
const FROM := 85
const FULL := 90
## The request: "50% more defense, 8x more damage" for every monster of level 90 and above.
const DEFENSE_MULT := 1.5
const DAMAGE_MULT := 8.0
## health_mult(L) = 1 + ((L - HP_FROM) / HP_SPAN)^HP_P: x1.7 at L100, x6.2 at L141, x14 at L200, x33 at L300.
const HP_FROM := 89
const HP_SPAN := 14.0
const HP_P := 1.25
## Experience from monsters for a hero past XP_FROM: x (1 + (level - XP_FROM) / XP_SPAN)^-XP_P
## (54% at L100, 15% at L141, 6% at L200, 2% at L300).
const XP_FROM := 90
const XP_SPAN := 20.0
const XP_P := 1.5

## Measurement switch (probes): false restores the game as it was before bh-042. Never saved; always true in play.
static var enabled := true

## 0 up to FROM, 1 from FULL on, a straight line between (used geometrically: the same factor every level).
static func ramp(level: int) -> float:
	if not enabled:
		return 0.0
	return clampf(float(level - FROM) / float(FULL - FROM), 0.0, 1.0)

static func active(level: int) -> bool:
	return enabled and level > FROM

## The ease-in multiplies by the same factor each level (x8 over five levels: x1.52 a level), never a jump of x2.
static func defense_mult(level: int) -> float:
	return pow(DEFENSE_MULT, ramp(level))

static func damage_mult(level: int) -> float:
	return pow(DAMAGE_MULT, ramp(level))

static func health_mult(level: int) -> float:
	if not enabled or level <= HP_FROM:
		return 1.0
	return 1.0 + pow(float(level - HP_FROM) / HP_SPAN, HP_P)

## Experience from monsters (and stage clears) for a hero of `hero_level`. Below XP_FROM the Descent's own fall-off
## (which starts at the same level) is used, so nothing changes there.
static func kill_xp_mult(hero_level: int) -> float:
	if not enabled:
		return Descent.kill_xp_mult(hero_level)
	var over := float(maxi(0, hero_level - XP_FROM))
	return pow(1.0 + over / XP_SPAN, -XP_P)

## A line for the Descent tooltip.
static func summary(level: int) -> String:
	if not active(level):
		return ""
	return "The Abyss (level %d+): monsters have %s Defense, %s damage and %s health; monsters give %d%% experience." % [
		FULL, _x(defense_mult(level)), _x(damage_mult(level)), _x(health_mult(level)), roundi(100.0 * kill_xp_mult(level))]

static func _x(v: float) -> String:
	return "x%.1f" % v if v < 10.0 else "x%d" % roundi(v)
