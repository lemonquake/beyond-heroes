extends SceneTree
## bh-023: census of wearable item bases (category x weight class x class hint, own model present).
func _initialize() -> void:
	var DBn = root.get_node("DB")
	var rows := []
	var counts := {}
	for id in DBn.item_bases:
		var b = DBn.item_bases[id]
		if not BH.CATEGORY_SLOTS.has(b.category):
			continue
		var key := "%s/%s" % [b.category, b.weapon_type if b.category == &"weapon" else b.weight_class]
		counts[key] = int(counts.get(key, 0)) + 1
		rows.append("%s|%s|%s|%s|%s|%s|lv%d|t%d|set=%s|own=%s|icon=%s" % [id, b.display_name, b.category, b.weapon_type, b.weight_class, b.class_hint, b.level_req, b.tier, b.set_id, ResourceLoader.exists("res://assets/items/%s.glb" % id), b.icon_path().get_file()])
	rows.sort()
	var f := FileAccess.open("res://../work/lemondev/bh-023/scratch/item_census.txt", FileAccess.WRITE)
	for r in rows:
		f.store_line(r)
	f.close()
	var ks := counts.keys()
	ks.sort()
	for k in ks:
		print(k, " ", counts[k])
	print("TOTAL ", rows.size())
	quit()
