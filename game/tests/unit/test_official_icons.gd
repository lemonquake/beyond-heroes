extends TestCase
## Coverage and identity checks for the shipped painted set. Requires packaged assets and Godot import first.

func _init() -> void:
	strict = true

func _texture_path(texture: Texture2D) -> String:
	return texture.resource_path if texture != null else ""

func test_every_manifest_route_loads_painted_art() -> void:
	var manifest := OfficialIcons.manifest()
	ok(not manifest.is_empty(), "official artwork manifest is present")
	var routes: Dictionary = manifest.get("routes", {})
	ok(not routes.is_empty(), "manifest contains routes")
	for source in routes:
		var target := String(routes[source])
		ok(target.begins_with("res://assets/ui/official/") and target.ends_with(".png"), "%s points to packaged painted artwork" % source)
		ok(ResourceLoader.exists(target), "%s is imported" % target)
		var texture := UIArt.tex(source)
		eq(_texture_path(texture), target, "shared texture lookup follows %s" % source)
		if texture:
			eq(texture.get_size(), Vector2(256, 256), "%s has standard icon dimensions" % target)
	for category in ["skills", "items", "talents", "status", "ui", "attributes", "elements", "classes"]:
		var directory: String = "res://assets/ui/icons/" + category
		for file in DirAccess.get_files_at(directory):
			if file.ends_with(".svg"):
				ok(routes.has(directory.path_join(file)), "all legacy routes are covered, including %s" % file)
	done()

func test_hero_and_tempo_skills_have_unique_own_identities() -> void:
	var seen := {}
	for id in DB.skills:
		var expected := "res://assets/ui/official/skills/%s.png" % id
		eq(OfficialIcons.identity("skills", String(id)), expected, "%s has its own identity route" % id)
		var path := _texture_path(UIArt.skill_icon(id))
		eq(path, expected, "%s resolves its own artwork" % id)
		ok(not seen.has(path), "%s does not share a different skill's artwork" % id)
		seen[path] = true
	for id in DataTempos.SKILLS:
		var expected := "res://assets/ui/official/skills/tempo_%s.png" % id
		eq(OfficialIcons.identity("tempo_skills", String(id)), expected, "%s has its own Tempo identity route" % id)
		var path := _texture_path(DataTempos.skill_icon(id))
		eq(path, expected, "%s bypasses the old kin-skill fallback" % id)
		ok(not seen.has(path), "%s does not reuse another skill's artwork" % id)
		seen[path] = true
	var aliases := {&"gravity_pull": &"arcane_surge", &"spike_tentacle": &"stone_spear", &"dark_arts": &"shadow_curse", &"mana_siphon": &"radiant_ward"}
	for alias in aliases:
		ok(_texture_path(UIArt.skill_icon(alias)) != _texture_path(UIArt.skill_icon(aliases[alias])), "%s is distinct from its former reused symbol" % alias)
	done()

func test_every_item_and_tree_node_resolves_without_svg() -> void:
	for id in DB.item_bases:
		var base: ItemBaseDef = DB.item_bases[id]
		var path := base.icon_path()
		ok(ResourceLoader.exists(path), "%s has an imported item icon" % id)
		ok(path.ends_with(".png"), "%s uses painted or rendered item art" % id)
	for id in DB.trees:
		for node in DB.trees[id].nodes:
			var texture := UIArt.node_icon(node)
			var path := _texture_path(texture)
			ok(path.ends_with(".png"), "%s.%s resolves painted tree art" % [id, node.id])
			if String(node.get("kind", "")) == "skill":
				eq(path, OfficialIcons.identity("skills", String(node.get("skill", node.id))), "main skill node preserves its identity")
			elif String(node.get("icon", "")) != "":
				eq(path, OfficialIcons.path(String(node.icon)), "side node retains its authored symbol")
	done()

func test_advanced_classes_signatures_and_weapon_upgrades_are_present() -> void:
	for id in DataTranscendence.CLASSES:
		var path := _texture_path(UIArt.icon("classes", String(id)))
		eq(path, "res://assets/ui/official/classes/%s.png" % id, "%s has an advanced class crest" % id)
	for id in DataTranscendence.SIGNATURES:
		var path := OfficialIcons.identity("signatures", String(id))
		eq(path, "res://assets/ui/official/traits/%s.png" % id, "%s has signature trait art" % id)
		ok(ResourceLoader.exists(path), "%s signature is imported" % id)
	for table in [{"prefix": "enchant_", "ids": DataUpgrades.enchant_ids()}, {"prefix": "tech_", "ids": DataUpgrades.tech_ids()}]:
		for id in table.ids:
			var key: String = table.prefix + String(id)
			var path := OfficialIcons.identity("upgrades", key)
			eq(path, "res://assets/ui/official/upgrades/%s.png" % key, "%s has upgrade artwork" % key)
			ok(ResourceLoader.exists(path), "%s upgrade is imported" % key)
	done()

func test_status_elements_and_attributes_use_the_live_painted_lookup() -> void:
	for id in StatusRules.DEFS:
		if StatusRules.is_hidden(id):
			continue
		var texture := UIArt.status_icon(id)
		ok(texture != null and _texture_path(texture).ends_with(".png"), "%s visible status has painted art" % id)
	for index in Elements.COUNT:
		var texture := UIArt.element_icon(index)
		ok(texture != null and _texture_path(texture).begins_with("res://assets/ui/official/"), "%s element uses official art" % Elements.NAMES[index])
	for id in BH.ATTRIBUTE_ICONS:
		var texture := UIArt.attribute_icon(id)
		ok(texture != null and _texture_path(texture).begins_with("res://assets/ui/official/"), "%s attribute uses official art" % id)
	done()

func test_preserved_equipment_is_unchanged() -> void:
	var retained: Dictionary = OfficialIcons.manifest().get("retained_artifacts", {})
	ok(not retained.is_empty(), "retained item renders have a recorded baseline")
	for path in retained:
		ok(ResourceLoader.exists(path), "retained render exists: %s" % path)
		# Original PNG bytes are available in the source checkout; release packs contain the imported texture instead.
		if FileAccess.file_exists(path):
			eq(FileAccess.get_sha256(path), String(retained[path].sha256), "retained source bytes unchanged: %s" % path)
	for id in DB.item_bases:
		var base: ItemBaseDef = DB.item_bases[id]
		if retained.has(base.icon):
			eq(base.icon_path(), base.icon, "%s retains its model-matching artwork" % id)
	done()

func test_border_center_has_real_transparency() -> void:
	var frame := IconBorders.DEFAULT.texture()
	ok(frame != null, "official default frame is imported")
	if frame == null:
		done()
		return
	var image := frame.get_image()
	ok(image != null, "frame has readable image data")
	if image == null:
		done()
		return
	if image.is_compressed():
		image.decompress()
	var start := Vector2i(image.get_size() * 0.25)
	var end := Vector2i(image.get_size() * 0.75)
	var max_alpha := 0.0
	for y in range(start.y, end.y):
		for x in range(start.x, end.x):
			max_alpha = maxf(max_alpha, image.get_pixel(x, y).a)
	# The one-bit alpha allowance accommodates PNG feathering while rejecting an opaque checkerboard or matte.
	ok(max_alpha <= 1.0 / 255.0 + 0.00001, "every pixel across the central opening is transparent")
	done()
