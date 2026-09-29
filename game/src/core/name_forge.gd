class_name NameForge
## bh-015: names built from three parts — a prefix, a middle and a suffix — so every new hero meets a different
## first Tempo and no two dropped weapons read the same.
##
## People (Tempos): syllables. PREFIX opens the name, MIDDLE (often empty) links it, SUFFIX closes it: "Kael" + "ven" +
## "dris" -> "Kaelvendris", "Ys" + "" + "oth" -> "Ysoth". Joins are smoothed (no three vowels or three consonants in a
## row, no doubled letters at a seam) and a name must be 4–10 letters. Every part is invented for Jre (LORE §8): no
## names borrowed from real cultures or languages, and a short list of sequences that read as real-world words is
## refused outright. Names already taken (other Tempos, townsfolk, renowned spirits) are skipped.
##
## Weapons (below Licensed; Licensed and better have proper names, ItemNames): words. A prefix made of a root and a
## tail ("Salt" + "worn" -> "Saltworn"), the base name in the middle, and a suffix ("of the Grey Ferry", "of Kaelmir").
## The weapon's element picks the roots ("Emberkissed", "Rimebound"), so a name still says something true.

const PREFIX := ["Ae", "Al", "Ar", "Ash", "Bael", "Bel", "Bran", "Cael", "Cor", "Cyr", "Dar", "Dor", "Drae", "El", "Ev",
	"Fael", "Fen", "Gal", "Gor", "Hal", "Hes", "Ith", "Jor", "Kael", "Kes", "Kor", "Lor", "Ly", "Mael", "Mor", "Nar",
	"Nev", "Or", "Os", "Pel", "Quel", "Ren", "Rho", "Sael", "Sel", "Tal", "Thal", "Tor", "Ul", "Vael", "Val", "Vesh",
	"Wyn", "Yl", "Ys", "Zel", "Zor", "Brev", "Cald", "Eth", "Grev", "Hald", "Irv", "Merr", "Oss", "Tev", "Vorn"]
const MIDDLE := ["", "", "", "", "", "a", "e", "i", "o", "ae", "ven", "dra", "ri", "mor", "sel", "the", "ver", "an", "el",
	"or", "ith", "wen", "ca"]
const SUFFIX := ["n", "r", "th", "ric", "wyn", "dor", "mir", "las", "vek", "sel", "ra", "ne", "iel", "ar", "os", "eth",
	"and", "is", "yn", "oth", "an", "el", "or", "ess", "ven", "dris", "rath", "wick", "holm", "dane", "ric", "vane", "mond",
	"ryn", "ros", "wen", "ald", "ek", "ith", "ane"]

## Sequences that read as real-world words or names: a rolled name containing one is thrown away.
const REFUSED := ["amihan", "dalis", "bayan", "lakan", "diwa", "ligaya", "mahal", "sinag", "ganda", "ibarra", "lola",
	"lolo", "tasyo", "mira", "tala", "malas", "sugue", "anak", "kuya", "hell", "damn", "ass", "fuk", "sex", "nazi",
	"god", "jesus", "allah", "orc", "hobbit"]

const VOWELS := "aeiouy"

# ---- People ----------------------------------------------------------------------------------------------------

## A new name from `rng`, not in `taken` (compared case-insensitively) and not any reserved name.
static func person(rng: RandomNumberGenerator, taken: Array = []) -> String:
	var avoid := {}
	for t in taken:
		avoid[String(t).get_slice(" ", 0).to_lower()] = true
	for r in reserved():
		avoid[r] = true
	var best := ""
	for i in 40:
		var n := _join3(_pick(PREFIX, rng), _pick(MIDDLE, rng), _pick(SUFFIX, rng))
		if not _good(n):
			continue
		best = n
		if not avoid.has(n.to_lower()):
			return n
	return best if best != "" else "Aelric"

## The first names of townsfolk and renowned spirits: a random Tempo never shares one.
static func reserved() -> Array:
	var out := []
	for id in DataTempos.LEGENDS:
		out.append(String(DataTempos.LEGENDS[id].name).get_slice(" ", 0).to_lower())
	if DB and "npcs" in DB:
		for n in DB.npcs.values():
			out.append(String(n.display_name).get_slice(" ", 0).to_lower())
	return out

static func _join3(a: String, b: String, c: String) -> String:
	return _seam(_seam(a, b), c).capitalize().replace(" ", "")

## Glue two parts: drop a doubled letter or a vowel clash at the seam.
static func _seam(a: String, b: String) -> String:
	if b == "" or a == "":
		return a + b
	var la := a[a.length() - 1].to_lower()
	var fb := b[0].to_lower()
	if la == fb:
		return a + b.substr(1)
	if VOWELS.contains(la) and VOWELS.contains(fb):
		return a + b.substr(1) if b.length() > 1 else a
	return a + b

static func _good(n: String) -> bool:
	if n.length() < 4 or n.length() > 10:
		return false
	var low := n.to_lower()
	for w in REFUSED:
		if low.contains(w):
			return false
	# no three vowels in a row; three consonants only around an h or after r / l / n ("rth", "ldr"), never four
	var run := ""
	for ch in low + "a":
		if VOWELS.contains(ch):
			if run.length() >= 4 or run.length() == 3 and not (run.contains("h") or run[0] in ["r", "l", "n"]):
				return false
			run = ""
		else:
			run += ch
	for i in low.length() - 2:
		if VOWELS.contains(low[i]) and VOWELS.contains(low[i + 1]) and VOWELS.contains(low[i + 2]):
			return false
	# no stutter ("elel", "anan") and no dangling "-ild" / "-old" sounds
	for i in low.length() - 3:
		if low.substr(i, 2) == low.substr(i + 2, 2):
			return false
	return not (low.ends_with("ild") or low.ends_with("old") or low.ends_with("rir"))

static func _pick(list: Array, rng: RandomNumberGenerator) -> String:
	return String(list[rng.randi_range(0, list.size() - 1)])

# ---- Weapons -----------------------------------------------------------------------------------------------------

## Roots by element (Elements enum order); PHYSICAL roots are plain craft and weather words.
const ROOTS := [
	["Salt", "Iron", "Oak", "Grey", "Old", "Stone", "Thorn", "Wolf", "Crow", "Hollow", "Bitter", "Grim", "Scar", "Red", "Black", "Wander"],
	["Ember", "Cinder", "Pyre", "Ash", "Scorch", "Flame"],
	["Rime", "Frost", "Winter", "Hoar", "Glacier", "Sleet"],
	["Storm", "Thunder", "Spark", "Tempest", "Bolt"],
	["Loam", "Root", "Quarry", "Boulder", "Moss"],
	["Gale", "Squall", "Zephyr", "Sky", "Gust"],
	["Tide", "Brine", "Wave", "Deep", "Reef"],
	["Dawn", "Sun", "Halo", "Bright", "Morrow"],
	["Gloam", "Dusk", "Night", "Shade", "Grave", "Hush"],
]
const TAILS := ["worn", "forged", "hewn", "bound", "wrought", "touched", "kissed", "bitten", "born", "marked", "sworn",
	"tempered", "cut", "blessed", "struck", "kept"]
## Suffix pieces: "of the <adjective> <place>" or "of <proper name>".
const SUFFIX_ADJ := ["Grey", "Last", "Quiet", "Broken", "Drowned", "Hollow", "Lantern", "Silent", "Burning", "Seventh",
	"Forgotten", "Wandering", "Iron", "Salted", "Pale", "Crimson", "Long", "Low"]
const SUFFIX_NOUN := ["Ferry", "Watch", "Road", "Vigil", "Tide", "Hearth", "March", "Oath", "Harbour", "Winter", "Gate",
	"Mile", "Barrow", "Moor", "Bell", "Pass", "Crossing", "Fields"]

## A forged prefix for a weapon of `element`: "Saltworn", "Emberkissed".
static func weapon_prefix(element: int, rng: RandomNumberGenerator) -> String:
	var roots: Array = ROOTS[element] if element >= 0 and element < ROOTS.size() else ROOTS[0]
	# an elemental weapon mostly takes its element's roots, sometimes a plain one
	if element != Elements.PHYSICAL and rng.randf() < 0.25:
		roots = ROOTS[0]
	return _pick(roots, rng) + _pick(TAILS, rng)

## A forged suffix: "of the Grey Ferry" or "of Kaelmir".
static func weapon_suffix(rng: RandomNumberGenerator) -> String:
	if rng.randf() < 0.4:
		return "of %s" % person(rng)
	return "of the %s %s" % [_pick(SUFFIX_ADJ, rng), _pick(SUFFIX_NOUN, rng)]
