class_name ClassRequirements
## Which classes may wear an equipment base: one rule system for every equip check, tooltip, shop, crafting and loot
## decision (Class Transcendence). A requirement is {"kind": ..., "ids": [...]}:
##
##   any           every hero class                                   "For any class"
##   family        a starting class and every class it advances into  "For Knight class" (+ "Includes Royal Guard, ...")
##   lineage       a named advancement and the classes after it       "For Royal Guard and its master classes"
##   exact         only that class                                    "For Grand Paladin only"
##   alternatives  a union of families / advancements, each with its  "For Hunter or Shadowblade classes"
##                 descendants
##
## Matching follows the registry (DataTranscendence ancestry), never name prefixes. An unknown id makes a requirement
## unsatisfiable (`validate` reports it), never silently open. The rule combines (AND) with level, attributes, slots and
## hands, rarity / guild rank and the story `wearers` list (DataSpecialWeapons). Unbound gear skips level and attributes
## as before but never the class rule.
##
## Existing bases (audit, docs/CLASS_TRANSCENDENCE.md): ordinary gear stays "any" (class_hint is only a loot and shop
## preference). Class set pieces (set bonuses written for one class) and uniques whose fixed power belongs to one class
## are that family's. The thirty-six transcendence pieces carry explicit lineage / exact rules.
##
## Tempos keep their own rules (TempoRules, `wearers`): family and "any" requirements do not bind them, and a lineage or
## exact piece (a transcendence piece) is not for Tempos unless the base says `tempo: true`.

const ANY := "any"
const FAMILY := "family"
const LINEAGE := "lineage"
const EXACT := "exact"
const ALTERNATIVES := "alternatives"
const KINDS := [ANY, FAMILY, LINEAGE, EXACT, ALTERNATIVES]

static var _cache := {}

## The requirement of a base: its explicit `class_req`, else the audited rule for existing gear.
static func of(base: ItemBaseDef) -> Dictionary:
	if base == null:
		return {"kind": ANY, "ids": []}
	if not base.class_req.is_empty():
		return base.class_req
	if _cache.has(base.id):
		return _cache[base.id]
	var r := derive(base)
	_cache[base.id] = r
	return r

## The audited rule for a base without an explicit requirement.
static func derive(base: ItemBaseDef) -> Dictionary:
	if not BH.CATEGORY_SLOTS.has(base.category):
		return {"kind": ANY, "ids": []}
	# a class set: its bonuses are written for one class
	if base.set_id != &"" and base.class_hint != &"" and base.category != &"accessory" and DataTranscendence.is_family(base.class_hint):
		return {"kind": FAMILY, "ids": [base.class_hint], "why": "class set"}
	# a unique whose fixed power belongs to one class
	for pid in base.fixed_powers:
		var pw := DB.power(StringName(pid))
		if pw != null and pw.class_hint != &"" and DataTranscendence.is_family(pw.class_hint):
			return {"kind": FAMILY, "ids": [pw.class_hint], "why": "class power"}
	return {"kind": ANY, "ids": []}

## "" when the rule is well formed (known kind, known ids of the right sort); otherwise what is wrong.
static func validate(req: Dictionary) -> String:
	var kind := String(req.get("kind", ANY))
	if not KINDS.has(kind):
		return "Unknown requirement kind %s" % kind
	var ids: Array = req.get("ids", [])
	if kind != ANY and ids.is_empty():
		return "A %s requirement names no class" % kind
	for id in ids:
		var sid := StringName(String(id))
		if not DataTranscendence.is_identity(sid):
			return "Unknown class %s" % String(id)
		if kind == FAMILY and not DataTranscendence.is_family(sid):
			return "%s is not a starting class" % DataTranscendence.name_of(sid)
	return ""

## Whether a hero of `line` (their lineage: [family, first transcendence, master]) meets `req`.
static func allows_line(req: Dictionary, line: Array) -> bool:
	if line.is_empty():
		return true                 # a bare equipment (previews, tools) is not class-gated
	var kind := String(req.get("kind", ANY))
	if kind == ANY:
		return true
	if validate(req) != "":
		return false
	var ids: Array = (req.get("ids", []) as Array).map(func(x): return StringName(String(x)))
	match kind:
		FAMILY:
			return ids.has(StringName(line[0]))
		LINEAGE, ALTERNATIVES:
			for id in ids:
				if line.has(id):
					return true
			return false
		EXACT:
			return ids.has(StringName(line.back()))
	return false

static func allows(base: ItemBaseDef, hero: HeroData) -> bool:
	return hero == null or allows_line(of(base), ClassTranscendence.lineage(hero))

## For one identity id (a preview or catalogue of "what could a Dark General wear").
static func allows_class(base: ItemBaseDef, class_id: StringName) -> bool:
	return allows_line(of(base), DataTranscendence.ancestry(class_id))

## "" when the hero's class may wear it, else the readable reason ("For Grand Paladin only").
static func check(base: ItemBaseDef, line: Array) -> String:
	if allows_line(of(base), line):
		return ""
	return text(base)

## Tempos: only explicit transcendence requirements bind them (they are never transcended), unless `tempo: true`.
static func tempo_allows(base: ItemBaseDef) -> bool:
	var req := of(base)
	var kind := String(req.get("kind", ANY))
	if kind == LINEAGE or kind == EXACT or kind == ALTERNATIVES:
		return bool(req.get("tempo", false))
	return true

## The requirement line every view shows: "For any class", "For Knight class", "For Grand Paladin only" ...
static func text(base: ItemBaseDef) -> String:
	return text_of(of(base))

static func text_of(req: Dictionary) -> String:
	var kind := String(req.get("kind", ANY))
	var ids: Array = (req.get("ids", []) as Array).map(func(x): return StringName(String(x)))
	if validate(req) != "":
		return "Class requirement unknown"
	match kind:
		FAMILY:
			return "For %s class%s" % [_names(ids), "es" if ids.size() > 1 else ""]
		LINEAGE:
			if ids.size() == 1 and DataTranscendence.stage_of(ids[0]) >= 2:
				return "For %s only" % DataTranscendence.name_of(ids[0])
			return "For %s and its master classes" % _names(ids) if ids.size() == 1 else "For %s and their master classes" % _names(ids)
		EXACT:
			return "For %s only" % _names(ids)
		ALTERNATIVES:
			return "For %s classes" % _names(ids)
	return "For any class"

## The second line where it helps: which classes a family or lineage includes.
static func detail(base: ItemBaseDef) -> String:
	var req := of(base)
	var kind := String(req.get("kind", ANY))
	var ids: Array = (req.get("ids", []) as Array).map(func(x): return StringName(String(x)))
	if validate(req) != "" or ids.is_empty():
		return ""
	var members: Array = []
	match kind:
		FAMILY:
			for f in ids:
				members.append_array(DataTranscendence.family_members(f).slice(1))
		LINEAGE, ALTERNATIVES:
			for id in ids:
				for c in DataTranscendence.children_of(id):
					members.append(c)
					members.append_array(DataTranscendence.children_of(c))
				if DataTranscendence.is_family(id):
					members.append_array(DataTranscendence.family_members(id).slice(1))
	if members.is_empty():
		return ""
	return "Includes %s" % _names(members, "and")

static func _names(ids: Array, joiner := "or") -> String:
	var names: Array[String] = []
	for id in ids:
		var n := DataTranscendence.name_of(StringName(id))
		if not names.has(n):
			names.append(n)
	if names.size() <= 1:
		return "".join(names)
	if names.size() == 2:
		return "%s %s %s" % [names[0], joiner, names[1]]
	return ", ".join(names.slice(0, names.size() - 1)) + ", %s %s" % [joiner, names.back()]

## [text, ok] lines for a hero (ok = they meet it); the detail line (ok = null) when the rule lists classes.
static func lines(base: ItemBaseDef, hero: HeroData) -> Array:
	var out := []
	var ok := allows(base, hero)
	out.append([text(base), ok])
	var d := detail(base)
	if d != "":
		out.append([d, null])
	return out

# ---- Audit manifest -------------------------------------------------------------------------------------------------

## Every equipment base with its requirement, readable text, level / drop band, story wearers and sources.
static func manifest() -> Array:
	var out := []
	var ids := DB.item_bases.keys()
	ids.sort()
	for id in ids:
		var b: ItemBaseDef = DB.item_bases[id]
		if not BH.CATEGORY_SLOTS.has(b.category):
			continue
		var req := of(b)
		var tempos := []
		for w in b.wearers:
			if DataTempos.CLASSES.has(StringName(w)):
				tempos.append(String(w))
		out.append({"id": String(id), "name": b.display_name, "category": String(b.category), "weapon_type": String(b.weapon_type),
			"kind": String(req.get("kind", ANY)), "ids": (req.get("ids", []) as Array).map(func(x): return String(x)),
			"why": String(req.get("why", "explicit" if not b.class_req.is_empty() else "shared")),
			"text": text(b), "detail": detail(b), "valid": validate(req) == "",
			"level": b.level_req, "drop_level": b.drop_level, "drop_weight": b.drop_weight, "class_hint": String(b.class_hint),
			"set": String(b.set_id), "unique": b.unique_name != "", "story": b.story, "boss_exclusive": b.boss_exclusive,
			"wearers": b.wearers.map(func(x): return String(x)), "tempo_wearers": tempos, "tempo_allowed": tempo_allows(b),
			"sources": DataTranscendenceGear.sources(b.id) if String(id).begins_with("tc_") else _sources(b)})
	return out

static func _sources(b: ItemBaseDef) -> Array:
	var out := []
	if b.story:
		out.append({"kind": "story", "id": "DataSpecialWeapons"})
		return out
	if b.boss_exclusive:
		out.append({"kind": "boss_set", "id": String(b.set_id)})
	elif b.set_id != &"":
		out.append({"kind": "set_drop", "id": String(b.set_id), "drop_level": b.drop_level})
	elif b.unique_name != "":
		out.append({"kind": "unique_drop", "drop_level": b.drop_level})
	elif b.drop_weight > 0:
		out.append({"kind": "loot", "id": "ItemGenerator.random_base", "drop_level": b.drop_level, "weight": b.drop_weight})
	if String(b.id).begins_with("artisan_"):
		out.append({"kind": "crafting", "id": "DataArtisanWeapons"})
	return out
