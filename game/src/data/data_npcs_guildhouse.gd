class_name DataNpcsGuildHouse
## The three people of the Guild House (bh-016): the steward who explains the guilds, opens the central quest board and
## grants charters for new guilds (bh-027), and one clerk at each old guild's counter. Graph format: see Dialogue. Positions are map-local (interior.gd, `int_guildhouse`).

const PORTRAIT := "res://assets/ui/portraits/%s.svg"
const CHAR := "res://assets/characters/%s.glb"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]

static func build() -> Array:
	return [_hollis(), _bram(), _sabeth(), grand_master(&"grand_master_edran", &"int_guildhouse", GRAND_MASTER_SPOT, 90.0)]

## Class Transcendence: where Grand Master Edran Vale stands in the Guild House (west of the benches, clear of the
## steward's table, the doors, the counters and the walkways).
const GRAND_MASTER_SPOT := Vector3(-8.6, 0, 2.8)

## A Grand Master: the public Class Transcendence service (no guild, rank, quest, gold or item asked). Any Guild House
## map can place one with its own id and spot; the services and the conversation are the same everywhere.
static func grand_master(id: StringName, map: StringName, pos: Vector3, yaw: float) -> NpcDef:
	var n := NpcDef.make(id, "Edran Vale", {"title": "Grand Master", "portrait": PORTRAIT % "keeper", "map": map,
		"position": pos, "yaw": yaw, "model": CHAR % "matron", "tint": Color(0.62, 0.58, 0.48), "idle_anims": IDLES,
		"services": [&"transcend"], "shop": &"grand_master_armory",
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"I am **Edran Vale**, Grand Master of this House. Knights, Hunters, Mages and Shadowblades come to me when their training has carried them as far as it can.",
						"At **level 60** I can teach you your **first advancement**. At **level 120** you choose one of **two master classes**. You keep everything you have learned; you gain three new skills and three new talents each time.",
						"You need no guild seal, no rank and no gold for this. Only the level."],
					"next": "hub"},
				"hub": {"text": "What do you need, {hero}?",
					"choices": [
						{"text": "Advancement. Show me my Class.", "next": "end", "actions": [{"service": "transcend"}]},
						{"text": "Show me the armory.", "next": "end", "actions": [{"open_shop": "grand_master_armory"}]},
						{"text": "How does advancing work?", "next": "how"},
						{"text": "Is a master choice permanent?", "next": "permanent"},
						_end("Thank you, Grand Master."),
					]},
				"how": {"text": [
						"Each advancement adds a page to your Skills and to your Talents: three skills and three talents, each already at level 1. Further levels cost points as usual.",
						"Your skill bar is never rearranged. New skills go into empty slots; the rest wait in your Skills window.",
						"If you reached level 120 without advancing, you may take both advancements here, one after the other."],
					"next": "hub"},
				"permanent": {"text": [
						"Yes. A master class is chosen once. Resetting skills or talents does not change it.",
						"I will show you both masters side by side, and you confirm before anything is written down."],
					"next": "hub"},
			},
		}})
	return n

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _npc(id: StringName, name: String, d: Dictionary) -> NpcDef:
	d["idle_anims"] = IDLES
	d["map"] = &"int_guildhouse"
	return NpcDef.make(id, name, d)

static func _hollis() -> NpcDef:
	return _npc(&"hollis", "Hollis Varnay", {"title": "Steward of the Guild House", "portrait": PORTRAIT % "keeper",
		"position": Vector3(0, 0, -3.2), "yaw": 0.0, "model": CHAR % "matron", "tint": Color(0.5, 0.42, 0.3),
		"services": [&"guild_jobs", &"found_guild", &"guild_window"],
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[{"guild": "own"}, {"not_visited": "featured"}], "featured"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Welcome to the **Guild House**. I am Hollis Varnay, steward. I keep the doors, the ledgers and the peace, mostly in that order.",
						"Every guild in Malasugue keeps a counter under this roof now: the **Swordfin Company**, the **Lantern Covenant**, and the newer companies that came when the roads got worse. Their banners hang along the walls.",
						"And there is one **Guild Quest Board** for all of them. Any hero may take any job, whatever seal they carry — or none at all."],
					"next": "hub"},
				"featured": {"text": [
						"{hero}. Look up — that is your banner at the head of the hall. We moved it there this morning.",
						"I will be plain. Malasugue is tired of waiting. The town believes **you** are the one who can bring our own heroes home: **Aljay and Roydo**, wherever the Spire took them — and that you will do it together with **Paul David**.",
						"So the House features your guild. Every adventurer who walks in sees it first. Do not make me take it down."],
					"next": "hub"},
				"hub": {"text": "What can the House do for you, {hero}?",
					"choices": [
						{"text": "Show me the Guild Quest Board.", "next": "end", "actions": [{"service": "guild_jobs"}]},
						{"text": "I want to found a guild of my own.", "next": "found", "conditions": [{"not_guild": "own"}], "hidden_if_unmet": true},
						{"text": "About my guild...", "next": "mine", "conditions": [{"guild": "own"}], "hidden_if_unmet": true},
						{"text": "Which guilds keep a counter here?", "next": "guilds"},
						{"text": "How do the jobs work?", "next": "jobs"},
						{"text": "Tell me about the Swordfin Company.", "next": "swordfin"},
						{"text": "Tell me about the Lantern Covenant.", "next": "lantern"},
						{"text": "Which guild should I choose?", "next": "choose"},
						{"text": "Who teaches class advancement?", "next": "grand_master"},
						_end("Thank you, steward."),
					]},
				"found": {"text": [
						"A charter of your own? The town grants one for **{found_fee} gold**. You name the guild, write its words and fly whatever banner you please.",
						"Adventurers will come to you — every class, at levels not far below your own — until your hall is full. Six to begin with; the hall can be expanded. Lead them well and the guild grows: passives for every member, and for the day you fight many at once.",
						"And a Guildmaster can **call the guild to arms**: your members march to your side for a quarter of an hour."],
					"choices": [
						{"text": "Draw up the charter.", "next": "end", "actions": [{"service": "found_guild"}]},
						{"text": "Not yet.", "next": "hub"},
					]},
				"mine": {"text": "Your ledger is in order. Press **{guild_key}** any time to see your members, your passives and your Call to Arms — or I can open it for you now.",
					"choices": [
						{"text": "Open my guild's ledger.", "next": "end", "actions": [{"service": "found_guild"}]},
						{"text": "Back.", "next": "hub"},
					]},
				"guilds": {"text": "The old houses on either side, and the newer companies along the walls. Each counter has its banner and its terms; read them, register with whichever suits you. Heroes from other worlds who pass through leave their banners too — we hang those on the north wall.",
					"choices": [
						{"text": "Show me all the guilds.", "next": "end", "actions": [{"service": "guild_window"}]},
						{"text": "Back.", "next": "hub"},
					]},
				"jobs": {"text": [
						"Every guild posts on the **one board** now, and anyone may take anything: a Swordfin hero can carry Covenant errands and a hero with no seal at all can take both. You may carry **five** at once.",
						"Do the work anywhere on Salmonan; it counts as you go. Hand it in for gold. Your **tier** adds a little on top, a job your own guild posted pays a little more, and every job handed in earns your guild renown."],
					"next": "hub"},
				"swordfin": {"text": "Steel work. Culling, camps, elites and champions. **Bram Ostler** keeps their counter, on the left. The Company posts what it needs killed and pays promptly.",
					"next": "hub"},
				"lantern": {"text": "Legwork and care. Herbs, surveys, ledgers carried to other towns, things made rather than bought. **Sabeth Wynn** keeps their counter, on the right. The Covenant pays less per hour and asks fewer of you to bleed.",
					"next": "hub"},
				"grand_master": {"text": "**Grand Master Edran Vale**, by the west wall. Any hero of level 60 or more may ask him; you need no guild for it. Advancement gives you new skills and talents and keeps everything you have.",
					"next": "hub"},
				"choose": {"text": [
						"Swordfin if you want to stand in front: physical and impact damage, cheaper steel at Brannoc's forge and better bounty gold from elites.",
						"Lantern if you would rather know why you are standing there: magic damage, more mana, cheaper rooms at the Salted Marlin and stronger potions. The newer companies each have their own terms on their counters. Your tier follows you if you change your mind — or start a guild of your own."],
					"next": "hub"},
			},
		}})

static func _bram() -> NpcDef:
	return _npc(&"bram", "Bram Ostler", {"title": "Swordfin Bounty Sergeant", "portrait": PORTRAIT % "swordfin_quartermaster",
		"position": Vector3(-6.4, 0, -3.5), "yaw": 0.0, "model": CHAR % "officer", "tint": Color(0.22, 0.36, 0.7),
		"services": [&"guild_jobs_swordfin"],
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Bram Ostler, bounty sergeant. If it bites, burns or steals from the mill, it is on my list. If it is on my list, it pays.",
					"next": "hub"},
				"hub": {"text": "Looking for work, {hero}?",
					"choices": [
						{"text": "Show me the quest board.", "next": "end", "actions": [{"service": "guild_jobs"}]},
						{"text": "Do I have to be a member?", "next": "member"},
						_end("Not today."),
					]},
				"member": {"text": "Not any more. The steward put every guild's work on the one board and anyone may take it. Sign with the Company if you want our seal: {join_fee} gold at the hall, {transfer_fee} to switch sides.",
					"next": "hub"},
			},
		}})

static func _sabeth() -> NpcDef:
	return _npc(&"sabeth", "Sabeth Wynn", {"title": "Lantern Errand Scribe", "portrait": PORTRAIT % "lantern_scribe",
		"position": Vector3(6.4, 0, -3.5), "yaw": 0.0, "model": CHAR % "scholar", "tint": Color(0.5, 0.32, 0.7),
		"services": [&"guild_jobs_lantern"],
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Sabeth Wynn, errand scribe. The Covenant does not post bounties so much as chores with consequences. Someone has to walk the ledgers to Olivar, after all.",
					"next": "hub"},
				"hub": {"text": "Yes? Mind the ink.",
					"choices": [
						{"text": "Show me the quest board.", "next": "end", "actions": [{"service": "guild_jobs"}]},
						{"text": "Do I have to be a member?", "next": "member"},
						_end("Another time."),
					]},
				"member": {"text": "No — the board is open to everyone now. Lio keeps the register in Lantern House if you want our seal. We are very fond of people who bring back what they were sent for.",
					"next": "hub"},
			},
		}})
