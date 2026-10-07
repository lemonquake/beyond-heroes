extends TestCase
## bh-040: the Descent (Descent, docs/THE_DESCENT.md). Nothing changes up to level 80; past it every curve moves
## smoothly against the hero: monster health and damage, elite and champion hit limits, the lethal-blow guard, how
## monsters fight, experience to level, experience from monsters and the price of a fall. Measurements behind the numbers:
## tests/tools/descent_probe.tscn (output/bh-040).

func _init() -> void:
	strict = true

## The pre-Descent formulas, kept here so the test proves levels 1-80 are untouched.
static func old_xp_to_next(level: int) -> int:
	var l := float(maxi(level, 1))
	return int(floor(XpCurve.A * pow(l, XpCurve.P) + XpCurve.B * l))

static func old_enemy_hp(def: EnemyDef, level: int, elite := false) -> float:
	return def.hp * def.scaled(level) * (2.6 if elite else 1.0) * CombatGrowth.health_factor(level) * CombatGrowth.enemy_health_bonus(level)

func test_nothing_changes_up_to_level_80() -> void:
	var def := DB.enemy(&"hollow_soldier")
	var base: Dictionary = DataEnemies.DIFFICULTY[1]
	for level in range(1, Descent.FROM + 1):
		eq(XpCurve.xp_to_next(level), old_xp_to_next(level), "L%d experience to level" % level)
		eq(Descent.health_mult(level), 1.0, "L%d monster health" % level)
		eq(Descent.damage_mult(level), 1.0, "L%d monster damage" % level)
		eq(Descent.hit_share(level, CombatBudget.Rank.ELITE), 1.0, "L%d elites have no hit limit" % level)
		eq(Descent.guard_bonus(level, CombatBudget.Rank.BOSS), 0.0, "L%d lethal-blow guard" % level)
		eq(Descent.death_xp_share(level), 0.0, "L%d a fall costs no experience" % level)
		eq(Descent.circle(level), 0, "L%d is above the Descent" % level)
		ok(Descent.fight(base, level) == base, "L%d monsters fight as before" % level)
		near(EnemyStats.build(def, level, base, []).get_stat(&"max_hp"), old_enemy_hp(def, level), 0.01, "L%d monster health unchanged" % level)
	for level in range(1, Descent.XP_FROM + 1):
		eq(Descent.kill_xp_mult(level), 1.0, "L%d full experience from monsters" % level)
	done()

## No steps: every curve moves a little each level, in one direction.
func test_the_descent_is_smooth_and_only_gets_harder() -> void:
	for level in range(Descent.FROM + 1, BH.LEVEL_CAP + 1):
		var hp := Descent.health_mult(level) / Descent.health_mult(level - 1)
		var dmg := Descent.damage_mult(level) / Descent.damage_mult(level - 1)
		ok(hp > 1.0 and hp < 1.06, "L%d monster health step %.3f" % [level, hp])
		ok(dmg > 1.0 and dmg < 1.06, "L%d monster damage step %.3f" % [level, dmg])
		ok(Descent.kill_xp_mult(level) <= Descent.kill_xp_mult(level - 1), "L%d monster experience never rises" % level)
		ok(Descent.death_xp_share(level) >= Descent.death_xp_share(level - 1), "L%d a fall never gets cheaper" % level)
		if level < BH.LEVEL_CAP:
			ok(XpCurve.xp_to_next(level) > XpCurve.xp_to_next(level - 1), "L%d experience to level rises" % level)
			var step := float(XpCurve.xp_to_next(level)) / float(XpCurve.xp_to_next(level - 1))
			ok(step < 1.08, "L%d experience step %.3f (no wall)" % [level, step])
	ok(Descent.health_mult(141) > 2.5, "level 141 monsters are much tougher (x%.2f)" % Descent.health_mult(141))
	ok(Descent.damage_mult(141) > 4.0, "level 141 monsters hit much harder (x%.2f)" % Descent.damage_mult(141))
	ok(Descent.kill_xp_mult(141) < 0.45, "level 141 heroes get under half the experience (x%.2f)" % Descent.kill_xp_mult(141))
	done()

func test_kills_per_level_climb_steeply() -> void:
	var at := {}
	for level in [80, 100, 141, 200, 299]:
		var ml: int = level - CombatBudget.ENCOUNTER_GAP
		at[level] = float(XpCurve.xp_to_next(level)) / float(XpCurve.kill_xp(ml, 1.0, level))
		print("DESCENT kills per level L%d: %.0f" % [level, at[level]])
	ok(at[100] > at[80] * 1.8, "level 100 needs far more kills than 80")
	ok(at[141] > at[80] * 6.0, "level 141 needs over six times the kills of level 80 (%.0f vs %.0f)" % [at[141], at[80]])
	ok(at[200] > at[141] * 2.0, "level 200 needs over twice the kills of 141")
	done()

func test_monster_stats_follow_the_descent() -> void:
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	for id in [&"hollow_soldier", &"glyphbound_warrior", &"astrarch"]:
		var def := DB.enemy(id)
		for level in [81, 100, 141, 200, 300]:
			var st := EnemyStats.build(def, level, diff, [])
			# bh-042: the Abyss multiplies on top of the Descent from level 86 (Abyss)
			near(st.get_stat(&"max_hp"), old_enemy_hp(def, level) * Descent.health_mult(level) * Abyss.health_mult(level), 0.5, "%s L%d health" % [id, level])
			near(st.get_stat(&"damage_mult"), CombatGrowth.enemy_damage_scale(level, def.level_scaling) * Descent.damage_mult(level) * Abyss.damage_mult(level), 0.0001,
				"%s L%d damage" % [id, level])
	done()

## A hit of any size leaves a Descent elite or champion standing; a monster above the Descent can still be one-shot.
func test_elites_and_champions_cannot_be_felled_by_one_blow() -> void:
	var def := DB.enemy(&"glyphbound_warrior")
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	var cases := [[141, true, false, Descent.ELITE_HIT_SHARE], [141, true, true, Descent.CHAMPION_HIT_SHARE], [60, true, false, 1.0],
		[100, false, false, 1.0], [141, false, false, Descent.NORMAL_HIT_SHARE]]
	for c in cases:
		var mods := [StatModifier.flat(&"threat_rank", float(CombatBudget.Rank.CHAMPION))] if c[2] else []
		var tgt := EnemyStats.build(def, c[0], diff, mods, c[1])
		var req := DamageRequest.new()
		req.attacker = blank_stats(c[0])
		req.target = tgt
		req.use_weapon = false
		req.base_min = 1.0e12
		req.base_max = 1.0e12
		req.evadable = false
		req.blockable = false
		req.can_crit = false
		var r := DamagePipeline.compute(req, rng(4))
		var share := float(r.total) / tgt.get_stat(&"max_hp")
		if float(c[3]) < 1.0:
			near(share, float(c[3]), 0.001, "L%d %s: one blow takes at most %d%%" % [c[0], "champion" if c[2] else ("elite" if c[1] else "monster"), roundi(float(c[3]) * 100.0)])
		else:
			ok(share >= 1.0, "L%d %s: no limit (%.2f)" % [c[0], "elite" if c[1] else "normal monster", share])
	done()

func test_the_lethal_blow_guard_loosens_with_depth() -> void:
	for rank in [CombatBudget.Rank.NORMAL, CombatBudget.Rank.CHAMPION, CombatBudget.Rank.BOSS]:
		eq(CombatBudget.blow_cap(rank, 60), float(CombatBudget.BLOW_CAP[rank]), "rank %d above the Descent" % rank)
		ok(CombatBudget.blow_cap(rank, 141) > CombatBudget.blow_cap(rank, 100), "rank %d rises with depth" % rank)
		near(CombatBudget.blow_cap(rank, 300), float(CombatBudget.BLOW_CAP[rank]) + float(Descent.GUARD_RISE[rank]), 0.0001, "rank %d at full depth" % rank)
		ok(CombatBudget.blow_cap(rank, 300) < 0.5, "rank %d: never a one-shot from full health" % rank)
	# the guard reads the attacker's level
	var hero := Actor.new()
	hero.team = BH.Team.PLAYER
	hero.stats = blank_stats(200)
	hero.stats.set_stat(&"max_hp", 10000.0)
	hero._stats_dirty = false
	hero.hp = 10000.0
	host.add_child(hero)
	var atk := blank_stats(200)
	atk.set_stat(&"threat_rank", float(CombatBudget.Rank.BOSS))
	var req := DamageRequest.new()
	req.attacker = atk
	req.use_weapon = false
	req.base_min = 1.0e9
	req.base_max = 1.0e9
	req.evadable = false
	req.blockable = false
	var res := hero.receive_hit(req)
	near(float(res.total), 10000.0 * CombatBudget.blow_cap(CombatBudget.Rank.BOSS, 200), 1.0, "a level-200 boss blow takes the loosened share")
	ok(hero.alive, "the hero stands")
	hero.free()
	done()

## Bosses: their heaviest blows lose their compression as the Descent deepens.
func test_bosses_hit_harder_deep_down() -> void:
	var plain60 := CombatBudget.boss_attack_mult(4.2, 60)
	eq(plain60, CombatBudget.boss_attack_mult(4.2), "above the Descent the old compression stands")
	ok(CombatBudget.boss_attack_mult(4.2, 141) > plain60 * 1.5, "a level-141 slam hits much harder than the compressed one")
	ok(CombatBudget.boss_attack_mult(4.2, 300) >= CombatBudget.boss_attack_mult(4.2, 141), "and keeps rising")
	done()

func test_monsters_fight_harder_deep_down() -> void:
	var base: Dictionary = DataEnemies.DIFFICULTY[1]
	var deep := Descent.fight(base, 141)
	ok(int(deep.tokens) >= int(base.tokens) + 2, "more monsters swing at once at level 141 (%d)" % int(deep.tokens))
	ok(float(deep.skill_rate) > float(base.skill_rate) * 1.2, "they attack and use skills more often")
	ok(float(deep.reaction) < float(base.reaction), "they hesitate less")
	ok(float(deep.elite) > float(base.elite), "more packs are led by elites")
	eq(float(deep.hp), float(base.hp), "health stays in EnemyStats (by monster level)")
	var bottom := Descent.fight(base, BH.LEVEL_CAP)
	ok(int(bottom.tokens) <= int(base.tokens) + Descent.TOKENS_MAX, "the swarm has a limit")
	ok(float(bottom.skill_rate) <= float(base.skill_rate) * Descent.SKILL_RATE_MAX + 0.0001, "attack rate has a limit")
	var dir := CombatDirector.new()
	dir.configure(deep)
	eq(dir.melee_tokens, int(deep.tokens), "the combat director lets them in")
	dir.free()
	var r := rng(40)
	var n := 0
	for i in 50:
		n = maxi(n, Spawner.roll_elite_mods(r, 200).size())
	ok(n >= 3, "level-200 elites carry extra affixes (%d)" % n)
	r = rng(40)
	var m := 0
	for i in 50:
		m = maxi(m, Spawner.roll_elite_mods(r, 60).size())
	ok(m <= 2, "level-60 elites keep one or two")
	done()

func test_experience_from_monsters_falls_off_past_90() -> void:
	eq(XpCurve.kill_xp(100, 1.0, 100, 0.0), maxi(1, int(round(XpCurve.monster_xp(100) * Abyss.kill_xp_mult(100)))), "kill experience carries the Abyss fall-off (bh-042)")
	ok(XpCurve.kill_xp(139, 1.0, 141, 0.0) < XpCurve.monster_xp(139) * 0.45, "a level-141 hero gets under half")
	eq(XpCurve.kill_xp(88, 1.0, 90, 0.0), XpCurve.monster_xp(88), "a level-90 hero gets it all")
	ok(XpCurve.kill_xp(139, 3.0, 141, 0.5) > XpCurve.kill_xp(139, 1.0, 141, 0.0) * 4.0, "rank and Experience Gain still count")
	done()

func test_a_fall_costs_experience_in_the_descent() -> void:
	var h := Game.new_hero(&"mage", "Descent")
	h.progress.add_xp(XpCurve.total_xp_for_level(141) + XpCurve.xp_to_next(141) / 2)
	eq(h.progress.level, 141, "level 141")
	var before := h.progress.xp
	var loss := Descent.death_xp_loss(h)
	eq(loss, int(floor(Descent.death_xp_share(141) * float(XpCurve.xp_to_next(141)))), "the share of the level's requirement")
	eq(h.progress.lose_xp(loss), loss, "taken")
	eq(h.progress.xp, before - loss, "from the progress inside the level")
	h.progress.xp = 10
	eq(Descent.death_xp_loss(h), 10, "never more than the progress")
	h.progress.lose_xp(Descent.death_xp_loss(h))
	eq(h.progress.xp, 0, "the level is kept")
	eq(h.progress.level, 141, "never a level")
	var young := Game.new_hero(&"knight", "Young")
	young.progress.add_xp(XpCurve.total_xp_for_level(60) + 5000)
	eq(Descent.death_xp_loss(young), 0, "above the Descent a fall costs no experience")
	done()

## The uncapped Archmage keystone multiplied a 10,000-Mana mage's spells by 5.2: it is bounded now.
func test_archmage_keystone_is_bounded() -> void:
	var st := blank_stats(141)
	st.flags[&"archmage"] = 25.0
	st.set_stat(&"max_mana", 10461.0)
	near(StatCalculator.archmage_more(st), 1.0 + StatCalculator.ARCHMAGE_MAX, 0.0001, "10,461 Mana: the bound")
	st.set_stat(&"max_mana", 500.0)
	near(StatCalculator.archmage_more(st), 1.2, 0.0001, "500 Mana: 20% more")
	st.flags.erase(&"archmage")
	eq(StatCalculator.archmage_more(st), 1.0, "without the keystone")
	ok(String(DB.tree(DB.class_def(&"mage").talent_tree_id).node(&"m_archmage").desc).contains("at most"), "the talent says so")
	done()

func test_circles_and_notices() -> void:
	eq(Descent.circle(80), 0, "80 is above")
	eq(Descent.circle(81), 1, "81 is the first circle")
	eq(Descent.circle(100), 1, "100 is still the first")
	eq(Descent.circle(101), 2, "101 opens the second")
	eq(Descent.circle(300), Descent.CIRCLES.size() - 1, "300 is the bottom")
	for level in range(81, 301):
		ok(Descent.circle_name(level) != "", "L%d has a circle name" % level)
	ok(Descent.level_notice(81, 1).contains("Descent"), "entering the Descent is announced")
	ok(Descent.level_notice(101, 1).contains("Circle II"), "a new circle is announced")
	eq(Descent.level_notice(102, 1), "", "an ordinary level is not")
	ok(Descent.summary(141).contains("health"), "the summary explains the numbers")
	done()

## Adaptive bosses: a Descent boss is built to last longer against the same hero.
func test_bosses_last_longer_in_the_descent() -> void:
	ok(Descent.boss_time_mult(141) > 1.5, "a level-141 boss lasts half as long again or more (x%.2f)" % Descent.boss_time_mult(141))
	ok(Descent.boss_time_mult(300) > Descent.boss_time_mult(141), "and longer still deep down")
	eq(Descent.boss_time_mult(80), 1.0, "level 80 unchanged")
	done()

## Diablo II's Hell penalty: a Descent monster strips armour reduction and resistances off a hero after the caps; heroes
## never strip each other's, and above the Descent nothing changes.
func test_the_resistance_penalty() -> void:
	eq(Descent.res_penalty(80), 0.0, "none above the Descent")
	ok(Descent.res_penalty(141) > 0.2, "about a quarter at level 141 (%.2f)" % Descent.res_penalty(141))
	near(Descent.res_penalty(300), Descent.RES_PENALTY_MAX, 0.0001, "the full penalty deep down")
	var hero := blank_stats(141)
	hero.set_stat(&"hero_source", 1.0)
	hero.set_stat(&"res_fire", 0.75)
	var monster := blank_stats(141)
	var fire := func(atk: DerivedStats) -> float:
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.SPELL
		req.attacker = atk
		req.target = hero
		req.base_min = 1000.0
		req.base_max = 1000.0
		req.conversion = {Elements.FIRE: 1.0}
		req.evadable = false
		req.blockable = false
		req.can_crit = false
		return float(DamagePipeline.compute(req, rng(9)).total)
	near(fire.call(monster), 1000.0 * (1.0 - (0.75 - Descent.res_penalty(141))), 1.0, "a capped Fire resistance loses the penalty")
	var other_hero := blank_stats(141)
	other_hero.set_stat(&"hero_source", 1.0)
	near(fire.call(other_hero), 250.0, 1.0, "a hero's blow meets the full resistance")
	near(fire.call(blank_stats(60)), 250.0, 1.0, "a level-60 monster meets the full resistance")
	done()

## Path of Exile's leech-rate rule: deep down leech refills at most LEECH_CAP of Maximum HP per second.
func test_life_leech_is_rate_capped_in_the_descent() -> void:
	eq(Descent.leech_cap(80), 0.0, "no cap above the Descent")
	near(Descent.leech_cap(200), Descent.LEECH_CAP, 0.0001, "the cap deep down")
	ok(Descent.leech_cap(85) > 0.9, "phased in: barely any cap at the start")
	var a := Actor.new()
	a.team = BH.Team.PLAYER
	a.level = 200
	a.stats = blank_stats(200)
	a.stats.set_stat(&"max_hp", 10000.0)
	a._stats_dirty = false
	host.add_child(a)
	var first := a.leech_allowance(5000.0)
	near(first, 10000.0 * Descent.LEECH_CAP, 0.5, "one second's worth at most")
	near(a.leech_allowance(5000.0), 0.0, 0.5, "and nothing more in the same frame")
	a.level = 60
	eq(a.leech_allowance(5000.0), 5000.0, "a level-60 hero leeches freely")
	a.free()
	done()

## Hit recovery: a Descent monster only flinches from a blow that takes a real share of its health; bosses never from
## damage alone. Pushes of every kind move it less.
func test_hit_recovery_and_push_resistance() -> void:
	for rank in [CombatBudget.Rank.NORMAL, CombatBudget.Rank.ELITE, CombatBudget.Rank.BOSS]:
		eq(Descent.flinch_share(80, rank), 0.0, "rank %d: any blow makes it flinch above the Descent" % rank)
		eq(Descent.knock_taken(80, rank), 1.0, "rank %d: pushed as before above the Descent" % rank)
		ok(Descent.flinch_share(141, rank) >= Descent.flinch_share(141, CombatBudget.Rank.NORMAL), "rank %d: higher ranks flinch less" % rank)
	ok(Descent.flinch_share(141, CombatBudget.Rank.BOSS) > 1.0, "bosses never flinch from damage alone")
	ok(Descent.knock_taken(141, CombatBudget.Rank.BOSS) <= 0.25, "a boss takes a quarter of a push or less")
	ok(Descent.knock_taken(141, CombatBudget.Rank.NORMAL) < 1.0, "a monster takes less of a push")
	var e := Enemy.new()
	e.setup(DB.enemy(&"glyphbound_warrior"), 141, [], DataEnemies.DIFFICULTY[1])
	host.add_child(e)
	e.ensure_stats()
	e.apply_knockback(Vector3.RIGHT, 10.0, null, null)
	near(e.knock_velocity.length(), 10.0 * Descent.knock_taken(141, CombatBudget.Rank.NORMAL), 0.01, "a direct push is resisted too")
	e.free()
	done()
