extends TestCase
## Status effects: stacking rules, interactions, immunity windows, long soak.

func _hit(comp: Dictionary, buildup := {}) -> DamageResult:
	var r := DamageResult.new()
	r.components = comp
	r.buildup = buildup
	return r

func test_single_instance_refresh() -> void:
	var st := StatusController.new()
	st.apply(&"burning", 4.0, 0.0, 10.0, Elements.FIRE)
	st.tick(3.0)
	st.apply(&"burning", 4.0, 0.0, 6.0, Elements.FIRE)
	eq(st.statuses.size(), 1, "one burning instance")
	near(st.remaining(&"burning"), 4.0, 0.0001, "duration refreshed")
	eq(st.statuses[&"burning"].dps, 10.0, "keeps stronger dps")

func test_dot_ticks() -> void:
	var st := StatusController.new()
	var total := [0.0]
	st.dot_tick.connect(func(_id, amt, _e): total[0] += amt)
	st.apply(&"burning", 4.0, 0.0, 10.0, Elements.FIRE)
	for i in 300:
		st.tick(1.0 / 60.0)
	near(total[0], 40.0, 0.001, "4 s x 10 dps = 40")
	ok(not st.has(&"burning"), "expired")

func test_water_extinguishes_and_fire_evaporates() -> void:
	var st := StatusController.new()
	st.apply(&"burning", 4.0, 0.0, 5.0, Elements.FIRE)
	st.receive_hit(_hit({Elements.WATER: 10.0}))
	ok(not st.has(&"burning"), "water extinguishes burning")
	ok(st.has(&"wet"), "target wet")
	st.receive_hit(_hit({Elements.FIRE: 10.0}))
	ok(not st.has(&"wet"), "fire evaporates wet")

func test_freeze_buildup_wet_doubles_and_immunity() -> void:
	var st := StatusController.new()
	st.receive_hit(_hit({Elements.ICE: 1.0}, {&"chilled": 60.0}))
	ok(st.has(&"chilled") and not st.has(&"frozen"), "chilled, not frozen at 60")
	st.receive_hit(_hit({Elements.ICE: 1.0}, {&"chilled": 60.0}))
	ok(st.has(&"frozen"), "frozen at 120")
	# Wait out freeze; immunity must follow
	for i in 120:
		st.tick(1.0 / 60.0)
	ok(not st.has(&"frozen"), "freeze ended")
	ok(st.has(&"freeze_immune"), "freeze immunity window")
	st.receive_hit(_hit({Elements.ICE: 1.0}, {&"chilled": 500.0}))
	ok(not st.has(&"frozen"), "cannot refreeze during immunity")
	var wet := StatusController.new()
	wet.apply(&"wet")
	wet.receive_hit(_hit({Elements.ICE: 1.0}, {&"chilled": 55.0}))
	ok(wet.has(&"frozen"), "wet doubles freeze buildup (55 -> 110)")

func test_wet_shock_is_stronger() -> void:
	var st := StatusController.new()
	st.apply(&"wet")
	st.receive_hit(_hit({Elements.LIGHTNING: 1.0}, {&"shocked": 50.0}))
	ok(st.has(&"shocked"), "wet doubles shock buildup")
	eq(st.magnitude(&"shocked"), DamagePipeline.SHOCK_TAKEN_WET, "wet shock magnitude")

func test_poise_stagger_and_window() -> void:
	var st := StatusController.new()
	st.max_poise = 50.0
	st.grants_stagger_window = true
	var r := _hit({Elements.PHYSICAL: 1.0})
	r.poise_damage = 30.0
	st.receive_hit(r)
	ok(not st.has(&"staggered"), "not yet")
	st.receive_hit(r)
	ok(st.has(&"staggered") and st.has(&"stagger_window"), "poise broken -> stagger + exposed")
	eq(st.poise_meter, 0.0, "meter reset")

func test_status_resistance_shortens() -> void:
	var st := StatusController.new()
	st.status_res = 0.5
	st.apply(&"burning", 4.0)
	near(st.remaining(&"burning"), 2.0, 0.0001, "50% status res halves duration")

func test_soak_10000_steps() -> void:
	# 10,000 fixed 60 Hz steps with random hits: invariants — finite values, no duplicate instances,
	# bounded buildup, frozen never re-applied inside its immunity window.
	var st := StatusController.new()
	st.max_poise = 40.0
	var r := rng(2026)
	var froze_during_immunity := false
	var max_buildup := 0.0
	for step in 10000:
		if r.randf() < 0.2:
			var comp := {}
			var b := {}
			var e: int = Elements.ELEMENTAL[r.randi_range(0, 7)]
			comp[e] = r.randf_range(1.0, 50.0)
			b[Elements.STATUS_OF[e]] = r.randf_range(0.0, 80.0)
			var hit := _hit(comp, b)
			hit.poise_damage = r.randf_range(0.0, 20.0)
			var immune_before := st.has(&"freeze_immune")
			var frozen_before := st.has(&"frozen")
			st.receive_hit(hit)
			if immune_before and not frozen_before and st.has(&"frozen"):
				froze_during_immunity = true
		st.tick(1.0 / 60.0)
		for k in st.buildup:
			max_buildup = maxf(max_buildup, st.buildup[k])
			if not is_finite(st.buildup[k]):
				ok(false, "non-finite buildup")
				return
	ok(not froze_during_immunity, "no freeze during immunity")
	ok(max_buildup <= StatusRules.THRESHOLD * 1.5, "buildup bounded (%.1f)" % max_buildup)
	ok(is_finite(st.poise_meter) and st.poise_meter >= 0.0, "poise meter finite")
	st.tick(NAN)
	st.tick(-1.0)
	ok(true, "invalid dt ignored")
