class_name RoutePlanner
extends RefCounted
## Plans journeys across Salmonan over DataIsland: roads (walked, measured along their authored polylines) and links
## (the South Gate road, doors, waypoint shrines, dungeon gates). The M atlas and the directions HUD both call this;
## nothing else decides routes.
##
## Modes: ROADS prefers maintained roads (trails cost more) and only uses the original paired waypoint when walking is
## impossible; SHORTEST walks the least distance including trails; WAYPOINTS may add a transfer between awakened
## shrines. A route never passes a link whose world flag is missing; if that is the only way, the plan fails with the
## lock's reason. Distances count walking only: shrine transfers, doors and dungeon interiors add none.

enum Mode { ROADS, SHORTEST, WAYPOINTS }
const MODE_NAMES := ["Roads", "Shortest walk", "Waypoints"]
const TRAIL_FACTOR := 1.6           # ROADS: a metre of trail costs this much
const SHRINE_COST := [600.0, 600.0, 40.0]
const DOOR_COST := 4.0
const DUNGEON_COST := 80.0
const START := "@start"
const SHORT_START_M := 12.0          # a first stretch shorter than this is not its own instruction

## plan(hero, map, local position, destination place id, mode) ->
##   {ok, reason, dest, mode, legs: [leg], steps: [step], walk_m, transfers, est_s}
## leg:  {kind: road|boundary|door|shrine|dungeon, id, name, from, to, map, points (local XZ, in travel order),
##        metres, text, step (index into steps)}
## step: {text, note, metres, kind}
static func plan(hero: HeroData, map_id: StringName, pos: Vector2, dest_id: String, mode: int = Mode.ROADS) -> Dictionary:
	var dest := DataIsland.place(dest_id)
	var out := {"ok": false, "reason": "", "dest": dest_id, "mode": mode, "legs": [], "steps": [], "walk_m": 0.0, "transfers": 0, "est_s": 0.0}
	if dest.is_empty():
		out.reason = "Unknown destination."
		return out
	var g := _graph(hero, mode, true)
	var start := _attach_start(g, map_id, pos)
	if start.is_empty():
		out.reason = "No known route from here."
		return out
	var path := _dijkstra(g, START, dest_id)
	if path.is_empty():
		# is there a way if every lock were open? then say which lock is in the way
		var g2 := _graph(hero, mode, false)
		_attach_start(g2, map_id, pos)
		var path2 := _dijkstra(g2, START, dest_id)
		out.reason = "No known route."
		for leg in path2:
			if leg.get("locked", false):
				out.reason = leg.get("why", "The way is locked.")
				break
		return out
	out.ok = true
	out.legs = path
	_describe(out, hero)
	return out

## Place ids a hero at (map, pos) is standing at or nearest (for "You are here" and arrival checks).
static func here(map_id: StringName, pos: Vector2) -> String:
	var best := ""
	var bd := INF
	for p in DataIsland.all_places():
		if StringName(p.map) != map_id:
			continue
		if not p.has("pos"):
			return p.id
		var d := pos.distance_to(p.pos)
		if d < bd:
			bd = d
			best = p.id
	return best

# ------------------------------------------------------------------------------------------------------------

static func _graph(hero: HeroData, mode: int, respect_locks: bool) -> Dictionary:
	var adj := {}
	for p in DataIsland.all_places():
		adj[p.id] = []
	for r in DataIsland.ROADS:
		var pts: Array = r.points
		var m := DataIsland.polyline_length(pts)
		var cost := m * (TRAIL_FACTOR if r.type == "trail" and mode == Mode.ROADS else 1.0)
		var back := pts.duplicate()
		back.reverse()
		adj[r.a].append({"to": r.b, "cost": cost, "leg": _road_leg(r, r.a, r.b, pts, m)})
		adj[r.b].append({"to": r.a, "cost": cost, "leg": _road_leg(r, r.b, r.a, back, m)})
	# bh-013: a junction standing part-way along a road (where a dungeon trail leaves it) joins both of its ends
	for p in DataIsland.all_places():
		if not p.has("on_road"):
			continue
		var rr := DataIsland.road(String(p.on_road))
		if rr.is_empty():
			continue
		var pr := DataIsland.project(p.pos, rr.points)
		var total := DataIsland.polyline_length(rr.points)
		for end in [[rr.a, 0.0], [rr.b, total]]:
			var pts := DataIsland.slice(rr.points, float(end[1]), float(pr.along))
			var m2 := absf(float(end[1]) - float(pr.along))
			var c2 := m2 * (TRAIL_FACTOR if rr.type == "trail" and mode == Mode.ROADS else 1.0)
			var back2 := pts.duplicate()
			back2.reverse()
			adj[end[0]].append({"to": p.id, "cost": c2, "leg": _road_leg(rr, end[0], p.id, pts, m2)})
			adj[p.id].append({"to": end[0], "cost": c2, "leg": _road_leg(rr, p.id, end[0], back2, m2)})
	for l in DataIsland.all_links():
		var locked: bool = l.has("flag") and not (hero != null and bool(hero.world_flags.get(StringName(l.flag), false)))
		if locked and respect_locks:
			continue
		var cost := 0.0
		match l.mode:
			"boundary":
				cost = 0.0
			"door":
				cost = DOOR_COST
			"dungeon":
				cost = DUNGEON_COST
			"shrine":
				cost = SHRINE_COST[mode]
		if locked:
			cost += 100000.0
		var leg := {"kind": l.mode, "id": l.id, "name": "", "from": l.a, "to": l.b, "map": DataIsland.place(l.a).map,
			"points": [], "metres": 0.0, "text": l.get("text", ""), "locked": locked, "why": l.get("why", "")}
		adj[l.a].append({"to": l.b, "cost": cost, "leg": leg})
		if not l.get("oneway", false):
			var back_leg := leg.duplicate()
			back_leg.from = l.b
			back_leg.to = l.a
			back_leg.map = DataIsland.place(l.b).map
			back_leg.text = l.get("back", l.get("text", ""))
			adj[l.b].append({"to": l.a, "cost": cost, "leg": back_leg})
	# the waypoint network: any two awakened network shrines (WAYPOINTS mode only)
	if mode == Mode.WAYPOINTS and hero != null:
		var awake := []
		for p in DataIsland.PLACES:
			if p.has("shrine") and DataIsland.NETWORK_SHRINES.has(StringName(p.shrine)) and hero.awakened_shrines.has(StringName(p.shrine)):
				awake.append(p)
		for a in awake:
			for b in awake:
				if a.id != b.id:
					adj[a.id].append({"to": b.id, "cost": SHRINE_COST[mode], "leg": {"kind": "shrine", "id": "network_%s_%s" % [a.id, b.id],
						"name": "", "from": a.id, "to": b.id, "map": a.map, "points": [], "metres": 0.0, "text": "", "locked": false}})
	return {"adj": adj}

static func _road_leg(r: Dictionary, from: String, to: String, pts: Array, m: float) -> Dictionary:
	return {"kind": "road", "id": r.id, "name": r.name, "type": r.type, "from": from, "to": to, "map": r.map, "points": pts, "metres": m, "text": ""}

## Join the hero's position to the graph: onto the nearest road of this map (both directions along it), or, where a map
## has no charted roads (interiors, dungeon floors), at the place that stands for that map.
static func _attach_start(g: Dictionary, map_id: StringName, pos: Vector2) -> Dictionary:
	var adj: Dictionary = g.adj
	adj[START] = []
	var best := {}
	for r in DataIsland.roads_on(map_id):
		var pr := DataIsland.project(pos, r.points)
		if best.is_empty() or pr.dist < best.pr.dist:
			best = {"road": r, "pr": pr}
	if not best.is_empty():
		var r: Dictionary = best.road
		var pr: Dictionary = best.pr
		var total := DataIsland.polyline_length(r.points)
		var approach := pos.distance_to(pr.point)
		for dir in [[r.a, 0.0], [r.b, total]]:
			var pts := DataIsland.slice(r.points, pr.along, dir[1])
			if approach > 0.5:
				pts.push_front(pos)
			var m := absf(dir[1] - pr.along) + approach
			var cost := m * (TRAIL_FACTOR if r.type == "trail" else 1.0)
			adj[START].append({"to": dir[0], "cost": cost, "leg": {"kind": "road", "id": r.id, "name": r.name, "type": r.type,
				"from": START, "to": dir[0], "map": r.map, "points": pts, "metres": m, "text": ""}})
		return best
	for p in DataIsland.all_places():
		if StringName(p.map) == map_id:
			adj[START].append({"to": p.id, "cost": 0.0, "leg": {}})
			return p
	return {}

static func _dijkstra(g: Dictionary, from: String, to: String) -> Array:
	var adj: Dictionary = g.adj
	var cost := {from: 0.0}
	var prev := {}
	var open := {from: true}
	var done := {}
	while not open.is_empty():
		var node := ""
		var bc := INF
		for n in open:
			if cost[n] < bc or (cost[n] == bc and String(n) < node):
				bc = cost[n]
				node = n
		open.erase(node)
		if node == to:
			break
		done[node] = true
		for e in adj.get(node, []):
			if done.has(e.to):
				continue
			var c: float = bc + e.cost
			if c < cost.get(e.to, INF):
				cost[e.to] = c
				prev[e.to] = {"from": node, "leg": e.leg}
				open[e.to] = true
	if not cost.has(to):
		return []
	var path := []
	var n := to
	while n != from:
		var pv: Dictionary = prev[n]
		if not (pv.leg as Dictionary).is_empty():
			path.push_front(pv.leg)
		n = pv.from
	return path

# ------------------------------------------------------------------------------------------------------------
# instructions

static func _pname(id: String) -> String:
	return DataIsland.place(id).get("name", id) if id != START else "here"

static func _describe(out: Dictionary, hero: HeroData) -> void:
	var legs: Array = out.legs
	var steps := []
	var walk := 0.0
	var transfers := 0
	var i := 0
	while i < legs.size():
		var leg: Dictionary = legs[i]
		match leg.kind:
			"road":
				# consecutive stretches of the same road read as one instruction
				var j := i
				var m := 0.0
				while j < legs.size() and legs[j].kind == "road" and legs[j].name == leg.name:
					m += legs[j].metres
					legs[j].step = steps.size()
					j += 1
				var last: Dictionary = legs[j - 1]
				if leg.from == START and m < SHORT_START_M and j < legs.size():
					# the hero is standing at the junction already: this stretch belongs to the next instruction
					walk += m
					for k in range(i, j):
						legs[k].step = steps.size()
					i = j
					continue
				var text := "Follow %s to %s" % [leg.name, _pname(last.to)]
				if leg.from == START and _pname(last.to) != "":
					text = "Head along %s to %s" % [leg.name, _pname(last.to)]
				# a road that ends at a map boundary: the boundary's own words say where it leads
				if j < legs.size() and legs[j].kind == "boundary":
					text = "%s (%s)" % [legs[j].text, leg.name]
					legs[j].step = steps.size()
					j += 1
				steps.append({"text": text, "note": "%s walking" % fmt_m(m), "metres": m, "kind": "road"})
				walk += m
				i = j
				continue
			"boundary":
				steps.append({"text": leg.text, "note": "", "metres": 0.0, "kind": "boundary"})
			"door":
				steps.append({"text": leg.text, "note": "Distance inside is not counted", "metres": 0.0, "kind": "door"})
			"dungeon":
				steps.append({"text": leg.text, "note": "Distance inside is not counted", "metres": 0.0, "kind": "dungeon"})
			"shrine":
				transfers += 1
				steps.append({"text": "At %s, use the waypoint to %s" % [_pname(leg.from), _pname(leg.to)],
					"note": "Waypoint transfer: stand on the shrine and press Interact", "metres": 0.0, "kind": "shrine"})
		leg.step = steps.size() - 1
		i += 1
	if steps.is_empty():
		steps.append({"text": "You are already at %s." % _pname(out.dest), "note": "", "metres": 0.0, "kind": "here"})
	out.steps = steps
	out.walk_m = walk
	out.transfers = transfers
	out.est_s = walk / walk_speed(hero)

static func walk_speed(hero: HeroData) -> float:
	if hero == null:
		return DataIsland.WALK_SPEED
	var v := hero.compute_stats().get_stat(&"move_speed", DataIsland.WALK_SPEED)
	return v if v > 0.5 else DataIsland.WALK_SPEED

static func fmt_m(m: float) -> String:
	if m >= 1000.0:
		return "%.2f km" % (m / 1000.0)
	return "%d m" % int(round(m))

static func fmt_s(s: float) -> String:
	if s < 60.0:
		return "%d sec" % int(ceil(s))
	return "%d min %d sec" % [int(s / 60.0), int(fmod(s, 60.0))]

## One line: "620 m · about 2 min 4 sec walking (combat not included) · 1 waypoint transfer".
static func summary(p: Dictionary) -> String:
	if not p.get("ok", false):
		return p.get("reason", "No known route.")
	var s := "%s · walking estimate %s (combat not included)" % [fmt_m(p.walk_m), fmt_s(p.est_s)]
	if p.transfers > 0:
		s += " · %d waypoint transfer%s" % [p.transfers, "" if p.transfers == 1 else "s"]
	return s
