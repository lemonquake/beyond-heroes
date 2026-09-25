class_name EnemyDef
extends Resource
## Enemy archetype definition. Stats are level-1 values scaled by `level_scaling`.

@export var id: StringName
@export var display_name: String
@export var archetype: StringName            # fodder, shield, ranged, caster, brute, assassin, boss
@export var model: String
@export var model_scale := 1.0
@export var tint := Color.WHITE
@export var hp := 40.0
@export var damage_min := 4.0
@export var damage_max := 7.0
@export var defense := 10.0
@export var evasion := 10.0
@export var accuracy := 30.0
@export var crit_chance := 0.03
@export var move_speed := 3.6
@export var weight := 1.0
@export var poise := 20.0
@export var knockback_res := 0.0
@export var status_res := 0.0
@export var affinity := Elements.PHYSICAL
@export var resistances := {}                # element -> fraction
@export var immune: Array = []               # elements
@export var aggro_range := 14.0
@export var leash_range := 32.0
@export var preferred_range := 1.8           # distance the AI tries to keep
@export var retreat_range := 0.0            # ranged: back off if the player is closer than this
@export var body_radius := 0.45
@export var body_height := 1.8
@export var attacks: Array = []              # [{id, anim, range, mult, element, knockback, poise, cooldown, kind, windup, radius, projectile, speed, telegraph, status}]
@export var xp_mult := 1.0
@export var drop_chance := 0.35
@export var gold := Vector2i(2, 8)
@export var level_scaling := 0.14            # +14% hp/damage per level (compounded linearly)
@export var sounds := {}                     # hurt, death, attack, idle
@export var blocks_front := false            # shield archetype
@export var guard_break := 60.0             # poise damage needed to break a guard
@export var can_be_elite := true
@export var anim_map := {}                   # override animation names (idle/run/...)

func scaled(level: int) -> float:
	return 1.0 + level_scaling * float(maxi(level, 1) - 1)
