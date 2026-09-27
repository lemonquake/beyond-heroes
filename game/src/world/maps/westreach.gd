extends MapBuilder
## MAP — Westreach, the roads below Malasugue's South Gate (outdoor, levels 1–4; provisional names, LORE §6b).
##
## A district on the island's south-west shoulder, laid out around the concept's coast circuit so a hero can choose a
## journey and come home by another road:
##   South Gate road -> Mill Road -> Old Mill Crossroads -> Mill Lane -> Lantern Fields -> Coast Road -> Tideglass Cove
##   -> Cove Steps -> back up to the gate. The Field Road is a shorter farm track between the gate and the fields; the
##   Forest Road climbs north from the mill into the Ruined Forest; the Lake Shore Road runs east over the mended
##   washout to Olivar, and the Fen Road leaves the fields east over the Fen Bridge for Wyman Outpost (bh-007). The road
##   polylines are DataIsland.ROADS: terrain beds, signposts, the atlas and the directions all read the same data.
## The land falls from the town plateau (0 m) to the millstream (-3 m), the terraced fields (-4 m) and the clifftop
## coast road, then down switchbacks to the cove beach (-12.5 m) at sea level (-14 m).

const MAP := &"westreach"
const W := 310
const D := 230
const X0 := -225.0
const Z0 := -62.0
const TOWN := Vector2(-112, -12)          # Malasugue's centre in this map's frame (the town is its own map)
const TOWN_FENCE := 40.0
const GATE := Vector2(-112, 40)
const MILL := Vector2(0, 0)
const FIELDS := Vector2(35, 110)
const COVE := Vector2(-178, 92)
const CAVE := Vector2(-191, 70)
const SHRINE := Vector2(-168, 86)
const MILL_HOUSE := Vector2(4, -21)
const BRIDGE := Vector2(20, 2)
const FEN_BRIDGE := Vector2(59, 97)
const EAST_EDGE := 81.0
const SEA_Y := -14.0
const PIER_X := -172.0
const STREAM := [Vector2(74, -66), Vector2(46, -44), Vector2(24, -32), Vector2(16, -22), Vector2(15.5, -10), Vector2(19, 2),
	Vector2(26, 20), Vector2(42, 48), Vector2(54, 78), Vector2(62, 108), Vector2(66, 128)]
## The land (clockwise); everything outside is sea. Shared with tools/ui_art/salmonan_atlas.py.
const LAND := [Vector2(-212, -90), Vector2(-203, -60), Vector2(-201, -30), Vector2(-205, 0), Vector2(-200, 40), Vector2(-199, 62),
	Vector2(-203, 78), Vector2(-207, 94), Vector2(-200, 104), Vector2(-189, 108), Vector2(-176, 111), Vector2(-163, 110),
	Vector2(-153, 114), Vector2(-146, 126), Vector2(-130, 134), Vector2(-100, 138), Vector2(-70, 140), Vector2(-40, 142),
	Vector2(-10, 140), Vector2(20, 136), Vector2(50, 134), Vector2(80, 138), Vector2(120, 150), Vector2(120, -100), Vector2(-212, -100)]
## Road-bed elevation anchors (x, z, height); inverse-distance blended into a smooth landform.
const ANCHORS := [
	Vector3(-112, 40, 0.0), Vector3(-112, 20, 0.3), Vector3(-80, 50, -0.4), Vector3(-44, 30, -1.4), Vector3(0, 0, -3.0),
	Vector3(-54, -51, 1.4), Vector3(-20, -30, -0.4), Vector3(40, -20, -2.4), Vector3(62, -52, 0.6), Vector3(35, 110, -4.0),
	Vector3(4, 66, -3.2), Vector3(-60, 78, -2.0), Vector3(-98, 124, -4.4), Vector3(-42, 126, -4.4), Vector3(12, 116, -4.4),
	Vector3(-146, 110, -9.0), Vector3(-124, 118, -5.6), Vector3(-178, 92, -12.5), Vector3(-196, 92, -12.2), Vector3(-186, 74, -11.8),
	Vector3(-152, 60, -4.6), Vector3(-140, 69, -6.6), Vector3(-152, 79, -9.0), Vector3(-166, 86, -11.2), Vector3(-140, 54, -2.8),
	Vector3(-190, 40, -1.0), Vector3(-160, 20, 0.5), Vector3(58, 96, -4.6), Vector3(-30, 56, -1.8), Vector3(66, 20, -2.6),
	Vector3(78, -9, -2.2), Vector3(76, 95, -3.8), Vector3(76, 40, -2.8),
]
## Crop plots (centre x, z, half size x, z) and flat pads kept level for buildings (x, z, radius).
const PLOTS := [[-2.0, 66.0, 12.0, 7.0], [-30.0, 100.0, 11.0, 6.0], [-60.0, 100.0, 11.0, 6.5], [-5.0, 106.0, 10.0, 4.5]]
const PADS := [[4.0, -21.0, 7.5], [46.0, 94.0, 6.5], [20.0, 128.0, 6.0], [-150.0, 97.0, 5.5], [-30.0, 52.0, 6.0],
	[-168.0, 86.0, 4.5], [0.0, 0.0, 8.0], [-112.0, 50.0, 6.0]]
## The short stretch from the gate arch down to the fork (not a separate route edge: the South Gate link lands on it).
const GATE_APPROACH := [Vector2(-112, 26), Vector2(-112, 40)]
const WOLVES := Vector2(-70, 112)
const GOBLIN_CAMP := Vector2(-30, 52)
const FIELD_RAID := Vector2(44, 84)
const SMUGGLERS := Vector2(-189, 77)
const FOREST_WATCH := Vector2(-44, -40)

var _w := W + 1
var _h := PackedFloat32Array()      # final ground height per lattice vertex
var _t := PackedFloat32Array()      # road-bed elevation
var _rd := PackedFloat32Array()     # distance to the nearest road/trail centre line
var _rt := PackedByteArray()        # 1 road, 2 trail (nearest)
var _ds := PackedFloat32Array()     # distance to the millstream
var _sea := PackedFloat32Array()    # signed distance to the coast (+ = sea)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.02, 0.035, 0.075), "sky_horizon": Color(0.13, 0.15, 0.24),
		"ambient": Color(0.3, 0.35, 0.48), "ambient_energy": 0.8,
		"fog": Color(0.13, 0.16, 0.24), "fog_density": 0.007, "fog_height": -8.0, "fog_height_density": 0.05,
		"sun": Color(0.56, 0.66, 0.95), "sun_energy": 0.6, "sun_rot": Vector3(-46, -35, 0), "glow": 0.8,
		"exposure": 1.12, "contrast": 1.06, "saturation": 0.92,
	})
	_prepare()
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), _height, _splat,
		{"grass": "grass", "moss": "forest_floor", "dirt": "sand_path", "path": "cobblestone", "rock": "rock_cliff"}, Color(0.92, 0.95, 0.9))
	_sea_and_stream()
	_edges()
	_town_wall()
	_crossroads()
	_mill()
	_fields()
	_coast()
	_cove()
	_roadside()
	_encounters()
	_herbs()
	_greenery()
	spawn(&"start", Vector3(GATE.x, 0, GATE.y + 4.0), 0.0, true)
	spawn(&"town_gate", Vector3(GATE.x, 0, GATE.y + 4.0), 0.0, true)
	spawn(&"forest_road", Vector3(-49, 0, -45), 140.0, true)
	spawn(&"cove_shrine", Vector3(SHRINE.x + 3.2, 0, SHRINE.y + 1.2), 90.0, true)
	spawn(&"olivar_road", Vector3(70.5, 0, -9.6), -90.0, true)
	spawn(&"fen_road", Vector3(70.5, 0, 95.4), -90.0, true)
	set_bounds(AABB(Vector3(-205, -20, -58), Vector3(286, 40, 196)))
	view("overview", Vector3(-70, -4, 40), 0.0, 62.0, 250.0, 50.0)
	view("topdown", Vector3(-75, -4, 45), 0.0, 89.5, 260.0, 55.0)
	view("gate", Vector3(GATE.x + 2, 0, GATE.y + 8), 0.0, 48.0, 34.0)
	view("crossroads", Vector3(0, -3, 2), -10.0, 46.0, 34.0)
	view("mill", Vector3(8, -3, -14), 20.0, 40.0, 24.0)
	view("fields", Vector3(20, -4, 92), 0.0, 50.0, 48.0)
	view("coast", Vector3(-80, -4, 118), 0.0, 45.0, 44.0)
	view("cove", Vector3(-176, -12, 94), 0.0, 48.0, 40.0)
	view("steps", Vector3(-146, -6, 66), 0.0, 52.0, 44.0)

# ------------------------------------------------------------------------------------------------------------
# landform (precomputed on the terrain lattice; ground() and the mesh sample the same heights)

func _i(ix: int, iz: int) -> int:
	return iz * _w + ix

func _prepare() -> void:
	var n := _w * (D + 1)
	for arr in [_h, _t, _rd, _ds, _sea]:
		arr.resize(n)
	_rt.resize(n)
	_rd.fill(99.0)
	_ds.fill(99.0)
	_sea.fill(99.0)
	for r in DataIsland.roads_on(MAP):
		_raster_line(r.points, _rd, 16.0, _rt, 1 if r.type == "road" else 2)
	_raster_line(GATE_APPROACH, _rd, 16.0, _rt, 1)
	_raster_line(STREAM, _ds, 12.0)
	# coast: distance to the land outline, signed by inside/outside
	var land := PackedVector2Array(LAND)
	var outline := LAND.duplicate()
	outline.append(LAND[0])
	_raster_line(outline, _sea, 30.0)
	for iz in D + 1:
		for ix in _w:
			var k := _i(ix, iz)
			var p := Vector2(X0 + ix, Z0 + iz)
			if not Geometry2D.is_point_in_polygon(p, land):
				_sea[k] = minf(_sea[k], 30.0)
			else:
				_sea[k] = -minf(_sea[k], 30.0)
			_t[k] = _bed(p)
	for iz in D + 1:
		for ix in _w:
			var k := _i(ix, iz)
			_h[k] = _shape(Vector2(X0 + ix, Z0 + iz), k)

func _raster_line(pts: Array, field: PackedFloat32Array, reach: float, types := PackedByteArray(), type := 0) -> void:
	for s in pts.size() - 1:
		var a: Vector2 = pts[s]
		var b: Vector2 = pts[s + 1]
		var x0 := clampi(int(floor(minf(a.x, b.x) - reach - X0)), 0, W)
		var x1 := clampi(int(ceil(maxf(a.x, b.x) + reach - X0)), 0, W)
		var z0 := clampi(int(floor(minf(a.y, b.y) - reach - Z0)), 0, D)
		var z1 := clampi(int(ceil(maxf(a.y, b.y) + reach - Z0)), 0, D)
		for iz in range(z0, z1 + 1):
			for ix in range(x0, x1 + 1):
				var d := _seg_dist(Vector2(X0 + ix, Z0 + iz), a, b)
				var k := _i(ix, iz)
				if d < field[k]:
					field[k] = d
					if type > 0:
						types[k] = type

static func _seg_dist(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var l2 := ab.length_squared()
	if l2 < 0.0001:
		return p.distance_to(a)
	return p.distance_to(a + ab * clampf((p - a).dot(ab) / l2, 0.0, 1.0))

func _bed(p: Vector2) -> float:
	var num := 0.0
	var den := 0.0
	for a: Vector3 in ANCHORS:
		var d2 := (p.x - a.x) * (p.x - a.x) + (p.y - a.y) * (p.y - a.y)
		var w := 1.0 / (d2 + 60.0)
		num += a.z * w
		den += w
	return num / den

func _noise(x: float, z: float) -> float:
	return sin(x * 0.11) * cos(z * 0.09) * 0.7 + sin(x * 0.043 + z * 0.061) * 1.0 + cos(z * 0.17 - x * 0.07) * 0.3

func _shape(p: Vector2, k: int) -> float:
	var t := _t[k]
	var h := t + _noise(p.x, p.y) * 0.9
	# rolling rise toward the forest in the north and the headland west of the cove
	h += 5.0 * smoothstep(-20.0, -58.0, p.y) * (1.0 - smoothstep(-70.0, -30.0, p.x) * 0.5)
	h += 6.0 * (1.0 - smoothstep(6.0, 22.0, p.distance_to(Vector2(-204, 64)))) * smoothstep(-188.0, -198.0, p.x)
	# the town plateau: level ground behind the palisade
	var dt := p.distance_to(TOWN)
	h = lerpf(h, 0.4 + _noise(p.x, p.y) * 0.15, 1.0 - smoothstep(TOWN_FENCE + 3.0, TOWN_FENCE + 9.0, dt))
	# terraced crop plots
	for pl in PLOTS:
		var q := Vector2(absf(p.x - pl[0]), absf(p.y - pl[1]))
		var inside := 1.0 - smoothstep(0.0, 3.0, maxf(q.x - pl[2], q.y - pl[3]))
		h = lerpf(h, t, inside)
	for pd in PADS:
		h = lerpf(h, t, 1.0 - smoothstep(pd[2] * 0.7, pd[2] + 2.0, p.distance_to(Vector2(pd[0], pd[1]))))
	# road beds: level with the smooth landform, wider for roads than for trails
	var half := 3.2 if _rt[k] == 1 else 1.8
	h = lerpf(t, h, smoothstep(half, half + 4.0, _rd[k]))
	# the millstream cuts its channel (the mill bridge spans it)
	h -= 2.6 * (1.0 - smoothstep(2.2, 5.5, _ds[k]))
	# the sea: sheer cliffs on the south coast, a shelving beach in the cove
	var beach := 1.0 - smoothstep(22.0, 40.0, p.distance_to(Vector2(-180, 108)))
	var s := _sea[k]
	var cliff := smoothstep(-1.5, 5.0, s)
	var shelf := smoothstep(-3.0, 16.0, s)
	h = lerpf(h, -19.0, lerpf(cliff, shelf, beach))
	return h

func _height(x: float, z: float) -> float:
	var fx := clampf(x - X0, 0.0, W - 0.001)
	var fz := clampf(z - Z0, 0.0, D - 0.001)
	var ix := int(fx)
	var iz := int(fz)
	var tx := fx - ix
	var tz := fz - iz
	var a := lerpf(_h[_i(ix, iz)], _h[_i(ix + 1, iz)], tx)
	var b := lerpf(_h[_i(ix, iz + 1)], _h[_i(ix + 1, iz + 1)], tx)
	return lerpf(a, b, tz)

func _k(x: float, z: float) -> int:
	return _i(clampi(roundi(x - X0), 0, W), clampi(roundi(z - Z0), 0, D))

func _splat(x: float, z: float) -> Color:
	var k := _k(x, z)
	var p := Vector2(x, z)
	var n := sin(x * 0.37 + z * 0.23) * 0.5 + 0.5
	var road := (1.0 - smoothstep(2.3, 3.4, _rd[k])) if _rt[k] == 1 else 0.0
	var trail := (1.0 - smoothstep(1.1, 2.1, _rd[k])) if _rt[k] == 2 else 0.0
	var plaza := maxf(1.0 - smoothstep(5.0, 6.5, p.length()), 1.0 - smoothstep(4.0, 5.5, p.distance_to(Vector2(-112, 49))))
	var soil := 0.0
	for pl in PLOTS:
		var q := Vector2(absf(x - pl[0]), absf(z - pl[1]))
		if q.x < pl[2] and q.y < pl[3]:
			soil = 1.0 if sin((z - pl[1]) * 2.25) > 0.0 else -1.0
	var sand := smoothstep(-2.0, 3.0, _sea[k]) + (1.0 - smoothstep(24.0, 34.0, p.distance_to(Vector2(-182, 100))))
	var bank := 1.0 - smoothstep(4.0, 7.0, _ds[k])
	var wood := smoothstep(-15.0, -45.0, z) * 0.7 + n * 0.3
	road *= 1.0 - clampf(sand, 0.0, 1.0)
	var r := clampf(maxf(maxf(trail, sand), bank * 0.6) + n * 0.08 + (0.8 if soil < 0.0 else 0.0), 0.0, 1.0)
	var g := clampf(maxf(1.0 if soil > 0.0 else 0.0, wood * (1.0 - road)), 0.0, 1.0) * (1.0 - trail)
	var b := clampf(maxf(road, plaza), 0.0, 1.0)
	return Color(r * (1.0 - b), g * (1.0 - b), b)

func _seg_on(pts: Array, p: Vector2) -> float:
	var d := INF
	for i in pts.size() - 1:
		d = minf(d, _seg_dist(p, pts[i], pts[i + 1]))
	return d

## Height of the road bed under a point (props and signs stand on this, not on the noisy verge).
func bed(x: float, z: float) -> float:
	return _t[_k(x, z)]

# ------------------------------------------------------------------------------------------------------------
# water, edges

func _sea_and_stream() -> void:
	water(Rect2(-330, -120, 520, 330), SEA_Y, Color(0.1, 0.36, 0.42), Color(0.015, 0.06, 0.09), 0.45, 3.5, 0.5)
	mist(Rect2(-330, 120, 520, 120), SEA_Y + 1.6, Color(0.24, 0.3, 0.42), 0.45)
	mist(Rect2(-330, -120, 110, 330), SEA_Y + 1.6, Color(0.24, 0.3, 0.42), 0.45)
	_stream_ribbon()
	# the stream falls off the clifftop into the sea
	var fall := VFXLib.particles(Color(0.7, 0.85, 0.95, 0.35), 30, 1.6, false, 0.6, 1.4, 20.0, Vector3(0, -5.0, 1.0), 1.5, false)
	fall.position = Vector3(66, -6.0, 131)
	deco.add_child(fall)

## A water ribbon along the millstream, its surface following the landform a little below the banks.
func _stream_ribbon() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts: Array = []
	for i in STREAM.size() - 1:
		var a: Vector2 = STREAM[i]
		var b: Vector2 = STREAM[i + 1]
		var n := int(ceil(a.distance_to(b) / 2.0))
		for j in n:
			pts.append(a.lerp(b, float(j) / n))
	pts.append(STREAM[STREAM.size() - 1])
	var verts := 0
	for i in pts.size():
		var p: Vector2 = pts[i]
		var dir: Vector2 = ((pts[mini(i + 1, pts.size() - 1)] as Vector2) - (pts[maxi(i - 1, 0)] as Vector2)).normalized()
		var side := Vector2(-dir.y, dir.x) * 3.2
		var y := _t[_k(p.x, p.y)] - 1.35
		if _sea[_k(p.x, p.y)] > -2.0:
			y = SEA_Y + 0.05
		st.set_uv(Vector2(0, i * 0.5))
		st.add_vertex(Vector3(p.x + side.x, y, p.y + side.y))
		st.set_uv(Vector2(1, i * 0.5))
		st.add_vertex(Vector3(p.x - side.x, y, p.y - side.y))
		if i > 0:
			var a := verts - 2
			st.add_index(a)
			st.add_index(a + 1)
			st.add_index(a + 2)
			st.add_index(a + 1)
			st.add_index(a + 3)
			st.add_index(a + 2)
		verts += 2
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.name = "Millstream"
	mi.mesh = st.commit()
	if Perf.lite:
		mi.material_override = WorldShaders.water_lite_material(Color(0.1, 0.3, 0.33), Color(0.02, 0.06, 0.08), 0.3)
	else:
		mi.material_override = WorldShaders.water_material(Color(0.1, 0.3, 0.33), Color(0.02, 0.06, 0.08), 0.3, 1.6)
		mi.material_override.set_shader_parameter("foam", 0.18)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.add_to_group(&"water")
	deco.add_child(mi)

func _edges() -> void:
	# the coast: a guard line just inside the cliff edge (on the beach it runs along the waterline)
	for i in LAND.size() - 3:
		var a: Vector2 = LAND[i]
		var b: Vector2 = LAND[i + 1]
		var mid := (a + b) * 0.5
		var inward := Vector2(b.y - a.y, a.x - b.x).normalized() * -1.2
		var beach := mid.distance_to(Vector2(-180, 108)) < 34.0
		var off := inward * (0.2 if beach else 1.0)
		var pa := a + off
		var pb := b + off
		if a.x < PIER_X and b.x > PIER_X:
			# the pier runs out through the waterline: leave it open and rail its sides
			var t := (PIER_X - a.x) / (b.x - a.x)
			var cut := pa.lerp(pb, t)
			var gap := (pb - pa).normalized() * 2.3
			boundary(Vector3(pa.x, -20.0, pa.y), Vector3(cut.x - gap.x, -20.0, cut.y - gap.y), 34.0)
			boundary(Vector3(cut.x + gap.x, -20.0, cut.y + gap.y), Vector3(pb.x, -20.0, pb.y), 34.0)
			for sx: float in [-2.3, 2.3]:
				boundary(Vector3(PIER_X + sx, -20.0, cut.y - 1.0), Vector3(PIER_X + sx, -20.0, 119.2), 34.0, 0.4)
			boundary(Vector3(PIER_X - 2.3, -20.0, 119.2), Vector3(PIER_X + 2.3, -20.0, 119.2), 34.0, 0.4)
			continue
		boundary(Vector3(pa.x, -20.0, pa.y), Vector3(pb.x, -20.0, pb.y), 34.0)
	# map edges inland: the northern treeline, the lake-side east
	boundary(Vector3(-200, -6, -57), Vector3(-58, -6, -57), 26.0)
	boundary(Vector3(-50, -6, -57), Vector3(EAST_EDGE, -6, -57), 26.0)
	boundary(Vector3(EAST_EDGE, -8, -57), Vector3(EAST_EDGE, -8, -13.6), 26.0)
	boundary(Vector3(EAST_EDGE, -8, -4.4), Vector3(EAST_EDGE, -8, 90.6), 26.0)
	boundary(Vector3(EAST_EDGE, -8, 99.4), Vector3(EAST_EDGE, -8, 136), 26.0)
	# the millstream's lower gorge: rails along both banks, open only where the mill bridge crosses
	var total := DataIsland.polyline_length(STREAM)
	for sgn: float in [-1.0, 1.0]:
		var prev := Vector2.INF
		var along := 0.0
		while along <= total:
			var c := DataIsland.point_at(STREAM, along)
			var ahead := DataIsland.point_at(STREAM, minf(total, along + 1.0))
			var back := DataIsland.point_at(STREAM, maxf(0.0, along - 1.0))
			var dir := (ahead - back).normalized()
			var q := c + Vector2(-dir.y, dir.x) * 4.4 * sgn
			var open := c.distance_to(BRIDGE) < 4.6 or c.distance_to(FEN_BRIDGE) < 4.6 or c.y < -26.0
			if prev != Vector2.INF and not open:
				_guard(prev, q)
			prev = Vector2.INF if open else q
			along += 4.0
	# cliff faces along the south coast and the western headland
	for i in range(11, LAND.size() - 4):
		var a: Vector2 = LAND[i]
		var b: Vector2 = LAND[i + 1]
		var steps := int(a.distance_to(b) / 11.0) + 1
		for j in steps:
			var p := a.lerp(b, (j + 0.5) / steps)
			var out := Vector2(b.y - a.y, a.x - b.x).normalized()
			var c := p + out * 4.5
			var yaw := rad_to_deg(atan2(out.x, out.y))
			decor("cliff_b" if (i + j) % 2 else "cliff_a", Vector3(c.x, -20.0, c.y), yaw + rng.randf_range(-12, 12), rng.randf_range(1.5, 2.0), false, true)
	for c: Vector2 in [Vector2(-209, 50), Vector2(-212, 66), Vector2(-209, 82), Vector2(-208, 18), Vector2(-210, -14), Vector2(-209, -44)]:
		decor("cliff_a", Vector3(c.x, -21.0, c.y), -90.0 + rng.randf_range(-15, 15), rng.randf_range(1.7, 2.2), false, true)
	# sea stacks off the coast
	for c: Vector3 in [Vector3(-120, 0, 158), Vector3(-60, 0, 162), Vector3(-214, 0, 118), Vector3(10, 0, 160), Vector3(-196, 0, 136)]:
		decor("rock_large", Vector3(c.x, SEA_Y - 1.5, c.z), rng.randf() * 360.0, rng.randf_range(2.2, 3.4), false, true)

func _guard(a: Vector2, b: Vector2) -> void:
	boundary(Vector3(a.x, bed(a.x, a.y) - 3.0, a.y), Vector3(b.x, bed(b.x, b.y) - 3.0, b.y), 7.0, 0.6)

# ------------------------------------------------------------------------------------------------------------
# Malasugue's palisade seen from outside, and the open South Gate

func _town_wall() -> void:
	var n := int(TAU * TOWN_FENCE / 4.0)
	for i in n:
		var a := TAU * (i + 0.5) / n
		var p := TOWN + Vector2(cos(a), sin(a)) * TOWN_FENCE
		var deg := rad_to_deg(a)
		if absf(deg - 90.0) < 6.5:
			continue
		kit("palisade_fence", Vector3(p.x, 0, p.y), -deg + 90.0 + 180.0, 1.0, props, true)
	var gz := TOWN.y + TOWN_FENCE - 0.6
	for sx: float in [-3.2, 3.2]:
		kit("pillar_quoin", Vector3(TOWN.x + sx, 0, gz), 0.0, 1.0, geo, true)
	kit("arch_quoin", Vector3(TOWN.x, 0, gz), 0.0, 1.0, geo, true)
	brazier(Vector3(TOWN.x - 5.2, 0, gz + 1.6), 3.2, true, true)
	brazier(Vector3(TOWN.x + 5.2, 0, gz + 1.6), 3.2, false, true)
	kit("banner_torn", Vector3(TOWN.x - 3.2, 3.6 + ground(TOWN.x - 3.2, gz), gz + 0.75), 180.0, 1.0, deco)
	kit("banner_torn", Vector3(TOWN.x + 3.2, 3.6 + ground(TOWN.x + 3.2, gz), gz + 0.75), 180.0, 1.0, deco)
	# rooftops beyond the palisade so the town reads from the road
	for r in [[Vector2(-128, -4), 30.0], [Vector2(-96, -6), -40.0], [Vector2(-104, -30), 15.0], [Vector2(-126, -24), 70.0]]:
		kit("house_intact", Vector3(r[0].x, 0, r[0].y), r[1], 1.0, deco, true)
	light(Vector3(TOWN.x, 6.0, TOWN.y + 4.0), Color(1.0, 0.7, 0.4), 2.0, 26.0)
	# a wall of collision around the palisade except the gate, and the walk-through exit into the town
	var m := 28
	for i in m:
		var a0 := TAU * i / m
		var a1 := TAU * (i + 1) / m
		var mid := rad_to_deg((a0 + a1) * 0.5)
		if absf(mid - 90.0) < 7.0:
			continue
		boundary(Vector3(TOWN.x + cos(a0) * (TOWN_FENCE + 1.2), 0, TOWN.y + sin(a0) * (TOWN_FENCE + 1.2)),
			Vector3(TOWN.x + cos(a1) * (TOWN_FENCE + 1.2), 0, TOWN.y + sin(a1) * (TOWN_FENCE + 1.2)), 8.0)
	boundary(Vector3(TOWN.x - 3.0, 0, gz - 2.6), Vector3(TOWN.x + 3.0, 0, gz - 2.6), 8.0)
	exit_zone(&"westreach_south_gate", Vector3(TOWN.x, 0, gz + 1.6), Vector3(6.0, 4.0, 3.0), &"sanctuary", &"gate", "Malasugue")
	lamp_post(Vector3(TOWN.x - 4.2, 0, GATE.y - 1.0), 180.0)
	lamp_post(Vector3(TOWN.x + 4.2, 0, GATE.y - 1.0), 0.0)

# ------------------------------------------------------------------------------------------------------------
# places

func _crossroads() -> void:
	# the South Gate fork: three roads and a signpost
	signpost_at(Vector2(-112, 52), [["Malasugue", Vector2(0, -1)], ["Old Mill", Vector2(12, 8)], ["Lantern Fields", Vector2(10, 18)],
		["Tideglass Cove", Vector2(-10, 10)]])
	kit("cart_hay", Vector3(-121, 0, 42.5), 70.0, 1.0, props, true)
	breakable("crate", Vector3(-118.6, 0, 41.0), 30.0, 20.0, true)
	breakable("barrel", Vector3(-104.6, 0, 42.0), 0.0, 20.0, true)
	kit("notice_board", Vector3(-104.0, 0, 51.5), -60.0, 1.0, props, true)
	# Old Mill Crossroads: four roads, a signpost on a grass island, a waystone and lamps
	signpost_at(Vector2(-4.5, 7.5), [["Malasugue", Vector2(-12, 6)], ["Ruined Forest", Vector2(-10, -10)],
		["Lantern Fields", Vector2(4, 16)], ["Olivar (Lake Shore Road)", Vector2(12, 1)]])
	kit("statue_small", Vector3(-3.4, 0, 8.6), 150.0, 0.9, props, true)
	for p: Vector3 in [Vector3(-7.5, 0, -4.0), Vector3(6.5, 0, 6.5), Vector3(-9.0, 0, 9.0)]:
		lamp_post(p, rng.randf() * 360.0)

func _mill() -> void:
	var c := MILL_HOUSE
	var y := bed(c.x, c.y)
	var h := kit("house_intact", Vector3(c.x, y, c.y), 0.0, 1.0, props)
	light(socket_pos(h, "door_light"), Color(1.0, 0.68, 0.35), 2.4, 8.0, false, true)
	light(Vector3(c.x - 2.0, y + 1.8, c.y + 4.6), Color(1.0, 0.6, 0.3), 1.2, 5.0)
	# the water wheel turns in the stream beside the mill, on a long axle from the east wall
	var wheel := Spinner.new()
	wheel.name = "WaterWheel"
	wheel.axis = Vector3.RIGHT
	wheel.speed = 0.55
	var wy := _t[_k(15.6, c.y)] - 0.4
	wheel.position = Vector3(15.6, wy, c.y)
	var wood := MaterialLibrary.env("BH_WoodDark")
	for i in 10:
		var paddle := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(1.4, 0.12, 0.9)
		paddle.mesh = bm
		paddle.material_override = wood
		var a := TAU * i / 10.0
		paddle.transform = Transform3D(Basis(Vector3.RIGHT, a), Vector3(0, sin(a) * 2.3, cos(a) * 2.3))
		wheel.add_child(paddle)
	for sx: float in [-0.62, 0.62]:
		var rim := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 2.25
		tm.outer_radius = 2.45
		tm.rings = 24
		rim.mesh = tm
		rim.material_override = wood
		rim.transform = Transform3D(Basis(Vector3.FORWARD, PI * 0.5), Vector3(sx, 0, 0))
		wheel.add_child(rim)
	deco.add_child(wheel)
	var axle := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.16
	cm.bottom_radius = 0.16
	cm.height = 8.0
	axle.mesh = cm
	axle.material_override = MaterialLibrary.env("BH_Iron")
	axle.transform = Transform3D(Basis(Vector3.FORWARD, PI * 0.5), Vector3(12.0, wy, c.y))
	deco.add_child(axle)
	var splash := VFXLib.particles(Color(0.75, 0.9, 1.0, 0.4), 18, 1.0, false, 0.25, 0.6, 30.0, Vector3(0, 1.2, 0.6), 0.5, false)
	splash.position = Vector3(15.6, wy - 1.8, c.y + 1.8)
	deco.add_child(splash)
	# the mill yard: sacks on a cart, barrels, a winch over the race, a lantern
	kit("cart_hay", Vector3(c.x - 6.8, 0, c.y + 6.5), 20.0, 1.0, props, true)
	kit("winch", Vector3(c.x + 7.0, 0, c.y + 5.2), -90.0, 1.0, props, true)
	for p: Vector3 in [Vector3(-4.8, 0, 4.4), Vector3(-5.6, 0, 3.4), Vector3(3.8, 0, 5.2)]:
		breakable("barrel" if p.x < 0.0 else "crate", Vector3(c.x, 0, c.y) + p, rng.randf() * 360.0, 20.0, true)
	kit("lantern_stand", Vector3(c.x + 5.0, 0, c.y + 4.4), 0.0, 1.0, props, true)
	light(Vector3(c.x + 5.45, bed(c.x + 5, c.y + 4.4) + 1.8, c.y + 4.4), Color(1.0, 0.7, 0.4), 2.0, 8.0, false, true)
	# the stone bridge on the Lake Shore Road, and the washed-out end beyond it
	# the bridge's ends meet the road bed (its deck arches 0.9 m above them), within the 0.5 m climb at each end
	arch("bridge_stone", Vector3(BRIDGE.x, (bed(BRIDGE.x - 6.0, BRIDGE.y) + bed(BRIDGE.x + 6.0, BRIDGE.y)) * 0.5, BRIDGE.y), 0.0)
	for sx: float in [-7.0, 7.0]:
		for dz: float in [-2.4, 2.4]:
			kit("pillar", Vector3(BRIDGE.x + sx, 0, BRIDGE.y + dz), 0.0, 0.4, geo, true)
	# the spring washout, planked over by Olivar's traders: rubble pushed aside, a timber causeway, a new sign
	var end := Vector2(56, -8)
	decor("rubble_pile", Vector3(end.x + 3.0, 0, end.y - 6.5), 30.0, 1.3, true, true)
	decor("log_fallen", Vector3(end.x + 6.0, 0, end.y + 5.5), 70.0, 1.0, true, true)
	for i in 3:
		var q := DataIsland.point_at(DataIsland.road("wr_lake_road").points, 58.0 + i * 5.6)
		kit("dock_planks", Vector3(q.x, bed(q.x, q.y) - 0.28, q.y), 10.0 + rng.randf_range(-3, 3), 0.95, deco)
	for sz: float in [-3.6, 3.6]:
		kit("wood_fence", Vector3(end.x + 6.0, 0, end.y - 1.2 + sz), 12.0, 1.0, props, true)
	signpost_at(Vector2(end.x - 3.0, end.y + 3.4), [["Olivar", Vector2(1, -0.2)], ["Old Mill", Vector2(-1, 0.3)]])
	signpost_at(Vector2(75.5, -4.8), [["Olivar (Lake Shore Road)", Vector2(1, 0)], ["Old Mill", Vector2(-1, 0.4)]])
	lamp_post(Vector3(72.0, 0, -14.0), 0.0)
	exit_zone(&"westreach_lake_road", Vector3(79.5, 0, -9.0), Vector3(3.0, 4.0, 8.4), &"olivar", &"west_road", "Olivar")

func _fields() -> void:
	# crop rows (leafy rows in dark soil) inside low fences, with a lantern at every corner
	for pl in PLOTS:
		var cx: float = pl[0]
		var cz: float = pl[1]
		var hx: float = pl[2]
		var hz: float = pl[3]
		var row := -hz + 0.7
		while row < hz - 0.4:
			var col := -hx + 0.8
			while col < hx - 0.5:
				decor("fern", Vector3(cx + col + rng.randf_range(-0.2, 0.2), 0, cz + row), rng.randf() * 360.0, rng.randf_range(0.45, 0.65))
				col += 1.25
			row += 1.4
		for sx: float in [-1.0, 1.0]:
			var fx := cx + sx * (hx + 0.8)
			var zz := -hz
			while zz < hz:
				if rng.randf() < 0.8:
					kit("wood_fence", Vector3(fx, 0, cz + zz + 2.0), 90.0, 1.0, props, true)
				zz += 4.2
		for corner: Vector2 in [Vector2(-1, -1), Vector2(1, 1)]:
			var lp := Vector2(cx + corner.x * (hx + 1.6), cz + corner.y * (hz + 1.2))
			kit("lantern_stand", Vector3(lp.x, 0, lp.y), rng.randf() * 360.0, 1.0, props, true)
			light(Vector3(lp.x + 0.4, ground(lp.x, lp.y) + 1.9, lp.y), Color(1.0, 0.72, 0.4), 2.2, 9.0, false, true)
	# the farmstead east of the lane, its store raided, and a cottage above the coast road
	var farm := kit("house_intact", Vector3(46, 0, 94), -90.0, 1.0, props, true)
	light(socket_pos(farm, "door_light"), Color(1.0, 0.68, 0.35), 2.2, 8.0, false, true)
	var cot := kit("house_intact", Vector3(20, 0, 128), 180.0, 1.0, props, true)
	light(socket_pos(cot, "door_light"), Color(1.0, 0.68, 0.35), 2.0, 7.0, false, true)
	kit("well", Vector3(38, 0, 101), 15.0, 1.0, props, true)
	kit("cart_hay", Vector3(40.5, 0, 86.0), -25.0, 1.0, props, true)
	for p: Vector3 in [Vector3(43.5, 0, 84.0), Vector3(44.6, 0, 85.1), Vector3(47.8, 0, 86.4), Vector3(38.2, 0, 90.4)]:
		breakable("crate" if rng.randf() < 0.6 else "barrel", p, rng.randf() * 360.0, 20.0, true)
	kit("wagon_broken", Vector3(50.0, 0, 80.5), 40.0, 1.0, props, true)
	signpost_at(Vector2(28.5, 104.0), [["Old Mill", Vector2(-9, -26)], ["Malasugue", Vector2(-27, -12)], ["Tideglass Cove", Vector2(-23, 6)],
		["Wyman Outpost (Fen Road)", Vector2(12, -4)]])
	_fen_road()

func _coast() -> void:
	# a ruined lookout on the clifftop, benches for the fishers' wives, lamps along the coast road
	var look := Vector2(-40, 134)
	kit("pillar_broken", Vector3(look.x - 2.0, 0, look.y), 0.0, 0.8, geo, true)
	kit("pillar", Vector3(look.x + 2.2, 0, look.y + 0.5), 0.0, 0.7, geo, true)
	kit("wall_low_broken", Vector3(look.x, 0, look.y + 1.2), 180.0, 1.0, geo, true)
	kit("bench", Vector3(look.x + 0.2, 0, look.y - 2.4), 180.0, 1.0, props, true)
	for p: Vector2 in [Vector2(-98, 128.5), Vector2(-14, 126.5), Vector2(-135, 119.5)]:
		lamp_post(Vector3(p.x, 0, p.y), rng.randf() * 360.0)
	for i in 14:
		var x := -130.0 + i * 11.0 + rng.randf_range(-3, 3)
		decor("rock_medium", Vector3(x, 0, 133.0 + rng.randf_range(-2, 2)), rng.randf() * 360.0, rng.randf_range(0.7, 1.2), true, true)

func _cove() -> void:
	# the beach: a pier into the bay, boats pulled up, drying racks and nets, two fishers' huts and the shrine
	var pier_x := PIER_X
	for i in 3:
		kit("dock_planks", Vector3(pier_x, SEA_Y + 0.55, 104.0 + i * 5.8), 90.0, 1.0, geo)
	walk_slab(Vector3(pier_x, SEA_Y + 0.9, 109.8), Vector3(4.0, 0.4, 17.4))
	kit("boat_rowing", Vector3(pier_x + 3.6, SEA_Y + 0.05, 112.0), 80.0, 1.0, deco)
	kit("boat_rowing", Vector3(pier_x - 3.8, SEA_Y + 0.05, 116.5), 100.0, 1.0, deco)
	kit("boat_rowing", Vector3(-188, 0, 100.5), 20.0, 1.0, props, true)
	kit("boat_rowing", Vector3(-160, 0, 103.5), -30.0, 1.0, props, true)
	for p in [[Vector2(-186, 94), 15.0], [Vector2(-162, 96), -20.0], [Vector2(-192, 88), 70.0]]:
		kit("fish_rack", Vector3(p[0].x, 0, p[0].y), p[1], 1.0, props, true)
	for p in [[Vector2(-182, 98), 0.0], [Vector2(-156, 99), -30.0]]:
		kit("fishing_nets", Vector3(p[0].x, 0, p[0].y), p[1], 1.0, props, true)
	var hut := kit("house_intact", Vector3(-150, 0, 97), -120.0, 0.8, props, true)
	light(socket_pos(hut, "door_light"), Color(1.0, 0.68, 0.35), 2.0, 7.0, false, true)
	for p: Vector2 in [Vector2(-176, 102), Vector2(-160, 92), Vector2(-190, 96)]:
		kit("lantern_stand", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 1.0, props, true)
		light(Vector3(p.x + 0.4, ground(p.x, p.y) + 1.9, p.y), Color(1.0, 0.72, 0.42), 2.4, 10.0, false, true)
	for p: Vector3 in [Vector3(-184, 0, 91), Vector3(-183, 0, 92.2), Vector3(-158, 0, 100)]:
		breakable("barrel", p, rng.randf() * 360.0, 20.0, true)
	campfire(Vector3(-170, 0, 97.5), 3.6)
	# the shrine: a waypoint on the rocks above the tideline
	floor_disc(Vector3(SHRINE.x, 0, SHRINE.y), 3.4, bed(SHRINE.x, SHRINE.y) + 0.05)
	var sy := bed(SHRINE.x, SHRINE.y) + 0.05
	teleporter(&"cove_shrine", Vector3(SHRINE.x, sy, SHRINE.y), &"sanctuary", &"waypoint", "Malasugue Town")
	for a: float in [0.3, 1.6, 3.4, 4.8]:
		decor("rock_medium", Vector3(SHRINE.x + cos(a) * 5.0, 0, SHRINE.y + sin(a) * 4.6), rng.randf() * 360.0, rng.randf_range(0.6, 0.9), true, true)
	signpost_at(Vector2(-164.5, 90.5), [["Malasugue (Cove Steps)", Vector2(12, -8)], ["Lantern Fields (Coast Road)", Vector2(14, 8)]])
	# the smugglers' sea cave in the western headland: a dark mouth, crates of the missing shipment
	var c := CAVE
	var cy := ground(c.x, c.y)
	for dz: float in [-5.0, 5.0]:
		decor("cliff_b", Vector3(c.x - 4.0, cy - 2.0, c.y + dz), -90.0 + rng.randf_range(-10, 10), 1.3, false, true)
	decor("cliff_a", Vector3(c.x - 6.5, cy + 2.5, c.y), -90.0, 1.4, false, true)
	var dark := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(4.2, 3.4)
	dark.mesh = qm
	var dm := StandardMaterial3D.new()
	dm.albedo_color = Color(0, 0, 0)
	dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	dark.material_override = dm
	dark.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(90)), Vector3(c.x - 2.2, cy + 1.7, c.y))
	deco.add_child(dark)
	blocker(Vector3(c.x - 3.2, cy + 2.0, c.y), Vector3(1.0, 4.0, 6.0))
	for p: Vector3 in [Vector3(1.6, 0, -2.2), Vector3(2.4, 0, -1.2), Vector3(1.2, 0, 2.6), Vector3(3.2, 0, 2.2)]:
		breakable("crate", Vector3(c.x, 0, c.y) + p, rng.randf() * 90.0, 20.0, true)
	kit("chest", Vector3(c.x + 0.6, 0, c.y + 0.4), 90.0, 1.0, props, true)
	torch_post(Vector3(c.x + 3.4, 0, c.y - 3.8))

func torch_post(p: Vector3) -> void:
	var y := ground(p.x, p.z) + 2.3
	flame(Vector3(p.x, y + 0.2, p.z), 1.0)
	light(Vector3(p.x, y + 0.6, p.z), FIRE, 2.6, 10.0, false, true)

func _roadside() -> void:
	# lamps along the maintained roads (every ~28 m), placed on the verge
	for id: String in ["wr_mill_road", "wr_field_road", "wr_forest_road", "wr_mill_lane"]:
		var pts: Array = DataIsland.road(id).points
		var total := DataIsland.polyline_length(pts)
		var along := 18.0
		var side := 1.0
		while along < total - 12.0:
			var a := DataIsland.point_at(pts, along)
			var b := DataIsland.point_at(pts, along + 1.0)
			var dir := (b - a).normalized()
			var off := Vector2(-dir.y, dir.x) * 4.2 * side
			lamp_post(Vector3(a.x + off.x, 0, a.y + off.y), rad_to_deg(atan2(-off.x, -off.y)))
			along += 30.0
			side = -side
	# the Forest Road's last stretch before the treeline: a waymarker and the walk-through into the forest
	signpost_at(Vector2(-47.5, -48.5), [["Ruined Forest", Vector2(-1, -1.2)], ["Old Mill", Vector2(1, 1)]])
	exit_zone(&"westreach_forest_road", Vector3(-55.0, 0, -53.6), Vector3(9.0, 4.0, 3.0), &"ruined_forest", &"south_road", "the Ruined Forest")

func _encounters() -> void:
	# wolves on the clifftop, goblins picking over a stolen-goods camp and raiding the farm store, smugglers at the
	# cave, and a pair of the forest's dead drifting down the Forest Road. The mill, the gate and the cove are safe.
	enemy_zone("coast_wolves", Vector3(WOLVES.x, 0, WOLVES.y), 5.0, [&"dire_wolf"], 3, 0.0, true)
	decor("bones_scatter", Vector3(WOLVES.x + 1.5, 0, WOLVES.y + 1.0), 40.0)
	var g := GOBLIN_CAMP
	campfire(Vector3(g.x, 0, g.y), 3.4)
	kit("tent_old", Vector3(g.x - 3.4, 0, g.y - 2.6), 50.0, 0.8, props, true)
	for p: Vector3 in [Vector3(2.6, 0, -1.6), Vector3(3.2, 0, -0.4), Vector3(-2.8, 0, 2.6), Vector3(1.4, 0, 2.8)]:
		breakable("crate" if rng.randf() < 0.6 else "barrel", Vector3(g.x, 0, g.y) + p, rng.randf() * 360.0, 20.0, true)
	decor("weapons_discarded", Vector3(g.x + 1.8, 0, g.y + 2.2), 30.0)
	enemy_zone("goblin_camp", Vector3(g.x, 0, g.y), 5.0, [&"goblin_skulker", &"goblin_skulker", &"goblin_summoner", &"goblin_skulker"], 4, 0.15, true)
	enemy_zone("field_raid", Vector3(FIELD_RAID.x, 0, FIELD_RAID.y), 6.0, [&"goblin_skulker"], 3, 0.1, true)
	enemy_zone("smugglers", Vector3(SMUGGLERS.x, 0, SMUGGLERS.y), 4.0, [&"bandit_cutthroat", &"bandit_marksman", &"bandit_bombardier"], 3, 0.2, true)
	enemy_zone("forest_watch", Vector3(FOREST_WATCH.x, 0, FOREST_WATCH.y), 4.0, [&"hollow_soldier"], 2, 0.0, true)

func _greenery() -> void:
	var blocked := func(x: float, z: float) -> bool:
		var k := _k(x, z)
		if _rd[k] < (6.0 if _rt[k] == 1 else 4.0) or _ds[k] < 6.0 or _sea[k] > -4.0:
			return true
		var p := Vector2(x, z)
		if p.distance_to(TOWN) < TOWN_FENCE + 5.0:
			return true
		for pl in PLOTS:
			if absf(x - pl[0]) < pl[2] + 3.0 and absf(z - pl[1]) < pl[3] + 3.0:
				return true
		for pd in PADS:
			if p.distance_to(Vector2(pd[0], pd[1])) < pd[2] + 2.0:
				return true
		for c: Vector2 in [COVE, CAVE, SHRINE, WOLVES, GOBLIN_CAMP, FIELD_RAID, SMUGGLERS, FOREST_WATCH, BRIDGE, Vector2(56, -8), FEN_BRIDGE,
				Vector2(-4.0, 57.5), Vector2(-38.0, 91.0), Vector2(22.0, 100.5), Vector2(-100.0, 62.0), Vector2(6.0, -11.0), Vector2(-2.5, 30.0),
				Vector2(40.0, 61.0), Vector2(-22.0, 61.0), Vector2(-20.0, -46.0), Vector2(18.0, -42.0)]:
			if p.distance_to(c) < 9.0:
				return true
		return p.distance_to(Vector2(-180, 100)) < 24.0
	# pines thicken toward the forest in the north; oaks and bushes around the farms; grass everywhere dry
	var north := func(x: float, z: float) -> bool: return blocked.call(x, z) or z > 30.0 + sin(x * 0.07) * 14.0
	var south := func(x: float, z: float) -> bool: return blocked.call(x, z) or z < 20.0
	var trees := scatter(["tree_pine", "tree_pine", "tree_pine", "tree_oak_twisted", "tree_dead_a"], Rect2(-205, -58, 285, 92), 240, 4.6,
		Vector2(0.8, 1.3), north, true, true)
	trees.append_array(scatter(["tree_oak_twisted", "tree_pine", "tree_dead_b"], Rect2(-205, 20, 285, 120), 76, 7.0, Vector2(0.8, 1.2), south, true, true))
	for t in trees:
		var k := _k(t.x, t.z)
		if _rd[k] < 14.0:
			blocker(Vector3(t.x, ground(t.x, t.z) + 2.0, t.z), Vector3(0.9, 4.0, 0.9))
	scatter(["bush_a", "bush_b", "fern"], Rect2(-205, -58, 285, 196), 270, 3.0, Vector2(0.7, 1.2), blocked, true, true)
	# grass has no spacing rule (MapBuilder.scatter's spacing check is quadratic in the count)
	var placed := 0
	var tries := 0
	while placed < 1700 and tries < 9000:
		tries += 1
		var x := -205.0 + rng.randf() * 285.0
		var z := -58.0 + rng.randf() * 196.0
		var k := _k(x, z)
		if _rd[k] < 3.0 or _sea[k] > -2.0 or _ds[k] < 3.5 or Vector2(x, z).distance_to(TOWN) < TOWN_FENCE + 2.0:
			continue
		decor("grass_clump", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.8, 1.4))
		placed += 1
	scatter(["rock_small", "rock_small", "mushrooms", "roots"], Rect2(-205, -58, 270, 196), 160, 3.0, Vector2(0.7, 1.2), blocked, true, true)
	scatter(["rock_medium", "stump", "log_fallen"], Rect2(-205, -58, 270, 196), 40, 9.0, Vector2(0.7, 1.1), blocked, false)
	# hedgerows along the field road
	var fr: Array = DataIsland.road("wr_field_road").points
	var along := 10.0
	while along < DataIsland.polyline_length(fr) - 10.0:
		var a := DataIsland.point_at(fr, along)
		var b := DataIsland.point_at(fr, along + 1.0)
		var dir := (b - a).normalized()
		var off := Vector2(-dir.y, dir.x) * 5.4
		decor("bush_b", Vector3(a.x + off.x, 0, a.y + off.y), rng.randf() * 360.0, rng.randf_range(0.8, 1.1), true, true)
		along += 3.6

## Signposts stand on the smooth road bed, not on the noisy verge.
func signpost_at(p: Vector2, arms: Array) -> Node3D:
	return signpost(p, arms, bed(p.x, p.y))

## bh-007: the Fen Road east from the fields, over the Fen Bridge, to the walk-through for Wyman Outpost.
func _fen_road() -> void:
	var b := FEN_BRIDGE
	arch("bridge_stone", Vector3(b.x, (bed(b.x - 6.0, b.y) + bed(b.x + 6.0, b.y)) * 0.5, b.y), 0.0)
	for sx: float in [-7.0, 7.0]:
		for dz: float in [-2.4, 2.4]:
			kit("pillar", Vector3(b.x + sx, 0, b.y + dz), 0.0, 0.4, geo, true)
	signpost_at(Vector2(74.5, 99.8), [["Wyman Outpost (Fen Road)", Vector2(1, 0)], ["Lantern Fields", Vector2(-1, 0.3)]])
	lamp_post(Vector3(69.0, 0, 91.0), 0.0)
	lamp_post(Vector3(48.0, 0, 108.5), 0.0)
	exit_zone(&"westreach_fen_road", Vector3(79.5, 0, 95.0), Vector3(3.0, 4.0, 8.4), &"wyman_outpost", &"west_road", "Wyman Outpost")

## bh-007: herb patches beside field walls (Silverleaf), on the stream banks (Mirebloom), near the goblins' fire
## (Emberroot) and in the dark of the northern woods (Brightcap).
func _herbs() -> void:
	for p: Vector2 in [Vector2(-4.0, 57.5), Vector2(-38.0, 91.0), Vector2(22.0, 100.5), Vector2(-100.0, 62.0)]:
		herb_patch(&"silverleaf", Vector3(p.x, 0, p.y))
	for p: Vector2 in [Vector2(6.0, -11.0), Vector2(-2.5, 30.0), Vector2(40.0, 61.0)]:
		herb_patch(&"mirebloom", Vector3(p.x, 0, p.y))
	herb_patch(&"emberroot", Vector3(-22.0, 0, 61.0))
	for p: Vector2 in [Vector2(-20.0, -46.0), Vector2(18.0, -42.0)]:
		herb_patch(&"brightcap", Vector3(p.x, 0, p.y))
