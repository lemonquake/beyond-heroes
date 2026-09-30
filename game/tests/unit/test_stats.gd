extends TestCase
## Stat calculation, equipment application/removal, dual wield and shields.

func _hero(cls_id := &"knight", with_gear := true) -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls_id), "Test")
	if with_gear:
		h.init_new()
	return h

func test_attribute_contributions_knight_level1() -> void:
	var h := _hero(&"knight", false)
	var s := h.compute_stats()
	# Knight L1: HP = 120 + 14*6 + 6*4 + 9*1 = 237.
	eq(s.get_stat(&"max_hp"), 237.0, "knight max hp")
	# Mana = 30 + 5*4 + 6*1 + 9*3 = 83.
	eq(s.get_stat(&"max_mana"), 83.0, "knight max mana")
	# Defense = (20 + 14*0.5) * 1.10 (class inc) = 29.7 -> floor 29
	eq(s.get_stat(&"defense"), 29.0, "knight defense")
	# Crit = unarmed 5% + DEX 10*0.08% + AGI 9*0.04% = 6.16%
	near(s.get_stat(&"crit_chance"), 0.0616, 0.00001, "crit chance")
	eq(s.get_stat(&"crit_damage"), 1.5, "default crit multiplier 1.5")
	# Move = 5.2 * (1 + AGI 9*0.25% + STR 14*0.2%) = 5.4626 (nothing carried: no load slowdown)
	near(s.get_stat(&"move_speed"), 5.2 * 1.0505, 0.0001, "move speed")

func test_move_speed_cap_and_attack_speed_dr() -> void:
	var h := _hero()
	var s := StatCalculator.compute(h.cls, 1, h.progress.base_attributes(), [StatModifier.inc(&"move_speed", 5.0)], WeaponLoadout.new())
	near(s.get_stat(&"move_speed"), 5.2 * 1.5, 0.0001, "move speed hard cap 150%")
	var s2 := StatCalculator.compute(h.cls, 1, {&"agi": 0}, [StatModifier.inc(&"attack_speed", 0.3)], WeaponLoadout.new())
	# soften(0.3) = 0.3/(1+0.2) = 0.25
	near(s2.get_stat(&"attack_speed"), 1.25, 0.0001, "diminishing returns")
	var s3 := StatCalculator.compute(h.cls, 1, {&"agi": 0}, [StatModifier.inc(&"attack_speed", 50.0)], WeaponLoadout.new())
	ok(s3.get_stat(&"attack_speed") <= StatCalculator.SPEED_MULT_MAX, "attack speed hard cap")
	var s4 := StatCalculator.compute(h.cls, 1, {&"agi": 0}, [StatModifier.more(&"move_speed", -0.95)], WeaponLoadout.new())
	near(s4.get_stat(&"move_speed"), 5.2 * StatCalculator.MOVE_MIN_FACTOR, 0.0001, "move speed floor")

func test_equip_unequip_applies_once_and_removes_cleanly() -> void:
	var h := _hero()
	var ring := DB.make_item(&"copper_ring", BH.Rarity.COMMON, 1, 5)
	ring.affixes = [{"id": "str", "tier": 0, "value": 4.0}, {"id": "max_hp", "tier": 0, "value": 12.0}, {"id": "res_fire", "tier": 0, "value": 0.1}]
	h.inventory.add(ring)
	# the ring is carried (in the bag or worn) in both snapshots, so weight and load match too
	var before := h.compute_stats().values.duplicate()
	eq(h.equip_from_inventory(ring, &"accessory_1"), "", "equip ok")
	var with := h.compute_stats()
	eq(with.get_stat(&"str"), before[&"str"] + 4.0, "+4 str once")
	# +4 STR -> +24 HP, +12 flat -> +36 HP
	eq(with.get_stat(&"max_hp"), before[&"max_hp"] + 36.0, "hp from str and affix")
	near(with.get_stat(&"res_fire"), before[&"res_fire"] + 0.1, 0.00001, "fire res")
	eq(h.unequip_to_inventory(&"accessory_1"), "", "unequip ok")
	var after := h.compute_stats().values
	for k in before:
		near(float(after[k]), float(before[k]), 0.00001, "stat %s restored" % k)
	# Equip twice into two different accessory slots: both count, still exactly once each.
	var ring2 := ring.clone()
	h.equip_from_inventory(ring, &"accessory_1")
	h.inventory.add(ring2)
	h.equip_from_inventory(ring2, &"accessory_2")
	eq(h.compute_stats().get_stat(&"str"), before[&"str"] + 8.0, "two rings stack additively")

func test_slot_layout_exact() -> void:
	eq(BH.SLOTS.size(), 14, "14 slots (bh-024 Leggings)")
	eq(BH.CATEGORY_SLOTS[&"leggings"].size(), 1, "1 leggings slot")
	eq(BH.CATEGORY_SLOTS[&"gloves"].size(), 2, "2 glove slots")
	eq(BH.CATEGORY_SLOTS[&"boots"].size(), 2, "2 boot slots")
	eq(BH.CATEGORY_SLOTS[&"accessory"].size(), 4, "4 accessory slots")
	var h := _hero()
	var helm := DB.make_item(&"iron_helm", 0, 1, 1)
	ok(h.equipment.check(helm, &"armor", 1, h.progress.base_attributes()) != "", "helm rejected in armor slot")

func test_dual_wield_and_two_handed_rules() -> void:
	var h := _hero()
	h.progress.allocated[&"dex"] = 30
	h.progress.allocated[&"agi"] = 30
	h.progress.allocated[&"str"] = 30
	h.equipment.unequip(&"sub_weapon")
	var axe := DB.make_item(&"hand_axe", 0, 1, 3)
	h.inventory.add(axe)
	eq(h.equip_from_inventory(axe, &"sub_weapon"), "", "axe into sub hand")
	var lo := h.equipment.loadout()
	ok(lo.dual_wield, "dual wield enabled")
	ok(not lo.has_shield, "no shield")
	var s := h.compute_stats()
	var solo := StatCalculator.compute(h.cls, 1, h.progress.base_attributes(), h.persistent_modifiers(), _single(h))
	near(s.get_stat(&"attack_speed") / solo.get_stat(&"attack_speed"), 1.15, 0.0001, "15% more attack speed")
	eq(s.get_stat(&"block_chance"), 0.0, "no block chance without shield")
	var gs := DB.make_item(&"rusted_claymore", 0, 1, 4)
	h.inventory.add(gs)
	eq(h.equip_from_inventory(gs, &"main_weapon"), "", "greatsword equips")
	eq(h.equipment.get_item(&"sub_weapon"), null, "two-handed clears sub hand")
	ok(h.inventory.index_of(axe) >= 0, "off-hand returned to inventory")
	var bow := DB.make_item(&"hunters_bow", 0, 1, 5)
	ok(h.equipment.check(bow, &"sub_weapon", 1, h.progress.base_attributes()) != "", "bow not allowed in sub hand")

func _single(h: HeroData) -> WeaponLoadout:
	var lo := h.equipment.loadout()
	lo.dual_wield = false
	lo.off_type = null
	return lo

func test_shield_block() -> void:
	var h := _hero()
	var s := h.compute_stats()
	ok(s.loadout.has_shield, "knight starts with shield")
	# Dexterity now affects only accuracy and critical chance.
	near(s.get_stat(&"block_chance"), 0.25, 0.00001, "shield block chance")
	# 60% shield + 10% class + STR14 * 0.2% = 72.8%
	near(s.get_stat(&"block_strength"), 0.728, 0.00001, "block strength")

func test_resistance_caps_and_explanations() -> void:
	var h := _hero(&"mage")
	var s := StatCalculator.compute(h.cls, 1, h.progress.base_attributes(), [StatModifier.flat(&"res_fire", 2.0), StatModifier.flat(&"res_ice", -5.0)], WeaponLoadout.new())
	eq(s.get_stat(&"res_fire"), StatCalculator.RES_CAP, "resistance cap")
	eq(s.get_stat(&"res_ice"), StatCalculator.RES_FLOOR, "resistance floor")
	ok(s.explain.has(&"max_hp") and s.explain[&"max_hp"].size() >= 3, "max hp has explanation lines")
	ok(s.explain.has(&"move_speed"), "move speed explained")

func test_talent_modifiers_modify_stats() -> void:
	var h := _hero()
	h.progress.talent_points = 10
	h.progress.level = 10
	var hp0 := h.compute_stats().get_stat(&"max_hp")
	eq(h.spend_talent_point(&"k_vit"), "", "learn vitality")
	var hp1 := h.compute_stats().get_stat(&"max_hp")
	near(hp1 / hp0, 1.06, 0.01, "vitality rank 1 = +6% max HP")
	eq(h.spend_talent_point(&"k_armor"), "", "learn tempered steel")
	var d0 := h.compute_stats().get_stat(&"defense")
	h.refund_talent_point(&"k_armor")
	ok(h.compute_stats().get_stat(&"defense") < d0, "refund removes defense bonus")
