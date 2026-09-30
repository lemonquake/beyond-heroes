extends TestCase

func _init() -> void:
	strict = true

func test_exact_codes_null_hero_and_documentation() -> void:
	eq(Cheats.CODES.size(), 26, "all current cheat codes")
	eq(Cheats.DESCRIPTIONS.size(), Cheats.CODES.size(), "complete reference")
	for code in Cheats.CODES:
		ok(Cheats.DESCRIPTIONS.has(code), "documented " + code)
		ok(Cheats.is_code("  " + code.to_upper() + "  "), "case and whitespace " + code)
		ok(not Cheats.is_code(code + " please"), "whole message only")
		ok(Cheats.apply(code, null).contains("No hero"), "null hero handled")
	eq(Cheats.apply("ordinary chat", null), "", "chat is not a cheat")
	done()

func test_requested_points_repeat_and_save() -> void:
	var h := Game.new_hero(&"knight", "Cheats")
	var gold := h.inventory.gold
	var sp := h.progress.skill_points
	var fp := h.progress.free_points
	var tp := h.progress.talent_points
	var notifications := [0]
	h.progress.points_changed.connect(func(): notifications[0] += 1)
	for i in 2:
		Cheats.apply(" ASDF ", h)
		Cheats.apply("LEL", h)
		Cheats.apply("jjwp", h)
	Cheats.apply("talenttime", h)
	eq(h.inventory.gold, gold + 100000, "exact gold")
	eq(h.progress.skill_points, sp + 20, "exact skill points")
	eq(h.progress.free_points, fp + 40, "exact stat points")
	eq(h.progress.talent_points, tp + 10, "exact talent points")
	eq(notifications[0], 5, "UI notifications emitted")
	var restored := HeroData.from_dict(h.to_dict())
	eq(restored.inventory.gold, h.inventory.gold, "gold persists")
	eq(restored.progress.to_dict(), h.progress.to_dict(), "point pools persist")
	Cheats.apply("deep pockets", h)
	eq(h.inventory.gold, gold + 200000, "extra gold code")
	done()

func test_item_gifts_and_full_bag_are_atomic() -> void:
	var h := Game.new_hero(&"mage", "Supplies")
	for pair in [["redbottle", &"health_potion", 20], ["bluebottle", &"mana_potion", 20], ["homeward", &"town_portal", 10], ["embers", &"soul_ember", 100]]:
		var before := h.inventory.count_of(pair[1])
		ok(Cheats.apply(pair[0], h).begins_with("Cheat: +"), "gift reports added count")
		eq(h.inventory.count_of(pair[1]), before + pair[2], "all requested items added")
	# Leave a partially filled compatible stack, but insufficient room for the whole gift.
	h.inventory = Inventory.new(1)
	var potion := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 1)
	potion.count = 19
	h.inventory.add(potion)
	var before := h.inventory.to_array()
	ok(Cheats.apply("redbottle", h).contains("nothing added"), "full gift refused")
	eq(h.inventory.to_array(), before, "not even a partial stack changes")
	ok(Cheats.apply("embers", h).contains("nothing added"), "no room for embers")
	eq(h.inventory.to_array(), before, "full inventory untouched")
	done()

func test_level_cap_rest_refund_and_tempo_revival() -> void:
	var h := Game.new_hero(&"knight", "Utility")
	Cheats.apply("oneup", h)
	eq(h.progress.level, 2, "one level")
	h.progress.add_xp(XpCurve.total_xp_for_level(BH.LEVEL_CAP) - h.progress.total_xp)
	ok(Cheats.apply("oneup", h).contains("cap"), "oneup respects cap")
	var free := h.progress.free_points
	ok(h.progress.allocate(&"str", 3), "allocate three points")
	Cheats.apply("freshstart", h)
	eq(h.progress.free_points, free, "refund exactly spent points")
	eq(h.progress.allocated[&"str"], 0, "allocation cleared")
	Cheats.apply("freshstart", h)
	eq(h.progress.free_points, free, "repeat refund does not duplicate points")
	h.play_time = 123
	Cheats.apply("wellrested", h)
	near(h.rested_seconds_left(), 1800.0, 0.01, "thirty minutes")
	h.rested_until += 1000
	Cheats.apply("wellrested", h)
	near(h.rested_seconds_left(), 2800.0, 0.01, "longer rest is preserved")
	var fallen := TempoData.new()
	fallen.uid = 1
	fallen.fallen = true
	fallen.hp_frac = 0
	fallen.mana_frac = 0
	var living := TempoData.new()
	living.uid = 2
	living.hp_frac = 0.3
	h.tempos = [fallen, living]
	var gold := h.inventory.gold
	ok(Cheats.apply("secondwind", h).contains("1 fallen"), "revival count")
	ok(not fallen.fallen, "revived")
	eq(fallen.hp_frac, 1.0, "full HP")
	eq(fallen.mana_frac, 1.0, "full mana")
	near(living.hp_frac, 0.3, 0.001, "living spirit unchanged")
	eq(h.inventory.gold, gold, "revival is free")
	ok(Cheats.apply("secondwind", h).contains("0 fallen"), "repeat safe")
	var restored := HeroData.from_dict(h.to_dict())
	ok(not restored.tempos[0].fallen, "revival persists")
	eq(restored.rested_until, h.rested_until, "rest persists")
	done()
