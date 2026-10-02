extends TestCase
## Efficiency mode (bh-009, Mobile): the Mobile preset, the lite map build (fewer triangles, chunked decoration and
## terrain, no shadows / sky / depth-reading shaders) with gameplay geometry untouched, the light budget and the
## animation sleep. Nothing here writes the player's settings file.

func _init() -> void:
	strict = true

var _saved := {}

func _save_settings() -> void:
	for k in Settings.KEYS:
		_saved[k] = Settings.get(k)

func _restore_settings() -> void:
	for k in _saved:
		Settings.set(k, _saved[k])

func _build(id: StringName, lite: bool) -> MapRoot:
	Settings.efficiency_mode = lite
	var m := Game.build_map(id)
	return m

static func _tris(mesh: Mesh) -> int:
	var t := 0
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var idx = arr[Mesh.ARRAY_INDEX]
		t += (idx as PackedInt32Array).size() / 3 if idx != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
	return t

static func _census(m: MapRoot) -> Dictionary:
	var out := {"tris": 0, "shadow_casters": 0, "decor_instances": {}, "chunks_ok": true}
	for n in m.find_children("*", "GeometryInstance3D", true, false):
		if n is MultiMeshInstance3D and n.multimesh and n.multimesh.mesh:
			var mm: MultiMesh = n.multimesh
			out.tris += _tris(mm.mesh) * mm.instance_count
			var parts := String(n.name).trim_prefix("Batch_").split("_")     # Batch_<asset>_<cx>_<cz>
			var asset := "_".join(parts.slice(0, parts.size() - 2))
			out.decor_instances[asset] = int(out.decor_instances.get(asset, 0)) + mm.instance_count
			# every instance lies inside its own chunk cell (the camera can cull the cell)
			var cell := Vector2i(floori(mm.get_instance_transform(0).origin.x / MapBuilder.CHUNK), floori(mm.get_instance_transform(0).origin.z / MapBuilder.CHUNK))
			for i in mm.instance_count:
				var o := mm.get_instance_transform(i).origin
				if Vector2i(floori(o.x / MapBuilder.CHUNK), floori(o.z / MapBuilder.CHUNK)) != cell:
					out.chunks_ok = false
		elif n is MeshInstance3D and n.mesh:
			out.tris += _tris(n.mesh)
		if n.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF and n is MultiMeshInstance3D:
			out.shadow_casters += 1
	return out

static func _heightmap(m: MapRoot) -> PackedFloat32Array:
	for cs in m.find_children("*", "CollisionShape3D", true, false):
		if cs.shape is HeightMapShape3D:
			return (cs.shape as HeightMapShape3D).map_data
	return PackedFloat32Array()

func test_mobile_preset() -> void:
	_save_settings()
	Settings._desktop_preset()
	ok(not Settings.lite, "desktop preset: efficiency off")
	Settings._efficiency_preset()
	ok(Settings.lite, "Mobile preset turns efficiency mode on")
	eq(Settings.shadows_quality, 0, "no shadows")
	eq(Settings.effects_quality, 0, "no post effects")
	eq(Settings.anti_aliasing, 0, "no anti-aliasing")
	ok(Settings.render_scale <= 0.75, "3D drawn below native resolution")
	eq(Settings.fps_limit, 30, "30 fps cap (battery, heat, steady frame pacing)")
	ok(not Settings.glow and not Settings.ssao, "glow and SSAO off in efficiency mode")
	ok("efficiency_mode" in Settings.KEYS, "efficiency mode is saved with the settings")
	ok(Settings.GROUPS.video.has("efficiency_mode"), "reset with the video group")
	_restore_settings()
	done()

func test_lite_build_is_lighter_with_the_same_gameplay() -> void:
	_save_settings()
	for id: StringName in [&"westreach", &"ruined_forest"]:
		var full := _build(id, false)
		var lite := _build(id, true)
		var cf := _census(full)
		var cl := _census(lite)
		ok(cl.tris < cf.tris * 0.75, "%s: lite build has at most 3/4 of the triangles (%d vs %d)" % [id, cl.tris, cf.tris])
		ok(cf.chunks_ok and cl.chunks_ok, "%s: decoration batches are cut into cullable cells" % id)
		eq(cl.shadow_casters, 0, "%s: no decoration casts shadows in efficiency mode" % id)
		if cf.decor_instances.has("fern"):
			ok(cl.decor_instances.get("fern", 0) < cf.decor_instances.fern * 0.35, "%s: undergrowth thinned" % id)
		for asset in cf.decor_instances:
			if String(asset).ends_with("~o"):
				# map-design pass: optional storytelling details (DataVignettes "o") are left out on Low by design
				eq(cl.decor_instances.get(asset, 0), 0, "%s: optional detail %s left out" % [id, asset])
				continue
			if not MapBuilder.LITE_KEEP.has(asset):
				eq(cl.decor_instances.get(asset, 0), cf.decor_instances[asset], "%s: %s (not thinned) kept whole" % [id, asset])
		# gameplay geometry is identical: the same ground heights, colliders, spawns, teleporters, exits
		eq(_heightmap(lite), _heightmap(full), "%s: identical collision height map" % id)
		eq(lite.find_children("*", "CollisionShape3D", true, false).size(), full.find_children("*", "CollisionShape3D", true, false).size(),
			"%s: the same colliders" % id)
		eq(lite.spawns.keys(), full.spawns.keys(), "%s: the same spawn points" % id)
		eq(lite.teleporters().size(), full.teleporters().size(), "%s: the same teleporters" % id)
		for sid in full.spawns:
			ok(lite.spawns[sid].position.is_equal_approx(full.spawns[sid].position), "%s: spawn %s in the same place" % [id, sid])
		# the terrain is drawn as culled tiles in efficiency mode
		var terr := lite.find_child("Terrain", true, false)
		ok(terr != null and terr.get_child_count() > 1, "%s: lite terrain is tiled" % id)
		# no sky pass, no SSAO/glow/colour grade, no sun shadow
		var env := lite.environment.environment
		ok(env.background_mode != Environment.BG_SKY and not env.ssao_enabled and not env.glow_enabled and not env.adjustment_enabled,
			"%s: lean environment" % id)
		ok(not lite.sun.shadow_enabled, "%s: no sun shadow" % id)
		for l: Light3D in lite.find_children("*", "Light3D", true, false):
			ok(not l.shadow_enabled, "%s: no light casts shadows" % id)
		# no shader reads the depth buffer (mist, full water)
		var depth_readers := 0
		for mi: MeshInstance3D in lite.find_children("*", "MeshInstance3D", true, false):
			var mat := mi.material_override as ShaderMaterial
			if mat and mat.shader and "hint_depth_texture" in mat.shader.code:
				depth_readers += 1
		eq(depth_readers, 0, "%s: no depth-reading shaders" % id)
		full.free()
		lite.free()
	_restore_settings()
	done()

func test_lite_navigation_matches() -> void:
	_save_settings()
	var holder := Node3D.new()
	host.add_child(holder)
	var polys := []
	for lite in [false, true]:
		var m := _build(&"ruined_forest", lite)
		holder.add_child(m)
		MapBuilder.isolate_navigation(m)
		MapBuilder.bake_navigation(m)
		polys.append(m.nav_region.navigation_mesh.get_polygon_count())
		m.free()
	eq(polys[1], polys[0], "the navmesh is baked from identical colliders")
	holder.free()
	_restore_settings()
	done()

func test_light_budget() -> void:
	_save_settings()
	Settings.efficiency_mode = true
	var holder := Node3D.new()
	host.add_child(holder)
	var lights: Array[OmniLight3D] = []
	# measured far from the origin, where other suites' maps (and their lights) may still stand
	var o := Vector3(5000, 0, 0)
	for i in 12:
		var l := OmniLight3D.new()
		l.omni_range = 8.0
		l.position = o + Vector3(i * 4.0, 2, 0)
		holder.add_child(l)
		lights.append(l)
	var hidden := OmniLight3D.new()     # a light its owner switched off stays off
	hidden.visible = false
	hidden.position = o + Vector3(1, 2, 0)
	holder.add_child(hidden)
	Perf._budget_lights(o)
	eq(Perf.stats.lights_on, Perf.LIGHT_BUDGET, "only the budgeted number of lights shine")
	for i in Perf.LIGHT_BUDGET:
		ok(not Perf._off_lights.has(lights[i]), "light %d (among the nearest) is on" % i)
	ok(Perf._off_lights.has(lights[11]), "the farthest light is off")
	ok(Perf._off_lights.has(hidden), "a hidden light never takes a slot")
	ok(lights[11].visible, "the budget never touches the node's own visibility")
	# walk to the other end: the budget follows
	Perf._budget_lights(o + Vector3(44, 0, 0))
	ok(not Perf._off_lights.has(lights[11]) and Perf._off_lights.has(lights[0]), "the budget follows the hero")
	Settings.efficiency_mode = false
	Perf._restore()
	ok(Perf._off_lights.is_empty(), "leaving efficiency mode gives every light back")
	holder.free()
	_restore_settings()
	done()

func test_anim_sleep_respects_frozen() -> void:
	var v := CharacterVisual.new()
	host.add_child(v)
	v.setup(DB.class_def(&"knight").model_path, 1.0, Color.WHITE, &"knight")
	ok(v.tree != null and v.tree.active, "tree runs")
	v.set_anim_awake(false)
	ok(not v.tree.active, "asleep: the tree stops")
	v.set_anim_awake(true)
	ok(v.tree.active, "awake: the tree runs again")
	v._frozen_pose = true
	v.set_anim_awake(false)
	v.set_anim_awake(true)
	ok(not v.tree.active, "waking never thaws a frozen body")
	v.free()
	done()

func test_particles_scaled() -> void:
	_save_settings()
	Settings.efficiency_mode = false
	eq(Perf.particles(50), 50, "desktop: every particle")
	Settings.efficiency_mode = true
	eq(Perf.particles(50), 20, "efficiency mode: 40 %")
	eq(Perf.particles(1), 1, "never zero")
	_restore_settings()
	done()

func test_save_does_not_override_device_settings() -> void:
	_save_settings()
	Settings._efficiency_preset()
	Settings.control_mode = "mobile"
	Settings.master_volume = 0.9
	# a save written on a desktop before efficiency mode existed
	var snap := {"shadows_quality": 3, "fps_limit": 0, "effects_quality": 3, "render_scale": 1.0, "control_mode": "pc",
		"anti_aliasing": 4, "master_volume": 0.5}
	Settings.from_dict(snap)
	ok(Settings.lite, "efficiency mode survives loading a save")
	eq(Settings.shadows_quality, 0, "the save's shadows stay on the desktop")
	eq(Settings.fps_limit, 30, "the 30 fps cap stays")
	eq(Settings.control_mode, "mobile", "touch play stays")
	near(Settings.master_volume, 0.5, 0.001, "hero-side settings still come from the save")
	_restore_settings()
	Settings.apply()
	done()
