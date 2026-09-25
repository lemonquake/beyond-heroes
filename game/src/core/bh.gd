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

# Equipment slots — exact configuration from the design spec.
const SLOTS: Array[StringName] = [
	&"main_weapon", &"sub_weapon", &"helm", &"inner_garment", &"armor",
	&"gloves_1", &"gloves_2", &"boots_1", &"boots_2",
	&"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4",
]
const SLOT_NAMES := {
	&"main_weapon": "Main Weapon", &"sub_weapon": "Sub Weapon", &"helm": "Helm",
	&"inner_garment": "Inner Garment", &"armor": "Armor",
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
	&"gloves": [&"gloves_1", &"gloves_2"],
	&"boots": [&"boots_1", &"boots_2"],
	&"accessory": [&"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4"],
}

enum Rarity { COMMON, MAGIC, RARE, EPIC, LEGENDARY, MYTHIC }
const RARITY_NAMES := ["Common", "Magic", "Rare", "Epic", "Legendary", "Mythic"]
const RARITY_COLORS := [
	Color(0.82, 0.80, 0.76), Color(0.42, 0.62, 1.0), Color(1.0, 0.86, 0.32),
	Color(0.72, 0.42, 1.0), Color(1.0, 0.55, 0.12), Color(1.0, 0.24, 0.30),
]

const LEVEL_CAP := 60

static func rarity_color(r: int) -> Color:
	return RARITY_COLORS[clampi(r, 0, RARITY_COLORS.size() - 1)]
