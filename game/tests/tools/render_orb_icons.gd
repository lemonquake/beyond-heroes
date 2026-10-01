extends Node3D
## bh-028: renders the celestial orb icons (assets/ui/icons/crystals/<family>_<grade>.png, 256 px) without Blender.
##   xvfb-run -a godot --rendering-driver opengl3 --path game --resolution 256x256 res://tests/tools/render_orb_icons.tscn
## Each grade has its own cut, as the other crystals do: Fragment a rough chipped stone, Shard a long hexagonal
## crystal, Crystalline an octagonal step-cut gem, Orbital a brilliant sphere inside two gold rings. Writes the raw
## renders to work/lemondev/bh-028/scratch/; tools/ui_art/bh028_orb_icons.py adds the backdrop and glow.

const FAMILIES := [&"sora", &"luna", &"sol", &"airah"]
const SIZE := 256

var _vp: SubViewport
var _pivot: Node3D
var _ring := Color(0.95, 0.75, 0.38)

func _ready() -> void:
	_vp = SubViewport.new()
	_vp.size = Vector2i(SIZE, SIZE)
	_vp.transparent_bg = true
	_vp.msaa_3d = Viewport.MSAA_8X
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.55, 0.62)
	env.ambient_light_energy = 0.9
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 0.15, 3.2)
	cam.fov = 34.0
	_vp.add_child(cam)
	cam.look_at(Vector3.ZERO)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-40, -35, 0)
	key.light_energy = 1.6
	_vp.add_child(key)
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-10, 150, 0)
	rim.light_energy = 1.1
	_vp.add_child(rim)
	var out_dir := ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-028/scratch/orb_raw")
	DirAccess.make_dir_recursive_absolute(out_dir)
	for f in FAMILIES:
		var col: Color = DataCrystals.FAMILIES[f].color
		for g in 4:
			if _pivot:
				_pivot.free()
			_pivot = Node3D.new()
			_vp.add_child(_pivot)
			_ring = RING[f]
			_build(g, col, hash(String(f)) % 1000)
			for i in 4:
				await RenderingServer.frame_post_draw
			_vp.get_texture().get_image().save_png(out_dir.path_join("%s_%d.png" % [f, g]))
	get_tree().quit()

func _gem_mat(col: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	var deep := Color.from_hsv(col.h, minf(1.0, col.s * 1.6 + 0.15), col.v * 0.62)
	m.albedo_color = deep
	m.metallic = 0.35
	m.roughness = 0.08
	m.emission_enabled = true
	m.emission = Color.from_hsv(col.h, minf(1.0, col.s * 1.3 + 0.1), col.v)
	m.emission_energy_multiplier = 0.32
	m.rim_enabled = true
	m.rim = 0.6
	m.rim_tint = 0.3
	m.clearcoat_enabled = true
	m.clearcoat = 1.0
	m.specular = 0.9
	return m

const RING := {&"sora": Color(0.78, 0.86, 0.95), &"luna": Color(0.85, 0.86, 0.92), &"sol": Color(0.95, 0.75, 0.38), &"airah": Color(0.62, 0.9, 0.75)}

func _gold(col := Color(0.95, 0.75, 0.38)) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.metallic = 1.0
	m.roughness = 0.25
	m.emission_enabled = true
	m.emission = Color(0.5, 0.35, 0.1)
	m.emission_energy_multiplier = 0.3
	return m

## A mesh with flat-shaded facets (every triangle its own normal).
func _faceted(mesh: Mesh) -> ArrayMesh:
	var arrays := mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var pv := PackedVector3Array()
	var pn := PackedVector3Array()
	for i in range(0, idx.size(), 3):
		var a := verts[idx[i]]
		var b := verts[idx[i + 1]]
		var c := verts[idx[i + 2]]
		var n := (c - a).cross(b - a)
		if n.length_squared() < 1e-12:
			continue
		n = n.normalized()
		for v in [a, b, c]:
			pv.append(v)
			pn.append(n)
	var out := []
	out.resize(Mesh.ARRAY_MAX)
	out[Mesh.ARRAY_VERTEX] = pv
	out[Mesh.ARRAY_NORMAL] = pn
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, out)
	return am

func _add(mesh: Mesh, mat: Material, pos := Vector3.ZERO, rot := Vector3.ZERO, scl := Vector3.ONE, flat := true) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = _faceted(mesh) if flat else mesh
	mi.material_override = mat
	mi.position = pos
	mi.rotation_degrees = rot
	mi.scale = scl
	_pivot.add_child(mi)
	return mi

func _cone(r: float, h: float, segs: int, tip_up := true) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = 0.0 if tip_up else r
	c.bottom_radius = r if tip_up else 0.0
	c.height = h
	c.radial_segments = segs
	c.rings = 1
	return c

func _build(g: int, col: Color, seed_value: int) -> void:
	var gem := _gem_mat(col)
	var core := StandardMaterial3D.new()
	core.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	core.albedo_color = col.lightened(0.55)
	core.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	core.albedo_color.a = 0.55
	match g:
		0:
			# Fragment: a rough, chipped lump
			var s := SphereMesh.new()
			s.radial_segments = 6
			s.rings = 3
			s.radius = 0.6
			s.height = 1.2
			_add(s, gem, Vector3.ZERO, Vector3(20, 35 + seed_value % 40, 15), Vector3(1.0, 0.72, 0.62))
			_add(_cone(0.32, 0.55, 4), gem, Vector3(0.35, 0.25, 0.05), Vector3(0, 10, -40), Vector3.ONE)
		1:
			# Shard: a long hexagonal crystal with a pointed tip, leaning
			var body := CylinderMesh.new()
			body.top_radius = 0.3
			body.bottom_radius = 0.34
			body.height = 1.1
			body.radial_segments = 6
			body.rings = 1
			var lean := Vector3(0, 30, -24)
			_add(body, gem, Vector3.ZERO, lean)
			var t := Transform3D(Basis.from_euler(lean * PI / 180.0), Vector3.ZERO)
			_add(_cone(0.3, 0.45, 6), gem, t * Vector3(0, 0.77, 0), lean)
			_add(_cone(0.34, 0.25, 6, false), gem, t * Vector3(0, -0.67, 0), lean)
			_add(_cone(0.14, 0.4, 6), gem, Vector3(-0.42, -0.35, 0.1), Vector3(0, 0, 30))
		2:
			# Crystalline: an octagonal step-cut stone, table up and toward the viewer
			var girdle := CylinderMesh.new()
			girdle.top_radius = 0.62
			girdle.bottom_radius = 0.62
			girdle.height = 0.14
			girdle.radial_segments = 8
			girdle.rings = 1
			var crown := CylinderMesh.new()
			crown.top_radius = 0.38
			crown.bottom_radius = 0.62
			crown.height = 0.24
			crown.radial_segments = 8
			crown.rings = 1
			var rot := Vector3(48, 22.5, 0)
			var t := Transform3D(Basis.from_euler(rot * PI / 180.0), Vector3.ZERO)
			_add(girdle, gem, Vector3.ZERO, rot)
			_add(crown, gem, t * Vector3(0, 0.19, 0), rot)
			_add(_cone(0.62, 0.62, 8, false), gem, t * Vector3(0, -0.38, 0), rot)
		3:
			# Orbital: a brilliant sphere inside two crossed gold rings
			var s := SphereMesh.new()
			s.radial_segments = 14
			s.rings = 7
			s.radius = 0.5
			s.height = 1.0
			_add(s, gem, Vector3.ZERO, Vector3(10, 20, 0))
			var c := SphereMesh.new()
			c.radius = 0.3
			c.height = 0.6
			_add(c, core, Vector3.ZERO, Vector3.ZERO, Vector3.ONE, false)
			for r in [Vector3(70, 0, 20), Vector3(70, 0, -35)]:
				var tor := TorusMesh.new()
				tor.inner_radius = 0.76
				tor.outer_radius = 0.82
				tor.rings = 48
				tor.ring_segments = 8
				_add(tor, _gold(_ring), Vector3.ZERO, r, Vector3.ONE, false)
