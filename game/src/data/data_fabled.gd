class_name DataFabled
## bh-039: the Fabled Arms — fifty-four named weapons from Legendary to Primordial, each with its own model
## (tools/blender/items/fabled_arms.py), its own signature strike (FabledProcs, a power on the weapon) and its own
## moving light while held (FabledFx.held). Divine and Primordial arms each have a signature and a held light of their
## own that no other weapon shares; the lower tiers share a pool of strikes in their own colours.
##
## Where they come from: the Legendary and Aether arms are uniques (ItemGenerator.random_special: elites, bosses, rare
## stock); the Cosmic .. Primordial arms stand in for the collection weapon of an Ascendant drop now and then
## (DataAscendant.roll_drop). The Debug console's Item Summoner lists them under "Fabled". docs/FABLED_ARMS.md.

const L := BH.Rarity.LEGENDARY
const A := BH.Rarity.AETHER
const C := BH.Rarity.COSMIC
const D := BH.Rarity.DIVINE
const E := BH.Rarity.ETERNAL
const P := BH.Rarity.PRIMORDIAL

## Per tier: level the arm is authored at, chance per hit, seconds between strikes, strength (share of the hit).
const TIER := {
	L: {"level": 35, "chance": 0.10, "cd": 1.4, "power": 0.8},
	A: {"level": 50, "chance": 0.12, "cd": 1.25, "power": 1.0},
	C: {"level": 70, "chance": 0.13, "cd": 1.1, "power": 1.2},
	D: {"level": 80, "chance": 0.15, "cd": 1.0, "power": 1.4},
	E: {"level": 90, "chance": 0.15, "cd": 1.0, "power": 1.4},
	P: {"level": 100, "chance": 0.16, "cd": 0.9, "power": 1.7},
}

const WIND := Elements.WIND
## [id, name, rarity, weapon type, element, signature, held light, colours [main, second], signature name, signature text, lore]
## Signatures: FabledProcs.KINDS. Held light: FabledFx — a surface mode, then the moving pieces.
const ROWS := [
	# ---- Legendary -------------------------------------------------------------------------------------------------
	["fa_vigil_of_the_last_oath", "Vigil of the Last Oath", L, &"sword", Elements.LIGHT, &"burst", ["sweep", "motes"],
		["ffe6a0", "fff8e0"], "Oathlight", "Hits may burst with oathlight around the target.",
		"Sworn to a keep that fell three hundred winters ago. It still keeps the watch its bearer could not."],
	["fa_gravewind_cleaver", "Gravewind Cleaver", L, &"greataxe", WIND, &"wave", ["flow", "leaves"],
		["9cf0c0", "e0fff0"], "Gravewind", "Hits may loose a howling wave of wind ahead of you.",
		"Forged on a hill of barrow-stones, where the wind never once stopped to rest."],
	["fa_hearthguard_maul", "Hearthguard Maul", L, &"club", Elements.FIRE, &"burst", ["embers_surface", "embers"],
		["ff8a30", "ffd080"], "Hearthfire", "Hits may burst into hearthfire around the target.",
		"Its head was cast from the iron of a village's last hearth. It has kept the cold out ever since."],
	["fa_thornwake", "Thornwake", L, &"spear", Elements.EARTH, &"spikes", ["verdant", "leaves"],
		["c8a060", "80c860"], "Thornwake", "Hits may raise a ring of stone thorns around the target.",
		"Cut from a thorn-oak that grew through an old battlefield. The roots remember every fallen spear."],
	["fa_widows_needle", "Widow's Needle", L, &"dagger", Elements.DARK, &"orbs", ["shadow", "smoke"],
		["a060ff", "40104a"], "Mourning", "Hits may send mourning spirits after nearby enemies.",
		"A gift from a widow to the man who wronged her. He wore it for a single night."],
	["fa_frostfang_talons", "Frostfang Talons", L, &"claw", Elements.ICE, &"spikes", ["frost", "frost"],
		["a0e0ff", "ffffff"], "Frostfang", "Hits may raise a ring of ice fangs around the target.",
		"Taken from a white wolf that hunted the high passes alone for a hundred years."],
	["fa_stormherald", "Stormherald", L, &"bow", Elements.LIGHTNING, &"chain", ["storm", "arcs"],
		["fff080", "a0c0ff"], "Herald's Call", "Hits may call lightning that leaps between enemies.",
		"Strung with a hair from a storm-giant's beard. Thunder follows its arrows like a hound."],
	["fa_ember_mandate", "Ember Mandate", L, &"staff", Elements.FIRE, &"meteor", ["molten", "embers"],
		["ff6020", "ffc060"], "Mandate of Ash", "Hits may bring a burning stone down on the target.",
		"The staff of a court sorcerer who signed decrees in fire. None were ever disobeyed."],
	["fa_tidecallers_javelin", "Tidecaller's Javelin", L, &"javelin", Elements.WATER, &"vortex", ["ripple", "drips"],
		["40a0ff", "c0f0ff"], "Undertow", "Hits may open a whirlpool that drags and slows enemies.",
		"Lost at sea three times. Each time the tide brought it back to the same fisherman's door."],
	["fa_ironvow_knuckles", "Ironvow Knuckles", L, &"knuckles", Elements.PHYSICAL, &"burst", ["runes", "motes"],
		["e0d8c8", "ffb060"], "Ironvow", "Hits may ring out in a shockwave of iron.",
		"Worn by a pit-fighter who swore never to lose. The vow is engraved on every knuckle."],
	# ---- Aether ---------------------------------------------------------------------------------------------------
	["fa_riftsong", "Riftsong", A, &"sword", Elements.LIGHTNING, &"chain", ["storm", "arcs"],
		["90d0ff", "ffffff"], "Riftsong", "Hits may sing lightning through the rift, leaping between enemies.",
		"It hums a single note when drawn. Those who hear it twice do not hear it a third time."],
	["fa_veilpiercer", "Veilpiercer", A, &"crossbow", Elements.DARK, &"wave", ["shadow", "smoke"],
		["b070ff", "301050"], "Veilpierce", "Hits may tear a line of shadow through everything ahead.",
		"Its bolts pass through the veil between the living and the dead, and something always follows them back."],
	["fa_lanternwood_wand", "Lanternwood Wand", A, &"wand", Elements.LIGHT, &"orbs", ["sweep", "stars"],
		["fff0b0", "ffd060"], "Lanternlight", "Hits may loose lantern spirits that seek out nearby enemies.",
		"Carved from the post of a lantern that guided pilgrims home through the marsh for two hundred years."],
	["fa_glasswing_axe", "Glasswing Axe", A, &"axe", WIND, &"blades", ["prism", "leaves"],
		["c0fff0", "a0d0ff"], "Glasswings", "Hits may rain blades of wind-glass around the target.",
		"Its head is so thin that light passes through it. It has never once been sharpened."],
	["fa_mournsteel", "Mournsteel", A, &"greatsword", Elements.ICE, &"spikes", ["frost", "frost"],
		["b0e8ff", "6080c0"], "Mourning Frost", "Hits may raise a ring of ice spears around the target.",
		"Quenched in the tears of a whole city on the day its king was buried."],
	["fa_wyrmbone_javelin", "Wyrmbone Javelin", A, &"javelin", Elements.FIRE, &"meteor", ["molten", "embers"],
		["ff7030", "ffe090"], "Wyrmfall", "Hits may bring a burning wyrm-stone down on the target.",
		"Carved from the rib of a young wyrm. The marrow inside it is still warm."],
	["fa_silent_canticle", "Silent Canticle", A, &"club", Elements.WATER, &"vortex", ["ripple", "motes"],
		["60c0ff", "e0f8ff"], "Silent Canticle", "Hits may open a soundless whirlpool that drags and slows enemies.",
		"A monk's mace from a drowned chapel. Underwater, the brothers say, it still rings the hours."],
	["fa_nightjar_claws", "Nightjar Claws", A, &"claw", Elements.DARK, &"orbs", ["shadow", "smoke"],
		["9050e0", "e0c0ff"], "Nightjars", "Hits may release night-birds of shadow that dive at nearby enemies.",
		"Named for the bird that sings only after dark. Its wearer hunted only after dark as well."],
	# ---- Cosmic ---------------------------------------------------------------------------------------------------
	["fa_polaris_edge", "Polaris Edge", C, &"sword", Elements.LIGHT, &"comet", ["starfield", "stars"],
		["c0d0ff", "ffffff"], "Polestar", "Hits may call a comet down on the target.",
		"Forged by a navigator-smith beneath the one star that never moves. It always points true."],
	["fa_nebula_reaper", "Nebula Reaper", C, &"greataxe", Elements.DARK, &"vortex", ["starfield", "motes"],
		["b080ff", "60e0ff"], "Nebula", "Hits may open a turning nebula that drags and slows enemies.",
		"The night sky is darker where this axe has been. Astronomers have noted the gaps."],
	["fa_meridian_lance", "Meridian Lance", C, &"spear", Elements.LIGHTNING, &"comet", ["storm", "stars"],
		["a0c8ff", "fff6a0"], "Meridian", "Hits may call a comet of lightning down on the target.",
		"Its point was set at the exact hour the sun crossed the meridian, and it remembers that light."],
	["fa_starwell", "Starwell", C, &"staff", Elements.LIGHT, &"meteor", ["starfield", "stars"],
		["9cb0ff", "fff0c0"], "Starwell", "Hits may drop a fallen star on the target.",
		"Drawn from a well so deep that, at the bottom, it is always night and full of stars."],
	["fa_huntsman_of_seven_stars", "Huntsman of Seven Stars", C, &"bow", Elements.LIGHTNING, &"blades", ["starfield", "stars"],
		["b0c0ff", "fff8b0"], "Seven Stars", "Hits may rain arrows of starlight around the target.",
		"Seven stars are set along its limbs, one for each hunter of the old constellation."],
	["fa_fists_of_the_falling_sky", "Fists of the Falling Sky", C, &"knuckles", Elements.EARTH, &"burst", ["starfield", "motes"],
		["c0a0ff", "ffd0a0"], "Skyfall", "Hits may land with the weight of the falling sky.",
		"Hammered from a star that fell on a monastery. The monks took it as an instruction."],
	["fa_moonshard", "Moonshard", C, &"dagger", Elements.ICE, &"comet", ["frost", "stars"],
		["c8e8ff", "ffffff"], "Moonfall", "Hits may call a shard of moonlight down on the target.",
		"A splinter of the moon, the stories say, chipped off when the moon was younger and closer."],
	["fa_eclipse_arbalest", "Eclipse Arbalest", C, &"crossbow", Elements.DARK, &"orbs", ["starfield", "smoke"],
		["8060ff", "ffb060"], "Eclipse", "Hits may loose eclipse-spheres that seek out nearby enemies.",
		"It was finished on the day the sun went dark at noon. It has never fired in full daylight since."],
	# ---- Divine (each signature and held light its own) ------------------------------------------------------------
	["fa_seraphs_promise", "Seraph's Promise", D, &"sword", Elements.LIGHT, &"seraph_wings", ["sweep", "wings", "feathers"],
		["fff0c0", "ffffff"], "Seraph's Wings", "Hits may unfurl a seraph's wings that sweep shut around you, striking every enemy nearby and healing you.",
		"A seraph promised a dying knight that his sword would never fall. It has never fallen, and it has never been put down."],
	["fa_benediction", "Benediction", D, &"greatsword", Elements.LIGHT, &"halo_descent", ["sweep", "halo", "motes_spiral"],
		["ffe090", "fff8e0"], "Descending Halo", "Hits may crown the target with a halo of judgement that falls and burns everything beneath it.",
		"Blessed by seven bishops in seven cathedrals, one blessing for each of the seven sins it was made to cut away."],
	["fa_dawnspear", "Dawnspear", D, &"spear", Elements.FIRE, &"sun_lance", ["sweep", "sunrays", "embers"],
		["ffb040", "fff0a0"], "Lance of Dawn", "Hits may hurl a lance of sunlight from the sky through the target, bursting into a sunrise.",
		"Its point catches the first light of every morning, wherever in the world it happens to be."],
	["fa_choirmasters_mace", "Choirmaster's Mace", D, &"club", Elements.LIGHT, &"choir_bells", ["runes", "runering", "motes"],
		["fff4b0", "ffd8f0"], "Choir of Bells", "Hits may ring three rings of holy sound that stun every enemy they reach.",
		"Every flange is tuned to a note of the cathedral hymn. Struck together, they sing the whole of it."],
	["fa_final_verdict", "Final Verdict", D, &"greataxe", Elements.LIGHT, &"sword_rain", ["sweep", "swords"],
		["ffe8a0", "d0e0ff"], "Verdict of Swords", "Hits may bring a ring of holy swords down around the target.",
		"The axe of the last high judge. It has passed one sentence a thousand times, and never once an acquittal."],
	["fa_featherfall", "Featherfall", D, &"bow", WIND, &"feather_storm", ["prism", "feathers", "motes_spiral"],
		["f0ffe8", "ffe8b0"], "Storm of Feathers", "Hits may raise a spiralling storm of golden feathers that cuts enemies and heals you.",
		"Strung by an angel with a single feather from her own wing. She was never seen to fly again."],
	["fa_herald_of_morning", "Herald of Morning", D, &"staff", Elements.LIGHT, &"dawn_pillar", ["sweep", "sunrays", "halo"],
		["ffd060", "fff8d8"], "Dawn Pillar", "Hits may raise a rising sun beneath the target that blooms into a pillar of light.",
		"The staff that wakes the sun. Its bearer must never sleep past dawn, or the morning will be late."],
	["fa_sanctum", "Sanctum", D, &"wand", Elements.LIGHT, &"sanctuary", ["runes", "hexsigil", "motes"],
		["fff0a0", "a0e0ff"], "Sanctuary", "Hits may lay a sanctuary on the ground that burns enemies inside it and heals you while it lasts.",
		"A wand of white ash cut from the tree beside the first altar. Where it points, the ground is holy."],
	["fa_auroras_reach", "Aurora's Reach", D, &"javelin", Elements.WATER, &"aurora_veil", ["prism", "aurora"],
		["70ffd0", "c080ff"], "Aurora Veil", "Hits may sweep a curtain of aurora forward through every enemy before you.",
		"Thrown once into the northern sky by a giant. It came down three winters later, trailing the lights behind it."],
	["fa_penance", "Penance", D, &"knuckles", Elements.LIGHT, &"starlit_scales", ["sweep", "scales", "motes"],
		["ffe080", "ffffff"], "Scales of Penance", "Hits may weigh the target on golden scales: the more it is wounded, the harder the light that strikes it.",
		"Worn by a penitent who boxed in the temple yard for a hundred days. On the last day the scales balanced."],
	# ---- Eternal --------------------------------------------------------------------------------------------------
	["fa_last_hour", "The Last Hour", E, &"sword", Elements.WATER, &"echo", ["ripple", "clock"],
		["ff90c8", "90ffe8"], "Last Hour", "Hits may echo through time and strike the target again.",
		"Every clock in the city stopped when this was forged. They all stopped at the same hour."],
	["fa_aeons_patience", "Aeon's Patience", E, &"greatsword", Elements.ICE, &"echo", ["ripple", "clock"],
		["ffb0d8", "b0f0ff"], "Patience", "Hits may echo through time and strike the target again.",
		"It took a thousand years to forge, one hammer-stroke each winter. The smith waited for every one."],
	["fa_evermoon", "Evermoon", E, &"spear", Elements.ICE, &"spikes", ["ripple", "stars"],
		["e0c0ff", "a0fff0"], "Evermoon", "Hits may raise a ring of moonlit ice around the target.",
		"The moon on its blade never wanes. On moonless nights it is the only moon there is."],
	["fa_stillwater_bow", "Stillwater", E, &"bow", Elements.WATER, &"vortex", ["ripple", "drips"],
		["ff98d0", "80ffe0"], "Stillwater", "Hits may still the water around the target into a whirlpool that drags and slows.",
		"Made by a hermit who sat beside one pond for forty years and never once saw it ripple."],
	["fa_talons_of_the_long_dusk", "Talons of the Long Dusk", E, &"claw", Elements.DARK, &"echo", ["ripple", "clock"],
		["e080ff", "80f0ff"], "Long Dusk", "Hits may echo through time and strike the target again.",
		"Forged at dusk in a land where dusk lasted a century. The light has not finished fading from them."],
	["fa_unwritten_chronicle", "The Unwritten Chronicle", E, &"staff", Elements.LIGHT, &"orbs", ["ripple", "runering"],
		["ffc0e0", "c0fff0"], "Unwritten Pages", "Hits may loose pages of light that seek out nearby enemies.",
		"Its head is a book whose pages fill themselves with what has not happened yet."],
	["fa_everember", "Everember", E, &"axe", Elements.FIRE, &"burst", ["ripple", "embers"],
		["ff90b0", "ffd090"], "Everember", "Hits may burst with a flame that will not go out.",
		"An ember from the first fire was set in its haft. It has not gone out, and it never will."],
	["fa_sandglass_arbalest", "Sandglass Arbalest", E, &"crossbow", Elements.EARTH, &"echo", ["ripple", "clock"],
		["ffc0a0", "a0ffe0"], "Sandglass", "Hits may echo through time and strike the target again.",
		"Its stock holds an hourglass that runs neither up nor down. Its bolts arrive a moment twice."],
	# ---- Primordial (each signature and held light its own) --------------------------------------------------------
	["fa_sunderer_of_ages", "Sunderer of Ages", P, &"greatsword", Elements.EARTH, &"magma_fissure", ["molten", "rocks", "embers"],
		["ff5010", "601008"], "Fissure of Ages", "Hits may split the ground from you to the target, and magma erupts along the crack.",
		"Older than the mountains it cut. The valleys of the south are the marks it left while the world was still soft."],
	["fa_coil_of_the_first_serpent", "Coil of the First Serpent", P, &"spear", Elements.FIRE, &"world_serpent", ["molten", "serpent", "embers"],
		["ff7020", "ffd040"], "The First Serpent", "Hits may raise a serpent of fire that coils up around the target and bursts.",
		"The first serpent wound itself around the world to keep it warm. This spear is one of its fangs."],
	["fa_titans_knuckle", "Titan's Knuckle", P, &"knuckles", Elements.EARTH, &"titan_fist", ["molten", "rocks"],
		["e08040", "504030"], "Titan's Fist", "Hits may raise a titan's stone fist from the ground beneath the target, hurling it upward.",
		"Broken from the hand of a titan who held up the sky. The sky has sagged a little since."],
	["fa_elderroot", "Elderroot", P, &"staff", Elements.EARTH, &"primeval_roots", ["verdant", "leaves", "seed"],
		["80e060", "d0a050"], "Primeval Roots", "Hits may wake thorned roots around the target that bind and tear every enemy they catch.",
		"A living root of the first tree. Leaves still grow on it in spring, wherever in the world its bearer stands."],
	["fa_skyfall", "Skyfall", P, &"bow", Elements.FIRE, &"meteor_swarm", ["molten", "drips", "smoke"],
		["ff6010", "ffb040"], "Skyfall", "Hits may call a swarm of meteors down on the target and everything around it.",
		"Strung with a molten thread pulled from a falling star. Where its arrows go, the sky follows."],
	["fa_maw_of_the_deep", "Maw of the Deep", P, &"greataxe", Elements.WATER, &"tidal_maw", ["ripple", "serpent", "drips"],
		["2080ff", "80fff0"], "Tidal Maw", "Hits may raise a wall of the deep sea that crashes down on the target, hurling enemies away.",
		"Hauled from the bottom of the oldest sea, where it lay in the jaws of something that is still down there."],
	["fa_obsidian_heart", "Obsidian Heart", P, &"dagger", Elements.DARK, &"obsidian_shards", ["shadow", "shards", "embers"],
		["c040ff", "ff5020"], "Obsidian Burst", "Hits may burst into a ring of obsidian spears that tear outward from the target.",
		"Chipped from the black glass at the heart of the first volcano. It is still warm, and it still beats."],
	["fa_cinder_tempest", "Cinder Tempest", P, &"axe", Elements.FIRE, &"ashen_tempest", ["molten", "vortex", "smoke"],
		["ff8030", "404040"], "Ashen Tempest", "Hits may raise a tornado of cinders that wanders through enemies, burning them.",
		"Forged in the ash-storm that buried the first city. The storm has not stopped; it lives in the axe."],
	["fa_wyrmfathers_claws", "Wyrmfather's Claws", P, &"claw", Elements.FIRE, &"dragon_breath", ["molten", "flames"],
		["ff4010", "ffd060"], "Wyrmfather's Breath", "Hits may breathe a cone of dragonfire from you through the target.",
		"Torn from the father of all dragons. Fire still answers them, as it answered him."],
	["fa_genesis", "Genesis", P, &"wand", Elements.FIRE, &"genesis_bloom", ["molten", "flower", "embers"],
		["ff6030", "ffe080"], "Genesis Bloom", "Hits may open a flower of molten rock beneath the target that bursts outward and heals you.",
		"The first flower grew from the first fire. It burned, and it bloomed, and it has never stopped doing either."],
]

## Attack rate by weapon type (each arm gets a small offset of its own).
const APS := {&"sword": 1.46, &"greatsword": 0.96, &"spear": 1.21, &"axe": 1.26, &"greataxe": 0.91, &"club": 1.11, &"staff": 1.01,
	&"wand": 1.61, &"bow": 1.11, &"crossbow": 0.83, &"dagger": 2.02, &"claw": 1.81, &"knuckles": 1.92, &"javelin": 1.16}
const ATTR := {&"knight": &"str", &"mage": &"int", &"ranger": &"dex", &"shadowblade": &"dex"}

static var _rows := {}

static func row(id: StringName) -> Array:
	if _rows.is_empty():
		for r in ROWS:
			_rows[StringName(r[0])] = r
	return _rows.get(id, [])

static func is_fabled(base: ItemBaseDef) -> bool:
	return base != null and String(base.id).begins_with("fa_") and not row(base.id).is_empty()

static func ids() -> Array:
	return ROWS.map(func(r): return StringName(r[0]))

static func ids_of(rarity: int) -> Array:
	return ROWS.filter(func(r): return int(r[2]) == rarity).map(func(r): return StringName(r[0]))

static func sig_power_id(id: StringName) -> StringName:
	return StringName("%s_sig" % id)

static func colors(id: StringName) -> Array:
	var r := row(id)
	if r.is_empty():
		return [Color.WHITE, Color.WHITE]
	return [Color.html(String(r[7][0])), Color.html(String(r[7][1]))]

static func bases() -> Array:
	var out := []
	for i in ROWS.size():
		var r: Array = ROWS[i]
		var rarity: int = r[2]
		var t: Dictionary = TIER[rarity]
		var lvl := int(t.level)
		var wt: StringName = r[3]
		var cls := DataItems._weapon_class(wt)
		var b := DataItems._b(StringName(r[0]), DB_NAMES.get(wt, String(wt).capitalize()), &"weapon", "", {
			"unique_name": r[1], "fixed_rarity": rarity, "weapon_type": wt, "class_hint": cls, "level_req": lvl, "drop_level": lvl,
			"requirements": {ATTR[cls]: int(lvl * 0.85)}, "value": 900 + 700 * (rarity - L), "drop_weight": 0, "tier": 3,
			"boss_exclusive": rarity >= C, "fixed_powers": [sig_power_id(StringName(r[0]))], "lore": r[10]})
		b.attacks_per_second = float(APS.get(wt, 1.2)) + 0.01 * float(i % 5)
		var dmg := DataItems.roster_damage(wt, lvl, b.attacks_per_second)
		b.damage_min = dmg.x * 1.08
		b.damage_max = dmg.y * 1.08
		b.element = int(r[4])
		b.element_share = 1.0 if cls == &"mage" else (0.0 if int(r[4]) == Elements.PHYSICAL else 0.4)
		var step := float(rarity - L)
		match cls:
			&"mage": b.implicit = [StatModifier.inc(&"magic_damage", 0.18 + 0.04 * step)]
			&"ranger": b.implicit = [StatModifier.inc(&"projectile_damage", 0.10 + 0.03 * step)] if wt != &"javelin" else [StatModifier.flat(&"crit_chance", 0.03 + 0.01 * step)]
			_: b.implicit = [StatModifier.flat(&"crit_chance", 0.03 + 0.01 * step)]
		if rarity >= C:
			# the Ascendant tiers' signature power too: a Fabled arm counts as one piece of its tier
			b.fixed_powers.append(DataAscendant.TIER[rarity].power)
		b.model = ItemBaseDef.ITEM_MODEL % b.id
		b.icon = DataItems.ICON3D % b.id
		b.weight = DataItems.default_weight(b) + 0.05 + 0.02 * float(i % 7)
		out.append(b)
	return out

const DB_NAMES := {&"greatsword": "Greatsword", &"greataxe": "Great Axe", &"club": "Mace", &"knuckles": "Knuckles", &"claw": "Claws"}

## One power per arm: its signature strike (FabledProcs reads the weapon, the flag only marks it). Never rolled.
static func powers() -> Array:
	var out := []
	for r in ROWS:
		var t: Dictionary = TIER[int(r[2])]
		var desc := "%s %d%% chance, at most once every %.1f s; %d%% of the hit as %s." % [String(r[9]), roundi(float(t.chance) * 100.0),
			float(t.cd), roundi(float(t.power) * 100.0 * FabledProcs.kind_mult(StringName(r[5]))), Elements.NAMES[int(r[4])] if int(r[4]) != Elements.PHYSICAL else "Physical"]
		out.append(DataItems._p(sig_power_id(StringName(r[0])), String(r[8]), desc, &"fabled_sig", 1.0, [&"weapon"], &"", [], &"fabled"))
	return out
