class_name DataNpcsWyman
## The people of Wyman Outpost (bh-007): the heroes of the camp (level, tier and guild shown on their plates and in the
## Hero Register), the quartermaster, the field smith and the camp healer. Names are provisional (LORE §6b) and never
## Filipino words (user rule). Graph format: see Dialogue.

const HERO := "res://assets/characters/%s.glb"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]
const PORTRAIT := "res://assets/ui/portraits/%s.svg"
const MAP := &"wyman_outpost"

static func build() -> Array:
	return [_aldric(), _gideon(), _maren(), _sabine(), _odo(), _yorick(), _tamsin(), _nell(), _hobb(), _greta(), _ottilie()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _p(id: String, fallback: String) -> String:
	var p := PORTRAIT % id
	return p if ResourceLoader.exists(p) else PORTRAIT % fallback

## A hero of the camp: [id, name, class, level, tier, guild, note, position, yaw, weapon, offhand, activity, tint, graph, pace_to]
static func _hero(id: StringName, name: String, cls: StringName, lvl: int, tier: int, guild: StringName, note: String, pos: Vector3,
		yaw: float, weapon: StringName, offhand: StringName, activity: StringName, tint: Color, graph: Dictionary, pace_to := Vector3.ZERO) -> NpcDef:
	return NpcDef.make(id, name, {"title": note, "portrait": _p("hero_" + String(id), "knight" if cls == &"knight" else "mage"), "map": MAP,
		"position": pos, "yaw": yaw, "model": HERO % cls, "tint": tint, "idle_anims": [&"idle", &"idle_look"],
		"hero_level": lvl, "hero_tier": tier, "hero_guild": guild, "hero_class": cls, "hero_note": note,
		"weapon": weapon, "offhand": offhand, "activity": activity, "pace_to": pace_to, "graph": graph})

# ------------------------------------------------------------------------------------------------ the commander
static func _aldric() -> NpcDef:
	return _hero(&"aldric", "Sir Aldric Vane", &"knight", 24, 4, &"swordfin", "Commander of the outpost", Vector3(-3.5, 0, -15.5), 10.0,
		&"runed_sword", &"warden_kite_shield", &"", Color(0.25, 0.4, 0.75), {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Stand easy. Sir Aldric Vane, Swordfin Company, Class B. I hold **Wyman Outpost** for whoever will help me hold it.",
						"Every hero who comes through signs the **Hero Register** by the lodge: name, level, tier, guild. It tells me who can take the marsh and who should take the waypoint home.",
						"The **bonfire** is yours. Rest there, and it becomes your **checkpoint**: if you fall out there, you can wake beside it instead of crawling back to wherever you dropped."],
					"actions": [{"relationship": 5}],
					"choices": [
						{"text": "Show me the register.", "next": "end", "actions": [{"service": "hero_roster"}]},
						{"text": "What is this camp for?", "next": "camp"},
						_end("Understood."),
					]},
				"hub": {"text": "Report, hero.",
					"choices": [
						{"text": "Show me the register.", "next": "end", "actions": [{"service": "hero_roster"}]},
						{"text": "What is this camp for?", "next": "camp"},
						{"text": "How do heroes climb the tiers?", "next": "tiers"},
						{"text": "What can I do here?", "next": "services"},
						_end(),
					]},
				"camp": {"text": [
						"**Reedwater Marsh** starts at our east wall. Something drowned there three winters ago and has not stopped drowning. We watch it; we have not crossed it. Not yet.",
						"Until we can, the outpost is a place to rest, to mend, to craft and to count heads. The Swordfin and the Lantern share this fire. Out here it does not matter which hall you signed at."],
					"next": "hub"},
				"tiers": {"text": [
						"Level and deeds. Your guild hall in Malasugue registers each promotion for a fee. You are **{tier}** now; next is **{next_tier}**, which asks for level {promo_level} and this deed: {promo_deed_text}.",
						"Gideon over there is Class B like me. Nell arrived last week, Class E, and has already set two tents on fire."],
					"next": "hub"},
				"services": {"text": "**Greggy** at the stall keeps supplies. **Greta** runs the field forge: she sells kit and lets you use the anvil. The **workbench** and **camp kettle** are free to anyone. **Ottilie** will see to your wounds by the fire.",
					"next": "hub"},
			},
		})

static func _short(first: Array, hub: String, topics: Array) -> Dictionary:
	var choices := []
	var nodes := {}
	for i in topics.size():
		var t: Array = topics[i]
		var key := "t%d" % i
		choices.append({"text": t[0], "next": key})
		nodes[key] = {"text": t[1], "next": "hub"}
	choices.append(_end())
	nodes["first"] = {"text": first, "next": "hub"}
	nodes["hub"] = {"text": hub, "choices": choices}
	return {"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]], "nodes": nodes}

static func _gideon() -> NpcDef:
	return _hero(&"gideon", "Gideon Rusk", &"knight", 28, 4, &"swordfin", "Veteran of three winters", Vector3(-14.0, 0, 21.4), 0.0,
		&"titan_greatsword", &"", &"spar", Color(0.45, 0.3, 0.2), _short(
			["Mind the backswing. Gideon Rusk. I was on the forest road the night the village fell. I have not stopped training since."],
			"Another round, or are you just watching?",
			[["Any advice?", "Throw them. Into trees, into walls, into each other. A goblin that hits a wall at speed does not get up. And never stand in a glowing circle: the champions like to mark the ground before they hit it."],
			["Tell me about the champions.", "**Grundle the Chained** on the watchtower hill hits like a falling house; bait his slam, then punish. **Warchief Karg** hides behind plate: bring Lightning or bring patience. Pip in Olivar keeps a tally of who is back."]]))

static func _maren() -> NpcDef:
	return _hero(&"maren", "Maren Holt", &"mage", 17, 3, &"lantern", "Marsh cartographer", Vector3(0.8, 0, 0.2), -110.0,
		&"storm_staff", &"", &"", Color(0.45, 0.3, 0.75), _short(
			["Warm your hands, the fire does not bite. Maren Holt, Lantern Covenant. I am mapping the marsh one soggy step at a time."],
			"Ink's drying. What do you need?",
			[["What have you mapped?", "The dry ground ends two hundred paces east. After that it is reeds, black water and old stone posts: a road, once. Someone built a causeway across the marsh long before Malasugue had walls."],
			["Any herbs out there?", "**Mirebloom** grows on the camp's east side, where the ground stays wet. Pick it: Greggy pays for it, and the kettle turns two into a mana draught."]]))

static func _sabine() -> NpcDef:
	return _hero(&"sabine", "Sabine Kestrel", &"mage", 19, 3, &"lantern", "Warden of the wards", Vector3(22.4, 0, 3.4), 90.0,
		&"frost_staff", &"", &"cast", Color(0.3, 0.5, 0.85), _short(
			["Quiet, please. Every ward on this wall is mine and they need tending at dusk. Sabine Kestrel, Class C."],
			"The wards hold. Mostly.",
			[["What are you warding against?", "Whatever lights those lamps out on the water. They are not lanterns. They drift toward anyone who stands still too long."],
			["Can I help?", "Get stronger. When the Register shows enough Class C heroes, Sir Aldric will send a party across. I would like it to be a party that comes back."]]))

static func _odo() -> NpcDef:
	return _hero(&"odo", "Odo Fairweather", &"knight", 12, 2, &"swordfin", "Scout captain", Vector3(8.5, 0, -26.0), 0.0,
		&"winged_spear", &"", &"pace", Color(0.3, 0.42, 0.3), _short(
			["Walking, always walking. Odo Fairweather, Class D. I run the scouts, which mostly means I run."],
			"Keep moving, it helps with the damp.",
			[["What do your scouts see?", "Goblins trading stolen grain up the Fen Road toward the fields. Wolves on the coast. And the dead on the Forest Road, which should not be walking that far from the catacombs."],
			["Stage clears?", "Clear every camp in Westreach in one go and the whole district quiets down for a while. Olivar's merchants love it: new stock every time. Something about good news and high prices."]]),
		Vector3(8.5, 0, -12.5))

static func _yorick() -> NpcDef:
	return _hero(&"yorick", "Yorick Dunmore", &"knight", 14, 3, &"lantern", "Keeper of the watchtower", Vector3(-20.0, 0, -20.0), 225.0,
		&"warden_longbow", &"", &"", Color(0.5, 0.45, 0.3), _short(
			["Up here! Yorick Dunmore. Class C, Lantern Covenant, and the only one in camp who can hit a heron at two hundred paces."],
			"Nothing moving. Yet.",
			[["What can you see from up there?", "The Watch Road north to Olivar, the Fen Road west to the fields, and the marsh. Always the marsh. On a clear night you can see Olivar's lamps across the water."]]))

static func _tamsin() -> NpcDef:
	return _hero(&"tamsin", "Tamsin Brisk", &"knight", 8, 2, &"", "Sellsword", Vector3(-10.0, 0, 23.0), 0.0,
		&"hand_axe", &"sigil_buckler", &"spar", Color(0.55, 0.25, 0.2), _short(
			["Do not tell Aldric I call it the Register of Show-offs. Tamsin Brisk. No guild. Class D anyway: the Swordfin registered me before I told them no."],
			"Coin's coin. What do you want?",
			[["Why no guild?", "Guilds take a cut. I take contracts. But the discounts are real: Swordfin members get Brannoc's forge cheaper, Lantern people sleep cheaper at the Salted Marlin. Pick one, if you like rules."],
			["Best way to make money?", "Salvage. Every sword you do not want is iron at the field forge; iron is ingots; ingots are better swords. And sell monster parts to Greggy: he pays more than anyone."]]))

static func _nell() -> NpcDef:
	return _hero(&"nell", "Nell Carrow", &"mage", 5, 1, &"", "Rookie, first week out", Vector3(-6.4, 0, 21.0), 0.0,
		&"bone_wand", &"", &"cast", Color(0.7, 0.45, 0.3), _short(
			["Oh! Sorry! I was aiming at the dummy. Nell Carrow. Class E! Well. Class E since Tuesday."],
			"I am getting better. The dummy is still standing, see?",
			[["Any tips for a newcomer?", "Rest at the bonfire before you go out. Always. The first time I fell in the fields I woke up by the mill with a headache and no idea where my tent was."],
			["What have you learned?", "Goblins drop **fire-pot resin**. Two of those and a bolt of linen make a firebomb at the workbench! I have made eleven. Aldric says I may not make a twelfth."]]))

# ------------------------------------------------------------------------------------------------ camp staff
static func _hobb() -> NpcDef:
	return NpcDef.make(&"hobb", "Greggy", {"title": "Quartermaster", "portrait": _p("quartermaster", "swordfin_quartermaster"), "map": MAP,
		"position": DataTownRows.npc_spot(&"hobb").position, "yaw": DataTownRows.npc_spot(&"hobb").yaw, "model": "res://assets/characters/merchant.glb", "tint": Color(0.4, 0.34, 0.22),
		"shop": &"wyman_supplies", "idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Greggy, quartermaster. Draughts, scrolls, bombs, ingots, leather. Fair prices: this is a camp, not Olivar.",
						"And I buy **monster parts** and **herbs** better than anyone on the island. Fangs, tusks, resin, dust. The camp runs on them."],
					"choices": [{"text": "Show me the supplies.", "next": "end", "actions": [{"open_shop": "wyman_supplies"}]}, _end("Later.")]},
				"hub": {"text": "Supplies are in. What do you need?",
					"choices": [{"text": "Show me the supplies.", "next": "end", "actions": [{"open_shop": "wyman_supplies"}]}, _end()]},
			},
		}})

static func _greta() -> NpcDef:
	return NpcDef.make(&"greta", "Greta Stonehand", {"title": "Field Smith", "portrait": _p("field_smith", "blacksmith"), "map": MAP,
		"position": DataTownRows.npc_spot(&"greta").position, "yaw": DataTownRows.npc_spot(&"greta").yaw, "model": "res://assets/characters/smith.glb", "tint": Color(0.36, 0.28, 0.22),
		"shop": &"wyman_outfitter", "idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Greta Stonehand. Brannoc taught me, and I will not tell you which of us is better. Yes you can use the anvil. No you cannot use my hammer.",
						"Bring me what you do not want and **salvage** it: iron from plate and blades, hide and linen from the light stuff, arcane dust from anything enchanted. Five iron shards make an ingot; ingots make a **Tempered Weapon** that beats most of what the dead drop."],
					"actions": [{"give_item": "iron_shard", "count": 5}, {"relationship": 4}],
					"choices": [
						{"text": "Let me use the anvil.", "next": "end", "actions": [{"service": "craft_forge"}]},
						{"text": "Show me your kit.", "next": "end", "actions": [{"open_shop": "wyman_outfitter"}]},
						_end("Thanks."),
					]},
				"hub": {"text": "Anvil's hot.",
					"choices": [
						{"text": "Let me use the anvil.", "next": "end", "actions": [{"service": "craft_forge"}]},
						{"text": "Show me your kit.", "next": "end", "actions": [{"open_shop": "wyman_outfitter"}]},
						{"text": "Let me use the workbench.", "next": "end", "actions": [{"service": "craft_workbench"}]},
						_end(),
					]},
			},
		}})

static func _ottilie() -> NpcDef:
	return NpcDef.make(&"ottilie", "Ottilie Brand", {"title": "Camp Healer", "portrait": _p("camp_healer", "mystic"), "map": MAP,
		"position": Vector3(-15.6, 0, -3.2), "yaw": 70.0, "model": "res://assets/characters/matron.glb", "tint": Color(0.7, 0.66, 0.55),
		"idle_anims": IDLES,
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"Sit, sit. Ottilie Brand. I patch heroes and brew what the kettle allows.",
						"Rest by the **bonfire** whenever you come in: it costs nothing, it mends everything, and if the marsh takes you, you will wake there. I have seen enough heroes carried back from the fields to insist."],
					"choices": [{"text": "I will rest by the fire.", "next": "end", "actions": [{"service": "camp_rest"}]},
						{"text": "Can I use the kettle?", "next": "end", "actions": [{"service": "craft_alchemy"}]}, _end("Later.")]},
				"hub": {"text": "Hurt? Tired? Both?",
					"choices": [
						{"text": "I will rest by the fire.", "next": "end", "actions": [{"service": "camp_rest"}]},
						{"text": "Can I use the kettle?", "next": "end", "actions": [{"service": "craft_alchemy"}]},
						_end(),
					]},
			},
		}})
