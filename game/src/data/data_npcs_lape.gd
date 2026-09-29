class_name DataNpcsLape
## bh-019: Lape the Ancient, relic appraiser of Malasugue — a very old black-hooded figure with an enormous staff who
## keeps a crooked stall of relics on the Merchant Quarter. His trade (service "lape_trade" -> LapeWindow): up to three
## items in his brass dishes, his appraisal, then one of three special-crafted, licensed pieces or the gold.

const PORTRAIT := "res://assets/ui/portraits/lape.svg"
const MODEL := "res://assets/characters/lape.glb"
const FALLBACK_MODEL := "res://assets/characters/mage.glb"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]

static func build() -> Array:
	return [_lape()]

static func _lape() -> NpcDef:
	var nodes := {
		"first": {"text": [
				"Hm? A living one. They so rarely stop.",
				"I am **Lape**. They call me the Ancient, which is rude and accurate. I appraise things. Old things, strange things, things you took from the dead and are not sure what to do with.",
				"Lay up to **three** items in my brass dishes. I will tell you what they truly are and what they are worth. Then I will offer you one of **three pieces I craft myself**, for your hands and your trade, each with a guild's license. Or my gold, if you prefer coin."],
			"next": "hub"},
		"hub": {"text": "The dishes are empty, {hero}. They do not like being empty.",
			"choices": [
				{"text": "Appraise my things.", "next": "end", "actions": [{"service": "lape_trade"}]},
				{"text": "How does your trade work?", "next": "how"},
				{"text": "What does \"licensed\" mean?", "next": "license"},
				{"text": "Who are you, really?", "next": "who"},
				{"text": "Farewell.", "next": "end"},
			]},
		"how": {"text": [
				"You put one, two or three things in the dishes. I look. I identify: sockets, crystals, runes, refits, powers, sets, seals, how well it was made. I tell you what each one is worth, to me.",
				"If the lot is worth enough, I **craft three pieces** for you to choose from: a weapon, armour, and jewellery, made for your class. The better the things you bring, the better I make: three fine pieces together are worth more than one.",
				"Take one of mine, or take the gold. Either way the things in the dishes stay with me. I pay better than the merchants; I am old, not greedy."],
			"next": "hub"},
		"license": {"text": [
				"Every piece I make carries a faction's **license**: the Order of the Dawn, the Circle of the Arcanum, the Wardens, the Hunters' Lodge, the Merchant League. A license adds its own bonus on top of everything else.",
				"I will also tell you what each piece asks of you: the level, the guild class you need to wear its tier, the strength or wit it wants. A relic you cannot wear yet is still a relic. You simply grow into it."],
			"next": "hub"},
		"who": {"text": [
				"I was here before the town. I will be here after it. In between, I trade.",
				"The staff? A gift from someone who did not need it any more. Do not touch it. It remembers them fondly and everyone else less so."],
			"actions": [{"relationship": 2}], "next": "hub"},
	}
	var spot := DataTownRows.npc_spot(&"lape")
	return NpcDef.make(&"lape", "Lape the Ancient", {"title": "Relic Appraiser", "portrait": PORTRAIT,
		"map": &"sanctuary", "position": spot.get("position", Vector3.ZERO), "yaw": spot.get("yaw", 0.0),
		"model": MODEL if ResourceLoader.exists(MODEL) else FALLBACK_MODEL, "tint": Color(0.06, 0.05, 0.07),
		"services": [&"lape_trade"], "idle_anims": IDLES,
		"graph": {"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]], "nodes": nodes}})
