class_name CrystalNames
## bh-022: the name a piece of equipment earns from the crystals set in its sockets ("Iron Longsword of the Nova Blast").
##
## Every crystal adds its grade + 1 (Fragment 1 .. Orbital 4) to its family's power in the piece. The families are
## ranked by power (ties: DataCrystals.ORDER), then:
##   one family       its own suffix, by tier = the best crystal's grade, or more when many are set (power 3 / 6 / 10):
##                    "of Embers" < "of the Burning" < "of the Blaze" < "of the Inferno"
##   two families     the pair's hybrid name (all 28 pairs), grander with power:  "of the Nova Blast" <
##                    "of the Grand Nova Blast" < "of the Eternal Nova Blast"
##   three families   the top pair's name with the third family's epithet:  "of the Venomous Nova Blast"
##   four             "of the Fourfold Nova Blast"
##   five or more     "of the Prismatic Nova Blast"
## Pieces with no crystal set (empty sockets included) keep their ordinary name.

## Power at which a single family's name climbs a tier (index = tier); the best crystal's grade is a floor.
const SINGLE_STEPS := [1, 3, 6, 10]
## Combined power of the top two families at which a hybrid name becomes Grand / Eternal.
const GRAND_AT := 4
const ETERNAL_AT := 8

## family -> [tier 0, tier 1, tier 2, tier 3]
const SINGLE := {
	&"ember": ["of Embers", "of the Burning", "of the Blaze", "of the Inferno"],
	&"aqua": ["of the Spring", "of the Tide", "of the Deep", "of the Maelstrom"],
	&"nova": ["of Starlight", "of the Nova", "of the Dawnstar", "of the Supernova"],
	&"thundra": ["of Sparks", "of Thunder", "of the Tempest", "of the Storm Throne"],
	&"vipera": ["of Venom", "of the Viper", "of the Basilisk", "of the Hydra"],
	&"bloodrift": ["of Leeching", "of the Bloodletter", "of the Crimson Rift", "of the Blood Sovereign"],
	&"essencerift": ["of Whispers", "of the Mindrift", "of the Soul Siphon", "of the Starved Void"],
	&"aetherift": ["of the Aether", "of Riftlight", "of the Worldtear", "of the Firmament"],
}

## The epithet a third family lends a hybrid name.
const EPITHET := {
	&"ember": "Burning", &"aqua": "Tidal", &"nova": "Radiant", &"thundra": "Thundering",
	&"vipera": "Venomous", &"bloodrift": "Bloodthirsty", &"essencerift": "Whispering", &"aetherift": "Aetheric",
}

## Every unordered pair of families -> the hybrid's name (key: the two ids in DataCrystals.ORDER order, "a+b").
const HYBRID := {
	"ember+aqua": "Scalding Tide",
	"ember+nova": "Nova Blast",
	"ember+thundra": "Firestorm",
	"ember+vipera": "Brimstone Fang",
	"ember+bloodrift": "Blood Pyre",
	"ember+essencerift": "Soulfire",
	"ember+aetherift": "Phoenix Rift",
	"aqua+nova": "Moontide",
	"aqua+thundra": "Stormsurge",
	"aqua+vipera": "Blackwater",
	"aqua+bloodrift": "Red Tide",
	"aqua+essencerift": "Drowned Mind",
	"aqua+aetherift": "Starlit Deep",
	"nova+thundra": "Thunderstar",
	"nova+vipera": "Plague Star",
	"nova+bloodrift": "Blood Moon",
	"nova+essencerift": "Eclipse",
	"nova+aetherift": "Heavenfall",
	"thundra+vipera": "Venom Storm",
	"thundra+bloodrift": "Crimson Thunder",
	"thundra+essencerift": "Mindstorm",
	"thundra+aetherift": "Skyrend",
	"vipera+bloodrift": "Blood Viper",
	"vipera+essencerift": "Nightshade",
	"vipera+aetherift": "Rift Serpent",
	"bloodrift+essencerift": "Devourer",
	"bloodrift+aetherift": "Bleeding Sky",
	"essencerift+aetherift": "Astral Mind",
}

## [[family, power, best grade], ...] strongest first, for the crystals in `gems` (ids or "" for an empty socket).
static func ranking(gems: Array) -> Array:
	var power := {}
	var best := {}
	for g in gems:
		var id := StringName(String(g))
		var f := DataCrystals.family_of(id)
		if f == &"":
			continue
		power[f] = int(power.get(f, 0)) + DataCrystals.grade_of(id) + 1
		best[f] = maxi(int(best.get(f, 0)), DataCrystals.grade_of(id))
	var out: Array = []
	for f in power:
		out.append([f, power[f], best[f]])
	out.sort_custom(func(a, b) -> bool:
		if a[1] != b[1]:
			return a[1] > b[1]
		return DataCrystals.ORDER.find(a[0]) < DataCrystals.ORDER.find(b[0]))
	return out

static func single_tier(power: int, best_grade := 0) -> int:
	var t := clampi(best_grade, 0, 3)
	for i in SINGLE_STEPS.size():
		if power >= SINGLE_STEPS[i]:
			t = maxi(t, i)
	return t

static func hybrid_name(a: StringName, b: StringName) -> String:
	var ia := DataCrystals.ORDER.find(a)
	var ib := DataCrystals.ORDER.find(b)
	var key := "%s+%s" % [a, b] if ia <= ib else "%s+%s" % [b, a]
	return String(HYBRID.get(key, ""))

## The suffix for a set of crystals ("" when none is set).
static func suffix_for(gems: Array) -> String:
	var r := ranking(gems)
	match r.size():
		0:
			return ""
		1:
			return String(SINGLE[r[0][0]][single_tier(int(r[0][1]), int(r[0][2]))])
	var pair := hybrid_name(r[0][0], r[1][0])
	if r.size() == 2:
		var p := int(r[0][1]) + int(r[1][1])
		var grand := "Eternal " if p >= ETERNAL_AT else ("Grand " if p >= GRAND_AT else "")
		return "of the %s%s" % [grand, pair]
	if r.size() == 3:
		return "of the %s %s" % [EPITHET[r[2][0]], pair]
	if r.size() == 4:
		return "of the Fourfold %s" % pair
	return "of the Prismatic %s" % pair

static func suffix(it: ItemInstance) -> String:
	if it == null or it.gems.is_empty():
		return ""
	return suffix_for(it.gems)

## The infusion colour of a piece: its crystals' family colours weighted by power (Color(0,0,0,0) when none).
static func color_for(gems: Array) -> Color:
	var r := ranking(gems)
	if r.is_empty():
		return Color(0, 0, 0, 0)
	var c := Color(0, 0, 0)
	var total := 0.0
	for e in r:
		var w := float(e[1])
		var fc: Color = DataCrystals.FAMILIES[e[0]].color
		c += Color(fc.r * w, fc.g * w, fc.b * w)
		total += w
	return Color(c.r / total, c.g / total, c.b / total, 1.0)

## Total crystal power set in a piece (0 = none): drives how strongly the infusion glows.
static func power(gems: Array) -> int:
	var t := 0
	for e in ranking(gems):
		t += int(e[1])
	return t
