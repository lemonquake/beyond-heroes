extends Node
## bh-028 evidence run (real renderer, real boot scene with HUD): the Sand Arena at Wyman Outpost.
## A level-50 hero with two Tempos walks down the lane, enters (the Tempos stay outside), fights the adventurers, falls,
## stands up at the gate, and walks out again (the Tempos rejoin).
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh028.tscn -- --class=knight --slot=97 --out=<dir>

var args := {}
var out := ""
var main: Node
var p: Player

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-028/evidence/shots")))
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
	var h := Game.hero
	var lvl := int(args.get("level", "50"))
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(lvl) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2028
	GuildSummons._gear_up(h, lvl, rng)
	for k in 2:
		var t := TempoData.new()
		t.uid = 9100 + k
		t.tempo_name = ["Corvane", "Ilsabet"][k]
		t.class_id = [&"swordsman", &"archer"][k]
		t.trait_id = &"valiant"
		t.skills = [DataTempos.tempo_class(t.class_id).signature]
		h.tempos.append(t)
	h.stats_dirty.emit()
	Game.ui_root.close_all()
	await _go(&"wyman_outpost", &"west_road")
	var arena := ArenaGrounds.active()
	print("BH028 arena ", arena != null, " fighters ", arena.fighters().size() if arena else -1)
	# the lane, with the companions
	_place(arena.gate + arena.gate_out * 9.0, arena.center)
	await _wait(150)
	await _shot("01_lane_with_companions")
	# in through the gate
	_place(arena.gate + (arena.center - arena.gate).normalized() * 5.0, arena.center)
	await _wait(240)
	_report("inside")
	await _shot("02_inside_rivals_close_in")
	await _overhead(arena, "03_overhead_free_for_all")
	await _wait(300)
	_report("fighting")
	await _shot("04_mid_fight")
	await _overhead(arena, "05_overhead_companions_waiting_outside", arena.gate + arena.gate_out * 4.0, 34.0)
	# a fall, and up again at the gate
	p.hp = 1.0
	p.die(arena.fighters()[0] if not arena.fighters().is_empty() else null)
	await _wait(30)
	print("BH028 death_screen_open ", Game.ui_root.pause_menu.visible)
	await _shot("06_fallen_in_the_arena")
	await _wait(int(ArenaGrounds.RESPAWN_DELAY * 60.0) + 20)
	print("BH028 after_fall alive=%s hp=%d/%d at_gate=%.1f m inside=%s" % [p.alive, p.hp, p.max_hp(), p.global_position.distance_to(arena.gate), arena.contains(p.global_position)])
	await _shot("07_stood_up_at_the_gate")
	# and out again
	_place(arena.gate + arena.gate_out * 9.0, arena.gate + arena.gate_out * 20.0)
	await _wait(200)
	_report("outside")
	await _shot("08_out_companions_rejoin")
	print("BH028 CAPTURE DONE -> ", out)
	get_tree().quit()

func _place(at: Vector3, look: Vector3) -> void:
	var spot := CombatQuery.ground_at(p.get_world_3d(), at + Vector3.UP * 2.0)
	var d := (look - at).slide(Vector3.UP)
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()

func _report(tag: String) -> void:
	var arena := ArenaGrounds.active()
	var fs := arena.fighters().map(func(f): return "%s L%d %s %.0f%%%s" % [f.display_name, f.level, f.hero.cls.id, f.hp_frac() * 100.0,
		" (falling back)" if f.mode == Tempo.Mode.RETREAT else ""])
	var ts := TempoParty.actors().map(func(t): return "%s waiting=%s %.1fm from gate" % [t.data.tempo_name, t.is_waiting(), t.global_position.distance_to(arena.gate)])
	print("BH028 %s player L%d hp %d/%d in_arena=%s | fighters %s | tempos %s" % [tag, Game.hero.progress.level, p.hp, p.max_hp(), p.is_arena_hero(), fs, ts])

func _overhead(arena: ArenaGrounds, label: String, target := Vector3.INF, dist := 46.0) -> void:
	var cam := Camera3D.new()
	Game.current_map.add_child(cam)
	var t := arena.center if target == Vector3.INF else target
	cam.fov = 50.0
	cam.global_position = t + Vector3(0, dist * 0.82, dist * 0.57)
	cam.look_at(t, Vector3.UP)
	var prev := get_viewport().get_camera_3d()
	cam.make_current()
	await _shot(label, 12)
	if prev:
		prev.make_current()
	cam.queue_free()

func _wait(frames := 10) -> void:
	for i in frames:
		await get_tree().process_frame

func _shot(label: String, frames := 8) -> void:
	await _wait(frames)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH028 SHOT ", label)

func _go(map_id: StringName, spawn: StringName) -> void:
	Game.travel(map_id, spawn)
	await _wait(5)
	for i in 1200:
		await get_tree().process_frame
		if not Game.travelling and Game.current_map_id == map_id:
			break
	await _wait(60)
