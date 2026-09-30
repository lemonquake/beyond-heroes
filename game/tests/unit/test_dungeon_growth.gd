extends TestCase

func _init() -> void:
	strict = true

func hero(level: int, cls := &"knight") -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls), "Depth test")
	h.init_new()
	h.progress.level = level
	return h

func test_thresholds_and_scaling() -> void:
	for row in [[24, 0], [25, 1], [34, 1], [35, 2], [44, 2], [45, 3], [49, 3], [50, 4], [55, 5], [60, 6], [100, 6]]:
		eq(DungeonGrowth.profile(row[0]).extra, row[1], "depth at %d" % row[0])
	for id in DataDungeons.order():
		var previous := Vector2i.ZERO
		for level in range(1, 61):
			var g := DungeonGrowth.profile(level)
			var lv := DungeonGrowth.levels(id, 1, g)
			ok(lv.x >= previous.x and lv.y >= previous.y, "%s scales monotonically at %d" % [id, level])
			ok(lv.x <= lv.y and lv.y <= BH.LEVEL_CAP, "bounded level range")
			previous = lv
		var early := DungeonGrowth.levels(id, 1, DungeonGrowth.profile(24))
		eq(early.x, DataDungeons.get_def(id).levels[0][0], "early dungeon unchanged")
		var deep := DungeonGrowth.levels(id, DataDungeons.floor_count(id) + 1, DungeonGrowth.profile(25))
		ok(deep.x >= 25, "new depths can drop level 25 equipment immediately")
	ok(DungeonGrowth.profile(50).elite_bonus > DungeonGrowth.profile(49).elite_bonus + 0.1, "50 is a significant change")
	done()

func test_visit_snapshot_and_save() -> void:
	var h := hero(24)
	DungeonGrowth.enter(h, &"dg_warren_1")
	h.current_map = &"dg_warren_1"
	h.progress.level = 50
	eq(DungeonGrowth.for_hero(h, &"warren").extra, 0, "mid-run leveling does not change floors")
	DungeonGrowth.enter(h, &"dg_warren_2")
	eq(DungeonGrowth.for_hero(h, &"warren").level, 24, "descending retains snapshot")
	var back := HeroData.from_dict(h.to_dict())
	eq(DungeonGrowth.for_hero(back, &"warren").level, 24, "save/load retains snapshot")
	h.current_map = &"westreach"
	DungeonGrowth.enter(h, &"dg_warren_1")
	h.current_map = &"dg_warren_1"
	eq(DungeonGrowth.for_hero(h, &"warren").extra, 4, "return visit adopts new level")
	eq(DataDungeons.reached_floors(h, &"warren"), [1], "no floor skip before clearing")
	for n in range(1, 4):
		h.world_flags[DataDungeons.seal_flag(&"warren", n)] = true
	eq(DataDungeons.reached_floors(h, &"warren"), [1, 2, 3, 4], "original progress preserved")
	h.world_flags[DataDungeons.cleared_flag(&"warren")] = true
	eq(DataDungeons.reached_floors(h, &"warren"), [1, 2, 3, 4, 5], "lord opens first added floor")
	h.world_flags[DataDungeons.seal_flag(&"warren", 7)] = true
	eq(DataDungeons.reached_floors(h, &"warren"), [1, 2, 3, 4, 5], "isolated old flag cannot skip uncompleted floors")
	var guest := hero(25)
	DungeonGrowth.enter(guest, &"dg_warren_10")
	guest.current_map = &"dg_warren_10"
	eq(DungeonGrowth.for_hero(guest, &"warren").extra, 6, "party return point keeps deep floor geometry valid")
	eq(DungeonGrowth.level_notice(50, 2), "Level 50: greater dungeon depths, larger packs and stronger elites appear on your next visit.", "crossed milestone notice")
	eq(DungeonGrowth.level_notice(51, 1), "", "no repeated notice")
	done()

func test_plans_and_reinforcements() -> void:
	for id in DataDungeons.order():
		var dd := DataDungeons.get_def(id)
		for depth in range(1, 7):
			var n := DataDungeons.floor_count(id) + depth
			var f := DataDungeons.floor_def(id, n)
			ok(DB.map_def(DataDungeons.map_id(id, n)) != null, "extended floor registered")
			var width: int = f.plan[0].length()
			for line in f.plan:
				eq(line.length(), width, "rectangular floor plan")
			var visited := {f.arrival: true}
			var queue := [f.arrival]
			while not queue.is_empty():
				var cell: Vector2i = queue.pop_front()
				for offset in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
					var next: Vector2i = cell + offset
					if next.x >= 0 and next.x < width and next.y >= 0 and next.y < f.plan.size() and not visited.has(next) and String(f.plan[next.y])[next.x] in ["0", "="]:
						visited[next] = true
						queue.append(next)
			for marker in [f.descent, f.seal] + f.camps.map(func(c): return c[0]) + f.chests.map(func(c): return c[0]):
				ok(visited.has(marker), "all gameplay markers reachable")
		for stage in [25, 50]:
			for seed_value in range(-8, 8):
				var pool := DungeonGrowth.pool(id, dd.pools.a, DungeonGrowth.profile(stage), seed_value)
				for eid in pool:
					ok(DB.enemy(eid) != null, "reinforcement %s registered" % eid)
				ok(pool[0] in DungeonGrowth.REINFORCEMENTS[dd.theme], "reinforcements occupy spawned positions")
	done()

func test_catalog_models_stats_and_class_loot() -> void:
	eq(DataDepthEquipment.ROWS.size(), 84, "80 new equipment designs + 4 depth leggings (bh-024)")
	var ids := {}
	var swords := 0
	var specials := 0
	for row in DataDepthEquipment.ROWS:
		var b := DB.item_base(StringName(row[0]))
		ok(b != null and not ids.has(b.id), "unique registered equipment")
		ids[b.id] = true
		ok(ResourceLoader.exists(b.model) and ResourceLoader.exists(b.icon), "%s has real model and rendered icon" % b.id)
		var model := ItemModels.instance(b)
		ok(ItemModels.bounds(model).size.length() > 0.1, "non-empty model")
		model.free()
		for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
			eq(ItemGenerator.class_fit(b, cls), cls == b.class_hint, "explicit class identity")
		if b.weapon_type == &"sword":
			swords += 1
		if b.unique_name != "":
			specials += 1
			var it := ItemGenerator.generate(b, b.drop_level, BH.Rarity.COMMON, rng(5))
			for power in b.fixed_powers:
				ok(DB.power(power) != null and it.powers.has(String(power)), "relic has a working registered power")
		var item := ItemGenerator.generate(b, b.drop_level, BH.Rarity.ADVANCED, rng(9))
		eq(ItemInstance.from_dict(item.to_dict()).base.id, b.id, "new equipment survives saves")
	eq(swords, 12, "twelve new sword designs")
	eq(specials, 8, "eight new named relics")
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var random := rng(456)
		var found := {}
		for i in 1200:
			var b := ItemGenerator.random_base(random, 60, [], cls, 1.0)
			ok(ItemGenerator.class_fit(b, cls), "class-specific drop")
			found[b.id] = true
		ok(found.keys().filter(func(id): return String(id).begins_with("depth_")).size() >= 15, "many new designs actually drop")
		eq(DataDepthEquipment.special(random, 24, cls), null, "specials gated until 25")
		ok(DataDepthEquipment.special(random, 25, cls) != null, "specials available from 25")
	done()

func test_live_floor_guards_treasure_and_exit() -> void:
	var old_hero := Game.hero
	Game.hero = hero(50)
	Game.hero.current_map = &"dg_warren_8"
	Game.hero.world_flags[DungeonGrowth.visit_key(&"warren")] = 50
	DataDungeons.record_raid(Game.hero, &"warren", 60.0)
	var map := Game.build_map(&"dg_warren_8")
	host.add_child(map)
	var nav := MapBuilder.isolate_navigation(map)
	MapBuilder.bake_navigation(map)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	var nm := map.nav_region.get_navigation_map()
	var arrival := NavigationServer3D.map_get_closest_point(nm, map.spawn_transform(&"arrival").origin)
	for marker in map.find_children("EnemyZone_*", "Marker3D", true, false):
		var target := NavigationServer3D.map_get_closest_point(nm, marker.global_position)
		var route := NavigationServer3D.map_get_path(nm, arrival, target, true)
		ok(not route.is_empty() and route[-1].distance_to(target) < 0.5, "built navigation reaches every camp")
	var sp := Spawner.populate(map, 1)
	ok(sp.spawned.size() >= 30, "deeper floors stay populated during original raid recovery")
	var guardians := sp.spawned.filter(func(e): return e.has_meta(&"depth_guardian"))
	eq(guardians.size(), 1, "exactly one named guardian")
	if not guardians.is_empty():
		ok(guardians[0].is_miniboss(), "guardian is initialized as a champion")
		eq(guardians[0].elite_mods.size(), 3, "greater-depth guardian has three elite abilities")
	var old_map := Game.current_map
	Game.current_map = map
	if not guardians.is_empty():
		guardians[0].set_meta(&"net_id", 701)
		var copy := NetWorld.make_enemy(Net.enemy_info(guardians[0]), true)
		ok(copy.is_miniboss() and copy.has_meta(&"depth_guardian"), "network replica keeps guardian identity")
		eq(copy.get_meta(&"dungeon_reward_bonus"), guardians[0].get_meta(&"dungeon_reward_bonus"), "network replica keeps reward profile")
		copy.free()
	Game.current_map = old_map
	var chests := map.find_children("Chest_*", "Node3D", true, false)
	ok(not chests.is_empty(), "treasure exists")
	for chest in chests:
		if chest is TreasureChest:
			ok(chest.guardian_alive(), "treasure locked while guardian pack lives")
	for e in sp.camps[DataDungeons.SEAL_ZONE]:
		e.alive = false
	sp._on_actor_died(sp.camps[DataDungeons.SEAL_ZONE][0], null)
	ok(Game.hero.world_flags.get(DataDungeons.seal_flag(&"warren", 8), false), "clearing final pack opens final exit")
	for chest in chests:
		if chest is TreasureChest:
			ok(not chest.guardian_alive(), "clearing pack unlocks treasure")
	map.free()
	NavigationServer3D.free_rid(nav)
	Game.hero = old_hero
	done()

func test_guardian_rewards_and_bundle_variety() -> void:
	var saved_rng := Loot.rng.state
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var player := Player.new()
		player.hero = hero(60, cls)
		player.stats = player.hero.compute_stats()
		for level in [25, 50]:
			Loot.rng.seed = 2573 + level
			var guardian := Enemy.new().setup(DB.enemy(&"mycelid_hulk"), level, [&"shielded"])
			guardian.make_miniboss({"id": &"reward_test", "name": "Test Guardian"})
			guardian.set_meta(&"depth_guardian", true)
			guardian.set_meta(&"dungeon_reward_bonus", DungeonGrowth.profile(level).reward_bonus)
			var relics := 0
			for i in 100:
				var seen := {}
				var drops := Loot.equipment_for(guardian, player)
				ok(drops.size() >= 3 and drops[0].base.is_weapon(), "guardian guarantees gear and a class weapon")
				for item: ItemInstance in drops:
					ok(item.base.boss_exclusive or ItemGenerator.class_fit(item.base, cls), "ordinary guardian gear fits receiver; boss collections keep all sets possible")
					ok(not seen.has(item.base.id), "no repeated base in a reward bundle")
					seen[item.base.id] = true
					if String(item.base.id).begins_with("depth_") and item.base.unique_name != "":
						relics += 1
			ok(relics >= (20 if level == 25 else 45) and relics <= (55 if level == 25 else 85), "guardian relic rate stays in its expected band")
			guardian.free()
		player.free()
	Loot.rng.state = saved_rng
	done()
