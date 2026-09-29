class_name QuakeMate
extends RefCounted
## One member of the Quake Team (bh-017): an AI ally hero who follows the player, fights beside them, heals itself, and
## shops for itself in town (QuakeBrain). It is a whole hero of its own — HeroData with a class, level, attributes, gear,
## bag, gold and Tempos — plus the TempoData that gives the fighting AI (Tempo) its class skills and personality.
## Saved inside the owner's hero (`quake_team`), so a team survives quitting.

const CLASS_TEMPO := {&"knight": &"swordsman", &"mage": &"mystic", &"ranger": &"archer", &"shadowblade": &"thief"}
## Which class each new mate picks first: a healer, a tank, then the ranged and shadow classes.
const PICK_ORDER := [&"mage", &"knight", &"ranger", &"shadowblade"]
## Tempos a mate may bind (each costs the same gold as the player's would).
const MAX_TEMPOS := 1

var uid := 0
var hero: HeroData
var tdata: TempoData
## What the last shopping trip looked at, so the mate only goes again when something changed.
var shop_gold := -1
var shop_level := 0
var shop_map: StringName = &""

func display_name() -> String:
	return hero.hero_name if hero else "Ally"

func class_id() -> StringName:
	return hero.cls.id if hero else &"knight"

func level() -> int:
	return hero.progress.level if hero else 1

# ---- creation ------------------------------------------------------------------------------------------------------

## The class the next mate should be: never the owner's own, never one already on the team while another is free.
static func pick_class(owner: HeroData, taken: Array) -> StringName:
	for c in PICK_ORDER:
		if c != owner.cls.id and not taken.has(c):
			return c
	for c in PICK_ORDER:
		if not taken.has(c):
			return c
	return PICK_ORDER[taken.size() % PICK_ORDER.size()]

static func create(owner: HeroData, p_uid: int, cls_id: StringName, rng: RandomNumberGenerator) -> QuakeMate:
	var m := QuakeMate.new()
	m.uid = p_uid
	var taken: Array = [owner.hero_name]
	for o in owner.quake_team:
		taken.append((o as QuakeMate).display_name())
	m.hero = Game.new_hero(cls_id, NameForge.person(rng, taken))
	m.hero.difficulty = owner.difficulty
	# their Tempos get their own serial range so the player's and the mates' spirits never share a uid
	m.hero.tempo_serial = p_uid * 1000
	m.tdata = TempoData.new()
	m.tdata.uid = 500000 + p_uid
	m._build_tempo_data(rng)
	m.sync_with(owner)
	# they start on the same footing as a fresh hero of that level: a few draughts and a little gold
	m.hero.inventory.gold = 40 + 30 * m.level()
	var hp := DB.make_item(&"health_potion", BH.Rarity.COMMON, m.level(), rng.randi())
	hp.count = 2
	m.hero.inventory.add(hp)
	return m

func _build_tempo_data(rng: RandomNumberGenerator) -> void:
	var tcls: StringName = CLASS_TEMPO.get(class_id(), &"swordsman")
	tdata.class_id = tcls
	tdata.tempo_name = hero.hero_name
	tdata.tint = hero.cls.tint
	var traits := DataTempos.TRAITS.keys()
	traits.sort()
	tdata.trait_id = traits[rng.randi_range(0, traits.size() - 1)]
	tdata.grade = 1
	refresh_skills()

## The class skills a hero of this level knows: every non-unique skill up to the grade its level would call.
func refresh_skills() -> void:
	var g := 1
	for i in DataTempos.GRADES.size():
		if level() >= int(DataTempos.GRADES[i].level):
			g = i + 1
	var td := tdata.class_def()
	var out: Array = [td.signature]
	for s in td.skills:
		if s != td.signature and not DataTempos.is_unique(s) and DataTempos.skill_grade(s) <= g and not out.has(s):
			out.append(s)
	tdata.skills = out
	tdata.grade = g

# ---- keeping up with the owner ---------------------------------------------------------------------------------------

## Match the owner's level, guild tier and story flags (gear rules), spend the points a level brings, refresh skills.
## Returns true when the mate levelled up.
func sync_with(owner: HeroData) -> bool:
	var grew := false
	var target := clampi(owner.progress.level, 1, BH.LEVEL_CAP)
	if hero.progress.level < target:
		hero.progress.add_xp(XpCurve.total_xp_for_level(target) - hero.progress.total_xp)
		grew = true
	QuakeBrain.spend_points(hero)
	hero.guild = owner.guild
	hero.tier = owner.tier
	hero.equipment.tier_rank = owner.tier
	hero.world_flags = owner.world_flags.duplicate()
	hero.play_time = owner.play_time
	hero.clear_count = owner.clear_count
	hero.difficulty = owner.difficulty
	if grew:
		refresh_skills()
		hero.stats_dirty.emit()
	return grew

# ---- saving ---------------------------------------------------------------------------------------------------------

func to_dict() -> Dictionary:
	var td := tdata.to_dict()
	return {"uid": uid, "hero": hero.to_dict(), "tempo": td, "shop": [shop_gold, shop_level, String(shop_map)]}

static func from_dict(d: Dictionary) -> QuakeMate:
	var hd = d.get("hero")
	if not (hd is Dictionary) or not (hd as Dictionary).has("class"):
		return null
	var h := HeroData.from_dict(hd)
	if h == null:
		return null
	var m := QuakeMate.new()
	m.uid = int(d.get("uid", 1))
	m.hero = h
	m.tdata = TempoData.from_dict(d.get("tempo", {}))
	m.tdata.uid = 500000 + m.uid
	m.tdata.tempo_name = h.hero_name
	if not QuakeMate.CLASS_TEMPO.has(h.cls.id):
		return null
	m.tdata.class_id = QuakeMate.CLASS_TEMPO[h.cls.id]
	m.tdata.tint = h.cls.tint
	m.refresh_skills()
	var sh: Array = d.get("shop", [-1, 0, ""])
	if sh.size() >= 3:
		m.shop_gold = int(sh[0])
		m.shop_level = int(sh[1])
		m.shop_map = StringName(sh[2])
	return m
