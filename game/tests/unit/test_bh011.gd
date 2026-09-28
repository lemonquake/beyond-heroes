extends TestCase
## bh-011: waypoints are interactables (the touch Interact button could not use them), monsters spawn on the real ground
## (camps used their marker's height: under the Ruined Forest bridge, inside the tower mound, where they fell out of
## the world and paid the hero experience on arrival), and the potion belt binds Q / E to any consumable.

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _begin(map_id: StringName, spawn: StringName = &"start") -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "Bh011World"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Belter")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(map_id, spawn)
	_player.bind(Game.hero)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame

func _end() -> void:
	for t in TempoParty.actors(host.get_tree()):
		t.free()
	for n in host.get_tree().get_nodes_in_group(&"loot"):
		n.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

# ---- waypoints ------------------------------------------------------------------------------------------------

func test_waypoint_is_an_interactable_the_hero_can_use() -> void:
	await _begin(&"sanctuary", &"waypoint")
	var t := Game.current_map.teleporter(&"sanctuary_waypoint")
	ok(t != null, "the town waypoint exists")
	ok(t.is_in_group(&"interactable"), "the waypoint joins the interactable group (touch Interact reaches it)")
	_player.teleport_to(t.arrival_point())
	await host.get_tree().physics_frame
	ok(_player.find_interact_target() == t, "standing on the dais, the hero's interact target is the waypoint")
	ok(t.interact_text().begins_with("Travel to"), "single destination prompt: %s" % t.interact_text())
	Game.hero.awakened_shrines[&"cove_shrine"] = true
	ok(t.interact_text().begins_with("Use Waypoint"), "several destinations prompt: %s" % t.interact_text())
	ok(t.interact_text().length() <= 26, "the prompt fits the touch button without cutting")
	ok(t.get_script().get_script_method_list().all(func(m): return m.name != "_unhandled_input"),
		"the waypoint no longer listens for a raw key event of its own (a second path would double-activate)")
	_end()
	done()

func test_locked_dais_is_not_offered() -> void:
	await _begin(&"catacombs", &"entrance")
	var t := Game.current_map.teleporter(&"catacombs_exit")
	ok(t != null and t.is_locked(), "the catacombs exit starts sealed")
	ok(not t.can_interact(_player), "a sealed dais offers no Interact")
	_end()
	done()

# ---- monster placement ----------------------------------------------------------------------------------------

func test_camps_stand_on_the_ground_not_their_marker_height() -> void:
	await _begin(&"ruined_forest", &"arrival")
	var space := Game.current_map.get_world_3d().direct_space_state
	var checked := 0
	for e: Enemy in host.get_tree().get_nodes_in_group(&"enemy"):
		if e.zone == null or not (String(e.zone.name) in ["EnemyZone_bridge", "EnemyZone_tower"]):
			continue
		checked += 1
		var from := e.global_position + Vector3.UP * 8.0
		var q := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 40.0, BH.LAYER_GROUND | BH.LAYER_WORLD)
		var hit := space.intersect_ray(q)
		ok(not hit.is_empty(), "%s has ground under it" % e.name)
		if not hit.is_empty():
			near(e.global_position.y, hit.position.y, 1.2, "%s (%s) stands on the surface under it" % [e.name, e.zone.name])
	ok(checked >= 6, "bridge and tower camps were checked (%d monsters)" % checked)
	_end()
	done()

func test_a_monster_that_falls_on_its_own_pays_nothing() -> void:
	await _begin(&"ruined_forest", &"arrival")
	var e: Enemy = host.get_tree().get_nodes_in_group(&"enemy")[0]
	var xp0 := Game.hero.progress.total_xp
	var died := [false]
	var cb := func(a: Node, _k: Node) -> void:
		if a == e:
			died[0] = true
	Events.actor_died.connect(cb)
	e.global_position = Vector3(e.global_position.x, -45.0, e.global_position.z)
	e._fell_out()
	Events.actor_died.disconnect(cb)
	ok(not died[0] and e.alive, "it is not killed by the fall")
	ok(e.global_position.y > -10.0, "it is put back at its camp (y %.1f)" % e.global_position.y)
	eq(Game.hero.progress.total_xp, xp0, "no experience for a fall nobody caused")
	_end()
	done()

# ---- potion belt ----------------------------------------------------------------------------------------------

func test_belt_defaults_bind_and_save() -> void:
	var h := Game.new_hero(&"mage", "Belt")
	eq(h.potion_belt[0], HeroData.BELT_AUTO_HEAL, "Q drinks the strongest health draught by default")
	eq(h.potion_belt[1], HeroData.BELT_AUTO_MANA, "E drinks the strongest mana draught by default")
	h.set_belt(0, &"frost_flask")
	h.set_belt(1, &"rejuvenation_elixir")
	eq(h.potion_belt[0], &"frost_flask", "any consumable can go on Q")
	var back := HeroData.from_dict(h.to_dict())
	eq(back.potion_belt[0], &"frost_flask", "the belt survives a save")
	eq(back.potion_belt[1], &"rejuvenation_elixir", "both slots survive a save")
	h.set_belt(1, &"no_such_item")
	eq(h.potion_belt[1], HeroData.BELT_AUTO_MANA, "an unknown item restores the default")
	h.set_belt(0, &"sage_staff")
	eq(h.potion_belt[0], HeroData.BELT_AUTO_HEAL, "equipment cannot go on the belt")
	var old := h.to_dict()
	old.erase("belt")
	eq(HeroData.from_dict(old).potion_belt[0], HeroData.BELT_AUTO_HEAL, "old saves get the default belt")
	done()

func test_belt_key_uses_the_bound_item() -> void:
	await _begin(&"sanctuary")
	var h := Game.hero
	var tonic := DB.make_item(&"swiftfoot_tonic", BH.Rarity.COMMON, 1, 7)
	tonic.count = 2
	h.inventory.add(tonic)
	h.inventory.add(DB.make_item(&"greater_mana_potion", BH.Rarity.COMMON, 1, 1))
	h.set_belt(0, &"swiftfoot_tonic")
	var hp_before := h.inventory.count_of(&"health_potion")
	ok(_player.use_belt(0), "Q uses the Swiftfoot Tonic bound to it")
	eq(h.inventory.count_of(&"swiftfoot_tonic"), 1, "one tonic was used")
	eq(h.inventory.count_of(&"health_potion"), hp_before, "no health draught was drunk instead")
	ok(_player.status.has(&"elixir_swift"), "the tonic's buff is on")
	eq(h.belt_preview(0).count, 1, "the belt shows the tonics left")
	_player.mana = 0.0
	ok(_player.use_belt(1), "E (auto) drinks a mana draught")
	eq(h.inventory.count_of(&"greater_mana_potion"), 0, "auto takes the strongest mana draught first")
	h.inventory.consume(&"swiftfoot_tonic", 1)
	ok(not _player.use_belt(0), "an empty bound slot does nothing")
	_end()
	done()
