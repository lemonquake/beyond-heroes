class_name LegendaryPowerDef
extends Resource
## A unique effect found on Mythical, Legendary and Aether items. Implemented as a flag (read by combat hooks) plus optional stats.

@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export var flag: StringName              # sets flags[flag] += magnitude on the wearer
@export var magnitude := 1.0
@export var modifiers: Array = []         # extra StatModifiers
@export var categories: Array = []
@export var class_hint: StringName = &""  # knight/mage preference for drop weighting
@export var tier: StringName = &"legendary" # mythical / legendary / aether — which rarity tier can roll it
