class_name DataNpcsTown
## The people who live and work indoors in Malasugue (docs/LORE.md §6) and the Tempo-Caller at the Shrine of the
## Fallen (§9). Each one knows their own corner of the world and nothing more; tone rules in LORE §8.
## Graph format: see Dialogue. Positions are map-local (interior rooms are centred on the origin, see interior.gd).

const PORTRAIT := "res://assets/ui/portraits/%s.svg"
const CHAR := "res://assets/characters/%s.glb"
const IDLES := [&"idle", &"idle_look", &"idle_adjust"]

static func build() -> Array:
	return [_hesta(), _fennick(), _marrow(), _venna(), _rhea(), _dax(), _oren(), _lio(), _tessaly(), _aurand(), _ilvena(), _thadric(),
		_zerin(), _veyra()]

static func _end(text := "Farewell.") -> Dictionary:
	return {"text": text, "next": "end"}

static func _npc(id: StringName, name: String, d: Dictionary) -> NpcDef:
	if not d.has("idle_anims"):
		d["idle_anims"] = IDLES
	return NpcDef.make(id, name, d)

# ================================================================================================ The Salted Marlin

static func _hesta() -> NpcDef:
	return _npc(&"hesta", "Hesta Brindle", {"title": "Innkeeper of the Salted Marlin", "portrait": PORTRAIT % "innkeeper",
		"map": &"int_tavern", "position": Vector3(4.0, 0, -4.6), "yaw": 0.0, "model": CHAR % "matron",
		"tint": Color(0.62, 0.3, 0.2), "services": [&"rest"],
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "boss_warden_defeated"}, {"not_visited": "warden"}], "warden"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Welcome to the **Salted Marlin**. Wipe your boots, the floor was scrubbed this morning and it will not be scrubbed again until the next one.",
						"I am **Hesta**. Rooms upstairs, stew on the fire, and every rumour on Salmonan comes through that door sooner or later."],
					"next": "hub"},
				"hub": {"text": "What will it be, {hero}?",
					"choices": [
						{"text": "Take a room ({rest_fee} gold).", "next": "end", "actions": [{"service": "rest"}]},
						{"text": "Any news worth hearing?", "next": "rumor"},
						{"text": "Who drinks here?", "next": "regulars"},
						{"text": "Why the Salted Marlin?", "next": "name"},
						_end("Another time, Hesta."),
					]},
				"name": {"text": "My grandfather hauled in a marlin longer than this bar. Salted half of it, sold the rest, bought the house. He told that story every night until he died, and now I tell it for him.",
					"actions": [{"relationship": 2}], "next": "hub"},
				"regulars": {"text": [
						"**Old Marrow** has had the table by the window for thirty years. **Fennick** sings for his supper by the fire. **Venna Kail** drinks alone and tips well; she wore the azure star once.",
						"Guild folk come in after their shifts. The Swordfin crowd argues, the Lantern crowd reads. I charge both the same. Almost."],
					"next": "hub"},
				"rumor": {"branch": [
					[[{"flag": "boss_warden_defeated"}], "rumor_4"],
					[[{"flag": "temple_seal_broken"}], "rumor_3"],
					[[{"flag": "catacombs_ritual_seen"}], "rumor_2"],
					[[], "rumor_1"],
				]},
				"rumor_1": {"text": "Fishers say goblins are picking over the burnt village for anything the dead left behind. And somebody saw **orc** tracks near the old watchtower. Orcs, on Salmonan. I told him to drink less.", "next": "hub"},
				"rumor_2": {"text": "A caravan from the north road brought word from **Corvessa**: shipyards working through the night, and nobody will say for whom. And the orc tracks were real. Hald's men found a camp.", "next": "hub"},
				"rumor_3": {"text": "Every lamp in this house leaned east the night the temple seal broke. Marrow swears the tide ran wrong the same hour. The **Lantern** crowd has been very quiet since. That is never good.", "next": "hub"},
				"rumor_4": {"text": "The dead stopped walking and the whole town slept. Then a ship came in from **Emberhal** with half its crew and a hold full of ash. The war the traders talk about is not a story any more.", "next": "hub"},
				"warden": {"text": "You are the one who went into the Hollow Throne and came back. Your first night is on the house. Do not argue, it is my house.",
					"actions": [{"relationship": 10}, {"give_item": "rejuvenation_elixir", "count": 1}], "next": "hub"},
			},
		}})

static func _fennick() -> NpcDef:
	return _npc(&"fennick", "Fennick Arlow", {"title": "Bard", "portrait": PORTRAIT % "bard",
		"map": &"int_tavern", "position": Vector3(-4.4, 0, 1.0), "yaw": 110.0, "model": CHAR % "bard", "tint": Color(0.75, 0.55, 0.15),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Ah, an audience that is not Marrow. Fennick Arlow, singer of old songs and a few new ones. Sit, the fire is free even if the songs are not.",
					"next": "hub"},
				"hub": {"text": "A song, a story, or a coin for the singer?",
					"choices": [
						{"text": "Sing about the Oathbound.", "next": "oathbound"},
						{"text": "What was the Binding?", "next": "binding"},
						{"text": "Do you know any songs about monsters?", "next": "monsters"},
						{"text": "Here, for the songs. (5 gold)", "next": "thanks", "conditions": [{"gold": 5}],
							"actions": [{"take_gold": 5}, {"relationship": 4}]},
						_end("Keep playing."),
					]},
				"oathbound": {"text": [
						"*They lit no lamp and asked no crown, they sang the sleeping giants down...*",
						"The **Oathbound** were the first heroes. The song says they used the Aether like a lullaby and swore to keep the great beasts sleeping. One oath for every creature, and one warden for every oath."],
					"next": "hub"},
				"binding": {"text": [
						"Before any kingdom, the **Gigas** walked, the **Tyrants** ruled the sky and the **Oros** coiled under the sea. People lived in caves and fought over them.",
						"The **Binding** put them to sleep. On Salmonan the oath was sworn at the **Forgotten Temple**, over the coil of the island's own Oros. That is the part of the song people stop singing along to."],
					"actions": [{"relationship": 2}], "next": "hub"},
				"monsters": {"text": "Plenty. Goblins who steal your boots while you wear them. Ogres who eat the boots after. Orcs who respect you right up until you lose. My favourite is about a fisherman who hooked an Oros. It is short. It ends badly.",
					"next": "hub"},
				"thanks": {"text": "A patron of the arts! For you, the next verse gets a hero in it. I will make you taller.", "next": "hub"},
			},
		}})

static func _marrow() -> NpcDef:
	return _npc(&"marrow", "Old Marrow", {"title": "Retired Fisherman", "portrait": PORTRAIT % "fisher",
		"map": &"int_tavern", "position": Vector3(-2.3, 0, 2.2), "yaw": 70.0, "model": CHAR % "fisher", "tint": Color(0.45, 0.42, 0.34),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[{"flag": "temple_seal_broken"}, {"not_visited": "again"}], "again"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Sit if you are sitting. Stand if you are standing. Do not hover. Sixty years on the water and I still cannot abide a body that hovers.",
					"next": "hub"},
				"hub": {"text": "Well?",
					"choices": [
						{"text": "Tell me about the night the tide ran backward.", "next": "tide"},
						{"text": "Where did the swordfish go?", "next": "fish"},
						{"text": "Do you believe in the Oros?", "next": "believe"},
						_end("Good evening, Marrow."),
					]},
				"tide": {"text": [
						"Three winters back, the same night the Warden fell. Clear sky, no wind. The tide came in at midnight when it should have been out, and it came in **from the land side**, like the sea was being pulled.",
						"Every fish in the cove turned and swam for open water. The bells on the old wreck off the point rang, and that wreck has been on the bottom since my grandfather's time."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"fish": {"text": "Out past the reef, deeper than they ever went. Fish know things. When the **swordfish** leave a coast, a fisher with sense leaves too. I am too old for sense.",
					"next": "hub"},
				"believe": {"text": "I believe the island breathes. Twice a day, like a sleeper. The scholars can call it what they like. I call it a reason to stay out of the deep water.",
					"next": "hub"},
				"again": {"text": "It happened again. The night your temple seal broke. The tide stood still for the length of a prayer. Whatever sleeps under us rolled over. **Do not wake it all the way.**",
					"actions": [{"relationship": 5}], "next": "hub"},
			},
		}})

static func _venna() -> NpcDef:
	return _npc(&"venna", "Venna Kail", {"title": "Retired Class A Hero", "portrait": PORTRAIT % "veteran",
		"map": &"int_tavern", "position": Vector3(-6.0, 0, -2.4), "yaw": 60.0, "model": CHAR % "officer", "tint": Color(0.28, 0.45, 0.8),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[{"tier_min": 5}, {"not_visited": "azure"}], "azure"], [[], "hub"]],
			"nodes": {
				"first": {"text": [
						"You have the waypoint's shine on you. It fades. The scars do not.",
						"Venna Kail. Class A, once. Now I sit by fires and tell young heroes things they will ignore."],
					"next": "hub"},
				"hub": {"text": "Ask, then.",
					"choices": [
						{"text": "What do the tiers really mean?", "next": "tiers"},
						{"text": "Tell me about the orc war on Emberhal.", "next": "emberhal"},
						{"text": "Any advice for a new hero?", "next": "advice"},
						{"text": "Which guild should I join?", "next": "guilds", "conditions": [{"no_guild": true}]},
						_end("Rest well, Venna."),
					]},
				"tiers": {"text": [
						"The letter on your emblem is a promise the **Accord** makes on your behalf: this one will not run. **Class E** means they let you carry a guild's licensed steel. **D** means they trust you with master work.",
						"Past **C** they want deeds, not just years: the ritual under the Catacombs, the temple seal, the Warden. Past **A**... there are maybe forty heroes in the Accord Isles with an **S**. The paper never tells you what it cost them."],
					"next": "hub"},
				"emberhal": {"text": [
						"A war-host of orcs came over the black sand under a red banner we had never seen. **Sulvane** colours, we learned later. They did not raid. They held ground, like soldiers.",
						"We broke them at the hot springs. Swordfin line in front, Lantern casters behind. Good plan. I lost half my company anyway. Orcs respect strength, and they tested ours for eleven days."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"advice": {"text": "Roll through a blow, do not trade it. Kill the one who heals first. And when something far bigger than you roars, it is not saying hello. Leave.",
					"next": "hub"},
				"guilds": {"text": "The **Swordfin Company** if you want to stand in front. The **Lantern Covenant** if you want to know why you are standing there. Both register you with the Accord, and your tier follows you if you change your mind.",
					"next": "hub"},
				"azure": {"text": "An azure star on your chest. I had that pin once. Wear it where people can see it. It helps them sleep.",
					"actions": [{"relationship": 8}], "next": "hub"},
			},
		}})

# ================================================================================================ Swordfin Hall

static func _rhea() -> NpcDef:
	return _npc(&"rhea", "Commander Rhea Talvanne", {"title": "Master of the Swordfin Company", "portrait": PORTRAIT % "swordfin_master",
		"map": &"int_swordfin", "position": Vector3(-3.2, 0, -0.55), "yaw": 0.0, "model": CHAR % "officer", "tint": Color(0.2, 0.36, 0.72),
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "boss_warden_defeated"}, {"guild": "swordfin"}, {"not_visited": "honour"}], "honour"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Commander **Rhea Talvanne**. This is the **Swordfin Company**: strike first, strike true.",
						"I am told the waypoint chose you. The waypoint does not fight wars. People do. Let us see which you are."],
					"next": "hub"},
				"hub": {"text": "Speak plainly. I am planning a war.",
					"choices": [
						{"text": "What war?", "next": "war"},
						{"text": "What do you know of the Gigas?", "next": "gigas"},
						{"text": "What is the Company's way?", "next": "way"},
						{"text": "Orcs on Salmonan?", "next": "orcs"},
						{"text": "How do I join?", "next": "join", "conditions": [{"not_guild": "swordfin"}]},
						_end("Commander."),
					]},
				"war": {"text": [
						"Three nations beyond the Accord's seas have sworn a **Pact of Wrath**. They call it a **Holy War**. They want the world back the way it was in the Age of Wrath: constant war, and only the strong left standing.",
						"Each of them has learned to drive one kind of ancient creature. We have guilds, palisades and whoever the waypoints send us. So I train whoever the waypoints send us."],
					"next": "hub"},
				"gigas": {"text": [
						"The **Kharvenn Dominion** hammers rune-chains into a sleeping **Gigas** and walks chain-priests in front of it to steer it with pain.",
						"I saw one on the horizon off Emberhal. I thought it was a hill until the hill took a step. You do not fight that. You fight the priests, and you make sure it never reaches a town."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"way": {"text": "Hold the line. Hit hard, hit first, and never leave a companion on the field. The Company thinks the Covenant talks too much. The Covenant thinks we die too young. We are both right.",
					"next": "hub"},
				"orcs": {"text": "An orc war-band sold to the **Sulvane Theocracy**, scouting Salmonan ahead of the war, with an ogre on a chain. Hald's men found their fires near the collapsed watchtower. Thin them out. Bounty pay is better through my quartermaster.",
					"next": "hub"},
				"join": {"text": "Talk to Quartermaster **Dax**. He keeps the register and he will take your fee. I will take your sweat.", "next": "hub"},
				"honour": {"text": "Morthar was a warden once. The Company does not celebrate the death of a guardian, even a broken one. But you did what the oath could not. The Company is proud to carry your name.",
					"actions": [{"relationship": 15}, {"give_gold": 200}], "next": "hub"},
			},
		}})

static func _dax() -> NpcDef:
	return _npc(&"dax", "Dax Harrowby", {"title": "Swordfin Quartermaster, Registrar", "portrait": PORTRAIT % "swordfin_quartermaster",
		"map": &"int_swordfin", "position": Vector3(3.6, 0, -2.7), "yaw": 0.0, "model": CHAR % "smith", "tint": Color(0.22, 0.35, 0.65),
		"services": [&"join_swordfin", &"promote"],
		"graph": _registrar_graph(&"swordfin", "Dax", [
				"Dax Harrowby, quartermaster of the **Swordfin Company**. I keep the register, the armory and the Commander's patience, in that order.",
				"Heroes are registered with the **Four-Island Accord** through a guild. No guild, no tier. No tier, no licensed steel. That is the law, and I like the law. It fits in a ledger."],
			"The Company's seal gives you, for every tier you hold: **+2% Physical Damage**, **+3% Impact Damage**, **+1% Knockback Resistance**. And **15% off at Brannoc's forge**, and **+10% bounty gold** from elites and bosses.",
			"Bounties are posted on the board. Right now: goblins picking the burnt village clean, an orc scout band near the watchtower, and the ogre they drag along. Elites and bosses pay extra to Company swords."),
	})

# ================================================================================================ Lantern House

static func _oren() -> NpcDef:
	return _npc(&"oren", "Archivist Oren Vale", {"title": "Master of the Lantern Covenant", "portrait": PORTRAIT % "lantern_master",
		"map": &"int_lantern", "position": Vector3(0, 0, -4.2), "yaw": 0.0, "model": CHAR % "scholar", "tint": Color(0.45, 0.28, 0.62),
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "temple_seal_broken"}, {"not_visited": "seal"}], "seal"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Come in, come in. Mind the stacks, they lean. Archivist **Oren Vale** of the **Lantern Covenant**.",
						"We keep the light between things. Mostly that means reading what the Oathbound wrote down and hoping they were not exaggerating."],
					"next": "hub"},
				"hub": {"text": "What would you like to understand?",
					"choices": [
						{"text": "What is the Binding, really?", "next": "binding"},
						{"text": "Is there truly an Oros under Salmonan?", "next": "oros"},
						{"text": "What is the Rekindling?", "next": "rekindling"},
						{"text": "What is the Aether?", "next": "aether"},
						{"text": "How do I join the Covenant?", "next": "join", "conditions": [{"not_guild": "lantern"}]},
						_end("Thank you, Archivist."),
					]},
				"binding": {"text": [
						"Not a chain. A **sleep**. The Oathbound sang the Aether into the great creatures until they dreamed instead of raged, and each oath was a promise to keep singing.",
						"When a warden breaks an oath, the song thins. Morthar broke his to hold back an Aether collapse the **Ashen Circle** caused. He saved us that night, and it hollowed him."],
					"next": "hub"},
				"oros": {"text": [
						"The oldest charts of Salmonan show a coastline that is a little wrong. It curves, as if the island were wrapped around something. The temple was built over the point where the curve closes.",
						"Yes. There is an **Oros**. We are standing on its dream."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"rekindling": {"text": [
						"The doctrine of the **Pact of Wrath**. It teaches that the Age of Accord made people soft, and that the world must be returned to the Age of Wrath so only the strong survive.",
						"The **Sulvane Theocracy** preaches it loudest. **Ysmer, the Drowned Crown**, wants our Oros awake and cannot wake it alone. It needs the seals broken from inside. Think about who has been breaking seals on this island."],
					"next": "hub"},
				"aether": {"text": "The light between things. It runs through old steel, through the waypoints and through you. It is neither good nor evil. The same light that carries you home can wake a sleeping serpent. That is why we keep it.",
					"next": "hub"},
				"join": {"text": "Scribe **Lio** keeps our register. Bring coin and patience; he checks everything twice.", "next": "hub"},
				"seal": {"text": "You broke the seal of the first oath. It had to be done to reach the Warden, and I have spent the night writing down exactly how much it cost. The song is thinner now. We must be quicker than Ysmer.",
					"actions": [{"relationship": 5}, {"give_xp": 80}], "next": "hub"},
			},
		}})

static func _lio() -> NpcDef:
	return _npc(&"lio", "Lio Sanvar", {"title": "Lantern Scribe, Registrar", "portrait": PORTRAIT % "lantern_scribe",
		"map": &"int_lantern", "position": Vector3(3.3, 0, 0.55), "yaw": 0.0, "model": CHAR % "merchant", "tint": Color(0.5, 0.32, 0.7),
		"services": [&"join_lantern", &"promote"],
		"graph": _registrar_graph(&"lantern", "Lio", [
				"Oh! A visitor. Lio Sanvar, scribe of the **Lantern Covenant**. I keep the register. Please do not touch the ink, it is older than both of us.",
				"The Covenant registers heroes with the **Four-Island Accord**. The Registry in **Aubren** on Veldmoor copies every page I send. So I write very neatly."],
			"The Covenant's seal gives you, for every tier you hold: **+2% Magic Damage**, **+2% Maximum Mana**, **+1% Status Resistance**. Also **15% off Seris's arcana**, **25% off a room at the Salted Marlin**, and potions heal **10% more**.",
			"We do not post bounties so much as questions. Why are wisps gathering near enchanted steel? Why do the tides run wrong? If you learn anything, the Archivist wants to hear it before anyone else does."),
	})

## Shared registrar conversation: join / transfer / promotion / tier explanation / perks / bounties.
static func _registrar_graph(gid: StringName, who: String, intro: Array, perks: String, bounties: String) -> Dictionary:
	var g := String(gid)
	return {
		"entries": [
			[[{"not_visited": "first"}], "first"],
			[[{"guild": g}, {"can_promote": true}], "ready"],
			[[], "hub"],
		],
		"nodes": {
			"first": {"text": intro, "next": "hub"},
			"hub": {"text": "Registration, promotion, questions. What can I do for you, {hero}?",
				"choices": [
					{"text": "Register me with the guild ({join_fee} gold).", "next": "end", "conditions": [{"no_guild": true}],
						"actions": [{"service": "join_" + g}]},
					{"text": "Transfer my registration here ({transfer_fee} gold, I keep my tier).", "next": "end",
						"conditions": [{"any_guild": true}, {"not_guild": g}], "actions": [{"service": "join_" + g}]},
					{"text": "Register my promotion to {next_tier} ({promo_fee} gold).", "next": "end",
						"conditions": [{"guild": g}, {"can_promote": true}], "actions": [{"service": "promote"}]},
					{"text": "What do I need for {next_tier}?", "next": "promo_info", "conditions": [{"guild": g}, {"can_promote": false}, {"tier_max": 7}]},
					{"text": "Explain the tiers.", "next": "tiers"},
					{"text": "What does the guild give its heroes?", "next": "perks"},
					{"text": "Any work?", "next": "bounties"},
					_end("That is all, %s." % who),
				]},
			"ready": {"text": "The register says you are ready for **{next_tier}**. The fee is **{promo_fee} gold**. Shall I write it in?",
				"choices": [
					{"text": "Write it in.", "next": "end", "actions": [{"service": "promote"}]},
					{"text": "Not yet.", "next": "hub"},
				]},
			"promo_info": {"text": "**{next_tier}** needs level **{promo_level}**, a fee of **{promo_fee} gold**, and a proven deed: {promo_deed_text}. You are registered as {tier}.",
				"next": "hub"},
			"tiers": {"text": [
					"Every hero starts **Unranked**. Registering makes you **Class E**. Then **D**, **C**, **B**, **A**, **S**, **SS**, and **SSS**, the rarest title in the Accord.",
					"Each tier needs a minimum level and a fee, and from **C** to **A** a deed the whole guild can vouch for. In return you may carry better steel: **Licensed** gear at E, **Master** at D, **Mythical** at C, **Legendary** at B, **Aether** relics at A.",
					"Every step also carries the **Accord bonus**: +2% Maximum HP and +1% Damage. The tier is yours, not the guild's. Change guilds and you keep it."],
				"next": "hub"},
			"perks": {"text": perks, "next": "hub"},
			"bounties": {"text": bounties, "next": "hub"},
		},
	}

# ================================================================================================ Homes

static func _tessaly() -> NpcDef:
	return _npc(&"tessaly", "Tessaly Grane", {"title": "Net-mender", "portrait": PORTRAIT % "netmender",
		"map": &"int_netmender", "position": Vector3(0.4, 0, -1.4), "yaw": 20.0, "model": CHAR % "matron", "tint": Color(0.2, 0.42, 0.45),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Door was open, so you walked in. Fine. Sit where there is no net. That leaves the floor. Tessaly Grane. I mend what the sea tears.",
					"next": "hub"},
				"hub": {"text": "Hands are busy, ears are free.",
					"choices": [
						{"text": "What is it like at sea these days?", "next": "sea"},
						{"text": "What are the drowned bells?", "next": "bells"},
						{"text": "Who is Ysmer?", "next": "ysmer"},
						_end("I will let you work."),
					]},
				"sea": {"text": "Empty. The swordfish left first, then the tuna, then the fishers' nerve. We row out past the reef now, and some nights the water below the boat is warm. Water should not be warm at night.",
					"next": "hub"},
				"bells": {"text": [
						"Some nights you hear bells under the water. Not church bells. Deeper. Slower.",
						"Old folk say the **drowned bells** are rung by people who went into the sea on purpose, a long way from here. My mother said never to row toward the sound. My mother was usually right."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"ysmer": {"text": [
						"Sailors from **Corvessa** talk about a kingdom called **Ysmer**, the **Drowned Crown**. A bell under a wave on deep green. They sing to the great serpents of the deep.",
						"If that is who is ringing the bells off our point, then they are singing to what is under this island. And they are patient."],
					"next": "hub"},
			},
		}})

static func _aurand() -> NpcDef:
	return _npc(&"aurand", "Aurand Quell", {"title": "Cartographer", "portrait": PORTRAIT % "cartographer",
		"map": &"int_cartographer", "position": Vector3(1.9, 0, -1.6), "yaw": -50.0, "model": CHAR % "scholar", "tint": Color(0.35, 0.3, 0.22),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Careful! That corner is the southern sea. Aurand Quell, cartographer. I map the Accord Isles, and lately I map the places other people are afraid of.",
					"next": "hub"},
				"hub": {"text": "Looking for a road, or a reason?",
					"choices": [
						{"text": "Show me the four islands.", "next": "islands"},
						{"text": "Where are the outside nations?", "next": "nations"},
						{"text": "Why is the map never finished?", "next": "unfinished"},
						_end("Thank you, Aurand."),
					]},
				"islands": {"text": [
						"**Salmonan**, here in the west: cliffs, coves, old forests, the temple. **Veldmoor** to the north, the biggest, with the Accord's Registry at **Aubren**.",
						"**Corvessa** in the east: harbours and shipyards and the richest guild houses. **Emberhal** in the south: black sand and hot springs, and closest to trouble."],
					"next": "hub"},
				"nations": {"text": [
						"Beyond the Accord's seas, and I draw them with a broad brush because nobody brings back good surveys. The **Kharvenn Dominion**, grey and iron. The **Sulvane Theocracy**, fire temples in the south-east. **Ysmer**, somewhere under the green water, if half the stories are true.",
						"All three signed the **Pact of Wrath**. Every new map I sell is to someone who wants to know how far away they are."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"unfinished": {"text": "Because hills move. That is not a joke. A survey off Emberhal drew the same ridge twice, forty paces apart. Keeper **Thadric** says a **Gigas** sleeps like a mountain until it does not. I have started drawing mountains in pencil.",
					"next": "hub"},
			},
		}})

static func _ilvena() -> NpcDef:
	return _npc(&"ilvena", "Ilvena Hald", {"title": "Captain Hald's Sister", "portrait": PORTRAIT % "widow",
		"map": &"int_widow", "position": Vector3(0.6, 0, -1.3), "yaw": 20.0, "model": CHAR % "matron", "tint": Color(0.32, 0.32, 0.36),
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"flag": "boss_warden_defeated"}, {"not_visited": "rest"}], "rest"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": "Oh. You are not the baker. Forgive me, I do not get many visitors. Ilvena. My brother keeps the south gate; you have probably met his temper.",
					"next": "hub"},
				"hub": {"text": "Would you like some tea? It is mostly hot water.",
					"choices": [
						{"text": "What happened in the first raid?", "next": "raid"},
						{"text": "Who was the soldier's token for?", "next": "token"},
						{"text": "How is your brother?", "next": "brother"},
						_end("Thank you, Ilvena."),
					]},
				"raid": {"text": [
						"The garrison was in the forest village, forty good soldiers. The dead came out of the Catacombs at night, and by morning the village was burning.",
						"The worst of it is that the soldiers did not stay dead either. The things you fight in the forest wear our garrison's colours. Somewhere out there, one of them is my husband."],
					"actions": [{"relationship": 3}], "next": "hub"},
				"token": {"text": "Edrin. Garrison bowman. They gave me his token because they never found anything else. If you see a **grave archer** who still holds the line like he was drilled to... end it quickly. Please.",
					"next": "hub"},
				"brother": {"text": "He has not slept a full night in three winters. He barred the south gate the day after the raid and swore to open it when the dead stop walking. He is stubborn. It is the family illness.",
					"next": "hub"},
				"rest": {"text": "They say the dead stopped walking. Last night I slept until the sun came in. I had forgotten what that was like. Thank you. From both of us.",
					"actions": [{"relationship": 12}, {"give_item": "health_potion", "count": 3}], "next": "hub"},
			},
		}})

static func _thadric() -> NpcDef:
	return _npc(&"thadric", "Keeper Thadric Moll", {"title": "Shrine-keeper, Bestiary Scholar", "portrait": PORTRAIT % "keeper",
		"map": &"int_keeper", "position": Vector3(0.4, 0, -1.5), "yaw": 0.0, "model": CHAR % "scholar", "tint": Color(0.6, 0.4, 0.14),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "Welcome. Speak softly near the shrine; the figures on it are sleeping, and so, we hope, are the things they stand for. Keeper Thadric Moll.",
					"next": "hub"},
				"hub": {"text": "The bestiary is open. Which page?",
					"choices": [
						{"text": "The Gigas.", "next": "gigas"},
						{"text": "The Tyrants.", "next": "tyrants"},
						{"text": "The Oros.", "next": "oros"},
						{"text": "Goblins, orcs and ogres.", "next": "common"},
						_end("Thank you, Keeper."),
					]},
				"gigas": {"text": "Giants of living stone and bone, ten to sixty metres tall. They built nothing, but ruins grow on their backs. When one stirs, the earthquakes come with a rhythm, like footsteps, and the stone is **warm** to the touch.",
					"next": "hub"},
				"tyrants": {"text": "Apex beasts, each one a species of its own: winged or armoured, and always hungry. They burn forests to drive herds. If you find **scorched circles** in a wood, or ash in the rain, you are already too close.",
					"next": "hub"},
				"oros": {"text": "Serpents of the deep that coil beneath islands and reefs. When one turns in its sleep, the tides go wrong and the fish flee the coast. Nobody alive in Malasugue has seen one awake. I intend to keep it that way.",
					"actions": [{"relationship": 2}], "next": "hub"},
				"common": {"text": [
						"**Goblins** follow strength and steal everything else; they throw fire-pots, so keep moving. **Orcs** live for the fight and respect only a strong enemy. **Ogres** are huge, slow and hungry, and hurl boulders when they cannot reach you.",
						"Orcs sometimes chain an ogre and drive it into battle. If you see chains, look for the orc holding them."],
					"next": "hub"},
			},
		}})

static func _zerin() -> NpcDef:
	return _npc(&"zerin", "Zerin Ven", {"title": "Refugee from Emberhal", "portrait": PORTRAIT % "refugee",
		"map": &"int_refugee", "position": Vector3(1.5, 0, -1.8), "yaw": 20.0, "model": CHAR % "traveler", "tint": Color(0.4, 0.34, 0.3),
		"graph": {
			"entries": [[[{"not_visited": "first"}], "first"], [[], "hub"]],
			"nodes": {
				"first": {"text": "...Sorry. I heard the door and thought... never mind. Zerin Ven. I came on the last ship out of **Emberhal**. The town was kind enough to lend me this roof.",
					"next": "hub"},
				"hub": {"text": "You want to hear about home. Everyone does, and nobody likes the answers.",
					"choices": [
						{"text": "What happened on Emberhal?", "next": "home"},
						{"text": "Who are the Sulvane?", "next": "sulvane"},
						{"text": "Did you see a Tyrant?", "next": "tyrant"},
						_end("I am sorry, Zerin."),
					]},
				"home": {"text": [
						"It started with sheep. Whole flocks gone overnight. Then scorched circles in the cane fields. Then a sound from the south, over the water, like a mountain clearing its throat.",
						"When the red ships came, the priests on board were already singing. They did not want our harbours. They wanted us to see what was coming."],
					"next": "hub"},
				"sulvane": {"text": "The **Sulvane Theocracy**. A burning tooth on red. They raise **Tyrants** from the egg in their fire temples and ride the young ones. They are the ones who declared the Holy War. The **Ashen Circle** you fight here wear their colours under the grey.",
					"actions": [{"relationship": 4}], "next": "hub"},
				"tyrant": {"text": "Its shadow. Only its shadow, over the whole harbour at once, and the heat of it on the back of my neck. I do not look up at the sky any more. I have ash in my cloak I cannot wash out.",
					"next": "hub"},
			},
		}})

# ================================================================================================ The Tempo-Caller

## Veyra Ashgrave keeps the Shrine of the Fallen and binds Tempos — spirits of warriors who died fighting monsters — to
## heroes who will lead them to their vengeance (companions: see TempoRules / LORE §9).
static func _veyra() -> NpcDef:
	return _npc(&"veyra", "Veyra Ashgrave", {"title": "Tempo-Caller", "portrait": PORTRAIT % "tempo_caller",
		"map": &"sanctuary", "position": DataTownRows.npc_spot(&"veyra").position, "yaw": DataTownRows.npc_spot(&"veyra").yaw, "model": CHAR % "elder", "tint": Color(0.3, 0.5, 0.58),
		"services": [&"tempo_hire", &"tempo_revive", &"tempo_renowned"],
		"graph": {
			"entries": [
				[[{"not_visited": "first"}], "first"],
				[[{"tempo_fallen": true}], "fallen"],
				[[], "hub"],
			],
			"nodes": {
				"first": {"text": [
						"Hush now. They are listening. Can you not feel them? Cold, like a draught from a door nobody opened.",
						"I am **Veyra Ashgrave**. I keep the **Shrine of the Fallen**. Warriors who died fighting the monsters of Jre do not always go quietly. Some come back as **Tempos**: spirits with one thing left in them, and that thing is **vengeance**.",
						"They cannot fight alone. They need a living hero to walk beside. The waypoint chose you. Perhaps they will too."],
					"actions": [{"relationship": 2}], "next": "hub"},
				"hub": {"text": "The spirits are restless tonight, {hero}.",
					"choices": [
						{"text": "Call the spirits. I want to bind a Tempo.", "next": "end", "actions": [{"service": "tempo_hire"}]},
						{"text": "Show me the renowned spirits.", "next": "renowned"},
						{"text": "One of my Tempos has fallen.", "next": "end", "conditions": [{"tempo_fallen": true}], "actions": [{"service": "tempo_revive"}]},
						{"text": "What exactly is a Tempo?", "next": "what"},
						{"text": "How do they fight?", "next": "fight"},
						{"text": "Why do they need me?", "next": "why"},
						{"text": "Will stronger spirits answer me?", "next": "grades"},
						_end("Rest easy, Veyra."),
					]},
				"what": {"text": [
						"Soldiers, hunters, cutpurses, anyone who fell to a monster's claw with a grudge still warm. The Aether holds their shape for a while. **Swordsmen** who held the line, **Archers** who kept the walls, **Thieves** who fought from the shadows. Older spirits too: **Mystics** who wove the Aether, **Wardens** who died still standing behind their shields.",
						"A Tempo's strength is borrowed. Bound to you, it takes **half of what you are**: half your might, half your endurance. As you grow, they grow. Give them steel, but no finer than one tier beneath your own; the dead cannot hold what the living have not earned."],
					"next": "hub"},
				"fight": {"text": [
						"Well. They are dead, not stupid. They guard the one who binds them, strike at whatever strikes you, and step out of the way of a big blow better than most of the living.",
						"Some carry a **mending** in them. Those will heal you before they heal themselves. When a Tempo is badly hurt it will fall back and tend itself; do not take it for cowardice.",
						"Two at a time, no more. A living heart can only carry so many ghosts."],
					"next": "hub"},
				"why": {"text": "A spirit without a living anchor thins out and drifts away before it ever finds its monster. You give them a road. They give you their blades. When one falls, bring its token to me and I will call it back, for a price. The Aether is not free, and neither am I.",
					"actions": [{"relationship": 2}], "next": "hub"},
				"grades": {"text": [
						"The dead are proud. The newly fallen will answer anyone. The old ones wait to see what you are made of.",
						"Grow, {hero}. Every few levels, or after a deed the whole island talks about, stronger **grades** of spirit answer instead: more skills in them, rarer ones, and more of your strength carried. When that happens the weaker ones fade from my shrine. The ones already bound to you stay as they are."],
					"next": "hub"},
				"renowned": {"text": [
						"Five of them. **Hollan Greywall**, who held the gate at Aubren. **Kavira Vane**, who called the storm down on her own blade. **Maudra Vell**, the Lantern Saint. **Cindrel Ashreed**, who killed a Tyrant. **Vessik Thorn**, who never gave the Ashen Circle a single name.",
						"They answer no one weaker than they were, and binding a name like that costs more gold than most heroes see in a year. But if you mean to go somewhere nobody comes back from, go with one of them."],
					"choices": [
						{"text": "Let me see them.", "next": "end", "actions": [{"service": "tempo_renowned"}]},
						{"text": "Another time.", "next": "hub"},
					]},
				"fallen": {"text": "I feel it. One of yours has gone quiet. Its token is cold in your pack. Shall I call it back?",
					"choices": [
						{"text": "Call it back.", "next": "end", "actions": [{"service": "tempo_revive"}]},
						{"text": "Something else first.", "next": "hub"},
					]},
			},
		}})
