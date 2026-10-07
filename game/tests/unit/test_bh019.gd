extends TestCase
## bh-019: Lape the Ancient's special trade (appraisal, 300+ remarks, three licensed special-crafted offers or gold),
## practice dummies in every safe town, the Hero's Vault shared by every hero (32 -> 64 -> 128 slots), and four
## shopkeepers renamed (Anton, Greggy, Taicho, Angkol Les).

const TEST_VAULT := "user://saves/vault_unit_test.json"

func _init() -> void:
	strict = true

func _hero(cls := &"knight", level := 20) -> HeroData:
	var h := Game.new_hero(cls, "Tester19")
	h.progress.level = level
	h.set_tier(DataGuilds.MAX_RANK)
	return h

func _gear(cat: StringName, rarity: int, ilvl := 20, seed_value := 1) -> ItemInstance:
	var r := rng(seed_value)
	var b := ItemGenerator.random_base(r, ilvl, [cat], &"", 0.0)
	return ItemGenerator.generate(b, ilvl, rarity, r)

# ---- renamed shopkeepers ----------------------------------------------------------------------------------------------

func test_four_shopkeepers_renamed() -> void:
	eq(DB.npc(&"tovin").display_name, "Anton", "Malasugue's provisioner is Anton")
	eq(DB.npc(&"hobb").display_name, "Greggy", "Wyman's quartermaster is Greggy")
	eq(DB.npc(&"corvin").display_name, "Taicho", "Olivar's arms broker is Taicho")
	eq(DB.npc(&"aldous").display_name, "Angkol Les", "Olivar's alchemist is Angkol Les")
	eq(DB.shop(&"tovin_goods").display_name, "Anton's Provisions", "Anton's shop sign")
	eq(DB.shop(&"olivar_arms").display_name, "Taicho's Arms Exchange", "Taicho's shop sign")
	eq(DB.shop(&"olivar_alchemy").display_name, "Angkol Les' Apothecary", "Angkol Les' shop sign")
	# no old name is left in anything a player reads from these four
	for id in [&"tovin", &"hobb", &"corvin", &"aldous"]:
		var text := JSON.stringify(DB.npc(id).graph)
		for old in ["Tovin", "Hobb", "Corvin", "Ashby", "Aldous", "Pell"]:
			ok(not text.contains(old), "%s's dialogue no longer says %s" % [id, old])
	for m in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		for s in DataTownRows.row(m).stands:
			for old in ["Tovin", "Hobb", "Ashby", "Pell's"]:
				ok(not String(s.title).contains(old) and not String(s.get("label", "")).contains(old), "%s/%s sign has no '%s'" % [m, s.id, old])
	done()

# ---- Lape the Ancient -------------------------------------------------------------------------------------------------

func test_lape_has_more_than_three_hundred_remarks() -> void:
	var n := DataLapeLines.count()
	ok(n >= 300, "Lape has %d different lines (300+ asked)" % n)
	for k in [&"weapon", &"shield", &"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"accessory", &"crystal", &"consumable", &"material", &"other"]:
		ok((DataLapeLines.KIND[k] as Array).size() >= 5, "remarks on %s" % k)
	eq(DataLapeLines.TIER.size(), BH.RARITY_COUNT, "a remark set for every tier")
	eq(DataLapeLines.WORTH.size(), LapeTrade.VALUE_BANDS.size() + 1, "a remark set for every worth band")
	eq(DataLapeLines.OFFER.size(), BH.Rarity.ESCHATON - BH.Rarity.LICENSED + 1, "an offer line for every tier he can offer (bh-041: up to Eschaton)")
	done()

func test_lape_stands_in_malasugue() -> void:
	var npc := DB.npc(&"lape")
	ok(npc != null, "Lape exists")
	if npc == null:
		done()
		return
	eq(npc.display_name, "Lape the Ancient", "his name")
	eq(npc.map, &"sanctuary", "in Malasugue")
	ok(npc.services.has(&"lape_trade"), "he trades")
	ok(DialogueBox.SERVICES.has(&"lape_trade"), "the dialogue knows the service")
	var st := DataTownRows.stand_of_npc(&"lape")
	ok(not st.is_empty(), "he has a stand")
	eq(String(st.get("model", "")), "stand_lape", "his own stand model")
	ok(Vector2(npc.position.x - st.pos.x, npc.position.z - st.pos.z).length() < 3.0, "he stands at it")
	ok(ResourceLoader.exists(DataNpcsLape.PORTRAIT), "his portrait")
	var hub: Dictionary = npc.graph.nodes.hub
	var opens := false
	for c in hub.choices:
		for a in c.get("actions", []):
			if a.get("service", "") == "lape_trade":
				opens = true
	ok(opens, "his hub opens the trade")
	done()

func test_lape_appraises_and_refuses() -> void:
	var h := _hero()
	var sword := _gear(&"weapon", BH.Rarity.ELITE, 20, 3)
	var ring := _gear(&"accessory", BH.Rarity.ADVANCED, 20, 4)
	h.inventory.add(sword)
	h.inventory.add(ring)
	var a := LapeTrade.appraise(h, [sword, ring])
	eq(int(a.value), LapeTrade.item_value(sword) + LapeTrade.item_value(ring), "the lot is worth the sum of its items")
	ok(LapeTrade.item_value(sword) > sword.sell_value(), "Lape pays more than a merchant (%d > %d)" % [LapeTrade.item_value(sword), sword.sell_value()])
	eq((a.items as Array).size(), 2, "a verdict for each item")
	for e in a.items:
		ok((e.lines as PackedStringArray).size() >= 4, "several remarks on %s" % (e.item as ItemInstance).display_name())
		ok((e.facts as PackedStringArray).size() >= 1, "identified facts on %s" % (e.item as ItemInstance).display_name())
		for l in e.lines:
			ok(not String(l).contains("{"), "no unfilled placeholder: %s" % l)
	# the same lot draws the same words and the same offers
	var b := LapeTrade.appraise(h, [ring, sword])
	eq(Array(b.items[1].lines), Array(a.items[0].lines), "remarks are stable for an item")
	eq((b.offers as Array).size(), (a.offers as Array).size(), "same number of offers")
	for i in (a.offers as Array).size():
		eq((b.offers[i] as ItemInstance).display_name(), (a.offers[i] as ItemInstance).display_name(), "offer %d does not re-roll" % i)
	# refusals
	sword.locked = true
	ok(LapeTrade.refuse_reason(sword) != "", "a locked item is refused")
	sword.locked = false
	ok(LapeTrade.refuse_reason(sword) == "", "an unlocked one is accepted")
	# junk: gold only
	var h2 := _hero(&"mage", 30)
	var junk := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 1)
	h2.inventory.add(junk)
	var c := LapeTrade.appraise(h2, [junk])
	ok(not c.craft, "a single draught is not enough to craft with")
	eq((c.offers as Array).size(), 0, "no crafted offers for it")
	ok((c.summary as PackedStringArray).size() >= 1, "he says why")
	done()

func test_lape_offers_three_licensed_class_pieces() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := _hero(cls, 22)
		var lot := [_gear(&"weapon", BH.Rarity.ELITE, 22, 11), _gear(&"armor", BH.Rarity.ELITE, 22, 12), _gear(&"helm", BH.Rarity.MASTER, 22, 13)]
		for it in lot:
			h.inventory.add(it)
		var a := LapeTrade.appraise(h, lot)
		ok(a.craft, "%s: a good lot is crafted for" % cls)
		# bh-041: three to five offers of several kinds; the crafted ones are licensed class pieces near the lot's tier
		var count := (a.offers as Array).size()
		ok(count >= 3 and count <= LapeTrade.MAX_OFFERS, "%s: three to five offers (%d)" % [cls, count])
		eq(int(a.tier), BH.Rarity.MYTHICAL, "%s: three Elite-or-better pieces with a Master among them -> one tier up (Mythical)" % cls)
		var cats := {}
		for i in count:
			var it: ItemInstance = a.offers[i]
			if a.kinds[i] != &"crafted":
				cats[it.base.category] = true
				continue
			ok(it.license != &"", "%s: %s is licensed" % [cls, it.display_name()])
			ok(it.crafted, "%s: %s is special-crafted" % [cls, it.display_name()])
			ok(absi(it.rarity - int(a.tier)) <= 1, "%s: %s is within a tier of the lot's (%s)" % [cls, it.display_name(), it.rarity_name()])
			ok(it.ilvl >= 22 and it.ilvl <= 24, "%s: item level near the hero's (%d)" % [cls, it.ilvl])
			if it.base.category != &"accessory":
				ok(ItemGenerator.class_fit(it.base, cls), "%s: %s is %s gear" % [cls, it.base.display_name, cls])
			cats[it.base.category] = true
			var reqs := LapeTrade.requirements(h, it)
			ok(String(reqs[0][0]).begins_with("Licensed: "), "%s: the license is spelled out first" % cls)
			var has_wear := false
			for r in reqs:
				if String(r[0]).begins_with("You can wear it now") or String(r[0]).begins_with("Not yet wearable"):
					has_wear = true
			ok(has_wear, "%s: he says whether it can be worn now" % cls)
		ok(cats.has(&"weapon"), "%s: a weapon among the offers" % cls)
	# tier rules
	var h1 := _hero()
	eq(LapeTrade.craft_tier([_gear(&"weapon", BH.Rarity.COMMON)]), BH.Rarity.LICENSED, "anything worth crafting for gives at least Licensed")
	eq(LapeTrade.craft_tier([_gear(&"weapon", BH.Rarity.LEGENDARY), _gear(&"helm", BH.Rarity.LEGENDARY, 20, 2), _gear(&"boots", BH.Rarity.LEGENDARY, 20, 3)]),
		BH.Rarity.LEGENDARY, "never above Legendary without an Aether piece")
	eq(LapeTrade.craft_tier([_gear(&"weapon", BH.Rarity.AETHER)]), BH.Rarity.AETHER, "an Aether piece earns Aether offers")
	ok(h1 != null, "")
	done()

func test_lape_trade_closes() -> void:
	var h := _hero(&"ranger", 20)
	var lot := [_gear(&"weapon", BH.Rarity.MASTER, 20, 21), _gear(&"gloves", BH.Rarity.ELITE, 20, 22)]
	for it in lot:
		h.inventory.add(it)
	var a := LapeTrade.appraise(h, lot)
	var gold0 := h.inventory.gold
	var r := LapeTrade.accept(h, lot, a, -1)
	ok(r.ok, "gold taken")
	eq(h.inventory.gold, gold0 + int(a.value), "the appraised gold is paid")
	for it in lot:
		ok(h.inventory.index_of(it) < 0, "%s went to Lape" % it.display_name())
	var again := LapeTrade.accept(h, lot, a, -1)
	ok(not again.ok, "the same lot cannot be traded twice")
	# take a crafted piece
	var lot2 := [_gear(&"weapon", BH.Rarity.MASTER, 20, 31), _gear(&"armor", BH.Rarity.MASTER, 20, 32), _gear(&"helm", BH.Rarity.MASTER, 20, 33)]
	for it in lot2:
		h.inventory.add(it)
	var a2 := LapeTrade.appraise(h, lot2)
	var pick: ItemInstance = a2.offers[1]
	var g1 := h.inventory.gold
	var r2 := LapeTrade.accept(h, lot2, a2, 1)
	ok(r2.ok, "a crafted piece taken")
	ok(h.inventory.index_of(pick) >= 0, "it is in the bag")
	eq(h.inventory.gold, g1, "no gold on top")
	ok(String(r2.line) != "", "Lape has a word for it")
	ok(not LapeTrade.accept(h, [], a2, 0).ok, "nothing to trade")
	done()

# ---- the Hero's Vault -------------------------------------------------------------------------------------------------

func _fresh_vault() -> HeroVault:
	for f in [TEST_VAULT, TEST_VAULT + ".bak", TEST_VAULT + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var v := HeroVault.new()
	v.path = TEST_VAULT
	return v

func test_vault_starts_at_32_and_grows() -> void:
	var v := _fresh_vault()
	eq(v.capacity(), 32, "32 slots to start")
	var h := _hero()
	h.inventory.gold = 3000
	eq(v.next_cost(), 2500, "64 slots cost 2,500")
	eq(v.upgrade(h), "", "upgrade paid")
	eq(v.capacity(), 64, "64 slots")
	eq(h.inventory.gold, 500, "2,500 taken")
	ok(v.upgrade(h) != "", "8,000 is too much for 500 gold")
	eq(v.capacity(), 64, "still 64")
	h.inventory.gold = 8000
	eq(v.next_cost(), 8000, "128 slots cost 8,000")
	eq(v.upgrade(h), "", "upgrade paid")
	eq(v.capacity(), 128, "128 slots")
	eq(h.inventory.gold, 0, "8,000 taken")
	ok(v.upgrade(h) != "", "128 is the largest")
	eq(v.next_cost(), 0, "nothing further to buy")
	done()

func test_vault_deposit_withdraw_and_share() -> void:
	var v := _fresh_vault()
	var a := _hero(&"knight", 10)
	a.inventory.cells.fill(null)   # a new hero's starter draughts would swallow the stack below
	var sword := _gear(&"weapon", BH.Rarity.ELITE, 10, 41)
	a.inventory.add(sword)
	var pots := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 1)
	pots.count = 5
	a.inventory.add(pots)
	eq(v.deposit(a, sword), "", "sword stored")
	ok(a.inventory.index_of(sword) < 0, "it left the bag")
	eq(v.deposit(a, pots), "", "draughts stored")
	var more := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 1)
	more.count = 3
	a.inventory.add(more)
	eq(v.deposit(a, more), "", "more draughts stored")
	eq(v.used(), 2, "the draughts stacked (2 slots used)")
	ok(v.save(), "the vault saves")
	# another hero (another save slot) opens the same vault
	var loaded := HeroVault.load_from(TEST_VAULT)
	eq(loaded.used(), 2, "the second hero sees both")
	var b := _hero(&"mage", 12)
	b.inventory.cells.fill(null)
	var idx := -1
	for i in loaded.cells.size():
		if loaded.cells[i] != null and (loaded.cells[i] as ItemInstance).base.id == sword.base.id:
			idx = i
	ok(idx >= 0, "the sword is there")
	eq(loaded.withdraw(b, idx), "", "the mage takes it out")
	eq(b.inventory.count_of(sword.base.id), 1, "it is in the mage's bag")
	eq(loaded.used(), 1, "one slot left in use")
	# full vault
	var v2 := _fresh_vault()
	var c := _hero(&"ranger", 5)
	for i in 32:
		var it := _gear(&"boots", BH.Rarity.COMMON, 5, 100 + i)
		c.inventory.add(it)
		v2.deposit(c, it)
	eq(v2.used(), 32, "32 stored")
	var extra := _gear(&"boots", BH.Rarity.COMMON, 5, 999)
	c.inventory.add(extra)
	ok(v2.deposit(c, extra) != "", "the 33rd is refused")
	ok(c.inventory.index_of(extra) >= 0, "and stays in the bag")
	# quest items stay with their hero
	var q: ItemInstance = null
	for base in DB.item_bases.values():
		if base.is_quest():
			q = DB.make_item(base.id)
			break
	if q:
		ok(HeroVault.refuse_reason(q) != "", "quest items are refused")
	# probes and tests never touch the player's vault
	eq(HeroVault.path_for_slot(99), HeroVault.PROBE_PATH, "test slots use the probe vault")
	eq(HeroVault.path_for_slot(0), HeroVault.PATH, "real slots share the real vault")
	eq(HeroVault.path_for_slot(2), HeroVault.PATH, "every real slot shares it")
	_fresh_vault()
	done()

func test_vault_round_trip_keeps_positions_and_size() -> void:
	var v := _fresh_vault()
	var h := _hero()
	h.inventory.gold = 5000
	v.upgrade(h)
	var ring := _gear(&"accessory", BH.Rarity.LEGENDARY, 20, 51)
	ring.sockets = 1
	ring.gems = ["ember_shard"]
	h.inventory.add(ring)
	v.deposit(h, ring, 40)
	ok(v.cells[40] == ring, "placed in slot 41")
	ok(v.save(), "saved")
	var w := HeroVault.load_from(TEST_VAULT)
	eq(w.capacity(), 64, "the size is remembered")
	ok(w.cells[40] != null, "slot 41 is still filled")
	if w.cells[40]:
		eq((w.cells[40] as ItemInstance).display_name(), ring.display_name(), "same ring")
		eq(Array((w.cells[40] as ItemInstance).gems), ["ember_shard"], "its crystal too")
	# a broken file falls back to the backup
	v.save()
	var f := FileAccess.open(TEST_VAULT, FileAccess.WRITE)
	f.store_string("{ broken")
	f.close()
	var r := HeroVault.load_from(TEST_VAULT)
	eq(r.used(), 1, "restored from the backup")
	_fresh_vault()
	done()

# ---- practice dummies, vaults and Lape in the world ------------------------------------------------------------------

var _holder: Node3D
var _saved := {}
var _player: Player

func _begin(map_id: StringName) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "Bh019World"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Tester19")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, &"start")
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	for t in TempoParty.actors(host.get_tree()):
		t.free()
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

func test_every_safe_town_has_a_dummy_and_a_vault() -> void:
	for map_id in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		await _begin(map_id)
		var tree := host.get_tree()
		var dummies := tree.get_nodes_in_group(&"practice_target")
		eq(dummies.size(), 1, "%s: one practice dummy" % map_id)
		var vaults := tree.get_nodes_in_group(&"vault_point")
		eq(vaults.size(), 1, "%s: one vault" % map_id)
		if not vaults.is_empty():
			ok((vaults[0] as Node).is_in_group(&"interactable"), "%s: the vault can be opened" % map_id)
			eq(String((vaults[0] as VaultPoint).interact_text()), "Open the Vault", "%s: its prompt" % map_id)
		if not dummies.is_empty():
			var d := dummies[0] as PracticeDummy
			ok(not d.is_in_group(&"enemy"), "%s: the dummy is not a monster (Tempos and the minimap ignore it)" % map_id)
			eq(d.collision_layer, BH.LAYER_ENEMY, "%s: but attacks land on it" % map_id)
			ok(_player._aim_targets().has(d), "%s: the hero's auto-aim can pick it" % map_id)
			ok(ResourceLoader.exists(MapBuilder.ENV_DIR % PracticeDummy.MODEL), "the dummy model is built")
			# hit it hard, many times
			d.ensure_stats()
			var total := 0
			for i in 20:
				var req := DamageRequest.new()
				req.kind = DamageRequest.Kind.ATTACK
				req.attacker = _player.stats if _player.stats else DerivedStats.new()
				req.base_min = 1.0e6
				req.base_max = 1.0e6
				var r := d.receive_hit(req, _player)
				total += r.total
				d._t += 0.1
			ok(d.alive, "%s: it never dies" % map_id)
			near(d.hp, d.max_hp(), 1.0, "%s: it is whole again after every hit" % map_id)
			eq(d._bout_total, total, "%s: the board counts every point (%d)" % [map_id, total])
			eq(d._bout_hits, 20, "%s: and every hit" % map_id)
			ok(d.dps() > 0.0, "%s: a damage-per-second figure (%.0f)" % [map_id, d.dps()])
			ok(String(d._board.text).contains("damage per second"), "%s: shown on its board" % map_id)
			d._t += 10.0
			d._update_board()
			ok(String(d._board.text).contains("Attack it"), "%s: a quiet dummy invites you to try" % map_id)
		for k in ["stand_vault"] + (["stand_lape"] if map_id == &"sanctuary" else []):
			ok(ResourceLoader.exists(MapBuilder.ENV_DIR % k), "%s is built" % k)
		if map_id == &"sanctuary":
			var lape := false
			for n in tree.get_nodes_in_group(&"npc"):
				if n is Npc and (n as Npc).def.id == &"lape":
					lape = true
			ok(lape, "Lape stands in Malasugue")
		_end()
	done()

func test_windows_open() -> void:
	ok(Game.ui_root == null or Game.ui_root.window(&"lape") is LapeWindow, "Lape's window is registered")
	ok(Game.ui_root == null or Game.ui_root.window(&"vault") is VaultWindow, "the vault window is registered")
	done()
