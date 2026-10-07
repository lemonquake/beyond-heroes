class_name Barrage
extends Node3D
## bh-042: bullet patterns for the Abyss bosses (docs/PLAN_bh-042.md, phase 2). One node carries a whole volley: every
## shot is plain data (position, velocity, curve, homing), drawn by two MultiMeshes (a glow and a white core) and tested
## against the few actors of the target team by distance, so a sixty-shot ring costs about as much as one projectile.
## Shots fly at chest height, stop at walls (a ray per shot every few frames), and can be evaded or rolled through like
## any aimed blow. A copy without a request (multiplayer: other machines) is drawn but never hits.
##
## Patterns (the attack's "pattern"):
##   radial  rings of `count` shots, `waves` rings `gap` s apart, each ring turned by `turn` degrees
##   spiral  `arms` streams turning `spin` degrees per second for `duration` s, `rate` shots per second per arm
##   fan     `waves` aimed fans of `count` shots over `spread` degrees, re-aimed every wave
##   wall    `waves` lines of shots `spacing` m apart and `width` m wide, aimed, with a `gap` m hole somewhere in each
##   orbit   rings whose shots curve (`curve` degrees per second) so the ring spirals outward
##   homing  `count` slow orbs that turn toward their target (`homing` degrees per second) for `seek` s
##   cross   a spiral with four arms, fast and dense

const SHOT_Y := 1.15
const WALL_EVERY := 4
const HIT_GAP := 0.18                       # one target is hit at most this often by one volley

var source: Node3D
var request: DamageRequest
var mask := BH.LAYER_PLAYER
var color := Color(0.3, 0.95, 0.9)
var radius := 0.38
var on_hit: Callable:                        # func(target: Actor, result: DamageResult)
	set(v):
		on_hit = v
		_on_hit_owner = SafeCallable.owner_of(v)
var _on_hit_owner := 0

var _plan: Array = []                        # pending shots: [time, angle_deg or -1 (aimed), extra dict]
var _clock := 0.0
var _a := {}
var _aim := Vector3.FORWARD
var _target: Node3D
var _origin := Vector3.ZERO
var _pos := PackedVector3Array()
var _vel := PackedVector3Array()
var _last := PackedVector3Array()
var _curve := PackedFloat32Array()
var _home := PackedFloat32Array()
var _left := PackedFloat32Array()
var _seek := PackedFloat32Array()
var _frame := 0
var _hit_cd := {}
var _targets: Array = []
var _targets_t := 0.0
var _glow: MultiMeshInstance3D
var _core: MultiMeshInstance3D

static var _sphere: SphereMesh

## Fire attack `a` from `from` toward `target` (or `aim` when there is no target). `req` null = visual copy only.
static func fire(parent: Node, a: Dictionary, from: Vector3, aim: Vector3, target: Node3D, req: DamageRequest, src: Node3D,
		p_mask := BH.LAYER_PLAYER) -> Barrage:
	var b := Barrage.new()
	Perf.mark_fx(b)
	b._a = a
	b.request = req
	b.source = src
	b.mask = p_mask
	b._target = target
	b._aim = Vector3(aim.x, 0.0, aim.z).normalized() if Vector3(aim.x, 0.0, aim.z).length() > 0.01 else Vector3.FORWARD
	b.color = a.get("color", b.color)
	b.radius = float(a.get("shot_radius", b.radius))
	parent.add_child(b)
	b.global_position = Vector3.ZERO
	b._origin = Vector3(from.x, from.y + SHOT_Y, from.z)
	b._build_plan()
	b._build_meshes()
	return b

func _build_plan() -> void:
	var pattern := String(_a.get("pattern", "radial"))
	var base := rad_to_deg(atan2(_aim.x, _aim.z))
	match pattern:
		"radial", "orbit":
			var n := int(_a.get("count", 24))
			var waves := int(_a.get("waves", 3))
			var gap := float(_a.get("gap", 0.45))
			var turn := float(_a.get("turn", 180.0 / maxf(1.0, n)))
			for w in waves:
				for i in n:
					_plan.append([w * gap, base + w * turn + 360.0 * i / n, {"curve": float(_a.get("curve", 0.0)) * (1.0 if w % 2 == 0 else -1.0)}])
		"spiral", "cross":
			var arms := int(_a.get("arms", 4 if pattern == "cross" else 3))
			var dur := float(_a.get("duration", 3.0))
			var rate := float(_a.get("rate", 10.0 if pattern == "cross" else 7.0))
			var spin := float(_a.get("spin", 40.0 if pattern == "cross" else 110.0))
			var steps := int(dur * rate)
			for s in steps:
				var t := float(s) / rate
				for k in arms:
					_plan.append([t, base + spin * t + 360.0 * k / arms, {}])
		"fan":
			var n := int(_a.get("count", 9))
			var spread := float(_a.get("spread", 70.0))
			var waves := int(_a.get("waves", 4))
			var gap := float(_a.get("gap", 0.35))
			for w in waves:
				for i in n:
					var off := 0.0 if n == 1 else lerpf(-spread * 0.5, spread * 0.5, float(i) / float(n - 1))
					_plan.append([w * gap, -1.0, {"off": off + (spread / maxf(1.0, n - 1) * 0.5 if w % 2 == 1 else 0.0)}])
		"wall":
			var waves := int(_a.get("waves", 3))
			var gap_t := float(_a.get("gap_time", 0.9))
			var width := float(_a.get("width", 18.0))
			var spacing := float(_a.get("spacing", 1.1))
			var hole := float(_a.get("gap", 3.0))
			var r := RandomNumberGenerator.new()
			r.seed = int(_a.get("seed", 0)) if _a.has("seed") else randi()
			for w in waves:
				var hole_at := r.randf_range(-width * 0.5 + hole, width * 0.5 - hole)
				var x := -width * 0.5
				while x <= width * 0.5:
					if absf(x - hole_at) > hole * 0.5:
						_plan.append([w * gap_t, -1.0, {"lateral": x}])
					x += spacing
		"homing":
			var n := int(_a.get("count", 6))
			for i in n:
				_plan.append([i * float(_a.get("gap", 0.12)), base + lerpf(-80.0, 80.0, float(i) / maxf(1.0, n - 1)), {"homing": float(_a.get("homing", 120.0))}])
	_plan.sort_custom(func(x, y): return x[0] < y[0])

func _build_meshes() -> void:
	if _sphere == null:
		_sphere = SphereMesh.new()
		_sphere.radial_segments = 10
		_sphere.rings = 5
		_sphere.radius = 0.5
		_sphere.height = 1.0
	var total := _plan.size()
	_glow = _multi(total, VFXLib.glow_material(color, 2.6), radius * 2.0)
	_core = _multi(total, VFXLib.glow_material(Color(1, 1, 1, 0.9), 1.6), radius * 0.95)

func _multi(n: int, mat: Material, size: float) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _sphere
	mm.instance_count = maxi(1, n)
	mm.visible_instance_count = 0
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.set_meta(&"size", size)
	add_child(mi)
	return mi

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_clock += delta
	_frame += 1
	_spawn_due()
	_step(delta)
	_draw()
	if _plan.is_empty() and _pos.is_empty():
		queue_free()

## The muzzle: the source while it lives (spirals follow a moving boss), else where the volley began.
func _muzzle() -> Vector3:
	if is_instance_valid(source) and source.is_inside_tree() and (not (source is Actor) or (source as Actor).alive):
		var p := source.global_position
		return Vector3(p.x, p.y + SHOT_Y, p.z)
	return _origin

func _aim_now(from: Vector3) -> Vector3:
	if is_instance_valid(_target) and _target.is_inside_tree():
		var d := _target.global_position - from
		d.y = 0.0
		if d.length() > 0.2:
			return d.normalized()
	return _aim

func _spawn_due() -> void:
	var speed := float(_a.get("speed", 9.0))
	var reach := float(_a.get("reach", 26.0))
	var seek := float(_a.get("seek", 2.5))
	while not _plan.is_empty() and float(_plan[0][0]) <= _clock:
		var s: Array = _plan.pop_front()
		var from := _muzzle()
		var ex: Dictionary = s[2]
		var dir: Vector3
		if float(s[1]) < 0.0:
			var aim := _aim_now(from)
			dir = aim.rotated(Vector3.UP, deg_to_rad(float(ex.get("off", 0.0))))
			if ex.has("lateral"):
				from += aim.cross(Vector3.UP).normalized() * float(ex.lateral) - aim * 2.0
		else:
			var ang := deg_to_rad(float(s[1]))
			dir = Vector3(sin(ang), 0.0, cos(ang))
		_pos.append(from)
		_last.append(from)
		_vel.append(dir * speed)
		_curve.append(deg_to_rad(float(ex.get("curve", 0.0))))
		_home.append(deg_to_rad(float(ex.get("homing", 0.0))))
		_seek.append(seek)
		_left.append(reach)

func _step(delta: float) -> void:
	var world := get_world_3d()
	if world == null:
		return
	_targets_t -= delta
	if request != null and _targets_t <= 0.0:
		_targets_t = 0.15
		_targets = CombatQuery.actors_in_radius(world, _muzzle(), float(_a.get("reach", 26.0)) + 8.0, mask, 16)
	for k in _hit_cd.keys():
		_hit_cd[k] = float(_hit_cd[k]) - delta
		if _hit_cd[k] <= 0.0:
			_hit_cd.erase(k)
	var i := 0
	while i < _pos.size():
		var v := _vel[i]
		if _curve[i] != 0.0:
			v = v.rotated(Vector3.UP, _curve[i] * delta)
		if _home[i] > 0.0 and _seek[i] > 0.0:
			_seek[i] -= delta
			var t := _homing_target(_pos[i])
			if t:
				var want := (t.global_position - _pos[i])
				want.y = 0.0
				if want.length() > 0.1:
					var cur := atan2(v.x, v.z)
					var goal := atan2(want.x, want.z)
					var turn := clampf(wrapf(goal - cur, -PI, PI), -_home[i] * delta, _home[i] * delta)
					v = v.rotated(Vector3.UP, turn)
		_vel[i] = v
		var step := v * delta
		_pos[i] += step
		_left[i] -= step.length()
		var gone := _left[i] <= 0.0
		if not gone and (_frame + i) % WALL_EVERY == 0:
			var q := PhysicsRayQueryParameters3D.create(_last[i], _pos[i], BH.LAYER_WORLD)
			if not world.direct_space_state.intersect_ray(q).is_empty():
				gone = true
			_last[i] = _pos[i]
		if not gone and request != null:
			gone = _test_hit(_pos[i])
		if gone:
			_remove(i)
		else:
			i += 1

func _homing_target(p: Vector3) -> Node3D:
	if is_instance_valid(_target) and _target.is_inside_tree():
		return _target
	return null

func _test_hit(p: Vector3) -> bool:
	for t in _targets:
		if not is_instance_valid(t) or not (t is Actor) or not (t as Actor).alive or t == source:
			continue
		var a := t as Actor
		var dh := Vector2(a.global_position.x - p.x, a.global_position.z - p.z).length()
		if dh > radius + a.body_radius:
			continue
		if p.y < a.global_position.y - 0.3 or p.y > a.global_position.y + a.body_height + 0.3:
			continue
		var id: int = a.get_instance_id()
		if _hit_cd.has(id):
			return true                    # spent on a target that was just struck (no stacking from one ring)
		_hit_cd[id] = HIT_GAP
		var req := request.clone()
		req.tags[&"projectile"] = true
		req.tags[&"push_dir"] = (a.global_position - p).slide(Vector3.UP).normalized()
		var res := a.receive_hit(req, source if is_instance_valid(source) else null, p)
		if SafeCallable.alive(on_hit, _on_hit_owner):
			on_hit.call(a, res)
		return true
	return false

func _remove(i: int) -> void:
	# packed arrays are copied on write: each one is moved by name
	var last := _pos.size() - 1
	_pos[i] = _pos[last]
	_vel[i] = _vel[last]
	_last[i] = _last[last]
	_curve[i] = _curve[last]
	_home[i] = _home[last]
	_left[i] = _left[last]
	_seek[i] = _seek[last]
	_pos.resize(last)
	_vel.resize(last)
	_last.resize(last)
	_curve.resize(last)
	_home.resize(last)
	_left.resize(last)
	_seek.resize(last)

func _draw() -> void:
	for mi in [_glow, _core]:
		var mm := (mi as MultiMeshInstance3D).multimesh
		var size := float(mi.get_meta(&"size"))
		var n := mini(_pos.size(), mm.instance_count)
		mm.visible_instance_count = n
		var basis := Basis.IDENTITY.scaled(Vector3.ONE * size)
		for i in n:
			mm.set_instance_transform(i, Transform3D(basis, _pos[i]))

## Shots still flying (tests).
func live_shots() -> int:
	return _pos.size()

func pending_shots() -> int:
	return _plan.size()
