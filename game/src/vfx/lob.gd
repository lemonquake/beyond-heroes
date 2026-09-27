class_name Lob
extends Node3D
## A thrown missile that arcs from a hand to the centre of an enemy's ground telegraph and lands exactly when the
## circle fills. Purely visual: the damage is the telegraphed AoE (AreaEffects.delayed), so timing stays fair.
## Kinds: "firepot" (goblin clay jar trailing fire), "boulder" (ogre rock trailing dust).

var from := Vector3.ZERO
var to := Vector3.ZERO
var flight := 0.8
var height := 3.0
var t := 0.0
var spin := Vector3.ZERO
var body: Node3D

static func throw(world: Node, kind: String, p_from: Vector3, p_to: Vector3, p_flight: float) -> Lob:
	if world == null or not is_instance_valid(world):
		return null
	var l := Lob.new()
	l.from = p_from
	l.to = p_to
	l.flight = maxf(p_flight, 0.2)
	l.height = clampf(p_from.distance_to(p_to) * 0.35, 1.5, 5.0)
	l.body = _firepot() if kind == "firepot" else _boulder()
	l.add_child(l.body)
	l.spin = Vector3(randf_range(-8, 8), randf_range(-6, 6), randf_range(-8, 8)) * (1.0 if kind == "firepot" else 0.4)
	var trail := VFXLib.particles(Color(1.0, 0.5, 0.15, 0.9), 24, 0.45, false, 0.28, 0.4, 30.0, Vector3(0, 1.0, 0), 0.05) if kind == "firepot" \
		else VFXLib.particles(Color(0.5, 0.46, 0.4, 0.5), 16, 0.6, false, 0.7, 0.4, 60.0, Vector3.ZERO, 0.2, false)
	l.add_child(trail)
	world.add_child(l)
	l.global_position = p_from
	return l

## Throw any node (a consumable's own model: Firebomb, Frost Flask) along the same arc, trailing `trail` coloured motes.
static func throw_node(world: Node, p_body: Node3D, p_from: Vector3, p_to: Vector3, p_flight: float, trail := Color(1, 1, 1, 0.8)) -> Lob:
	if world == null or not is_instance_valid(world):
		return null
	var l := Lob.new()
	l.from = p_from
	l.to = p_to
	l.flight = maxf(p_flight, 0.2)
	l.height = clampf(p_from.distance_to(p_to) * 0.35, 1.2, 4.0)
	l.body = p_body if p_body else Node3D.new()
	l.add_child(l.body)
	l.spin = Vector3(randf_range(-9, 9), randf_range(-5, 5), randf_range(-9, 9))
	l.add_child(VFXLib.particles(Color(trail.r, trail.g, trail.b, 0.85), 20, 0.4, false, 0.22, 0.3, 30.0, Vector3(0, 0.6, 0), 0.05))
	world.add_child(l)
	l.global_position = p_from
	return l

func _process(delta: float) -> void:
	t += delta
	var u := clampf(t / flight, 0.0, 1.0)
	var p := from.lerp(to, u)
	p.y += height * 4.0 * u * (1.0 - u)
	global_position = p
	if body:
		body.rotation += spin * delta
	if u >= 1.0:
		queue_free()

static func _firepot() -> Node3D:
	var root := Node3D.new()
	var jar := MeshInstance3D.new()
	var m := SphereMesh.new()
	m.radius = 0.16
	m.height = 0.3
	jar.mesh = m
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.55, 0.32, 0.18)
	mat.roughness = 0.9
	jar.material_override = mat
	root.add_child(jar)
	var rag := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = 0.05
	c.bottom_radius = 0.07
	c.height = 0.12
	rag.mesh = c
	rag.position.y = 0.17
	rag.material_override = VFXLib.glow_material(Color(1.0, 0.55, 0.15), 3.0)
	root.add_child(rag)
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.55, 0.2)
	light.light_energy = 1.5
	light.omni_range = 4.0
	root.add_child(light)
	return root

static func _boulder() -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var mesh := MapBuilder.library_mesh("rock_medium")
	if mesh:
		mi.mesh = mesh
		mi.scale = Vector3.ONE * 0.45
	else:
		var sm := SphereMesh.new()
		sm.radius = 0.5
		sm.height = 0.9
		mi.mesh = sm
	var mat := MaterialLibrary.env("BH_Stone")
	if mat:
		mi.material_override = mat
	root.add_child(mi)
	return root
