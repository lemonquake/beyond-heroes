class_name Elements
## Centralized elemental damage table.
##
## Two independent layers decide how much elemental damage lands:
##  1. AFFINITY matrix (attack element x defender affinity) — thematic strengths/weaknesses.
##  2. Numeric resistances on the defender (res_<element>), with penetration and caps, handled by DamagePipeline.
## Every non-neutral entry in the matrix has a written reason in RELATION_NOTES.

enum { PHYSICAL, FIRE, ICE, LIGHTNING, EARTH, WIND, WATER, LIGHT, DARK }
const COUNT := 9
const ELEMENTAL: Array[int] = [FIRE, ICE, LIGHTNING, EARTH, WIND, WATER, LIGHT, DARK]

const KEYS: Array[StringName] = [&"physical", &"fire", &"ice", &"lightning", &"earth", &"wind", &"water", &"light", &"dark"]
const NAMES: Array[String] = ["Physical", "Fire", "Ice", "Lightning", "Earth", "Wind", "Water", "Light", "Dark"]
const COLORS: Array[Color] = [
	Color(0.86, 0.84, 0.80), Color(1.0, 0.45, 0.12), Color(0.55, 0.88, 1.0),
	Color(0.98, 0.92, 0.35), Color(0.78, 0.58, 0.30), Color(0.62, 0.95, 0.66),
	Color(0.20, 0.55, 1.0), Color(1.0, 0.95, 0.70), Color(0.66, 0.35, 0.95),
]
## Identity: the status each element builds up on hit.
const STATUS_OF: Array[StringName] = [&"stagger", &"burning", &"chilled", &"shocked", &"armor_broken", &"windswept", &"wet", &"purged", &"cursed"]
const IDENTITY: Array[String] = [
	"Raw force. Mitigated by Defense; builds Stagger.",
	"Burning: damage over time. Offensive pressure. Spreads with Wind.",
	"Chill slows; Chill buildup becomes Freeze. Wet targets freeze twice as fast.",
	"Shock: target takes more damage. High burst, can chain. Wet targets are shocked harder.",
	"Armor Break (-40% Defense) and heavy stagger. Crushes armored targets harder.",
	"Windswept: knockback x1.5 and slowed. Fans Burning onto nearby foes.",
	"Wet: conducts Lightning, speeds Freeze, extinguishes Burning.",
	"Radiant. Purges enemy regeneration and buffs; purifies Curses for a burst.",
	"Curse amplifies all damage taken; Dark hits drain life and rend Purged targets.",
]
## Audio identity: cast and impact sounds per element (names in assets/audio/sfx).
const SFX_CAST: Array[StringName] = [&"swing_heavy", &"cast_fire", &"cast_ice", &"cast_lightning", &"cast_earth", &"wind_gust", &"water_wave", &"holy_chime", &"dark_cast"]
const SFX_HIT: Array[StringName] = [&"hit_flesh", &"fire_explode", &"freeze", &"lightning_zap", &"rock_impact", &"wind_gust", &"water_splash", &"holy_strike", &"dark_curse"]
## Visual identity: short description of each element's VFX language (docs + codex).
const VFX_NOTES: Array[String] = [
	"Dust, sparks and white impact flashes.", "Orange-white flames, embers and heat shimmer.", "Pale blue frost shards, mist and ice crystals.",
	"Yellow-white forked arcs and bright flicker.", "Ochre rock chunks, dust clouds and ground cracks.", "Pale green swirling streaks and leaves.",
	"Deep blue splashes, droplets and ripples.", "Warm golden radiance, halos and motes.", "Violet-black smoke, tendrils and drained sparks.",
]

## Affinity multiplier: AFFINITY[attack][defender_affinity].
## Neutral affinity is PHYSICAL (index 0) — no elemental nature.
## Wheel: Fire > Ice > Wind > Earth > Lightning > Water > Fire. Strong 1.5, reverse 0.75, same 0.5.
## Light and Dark oppose each other (1.5 both ways), same 0.5.
const STRONG := 1.5
const WEAK := 0.75
const SAME := 0.5
static var _matrix: Array = []

const RELATION_NOTES := {
	"fire>ice": "Fire melts ice.",
	"ice>wind": "Ice stills and freezes moving air.",
	"wind>earth": "Wind erodes stone and scatters dust.",
	"earth>lightning": "Earth grounds lightning.",
	"lightning>water": "Water conducts lightning.",
	"water>fire": "Water douses fire.",
	"light>dark": "Radiance burns away corruption.",
	"dark>light": "Corruption devours the holy.",
	"same": "Creatures of an element shrug off half of that element.",
	"reverse": "Attacking against the wheel is 25% weaker (e.g. Ice into a Fire creature melts).",
	"physical": "Physical damage ignores affinity; Defense and Physical Resistance handle it.",
}

static func _build() -> void:
	_matrix.resize(COUNT)
	for a in COUNT:
		var row: Array[float] = []
		row.resize(COUNT)
		row.fill(1.0)
		_matrix[a] = row
	var wheel := [FIRE, ICE, WIND, EARTH, LIGHTNING, WATER]
	for i in wheel.size():
		var atk: int = wheel[i]
		var beats: int = wheel[(i + 1) % wheel.size()]
		_matrix[atk][beats] = STRONG
		_matrix[beats][atk] = WEAK
	_matrix[LIGHT][DARK] = STRONG
	_matrix[DARK][LIGHT] = STRONG
	for e in ELEMENTAL:
		_matrix[e][e] = SAME

static func affinity(attack_element: int, defender_affinity: int) -> float:
	if _matrix.is_empty():
		_build()
	if attack_element == PHYSICAL or defender_affinity == PHYSICAL:
		return 1.0
	return _matrix[attack_element][defender_affinity]

static func key(e: int) -> StringName:
	return KEYS[e]

static func from_key(k: StringName) -> int:
	var i := KEYS.find(k)
	return i if i >= 0 else PHYSICAL

static func res_key(e: int) -> StringName:
	return StringName("res_" + String(KEYS[e])) if e != PHYSICAL else &"phys_res"

static func dmg_key(e: int) -> StringName:
	return StringName("dmg_" + String(KEYS[e]))

static func pen_key(e: int) -> StringName:
	return StringName("pen_" + String(KEYS[e])) if e != PHYSICAL else &"pen_armor"

static func color(e: int) -> Color:
	return COLORS[e]

## Developer-viewable damage matrix as Markdown (also written to docs/ELEMENT_MATRIX.md by the test runner).
static func matrix_markdown() -> String:
	var s := "# Beyond Heroes — Elemental Damage Matrix\n\n"
	s += "Rows: attacking element. Columns: defender affinity. Values multiply damage before numeric resistance.\n\n"
	s += "| Attack \\ Affinity |"
	for d in ELEMENTAL:
		s += " %s |" % NAMES[d]
	s += "\n|---|" + "---|".repeat(ELEMENTAL.size()) + "\n"
	for a in ELEMENTAL:
		s += "| **%s** |" % NAMES[a]
		for d in ELEMENTAL:
			var m := affinity(a, d)
			s += (" **%.2f** |" % m) if m > 1.0 else ((" _%.2f_ |" % m) if m < 1.0 else " 1.00 |")
		s += "\n"
	s += "\nPhysical attacks and neutral (no-affinity) defenders always use 1.00.\n\n## Relationships\n\n"
	for k in RELATION_NOTES:
		s += "- **%s** — %s\n" % [k, RELATION_NOTES[k]]
	s += "\n## Element identities\n\n"
	for e in COUNT:
		s += "- **%s** (builds `%s`): %s\n" % [NAMES[e], STATUS_OF[e], IDENTITY[e]]
	s += "\n## Interactions (StatusController)\n\n"
	for line in StatusRules.INTERACTION_DOCS:
		s += "- %s\n" % line
	return s
