extends SettlementBuilder
## MAP — The Coilwood (bh-029; Zarael, levels 50–56). "Jungle over the Wirewrights' fields."
##
## The road from Agdao's east gate runs east through a jungle of giant buttress trees and palms that has swallowed the
## Wirewrights' step-fields: low terraced earth banks held by ruined glyph walls, and a broken aqueduct that once fed
## them. The Heartwire's relay lines run inlaid down the old paved road and out along the trails to three relay pylons;
## the Kharvenn chain-priests have chained all three (quest "Wire-sick": RelayPylon + zr_relay_chains, hidden on
## DataZarael.RELAY_FLAGS) and guard each with a small camp. Their main camp sits on the rise north of the Relay Lines;
## the Serpent trail climbs past the eastern relay to the jade jaws of the Jade Sepulchre. A waypoint glows in a ruined
## shrine just off the road near the west edge (safe ground). East, the road leaves the trees for the Glasswire Barrens.
## Every frozen spot comes from DataZarael / DataDungeonsZarael; the road beds follow DataIsland's Zarael polylines.

const MAP := &"zr_coilwood"
const SHRINE := Vector2(-108.0, 7.5)       # the shrine stands just north of the road; its stair comes down to the road
const SHRINE_S := 1.25                     # shrine scale (the waypoint dais must clear the altar inside)
const AQ_X := -88.0                        # the aqueduct runs north-south on this line
const AQ_Z := Vector2(-46.0, 50.0)         # from the hills in the north to its broken southern stub
const AQ_GAPS := [[6.0, 22.0], [-22.0, -18.0]]   # z ranges where spans have fallen (the road passes the first)
const CISTERN := Rect2(31.0, 57.0, 12.0, 9.0)
## Landform anchors (x, z, height): inverse-distance blended into the smooth ground the road beds follow.
const ANCHORS := [
	Vector3(-136, 30, 0.6), Vector3(-108, 9, 1.0), Vector3(-88, 14, 1.6), Vector3(-60, 10, 2.0), Vector3(-75, -6, 3.0),
	Vector3(-75, -18, 4.2), Vector3(-75, -30, 5.4), Vector3(-44, -6, 3.0), Vector3(-44, -18, 4.2), Vector3(-44, -30, 5.4),
	Vector3(-58, -42, 6.4), Vector3(-20, 4, 2.8), Vector3(10, 0, 3.0), Vector3(-20, 30, 2.0), Vector3(-20, 42, 0.8),
	Vector3(18, 52, 0.4), Vector3(40, 66, 0.2), Vector3(60, 46, 1.2), Vector3(28, -58, 5.6), Vector3(18, -26, 4.0),
	Vector3(40, -4, 4.2), Vector3(66, -28, 7.0), Vector3(70, -6, 4.8), Vector3(86, -18, 6.0), Vector3(86, -30, 7.2),
	Vector3(84, -42, 8.4), Vector3(96, -58, 9.0), Vector3(100, 2, 4.0), Vector3(136, 8, 3.0), Vector3(-110, 56, 0.8),
	Vector3(-118, -40, 7.0), Vector3(110, 50, 2.0), Vector3(-50, 60, 1.4), Vector3(-10, -60, 7.0), Vector3(120, -40, 9.0),
]
## Step-fields: flat terraces (centre x, z, half x, half z, height), ruined glyph walls along their lower (south) edges.
const FIELDS := [
	[-75.0, -6.0, 7.0, 4.5, 3.0], [-75.0, -18.0, 7.0, 4.5, 4.2], [-75.0, -30.0, 7.0, 4.5, 5.4],
	[-44.0, -6.0, 9.0, 4.5, 3.0], [-44.0, -18.0, 9.0, 4.5, 4.2], [-44.0, -30.0, 9.0, 4.5, 5.4],
	[86.0, -18.0, 10.0, 4.5, 6.0], [86.0, -30.0, 10.0, 4.5, 7.2], [84.0, -42.0, 8.0, 4.0, 8.4],
	[-20.0, 30.0, 10.0, 4.5, 2.0], [-20.0, 42.0, 10.0, 4.5, 0.8],
]
## Ground kept level for structures: [x, z, radius].
const PADS := [[-108.0, 7.5, 9.5], [-58.0, -42.0, 7.0], [18.0, 52.0, 7.0], [66.0, -28.0, 7.0], [28.0, -58.0, 16.0],
	[96.0, -58.0, 10.0], [10.0, 0.0, 8.0]]
## Encounter camps: [id, centre, radius, monsters, count, levels, elite chance]. Levels rise with distance from Agdao.
const CAMPS := [
	["cw_road_south", Vector2(-86, 38), 5.0, [&"glyphbound_warrior", &"coil_shaman", &"glyphbound_warrior"], 3, Vector2i(50, 51), 0.1],
	["cw_aqueduct", Vector2(-100, -22), 5.0, [&"glyphbound_warrior", &"wireback_stalker", &"glyphbound_warrior"], 4, Vector2i(50, 52), 0.1],
	["cw_relay_west", Vector2(-49, -46), 5.0, [&"chain_priest", &"chain_bearer", &"glyphbound_warrior"], 4, Vector2i(50, 52), 0.15],
	["cw_fields", Vector2(-75, -36), 5.0, [&"mossback_idol", &"glyphbound_warrior", &"coil_shaman"], 3, Vector2i(51, 53), 0.15],
	["cw_lines", Vector2(-18, 18), 5.0, [&"relay_mote", &"wireback_stalker", &"relay_mote", &"relay_mote"], 4, Vector2i(52, 53), 0.1],
	["cw_relay_south", Vector2(8, 60), 5.0, [&"chain_priest", &"chain_bearer", &"coil_shaman"], 4, Vector2i(52, 54), 0.15],
	["cw_cistern", Vector2(-14, 64), 5.0, [&"mossback_idol", &"coil_shaman", &"glyphbound_warrior"], 3, Vector2i(52, 54), 0.15],
	["cw_north", Vector2(-16, -48), 5.0, [&"relay_mote", &"coil_shaman", &"relay_mote"], 4, Vector2i(53, 54), 0.15],
	["cw_south_wood", Vector2(58, 52), 5.5, [&"wireback_stalker", &"mossback_idol", &"wireback_stalker"], 4, Vector2i(53, 55), 0.15],
	["cw_relay_east", Vector2(56, -38), 5.0, [&"chain_priest", &"chain_bearer", &"wireback_stalker", &"chain_priest"], 5, Vector2i(54, 56), 0.2],
	["cw_camp", Vector2(28, -60), 7.0, [&"chain_priest", &"chain_bearer", &"chain_priest", &"chain_bearer", &"glyphbound_warrior"], 6, Vector2i(54, 56), 0.25],
	["cw_camp_pens", Vector2(16, -66), 4.5, [&"chain_bearer", &"wireback_stalker", &"chain_priest"], 4, Vector2i(54, 56), 0.2],
	["cw_jade", Vector2(76, -58), 5.0, [&"mossback_idol", &"glyphbound_warrior", &"coil_shaman"], 4, Vector2i(55, 56), 0.2],
	["cw_east_road", Vector2(110, 24), 5.0, [&"glyphbound_warrior", &"coil_shaman", &"relay_mote"], 4, Vector2i(54, 55), 0.15],
]
const WEST_EXIT := [Vector2(-152, 30.0), Vector2(-136, 30.0), Vector2(-120, 24.0)]
const EAST_EXIT := [Vector2(100, 2.0), Vector2(136, 8.0), Vector2(152, 10.5)]

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.025, 0.021, 0.036), "sky_horizon": Color(0.208, 0.142, 0.177),
		"ambient": Color(0.421, 0.419, 0.426), "ambient_energy": 1.1,
		"fog": Color(0.119, 0.106, 0.127), "fog_density": 0.006, "fog_height": 0.5, "fog_height_density": 0.07,
		"sun": Color(0.824, 0.68, 0.699), "sun_energy": 0.58, "sun_rot": Vector3(-44, 28, 0), "glow": 0.95,
		"exposure": 1.22, "contrast": 1.08, "saturation": 0.98,
	})
	prepare(-152.0, -112.0, 304, 224, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "jungle_floor", "moss": "jungle_floor", "dirt": "red_clay", "path": "terrace_paving", "rock": "cliff_ochre"},
		Color(0.9, 0.95, 0.88))
	_edges()
	_shrine()
	_aqueduct()
	_fields()
	_cistern()
	_relay_lines()
	_relays()
	_kharvenn_camp()
	_gates()
	_ruins()
	_encounters()
	_atmosphere()
	_greenery()
	_map_design()
	spawn(&"agdao_road", Vector3(DataZarael.CW_WEST.x, 0, DataZarael.CW_WEST.z), 90.0, true)
	spawn(&"start", Vector3(DataZarael.CW_WEST.x, 0, DataZarael.CW_WEST.z), 90.0, true)
	spawn(&"barrens_road", Vector3(DataZarael.CW_EAST.x, 0, DataZarael.CW_EAST.z), -90.0, true)
	set_bounds(AABB(Vector3(-140, -6, -100), Vector3(280, 40, 200)))
	view("overview", Vector3(0, 2, 4), 0.0, 60.0, 250.0, 50.0)
	view("topdown", Vector3(0, 2, 0), 0.0, 89.5, 270.0, 55.0)
	view("shrine", Vector3(-108, 3, 12), 0.0, 44.0, 30.0, 45.0)
	view("aqueduct", Vector3(-86, 4, 8), 25.0, 36.0, 38.0, 45.0)
	view("step_fields", Vector3(-60, 5, -20), 0.0, 46.0, 56.0, 45.0)
	view("relay_west", Vector3(-56, 7, -40), 0.0, 46.0, 30.0, 45.0)
	view("relay_south", Vector3(22, 2, 54), 0.0, 62.0, 30.0, 45.0)
	view("relay_east", Vector3(66, 8, -26), -15.0, 46.0, 30.0, 45.0)
	view("kharvenn_camp", Vector3(26, 7, -58), 0.0, 50.0, 42.0, 45.0)
	view("jade_gate", Vector3(94, 10, -56), 0.0, 42.0, 30.0, 45.0)
	view("east_road", Vector3(122, 4, 8), -30.0, 44.0, 34.0, 45.0)

# ------------------------------------------------------------------------------------------------------------
# landform

func _noise(x: float, z: float) -> float:
	return sin(x * 0.13 + z * 0.05) * 0.5 + cos(x * 0.047 - z * 0.11) * 0.7 + sin(z * 0.21 + x * 0.17) * 0.25

func _idw(x: float, z: float) -> float:
	var num := 0.0
	var den := 0.0
	for a: Vector3 in ANCHORS:
		var d2 := (x - a.x) * (x - a.x) + (z - a.y) * (z - a.y)
		var w := 1.0 / (d2 * d2 + 900.0)
		num += a.z * w
		den += w
	return num / den

## How much an exit corridor keeps the map-edge hills away (1 on the road out, 0 elsewhere).
func _corridor(x: float, z: float) -> float:
	var p := Vector2(x, z)
	var d := minf(seg_dist(p, WEST_EXIT[0], WEST_EXIT[1]), seg_dist(p, WEST_EXIT[1], WEST_EXIT[2]))
	d = minf(d, minf(seg_dist(p, EAST_EXIT[0], EAST_EXIT[1]), seg_dist(p, EAST_EXIT[1], EAST_EXIT[2])))
	return 1.0 - smoothstep(6.0, 13.0, d)

func _landform(x: float, z: float) -> float:
	var h := _idw(x, z)
	# the jungle climbs into hills on every side: the map's edges read as forested slopes
	var e := maxf(maxf(absf(z) - 84.0, absf(x) - 128.0), 0.0)
	h += minf(e * 0.8, 18.0) * (1.0 - _corridor(x, z)) + smoothstep(0.0, 20.0, e) * _noise(x * 1.7, z * 1.7) * 2.0
	return h

## Distance to the road stubs that run on from the charted road ends to the map edge (the exits).
func _stub_dist(x: float, z: float) -> float:
	var p := Vector2(x, z)
	return minf(seg_dist(p, WEST_EXIT[0], WEST_EXIT[1]), seg_dist(p, EAST_EXIT[1], EAST_EXIT[2]))

## Distance to any route (charted roads, trails, exit stubs) without the 14 m cap of the lattice field.
var _segs: Array = []
func _route_dist(x: float, z: float) -> float:
	if _segs.is_empty():
		for r in DataIsland.roads_on(MAP):
			for i in r.points.size() - 1:
				_segs.append([r.points[i], r.points[i + 1]])
		_segs.append([WEST_EXIT[0], WEST_EXIT[1]])
		_segs.append([EAST_EXIT[1], EAST_EXIT[2]])
	var p := Vector2(x, z)
	var d := INF
	for sg in _segs:
		d = minf(d, seg_dist(p, sg[0], sg[1]))
	return d

func _shape(x: float, z: float, b: float, _rd: float, _rt: int) -> float:
	var h := b + _noise(x, z) * 0.75
	var sd := _stub_dist(x, z)
	if sd < 7.0:
		h = lerpf(b, h, smoothstep(3.0, 6.5, sd))
	for f in FIELDS:
		var q := Vector2(absf(x - f[0]), absf(z - f[1]))
		var inside := 1.0 - smoothstep(0.0, 3.0, maxf(q.x - f[2], q.y - f[3]))
		if inside > 0.0:
			h = lerpf(h, f[4], inside)
	for p in PADS:
		var d := Vector2(x, z).distance_to(Vector2(p[0], p[1]))
		if d < p[2] + 3.0:
			h = lerpf(h, b, 1.0 - smoothstep(p[2] * 0.7, p[2] + 3.0, d))
	# the aqueduct stands on a smooth berm (its spans follow the landform without gaps under the piers)
	var ax := absf(x - AQ_X)
	if ax < 6.0 and z > AQ_Z.x - 4.0 and z < AQ_Z.y + 4.0:
		h = lerpf(h, _idw(AQ_X, z), 1.0 - smoothstep(2.4, 5.5, ax))
	# the cistern: a sunken stone tank by the southern relay
	var cq := Vector2(absf(x - CISTERN.get_center().x), absf(z - CISTERN.get_center().y))
	var cin := 1.0 - smoothstep(-0.6, 0.6, maxf(cq.x - CISTERN.size.x * 0.5, cq.y - CISTERN.size.y * 0.5))
	if cin > 0.0:
		h = lerpf(h, b - 2.6, cin)
	return h

func _splat(x: float, z: float) -> Color:
	var k := _k(x, z)
	var rdd := _rd[k]
	var n := sin(x * 0.41 + z * 0.29) * 0.5 + 0.5
	var n2 := sin(x * 0.9 - z * 0.7) * cos(z * 0.53 + x * 0.2) * 0.5 + 0.5
	# the paved Wirewright road, overgrown: paving broken by moss and roots toward its edges
	if absf(x) > 132.0:
		rdd = minf(rdd, _stub_dist(x, z))
	var road := (1.0 - smoothstep(2.0, 3.6, rdd)) if (_rt[k] == 1 or absf(x) > 132.0) else 0.0
	road *= clampf(0.55 + n2 * 0.7 - smoothstep(1.0, 3.2, rdd) * 0.5, 0.0, 1.0)
	var trail := (1.0 - smoothstep(1.0, 2.2, rdd)) if _rt[k] == 2 else 0.0
	var field := 0.0
	for f in FIELDS:
		if absf(x - f[0]) < f[2] and absf(z - f[1]) < f[3]:
			field = 1.0
	var plaza := 0.0
	for p in PADS:
		var d := Vector2(x, z).distance_to(Vector2(p[0], p[1]))
		plaza = maxf(plaza, (1.0 - smoothstep(float(p[2]) * 0.45, float(p[2]) * 0.8, d)) * (0.55 + n2 * 0.4))
	var r := clampf(maxf(trail, field * (0.45 + n * 0.3)) + n * 0.06, 0.0, 1.0)
	var g := clampf(0.35 + n * 0.5, 0.0, 1.0) * (1.0 - trail) * (1.0 - field * 0.6)
	var bb := clampf(maxf(road, plaza * 0.8), 0.0, 1.0)
	return Color(r * (1.0 - bb), g * (1.0 - bb), bb)

# ------------------------------------------------------------------------------------------------------------
# helpers

## Lowest ground over a footprint (structures stand on it and are never left floating on a slope).
func _foot(c: Vector2, r: float) -> float:
	var m := height_at(c.x, c.y)
	for i in 8:
		var a := TAU * i / 8.0
		m = minf(m, height_at(c.x + cos(a) * r, c.y + sin(a) * r))
	return m

## A transform that lays a piece modelled along local X (length `piece_len`) from a to b, tilted with the ground.
func _xf_along(a: Vector3, b: Vector3, piece_len: float, stretch := 1.0) -> Transform3D:
	var d := b - a
	var l := d.length()
	var ax := d / l
	var ay := (Vector3.UP - ax * ax.y).normalized()
	var az := ax.cross(ay)
	return Transform3D(Basis(ax * (l / piece_len) * stretch, ay, az), (a + b) * 0.5)

func _decor_xf(n: String, t: Transform3D, shadows := false) -> void:
	if not _batches.has(n):
		_batches[n] = {"transforms": [], "shadows": shadows}
	_batches[n].transforms.append(t)

## Pieces modelled along X laid end to end along a polyline: consecutive pieces share their end points exactly, so the
## run is continuous through every bend (each piece is a chord, scaled to its true length).
func _lay(n: String, pts: Array, piece_len: float, y_off: float, trim0 := 0.0, trim1 := 0.0) -> int:
	var total := DataIsland.polyline_length(pts) - trim0 - trim1
	if total <= 0.5:
		return 0
	var count := maxi(1, roundi(total / piece_len))
	var step := total / count
	for i in count:
		var a := DataIsland.point_at(pts, trim0 + i * step)
		var b := DataIsland.point_at(pts, trim0 + (i + 1) * step)
		_decor_xf(n, _xf_along(Vector3(a.x, height_at(a.x, a.y) + y_off, a.y), Vector3(b.x, height_at(b.x, b.y) + y_off, b.y), piece_len, 1.01))
	return count

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
	return _rd[k] < (road_pad if _rt[k] == 1 else trail_pad)

# ------------------------------------------------------------------------------------------------------------
# edges and exits

func _edges() -> void:
	# the map edge: a collision line all round, open only where the two roads leave
	boundary(Vector3(-140, -6, -100), Vector3(140, -6, -100), 40.0)
	boundary(Vector3(-140, -6, 100), Vector3(140, -6, 100), 40.0)
	boundary(Vector3(-140, -6, -100), Vector3(-140, -6, 24.5), 40.0)
	boundary(Vector3(-140, -6, 35.5), Vector3(-140, -6, 100), 40.0)
	boundary(Vector3(140, -6, -100), Vector3(140, -6, 3.0), 40.0)
	boundary(Vector3(140, -6, 14.0), Vector3(140, -6, 100), 40.0)
	corridor_rails([Vector2(-142, 30.0), Vector2(-136, 30.0), Vector2(-128, 27.0)], 5.5)
	corridor_rails([Vector2(124, 6.0), Vector2(136, 8.0), Vector2(142, 9.0)], 5.5)
	exit_zone(&"coilwood_agdao_road", Vector3(-138.6, 0, 30.0), Vector3(2.6, 4.0, 10.0), &"agdao", &"coil_gate", "Agdao")
	exit_zone(&"coilwood_barrens_road", Vector3(138.6, 0, 8.6), Vector3(2.6, 4.0, 10.0), &"zr_barrens", &"coil_road", "the Glasswire Barrens")
	# old Wirewright road markers at both ends: a pair of serpent statues on the verge and a signpost
	for e in [[Vector2(-128, 27.2), 90.0], [Vector2(127, 7.0), -90.0]]:
		var c: Vector2 = e[0]
		var yaw: float = e[1]
		var side := Vector2(cos(deg_to_rad(yaw)), -sin(deg_to_rad(yaw)))
		for s: float in [-1.0, 1.0]:
			var q := c + side * 6.0 * s
			_on("zr_serpent_statue", q, yaw, 1.0, 1.0, geo)
	signpost_bed(Vector2(-125.5, 33.5), [["Agdao", Vector2(-1, 0.1)], ["The Overgrown Shrine", Vector2(1, -0.4)],
		["The Relay Lines", Vector2(1, -0.2)]])
	signpost_bed(Vector2(124.0, 13.5), [["The Glasswire Barrens", Vector2(1, 0.1)], ["The Relay Lines", Vector2(-1, -0.1)],
		["Agdao", Vector2(-1, 0.15)]])

# ------------------------------------------------------------------------------------------------------------
# the overgrown shrine and its waypoint

func _shrine() -> void:
	var c := SHRINE
	var half := 4.2 * SHRINE_S
	var y := _foot(c, half) - 0.05
	kit("zr_ruin_shrine", Vector3(c.x, y, c.y), 0.0, SHRINE_S, geo)
	# the base top (collision) is 1.4 m, scaled; the waypoint dais stands in front of the altar
	var top := y + 1.4 * SHRINE_S
	teleporter(&"coil_shrine", Vector3(c.x, top + 0.04, c.y + 0.35), &"agdao", &"agdao_shrine", "Agdao", 0.0)
	spawn(&"coil_shrine", Vector3(c.x + 1.2, top + 0.05, c.y + 4.3), 0.0)
	# glyph steles at the base's front corners, braziers either side of the stair foot
	for s: float in [-1.0, 1.0]:
		_on("zr_glyph_stele", Vector2(c.x + s * (half + 1.4), c.y + half - 0.6), 0.0, 1.0, 1.0, geo)
		_brazier(Vector2(c.x + s * 2.9, c.y + half + 3.4), 2.6)
	light(Vector3(c.x, top + 2.6, c.y), Color(0.45, 0.85, 1.0), 1.6, 10.0)
	# the waypoint line: the shrine's own wire channel runs on down the stair to the road
	keep_clear(c.x, c.y, half + 3.0)

# ------------------------------------------------------------------------------------------------------------
# the broken aqueduct (spans tilt with the berm, so every pier stands on the ground and the channel is continuous)

func _aqueduct() -> void:
	var n := int(round((AQ_Z.y - AQ_Z.x) / 4.0))
	var vines := 0
	for i in n:
		var z0 := AQ_Z.x + i * 4.0
		var z1 := z0 + 4.0
		var fallen := false
		for g in AQ_GAPS:
			if z1 > g[0] and z0 < g[1]:
				fallen = true
		if fallen:
			# fallen spans: rubble and a toppled block in the gap
			if rng.randf() < 0.7:
				decor("rubble_pile", Vector3(AQ_X + rng.randf_range(2.5, 4.0) * (1.0 if i % 2 else -1.0), 0, z0 + 2.0), rng.randf() * 360.0, 1.1, true, true)
			continue
		var a := Vector3(AQ_X, height_at(AQ_X, z0) - 0.12, z0)
		var b := Vector3(AQ_X, height_at(AQ_X, z1) - 0.12, z1)
		var t := _xf_along(a, b, 4.0)
		var piece := kit("zr_aqueduct_4m", t.origin, 0.0, 1.0, geo)
		piece.transform = t
		if i % 3 == 1 and vines < 9:
			vines += 1
			# a vine curtain hangs from the frieze on the camera (east, +X) face
			var vt := Transform3D(Basis(Vector3.UP, deg_to_rad(90.0)), t.origin + Vector3(1.06, 0.0, 0.0))
			_decor_xf("zr_vine_curtain", vt.scaled_local(Vector3(0.95, 1.0, 1.0)))
	# the north end runs into the hillside; the south end is a broken stub over a rubble fan
	decor("rubble_pile", Vector3(AQ_X + 1.0, 0, AQ_Z.y + 2.5), 20.0, 1.4, true, true)
	decor("zr_rock_ochre_medium", Vector3(AQ_X - 2.0, 0, AQ_Z.y + 3.5), 70.0, 1.0, true, true)
	decor("rubble_pile", Vector3(AQ_X - 0.5, 0, AQ_Z.x - 2.5), 200.0, 1.3, true, true)

# ------------------------------------------------------------------------------------------------------------
# the step-fields: ruined glyph walls hold the terrace banks; agave and ferns grow where the crops were

func _fields() -> void:
	for f in FIELDS:
		var cx: float = f[0]
		var cz: float = f[1]
		var hx: float = f[2]
		var hz: float = f[3]
		# retaining walls along the lower (south) edge, broken, with gaps where a trail climbs through
		var x := cx - hx + 2.2
		while x < cx + hx - 1.0:
			var p := Vector2(x, cz + hz + 1.2)
			if not _near_route(p.x, p.y, 7.0, 5.0) and rng.randf() < 0.88:
				_on("zr_ruin_wall", p, 0.0 if rng.randf() < 0.6 else 180.0, rng.randf_range(0.82, 1.0), 2.0, geo, 0.25)
			x += 4.6
		# crop rows gone wild
		for i in int(hx * hz * 0.5):
			var q := Vector2(cx + rng.randf_range(-hx, hx), cz + rng.randf_range(-hz, hz))
			if _near_route(q.x, q.y, 5.0, 3.0):
				continue
			decor("zr_agave" if rng.randf() < 0.55 else "grass_clump", Vector3(q.x, 0, q.y), rng.randf() * 360.0, rng.randf_range(0.7, 1.15))

# ------------------------------------------------------------------------------------------------------------
# the cistern by the southern relay

func _cistern() -> void:
	var r := CISTERN
	var c := r.get_center()
	var wy := height_at(c.x, c.y) + 1.5
	water(Rect2(r.position.x - 0.5, r.position.y - 0.5, r.size.x + 1.0, r.size.y + 1.0), wy, Color(0.1, 0.32, 0.26), Color(0.02, 0.06, 0.05), 0.4, 2.0, 0.15)
	# a stone rim all round (the tank is closed: its walls are the colliders)
	for side in 4:
		var horiz := side < 2
		var length := r.size.x if horiz else r.size.y
		var n := maxi(1, roundi(length / 4.0))
		for i in n:
			var t := (i + 0.5) / n
			var p: Vector2
			if side == 0:
				p = Vector2(r.position.x + t * r.size.x, r.position.y - 0.4)
			elif side == 1:
				p = Vector2(r.position.x + t * r.size.x, r.end.y + 0.4)
			elif side == 2:
				p = Vector2(r.position.x - 0.4, r.position.y + t * r.size.y)
			else:
				p = Vector2(r.end.x + 0.4, r.position.y + t * r.size.y)
			var yaw := (0.0 if side == 1 else 180.0) if horiz else (90.0 if side == 3 else -90.0)
			var sc := length / n / 4.4 * 1.06
			var y := minf(height_at(p.x, p.y), wy - 0.6)
			var w := kit("zr_ruin_wall", Vector3(p.x, y - 0.3, p.y), yaw, 1.0, geo)
			w.scale = Vector3(sc, 0.7 if side == 1 else 0.9, 1.0)
	mist(Rect2(r.position.x - 24.0, r.position.y - 18.0, 60.0, 40.0), height_at(c.x, c.y) + 2.2, Color(0.42, 0.5, 0.48), 0.4)

# ------------------------------------------------------------------------------------------------------------
# the Heartwire relay lines: wire channels inlaid down the road and the trails, carrier pylons on the verge

func _relay_lines() -> void:
	var main: Array = []
	for id: String in ["zc_road", "zc_road_2", "zc_road_3"]:
		var pts: Array = DataIsland.road(id).points
		if main.is_empty():
			main.append_array(pts)
		else:
			main.append_array(pts.slice(1))
	_lay("zr_wire_conduit_4m", main, 4.0, 0.045, 3.0, 2.5)
	for id: String in ["zc_relay1_trail", "zc_relay2_trail", "zc_relay3_trail"]:
		var pts: Array = DataIsland.road(id).points
		_lay("zr_wire_conduit_4m", pts, 4.0, 0.045, 2.5 if id != "zc_relay1_trail" else 0.5, 2.6)
	# the shrine's line down its stair to the road
	_lay("zr_wire_conduit_4m", [Vector2(SHRINE.x, SHRINE.y + 6.4 * SHRINE_S + 0.1), Vector2(SHRINE.x, 17.6)], 4.0, 0.045)
	# carrier pylons beside the main line (dead relays now: only the Blackwire pulses in their coils)
	var total := DataIsland.polyline_length(main)
	var along := 22.0
	var side := 1.0
	while along < total - 12.0:
		var a := DataIsland.point_at(main, along)
		var b := DataIsland.point_at(main, along + 1.0)
		var dir := (b - a).normalized()
		var o := a + Vector2(-dir.y, dir.x) * 4.6 * side
		if is_clear(o.x, o.y, 1.0) and absf(o.x - AQ_X) > 5.0:
			_on("zr_wire_pylon", o, _yaw_to(o, a), 1.0, 0.9, props, 0.1)
		along += 34.0
		side = -side
	# where the lines meet: a ring of steles round the junction of the Relay Lines
	for i in 5:
		var ang := TAU * (i + 0.35) / 5.0
		var p := Vector2(10, 0) + Vector2(cos(ang), sin(ang)) * 7.4
		if not _near_route(p.x, p.y, 4.6, 3.2):
			_on("zr_glyph_stele", p, _yaw_to(p, Vector2(10, 0)), 0.9, 1.0, geo)
	light(Vector3(10, height_at(10, 0) + 1.5, 0), Color(1.0, 1.0, 1.0), 2.2, 12.0)
	signpost_bed(Vector2(14.5, 6.5), [["Agdao", Vector2(-1, 0.1)], ["Western Relay", Vector2(-1, -0.6)], ["Southern Relay", Vector2(0.15, 1)],
		["Eastern Relay", Vector2(1, -0.5)], ["The Glasswire Barrens", Vector2(1, 0)]])
	signpost_bed(Vector2(-55.0, 15.5), [["Agdao", Vector2(-1, 0.2)], ["Western Relay", Vector2(0, -1)], ["The Relay Lines", Vector2(1, -0.2)]])

# ------------------------------------------------------------------------------------------------------------
# the three chained relay pylons and their guard camps

func _relays() -> void:
	var trails := ["zc_relay1_trail", "zc_relay2_trail", "zc_relay3_trail"]
	for i in 3:
		var c: Vector2 = DataZarael.CW_RELAYS[i]
		var pts: Array = DataIsland.road(trails[i]).points
		var from: Vector2 = pts[pts.size() - 2]
		var yaw := _yaw_to(c, from)
		var y := _foot(c, 1.6) - 0.62
		var at := Vector3(c.x, y, c.y)
		kit("zr_relay_pylon", at, yaw, 1.0, geo)
		hide_when(kit("zr_relay_chains", at, yaw, 1.0, deco), DataZarael.RELAY_FLAGS[i])
		var rp := RelayPylon.new().setup(i + 1)
		rp.position = at
		markers.add_child(rp)
		keep_clear(c.x, c.y, 6.0)
		# the Kharvenn ring of rune-spikes round it, a tent and a chain rack, two braziers
		for k in 7:
			var ang := TAU * (k + 0.5) / 7.0 + i
			var q := c + Vector2(cos(ang), sin(ang)) * 6.2
			if _near_route(q.x, q.y, 4.0, 3.2):
				continue
			_on("zr_chain_spike", q, rng.randf() * 360.0, rng.randf_range(0.85, 1.1), 0.6, props, 0.1)
		var back := (c - from).normalized()
		var side := Vector2(-back.y, back.x)
		var tent := c + back * 7.5 + side * 5.5
		_on("zr_kharvenn_tent", tent, _yaw_to(tent, c), 1.0, 2.1, props, 0.08)
		var rack := c + back * 6.0 - side * 6.5
		_on("zr_chain_rack", rack, _yaw_to(rack, c) + 90.0, 1.0, 1.6, props, 0.05)
		_brazier(c + side * 4.2 - back * 2.0, 2.8)
		_brazier(c - side * 4.2 - back * 2.0, 2.8)
		for q in [tent, rack]:
			keep_clear(q.x, q.y, 3.0)

# ------------------------------------------------------------------------------------------------------------
# the Kharvenn camp on the rise north of the Relay Lines

func _kharvenn_camp() -> void:
	var c := DataZarael.CW_CAMP
	var from := Vector2(26, -44)
	keep_clear(c.x, c.y, 17.0)
	# a stockade of rune-spikes and chain racks round the camp, open toward the Chain trail
	var n := 22
	for i in n:
		var ang := TAU * (i + 0.5) / n
		var q := c + Vector2(cos(ang), sin(ang)) * 14.5
		if q.distance_to(from) < 7.5 or _near_route(q.x, q.y, 4.0, 3.4):
			continue
		if i % 4 == 2:
			_on("zr_chain_rack", q, rad_to_deg(-ang) + 90.0 + 90.0, 1.0, 1.6, props, 0.05)
		else:
			_on("zr_chain_spike", q, rng.randf() * 360.0, rng.randf_range(1.0, 1.3), 0.7, props, 0.12)
	# iron tents in a half ring on the north side, their open fronts toward the fire square
	for t in [[-8.0, -5.0], [-3.0, -9.0], [3.5, -9.0], [8.5, -5.0], [-9.5, 2.5], [9.5, 2.5]]:
		var p := c + Vector2(t[0], t[1])
		_on("zr_kharvenn_tent", p, _yaw_to(p, c), 1.0, 2.1, props, 0.08)
	for r in [[-4.5, 4.5, 30.0], [5.0, 5.0, -35.0], [0.0, -3.5, 90.0]]:
		_on("zr_chain_rack", c + Vector2(r[0], r[1]), r[2], 1.0, 1.6, props, 0.05)
	_brazier(c + Vector2(-3.0, 1.0), 3.6, true)
	_brazier(c + Vector2(3.0, 1.0), 3.0)
	_brazier(c + Vector2(-6.0, 9.0), 2.8)
	_brazier(c + Vector2(6.0, 9.0), 2.8)
	for p in [Vector2(-2.0, 7.0), Vector2(2.4, 7.4), Vector2(-7.0, -1.0)]:
		decor("bones_scatter", Vector3(c.x + p.x, 0, c.y + p.y), rng.randf() * 360.0, 1.0)
	decor("weapons_discarded", Vector3(c.x + 6.5, 0, c.y - 1.5), 40.0, 1.0)

# ------------------------------------------------------------------------------------------------------------
# the Jade Sepulchre gate, framed by ruins and ferns

func _gates() -> void:
	for gid in DataDungeons.gates_on(MAP):
		var gs: Dictionary = DataDungeons.get_def(gid).surface
		var p: Vector2 = gs.pos
		var yaw: float = gs.yaw
		dungeon_gate(gid, p, yaw)
		keep_clear(p.x, p.y, 9.0)
		var fwd := Vector2(sin(deg_to_rad(yaw)), cos(deg_to_rad(yaw)))
		var side := Vector2(fwd.y, -fwd.x)
		# broken walls either side of the serpent's head, columns, and the jungle closing in behind it
		for s: float in [-1.0, 1.0]:
			var wp := p - fwd * 4.2 + side * s * 8.4
			if not _near_route(wp.x, wp.y, 5.0, 4.0):
				_on("zr_ruin_wall", wp, yaw + (180.0 if s > 0 else 0.0), 1.0, 2.0, geo, 0.25)
			var cp := p + fwd * 1.5 + side * s * 7.6
			if not _near_route(cp.x, cp.y, 4.0, 3.0):
				_on("zr_ruin_column", cp, yaw + s * 30.0, 1.0, 0.8, geo, 0.1)
			decor("zr_fern_giant", Vector3(p.x - fwd.x * 1.0 + side.x * s * 6.8, 0, p.y - fwd.y * 1.0 + side.y * s * 6.8), rng.randf() * 360.0, 1.1)
			decor("zr_bush_jungle", Vector3(p.x + fwd.x * 4.5 + side.x * s * 6.2, 0, p.y + fwd.y * 4.5 + side.y * s * 6.2), rng.randf() * 360.0, 0.9)
		for k in 6:
			var q := p + Vector2(rng.randf_range(-12.0, 12.0), -rng.randf_range(9.0, 14.0))
			if _near_route(q.x, q.y, 8.0, 6.0):
				continue
			decor("zr_palm" if k % 2 == 0 else "zr_fern_giant", Vector3(q.x, 0, q.y), rng.randf() * 360.0, rng.randf_range(0.85, 1.1), true, true)

# ------------------------------------------------------------------------------------------------------------
# ruins in the jungle: columns, steles, broken walls

func _ruins() -> void:
	var spots := [
		[Vector2(-30, 14), "zr_ruin_column"], [Vector2(-34, -2), "zr_ruin_wall"], [Vector2(28, 14), "zr_ruin_column"],
		[Vector2(-10, -16), "zr_ruin_wall"], [Vector2(46, 12), "zr_glyph_stele"], [Vector2(-96, 26), "zr_ruin_column"],
		[Vector2(-116, -14), "zr_ruin_wall"], [Vector2(-104, 40), "zr_ruin_wall"], [Vector2(70, 22), "zr_ruin_column"],
		[Vector2(94, -8), "zr_glyph_stele"], [Vector2(114, -14), "zr_ruin_wall"], [Vector2(40, 34), "zr_ruin_wall"],
		[Vector2(-60, 44), "zr_ruin_column"], [Vector2(-40, 60), "zr_ruin_wall"], [Vector2(76, 70), "zr_ruin_column"],
		[Vector2(4, -36), "zr_glyph_stele"], [Vector2(-130, 4), "zr_ruin_column"], [Vector2(118, 40), "zr_glyph_stele"],
	]
	for s in spots:
		var p: Vector2 = s[0]
		if _near_route(p.x, p.y, 6.0, 4.0) or not is_clear(p.x, p.y, 2.0):
			continue
		var nm: String = s[1]
		var w := _on(nm, p, rng.randf_range(-25.0, 25.0) + (0.0 if rng.randf() < 0.7 else 180.0), 1.0, 1.4 if nm == "zr_ruin_wall" else 0.8, geo, 0.2)
		if nm == "zr_ruin_wall" and rng.randf() < 0.6:
			# vines over the tall end of the wall (local x -2.2 .. 0.2, where its top stays above the curtain)
			var t := w.transform * Transform3D(Basis.IDENTITY.scaled(Vector3(0.6, 0.6, 0.6)), Vector3(-1.0, 0.0, 0.48))
			_decor_xf("zr_vine_curtain", t)
		keep_clear(p.x, p.y, 3.0)

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
# mist in the hollows, Blackwire glow in the wood

func _atmosphere() -> void:
	mist(Rect2(-60, 46, 70, 44), 2.4, Color(0.4, 0.42, 0.5), 0.35)
	mist(Rect2(30, 30, 70, 40), 3.0, Color(0.42, 0.4, 0.5), 0.3)
	mist(Rect2(-140, 40, 60, 50), 2.2, Color(0.4, 0.42, 0.5), 0.3)
	mist(Rect2(-120, -70, 40, 30), 8.0, Color(0.42, 0.4, 0.52), 0.28)
	# a few pale pools of light where the Blackwire runs warm under the roots
	for p: Vector2 in [Vector2(-34, 40), Vector2(48, 26), Vector2(-118, 46), Vector2(104, -30), Vector2(-26, -40)]:
		light(Vector3(p.x, height_at(p.x, p.y) + 1.2, p.y), Color(1.0, 1.0, 1.0), 1.4, 9.0)
		decor("zr_glass_growth", Vector3(p.x, 0, p.y), rng.randf() * 360.0, 0.55, true, true)

# ------------------------------------------------------------------------------------------------------------
# the jungle

func _blocked(x: float, z: float, road_pad := 6.0, trail_pad := 4.0) -> bool:
	if _near_route(x, z, road_pad, trail_pad):
		return true
	if not is_clear(x, z, 1.5):
		return true
	if absf(x - AQ_X) < 4.5 and z > AQ_Z.x - 3.0 and z < AQ_Z.y + 3.0:
		return true
	if x > CISTERN.position.x - 3.0 and x < CISTERN.end.x + 3.0 and z > CISTERN.position.y - 3.0 and z < CISTERN.end.y + 3.0:
		return true
	return _stub_dist(x, z) < 7.0

func _in_field(x: float, z: float, pad := 2.0) -> bool:
	for f in FIELDS:
		if absf(x - f[0]) < f[2] + pad and absf(z - f[1]) < f[3] + pad:
			return true
	return false

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

func _greenery() -> void:
	# a giant tree's crown (12-18 m up) hides whatever lies 4-20 m north of its trunk from the game camera (which looks
	# north from 14 m south of the hero, 19 m up): none stands south of a road, trail, camp or landmark within that reach
	var tree_free := func(x: float, z: float) -> bool:
		if _in_field(x, z, 6.0):
			return true
		for k: float in [0.0, 7.0, 14.0, 21.0]:
			if _route_dist(x, z - k) < (16.0 if k == 0.0 else 10.0) or not is_clear(x, z - k, 9.0):
				return true
		return _blocked(x, z, 15.0, 10.0)
	var under := func(x: float, z: float) -> bool:
		return _blocked(x, z) or _in_field(x, z, 0.5)
	var bounds := Rect2(-152, -112, 304, 224)
	# efficiency mode (bh-009) keeps about half the jungle (MapBuilder.LITE_KEEP only thins the old kit's names)
	var lite := 0.5 if Perf.lite else 1.0
	# giant buttress trees well back from the paths (their crowns would hide the hero), palms and tree ferns nearer
	var ceibas := _scatter(["zr_tree_ceiba"], bounds, int(190 * lite), 11.0, Vector2(0.8, 1.15), tree_free, true)
	var palms := _scatter(["zr_palm", "zr_palm", "zr_fern_giant"], bounds, int(400 * lite), 4.8, Vector2(0.8, 1.25),
		func(x: float, z: float) -> bool: return _blocked(x, z, 6.5, 4.5) or _in_field(x, z, 1.0), true)
	for t in ceibas:
		if road_dist(t.x, t.z) < 26.0 and absf(t.x) < 138.0 and absf(t.z) < 98.0:
			blocker(Vector3(t.x, height_at(t.x, t.z) + 2.0, t.z), Vector3(3.0, 4.0, 3.0))
	for t in palms:
		if road_dist(t.x, t.z) < 12.0:
			blocker(Vector3(t.x, height_at(t.x, t.z) + 1.5, t.z), Vector3(0.7, 3.0, 0.7))
	_scatter(["zr_bush_jungle", "zr_bush_jungle", "fern", "fern"], bounds, int(560 * lite), 2.8, Vector2(0.7, 1.25), under)
	_scatter(["zr_agave", "fern", "mushrooms", "roots"], bounds, 260, 2.6, Vector2(0.7, 1.1), under)
	_scatter(["zr_rock_ochre_medium", "log_fallen", "stump"], bounds, 40, 9.0, Vector2(0.7, 1.1), under, true)
	# the forested hills round the edge: palms, tree ferns and bushes thick on the slopes
	var edge := func(x: float, z: float) -> bool:
		return maxf(absf(z) - 86.0, absf(x) - 130.0) < 0.0 or _stub_dist(x, z) < 8.0
	_scatter(["zr_palm", "zr_fern_giant", "zr_bush_jungle", "zr_bush_jungle"], bounds, int(340 * lite), 3.8, Vector2(0.9, 1.35), edge)
	# undergrowth carpet (no spacing rule: scatter's spacing check is quadratic in the count)
	var placed := 0
	var tries := 0
	while placed < int(1500 * lite) and tries < 8000:
		tries += 1
		var x := -150.0 + rng.randf() * 300.0
		var z := -110.0 + rng.randf() * 220.0
		if _near_route(x, z, 3.2, 2.0) or not is_clear(x, z, 0.0):
			continue
		decor("grass_clump", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.9, 1.5))
		placed += 1

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the jungle's groups and transitions — moss and rock where the ground breaks, fallen
# trunks under the canopy, the aqueduct's fallen stones beside the road it once crossed, an offering at the shrine's
# foot and a threshold of memorial urns before the Jade Sepulchre. The shrine and relay pylons stay clear of the trail
# view; nothing glows (all relay light stays the island's white).

func _clear_here(x: float, z: float, r: float) -> bool:
	return not _blocked(x, z, r + 3.0, r + 2.0) and not _in_field(x, z, r)

func _map_design() -> void:
	clear_fn = _clear_here
	var sh := Vector3(SHRINE.x, 0, SHRINE.y)
	place_near("offering", sh + Vector3(6.0, 0, 8.0), sh, 9.0, 15.0, 0.0)
	var jade: Vector2 = DataDungeons.get_def(&"jade_sepulchre").surface.pos
	place_near("jade_threshold", Vector3(jade.x - 2.0, 0, jade.y + 7.0), Vector3(jade.x, 0, jade.y), 8.0, 15.0, 200.0)
	# the aqueduct's fallen spans: stones and a toppled column on the verges either side of the gap the road uses
	for c in [[Vector3(AQ_X - 5.5, 0, 9.0), 0.0], [Vector3(AQ_X + 5.8, 0, 19.0), 120.0], [Vector3(AQ_X - 5.0, 0, -20.0), 60.0]]:
		kit("kd_debris_stone", c[0], c[1], 1.5, deco, true)
	var col := kit("kd_column", Vector3(AQ_X + 6.5, 0.5, 12.0), 15.0, 0.9, deco, true)
	col.rotation = Vector3(0, deg_to_rad(15.0), deg_to_rad(84.0))
	for q in [Vector3(-40.0, 0, 30.0), Vector3(40.0, 0, -6.0), Vector3(-20.0, 0, -60.0)]:
		place_near("fallen_tree", q, q, 0.0, 12.0, rng.randf() * 360.0)
	for q in [Vector3(-70.0, 0, 34.0), Vector3(10.0, 0, 24.0), Vector3(60.0, 0, 30.0), Vector3(-30.0, 0, -30.0)]:
		place_near("rock_cluster_m", q, q, 0.0, 12.0, rng.randf() * 360.0)
	for q in [Vector3(-60.0, 0, 10.0), Vector3(30.0, 0, 10.0)]:
		place_near("palm_group", q, q, 0.0, 14.0, rng.randf() * 360.0)
