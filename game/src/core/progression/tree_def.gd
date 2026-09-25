class_name TreeDef
extends Resource
## A progression tree (skill tree or talent tree). Nodes are Dictionaries for compact data authoring:
## {
##   id: StringName, name: String, kind: "skill" | "upgrade" | "minor" | "major" | "keystone",
##   icon: String, pos: Vector2 (grid units), max_rank: int, cost: int (points per rank),
##   requires: [ids]  (any one of them at rank >= 1; empty = root), requires_all: [ids],
##   req_level: int, req_tree_points: int (points already spent in this tree),
##   skill: StringName (kind skill/upgrade), params: {param: delta per rank} (upgrade),
##   mods: [[stat, op, value_per_rank], ...], flags: {flag: value_per_rank},
##   desc: String, branch: String
## }

@export var id: StringName
@export var display_name: String
@export var points_kind: StringName = &"skill"    # skill or talent
@export var branches: Array = []                   # [{name, color, x}] column captions
var nodes: Array = []
var _index := {}

func index() -> Dictionary:
	if _index.is_empty():
		for n in nodes:
			_index[n.id] = n
	return _index

func node(id: StringName) -> Dictionary:
	return index().get(id, {})

func dependents_of(id: StringName) -> Array:
	var out := []
	for n in nodes:
		if n.get("requires", []).has(id) or n.get("requires_all", []).has(id):
			out.append(n)
	return out
