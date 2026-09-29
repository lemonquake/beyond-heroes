class_name CharacterVisual
extends Node3D
## Presentation of a character: model, AnimationTree blending, weapon attachment, hit flash, status visuals.
## Gameplay never reads state from here except animation timing metadata (DB.anim), so the simulation stays
## deterministic whether or not a model is present.
##
## AnimationTree layout (built in code, driven through `parameters/...`):
##
##   relaxed_bs (BlendSpace2D: idle / walk / run)            ─┐
##   combat_bs  (BlendSpace2D: stance idle, walk, run_combat,  ├ combat (Blend2) ─┐
##               walk_back, strafe_l / strafe_r)              ─┘                  ├ hurt (Blend2) ─ loco_ts ─┐
##   hurt_bs    (BlendSpace2D: idle_hurt / walk_hurt / run_hurt)─────────────────┘                          │
##   upper_anim ─ upper_ts ─────────────────────────────── upper (Blend2, upper-body filter) ◄──────────────┘
##   state (Transition, xfade): "loco" = upper output | "a" = anim_a ─ a_ts | "b" = anim_b ─ b_ts ─► output
##
## One-shot actions (attacks, casts, reactions, death, fidgets) alternate between slots A and B so consecutive
## actions (combo chains) crossfade instead of snapping. Loops (block, channel, whirlwind) also use the slots.

signal action_finished(anim: StringName)

const BLEND := 0.12
const REACTION_BLEND := 0.07
const LOCO_RETURN_BLEND := 0.22
const UPPER_BONES := ["spine", "chest", "neck", "head", "shoulder.L", "upper_arm.L", "forearm.L", "hand.L", "weapon.L",
	"shoulder.R", "upper_arm.R", "forearm.R", "hand.R", "weapon.R", "cape.1", "cape.2"]
const FIDGETS := {&"knight": [&"idle_look", &"idle_adjust", &"idle_knight"], &"mage": [&"idle_look", &"idle_adjust", &"idle_mage"],
	&"ranger": [&"idle_look", &"idle_adjust", &"idle_ranger"], &"shadowblade": [&"idle_look", &"idle_adjust", &"idle_shadowblade"]}

var model: Node3D
var anim_player: AnimationPlayer
var tree: AnimationTree
var skeleton: Skeleton3D
var fallback := false
var model_scale := 1.0
var ground_speed_walk := 1.6
var ground_speed_run := 5.0
var ground_speed_strafe := 3.2
var ground_speed_back := 1.8
var personality: StringName = &""          # knight / mage fidget set
## Animation LOD (bh-014): heroes, Tempos, bosses and townsfolk keep every locomotion clip in phase; the rank and file
## of a monster pack let clips at zero weight rest (set before setup()). From an isometric camera nobody can tell a
## goblin's feet re-phasing through a walk-to-run blend; a brawl of 40 of them saved ~3 ms a frame.
var full_sync := true
var tint_primary := Color.WHITE

var _slot := &"a"                           # slot that holds the current (or last) action
var _action := &""
var _action_left := 0.0
var _action_loop := false
var _in_action := false
var _reaction := false
var _dead := false
var _combat := 0.0                          # smoothed 0..1
var _combat_target := 0.0
var _hurt := 0.0
var _hurt_target := 0.0
var _upper := 0.0
var _upper_target := 0.0
var _upper_anim := &""
var _stance_idle := &"idle_1h"
var _idle_time := 0.0
var _fidget_at := 8.0
var _loco_pos := Vector2.ZERO
var _overlay: ShaderMaterial
var _flash_tw: Tween
var _status_nodes := {}
var _weapon_nodes := {}
var _set_nodes: Array[Node3D] = []
var _set_appearance := ""
var _meshes: Array[MeshInstance3D] = []
var _trail: WeaponTrail
var _rng := RandomNumberGenerator.new()

static var _overlay_shader: Shader
## Networking (bh-008): what this visual looks like and which action it plays, so another machine can mirror it.
var appearance := {}                        # model, scale, tint, pers, weapons {hand: [path, offset]}
var action_serial := 0                      # bumps on every new action (the same clip twice still restarts remotely)
var action_rate := 1.0

func setup(model_path: String, scale_factor := 1.0, primary_tint := Color.WHITE, p_personality := &"") -> void:
	appearance = {"model": model_path, "scale": scale_factor, "tint": primary_tint, "pers": p_personality, "weapons": {}}
	model_scale = scale_factor
	tint_primary = primary_tint
	personality = p_personality
	_rng.seed = hash(model_path) ^ get_instance_id()
	if model_path != "" and ResourceLoader.exists(model_path):
		var ps: PackedScene = load(model_path)
		model = ps.instantiate()
		add_child(model)
		model.scale = Vector3.ONE * scale_factor
		anim_player = _find(model, "AnimationPlayer") as AnimationPlayer
		skeleton = _find(model, "Skeleton3D") as Skeleton3D
		if anim_player:
			_prepare_animations()
			_build_tree()
		elif model.find_child("core", true, false) != null:
			# a static floating creature (wisp convention: core + rings + ribbons, no skeleton) is animated here
			_setup_floating()
	else:
		fallback = true
		model = _build_fallback()
		add_child(model)
		model.scale = Vector3.ONE * scale_factor
	_collect_meshes(model)
	MaterialLibrary.apply_character(_meshes, primary_tint)
	_setup_overlay()
	ground_speed_walk = float(DB.anim(&"walk").get("ground_speed", 1.6)) * scale_factor
	ground_speed_run = float(DB.anim(&"run").get("ground_speed", 5.0)) * scale_factor
	ground_speed_strafe = float(DB.anim(&"strafe_l").get("ground_speed", 3.2)) * scale_factor
	ground_speed_back = float(DB.anim(&"walk_back").get("ground_speed", 1.8)) * scale_factor
	_fidget_at = _rng.randf_range(7.0, 12.0)

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
		n.layers = 2   # characters: ground stains (Gore decals, cull mask 1) never project onto bodies
	for c in n.get_children():
		_collect_meshes(c)

func _prepare_animations() -> void:
	preload("res://src/actors/crossbow_animations.gd").install(anim_player)
	for lib_name in anim_player.get_animation_library_list():
		var lib := anim_player.get_animation_library(lib_name)
		for an in lib.get_animation_list():
			var meta := DB.anim(an)
			lib.get_animation(an).loop_mode = Animation.LOOP_LINEAR if meta.get("loop", false) else Animation.LOOP_NONE

func has_anim(n: StringName) -> bool:
	if anim_player == null:
		return false
	return anim_player.has_animation(n)

## First available name from a preference list (lets data ask for "sword_4" and fall back to "sword_1").
func pick(names: Array) -> StringName:
	for n in names:
		if has_anim(n):
			return n
	return names[0] if not names.is_empty() else &""

# ---- AnimationTree -----------------------------------------------------------------------------------------

func _anim_node(n: StringName) -> AnimationNodeAnimation:
	var a := AnimationNodeAnimation.new()
	a.animation = n if has_anim(n) else &"idle"
	return a

func _bs(points: Array) -> AnimationNodeBlendSpace2D:
	var bs := AnimationNodeBlendSpace2D.new()
	bs.min_space = Vector2(-2.0, -2.0)
	bs.max_space = Vector2(2.0, 2.0)
	# sync keeps every clip of the space advancing (feet stay in phase when walk blends into run) but evaluates all of
	# them every frame, weight 0 or not: ~90 % of a character's animation cost. Efficiency mode (bh-009) lets the idle
	# clips rest instead, and so do ordinary monsters everywhere (bh-014 animation LOD, `full_sync`).
	bs.sync = full_sync and not Perf.lite
	# every point gets a name: Godot 4.7 warns (with a full script backtrace) for each unnamed point, and printing that
	# took ~45 ms a point — about 0.9 s of frozen game every time a monster spawned (bh-014)
	for i in points.size():
		bs.add_blend_point(_anim_node(points[i][0]), points[i][1], -1, StringName("p%d" % i))
	return bs

func _build_tree() -> void:
	tree = AnimationTree.new()
	tree.name = "AnimTree"
	anim_player.get_parent().add_child(tree)
	tree.anim_player = tree.get_path_to(anim_player)
	tree.root_node = anim_player.root_node
	var root := AnimationNodeBlendTree.new()
	var relaxed := _bs([[&"idle", Vector2.ZERO], [&"walk", Vector2(0, 1)], [&"run", Vector2(0, 2)], [&"walk_back", Vector2(0, -1)],
		[&"strafe_l", Vector2(-1, 0)], [&"strafe_r", Vector2(1, 0)]])
	var combat := _bs([[_stance_idle, Vector2.ZERO], [&"walk", Vector2(0, 1)], [&"run_combat", Vector2(0, 2)],
		[&"walk_back", Vector2(0, -1)], [&"walk_back", Vector2(0, -2)], [&"strafe_l", Vector2(-1, 0)], [&"strafe_r", Vector2(1, 0)],
		[&"strafe_l", Vector2(-2, 0)], [&"strafe_r", Vector2(2, 0)]])
	var hurt := _bs([[&"idle_hurt", Vector2.ZERO], [&"walk_hurt", Vector2(0, 1)], [&"run_hurt", Vector2(0, 2)],
		[&"walk_back", Vector2(0, -1)], [&"strafe_l", Vector2(-1, 0)], [&"strafe_r", Vector2(1, 0)]])
	root.add_node(&"relaxed_bs", relaxed, Vector2(0, 0))
	root.add_node(&"combat_bs", combat, Vector2(0, 200))
	root.add_node(&"hurt_bs", hurt, Vector2(0, 400))
	root.add_node(&"combat", AnimationNodeBlend2.new(), Vector2(300, 100))
	root.add_node(&"hurt", AnimationNodeBlend2.new(), Vector2(500, 200))
	root.add_node(&"loco_ts", AnimationNodeTimeScale.new(), Vector2(700, 200))
	var upper := AnimationNodeBlend2.new()
	upper.filter_enabled = true
	for p in _upper_filter_paths():
		upper.set_filter_path(p, true)
	root.add_node(&"upper", upper, Vector2(900, 200))
	root.add_node(&"upper_anim", _anim_node(&"block_loop"), Vector2(500, 500))
	root.add_node(&"upper_ts", AnimationNodeTimeScale.new(), Vector2(700, 500))
	root.add_node(&"anim_a", _anim_node(&"idle"), Vector2(900, 400))
	root.add_node(&"a_ts", AnimationNodeTimeScale.new(), Vector2(1100, 400))
	root.add_node(&"anim_b", _anim_node(&"idle"), Vector2(900, 600))
	root.add_node(&"b_ts", AnimationNodeTimeScale.new(), Vector2(1100, 600))
	var state := AnimationNodeTransition.new()
	state.xfade_time = BLEND
	state.allow_transition_to_self = true
	state.add_input("loco")
	state.add_input("a")
	state.add_input("b")
	root.add_node(&"state", state, Vector2(1300, 300))
	root.connect_node(&"combat", 0, &"relaxed_bs")
	root.connect_node(&"combat", 1, &"combat_bs")
	root.connect_node(&"hurt", 0, &"combat")
	root.connect_node(&"hurt", 1, &"hurt_bs")
	root.connect_node(&"loco_ts", 0, &"hurt")
	root.connect_node(&"upper", 0, &"loco_ts")
	root.connect_node(&"upper_ts", 0, &"upper_anim")
	root.connect_node(&"upper", 1, &"upper_ts")
	root.connect_node(&"a_ts", 0, &"anim_a")
	root.connect_node(&"b_ts", 0, &"anim_b")
	root.connect_node(&"state", 0, &"upper")
	root.connect_node(&"state", 1, &"a_ts")
	root.connect_node(&"state", 2, &"b_ts")
	root.connect_node(&"output", 0, &"state")
	tree.tree_root = root
	tree.active = true
	for p in ["loco_ts", "upper_ts", "a_ts", "b_ts"]:
		tree.set("parameters/%s/scale" % p, 1.0)
	tree.set("parameters/combat/blend_amount", 0.0)
	tree.set("parameters/hurt/blend_amount", 0.0)
	tree.set("parameters/upper/blend_amount", 0.0)
	tree.set("parameters/state/transition_request", "loco")

var _anim_awake := true
var _frozen_pose := false           # Frozen status: the body is ice, the tree holds its pose

## Efficiency mode (bh-009, Perf): off screen or far away the tree stops evaluating and the pose freezes. Timers,
## action ends and every gameplay signal keep running in _process, so nothing waits on a sleeping tree.
func set_anim_awake(on: bool) -> void:
	if on == _anim_awake or tree == null:
		return
	_anim_awake = on
	tree.active = on and not _frozen_pose
	if on:
		# catch the blends up with what happened while asleep (they are only pushed to the tree while awake)
		tree.set(&"parameters/combat/blend_amount", _combat)
		tree.set(&"parameters/hurt/blend_amount", _hurt)
		tree.set(&"parameters/upper/blend_amount", _upper)

## Track paths of upper-body bones (taken from a real animation so the NodePath format matches the import).
func _upper_filter_paths() -> Array:
	var out := []
	var sample: StringName = &"idle" if has_anim(&"idle") else (anim_player.get_animation_list()[0] if not anim_player.get_animation_list().is_empty() else &"")
	if sample == &"":
		return out
	var a := anim_player.get_animation(sample)
	for i in a.get_track_count():
		var p := a.track_get_path(i)
		if p.get_subname_count() > 0 and UPPER_BONES.has(String(p.get_subname(0))):
			out.append(p)
	return out

func _root() -> AnimationNodeBlendTree:
	return tree.tree_root as AnimationNodeBlendTree

## Weapon stance idle used by the combat blend space ("idle_shield", "idle_2h", "idle_staff", ...).
func set_stance(idle_anim: StringName) -> void:
	_stance_idle = idle_anim
	if tree == null:
		return
	var bs := _root().get_node(&"combat_bs") as AnimationNodeBlendSpace2D
	var n := bs.get_blend_point_node(0) as AnimationNodeAnimation
	n.animation = idle_anim if has_anim(idle_anim) else &"idle"

## Locomotion input: local velocity (x = right, y = forward in m/s), combat stance flag, hurt amount 0..1.
func update_locomotion(local_velocity: Vector2, combat_stance: bool, hurt_amount := 0.0, delta := 0.016) -> void:
	_combat_target = 1.0 if combat_stance else 0.0
	_hurt_target = clampf(hurt_amount, 0.0, 1.0)
	var speed := local_velocity.length()
	var dir := local_velocity / speed if speed > 0.001 else Vector2.ZERO
	var fwd := maxf(0.0, dir.y)
	var ref_walk := lerpf(ground_speed_walk, ground_speed_back, maxf(0.0, -dir.y))
	ref_walk = lerpf(ref_walk, ground_speed_strafe * 0.5, absf(dir.x))
	var ref_run := lerpf(ground_speed_run, ground_speed_strafe, absf(dir.x) * (1.0 - fwd))
	var n := 0.0
	if speed <= ref_walk:
		n = speed / maxf(ref_walk, 0.01)
	else:
		n = 1.0 + (speed - ref_walk) / maxf(ref_run - ref_walk, 0.01)
	n = minf(n, 2.0)
	var target := dir * n
	_loco_pos = _loco_pos.lerp(target, 1.0 - exp(-14.0 * delta))
	if speed > 0.2:
		_idle_time = 0.0
	if tree:
		if not _anim_awake:
			return      # nobody sees this pose (Perf); the smoothed blend position above is kept for waking up
		var p := Vector2(_loco_pos.x, _loco_pos.y)
		# StringName paths: a String path is hashed into a StringName on every call (4 calls per character per step)
		tree.set(&"parameters/relaxed_bs/blend_position", Vector2(0.0, maxf(0.0, p.length()) * signf(p.y + 0.001)))
		tree.set(&"parameters/combat_bs/blend_position", p)
		tree.set(&"parameters/hurt_bs/blend_position", p)
		var expected := 0.0
		var ln := p.length()
		expected = ref_walk * ln if ln <= 1.0 else ref_walk + (ln - 1.0) * (ref_run - ref_walk)
		var ts := clampf(speed / expected, 0.6, 1.6) if expected > 0.3 and speed > 0.3 else 1.0
		tree.set(&"parameters/loco_ts/scale", ts)
	elif fallback:
		_fb_speed = speed

func _process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_combat = move_toward(_combat, _combat_target, delta * 3.5)
	_hurt = move_toward(_hurt, _hurt_target, delta * 1.5)
	_upper = move_toward(_upper, _upper_target, delta * 8.0)
	if tree and _anim_awake:
		tree.set(&"parameters/combat/blend_amount", _combat)
		tree.set(&"parameters/hurt/blend_amount", _hurt)
		tree.set(&"parameters/upper/blend_amount", _upper)
	if _in_action and not _action_loop:
		_action_left -= delta
		if _action_left <= 0.0:
			_end_action()
	if not _in_action and not _dead:
		_idle_time += delta
		if _idle_time > _fidget_at and _combat < 0.05 and _hurt < 0.3 and _loco_pos.length() < 0.05:
			_play_fidget()
	if fallback:
		_animate_fallback(delta)
	if _floating:
		_animate_floating(delta)
	if _trail:
		_trail.tick(delta)
	_update_motion(delta)

# ---- Procedural motion layer: hit flinch (spring) + authored skill poses, applied on top of the clips -----------
# The whole visual node is tilted/offset/squashed, so it layers over any animation (and over creatures without a rig).

const FLINCH_STIFF := 260.0
const FLINCH_DAMP := 16.0
const FLINCH_TILT := 0.55          # radians of lean per unit of flinch
const FLINCH_SHIFT := 0.22         # metres of body shove per unit of flinch

var _flinch := Vector3.ZERO        # local-space lean direction * amount (x/z used)
var _flinch_v := Vector3.ZERO
var _squash := 0.0                 # 0..1 vertical squash from impacts, decays fast
var _shake := 0.0                  # 0..1 high-frequency tremble (heavy hits, stagger)
var _shake_t := 0.0
## Skill pose offsets (tweened by SkillFX): position, euler rotation, scale, and the height the rotation pivots around.
var pose_pos := Vector3.ZERO
var pose_rot := Vector3.ZERO
var pose_scale := Vector3.ONE
var pose_pivot := 0.0
var _pose_tw: Tween
var _motion_on := false
var _rest := Transform3D.IDENTITY   # the node's own transform before the layer took over (menus place visuals)

func _wake_motion() -> void:
	if not _motion_on:
		_rest = transform
		_motion_on = true

## Knock the body away from a blow. `world_dir` is the direction the blow travelled (attacker -> target);
## `strength` ~0.2 (jab) .. 1.5 (crushing crit). Heavy actors should pass a reduced strength.
func flinch(world_dir: Vector3, strength: float) -> void:
	if _dead or not is_finite(strength) or strength <= 0.0:
		return
	var d := world_dir.slide(Vector3.UP)
	if d.length_squared() < 0.0001:
		d = -global_transform.basis.z
	var local := (global_transform.basis.inverse() * d.normalized()).slide(Vector3.UP).normalized()
	_wake_motion()
	_flinch_v += local * clampf(strength, 0.0, 1.6) * 7.0
	_squash = maxf(_squash, clampf(strength * 0.6, 0.0, 0.8))
	if strength >= 0.7:
		_shake = maxf(_shake, clampf(strength - 0.5, 0.0, 1.0))

## Tremble in place (stagger, guard break) without a push direction.
func shudder(amount := 0.8) -> void:
	_wake_motion()
	_shake = maxf(_shake, amount)

## Tween the skill pose layer through `keys`: [[time_s, {pos, rot, scale, pivot}], ...] relative to now.
## Each key eases from the previous state; the pose always returns to rest at the end.
func play_pose(keys: Array, settle := 0.18) -> void:
	if _pose_tw:
		_pose_tw.kill()
	_wake_motion()
	_pose_tw = create_tween()
	var t_prev := 0.0
	for k in keys:
		var t: float = k[0]
		var dur := maxf(0.01, t - t_prev)
		t_prev = t
		var d: Dictionary = k[1]
		if d.get("instant", false):
			# jump straight to this state (e.g. a full flip ends at TAU: snap to 0 so it doesn't unwind)
			_pose_tw.tween_callback(func() -> void:
				pose_pos = d.get("pos", Vector3.ZERO)
				pose_rot = d.get("rot", Vector3.ZERO)
				pose_scale = d.get("scale", Vector3.ONE))
			continue
		var trans: int = d.get("trans", Tween.TRANS_SINE)
		var ease_: int = d.get("ease", Tween.EASE_OUT)
		_pose_tw.set_parallel(true)
		_pose_tw.tween_property(self, "pose_pos", d.get("pos", Vector3.ZERO), dur).set_trans(trans).set_ease(ease_)
		_pose_tw.tween_property(self, "pose_rot", d.get("rot", Vector3.ZERO), dur).set_trans(trans).set_ease(ease_)
		_pose_tw.tween_property(self, "pose_scale", d.get("scale", Vector3.ONE), dur).set_trans(trans).set_ease(ease_)
		_pose_tw.tween_property(self, "pose_pivot", d.get("pivot", pose_pivot), dur)
		_pose_tw.set_parallel(false)
		_pose_tw.tween_interval(0.0)
	_pose_tw.set_parallel(true)
	_pose_tw.tween_property(self, "pose_pos", Vector3.ZERO, settle).set_trans(Tween.TRANS_SINE)
	_pose_tw.tween_property(self, "pose_rot", Vector3.ZERO, settle).set_trans(Tween.TRANS_SINE)
	_pose_tw.tween_property(self, "pose_scale", Vector3.ONE, settle).set_trans(Tween.TRANS_SINE)

## Ease the pose layer back to rest (an interrupted skill).
func relax_pose(time := 0.1) -> void:
	if not _motion_on or (pose_pos == Vector3.ZERO and pose_rot == Vector3.ZERO and pose_scale == Vector3.ONE):
		return
	play_pose([], time)

func clear_pose() -> void:
	if _pose_tw:
		_pose_tw.kill()
	pose_pos = Vector3.ZERO
	pose_rot = Vector3.ZERO
	pose_scale = Vector3.ONE
	pose_pivot = 0.0

func _update_motion(delta: float) -> void:
	if not _motion_on:
		return
	delta = minf(delta, 0.05)
	_flinch_v += (-_flinch * FLINCH_STIFF - _flinch_v * FLINCH_DAMP) * delta
	_flinch += _flinch_v * delta
	_squash = move_toward(_squash, 0.0, delta * 5.0)
	_shake = move_toward(_shake, 0.0, delta * 2.5)
	_shake_t += delta
	if _dead:
		_flinch = _flinch.lerp(Vector3.ZERO, clampf(delta * 8.0, 0.0, 1.0))
	var rot := pose_rot + Vector3(_flinch.z * FLINCH_TILT, 0.0, -_flinch.x * FLINCH_TILT)
	var pos := pose_pos + Vector3(_flinch.x, 0.0, _flinch.z) * FLINCH_SHIFT
	if _shake > 0.0:
		pos += Vector3(sin(_shake_t * 71.0), 0.0, cos(_shake_t * 57.0)) * 0.035 * _shake
		rot.z += sin(_shake_t * 63.0) * 0.05 * _shake
	var sq := _squash * 0.14
	var sc := pose_scale * Vector3(1.0 + sq * 0.5, 1.0 - sq, 1.0 + sq * 0.5)
	var b := Basis.from_euler(rot) * Basis.from_scale(sc)
	if pose_pivot != 0.0:
		var piv := Vector3.UP * pose_pivot
		pos += piv - b * piv
	transform = _rest * Transform3D(b, pos)
	var posing := _pose_tw != null and _pose_tw.is_running()
	if not posing and _flinch.length() < 0.002 and _flinch_v.length() < 0.01 and _squash <= 0.0 and _shake <= 0.0 and pose_pos == Vector3.ZERO and pose_rot == Vector3.ZERO and pose_scale == Vector3.ONE:
		_flinch = Vector3.ZERO
		_flinch_v = Vector3.ZERO
		transform = _rest
		_motion_on = false

func _end_action() -> void:
	var a := _action
	_in_action = false
	_reaction = false
	_action = &""
	_action_left = 0.0
	if not _dead:
		_request(&"loco", LOCO_RETURN_BLEND)
	action_finished.emit(a)

func _request(state: StringName, xfade: float) -> void:
	if tree == null:
		return
	(_root().get_node(&"state") as AnimationNodeTransition).xfade_time = xfade
	tree.set("parameters/state/transition_request", String(state))

func _play_fidget() -> void:
	_idle_time = 0.0
	_fidget_at = _rng.randf_range(9.0, 16.0)
	var set_: Array = FIDGETS.get(personality, [&"idle_look", &"idle_adjust"])
	var n: StringName = set_[_rng.randi_range(0, set_.size() - 1)]
	if has_anim(n):
		play_action(n, 1.0, 0.35)

func is_busy() -> bool:
	return _in_action and not _is_fidget()

func _is_fidget() -> bool:
	return _action in [&"idle_look", &"idle_adjust", &"idle_knight", &"idle_mage"]

## Cancel a fidget when the owner starts moving or fighting.
func interrupt_fidget() -> void:
	if _in_action and _is_fidget():
		_end_action()

## Length of a clip in seconds: the model's own clip when it has one (creatures with their own rigs), else metadata.
func clip_length(n: StringName, fallback := 0.7) -> float:
	if has_anim(n):
		return anim_player.get_animation(n).length
	return float(DB.anim(n).get("length", fallback))

## One-shot action (attack, cast, skill, interaction). Returns its duration in seconds at the given rate.
func play_action(n: StringName, rate := 1.0, blend := BLEND) -> float:
	if _dead:
		return 0.0
	var length := clip_length(n)
	if _floating:
		_float_pulse = 1.0
	_action = n
	_action_loop = false
	_in_action = true
	_reaction = false
	_action_left = length / maxf(rate, 0.05)
	_start_slot(n, rate, blend)
	if fallback:
		_fb_action_t = 0.0
		_fb_action_len = _action_left
	return _action_left

## Looping action (whirlwind, block, bow draw, channel, boss charge). Stays until stop_action().
func hold_action(n: StringName, rate := 1.0, blend := BLEND) -> void:
	if _dead:
		return
	_action = n
	_action_loop = true
	_in_action = true
	_reaction = false
	_action_left = 0.0
	_start_slot(n, rate, blend)

func _start_slot(n: StringName, rate: float, blend: float) -> void:
	if tree == null:
		return
	action_serial += 1
	action_rate = rate
	_slot = &"b" if _slot == &"a" else &"a"
	var node := _root().get_node(StringName("anim_" + String(_slot))) as AnimationNodeAnimation
	node.animation = n if has_anim(n) else &"idle"
	tree.set("parameters/%s_ts/scale" % _slot, rate)
	_request(_slot, blend)

func set_action_rate(rate: float) -> void:
	if tree and _in_action:
		tree.set("parameters/%s_ts/scale" % _slot, rate)

func stop_action() -> void:
	if _in_action and not _dead:       # the death pose is not an action to cancel (a fallen co-op hero stood up, bh-011)
		_end_action()

func current_action() -> StringName:
	return _action

## Upper-body overlay while the legs keep walking (guard walk, bow draw, channel). &"" clears it.
func set_upper(n: StringName, rate := 1.0) -> void:
	if tree == null:
		return
	if n == &"":
		_upper_target = 0.0
		return
	if n != _upper_anim:
		_upper_anim = n
		(_root().get_node(&"upper_anim") as AnimationNodeAnimation).animation = n if has_anim(n) else &"idle"
	tree.set("parameters/upper_ts/scale", rate)
	_upper_target = 1.0

func play_reaction(kind: StringName, direction := &"") -> void:
	if _dead:
		return
	var n: StringName
	match kind:
		&"hit":
			n = pick([StringName("hit_" + String(direction)), &"hit_light", &"hit"]) if direction != &"" else pick([&"hit_light", &"hit"])
		&"hit_heavy": n = pick([&"hit_heavy", &"hit"])
		&"stagger": n = pick([&"stagger_small", &"stagger"])
		&"stagger_heavy": n = pick([&"stagger_heavy", &"stagger"])
		&"knockback": n = &"knockback"
		&"launch": n = pick([&"launch", &"knockback"])
		&"wall": n = pick([&"wall_impact", &"hit_heavy"])
		&"knockdown": n = pick([&"knockdown", &"knockback"])
		&"land", &"getup": n = &"getup"
		&"block": n = &"block_impact"
		&"parry": n = &"parry"
		_: n = kind
	var length := clip_length(n, 0.4)
	if _floating:
		_float_pulse = maxf(_float_pulse, 0.6)
	if kind == &"hit" and _in_action and not _reaction and not _is_fidget():
		flash(Color(1, 0.9, 0.85), 0.8)
		return  # light hits don't interrupt actions; heavier reactions do
	_action = n
	_action_loop = false
	_in_action = true
	_reaction = true
	_action_left = length
	_start_slot(n, 1.0, REACTION_BLEND)
	if fallback:
		_fb_react = length

func play_death(clip: StringName = &"death") -> void:
	_dead = true
	clear_pose()
	_in_action = true
	_action_loop = true
	_upper_target = 0.0
	if tree:
		_start_slot(clip if has_anim(clip) else &"death", 1.0, 0.1)
	elif _floating:
		_float_dying = true
	elif fallback and model:
		var tw := create_tween()
		tw.tween_property(model, "rotation:x", -PI / 2.0, 0.5).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	set_rim(Color.BLACK, 0.0)
	set_trail(false)
	for id in _status_nodes.keys():
		set_status_visual(id, false)

func revive() -> void:
	_dead = false
	_in_action = false
	_action = &""
	if tree:
		play_action(&"revive" if has_anim(&"revive") else &"getup", 1.0, 0.1)
	elif fallback and model:
		model.rotation.x = 0.0

func is_dead() -> bool:
	return _dead

# ---- Overlay: hit flash and status rim ----------------------------------------------------------------------

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

# ---- Weapons ------------------------------------------------------------------------------------------------

## Per-slot regalia follows the animated skeleton; rebuilding only when the set
## piece IDs change keeps stat refreshes and inventory hovering inexpensive.
func dress_equipment(equipment: Equipment) -> void:
	var parts: Array[String] = []
	var worn := {}
	for slot in equipment.slots:
		var item := equipment.get_item(slot)
		if item and preload("res://src/actors/boss_set_visuals.gd").has_theme(item.base.set_id):
			parts.append("%s:%s" % [slot,item.base.id])
			worn[slot] = String(item.base.id)
	var signature := ",".join(parts)
	appearance["set_gear"] = worn
	if signature == _set_appearance:
		return
	_set_appearance = signature
	for old in _set_nodes:
		for mesh in _meshes.duplicate():
			if not is_instance_valid(mesh) or old.is_ancestor_of(mesh): _meshes.erase(mesh)
		old.get_parent().remove_child(old)
		old.queue_free()
	_set_nodes = preload("res://src/actors/boss_set_visuals.gd").wear(self,equipment)
	for attachment in _set_nodes:
		var meshes: Array[MeshInstance3D] = []
		_collect_into(attachment,meshes)
		for mesh in meshes:
			mesh.layers = 2
			mesh.material_overlay = _overlay
			_meshes.append(mesh)

func attach_weapon(hand: StringName, model_path: String, offset := Transform3D.IDENTITY) -> void:
	detach_weapon(hand)
	if model_path == "" or not ResourceLoader.exists(model_path):
		return
	if appearance.has("weapons"):
		appearance.weapons[hand] = [model_path, offset]
	var bone := "weapon.R" if hand == &"main" else "weapon.L"
	var holder: Node3D
	if skeleton and skeleton.find_bone(bone) >= 0:
		var ba := BoneAttachment3D.new()
		ba.bone_name = bone
		skeleton.add_child(ba)
		holder = ba
	else:
		holder = Node3D.new()
		(_fb_arm if fallback and _fb_arm else model).add_child(holder)
		holder.position = Vector3(0, 0, 0.25) if fallback else Vector3(0.35 if hand == &"main" else -0.35, 1.0, 0.1)
		if fallback:
			holder.rotation = Vector3(PI * 0.5, 0, 0)
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
	if appearance.has("weapons"):
		(appearance.weapons as Dictionary).erase(hand)
	if _weapon_nodes.has(hand):
		var n: Node = _weapon_nodes[hand]
		for m in _meshes.duplicate():
			if not is_instance_valid(m) or n.is_ancestor_of(m):
				_meshes.erase(m)
		n.queue_free()
		_weapon_nodes.erase(hand)

func has_weapon(hand: StringName) -> bool:
	return _weapon_nodes.has(hand)

## World position of a point along the weapon (0 = grip, 1 = tip) — used for trails and projectile spawns.
func weapon_point(hand := &"main", t := 1.0, length := 1.0) -> Vector3:
	if _weapon_nodes.has(hand) and is_instance_valid(_weapon_nodes[hand]):
		var n: Node3D = _weapon_nodes[hand]
		return n.global_transform * Vector3(0, length * t, 0)
	return global_position + Vector3.UP * 1.2 * model_scale + global_transform.basis.z * 0.8 * model_scale

func weapon_tip_position(hand := &"main") -> Vector3:
	return weapon_point(hand, 1.0)

## Swing trail following the main-hand weapon between grip*0.35 and tip (enabled during hit windows).
func set_trail(on: bool, color := Color(1, 0.95, 0.85, 0.6), length := 1.0) -> void:
	if on:
		if _trail == null:
			_trail = WeaponTrail.new()
			add_child(_trail)
		_trail.begin(self, color, length)
	elif _trail:
		_trail.end()

# ---- Status visuals -----------------------------------------------------------------------------------------

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
		&"poisoned": node = VFXLib.particles(Color(0.45, 0.9, 0.25, 0.7), 10, 1.2, false, 0.12, 0.4, 20.0, Vector3(0, 0.5, 0), h * 0.3)
		&"armor_broken": node = VFXLib.status_particles(Elements.EARTH, h)
		&"windswept": node = VFXLib.status_particles(Elements.WIND, h)
		&"purged": node = VFXLib.status_particles(Elements.LIGHT, h)
		&"frozen": node = VFXLib.ice_block(h, model_scale)
		&"stunned", &"staggered": node = VFXLib.stun_stars(h)
		&"bleeding": node = VFXLib.status_particles(Elements.PHYSICAL, h)
		&"haste", &"empowered": node = VFXLib.particles(Color(1.0, 0.85, 0.4, 0.6), 8, 0.8, false, 0.1, 0.8, 30.0, Vector3(0, 0.3, 0), h * 0.35)
	if node:
		if node.get_parent() == null:
			add_child(node)
		if node is GPUParticles3D and node.position == Vector3.ZERO:
			node.position = Vector3.UP * h * 0.5
		_status_nodes[id] = node
	_refresh_rim()

func _refresh_rim() -> void:
	var c := Color.BLACK
	var a := 0.0
	for id in [&"frozen", &"burning", &"shocked", &"cursed", &"poisoned", &"armor_broken", &"chilled", &"wet", &"empowered"]:
		if _status_nodes.has(id):
			match id:
				&"frozen": c = Color(0.6, 0.9, 1.0); a = 1.2
				&"burning": c = Color(1.0, 0.45, 0.1); a = 0.9
				&"shocked": c = Color(1.0, 0.95, 0.4); a = 0.8
				&"cursed": c = Color(0.6, 0.2, 0.9); a = 0.8
				&"poisoned": c = Color(0.4, 0.85, 0.2); a = 0.6
				&"armor_broken": c = Color(0.8, 0.55, 0.25); a = 0.5
				&"chilled": c = Color(0.5, 0.8, 1.0); a = 0.5
				&"wet": c = Color(0.2, 0.45, 0.9); a = 0.4
				&"empowered": c = Color(1.0, 0.8, 0.3); a = 0.4
			break
	_frozen_pose = _status_nodes.has(&"frozen") and not _dead
	if tree:
		tree.active = _anim_awake and not _frozen_pose
	set_rim(c, a)

# ---- Fallback body (used when a model file is missing, e.g. before the character builder delivers) ----------

var _fb_action_t := 0.0
var _fb_action_len := 0.0
var _fb_react := 0.0
var _fb_arm: Node3D
var _fb_bob := 0.0
var _fb_speed := 0.0

func _build_fallback() -> Node3D:
	var root := Node3D.new()
	root.name = "FallbackBody"
	var mat := StandardMaterial3D.new()
	mat.albedo_color = tint_primary.darkened(0.25)
	mat.roughness = 0.6
	var body := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.3
	cap.height = 1.45
	body.mesh = cap
	body.position.y = 0.85
	body.material_override = mat
	root.add_child(body)
	var head := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.19
	sph.height = 0.38
	head.mesh = sph
	head.position.y = 1.7
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color(0.55, 0.52, 0.5)
	head.material_override = hm
	root.add_child(head)
	_fb_arm = Node3D.new()
	_fb_arm.position = Vector3(0.36, 1.25, 0.0)
	root.add_child(_fb_arm)
	return root

func _animate_fallback(delta: float) -> void:
	if _dead or model == null:
		return
	_fb_bob += delta * (4.0 + _fb_speed * 2.0)
	model.position.y = absf(sin(_fb_bob)) * 0.05 * minf(_fb_speed, 1.0)
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
		model.rotation.x = lerpf(model.rotation.x, 0.12 * _hurt, delta * 4.0)

# ---- Per-instance materials: stealth shimmer, corpse darkening and dissolve ------------------------------------

var _local_mats := {}               # MeshInstance3D -> Array[StandardMaterial3D] (instance copies of the overrides)
var _opacity := 1.0

func _ensure_local_materials() -> void:
	if not _local_mats.is_empty():
		return
	for m in _meshes:
		if not is_instance_valid(m) or m.mesh == null:
			continue
		var arr: Array = []
		for i in m.mesh.get_surface_count():
			var src := m.get_surface_override_material(i)
			if src == null:
				src = m.mesh.surface_get_material(i)
			var c: Material = src.duplicate() if src else StandardMaterial3D.new()
			if c is BaseMaterial3D:
				(c as BaseMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
			m.set_surface_override_material(i, c)
			arr.append(c)
		_local_mats[m] = arr

## 1 = solid, 0 = gone. Dithered (alpha hash), so it stays depth-sorted and cheap.
func set_opacity(a: float) -> void:
	a = clampf(a, 0.0, 1.0)
	if is_equal_approx(a, _opacity):
		return
	_opacity = a
	_ensure_local_materials()
	for arr in _local_mats.values():
		for c in arr:
			if c is BaseMaterial3D:
				(c as BaseMaterial3D).albedo_color.a = a

## Corpse decay: darken and desaturate the body toward `tint` by `amount` (0..1). Emission dies with it.
func set_decay(amount: float, tint := Color(0.16, 0.14, 0.12)) -> void:
	_ensure_local_materials()
	for arr in _local_mats.values():
		for c in arr:
			if not c is BaseMaterial3D:
				continue
			var b := c as BaseMaterial3D
			if not b.has_meta(&"base_albedo"):
				b.set_meta(&"base_albedo", b.albedo_color)
				b.set_meta(&"base_emission", b.emission_energy_multiplier)
			var base: Color = b.get_meta(&"base_albedo")
			var grey := base.get_luminance()
			var c2 := base.lerp(Color(grey, grey, grey), amount * 0.6).lerp(tint, amount * 0.55)
			c2.a = b.albedo_color.a
			b.albedo_color = c2
			b.emission_energy_multiplier = float(b.get_meta(&"base_emission")) * (1.0 - amount)

# ---- Floating Aether creature (no skeleton: core + spinning shard rings + ribbons) ----------------------------

var _floating := false
var _float_t := 0.0
var _float_pulse := 0.0
var _float_dying := false
var _float_rings: Array[Node3D] = []
var _float_core: Node3D
var _float_ribbons: Node3D
var _float_light: OmniLight3D
var _float_wings: Array[Node3D] = []
## Height the floating model hovers at (bh-013: 0 for a nest that sits on the ground); set by the owner.
var float_hover := 1.2
## Turns of the core per second about its own up axis (bh-013: a Void Rift's vortex swirls); set by the owner.
var float_core_spin := 0.0

func _setup_floating() -> void:
	_floating = true
	_float_core = model.find_child("core", true, false) as Node3D
	_float_ribbons = model.find_child("ribbons", true, false) as Node3D
	for i in range(1, 6):
		var r := model.find_child("ring_%d" % i, true, false) as Node3D
		if r:
			_float_rings.append(r)
	for wn in ["wing_l", "wing_r"]:
		var w := model.find_child(wn, true, false) as Node3D
		if w:
			w.set_meta(&"rest", w.transform)
			_float_wings.append(w)
	_float_light = OmniLight3D.new()
	# the Aether wisp's cyan by default; other floating creatures (bh-012: Ice Wraith, Starmote) glow in their own tint
	_float_light.light_color = Color(0.5, 0.95, 1.0) if tint_primary == Color.WHITE else tint_primary.lerp(Color.WHITE, 0.25)
	_float_light.light_energy = 1.4
	_float_light.omni_range = 5.0
	add_child(_float_light)
	_float_t = _rng.randf() * 10.0

func _animate_floating(delta: float) -> void:
	_float_t += delta
	_float_pulse = maxf(0.0, _float_pulse - delta * 1.6)
	var hover := float_hover * model_scale
	if _float_dying:
		# implode: rings collapse into the core, then everything winks out
		model.scale = model.scale.lerp(Vector3.ONE * 0.01, 1.0 - exp(-5.0 * delta))
		if _float_light:
			_float_light.light_energy = lerpf(_float_light.light_energy, 0.0, 1.0 - exp(-4.0 * delta))
		return
	# a structure on the ground (hover 0: the Waxen Hive) stays planted; everything else bobs
	var grounded := float_hover <= 0.01
	model.position.y = hover if grounded else hover + sin(_float_t * 1.7) * 0.12 + _loco_pos.length() * 0.05
	var spin := 1.0 + _float_pulse * 4.0 + _combat * 0.8
	for i in _float_rings.size():
		# each ring keeps its authored tilt and spins in its own plane (local +Y)
		var r := _float_rings[i]
		r.rotate_object_local(Vector3.UP, delta * (0.9 + 0.55 * i) * spin * (1.0 if i % 2 == 0 else -1.0))
		var sc := 1.0 - 0.25 * _float_pulse
		r.basis = r.basis.orthonormalized().scaled(Vector3.ONE * sc)
	if _float_core:
		var breathe := 0.03 * sin(_float_t * 2.0) + 0.12 * _float_pulse if grounded else 0.08 * sin(_float_t * 5.0) + 0.35 * _float_pulse
		_float_core.scale = Vector3.ONE * (1.0 + breathe)
		if float_core_spin != 0.0:
			_float_core.rotate_object_local(Vector3.UP, delta * TAU * float_core_spin)
	for wi in _float_wings.size():
		# bh-013: insect wings beat about their root (local Z), mirrored left and right
		var w := _float_wings[wi]
		var rest: Transform3D = w.get_meta(&"rest")
		var flap := sin(_float_t * 38.0) * deg_to_rad(35.0) * (1.0 if wi == 0 else -1.0)
		w.transform = rest * Transform3D(Basis(Vector3.BACK, flap), Vector3.ZERO)
	if _float_ribbons:
		_float_ribbons.rotation.y += delta * 0.6
		_float_ribbons.rotation.x = sin(_float_t * 1.3) * 0.12 - _loco_pos.y * 0.15
	if _float_light:
		_float_light.position.y = hover
		_float_light.light_energy = 1.2 + 0.3 * sin(_float_t * 3.0) + 2.5 * _float_pulse
