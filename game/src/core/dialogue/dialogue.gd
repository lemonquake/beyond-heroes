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
##   {"relationship_min": n} {"map": id} {"guild": id} {"not_guild": id} {"no_guild": true} {"any_guild": true}
##   {"tier_min": rank} {"tier_max": rank} {"can_promote": true} {"rested": true} {"tempo_fallen": true} {"tempos_min": n}
## Actions: {"set_flag": id, "value": v} {"give_item": base_id, "count": n, "rarity": r} {"take_item": base_id, "count": n}
##   {"give_gold": n} {"take_gold": n} {"give_xp": n} {"open_shop": shop_id} {"relationship": delta}
##   {"event": id, ...} (quest-ready hook) {"unlock_teleporter": id} {"heal": 1} {"skill_point": n} {"talent_point": n}
##   {"cutscene": id, "resume": node_id} (bh-021: the conversation closes, the cutscene plays, then it reopens at `resume`)
##   {"service": "respec" | "heal" | "rest" | "mystic_heal" | "promote" | "join_swordfin" | "join_lantern" | "tempo_hire" |
##   "tempo_revive"}
##   (performed by the NPC service layer after the player confirms the price)
## Text placeholders filled from the hero: {tempo} (the starter Tempo's name) {hero} {tier} {tier_letter} {guild} {rest_fee} {mystic_fee} {next_tier}
##   {promo_fee} {promo_level} {promo_deed} {promo_deed_text} {join_fee} {transfer_fee} {champions} {clears}
##   and {key:<input action>} — the key currently bound to that action ("I", "Space", "LMB"), so tutorials never quote
##   a stale key after the player rebinds it.
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
	if c.has("guild"):
		return hero.guild == StringName(c.guild)
	if c.has("not_guild"):
		return hero.guild != StringName(c.not_guild)
	if c.has("no_guild"):
		return hero.guild == &""
	if c.has("any_guild"):
		return hero.guild != &""
	if c.has("tier_min"):
		return hero.tier >= int(c.tier_min)
	if c.has("tier_max"):
		return hero.tier <= int(c.tier_max)
	if c.has("can_promote"):
		return bool(GuildRules.next_promotion(hero).ok) == bool(c.can_promote)
	if c.has("rested"):
		return hero.is_rested() == bool(c.rested)
	if c.has("tempo_fallen"):
		return TempoRules.has_fallen(hero) == bool(c.tempo_fallen)
	if c.has("tempos_min"):
		return hero.tempos.size() >= int(c.tempos_min)
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
		elif a.has("cutscene"):
			out["cutscene"] = {"id": StringName(a.cutscene), "resume": String(a.get("resume", ""))}
		elif a.has("skill_point"):
			hero.progress.skill_points += int(a.skill_point)
			hero.progress.points_changed.emit()
		elif a.has("talent_point"):
			hero.progress.talent_points += int(a.talent_point)
			hero.progress.points_changed.emit()
		else:
			push_warning("Unknown dialogue action %s" % a)
	hero.check_promotions()
	return out

## Fill {placeholders} with live values (prices, tier) so dialogue never quotes a stale fee.
static func fill(text: String, hero: HeroData) -> String:
	if not "{" in text:
		return text
	text = fill_keys(text)
	if hero == null or not "{" in text:
		return text
	var p := GuildRules.next_promotion(hero)
	var nxt: int = p.get("rank", -1)
	var g := DataGuilds.guild(hero.guild)
	var vals := {
		"hero": hero.hero_name, "tier": DataGuilds.tier_name(hero.tier), "tier_letter": DataGuilds.letter(hero.tier),
		"guild": String(g.get("name", "no guild")), "rest_fee": str(NpcServices.rest_cost(hero)),
		"mystic_fee": str(NpcServices.mystic_heal_cost(hero)),
		"next_tier": ("Class %s" % DataGuilds.letter(nxt)) if nxt > 0 else "none",
		"promo_fee": str(p.get("fee", 0)), "promo_level": str(p.get("level", 0)), "promo_deed": String(p.get("deed", "")),
		"promo_deed_text": String(p.get("deed", "")) if String(p.get("deed", "")) != "" else "none required",
		"join_fee": str(DataGuilds.tier(1).fee), "transfer_fee": str(DataGuilds.TRANSFER_FEE),
		"tempo": starter_name(hero),
	}
	# bh-007: champions (minibosses) and the clear counter behind Olivar's stock
	if "{champions}" in text:
		vals["champions"] = DataMinibosses.rumours(hero)
	vals["clears"] = str(hero.clear_count)
	for k in vals:
		text = text.replace("{%s}" % k, vals[k])
	return text

## The hero's first Tempo, as the guide and the Field Guide name it (bh-015: rolled per hero).
static func starter_name(hero: HeroData) -> String:
	if hero != null and hero.starter_name != "":
		return hero.starter_name
	return String(DataTempos.STARTER.name)

## Replace every {key:<action>} with the key bound to that input action (or the action name if it has none).
static func fill_keys(text: String) -> String:
	if Settings.touch_mode:
		text = _touch_phrases(text)
	var at := text.find("{key:")
	while at >= 0:
		var close := text.find("}", at)
		if close < 0:
			break
		var action := text.substr(at + 5, close - at - 5)
		var k := Settings.binding_text(StringName(action)) if not Settings.touch_mode else String(TOUCH_NAMES.get(action, action.capitalize()))
		text = text.substr(0, at) + (k if k != "" else action.capitalize()) + text.substr(close + 1)
		at = text.find("{key:", at)
	return text

## Touch play (bh-008): the on-screen control each action lives on, and whole keyboard phrases said the touch way.
const TOUCH_NAMES := {"primary": "Attack", "secondary": "Heavy", "dodge": "Dodge", "guard": "Guard", "interact": "Interact",
	"skill_1": "Skill 1", "skill_2": "Skill 2", "skill_3": "Skill 3", "skill_4": "Skill 4", "skill_5": "Skill 5", "skill_6": "Skill 6",
	"potion_health": "the HP orb", "potion_mana": "the Mana orb", "inventory": "Bag", "chat": "Chat", "pause": "Back",
	"character": "Menu > Character", "skills": "Menu > Skills", "talents": "Menu > Talents", "tempos": "Menu > Tempos",
	"world_map": "the minimap", "guide": "Menu > Field Guide", "show_loot": "the labels", "attack_in_place": "Attack",
	"move_up": "the stick", "move_down": "the stick", "move_left": "the stick", "move_right": "the stick"}
const TOUCH_PHRASES := [
	["**{key:move_up} {key:move_left} {key:move_down} {key:move_right}** to move; you face the cursor.",
		"The **stick** under your left thumb moves you; your blows turn toward the nearest enemy."],
	[" and holding it keeps the chain going", ", and holding it keeps the chain going"],
	["keys **{key:skill_1}** to **{key:skill_6}**", "the round buttons around **Attack**: tap one to cast at the nearest enemy, or drag it to aim"],
	["Your skills sit on the bar at the bottom,", "Your skills sit on"],
	["Hold **{key:show_loot}** to see everything lying on the ground, and click an item to pick it up. The mouse wheel zooms the view.",
		"Tap an item's name on the ground to pick it up, or walk over it with Auto-Loot on. Pinch the screen to zoom."],
	["**{key:potion_health}** drinks a health draught, **{key:potion_mana}** a mana draught. The **Potion Belt** in your Inventory puts any potion on either key.",
		"Tap **the HP orb** to drink a health draught, **the Mana orb** for a mana draught. The **Potion Belt** in your Bag puts any potion on either orb."],
	["**{key:inventory}** Inventory, **{key:character}** Character, **{key:skills}** Skills, **{key:talents}** Talents, **{key:tempos}** Tempos, **{key:world_map}** Map.",
		"**Bag** opens your Inventory; **Menu** has Character, Skills, Talents, Tempos and the rest; tap **the minimap** for the Map."],
	["**{key:chat}** opens the chat line; **{key:pause}** closes a window, or pauses.", "**Chat** opens the chat line; your phone's **Back** closes a window, or pauses."],
	["press **{key:guide}**", "open **Menu > Field Guide**"],
	["**{key:tempos}** opens my window.", "**Menu > Tempos** opens my window."],
]

static func _touch_phrases(text: String) -> String:
	for pair in TOUCH_PHRASES:
		text = text.replace(pair[0], pair[1])
	return text

## Convert **important words** to BBCode highlight.
static func highlight(text: String, color := "#f5cc75") -> String:
	var out := ""
	var parts := text.split("**")
	for i in parts.size():
		out += ("[color=%s]%s[/color]" % [color, parts[i]]) if i % 2 == 1 else parts[i]
	return out

static func plain(text: String) -> String:
	return text.replace("**", "")
