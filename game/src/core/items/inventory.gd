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
			if c != null and c.base == item.base and c.count < c.base.stack_max:
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
			if c != null and c.base == item.base:
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

const SORT_MODES := ["rarity", "type", "level", "name"]
const CATEGORY_ORDER := [&"weapon", &"shield", &"helm", &"armor", &"inner_garment", &"gloves", &"boots", &"accessory", &"consumable", &"material"]

func sort(mode: String) -> void:
	var items := []
	for c in cells:
		if c != null:
			items.append(c)
	items.sort_custom(func(a: ItemInstance, b: ItemInstance) -> bool:
		match mode:
			"rarity":
				if a.rarity != b.rarity: return a.rarity > b.rarity
			"type":
				var ca := CATEGORY_ORDER.find(a.base.category)
				var cb := CATEGORY_ORDER.find(b.base.category)
				if ca != cb: return ca < cb
			"level":
				if a.ilvl != b.ilvl: return a.ilvl > b.ilvl
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
	"materials": [&"material", &"consumable"],
}

static func matches_filter(item: ItemInstance, filter: String) -> bool:
	if item == null:
		return false
	var cats: Array = FILTERS.get(filter, [])
	return cats.is_empty() or cats.has(item.base.category)

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
