extends TestCase

func _init() -> void:
	strict = true

func geared(cid: StringName, level: int, rarity := BH.Rarity.MASTER) -> HeroData:
	var h := Game.new_hero(cid, "Balance audit")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	h.progress.allocate(&"int" if cid == &"mage" else (&"dex" if cid == &"ranger" else &"str"), h.progress.free_points)
	h.equipment.tier_rank = 8
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

func test_screenshot_weapons_and_legacy_migration() -> void:
	var bow := DB.make_item(&"artisan_dragon_rib_bow", BH.Rarity.MASTER, 49, 1)
	var crossbow := DB.make_item(&"frost_fork_crossbow", BH.Rarity.MASTER, 49, 1)
	for it in [bow, crossbow]:
		it.quality = 0.14
		it.affixes.clear()
	crossbow.affixes.append({"id": "local_phys", "tier": 3, "value": 0.40, "mw": true})
	var bow_dps := (bow.damage_range().x + bow.damage_range().y) * 0.5 * bow.base.weapon_aps()
	var cross_dps := (crossbow.damage_range().x + crossbow.damage_range().y) * 0.5 * crossbow.base.weapon_aps()
	ok(cross_dps / bow_dps < 1.45, "masterwork advantage is bounded at matching item level")
	var saved := crossbow.to_dict()
	saved.erase("balance_version")
	saved.affixes[0].value = 1.0
	saved.affixes.append({"id": "magic_damage", "tier": 2, "value": 0.34})
	var migrated := ItemInstance.from_dict(saved)
	near(migrated.affixes[0].value, 0.40, 0.001, "old 100% roll becomes 40% masterwork")
	for affix in migrated.affixes:
		ok(ItemGenerator.affix_fits(migrated.base, DB.affix(StringName(affix.id))), "saved class affixes repaired")
	eq(ItemInstance.from_dict(migrated.to_dict()).to_dict(), migrated.to_dict(), "migration is idempotent")
	print("SCREENSHOT corrected bow=", bow.damage_range(), " crossbow=", crossbow.damage_range(), " DPS ratio=", cross_dps / bow_dps)
	done()

func test_class_sets_and_powers() -> void:
	for base: ItemBaseDef in DB.item_bases.values():
		if base.set_id == &"":
			continue
		for seed_value in range(4):
			var it := DB.make_item(base.id, BH.Rarity.AETHER, 49, seed_value)
			for a in it.affixes:
				ok(ItemGenerator.affix_fits(base, DB.affix(StringName(a.id))), "%s affix fits class" % base.id)
			for id in it.powers:
				ok(ItemGenerator.power_fits(base, DB.power(StringName(id))), "%s power fits class" % base.id)
	done()

func test_milestones_and_full_progression() -> void:
	for level in [29, 30, 44, 45, 59, 60, 74, 75, 89, 90, 104, 105, 150, 225, 300]:
		var floor_level := CombatGrowth.encounter_level(5, level)
		# bh-028: from level 30 monsters follow the hero closely (CombatBudget.ENCOUNTER_GAP) instead of 15-level steps
		eq(floor_level, 5 if level < 30 else level - CombatBudget.ENCOUNTER_GAP, "authored floor, then close behind the hero")
		if level >= 30:
			ok(floor_level <= level and floor_level >= level - CombatBudget.ENCOUNTER_GAP, "encounter level")
		eq(CombatGrowth.encounter_level(5, level, true), level, "boss matches hero level")
		for cid in [&"knight", &"mage", &"ranger", &"shadowblade"]:
			var h := geared(cid, level)
			var st := h.compute_stats()
			ItemCompare._add_weapon_rows(st)
			var enemy := EnemyStats.build(DB.enemy(&"hollow_soldier"), level, {}, [])
			var boss := EnemyStats.build(DB.enemy(&"boss_warden"), level, {}, [], false, true)
			var hp := EnemyStats.boss_health(h, boss)
			var seconds := enemy.get_stat(&"max_hp") / st.get_stat(&"weapon_dps")
			# Ten stat points per level allow an all-offense build to kill ordinary foes quickly.
			ok(is_finite(seconds) and seconds > 0.0 and seconds < 25.0, "%s level %d regular TTK %.1f" % [cid, level, seconds])
			ok(hp > ItemCompare.basic_hit(st) * st.get_stat(&"crit_damage") * 3.0, "boss survives a critical hit")
			if level in [30, 45, 60, 75, 90, 105, 300]:
				print("AUDIT ", JSON.stringify({"class": cid, "level": level, "dps": roundi(st.get_stat(&"weapon_dps")), "enemy_hp": roundi(enemy.get_stat(&"max_hp")), "seconds": snappedf(seconds, 0.1), "boss_hp": roundi(hp)}))
	done()

func test_ranger_burst_and_proc_scaling() -> void:
	var h := geared(&"ranger", 49, BH.Rarity.AETHER)
	# Spend a legal level-49 point budget through the real progression APIs.
	for id in [&"frost_arrow", &"deadeye", &"keen_eye", &"deadly_aim", &"piercing_arrows"]:
		eq(h.spend_skill_point(id), "", "Ranger burst build prerequisites")
	for i in 24:
		eq(h.spend_skill_point(&"deadeye"), "", "rank Deadeye with available points")
	for i in 15:
		eq(h.spend_skill_point(&"power_shot"), "", "rank the Deadeye synergy")
	for id in [&"r_dex", &"r_bow", &"r_projdmg"]:
		eq(h.spend_talent_point(id), "", "Ranger offensive talent prerequisites")
	for i in 15:
		eq(h.spend_talent_point(&"r_dex"), "", "Dexterity investment")
	for i in 15:
		eq(h.spend_talent_point(&"r_projdmg"), "", "projectile investment")
	var st := h.compute_stats()
	var target := EnemyStats.build(DB.enemy(&"kethrax"), 49, {}, [], false, true)
	var boss_hp := EnemyStats.boss_health(h, target)
	target = EnemyStats.build(DB.enemy(&"kethrax"), 49, {}, [StatModifier.more(&"max_hp", boss_hp / target.get_stat(&"max_hp") - 1.0)], false, true)
	var caster := Actor.new()
	caster.stats = st
	var params := h.resolved_skill(&"deadeye")
	params["_focus"] = 100.0
	var req := SkillRunner.new(caster).make_request(DB.skill(&"deadeye"), params)
	req.target = target
	req.evadable = false
	req.force_crit = true
	req.heavy = true
	req.tags[&"projectile"] = true
	var max_hit := 0
	for i in 200:
		max_hit = maxi(max_hit, DamagePipeline.compute(req, rng(i)).total)
	caster.free()
	print("RANGER burst=", max_hit, " boss_hp=", target.get_stat(&"max_hp"))
	ok(max_hit <= 12000, "level 49 legendary-or-better boss critical stays below 12,000")
	ok(max_hit <= target.get_stat(&"max_hp") * 0.081, "critical never removes 20% of boss HP")
	req.target.set_stat(&"damage_taken", 1.4)
	var marked_max := 0
	for i in 200:
		marked_max = maxi(marked_max, DamagePipeline.compute(req, rng(i)).total)
	ok(marked_max >= 9000 and marked_max <= 12000, "stacked high-end boss critical reaches the requested 9k-12k band")
	print("RANGER marked boss critical=", marked_max)
	var boss := EnemyStats.build(DB.enemy(&"boss_warden"), 49, {}, [], false, true)
	ok(EnemyStats.boss_health(h, boss) > max_hit * 8.0, "boss supports multiple burst rotations")
	var proc := DamageRequest.new()
	proc.attacker = st
	proc.target = blank_stats(49)
	proc.kind = DamageRequest.Kind.SPELL
	proc.base_min = 100
	proc.base_max = 100
	proc.tags[&"proc"] = true
	proc.conversion = {Elements.LIGHTNING: 1.0}
	proc.force_crit = true
	proc.more = [["Offensive passive", 2.0]]
	eq(DamagePipeline.compute(proc, rng()).total, 100, "inherited proc damage is not multiplied again")
	done()

func test_automatic_rank_all_requirements_and_reload() -> void:
	var h := Game.new_hero(&"ranger", "Early story")
	h.progress.add_xp(210)
	for flag in GuildRules.OPENING_DEEDS:
		if flag == &"mq_three_told":
			continue
		h.world_flags[flag] = true
	h.check_promotions()
	eq(h.tier, 0, "incomplete opening story does not promote")
	h.world_flags[&"mq_three_told"] = true
	h.check_promotions()
	eq(h.tier, 1, "opening quests earn a rank without guild or gold")
	eq(h.guild, &"", "guild choice remains the player's")
	h.guild = &"swordfin"
	h.check_promotions()
	eq(h.tier, 2, "registered hero earns first promotion from opening quests")
	h.progress.level = 12
	h.world_flags[&"catacombs_ritual_seen"] = true
	h.guild_jobs["done"] = 5
	h.dungeon_raids["warren"] = {"count": 1}
	h.miniboss_log[&"snagtooth"] = {"kills": 1}
	h.inventory.gold = 399
	h.check_promotions()
	eq(h.tier, 2, "all deeds without fee cannot promote")
	h.inventory.gold = 500
	h.inventory.changed.emit()
	eq(h.tier, 3, "final gold requirement triggers promotion automatically")
	eq(h.inventory.gold, 100, "fee charged once")
	var copy := HeroData.from_dict(h.to_dict())
	eq(copy.tier, 3, "rank persists")
	eq(copy.inventory.gold, 100, "load cannot charge again")
	done()

func test_first_story_boss_spawn_and_snapshot() -> void:
	var saved_hero := Game.hero
	var holder := Node3D.new()
	host.add_child(holder)
	Game.hero = geared(&"ranger", 49)
	var boss := Spawner.spawn_enemy(holder, DB.enemy(&"kethrax"), 6, [], Vector3.ZERO, DataEnemies.DIFFICULTY[1])
	boss.set_meta(&"net_id", 998)
	eq(boss.level, 49, "first story boss follows player level")
	var health := boss.max_hp()
	ok(health > 40000, "first story boss survives several level-49 bursts")
	var snapshot := boss.encounter_hp_mult
	Game.hero.equipment.slots[&"main_weapon"] = null
	boss.rebuild_stats()
	near(boss.max_hp(), health, 0.1, "gear swap does not resize active encounter")
	near(float(Net.enemy_info(boss).encounter_hp_mult), snapshot, 0.000001, "network snapshot retains encounter health")
	print("STORY_BOSS ", JSON.stringify({"level": boss.level, "hp": roundi(health)}))
	holder.queue_free()
	Game.hero = saved_hero
	await host.get_tree().process_frame
	done()

func test_item_preview_matches_pipeline() -> void:
	for cid in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := geared(cid, 49)
		var st := h.compute_stats()
		var req := DamageRequest.new()
		req.attacker = st
		req.target = blank_stats(49)
		# The preview is target-independent; penetration below a target's 0% resistance is not part of it. A target
		# that resists exactly the attacker's penetration leaves the hit at its untargeted value.
		for e in Elements.ELEMENTAL:
			req.target.values[Elements.res_key(e)] = st.get_stat(Elements.pen_key(e))
		req.can_crit = false
		req.evadable = false
		if st.loadout.main_type.ranged:
			req.tags[&"projectile"] = true
		var total := 0.0
		var random := rng(471)
		for i in 1000:
			total += DamagePipeline.compute(req, random).total
		var expected := ItemCompare.basic_hit(st)
		near(total / 1000.0, expected, expected * 0.035, "equipment preview matches %s actual hit average" % cid)
	done()

func test_boss_guard_extreme_hits_procs_and_lower_rarity() -> void:
	for rarity in [BH.Rarity.ELITE, BH.Rarity.MASTER, BH.Rarity.LEGENDARY]:
		var h := geared(&"ranger", 49, rarity)
		var target := EnemyStats.build(DB.enemy(&"kethrax"), 49, {}, [], false, true)
		var hp := EnemyStats.boss_health(h, target)
		target = EnemyStats.build(DB.enemy(&"kethrax"), 49, {}, [StatModifier.more(&"max_hp", hp / target.get_stat(&"max_hp") - 1.0)], false, true)
		var req := DamageRequest.new()
		req.attacker = h.compute_stats()
		req.target = target
		req.weapon_mult = 6.0
		req.force_crit = true
		req.evadable = false
		req.tags[&"projectile"] = true
		var max_hit := 0
		for i in 100:
			max_hit = maxi(max_hit, DamagePipeline.compute(req, rng(i)).total)
		# Extra attribute points can reach the burst ceiling even with lower-rarity gear.
		ok(max_hit <= 12000, "boss critical stays within the level-49 burst budget")
		print("BOSS_CRIT ", JSON.stringify({"rarity": rarity, "max_hit": max_hit, "hp": roundi(hp)}))
		for kind in [DamageRequest.Kind.ATTACK, DamageRequest.Kind.SPELL, DamageRequest.Kind.DOT, DamageRequest.Kind.IMPACT]:
			req.kind = kind
			req.use_weapon = false
			req.base_min = 1e9
			req.base_max = 1e9
			req.tags[&"proc"] = true
			var hit := DamagePipeline.compute(req, rng())
			ok(hit.total <= 12000 and hit.total <= hp * 0.081, "all damage paths obey boss burst protection")
	done()

func test_boss_difficulty_and_weak_equipment_floor() -> void:
	var h := geared(&"ranger", 49)
	var normal := EnemyStats.build(DB.enemy(&"kethrax"), 49, {"hp": 1.0}, [], false, true)
	var hard := EnemyStats.build(DB.enemy(&"kethrax"), 49, {"hp": 1.5}, [], false, true)
	ok(EnemyStats.boss_health(h, hard) > EnemyStats.boss_health(h, normal), "adaptive bosses preserve difficulty HP")
	h.equipment.slots[&"main_weapon"] = null
	ok(EnemyStats.boss_health(h, normal) > 20000, "unequipping before entering cannot erase boss health")
	done()
