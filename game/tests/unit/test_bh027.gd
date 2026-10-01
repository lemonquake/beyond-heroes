extends TestCase
## bh-027 (Alpha 0.3): accessories drop again (and twenty new ones), guilds of your own, the rolled guilds of the Guild
## House, recruitment, passives, Guild War, Call to Arms, the central quest board, multiplayer guild data, Showcase.

var _saved := {}
var _holder: Node3D
var _player: Player

func _init() -> void:
	strict = true

func _hero(cls := &"knight", level := 20, gold := 200000) -> HeroData:
	var h := Game.new_hero(cls, "Founder")
	h.progress.add_xp(XpCurve.total_xp_for_level(level))
	h.inventory.gold = gold
	return h

func _begin(map_id: StringName, hero: HeroData = null) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = hero if hero else _hero()
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
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

# ---- accessories ----------------------------------------------------------------------------------------------------

func test_twenty_new_accessories_are_complete() -> void:
	var ids := DataAccessories.ids()
	eq(ids.size(), 20, "twenty new accessories")
	var shapes := {}
	for id in ids:
		var b := DB.item_base(id)
		ok(b != null and b.category == &"accessory", "%s is an accessory" % id)
		ok(ResourceLoader.exists(b.icon), "%s has an icon" % id)
		ok(ResourceLoader.exists("res://assets/items/%s.glb" % id), "%s has a model" % id)
		ok(HeroWear.has_model(String(id)), "%s is worn on the hero" % id)
		ok(not b.implicit.is_empty(), "%s grants something of its own" % id)
		ok(b.lore != "", "%s has a story" % id)
		shapes[DataAccessories.rows().filter(func(r): return r[0] == id)[0][2]] = true
	eq(shapes.size(), 20, "every one has its own shape")
	done()

func test_accessories_drop_with_weapons() -> void:
	var saved := Loot.rng.state
	Loot.rng.seed = 2027
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var p := Player.new()
		p.hero = Game.new_hero(cls, "Looter")
		p.stats = p.hero.compute_stats()
		var boss := Enemy.new().setup(DB.enemy(&"hollow_soldier"), 25)
		boss.is_boss = true
		for i in 30:
			var items := Loot.equipment_for(boss, p)
			ok(items[0].base.is_weapon(), "a boss still drops a weapon first")
			ok(items.any(func(it): return it.base.category == &"accessory"), "%s: a boss always drops an accessory too" % cls)
		var mob := Enemy.new().setup(DB.enemy(&"hollow_soldier"), 25)
		var acc := 0
		var any := 0
		for i in 1500:
			for it in Loot.equipment_for(mob, p):
				any += 1
				if it.base.category == &"accessory":
					acc += 1
					ok(ItemGenerator.accessory_fits(it.base, cls), "an accessory anyone of the class can wear")
		ok(any > 0 and acc > 0 and float(acc) / float(any) > 0.12, "%s: ordinary monsters drop accessories (%d of %d)" % [cls, acc, any])
		boss.free()
		mob.free()
		p.free()
	Loot.rng.state = saved
	done()

# ---- guild names and the rolled guilds ------------------------------------------------------------------------------

func test_guild_names_read_like_names() -> void:
	var r := rng(91)
	var seen := {}
	var words := {}
	for w in GuildNames.ADJECTIVES + GuildNames.GROUPS + GuildNames.EMBLEMS.keys() + GuildNames.EMBLEMS.values() + \
			["The", "of", "the", "and", "Order", "Fellowship", "Brotherhood", "Circle", "League", "Society", "Company", "Keepers", "Sons",
			"Daughters", "Children", "Heirs", "Riders", "Hunters", "Shields", "Vanguard", "Watch", "Guard", "Legion", "Brigade", "Host", "Banner",
			"Band", "Lodge", "Trust", "Expedition", "Kinship", "Wardens"]:
		for part in String(w).split(" "):
			words[part] = true
	var gibberish := 0
	for i in 400:
		var n := GuildNames.roll_name(r, seen.keys())
		seen[n] = true
		ok(n.length() >= 6 and n.length() <= 32, "a name of a sensible length: %s" % n)
		for part in n.split(" "):
			if not words.has(part):
				# a place: two real words joined (Ash + vale)
				var ok_place := false
				for h in GuildNames.PLACE_HEADS:
					if part.begins_with(h) and GuildNames.PLACE_TAILS.has(part.substr(String(h).length())):
						ok_place = true
				if not ok_place:
					gibberish += 1
	eq(gibberish, 0, "every word of every name is a real word or a joined place name")
	ok(seen.size() >= 300, "names rarely repeat (%d different of 400)" % seen.size())
	eq(GuildNames.short("Order of the Gilded Anchor"), "Gilded Anchor", "short form")
	done()

func test_the_guild_house_guilds_are_rolled_once_and_saved() -> void:
	var h := _hero()
	var w := GuildRegistry.world(h)
	eq((w.npc as Array).size(), GuildRegistry.NPC_COUNT, "four guilds set up in the Guild House")
	var names := {}
	for g in w.npc:
		names[g.name] = true
		eq((g.perks as Array).size(), 3, "%s grants three perks" % g.name)
		ok(String(g.master) != "" and String(g.motto) != "", "%s has a master and a motto" % g.name)
	eq(names.size(), GuildRegistry.NPC_COUNT, "four different names")
	var ids := GuildRegistry.all_ids(h)
	ok(ids.size() >= 6, "with the two old guilds, at least six to show (%d)" % ids.size())
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(GuildRegistry.world(back).npc, w.npc, "the same guilds after saving and loading")
	ok(GuildRegistry.banner(h, &"npc_0") != null, "a painted banner for a rolled guild")
	# joining one works like the old guilds and grants its perks
	eq(GuildRules.join(h, &"npc_2"), "", "register with a rolled guild")
	eq(h.guild, &"npc_2", "member")
	var sources := GuildRules.modifiers(h).map(func(m): return m.source)
	ok(sources.has(String(GuildRegistry.info(h, &"npc_2").short)), "its perks apply")
	eq(HeroData.from_dict(h.to_dict()).guild, &"npc_2", "membership survives a save")
	done()

# ---- founding, members, slots ------------------------------------------------------------------------------------

func test_found_a_guild() -> void:
	var h := _hero(&"mage", 20, 900)
	ok(OwnGuild.found_error(h, "The Iron Stags").contains("1000"), "the charter costs 1000 gold")
	h.inventory.gold = 5000
	ok(OwnGuild.found_error(h, "x") != "", "a name is needed")
	ok(OwnGuild.found_error(h, "The Swordfin Company") != "", "an existing guild's name is taken")
	eq(OwnGuild.found(h, "The Iron Stags", "Hold the line.", "We hunt the Hollow and keep the roads.", {"crest": "star"}), "", "found it")
	eq(h.inventory.gold, 4000, "the fee is paid")
	eq(h.guild, GuildRegistry.OWN, "the hero leads it")
	ok(OwnGuild.is_master(h), "Guildmaster")
	eq(h.tier, 1, "registered as a Class E hero")
	eq(OwnGuild.slots(h), 6, "six member slots to begin with")
	eq(GuildRules.display_name(h), "The Iron Stags", "its name")
	eq(String(GuildRegistry.info(h, GuildRegistry.OWN).info), "We hunt the Hollow and keep the roads.", "its guild info")
	ok(GuildRules.join_error(h, &"swordfin") != "", "a Guildmaster cannot join another guild")
	ok(OwnGuild.found_error(h, "Second") != "", "one guild per hero")
	done()

func test_adventurers_join_until_full_at_the_right_levels() -> void:
	var h := _hero(&"knight", 20)
	OwnGuild.found(h, "The Wandering Compass Company", "", "", {})
	eq(OwnGuild.recruit_range(h), Vector2i(13, 20), "a level 20 Guildmaster draws levels 13-20")
	var classes := {}
	for i in 400:
		h.play_time += 60.0
		OwnGuild.advance(h, 60.0)
	eq(OwnGuild.members(h).size(), 6, "adventurers joined until the guild was full")
	for m in OwnGuild.members(h):
		ok(int(m.level) >= 13 and int(m.level) <= 20, "%s is level %d" % [m.name, m.level])
		ok(DataGuildPassives.TRAITS.has(StringName(m.trait)), "%s has a trait" % m.name)
		classes[m.cls] = true
	ok(OwnGuild.recruit_in(h) == INF, "nobody applies to a full guild")
	ok(float(h.own_guild.treasury) > 0.0, "members pay tithes")
	ok(float(h.own_guild.renown) > 0.0, "members earn renown")
	# kick and the slot opens
	var first: Dictionary = OwnGuild.members(h)[0]
	eq(OwnGuild.kick(h, int(first.id)), "", "dismiss a member")
	eq(OwnGuild.members(h).size(), 5, "one fewer")
	ok(OwnGuild.recruit_in(h) < INF, "a new applicant is on the way")
	# slots
	h.inventory.gold = 100000
	eq(OwnGuild.next_slot_upgrade(h), [9, 10000], "9 slots for 10,000 gold")
	eq(OwnGuild.buy_slots(h), "", "buy")
	eq(OwnGuild.next_slot_upgrade(h), [12, 15000], "12 slots for 15,000 gold")
	OwnGuild.buy_slots(h)
	eq(OwnGuild.next_slot_upgrade(h), [15, 25000], "15 slots for 25,000 gold")
	OwnGuild.buy_slots(h)
	eq(OwnGuild.slots(h), 15, "fifteen slots")
	eq(h.inventory.gold, 100000 - 50000, "50,000 gold in all")
	ok(OwnGuild.buy_slots(h) != "", "no more than fifteen")
	# a level 40 Guildmaster draws stronger recruits
	var g40 := _hero(&"mage", 40)
	OwnGuild.found(g40, "Order of the Sable Owl", "", "", {})
	var r := OwnGuild.recruit_range(g40)
	ok(r.x >= 25 and r.y == 40, "level 40: recruits at %d-%d" % [r.x, r.y])
	done()

# ---- passives and Guild War ---------------------------------------------------------------------------------------

func test_passives_and_guild_war() -> void:
	var h := _hero(&"ranger", 30)
	OwnGuild.found(h, "The Tidewatch Herons", "", "", {})
	var base := h.compute_stats().get_stat(&"max_hp")
	eq(OwnGuild.upgrade(h, &"iron_discipline"), "", "rank 1 at guild level 1")
	ok(h.compute_stats().get_stat(&"max_hp") > base, "Iron Discipline raises Maximum HP")
	ok(OwnGuild.upgrade_error(h, &"iron_discipline").contains("guild level"), "rank 2 waits for guild level 3")
	ok(OwnGuild.upgrade_error(h, &"rallying_cry").contains("guild level"), "Guild War passives need guild level 4")
	OwnGuild.add_renown(h, 50000.0)
	ok(OwnGuild.level(h) >= 10, "renown raises the guild's level (%d)" % OwnGuild.level(h))
	eq(OwnGuild.upgrade(h, &"rallying_cry"), "", "Rallying Cry")
	eq(OwnGuild.upgrade(h, &"shield_wall"), "", "Shield Wall")
	ok(GuildRules.has_war_passives(h), "the guild has Guild War passives")
	eq(GuildRules.war_modifiers(h, 0).size(), 0, "nothing alone")
	var four: Array = GuildRules.war_modifiers(h, 4)
	var twelve: Array = GuildRules.war_modifiers(h, 12)
	var forty: Array = GuildRules.war_modifiers(h, 40)
	ok(four.size() == 2, "two Guild War modifiers")
	ok(twelve[0].value > four[0].value, "they grow with comrades")
	eq(forty[0].value, twelve[0].value, "capped at %d comrades" % DataGuildPassives.WAR_CAP)
	done()

# ---- Call to Arms ---------------------------------------------------------------------------------------------------

func test_call_to_arms() -> void:
	var h := _hero(&"knight", 18)
	OwnGuild.found(h, "Ashvale Vanguard", "", "", {})
	await _begin(&"ruined_forest", h)
	ok(GuildSummons.call_error(h).contains("Nobody"), "nobody to call before anyone joins")
	for i in 3:
		OwnGuild.recruit(h)
	var res := GuildSummons.call_to_arms(h, _player)
	ok(res.ok, "Call to Arms: %s" % res.text)
	await host.get_tree().physics_frame
	eq(GuildSummons.fighters(host.get_tree()).size(), 1, "rank 1 calls one member")
	near(GuildSummons.time_left(h), 900.0, 1.0, "for 15 minutes")
	near(GuildSummons.cooldown_left(h), 1800.0, 1.0, "again in 30 minutes")
	var f: GuildFighter = GuildSummons.fighters(host.get_tree())[0]
	var strongest: Dictionary = GuildSummons.answering(h)[0]
	eq(f.member_id, int(strongest.id), "the strongest member answers")
	eq(f.hero.progress.level, int(strongest.level), "at their own level")
	ok(f.hero.equipment.get_item(&"main_weapon") != null, "armed")
	ok(GuildSummons.call_error(h) != "", "cannot call twice")
	# rank 2 calls two
	h.inventory.gold = 100000
	ok(GuildSummons.upgrade_error(h).contains("guild level"), "rank 2 needs guild level 3")
	OwnGuild.add_renown(h, 5000.0)
	eq(GuildSummons.upgrade(h), "", "train rank 2")
	eq(GuildSummons.rank(h), 2, "rank 2")
	eq(GuildSummons.answering(h).size(), 2, "two members would answer")
	# the call ends after 15 minutes
	h.play_time += 901.0
	GuildSummons.tick(h)
	await host.get_tree().process_frame
	eq(GuildSummons.fighters(host.get_tree()).size(), 0, "the fighters went home")
	ok(GuildSummons.cooldown_left(h) > 0.0, "still cooling down")
	h.play_time += 900.0
	ok(GuildSummons.call_error(h) == "", "ready again after 30 minutes")
	_end()
	done()

# ---- saving -------------------------------------------------------------------------------------------------------

func test_own_guild_survives_saving() -> void:
	var h := _hero(&"shadowblade", 25)
	OwnGuild.found(h, "Keepers of the Silver Tide", "Bring them home.", "Line one.\nLine two.", {"crest": "moon", "field": "1f3d8c"})
	for i in 4:
		OwnGuild.recruit(h)
	h.inventory.gold = 50000
	OwnGuild.buy_slots(h)
	OwnGuild.upgrade(h, &"sharpened_steel")
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(back.guild, GuildRegistry.OWN, "still the Guildmaster")
	eq(String(back.own_guild.name), "Keepers of the Silver Tide", "name")
	eq(String(back.own_guild.info), "Line one.\nLine two.", "guild info")
	eq(OwnGuild.members(back).size(), 4, "members")
	eq(OwnGuild.slots(back), 9, "slots")
	eq(OwnGuild.rank(back, &"sharpened_steel"), 1, "passives")
	eq(String(back.own_guild.style.crest), "moon", "banner design")
	eq(OwnGuild.from_plain({"name": ""}), {}, "a nameless guild loads as none")
	var bad := h.to_dict()
	bad.own_guild = {"name": "Broken", "slots": 999, "members": [{"id": 1, "cls": "dragon", "name": "X"}, "junk"], "passives": {"nope": 9, "war_drums": 99}}
	var hb := HeroData.from_dict(bad)
	eq(OwnGuild.slots(hb), 6, "impossible slots fall back to six")
	eq(OwnGuild.members(hb).size(), 0, "broken members are dropped")
	eq(OwnGuild.rank(hb, &"war_drums"), 5, "ranks are clamped")
	done()

# ---- multiplayer guild data ------------------------------------------------------------------------------------------

func test_a_fellow_heros_guild() -> void:
	var master := _hero(&"knight", 30)
	OwnGuild.found(master, "The Golden Keys", "One shield, many hands.", "Open to all.", {"crest": "key"})
	OwnGuild.upgrade(master, &"sharpened_steel")
	eq(OwnGuild.add_player_member(master, "Ilyra", "mage", 22), "", "a fellow player joins")
	ok(OwnGuild.has_player_member(master, "Ilyra"), "listed as a Sworn Hero")
	eq(OwnGuild.members(master).size(), 1, "they take a slot")
	var snap := OwnGuild.snapshot(master)
	var member := _hero(&"mage", 22)
	member.hero_name = "Ilyra"
	member.guild = GuildRegistry.REMOTE
	member.remote_guild = GuildRegistry.clean_remote(snap)
	eq(GuildRules.display_name(member), "The Golden Keys", "the member flies the Guildmaster's guild")
	eq(GuildRules.guild_key(member), GuildRules.guild_key(master), "both recognise the same guild")
	ok(GuildRules.modifiers(member).any(func(m): return m.source == "Golden Keys"), "the guild's passives reach the member")
	ok(not GuildRules.can_customise(member), "only the Guildmaster renames it")
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(member.to_dict())))
	eq(back.guild, GuildRegistry.REMOTE, "membership survives a save")
	eq(String(back.remote_guild.info), "Open to all.", "with the guild info")
	# importing another player's guild into the Guild House
	var other := _hero(&"ranger", 10)
	GuildRegistry.import_remote(other, snap)
	GuildRegistry.import_remote(other, snap)
	eq((GuildRegistry.world(other).imported as Array).size(), 1, "imported once")
	ok(GuildRegistry.all_ids(other).has(&"imp_0"), "it hangs in the Guild House")
	eq(String(GuildRegistry.info(other, &"imp_0").master), "Founder", "with its Guildmaster")
	eq(GuildRegistry.clean_remote({"name": "", "master": "x"}), {}, "a nameless snapshot is refused")
	# the profile every player sends
	var prof := Net.guild_profile(master)
	eq(String(prof.name), "The Golden Keys", "profile name")
	eq(String(prof.key), OwnGuild.key(master), "profile key")
	eq(OwnGuild.kick(master, int(OwnGuild.members(master)[0].id)), "", "the Guildmaster can dismiss a fellow player")
	done()

func test_whisper_and_showcase_packs() -> void:
	var saved_peers := Net.peers
	Net.peers = {1: {"name": "Ann Mar"}, 2: {"name": "Ann"}, 3: {"name": "Bo"}}
	eq(ChatBox.parse_whisper("/w Bo hello there"), [3, "hello there"], "whisper to Bo")
	eq(ChatBox.parse_whisper("/w Ann Mar hi"), [1, "hi"], "the longest matching name wins")
	eq(ChatBox.parse_whisper("/tell Ann hi"), [2, "hi"], "/tell works too")
	eq(int(ChatBox.parse_whisper("/w Nobody hi")[0]), 0, "unknown name")
	Net.peers = saved_peers
	var h := _hero(&"knight", 12)
	OwnGuild.found(h, "Thornwood Watch", "Brave the dark.", "We meet at dusk.", {})
	var pack := Net.showcase_pack(h)
	ok(not pack.has("stats"), "no stats in a Showcase")
	eq(String(pack.guild.name), "Thornwood Watch", "the guild travels with it")
	var copy := ShowcaseWindow.hero_from_pack(JSON.parse_string(JSON.stringify(pack)))
	for slot in ShowcaseWindow.SLOTS:
		var a := h.equipment.get_item(slot)
		var b := copy.equipment.get_item(slot)
		eq(b.base.id if b else &"", a.base.id if a else &"", "%s shown as worn" % slot)
	var info := ShowcaseWindow._as_info(pack.guild)
	eq(String(info.info), "We meet at dusk.", "the guild's page shows its info")
	ok(ShowcaseWindow._banner_of(pack.guild) != null, "and a banner")
	done()

# ---- the central board -----------------------------------------------------------------------------------------------

func test_the_central_board_is_open_to_everyone() -> void:
	var h := _hero(&"mage", 12)
	var b := GuildJobs.refresh_board(h, GuildJobs.CENTRAL)
	eq(b.size(), GuildJobs.CENTRAL_SIZE, "nine postings at once")
	var issuers := {}
	for j in b:
		issuers[String(j.guild)] = true
		eq(GuildJobs.accept_error(h, GuildJobs.CENTRAL, int(j.id)) if GuildJobs.active(h).size() < GuildJobs.ACTIVE_MAX else "", "", "a hero with no guild may take %s" % j.title)
	ok(issuers.size() >= 2, "posted by several guilds")
	for i in GuildJobs.ACTIVE_MAX:
		var board := GuildJobs.refresh_board(h, GuildJobs.CENTRAL)
		eq(GuildJobs.accept(h, GuildJobs.CENTRAL, int(board[0].id)), "", "take job %d" % (i + 1))
	ok(GuildJobs.accept_error(h, GuildJobs.CENTRAL, int(GuildJobs.refresh_board(h, GuildJobs.CENTRAL)[0].id)).contains("already carry"), "five at once")
	# a job of the hero's own guild pays more, and handing in earns the guild renown
	OwnGuild.found(h, "Order of the Ivory Bell", "", "", {})
	var j: Dictionary = GuildJobs.active(h)[0]
	var plain := GuildJobs.payout(h, j)
	j.guild = String(GuildRegistry.OWN)
	ok(GuildJobs.payout(h, j) > plain, "own-guild postings pay a bonus")
	j.progress = j.goal
	var renown := float(h.own_guild.renown)
	eq(GuildJobs.claim(h, int(j.id)), "", "hand in")
	ok(float(h.own_guild.renown) > renown, "the guild earned renown")
	done()

# ---- the Guild House and its banner ------------------------------------------------------------------------------------

func test_guild_house_shows_the_guilds_and_features_yours() -> void:
	var h := _hero(&"knight", 20)
	await _begin(&"int_guildhouse", h)
	var counters := host.get_tree().get_nodes_in_group(&"interactable").filter(func(n): return n is GuildCounter and n.can_interact(null))
	ok(counters.size() >= 6, "the old houses and the four newer guilds (%d)" % counters.size())
	var display: GuildBannerDisplay = null
	for n in Game.current_map.find_children("*", "GuildBannerDisplay", true, false):
		display = n
	ok(display != null, "the hero's banner hangs in the hall")
	eq(display.feature_text(), "", "nothing featured without a guild of your own")
	OwnGuild.found(h, "The Unbroken Oaks", "From ash, we rise.", "", {})
	await host.get_tree().process_frame
	ok(display.feature_text().contains("Aljay and Roydo") and display.feature_text().contains("Paul David"), "your guild is featured: the town believes in you")
	_end()
	await _begin(&"sanctuary", h)
	var banners := host.get_tree().get_nodes_in_group(&"guild_hall_banner")
	eq(banners.size(), 1, "one great banner outside the Guild House")
	var gb: GuildHallBanner = banners[0]
	ok(gb.flying(), "flying for a hero with a guild")
	eq(gb.shown_name(), "THE UNBROKEN OAKS", "with the guild's name across it")
	OwnGuild.disband(h)
	await host.get_tree().process_frame
	ok(not gb.flying(), "taken down without a guild")
	_end()
	done()
