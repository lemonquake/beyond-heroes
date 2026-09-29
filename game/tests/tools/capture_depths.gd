extends Node
## Renderer smoke test; launch with --class=knight --level=50 --map=dg_warren_8 --slot=94 --starter=0.

func _ready() -> void:
	_run.call_deferred()

func shot(label: String) -> void:
	for i in 20:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://../output/depth-" + label + ".png")

func _run() -> void:
	add_child(load("res://src/main.gd").new())
	for i in 2000:
		await get_tree().process_frame
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
	assert(Game.in_session)
	Game.god_mode = true
	var map := Game.current_map
	var sp := Spawner.current()
	assert(sp != null and sp.spawned.size() >= 30)
	var guardian: Enemy
	for e in sp.spawned:
		if e.has_meta(&"depth_guardian"):
			guardian = e
	assert(guardian != null and guardian.elite_mods.size() == 3)
	var camera := Camera3D.new()
	map.add_child(camera)
	camera.far = 400.0
	camera.fov = 45.0
	var target := guardian.global_position
	camera.position = target + Vector3(8, 13, 18)
	camera.look_at(target)
	camera.make_current()
	await get_tree().create_timer(4.0).timeout
	await shot("guardian")
	camera.position = Vector3(0, 75, 49)
	camera.look_at(Vector3.ZERO)
	camera.make_current()
	await shot("floor")
	for e in sp.camps[DataDungeons.SEAL_ZONE].duplicate():
		if is_instance_valid(e) and e.alive:
			e.die(Game.player)
	await get_tree().process_frame
	assert(Game.hero.world_flags.get(DataDungeons.seal_flag(&"warren", 8), false))
	var chests := map.find_children("Chest_*", "Node3D", true, false)
	for chest in chests:
		if chest is TreasureChest:
			assert(not chest.guardian_alive())
	print("DEPTH RENDER PASS: named guardian, 3 abilities, populated floor, real kills open exit and treasure")
	get_tree().quit()
