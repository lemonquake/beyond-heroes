class_name DataLapeLines
## bh-019: what Lape the Ancient says while he appraises (LapeTrade). Every item gets an opening look, a word on its
## kind, its tier, what he finds when he identifies it (sockets, crystals, runes, refits, powers, sets, licenses,
## quality, weight, age) and a verdict on its worth; the whole lot gets a summing-up and his offer. Lines are picked
## from the item's own seed, so the same item always draws the same remarks. Placeholders: {item} the item's name,
## {base} its kind ("Longsword"), {hero} the hero's name, {n} a number the line is about.
## `count()` is the number of distinct lines (the design asks for more than 300).

const OPEN := [
	"Hm. Let me see what you have carried so far.",
	"Closer. My eyes are older than your kingdom.",
	"Put it down gently. Things remember how they are handled.",
	"Ah. Another thing that outlived its owner.",
	"Let the lamp see it. The lamp is honest; people are not.",
	"So this is what the road gave you.",
	"I have held ten thousand of these. Let us see if this is the ten thousand and first.",
	"Turn it to the light. No, the other way. There.",
	"Mm. It smells of the road, and of something that did not survive it.",
	"Every object has a voice. Most of them only complain.",
	"I will not bite. The staff might.",
	"Hold still, {hero}. I am listening to it, not to you.",
	"Hm, hm. Someone made this with their hands, once. Let us honour that much.",
	"You carry it like it is heavy. Is it the weight, or the story?",
	"Place it in the dish. The brass knows a lie when it holds one.",
	"Ah, the smell of old iron and new ambition.",
	"Let old Lape have a look. Old Lape has time. Old Lape has nothing but time.",
	"I have seen this shape before. Not this one. Its grandmother, perhaps.",
	"Patience. The first look is for the eyes, the second for the truth.",
	"You found this, or it found you? It matters more than you think.",
	"The dust on it is younger than the dust on me. That is a start.",
	"Mm. Warm. It was used recently. Recently for me is a hundred years.",
	"Show me. And do not tell me what you think it is worth. Everyone guesses wrong.",
	"The staff is humming. It does that when something interesting comes near. Or when it is hungry.",
	"Let me put my thumb on it. Thumbs know things the eyes forget.",
	"Oh, do not look so worried. I have never cheated a hero. Not a living one.",
	"Another offering for the dishes. Good. The dishes get lonely.",
	"Quiet now. Let the thing speak for itself.",
	"Mm. Salt, blood, and a little rain. You have been busy.",
	"Every relic lies a little at first. Give it a moment to confess.",
]

## Remarks on the kind of item (ItemBaseDef.category; weapons also by feel).
const KIND := {
	&"weapon": [
		"A weapon. Of course. Heroes bring me weapons the way cats bring birds.",
		"{base}. The balance is honest. The last hand on it was not.",
		"Look at the wear on the grip. Somebody lived by this, and possibly died by it.",
		"A blade remembers every parry. This one remembers a great many.",
		"The edge has been sharpened by three different hands. None of them agreed.",
		"Good steel sings when you tap it. Listen. There. It is humming a soldier's song.",
		"Weapons are only promises. This one keeps them, mostly.",
		"A {base}. I carried one of these at the fall of a city nobody remembers now.",
		"Hm. The fuller is clean. Whoever made it did not rush.",
		"The haft is scored where fingers tightened. Fear leaves marks, you know.",
		"Hold it like that and it will outlive you. Hold it properly and you may outlive it.",
		"A killing thing, honestly made. I respect it more than most people.",
	],
	&"shield": [
		"A shield. The most honest thing a hero owns: it only ever says no.",
		"Look at these dents. Each one is a day someone went home.",
		"The boss is loose. It saved a life and paid for it.",
		"Shields are the quiet heroes. Nobody writes songs about them.",
		"Oak and iron and stubbornness. The best shields are mostly stubbornness.",
		"Hm, the paint is gone but the wood still remembers the colours.",
	],
	&"helm": [
		"A helm. Whoever wore this kept their thoughts inside it. Most of them, anyway.",
		"There is a notch above the brow. Somebody ducked, once, just in time.",
		"Iron hats are older than crowns. They are also more useful.",
		"The padding is gone, but the shape of a head is still in it. How strange.",
		"A good helm makes a coward brave and a brave fool live longer.",
		"The visor sticks. Everything sticks at my age too.",
	],
	&"armor": [
		"Body armour. A second skin for people whose first one is too soft.",
		"The straps have been re-stitched. By someone who loved the wearer, I think.",
		"Hm, the chest is scarred and the back is clean. The wearer never ran. Good.",
		"This carried a heartbeat for years. I can still feel where it sat.",
		"Armour is a conversation between the smith and every blade that comes after.",
		"Heavy on the shoulders, light on the conscience. That is the right way round.",
	],
	&"inner_garment": [
		"An undergarment. I have appraised crowns, and now this. The road humbles us all.",
		"The quilting is fine work. Nobody sees it, which is why it is honest.",
		"Worn under the steel, where the sweat and the fear live.",
		"Soft things last longer than you think. They do not try to be hard.",
		"Hm. Mended at the elbow, twice. Somebody could not bear to part with it.",
	],
	&"leggings": [
		"Leggings. Nobody writes songs about them, and nobody wins a fight without them.",
		"The knees are scuffed and the seat is shiny. Somebody knelt to pray and sat to wait. Both, a lot.",
		"Hm. Mud to the thigh on one side only. The wearer forded rivers with a limp.",
		"A good pair of leggings keeps your dignity and your blood on the inside.",
		"Every buckle re-punched a hole further out. Fed well, this one. Or bloated with courage.",
	],
	&"gloves": [
		"Gloves. Hands tell everything. Gloves tell what the hands wanted to hide.",
		"The fingertips are worn through. A climber, or a thief. Possibly both.",
		"A glove holds the shape of a hand like a memory holds a face.",
		"Hm. Blood on the knuckles, old. Somebody's, not the wearer's.",
		"Good gloves are the difference between a grip and a drop.",
	],
	&"boots": [
		"Boots. The road writes its whole story on the soles.",
		"These have walked further than most kings ever will.",
		"Mud from three different rivers. I can taste the difference. Do not ask how.",
		"The heel is worn on the outside. The wearer always leaned toward the next fight.",
		"Boots never get the glory. They carry the glory there, and wait outside.",
	],
	&"accessory": [
		"A trinket. Small things carry the heaviest secrets.",
		"Rings are circles, and circles are promises that never end. This one almost did.",
		"Hm. Warm from your skin. Jewellery gets attached, you know. Literally.",
		"The setting is old, the stone is older. Somebody married them well.",
		"An amulet sees the world from over the heart. It knows things.",
		"A charm. Half of them are nonsense and the other half are terrifying. Let us see which.",
		"Look how the gold has worn thin where a thumb turned it. A nervous owner.",
		"Small enough to swallow. People have. I have fished a few of these out of stranger places than pockets.",
	],
	&"crystal": [
		"A crystal. A storm held still. Do not drop it.",
		"Ah, a stone that remembers the deep places. I can hear it breathing.",
		"Crystals do not like to be sold. They like to be used. Keep that in mind.",
		"The light inside is moving. It always moves when I look. Shy thing.",
		"I watched the first of these come out of the ground. It screamed. This one only sulks.",
		"Hm. Cut clean. Whoever freed this knew their business.",
		"Hold it to your ear sometime. On second thought, do not.",
		"Stones are patient. I am patient. We understand each other.",
	],
	&"consumable": [
		"A draught? You bring an ancient appraiser a bottle of medicine. Charming.",
		"Consumables. Things made to be used up. Like heroes, forgive me.",
		"Hm. It is still good. Most of them go off after a century or two.",
		"The cork is honest. The label is optimistic.",
		"I will take it, but understand: I am appraising a lunch, not a relic.",
		"Scrolls and flasks. The small change of the adventuring life.",
		"Mm. Smells like somebody's grandmother's cure for everything.",
		"Keep the good ones, {hero}. You will need them more than my shelves do.",
	],
	&"material": [
		"Raw materials. Not yet a thing, only the promise of one.",
		"Leather and ore and bits of monster. Well, everything begins as bits of something.",
		"Ah, crafting stock. A smith would kiss you. I will merely nod.",
		"Hm. Good grain. Somebody will make something of this, one day.",
		"You bring me ingredients and expect a feast. Very well, I can cook.",
		"Material is honest. It has not had time to become anything else yet.",
		"Parts of a beast. It did not want to give them up. You were persuasive.",
		"Scraps weigh little and mean less. But three scraps together may mean something.",
	],
	&"other": [
		"Hm. I am not sure what this is. That is rare. I rather like it.",
		"An oddity. The shelves behind me are full of oddities, and I am the oldest of them.",
		"I will call it a curiosity and leave the rest to the scholars.",
		"This belongs in a story, not a shop. But here we both are.",
		"A strange one. It does not want to be looked at too closely.",
	],
}

## Remarks on the item's tier (BH.Rarity), four per tier.
const TIER := [
	["A beginner's piece. Everyone starts somewhere. Most people start here.", "Training gear. It taught somebody. Now it can retire.",
		"Simple. So was I, once. It did not last.", "Hm. Made for learning, not for legends."],
	["Common work. Nothing wrong with common. Most of the world is common, and it still turns.", "Plain. Plain is honest.",
		"A common piece. The smith was paid by the dozen, I think.", "Serviceable. That is a word for things nobody will miss."],
	["Basic, but with a spark. One little enchantment, like a candle in a window.", "Basic work with one good idea in it.",
		"Hm, a single rune of intent. Modest. I like modest.", "Basic. It is trying. I respect things that try."],
	["Advanced work. Two ideas in one object, and they get along. Rare in people, too.", "Advanced. The maker knew what they were about.",
		"Hm. Two enchantments, well married.", "Advanced. This has seen a proper forge, not a village hearth."],
	["Licensed. It carries a guild's mark, and the guild's pride with it.", "A licensed piece. Somebody signed their name to this and meant it.",
		"Hm. Licensed. The seal is genuine; I checked it with my teeth.", "Licensed work. Guild smiths do not hurry, and it shows."],
	["Elite. Now we are talking, {hero}.", "Elite craft. There are perhaps a dozen hands left who could make this.",
		"Hm, elite. The runes lie deep, like roots.", "Elite. I sat up a little. You saw me sit up."],
	["Master work. The smith poured a year into this and a little of their soul.", "A master's piece. Look at the perfected line. Look at it.",
		"Master-made. I have not held one of these since the old bridge fell.", "Hm, master work. Handle it with both hands, please."],
	["Mythical. Things like this are supposed to be stories.", "A mythical piece. It has a power in it that does not belong to this age.",
		"Oh. Oh, my. Mythical.", "Mythical. I will not ask what you did to get it. I will assume it was heroic."],
	["Legendary. There are songs about this. Bad songs, mostly, but songs.", "A legend, sitting on my table like a turnip. The world is absurd.",
		"Legendary. It has changed the ending of a war before. Possibly two.", "Hm. Legendary. My staff just stopped humming to listen."],
	["Aether. I have not seen Aether-touched work in four hundred years.", "This is Aether. It is not entirely in this world. Neither am I.",
		"Aether. My hands are shaking and I am not ashamed of it.", "Aether-work. Whatever you pay for this, it will not be enough."],
	["Cosmic. There is a night sky inside this metal, {hero}. Look. No, look properly.", "Cosmic work. It was forged under stars that have since moved.",
		"Hm. Cosmic. The stars on it are still turning. Slowly. Patiently.", "A Cosmic piece. I would put my lamp out, but it would light the room anyway."],
	["Divine. I took my hat off. I am not a hat person. I took it off.", "This is Divine. Somebody prayed this into the world, and somebody answered.",
		"Hm. Divine. It is warm, the way a hearth is warm when someone you love has just left the room.", "Divine work. Keep it close, and keep it clean."],
	["Eternal. It does not age. I checked. I have been checking for some time now.", "An Eternal piece. My clock stopped when you put it down.",
		"Hm. Eternal. Whoever made this is long dead, and this has not noticed.", "Eternal. It will outlast you, me, and the bridge we never rebuilt."],
	["Primordial. Older than the mountains, {hero}. Older than the word for mountain.", "This is Primordial. The world was still soft and hot when this was made.",
		"Hm. Primordial. Do not set it on the wooden table. Please. The stone one.", "Primordial. I have read about these in books that were themselves only rumours."],
]

## What he finds when he identifies it.
const FIND := {
	&"sockets_empty": [
		"There is a socket in it, empty. A mouth waiting for a stone.",
		"Open sockets. Somebody meant to finish this and never did.",
		"Hm. Hollow sockets. It is hungry for a crystal.",
		"An empty socket is a question. Most people never answer it.",
		"The sockets are clean. Nobody has set anything in them yet.",
	],
	&"sockets_filled": [
		"A crystal is set in it. I can feel it pulling at my fingers.",
		"Stones in the sockets. Well set, too. The lapidary was careful.",
		"Hm. It has crystals in it. That changes the arithmetic considerably.",
		"The set stones are singing to each other. It is a pleasant sound, for now.",
		"Crystals, properly seated. Somebody spent real money on this.",
		"I count the stones: {n}. Each one a small storm in a cage.",
	],
	&"enchant": [
		"There is a rune on the blade, burning quietly. An enchanter's work.",
		"Hm. It has been enchanted. The element is still settling into the steel.",
		"A rune of the old kind. I remember when every blade had one.",
		"The enchantment is good. Not great. Good is rarer than great, you know.",
		"It hums with an element. Keep it away from my beard.",
		"Ah, someone taught this weapon a second language. Fire, frost, or worse.",
	],
	&"foretech": [
		"A Fore-Tech refit. The new tinkering. I do not trust it, but it works.",
		"Somebody has been at this with fine files and clever screws.",
		"Hm, the mechanism is sound. Modern work. Everything is modern to me.",
		"Refitted. The balance was changed with real skill.",
		"Fore-Tech. The smiths of today are clever children. Clever, though.",
		"A mechanical refit, rank {n}. Somebody took this seriously.",
	],
	&"powers": [
		"There is a power sleeping in it. Do not wake it on my table.",
		"Hm. It carries a gift that does not come from any forge.",
		"A power is bound into it. I can see the shape of it, like a fish under ice.",
		"Something lives in this. Something useful, I think. Probably.",
		"It has a power. Old ones like this one are never quite tame.",
		"Mm. The power in it is awake and watching me. We are being polite to each other.",
	],
	&"set": [
		"Part of a set. Somewhere its brothers are waiting for it.",
		"A set piece. Alone it is good; together they are a small army.",
		"Hm. I know this set. I sold its helmet to a king once. He lost his head anyway.",
		"The set mark is here, on the inside. Incomplete things are always a little sad.",
		"One of a family. Families are expensive to reunite.",
	],
	&"unique": [
		"This one has a name of its own. Things with names have histories.",
		"A unique piece. There is only one, and you have it. Think about that.",
		"Hm. I know this name. So does a certain graveyard.",
		"Named work. It does not like being called anything else.",
		"Unique. The world made exactly one, and then lost the recipe.",
	],
	&"license": [
		"The license mark is clean. A guild stands behind this.",
		"Licensed by a faction. They take their seals seriously; so should you.",
		"Hm. The guild's stamp. They would want to know where you found it.",
		"The license gives it a little extra. Bureaucracy, for once, being useful.",
		"A guild seal. Somebody filled in a great many forms for this.",
		"Licensed. The stamp is still sharp. It has not been forged. I would know.",
	],
	&"quality_high": [
		"The quality is exceptional. The smith was having a very good day.",
		"Look at the finish. Better than it needs to be. That is how you know.",
		"Hm, fine quality. The kind that takes an extra week nobody pays for.",
		"Superb metal. Somebody chose every piece of it by hand.",
		"High quality. I am, reluctantly, impressed.",
	],
	&"quality_low": [
		"The work is rough. It will do the job and complain about it.",
		"Hurried craft. The smith had other things on their mind.",
		"Hm. A little crude. Crude things are honest, at least.",
		"Rough quality. Still, rough things survive. Look at me.",
	],
	&"many_affixes": [
		"So many enchantments on one piece. It is crowded in there.",
		"Hm, {n} enchantments. They are fighting for room and all of them are winning.",
		"Layer upon layer of runes. Somebody could not stop themselves.",
		"This is thick with magic. I can taste copper when I hold it.",
		"Many gifts in one object. Greedy, but in the good way.",
	],
	&"no_affixes": [
		"No enchantments at all. Just the thing itself. Refreshing.",
		"Plain as bread. Nothing hidden, nothing promised.",
		"Hm. Not a single rune. It must rely on being well made.",
		"Unenchanted. The world overrates magic, you know.",
		"It is exactly what it looks like. How rare.",
	],
	&"heavy": [
		"Heavy. You carried this? No wonder you walk like that.",
		"The weight of it. Strong arms made it and strong arms must carry it.",
		"Hm, heavy work. Heavy things hit hard and stay put.",
		"This weighs as much as a bad decision.",
	],
	&"light": [
		"Light as a rumour. Easy to carry, easy to lose.",
		"Hm, light. The maker worked hard to take the weight out.",
		"You barely notice it until you need it. The best things are like that.",
		"Light work. Quick hands will like this.",
	],
	&"ilvl_high": [
		"Made for deep places. Item level {n}. It has seen things.",
		"This comes from far down the road, level {n}. Further than most heroes go.",
		"Hm, high-level work. The monsters that carried this were not small.",
		"Level {n}. You have been somewhere dangerous, {hero}.",
	],
	&"ilvl_low": [
		"From the early roads. Level {n}. A souvenir of when you were small.",
		"Low-level work. Everyone keeps their first sword too long.",
		"Hm, level {n}. This comes from the gentle end of the world.",
		"Beginner's country. You have grown past this, I think.",
	],
	&"stack": [
		"{n} of them. Quantity has its own quality.",
		"A little heap. I will count them. I like counting.",
		"Hm, {n}. You were thorough. Or you could not stop picking them up.",
		"A whole stack. The scales will enjoy this.",
		"Several of the same. Like soldiers. Or sheep.",
	],
	&"named": [
		"It has been given a name. Names make things harder to throw away.",
		"Named. Somebody loved this, or feared it.",
		"Hm, a proper name. I will say it carefully.",
		"It answers to a name. I will not tell you what it calls you.",
		"A named piece. The name is older than the edge.",
	],
}

## A verdict on the single item's worth, by the gold it is worth to him (see LapeTrade.VALUE_BANDS).
const WORTH := [
	["Worth almost nothing. But almost is not nothing.", "Scraps. Honest scraps, but scraps.",
		"I would not cross a street for it. Luckily, I do not have to.", "A few coppers. Do not spend them all at once.",
		"Hm. It is worth what a beggar would pay, and he would haggle.", "Nearly worthless. Nearly. I have a soft spot for nearly."],
	["A modest thing, modestly priced.", "Worth a little. A meal, a bed, a candle.",
		"Hm, small coin. Small coin adds up.", "Not much, but not nothing.",
		"Enough for a good pair of socks. Do not underestimate socks.", "A small sum. Honest work for honest coin."],
	["A fair piece. Worth a fair price.", "Solid value. You were right to bring it.",
		"Hm. This is worth something, and I am paying attention.", "Fair worth. A merchant would underpay you for it.",
		"Respectable. Like a good neighbour.", "Worth keeping, worth trading. Both are fine answers."],
	["Good value. Now we are getting somewhere.", "Hm, this is worth a good deal. My eyebrows went up. Did you see?",
		"Valuable. You have a good eye, or good luck. Luck is also a talent.", "A real prize. Not a trinket.",
		"This is worth more than most heroes carry in a year.", "Good. Very good. Put it down slowly."],
	["Very valuable. I would lock the door, if I had a door.", "A great piece. I am doing sums I have not done in centuries.",
		"Hm. This alone could buy a small house. A small, damp house, but still.", "Great worth. Somebody will weep that they lost this.",
		"Precious. That is the correct word. I checked.", "This is the kind of thing wars are fought over. Small wars."],
	["A treasure. There is no other word.", "Priceless, almost. I will find a price anyway; it is my trade.",
		"Hm. I have seen kingdoms traded for less.", "A treasure. My staff is warm. It never gets warm.",
		"This could found a dynasty. Or end one.", "Treasure. Real treasure. I had forgotten the feeling."],
]

## Summing up the lot.
const DECLINE := [
	"This is not enough to craft with, {hero}. I will give you coin for it, nothing more.",
	"Too little for my hands to shape. Coin, then, and no hard feelings.",
	"I cannot make a relic out of pocket lint. Take the gold, or bring me something with a story.",
	"Hm. Not enough here to wake the anvil. I will pay you in coin.",
	"These will not become anything worth your arm. Gold is the honest offer.",
	"My craft needs more than this to work with. The gold is yours if you want it.",
	"Bring me better, and I will make you better. Today, only coin.",
	"The scales say coin. The scales are rarely wrong.",
]

## Before the three offers, by the tier he can make (index 0 = Licensed ... 5 = Aether).
const OFFER := [
	["For these I can make licensed work. Three pieces, guild-sealed. Choose one, or take the coin.",
		"Licensed pieces, three of them, made for someone like you. Look carefully.",
		"I have three things for you. Guild work, sealed and honest. Or the gold."],
	["Elite work, and licensed besides. Three choices. Only one goes home with you.",
		"You brought good things, so I will be generous. Elite, all three. Choose well.",
		"Three elite pieces, each with a guild's seal. Do not take all day."],
	["Master work. I have not offered master work in a long time. Three pieces, one choice.",
		"For these, master-made pieces, licensed and sealed. Take your time.",
		"Hm. You have earned master work. Here are three."],
	["Mythical. You brought me enough to wake something old. Three of them, one for you.",
		"I can make mythical pieces for this lot. Choose, and choose wisely.",
		"Three mythical pieces. Each has a power in it I have not named aloud in years."],
	["Legendary. There, I said it. Three legends, one choice.",
		"For this lot I will make legends. Each one sealed, each one yours to choose.",
		"Legendary pieces. Do not tell the other merchants. They will cry."],
	["Aether. The rarest thing I can shape. Three pieces, one choice, no second chances.",
		"Aether-work, for Aether-work. Choose carefully, {hero}. These do not come twice.",
		"Three pieces of Aether. My hands will need a century to recover."],
]

## A word after his offer about the requirements he has told you about.
const REQS := [
	"Mind what I told you about each piece: licenses, levels, what your arms can bear. I do not take things back.",
	"Read the requirements. A relic you cannot wear is a very expensive paperweight.",
	"Each piece has its conditions. I have written them out for you. You can read, I hope.",
	"Some of these you can wear today, some you will grow into. Choose with tomorrow in mind.",
	"The seals mean guild bonuses. The levels mean patience. Both are written there.",
	"Look at what each one asks of you before you look at what it gives.",
]

## After the trade.
const AFTER_ITEM := [
	"A good choice. Or at least an interesting one. Go and make it famous.",
	"It suits you. Things always suit people who earned them.",
	"Take it. Treat it well. It will know if you do not.",
	"Hm. Yes. I think it wanted to go with you.",
	"Done. The dishes are empty again. They will be hungry by tomorrow.",
	"Wear it in good health, and come back when the road gives you more.",
	"There. Now go, before I change my mind. I never change my mind, but go anyway.",
	"A fine trade. I will remember it. I remember everything, unfortunately.",
]
const AFTER_GOLD := [
	"Coin, then. Practical. I was practical once.",
	"The gold is yours. Spend it on something that keeps you alive.",
	"Hm. The safe choice. Safe choices have kept many heroes breathing.",
	"Counted and paid. Do not let the Stranger sell you a cursed teapot with it.",
	"Gold. It does not have a soul, but it does have uses.",
	"Take your coin. The relics will go on my shelves, and wait for someone braver.",
	"A sensible trade. I will think of you fondly, for a little while.",
	"There. Heavier pockets, lighter bag. The oldest bargain in the world.",
]

## When the window opens and the dishes are empty.
const IDLE := [
	"Three dishes, {hero}. Put something in each, or in one. I am not fussy.",
	"Bring me what you do not need. I will tell you what it really is.",
	"I appraise, I identify, I offer. Then you choose. That is the whole of it.",
	"Old things, new things, broken things. Put them in the brass.",
	"I was trading before the first stone of this town was laid. Show me your wares.",
	"Everything has a value. Most people are too hurried to learn it.",
	"The staff? It is older than I am. Do not touch it. It bites.",
	"Place your items, then ask me to look. I do not look for free. Well, I do. But ask nicely.",
	"You may take my offer or my gold. Nobody leaves my table with nothing.",
	"The road is full of relics nobody understands. I understand them. It is my curse.",
	"People call me ancient. Rude, but accurate.",
	"Up to three things at a time. My hands are old, and there are only two of them.",
	"I do not buy junk. I buy stories. Sometimes the stories are junk.",
	"Hm. You smell of adventure. Adventure smells like wet dog, mostly.",
	"Come, come. The lamp is lit and the scales are balanced.",
	"I make things for heroes who bring me things. It is a very old arrangement.",
]

static func pools() -> Array:
	var out := [OPEN, TIER, WORTH, DECLINE, OFFER, REQS, AFTER_ITEM, AFTER_GOLD, IDLE]
	for k in KIND:
		out.append(KIND[k])
	for k in FIND:
		out.append(FIND[k])
	return out

## Every distinct line he can say (nested lists flattened).
static func count() -> int:
	var seen := {}
	for p in pools():
		for x in p:
			if x is Array:
				for y in x:
					seen[y] = true
			else:
				seen[x] = true
	return seen.size()

static func pick(pool: Array, rng: RandomNumberGenerator) -> String:
	return String(pool[rng.randi_range(0, pool.size() - 1)]) if not pool.is_empty() else ""

static func fill(line: String, it: ItemInstance = null, hero_name := "hero", n := 0) -> String:
	var s := line.replace("{hero}", hero_name).replace("{n}", str(n))
	if it:
		s = s.replace("{item}", it.display_name()).replace("{base}", it.base.display_name)
	return s
