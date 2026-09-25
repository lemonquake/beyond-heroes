class_name AffixDef
extends Resource
## A random item modifier with level-gated tiers.

@export var id: StringName
@export var label: String                 # prefix/suffix word used in Magic item names
@export var is_prefix := true
@export var stat: StringName
@export var op := StatModifier.Op.FLAT
@export var tiers: Array = []             # [[min_item_level, min_value, max_value], ...] ascending
@export var categories: Array = []        # allowed item categories (empty = all equipment)
@export var group: StringName             # at most one affix per group on an item
@export var weight := 100
@export var integer := false              # round rolled values

func allowed_tiers(ilvl: int) -> Array:
	var out := []
	for i in tiers.size():
		if ilvl >= int(tiers[i][0]):
			out.append(i)
	return out

func allows(category: StringName) -> bool:
	return categories.is_empty() or categories.has(category)
