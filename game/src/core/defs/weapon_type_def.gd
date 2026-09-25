class_name WeaponTypeDef
extends Resource
## Weapon category: stance, animations, timing, scaling, reach and impact profile.

@export var id: StringName
@export var display_name: String
@export var two_handed := false
@export var dual_wieldable := false
@export var ranged := false                 # fires projectiles on attack (bow, wand, staff light)
@export var projectile_element := -1        # -1 = uses weapon's element or physical
@export var projectile_speed := 26.0
@export var attacks_per_second := 1.2       # base rate at 1.0 attack speed
@export var reach := 2.2                    # melee reach (m) or projectile max range
@export var arc_degrees := 110.0            # melee hit cone
@export var crit_chance := 0.05
@export var impact := 1.0                   # knockback/impact multiplier of this weapon type
@export var knockback := 3.0                # base knockback speed (m/s) of a light hit
@export var poise_damage := 10.0
@export var heavy_multiplier := 1.8
@export var heavy_knockback := 9.0
@export var charge_max := 0.0               # seconds; >0 enables a charged heavy attack
@export var charge_bonus := 1.0             # extra damage multiplier at full charge
@export var scaling := {}                   # {&"str": 1.0} — % damage per attribute point
@export var idle_anim := &"idle_combat"
@export var light_anims: Array = []
@export var heavy_anim: StringName
@export var dual_light_anims: Array = []
@export var dual_heavy_anim: StringName
@export var swing_sound := &"swing_light"
@export var hit_sound := &"hit_flesh"
@export var icon := ""
@export var model := ""
@export var grip_offset := Transform3D.IDENTITY   # attachment correction in the hand socket
