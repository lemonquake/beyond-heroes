class_name TreeState
extends RefCounted
## Ranks invested in a TreeDef, with prerequisite/point enforcement and safe refunds.

signal changed

var tree: TreeDef
var ranks := {}          # node id -> rank
## Class Transcendence: free ranks a hero earned (node id -> rank). They count as learned for prerequisites, are never
## paid points (points_spent, refunds, tree-point gates) and survive reset(). Set by HeroData from the hero's path.
var floors := {}

func _init(p_tree: TreeDef = null) -> void:
	tree = p_tree

func rank(id: StringName) -> int:
	return ranks.get(id, 0)

## Free ranks of a node (0 for ordinary nodes).
func floor_of(id: StringName) -> int:
	return int(floors.get(id, 0))

## Ranks bought with points.
func paid_rank(id: StringName) -> int:
	return maxi(0, rank(id) - floor_of(id))

## Points actually paid into this tree (granted free ranks excluded).
func points_spent() -> int:
	var t := 0
	for id in ranks:
		t += maxi(0, int(ranks[id]) - floor_of(id)) * int(tree.node(id).get("cost", 1))
	return t

## Replace the free ranks; every floored node is raised to at least its floor. Idempotent: never awards points.
func set_floors(f: Dictionary) -> void:
	floors.clear()
	for id in f:
		if tree.node(id).is_empty():
			continue
		floors[id] = clampi(int(f[id]), 0, int(tree.node(id).get("max_rank", 1)))
		if rank(id) < int(floors[id]):
			ranks[id] = int(floors[id])
	changed.emit()

## Empty string when the node can gain a rank; otherwise the reason.
func can_rank_up(id: StringName, available_points: int, hero_level: int) -> String:
	var n := tree.node(id)
	if n.is_empty():
		return "Unknown node"
	if rank(id) >= int(n.get("max_rank", 1)):
		return "Maximum rank"
	var cost := int(n.get("cost", 1))
	if available_points < cost:
		return "Requires %d point%s" % [cost, "s" if cost > 1 else ""]
	if hero_level < int(n.get("req_level", 1)):
		return "Requires level %d" % int(n.get("req_level", 1))
	if points_spent() < int(n.get("req_tree_points", 0)):
		return "Requires %d points spent in this tree" % int(n.get("req_tree_points", 0))
	var req: Array = n.get("requires", [])
	if not req.is_empty():
		var ok := false
		for r in req:
			if rank(r) > 0:
				ok = true
				break
		if not ok:
			var names := []
			for r in req:
				names.append(tree.node(r).get("name", String(r)))
			return "Requires %s" % " or ".join(names)
	for r in n.get("requires_all", []):
		if rank(r) <= 0:
			return "Requires %s" % tree.node(r).get("name", String(r))
	# Keystones in the same exclusive group are mutually exclusive.
	var ex: String = n.get("exclusive", "")
	if ex != "":
		for other in tree.nodes:
			if other.id != id and other.get("exclusive", "") == ex and rank(other.id) > 0:
				return "Excludes %s" % other.name
	return ""

func rank_up(id: StringName, available_points: int, hero_level: int) -> int:
	## Returns the number of points consumed (0 on failure).
	if can_rank_up(id, available_points, hero_level) != "":
		return 0
	ranks[id] = rank(id) + 1
	changed.emit()
	return int(tree.node(id).get("cost", 1))

## A rank can be removed if the node would still satisfy nothing-depends-on-it and tree-point gates stay valid.
func can_refund(id: StringName) -> String:
	if rank(id) <= 0:
		return "Not learned"
	if rank(id) <= floor_of(id):
		var by := StringName(tree.node(id).get("granted_by", &""))
		return "Granted by %s; it cannot be unlearned" % DataTranscendence.name_of(by) if by != &"" else "Granted rank; it cannot be unlearned"
	if rank(id) == 1:
		for dep in tree.dependents_of(id):
			if rank(dep.id) <= 0:
				continue
			var alt := false
			for r in dep.get("requires", []):
				if r != id and rank(r) > 0:
					alt = true
			if dep.get("requires_all", []).has(id) or (dep.get("requires", []).has(id) and not alt):
				return "%s depends on it" % dep.name
	var cost := int(tree.node(id).get("cost", 1))
	var after := points_spent() - cost
	for other_id in ranks:
		if ranks[other_id] > 0 and other_id != id and int(tree.node(other_id).get("req_tree_points", 0)) > after:
			return "%s needs more points in this tree" % tree.node(other_id).name
	return ""

func refund(id: StringName) -> int:
	if can_refund(id) != "":
		return 0
	ranks[id] = rank(id) - 1
	if ranks[id] <= 0:
		ranks.erase(id)
	changed.emit()
	return int(tree.node(id).get("cost", 1))

## Refund every paid rank (returns the points); granted free ranks stay.
func reset() -> int:
	var p := points_spent()
	ranks.clear()
	for id in floors:
		if int(floors[id]) > 0:
			ranks[id] = int(floors[id])
	changed.emit()
	return p

## Stat modifiers granted by ranked nodes (talents).
func modifiers() -> Array:
	var out: Array = []
	for id in ranks:
		var n := tree.node(id)
		if n.get("kind", "") == "passive":
			continue
		var r := tree.power_of(id, ranks[id])
		for m in n.get("mods", []):
			out.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, float(m[2]) * r, "Talent: %s" % n.name))
		var fl: Dictionary = n.get("flags", {})
		for f in fl:
			out.append(StatModifier.flat(StringName("flag_" + String(f)), float(fl[f]) * r, "Talent: %s" % n.name))
	return out

## Passive skills (bh-010): value at rank r = base + per_rank * (r - 1). `bonus` = +skill levels from items (only
## raises passives already learned, like every other skill).
func passive_modifiers(bonus := 0) -> Array:
	var out: Array = []
	for id in ranks:
		var n := tree.node(id)
		if n.get("kind", "") != "passive" or int(ranks[id]) <= 0:
			continue
		var r := tree.power_of(id, int(ranks[id]) + bonus)
		for m in n.get("mods", []):
			out.append(StatModifier.new(StringName(m[0]), int(m[1]) as StatModifier.Op, passive_value(m, r), n.name))
		var fl: Dictionary = n.get("flags", {})
		for f in fl:
			var value := minf(passive_value([f, 0, fl[f][0], fl[f][1]], r), float(DataClassRework.CAPS.get(f, INF)))
			out.append(StatModifier.flat(StringName("flag_" + String(f)), value, n.name))
	return out

## [stat, op, base, per_rank] at rank r.
static func passive_value(m: Array, r: float) -> float:
	var base := float(m[2])
	var per := float(m[3]) if m.size() > 3 else 0.0
	return base + per * (maxf(r, 1.0) - 1.0)

func to_dict() -> Dictionary:
	var d := {}
	for id in ranks:
		d[String(id)] = ranks[id]
	return d

## Returns points removed by the new side-ability caps, for old-save migration.
func from_dict(d: Dictionary) -> int:
	ranks.clear()
	var refunded := 0
	for k in d:
		var id := StringName(k)
		var n := tree.node(id)
		if not n.is_empty():
			var old_rank := clampi(int(d[k]), 0, TreeDef.LEVEL_MAX)
			ranks[id] = mini(old_rank, int(n.get("max_rank", 1)))
			refunded += (old_rank - int(ranks[id])) * int(n.get("cost", 1))
	changed.emit()
	return refunded
