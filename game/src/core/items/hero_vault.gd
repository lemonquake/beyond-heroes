class_name HeroVault
extends RefCounted
## bh-019: the Hero's Vault — storage shared by every hero on this computer (all save slots). It starts with 32
## slots and can be enlarged at the vault itself: 64 slots for 2,500 gold, then 128 for 8,000 (paid by the hero who
## is there). Stored in user://saves/vault.json beside the hero saves, written the same careful way (a checked new
## file replaces the old one, the old one kept as .bak). Probes and tests (save slots 90+) use their own vault file,
## so they can never touch the player's.
##
## Every deposit or withdrawal also saves the hero straight away (see VaultWindow), so an item is never in both the
## vault and a hero's save, or in neither, after a crash.

const SIZES := [32, 64, 128]
const UPGRADE_COST := [2500, 8000]      # to go from SIZES[i] to SIZES[i + 1]
const PATH := "user://saves/vault.json"
const PROBE_PATH := "user://saves/vault_probe.json"
const VERSION := 1

static var _shared: HeroVault

var level := 0                          # index into SIZES
var cells: Array = []                   # ItemInstance or null
var path := PATH

signal changed

static func path_for_slot(slot: int) -> String:
	return PROBE_PATH if slot >= 90 else PATH

## The vault of this computer (loaded once, reloaded when the save-slot family changes).
static func shared() -> HeroVault:
	var p := path_for_slot(Game.save_slot)
	if _shared == null or _shared.path != p:
		_shared = HeroVault.load_from(p)
	return _shared

static func forget() -> void:
	_shared = null

func _init() -> void:
	cells.resize(SIZES[0])

func capacity() -> int:
	return cells.size()

func used() -> int:
	var n := 0
	for c in cells:
		if c != null:
			n += 1
	return n

func next_cost() -> int:
	return UPGRADE_COST[level] if level < UPGRADE_COST.size() else 0

func next_size() -> int:
	return SIZES[level + 1] if level + 1 < SIZES.size() else capacity()

## Buy the next vault size with the hero's gold. Returns "" or why not.
func upgrade(hero: HeroData) -> String:
	if level >= UPGRADE_COST.size():
		return "The vault is as large as it gets."
	var cost := next_cost()
	if hero == null or hero.inventory.gold < cost:
		return "Not enough gold (%d needed)." % cost
	hero.inventory.gold -= cost
	level += 1
	cells.resize(SIZES[level])
	hero.inventory.changed.emit()
	changed.emit()
	return ""

## Why an item cannot go in the vault ("" when it can).
static func refuse_reason(it: ItemInstance) -> String:
	if it == null:
		return "Nothing there."
	if it.base.is_quest():
		return "Quest items stay with the hero who carries them."
	return ""

## Move an item from the hero's bag into the vault (stacks merge). Returns "" or why not.
func deposit(hero: HeroData, it: ItemInstance, at := -1) -> String:
	var why := refuse_reason(it)
	if why != "":
		return why
	if hero.inventory.index_of(it) < 0:
		return "That is not in your bag."
	if it.base.is_stackable():
		for c in cells:
			if c != null and c.stacks_with(it) and c.count < c.base.stack_max:
				var moved := mini(it.count, c.base.stack_max - c.count)
				c.count += moved
				it.count -= moved
				if it.count <= 0:
					break
		if it.count <= 0:
			hero.inventory.remove_item(it)
			changed.emit()
			return ""
	var idx := at if at >= 0 and at < cells.size() and cells[at] == null else cells.find(null)
	if idx < 0:
		hero.inventory.changed.emit()
		changed.emit()
		return "The vault is full."
	hero.inventory.remove_item(it)
	cells[idx] = it
	changed.emit()
	return ""

## Move a vault item into the hero's bag. Returns "" or why not.
func withdraw(hero: HeroData, idx: int) -> String:
	if idx < 0 or idx >= cells.size() or cells[idx] == null:
		return "That slot is empty."
	var it: ItemInstance = cells[idx]
	if not hero.inventory.can_fit(it):
		return "Your bag is full."
	cells[idx] = null
	var left := hero.inventory.add(it)
	if left > 0:
		# part of a stack did not fit: it stays in the vault
		cells[idx] = it
	changed.emit()
	return "" if left == 0 else "Your bag is full: %d stayed in the vault." % left

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

func sort() -> void:
	var items := cells.filter(func(c): return c != null)
	items.sort_custom(func(x: ItemInstance, y: ItemInstance) -> bool:
		if x.rarity != y.rarity:
			return x.rarity > y.rarity
		if x.base.category != y.base.category:
			return String(x.base.category) < String(y.base.category)
		return x.display_name() < y.display_name())
	for i in cells.size():
		cells[i] = items[i] if i < items.size() else null
	changed.emit()

# ---- storage --------------------------------------------------------------------------------------------------

func to_dict() -> Dictionary:
	var arr := []
	for i in cells.size():
		if cells[i] != null:
			var d: Dictionary = (cells[i] as ItemInstance).to_dict()
			d["slot"] = i
			arr.append(d)
	return {"version": VERSION, "level": level, "items": arr, "saved_at": int(Time.get_unix_time_from_system())}

static func from_dict(d: Dictionary, p := PATH) -> HeroVault:
	var v := HeroVault.new()
	v.path = p
	v.level = clampi(int(d.get("level", 0)), 0, SIZES.size() - 1)
	v.cells.resize(SIZES[v.level])
	for e in d.get("items", []):
		if not (e is Dictionary):
			continue
		var it := ItemInstance.from_dict(e)
		if it == null:
			continue
		var i := int(e.get("slot", -1))
		if i < 0 or i >= v.cells.size() or v.cells[i] != null:
			i = v.cells.find(null)
		if i >= 0:
			v.cells[i] = it
	return v

static func _valid(d) -> bool:
	return d is Dictionary and d.has("level") and d.get("items") is Array

static func load_from(p := PATH) -> HeroVault:
	for f in [p, p + ".bak", p + ".tmp"]:
		if not FileAccess.file_exists(f):
			continue
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(f))
		if _valid(parsed):
			if f != p:
				push_warning("Vault restored from %s" % f.get_file())
			return from_dict(parsed, p)
		push_warning("Unreadable vault file %s" % f)
	var v := HeroVault.new()
	v.path = p
	return v

## Write the vault without ever leaving it unreadable (same scheme as SaveSystem.save_hero).
func save() -> bool:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		push_error("Cannot write the vault: %s" % FileAccess.get_open_error())
		return false
	var data := to_dict()
	f.store_string(JSON.stringify(data, "  "))
	f.close()
	var back = JSON.parse_string(FileAccess.get_file_as_string(tmp))
	if not _valid(back) or (back.items as Array).size() != (data.items as Array).size():
		push_error("Vault check failed: the previous vault is kept")
		DirAccess.remove_absolute(tmp)
		return false
	if FileAccess.file_exists(path):
		if FileAccess.file_exists(path + ".bak"):
			DirAccess.remove_absolute(path + ".bak")
		DirAccess.rename_absolute(path, path + ".bak")
	if DirAccess.rename_absolute(tmp, path) != OK:
		push_error("Cannot replace the vault file: the previous one is kept as a backup")
		if not FileAccess.file_exists(path) and FileAccess.file_exists(path + ".bak"):
			DirAccess.copy_absolute(path + ".bak", path)
		return false
	return true
