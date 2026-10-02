class_name HeroBody
extends RefCounted
## bh-023: the hero's own body on a CharacterVisual (model HeroLook.MODEL): applies a look (skin shader, shape keys,
## hair and beard, head / hand / foot size, height) and dresses the body in the equipment's worn models.
##
## Cost: the body is one draw call whatever the look; hair and beard add one each; every worn piece is one skinned
## mesh with a few surfaces. Shape keys only move vertices when a look uses them.

const SKIN_SHADER := preload("res://src/actors/hero/hero_skin.gdshader")
const HAIR_SHADER := preload("res://src/actors/hero/hero_hair.gdshader")
const SKIN_TEX := "res://assets/characters/hero/hero_skin.png"
const MASK_TEX := "res://assets/characters/hero/hero_masks.png"
const SIZED_BONES := {"head": ["head"], "hands": ["hand.L", "hand.R"], "feet": ["foot.L", "foot.R"]}
const NO_HIDE := Vector2(9.0, 9.0)

var visual: CharacterVisual
var body: MeshInstance3D
var skin: ShaderMaterial
var look := {}
var base_scale := 1.0
var _head: BoneAttachment3D
var _hair: MeshInstance3D
var _beard: MeshInstance3D
var _hair_path := ""
var _beard_path := ""
var _hair_mat: ShaderMaterial
var _beard_mat: ShaderMaterial
var _wear: Array[MeshInstance3D] = []
var _wear_sig := "-"
## bh-031: a persona's colours for its worn pieces (HeroWear.dye_key -> hex); empty for a player's hero
var dyes := {}
## bh-031: set for personas (they never change clothes): the outfit is baked into one shared mesh under this key
var merge_key := ""

func _body_key_sig() -> String:
	var parts := PackedStringArray()
	for k in HeroLook.BODY_KEYS:
		parts.append("%.3f" % float(look.get(k, 0.0)))
	return ",".join(parts)
var _hide_hair := false
var _opacity := 1.0
var _decay := 0.0

static func is_hero(model_path: String) -> bool:
	return model_path == HeroLook.MODEL

func _init(v: CharacterVisual) -> void:
	visual = v
	base_scale = v.model_scale
	for m in v._meshes:
		if m.mesh and m.mesh.get_surface_count() > 0 and m.mesh.surface_get_material(0) \
				and m.mesh.surface_get_material(0).resource_name.begins_with("BH_HeroSkin"):
			body = m
			break
	if body == null:
		return
	skin = ShaderMaterial.new()
	skin.shader = SKIN_SHADER
	skin.set_shader_parameter(&"skin_tex", load(SKIN_TEX))
	skin.set_shader_parameter(&"mask_tex", load(MASK_TEX))
	body.set_surface_override_material(0, skin)
	# the body's bounds must cover the largest sliders (a giant head, hair to the floor) so it is never culled early
	body.extra_cull_margin = 1.2
	apply({})

func ok() -> bool:
	return body != null

# ---- Look --------------------------------------------------------------------------------------------------------

## Apply a look (any Dictionary: it is cleaned first). Cheap enough to call on every slider movement.
func apply(src: Dictionary) -> void:
	if body == null:
		return
	look = HeroLook.sanitize(src)
	var l := look
	skin.set_shader_parameter(&"skin_color", HeroLook.rgb(l, "skin"))
	skin.set_shader_parameter(&"underwear_color", HeroLook.rgb(l, "underwear"))
	skin.set_shader_parameter(&"top_wrap", smoothstep(0.25, 0.6, float(l["female"])))
	skin.set_shader_parameter(&"pattern", HeroLook.choice_index("pattern", l["pattern"]))
	skin.set_shader_parameter(&"pattern_color", HeroLook.rgb(l, "pattern_color"))
	skin.set_shader_parameter(&"pattern_amount", l["pattern_amount"])
	skin.set_shader_parameter(&"pattern_scale", l["pattern_scale"])
	skin.set_shader_parameter(&"hair_color", HeroLook.rgb(l, "hair_color"))
	skin.set_shader_parameter(&"scalp_shade", HeroLook.scalp_shade(l))
	skin.set_shader_parameter(&"stubble", l["stubble"])
	skin.set_shader_parameter(&"lip_color", HeroLook.rgb(l, "lip_color"))
	skin.set_shader_parameter(&"lip_amount", l["lip_amount"])
	skin.set_shader_parameter(&"eye_style", HeroLook.choice_index("eye", l["eye"]))
	skin.set_shader_parameter(&"eye_color", HeroLook.rgb(l, "eye_color"))
	for k in ["eye_size", "eye_spacing", "eye_height", "eye_tilt", "eye_glow", "brow_thick", "brow_tilt", "brow_height"]:
		skin.set_shader_parameter(StringName(k), l[k])
	skin.set_shader_parameter(&"brow_style", HeroLook.choice_index("brow", l["brow"]))
	skin.set_shader_parameter(&"brow_color", HeroLook.rgb(l, "brow_color"))
	skin.set_shader_parameter(&"marking", HeroLook.choice_index("marking", l["marking"]))
	skin.set_shader_parameter(&"marking_color", HeroLook.rgb(l, "marking_color"))
	for k in HeroLook.SHAPE_KEYS:
		var i := body.find_blend_shape_by_name(StringName(k))
		if i >= 0:
			body.set_blend_shape_value(i, l[k])
	_apply_body_keys()
	_apply_sizes()
	_set_hair(false, HeroLook.hair_model(l), HeroLook.rgb(l, "hair_color"), l["hair_length"])
	_set_hair(true, HeroLook.beard_model(l), HeroLook.rgb(l, "beard_color"), l["beard_length"])
	_refresh_hair_visibility()

func _apply_body_keys() -> void:
	for m in _wear:
		if not is_instance_valid(m):
			continue
		for k in HeroLook.BODY_KEYS:
			var i := m.find_blend_shape_by_name(StringName(k))
			if i >= 0:
				m.set_blend_shape_value(i, look[k])

func _apply_sizes() -> void:
	var sk := visual.skeleton
	if sk == null:
		return
	for key in SIZED_BONES:
		var s := float(look[key])
		for bn in SIZED_BONES[key]:
			var i := sk.find_bone(bn)
			if i >= 0:
				sk.set_bone_pose_scale(i, Vector3.ONE * s)
		if key == "hands":
			# weapons keep their own size in a bigger fist
			for bn in ["weapon.L", "weapon.R"]:
				var wi := sk.find_bone(bn)
				if wi >= 0:
					sk.set_bone_pose_scale(wi, Vector3.ONE / s)
	visual.set_model_scale(base_scale * float(look["height"]))

func _head_attachment() -> BoneAttachment3D:
	if _head == null or not is_instance_valid(_head):
		_head = BoneAttachment3D.new()
		_head.name = "HeroHead"
		_head.bone_name = "head"
		visual.skeleton.add_child(_head)
	return _head

func _set_hair(beard: bool, path: String, col: Vector3, length: float) -> void:
	var cur := _beard if beard else _hair
	var cur_path := _beard_path if beard else _hair_path
	if path != cur_path:
		if cur and is_instance_valid(cur):
			visual.release_mesh(cur)
			cur.queue_free()
		cur = null
		if path != "" and visual.skeleton:
			var src := _hair_src(path)
			if not src.is_empty():
				cur = MeshInstance3D.new()
				cur.mesh = src[0]
				var xf: Transform3D = src[1]
				var at := _head_attachment()
				at.add_child(cur)
				var rest := visual.skeleton.get_bone_global_rest(visual.skeleton.find_bone("head"))
				cur.transform = rest.affine_inverse() * xf
				cur.name = "Beard" if beard else "Hair"
				cur.extra_cull_margin = 2.0
				var mat := ShaderMaterial.new()
				mat.shader = HAIR_SHADER
				cur.material_override = mat
				visual.adopt_mesh(cur)
				if beard:
					_beard_mat = mat
				else:
					_hair_mat = mat
		if beard:
			_beard = cur
			_beard_path = path
		else:
			_hair = cur
			_hair_path = path
	if cur and is_instance_valid(cur):
		var mat := _beard_mat if beard else _hair_mat
		mat.set_shader_parameter(&"hair_color", col)
		mat.set_shader_parameter(&"opacity", _opacity)
		mat.set_shader_parameter(&"decay", _decay)
		var i := cur.find_blend_shape_by_name(&"length")
		if i >= 0:
			cur.set_blend_shape_value(i, length)

## bh-031: a persona's cloth colour by layer, so a shirt, a coat and breeches never melt into one suit: the inner
## garment leans to undyed linen ("inner" sets it), the legs go darker ("legs" sets them).
static func layer_dye(d: Dictionary, slot: String) -> Dictionary:
	if not d.has("cloth"):
		return d
	var out := d.duplicate()
	var c := Color(String(d.cloth))
	if slot == "leggings":
		out["cloth"] = String(d.get("legs", c.darkened(0.4).to_html(false)))
	elif slot == "inner_garment":
		out["cloth"] = String(d.get("inner", c.lerp(Color("d8d0bc"), 0.6).to_html(false)))
	return out

## bh-031: a hair or beard model read once: [mesh, transform in model space] (every NPC with a ponytail shares it).
static var _hair_cache := {}

static func _hair_src(path: String) -> Array:
	if _hair_cache.has(path):
		return _hair_cache[path]
	var out: Array = []
	var ps := load(path) as PackedScene
	if ps:
		var scene: Node = ps.instantiate()
		var found := scene.find_children("*", "MeshInstance3D", true, false)
		if scene is MeshInstance3D:
			found.append(scene)
		if not found.is_empty():
			out = [(found[0] as MeshInstance3D).mesh, _model_xf(found[0], scene)]
		scene.free()
	_hair_cache[path] = out
	return out

## A node's transform relative to the root of the scene it was loaded in.
static func _model_xf(n: Node3D, root: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	var c: Node = n
	while c and c != root:
		if c is Node3D:
			t = (c as Node3D).transform * t
		c = c.get_parent()
	if root is Node3D and n != root:
		t = (root as Node3D).transform * t
	return t

func _refresh_hair_visibility() -> void:
	if _hair and is_instance_valid(_hair):
		_hair.visible = not _hide_hair

# ---- Worn equipment ----------------------------------------------------------------------------------------------

## Dress the body in the equipment's worn models. Rebuilds only when the worn set changes.
func dress(equipment: Equipment) -> void:
	if body == null or visual.skeleton == null:
		return
	var show_helm := bool(look.get("show_helm", true))
	var plan := HeroWear.plan(equipment, show_helm)
	var sig: String = plan.sig + ("|%d" % dyes.hash() if not dyes.is_empty() else "")
	if sig == _wear_sig:
		return
	_wear_sig = sig
	for m in _wear:
		if is_instance_valid(m):
			visual.release_mesh(m)
			m.get_parent().remove_child(m)
			m.queue_free()
	_wear.clear()
	var mkey := "%s|%s|%s" % [merge_key, sig, _body_key_sig()]
	if merge_key != "" and HeroWear._merged.has(mkey):
		# another wearer of this exact outfit already baked it: share that mesh, build nothing
		var shared := HeroWear.merge([] as Array[MeshInstance3D], visual.skeleton, mkey)
		if shared:
			_wear.append(shared)
			visual.adopt_mesh(shared)
			_finish_dress(plan)
			return
	for piece in plan.pieces:
		if not dyes.is_empty():
			piece["dye"] = layer_dye(dyes, String(piece.get("slot", "")))
		for m in HeroWear.build(piece, visual.skeleton):
			visual.adopt_mesh(m)
			_wear.append(m)
	_apply_body_keys()
	if merge_key != "" and _wear.size() > 1:
		# bh-031: a persona never changes clothes: one baked mesh for the whole outfit (HeroWear.merge)
		var merged := HeroWear.merge(_wear, visual.skeleton, mkey)
		if merged:
			for m in _wear:
				visual.release_mesh(m)
				m.get_parent().remove_child(m)
				m.queue_free()
			_wear.clear()
			_wear.append(merged)
			visual.adopt_mesh(merged)
	_finish_dress(plan)

## The body's cut-outs under what is worn, and the hair under a helm.
func _finish_dress(plan: Dictionary) -> void:
	var hide: Dictionary = plan.hide
	skin.set_shader_parameter(&"hide_sleeve", hide.get("sleeve", NO_HIDE))
	skin.set_shader_parameter(&"hide_glove_l", hide.get("glove_l", NO_HIDE))
	skin.set_shader_parameter(&"hide_glove_r", hide.get("glove_r", NO_HIDE))
	skin.set_shader_parameter(&"hide_z1", hide.get("z1", NO_HIDE))
	skin.set_shader_parameter(&"hide_z2", hide.get("z2", NO_HIDE))
	skin.set_shader_parameter(&"hide_boot_l", hide.get("boot_l", NO_HIDE))
	skin.set_shader_parameter(&"hide_boot_r", hide.get("boot_r", NO_HIDE))
	_hide_hair = bool(plan.hide_hair)
	_refresh_hair_visibility()
	visual.refresh_local_materials()

# ---- Stealth and corpse decay (CharacterVisual forwards these) --------------------------------------------------

func set_opacity(a: float) -> void:
	_opacity = a
	for m in [skin, _hair_mat, _beard_mat]:
		if m:
			m.set_shader_parameter(&"opacity", a)

func set_decay(amount: float) -> void:
	_decay = amount
	for m in [skin, _hair_mat, _beard_mat]:
		if m:
			m.set_shader_parameter(&"decay", amount)
