extends TestCase
## Map-design pass (2026-10-03): the prepared Kenney pieces follow the kit contract, the batcher keeps every part of a
## multi-part piece, authored groups and dungeon motifs reference real pieces and stay deterministic, dungeon dressing
## keeps markers, stairs, bridges and side rooms open, theme materials do not leak between maps, and Low quality only
## thins optional detail (colliders and landmarks never change).

static var _nav_rids: Array[RID] = []
var _holder: Node3D

func _init() -> void:
	strict = true

func _kd_files() -> Array:
	return Array(DirAccess.get_files_at("res://assets/environment/")).filter(func(f): return f.begins_with("kd_") and f.ends_with(".glb"))

func _tris(mesh: Mesh) -> int:
	var n := 0
	for i in mesh.get_surface_count():
		var idx: int = mesh.surface_get_array_index_len(i)
		n += (idx if idx > 0 else mesh.surface_get_array_len(i)) / 3
	return n

# ---- prepared pieces ---------------------------------------------------------------------------------------------

func test_prepared_pieces_follow_the_kit_contract() -> void:
	var files := _kd_files()
	ok(files.size() >= 100, "the prepared set is present (%d pieces)" % files.size())
	for f in files:
		var inst: Node3D = (load("res://assets/environment/" + f) as PackedScene).instantiate()
		var meshes := inst.find_children("*", "MeshInstance3D", true, false)
		eq(meshes.size(), 1, "%s is one mesh" % f)
		if meshes.size() != 1:
			inst.free()
			continue
		var mi: MeshInstance3D = meshes[0]
		var t := Transform3D.IDENTITY
		var n: Node = mi
		while n != inst:
			t = (n as Node3D).transform * t
			n = n.get_parent()
		ok(t.is_equal_approx(Transform3D.IDENTITY), "%s mesh has an identity transform" % f)
		var surfaces := mi.mesh.get_surface_count()
		ok(surfaces >= 1 and surfaces <= 4, "%s has 1-4 surfaces (%d)" % [f, surfaces])
		for i in surfaces:
			var m := mi.mesh.surface_get_material(i)
			var nm := m.resource_name.get_slice(".", 0) if m else "<none>"
			ok(MaterialLibrary.ENV.has(nm), "%s surface %d uses a contract material (%s)" % [f, i, nm])
		var tris := _tris(mi.mesh)
		# focal pieces placed singly get a documented allowance (brief: boats/focal wreck <= 2500); everything else <= 600
		var cap: int = {"kd_wreck.glb": 2500, "kd_bars_gate.glb": 800}.get(f, 600)
		ok(tris <= cap, "%s within its budget (%d <= %d triangles)" % [f, tris, cap])
		var box := mi.get_aabb()
		ok(absf(box.position.y) < 0.02, "%s stands on its origin (bottom %.3f)" % [f, box.position.y])
		ok(inst.find_children("*", "AnimationPlayer", true, false).is_empty() and inst.find_children("*", "Skeleton3D", true, false).is_empty(),
			"%s carries no animation or skeleton" % f)
		inst.free()
	done()

func test_scale_against_the_hero() -> void:
	# initial art targets from the brief: seats ~0.45 m, table tops ~0.75 m, broadleaf trees 4-8 m, palms 5-10 m
	var h := func(nm: String) -> float:
		var inst: Node3D = MapBuilder.scene(nm).instantiate()
		var b := MapBuilder._local_box(nm, inst)
		inst.free()
		return b.size.y
	ok(absf(h.call("kd_table") - 0.75) < 0.08, "a table top is about 0.75 m (%.2f)" % h.call("kd_table"))
	ok(h.call("kd_chair") > 0.9 and h.call("kd_chair") < 1.15, "a chair back stands about a metre (%.2f)" % h.call("kd_chair"))
	for t in ["kd_tree_oak", "kd_tree_broadleaf", "kd_tree_detailed", "kd_tree_thin"]:
		ok(h.call(t) >= 4.0 and h.call(t) <= 8.0, "%s is 4-8 m (%.1f)" % [t, h.call(t)])
	for t in ["kd_palm", "kd_palm_bend", "kd_palm_tall"]:
		ok(h.call(t) >= 5.0 and h.call(t) <= 10.0, "%s is 5-10 m (%.1f)" % [t, h.call(t)])
	ok(h.call("kd_barrel") > 0.85 and h.call("kd_barrel") < 1.05, "a barrel is under the hero's chest (%.2f)" % h.call("kd_barrel"))
	done()

func test_batched_pieces_keep_every_part() -> void:
	# the armillary sphere is five transformed parts: the batcher must merge all of them where they stand
	var inst: Node3D = MapBuilder.scene("armillary_sphere").instantiate()
	var verts := 0
	for mi in inst.find_children("*", "MeshInstance3D", true, false):
		for i in (mi as MeshInstance3D).mesh.get_surface_count():
			verts += (mi as MeshInstance3D).mesh.surface_get_array_len(i)
	var box := MapBuilder._local_box("armillary_sphere", inst)
	inst.free()
	var merged := MapBuilder._merged_mesh(MapBuilder.scene("armillary_sphere").instantiate())
	var mv := 0
	for i in merged.get_surface_count():
		mv += merged.surface_get_array_len(i)
	eq(mv, verts, "every part's vertices are in the batched mesh")
	ok(merged.get_aabb().position.is_equal_approx(box.position) and merged.get_aabb().size.is_equal_approx(box.size),
		"parts keep their transforms (bounds %s vs %s)" % [merged.get_aabb(), box])
	# a one-part piece is used as is
	var one := MapBuilder._merged_mesh(MapBuilder.scene("kd_barrel").instantiate())
	eq(one.get_surface_count(), 2, "a single-mesh piece keeps its two surfaces")
	done()

func test_groups_and_motifs_reference_real_pieces() -> void:
	for nm in DataVignettes.pieces() + DataDungeonRoles.pieces():
		ok(ResourceLoader.exists(MapBuilder.ENV_DIR % nm), "%s exists" % nm)
	var themes := {}
	for id in DataDungeons.defs():
		themes[StringName(DataDungeons.get_def(id).theme)] = true
	for th in themes:
		ok(DataDungeonRoles.T.has(th), "theme %s has room roles" % th)
	for th in DataDungeonRoles.T:
		for role in ["arrival", "work", "function", "traversal", "seal", "decay"]:
			for m in DataDungeonRoles.T[th].get(role, []):
				ok(DataDungeonRoles.M.has(m), "%s/%s motif %s exists" % [th, role, m])
	for d in DataDungeonRoles.BY_DUNGEON:
		ok(DataDungeons.defs().has(d), "variant %s is a registered dungeon" % d)
	# Low thins every batched new piece on purpose (MapBuilder.LITE_KEEP), never by accident
	for k in DataVignettes.V:
		for p in DataVignettes.V[k].pieces:
			if p[4] == "b":
				ok(MapBuilder.LITE_KEEP.has(p[0]), "%s (batched in %s) has a Low retention" % [p[0], k])
	done()

# ---- maps --------------------------------------------------------------------------------------------------------

func _build(id: StringName) -> MapRoot:
	return Game.build_map(id)

func test_town_groups_are_deterministic_and_on_their_surfaces() -> void:
	var a := _build(&"sanctuary")
	var b := _build(&"sanctuary")
	var va: Array = a.get_meta(&"vignettes", [])
	var vb: Array = b.get_meta(&"vignettes", [])
	ok(va.size() >= 20, "Malasugue has its authored groups (%d)" % va.size())
	eq(va.map(func(g): return "%s@%s" % [g.name, g.origin]), vb.map(func(g): return "%s@%s" % [g.name, g.origin]), "a rebuild places the same groups")
	for g in va:
		for h in va:
			if g != h:
				ok(Vector2(g.origin.x - h.origin.x, g.origin.z - h.origin.z).length() >= (float(g.r) + float(h.r)) * 0.84 or not (g.checked and h.checked),
					"%s and %s do not overlap" % [g.name, h.name])
	a.free()
	b.free()
	# Agdao: every group stands at its own terrace's height, never on the terrain under a raised surface
	var ag := _build(&"agdao")
	var builder: GDScript = load(ag.def.builder)
	var probe = builder.new()
	var n := 0
	for g in ag.get_meta(&"vignettes", []):
		var o: Vector3 = g.origin
		var tier: Dictionary = probe.TIERS[probe.tier_at(o.z + 1.6)]
		if o.z > 50.0 or o.x < float(tier.x0) or o.x > float(tier.x1):
			continue              # moored boats, and the hillside groups that follow the slope
		var want: float = probe.tier_y(probe.tier_at(o.z + 1.6))
		ok(absf(o.y - want) < 0.05, "Agdao %s at (%.0f, %.0f) stands on its terrace (%.1f vs %.1f)" % [g.name, o.x, o.z, o.y, want])
		n += 1
	ok(n >= 15, "Agdao's terraces are dressed (%d groups)" % n)
	ag.free()
	done()

func test_every_outdoor_map_has_three_composed_places() -> void:
	for id in [&"sanctuary", &"westreach", &"olivar", &"wyman_outpost", &"ruined_forest", &"agdao", &"zr_coilwood", &"zr_barrens", &"zr_citadel"]:
		var m := _build(id)
		var names := {}
		for g in m.get_meta(&"vignettes", []):
			names[g.name] = true
		ok(names.size() >= 3, "%s has at least three kinds of authored place (%s)" % [id, names.keys()])
		m.free()
	done()

func test_low_quality_only_thins_optional_detail() -> void:
	var was := Settings.efficiency_mode
	var count := func(lite: bool) -> Array:
		Settings.efficiency_mode = lite
		var m := _build(&"sanctuary")
		var bodies := m.find_child("Props", true, false).find_children("*", "StaticBody3D", true, false).size()
		var groups: int = (m.get_meta(&"vignettes", []) as Array).size()
		var deco := m.find_child("Decoration", true, false).get_child_count()
		m.free()
		return [bodies, groups, deco]
	var hi: Array = count.call(false)
	var lo: Array = count.call(true)
	Settings.efficiency_mode = was
	eq(lo[0], hi[0], "Low keeps every collider")
	eq(lo[1], hi[1], "Low keeps every authored group")
	ok(lo[2] <= hi[2], "Low draws no more decoration (%d vs %d)" % [lo[2], hi[2]])
	done()

## Stone surfaces of the prepared pieces in a built map (batched, so read from the MultiMesh meshes).
func _kd_stone(m: Node) -> Array:
	var out := []
	for n in m.find_children("Batch_kd_*", "MultiMeshInstance3D", true, false):
		var mesh := (n as MultiMeshInstance3D).multimesh.mesh
		for i in mesh.get_surface_count():
			var mat := mesh.surface_get_material(i)
			if mat and mat.resource_name == "BH_Stone":
				out.append(mat)
	return out

func test_theme_materials_do_not_leak() -> void:
	MaterialLibrary.pop_theme()
	var town_stone := MaterialLibrary.env("BH_Stone")
	var dg := _build(DataDungeons.map_id(&"ember", 1))
	eq(MaterialLibrary.theme_id, "", "the dungeon's theme is popped after its build")
	var ds := _kd_stone(dg)
	ok(not ds.is_empty() and ds.all(func(m): return m != town_stone), "prepared stone pieces take the dungeon's own stone (%d)" % ds.size())
	dg.free()
	var town := _build(&"sanctuary")
	var ts := _kd_stone(town)
	ok(not ts.is_empty() and ts.all(func(m): return m == town_stone), "back in town, stone is town stone (%d)" % ts.size())
	town.free()
	done()

# ---- dungeons ----------------------------------------------------------------------------------------------------

func _dungeon_floors() -> Array:
	var out := []
	for id in DataDungeons.defs():
		out.append(DataDungeons.map_id(id, 1))
		out.append(DataDungeons.map_id(id, DataDungeons.floor_count(id)))
	return out

func test_dungeon_rooms_have_roles_and_keep_markers_clear() -> void:
	var themes := {}
	for mid in _dungeon_floors():
		var m := _build(mid)
		var rooms: Array = m.get_meta(&"rooms", [])
		ok(not rooms.is_empty(), "%s has rooms" % mid)
		var keep := {}
		for c in m.get_meta(&"room_keep", []):
			keep[Vector2i(c[0], c[1])] = true
		var roles := {}
		var groups := 0
		for r in rooms:
			roles[r.role] = true
			for g in r.groups:
				groups += 1
				var c := Vector2i(g.cell[0], g.cell[1])
				ok(not keep.has(c), "%s: %s at %s stays off marker cells" % [mid, g.motif, c])
		ok(roles.has("arrival"), "%s has an arrival room" % mid)
		ok(groups >= 3, "%s has rooms with a purpose (%d groups)" % [mid, groups])
		var p := DataDungeons.parse(mid)
		if p[1] == DataDungeons.floor_count(p[0]):
			ok(roles.has("boss"), "%s (the last floor) has a boss arena" % mid)
		themes[String(DataDungeons.get_def(p[0]).theme)] = true
		m.free()
	ok(themes.size() >= 25, "every theme dressed (%d)" % themes.size())
	# determinism: a rebuild dresses the same cells
	var a := _build(&"dg_deeps_2")
	var b := _build(&"dg_deeps_2")
	eq(JSON.stringify(a.get_meta(&"rooms")), JSON.stringify(b.get_meta(&"rooms")), "a floor rebuilds with the same rooms and motifs")
	a.free()
	b.free()
	# deeper growth floors keep their own theme's dressing (no generic fallback)
	var deep := _build(DataDungeons.map_id(&"warren", DataDungeons.floor_count(&"warren") + 1))
	var motifs: Array = []
	for r in deep.get_meta(&"rooms", []):
		for g in r.groups:
			motifs.append(g.motif)
	ok(not motifs.is_empty(), "a growth floor is dressed")
	ok(not motifs.has("storage_wet") and not motifs.has("coffin_old"), "a fungal growth floor is not dressed as the drowned Deeps (%s)" % [motifs])
	deep.free()
	done()

func _path(m: MapRoot, a: Vector3, b: Vector3, tol := 2.0) -> bool:
	var nm := m.nav_region.get_navigation_map()
	var pa := NavigationServer3D.map_get_closest_point(nm, a)
	var pb := NavigationServer3D.map_get_closest_point(nm, b)
	var path := NavigationServer3D.map_get_path(nm, pa, pb, true)
	return not path.is_empty() and path[path.size() - 1].distance_to(pb) < 0.3 and pb.distance_to(b) < tol

## No side room is cut off: every floor cell not itself holding a corner landmark is reachable from the arrival.
func test_dungeon_dressing_never_blocks_a_room() -> void:
	_holder = Node3D.new()
	host.add_child(_holder)
	for id in DataDungeons.defs():
		var mid := DataDungeons.map_id(id, 1)
		var m := Game.build_map(mid)
		_holder.add_child(m)
		_nav_rids.append(MapBuilder.isolate_navigation(m))
		MapBuilder.bake_navigation(m)
		var start: Vector3 = m.spawns[&"start"].global_position
		var skip := {}
		for r in m.get_meta(&"rooms", []):
			for g in r.groups:
				var mot: Dictionary = DataDungeonRoles.M.get(g.motif, {})
				if String(g.motif).begins_with("boss:") or mot.get("corner", false):
					skip[Vector2i(g.cell[0], g.cell[1])] = true
		var p := DataDungeons.parse(mid)
		var plan: Array = DataDungeons.floor_def(p[0], p[1]).plan
		var bad := []
		for r in plan.size():
			for c in String(plan[r]).length():
				var k := String(plan[r])[c]
				if not k in ["0", "1", "2"] or skip.has(Vector2i(c, r)):
					continue
				var xz := DataDungeons.cell_xz(plan, Vector2i(c, r))
				if not _path(m, start, Vector3(xz.x, int(k) * 4.0, xz.y)):
					bad.append(Vector2i(c, r))
		ok(bad.is_empty(), "%s: every room cell is reachable %s" % [mid, bad])
	for rid in _nav_rids:
		NavigationServer3D.free_rid(rid)
	_nav_rids.clear()
	_holder.queue_free()
	await host.get_tree().process_frame
	done()
