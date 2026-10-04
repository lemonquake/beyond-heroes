class_name Breakable
extends StaticBody3D
## Destructible prop (crate, barrel, urn, small statue). Intact it is a static obstacle; when its HP is spent it
## swaps to the pre-fractured `<name>_fragments.glb` pieces as short-lived rigid bodies thrown away from the hit.
## Debris lives on the debris layer (collides with world only), is capped in speed and despawns, so a chain of
## breaking props cannot feed back into itself.

signal broken(breakable: Breakable)

const SOUNDS := {"crate": &"break_wood", "barrel": &"break_wood", "urn": &"break_pottery", "statue_small": &"break_stone"}
const MASS := {"crate": 6.0, "barrel": 9.0, "urn": 3.0, "statue_small": 25.0}
const DEBRIS_LIFETIME := 5.0
const MAX_DEBRIS_SPEED := 9.0

@export var kind := "crate"
@export var max_hp := 20.0

var hp := 20.0
var _visual: Node3D
var _broken := false

func setup(p_kind: String, p_hp := 20.0) -> Breakable:
	kind = p_kind
	max_hp = p_hp
	return self

func _ready() -> void:
	hp = max_hp
	add_to_group(&"breakable")
	_fragments(kind)            # bh-037: built here, while the map loads, not on the blow that breaks the prop
	# props layer: blocks bodies but is not baked into the navmesh (breakables are dynamic obstacles)
	collision_layer = BH.LAYER_PROPS
	collision_mask = 0
	var scene: PackedScene = load("res://assets/environment/%s.glb" % kind)
	_visual = scene.instantiate()
	add_child(_visual)
	MaterialLibrary.apply_environment(_visual)
	# The kit's -colonly helper became a StaticBody3D child; this node is the body, so reuse its shapes.
	for sb in _visual.find_children("*", "StaticBody3D", true, false):
		for cs in sb.get_children():
			if cs is CollisionShape3D:
				var c2 := CollisionShape3D.new()
				c2.shape = cs.shape
				c2.transform = sb.transform * cs.transform
				add_child(c2)
		# free now, not deferred: a lingering world-layer body would be baked into the navmesh as a wall
		sb.get_parent().remove_child(sb)
		sb.free()

## The pre-fractured pieces of `kind`: [{mesh, xf, center, shape}], built once per kind and shared by every prop of it.
## bh-037: each break used to load the fragments and compute a *simplified* convex hull per piece on the spot: a barrel
## froze the game 186 ms, a crate 221, a small statue 428 and an urn 585 ms. Plain hulls (6-15 ms per kind, once) are
## just as good for debris that lives five seconds.
static var _frag_cache := {}

static func _fragments(k: String) -> Array:
	if _frag_cache.has(k):
		return _frag_cache[k]
	var out: Array = []
	var frag_path := "res://assets/environment/%s_fragments.glb" % k
	if ResourceLoader.exists(frag_path):
		var fr: Node3D = (load(frag_path) as PackedScene).instantiate()
		for p in fr.find_children("frag_*", "MeshInstance3D", true, false):
			var mi: MeshInstance3D = p
			out.append({"mesh": mi.mesh, "xf": mi.transform, "center": mi.get_aabb().get_center(),
				"shape": mi.mesh.create_convex_shape(true, false)})
		fr.free()
	_frag_cache[k] = out
	return out

## Apply damage from a hit. `impulse` is the horizontal push direction * strength (m/s scale).
func take_hit(amount: float, impulse := Vector3.ZERO) -> void:
	if _broken:
		return
	hp -= amount
	if hp <= 0.0:
		shatter(impulse)

func shatter(impulse := Vector3.ZERO) -> void:
	if _broken:
		return
	_broken = true
	var parent := get_parent()
	var pieces := _fragments(kind)
	var total_mass: float = MASS.get(kind, 6.0)
	for pc: Dictionary in pieces:
		var body := RigidBody3D.new()
		body.collision_layer = BH.LAYER_DEBRIS
		body.collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND
		body.mass = maxf(total_mass / pieces.size(), 0.2)
		var cs := CollisionShape3D.new()
		cs.shape = pc.shape
		var center: Vector3 = pc.center
		var m2 := MeshInstance3D.new()
		m2.mesh = pc.mesh
		m2.position = -center
		cs.position = -center
		body.add_child(m2)
		body.add_child(cs)
		parent.add_child(body)
		body.global_transform = global_transform * (pc.xf as Transform3D) * Transform3D(Basis.IDENTITY, center)
		MaterialLibrary.apply_environment(m2)
		var out := (body.global_position - global_position)
		out.y = 0.0
		var v := out.normalized() * 2.0 + Vector3.UP * 2.5 + impulse
		body.linear_velocity = v.limit_length(MAX_DEBRIS_SPEED)
		body.angular_velocity = Vector3(randf_range(-6, 6), randf_range(-6, 6), randf_range(-6, 6))
		var tw := body.create_tween()
		tw.tween_interval(DEBRIS_LIFETIME)
		tw.tween_property(m2, "scale", Vector3.ONE * 0.01, 0.6)
		tw.tween_callback(body.queue_free)
	var snd: StringName = SOUNDS.get(kind, &"break_wood")
	Audio.play_at(snd, global_position)
	Events.impact.emit(global_position + Vector3.UP * 0.4, 0.5, &"wood" if kind in ["crate", "barrel"] else &"stone")
	broken.emit(self)
	queue_free()
