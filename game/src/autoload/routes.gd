extends Node
## The tracked journey (autoload `Routes`): the destination chosen on the M atlas and the route preference, replanned
## from the hero's real position with RoutePlanner. Answers the directions HUD and the minimap: the current
## instruction, the remaining walking distance, a guide point a few metres ahead on the road, and the route's polyline
## on the current map. Replans after a map change or a world-flag change, and when the hero has been more than
## OFF_ROUTE_M from the route for OFF_ROUTE_S (at most one replan per REPLAN_MIN_S), so a wrong turn is corrected
## without the arrow flickering between routes. Arriving clears the route; it never enters a door or uses a shrine.
## Also records non-public places (DataIsland `public: false`) when the hero walks near them.

signal changed
signal arrived(place_id: String)

const OFF_ROUTE_M := 10.0
const OFF_ROUTE_S := 1.0
const REPLAN_MIN_S := 0.5
const ARRIVE_M := 6.0
const LOOKAHEAD_M := 9.0
const DISCOVER_M := 16.0

var dest := ""
var mode := 0
var plan := {}
var instruction := ""
var note := ""
var remaining_m := 0.0
var guide := Vector3.ZERO           # world point to steer toward on the current map
var has_guide := false
var path_here: Array = []           # this map's part of the route (local XZ, travel order)
var along_here := 0.0               # the hero's progress along path_here
var replans := 0                    # for tests and the debug overlay
var _steps_here: Array = []         # [cumulative end distance, step index] per leg on this map
var _walk_after := 0.0              # walking metres on later maps
var _off_t := 0.0
var _since_plan := 99.0
var _pending := false
var _tick := 0.0
var _disc_t := 0.0

func _ready() -> void:
	Events.map_loaded.connect(func(_id: StringName) -> void: _request())
	Events.world_flag_set.connect(func(_f: StringName, _v: Variant) -> void: _request())
	Game.session_started.connect(_on_session)
	Game.session_ended.connect(_reset)

func active() -> bool:
	return dest != ""

## Start tracking a route to `place_id`.
func set_route(place_id: String, p_mode := 0) -> void:
	dest = place_id
	mode = p_mode
	if Game.hero:
		Game.hero.route = {"dest": dest, "mode": mode}
	replan()

func clear_route() -> void:
	_reset()
	if Game.hero:
		Game.hero.route = {}
	changed.emit()

func _reset() -> void:
	dest = ""
	plan = {}
	instruction = ""
	note = ""
	remaining_m = 0.0
	has_guide = false
	path_here = []
	_steps_here = []
	_pending = false

func _on_session() -> void:
	_reset()
	if Game.hero and not Game.hero.route.is_empty():
		dest = String(Game.hero.route.get("dest", ""))
		mode = int(Game.hero.route.get("mode", 0))
		_request()

func _request() -> void:
	if active():
		_pending = true

## The hero's position in the current map's local XZ.
func hero_local() -> Vector2:
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p) or Game.current_map == null:
		return Vector2.ZERO
	var l := Game.current_map.to_local(p.global_position) if p.is_inside_tree() and Game.current_map.is_inside_tree() else p.position
	return Vector2(l.x, l.z)

func replan() -> void:
	_since_plan = 0.0
	_pending = false
	_off_t = 0.0
	if not active() or Game.current_map == null:
		return
	plan = RoutePlanner.plan(Game.hero, Game.current_map_id, hero_local(), dest, mode)
	replans += 1
	_build_here()
	_update(0.0)
	changed.emit()

func _build_here() -> void:
	path_here = []
	_steps_here = []
	_walk_after = 0.0
	if not plan.get("ok", false):
		return
	var run := 0.0
	var local := true
	for leg in plan.legs:
		if local and leg.kind == "road" and StringName(leg.map) == Game.current_map_id:
			for i in (leg.points as Array).size():
				var pt: Vector2 = leg.points[i]
				if not path_here.is_empty() and (path_here[path_here.size() - 1] as Vector2).distance_to(pt) < 0.01:
					continue
				if not path_here.is_empty():
					run += (path_here[path_here.size() - 1] as Vector2).distance_to(pt)
				path_here.append(pt)
			_steps_here.append([run, leg.step])
		else:
			if local and _steps_here.is_empty():
				_steps_here.append([0.0, leg.step])
			local = false
			_walk_after += float(leg.metres)

func _process(delta: float) -> void:
	if not active() or not Game.in_session or Game.travelling:
		return
	_since_plan += delta
	if _pending and _since_plan >= REPLAN_MIN_S:
		replan()
		return
	_tick -= delta
	if _tick > 0.0:
		return
	_tick = 0.15
	_update(0.15)

func _update(dt: float) -> void:
	if not plan.get("ok", false):
		instruction = plan.get("reason", "No known route.")
		note = ""
		has_guide = false
		remaining_m = 0.0
		return
	var pos := hero_local()
	var here_left := 0.0
	var step := 0
	if path_here.size() >= 2:
		var pr := DataIsland.project(pos, path_here)
		along_here = pr.along
		var total := DataIsland.polyline_length(path_here)
		here_left = maxf(0.0, total - pr.along)
		var g := DataIsland.point_at(path_here, minf(total, pr.along + LOOKAHEAD_M))
		guide = Vector3(g.x, _ground_y(g), g.y)
		has_guide = true
		if pr.dist > OFF_ROUTE_M:
			_off_t += dt
			if _off_t >= OFF_ROUTE_S and _since_plan >= REPLAN_MIN_S:
				_pending = true
		else:
			_off_t = 0.0
		step = int(_steps_here[_steps_here.size() - 1][1])
		for s in _steps_here:
			if pr.along <= float(s[0]) + 0.5:
				step = int(s[1])
				break
		# at the end of this map's roads the next step is the link (the gate, a door, a shrine)
		if here_left < 3.0:
			var next := _first_leg_after_here()
			if not next.is_empty():
				step = int(next.step)
	else:
		has_guide = false
		if not _steps_here.is_empty():
			step = int(_steps_here[0][1])
	# the end of this map's roads: steer to the thing that carries the hero on (the gate road's boundary, a door, a
	# waypoint dais, a dungeon gate), not just to the junction beside it
	if path_here.size() < 2 or here_left < 3.0:
		var next := _first_leg_after_here()
		var tp: Variant = link_point(next) if not next.is_empty() else null
		if tp != null:
			guide = tp
			has_guide = true
			step = int(next.step)
			if path_here.size() < 2:
				here_left += Vector2(guide.x, guide.z).distance_to(pos)
	var steps: Array = plan.steps
	step = clampi(step, 0, steps.size() - 1)
	instruction = steps[step].text
	note = "" if steps[step].kind == "road" else steps[step].note
	remaining_m = here_left + _walk_after
	_check_arrival(pos, here_left)

## The first leg that is not a road on this map (the plan always starts here, so it is the one after this map's roads).
func _first_leg_after_here() -> Dictionary:
	for leg in plan.legs:
		if not (leg.kind == "road" and StringName(leg.map) == Game.current_map_id):
			return leg
	return {}

## World position of the object that performs a link leg on the current map, or null.
func link_point(leg: Dictionary) -> Variant:
	var map := Game.current_map
	if map == null or not map.is_inside_tree():
		return null
	var to_map := StringName(DataIsland.place(String(leg.get("to", ""))).get("map", ""))
	match leg.get("kind", ""):
		"boundary":
			for n in get_tree().get_nodes_in_group(&"map_exit"):
				if map.is_ancestor_of(n) and (n as MapExit).destination_map == to_map:
					return (n as Node3D).global_position
		"door":
			for n in get_tree().get_nodes_in_group(&"door"):
				if map.is_ancestor_of(n) and (n as DoorPortal).destination_map == to_map:
					return (n as Node3D).global_position
		"shrine", "dungeon":
			var from := DataIsland.place(String(leg.get("from", "")))
			var best: Node3D = null
			var bd := INF
			for t in map.teleporters():
				var d := 0.0
				if from.has("pos"):
					d = t.global_position.distance_to(map.to_global(Vector3(from.pos.x, t.position.y, from.pos.y)))
				if d < bd:
					bd = d
					best = t
			if best:
				return best.global_position
	return null

func _ground_y(p: Vector2) -> float:
	var pl := Game.player as Node3D
	return pl.global_position.y if pl else 0.0

func _check_arrival(pos: Vector2, here_left: float) -> void:
	var d := DataIsland.place(dest)
	if d.is_empty() or StringName(d.map) != Game.current_map_id:
		return
	var there := not d.has("pos") or pos.distance_to(d.pos) < ARRIVE_M or (path_here.size() >= 2 and here_left < ARRIVE_M and _walk_after <= 0.0 and _last_leg_local())
	if there:
		var name: String = d.name
		var id := dest
		clear_route()
		Events.notify.emit("You have arrived: %s" % name, &"discovery")
		arrived.emit(id)

func _last_leg_local() -> bool:
	if plan.legs.is_empty():
		return true
	var last: Dictionary = plan.legs[plan.legs.size() - 1]
	return last.kind == "road" and StringName(last.map) == Game.current_map_id

# ---- discovery of places that are not public knowledge -----------------------------------------------------

func _physics_process(delta: float) -> void:
	_disc_t -= delta
	if _disc_t > 0.0 or not Game.in_session or Game.hero == null or Game.current_map == null:
		return
	_disc_t = 0.5
	var pos := hero_local()
	for p in DataIsland.PLACES:
		if p.get("public", true) or Game.hero.known_places.has(p.id) or StringName(p.map) != Game.current_map_id:
			continue
		if p.has("pos") and pos.distance_to(p.pos) < DISCOVER_M:
			Game.hero.known_places[p.id] = true
			Events.notify.emit("Discovered: %s" % p.name, &"discovery")

## A place the hero knows about (public geography, or found on foot). Dungeons count once their map is discovered or
## their entrance is known; the temple sequence stays hidden until reached.
static func is_known(hero: HeroData, p: Dictionary) -> bool:
	if hero == null:
		return p.get("public", true)
	if p.kind == "dungeon":
		return hero.discovered_maps.has(StringName(p.map)) or (p.id == "catacombs")
	if not p.get("public", true):
		return hero.known_places.has(p.id)
	return true
