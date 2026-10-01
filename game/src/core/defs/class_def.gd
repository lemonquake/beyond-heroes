class_name ClassDef
extends Resource
## Playable hero class definition (data only).

@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export var model_path: String
@export var base_attributes := {}          # {&"str": 14, ...}
@export var growth_per_level := {}         # automatic attribute growth per level
@export var free_points_per_level := 10
@export var skill_points_per_level := 2
@export var talent_points_per_level := 1
@export var base_hp := 100.0
@export var hp_per_level := 10.0
## bh-028: bonus Maximum HP per level-up for every hero class (StatCalculator.LEVEL_UP_HP). Tempo shells set it to 0: they
## mirror the hero's HP, bonus included.
@export var level_up_hp := StatCalculator.LEVEL_UP_HP
@export var base_mana := 50.0
@export var mana_per_level := 5.0
@export var mana_regen_mult := 1.0
@export var base_defense := 0.0
@export var base_move_speed := 5.0
@export var base_knockback_res := 0.0
@export var base_poise := 30.0
@export var dodge_cooldown := 1.2
@export var resource_kind: StringName = &""   # &"valor" or &"arcane"
@export var class_modifiers: Array = []       # Array[StatModifier] always applied (class quirks)
@export var starting_items: Array = []        # Array of item base ids to equip at start
@export var starting_skills: Array = []       # skill ids unlocked at level 1
@export var skill_tree_id: StringName
@export var talent_tree_id: StringName
@export var weapon_mastery := {}              # weapon type id -> damage bonus fraction
@export var tint := Color.WHITE
# Presentation (hero selection)
@export var tagline := ""
@export var difficulty := 1                    # 1 straightforward .. 3 demanding
@export var class_resource_name := ""
@export_multiline var resource_desc := ""
@export var strengths: Array = []
@export var weaknesses: Array = []
@export var major_attributes: Array = []
