extends Node
## Real renderer smoke check, using scratch save slot 96 only.

var out := "res://../output/progression-visual"

func _ready() -> void:
	_run.call_deferred()

func _frames(count: int) -> void:
	for i in count:
		await get_tree().process_frame

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("CAPTURE ", name)

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var main := load("res://src/main.gd").new() as Node
	add_child(main)
	for i in 2000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	assert(Game.in_session, "Session started")
	var h := Game.hero
	h.progress.allocate(&"str", 58)
	h.progress.allocate(&"dex", 29)
	h.inventory.gold = 100000
	GuildRules.join(h, &"swordfin")
	h.world_flags[&"mq_maelis_orders"] = true
	h.guild_jobs["done"] = 2
	assert(GuildRules.promote(h) == "")
	var weapon := DB.make_item(&"gravewatch_longsword", BH.Rarity.ELITE, 30, 2201)
	h.inventory.add(weapon)
	assert(h.equip_from_inventory(weapon, &"main_weapon") == "")
	Game.player.ensure_stats()
	await get_tree().create_timer(6.0).timeout
	Game.ui_root.close_all()
	Game.ui_root.open(&"character")
	await _frames(40)
	await _shot("character-and-rank")
	Game.ui_root.close_all()
	await Game.travel(&"olivar", &"start")
	await _frames(40)
	# Check Paul David is in the live town and his special plate is visible.
	var actor: Node3D
	for npc in get_tree().get_nodes_in_group(&"npc"):
		if npc.def.id == &"paul_david":
			actor = npc
	assert(actor != null, "Paul David is present in Olivar")
	Game.player.teleport_to(actor.global_position + Vector3(0, 0.2, 3))
	await _frames(50)
	await _shot("paul-david-in-olivar")
	await Game.travel(&"weeping_causeway", &"start")
	await _frames(50)
	Game.god_mode = true
	var boss := StoryDirector.map_boss(&"kethrax") as Enemy
	assert(boss != null, "Kethrax spawns in the real map")
	Game.player.teleport_to(boss.global_position + Vector3(-5, 0.2, 0))
	Game.set_world_flag(&"kethrax_intro_seen")
	await _frames(20)
	assert(CutscenePlayer.is_playing(), "Boss introduction runs")
	CutscenePlayer.active.skip_all()
	await _frames(5)
	assert(not Game.in_cutscene, "Input returned after intro")
	var hp := boss.hp
	var req := DamageRequest.new()
	req.attacker = Game.player.stats
	req.evadable = false
	req.can_crit = false
	boss.receive_hit(req, Game.player)
	assert(boss.hp < hp and boss.alive, "Boss survives a real weapon hit")
	await _frames(10)
	await _shot("kethrax-fight")
	boss.die(Game.player)
	await get_tree().create_timer(3.0).timeout
	assert(h.world_flags.get(&"boss_kethrax_defeated", false), "Victory saved to story")
	assert(CutscenePlayer.is_playing(), "Victory cutscene runs")
	assert(CutscenePlayer.active.cutscene.id == &"chain_breaks")
	CutscenePlayer.active.skip_all()
	await _frames(5)
	assert(not Game.in_cutscene, "Victory returns input")
	print("PROGRESSION RENDER SMOKE PASS")
	get_tree().quit()
