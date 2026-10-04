extends TestCase
## Class Transcendence signature traits (DataTranscendence.SIGNATURES, ClassSignature): every one of the twelve does
## what its text says through the real hooks (blocks, dodges, weapon attacks, paid spells, kills), stays bounded
## (caps, internal cooldowns, proc tags), masters keep their first trait, and other machines only draw allowed marks.

var world: Node3D
var player: Player
var old_fx: Node3D
var _hits: Array = []           # [victim, label] for every hit (Events.damage_dealt)

class Dummy:
	extends Actor
	var is_boss := false

func _init() -> void:
	strict = true

func _on_dmg(victim: Node, res: DamageResult, _pt: Vector3, _attacker: Node) -> void:
	if res != null and not res.evaded:
		_hits.append([victim, res.skill_name, res.total])

func setup(cls: StringName, path: Array, level := 130, weapon := &"") -> void:
	old_fx = FX.world
	world = Node3D.new()
	host.add_child(world)
	FX.world = world
	var h := Game.new_hero(cls, "Signature test")
	h.progress.level = level
	for attr in BH.ATTRIBUTES:
		h.progress.allocated[attr] = 120
	for id in path:
		eq(ClassTranscendence.transcend(h, id).ok, true, "advance to %s" % id)
	if weapon != &"":
		h.equipment.equip(DB.make_item(weapon, BH.Rarity.BASIC, 1, 130), &"main_weapon", 130, TempoRules.NO_ATTR)
	player = Player.new()
	world.add_child(player)
	player.bind(h)
	player.set_physics_process(false)
	Game.hover_target = null
	player.mark_stats_dirty()
	player.ensure_stats()
	player.stats.set_stat(&"max_hp", 10000.0)
	player.stats.set_stat(&"max_mana", 5000.0)
	player.hp = 5000.0
	player.mana = 5000.0
	player._stats_dirty = false
	player.first_person = false
	_hits.clear()
	if not Events.damage_dealt.is_connected(_on_dmg):
		Events.damage_dealt.connect(_on_dmg)

func cleanup() -> void:
	if Events.damage_dealt.is_connected(_on_dmg):
		Events.damage_dealt.disconnect(_on_dmg)
	world.free()
	FX.world = old_fx if is_instance_valid(old_fx) else null

func dummy(at: Vector3, boss := false, hp := 1000000.0) -> Dummy:
	var a := Dummy.new()
	a.is_boss = boss
	a.stats = blank_stats(120)
	a.stats.set_stat(&"max_hp", hp)
	a.stats.set_stat(&"evasion", 0.0)
	a.hp = hp
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

func hits_on(a: Node, label: String) -> int:
	return _hits.filter(func(h): return h[0] == a and String(h[1]) == label).size()

func labels(req: DamageRequest) -> Array:
	return req.more.map(func(m): return String(m[0]))

## A light attack through the real path; the first hit window (melee) or the release (ranged) runs at once.
func swing() -> TimedAction:
	player.aim_point = ahead(6.0)
	player.aim_override = player.aim_point
	player._start_light()
	var a := player.action
	if a.on_window.is_valid():
		a.on_window.call(0, true)
	if a.on_release.is_valid():
		a.on_release.call()
	player._cancel_action(true)
	return a

func sig() -> ClassSignature:
	return player.get_node_or_null(^"ClassSignature") as ClassSignature

# ---- Registry ---------------------------------------------------------------------------------------------------------

func test_every_advanced_class_has_a_signature() -> void:
	for id in DataTranscendence.CLASSES:
		ok(DataTranscendence.SIGNATURES.has(id), "%s has a signature trait" % id)
		var text := DataTranscendence.signature_text(id)
		ok(text.length() > 40 and not text.contains("{"), "%s text is filled in" % id)
		ok(String(DataTranscendence.info(id).get("armor_look", "")).length() > 20, "%s describes its class armour" % id)
	for fam in DataTranscendence.FAMILIES:
		ok(not DataTranscendence.SIGNATURES.has(fam), "%s (starting class) has none" % fam)
	var names := {}
	for id in DataTranscendence.SIGNATURES:
		names[String(DataTranscendence.SIGNATURES[id].name)] = true
	eq(names.size(), 12, "twelve distinct trait names")
	# every mark kind belongs to a real identity, and only that line may show it
	for k in ClassSignature.KIND_OWNER:
		var owner_id: StringName = ClassSignature.KIND_OWNER[k]
		ok(DataTranscendence.SIGNATURES.has(owner_id), "%s belongs to %s" % [k, owner_id])
		ok(ClassSignature.allowed(owner_id, k), "%s may show %s" % [owner_id, k])
		for other in DataTranscendence.CLASSES:
			var line := DataTranscendence.ancestry(other)
			eq(ClassSignature.allowed(other, k), line.has(owner_id), "%s / %s follows the class line" % [other, k])
	ok(not ClassSignature.allowed(&"knight", &"crest"), "a starting Knight shows no crests")
	ok(not ClassSignature.allowed(&"", &"crest"), "an unknown class shows nothing")
	ok(not ClassSignature.allowed(&"grand_paladin", &"made_up"), "unknown mark kinds are refused")
	done()

func test_traits_follow_the_class_line() -> void:
	setup(&"knight", [])
	eq(sig(), null, "a starting class has no trait node")
	cleanup()
	setup(&"knight", [&"royal_guard"])
	eq(sig().ids, [&"royal_guard"], "first transcendence: its own trait")
	cleanup()
	setup(&"knight", [&"royal_guard", &"grand_paladin"])
	eq(sig().ids, [&"royal_guard", &"grand_paladin"], "a master keeps its first trait and adds its own")
	ok(not sig().has(&"dark_general"), "the sibling master's trait is never present")
	# advancing in place rebuilds the node once
	cleanup()
	setup(&"mage", [&"arcanist"])
	var first := sig()
	ClassTranscendence.transcend(player.hero, &"archmage")
	player.refresh_class_look()
	ok(sig() != first and sig().ids == [&"arcanist", &"archmage"], "advancing swaps in the master's traits")
	var same := sig()
	player.refresh_class_look()
	eq(sig(), same, "a refresh without a change keeps the node")
	await frames(1)
	cleanup()
	done()

# ---- Knight family ------------------------------------------------------------------------------------------------------

func test_royal_aegis_crests_and_retort() -> void:
	setup(&"knight", [&"royal_guard"], 130, &"knights_arming_sword")
	await frames(1)
	var front := dummy(ahead(1.4))
	var side := dummy(ahead(3.2))
	await frames(2)
	var blocked := DamageResult.new()
	blocked.blocked = true
	blocked.total = 10
	for i in 5:
		player._on_blocked(blocked, front)
	eq(player.status.stacks(&"royal_crest"), 3, "crests stop at three")
	sig()._tick(0.016)
	eq(sig().count(&"crest"), 3, "three crests counted")
	var a := swing()
	ok(not player.status.has(&"royal_crest"), "the retort spends the crests")
	ok(hits_on(front, "Royal Retort") >= 1 and hits_on(side, "Royal Retort") >= 1, "the shield wave strikes enemies ahead")
	ok(front.status.has(&"staggered") or side.status.has(&"staggered"), "the wave staggers")
	sig()._tick(0.016)
	eq(sig().count(&"crest"), 0, "crests cleared")
	_hits.clear()
	swing()
	eq(hits_on(side, "Royal Retort"), 0, "no retort without crests")
	cleanup()
	done()

func test_retort_bonus_rides_on_the_attack() -> void:
	setup(&"knight", [&"royal_guard"], 130, &"knights_arming_sword")
	await frames(1)
	dummy(ahead(1.4))
	for i in 3:
		player.status.apply(&"royal_crest", 10.0)
	var a := TimedAction.new()
	var req := player._weapon_request(a, false, 1.0)
	ok(labels(req).has("Royal Retort"), "the attack carries Royal Retort")
	near(float(req.more[labels(req).find("Royal Retort")][1]), 1.3, 0.001, "+30% damage")
	var req2 := player._weapon_request(a, false, 1.0)
	ok(labels(req2).has("Royal Retort"), "a later hit window of the same attack keeps it")
	var b := TimedAction.new()
	ok(not labels(player._weapon_request(b, false, 1.0)).has("Royal Retort"), "the next attack does not")
	cleanup()
	done()

func test_conquerors_dread_stacks_and_caps() -> void:
	setup(&"knight", [&"royal_guard", &"dark_general"])
	await frames(1)
	player.on_valor_spent(30.0)
	eq(player.status.stacks(&"dread"), 1, "spending Valor adds Dread")
	player.on_valor_spent(0.0)
	eq(player.status.stacks(&"dread"), 1, "spending nothing adds none")
	for i in 6:
		var v := dummy(ahead(2.0), false, 10.0)
		v.die(player)
	eq(player.status.stacks(&"dread"), 5, "Dread stops at five")
	var dmg := 0.0
	var dr := 0.0
	for m in player.status.stat_modifiers():
		if m.stat == &"outgoing_damage":
			dmg += m.value
		elif m.stat == &"damage_taken":
			dr += m.value
	near(dmg, 0.10, 0.0001, "five Dread: 10% more damage")
	near(dr, -0.10, 0.0001, "five Dread: 10% less damage taken")
	sig()._tick(0.016)
	eq(sig().count(&"dread"), 5, "five Dread counted")
	ok(sig().has(&"royal_guard"), "the Dark General keeps Royal Aegis")
	cleanup()
	done()

func test_dawnbringer_every_fifth_hit_with_cooldown() -> void:
	setup(&"knight", [&"royal_guard", &"grand_paladin"], 130, &"knights_arming_sword")
	await frames(1)
	var t := dummy(ahead(1.3))
	var near_foe := dummy(ahead(-2.0))
	await frames(2)
	var hp0 := player.hp
	var r := DamageResult.new()
	r.total = 50
	var req := DamageRequest.new()
	req.tags[&"weapon"] = true
	for i in 4:
		sig().on_hit_dealt(t, r, req, null)
	eq(hits_on(near_foe, "Dawnbringer"), 0, "four hits: not yet")
	sig()._tick(0.016)
	eq(sig().count(&"sun"), 4, "four suns gathered")
	sig().on_hit_dealt(t, r, req, null)
	ok(hits_on(near_foe, "Dawnbringer") == 1 and hits_on(t, "Dawnbringer") == 1, "the fifth hit breaks the dawn on every enemy around")
	ok(player.hp > hp0, "the dawn heals the paladin")
	near(player.hp - hp0, player.max_hp() * 0.02, 1.0, "2% of Maximum HP")
	for i in 5:
		sig().on_hit_dealt(t, r, req, null)
	eq(hits_on(near_foe, "Dawnbringer"), 1, "at most once every 3 s")
	sig()._time += 3.1
	sig().on_hit_dealt(t, r, req, null)
	eq(hits_on(near_foe, "Dawnbringer"), 2, "ready again after the cooldown")
	# its own hits are procs: they never count toward the next dawn
	var proc := DamageRequest.new()
	proc.tags[&"weapon"] = true
	proc.tags[&"proc"] = true
	var before := sig()._dawn_hits
	sig().on_hit_dealt(t, r, proc, null)
	eq(sig()._dawn_hits, before, "proc hits never feed Dawnbringer")
	cleanup()
	done()

# ---- Hunter family ------------------------------------------------------------------------------------------------------

func _shot_req() -> DamageRequest:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = player.stats
	req.use_weapon = true
	req.tags[&"projectile"] = true
	req.tags[&"weapon"] = true
	return req

func test_hunters_opening_once_per_enemy() -> void:
	setup(&"ranger", [&"tracker"], 130, &"hunters_bow")
	await frames(1)
	var t := dummy(ahead(8.0))
	var req := _shot_req()
	var res := t.receive_hit(req, player, t.center())
	ok(labels(req).has("Hunter's Opening") and res.is_crit, "the first shot on a full-health enemy is a critical hit with the bonus")
	var req2 := _shot_req()
	t.receive_hit(req2, player, t.center())
	ok(not labels(req2).has("Hunter's Opening"), "never twice on the same enemy")
	var melee := DamageRequest.new()
	melee.kind = DamageRequest.Kind.ATTACK
	melee.attacker = player.stats
	var fresh := dummy(ahead(2.0))
	fresh.receive_hit(melee, player, fresh.center())
	ok(not labels(melee).has("Hunter's Opening"), "melee hits never open")
	cleanup()
	done()

func test_rooted_stance_holds_and_breaks() -> void:
	setup(&"ranger", [&"tracker", &"wildwarden"], 130, &"hunters_bow")
	await frames(1)
	player.mark_combat()
	player.velocity = Vector3.ZERO
	sig()._tick(0.5)
	ok(not player.status.has(&"rooted_stance"), "not before a second")
	sig()._tick(0.6)
	ok(player.status.has(&"rooted_stance"), "standing still in a fight roots the Wildwarden")
	eq(sig().count(&"roots"), 1, "rooted")
	var t := dummy(ahead(8.0))
	var r := DamageResult.new()
	r.total = 40
	sig().on_hit_dealt(t, r, _shot_req(), null)
	ok(t.status.has(&"slowed"), "rooted shots Slow")
	player.velocity = Vector3(4, 0, 0)
	sig()._tick(0.1)
	ok(not player.status.has(&"rooted_stance"), "moving breaks the roots")
	eq(sig().count(&"roots"), 0, "roots released")
	ok(sig().has(&"tracker"), "the Wildwarden keeps Hunter's Opening")
	cleanup()
	done()

func test_star_chart_fills_and_fires_a_shooting_star() -> void:
	setup(&"ranger", [&"tracker", &"starstrider"], 130, &"hunters_bow")
	await frames(1)
	var near_t := dummy(ahead(4.0))
	var far_t := dummy(ahead(14.0))
	var r := DamageResult.new()
	r.total = 40
	sig().on_hit_dealt(near_t, r, _shot_req(), null)
	eq(player.status.stacks(&"star_chart") if player.status.has(&"star_chart") else 0, 0, "close shots add no star")
	for i in 7:
		sig().on_hit_dealt(far_t, r, _shot_req(), null)
	eq(player.status.stacks(&"star_chart"), 5, "stars stop at five")
	sig()._tick(0.016)
	eq(sig().count(&"star"), 5, "five stars over the head")
	player.aim_point = ahead(20.0)
	player.aim_override = player.aim_point
	player._start_light()
	var a := player.action
	a.on_release.call()
	var shots := world.get_children().filter(func(n): return n is Projectile)
	eq(shots.size(), 1, "one shot")
	var pr: Projectile = shots[0]
	ok(pr.request.tags.has(&"sig_shoot") and labels(pr.request).has("Shooting Star"), "it is a Shooting Star")
	eq(pr.pierce, 99, "it pierces every enemy in line")
	near(pr.pierce_falloff, 0.6, 0.001, "later enemies take 60%")
	ok(not player.status.has(&"star_chart"), "the chart is spent")
	# the star itself adds no new star
	sig().on_hit_dealt(far_t, r, pr.request, null)
	ok(not player.status.has(&"star_chart"), "a Shooting Star never refills the chart")
	pr.free()
	player._cancel_action(true)
	cleanup()
	done()

# ---- Mage family ----------------------------------------------------------------------------------------------------------

func _spell(id: StringName) -> SkillDef:
	return DB.skill(id)

func test_runescript_runes_and_bonus() -> void:
	setup(&"mage", [&"arcanist"])
	await frames(1)
	var s := _spell(&"ar_aether_lance")
	sig().on_spell_paid(s, 0.0)
	ok(not player.status.has(&"runescript"), "a free spell writes no rune")
	for i in 5:
		sig().on_spell_paid(s, 20.0)
	eq(player.status.stacks(&"runescript"), 3, "runes stop at three")
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	sig().decorate(req)
	near(float(req.more[0][1]), 1.12, 0.0001, "three runes: 12% more spell damage")
	var atk := DamageRequest.new()
	atk.kind = DamageRequest.Kind.ATTACK
	sig().decorate(atk)
	ok(atk.more.is_empty(), "weapon attacks get nothing")
	var proc := DamageRequest.new()
	proc.kind = DamageRequest.Kind.SPELL
	proc.tags[&"proc"] = true
	sig().decorate(proc)
	ok(proc.more.is_empty(), "procs get nothing")
	sig()._tick(0.016)
	eq(sig().count(&"rune"), 3, "three runes circle the Arcanist")
	cleanup()
	done()

func test_elemental_attunement_turns_and_bolts_once_per_cast() -> void:
	setup(&"mage", [&"arcanist", &"archmage"])
	await frames(1)
	var t := dummy(ahead(6.0))
	var s := _spell(&"am_grand_convergence")
	eq(sig()._attune, 0, "starts attuned to Fire")
	sig().on_spell_paid(s, 20.0)
	eq(sig()._attune, 1, "a damaging spell turns it to Ice")
	sig().on_spell_paid(_spell(&"am_spellweave"), 20.0)
	eq(sig()._attune, 1, "a non-damaging spell does not turn it")
	var r := DamageResult.new()
	r.total = 1000
	player._cast_serial = 40
	sig().on_hit_dealt(t, r, null, s)
	eq(hits_on(t, "Attuned bolt"), 1, "the first enemy struck takes an attuned bolt")
	var bolt: Array = _hits.filter(func(h): return String(h[1]) == "Attuned bolt")
	ok(int(bolt[0][2]) > 0 and int(bolt[0][2]) <= 260, "the bolt is about 20% of the hit")
	sig().on_hit_dealt(t, r, null, s)
	eq(hits_on(t, "Attuned bolt"), 1, "once per cast")
	player._cast_serial = 41
	sig().on_hit_dealt(t, r, null, _spell(&"am_spellweave"))
	eq(hits_on(t, "Attuned bolt"), 2, "the next cast bolts again")
	var proc := DamageRequest.new()
	proc.tags[&"proc"] = true
	player._cast_serial = 42
	sig().on_hit_dealt(t, r, proc, s)
	eq(hits_on(t, "Attuned bolt"), 2, "proc hits never bolt")
	cleanup()
	done()

func test_collapse_pulls_and_damages_with_cooldown() -> void:
	setup(&"mage", [&"arcanist", &"void_sovereign"])
	await frames(1)
	var victim := dummy(ahead(8.0), false, 10.0)
	var near_foe := dummy(ahead(10.5))
	var boss := dummy(ahead(5.5), true)
	var d0 := near_foe.global_position.distance_to(victim.global_position)
	var b0 := boss.global_position.distance_to(victim.global_position)
	await frames(2)                      # the bodies reach their places in the physics space
	victim.die(player)
	var r := DamageResult.new()
	r.total = 2000
	sig().on_hit_dealt(victim, r, null, _spell(&"vs_null_lance"))
	ok(hits_on(near_foe, "Collapse") == 1 and hits_on(boss, "Collapse") == 1, "the collapse strikes enemies around the fallen")
	ok(near_foe.global_position.distance_to(victim.global_position) < d0 - 0.5, "and pulls them in")
	near(boss.global_position.distance_to(victim.global_position), b0, 0.01, "bosses are not pulled")
	var v2 := dummy(ahead(8.0), false, 10.0)
	v2.die(player)
	sig().on_hit_dealt(v2, r, null, _spell(&"vs_null_lance"))
	eq(hits_on(near_foe, "Collapse"), 1, "at most once every 2 s")
	var v3 := dummy(ahead(8.0), false, 10.0)
	v3.die(player)
	sig()._time += 2.1
	sig().on_hit_dealt(v3, r, null, null)
	eq(hits_on(near_foe, "Collapse"), 1, "weapon kills never collapse")
	cleanup()
	done()

# ---- Shadowblade family -------------------------------------------------------------------------------------------------

func test_from_the_shadows_after_a_dodge() -> void:
	setup(&"shadowblade", [&"nightstalker"], 130, &"rondel_dagger")
	await frames(1)
	var t := dummy(ahead(1.2))
	var a0 := TimedAction.new()
	ok(not labels(player._weapon_request(a0, false, 1.0)).has("From the Shadows"), "no bonus without a dodge")
	sig().on_dodge()
	ok(player.status.has(&"shadow_strike"), "a dodge readies the strike")
	sig()._tick(0.016)
	eq(sig().count(&"shade"), 2, "shade gathers")
	var a := TimedAction.new()
	var req := player._weapon_request(a, false, 1.0)
	ok(labels(req).has("From the Shadows"), "the next attack strikes from the shadows")
	ok(not player.status.has(&"shadow_strike"), "and spends it")
	var combo0 := player.resource.value
	var r := DamageResult.new()
	r.total = 50
	sig().on_hit_dealt(t, r, req, null)
	sig().on_hit_dealt(t, r, req, null)
	near(player.resource.value - combo0, 1.0, 0.001, "+1 Combo, once per attack")
	cleanup()
	done()

func test_soul_harvest_on_kills() -> void:
	setup(&"shadowblade", [&"nightstalker", &"phantom_reaper"])
	await frames(1)
	player.cooldowns[&"pr_phantom_crossing"] = 10.0
	var c0 := player.resource.value
	var v := dummy(ahead(2.0), false, 10.0)
	v.die(player)
	near(player.resource.value - c0, 1.0, 0.001, "+1 Combo")
	near(player.cooldowns[&"pr_phantom_crossing"], 8.0, 0.001, "Phantom Crossing 2 s sooner")
	var v2 := dummy(ahead(2.0), false, 10.0)
	v2.die(player)
	near(player.cooldowns[&"pr_phantom_crossing"], 8.0, 0.001, "at most once per second")
	var other := dummy(ahead(2.0), false, 10.0)
	other.die(null)
	near(player.resource.value - c0, 1.0, 0.001, "someone else's kill gives nothing")
	cleanup()
	done()

func test_blood_price_spreads_bleeding_and_heals() -> void:
	setup(&"shadowblade", [&"nightstalker", &"blood_sovereign"])
	await frames(1)
	var v := dummy(ahead(3.0), false, 10.0)
	var near_foe := dummy(ahead(4.5))
	var far_foe := dummy(ahead(9.0))
	await frames(2)
	v.status.apply(&"bleeding", 4.0, 0.0, 100.0, Elements.PHYSICAL)
	var hp0 := player.hp
	v.die(player)
	ok(near_foe.status.has(&"bleeding"), "the burst makes nearby enemies bleed")
	near(float(near_foe.status.statuses[&"bleeding"].dps), 40.0, 0.01, "at 40% of the bleed")
	ok(not far_foe.status.has(&"bleeding"), "only within 3 m")
	near(player.hp - hp0, player.max_hp() * 0.02, 1.0, "the Blood Sovereign recovers 2%")
	var dry := dummy(ahead(3.0), false, 10.0)
	sig()._time += 1.1
	var hp1 := player.hp
	dry.die(player)
	near(player.hp, hp1, 0.001, "no bleed, no price")
	cleanup()
	done()

# ---- Looks and cleanup --------------------------------------------------------------------------------------------------

func test_trait_node_cleans_up() -> void:
	setup(&"knight", [&"royal_guard"], 130, &"knights_arming_sword")
	await frames(1)
	eq(sig().get_child_count(), 0, "the trait node draws nothing on the hero")
	ok(ClassSignature.swing_color(ClassTranscendence.lineage(player.hero)).a > 0.0, "advanced classes swing in their colours")
	eq(ClassSignature.swing_color([&"knight"]).a, 0.0, "starting classes keep the weapon's own trail")
	var n := sig()
	player.queue_free()
	await frames(2)
	ok(not is_instance_valid(n), "freed with the hero")
	cleanup()
	done()

func test_remote_marks_draw_without_mechanics() -> void:
	old_fx = FX.world
	world = Node3D.new()
	host.add_child(world)
	FX.world = world
	var av := Node3D.new()
	world.add_child(av)
	var s := ClassSignature.sync(av, DataTranscendence.ancestry(&"starstrider"), true)
	ok(s != null and s.remote, "another player's Starstrider can show its bursts")
	s.show_count(&"crest", 3)
	eq(s.count(&"crest"), 0, "charges of a trait it lacks are ignored")
	s.burst(&"opening", Vector3(0, 1, 0))
	s.burst(&"retort", Vector3(0, 1, 0))
	await frames(1)
	ok(ClassSignature.sync(av, DataTranscendence.ancestry(&"ranger"), true) == null and av.get_node_or_null(^"ClassSignature") == null, "a starting class drops them")
	world.free()
	FX.world = old_fx if is_instance_valid(old_fx) else null
	done()

# ---- Talents never go empty ---------------------------------------------------------------------------------------------

## Every transcendence talent changes something at levels 60, 130 and 300: each stat it grants moves the hero's stats
## (no cap already reached by attributes alone), and each flag it grants is present.
func test_no_transcendence_talent_is_empty() -> void:
	for lvl in [60, 130, 300]:
		for id in DataTranscendence.CLASSES:
			var line := DataTranscendence.ancestry(id)
			if lvl < DataTranscendence.level_for_stage(DataTranscendence.stage_of(id)):
				continue
			var h := Game.new_hero(line[0], "Talent check")
			h.progress.add_xp(XpCurve.total_xp_for_level(lvl))
			for step in line.slice(1):
				ClassTranscendence.transcend(h, step)
			for tid in DataTranscendence.info(id).talents:
				var t: Dictionary = DataTranscendence.TALENTS[tid]
				var with := h.compute_stats()
				for f in t.get("flags", {}):
					ok(with.flag(f) > 0.0, "L%d %s: %s is active" % [lvl, tid, f])
				if not t.has("mods"):
					continue
				var floors := h.talent_tree.floors.duplicate()
				var ranks := h.talent_tree.ranks.duplicate()
				h.talent_tree.floors.erase(tid)
				h.talent_tree.ranks[tid] = 0
				var without := h.compute_stats()
				# at least one of its stats moves (a part may sit at a cap Strength or Wisdom reach alone, e.g. Block Strength)
				var moved: Array[String] = []
				for m in t.mods:
					if not is_equal_approx(with.get_stat(m[0]), without.get_stat(m[0])):
						moved.append(String(m[0]))
				ok(not moved.is_empty(), "L%d %s changes the hero's stats (%s)" % [lvl, tid, ", ".join(moved)])
				h.talent_tree.floors = floors
				h.talent_tree.ranks = ranks
	done()
