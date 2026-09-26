class_name MapBuilder
extends RefCounted
## Base class for handcrafted map scripts (src/world/maps/<id>.gd). A map script overrides `compose()` and uses
## the helpers below to place the Blender kit, lay rooms on the 4 m wall grid, sculpt terrain, add water, fog,
## light, spawn points, teleporters and gameplay markers. Everything is deterministic (RNG seeded by map id), so a
## map rebuilds identically every time it is loaded and tests can make exact assertions about it.
##
## Conventions: metres, Y up, the isometric camera looks from +Z (south) toward -Z, so kit "fronts" (doors,
## sconces, facades) face +Z. Interiors use full-height walls on the north/east/west sides and low cutaway walls on
## the south side so rooms stay readable from above.

const ENV_DIR := "res://assets/environment/%s.glb"
const WALL := 4.0

static var _scenes := {}
static var _lib_meshes := {}

var root: MapRoot
var def: MapDef
var rng := RandomNumberGenerator.new()
var nav: NavigationRegion3D          # colliding geometry lives under here so the navmesh bake sees it
var geo: Node3D                      # architecture / terrain
var props: Node3D                    # colliding props
var deco: Node3D                     # non-colliding decoration
var lights: Node3D
var markers: Node3D
var height_fn: Callable              # (x, z) -> ground height, set by terrain()
var _batches := {}                   # asset name -> {transforms: Array[Transform3D], shadows: bool}
var _light_count := 0
var _shadow_lights := 0

# ------------------------------------------------------------------------------------------------------------
# lifecycle

func build(p_def: MapDef) -> MapRoot:
	def = p_def
	rng.seed = hash(String(def.id))
	root = MapRoot.new()
	root.name = "Map_%s" % def.id
	root.def = def
	nav = NavigationRegion3D.new()
	nav.name = "Navigation"
	root.add_child(nav)
	root.nav_region = nav
	geo = _group(nav, "Geometry")
	props = _group(nav, "Props")
	deco = _group(root, "Decoration")
	lights = _group(root, "Lights")
	markers = _group(root, "Markers")
	var nm := NavigationMesh.new()
	nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	nm.geometry_collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND
	nm.geometry_source_geometry_mode = NavigationMesh.SOURCE_GEOMETRY_ROOT_NODE_CHILDREN
	nm.cell_size = 0.25
	nm.cell_height = 0.25
	nm.agent_radius = 0.5
	nm.agent_height = 2.0
	nm.agent_max_climb = 0.5
	nm.agent_max_slope = 40.0
	nm.region_min_size = 4.0
	nav.navigation_mesh = nm
	compose()
	_flush_batches()
	return root

## Override in map scripts.
func compose() -> void:
	pass

## Bake the navigation mesh. Call once the map is inside the scene tree (global transforms must be valid).
static func bake_navigation(map: MapRoot) -> void:
	if map.nav_region and map.nav_region.navigation_mesh:
		map.nav_region.bake_navigation_mesh(false)
		# push the result to the server now (the region otherwise picks it up a frame later)
		NavigationServer3D.region_set_navigation_mesh(map.nav_region.get_rid(), map.nav_region.navigation_mesh)
		var nav_map := map.nav_region.get_navigation_map()
		# Godot 4.5+ rebuilds maps asynchronously by default; a freshly loaded map must be queryable at once
		# (spawners and AI path on the first frame), so this map syncs on the main thread.
		if NavigationServer3D.has_method(&"map_set_use_async_iterations"):
			NavigationServer3D.call(&"map_set_use_async_iterations", nav_map, false)
		NavigationServer3D.map_force_update(nav_map)

## Give the map its own navigation map (tests build several maps side by side; each must path in isolation).
static func isolate_navigation(map: MapRoot) -> RID:
	var rid := NavigationServer3D.map_create()
	NavigationServer3D.map_set_cell_size(rid, 0.25)
	NavigationServer3D.map_set_cell_height(rid, 0.25)
	NavigationServer3D.map_set_active(rid, true)
	map.nav_region.set_navigation_map(rid)
	return rid

func _group(parent: Node, n: String) -> Node3D:
	var g := Node3D.new()
	g.name = n
	parent.add_child(g)
	return g

# ------------------------------------------------------------------------------------------------------------
# kit placement

static func scene(name: String) -> PackedScene:
	if not _scenes.has(name):
		var p := ENV_DIR % name
		assert(ResourceLoader.exists(p), "missing environment asset %s" % p)
		_scenes[name] = load(p)
	return _scenes[name]

func ground(x: float, z: float) -> float:
	return height_fn.call(x, z) if height_fn.is_valid() else 0.0

## Place a kit piece. `pos.y` is used as-is unless `on_ground` is set, in which case the terrain height is added.
func kit(name: String, pos: Vector3, yaw_deg := 0.0, scale := 1.0, parent: Node3D = null, on_ground := false) -> Node3D:
	var n: Node3D = scene(name).instantiate()
	n.name = "%s_%d" % [name, (parent if parent else props).get_child_count()]
	var p := pos
	if on_ground:
		p.y += ground(pos.x, pos.z)
	n.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)).scaled(Vector3.ONE * scale), p)
	(parent if parent else props).add_child(n)
	MaterialLibrary.apply_environment(n)
	return n

## Architecture piece (goes under Geometry).
func arch(name: String, pos: Vector3, yaw_deg := 0.0, scale := 1.0) -> Node3D:
	return kit(name, pos, yaw_deg, scale, geo)

## Non-colliding decoration, batched into one MultiMesh per asset (grass, ferns, bones, cobwebs, small rocks).
func decor(name: String, pos: Vector3, yaw_deg := 0.0, scale := 1.0, on_ground := true, shadows := false, tilt := 0.0) -> void:
	var p := pos
	if on_ground:
		p.y += ground(pos.x, pos.z)
	var b := Basis(Vector3.UP, deg_to_rad(yaw_deg))
	if tilt != 0.0:
		b = Basis(Vector3(1, 0, 0).rotated(Vector3.UP, rng.randf() * TAU), deg_to_rad(tilt)) * b
	if not _batches.has(name):
		_batches[name] = {"transforms": [], "shadows": shadows}
	_batches[name].transforms.append(Transform3D(b.scaled(Vector3.ONE * scale), p))

static func library_mesh(name: String) -> Mesh:
	if _lib_meshes.has(name):
		return _lib_meshes[name]
	var inst := scene(name).instantiate()
	var found: MeshInstance3D = null
	for c in inst.find_children("*", "MeshInstance3D", true, false):
		found = c
		break
	var mesh: Mesh = found.mesh.duplicate() if found else null
	if mesh:
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i)
			var rep := MaterialLibrary.env(mat.resource_name if mat else "")
			if rep:
				mesh.surface_set_material(i, rep)
	inst.free()
	_lib_meshes[name] = mesh
	return mesh

func _flush_batches() -> void:
	for name in _batches:
		var mesh := library_mesh(name)
		if mesh == null:
			continue
		var tr: Array = _batches[name].transforms
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = tr.size()
		for i in tr.size():
			mm.set_instance_transform(i, tr[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "Batch_%s" % name
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if _batches[name].shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		deco.add_child(mmi)
	_batches.clear()

func breakable(kind: String, pos: Vector3, yaw_deg := 0.0, hp := 20.0, on_ground := false) -> Breakable:
	var b := Breakable.new().setup(kind, hp)
	var p := pos
	if on_ground:
		p.y += ground(pos.x, pos.z)
	b.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)), p)
	props.add_child(b)
	return b

## Scatter kit/decor pieces inside a rect (x, z, w, d) with minimum spacing and an optional reject predicate
## `avoid(x, z) -> bool`. Returns the placed positions.
func scatter(names: Array, rect: Rect2, count: int, spacing := 1.0, scale_rng := Vector2(0.8, 1.2), avoid := Callable(),
		as_decor := true, shadows := false, tilt := 0.0) -> Array[Vector3]:
	var placed: Array[Vector3] = []
	var tries := count * 12
	while placed.size() < count and tries > 0:
		tries -= 1
		var x := rect.position.x + rng.randf() * rect.size.x
		var z := rect.position.y + rng.randf() * rect.size.y
		if avoid.is_valid() and avoid.call(x, z):
			continue
		var ok := true
		for q in placed:
			if Vector2(q.x - x, q.z - z).length() < spacing:
				ok = false
				break
		if not ok:
			continue
		var p := Vector3(x, 0, z)
		var nm: String = names[rng.randi() % names.size()]
		var s := rng.randf_range(scale_rng.x, scale_rng.y)
		if as_decor:
			decor(nm, p, rng.randf() * 360.0, s, true, shadows, tilt)
		else:
			kit(nm, p, rng.randf() * 360.0, s, null, true)
		placed.append(p)
	return placed

# ------------------------------------------------------------------------------------------------------------
# architecture on the 4 m grid

## A straight wall run from a to b (axis aligned, length a multiple of 4 m) using `piece`. `skip` lists 0-based
## segment indices to leave open, `swap` maps segment index -> alternative piece (doorway, window, broken...).
func wall_run(a: Vector3, b: Vector3, piece := "wall_stone_capped", skip := [], swap := {}, flip := false) -> void:
	var d := b - a
	var len := d.length()
	var n := int(round(len / WALL))
	if n <= 0:
		return
	var dir := d / len
	var yaw := rad_to_deg(atan2(-dir.z, dir.x)) + (180.0 if flip else 0.0)
	for i in n:
		if i in skip:
			continue
		var c := a + dir * (WALL * 0.5 + WALL * i)
		arch(swap.get(i, piece), c, yaw)

## Floor tiles covering rect (x, z, w, d) with the walkable top at `y`.
func floor_tiles(rect: Rect2, y := 0.0, piece := "floor_tile_4m") -> void:
	var nx := int(round(rect.size.x / WALL))
	var nz := int(round(rect.size.y / WALL))
	for i in nx:
		for j in nz:
			arch(piece, Vector3(rect.position.x + WALL * (i + 0.5), y - 0.3, rect.position.y + WALL * (j + 0.5)), 90.0 * ((i * 7 + j * 3) % 4))

## A room on the grid: floor, full walls north/east/west, cutaway south wall, quoin pillars at the corners.
## Segment indices on every side count from its north (east/west sides) or west (north/south sides) end.
## opts: {y, floor(bool), north/east/west/south: piece or "" to omit, doors: {side: [segment indices]} for doorway
## pieces (north/east/west) or gaps (south), gaps: {side: [indices]} for open segments, swap: {side: {i: piece}},
## pillars(bool)}
func room(rect: Rect2, opts := {}) -> void:
	var y: float = opts.get("y", 0.0)
	if opts.get("floor", true):
		floor_tiles(rect, y, opts.get("floor_piece", "floor_tile_4m"))
	var x0 := rect.position.x
	var x1 := rect.position.x + rect.size.x
	var z0 := rect.position.y
	var z1 := rect.position.y + rect.size.y
	var doors: Dictionary = opts.get("doors", {})
	var gaps: Dictionary = opts.get("gaps", {})
	var swaps: Dictionary = opts.get("swap", {})
	var sides := {
		"north": [Vector3(x0, y, z0), Vector3(x1, y, z0), opts.get("north", "wall_stone_capped")],
		"south": [Vector3(x0, y, z1), Vector3(x1, y, z1), opts.get("south", "wall_low")],
		"west": [Vector3(x0, y, z0), Vector3(x0, y, z1), opts.get("west", "wall_stone_capped")],
		"east": [Vector3(x1, y, z0), Vector3(x1, y, z1), opts.get("east", "wall_stone_capped")],
	}
	for s in sides:
		var piece: String = sides[s][2]
		if piece == "":
			continue
		var sw: Dictionary = (swaps.get(s, {}) as Dictionary).duplicate()
		var sk: Array = (gaps.get(s, []) as Array).duplicate()
		for i in doors.get(s, []):
			if s == "south":
				sk.append(i)
			else:
				sw[i] = "wall_doorway"
		# north/west/east pieces face inward (+Z for north, etc.) so torches and doorways read from inside
		wall_run(sides[s][0], sides[s][1], piece, sk, sw, s == "south" or s == "east")
	if opts.get("pillars", true):
		for c: Vector3 in [Vector3(x0, y, z0), Vector3(x1, y, z0), Vector3(x0, y, z1), Vector3(x1, y, z1)]:
			var tall := is_equal_approx(c.z, z0)
			arch("pillar_quoin" if tall else "pillar", c).scale = Vector3(1, 1.02 if tall else 0.36, 1)

## Corridor strip on the grid. axis "z" runs north-south with full walls west/east; axis "x" runs east-west with a
## full north wall and a cutaway south wall. `gaps` = {"west"/"east"/"north"/"south": [segment indices]} opens side
## junctions (segments counted from the corridor's north / west end).
func corridor(rect: Rect2, axis := "z", opts := {}) -> void:
	var y: float = opts.get("y", 0.0)
	floor_tiles(rect, y)
	var x0 := rect.position.x
	var x1 := rect.position.x + rect.size.x
	var z0 := rect.position.y
	var z1 := rect.position.y + rect.size.y
	var gaps: Dictionary = opts.get("gaps", {})
	var piece: String = opts.get("piece", "wall_stone_capped")
	if axis == "z":
		wall_run(Vector3(x0, y, z0), Vector3(x0, y, z1), piece, gaps.get("west", []))
		wall_run(Vector3(x1, y, z0), Vector3(x1, y, z1), piece, gaps.get("east", []), {}, true)
	else:
		wall_run(Vector3(x0, y, z0), Vector3(x1, y, z0), piece, gaps.get("north", []))
		wall_run(Vector3(x0, y, z1), Vector3(x1, y, z1), opts.get("south_piece", "wall_low"), gaps.get("south", []), {}, true)

## Ring of cliff faces around `center` whose tops sit at `top_y` (so they frame the playable area from below and
## never rise over it). Faces point outward.
const CLIFF_H := {"cliff_a": 6.19, "cliff_b": 9.0}

func cliff_ring(center: Vector3, radius: float, top_y: float, n := 16, scale_rng := Vector2(1.6, 2.2), radius_z := -1.0,
		jitter := 3.0) -> void:
	for i in n:
		var a := TAU * (i + rng.randf() * 0.3) / n
		var nm := "cliff_b" if i % 2 else "cliff_a"
		var s := rng.randf_range(scale_rng.x, scale_rng.y)
		var rz := radius_z if radius_z > 0.0 else radius
		var p := center + Vector3(cos(a) * (radius + rng.randf() * jitter), 0, sin(a) * (rz + rng.randf() * jitter))
		p.y = top_y - CLIFF_H[nm] * s
		decor(nm, p, rad_to_deg(-a) - 90.0, s, false, true)

## Round stone floor (visual disc + cylinder collision) with its top at `y`.
func floor_disc(center: Vector3, radius: float, y := 0.0, texture_set := "stone_floor") -> void:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = radius
	cm.bottom_radius = radius
	cm.height = 0.4
	cm.radial_segments = 48
	mi.mesh = cm
	var m := StandardMaterial3D.new()
	m.albedo_texture = load("res://assets/textures/%s_albedo.png" % texture_set)
	m.normal_enabled = true
	m.normal_texture = load("res://assets/textures/%s_normal.png" % texture_set)
	m.roughness_texture = load("res://assets/textures/%s_rough.png" % texture_set)
	m.albedo_color = Color(0.62, 0.6, 0.6)
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE * 0.4
	mi.material_override = m
	mi.position = center + Vector3(0, y - 0.2, 0)
	geo.add_child(mi)
	var sb := StaticBody3D.new()
	sb.collision_layer = BH.LAYER_WORLD | BH.LAYER_GROUND
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = radius
	shape.height = 0.4
	cs.shape = shape
	sb.add_child(cs)
	sb.position = mi.position
	geo.add_child(sb)

## Invisible boundary (collision only) from a to b, `h` tall — used sparingly where cliffs/trees already read as
## the edge, to guarantee the player can never leave the handcrafted area.
func boundary(a: Vector3, b: Vector3, h := 6.0, thick := 1.0) -> void:
	var sb := StaticBody3D.new()
	sb.name = "Boundary_%d" % geo.get_child_count()
	sb.collision_layer = BH.LAYER_WORLD
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	var d := b - a
	bs.size = Vector3(d.length() + thick, h, thick)
	cs.shape = bs
	sb.add_child(cs)
	sb.transform = Transform3D(Basis(Vector3.UP, atan2(-d.z, d.x)), (a + b) * 0.5 + Vector3.UP * h * 0.5)
	sb.set_meta(&"boundary", true)
	geo.add_child(sb)

## Solid invisible block (for water pits etc.).
func blocker(center: Vector3, size: Vector3) -> void:
	var sb := StaticBody3D.new()
	sb.collision_layer = BH.LAYER_WORLD
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	sb.add_child(cs)
	sb.position = center
	geo.add_child(sb)

## Flat walkable slab (box collider + no visual) used under visual floors that are not kit tiles.
func walk_slab(center: Vector3, size: Vector3) -> void:
	blocker(center - Vector3(0, size.y * 0.5, 0), size)

# ------------------------------------------------------------------------------------------------------------
# terrain, water, atmosphere

## Heightfield terrain centred at `center` covering `size` metres at 1 m resolution. `hfn(x, z)` gives the
## height in world space, `splat(x, z)` gives vertex colour weights (R dirt/path, G forest floor, B cobble).
func terrain(size: Vector2i, center: Vector3, hfn: Callable, splat: Callable, textures := {}, tint := Color.WHITE) -> MeshInstance3D:
	height_fn = hfn
	var w := size.x + 1
	var d := size.y + 1
	var x0 := center.x - size.x * 0.5
	var z0 := center.z - size.y * 0.5
	var heights := PackedFloat32Array()
	heights.resize(w * d)
	for j in d:
		for i in w:
			heights[j * w + i] = hfn.call(x0 + i, z0 + j)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in d:
		for i in w:
			var x := x0 + i
			var z := z0 + j
			st.set_color(splat.call(x, z))
			st.set_uv(Vector2(x, z) * 0.25)
			st.add_vertex(Vector3(x, heights[j * w + i], z))
	for j in d - 1:
		for i in w - 1:
			var a := j * w + i
			st.add_index(a)
			st.add_index(a + 1)
			st.add_index(a + w)
			st.add_index(a + 1)
			st.add_index(a + w + 1)
			st.add_index(a + w)
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.name = "Terrain"
	mi.mesh = st.commit()
	mi.material_override = MaterialLibrary.terrain_material(textures.get("grass", "grass"), textures.get("dirt", "dirt"),
		textures.get("moss", "forest_floor"), textures.get("path", "cobblestone"), textures.get("rock", "rock_cliff"), tint)
	geo.add_child(mi)
	var sb := StaticBody3D.new()
	sb.name = "TerrainBody"
	sb.collision_layer = BH.LAYER_GROUND | BH.LAYER_WORLD
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var hs := HeightMapShape3D.new()
	hs.map_width = w
	hs.map_depth = d
	hs.map_data = heights
	cs.shape = hs
	sb.add_child(cs)
	sb.position = Vector3(x0 + size.x * 0.5, 0, z0 + size.y * 0.5)
	geo.add_child(sb)
	return mi

func water(rect: Rect2, y: float, shallow := Color(0.12, 0.62, 0.62), deep := Color(0.02, 0.12, 0.16), glow := 0.9, depth_fade := 2.5, foam := 0.3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = "Water_%d" % deco.get_child_count()
	var pm := PlaneMesh.new()
	pm.size = rect.size
	pm.subdivide_width = int(rect.size.x / 4)
	pm.subdivide_depth = int(rect.size.y / 4)
	mi.mesh = pm
	mi.material_override = WorldShaders.water_material(shallow, deep, glow, depth_fade)
	mi.material_override.set_shader_parameter("foam", foam)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = Vector3(rect.position.x + rect.size.x * 0.5, y, rect.position.y + rect.size.y * 0.5)
	mi.add_to_group(&"water")
	deco.add_child(mi)
	return mi

func mist(rect: Rect2, y: float, c := Color(0.55, 0.65, 0.75), density := 0.35) -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = rect.size
	mi.mesh = pm
	mi.material_override = WorldShaders.mist_material(c, density)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = Vector3(rect.position.x + rect.size.x * 0.5, y, rect.position.y + rect.size.y * 0.5)
	deco.add_child(mi)

## Light shaft from `top` pointing down along `dir`.
func shaft(top: Vector3, dir: Vector3, length: float, radius: float, c := Color(0.55, 0.7, 1.0), intensity := 0.35) -> void:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = radius * 0.7
	cm.bottom_radius = radius
	cm.height = length
	cm.cap_top = false
	cm.cap_bottom = false
	cm.radial_segments = 16
	mi.mesh = cm
	mi.material_override = WorldShaders.shaft_material(c, intensity)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var d := dir.normalized()
	var up := -d
	var basis := Basis.looking_at(Vector3.FORWARD if absf(up.dot(Vector3.FORWARD)) < 0.99 else Vector3.RIGHT, up)
	basis = Basis(basis.x, up, basis.x.cross(up)).orthonormalized()
	mi.transform = Transform3D(basis, top + d * length * 0.5)
	deco.add_child(mi)

## WorldEnvironment + key light from a preset dictionary.
func environment(p: Dictionary) -> void:
	var env := Environment.new()
	if p.get("sky", false):
		env.background_mode = Environment.BG_SKY
		env.sky = WorldShaders.night_sky(p.get("sky_top", Color(0.03, 0.05, 0.1)), p.get("sky_horizon", Color(0.16, 0.18, 0.26)))
	else:
		env.background_mode = Environment.BG_COLOR
		env.background_color = p.get("bg", Color(0.02, 0.02, 0.03))
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = p.get("ambient", Color(0.2, 0.22, 0.3))
	env.ambient_light_energy = p.get("ambient_energy", 0.5)
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = p.get("exposure", 1.0)
	env.tonemap_white = 6.0
	env.ssao_enabled = Settings.ssao
	env.ssao_radius = 1.4
	env.ssao_intensity = 2.2
	env.ssao_power = 1.6
	env.ssil_enabled = false
	env.glow_enabled = Settings.glow
	env.glow_intensity = p.get("glow", 0.7)
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 1.1
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.set_glow_level(0, 0.0)
	env.set_glow_level(2, 1.0)
	env.set_glow_level(3, 0.8)
	env.set_glow_level(5, 0.5)
	env.fog_enabled = Settings.fog
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = p.get("fog", Color(0.12, 0.14, 0.2))
	env.fog_light_energy = p.get("fog_energy", 1.0)
	env.fog_density = p.get("fog_density", 0.012)
	env.fog_sky_affect = 0.6
	env.fog_height = p.get("fog_height", 2.0)
	env.fog_height_density = p.get("fog_height_density", 0.08)
	env.adjustment_enabled = true
	env.adjustment_brightness = 1.0
	env.adjustment_contrast = p.get("contrast", 1.08)
	env.adjustment_saturation = p.get("saturation", 0.95)
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	we.environment = env
	root.add_child(we)
	root.environment = we
	var sun := DirectionalLight3D.new()
	sun.name = "KeyLight"
	sun.light_color = p.get("sun", Color(0.55, 0.62, 0.85))
	sun.light_energy = p.get("sun_energy", 0.6)
	sun.rotation_degrees = p.get("sun_rot", Vector3(-55, 35, 0))
	sun.shadow_enabled = Settings.shadows_quality > 0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 60.0
	sun.shadow_blur = 1.5
	sun.light_angular_distance = 1.0
	root.add_child(sun)
	root.sun = sun

# ------------------------------------------------------------------------------------------------------------
# lights and fire

func light(pos: Vector3, c: Color, energy := 1.5, range_m := 8.0, shadow := false, flicker := false) -> OmniLight3D:
	var l: OmniLight3D = FlickerLight.new() if flicker else OmniLight3D.new()
	if flicker:
		(l as FlickerLight).base_energy = energy
	l.light_color = c
	l.light_energy = energy
	l.omni_range = range_m
	l.omni_attenuation = 0.9
	l.shadow_enabled = shadow and Settings.shadows_quality > 1
	l.set_meta(&"wants_shadow", shadow)
	l.light_bake_mode = Light3D.BAKE_DISABLED
	l.position = pos
	lights.add_child(l)
	_light_count += 1
	if l.shadow_enabled:
		_shadow_lights += 1
	return l

const FIRE := Color(1.0, 0.62, 0.3)

func flame(pos: Vector3, s := 1.0) -> void:
	var p := VFXLib.particles(Color(1.0, 0.48, 0.12, 0.8), int(10 * s) + 4, 0.45, false, 0.3 * s, 0.9 * s, 14.0,
		Vector3(0, 1.4 * s, 0), 0.08 * s)
	p.position = pos
	p.visibility_aabb = AABB(Vector3(-1, -0.5, -1), Vector3(2, 3, 2))
	deco.add_child(p)
	var core := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.09 * s
	sm.height = 0.26 * s
	core.mesh = sm
	core.material_override = VFXLib.glow_material(Color(1.0, 0.6, 0.2), 3.5)
	core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	core.position = pos + Vector3(0, 0.05 * s, 0)
	deco.add_child(core)

## Local-space socket position without requiring the node to be in the tree.
func socket_pos(n: Node3D, sname: String) -> Vector3:
	var s := n.find_child(sname, true, false) as Node3D
	if s == null:
		return n.position + Vector3.UP
	var t := s.transform
	var p: Node = s.get_parent()
	while p and p != n:
		t = (p as Node3D).transform * t
		p = p.get_parent()
	return n.transform * t.origin

## Wall torch: `pos` is the point on the wall face at mounting height, `yaw` turns the torch to face away from
## the wall (0 = faces +Z).
func torch(pos: Vector3, yaw_deg := 0.0, energy := 3.0, shadow := false) -> void:
	var n := kit("torch_sconce", pos, yaw_deg, 1.0, deco)
	var f := socket_pos(n, "flame")
	flame(f, 0.8)
	var out := Vector3(0, 0, 0.35).rotated(Vector3.UP, deg_to_rad(yaw_deg))
	light(f + out + Vector3(0, 0.25, 0), FIRE, energy, 10.0, shadow, true)

func brazier(pos: Vector3, energy := 3.4, shadow := false, on_ground := false) -> void:
	var n := kit("brazier", pos, rng.randf() * 360.0, 1.0, props, on_ground)
	var f := socket_pos(n, "flame")
	flame(f, 1.4)
	light(f + Vector3(0, 0.4, 0), FIRE, energy, 12.0, shadow, true)

func campfire(pos: Vector3, energy := 5.0, on_ground := true) -> void:
	var n := kit("campfire", pos, rng.randf() * 360.0, 1.0, props, on_ground)
	var f := socket_pos(n, "flame")
	flame(f, 1.3)
	light(f + Vector3(0, 0.8, 0), FIRE, energy, 13.0, true, true)
	var smoke := VFXLib.particles(Color(0.3, 0.3, 0.32, 0.25), 10, 3.5, false, 1.2, 0.6, 10.0, Vector3(0, 0.6, 0), 0.2, false)
	smoke.position = f + Vector3(0, 0.8, 0)
	deco.add_child(smoke)

func candles(pos: Vector3, energy := 1.2, on_ground := false) -> void:
	var n := kit("candles_cluster", pos, rng.randf() * 360.0, 1.0, deco, on_ground)
	light(socket_pos(n, "light") + Vector3(0, 0.3, 0), Color(1.0, 0.72, 0.4), energy, 5.5, false, true)

func lamp_post(pos: Vector3, yaw_deg := 0.0, on_ground := true) -> void:
	var n := kit("lamp_post", pos, yaw_deg, 1.0, props, on_ground)
	var lp := socket_pos(n, "light")
	var glow := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.09
	sm.height = 0.18
	glow.mesh = sm
	glow.material_override = VFXLib.glow_material(Color(1.0, 0.7, 0.35), 4.0)
	glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	glow.position = lp + Vector3(0, -0.12, 0)
	deco.add_child(glow)
	light(lp + Vector3(0, -0.45, 0), Color(1.0, 0.7, 0.4), 5.0, 10.0, false, true)

# ------------------------------------------------------------------------------------------------------------
# gameplay markers

func spawn(id: StringName, pos: Vector3, yaw_deg := 0.0, on_ground := false) -> Marker3D:
	var m := Marker3D.new()
	m.name = "Spawn_%s" % id
	var p := pos
	if on_ground:
		p.y += ground(pos.x, pos.z)
	m.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)), p)
	m.add_to_group(&"spawn_point")
	m.set_meta(&"spawn_id", id)
	markers.add_child(m)
	root.spawns[id] = m
	return m

func teleporter(id: StringName, pos: Vector3, dest_map: StringName, dest_spawn: StringName, dest_name: String,
		yaw_deg := 0.0, locked := false, unlock_flag := &"", hint := "The runes are dark.") -> Teleporter:
	var t := Teleporter.new()
	t.name = "Teleporter_%s" % id
	t.teleporter_id = id
	t.destination_map = dest_map
	t.destination_spawn = dest_spawn
	t.destination_name = dest_name
	t.locked = locked
	t.unlock_flag = unlock_flag
	t.locked_hint = hint
	t.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(yaw_deg)), pos)
	props.add_child(t)
	# The dais itself must block navigation around its standing stones but stay walkable on top.
	return t

## Future enemy system reads these: where packs spawn, which archetypes, pack size, elite chance.
func enemy_zone(id: String, pos: Vector3, radius: float, enemies: Array, count: int, elite_chance := 0.0, on_ground := false) -> Marker3D:
	var m := Marker3D.new()
	m.name = "EnemyZone_%s" % id
	var p := pos
	if on_ground:
		p.y += ground(pos.x, pos.z)
	m.position = p
	m.add_to_group(&"enemy_zone")
	m.set_meta(&"radius", radius)
	m.set_meta(&"enemies", enemies)
	m.set_meta(&"count", count)
	m.set_meta(&"elite_chance", elite_chance)
	markers.add_child(m)
	return m

func flag_trigger(flag: StringName, center: Vector3, size: Vector3, message := "", xp := 0) -> FlagTrigger:
	var t := FlagTrigger.new()
	t.name = "Trigger_%s" % flag
	t.flag = flag
	t.message = message
	t.xp_reward = xp
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	t.add_child(cs)
	t.position = center
	markers.add_child(t)
	return t

## Named point of interest used by previews and (later) the world map / camera cinematics.
func view(name: String, target: Vector3, yaw_deg := 0.0, pitch_deg := 50.0, dist := 22.0, fov := 45.0) -> void:
	root.views[name] = {"target": target, "yaw": yaw_deg, "pitch": pitch_deg, "dist": dist, "fov": fov}

## Hide `n` once the hero holds `flag` (e.g. a corruption membrane sealing a door). Checked on load and when fired.
func hide_when(n: Node, flag: StringName) -> void:
	n.set_meta(&"hide_when_flag", flag)
	n.add_to_group(&"flag_visual")

func set_bounds(aabb: AABB) -> void:
	root.bounds = aabb

func stats() -> Dictionary:
	return {"lights": _light_count, "shadow_lights": _shadow_lights}
