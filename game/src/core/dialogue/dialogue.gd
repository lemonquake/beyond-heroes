class_name Dialogue
extends RefCounted
## The dialogue model: a conversation graph plus the rules that evaluate it against the world. Data only (no UI).
##
## Graph: {"entries": [[conditions, node_id], ...], "nodes": {node_id: node}}
## Node:  {"speaker": String (npc name by default), "portrait": path, "text": String | [String, ...] (lines),
##         "voice": audio id (optional, voice-ready), "choices": [choice], "next": node_id, "actions": [action],
##         "conditions": [...]}
## Choice: {"text": String, "next": node_id | "end", "conditions": [...], "actions": [...], "hidden_if_unmet": bool}
##
## Conditions (all must hold): {"flag": id} {"not_flag": id} {"flag": id, "value": v} {"level_min": n} {"level_max": n}
##   {"class": id} {"visited": "node_id"} {"not_visited": "node_id"} {"item": base_id, "count": n} {"gold": n}
##   {"relationship_min": n} {"map": id}
## Actions: {"set_flag": id, "value": v} {"give_item": base_id, "count": n, "rarity": r} {"take_item": base_id, "count": n}
##   {"give_gold": n} {"take_gold": n} {"give_xp": n} {"open_shop": shop_id} {"relationship": delta}
##   {"event": id, ...} (quest-ready hook) {"unlock_teleporter": id} {"heal": 1} {"skill_point": n} {"talent_point": n}
##   {"service": "respec" | "heal"} (performed by the NPC service layer)
## Branch node: {"branch": [[conditions, node_id], ...]} jumps to the first matching node without showing anything.
##
## Text may mark important words with **double asterisks**; the UI highlights them.

var npc_id: StringName
var graph: Dictionary

func _init(p_npc: StringName = &"", p_graph: Dictionary = {}) -> void:
	npc_id = p_npc
	graph = p_graph

## First entry whose conditions hold (greetings react to world state).
func entry_node(hero: HeroData) -> String:
	for e in graph.get("entries", []):
		if check_all(e[0], hero):
			return String(e[1])
	return ""

func node(id: String) -> Dictionary:
	return graph.get("nodes", {}).get(id, {})

## Follow branch nodes to the first real node (max depth guards against authoring loops).
func resolve(id: String, hero: HeroData) -> String:
	for i in 8:
		var n := node(id)
		if not n.has("branch"):
			return id
		var nxt := ""
		for b in n.branch:
			if check_all(b[0], hero):
				nxt = String(b[1])
				break
		if nxt == "":
			return ""
		id = nxt
	push_warning("Dialogue branch loop at %s" % id)
	return ""

func lines_of(n: Dictionary) -> PackedStringArray:
	var t = n.get("text", "")
	if t is Array:
		return PackedStringArray(t)
	return PackedStringArray([String(t)])

## Choices visible for a node (unmet ones are hidden unless the node wants them shown disabled).
func choices(n: Dictionary, hero: HeroData) -> Array:
	var out := []
	for c in n.get("choices", []):
		var met := check_all(c.get("conditions", []), hero)
		if met or not c.get("hidden_if_unmet", true):
			var cc: Dictionary = c.duplicate()
			cc["enabled"] = met
			out.append(cc)
	return out

func check_all(conds: Array, hero: HeroData) -> bool:
	for c in conds:
		if not check(c, hero):
			return false
	return true

func check(c: Dictionary, hero: HeroData) -> bool:
	if hero == null:
		return false
	if c.has("flag"):
		var v = hero.world_flags.get(StringName(c.flag), false)
		return v == c.get("value", true) if c.has("value") else bool(v)
	if c.has("not_flag"):
		return not bool(hero.world_flags.get(StringName(c.not_flag), false))
	if c.has("level_min"):
		return hero.progress.level >= int(c.level_min)
	if c.has("level_max"):
		return hero.progress.level <= int(c.level_max)
	if c.has("class"):
		return hero.cls.id == StringName(c["class"])
	if c.has("visited"):
		return hero.dialogue_visited(npc_id, String(c.visited))
	if c.has("not_visited"):
		return not hero.dialogue_visited(npc_id, String(c.not_visited))
	if c.has("item"):
		return hero.inventory.count_of(StringName(c.item)) >= int(c.get("count", 1))
	if c.has("gold"):
		return hero.inventory.gold >= int(c.gold)
	if c.has("relationship_min"):
		return hero.relationship(npc_id) >= int(c.relationship_min)
	if c.has("map"):
		return hero.current_map == StringName(c.map)
	push_warning("Unknown dialogue condition %s" % c)
	return false

## Apply node/choice actions. Returns side requests for the UI layer (e.g. {"open_shop": id}).
func run_actions(actions: Array, hero: HeroData) -> Dictionary:
	var out := {}
	for a in actions:
		if a.has("set_flag"):
			var v = a.get("value", true)
			hero.world_flags[StringName(a.set_flag)] = v
			Events.world_flag_set.emit(StringName(a.set_flag), v)
		elif a.has("give_item"):
			var it := DB.make_item(StringName(a.give_item), int(a.get("rarity", BH.Rarity.COMMON)), maxi(1, hero.progress.level), int(a.get("seed", 0)))
			if it:
				it.count = int(a.get("count", 1))
				var left := hero.inventory.add(it)
				Events.notify.emit("Received %s" % it.display_name() if left == 0 else "Inventory full — %s lost" % it.display_name(), &"loot")
		elif a.has("take_item"):
			hero.inventory.consume(StringName(a.take_item), int(a.get("count", 1)))
		elif a.has("give_gold"):
			hero.inventory.gold += int(a.give_gold)
			hero.inventory.changed.emit()
			Events.gold_picked.emit(int(a.give_gold))
		elif a.has("take_gold"):
			hero.inventory.gold = maxi(0, hero.inventory.gold - int(a.take_gold))
			hero.inventory.changed.emit()
		elif a.has("give_xp"):
			hero.progress.add_xp(int(a.give_xp))
			Events.xp_gained.emit(int(a.give_xp))
		elif a.has("open_shop"):
			out["open_shop"] = StringName(a.open_shop)
		elif a.has("relationship"):
			hero.add_relationship(npc_id, int(a.relationship))
		elif a.has("event"):
			var args: Dictionary = a.duplicate()
			args.erase("event")
			Events.dialogue_event.emit(StringName(a.event), args)
		elif a.has("unlock_teleporter"):
			hero.unlocked_teleporters[StringName(a.unlock_teleporter)] = true
		elif a.has("heal"):
			out["heal"] = true
		elif a.has("service"):
			out["service"] = StringName(a.service)
		elif a.has("skill_point"):
			hero.progress.skill_points += int(a.skill_point)
			hero.progress.points_changed.emit()
		elif a.has("talent_point"):
			hero.progress.talent_points += int(a.talent_point)
			hero.progress.points_changed.emit()
		else:
			push_warning("Unknown dialogue action %s" % a)
	return out

## Convert **important words** to BBCode highlight.
static func highlight(text: String, color := "#f5cc75") -> String:
	var out := ""
	var parts := text.split("**")
	for i in parts.size():
		out += ("[color=%s]%s[/color]" % [color, parts[i]]) if i % 2 == 1 else parts[i]
	return out

static func plain(text: String) -> String:
	return text.replace("**", "")
