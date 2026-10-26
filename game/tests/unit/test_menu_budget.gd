extends TestCase
## Efficiency menus must not construct a gameplay map before a player can choose Play.

func _init() -> void:
	strict = true

func _nodes(root: Node) -> Array[Node]:
	var nodes: Array[Node] = [root]
	for child in root.get_children():
		nodes.append_array(_nodes(child))
	return nodes

func test_efficiency_backdrop_has_no_gameplay_dependencies() -> void:
	var prior := Settings.efficiency_mode
	Settings.efficiency_mode = true
	var world := Node3D.new()
	host.add_child(world)
	var menu := MainMenu.new()
	menu.build_backdrop(world)
	ok(menu._backdrop_lite, "the Efficiency path is selected")
	eq(menu._heroes.size(), 1, "only one character is loaded for the menu stage")
	eq(menu._heroes[0].appearance.model, HeroModels.MODELS[&"knight"], "the preview uses the selected Knight class model")
	ok(menu._heroes[0]._weapon_nodes.has(&"main"), "the stage preview carries its starter weapon")
	ok(menu._heroes[0]._weapon_nodes.has(&"off"), "the stage preview carries its starter shield")
	var nodes := _nodes(menu.backdrop)
	ok(nodes.size() <= 192, "the menu stage has a bounded node budget")
	var lights := 0
	for node in nodes:
		ok(not node is MapRoot, "no gameplay map is built for Efficiency menus")
		ok(not node is Actor, "no gameplay actor is built for Efficiency menus")
		ok(not node is CollisionObject3D, "the visual stage has no collision objects")
		ok(not node is NavigationRegion3D, "the visual stage has no navigation mesh")
		ok(not node is GPUParticles3D and not node is CPUParticles3D, "the stage has no particle simulation")
		if node is Light3D:
			lights += 1
			ok(not (node as Light3D).shadow_enabled, "the stage adds no shadow pass")
	eq(lights, 1, "the small scene has one light")
	ok(menu._cam.far <= 60.0, "the mobile stage camera has a short draw range")
	menu.dispose_backdrop()
	await host.get_tree().process_frame
	eq(world.get_child_count(), 0, "disposing removes every stage node")
	eq(menu._heroes.size(), 0, "disposing clears the preview references")
	eq(menu._cam, null, "disposing clears the camera reference")
	menu.free()
	world.free()
	Settings.efficiency_mode = prior
	done()

func test_desktop_backdrop_keeps_four_class_models() -> void:
	var prior := Settings.efficiency_mode
	Settings.efficiency_mode = false
	var world := Node3D.new()
	host.add_child(world)
	var menu := MainMenu.new()
	menu.build_backdrop(world)
	ok(not menu._backdrop_lite, "the existing desktop backdrop remains selected")
	eq(menu._heroes.size(), 4, "desktop keeps the four class previews")
	for visual in menu._heroes:
		ok(HeroModels.is_role(String(visual.appearance.model)), "desktop uses a selected class model")
		ok(not visual.fallback, "the class model is imported and available")
	ok(menu.backdrop.get_children().any(func(node: Node) -> bool: return node is MapRoot), "desktop keeps the town backdrop")
	menu.dispose_backdrop()
	await host.get_tree().process_frame
	eq(world.get_child_count(), 0, "desktop teardown still removes the map and previews")
	menu.free()
	world.free()
	Settings.efficiency_mode = prior
	done()
