extends TestCase
## bh-035: multiplayer interest management and compact snapshots, and the frame-time fixes for big fights.
##   - a hero or monster snapshot survives the packed form; a malformed packet decodes to nothing; an idle monster is
##     recognised as unchanged (the live relay and stream rates: server/integration_probe.py --stages bandwidth)
##   - spawning a character never rewrites the shared animation library (each write cleared every other character's
##     animation caches: ~75 ms on the frame after each humanoid spawn)
##   - crowd LOD thins only the monsters that are waiting in a big fight; animation stride steps the tree by hand
## Frame times: tests/tools/perf_probe.gd --stress=40 (see work/lemondev/bh-035).

const DT := 1.0 / 60.0

var _holder: Node3D

func _init() -> void:
	strict = true

func _arena() -> Node3D:
	_holder = Node3D.new()
	host.add_child(_holder)
	var floor_body := StaticBody3D.new()
	floor_body.collision_layer = BH.LAYER_GROUND | BH.LAYER_WORLD
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(80, 1, 80)
	cs.shape = box
	cs.position.y = -0.5
	floor_body.add_child(cs)
	_holder.add_child(floor_body)
	return _holder

func _spawn(id: StringName, at: Vector3) -> Enemy:
	return Spawner.spawn_enemy(_holder, DB.enemy(id), 2, [], at, DataEnemies.DIFFICULTY[1])

func _actor_state() -> Array:
	return [Vector3(12.5, 3.25, -40.125), 1.234, Vector3(3.5, -0.5, -2.25), 812.5, 1200.0, true, "slash_heavy", 4097, 1.25, true, false, 57]

func _monster_state(id: int) -> Array:
	return [id, Vector3(-3.0, 0.5, 9.75), -2.9, Vector3(0.0, 0.0, 4.0), 15000.0, 18000.0, "", 70000, 1.0, false, true, 250.0]

func test_actor_snapshot_round_trips_and_shrinks() -> void:
	var s := _actor_state()
	var bytes := NetCodec.pack_actor(s)
	var back := NetCodec.unpack_actor(bytes)
	eq(back.size(), 12, "twelve fields come back")
	ok((back[0] as Vector3).is_equal_approx(s[0]), "position is exact (32-bit floats)")
	ok(absf(float(back[1]) - 1.234) < 0.001, "yaw within a thousandth of a radian")
	ok((back[2] as Vector3).distance_to(s[2]) < 0.011, "velocity within a centimetre per second")
	eq(back[3], 812.5, "health")
	eq(back[4], 1200.0, "maximum health")
	eq(back[5], true, "alive flag")
	eq(back[6], "slash_heavy", "action name")
	eq(back[7], 4097, "action serial")
	ok(absf(float(back[8]) - 1.25) < 0.001, "action rate")
	eq(back[9], true, "loop flag")
	eq(back[10], false, "combat flag")
	eq(back[11], 57, "level")
	ok(NetGuard.ally_pack_ok([{"k": "p", "s": back}]), "the decoded state passes the host's checks")
	var before := var_to_bytes(s).size()
	ok(bytes.size() * 2 < before, "packed %d bytes vs %d as Variants" % [bytes.size(), before])
	done()

func test_monster_batch_round_trips() -> void:
	var states := []
	for i in 20:
		states.append(_monster_state(100 + i))
	var blob := NetCodec.pack_monsters(states)
	ok(blob.size() < 1300, "twenty monsters fit one unfragmented packet (%d bytes)" % blob.size())
	var back := NetCodec.unpack_monsters(blob)
	eq(back.size(), 20, "every monster decodes")
	eq(back[3][0], 103, "ids keep their order")
	eq(back[0][4], 15000.0, "health")
	eq(back[0][11], 250.0, "shield")
	eq(back[0][10], true, "engaged flag")
	eq(back[0][7], 70000 & 0xFFFF, "serial wraps at 16 bits (compared only for change)")
	done()

func test_malformed_packets_decode_to_nothing() -> void:
	var good := NetCodec.pack_monsters([_monster_state(1), _monster_state(2)])
	eq(NetCodec.unpack_monsters(good.slice(0, good.size() - 3)).size(), 1, "a cut-off batch keeps only whole monsters")
	eq(NetCodec.unpack_monsters(PackedByteArray([255, 255])).size(), 0, "an absurd count is refused")
	eq(NetCodec.unpack_monsters("nonsense").size(), 0, "a wrong type is refused")
	eq(NetCodec.unpack_actor(PackedByteArray([1, 2, 3])).size(), 0, "a short hero snapshot is refused")
	var wire := NetCodec.pack_allies([{"k": "p", "s": _actor_state(), "n": "Ana"}])
	eq(NetCodec.unpack_allies(wire).size(), 1, "an ally pack round-trips")
	eq(NetCodec.unpack_allies(wire)[0].n, "Ana", "with its name")
	eq(NetCodec.unpack_allies([{"k": "p", "s": _actor_state()}]).size(), 0, "the old unpacked form is refused")
	eq(NetCodec.unpack_allies([{"k": "p", "b": PackedByteArray([0])}]).size(), 0, "a broken entry spoils the pack")
	var nan_state := _actor_state()
	nan_state[0] = Vector3(NAN, 0, 0)
	var nan_pack := NetCodec.unpack_allies(NetCodec.pack_allies([{"k": "p", "s": nan_state}]))
	ok(not NetGuard.ally_pack_ok(nan_pack), "a NaN position still fails the host's checks after decoding")
	done()

func test_idle_monsters_are_not_resent() -> void:
	var a := _monster_state(5)
	var b := a.duplicate()
	ok(not Net.enemy_changed(a, b), "an identical state is idle")
	b[1] = (a[1] as Vector3) + Vector3(0.01, 0, 0)
	ok(not Net.enemy_changed(a, b), "a centimetre of drift is not worth a packet")
	b[1] = (a[1] as Vector3) + Vector3(0.05, 0, 0)
	ok(Net.enemy_changed(a, b), "five centimetres is")
	b = a.duplicate()
	b[4] = 14999.0
	ok(Net.enemy_changed(a, b), "any health change is sent")
	b = a.duplicate()
	b[7] = 70001
	ok(Net.enemy_changed(a, b), "a new action is sent")
	b = a.duplicate()
	b[2] = float(a[2]) + 0.05
	ok(Net.enemy_changed(a, b), "a visible turn is sent")
	done()

func test_rates_and_protocol() -> void:
	ok(Net.PROTOCOL >= 19, "bh-035 packets need protocol 19 (%d)" % Net.PROTOCOL)
	ok(Net.ENEMY_KEEPALIVE < Net.GONE_AFTER * 0.5, "an idle monster is refreshed well before its replica would expire")
	ok(Net.ENEMY_FAR < Net.ENEMY_RANGE, "far monsters are still streamed")
	ok(Net.ALLY_AWAY_EVERY > Net.ALLY_FAR_EVERY, "other maps get the slimmest rate")
	done()

func test_spawning_leaves_the_shared_animations_alone() -> void:
	_arena()
	var first := _spawn(&"bandit_cutthroat", Vector3.ZERO)          # the first of a model may set its clips' loop modes
	var lib := first.visual.anim_player.get_animation_library(&"")
	var writes := [0]
	var count := func() -> void: writes[0] += 1
	var watched: Array = []
	for an in lib.get_animation_list():
		var clip := lib.get_animation(an)
		clip.changed.connect(count)
		watched.append(clip)
	for i in 3:
		_spawn(&"bandit_cutthroat", Vector3(3.0 * i, 0, 4))
	eq(writes[0], 0, "three more spawns wrote nothing to the %d shared clips" % watched.size())
	for clip in watched:
		clip.changed.disconnect(count)
	_holder.free()
	done()

func test_crowd_lod_thins_only_waiting_monsters() -> void:
	_arena()
	var e := _spawn(&"bandit_cutthroat", Vector3(0, 0.2, 0))
	var boss_def: EnemyDef = DB.enemy(&"bandit_cutthroat").duplicate()
	boss_def.archetype = &"boss"
	var boss := Spawner.spawn_enemy(_holder, boss_def, 2, [], Vector3(6, 0.2, 0), DataEnemies.DIFFICULTY[1])
	for i in 20:
		await host.get_tree().physics_frame
	var S := EnemyBrain.State
	var saved_n := Enemy._awake_n
	Enemy._awake_n = 40
	e.brain.state = S.POSITION
	e.velocity = Vector3.ZERO
	e.knock_velocity = Vector3.ZERO
	ok(e.is_on_floor(), "the monster stands on the arena floor")
	ok(e._crowd_half(), "in a crowd, a monster circling for a token is thinned")
	e.brain.state = S.ATTACK
	ok(not e._crowd_half(), "an attacking monster always runs every step")
	e.brain.state = S.STAGGER
	ok(not e._crowd_half(), "a staggered one too")
	e.brain.state = S.POSITION
	e.knock_velocity = Vector3(5, 0, 0)
	ok(not e._crowd_half(), "a knocked-back one too")
	e.knock_velocity = Vector3.ZERO
	boss.brain.state = S.POSITION
	ok(not boss._crowd_half(), "a boss is never thinned")
	Enemy._awake_n = 4                         # below the threshold on desktop and in efficiency mode (half of it)
	ok(not e._crowd_half(), "a small fight is never thinned")
	Enemy._awake_n = 40
	# a thinned monster thinks on every other call (each monster alternates on its own, so hand-stepped tests still work)
	var skipped := 0
	for i in 6:
		e.brain.state = S.POSITION              # its own thinking may move it on; keep it waiting for the count
		Enemy._awake_n = 40                     # a full step rebuilds the neighbour grid, which counts this small arena
		e._physics_process(DT)
		if e._lod_acc > 0.0:
			skipped += 1
	eq(skipped, 3, "a thinned monster thinks on every other step and coasts on the rest")
	Enemy._awake_n = saved_n
	_holder.free()
	done()

func test_animation_stride_steps_the_tree_by_hand() -> void:
	_arena()
	var e := _spawn(&"bandit_cutthroat", Vector3.ZERO)
	var v := e.visual
	ok(v.crowd_lod, "an ordinary monster may animate at a coarser rate in a crowd")
	v.set_anim_stride(3)
	eq(v.tree.callback_mode_process, AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL, "a coarse tree is stepped by hand")
	var advanced := 0
	for i in 6:
		var acc := v._anim_acc
		v._step_anim(DT)
		if v._anim_acc < acc + DT * 0.5:
			advanced += 1
	eq(advanced, 2, "every third frame it advances by the time that passed")
	v.set_anim_stride(1)
	eq(v.tree.callback_mode_process, AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_IDLE, "back to every frame")
	eq(v._anim_acc, 0.0, "nothing left owed")
	var bdef: EnemyDef = DB.enemy(&"bandit_cutthroat").duplicate()
	bdef.archetype = &"boss"
	var boss := Spawner.spawn_enemy(_holder, bdef, 2, [], Vector3(5, 0, 0), DataEnemies.DIFFICULTY[1])
	ok(not boss.visual.crowd_lod, "a boss always animates every frame")
	_holder.free()
	done()
