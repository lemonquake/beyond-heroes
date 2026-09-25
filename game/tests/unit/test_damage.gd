extends TestCase
## Damage pipeline tests. Expected values are hand-computed oracles, not re-derived from pipeline code.

func _spell(atk: DerivedStats, tgt: DerivedStats, amount: float, element := Elements.PHYSICAL) -> DamageRequest:
	var r := DamageRequest.new()
	r.kind = DamageRequest.Kind.SPELL
	r.attacker = atk
	r.target = tgt
	r.base_min = amount
	r.base_max = amount
	r.can_crit = false
	r.blockable = false
	if element != Elements.PHYSICAL:
		r.conversion = {element: 1.0}
	return r

func test_crit_is_exactly_1_5x_before_mitigation() -> void:
	var atk := blank_stats()
	var tgt := blank_stats()
	var req := _spell(atk, tgt, 100.0)
	var normal := DamagePipeline.compute(req, rng())
	eq(normal.total, 100, "normal hit")
	req.can_crit = true
	req.force_crit = true
	var crit := DamagePipeline.compute(req, rng())
	ok(crit.is_crit, "forced crit flagged")
	eq(crit.pre_mitigation, 150.0, "crit pre-mitigation = 150")
	eq(crit.total, 150, "crit total with no mitigation = 150")
	atk.values[&"crit_damage"] = 1.75
	eq(DamagePipeline.compute(req, rng()).total, 175, "crit damage modifier respected")

func test_crit_then_armor() -> void:
	var atk := blank_stats()
	var tgt := blank_stats()
	tgt.values[&"defense"] = 100.0
	var req := _spell(atk, tgt, 100.0)
	req.can_crit = true
	req.force_crit = true
	var r := DamagePipeline.compute(req, rng())
	# DR = 100 / (100 + 40 + 12*1) = 0.657895 ; 150 * 0.342105 = 51.3158
	eq(r.pre_mitigation, 150.0, "crit applied before mitigation")
	eq(r.total, 51, "armor after crit")

func test_armor_formula() -> void:
	near(StatCalculator.armor_reduction(100.0, 1), 100.0 / 152.0, 0.00001, "armor DR level 1")
	near(StatCalculator.armor_reduction(300.0, 10), 300.0 / 460.0, 0.00001, "armor DR level 10")
	eq(StatCalculator.armor_reduction(0.0, 5), 0.0, "no armor")
	var atk := blank_stats()
	var tgt := blank_stats()
	tgt.values[&"defense"] = 1.0e9
	var r := DamagePipeline.compute(_spell(atk, tgt, 100.0), rng())
	eq(r.total, 25, "physical resistance capped at 75%")

func test_resistance_penetration_affinity_immunity() -> void:
	var atk := blank_stats()
	var tgt := blank_stats()
	tgt.values[&"res_fire"] = 0.5
	eq(DamagePipeline.compute(_spell(atk, tgt, 100.0, Elements.FIRE), rng()).total, 50, "50% fire res")
	atk.values[&"pen_fire"] = 0.2
	eq(DamagePipeline.compute(_spell(atk, tgt, 100.0, Elements.FIRE), rng()).total, 70, "20% penetration")
	var tgt2 := blank_stats()
	tgt2.affinity = Elements.ICE
	eq(DamagePipeline.compute(_spell(blank_stats(), tgt2, 100.0, Elements.FIRE), rng()).total, 150, "fire vs ice affinity x1.5")
	tgt2.affinity = Elements.FIRE
	eq(DamagePipeline.compute(_spell(blank_stats(), tgt2, 100.0, Elements.FIRE), rng()).total, 50, "same element x0.5")
	eq(DamagePipeline.compute(_spell(blank_stats(), tgt2, 100.0, Elements.WATER), rng()).total, 150, "water vs fire x1.5")
	eq(DamagePipeline.compute(_spell(blank_stats(), tgt2, 100.0, Elements.ICE), rng()).total, 75, "ice vs fire x0.75")
	var tgt3 := blank_stats()
	tgt3.values[&"res_dark"] = -0.5
	eq(DamagePipeline.compute(_spell(blank_stats(), tgt3, 100.0, Elements.DARK), rng()).total, 150, "negative resistance = weakness")
	tgt3.immune[Elements.DARK] = true
	var imm := DamagePipeline.compute(_spell(blank_stats(), tgt3, 100.0, Elements.DARK), rng())
	eq(imm.total, 0, "immune")
	ok(imm.immune, "immune flag")
	tgt3.absorb[Elements.DARK] = 0.5
	eq(DamagePipeline.compute(_spell(blank_stats(), tgt3, 100.0, Elements.DARK), rng()).healed, 50, "absorb heals")

func test_element_matrix_is_thematic_and_symmetric_where_documented() -> void:
	var wheel := [Elements.FIRE, Elements.ICE, Elements.WIND, Elements.EARTH, Elements.LIGHTNING, Elements.WATER]
	for i in wheel.size():
		var a: int = wheel[i]
		var b: int = wheel[(i + 1) % 6]
		eq(Elements.affinity(a, b), 1.5, "%s beats %s" % [Elements.NAMES[a], Elements.NAMES[b]])
		eq(Elements.affinity(b, a), 0.75, "%s weak into %s" % [Elements.NAMES[b], Elements.NAMES[a]])
	eq(Elements.affinity(Elements.LIGHT, Elements.DARK), 1.5, "light vs dark")
	eq(Elements.affinity(Elements.DARK, Elements.LIGHT), 1.5, "dark vs light")
	eq(Elements.affinity(Elements.PHYSICAL, Elements.FIRE), 1.0, "physical ignores affinity")
	eq(Elements.affinity(Elements.FIRE, Elements.PHYSICAL), 1.0, "neutral defender")
	# Every non-wheel, non-light/dark, non-same pair must be neutral (no filler relationships).
	var strong := 0
	for a in Elements.ELEMENTAL:
		for b in Elements.ELEMENTAL:
			if Elements.affinity(a, b) > 1.0:
				strong += 1
	eq(strong, 8, "exactly 8 strong relationships")

func test_status_interactions_in_pipeline() -> void:
	var st := StatusController.new()
	st.apply(&"wet")
	var req := _spell(blank_stats(), blank_stats(), 100.0, Elements.LIGHTNING)
	req.target_status = st
	eq(DamagePipeline.compute(req, rng()).total, 125, "wet + lightning x1.25")
	var req2 := _spell(blank_stats(), blank_stats(), 100.0, Elements.FIRE)
	req2.target_status = st
	eq(DamagePipeline.compute(req2, rng()).total, 80, "wet dampens fire x0.8")
	var st2 := StatusController.new()
	st2.apply(&"shocked", -1.0, 0.15)
	var req3 := _spell(blank_stats(), blank_stats(), 100.0)
	req3.target_status = st2
	eq(DamagePipeline.compute(req3, rng()).total, 115, "shocked +15% taken")
	var st3 := StatusController.new()
	st3.apply(&"frozen")
	var req4 := _spell(blank_stats(), blank_stats(), 100.0)
	req4.heavy = true
	req4.target_status = st3
	var sh := DamagePipeline.compute(req4, rng())
	ok(sh.shattered, "heavy hit on frozen shatters")
	eq(sh.total, 130, "shatter x1.3")

func test_combined_modifier_chain() -> void:
	var atk := blank_stats()
	atk.values[&"magic_damage"] = 0.5
	atk.values[&"dmg_fire"] = 0.3
	atk.values[&"damage"] = 0.2
	var tgt := blank_stats()
	tgt.values[&"res_fire"] = 0.25
	var st := StatusController.new()
	st.apply(&"cursed")
	var req := _spell(atk, tgt, 100.0, Elements.FIRE)
	req.skill_mult = 1.2
	req.can_crit = true
	req.force_crit = true
	req.more = [["Test more", 1.1]]
	req.target_status = st
	var r := DamagePipeline.compute(req, rng())
	# 100 *1.5 attr =150 *1.2 skill =180 *1.3 fire =234 *1.5 crit =351 *1.2 inc =421.2 *1.1 more =463.32
	near(r.pre_mitigation, 463.32, 0.001, "pre-mitigation chain")
	# *0.75 res =347.49 *1.15 curse =399.6135 -> 400
	eq(r.total, 400, "final combined")

func test_block_and_parry() -> void:
	var tgt := blank_stats()
	tgt.values[&"block_strength"] = 0.6
	var req := _spell(blank_stats(), tgt, 100.0)
	req.kind = DamageRequest.Kind.ATTACK
	req.use_weapon = false
	req.evadable = false
	req.blockable = true
	req.guarding = true
	var r := DamagePipeline.compute(req, rng())
	ok(r.blocked, "guarding blocks")
	eq(r.total, 40, "60% block strength")
	req.perfect_block = true
	var p := DamagePipeline.compute(req, rng())
	eq(p.total, 0, "parry prevents all")
	ok(p.perfect_block and not p.immune, "parry is not immunity")

func test_weapon_attack_and_dual_wield() -> void:
	var atk := blank_stats()
	atk.loadout.main_type = DB.weapon_type(&"sword")
	atk.loadout.main_min = 10.0
	atk.loadout.main_max = 10.0
	atk.values[&"phys_damage"] = 0.2
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = atk
	req.target = blank_stats()
	req.can_crit = false
	req.evadable = false
	req.blockable = false
	eq(DamagePipeline.compute(req, rng()).total, 12, "weapon 10 * 1.2")
	atk.loadout.dual_wield = true
	atk.loadout.off_type = DB.weapon_type(&"dagger")
	atk.loadout.off_min = 20.0
	atk.loadout.off_max = 20.0
	req.hand = 1
	# off hand 20 * 0.85 = 17 * 1.2 = 20.4 -> 20
	eq(DamagePipeline.compute(req, rng()).total, 20, "off-hand dual wield damage")
	req.hand = 0
	# main 10 * 0.85 = 8.5 * 1.2 = 10.2 -> 10
	eq(DamagePipeline.compute(req, rng()).total, 10, "main-hand dual wield damage")

func test_dot_and_impact_rules() -> void:
	var tgt := blank_stats()
	tgt.values[&"defense"] = 152.0 - 52.0  # DR 100/152
	var dot := _spell(null, tgt, 10.0)
	dot.kind = DamageRequest.Kind.DOT
	eq(DamagePipeline.compute(dot, rng()).total, 10, "DOT is pre-mitigated")
	var imp := _spell(null, tgt, 100.0)
	imp.kind = DamageRequest.Kind.IMPACT
	# half armor: 50 / (50 + 40 + 12) = 0.4902 -> 50.98 -> 51
	eq(DamagePipeline.compute(imp, rng()).total, 51, "impact meets half armor")

func test_knockback_and_caps() -> void:
	var atk := blank_stats()
	atk.values[&"impact_strength"] = 1.2
	var tgt := blank_stats()
	tgt.values[&"knockback_res"] = 0.25
	var req := _spell(atk, tgt, 10.0)
	req.knockback = 10.0
	req.target_weight = 2.0
	near(DamagePipeline.compute(req, rng()).knockback, 4.5, 0.0001, "10*1.2*0.75/2")
	req.knockback = 1000.0
	req.target_weight = 0.01
	eq(DamagePipeline.compute(req, rng()).knockback, DamagePipeline.MAX_KNOCKBACK, "knockback hard cap")

func test_minimum_and_determinism() -> void:
	eq(DamagePipeline.compute(_spell(blank_stats(), blank_stats(), 0.3), rng()).total, 1, "minimum 1 damage")
	var atk := blank_stats()
	atk.values[&"crit_chance"] = 0.5
	var tgt := blank_stats()
	tgt.values[&"evasion"] = 40.0
	atk.values[&"accuracy"] = 20.0
	var req := _spell(atk, tgt, 50.0)
	req.kind = DamageRequest.Kind.ATTACK
	req.use_weapon = false
	req.base_min = 40.0
	req.base_max = 60.0
	req.can_crit = true
	var a := []
	var b := []
	var r1 := rng(99)
	var r2 := rng(99)
	for i in 200:
		a.append(DamagePipeline.compute(req, r1).total)
		b.append(DamagePipeline.compute(req, r2).total)
	eq(a, b, "same seed -> same sequence")
	var evades := 0
	var r3 := rng(7)
	for i in 4000:
		if DamagePipeline.compute(req, r3).evaded:
			evades += 1
	# evade = 40 / (40 + 20*4) = 0.3333
	near(evades / 4000.0, 1.0 / 3.0, 0.03, "evasion rate matches formula")

func test_displayed_equals_applied() -> void:
	# The number shown is result.total; sum of rounded components must round to the same value.
	var atk := blank_stats()
	atk.values[&"crit_chance"] = 0.3
	var r := rng(3)
	for i in 500:
		var req := _spell(atk, blank_stats(), 37.3 + i * 0.7, Elements.FIRE)
		req.conversion = {Elements.FIRE: 0.4, Elements.EARTH: 0.35, Elements.PHYSICAL: 0.25}
		req.can_crit = true
		var res := DamagePipeline.compute(req, r)
		var s := 0.0
		for e in res.components:
			s += res.components[e]
		if res.total != maxi(1, roundi(s)):
			ok(false, "total %d != components %f" % [res.total, s])
			return
	ok(true, "500 mixed hits consistent")
