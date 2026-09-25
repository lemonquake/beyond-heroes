class_name ItemBaseDef
extends Resource
## A base item type ("Iron Longsword", "Warden Kite Shield", "Silk Undershirt").

@export var id: StringName
@export var display_name: String
@export var category: StringName          # weapon, shield, helm, inner_garment, armor, gloves, boots, accessory, material, consumable
@export var weapon_type: StringName       # for category weapon
@export var icon: String                  # res path to icon svg
@export var level_req := 1
@export var drop_level := 1               # min item level to drop
@export var requirements := {}            # attribute -> min value
@export var damage_min := 0.0
@export var damage_max := 0.0
@export var element := Elements.PHYSICAL
@export var element_share := 0.0
@export var defense := 0.0
@export var block_chance := 0.0
@export var block_strength := 0.0
@export var implicit: Array = []          # Array[StatModifier]
@export var stack_max := 1
@export var value := 10
@export var weight_class: StringName = &"" # heavy / light / cloth (flavor + class affinity)
@export var model := ""                   # weapon/shield model path
@export var drop_weight := 100
@export_multiline var flavor := ""
@export var consumable_effect := {}       # {"heal": 0.35} etc.

func is_weapon() -> bool:
	return category == &"weapon"

func is_stackable() -> bool:
	return stack_max > 1
