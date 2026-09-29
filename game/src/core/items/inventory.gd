class_name Inventory
extends RefCounted
## Grid inventory (fixed capacity, one item per cell) with stacking, sorting and filtering.

signal changed

const COLUMNS := 10
const ROWS := 10
const BAG_CAPACITY := 84
const BELT_CAPACITY := 16

var cells: Array = []        # ItemInstance or null
var gold := 0
var bag_capacity: int

func _init(size := -1) -> void:
	# Explicit sizes remain ordinary grids (vaults, simulations and tests).
	bag_capacity = BAG_CAPACITY if size < 0 else size
	cells.resize(bag_capacity + (BELT_CAPACITY if size < 0 else 0))

func capacity() -> int:
	return cells.size()

func free_cells(include_belt := false) -> int:
	var n := 0
	for i in (cells.size() if include_belt else bag_capacity):
		if cells[i] == null:
			n += 1
	return n

func accepts(index: int, item: ItemInstance) -> bool:
	return index >= 0 and index < cells.size() and (item == null or index < bag_capacity or item.base.is_consumable())

func first_free(item: ItemInstance) -> int:
	# Consumables fill the reserved belt first, then overflow into the Utility Bag.
	if item != null and item.base.is_consumable():
		for i in range(bag_capacity, cells.size()):
			if cells[i] == null:
				return i
	for i in bag_capacity:
		if cells[i] == null:
			return i
	return -1

func bag_of(index: int) -> String:
	if index >= bag_capacity:
		return "belt"
	var item: ItemInstance = cells[index]
	return "gear" if item != null and item.is_equipment() else "utility"

## Adds an item, merging stacks first. Returns the leftover count that did not fit (0 = fully added).
func add(item: ItemInstance) -> int:
	if item == null:
		return 0
	if item.base.is_stackable():
		for c in cells:
			if c != null and c.stacks_with(item) and c.count < c.base.stack_max:
				var moved := mini(item.count, c.base.stack_max - c.count)
				c.count += moved
				item.count -= moved
				if item.count <= 0:
					changed.emit()
					return 0
	while item.count > 0:
		var idx := first_free(item)
		if idx < 0:
			changed.emit()
			return item.count
		if item.base.is_stackable() and item.count > item.base.stack_max:
			var part := item.clone()
			part.count = item.base.stack_max
			item.count -= item.base.stack_max
			cells[idx] = part
		else:
			cells[idx] = item
			changed.emit()
			return 0
	changed.emit()
	return 0

func can_fit(item: ItemInstance) -> bool:
	if item == null:
		return true
	var room := 0
	for i in cells.size():
		if not accepts(i, item):
			continue
		var c: ItemInstance = cells[i]
		if c == null:
			room += item.base.stack_max
		elif c.stacks_with(item):
			room += c.base.stack_max - c.count
	return room >= item.count

func put_at(index: int, item: ItemInstance) -> ItemInstance:
	if not accepts(index, item):
		return item
	var prev: ItemInstance = cells[index]
	cells[index] = item
	changed.emit()
	return prev

func take(index: int) -> ItemInstance:
	if index < 0 or index >= cells.size():
		return null
	var it: ItemInstance = cells[index]
	cells[index] = null
	if it != null:
		changed.emit()
	return it

func index_of(item: ItemInstance) -> int:
	return cells.find(item)

func remove_item(item: ItemInstance) -> bool:
	var i := cells.find(item)
	if i < 0:
		return false
	cells[i] = null
	changed.emit()
	return true

## Total carried weight of everything in the bag (stacks count every unit). Gold weighs nothing.
func weight() -> float:
	var w := 0.0
	for c in cells:
		if c != null:
			w += (c as ItemInstance).weight()
	return w

func count_of(base_id: StringName) -> int:
	var n := 0
	for c in cells:
		if c != null and c.base.id == base_id:
			n += c.count
	return n

## Consume `n` of a stackable base. Returns true if enough existed.
func consume(base_id: StringName, n := 1) -> bool:
	if count_of(base_id) < n:
		return false
	for i in cells.size():
		var c: ItemInstance = cells[i]
		if c != null and c.base.id == base_id:
			var used := mini(n, c.count)
			c.count -= used
			n -= used
			if c.count <= 0:
				cells[i] = null
			if n <= 0:
				break
	changed.emit()
	return true

const SORT_MODES := ["rarity", "type", "level", "name", "value", "weight"]
const CATEGORY_ORDER := [&"weapon", &"shield", &"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"accessory",
	&"consumable", &"material", &"crystal", &"quest"]

## Compacts and sorts the grid. Favorites always come first; locked items keep their relative order within a group.
func sort(mode: String, ascending := false) -> void:
	_sort_range(mode, ascending, 0, bag_capacity)
	_sort_range(mode, ascending, bag_capacity, cells.size())
	changed.emit()

func _sort_range(mode: String, ascending: bool, start: int, end: int) -> void:
	var items := []
	for i in range(start, end):
		var c: ItemInstance = cells[i]
		if c != null:
			items.append(c)
	items.sort_custom(func(a: ItemInstance, b: ItemInstance) -> bool:
		if a.favorite != b.favorite:
			return a.favorite
		match mode:
			"rarity":
				if a.rarity != b.rarity: return (a.rarity < b.rarity) if ascending else (a.rarity > b.rarity)
			"type":
				var ca := CATEGORY_ORDER.find(a.base.category)
				var cb := CATEGORY_ORDER.find(b.base.category)
				if ca != cb: return (ca > cb) if ascending else (ca < cb)
			"level":
				if a.ilvl != b.ilvl: return (a.ilvl < b.ilvl) if ascending else (a.ilvl > b.ilvl)
			"value":
				var va := a.base_value()
				var vb := b.base_value()
				if va != vb: return (va < vb) if ascending else (va > vb)
			"weight":
				if a.weight() != b.weight(): return (a.weight() < b.weight()) if ascending else (a.weight() > b.weight())
			"name":
				pass
		var na := a.display_name()
		var nb := b.display_name()
		if na != nb: return (na > nb) if mode == "name" and ascending else (na < nb)
		return a.uid < b.uid)
	for i in range(start, end):
		cells[i] = items[i - start] if i - start < items.size() else null

const FILTERS := {
	"all": [],
	"weapons": [&"weapon", &"shield"],
	"armor": [&"helm", &"armor", &"inner_garment", &"gloves", &"boots"],
	"accessories": [&"accessory"],
	"consumables": [&"consumable"],
	"materials": [&"material", &"crystal"],
	"quest": [&"quest"],
	"potions": [&"consumable"],
	"scrolls": [&"consumable"],
	"keys": [&"quest"],
}
const TABS := ["all", "weapons", "armor", "accessories", "materials", "potions", "scrolls", "keys", "consumables"]
const FILTER_NAMES := {"all": "All", "weapons": "Weapons", "armor": "Armor", "accessories": "Accessories",
	"consumables": "Consumables", "materials": "Ingredients", "quest": "Quest", "potions": "Potions", "scrolls": "Scrolls", "keys": "Keys & Quest"}

static func is_scroll(item: ItemInstance) -> bool:
	return item.base.is_consumable() and (String(item.base.id).contains("scroll") or item.base.id == &"town_portal" or item.base.consumable_effect.has("learn_recipe"))

static func is_potion(item: ItemInstance) -> bool:
	var id := String(item.base.id)
	return item.base.is_consumable() and not is_scroll(item) and (id.contains("potion") or id.contains("elixir") or id.contains("tonic") or id.contains("draught") or id.contains("brew") or id.contains("infusion"))

## Category filter + optional minimum rarity + free-text search on name, base name and enchantment text.
static func matches_filter(item: ItemInstance, filter: String, min_rarity := 0, search := "") -> bool:
	if item == null:
		return false
	var cats: Array = FILTERS.get(filter, [])
	if not cats.is_empty() and not cats.has(item.base.category):
		return false
	if filter == "scrolls" and not is_scroll(item):
		return false
	if filter == "potions" and not is_potion(item):
		return false
	if item.rarity < min_rarity:
		return false
	if search.strip_edges() != "":
		var q := search.strip_edges().to_lower()
		var hay := (item.display_name() + " " + item.base.display_name + " " + item.rarity_name() + " " + " ".join(item.affix_lines())).to_lower()
		if hay.find(q) < 0:
			return false
	return true

## Split `amount` off a stack into a free cell. Returns the new stack (or null if impossible).
func split(index: int, amount: int) -> ItemInstance:
	if index < 0 or index >= cells.size():
		return null
	var src: ItemInstance = cells[index]
	if src == null or not src.base.is_stackable() or amount <= 0 or amount >= src.count:
		return null
	var free := first_free(src)
	if free < 0:
		return null
	var part := src.clone()
	part.locked = false
	part.favorite = false
	part.count = amount
	src.count -= amount
	cells[free] = part
	changed.emit()
	return part

## Merge the stack at `from` into the stack at `to` when compatible; otherwise swap the two cells.
func move(from: int, to: int) -> void:
	if from == to or from < 0 or to < 0 or from >= cells.size() or to >= cells.size():
		return
	var a: ItemInstance = cells[from]
	var b: ItemInstance = cells[to]
	if not accepts(to, a) or not accepts(from, b):
		return
	if a != null and b != null and a.stacks_with(b) and b.count < b.base.stack_max:
		var moved := mini(a.count, b.base.stack_max - b.count)
		b.count += moved
		a.count -= moved
		if a.count <= 0:
			cells[from] = null
	else:
		cells[from] = b
		cells[to] = a
	changed.emit()

## Destroy an item (UI asks for confirmation first). Protected items refuse.
func destroy(item: ItemInstance) -> bool:
	if item == null or item.is_protected():
		return false
	return remove_item(item)

func junk_items() -> Array:
	var out := []
	for c in cells:
		if c != null and c.junk and not c.is_protected() and c.base.sellable:
			out.append(c)
	return out

func to_array() -> Array:
	var out := []
	for c in cells:
		out.append(c.to_dict() if c != null else null)
	return out

func from_array(arr: Array) -> void:
	for i in cells.size():
		cells[i] = null
	for i in mini(arr.size(), cells.size()):
		if arr[i] is Dictionary:
			cells[i] = ItemInstance.from_dict(arr[i])
	# Older saves had only general bag slots. Move consumables into the new belt
	# without changing their stack, identity, flags or the position of other items.
	if arr.size() <= bag_capacity and cells.size() > bag_capacity:
		for i in bag_capacity:
			var item: ItemInstance = cells[i]
			if item != null and item.base.is_consumable():
				var dest := first_free(item)
				if dest >= bag_capacity:
					cells[dest] = item
					cells[i] = null
	changed.emit()

## Independent copy for transactional space checks; never consumes the real items.
func copy() -> Inventory:
	var out := Inventory.new(cells.size())
	out.bag_capacity = bag_capacity
	out.from_array(to_array())
	return out
