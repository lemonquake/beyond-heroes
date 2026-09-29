class_name DataNpcs
## The people of Malasugue Town (outdoor posts) and their conversations. The indoor townsfolk live in DataNpcsTown. Graph format: see Dialogue.
## World flags used: catacombs_ritual_seen, temple_seal_broken, boss_warden_defeated, south_gate_open (Hald opens the gate).

const MAGE := "res://assets/characters/mage.glb"
const KNIGHT := "res://assets/characters/knight.glb"
const TOWN := "res://assets/characters/%s.glb"
const TOWN_IDLES := [&"idle", &"idle_look", &"idle_adjust"]
const PORTRAIT := "res://assets/ui/portraits/%s.svg"

static func build() -> Array:
	return [_maelis(), _tovin(), _brannoc(), _seris(), _hald(), _stranger()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

# ------------------------------------------------------------------------------------------------ Elder Maelis
static func _maelis() -> NpcDef:
	return NpcDef.make(&"maelis", "Elder Maelis", {"title": "Keeper of the Hearth", "portrait": PORTRAIT % "elder",
		"position": Vector3(5.2, 0, -0.2), "yaw": -51.0, "model": TOWN % "elder", "tint": Color(0.55, 0.5, 0.42), "idle_anims": TOWN_IDLES,
		"graph": {
			"entries": [
				[[{"flag": "boss_warden_defeated"}, {"not_visited": "warden_fallen"}], "warden_fallen"],
				[[{"flag": "temple_seal_broken"}, {"not_visited": "seal"}], "seal"],
				[[{"flag": "catacombs_ritual_seen"}, {"not_visited": "ritual"}], "ritual"],
				[[{"not_visited": "first"}], "first"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"So the waypoint still answers. I had begun to think it would stay dark forever.",
						"This is **Malasugue**, the last lit hearth on this coast of Salmonan. That terrace is the **Sanctuary Terrace**; the light you came through lives there. Whatever you were before, here you are a guest.",
						"Take these. The road to the **Ruined Forest** eats the careless first."],
					"actions": [{"give_item": "health_potion", "count": 3}, {"relationship": 5}],
					"choices": [
						{"text": "What happened to this place?", "next": "history"},
						{"text": "Who else lives here?", "next": "people"},
						_end("I will manage. Farewell."),
					]},
				"hub": {"text": "The hearth is warm and the wards hold. What do you need, wanderer?",
					"choices": [
						{"text": "Tell me again what happened here.", "next": "history"},
						{"text": "Who can help me prepare?", "next": "people"},
						{"text": "Where should I go next?", "next": "advice"},
						{"text": "The Warden is dead. What now?", "next": "after", "conditions": [{"flag": "boss_warden_defeated"}]},
						_end(),
					]},
				"history": {"text": [
						"Three winters ago the **Hollow Warden** woke beneath the Forgotten Temple. He was sworn to guard the first oath. Something inside him forgot the oath and kept the sword.",
						"His dead march out of the **Catacombs** each night. The forest village fell first. We lit the hearth wards and we have held since."],
					"choices": [{"text": "Why not leave the valley?", "next": "leave"}, {"text": "I have heard enough.", "next": "hub"}]},
				"leave": {"text": "The waypoint is the only road out that the dead do not watch, and it answers only to those it chooses. It chose you. Draw your own conclusions.",
					"actions": [{"relationship": 2}], "next": "hub"},
				"people": {"text": [
						"Everything a hero needs stands on **Merchant Row**, the signed street off the plaza's south-east corner. **Tovin** has General Goods (draughts, salts, scrolls); **Brannoc** sells Arms & Armor and keeps the Forge at the far end; nobody in the valley works steel better.",
						"**Seris** reads the Aether at her Arcana stand on the same street. She can mend wounds and, for a price, unmake the paths you have chosen. The Alchemy Table, the Workbench and the Tempo Shrine are there too.",
						"And **Captain Hald** watches the south gate. Ask him about the road."],
					"next": "hub"},
				"advice": {"branch": [
					[[{"not_flag": "catacombs_ritual_seen"}], "advice_forest"],
					[[{"flag": "catacombs_ritual_seen"}, {"not_flag": "temple_seal_broken"}], "advice_temple"],
					[[{"flag": "temple_seal_broken"}, {"not_flag": "boss_warden_defeated"}], "advice_throne"],
					[[{"flag": "boss_warden_defeated"}], "after"],
				]},
				"advice_forest": {"text": "Through the waypoint lies the **Ruined Forest**. Past the fallen village, across the river, there is a gate into the **Catacombs**. Find out what the dead are doing down there.", "next": "hub"},
				"advice_temple": {"text": "You saw their ritual circle. It points to the **Forgotten Temple**. Its sanctum is sealed by the first oath. There will be an **altar** that remembers it.", "next": "hub"},
				"advice_throne": {"text": "The seal is broken; the way to the **Hollow Throne** is open. When you face him, remember: he was a guardian once. Guardians lower their guard only to strike.", "next": "hub"},
				"ritual": {"text": [
						"You went into the Catacombs and came back. And you look like someone who saw a **ritual circle**.",
						"They are not merely raising the dead. They are feeding something. The Temple, then. It always comes back to the Temple."],
					"actions": [{"relationship": 5}, {"give_xp": 60}], "next": "hub"},
				"seal": {"text": [
						"I felt it in the hearth when the **seal of the first oath** broke. Every flame in Malasugue leaned toward the east.",
						"The Warden will know too. Rest, prepare, and go before he gathers his strength."],
					"actions": [{"relationship": 5}], "next": "hub"},
				"warden_fallen": {"text": [
						"The dead did not march last night. For the first time in three winters, **the valley slept**.",
						"You have done what our knights could not. Malasugue will remember your name, and I will teach you what I can."],
					"actions": [{"relationship": 20}, {"skill_point": 1}, {"talent_point": 1}, {"event": "warden_thanks"}],
					"choices": [{"text": "It was the right thing to do.", "next": "hub", "actions": [{"relationship": 5}]},
						{"text": "I expect to be paid.", "next": "paid"}]},
				"paid": {"text": "Honest, at least. Tovin has set aside a purse for you. Do not spend it all on draughts.",
					"actions": [{"give_gold": 250}, {"relationship": -5}], "next": "hub"},
				"after": {"text": "The valley is quiet, but the Aether is not. Seris says the waypoint hums at night, as if something far away is calling back. When you are ready, we will find out what.", "next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ Tovin
static func _tovin() -> NpcDef:
	return NpcDef.make(&"tovin", "Tovin", {"title": "Provisioner", "portrait": PORTRAIT % "merchant",
		"position": DataTownRows.npc_spot(&"tovin").position, "yaw": DataTownRows.npc_spot(&"tovin").yaw, "model": TOWN % "merchant", "tint": Color(0.62, 0.38, 0.2), "shop": &"tovin_goods",
		"idle_anims": TOWN_IDLES,
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "boss_warden_defeated"}, {"not_visited": "celebrate"}], "celebrate"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": "A new face! Tovin, provisioner. Draughts, salts, scrolls, bits of iron. If it keeps you breathing, I sell it. At a fair price, mostly.",
					"choices": [{"text": "Show me your wares.", "next": "end", "actions": [{"open_shop": "tovin_goods"}]},
						{"text": "Mostly?", "next": "mostly"}, _end("Another time.")]},
				"mostly": {"text": "Prices move with trust, friend. Be good to Malasugue and Malasugue is good to you. That is not a rule, it is just how people work.",
					"actions": [{"relationship": 3}], "next": "hub"},
				"hub": {"text": "Back again? Good. The shelves are fresher than the bread.",
					"choices": [
						{"text": "Show me your wares.", "next": "end", "actions": [{"open_shop": "tovin_goods"}]},
						{"text": "Any news?", "next": "news"},
						_end(),
					]},
				"news": {"branch": [
					[[{"not_flag": "catacombs_ritual_seen"}], "news_1"],
					[[{"flag": "catacombs_ritual_seen"}, {"not_flag": "boss_warden_defeated"}], "news_2"],
					[[{"flag": "boss_warden_defeated"}], "news_3"],
				]},
				"news_1": {"text": "Folk say lights move in the **Catacombs** at night. I say folk should buy more **Health Draughts**.", "next": "hub"},
				"news_2": {"text": "A **hooded stranger** walked in past the east side of Merchant Row two nights ago and has not left. Pays in old coin. Sells things I cannot name.", "next": "hub"},
				"news_3": {"text": "Business is terrible. Nobody needs **Purifying Salts** when the dead stay dead. I have never been happier.", "next": "hub"},
				"celebrate": {"text": "The hero of Malasugue! Here, on the house. Do not tell Brannoc, he will want the same.",
					"actions": [{"give_item": "rejuvenation_elixir", "count": 2}, {"relationship": 10}], "next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ Brannoc
static func _brannoc() -> NpcDef:
	return NpcDef.make(&"brannoc", "Brannoc", {"title": "Blacksmith", "portrait": PORTRAIT % "blacksmith",
		"position": DataTownRows.npc_spot(&"brannoc").position, "yaw": DataTownRows.npc_spot(&"brannoc").yaw, "model": TOWN % "smith", "tint": Color(0.3, 0.26, 0.22), "shop": &"brannoc_forge",
		"idle_anims": TOWN_IDLES,
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "temple_seal_broken"}, {"not_visited": "temple_steel"}], "temple_steel"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Mind the sparks. Brannoc. I make things that cut and things that stop cutting.",
						"Your gear is **Beginner** work. It will not survive the Catacombs. Bring me coin and I will fix that."],
					"choices": [{"text": "Let me see what you have.", "next": "end", "actions": [{"open_shop": "brannoc_forge"}]},
						{"text": "What makes good steel?", "next": "steel"},
						{"text": "My gear is fine.", "next": "fine"}]},
				"fine": {"text": "Then I will see you at your funeral. Bring the gear, I will want the scrap.", "actions": [{"relationship": -3}], "next": "hub"},
				"steel": {"text": [
						"Look at the **rarity** first. Common steel is honest and plain. From **Basic** up, the metal takes enchantments, and more of them the higher you go.",
						"**Licensed** pieces carry a guild stamp and a guild's trick. **Master** work has a perfected enchantment you will not find anywhere else.",
						"Past that, **Mythical**, **Legendary**, **Aether**. Those are not made. Those are found."],
					"actions": [{"relationship": 4}], "next": "hub"},
				"hub": {"text": "Forge is hot. What will it be?",
					"choices": [
						{"text": "Let me see what you have.", "next": "end", "actions": [{"open_shop": "brannoc_forge"}]},
						{"text": "Can I use your anvil?", "next": "anvil"},
						{"text": "Tell me about rarity again.", "next": "steel"},
						{"text": "Anything special in stock?", "next": "special"},
						_end("Keep the fire going."),
					]},
				"special": {"branch": [
					[[{"not_flag": "catacombs_ritual_seen"}], "special_no"],
					[[{"flag": "catacombs_ritual_seen"}], "special_yes"],
				]},
				"special_no": {"text": "Special? Come back when you have seen what is under the chapel. I will not waste my best plate on a stranger who has not.", "next": "hub"},
				"special_yes": {"text": "For you, yes. I rebuilt an **Aether Guardian** helm from the old order's patterns. Level eight or better, and it is yours for the right price.", "next": "hub"},
				"anvil": {"branch": [
					[[{"not_visited": "anvil_first"}], "anvil_first"],
					[[], "anvil_go"],
				]},
				"anvil_first": {"text": [
						"You want to work your own steel? Good. Saves me the sweat.",
						"Five **iron shards** make an **ingot**. Ingots, cured leather and the right monster parts make a blade or a plate, and it comes out **fine quality** every time, which is more than I can say for what the dead drop.",
						"Anything you do not want, break down on the anvil. Iron back, and dust if it was enchanted. The camp at **Wyman Outpost** keeps a field forge too, if you are ever out that way."],
					"actions": [{"relationship": 3}],
					"choices": [{"text": "Show me the anvil.", "next": "end", "actions": [{"service": "craft_forge"}]}, {"text": "Maybe later.", "next": "hub"}]},
				"anvil_go": {"text": "The anvil is yours. Do not dent it.", "next": "end", "actions": [{"service": "craft_forge"}]},
				"temple_steel": {"text": "You broke the temple seal. My forge flared blue the same night. Whatever steel they buried there, I want to see it. Bring me anything strange you find.",
					"actions": [{"relationship": 5}], "next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ Seris
static func _seris() -> NpcDef:
	return NpcDef.make(&"seris", "Seris", {"title": "Aether Mystic", "portrait": PORTRAIT % "mystic",
		"position": DataTownRows.npc_spot(&"seris").position, "yaw": DataTownRows.npc_spot(&"seris").yaw, "model": MAGE, "tint": Color(0.2, 0.35, 0.55), "shop": &"seris_arcana",
		"services": [&"mystic_heal", &"respec"], "idle_anims": [&"idle", &"idle_mage"],
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"The Aether bends around you. It does not do that for everyone.",
						"I am Seris. I sell what the Aether leaves behind, I mend what the dead break, and I can **unweave** the paths you have chosen, if you come to regret them."],
					"next": "hub"},
				"hub": {"text": "Ask.",
					"choices": [
						{"text": "Show me your arcana.", "next": "end", "actions": [{"open_shop": "seris_arcana"}]},
						{"text": "Mend my wounds ({mystic_fee} gold).", "next": "healed", "actions": [{"service": "mystic_heal"}]},
						{"text": "Unweave my skills and talents.", "next": "respec"},
						{"text": "What is the Aether?", "next": "aether"},
						_end(),
					]},
				"healed": {"text": [
						"The Aether remembers you whole, for a price. It always asks one.",
						"If you want mending that comes with a bed and a hot meal, **Hesta** lets rooms at the **Salted Marlin**, west of the plaza. Cheaper, and she does not stare."],
					"next": "hub"},
				"respec": {"text": "Every point you spent returns to you. **Starting skills** stay, they are part of you. The weaving costs gold; the price grows with your level.",
					"choices": [
						{"text": "Do it.", "next": "respec_done", "actions": [{"service": "respec"}]},
						{"text": "Not now.", "next": "hub"},
					]},
				"respec_done": {"text": "It is done. Choose more carefully. Or do not. I am paid either way.", "next": "hub"},
				"aether": {"text": [
						"The light between things. It runs through old steel in **engraved channels**, through the waypoints, through heroes.",
						"The rarest relics carry so much of it they change the hands that hold them. When you find an **Aether** relic, you will know. Everyone will know."],
					"actions": [{"relationship": 3}], "next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ Captain Hald
static func _hald() -> NpcDef:
	return NpcDef.make(&"hald", "Captain Hald", {"title": "Gate Captain", "portrait": PORTRAIT % "captain",
		"position": Vector3(-4.2, 0, 34.5), "yaw": 180.0, "model": KNIGHT, "tint": Color(0.5, 0.12, 0.1),
		"idle_anims": [&"idle", &"idle_knight", &"idle_look"],
		"graph": {
			"entries": [
				[[{"flag": "boss_warden_defeated"}, {"not_visited": "salute"}], "salute"],
				[[{"not_visited": "first"}], "first"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Halt. The south road has been closed three winters. This gate has not opened since the forest garrison fell.",
						"You came through the **waypoint**? Then you are either a hero or a very lost pilgrim. Which is it?"],
					"choices": [
						{"text": "A hero, apparently.", "next": "hero", "actions": [{"relationship": 3}]},
						{"text": "A lost pilgrim.", "next": "pilgrim"},
						{"text": "None of your business.", "next": "rude", "actions": [{"relationship": -5}]},
					]},
				"hero": {"text": "Good. Heroes I can use. Take this **Scroll of Return**. Read it anywhere and it will pull you back to the hearth. We have lost too many to long walks home.",
					"actions": [{"give_item": "return_scroll", "count": 1}], "next": "hub"},
				"pilgrim": {"text": "Lost pilgrims do not carry that much steel. Keep your secrets. But if you go through the waypoint, go armed.", "next": "hub"},
				"rude": {"text": "Fair enough. Just do not make trouble inside my walls.", "next": "hub"},
				"hub": {"text": "Gate holds. What do you need?",
					"choices": [
						{"text": "About the south road...", "next": "road", "conditions": [{"not_flag": "south_gate_open"}], "hidden_if_unmet": true},
						{"text": "How are the roads below?", "next": "road_open", "conditions": [{"flag": "south_gate_open"}], "hidden_if_unmet": true},
						{"text": "Advice for the fight?", "next": "tactics"},
						{"text": "How do elites work?", "next": "elites"},
						_end("Stay sharp."),
					]},
				"tactics": {"text": [
						"Do not stand and trade blows. **Dodge** through their swings. The roll carries you clear if you time it.",
						"Throw them into walls, pillars, each other. The **impact** hurts them more than your blade. And a **wet** enemy takes lightning like a rod in a storm."],
					"actions": [{"relationship": 2}], "next": "hub"},
				"elites": {"text": "Elites carry a name like **Flaming** or **Vampiric** above their heads. Each one changes how they fight. Read the name before you close in. They also carry better loot.", "next": "hub"},
				"road": {"text": [
						"The dead came up that road once. They have not come up it since; they keep to the forest now.",
						"But the farms below still feed this town, and nobody has walked to the **Old Mill** without an escort since spring. Goblins in the **Lantern Fields**, wolves on the cliffs, smugglers at **Tideglass Cove**. Nothing a hero cannot handle."],
					"choices": [
						{"text": "Open the gate. I will walk the roads.", "next": "road_opened", "actions": [{"set_flag": "south_gate_open"}, {"relationship": 5}]},
						{"text": "Not yet.", "next": "hub"},
					]},
				"road_opened": {"text": [
						"Then it is done. Lift the bar!",
						"The road forks below the gate: the **Mill Road** to the crossroads, the **Field Road** to the farms, the **Cove Steps** down to the sea. Press **M**: the cartographer's chart names every road we still keep, and it will walk you there if you ask it."],
					"next": "hub"},
				"road_open": {"text": "The gate stays open while you keep the roads. The **Forest Road** climbs from the Old Mill to the fallen village, if you would rather walk than trust the waypoint.", "next": "hub"},
				"salute": {"text": "Hero. The men want to raise the old banners over the south gate, for the first time in three winters. They want you to see it.",
					"actions": [{"set_flag": "south_gate_ceremony"}, {"relationship": 15}, {"give_gold": 150}], "next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ The Hooded Stranger
static func _stranger() -> NpcDef:
	return NpcDef.make(&"stranger", "Hooded Stranger", {"title": "Dealer in Rare Goods", "portrait": PORTRAIT % "stranger",
		"position": DataTownRows.npc_spot(&"stranger").position, "yaw": DataTownRows.npc_spot(&"stranger").yaw, "model": MAGE, "tint": Color(0.12, 0.1, 0.14), "shop": &"stranger_wares",
		"presence": [{"flag": "catacombs_ritual_seen"}],
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "boss_warden_defeated"}, {"not_visited": "aether_offer"}], "aether_offer"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"You smell of the catacombs. Good. People who go down there come back needing things.",
						"I deal in **rare goods**. Expensive, and worth it. I do not haggle and I do not explain where they come from."],
					"choices": [{"text": "Show me.", "next": "end", "actions": [{"open_shop": "stranger_wares"}]},
						{"text": "Who are you?", "next": "who"}, _end("Not today.")]},
				"who": {"text": "Someone who was here before your town had walls, and will be here after. Buy something.", "next": "hub"},
				"hub": {"text": "Well?",
					"choices": [{"text": "Show me your goods.", "next": "end", "actions": [{"open_shop": "stranger_wares"}]}, _end("Later.")]},
				"aether_offer": {"text": "The Warden is dead, and his relics have loosened their grip on the Aether. I have something for you now. It is not cheap. Nothing that changes a hero is.",
					"actions": [{"event": "stranger_aether_offer"}], "next": "hub"},
			},
		}})
