extends Node
## Enemy review captures with the real renderer: the roster line-up, material hit bursts (blood, bone, stone,
## Aether, shadow), deaths chosen by the killing blow, blood pools, and the corpse decay stages.
##   tools/render.sh --resolution 1600x900 res://tests/tools/capture_enemies.tscn -- --out=<dir> [--only=lineup|hits|decay]
## Uses the town plaza as a lit, flat stage; enemies are frozen in place (no player, AI idle).

var out := ""
var cam: Camera3D
var dummy: Node3D
var enemies := {}

const ROSTER := [&"hollow_soldier", &"bonewarden", &"grave_archer", &"aether_sentinel", &"boss_warden",
	&"ashen_cultist", &"ashen_acolyte", &"ghoul_brute", &"shade_stalker",
	&"bandit_cutthroat", &"bandit_marksman", &"goblin_skulker", &"orc_reaver", &"ogre_crusher", &"dire_wolf", &"aether_wisp"]

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", "/tmp/claude-0/enemy_shots"))
	var only := String(args.get("only", ""))
	DirAccess.make_dir_recursive_absolute(out)
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "Capture")
	h.init_new()
	Game.hero = h
	Game.load_map(&"sanctuary")
	cam = Camera3D.new()
	Game.current_map.add_child(cam)
	cam.far = 300.0
	cam.make_current()
	dummy = Node3D.new()
	Game.current_map.add_child(dummy)
	await _frames(5)
	if only == "" or only == "lineup":
		await _lineup()
	if only == "" or only == "hits":
		await _hits_and_deaths()
	print("CAPTURE DONE")
	get_tree().quit()

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _shot(name: String, frames := 6) -> void:
	await _frames(frames)
	var img := get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
	print("SHOT ", name)

func _look(target: Vector3, dist: float, pitch: float, yaw := 0.0, fov := 40.0) -> void:
	cam.fov = fov
	var off := Vector3(0, 0, dist).rotated(Vector3.RIGHT, -deg_to_rad(pitch)).rotated(Vector3.UP, deg_to_rad(yaw))
	cam.global_position = target + off
	cam.look_at(target, Vector3.UP)

func _spawn(id: StringName, pos: Vector3, yaw := 0.0) -> Enemy:
	var e := Spawner.spawn_enemy(Game.current_map, DB.enemy(id), 5, [], pos, DataEnemies.DIFFICULTY[1])
	e.patrol_radius = 0.0
	e.rotation.y = deg_to_rad(yaw)
	e.set_physics_process(false)          # frozen pose: animation only
	enemies[id] = e
	return e

func _clear() -> void:
	for e in enemies.values():
		if is_instance_valid(e):
			e.queue_free()
	enemies.clear()
	Enemy._corpses.clear()

func _lineup() -> void:
	var row1 := ROSTER.slice(0, 8)
	var row2 := ROSTER.slice(8)
	for i in row1.size():
		_spawn(row1[i], Vector3(-15.0 + i * 4.3, 0, 12.0), 0.0)
	for i in row2.size():
		_spawn(row2[i], Vector3(-15.0 + i * 4.3, 0, 19.0), 0.0)
	await _frames(30)
	_look(Vector3(0, 1.5, 15.5), 36.0, 30.0, 0.0, 42.0)
	await _shot("enemies_lineup", 10)
	# closer views, left and right halves of each row (gameplay-like pitch)
	_look(Vector3(-8.5, 1.4, 12.0), 15.0, 22.0, 0.0, 45.0)
	await _shot("enemies_row1_left")
	_look(Vector3(8.5, 1.8, 12.0), 15.0, 22.0, 0.0, 45.0)
	await _shot("enemies_row1_right")
	_look(Vector3(-8.5, 1.4, 19.0), 15.0, 22.0, 0.0, 45.0)
	await _shot("enemies_row2_left")
	_look(Vector3(8.5, 1.8, 19.0), 15.0, 22.0, 0.0, 45.0)
	await _shot("enemies_row2_right")
	_clear()
	await _frames(5)

func _req(amount: float, knock := 3.0, crit := false) -> DamageRequest:
	var r := DamageRequest.new()
	r.kind = DamageRequest.Kind.ATTACK
	var st := TestCase.blank_stats(10)
	st.values[&"crit_chance"] = 1.0 if crit else 0.0
	st.values[&"accuracy_chance"] = 1.0
	r.attacker = st
	r.base_min = amount
	r.base_max = amount
	r.knockback = knock
	r.evadable = false
	r.blockable = false
	return r

func _hits_and_deaths() -> void:
	var ids := [&"bandit_cutthroat", &"goblin_skulker", &"orc_reaver", &"ghoul_brute", &"hollow_soldier", &"aether_sentinel", &"shade_stalker", &"ashen_cultist"]
	for i in ids.size():
		var e := _spawn(ids[i], Vector3(-10.5 + i * 3.0, 0, 14.0), 0.0)
		e.set_physics_process(true)
		e.brain.go(EnemyBrain.State.IDLE)
	await _frames(20)
	dummy.global_position = Vector3(0, 1, 26.0)
	_look(Vector3(0, 1.0, 14.0), 16.0, 30.0, 0.0, 48.0)
	# material hit bursts: one strong hit each, captured mid-spray
	for id in ids:
		var e: Enemy = enemies[id]
		e.invulnerable = false
		e.receive_hit(_req(4.0, 1.0, true), dummy, e.center())
	await _shot("hits_materials", 4)
	# killing blows: heavy knockback (thrown back), crit (forward), plain
	var k := 0
	for id in ids:
		var e: Enemy = enemies[id]
		var heavy := k % 3 == 0
		e.receive_hit(_req(9999.0, 12.0 if heavy else 2.0, k % 3 == 1), dummy, e.center())
		k += 1
	await _shot("deaths_t0_3s", 18)
	await get_tree().create_timer(1.4).timeout
	await _shot("deaths_t1_5s", 2)
	await get_tree().create_timer(5.0).timeout
	await _shot("deaths_pools_t6s", 2)
	_look(Vector3(-6, 0.5, 14.0), 9.0, 45.0, 0.0, 45.0)
	await _shot("deaths_pools_close", 4)
	# decay stages on whatever corpses remain (fast-forward the fresh stage)
	for e in enemies.values():
		if is_instance_valid(e) and not e.alive:
			e._decay()
	await get_tree().create_timer(5.0).timeout
	_look(Vector3(0, 1.0, 14.0), 16.0, 30.0, 0.0, 48.0)
	await _shot("decay_t5s", 2)
	await get_tree().create_timer(4.5).timeout
	await _shot("decay_dissolving", 2)
	await get_tree().create_timer(3.0).timeout
	await _shot("decay_gone", 2)
	_clear()
