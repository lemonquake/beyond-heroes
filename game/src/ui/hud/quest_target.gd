class_name QuestTarget
extends RefCounted
## bh-015: where the current objective (Objectives.current) is, seen from the hero's map — for the minimap's quest
## marker, its rim chevron and the gold quest trail.
##   final  the objective spot itself is on this map: the NPC to see, the trigger that completes it (a FlagTrigger named
##          Trigger_<done_flag>), the boss of its arena, or the objective's place on this map's surface
##   else   the way on toward it — the gate road's boundary, a door, a waypoint or a dungeon gate — found with the same
##          RoutePlanner the tracked route uses, plus this map's roads toward it (`path`, local XZ in travel order)
## Resolved at most once a second; the route is re-planned on a new map, when the objective changes, or once the hero
## has walked REPLAN_M from where it was planned.

const REPLAN_M := 20.0

var has := false
var final := false
var world := Vector3.ZERO
var path: Array = []
var title := ""
var step := ""
var id := ""
var _t := 0.0
var _plan := {}
var _plan_key := ""
var _plan_from := Vector2.INF
var _trigger_cache := {}            # "map/flag" -> FlagTrigger (or null)

func update(delta: float) -> void:
	_t -= delta
	if _t > 0.0:
		return
	_t = 1.0
	resolve()

## Force a fresh answer on the next update (a map load, a world flag).
func invalidate() -> void:
	_t = 0.0
	_plan_key = ""

func resolve() -> void:
	has = false
	final = false
	path = []
	var hero := Game.hero
	var map := Game.current_map
	var p := Game.player as Node3D
	if hero == null or map == null or not is_instance_valid(map) or not map.is_inside_tree() or p == null or not is_instance_valid(p):
		return
	var o := Objectives.current(hero)
	if o.is_empty():
		id = ""
		return
	id = String(o.id)
	title = String(o.title)
	step = String(o.get("step", ""))
	var spot: Variant = _spot_here(o, map)
	if spot != null:
		has = true
		final = true
		world = spot
		return
	var place_id := String(o.get("place", ""))
	var pl := DataIsland.place(place_id)
	if pl.is_empty():
		return
	if StringName(pl.map) == Game.current_map_id and pl.has("pos"):
		has = true
		final = true
		world = map.to_global(Vector3(pl.pos.x, 0.0, pl.pos.y))
		world.y = p.global_position.y
		return
	var here := Routes.hero_local()
	var key := "%s/%s" % [Game.current_map_id, place_id]
	if key != _plan_key or here.distance_to(_plan_from) > REPLAN_M:
		_plan = RoutePlanner.plan(hero, Game.current_map_id, here, place_id, RoutePlanner.Mode.ROADS)
		_plan_key = key
		_plan_from = here
	if not _plan.get("ok", false):
		return
	var next := {}
	for leg in _plan.legs:
		if leg.kind == "road" and StringName(leg.map) == Game.current_map_id:
			for pt in leg.points:
				if path.is_empty() or (path[path.size() - 1] as Vector2).distance_to(pt) > 0.01:
					path.append(pt)
		else:
			next = leg
			break
	var tp: Variant = Routes.link_point(next) if not next.is_empty() else null
	if tp != null:
		world = tp
		has = true
	elif path.size() >= 1:
		var last: Vector2 = path[path.size() - 1]
		world = map.to_global(Vector3(last.x, 0.0, last.y))
		world.y = p.global_position.y
		has = true
		final = next.is_empty()

## The objective's own spot on this map, or null.
func _spot_here(o: Dictionary, map: Node) -> Variant:
	var tree := map.get_tree()
	var npc := StringName(o.get("npc", &""))
	if npc != &"":
		for n in tree.get_nodes_in_group(&"npc"):
			if "def" in n and n.def and n.def.id == npc and map.is_ancestor_of(n):
				return (n as Node3D).global_position
	var flag := StringName(o.get("done_flag", &""))
	if flag != &"":
		var ck := "%s/%s" % [Game.current_map_id, flag]
		if not _trigger_cache.has(ck) or not is_instance_valid(_trigger_cache[ck]):
			_trigger_cache[ck] = map.find_child("Trigger_%s" % flag, true, false)
		var t: Node = _trigger_cache[ck]
		if t is Node3D:
			return (t as Node3D).global_position
	if StringName(o.get("map", &"")) == Game.current_map_id or String(o.get("place", "")) != "" \
			and StringName(DataIsland.place(String(o.place)).get("map", "")) == Game.current_map_id:
		for b in tree.get_nodes_in_group(&"boss"):
			if b is Node3D and map.is_ancestor_of(b) and bool(b.get("alive")):
				return (b as Node3D).global_position
	return null

## This map's quest trail in world space (for drawing), empty when there is none.
func trail_world() -> PackedVector3Array:
	var out := PackedVector3Array()
	var map := Game.current_map
	if map == null or path.size() < 2:
		return out
	for pt in path:
		out.append(map.to_global(Vector3(pt.x, 0.0, pt.y)))
	return out
