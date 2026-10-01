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

## bh-029: Act IV — Zarael, the Corrupted (docs/LORE.md §11; DataZarael). It opens when Kethrax falls (the ship comes to
## Wyman), so it runs beside Act III: the tracker shows it while the hero is on Zarael (or sailing for it), and once the
## main chain above is done.
const ZARAEL_LEVEL := 28
const ZARAEL := [
	{"id": "zr_ship", "act": 4, "title": "The Ship at Wyman",
		"text": "A ship from Zarael, the corrupted island in the east, has put in at Wyman Outpost's Marsh Jetty. Its captain is asking for the hero who killed Kethrax.",
		"map": &"wyman_outpost", "place": "wy_jetty", "npc": &"ilsa", "done_flag": &"zr_ship_sailed", "step": "Speak with Captain Ilsa Rhondar at the Marsh Jetty.", "level": 30},
	{"id": "zr_terax", "act": 4, "title": "Agdao",
		"text": "The ship has carried you to Agdao, Zarael's harbour town. Someone is waiting on the pier.",
		"map": &"agdao", "place": "agd_pier", "npc": &"terax", "done_flag": &"zr_terax_met", "step": "Meet Terax on Agdao's pier.", "level": 30},
	{"id": "zr_council", "act": 4, "title": "The Wirekeeper",
		"text": "Terax says the Wirekeeper, Halvessa Orn, keeps the Heartwire's last working conduit at the top of the Crown of Steps. She will tell you what is killing Agdao.",
		"map": &"agdao", "place": "agd_crown", "npc": &"wirekeeper", "done_flag": &"zr_wirekeeper_met", "step": "Climb the Crown of Steps and speak with Wirekeeper Halvessa Orn.", "level": 30},
	{"id": "zr_relays", "act": 4, "title": "Wire-sick",
		"text": "The Kharvenn chain-priests have chained three relay pylons in the Coilwood, and the Blackwire runs from them straight into Agdao's terraces. Cut the chains.",
		"map": &"zr_coilwood", "place": "zc_relays", "done_flag": &"zr_relays_cut", "step": "Cut the chains from the three relay pylons in the Coilwood.", "level": 32},
	{"id": "zr_vault_jade", "act": 4, "title": "The Jade Sepulchre",
		"text": "The first Vault, where the Wirewright kings sleep. Aljay and Terax emptied it two winters ago; it is full again. Its lord feeds the first ward pylon on the Bridge of Death.",
		"map": &"zr_coilwood", "place": "zc_jade", "done_flag": &"dg_jade_sepulchre_cleared", "step": "Defeat Quorrath, the Jade Sleeper, in the Jade Sepulchre.", "level": 36},
	{"id": "zr_vault_obsidian", "act": 4, "title": "The Obsidian Engine",
		"text": "The second Vault: the machine halls that spun the Heartwire's current up from the island's heat, now stoked with pain.",
		"map": &"zr_barrens", "place": "zb_obsidian", "done_flag": &"dg_obsidian_engine_cleared", "step": "Defeat Kalvex, the Engine Heart, in the Obsidian Engine.", "level": 42},
	{"id": "zr_vault_vein", "act": 4, "title": "The Veinworks",
		"text": "The third Vault goes down into the giant itself. The chains there were driven into something with a pulse.",
		"map": &"zr_barrens", "place": "zb_vein", "done_flag": &"dg_veinworks_cleared", "step": "Defeat Ysvharn, the Giant's Heart, in the Veinworks.", "level": 48},
	{"id": "zr_bridge", "act": 4, "title": "The Bridge of Death",
		"text": "The three Vaults are quiet and their ward pylons burn steady white again. Cross the Bridge of Death; Varrogh, the Deathspan Colossus, still holds the far end.",
		"map": &"bridge_of_death", "place": "br_platform", "done_flag": &"boss_deathspan_defeated", "step": "Cross the Bridge of Death and defeat Varrogh.", "level": 46},
	{"id": "zr_abbot", "act": 4, "title": "The Leash-Abbot",
		"text": "In the Heart Citadel, Orvul Dram, the Leash-Abbot, is chaining the Dawn Engine itself to wake Zarael on a leash.",
		"map": &"zr_citadel", "place": "hc_engine", "done_flag": &"boss_leash_abbot_defeated", "step": "Defeat Orvul Dram, the Leash-Abbot, at the Dawn Engine.", "level": 50},
	{"id": "zr_dawn", "act": 4, "title": "The Dawn Current",
		"text": "The chains on the Dawn Engine are loose. Wake it, and let the old current run clean and white through the Heartwire again.",
		"map": &"zr_citadel", "place": "hc_engine", "done_flag": &"zr_heartwire_restored", "step": "Wake the Dawn Engine.", "level": 50},
	{"id": "zr_home", "act": 4, "title": "Agdao Lit",
		"text": "Every lamp in Agdao is burning steady white. Terax is waiting on the pier, and has one more thing to tell you about Aljay.",
		"map": &"agdao", "place": "agd_pier", "npc": &"terax", "done_flag": &"", "visit": "dawn", "step": "Return to Terax in Agdao."},
]

static func current(hero: HeroData) -> Dictionary:
	if hero == null:
		return {}
	var main := _first_open(hero, CHAIN)
	var zr := _first_open(hero, ZARAEL) if bool(hero.world_flags.get(&"boss_kethrax_defeated", false)) else {}
	if not zr.is_empty():
		# on Zarael (or with the main story done) the island's own quest leads; a hero strong enough for Zarael who is
		# still finishing Act III on Salmonan is pointed at the ship as well
		if main.is_empty() or DataZarael.is_zarael_map(hero.current_map):
			return zr
		if int(main.get("act", 0)) >= 3 and hero.progress.level >= ZARAEL_LEVEL:
			return zr
	return main

static func _first_open(hero: HeroData, chain: Array) -> Dictionary:
	for o in chain:
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
	for o in CHAIN + ZARAEL:
		if is_done(hero, o):
			out.append(o)
	return out

static func by_id(id: String) -> Dictionary:
	for o in CHAIN + ZARAEL:
		if o.id == id:
			return o
	return {}

## "Act I — The Waypoint's Choice" style header for the tracker.
static func act_name(act: int) -> String:
	return ["", "Act I — The Waypoint's Choice", "Act II — The Chain-Marshal", "Act III — The Hollow Warden",
		"Act IV — Zarael, the Corrupted"][clampi(act, 0, 4)]
