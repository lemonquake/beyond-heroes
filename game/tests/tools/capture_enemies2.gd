extends Node
## bh-010 evidence: every new monster in-engine at the gameplay camera, plus a few mechanic moments (the Mimic asleep
## and awake, the Rune Golem's three core colours, a lit powder keg, a War Totem, spiderlings).
## Boots a knight into a real map on a probe save slot (never 0-2), clears the camps and stands each monster in front
## of the hero, idling (and once mid-attack).
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_enemies2.tscn -- --slot=95 --out=<dir> [--map=ruined_forest] [--only=<id>]

const NEW := [&"necromancer", &"goblin_summoner", &"orc_shaman", &"frost_revenant", &"plague_bloater", &"bandit_bombardier",
	&"mire_troll", &"rune_golem", &"broodmother", &"treasure_mimic", &"spiderling", &"war_totem"]

var out := ""
var player: Player
var shots: Array = []

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var slot := int(args.get("slot", "95"))
	if slot < 93 or slot > 99:
		push_error("capture_enemies2 must run on a probe slot (93-99), got %d" % slot)
		get_tree().quit(2)
		return
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-010/evidence/enemies_runtime")))
	DirAccess.make_dir_recursive_absolute(out)
	var only := String(args.get("only", ""))
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	Game.save_slot = slot
	Game.hero = Game.new_hero(&"knight", "Probe")
	Game.hero.progress.add_xp(8000)
	await Game._begin_session(StringName(args.get("map", "ruined_forest")), &"start")
	player = Game.player as Player
	player.input_enabled = false
	Game.god_mode = true
	await _frames(20)
	await _clear()
	for id in NEW:
		if only != "" and only != String(id):
			continue
		await _portrait(id)
	if only == "":
		await _lineup()
	print("ENEMIES2 DONE ", shots.size(), " shots -> ", out)
	get_tree().quit()

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _shot(name: String, frames := 8) -> void:
	await _frames(frames)
	var img := get_viewport().get_texture().get_image()
	var p := out.path_join(name + ".png")
	img.save_png(p)
	shots.append(p)
	print("SHOT ", p)

func _clear() -> void:
	for e in get_tree().get_nodes_in_group(&"enemy") + get_tree().get_nodes_in_group(&"corpse"):
		e.queue_free()
	await _frames(3)

func _spawn(id: StringName, offset: Vector3, frozen := true) -> Enemy:
	var e := Spawner.spawn_enemy(FX.world, DB.enemy(id), maxi(1, player.level), [], CombatQuery.ground_at(player.get_world_3d(), player.global_position + offset), DataEnemies.DIFFICULTY[1])
	e.patrol_radius = 0.0
	if frozen:
		e.set_physics_process(false)
	e.face_toward(player.global_position)
	return e

## In front of the hero toward the camera's view (the gameplay camera looks down the -Z / +Z axis of the map).
func _front(dist: float, side := 0.0) -> Vector3:
	var cam := get_viewport().get_camera_3d()
	var f := Vector3(0, 0, -1)
	if cam:
		f = (cam.global_position - player.global_position).slide(Vector3.UP).normalized()
		if f.length() < 0.1:
			f = Vector3(0, 0, 1)
	var right := f.cross(Vector3.UP)
	return f * dist + right * side

func _portrait(id: StringName) -> void:
	var e := _spawn(id, _front(3.2))
	await _frames(40)
	await _shot("enemy_%s_idle" % id)
	var d: EnemyDef = e.def
	match id:
		&"treasure_mimic":
			e.set_physics_process(true)
			e.ext.wake(player)
			await _frames(12)
			await _shot("enemy_treasure_mimic_wake", 0)
			await _frames(40)
			e.visual.play_action(&"mimic_tongue")
			await _frames(10)
			await _shot("enemy_treasure_mimic_tongue", 0)
		&"rune_golem":
			for i in 2:
				e.ext.shift_rune()
				await _frames(20)
				await _shot("enemy_rune_golem_%s" % String(Elements.KEYS[e.ext.rune_element()]))
		&"bandit_bombardier":
			e.ext.light_fuse()
			await _frames(20)
			await _shot("enemy_bandit_bombardier_lit_fuse")
		&"plague_bloater":
			e.hp = e.max_hp() * 0.3
			e.ext.swell()
			await _frames(20)
			await _shot("enemy_plague_bloater_swelling")
		&"war_totem":
			e.ext.pulse()
			await _frames(6)
			await _shot("enemy_war_totem_pulse", 0)
		_:
			if not d.attacks.is_empty():
				var a: Dictionary = d.attacks[0]
				var t := e.visual.play_action(a.anim)
				await _frames(maxi(4, int(t * 30.0)))
				await _shot("enemy_%s_attack" % id, 0)
	e.queue_free()
	await _frames(4)

func _lineup() -> void:
	var list := NEW.duplicate()
	var made: Array = []
	for i in list.size():
		var row := i / 6
		var col := i % 6
		made.append(_spawn(list[i], _front(4.5 + row * 4.0, -8.0 + col * 3.2)))
	await _frames(60)
	await _shot("enemies2_lineup", 10)
	for e in made:
		if is_instance_valid(e):
			e.queue_free()
