extends TestCase
## Salmonan as one geography (DataIsland, RoutePlanner, Routes, the South Gate, the waypoint network, save v4):
## the data is consistent, every charted road is really walkable on the built maps' navmeshes, the topology has the
## loops the design asks for, routes respect locks and explain them, distances count walking only, the directions
## service replans off route and clears on arrival, and v3 saves migrate without granting travel they did not have.

const SURFACE: Array[StringName] = [&"sanctuary", &"westreach", &"ruined_forest", &"olivar", &"wyman_outpost"]

static var _maps := {}
var _holder: Node3D

func _init() -> void:
	strict = true

func _hero(flags := {}) -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(&"knight"), "IslandTest")
	h.init_new()
	for f in flags:
		h.world_flags[StringName(f)] = flags[f]
	return h

func _map(id: StringName) -> MapRoot:
	if _maps.has(id) and is_instance_valid(_maps[id]):
		return _maps[id]
	if _holder == null or not is_instance_valid(_holder):
		_holder = Node3D.new()
		_holder.name = "IslandTestHolder"
		host.add_child(_holder)
	var prev := Game.hero
	Game.hero = _hero({"mq_marsh_gate_open": true})
	var m := Game.build_map(id)
	_holder.add_child(m)
	MapBuilder.isolate_navigation(m)
	m.apply_flag_visuals()
	MapBuilder.bake_navigation(m)
	Game.hero = prev
	_maps[id] = m
	return m

func _nav(m: MapRoot) -> RID:
	return m.nav_region.get_navigation_map()

# ------------------------------------------------------------------------------------------------------------

func test_aa_build_surface_maps() -> void:
	for id in SURFACE:
		ok(_map(id) != null, "%s built" % id)
	# Malasugue as it loads once Captain Hald has opened the gate (the flag applies before the navmesh bakes)
	var prev := Game.hero
	Game.hero = _hero({"south_gate_open": true})
	var t := Game.build_map(&"sanctuary")
	_holder.add_child(t)
	MapBuilder.isolate_navigation(t)
	t.apply_flag_visuals()
	MapBuilder.bake_navigation(t)
	_maps[&"sanctuary_open"] = t
	Game.hero = prev
	await host.get_tree().physics_frame
	await host.get_tree().physics_frame
	done()

func test_data_is_consistent() -> void:
	var ids := {}
	for p in DataIsland.all_places():
		ok(not ids.has(p.id), "place id %s unique" % p.id)
		ids[p.id] = true
		ok(DB.map_def(StringName(p.map)) != null, "%s is on a real map (%s)" % [p.id, p.map])
		if p.has("shrine"):
			ok(DataIsland.NETWORK.has(StringName(p.shrine)), "%s's shrine %s is a network shrine" % [p.id, p.shrine])
	var road_ids := {}
	for r in DataIsland.ROADS:
		ok(not road_ids.has(r.id), "road id %s unique" % r.id)
		road_ids[r.id] = true
		var a := DataIsland.place(r.a)
		var b := DataIsland.place(r.b)
		ok(not a.is_empty() and not b.is_empty(), "%s joins real places" % r.id)
		ok(a.map == r.map and b.map == r.map, "%s: both ends on %s" % [r.id, r.map])
		ok(DataIsland.is_surface(StringName(r.map)), "%s is on a charted surface map" % r.id)
		ok((r.points[0] as Vector2).distance_to(a.pos) < 0.01, "%s starts on %s" % [r.id, r.a])
		ok((r.points[r.points.size() - 1] as Vector2).distance_to(b.pos) < 0.01, "%s ends on %s" % [r.id, r.b])
		ok(r.type in ["road", "trail"], "%s has a road type" % r.id)
	var link_ids := {}
	for l in DataIsland.all_links():
		ok(not link_ids.has(l.id), "link id %s unique" % l.id)
		link_ids[l.id] = true
		ok(not DataIsland.place(l.a).is_empty() and not DataIsland.place(l.b).is_empty(), "%s joins real places" % l.id)
		ok(l.mode in ["boundary", "door", "shrine", "dungeon", "ship"], "%s has a known mode" % l.id)
		if l.has("flag"):
			ok(String(l.get("why", "")) != "", "locked link %s explains its lock" % l.id)
	for id in DataIsland.NETWORK:
		var n: Dictionary = DataIsland.NETWORK[id]
		ok(DataIsland.place(n.place).get("shrine", "") == String(id), "network shrine %s stands at %s" % [id, n.place])
	done()

func test_shrines_exits_and_signs_exist_in_the_built_maps() -> void:
	for id in DataIsland.NETWORK:
		var n: Dictionary = DataIsland.NETWORK[id]
		var m := _map(n.map)
		var t := m.teleporter(id)
		ok(t != null, "%s exists on %s" % [id, n.map])
		ok(m.spawns.has(n.spawn), "%s lands on spawn %s" % [id, n.spawn])
		if t:
			var p := DataIsland.place(n.place)
			ok(Vector2(t.position.x, t.position.z).distance_to(p.pos) < 14.0, "%s stands at %s (%.1f m)" % [id, n.place, Vector2(t.position.x, t.position.z).distance_to(p.pos)])
			ok(m.spawn_transform(n.spawn).origin.distance_to(t.global_position) < 6.0, "%s's arrival spawn is beside its dais" % id)
	for l in DataIsland.LINKS:
		if l.mode != "boundary":
			continue
		for dir in [[l.a, l.b], [l.b, l.a]]:
			var from := DataIsland.place(dir[0])
			var to := DataIsland.place(dir[1])
			var m := _map(StringName(from.map))
			var found: MapExit = null
			for e in m.find_children("Exit_*", "MapExit", true, false):
				if (e as MapExit).destination_map == StringName(to.map):
					found = e
			ok(found != null, "%s: an exit on %s leads to %s" % [l.id, from.map, to.map])
			if found:
				ok(_map(StringName(to.map)).spawns.has(found.destination_spawn), "%s lands on a real spawn (%s)" % [found.exit_id, found.destination_spawn])
				ok(Vector2(found.position.x, found.position.z).distance_to(from.pos) < 16.0, "%s is at %s (%.1f m)" % [found.exit_id, from.id,
					Vector2(found.position.x, found.position.z).distance_to(from.pos)])
				# the arrival spawn must not stand inside the far side's exit (no bounce back)
				for e2 in _map(StringName(to.map)).find_children("Exit_*", "MapExit", true, false):
					var sp := _map(StringName(to.map)).spawn_transform(found.destination_spawn).origin
					ok(sp.distance_to((e2 as Node3D).global_position) > 4.5, "%s arrival is clear of %s" % [found.exit_id, e2.name])
	var signs := 0
	for id in SURFACE:
		signs += _map(id).find_children("*", "SignLabels", true, false).size()
	ok(signs >= 6, "signposts name the roads (%d)" % signs)
	done()

## Every charted road follows walkable ground: samples along it sit on the navmesh and its ends are connected.
func test_roads_are_walkable_on_the_navmesh() -> void:
	for r in DataIsland.ROADS:
		var m := _map(StringName(r.map))
		var nm := _nav(m)
		var pts: Array = r.points
		var total := DataIsland.polyline_length(pts)
		var worst := 0.0
		var along := 0.0
		while along <= total:
			var p := DataIsland.point_at(pts, along)
			var y := _ground_y(m, p)
			var q := NavigationServer3D.map_get_closest_point(nm, Vector3(p.x, y, p.y))
			worst = maxf(worst, Vector2(q.x, q.z).distance_to(p))
			along += 5.0
		ok(worst < 2.2, "%s stays on the navmesh (worst %.2f m off)" % [r.id, worst])
		var a: Vector2 = pts[0]
		var b: Vector2 = pts[pts.size() - 1]
		var from := NavigationServer3D.map_get_closest_point(nm, Vector3(a.x, _ground_y(m, a), a.y))
		var to := NavigationServer3D.map_get_closest_point(nm, Vector3(b.x, _ground_y(m, b), b.y))
		var path := NavigationServer3D.map_get_path(nm, from, to, true)
		var reached := not path.is_empty() and path[path.size() - 1].distance_to(to) < 0.6
		ok(reached, "%s: %s reaches %s on foot" % [r.id, r.a, r.b])
		if not reached:
			print("ROAD NAV %s from=%s to=%s end=%s" % [r.id, from, to, path[path.size() - 1] if not path.is_empty() else "none"])
		if not path.is_empty():
			var walked := 0.0
			for i in path.size() - 1:
				walked += Vector2(path[i].x, path[i].z).distance_to(Vector2(path[i + 1].x, path[i + 1].z))
			ok(walked < total * 1.35 + 6.0, "%s: the walked way (%.0f m) matches the road (%.0f m)" % [r.id, walked, total])
	done()

## Height of the walkable surface of this map at a point: among the surfaces of THIS map under it (terrain, bridge
## decks, slabs — the test builds every surface map at the same origin, so other maps' colliders are skipped), the
## one with navmesh closest to it (a bridge deck over a ravine, not the ravine floor; the road, not an arch over it).
func _ground_y(m: MapRoot, p: Vector2) -> float:
	var space := m.get_world_3d().direct_space_state
	var nm := _nav(m)
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, 60, p.y), Vector3(p.x, -60, p.y), BH.LAYER_GROUND | BH.LAYER_WORLD)
	var exclude: Array[RID] = []
	var best_y := 0.0
	var best := INF
	for i in 16:
		q.exclude = exclude
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			break
		exclude.append(hit.rid)
		if not (hit.collider is Node and m.is_ancestor_of(hit.collider)) or (hit.normal as Vector3).y < 0.6:
			continue
		var c := NavigationServer3D.map_get_closest_point(nm, hit.position)
		var d := c.distance_to(hit.position)
		if d < 0.6:
			return hit.position.y   # the highest walkable surface (a bridge deck before the ravine floor under it)
		if d < best:
			best = d
			best_y = hit.position.y
	return best_y

func test_sea_and_cliffs_are_not_routes() -> void:
	var m := _map(&"westreach")
	var nm := _nav(m)
	var gate := m.spawn_transform(&"town_gate").origin
	var from := NavigationServer3D.map_get_closest_point(nm, gate)
	for sea in [Vector3(-100, -19, 150), Vector3(-185, -19, 125), Vector3(-215, -19, 40), Vector3(0, -19, 150)]:
		var q := NavigationServer3D.map_get_closest_point(nm, sea)
		var path := NavigationServer3D.map_get_path(nm, from, q, true)
		var reached := not path.is_empty() and path[path.size() - 1].distance_to(q) < 1.0
		ok(not reached, "the sea floor near %s cannot be walked to from the gate" % sea)
	var path := NavigationServer3D.map_get_path(nm, gate, NavigationServer3D.map_get_closest_point(nm, Vector3(-178, -12.5, 92)), true)
	ok(not path.is_empty(), "the cove is reachable from the gate on foot (down the Cove Steps)")
	done()

## The playable exterior has at least two independent loops walked on roads alone, and three early named destinations
## reachable on foot from the town once the gate is open.
func test_topology_loops_and_early_choices() -> void:
	var nodes := {}
	var edges := 0
	var adj := {}
	for r in DataIsland.ROADS:
		nodes[r.a] = true
		nodes[r.b] = true
		edges += 1
		adj.get_or_add(r.a, []).append(r.b)
		adj.get_or_add(r.b, []).append(r.a)
	# bh-013: a junction part-way along a road (where a dungeon trail leaves it) joins both of that road's ends
	for pl in DataIsland.all_places():
		var rr := DataIsland.road(String(pl.get("on_road", "")))
		if rr.is_empty():
			continue
		nodes[pl.id] = true
		for end in [rr.a, rr.b]:
			edges += 1
			adj.get_or_add(pl.id, []).append(end)
			adj.get_or_add(end, []).append(pl.id)
	for l in DataIsland.LINKS:
		# bh-029: the ship joins Salmonan's network to Zarael's (Wyman's Marsh Jetty to Agdao's pier)
		if l.mode == "boundary" or l.mode == "ship":
			nodes[l.a] = true
			nodes[l.b] = true
			edges += 1
			adj.get_or_add(l.a, []).append(l.b)
			adj.get_or_add(l.b, []).append(l.a)
	var comps := 0
	var seen := {}
	for n in nodes:
		if seen.has(n):
			continue
		comps += 1
		var stack := [n]
		while not stack.is_empty():
			var c = stack.pop_back()
			if seen.has(c):
				continue
			seen[c] = true
			stack.append_array(adj.get(c, []))
	var cycles := edges - nodes.size() + comps
	ok(cycles >= 2, "walkable exterior has at least 2 independent loops (%d)" % cycles)
	ok(comps == 1, "town, Westreach and the forest are one walkable network (%d components)" % comps)
	var h := _hero({"south_gate_open": true})
	for dest in ["wr_mill", "wr_fields", "wr_cove"]:
		var p := RoutePlanner.plan(h, &"sanctuary", Vector2(0, 14.5), dest, RoutePlanner.Mode.ROADS)
		ok(p.ok and p.transfers == 0, "%s reachable on foot from the plaza (%s)" % [dest, RoutePlanner.summary(p)])
		ok(p.walk_m > 60.0 and p.walk_m < 450.0, "%s is a short outing (%.0f m)" % [dest, p.walk_m])
	done()

func test_routes_respect_the_gate_and_explain_locks() -> void:
	var closed := _hero()
	var open := _hero({"south_gate_open": true})
	var via_forest := RoutePlanner.plan(closed, &"sanctuary", Vector2(0, 14.5), "wr_fields", RoutePlanner.Mode.ROADS)
	ok(via_forest.ok, "with the gate barred the fields are still reachable (the waypoint and the Forest Road)")
	ok(via_forest.legs.all(func(l): return l.id != "south_gate"), "a barred gate is never part of a route")
	eq(via_forest.transfers, 1, "that route uses the town waypoint once")
	var direct := RoutePlanner.plan(open, &"sanctuary", Vector2(0, 14.5), "wr_fields", RoutePlanner.Mode.ROADS)
	ok(direct.ok and direct.legs.any(func(l): return l.id == "south_gate"), "with the gate open the route leaves by the South Gate")
	eq(direct.transfers, 0, "and walks all the way")
	ok(direct.walk_m < via_forest.walk_m, "the gate road is the shorter walk (%.0f < %.0f m)" % [direct.walk_m, via_forest.walk_m])
	var temple := RoutePlanner.plan(open, &"sanctuary", Vector2(0, 14.5), "temple", RoutePlanner.Mode.ROADS)
	ok(not temple.ok and "ritual" in temple.reason, "the temple explains its lock (%s)" % temple.reason)
	var throne := RoutePlanner.plan(_hero({"catacombs_ritual_seen": true}), &"sanctuary", Vector2(0, 14.5), "throne", RoutePlanner.Mode.ROADS)
	ok(not throne.ok and "seal" in throne.reason, "the Hollow Throne explains its lock (%s)" % throne.reason)
	var nowhere := RoutePlanner.plan(open, &"sanctuary", Vector2(0, 14.5), "no_such_place", RoutePlanner.Mode.ROADS)
	ok(not nowhere.ok, "an unknown destination never produces a route")
	done()

func test_modes_distances_and_steps() -> void:
	var h := _hero({"south_gate_open": true})
	h.awakened_shrines[&"cove_shrine"] = true
	var walk := RoutePlanner.plan(h, &"sanctuary", Vector2(0, -18), "wr_cove", RoutePlanner.Mode.ROADS)
	var jump := RoutePlanner.plan(h, &"sanctuary", Vector2(0, -18), "wr_cove", RoutePlanner.Mode.WAYPOINTS)
	ok(walk.ok and walk.transfers == 0, "Roads walks to the cove")
	ok(jump.ok and jump.transfers == 1, "Waypoints jumps from the terrace to the awakened cove shrine")
	ok(jump.walk_m < walk.walk_m * 0.3, "the jump saves walking (%.0f vs %.0f m)" % [jump.walk_m, walk.walk_m])
	for p in [walk, jump]:
		var sum := 0.0
		for leg in p.legs:
			sum += float(leg.metres)
			if leg.kind != "road":
				eq(float(leg.metres), 0.0, "%s legs add no walking distance" % leg.kind)
		near(p.walk_m, sum, 0.01, "walk distance is the sum of walked legs")
		ok(not p.steps.is_empty() and p.steps.all(func(s): return s.text != ""), "every step has an instruction")
	# Roads prefers the maintained road over a trail; Shortest walk takes the trail when it is shorter
	var roads := RoutePlanner.plan(h, &"westreach", Vector2(-112, 44), "wr_cove", RoutePlanner.Mode.ROADS)
	var short := RoutePlanner.plan(h, &"westreach", Vector2(-112, 44), "wr_cove", RoutePlanner.Mode.SHORTEST)
	ok(short.legs.any(func(l): return l.get("id", "") == "wr_cove_steps"), "Shortest walk takes the Cove Steps trail")
	ok(short.walk_m <= roads.walk_m + 0.01, "Shortest walk is never longer than Roads")
	# from inside a building the first step leaves it through its door
	var inn := RoutePlanner.plan(h, &"int_tavern", Vector2.ZERO, "town_gate", RoutePlanner.Mode.ROADS)
	ok(inn.ok and inn.steps[0].text == "Leave The Salted Marlin", "inside the inn: first leave it (%s)" % inn.steps[0].text if inn.ok else inn.reason)
	# standing a few metres from a junction does not produce a separate "head along" step
	var near_fields := RoutePlanner.plan(h, &"westreach", Vector2(33, 109), "wr_mill", RoutePlanner.Mode.ROADS)
	ok(near_fields.ok and near_fields.steps.size() == 1 and "Mill Lane" in near_fields.steps[0].text, "one clear step from the fields to the mill (%s)" % str(near_fields.steps.map(func(s): return s.text)))
	var here := RoutePlanner.plan(h, &"westreach", Vector2(35, 110), "wr_fields", RoutePlanner.Mode.ROADS)
	ok(here.ok and here.walk_m < 1.0, "a route to where you stand is empty")
	done()

## The directions service: replans once when the hero strays, never before, and clears on arrival.
func test_routes_service_replans_and_arrives() -> void:
	var prev := [Game.hero, Game.current_map, Game.current_map_id, Game.player]
	var m := _map(&"westreach")
	Game.hero = _hero({"south_gate_open": true})
	Game.current_map = m
	Game.current_map_id = &"westreach"
	var body := Node3D.new()
	m.add_child(body)
	Game.player = body
	body.position = Vector3(-80, 0, 50)          # on the Mill Road
	Routes.set_route("wr_fields", RoutePlanner.Mode.ROADS)
	ok(Routes.plan.ok, "route planned from the Mill Road")
	ok(Routes.path_here.size() >= 2 and Routes.has_guide, "a guide point on this map")
	ok(Routes.guide.distance_to(body.position) < 14.0, "the guide is just ahead (%.1f m)" % Routes.guide.distance_to(body.position))
	ok(Routes.instruction != "" and Routes.remaining_m > 50.0, "instruction '%s', %.0f m left" % [Routes.instruction, Routes.remaining_m])
	var r0 := Routes.replans
	body.position += Vector3(0, 0, -6)           # 6 m off the road: within tolerance
	Routes._update(0.6)
	Routes._update(0.6)
	ok(not Routes._pending, "a small detour does not replan")
	body.position = Vector3(-60, 0, 10)          # well off the route
	Routes._since_plan = 5.0
	Routes._update(0.6)
	ok(not Routes._pending, "not after half a second off route")
	Routes._update(0.6)
	ok(Routes._pending, "replans after a second more than 10 m off route")
	Routes.replan()
	eq(Routes.replans - r0, 1, "exactly one replan")
	body.position = Vector3(34, 0, 108)          # at the fields
	Routes._update(0.2)
	ok(not Routes.active(), "arrival clears the route")
	eq(Game.hero.route, {}, "and forgets it on the hero")
	body.queue_free()
	Game.hero = prev[0]
	Game.current_map = prev[1]
	Game.current_map_id = prev[2]
	Game.player = prev[3]
	done()

func test_south_gate_opens_with_the_flag() -> void:
	var prev := Game.hero
	Game.hero = _hero()
	var town := Game.build_map(&"sanctuary")
	_holder.add_child(town)
	town.apply_flag_visuals()
	var bar := town.find_child("GateBar", true, false) as StaticBody3D
	ok(bar != null and bar.collision_layer != 0, "the barred gate collides")
	var exit: MapExit = town.find_child("Exit_sanctuary_south_gate", true, false)
	ok(exit != null and not exit.is_open(), "the gate road is shut without the flag")
	Game.hero.world_flags[&"south_gate_open"] = true
	town.apply_flag_visuals(&"south_gate_open")
	ok(bar.collision_layer == 0 and not bar.visible, "Captain Hald's key lifts the bar (no collision, hidden)")
	ok(exit.is_open(), "the gate road opens")
	town.free()
	# the navmesh baked on a fresh load with the flag set runs out through the gate
	var open_town := _open_town_nav()
	ok(open_town, "with the gate open the navmesh runs from the plaza out of the gate")
	Game.hero = prev
	var hald: NpcDef = DB.npcs.get(&"hald")
	ok(hald.graph.nodes.has("road") and hald.graph.nodes.has("road_opened"), "Captain Hald has the South Gate conversation")
	var sets := false
	for ch in hald.graph.nodes.road.choices:
		for a in ch.get("actions", []):
			sets = sets or a.get("set_flag", "") == "south_gate_open"
	ok(sets, "choosing to walk the roads sets south_gate_open")
	done()

func _open_town_nav() -> bool:
	var t: MapRoot = _maps[&"sanctuary_open"]
	var nm := _nav(t)
	var a := NavigationServer3D.map_get_closest_point(nm, t.spawns[&"start"].global_position)
	var target := Vector3(0, 0, 46)
	var b := NavigationServer3D.map_get_closest_point(nm, target)
	var path := NavigationServer3D.map_get_path(nm, a, b, true)
	return not path.is_empty() and Vector2(b.x, b.z).distance_to(Vector2(target.x, target.z)) < 1.5 and path[path.size() - 1].distance_to(b) < 0.5

func test_waypoint_network() -> void:
	var prev := Game.hero
	var town := _map(&"sanctuary")
	var tp := town.teleporter(&"sanctuary_waypoint")
	Game.hero = _hero()
	var d := tp.destinations()
	eq(d.size(), 1, "a new hero's terrace waypoint goes only to the forest (unchanged)")
	eq(d[0].map, &"ruined_forest", "its own destination first")
	Game.hero.awakened_shrines[&"cove_shrine"] = true
	d = tp.destinations()
	eq(d.size(), 2, "an awakened cove shrine becomes a second destination")
	ok(d.any(func(x): return x.map == &"westreach" and x.spawn == &"cove_shrine"), "the cove, arriving beside its dais")
	# discovery and awakening are separate: a locked dungeon dais is recorded but never awakened
	var cat := _map(&"forgotten_temple")
	var gate := cat.teleporter(&"temple_throne_gate")
	gate.discover()
	ok(Game.hero.unlocked_teleporters.has(&"temple_throne_gate"), "a locked dais is discovered")
	ok(not Game.hero.awakened_shrines.has(&"temple_throne_gate"), "but not awakened")
	var cove := _map(&"westreach").teleporter(&"cove_shrine")
	Game.hero.awakened_shrines.erase(&"cove_shrine")
	cove.discover()
	ok(Game.hero.awakened_shrines.has(&"cove_shrine"), "standing on the cove shrine awakens it")
	Game.hero = prev
	done()

func test_save_v3_migrates_to_v4() -> void:
	var v3 := {"version": 3, "hero": {"class": "knight", "name": "Old", "teleporters": ["sanctuary_waypoint", "forest_waypoint", "catacombs_exit", "catacomb_gate"],
		"discovered_maps": ["sanctuary", "ruined_forest", "catacombs"], "flags": {"catacombs_ritual_seen": true}, "map": "catacombs", "spawn": "entrance"}}
	var d := SaveSystem.migrate(v3.duplicate(true))
	eq(int(d.version), SaveSystem.CURRENT_VERSION, "migrated to the current version")
	var aw: Array = d.hero.awakened_shrines
	ok(aw.has("sanctuary_waypoint") and aw.has("forest_waypoint"), "the two legacy waypoints stay usable")
	ok(not aw.has("catacombs_exit") and not aw.has("catacomb_gate"), "dungeon daises are not turned into network shrines")
	eq(d.hero.route, {}, "no route yet")
	var h := HeroData.from_dict(d.hero)
	ok(h != null and h.current_map == &"catacombs" and h.world_flags.get(&"catacombs_ritual_seen", false), "map, spawn and flags survive")
	ok(h.unlocked_teleporters.has(&"catacombs_exit"), "discovered daises are still discovered")
	# a v4 round trip keeps awakened shrines, found places and the tracked route; unknown ids are dropped
	h.awakened_shrines[&"cove_shrine"] = true
	h.known_places["wr_cave"] = true
	h.route = {"dest": "wr_fields", "mode": 2}
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	ok(back.awakened_shrines.has(&"cove_shrine") and back.known_places.has("wr_cave"), "shrines and found places round-trip")
	eq(back.route, {"dest": "wr_fields", "mode": 2}, "the tracked route round-trips")
	var bad := h.to_dict()
	bad["route"] = {"dest": "removed_place", "mode": 0}
	bad["known_places"] = ["removed_place"]
	bad["awakened_shrines"] = ["not_a_shrine"]
	var h2 := HeroData.from_dict(bad)
	ok(h2.route.is_empty() and h2.known_places.is_empty() and h2.awakened_shrines.is_empty(), "missing places and shrines fail gracefully")
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
