class_name Shop
extends RefCounted
## A merchant's live stock for one hero: generation, refresh, buy / sell / buyback and persistence.
## Pure model (no nodes, no UI). The state lives in HeroData.shops[id] so saves restore the exact stock.
##
## Refresh: stock rerolls when `refresh_minutes` of play time have passed since the last roll, or when the hero has
## outgrown it by 3+ levels. Fixed items are always present; specials appear once their level/flag gate opens and
## never return after being bought.

signal changed

const BUYBACK_MAX := 12

var def: ShopDef
var stock: Array = []             # [{item: ItemInstance, infinite: bool, special: String}]
var buyback: Array = []           # [{item: ItemInstance, price: int}] newest first
var refresh_index := 0
var next_refresh_at := 0.0        # hero play time (s)
var stock_level := 1
var specials_sold := {}           # special id -> true
var stock_clears := 0             # restock_on_clears shops: the hero's clear count when this stock was rolled
var _hero: HeroData               # the hero this stock belongs to (every change is written back to it)

## Opens the shop for a hero: restores the saved state (or rolls fresh stock) and refreshes if due.
static func open(p_def: ShopDef, hero: HeroData) -> Shop:
	var s := Shop.new()
	s.def = p_def
	var saved: Dictionary = hero.shops.get(p_def.id, {})
	if saved.is_empty():
		s.generate(hero)
	else:
		s.from_dict(saved)
		s.maybe_refresh(hero)
	# Restore newly introduced or newly unlocked unlimited goods without rerolling
	# finite stock, buyback items, or already purchased specials in an existing save.
	s._ensure_infinite_stock(hero)
	s.save(hero)
	s._hero = hero
	s.changed.connect(s._write_back)
	return s

func _write_back() -> void:
	if _hero:
		save(_hero)

func _ensure_infinite_stock(hero: HeroData) -> void:
	for f in def.fixed:
		if not f.get("infinite", false) or hero.progress.level < int(f.get("level_min", 1)):
			continue
		var base_id := StringName(f.base)
		var present := false
		for entry in stock:
			if entry.infinite and entry.item.base.id == base_id:
				present = true
				break
		if not present:
			var it := DB.make_item(base_id, int(f.get("rarity", BH.Rarity.COMMON)), hero.progress.level, hash(base_id) | 1)
			if it:
				stock.append({"item": it, "infinite": true, "special": ""})

func refresh_due(hero: HeroData) -> bool:
	if def.restock_on_clears:
		return hero.clear_count != stock_clears
	return hero.play_time >= next_refresh_at or hero.progress.level >= stock_level + 3

func maybe_refresh(hero: HeroData) -> bool:
	if refresh_due(hero):
		refresh_index += 1
		generate(hero)
		return true
	_add_new_specials(hero)
	return false

func seconds_to_refresh(hero: HeroData) -> float:
	return maxf(0.0, next_refresh_at - hero.play_time)

# ---- Generation ----------------------------------------------------------------------------------------------

func generate(hero: HeroData) -> void:
	var lvl := clampi(hero.progress.level, 1, BH.LEVEL_CAP)
	stock_level = lvl
	stock_clears = hero.clear_count
	next_refresh_at = hero.play_time + def.refresh_minutes * 60.0
	var ilvl := mini(BH.LEVEL_CAP, lvl + def.ilvl_bonus)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%s|%d|%s" % [def.id, refresh_index, hero.hero_name])
	stock.clear()
	for f in def.fixed:
		if lvl < int(f.get("level_min", 1)):
			continue
		var it := DB.make_item(StringName(f.base), int(f.get("rarity", BH.Rarity.COMMON)), lvl, rng.randi() | 1)
		if it:
			stock.append({"item": it, "infinite": bool(f.get("infinite", false)), "special": ""})
	var pool_items: Array = []
	for p in def.pools:
		for i in int(p.get("count", 1)):
			var base := _pool_base(p, lvl, rng, hero)
			if base == null:
				continue
			var it := ItemGenerator.generate(base, ilvl, _pool_rarity(lvl, rng), _child_rng(rng))
			pool_items.append(it)
	# the occasional rare piece
	if not pool_items.is_empty() and rng.randf() < def.rare_chance and lvl >= 4:
		var idx := rng.randi_range(0, pool_items.size() - 1)
		var old: ItemInstance = pool_items[idx]
		var rare := BH.Rarity.MASTER if lvl >= 14 and rng.randf() < 0.3 else BH.Rarity.ELITE
		pool_items[idx] = ItemGenerator.generate(old.base, ilvl, maxi(rare, old.rarity), _child_rng(rng))
	for it in pool_items:
		stock.append({"item": it, "infinite": false, "special": ""})
	_add_new_specials(hero)
	changed.emit()

func _child_rng(rng: RandomNumberGenerator) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = rng.randi() | 1
	return r

func _pool_base(p: Dictionary, lvl: int, rng: RandomNumberGenerator, hero: HeroData) -> ItemBaseDef:
	var cats: Array = p.get("categories", [])
	var wtypes: Array = p.get("weapon_types", [])
	var hint: StringName = hero.cls.id if p.get("class_hint", false) else &""
	for attempt in 16:
		var b := ItemGenerator.random_base(rng, lvl, cats, hint)
		if b == null:
			return null
		if wtypes.is_empty() or (b.weapon_type != &"" and wtypes.has(b.weapon_type)):
			return b
	return null

## Merchant rarity table: grounded early, broader later (monsters and bosses remain the source of the high tiers).
func _pool_rarity(lvl: int, rng: RandomNumberGenerator) -> int:
	var w := [0.0, 50.0, 30.0, 15.0 if lvl >= 3 else 0.0, 6.0 if lvl >= 6 else 0.0, 2.0 if lvl >= 10 else 0.0]
	if not def.rarity_weights.is_empty():
		w = def.rarity_weights.duplicate()
		# premium tables still grow with the hero: Master stock from level 5, Mythical from level 12
		for i in w.size():
			if (i >= BH.Rarity.MYTHICAL and lvl < 12) or (i == BH.Rarity.MASTER and lvl < 5):
				w[i] = 0.0
	var total := 0.0
	for x in w:
		total += x
	var r := rng.randf() * total
	for i in w.size():
		r -= w[i]
		if r <= 0.0 and w[i] > 0.0:
			return maxi(i, def.rarity_floor)
	return maxi(BH.Rarity.COMMON, def.rarity_floor)

func _add_new_specials(hero: HeroData) -> void:
	for sp in def.specials:
		var sid := String(sp.id)
		if specials_sold.has(sid) or _has_special(sid):
			continue
		if hero.progress.level < int(sp.get("level_min", 1)):
			continue
		if sp.has("flag") and not bool(hero.world_flags.get(StringName(sp.flag), false)):
			continue
		var it := DB.make_item(StringName(sp.base), int(sp.get("rarity", BH.Rarity.ELITE)), maxi(hero.progress.level, int(sp.get("level_min", 1))), hash(sid) | 1)
		if it:
			stock.append({"item": it, "infinite": false, "special": sid})

func _has_special(sid: String) -> bool:
	for e in stock:
		if e.special == sid:
			return true
	return false

# ---- Trading --------------------------------------------------------------------------------------------------

func buy_price(entry_index: int, hero: HeroData, count := 1) -> int:
	if entry_index < 0 or entry_index >= stock.size():
		return 0
	return ShopPricing.buy_total(stock[entry_index].item, def, count, hero.relationship(def.npc), GuildRules.shop_discount(hero, def.id))

## Buy `count` of a stock entry (count > 1 only for stackables). Returns {ok, error, price, item}.
func buy(entry_index: int, hero: HeroData, count := 1) -> Dictionary:
	if entry_index < 0 or entry_index >= stock.size():
		return {"ok": false, "error": "That item is no longer in stock"}
	var e: Dictionary = stock[entry_index]
	var src: ItemInstance = e.item
	count = maxi(1, count)
	if not src.base.is_stackable():
		count = 1
	elif not e.infinite:
		count = mini(count, src.count)
	var price := buy_price(entry_index, hero, count)
	if hero.inventory.gold < price:
		return {"ok": false, "error": "Not enough gold", "price": price}
	var bought := src.clone()
	bought.count = count
	if not hero.inventory.can_fit(bought):
		return {"ok": false, "error": "Inventory is full", "price": price}
	hero.inventory.gold -= price
	hero.inventory.add(bought)
	if not e.infinite:
		if src.base.is_stackable() and src.count > count:
			src.count -= count
		else:
			stock.remove_at(entry_index)
			if e.special != "":
				specials_sold[e.special] = true
	Events.item_bought.emit(bought, price)
	changed.emit()
	return {"ok": true, "price": price, "item": bought}

func sell_price(item: ItemInstance, hero: HeroData) -> int:
	return ShopPricing.sell_total(item, def, hero.relationship(def.npc))

## Sell an inventory item (whole stack). Protected (locked/favorite) and unsellable items refuse.
func sell(item: ItemInstance, hero: HeroData) -> Dictionary:
	if item == null or hero.inventory.index_of(item) < 0:
		return {"ok": false, "error": "Item not in inventory"}
	if item.is_protected():
		return {"ok": false, "error": "Item is locked"}
	if not item.base.sellable:
		return {"ok": false, "error": "The merchant will not buy this"}
	var gold := sell_price(item, hero)
	hero.inventory.remove_item(item)
	hero.inventory.gold += gold
	hero.inventory.changed.emit()
	buyback.push_front({"item": item, "price": gold})
	while buyback.size() > mini(def.buyback_size, BUYBACK_MAX):
		buyback.pop_back()
	Events.item_sold.emit(item, gold)
	changed.emit()
	return {"ok": true, "gold": gold}

## Sell every item marked as junk. Returns total gold.
func sell_junk(hero: HeroData) -> int:
	var total := 0
	for it in hero.inventory.junk_items():
		var r := sell(it, hero)
		if r.ok:
			total += int(r.gold)
	return total

## Buy back a sold item for exactly what the merchant paid.
func buy_back(index: int, hero: HeroData) -> Dictionary:
	if index < 0 or index >= buyback.size():
		return {"ok": false, "error": "Nothing to buy back"}
	var e: Dictionary = buyback[index]
	if hero.inventory.gold < int(e.price):
		return {"ok": false, "error": "Not enough gold", "price": e.price}
	if not hero.inventory.can_fit(e.item):
		return {"ok": false, "error": "Inventory is full", "price": e.price}
	hero.inventory.gold -= int(e.price)
	hero.inventory.add(e.item)
	buyback.remove_at(index)
	changed.emit()
	return {"ok": true, "price": e.price, "item": e.item}

# ---- Persistence ------------------------------------------------------------------------------------------------

func save(hero: HeroData) -> void:
	hero.shops[def.id] = to_dict()

func to_dict() -> Dictionary:
	var st := []
	for e in stock:
		st.append({"item": e.item.to_dict(), "infinite": e.infinite, "special": e.special})
	var bb := []
	for e in buyback:
		bb.append({"item": e.item.to_dict(), "price": e.price})
	return {"refresh": refresh_index, "next_at": next_refresh_at, "level": stock_level, "stock": st, "buyback": bb,
		"specials_sold": specials_sold.keys(), "clears": stock_clears}

func from_dict(d: Dictionary) -> void:
	refresh_index = int(d.get("refresh", 0))
	next_refresh_at = float(d.get("next_at", 0.0))
	stock_level = int(d.get("level", 1))
	stock_clears = int(d.get("clears", 0))
	stock.clear()
	for e in d.get("stock", []):
		var it := ItemInstance.from_dict(e.get("item", {}))
		if it:
			stock.append({"item": it, "infinite": bool(e.get("infinite", false)), "special": String(e.get("special", ""))})
	buyback.clear()
	for e in d.get("buyback", []):
		var it := ItemInstance.from_dict(e.get("item", {}))
		if it:
			buyback.append({"item": it, "price": int(e.get("price", 0))})
	specials_sold.clear()
	for k in d.get("specials_sold", []):
		specials_sold[String(k)] = true
