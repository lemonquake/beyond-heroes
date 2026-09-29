class_name QuakeBrain
extends RefCounted
## The head of a Quake Team mate (bh-017): everything a hero does with their pockets — spend attribute points, judge a
## piece of gear by how much stronger it would make them, buy and wear the best, sell what they replaced, keep
## draughts in the bag, and bind a Tempo at the shrine. Pure rules over the mate's own HeroData (no nodes), driven by
## the QuakeAlly actor when it walks to a stand in town.

const GEAR_MIN_GAIN := 0.03            # a purchase must make the mate at least 3% stronger
const MAX_BUYS_PER_STAND := 3
const HEAL_IDS := [&"minor_health_potion", &"health_potion", &"greater_health_potion", &"superior_health_potion"]
const MANA_IDS := [&"minor_mana_potion", &"mana_potion", &"greater_mana_potion", &"superior_mana_potion"]
const DRAUGHT_CLASSES := [&"mage"]

# ---- points --------------------------------------------------------------------------------------------------------

## Spend free attribute points on the class's major attributes (first ones most).
static func spend_points(hero: HeroData) -> void:
	var majors: Array = hero.cls.major_attributes
	if majors.is_empty() or hero.progress.free_points <= 0:
		return
	var pattern := [0, 0, 1, 0, 1, 2]
	var i := 0
	while hero.progress.free_points > 0 and i < 400:
		var a: StringName = majors[mini(int(pattern[i % pattern.size()]), majors.size() - 1)]
		if not hero.progress.allocate(a, 1):
			break
		i += 1

# ---- rating ---------------------------------------------------------------------------------------------------------

## One number for "how strong is this hero right now": offence (weapon damage, speed, crits, damage bonuses, added
## elemental damage) and staying power (HP, resistances, evasion), blended.
static func rating(hero: HeroData) -> float:
	var s := hero.compute_stats()
	var lo := s.loadout
	var caster := hero.cls.id == &"mage"
	var dmg := (lo.main_min + lo.main_max) * 0.5
	if lo.dual_wield:
		dmg = (dmg + (lo.off_min + lo.off_max) * 0.5) * 0.5 * (1.0 + WeaponLoadout.DUAL_ATTACK_SPEED_MORE)
	var aps := lo.aps() * s.get_stat(&"attack_speed", 1.0)
	var crit := clampf(s.get_stat(&"crit_chance") + lo.main_crit, 0.0, 1.0)
	var bonus := 1.0 + s.get_stat(&"damage") + s.get_stat(&"weapon_damage")
	if caster:
		bonus += s.get_stat(&"magic_damage") + s.get_stat(&"elemental_damage") * 0.5
	else:
		bonus += s.get_stat(&"phys_damage") + s.get_stat(&"heavy_damage") * 0.2
	var added := 0.0
	for e in Elements.ELEMENTAL:
		added += s.get_stat(StringName("added_" + String(Elements.key(e))))
	added += s.get_stat(&"added_physical")
	var offence := (dmg * bonus + added) * aps * (1.0 + crit * (s.get_stat(&"crit_damage", 1.5) - 1.0))
	if caster:
		offence *= 1.0 + s.get_stat(&"max_mana") / 500.0
	var pres := clampf(s.get_stat(&"phys_res"), 0.0, 0.75)
	var defence := s.get_stat(&"max_hp", 100.0) / (1.0 - pres) * (1.0 + s.get_stat(&"evade_chance") * 0.6 + s.get_stat(&"block_chance") * 0.3)
	defence *= 1.0 + s.get_stat(&"hp_regen") / 60.0
	return pow(maxf(1.0, offence), 0.6) * pow(maxf(1.0, defence), 0.4)

## Whether an item is gear for this hero's class (weapons and armor only; accessories suit everyone).
static func suits(hero: HeroData, item: ItemInstance) -> bool:
	if item == null or not item.is_equipment():
		return false
	if item.base.category == &"accessory":
		return true
	return ItemGenerator.class_fit(item.base, hero.cls.id)

## How much stronger wearing `item` would make the hero, and in which slot: {gain (fraction of the current rating), slot}.
static func best_slot(hero: HeroData, item: ItemInstance, now: float) -> Dictionary:
	var best := {"gain": -1.0, "slot": &""}
	if not suits(hero, item):
		return best
	var eq := hero.equipment
	var lvl := hero.progress.level
	var attrs := hero.progress.base_attributes()
	for slot in BH.CATEGORY_SLOTS.get(item.base.category, []):
		if eq.check(item, slot, lvl, attrs) != "":
			continue
		var old: ItemInstance = eq.slots[slot]
		var old_sub: ItemInstance = eq.slots[&"sub_weapon"]
		eq.slots[slot] = item
		if slot == &"main_weapon":
			var wt := eq.weapon_type_of(item)
			var sub: ItemInstance = eq.slots[&"sub_weapon"]
			if sub != null and wt != null and (wt.two_handed or (sub.base.is_weapon() and not wt.dual_wieldable)):
				eq.slots[&"sub_weapon"] = null
		var r := rating(hero)
		eq.slots[slot] = old
		eq.slots[&"sub_weapon"] = old_sub
		var gain := r / maxf(1.0, now) - 1.0
		if gain > float(best.gain):
			best = {"gain": gain, "slot": slot}
	return best

## Wear the best of what is in the bag, one piece at a time, until nothing helps. Returns the names put on.
static func equip_best(hero: HeroData) -> Array:
	var worn := []
	for _pass in 12:
		var now := rating(hero)
		var pick: ItemInstance = null
		var pick_slot: StringName = &""
		var pick_gain := 0.002
		for it in hero.inventory.cells:
			if it == null or not it.is_equipment():
				continue
			var b := best_slot(hero, it, now)
			if float(b.gain) > pick_gain:
				pick_gain = float(b.gain)
				pick = it
				pick_slot = b.slot
		if pick == null:
			break
		if hero.equip_from_inventory(pick, pick_slot) != "":
			break
		worn.append(pick.display_name())
	return worn

# ---- shopping -------------------------------------------------------------------------------------------------------

## What a mate does at one stand of the town row (DataTownRows). Returns {"msgs": [String], "hired": TempoData or null}.
static func visit_stand(mate: QuakeMate, stand: Dictionary) -> Dictionary:
	var out := {"msgs": [], "hired": null}
	match String(stand.kind):
		DataTownRows.SHOP:
			out.msgs = visit_shop(mate, stand)
		DataTownRows.SHRINE:
			var t := visit_shrine(mate)
			if t != null:
				out.hired = t
				out.msgs = ["%s binds a Tempo: %s the %s." % [mate.display_name(), t.tempo_name, t.class_name_text()]]
	return out

static func visit_shop(mate: QuakeMate, stand: Dictionary) -> Array:
	var msgs := []
	var npc := DB.npc(StringName(stand.get("npc", &"")))
	if npc == null or npc.shop == &"":
		return msgs
	var def := DB.shop(npc.shop)
	if def == null:
		return msgs
	var hero := mate.hero
	var shop := Shop.open(def, hero)
	# gear first (the biggest thing), then the draughts the gold left over can buy
	msgs.append_array(_buy_gear(mate, shop))
	_buy_draughts(mate, shop)
	return msgs

static func _reserve(hero: HeroData) -> int:
	return 20 + 4 * hero.progress.level

static func _buy_gear(mate: QuakeMate, shop: Shop) -> Array:
	var msgs := []
	var hero := mate.hero
	for n in MAX_BUYS_PER_STAND:
		var now := rating(hero)
		var budget := hero.inventory.gold - _reserve(hero)
		if budget <= 0:
			break
		var best_i := -1
		var best_score := 0.0
		var best_slot: StringName = &""
		for i in shop.stock.size():
			var e: Dictionary = shop.stock[i]
			var it: ItemInstance = e.item
			if not it.is_equipment():
				continue
			var price := shop.buy_price(i, hero)
			if price <= 0 or price > budget:
				continue
			var b := best_slot(hero, it, now)
			if float(b.gain) < GEAR_MIN_GAIN:
				continue
			# a bigger jump wins, a cheaper one breaks ties
			var score := float(b.gain) - 0.00002 * float(price)
			if score > best_score:
				best_score = score
				best_i = i
				best_slot = b.slot
		if best_i < 0:
			break
		var item: ItemInstance = shop.stock[best_i].item
		var r := shop.buy(best_i, hero, 1)
		if not r.ok:
			break
		var bought: ItemInstance = r.item
		var before := hero.equipment.get_item(best_slot)
		if hero.equip_from_inventory(bought, best_slot) != "":
			break
		msgs.append("%s bought %s (%d gold) and put it on." % [mate.display_name(), bought.display_name(), int(r.price)])
		# sell the piece it replaced
		if before != null and hero.inventory.index_of(before) >= 0 and not before.is_protected():
			shop.sell(before, hero)
	return msgs

static func _potion_count(hero: HeroData, ids: Array) -> int:
	var n := 0
	for id in ids:
		n += hero.inventory.count_of(id)
	return n

static func _buy_draughts(mate: QuakeMate, shop: Shop) -> void:
	var hero := mate.hero
	var want_hp := 4 if hero.progress.level < 10 else 6
	var want_mana := 3 if DRAUGHT_CLASSES.has(hero.cls.id) else 0
	for pair in [[HEAL_IDS, want_hp], [MANA_IDS, want_mana]]:
		var ids: Array = pair[0]
		var want: int = pair[1]
		var have := _potion_count(hero, ids)
		if have >= want:
			continue
		# the strongest draught this shop sells that the hero may use and can pay for
		var best_i := -1
		var best_rank := -1
		for i in shop.stock.size():
			var b: ItemBaseDef = (shop.stock[i].item as ItemInstance).base
			var rank := ids.find(b.id)
			if rank > best_rank and b.level_req <= hero.progress.level:
				best_rank = rank
				best_i = i
		if best_i < 0:
			continue
		for k in want - have:
			var budget := hero.inventory.gold - (_reserve(hero) if k > 0 else 0)
			if budget <= 0 or shop.buy_price(best_i, hero) > budget:
				break
			if not shop.buy(best_i, hero, 1).ok:
				break

## Bind a Tempo at the shrine when the mate can pay and has none yet. Returns the new TempoData or null.
static func visit_shrine(mate: QuakeMate) -> TempoData:
	var hero := mate.hero
	if hero.tempos.size() >= QuakeMate.MAX_TEMPOS:
		return null
	var offers := TempoRules.roster(hero)
	var want_heal := hero.cls.id != &"mage"
	var best := -1
	var best_score := -1.0
	for i in offers.size():
		var t: TempoData = offers[i]
		if hero.inventory.gold < t.price + _reserve(hero) or TempoRules.hire_error(hero, i) != "":
			continue
		var score := float(t.skills.size()) + (2.0 if t.has_heal() == want_heal else 0.0) + float(t.grade) * 0.5
		if score > best_score:
			best_score = score
			best = i
	if best < 0:
		return null
	return TempoRules.hire(hero, best)

## A cheap check for "is a trip to town worth it": more gold than last time, a new level, or a new map.
static func wants_trip(mate: QuakeMate, map_id: StringName) -> bool:
	var g := mate.hero.inventory.gold
	if mate.shop_map != map_id or mate.hero.progress.level > mate.shop_level:
		return true
	return g >= mate.shop_gold + maxi(60, mate.shop_gold / 4)

static func trip_done(mate: QuakeMate, map_id: StringName) -> void:
	mate.shop_gold = mate.hero.inventory.gold
	mate.shop_level = mate.hero.progress.level
	mate.shop_map = map_id
