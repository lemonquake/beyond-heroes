extends Node
## Evidence run for combat feedback: swing arcs following the facing, impact/flinch, finisher and heavy impacts,
## crit and skill damage numbers, skill-name banners, Knight skill choreography, and blocked-hit effects.
## Boots a knight straight into a map, clears the area, stands training dummies around the hero and drives the real
## Player actions (no input), capturing native screenshots at the effect moments.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_combat_fx.tscn -- --out=<dir>

var out := ""
var player: Player
var shots: Array = []
var _last_res: DamageResult

## Dummies never die: top them up every frame so every shot has a live, flinching target.
func _process(_d: float) -> void:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.alive and e.stats:
			e.hp = e.max_hp()

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/combat_fx")))
	DirAccess.make_dir_recursive_absolute(out)
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	Game.save_slot = 98
	Game.hero = Game.new_hero(&"knight", "Probe")
	Game.hero.progress.add_xp(20000)
	for sid in [&"cleave", &"shield_bash", &"leap_slam", &"whirlwind", &"war_cry", &"judgment", &"ground_fissure", &"iron_bulwark"]:
		Game.hero.skill_tree.ranks[sid] = 3
	await Game._begin_session(StringName(args.get("map", "ruined_forest")), &"start")
	player = Game.player as Player
	player.input_enabled = false
	Game.god_mode = true
	Events.damage_dealt.connect(func(t: Node, r: DamageResult, _p: Vector3, att: Node) -> void:
		if att == player or t == player:
			_last_res = r)
	await _frames(20)
	for e in get_tree().get_nodes_in_group(&"enemy"):
		e.queue_free()
	await _frames(5)
	await _run()
	print("COMBAT FX DONE ", shots.size(), " shots -> ", out)
	get_tree().quit()

func _dummy(id: StringName, offset: Vector3, frozen := true) -> Enemy:
	var def := DB.enemy(id)
	var e := Spawner.spawn_enemy(FX.world, def, maxi(1, player.level), [], player.global_position + offset, DataEnemies.DIFFICULTY[1])
	if frozen:
		e.set_physics_process(false)
	e.face_toward(player.global_position)
	return e

func _refill() -> void:
	player.mana = player.max_mana()
	player.hp = player.max_hp()
	player.cooldowns.clear()
	if player.resource:
		player.resource.gain(100.0)

func _clear_dummies() -> void:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		e.queue_free()
	await _frames(3)

func _run() -> void:
	# --- swing arcs must point where the hero faces (was always south) ---
	for d in [["north", Vector3(0, 0, -2.2)], ["east", Vector3(2.2, 0, 0)], ["southwest", Vector3(-1.6, 0, 1.6)]]:
		var e := _dummy(&"hollow_soldier", d[1])
		e.hp = 99999.0
		player.aim_override = player.global_position + d[1] * 2.0
		await _frames(8)
		player._face_aim_now()
		player._start_light()
		await _until(func() -> bool: return player.action != null and player.action.elapsed >= player.action.first_hit_time() + 0.07)
		await _shot("swing_%s" % d[0], 0)
		await _frames(40)
		await _clear_dummies()
	# --- impact + flinch on a normal hit, then the finisher combo hit ---
	var tgt := _dummy(&"hollow_soldier", Vector3(0, 0, -2.0))
	tgt.hp = 99999.0
	player.aim_override = tgt.global_position
	await _frames(6)
	for i in 4:
		player._start_light()
		await _until(func() -> bool: return player.action != null and player.action.elapsed >= player.action.first_hit_time() + 0.03)
		if i == 0:
			await _shot("hit_impact_flinch", 1)
		if i == 3:
			await _shot("finisher_impact", 2)
		await _until(func() -> bool: return player.action == null or player.action.in_combo_window())
	await _frames(40)
	# --- heavy attack impact ---
	player._start_heavy(0.0, false)
	await _until(func() -> bool: return player.action != null and player.action.elapsed >= player.action.first_hit_time() + 0.03)
	await _shot("heavy_impact", 2)
	await _frames(50)
	# --- critical hit number ---
	player._riposte_t = 5.0
	player._start_light()
	await _until(func() -> bool: return _last_res != null and _last_res.is_crit, 90)
	await _shot("crit_number", 6)
	player._riposte_t = 0.0
	await _frames(60)
	# --- Knight skills: banner at cast, then the landing moment ---
	for sid in [&"cleave", &"shield_bash", &"leap_slam", &"war_cry", &"judgment", &"ground_fissure", &"iron_bulwark"]:
		await _clear_dummies()
		var dist := 5.0 if sid in [&"leap_slam", &"judgment", &"ground_fissure", &"shield_bash"] else 2.0
		var a1 := _dummy(&"hollow_soldier", Vector3(0, 0, -dist))
		var a2 := _dummy(&"hollow_soldier", Vector3(1.2, 0, -dist + 0.4))
		a1.hp = 99999.0
		a2.hp = 99999.0
		player.aim_override = a1.global_position
		await _frames(10)
		player._face_aim_now()
		_refill()
		player._start_skill(sid)
		if player.action == null:
			print("COMBAT FX skill failed to start: ", sid, " ", player.skill_block_reason(sid))
			continue
		var act := player.action
		await _until(func() -> bool: return act.elapsed >= 0.16)
		await _shot("skill_%s_cast" % sid, 0)
		var hit_t := act.first_hit_time()
		await _until(func() -> bool: return act.elapsed >= hit_t + 0.05 or player.action != act, 240)
		await _shot("skill_%s_hit" % sid, 3)
		await _frames(70)
	# --- Whirlwind (channel) ---
	await _clear_dummies()
	_dummy(&"hollow_soldier", Vector3(0, 0, -1.8)).hp = 99999.0
	_dummy(&"hollow_soldier", Vector3(1.6, 0, 0.6)).hp = 99999.0
	_refill()
	player._start_skill(&"whirlwind")
	await _frames(40)
	await _shot("skill_whirlwind", 0)
	player._stop_channel()
	await _frames(40)
	# --- an enemy guarding against the hero's blows ---
	await _clear_dummies()
	var shield := _dummy(&"bonewarden", Vector3(0, 0, -2.0))
	shield.hp = 99999.0
	player.aim_override = shield.global_position
	await _frames(10)
	var got := false
	for i in 16:
		_last_res = null
		player._start_light()
		await _until(func() -> bool: return _last_res != null, 60)
		if _last_res != null and _last_res.blocked:
			await _shot("enemy_blocks", 2)
			got = true
			break
		await _until(func() -> bool: return player.action == null or player.action.in_combo_window())
		await _frames(10)
	if not got:
		print("COMBAT FX enemy never blocked")
	await _frames(40)
	# --- the hero guarding an enemy blow ---
	await _clear_dummies()
	var foe := _dummy(&"hollow_soldier", Vector3(0, 0, -1.8), false)
	foe.hp = 99999.0
	player.aim_override = foe.global_position
	player._face_aim_now()
	player._set_guard(true)
	player._guard_t = 10.0
	got = false
	for i in 600:
		_last_res = null
		await get_tree().physics_frame
		player.aim_override = foe.global_position
		if _last_res != null and _last_res.blocked:
			await _shot("hero_blocks", 2)
			got = true
			break
	if not got:
		print("COMBAT FX hero block not captured")
	player._set_guard(false)

func _until(cond: Callable, max_frames := 180) -> void:
	for i in max_frames:
		if cond.call():
			return
		await get_tree().process_frame

func _shot(label: String, wait_frames := 2) -> void:
	for i in wait_frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(label + ".png"))
	shots.append(label)
	print("COMBAT FX SHOT ", label)

func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame
