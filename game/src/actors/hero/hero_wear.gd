class_name HeroWear
extends RefCounted
## bh-023: what the hero's equipment looks like when worn. Every wearable base has a model fitted to the hero body
## (res://assets/characters/hero/wear/<base id>.glb, tools/blender/hero/hero_wear.py): skinned to the shared bones so
## it bends with the body and carrying the body's shape keys so it follows the body sliders. manifest.json says which
## parts of the body each piece covers (so skin never pokes through) and whether a helm hides the hair.
##
## Boss collections keep their authored regalia (BossSetVisuals) and get a plain under-layer in the set's cloth
## colour beneath the plates.

const DIR := "res://assets/characters/hero/wear/"
const MANIFEST := DIR + "manifest.json"
const SLOTS: Array[StringName] = [&"inner_garment", &"armor", &"helm", &"gloves_1", &"gloves_2", &"boots_1", &"boots_2",
	&"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4"]
## Left-hand / left-foot slots (the other of each pair is the right).
const LEFT := [&"gloves_1", &"boots_1", &"accessory_1", &"accessory_3"]
const UNDER_BODY := "_under_body"
const UNDER_HANDS := "_under_hands"
const UNDER_FEET := "_under_feet"
const SHOES := "_shoes"
const FAR := Vector2(9.0, 9.0)
## Boss helms that are open crowns (the hair stays).
const BOSS_HELM_KEEPS_HAIR := ["grievance_of_the_fairy", "winter_court"]

static var _manifest := {}
static var _loaded := false

static func manifest() -> Dictionary:
	if not _loaded:
		_loaded = true
		if FileAccess.file_exists(MANIFEST):
			var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
			if parsed is Dictionary:
				_manifest = parsed
	return _manifest

static func has_model(id: String) -> bool:
	return ResourceLoader.exists(DIR + id + ".glb")

## The worn model id of a base: its own, else the stand-in for its kind ("helm/heavy"), else "".
static func model_id(base: ItemBaseDef) -> String:
	if has_model(String(base.id)):
		return String(base.id)
	var fb: Dictionary = manifest().get("fallback", {})
	for key in ["%s/%s/%s" % [base.category, base.weight_class, base.class_hint], "%s/%s" % [base.category, base.weight_class],
			String(base.category)]:
		var id := String(fb.get(key, ""))
		if id != "" and has_model(id):
			return id
	return ""

static func _info(id: String) -> Dictionary:
	return (manifest().get("items", {}) as Dictionary).get(id, {})

static func _side(slot: StringName) -> String:
	if slot.begins_with("gloves") or slot.begins_with("boots") or slot.begins_with("accessory"):
		return "L" if LEFT.has(slot) else "R"
	return ""

static func _range(v: Variant) -> Vector2:
	return Vector2(float(v[0]), float(v[1])) if v is Array and (v as Array).size() == 2 else FAR

## Everything to put on for this equipment: {sig, pieces: [{id, side, tint}], hide: {...}, hide_hair}.
static func plan(equipment: Equipment, show_helm := true) -> Dictionary:
	var pieces: Array = []
	var sig: Array[String] = []
	var spans: Array = []              # covered heights of the trunk and legs
	var hide := {}
	var hide_hair := false
	var clothed := false
	var booted := {"L": false, "R": false}
	for slot in SLOTS:
		var item := equipment.get_item(slot)
		if item == null or item.base == null:
			continue
		if slot == &"helm" and not show_helm:
			sig.append("helm:hidden")
			continue
		var base := item.base
		var side := _side(slot)
		sig.append("%s:%s" % [slot, base.id])
		if BossSetVisuals.has_theme(base.set_id) and not has_model(String(base.id)):
			# regalia plates over a plain under-layer in the set's colour
			var tint := Color(String(BossSetVisuals.THEMES[String(base.set_id)][1])).darkened(0.35)
			var under := ""
			if slot == &"armor" or slot == &"inner_garment":
				under = UNDER_BODY
				clothed = true
			elif slot.begins_with("gloves"):
				under = UNDER_HANDS
			elif slot.begins_with("boots"):
				under = UNDER_FEET
				booted[side] = true
			elif slot == &"helm":
				hide_hair = hide_hair or not BOSS_HELM_KEEPS_HAIR.has(String(base.set_id))
			if under != "" and has_model(under) and not pieces.any(func(p): return p.id == under and p.side == side):
				pieces.append({"id": under, "side": side, "tint": tint})
				_cover(_info(under), side, spans, hide)
			continue
		var id := model_id(base)
		if id == "":
			continue
		var info := _info(id)
		pieces.append({"id": id, "side": side, "tint": Color(0.5, 0.2, 0.18)})
		_cover(info, side, spans, hide)
		if slot == &"armor" or slot == &"inner_garment":
			clothed = true
		elif slot.begins_with("boots"):
			booted[side] = true
		elif slot == &"helm" and String(info.get("hair", "hide")) == "hide":
			hide_hair = true
	# nobody goes to war barefoot in a coat of mail: plain shoes unless boots are worn
	if clothed and has_model(SHOES):
		for side in ["L", "R"]:
			if not booted[side]:
				pieces.append({"id": SHOES, "side": side, "tint": Color(0.2, 0.13, 0.08)})
				_cover(_info(SHOES), side, spans, hide)
				sig.append("shoe" + side)
	# the two widest covered height ranges (overlapping ones merged)
	spans.sort_custom(func(a, b): return a.x < b.x)
	var merged: Array = []
	for s: Vector2 in spans:
		if not merged.is_empty() and s.x <= (merged[-1] as Vector2).y + 0.005:
			merged[-1] = Vector2((merged[-1] as Vector2).x, maxf((merged[-1] as Vector2).y, s.y))
		else:
			merged.append(s)
	merged.sort_custom(func(a, b): return a.y - a.x > b.y - b.x)
	if merged.size() > 0:
		hide["z1"] = merged[0]
	if merged.size() > 1:
		hide["z2"] = merged[1]
	return {"sig": ",".join(sig), "pieces": pieces, "hide": hide, "hide_hair": hide_hair}

static func _cover(info: Dictionary, side: String, spans: Array, hide: Dictionary) -> void:
	var h: Dictionary = info.get("hide", {})
	for k in ["z", "z2"]:
		var r := _range(h.get(k))
		if r != FAR:
			spans.append(r)
	var sl := _range(h.get("sleeve"))
	if sl != FAR:
		var cur: Vector2 = hide.get("sleeve", FAR)
		hide["sleeve"] = sl if cur == FAR else Vector2(minf(cur.x, sl.x), maxf(cur.y, sl.y))
	for pair in [["glove", "glove_"], ["boot", "boot_"]]:
		var r := _range(h.get(pair[0]))
		if r != FAR and side != "":
			var key: String = pair[1] + side.to_lower()
			var cur: Vector2 = hide.get(key, FAR)
			hide[key] = r if cur == FAR else Vector2(minf(cur.x, r.x), maxf(cur.y, r.y))

## The meshes of one worn piece, skinned to `skeleton` (added as its children).
static func build(piece: Dictionary, skeleton: Skeleton3D) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	var path := DIR + String(piece.id) + ".glb"
	if not ResourceLoader.exists(path):
		return out
	var scene: Node = (load(path) as PackedScene).instantiate()
	var side := String(piece.get("side", ""))
	for n in scene.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if side != "" and (nm.ends_with("_L") or nm.ends_with("_R")) and not nm.ends_with("_" + side):
			continue
		mi.get_parent().remove_child(mi)
		mi.owner = null
		mi.name = "Wear_%s%s" % [piece.id, ("_" + side) if side != "" else ""]
		skeleton.add_child(mi)
		mi.skeleton = NodePath("..")
		mi.transform = Transform3D.IDENTITY
		mi.extra_cull_margin = 0.6
		out.append(mi)
	scene.free()
	MaterialLibrary.apply_character(out, piece.get("tint", Color(0.5, 0.2, 0.18)))
	return out
