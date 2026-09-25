class_name CombatQuery
## Spatial queries for hit detection. Uses the physics server (no Area3D hitboxes) so hit windows
## are evaluated exactly on the frames the animation metadata says the weapon connects.

static var _sphere := SphereShape3D.new()

## Living actors of `team_mask` layers whose body is within `radius` of `center` (horizontal distance
## uses body radius so large enemies are hit at their edge).
static func actors_in_radius(world: World3D, center: Vector3, radius: float, layer_mask: int, max_results := 48) -> Array:
	var space := world.direct_space_state
	_sphere.radius = radius + 1.5
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = _sphere
	q.transform = Transform3D(Basis.IDENTITY, center)
	q.collision_mask = layer_mask
	q.collide_with_areas = false
	var out := []
	for hit in space.intersect_shape(q, max_results):
		var a = hit.collider
		if a is Actor and a.alive and not out.has(a):
			var d := Vector2(a.global_position.x - center.x, a.global_position.z - center.z).length()
			if d <= radius + a.body_radius and absf(a.global_position.y - center.y) < 3.0 + a.body_height:
				out.append(a)
	return out

## Actors inside a horizontal cone (facing = forward direction, arc in degrees).
static func actors_in_arc(world: World3D, origin: Vector3, facing: Vector3, reach: float, arc_deg: float, layer_mask: int) -> Array:
	var out := []
	var f := Vector3(facing.x, 0, facing.z).normalized()
	var half := deg_to_rad(arc_deg) * 0.5
	for a in actors_in_radius(world, origin, reach, layer_mask):
		var to := a.global_position - origin
		to.y = 0.0
		var dist := to.length()
		if dist < a.body_radius + 0.4:
			out.append(a)   # overlapping bodies are always hit
			continue
		# Widen the cone by the target's angular size so big enemies at the edge still register.
		var ang := f.angle_to(to.normalized())
		var slack := atan2(a.body_radius, maxf(dist, 0.1))
		if ang <= half + slack:
			out.append(a)
	return out

## Actors within a rectangle extending `length` along `dir` with total `width`.
static func actors_in_line(world: World3D, origin: Vector3, dir: Vector3, length: float, width: float, layer_mask: int) -> Array:
	var d := Vector3(dir.x, 0, dir.z).normalized()
	var mid := origin + d * length * 0.5
	var out := []
	for a in actors_in_radius(world, mid, length * 0.5 + width, layer_mask):
		var to := a.global_position - origin
		to.y = 0.0
		var along := to.dot(d)
		var side := absf(to.dot(d.cross(Vector3.UP)))
		if along >= -a.body_radius and along <= length + a.body_radius and side <= width * 0.5 + a.body_radius:
			out.append(a)
	return out

static func nearest(actors: Array, pos: Vector3) -> Actor:
	var best: Actor = null
	var bd := INF
	for a in actors:
		var d: float = a.global_position.distance_squared_to(pos)
		if d < bd:
			bd = d
			best = a
	return best

## Ground point below/at a position (for AoE placement), or the position itself if nothing is hit.
static func ground_at(world: World3D, pos: Vector3) -> Vector3:
	var q := PhysicsRayQueryParameters3D.create(pos + Vector3.UP * 6.0, pos + Vector3.DOWN * 12.0, BH.LAYER_WORLD | BH.LAYER_GROUND)
	var r := world.direct_space_state.intersect_ray(q)
	return r.position if r else pos

## True if the straight segment is blocked by world geometry.
static func blocked(world: World3D, from: Vector3, to: Vector3) -> bool:
	var q := PhysicsRayQueryParameters3D.create(from, to, BH.LAYER_WORLD)
	return not world.direct_space_state.intersect_ray(q).is_empty()

## Furthest reachable point along a path (for blink/dash/leap): stops before walls.
static func reachable_point(world: World3D, from: Vector3, to: Vector3, radius := 0.45) -> Vector3:
	var a := from + Vector3.UP * 0.9
	var b := to + Vector3.UP * 0.9
	var q := PhysicsRayQueryParameters3D.create(a, b, BH.LAYER_WORLD)
	var r := world.direct_space_state.intersect_ray(q)
	if r.is_empty():
		return to
	var hit: Vector3 = r.position
	var back := (a - b).normalized() * (radius + 0.15)
	return Vector3(hit.x + back.x, from.y, hit.z + back.z)
