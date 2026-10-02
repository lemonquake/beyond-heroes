extends TestCase
## bh-032: what another machine may send. A modified client must not be able to stall the room, flood it, or pass a wrong
## type or a NaN into a handler. These cover NetGuard directly; tools/net_probe_hostile exercises the live handlers.

func _init() -> void:
	strict = true

func test_rate_limit_allows_a_burst_then_refills() -> void:
	NetGuard.reset()
	var t := 1000
	var allowed := 0
	for i in 20:
		if NetGuard.allow(7, "chat", 1.0, 5.0, t):
			allowed += 1
	eq(allowed, 5, "a burst of 5 passes, the rest is dropped")
	ok(not NetGuard.allow(7, "chat", 1.0, 5.0, t), "still empty at the same instant")
	ok(NetGuard.allow(7, "chat", 1.0, 5.0, t + 1100), "one message is allowed again a second later")
	ok(NetGuard.allow(8, "chat", 1.0, 5.0, t), "another peer has its own allowance")
	ok(NetGuard.allow(7, "ping", 1.0, 5.0, t), "another message kind has its own allowance")
	NetGuard.forget(7)
	ok(NetGuard.allow(7, "chat", 1.0, 5.0, t), "forgetting a departed peer clears its bucket")
	NetGuard.reset()
	done()

func test_rate_never_exceeds_the_burst_after_a_long_pause() -> void:
	NetGuard.reset()
	ok(NetGuard.allow(3, "hit", 40.0, 80.0, 0), "first hit")
	var n := 0
	for i in 200:
		if NetGuard.allow(3, "hit", 40.0, 80.0, 3_600_000):
			n += 1
	eq(n, 80, "an hour of silence still only buys the burst")
	NetGuard.reset()
	done()

func test_profile_is_cleaned() -> void:
	var good := {"name": "Aldric", "cls": "knight", "level": 12, "map": "sanctuary", "dungeon_level": 12, "device": "PC", "guild": {}}
	var clean := NetGuard.clean_profile(good)
	eq(clean.name, "Aldric", "a normal profile keeps its name")
	eq(clean.level, 12, "and its level")
	var evil := {"name": "X".repeat(500), "cls": "knight", "level": 999999, "map": "m".repeat(1000), "device": "PC", "extra": "y".repeat(100)}
	clean = NetGuard.clean_profile(evil)
	eq(clean.name.length(), 18, "names are cut to 18 characters")
	eq(clean.level, BH.LEVEL_CAP, "levels are capped")
	eq(clean.map.length(), 64, "map ids are bounded")
	ok(not clean.has("extra"), "unknown keys are dropped")
	eq(NetGuard.clean_profile({"name": "Big", "blob": "z".repeat(NetGuard.MAX_PROFILE_BYTES + 10)}), {}, "an oversized profile is refused")
	eq(NetGuard.clean_profile("nope"), {}, "a non-dictionary profile is refused")
	eq(NetGuard.clean_profile({"level": NAN, "name": "N"}).level, 1, "NaN level falls back to 1")
	done()

func _pack(pos := Vector3(1, 0, 2)) -> Array:
	return [{"k": "p", "s": [pos, 0.5, Vector3.ZERO, 100.0, 120.0, true, "idle", 1, 1.0, false, false, 7]}]

func test_ally_pack_validation() -> void:
	ok(NetGuard.ally_pack_ok(_pack()), "a real snapshot passes")
	ok(not NetGuard.ally_pack_ok(_pack(Vector3(NAN, 0, 0))), "NaN position is refused")
	ok(not NetGuard.ally_pack_ok(_pack(Vector3(INF, 0, 0))), "infinite position is refused")
	ok(not NetGuard.ally_pack_ok("hello"), "a string is not a snapshot")
	ok(not NetGuard.ally_pack_ok([5]), "an entry that is not a dictionary is refused")
	ok(not NetGuard.ally_pack_ok([{"k": "p", "s": [1, 2]}]), "a short state array is refused")
	ok(not NetGuard.ally_pack_ok([{"k": 5, "s": []}]), "a non-string key is refused")
	var many := []
	for i in NetGuard.MAX_ALLIES_PER_PACK + 1:
		many.append(_pack()[0])
	ok(not NetGuard.ally_pack_ok(many), "more allies than the limit is refused")
	var wrong := _pack()
	wrong[0].s[5] = "alive"
	ok(not NetGuard.ally_pack_ok(wrong), "alive must be a boolean")
	done()

func test_reported_hit_is_clamped_and_typed() -> void:
	var legit := {"total": 340, "healed": 0, "is_crit": true, "evaded": false, "dominant_element": 2, "components": {0: 200.0, 2: 140.0},
		"buildup": {&"burning": 30.0}, "reactions": ["melt"], "tags": {&"push_dir": Vector3(1, 0, 0), &"launch": 0.0}, "knockback": 4.0}
	var clean := NetGuard.clean_result(legit)
	eq(clean.total, 340, "a normal hit keeps its damage")
	ok(clean.total is int, "damage stays an integer")
	eq(clean.components[2], 140.0, "components survive")
	eq(clean.buildup[&"burning"], 30.0, "status buildup survives")
	eq(clean.reactions, ["melt"], "reactions survive")
	eq(NetGuard.clean_result({"total": 5e12}).total, int(NetGuard.HIT_DAMAGE_CAP), "an impossible blow is clamped")
	eq(NetGuard.clean_result({"total": -500}).total, 0, "negative damage cannot heal a monster")
	eq(NetGuard.clean_result({"total": NAN}), {}, "NaN damage refuses the whole hit")
	eq(NetGuard.clean_result({"total": INF}), {}, "infinite damage refuses the whole hit")
	eq(NetGuard.clean_result(["total"]), {}, "a non-dictionary hit is refused")
	var dirty := NetGuard.clean_result({"total": 1, "buildup": {&"x": 9999.0, "name_" + "y".repeat(40): 5.0}, "tags": {&"push_dir": Vector3(NAN, 0, 0), &"launch": 1e9}})
	eq(dirty.buildup[&"x"], 100.0, "buildup is capped at 100")
	eq(dirty.buildup.size(), 1, "overlong status names are dropped")
	eq(dirty.tags[&"push_dir"], Vector3.ZERO, "a NaN push direction becomes none")
	eq(dirty.tags[&"launch"], DamagePipeline.MAX_LAUNCH, "launch is capped")
	var decoded := NetCodec.decode_result(clean)
	eq(decoded.total, 340, "the cleaned hit decodes into a DamageResult")
	ok(decoded.reactions.has(&"melt"), "with its reaction")
	done()

func test_fits_measures_nested_payloads() -> void:
	ok(NetGuard.fits({"a": [1, 2, 3]}, 200), "small payloads fit")
	ok(not NetGuard.fits({"a": "x".repeat(5000)}, 1000), "large payloads do not")
	done()
