class_name HeroWear
extends RefCounted
## bh-023: what the hero's equipment looks like when worn. Every wearable base has a model fitted to the hero body
## (res://assets/characters/hero/wear/<base id>.glb, tools/blender/hero/hero_wear.py): skinned to the shared bones so
## it bends with the body and carrying the body's shape keys so it follows the body sliders. manifest.json says which
## parts of the body each piece covers (so skin never pokes through) and whether a helm hides the hair.
##
## Boss collections keep their authored regalia (BossSetVisuals) and get a plain under-layer in the set's cloth
## colour beneath the plates.
##
## bh-024: legs are their own slot. Body garments stop at the hips; the legs are covered by the Leggings, by the set
## colour's under-layer beneath boss Legguards, or — for a hero wearing a shirt or coat but no leggings — by plain
## breeches, so nobody walks out in a hauberk and bare legs. A pair of leggings carries its outer parts in separate
## meshes (tools/blender/hero/hero_wear_legs.py) that are left off where something is worn over them: the belt and
## hanging panels under any shirt or coat, thigh plates under skirts reaching below SKIRT_HIP, knee cops under robes
## reaching below SKIRT_KNEE, ankle cuffs and low wraps inside a boot.

const DIR := "res://assets/characters/hero/wear/"
const MANIFEST := DIR + "manifest.json"
const SLOTS: Array[StringName] = [&"inner_garment", &"armor", &"leggings", &"helm", &"gloves_1", &"gloves_2", &"boots_1", &"boots_2",
	&"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4"]
## Left-hand / left-foot slots (the other of each pair is the right).
const LEFT := [&"gloves_1", &"boots_1", &"accessory_1", &"accessory_3"]
const UNDER_BODY := "_under_body"
const UNDER_HANDS := "_under_hands"
const UNDER_FEET := "_under_feet"
const UNDER_LEGS := "_under_legs"
const SHOES := "_shoes"
const BREECHES := "_breeches"
const SKIRT_HIP := 0.80
const SKIRT_KNEE := 0.45
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
	var legged := false
	var legs_piece := {}
	var skirt := 9.0
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
			elif slot == &"leggings":
				under = UNDER_LEGS
				legged = true
			elif slot.begins_with("gloves"):
				under = UNDER_HANDS
			elif slot.begins_with("boots"):
				under = UNDER_FEET
				booted[side] = true
			elif slot == &"helm":
				hide_hair = hide_hair or not BOSS_HELM_KEEPS_HAIR.has(String(base.set_id))
			if under != "" and has_model(under) and not pieces.any(func(p): return p.id == under and p.side == side):
				pieces.append({"id": under, "side": side, "tint": tint, "slot": String(slot)})
				_cover(_info(under), side, spans, hide)
			continue
		var id := model_id(base)
		if id == "":
			continue
		var info := _info(id)
		var piece := {"id": id, "side": side, "tint": Color(0.5, 0.2, 0.18), "slot": String(slot)}
		pieces.append(piece)
		_cover(info, side, spans, hide)
		if slot == &"armor" or slot == &"inner_garment":
			clothed = true
			skirt = minf(skirt, float(info.get("skirt", 9.0)))
		elif slot == &"leggings":
			legged = true
			legs_piece = piece
		elif slot.begins_with("boots"):
			booted[side] = true
		elif slot == &"helm" and String(info.get("hair", "hide")) == "hide":
			hide_hair = true
	# what the leggings carry over the cloth stays off where something else is worn over it
	if not legs_piece.is_empty():
		var skip: Array[String] = []
		if clothed:
			skip.append("waist")
		if skirt < SKIRT_HIP:
			skip.append("hip")
		if skirt < SKIRT_KNEE:
			skip.append("knee")
		for sd in ["L", "R"]:
			if booted[sd]:
				skip.append("ankle_" + sd)
		legs_piece["skip"] = skip
	# nor bare-legged under one: plain breeches unless leggings are worn
	if clothed and not legged and has_model(BREECHES):
		pieces.append({"id": BREECHES, "side": "", "tint": Color(0.22, 0.17, 0.12), "slot": "leggings"})
		_cover(_info(BREECHES), "", spans, hide)
		sig.append("breeches")
	# nobody goes to war barefoot in a coat of mail: plain shoes unless boots are worn
	if (clothed or legged) and has_model(SHOES):
		for side in ["L", "R"]:
			if not booted[side]:
				pieces.append({"id": SHOES, "side": side, "tint": Color(0.2, 0.13, 0.08), "slot": "boots"})
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

## The meshes of one worn piece, skinned to `skeleton` (added as its children). piece.dye (bh-031): a persona's
## colours for the cloth, trim, leather and metal of the piece (see dye_key).
static func build(piece: Dictionary, skeleton: Skeleton3D) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	var parts := _parts(String(piece.id))
	if parts.is_empty():
		return out
	var side := String(piece.get("side", ""))
	var skip: Array = piece.get("skip", [])
	for part in parts:
		var nm: String = part[0]
		if side != "" and (nm.ends_with("_L") or nm.ends_with("_R")) and not nm.ends_with("_" + side):
			continue
		if skip.any(func(t): return nm == "wear_" + String(t)):
			continue
		var mi := MeshInstance3D.new()
		mi.mesh = part[1]
		mi.skin = part[2]
		mi.name = "Wear_%s%s" % [piece.id, ("_" + side) if side != "" else ""]
		skeleton.add_child(mi)
		mi.skeleton = NodePath("..")
		mi.extra_cull_margin = 0.6
		out.append(mi)
	MaterialLibrary.apply_character(out, piece.get("tint", Color(0.5, 0.2, 0.18)))
	var dye: Dictionary = piece.get("dye", {})
	if not dye.is_empty():
		_dye(out, dye)
	return out

## bh-031: a piece's meshes are read from its GLB once ([name, mesh, skin] each); every wearer after that gets new
## MeshInstance3Ds on the shared resources instead of instancing the scene again (a pack of 40 dressed monsters).
static var _part_cache := {}

static func _parts(id: String) -> Array:
	if _part_cache.has(id):
		return _part_cache[id]
	var parts: Array = []
	var path := DIR + id + ".glb"
	if ResourceLoader.exists(path):
		var ps := load(path) as PackedScene
		if ps:
			var scene: Node = ps.instantiate()
			for n in scene.find_children("*", "MeshInstance3D", true, false):
				var mi := n as MeshInstance3D
				parts.append([String(mi.name), mi.mesh, mi.skin])
			scene.free()
	_part_cache[id] = parts
	return parts

## Which persona colour a worn surface takes: "cloth" (the dark ones: "trim"), "leather", "metal" (a tint) or "".
const DARK_CLOTH := ["it_hw_black", "it_hw_navy"]

static func dye_key(material_name: String) -> String:
	var base := material_name.get_slice("__", 0)
	var pal := material_name.get_slice("__", 1) if "__" in material_name else ""
	if base.begins_with("BH_Cloth"):
		return "trim" if DARK_CLOTH.has(pal) else "cloth"
	if base == "BH_Leather":
		return "leather"
	if base in ["BH_Steel", "BH_DarkSteel", "BH_Mail"]:
		return "metal"
	if base in ["BH_Gold", "BH_Bronze"]:
		return "gold"
	return ""

static var _dyed := {}

static func _dye(meshes: Array[MeshInstance3D], dye: Dictionary) -> void:
	for mi in meshes:
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(i)
			var key := dye_key(src.resource_name.get_slice(".", 0) if src else "")
			if key == "" or not dye.has(key):
				continue
			var cur := mi.get_surface_override_material(i) as BaseMaterial3D
			if cur == null:
				cur = src as BaseMaterial3D
			if cur == null:
				continue
			var col := Color(String(dye[key]))
			var ck := "%d|%s|%s" % [cur.get_instance_id(), key, col.to_html(false)]
			if not _dyed.has(ck):
				var m := cur.duplicate() as BaseMaterial3D
				# metals keep their sheen and take the colour as a tint; cloth and leather take it outright
				m.albedo_color = cur.albedo_color * col if key == "metal" or key == "gold" else col
				_dyed[ck] = m
			mi.set_surface_override_material(i, _dyed[ck])

# ---- bh-031: one mesh for a persona's whole outfit -------------------------------------------------------------

## Every MeshInstance3D a dressed persona adds costs a skinning pass and a draw call per surface. A townsperson or a
## monster never changes clothes, so their pieces are baked into one skinned mesh: shape keys applied at their current
## weights, bones remapped onto one Skin, surfaces that share a material and vertex format joined. The result is cached
## by `key` and shared by every wearer with the same look and outfit (a pack of 30 bandits shares one mesh).
static var _merged := {}

static func merge(parts: Array[MeshInstance3D], skeleton: Skeleton3D, key: String) -> MeshInstance3D:
	var cached: Array = _merged.get(key, [])
	if cached.is_empty():
		cached = _merge_build(parts)
		if cached.is_empty():
			return null
		if _merged.size() > 160:
			_merged.clear()
		_merged[key] = cached
	var mi := MeshInstance3D.new()
	mi.name = "WearMerged"
	mi.mesh = cached[0]
	mi.skin = cached[1]
	skeleton.add_child(mi)
	mi.skeleton = NodePath("..")
	mi.extra_cull_margin = 0.6
	var mats: Array = cached[2]
	for i in mats.size():
		mi.set_surface_override_material(i, mats[i])
	return mi

static func _merge_build(parts: Array[MeshInstance3D]) -> Array:
	var skin := Skin.new()
	var bind_of := {}                 # bone name -> unified bind index
	var groups := {}                  # material id | format -> {mat, arrays: [...]}
	var order: Array = []
	for mi in parts:
		if mi == null or mi.mesh == null or mi.skin == null:
			return []
		var src_skin := mi.skin
		var remap := PackedInt32Array()
		for b in src_skin.get_bind_count():
			var nm := String(src_skin.get_bind_name(b))
			if nm == "":
				return []
			if not bind_of.has(nm):
				bind_of[nm] = skin.get_bind_count()
				skin.add_named_bind(nm, src_skin.get_bind_pose(b))
			remap.append(int(bind_of[nm]))
		var mesh := mi.mesh as ArrayMesh
		if mesh == null:
			return []
		var nshapes := mesh.get_blend_shape_count()
		for s in mesh.get_surface_count():
			var arr := mesh.surface_get_arrays(s)
			var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			if nshapes > 0:
				var base_v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
				var shapes := mesh.surface_get_blend_shape_arrays(s)
				for k in nshapes:
					var w := mi.get_blend_shape_value(k)
					if absf(w) < 0.0001 or k >= shapes.size():
						continue
					var sv: PackedVector3Array = shapes[k][Mesh.ARRAY_VERTEX]
					for v in verts.size():
						verts[v] += (sv[v] - base_v[v]) * w
				arr[Mesh.ARRAY_VERTEX] = verts
			var bones = arr[Mesh.ARRAY_BONES]
			if bones == null:
				return []
			var nb := PackedInt32Array(bones)
			for i in nb.size():
				nb[i] = remap[nb[i]] if nb[i] < remap.size() else 0
			arr[Mesh.ARRAY_BONES] = nb
			var mat := mi.get_surface_override_material(s)
			if mat == null:
				mat = mesh.surface_get_material(s)
			var fmt := mesh.surface_get_format(s) & Mesh.ARRAY_FORMAT_CUSTOM_BASE - 1
			var gk := "%d|%d" % [mat.get_instance_id() if mat else 0, fmt]
			if not groups.has(gk):
				groups[gk] = {"mat": mat, "parts": []}
				order.append(gk)
			groups[gk].parts.append(arr)
	var out := ArrayMesh.new()
	var mats: Array = []
	for gk in order:
		var g: Dictionary = groups[gk]
		var arr := _join(g.parts)
		if arr.is_empty():
			continue
		var flags := Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS if (arr[Mesh.ARRAY_BONES] as PackedInt32Array).size() == (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() * 8 else 0
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr, [], {}, flags)
		mats.append(g.mat)
	return [out, skin, mats]

## Concatenate surface arrays of one format (indices shifted).
static func _join(list: Array) -> Array:
	if list.size() == 1:
		return list[0]
	var out: Array = []
	out.resize(Mesh.ARRAY_MAX)
	var base := 0
	for arr in list:
		var n := (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
		for k in Mesh.ARRAY_MAX:
			var a = arr[k]
			if a == null:
				continue
			if k == Mesh.ARRAY_INDEX:
				var idx := PackedInt32Array(a)
				for i in idx.size():
					idx[i] += base
				a = idx
			if out[k] == null:
				out[k] = a.duplicate()
			else:
				out[k].append_array(a)
		base += n
	return out
