extends Node
## bh-030 crash hunt: a level 53 hero in the middle of a large pack, every area skill of the class cast over and over with
## no cooldowns (Game.debug_no_cooldowns) and infinite Mana, wearing the chain-reaction powers (Winter's, Frostbitten,
## Pyrelord's, Conductor's, Riftborn). Prints a heartbeat every second so a crash shows where it happened.
##   godot --headless --path game res://tests/tools/stress_aoe.tscn -- --class=mage --enemies=120 --seconds=60 [--waves=4]

var args := {}
var player: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var cls := StringName(args.get("class", "mage"))
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	Game.save_slot = 99
	Game.hero = Game.new_hero(cls, "Stress")
	Game.hero.progress.add_xp(XpCurve.total_xp_for_level(int(args.get("level", "53"))))
	Game.hero.progress.allocate_along_build(Game.hero.progress.free_points)
	for n in Game.hero.skill_tree.tree.nodes:
		Game.hero.skill_tree.ranks[n.id] = maxi(1, int(n.get("base_rank", 5)))
	Game.hero._skills_changed()
	_gear()
	await Game._begin_session(StringName(args.get("map", "ruined_forest")), &"start")
	player = Game.player as Player
	Game.god_mode = true
	Game.infinite_mana = true
	Game.debug_no_cooldowns = true
	Game.debug_one_hit = args.get("onehit", "1") == "1"
	var skills := []
	for n in Game.hero.skill_tree.tree.nodes:
		var s := DB.skill(n.id)
		if s and Game.hero.skill_rank(n.id) > 0 and not s.is_aura() and s.behavior != &"":
			skills.append(n.id)
	print("STRESS skills: ", skills)
	var seconds := float(args.get("seconds", "60"))
	var waves := int(args.get("waves", "4"))
	var t := 0.0
	var beat := 0.0
	var wave_t := 0.0
	var si := 0
	_spawn(int(args.get("enemies", "120")))
	var w := 1
	while t < seconds:
		await get_tree().physics_frame
		var d := get_physics_process_delta_time()
		t += d
		beat += d
		wave_t += d
		var enemies := get_tree().get_nodes_in_group(&"enemy").filter(func(e): return e.alive)
		if (enemies.size() < 15 or wave_t > 12.0) and w < waves:
			w += 1
			wave_t = 0.0
			_spawn(int(args.get("enemies", "120")))
		if not enemies.is_empty():
			player.aim_override = (enemies[randi() % enemies.size()] as Node3D).global_position
		if player.action == null or player.action.can_cancel():
			player._request(&"skill", skills[si % skills.size()])
			si += 1
		if beat >= 1.0:
			beat = 0.0
			print("BEAT t=%.0f wave=%d enemies=%d action=%s queued=%s alive=%s hp=%d pos=%s nodes=%d fps=%d orphans=%d" % [t, w, enemies.size(), player.action_kind if player.action else &"-", player._queued, player.alive, player.hp, player.global_position.round(), Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
				Engine.get_frames_per_second(), Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)])
	print("STRESS DONE")
	Game.in_session = false
	get_tree().quit(0)

func _gear() -> void:
	var h := Game.hero
	for pair in [[&"apprentice_robe", [&"m_embersoul"]], [&"linen_hood", [&"conductor"]], [&"silk_glove", [&"frostbite", &"a_frozen_explode"]],
			[&"bone_amulet", [&"pyre", &"a_crit_lightning", &"m_vampiric"]]]:
		var it := DB.make_item(pair[0], BH.Rarity.LEGENDARY, 53, 11)
		if it == null:
			continue
		for p in pair[1]:
			if DB.power(p) and not it.powers.has(String(p)):
				it.powers.append(String(p))
		h.equipment.equip(it, h.equipment.auto_slot(it), 300, {})

func _spawn(n: int) -> void:
	var defs := DB.enemies.values().filter(func(d): return not d.id in [&"boss_warden"] and not String(d.id).begins_with("boss"))
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	for i in n:
		var ang := TAU * float(i) / float(n)
		var r := 3.0 + 9.0 * float(i % 7) / 7.0
		var pos := player.global_position + Vector3(cos(ang) * r, 0.5, sin(ang) * r)
		Spawner.spawn_enemy(Game.current_map, defs[i % defs.size()], Game.hero.progress.level, [], pos, diff)
