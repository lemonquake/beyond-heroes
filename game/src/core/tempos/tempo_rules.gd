class_name TempoRules
## Rules for Tempos (spirit companions, docs/LORE.md §9). Pure functions over HeroData / TempoData — the Tempo-Caller's
## services, the Tempo window, the Tempo actor and the tests all call these.
##
## * Strength: a Tempo mirrors 50% of its hero's persistent stats (pools, defense, accuracy, evasion, critical chance,
##   damage bonuses, resistances). Its own gear, class and trait add on top, and every "increased" / "more" modifier
##   then applies to the total — so a Tempo's gear always matters and it grows as its hero grows.
## * Gear: one rarity tier below the best its hero may wear (Unranked heroes' Tempos: up to Advanced), class weapons only,
##   the hero's level requirement; spirits ignore attribute requirements.
## * At most two Tempos bound at once (fallen ones count until they are called back or released).

const MIRROR_KEYS: Array[StringName] = [&"max_hp", &"max_mana", &"hp_regen", &"mana_regen", &"defense", &"evasion",
	&"accuracy", &"crit_chance", &"status_res", &"knockback_res", &"poise", &"phys_damage", &"magic_damage",
	&"elemental_damage", &"healing", &"projectile_damage", &"damage", &"added_physical"]
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
static func spirit_loadout(class_id: StringName, level: int) -> WeaponLoadout:
	var td := DataTempos.tempo_class(class_id)
	var wt := DB.weapon_type(td.get("spirit_weapon", &"sword"))
	var lo := WeaponLoadout.new()
	lo.main_type = wt
	lo.main_min = 3.0 + 0.9 * float(level)
	lo.main_max = 6.0 + 1.5 * float(level)
	lo.main_crit = wt.crit_chance if wt else 0.05
	lo.main_element = Elements.LIGHT
	lo.main_elem_share = 0.2
	if class_id == &"thief" and wt != null:
		lo.off_type = wt
		lo.off_min = lo.main_min * 0.9
		lo.off_max = lo.main_max * 0.9
		lo.off_element = Elements.LIGHT
		lo.off_elem_share = 0.2
		lo.dual_wield = true
	return lo

## Weapon configuration the Tempo actually fights with.
static func loadout(t: TempoData, level: int) -> WeaponLoadout:
	var lo := t.equipment.loadout()
	return spirit_loadout(t.class_id, level) if lo.is_unarmed() else lo

## Derived stats: 50% of `hero_stats` (the hero's persistent stats) + the Tempo's gear, class and trait.
## `hero_stats` may be null (tools, previews): the Tempo then has only its own.
static func compute(t: TempoData, hero_stats: DerivedStats, level: int, hero_cls: ClassDef = null, runtime: Array = []) -> DerivedStats:
	var mods: Array = []
	var who := "Soul-bond (50% of your hero)"
	if hero_stats != null:
		for k in mirror_keys():
			var v := hero_stats.get_stat(k) * DataTempos.MIRROR
			if absf(v) > 0.00001:
				mods.append(StatModifier.flat(k, v, who))
	mods.append_array(t.equipment.modifiers())
	mods.append_array(DataTempos.mods_from(t.class_def().get("mods", []), t.class_name_text()))
	mods.append_array(DataTempos.mods_from(t.trait_def().get("mods", []), String(t.trait_def().get("name", ""))))
	mods.append_array(runtime)
	var d := StatCalculator.compute(shell(t.class_id, hero_cls), level, {}, mods, loadout(t, level))
	if hero_stats != null:
		# attributes shown on the sheet: the mirrored half plus what the Tempo's own gear adds
		for a in BH.ATTRIBUTES:
			var mirrored := floorf(hero_stats.get_stat(a) * DataTempos.MIRROR)
			var lines := PackedStringArray(["Mirrored from your hero (50%%): %d" % mirrored])
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
	if hero.progress.level < item.base.level_req:
		return "Requires level %d" % item.base.level_req
	if not rarity_allowed(hero, item.rarity):
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
	hero.inventory.cells[idx] = null
	var res := t.equipment.equip(item, slot, hero.progress.level, NO_ATTR)
	for d in res.displaced:
		if hero.inventory.cells[idx] == null:
			hero.inventory.cells[idx] = d
		else:
			hero.inventory.add(d)
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
	t.equipment.unequip(slot)
	hero.inventory.add(it)
	var orphan := t.equipment.orphaned_sub()
	if orphan != null:
		t.equipment.unequip(&"sub_weapon")
		hero.inventory.add(orphan)
	hero.inventory.changed.emit()
	Events.tempo_changed.emit(t.uid)
	return ""

# ---- Binding, calling back, releasing ------------------------------------------------------------------------------

static func hire_cost(t: TempoData, level: int) -> int:
	var c := (80.0 + 30.0 * float(maxi(1, level) - 1)) * (1.0 + 0.2 * float(maxi(0, t.skills.size() - 2)))
	if t.has_heal():
		c *= 1.15
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

## Spirits answering the Tempo-Caller right now (refreshed on a play-time clock and after each binding).
static func roster(hero: HeroData) -> Array:
	var r: Dictionary = hero.tempo_roster
	if (r.get("offers", []) as Array).is_empty() or hero.play_time >= float(r.get("refresh_at", 0.0)):
		refresh_roster(hero)
	var out := []
	for d in hero.tempo_roster.offers:
		out.append(TempoData.from_dict(d))
	return out

static func refresh_roster(hero: HeroData) -> void:
	var serial := int(hero.tempo_roster.get("serial", 0))
	var offers := []
	var taken := hero.tempos.map(func(t): return t.tempo_name)
	var classes := DataTempos.class_ids()
	for i in DataTempos.ROSTER_SIZE:
		serial += 1
		var cls: StringName = classes[i] if i < classes.size() else &""
		var t := generate(hash("%s/%d" % [hero.hero_name, serial]), hero.progress.level, cls, taken)
		taken.append(t.tempo_name)
		offers.append(t.to_dict())
	hero.tempo_roster = {"offers": offers, "refresh_at": hero.play_time + DataTempos.ROSTER_REFRESH, "serial": serial}

## A random spirit (deterministic for a seed): class, name, personality, 2–3 skills (the class signature first), where
## it fell, a spectral tint and its price.
static func generate(seed_value: int, level: int, class_id: StringName = &"", taken: Array = []) -> TempoData:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var t := TempoData.new()
	var classes := DataTempos.class_ids()
	t.class_id = class_id if DataTempos.CLASSES.has(class_id) else classes[rng.randi_range(0, classes.size() - 1)]
	var names: Array = DataTempos.NAMES.filter(func(n): return not taken.has(n))
	if names.is_empty():
		names = DataTempos.NAMES
	t.tempo_name = names[rng.randi_range(0, names.size() - 1)]
	var traits := DataTempos.TRAITS.keys()
	traits.sort()
	t.trait_id = traits[rng.randi_range(0, traits.size() - 1)]
	var td := t.class_def()
	t.skills = [td.signature]
	var pool: Array = (td.skills as Array).filter(func(s): return s != td.signature)
	var extra := 2 if rng.randf() < 0.45 else 1
	for i in extra:
		var s: StringName = pool[rng.randi_range(0, pool.size() - 1)]
		pool.erase(s)
		t.skills.append(s)
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
	return [&"iron_longsword"]

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
	hero.tempo_serial += 1
	t.uid = hero.tempo_serial
	for bid in starter_kit(t.class_id):
		var it := DB.make_item(bid, BH.Rarity.BEGINNER, 1, hash("%s%d" % [bid, t.uid]))
		if it:
			var slot := auto_slot(t, it)
			t.equipment.equip(it, slot, hero.progress.level, NO_ATTR)
	hero.tempos.append(t)
	# a new spirit answers in its place
	var serial := int(hero.tempo_roster.get("serial", 0)) + 1
	var taken := hero.tempos.map(func(x): return x.tempo_name)
	for o in hero.tempo_roster.offers:
		taken.append(String(o.get("name", "")))
	hero.tempo_roster.offers[index] = generate(hash("%s/%d" % [hero.hero_name, serial]), hero.progress.level, t.class_id, taken).to_dict()
	hero.tempo_roster["serial"] = serial
	Events.tempo_changed.emit(t.uid)
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
	var gear := t.equipment.equipped_items()
	if hero.inventory.free_cells() < gear.size():
		return "Your bag cannot hold its gear (%d free cells needed)" % gear.size()
	for s in BH.SLOTS:
		var it := t.equipment.get_item(s)
		if it != null:
			t.equipment.slots[s] = null
			hero.inventory.add(it)
	hero.tempos.erase(t)
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
