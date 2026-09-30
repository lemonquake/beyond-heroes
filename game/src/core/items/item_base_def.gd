class_name ItemBaseDef
extends Resource
## A base item type ("Iron Longsword", "Warden Kite Shield", "Silk Undershirt").

@export var id: StringName
@export var display_name: String
@export var category: StringName          # weapon, shield, helm, inner_garment, armor, leggings, gloves, boots, accessory, material, consumable
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
@export var model := ""                   # 3D model (res path); "" = res://assets/items/<id>.glb, then the type fallback
@export var weight := -1.0                # carried weight per unit (-1 = category default, see DataItems.default_weight)
@export var attacks_per_second := 0.0     # weapons: this weapon's own attack rate (0 = the weapon type's rate)
@export var drop_weight := 100
@export_multiline var flavor := ""
@export var consumable_effect := {}       # {"heal": 0.35} etc.
@export var set_id: StringName = &""       # item set this base belongs to (set pieces drop at a fixed rarity)
@export var boss_exclusive := false       # dedicated level-30+ boss collection; never enters generic rewards
@export var equip_slots: Array = []       # optional exact slot restriction for distinct left/right set pieces
@export var unique_name := ""             # named unique (fixed name, fixed rarity, fixed powers)
@export var fixed_rarity := -1            # >= 0 forces the rarity when generated
@export var fixed_powers: Array = []      # power ids always present on this base (uniques)
@export var fixed_mods: Array = []        # extra StatModifiers of a unique (on top of rolled affixes)
@export var tier := 1                     # visual/model tier 1..3 (icon and weapon model variant)
@export var class_hint: StringName = &""  # knight / mage preference (drop weighting, shop stock)
@export var sellable := true
@export_multiline var lore := ""

const ITEM_MODEL := "res://assets/items/%s.glb"

func equipment_slots() -> Array:
	return equip_slots if not equip_slots.is_empty() else BH.CATEGORY_SLOTS.get(category, [])

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
			&"leggings": fb = "res://assets/ui/icons/items/%s.svg" % ("leggings_plate" if weight_class == &"heavy" else ("leggings_leather" if class_hint in [&"ranger", &"shadowblade"] else "leggings_cloth"))
			&"gloves": fb = "res://assets/ui/icons/items/%s.svg" % ("gloves_cloth" if weight_class == &"cloth" else "gloves_plate")
			&"boots": fb = "res://assets/ui/icons/items/%s.svg" % ("boots_cloth" if weight_class == &"cloth" else "boots_plate")
			&"accessory": fb = "res://assets/ui/icons/items/ring.svg"
			&"consumable": fb = "res://assets/ui/icons/items/potion_health.svg"
			&"crystal": fb = "res://assets/ui/icons/items/aether_shard.svg"
			_: fb = "res://assets/ui/icons/items/mat_iron_shard.svg"
	return fb

## The 3D model of this base: its own model (assets/items/<id>.glb), else the weapon-type / shield model, else "".
func model_path() -> String:
	if model != "" and ResourceLoader.exists(model):
		return model
	var own := ITEM_MODEL % id
	if ResourceLoader.exists(own):
		return own
	if is_weapon():
		var wt := DB.weapon_type(weapon_type)
		if wt and ResourceLoader.exists(wt.model):
			return wt.model
	elif category == &"shield":
		return "res://assets/weapons/shield.glb"
	return ""

## Attacks per second at 1.0 attack speed: the weapon's own rate, else its type's.
func weapon_aps() -> float:
	if attacks_per_second > 0.0:
		return attacks_per_second
	var wt := DB.weapon_type(weapon_type) if is_weapon() else null
	return wt.attacks_per_second if wt else 1.4
