extends TestCase
## Actual equipment, attributes and damage pipeline at progression milestones.

func _init() -> void:
	strict = true

func _hero(cid: StringName, level: int) -> HeroData:
	var h := Game.new_hero(cid, "Progression test")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	var primary := &"int" if cid == &"mage" else &"str"
	h.progress.allocate(primary, (level - 1) * 2)
	h.progress.allocate(&"wis" if cid == &"mage" else &"dex", level - 1)
	return h

func _weapon(h: HeroData, rarity := BH.Rarity.ELITE) -> ItemInstance:
	var type: StringName = {&"knight": &"sword", &"mage": &"staff", &"ranger": &"bow", &"shadowblade": &"dagger"}[h.cls.id]
	var best: ItemBaseDef
	for b: ItemBaseDef in DB.item_bases.values():
		if b.weapon_type != type or b.level_req > h.progress.level or b.drop_weight <= 0 or b.unique_name != "" or b.set_id != &"":
			continue
		if best == null or b.level_req > best.level_req:
			best = b
	var it := DB.make_item(best.id, rarity, h.progress.level, 2201)
	h.inventory.add(it)
	eq(h.equip_from_inventory(it, &"main_weapon"), "", "level-appropriate weapon equips")
	return it

func _hit(h: HeroData, target: DerivedStats, spell := false, multiplier := 1.0) -> float:
	var req := DamageRequest.new()
	req.attacker = h.compute_stats()
	req.target = target
	req.evadable = false
	req.can_crit = false
	req.weapon_mult = multiplier
	if spell:
		var p := DB.skill(&"firebolt").resolve(mini(25, h.progress.level))
		req.kind = DamageRequest.Kind.SPELL
		req.use_weapon = false
		req.base_min = p.damage_min
		req.base_max = p.damage_max
		req.conversion = {Elements.FIRE: 1.0}
	var random := rng(814)
	var total := 0.0
	for i in 300:
		total += DamagePipeline.compute(req, random).total
	return total / 300.0

func test_progression_damage_and_enemy_survival() -> void:
	var report := []
	for cid in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var previous := 0.0
		for level in [5, 10, 15, 20, 25, 30, 45, 60]:
			var h := _hero(cid, level)
			var weapon := _weapon(h)
			var enemy := EnemyStats.build(DB.enemy(&"hollow_soldier"), level, {}, [])
			var normal := _hit(h, enemy)
			var special := _hit(h, enemy, cid == &"mage", 1.0 if cid == &"mage" else 1.9)
			ok(normal > previous, "%s damage grows at level %d" % [cid, level])
			previous = normal
			if level in [25, 30]:
				ok(special >= 300, "%s level %d strong hit reaches 300+ (%d)" % [cid, level, special])
				ok(enemy.get_stat(&"max_hp") > normal * 2.0, "same-level regular survives multiple normal hits")
			var range := weapon.damage_range()
			report.append({"class": String(cid), "level": level, "weapon": String(weapon.base.id), "weapon_min": roundi(range.x), "weapon_max": roundi(range.y), "hit": roundi(normal), "skill_hit": roundi(special), "enemy_hp": roundi(enemy.get_stat(&"max_hp")), "hits_to_kill": snappedf(enemy.get_stat(&"max_hp") / normal, 0.1)})
			print("GROWTH ", JSON.stringify(report[-1]))
	var file := FileAccess.open("res://../output/combat-growth.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "  "))
	done()

func test_opening_levels_unchanged() -> void:
	for level in range(1, 6):
		eq(CombatGrowth.weapon_factor(level), 1.0, "opening weapon budget")
		eq(CombatGrowth.health_factor(level), 1.0, "opening enemy HP")
		eq(CombatGrowth.physical_attack(70, level), 0.0, "no opening attack boost")
		eq(CombatGrowth.spell_power(70, 40, 50, level), 0.0, "no opening spell boost")
	done()

func test_item_level_saves_and_requirements() -> void:
	var low := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 5, 12)
	var high := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 30, 12)
	ok(high.damage_range().x > low.damage_range().y * 3.0, "a later drop is substantially stronger")
	var copy := ItemInstance.from_dict(high.to_dict())
	eq(copy.damage_range(), high.damage_range(), "reload does not compound the buff")
	eq(high.required_level(), 27, "late drops cannot be passed to a new hero")
	var pinnacle := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, BH.LEVEL_CAP + 5, 12)
	eq(pinnacle.required_level(), BH.LEVEL_CAP, "pinnacle drops remain wearable at the player cap")
	var hero := _hero(&"knight", 5)
	ok(hero.equipment.check(high, &"main_weapon", 5, hero.progress.base_attributes()).contains("level 27"), "real equip path enforces item level")
	var serialized := hero.to_dict()
	serialized.erase("tier_rules_version")
	serialized["guild"] = "swordfin"
	serialized["tier"] = 7
	var old := HeroData.from_dict(serialized)
	eq(old.tier, 1, "legacy purchased SS is reassessed")
	ok(old.inventory.gold > hero.inventory.gold, "removed promotions refunded")
	var again := HeroData.from_dict(old.to_dict())
	eq(again.inventory.gold, old.inventory.gold, "refund happens once")
	eq(again.equipment.equipped_items().size(), hero.equipment.equipped_items().size(), "gear retained")
	done()

func test_attributes_and_caster_equipment() -> void:
	var mage := _hero(&"mage", 30)
	var target := blank_stats(30)
	var before := _hit(mage, target, true)
	_weapon(mage)
	var equipped := _hit(mage, target, true)
	ok(equipped > before * 1.15, "upgrading a staff improves actual spell damage")
	var bolt := _hit(mage, target)
	mage.progress.allocated[&"int"] += 20
	ok(_hit(mage, target, true) > equipped * 1.15, "INT improves spells")
	ok(_hit(mage, target) > bolt * 1.1, "INT improves elemental staff attacks")
	var knight := _hero(&"knight", 30)
	_weapon(knight)
	before = _hit(knight, target)
	knight.progress.allocated[&"str"] += 20
	ok(_hit(knight, target) > before * 1.1, "STR improves physical hits")
	done()

func test_percentage_procs_do_not_scale_twice() -> void:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = blank_stats(30)
	req.target = blank_stats(30)
	req.base_min = 100
	req.base_max = 100
	req.can_crit = false
	req.evadable = false
	var ordinary := DamagePipeline.compute(req, rng(7)).total
	req.attacker.set_stat(&"spell_power", 2.0)
	ok(DamagePipeline.compute(req, rng(7)).total > ordinary * 2.9, "ordinary spells use spell power")
	for tag in [&"proc", &"thorns"]:
		req.tags = {tag: true}
		eq(DamagePipeline.compute(req, rng(7)).total, ordinary, "percentage damage does not gain spell power again")
	done()

func test_rank_requires_distinct_achievements() -> void:
	var h := _hero(&"knight", 60)
	h.inventory.gold = 1000000
	GuildRules.join(h, &"swordfin")
	ok(not GuildRules.next_promotion(h).ok, "level and gold alone do not even earn D")
	for r in range(2, DataGuilds.MAX_RANK + 1):
		var t := DataGuilds.tier(r)
		ok(int(t.level) <= BH.LEVEL_CAP, "every player rank is reachable")
		if t.flag != "":
			h.world_flags[StringName(t.flag)] = true
	h.guild_jobs["done"] = 120
	h.miniboss_log[&"snagtooth"] = {"kills": 10000}
	h.dungeon_raids["warren"] = {"count": 10000}
	h.set_tier(5)
	ok(not GuildRules.next_promotion(h).ok, "farming one boss cannot earn S")
	for i in 16:
		h.miniboss_log[StringName("champion_%d" % i)] = {"kills": 1}
	for id in DataDungeons.order():
		h.dungeon_raids[String(id)] = {"count": 1}
	for rank in [6, 7, 8]:
		eq(GuildRules.promote(h), "", "achievements earn rank %d" % rank)
		eq(h.tier, rank, "one rank per promotion")
	var d := h.to_dict()
	d.erase("tier_rules_version")
	eq(HeroData.from_dict(d).tier, 8, "old saves retain earned ranks")
	done()
