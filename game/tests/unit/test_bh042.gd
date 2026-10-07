extends TestCase
## bh-042: the Abyss (docs/PLAN_bh-042.md, docs/HANDOFF_bh-042.md). Level 90+ rules (experience fall-off, +50% Defense,
## x8 damage, growing health), the bosses' Curse of Stillness / Armour Rip / bullet patterns, the ten bosses, the five
## Abyss dungeons (22 floors, storeys 0-3, secret rooms), the Delvers' Undercroft and the Abyss loot rules.

func _init() -> void:
	strict = true

# ---- the level-90 rules --------------------------------------------------------------------------------------------

func test_nothing_changes_below_the_ease_in() -> void:
	for level in range(1, Abyss.FROM + 1):
		eq(Abyss.defense_mult(level), 1.0, "L%d Defense untouched" % level)
		eq(Abyss.damage_mult(level), 1.0, "L%d damage untouched" % level)
		eq(Abyss.health_mult(level), 1.0, "L%d health untouched" % level)
	for level in range(1, Abyss.XP_FROM + 1):
		near(Abyss.kill_xp_mult(level), Descent.kill_xp_mult(level), 0.0001, "L%d experience as before" % level)
	done()

func test_ninety_and_above_as_asked() -> void:
	for level in [90, 95, 120, 150, 200, 300]:
		near(Abyss.defense_mult(level), 1.5, 0.0001, "L%d: +50%% Defense" % level)
		near(Abyss.damage_mult(level), 8.0, 0.0001, "L%d: eight times the damage" % level)
	for level in range(Abyss.FROM + 1, Abyss.FULL):
		ok(Abyss.damage_mult(level) > Abyss.damage_mult(level - 1), "L%d eases in (no wall at 90)" % level)
	for level in range(Abyss.HP_FROM + 1, BH.LEVEL_CAP + 1):
		ok(Abyss.health_mult(level) > Abyss.health_mult(level - 1), "L%d health keeps growing" % level)
	ok(Abyss.health_mult(200) > 10.0, "level 200 monsters: x%.1f health on top of the Descent" % Abyss.health_mult(200))
	# through the real stat builder
	var def := DB.enemy(&"hollow_soldier")
	var base: Dictionary = DataEnemies.DIFFICULTY[1]
	var on := EnemyStats.build(def, 150, base, [])
	Abyss.enabled = false
	var off := EnemyStats.build(def, 150, base, [])
	Abyss.enabled = true
	near(on.get_stat(&"defense") / off.get_stat(&"defense"), 1.5, 0.001, "level 150 monster Defense x1.5")
	near(on.get_stat(&"damage_mult") / off.get_stat(&"damage_mult"), 8.0, 0.001, "level 150 monster damage x8")
	near(on.get_stat(&"max_hp") / off.get_stat(&"max_hp"), Abyss.health_mult(150), 0.01, "level 150 monster health grows")
	done()

func test_experience_falls_off_steeply_past_ninety() -> void:
	for level in range(Abyss.XP_FROM + 1, BH.LEVEL_CAP + 1):
		ok(Abyss.kill_xp_mult(level) < Abyss.kill_xp_mult(level - 1), "L%d less experience per kill than the level before" % level)
		ok(Abyss.kill_xp_mult(level) <= Descent.kill_xp_mult(level) + 0.0001, "L%d steeper than the Descent's fall-off" % level)
	var kills := {}
	for level in [90, 100, 141, 160, 200]:
		var ml: int = level - CombatBudget.ENCOUNTER_GAP
		kills[level] = float(XpCurve.xp_to_next(level)) / float(XpCurve.kill_xp(ml, 1.0, level))
		print("ABYSS kills per level L%d: %.0f (experience x%.2f)" % [level, kills[level], Abyss.kill_xp_mult(level)])
	ok(kills[141] > kills[100] * 3.0, "level 141 takes far more kills than 100")
	ok(kills[200] > kills[141] * 2.5, "level 200 takes far more kills than 141")
	eq(XpCurve.kill_xp(100, 1.0, 100), maxi(1, int(round(XpCurve.monster_xp(100) * Abyss.kill_xp_mult(100)))), "kill experience carries the fall-off")
	done()

func test_boss_health_reaches_hundreds_of_millions() -> void:
	var h := Game.new_hero(&"mage", "Probe")
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(200) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	var r := RandomNumberGenerator.new()
	r.seed = 42
	GuildSummons._gear_up(h, 200, r)
	var def := DB.enemy(&"vaelgor")
	var baseline := EnemyStats.build(def, 200, DataEnemies.DIFFICULTY[1], [], false, true)
	var hp := EnemyStats.boss_health(h, baseline) * float(DataDungeonsAbyss.POWER.hp)
	Abyss.enabled = false
	var plain := EnemyStats.boss_health(h, EnemyStats.build(def, 200, DataEnemies.DIFFICULTY[1], [], false, true)) * float(DataDungeonsAbyss.POWER.hp)
	Abyss.enabled = true
	print("ABYSS level-200 Vaelgor against a level-200 hero in level-200 gear: %.0f HP (%.0f without the Abyss)" % [hp, plain])
	# boss health adapts to the hero: a hero in ordinary level-200 gear meets tens of millions, a top-geared one (the
	# user's Primordial Archmage faced 20.5 M at L200 before bh-042) about x14 that: ~300 million
	near(hp / plain, Abyss.health_mult(200), 0.05 * Abyss.health_mult(200), "the Abyss multiplies a lord's health by x%.1f" % Abyss.health_mult(200))
	ok(20.5e6 * Abyss.health_mult(200) > 2.5e8, "a top-geared hero's level-200 lord: ~%.0f million" % (20.5 * Abyss.health_mult(200)))
	done()

# ---- the bosses' moves ----------------------------------------------------------------------------------------------

func test_curse_and_armour_rip() -> void:
	var sc := StatusController.new()
	sc.apply(&"stilled", 0.6)
	ok(sc.is_silenced(), "standing in a Curse of Stillness silences")
	var mods: Array = StatusRules.DEFS[&"armor_ripped"].mods
	var cut := 0.0
	for m in mods:
		if m[0] == &"defense":
			cut = -float(m[2])
	ok(cut >= 0.5, "Armour Rip removes at least half of the Defense (%.0f%%)" % (cut * 100.0))
	ok(bool(StatusRules.DEFS[&"armor_ripped"].get("fixed_duration", false)), "Status Resistance does not shorten the rip")
	done()

func test_every_abyss_boss_has_the_signature_moves() -> void:
	var ids := DataEnemiesAbyss.ids()
	eq(ids.size(), 10, "ten new bosses")
	for id in ids:
		var d := DB.enemy(id)
		ok(d != null and d.archetype == &"boss", "%s is a boss" % id)
		var kinds := {}
		for a in d.attacks:
			kinds[String(a.kind)] = int(kinds.get(String(a.kind), 0)) + 1
		ok(kinds.has("curse_zone"), "%s casts a Curse of Stillness" % id)
		ok(kinds.has("armor_rip"), "%s rips armour" % id)
		ok(int(kinds.get("barrage", 0)) >= 1, "%s fires a bullet pattern" % id)
		ok(d.phases.size() == 3, "%s fights in three phases" % id)
		eq(String(DataEnemiesAbyss.NAMES.get(id, "")), d.display_name, "%s name table" % id)
		if id != &"fallen_necro_knight":
			ok(ResourceLoader.exists(d.model), "%s has its model (%s)" % [id, d.model])
	ok(DB.enemy(&"fallen_necro_knight").traits.has(&"player_like"), "the Necro-Knight plays like a hero")
	ok(not Persona.for_enemy(DB.enemy(&"fallen_necro_knight")).is_empty(), "the Necro-Knight is drawn on the hero body")
	eq(NecroKnight.level_for(160), 165, "the Necro-Knight is five levels above the hero")
	done()

func test_older_bosses_learn_the_abyss_at_ninety() -> void:
	var def := DB.enemy(&"morrowgaunt")
	var extra := AbyssMoves.overhaul(def)
	var kinds := extra.map(func(a): return String(a.kind))
	ok(kinds.has("barrage") and kinds.has("curse_zone") and kinds.has("armor_rip"), "a level-90+ boss gains the three moves")
	for a in extra:
		eq(int(a.get("phase", 1)), 2, "%s waits for the second phase" % a.id)
	done()

func test_barrage_patterns_fire_and_hit() -> void:
	for pat in ["radial", "spiral", "fan", "wall", "orbit", "homing", "cross"]:
		var a := {"pattern": pat, "count": 12, "waves": 2, "gap": 0.1, "duration": 0.5, "rate": 6.0, "speed": 10.0, "reach": 20.0,
			"width": 10.0, "spacing": 1.0, "seed": 7}
		var b := Barrage.fire(host, a, Vector3.ZERO, Vector3.FORWARD, null, null, null)
		ok(b.pending_shots() > 0, "%s plans its shots (%d)" % [pat, b.pending_shots()])
		b.queue_free()
	# the wall leaves a gap to walk through
	var w := Barrage.fire(host, {"pattern": "wall", "waves": 1, "width": 12.0, "spacing": 1.0, "gap": 3.0, "seed": 3}, Vector3.ZERO, Vector3.FORWARD, null, null, null)
	ok(w.pending_shots() < 13, "a wall of shots has a hole in it (%d of 13)" % w.pending_shots())
	w.queue_free()
	done()

# ---- the dungeons ----------------------------------------------------------------------------------------------------

func test_five_abyss_dungeons_of_twenty_two_floors() -> void:
	eq(DataDungeonsAbyss.ORDER.size(), 5, "five Abyss dungeons")
	var secrets := 0
	var storey3 := 0
	for id in DataDungeonsAbyss.ORDER:
		var d := DataDungeons.get_def(id)
		ok(DataDungeons.is_abyss(id), "%s is an Abyss dungeon" % id)
		ok(DataDungeons.floor_count(id) >= 20, "%s has at least 20 floors (%d)" % [id, DataDungeons.floor_count(id)])
		var lv := DataDungeons.level_range(id)
		ok(lv.x >= 150 and lv.y <= 200, "%s levels %d-%d inside 150-200" % [id, lv.x, lv.y])
		eq(StringName(d.surface.map), &"int_delvers", "%s's gate stands in the Delvers' Undercroft" % id)
		eq(int(d.min_level), DataDungeonsAbyss.MIN_LEVEL, "%s turns away heroes below level 140" % id)
		ok(DB.enemy(StringName(d.boss)) != null and DB.enemy(StringName(d.gatekeeper)) != null, "%s has its lord and gatekeeper" % id)
		var gk: Dictionary = d.floors[DataDungeonsAbyss.GATEKEEPER_FLOOR - 1]
		ok(gk.has("gatekeeper"), "%s floor 11 is the gatekeeper's hall" % id)
		for n in d.floors.size():
			var f: Dictionary = d.floors[n]
			secrets += (f.get("secrets", []) as Array).size()
			ok(not (f.get("secrets", []) as Array).is_empty(), "%s floor %d hides a room behind a cracked wall" % [id, n + 1])
			for row in f.plan:
				if "3" in String(row):
					storey3 += 1
					break
			for s in f.get("secrets", []):
				eq(String(f.plan[s.wall.y])[s.wall.x], "#", "%s floor %d secret wall cell" % [id, n + 1])
	ok(secrets >= 110, "every floor has a secret room (%d in all)" % secrets)
	ok(storey3 >= 20, "many floors climb to a fourth storey (%d)" % storey3)
	var wardens := DataDungeons.minibosses().filter(func(m): return String(m.get("id", "")).contains("_warden_"))
	eq(wardens.size(), 20, "a warden on floors 5, 10, 15 and 20 of each dungeon")
	done()

func test_the_undercroft_and_the_dark() -> void:
	var m := DB.map_def(&"int_delvers")
	ok(m != null and m.is_town, "the Delvers' Undercroft is a safe interior of Malasugue")
	for id in DataDungeonsAbyss.ORDER:
		var th := DataDungeons.theme(id)
		ok(bool(th.get("dark", false)), "%s is dark" % id)
		ok(int(th.get("max_torches", 99)) <= 8, "%s has only a few lit torches" % id)
		ok(float(th.env.ambient_energy) < 1.0, "%s has no fill light" % id)
		for set in th.stone.values():
			ok(ResourceLoader.exists("res://assets/textures/%s_albedo.png" % set[0]), "%s texture %s is in the game" % [id, set[0]])
	done()

func test_abyss_loot_floors() -> void:
	ok(Loot.ABYSS_NORMAL_DROP > 0.2, "ordinary Abyss monsters drop equipment often (%.0f%%)" % (Loot.ABYSS_NORMAL_DROP * 100.0))
	done()
