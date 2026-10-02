class_name SkillDef
extends Resource

## Active skill definition. Behaviour-specific numbers live in `params` so upgrade nodes can modify them by name.
##
## Behaviours: melee_arc, projectile, ground_aoe, self_aoe, leap, blink, buff, spin, chain, wave, dash_strike, judgment,
## (bh-010) flurry, spiral, aura, storm, sentry, orb, trap, vault, shadow_step, veil, mark

## bh-029: no skill fires faster than once a second, whatever its base cooldown or the hero's Cooldown Reduction.
const MIN_COOLDOWN := 1.0

@export var id: StringName
@export var display_name: String
@export_multiline var description: String   # may use {damage}, {radius}, {duration}, {count}, etc.
@export var class_id: StringName
@export var icon: String
@export var behavior: StringName
@export var kind := DamageRequest.Kind.SPELL   # ATTACK uses weapon damage (weapon_pct), SPELL uses base damage
@export var element := Elements.PHYSICAL
@export var conversion := {}                 # element -> share (overrides element)
@export var anim: StringName = &"cast_quick"
@export var anim_speed_stat: StringName = &"cast_speed"  # attack_speed for weapon skills
@export var max_rank := 5                    # rank the numbers below were tuned for; levels up to TreeDef.LEVEL_MAX use the tail curve
@export var mana_cost := 10.0
@export var mana_per_rank := 1.0
@export var valor_cost := 0.0                # knight
@export var cooldown := 0.0
@export var requires := &""                  # "melee", "shield", "" — weapon requirement
@export var params := {}                     # base parameters (damage_min/max, weapon_pct, radius, ...)
@export var per_rank := {}                   # param -> added per rank beyond 1
@export var sound_cast := &""
@export var sound_hit := &""
@export var vfx := &""
@export var tags: Array = []
# ---- bh-010 ----------------------------------------------------------------------------------------------------
@export var projectile_look := "orb"         # orb | arrow | fire | dark (Projectile looks)
## Statuses put on every enemy the skill hits: {status: [duration (number or param name), magnitude (number or param)]}
@export var on_hit_status := {}
## Auras: [[stat, op, param, scale]] -> StatModifier(stat, op, params[param] * scale) on every ally in the radius
@export var aura_mods: Array = []
@export var aura_kind := &""                 # offense | defense (auras)
@export var weapon_req_label := ""            # shown when `requires` is a custom requirement

## Hard horizontal travel limits, applied after every rank and side-passive bonus.
const MOVEMENT_LIMITS := {&"dash_strike": 8.0, &"leap": 14.0, &"blink": 12.0, &"vault": 10.0, &"shadow_step": 12.0}

func movement_limit() -> float:
	return float(MOVEMENT_LIMITS.get(behavior, 0.0))

func movement_distance(p: Dictionary) -> float:
	var key := "dash" if behavior == &"dash_strike" else "range"
	return clampf(float(p.get(key, params.get(key, 0.0))), 0.0, movement_limit())

func is_aura() -> bool:
	return behavior == &"aura"

func mana_at(rank: int) -> float:
	return mana_cost + mana_per_rank * (power(rank) - 1.0)

## Ranks' worth of effect at `rank` (a rank past `max_rank` counts for less).
func power(rank: int) -> float:
	return TreeDef.rank_power(maxi(rank, 1), max_rank)

## Parameters at a rank with upgrade deltas applied. upgrades: {param: total delta}.
func resolve(rank: int, upgrades: Dictionary = {}) -> Dictionary:
	var p := params.duplicate(true)
	var r := maxi(rank, 1)
	for k in per_rank:
		p[k] = float(p.get(k, 0.0)) + float(per_rank[k]) * (power(r) - 1.0)
	for k in upgrades:
		var v = upgrades[k]
		if v is bool:
			p[k] = v
		else:
			p[k] = float(p.get(k, 0.0)) + float(v)
	p["rank"] = r
	if movement_limit() > 0.0:
		p["dash" if behavior == &"dash_strike" else "range"] = movement_distance(p)
	for key in ["knockback", "launch"]:
		if p.has(key):
			p[key] = clampf(float(p[key]), 0.0, DamagePipeline.MAX_KNOCKBACK if key == "knockback" else DamagePipeline.MAX_LAUNCH)
	if id == &"spike_tentacle":
		p["stun_duration"] = minf(1.6, float(p.stun_duration))
	return p
