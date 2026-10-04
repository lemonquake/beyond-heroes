class_name PlayerCamera
extends Camera3D
## Isometric follow camera: critically-damped follow with a small look-ahead toward the aim point, wheel zoom,
## trauma-based screen shake (Settings.screen_shake), and occlusion fading of architecture between camera and hero.
## bh-030: first-person view. The camera sits at the hero's eyes and looks where the mouse turns it (captured while
## no window is open); WASD moves relative to the view, the hero always faces it, and attacks go to the crosshair.
## On a touch screen a drag on the open screen turns the view.

const PITCH := 54.0
const YAW := 0.0
const ZOOM_MIN := 10.0
const ZOOM_MAX := 24.0
const FOLLOW_RATE := 9.0
const LOOK_AHEAD := 0.12            # fraction of the aim offset the camera leans toward
const MAX_LOOK_AHEAD := 2.5
const SHAKE_DECAY := 1.6
const SHAKE_MAX_OFFSET := 0.45
const SHAKE_MAX_ROLL := 0.035

var target: Node3D
var dist := 16.0
var _dist_target := 16.0
var _focus := Vector3.ZERO
var _trauma := 0.0
var _t := 0.0
var _noise := FastNoiseLite.new()
var _faded := {}                    # MeshInstance3D -> {surface: original override material}
var _fade_timer := 0.0
var first_person := false
var fp_yaw := 0.0                   # radians; 0 looks toward -Z like the isometric view
var fp_pitch := -0.12
const EYE := 1.62
const EYE_FORWARD := 0.22           # just in front of the face, so the inside of a helmet never fills the screen
const FP_SENS := 0.0028
const PITCH_LIMIT := 1.35
var _captured := false

func _ready() -> void:
	top_level = true
	# bh-030: keeps running while the game is paused, so the pause menu always gets the mouse back in first person
	process_mode = Node.PROCESS_MODE_ALWAYS
	fov = 40.0
	far = 90.0 if Perf.lite else 400.0   # efficiency mode: the fog hides the horizon anyway
	near = 0.3
	_noise.seed = 7
	_noise.frequency = 1.0
	Events.camera_shake.connect(add_trauma)
	dist = Settings.camera_zoom * 16.0 if Settings.camera_zoom > 0.0 else 16.0
	_dist_target = dist

func add_trauma(amount: float) -> void:
	_trauma = clampf(_trauma + amount * Settings.screen_shake, 0.0, 1.0)

func zoom(delta_steps: float) -> void:
	_dist_target = clampf(_dist_target + delta_steps * 1.5, ZOOM_MIN, ZOOM_MAX)

func snap() -> void:
	if target == null:
		return
	_focus = target.global_position + Vector3.UP * 1.1
	_apply(0.0)

func offset_dir() -> Vector3:
	return Vector3(0, 0, 1).rotated(Vector3.RIGHT, -deg_to_rad(PITCH)).rotated(Vector3.UP, deg_to_rad(YAW))

## World-space right/forward on the ground plane (for camera-relative movement input).
func ground_basis() -> Basis:
	return Basis(Vector3.UP, fp_yaw) if first_person else Basis(Vector3.UP, deg_to_rad(YAW))

## bh-030: switch between the isometric and the first-person view. The view starts looking the way the hero faces.
func set_first_person(on: bool) -> void:
	first_person = on
	clear_occlusion()
	near = 0.05 if on else 0.3
	if on and target:
		var f: Vector3 = target.global_transform.basis.z
		fp_yaw = atan2(-f.x, -f.z)
		fp_pitch = -0.12
	apply_fov()
	_update_capture()

func apply_fov() -> void:
	fov = clampf(Settings.fp_fov, 50.0, 120.0) if first_person else 40.0

## The direction the first-person view looks (the crosshair).
func look_dir() -> Vector3:
	return -global_transform.basis.z

## Mouse look: the mouse is captured while playing in first person and freed for any window, menu or pause.
func _update_capture() -> void:
	var want := first_person and not Settings.touch_mode and Game.in_session and not Game.ui_blocking and not get_tree().paused \
		and DisplayServer.get_name() != "headless"
	if want != _captured:
		_captured = want
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if want else Input.MOUSE_MODE_VISIBLE

func _unhandled_input(e: InputEvent) -> void:
	if not first_person:
		return
	if e is InputEventMouseMotion and _captured:
		_turn((e as InputEventMouseMotion).relative * FP_SENS * Settings.mouse_sensitivity)
	elif e is InputEventScreenDrag and Settings.touch_mode:
		# a drag that no on-screen control took turns the view
		_turn((e as InputEventScreenDrag).relative * FP_SENS * 1.6 * Settings.mouse_sensitivity)

func _turn(d: Vector2) -> void:
	fp_yaw = wrapf(fp_yaw - d.x, -PI, PI)
	fp_pitch = clampf(fp_pitch - d.y, -PITCH_LIMIT, PITCH_LIMIT)

func _exit_tree() -> void:
	if _captured:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		_captured = false

func _process(delta: float) -> void:
	if target == null or not is_instance_valid(target) or not is_finite(delta):
		return
	if get_tree().paused:
		_update_capture()
		return
	_t += delta
	if first_person:
		_update_capture()
		_trauma = maxf(0.0, _trauma - SHAKE_DECAY * delta)
		_apply_first_person()
		return
	dist = lerpf(dist, _dist_target, 1.0 - exp(-10.0 * delta))
	var tp := _target_pos()
	var want := tp + Vector3.UP * 1.1
	if target.get("aim_point") != null:
		var ap: Vector3 = target.aim_point
		var lean := (ap - tp) * LOOK_AHEAD
		lean.y = 0.0
		if lean.length() > MAX_LOOK_AHEAD:
			lean = lean.normalized() * MAX_LOOK_AHEAD
		want += lean
	_focus = _focus.lerp(want, 1.0 - exp(-FOLLOW_RATE * delta))
	_trauma = maxf(0.0, _trauma - SHAKE_DECAY * delta)
	_apply(delta)
	_fade_timer -= delta
	if _fade_timer <= 0.0:
		_fade_timer = 0.1
		_update_occlusion()

## bh-037: where the hero is drawn this frame (between its last two physics steps, CharacterVisual.smoothed_body_transform).
## Following the raw body made the camera step at 60 Hz on a faster screen.
func _target_pos() -> Vector3:
	var v = target.get(&"visual")
	if v is CharacterVisual and is_instance_valid(v) and (v as CharacterVisual).smooth_motion:
		return (v as CharacterVisual).smoothed_body_transform().origin
	return target.global_position

func _apply(_delta: float) -> void:
	var off := offset_dir() * dist
	var pos := _focus + off
	var roll := 0.0
	if _trauma > 0.0 and not Settings.reduced_motion:
		var s := _trauma * _trauma
		pos += Vector3(_noise.get_noise_2d(_t * 23.0, 1.0), _noise.get_noise_2d(_t * 23.0, 50.0), _noise.get_noise_2d(_t * 23.0, 99.0)) * SHAKE_MAX_OFFSET * s
		roll = _noise.get_noise_2d(_t * 17.0, 200.0) * SHAKE_MAX_ROLL * s
	global_position = pos
	look_at(pos - off, Vector3.UP)
	rotate_object_local(Vector3.FORWARD, roll)

func _apply_first_person() -> void:
	var flat := Vector3(-sin(fp_yaw), 0.0, -cos(fp_yaw))
	var pos: Vector3 = _target_pos() + Vector3.UP * EYE + flat * EYE_FORWARD
	if _trauma > 0.0 and not Settings.reduced_motion:
		var s := _trauma * _trauma * 0.25
		pos += Vector3(_noise.get_noise_2d(_t * 23.0, 1.0), _noise.get_noise_2d(_t * 23.0, 50.0), 0.0) * SHAKE_MAX_OFFSET * s
	global_position = pos
	global_rotation = Vector3(fp_pitch, fp_yaw, 0.0)

## Fade architecture that hides the hero (dithered alpha copy of each material), restore when clear.
func _update_occlusion() -> void:
	var still := {}
	var world := get_world_3d()
	if world and target:
		var from := global_position
		for h in [0.4, 1.2, 1.8]:
			var to: Vector3 = target.global_position + Vector3.UP * h
			var exclude: Array[RID] = []
			for i in 4:
				var q := PhysicsRayQueryParameters3D.create(from, to, BH.LAYER_WORLD)
				q.exclude = exclude
				var hit := world.direct_space_state.intersect_ray(q)
				if hit.is_empty():
					break
				exclude.append(hit.rid)
				var root := _kit_root(hit.collider)
				if root:
					for mi in root.find_children("*", "MeshInstance3D", true, false):
						still[mi] = true
	for mi in still:
		if not _faded.has(mi) and is_instance_valid(mi):
			var orig := {}
			for s in mi.mesh.get_surface_count():
				orig[s] = mi.get_surface_override_material(s)
				mi.set_surface_override_material(s, MaterialLibrary.faded(mi.get_active_material(s)))
			_faded[mi] = orig
	for mi in _faded.keys():
		if not still.has(mi):
			if is_instance_valid(mi):
				var orig: Dictionary = _faded[mi]
				for s in orig:
					mi.set_surface_override_material(s, orig[s])
			_faded.erase(mi)

## The placed kit piece that owns a collider (direct child of the map's Geometry/Props group).
func _kit_root(col: Object) -> Node3D:
	var n := col as Node
	var last: Node3D = null
	while n != null and not (n is MapRoot):
		if n is Node3D:
			last = n
		var p := n.get_parent()
		if p != null and (p.name == "Geometry" or p.name == "Props"):
			return n as Node3D
		n = p
	return null

func clear_occlusion() -> void:
	for mi in _faded.keys():
		if is_instance_valid(mi):
			var orig: Dictionary = _faded[mi]
			for s in orig:
				mi.set_surface_override_material(s, orig[s])
	_faded.clear()
