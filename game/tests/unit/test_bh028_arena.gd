extends TestCase
## bh-028: the combat budget (CombatBudget) and the Sand Arena (ArenaGrounds, ArenaFighter). The evasion, level HP,
## orb and special-dungeon checks of the same update are in test_bh028.gd.

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _tree() -> SceneTree:
	return host.get_tree()

func _frames(n := 1) -> void:
	for i in n:
		await _tree().physics_frame

func _until(cond: Callable, seconds: float) -> bool:
	var t := 0.0
	while t < seconds:
		if cond.call():
			return true
		await _tree().physics_frame
		t += Engine.time_scale / Engine.physics_ticks_per_second
	return cond.call()

## A hero of `level` whose points follow the class build and who wears gear of that level at `rarity`.
static func geared(cid: StringName, level: int, rarity := BH.Rarity.ADVANCED, pure := false) -> HeroData:
	var h := Game.new_hero(cid, "Budget")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	if pure:
		h.progress.allocate(&"int" if cid == &"mage" else (&"dex" if cid == &"ranger" else &"str"), h.progress.free_points)
	else:
		h.progress.allocate_along_build(h.progress.free_points)
	var family: StringName = {&"knight": &"sword", &"mage": &"staff", &"ranger": &"crossbow", &"shadowblade": &"dagger"}[cid]
	var best: ItemBaseDef
	for b: ItemBaseDef in DB.item_bases.values():
		if b.weapon_type == family and b.level_req <= level and b.drop_weight > 0 and b.unique_name == "" and b.set_id == &"":
			if best == null or b.level_req > best.level_req:
				best = b
	h.equipment.slots[&"main_weapon"] = DB.make_item(best.id, rarity, level, 493)
	for slot in BH.SLOTS:
		if slot in [&"main_weapon", &"sub_weapon"]:
			continue
		var cat := StringName(String(slot).split("_")[0]) if slot != &"inner_garment" else slot
		var base := ItemGenerator.random_base(rng(hash(String(slot))), level, [cat], cid)
		if base != null:
			h.equipment.slots[slot] = DB.make_item(base.id, rarity, level, hash(String(slot)))
	return h

## A monster blow on a hero's stats: no evasion or block, the average roll.
static func blow(att: DerivedStats, def: EnemyDef, mult: float, target: DerivedStats, crit := false) -> float:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = att
	req.target = target
	req.use_weapon = false
	var rr := EnemyStats.attack_range(def, att, mult)
	req.base_min = (rr.x + rr.y) * 0.5
	req.base_max = req.base_min
	req.evadable = false
	req.blockable = false
	req.can_crit = crit
	req.force_crit = crit
	return float(DamagePipeline.compute(req, rng(1)).total)

static func heaviest(def: EnemyDef) -> float:
	var m := 1.0
	for a in def.attacks:
		m = maxf(m, float(a.get("mult", 1.0)))
	return m

# ---- the budget ----------------------------------------------------------------------------------------------------

func test_monster_damage_follows_the_reference_hero() -> void:
	for per_level in [0.08, 0.14, 0.2]:
		for level in range(1, 6):
			near(CombatGrowth.enemy_damage_scale(level, per_level), 1.0 + per_level * (level - 1), 0.000001, "opening levels keep their damage")
		var k := CombatGrowth.enemy_damage_scale(6, per_level) / CombatBudget.hero_hp_ref(6)
		for level in [6, 10, 29, 30, 44, 45, 46, 60, 100, 200, 300]:
			near(CombatGrowth.enemy_damage_scale(level, per_level) / CombatBudget.hero_hp_ref(level), k, k * 0.000001,
				"L%d damage grows exactly with the reference hero" % level)
	done()

func test_no_difficulty_steps() -> void:
	var def := DB.enemy(&"hollow_soldier")
	var prev := EnemyStats.build(def, 5, DataEnemies.DIFFICULTY[1], [])
	for level in range(6, 301):
		var cur := EnemyStats.build(def, level, DataEnemies.DIFFICULTY[1], [])
		var dmg := cur.get_stat(&"damage_mult") / prev.get_stat(&"damage_mult")
		var hp := cur.get_stat(&"max_hp") / prev.get_stat(&"max_hp")
		ok(dmg > 1.0 and dmg < 1.13, "L%d damage step %.3f" % [level, dmg])
		# (levels 6-14 keep the opening's original steep health ramp)
		ok(hp > 1.0 and hp < (1.32 if level < 10 else (1.25 if level < 15 else 1.2)), "L%d health step %.3f" % [level, hp])
		prev = cur
	for level in [30, 44, 45, 46, 59, 60, 61, 120, 300]:
		eq(CombatGrowth.encounter_level(5, level), level - CombatBudget.ENCOUNTER_GAP, "L%d monsters stay close to the hero" % level)
		eq(CombatGrowth.encounter_level(5, level, true), level, "bosses match the hero")
	eq(CombatGrowth.encounter_level(5, 29), 5, "below 30 the authored level stands")
	eq(CombatGrowth.encounter_level(80, 50), 80, "a higher authored level stands")
	done()

func test_vitality_and_its_explanation() -> void:
	for cid in CLASSES:
		var cls := DB.class_def(cid).duplicate() as ClassDef
		cls.class_modifiers = []
		for level in [1, 4, 5, 6, 50, 299]:
			var a := StatCalculator.compute(cls, level, {}, [], WeaponLoadout.new()).get_stat(&"max_hp")
			var b := StatCalculator.compute(cls, level + 1, {}, [], WeaponLoadout.new()).get_stat(&"max_hp")
			var expect: float = cls.hp_per_level + cls.level_up_hp + (CombatBudget.VITALITY_PER_LEVEL if level >= 5 else 0.0)
			near(b - a, expect, 1.01, "%s: level %d -> %d adds class health%s" % [cid, level, level + 1, " and Vitality" if level >= 5 else ""])
		var lines: PackedStringArray = StatCalculator.compute(cls, 50, {}, [], WeaponLoadout.new()).explain.get(&"max_hp", PackedStringArray())
		ok(" ".join(lines).contains("Vitality"), "the character sheet explains Vitality")
	eq(CombatBudget.vitality(50), 720.0, "16 per level after 5")
	done()

## The heart of the fix: the share of an average hero's health a monster blow takes is the same at every level up to
## the Descent, and a boss's heaviest critical leaves an average hero standing for at least five such blows. bh-040: past
## level 80 the Descent raises every share on purpose (Descent.damage_mult, the resistance penalty, uncompressed boss
## slams): there the shares must climb with depth instead.
func test_hits_to_kill_are_flat_across_levels() -> void:
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	var boss_ids := [&"astrarch", &"kethrax", &"boss_warden"]
	for cid in CLASSES:
		var shares := []
		var deep := {}
		for level in [10, 30, 40, 45, 50, 80, 100, 141, 300]:
			var st := geared(cid, level).compute_stats()
			var hp := st.get_stat(&"max_hp")
			var normal := 0.0
			var heavy := 0.0
			for def: EnemyDef in DB.enemies.values():
				if def.attacks.is_empty() or def.archetype == &"boss":
					continue
				var ns := EnemyStats.build(def, level, diff, [])
				normal = maxf(normal, blow(ns, def, 1.0, st))
				var es := EnemyStats.build(def, level, diff, [StatModifier.flat(&"threat_rank", CombatBudget.Rank.CHAMPION),
					StatModifier.more(&"outgoing_damage", 0.25)], true)
				heavy = maxf(heavy, blow(es, def, heaviest(def), st, true))
			var boss_heavy := 0.0
			for id in boss_ids:
				var def := DB.enemy(id)
				var bs := EnemyStats.build(def, level, diff, [], false, true)
				boss_heavy = maxf(boss_heavy, blow(bs, def, heaviest(def), st, true))
			for def: EnemyDef in DB.enemies.values():
				if def.archetype == &"boss" and not def.attacks.is_empty():
					var bs := EnemyStats.build(def, level, diff, [], false, true)
					boss_heavy = maxf(boss_heavy, blow(bs, def, heaviest(def), st, true))
			print("BUDGET %s L%d hp %d normal %.1f%% champion %.1f%% boss %.1f%%" % [cid, level, hp, normal / hp * 100.0, heavy / hp * 100.0, boss_heavy / hp * 100.0])
			if Descent.active(level):
				deep[level] = [normal / hp, heavy / hp, boss_heavy / hp]
				continue
			ok(boss_heavy <= hp * 0.205, "%s L%d: a boss's heaviest critical takes %.1f%% (five hits at least)" % [cid, level, boss_heavy / hp * 100.0])
			ok(heavy < hp * 0.4, "%s L%d: an elite champion's heaviest critical takes %.1f%%" % [cid, level, heavy / hp * 100.0])
			ok(normal < hp * 0.08, "%s L%d: an ordinary monster's plain blow takes %.1f%%" % [cid, level, normal / hp * 100.0])
			shares.append([normal / hp, heavy / hp, boss_heavy / hp])
		# the same share from level 30 to 80 (gear rolls differ a little level to level)
		var bosses: Array = shares.slice(1).map(func(x): return x[2])
		var lo: float = bosses.min()
		var hi: float = bosses.max()
		ok(hi / lo < 1.45, "%s: the boss share stays within a narrow band from level 30 to 80 (%.1f%%-%.1f%%)" % [cid, lo * 100.0, hi * 100.0])
		# the Descent: every share climbs with depth, and by level 141 a plain blow hurts several times as much as at 80
		var at80: Array = shares[shares.size() - 1]
		for k in 3:
			ok(deep[100][k] > at80[k] and deep[141][k] > deep[100][k] and deep[300][k] > deep[141][k],
				"%s: share %d climbs through the Descent (%.2f%% at 80, %.2f%% at 141, %.2f%% at 300)" % [cid, k, at80[k] * 100.0, deep[141][k] * 100.0, deep[300][k] * 100.0])
		ok(deep[141][0] > at80[0] * 4.0, "%s: a plain blow at 141 takes over four times its level-80 share" % cid)
	done()

## The lethal-blow guard: whatever the build, no single monster hit takes more than its rank's share.
func test_lethal_blow_guard() -> void:
	for row in [[CombatBudget.Rank.NORMAL, 0.35], [CombatBudget.Rank.CHAMPION, 0.35], [CombatBudget.Rank.BOSS, 0.25]]:
		var hero := Actor.new()
		hero.team = BH.Team.PLAYER
		hero.stats = blank_stats(50)
		hero.stats.set_stat(&"max_hp", 2000.0)
		hero._stats_dirty = false
		hero.hp = 2000.0
		host.add_child(hero)
		var atk := blank_stats(50)
		atk.set_stat(&"threat_rank", float(row[0]))
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.ATTACK
		req.attacker = atk
		req.use_weapon = false
		req.base_min = 1.0e6
		req.base_max = 1.0e6
		req.evadable = false
		req.blockable = false
		var res := hero.receive_hit(req)
		eq(float(res.total), 2000.0 * float(row[1]), "rank %d: a million-damage blow takes %d%%" % [row[0], roundi(float(row[1]) * 100)])
		ok(res.capped, "the result says the guard held")
		ok(hero.alive, "the hero stands")
		hero.free()
	# monsters themselves are not guarded
	var mon := Actor.new()
	mon.team = BH.Team.ENEMY
	mon.stats = blank_stats(50)
	mon._stats_dirty = false
	mon.hp = 1000.0
	host.add_child(mon)
	var hit := DamageRequest.new()
	hit.attacker = blank_stats(50)
	hit.use_weapon = false
	hit.base_min = 5000.0
	hit.base_max = 5000.0
	hit.evadable = false
	hit.blockable = false
	hit.can_crit = false
	mon.receive_hit(hit)
	ok(not mon.alive, "a monster has no guard")
	mon.free()
	done()

## Bosses: the heaviest attacks are compressed, plain strikes barely change.
func test_boss_attack_compression() -> void:
	near(CombatBudget.boss_attack_mult(1.0), CombatBudget.BOSS_DAMAGE, 0.0001, "a plain strike")
	near(CombatBudget.boss_attack_mult(4.2), (1.6 + 2.6 * 0.5) * CombatBudget.BOSS_DAMAGE, 0.0001, "a 4.2x slam hits like 2.9x")
	var def := DB.enemy(&"astrarch")
	var boss := EnemyStats.build(def, 50, {}, [], false, true)
	var norm := EnemyStats.build(def, 50, {}, [])
	eq(int(boss.get_stat(&"threat_rank")), CombatBudget.Rank.BOSS, "boss rank recorded")
	ok(EnemyStats.attack_range(def, boss, 4.2).y < EnemyStats.attack_range(def, norm, 4.2).y * 0.6, "the boss's slam is compressed")
	done()

# ---- hero against hero -----------------------------------------------------------------------------------------------

## A duel between two average heroes of the same level lasts seconds, not frames, at every level.
func test_pvp_duel_length() -> void:
	for level in [10, 30, 50, 100, 300]:
		for pair in [[&"knight", &"mage"], [&"ranger", &"shadowblade"]]:
			var a := geared(pair[0], level).compute_stats()
			var b := geared(pair[1], level).compute_stats()
			ItemCompare._add_weapon_rows(a)
			var req := DamageRequest.new()
			req.attacker = a
			req.target = b
			req.can_crit = false
			req.evadable = false
			req.blockable = false
			req.more.append(["Arena", CombatBudget.pvp_mult(level)])
			var hit := 0.0
			for i in 40:
				hit += DamagePipeline.compute(req, rng(i)).total
			hit /= 40.0
			var aps := maxf(0.3, a.get_stat(&"attacks_per_second"))
			var seconds := b.get_stat(&"max_hp") / maxf(1.0, hit * aps)
			ok(seconds > 4.0 and seconds < 60.0, "L%d %s on %s: %.1f s of basic attacks" % [level, pair[0], pair[1], seconds])
			print("PVP L%d %s->%s hit %d / hp %d = %.1f s" % [level, pair[0], pair[1], hit, b.get_stat(&"max_hp"), seconds])
	done()

## The arena's network hit: the attacker's half and the owner's half give the same number as one machine would.
func test_split_resolution_matches_the_pipeline() -> void:
	var a := geared(&"ranger", 50).compute_stats()
	var b := geared(&"knight", 50).compute_stats()
	for kind in [DamageRequest.Kind.ATTACK, DamageRequest.Kind.SPELL]:
		var req := DamageRequest.new()
		req.kind = kind
		req.attacker = a
		req.target = b
		req.can_crit = false
		req.evadable = false
		req.blockable = false
		if kind == DamageRequest.Kind.SPELL:
			req.use_weapon = false
			req.base_min = 400.0
			req.base_max = 400.0
			req.conversion = {Elements.FIRE: 0.7, Elements.LIGHTNING: 0.3}
		var whole := float(DamagePipeline.compute(req, rng(7)).total)
		var d := Net.offense_pack(req, b.level, rng(7))
		var back := Net.defense_request(d)
		back.target = b
		var split := float(DamagePipeline.compute(back, rng(7)).total)
		near(split, whole, maxf(2.0, whole * 0.02), "kind %d: %d on one machine, %d split" % [kind, whole, split])
		eq(back.attacker.get_stat(&"hero_source"), 1.0, "the owner sees a hero's blow (arena scaling applies there)")
	done()

# ---- the Sand Arena --------------------------------------------------------------------------------------------------

func _begin(level := 30) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "ts": Engine.time_scale}
	_holder = Node3D.new()
	_holder.name = "ArenaTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = geared(&"knight", level)
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"wyman_outpost", &"west_road")
	_player.bind(Game.hero)
	await _frames(3)

func _end() -> void:
	Engine.time_scale = float(_saved.get("ts", 1.0))
	for t in TempoParty.actors(_tree()):
		t.free()
	var a := ArenaGrounds.active()
	if a:
		for f in a.fighters():
			f.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

func _place(p: Node3D, at: Vector3) -> void:
	p.global_position = CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0) + Vector3.UP * 0.05
	if p is CharacterBody3D:
		(p as CharacterBody3D).velocity = Vector3.ZERO

func test_arena_layout_and_population() -> void:
	await _begin(30)
	var arena := ArenaGrounds.active()
	ok(arena != null, "Wyman Outpost has a Sand Arena")
	if arena == null:
		_end()
		done()
		return
	ok(arena.contains(arena.gate), "the gate spawn is on the sand")
	ok(not arena.contains(arena.gate + arena.gate_out * 6.0), "the lane is outside")
	ok(Game.current_map.spawns.has(ArenaGrounds.GATE_SPAWN), "a spawn marker at the gate")
	ok(not arena.contains(Game.current_map.spawn_transform(&"west_road").origin), "the road is not in the arena")
	# the lane leads in: a walkable path from the Fen Road to the middle of the sand
	var nav := _player.get_world_3d().navigation_map
	var road := Game.current_map.spawn_transform(&"west_road").origin
	var reaches := func() -> bool:
		var path := NavigationServer3D.map_get_path(nav, road, arena.center, true)
		return path.size() > 1 and path[path.size() - 1].distance_to(arena.center) < 1.5
	# the navigation mesh finishes baking on a worker thread, so give it a moment
	ok(await _until(reaches, 5.0), "a path from the Fen Road reaches the centre of the sand")
	# the arena fills itself, at the party's level
	ok(await _until(func(): return arena.fighters().size() >= ArenaGrounds.FIGHTERS, 20.0), "adventurers walk in (%d)" % arena.fighters().size())
	# a fighter knocked through the gate walks straight back in, so allow a moment for that
	ok(await _until(func(): return arena.fighters().all(func(f): return arena.contains(f.global_position)), 4.0),
		"every adventurer is on the sand")
	for f in arena.fighters():
		eq(f.level, 30, "%s is level 30, like the hero" % f.display_name)
		ok(not f.is_in_group(&"tempo") and not f.is_in_group(&"ally"), "not a companion")
		ok(f.is_in_group(&"arena_target"), "a target for heroes on the sand")
	_end()
	done()

func test_adventurers_fight_each_other_and_fall_back() -> void:
	await _begin(30)
	var arena := ArenaGrounds.active()
	arena.max_fighters = 0                              # only the two placed here
	Engine.time_scale = 4.0
	var a := arena.spawn_fighter(&"knight", 30)
	var b := arena.spawn_fighter(&"shadowblade", 30)
	_place(a, arena.center + Vector3(-2, 0, 0))
	_place(b, arena.center + Vector3(2, 0, 0))
	ok(await _until(func(): return a.hp < a.max_hp() or b.hp < b.max_hp(), 15.0), "two adventurers fight each other")
	ok(a.target == b or b.target == a, "they target each other")
	# a badly hurt adventurer with no draughts left falls back and uses what it has to get away
	Engine.time_scale = 1.0
	var hurt := a
	var other := b
	hurt.hero.inventory.consume(&"health_potion", hurt.hero.inventory.count_of(&"health_potion"))
	_place(other, hurt.global_position + Vector3(1.5, 0, 0))
	hurt.hp = hurt.max_hp() * 0.15
	hurt.health_changed.emit(hurt.hp, hurt.max_hp())
	ok(await _until(func(): return hurt.mode == Tempo.Mode.RETREAT, 2.0), "%s falls back at %d%% health" % [hurt.display_name, roundi(hurt.hp_frac() * 100)])
	ok(hurt.debug_log.any(func(l): return String(l).contains("retreat")), "the retreat is logged")
	# blows between heroes are scaled and capped
	var req := other._weapon_request(0, 50.0, true, "test")
	req.evadable = false
	req.blockable = false
	var target_hp := other.max_hp()
	var res := other.receive_hit(req, hurt)
	ok(float(res.total) <= target_hp * CombatBudget.PVP_BLOW_CAP + 1.0, "no arena blow takes more than %d%%" % roundi(CombatBudget.PVP_BLOW_CAP * 100))
	_end()
	done()

func test_companions_wait_outside_and_come_back() -> void:
	await _begin(30)
	var arena := ArenaGrounds.active()
	arena.max_fighters = 0
	var t := TempoData.new()
	t.uid = 7701
	t.tempo_name = "Waiter"
	t.class_id = &"swordsman"
	t.trait_id = &"valiant"
	t.skills = [DataTempos.tempo_class(&"swordsman").signature]
	Game.hero.tempos.append(t)
	TempoParty.refresh(Game.hero)
	await _frames(3)
	var tempo := TempoParty.actor_for(7701)
	ok(tempo != null, "the Tempo is out")
	_place(_player, arena.gate + (arena.center - arena.gate).normalized() * 4.0)
	ok(await _until(func(): return tempo.is_waiting(), 3.0), "the Tempo waits when its hero enters")
	await _frames(30)
	ok(not arena.contains(tempo.global_position), "and it stays outside the palisade")
	ok(tempo.invulnerable, "nothing can hurt it while it waits")
	ok(tempo.target == null, "it fights nobody")
	_place(_player, arena.gate + arena.gate_out * 8.0)
	ok(await _until(func(): return not tempo.is_waiting(), 3.0), "it follows again when the hero comes out")
	ok(not tempo.invulnerable, "and can be hurt again")
	_end()
	done()

func test_a_fall_in_the_arena_costs_nothing() -> void:
	await _begin(30)
	var arena := ArenaGrounds.active()
	arena.max_fighters = 0
	_place(_player, arena.center)
	await _frames(2)
	Game.hero.inventory.gold = 5000
	var a := arena.spawn_fighter(&"mage", 30)
	_player.die(a)
	ok(not _player.alive, "the hero falls")
	ok(ArenaGrounds.handles_death(_player), "the arena takes care of it (no death screen)")
	ok(await _until(func(): return _player.alive, ArenaGrounds.RESPAWN_DELAY + 2.0), "the hero stands up again")
	ok(_player.global_position.distance_to(arena.gate) < 2.0, "at the gate")
	eq(_player.hp, _player.max_hp(), "with full health")
	eq(Game.hero.inventory.gold, 5000, "and no gold lost")
	ok(_player.invulnerable, "briefly untouchable")
	# an adventurer cannot hit a hero who is outside the palisade
	_place(_player, arena.gate + arena.gate_out * 8.0)
	await _frames(2)
	var hp := _player.hp
	var req := a._weapon_request(0, 5.0, true, "through the gate")
	req.evadable = false
	_player.invulnerable = false
	_player.receive_hit(req, a)
	eq(_player.hp, hp, "no blows reach past the palisade")
	_end()
	done()
