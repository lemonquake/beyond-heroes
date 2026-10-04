class_name DamageRequest
extends RefCounted
## Everything the damage pipeline needs to resolve one hit. Built by skills/attacks/hazards.

enum Kind { ATTACK, SPELL, IMPACT, DOT, ENVIRONMENT }

var kind: Kind = Kind.ATTACK
var attacker: DerivedStats          # may be null (environment)
var target: DerivedStats
var target_status: StatusController # may be null
var base_min := 0.0
var base_max := 0.0
var hand := 0                       # weapon hand for attacks (dual wield)
var use_weapon := true              # attacks: roll the weapon range instead of base_min/max
var weapon_mult := 1.0              # heavy attack / charge / weapon-type multiplier
var skill_mult := 1.0               # skill damage effectiveness (rank scaled)
var conversion := {}                # spells: element -> fraction (sums to 1). Attacks: extra conversion of weapon damage
var bonus_inc := 0.0                # skill-local increased damage
var more: Array = []                # [[label, factor], ...] multiplicative offensive bonuses
var can_crit := true
var force_crit := false
var crit_bonus := 0.0               # added crit chance for this hit
var evadable := true
var graze := false                  # bh-028: an area hit; evaded at the graze odds (DamagePipeline.GRAZE_*)
var blockable := true
var guarding := false               # target is actively guarding and the hit is frontal
var perfect_block := false          # guard started within the parry window
var knockback := 0.0                # base knockback speed (m/s)
var poise := 0.0                    # base poise damage
var status_power := 1.0             # multiplier on status buildup
var direct_status := {}             # status id -> buildup applied directly (e.g. Firebolt ignite 100)
var heavy := false
var target_weight := 1.0
var positional_mult := 1.0          # weak point / backstab multiplier (already decided by caller)
var tags := {}                      # &"melee", &"projectile", &"aoe", &"spell_school_*"
var label := ""                     # debug label (skill name)
## Class Transcendence (Null Lance): extra armor and resistance penetration of this hit, added to the attacker's own
## before the usual limits (armor penetration at most 100%, resistances never below the floor).
var pen_extra := 0.0

## Shallow copy with independent containers (one request per target for AoE / projectiles).
func clone() -> DamageRequest:
	var r := DamageRequest.new()
	for p in ["kind", "attacker", "base_min", "base_max", "hand", "use_weapon", "weapon_mult", "skill_mult", "bonus_inc",
			"can_crit", "force_crit", "crit_bonus", "evadable", "graze", "blockable", "guarding", "perfect_block", "knockback", "poise",
			"status_power", "heavy", "target_weight", "positional_mult", "label", "pen_extra"]:
		r.set(p, get(p))
	r.conversion = conversion.duplicate()
	r.more = more.duplicate(true)
	r.direct_status = direct_status.duplicate()
	r.tags = tags.duplicate()
	return r
