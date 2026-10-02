extends Node
## bh-031: what drawing monsters on the hero body costs. 60 humanoid monsters (AI frozen) stand around the camera
## on a real map, first on their old models, then as personas; frame time is averaged over 6 s each, and the time to
## set each monster up is measured.
##   godot --path game --resolution 1920x1080 res://tests/tools/bench_bh031.tscn [-- --count=60] [-- --lite=1]

var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	Game.save_slot = 99
	Game.hero = Game.new_hero(&"knight", "Bench")
	await Game._begin_session(&"ruined_forest", &"start")
	Game.god_mode = true
	Game.debug_freeze_ai = true
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var count := int(args.get("count", "60"))
	var ids := [&"bandit_cutthroat", &"hollow_soldier", &"ashen_cultist", &"orc_reaver", &"goblin_skulker", &"drowned_deckhand",
		&"bandit_marksman", &"forsaken_legionnaire", &"chain_bearer", &"wiresick_husk"]
	for mode in String(args.get("modes", "old,persona")).split(","):
		Persona.enabled = mode != "old"
		var t0 := Time.get_ticks_usec()
		var list := []
		var p: Node3D = Game.player
		for i in count:
			var e := Enemy.new()
			e.setup(DB.enemy(ids[i % ids.size()]), 20)
			Game.current_map.add_child(e)
			var a := TAU * float(i) / count
			e.global_position = p.global_position + Vector3(cos(a), 0, sin(a)) * (3.0 + float(i % 4) * 1.6)
			list.append(e)
			if mode == "noshape" or mode == "bare":
				for m in e.visual._meshes:
					if m.mesh:
						for k in m.mesh.get_blend_shape_count():
							m.set_blend_shape_value(k, 0.0)
			if mode == "noshadow" or mode == "bare":
				for m in e.visual._meshes:
					m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var setup_ms := float(Time.get_ticks_usec() - t0) / 1000.0
		for f in 60:
			await get_tree().process_frame
		var frames := 0
		var t1 := Time.get_ticks_usec()
		while Time.get_ticks_usec() - t1 < 6000000:
			await get_tree().process_frame
			frames += 1
		var ms := float(Time.get_ticks_usec() - t1) / 1000.0 / frames
		print("BENCH %s: %d monsters, setup %.1f ms (%.2f ms each), frame %.2f ms (%.0f fps), draw calls %d" % [mode, count, setup_ms,
			setup_ms / count, ms, 1000.0 / ms, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)])
		for e in list:
			e.queue_free()
		for f in 10:
			await get_tree().process_frame
	Persona.enabled = true
	get_tree().quit()
