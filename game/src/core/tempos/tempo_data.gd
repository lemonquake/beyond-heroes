class_name TempoData
extends RefCounted
## Persistent state of one Tempo (a bound spirit companion): who it was, what it can do, what it wears, and whether it
## has fallen. Pure model (no nodes); the Tempo actor reads it and writes its HP/mana back when a map unloads.

signal changed

var uid := 0
var tempo_name := "Tempo"
var class_id: StringName = &"swordsman"
var trait_id: StringName = &"valiant"
var skills: Array = []                 # skill ids (StringName), signature first
var origin := ""                       # how it died (flavour)
var tint := Color(0.4, 0.6, 0.75)
var price := 0                         # what the hero paid to bind it (revival scales with it)
var equipment := Equipment.new()      # ungated here; TempoRules applies the Tempo rarity ceiling
var fallen := false
var hp_frac := 1.0
var mana_frac := 1.0
var kills := 0
var grade := 1                         # spirit grade at binding (DataTempos.GRADES); renowned spirits ignore it
var legend_id: StringName = &""        # a renowned spirit (DataTempos.LEGENDS), else &""
var stars := 0                         # summoned at the shrine (bh-012): 3, 4 or 5 stars; 0 = bound the old way
var resonance := 0                     # duplicates called later strengthen it: 0..TempoGacha.MAX_RESONANCE

func _init() -> void:
	equipment.changed.connect(_on_equipment)

func _on_equipment() -> void:
	changed.emit()

func class_def() -> Dictionary:
	return DataTempos.tempo_class(class_id)

func trait_def() -> Dictionary:
	return DataTempos.trait_def(trait_id)

func class_name_text() -> String:
	return String(class_def().get("name", "Tempo"))

func is_legend() -> bool:
	return legend_id != &""

func legend_def() -> Dictionary:
	return DataTempos.legend(legend_id)

## Share of its hero's strength this spirit carries (grade 1: half; renowned: three quarters; Mythic and Eternal more).
func mirror() -> float:
	var base := float(renowned_def().mirror) if is_legend() else float(DataTempos.grade_def(grade).mirror)
	return base + TempoGacha.RESONANCE_MIRROR * float(resonance)

## bh-022: the renowned tier of this spirit (DataTempos.RENOWNED_TIERS: Renowned, Mythic, Eternal).
func renowned_def() -> Dictionary:
	return DataTempos.renowned_tier(DataTempos.legend_tier(legend_id))

func grade_name() -> String:
	return String(renowned_def().name) if is_legend() else String(DataTempos.grade_def(grade).name)

func grade_color() -> Color:
	return renowned_def().color if is_legend() else DataTempos.grade_def(grade).color

## "Hollan Greywall, the Unbroken" for renowned spirits, else the plain name.
func full_name() -> String:
	return "%s, %s" % [tempo_name, legend_def().title] if is_legend() else tempo_name

func has_heal() -> bool:
	for s in skills:
		if DataTempos.is_heal(s):
			return true
	return false

func to_dict() -> Dictionary:
	return {"uid": uid, "name": tempo_name, "class": String(class_id), "trait": String(trait_id),
		"skills": skills.map(func(s): return String(s)), "origin": origin, "tint": [tint.r, tint.g, tint.b], "price": price,
		"equipment": equipment.to_dict(), "fallen": fallen, "hp": hp_frac, "mana": mana_frac, "kills": kills,
		"grade": grade, "legend": String(legend_id), "stars": stars, "resonance": resonance}

static func from_dict(d: Dictionary) -> TempoData:
	var t := TempoData.new()
	t.uid = int(d.get("uid", 0))
	t.tempo_name = String(d.get("name", "Tempo"))
	var c := StringName(d.get("class", "swordsman"))
	t.class_id = c if DataTempos.CLASSES.has(c) else &"swordsman"
	var tr := StringName(d.get("trait", "valiant"))
	t.trait_id = tr if DataTempos.TRAITS.has(tr) else &"valiant"
	t.skills = []
	for s in d.get("skills", []):
		if DataTempos.SKILLS.has(StringName(s)):
			t.skills.append(StringName(s))
	if t.skills.is_empty():
		t.skills.append(t.class_def().signature)
	t.origin = String(d.get("origin", ""))
	var tc: Array = d.get("tint", [0.4, 0.6, 0.75])
	t.tint = Color(float(tc[0]), float(tc[1]), float(tc[2])) if tc.size() >= 3 else Color(0.4, 0.6, 0.75)
	t.price = int(d.get("price", 0))
	t.equipment.from_dict(d.get("equipment", {}))
	t.fallen = bool(d.get("fallen", false))
	t.hp_frac = clampf(float(d.get("hp", 1.0)), 0.0, 1.0)
	t.mana_frac = clampf(float(d.get("mana", 1.0)), 0.0, 1.0)
	t.kills = int(d.get("kills", 0))
	# absent in bh-004 saves: a grade-1 nameless spirit
	t.grade = clampi(int(d.get("grade", 1)), 1, DataTempos.max_grade())
	var lg := StringName(d.get("legend", ""))
	t.legend_id = lg if not DataTempos.legend(lg).is_empty() else &""
	t.stars = clampi(int(d.get("stars", 0)), 0, 5)
	t.resonance = clampi(int(d.get("resonance", 0)), 0, 5)
	return t
