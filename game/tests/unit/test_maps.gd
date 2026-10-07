extends TestCase
## Maps, teleporters and the environment kit: every map builds, every teleporter points at a real map + spawn,
## spawns stand on the navmesh, the critical routes are walkable, locks follow their world flags, map loading
## puts the player exactly on the named spawn, builds are deterministic, the kit's materials/collision are valid.

const SY_TEMPLE := 2.0
const MAP_IDS: Array[StringName] = [&"sanctuary", &"westreach", &"ruined_forest", &"catacombs", &"forgotten_temple", &"boss_arena"]

static var _maps := {}
var _holder: Node3D

func _init() -> void:
	strict = true

func _hero() -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "MapTest")
	h.init_new()
	return h

## Build (once) and bake a map inside the tree, parented to a holder node.
func _map(id: StringName) -> MapRoot:
	if _maps.has(id) and is_instance_valid(_maps[id]):
		return _maps[id]
	if _holder == null or not is_instance_valid(_holder):
		_holder = Node3D.new()
		_holder.name = "MapTestHolder"
		host.add_child(_holder)
	var m := Game.build_map(id)
	_holder.add_child(m)
	MapBuilder.isolate_navigation(m)
	MapBuilder.bake_navigation(m)
	_maps[id] = m
	return m

func _nav_map(m: MapRoot) -> RID:
	return m.nav_region.get_navigation_map()

func _path_reaches(m: MapRoot, from: Vector3, to: Vector3, tol := 1.2) -> bool:
	var nm := _nav_map(m)
	var a := NavigationServer3D.map_get_closest_point(nm, from)
	var b := NavigationServer3D.map_get_closest_point(nm, to)
	var path := NavigationServer3D.map_get_path(nm, a, b, true)
	if path.is_empty():
		return false
	return path[path.size() - 1].distance_to(b) < 0.3 and b.distance_to(to) < tol and a.distance_to(from) < tol

# ------------------------------------------------------------------------------------------------------------

## Runs first (alphabetical): build and bake every map, then let the navigation server sync its regions.
func test_aa_build_and_sync_all_maps() -> void:
	for id in MAP_IDS:
		ok(_map(id) != null, "%s built" % id)
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	for id in MAP_IDS:
		var q := NavigationServer3D.map_get_closest_point(_nav_map(_maps[id]), _maps[id].spawns[&"start"].global_position)
		ok(q != Vector3.ZERO or _maps[id].spawns[&"start"].global_position.length() < 0.5, "%s navigation synced" % id)
	done()

func test_all_maps_build_with_spawns_and_views() -> void:
	for id in MAP_IDS:
		var def := DB.map_def(id)
		ok(def != null, "%s has a MapDef" % id)
		ok(ResourceLoader.exists(def.builder), "%s builder script exists" % id)
		var m := _map(id)
		ok(m != null and m.def == def, "%s builds" % id)
		ok(m.spawns.has(&"start"), "%s has a start spawn" % id)
		ok(m.views.has("overview"), "%s has an overview view" % id)
		ok(m.environment != null and m.sun != null, "%s has environment + key light" % id)
		ok(m.nav_region != null and m.nav_region.navigation_mesh.get_polygon_count() > 50, "%s navmesh baked (%d polys)" % [id, m.nav_region.navigation_mesh.get_polygon_count()])
		ok(m.bounds.size.length() > 10.0, "%s has bounds" % id)
	done()

func test_teleporter_links_resolve() -> void:
	var ids := {}
	var count := 0
	for id in MAP_IDS:
		for t in _map(id).teleporters():
			count += 1
			ok(not ids.has(t.teleporter_id), "teleporter id %s unique" % t.teleporter_id)
			ids[t.teleporter_id] = id
			ok(DB.map_def(t.destination_map) != null, "%s -> map %s exists" % [t.teleporter_id, t.destination_map])
			ok(t.destination_name == DB.map_def(t.destination_map).display_name, "%s destination name matches map" % t.teleporter_id)
			var dest := _map(t.destination_map)
			ok(dest.spawns.has(t.destination_spawn), "%s -> spawn %s exists on %s" % [t.teleporter_id, t.destination_spawn, t.destination_map])
	ok(count >= 8, "at least 8 teleporters across the slice (got %d)" % count)
	# the chain Sanctuary -> Forest -> Catacombs -> Temple -> Arena -> Sanctuary is complete
	var chain := {&"sanctuary": &"ruined_forest", &"ruined_forest": &"catacombs", &"catacombs": &"forgotten_temple",
		&"forgotten_temple": &"boss_arena", &"boss_arena": &"sanctuary"}
	for from in chain:
		var found := false
		for t in _map(from).teleporters():
			found = found or t.destination_map == chain[from]
		ok(found, "%s links forward to %s" % [from, chain[from]])
	done()

func test_spawns_stand_on_navmesh() -> void:
	for id in MAP_IDS:
		var m := _map(id)
		for sid in m.spawns:
			var p: Vector3 = m.spawns[sid].global_position
			var q := NavigationServer3D.map_get_closest_point(_nav_map(m), p)
			ok(q.distance_to(p) < 0.9, "%s spawn %s on navmesh (off by %.2f m)" % [id, sid, q.distance_to(p)])
	done()

func test_teleporters_reachable_from_start() -> void:
	for id in MAP_IDS:
		var m := _map(id)
		var start: Vector3 = m.spawns[&"start"].global_position
		for t in m.teleporters():
			ok(_path_reaches(m, start, t.arrival_point(), 1.6), "%s: start reaches teleporter %s" % [id, t.teleporter_id])
	done()

func test_critical_routes_walkable() -> void:
	var cat := _map(&"catacombs")
	var ritual: FlagTrigger = cat.find_child("Trigger_catacombs_ritual_seen", true, false)
	ok(ritual != null, "catacombs ritual trigger exists")
	ok(_path_reaches(cat, cat.spawns[&"entrance"].global_position, ritual.global_position - Vector3(0, 1, 0)), "catacombs: entrance -> ritual circle")
	ok(_path_reaches(cat, cat.spawns[&"entrance"].global_position, Vector3(32, -2.0, -6.0), 1.5), "catacombs: entrance -> cistern dock")
	ok(_path_reaches(cat, cat.spawns[&"entrance"].global_position, Vector3(22, 0, -40)), "catacombs: entrance -> treasure alcove")
	ok(_path_reaches(cat, Vector3(-28, 0, 0), Vector3(-20, 0, -34)), "catacombs: barracks -> ossuary (west loop)")
	var forest := _map(&"ruined_forest")
	ok(_path_reaches(forest, forest.spawns[&"arrival"].global_position, Vector3(20, 0, -15) + Vector3(0, forest.spawns[&"arrival"].global_position.y, 0), 2.5), "forest: arrival -> camp")
	ok(_path_reaches(forest, forest.spawns[&"arrival"].global_position, forest.spawns[&"catacomb_gate"].global_position), "forest: arrival -> catacomb gate (over the bridge)")
	var temple := _map(&"forgotten_temple")
	var seal: FlagTrigger = temple.find_child("Trigger_temple_seal_broken", true, false)
	ok(_path_reaches(temple, temple.spawns[&"arrival"].global_position, temple.spawns[&"sanctum"].global_position), "temple: arrival -> sanctum (grand stair)")
	ok(_path_reaches(temple, temple.spawns[&"sanctum"].global_position, seal.global_position - Vector3(0, 1, 0), 1.6), "temple: sanctum -> altar of the first oath")
	ok(_path_reaches(temple, temple.spawns[&"sanctum"].global_position, Vector3(0, SY_TEMPLE + 0.8, -36.2), 1.6), "temple: sanctum -> top of the facade steps")
	var arena := _map(&"boss_arena")
	var boss := arena.get_tree().get_nodes_in_group(&"boss_spawn").filter(func(n): return arena.is_ancestor_of(n))
	ok(boss.size() == 1, "arena has one boss spawn")
	ok(_path_reaches(arena, arena.spawns[&"arrival"].global_position, boss[0].global_position), "arena: arrival -> throne (bridge + dais stair)")
	var pillars := arena.get_tree().get_nodes_in_group(&"arena_pillar").filter(func(n): return arena.is_ancestor_of(n))
	eq(pillars.size(), 8, "arena has 8 impact pillars")
	done()

func test_water_and_edges_block_walking() -> void:
	# nothing walkable below the catacomb pool surface except the dock/landing, and the forest ravine floor is cut off
	var cat := _map(&"catacombs")
	var pool_floor := Vector3(28.0, -4.1, -12.0)
	var start: Vector3 = cat.spawns[&"entrance"].global_position
	ok(not _path_reaches(cat, start, pool_floor, 0.8), "catacombs: pool floor is not reachable on foot")
	var forest := _map(&"ruined_forest")
	var ravine := Vector3(0.5, -7.0, -25.0)
	ok(not _path_reaches(forest, forest.spawns[&"arrival"].global_position, ravine, 1.2), "forest: ravine floor is not reachable")
	done()

func test_locked_teleporters_follow_flags() -> void:
	var prev := Game.hero
	Game.hero = _hero()
	var cases := [[&"catacombs", &"catacombs_exit", &"catacombs_ritual_seen"],
		[&"forgotten_temple", &"temple_throne_gate", &"temple_seal_broken"],
		[&"boss_arena", &"arena_return", &"boss_warden_defeated"]]
	for c in cases:
		var t := _map(c[0]).teleporter(c[1])
		ok(t != null, "%s exists" % c[1])
		ok(t.is_locked(), "%s starts locked" % c[1])
		eq(t.unlock_flag, c[2], "%s unlock flag" % c[1])
		ok(not t.activate_would_travel(), "%s refuses to travel while locked" % c[1])
		Game.hero.world_flags[c[2]] = true
		ok(not t.is_locked(), "%s unlocks with %s" % [c[1], c[2]])
		ok(t.activate_would_travel(), "%s would travel once unlocked" % c[1])
	for id in [&"sanctuary_waypoint", &"forest_waypoint", &"catacomb_gate", &"catacombs_entrance", &"temple_arrival"]:
		var found := false
		for mid in MAP_IDS:
			var t := _map(mid).teleporter(id)
			if t:
				found = true
				ok(not t.is_locked(), "%s is open from the start" % id)
		ok(found, "%s exists" % id)
	Game.hero = prev
	done()

func test_flag_trigger_sets_flag_and_hides_seal() -> void:
	var prev := Game.hero
	Game.hero = _hero()
	var temple := _map(&"forgotten_temple")
	var seal := temple.find_child("DoorSeal", true, false) as Node3D
	ok(seal != null and seal.visible, "temple door seal visible before the flag")
	var trig: FlagTrigger = temple.find_child("Trigger_temple_seal_broken", true, false)
	var prev_map := Game.current_map
	Game.current_map = temple
	var xp0 := Game.hero.progress.total_xp
	trig.fire()
	ok(Game.hero.world_flags.get(&"temple_seal_broken", false), "altar trigger sets temple_seal_broken")
	eq(Game.hero.progress.total_xp - xp0, trig.xp_reward, "exploration XP granted once")
	ok(not temple.teleporter(&"temple_throne_gate").is_locked(), "throne gate unlocked by the trigger")
	# a fresh load of the map with the flag already set starts with the seal hidden
	var fresh := Game.build_map(&"forgotten_temple")
	_holder.add_child(fresh)
	fresh.apply_flag_visuals()
	var seal2 := fresh.find_child("DoorSeal", true, false) as Node3D
	ok(not seal2.visible, "seal hidden on load when the flag is already set")
	fresh.free()
	Game.current_map = prev_map
	Game.hero = prev
	done()

func test_load_map_places_player_on_named_spawn() -> void:
	var prev_parent := Game.world_parent
	var prev_player := Game.player
	var prev_map := Game.current_map
	var prev_hero := Game.hero
	var holder := Node3D.new()
	host.add_child(holder)
	Game.world_parent = holder
	Game.hero = _hero()
	var body := CharacterBody3D.new()
	body.add_to_group(&"player")
	Game.player = body
	# follow every teleporter link: arriving must put the body exactly on the destination spawn
	for pair in [[&"ruined_forest", &"arrival"], [&"catacombs", &"entrance"], [&"forgotten_temple", &"arrival"],
			[&"boss_arena", &"arrival"], [&"sanctuary", &"waypoint"], [&"ruined_forest", &"catacomb_gate"], [&"catacombs", &"exit"]]:
		var m := Game.load_map(pair[0], pair[1])
		var want: Vector3 = m.spawns[pair[1]].global_position
		ok(body.get_parent() == m, "player reparented into %s" % pair[0])
		near(body.global_position.distance_to(want), 0.05, 0.02, "player on %s/%s" % pair)
		eq(Game.hero.current_map, pair[0], "hero.current_map updated")
		eq(Game.hero.current_spawn, pair[1], "hero.current_spawn updated")
		ok(Game.hero.discovered_maps.has(pair[0]), "%s marked discovered" % pair[0])
	eq(holder.get_children().filter(func(c): return not c.is_queued_for_deletion()).size(), 1, "old maps released on load (only the current map remains)")
	if Game.current_map:
		Game.current_map.remove_child(body)
	body.free()
	holder.queue_free()
	Game.current_map = prev_map
	Game.player = prev_player
	Game.world_parent = prev_parent
	Game.hero = prev_hero
	done()

func test_builds_are_deterministic() -> void:
	for id in [&"catacombs", &"ruined_forest"]:
		var a := Game.build_map(id)
		var b := Game.build_map(id)
		var na := a.find_children("*", "Node3D", true, false)
		var nb := b.find_children("*", "Node3D", true, false)
		eq(na.size(), nb.size(), "%s rebuild has the same node count" % id)
		var same := true
		for i in mini(na.size(), 400):
			var auto_named := String(na[i].name).begins_with("@")
			if (na[i] as Node3D).transform != (nb[i] as Node3D).transform or (not auto_named and na[i].name != nb[i].name):
				same = false
				break
		ok(same, "%s rebuild places nodes identically" % id)
		a.free()
		b.free()
	done()

func test_environment_kit_is_valid() -> void:
	var files := DirAccess.get_files_at("res://assets/environment/")
	var n := 0
	for f in files:
		if not f.ends_with(".glb"):
			continue
		n += 1
		var inst: Node = (load("res://assets/environment/" + f) as PackedScene).instantiate()
		if f.begins_with("ph_"):
			# bh-033: downloaded CC0 props (Poly Haven) keep their own scanned PBR materials instead of the kit's
			# contract set; they must still be textured and stay inside the prop budget (docs/ASSET_SOURCES.md)
			var tris := 0
			for mi in inst.find_children("*", "MeshInstance3D", true, false):
				for i in mi.mesh.get_surface_count():
					var m := mi.mesh.surface_get_material(i) as BaseMaterial3D
					# bh-042: the chandeliers' wrought-iron and glass parts are plain PBR colours
					ok(m != null and (m.albedo_texture != null or f in ["ph_chandelier_02.glb", "ph_lantern_chandelier_01.glb"]), "%s surface %d is textured" % [f, i])
					tris += mi.mesh.surface_get_array_len(i) / 3 if mi.mesh.surface_get_format(i) & Mesh.ARRAY_FORMAT_INDEX == 0 else mi.mesh.surface_get_array_index_len(i) / 3
			ok(tris <= 10500, "%s stays within the prop budget (%d triangles)" % [f, tris])
			inst.free()
			continue
		var bad := []
		for mi in inst.find_children("*", "MeshInstance3D", true, false):
			for i in mi.mesh.get_surface_count():
				var mat: Material = mi.mesh.surface_get_material(i)
				var nm := mat.resource_name.get_slice(".", 0) if mat else "<none>"
				if not MaterialLibrary.ENV.has(nm):
					bad.append(nm)
		ok(bad.is_empty(), "%s uses only contract materials %s" % [f, bad])
		inst.free()
	ok(n >= 90, "environment kit has at least 90 pieces (got %d)" % n)
	for arch in ["wall_straight", "wall_stone_capped", "wall_low", "wall_doorway", "floor_tile_4m", "stairs", "pillar_quoin",
			"bridge_stone", "teleporter_platform", "temple_facade", "house_intact", "throne"]:
		var inst: Node = MapBuilder.scene(arch).instantiate()
		ok(inst.find_children("*", "StaticBody3D", true, false).size() > 0, "%s has collision" % arch)
		inst.free()
	for s in [["torch_sconce", "flame"], ["brazier", "flame"], ["campfire", "flame"], ["lamp_post", "light"],
			["teleporter_platform", "center"], ["house_intact", "door_light"], ["throne", "light"]]:
		var inst: Node = MapBuilder.scene(s[0]).instantiate()
		ok(inst.find_child(s[1], true, false) != null, "%s has socket %s" % s)
		inst.free()
	done()

func test_breakables_shatter_into_fragments() -> void:
	var holder := Node3D.new()
	host.add_child(holder)
	for kind in ["crate", "barrel", "urn", "statue_small"]:
		var b := Breakable.new().setup(kind, 10.0)
		holder.add_child(b)
		ok(b.get_child_count() >= 2, "%s built (visual + collision)" % kind)
		var before := holder.get_child_count()
		b.take_hit(4.0)
		ok(not b.is_queued_for_deletion(), "%s survives a hit below its HP" % kind)
		b.take_hit(7.0, Vector3(3, 0, 0))
		var frags := holder.get_child_count() - before
		ok(frags >= 6 and frags <= 14, "%s shatters into 6-14 fragments (got %d)" % [kind, frags])
		ok(b.is_queued_for_deletion(), "%s removed after breaking" % kind)
		var fast := 0.0
		for c in holder.get_children():
			if c is RigidBody3D:
				fast = maxf(fast, (c as RigidBody3D).linear_velocity.length())
		ok(fast <= Breakable.MAX_DEBRIS_SPEED + 0.001, "%s debris speed capped (%.1f)" % [kind, fast])
		for c in holder.get_children():
			c.free()
	holder.free()
	done()

func test_zz_cleanup() -> void:
	for id in _maps:
		if is_instance_valid(_maps[id]):
			_maps[id].free()
	_maps.clear()
	if _holder and is_instance_valid(_holder):
		_holder.free()
	ok(true, "cleanup")
	done()
