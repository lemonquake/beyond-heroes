extends TestCase

func _init() -> void:
	strict = true

func test_both_bridges_walkable_in_both_directions() -> void:
	var script: GDScript = load("res://src/world/maps/westreach.gd")
	if "--bridge-baseline" in OS.get_cmdline_user_args():
		script = GDScript.new()
		script.source_code = FileAccess.get_file_as_string("res://src/world/maps/westreach.gd").replace("for bridge: Vector2 in [BRIDGE, FEN_BRIDGE]:", "for bridge: Vector2 in []:")
		script.reload()
	var builder = script.new()
	var map: MapRoot = builder.build(DB.map_def(&"westreach"))
	host.add_child(map)
	var nav := MapBuilder.isolate_navigation(map)
	MapBuilder.bake_navigation(map)
	var p := Player.new()
	p.name = "BridgeWalker"
	map.add_child(p)
	p.bind(Game.new_hero(&"knight", "Bridge QA"))
	p.set_physics_process(false)
	p.collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	for bridge: Vector2 in [builder.BRIDGE, builder.FEN_BRIDGE]:
		for dir in [-1.0, 1.0]:
			for lane in [-0.7, 0.0, 0.7]:
				var start := Vector3(bridge.x - dir * 9.5, builder.ground(bridge.x - dir * 9.5, bridge.y + lane) + 0.08, bridge.y + lane)
				p.teleport_to(start)
				for i in 400:
					await host.get_tree().physics_frame
					p.physics_move(1.0 / 60.0, Vector3(dir * 4.0, 0, 0))
					if (p.global_position.x - bridge.x) * dir >= 9.0:
						break
				var crossed: bool = (p.global_position.x - bridge.x) * dir >= 9.0
				ok(crossed, "bridge %s direction %.0f lane %.1f: actual player reached %s" % [bridge, dir, lane, p.global_position])
				if not crossed:
					for i in p.get_slide_collision_count():
						var col := p.get_slide_collision(i)
						print("BRIDGE blocked by %s normal=%s point=%s" % [col.get_collider().get_path(), col.get_normal(), col.get_position()])
		var a := Vector3(bridge.x - 10.0, builder.ground(bridge.x - 10.0, bridge.y), bridge.y)
		var b := Vector3(bridge.x + 10.0, builder.ground(bridge.x + 10.0, bridge.y), bridge.y)
		var path := NavigationServer3D.map_get_path(nav, a, b, true)
		ok(not path.is_empty() and path[-1].distance_to(b) < 1.0, "companions can path across %s" % bridge)
	map.free()
	NavigationServer3D.free_rid(nav)
	done()
