class_name CutsceneActor
extends Node3D
## bh-021: a character in a cutscene — a GLB played straight through its AnimationPlayer (crossfaded clips, cinematic
## cs_* loops), weapons on bone attachments, surfaces that can be hidden (Paul David's sheathed hilt when he holds
## Stormwake), and legend effects (LegendFX) parented to it. It never simulates anything: the cutscene moves it.

## Cinematic clips that loop (tools/blender/characters/lib_cinematic.py marks the same set).
const LOOPS := [&"cs_aj_kneel", &"cs_aj_point", &"cs_aj_charge", &"cs_aj_chained", &"cs_aj_stand", &"cs_ro_shoulder",
	&"cs_ro_brace", &"cs_ro_stand", &"cs_pd_idle", &"cs_pd_shard", &"cs_pd_gesture", &"cs_pd_ready", &"cs_kx_pull",
	&"idle", &"idle_look", &"idle_1h", &"idle_2h", &"idle_spear", &"idle_staff", &"walk", &"run", &"run_combat",
	&"interact_talk", &"cast_channel", &"boss_charge", &"block_loop", &"launch"]

const WEAPONS := "res://assets/weapons/legend/%s.glb"
const CHARS := "res://assets/characters/%s.glb"

var model: Node3D
var anim: AnimationPlayer
var skeleton: Skeleton3D
var clip := &""
var _weapons := {}
var _meshes: Array[MeshInstance3D] = []
static var _hide_mat: ShaderMaterial

## A cutscene actor from a character id (assets/characters/<id>.glb) or a full res:// path.
static func make(id_or_path: String, scale_factor := 1.0, tint := Color.WHITE) -> CutsceneActor:
	var a := CutsceneActor.new()
	a.name = "Actor_" + id_or_path.get_file().get_basename()
	a.process_mode = Node.PROCESS_MODE_ALWAYS
	var path := id_or_path if id_or_path.begins_with("res://") else CHARS % id_or_path
	if ResourceLoader.exists(path):
		a.model = (load(path) as PackedScene).instantiate()
	else:
		push_warning("CutsceneActor: missing model %s" % path)
		a.model = Node3D.new()
	a.add_child(a.model)
	a.model.scale = Vector3.ONE * scale_factor
	a.anim = a._find(a.model, "AnimationPlayer") as AnimationPlayer
	a.skeleton = a._find(a.model, "Skeleton3D") as Skeleton3D
	a._collect(a.model, a._meshes)
	MaterialLibrary.apply_character(a._meshes, tint)
	if a.anim:
		own_clips(a.anim)
	return a

## bh-029: the hero's own body as it looks right now: the HeroLook (face, hair, height, build) and every worn piece
## (HeroWear and boss regalia). A plain `make` of hero.glb showed the bare base body. A CharacterVisual dresses it;
## its AnimationTree is switched off so the cutscene drives the AnimationPlayer directly like any other actor.
static func make_hero(app: Dictionary, look: Dictionary, equipment: Equipment) -> CutsceneActor:
	var a := CutsceneActor.new()
	a.name = "Actor_hero"
	a.process_mode = Node.PROCESS_MODE_ALWAYS
	var cv := CharacterVisual.new()
	cv.name = "HeroVisual"
	a.add_child(cv)
	cv.setup(String(app.get("model", "")), float(app.get("scale", 1.0)), app.get("tint", Color.WHITE), app.get("pers", &""))
	if not look.is_empty():
		cv.set_look(look)
	if equipment:
		cv.dress_equipment(equipment)
	if cv.tree:
		cv.tree.active = false
	cv.process_mode = Node.PROCESS_MODE_DISABLED
	a.model = cv
	a.anim = cv.anim_player
	if a.anim:
		a.anim.process_mode = Node.PROCESS_MODE_ALWAYS
	a.skeleton = cv.skeleton
	a._collect(cv, a._meshes)
	if a.anim:
		own_clips(a.anim)
		a.anim.play(&"idle" if a.anim.has_animation(&"idle") else a.anim.current_animation)
	return a

## bh-031: a person drawn on the hero body (Persona: an NPC such as Paul David, a humanoid boss such as Kethrax). The
## cinematic clips (cs_*) authored on their old model are carried over: every character shares the 24-bone rig, so
## the tracks only need pointing at the hero's skeleton.
static func make_persona(persona: Dictionary, clips_from := "", scale_factor := 1.0) -> CutsceneActor:
	var a := make_hero({"model": Persona.MODEL, "scale": scale_factor * float(persona.get("size", 1.0))}, {}, null)
	a.name = "Actor_persona"
	var cv := a.model as CharacterVisual
	if cv and cv.hero:
		cv.process_mode = Node.PROCESS_MODE_INHERIT
		# weapons are the cutscene's to attach (a copy carries the live character's, a legend its own)
		var bare := persona.duplicate()
		bare.erase("main")
		bare.erase("off")
		Persona.apply(cv, bare)
		if cv.tree:
			cv.tree.active = false
		cv.process_mode = Node.PROCESS_MODE_DISABLED
		a._meshes.clear()
		a._collect(cv, a._meshes)
	var src := clips_from if clips_from.begins_with("res://") or clips_from == "" else CHARS % clips_from
	if src != "" and a.anim and ResourceLoader.exists(src):
		var node: Node = (load(src) as PackedScene).instantiate()
		var sap := a._find(node, "AnimationPlayer") as AnimationPlayer
		if sap:
			var skel_path := String(a.anim.get_node(a.anim.root_node).get_path_to(a.skeleton)) if a.skeleton else "Skeleton3D"
			var lib := a.anim.get_animation_library(&"")
			for an in sap.get_animation_list():
				if not String(an).begins_with("cs_") or a.anim.has_animation(an):
					continue
				var anim := sap.get_animation(an).duplicate(true) as Animation
				for t in anim.get_track_count():
					var p := anim.track_get_path(t)
					if p.get_subname_count() > 0:
						anim.track_set_path(t, NodePath(skel_path + ":" + String(p.get_subname(0))))
				anim.loop_mode = Animation.LOOP_LINEAR if LOOPS.has(StringName(an)) else Animation.LOOP_NONE
				lib.add_animation(an, anim)
		node.free()
	return a

## The cutscene's own loop settings, on the actor's own copies. A GLB's Animation resources are shared by every
## instance of it, the live player's included: setting loop_mode on them in place left the hero's run, strafe and
## sprint clips playing once and freezing after every cutscene. Clips whose setting already matches stay shared; the
## libraries themselves are always the actor's own (make_persona adds cinematic clips to them).
static func own_clips(ap: AnimationPlayer) -> void:
	for lib_name in ap.get_animation_library_list():
		var src := ap.get_animation_library(lib_name)
		var lib := AnimationLibrary.new()
		for an in src.get_animation_list():
			var clip_res := src.get_animation(an)
			var want := Animation.LOOP_LINEAR if LOOPS.has(StringName(an)) else Animation.LOOP_NONE
			if clip_res.loop_mode != want:
				clip_res = clip_res.duplicate() as Animation
				clip_res.loop_mode = want
			lib.add_animation(an, clip_res)
		ap.remove_animation_library(lib_name)
		ap.add_animation_library(lib_name, lib)

func _find(n: Node, cls: String) -> Node:
	if n.get_class() == cls:
		return n
	for c in n.get_children():
		var r := _find(c, cls)
		if r:
			return r
	return null

func _collect(n: Node, out: Array[MeshInstance3D]) -> void:
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		_collect(c, out)

func has_clip(n: StringName) -> bool:
	return anim != null and anim.has_animation(n)

## Crossfade into a clip. `at` starts part-way through (seconds); speed < 1 slows it (slow motion).
func play(n: StringName, blend := 0.25, speed := 1.0, at := 0.0) -> void:
	if not has_clip(n):
		push_warning("CutsceneActor %s has no clip %s" % [name, n])
		return
	clip = n
	anim.play(n, blend, speed)
	if at > 0.0:
		anim.seek(at, true)

func clip_length(n: StringName) -> float:
	return anim.get_animation(n).length if has_clip(n) else 0.0

func set_speed(s: float) -> void:
	if anim:
		anim.speed_scale = s

## Put a legend weapon (assets/weapons/legend/<id>.glb) or any weapon GLB on a bone (weapon.R by default).
func attach(slot: StringName, weapon: String, bone := "weapon.R", xf := Transform3D.IDENTITY) -> Node3D:
	detach(slot)
	var path := weapon if weapon.begins_with("res://") else WEAPONS % weapon
	if skeleton == null or not ResourceLoader.exists(path):
		return null
	var ba := BoneAttachment3D.new()
	ba.bone_name = bone
	skeleton.add_child(ba)
	var w: Node3D = (load(path) as PackedScene).instantiate()
	w.transform = xf
	ba.add_child(w)
	var ms: Array[MeshInstance3D] = []
	_collect(w, ms)
	MaterialLibrary.apply_character(ms, Color.WHITE)
	_weapons[slot] = ba
	return w

func detach(slot: StringName) -> void:
	if _weapons.has(slot):
		(_weapons[slot] as Node).queue_free()
		_weapons.erase(slot)

func weapon(slot: StringName) -> Node3D:
	return _weapons.get(slot) as Node3D

## Hide (or show again) every surface whose material name starts with `prefix` ("BH_Hilt").
func hide_surfaces(prefix: String, hidden := true) -> void:
	if _hide_mat == null:
		_hide_mat = ShaderMaterial.new()
		_hide_mat.shader = Shader.new()
		_hide_mat.shader.code = "shader_type spatial;\nrender_mode unshaded, cull_disabled;\nvoid fragment() { discard; }\n"
	for mi in _meshes:
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i)
			if m and m.resource_name.begins_with(prefix):
				if hidden:
					mi.set_surface_override_material(i, _hide_mat)
				else:
					MaterialLibrary.apply_character([mi], Color.WHITE)

## World position of a bone (e.g. "head", "chest", "weapon.R").
func bone_pos(bone: String) -> Vector3:
	if skeleton == null:
		return global_position
	var i := skeleton.find_bone(bone)
	if i < 0:
		return global_position
	return skeleton.global_transform * skeleton.get_bone_global_pose(i).origin

## A node that follows a bone (for effects on the hand, the chest, the head).
func follow(bone: String) -> Node3D:
	if skeleton == null:
		return self
	var ba := BoneAttachment3D.new()
	ba.bone_name = bone
	skeleton.add_child(ba)
	return ba

func face(target: Vector3) -> void:
	var d := target - global_position
	d.y = 0.0
	if d.length() > 0.01:
		rotation.y = atan2(d.x, d.z)

## Recolour every glowing surface (the Legion's eyes violet instead of the garrison's green).
func recolor_emission(c: Color, energy := -1.0) -> void:
	# bh-031: on the hero body the glow is in the eyes (drawn by the skin shader)
	var cv := model as CharacterVisual
	if cv and cv.hero:
		var lk: Dictionary = cv.hero.look.duplicate()
		lk["eye"] = "glowing"
		lk["eye_color"] = c.to_html(false)
		lk["eye_glow"] = 1.0
		cv.set_look(lk)
	for mi in _meshes:
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var m := mi.get_surface_override_material(i)
			if m == null:
				m = mi.mesh.surface_get_material(i)
			if m is BaseMaterial3D and (m as BaseMaterial3D).emission_enabled:
				var d := (m as BaseMaterial3D).duplicate() as BaseMaterial3D
				d.emission = c
				d.albedo_color = c.darkened(0.3)
				if energy > 0.0:
					d.emission_energy_multiplier = energy
				mi.set_surface_override_material(i, d)

## An overlay on every mesh (a ghost's glow, a flash of light); null clears it.
func set_overlay(m: Material) -> void:
	for mi in _meshes:
		mi.material_overlay = m

## Swap every surface to one material (a spirit made of light).
func set_override(m: Material) -> void:
	for mi in _meshes:
		mi.material_override = m
