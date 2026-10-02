extends TestCase
## bh-030: gear that keeps pace with its level, the Alt quick-use belt, dynamic Guild Quests, the Debug console and its
## cheats (azrin azrael, quake quake), first-person view, profile pictures and saved official accounts.

func _init() -> void:
	strict = true

func _kit_defense(level: int, weight: StringName) -> float:
	var t := 0.0
	for cat in [&"helm", &"inner_garment", &"armor", &"gloves", &"boots", &"leggings"]:
		t += GearScaling.slot_defense(cat, weight, level)
	return t

func test_high_level_armor_is_strong() -> void:
	# the reported case: a level 53 piece of a level 1 base
	var it := DB.make_item(&"iron_gauntlet", BH.Rarity.COMMON, 53, 7)
	it.quality = 0.0
	var old := it.base.defense * CombatGrowth.armor_factor(53)
	print("  [gear] iron gauntlet L53 defense %.1f (old %.1f)" % [it.defense_value(), old])
	ok(it.defense_value() >= 120.0, "a plain level 53 gauntlet has at least 120 Defense (old %.0f, now %.0f)" % [old, it.defense_value()])
	# every slot at level 53 beats the 50-70 Defense pieces of levels 20-30
	for cat in [&"helm", &"inner_garment", &"armor", &"gloves", &"boots", &"leggings"]:
		var row := ""
		for lvl in [10, 20, 30, 53, 100]:
			row += "  L%d %4.0f" % [lvl, GearScaling.slot_defense(cat, &"heavy", lvl)]
		print("  [gear] %-14s%s" % [cat, row])
		ok(GearScaling.slot_defense(cat, &"heavy", 53) > 110.0, "a level 53 plate %s is above 110 Defense" % cat)
		ok(GearScaling.slot_defense(cat, &"heavy", 53) > 1.8 * GearScaling.slot_defense(cat, &"heavy", 25), "a level 53 %s is far stronger than a level 25 one" % cat)
	# levels 1-5 keep their authored numbers
	var low := DB.make_item(&"iron_gauntlet", BH.Rarity.COMMON, 3, 7)
	low.quality = 0.0
	eq(low.defense_value(), low.base.defense, "a level 3 gauntlet keeps its authored Defense")
	# a full kit keeps its share of reduction against monsters of its level, at 16, 50 and 300
	for lvl in [16, 50, 120, 300]:
		var heavy := _kit_defense(lvl, &"heavy")
		var dr := StatCalculator.armor_reduction(heavy, lvl)
		print("  [gear] heavy kit L%d: %.0f Defense, %.1f%% vs same level" % [lvl, heavy, dr * 100.0])
		ok(dr > 0.40 and dr < 0.66, "a heavy kit at level %d reduces same-level hits 40-66%% (got %.1f%%)" % [lvl, dr * 100.0])
		var cloth := StatCalculator.armor_reduction(_kit_defense(lvl, &"cloth"), lvl)
		ok(cloth < dr and cloth > 0.08, "cloth stays lighter than plate at level %d (%.1f%%)" % [lvl, cloth * 100.0])
	# higher item level = stronger, for every armour slot
	for cat in [&"helm", &"armor", &"gloves", &"boots", &"shield", &"leggings"]:
		ok(GearScaling.slot_defense(cat, &"heavy", 60) > GearScaling.slot_defense(cat, &"heavy", 50), "%s grows from 50 to 60" % cat)
	done()

func test_flat_enchantments_grow_percentages_do_not() -> void:
	var it := DB.make_item(&"iron_helm", BH.Rarity.COMMON, 80, 3)
	it.affixes = [{"id": "max_hp", "tier": 3, "value": 60.0}, {"id": "str", "tier": 3, "value": 16.0},
		{"id": "res_fire", "tier": 2, "value": 0.25}, {"id": "crit_chance", "tier": 2, "value": 0.05}]
	ok(it.affix_value(it.affixes[0]) > 100.0, "+60 Health on a level 80 helm grows (%.0f)" % it.affix_value(it.affixes[0]))
	ok(it.affix_value(it.affixes[1]) > 16.0, "+16 Strength grows (%.0f)" % it.affix_value(it.affixes[1]))
	eq(it.affix_value(it.affixes[2]), 0.25, "resistance stays as rolled")
	eq(it.affix_value(it.affixes[3]), 0.05, "critical chance stays as rolled")
	var low := DB.make_item(&"iron_helm", BH.Rarity.COMMON, 30, 3)
	low.affixes = [{"id": "max_hp", "tier": 2, "value": 40.0}]
	eq(low.affix_value(low.affixes[0]), 40.0, "below the top tier's level nothing changes")
	# implicit flats grow; implicit percentages do not
	var veil := DB.make_item(&"seers_circlet", BH.Rarity.COMMON, 60, 3)
	var mana := 0.0
	for m in veil.modifiers():
		if m.stat == &"max_mana":
			mana += m.value
	ok(mana > 36.0 * 2.0, "the Seer's Veil +36 Mana implicit grows at level 60 (%.0f)" % mana)
	var robe := DB.make_item(&"magister_robe", BH.Rarity.COMMON, 60, 3)
	for m in robe.modifiers():
		if m.stat == &"magic_damage":
			eq(m.value, 0.10, "the Magister Robe's 10% increased magic damage stays 10%")
	done()

func test_guild_board_never_runs_dry() -> void:
	var h := Game.new_hero(&"knight", "Board Tester")
	h.progress.add_xp(XpCurve.total_xp_for_level(53))
	h.discovered_maps[&"westreach"] = true
	h.discovered_maps[&"ruined_forest"] = true
	var board := GuildJobs.refresh_board(h, GuildJobs.CENTRAL)
	eq(board.size(), GuildJobs.CENTRAL_SIZE, "a level 53 hero sees a full board")
	var dungeon := board.filter(func(j): return String(j.kind).begins_with("dungeon_"))
	ok(dungeon.size() >= 2, "dungeon work is on the board (%d postings)" % dungeon.size())
	# take, finish and hand in many jobs: the board keeps refilling
	for round in 12:
		var b := GuildJobs.refresh_board(h, GuildJobs.CENTRAL)
		ok(not b.is_empty(), "round %d: the board still has postings" % round)
		if b.is_empty():
			break
		var id := int(b[0].id)
		eq(GuildJobs.accept(h, GuildJobs.CENTRAL, id), "", "accept round %d" % round)
		var j := GuildJobs.find_active(h, id)
		j.progress = j.goal
		eq(GuildJobs.claim(h, id), "", "claim round %d" % round)
	# dungeon progress hooks
	var dg: StringName = DataDungeons.order()[0]
	var tpl := DataGuildJobs.template("dyn:dungeon_kill:%s" % dg)
	ok(not tpl.is_empty(), "a dynamic dungeon template resolves")
	var rng := RandomNumberGenerator.new()
	var job := GuildJobs.make_job(h, tpl, rng)
	GuildJobs.active(h).append(job)
	GuildJobs.on_kill(h, false, String(DataDungeons.map_id(dg, 2)))
	eq(int(job.progress), 1, "a kill on floor 2 counts for the dungeon's delve")
	GuildJobs.on_kill(h, false, "westreach")
	eq(int(job.progress), 1, "a kill outside does not")
	var depth := GuildJobs.make_job(h, DataGuildJobs.template("dyn:dungeon_depth:%s" % dg), rng)
	GuildJobs.active(h).append(depth)
	GuildJobs.progress(h, "dungeon_depth", 3, String(dg))
	eq(int(depth.progress), mini(3, int(depth.goal)), "reaching floor 3 records the depth")
	# saves keep dynamic jobs
	var back := GuildJobs.from_dict(GuildJobs.to_dict(h))
	ok((back.active as Array).any(func(x): return String(x.tpl).begins_with("dyn:")), "dynamic jobs survive a save")
	# the repost button gives a fresh board
	var before := GuildJobs.board(h, GuildJobs.CENTRAL).map(func(x): return int(x.id))
	var after := GuildJobs.repost(h).map(func(x): return int(x.id))
	ok(not after.is_empty() and after.all(func(i): return not before.has(i)), "Post New Jobs replaces the postings")
	done()

func test_effects_ignore_callbacks_of_freed_owners() -> void:
	# a lambda written inside a node (like an Enemy's blast callback) whose node is freed before the effect fires
	var s := GDScript.new()
	s.source_code = "extends Node\nvar calls := 0\nfunc make() -> Callable:\n\treturn func(_a = null, _b = null, _c = null) -> void: calls += 1\n"
	s.reload()
	var owner: Node = s.new()
	var cb: Callable = owner.make()
	var pr := Projectile.new()
	pr.on_hit = cb
	pr.on_end = cb
	ok(SafeCallable.alive(pr.on_hit, pr._on_hit_owner), "the callback is live while its owner is")
	owner.free()
	ok(not SafeCallable.alive(pr.on_hit, pr._on_hit_owner), "the callback is skipped once its owner is freed")
	var blast := AreaEffects.DelayedBlast.new()
	blast.on_blast = func(_p, _h) -> void: pass
	ok(SafeCallable.alive(blast.on_blast, blast._on_blast_owner), "a callback of a living owner still runs")
	pr.free()
	blast.free()
	done()

func test_cheats_debug_unlock_and_quake_quake() -> void:
	var h := Game.new_hero(&"knight", "Cheat Tester")
	ok(Cheats.is_code("azrin azrael") and Cheats.is_code("Quake Quake "), "the new codes are codes")
	ok(not h.debug_unlocked, "the console starts locked")
	ok(Cheats.apply("azrin azrael", h).contains("unlocked"), "azrin azrael unlocks the console")
	ok(h.debug_unlocked, "the hero remembers it")
	ok(HeroData.from_dict(h.to_dict()).debug_unlocked, "the unlock survives a save")
	ok(not HeroData.from_dict(Game.new_hero(&"mage", "Old").to_dict()).debug_unlocked, "other heroes stay locked")
	eq(h.debug_unlocked, true, "azrin azrael is not the azrin + azrael cheats (no level change)")
	eq(h.progress.level, 1, "level unchanged")
	ok(Cheats.apply("quake quake", h).contains("No Quake Team"), "quake quake with nobody to dismiss says so")
	for code in Cheats.CODES:
		ok(Cheats.DESCRIPTIONS.has(code), "%s has a description" % code)
	done()

func test_debug_console_builds_every_page() -> void:
	var old := Game.hero
	Game.hero = Game.new_hero(&"mage", "Console")
	Game.hero.debug_unlocked = true
	var vp := SubViewport.new()
	vp.size = Vector2i(1920, 1080)
	host.add_child(vp)
	var w := DebugWindow.new()
	w.theme = UITheme.theme()
	vp.add_child(w)
	w.open()
	for p in DebugWindow.PAGES:
		w.show_page(String(p[0]))
		await host.get_tree().process_frame
		ok(w._page_box.get_child_count() > 2, "page %s has controls" % p[0])
	# the Item Summoner: a perfect legendary helm with 3 sockets and 30% quality
	w.show_page("items")
	var idx := w._base_ids.find(&"visored_greathelm")
	if idx < 0:
		w._search.text = "Visored"
		w._fill_bases()
		idx = w._base_ids.find(&"visored_greathelm")
	ok(idx >= 0, "the helm is in the summoner list")
	w._base.selected = maxi(0, idx)
	w._rarity.selected = BH.Rarity.LEGENDARY
	w._ilvl.value = 60
	w._quality.value = 30
	w._sockets.value = 3
	w._perfect.button_pressed = true
	var before := Game.hero.inventory.free_cells()
	w._summon_item()
	eq(Game.hero.inventory.free_cells(), before - 1, "the summoned item is in the bag")
	var it: ItemInstance = null
	for c in Game.hero.inventory.cells:
		if c and c.base.id == &"visored_greathelm":
			it = c
	ok(it != null and it.rarity == BH.Rarity.LEGENDARY and it.ilvl == 60 and it.sockets == 3 and is_equal_approx(it.quality, 0.3), "rarity, level, sockets and quality are as chosen")
	# the Tempo Summoner and Unsummoner
	w.show_page("tempos")
	var n := Game.hero.spirit_hall.size()
	w._summon_tempo(false)
	eq(Game.hero.spirit_hall.size(), n + 1, "a spirit is summoned to the hall")
	var t: TempoData = Game.hero.spirit_hall[-1]
	w._unsummon(t)
	ok(not Game.hero.spirit_hall.has(t), "and unsummoned")
	w.queue_free()
	vp.queue_free()
	Game.hero = old
	done()

func test_profile_picture_and_alt_keys() -> void:
	var h := Game.new_hero(&"ranger", "Pic")
	var img := Image.create(400, 300, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.2, 0.6, 0.9))
	eq(ProfilePicture.set_picture(h, img), "", "a picture is accepted")
	var back := HeroData.from_dict(h.to_dict())
	eq(back.profile_pic.size(), h.profile_pic.size(), "the picture survives a save")
	var tex := ProfilePicture.texture_of(back.profile_pic)
	ok(tex != null and tex.get_width() == ProfilePicture.SIZE and tex.get_height() == ProfilePicture.SIZE, "it is a square of SIZE")
	ok(not ProfilePicture.valid(PackedByteArray([1, 2, 3])), "junk bytes are refused")
	ProfilePicture.clear(h)
	ok(h.profile_pic.is_empty(), "the picture can be removed")
	# Alt+Q is its own binding, distinct from Q
	var k := InputEventKey.new()
	k.physical_keycode = KEY_Q
	k.alt_pressed = true
	var d := Settings.event_to_desc(k)
	ok(bool(d.get("alt", false)), "Alt is kept in the binding")
	var plain := InputEventKey.new()
	plain.physical_keycode = KEY_Q
	ok(not Settings._same_input(k, plain), "Alt+Q is not Q")
	ok((Settings.desc_to_event(d) as InputEventKey).alt_pressed, "and it reads back with Alt")
	ok(Settings.binding_text(&"quick_1").begins_with("Alt+"), "quick key 1 shows as Alt+...")
	eq(HeroData.BELT_SIZE, 6, "six belt keys")
	var hb := Game.new_hero(&"knight", "Belt")
	var old_save := hb.to_dict()
	old_save["belt"] = ["auto_heal", "auto_mana"]
	var loaded := HeroData.from_dict(old_save)
	eq(loaded.potion_belt.size(), 6, "an old two-slot belt loads into six")
	eq(loaded.potion_belt[3], &"", "new quick slots start empty")
	done()

func test_saved_accounts_remember_and_forget() -> void:
	var keep := SavedAccounts.path
	SavedAccounts.path = "user://test_accounts_bh030.dat"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SavedAccounts.path))
	var url := "https://10.0.0.5:8443"
	SavedAccounts.remember(url, "First_User", "a very long password", false)
	SavedAccounts.remember(url, "Second_User", "another long password", true)
	SavedAccounts.remember("https://other:8443", "Elsewhere", "", false)
	var mine := SavedAccounts.for_server(url)
	eq(mine.size(), 2, "two accounts for this server")
	eq(String(mine[0].userid), "Second_User", "the latest first")
	eq(String(mine[0].password), "another long password", "a remembered password comes back")
	eq(String(mine[1].password), "", "an unremembered password is never stored")
	var raw := FileAccess.get_file_as_bytes(SavedAccounts.path).get_string_from_ascii()
	ok(not raw.contains("another long password"), "the file is encrypted")
	SavedAccounts.remember(url, "second_user", "", false)
	eq(SavedAccounts.for_server(url).size(), 2, "the same UserID is updated, not duplicated")
	eq(String(SavedAccounts.for_server(url)[0].password), "", "unticking Remember password forgets it")
	SavedAccounts.forget(url, "First_User")
	eq(SavedAccounts.for_server(url).size(), 1, "forget removes it")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SavedAccounts.path))
	SavedAccounts.path = keep
	done()
