extends TestCase
## bh-018: carry capacity doubled, the socketing system (32 crystals, Socket Specialists, add / remove / set / purge /
## crystallize), crystal drops and shops, dungeon gate aprons you can walk onto, and the redesigned trade quarters.

func _init() -> void:
	strict = true

func _hero(cls := &"knight", level := 20) -> HeroData:
	var h := Game.new_hero(cls, "Tester18")
	h.progress.level = level
	h.set_tier(DataGuilds.MAX_RANK)   # high-tier gear needs a ranked hero
	return h

func _gear(base: StringName, rarity: int, ilvl := 20) -> ItemInstance:
	var it := ItemGenerator.generate(DB.item_base(base), ilvl, rarity, rng(ilvl * 7 + rarity))
	it.sockets = 0
	it.gems.clear()
	it.powers.clear()   # keep rolled legendary powers out of the crystal arithmetic
	return it

func _crystal(id: StringName, n := 1) -> ItemInstance:
	var c := DB.make_item(id, BH.Rarity.COMMON, 1, 11)
	c.count = n
	return c

# ---- carry capacity -------------------------------------------------------------------------------------------------

func test_carry_capacity_is_doubled() -> void:
	eq(StatCalculator.CARRY_BASE, 220.0, "base capacity doubled again to 220")
	eq(StatCalculator.CARRY_PER_STR, 6.4, "6.4 per Strength")
	var h := _hero(&"knight", 1)
	var d := h.compute_stats()
	var strength := d.get_stat(&"str")
	near(d.get_stat(&"carry_capacity"), 2.0 * (110.0 + strength * 3.2), 0.01, "a new knight carries twice the previous capacity")
	eq(float(StatusRules.DEFS[&"elixir_feather"].mods[0][2]), 120.0, "the Featherweight Draught doubles too (+120)")
	done()

# ---- crystals -------------------------------------------------------------------------------------------------------

func test_thirty_two_crystals() -> void:
	var n := 0
	for f in DataCrystals.ORDER:
		for g in 4:
			var id := DataCrystals.id_of(f, g)
			var b := DB.item_base(id)
			ok(b != null, "%s exists" % id)
			if b == null:
				continue
			n += 1
			eq(b.category, &"crystal", "%s is a crystal" % id)
			ok(b.stack_max > 1, "%s stacks" % id)
			eq(b.display_name, "%s %s" % [DataCrystals.FAMILIES[f].name, DataCrystals.GRADE_NAMES[g]], "%s is named" % id)
			eq(DataCrystals.family_of(id), f, "%s family" % id)
			eq(DataCrystals.grade_of(id), g, "%s grade" % id)
			ok(DataCrystals.describe(id).size() >= 1, "%s says what it does" % id)
			var it := DB.make_item(id)
			eq(it.rarity, b.fixed_rarity, "%s keeps its grade's colour" % id)
	eq(n, 32, "8 families x 4 grades")
	eq(DataCrystals.price(&"ember_fragment"), 5000, "the lowest tier costs 5,000 gold")
	ok(DataCrystals.price(&"ember_orbital") > DataCrystals.price(&"ember_crystalline"), "higher grades cost more")
	ok(DataCrystals.price(&"aetherift_fragment") > DataCrystals.price(&"ember_fragment"), "Aetherift costs more")
	for grp in [DataCrystals.WEAPON, DataCrystals.ARMOR, DataCrystals.JEWEL]:
		var pv: Array = DataCrystals.FAMILIES[&"aetherift"].passive[grp]
		for g in 4:
			var t := DataCrystals.passive_text(pv, g)
			ok(not t.contains("%s") and t.length() > 20, "Aetherift %s passive reads: %s" % [grp, t])
	ok(not DataCrystals.is_crystal(&"aether_shard") and not DataCrystals.is_crystal(&"frost_crystal"), "old materials are not crystals")
	done()

func test_crystal_effects_depend_on_the_gear() -> void:
	var w := DataCrystals.mods(&"ember_shard", &"weapon")
	var a := DataCrystals.mods(&"ember_shard", &"armor")
	var j := DataCrystals.mods(&"ember_shard", &"accessory")
	ok(w.size() > 0 and w[0].stat == &"added_fire", "Ember in a weapon adds fire damage")
	ok(a.size() > 0 and a[0].stat == &"res_fire", "Ember in armour resists fire")
	ok(j.size() > 0 and j[0].stat == &"dmg_fire", "Ember in jewellery raises fire damage")
	ok(DataCrystals.mods(&"bloodrift_orbital", &"helm").is_empty(), "Bloodrift gives nothing outside weapons")
	ok(DataCrystals.weapon_only(&"bloodrift") and DataCrystals.weapon_only(&"essencerift"), "the two rifts are weapons only")
	var stats: Array = DataCrystals.mods(&"ember_fragment", &"weapon")
	var stats4: Array = DataCrystals.mods(&"ember_orbital", &"weapon")
	ok(float(stats4[0].value) > float(stats[0].value) * 5.0, "an Orbital is far stronger than a Fragment")
	# Aetherift carries a rare passive in every kind of gear
	for cat in [&"weapon", &"armor", &"accessory"]:
		var found := false
		for m in DataCrystals.mods(&"aetherift_shard", cat):
			if String(m.stat).begins_with("flag_"):
				found = true
		ok(found, "Aetherift in %s grants a passive" % cat)
	done()

func test_max_sockets_follow_the_tier() -> void:
	var want := {BH.Rarity.BEGINNER: 1, BH.Rarity.COMMON: 1, BH.Rarity.BASIC: 2, BH.Rarity.ADVANCED: 3, BH.Rarity.ELITE: 4,
		BH.Rarity.MASTER: 5, BH.Rarity.MYTHICAL: 6, BH.Rarity.AETHER: 7}
	for r in want:
		var it := _gear(&"iron_longsword", r)
		it.rarity = r
		eq(Sockets.max_sockets(it), want[r], "%s: %d sockets at most" % [BH.rarity_name(r), want[r]])
	eq(Sockets.max_sockets(_crystal(&"ember_fragment")), 0, "a crystal has no sockets")
	done()

# ---- the Specialist's services ------------------------------------------------------------------------------------

func test_add_sockets_up_to_the_maximum() -> void:
	var h := _hero()
	h.inventory.gold = 10_000_000
	var it := _gear(&"iron_hauberk", BH.Rarity.ELITE)
	h.inventory.add(it)
	var fees := []
	for i in 4:
		var fee := Sockets.add_fee(it)
		var g0 := h.inventory.gold
		var r := Sockets.apply(h, it, Sockets.ADD)
		ok(r.ok, "socket %d opens" % (i + 1))
		eq(g0 - h.inventory.gold, fee, "socket %d costs exactly its fee" % (i + 1))
		fees.append(fee)
	eq(it.sockets, 4, "four sockets on an Elite piece")
	eq(it.gems.size(), 4, "one slot per socket")
	ok(fees[3] > fees[0] * 4, "every socket costs more than the last (%s)" % str(fees))
	var r2 := Sockets.apply(h, it, Sockets.ADD)
	ok(not r2.ok, "no fifth socket on an Elite piece")
	var poor := _hero()
	var it2 := _gear(&"iron_hauberk", BH.Rarity.ELITE)
	poor.inventory.add(it2)
	poor.inventory.gold = 10
	ok(not Sockets.apply(poor, it2, Sockets.ADD).ok, "no gold, no socket")
	eq(it2.sockets, 0, "nothing changed")
	done()

func test_set_crystals_and_stats() -> void:
	var h := _hero()
	h.inventory.gold = 1_000_000
	var sword := _gear(&"iron_longsword", BH.Rarity.MASTER, 1)
	h.inventory.add(sword)
	var err := h.equip_from_inventory(sword, &"main_weapon")
	ok(h.equipment.get_item(&"main_weapon") == sword, "the sword is worn (%s)" % err)
	ok(not Sockets.set_crystal(h, sword, _crystal(&"ember_shard")).ok, "a crystal not in the bag cannot be set")
	var stack := _crystal(&"ember_shard", 3)
	h.inventory.add(stack)
	ok(not Sockets.set_crystal(h, sword, stack).ok, "no socket, no crystal")
	Sockets.apply(h, sword, Sockets.ADD)
	Sockets.apply(h, sword, Sockets.ADD)
	var before := h.compute_stats().get_stat(&"added_fire")
	var r := Sockets.set_crystal(h, sword, stack)
	ok(r.ok, "an Ember Shard is set")
	eq(stack.count, 2, "one crystal left the stack")
	eq(String(sword.gems[0]), "ember_shard", "it sits in the first socket")
	near(h.compute_stats().get_stat(&"added_fire") - before, 10.0, 0.01, "the worn sword now adds 10 fire damage")
	# a bloodrift into armour is refused, into the sword accepted
	var helm := _gear(&"iron_helm", BH.Rarity.BASIC, 1)
	h.inventory.add(helm)
	Sockets.apply(h, helm, Sockets.ADD)
	var blood := _crystal(&"bloodrift_fragment")
	h.inventory.add(blood)
	ok(not Sockets.set_crystal(h, helm, blood).ok, "Bloodrift does not fit a helm")
	ok(Sockets.set_crystal(h, sword, blood).ok, "Bloodrift fits the sword")
	ok(h.compute_stats().get_stat(&"life_leech") >= 0.01, "and the sword now drinks life")
	eq(h.inventory.count_of(&"bloodrift_fragment"), 0, "the last Bloodrift left the bag")
	ok(not Sockets.set_crystal(h, sword, stack).ok, "both sockets are full")
	done()

func test_remove_socket_only_when_empty() -> void:
	var h := _hero()
	h.inventory.gold = 1_000_000
	var it := _gear(&"silver_ring", BH.Rarity.BASIC)
	h.inventory.add(it)
	ok(not Sockets.apply(h, it, Sockets.REMOVE).ok, "no socket to close")
	Sockets.apply(h, it, Sockets.ADD)
	Sockets.apply(h, it, Sockets.ADD)
	var c := _crystal(&"nova_fragment")
	h.inventory.add(c)
	Sockets.set_crystal(h, it, c)
	ok(Sockets.apply(h, it, Sockets.REMOVE).ok, "the empty second socket closes")
	eq(it.sockets, 1, "one socket left")
	eq(String(it.gems[0]), "nova_fragment", "the crystal stays in its socket")
	ok(not Sockets.apply(h, it, Sockets.REMOVE).ok, "a socket holding a crystal does not close")
	done()

func test_purge_destroys_the_crystals() -> void:
	var h := _hero()
	h.inventory.gold = 1_000_000
	var it := _gear(&"iron_hauberk", BH.Rarity.ADVANCED)
	h.inventory.add(it)
	for i in 3:
		Sockets.apply(h, it, Sockets.ADD)
	for id in [&"aqua_shard", &"vipera_fragment"]:
		var c := _crystal(id)
		h.inventory.add(c)
		Sockets.set_crystal(h, it, c)
	var fee := Sockets.purge_fee(it)
	var g0 := h.inventory.gold
	var r := Sockets.apply(h, it, Sockets.PURGE)
	ok(r.ok, "purged")
	eq(g0 - h.inventory.gold, fee, "the fee is taken once")
	eq(Sockets.filled(it), 0, "no crystal left in it")
	eq(it.sockets, 3, "the sockets stay")
	eq(h.inventory.count_of(&"aqua_shard") + h.inventory.count_of(&"vipera_fragment"), 0, "the crystals are gone, not returned")
	ok(h.inventory.index_of(it) >= 0, "the piece is kept")
	ok(not Sockets.apply(h, it, Sockets.PURGE).ok, "nothing left to purge")
	done()

func test_crystallization_keeps_the_crystals() -> void:
	var h := _hero()
	h.inventory.gold = 1_000_000
	var it := _gear(&"iron_longsword", BH.Rarity.ELITE, 1)
	h.inventory.add(it)
	h.equip_from_inventory(it, &"main_weapon")
	for i in 3:
		Sockets.apply(h, it, Sockets.ADD)
	for id in [&"ember_crystalline", &"thundra_shard", &"ember_crystalline"]:
		var c := _crystal(id)
		h.inventory.add(c)
		Sockets.set_crystal(h, it, c)
	it.locked = true
	ok(not Sockets.apply(h, it, Sockets.CRYSTALLIZE).ok, "a locked piece is not ground up")
	it.locked = false
	var fee := Sockets.crystallize_fee(it)
	eq(fee, roundi((45000 * 2 + 15000) * 0.1), "a tenth of the crystals' worth")
	var g0 := h.inventory.gold
	var r := Sockets.apply(h, it, Sockets.CRYSTALLIZE)
	ok(r.ok, "crystallized")
	eq(g0 - h.inventory.gold, fee, "the fee is taken once")
	ok(h.equipment.get_item(&"main_weapon") == null, "the worn sword is gone from the hand")
	ok(h.inventory.index_of(it) < 0, "and not in the bag either")
	eq(h.inventory.count_of(&"ember_crystalline"), 2, "both Ember Crystallines came back")
	eq(h.inventory.count_of(&"thundra_shard"), 1, "the Thundra Shard came back")
	done()

func test_check_messages_are_plain() -> void:
	var h := _hero()
	var it := _gear(&"iron_helm", BH.Rarity.COMMON)
	ok(Sockets.check(h, it, Sockets.ADD).contains("not with you"), "a piece the hero does not have")
	h.inventory.add(it)
	h.inventory.gold = 0
	ok(Sockets.check(h, it, Sockets.ADD).begins_with("Not enough gold"), "no gold")
	ok(Sockets.check(h, it, Sockets.PURGE) != "", "no crystal to purge")
	done()

# ---- saves ---------------------------------------------------------------------------------------------------------

func test_sockets_survive_a_save() -> void:
	var it := _gear(&"iron_longsword", BH.Rarity.MASTER)
	it.sockets = 3
	it.gems = ["ember_orbital", "", "aetherift_fragment"]
	var back := ItemInstance.from_dict(JSON.parse_string(JSON.stringify(it.to_dict())))
	eq(back.sockets, 3, "three sockets after a save")
	eq(back.gems, ["ember_orbital", "", "aetherift_fragment"], "the crystals too")
	var plain := _gear(&"iron_longsword", BH.Rarity.MASTER)
	var pd := plain.to_dict()
	ok(not pd.has("sk") and not pd.has("gems"), "an unsocketed item writes no new keys")
	eq(ItemInstance.from_dict(pd).sockets, 0, "an old save loads with no sockets")
	var odd := it.to_dict()
	odd["gems"] = ["no_such_crystal", "ember_shard"]
	var ob := ItemInstance.from_dict(odd)
	eq(ob.gems, ["", "ember_shard", ""], "an unknown crystal becomes an empty socket; missing entries are empty")
	done()

# ---- combat -------------------------------------------------------------------------------------------------------

func test_vipera_poisons_on_hit() -> void:
	var h := _hero()
	var sword := _gear(&"iron_longsword", BH.Rarity.MASTER, 1)
	sword.sockets = 2
	sword.gems = ["vipera_orbital", "vipera_orbital"]
	h.inventory.add(sword)
	h.equip_from_inventory(sword, &"main_weapon")
	var atk := h.compute_stats()
	near(atk.get_stat(&"poison_on_hit"), 90.0, 0.01, "two Vipera Orbitals: 90 poison buildup a hit")
	var tgt := _hero(&"mage", 1).compute_stats()
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.attacker = atk
	req.target = tgt
	req.use_weapon = false
	req.base_min = 20.0
	req.base_max = 20.0
	req.evadable = false
	req.blockable = false
	req.can_crit = false
	var r := DamagePipeline.compute(req, rng(3))
	ok(r.total > 0, "the hit lands")
	ok(float(r.buildup.get(&"poisoned", 0.0)) >= 45.0, "and builds poison (%.1f)" % float(r.buildup.get(&"poisoned", 0.0)))
	done()

func test_aetherift_passives_reach_the_hero() -> void:
	var h := _hero()
	var ring := _gear(&"sigil_ring", BH.Rarity.AETHER)
	ring.sockets = 1
	ring.gems = ["aetherift_orbital"]
	h.inventory.add(ring)
	h.equip_from_inventory(ring, &"accessory_1")
	var d := h.compute_stats()
	ok(d.has_flag(&"crit_cdr"), "Rift Tempo is active")
	near(d.flag(&"crit_cdr"), 0.5, 0.001, "an Orbital cuts cooldowns by 0.5 s on a crit")
	ok(d.get_stat(&"skill_levels") >= 1.0, "an Aetherift Orbital in jewellery raises every skill")
	done()

# ---- drops and shops -----------------------------------------------------------------------------------------------

func test_bosses_and_champions_drop_crystals() -> void:
	var r := rng(99)
	var grades := [0, 0, 0, 0]
	var aether := 0
	for i in 4000:
		var id := DataCrystals.roll_drop(r, 30, true)
		if i < 3:
			ok(DataCrystals.is_crystal(id), "a boss drop is a crystal")
		grades[DataCrystals.grade_of(id)] += 1
		if DataCrystals.family_of(id) == &"aetherift":
			aether += 1
	ok(grades[3] > 0 and grades[2] > 0, "bosses can drop Crystallines and Orbitals (%s)" % str(grades))
	ok(aether > 40 and aether < 400, "Aetherift is rare (%d of 4000)" % aether)
	var mini := [0, 0, 0, 0]
	for i in 2000:
		mini[DataCrystals.grade_of(DataCrystals.roll_drop(r, 20, false))] += 1
	ok(mini[2] == 0 and mini[3] == 0, "champions drop only Fragments and Shards (%s)" % str(mini))
	ok(mini[0] > 0 and mini[1] > 0, "both of them")
	# the drop code itself: every boss and every miniboss adds a crystal
	var src := FileAccess.get_file_as_string("res://src/autoload/loot.gd")
	ok(src.contains("if e.is_boss or e.is_miniboss():") and src.contains("DataCrystals.roll_drop"), "Loot.drop_for always adds a crystal for bosses and champions")
	done()

func test_specialists_in_every_town() -> void:
	var seen := {}
	for id in [&"ysolde", &"anselm", &"dagna"]:
		var n := DB.npc(id)
		ok(n != null, "%s exists" % id)
		if n == null:
			continue
		seen[n.map] = true
		ok(n.services.has(&"socketing"), "%s works on sockets" % id)
		var sh := DB.shop(n.shop)
		ok(sh != null, "%s sells crystals" % id)
		ok(ResourceLoader.exists(n.portrait), "%s has a portrait" % id)
		var st := DataTownRows.stand_of_npc(id)
		ok(not st.is_empty(), "%s has a stand" % id)
		if sh:
			var frag: Dictionary = {}
			for f in sh.fixed:
				if f.base == &"ember_fragment":
					frag = f
			ok(not frag.is_empty(), "%s sells Ember Fragments" % id)
			var it := DB.make_item(&"ember_fragment")
			eq(ShopPricing.buy_price(it, sh), 5000, "%s: 5,000 gold for a Fragment" % id)
	for m in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		ok(seen.has(m), "a Socket Specialist in %s" % m)
	ok(DialogueBox.SERVICES.has(&"socketing"), "the dialogue service is known")
	done()

# ---- dungeon gates --------------------------------------------------------------------------------------------------

func test_gate_aprons_never_stand_above_the_dais() -> void:
	# the dungeon gate floor used to be raised by the ground height twice: a slab above the portal nobody could climb
	for map_id in [&"ruined_forest", &"olivar"]:
		var holder := Node3D.new()
		host.add_child(holder)
		var saved := Game.world_parent
		Game.world_parent = holder
		var m := Game.build_map(map_id)
		holder.add_child(m)
		await host.get_tree().physics_frame
		await host.get_tree().physics_frame
		var space := m.get_world_3d().direct_space_state
		for t in m.teleporters():
			if t.dungeon_gate == &"":
				continue
			var c := t.position
			for k in 8:
				var a := TAU * k / 8.0
				var p := c + Vector3(cos(a), 0, sin(a)) * 2.9
				var q := PhysicsRayQueryParameters3D.create(m.to_global(p + Vector3.UP * 3.0), m.to_global(p - Vector3.UP * 3.0), BH.LAYER_WORLD | BH.LAYER_GROUND)
				var hit := space.intersect_ray(q)
				if hit.is_empty():
					continue
				var top := m.to_local(hit.position).y
				ok(top <= c.y + 0.3, "%s gate %s: the floor at 2.9 m is not a pedestal (%.2f above the dais base)" % [map_id, t.teleporter_id, top - c.y])
		Game.world_parent = saved
		holder.free()
	done()

# ---- trade quarters ------------------------------------------------------------------------------------------------

func test_every_shopkeeper_has_their_own_stand() -> void:
	var models := {}
	for m in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		for s in DataTownRows.row(m).stands:
			if String(s.kind) != DataTownRows.SHOP:
				continue
			var model := String(s.get("model", ""))
			ok(model.begins_with("stand_"), "%s: %s has a stand model" % [m, s.npc])
			ok(not models.has(model), "%s's stand (%s) is unique" % [s.npc, model])
			models[model] = true
			ok(ResourceLoader.exists(MapBuilder.ENV_DIR % model), "%s is built" % model)
	ok(models.size() >= 12, "%d different shop stands" % models.size())
	done()

func test_older_games_cannot_join() -> void:
	ok(Net.PROTOCOL >= 6, "an older game would lose socketed items and crystals in a trade (protocol %d)" % Net.PROTOCOL)
	done()
