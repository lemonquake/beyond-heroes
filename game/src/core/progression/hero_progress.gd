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
		"skill_points": skill_points, "talent_points": talent_points, "point_rules_version": 1}

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
	if int(d.get("point_rules_version", 0)) < 1:
		free_points += (level - 1) * maxi(0, cls.free_points_per_level - 3)
		skill_points += (level - 1) * maxi(0, cls.skill_points_per_level - 1)
	xp_changed.emit()
	points_changed.emit()
