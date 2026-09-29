extends Node
## Versioned save/load (autoload `SaveSystem`). Saves are JSON in user://saves/slot_<n>.json.
## Each file: {"version": N, "saved_at": unix, "hero": {...}, "settings": {...}}.
## Older versions are upgraded step-by-step through MIGRATIONS before loading.

const CURRENT_VERSION := 4
const SAVE_DIR := "user://saves"
const SLOTS := 8

## version -> Callable(dict) -> dict  (upgrades from `version` to `version + 1`)
var MIGRATIONS := {
	1: _migrate_1_to_2,
	2: _migrate_2_to_3,
	3: _migrate_3_to_4,
}

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)

func slot_path(slot: int) -> String:
	return "%s/slot_%d.json" % [SAVE_DIR, slot]

func serialize(hero: HeroData) -> Dictionary:
	return {"version": CURRENT_VERSION, "saved_at": int(Time.get_unix_time_from_system()), "hero": hero.to_dict(),
		"settings": Settings.to_dict()}

## Write the slot without ever leaving it unreadable (bh-015): the new file is written beside the old one and read
## back; only a file that parses to this hero replaces the save, and the previous save is kept as slot_<n>.json.bak.
## A crash at any point leaves either the old save, the backup, or the checked new file.
func save_hero(hero: HeroData, slot: int) -> bool:
	if hero == null or hero.cls == null:
		return false
	var data := serialize(hero)
	var path := slot_path(slot)
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		push_error("Cannot write save: %s" % FileAccess.get_open_error())
		return false
	var text := JSON.stringify(data, "  ")
	f.store_string(text)
	f.close()
	var back = JSON.parse_string(FileAccess.get_file_as_string(tmp))
	if not _valid(back) or String(back.hero.get("name", "")) != hero.hero_name:
		push_error("Save check failed for slot %d: the previous save is kept" % slot)
		DirAccess.remove_absolute(tmp)
		return false
	if FileAccess.file_exists(path):
		if FileAccess.file_exists(path + ".bak"):
			DirAccess.remove_absolute(path + ".bak")
		DirAccess.rename_absolute(path, path + ".bak")
	if DirAccess.rename_absolute(tmp, path) != OK:
		push_error("Cannot replace save in slot %d: the previous save is kept as a backup" % slot)
		if not FileAccess.file_exists(path) and FileAccess.file_exists(path + ".bak"):
			DirAccess.copy_absolute(path + ".bak", path)
		return false
	return true

static func _valid(d) -> bool:
	return d is Dictionary and d.get("hero") is Dictionary and String(d.hero.get("class", "")) != "" and d.hero.has("progress")

## The slot's data, from the save itself or — when it is missing or unreadable — from its backup, or from a checked
## new file a crash left behind.
func read_slot(slot: int) -> Dictionary:
	for path in [slot_path(slot), slot_path(slot) + ".bak", slot_path(slot) + ".tmp"]:
		if not FileAccess.file_exists(path):
			continue
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if not _valid(parsed):
			push_warning("Corrupt save file %s" % path)
			continue
		if path != slot_path(slot):
			push_warning("Slot %d restored from %s" % [slot, path.get_file()])
		return migrate(parsed)
	return {}

func migrate(data: Dictionary) -> Dictionary:
	var v := int(data.get("version", 1))
	while v < CURRENT_VERSION:
		if not MIGRATIONS.has(v):
			push_error("No migration from save version %d" % v)
			return {}
		data = MIGRATIONS[v].call(data)
		v += 1
		data["version"] = v
	return data

func load_hero(slot: int) -> HeroData:
	var data := read_slot(slot)
	if data.is_empty():
		return null
	if data.has("settings"):
		Settings.from_dict(data["settings"])
	return HeroData.from_dict(data.get("hero", {}))

func slot_summary(slot: int) -> Dictionary:
	var data := read_slot(slot)
	if data.is_empty():
		return {}
	var h: Dictionary = data.get("hero", {})
	return {"name": h.get("name", "?"), "class": h.get("class", "?"), "level": h.get("progress", {}).get("level", 1),
		"map": h.get("map", "sanctuary"), "saved_at": data.get("saved_at", 0), "play_time": h.get("play_time", 0.0)}

func delete_slot(slot: int) -> void:
	for path in [slot_path(slot), slot_path(slot) + ".bak", slot_path(slot) + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)

# v1 stored the skill bar under "hotbar" and had no potion belt / play_time.
func _migrate_1_to_2(d: Dictionary) -> Dictionary:
	var h: Dictionary = d.get("hero", {})
	if h.has("hotbar") and not h.has("skill_bar"):
		h["skill_bar"] = h["hotbar"]
		h.erase("hotbar")
	if not h.has("play_time"):
		h["play_time"] = 0.0
	d["hero"] = h
	return d

# v2 used six rarities (Common, Magic, Rare, Epic, Legendary, Mythic); v3 uses the ten design tiers.
const V2_RARITY_MAP := [1, 3, 5, 6, 8, 9]

func _migrate_2_to_3(d: Dictionary) -> Dictionary:
	var h: Dictionary = d.get("hero", {})
	var remap := func(it):
		if it is Dictionary and it.has("rarity"):
			it["rarity"] = V2_RARITY_MAP[clampi(int(it["rarity"]), 0, V2_RARITY_MAP.size() - 1)]
	for it in h.get("inventory", []):
		remap.call(it)
	var eq: Dictionary = h.get("equipment", {})
	for k in eq:
		remap.call(eq[k])
	d["hero"] = h
	return d

# v4 separates "awakened" waypoint shrines (travel destinations) from "discovered" teleporters: v3 recorded every dais
# the hero stepped on, locked or not. Only the two original network waypoints (never locked) carry over as awakened;
# the town's own waypoint is always awakened. Discovered places and the tracked route start empty.
const V4_LEGACY_SHRINES := ["sanctuary_waypoint", "forest_waypoint"]

func _migrate_3_to_4(d: Dictionary) -> Dictionary:
	var h: Dictionary = d.get("hero", {})
	var awake := ["sanctuary_waypoint"]
	for t in h.get("teleporters", []):
		if V4_LEGACY_SHRINES.has(String(t)) and not awake.has(String(t)):
			awake.append(String(t))
	h["awakened_shrines"] = awake
	h["known_places"] = []
	h["route"] = {}
	d["hero"] = h
	return d
