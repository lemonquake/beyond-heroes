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
@export var set_id: StringName = &""       # item set this base belongs to (set pieces drop at a fixed rarity)
@export var unique_name := ""             # named unique (fixed name, fixed rarity, fixed powers)
@export var fixed_rarity := -1            # >= 0 forces the rarity when generated
@export var fixed_powers: Array = []      # power ids always present on this base (uniques)
@export var fixed_mods: Array = []        # extra StatModifiers of a unique (on top of rolled affixes)
@export var tier := 1                     # visual/model tier 1..3 (icon and weapon model variant)
@export var class_hint: StringName = &""  # knight / mage preference (drop weighting, shop stock)
@export var sellable := true
@export_multiline var lore := ""

func is_weapon() -> bool:
	return category == &"weapon"

func is_stackable() -> bool:
	return stack_max > 1

func is_quest() -> bool:
	return category == &"quest"

func is_consumable() -> bool:
	return category == &"consumable"

## Icon with graceful fallback: a tiered icon that is not (yet) authored falls back to the category/type icon.
func icon_path() -> String:
	if icon != "" and ResourceLoader.exists(icon):
		return icon
	var fb := ""
	if is_weapon():
		fb = "res://assets/ui/icons/items/%s.svg" % weapon_type
	else:
		match category:
			&"shield": fb = "res://assets/ui/icons/items/shield.svg"
			&"helm": fb = "res://assets/ui/icons/items/%s.svg" % ("helm_hood" if weight_class == &"cloth" else "helm_plate")
			&"armor": fb = "res://assets/ui/icons/items/%s.svg" % ("armor_robe" if weight_class == &"cloth" else "armor_plate")
			&"inner_garment": fb = "res://assets/ui/icons/items/inner_garment.svg"
			&"gloves": fb = "res://assets/ui/icons/items/%s.svg" % ("gloves_cloth" if weight_class == &"cloth" else "gloves_plate")
			&"boots": fb = "res://assets/ui/icons/items/%s.svg" % ("boots_cloth" if weight_class == &"cloth" else "boots_plate")
			&"accessory": fb = "res://assets/ui/icons/items/ring.svg"
			&"consumable": fb = "res://assets/ui/icons/items/potion_health.svg"
			_: fb = "res://assets/ui/icons/items/mat_iron_shard.svg"
	return fb
