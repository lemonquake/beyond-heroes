class_name DataRelics
## Relics and gacha loot (bh-012): Relic Caches, Soul Embers, dungeon materials, the new equipment passives, relic
## powers, and the word tables ItemNames draws a unique proper name and epithet from.
## Every name part is invented for Jre (user rule: no Filipino or other real-culture names).

const ICON3D := "res://assets/ui/icons/items3d/%s.png"

## Relic Cache tiers: what each holds when opened (ItemGenerator.relic_items) and how it looks in the reveal.
const CACHES := [
	{"id": &"relic_cache_worn", "name": "Worn Relic Cache", "items": 2, "floor": BH.Rarity.ELITE, "min": BH.Rarity.ADVANCED, "bonus": 0.3, "ilvl": 0,
		"color": Color(0.75, 0.6, 0.4), "value": 80,
		"flavor": "A sealed coffer from the deep places, its lock rusted shut. Open it: two pieces of gear, at least one Elite."},
	{"id": &"relic_cache_gilded", "name": "Gilded Relic Cache", "items": 3, "floor": BH.Rarity.MASTER, "min": BH.Rarity.ELITE, "bonus": 0.8, "ilvl": 2,
		"color": Color(1.0, 0.78, 0.3), "value": 260,
		"flavor": "Gold leaf over black iron, warm to the touch. Three pieces of gear, at least one Master-made."},
	{"id": &"relic_cache_radiant", "name": "Radiant Relic Cache", "items": 4, "floor": BH.Rarity.MYTHICAL, "min": BH.Rarity.MASTER, "bonus": 1.6, "ilvl": 4,
		"color": Color(0.8, 0.6, 1.0), "value": 900,
		"flavor": "It hums, and the light leaks out between the slats. Four pieces of gear, at least one Mythical — and sometimes far more."},
]

## The five dungeon materials (DataDungeons LIST.material) and the Soul Ember.
const MATERIALS := [
	[&"glowcap_spore", "Glowcap Spore", 14, 50, "A pinch of glowing dust from the Hollowroot Warren. Alchemists pay well for it."],
	[&"tide_pearl", "Tide Pearl", 18, 50, "A grey pearl from the Saltmouth Deeps. Hold it to your ear and it rings like a bell."],
	[&"slag_ember", "Slag Ember", 22, 50, "A lump of slag from the Emberforge Depths that never quite cools."],
	[&"rime_shard", "Rime Shard", 26, 50, "Ice from the Rimeglass Barrow. It frosts your fingers even through gloves."],
	[&"star_glass", "Starglass", 32, 50, "A splinter of the Shattered Orrery's lenses, with a tiny moving star inside."],
]

static func items(out: Array) -> void:
	for c in CACHES:
		var b := ItemBaseDef.new()
		b.id = c.id
		b.display_name = c.name
		b.category = &"consumable"
		b.icon = ICON3D % c.id
		b.stack_max = 20
		b.value = int(c.value)
		b.weight = 0.5
		b.drop_weight = 0
		b.flavor = c.flavor
		b.consumable_effect = {"cache": CACHES.find(c)}
		out.append(b)
	var e := ItemBaseDef.new()
	e.id = &"soul_ember"
	e.display_name = "Soul Ember"
	e.category = &"material"
	e.icon = ICON3D % "soul_ember"
	e.stack_max = 9999
	e.value = 0
	e.weight = 0.01
	e.drop_weight = 0
	e.sellable = false
	e.flavor = "A spark of a fallen warrior's will. At the Shrine of the Fallen, Veyra Ashgrave burns them to call Tempos: %d for one call, %d for ten." % [TempoGacha.COST_ONE, TempoGacha.COST_TEN]
	out.append(e)
	for m in MATERIALS:
		var b := ItemBaseDef.new()
		b.id = m[0]
		b.display_name = m[1]
		b.category = &"material"
		b.icon = ICON3D % m[0]
		b.value = m[2]
		b.stack_max = m[3]
		b.flavor = m[4]
		b.weight = 0.1
		b.drop_weight = 0
		out.append(b)

## New equipment passives (bh-012): gold, experience, regeneration %, on-kill restoration, potions, thorns, champions,
## Soul Embers and Tempos. Rows as DataItems._a(): id, label, prefix, stat, op, tiers, categories, group, weight, integer.
static func affixes() -> Array:
	var F := StatModifier.Op.FLAT
	var I := StatModifier.Op.INC
	var WEAP := [&"weapon"]
	var ARM := [&"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"shield"]
	var JEW := [&"accessory"]
	return [
		DataItems._a(&"gold_find", "of Plenty", false, &"gold_find", I, [[1, 0.08, 0.15], [12, 0.16, 0.28], [25, 0.29, 0.45]],
			JEW + [&"helm", &"gloves", &"boots"], &"gold_find", 60),
		DataItems._a(&"xp_gain", "of Learning", false, &"xp_gain", I, [[1, 0.03, 0.06], [12, 0.07, 0.1], [25, 0.11, 0.15]],
			JEW + [&"helm", &"armor"], &"xp_gain", 45),
		DataItems._a(&"hp_regen_pct", "of Vigor", false, &"hp_regen", I, [[1, 0.1, 0.2], [12, 0.21, 0.35], [25, 0.36, 0.5]],
			ARM + JEW, &"hp_regen_pct", 60),
		DataItems._a(&"mana_regen_pct", "of the Wellspring", false, &"mana_regen", I, [[1, 0.1, 0.2], [12, 0.21, 0.35], [25, 0.36, 0.5]],
			ARM + JEW + WEAP, &"mana_regen_pct", 60),
		DataItems._a(&"hp_on_kill", "of Reaping", false, &"hp_on_kill", F, [[1, 3, 6], [12, 7, 14], [25, 15, 28]],
			WEAP + JEW + [&"gloves"], &"hp_on_kill", 50, true),
		DataItems._a(&"mana_on_kill", "of the Harvest", false, &"mana_on_kill", F, [[1, 2, 4], [12, 5, 9], [25, 10, 16]],
			WEAP + JEW, &"mana_on_kill", 45, true),
		DataItems._a(&"potion_power", "of the Alchemist", false, &"potion_power", I, [[1, 0.1, 0.18], [15, 0.19, 0.3]],
			[&"armor", &"gloves", &"accessory", &"inner_garment"], &"potion_power", 45),
		DataItems._a(&"thorns", "Thorned", true, &"thorns", F, [[1, 3, 6], [12, 8, 16], [25, 18, 32]],
			[&"armor", &"shield", &"inner_garment"], &"thorns", 50, true),
		DataItems._a(&"elite_damage", "Champion-slaying", true, &"elite_damage", I, [[5, 0.06, 0.1], [15, 0.11, 0.18], [30, 0.19, 0.26]],
			WEAP + JEW + [&"gloves"], &"elite_damage", 45),
		DataItems._a(&"ember_find", "of the Spirit-caller", false, &"ember_find", I, [[1, 0.1, 0.2], [15, 0.21, 0.35]],
			JEW + [&"helm"], &"ember_find", 35),
		DataItems._a(&"tempo_damage", "Soulbound", true, &"tempo_damage", I, [[1, 0.08, 0.15], [15, 0.16, 0.26], [30, 0.27, 0.4]],
			JEW + [&"helm", &"armor"], &"tempo_damage", 45),
	]

## Relic powers (bh-012): a fourth power tier rolled by Licensed and better gear as a "signature" passive. They are
## plain stat bundles (no new behaviour), so each reads clearly on the tooltip.
static func powers() -> Array:
	var I := StatModifier.Op.INC
	var F := StatModifier.Op.FLAT
	return [
		_p(&"r_goldrush", "Goldrush", "+35% Gold Find and +10% Magic Find.", [[&"gold_find", I, 0.35], [&"magic_find", F, 0.1]], [&"accessory", &"gloves", &"boots", &"helm"]),
		_p(&"r_scholar", "Scholar's", "+12% Experience gained.", [[&"xp_gain", I, 0.12]], [&"accessory", &"helm", &"armor"]),
		_p(&"r_spring", "Springwater", "+40% HP Regeneration and +40% Mana Regeneration.", [[&"hp_regen", I, 0.4], [&"mana_regen", I, 0.4]], []),
		_p(&"r_reaper", "Reaper's", "Kills restore 20 HP and 10 Mana.", [[&"hp_on_kill", F, 20.0], [&"mana_on_kill", F, 10.0]], [&"weapon", &"gloves", &"accessory"]),
		_p(&"r_alchemist", "Alchemist's", "Potions restore 30% more.", [[&"potion_power", I, 0.3]], [&"armor", &"accessory", &"gloves", &"inner_garment"]),
		_p(&"r_bramble", "Bramblecoat", "Melee attackers take 40 damage.", [[&"thorns", F, 40.0]], [&"armor", &"shield", &"inner_garment"]),
		_p(&"r_giantbane", "Giantbane", "22% more damage against elites, champions and bosses.", [[&"elite_damage", I, 0.22]], [&"weapon", &"gloves", &"accessory"]),
		_p(&"r_spiritcall", "Spirit-called", "+40% Soul Embers found and your Tempos deal 15% more damage.", [[&"ember_find", I, 0.4], [&"tempo_damage", I, 0.15]], [&"accessory", &"helm"]),
		_p(&"r_windrunner", "Windrunner's", "+8% Movement Speed and 15% faster dodge recovery.", [[&"move_speed", I, 0.08], [&"dodge_cooldown", I, -0.15]], [&"boots"]),
		_p(&"r_bulwark", "Unbowed", "+12% maximum HP and +8% to all resistances.", [[&"max_hp", I, 0.12], [&"res_all", F, 0.08]], [&"armor", &"helm", &"shield"]),
	]

static func _p(id: StringName, name: String, desc: String, mods: Array, cats: Array) -> LegendaryPowerDef:
	var list := []
	for m in mods:
		list.append(StatModifier.new(m[0], m[1], m[2]))
	return DataItems._p(id, name, desc, &"relic", 1.0, cats, &"", list, &"relic")

# ---- Name tables (ItemNames) --------------------------------------------------------------------------------------

const ONSET := ["Vor", "Kael", "Thar", "Mor", "Ess", "Val", "Dra", "Sil", "Gar", "Fen", "Ul", "Bre", "Cor", "Hal", "Isk",
	"Ryn", "Ast", "Zor", "Ner", "Tor", "Ael", "Wyr", "Grim", "Sol", "Khar", "Ves", "Oth", "Cyr", "Dun", "Eld", "Fyr",
	"Gwen", "Hroth", "Ith", "Jor", "Kest", "Lor", "Myr", "Nyx", "Orn", "Pry", "Quel", "Rhae", "Sket", "Tyr", "Urth", "Vyl", "Wren", "Xan", "Yor", "Zeph"]
const MIDDLE := ["", "", "", "e", "i", "o", "ae", "y", "or", "an", "el", "ith", "en", "ar"]
const CODA := ["thar", "ghast", "mund", "dris", "wyn", "reth", "gar", "vane", "dor", "mir", "quill", "sk", "nor", "ven", "rak",
	"dell", "holt", "ris", "byrn", "thel", "gorn", "lith", "grim", "wald", "fang", "crest", "moor", "spire", "shard", "brand",
	"helm", "ward", "rune", "vex", "kar", "loch", "wick", "morn", "vald", "thorn"]

## Epithet nouns by item category.
const NOUNS := {
	&"weapon": ["Fang", "Edge", "Bane", "Reaver", "Song", "Oath", "Vow", "Verdict", "Requiem", "Fury", "Promise", "Hunger", "Whisper", "Thunder", "Mercy"],
	&"shield": ["Aegis", "Bulwark", "Wall", "Refuge", "Bastion", "Vigil"],
	&"helm": ["Crown", "Visage", "Brow", "Gaze", "Diadem", "Watch"],
	&"armor": ["Mantle", "Shroud", "Carapace", "Vigil", "Embrace", "Bulwark", "Hide"],
	&"inner_garment": ["Veil", "Skin", "Weave", "Second Skin", "Lining"],
	&"gloves": ["Grip", "Grasp", "Hand", "Touch", "Reach"],
	&"boots": ["Stride", "Path", "March", "Wander", "Step"],
	&"accessory": ["Sigil", "Seal", "Eye", "Heart", "Tear", "Coil", "Knot", "Echo", "Star"],
}

## Theme words by element key, then by affix stat (the strongest affix picks the word when no element speaks).
const ELEMENT_WORDS := {
	&"fire": ["Ember", "Cinder", "Pyre", "Ash", "Kindled Sun", "Last Flame"],
	&"ice": ["Rime", "Winter", "Frost", "Long Night", "White Silence", "Glacier"],
	&"lightning": ["Storm", "Thunder", "Tempest", "Broken Sky", "Skyfall"],
	&"dark": ["Night", "Hollow", "Umbra", "Black Tide", "Unlit Hour"],
	&"light": ["Dawn", "Radiance", "First Light", "Morning Star"],
	&"earth": ["Stone", "Mountain", "Deep Root", "Iron Hill"],
	&"water": ["Tide", "Deep", "Drowned Bell", "Salt Wind", "Undertow"],
	&"wind": ["Gale", "Howling Pass", "Four Winds"],
}
const STAT_WORDS := {
	&"life_leech": ["Blood", "Red Thirst"], &"hp_on_kill": ["Harvest", "Reaping"], &"crit_chance": ["Ruin", "Keen Eye"],
	&"crit_damage": ["Ruin", "Executioner"], &"gold_find": ["Fortune", "Coin", "Gilded Road"], &"xp_gain": ["Wisdom", "Lore"],
	&"magic_find": ["Fortune", "Luck"], &"hp_regen": ["Mending", "Spring"], &"mana_regen": ["Wellspring", "Clear Mind"],
	&"tempo_damage": ["Spirits", "Fallen Choir"], &"ember_find": ["Embers", "Spirits"], &"thorns": ["Thorns", "Bramble"],
	&"elite_damage": ["Giants", "Champions"], &"attack_speed": ["Fury", "Quickening"], &"move_speed": ["Wind", "Wanderer"],
	&"max_hp": ["Oak", "Unbroken"], &"defense": ["Iron", "Rampart"], &"str": ["Titan", "Ox"], &"agi": ["Lynx", "Swift Hunt"],
	&"int": ["Sage", "Stars"], &"wis": ["Owl", "Still Water"], &"spi": ["Monk", "Candle"], &"dex": ["Hawk", "True Aim"],
}
const PLAIN_WORDS := ["Forgotten King", "Last Watch", "Silent Road", "Broken Oath", "Old Kings", "Lost Legion", "Wandering Star", "Unsung", "Long March", "First Oath"]
const TEMPLATES := ["%s of the %s", "%s of %s", "the %s's %s", "%s of the %s"]
