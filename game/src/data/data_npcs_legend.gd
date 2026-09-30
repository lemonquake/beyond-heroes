class_name DataNpcsLegend
## bh-021: Paul David, the Tempest Blade — Class SX, the last of the Dawnbreakers who can still be found, living
## quietly by the lake in Olivar (docs/LORE.md §10). His name plate burns with the legends' effect (LegendPlate).
## World flags: mq_shard_taken (the hero carries the Dusk-Piercer Shard) -> the_three cutscene -> mq_three_told;
## boss_kethrax_defeated -> mq_kethrax_reported; boss_warden_defeated -> the Black Spire. Graph format: see Dialogue.

const LAKESIDE := Vector3(24.6, 0, -30.2)
## He speaks of Aljay and Roydo under Aljay's theme: a node's "music" plays until the conversation ends.
const ALJAY := &"aljay_theme"

static func build() -> Array:
	return [_paul_david()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _paul_david() -> NpcDef:
	return NpcDef.make(&"paul_david", "Paul David", {"title": "The Tempest Blade", "legend": &"paul_david",
		"portrait": "res://assets/ui/portraits/paul_david.png", "map": &"olivar",
		"position": LAKESIDE, "yaw": 200.0, "model": "res://assets/characters/paul_david.glb", "model_scale": 1.03,
		"idle_anims": [&"idle", &"idle_look"],
		"graph": {
			"entries": [
				[[{"flag": "boss_warden_defeated"}, {"flag": "mq_kethrax_reported"}, {"not_visited": "spire"}], "spire"],
				[[{"flag": "boss_kethrax_defeated"}, {"not_flag": "mq_kethrax_reported"}], "report"],
				[[{"flag": "mq_three_told"}], "hub"],
				[[{"flag": "mq_shard_taken"}], "shard"],
				[[{"not_visited": "stranger"}], "stranger"],
				[[], "stranger_hub"],
			],
			"nodes": {
				# ---- before the shard: a tired old swordsman who wants to be left alone
				"stranger": {"text": [
						"You have the look of someone the waypoint picked. It has poor taste, lately.",
						"**Paul David**. I sit by this water because it is quiet. Go and be a hero somewhere loud."],
					"choices": [
						{"text": "The plate over your name says Class SX. There is no such tier.", "next": "sx"},
						{"text": "Why here?", "next": "why_here"},
						_end("I will leave you to the lake."),
					]},
				"stranger_hub": {"text": "Still here. The lake is still quiet. One of us should be.",
					"choices": [
						{"text": "What is Class SX?", "next": "sx"},
						_end(),
					]},
				"sx": {"text": [
						"There was. The Registry minted it once, for three of us, and then it struck the three of us out of every book in Aubren.",
						"**Class SX**. They called it **Beyond**. You will not find it in a guild hall, and you should not want to."],
					"next": "stranger_hub"},
				"why_here": {"text": "Because three winters ago I stopped being needed, and a man has to sit somewhere. Olivar sells good bread. Ask **Pip**; he will tell you worse stories about me than I would.",
					"next": "stranger_hub"},
				# ---- the shard
				"shard": {"music": ALJAY, "text": [
						"...Where did you get that.",
						"No. Do not unwrap it. I can feel it through the cloth. It is **warm**. Three winters, and it is still warm.",
						"**Aldric** sent you. Of course he did. Then you had better hear it from someone who was there, and not from a song they burned."],
					"choices": [
						{"text": "Tell me what this is.", "next": "end", "actions": [{"cutscene": "the_three", "resume": "after_tale"}]},
					]},
				"after_tale": {"music": ALJAY, "text": [
						"So now you know what the Registry does not. **Aljay** did not turn. He was **sold**, and Roydo and I with him.",
						"That shard is the tip of **Dusk-Piercer**. Aljay broke it in **Kethrax**'s chest while they dragged him under. It glows while its master lives. It is glowing.",
						"And Kethrax has come back to the marsh to find it. With it, he could break what is left of Aljay's will. With it, **you** can break Kethrax: the lance remembers the wound."],
					"choices": [
						{"text": "Why not face him yourself?", "next": "brand"},
						{"text": "Where do I find him?", "next": "orders"},
					]},
				"brand": {"music": ALJAY, "text": [
						"Look at my hand. That is his **chain-brand**. While Kethrax lives, this hand will not close on a hilt; I have tried until the skin split.",
						"I cannot go. You can. The waypoint chose you. It chose Aljay once, too, when he was not much older than you."],
					"next": "orders"},
				"orders": {"music": ALJAY, "text": [
						"He will be where it happened: the **Weeping Causeway**, out past **Wyman Outpost**, at the old **Drowned Tollhouse**.",
						"Aldric keeps the **Marsh Gate** barred. Tell him Paul David says to open it; he still owes me a horse.",
						"Kill Kethrax, and one of the chains on Aljay breaks. So does this brand. Then come back and tell me. I will be here. I am always here."],
					"actions": [{"set_flag": "mq_three_told"}, {"give_xp": 120}, {"relationship": 15}],
					"choices": [
						{"text": "I will face him.", "next": "end"},
						{"text": "Tell me the story again first.", "next": "end", "actions": [{"cutscene": "the_three", "resume": "hub"}]},
					]},
				# ---- afterward
				"hub": {"branch": [
					[[{"flag": "boss_kethrax_defeated"}], "hub_after"],
					[[], "hub_before"],
				]},
				"hub_before": {"text": "The shard is still warm. So is he, somewhere. Kethrax is on the **Weeping Causeway**, past Wyman's **Marsh Gate**.",
					"choices": [
						{"text": "Tell me of Aljay and Roydo again.", "next": "end", "actions": [{"cutscene": "the_three", "resume": "hub"}]},
						{"text": "What was Aljay like?", "next": "aljay"},
						{"text": "And Roydo?", "next": "roydo"},
						{"text": "What is Class SX?", "next": "sx2"},
						_end(),
					]},
				"hub_after": {"text": "The lake is quiet tonight. For once it is the good kind of quiet.",
					"choices": [
						{"text": "Tell me of Aljay and Roydo again.", "next": "end", "actions": [{"cutscene": "the_three", "resume": "hub"}]},
						{"text": "What was Aljay like?", "next": "aljay"},
						{"text": "And Roydo?", "next": "roydo"},
						{"text": "What holds Aljay now?", "next": "chains", "conditions": [{"flag": "mq_kethrax_reported"}], "hidden_if_unmet": true},
						_end(),
					]},
				"aljay": {"music": ALJAY, "text": [
						"Stubborn. Kind, which nobody believed, because of the helm. He used to carry the old smith's grandchildren on his shoulders at the harvest fair with the Tyrant's fire still leaking out of his armour.",
						"The darkness spoke to him every night. Every morning he got up and walked the wall anyway. That is the whole of him."],
					"next": "hub"},
				"roydo": {"music": ALJAY, "text": [
						"Roydo laughed like a landslide and prayed like a child. When the Legion came up the causeway, he told us to go, and then he **became a wall**.",
						"His light went into the black water. People say he drowned. The Righteous Hammer does not drown. I have never found him, and I have never stopped looking."],
					"next": "hub"},
				"sx2": {"text": "**Class SX**, **Beyond**: above SSS. The Registry made it for us and unmade it after. The name is still true. The book is what lies.",
					"next": "hub"},
				"report": {"music": ALJAY, "text": [
						"You do not have to say it. I felt it. **Here.**",
						"Three winters this hand would not close. Look at it. The brand is ash.",
						"And on the **Black Spire**, one chain broke tonight. Only one. But he felt it; I would stake my life on it. He knows someone is coming."],
					"actions": [{"set_flag": "mq_kethrax_reported"}, {"give_xp": 400}, {"give_gold": 300}, {"skill_point": 1}, {"relationship": 25}],
					"next": "chains"},
				"chains": {"music": ALJAY, "text": [
						"Three chains hold him. **Kethrax**'s Tyrant-chain: gone. The **Ashen seal**, sworn over the Forgotten Temple's broken oath the same winter; it feeds on the Hollow Warden. And the last: the lie itself, the name they wrote on him. **Forsaken**.",
						"The winter we were away, **Morthar** held the Forgotten Temple alone. He was my friend. Give him rest, and the Ashen seal goes with him. Go through the Ruined Forest to the Catacombs; the dead will show you the way down."],
					"next": "hub"},
				"spire": {"music": ALJAY, "text": [
						"Morthar sleeps. Good. **Two chains**, then.",
						"The last one no blade can cut. It is written in the Registry at **Aubren**, in a High Registrar's hand: **Aljay, Forsaken**. We are going to make them take it back, and then we are going to the **Black Spire** to bring him home.",
						"Not today. You are not ready, and neither am I; I have three winters of rust to scrape off this arm. But soon. Keep that shard close. When it burns hot, he is calling."],
					"actions": [{"give_xp": 600}, {"talent_point": 1}, {"relationship": 25}],
					"choices": [
						{"text": "Soon, then.", "next": "end"},
					]},
			},
		}})
