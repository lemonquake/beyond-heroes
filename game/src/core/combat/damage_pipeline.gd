class_name DamagePipeline
## The single authoritative damage pipeline.
##
## Base -> Attribute scaling -> Weapon modifier -> Skill modifier -> Element split/modifier -> Critical check
## -> Offensive bonuses -> Target defense (armor, penetration) -> Target resistance (affinity, resistance,
## penetration, immunity, absorption) -> Status modifiers -> Block -> Final (rounded) -> Impact / physics / buildup.
##
## Deterministic: all randomness comes from the RandomNumberGenerator passed in.

const EVADE_ACC_FACTOR := 4.0
const EVADE_CAP := 0.5
const SHOCK_TAKEN := 0.15
const SHOCK_TAKEN_WET := 0.25
const CURSE_TAKEN := 0.15
const WET_LIGHTNING_MULT := 1.25
const WET_FIRE_MULT := 0.8
const SHATTER_MULT := 1.3
const PURIFY_MULT := 1.3
const EARTH_VS_ARMOR := 0.5          # earth component * (1 + target armor DR * this)
const STAGGERED_TAKEN := 0.3         # bosses/elites during a stagger window
const IMPACT_ARMOR_FACTOR := 0.5     # collision damage only meets half the armor
const PERFECT_BLOCK_STRENGTH := 1.0
const KB_CRIT_MULT := 1.25
const KB_BLOCKED_MULT := 0.3
const WIND_KB_BONUS := 0.5
const EARTH_POISE_BONUS := 0.5
const DARK_DRAIN := 0.10
const MAX_KNOCKBACK := 28.0          # m/s hard cap per hit
static var debug_enabled := false

static func compute(req: DamageRequest, rng: RandomNumberGenerator) -> DamageResult:
	var r := DamageResult.new()
	var atk := req.attacker
	var tgt := req.target
	var atk_level := atk.level if atk != null else tgt.level
	var st := req.target_status
	r.log_step("== %s (%s) ==" % [req.label, DamageRequest.Kind.keys()[req.kind]])

	# 0. Evasion (weapon attacks only).
	if req.kind == DamageRequest.Kind.ATTACK and req.evadable and atk != null:
		var eva := tgt.get_stat(&"evasion")
		var acc := maxf(1.0, atk.get_stat(&"accuracy"))
		var evade_chance := minf(EVADE_CAP, eva / (eva + acc * EVADE_ACC_FACTOR)) if eva > 0.0 else 0.0
		if st != null and (st.has(&"frozen") or st.has(&"stunned") or st.has(&"staggered")):
			evade_chance = 0.0
		var roll := rng.randf()
		r.log_step("Evasion: %.1f%% (roll %.3f)" % [evade_chance * 100.0, roll])
		if roll < evade_chance:
			r.evaded = true
			r.log_step("EVADED")
			_debug(r)
			return r

	# 1. Base damage.
	var base: float
	if req.kind == DamageRequest.Kind.ATTACK and req.use_weapon and atk != null:
		var wr := StatCalculator.weapon_range(atk, req.hand)
		base = lerpf(wr.x, wr.y, rng.randf())
		r.log_step("Base weapon roll %.1f (range %.1f-%.1f)" % [base, wr.x, wr.y])
	else:
		base = lerpf(req.base_min, req.base_max, rng.randf()) if req.base_max > req.base_min else req.base_min
		r.log_step("Base roll %.1f" % base)

	# 2. Attribute scaling.
	var attr_scale := 0.0
	if atk != null:
		match req.kind:
			DamageRequest.Kind.ATTACK: attr_scale = atk.get_stat(&"phys_damage")
			DamageRequest.Kind.SPELL: attr_scale = atk.get_stat(&"magic_damage")
	var dmg := base * (1.0 + attr_scale)
	r.log_step("Attribute scaling +%.1f%% -> %.1f" % [attr_scale * 100.0, dmg])

	# 3. Weapon modifier, 4. Skill modifier.
	dmg *= req.weapon_mult
	r.log_step("Weapon modifier x%.2f -> %.1f" % [req.weapon_mult, dmg])
	dmg *= req.skill_mult
	r.log_step("Skill modifier x%.2f -> %.1f" % [req.skill_mult, dmg])

	# 5. Element split and element modifiers.
	var comp := {}
	if req.kind == DamageRequest.Kind.ATTACK and atk != null:
		var share := atk.loadout.elem_share_for(req.hand) if atk.loadout != null else 0.0
		var wel := atk.loadout.element_for(req.hand) if atk.loadout != null else Elements.PHYSICAL
		_add(comp, Elements.PHYSICAL, dmg * (1.0 - share))
		if share > 0.0:
			_add(comp, wel, dmg * share)
		for e in req.conversion:
			var moved: float = comp.get(Elements.PHYSICAL, 0.0) * float(req.conversion[e])
			_add(comp, Elements.PHYSICAL, -moved)
			_add(comp, int(e), moved)
		for e in Elements.ELEMENTAL:
			var added := atk.get_stat(StringName("added_" + String(Elements.key(e))))
			if added > 0.0:
				_add(comp, e, added * lerpf(0.8, 1.2, rng.randf()) * req.weapon_mult * req.skill_mult)
	elif req.conversion.is_empty():
		_add(comp, Elements.PHYSICAL, dmg)
	else:
		for e in req.conversion:
			_add(comp, int(e), dmg * float(req.conversion[e]))
	if atk != null:
		for e in comp.keys():
			if e == Elements.PHYSICAL:
				continue
			var em := 1.0 + atk.get_stat(&"elemental_damage") + atk.get_stat(Elements.dmg_key(e))
			comp[e] *= em
			r.log_step("%s modifier x%.2f -> %.1f" % [Elements.NAMES[e], em, comp[e]])

	# 6. Critical check.
	if req.can_crit and atk != null and req.kind != DamageRequest.Kind.DOT and req.kind != DamageRequest.Kind.IMPACT:
		var cc := clampf(atk.get_stat(&"crit_chance") + req.crit_bonus, 0.0, StatCalculator.CRIT_CAP)
		var roll := rng.randf()
		r.is_crit = req.force_crit or roll < cc
		r.log_step("Critical chance %.1f%% (roll %.3f)%s" % [cc * 100.0, roll, " — forced" if req.force_crit else ""])
		if r.is_crit:
			var cm := atk.get_stat(&"crit_damage", StatCalculator.CRIT_DAMAGE_BASE)
			_scale_all(comp, cm)
			r.log_step("CRITICAL x%.2f -> %.1f" % [cm, _sum(comp)])

	# 7. Offensive bonuses.
	if atk != null and req.kind != DamageRequest.Kind.DOT:
		var inc := atk.get_stat(&"damage") + req.bonus_inc
		if req.kind == DamageRequest.Kind.ATTACK:
			inc += atk.get_stat(&"weapon_damage")
			if atk.loadout != null and atk.loadout.type_for(req.hand) != null:
				inc += atk.get_stat(StringName("dmg_wt_" + String(atk.loadout.type_for(req.hand).id)))
		if req.heavy:
			inc += atk.get_stat(&"heavy_damage")
		if req.kind == DamageRequest.Kind.IMPACT:
			inc += atk.get_stat(&"impact_damage")
		_scale_all(comp, 1.0 + inc)
		r.log_step("Increased damage +%.1f%% -> %.1f" % [inc * 100.0, _sum(comp)])
	for m in req.more:
		_scale_all(comp, float(m[1]))
		r.log_step("%s x%.2f -> %.1f" % [m[0], float(m[1]), _sum(comp)])
	r.pre_mitigation = _sum(comp)

	var mitigated := req.kind != DamageRequest.Kind.DOT
	# 8. Target defense (physical) with armor penetration.
	var armor_dr := 0.0
	if mitigated:
		var pen_armor := atk.get_stat(&"pen_armor") if atk != null else 0.0
		var eff_def := tgt.get_stat(&"defense") * (1.0 - clampf(pen_armor, 0.0, 1.0))
		if req.kind == DamageRequest.Kind.IMPACT:
			eff_def *= IMPACT_ARMOR_FACTOR
		armor_dr = StatCalculator.armor_reduction(eff_def, atk_level)
		var pdr := clampf(armor_dr + tgt.get_stat(&"phys_res_flat"), -1.0, StatCalculator.RES_CAP)
		if comp.has(Elements.PHYSICAL):
			comp[Elements.PHYSICAL] *= (1.0 - pdr)
			r.log_step("Defense %d (pen %.0f%%) vs level %d: -%.1f%% physical -> %.1f" % [roundi(eff_def), pen_armor * 100.0, atk_level, pdr * 100.0, comp[Elements.PHYSICAL]])
		if comp.has(Elements.EARTH) and armor_dr > 0.0:
			var em := 1.0 + armor_dr * EARTH_VS_ARMOR
			comp[Elements.EARTH] *= em
			r.log_step("Earth crushes armor x%.2f" % em)

	# 9. Target resistance: affinity, resistance, penetration, immunity, absorption.
	if mitigated:
		for e in comp.keys():
			if e == Elements.PHYSICAL:
				continue
			if tgt.immune.has(e):
				r.log_step("%s: IMMUNE" % Elements.NAMES[e])
				if tgt.absorb.has(e):
					r.healed += roundi(comp[e] * float(tgt.absorb[e]))
				comp[e] = 0.0
				continue
			var aff := Elements.affinity(e, tgt.affinity)
			var res := tgt.get_stat(Elements.res_key(e))
			var pen := atk.get_stat(Elements.pen_key(e)) if atk != null else 0.0
			var eff_res := clampf(res - pen, StatCalculator.RES_FLOOR, 1.0)
			comp[e] *= aff * (1.0 - eff_res)
			r.log_step("%s: affinity x%.2f, resistance %.0f%% - pen %.0f%% -> %.1f" % [Elements.NAMES[e], aff, res * 100.0, pen * 100.0, comp[e]])

	# 10. Status modifiers.
	if st != null:
		var wet := st.has(&"wet")
		if wet and comp.has(Elements.LIGHTNING):
			comp[Elements.LIGHTNING] *= WET_LIGHTNING_MULT
			r.log_step("Wet conducts Lightning x%.2f" % WET_LIGHTNING_MULT)
		if wet and comp.has(Elements.FIRE):
			comp[Elements.FIRE] *= WET_FIRE_MULT
			r.log_step("Wet dampens Fire x%.2f" % WET_FIRE_MULT)
		if st.has(&"frozen") and comp.get(Elements.PHYSICAL, 0.0) > 0.0 and (req.heavy or req.kind == DamageRequest.Kind.IMPACT):
			comp[Elements.PHYSICAL] *= SHATTER_MULT
			r.shattered = true
			r.log_step("SHATTER x%.2f" % SHATTER_MULT)
		if st.has(&"cursed") and comp.get(Elements.LIGHT, 0.0) > 0.0:
			comp[Elements.LIGHT] *= PURIFY_MULT
			r.purified = true
			r.log_step("PURIFY x%.2f" % PURIFY_MULT)
		var taken := 0.0
		if st.has(&"shocked"):
			taken += st.magnitude(&"shocked", SHOCK_TAKEN)
		if st.has(&"cursed"):
			taken += CURSE_TAKEN
		if st.has(&"stagger_window"):
			taken += STAGGERED_TAKEN
		if taken > 0.0:
			_scale_all(comp, 1.0 + taken)
			r.log_step("Status: +%.0f%% damage taken -> %.1f" % [taken * 100.0, _sum(comp)])
	if req.positional_mult != 1.0:
		_scale_all(comp, req.positional_mult)
		r.log_step("Positional x%.2f" % req.positional_mult)

	# 11. Block.
	if req.blockable and req.kind != DamageRequest.Kind.DOT and req.kind != DamageRequest.Kind.IMPACT:
		var bchance := 1.0 if req.guarding else tgt.get_stat(&"block_chance")
		if bchance > 0.0:
			var roll := rng.randf()
			if roll < bchance:
				r.blocked = true
				r.perfect_block = req.perfect_block
				var bs := PERFECT_BLOCK_STRENGTH if req.perfect_block else tgt.get_stat(&"block_strength")
				var before := _sum(comp)
				_scale_all(comp, 1.0 - bs)
				r.blocked_amount = before - _sum(comp)
				r.log_step("%s: %.0f%% prevented -> %.1f" % ["PARRY" if req.perfect_block else "BLOCK", bs * 100.0, _sum(comp)])

	# 12. Final damage.
	var total := 0.0
	var best := -1.0
	for e in comp:
		comp[e] = maxf(0.0, comp[e])
		total += comp[e]
		if comp[e] > best:
			best = comp[e]
			r.dominant_element = e
	r.components = comp
	r.immune = total <= 0.0 and not comp.is_empty() and not r.blocked
	r.total = roundi(total)
	if total > 0.0 and r.total < 1:
		r.total = 1
	r.log_step("FINAL %d" % r.total)

	# 13. Impact, poise, buildup, leech.
	var total_pre := maxf(0.0001, r.pre_mitigation)
	var wind_share: float = (comp.get(Elements.WIND, 0.0) / maxf(total, 0.0001)) if total > 0.0 else 0.0
	var earth_share: float = (comp.get(Elements.EARTH, 0.0) / maxf(total, 0.0001)) if total > 0.0 else 0.0
	if req.knockback > 0.0:
		var kb := req.knockback
		if atk != null:
			kb *= atk.get_stat(&"impact_strength", 1.0)
		kb *= 1.0 - tgt.get_stat(&"knockback_res")
		kb *= 1.0 + wind_share * WIND_KB_BONUS
		if r.is_crit:
			kb *= KB_CRIT_MULT
		if r.blocked:
			kb *= KB_BLOCKED_MULT
		kb /= maxf(0.25, req.target_weight)
		r.knockback = clampf(kb, 0.0, MAX_KNOCKBACK)
		r.log_step("Knockback %.1f m/s (weight %.1f)" % [r.knockback, req.target_weight])
	if req.poise > 0.0:
		var pd := req.poise * (1.0 + earth_share * EARTH_POISE_BONUS)
		if r.is_crit:
			pd *= 1.2
		if r.blocked:
			pd *= 0.25
		r.poise_damage = pd
	var max_hp := maxf(1.0, tgt.get_stat(&"max_hp", 100.0))
	var sres := tgt.get_stat(&"status_res")
	for e in comp:
		if e == Elements.PHYSICAL or comp[e] <= 0.0:
			continue
		var sid: StringName = Elements.STATUS_OF[e]
		if sid == &"stagger" or sid == &"windswept":
			continue
		var b: float = comp[e] / max_hp * 100.0 * 2.5 * req.status_power * (1.0 - sres)
		r.buildup[sid] = r.buildup.get(sid, 0.0) + b
	for sid in req.direct_status:
		r.buildup[sid] = r.buildup.get(sid, 0.0) + float(req.direct_status[sid]) * (1.0 - sres * 0.5)
	if atk != null and r.total > 0:
		r.leech = r.total * atk.get_stat(&"life_leech") + comp.get(Elements.DARK, 0.0) * DARK_DRAIN
	_debug(r)
	return r

## Blocked hits by a shield-less target, evasion etc. are decided above; this helper previews an average hit
## (no randomness) for tooltips — it runs the same pipeline with a fixed-midpoint RNG.
static func preview(req: DamageRequest) -> DamageResult:
	var rng := RandomNumberGenerator.new()
	rng.seed = 12345
	var saved_eva := req.evadable
	var saved_block := req.blockable
	var saved_crit := req.can_crit
	req.evadable = false
	req.blockable = false
	req.can_crit = false
	var r := compute(req, rng)
	req.evadable = saved_eva
	req.blockable = saved_block
	req.can_crit = saved_crit
	return r

static func _add(comp: Dictionary, e: int, v: float) -> void:
	comp[e] = comp.get(e, 0.0) + v

static func _scale_all(comp: Dictionary, f: float) -> void:
	for e in comp:
		comp[e] *= f

static func _sum(comp: Dictionary) -> float:
	var s := 0.0
	for e in comp:
		s += comp[e]
	return s

static func _debug(r: DamageResult) -> void:
	if debug_enabled:
		print(r.breakdown())
