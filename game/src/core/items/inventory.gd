class_name Inventory
extends RefCounted
## Grid inventory (fixed capacity, one item per cell) with stacking, sorting and filtering.

signal changed

const COLUMNS := 10
const ROWS := 6

var cells: Array = []        # ItemInstance or null
var gold := 0

func _init(capacity := COLUMNS * ROWS) -> void:
	cells.resize(capacity)

func capacity() -> int:
	return cells.size()

func free_cells() -> int:
	var n := 0
	for c in cells:
		if c == null:
			n += 1
	return n

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
		var idx := cells.find(null)
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
	if cells.find(null) >= 0:
		return true
	if item.base.is_stackable():
		var room := 0
		for c in cells:
			if c != null and c.stacks_with(item):
				room += c.base.stack_max - c.count
		return room >= item.count
	return false

func put_at(index: int, item: ItemInstance) -> ItemInstance:
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

const SORT_MODES := ["rarity", "type", "level", "name", "value"]
const CATEGORY_ORDER := [&"weapon", &"shield", &"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"accessory",
	&"consumable", &"material", &"quest"]

## Compacts and sorts the grid. Favorites always come first; locked items keep their relative order within a group.
func sort(mode: String) -> void:
	var items := []
	for c in cells:
		if c != null:
			items.append(c)
	items.sort_custom(func(a: ItemInstance, b: ItemInstance) -> bool:
		if a.favorite != b.favorite:
			return a.favorite
		match mode:
			"rarity":
				if a.rarity != b.rarity: return a.rarity > b.rarity
			"type":
				var ca := CATEGORY_ORDER.find(a.base.category)
				var cb := CATEGORY_ORDER.find(b.base.category)
				if ca != cb: return ca < cb
			"level":
				if a.ilvl != b.ilvl: return a.ilvl > b.ilvl
			"value":
				var va := a.base_value()
				var vb := b.base_value()
				if va != vb: return va > vb
			"name":
				pass
		var na := a.display_name()
		var nb := b.display_name()
		if na != nb: return na < nb
		return a.uid < b.uid)
	for i in cells.size():
		cells[i] = items[i] if i < items.size() else null
	changed.emit()

const FILTERS := {
	"all": [],
	"weapons": [&"weapon", &"shield"],
	"armor": [&"helm", &"armor", &"inner_garment", &"gloves", &"boots"],
	"accessories": [&"accessory"],
	"consumables": [&"consumable"],
	"materials": [&"material"],
	"quest": [&"quest"],
}
const FILTER_NAMES := {"all": "All", "weapons": "Weapons", "armor": "Armor", "accessories": "Accessories",
	"consumables": "Consumables", "materials": "Materials", "quest": "Quest"}

## Category filter + optional minimum rarity + free-text search on name, base name and enchantment text.
static func matches_filter(item: ItemInstance, filter: String, min_rarity := 0, search := "") -> bool:
	if item == null:
		return false
	var cats: Array = FILTERS.get(filter, [])
	if not cats.is_empty() and not cats.has(item.base.category):
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
	var free := cells.find(null)
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
	changed.emit()
