extends Node
## bh-016 evidence run (real renderer, real boot scene with HUD): skill / talent levels to 25, the Guild House from the
## plaza and inside, its conversation and the job boards.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh016.tscn -- --class=knight --slot=97 --out=<dir>
## Optional --only=levels,house,jobs

var args := {}
var out := ""
var main: Node
var p: Player
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-016/evidence/shots")))
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
	if _want("levels"):
		await _levels()
	if _want("house"):
		await _house()
	if _want("jobs"):
		await _jobs()
	print("BH016 CAPTURE DONE -> ", out)
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
	print("BH016 SHOT ", label)

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

func _levels() -> void:
	var h := Game.hero
	h.progress.level = 40
	h.progress.skill_points = 30
	h.progress.talent_points = 30
	for id in [&"cleave", &"shield_bash", &"leap_slam", &"whirlwind"]:
		h.skill_tree.ranks[id] = 1
	h.skill_tree.ranks[&"cleave"] = 25
	h.skill_tree.ranks[&"shield_bash"] = 12
	h.skill_tree.ranks[&"leap_slam"] = 5
	h.skill_tree.ranks[&"whirlwind"] = 3
	h.talent_tree.ranks[&"k_str"] = 25
	h.talent_tree.ranks[&"k_sword"] = 9
	h.talent_tree.ranks[&"k_crit"] = 3
	h.skill_tree.changed.emit()
	h.talent_tree.changed.emit()
	Game.ui_root.open(&"skills")
	await _shot("levels_skills", 20)
	Game.ui_root.close_all()
	Game.ui_root.open(&"talents")
	await _shot("levels_talents", 20)
	Game.ui_root.close_all()

func _house() -> void:
	await _go(&"sanctuary", &"start")
	p.teleport_to(Vector3(-6.0, 0.2, -1.5))
	await _wait(40)
	await _shot("house_plaza_view", 20)
	p.teleport_to(Vector3(-11.0, 0.2, -2.6))
	await _wait(40)
	await _shot("house_door", 20)
	await _door(&"int_guildhouse", &"start")
	await _shot("house_inside_entrance", 20)
	p.teleport_to(Vector3(0.0, 0.2, 0.8))
	await _wait(40)
	await _shot("house_inside_middle", 20)
	# the steward's conversation
	for n in get_tree().get_nodes_in_group(&"npc"):
		if n is Npc and n.def.id == &"hollis":
			p.teleport_to(n.global_position + Vector3(0, 0, 1.6))
			await _wait(20)
			Events.talk_requested.emit(n)
			await _wait(90)
			await _shot("house_steward_talk", 10)
			Game.ui_root.close_all()
			break

func _jobs() -> void:
	var h := Game.hero
	h.progress.level = 8
	h.inventory.gold = 1200
	if Game.current_map_id != &"int_guildhouse":
		await _door(&"int_guildhouse", &"start")
	Game.ui_root.open_guild_jobs(&"lantern")
	await _shot("jobs_lantern_not_member", 20)
	Game.ui_root.close_all()
	GuildRules.join(h, &"swordfin")
	Game.ui_root.open_guild_jobs(&"swordfin")
	await _shot("jobs_swordfin_member", 20)
	var b := GuildJobs.board(h, &"swordfin")
	GuildJobs.accept(h, &"swordfin", int(b[0].id))
	GuildJobs.accept(h, &"swordfin", int(GuildJobs.board(h, &"swordfin")[0].id))
	var j: Dictionary = GuildJobs.active(h)[0]
	j.progress = int(j.goal)
	Events.guild_jobs_changed.emit()
	await _shot("jobs_accepted_one_done", 20)
	Game.ui_root.open_guild_jobs(&"lantern")
	await _shot("jobs_lantern_tab", 20)
	GuildJobs.claim(h, int(j.id))
	Game.ui_root.open_guild_jobs(&"swordfin")
	await _shot("jobs_after_claim", 20)
	Game.ui_root.close_all()
