extends TestCase
## Class Transcendence, stage 2: every new behaviour family and every special hook does what its text says, with real
## casts through Player._start_skill / SkillRunner (resources paid once, statuses, caps, no recursion, cleanup).

var world: Node3D
var player: Player
var old_fx: Node3D
var _hits: Array = []           # [victim, skill name] for every hit (Events.damage_dealt)

func _on_dmg(victim: Node, res: DamageResult, _pt: Vector3, _attacker: Node) -> void:
	if res != null and not res.evaded:
		_hits.append([victim, res.skill_name])

## Hits on `a` whose skill name is exactly `name`.
func hits_on(a: Node, name: String) -> int:
	return _hits.filter(func(h): return h[0] == a and String(h[1]) == name).size()

class Dummy:
	extends Actor
	var is_boss := false
	var taunted_by: Actor
	func taunt(by: Actor, _d: float) -> void:
		taunted_by = by

func _init() -> void:
	strict = true

func setup(cls: StringName, path: Array, level := 130) -> void:
	old_fx = FX.world
	world = Node3D.new()
	host.add_child(world)
	FX.world = world
	var h := Game.new_hero(cls, "Skill test")
	h.progress.level = level
	for id in path:
		ClassTranscendence.transcend(h, id)
	player = Player.new()
	world.add_child(player)
	player.bind(h)
	player.set_physics_process(false)
	Game.hover_target = null
	player.mark_stats_dirty()
	player.ensure_stats()
	player.stats.set_stat(&"max_hp", 10000.0)
	player.stats.set_stat(&"max_mana", 5000.0)
	player.hp = 8000.0
	player.mana = 5000.0
	player._stats_dirty = false
	_hits.clear()
	if not Events.damage_dealt.is_connected(_on_dmg):
		Events.damage_dealt.connect(_on_dmg)

func cleanup() -> void:
	if Events.damage_dealt.is_connected(_on_dmg):
		Events.damage_dealt.disconnect(_on_dmg)
	world.free()
	FX.world = old_fx if is_instance_valid(old_fx) else null

func dummy(at: Vector3, boss := false) -> Dummy:
	var a := Dummy.new()
	a.is_boss = boss
	a.stats = blank_stats(120)
	a.stats.set_stat(&"max_hp", 1000000.0)
	a.stats.set_stat(&"max_mana", 100.0)
	a.stats.set_stat(&"evasion", 0.0)        # no chance misses: every check here is about what a hit does
	a.hp = 1000000.0
	a.collision_layer = BH.LAYER_ENEMY
	a.collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.8
	capsule.radius = 0.4
	shape.shape = capsule
	shape.position.y = 0.9
	a.add_child(shape)
	world.add_child(a)
	a.position = at
	a._stats_dirty = false
	return a

func frames(n: int) -> void:
	for i in n:
		await host.get_tree().physics_frame

func ahead(d: float) -> Vector3:
	return player.global_position + player.forward() * d

## Start the skill through the real path (block reasons, setup, payment) and fire its release and first window.
func cast(sid: StringName, aim := Vector3.INF) -> TimedAction:
	player.aim_point = aim if aim != Vector3.INF else ahead(4.0)
	player.aim_override = player.aim_point      # never the player's own first-person setting (tests read settings.cfg)
	player.first_person = false
	player.cooldowns.erase(sid)
	var why := player.skill_block_reason(sid)
	eq(why, "", "%s castable" % sid)
	player._start_skill(sid)
	var a := player.action
	if a == null:
		return null
	if a.on_release.is_valid():
		a.on_release.call()
	if a.on_window.is_valid():
		a.on_window.call(0, true)
	return a

func hurt(a: Actor) -> float:
	return a.max_hp() - a.hp

# ---- Knight ---------------------------------------------------------------------------------------------------------

func test_royal_guard_rush_challenge_and_standard() -> void:
	setup(&"knight", [&"royal_guard"])
	await frames(2)
	var a := dummy(ahead(1.2))
	var boss := dummy(ahead(-2.0), true)
	var mana := player.mana
	cast(&"rg_bastion_rush")
	ok(hurt(a) > 0.0, "Bastion Rush hits")
	ok(player.mana < mana, "Mana paid")
	ok(player.cooldowns.has(&"rg_bastion_rush"), "cooldown started once")
	near(player.cooldown_total[&"rg_bastion_rush"], player.skill_cooldown(&"rg_bastion_rush"), 0.01, "10 s cooldown")
	# the shield requirement
	var shield := player.hero.equipment.get_item(&"sub_weapon")
	player.hero.equipment.slots[&"sub_weapon"] = null
	player.mark_stats_dirty()
	player.ensure_stats()
	player.cooldowns.erase(&"rg_bastion_rush")
	eq(player.skill_block_reason(&"rg_bastion_rush"), "Requires a shield", "no shield, no rush")
	player.hero.equipment.slots[&"sub_weapon"] = shield
	player.mark_stats_dirty()
	player.ensure_stats()
	cast(&"rg_sovereigns_challenge")
	eq(a.taunted_by, player, "an ordinary enemy is challenged")
	eq(boss.taunted_by, null, "a boss resists the challenge")
	ok(player.status.has(&"sovereign_challenge"), "the caster still gets the protection")
	player.ensure_stats()
	ok(player.stats.get_stat(&"damage_taken", 1.0) < 0.85, "less damage taken")
	# the standard: allies inside gain block, refreshed, never stacked
	var block0 := player.stats.get_stat(&"block_chance")
	cast(&"rg_bulwark_standard", player.global_position)
	await frames(3)
	ok(player.status.has(&"rg_bulwark_standard"), "standing at the standard")
	player.mark_stats_dirty()
	player.ensure_stats()
	ok(player.stats.get_stat(&"block_chance") > block0, "more block chance near the standard")
	var zones := world.get_children().filter(func(c): return c is TranscendZone)
	eq(zones.size(), 1, "one standard")
	cast(&"rg_bulwark_standard", player.global_position)
	await frames(2)
	var live := world.get_children().filter(func(c): return c is TranscendZone and not c._ending)
	eq(live.size(), 1, "a second standard replaces the first")
	cleanup()
	done()

func test_dark_general_and_grand_paladin_spend_valor_once() -> void:
	setup(&"knight", [&"royal_guard", &"dark_general"])
	await frames(2)
	var a := dummy(ahead(1.5))
	player.resource.value = 80.0
	cast(&"dg_dread_cleave")
	ok(a.status.has(&"weakened"), "Dread Cleave weakens")
	ok(hurt(a) > 0.0, "Dread Cleave hits")
	player.resource.value = 60.0
	player.hero.talent_tree.ranks[&"dg_iron_tyrant"] = 1
	player.mark_stats_dirty()
	player.ensure_stats()
	var before := a.hp
	cast(&"dg_black_dominion", a.global_position)
	ok(player.resource.value <= 12.0, "Black Dominion spends all Valor once (only the landing hit's gain is left: %d)" % player.resource.value)
	ok(a.hp < before, "the landing strike hits at once")
	ok(player.shield_hp > 0.0, "Iron Tyrant: a barrier after spending 20+ Valor")
	var shield1 := player.shield_hp
	player.resource.value = 60.0
	player.cooldowns.erase(&"dg_black_dominion")
	cast(&"dg_black_dominion", a.global_position)
	near(player.shield_hp, shield1, 0.01, "Iron Tyrant waits its 15 s before the next barrier")
	var mid := a.hp
	await frames(40)
	ok(a.hp < mid, "the dark zone pulses")
	cast(&"dg_warbound_advance")
	ok(player.status.has(&"warbound"), "Warbound Advance braces the caster")
	cleanup()
	setup(&"knight", [&"royal_guard", &"grand_paladin"])
	await frames(2)
	var b := dummy(ahead(1.5))
	player.resource.value = 0.0
	b.rng.seed = 7
	cast(&"gp_dawn_verdict")
	var plain := hurt(b)
	b.hp = b.max_hp()
	player.resource.value = 100.0
	player.cooldowns.erase(&"gp_dawn_verdict")
	b.rng.seed = 7
	cast(&"gp_dawn_verdict")
	ok(hurt(b) > plain * 1.4, "100 Valor makes Dawn Verdict much stronger (%d vs %d)" % [hurt(b), plain])
	ok(player.resource.value <= 12.0, "and it is spent once")
	# Oath of Mercy: one ailment lifted, barrier capped to a quarter of Maximum HP
	player.status.apply(&"poisoned", 5.0)
	player.status.apply(&"slowed", 5.0)
	player.shield_hp = 0.0
	cast(&"gp_oath_of_mercy")
	ok(not player.status.has(&"poisoned"), "the worst ailment is lifted")
	ok(player.status.has(&"slowed"), "only one")
	ok(player.shield_hp > 0.0 and player.shield_hp <= player.max_hp() * 0.25 + 0.01, "barrier, at most a quarter of Maximum HP")
	# Sanctified Ground: Light pulses and capped healing
	player.hp = player.max_hp() * 0.5
	var hp0 := player.hp
	cast(&"gp_sanctified_ground", player.global_position)
	await frames(500)
	var healed := (player.hp - hp0) / player.max_hp()
	ok(healed > 0.0, "allies heal inside")
	ok(healed <= 0.0801 * (1.0 + player.stats.get_stat(&"healing")) + 0.001, "at most the cast's cap (%.3f)" % healed)
	cleanup()
	done()

# ---- Hunter ---------------------------------------------------------------------------------------------------------

func test_tracker_quarry_snares_and_volley() -> void:
	setup(&"ranger", [&"tracker"])
	await frames(2)
	var a := dummy(ahead(6.0))
	var boss := dummy(ahead(6.0) + player.forward().cross(Vector3.UP) * 1.2, true)
	cast(&"tr_quarry_mark", a.global_position)
	ok(a.status.has(&"quarry"), "the quarry is marked")
	eq(int(a.get_meta(&"quarry_by")), player.get_instance_id(), "marked for this Tracker only")
	var req := DamageRequest.new()
	req.attacker = player.stats
	req.use_weapon = false
	req.base_min = 100.0
	req.base_max = 100.0
	req.tags[&"projectile"] = true
	var other := Dummy.new()
	world.add_child(other)
	a._positional_bonuses(req, player)
	eq(req.more.filter(func(m): return m[0] == "Quarry").size(), 1, "the Tracker's own shot gets the bonus")
	var req2 := req.clone()
	req2.more.clear()
	a._positional_bonuses(req2, other)
	eq(req2.more.filter(func(m): return m[0] == "Quarry").size(), 0, "someone else's shot does not")
	# Snareline: each enemy caught once, a boss slowed instead of rooted
	cast(&"tr_snareline", ahead(6.0))
	var lines := world.get_children().filter(func(c): return c is SnareLine)
	eq(lines.size(), 1, "a line of snares")
	var line: SnareLine = lines[0]
	ok(line.points.size() >= 3, "several snares (%d)" % line.points.size())
	a.global_position = line.points[1]
	boss.global_position = line.points[2]
	await frames(10)
	ok(a.status.has(&"rooted"), "an ordinary enemy is rooted")
	ok(not boss.status.has(&"rooted") and boss.status.has(&"slowed"), "a boss is slowed instead")
	var after := a.hp
	await frames(10)
	eq(a.hp, after, "caught once per cast")
	# Trail Volley: one hit per enemy for the whole fan
	a.global_position = ahead(3.0)
	a.status.clear()
	cast(&"tr_trail_volley", a.global_position)
	await frames(20)
	eq(hits_on(a, "Trail Volley"), 1, "one shot of the seven-shot fan per enemy")
	cleanup()
	done()

func test_wildwarden_and_starstrider() -> void:
	setup(&"ranger", [&"tracker", &"wildwarden"])
	await frames(2)
	var a := dummy(ahead(5.0))
	var boss := dummy(ahead(5.0) + Vector3(1.0, 0, 0), true)
	cast(&"ww_living_thicket", a.global_position)
	await frames(4)
	ok(a.status.has(&"rooted"), "the thicket roots on first touch")
	ok(boss.status.has(&"slowed") and not boss.status.has(&"rooted"), "bosses only slowed")
	player.global_position = a.global_position + Vector3(0.5, 0, 0)
	player.hero.talent_tree.ranks[&"ww_rootbound_guard"] = 1
	player.mark_stats_dirty()
	player.ensure_stats()
	await frames(70)
	ok(player.status.has(&"rootbound"), "Rootbound Guard while standing in your own thicket")
	cast(&"ww_wardens_refuge", player.global_position)
	await frames(3)
	ok(player.shield_hp > 0.0, "the refuge shields")
	var s1 := player.shield_hp
	await frames(60)
	ok(player.shield_hp <= s1 + 0.01, "one barrier per cast")
	ok(player.status.has(&"ww_wardens_refuge"), "slow resistance inside")
	player.global_position = Vector3.ZERO
	cast(&"ww_briar_volley", ahead(6.0))
	await frames(5)
	ok(world.get_children().any(func(c): return c is AreaEffects.Hazard), "a briar patch")
	cleanup()
	setup(&"ranger", [&"tracker", &"starstrider"])
	await frames(2)
	var x := dummy(ahead(6.0))
	var y := dummy(ahead(9.0))
	player.resource.value = 80.0
	cast(&"ss_astral_pierce", x.global_position)
	await frames(15)
	ok(player.resource.value <= 12.0, "Focus spent once (%d left from the hits)" % player.resource.value)
	ok(hurt(x) > 0.0 and hurt(y) > 0.0, "pierces both")
	ok(hurt(y) < hurt(x) * 0.9, "weaker after the first (%d vs %d)" % [hurt(y), hurt(x)])
	cast(&"ss_comet_step", ahead(5.0))
	ok(player.status.has(&"comet_ready"), "Comet Step readies a shot")
	ok(player.invulnerable, "untouchable in the air")
	var bonus := player.take_comet()
	ok(bonus > 0.3, "the next shot is empowered")
	eq(player.take_comet(), 0.0, "once")
	x.hp = x.max_hp()
	cast(&"ss_constellation_rain", x.global_position)
	await frames(200)
	ok(hits_on(x, "Constellation Rain") >= 1, "the stars land")
	ok(hits_on(x, "Constellation Rain") <= 3, "at most three hits on one enemy (%d)" % hits_on(x, "Constellation Rain"))
	cleanup()
	done()

# ---- Mage -----------------------------------------------------------------------------------------------------------

func test_arcanist_circle_ward_and_lance() -> void:
	setup(&"mage", [&"arcanist"])
	await frames(2)
	var a := dummy(ahead(6.0))
	var b := dummy(ahead(9.0))
	cast(&"ar_aether_lance", a.global_position)
	await frames(30)
	ok(hits_on(a, "Aether Lance") == 1 and hits_on(b, "Aether Lance") == 1, "the lance pierces (%d, %d; %s)" % [hits_on(a, "Aether Lance"), hits_on(b, "Aether Lance"), str(_hits)])
	cast(&"ar_runic_circle", player.global_position)
	await frames(3)
	ok(player.status.has(&"runic_circle"), "inside the circle")
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	player.decorate_request(req, DB.skill(&"ar_aether_lance"))
	ok(req.more.any(func(m): return m[0] == "Runic Circle"), "paid spells are stronger in the circle")
	var req2 := DamageRequest.new()
	req2.kind = DamageRequest.Kind.SPELL
	player.decorate_request(req2, DB.skill(&"mana_siphon"))
	ok(not req2.more.any(func(m): return m[0] == "Runic Circle"), "a free spell is not")
	player.shield_hp = 0.0
	var mana0 := player.mana
	cast(&"ar_mana_ward")
	var paid := mana0 - player.mana
	ok(paid > 0.0, "the ward costs Mana")
	ok(player.shield_hp > 0.0 and player.shield_hp <= player.max_hp() * 0.4, "a capped barrier")
	near(player.shield_hp, minf(paid * 3.0, player.max_hp() * 0.3), 1.0, "sized from the Mana actually paid")
	player.ensure_stats()
	player.mana = player.max_mana() * 0.5
	var m1 := player.mana
	var hit := DamageRequest.new()
	hit.use_weapon = false
	hit.base_min = 50.0
	hit.base_max = 50.0
	player.receive_hit(hit, a)
	near(player.mana, m1, 0.01, "taking hits never drains more Mana")
	cleanup()
	done()

func test_archmage_weave_convergence_and_tempest() -> void:
	setup(&"mage", [&"arcanist", &"archmage"])
	await frames(2)
	var a := dummy(ahead(6.0))
	player.resource.value = 4.0
	cast(&"am_grand_convergence", a.global_position)
	eq(player.resource.value, 1.0, "charge spent once (then the cast adds one)")
	await frames(60)
	ok(hurt(a) > 0.0, "the convergence lands")
	# Spellweave: the next paid spell repeats once, weaker, and never again
	a.hp = a.max_hp()
	cast(&"am_spellweave")
	ok(player.status.has(&"spellweave"), "woven")
	player.hero.skill_tree.ranks[&"firebolt"] = 1
	cast(&"firebolt", a.global_position)
	ok(not player.status.has(&"spellweave"), "the weave is spent")
	await host.get_tree().create_timer(0.7).timeout
	await frames(20)
	eq(hits_on(a, "Firebolt (Spellweave)"), 1, "the bolt repeats once, woven")
	ok(hits_on(a, "Firebolt") >= 1, "and the original lands")
	cast(&"firebolt", a.global_position)
	await host.get_tree().create_timer(0.7).timeout
	await frames(20)
	eq(hits_on(a, "Firebolt (Spellweave)"), 1, "no weave without the buff (no recursion)")
	# Prismatic Tempest: element cycle and the per-enemy cap
	a.status.clear()
	cast(&"am_prismatic_tempest", a.global_position)
	await frames(300)
	ok(hits_on(a, "Prismatic Tempest") >= 3, "the tempest strikes (%d)" % hits_on(a, "Prismatic Tempest"))
	ok(hits_on(a, "Prismatic Tempest") <= 6, "never more than six times on one enemy")
	cleanup()
	done()

func test_void_sovereign_pull_penetration_and_rift() -> void:
	setup(&"mage", [&"arcanist", &"void_sovereign"])
	await frames(2)
	var center := ahead(8.0)
	var a := dummy(center + Vector3(3.5, 0, 0))
	var boss := dummy(center + Vector3(-3.5, 0, 0), true)
	cast(&"vs_event_horizon", center)
	await frames(40)
	ok(a.global_position.distance_to(center) < 3.4, "pulled toward the well")
	near(boss.global_position.distance_to(center), 3.5, 0.05, "bosses are not pulled")
	ok(hurt(a) > 0.0, "and it hurts")
	var p := player.skill_params(&"vs_null_lance")
	var req := player.runner.make_request(DB.skill(&"vs_null_lance"), p)
	near(req.pen_extra, 0.15, 0.001, "Null Lance carries extra penetration")
	player.resource.value = 5.0
	var before := boss.hp
	cast(&"vs_rift_collapse", boss.global_position)
	eq(player.resource.value, 1.0, "the rift spends the charge once")
	await frames(20)
	eq(boss.hp, before, "nothing happens before the warning ends")
	await frames(120)
	ok(boss.hp < before, "then it collapses")
	cleanup()
	done()

# ---- Shadowblade ----------------------------------------------------------------------------------------------------

func test_nightstalker_lunge_veil_execution() -> void:
	setup(&"shadowblade", [&"nightstalker"])
	await frames(2)
	var a := dummy(ahead(1.2))
	var b := dummy(ahead(1.4) + Vector3(0.6, 0, 0))
	player.resource.value = 0.0
	cast(&"ns_umbral_lunge")
	ok(player.resource.value >= 1.0 and player.resource.value <= 2.0, "Combo once per cast, not per enemy (%d)" % player.resource.value)
	cast(&"ns_gloom_veil")
	ok(player.status.has(&"stealth") and player.status.has(&"gloom_veil"), "hidden and evasive")
	player._on_hit_dealt(a, a.receive_hit(DamageRequest.new(), player), null)
	ok(not player.status.has(&"gloom_veil"), "attacking ends the veil")
	# Marked Execution: more against a marked enemy, single target
	player.resource.value = 3.0
	a.hp = a.max_hp()
	b.hp = b.max_hp()
	a.rng.seed = 11
	cast(&"ns_marked_execution")
	var plain := hurt(a)
	eq(player.resource.value, 0.0, "a finisher spends Combo")
	ok(hurt(b) == 0.0, "one target only")
	a.hp = a.max_hp()
	a.status.apply(&"marked", 8.0, 10.0)
	player.resource.value = 3.0
	player.cooldowns.erase(&"ns_marked_execution")
	a.rng.seed = 11
	cast(&"ns_marked_execution")
	ok(hurt(a) > plain * 1.15, "the mark adds damage (%d vs %d)" % [hurt(a), plain])
	cleanup()
	done()

func test_phantom_reaper_and_blood_sovereign() -> void:
	setup(&"shadowblade", [&"nightstalker", &"phantom_reaper"])
	await frames(2)
	var near_one := dummy(ahead(1.5))
	var far_one := dummy(ahead(3.0) + player.forward().cross(Vector3.UP) * 1.0)
	player.resource.value = 3.0
	near_one.rng.seed = 5
	far_one.rng.seed = 5          # the same rolls for both (crit, damage), so only the arc's share differs
	cast(&"pr_reapers_arc")
	ok(hurt(near_one) > 0.0 and hurt(far_one) > 0.0, "the arc reaches both")
	ok(hurt(far_one) < hurt(near_one) * 0.8, "the second enemy takes less")
	# afterimages: proc-tagged, so Double Attack never repeats them
	near_one.hp = near_one.max_hp()
	player.hero.skill_tree.ranks[&"double_attack"] = 25
	player.mark_stats_dirty()
	player.ensure_stats()
	cast(&"pr_afterimage_flurry")
	await host.get_tree().create_timer(1.4).timeout
	ok(hurt(near_one) > 0.0, "afterimages strike")
	eq(player.class_passives.double_cd, 0.0, "Double Attack never triggered by an afterimage")
	cast(&"pr_phantom_crossing", near_one.global_position)
	ok(player.status.has(&"phantom_evade"), "a bounded evade window")
	cleanup()
	setup(&"shadowblade", [&"nightstalker", &"blood_sovereign"])
	await frames(2)
	var a := dummy(ahead(1.4))
	cast(&"bs_crimson_rend")
	ok(a.status.has(&"bleeding") or a.status.buildup.get(&"bleeding", 0.0) > 0.0, "Crimson Rend makes it bleed")
	# Sanguine Pact never kills
	player.hp = 1.0
	cast(&"bs_sanguine_pact")
	eq(player.hp, 1.0, "the price never takes the last point of HP")
	ok(player.alive, "alive")
	player.hp = 1000.0
	player.cooldowns.erase(&"bs_sanguine_pact")
	cast(&"bs_sanguine_pact")
	near(player.hp, 880.0, 0.5, "12% of current HP")
	ok(player.status.has(&"sanguine_pact"), "the pact's window")
	# Blood Eclipse heals from damage dealt, capped per cast
	player.hp = 100.0
	a.status.apply(&"bleeding", 5.0, 0.0, 1.0)
	player.resource.value = 5.0
	cast(&"bs_blood_eclipse")
	ok(player.hp > 100.0, "heals from the damage")
	ok(player.hp - 100.0 <= player.max_hp() * 0.12 + 0.5, "never more than 12% of Maximum HP")
	cleanup()
	done()

# ---- Ranks, items, gating ---------------------------------------------------------------------------------------------

func test_rank_25_plus_items_and_text_stay_bounded() -> void:
	for id in DataTranscendence.CLASSES:
		for sid in DataTranscendence.info(id).skills:
			var s := DB.skill(sid)
			var p1 := s.resolve(1)
			var p30 := s.resolve(30)
			for k in s.per_rank:
				ok(float(p30[k]) >= float(p1[k]), "%s %s grows" % [sid, k])
			if p30.has("dash"):
				ok(float(p30.dash) <= 8.0, "%s dash capped" % sid)
			ok(Tips.skill_text(s, p30).find("{") < 0, "%s text fully filled at rank 30" % sid)
			ok(Tips.skill_text(s, p1).find("{") < 0, "%s text fully filled at rank 1" % sid)
		for tid in DataTranscendence.info(id).talents:
			ok(DataTranscendence.talent_text(tid, 1).find("{") < 0, "%s text filled" % tid)
			ok(DataTranscendence.talent_text(tid, 25).find("{") < 0, "%s rank 25 text filled" % tid)
	# talent growth is diminishing and capped
	near(TreeDef.rank_power(25, 1, DataTranscendence.TAIL), 7.0, 0.001, "rank 25 = 7x rank 1")
	near(DataTranscendence.cap(&"pr_finisher", 0.03 * 7.0 * 2.0), 0.25, 0.001, "flag caps hold with item ranks")
	done()

func test_sibling_skill_cannot_run_even_when_forced() -> void:
	setup(&"knight", [&"royal_guard", &"grand_paladin"])
	await frames(2)
	player.hero.skill_tree.ranks[&"dg_dread_cleave"] = 5
	eq(player.skill_block_reason(&"dg_dread_cleave"), "Not learned", "the HUD refuses the sibling skill")
	var s := DB.skill(&"dg_dread_cleave")
	var a := TimedAction.from_anim(s.anim, 1.0)
	ok(not player.runner.setup(s, s.resolve(5), a), "SkillRunner refuses it too")
	cleanup()
	done()

func test_talent_flags_reach_their_hooks() -> void:
	setup(&"ranger", [&"tracker", &"starstrider"])
	await frames(2)
	player.hero.talent_tree.ranks[&"ss_steady_constellation"] = 5
	player.hero.talent_tree.ranks[&"ss_comet_rhythm"] = 1
	player.mark_stats_dirty()
	player.ensure_stats()
	ok(player.resource.decay_mult < 1.0 and player.resource.decay_mult >= 0.5, "Focus fades slower out of combat, bounded")
	player.cooldowns[&"ss_astral_pierce"] = 10.0
	var crit := DamageResult.new()
	crit.is_crit = true
	crit.total = 10
	var t := dummy(ahead(3.0))
	player._on_hit_dealt(t, crit, null)
	ok(player.cooldowns[&"ss_astral_pierce"] < 10.0, "a crit trims cooldowns")
	var cd1: float = player.cooldowns[&"ss_astral_pierce"]
	player._on_hit_dealt(t, crit, null)
	near(player.cooldowns[&"ss_astral_pierce"], cd1, 0.001, "at most once per second")
	cleanup()
	setup(&"shadowblade", [&"nightstalker"])
	await frames(2)
	player.hero.talent_tree.ranks[&"ns_patient_blade"] = 25
	player.hero.skill_tree.ranks[&"shadow_discipline"] = 25
	player.mark_stats_dirty()
	player.ensure_stats()
	ok(player.resource.decay_delay_bonus <= ClassResource.COMBO_LINGER_CAP + 0.001, "Combo lingering capped at 4 s")
	player.hero.talent_tree.ranks[&"ns_ambush_training"] = 1
	player.mark_stats_dirty()
	player.ensure_stats()
	player.status.apply(&"stealth", 2.0)
	player._transcend_tick()
	player.status.remove(&"stealth")
	player._transcend_tick()
	ok(player.status.has(&"ambush_ready"), "Ambush Training after Stealth ends")
	cleanup()
	done()
