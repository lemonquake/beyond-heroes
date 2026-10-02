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

## Main skills, passives and minor talents can be raised to this level.
const LEVEL_MAX := 25
## Past the level a node used to top out at (its `base_rank`) each extra level is worth this share of a normal one;
## single-level nodes (majors, keystones, one-off upgrades) grow far more slowly.
const TAIL := 0.5
const TAIL_SINGLE := 0.1

## Side upgrades have one or four levels; major talents and keystones are learned once.
## The authored cap is kept as `base_rank`. Safe to call twice.
func finalize_levels() -> void:
	for n in nodes:
		if not n.has("base_rank"):
			n["base_rank"] = int(n.get("max_rank", 1))
		match n.get("kind", ""):
			"upgrade":
				n["max_rank"] = 1 if int(n.base_rank) <= 1 else 4
			"major", "keystone":
				n["max_rank"] = 1
			_:
				n["max_rank"] = LEVEL_MAX

## Effective number of "ranks worth" of effect at `rank`: identical to `rank` up to `base`, then diminishing.
static func rank_power(rank: int, base: int) -> float:
	if rank <= base:
		return float(maxi(rank, 0))
	return float(base) + float(rank - base) * (TAIL_SINGLE if base <= 1 else TAIL)

func power_of(id: StringName, rank: int) -> float:
	var n := node(id)
	return rank_power(clampi(rank, 0, int(n.get("max_rank", 1))), int(n.get("base_rank", n.get("max_rank", 1))))

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
