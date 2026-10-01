class_name DataNpcsZarael
## bh-029: the people of Zarael (docs/LORE.md §11) — Captain Ilsa Rhondar and Agdao's ship (at Wyman's Marsh Jetty once
## Kethrax has fallen, and at Agdao's pier), Terax, Wirekeeper Halvessa Orn on the Crown of Steps, and Agdao's
## townsfolk. "Zarael", "Agdao", "Terax" and "Aljay" are the author's names; every other name is invented for Jre
## (never Filipino words, never borrowed real-culture names — user rule). Graph format: see Dialogue.
## Quest flags: DataZarael (zr_ship_sailed, zr_terax_met, zr_wirekeeper_met, zr_relays_cut, dg_*_cleared,
## boss_deathspan_defeated, boss_leash_abbot_defeated, zr_heartwire_restored).

const CHAR := "res://assets/characters/%s.glb"
const PORTRAIT := "res://assets/ui/portraits/%s.svg"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]

const C_TERAX := Color(0.95, 0.78, 0.4)

static func build() -> Array:
	return [_ilsa(&"ilsa", &"wyman_outpost", DataZarael.WY_CAPTAIN, -100.0), _ilsa(&"ilsa_agdao", &"agdao", Vector3(-17.4, 0.0, 61.0), 90.0),
		_terax(), _wirekeeper(), _dorrit(), _brisa(), _ysenne(), _toma(), _caius(), _quillan(), _sorrel()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _p(id: String, fallback: String) -> String:
	var p := PORTRAIT % id
	return p if ResourceLoader.exists(p) else PORTRAIT % fallback

## A bh-029 model if its builder delivered it, else an existing townsfolk body.
static func _m(id: String, fallback: String) -> String:
	var p := CHAR % id
	return p if ResourceLoader.exists(p) else CHAR % fallback

# ------------------------------------------------------------------------------------------------ the ship's captain
static func _ilsa(id: StringName, map: StringName, pos: Vector3, yaw: float) -> NpcDef:
	var at_wyman := map == &"wyman_outpost"
	var nodes := {
		"offer": {"text": [
				"You are the one who put Kethrax in the marsh? Then I have crossed the sea for the right face. **Ilsa Rhondar**, master of the **Sunwake**, out of **Agdao** on **Zarael**.",
				"I was sent by **Terax**, Warden of Agdao. When word came over the water that a Kharvenn-made chain had broken, Terax said: find whoever broke it, and bring them home with you.",
				"Zarael is dying, hero. Slowly, the way a lamp dies. I will not lie to you about the crossing either: the sea between is grey and the island at the end of it is worse. Will you come?"],
			"choices": [
				{"text": "Set sail for Zarael.", "next": "end", "actions": [{"set_flag": "zr_ship_sailed"}, {"service": "sail_zarael"}]},
				{"text": "What is wrong with Zarael?", "next": "why"},
				{"text": "Who is Terax?", "next": "who"},
				_end("Not yet. Wait for me."),
			]},
		"why": {"text": [
				"Our island runs on wire. Old wire, white-bright, laid in the stone by people who were dust before the Binding: the **Heartwire**. It lit our lamps and lifted our water up the terraces for a thousand years.",
				"Seven winters ago it went wrong. It still glows white, but it stutters, like a sick man's pulse, and it hums. The Kharvenn did it, Terax says, with their chains. Now the wire makes people sick, and the old guardians of the island hunt anyone they find."],
			"next": "offer_hub"},
		"who": {"text": "The Warden of Agdao. Hard as the steps of the Crown, and about as talkative. Terax will tell you the rest when we land; Terax asked me to say only this: **someone you are looking for passed through Agdao.**",
			"next": "offer_hub"},
		"offer_hub": {"text": "The tide will not wait all season. Well?",
			"choices": [
				{"text": "Set sail for Zarael.", "next": "end", "actions": [{"set_flag": "zr_ship_sailed"}, {"service": "sail_zarael"}]},
				_end("Soon."),
			]},
		"hub": {"text": "The Sunwake is ready when you are. She knows the way between Wyman and Agdao better than I do." if at_wyman else "Back to Salmonan? The Sunwake will carry you to Wyman Outpost's jetty, and bring you home again whenever you ask.",
			"choices": [
				{"text": "Sail to Agdao, on Zarael." if at_wyman else "Sail to Wyman Outpost, on Salmonan.", "next": "end", "actions": [{"service": "sail_zarael" if at_wyman else "sail_wyman"}]},
				{"text": "Tell me about the Sunwake.", "next": "ship"},
				_end("Not today."),
			]},
		"ship": {"text": "Built in Agdao from Coilwood timber, with a serpent on the stern for luck. The lanterns are Heartwire: they still burn, because Wirekeeper Orn blessed them herself before the wire turned. Steady at sea, stuttering in harbour. Do not ask me why.",
			"next": "hub"},
	}
	var entries := [[[{"not_flag": "zr_ship_sailed"}], "offer"], [[], "hub"]] if at_wyman else [[[], "hub"]]
	var d := {"title": "Master of the Sunwake", "portrait": _p("ilsa", "captain"), "map": map, "position": pos, "yaw": yaw,
		"model": _m("ilsa", "fisher"), "tint": Color(0.22, 0.32, 0.4), "idle_anims": IDLES, "graph": {"entries": entries, "nodes": nodes}}
	if at_wyman:
		d["presence"] = [{"flag": String(DataZarael.SHIP_FLAG)}]
	return NpcDef.make(id, "Captain Ilsa Rhondar", d)

# ------------------------------------------------------------------------------------------------ Terax
static func _terax() -> NpcDef:
	return NpcDef.make(&"terax", "Terax", {"title": "Warden of Agdao", "portrait": _p("terax", "captain"), "map": &"agdao",
		"position": DataZarael.AG_TERAX, "yaw": 0.0, "model": _m("terax", "officer"), "tint": Color(0.3, 0.5, 0.4), "idle_anims": [&"idle", &"idle_look"],
		"graph": {
			"entries": [
				[[{"flag": "zr_heartwire_restored"}, {"not_visited": "dawn"}], "dawn"],
				[[{"not_flag": "zr_terax_met"}], "welcome"],
				[[{"flag": "boss_leash_abbot_defeated"}, {"not_flag": "zr_heartwire_restored"}], "wake_it"],
				[[{"flag": "boss_deathspan_defeated"}, {"not_visited": "crossed"}], "crossed"],
				[[], "hub"],
			],
			"nodes": {
				# the cutscene (terax_welcome) normally plays on the pier; this is the same welcome if it was skipped
				"welcome": {"text": [
						"So the sea gave you back. Terax, Warden of Agdao. Ilsa found you; good.",
						"I will say it plainly, because plain is all I have left. **Two winters ago a man came over that same water.** Black dragon-scale. Red eyes. Broken chain links hanging from his wrists like bracelets. **Aljay.**",
						"He went down into the three Vaults with me, where no one had come back from. We cleared them. For the first time in five years people crossed the **Bridge of Death**. Then he crossed it alone, and for one season the wires burned steady and bright."],
					"actions": [{"set_flag": "zr_terax_met"}, {"give_xp": 1500}, {"relationship": 10}],
					"choices": [
						{"text": "The Accord says he was taken three winters ago.", "next": "accord"},
						{"text": "What do you need from me?", "next": "need"},
					]},
				"accord": {"text": "Then the Accord is wrong, or he walked out of his chains. I know what I saw. He did not speak of where he had been. He asked about the Bridge, and about the Kharvenn, and he did not sleep.",
					"next": "need"},
				"need": {"text": [
						"The chain-priests came back last winter under a new master: **Orvul Dram, the Leash-Abbot**. The Vaults woke again, worse than before. The Blackwire is in our streets now. Our lifts are dead. Half the terraces are dark.",
						"Climb the **Crown of Steps**. **Wirekeeper Halvessa Orn** keeps the last working conduit at the top. She can tell you what the wire is doing. I can only tell you who to hit."],
					"next": "hub"},
				"hub": {"text": "Hero.",
					"choices": [
						{"text": "Tell me about Aljay again.", "next": "aljay"},
						{"text": "What is the Heartwire?", "next": "heartwire"},
						{"text": "What is the Bridge of Death?", "next": "bridge"},
						{"text": "Tell me about the three Vaults.", "next": "vaults"},
						{"text": "Who are the Kharvenn?", "next": "kharvenn"},
						_end("I will be back."),
					]},
				"aljay": {"text": [
						"He fought like a man with nothing left to lose and something left to protect. I never asked what. In the Veinworks he held a door against things I will not describe, and laughed once, at nothing.",
						"When he came back over the Bridge he asked for a boat going **east**. Not west, toward Salmonan and home. East. Wherever he was going, it was not finished."],
					"next": "hub"},
				"heartwire": {"text": [
						"Bright wire, laid in the stone by the **Wirewrights** before anyone wrote anything down. It runs under every street in Agdao, through the Coilwood, across the Barrens, over the Bridge, to the **Dawn Engine** in the **Heart Citadel**.",
						"The Wirewrights did not build it for lamps. Halvessa will tell you it was built as a **lullaby**. The island is named for what sleeps under it. **Zarael.**"],
					"next": "hub"},
				"bridge": {"text": [
						"Three hundred paces of Wirewright stone over a gorge nobody has seen the bottom of. It is the only road to the Heart Citadel.",
						"Its **ward pylons** decide who may cross. Each one is fed by one of the three Vaults. While the Vaults are chained, the pylons flicker and spit and they burn anyone on the span. We call it the Bridge of Death because we have buried the people who tried."],
					"next": "hub"},
				"vaults": {"text": [
						"The **Jade Sepulchre** in the Coilwood, where the Wirewright kings sleep. The **Obsidian Engine** and the **Veinworks** in the Barrens: one spins the current, the other goes down into the giant itself.",
						"Kill what holds each Vault, and its pylon on the Bridge will burn steady again. That is how Aljay and I opened the Bridge. It is the only way I know."],
					"next": "hub"},
				"kharvenn": {"text": "The Dominion that leashes Gigas. They hammer chains into a giant's bones and steer it with pain. They want Zarael on a leash, walking into the Holy War. Every chain they drive into our wire is a chain in our giant.",
					"next": "hub"},
				"crossed": {"text": [
						"You crossed. Varrogh is down. ...I stood at the south gatehouse and watched the pylons go steady and white one after another. I have not cried since I was a child. I am not crying now.",
						"The **Leash-Abbot** is at the Dawn Engine. End him, and wake the Engine. Then Zarael can sleep, and so can I."],
					"actions": [{"give_xp": 4000}, {"relationship": 6}], "next": "hub"},
				"wake_it": {"text": "Orvul Dram is dead? Then why is the wire still stuttering? ...The Engine. Go back to the Heart Citadel and **wake the Dawn Engine**. The chains are off it; it only needs a hand on it.",
					"next": "hub"},
				"dawn": {"text": [
						"Look at it. Every lamp on the terraces. The lifts are running; I heard the counterweights an hour ago and did not know the sound. Steady white light, all the way up the Crown of Steps.",
						"Agdao will not forget your name, and neither will I. ...There is one more thing. When Aljay left, he gave me this to keep, and said: **give it to whoever finishes what I started here.**",
						"A link of black chain, broken. Still warm. I think he meant it for you. I think he knew someone would come."],
					"actions": [{"give_item": "quest_broken_link", "count": 1}, {"give_xp": 12000}, {"give_gold": 6000}, {"relationship": 20}],
					"choices": [
						{"text": "Where was he going?", "next": "east"},
						_end("Thank you, Terax."),
					]},
				"east": {"text": "East. Past Zarael, past where Ilsa will sail. Toward the Black Spire, if the Kharvenn are right about where they keep their prisoners. Rest first. You have earned one quiet night under steady light.",
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ the Wirekeeper
static func _wirekeeper() -> NpcDef:
	return NpcDef.make(&"wirekeeper", "Wirekeeper Halvessa Orn", {"title": "Keeper of the Heartwire", "portrait": _p("wirekeeper", "scholar"), "map": &"agdao",
		"position": Vector3(DataZarael.AG_WIREKEEPER.x, 33.8, DataZarael.AG_WIREKEEPER.z), "yaw": 0.0, "model": _m("wirekeeper", "scholar"),
		"tint": Color(0.2, 0.45, 0.45), "idle_anims": IDLES,
		"graph": {
			"entries": [
				[[{"not_flag": "zr_wirekeeper_met"}], "first"],
				[[{"flag": "zr_relays_cut"}, {"not_visited": "relays_done"}], "relays_done"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Mind the edge; the stairs are older than the town. Halvessa Orn. I keep the conduit, and the conduit keeps me. Terax sent you? Then sit, and look down at Agdao while I talk.",
						"The **Wirewrights** built Zarael's **Heartwire** for one purpose: to keep a **Gigas** asleep. The island is named after it. Zarael lies under us, and has for longer than there have been people to say its name.",
						"Other peoples swore oaths over their giants. The Wirewrights wrote a song in wire. The **Dawn Engine** in the Heart Citadel sings it, slow and bright, through every line. The lamps and the lifts are only the overflow.",
						"The Kharvenn chain-priests want the opposite song. Their chains feed **pain** down the lines: the **Blackwire**. Pain wakes a giant, and a giant in pain will follow the hand that stops it hurting. That is how they leash Gigas.",
						"Start close. Three **relay pylons** in the **Coilwood** carry the Blackwire into our terraces. The priests have chained them. **Cut the chains**, and Agdao breathes a little."],
					"actions": [{"set_flag": "zr_wirekeeper_met"}, {"give_xp": 1800}, {"relationship": 8}],
					"choices": [
						{"text": "Why do the lines make people sick?", "next": "sick"},
						_end("I will cut them."),
					]},
				"sick": {"text": "A body is wire too, in its way. Stand near the Blackwire long enough and it sings in you. First you cannot sleep, then you cannot stop humming, then the wire starts to grow. **Mother Ysenne** on the harbour cuts it out of those she can reach in time.",
					"next": "hub"},
				"relays_done": {"text": [
						"I felt it. Three lines went quiet at once. Agdao is breathing easier tonight; look, the lamps on the market terrace are steadier.",
						"Now the hard part. The Blackwire's real sources are the three **Vaults**. Each holds a lord the chain-priests have fed until it is only pain. Kill them, and their pylons on the **Bridge of Death** will burn steady again. Terax will tell you the way; Terax has walked it."],
					"actions": [{"give_xp": 3000}, {"give_gold": 1500}, {"relationship": 6}], "next": "hub"},
				"hub": {"text": "The conduit hums. What do you want to know?",
					"choices": [
						{"text": "What is the Heartwire for?", "next": "for"},
						{"text": "Tell me about the Wirewrights.", "next": "wrights"},
						{"text": "What happens if the Kharvenn win?", "next": "lose"},
						{"text": "Did you meet Aljay?", "next": "aljay"},
						_end("Thank you, Wirekeeper."),
					]},
				"for": {"text": "To sing a giant to sleep. Everything else, the lamps, the lifts, the water that runs uphill, the gates that know a friend, is what spills over from a song that loud.",
					"next": "hub"},
				"wrights": {"text": "We know their wire and their stone and nothing of their faces. They carved no portraits; only glyphs, and every glyph we have read is an instruction. **Mind the current. Mend the line. Let it sleep.** The last line is on every gate in the town.",
					"next": "hub"},
				"lose": {"text": "Then Zarael stands up. A Gigas on a Kharvenn leash, walking into the sea toward Salmonan and the Accord, with Agdao still on its back. The Holy War would not need an army after that.",
					"next": "hub"},
				"aljay": {"text": "He climbed these stairs once and stood where you are. He asked me whether wire could hold something that did not want to be held. I said yes, if it was sung to gently. He said nobody had ever sung to him. Then he went down to the Vaults.",
					"next": "hub"},
			},
		}})

# ------------------------------------------------------------------------------------------------ Agdao's townsfolk
static func _short(first: Array, hub: String, topics: Array, extra_choices: Array = []) -> Dictionary:
	var choices := extra_choices.duplicate()
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

static func _dorrit() -> NpcDef:
	return NpcDef.make(&"dorrit", "Dorrit Vask", {"title": "Obsidian Arms", "portrait": _p("agdao_vendor", "merchant"), "map": &"agdao",
		"position": Vector3(-12.0, 0.0, 22.6), "yaw": 0.0, "model": _m("agdao_vendor", "merchant"), "tint": Color(0.5, 0.2, 0.14),
		"shop": &"agdao_arms", "idle_anims": IDLES, "graph": _short(
			["Glass-edged and bronze-bound, every piece of it. Dorrit Vask. My family has armed Agdao's terrace guard for eleven generations, and now I sell to anyone who will go out and fight what the terrace guard became."],
			"Something sharp, or something to stop sharp things?",
			[["Why is it so dear?", "Because the smiths who make it work by lamplight, and the lamps make them sick. Every blade I sell cost someone a night of humming. Buy it, and use it on a chain-priest."]],
			[{"text": "Show me your arms.", "next": "end", "actions": [{"open_shop": "agdao_arms"}]}])})

static func _brisa() -> NpcDef:
	return NpcDef.make(&"brisa", "Brisa Kettle", {"title": "Remedies and Draughts", "portrait": _p("agdao_vendor", "merchant"), "map": &"agdao",
		"position": Vector3(12.0, 0.0, 22.6), "yaw": 0.0, "model": _m("agdao_vendor", "merchant"), "tint": Color(0.18, 0.4, 0.36),
		"shop": &"agdao_remedies", "idle_anims": IDLES, "graph": _short(
			["Mind the jars, the green ones bite. Brisa Kettle. Mother Ysenne cuts the wire out; I make what helps them sleep afterwards. And what helps heroes not need her at all."],
			"Draughts, salves, something for the road?",
			[["What helps against the wire?", "Nothing helps against the wire. Distance helps. Fewer hours near the lines. Stormward draught takes the edge off the shocks the wire-sick throw; drink one before the Barrens."]],
			[{"text": "Show me your remedies.", "next": "end", "actions": [{"open_shop": "agdao_remedies"}]},
			{"text": "Let me use your brewing table.", "next": "end", "actions": [{"service": "craft_alchemy"}]}])})

static func _ysenne() -> NpcDef:
	return NpcDef.make(&"ysenne", "Mother Ysenne", {"title": "Healer of the Wire-sick", "portrait": _p("agdao_elder", "elder"), "map": &"agdao",
		"position": Vector3(-46.0, 0.0, 40.2), "yaw": 10.0, "model": _m("agdao_elder", "elder"), "tint": Color(0.5, 0.4, 0.3),
		"idle_anims": IDLES, "graph": _short(
			["Sit. You are bleeding on my clean floor. I am Ysenne; the harbour calls me Mother because I have cut the wire out of half of it."],
			"Wounds, or questions?",
			[["How do you cut out wire?", "Early, with a hot knife and a song. The song is the important part; the wire listens. Late, I cannot. Late, they go up to the Barrens, and you meet them there. Be quick with them. They were somebody's."],
			["Who was Aljay to Agdao?", "A storm with a face. He brought me a child from the Veinworks, wire to the elbow, and held her down while I cut. She is fourteen now and sells fish on the quay. Ask her about him; she will tell you he hummed to her."]],
			[{"text": "Tend my wounds.", "next": "end", "actions": [{"heal": 1}]}])})

static func _toma() -> NpcDef:
	return NpcDef.make(&"toma", "Toma Kettridge", {"title": "Lift Engineer", "portrait": _p("agdao_porter", "smith"), "map": &"agdao",
		"position": Vector3(45.0, 0.0, -14.0), "yaw": 20.0, "model": _m("agdao_porter", "smith"), "tint": Color(0.42, 0.3, 0.18),
		"idle_anims": IDLES, "graph": _short(
			["Don't touch that lever, it bites. Toma Kettridge, lift engineer, which these days means: man who stands next to a lift that does not work."],
			"Need a hand, or need a lift? I can only offer one.",
			[["How do the lifts work?", "Counterweights of stone, chains of Wirewright bronze, and a coil at the top that pulls when the current tells it to. Steady current, the coil pulls smooth. Stuttering current, the coil does what it likes. Mostly it sulks."],
			["What would fix them?", "The current. Nothing else. I have taken this one apart nine times. The Wirewrights built it better than I can think. It is waiting for the steady light to come back, same as the rest of us."]])})

static func _caius() -> NpcDef:
	return NpcDef.make(&"caius", "Speaker Caius Wend", {"title": "Speaker of the Terraces", "portrait": _p("agdao_elder", "elder"), "map": &"agdao",
		"position": Vector3(-30.0, 0.0, -6.4), "yaw": 0.0, "model": _m("agdao_elder", "elder"), "tint": Color(0.36, 0.28, 0.42),
		"idle_anims": IDLES, "graph": _short(
			["Welcome to the council porch. Caius Wend, Speaker of the Terraces, which is a grand name for the man who reads the complaints. Lately they all say the same thing: the lamps."],
			"The council is in recess. It has been in recess for a year.",
			[["Tell me about Agdao.", "Five terraces up a hill to the Crown of Steps. The harbour feeds us, the Coilwood used to, the farms past the Bridge used to more. We built on the Wirewrights' terraces because they were already there and already lit."],
			["What does the council want of me?", "What everyone wants: the steady light back. And something no one says aloud: we want to know that if the light comes back, it stays. Last time it lasted a season."]])})

static func _quillan() -> NpcDef:
	return NpcDef.make(&"quillan", "Quillan Ashby", {"title": "Bridge Scout", "portrait": _p("agdao_porter", "traveler"), "map": &"zr_barrens",
		"position": Vector3(DataZarael.GB_CAMP.x + 3.5, 0.0, DataZarael.GB_CAMP.y - 2.0), "yaw": 200.0, "model": _m("agdao_porter", "traveler"),
		"tint": Color(0.3, 0.34, 0.24), "idle_anims": IDLES, "graph": _short(
			["Keep your voice down; sound carries out here and the glass answers. Quillan Ashby. I watch the Bridge of Death for Terax, from a safe distance, which is a long one."],
			"What do you need to know about the Barrens?",
			[["What is on the Bridge?", "Constructs on the span: **Span Wardens** with tower shields, **Ward Eyes** that sweep the deck with light. And **Varrogh** on the far platform, the Deathspan Colossus. While the pylons flicker, the span itself throws lightning. Do the Vaults first."],
			["Where are the Vaults?", "The **Obsidian Engine** is north-west of this camp, past the black glass. The **Veinworks** is east, where the ground is red. The Jade Sepulchre is back in the Coilwood, north-east of the old shrine road."]])})

static func _sorrel() -> NpcDef:
	return NpcDef.make(&"sorrel", "Sorrel", {"title": "Fishmonger", "portrait": _p("agdao_vendor", "fisher"), "map": &"agdao",
		"position": Vector3(14.0, 0.0, 41.0), "yaw": 0.0, "model": _m("agdao_vendor", "fisher"), "tint": Color(0.2, 0.36, 0.42),
		"idle_anims": IDLES, "graph": _short(
			["Fish? Fresh this morning. Or as fresh as anything is in Agdao. I'm Sorrel. Mother Ysenne says I talk too much. Mother Ysenne cut a wire out of my arm when I was eleven, so she can say what she likes."],
			"Fish, gossip, or both?",
			[["You knew Aljay?", "He carried me out of the Veinworks. He hummed the whole way, the same four notes, over and over. When I asked him what it was, he said it was the only song his mother knew. I hum it to the nets now."]])})
