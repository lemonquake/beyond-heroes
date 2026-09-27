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
var mana_leech := 0.0               # Mana returned to the attacker
var reactions: Array[StringName] = []   # elemental reactions that fired (shatter, melt, purify, conduct, extinguish, fan, umbral)
var absorbed := 0                   # part of `total` soaked by a ward/shield (HP loss = total - absorbed)
var dominant_element := Elements.PHYSICAL
var skill: StringName = &""          # id of the skill that dealt this (styled damage numbers), empty for attacks
var skill_name := ""
var heavy := false                  # heavy / charged / skill blow (bigger impact feedback)
var finisher := false               # last hit of a combo chain
var steps := PackedStringArray()    # debug breakdown

func log_step(s: String) -> void:
	steps.append(s)

const REACTION_NAMES := {&"shatter": "Shatter", &"melt": "Melt", &"purify": "Purify", &"conduct": "Conduct",
	&"extinguish": "Extinguish", &"fan": "Fan the Flames", &"umbral": "Umbral Rend"}

func breakdown() -> String:
	return "\n".join(steps)
