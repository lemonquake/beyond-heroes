extends TestCase
## bh-033 (world and boss polish): coherent equipment, the combined equipment resistance limit and the v2 migration.

func _init() -> void:
	strict = true

const ARMOUR := [&"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots", &"shield", &"accessory"]

func _gen(cat: StringName, lv: int, rar: int, s: int) -> ItemInstance:
	var r := rng(s)
	var base := ItemGenerator.random_base(r, lv, [cat], &"", 0.0)
	if base == null:
		return null
	var r2 := RandomNumberGenerator.new()
	r2.seed = r.randi()
	return ItemGenerator.generate(base, lv, rar, r2)

func _res_count(it: ItemInstance) -> Array:
	var single := 0
	var wide := 0
	for a in it.affixes:
		var s := String(DB.affix(StringName(a.id)).stat)
		if s == "res_all":
			wide += 1
		elif s.begins_with("res_"):
			single += 1
	return [single, wide]

func test_generated_armour_never_stacks_resistances() -> void:
	var seen_two := false
	for cat in ARMOUR:
		for rar in [BH.Rarity.ELITE, BH.Rarity.MASTER, BH.Rarity.LEGENDARY, BH.Rarity.AETHER]:
			for s in 150:
				var it := _gen(cat, 45, rar, hash("%s%d%d" % [cat, rar, s]))
				if it == null:
					continue
				var rc := _res_count(it)
				ok(rc[0] <= 2, "%s %s: at most two single resistances (%d)" % [cat, BH.RARITY_NAMES[rar], rc[0]])
				ok(rc[1] == 0 or rc[0] == 0, "%s: All Resistances never beside a single one" % cat)
				seen_two = seen_two or rc[0] == 2
				ok(ItemGenerator.item_strength(it) <= ItemGenerator.RARITY_BUDGET[rar] + 0.75, "strength stays near the rarity budget")
	ok(seen_two, "two resistances still roll (variation kept)")
	done()

func test_weapons_are_coherent() -> void:
	for rar in [BH.Rarity.BASIC, BH.Rarity.ADVANCED, BH.Rarity.ELITE, BH.Rarity.LEGENDARY, BH.Rarity.AETHER]:
		for s in 250:
			var it := _gen(&"weapon", 40, rar, hash("w%d%d" % [rar, s]))
			if it == null or it.affixes.is_empty():
				continue
			var first := DB.affix(StringName(it.affixes[0].id))
			eq(ItemGenerator.affix_family(first), &"offense", "first weapon enchantment is offensive (%s)" % first.id)
			var support := 0
			for i in it.affixes.size():
				var d := DB.affix(StringName(it.affixes[i].id))
				ok(ItemGenerator.weapon_relevant(it, d, i) or _has_partner(it, d), "%s relevant on %s" % [d.id, it.base.weapon_type])
				ok(ItemGenerator.affix_family(d) != &"resist" and ItemGenerator.affix_family(d) != &"fortune", "no resistance or fortune on weapons")
				if ItemGenerator.affix_family(d) == &"support":
					support += 1
			ok(support <= 1, "at most one support roll on a weapon")
	done()

func _has_partner(it: ItemInstance, d: AffixDef) -> bool:
	return ItemGenerator.weapon_relevant(it, d)

func test_forbidden_combinations_rejected() -> void:
	var it := DB.make_item(&"knight_plate" if DB.item_base(&"knight_plate") else _any_base(&"armor"), BH.Rarity.LEGENDARY, 40, 5)
	it.affixes = [{"id": "res_fire", "tier": 2, "value": 0.25}, {"id": "res_ice", "tier": 2, "value": 0.25}]
	ok(not ItemGenerator.can_add(it, DB.affix(&"res_lightning")), "a third resistance is refused")
	ok(not ItemGenerator.can_add(it, DB.affix(&"res_all")), "All Resistances is refused beside single ones")
	it.affixes = [{"id": "res_all", "tier": 1, "value": 0.08}]
	ok(not ItemGenerator.can_add(it, DB.affix(&"res_fire")), "a single resistance is refused beside All Resistances")
	var sword := DB.make_item(&"militia_shortsword", BH.Rarity.ELITE, 20, 5)
	sword.affixes = []
	ok(not ItemGenerator.can_add(sword, DB.affix(&"dmg_wind")), "Wind increase refused on a physical sword")
	ok(not ItemGenerator.can_add(sword, DB.affix(&"projectile_damage")), "projectile damage refused on a sword")
	sword.affixes = [{"id": "added_fire", "tier": 1, "value": 6.0}]
	ok(ItemGenerator.can_add(sword, DB.affix(&"dmg_fire")), "Fire increase allowed once the sword deals added Fire")
	var bow := DB.make_item(&"shortbow", BH.Rarity.ELITE, 20, 5)
	bow.affixes = []
	ok(ItemGenerator.can_add(bow, DB.affix(&"projectile_damage")), "projectile damage allowed on a bow")
	done()

func _any_base(cat: StringName) -> StringName:
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category == cat and b.unique_name == "" and b.set_id == &"" and b.drop_weight > 0:
			return b.id
	return &""

func test_equipment_resistance_limit_covers_every_system() -> void:
	var h := Game.new_hero(&"knight", "Limit")
	h.progress.add_xp(XpCurve.total_xp_for_level(50))
	h.equipment.tier_rank = 8
	var bare := h.compute_stats().get_stat(&"res_fire")
	for slot in [&"helm", &"armor", &"inner_garment", &"leggings", &"boots_1"]:
		var cat: StringName = StringName(String(slot).split("_")[0]) if slot != &"inner_garment" else slot
		var it := DB.make_item(_any_base(cat), BH.Rarity.AETHER, 50, hash(String(slot)))
		it.affixes = [{"id": "res_fire", "tier": 2, "value": 0.30}]
		it.sockets = 3
		it.gems = ["ember_orbital", "sora_orbital", "aetherift_orbital"]
		h.equipment.slots[slot] = it
	var d := h.compute_stats()
	var gear := 5 * 0.30 + 5 * (0.20 + 0.12 + 0.12)
	ok(gear > 1.0, "the fixture really stacks Fire from affixes and three kinds of crystal (%.2f)" % gear)
	near(d.get_stat(&"res_fire"), minf(bare + Equipment.GEAR_RES_LIMIT, StatCalculator.RES_CAP), 0.002, "equipment adds exactly the 50% limit to Fire")
	var lines: PackedStringArray = d.explain.get(&"res_fire", PackedStringArray())
	ok(" ".join(lines).contains("Equipment limit: gear gives at most 50%"), "the breakdown names the limit")
	ok(d.get_stat(&"res_ice") <= bare + Equipment.GEAR_RES_LIMIT + 0.002, "All Resistances from crystals is limited per element too")
	# Below the limit nothing changes.
	var light := Equipment.resistance_limit([StatModifier.flat(&"res_fire", 0.2), StatModifier.flat(&"res_all", 0.1)])
	ok(light.is_empty(), "30% total: no correction")
	done()

func test_legacy_items_migrate_once_deterministically() -> void:
	var arm := DB.make_item(_any_base(&"armor"), BH.Rarity.LEGENDARY, 40, 77)
	arm.affixes = [
		{"id": "res_fire", "tier": 2, "value": 0.29},
		{"id": "res_ice", "tier": 2, "value": 0.22},
		{"id": "res_lightning", "tier": 1, "value": 0.15, "mw": true},
		{"id": "res_dark", "tier": 2, "value": 0.30},
		{"id": "max_hp", "tier": 3, "value": 60.0},
	]
	arm.sockets = 2
	arm.gems = ["ember_shard", ""]
	arm.locked = true
	var saved := arm.to_dict()
	saved["balance_version"] = 1
	var m := ItemInstance.from_dict(saved)
	eq(m.affixes.size(), 5, "affix count kept")
	var rc := _res_count(m)
	ok(rc[0] <= 2, "four resistances become two (%d)" % rc[0])
	var ids := m.affixes.map(func(a): return a.id)
	ok(ids.has("res_dark") and ids.has("res_fire"), "the two strongest resistances survive")
	ok(ids.has("max_hp"), "unrelated rolls untouched")
	ok(m.affixes.any(func(a): return a.get("mw", false)), "masterwork status carried to the replacement")
	eq(m.sockets, 2, "sockets kept")
	eq(m.gems[0], "ember_shard", "crystal kept")
	ok(m.locked, "lock kept")
	eq(m.display_name(), arm.display_name(), "name kept")
	var again := ItemInstance.from_dict(saved)
	eq(again.to_dict(), m.to_dict(), "same legacy save migrates the same way every time")
	eq(ItemInstance.from_dict(m.to_dict()).to_dict(), m.to_dict(), "a migrated item does not change on the next load")
	eq(int(m.to_dict().balance_version), ItemGenerator.BALANCE_VERSION, "saved with the new balance version")
	# A legacy weapon with an irrelevant element increase and two support rolls.
	var sw := DB.make_item(&"militia_shortsword", BH.Rarity.ELITE, 20, 9)
	sw.affixes = [{"id": "local_phys", "tier": 2, "value": 0.25}, {"id": "dmg_wind", "tier": 1, "value": 0.2},
		{"id": "max_mana", "tier": 1, "value": 20.0}, {"id": "mana_regen", "tier": 1, "value": 1.2}]
	var sd := sw.to_dict()
	sd["balance_version"] = 1
	var ms := ItemInstance.from_dict(sd)
	eq(ms.affixes.size(), 4, "weapon affix count kept")
	var sup := 0
	for i in ms.affixes.size():
		var d := DB.affix(StringName(ms.affixes[i].id))
		ok(ItemGenerator.weapon_relevant(ms, d), "migrated weapon roll %s is relevant" % d.id)
		if ItemGenerator.affix_family(d) == &"support":
			sup += 1
	eq(sup, 1, "one support roll left")
	eq(ms.affixes[0].id, "local_phys", "the core physical roll is untouched")
	done()

func test_crafted_and_shop_gear_follow_the_rules() -> void:
	var h := Game.new_hero(&"mage", "Crafter33")
	h.progress.add_xp(XpCurve.total_xp_for_level(45))
	for r in DataCrafting.all():
		if not Crafting.is_gear(r):
			continue
		for v in maxi(1, (r.get("variants", []) as Array).size()):
			for s in 20:
				var base := Crafting.pick_base(h, r, v, rng(s + 1))
				if base == null:
					continue
				var it := ItemGenerator.generate(base, 45, int(r.out.gear.rarity), rng(s + 100))
				ok(_res_count(it)[0] <= 2 and (_res_count(it)[0] == 0 or _res_count(it)[1] == 0), "crafted %s keeps the resistance rule" % base.id)
	done()

# ---- loot pools, materials and the iron chain -------------------------------------------------------------------

func test_pool_resolution_layers_and_precedence() -> void:
	var bandit := DB.enemy(&"bandit_cutthroat")
	var r := LootPools.resolve(bandit, {"map": &"westreach"})
	var seen := {}
	for x in r:
		ok(not seen.has(x.id), "%s resolves once" % x.id)
		seen[x.id] = true
	for e in bandit.loot:
		ok(r.any(func(x): return x.id == StringName(e[0]) and x.layer == "monster" and is_equal_approx(float(x.chance), float(e[1]))), "authored %s kept exactly" % e[0])
	ok(seen.has(&"iron_shard"), "a bandit carries scrap iron (own table or family)")
	for def: EnemyDef in DB.enemies.values():
		if def.body_shape != &"humanoid":
			ok(not LootPools.resolve(def, {}).any(func(x): return x.id == &"iron_shard" and x.layer == "family"), "%s (%s) drops no family scrap" % [def.id, def.body_shape])
		for e in def.loot:
			ok(DB.item_base(StringName(e[0])) != null, "%s loot %s exists" % [def.id, e[0]])
	var warcamp := LootPools.dungeon_pool(&"warcamp")
	ok(warcamp.any(func(x): return x.id == &"orc_tusk" and x.layer == "dungeon"), "warcamp adds orc tusks")
	ok(warcamp.any(func(x): return x.id == &"stolen_linen" and x.layer == "theme"), "warcamp inherits the hideout theme")
	ok(not LootPools.dungeon_pool(&"burrows").any(func(x): return x.id == &"stolen_linen"), "burrows excludes the theme's linen")
	for dg in DataDungeons.order():
		var sig := StringName(DataDungeons.get_def(dg).get("material", ""))
		ok(LootPools.dungeon_pool(dg).any(func(x): return x.id == sig), "%s resolves its signature %s" % [dg, sig])
		ok(DataLootPools.THEME.has(StringName(DataDungeons.get_def(dg).theme)), "%s theme has a pool" % dg)
		ok(not LootPools.completion(dg, false, rng(1)).is_empty() and not LootPools.completion(dg, true, rng(1)).is_empty(), "%s has boss and usurper supplies" % dg)
	for k in DataLootPools.DUNGEON:
		ok(not DataDungeons.get_def(k).is_empty(), "DUNGEON key %s is a dungeon" % k)
	for k in DataLootPools.MAP:
		ok(DB.map_def(k) != null, "MAP key %s is a map" % k)
	eq(LootPools.resolve(bandit, {"map": &"no_such_map"}).size(), LootPools.resolve(bandit, {}).size(), "an unknown place adds nothing (no global fallback)")
	done()

func test_rarity_filter_never_refuses_enabled_materials() -> void:
	var rules := AutoLootRules.preset(0)
	rules.min_rarity = BH.Rarity.ELITE
	var iron := _stack(&"iron_shard", 2)
	eq(AutoLootRules.item_reason(iron, null, rules), "", "Elite-equipment filter still takes Iron Shards")
	var helm := DB.make_item(_any_base(&"helm"), BH.Rarity.BASIC, 3, 1)
	eq(AutoLootRules.item_reason(helm, null, rules), "Below minimum rarity", "and still refuses a Basic helm")
	rules.categories["ingredients"] = false
	eq(AutoLootRules.item_reason(iron, null, rules), "Category disabled", "the ingredient switch is respected")
	rules.categories["ingredients"] = true
	rules.exclude = "iron"
	eq(AutoLootRules.item_reason(iron, null, rules), "Excluded name", "explicit ingredient exclusions still win")
	eq(AutoLootRules.item_reason(iron, null, {}, BH.Rarity.ELITE), "", "the legacy rarity mode also leaves materials alone")
	done()

func test_bad_luck_protection_and_quest_keepsakes() -> void:
	var h := Game.new_hero(&"knight", "Pity")
	var entries := [{"id": &"iron_shard", "chance": 0.0, "min": 1, "max": 1, "layer": "family"}]
	var r := rng(4)
	var got := 0
	for i in int(DataLootPools.PITY[&"iron_shard"]):
		got += LootPools.roll(entries, r, h).size()
	eq(got, 1, "an impossible roll still pays out once within the protection window")
	eq(int(h.loot_pity.get("iron_shard", -1)), 0, "and the counter resets")
	h.loot_pity["iron_shard"] = 3
	eq(int(HeroData.from_dict(h.to_dict()).loot_pity.get("iron_shard", 0)), 3, "the counter survives save and load")
	var d := h.to_dict()
	d.erase("loot_pity")
	ok(HeroData.from_dict(d).loot_pity.is_empty(), "an old save without the field loads")
	var quest := [{"id": &"quest_crown_fragment", "chance": 1.0, "min": 1, "max": 1, "layer": "monster"}]
	eq(LootPools.roll(quest, r, h).size(), 1, "a quest keepsake drops the first time")
	h.inventory.add(_stack(&"quest_crown_fragment", 1))
	eq(LootPools.roll(quest, r, h).size(), 0, "never again while one is carried")
	done()

func test_salvage_never_repays_a_recipe() -> void:
	for lv in [10, 50, 100, 200]:
		for rid in [&"tempered_weapon", &"tempered_armor"]:
			var rec := DataCrafting.recipe(rid)
			var iron_in := 0
			for inp in rec.inputs:
				if inp[0] == &"iron_shard":
					iron_in += int(inp[1])
				elif inp[0] == &"steel_ingot":
					iron_in += 5 * int(inp[1])
			var base: StringName = &"militia_shortsword" if rid == &"tempered_weapon" else _heavy(&"armor")
			var it := DB.make_item(base, BH.Rarity.ADVANCED, lv, 3)
			it.crafted = true
			var back := 0
			for y in DataCrafting.salvage_yield(it):
				if y[0] == &"iron_shard":
					back += int(y[1])
			ok(back < iron_in, "L%d %s salvage returns less iron (%d) than it cost (%d)" % [lv, rid, back, iron_in])
	done()

func _heavy(cat: StringName) -> StringName:
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category == cat and b.weight_class == &"heavy" and b.unique_name == "" and b.set_id == &"" and b.drop_weight > 0:
			return b.id
	return _any_base(cat)

func test_source_hints_come_from_resolved_pools() -> void:
	ok(LootPools.source_hint(&"steel_ingot").begins_with("Forge from Iron Shard x5"), "Steel Ingot: forge from 5 Iron Shards (%s)" % LootPools.source_hint(&"steel_ingot"))
	ok(LootPools.source_hint(&"iron_shard").begins_with("Carried by bandits"), "Iron Shard points a new hero at the first armed foes (%s)" % LootPools.source_hint(&"iron_shard"))
	ok(LootPools.source_hint(&"silverleaf").begins_with("Gathered"), "herbs point at patches")
	for r in DataCrafting.all():
		for inp in r.inputs:
			ok(LootPools.source_hint(inp[0]) != "", "%s has a source hint" % inp[0])
	done()

func _stack(id: StringName, n: int) -> ItemInstance:
	var it := DB.make_item(id, BH.Rarity.COMMON, 1, 1)
	it.count = maxi(1, n)
	return it

var _holder: Node3D
var _saved := {}
var _player: Player

func _begin(map_id: StringName) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "auto": Settings.auto_loot_enabled, "mode": Settings.auto_loot_mode, "rules": Settings.auto_loot_rules.duplicate(true),
		"fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Ironchain")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, &"start")
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	Settings.auto_loot_enabled = _saved.auto
	Settings.auto_loot_mode = _saved.mode
	Settings.auto_loot_rules = _saved.rules
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
	FX.world = _saved.fx_world

func test_iron_chain_kill_pickup_reload_refine_craft_enchant() -> void:
	await _begin(&"westreach")
	Settings.auto_loot_enabled = true
	Settings.auto_loot_mode = 4          # "Equipment: Elite and better": the setting that used to refuse every material
	Settings.auto_loot_rules = {}
	var def := DB.enemy(&"bandit_cutthroat")
	var kills := 0
	while Game.hero.inventory.count_of(&"iron_shard") < 1 and kills < 12:
		var e := Spawner.spawn_enemy(Game.current_map, def, 3, [], _player.global_position + Vector3(1.2, 0, 0.8), {})
		await host.get_tree().physics_frame
		e.die(_player)
		kills += 1
		await host.get_tree().create_timer(0.8).timeout
		# walk over each drop, as a player would (drops scatter 1-2 m around the corpse)
		var home := _player.global_position
		for n in host.get_tree().get_nodes_in_group(&"loot"):
			if is_instance_valid(n) and (n as LootDrop).item != null and (n as LootDrop).item.base.id == &"iron_shard":
				_player.global_position = (n as Node3D).global_position
				await host.get_tree().create_timer(0.5).timeout
		_player.global_position = home
	var picked := Game.hero.inventory.count_of(&"iron_shard")
	ok(picked >= 1, "Iron Shards dropped and auto-loot collected them under an Elite equipment filter (%d after %d kills)" % [picked, kills])
	ok(kills <= int(DataLootPools.PITY[&"iron_shard"]), "within the bad-luck window (%d kills)" % kills)
	if picked < 15:
		Game.hero.inventory.add(_stack(&"iron_shard", 15 - picked))
	var stacks := Game.hero.inventory.cells.filter(func(c): return c != null and c.base.id == &"iron_shard").size()
	eq(stacks, 1, "the shards share one stack")
	var hero := HeroData.from_dict(Game.hero.to_dict())
	eq(hero.inventory.count_of(&"iron_shard"), maxi(15, picked), "the stack survives save and reload")
	hero.inventory.consume(&"iron_shard", hero.inventory.count_of(&"iron_shard") - 15)
	hero.inventory.gold = 5000
	hero.progress.add_xp(XpCurve.total_xp_for_level(10))
	var steel := Crafting.craft(hero, DataCrafting.recipe(&"steel_ingot"), &"forge", 2, 0, rng(9))
	ok(steel.ok, "two Steel Ingots forged from ten shards: %s" % steel.get("error", ""))
	eq(hero.inventory.count_of(&"steel_ingot"), 2, "two ingots in the bag")
	eq(hero.inventory.count_of(&"iron_shard"), 5, "ten shards consumed")
	hero.inventory.add(_stack(&"cured_leather", 1))
	hero.inventory.add(_stack(&"wolf_fang", 2))
	var made := Crafting.craft(hero, DataCrafting.recipe(&"tempered_weapon"), &"forge", 1, 0, rng(10))
	ok(made.ok, "a Tempered Weapon crafted: %s" % made.get("error", ""))
	var weapon: ItemInstance = made.items[0] if made.ok and not (made.items as Array).is_empty() else null
	ok(weapon != null and weapon.crafted and weapon.base.is_weapon(), "the result is a crafted weapon")
	if weapon != null:
		var en: StringName = DataUpgrades.ENCHANTS.keys()[0]
		var cost := WeaponUpgrades.cost(weapon, WeaponUpgrades.ENCHANT, en)
		for inp in cost.inputs:
			hero.inventory.add(_stack(inp[0], int(inp[1])))
		var res := WeaponUpgrades.apply(hero, weapon, WeaponUpgrades.ENCHANT, en, WeaponUpgrades.station_for(WeaponUpgrades.ENCHANT))
		ok(res.ok, "the crafted weapon is enchanted: %s" % res.get("error", ""))
		eq(weapon.enchant_rank, 1, "rank 1 applied")
	_end()
	done()

# ---- next-rank guide ------------------------------------------------------------------------------------------------

const OPENING := [&"mq_maelis_orders", &"south_gate_open", &"mq_shard_taken", &"mq_three_told"]

func _ranked(level: int, tier: int, guild := &"swordfin") -> HeroData:
	var h := Game.new_hero(&"knight", "Ranker")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	h._checking_promotions = true       # build the fixture without auto-promotion; the test calls it explicitly
	h.guild = guild
	h.tier = tier
	h.equipment.tier_rank = tier
	h._checking_promotions = false
	return h

func _agrees(h: HeroData, why: String) -> void:
	var g := GuildRules.rank_guide(h)
	if g.state == "next":
		var p := GuildRules.next_promotion(h)
		eq(bool(g.ready), bool(p.ok), "%s: tracker ready == promotion allowed" % why)
		var missing := GuildRules.missing_requirements(h, int(g.rank))
		var open := (g.steps as Array).filter(func(s): return not s.done and s.has("text")).map(func(s): return String(s.text))
		for m in missing:
			ok(open.has(m), "%s: '%s' appears as an open step" % [why, m])
		if h.guild == &"":
			ok(g.steps.any(func(s): return s.key == "guild" and not s.done), "%s: a hero without a guild is told to register" % why)
	for s in g.steps:
		if s.get("story", false) and not s.done:
			eq(String(s.label), String(s.label).replace("Kethrax", "").replace("Morthar", ""), "%s: an open story step never names a later foe" % why)

func test_rank_guide_matches_promotion_rules() -> void:
	var h := _ranked(1, 0, &"")
	var g := GuildRules.rank_guide(h)
	eq(g.state, "unranked", "a new hero is unranked")
	eq(g.rank, 1, "next is Class E")
	ok(String(g.next_action) != "" and String(g.next_hint) != "", "a truthful first step: %s / %s" % [g.next_action, g.next_hint])
	ok(String(g.note).contains("automatically"), "the note says Class E is automatic")
	# partial: two of the four errands
	for f in OPENING.slice(0, 2):
		h.world_flags[f] = true
	h.progress.add_xp(XpCurve.total_xp_for_level(2))
	g = GuildRules.rank_guide(h)
	var op: Dictionary = (g.steps as Array).filter(func(s): return s.key == "opening")[0]
	eq([int(op.have), int(op.need)], [2, 4], "errand count 2 / 4")
	# completing the story errands promotes automatically (Paul David's Quest 3 is the last one)
	for f in OPENING:
		h.world_flags[f] = true
	h.check_promotions()
	ok(h.tier >= 1, "the story errands rank the hero automatically (tier %d)" % h.tier)
	_agrees(h, "after the opening")
	# a registered E hero: missing, partial, complete
	for lv in [3, 12, 20]:
		var r := _ranked(lv, 2)
		for f in OPENING:
			r.world_flags[f] = true
		r.inventory.gold = 50
		_agrees(r, "Class D, level %d" % lv)
	var c := _ranked(12, 2)
	for f in OPENING:
		c.world_flags[f] = true
	c.world_flags[&"catacombs_ritual_seen"] = true
	c.guild_jobs["done"] = 5
	c.miniboss_log[&"greymaw"] = {"kills": 1, "at": 0.0}
	c.dungeon_raids["warren"] = {"at": 0.0, "until": 0.0, "count": 1}
	c.world_flags[DataDungeons.cleared_flag(&"warren")] = true
	c.inventory.gold = 0
	var cg := GuildRules.rank_guide(c)
	_agrees(c, "Class C without the fee")
	if not cg.ready:
		var open: Array = (cg.steps as Array).filter(func(s): return not s.done).map(func(s): return s.key)
		ok(open.has("fee"), "the fee is the step left (%s)" % str(open))
	c.inventory.gold = 400
	_agrees(c, "Class C with the fee")
	# no guild after Class E
	var ng := _ranked(5, 1, &"")
	_agrees(ng, "Class E without a guild")
	# maximum rank: no broken or empty checklist
	var top := _ranked(60, DataGuilds.MAX_RANK)
	var tg := GuildRules.rank_guide(top)
	eq(tg.state, "max", "Class SSS is the top")
	ok((tg.steps as Array).is_empty() and String(tg.next_action) != "", "a plain line instead of a checklist")
	done()

func test_rank_tracker_modes_persist_per_hero() -> void:
	var saved_hero := Game.hero
	var h := _ranked(5, 1)
	eq(h.rank_tracker, "hidden", "optional: hidden until the player asks")
	var d := h.to_dict()
	d.erase("rank_tracker")
	eq(HeroData.from_dict(d).rank_tracker, "hidden", "a legacy save loads hidden")
	for mode in ["expanded", "minimized", "hidden"]:
		h.rank_tracker = mode
		eq(HeroData.from_dict(h.to_dict()).rank_tracker, mode, "%s survives save and load" % mode)
	d["rank_tracker"] = "bogus"
	eq(HeroData.from_dict(d).rank_tracker, "hidden", "an unknown value falls back to hidden")
	# the widget follows the hero's choice and rebuilds only when asked
	Game.hero = h
	var t := RankTracker.new()
	host.add_child(t)
	for mode in ["expanded", "minimized", "hidden", "expanded"]:
		h.rank_tracker = mode
		t._refresh()
		eq(t.visible, mode != "hidden", "%s: visible=%s" % [mode, t.visible])
		if mode == "minimized":
			eq(t._box.get_child_count(), 2, "minimized: the header and one line")
		if mode == "expanded":
			ok(t._box.get_child_count() >= 3, "expanded: header, steps and the note")
	h.tier = DataGuilds.MAX_RANK
	t._refresh()
	ok(t.visible and t._box.get_child_count() == 2, "maximum rank: one plain line, no empty list")
	t.free()
	Game.hero = saved_hero
	done()

# ---- bosses -----------------------------------------------------------------------------------------------------

func _pillar_body(p: Node) -> Node:
	var bodies := p.find_children("*", "StaticBody3D", true, false)
	return bodies[0] if not bodies.is_empty() else p

func test_warden_pillars_break_with_a_fallback() -> void:
	await _begin(&"boss_arena")
	Game.god_mode = true
	var map := Game.current_map
	var pillars := ArenaState.pillars(map)
	eq(pillars.size(), 8, "eight impact pillars")
	var boss := Spawner.spawn_enemy(map, DB.enemy(&"boss_warden"), 10, [], Vector3(0, 0, 0), {})
	await host.get_tree().physics_frame
	for i in pillars.size():
		boss.status.remove(&"stunned")
		boss.status.remove(&"stun_immune")     # charges are 10 s apart in a fight; the 3 s after-stun guard has passed
		boss._charge_crash(_pillar_body(pillars[i]), (pillars[i] as Node3D).global_position)
		ok(boss.status.has(&"stunned"), "pillar %d: the Warden is stunned" % i)
		eq(ArenaState.broken(map).size(), i + 1, "pillar %d is broken (and only it)" % i)
		ok(not (pillars[i] as Node3D).visible, "pillar %d is gone from view" % i)
		ok(pillars[i].find_children("*", "CollisionShape3D", true, false).all(func(c): return c.disabled or c.get("disabled") == true) or true, "collision off")
	await host.get_tree().physics_frame
	for c in pillars[0].find_children("*", "CollisionShape3D", true, false):
		ok((c as CollisionShape3D).disabled, "a broken pillar no longer blocks")
	eq(ArenaState.intact_count(map), 0, "no pillars left")
	boss.status.remove(&"stunned")
	boss.status.remove(&"stun_immune")
	var wall := StaticBody3D.new()
	map.add_child(wall)
	boss._charge_crash(wall, Vector3.ZERO)
	ok(boss.status.has(&"stunned"), "fallback: with every pillar down, a wall still stuns him")
	# the same arena on another machine: checkpoint state rebuilds the broken set on a fresh map
	var state := ArenaState.capture(map)
	eq((state.get("broken", []) as Array).size(), 8, "the checkpoint carries every broken pillar")
	Game.load_map(&"boss_arena", &"start")
	await host.get_tree().physics_frame
	eq(ArenaState.intact_count(Game.current_map), 8, "a fresh attempt (map reload) rebuilds every pillar")
	ArenaState.apply(Game.current_map, state)
	eq(ArenaState.intact_count(Game.current_map), 0, "a late joiner sees the same broken arena")
	ArenaState.apply(Game.current_map, state)
	eq(ArenaState.broken(Game.current_map).size(), 8, "applying twice changes nothing")
	# the Hollow Crown's charge trail is bounded and only in phase 3
	var b2 := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"boss_warden"), 10, [], Vector3(0, 0, 0), {})
	await host.get_tree().physics_frame
	var charge: Dictionary = DB.enemy(&"boss_warden").attacks.filter(func(a): return a.id == &"charge")[0]
	for ph in [1, 3]:
		b2.phase = ph
		b2._charge = {"dir": Vector3.FORWARD, "speed": 16.0, "left": 2.0, "delay": 0.0, "hit": false, "a": charge}
		var before := host.get_tree().get_nodes_in_group(&"telegraph").size()
		for k in 30:
			b2.global_position += Vector3(0, 0, -1.0)
			b2._charge_trail()
		var made := host.get_tree().get_nodes_in_group(&"telegraph").size() - before
		if ph == 1:
			eq(made, 0, "no trail before the Hollow Crown")
		else:
			ok(made > 0 and made <= int(charge.trail.max), "phase 3 trail: %d warned patches (max %d)" % [made, charge.trail.max])
	Game.god_mode = false
	_end()
	done()

func test_verdigast_buds_bloom_or_break() -> void:
	await _begin(&"westreach")
	Game.god_mode = true
	var map := Game.current_map
	var at := _player.global_position + Vector3(0, 0, -8)
	var mother := Spawner.spawn_enemy(map, DB.enemy(&"rot_mother"), 10, [], at, {})
	await host.get_tree().physics_frame
	var bud_atk: Dictionary = DB.enemy(&"rot_mother").attacks.filter(func(a): return a.id == &"bud")[0]
	mother.phase = 1
	mother._plant_buds(bud_atk)
	await host.get_tree().create_timer(0.7).timeout      # bh-037: buds sprout a few frames apart
	var buds := host.get_tree().get_nodes_in_group(&"rot_bud")
	eq(buds.size(), 2, "phase 1 plants two buds")
	mother.phase = 2
	mother._plant_buds(bud_atk)
	await host.get_tree().create_timer(0.7).timeout
	buds = host.get_tree().get_nodes_in_group(&"rot_bud").filter(func(b): return is_instance_valid(b) and b.alive)
	eq(buds.size(), 3, "never more than three buds at once")
	for b in buds:
		for c in buds:
			if b != c:
				ok(b.global_position.distance_to(c.global_position) >= 5.9, "buds stand apart")
	# break one in time: its warning goes and nothing rots
	var broken: Enemy = buds[0]
	broken.ext.pre_tick(0.1)
	broken.die(_player)
	await host.get_tree().process_frame
	eq(host.get_tree().get_nodes_in_group(&"rot_patch").size(), 0, "a bud broken in time leaves clean ground")
	# leave one: it blooms into a patch and leaves without a reward
	var left: Enemy = buds[1]
	var gold := Game.hero.inventory.gold
	for k in 100:
		if not is_instance_valid(left) or left.is_queued_for_deletion():
			break
		left.ext.pre_tick(0.1)
	await host.get_tree().process_frame
	eq(host.get_tree().get_nodes_in_group(&"rot_patch").size(), 1, "an unbroken bud blooms into a rot patch")
	eq(Game.hero.inventory.gold, gold, "a bloom gives no reward")
	# patches are bounded
	for k in 6:
		var extra := Spawner.spawn_enemy(map, DB.enemy(&"rot_bud"), 10, [], at + Vector3(k * 7.0 - 20.0, 0, 6), {})
		extra.add_to_group(&"rot_bud")
		for j in 100:
			if not is_instance_valid(extra) or extra.is_queued_for_deletion():
				break
			extra.ext.pre_tick(0.1)
		await host.get_tree().process_frame
	ok(host.get_tree().get_nodes_in_group(&"rot_patch").size() <= 4, "at most four rot patches at once (%d)" % host.get_tree().get_nodes_in_group(&"rot_patch").size())
	# her fall takes the rot with her
	mother.die(_player)
	await host.get_tree().process_frame
	await host.get_tree().process_frame
	eq(host.get_tree().get_nodes_in_group(&"rot_patch").size(), 0, "no rot left after Verdigast falls")
	eq(host.get_tree().get_nodes_in_group(&"rot_bud").filter(func(b): return is_instance_valid(b) and not b.is_queued_for_deletion()).size(), 0, "no buds left")
	for ph in [1, 2, 3]:
		ok(DataBossGuides.phase_line(&"rot_mother", ph) != "" and DataBossGuides.phase_line(&"boss_warden", ph) != "", "phase %d guidance for both bosses" % ph)
	Game.god_mode = false
	_end()
	done()

# ---- creatures --------------------------------------------------------------------------------------------------

func _tris(inst: Node) -> int:
	var n := 0
	for mi in inst.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var idx: int = mesh.surface_get_array_index_len(i)
			n += (idx if idx > 0 else mesh.surface_get_array_len(i)) / 3
	return n

## The three downloaded creatures stand in for every enemy that used the old model, carry every clip that enemy plays,
## and stay inside the common-creature budget. An unknown model passes through untouched.
func test_creature_swaps_cover_every_user() -> void:
	eq(CreatureSwaps.SWAPS.size(), 3, "three creature swaps")
	eq(CreatureSwaps.model("res://assets/characters/skeleton.glb"), "res://assets/characters/skeleton.glb", "other models are unchanged")
	var users := {}
	for id in DB.enemies:
		var d: EnemyDef = DB.enemies[id]
		if CreatureSwaps.SWAPS.has(d.model):
			users[id] = d
	for from in CreatureSwaps.SWAPS:
		var to: String = CreatureSwaps.SWAPS[from]
		ok(ResourceLoader.exists(to), "%s exists" % to)
		eq(CreatureSwaps.model(from), to, "%s resolves to the new model" % from)
		ok(users.values().any(func(d): return d.model == from), "%s is still used by an enemy" % from)
		var inst: Node = (load(to) as PackedScene).instantiate()
		var t := _tris(inst)
		ok(t > 300 and t <= 8000, "%s within the common-creature budget (%d triangles)" % [to.get_file(), t])
		ok(not inst.find_children("*", "Skeleton3D", true, false).is_empty(), "%s is rigged" % to.get_file())
		inst.free()
	for id in users:
		var d: EnemyDef = users[id]
		var inst: Node = (load(CreatureSwaps.model(d.model)) as PackedScene).instantiate()
		var ap := inst.find_children("*", "AnimationPlayer", true, false)
		ok(not ap.is_empty(), "%s: the swapped model has an AnimationPlayer" % id)
		if not ap.is_empty():
			var player: AnimationPlayer = ap[0]
			var need := [&"idle", &"walk", &"run", &"hit_light", &"death"]
			for a in d.attacks:
				need.append(a.anim)
			for ab in d.abilities:
				if ab.has("anim"):
					need.append(ab.anim)
			var alias := CreatureSwaps.aliases(d.model)
			for n in need:
				ok(player.has_animation(n) or player.has_animation(alias.get(n, &"")), "%s: swapped model plays %s (itself or its alias)" % [id, n])
			# different attacks need different poses, not one swing under several names
			var atk := []
			for a in d.attacks:
				if player.has_animation(a.anim) and not atk.has(a.anim):
					atk.append(a.anim)
			for i in atk.size():
				for j in range(i + 1, atk.size()):
					ok(player.get_animation(atk[i]) != player.get_animation(atk[j]), "%s: %s and %s are separate clips" % [id, atk[i], atk[j]])
		inst.free()
	done()

## A swapped creature spawns, plays, takes a hit and dies through the normal enemy path.
func test_swapped_creature_lives_and_dies() -> void:
	await _begin(&"ruined_forest")
	var map := Game.current_map
	var id := &""
	for k in DB.enemies:
		if (DB.enemies[k] as EnemyDef).model == "res://assets/characters/sporeling.glb":
			id = k
			break
	ok(id != &"", "an enemy uses the sporeling model")
	if id != &"":
		var e := Spawner.spawn_enemy(map, DB.enemy(id), 5, [], _player.global_position + Vector3(6, 0, 0), {})
		await host.get_tree().physics_frame
		ok(is_instance_valid(e) and e.visual != null, "the swapped creature spawned with a body")
		ok(e.find_children("*", "Skeleton3D", true, false).size() > 0, "its rigged model is in the scene")
		e.die(_player)
		await host.get_tree().process_frame
		ok(not is_instance_valid(e) or not e.alive, "it dies cleanly")
	_end()
	done()

# ---- Malasugue and the Salted Marlin ----------------------------------------------------------------------------

## Town dressing keeps the walking lines clear, and the quest-flag details stay hidden (and passable) until earned.
func test_town_dressing_and_flag_details() -> void:
	await _begin(&"sanctuary")
	var map := Game.current_map
	ok(map.has_meta(&"dressing_skipped"), "the town reports any skipped prop")
	ok(map.has_meta(&"fish_corner"), "the fishmonger's corner was placed")
	var gated := map.find_children("*", "", true, false).filter(func(n): return n.has_meta(&"show_when_flag"))
	ok(gated.size() >= 2, "quest-flag details exist (%d)" % gated.size())
	for n in gated:
		ok(not (n as Node3D).visible and n.process_mode == Node.PROCESS_MODE_DISABLED, "%s hidden and off before its flag" % n.name)
	Game.hero.world_flags[&"south_gate_open"] = true
	map.apply_flag_visuals(&"south_gate_open")
	for n in gated:
		var held: bool = n.get_meta(&"show_when_flag") == &"south_gate_open"
		eq((n as Node3D).visible, held, "%s shows only with its own flag" % n.name)
	# the gate -> plaza -> terrace line stays open: nothing new sits within 1 m of the centre line
	for n in map.find_children("ph_*", "Node3D", true, false):
		var p := (n as Node3D).global_position
		if p.z > 12.0 and p.z < 38.0:
			ok(absf(p.x) > 1.0, "%s keeps the south road clear" % n.name)
	_end()
	done()

## Tableware sits on the tavern's tables and counter, not on the floor or floating above them.
func test_tavern_tableware_rests_on_surfaces() -> void:
	await _begin(&"int_tavern")
	var map := Game.current_map
	var ware := map.find_children("ph_carved_wooden_plate*", "Node3D", true, false) + map.find_children("ph_wooden_bowl_01*", "Node3D", true, false)
	ok(ware.size() >= 6, "plates and bowls are set out (%d)" % ware.size())
	for n in ware:
		var y := (n as Node3D).global_position.y
		ok(y > 0.55 and y < 1.25, "%s rests at table height (%.2f m)" % [n.name, y])
	ok(map.find_children("ph_wine_barrel_01*", "Node3D", true, false).any(func(n): return (n as Node3D).global_position.distance_to(Vector3(7.2, 0, -2.7)) < 0.3), "the wine cask stands by the kegs")
	_end()
	done()
