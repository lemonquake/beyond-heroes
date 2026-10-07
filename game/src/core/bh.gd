class_name BH
## Project-wide constants: physics layers, attributes, equipment slots, rarities.

# Physics layers (bit values).
const LAYER_WORLD := 1
const LAYER_PLAYER := 2
const LAYER_ENEMY := 4
const LAYER_PROPS := 8
const LAYER_DEBRIS := 16
const LAYER_INTERACT := 32
const LAYER_GROUND := 64
const LAYER_HURTBOX := 128

enum Team { PLAYER, ENEMY, NEUTRAL }

# The six primary attributes, in display order.
const ATTRIBUTES: Array[StringName] = [&"str", &"agi", &"int", &"wis", &"spi", &"dex"]
const ATTRIBUTE_NAMES := {
	&"str": "Strength", &"agi": "Agility", &"int": "Intelligence",
	&"wis": "Wisdom", &"spi": "Spirit", &"dex": "Dexterity",
}
const ATTRIBUTE_ICONS := {
	&"str": "strength", &"agi": "agility", &"int": "intelligence",
	&"wis": "wisdom", &"spi": "spirit", &"dex": "dexterity",
}

# Equipment slots — the design spec's thirteen plus Leggings (bh-024).
const SLOTS: Array[StringName] = [
	&"main_weapon", &"sub_weapon", &"helm", &"inner_garment", &"armor", &"leggings",
	&"gloves_1", &"gloves_2", &"boots_1", &"boots_2",
	&"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4",
]
const SLOT_NAMES := {
	&"main_weapon": "Main Weapon", &"sub_weapon": "Sub Weapon", &"helm": "Helm",
	&"inner_garment": "Inner Garment", &"armor": "Armor", &"leggings": "Leggings",
	&"gloves_1": "Gloves I", &"gloves_2": "Gloves II",
	&"boots_1": "Boots I", &"boots_2": "Boots II",
	&"accessory_1": "Accessory I", &"accessory_2": "Accessory II",
	&"accessory_3": "Accessory III", &"accessory_4": "Accessory IV",
}
# Item category -> slots that accept it.
const CATEGORY_SLOTS := {
	&"weapon": [&"main_weapon", &"sub_weapon"],
	&"shield": [&"sub_weapon"],
	&"helm": [&"helm"],
	&"inner_garment": [&"inner_garment"],
	&"armor": [&"armor"],
	&"leggings": [&"leggings"],
	&"gloves": [&"gloves_1", &"gloves_2"],
	&"boots": [&"boots_1", &"boots_2"],
	&"accessory": [&"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4"],
}

# Item rarity — the ten exact tiers from the design spec, lowest to highest, and (bh-034) the four Ascendant tiers above
# them: Cosmic, Divine, Eternal and Primordial, found only on dungeon bosses of level 70+ (DataAscendant).
enum Rarity { BEGINNER, COMMON, BASIC, ADVANCED, LICENSED, ELITE, MASTER, MYTHICAL, LEGENDARY, AETHER, COSMIC, DIVINE, ETERNAL, PRIMORDIAL, ESCHATON }
const RARITY_COUNT := 15
const RARITY_NAMES := ["Beginner", "Common", "Basic", "Advanced", "Licensed", "Elite", "Master", "Mythical", "Legendary", "Aether",
	"Cosmic", "Divine", "Eternal", "Primordial", "Eschaton"]
const RARITY_COLORS := [
	Color(0.64, 0.60, 0.54), Color(0.90, 0.89, 0.86), Color(0.47, 0.86, 0.40), Color(0.38, 0.64, 1.00),
	Color(0.27, 0.87, 0.80), Color(1.00, 0.84, 0.30), Color(1.00, 0.58, 0.20), Color(0.86, 0.42, 1.00),
	Color(1.00, 0.33, 0.22), Color(0.58, 0.98, 1.00),
	Color(0.55, 0.47, 1.00), Color(1.00, 0.95, 0.66), Color(1.00, 0.52, 0.76), Color(1.00, 0.16, 0.26),
	Color(0.86, 0.91, 1.00),   # bh-041 Eschaton: mirror chrome (its names and frames also shimmer through the spectrum)
]
## One-line identity of each tier (tooltips, codex, docs).
const RARITY_DESC := [
	"Starting equipment. Simple and dependable.",
	"Basic loot with no enchantments.",
	"Improved equipment with one enchantment.",
	"The first real build customization: two enchantments.",
	"Specialized faction equipment carrying a guild license.",
	"High-quality rare equipment with strong enchantments.",
	"Masterwork gear: superior base quality and a perfected enchantment.",
	"Extremely rare magical items with a mythical property.",
	"Build-defining equipment with a legendary power.",
	"The extraordinary tier. Aether items alter your abilities.",
	"Ascendant. Starlight forged into steel, dropped only by dungeon lords of level 70 and above. Calls down falling stars.",
	"Ascendant. Blessed relics of a forgotten heaven, from dungeon lords of level 80 and above. Brings down holy Judgement.",
	"Ascendant. Pieces outside of time, from dungeon lords of level 90 and above. Every blow may Echo.",
	"Ascendant. The oldest things in the world, from dungeon lords of level 100 and above. The ground Erupts at your hand.",
	"Beyond Ascendant. The last things the world will make. No monster carries them: only Lape the Ancient, from the greatest treasures laid in his dishes. What it strikes is Unmade.",
]
## Loot presentation per tier: beam height (m, 0 = none), drop sound, label scale.
const RARITY_BEAM := [0.0, 0.0, 0.0, 1.2, 1.6, 2.4, 3.2, 4.2, 5.5, 8.0, 10.0, 11.0, 12.0, 14.0, 18.0]
const RARITY_DROP_SOUND := [&"loot_drop", &"loot_drop", &"loot_drop", &"loot_drop", &"loot_drop_rare", &"loot_drop_rare",
	&"loot_drop_rare", &"loot_drop_legendary", &"loot_drop_legendary", &"loot_drop_legendary", &"loot_drop_legendary",
	&"loot_drop_legendary", &"loot_drop_legendary", &"loot_drop_legendary", &"loot_drop_legendary"]

const LEVEL_CAP := 300

static func rarity_color(r: int) -> Color:
	return RARITY_COLORS[clampi(r, 0, RARITY_COUNT - 1)]

static func rarity_name(r: int) -> String:
	return RARITY_NAMES[clampi(r, 0, RARITY_COUNT - 1)]
