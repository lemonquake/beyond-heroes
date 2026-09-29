extends Node
## bh-017 evidence run (real renderer, real boot scene with HUD): the trade rows of the three towns, the new buffs and
## debuffs on the HUD, weapon Enchantment and Fore-Tech, the guild name and banner, and the Quake Team.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh017.tscn -- --class=knight --slot=97 --out=<dir>
## Optional --only=rows,status,upgrade,guild,quake,drops

var args := {}
var out := ""
var main: Node
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-017/evidence/shots")))
	only = String(args.get("only", "")).split(",", false)
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
	if _want("rows"):
		await _rows()
	if _want("status"):
		await _status()
	if _want("upgrade"):
		await _upgrade()
	if _want("guild"):
		await _guild()
	if _want("quake"):
		await _quake()
	if _want("drops"):
		_drops()
	print("BH017 CAPTURE DONE -> ", out)
	get_tree().quit()

func _want(k: String) -> bool:
	return only.is_empty() or only.has(k)

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 8) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH017 SHOT ", label)

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

func _at(x: float, z: float) -> void:
	p.teleport_to(Game.current_map.to_global(Vector3(x, 0.3, z)))

func _rows() -> void:
	await _go(&"sanctuary", &"start")
	_at(14.8, 8.0)
	await _wait(50)
	await _shot("row_sanctuary_from_plaza", 20)
	_at(14.8, 13.5)
	await _wait(50)
	await _shot("row_sanctuary_gate", 20)
	_at(14.8, 19.0)
	await _wait(50)
	await _shot("row_sanctuary_middle", 20)
	_at(14.8, 27.0)
	await _wait(50)
	await _shot("row_sanctuary_south", 20)
	# a merchant at the counter
	_at(11.0, 15.0)
	await _wait(40)
	await _shot("row_sanctuary_goods_stand", 15)
	_at(11.0, 25.0)
	await _wait(40)
	await _shot("row_sanctuary_arms_stand", 15)
	_at(18.6, 20.0)
	await _wait(40)
	await _shot("row_sanctuary_alchemy_stand", 15)
	await _go(&"olivar", &"start")
	_at(-5.2, 13.0)
	await _wait(50)
	await _shot("row_olivar_gate", 20)
	_at(-5.2, 22.0)
	await _wait(50)
	await _shot("row_olivar_middle", 20)
	await _go(&"wyman_outpost", &"start")
	_at(4.0, 11.5)
	await _wait(50)
	await _shot("row_wyman_gate", 20)
	_at(4.0, 20.0)
	await _wait(50)
	await _shot("row_wyman_middle", 20)

func _status() -> void:
	await _go(&"sanctuary", &"start")
	_at(0.0, 10.0)
	await _wait(30)
	for id in [&"vigor", &"keen", &"windstep", &"titan", &"spirit_ward"]:
		p.status.apply(id, 40.0)
	for id in [&"grievous", &"enfeebled", &"dazzled", &"sundered", &"demoralized"]:
		p.status.apply(id, 40.0)
	p.status.apply(&"grievous", 40.0)
	p.mark_stats_dirty()
	await _shot("status_bar_all_ten", 40)
	# hover text is a tooltip; also show the wounded hero not healing as much
	p.hp = p.max_hp() * 0.5
	var h0 := p.hp
	p.heal(100.0, false)
	print("BH017 heal under two Grievous Wounds: +%d of 100" % roundi(p.hp - h0))
	for id in [&"vigor", &"keen", &"windstep", &"titan", &"spirit_ward", &"grievous", &"enfeebled", &"dazzled", &"sundered", &"demoralized"]:
		p.status.remove(id)

func _upgrade() -> void:
	var h := Game.hero
	h.progress.level = 20
	h.inventory.gold = 20000
	for pair in [[&"iron_shard", 60], [&"steel_ingot", 12], [&"orc_tusk", 8], [&"ember_core", 12], [&"frost_crystal", 6], [&"arcane_dust", 30],
			[&"wisp_mote", 10], [&"champion_essence", 3], [&"ogre_sinew", 3], [&"rune_plate", 3]]:
		var it := DB.make_item(pair[0], BH.Rarity.COMMON, 1, 3)
		it.count = int(pair[1])
		h.inventory.add(it)
	var w := DB.make_item(&"sunsteel_blade", BH.Rarity.ELITE, 20, 5)
	h.inventory.add(w)
	h.equip_from_inventory(w, &"main_weapon")
	await _go(&"sanctuary", &"start")
	_at(19.4, 21.0)
	await _wait(40)
	Game.ui_root.open_crafting(&"alchemy", "Alchemy Table")
	await _wait(10)
	var cw := Game.ui_root.window(&"crafting") as CraftingWindow
	cw._tabs.current_tab = 2
	cw._show_page()
	await _shot("upgrade_enchant_page", 20)
	WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy")
	WeaponUpgrades.apply(h, w, WeaponUpgrades.ENCHANT, &"flame", &"alchemy")
	cw._show_page()
	await _shot("upgrade_enchant_rank2", 20)
	Game.ui_root.close_all()
	Game.ui_root.open_crafting(&"forge", "Forge")
	await _wait(10)
	cw._tabs.current_tab = 3
	cw._show_page()
	for i in 3:
		WeaponUpgrades.apply(h, w, WeaponUpgrades.FORETECH, &"serrate", &"forge")
	cw._show_page()
	await _shot("upgrade_foretech_page", 20)
	Game.ui_root.close_all()
	Game.ui_root.open(&"inventory")
	await _wait(10)
	var slot: ItemSlot = null
	for n in Game.ui_root.find_children("*", "ItemSlot", true, false):
		if (n as ItemSlot).item == w:
			slot = n
			break
	if slot:
		TooltipLayer.show_for(slot, func() -> Control: return Tips.item(w, {"hero": h}))
		await _shot("upgrade_weapon_tooltip", 20)
	Game.ui_root.close_all()

func _guild() -> void:
	var h := Game.hero
	h.inventory.gold = 2000
	await _go(&"sanctuary", &"start")
	if h.guild == &"":
		GuildRules.join(h, &"swordfin")
	await _wait(100)
	await _shot("guild_open_naming_invite", 20)
	Game.ui_root.close_all()
	GuildRules.set_alias(h, "The Lemon Legion")
	var img := Image.create(400, 600, false, Image.FORMAT_RGBA8)
	for y in 600:
		for x in 400:
			var t := float(y) / 600.0
			img.set_pixel(x, y, Color(0.95 - 0.5 * t, 0.7 - 0.3 * t + 0.2 * sin(float(x) * 0.05), 0.1 + 0.6 * t, 1.0))
	for cy in range(200, 400):
		for cx in range(120, 280):
			if Vector2(cx - 200, cy - 300).length() < 80.0:
				img.set_pixel(cx, cy, Color(1.0, 0.95, 0.4, 1.0))
	GuildRules.set_banner(h, img)
	Game.ui_root.open(&"guild_custom")
	await _shot("guild_custom_window", 20)
	Game.ui_root.close_all()
	await _door(&"int_guildhouse", &"start")
	p.teleport_to(Game.current_map.to_global(Vector3(0.0, 0.3, 0.6)))
	await _wait(40)
	await _shot("guild_house_banner", 20)
	Game.ui_root.open(&"character")
	await _shot("guild_character_window", 20)
	Game.ui_root.close_all()

func _quake() -> void:
	var h := Game.hero
	h.progress.level = 14
	h.inventory.gold = 500
	await _go(&"sanctuary", &"start")
	_at(0.0, 10.0)
	await _wait(30)
	for i in 3:
		var line := Cheats.apply("quake team", h, p)
		print("BH017 ", line)
		await _wait(20)
	await _shot("quake_team_called", 40)
	for m in h.quake_team:
		(m as QuakeMate).hero.inventory.gold = 3500
	_at(14.8, 12.0)
	await _wait(200)
	await _shot("quake_team_shopping_1", 10)
	await _wait(300)
	await _shot("quake_team_shopping_2", 10)
	await _wait(400)
	await _shot("quake_team_shopping_3", 10)
	for m in h.quake_team:
		var mm := m as QuakeMate
		print("BH017 ally ", mm.display_name(), " ", mm.hero.cls.id, " gold ", mm.hero.inventory.gold, " rating ", QuakeBrain.rating(mm.hero), " tempos ", mm.hero.tempos.size())
	# out to fight
	await _go(&"westreach", &"town_gate")
	await _wait(120)
	await _shot("quake_team_westreach", 20)
	await _go(&"ruined_forest", &"arrival")
	await _wait(200)
	await _shot("quake_team_forest_fight", 20)

func _drops() -> void:
	var r := RandomNumberGenerator.new()
	r.seed = 17
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var fit := 0
		var tot := 1000
		for i in tot:
			var b := ItemGenerator.random_base(r, 18, [], cls)
			if b and ItemGenerator.class_fit(b, cls):
				fit += 1
		print("BH017 drops %s: %.1f%% class gear" % [cls, 100.0 * fit / tot])
