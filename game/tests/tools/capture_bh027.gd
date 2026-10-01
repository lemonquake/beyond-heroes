extends Node
## bh-027 evidence run (real renderer, real boot scene with HUD): the Guild window's pages, founding a guild, the Guild
## House inside and out (the great banner), Showcase, a guild's page, the player menu and the new accessories.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh027.tscn -- --class=knight --slot=97 --out=<dir>

var args := {}
var out := ""
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-027/evidence/shots")))
	DirAccess.make_dir_recursive_absolute(out)
	main = load("res://src/main.gd").new()
	main.name = "Main"
	add_child(main)
	for i in 1500:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	await _wait(60)
	p = Game.player as Player
	Game.god_mode = true
	var h := Game.hero
	h.progress.add_xp(XpCurve.total_xp_for_level(20))
	h.inventory.gold = 120000
	Game.ui_root.close_all()
	await _guild_window_unfounded()
	await _found(h)
	await _guild_pages(h)
	await _house(h)
	await _showcase(h)
	await _accessories(h)
	print("BH027 CAPTURE DONE -> ", out)
	get_tree().quit()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 8) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH027 SHOT ", label)

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1200:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _door(map_id: StringName, spawn: StringName) -> void:
	Game.door_travel(map_id, spawn)
	await _wait(5)
	for i in 1200:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)

func _guild_window_unfounded() -> void:
	var w := Game.ui_root.window(&"guild") as GuildWindow
	w._form = {"name": "The Unbroken Oaks", "motto": "From ash, we rise.", "info": "We hunt the Hollow, keep the south roads open and bring the lost home. Every class welcome; Guild Wars on Fridays.",
		"style": {"field": "1a5c6b", "metal": 0, "crest": "tree", "division": "chevron"}}
	Game.ui_root.open_guild("found")
	await _shot("guild_found_page", 20)
	Game.ui_root.open_guild("guilds")
	await _shot("guild_all_guilds", 20)
	Game.ui_root.close_all()

func _found(h: HeroData) -> void:
	OwnGuild.found(h, "The Unbroken Oaks", "From ash, we rise.", "We hunt the Hollow, keep the south roads open and bring the lost home. Every class welcome; Guild Wars on Fridays.",
		{"field": "1a5c6b", "metal": 0, "crest": "tree", "division": "chevron"})
	await _wait(200)
	for i in 6:
		OwnGuild.recruit(h)
	OwnGuild.add_renown(h, 9000.0)
	for id in [&"sharpened_steel", &"iron_discipline", &"war_chest", &"rallying_cry", &"shield_wall"]:
		OwnGuild.upgrade(h, id)
	h.own_guild.treasury = 840.0
	Game.ui_root.close_all()

func _guild_pages(h: HeroData) -> void:
	for pg in ["overview", "members", "passives", "war", "summon"]:
		Game.ui_root.open_guild(pg)
		await _shot("guild_%s" % pg, 20)
	Game.ui_root.close_all()
	var res := GuildSummons.call_to_arms(h, p)
	print("BH027 call: ", res.text)
	await _wait(60)
	p.teleport_to(p.global_position + Vector3(0, 0.1, 0))
	await _shot("call_to_arms_in_world", 40)

func _house(h: HeroData) -> void:
	await _go(&"sanctuary", &"start")
	p.teleport_to(Vector3(-2.0, 0.2, 5.0))
	await _wait(60)
	await _shot("house_great_banner", 30)
	p.teleport_to(Vector3(-6.0, 0.2, 2.0))
	await _wait(40)
	await _shot("house_great_banner_close", 30)
	await _door(&"int_guildhouse", &"start")
	await _shot("house_inside_entrance", 20)
	p.teleport_to(Vector3(0.0, 0.2, 4.8))
	await _wait(40)
	await _shot("house_inside_board", 20)
	p.teleport_to(Vector3(0.0, 0.2, -1.0))
	await _wait(40)
	await _shot("house_inside_featured", 20)
	p.teleport_to(Vector3(-9.0, 0.2, 2.0))
	await _wait(40)
	await _shot("house_inside_west_counters", 20)
	Game.ui_root.open_guild_jobs(&"")
	await _shot("quest_board_central", 20)
	Game.ui_root.close_all()
	for n in get_tree().get_nodes_in_group(&"interactable"):
		if n is GuildCounter and String(n.slot) == "npc_1":
			n.interact(p)
			break
	await _shot("guild_detail_npc", 20)
	Game.ui_root.close_all()
	for n in get_tree().get_nodes_in_group(&"npc"):
		if n is Npc and n.def.id == &"hollis":
			p.teleport_to(n.global_position + Vector3(0, 0, 1.6))
			await _wait(20)
			Events.talk_requested.emit(n)
			await _wait(120)
			await _shot("steward_featured", 10)
			Game.ui_root.close_all()
			break

func _showcase(h: HeroData) -> void:
	var other := Game.new_hero(&"mage", "Ilyra")
	other.progress.add_xp(XpCurve.total_xp_for_level(22))
	for id in [&"star_pendant", &"twinmoon_band", &"spirit_bell"]:
		var it := DB.make_item(id, BH.Rarity.ELITE, 22, hash(id))
		other.equipment.equip(it, other.equipment.auto_slot(it), 22, other.progress.base_attributes())
	other.guild = &"lantern"
	other.tier = 3
	var theirs := Net.showcase_pack(other)
	for id in [&"kingsguard_crown_ring", &"sunforged_medallion", &"wolfclaw_torc"]:
		var it := DB.make_item(id, BH.Rarity.MASTER, 20, hash(id))
		h.equipment.equip(it, h.equipment.auto_slot(it), 20, h.progress.base_attributes())
	Game.ui_root.open_showcase(Net.showcase_pack(h), theirs)
	await _shot("showcase", 90)
	var w := Game.ui_root.window(&"guild_detail") as GuildDetailWindow
	w.show_guild(ShowcaseWindow._as_info(Net.showcase_pack(h).guild), GuildRegistry.banner(h, h.guild))
	await _shot("guild_detail_own", 20)
	Game.ui_root.close_all()
	var saved := Net.peers
	Net.peers = {1: {"name": h.hero_name}, 2: {"name": "Ilyra", "cls": "mage", "level": 22, "guild": Net.guild_profile(other)}}
	PlayerMenu.open_for(Game.ui_root._root, 2, Vector2(820, 380))
	await _shot("player_menu", 12)
	for n in Game.ui_root._root.get_children():
		if n is PlayerMenu:
			n.queue_free()
	Net.peers = saved

func _accessories(h: HeroData) -> void:
	await _go(&"ruined_forest", &"start")
	var at := p.global_position + Vector3(0, 0, 3)
	var i := 0
	for id in DataAccessories.ids():
		var it := DB.make_item(id, [BH.Rarity.ADVANCED, BH.Rarity.ELITE, BH.Rarity.MASTER, BH.Rarity.MYTHICAL][i % 4], 30, i + 1)
		Loot.spawn_item(it, at, TAU * float(i) / 20.0, 1.2 + 0.5 * float(i % 3))
		i += 1
	Settings.loot_labels_always = true
	await _wait(90)
	await _shot("accessories_on_the_ground", 30)
	for id in DataAccessories.ids():
		h.inventory.add(DB.make_item(id, BH.Rarity.ELITE, 30, hash(id)))
	Game.ui_root.open(&"inventory")
	await _shot("accessories_in_the_bag", 30)
	Game.ui_root.close_all()
