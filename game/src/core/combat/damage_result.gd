class_name DamageResult
extends RefCounted
## Output of DamagePipeline.compute — the only authority on damage numbers.

var total := 0                      # HP removed from the target (what the damage number shows)
var healed := 0                     # absorption healing on the target
var components := {}                # element -> final float amount (after everything, before rounding)
var pre_mitigation := 0.0           # sum after crit and offensive bonuses, before defense/resistance
var is_crit := false
var evaded := false
var blocked := false
var perfect_block := false
var blocked_amount := 0.0
var immune := false
var shattered := false
var purified := false
var knockback := 0.0                # final knockback speed (m/s) to apply to the target
var poise_damage := 0.0
var buildup := {}                   # status id -> buildup points (0-100 scale)
var leech := 0.0                    # HP returned to the attacker
var dominant_element := Elements.PHYSICAL
var steps := PackedStringArray()    # debug breakdown

func log_step(s: String) -> void:
	steps.append(s)

func breakdown() -> String:
	return "\n".join(steps)
