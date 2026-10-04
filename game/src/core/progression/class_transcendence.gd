class_name ClassTranscendence
## Class Transcendence: the one progression service. A hero's saved `class` is their starting family and never
## changes; the advancement is `HeroData.transcendence_path` ([first transcendence, master], at most two steps), saved
## as the optional {"schema": 1, "path": [...]} field. Identity, granted content and theme are all derived from
## the path; nothing about them is stored or trusted from elsewhere.
##
## Eligibility is derived, never a stored currency:
##   eligible_steps  = min(2, floor(level / 60))
##   available_steps = max(0, eligible_steps - completed_steps)
## The level and the predecessor are checked again at the moment of advancing (`can_transcend`).
##
## Each advancement grants its three skills and three talents at rank 1 as free ranks (TreeState.floors): they are
## learned, never paid points, never refunded, and rebuilt from the path on every load, so a save, a respec, a failed
## upload or a repeated click can never grant them twice or lose them.

const SCHEMA := 1
const MAX_STEPS := 2
const STEP_LEVEL := 60

# ---- Identity -------------------------------------------------------------------------------------------------------

static func base_family(hero: HeroData) -> StringName:
	return hero.cls.id if hero != null and hero.cls != null else &""

static func completed_steps(hero: HeroData) -> int:
	return hero.transcendence_path.size() if hero != null else 0

static func eligible_steps_at(level: int) -> int:
	return clampi(level / STEP_LEVEL, 0, MAX_STEPS)

static func eligible_steps(hero: HeroData) -> int:
	return eligible_steps_at(hero.progress.level) if hero != null else 0

static func available_steps(hero: HeroData) -> int:
	return maxi(0, eligible_steps(hero) - completed_steps(hero))

## The hero's current class id: the last step of the path, or the starting family.
static func current_class_id(hero: HeroData) -> StringName:
	if hero == null or hero.cls == null:
		return &""
	return hero.transcendence_path.back() if not hero.transcendence_path.is_empty() else hero.cls.id

static func current_class_name(hero: HeroData) -> String:
	return DataTranscendence.name_of(current_class_id(hero))

## Display name of an identity id (Knight, Hunter, Royal Guard ...). Unknown ids read "Hero".
static func class_name_of(id: StringName) -> String:
	return DataTranscendence.name_of(id) if DataTranscendence.is_identity(id) else "Hero"

## [family, first transcendence, master] as far as the hero has advanced.
static func lineage(hero: HeroData) -> Array:
	if hero == null or hero.cls == null:
		return []
	var out: Array = [hero.cls.id]
	out.append_array(hero.transcendence_path)
	return out

## The identities the hero could advance into next (ignores level; see can_transcend).
static func valid_next_choices(hero: HeroData) -> Array:
	if hero == null or completed_steps(hero) >= MAX_STEPS:
		return []
	return DataTranscendence.children_of(current_class_id(hero))

## The level the next advancement needs (0 when both are complete).
static func next_level(hero: HeroData) -> int:
	var done := completed_steps(hero)
	return 0 if done >= MAX_STEPS else STEP_LEVEL * (done + 1)

## "" when `hero` may advance into `target` now; otherwise the reason, in plain words.
static func can_transcend(hero: HeroData, target: StringName) -> String:
	if hero == null or hero.cls == null:
		return "No hero"
	if not DataTranscendence.is_advanced(target):
		return "Unknown class"
	if DataTranscendence.family_of(target) != hero.cls.id:
		return "%s is not a %s class" % [DataTranscendence.name_of(target), DataTranscendence.name_of(hero.cls.id)]
	if hero.transcendence_path.has(target):
		return "Already a %s" % DataTranscendence.name_of(target)
	if completed_steps(hero) >= MAX_STEPS:
		return "Both advancements are complete"
	if DataTranscendence.parent_of(target) != current_class_id(hero):
		var parent := DataTranscendence.parent_of(target)
		return "Requires level %d and %s" % [DataTranscendence.level_for_stage(DataTranscendence.stage_of(target)), DataTranscendence.name_of(parent)]
	var need := DataTranscendence.level_for_stage(DataTranscendence.stage_of(target))
	if hero.progress.level < need:
		if DataTranscendence.stage_of(target) >= 2:
			return "Requires level %d and %s" % [need, DataTranscendence.name_of(DataTranscendence.parent_of(target))]
		return "Requires level %d" % need
	return ""

## Advance `hero` into `target`. Checks the hero's current state (never a cached window state), extends the path,
## rebuilds the trees and grants the six free ranks, places the new skills in empty bar slots only. Repeating the call
## after it succeeded fails ("Already a ..."): nothing is granted twice.
## Returns {ok, error, placed: [skill ids put on the bar], skills: [...], talents: [...]}.
static func transcend(hero: HeroData, target: StringName) -> Dictionary:
	var why := can_transcend(hero, target)
	if why != "":
		return {"ok": false, "error": why}
	hero.transcendence_path.append(target)
	hero.apply_identity()
	var d := DataTranscendence.info(target)
	var placed: Array = []
	for sid in d.get("skills", []):
		if hero.skill_bar.has(sid):
			continue
		var idx := hero.skill_bar.find(&"")
		if idx < 0:
			break
		hero.skill_bar[idx] = sid
		placed.append(sid)
	hero.progress.points_changed.emit()
	hero.skills_changed.emit()
	hero.stats_dirty.emit()
	return {"ok": true, "error": "", "placed": placed, "skills": (d.get("skills", []) as Array).duplicate(),
		"talents": (d.get("talents", []) as Array).duplicate()}

## The free ranks the hero's path has earned: {"skills": {node id: 1}, "talents": {node id: 1}}.
static func earned_rank_floors(hero: HeroData) -> Dictionary:
	return floors_for_path(hero.transcendence_path if hero != null else [])

static func floors_for_path(path: Array) -> Dictionary:
	var skills := {}
	var talents := {}
	for id in path:
		var d := DataTranscendence.info(StringName(id))
		for s in d.get("skills", []):
			skills[s] = 1
		for t in d.get("talents", []):
			talents[t] = 1
	return {"skills": skills, "talents": talents}

## Whether a skill belongs to the hero's family or to an identity on the hero's path. A sibling master's skill (or any
## other family's) is never allowed, whatever ranks a save or a forged request claims.
static func skill_allowed(hero: HeroData, skill_id: StringName) -> bool:
	if hero == null or hero.cls == null:
		return false
	var s := DB.skill(skill_id)
	if s == null:
		return false
	return identity_allows(lineage(hero), s.class_id)

## Content tagged with `owner_id` (a family or an identity) is usable by a hero of `line` (their lineage).
static func identity_allows(line: Array, owner_id: StringName) -> bool:
	if owner_id == &"":
		return true
	return line.has(owner_id)

# ---- Path validation --------------------------------------------------------------------------------------------------

## The longest valid prefix of `raw` for a hero of `family` at `level`: known identities only, each the child of the
## previous step, each at or below the hero's level, at most two steps. {"path": Array[StringName], "error": ""}.
## `error` explains what was dropped (empty when `raw` was already valid).
static func validate_path(family: StringName, level: int, raw: Variant) -> Dictionary:
	var out: Array[StringName] = []
	if raw == null:
		return {"path": out, "error": ""}
	if not raw is Array:
		return {"path": out, "error": "The class advancement record was not a list; the hero keeps the starting class."}
	var prev := family
	for v in raw:
		if out.size() >= MAX_STEPS:
			return {"path": out, "error": "More than two class advancements were recorded; only the first two are kept."}
		if not (v is String or v is StringName):
			return {"path": out, "error": "An unreadable class advancement was dropped."}
		var id := StringName(String(v))
		if not DataTranscendence.is_advanced(id):
			return {"path": out, "error": "Unknown class %s was dropped." % String(id)}
		if DataTranscendence.parent_of(id) != prev:
			return {"path": out, "error": "%s does not follow %s; it was dropped." % [DataTranscendence.name_of(id), DataTranscendence.name_of(prev)]}
		if level < DataTranscendence.level_for_stage(DataTranscendence.stage_of(id)):
			return {"path": out, "error": "%s needs level %d; it was dropped." % [DataTranscendence.name_of(id), DataTranscendence.level_for_stage(DataTranscendence.stage_of(id))]}
		out.append(id)
		prev = id
	return {"path": out, "error": ""}

## The optional save field of a hero: {"schema": 1, "path": [...]} ({} for a hero who has not advanced).
static func to_save(hero: HeroData) -> Dictionary:
	if hero == null or (hero.transcendence_path.is_empty() and hero.dormant_ranks.is_empty()):
		return {}
	var d := {"schema": SCHEMA, "path": hero.transcendence_path.map(func(x): return String(x))}
	if not hero.dormant_ranks.is_empty():
		d["dormant"] = hero.dormant_ranks.duplicate(true)
	return d

## Read the save field (absent = the starting class). Returns {"path", "error", "dormant"}.
static func from_save(family: StringName, level: int, raw: Variant) -> Dictionary:
	if raw == null or (raw is Dictionary and (raw as Dictionary).is_empty()):
		return {"path": [] as Array[StringName], "error": "", "dormant": {}}
	if not raw is Dictionary:
		return {"path": [] as Array[StringName], "error": "The class advancement record could not be read; the hero keeps the starting class.", "dormant": {}}
	var d: Dictionary = raw
	if int(d.get("schema", 0)) != SCHEMA:
		return {"path": [] as Array[StringName], "error": "Unknown class advancement format; the hero keeps the starting class.", "dormant": {}}
	var res := validate_path(family, level, d.get("path", []))
	var dormant: Dictionary = d.get("dormant", {}) if d.get("dormant", {}) is Dictionary else {}
	res["dormant"] = dormant
	return res

## Whether `newer` legitimately continues `older` (official saves): equal, or older plus one or two valid steps.
static func monotonic(older: Array, newer: Array) -> bool:
	if newer.size() < older.size():
		return false
	for i in older.size():
		if StringName(String(older[i])) != StringName(String(newer[i])):
			return false
	return true

# ---- Composed trees ---------------------------------------------------------------------------------------------------

static var _composed := {}

## The skill or talent tree of a family with the pages of every identity on `path` appended. Immutable and cached per
## (tree, path): heroes of the same identity share it, and no hero's advancement ever touches the shared base tree.
## `preview` adds the page of one more identity (Grand Master and locked previews) without granting anything.
static func compose_tree(base: TreeDef, path: Array, talents: bool) -> TreeDef:
	if base == null or path.is_empty():
		return base
	var key := "%s|%s" % [base.id, ",".join(path.map(func(x): return String(x)))]
	if _composed.has(key):
		return _composed[key]
	var t := TreeDef.new()
	t.id = base.id
	t.display_name = base.display_name
	t.points_kind = base.points_kind
	t.branches = base.branches.duplicate()
	var pages: Array = base.pages.duplicate(true)
	if pages.is_empty():
		pages = [{"name": "Talents" if talents else "Skills", "desc": base.display_name}]
	t.nodes = base.nodes.duplicate()        # the node dictionaries are shared read-only
	for id in path:
		var ident := StringName(String(id))
		var page := pages.size()
		pages.append(DataTranscendenceSkills.page_of(ident))
		var col: Color = DataTranscendence.info(ident).get("primary", Color.WHITE)
		t.branches.append({"name": DataTranscendence.name_of(ident), "x": 4.0, "color": col.lightened(0.2), "page": page})
		var nodes := DataTranscendenceSkills.talent_nodes(ident, page) if talents else DataTranscendenceSkills.skill_nodes(ident, page)
		t.nodes.append_array(nodes)
	t.pages = pages
	t.finalize_levels()
	_composed[key] = t
	return t

## The page index of an identity in a composed tree (-1 when it is not on it).
static func page_index(tree: TreeDef, identity: StringName) -> int:
	for i in tree.pages.size():
		if StringName(tree.pages[i].get("identity", &"")) == identity:
			return i
	return -1

# ---- Themes -----------------------------------------------------------------------------------------------------------

## {name, primary, accent, stage}: the class colours (labels, cards, skill pages).
static func class_theme(class_id: StringName) -> Dictionary:
	var d := DataTranscendence.info(class_id)
	if d.is_empty():
		return {"name": "Hero", "primary": UITheme.GOLD, "accent": UITheme.GOLD, "stage": 0}
	var stage := DataTranscendence.stage_of(class_id)
	return {"name": String(d.name), "primary": d.primary, "accent": d.accent, "stage": stage}

## The colour a class name is written in on a dark background (floating name plates, cards): readable, never the
## near-black Dark General charcoal itself. Base families keep the familiar gold.
static func label_color(class_id: StringName) -> Color:
	var stage := DataTranscendence.stage_of(class_id)
	if stage <= 0:
		return UITheme.GOLD
	var th := class_theme(class_id)
	var c: Color = th.primary
	if c.get_luminance() < 0.35:
		c = th.accent
	return c.lightened(0.15) if c.get_luminance() < 0.5 else c

## The current class id written in a saved hero dictionary (save cards, account cards): family + validated path.
static func class_of_save(h: Variant) -> StringName:
	if not h is Dictionary:
		return &""
	var fam := StringName(String((h as Dictionary).get("class", "")))
	if not DataTranscendence.is_family(fam):
		return fam
	var lvl := int(((h as Dictionary).get("progress", {}) as Dictionary).get("level", 1)) if (h as Dictionary).get("progress", {}) is Dictionary else 1
	var res := from_save(fam, lvl, (h as Dictionary).get("transcendence", null))
	return (res.path as Array).back() if not (res.path as Array).is_empty() else fam

# ---- Network identity -------------------------------------------------------------------------------------------------

## The compact identity another player sends: the path joined by commas ("" = the starting class).
static func path_text(hero: HeroData) -> String:
	return ",".join(hero.transcendence_path.map(func(x): return String(x))) if hero != null else ""

## A peer's claimed identity, checked against their family and level: the valid prefix of the path. Free text, colours
## or effects are never taken from a peer; the label and theme come from this registry.
static func peer_path(family: StringName, level: int, text: Variant) -> Array:
	if not text is String or (text as String).length() > 64:
		return []
	if (text as String) == "":
		return []
	return validate_path(family, level, Array((text as String).split(",", false))).path

static func peer_class_id(family: StringName, level: int, text: Variant) -> StringName:
	var p := peer_path(family, level, text)
	return p.back() if not p.is_empty() else family

# ---- Future Transcendent Dungeons -------------------------------------------------------------------------------------

## A reusable entry rule for content that asks for an advanced class: {"min_stage": 0..2, "families": [..] (empty = any),
## "classes": [exact ids], "lineages": [ids whose descendants also qualify]}. Unknown ids in the rule make it
## unsatisfiable (and are reported), never silently open. Returns "" when the hero qualifies, else the reason.
static func requirement_check(hero: HeroData, rule: Dictionary) -> String:
	if hero == null or hero.cls == null:
		return "No hero"
	return requirement_check_line(lineage(hero), rule)

static func requirement_check_line(line: Array, rule: Dictionary) -> String:
	if line.is_empty():
		return "No hero"
	var current: StringName = line.back()
	var family: StringName = line[0]
	for key in ["families", "classes", "lineages"]:
		for id in rule.get(key, []):
			if not DataTranscendence.is_identity(StringName(id)):
				return "This entry rule names an unknown class (%s)." % String(id)
	var min_stage := clampi(int(rule.get("min_stage", 0)), 0, MAX_STEPS)
	if line.size() - 1 < min_stage:
		return "Requires a %s class" % ("master" if min_stage >= 2 else "transcended")
	var fams: Array = rule.get("families", [])
	if not fams.is_empty() and not fams.map(func(x): return StringName(x)).has(family):
		return "For %s classes" % _join_names(fams)
	var classes: Array = rule.get("classes", [])
	var lineages: Array = rule.get("lineages", [])
	if not classes.is_empty() or not lineages.is_empty():
		var ok := classes.map(func(x): return StringName(x)).has(current)
		for l in lineages:
			if line.has(StringName(l)):
				ok = true
		if not ok:
			var names := _join_names(classes + lineages)
			return "For %s only" % names
	return ""

static func _join_names(ids: Array) -> String:
	var names: Array[String] = []
	for id in ids:
		names.append(DataTranscendence.name_of(StringName(id)))
	if names.size() <= 1:
		return "".join(names)
	return ", ".join(names.slice(0, names.size() - 1)) + " or " + names.back()
