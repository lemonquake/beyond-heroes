extends TestCase
## XP curve, multi-level carry-over, trees (prerequisites, refunds, exclusivity).

func _hero(cls_id := &"knight") -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls_id), "Test")
	h.init_new()
	return h

func test_xp_curve_values() -> void:
	eq(XpCurve.xp_to_next(1), 200, "L1 -> 200")
	eq(XpCurve.xp_to_next(10), int(floor(80.0 * pow(10.0, 1.75) + 1200.0)), "L10")
	ok(XpCurve.xp_to_next(20) > XpCurve.xp_to_next(19), "monotonic")
	eq(XpCurve.xp_to_next(BH.LEVEL_CAP), 0, "no xp at cap")
	# Kills to level stays within a sane band (not absurdly grindy).
	for l in [1, 10, 20, 40]:
		var kills := float(XpCurve.xp_to_next(l)) / float(XpCurve.monster_xp(l))
		ok(kills > 5.0 and kills < 120.0, "kills per level at %d = %.1f" % [l, kills])

func test_multi_level_carry_over() -> void:
	var h := _hero()
	var need := XpCurve.xp_to_next(1) + XpCurve.xp_to_next(2) + XpCurve.xp_to_next(3)
	var gained := h.progress.add_xp(need + 37)
	eq(gained, 3, "three levels at once")
	eq(h.progress.level, 4, "level 4")
	eq(h.progress.xp, 37, "remainder carried over")
	eq(h.progress.free_points, 9, "3 attribute points per level")
	eq(h.progress.skill_points, 3, "skill points")
	eq(h.progress.talent_points, 3, "talent points")
	eq(h.progress.total_xp, need + 37, "total xp")
	# Growth applied
	eq(h.progress.base_attributes()[&"str"], 14 + roundi(1.5 * 3), "strength growth")

func test_level_cap() -> void:
	var h := _hero()
	h.progress.add_xp(XpCurve.total_xp_for_level(BH.LEVEL_CAP) + 999999)
	eq(h.progress.level, BH.LEVEL_CAP, "capped")
	eq(h.progress.xp, 0, "no overflow at cap")
	eq(h.progress.add_xp(1000), 0, "no gain past cap")

func test_attribute_allocation() -> void:
	var h := _hero()
	h.progress.free_points = 2
	ok(h.progress.allocate(&"dex", 2), "allocate 2")
	ok(not h.progress.allocate(&"dex", 1), "cannot overspend")
	eq(h.compute_stats().get_stat(&"dex"), 12.0, "dex applied")

func test_skill_tree_prerequisites_and_refunds() -> void:
	var h := _hero()
	h.progress.level = 20
	h.progress.skill_points = 20
	ok(h.spend_skill_point(&"whirlwind") != "", "whirlwind locked without its prerequisite")
	eq(h.spend_skill_point(&"cleave_wide"), "", "great arc (requires cleave)")
	eq(h.spend_skill_point(&"whirlwind"), "", "whirlwind now available")
	ok(h.skill_bar.has(&"whirlwind"), "auto-assigned to bar")
	ok(h.refund_skill_point(&"cleave_wide") != "", "cannot refund a node others depend on")
	eq(h.spend_skill_point(&"cleave_bleed"), "", "second parent")
	eq(h.refund_skill_point(&"cleave_wide"), "", "refund ok when an alternative parent exists")
	var pts := h.progress.skill_points
	eq(h.refund_skill_point(&"whirlwind"), "", "refund whirlwind")
	eq(h.progress.skill_points, pts + 1, "point returned")
	ok(not h.skill_bar.has(&"whirlwind"), "removed from bar")
	h.progress.level = 1
	ok(h.spend_skill_point(&"leap_slam") != "", "level requirement enforced")

func test_skill_upgrades_modify_params() -> void:
	var h := _hero(&"mage")
	h.progress.level = 10
	h.progress.skill_points = 10
	var base := h.resolved_skill(&"firebolt")
	eq(base.explode_radius, 0.0, "no explosion at base")
	h.spend_skill_point(&"firebolt")
	h.spend_skill_point(&"firebolt_explode")
	var up := h.resolved_skill(&"firebolt")
	eq(up.explode_radius, 2.2, "upgrade adds explosion")
	eq(up.rank, 2, "rank 2")
	near(up.damage_min, 9.0 + 3.0, 0.0001, "rank scaling")

func test_talent_tree_gates_and_keystone_exclusivity() -> void:
	var h := _hero()
	h.progress.level = 30
	h.progress.talent_points = 40
	ok(h.spend_talent_point(&"k_crit_cd") != "", "major node needs path")
	h.spend_talent_point(&"k_str")
	h.spend_talent_point(&"k_sword")
	h.spend_talent_point(&"k_heavy")
	ok(h.spend_talent_point(&"k_crit_cd").contains("points spent"), "tree point gate (%s)" % h.talent_tree.can_rank_up(&"k_crit_cd", 10, 30))
	h.spend_talent_point(&"k_str")
	h.spend_talent_point(&"k_str")
	eq(h.spend_talent_point(&"k_crit_cd"), "", "gate satisfied")
	# Build toward both keystones
	for id in [&"k_vit", &"k_armor", &"k_block", &"k_block_mana", &"k_spi", &"k_momentum", &"k_earth", &"k_frozen"]:
		eq(h.spend_talent_point(id), "", "learn %s" % id)
	eq(h.spend_talent_point(&"k_unbreakable"), "", "first keystone")
	ok(h.spend_talent_point(&"k_juggernaut").begins_with("Excludes"), "keystones exclusive")
	ok(h.compute_stats().has_flag(&"unstaggerable"), "keystone flag active")
