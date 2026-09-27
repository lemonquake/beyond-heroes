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
##   desc: String, branch: String,
##   page: int (skill trees with several pages: Combat / Auras / Disciplines ...; default 0),
##   kind "passive" (bh-010): always-on ranked skill, mods: [[stat, op, base, per_rank]], flags: {flag: [base, per_rank]},
##   synergies (kind skill): [[node_id, pct_per_rank]] -> +pct% damage per rank of that node (Diablo II style)
## }

@export var id: StringName
@export var display_name: String
@export var points_kind: StringName = &"skill"    # skill or talent
@export var branches: Array = []                   # [{name, color, x, page}] column captions
@export var pages: Array = []                      # [{name, desc}] (empty = one page)
var nodes: Array = []
var _index := {}

func index() -> Dictionary:
	if _index.is_empty():
		for n in nodes:
			_index[n.id] = n
	return _index

func node(id: StringName) -> Dictionary:
	return index().get(id, {})

func page_count() -> int:
	return maxi(1, pages.size())

func nodes_on_page(page: int) -> Array:
	return nodes.filter(func(n): return int(n.get("page", 0)) == page)

func dependents_of(id: StringName) -> Array:
	var out := []
	for n in nodes:
		if n.get("requires", []).has(id) or n.get("requires_all", []).has(id):
			out.append(n)
	return out
