class_name Objectives
## The main story as quest-ready objectives derived from world flags (bh-021: "The Forsaken Hero", docs/LORE.md §10).
## Each entry: {id, act, title, text, map (where it happens), place (DataIsland place the minimap and the quest route
## steer to), npc (who to see, if anyone), done_flag, step, level (recommended, optional)}. The first entry whose flag
## is not set is current. Every step keys on its own flag, so an old save simply picks up the first new step it has not
## done. Entries with done_flag "" end when their NPC's `visit` node has been seen.

const CHAIN := [
	# ---- Act I — The Waypoint's Choice
	{"id": "awaken", "act": 1, "title": "The Waypoint's Choice",
		"text": "The waypoint on the Sanctuary Terrace woke for you. Elder Maelis keeps the hearth in Malasugue's plaza; she has been waiting for someone it would choose.",
		"map": &"sanctuary", "place": "town", "npc": &"maelis", "done_flag": &"mq_maelis_orders", "step": "Speak with Elder Maelis by the hearth."},
	{"id": "gate", "act": 1, "title": "The Barred Gate",
		"text": "Maelis has an errand that leaves the walls. Captain Hald keeps the South Gate barred; show him the Elder's token.",
		"map": &"sanctuary", "place": "town_gate", "npc": &"hald", "done_flag": &"south_gate_open", "step": "Ask Captain Hald to open the South Gate."},
	{"id": "wyman", "act": 1, "title": "Orders for Wyman",
		"text": "Take the Fen Road across Westreach to Wyman Outpost. Sir Aldric Vane holds a sealed reliquary for Malasugue; bring back what is in it.",
		"map": &"wyman_outpost", "place": "wy_camp", "npc": &"aldric", "done_flag": &"mq_shard_taken", "step": "Ask Sir Aldric Vane at Wyman Outpost for the sealed reliquary.", "level": 2},
	{"id": "olivar", "act": 1, "title": "The Swordsman by the Lake",
		"text": "The reliquary held the broken tip of a black lance that glows like an ember. Aldric's letter names an old swordsman living by the lake in Olivar: Paul David.",
		"map": &"olivar", "place": "olv_paul", "npc": &"paul_david", "done_flag": &"mq_three_told", "step": "Bring the Dusk-Piercer Shard to Paul David in Olivar.", "level": 3},
	# ---- Act II — The Chain-Marshal
	{"id": "marsh", "act": 2, "title": "The Marsh Gate",
		"text": "Kethrax, the Chain-Marshal who took Aljay, has come back to Reedwater Marsh for the shard. Paul David's word opens the Marsh Gate at Wyman Outpost.",
		"map": &"wyman_outpost", "place": "wy_camp", "npc": &"aldric", "done_flag": &"mq_marsh_gate_open", "step": "Return to Sir Aldric at Wyman Outpost; he will open the Marsh Gate.", "level": 4},
	{"id": "kethrax", "act": 2, "title": "The Chain-Marshal",
		"text": "Cross the Weeping Causeway to the Drowned Tollhouse, where the Dawnbreakers were betrayed, and end Kethrax. His chains hold Aljay in the Black Spire; his brand holds Paul David's sword hand.",
		"map": &"weeping_causeway", "place": "wc_tollhouse", "done_flag": &"boss_kethrax_defeated", "step": "Defeat Kethrax on the Weeping Causeway.", "level": 6},
	{"id": "report", "act": 2, "title": "A Chain Breaks",
		"text": "Kethrax is dead and one of the chains on the Black Spire broke with him. Paul David will want to know — and to see his hand.",
		"map": &"olivar", "place": "olv_paul", "npc": &"paul_david", "done_flag": &"mq_kethrax_reported", "step": "Return to Paul David in Olivar."},
	# ---- Act III — The Hollow Warden (the winter the Dawnbreakers were away)
	{"id": "forest", "act": 3, "title": "The Fallen Village",
		"text": "The winter the Dawnbreakers were betrayed, the Ashen Circle struck the Forgotten Temple and Morthar, the last Warden, was hollowed holding it alone. Take the waypoint on the Sanctuary Terrace to the Ruined Forest and find the gate into the Catacombs.",
		"map": &"ruined_forest", "place": "catacombs", "done_flag": &"catacombs_ritual_seen", "step": "Find out what the dead are doing beneath the drowned chapel.", "level": 5},
	{"id": "temple", "act": 3, "title": "The First Oath", "text": "Enter the Forgotten Temple and find the altar that remembers the first oath.",
		"map": &"forgotten_temple", "place": "temple", "done_flag": &"temple_seal_broken", "step": "Break the seal on the temple sanctum.", "level": 8},
	{"id": "warden", "act": 3, "title": "The Hollow Throne", "text": "Face Morthar, the Hollow Warden, on his throne. Paul David asked you to give his old friend rest.",
		"map": &"boss_arena", "place": "throne", "done_flag": &"boss_warden_defeated", "step": "Defeat the Hollow Warden.", "level": 10},
	{"id": "after", "act": 3, "title": "A Quiet Valley", "text": "The dead sleep. Return to Malasugue; Elder Maelis wants to speak with you.",
		"map": &"sanctuary", "place": "town", "npc": &"maelis", "done_flag": &"", "visit": "warden_fallen", "step": "Speak with Elder Maelis."},
	{"id": "spire", "act": 3, "title": "The Road to the Black Spire",
		"text": "Two of the three chains are broken. Paul David has been counting the days until someone could say it aloud: it is time to bring Aljay home.",
		"map": &"olivar", "place": "olv_paul", "npc": &"paul_david", "done_flag": &"", "visit": "spire", "step": "Speak with Paul David in Olivar."},
]

static func current(hero: HeroData) -> Dictionary:
	if hero == null:
		return {}
	for o in CHAIN:
		if is_done(hero, o):
			continue
		return o
	return {}

static func is_done(hero: HeroData, o: Dictionary) -> bool:
	if o.done_flag != &"":
		return bool(hero.world_flags.get(o.done_flag, false))
	return hero.dialogue_visited(StringName(o.npc), String(o.get("visit", "")))

static func completed(hero: HeroData) -> Array:
	var out := []
	for o in CHAIN:
		if is_done(hero, o):
			out.append(o)
	return out

static func by_id(id: String) -> Dictionary:
	for o in CHAIN:
		if o.id == id:
			return o
	return {}

## "Act I — The Waypoint's Choice" style header for the tracker.
static func act_name(act: int) -> String:
	return ["", "Act I — The Waypoint's Choice", "Act II — The Chain-Marshal", "Act III — The Hollow Warden"][clampi(act, 0, 3)]
