class_name DataNpcsOlivar
## The people of Olivar (bh-007), a lake-trade town east of the Old Mill. Names are provisional (LORE §6b) and never
## Filipino words (user rule). Graph format: see Dialogue. Olivar's merchants sell advanced gear at a premium and
## restock whenever the hero clears a stage or defeats a miniboss (HeroData.clear_count, ShopDef.restock_on_clears).

const TOWN := "res://assets/characters/%s.glb"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]
const PORTRAIT := "res://assets/ui/portraits/%s.svg"

static func build() -> Array:
	return [_hollis(), _corvin(), _elsbeth(), _aldous(), _wren(), _pip()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _p(id: String, fallback: String) -> String:
	var p := PORTRAIT % id
	return p if ResourceLoader.exists(p) else PORTRAIT % fallback

# ------------------------------------------------------------------------------------------------ the reeve
static func _hollis() -> NpcDef:
	return NpcDef.make(&"hollis", "Reeve Hollis Garrow", {"title": "Reeve of Olivar", "portrait": _p("reeve", "captain"), "map": &"olivar",
		"position": Vector3(-4.5, 0, -2.0), "yaw": 160.0, "model": TOWN % "officer", "tint": Color(0.36, 0.4, 0.3), "idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"A hero on the Lake Shore Road. We have not had one of those since the washout. Hollis Garrow, reeve of **Olivar**. Welcome.",
						"We are traders, not fighters. Grain from the lake farms, timber from the north shore, steel and stones from wherever a barge can reach.",
						"Our merchants sell the good stock, and they charge for it. But they will turn their stalls inside out for anyone who brings word of a **cleared stage** or a **fallen champion**. News moves prices, here."],
					"actions": [{"relationship": 5}],
					"choices": [
						{"text": "How does the stock change?", "next": "stock"},
						{"text": "Who should I see?", "next": "people"},
						_end("I will look around."),
					]},
				"hub": {"text": "The scales are honest and the lamps are lit. What can Olivar do for you?",
					"choices": [
						{"text": "Remind me how the stock changes.", "next": "stock"},
						{"text": "Who should I see?", "next": "people"},
						{"text": "What lies beyond Olivar?", "next": "beyond"},
						_end(),
					]},
				"stock": {"text": [
						"Every merchant in Olivar restocks when a hero clears a **stage** (every camp of a place like Westreach or the Ruined Forest, in one outing) or defeats a **miniboss**, one of the named champions that hold the camps.",
						"You have brought us **{clears}** such tidings so far. Every one of them is a new stall of goods. The next is up to you."],
					"next": "hub"},
				"people": {"text": [
						"**Corvin Ashby** at the Arms Exchange sells advanced weapons and armor. **Elsbeth Crane** at Fine Settings sells rings, amulets and charms. They and the apothecary, the alchemy table, the workbench and the forge all stand along **Market Row**, south-west of the plaza. Both cost a fortune and are worth it.",
						"**Master Aldous Pell** brews at his alchemy table west of the plaza; he sells herbs and recipe scrolls too. **Wren Talbot** keeps the docks, and **Pip** keeps everyone's secrets and none of his own."],
					"next": "hub"},
				"beyond": {"text": [
						"South, the **Watch Road** runs to **Wyman Outpost**, the hero camp above Reedwater Marsh. Rest at their bonfire and you will have a place to wake if the road goes badly.",
						"North is the lake. The waypoint on our terrace will carry you home to Malasugue once you have stood on it."],
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ arms broker
static func _corvin() -> NpcDef:
	return NpcDef.make(&"corvin", "Corvin Ashby", {"title": "Arms Broker", "portrait": _p("arms_broker", "merchant"), "map": &"olivar",
		"position": DataTownRows.npc_spot(&"corvin").position, "yaw": DataTownRows.npc_spot(&"corvin").yaw, "model": TOWN % "merchant", "tint": Color(0.32, 0.18, 0.14), "shop": &"olivar_arms",
		"idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Corvin Ashby, Arms Exchange. Nothing on my racks is Common, and nothing on my racks is cheap.",
						"I buy what the barges bring and I sell it once. When you come back with news of a cleared stage or a champion's head, the racks change. Come often."],
					"choices": [{"text": "Show me the racks.", "next": "end", "actions": [{"open_shop": "olivar_arms"}]},
						{"text": "Why so expensive?", "next": "price"}, _end("Another time.")]},
				"price": {"text": "Because every piece is **Advanced** or better and forged above your weight. The enchantments run deeper than anything Brannoc keeps in stock. You pay for the barge, the risk and my smile.",
					"actions": [{"relationship": 2}], "next": "hub"},
				"hub": {"text": "Racks are full. For now.",
					"choices": [
						{"text": "Show me the racks.", "next": "end", "actions": [{"open_shop": "olivar_arms"}]},
						{"text": "Do you sell recipes?", "next": "recipes"},
						_end("Another time."),
					]},
				"recipes": {"text": "Forge recipes for **Champion's** weapons and armor, when I have them. You will need **Champion Essence** to make them: the minibosses carry it. If you ever see an **Aetherforged** recipe on my table, buy it before someone else does.",
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ jeweller
static func _elsbeth() -> NpcDef:
	return NpcDef.make(&"elsbeth", "Elsbeth Crane", {"title": "Jeweller", "portrait": _p("jeweller", "lantern_scribe"), "map": &"olivar",
		"position": DataTownRows.npc_spot(&"elsbeth").position, "yaw": DataTownRows.npc_spot(&"elsbeth").yaw, "model": TOWN % "matron", "tint": Color(0.42, 0.22, 0.5), "shop": &"olivar_jewels",
		"idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Careful, those are not for touching. Elsbeth Crane. Rings, amulets, charms: settings that hold an enchantment the way a good lamp holds a flame.",
						"My stones change when the town's luck changes. Bring Olivar good news and I will have something new under the glass."],
					"choices": [{"text": "Show me what is under the glass.", "next": "end", "actions": [{"open_shop": "olivar_jewels"}]}, _end("Later, then.")]},
				"hub": {"text": "Looking for something that sparkles, or something that saves your life? Most of mine do both.",
					"choices": [{"text": "Show me what is under the glass.", "next": "end", "actions": [{"open_shop": "olivar_jewels"}]},
						{"text": "Can I make my own?", "next": "craft"}, _end()]},
				"craft": {"text": "A **Hunter's Charm**, at any decent workbench: wolf fangs, cured leather, a little iron. For anything finer you need **Champion Essence** and my recipe for a **Champion's Trinket**. I sell it, when I have it.",
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ alchemist
static func _aldous() -> NpcDef:
	return NpcDef.make(&"aldous", "Master Aldous Pell", {"title": "Alchemist", "portrait": _p("alchemist", "keeper"), "map": &"olivar",
		"position": DataTownRows.npc_spot(&"aldous").position, "yaw": DataTownRows.npc_spot(&"aldous").yaw, "model": TOWN % "scholar", "tint": Color(0.2, 0.36, 0.26), "shop": &"olivar_alchemy",
		"idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Ah! Mind the kettle. Aldous Pell, master of this table and of very little else.",
						"Everything the monsters out there carry is an ingredient, if you know what to do with it. **Wolf fangs** for swiftness. **Orc tusks** for iron skin. **Grave dust** for salts. And herbs: **Silverleaf** by the roads, **Mirebloom** by the water, **Emberroot** where it is warm, **Brightcap** in the dark.",
						"Bring me the parts and I will lend you my table. Or buy from my shelves, if you are in a hurry."],
					"actions": [{"give_item": "silverleaf", "count": 4}, {"relationship": 4}],
					"choices": [{"text": "Let me use your table.", "next": "end", "actions": [{"service": "craft_alchemy"}]},
						{"text": "Show me your shelves.", "next": "end", "actions": [{"open_shop": "olivar_alchemy"}]}, _end("Thank you.")]},
				"hub": {"text": "The kettle is warm. Brewing or buying?",
					"choices": [
						{"text": "Let me use your table.", "next": "end", "actions": [{"service": "craft_alchemy"}]},
						{"text": "Show me your shelves.", "next": "end", "actions": [{"open_shop": "olivar_alchemy"}]},
						{"text": "How do I learn new recipes?", "next": "learn"},
						_end(),
					]},
				"learn": {"text": "**Recipe scrolls**. Read one and the method is yours for good. I sell a few, the champions of this island carry others. Nobody knows why a goblin fence carries a recipe for Sage's Infusion. I do not ask.",
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ dockmaster
static func _wren() -> NpcDef:
	return NpcDef.make(&"wren", "Wren Talbot", {"title": "Dockmaster", "portrait": _p("dockmaster", "fisher"), "map": &"olivar",
		"position": Vector3(7.5, 0, -39.5), "yaw": 200.0, "model": TOWN % "fisher", "tint": Color(0.3, 0.36, 0.42), "idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Tally's short again. Oh, a customer. Wren Talbot, dockmaster. Barges in, barges out, and a count of everything in between.",
						"**Stillwater Lake** is deeper than it looks and quieter than it should be. The north shore barges stopped running last month. Nobody will say why."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"hub": {"text": "Mind the planks, they are older than me.",
					"choices": [
						{"text": "What is on the north shore?", "next": "north"},
						{"text": "Any work?", "next": "work"},
						_end(),
					]},
				"north": {"text": "Timber camps under the **Northern Heights**. When the barges stop, it is usually weather. This time the weather was fine. When the heroes at Wyman are done with the marsh, somebody should look.",
					"next": "hub"},
				"work": {"text": "Not for a hero. But the goblins south of the mill have been fencing stolen grain through a fellow called **Snagtooth**. Stop him and every stall in Olivar will thank you with new stock.",
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ the bard (champion rumours)
static func _pip() -> NpcDef:
	return NpcDef.make(&"pip", "Pip Larkspur", {"title": "Bard, rumour-monger", "portrait": _p("bard_pip", "bard"), "map": &"olivar",
		"position": Vector3(5.0, 0, -7.2), "yaw": -150.0, "model": TOWN % "bard", "tint": Color(0.55, 0.3, 0.12), "idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"A new face! Pip Larkspur, songs for a copper, rumours for free. Well. Rumours for the pleasure of watching your face.",
						"I keep the tally of the island's **champions**: the named brutes who hold the camps. Beat one and Olivar's stalls turn over. Beat one twice and I write a verse about you."],
					"next": "rumours"},
				"hub": {"text": "Song or rumour?",
					"choices": [
						{"text": "Which champions are out there?", "next": "rumours"},
						{"text": "What is a stage clear?", "next": "stage"},
						_end("Neither, thanks."),
					]},
				"rumours": {"text": ["Here is the tally, fresh as this morning:", "{champions}",
						"A beaten champion crawls back to its camp after a while. They always do."],
					"next": "hub"},
				"stage": {"text": "Clear every camp of a place in one outing: every goblin, every wolf, every walking dead thing. That is a **stage**. You will know when it happens; the whole island seems to exhale.",
					"next": "hub"},
			},
		}})
