extends TestCase
## Townspeople and interiors: NPC data is consistent, every NPC stands on the ground after map changes (the floating
## townsfolk regression: returning from the forest used to leave them metres in the air), and every interior can be
## entered and left through its doors any number of times without duplicating maps, players, NPCs or Tempos.

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _tree() -> SceneTree:
	return host.get_tree()

func _frames(n := 2) -> void:
	for i in n:
		await _tree().physics_frame

## A real session in miniature: a world holder, a fresh hero and a real Player (NPCs and Tempos only populate for one).
func _begin() -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "NpcTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "NpcTest")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player

func _load(id: StringName, spawn: StringName) -> MapRoot:
	var m := Game.load_map(id, spawn)
	if _player.hero == null:
		_player.bind(Game.hero)
	return m

func _end() -> void:
	for t in TempoParty.actors(_tree()):
		t.free()
	if is_instance_valid(_player):
		if _player.get_parent():
			_player.get_parent().remove_child(_player)
		_player.free()
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

func _interior_ids() -> Array:
	var out := []
	for d in DataMaps.interiors():
		out.append(d.id)
	return out

func _npcs_in(map: MapRoot) -> Array:
	return _tree().get_nodes_in_group(&"npc").filter(func(n): return n is Npc and map.is_ancestor_of(n))

func _doors_in(map: MapRoot) -> Array:
	return _tree().get_nodes_in_group(&"door").filter(func(n): return n is DoorPortal and map.is_ancestor_of(n))

func _door_to(map: MapRoot, dest: StringName) -> DoorPortal:
	for d in _doors_in(map):
		if d.destination_map == dest:
			return d
	return null

## Height of an NPC above whatever is under its feet (a short ray from its hips; INF when nothing is there).
func _ground_gap(n: Node3D) -> float:
	var from := n.global_position + Vector3.UP * 1.0
	var q := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 4.0, BH.LAYER_GROUND | BH.LAYER_WORLD)
	var hit := n.get_world_3d().direct_space_state.intersect_ray(q)
	if hit.is_empty():
		return INF
	return n.global_position.y - hit.position.y

func _check_grounded(map: MapRoot, where: String) -> void:
	var npcs := _npcs_in(map)
	for n in npcs:
		var gap := _ground_gap(n)
		ok(absf(gap) < 0.1, "%s: %s stands on the ground (gap %.2f m)" % [where, n.def.id, gap])

# ------------------------------------------------------------------------------------------------------------

func test_data() -> void:
	var interiors := _interior_ids()
	eq(interiors.size(), 9, "nine interiors (bh-016: the Guild House)")
	for id in interiors:
		var d := DB.map_def(id)
		ok(d != null and d.interior and d.is_town and d.parent_map == &"sanctuary", "%s is a town interior of sanctuary" % id)
	var names := {}
	for n in DB.npcs.values():
		ok(DB.map_def(n.map) != null, "%s lives on a real map (%s)" % [n.id, n.map])
		ok(not names.has(n.display_name), "%s has a unique name" % n.display_name)
		names[n.display_name] = true
		for s in n.services:
			ok(DialogueBox.SERVICES.has(s), "%s service %s is known" % [n.id, s])
		for node in n.graph.get("nodes", {}).values():
			for c in node.get("choices", []):
				for a in c.get("actions", []):
					if a.has("service"):
						ok(DialogueBox.SERVICES.has(StringName(a.service)), "%s dialogue service %s is known" % [n.id, a.service])
			for a in node.get("actions", []):
				if a.has("service"):
					ok(DialogueBox.SERVICES.has(StringName(a.service)), "%s dialogue service %s is known" % [n.id, a.service])
	# every interior has somebody at home
	for id in interiors:
		ok(DB.npcs.values().any(func(n): return n.map == id), "%s has at least one resident" % id)
	done()

func test_npcs_stand_on_ground_after_travel() -> void:
	_begin()
	Game.hero.world_flags[&"catacombs_ritual_seen"] = true    # the Hooded Stranger joins the market
	_load(&"ruined_forest", &"start")
	await _frames(3)
	var town := _load(&"sanctuary", &"waypoint")
	await _frames(2)
	var npcs := _npcs_in(town)
	ok(npcs.size() >= 7, "town NPCs populated (%d)" % npcs.size())
	_check_grounded(town, "town after the forest")
	# and once more through a door and back, the path the bug report took
	for id in _interior_ids():
		var room := _load(id, &"start")
		await _frames(2)
		ok(room.spawns.has(&"start"), "%s has a start spawn" % id)
		ok(not _npcs_in(room).is_empty(), "%s has its residents" % id)
		_check_grounded(room, id)
	town = _load(&"sanctuary", &"waypoint")
	await _frames(2)
	_check_grounded(town, "town after the interiors")
	_end()
	done()

func test_door_cycles() -> void:
	_begin()
	var town := _load(&"sanctuary", &"waypoint")
	# two bound Tempos travel along: none may be duplicated by the door swaps
	Game.hero.inventory.gold = 100000
	TempoRules.roster(Game.hero)
	ok(TempoRules.hire(Game.hero, 0) != null and TempoRules.hire(Game.hero, 1) != null, "two Tempos bound")
	TempoParty.refresh(Game.hero)
	await _frames(2)
	var interiors := _interior_ids()
	for id in interiors:
		ok(_door_to(town, id) != null, "sanctuary has a door into %s" % id)
		ok(town.spawns.has(StringName("door_%s" % id)), "sanctuary has the spawn door_%s" % id)
	for d in _doors_in(town):
		ok(DB.map_def(d.destination_map) != null, "town door -> real map %s" % d.destination_map)
	for cycle in 3:
		for id in interiors:
			var door := _door_to(Game.current_map, id)
			if door == null:
				ok(false, "cycle %d: no door into %s" % [cycle, id])
				continue
			var in_spawn := door.destination_spawn
			var room := _load(door.destination_map, in_spawn)
			await _frames(2)
			eq(Game.current_map_id, id, "entered %s" % id)
			near(_player.global_position.distance_to(room.spawn_transform(in_spawn).origin), 0.05, 0.1,
				"player on %s/%s" % [id, in_spawn])
			var want := DB.npcs.values().filter(func(n): return n.map == id and NpcDirectory.is_present(n, Game.hero)).size()
			eq(_npcs_in(room).size(), want, "%s has exactly its residents" % id)
			var exit := _door_to(room, &"sanctuary")
			ok(exit != null, "%s has an exit to the street" % id)
			if exit == null:
				continue
			eq(exit.destination_spawn, StringName("door_%s" % id), "%s exit leads to its own front door" % id)
			ok(not exit.entering, "%s exit is marked as leaving" % id)
			var out_spawn := exit.destination_spawn
			town = _load(exit.destination_map, out_spawn)
			await _frames(2)
			near(_player.global_position.distance_to(town.spawn_transform(out_spawn).origin), 0.05, 0.1,
				"back on sanctuary/%s" % out_spawn)
	await _frames(1)
	eq(_holder.get_children().filter(func(c): return not c.is_queued_for_deletion()).size(), 1, "exactly one map loaded")
	eq(_tree().get_nodes_in_group(&"player").size(), 1, "exactly one player")
	var ids := {}
	for n in _npcs_in(Game.current_map):
		ok(not ids.has(n.def.id), "NPC %s not duplicated" % n.def.id)
		ids[n.def.id] = true
	eq(TempoParty.actors(_tree()).size(), TempoRules.active(Game.hero).size(), "one actor per standing Tempo")
	_end()
	done()
