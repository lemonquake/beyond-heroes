extends TestCase
## bh-016: every skill and talent goes to level 25 (the old cap keeps its old numbers; deeper levels taper off), the
## Guild House (two counters, job boards, paid miniquests that save with the hero), and the player trade (rules,
## atomic swap, the request state machine offline).

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _begin(map_id: StringName, spawn: StringName = &"start") -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "Bh016World"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Guilder")
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

func _hero(cls := &"knight", level := 1) -> HeroData:
	var h := Game.new_hero(cls, "Tester")
	h.progress.level = level
	return h

# ---- 25 levels ----------------------------------------------------------------------------------------------------

func test_main_nodes_reach_25_and_side_nodes_have_limits() -> void:
	var nodes := 0
	for id in [&"knight_skills", &"mage_skills", &"ranger_skills", &"shadowblade_skills", &"knight_talents", &"mage_talents", &"ranger_talents", &"shadowblade_talents"]:
		var t := DB.tree(id)
		ok(t != null, "tree %s exists" % id)
		if t == null:
			continue
		for n in t.nodes:
			nodes += 1
			var cap := 25
			if n.kind == "upgrade":
				cap = 1 if int(n.base_rank) <= 1 else 4
			elif n.kind in ["major", "keystone"]:
				cap = 1
			eq(int(n.max_rank), cap, "%s.%s tops out at level %d" % [id, n.id, cap])
			ok(int(n.base_rank) >= 1 and int(n.base_rank) <= TreeDef.LEVEL_MAX, "%s.%s has a valid authored cap (%s)" % [id, n.id, n.base_rank])
	ok(nodes > 150, "%d skill and talent nodes checked" % nodes)
	done()

func test_old_levels_keep_old_numbers() -> void:
	for r in range(0, 6):
		eq(TreeDef.rank_power(r, 5), float(r), "rank %d of a 5-rank node is unchanged" % r)
	for r in range(0, 4):
		eq(TreeDef.rank_power(r, 3), float(r), "rank %d of a 3-rank node is unchanged" % r)
	eq(TreeDef.rank_power(1, 1), 1.0, "a single-rank node at rank 1 is unchanged")
	var last := 0.0
	for r in range(0, 26):
		var p := TreeDef.rank_power(r, 5)
		ok(p >= last, "power never falls (%d)" % r)
		last = p
	near(TreeDef.rank_power(25, 5), 15.0, 0.001, "level 25 of a 5-rank node is worth 15 old ranks")
	near(TreeDef.rank_power(25, 1), 3.4, 0.001, "level 25 of a one-rank keystone is worth 3.4")
	# a real skill and a real talent
	var h := _hero()
	var cleave := DB.skill(&"cleave")
	near(float(cleave.resolve(3).weapon_pct), 150.0 + 18.0 * 2.0, 0.001, "Cleave rank 3 as before")
	near(float(cleave.resolve(5).weapon_pct), 150.0 + 18.0 * 4.0, 0.001, "Cleave rank 5 as before")
	ok(float(cleave.resolve(25).weapon_pct) > float(cleave.resolve(5).weapon_pct), "Cleave keeps growing to level 25")
	ok(float(cleave.resolve(25).weapon_pct) < 150.0 + 18.0 * 24.0, "...but slower than a straight line")
	near(cleave.mana_at(3), 4.0 + 0.5 * 2.0, 0.001, "mana cost at rank 3 as before")
	# what the extra 20 levels buy: a real gain, but nowhere near a straight line (which would be 3.5x here)
	var fb := DB.skill(&"firebolt")
	var avg5 := (float(fb.resolve(5).damage_min) + float(fb.resolve(5).damage_max)) * 0.5
	var avg25 := (float(fb.resolve(25).damage_min) + float(fb.resolve(25).damage_max)) * 0.5
	ok(avg25 / avg5 > 1.5 and avg25 / avg5 < 3.2, "Firebolt level 25 hits %.1fx as hard as level 5" % (avg25 / avg5))
	h.talent_tree.ranks[&"k_str"] = 3
	var m3 := h.talent_tree.modifiers()
	near(float(m3[0].value), 9.0, 0.001, "Might rank 3 = +9 Strength as before")
	h.talent_tree.ranks[&"k_str"] = 25
	near(float(h.talent_tree.modifiers()[0].value), 3.0 * TreeDef.rank_power(25, 3), 0.001, "Might level 25 = the tapered sum")
	done()

func test_levels_are_learned_and_saved() -> void:
	var h := _hero(&"knight", 60)
	h.progress.skill_points = 40
	h.progress.talent_points = 60
	for i in 24:
		eq(h.spend_skill_point(&"cleave"), "", "Cleave level %d (it starts at 1)" % (i + 2))
	eq(h.skill_rank(&"cleave"), 25, "Cleave is level 25")
	ok(h.spend_skill_point(&"cleave") != "", "there is no level 26")
	eq(h.progress.skill_points, 16, "24 points spent")
	for i in 25:
		eq(h.spend_talent_point(&"k_str"), "", "Might level %d" % (i + 1))
	ok(h.spend_talent_point(&"k_str") != "", "Might has no level 26")
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(back.skill_rank(&"cleave"), 25, "level 25 survives a save")
	eq(back.talent_tree.rank(&"k_str"), 25, "talent level 25 survives a save")
	eq(back.refund_skill_point(&"cleave"), "", "a level refunds")
	eq(back.skill_rank(&"cleave"), 24, "level 24 after the refund")
	# a value from a hand-edited save cannot pass 25
	var d := h.to_dict()
	d.skills.cleave = 99
	eq(HeroData.from_dict(d).skill_rank(&"cleave"), 25, "a hand-edited 99 is clamped to 25")
	done()

func test_level_25_stays_finite_everywhere() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := _hero(cls, 60)
		for n in h.skill_tree.tree.nodes:
			h.skill_tree.ranks[n.id] = 25
		for n in h.talent_tree.tree.nodes:
			h.talent_tree.ranks[n.id] = 25
		for sk in DB.skills.values():
			var s: SkillDef = sk
			if s.class_id != cls:
				continue
			var p: Dictionary = s.resolve(25, h.skill_upgrades(s.id))
			for k in p:
				if p[k] is float:
					ok(is_finite(p[k]), "%s.%s finite at 25" % [s.id, k])
			ok(s.mana_at(25) < 400.0, "%s mana at 25 is sane (%.0f)" % [s.id, s.mana_at(25)])
		for m in h.talent_tree.modifiers() + h.skill_tree.passive_modifiers():
			ok(is_finite(float(m.value)), "%s modifier finite" % m.stat)
	done()

# ---- Guild jobs -----------------------------------------------------------------------------------------------------

func test_job_templates_are_sound() -> void:
	var ids := {}
	for t in DataGuildJobs.TEMPLATES:
		ok(not ids.has(t.id), "%s is unique" % t.id)
		ids[t.id] = true
		ok(DataGuilds.GUILDS.has(StringName(t.guild)) or String(t.guild) == "open", "%s names a guild (or is an open posting, bh-027)" % t.id)
		ok(DataGuildJobs.KINDS.has(t.kind), "%s has a known kind" % t.id)
		ok(t.goal.x >= 1 and t.goal.y >= t.goal.x, "%s goal range" % t.id)
		ok(t.lvl.x >= 1 and t.lvl.y >= t.lvl.x, "%s level range" % t.id)
		ok(int(t.unit) > 0, "%s pays" % t.id)
		if t.kind in ["kill_map", "visit"]:
			ok(DB.map_def(StringName(t.map)) != null, "%s names a real map (%s)" % [t.id, t.get("map", "")])
		ok(not (String(t.text).contains("Filipino")), "%s text" % t.id)
	for g in [&"swordfin", &"lantern"]:
		ok(DataGuildJobs.for_guild(g).size() >= 8, "%s posts at least 8 kinds of work" % g)
		for lvl in [1, 5, 10, 25, 60]:
			var h := _hero(&"knight", lvl)
			eq(GuildJobs.refresh_board(h, g).size(), GuildJobs.BOARD_SIZE, "%s board is full at level %d" % [g, lvl])
	done()

func test_take_and_finish_a_job() -> void:
	var h := _hero(&"knight", 4)
	h.inventory.gold = 0
	var sb := GuildJobs.refresh_board(h, &"swordfin")
	var first: Dictionary = sb[0]
	# bh-027: the jobs are open to every hero, in a guild or not, whichever guild posted them
	eq(GuildJobs.accept_error(h, &"swordfin", int(first.id)), "", "jobs before joining a guild")
	h.inventory.gold = 500
	eq(GuildRules.join(h, &"swordfin"), "", "join Swordfin")
	h.inventory.gold = 0
	eq(GuildJobs.accept_error(h, &"lantern", int(GuildJobs.refresh_board(h, &"lantern")[0].id)), "", "a Swordfin hero may take Lantern work")
	eq(GuildJobs.accept(h, &"swordfin", int(first.id)), "", "take the first posting")
	eq(GuildJobs.active(h).size(), 1, "one job carried")
	eq(GuildJobs.board(h, &"swordfin").size(), GuildJobs.BOARD_SIZE, "the board is pinned back up")
	ok(not GuildJobs.board(h, &"swordfin").any(func(j): return j.tpl == first.tpl), "the same posting is not offered twice")
	ok(GuildJobs.claim(h, int(first.id)).contains("not finished"), "cannot hand in early")
	# finish it by its own kind
	var j: Dictionary = GuildJobs.find_active(h, int(first.id))
	var kind := String(j.kind)
	for i in int(j.goal) + 3:
		match kind:
			"kill_any": GuildJobs.on_kill(h, false, "sanctuary")
			"kill_map": GuildJobs.on_kill(h, false, String(j.map))
			"kill_elite": GuildJobs.on_kill(h, true, "westreach")
			_: GuildJobs.progress(h, kind, 1, String(j.map))
	ok(GuildJobs.is_done(j), "%s finished (%d/%d)" % [kind, j.progress, j.goal])
	ok(int(j.progress) <= int(j.goal), "progress stops at the goal")
	var pay := GuildJobs.payout(h, j)
	ok(pay >= int(j.reward), "the payout is the reward plus the tier bonus (%d vs %d)" % [pay, j.reward])
	eq(GuildJobs.claim(h, int(first.id)), "", "hand it in")
	eq(h.inventory.gold, pay, "the guild paid")
	eq(GuildJobs.active(h).size(), 0, "the job is gone")
	eq(int(GuildJobs.state(h).done), 1, "one job done")
	eq(int(GuildJobs.state(h).earned), pay, "the earnings are counted")
	ok(GuildJobs.claim(h, int(first.id)) != "", "it cannot be paid twice")
	done()

func test_job_limits_and_kinds() -> void:
	var h := _hero(&"mage", 10)
	h.inventory.gold = 500
	GuildRules.join(h, &"lantern")
	for i in GuildJobs.ACTIVE_MAX:
		var b := GuildJobs.refresh_board(h, &"lantern")
		eq(GuildJobs.accept(h, &"lantern", int(b[0].id)), "", "take job %d" % (i + 1))
	var extra := GuildJobs.refresh_board(h, &"lantern")
	ok(GuildJobs.accept_error(h, &"lantern", int(extra[0].id)).contains("already carry"), "at most %d jobs at once" % GuildJobs.ACTIVE_MAX)
	# a visit job counts only in its own map; a map-kill only in its own map
	var h2 := _hero(&"knight", 6)
	var visit := {"id": 901, "tpl": "ln_survey_catacombs", "guild": "lantern", "kind": "visit", "title": "t", "text": "t", "goal": 1, "progress": 0, "reward": 90, "map": "catacombs"}
	var kill := {"id": 902, "tpl": "sw_forest", "guild": "swordfin", "kind": "kill_map", "title": "t", "text": "t", "goal": 3, "progress": 0, "reward": 80, "map": "ruined_forest"}
	GuildJobs.state(h2).active = [visit, kill]
	GuildJobs.progress(h2, "visit", 1, "olivar")
	eq(int(visit.progress), 0, "arriving somewhere else does not count")
	GuildJobs.on_kill(h2, false, "westreach")
	eq(int(kill.progress), 0, "kills in another map do not count")
	GuildJobs.progress(h2, "visit", 1, "catacombs")
	GuildJobs.on_kill(h2, false, "ruined_forest")
	eq(int(visit.progress), 1, "the survey is filed on arrival")
	eq(int(kill.progress), 1, "a kill in the right map counts")
	eq(GuildJobs.abandon(h2, 902), "", "a job can be dropped")
	eq(GuildJobs.active(h2).size(), 1, "one left")
	done()

func test_board_drops_outgrown_postings() -> void:
	var h := _hero(&"knight", 1)
	var b := GuildJobs.refresh_board(h, &"swordfin")
	var early := b.filter(func(j): return String(j.tpl) in ["sw_westreach", "sw_forest"])
	h.progress.level = 30
	var later := GuildJobs.refresh_board(h, &"swordfin")
	eq(later.size(), GuildJobs.BOARD_SIZE, "still a full board at level 30")
	for j in later:
		var t := DataGuildJobs.template(String(j.tpl))
		ok(30 >= t.lvl.x and 30 <= t.lvl.y, "%s suits level 30" % j.tpl)
	ok(early.size() >= 0, "checked")
	# reward grows with level
	var t := DataGuildJobs.template("sw_cull")
	ok(GuildJobs.base_reward(t, 25, 40) > GuildJobs.base_reward(t, 25, 1), "the same job pays more to a stronger hero")
	done()

func test_jobs_save_and_old_saves_load() -> void:
	var h := _hero(&"knight", 8)
	h.inventory.gold = 500
	GuildRules.join(h, &"swordfin")
	var b := GuildJobs.refresh_board(h, &"swordfin")
	GuildJobs.accept(h, &"swordfin", int(b[0].id))
	GuildJobs.progress(h, String(GuildJobs.active(h)[0].kind), 1, String(GuildJobs.active(h)[0].map))
	var d: Dictionary = JSON.parse_string(JSON.stringify(h.to_dict()))
	var back := HeroData.from_dict(d)
	eq(GuildJobs.active(back).size(), 1, "the carried job survives a save")
	eq(int(GuildJobs.active(back)[0].id), int(GuildJobs.active(h)[0].id), "same job")
	eq(int(GuildJobs.active(back)[0].progress), int(GuildJobs.active(h)[0].progress), "same progress")
	eq(GuildJobs.board(back, &"swordfin").size(), GuildJobs.BOARD_SIZE, "the board survives too")
	# an old save (no guild_jobs) and a damaged one
	var old := h.to_dict()
	old.erase("guild_jobs")
	var o := HeroData.from_dict(old)
	ok(o != null, "old saves load")
	eq(GuildJobs.active(o).size(), 0, "no jobs in an old save")
	eq(GuildJobs.refresh_board(o, &"swordfin").size(), GuildJobs.BOARD_SIZE, "and a board appears on first visit")
	var bad := h.to_dict()
	bad.guild_jobs = {"active": [{"id": 1, "goal": 3, "tpl": "not_a_job"}, 7, "x"], "board": {"nowhere": [], "swordfin": "oops"}, "done": -5}
	var hb := HeroData.from_dict(bad)
	eq(GuildJobs.active(hb).size(), 0, "unknown and malformed jobs are dropped")
	eq(int(GuildJobs.state(hb).done), 0, "a negative count is clamped")
	done()

func test_the_guild_house_exists() -> void:
	var md := DB.map_def(&"int_guildhouse")
	ok(md != null and md.interior and md.parent_map == &"sanctuary", "the Guild House interior is a Malasugue interior")
	for id in [&"hollis", &"bram", &"sabeth"]:
		var d := DB.npc(id)
		ok(d != null and d.map == &"int_guildhouse", "%s works in the Guild House" % id)
		if d:
			ok(Dialogue.fill(String(d.display_name), Game.hero) != "", "%s has a name" % id)
	ok(DataIsland.INTERIORS.has("int_guildhouse"), "the world map knows the interior")
	ok(not DataIsland.place("town_guildhouse").is_empty(), "the world map lists the building")
	ok(FileAccess.file_exists("res://assets/environment/guild_house.glb"), "the exterior model is in the game")
	done()

func test_guild_house_builds() -> void:
	await _begin(&"sanctuary")
	var town: MapRoot = Game.current_map
	ok(town.spawns.has(&"door_int_guildhouse"), "the town has a spawn outside the Guild House door")
	var doors := 0
	for p in town.find_children("*", "DoorPortal", true, false):
		if p.destination_map == &"int_guildhouse":
			doors += 1
	eq(doors, 1, "one door leads into the Guild House")
	Game.load_map(&"int_guildhouse", &"start")
	for i in 4:
		await host.get_tree().process_frame
	var room: MapRoot = Game.current_map
	ok(room.spawns.has(&"start"), "the room has an entrance")
	var boards := 0
	for n in host.get_tree().get_nodes_in_group(&"interactable"):
		if is_instance_valid(n) and n is GuildJobBoard and room.is_ancestor_of(n):
			boards += 1
			ok(n.interact_text().contains("Quest Board"), "the board says what it is")
	eq(boards, 1, "bh-027: one central Guild Quest Board for every guild")
	var counters := 0
	for n in host.get_tree().get_nodes_in_group(&"interactable"):
		if is_instance_valid(n) and n is GuildCounter and room.is_ancestor_of(n) and n.can_interact(null):
			counters += 1
	ok(counters >= 6, "bh-027: at least six guilds keep a counter in the hall (%d)" % counters)
	var npcs := 0
	for n in host.get_tree().get_nodes_in_group(&"npc"):
		if is_instance_valid(n) and n is Npc and room.is_ancestor_of(n):
			npcs += 1
	eq(npcs, 3, "the steward and the two clerks stand in the room")
	_end()
	done()

func test_dialogue_reaches_the_boards() -> void:
	var seen := {}
	for id in [&"hollis", &"bram", &"sabeth"]:
		var d := DB.npc(id)
		for nid in d.graph.nodes:
			var node: Dictionary = d.graph.nodes[nid]
			for c in node.get("choices", []):
				for a in c.get("actions", []):
					if a.has("service"):
						seen[String(a.service)] = true
	ok(seen.has("guild_jobs"), "the steward opens the boards")
	ok(seen.has("found_guild"), "bh-027: the steward grants charters for new guilds")
	ok(seen.size() >= 2, "the clerks and the steward open the central board")
	done()

# ---- Trade --------------------------------------------------------------------------------------------------------

func _item(id := &"health_potion", count := 1, seed_v := 1) -> ItemInstance:
	var it := DB.make_item(id, BH.Rarity.COMMON, 1, seed_v)
	it.count = count
	return it

func test_trade_rules() -> void:
	var a := _hero()
	var b := _hero(&"mage")
	a.inventory.gold = 300
	b.inventory.gold = 50
	a.inventory.cells.fill(null)
	b.inventory.cells.fill(null)
	var pot := _item(&"health_potion", 3)
	var sword := DB.make_item(a.cls.starting_items[0], BH.Rarity.COMMON, 1, 5)
	a.inventory.add(pot)
	a.inventory.add(sword)
	var mana := _item(&"mana_potion", 2, 4)
	b.inventory.add(mana)
	ok(TradeRules.item_error(pot) == "", "a plain potion may be traded")
	pot.locked = true
	ok(TradeRules.item_error(pot) != "", "a locked item may not")
	pot.locked = false
	pot.favorite = true
	ok(TradeRules.item_error(pot) != "", "nor a favorite")
	pot.favorite = false
	# atomic swap between two heroes
	var give := {"gold": 100, "items": [pot, sword]}
	var take := {"gold": 20, "items": [mana]}
	eq(TradeRules.offer_error(a, give), "", "A can honour the offer")
	eq(TradeRules.offer_error(b, take), "", "B can honour the offer")
	var wire_a := TradeRules.to_wire(give)
	var wire_b := TradeRules.to_wire(take)
	var a_gets := TradeRules.read_incoming(JSON.parse_string(JSON.stringify(wire_b)))
	var b_gets := TradeRules.read_incoming(JSON.parse_string(JSON.stringify(wire_a)))
	eq(a_gets.items.size(), 1, "one item reaches A")
	eq(b_gets.items.size(), 2, "two items reach B")
	eq(TradeRules.swap(a, give, a_gets), "", "A swaps")
	eq(TradeRules.swap(b, take, b_gets), "", "B swaps")
	eq(a.inventory.gold, 300 - 100 + 20, "A's gold")
	eq(b.inventory.gold, 50 - 20 + 100, "B's gold")
	eq(a.inventory.count_of(&"health_potion"), 0, "A gave the potions away")
	eq(a.inventory.count_of(&"mana_potion"), 2, "A got the mana potions")
	eq(b.inventory.count_of(&"health_potion"), 3, "B got the potions")
	ok(b.inventory.index_of(sword) < 0 and a.inventory.index_of(sword) < 0, "the sword is a new copy on B's side")
	eq(b.inventory.count_of(sword.base.id), 1, "B holds the sword")
	eq(b.inventory.count_of(&"mana_potion"), 0, "B gave the mana potions away")
	done()

func test_trade_refuses_bad_offers_and_changes_nothing() -> void:
	var a := _hero()
	a.inventory.gold = 40
	a.inventory.cells.fill(null)
	var pot := _item(&"health_potion", 2)
	a.inventory.add(pot)
	ok(TradeRules.offer_error(a, {"gold": 41, "items": []}) != "", "more gold than you hold")
	ok(TradeRules.offer_error(a, {"gold": -1, "items": []}) != "", "negative gold")
	ok(TradeRules.offer_error(a, {"gold": 0, "items": [_item(&"mana_potion")]}) != "", "an item you do not hold")
	ok(TradeRules.offer_error(a, {"gold": 0, "items": [pot, pot]}) != "", "the same item twice")
	var many := []
	for i in TradeRules.MAX_ITEMS + 1:
		many.append(pot)
	ok(TradeRules.offer_error(a, {"gold": 0, "items": many}) != "", "too many items")
	# a full bag cannot take more than it gives
	for i in a.inventory.capacity():
		if a.inventory.cells[i] == null:
			a.inventory.cells[i] = _item(&"mana_potion", 20, 100 + i)
			a.inventory.cells[i].seed_value = 100 + i
	var incoming := {"gold": 5, "items": [TradeRules.read_incoming({"items": [_item(&"health_potion", 1, 9).to_dict()]}).items[0],
		TradeRules.read_incoming({"items": [_item(&"mana_potion", 1, 8).to_dict()]}).items[0]]}
	var gold_before := a.inventory.gold
	ok(TradeRules.swap(a, {"gold": 10, "items": [pot]}, incoming) != "", "two arriving items do not fit where one leaves")
	eq(a.inventory.gold, gold_before, "nothing changed: gold")
	ok(a.inventory.index_of(pot) >= 0, "nothing changed: the offered item is still there")
	# the other side's claims are cleaned
	var raw := {"gold": 999999999999, "items": [{"base": "no_such_item"}, 5, _item(&"health_potion", 99999).to_dict()]}
	var clean := TradeRules.read_incoming(raw)
	ok(clean.gold <= TradeRules.MAX_GOLD, "a silly gold claim is capped")
	eq(clean.items.size(), 1, "unknown and malformed items are dropped")
	ok(clean.items[0].count <= clean.items[0].base.stack_max, "a stack cannot exceed its size")
	var d := _item(&"health_potion").to_dict()
	d["locked"] = true
	d["favorite"] = true
	var li: ItemInstance = TradeRules.read_incoming({"items": [d]}).items[0]
	ok(not li.locked and not li.favorite, "another player's locks are not inherited")
	eq(TradeRules.describe({"gold": 0, "items": []}), "nothing", "an empty offer reads 'nothing'")
	eq(TradeRules.describe({"gold": 120, "items": [pot]}), "1 item and 120 gold", "an offer reads plainly")
	done()

func test_trade_state_offline() -> void:
	ok(not Net.in_trade(), "no trade at start")
	ok(Net.trade_error(2) != "", "no trade without a multiplayer game")
	eq(Net.trade_set_offer(5, []), "There is no open trade.", "no offer without a trade")
	Net.trade_accept(true)
	ok(not Net.in_trade(), "accepting nothing changes nothing")
	Net.trade_cancel("x")
	Net.trade_reset("")
	ok(Net.PROTOCOL >= 5, "an older game cannot join a trading game (protocol %d)" % Net.PROTOCOL)
	done()
