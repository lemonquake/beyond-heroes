class_name DataNpcsSockets
## bh-018: the Socket Specialists, one in every town — Ysolde Marr (Malasugue), Anselm Cray (Olivar), Dagna Flint
## (Wyman Outpost). Each opens sockets in equipment, sets crystals, purges and crystallizes (service "socketing" ->
## SocketWindow) and sells crystals from their own shop. Names are never Filipino words (user rule).

const CHAR := "res://assets/characters/%s.glb"
const PORTRAIT := "res://assets/ui/portraits/%s.svg"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]

static func build() -> Array:
	return [_ysolde(), _anselm(), _dagna()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

## The rules every specialist can explain (same facts, their own voice in the intro lines).
static func _rules() -> Dictionary:
	return {
		"how": {"text": [
				"Every piece of gear can take sockets. How many depends on its tier: **Beginner** and **Common** one, **Basic** two, **Advanced** and **Licensed** three, **Elite** four, **Master** five, **Mythical** and **Legendary** six, and an **Aether** piece seven.",
				"I open them one at a time, and each one costs more than the last. Once a socket is open you can set a crystal in it, free of charge. A crystal gives different gifts in a **weapon**, in **armour** and in **jewellery**: hover over it and you will see all three.",
				"**Bloodrift** and **Essencerift** drink through a blade only, so they go in weapons and nowhere else."],
			"next": "hub"},
		"out": {"text": [
				"A set crystal does not come out on its own. You have two ways.",
				"**Purge**: I break the crystals out. The piece and its sockets stay, empty, but the crystals shatter. Cheap.",
				"**Crystallization**: the other way round. The piece is ground to dust and every crystal comes back to you whole. Costs a tenth of what the crystals are worth.",
				"And if you only want fewer sockets, I can close an empty one."],
			"next": "hub"},
		"find": {"text": [
				"Crystals come in four grades: **Fragment**, **Shard**, **Crystalline** and **Orbital**, the strongest. Eight kinds: **Ember**, **Aqua**, **Nova**, **Thundra**, **Vipera**, **Bloodrift**, **Essencerift**, and **Aetherift**, which is rare and strange.",
				"Every **boss** carries one, always. **Champions** (the minibosses) carry a Fragment or a Shard. Or you buy mine. I do not haggle: a Fragment is five thousand gold."],
			"next": "hub"},
	}

static func _hub(greeting: String, shop: String, extra: Array = []) -> Dictionary:
	var choices := [
		{"text": "Work on my gear (sockets and crystals).", "next": "end", "actions": [{"service": "socketing"}]},
		{"text": "Show me your crystals.", "next": "end", "actions": [{"open_shop": shop}]},
		{"text": "How do sockets work?", "next": "how"},
		{"text": "How do I get a crystal out again?", "next": "out"},
		{"text": "Where do crystals come from?", "next": "find"},
	]
	choices.append_array(extra)
	choices.append(_end())
	return {"text": greeting, "choices": choices}

static func _ysolde() -> NpcDef:
	var nodes := _rules()
	nodes["first"] = {"text": [
			"Mind the wheel, it bites. **Ysolde Marr**, lapidary. My father cut glass for the chapel windows; I cut things that are harder than glass and a great deal more dangerous.",
			"Bring me a blade or a breastplate and I will open it to take a crystal. Bring me the crystal too, or buy one of mine."],
		"next": "hub"}
	nodes["hub"] = _hub("What are we cutting today, {hero}?", "lapidary_crystals", [{"text": "Why is it so dear?", "next": "dear"}])
	nodes["dear"] = {"text": "Because a crystal is a storm, a fire or a wound held still. One slip of the wheel and it lets go. I charge for the years I have spent not slipping.",
		"actions": [{"relationship": 2}], "next": "hub"}
	var spot := DataTownRows.npc_spot(&"ysolde")
	return NpcDef.make(&"ysolde", "Ysolde Marr", {"title": "Lapidary (Socket Specialist)", "portrait": PORTRAIT % "lapidary",
		"map": &"sanctuary", "position": spot.get("position", Vector3.ZERO), "yaw": spot.get("yaw", 0.0), "model": CHAR % "matron",
		"tint": Color(0.46, 0.24, 0.12), "shop": &"lapidary_crystals", "services": [&"socketing"], "idle_anims": IDLES,
		"graph": {"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]], "nodes": nodes}})

static func _anselm() -> NpcDef:
	var nodes := _rules()
	nodes["first"] = {"text": [
			"Hm? Ah. A customer, not a gull. **Anselm Cray**, gem-cutter. Fifty-one years at the wheel and I still have all ten fingers, which in this trade is a boast.",
			"The barges bring stones from every shore of the lake. I open gear to hold them, and I set them so they stay set."],
		"next": "hub"}
	nodes["hub"] = _hub("Speak up, the wheel is loud.", "gemcutter_crystals", [{"text": "Which crystal should I choose?", "next": "choose"}])
	nodes["choose"] = {"text": [
			"Fire in the blade if you like to hit hard, **Aqua** in the armour if you like to stay alive. **Thundra** in a ring makes your hands quick. **Vipera** makes every cut fester.",
			"And **Aetherift**... if one ever finds you, keep it. It carries something no other stone does."],
		"next": "hub"}
	var spot := DataTownRows.npc_spot(&"anselm")
	return NpcDef.make(&"anselm", "Anselm Cray", {"title": "Gem-cutter (Socket Specialist)", "portrait": PORTRAIT % "gemcutter",
		"map": &"olivar", "position": spot.get("position", Vector3.ZERO), "yaw": spot.get("yaw", 0.0), "model": CHAR % "elder",
		"tint": Color(0.28, 0.18, 0.42), "shop": &"gemcutter_crystals", "services": [&"socketing"], "idle_anims": IDLES,
		"graph": {"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]], "nodes": nodes}})

static func _dagna() -> NpcDef:
	var nodes := _rules()
	nodes["first"] = {"text": [
			"Don't touch the cart. **Dagna Flint**. I dig crystals out of the marsh caves where nothing else wants to go, and I fit them to heroes who go there next.",
			"Camp prices on the work. The stones cost what they cost."],
		"next": "hub"}
	nodes["hub"] = _hub("Swords, stones, or stories?", "prospector_crystals", [{"text": "Where do you dig?", "next": "dig"}])
	nodes["dig"] = {"text": "Under Reedwater, where the old lights still hum in the rock. Champions nest there too; they swallow crystals like hens swallow grit. Kill one and look inside.",
		"next": "hub"}
	var spot := DataTownRows.npc_spot(&"dagna")
	return NpcDef.make(&"dagna", "Dagna Flint", {"title": "Crystal Prospector (Socket Specialist)", "portrait": PORTRAIT % "prospector",
		"map": &"wyman_outpost", "position": spot.get("position", Vector3.ZERO), "yaw": spot.get("yaw", 0.0), "model": CHAR % "traveler",
		"tint": Color(0.4, 0.34, 0.16), "shop": &"prospector_crystals", "services": [&"socketing"], "idle_anims": IDLES,
		"graph": {"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]], "nodes": nodes}})
