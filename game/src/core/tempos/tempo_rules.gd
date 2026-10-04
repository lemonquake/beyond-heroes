class_name TempoRules
## Rules for Tempos (spirit companions, docs/LORE.md §9). Pure functions over HeroData / TempoData — the Tempo-Caller's
## services, the Tempo window, the Tempo actor and the tests all call these.
##
## * Strength: a Tempo mirrors a share of its hero's persistent stats (50% at grade 1, up to 70% at grade 5, 75% for
##   the renowned spirits — DataTempos.GRADES) (pools, defense, accuracy, evasion, critical chance,
##   damage bonuses, resistances). Its own gear, class and trait add on top, and every "increased" / "more" modifier
##   then applies to the total — so a Tempo's gear always matters and it grows as its hero grows.
## * Gear: one rarity tier below the best its hero may wear (Unranked heroes' Tempos: up to Advanced), class weapons only,
##   the hero's level requirement; spirits ignore attribute requirements.
## * At most two Tempos bound at once (fallen ones count until they are called back or released).
## * Grades: the spirits answering the Tempo-Caller grow with the hero (level or story deeds): more skills, rarer
##   skills, new classes, a larger share of the hero's strength, higher prices. A rise replaces the offers at once.
## * Renowned spirits (DataTempos.LEGENDS): five named warriors with their own skills, a level requirement and a price
##   far above the nameless spirits. Each can be bound once; released, it returns to the shrine.
## * Every new hero starts with Tobren (DataTempos.STARTER), a grade-1 Swordsman, bound for free.

const MIRROR_KEYS: Array[StringName] = [&"max_hp", &"max_mana", &"hp_regen", &"mana_regen", &"defense", &"evasion",
	&"accuracy", &"crit_chance", &"status_res", &"knockback_res", &"poise", &"phys_damage", &"magic_damage",
	&"elemental_damage", &"healing", &"projectile_damage", &"damage", &"added_physical", &"physical_attack", &"spell_power"]
const NO_ATTR := {&"str": 9999, &"agi": 9999, &"int": 9999, &"wis": 9999, &"spi": 9999, &"dex": 9999}

static var _shells := {}

# ---- Stats ------------------------------------------------------------------------------------------------------

## Keys mirrored from the hero, including every resistance and elemental damage bonus.
static func mirror_keys() -> Array[StringName]:
	var out: Array[StringName] = MIRROR_KEYS.duplicate()
	for e in Elements.ELEMENTAL:
		out.append(Elements.res_key(e))
		out.append(Elements.dmg_key(e))
		out.append(StringName("added_" + String(Elements.key(e))))
	return out

## A class shell with no pools of its own: everything a Tempo has comes from its hero (mirrored) and its gear.
static func shell(class_id: StringName, hero_cls: ClassDef) -> ClassDef:
	var key := "%s/%s" % [class_id, hero_cls.id if hero_cls else &""]
	if _shells.has(key):
		return _shells[key]
	var c := ClassDef.new()
	var td := DataTempos.tempo_class(class_id)
	c.id = StringName("tempo_%s" % class_id)
	c.display_name = String(td.get("name", "Tempo"))
	c.base_hp = 0.0
	c.hp_per_level = 0.0
	c.level_up_hp = 0.0
	c.vitality = false
	c.base_mana = 0.0
	c.mana_per_level = 0.0
	c.base_defense = 0.0
	c.base_poise = 0.0
	c.base_knockback_res = 0.0
	c.base_move_speed = (hero_cls.base_move_speed if hero_cls else 5.0) * 1.05
	c.dodge_cooldown = float(td.get("dodge_cooldown", 2.0))
	c.weapon_mastery = {}
	for w in td.get("weapons", []):
		c.weapon_mastery[w] = 0.1
	_shells[key] = c
	return c

## The ghostly blade a Tempo fights with when its hands are empty: weaker than real steel, but never useless.
## A renowned spirit carries the weapon it died with (its `spirit` entry): stronger, and of its own element.
static func spirit_loadout(class_id: StringName, level: int, legend_id: StringName = &"") -> WeaponLoadout:
	var td := DataTempos.tempo_class(class_id)
	var sp: Dictionary = DataTempos.legend(legend_id).get("spirit", {})
	var wt := DB.weapon_type(sp.get("weapon", td.get("spirit_weapon", &"sword")))
	var power := float(sp.get("power", 1.0))
	var lo := WeaponLoadout.new()
	lo.main_type = wt
	lo.main_min = (3.0 + 0.9 * float(level)) * power * CombatGrowth.weapon_factor(level)
	lo.main_max = (6.0 + 1.5 * float(level)) * power * CombatGrowth.weapon_factor(level)
	lo.main_crit = wt.crit_chance if wt else 0.05
	lo.main_aps = wt.attacks_per_second if wt else WeaponLoadout.UNARMED_APS
	lo.main_element = int(sp.get("element", Elements.LIGHT))
	lo.main_elem_share = float(sp.get("share", 0.2))
	if wt != null and wt.id == &"dagger" and (td.get("sub", []) as Array).has(&"dagger"):
		lo.off_type = wt
		lo.off_min = lo.main_min * 0.9
		lo.off_max = lo.main_max * 0.9
		lo.off_aps = lo.main_aps
		lo.off_element = lo.main_element
		lo.off_elem_share = lo.main_elem_share
		lo.dual_wield = true
	return lo

## Weapon configuration the Tempo actually fights with.
static func loadout(t: TempoData, level: int) -> WeaponLoadout:
	var lo := t.equipment.loadout()
	return spirit_loadout(t.class_id, level, t.legend_id) if lo.is_unarmed() else lo

## Derived stats: the Tempo's share (TempoData.mirror) of `hero_stats` (the hero's persistent stats) + its gear, class,
## trait and — for a renowned spirit — its own strengths.
## `hero_stats` may be null (tools, previews): the Tempo then has only its own.
static func compute(t: TempoData, hero_stats: DerivedStats, level: int, hero_cls: ClassDef = null, runtime: Array = []) -> DerivedStats:
	var mods: Array = []
	var share := t.mirror()
	var who := "Soul-bond (%d%% of your hero)" % roundi(share * 100.0)
	if hero_stats != null:
		for k in mirror_keys():
			var v := hero_stats.get_stat(k) * share
			if absf(v) > 0.00001:
				mods.append(StatModifier.flat(k, v, who))
	mods.append_array(t.equipment.modifiers())
	mods.append_array(DataTempos.mods_from(t.class_def().get("mods", []), t.class_name_text()))
	mods.append_array(DataTempos.mods_from(t.trait_def().get("mods", []), String(t.trait_def().get("name", ""))))
	if t.is_legend():
		mods.append_array(DataTempos.mods_from(t.legend_def().get("mods", []), t.full_name()))
	if hero_stats != null and hero_stats.get_stat(&"tempo_damage") > 0.0:
		mods.append(StatModifier.more(&"outgoing_damage", hero_stats.get_stat(&"tempo_damage"), "Your Soulbound gear"))
	if t.resonance > 0:
		mods.append_array(TempoGacha.resonance_mods(t))
	mods.append_array(runtime)
	var d := StatCalculator.compute(shell(t.class_id, hero_cls), level, {}, mods, loadout(t, level))
	if hero_stats != null:
		# attributes shown on the sheet: the mirrored half plus what the Tempo's own gear adds
		for a in BH.ATTRIBUTES:
			var mirrored := floorf(hero_stats.get_stat(a) * share)
			var lines := PackedStringArray(["Mirrored from your hero (%d%%): %d" % [roundi(share * 100.0), mirrored]])
			if d.get_stat(a) > 0.0:
				lines.append("Tempo gear: +%d" % d.get_stat(a))
			d.set_stat(a, mirrored + d.get_stat(a), lines)
		# a Tempo always keeps pace with its hero
		var hms := hero_stats.get_stat(&"move_speed", 5.0) * 1.05
		if d.get_stat(&"move_speed") < hms:
			d.set_stat(&"move_speed", hms, PackedStringArray(["Keeps pace with your hero: %.2f m/s" % hms]))
	return d

## Persistent hero stats (no temporary buffs), the base a Tempo mirrors.
static func hero_mirror(hero: HeroData) -> DerivedStats:
	return hero.compute_stats([]) if hero else null

# ---- Gear -------------------------------------------------------------------------------------------------------

## Highest rarity the hero may wear (tier gating, docs/LORE.md §5).
static func hero_rarity_cap(hero: HeroData) -> int:
	var best := 0
	for r in BH.RARITY_COUNT:
		if DataGuilds.rank_for_rarity(r) <= hero.tier:
			best = r
	return best

## Highest rarity a Tempo of this hero may wear: one tier below the hero's.
static func rarity_cap(hero: HeroData) -> int:
	return maxi(0, hero_rarity_cap(hero) - 1)

static func rarity_allowed(hero: HeroData, rarity: int) -> bool:
	return rarity <= rarity_cap(hero) and DataGuilds.rank_for_rarity(rarity) <= hero.tier

## Highest rarity actually wearable (skips tiers the hero's registration does not cover, e.g. Licensed when Unranked).
static func best_wearable_rarity(hero: HeroData) -> int:
	for r in range(rarity_cap(hero), -1, -1):
		if rarity_allowed(hero, r):
			return r
	return 0

## Why `item` cannot go into `slot` on Tempo `t` ("" = it can).
static func equip_error(hero: HeroData, t: TempoData, item: ItemInstance, slot: StringName = &"") -> String:
	if item == null or not item.is_equipment():
		return "Cannot be equipped"
	if slot == &"":
		slot = auto_slot(t, item)
	if slot == &"":
		return "Cannot be equipped"
	var allowed: Array = BH.CATEGORY_SLOTS.get(item.base.category, [])
	if not allowed.has(slot):
		return "Does not fit in %s" % BH.SLOT_NAMES[slot]
	if not DataSpecialWeapons.can_wear(item.base, t.class_id):
		return DataSpecialWeapons.wearers_text(item.base)
	if not ClassRequirements.tempo_allows(item.base):
		return "%s; not for Tempos" % ClassRequirements.text(item.base)
	if not item.unbound and hero.progress.level < item.required_level():
		return "Requires level %d" % item.required_level()
	if item.unbound:
		# bh-026: Unbound gear skips the Tempo rarity ceiling as it skips the hero's; Class E is all it asks
		if hero.tier < DataSpecialWeapons.UNBOUND_RANK:
			return "Requires a Class %s hero (Unbound gear)" % DataGuilds.letter(DataSpecialWeapons.UNBOUND_RANK)
	elif not rarity_allowed(hero, item.rarity):
		return "Tempos may wear %s gear at most (one tier below yours)" % BH.rarity_name(best_wearable_rarity(hero))
	var td := t.class_def()
	if slot == &"main_weapon":
		if not item.base.is_weapon() or not (td.weapons as Array).has(item.base.weapon_type):
			return "A %s cannot wield that" % td.name
	elif slot == &"sub_weapon":
		var sub: Array = td.get("sub", [])
		if item.base.category == &"shield":
			if not sub.has(&"shield"):
				return "A %s fights without a shield" % td.name
		elif not item.base.is_weapon() or not sub.has(item.base.weapon_type):
			return "A %s cannot hold that in the off hand" % td.name
	return t.equipment.check(item, slot, hero.progress.level, NO_ATTR)

static func auto_slot(t: TempoData, item: ItemInstance) -> StringName:
	if item == null or not item.is_equipment():
		return &""
	if item.base.category == &"shield":
		return &"sub_weapon"
	if item.base.is_weapon():
		if not item.base.equipment_slots().has(&"sub_weapon"):
			return &"main_weapon"
		var td := t.class_def()
		var main := t.equipment.get_item(&"main_weapon")
		if main != null and t.equipment.get_item(&"sub_weapon") == null and (td.get("sub", []) as Array).has(item.base.weapon_type):
			var wt := DB.weapon_type(item.base.weapon_type)
			var mt := DB.weapon_type(main.base.weapon_type)
			if wt and mt and wt.dual_wieldable and mt.dual_wieldable:
				return &"sub_weapon"
		return &"main_weapon"
	return t.equipment.auto_slot(item)

## Move an item from the hero's bag onto the Tempo. Displaced pieces go back to the bag. "" or an error.
static func equip_from_inventory(hero: HeroData, t: TempoData, item: ItemInstance, slot: StringName = &"") -> String:
	if slot == &"":
		slot = auto_slot(t, item)
	var err := equip_error(hero, t, item, slot)
	if err != "":
		return err
	var idx := hero.inventory.index_of(item)
	if idx < 0:
		return "That item is not in your bag"
	var needed := 1 if t.equipment.get_item(slot) != null else 0
	if slot == &"main_weapon":
		var wt := t.equipment.weapon_type_of(item)
		var sub := t.equipment.get_item(&"sub_weapon")
		if sub != null and wt != null and (wt.two_handed or (sub.base.is_weapon() and not wt.dual_wieldable)):
			needed += 1
	if needed > hero.inventory.free_cells() + (1 if idx < hero.inventory.bag_capacity else 0):
		return "Gear Bag needs room for the replaced equipment"
	hero._loading_equipment = true
	hero.inventory.cells[idx] = null
	var res := t.equipment.equip(item, slot, hero.progress.level, NO_ATTR)
	for d in res.displaced:
		if hero.inventory.cells[idx] == null:
			hero.inventory.cells[idx] = d
		else:
			hero.inventory.add(d)
	hero._loading_equipment = false
	hero.inventory.changed.emit()
	Events.tempo_changed.emit(t.uid)
	return ""

## Take an item off the Tempo and put it in the hero's bag.
static func unequip_to_inventory(hero: HeroData, t: TempoData, slot: StringName) -> String:
	var it := t.equipment.get_item(slot)
	if it == null:
		return ""
	var needed := 1
	var sub := t.equipment.get_item(&"sub_weapon")
	if slot == &"main_weapon" and sub != null and sub.base.is_weapon():
		needed = 2
	if hero.inventory.free_cells() < needed:
		return "Your bag is full"
	hero._loading_equipment = true
	t.equipment.unequip(slot)
	hero.inventory.add(it)
	var orphan := t.equipment.orphaned_sub()
	if orphan != null:
		t.equipment.unequip(&"sub_weapon")
		hero.inventory.add(orphan)
	hero._loading_equipment = false
	hero.inventory.changed.emit()
	Events.tempo_changed.emit(t.uid)
	return ""

# ---- Binding, calling back, releasing ------------------------------------------------------------------------------

## Price of a nameless spirit: grows with the hero's level, its number of skills, a mend, and its grade.
## Renowned spirits have a fixed price (DataTempos.LEGENDS).
static func hire_cost(t: TempoData, level: int) -> int:
	if t.is_legend():
		return int(t.legend_def().price)
	var c := (80.0 + 30.0 * float(maxi(1, level) - 1)) * (1.0 + 0.2 * float(maxi(0, t.skills.size() - 2)))
	if t.has_heal():
		c *= 1.15
	c *= float(DataTempos.grade_def(t.grade).price)
	return int(snappedf(c, 5.0))

static func revive_cost(t: TempoData, hero: HeroData) -> int:
	return int(snappedf(25.0 + 12.0 * float(hero.progress.level) + float(t.price) * 0.2, 5.0))

static func bound_count(hero: HeroData) -> int:
	return hero.tempos.size()

static func active(hero: HeroData) -> Array:
	return hero.tempos.filter(func(t): return not t.fallen) if hero else []

static func has_fallen(hero: HeroData) -> bool:
	for t in hero.tempos:
		if t.fallen:
			return true
	return false

static func find(hero: HeroData, uid: int) -> TempoData:
	for t in hero.tempos:
		if t.uid == uid:
			return t
	return null

# ---- Grades -------------------------------------------------------------------------------------------------------

## Whether the hero has reached spirit grade `g` (its level, or its deed when the grade has one).
static func grade_reached(hero: HeroData, g: int) -> bool:
	if hero == null:
		return g <= 1
	var gd := DataTempos.grade_def(g)
	if hero.progress.level >= int(gd.level):
		return true
	return gd.flag != &"" and bool(hero.world_flags.get(gd.flag, false))

## The grade of the spirits answering the Tempo-Caller for this hero right now.
static func current_grade(hero: HeroData) -> int:
	var best := 1
	for g in range(2, DataTempos.max_grade() + 1):
		if grade_reached(hero, g):
			best = g
	return best

## What unlocks the next grade: {"grade": n, "name", "text"} or {} at the top.
static func next_grade(hero: HeroData) -> Dictionary:
	var g := current_grade(hero) + 1
	if g > DataTempos.max_grade():
		return {}
	var gd := DataTempos.grade_def(g)
	var how := "reach level %d" % int(gd.level)
	if String(gd.deed) != "":
		how += " or %s" % gd.deed
	return {"grade": g, "name": String(gd.name), "text": how}

## Call when the hero levels up or a deed is done: if the spirits' grade rose, the old offers fade and stronger
## spirits answer at once. Returns the new grade, or 0 when nothing changed.
static func check_grade(hero: HeroData) -> int:
	if hero == null:
		return 0
	var g := current_grade(hero)
	if g <= int(hero.tempo_roster.get("grade", 1)):
		return 0
	refresh_roster(hero)
	return g

## Spirits answering the Tempo-Caller right now (refreshed on a play-time clock, after each binding, and whenever
## the hero reaches a new grade).
static func roster(hero: HeroData) -> Array:
	var r: Dictionary = hero.tempo_roster
	var stale := (r.get("offers", []) as Array).is_empty() or hero.play_time >= float(r.get("refresh_at", 0.0))
	if stale or int(r.get("grade", 1)) < current_grade(hero):
		refresh_roster(hero)
	var out := []
	for d in hero.tempo_roster.offers:
		out.append(TempoData.from_dict(d))
	return out

static func refresh_roster(hero: HeroData) -> void:
	var serial := int(hero.tempo_roster.get("serial", 0))
	var grade := current_grade(hero)
	var offers := []
	var taken := hero.tempos.map(func(t): return t.tempo_name)
	var classes := DataTempos.classes_for_grade(grade)
	# more classes than places: rotate so every class answers over a few refreshes, the newest first
	if classes.size() > DataTempos.ROSTER_SIZE:
		classes.reverse()
		var shift := (serial / DataTempos.ROSTER_SIZE) % classes.size()
		classes = classes.slice(shift) + classes.slice(0, shift)
	for i in DataTempos.ROSTER_SIZE:
		serial += 1
		var cls: StringName = classes[i] if i < classes.size() else &""
		var t := generate(hash("%s/%d" % [hero.hero_name, serial]), hero.progress.level, cls, taken, grade)
		taken.append(t.tempo_name)
		offers.append(t.to_dict())
	hero.tempo_roster = {"offers": offers, "refresh_at": hero.play_time + DataTempos.ROSTER_REFRESH, "serial": serial,
		"grade": grade}

## A random spirit of `grade` (deterministic for a seed): class, name, personality, skills (the class signature first,
## then as many as the grade grants, drawn from the skills that grade may know), where it fell, a spectral tint and
## its price.
static func generate(seed_value: int, level: int, class_id: StringName = &"", taken: Array = [], grade := 1) -> TempoData:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var t := TempoData.new()
	t.grade = clampi(grade, 1, DataTempos.max_grade())
	var classes := DataTempos.classes_for_grade(t.grade)
	t.class_id = class_id if DataTempos.CLASSES.has(class_id) else classes[rng.randi_range(0, classes.size() - 1)]
	t.tempo_name = NameForge.person(rng, taken)   # bh-015: prefix + middle + suffix, never a fixed list
	var traits := DataTempos.TRAITS.keys()
	traits.sort()
	t.trait_id = traits[rng.randi_range(0, traits.size() - 1)]
	var td := t.class_def()
	t.skills = [td.signature]
	var pool := DataTempos.rollable_skills(t.class_id, t.grade)
	var span: Array = DataTempos.grade_def(t.grade).extra
	var extra := (2 if rng.randf() < 0.45 else 1) if t.grade == 1 else rng.randi_range(int(span[0]), int(span[1]))
	for i in mini(extra, pool.size()):
		if pool.is_empty():
			break
		var s: StringName = pool[rng.randi_range(0, pool.size() - 1)]
		pool.erase(s)
		t.skills.append(s)
		# a spirit knows one mend at most
		if DataTempos.is_heal(s):
			pool = pool.filter(func(x): return not DataTempos.is_heal(x))
	t.origin = DataTempos.ORIGINS[rng.randi_range(0, DataTempos.ORIGINS.size() - 1)]
	var base: Color = td.tint
	t.tint = Color.from_hsv(fposmod(base.h + rng.randf_range(-0.05, 0.05), 1.0), clampf(base.s * rng.randf_range(0.8, 1.1), 0.0, 1.0),
		clampf(base.v * rng.randf_range(0.85, 1.15), 0.1, 1.0))
	t.price = hire_cost(t, level)
	return t

## Class starter kit: every Tempo arrives holding the weapon it died with (Beginner quality).
static func starter_kit(class_id: StringName) -> Array:
	match class_id:
		&"archer": return [&"hunters_bow"]
		&"thief": return [&"rondel_dagger", &"rondel_dagger"]
		&"mystic": return [&"ashwood_staff"]
	return [&"iron_longsword"]

## Off-hand gear a class arrives with besides its weapons (a Warden's shield).
static func starter_offhand(class_id: StringName) -> Array:
	return [&"warden_kite_shield"] if class_id == &"warden" else []

## Give a freshly bound spirit its uid and starting gear, and add it to the hero's Tempos.
static func _bind_new(hero: HeroData, t: TempoData, kit: Array) -> void:
	hero.tempo_serial += 1
	t.uid = hero.tempo_serial
	for bid in kit:
		var it := DB.make_item(bid, BH.Rarity.BEGINNER, 1, hash("%s%d" % [bid, t.uid]))
		if it:
			var slot := auto_slot(t, it)
			t.equipment.equip(it, slot, hero.progress.level, NO_ATTR)
	hero.tempos.append(t)

static func hire_error(hero: HeroData, index: int) -> String:
	var offers: Array = hero.tempo_roster.get("offers", [])
	if index < 0 or index >= offers.size():
		return "That spirit has already faded"
	if bound_count(hero) >= DataTempos.MAX_ACTIVE:
		return "You can carry only %d Tempos. Release one first." % DataTempos.MAX_ACTIVE
	var cost := int(offers[index].get("price", 0))
	if hero.inventory.gold < cost:
		return "Not enough gold (%d needed)" % cost
	return ""

## Bind the offered spirit `index`: pay, give it its starter weapon, and let a new spirit take its place in the roster.
static func hire(hero: HeroData, index: int) -> TempoData:
	if hire_error(hero, index) != "":
		return null
	var d: Dictionary = hero.tempo_roster.offers[index]
	var t := TempoData.from_dict(d)
	hero.inventory.gold -= t.price
	hero.inventory.changed.emit()
	_bind_new(hero, t, starter_kit(t.class_id) + starter_offhand(t.class_id))
	# a new spirit answers in its place
	var serial := int(hero.tempo_roster.get("serial", 0)) + 1
	var taken := hero.tempos.map(func(x): return x.tempo_name)
	for o in hero.tempo_roster.offers:
		taken.append(String(o.get("name", "")))
	hero.tempo_roster.offers[index] = generate(hash("%s/%d" % [hero.hero_name, serial]), hero.progress.level, t.class_id, taken,
		int(hero.tempo_roster.get("grade", t.grade))).to_dict()
	hero.tempo_roster["serial"] = serial
	Events.tempo_changed.emit(t.uid)
	return t

# ---- Renowned spirits and the starter ---------------------------------------------------------------------------

## A renowned spirit as it waits at the shrine (uid 0 until bound).
static func legend_data(id: StringName) -> TempoData:
	var lg := DataTempos.legend(id)
	if lg.is_empty():
		return null
	var t := TempoData.new()
	t.legend_id = id
	t.tempo_name = String(lg.name)
	t.class_id = lg["class"]
	t.trait_id = lg.trait
	t.skills = (lg.skills as Array).duplicate()
	t.origin = String(lg.origin)
	t.tint = lg.tint
	t.grade = DataTempos.max_grade()
	t.price = int(lg.price)
	return t

static func legend_bound(hero: HeroData, id: StringName) -> bool:
	return hero.tempos.any(func(t): return t.legend_id == id)

## Why a renowned spirit cannot be bound right now ("" = it can).
static func legend_error(hero: HeroData, id: StringName) -> String:
	var lg := DataTempos.legend(id)
	if lg.is_empty():
		return "No such spirit"
	if legend_bound(hero, id):
		return "%s already walks with you" % lg.name
	if hero.progress.level < int(lg.level):
		return "Answers only a hero of level %d" % int(lg.level)
	if bound_count(hero) >= DataTempos.MAX_ACTIVE:
		return "You can carry only %d Tempos. Release one first." % DataTempos.MAX_ACTIVE
	if hero.inventory.gold < int(lg.price):
		return "Not enough gold (%d needed)" % int(lg.price)
	return ""

## Bind a renowned spirit: pay its price; it arrives with its own ghost weapon (and its kit).
static func hire_legend(hero: HeroData, id: StringName) -> TempoData:
	if legend_error(hero, id) != "":
		return null
	var t := legend_data(id)
	hero.inventory.gold -= t.price
	hero.inventory.changed.emit()
	_bind_new(hero, t, DataTempos.legend(id).get("kit", []))
	Events.tempo_changed.emit(t.uid)
	return t

## Every new hero starts with a starter Tempo (DataTempos.STARTER: a grade-1 Swordsman), bound for free. Its name is
## rolled for this hero (NameForge; bh-015 — it used to be Tobren for everyone). `seed_value` 0 = a fresh random seed.
## Does nothing if the hero has any Tempo.
static func grant_starter(hero: HeroData, seed_value := 0) -> TempoData:
	if hero == null or not hero.tempos.is_empty():
		return null
	var st := DataTempos.STARTER
	var t := TempoData.new()
	var rng := RandomNumberGenerator.new()
	if seed_value != 0:
		rng.seed = seed_value
	else:
		rng.randomize()
	t.tempo_name = NameForge.person(rng, [hero.hero_name])
	hero.starter_name = t.tempo_name
	t.class_id = st["class"]
	t.trait_id = st.trait
	t.skills = (st.skills as Array).duplicate()
	t.origin = String(st.origin)
	t.tint = st.tint
	t.grade = 1
	t.price = 0
	_bind_new(hero, t, starter_kit(t.class_id))
	return t

static func revive_error(hero: HeroData, t: TempoData) -> String:
	if t == null or not t.fallen:
		return "That Tempo has not fallen"
	var cost := revive_cost(t, hero)
	if hero.inventory.gold < cost:
		return "Not enough gold (%d needed)" % cost
	return ""

static func revive(hero: HeroData, t: TempoData) -> String:
	var err := revive_error(hero, t)
	if err != "":
		return err
	hero.inventory.gold -= revive_cost(t, hero)
	hero.inventory.changed.emit()
	t.fallen = false
	t.hp_frac = 1.0
	t.mana_frac = 1.0
	Events.tempo_changed.emit(t.uid)
	return ""

## Release a Tempo for good. Its gear goes back to the hero's bag (refused when the bag cannot hold it).
static func release(hero: HeroData, t: TempoData) -> String:
	if t == null or not hero.tempos.has(t):
		return "No such Tempo"
	var gear := t.equipment.equipped_items() + t.equipment.recovered_items
	if hero.inventory.free_cells() < gear.size():
		return "Your bag cannot hold its gear (%d free cells needed)" % gear.size()
	hero._loading_equipment = true
	for s in BH.SLOTS:
		var it := t.equipment.get_item(s)
		if it != null:
			t.equipment.slots[s] = null
			hero.inventory.add(it)
	for it in t.equipment.recovered_items:
		hero.inventory.add(it)
	t.equipment.recovered_items.clear()
	hero.tempos.erase(t)
	hero._loading_equipment = false
	hero.inventory.changed.emit()
	Events.tempo_changed.emit(t.uid)
	return ""

## Rest at the inn / full restoration: every standing Tempo is made whole.
static func restore_all(hero: HeroData) -> void:
	for t in hero.tempos:
		if not t.fallen:
			t.hp_frac = 1.0
			t.mana_frac = 1.0
	Events.tempo_changed.emit(0)
