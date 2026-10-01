class_name HeroProgress
extends RefCounted
## Level, experience, attribute allocation and point pools of a hero.

signal leveled_up(new_level: int, levels_gained: int)
signal xp_changed
signal points_changed

var cls: ClassDef
var level := 1
var xp := 0                          # progress inside the current level
var total_xp := 0
var allocated := {}                  # attribute -> points spent by the player
var free_points := 0
var skill_points := 0
var talent_points := 0
## bh-027: attribute points the survival rebalance's migration spent for an old save on load (0 = none); Game tells the
## player once.
var auto_allocated := 0

## Saves written before the survival rebalance (5068ae1) earned 3 attribute points and 1 skill point per level.
const POINT_RULES_VERSION := 2
const OLD_FREE_PER_LEVEL := 3
const OLD_SKILL_PER_LEVEL := 1

func setup(p_cls: ClassDef) -> void:
	cls = p_cls
	for a in BH.ATTRIBUTES:
		allocated[a] = 0

## Attribute totals before equipment: class base + growth * (level - 1) + allocated.
func base_attributes() -> Dictionary:
	var out := {}
	for a in BH.ATTRIBUTES:
		out[a] = int(cls.base_attributes.get(a, 0)) + int(roundf(float(cls.growth_per_level.get(a, 0.0)) * float(level - 1))) + int(allocated.get(a, 0))
	return out

## Adds XP, handling any number of level-ups with carry-over. Returns levels gained.
func add_xp(amount: int) -> int:
	if amount <= 0 or level >= BH.LEVEL_CAP:
		return 0
	xp += amount
	total_xp += amount
	var gained := 0
	while level < BH.LEVEL_CAP and xp >= XpCurve.xp_to_next(level):
		xp -= XpCurve.xp_to_next(level)
		level += 1
		gained += 1
		free_points += cls.free_points_per_level
		skill_points += cls.skill_points_per_level
		talent_points += cls.talent_points_per_level
	if level >= BH.LEVEL_CAP:
		xp = 0
	xp_changed.emit()
	if gained > 0:
		points_changed.emit()
		leveled_up.emit(level, gained)
	return gained

func allocate(attr: StringName, n := 1) -> bool:
	if n <= 0 or free_points < n or not allocated.has(attr):
		return false
	allocated[attr] += n
	free_points -= n
	points_changed.emit()
	return true

## Spend `n` free points in the same proportions as the points the hero already spent (largest remainder first), or
## along the class's major attributes (3 : 2 : 1) when nothing is spent yet. Returns the points spent.
func allocate_along_build(n: int) -> int:
	n = mini(n, free_points)
	if n <= 0:
		return 0
	var weights := {}
	var total := 0.0
	for a in BH.ATTRIBUTES:
		var w := float(allocated.get(a, 0))
		if w > 0.0:
			weights[a] = w
			total += w
	if total <= 0.0:
		var majors: Array = cls.major_attributes if cls and not cls.major_attributes.is_empty() else [BH.ATTRIBUTES[0]]
		for i in majors.size():
			weights[majors[i]] = float(maxi(1, 3 - i))
			total += weights[majors[i]]
	var given := {}
	var rest := []
	var spent := 0
	for a in weights:
		var exact := float(n) * float(weights[a]) / total
		given[a] = int(floor(exact))
		spent += int(given[a])
		rest.append([exact - floor(exact), String(a)])
	rest.sort_custom(func(x, y): return x[0] > y[0] or (x[0] == y[0] and x[1] < y[1]))
	var k := 0
	while spent < n and not rest.is_empty():
		var a := StringName(rest[k % rest.size()][1])
		given[a] = int(given[a]) + 1
		spent += 1
		k += 1
	for a in given:
		if int(given[a]) > 0:
			allocated[a] = int(allocated.get(a, 0)) + int(given[a])
	free_points -= spent
	points_changed.emit()
	return spent

func reset_attributes() -> void:
	for a in allocated:
		free_points += allocated[a]
		allocated[a] = 0
	points_changed.emit()

func to_dict() -> Dictionary:
	var al := {}
	for a in allocated:
		al[String(a)] = allocated[a]
	return {"level": level, "xp": xp, "total_xp": total_xp, "allocated": al, "free_points": free_points,
		"skill_points": skill_points, "talent_points": talent_points, "point_rules_version": POINT_RULES_VERSION}

func from_dict(d: Dictionary) -> void:
	level = clampi(int(d.get("level", 1)), 1, BH.LEVEL_CAP)
	xp = maxi(0, int(d.get("xp", 0)))
	total_xp = int(d.get("total_xp", 0))
	var al: Dictionary = d.get("allocated", {})
	for a in BH.ATTRIBUTES:
		allocated[a] = int(al.get(String(a), 0))
	free_points = int(d.get("free_points", 0))
	skill_points = int(d.get("skill_points", 0))
	talent_points = int(d.get("talent_points", 0))
	# Preserve spent, quest and cheat points; credit only the newly added level rewards.
	var version := int(d.get("point_rules_version", 0))
	var credit := (level - 1) * maxi(0, cls.free_points_per_level - OLD_FREE_PER_LEVEL)
	if version < 1:
		free_points += credit
		skill_points += (level - 1) * maxi(0, cls.skill_points_per_level - OLD_SKILL_PER_LEVEL)
	# bh-027: the credited attribute points are spent at once, along the hero's own build, so an old hero's Maximum HP,
	# Mana and the rest match the new balance the moment the save loads (they used to sit unspent until noticed).
	# Skill points stay the player's to place.
	auto_allocated = 0
	if version < 2 and credit > 0:
		auto_allocated = allocate_along_build(mini(credit, free_points))
	xp_changed.emit()
	points_changed.emit()
