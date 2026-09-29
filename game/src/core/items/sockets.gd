class_name Sockets
## bh-018: the Socket Specialist's services — pure rules over HeroData and ItemInstance (SocketWindow, dialogue, tests).
##
##   Add Socket       opens one more socket, up to the piece's tier maximum (DataCrystals.MAX_SOCKETS: 1 .. 7). Fee grows
##                    with every socket already open and with the item level.
##   Remove Socket    closes an empty socket (a socket holding a crystal must be emptied first).
##   Set Crystal      free: a crystal from the bag goes into an empty socket. It stays there until the piece is purged
##                    or crystallized — crystals are never simply pulled out.
##   Purge            breaks every crystal out of the piece: the crystals are DESTROYED, the piece and its sockets stay.
##   Crystallization  the piece is DESTROYED; every crystal set in it comes back to the bag intact.
## Every step works on a piece in the bag or worn (worn pieces update the hero's stats at once). Gold is taken exactly
## once and nothing changes when a check fails.

const ADD := &"add"
const REMOVE := &"remove"
const PURGE := &"purge"
const CRYSTALLIZE := &"crystallize"

const ADD_FEE := 400.0
const REMOVE_FEE := 200.0
const PURGE_FEE := 300.0
const CRYSTALLIZE_SHARE := 0.10       # of the crystals' shop value

static func max_sockets(it: ItemInstance) -> int:
	if it == null or not it.is_equipment():
		return 0
	return DataCrystals.MAX_SOCKETS[clampi(it.rarity, 0, DataCrystals.MAX_SOCKETS.size() - 1)]

static func filled(it: ItemInstance) -> int:
	var n := 0
	for g in it.gems:
		if String(g) != "":
			n += 1
	return n

static func first_empty(it: ItemInstance) -> int:
	for i in it.gems.size():
		if String(it.gems[i]) == "":
			return i
	return -1

static func _lvl(it: ItemInstance) -> float:
	return 1.0 + float(maxi(it.ilvl, 1)) / 20.0

static func add_fee(it: ItemInstance) -> int:
	return roundi(ADD_FEE * pow(float(it.sockets + 1), 2.0) * _lvl(it))

static func remove_fee(it: ItemInstance) -> int:
	return roundi(REMOVE_FEE * float(maxi(it.sockets, 1)) * _lvl(it))

static func purge_fee(it: ItemInstance) -> int:
	return roundi(PURGE_FEE * float(maxi(filled(it), 1)) * _lvl(it))

static func crystallize_fee(it: ItemInstance) -> int:
	var v := 0.0
	for g in it.gems:
		if String(g) != "":
			v += float(DataCrystals.price(StringName(g)))
	return maxi(100, roundi(v * CRYSTALLIZE_SHARE))

static func fee(it: ItemInstance, service: StringName) -> int:
	match service:
		ADD: return add_fee(it)
		REMOVE: return remove_fee(it)
		PURGE: return purge_fee(it)
		CRYSTALLIZE: return crystallize_fee(it)
	return 0

static func is_with(hero: HeroData, it: ItemInstance) -> bool:
	return hero.equipment.slot_of(it) != &"" or hero.inventory.index_of(it) >= 0

## Every piece of equipment the hero has: worn first, then the bag.
static func pieces(hero: HeroData) -> Array:
	var out: Array = hero.equipment.equipped_items().duplicate()
	for it in hero.inventory.cells:
		if it != null and it.is_equipment():
			out.append(it)
	return out

## The crystals in the bag that fit this piece (one entry per stack).
static func crystals_for(hero: HeroData, it: ItemInstance) -> Array:
	var out: Array = []
	for c in hero.inventory.cells:
		if c != null and c.base.category == &"crystal" and fits(c.base.id, it):
			out.append(c)
	return out

static func fits(crystal_id: StringName, it: ItemInstance) -> bool:
	var f := DataCrystals.family_of(crystal_id)
	if f == &"" or it == null or not it.is_equipment():
		return false
	return not DataCrystals.weapon_only(f) or it.base.is_weapon()

## "" when the service can be done now, else the reason.
static func check(hero: HeroData, it: ItemInstance, service: StringName) -> String:
	if it == null or not it.is_equipment():
		return "Choose a piece of equipment"
	if not is_with(hero, it):
		return "That piece is not with you"
	match service:
		ADD:
			if it.sockets >= max_sockets(it):
				return "%s pieces hold at most %d socket%s" % [it.rarity_name(), max_sockets(it), "" if max_sockets(it) == 1 else "s"]
		REMOVE:
			if it.sockets <= 0:
				return "It has no socket to close"
			if first_empty(it) < 0:
				return "Every socket holds a crystal: purge or crystallize first"
		PURGE:
			if filled(it) == 0:
				return "No crystal is set in it"
		CRYSTALLIZE:
			if filled(it) == 0:
				return "No crystal is set in it"
			if it.is_protected():
				return "It is locked: unlock it first"
			var free := hero.inventory.free_cells()
			var need := 0
			for g in it.gems:
				if String(g) != "" and not _stacks_into(hero, StringName(g)):
					need += 1
			if hero.equipment.slot_of(it) == &"":
				free += 1   # the piece itself leaves the bag
			if need > free:
				return "Not enough room in your bag for the crystals"
		_:
			return "Unknown service"
	if hero.inventory.gold < fee(it, service):
		return "Not enough gold (%d needed)" % fee(it, service)
	return ""

static func _stacks_into(hero: HeroData, crystal_id: StringName) -> bool:
	for c in hero.inventory.cells:
		if c != null and c.base.id == crystal_id and c.count < c.base.stack_max:
			return true
	return false

## Do the service. Returns {ok, error, crystals (Array of ids returned or destroyed)}.
static func apply(hero: HeroData, it: ItemInstance, service: StringName) -> Dictionary:
	var err := check(hero, it, service)
	if err != "":
		return {"ok": false, "error": err}
	var cost := fee(it, service)
	var worn := hero.equipment.slot_of(it)
	var touched: Array = []
	match service:
		ADD:
			it.sockets += 1
			it.gems.append("")
		REMOVE:
			var i := it.gems.rfind("")
			it.gems.remove_at(i)
			it.sockets -= 1
		PURGE:
			for i in it.gems.size():
				if String(it.gems[i]) != "":
					touched.append(it.gems[i])
					it.gems[i] = ""
		CRYSTALLIZE:
			for g in it.gems:
				if String(g) != "":
					touched.append(g)
			if worn != &"":
				hero.equipment.unequip(worn)
				var orphan := hero.equipment.orphaned_sub()
				if orphan != null:
					hero.equipment.unequip(&"sub_weapon")
					hero.inventory.add(orphan)
			else:
				hero.inventory.remove_item(it)
			for g in touched:
				hero.inventory.add(DB.make_item(StringName(g), BH.Rarity.COMMON, 1))
	hero.inventory.gold -= cost
	if worn != &"":
		hero.equipment.changed.emit()
	hero.inventory.changed.emit()
	return {"ok": true, "crystals": touched, "gold": cost}

## Set one crystal from the bag (taken from `stack`) into the first empty socket, or socket `index`. Free.
static func set_crystal(hero: HeroData, it: ItemInstance, stack: ItemInstance, index := -1) -> Dictionary:
	if it == null or not it.is_equipment() or not is_with(hero, it):
		return {"ok": false, "error": "Choose a piece of equipment"}
	if stack == null or stack.base.category != &"crystal" or hero.inventory.index_of(stack) < 0:
		return {"ok": false, "error": "Choose a crystal from your bag"}
	if not fits(stack.base.id, it):
		return {"ok": false, "error": "%s fits weapons only" % DataCrystals.FAMILIES[DataCrystals.family_of(stack.base.id)].name}
	var i := index if index >= 0 else first_empty(it)
	if i < 0 or i >= it.gems.size():
		return {"ok": false, "error": "No empty socket" if it.sockets > 0 else "It has no socket: a Socket Specialist can open one"}
	if String(it.gems[i]) != "":
		return {"ok": false, "error": "That socket already holds a crystal"}
	it.gems[i] = String(stack.base.id)
	if stack.count > 1:
		stack.count -= 1
	else:
		hero.inventory.remove_item(stack)
	if hero.equipment.slot_of(it) != &"":
		hero.equipment.changed.emit()
	hero.inventory.changed.emit()
	return {"ok": true, "socket": i}

## "2 / 4 sockets · Ember Shard, Nova Fragment" style summary for lists ("" when it has none).
static func summary(it: ItemInstance) -> String:
	if it.sockets <= 0:
		return ""
	var names := PackedStringArray()
	for g in it.gems:
		if String(g) != "":
			names.append(DB.item_base(StringName(g)).display_name if DB.item_base(StringName(g)) else String(g))
	return "%d / %d sockets filled%s" % [filled(it), it.sockets, (" · " + ", ".join(names)) if not names.is_empty() else ""]
