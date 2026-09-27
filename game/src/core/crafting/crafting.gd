class_name Crafting
## Crafting rules (bh-007): which recipes a hero knows, whether a recipe can be made here and now, making it
## (inputs and gold taken exactly once, results added to the bag), learning recipes from scrolls, and salvage.
## Pure model: no nodes. Recipes are data (DataCrafting); the hero keeps what they learned in HeroData.known_recipes.

const MAX_BATCH := 20

static func recipes_for(station: StringName) -> Array:
	var out := DataCrafting.all().filter(func(r): return (r.stations as Array).has(station))
	out.sort_custom(func(a, b): return [String(a.group), int(a.level), String(a.name)] < [String(b.group), int(b.level), String(b.name)])
	return out

static func is_known(hero: HeroData, r: Dictionary) -> bool:
	return bool(r.get("known", false)) or hero.known_recipes.has(StringName(r.id))

## The scroll that teaches a recipe (base id), or &"" when it is known from the start.
static func scroll_for(recipe_id: StringName) -> StringName:
	for s in DataCrafting.SCROLLS:
		if s[1] == recipe_id:
			return s[0]
	return &""

static func is_gear(r: Dictionary) -> bool:
	return (r.out as Dictionary).has("gear")

## How many times the hero could make this right now (materials and gold; ignores bag space).
static func max_craftable(hero: HeroData, r: Dictionary) -> int:
	var n := MAX_BATCH
	for inp in r.inputs:
		n = mini(n, hero.inventory.count_of(inp[0]) / maxi(1, int(inp[1])))
	var fee := int(r.get("gold", 0))
	if fee > 0:
		n = mini(n, hero.inventory.gold / fee)
	return maxi(0, n)

## "" when the recipe can be made `times` times at `station`, else the reason (shown on the button / in a notice).
static func check(hero: HeroData, r: Dictionary, station: StringName, times := 1, variant := 0) -> String:
	if r.is_empty():
		return "Unknown recipe"
	if not (r.stations as Array).has(station):
		return "Needs a %s" % DataCrafting.station_names(r.stations)
	if not is_known(hero, r):
		return "Recipe not learned"
	if hero.progress.level < int(r.get("level", 1)):
		return "Requires level %d" % int(r.level)
	if times < 1 or times > MAX_BATCH:
		return "Invalid amount"
	for inp in r.inputs:
		var need := int(inp[1]) * times
		var have := hero.inventory.count_of(inp[0])
		if have < need:
			var b := DB.item_base(inp[0])
			return "Missing %s (%d / %d)" % [b.display_name if b else String(inp[0]), have, need]
	var fee := int(r.get("gold", 0)) * times
	if hero.inventory.gold < fee:
		return "Not enough gold (%d needed)" % fee
	if is_gear(r):
		var vs: Array = r.get("variants", [])
		if variant < 0 or variant >= maxi(1, vs.size()):
			return "Choose what to make"
		if pick_base(hero, r, variant, RandomNumberGenerator.new()) == null:
			return "Nothing of that kind can be made at your level"
	if not _fits(hero, r, times):
		return "Inventory is full"
	return ""

## Bag space for the results, counting cells the used-up inputs would free.
static func _fits(hero: HeroData, r: Dictionary, times: int) -> bool:
	var inv := hero.inventory
	var freed := 0
	for inp in r.inputs:
		var need := int(inp[1]) * times
		for c in inv.cells:
			if c != null and c.base.id == inp[0] and c.count <= need:
				need -= c.count
				freed += 1
	var free := inv.free_cells() + freed
	if is_gear(r):
		return free >= times
	var out: Dictionary = r.out
	var b := DB.item_base(out.base)
	if b == null:
		return false
	var total := int(out.get("count", 1)) * times
	var room := 0
	for c in inv.cells:
		if c != null and c.base.id == b.id and c.rarity == BH.Rarity.COMMON:
			room += b.stack_max - c.count
	return total <= room + free * b.stack_max

## The base a gear recipe makes for this hero: among bases of the chosen kind that the hero's level allows, the most
## advanced ones (highest level requirement), preferring the hero's class. Set pieces and uniques are never crafted.
static func pick_base(hero: HeroData, r: Dictionary, variant: int, rng: RandomNumberGenerator) -> ItemBaseDef:
	var vs: Array = r.get("variants", [])
	if vs.is_empty():
		return null
	var v: Dictionary = vs[clampi(variant, 0, vs.size() - 1)]
	var cats: Array = v.get("categories", [])
	var wts: Array = v.get("weapon_types", [])
	var lvl := hero.progress.level
	var pool := []
	var best := -1
	for b: ItemBaseDef in DB.item_bases.values():
		if not cats.has(b.category) or b.set_id != &"" or b.unique_name != "" or b.drop_weight <= 0 or b.level_req > lvl:
			continue
		if not wts.is_empty() and not wts.has(b.weapon_type):
			continue
		pool.append(b)
		best = maxi(best, b.level_req)
	if pool.is_empty():
		return null
	# the best tier the hero can wear: bases within 4 levels of the highest requirement found
	pool = pool.filter(func(b): return b.level_req >= best - 4)
	var mine := pool.filter(func(b): return b.class_hint == hero.cls.id)
	if not mine.is_empty():
		pool = mine
	pool.sort_custom(func(a, b): return String(a.id) < String(b.id))
	return pool[rng.randi_range(0, pool.size() - 1)]

## Make the recipe `times` times. Returns {ok, error, items: [ItemInstance], gold}. Nothing changes when it fails.
static func craft(hero: HeroData, r: Dictionary, station: StringName, times := 1, variant := 0, rng: RandomNumberGenerator = null) -> Dictionary:
	var err := check(hero, r, station, times, variant)
	if err != "":
		return {"ok": false, "error": err}
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	var made := []
	var out: Dictionary = r.out
	for i in times:
		if is_gear(r):
			var g: Dictionary = out.gear
			var base := pick_base(hero, r, variant, rng)
			var ilvl := hero.progress.level + int(g.get("ilvl_bonus", 0))
			var child := RandomNumberGenerator.new()
			child.seed = rng.randi() | 1
			var it := ItemGenerator.generate(base, ilvl, int(g.rarity), child)
			var q: Array = g.get("quality", [0.0, 0.0])
			it.quality = maxf(it.quality, snappedf(rng.randf_range(float(q[0]), float(q[1])), 0.01))
			it.crafted = true
			made.append(it)
		else:
			var it2 := DB.make_item(out.base, BH.Rarity.COMMON, hero.progress.level, rng.randi() | 1)
			it2.count = int(out.get("count", 1))
			made.append(it2)
	for inp in r.inputs:
		hero.inventory.consume(inp[0], int(inp[1]) * times)
	var fee := int(r.get("gold", 0)) * times
	hero.inventory.gold -= fee
	for it in made:
		hero.inventory.add(it)
	hero.crafted_count += times
	hero.inventory.changed.emit()
	Events.item_crafted.emit(StringName(r.id), made)
	return {"ok": true, "items": made, "gold": fee}

## Use a recipe scroll: "" when learned (the scroll is then consumed by the caller), else why not.
static func learn(hero: HeroData, recipe_id: StringName) -> String:
	var r := DataCrafting.recipe(recipe_id)
	if r.is_empty():
		return "This recipe is unreadable"
	if is_known(hero, r):
		return "You already know how to make %s" % r.name
	hero.known_recipes[StringName(recipe_id)] = true
	Events.recipe_learned.emit(StringName(recipe_id))
	return ""

## Salvage: an unprotected piece of equipment from the bag becomes materials. Returns {ok, error, items}.
static func salvage(hero: HeroData, it: ItemInstance) -> Dictionary:
	if it == null or hero.inventory.index_of(it) < 0:
		return {"ok": false, "error": "Item not in your bag"}
	if not it.is_equipment():
		return {"ok": false, "error": "Only weapons, armor and accessories can be salvaged"}
	if it.is_protected():
		return {"ok": false, "error": "Item is locked"}
	var yields := DataCrafting.salvage_yield(it)
	var new_stacks := 0
	for y in yields:
		var room := false
		for c in hero.inventory.cells:
			if c != null and c.base.id == y[0] and c.count + int(y[1]) <= c.base.stack_max:
				room = true
		new_stacks += 0 if room else 1
	if new_stacks > hero.inventory.free_cells() + 1:
		return {"ok": false, "error": "Inventory is full"}
	var got := []
	for y in yields:
		var m := DB.make_item(y[0], BH.Rarity.COMMON, it.ilvl, 1)
		m.count = int(y[1])
		got.append(m)
	hero.inventory.remove_item(it)
	for m in got:
		hero.inventory.add(m)
	hero.inventory.changed.emit()
	return {"ok": true, "items": got}
