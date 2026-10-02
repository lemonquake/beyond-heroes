extends TestCase
## bh-007: ingredients and crafting (recipes, stations, gear variants, batches, learning, salvage), Olivar's merchants
## restocking on stage clears and miniboss kills, minibosses and stage clears in the real spawner, Wyman Outpost's
## bonfire checkpoint and hero register, herb patches, and where the new places put their people and stations.

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _hero(cls := &"knight", lvl := 1) -> HeroData:
	var h := Game.new_hero(cls, "Crafter")
	if lvl > 1:
		h.progress.add_xp(XpCurve.total_xp_for_level(lvl) - h.progress.total_xp)
	return h

func _give(h: HeroData, id: StringName, n: int) -> void:
	var it := DB.make_item(id, BH.Rarity.COMMON, 1, 1)
	it.count = n
	h.inventory.add(it)

func _begin(map_id: StringName, spawn: StringName = &"start", lvl := 3) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "CraftTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = _hero(&"knight", lvl)
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, spawn)
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	for t in TempoParty.actors(host.get_tree()):
		t.free()
	for n in host.get_tree().get_nodes_in_group(&"loot"):
		n.free()
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

# ---- data ---------------------------------------------------------------------------------------------------------

func test_recipes_and_ingredients_are_consistent() -> void:
	var ids := {}
	for r in DataCrafting.all():
		ok(not ids.has(r.id), "recipe %s unique" % r.id)
		ids[r.id] = true
		ok(not (r.stations as Array).is_empty(), "%s has a station" % r.id)
		for st in r.stations:
			ok(DataCrafting.STATIONS.has(st), "%s: station %s exists" % [r.id, st])
		for inp in r.inputs:
			ok(DB.item_base(inp[0]) != null, "%s: input %s exists" % [r.id, inp[0]])
			ok(int(inp[1]) > 0, "%s: input count positive" % r.id)
		var out: Dictionary = r.out
		if out.has("base"):
			ok(DB.item_base(out.base) != null, "%s: output %s exists" % [r.id, out.base])
		else:
			ok(out.has("gear") and not (r.get("variants", []) as Array).is_empty(), "%s: gear recipe has variants" % r.id)
		if not bool(r.get("known", false)):
			ok(Crafting.scroll_for(StringName(r.id)) != &"", "%s is learned from a scroll" % r.id)
	for s in DataCrafting.SCROLLS:
		var b := DB.item_base(s[0])
		ok(b != null and b.consumable_effect.get("learn_recipe", "") == String(s[1]), "scroll %s teaches %s" % [s[0], s[1]])
		ok(b != null and b.drop_weight == 0, "scroll %s is not a random drop" % s[0])
	# every new ingredient has a source: an enemy, a herb patch, a recipe, or a miniboss
	var sources := {}
	for e: EnemyDef in DB.enemies.values():
		for l in e.loot:
			sources[l[0]] = true
	for h in GatherNode.LOOK:
		sources[h] = true
	for r in DataCrafting.all():
		if (r.out as Dictionary).has("base"):
			sources[r.out.base] = true
	sources[&"champion_essence"] = true
	for m in DataCrafting.MATERIALS:
		ok(sources.has(m[0]), "%s can be obtained" % m[0])
		ok(Tips.material_uses(m[0]) != "", "%s is used in a recipe" % m[0])
	# every enemy family drops at least one crafting ingredient
	var fams := {}
	var used := {}
	for r in DataCrafting.all():
		for inp in r.inputs:
			used[inp[0]] = true
	for e: EnemyDef in DB.enemies.values():
		# Summoned hazards such as Rot Buds deliberately grant no XP or loot.
		if e.xp_mult <= 0.0 and e.drop_chance <= 0.0 and e.loot.is_empty():
			continue
		fams.get_or_add(e.family, false)
		for l in e.loot:
			if used.has(l[0]):
				fams[e.family] = true
	for f in fams:
		ok(fams[f], "the %s family drops a crafting ingredient" % f)
	done()

# ---- crafting rules -------------------------------------------------------------------------------------------------

func test_craft_consumes_exactly_and_refuses_cleanly() -> void:
	var h := _hero()
	h.inventory.gold = 100
	_give(h, &"silverleaf", 5)
	var r := DataCrafting.recipe(&"health_potion")
	var before := h.inventory.count_of(&"health_potion")
	var res := Crafting.craft(h, r, &"alchemy", 2)
	ok(res.ok, "two batches of health draughts (%s)" % res.get("error", ""))
	eq(h.inventory.count_of(&"silverleaf"), 1, "exactly 4 silverleaf used")
	eq(h.inventory.count_of(&"health_potion"), before + 4, "2 x 2 draughts made")
	eq(h.inventory.gold, 96, "fee 2 gold per batch")
	eq(h.crafted_count, 2, "crafted counter")
	var gold := h.inventory.gold
	var fail := Crafting.craft(h, r, &"alchemy", 1)
	ok(not fail.ok and String(fail.error).begins_with("Missing"), "refuses without enough herbs (%s)" % fail.get("error", ""))
	eq(h.inventory.gold, gold, "nothing taken on refusal")
	_give(h, &"silverleaf", 4)
	ok(Crafting.check(h, r, &"forge") != "", "a forge cannot brew draughts")
	ok(Crafting.check(h, r, &"workbench") == "", "the camp workbench can")
	var locked := DataCrafting.recipe(&"berserker_draught")
	ok(Crafting.check(_hero(&"knight", 9), locked, &"alchemy") == "Recipe not learned", "scroll recipes start locked")
	var high := DataCrafting.recipe(&"greater_health_potion")
	ok(Crafting.check(h, high, &"alchemy").begins_with("Requires level"), "level gate")
	h.inventory.gold = 0
	ok(Crafting.check(h, r, &"alchemy").begins_with("Not enough gold"), "fee gate")
	# a full bag refuses before anything is taken
	var full := _hero()
	full.inventory.gold = 500
	_give(full, &"iron_shard", 5)
	var n := 0
	while full.inventory.free_cells() > 0 and n < 200:
		full.inventory.add(DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 1, 100 + n))
		n += 1
	var ingot := DataCrafting.recipe(&"steel_ingot")
	ok(Crafting.check(full, ingot, &"forge") == "", "an ingot fits where its shards were (the stack frees a cell)")
	var weapon := DataCrafting.recipe(&"tempered_weapon")
	_give(full, &"steel_ingot", 2)
	ok(Crafting.check(full, weapon, &"forge") != "", "gear needs the materials and a free cell")
	done()

func test_gear_recipes_make_the_chosen_kind_at_the_heroes_level() -> void:
	var r := DataCrafting.recipe(&"tempered_weapon")
	for cls_case in [[&"knight", &"sword"], [&"knight", &"spear"], [&"mage", &"staff"], [&"mage", &"wand"]]:
		var h := _hero(cls_case[0], 12)
		h.inventory.gold = 1000
		_give(h, &"steel_ingot", 2)
		_give(h, &"cured_leather", 1)
		_give(h, &"wolf_fang", 2)
		var v := -1
		for i in (r.variants as Array).size():
			if (r.variants[i].get("weapon_types", []) as Array).has(cls_case[1]):
				v = i
		var rng := RandomNumberGenerator.new()
		rng.seed = 42
		var res := Crafting.craft(h, r, &"forge", 1, v, rng)
		ok(res.ok, "%s crafts a %s (%s)" % [cls_case[0], cls_case[1], res.get("error", "")])
		if res.ok:
			var it: ItemInstance = res.items[0]
			eq(it.base.weapon_type, cls_case[1], "the chosen kind")
			eq(it.rarity, BH.Rarity.ADVANCED, "Advanced")
			ok(it.crafted, "marked crafted")
			ok(it.quality >= 0.08, "fine quality (%.2f)" % it.quality)
			ok(it.base.level_req <= 12 and it.base.level_req >= 5, "a base the hero can use, not a starter (%s, req %d)" % [it.base.id, it.base.level_req])
			ok(h.inventory.index_of(it) >= 0, "into the bag")
			var back := ItemInstance.from_dict(JSON.parse_string(JSON.stringify(it.to_dict())))
			ok(back.crafted and absf(back.quality - it.quality) < 0.001, "crafted flag and quality survive a save")
	var armor := DataCrafting.recipe(&"tempered_armor")
	var h2 := _hero(&"mage", 6)
	h2.inventory.gold = 1000
	_give(h2, &"steel_ingot", 1)
	_give(h2, &"cured_leather", 2)
	_give(h2, &"beast_hide", 2)
	var res2 := Crafting.craft(h2, armor, &"forge", 1, 0)
	ok(res2.ok and res2.items[0].base.category == &"helm", "the first armor variant makes a helm")
	if res2.ok:
		eq(res2.items[0].base.class_hint, &"mage", "a mage gets a mage's helm")
	done()

func test_learning_scrolls_and_saves() -> void:
	var h := _hero(&"knight", 9)
	ok(Crafting.learn(h, &"berserker_draught") == "", "a scroll teaches its recipe")
	ok(Crafting.is_known(h, DataCrafting.recipe(&"berserker_draught")), "now known")
	ok(Crafting.learn(h, &"berserker_draught") != "", "a second copy is refused (not wasted)")
	ok(Crafting.learn(h, &"no_such_recipe") != "", "unknown recipes are refused")
	h.clear_count = 4
	h.checkpoint = {"map": "wyman_outpost", "spawn": "bonfire", "name": "Wyman Outpost"}
	h.miniboss_log[&"snagtooth"] = {"kills": 2, "at": 33.5}
	h.stages_cleared[&"westreach"] = 3
	h.gather_log["westreach/3"] = 12.0
	h.crafted_count = 7
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	ok(back.known_recipes.has(&"berserker_draught"), "learned recipes survive a save")
	eq(back.clear_count, 4, "clear counter saved")
	eq(back.checkpoint.get("spawn", ""), "bonfire", "checkpoint saved")
	eq(int(back.miniboss_log[&"snagtooth"].kills), 2, "miniboss log saved")
	eq(int(back.stages_cleared[&"westreach"]), 3, "stage clears saved")
	near(float(back.gather_log.get("westreach/3", 0.0)), 12.0, 0.001, "picked herbs saved")
	eq(back.crafted_count, 7, "crafted count saved")
	var old := h.to_dict()
	for k in ["known_recipes", "clear_count", "checkpoint", "miniboss_log", "stages_cleared", "gather_log", "crafted_count"]:
		old.erase(k)
	var legacy := HeroData.from_dict(old)
	ok(legacy != null and legacy.clear_count == 0 and legacy.checkpoint.is_empty(), "older saves load without the new keys")
	done()

func test_salvage() -> void:
	var h := _hero(&"knight", 10)
	var plate := ItemGenerator.generate(DB.item_base(&"iron_longsword"), 10, BH.Rarity.ELITE, RandomNumberGenerator.new())
	h.inventory.add(plate)
	var y := DataCrafting.salvage_yield(plate)
	ok(y.any(func(e): return e[0] == &"iron_shard"), "blades give iron")
	ok(y.any(func(e): return e[0] == &"arcane_dust"), "enchanted gear gives dust")
	ok(y.any(func(e): return e[0] == &"wisp_mote"), "Elite gear gives a wisp mote")
	var res := Crafting.salvage(h, plate)
	ok(res.ok and h.inventory.index_of(plate) < 0, "salvaged away")
	ok(h.inventory.count_of(&"iron_shard") > 0, "materials in the bag")
	var keep := ItemGenerator.generate(DB.item_base(&"iron_longsword"), 10, BH.Rarity.COMMON, RandomNumberGenerator.new())
	keep.locked = true
	h.inventory.add(keep)
	ok(not Crafting.salvage(h, keep).ok, "locked items are never salvaged")
	ok(not Crafting.salvage(h, null).ok, "nothing to salvage")
	done()

# ---- Olivar -------------------------------------------------------------------------------------------------------

func test_olivar_restocks_on_clears_only() -> void:
	var h := _hero(&"knight", 8)
	for sid in [&"olivar_arms", &"olivar_jewels", &"olivar_alchemy"]:
		var def := DB.shop(sid)
		ok(def != null and def.restock_on_clears, "%s restocks on clears" % sid)
		ok(DB.npc(def.npc) != null and DB.npc(def.npc).map == &"olivar", "%s is kept by someone in Olivar" % sid)
	var arms := DB.shop(&"olivar_arms")
	var s1 := Shop.open(arms, h)
	var sig1 := s1.stock.map(func(e): return e.item.to_dict())
	h.play_time += 3600.0 * 10.0
	var s2 := Shop.open(arms, h)
	eq(s2.stock.map(func(e): return e.item.to_dict()), sig1, "time alone never restocks Olivar")
	for e in s2.stock:
		var it: ItemInstance = e.item
		if it.is_equipment():
			ok(it.rarity >= BH.Rarity.ADVANCED, "%s is Advanced or better" % it.display_name())
			ok(it.ilvl >= h.progress.level + 3, "%s is forged above the hero's level (ilvl %d)" % [it.display_name(), it.ilvl])
	var price := ShopPricing.buy_total(s2.stock[0].item, arms, 1, 0, 0.0)
	ok(price > s2.stock[0].item.base_value(), "premium prices")
	h.add_clear()
	var s3 := Shop.open(arms, h)
	ok(s3.stock.map(func(e): return e.item.to_dict()) != sig1, "a clear rerolls the stock")
	eq(s3.refresh_index, s1.refresh_index + 1, "one restock per clear")
	var s4 := Shop.open(arms, h)
	eq(s4.refresh_index, s3.refresh_index, "no second restock without another clear")
	# the town's normal merchants keep their timers
	ok(not DB.shop(&"tovin_goods").restock_on_clears and not DB.shop(&"wyman_supplies").restock_on_clears, "only Olivar cycles on clears")
	done()

# ---- minibosses and stage clears ------------------------------------------------------------------------------------

func test_miniboss_data() -> void:
	for m in DataMinibosses.LIST:
		ok(DB.enemy(m.enemy) != null, "%s: enemy %s exists" % [m.id, m.enemy])
		ok(DB.map_def(m.map) != null and not DB.map_def(m.map).is_town, "%s holds a combat map" % m.id)
		for mod in m.mods:
			ok(DB.elite_mods.has(mod), "%s: modifier %s exists" % [m.id, mod])
		ok(String(m.name) != "" and String(m.title) != "", "%s has a name and a title" % m.id)
	var h := _hero()
	ok(not DataMinibosses.resting(h, &"snagtooth"), "a new hero finds every champion home")
	h.miniboss_log[&"snagtooth"] = {"kills": 1, "at": h.play_time}
	ok(DataMinibosses.resting(h, &"snagtooth"), "a beaten champion rests")
	h.play_time += DataMinibosses.RESPAWN + 1.0
	ok(not DataMinibosses.resting(h, &"snagtooth"), "and comes back after %d s of play" % int(DataMinibosses.RESPAWN))
	ok(DataMinibosses.rumours(h).find("Snagtooth") >= 0, "the rumour-monger names them")
	ok(not DataMinibosses.scroll_pool().is_empty(), "minibosses can drop recipe scrolls")
	done()

func test_westreach_champions_and_stage_clear() -> void:
	await _begin(&"westreach", &"town_gate", 3)
	var sp := Game.current_map.get_node_or_null(^"Spawner") as Spawner
	ok(sp != null, "the spawner runs")
	var names := sp.minibosses.map(func(e): return e.miniboss.id)
	for m in DataMinibosses.on_map(&"westreach"):
		ok(names.has(m.id), "%s holds its camp" % m.name)
	for e in sp.minibosses:
		ok(e.is_miniboss() and e.is_elite and e.display_name == e.miniboss.name, "%s is a named elite" % e.display_name)
		var plain := Spawner.spawn_enemy(_holder, e.def, e.level, e.elite_mods, Vector3(500, 0, 500), sp.difficulty)
		await host.get_tree().process_frame
		ok(e.max_hp() > plain.max_hp() * 1.4, "%s is much tougher than an elite (%d vs %d HP)" % [e.display_name, e.max_hp(), plain.max_hp()])
		plain.free()
	ok(sp.camp_total() >= 4, "Westreach has its camps (%d)" % sp.camp_total())
	var events := {"camp": 0, "stage": 0, "boss": 0, "clears": 0}
	var on_camp := func(_m, _z, _l, _t): events.camp += 1
	var on_stage := func(_m): events.stage += 1
	var on_boss := func(_id): events.boss += 1
	Events.camp_cleared.connect(on_camp)
	Events.stage_cleared.connect(on_stage)
	Events.miniboss_defeated.connect(on_boss)
	var h := Game.hero
	var c0 := h.clear_count
	# a champion falls: logged, counted, and it will not be there on the next load
	var champ: Enemy = sp.minibosses[0]
	var champ_id := StringName(champ.miniboss.id)
	champ.die(_player)
	eq(events.boss, 1, "miniboss_defeated fires")
	eq(h.clear_count, c0 + 1, "a champion kill counts as a clear")
	ok(DataMinibosses.resting(h, champ_id), "the champion rests")
	ok(host.get_tree().get_nodes_in_group(&"loot").any(func(n): return n.item != null and n.item.base.id == &"champion_essence"), "it drops Champion Essence")
	# every camp cleared: exactly one stage clear
	for zone in sp.camps:
		for e in sp.camps[zone]:
			if is_instance_valid(e) and e.alive:
				e.die(_player)
	eq(events.camp, sp.camp_total(), "every camp reports its clear")
	eq(events.stage, 1, "one stage clear")
	eq(h.clear_count, c0 + 2, "the stage clear counts too")
	eq(int(h.stages_cleared.get(&"westreach", 0)), 1, "remembered per map")
	Events.camp_cleared.disconnect(on_camp)
	Events.stage_cleared.disconnect(on_stage)
	Events.miniboss_defeated.disconnect(on_boss)
	# reload: the beaten champion stays away, the others are back
	Game.load_map(&"westreach", &"town_gate")
	await host.get_tree().physics_frame
	var sp2 := Game.current_map.get_node_or_null(^"Spawner") as Spawner
	ok(not sp2.minibosses.any(func(e): return StringName(e.miniboss.id) == champ_id), "the beaten champion is not back yet")
	eq(sp2.minibosses.size(), DataMinibosses.on_map(&"westreach").size() - 1, "the others hold their camps")
	_end()
	done()

# ---- Wyman Outpost ------------------------------------------------------------------------------------------------

func test_wyman_checkpoint_register_and_heroes() -> void:
	await _begin(&"wyman_outpost", &"start", 5)
	var fires := host.get_tree().get_nodes_in_group(&"checkpoint")
	eq(fires.size(), 1, "one bonfire")
	var fire := fires[0] as CampBonfire
	ok(Game.current_map.spawns.has(fire.spawn_id), "the bonfire has a wake spawn")
	_player.hp = 1.0
	Game.hero.inventory.gold = 50
	eq(fire.rest(Game.hero, _player), "", "resting is free")
	eq(Game.hero.inventory.gold, 50, "no fee")
	near(_player.hp, _player.max_hp(), 0.5, "fully restored")
	eq(Game.checkpoint_name(), "Wyman Outpost", "checkpoint set")
	ok(fire.is_current(), "the bonfire knows it is the checkpoint")
	var heroes := HeroRosterWindow.entries(&"wyman_outpost", Game.hero)
	ok(heroes.size() >= 8, "the register lists the camp's heroes and you (%d)" % heroes.size())
	for i in heroes.size() - 1:
		ok(heroes[i].level >= heroes[i + 1].level, "sorted by level")
	ok(heroes.any(func(e): return e.you), "you are on the register")
	for d: NpcDef in DB.npcs.values():
		if not d.is_hero():
			continue
		ok(d.hero_tier == 0 or d.hero_level >= int(DataGuilds.tier(d.hero_tier).level), "%s's tier fits their level" % d.display_name)
		ok(d.hero_guild == &"" or DataGuilds.GUILDS.has(d.hero_guild), "%s's guild exists" % d.display_name)
		ok(d.weapon == &"" or DB.item_base(d.weapon) != null, "%s's weapon exists" % d.display_name)
	var npcs := host.get_tree().get_nodes_in_group(&"npc")
	var plates := npcs.filter(func(n): return n is Npc and n.def.is_hero())
	ok(plates.size() >= 8, "the heroes stand in camp (%d)" % plates.size())
	for n in plates:
		ok((n as Npc).plate_text().find("Lv %d" % n.def.hero_level) >= 0, "%s's plate shows the level" % n.def.display_name)
	ok(host.get_tree().get_nodes_in_group(&"interactable").any(func(n): return n is RosterBoard), "the register board")
	_end()
	done()

## Stations, herb patches and townspeople of the new places stand on walkable ground.
func test_new_places_are_reachable() -> void:
	for id in [&"olivar", &"wyman_outpost", &"westreach", &"ruined_forest", &"sanctuary"]:
		await _begin(id, &"start" if id != &"westreach" else &"town_gate", 3)
		var map := Game.current_map
		var nm := map.nav_region.get_navigation_map()
		var nodes: Array = []
		nodes.append_array(host.get_tree().get_nodes_in_group(&"crafting_station"))
		nodes.append_array(host.get_tree().get_nodes_in_group(&"gather_node"))
		if id == &"olivar" or id == &"wyman_outpost":
			nodes.append_array(host.get_tree().get_nodes_in_group(&"npc").filter(func(n): return n.def.id != &"yorick"))
		for n in nodes:
			var p: Vector3 = (n as Node3D).global_position
			var q := NavigationServer3D.map_get_closest_point(nm, p)
			ok(Vector2(q.x, q.z).distance_to(Vector2(p.x, p.z)) < 2.2, "%s on %s can be walked up to (%.1f m)" % [n.name, id, Vector2(q.x, q.z).distance_to(Vector2(p.x, p.z))])
		var stations := host.get_tree().get_nodes_in_group(&"crafting_station").map(func(s): return s.station)
		match id:
			&"sanctuary": ok(stations.has(&"forge"), "Malasugue has Brannoc's anvil")
			&"olivar": ok(stations.has(&"alchemy"), "Olivar has an alchemy table")
			&"wyman_outpost": ok(stations.has(&"forge") and stations.has(&"workbench") and stations.has(&"alchemy"), "Wyman has forge, workbench and kettle")
		_end()
	done()

func test_herb_patches_pick_and_regrow() -> void:
	await _begin(&"westreach", &"town_gate", 2)
	var herbs := host.get_tree().get_nodes_in_group(&"gather_node")
	ok(herbs.size() >= 8, "Westreach has herb patches (%d)" % herbs.size())
	var g := herbs[0] as GatherNode
	var id := g.herb
	var key := g.key
	var n := g.gather(Game.hero)
	ok(n >= 1 and n <= 3, "picked 1-3")
	eq(Game.hero.inventory.count_of(id), n, "into the bag")
	ok(not g.can_interact(_player), "a picked patch is bare")
	eq(g.gather(Game.hero), 0, "cannot be picked twice")
	Game.load_map(&"westreach", &"town_gate")
	await host.get_tree().physics_frame
	var again := host.get_tree().get_nodes_in_group(&"gather_node").filter(func(x): return is_instance_valid(x) and x.key == key)
	ok(not again.is_empty() and not again[0].is_ready(), "still bare after reloading the map")
	Game.hero.play_time += GatherNode.REGROW + 1.0
	ok(again[0].is_ready(), "regrows with time")
	_end()
	done()
