class_name CharacterVisual
extends Node3D
## Presentation of a character: model, animation playback with crossfades, weapon attachment, hit flash,
## status visuals and footstep events. Gameplay never reads state from here except animation timing metadata.

signal footstep
signal action_finished(anim: StringName)

const BLEND := 0.15
const LOCO_BLEND := 0.22

var model: Node3D
var anim_player: AnimationPlayer
var skeleton: Skeleton3D
var fallback := false
var model_scale := 1.0
var ground_speed_walk := 1.6
var ground_speed_run := 5.0
var idle_anim: StringName = &"idle"
var _action := &""
var _action_left := 0.0
var _reaction_left := 0.0
var _loco := &""
var _last_loco_pos := 0.0
var _dead := false
var _overlay: ShaderMaterial
var _flash_tw: Tween
var _status_nodes := {}
var _weapon_nodes := {}
var tint_primary := Color.WHITE
var _meshes: Array[MeshInstance3D] = []

static var _overlay_shader: Shader

func setup(model_path: String, scale_factor := 1.0, primary_tint := Color.WHITE) -> void:
	model_scale = scale_factor
	tint_primary = primary_tint
	if ResourceLoader.exists(model_path):
		var ps: PackedScene = load(model_path)
		model = ps.instantiate()
		add_child(model)
		model.scale = Vector3.ONE * scale_factor
		anim_player = _find(model, "AnimationPlayer") as AnimationPlayer
		skeleton = _find(model, "Skeleton3D") as Skeleton3D
		_prepare_animations()
	else:
		fallback = true
		model = _build_fallback()
		add_child(model)
		model.scale = Vector3.ONE * scale_factor
	_collect_meshes(model)
	MaterialLibrary.apply_character(_meshes, primary_tint)
	_setup_overlay()
	var walk := DB.anim(&"walk")
	var run := DB.anim(&"run")
	ground_speed_walk = float(walk.get("ground_speed", 1.6)) * scale_factor
	ground_speed_run = float(run.get("ground_speed", 5.0)) * scale_factor

func _find(n: Node, cls: String) -> Node:
	if n.get_class() == cls:
		return n
	for c in n.get_children():
		var r := _find(c, cls)
		if r:
			return r
	return null

func _collect_meshes(n: Node) -> void:
	if n is MeshInstance3D:
		_meshes.append(n)
		n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for c in n.get_children():
		_collect_meshes(c)

func _prepare_animations() -> void:
	if anim_player == null:
		return
	anim_player.playback_default_blend_time = BLEND
	for lib_name in anim_player.get_animation_library_list():
		var lib := anim_player.get_animation_library(lib_name)
		for an in lib.get_animation_list():
			var meta := DB.anim(an)
			var a := lib.get_animation(an)
			a.loop_mode = Animation.LOOP_LINEAR if meta.get("loop", false) else Animation.LOOP_NONE

func has_anim(n: StringName) -> bool:
	return anim_player != null and anim_player.has_animation(n)

func _setup_overlay() -> void:
	if _overlay_shader == null:
		_overlay_shader = Shader.new()
		_overlay_shader.code = """
shader_type spatial;
render_mode blend_add, unshaded, cull_back, depth_draw_never;
uniform vec4 flash_color : source_color = vec4(1.0);
uniform float flash = 0.0;
uniform vec4 rim_color : source_color = vec4(0.0);
uniform float rim = 0.0;
void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.5);
	vec3 c = flash_color.rgb * flash * (0.35 + 0.65 * fres) + rim_color.rgb * rim * fres;
	ALBEDO = c;
	ALPHA = 1.0;
}
"""
	_overlay = ShaderMaterial.new()
	_overlay.shader = _overlay_shader
	for m in _meshes:
		m.material_overlay = _overlay

func set_rim(color: Color, amount: float) -> void:
	if _overlay:
		_overlay.set_shader_parameter("rim_color", color)
		_overlay.set_shader_parameter("rim", amount)

func flash(color := Color(1, 1, 1), strength := 1.0, time := 0.14) -> void:
	if _overlay == null:
		return
	if _flash_tw:
		_flash_tw.kill()
	_overlay.set_shader_parameter("flash_color", color)
	_overlay.set_shader_parameter("flash", strength)
	_flash_tw = create_tween()
	_flash_tw.tween_method(func(v): _overlay.set_shader_parameter("flash", v), strength, 0.0, time)

# ---- Weapons ----------------------------------------------------------------------------------------------

func attach_weapon(hand: StringName, model_path: String, offset := Transform3D.IDENTITY) -> void:
	detach_weapon(hand)
	if model_path == "" or not ResourceLoader.exists(model_path):
		return
	var bone := "weapon.R" if hand == &"main" else "weapon.L"
	var holder: Node3D
	if skeleton and skeleton.find_bone(bone) >= 0:
		var ba := BoneAttachment3D.new()
		ba.bone_name = bone
		skeleton.add_child(ba)
		holder = ba
	else:
		holder = Node3D.new()
		model.add_child(holder)
		holder.position = Vector3(0.35 if hand == &"main" else -0.35, 1.0, 0.1)
	var w: Node3D = load(model_path).instantiate()
	w.transform = offset
	holder.add_child(w)
	var ms: Array[MeshInstance3D] = []
	_collect_into(w, ms)
	MaterialLibrary.apply_character(ms, tint_primary)
	for m in ms:
		m.material_overlay = _overlay
		_meshes.append(m)
	_weapon_nodes[hand] = holder

func _collect_into(n: Node, out: Array[MeshInstance3D]) -> void:
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		_collect_into(c, out)

func detach_weapon(hand: StringName) -> void:
	if _weapon_nodes.has(hand):
		var n: Node = _weapon_nodes[hand]
		for c in n.get_children():
			for m in _meshes.duplicate():
				if not is_instance_valid(m) or c.is_ancestor_of(m) or c == m:
					_meshes.erase(m)
		n.queue_free()
		_weapon_nodes.erase(hand)

func weapon_tip_position(hand := &"main") -> Vector3:
	if _weapon_nodes.has(hand):
		var n: Node3D = _weapon_nodes[hand]
		return n.global_transform * Vector3(0, 0.9, 0)
	return global_position + Vector3.UP * 1.2 + global_transform.basis.z * 0.8

# ---- Animation --------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if _action_left > 0.0:
		_action_left -= delta
		if _action_left <= 0.0:
			var a := _action
			_action = &""
			action_finished.emit(a)
	if _reaction_left > 0.0:
		_reaction_left -= delta
	if fallback:
		_animate_fallback(delta)
	_footsteps()

func is_busy() -> bool:
	return _action_left > 0.0 or _reaction_left > 0.0

## Locomotion by horizontal speed. Playback rate matches the authored ground speed to avoid foot sliding.
func update_locomotion(speed: float, idle_name: StringName = &"") -> void:
	if _dead or _action_left > 0.0 or _reaction_left > 0.0:
		return
	var target: StringName
	var rate := 1.0
	if speed < 0.25:
		target = idle_name if idle_name != &"" and has_anim(idle_name) else idle_anim
	elif speed < (ground_speed_walk + ground_speed_run) * 0.45:
		target = &"walk"
		rate = clampf(speed / ground_speed_walk, 0.6, 2.2)
	else:
		target = &"run"
		rate = clampf(speed / ground_speed_run, 0.6, 1.8)
	_play(target, LOCO_BLEND, rate)
	_loco = target

func _play(n: StringName, blend: float, rate: float) -> void:
	if anim_player == null or not anim_player.has_animation(n):
		return
	if anim_player.current_animation == n:
		anim_player.speed_scale = rate
		return
	anim_player.play(n, blend)
	anim_player.speed_scale = rate

## One-shot action (attack, cast, skill). Returns its duration in seconds at the given rate.
func play_action(n: StringName, rate := 1.0, blend := 0.08) -> float:
	if _dead:
		return 0.0
	var meta := DB.anim(n)
	var length := float(meta.get("length", 0.7))
	_action = n
	_action_left = length / maxf(rate, 0.05)
	_reaction_left = 0.0
	_loco = &""
	if anim_player and anim_player.has_animation(n):
		anim_player.play(n, blend)
		anim_player.seek(0.0, true)
		anim_player.speed_scale = rate
	elif fallback:
		_fb_action_t = 0.0
		_fb_action_len = _action_left
	return _action_left

## Looping channel animation (whirlwind, block, bow draw). Stays until stop_action().
func hold_action(n: StringName, rate := 1.0) -> void:
	_action = n
	_action_left = 9999.0
	if anim_player and anim_player.has_animation(n):
		anim_player.play(n, 0.12)
		anim_player.speed_scale = rate

func stop_action() -> void:
	_action_left = 0.0
	_action = &""

func current_action() -> StringName:
	return _action

func play_reaction(kind: StringName) -> void:
	if _dead:
		return
	var n: StringName
	match kind:
		&"hit": n = &"hit"
		&"stagger": n = &"stagger"
		&"knockback": n = &"knockback"
		&"land": n = &"getup"
		&"block": n = &"block_impact"
		&"parry": n = &"parry"
		_: n = kind
	var meta := DB.anim(n)
	var length := float(meta.get("length", 0.4))
	if kind == &"hit" and _action_left > 0.0:
		flash(Color(1, 0.9, 0.85), 0.8)
		return  # light hits don't interrupt actions; heavier reactions do
	_action = &""
	_action_left = 0.0
	_reaction_left = length
	if anim_player and anim_player.has_animation(n):
		anim_player.play(n, 0.06)
		anim_player.seek(0.0, true)
		anim_player.speed_scale = 1.0
	elif fallback:
		_fb_react = length

func play_death() -> void:
	_dead = true
	_action_left = 0.0
	if anim_player and anim_player.has_animation(&"death"):
		anim_player.play(&"death", 0.1)
		anim_player.speed_scale = 1.0
	elif fallback:
		var tw := create_tween()
		tw.tween_property(model, "rotation:x", -PI / 2.0, 0.5).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	set_rim(Color.BLACK, 0.0)
	for id in _status_nodes.keys():
		set_status_visual(id, false)

func _footsteps() -> void:
	if anim_player == null or (_loco != &"walk" and _loco != &"run"):
		return
	var meta := DB.anim(_loco)
	var pos := anim_player.current_animation_position
	for t in meta.get("footsteps", []):
		var ft := float(t)
		if (_last_loco_pos < ft and pos >= ft) or (pos < _last_loco_pos and (ft > _last_loco_pos or ft <= pos)):
			footstep.emit()
			break
	_last_loco_pos = pos

# ---- Status visuals ---------------------------------------------------------------------------------------

func set_status_visual(id: StringName, on: bool) -> void:
	if not on:
		if _status_nodes.has(id):
			var n: Node = _status_nodes[id]
			if is_instance_valid(n):
				if n is GPUParticles3D:
					n.emitting = false
					get_tree().create_timer(1.0).timeout.connect(n.queue_free)
				else:
					n.queue_free()
			_status_nodes.erase(id)
		_refresh_rim()
		return
	if _status_nodes.has(id) or _dead:
		return
	var h := 1.8 * model_scale
	var node: Node3D = null
	match id:
		&"burning": node = VFXLib.status_particles(Elements.FIRE, h)
		&"shocked": node = VFXLib.status_particles(Elements.LIGHTNING, h)
		&"cursed": node = VFXLib.status_particles(Elements.DARK, h)
		&"chilled": node = VFXLib.status_particles(Elements.ICE, h)
		&"wet": node = VFXLib.status_particles(Elements.WATER, h)
		&"frozen": node = VFXLib.ice_block(h, model_scale)
		&"stunned", &"staggered": node = VFXLib.stun_stars(h)
		&"bleeding": node = VFXLib.status_particles(Elements.PHYSICAL, h)
	if node:
		add_child(node)
		_status_nodes[id] = node
	if id == &"frozen" and anim_player:
		anim_player.speed_scale = 0.0
	_refresh_rim()

func _refresh_rim() -> void:
	var c := Color.BLACK
	var a := 0.0
	for id in [&"frozen", &"burning", &"shocked", &"cursed", &"chilled", &"wet"]:
		if _status_nodes.has(id):
			match id:
				&"frozen": c = Color(0.6, 0.9, 1.0); a = 1.2
				&"burning": c = Color(1.0, 0.45, 0.1); a = 0.9
				&"shocked": c = Color(1.0, 0.95, 0.4); a = 0.8
				&"cursed": c = Color(0.6, 0.2, 0.9); a = 0.8
				&"chilled": c = Color(0.5, 0.8, 1.0); a = 0.5
				&"wet": c = Color(0.2, 0.45, 0.9); a = 0.4
			break
	if not _status_nodes.has(&"frozen") and anim_player and anim_player.speed_scale == 0.0 and not _dead:
		anim_player.speed_scale = 1.0
	set_rim(c, a)

# ---- Temporary fallback body (only used until the rigged models exist) ------------------------------------

var _fb_action_t := 0.0
var _fb_action_len := 0.0
var _fb_react := 0.0
var _fb_arm: Node3D
var _fb_bob := 0.0

func _build_fallback() -> Node3D:
	var root := Node3D.new()
	root.name = "TemporaryBody"
	var body := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.32
	cap.height = 1.5
	body.mesh = cap
	body.position.y = 0.85
	var mat := StandardMaterial3D.new()
	mat.albedo_color = tint_primary.darkened(0.2)
	mat.roughness = 0.6
	body.material_override = mat
	root.add_child(body)
	var head := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.2
	sph.height = 0.4
	head.mesh = sph
	head.position.y = 1.72
	root.add_child(head)
	_fb_arm = Node3D.new()
	_fb_arm.position = Vector3(0.38, 1.25, 0.0)
	root.add_child(_fb_arm)
	var blade := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.08, 0.08, 1.0)
	blade.mesh = bm
	blade.position = Vector3(0, 0, 0.5)
	_fb_arm.add_child(blade)
	return root

func _animate_fallback(delta: float) -> void:
	if _dead:
		return
	_fb_bob += delta * 8.0
	if _fb_action_len > 0.0:
		_fb_action_t += delta
		var t := clampf(_fb_action_t / _fb_action_len, 0.0, 1.0)
		_fb_arm.rotation.y = lerpf(1.4, -1.4, ease(t, 0.4))
		if t >= 1.0:
			_fb_action_len = 0.0
	else:
		_fb_arm.rotation.y = lerpf(_fb_arm.rotation.y, 0.4, delta * 8.0)
	if _fb_react > 0.0:
		_fb_react -= delta
		model.rotation.x = -0.25 if _fb_react > 0.0 else 0.0
	else:
		model.rotation.x = 0.0
