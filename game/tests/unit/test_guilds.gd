extends TestCase
## Hero tiers and guilds (docs/LORE.md §5): joining, transfers, promotion requirements, equip gating by rarity,
## perks and discounts, the inn (fee, restore, Well Rested), dialogue conditions/placeholders, save round-trip.

func _init() -> void:
	strict = true

func _hero(gold := 100000, level := 1) -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "GuildTest")
	h.init_new()
	h.inventory.gold = gold
	if level > 1:
		h.progress.add_xp(XpCurve.total_xp_for_level(level))
	return h

func test_tier_table() -> void:
	eq(DataGuilds.TIERS.size(), 9, "Unranked + eight tiers")
	var letters := []
	for r in range(1, DataGuilds.MAX_RANK + 1):
		letters.append(DataGuilds.letter(r))
	eq(",".join(letters), "E,D,C,B,A,S,SS,SSS", "tier letters in order")
	for r in range(2, DataGuilds.MAX_RANK + 1):
		ok(int(DataGuilds.tier(r).level) > int(DataGuilds.tier(r - 1).level), "tier %d needs a higher level than %d" % [r, r - 1])
		ok(int(DataGuilds.tier(r).fee) > int(DataGuilds.tier(r - 1).fee), "tier %d costs more than %d" % [r, r - 1])
	eq(DataGuilds.rank_for_rarity(BH.Rarity.ELITE), 0, "Elite is not gated")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.LICENSED), 1, "Licensed needs Class E")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.MASTER), 2, "Master needs Class D")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.MYTHICAL), 3, "Mythical needs Class C")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.LEGENDARY), 4, "Legendary needs Class B")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.AETHER), 5, "Aether needs Class A")
	eq(DataGuilds.GUILDS.size(), 2, "two guilds in Malasugue")
	done()

func test_join_and_transfer() -> void:
	var h := _hero(60)
	eq(h.tier, 0, "new hero is Unranked")
	eq(GuildRules.join_fee(h, &"swordfin"), 50, "first registration costs the Class E fee")
	eq(GuildRules.join(h, &"swordfin"), "", "joins")
	eq(h.guild, &"swordfin", "member")
	eq(h.tier, 1, "registered as Class E")
	eq(h.inventory.gold, 10, "paid exactly 50")
	ok(GuildRules.join(h, &"swordfin") != "", "cannot join the same guild twice")
	ok(GuildRules.join(h, &"lantern") != "", "transfer refused without the fee")
	eq(h.guild, &"swordfin", "still Swordfin after a refused transfer")
	h.inventory.gold = 1000
	h.set_tier(3)
	eq(GuildRules.join(h, &"lantern"), "", "transfer with the fee")
	eq(h.inventory.gold, 1000 - DataGuilds.TRANSFER_FEE, "transfer fee charged")
	eq(h.tier, 3, "tier kept across a transfer")
	ok(GuildRules.join(h, &"nonsense") != "", "unknown guild refused")
	done()

func test_promotion_requirements() -> void:
	var h := _hero(100000, 1)
	ok(not GuildRules.next_promotion(h).ok, "Unranked heroes cannot be promoted")
	GuildRules.join(h, &"lantern")
	var p := GuildRules.next_promotion(h)
	eq(int(p.rank), 2, "next is D")
	ok(not p.ok and String(p.error).contains("level"), "D needs level 4")
	h.progress.add_xp(XpCurve.total_xp_for_level(4))
	var gold := h.inventory.gold
	eq(GuildRules.promote(h), "", "promoted to D at level 4")
	eq(h.tier, 2, "Class D")
	eq(h.inventory.gold, gold - 150, "D fee charged exactly")
	h.progress.add_xp(XpCurve.total_xp_for_level(8))
	var pc := GuildRules.next_promotion(h)
	ok(not pc.ok and String(pc.error).contains("deed"), "C needs the Catacomb ritual deed")
	eq(h.tier, 2, "not promoted without the deed")
	h.world_flags[&"catacombs_ritual_seen"] = true
	eq(GuildRules.promote(h), "", "promoted to C with the deed")
	h.inventory.gold = 10
	ok(GuildRules.promote(h) != "", "no promotion without gold")
	eq(h.tier, 3, "tier unchanged after a failed promotion")
	eq(h.inventory.gold, 10, "gold unchanged after a failed promotion")
	h.set_tier(DataGuilds.MAX_RANK)
	eq(int(GuildRules.next_promotion(h).rank), -1, "nothing above SSS")
	done()

func test_equip_gating() -> void:
	var h := _hero(0, 20)
	for a in BH.ATTRIBUTES:
		h.progress.allocated[a] = 60
	var ring := DB.make_item(&"copper_ring", BH.Rarity.LICENSED, 5, 7)
	ok(ring != null and ring.rarity == BH.Rarity.LICENSED, "licensed test item")
	h.inventory.add(ring)
	var err := h.equip_from_inventory(ring)
	ok(err.begins_with("Requires a Class E"), "Unranked cannot equip Licensed (%s)" % err)
	ok(h.equipment.slot_of(ring) == &"", "not equipped")
	ok(h.inventory.index_of(ring) >= 0, "still in the inventory")
	h.inventory.gold = 100
	GuildRules.join(h, &"swordfin")
	eq(h.equip_from_inventory(ring), "", "Class E equips Licensed")
	# every gated rarity is refused one tier below its gate and accepted at it
	for rar in [BH.Rarity.MASTER, BH.Rarity.MYTHICAL, BH.Rarity.LEGENDARY, BH.Rarity.AETHER]:
		var need := DataGuilds.rank_for_rarity(rar)
		var it := DB.make_item(ring.base.id, rar, 20, 11 + rar)
		h.set_tier(need - 1)
		ok(h.equipment.check(it, h.equipment.auto_slot(it), 20, h.progress.base_attributes()).begins_with("Requires a Class"), "%s refused below Class %s" % [BH.rarity_name(rar), DataGuilds.letter(need)])
		h.set_tier(need)
		eq(h.equipment.check(it, h.equipment.auto_slot(it), 20, h.progress.base_attributes()), "", "%s accepted at Class %s" % [BH.rarity_name(rar), DataGuilds.letter(need)])
	# a bare Equipment (previews, tools) is ungated
	var bare := Equipment.new()
	var aeth := DB.make_item(ring.base.id, BH.Rarity.AETHER, 20, 3)
	eq(bare.check(aeth, bare.auto_slot(aeth), 60, {&"str": 99, &"agi": 99, &"int": 99, &"wis": 99, &"spi": 99, &"dex": 99}), "", "ungated default")
	done()

func test_perks_and_discounts() -> void:
	var h := _hero()
	var before := h.compute_stats()
	GuildRules.join(h, &"swordfin")
	h.set_tier(4)
	var after := h.compute_stats()
	ok(after.get_stat(&"max_hp") > before.get_stat(&"max_hp"), "Accord bonus raises Maximum HP")
	near(after.get_stat(&"phys_damage") - before.get_stat(&"phys_damage"), 0.08, 0.0001, "Swordfin +2% physical damage per tier step")
	near(GuildRules.shop_discount(h, &"brannoc_forge"), 0.15, 0.0001, "Swordfin forge discount")
	near(GuildRules.shop_discount(h, &"seris_arcana"), 0.0, 0.0001, "no arcana discount for Swordfin")
	near(GuildRules.elite_gold_bonus(h), 0.10, 0.0001, "bounty pay")
	# discounted purchase charges the discounted price exactly
	var shop := Shop.open(DB.shop(&"brannoc_forge"), h)
	shop.generate(h)
	var idx := 0
	var full := ShopPricing.buy_total(shop.stock[idx].item, shop.def, 1, h.relationship(shop.def.npc))
	var disc := shop.buy_price(idx, h, 1)
	eq(disc, maxi(1, ceili(float(full) * 0.85)), "15% off at the forge")
	var gold := h.inventory.gold
	var res := shop.buy(idx, h, 1)
	ok(res.ok, "bought")
	eq(gold - h.inventory.gold, disc, "charged the quoted discounted price")
	GuildRules.join(h, &"lantern")
	near(GuildRules.inn_discount(h), 0.25, 0.0001, "Lantern inn discount")
	near(after.get_stat(&"magic_damage"), before.get_stat(&"magic_damage"), 0.0001, "Swordfin gave no magic damage")
	var lan := h.compute_stats()
	ok(lan.get_stat(&"max_mana") > after.get_stat(&"max_mana"), "Lantern raises Maximum Mana")
	done()

func test_inn_rest() -> void:
	var h := _hero(0, 5)
	var fee := NpcServices.rest_cost(h)
	eq(fee, 10 + 5 * 5, "rest fee at level 5")
	ok(NpcServices.rest(h, null) != "", "no rest without gold")
	ok(not h.is_rested(), "not rested after a refused rest")
	h.inventory.gold = fee
	eq(NpcServices.rest(h, null), "", "rests")
	eq(h.inventory.gold, 0, "paid exactly the fee")
	ok(h.is_rested(), "Well Rested")
	var s := h.compute_stats()
	near(s.get_stat(&"xp_gain"), HeroData.RESTED_XP, 0.0001, "rest grants experience gain")
	h.play_time += NpcServices.REST_DURATION + 1.0
	ok(not h.is_rested(), "rest wears off")
	h.guild = &"lantern"
	h.set_tier(1)
	eq(NpcServices.rest_cost(h), int(round((10 + 25) * 0.75)), "Lantern pays 25% less")
	eq(NpcServices.mystic_heal_cost(h), (10 + 25) * 2, "Seris charges twice the base inn price")
	done()

func test_dialogue_conditions_and_placeholders() -> void:
	var h := _hero(1000, 5)
	var d := Dialogue.new(&"x", {})
	ok(d.check({"no_guild": true}, h), "no_guild before joining")
	GuildRules.join(h, &"lantern")
	ok(d.check({"guild": "lantern"}, h), "guild condition")
	ok(d.check({"not_guild": "swordfin"}, h), "not_guild condition")
	ok(d.check({"tier_min": 1}, h) and not d.check({"tier_min": 2}, h), "tier_min")
	ok(d.check({"can_promote": true}, h), "can promote to D at level 5")
	var t := Dialogue.fill("Rest for {rest_fee}. Next: {next_tier} for {promo_fee}. You are {tier}.", h)
	ok(not t.contains("{"), "all placeholders filled")
	ok(t.contains(str(NpcServices.rest_cost(h))) and t.contains("Class D") and t.contains("150"), "live values: %s" % t)
	done()

func test_save_round_trip() -> void:
	var h := _hero(5000, 12)
	GuildRules.join(h, &"swordfin")
	h.set_tier(4)
	h.play_time = 100.0
	h.rested_until = 700.0
	var d := h.to_dict()
	var h2 := HeroData.from_dict(JSON.parse_string(JSON.stringify(d)))
	eq(h2.guild, &"swordfin", "guild saved")
	eq(h2.tier, 4, "tier saved")
	eq(h2.equipment.tier_rank, 4, "equipment gating restored")
	near(h2.rested_until, 700.0, 0.001, "rest saved")
	ok(h2.is_rested(), "still rested after load")
	# an old save (no guild keys) loads Unranked and keeps whatever was equipped
	var old := d.duplicate(true)
	old.erase("guild")
	old.erase("tier")
	old.erase("rested_until")
	var h3 := HeroData.from_dict(old)
	eq(h3.tier, 0, "old saves load Unranked")
	eq(h3.equipment.equipped_items().size(), h.equipment.equipped_items().size(), "old saves keep equipped items")
	# a save naming an unknown guild is sanitised
	var bad := d.duplicate(true)
	bad["guild"] = "pirates"
	bad["tier"] = 99
	var h4 := HeroData.from_dict(bad)
	eq(h4.guild, &"", "unknown guild dropped")
	eq(h4.tier, 0, "tier without a guild dropped")
	done()
