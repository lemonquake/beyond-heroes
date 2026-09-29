extends TestCase
## Shops (pricing formula, stock generation/refresh, buy/sell/buyback, specials, persistence), dialogue
## (entries react to world flags, branches, choices, actions, memory, relationship) and NPC services (respec).

func _init() -> void:
	strict = true

func _hero(cls_id := &"knight", gold := 5000) -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(cls_id), "ShopTest")
	h.init_new()
	h.inventory.gold = gold
	return h

func test_data_is_consistent() -> void:
	ok(DB.npcs.size() >= 6, "six townspeople")
	for n in DB.npcs.values():
		var d := Dialogue.new(n.id, n.graph)
		ok(ResourceLoader.exists(n.portrait), "%s portrait exists" % n.id)
		ok(n.shop == &"" or DB.shop(n.shop) != null, "%s shop exists" % n.id)
		var nodes: Dictionary = n.graph.get("nodes", {})
		for e in n.graph.get("entries", []):
			ok(nodes.has(String(e[1])), "%s entry -> %s exists" % [n.id, e[1]])
		for id in nodes:
			var node: Dictionary = nodes[id]
			var targets := []
			if node.has("next"):
				targets.append(String(node.next))
			for c in node.get("choices", []):
				targets.append(String(c.get("next", "end")))
				for a in c.get("actions", []):
					if a.has("open_shop"):
						ok(DB.shop(StringName(a.open_shop)) != null, "%s/%s opens a real shop" % [n.id, id])
			for b in node.get("branch", []):
				targets.append(String(b[1]))
			for t in targets:
				ok(t == "end" or nodes.has(t), "%s/%s -> %s exists" % [n.id, id, t])
			for a in node.get("actions", []):
				if a.has("give_item"):
					ok(DB.item_base(StringName(a.give_item)) != null, "%s/%s gives a real item" % [n.id, id])
		ok(d.entry_node(_hero()) != "", "%s always has an entry" % n.id)
	for s in DB.shops.values():
		ok(DB.npc(s.npc) != null and DB.npc(s.npc).shop == s.id, "%s is run by its NPC" % s.id)
		for f in s.fixed:
			ok(DB.item_base(StringName(f.base)) != null, "%s fixed %s exists" % [s.id, f.base])
		for sp in s.specials:
			ok(DB.item_base(StringName(sp.base)) != null, "%s special %s exists" % [s.id, sp.base])
	done()

func test_pricing_formula() -> void:
	var h := _hero()
	var tovin := DB.shop(&"tovin_goods")
	var brannoc := DB.shop(&"brannoc_forge")
	var potion := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 3)
	# neutral: buy = ceil(value x markup x specialty), sell = floor(value x 0.25 x sell_rate x specialty)
	var v := potion.base_value()
	eq(ShopPricing.buy_price(potion, tovin, 0), maxi(1, ceili(v * 1.0 * 0.9)), "specialist buy price")
	eq(ShopPricing.sell_price(potion, tovin, 0), maxi(1, floori(v * 0.25 * 1.2)), "specialist sell price")
	eq(ShopPricing.buy_price(potion, brannoc, 0), maxi(1, ceili(v * 1.05)), "non-specialist buy price")
	# reputation moves prices within ±10%
	var sword := DB.make_item(&"iron_sword" if DB.item_base(&"iron_sword") else ItemGenerator.random_base(rng(3), 5, [&"weapon"]).id, BH.Rarity.ADVANCED, 5, 9)
	var neutral := ShopPricing.buy_price(sword, brannoc, 0)
	var loved := ShopPricing.buy_price(sword, brannoc, 100)
	var hated := ShopPricing.buy_price(sword, brannoc, -100)
	ok(loved < neutral and neutral < hated, "reputation orders prices (%d < %d < %d)" % [loved, neutral, hated])
	near(float(loved) / float(neutral), 0.9, 0.02, "max reputation = 10% off")
	# never profitable to buy and sell back
	for shop in DB.shops.values():
		for r in [0, 100]:
			ok(ShopPricing.sell_price(sword, shop, r) <= ShopPricing.buy_price(sword, shop, r), "%s no buy/sell loop at rel %d" % [shop.id, r])
	# higher rarity is worth more; higher item level is worth more
	var lo := DB.make_item(sword.base.id, BH.Rarity.COMMON, 5, 1)
	var hi := DB.make_item(sword.base.id, BH.Rarity.ELITE, 5, 1)
	ok(ShopPricing.buy_price(hi, brannoc) > ShopPricing.buy_price(lo, brannoc) * 3, "Elite costs far more than Common")
	var lvl20 := DB.make_item(sword.base.id, BH.Rarity.COMMON, 20, 1)
	ok(ShopPricing.buy_price(lvl20, brannoc) > ShopPricing.buy_price(lo, brannoc), "item level raises price")
	ok(ShopPricing.needs_confirmation(600, 10000), "expensive purchase asks")
	ok(ShopPricing.needs_confirmation(450, 1000), "large share of gold asks")
	ok(not ShopPricing.needs_confirmation(20, 1000), "cheap purchase does not ask")
	done()

func test_stock_generation_and_refresh() -> void:
	var h := _hero()
	var s := Shop.open(DB.shop(&"brannoc_forge"), h)
	ok(s.stock.size() >= 10, "smith has a full rack (%d)" % s.stock.size())
	for e in s.stock:
		ok(e.item.is_equipment(), "smith sells equipment only")
		ok(e.item.rarity <= BH.Rarity.ADVANCED or e.item.rarity == BH.Rarity.ELITE, "level-1 stock stays grounded (%s)" % e.item.rarity_name())
		if e.item.base.category == &"weapon":
			ok(not (e.item.base.weapon_type in [&"staff", &"wand"]), "smith does not sell staves")
	var s2 := Shop.open(DB.shop(&"seris_arcana"), h)
	for e in s2.stock:
		if e.item.base.category == &"weapon":
			ok(e.item.base.weapon_type in [&"staff", &"wand"], "mystic sells only staves/wands")
	# the same shop reopened is the same stock (persisted, not rerolled)
	var names := s.stock.map(func(e): return e.item.display_name())
	var again := Shop.open(DB.shop(&"brannoc_forge"), h)
	eq(again.stock.map(func(e): return e.item.display_name()), names, "reopening keeps stock")
	# refresh after the timer
	h.play_time += DB.shop(&"brannoc_forge").refresh_minutes * 60.0 + 1.0
	var later := Shop.open(DB.shop(&"brannoc_forge"), h)
	eq(later.refresh_index, 1, "stock refreshed once")
	ok(later.stock.map(func(e): return e.item.display_name()) != names, "new stock after refresh")
	# level scaling: outleveling forces a refresh and stock follows the hero
	h.progress.add_xp(XpCurve.total_xp_for_level(15))
	var scaled := Shop.open(DB.shop(&"brannoc_forge"), h)
	eq(scaled.stock_level, h.progress.level, "stock level follows the hero")
	for e in scaled.stock:
		eq(e.item.ilvl, h.progress.level, "item level = hero level")
	# two different merchants never carry identical goods
	var t := Shop.open(DB.shop(&"tovin_goods"), h)
	var overlap := 0
	for e in t.stock:
		for f in scaled.stock:
			if e.item.base.id == f.item.base.id:
				overlap += 1
	eq(overlap, 0, "provisioner and smith share no bases")
	done()

func test_buy_sell_buyback() -> void:
	var h := _hero(&"knight", 1000)
	var s := Shop.open(DB.shop(&"tovin_goods"), h)
	var idx := -1
	for i in s.stock.size():
		if s.stock[i].item.base.id == &"health_potion":
			idx = i
	ok(idx >= 0, "potions in stock")
	var had := h.inventory.count_of(&"health_potion")
	var price := s.buy_price(idx, h, 5)
	var r := s.buy(idx, h, 5)
	ok(r.ok, "bought five potions")
	eq(h.inventory.gold, 1000 - price, "gold charged exactly")
	eq(h.inventory.count_of(&"health_potion"), had + 5, "potions received")
	ok(idx < s.stock.size() and s.stock[idx].item.base.id == &"health_potion", "infinite stock stays")
	# not enough gold
	h.inventory.gold = 0
	var fail := s.buy(idx, h, 1)
	ok(not fail.ok and fail.error == "Not enough gold", "refuses without gold")
	eq(h.inventory.count_of(&"health_potion"), had + 5, "nothing given on failure")
	# sell a stack, buy it back for exactly the same gold
	h.inventory.gold = 100
	var stack: ItemInstance = null
	for c in h.inventory.cells:
		if c != null and c.base.id == &"health_potion":
			stack = c
	var n := stack.count
	var got := s.sell_price(stack, h)
	var sr := s.sell(stack, h)
	ok(sr.ok, "sold")
	eq(h.inventory.gold, 100 + got, "sale gold")
	eq(h.inventory.count_of(&"health_potion"), (had + 5) - n, "stack removed")
	eq(s.buyback.size(), 1, "in buyback")
	var bb := s.buy_back(0, h)
	ok(bb.ok, "bought back")
	eq(h.inventory.gold, 100, "buyback costs exactly what was paid")
	eq(h.inventory.count_of(&"health_potion"), had + 5, "stack restored")
	# locked items refuse
	stack = null
	for c in h.inventory.cells:
		if c != null and c.base.id == &"health_potion":
			stack = c
	stack.locked = true
	ok(not s.sell(stack, h).ok, "locked item cannot be sold")
	stack.locked = false
	# quest items are unsellable
	var q := DB.make_item(&"quest_tablet", BH.Rarity.COMMON, 1, 1)
	h.inventory.add(q)
	ok(not s.sell(q, h).ok, "quest item refused")
	# junk selling
	var junk := DB.make_item(&"copper_ring", BH.Rarity.COMMON, 1, 5)
	junk.junk = true
	h.inventory.add(junk)
	ok(s.sell_junk(h) > 0, "junk sold")
	ok(h.inventory.index_of(junk) < 0, "junk gone")
	done()

func test_specials_and_persistence() -> void:
	var h := _hero(&"knight", 100000)
	var def := DB.shop(&"brannoc_forge")
	h.progress.add_xp(XpCurve.total_xp_for_level(9))
	var s := Shop.open(def, h)
	ok(not s._has_special("brannoc_guardian_helm"), "special gated by world flag")
	h.world_flags[&"catacombs_ritual_seen"] = true
	s = Shop.open(def, h)
	ok(s._has_special("brannoc_guardian_helm"), "special appears once the flag is set")
	var idx := -1
	for i in s.stock.size():
		if s.stock[i].special == "brannoc_guardian_helm":
			idx = i
	var helm: ItemInstance = s.stock[idx].item
	eq(helm.rarity, BH.Rarity.MASTER, "special rarity")
	ok(s.buy(idx, h).ok, "bought the special")
	ok(not s._has_special("brannoc_guardian_helm"), "special gone after purchase")
	h.play_time += 100000.0
	s = Shop.open(def, h)
	ok(not s._has_special("brannoc_guardian_helm"), "specials never return after refresh")
	# full save round trip keeps the exact stock and buyback
	var sold: ItemInstance = null
	for c in h.inventory.cells:
		if c != null and c.base.id == &"health_potion":
			sold = c
	s.sell(sold, h)
	var before := JSON.stringify(s.to_dict())
	var h2 := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	var s2 := Shop.open(def, h2)
	eq(JSON.stringify(s2.to_dict()), before, "shop state round-trips through a save")
	done()

func test_dialogue_reacts_to_world() -> void:
	var h := _hero()
	var maelis := DB.npc(&"maelis")
	var d := Dialogue.new(maelis.id, maelis.graph)
	eq(d.entry_node(h), "orders", "first meeting begins the Wyman errand")
	h.world_flags[&"mq_maelis_orders"] = true
	eq(d.entry_node(h), "hub", "afterwards the hub")
	h.world_flags[&"catacombs_ritual_seen"] = true
	eq(d.entry_node(h), "ritual", "reacts to the catacombs")
	h.mark_dialogue_visited(&"maelis", "ritual")
	h.world_flags[&"boss_warden_defeated"] = true
	eq(d.entry_node(h), "warden_fallen", "Warden defeated line only after the kill")
	# branch resolution
	var h2 := _hero()
	eq(d.resolve("advice", h2), "advice_forest", "advice points to the forest first")
	h2.world_flags[&"catacombs_ritual_seen"] = true
	eq(d.resolve("advice", h2), "advice_temple", "then the temple")
	h2.world_flags[&"temple_seal_broken"] = true
	eq(d.resolve("advice", h2), "advice_throne", "then the throne")
	# conditional choice visibility
	var hub := d.node("hub")
	var vis := d.choices(hub, h2).map(func(c): return c.text)
	ok(not vis.has("The Warden is dead. What now?"), "Warden choice hidden before the kill")
	h2.world_flags[&"boss_warden_defeated"] = true
	vis = d.choices(hub, h2).map(func(c): return c.text)
	ok(vis.has("The Warden is dead. What now?"), "Warden choice shown after the kill")
	done()

func test_dialogue_session_flow() -> void:
	var h := _hero()
	var potions := h.inventory.count_of(&"health_potion")
	var s := DialogueSession.start(DB.npc(&"maelis"), h)
	var shown := []
	var offered := []
	s.line_shown.connect(func(_sp, _po, text, _i, _n): shown.append(text))
	s.choices_shown.connect(func(c): offered.append(c))
	s.begin()
	eq(shown.size(), 1, "first line shown")
	ok(String(shown[0]).find("waypoint") >= 0, "opening line")
	eq(h.inventory.count_of(&"health_potion"), potions + 3, "gift on first meeting")
	eq(h.relationship(&"maelis"), 5, "relationship raised")
	s.advance()
	s.advance()
	s.advance()
	eq(shown.size(), 4, "four opening lines")
	ok(String(shown[1]).find("[color=") >= 0, "important words highlighted")
	eq(offered.size(), 1, "choices offered after the last line")
	s.choose(0)  # reliquary
	ok(String(shown[4]).find("warm") >= 0, "reliquary clue")
	s.advance()
	s.advance()  # -> hub (next)
	eq(s.node_id, "hub", "back at the hub")
	var n_choices: int = s.choices.size()
	s.choose(n_choices - 1)  # farewell
	ok(s.finished, "ended")
	# the gift is not given twice
	var s2 := DialogueSession.start(DB.npc(&"maelis"), h)
	s2.begin()
	eq(s2.node_id, "hub", "second talk starts at the hub")
	eq(h.inventory.count_of(&"health_potion"), potions + 3, "no second gift")
	# shop requests reach the listener
	var req := []
	var t := DialogueSession.start(DB.npc(&"tovin"), h)
	t.request.connect(func(k, a): req.append([k, a]))
	t.begin()
	t.choose(0)
	eq(req, [[&"open_shop", &"tovin_goods"]], "open shop request")
	ok(t.finished, "dialogue closes when the shop opens")
	# a disabled/hidden choice cannot be forced
	var m := DialogueSession.start(DB.npc(&"maelis"), h)
	m.begin()
	var before_node := m.node_id
	m.choose(99)
	eq(m.node_id, before_node, "invalid choice ignored")
	done()

func test_respec_service() -> void:
	var h := _hero(&"knight", 0)
	h.progress.add_xp(XpCurve.total_xp_for_level(6))
	var sp := h.progress.skill_points
	var tp := h.progress.talent_points
	var spent_s := 0
	for n in h.skill_tree.tree.nodes:
		if h.progress.skill_points > 0 and h.spend_skill_point(n.id) == "":
			spent_s += 1
	var spent_t := 0
	for n in h.talent_tree.tree.nodes:
		if h.progress.talent_points > 0 and h.spend_talent_point(n.id) == "":
			spent_t += 1
	ok(spent_s > 0 and spent_t > 0, "spent points (%d skill, %d talent)" % [spent_s, spent_t])
	var stats_before_talents := h.compute_stats().get_stat(&"max_hp")
	eq(NpcServices.respec(h), "Not enough gold (%d needed)" % NpcServices.respec_cost(h.progress.level), "costs gold")
	h.inventory.gold = NpcServices.respec_cost(h.progress.level)
	eq(NpcServices.respec(h), "", "respec done")
	eq(h.inventory.gold, 0, "paid exactly")
	eq(h.progress.skill_points, sp, "every skill point back")
	eq(h.progress.talent_points, tp, "every talent point back")
	for s in h.cls.starting_skills:
		eq(h.skill_rank(s), 1, "starting skill kept")
		ok(h.skill_bar.has(s), "starting skill stays on the bar")
	eq(h.talent_tree.points_spent(), 0, "talents cleared")
	var fresh := _hero()
	fresh.progress.add_xp(XpCurve.total_xp_for_level(6))
	eq(h.compute_stats().get_stat(&"max_hp"), fresh.compute_stats().get_stat(&"max_hp"), "stats equal an unspent hero")
	ok(stats_before_talents >= 0.0, "sanity")
	eq(NpcServices.respec(h), "Nothing to unweave", "second respec refused")
	done()

func test_hero_npc_state_round_trip() -> void:
	var h := _hero()
	h.difficulty = 2
	h.mark_dialogue_visited(&"hald", "first")
	h.add_relationship(&"hald", -250)
	h.npc(&"tovin")["gift_given"] = true
	var h2 := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(h2.difficulty, 2, "difficulty")
	ok(h2.dialogue_visited(&"hald", "first"), "visited node")
	eq(h2.relationship(&"hald"), HeroData.REL_MIN, "relationship clamped and kept")
	eq(h2.npc(&"tovin").get("gift_given", false), true, "npc state")
	eq(JSON.stringify(h2.to_dict()), JSON.stringify(h.to_dict()), "exact round trip")
	done()

func test_npcs_placed_in_sanctuary() -> void:
	var prev := Game.hero
	Game.hero = _hero()
	var m := Game.build_map(&"sanctuary")
	host.add_child(m)
	await host.get_tree().physics_frame
	var placed := NpcDirectory.populate(m)
	eq(placed.size(), 8, "eight townspeople before the ritual, including Ysolde and Lape")
	for n in placed:
		var gy := NpcDirectory.ground_height(m, n.def.position)
		ok(absf(n.global_position.y - m.global_position.y - gy) < 0.05, "%s stands on the ground" % n.def.id)
		ok(n.global_position.y > m.global_position.y - 0.5 and n.global_position.y < m.global_position.y + 1.5, "%s height sane (%.2f)" % [n.def.id, n.global_position.y])
		ok(n.is_in_group(&"interactable"), "%s is interactable" % n.def.id)
		eq(n.interact_text(), "Talk to %s" % n.def.display_name, "%s prompt" % n.def.id)
	# NPCs keep clear of each other and of the fountain
	for a in placed:
		for b in placed:
			if a != b:
				ok(a.global_position.distance_to(b.global_position) > 3.0, "%s and %s apart" % [a.def.id, b.def.id])
	m.get_node("NPCs").queue_free()
	Game.hero.world_flags[&"catacombs_ritual_seen"] = true
	await host.get_tree().process_frame
	placed = NpcDirectory.populate(m)
	eq(placed.size(), 9, "the stranger arrives after the ritual")
	m.queue_free()
	Game.hero = prev
	done()
