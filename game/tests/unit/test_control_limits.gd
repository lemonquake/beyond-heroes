extends TestCase

func _init() -> void:
	strict = true

func test_side_caps_and_old_save_refunds() -> void:
	var h := Game.new_hero(&"knight", "Balance test")
	h.progress.level = 60
	h.progress.skill_points = 0
	h.progress.talent_points = 0
	h.skill_tree.ranks = {&"cleave": 25, &"cleave_bleed": 25, &"bash_chain": 25}
	var talent_id: StringName = &""
	for n in h.talent_tree.tree.nodes:
		if n.kind == "keystone":
			talent_id = n.id
			h.talent_tree.ranks[n.id] = 25
			break
	var saved_total := h.skill_tree.points_spent()
	var saved_talents := h.talent_tree.points_spent()
	var back := HeroData.from_dict(h.to_dict())
	eq(back.skill_tree.rank(&"cleave"), 25, "main skills retain level 25")
	eq(back.skill_tree.rank(&"cleave_bleed"), 1, "one-time side ability is capped at one")
	eq(back.skill_tree.rank(&"bash_chain"), 4, "repeatable side ability is capped at four")
	eq(back.skill_tree.points_spent() + back.progress.skill_points, saved_total, "all removed skill ranks are refunded")
	ok(talent_id != &"", "a keystone was checked")
	eq(back.talent_tree.rank(talent_id), 1, "keystones are learned once")
	eq(back.talent_tree.points_spent() + back.progress.talent_points, saved_talents, "removed talent ranks are refunded")
	eq(back.skill_tree.can_rank_up(&"bash_chain", 100, 60), "Maximum rank", "cannot purchase a fifth side rank")
	var again := HeroData.from_dict(back.to_dict())
	eq(again.progress.skill_points, back.progress.skill_points, "loading again cannot duplicate refunds")
	eq(again.progress.talent_points, back.progress.talent_points, "talent refunds happen once")
	back.skill_tree.ranks[&"bash_chain"] = 999
	eq(back.skill_upgrades(&"shield_bash"), again.skill_upgrades(&"shield_bash"), "runtime effects also clamp invalid side ranks")
	done()

func test_skill_and_network_force_caps() -> void:
	for sk: SkillDef in DB.skills.values():
		var p := sk.resolve(999, {"knockback": 1e9, "launch": 1e9})
		eq(p.knockback, DamagePipeline.MAX_KNOCKBACK, "%s caps knockback after upgrades" % sk.id)
		eq(p.launch, DamagePipeline.MAX_LAUNCH, "%s caps launch after upgrades" % sk.id)
	var cleaned := NetGuard.clean_result({"knockback": 1e9, "tags": {&"launch": 1e9}})
	eq(cleaned.knockback, DamagePipeline.MAX_KNOCKBACK, "network knockback follows the gameplay cap")
	eq(cleaned.tags[&"launch"], DamagePipeline.MAX_LAUNCH, "network launch follows the gameplay cap")
	done()

func test_repeated_poise_breaks_do_not_extend_knockover() -> void:
	var st := StatusController.new()
	st.max_poise = 10.0
	var hit := DamageResult.new()
	hit.poise_damage = 1000.0
	st.receive_hit(hit)
	for i in 45:
		st.tick(1.0 / 60.0)
		st.receive_hit(hit)
	st.tick(0.01)
	ok(not st.has(&"staggered"), "repeated poise damage cannot extend stagger beyond 0.75 seconds")
	st.receive_hit(hit)
	ok(not st.has(&"staggered"), "recovery prevents another knockover")
	st.tick(StatusController.STAGGER_RECOVERY)
	st.receive_hit(hit)
	ok(st.has(&"staggered"), "poise breaks work again after recovery")
	st.clear()
	st.status_res = 1.0
	st.apply(&"staggered")
	ok(not st.has(&"staggered"), "full resistance cannot create an infinite stagger")
	done()

func test_repeated_pushes_have_bounded_travel_and_recovery() -> void:
	var a := Actor.new()
	host.add_child(a)
	a.position = Vector3(0, 10, 0)
	a.apply_knockback(Vector3.RIGHT, 8.0, null, null)
	a.apply_knockback(Vector3.RIGHT, 8.0, null, null)
	eq(a.knock_velocity.length(), 8.0, "repeated hits do not add momentum")
	a.apply_knockback(Vector3(NAN, 0, 0), 12.0, null, null)
	eq(a.knock_velocity.length(), 8.0, "invalid direction is rejected")
	var origin := a.position
	for i in 45:
		a.apply_knockback(Vector3.RIGHT, 1e9, null, null)
		a.physics_move(1.0 / 60.0, Vector3.ZERO)
	ok(a.position.x - origin.x <= Actor.MAX_KNOCK_DISTANCE + 0.001, "repeated max-strength hits cannot exceed three meters")
	ok(a._knock_remaining <= 0.0, "repeated hits cannot extend the duration")
	ok(a._knock_recovery > 0.0, "episode ends with push protection")
	a.apply_knockback(Vector3.RIGHT, 1e9, null, null, 0, 1e9)
	eq(a.knock_velocity, Vector3.ZERO, "recovery prevents a fresh push")
	for i in 37:
		a.physics_move(1.0 / 60.0, Vector3.ZERO)
	a.apply_knockback(Vector3.RIGHT, 1e9, null, null)
	eq(a.knock_velocity.length(), DamagePipeline.MAX_KNOCKBACK, "push works after recovery")
	a.free()
	done()

func test_light_targets_cannot_be_relaunched_or_thrown_too_high() -> void:
	var a := Actor.new()
	host.add_child(a)
	a.position = Vector3(0, 10, 0)
	a.weight = 0.1
	a.apply_knockback(Vector3.UP, 2.0, null, null, 0, 1e9)
	eq(a._vertical, DamagePipeline.MAX_LAUNCH, "upward velocity caps after weight scaling")
	eq(a.knock_velocity.y, 0.0, "push direction cannot bypass vertical throw cap")
	var origin := a.position.y
	var peak := origin
	for i in 40:
		a.physics_move(1.0 / 60.0, Vector3.ZERO)
		peak = maxf(peak, a.position.y)
		var before := a._vertical
		a.apply_knockback(Vector3.UP, 2.0, null, null, 0, 1e9)
		eq(a._vertical, before, "airborne target cannot be relaunched at frame %d" % i)
	ok(peak - origin <= Actor.MAX_LAUNCH_HEIGHT + 0.001, "throw height stays within one meter")
	a.free()
	done()
