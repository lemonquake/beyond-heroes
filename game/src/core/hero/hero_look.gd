class_name HeroLook
extends RefCounted
## bh-023: how a hero looks. Pure data (a Dictionary the save file, the creator and the network all pass around) plus
## the rules for it: defaults, ranges, the lists of styles, clean-up of anything read from disk or the network, random
## looks and the creator's presets. No nodes; HeroBody turns a look into a model.
##
## An empty Dictionary means "the plain hero": every hero made before bh-023 loads that way.

const VERSION := 1
const MODEL := "res://assets/characters/hero.glb"

## Sliders: key -> [default, min, max]. The top of many ranges is deliberately silly.
const SLIDERS := {
	"female": [0.0, 0.0, 1.0],
	"height": [1.0, 0.82, 1.18], "head": [1.0, 0.7, 2.2], "hands": [1.0, 0.7, 2.4], "feet": [1.0, 0.7, 2.4],
	"muscle": [0.0, -1.0, 1.5], "belly": [0.0, -0.6, 2.2], "build": [0.0, -1.0, 2.0], "rear": [0.0, -0.5, 2.5],
	"nose_size": [0.0, -0.8, 3.0], "nose_long": [0.0, -0.4, 3.5], "nose_wide": [0.0, -0.8, 2.5], "nose_up": [0.0, -1.5, 1.5],
	"ears_size": [0.0, -0.9, 3.0], "ears_point": [0.0, 0.0, 3.0], "ears_out": [0.0, -0.5, 2.5],
	"lips_full": [0.0, -1.0, 2.5], "mouth_wide": [0.0, -0.8, 2.0], "mouth_smile": [0.0, -1.5, 2.0],
	"jaw_wide": [0.0, -1.0, 1.5], "chin_long": [0.0, -0.8, 3.0], "cheeks": [0.0, -1.0, 1.6], "brow_heavy": [0.0, -1.0, 2.5],
	"eyes_pop": [0.0, -1.0, 2.5],
	"eye_size": [1.0, 0.5, 3.2], "eye_spacing": [0.0, -0.008, 0.014], "eye_height": [0.0, -0.006, 0.010],
	"eye_tilt": [0.0, -0.4, 0.4], "eye_glow": [0.0, 0.0, 1.0],
	"brow_thick": [1.0, 0.4, 3.0], "brow_tilt": [0.0, -0.5, 0.5], "brow_height": [0.0, -0.004, 0.012],
	"hair_length": [0.0, 0.0, 4.0], "beard_length": [0.0, 0.0, 4.0], "stubble": [0.3, 0.0, 1.0],
	"lip_amount": [0.0, 0.0, 1.0], "pattern_amount": [1.0, 0.2, 1.0], "pattern_scale": [1.0, 0.4, 3.0],
}
## The sliders that are shape keys on the body mesh (tools/blender/hero/hero_shapes.py).
const SHAPE_KEYS := ["nose_size", "nose_long", "nose_wide", "nose_up", "ears_size", "ears_point", "ears_out", "lips_full",
	"mouth_wide", "mouth_smile", "jaw_wide", "chin_long", "cheeks", "brow_heavy", "eyes_pop", "muscle", "belly", "build", "rear", "female"]
## The shape keys clothing follows. bh-031: "female" is the body fitted from the player's female model
## (tools/blender/hero/hero_female.py); worn pieces carry it too.
const BODY_KEYS := ["muscle", "belly", "build", "rear", "female"]
## Colours: key -> default hex ("" = follow the hair colour).
const COLORS := {
	"skin": "b27e62", "pattern_color": "2a1c16", "underwear": "17171a", "hair_color": "2b1d14", "brow_color": "",
	"beard_color": "", "eye_color": "5b4a3a", "lip_color": "a8544e", "marking_color": "8c1410",
}
## Styles: key -> [[id, label], ...]; the first is the default. The order of "pattern", "eye", "brow" and "marking"
## is the shader's numbering (hero_skin.gdshader).
const CHOICES := {
	"pattern": [["none", "Plain"], ["stripes", "Stripes"], ["spots", "Spots"], ["scales", "Scales"], ["stone", "Cracked Stone"],
		["chequers", "Chequers"], ["halves", "Two Halves"], ["stars", "Starlight"], ["molten", "Molten"], ["metal", "Cast Metal"],
		["camo", "Mottled"], ["spectral", "Spectral"]],
	"eye": [["natural", "Natural"], ["round", "Round"], ["keen", "Keen"], ["sleepy", "Sleepy"], ["fierce", "Fierce"],
		["doe", "Doe"], ["cat", "Cat"], ["dots", "Dots"], ["glowing", "Glowing"], ["closed", "Smiling Shut"]],
	"brow": [["natural", "Natural"], ["straight", "Straight"], ["arched", "Arched"], ["bushy", "Bushy"], ["thin", "Thin"],
		["single", "Single Brow"], ["none", "None"]],
	"marking": [["none", "None"], ["band", "Eye Band"], ["stripes", "Cheek Stripes"], ["rosy", "Rosy Cheeks"],
		["freckles", "Freckles"], ["painted", "Painted Nose"], ["rites", "Rite Marks"], ["scar", "Scar"]],
	"hair": [["shaved", "Shaved"], ["bald", "Bald"], ["crop", "Crop"], ["sidepart", "Side Part"], ["slick", "Slicked Back"],
		["spiky", "Spiky"], ["mohawk", "Crest"], ["long", "Long"], ["ponytail", "Ponytail"], ["topknot", "Topknot"],
		["braids", "Braids"], ["pigtails", "Pigtails"], ["curly", "Curls"], ["bowl", "Bowl Cut"], ["tonsure", "Tonsure"],
		["wild", "Wild Mane"]],
	"beard": [["none", "None"], ["moustache", "Moustache"], ["handlebar", "Handlebar"], ["goatee", "Goatee"], ["full", "Full Beard"],
		["long", "Long Beard"], ["chops", "Chops"], ["braided", "Braided Beard"]],
}
## Hair and beard styles that are a model (the others are only the scalp / stubble tint).
const HAIR_MODEL := "res://assets/characters/hero/hair/%s.glb"
const BEARD_MODEL := "res://assets/characters/hero/beard/%s.glb"
const FLAGS := {"show_helm": true}

## Swatches the creator offers (any colour can also be mixed by hand).
const SKIN_TONES := ["f3d3bd", "e8bfa2", "d9a585", "c8916d", "b27e62", "9b6a4f", "80523a", "643d2a", "4a2c1f", "331d15",
	"8fae6a", "5f8f4e", "7b8fb8", "a57bb8", "c9c9cf", "b5523f"]
const HAIR_TONES := ["0f0c0b", "2b1d14", "4a2f1d", "6b4423", "8c5a2b", "b07a3a", "d4a853", "e8d28a", "8c2f1a", "c0491f",
	"8a8a8e", "e6e6e8", "3a5fa8", "7a3fa0", "2f8f5a", "d14a8a"]
const EYE_TONES := ["5b4a3a", "3a2a1c", "7a5a2c", "5a7a3a", "3a7a6a", "3f6fa8", "6f8fb8", "8a8f98", "7a4aa8", "c02a2a",
	"e0a020", "20c0d0"]
const LIP_TONES := ["a8544e", "c2605a", "8c3a3a", "d07a70", "7a2a3a", "b0306a", "402030", "2a6a8a"]
const MARK_TONES := ["8c1410", "14100e", "e8e4da", "2f4f8c", "2f6f3a", "c89a2a", "6a2a8a", "d14a2a"]
const CLOTH_TONES := ["17171a", "e8e2d2", "7a1a1a", "1f3f7a", "2f5f2a", "c89a2a", "5a2a7a", "d14a8a"]

static func _default_for(key: String) -> Variant:
	if SLIDERS.has(key):
		return SLIDERS[key][0]
	if COLORS.has(key):
		return COLORS[key]
	if CHOICES.has(key):
		return CHOICES[key][0][0]
	return FLAGS.get(key)

## The plain hero, every key present.
static func defaults() -> Dictionary:
	var d := {"v": VERSION}
	for k in SLIDERS:
		d[k] = SLIDERS[k][0]
	for k in COLORS:
		d[k] = COLORS[k]
	for k in CHOICES:
		d[k] = CHOICES[k][0][0]
	for k in FLAGS:
		d[k] = FLAGS[k]
	return d

static func choice_ids(key: String) -> Array:
	return (CHOICES[key] as Array).map(func(c): return c[0])

static func choice_index(key: String, id: String) -> int:
	var ids := choice_ids(key)
	return maxi(0, ids.find(id))

static func choice_label(key: String, id: String) -> String:
	for c in CHOICES[key]:
		if c[0] == id:
			return c[1]
	return id

static func _hex_ok(s: String) -> bool:
	return s.length() == 6 and s.is_valid_hex_number()

## A complete, in-range look from whatever was stored or received (unknown keys dropped, bad values replaced).
static func sanitize(src: Variant) -> Dictionary:
	var d := defaults()
	if not (src is Dictionary):
		return d
	for k in SLIDERS:
		var v = src.get(k)
		if v is float or v is int:
			var f := float(v)
			if is_finite(f):
				d[k] = clampf(f, SLIDERS[k][1], SLIDERS[k][2])
	for k in COLORS:
		var v = src.get(k)
		if v is String and (_hex_ok(v) or (v == "" and COLORS[k] == "")):
			d[k] = (v as String).to_lower()
	for k in CHOICES:
		var v = src.get(k)
		if v is String and choice_ids(k).has(v):
			d[k] = v
	for k in FLAGS:
		var v = src.get(k)
		if v is bool:
			d[k] = v
	return d

## Whether a look is the plain hero (nothing worth storing or sending).
static func is_plain(look: Dictionary) -> bool:
	if look.is_empty():
		return true
	var d := defaults()
	for k in d:
		if k != "v" and look.has(k) and look[k] != d[k]:
			return false
	return true

## What the save file keeps: only what differs from the plain hero.
static func to_save(look: Dictionary) -> Dictionary:
	var out := {}
	var d := defaults()
	for k in d:
		if k != "v" and look.has(k) and look[k] != d[k]:
			out[k] = look[k]
	if not out.is_empty():
		out["v"] = VERSION
	return out

static func color(look: Dictionary, key: String) -> Color:
	var s := String(look.get(key, COLORS.get(key, "")))
	if s == "":
		s = String(look.get("hair_color", COLORS["hair_color"]))
	return Color.html(s)

## The colour as the sRGB triplet the hero shaders expect.
static func rgb(look: Dictionary, key: String) -> Vector3:
	var c := color(look, key)
	return Vector3(c.r, c.g, c.b)

static func hair_model(look: Dictionary) -> String:
	var p := HAIR_MODEL % String(look.get("hair", "shaved"))
	return p if ResourceLoader.exists(p) else ""

static func beard_model(look: Dictionary) -> String:
	var p := BEARD_MODEL % String(look.get("beard", "none"))
	return p if ResourceLoader.exists(p) else ""

## How strongly the scalp is tinted with the hair colour: a shaved head shows stubble, a bald one none, and under a
## modelled style the scalp is dark so no skin shines through the locks.
static func scalp_shade(look: Dictionary) -> float:
	match String(look.get("hair", "shaved")):
		"bald": return 0.0
		"shaved": return 0.5
		"tonsure", "mohawk", "topknot": return 0.3
		_: return 0.8

# ---- Random looks and presets -----------------------------------------------------------------------------------

static func _pick(rng: RandomNumberGenerator, list: Array) -> Variant:
	return list[rng.randi_range(0, list.size() - 1)]

## A random look. `silly` 0 = a believable person, 1 = anything goes.
static func random(rng: RandomNumberGenerator, silly := 0.0) -> Dictionary:
	var d := defaults()
	var natural := silly < 0.5
	var woman := rng.randf() < 0.5
	d["skin"] = _pick(rng, SKIN_TONES.slice(0, 10) if natural else SKIN_TONES)
	d["hair_color"] = _pick(rng, HAIR_TONES.slice(0, 12) if natural else HAIR_TONES)
	d["eye_color"] = _pick(rng, EYE_TONES.slice(0, 8) if natural else EYE_TONES)
	d["hair"] = _pick(rng, choice_ids("hair"))
	d["beard"] = _pick(rng, choice_ids("beard")) if rng.randf() < 0.45 else "none"
	d["stubble"] = rng.randf_range(0.0, 0.8) if rng.randf() < 0.5 else 0.0
	d["eye"] = _pick(rng, choice_ids("eye").slice(0, 7) if natural else choice_ids("eye"))
	d["brow"] = _pick(rng, choice_ids("brow").slice(0, 5) if natural else choice_ids("brow"))
	if rng.randf() < 0.2 + 0.4 * silly:
		d["marking"] = _pick(rng, choice_ids("marking"))
		d["marking_color"] = _pick(rng, MARK_TONES)
	if rng.randf() < silly * 0.6:
		d["pattern"] = _pick(rng, choice_ids("pattern"))
		d["pattern_color"] = _pick(rng, HAIR_TONES + MARK_TONES)
	for k in SLIDERS:
		if k in ["stubble", "pattern_amount", "pattern_scale", "eye_glow", "lip_amount", "female"]:
			continue
		var s: Array = SLIDERS[k]
		# a bell around the default; the wider the sillier
		var spread := lerpf(0.10, 0.42, silly)
		var u := (rng.randf() + rng.randf() + rng.randf()) / 3.0 * 2.0 - 1.0
		var span := (float(s[2]) - float(s[0])) if u > 0.0 else (float(s[0]) - float(s[1]))
		d[k] = clampf(float(s[0]) + u * span * spread * 2.2, s[1], s[2])
		if silly > 0.7 and rng.randf() < 0.12:
			d[k] = s[2] if rng.randf() < 0.75 else s[1]
	if natural:
		d["hair_length"] = clampf(float(d["hair_length"]), 0.0, 1.2)
		d["beard_length"] = clampf(float(d["beard_length"]), 0.0, 1.2)
	if woman:
		feminize(d, rng)
	return sanitize(d)

## bh-031: turn a look into a woman's: the female figure, no beard or stubble, finer brows, a little shorter and
## lighter-built, longer hair more often. Keeps everything else (colours, face sliders, markings).
static func feminize(d: Dictionary, rng: RandomNumberGenerator = null) -> Dictionary:
	d["female"] = 1.0
	d["beard"] = "none"
	d["stubble"] = 0.0
	if String(d.get("brow", "natural")) in ["bushy", "single"]:
		d["brow"] = "arched"
	d["brow_thick"] = minf(float(d.get("brow_thick", 1.0)), 0.85)
	d["height"] = float(d.get("height", 1.0)) * 0.95
	d["build"] = float(d.get("build", 0.0)) - 0.15
	d["muscle"] = float(d.get("muscle", 0.0)) - 0.2
	if rng != null and String(d.get("hair", "")) in ["shaved", "bald", "crop", "bowl", "tonsure", "spiky"] and rng.randf() < 0.8:
		d["hair"] = ["long", "ponytail", "braids", "topknot", "curly", "pigtails", "sidepart"][rng.randi_range(0, 6)]
	return d

## The creator's ready-made starting points: [id, label, look overrides].
const PRESETS := [
	["plain", "Plain", {}],
	["veteran", "Veteran", {"hair": "crop", "hair_color": "4a2f1d", "beard": "full", "stubble": 0.7, "marking": "scar",
		"marking_color": "8c5a50", "jaw_wide": 0.5, "brow_heavy": 0.6, "muscle": 0.6, "eye": "keen", "brow": "bushy"}],
	["scholar", "Scholar", {"hair": "sidepart", "hair_color": "8a8a8e", "beard": "goatee", "stubble": 0.0, "build": -0.5,
		"muscle": -0.5, "eye": "sleepy", "brow": "thin", "nose_long": 0.4, "chin_long": 0.3, "skin": "e8bfa2"}],
	["wanderer", "Wanderer", {"hair": "ponytail", "hair_color": "6b4423", "stubble": 0.35, "skin": "c8916d", "eye": "natural",
		"eye_color": "5a7a3a", "marking": "freckles", "marking_color": "80523a"}],
	["shade", "Shade", {"hair": "slick", "hair_color": "0f0c0b", "stubble": 0.0, "skin": "d9a585", "eye": "fierce",
		"eye_color": "8a8f98", "brow": "straight", "marking": "band", "marking_color": "14100e", "build": -0.3, "cheeks": -0.6}],
	["giant", "Hill Giant", {"hair": "wild", "hair_color": "8c2f1a", "beard": "braided", "beard_length": 1.2, "height": 1.18,
		"muscle": 1.4, "build": 1.0, "hands": 1.5, "feet": 1.4, "jaw_wide": 1.2, "brow_heavy": 1.4, "nose_size": 0.8,
		"brow": "bushy", "skin": "9b6a4f"}],
	["fey", "Moon Elf", {"hair": "long", "hair_color": "e6e6e8", "hair_length": 1.2, "stubble": 0.0, "skin": "c9c9cf",
		"eye": "doe", "eye_color": "7a4aa8", "eye_glow": 0.5, "ears_point": 2.2, "ears_size": 0.4, "brow": "arched",
		"build": -0.7, "muscle": -0.6, "chin_long": 0.3, "cheeks": -0.4, "height": 1.08}],
	["goblin", "Goblin King", {"hair": "mohawk", "hair_color": "2f8f5a", "hair_length": 1.0, "stubble": 0.0, "skin": "5f8f4e",
		"eye": "cat", "eye_color": "e0a020", "eye_size": 1.9, "ears_size": 2.0, "ears_point": 2.4, "ears_out": 1.6,
		"nose_long": 2.2, "nose_size": 0.8, "mouth_wide": 1.2, "mouth_smile": 1.4, "height": 0.84, "head": 1.45,
		"belly": 1.2, "hands": 1.5, "feet": 1.6, "brow": "single"}],
	["golem", "Stone Golem", {"hair": "bald", "stubble": 0.0, "pattern": "stone", "pattern_color": "1a1a1c", "skin": "8a8a8e",
		"eye": "glowing", "eye_color": "20c0d0", "brow": "none", "muscle": 1.5, "build": 1.4, "jaw_wide": 1.5,
		"brow_heavy": 2.0, "hands": 1.7, "height": 1.15}],
	["shieldmaiden", "Shieldmaiden", {"female": 1.0, "hair": "braids", "hair_color": "b07a3a", "hair_length": 0.8, "stubble": 0.0,
		"skin": "e8bfa2", "eye": "keen", "eye_color": "3f6fa8", "brow": "straight", "brow_thick": 0.8, "muscle": 0.5,
		"jaw_wide": 0.1, "height": 0.97, "marking": "freckles", "marking_color": "80523a"}],
	["huntress", "Huntress", {"female": 1.0, "hair": "ponytail", "hair_color": "2b1d14", "hair_length": 0.6, "stubble": 0.0,
		"skin": "9b6a4f", "eye": "cat", "eye_color": "5a7a3a", "brow": "arched", "brow_thick": 0.7, "build": -0.4,
		"height": 0.95, "lips_full": 0.4, "lip_amount": 0.3, "lip_color": "8c3a3a", "cheeks": -0.3}],
	["matron", "Matron", {"female": 1.0, "hair": "topknot", "hair_color": "8a8a8e", "stubble": 0.0, "skin": "d9a585",
		"eye": "sleepy", "eye_color": "5b4a3a", "brow": "thin", "belly": 0.6, "build": 0.4, "cheeks": 0.6, "height": 0.92,
		"mouth_smile": 0.6, "marking": "rosy", "marking_color": "c2605a"}],
	["jester", "Jester", {"hair": "pigtails", "hair_color": "d14a8a", "stubble": 0.0, "pattern": "halves", "pattern_color": "e8e2d2",
		"skin": "b5523f", "marking": "painted", "marking_color": "c02a2a", "eye": "round", "eye_size": 1.6, "mouth_smile": 1.8,
		"mouth_wide": 0.9, "nose_size": 1.4, "underwear": "c89a2a", "lip_amount": 0.8, "lip_color": "b0306a"}],
]

static func preset(id: String) -> Dictionary:
	for p in PRESETS:
		if p[0] == id:
			var d := defaults()
			d.merge(p[2], true)
			return sanitize(d)
	return defaults()

## A stable short signature (rebuild the model only when it changes).
static func signature(look: Dictionary) -> int:
	return hash(JSON.stringify(to_save(sanitize(look)), "", true))
