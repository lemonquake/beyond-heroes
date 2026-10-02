extends SettlementBuilder
## MAP — The Glasswire Barrens (bh-029; Zarael, levels 36–42). "Where the Blackwire broke the ground."
##
## East of the Coilwood the trees give out on a red cracked plain. Where the Blackwire broke through, the ground split in
## long fissures of dark soil and violet glass grew out of them; they all run back to the fallen Wirewright colossus, face
## up in a shallow bowl, its broken coils still throwing sparks. Ochre outcrops and mesa cliffs wall the plain; a line of
## dead relay pylons crosses it toward Agdao. Agdao's scouts and the farmers who could not get home over the Bridge hold a
## walled camp on the road (waypoint, bonfire checkpoint, Quillan Ashby); the Bridge Road climbs north through a pass to
## the Bridge of Death. Two Vaults open here: the Obsidian Engine's black-glass doors in the north-west and the Veinworks'
## cleft of bone in the east. Frozen spots: DataZarael / DataDungeonsZarael; road beds follow DataIsland's polylines.

const MAP := &"zr_barrens"
const CAMP_R := 19.0
const COLOSSUS := Vector3(52.0, 0.0, -42.0)   # its body lies just north of the trail's end (the landmark spot)
const COLOSSUS_S := 1.5
## Landform anchors (x, z, height): inverse-distance blended into the smooth ground the road beds follow.
const ANCHORS := [
	Vector3(-126, 10, 0.5), Vector3(-90, 16, 0.8), Vector3(-60, 26, 1.0), Vector3(-40, 30, 1.0), Vector3(-16, 22, 0.8),
	Vector3(0, 10, 0.6), Vector3(14, -20, 0.2), Vector3(24, -50, 0.0), Vector3(28, -76, 1.6), Vector3(30, -96, 3.0),
	Vector3(52, -40, -1.8), Vector3(40, -34, -1.0), Vector3(66, -46, -1.2), Vector3(48, -28, -0.6), Vector3(-70, -64, 2.2),
	Vector3(-62, -30, 1.2), Vector3(-52, 6, 1.0), Vector3(84, 40, 2.4), Vector3(60, 34, 1.4), Vector3(30, 20, 0.5),
	Vector3(-20, 76, 0.4), Vector3(-90, 60, 1.6), Vector3(-100, -40, 2.6), Vector3(100, -20, 2.2), Vector3(100, 70, 3.0),
	Vector3(-10, -60, 1.0), Vector3(80, -76, 4.0), Vector3(-30, -86, 3.4), Vector3(20, 60, 0.6),
]
## The Blackwire fissures (dark soil, a shallow trench, glass growths along them): they all run back to the colossus.
const FISSURES := [
	[Vector2(52, -40), Vector2(70, -12), Vector2(80, 14), Vector2(86, 36)],
	[Vector2(52, -40), Vector2(22, -60), Vector2(-10, -70), Vector2(-40, -66), Vector2(-66, -62)],
	[Vector2(52, -40), Vector2(88, -56), Vector2(118, -72)],
	[Vector2(-8, -16), Vector2(-44, -28), Vector2(-76, -26), Vector2(-108, -40)],
	[Vector2(6, 26), Vector2(-4, 52), Vector2(-26, 84)],
	[Vector2(70, -12), Vector2(104, 4), Vector2(124, 0)],
]
const PADS := [[-40.0, 30.0, 22.0], [-70.0, -64.0, 10.0], [84.0, 40.0, 10.0], [52.0, -40.0, 18.0]]
## Encounter camps: [id, centre, radius, monsters, count, levels, elite chance]. Levels rise from the west road.
const CAMPS := [
	["gb_west_husks", Vector2(-96, -4), 5.0, [&"wiresick_husk", &"wiresick_husk", &"wiresick_husk", &"relay_mote"], 4, Vector2i(36, 37), 0.1],
	["gb_southwest", Vector2(-92, 50), 5.0, [&"glasswire_scorpion", &"wiresick_husk", &"wiresick_husk"], 3, Vector2i(36, 38), 0.1],
	["gb_south_husks", Vector2(-18, 76), 6.0, [&"wiresick_husk", &"wiresick_husk", &"relay_mote", &"wiresick_husk", &"wiresick_husk"], 5, Vector2i(36, 38), 0.1],
	["gb_glass_trail", Vector2(-48, -22), 5.0, [&"arc_sentinel", &"wiresick_husk", &"wiresick_husk"], 4, Vector2i(37, 39), 0.15],
	["gb_red_flats", Vector2(14, 48), 5.0, [&"wiresick_husk", &"relay_mote", &"glasswire_scorpion"], 4, Vector2i(37, 39), 0.15],
	["gb_scorpions", Vector2(-14, -32), 5.5, [&"glasswire_scorpion", &"glasswire_scorpion", &"wiresick_husk"], 3, Vector2i(38, 40), 0.15],
	["gb_obsidian", Vector2(-86, -56), 5.0, [&"arc_sentinel", &"chain_priest", &"arc_sentinel"], 4, Vector2i(39, 41), 0.2],
	["gb_colossus", Vector2(72, -24), 5.0, [&"arc_sentinel", &"relay_mote", &"glasswire_scorpion"], 4, Vector2i(40, 42), 0.2],
	["gb_colossus_chains", Vector2(42, -62), 5.5, [&"chain_priest", &"chain_bearer", &"wiresick_husk", &"chain_priest"], 5, Vector2i(40, 42), 0.2],
	["gb_bridge_road", Vector2(8, -80), 5.0, [&"chain_priest", &"chain_bearer", &"arc_sentinel"], 4, Vector2i(40, 42), 0.2],
	["gb_vein", Vector2(64, 56), 5.0, [&"glasswire_scorpion", &"chain_bearer", &"wiresick_husk"], 4, Vector2i(40, 42), 0.2],
	["gb_east", Vector2(104, 8), 5.0, [&"arc_sentinel", &"arc_sentinel", &"relay_mote"], 3, Vector2i(41, 42), 0.2],
	["gb_east_glass", Vector2(100, -58), 5.0, [&"glasswire_scorpion", &"relay_mote", &"glasswire_scorpion"], 4, Vector2i(41, 42), 0.25],
]
const WEST_EXIT := [Vector2(-144, 10.0), Vector2(-126, 10.0)]
const NORTH_EXIT := [Vector2(30, -96.0), Vector2(31.0, -128.0)]
## The dead relay line across the plain: [x, z, toppled].
const DEAD_PYLONS := [[-104.0, -30.0, false], [-74.0, -40.0, true], [-36.0, -42.0, false], [-4.0, -44.0, true], [92.0, -32.0, false]]

var _fd := PackedFloat32Array()        # distance to the nearest fissure, per lattice vertex

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.031, 0.02, 0.031), "sky_horizon": Color(0.293, 0.174, 0.179),
		"ambient": Color(0.425, 0.373, 0.372), "ambient_energy": 1.0,
		"fog": Color(0.171, 0.116, 0.122), "fog_density": 0.0055, "fog_height": 0.0, "fog_height_density": 0.05,
		"sun": Color(0.889, 0.673, 0.619), "sun_energy": 0.7, "sun_rot": Vector3(-36, 32, 0), "glow": 1.0,
		"exposure": 1.18, "contrast": 1.08, "saturation": 0.96,
	})
	# the fissure field is needed while the lattice is shaped: lay it out on the same lattice first
	X0 = -142.0
	Z0 = -128.0
	W = 284
	D = 242
	_gw = W + 1
	_fd.resize(_gw * (D + 1))
	_fd.fill(99.0)
	for f in FISSURES:
		raster_line(f, _fd, 8.0)
	prepare(X0, Z0, W, D, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "red_clay", "moss": "blackwire_soil", "dirt": "sand_path", "path": "terrace_paving", "rock": "cliff_ochre"},
		Color(1.0, 0.94, 0.9))
	_edges()
	_camp()
	_colossus()
	_fissures()
	_dead_relays()
	_gates()
	_outcrops()
	_encounters()
	_scrub()
	_map_design()
	spawn(&"coil_road", Vector3(DataZarael.GB_WEST.x, 0, DataZarael.GB_WEST.z), 90.0, true)
	spawn(&"start", Vector3(DataZarael.GB_WEST.x, 0, DataZarael.GB_WEST.z), 90.0, true)
	spawn(&"bridge_road", Vector3(DataZarael.GB_NORTH.x, 0, DataZarael.GB_NORTH.z), 0.0, true)
	set_bounds(AABB(Vector3(-130, -6, -100), Vector3(260, 40, 200)))
	view("overview", Vector3(0, 0, 0), 0.0, 60.0, 240.0, 50.0)
	view("topdown", Vector3(0, 0, 0), 0.0, 89.5, 260.0, 55.0)
	view("camp", Vector3(-40, 2, 30), 0.0, 50.0, 46.0, 45.0)
	view("colossus", Vector3(50, 0, -38), 0.0, 40.0, 56.0, 45.0)
	view("crossroads", Vector3(2, 1, 6), 0.0, 46.0, 40.0, 45.0)
	view("obsidian_gate", Vector3(-70, 3, -62), 0.0, 44.0, 30.0, 45.0)
	view("vein_gate", Vector3(82, 3, 40), 0.0, 44.0, 32.0, 45.0)
	view("north_pass", Vector3(28, 3, -84), 0.0, 44.0, 40.0, 45.0)
	view("west_road", Vector3(-112, 2, 12), 0.0, 46.0, 40.0, 45.0)

# ------------------------------------------------------------------------------------------------------------
# landform

func _noise(x: float, z: float) -> float:
	return sin(x * 0.09 + z * 0.04) * 0.6 + cos(x * 0.035 - z * 0.08) * 0.8 + sin(z * 0.19 + x * 0.15) * 0.2

func _idw(x: float, z: float) -> float:
	var num := 0.0
	var den := 0.0
	for a: Vector3 in ANCHORS:
		var d2 := (x - a.x) * (x - a.x) + (z - a.y) * (z - a.y)
		var w := 1.0 / (d2 * d2 + 900.0)
		num += a.z * w
		den += w
	return num / den

func _stub_dist(x: float, z: float) -> float:
	var p := Vector2(x, z)
	return minf(seg_dist(p, WEST_EXIT[0], WEST_EXIT[1]), seg_dist(p, NORTH_EXIT[0], NORTH_EXIT[1]))

## Distance to any route (charted roads, trails, exit stubs) without the 14 m cap of the lattice field.
var _segs: Array = []
func _route_dist(x: float, z: float) -> float:
	if _segs.is_empty():
		for r in DataIsland.roads_on(MAP):
			for i in r.points.size() - 1:
				_segs.append([r.points[i], r.points[i + 1]])
		_segs.append([WEST_EXIT[0], WEST_EXIT[1]])
		_segs.append([NORTH_EXIT[0], NORTH_EXIT[1]])
	var p := Vector2(x, z)
	var d := INF
	for sg in _segs:
		d = minf(d, seg_dist(p, sg[0], sg[1]))
	return d

func _landform(x: float, z: float) -> float:
	var h := _idw(x, z)
	# mesa country rises on every side; the two roads leave through cuts
	var e := maxf(maxf(absf(z) - 86.0, absf(x) - 118.0), 0.0)
	var cut := 1.0 - smoothstep(6.0, 14.0, _stub_dist(x, z))
	h += minf(e * 1.0, 16.0) * (1.0 - cut)
	return h

func _shape(x: float, z: float, b: float, _rd: float, _rt: int) -> float:
	var h := b + _noise(x, z) * 0.7 + (sin(x * 0.031 + 1.3) * cos(z * 0.027 - 0.4)) * 1.3
	var sd := _stub_dist(x, z)
	if sd < 7.0:
		h = lerpf(b, h, smoothstep(3.0, 6.5, sd))
	for p in PADS:
		var d := Vector2(x, z).distance_to(Vector2(p[0], p[1]))
		if d < p[2] + 3.0:
			h = lerpf(h, b + _noise(x, z) * 0.12, 1.0 - smoothstep(p[2] * 0.6, p[2] + 3.0, d))
	# the fissures: a shallow trench of broken ground (the road beds are levelled over it afterwards)
	var fd := _fd[_k(x, z)]
	if fd < 3.0:
		h -= 0.55 * (1.0 - smoothstep(0.6, 3.0, fd))
	return h

func _splat(x: float, z: float) -> Color:
	var k := _k(x, z)
	var rdd := _rd[k]
	if absf(x) > 124.0 or z < -94.0:
		rdd = minf(rdd, _stub_dist(x, z))
	var n := sin(x * 0.37 + z * 0.23) * 0.5 + 0.5
	var n2 := sin(x * 0.8 - z * 0.6) * cos(z * 0.47 + x * 0.2) * 0.5 + 0.5
	var is_road := _rt[k] == 1 or absf(x) > 124.0 or z < -94.0
	# the old Wirewright road: worn paving, half buried in red dust
	var road := (1.0 - smoothstep(1.8, 3.4, rdd)) * clampf(0.35 + n2 * 0.8, 0.0, 1.0) if is_road else 0.0
	var trail := (1.0 - smoothstep(1.0, 2.4, rdd)) if _rt[k] == 2 else 0.0
	var dust := (1.0 - smoothstep(2.5, 4.5, rdd)) * 0.6 if is_road else 0.0
	var wob := sin(x * 0.53 + z * 0.31) * cos(z * 0.47 - x * 0.19)
	var fiss := (1.0 - smoothstep(0.6 + wob * 0.5, 2.6 + wob * 1.4, _fd[k])) * (0.8 + n * 0.2)
	var patch := smoothstep(0.35, 0.8, sin(x * 0.045 + z * 0.02) * cos(z * 0.05 - x * 0.013) * 0.5 + 0.5 + n2 * 0.25)
	var bowl := (1.0 - smoothstep(10.0, 24.0, Vector2(x, z).distance_to(Vector2(52, -40)))) * (0.55 + n2 * 0.45)
	var camp := 1.0 - smoothstep(CAMP_R - 6.0, CAMP_R - 2.0, Vector2(x, z).distance_to(DataZarael.GB_CAMP))
	var r := clampf(maxf(maxf(maxf(trail, dust), camp * 0.7), patch * 0.55) + n * 0.1, 0.0, 1.0)
	var g := clampf(maxf(fiss, bowl * 0.85), 0.0, 1.0) * (1.0 - trail)
	var bb := clampf(road, 0.0, 1.0)
	return Color(r * (1.0 - bb) * (1.0 - g * 0.6), g * (1.0 - bb), bb)

# ------------------------------------------------------------------------------------------------------------
# helpers

func _foot(c: Vector2, r: float) -> float:
	var m := height_at(c.x, c.y)
	for i in 8:
		var a := TAU * i / 8.0
		m = minf(m, height_at(c.x + cos(a) * r, c.y + sin(a) * r))
	return m

func _brazier(p: Vector2, energy := 3.0, shadow := false) -> void:
	var y := _foot(p, 0.55)
	var n := kit("zr_brazier_stone", Vector3(p.x, y, p.y), rng.randf() * 360.0)
	var f := socket_pos(n, "flame")
	flame(f, 1.1)
	light(f + Vector3(0, 0.5, 0), FIRE, energy, 11.0, shadow, true)

func _on(n: String, p: Vector2, yaw: float, s := 1.0, r := 1.0, parent: Node3D = null, sink := 0.05) -> Node3D:
	return kit(n, Vector3(p.x, _foot(p, r * s) - sink, p.y), yaw, s, parent)

func _yaw_to(from: Vector2, to: Vector2) -> float:
	var d := to - from
	return rad_to_deg(atan2(d.x, d.y))

func _near_route(x: float, z: float, road_pad: float, trail_pad: float) -> bool:
	var k := _k(x, z)
	return _rd[k] < (road_pad if _rt[k] == 1 else trail_pad) or _stub_dist(x, z) < road_pad

func _decor_xf(n: String, t: Transform3D, shadows := false) -> void:
	if not _batches.has(n):
		_batches[n] = {"transforms": [], "shadows": shadows}
	_batches[n].transforms.append(t)

## Scatter with a minimum spacing kept by a hash grid (linear in the count, unlike MapBuilder.scatter's pairwise check).
func _scatter(names: Array, rect: Rect2, count: int, spacing: float, scale_rng: Vector2, avoid: Callable, shadows := false) -> Array[Vector3]:
	var placed: Array[Vector3] = []
	var grid := {}
	var cell := maxf(spacing, 0.5)
	var tries := count * 10
	while placed.size() < count and tries > 0:
		tries -= 1
		var x := rect.position.x + rng.randf() * rect.size.x
		var z := rect.position.y + rng.randf() * rect.size.y
		var ci := floori(x / cell)
		var cj := floori(z / cell)
		var ok := true
		for di in range(-1, 2):
			for dj in range(-1, 2):
				var q: Variant = grid.get(Vector2i(ci + di, cj + dj))
				if q != null and Vector2(x, z).distance_to(q) < spacing:
					ok = false
		if not ok or avoid.call(x, z):
			continue
		grid[Vector2i(ci, cj)] = Vector2(x, z)
		decor(names[rng.randi() % names.size()], Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(scale_rng.x, scale_rng.y), true, shadows)
		placed.append(Vector3(x, 0, z))
	return placed

# ------------------------------------------------------------------------------------------------------------
# edges: mesa cliffs, the two exits

func _edges() -> void:
	boundary(Vector3(-130, -6, -100), Vector3(24.5, -6, -100), 40.0)
	boundary(Vector3(35.5, -6, -100), Vector3(130, -6, -100), 40.0)
	boundary(Vector3(-130, -6, 100), Vector3(130, -6, 100), 40.0)
	boundary(Vector3(-130, -6, -100), Vector3(-130, -6, 4.5), 40.0)
	boundary(Vector3(-130, -6, 15.5), Vector3(-130, -6, 100), 40.0)
	boundary(Vector3(130, -6, -100), Vector3(130, -6, 100), 40.0)
	corridor_rails([Vector2(-144, 10.0), Vector2(-126, 10.0), Vector2(-114, 12.0)], 5.5)
	corridor_rails([Vector2(29.0, -84.0), Vector2(30.0, -96.0), Vector2(30.5, -104.0)], 5.5)
	exit_zone(&"barrens_coil_road", Vector3(-129.0, 0, 10.0), Vector3(2.4, 4.0, 10.0), &"zr_coilwood", &"barrens_road", "the Coilwood")
	exit_zone(&"barrens_bridge_road", Vector3(30.3, 0, -98.6), Vector3(10.0, 4.0, 2.6), &"bridge_of_death", &"barrens_road", "the Bridge of Death")
	# mesa cliffs: faces toward the plain, set into the rising ground; open where the roads cut through
	var x := -134.0
	while x < 136.0:
		if absf(x - 30.0) > 13.0:
			var s := rng.randf_range(1.0, 1.35)
			var z := -93.5 - rng.randf_range(0.0, 2.5)
			decor("zr_cliff_ochre", Vector3(x, height_at(x, z + 3.0) - 1.2, z), rng.randf_range(-8, 8), s, false, true)
		x += 11.0
	var z2 := -96.0
	while z2 < 96.0:
		var s2 := rng.randf_range(1.0, 1.35)
		decor("zr_cliff_ochre", Vector3(124.0 + rng.randf_range(0.0, 2.5), height_at(120.0, z2) - 1.2, z2), -90.0 + rng.randf_range(-8, 8), s2, false, true)
		if absf(z2 - 10.0) > 13.0:
			decor("zr_cliff_ochre", Vector3(-124.0 - rng.randf_range(0.0, 2.5), height_at(-120.0, z2) - 1.2, z2), 90.0 + rng.randf_range(-8, 8), s2, false, true)
		z2 += 11.0
	# the pass north: cliffs either side of the Bridge Road, then the gorge's rim beyond the edge
	for c in [[Vector2(16.0, -90.0), 90.0], [Vector2(15.0, -101.0), 90.0], [Vector2(44.0, -89.0), -90.0], [Vector2(45.5, -100.0), -90.0], [Vector2(16.5, -112.0), 90.0], [Vector2(45.0, -112.0), -90.0], [Vector2(17.5, -123.0), 90.0], [Vector2(44.0, -123.0), -90.0]]:
		var p: Vector2 = c[0]
		decor("zr_cliff_ochre", Vector3(p.x, height_at(p.x, p.y) - 1.4, p.y), c[1], 1.15, false, true)
	# the south edge: outcrops on the slope (the camera never looks back at a cliff's rear)
	var xs := -128.0
	while xs < 128.0:
		var zz := 93.0 + rng.randf_range(-2.0, 4.0)
		decor("zr_rock_ochre_large", Vector3(xs + rng.randf_range(-3, 3), 0, zz), rng.randf() * 360.0, rng.randf_range(1.1, 2.3), true, true)
		if rng.randf() < 0.6:
			decor("zr_rock_ochre_medium", Vector3(xs + rng.randf_range(-4, 4), 0, zz - rng.randf_range(4.0, 7.0)), rng.randf() * 360.0, rng.randf_range(0.8, 1.5), true, true)
		xs += rng.randf_range(7.0, 12.0)
	# markers at the road ends
	signpost_bed(Vector2(-118.0, 16.5), [["The Coilwood", Vector2(-1, 0)], ["Survivors' Camp", Vector2(1, 0.25)]])
	signpost_bed(Vector2(35.5, -86.0), [["The Bridge of Death", Vector2(0, -1)], ["Glass Crossroads", Vector2(-0.3, 1)]])
	for e in [[Vector2(-120.0, 3.5), 90.0], [Vector2(-120.0, 16.5), 90.0], [Vector2(23.5, -88.0), 0.0], [Vector2(36.5, -88.0), 0.0]]:
		_on("zr_glyph_stele", e[0], e[1], 1.0, 1.0, geo)

# ------------------------------------------------------------------------------------------------------------
# the survivors' camp: a ring of ruined walls patched with timber, the waypoint, the bonfire, tents and stores

func _camp() -> void:
	var c := DataZarael.GB_CAMP
	keep_clear(c.x, c.y, CAMP_R + 2.0)
	var gaps := [191.3, 341.6, 243.4]
	var n := 28
	for i in n:
		var a := 360.0 * (i + 0.5) / n
		var open := false
		for g: float in gaps:
			if absf(wrapf(a - g, -180.0, 180.0)) < 11.0:
				open = true
		if open:
			continue
		var ar := deg_to_rad(a)
		var p := c + Vector2(cos(ar), sin(ar)) * CAMP_R
		var yaw := -(a + 90.0)
		if sin(ar) > 0.35:
			# the camera side: a lower timber palisade so the camp stays readable from above
			_on("palisade_fence", p, yaw, 1.08, 1.0, props, 0.15)
			var t := Vector2(-sin(ar), cos(ar)) * 2.2
			boundary(Vector3(p.x - t.x, height_at(p.x, p.y) - 1.0, p.y - t.y), Vector3(p.x + t.x, height_at(p.x, p.y) - 1.0, p.y + t.y), 5.0, 0.6)
		else:
			_on("zr_ruin_wall", p, yaw + (180.0 if i % 3 == 0 else 0.0), 1.0, 2.0, geo, 0.25)
	# gate braziers either side of the three openings
	for g: float in gaps:
		for s: float in [-1.0, 1.0]:
			if g == 243.4 and s > 0.0:
				continue
			var ar := deg_to_rad(g + s * 13.5)
			_brazier(c + Vector2(cos(ar), sin(ar)) * (CAMP_R - 1.6), 2.6)
	# the waypoint on a paved apron (south-west), the bonfire (south-east)
	var tp := Vector2(-47.0, 38.0)
	var ty := height_at(tp.x, tp.y) + 0.05
	apron(tp, ty, 3.2, "terrace_paving")
	teleporter(&"barrens_shrine", Vector3(tp.x, ty, tp.y), &"agdao", &"agdao_shrine", "Agdao", 0.0)
	spawn(&"barrens_shrine", Vector3(tp.x + 3.2, 0, tp.y + 2.0), 30.0, true)
	for a: float in [0.6, 2.4, 4.0]:
		_on("zr_glyph_stele", tp + Vector2(cos(a), sin(a)) * 4.6, rad_to_deg(-a) - 90.0, 0.8, 1.0, geo)
	bonfire("Survivors' Camp", Vector3(-30.0, 0, 37.0), &"barrens_camp", 0.0)
	for b in [Vector2(-26.5, 35.0), Vector2(-33.5, 34.5), Vector2(-27.0, 40.5)]:
		decor("bedroll", Vector3(b.x, 0, b.y), _yaw_to(b, Vector2(-30, 37)), 1.0)
	# Quillan Ashby stands by the road at GB_CAMP + (3.5, -2): kept clear
	keep_clear(c.x + 3.5, c.y - 2.0, 2.5)
	# tents and stores round the inside of the ring
	for t in [[Vector2(-53.0, 24.0), 0.0], [Vector2(-26.0, 18.0), 0.0], [Vector2(-54.0, 37.5), 0.0]]:
		var p: Vector2 = t[0]
		_on("tent_old", p, _yaw_to(p, c), 1.0, 1.8, props, 0.05)
	_on("zr_market_stall_a", Vector2(-37.0, 17.5), 0.0, 1.0, 1.6, props, 0.05)
	_on("weapon_rack", Vector2(-56.5, 30.0), 90.0, 1.0, 0.8, props, 0.02)
	_on("wagon_broken", Vector2(-22.0, 27.0), -70.0, 1.0, 1.6, props, 0.05)
	for p in [Vector2(-33.5, 15.8), Vector2(-41.0, 16.2), Vector2(-24.0, 21.5), Vector2(-50.0, 20.5), Vector2(-56.5, 33.5)]:
		decor("crate" if rng.randf() < 0.55 else "barrel", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 1.0, true, true)
	light(Vector3(c.x, height_at(c.x, c.y) + 5.0, c.y), Color(1.0, 0.7, 0.45), 1.6, 22.0)
	signpost_bed(Vector2(-35.0, 25.0), [["The Coilwood", Vector2(-1, -0.2)], ["Obsidian Engine", Vector2(-0.45, -1)],
		["Glass Crossroads", Vector2(1, -0.35)]])

# ------------------------------------------------------------------------------------------------------------
# the fallen colossus in its bowl, the Kharvenn picking at it

func _colossus() -> void:
	var y := height_at(COLOSSUS.x, COLOSSUS.z) - 0.25
	kit("zr_colossus_fallen", Vector3(COLOSSUS.x, y, COLOSSUS.z), -8.0, COLOSSUS_S, geo)
	keep_clear(COLOSSUS.x, COLOSSUS.z, 24.0)
	for p in [Vector3(30.0, 2.5, -40.0), Vector3(62.0, 3.0, -36.0), Vector3(76.0, 2.0, -44.0)]:
		light(Vector3(p.x, height_at(p.x, p.z) + p.y, p.z), Color(1.0, 1.0, 1.0), 2.6, 14.0)
	# glass bursting out round its chest; chain-spikes the chain-priests drove in to drink the current
	for i in 9:
		var a := TAU * i / 9.0 + 0.3
		var q := Vector2(COLOSSUS.x, COLOSSUS.z) + Vector2(cos(a) * rng.randf_range(16.0, 21.0), sin(a) * rng.randf_range(12.0, 15.0))
		if _near_route(q.x, q.y, 5.0, 3.5):
			continue
		decor("zr_glass_growth", Vector3(q.x, 0, q.y), rng.randf() * 360.0, rng.randf_range(0.9, 1.5), true, true)
	for i in 6:
		var a := TAU * i / 6.0 + 0.9
		var q := Vector2(COLOSSUS.x, COLOSSUS.z) + Vector2(cos(a) * 18.5, sin(a) * 13.0)
		if _near_route(q.x, q.y, 5.0, 3.5):
			continue
		_on("zr_chain_spike", q, rng.randf() * 360.0, 1.2, 0.7, props, 0.12)
	# the chain-priests' work camp north of it
	for t in [[Vector2(36.0, -64.0), 0.0], [Vector2(48.0, -66.0), 0.0]]:
		var p: Vector2 = t[0]
		_on("zr_kharvenn_tent", p, _yaw_to(p, Vector2(42.0, -60.0)), 1.0, 2.1, props, 0.08)
	_on("zr_chain_rack", Vector2(42.0, -68.5), 0.0, 1.0, 1.6, props, 0.05)
	_brazier(Vector2(38.5, -58.0), 2.8, true)
	_brazier(Vector2(46.0, -58.5), 2.6)
	signpost_bed(Vector2(4.5, 14.5), [["Survivors' Camp", Vector2(-1, 0.6)], ["The Bridge of Death", Vector2(0.4, -1)],
		["The Fallen Colossus", Vector2(1, -0.9)], ["Veinworks", Vector2(1, 0.35)]])

# ------------------------------------------------------------------------------------------------------------
# Blackwire fissures and their glass

func _fissures() -> void:
	var lit := 0
	for f in FISSURES:
		var total := DataIsland.polyline_length(f)
		var along := 4.0
		while along < total - 2.0:
			var p := DataIsland.point_at(f, along) + Vector2(rng.randf_range(-2.2, 2.2), rng.randf_range(-2.2, 2.2))
			along += rng.randf_range(5.0, 9.0)
			if _near_route(p.x, p.y, 6.0, 4.0) or not is_clear(p.x, p.y, 1.0):
				continue
			var s := rng.randf_range(0.6, 1.4)
			decor("zr_glass_growth", Vector3(p.x, 0, p.y), rng.randf() * 360.0, s, true, s > 1.0)
			if _route_dist(p.x, p.y) < 12.0:
				blocker(Vector3(p.x, height_at(p.x, p.y) + 1.2, p.y), Vector3(2.0 * s, 2.4, 2.0 * s))
			if s > 1.25 and lit < 7 and rng.randf() < 0.5:
				lit += 1
				light(Vector3(p.x, height_at(p.x, p.y) + 1.6, p.y), Color(1.0, 1.0, 1.0), 1.8, 10.0)

# ------------------------------------------------------------------------------------------------------------
# the dead relay line toward Agdao

func _dead_relays() -> void:
	for d in DEAD_PYLONS:
		var p := Vector2(d[0], d[1])
		if d[2]:
			# toppled: the pylon lies on its side, its plinth torn out of the ground
			var yaw := rng.randf_range(0.0, 360.0)
			var b := Basis(Vector3.UP, deg_to_rad(yaw)) * Basis(Vector3(1, 0, 0), deg_to_rad(90.0))
			var n := kit("zr_relay_pylon", Vector3(p.x, height_at(p.x, p.y) + 0.75, p.y), 0.0, 1.0, geo)
			n.transform = Transform3D(b, Vector3(p.x, height_at(p.x, p.y) + 0.75, p.y))
			decor("rubble_pile", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 1.2, true, true)
		else:
			_on("zr_relay_pylon", p, rng.randf() * 360.0, 1.0, 1.6, geo, 0.62)
			decor("zr_glass_growth", Vector3(p.x + 3.0, 0, p.y + 1.5), rng.randf() * 360.0, 0.7, true, false)
		keep_clear(p.x, p.y, 5.0)

# ------------------------------------------------------------------------------------------------------------
# the two Vault gates

func _gates() -> void:
	for gid in DataDungeons.gates_on(MAP):
		var gs: Dictionary = DataDungeons.get_def(gid).surface
		var p: Vector2 = gs.pos
		var yaw: float = gs.yaw
		dungeon_gate(gid, p, yaw)
		keep_clear(p.x, p.y, 9.0)
		var fwd := Vector2(sin(deg_to_rad(yaw)), cos(deg_to_rad(yaw)))
		var side := Vector2(fwd.y, -fwd.x)
		if gid == &"veinworks":
			# the Veinworks: a cleft in an ochre outcrop, rock heaped behind and beside it
			for s: float in [-1.0, 1.0]:
				var q := p - fwd * 4.5 + side * s * 7.0
				if q.y > p.y + 2.0:
					q = p - fwd * 7.5 + side * s * 3.0
				if not _near_route(q.x, q.y, 5.0, 3.5) and q.y < p.y + 2.0:
					_on("zr_rock_ochre_large", q, yaw + s * 35.0, 1.3, 3.0, geo, 0.3)
			var back := p - fwd * 10.0
			decor("zr_cliff_ochre", Vector3(back.x, _foot(back, 4.0) - 1.0, back.y), yaw, 1.2, false, true)
		else:
			# the Obsidian Engine: black glass shoulders out of the ground round its doors
			for s: float in [-1.0, 1.0]:
				var q := p + side * s * 7.5 - fwd * 1.0
				if not _near_route(q.x, q.y, 5.0, 3.5):
					decor("zr_glass_growth", Vector3(q.x, 0, q.y), rng.randf() * 360.0, 1.5, true, true)
					blocker(Vector3(q.x, height_at(q.x, q.y) + 1.2, q.y), Vector3(2.8, 2.4, 2.8))
				var r := p + side * s * 9.5 + fwd * 3.0
				if not _near_route(r.x, r.y, 5.0, 3.5) and r.y < p.y + 3.0:
					_on("zr_rock_ochre_medium", r, rng.randf() * 360.0, 1.2, 1.2, geo, 0.2)

# ------------------------------------------------------------------------------------------------------------
# outcrops on the plain

## Ruins of the Wirewright works the Blackwire broke: wall stubs, columns, a toppled stele (dressing, not cover walls).
const RUINS := [[Vector2(-84, 30), "zr_ruin_wall"], [Vector2(-78, 34), "zr_ruin_column"], [Vector2(-20, 4), "zr_ruin_column"],
	[Vector2(16, 0), "zr_ruin_wall"], [Vector2(-24, 56), "zr_ruin_wall"], [Vector2(-30, 60), "zr_ruin_column"], [Vector2(40, 8), "zr_ruin_wall"],
	[Vector2(68, 14), "zr_ruin_column"], [Vector2(-96, -52), "zr_ruin_wall"], [Vector2(-54, -78), "zr_ruin_column"], [Vector2(8, -62), "zr_ruin_wall"],
	[Vector2(88, -6), "zr_ruin_wall"], [Vector2(-8, 34), "zr_glyph_stele"], [Vector2(56, 22), "zr_glyph_stele"], [Vector2(-104, 4), "zr_glyph_stele"],
	[Vector2(30, -40), "zr_glyph_stele"]]

func _outcrops() -> void:
	for rr in RUINS:
		var rp: Vector2 = rr[0]
		var nm: String = rr[1]
		if _near_route(rp.x, rp.y, 6.0, 4.0) or not is_clear(rp.x, rp.y, 2.0):
			continue
		_on(nm, rp, rng.randf_range(-30.0, 30.0) + (180.0 if rng.randf() < 0.3 else 0.0), 1.0, 1.4 if nm == "zr_ruin_wall" else 0.8, geo, 0.3)
		decor("rubble_pile", Vector3(rp.x + rng.randf_range(-2.5, 2.5), 0, rp.y + rng.randf_range(1.5, 3.0)), rng.randf() * 360.0, rng.randf_range(0.7, 1.1), true, true)
		keep_clear(rp.x, rp.y, 3.5)
	# glass fields: clusters where the Blackwire welled up away from the fissures
	for gf: Vector2 in [Vector2(-62, 64), Vector2(96, 66), Vector2(-108, -16), Vector2(-20, -50), Vector2(104, -82)]:
		for k in 6:
			var q := gf + Vector2(rng.randf_range(-7, 7), rng.randf_range(-6, 6))
			if _near_route(q.x, q.y, 6.0, 4.0) or not is_clear(q.x, q.y, 1.0):
				continue
			decor("zr_glass_growth", Vector3(q.x, 0, q.y), rng.randf() * 360.0, rng.randf_range(0.6, 1.5), true, true)
		light(Vector3(gf.x, height_at(gf.x, gf.y) + 1.6, gf.y), Color(1.0, 1.0, 1.0), 1.6, 11.0)
	var spots := [Vector2(-100, 30), Vector2(-76, 72), Vector2(-44, 86), Vector2(60, 84), Vector2(-112, 70), Vector2(112, 30),
		Vector2(-36, -36), Vector2(84, -60), Vector2(-120, -84), Vector2(116, -88), Vector2(-60, -90), Vector2(-108, -66), Vector2(-30, -60), Vector2(-60, 60), Vector2(10, 74),
		Vector2(40, 80), Vector2(76, 70), Vector2(104, 50), Vector2(108, -40), Vector2(70, -80), Vector2(-16, -84), Vector2(-84, -8),
		Vector2(24, 30), Vector2(-4, -54), Vector2(94, 22)]
	for p: Vector2 in spots:
		if _near_route(p.x, p.y, 8.0, 6.0) or not is_clear(p.x, p.y, 4.0):
			continue
		_on("zr_rock_ochre_large", p, rng.randf() * 360.0, rng.randf_range(1.0, 1.7), 3.2, geo, 0.3)
		for k in 3:
			var q := p + Vector2(rng.randf_range(-7, 7), rng.randf_range(-7, 7))
			if not _near_route(q.x, q.y, 6.0, 4.0):
				decor("zr_rock_ochre_medium", Vector3(q.x, 0, q.y), rng.randf() * 360.0, rng.randf_range(0.6, 1.1), true, true)
		keep_clear(p.x, p.y, 6.0)

# ------------------------------------------------------------------------------------------------------------
# monsters (the Spawner reads these; no monster is instantiated here)

func _encounters() -> void:
	for c in CAMPS:
		var p: Vector2 = c[1]
		var m := enemy_zone(c[0], Vector3(p.x, 0, p.y), c[2], c[3], c[4], c[6], true)
		m.set_meta(&"levels", c[5])
		keep_clear(p.x, p.y, 4.0)
		decor("bones_scatter", Vector3(p.x + 1.4, 0, p.y + 1.0), rng.randf() * 360.0, 0.9)

# ------------------------------------------------------------------------------------------------------------
# dry scrub

func _scrub() -> void:
	var bounds := Rect2(-142, -114, 284, 228)
	var lite := 0.5 if Perf.lite else 1.0
	var free := func(x: float, z: float) -> bool:
		return _near_route(x, z, 4.5, 3.0) or not is_clear(x, z, 1.0)
	_scatter(["zr_agave", "zr_agave", "grass_clump"], bounds, int(360 * lite), 3.4, Vector2(0.6, 1.1), free)
	_scatter(["tree_dead_a", "tree_dead_b"], bounds, 34, 16.0, Vector2(0.8, 1.1),
		func(x: float, z: float) -> bool: return _route_dist(x, z) < 9.0 or not is_clear(x, z, 4.0), true)
	_scatter(["zr_rock_ochre_medium", "rock_small", "rubble_pile"], bounds, 220, 4.0, Vector2(0.5, 1.0), free, true)
	var placed := 0
	var tries := 0
	while placed < int(700 * lite) and tries < 5000:
		tries += 1
		var x := -140.0 + rng.randf() * 280.0
		var z := -112.0 + rng.randf() * 224.0
		if _near_route(x, z, 3.2, 2.0) or _fd[_k(x, z)] < 3.0 or not is_clear(x, z, 0.0):
			continue
		decor("grass_clump", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.6, 1.1))
		placed += 1

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): scraps of salvage and labour where people work — round the survivors' camp, at the
# fallen colossus being picked over, and at the two Vault mouths, which differ: the Obsidian Engine keeps a service
# entrance (a fire basket, stacked stores), the Veinworks an abandoned extraction (spoil, tipped barrels, a shovel).
# Bare shattered rock (no moss, no grass): the barrens stay barren.

func _clear_here(x: float, z: float, r: float) -> bool:
	var p := Vector2(x, z)
	for c in CAMPS:
		if p.distance_to(c[1]) < float(c[2]) + r + 3.0:
			return false
	return not _near_route(x, z, r + 3.0, r + 2.0) and is_clear(x, z, r * 0.5)

func _map_design() -> void:
	clear_fn = _clear_here
	var camp := Vector3(-40.0, 0, 30.0)
	for c in [["salvage", Vector3(-58.0, 0, 30.0)], ["tool_corner", Vector3(-40.0, 0, 50.0)], ["supply_corner", Vector3(-24.0, 0, 42.0)]]:
		place_near(c[0], c[1], camp, 15.0, 24.0, rng.randf() * 360.0, {"check": false})
	place_near("excavation", COLOSSUS + Vector3(-16.0, 0, 14.0), COLOSSUS, 18.0, 28.0, 30.0)
	place_near("salvage", COLOSSUS + Vector3(18.0, 0, 10.0), COLOSSUS, 18.0, 28.0, -40.0)
	var ob: Vector2 = DataDungeons.get_def(&"obsidian_engine").surface.pos
	var basket := Vector3(ob.x + 6.5, 0, ob.y + 7.0)
	if not touches_solid(Vector3(basket.x, height_at(basket.x, basket.z), basket.z), 1.0):
		kit("kd_fire_basket", basket, 0.0, 1.0, props, true)
		flame(Vector3(basket.x, height_at(basket.x, basket.z) + 0.45, basket.z), 0.9)
		light(Vector3(basket.x, height_at(basket.x, basket.z) + 1.4, basket.z), FIRE, 2.0, 8.0, false, true)
	place_near("cargo_stack", Vector3(ob.x - 7.0, 0, ob.y + 7.0), Vector3(ob.x, 0, ob.y), 6.0, 12.0, 160.0)
	var vn: Vector2 = DataDungeons.get_def(&"veinworks").surface.pos
	place_near("excavation", Vector3(vn.x - 7.0, 0, vn.y - 5.0), Vector3(vn.x, 0, vn.y), 6.0, 12.0, 250.0)
	for c in [Vector3(vn.x - 5.0, 0, vn.y + 6.5), Vector3(vn.x + 6.0, 0, vn.y - 7.0)]:
		if not touches_solid(Vector3(c.x, height_at(c.x, c.z), c.z), 0.8):
			kit("kd_barrel", c + Vector3(0, 0.45, 0), rng.randf() * 360.0, 0.9, deco, true).rotation.z = deg_to_rad(84.0)
	for q in [[Vector3(-80.0, 0, 20.0), "kd_shore_rocks_a"], [Vector3(-10.0, 0, 30.0), "kd_shore_rocks_c"], [Vector3(30.0, 0, -10.0), "kd_shore_rocks_b"],
			[Vector3(-60.0, 0, -40.0), "kd_shore_rocks_c"], [Vector3(60.0, 0, 20.0), "kd_shore_rocks_a"]]:
		var p: Vector3 = q[0]
		if _clear_here(p.x, p.z, 3.5) and not touches_solid(Vector3(p.x, height_at(p.x, p.z), p.z), 3.0):
			kit(q[1], p - Vector3(0, 0.4, 0), rng.randf() * 360.0, rng.randf_range(0.8, 1.1), props, true)
