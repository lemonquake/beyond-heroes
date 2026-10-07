extends TestCase
## bh-041: player trades that settle on the official server, the Debug sweep, Tempo commands (Aggro / Defend /
## Passive), the Eschaton tier and its catalogue, Lape's reworked trade, and windows that stay on the screen.

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _tree() -> SceneTree:
	return host.get_tree()

# ---- trades ----------------------------------------------------------------------------------------------------------

func test_an_official_trade_hands_the_server_the_exact_records() -> void:
	var sword := DB.make_item(&"iron_longsword", BH.Rarity.ELITE, 20, 5)
	var helm := DB.make_item(DB.item_bases.values().filter(func(b): return b.category == &"helm")[0].id, BH.Rarity.MASTER, 20, 6)
	var saved := [sword.to_dict(), null, helm.to_dict(), null]
	var coming := {"gold": 10, "items": [DB.make_item(&"iron_longsword", BH.Rarity.LEGENDARY, 30, 9).to_dict()]}
	coming.items[0]["locked"] = true
	var bag := Official.trade_bag(saved, [0], coming.items, 4)
	eq(bag.size(), 4, "the bag keeps its size")
	ok(bag[2] is Dictionary and JSON.stringify(bag[2], "", true) == JSON.stringify(helm.to_dict(), "", true), "an untouched cell is the very record that was saved")
	var arrived := bag.filter(func(c): return c is Dictionary and int(c.get("rarity", 0)) == BH.Rarity.LEGENDARY)
	eq(arrived.size(), 1, "the arriving item is placed once")
	ok(not (arrived[0] as Dictionary).has("locked"), "the sender's lock does not travel")
	eq(Official.trade_bag([sword.to_dict()], [], coming.items, 1).size(), 0, "no room without merging stacks: [] (the rules place them instead)")
	# what arrived over the network is kept exactly, for the server
	var wire := TradeRules.to_wire({"gold": 7, "items": [sword]})
	var read := TradeRules.read_incoming(wire)
	eq(JSON.stringify(read.wire, "", true), JSON.stringify(wire, "", true), "read_incoming keeps the offer exactly as it arrived")
	var broken := {"gold": 3, "items": [{"base": "no_such_item"}, sword.to_dict()]}
	eq((TradeRules.read_incoming(broken).wire.items as Array).size(), 1, "an unreadable item is left out of the kept record too")
	done()

func test_a_trade_in_progress_cannot_be_closed_from_one_side() -> void:
	var w := TradeWindow.new()
	host.add_child(w)
	Net.trade = {"peer": 9, "name": "Friend", "phase": "open", "mine": {"gold": 0, "items": []}, "theirs": {"gold": 0, "items": []},
		"rev": 0, "their_rev": 0, "my_ok": true, "their_ok": true, "committing": true, "their_ready": false, "sent": {}}
	w.close_window()
	ok(Net.in_trade(), "both accepted: closing the window does not call it off")
	Net.trade["committing"] = false
	Net.trade_reset("")
	w.free()
	ok(not Net.in_trade(), "reset")
	done()

func test_requests_have_their_own_box() -> void:
	var src := FileAccess.get_file_as_string("res://src/ui/ui_root.gd")
	ok(src.contains("request_box = ConfirmDialog.new()"), "UIRoot has a box for other players' requests")
	var net := FileAccess.get_file_as_string("res://src/net/net.gd")
	ok(net.contains("var box: ConfirmDialog = _request_box()"), "a Trade Request asks in it")
	ok(Net.PROTOCOL >= 22, "a new online version: older games cannot join (%d)" % Net.PROTOCOL)
	done()

# ---- the Debug sweep -------------------------------------------------------------------------------------------------

func test_debug_access_is_swept_once() -> void:
	var h := Game.new_hero(&"mage", "Sweep")
	h.debug_unlocked = true
	var d := h.to_dict()
	eq(int(d.debug_sweep), HeroData.DEBUG_SWEEP, "a save written now records the sweep")
	var old := d.duplicate(true)
	old.erase("debug_sweep")
	ok(not HeroData.from_dict(old).debug_unlocked, "a save from before the sweep loses its Debug console")
	ok(HeroData.from_dict(d).debug_unlocked, "unlocked again after the sweep: it stays unlocked")
	Game.god_mode = true
	Game.debug_one_hit = true
	Game.debug_freeze_ai = true
	Game.debug_damage_mult = 5.0
	Game.debug_min_drop = BH.Rarity.COSMIC
	Game.reset_debug()
	ok(not Game.god_mode and not Game.debug_one_hit and not Game.debug_freeze_ai and Game.debug_damage_mult == 1.0 and Game.debug_min_drop == -1,
		"every switch is back to normal")
	done()

# ---- Tempo commands --------------------------------------------------------------------------------------------------

func _begin() -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "freeze": Game.debug_freeze_ai}
	_holder = Node3D.new()
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Commander")
	Game.hero.progress.add_xp(XpCurve.total_xp_for_level(10))
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"start")
	_player.bind(Game.hero)
	for i in 2:
		await _tree().physics_frame

func _end() -> void:
	for t in TempoParty.actors(_tree()):
		t.free()
	for e in _tree().get_nodes_in_group(&"enemy"):
		e.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	Game.debug_freeze_ai = _saved.freeze
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

func test_tempo_command_rules_and_save() -> void:
	var h := Game.new_hero(&"ranger", "Orders")
	eq(h.tempo_command, &"defend", "Tempos defend until told otherwise")
	eq(TempoRules.cycle_command(h), &"passive", "Defend -> Passive")
	eq(TempoRules.cycle_command(h), &"aggro", "Passive -> Aggro")
	eq(TempoRules.cycle_command(h), &"defend", "Aggro -> Defend")
	TempoRules.set_command(h, &"aggro")
	eq(HeroData.from_dict(h.to_dict()).tempo_command, &"aggro", "the order is saved")
	var d := h.to_dict()
	d.erase("tempo_command")
	eq(HeroData.from_dict(d).tempo_command, &"defend", "an older save defends")
	d["tempo_command"] = "berserk"
	eq(HeroData.from_dict(d).tempo_command, &"defend", "an unknown order reads as Defend")
	ok(InputMap.has_action(&"tempo_command"), "a key steps through the orders")
	done()

func test_tempos_follow_their_orders() -> void:
	await _begin()
	Game.debug_freeze_ai = true          # the monster stands idle where it is put
	var t := TempoData.new()
	t.uid = 1
	t.tempo_name = "Order"
	t.class_id = DataTempos.class_ids()[0]
	t.trait_id = &"valiant"
	t.skills = [DataTempos.tempo_class(t.class_id).signature]
	Game.hero.tempos.append(t)
	TempoParty.refresh(Game.hero)
	for i in 2:
		await _tree().physics_frame
	var a := TempoParty.actor_for(t.uid)
	ok(a != null, "the Tempo stands beside the hero")
	if a == null:
		_end()
		done()
		return
	var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(&"hollow_soldier"), 10, [], _player.global_position + Vector3(9, 0, 0), DataEnemies.DIFFICULTY[1])
	for i in 2:
		await _tree().physics_frame
	ok(e != null and not e.is_aggressive(), "an idle monster 9 m away")
	Game.hero.tempo_command = &"defend"
	eq(a._choose_target(), null, "Defend: an idle monster is left alone while the hero is not fighting")
	Game.hero.tempo_command = &"aggro"
	eq(a._choose_target(), e, "Aggro: it is hunted")
	Game.hero.tempo_command = &"passive"
	e.last_attacker = a
	eq(a._choose_target(), null, "Passive: never a target, even one that fights it")
	Game.hero.tempo_command = &"defend"
	eq(a._choose_target(), e, "Defend: a monster that fights it is fought back")
	_end()
	done()

# ---- Eschaton --------------------------------------------------------------------------------------------------------

func test_eschaton_is_the_tier_past_primordial() -> void:
	eq(BH.Rarity.ESCHATON, 14, "the fifteenth tier")
	eq(BH.rarity_name(BH.Rarity.ESCHATON), "Eschaton", "its name")
	ok(DataAscendant.mult(BH.Rarity.ESCHATON) > DataAscendant.mult(BH.Rarity.PRIMORDIAL), "stronger than Primordial")
	ok(AscendantFx.has_look(BH.Rarity.ESCHATON), "its chrome light")
	ok(UIArt.rarity_frame(BH.Rarity.ESCHATON) != null and UIArt.rarity_glow(BH.Rarity.ESCHATON) != null, "its slot frame and glow")
	eq(DataGuilds.rank_for_rarity(BH.Rarity.ESCHATON), 8, "Class SSS to wear")
	eq(float(DataAscendant.TIER[BH.Rarity.ESCHATON].chance), 0.0, "no monster drops it")
	var r := rng(5)
	var esc := 0
	for i in 3000:
		var drop := DataAscendant.roll_drop(150, true, &"knight", 2.0, r)
		if drop and drop.rarity == BH.Rarity.ESCHATON:
			esc += 1
	eq(esc, 0, "3,000 dungeon lords of level 150: no Eschaton")
	ok(ItemGenerator.generate(DB.item_base(&"iron_longsword"), 120, BH.Rarity.ESCHATON, r).rarity == BH.Rarity.AETHER, "a plain base never becomes Eschaton")
	done()

func test_ten_of_everything_for_every_class() -> void:
	var by := {}
	for b: ItemBaseDef in DB.item_bases.values():
		if not DataEschaton.is_eschaton(b):
			continue
		var cls: StringName = b.class_hint
		var key := "%s/%s/%s" % [cls, b.category, b.weapon_type if b.is_weapon() else ""]
		by[key] = int(by.get(key, 0)) + 1
	for cls: StringName in DataEschaton.CLASSES:
		for cat in [&"helm", &"armor", &"inner_garment", &"leggings", &"gloves", &"boots"]:
			eq(int(by.get("%s/%s/" % [cls, cat], 0)), 10, "%s: ten Eschaton %s" % [cls, cat])
		for wt in DataEschaton.WEAPONS[cls]:
			eq(int(by.get("%s/weapon/%s" % [cls, wt], 0)), 10, "%s: ten Eschaton %s" % [cls, wt])
			ok(DB.class_def(cls).weapon_mastery.has(wt), "%s masters %s" % [cls, wt])
		eq(DB.class_def(cls).weapon_mastery.size(), (DataEschaton.WEAPONS[cls] as Array).size(), "%s: every weapon type it masters" % cls)
	eq(int(by.get("knight/shield/", 0)), 10, "knights: ten Eschaton shields")
	eq(int(by.get("/accessory/", 0)), 40, "forty jewels (any class may wear a jewel)")
	eq(DataEschaton.COLLECTIONS.size(), 40, "forty collections, ten per class")
	done()

func test_every_eschaton_piece_has_its_model_icon_and_power() -> void:
	var r := rng(9)
	var n := 0
	var names := {}
	for b: ItemBaseDef in DB.item_bases.values():
		if not DataEschaton.is_eschaton(b):
			continue
		n += 1
		ok(not names.has(b.display_name), "%s has its own name" % b.display_name)
		names[b.display_name] = true
		ok(ResourceLoader.exists(b.model), "%s model" % b.id)
		ok(ResourceLoader.exists(b.icon), "%s icon" % b.id)
		if b.category in [&"gloves", &"boots"]:
			ok(ResourceLoader.exists(b.model.get_basename() + "_R.glb"), "%s right-side model" % b.id)
		ok(b.boss_exclusive and b.drop_weight == 0, "%s never enters ordinary loot" % b.id)
		if n % 7 == 0:
			var it := DB.make_item(b.id, BH.Rarity.COMMON, 120, r.randi())
			eq(it.rarity, BH.Rarity.ESCHATON, "%s is Eschaton" % b.id)
			ok(it.powers.has("esc_unmaking"), "%s carries Unmaking" % b.id)
			ok(it.affixes.size() >= 8, "%s carries eight enchantments (%d)" % [b.id, it.affixes.size()])
			var back := ItemInstance.from_dict(it.to_dict())
			eq(back.rarity, BH.Rarity.ESCHATON, "the tier survives a save")
	eq(n, 470, "470 Eschaton pieces (290 armour and jewels, 180 weapons)")
	done()

# ---- Lape ------------------------------------------------------------------------------------------------------------

func _lape_hero(cls := &"mage", lvl := 120) -> HeroData:
	var h := Game.new_hero(cls, "Lot")
	h.progress.add_xp(XpCurve.total_xp_for_level(lvl))
	h.inventory.gold = 50000000
	return h

func _asc(rarity: int, cls := &"mage", seed_v := 1) -> ItemInstance:
	return DataAscendant.roll_drop(110, false, cls, 0.0, rng(seed_v), rarity)

func test_the_last_work_follows_the_lot() -> void:
	var p := [_asc(BH.Rarity.PRIMORDIAL, &"mage", 1), _asc(BH.Rarity.PRIMORDIAL, &"mage", 2), _asc(BH.Rarity.PRIMORDIAL, &"mage", 3)]
	var c := [_asc(BH.Rarity.COSMIC, &"mage", 4), _asc(BH.Rarity.COSMIC, &"mage", 5), _asc(BH.Rarity.COSMIC, &"mage", 6)]
	ok(LapeTrade.eschaton_chance(p) > 0.5, "three Primordial pieces: more likely than not (%.2f)" % LapeTrade.eschaton_chance(p))
	ok(LapeTrade.eschaton_chance(c) < LapeTrade.eschaton_chance(p) and LapeTrade.eschaton_chance(c) > 0.05, "three Cosmic: a chance (%.2f)" % LapeTrade.eschaton_chance(c))
	eq(LapeTrade.eschaton_chance([DB.make_item(&"iron_longsword", BH.Rarity.MASTER, 20, 1)]), 0.0, "ordinary gear: never")
	# across many draws of the same Primordial lot the last work appears about as often as promised, always for the class
	var h := _lape_hero()
	for it in p:
		h.inventory.add(it)
	var seen := 0
	var a := LapeTrade.appraise(h, p)
	for d in 60:
		var ap := LapeTrade.appraise(h, p, d)
		if ap.eschaton:
			seen += 1
			var at: int = (ap.kinds as Array).find(&"eschaton")
			var e: ItemInstance = ap.offers[at]
			eq(e.rarity, BH.Rarity.ESCHATON, "an Eschaton offer is Eschaton")
			ok(e.base.category == &"accessory" or ItemGenerator.class_fit(e.base, &"mage"), "%s is mage gear" % e.base.display_name)
	ok(seen > 20 and seen < 55, "the last work came %d times in 60 draws (about 63%%)" % seen)
	# the same draw is the same offers; another draw is not
	var a2 := LapeTrade.appraise(h, [p[2], p[0], p[1]])
	eq((a2.offers as Array).map(func(x): return x.display_name()), (a.offers as Array).map(func(x): return x.display_name()), "the same lot, the same first look")
	done()

func test_offers_follow_the_lot_and_redraws_are_paid() -> void:
	var h := _lape_hero(&"knight", 60)
	var kinds_seen := {}
	var weapon_lot := []
	var r := rng(31)
	for i in 3:
		var b := ItemGenerator.random_base(r, 58, [&"weapon"], &"knight", 1.0)
		var it := ItemGenerator.generate(b, 58, BH.Rarity.LEGENDARY, r)
		weapon_lot.append(it)
		h.inventory.add(it)
	var weapons := 0
	var total := 0
	var a := LapeTrade.appraise(h, weapon_lot)
	ok(a.craft, "a good lot")
	ok((a.combos as Array).has(&"same_kind"), "Lape sees three of a kind")
	for d in 30:
		var ap := LapeTrade.appraise(h, weapon_lot, d)
		ok((ap.offers as Array).size() >= 3 and (ap.offers as Array).size() <= LapeTrade.MAX_OFFERS, "three to five offers")
		var has_weapon := false
		for i in (ap.offers as Array).size():
			var it: ItemInstance = ap.offers[i]
			kinds_seen[ap.kinds[i]] = true
			total += 1
			if it.base.category == &"weapon":
				weapons += 1
				has_weapon = true
		ok(has_weapon, "always a weapon on the table")
	ok(float(weapons) / float(total) > 0.5, "a lot of blades draws mostly blades (%d of %d)" % [weapons, total])
	ok(kinds_seen.has(&"reforged"), "a laid piece comes back reforged now and then")
	# a paid redraw
	var gold := h.inventory.gold
	var cost := LapeTrade.redraw_cost(a, 1)
	var re := LapeTrade.redraw(h, weapon_lot, a)
	ok(re.ok, "Lape looks again")
	eq(h.inventory.gold, gold - cost, "for %d gold" % cost)
	eq(int(re.appraisal.draw), 1, "the second look")
	ok(LapeTrade.redraw_cost(re.appraisal, 2) > cost, "each look costs more")
	h.inventory.gold = 0
	ok(not LapeTrade.redraw(h, weapon_lot, re.appraisal).ok, "no gold, no second look")
	# taking an offer
	var pick: ItemInstance = re.appraisal.offers[0]
	var res := LapeTrade.accept(h, weapon_lot, re.appraisal, 0)
	ok(res.ok and h.inventory.index_of(pick) >= 0, "the chosen piece is in the bag")
	done()

func test_set_pieces_are_mended() -> void:
	var h := _lape_hero(&"knight", 110)
	var row: Array = DataAscendant.COLLECTIONS.filter(func(x): return x[3] == &"knight" and x[1] == BH.Rarity.ETERNAL)[0]
	var lot := []
	for piece in ["helm", "armor"]:
		var it := DB.make_item(DataAscendant.piece_id(StringName(row[0]), piece), BH.Rarity.COMMON, 110, lot.size() + 3)
		lot.append(it)
		h.inventory.add(it)
	var mended := 0
	for d in 20:
		var ap := LapeTrade.appraise(h, lot, d)
		var at: int = (ap.kinds as Array).find(&"mended")
		if at >= 0:
			mended += 1
			var it: ItemInstance = ap.offers[at]
			eq(it.base.set_id, StringName(row[0]), "the mended piece is of the same collection")
			ok(not [&"helm", &"armor"].has(it.base.category), "and one that was not laid down")
	ok(mended >= 5, "two pieces of one collection: Lape offers the missing ones (%d of 20 looks)" % mended)
	done()

func test_lape_has_words_for_the_new_ways() -> void:
	for k in [&"same_kind", &"same_set", &"element", &"ascendant", &"fabled", &"socketed", &"mixed", &"omen"]:
		ok((DataLapeLines.COMBO[k] as Array).size() >= 2, "remarks on a %s lot" % k)
	for k in [&"crafted", &"reforged", &"mended", &"fabled", &"ascendant", &"hoard", &"eschaton"]:
		ok(DataLapeLines.OFFER_KIND.has(k), "a label for %s offers" % k)
	ok(DataLapeLines.ESCHATON_REVEAL.size() >= 4 and DataLapeLines.REDRAW.size() >= 4 and DataLapeLines.AFTER_ESCHATON.size() >= 3, "the last work has its words")
	done()

func test_the_reveal_plays_and_finishes() -> void:
	var it := DB.make_item(DataEschaton.weapon_id(&"mage", &"staff", 0), BH.Rarity.COMMON, 120, 3)
	var holder := Control.new()
	holder.size = Vector2(1920, 1080)
	host.add_child(holder)
	var done_cb := [false]
	var rev := EschatonReveal.play(holder, it, func() -> void: done_cb[0] = true)
	for i in 30:
		await _tree().process_frame
	ok(is_instance_valid(rev), "the eclipse is open")
	rev._finish()
	await _tree().create_timer(0.8).timeout
	ok(done_cb[0], "it hands back to the table")
	holder.free()
	done()

# ---- windows on the screen ------------------------------------------------------------------------------------------

func test_windows_keep_their_content_inside() -> void:
	var src := FileAccess.get_file_as_string("res://src/ui/widgets/ui_window.gd")
	ok(src.contains("holder.clip_contents = true"), "a window's content cannot stretch it past the screen")
	for path in ["res://src/ui/windows/skills_window.gd", "res://src/ui/windows/talents_window.gd"]:
		ok(FileAccess.get_file_as_string(path).contains("_tabs = HFlowContainer.new()"), "%s: page tabs wrap" % path.get_file())
	ok(FileAccess.get_file_as_string("res://src/ui/widgets/tooltip_layer.gd").contains("static func fit_columns"), "tall tooltips flow into columns")
	# a card taller than the screen becomes columns that fit
	var card := PanelContainer.new()
	card.theme_type_variation = &"TooltipFrame"
	var v := VBoxContainer.new()
	card.add_child(v)
	for i in 60:
		var l := Label.new()
		l.text = "line %d" % i
		l.custom_minimum_size = Vector2(300, 30)
		v.add_child(l)
	host.add_child(card)
	await _tree().process_frame
	await _tree().process_frame
	card.reset_size()
	ok(card.size.y > 1500.0, "a 60-line card is %d px tall" % card.size.y)
	ok(TooltipLayer.fit_columns(card, 1000.0), "it is split")
	await _tree().process_frame
	card.reset_size()
	ok(card.size.y <= 1000.0, "now %d px tall" % card.size.y)
	card.free()
	done()
