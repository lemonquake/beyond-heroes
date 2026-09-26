extends Node
## Versioned save/load (autoload `SaveSystem`). Saves are JSON in user://saves/slot_<n>.json.
## Each file: {"version": N, "saved_at": unix, "hero": {...}, "settings": {...}}.
## Older versions are upgraded step-by-step through MIGRATIONS before loading.

const CURRENT_VERSION := 4
const SAVE_DIR := "user://saves"
const SLOTS := 3

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

func save_hero(hero: HeroData, slot: int) -> bool:
	var data := serialize(hero)
	var tmp := slot_path(slot) + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		push_error("Cannot write save: %s" % FileAccess.get_open_error())
		return false
	f.store_string(JSON.stringify(data, "  "))
	f.close()
	# Atomic-ish replace so a crash mid-write never corrupts the previous save.
	if FileAccess.file_exists(slot_path(slot)):
		DirAccess.remove_absolute(slot_path(slot))
	DirAccess.rename_absolute(tmp, slot_path(slot))
	return true

func read_slot(slot: int) -> Dictionary:
	if not FileAccess.file_exists(slot_path(slot)):
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(slot_path(slot)))
	if not parsed is Dictionary:
		push_warning("Corrupt save in slot %d" % slot)
		return {}
	return migrate(parsed)

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
	if FileAccess.file_exists(slot_path(slot)):
		DirAccess.remove_absolute(slot_path(slot))

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
