class_name WeaponUpgrades
## Weapon upgrades (bh-017): Enchantment at an Alchemy Table and Fore-Tech at a Forge — see DataUpgrades. Pure rules over
## HeroData and ItemInstance: what a step costs, whether it can be done here and now, and doing it (materials and gold
## taken exactly once, the weapon changed in place, wherever it is — in the bag or in a hand slot).

const ENCHANT := &"enchant"
const FORETECH := &"foretech"

## The station each kind of upgrade needs.
static func station_for(kind: StringName) -> StringName:
	return &"alchemy" if kind == ENCHANT else &"forge"

static func kind_name(kind: StringName) -> String:
	return "Enchantment" if kind == ENCHANT else "Fore-Tech"

static func current_id(it: ItemInstance, kind: StringName) -> StringName:
	return it.enchant if kind == ENCHANT else it.foretech

static func current_rank(it: ItemInstance, kind: StringName) -> int:
	if current_id(it, kind) == &"":
		return 0
	return it.enchant_rank if kind == ENCHANT else it.foretech_rank

static func max_rank(kind: StringName) -> int:
	return DataUpgrades.ENCHANT_MAX if kind == ENCHANT else DataUpgrades.TECH_MAX

## The rank the weapon would have after applying `id`: one more if it already carries `id`, else 1 (a new type starts over).
static func next_rank(it: ItemInstance, kind: StringName, id: StringName) -> int:
	return current_rank(it, kind) + 1 if current_id(it, kind) == id else 1

## {inputs [[base id, n]], gold, level} of applying `id` to `it` now.
static func cost(it: ItemInstance, kind: StringName, id: StringName) -> Dictionary:
	var r := next_rank(it, kind, id)
	return DataUpgrades.enchant_cost(id, r) if kind == ENCHANT else DataUpgrades.tech_cost(r)

## Every weapon the hero could upgrade: the two hand slots first, then the bag.
static func weapons(hero: HeroData) -> Array:
	var out: Array = []
	for slot in [&"main_weapon", &"sub_weapon"]:
		var it: ItemInstance = hero.equipment.get_item(slot)
		if it != null and it.base.is_weapon():
			out.append(it)
	for it in hero.inventory.cells:
		if it != null and it.base.is_weapon():
			out.append(it)
	return out

static func is_equipped(hero: HeroData, it: ItemInstance) -> bool:
	return hero.equipment.slot_of(it) != &""

## "" when the step can be taken at `station`, else the reason.
static func check(hero: HeroData, it: ItemInstance, kind: StringName, id: StringName, station: StringName) -> String:
	if it == null or not it.base.is_weapon():
		return "Choose a weapon"
	if not is_equipped(hero, it) and hero.inventory.index_of(it) < 0:
		return "That weapon is not with you"
	if station != station_for(kind):
		return "Needs %s" % ("an Alchemy Table" if kind == ENCHANT else "a Forge")
	var known := DataUpgrades.ENCHANTS.has(id) if kind == ENCHANT else DataUpgrades.TECHS.has(id)
	if not known:
		return "Choose an upgrade"
	if current_id(it, kind) == id and current_rank(it, kind) >= max_rank(kind):
		return "Already at the highest rank"
	var c := cost(it, kind, id)
	if hero.progress.level < int(c.level):
		return "Requires level %d" % int(c.level)
	for inp in c.inputs:
		var have := hero.inventory.count_of(inp[0])
		if have < int(inp[1]):
			var b := DB.item_base(inp[0])
			return "Missing %s (%d / %d)" % [b.display_name if b else String(inp[0]), have, int(inp[1])]
	if hero.inventory.gold < int(c.gold):
		return "Not enough gold (%d needed)" % int(c.gold)
	return ""

## Take the step. Returns {ok, error, rank}. Nothing changes when it fails.
static func apply(hero: HeroData, it: ItemInstance, kind: StringName, id: StringName, station: StringName) -> Dictionary:
	var err := check(hero, it, kind, id, station)
	if err != "":
		return {"ok": false, "error": err}
	var c := cost(it, kind, id)
	var rank := next_rank(it, kind, id)
	for inp in c.inputs:
		hero.inventory.consume(inp[0], int(inp[1]))
	hero.inventory.gold -= int(c.gold)
	if kind == ENCHANT:
		it.enchant = id
		it.enchant_rank = rank
	else:
		it.foretech = id
		it.foretech_rank = rank
	hero.crafted_count += 1
	if is_equipped(hero, it):
		hero.equipment.changed.emit()
	hero.inventory.changed.emit()
	Events.weapon_upgraded.emit(it, kind)
	return {"ok": true, "rank": rank}

## A one-line summary for lists: "Flame Etching II" / "Whetted Edge +3" / "".
static func summary(it: ItemInstance, kind: StringName) -> String:
	var id := current_id(it, kind)
	var r := current_rank(it, kind)
	if id == &"" or r < 1:
		return ""
	if kind == ENCHANT:
		return "%s %s" % [DataUpgrades.enchant(id).name, DataUpgrades.roman(r)]
	return "%s +%d" % [DataUpgrades.tech(id).name, r]
