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
			var scene: Node3D = (load(path) as PackedScene).instantiate()
			var found := scene.find_children("*", "MeshInstance3D", true, false)
			if scene is MeshInstance3D:
				found.append(scene)
			if not found.is_empty():
				cur = found[0]
				var xf := _model_xf(cur, scene)
				if cur.get_parent():
					cur.get_parent().remove_child(cur)
				cur.owner = null
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
			if cur != scene:
				scene.free()
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
	var sig: String = plan.sig
	if sig == _wear_sig:
		return
	_wear_sig = sig
	for m in _wear:
		if is_instance_valid(m):
			visual.release_mesh(m)
			m.get_parent().remove_child(m)
			m.queue_free()
	_wear.clear()
	for piece in plan.pieces:
		for m in HeroWear.build(piece, visual.skeleton):
			visual.adopt_mesh(m)
			_wear.append(m)
	_apply_body_keys()
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
