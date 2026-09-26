extends Node
## Real-game check of slash direction: the actual Player (real input, real attack chain) swings toward four aim
## points; a frame is saved right after each slash appears. Output: <out>/swing_<dir>.png
func _ready() -> void:
	var out := String(OS.get_cmdline_user_args()[0]) if not OS.get_cmdline_user_args().is_empty() else "/tmp"
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	Game.hero = Game.new_hero(&"knight", "SwingTest")
	Game.save_slot = 98
	await Game._begin_session(&"sanctuary", &"start")
	var p := Game.player as Player
	for i in 60:
		await get_tree().physics_frame
	var origin := p.global_position
	for d in [["north", Vector3(0, 0, -1)], ["east", Vector3(1, 0, 0)], ["south", Vector3(0, 0, 1)], ["west", Vector3(-1, 0, 0)]]:
		p.global_position = origin
		p.aim_override = origin + d[1] * 5.0
		for i in 40:
			await get_tree().physics_frame
		var before := FX.world.get_child_count()
		Input.action_press(&"primary")
		await get_tree().physics_frame
		Input.action_release(&"primary")
		# wait until the slash mesh exists, then a few frames for it to sweep
		for i in 60:
			await get_tree().physics_frame
			if FX.world.get_child_count() > before:
				var found := false
				for c in FX.world.get_children().slice(before):
					if c is MeshInstance3D and c.mesh is ArrayMesh:
						found = true
				if found:
					break
		for i in 4:
			await get_tree().process_frame
		var f := p.forward()
		print("SWING %s facing (%.2f, %.2f) aim (%.0f, %.0f)" % [d[0], f.x, f.z, d[1].x, d[1].z])
		get_viewport().get_texture().get_image().save_png(out.path_join("swing_%s.png" % d[0]))
		for i in 50:
			await get_tree().physics_frame
	Game.in_session = false
	get_tree().quit()
