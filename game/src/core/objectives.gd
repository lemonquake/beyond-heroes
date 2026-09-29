class_name Objectives
## The main path as quest-ready objectives derived from world flags (a full quest system can replace this table).
## Each entry: {id, title, text, map (where it happens), place (DataIsland place the minimap and the quest route steer to),
## npc (who to see, if anyone), done_flag}. The first entry whose flag is not set is current.

const CHAIN := [
	{"id": "forest", "title": "The Fallen Village", "text": "Take the waypoint on the Sanctuary Terrace to the Ruined Forest and find the gate into the Catacombs.",
		"map": &"ruined_forest", "place": "catacombs", "done_flag": &"catacombs_ritual_seen", "step": "Find out what the dead are doing beneath the drowned chapel."},
	{"id": "temple", "title": "The First Oath", "text": "Enter the Forgotten Temple and find the altar that remembers the first oath.",
		"map": &"forgotten_temple", "place": "temple", "done_flag": &"temple_seal_broken", "step": "Break the seal on the temple sanctum."},
	{"id": "warden", "title": "The Hollow Throne", "text": "Face Morthar, the Hollow Warden, on his throne.",
		"map": &"boss_arena", "place": "throne", "done_flag": &"boss_warden_defeated", "step": "Defeat the Hollow Warden."},
	{"id": "after", "title": "A Quiet Valley", "text": "The dead sleep. Return to Malasugue; Elder Maelis wants to speak with you.",
		"map": &"sanctuary", "place": "town", "npc": &"maelis", "done_flag": &"", "step": "Speak with Elder Maelis."},
]

static func current(hero: HeroData) -> Dictionary:
	if hero == null:
		return {}
	for o in CHAIN:
		if o.done_flag == &"" or not bool(hero.world_flags.get(o.done_flag, false)):
			if o.id == "after" and hero.dialogue_visited(&"maelis", "warden_fallen"):
				return {}
			return o
	return {}

static func completed(hero: HeroData) -> Array:
	var out := []
	for o in CHAIN:
		if o.done_flag != &"" and bool(hero.world_flags.get(o.done_flag, false)):
			out.append(o)
	return out
