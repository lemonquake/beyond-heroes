extends Node
## Runtime inventory of icon-bearing content. Deliberately observes the actual database and lookup functions.

var records: Array = []

func _record(family: String, id: String, title: String, effect: String, requested: String, resolved: String, extra := {}) -> void:
	var row := {"family": family, "id": id, "name": title, "effect": effect, "requested_path": requested,
		"resolved_path": resolved, "missing": resolved == "" or not ResourceLoader.exists(resolved),
		"fallback": requested != "" and requested != resolved}
	row.merge(extra)
	records.append(row)

func _path(texture: Texture2D) -> String:
	return texture.resource_path if texture != null else ""

func _node(n: Dictionary, tree: String) -> void:
	_record("tree_nodes", String(n.id), String(n.get("name", n.id)), String(n.get("desc", "")), String(n.get("icon", "")),
		_path(UIArt.node_icon(n)), {"tree": tree, "kind": String(n.get("kind", "")), "skill": String(n.get("skill", "")),
		"params": n.get("params", {}), "mods": n.get("mods", []), "flags": n.get("flags", {})})

func _ready() -> void:
	for id in DB.skills:
		var s: SkillDef = DB.skills[id]
		_record("skills", String(id), s.display_name, s.description, s.icon, _path(UIArt.skill_icon(id)),
			{"class_id": String(s.class_id), "element": Elements.NAMES[s.element], "behavior": String(s.behavior), "params": s.params})
	for id in DB.item_bases:
		var b: ItemBaseDef = DB.item_bases[id]
		_record("items", String(id), b.display_name, b.flavor + (" " + b.lore if b.lore != "" else ""), b.icon, b.icon_path(),
			{"category": String(b.category), "weapon_type": String(b.weapon_type), "weight_class": String(b.weight_class), "tier": b.tier,
			"element": Elements.NAMES[b.element], "consumable_effect": b.consumable_effect, "unique_name": b.unique_name, "set_id": String(b.set_id)})
	for id in DB.trees:
		for n in DB.trees[id].nodes:
			_node(n, String(id))
	for id in DataTranscendence.CLASSES:
		for n in DataTranscendenceSkills.skill_nodes(id, 0) + DataTranscendenceSkills.talent_nodes(id, 0):
			_node(n, String(id))
		var c: Dictionary = DataTranscendence.CLASSES[id]
		_record("classes", String(id), String(c.name), String(c.desc), "res://assets/ui/icons/classes/%s.svg" % id,
			_path(UIArt.icon("classes", String(id))), {"family_class": String(c.family)})
	for id in DB.classes:
		var c: ClassDef = DB.classes[id]
		_record("classes", String(id), c.display_name, c.description, "res://assets/ui/icons/classes/%s.svg" % id, _path(UIArt.icon("classes", String(id))))
	for id in DataTranscendence.SIGNATURES:
		var s: Dictionary = DataTranscendence.SIGNATURES[id]
		_record("signature_traits", String(id), String(s.name), DataTranscendence.signature_text(id), "", _path(UIArt.icon("traits", String(id))))
	for id in DB.weapon_types:
		var w: WeaponTypeDef = DB.weapon_types[id]
		_record("weapon_types", String(id), w.display_name, w.description, w.icon, w.icon,
			{"two_handed": w.two_handed, "ranged": w.ranged})
	for id in StatusRules.DEFS:
		var s: Dictionary = StatusRules.DEFS[id]
		if s.get("hidden", false):
			continue
		_record("status", String(id), String(s.get("name", id)), String(s.get("desc", "")), StatusRules.icon_of(id), _path(UIArt.status_icon(id)),
			{"icon_id": String(s.get("icon", "")), "item_id": String(s.get("item", ""))})
	for id in DataTempos.SKILLS:
		var s: Dictionary = DataTempos.SKILLS[id]
		_record("tempo_skills", String(id), String(s.get("name", id)), String(s.get("desc", "")), "res://assets/ui/icons/skills/tempo_%s.svg" % id,
			_path(DataTempos.skill_icon(id)), {"kind": String(s.get("kind", "")), "data": s})
	for id in DataTempos.CLASSES:
		var c: Dictionary = DataTempos.CLASSES[id]
		_record("tempo_classes", String(id), String(c.name), String(c.desc), "res://assets/ui/icons/classes/tempo_%s.svg" % id, _path(DataTempos.class_icon(id)))
	for table in [{"kind": "enchant", "defs": DataUpgrades.ENCHANTS}, {"kind": "tech", "defs": DataUpgrades.TECHS}]:
		for id in table.defs:
			var u: Dictionary = table.defs[id]
			_record("upgrades", "%s_%s" % [table.kind, id], String(u.name), String(u.text), "", _path(UIArt.icon("upgrades", "%s_%s" % [table.kind, id])), {"kind": table.kind, "data": u})
	for i in Elements.NAMES.size():
		_record("elements", String(Elements.NAMES[i]).to_lower(), Elements.NAMES[i], Elements.IDENTITY[i], "", _path(UIArt.element_icon(i)))
	for id in BH.ATTRIBUTE_ICONS:
		_record("attributes", String(id), String(BH.ATTRIBUTE_ICONS[id]), "Hero attribute", "", _path(UIArt.attribute_icon(id)))
	_scan_ui("res://assets/ui/icons/ui")
	var counts := {}
	var missing := {}
	var routes := {}
	for row in records:
		counts[row.family] = int(counts.get(row.family, 0)) + 1
		if row.missing:
			missing[row.family] = int(missing.get(row.family, 0)) + 1
		if row.resolved_path != "":
			routes[row.resolved_path] = true
	var out := {"generated_from": "live DB and UIArt on 2026-10-27", "counts": counts, "missing_counts": missing,
		"unique_resolved_routes": routes.size(), "records": records}
	var dest := ProjectSettings.globalize_path("res://../output/official-icons-20261027/catalog.json")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			dest = ProjectSettings.globalize_path(arg.substr(6))
	DirAccess.make_dir_recursive_absolute(dest.get_base_dir())
	var file := FileAccess.open(dest, FileAccess.WRITE)
	file.store_string(JSON.stringify(out, "  "))
	file.close()
	print("OFFICIAL_ICON_CATALOG ", JSON.stringify({"counts": counts, "missing_counts": missing, "unique_resolved_routes": routes.size()}))
	get_tree().quit()

func _scan_ui(folder: String) -> void:
	for file in DirAccess.get_files_at(folder):
		if file.get_extension() not in ["svg", "png"]:
			continue
		var id := file.get_basename()
		_record("ui", id, id.capitalize(), "Interface action or marker", folder.path_join(file), _path(UIArt.ui_icon(id)))
