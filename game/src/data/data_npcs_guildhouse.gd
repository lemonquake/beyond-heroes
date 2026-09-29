class_name DataNpcsGuildHouse
## The three people of the Guild House (bh-016): the steward who explains both guilds and opens the job boards, and one
## clerk at each guild's counter. Graph format: see Dialogue. Positions are map-local (interior.gd, `int_guildhouse`).

const PORTRAIT := "res://assets/ui/portraits/%s.svg"
const CHAR := "res://assets/characters/%s.glb"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]

static func build() -> Array:
	return [_hollis(), _bram(), _sabeth()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _npc(id: StringName, name: String, d: Dictionary) -> NpcDef:
	d["idle_anims"] = IDLES
	d["map"] = &"int_guildhouse"
	return NpcDef.make(id, name, d)

static func _hollis() -> NpcDef:
	return _npc(&"hollis", "Hollis Varnay", {"title": "Steward of the Guild House", "portrait": PORTRAIT % "keeper",
		"position": Vector3(0, 0, -3.2), "yaw": 0.0, "model": CHAR % "matron", "tint": Color(0.5, 0.42, 0.3),
		"services": [&"guild_jobs"],
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Welcome to the **Guild House**. I am Hollis Varnay, steward. I keep the doors, the ledgers and the peace, mostly in that order.",
						"The **Swordfin Company** and the **Lantern Covenant** hold their own halls elsewhere in Malasugue. This is the house they share: a counter for each, one board of odd jobs for each, and a rule that nobody draws steel under this roof."],
					"next": "hub"},
				"hub": {"text": "Which counter can I point you to, {hero}?",
					"choices": [
						{"text": "Show me the job boards.", "next": "end", "actions": [{"service": "guild_jobs"}]},
						{"text": "How do the jobs work?", "next": "jobs"},
						{"text": "Tell me about the Swordfin Company.", "next": "swordfin"},
						{"text": "Tell me about the Lantern Covenant.", "next": "lantern"},
						{"text": "Which guild should I choose?", "next": "choose"},
						_end("Thank you, steward."),
					]},
				"jobs": {"text": [
						"Each guild posts four jobs at a time, for heroes of your level. **Only a registered member** may take a guild's jobs, and you may carry **three** at once.",
						"Do the work anywhere on Salmonan; it counts as you go. Come back and hand it in, and the guild pays in gold. Your **tier** adds a little on top, and a fresh posting replaces every one you finish."],
					"next": "hub"},
				"swordfin": {"text": "Steel work. Culling, camps, elites and champions. **Bram Ostler** keeps their counter, on the left. The Company posts what it needs killed and pays promptly.",
					"next": "hub"},
				"lantern": {"text": "Legwork and care. Herbs, surveys, ledgers carried to other towns, things made rather than bought. **Sabeth Wynn** keeps their counter, on the right. The Covenant pays less per hour and asks fewer of you to bleed.",
					"next": "hub"},
				"choose": {"text": [
						"Swordfin if you want to stand in front: physical and impact damage, cheaper steel at Brannoc's forge and better bounty gold from elites.",
						"Lantern if you would rather know why you are standing there: magic damage, more mana, cheaper rooms at the Salted Marlin and stronger potions. Your tier follows you if you change your mind. It is only the transfer fee that follows you too."],
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
						{"text": "Show me the Company's bounties.", "next": "end", "actions": [{"service": "guild_jobs_swordfin"}]},
						{"text": "Do I have to be a member?", "next": "member"},
						_end("Not today."),
					]},
				"member": {"text": "To take Swordfin work, yes. Register at the Company's hall, or use the steward's ledger here. {join_fee} gold to sign on, {transfer_fee} to switch sides. Then the board is yours.",
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
						{"text": "Show me the Covenant's errands.", "next": "end", "actions": [{"service": "guild_jobs_lantern"}]},
						{"text": "Do I have to be a member?", "next": "member"},
						_end("Another time."),
					]},
				"member": {"text": "For Covenant errands, yes. Lio keeps the register in Lantern House, and the steward can take a transfer. We are very fond of people who bring back what they were sent for.",
					"next": "hub"},
			},
		}})
