extends Node
## Perf (autoload, bh-009): the runtime half of efficiency mode (Settings.lite, on with Mobile). The build-time half
## lives in the map builders, materials and effects, which ask `Perf.lite` and take their cheap path.
##
## While efficiency mode is on, five times a second:
##  - Light budget: only the LIGHT_BUDGET point/spot lights nearest the hero shine; the rest are switched off in the
##    renderer (not on the node, so gameplay code that shows or hides its own lights is never overridden). Low-end
##    phones draw every lit object once more per light, so 70 torches in a town are what makes it unplayable.
##  - Animation sleep: characters off screen or far away stop evaluating their AnimationTree (the pose freezes where
##    nobody can see it). Gameplay never reads the pose, so combat and AI are unaffected.
## Nothing here changes a desktop session: with efficiency mode off every light and tree is left alone.

const LIGHT_BUDGET := 6
const LIGHT_RADIUS := 32.0          # a light further than this from the hero never takes a slot
const ANIM_RANGE := 40.0            # characters further than this from the camera focus stop animating
const FRUSTUM_MARGIN := 3.0         # metres outside the screen edge that still count as on screen
const TICK := 0.2

## Efficiency mode (Settings.lite), mirrored here so builders and effects have one short name to ask.
var lite: bool:
	get: return Settings.lite

var _lights: Array[Light3D] = []
var _visuals: Array[CharacterVisual] = []
var _off_lights := {}               # Light3D -> true while this governor keeps it dark
var _t := 0.0
var _was_lite := false
## Last tick's numbers (perf probe, tests).
var stats := {"lights_total": 0, "lights_on": 0, "visuals": 0, "anim_awake": 0}

func _ready() -> void:
	get_tree().node_added.connect(_on_node_added)

func _on_node_added(n: Node) -> void:
	if n is OmniLight3D or n is SpotLight3D:
		_lights.append(n)
	elif n is CharacterVisual:
		_visuals.append(n)

## Particle counts in efficiency mode: fewer sparks, same look (at least one).
func particles(amount: int) -> int:
	return maxi(1, int(ceil(amount * 0.4))) if lite else amount

var _fps_t := 0.0

func _process(delta: float) -> void:
	# debug builds on a phone: the frame rate in logcat every 5 s (`adb logcat -s godot`), for testing on real devices
	if OS.is_debug_build() and Settings.is_mobile_device():
		_fps_t += delta
		if _fps_t >= 5.0:
			_fps_t = 0.0
			print("BH_FPS %d lite=%s lights_on=%d anim_awake=%d/%d" % [Engine.get_frames_per_second(), lite, stats.lights_on, stats.anim_awake, stats.visuals])
	if not lite:
		if _was_lite:
			_restore()
		return
	_was_lite = true
	_t -= delta
	if _t > 0.0:
		return
	_t = TICK
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var focus := _focus(cam)
	_budget_lights(focus)
	_sleep_animations(cam, focus)

## The hero if there is one, else the ground point the camera looks at (title screen backdrop).
func _focus(cam: Camera3D) -> Vector3:
	var p = Game.player
	if p and is_instance_valid(p) and p.is_inside_tree():
		return (p as Node3D).global_position
	return cam.global_position - cam.global_basis.z * 18.0

func _budget_lights(focus: Vector3) -> void:
	var cand: Array = []
	var i := 0
	while i < _lights.size():
		var l := _lights[i]
		if not is_instance_valid(l):
			_lights.remove_at(i)
			continue
		i += 1
		if not l.is_inside_tree():
			continue
		var reach: float = (l as OmniLight3D).omni_range if l is OmniLight3D else (l as SpotLight3D).spot_range
		cand.append([l.global_position.distance_to(focus) - reach * 0.35, l])
	cand.sort_custom(func(a, b): return a[0] < b[0])
	var on := 0
	for c in cand:
		var l: Light3D = c[1]
		var want: bool = on < LIGHT_BUDGET and c[0] < LIGHT_RADIUS and l.is_visible_in_tree() and l.light_energy > 0.0
		if want:
			on += 1
		_set_light(l, want)
	stats.lights_total = cand.size()
	stats.lights_on = on

func _set_light(l: Light3D, on: bool) -> void:
	if on:
		if _off_lights.has(l):
			_off_lights.erase(l)
			RenderingServer.instance_set_visible(l.get_instance(), l.is_visible_in_tree())
	else:
		# re-applied every tick: the node resets its renderer visibility whenever its own `visible` changes
		_off_lights[l] = true
		RenderingServer.instance_set_visible(l.get_instance(), false)

func _sleep_animations(cam: Camera3D, focus: Vector3) -> void:
	var planes := cam.get_frustum()
	var awake := 0
	var i := 0
	while i < _visuals.size():
		var v := _visuals[i]
		if not is_instance_valid(v):
			_visuals.remove_at(i)
			continue
		i += 1
		if v.tree == null or not v.is_inside_tree():
			continue
		var p := v.global_position + Vector3.UP
		var show := p.distance_to(focus) < ANIM_RANGE and v.is_visible_in_tree()
		if show:
			for pl: Plane in planes:
				if pl.distance_to(p) > FRUSTUM_MARGIN:   # frustum planes point outward
					show = false
					break
		v.set_anim_awake(show)
		if show:
			awake += 1
	stats.visuals = _visuals.size()
	stats.anim_awake = awake

## Efficiency mode was switched off: give every light and animation back.
func _restore() -> void:
	_was_lite = false
	for l in _off_lights:
		if is_instance_valid(l):
			RenderingServer.instance_set_visible(l.get_instance(), l.is_visible_in_tree())
	_off_lights.clear()
	for v in _visuals:
		if is_instance_valid(v):
			v.set_anim_awake(true)
