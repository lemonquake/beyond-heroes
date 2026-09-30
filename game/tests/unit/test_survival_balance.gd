extends TestCase
## Regression coverage for pools, save migration, aimed attacks, retaliation and travel limits.

func _init() -> void:
	strict = true

func test_attribute_pools_and_level_rewards() -> void:
	for cid in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := Game.new_hero(cid, "Survival")
		var cls := h.cls.duplicate() as ClassDef
		cls.class_modifiers = []
		var base := StatCalculator.compute(cls, 1, {}, [], WeaponLoadout.new())
		for row in [[&"str", &"max_hp", 6.0], [&"wis", &"max_hp", 4.0], [&"int", &"max_mana", 4.0], [&"spi", &"max_mana", 3.0]]:
			var added := StatCalculator.compute(cls, 1, {row[0]: 10}, [], WeaponLoadout.new())
			eq(added.get_stat(row[1]) - base.get_stat(row[1]), row[2] * 10, "%s contribution for %s" % [row[0], cid])
		h.progress.add_xp(XpCurve.total_xp_for_level(40))
		eq(h.progress.free_points, 390, "39 levels grant 390 stat points")
		eq(h.progress.skill_points, 78, "39 levels grant 78 skill points")
		eq(h.progress.talent_points, 39, "talent reward retained")
	done()

func test_old_save_gets_missing_points_once() -> void:
	var h := Game.new_hero(&"mage", "Old save")
	var data := h.to_dict()
	var old: Dictionary = data.progress
	old.erase("point_rules_version")
	old.level = 40
	old.free_points = 12
	old.skill_points = 3
	old.allocated = {"int": 100, "wis": 5}
	var loaded := HeroData.from_dict(data)
	eq(loaded.progress.free_points, 285, "273 missing stat points credited")
	eq(loaded.progress.skill_points, 42, "39 missing skill points credited")
	eq(loaded.progress.allocated[&"int"], 100, "existing allocation retained")
	var again := HeroData.from_dict(loaded.to_dict())
	eq(again.progress.to_dict(), loaded.progress.to_dict(), "reload does not grant twice")
	loaded.progress.add_xp(XpCurve.xp_to_next(40))
	eq(loaded.progress.free_points, 295, "new level grants ten after migration")
	eq(loaded.progress.skill_points, 44, "new level grants two after migration")
	done()

func test_evasion_and_dexterity_affect_real_aimed_hits() -> void:
	var cls := DB.class_def(&"knight")
	var target := StatCalculator.compute(cls, 40, {&"agi": 100}, [], WeaponLoadout.new())
	var low := StatCalculator.compute(cls, 40, {&"dex": 20}, [], WeaponLoadout.new())
	var high := StatCalculator.compute(cls, 40, {&"dex": 180}, [], WeaponLoadout.new())
	var low_hits := 0
	var high_hits := 0
	for kind in [DamageRequest.Kind.ATTACK, DamageRequest.Kind.SPELL]:
		var random := rng(410)
		for attacker in [low, high]:
			var hits := 0
			var req := DamageRequest.new()
			req.attacker = attacker
			req.target = target
			req.kind = kind
			req.use_weapon = false
			req.base_min = 20
			req.base_max = 20
			req.can_crit = false
			req.blockable = false
			for i in 2000:
				hits += int(not DamagePipeline.compute(req, random).evaded)
			if attacker == low:
				low_hits = hits
			else:
				high_hits = hits
			req.evadable = false
			ok(not DamagePipeline.compute(req, random).evaded, "unavoidable effects remain unavoidable")
		ok(low_hits < 1100, "AGI avoids a meaningful share of aimed hits")
		ok(high_hits > low_hits + 400, "DEX counters AGI in the pipeline")
	near(target.get_stat(&"evade_chance"), DamagePipeline.evade_chance(200, 186), 0.00001, "sheet uses actual reference accuracy growth")
	done()

func test_movement_caps_after_side_passives_and_large_physics_steps() -> void:
	for row in [[&"shield_bash", "dash", 8.0], [&"leap_slam", "range", 14.0], [&"blink", "range", 12.0], [&"vault", "range", 10.0], [&"shadow_step", "range", 12.0]]:
		var skill := DB.skill(row[0])
		var params := skill.resolve(300, {row[1]: 10000.0})
		eq(params[row[1]], row[2], "rank and upgrade capped for %s" % row[0])
		eq(skill.movement_distance({row[1]: 10000.0}), row[2], "execution clamps parameters too")
		ok(Tips.skill_text(skill, params).contains("Maximum travel distance:"), "tooltip shows maximum")
	var p := Player.new()
	p.stats = blank_stats()
	p.dash(Vector3.FORWARD, 80.0, 0.1)
	near(p._movement(0.16).length() * 0.16, 8.0, 0.00001, "slow frame cannot overshoot the dash distance")
	eq(p._dash_t, 0.0, "dash completes")
	p.free()
	done()

func test_enemy_retaliation_has_shared_limit_and_no_reflection_loop() -> void:
	var victim := Actor.new()
	victim.team = BH.Team.PLAYER
	victim.stats = blank_stats(50)
	victim._stats_dirty = false
	victim.hp = 1000
	host.add_child(victim)
	var enemies: Array[Actor] = []
	for i in 4:
		var enemy := Actor.new()
		enemy.stats = blank_stats(50)
		enemy._stats_dirty = false
		enemy.hp = 1000
		host.add_child(enemy)
		enemies.append(enemy)
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = enemy.stats
		req.base_min = 1000000
		req.base_max = req.base_min
		req.tags[&"thorns"] = true
		req.evadable = false
		victim.receive_hit(req, enemy)
	eq(victim.hp, 920.0, "pack reflection costs at most 8% HP per window")
	victim.physics_move(0.5, Vector3.ZERO)
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = enemies[0].stats
	req.base_min = 1000000
	req.base_max = req.base_min
	req.tags[&"thorns"] = true
	req.evadable = false
	eq(victim.receive_hit(req, enemies[0]).total, 80, "retaliation resumes after cooldown")
	var knight := Enemy.new()
	knight.def = DB.enemy(&"mirror_knight")
	host.add_child(knight)
	knight.status.apply(&"mirror_guard", 3.0)
	var ext = load("res://src/actors/enemy/enemy_traits_x.gd").new(knight)
	victim.position = Vector3(0, 0, 2)
	ext.prepare_incoming(req, victim)
	ok(not req.tags.has(&"mirror_reflect"), "Mirror Guard cannot reflect thorns again")
	# Exercise the real Mirror and Thorns producers with a million-damage hit.
	victim._enemy_retaliation_cd = 0.0
	var mirror_hit := DamageResult.new()
	mirror_hit.total = 1000000
	var frontal := DamageRequest.new()
	frontal.tags[&"mirror_reflect"] = true
	var before := victim.hp
	ext.on_hit(mirror_hit, frontal, victim)
	eq(before - victim.hp, 80, "Mirror producer respects final retaliation limit")
	victim._enemy_retaliation_cd = 0.0
	var thorned := enemies[0]
	thorned.stats.set_stat(&"max_hp", 2000000)
	thorned.hp = 2000000
	thorned.status.apply(&"aura_thorns", 0.0, 0.25)
	thorned._stats_dirty = false
	var blow := DamageRequest.new()
	blow.attacker = victim.stats
	blow.use_weapon = false
	blow.base_min = 1000000
	blow.base_max = blow.base_min
	blow.evadable = false
	blow.can_crit = false
	before = victim.hp
	thorned.receive_hit(blow, victim)
	eq(before - victim.hp, 80, "Thorns producer respects final retaliation limit")
	knight.free()
	for enemy in enemies:
		enemy.free()
	victim.free()
	done()

func test_level_40_plus_enemy_damage_budget() -> void:
	for level in [40, 50, 60, 100, 200, 300]:
		var highest := 0.0
		for def: EnemyDef in DB.enemies.values():
			var stats := EnemyStats.build(def, level, DataEnemies.DIFFICULTY[1], [], true)
			ok(stats.get_stat(&"damage_mult") < def.scaled(level) * 1.3 * (1.0 + 0.04 * CombatGrowth.milestone(level)), "reduced late damage: %s L%d" % [def.id, level])
			for attack in def.attacks:
				highest = maxf(highest, EnemyStats.attack_range(def, stats, float(attack.get("mult", 1.0))).y * 1.5)
		# Strongest authored attack, elite multiplier and critical included; no armor/block/evasion.
		var hero := Game.new_hero(&"mage", "Survival budget")
		hero.progress.add_xp(XpCurve.total_xp_for_level(level))
		hero.progress.allocate(&"wis", (level - 1) * 3)
		var hp := hero.compute_stats().get_stat(&"max_hp")
		ok(highest < hp * 0.8, "L%d strongest elite critical %.0f leaves room to react against %.0f HP" % [level, highest, hp])
		print("SURVIVAL L%d strongest elite critical %.0f / mage HP %.0f" % [level, highest, hp])
	done()
