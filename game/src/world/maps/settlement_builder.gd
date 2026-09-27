class_name SettlementBuilder
extends MapBuilder
## Shared helpers for the walled settlements outside Malasugue (bh-007: Olivar and Wyman Outpost): a terrain lattice
## with the road beds of DataIsland flattened into it (the same polylines the atlas draws and the route planner
## walks), palisade runs with gate gaps, collision rails along road corridors, footprint-aware greenery, and the
## walk-through boundaries to neighbouring districts.

var X0 := -70.0
var Z0 := -70.0
var W := 140
var D := 140
var _gw := 141
var _rd := PackedFloat32Array()     # distance to the nearest road/trail centre line
var _rt := PackedByteArray()        # 1 road, 2 trail
var _bed := PackedFloat32Array()    # road-bed height (smooth landform) per lattice vertex
var _h := PackedFloat32Array()      # final height per lattice vertex
## Footprints kept clear of grass, trees and bushes: [centre x, z, radius].
var clear_spots: Array = []

func _i(ix: int, iz: int) -> int:
	return iz * _gw + ix

func _k(x: float, z: float) -> int:
	return _i(clampi(roundi(x - X0), 0, W), clampi(roundi(z - Z0), 0, D))

## Build the lattice: `landform(x, z)` is the smooth ground, `shape(x, z, landform, road_distance, road_type)` the final
## height (roads are levelled onto the landform by this helper afterwards).
func prepare(x0: float, z0: float, w: int, d: int, landform: Callable, shape: Callable) -> void:
	X0 = x0
	Z0 = z0
	W = w
	D = d
	_gw = W + 1
	var n := _gw * (D + 1)
	_rd.resize(n)
	_rd.fill(99.0)
	_rt.resize(n)
	_bed.resize(n)
	_h.resize(n)
	for r in DataIsland.roads_on(def.id):
		raster_line(r.points, _rd, 14.0, _rt, 1 if r.type == "road" else 2)
	for iz in D + 1:
		for ix in _gw:
			var k := _i(ix, iz)
			var x := X0 + ix
			var z := Z0 + iz
			_bed[k] = landform.call(x, z)
			var h: float = shape.call(x, z, _bed[k], _rd[k], _rt[k])
			var half := 3.0 if _rt[k] == 1 else 1.7
			_h[k] = lerpf(_bed[k], h, smoothstep(half, half + 3.5, _rd[k]))

func raster_line(pts: Array, field: PackedFloat32Array, reach: float, types := PackedByteArray(), type := 0) -> void:
	for s in pts.size() - 1:
		var a: Vector2 = pts[s]
		var b: Vector2 = pts[s + 1]
		var x0 := clampi(int(floor(minf(a.x, b.x) - reach - X0)), 0, W)
		var x1 := clampi(int(ceil(maxf(a.x, b.x) + reach - X0)), 0, W)
		var z0 := clampi(int(floor(minf(a.y, b.y) - reach - Z0)), 0, D)
		var z1 := clampi(int(ceil(maxf(a.y, b.y) + reach - Z0)), 0, D)
		for iz in range(z0, z1 + 1):
			for ix in range(x0, x1 + 1):
				var dd := seg_dist(Vector2(X0 + ix, Z0 + iz), a, b)
				var k := _i(ix, iz)
				if dd < field[k]:
					field[k] = dd
					if type > 0:
						types[k] = type

static func seg_dist(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var l2 := ab.length_squared()
	if l2 < 0.0001:
		return p.distance_to(a)
	return p.distance_to(a + ab * clampf((p - a).dot(ab) / l2, 0.0, 1.0))

func height_at(x: float, z: float) -> float:
	var fx := clampf(x - X0, 0.0, W - 0.001)
	var fz := clampf(z - Z0, 0.0, D - 0.001)
	var ix := int(fx)
	var iz := int(fz)
	var tx := fx - ix
	var tz := fz - iz
	var a := lerpf(_h[_i(ix, iz)], _h[_i(ix + 1, iz)], tx)
	var b := lerpf(_h[_i(ix, iz + 1)], _h[_i(ix + 1, iz + 1)], tx)
	return lerpf(a, b, tz)

func road_dist(x: float, z: float) -> float:
	return _rd[_k(x, z)]

func road_type(x: float, z: float) -> int:
	return _rt[_k(x, z)]

func bed(x: float, z: float) -> float:
	return _bed[_k(x, z)]

## Palisade stakes from a to b (4 m pieces), leaving `gaps` ([centre along the run in metres, half width]) open.
func palisade_run(a: Vector2, b: Vector2, gaps: Array = [], solid := true) -> void:
	var run_len := a.distance_to(b)
	var dir := (b - a) / maxf(run_len, 0.001)
	var yaw := rad_to_deg(atan2(-dir.y, dir.x))
	var n := maxi(1, int(round(run_len / 4.0)))
	var step := run_len / n
	for i in n:
		var t := (i + 0.5) * step
		var open := false
		for g in gaps:
			if absf(t - float(g[0])) < float(g[1]) + step * 0.5 - 0.2:
				open = true
		if open:
			continue
		var p := a + dir * t
		kit("palisade_fence", Vector3(p.x, 0, p.y), yaw, step / 4.0 * 1.01, props, true)
	if not solid:
		return
	# collision just inside the stakes, split around the gaps
	var cuts := [0.0]
	for g in gaps:
		cuts.append(float(g[0]) - float(g[1]))
		cuts.append(float(g[0]) + float(g[1]))
	cuts.append(run_len)
	for i in range(0, cuts.size(), 2):
		var s0: float = cuts[i]
		var s1: float = cuts[i + 1]
		if s1 - s0 < 0.3:
			continue
		var pa := a + dir * s0
		var pb := a + dir * s1
		boundary(Vector3(pa.x, ground(pa.x, pa.y) - 1.0, pa.y), Vector3(pb.x, ground(pb.x, pb.y) - 1.0, pb.y), 8.0, 0.8)

## A gatehouse over a road: two quoined pillars, an arch, braziers and hanging banners.
func gatehouse(c: Vector2, yaw_deg: float, banner := "banner_torn") -> void:
	var fwd := Vector2(sin(deg_to_rad(yaw_deg)), cos(deg_to_rad(yaw_deg)))
	var side := Vector2(fwd.y, -fwd.x)
	var y := ground(c.x, c.y)
	for sx: float in [-3.2, 3.2]:
		var p := c + side * sx
		kit("pillar_quoin", Vector3(p.x, y, p.y), yaw_deg, 1.0, geo)
		kit(banner, Vector3(p.x, y + 3.6, p.y) + Vector3(fwd.x, 0, fwd.y) * 0.75, yaw_deg, 1.0, deco)
	kit("arch_quoin", Vector3(c.x, y, c.y), yaw_deg, 1.0, geo)
	for sx: float in [-5.2, 5.2]:
		var p := c + side * sx + fwd * 1.6
		brazier(Vector3(p.x, 0, p.y), 3.0, false, true)

## Rails along both sides of a road corridor outside a gate (keeps the hero on the road to the boundary).
func corridor_rails(pts: Array, half: float) -> void:
	for sgn: float in [-1.0, 1.0]:
		for i in pts.size() - 1:
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			var dir := (b - a).normalized()
			var off := Vector2(-dir.y, dir.x) * half * sgn
			boundary(Vector3(a.x + off.x, ground(a.x, a.y) - 2.0, a.y + off.y), Vector3(b.x + off.x, ground(b.x, b.y) - 2.0, b.y + off.y), 10.0, 0.6)

func is_clear(x: float, z: float, pad := 0.0) -> bool:
	for c in clear_spots:
		if Vector2(x, z).distance_to(Vector2(c[0], c[1])) < float(c[2]) + pad:
			return false
	return true

func keep_clear(x: float, z: float, r: float) -> void:
	clear_spots.append([x, z, r])

## Lamp posts along a road every `every` metres, alternating sides.
func road_lamps(road_id: String, every := 22.0, off := 4.0, start := 8.0) -> void:
	var pts: Array = DataIsland.road(road_id).points
	var total := DataIsland.polyline_length(pts)
	var along := start
	var side := 1.0
	while along < total - 4.0:
		var a := DataIsland.point_at(pts, along)
		var b := DataIsland.point_at(pts, along + 1.0)
		var dir := (b - a).normalized()
		var o := Vector2(-dir.y, dir.x) * off * side
		if is_clear(a.x + o.x, a.y + o.y, 1.0):
			lamp_post(Vector3(a.x + o.x, 0, a.y + o.y), rad_to_deg(atan2(-o.x, -o.y)))
		along += every
		side = -side

func signpost_bed(p: Vector2, arms: Array) -> Node3D:
	return signpost(p, arms, height_at(p.x, p.y))
