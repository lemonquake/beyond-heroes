class_name TempoGacha
## Tempo summoning (bh-012): Veyra Ashgrave burns Soul Embers to call a spirit — or ten — out of the Aether.
##
## * Stars: 3 (a nameless spirit of the hero's grade), 4 (a stronger nameless spirit: one grade higher, one more skill,
##   an honoured title), 5 (a renowned spirit). Base rates RATE_5 / RATE_4.
## * Pity: every tenth call without a 4-star or better is one; from call SOFT_PITY without a 5-star the 5-star chance
##   climbs by SOFT_STEP per call, and call HARD_PITY is always a 5-star. A ten-call always holds a 4-star or better.
## * The banner: one renowned spirit is featured each day; half of all 5-stars are the featured spirit (and a 5-star
##   that missed the feature guarantees it next time).
## * Duplicates: a renowned spirit called again raises its Resonance (up to MAX_RESONANCE): more of its hero's strength,
##   more HP and damage. Past the cap it turns into Soul Embers.
## * Summoned spirits wait in the Spirit Hall until bound (free); a bound spirit can swap places with one in the hall.
##   A hall spirit can be released for embers. Every hero gets WELCOME_EMBERS once (a free ten-call).

const COST_ONE := 10
const COST_TEN := 90
const RATE_5 := 0.016
const RATE_4 := 0.13
const SOFT_PITY := 50
const SOFT_STEP := 0.06
const HARD_PITY := 70
const FOUR_PITY := 10
const MAX_RESONANCE := 5
const RESONANCE_MIRROR := 0.02
const HALL_CAP := 40
const WELCOME_EMBERS := 100
const RELEASE_EMBERS := {3: 2, 4: 8, 5: 25}
const OVERFLOW_EMBERS := 40
const EMBER := &"soul_ember"
const STAR_COLORS := {3: Color(0.55, 0.85, 1.0), 4: Color(0.85, 0.6, 1.0), 5: Color(1.0, 0.78, 0.3)}
## Honoured titles a 4-star nameless spirit carries.
const EPITHETS := ["the Unyielding", "the Pale Blade", "Oathkeeper", "the Last Watch", "Stormborn", "the Grey Sentinel",
	"Emberheart", "the Lantern-bearer", "the Unburied", "Frostmantle", "the Far-seer", "Nightwalker"]

# ---- currency --------------------------------------------------------------------------------------------------------

static func embers(hero: HeroData) -> int:
	return hero.inventory.count_of(EMBER) if hero else 0

static func add_embers(hero: HeroData, n: int) -> void:
	if hero == null or n <= 0:
		return
	var it := DB.make_item(EMBER, BH.Rarity.COMMON, 1, n)
	it.count = n
	hero.inventory.add(it)
	hero.inventory.changed.emit()

static func state(hero: HeroData) -> Dictionary:
	if hero.summon.is_empty():
		hero.summon = {"calls": 0, "pity4": 0, "pity5": 0, "welcome": false, "lost_feature": false, "history": []}
	return hero.summon

## The one-time gift of Soul Embers (a first ten-call). True when it was given just now.
static func ensure_welcome(hero: HeroData) -> bool:
	if hero == null:
		return false
	var st := state(hero)
	if bool(st.get("welcome", false)):
		return false
	st["welcome"] = true
	add_embers(hero, WELCOME_EMBERS)
	return true

## Gold price of ten Soul Embers at the shrine (it grows with the hero).
static func ember_price(hero: HeroData) -> int:
	return 150 + 25 * (hero.progress.level if hero else 1)

static func buy_embers(hero: HeroData) -> String:
	var p := ember_price(hero)
	if hero.inventory.gold < p:
		return "Not enough gold (%d needed)" % p
	hero.inventory.gold -= p
	add_embers(hero, 10)
	return ""

# ---- the banner ------------------------------------------------------------------------------------------------------

## Today's featured renowned spirit (rotates daily through the summon pool of the hero's tier; bh-022: from level 25
## the Mythic, from 45 the Eternal). `level` -1 = the first tier.
static func featured(day := -1, level := -1) -> StringName:
	if day < 0:
		day = int(Time.get_unix_time_from_system() / 86400.0)
	var ids := DataTempos.summon_legend_ids(level)
	return ids[posmod(day, ids.size())]

# ---- calling ----------------------------------------------------------------------------------------------------------

static func call_error(hero: HeroData, n: int) -> String:
	if hero == null:
		return "No hero"
	var cost := COST_TEN if n >= 10 else COST_ONE * n
	if embers(hero) < cost:
		return "Not enough Soul Embers (%d needed, you have %d)" % [cost, embers(hero)]
	if hero.spirit_hall.size() + n > HALL_CAP + 10:
		return "The Spirit Hall is full. Release some spirits first."
	return ""

## The 5-star chance for the next call given the calls since the last 5-star.
static func rate_5(pity5: int) -> float:
	if pity5 + 1 >= HARD_PITY:
		return 1.0
	if pity5 + 1 > SOFT_PITY:
		return minf(1.0, RATE_5 + SOFT_STEP * float(pity5 + 1 - SOFT_PITY))
	return RATE_5

## Roll one call's stars and advance the pity counters in `st`.
static func roll_stars(st: Dictionary, rng: RandomNumberGenerator) -> int:
	var p5 := int(st.get("pity5", 0))
	var p4 := int(st.get("pity4", 0))
	var r := rng.randf()
	var stars := 3
	if r < rate_5(p5):
		stars = 5
	elif r < rate_5(p5) + RATE_4 or p4 + 1 >= FOUR_PITY:
		stars = 4
	st["pity5"] = 0 if stars == 5 else p5 + 1
	st["pity4"] = 0 if stars >= 4 else p4 + 1
	st["calls"] = int(st.get("calls", 0)) + 1
	return stars

## Call `n` spirits (1 or 10). Pays in embers and returns the results:
## [{tempo: TempoData, stars, new: bool, resonance: int, refund: int}]. Empty on error.
static func summon(hero: HeroData, n: int, rng: RandomNumberGenerator = null) -> Array:
	n = 10 if n >= 10 else maxi(1, n)
	if call_error(hero, n) != "":
		return []
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	hero.inventory.consume(EMBER, COST_TEN if n == 10 else COST_ONE * n)
	var st := state(hero)
	var out := []
	var best := 0
	for i in n:
		var stars := roll_stars(st, rng)
		if n == 10 and i == n - 1 and best < 4 and stars < 4:
			stars = 4        # a ten-call always holds a 4-star (pity counted the same way)
			st["pity4"] = 0
		best = maxi(best, stars)
		out.append(_resolve(hero, stars, rng, st))
	var hist: Array = st.get("history", [])
	for r in out:
		hist.push_front({"name": (r.tempo as TempoData).full_name(), "stars": r.stars})
	st["history"] = hist.slice(0, 30)
	hero.inventory.changed.emit()
	Events.tempo_changed.emit(0)
	return out

static func _resolve(hero: HeroData, stars: int, rng: RandomNumberGenerator, st: Dictionary) -> Dictionary:
	if stars == 5:
		var id := _pick_legend(st, rng, hero.progress.level)
		var have := owned_legend(hero, id)
		if have != null:
			if have.resonance < MAX_RESONANCE:
				have.resonance += 1
				return {"tempo": have, "stars": 5, "new": false, "resonance": have.resonance, "refund": 0}
			add_embers(hero, OVERFLOW_EMBERS)
			return {"tempo": have, "stars": 5, "new": false, "resonance": have.resonance, "refund": OVERFLOW_EMBERS}
		var t := TempoRules.legend_data(id)
		t.stars = 5
		t.price = 0
		_to_hall(hero, t)
		return {"tempo": t, "stars": 5, "new": true, "resonance": 0, "refund": 0}
	var grade := TempoRules.current_grade(hero) + (1 if stars == 4 else 0)
	grade = clampi(grade, 1, DataTempos.max_grade())
	var taken := (hero.tempos + hero.spirit_hall).map(func(x): return x.tempo_name)
	var t2 := TempoRules.generate(rng.randi(), hero.progress.level, &"", taken, grade)
	if stars == 4:
		# an honoured spirit: one more skill than its grade grants, and a title
		var pool := DataTempos.rollable_skills(t2.class_id, t2.grade).filter(func(s): return not t2.skills.has(s) and not DataTempos.is_heal(s))
		if not pool.is_empty():
			t2.skills.append(pool[rng.randi_range(0, pool.size() - 1)])
		t2.tempo_name = "%s %s" % [t2.tempo_name, EPITHETS[rng.randi_range(0, EPITHETS.size() - 1)]]
	t2.stars = stars
	t2.price = 0
	_to_hall(hero, t2)
	return {"tempo": t2, "stars": stars, "new": true, "resonance": 0, "refund": 0}

## Half of the 5-stars are the featured spirit; missing it guarantees the feature next time.
static func _pick_legend(st: Dictionary, rng: RandomNumberGenerator, level := -1) -> StringName:
	var feat := featured(-1, level)
	if bool(st.get("lost_feature", false)) or rng.randf() < 0.5:
		st["lost_feature"] = false
		return feat
	st["lost_feature"] = true
	var others := DataTempos.summon_legend_ids(level).filter(func(x): return x != feat)
	return others[rng.randi_range(0, others.size() - 1)]

static func _to_hall(hero: HeroData, t: TempoData) -> void:
	hero.tempo_serial += 1
	t.uid = hero.tempo_serial
	var kit: Array = DataTempos.legend(t.legend_id).get("kit", []) if t.is_legend() else TempoRules.starter_kit(t.class_id) + TempoRules.starter_offhand(t.class_id)
	for bid in kit:
		var it := DB.make_item(bid, BH.Rarity.BEGINNER, 1, hash("%s%d" % [bid, t.uid]))
		if it:
			t.equipment.equip(it, TempoRules.auto_slot(t, it), hero.progress.level, TempoRules.NO_ATTR)
	hero.spirit_hall.append(t)

## The hero's copy of a renowned spirit (bound or waiting in the hall), or null.
static func owned_legend(hero: HeroData, id: StringName) -> TempoData:
	for t in hero.tempos + hero.spirit_hall:
		if t.legend_id == id:
			return t
	return null

# ---- the Spirit Hall ------------------------------------------------------------------------------------------------

static func find_in_hall(hero: HeroData, uid: int) -> TempoData:
	for t in hero.spirit_hall:
		if t.uid == uid:
			return t
	return null

## Bind a hall spirit (free) when a place is open. "" or an error.
static func bind(hero: HeroData, uid: int) -> String:
	var t := find_in_hall(hero, uid)
	if t == null:
		return "That spirit is not in the hall"
	if TempoRules.bound_count(hero) >= DataTempos.MAX_ACTIVE:
		return "You can carry only %d Tempos. Swap one out instead." % DataTempos.MAX_ACTIVE
	hero.spirit_hall.erase(t)
	t.fallen = false
	t.hp_frac = 1.0
	t.mana_frac = 1.0
	hero.tempos.append(t)
	Events.tempo_changed.emit(t.uid)
	return ""

## A bound Tempo goes to rest in the hall and a hall spirit takes its place (both keep their gear).
static func swap(hero: HeroData, bound_uid: int, hall_uid: int) -> String:
	var b := TempoRules.find(hero, bound_uid)
	var h := find_in_hall(hero, hall_uid)
	if b == null or h == null:
		return "No such spirit"
	var i := hero.tempos.find(b)
	hero.tempos[i] = h
	hero.spirit_hall.erase(h)
	b.fallen = false
	b.hp_frac = 1.0
	hero.spirit_hall.append(b)
	h.fallen = false
	h.hp_frac = 1.0
	h.mana_frac = 1.0
	Events.tempo_changed.emit(h.uid)
	return ""

## A bound Tempo goes to rest in the hall (freeing a place).
static func rest(hero: HeroData, bound_uid: int) -> String:
	var b := TempoRules.find(hero, bound_uid)
	if b == null:
		return "No such Tempo"
	if hero.spirit_hall.size() >= HALL_CAP:
		return "The Spirit Hall is full"
	hero.tempos.erase(b)
	b.fallen = false
	b.hp_frac = 1.0
	hero.spirit_hall.append(b)
	Events.tempo_changed.emit(b.uid)
	return ""

## Let a hall spirit go for embers. Its gear returns to the bag (refused when the bag cannot hold it).
static func release(hero: HeroData, uid: int) -> int:
	var t := find_in_hall(hero, uid)
	if t == null:
		return -1
	var gear := t.equipment.equipped_items() + t.equipment.recovered_items
	if hero.inventory.free_cells() < gear.size():
		return -1
	hero._loading_equipment = true
	for s in BH.SLOTS:
		var it := t.equipment.get_item(s)
		if it != null:
			t.equipment.slots[s] = null
			if it.rarity > BH.Rarity.BEGINNER:
				hero.inventory.add(it)
	for it in t.equipment.recovered_items:
		hero.inventory.add(it)
	t.equipment.recovered_items.clear()
	hero.spirit_hall.erase(t)
	hero._loading_equipment = false
	var n: int = RELEASE_EMBERS.get(maxi(3, t.stars), 2) + (t.resonance * 10 if t.stars == 5 else 0)
	add_embers(hero, n)
	Events.tempo_changed.emit(0)
	return n

# ---- strength --------------------------------------------------------------------------------------------------------

## Resonance bonuses on top of the mirror share (TempoData.mirror adds RESONANCE_MIRROR per rank).
static func resonance_mods(t: TempoData) -> Array:
	var r := float(t.resonance)
	var src := "Resonance %s" % roman(t.resonance)
	return [StatModifier.inc(&"max_hp", 0.06 * r, src), StatModifier.more(&"outgoing_damage", 0.05 * r, src)]

static func roman(n: int) -> String:
	return ["", "I", "II", "III", "IV", "V"][clampi(n, 0, 5)]

## Card data for the reveal window.
static func card(r: Dictionary) -> Dictionary:
	var t: TempoData = r.tempo
	var stars := int(r.stars)
	var col: Color = STAR_COLORS.get(stars, Color.WHITE)
	var lines := ["%s · %s" % [t.class_name_text(), String(t.trait_def().get("name", ""))]]
	for s in t.skills:
		lines.append(String(DataTempos.skill(s).get("name", s)))
	var badge := "NEW" if r.new else ("Resonance %s" % roman(int(r.resonance)) if int(r.refund) == 0 else "+%d Soul Embers" % int(r.refund))
	return {"title": t.full_name(), "sub": t.grade_name() + (" spirit" if not t.is_legend() else " spirit — %s" % t.legend_def().get("pitch", "")),
		"lines": lines, "color": col, "stars": stars, "icon": DataTempos.class_icon(t.class_id), "rank": {3: 0, 4: 2, 5: 4}[stars],
		"badge": badge, "banner": "%s answers your call!" % t.tempo_name if stars == 5 else ""}
