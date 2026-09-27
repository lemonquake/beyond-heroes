extends Node
## Writes every item base (id, category, type, tier, element ...) to tools/blender/items/items.json for the Blender
## item-model pipeline (tools/blender/items/build_items.py). A scene (not -s) because item bases use autoloads:
##   godot --headless --path game res://tests/tools/dump_items.tscn
func _ready() -> void:
	var out := []
	for b: ItemBaseDef in DataItems.bases():
		out.append({"id": String(b.id), "name": b.display_name, "category": String(b.category), "weapon_type": String(b.weapon_type),
			"weight_class": String(b.weight_class), "tier": b.tier, "element": b.element, "element_share": b.element_share,
			"icon": b.icon.get_file().get_basename(), "icon_path": b.icon, "set_id": String(b.set_id), "unique": b.unique_name, "level": b.level_req,
			"effect": b.consumable_effect.keys(), "weight": b.weight, "aps": b.attacks_per_second, "defense": b.defense})
	var path := ProjectSettings.globalize_path("res://").path_join("../tools/blender/items/items.json")
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(out, "  "))
	f.close()
	print("DUMP %d item bases -> %s" % [out.size(), path])
	get_tree().quit()
