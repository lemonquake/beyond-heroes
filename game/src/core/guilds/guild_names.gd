class_name GuildNames
## bh-027: guild names that read like guilds, not like dice rolls. Every name is built from real words by a handful of
## patterns a chronicler would use — "The Iron Stags", "Order of the Gilded Anchor", "The Saltmarsh Wardens",
## "Emberhold Vanguard", "The Wandering Compass Company" — so no syllable soup ever reaches a banner. Places are two
## real words joined ("Ash" + "vale"), and each emblem carries its own plural ("Wolves", not "Wolfs").
##
## Deterministic for a given RandomNumberGenerator state; names already taken (compared without "The") are skipped.

const ADJECTIVES := ["Iron", "Silver", "Gilded", "Crimson", "Azure", "Ashen", "Emerald", "Twilight", "Stormborn", "Wandering",
	"Sworn", "Dawnlit", "Moonlit", "Unbroken", "Evergreen", "Starlit", "Golden", "Grey", "Stone", "Salt-Sworn", "Copper",
	"Scarlet", "Frostbound", "Sunforged", "Tidewatch", "Oathbound", "Brass", "Ivory", "Hearthbound", "Windward", "Last",
	"Undying", "Quiet", "Steadfast", "Lantern-Lit", "Thornwood", "Sable", "Violet", "Seafaring", "Highland"]

## emblem -> plural
const EMBLEMS := {
	"Stag": "Stags", "Wolf": "Wolves", "Raven": "Ravens", "Lion": "Lions", "Serpent": "Serpents", "Anchor": "Anchors",
	"Oak": "Oaks", "Compass": "Compasses", "Hammer": "Hammers", "Shield": "Shields", "Crown": "Crowns", "Rose": "Roses",
	"Falcon": "Falcons", "Bear": "Bears", "Tide": "Tides", "Flame": "Flames", "Star": "Stars", "Moon": "Moons",
	"Sun": "Suns", "Tower": "Towers", "Key": "Keys", "Thorn": "Thorns", "Hound": "Hounds", "Gull": "Gulls", "Heron": "Herons",
	"Otter": "Otters", "Boar": "Boars", "Blade": "Blades", "Arrow": "Arrows", "Bell": "Bells", "Kraken": "Krakens",
	"Griffin": "Griffins", "Lynx": "Lynxes", "Owl": "Owls", "Hawk": "Hawks", "Oar": "Oars", "Spear": "Spears",
}

const GROUPS := ["Company", "Fellowship", "Order", "Vanguard", "Wardens", "Rangers", "Guard", "Brigade", "League", "Society",
	"Circle", "Legion", "Watch", "Band", "Host", "Accord", "Pact", "Lodge", "Trust", "Banner", "Kinship", "Expedition"]
## groups that already read as a plural body of people ("the Saltmarsh Wardens")
const PLURAL_GROUPS := ["Wardens", "Rangers"]

const PLACE_HEADS := ["Ash", "Salt", "Thorn", "Stone", "Wind", "Frost", "Oak", "Raven", "Gull", "Tide", "Ember", "Mist", "Dun",
	"Bright", "Fen", "Iron", "Sea", "Elder", "Heron", "Gold", "Red", "Wolf", "Storm", "Mill", "Moss", "Pine", "Cliff", "Harbor"]
const PLACE_TAILS := ["vale", "hold", "reach", "ford", "moor", "crest", "haven", "marsh", "fall", "wick", "mere", "gate",
	"watch", "stead", "brook", "hollow", "cairn", "field", "shore", "wood", "ridge", "harbor"]

## Joins that read badly.
const REFUSED := ["harborharbor", "stonestead", "tidetide", "oakwood", "pinewood", "redreach", "ironiron", "millmill"]

const MOTTOS := ["Hold the line.", "Steel before sorrow.", "By oath and by oar.", "We keep the road open.", "No one walks alone.",
	"First in, last out.", "Light the way home.", "The tide always turns.", "Every debt repaid.", "Stand where others fall.",
	"Salt in the blood, fire in the heart.", "Few in number, many in deed.", "We do not forget.", "Guard the hearth.",
	"Onward, and together.", "From ash, we rise.", "Fortune favours the steady.", "Our word is our blade.",
	"Where the banner flies, we follow.", "Nothing is lost that is sought.", "Mend what is broken.", "Brave the dark.",
	"One shield, many hands.", "The storm is our song.", "We answer the bell.", "Faith in the fellow beside you.",
	"Hunt the shadow, spare the lost.", "Keep faith, keep watch.", "Bring them home.", "The oath outlives the sword."]

## A fresh guild name. `taken` holds names already in use (any case, with or without "The").
static func roll_name(rng: RandomNumberGenerator, taken: Array = []) -> String:
	var avoid := {}
	for t in taken:
		avoid[_key(String(t))] = true
	var best := ""
	for i in 60:
		var n := _roll(rng)
		if n.length() > 32:
			continue
		best = n
		if not avoid.has(_key(n)):
			return n
	return best if best != "" else "The Wandering Company"

static func _key(n: String) -> String:
	var k := n.strip_edges().to_lower()
	return k.substr(4) if k.begins_with("the ") else k

static func _pick(list: Array, rng: RandomNumberGenerator) -> String:
	return String(list[rng.randi_range(0, list.size() - 1)])

static func _emblem(rng: RandomNumberGenerator) -> String:
	var keys := EMBLEMS.keys()
	keys.sort()
	return String(keys[rng.randi_range(0, keys.size() - 1)])

## A place of Salmonan's kind: two real words joined, capitalised once ("Ashvale", "Saltmarsh", "Gullharbor").
static func place(rng: RandomNumberGenerator) -> String:
	for i in 20:
		var h := _pick(PLACE_HEADS, rng)
		var t := _pick(PLACE_TAILS, rng)
		var p := h + t
		# no doubled letter at the seam ("Ashhold", "Emberreach") and none of the joins that read badly
		if REFUSED.has(p.to_lower()) or h.substr(h.length() - 1).to_lower() == t.substr(0, 1):
			continue
		return p
	return "Ashvale"

static func _roll(rng: RandomNumberGenerator) -> String:
	var adj := _pick(ADJECTIVES, rng)
	var em := _emblem(rng)
	match rng.randi_range(0, 6):
		0:  # The Iron Stags
			return "The %s %s" % [adj, EMBLEMS[em]]
		1:  # Order of the Gilded Anchor
			var g := _pick(["Order", "Fellowship", "Brotherhood", "Circle", "League", "Society", "Company"], rng)
			return "%s of the %s %s" % [g, adj, em]
		2:  # The Saltmarsh Wardens
			var g := _pick(GROUPS, rng)
			return "The %s %s" % [place(rng), g]
		3:  # Emberhold Vanguard
			return "%s %s" % [place(rng), _pick(["Vanguard", "Watch", "Guard", "Company", "Legion", "Brigade", "Host", "Banner"], rng)]
		4:  # The Wolf and Anchor
			var em2 := _emblem(rng)
			if em2 == em:
				return "The %s %s" % [adj, EMBLEMS[em]]
			return "The %s and %s" % [em, em2]
		5:  # The Wandering Compass Company
			return "The %s %s %s" % [adj, em, _pick(["Company", "Band", "Lodge", "Trust", "Expedition", "Kinship"], rng)]
		_:  # Keepers of the Silver Tide
			var who := _pick(["Keepers", "Sons and Daughters", "Wardens", "Children", "Heirs", "Riders", "Hunters", "Shields"], rng)
			return "%s of the %s %s" % [who, adj, em]

## The short form a board or a nameplate uses ("Iron Stags", "Gilded Anchor", "Saltmarsh Wardens").
static func short(full: String) -> String:
	var s := full.strip_edges()
	if s.begins_with("The "):
		s = s.substr(4)
	var of := s.find(" of the ")
	if of >= 0:
		s = s.substr(of + 8)
	for g in ["Company", "Band", "Lodge", "Trust", "Expedition", "Kinship"]:
		if s.ends_with(" " + g) and s.count(" ") >= 2:
			s = s.substr(0, s.length() - g.length() - 1)
	return s

static func motto(rng: RandomNumberGenerator) -> String:
	return _pick(MOTTOS, rng)
