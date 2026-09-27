class_name SkillDef
extends Resource
## Active skill definition. Behaviour-specific numbers live in `params` so upgrade nodes can modify them by name.
##
## Behaviours: melee_arc, projectile, ground_aoe, self_aoe, leap, blink, buff, spin, chain, wave, dash_strike, judgment,
## (bh-010) flurry, spiral, aura, storm, sentry, orb, trap, vault, shadow_step, veil, mark

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
@export var max_rank := 5
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

func is_aura() -> bool:
	return behavior == &"aura"

func mana_at(rank: int) -> float:
	return mana_cost + mana_per_rank * float(maxi(rank, 1) - 1)

## Parameters at a rank with upgrade deltas applied. upgrades: {param: total delta}.
func resolve(rank: int, upgrades: Dictionary = {}) -> Dictionary:
	var p := params.duplicate(true)
	var r := maxi(rank, 1)
	for k in per_rank:
		p[k] = float(p.get(k, 0.0)) + float(per_rank[k]) * float(r - 1)
	for k in upgrades:
		var v = upgrades[k]
		if v is bool:
			p[k] = v
		else:
			p[k] = float(p.get(k, 0.0)) + float(v)
	p["rank"] = r
	return p
