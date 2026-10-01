extends SettlementBuilder
## MAP — Wyman Outpost, the hero camp on a rise above Reedwater Marsh (bh-007; safe zone, provisional name set by the
## author). The Watch Road comes down from Olivar to its north gate; the Fen Road runs west over the Fen Bridge to
## Lantern Fields (Westreach).
##
## A round stockade around a great bonfire (the checkpoint: rest free, wake here after a fall). Around the fire: the
## heroes' tents with their guild banners, the commander's lodge, the Hero Register board, the quartermaster's stall,
## Greta Stonehand's field forge, a workbench, the healer's camp kettle, a training yard with dummies, a watchtower,
## the waypoint and, on the east side, the Marsh Overlook above the reeds and black water of Reedwater Marsh.
## bh-028: south of the Fen Road, a lane leads to the Sand Arena: a ring of sand inside a palisade, with spectator
## galleries on two sides, where heroes and wandering adventurers fight each other (ArenaGrounds).

const R := 31.0                          # stockade radius
const ARENA := Vector2(-35, 44)          # bh-028: the Sand Arena
const ARENA_R := 20.0
const ARENA_Y := 0.0                     # the flattened ground under the sand
const SAND_Y := 0.14                     # the top of the sand
const ARENA_GATE_HALF := 9.5             # degrees either side of the gate left open in the palisade
const ARENA_LANE := 4.0                  # half width of the lane from the Fen Road to the gate
## Degrees around the arena (atan2(z, x) from its centre) of the gate (north, towards the road) and the fighters' door.
const ARENA_GATE_DEG := -90.0
const ARENA_DOOR_DEG := 90.0
const BONFIRE := Vector2(-4, -2)
const MARSH_X := 36.0
const MARSH_Y := -1.35
const LODGE := Vector2(-6, -22)
const REGISTER := Vector2(-8, -9.4)
const QUARTER := Vector2(-4, 18.5)
const FORGE := Vector2(16, 11)
const BENCH := Vector2(12, -3.5)
const KETTLE := Vector2(-13, -1)
const YARD := Vector2(-11, 24)
const SHRINE := Vector2(-19.5, 15.5)
const TOWER := Vector2(-20, -20)
const OVERLOOK := Vector2(26, 0)
const TENTS := [Vector2(-19, -11), Vector2(-9, -26), Vector2(13, -21), Vector2(21, -10), Vector2(-24, 3), Vector2(20, 24)]
## Gate crossings on the stockade (angle in degrees, measured with atan2(z, x)).
var _north_gate := 0.0
var _west_gate := 0.0
var _marsh_gate := 0.0              # bh-021: the Marsh Gate to the Weeping Causeway (barred until mq_marsh_gate_open)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.02, 0.035, 0.07), "sky_horizon": Color(0.13, 0.16, 0.22),
		"ambient": Color(0.3, 0.35, 0.44), "ambient_energy": 0.78,
		"fog": Color(0.14, 0.18, 0.22), "fog_density": 0.008, "fog_height": -3.0, "fog_height_density": 0.08,
		"sun": Color(0.55, 0.66, 0.9), "sun_energy": 0.55, "sun_rot": Vector3(-48, -40, 0), "glow": 0.85,
		"exposure": 1.1, "contrast": 1.07, "saturation": 0.9,
	})
	prepare(-95.0, -72.0, 200, 140, _landform, _shape)
	terrain(Vector2i(W, D), Vector3(X0 + W * 0.5, 0, Z0 + D * 0.5), height_at, _splat,
		{"grass": "grass", "moss": "forest_floor", "dirt": "dirt", "path": "cobblestone", "rock": "rock_cliff"}, Color(0.9, 0.94, 0.88))
	_north_gate = _gate_angle(DataIsland.road("wy_north_road").points)
	_west_gate = _gate_angle(DataIsland.road("wy_west_road").points)
	_marsh_gate = _gate_angle(DataIsland.road("wy_marsh_road").points)
	_marsh()
	_jetty()
	_stockade()
	_fire_ring()
	_tents()
	_lodge_and_register()
	_trade_row()
	_training_yard()
	_tower_and_overlook()
	_shrine()
	_herbs()
	_wild_camps()
	keep_clear(ARENA.x, ARENA.y, ARENA_R + 9.0)
	keep_clear(ARENA.x, ARENA.y - ARENA_R - 4.0, ARENA_LANE + 2.0)
	var og: Dictionary = DataDungeons.get_def(&"orrery").surface
	dungeon_gate(&"orrery", og.pos, og.yaw)
	keep_clear(og.pos.x, og.pos.y, 8.0)
	_greenery()
	_arena()
	spawn(&"start", Vector3(0, 0, 9.0), 180.0, true)
	spawn(&"north_road", Vector3(7.5, 0, -47.0), 0.0, true)
	spawn(&"west_road", Vector3(-51.5, 0, 18.4), 100.0, true)
	set_bounds(AABB(Vector3(-66, -6, -62), Vector3(132, 24, 130)))
	view("overview", Vector3(0, 0, 0), 0.0, 62.0, 100.0, 45.0)
	view("topdown", Vector3(0, 0, -4), 0.0, 89.5, 118.0, 50.0)
	view("bonfire", Vector3(0, 1, -2), 0.0, 48.0, 22.0)
	view("forge", Vector3(4, 1, 20), 0.0, 50.0, 28.0)
	view("row_gate", Vector3(4, 1, 15), 0.0, 40.0, 22.0)
	view("yard", Vector3(-10, 1, 22), 20.0, 48.0, 20.0)
	view("overlook", Vector3(30, 0, 0), -60.0, 35.0, 30.0)
	view("arena", Vector3(ARENA.x, 0, ARENA.y), 0.0, 62.0, 58.0, 45.0)
	view("arena_gate", Vector3(ARENA.x, 1, ARENA.y - ARENA_R + 4.0), 180.0, 38.0, 24.0, 45.0)

## bh-012: an orc band camped on the Brass path, between the Watch Road and the Orrery gate (the town stays safe).
func _wild_camps() -> void:
	wild_camp("brass_path_orcs", Vector2(-13, -51), 4.0, [&"orc_reaver", &"goblin_skulker", &"goblin_skulker", &"orc_shaman"], 4, Vector2i(4, 6), 0.15)

## Where a road leaving the camp crosses the stockade circle (degrees).
func _gate_angle(pts: Array) -> float:
	var total := DataIsland.polyline_length(pts)
	var along := 0.0
	while along <= total:
		var p := DataIsland.point_at(pts, along)
		if p.length() <= R:
			return rad_to_deg(atan2(p.y, p.x))
		along += 0.25
	return 0.0

# ------------------------------------------------------------------------------------------------------------
# landform

func _noise(x: float, z: float) -> float:
	return sin(x * 0.12) * cos(z * 0.1) * 0.6 + sin(x * 0.051 + z * 0.037) * 0.9

func _landform(x: float, z: float) -> float:
	var d := Vector2(x, z).length()
	var h := 1.2 * (1.0 - smoothstep(30.0, 44.0, d)) + _noise(x, z) * 0.35
	# the marsh to the east: the ground sinks under black water
	h = lerpf(h, -2.2, smoothstep(MARSH_X - 4.0, MARSH_X + 6.0, x))
	return _arena_flat(x, z, h)

## bh-028: the ground under the arena, its lane and its galleries is level.
func _arena_flat(x: float, z: float, h: float) -> float:
	var d := Vector2(x, z).distance_to(ARENA)
	var k := 1.0 - smoothstep(ARENA_R + 6.0, ARENA_R + 11.0, d)
	if z > ARENA.y - ARENA_R - 12.0 and z < ARENA.y:
		k = maxf(k, 1.0 - smoothstep(ARENA_LANE + 1.0, ARENA_LANE + 3.0, absf(x - ARENA.x)))
	return lerpf(h, ARENA_Y, k)

func _shape(x: float, z: float, b: float, _rd: float, _rt: int) -> float:
	var d := Vector2(x, z).length()
	var n := _noise(x * 1.9, z * 1.9) * (0.1 if d < R else 0.5)
	return b + n * smoothstep(ARENA_R + 5.0, ARENA_R + 10.0, Vector2(x, z).distance_to(ARENA))

func _splat(x: float, z: float) -> Color:
	var k := _k(x, z)
	var n := sin(x * 0.37 + z * 0.23) * 0.5 + 0.5
	var road := (1.0 - smoothstep(2.4, 3.5, _rd[k])) if _rt[k] == 1 else 0.0
	var trail := (1.0 - smoothstep(1.1, 2.1, _rd[k])) if _rt[k] == 2 else 0.0
	var d := Vector2(x, z).length()
	var trodden := 1.0 - smoothstep(9.0, 26.0, d)
	var fire := 1.0 - smoothstep(4.5, 6.0, Vector2(x, z).distance_to(BONFIRE))
	var marsh := smoothstep(MARSH_X - 6.0, MARSH_X + 2.0, x)
	var r := clampf(maxf(maxf(trail, trodden * 0.7), fire) + n * 0.1, 0.0, 1.0)
	var g := clampf(marsh + n * 0.3 + (1.0 - trodden) * 0.35, 0.0, 1.0) * (1.0 - trail)
	var b := clampf(maxf(road * 0.8, DataTownRows.paved(&"wyman_outpost", x, z) * 0.85), 0.0, 1.0)
	# bh-028: trodden earth around the arena and along its lane
	var trod := 1.0 - smoothstep(ARENA_R + 3.0, ARENA_R + 9.0, Vector2(x, z).distance_to(ARENA))
	if absf(x - ARENA.x) < ARENA_LANE + 1.5 and z > ARENA.y - ARENA_R - 10.0 and z < ARENA.y:
		trod = 1.0
	r = maxf(r, trod)
	g *= 1.0 - trod
	return Color(r * (1.0 - b), g * (1.0 - b), b)

# ------------------------------------------------------------------------------------------------------------
# the marsh and the stockade

func _marsh() -> void:
	var w := water(Rect2(MARSH_X + 1.0, -72, 105.0 - MARSH_X - 1.0, 140), MARSH_Y, Color(0.1, 0.2, 0.16), Color(0.02, 0.05, 0.04), 0.25, 2.0, 0.12)
	# bh-029: still black marsh water. The default near-mirror ripples caught the moon as a grid of white discs.
	if w.material_override is ShaderMaterial:
		w.material_override.set_shader_parameter("rough", 0.3)
		w.material_override.set_shader_parameter("ripple", 0.25)
	mist(Rect2(MARSH_X + 2.0, -72, 103.0 - MARSH_X, 140), MARSH_Y + 1.0, Color(0.2, 0.25, 0.25), 0.3)
	for i in 34:
		var x := MARSH_X + 4.0 + rng.randf() * 60.0
		var z := -68.0 + rng.randf() * 130.0
		if not _jetty_lane(x, z, 3.0):
			decor("tree_dead_a" if i % 2 else "tree_dead_b", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.9, 1.4), true, true, 6.0)
	for i in 80:
		var x := MARSH_X - 1.0 + rng.randf() * 24.0
		var z := -55.0 + rng.randf() * 100.0
		if not _jetty_lane(x, z, 1.0):
			decor("fern", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.6, 1.0))
	for i in 6:
		decor("pillar_broken", Vector3(MARSH_X + 8.0 + rng.randf() * 18.0, -0.6, -40.0 + i * 14.0), rng.randf() * 360.0, 0.7, true, true, 12.0)
	# will-o'-lights far out on the water
	for i in 3:
		var p := Vector3(MARSH_X + 14.0 + rng.randf() * 20.0, MARSH_Y + 1.2, -40.0 + rng.randf() * 80.0)
		light(p, Color(0.5, 1.0, 0.8), 1.6, 7.0, false, true)
	# bh-021: the marsh line stays closed except where the Marsh Gate's causeway leaves the camp
	boundary(Vector3(MARSH_X - 2.0, -4.0, -66.0), Vector3(MARSH_X - 2.0, -4.0, 2.6), 12.0)
	# bh-029: open where the Marsh Jetty leaves the bank (_jetty)
	var jz := DataZarael.WY_JETTY_ROOT.y
	boundary(Vector3(MARSH_X - 2.0, -4.0, 11.8), Vector3(MARSH_X - 2.0, -4.0, jz - 3.6), 12.0)
	boundary(Vector3(MARSH_X - 2.0, -4.0, jz + 3.6), Vector3(MARSH_X - 2.0, -4.0, 54.0), 12.0)

## bh-021: the Marsh Gate — an iron gate and a bar across the arch until Sir Aldric opens it (mq_marsh_gate_open), a
## short railed causeway of planks out over the reeds, and the boundary into the Weeping Causeway map.
func _marsh_gate_bar() -> void:
	var a := deg_to_rad(_marsh_gate)
	var c := Vector2(cos(a), sin(a)) * R
	var yaw := rad_to_deg(atan2(c.x, c.y))
	var y := ground(c.x, c.y)
	var sb := StaticBody3D.new()
	sb.name = "MarshGateBar"
	sb.collision_layer = BH.LAYER_WORLD
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(6.4, 4.0, 0.8)
	cs.shape = bs
	sb.add_child(cs)
	sb.position = Vector3(c.x, y + 2.0, c.y)
	sb.rotation.y = deg_to_rad(yaw)
	geo.add_child(sb)
	hide_when(sb, &"mq_marsh_gate_open")
	hide_when(kit("gate_iron", Vector3(c.x, y, c.y), yaw, 1.0, props), &"mq_marsh_gate_open")
	var out := Vector2(MARSH_X + 0.5, 7.2)
	corridor_rails([c, out], 3.6)
	boundary(Vector3(out.x + 1.2, -4.0, out.y - 4.0), Vector3(out.x + 1.2, -4.0, out.y + 4.0), 12.0)
	for i in 4:
		var p := c.lerp(out, (i + 0.5) / 4.0)
		kit("dock_planks", Vector3(p.x, ground(p.x, p.y) + 0.05, p.y), yaw + 90.0, 1.0, deco)
	exit_zone(&"wyman_marsh_gate", Vector3(out.x - 0.6, 0, out.y), Vector3(2.4, 4.0, 7.0), &"weeping_causeway", &"arrival",
		"The Weeping Causeway", &"mq_marsh_gate_open", "The Marsh Gate is barred. Sir Aldric holds the key.")
	spawn(&"marsh_gate", Vector3(c.x - 3.5, 0, c.y - 1.0), -95.0, true)

func _in_gap(deg: float) -> bool:
	return absf(wrapf(deg - _north_gate, -180.0, 180.0)) < 7.5 or absf(wrapf(deg - _west_gate, -180.0, 180.0)) < 7.5 		or absf(wrapf(deg - _marsh_gate, -180.0, 180.0)) < 7.5 or absf(wrapf(deg - DataZarael.WY_JETTY_GATE_DEG, -180.0, 180.0)) < 5.0

## bh-029: the Marsh Jetty — a small gate in the south-east of the stockade, a boardwalk down to the bank, a square
## landing on the bank and a jetty out over the marsh. Once Kethrax has fallen, Agdao's ship (the Sunwake) lies at its end
## and Captain Ilsa Rhondar waits by the gangplank (DataNpcsZarael; she sails to Zarael). DataZarael holds every spot.
## Every piece is a whole `zr_jetty_wood` segment (4 m long, 3 m deck) laid end to end at exactly its own length, so the
## deck is one unbroken walk from the gate to the gangplank.
const JETTY_SEG := 4.0
const JETTY_HALF_W := 1.5

func _jetty() -> void:
	var root: Vector2 = DataZarael.WY_JETTY_ROOT       # centre of the landing
	var end: Vector2 = DataZarael.WY_JETTY_END
	var gate: Vector2 = DataZarael.WY_WALK[0]
	# deck height: clear of the bank everywhere under the landing, never below the marsh's flood line
	var deck := MARSH_Y + 1.0
	for dx in [-JETTY_SEG, 0.0, JETTY_SEG]:
		for dz in [-3.0, 0.0, 3.0]:
			deck = maxf(deck, ground(root.x + dx, root.y + dz) + 0.08)
	# the landing: 2 x 2 segments (8 m x 6 m), mooring posts on the outside edges
	for ix in 2:
		for iz in 2:
			var c := Vector3(root.x + (ix - 0.5) * JETTY_SEG, deck + 0.02, root.y + (iz - 0.5) * 2.0 * JETTY_HALF_W)
			_jetty_seg(c, 90.0 if iz == 0 else -90.0)
	# the jetty: whole segments from the landing's east edge to the end. Each segment's own mooring post stands on the
	# north edge; a matching post on the south edge, and rope rails run post to post along both sides.
	var x0 := root.x + JETTY_SEG
	var segs := int(round((end.x - x0) / JETTY_SEG))
	var tip := x0 + segs * JETTY_SEG
	for k in segs:
		_jetty_seg(Vector3(x0 + (k + 0.5) * JETTY_SEG, deck, end.y), 90.0)
	for side in [-1, 1]:
		var line: Array[Vector3] = [Vector3(x0 + 0.15, deck, end.y + side * 1.62)]
		for k in segs:
			line.append(Vector3(x0 + (k + 0.5) * JETTY_SEG, deck, end.y + side * 1.62))
		line.append(Vector3(tip - 0.15, deck, end.y + side * 1.62))
		for i in line.size():
			if side > 0 or i == 0 or i == line.size() - 1:
				_post(line[i])
			if i > 0:
				_rope(line[i - 1] + Vector3(0, 0.6, 0), line[i] + Vector3(0, 0.6, 0))
	# the boardwalk: whole segments from the stockade gate down to the landing's centre (hidden under the landing there),
	# each tilted to follow the bank and never below the deck
	var dir := (root - gate).normalized()
	var run := gate.distance_to(root)
	var n := ceili(run / JETTY_SEG)
	var step := run / n
	var hts: Array[float] = []
	for k in n + 1:
		var p := gate + dir * step * k
		var h := maxf(ground(p.x, p.y) + 0.1, deck)
		if k < n:
			var m := gate + dir * step * (k + 0.5)
			h = maxf(h, ground(m.x, m.y) + 0.1)
		hts.append(h)
	hts[n] = deck
	for k in n:
		var a := gate + dir * step * k
		var b := gate + dir * step * (k + 1)
		var a3 := Vector3(a.x, hts[k] + 0.006 * (k % 2), a.y)
		var b3 := Vector3(b.x, hts[k + 1] + 0.006 * (k % 2), b.y)
		var f := (b3 - a3).normalized()
		var x := Vector3.UP.cross(f).normalized()
		var seg := _jetty_seg((a3 + b3) * 0.5, 0.0)
		seg.basis = Basis(x, f.cross(x), f * ((b3 - a3).length() / JETTY_SEG))
		keep_clear(a.x, a.y, 3.0)
	keep_clear(root.x, root.y, 6.0)
	# rails: nobody steps off into the black water. The landing's west part rests on the bank (open to the camp).
	var bx := MARSH_X - 2.0
	var lz0 := root.y - 2.0 * JETTY_HALF_W
	var lz1 := root.y + 2.0 * JETTY_HALF_W
	var lx1 := root.x + JETTY_SEG
	var y0 := deck - 3.0
	boundary(Vector3(bx, y0, lz0 - 0.2), Vector3(lx1, y0, lz0 - 0.2), 8.0, 0.4)
	boundary(Vector3(bx, y0, lz1 + 0.2), Vector3(lx1, y0, lz1 + 0.2), 8.0, 0.4)
	boundary(Vector3(lx1 + 0.2, y0, lz0), Vector3(lx1 + 0.2, y0, end.y - JETTY_HALF_W), 8.0, 0.4)
	boundary(Vector3(lx1 + 0.2, y0, end.y + JETTY_HALF_W), Vector3(lx1 + 0.2, y0, lz1), 8.0, 0.4)
	boundary(Vector3(lx1, y0, end.y - JETTY_HALF_W - 0.2), Vector3(tip, y0, end.y - JETTY_HALF_W - 0.2), 8.0, 0.4)
	boundary(Vector3(lx1, y0, end.y + JETTY_HALF_W + 0.2), Vector3(tip, y0, end.y + JETTY_HALF_W + 0.2), 8.0, 0.4)
	boundary(Vector3(tip + 0.2, y0, end.y - JETTY_HALF_W), Vector3(tip + 0.2, y0, end.y + JETTY_HALF_W), 8.0, 0.4)
	# lamps stand on the deck's edge, their arms over the boards
	lamp_post(Vector3(lx1 - 0.6, deck + 0.02, lz0 + 0.25), -90.0, false)
	lamp_post(Vector3(tip - 1.0, deck, end.y + JETTY_HALF_W - 0.25), 90.0, false)
	spawn(&"jetty", Vector3(DataZarael.WY_SPAWN.x, deck, DataZarael.WY_SPAWN.z), -90.0)
	signpost(Vector2(root.x - 4.5, lz1 + 1.5), [["Marsh Jetty", Vector2(1, 0)]])
	if DataZarael.ship_ready(Game.hero):
		var s := DataZarael.WY_SHIP
		if ResourceLoader.exists(ENV_DIR % "zr_ship"):
			var ship := kit("zr_ship", Vector3(s.x, MARSH_Y + 0.1, s.z), 0.0, 1.0, props)
			ship.add_to_group(&"zr_ship_model")
		# the gangplank: from the jetty's last boards up onto the ship's rail (hull side at s.x - 3, rail 2.95 m up)
		_gangplank(Vector3(tip - 0.9, deck, end.y), Vector3(s.x - 2.75, MARSH_Y + 0.1 + 2.98, end.y))
		light(Vector3(s.x, MARSH_Y + 4.0, s.z - 9.0), Color(1.0, 1.0, 1.0), 2.0, 9.0, false, true)
		light(Vector3(s.x, MARSH_Y + 4.5, s.z + 9.0), Color(1.0, 1.0, 1.0), 2.0, 9.0, false, true)

## bh-029: true near the jetty, its landing, the boardwalk or the ship (no tree or fern grows through the boards).
func _jetty_lane(x: float, z: float, margin: float) -> bool:
	var root: Vector2 = DataZarael.WY_JETTY_ROOT
	if x > root.x - 5.0 - margin and x < DataZarael.WY_SHIP.x + 4.0 + margin and absf(z - root.y) < 3.2 + margin:
		return true
	if absf(x - DataZarael.WY_SHIP.x) < 4.0 + margin and absf(z - DataZarael.WY_SHIP.z) < 15.0 + margin:
		return true
	var g: Vector2 = DataZarael.WY_WALK[0]
	var q := Geometry2D.get_closest_point_to_segment(Vector2(x, z), g, root)
	return q.distance_to(Vector2(x, z)) < 2.0 + margin

## One jetty segment (deck top at `c`); yaw 90 puts its mooring post on the north (-Z) side, -90 on the south.
func _jetty_seg(c: Vector3, yaw: float) -> Node3D:
	return kit("zr_jetty_wood", c, yaw, 1.0, props)

## A mooring post standing in the marsh beside the deck, its top 0.75 m above the boards (matches zr_jetty_wood's own).
func _post(at: Vector3) -> void:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.14
	cm.bottom_radius = 0.16
	cm.height = 3.3
	cm.radial_segments = 8
	mi.mesh = cm
	mi.material_override = MaterialLibrary.env("BH_WoodDark")
	mi.position = at + Vector3(0, 0.75 - 1.65, 0)
	props.add_child(mi)
	var cap := MeshInstance3D.new()
	var cc := CylinderMesh.new()
	cc.top_radius = 0.16
	cc.bottom_radius = 0.16
	cc.height = 0.06
	cc.radial_segments = 8
	cap.mesh = cc
	cap.material_override = MaterialLibrary.env("BH_Iron")
	cap.position = at + Vector3(0, 0.75, 0)
	props.add_child(cap)

## A slack-free rope rail between two points.
func _rope(a: Vector3, b: Vector3) -> void:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.035
	cm.bottom_radius = 0.035
	cm.height = a.distance_to(b)
	cm.radial_segments = 6
	cm.rings = 1
	mi.mesh = cm
	mi.material_override = MaterialLibrary.env("BH_Rope")
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var up := (b - a).normalized()
	var side := up.cross(Vector3.FORWARD if absf(up.dot(Vector3.FORWARD)) < 0.95 else Vector3.RIGHT).normalized()
	mi.transform = Transform3D(Basis(side, up, side.cross(up)), (a + b) * 0.5)
	deco.add_child(mi)

## A boarding plank with cleats and rope hand-lines, from `a` (on the jetty) to `b` (on the ship's rail).
func _gangplank(a: Vector3, b: Vector3) -> void:
	var f := (b - a).normalized()
	var x := Vector3.UP.cross(f).normalized()
	var basis := Basis(x, f.cross(x), f)
	var len := a.distance_to(b)
	var root3 := Node3D.new()
	root3.name = "Gangplank"
	root3.transform = Transform3D(basis, a)
	props.add_child(root3)
	var wood := MaterialLibrary.env("BH_Wood")
	var dark := MaterialLibrary.env("BH_WoodDark")
	for i in 3:
		_box(root3, Vector3((i - 1) * 0.29, 0.03, len * 0.5), Vector3(0.27, 0.06, len), wood)
	for i in int(len / 0.45):
		_box(root3, Vector3(0, 0.08, 0.3 + i * 0.45), Vector3(0.84, 0.04, 0.06), dark)
	for sx in [-1, 1]:
		_box(root3, Vector3(sx * 0.46, 0.45, 0.15), Vector3(0.07, 0.9, 0.07), dark)
		_rope(a + basis * Vector3(sx * 0.46, 0.85, 0.15), a + basis * Vector3(sx * 0.46, 0.25, len - 0.1))

func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)

func _stockade() -> void:
	var n := int(TAU * R / 4.0)
	for i in n:
		var a := TAU * (i + 0.5) / n
		var deg := rad_to_deg(a)
		if _in_gap(deg):
			continue
		var p := Vector2(cos(a), sin(a)) * R
		kit("palisade_fence", Vector3(p.x, 0, p.y), -deg + 90.0 + 180.0, 1.0, props, true)
	var m := 120
	for i in m:
		var a0 := TAU * i / m
		var a1 := TAU * (i + 1) / m
		if _in_gap(rad_to_deg((a0 + a1) * 0.5)) or _in_gap(rad_to_deg(a0)) or _in_gap(rad_to_deg(a1)):
			continue
		var p0 := Vector2(cos(a0), sin(a0)) * (R + 1.0)
		var p1 := Vector2(cos(a1), sin(a1)) * (R + 1.0)
		boundary(Vector3(p0.x, ground(p0.x, p0.y) - 1.0, p0.y), Vector3(p1.x, ground(p1.x, p1.y) - 1.0, p1.y), 8.0, 0.8)
	# gap edges: close the corners beside each gate
	for g: float in [_north_gate, _west_gate, _marsh_gate]:
		for side: float in [-1.0, 1.0]:
			var a := deg_to_rad(g + side * 7.5)
			var q0 := Vector2(cos(a), sin(a)) * (R - 1.0)
			var q1 := Vector2(cos(a), sin(a)) * (R + 3.5)
			boundary(Vector3(q0.x, ground(q0.x, q0.y) - 1.0, q0.y), Vector3(q1.x, ground(q1.x, q1.y) - 1.0, q1.y), 8.0, 0.6)
	for g: float in [_north_gate, _west_gate, _marsh_gate]:
		var a := deg_to_rad(g)
		var c := Vector2(cos(a), sin(a)) * R
		gatehouse(c, rad_to_deg(atan2(c.x, c.y)))
	_marsh_gate_bar()
	# corridors along the roads to the district boundaries
	var ng := Vector2(cos(deg_to_rad(_north_gate)), sin(deg_to_rad(_north_gate))) * (R + 1.0)
	var wg := Vector2(cos(deg_to_rad(_west_gate)), sin(deg_to_rad(_west_gate))) * (R + 1.0)
	corridor_rails([ng, Vector2(7.0, -44.0)], 4.6)
	# bh-012: the Watch Road's west rail opens onto the Brass path to the Orrery gate (its own corridor)
	boundary(Vector3(7.0 + 4.6, ground(7, -44) - 2.0, -44.0), Vector3(8.0 + 4.6, ground(8, -62) - 2.0, -62.0), 10.0, 0.6)
	boundary(Vector3(7.0 - 4.6, ground(7, -44) - 2.0, -44.0), Vector3(7.2 - 4.6, ground(7, -50) - 2.0, -50.5), 10.0, 0.6)
	boundary(Vector3(7.8 - 4.6, ground(8, -60) - 2.0, -59.5), Vector3(8.0 - 4.6, ground(8, -62) - 2.0, -62.0), 10.0, 0.6)
	corridor_rails([Vector2(3.2, -55.3), Vector2(-4.0, -54.0), Vector2(-16.0, -50.0), Vector2(-28.0, -46.0), Vector2(-34.0, -44.0)], 5.2)
	boundary(Vector3(-34.0, -2.0, -50.0), Vector3(-34.0, -2.0, -38.0), 12.0)
	boundary(Vector3(3.0, -2.0, -62.0), Vector3(13.0, -2.0, -62.0), 12.0)
	_fen_road_rails(wg)
	boundary(Vector3(-66.0, -2.0, 16.4), Vector3(-66.0, -2.0, 26.0), 12.0)
	exit_zone(&"wyman_watch_road", Vector3(8.0, 0, -57.5), Vector3(8.4, 4.0, 3.0), &"olivar", &"south_road", "Olivar")
	exit_zone(&"wyman_fen_road", Vector3(-61.5, 0, 20.3), Vector3(3.0, 4.0, 8.4), &"westreach", &"fen_road", "Westreach")
	signpost_bed(Vector2(12.0, -40.0), [["Olivar (Watch Road)", Vector2(0, -1)], ["Wyman Outpost", Vector2(0, 1)]])
	signpost_bed(Vector2(-44.0, 22.0), [["Lantern Fields (Fen Road)", Vector2(-1, 0.2)], ["Wyman Outpost", Vector2(1, -0.3)]])
	for p: Vector2 in [Vector2(2.2, -44.0), Vector2(12.4, -52.0), Vector2(-40.0, 11.5), Vector2(-54.0, 23.5)]:
		lamp_post(Vector3(p.x, 0, p.y), rng.randf() * 360.0)

# ------------------------------------------------------------------------------------------------------------
# the camp

func _fire_ring() -> void:
	bonfire("Wyman Outpost", Vector3(BONFIRE.x, 0, BONFIRE.y), &"bonfire", 0.0)
	keep_clear(BONFIRE.x, BONFIRE.y, 6.0)
	for i in 4:
		var a := TAU * i / 4.0 + PI / 4.0
		var p := BONFIRE + Vector2(cos(a), sin(a)) * 4.4
		if road_dist(p.x, p.y) < 3.8:
			continue
		kit("bench", Vector3(p.x, 0, p.y), rad_to_deg(atan2(-(p.x - BONFIRE.x), -(p.y - BONFIRE.y))), 1.0, props, true)
	for i in 5:
		var a := TAU * i / 5.0 + 0.4
		var lp := BONFIRE + Vector2(cos(a), sin(a)) * 6.4
		if road_dist(lp.x, lp.y) > 4.5:
			decor("log_fallen", Vector3(lp.x, 0, lp.y), rad_to_deg(a) + 90.0, 0.7, true, true)

func _tent_yaw(p: Vector2) -> float:
	var to := BONFIRE - p
	return rad_to_deg(atan2(to.x, to.y))

func _tents() -> void:
	for i in TENTS.size():
		var p: Vector2 = TENTS[i]
		var yaw := _tent_yaw(p)
		kit("tent_old", Vector3(p.x, 0, p.y), yaw, 1.15, props, true)
		keep_clear(p.x, p.y, 3.6)
		var fwd := Vector2(sin(deg_to_rad(yaw)), cos(deg_to_rad(yaw)))
		var side := Vector2(fwd.y, -fwd.x)
		var br := p + fwd * 2.2 + side * 1.2
		kit("bedroll", Vector3(br.x, 0, br.y), yaw + 90.0, 1.0, props, true)
		# a guild banner on a pole beside every other tent
		var pole := p + side * -2.9 + fwd * 0.8
		var y := height_at(pole.x, pole.y)
		var pm := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.05
		cm.bottom_radius = 0.07
		cm.height = 4.2
		pm.mesh = cm
		pm.material_override = MaterialLibrary.env("BH_WoodDark")
		pm.position = Vector3(pole.x, y + 2.1, pole.y)
		deco.add_child(pm)
		kit("guild_banner_swordfin" if i % 2 == 0 else "guild_banner_lantern", Vector3(pole.x, y + 4.0, pole.y) + Vector3(fwd.x, 0, fwd.y) * 0.1, yaw, 0.85, deco)
		if i % 3 == 0:
			var l := p + fwd * 2.6 - side * 1.8
			kit("lantern_stand", Vector3(l.x, 0, l.y), yaw, 1.0, props, true)
			light(Vector3(l.x + 0.4, height_at(l.x, l.y) + 1.8, l.y), Color(1.0, 0.72, 0.42), 2.0, 8.0, false, true)
		for c in [p - fwd * 1.6 + side * 2.2]:
			breakable("crate" if i % 2 else "barrel", Vector3(c.x, 0, c.y), rng.randf() * 360.0, 20.0, true)

func _lodge_and_register() -> void:
	var h := kit("house_intact", Vector3(LODGE.x, 0, LODGE.y), 0.0, 0.85, props, true)
	light(socket_pos(h, "door_light"), Color(1.0, 0.68, 0.35), 2.4, 8.0, false, true)
	keep_clear(LODGE.x, LODGE.y, 5.5)
	kit("map_table", Vector3(LODGE.x + 3.4, 0, LODGE.y + 6.2), 10.0, 1.0, props, true)
	candles(Vector3(LODGE.x + 3.4, 1.13 + height_at(LODGE.x + 3.4, LODGE.y + 6.2), LODGE.y + 6.2))
	kit("guild_banner_swordfin", Vector3(LODGE.x - 2.2, height_at(LODGE.x, LODGE.y) + 3.4, LODGE.y + 3.9), 0.0, 1.0, deco)
	kit("guild_banner_lantern", Vector3(LODGE.x + 2.2, height_at(LODGE.x, LODGE.y) + 3.4, LODGE.y + 3.9), 0.0, 1.0, deco)
	# the Hero Register: a notice board of signed cards, lit by a lantern
	kit("notice_board", Vector3(REGISTER.x, 0, REGISTER.y), 0.0, 1.0, props, true)
	var rb := RosterBoard.new()
	rb.name = "HeroRegister"
	rb.position = Vector3(REGISTER.x, height_at(REGISTER.x, REGISTER.y), REGISTER.y + 0.9)
	markers.add_child(rb)
	kit("lantern_stand", Vector3(REGISTER.x + 1.9, 0, REGISTER.y + 0.2), 0.0, 1.0, props, true)
	light(Vector3(REGISTER.x + 2.3, height_at(REGISTER.x, REGISTER.y) + 1.8, REGISTER.y + 0.2), Color(1.0, 0.75, 0.45), 2.2, 7.0, false, true)
	keep_clear(REGISTER.x, REGISTER.y, 2.5)

## bh-018: Quartermaster Row (DataTownRows) south of the bonfire: the quartermaster's tent, the field smith's campaign forge,
## the crystal prospector's cart, the camp kettle and the workbench.
func _trade_row() -> void:
	TownRowBuilder.build(self, def.id)

## A straw training dummy: post, crossbar and a stuffed sack (solid, so heroes and the player can swing at it).
func dummy(p: Vector2, yaw: float) -> void:
	var y := height_at(p.x, p.y)
	var root3 := Node3D.new()
	root3.name = "Dummy_%d" % props.get_child_count()
	root3.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(yaw)), Vector3(p.x, y, p.y))
	var wood := MaterialLibrary.env("BH_WoodDark")
	var straw := StandardMaterial3D.new()
	straw.albedo_color = Color(0.72, 0.6, 0.36)
	straw.roughness = 1.0
	var post := MeshInstance3D.new()
	var pm := CylinderMesh.new()
	pm.top_radius = 0.07
	pm.bottom_radius = 0.09
	pm.height = 2.0
	post.mesh = pm
	post.material_override = wood
	post.position.y = 1.0
	root3.add_child(post)
	var bar := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.2, 0.09, 0.09)
	bar.mesh = bm
	bar.material_override = wood
	bar.position.y = 1.55
	root3.add_child(bar)
	var sack := MeshInstance3D.new()
	var sm := CapsuleMesh.new()
	sm.radius = 0.26
	sm.height = 0.95
	sack.mesh = sm
	sack.material_override = straw
	sack.position.y = 1.35
	root3.add_child(sack)
	var head := MeshInstance3D.new()
	var hm := SphereMesh.new()
	hm.radius = 0.17
	hm.height = 0.34
	head.mesh = hm
	head.material_override = straw
	head.position.y = 1.95
	root3.add_child(head)
	var sb := StaticBody3D.new()
	sb.collision_layer = BH.LAYER_PROPS
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.3
	cap.height = 2.0
	cs.shape = cap
	cs.position.y = 1.0
	sb.add_child(cs)
	root3.add_child(sb)
	props.add_child(root3)

func _training_yard() -> void:
	var y := YARD
	for p in [[Vector2(-3.0, 0.0), 180.0], [Vector2(1.0, 1.4), 200.0], [Vector2(4.6, -0.6), 150.0]]:
		dummy(y + p[0], p[1])
	kit("weapon_rack", Vector3(y.x - 6.0, 0, y.y + 1.0), 80.0, 1.0, props, true)
	kit("weapon_rack", Vector3(y.x + 7.5, 0, y.y + 0.8), -80.0, 1.0, props, true)
	for i in 5:
		kit("wood_fence", Vector3(y.x - 6.0 + i * 3.3, 0, y.y + 3.6), 0.0, 0.9, props, true)
	torch_post(Vector2(y.x - 6.5, y.y - 2.5))
	torch_post(Vector2(y.x + 8.0, y.y - 2.5))
	keep_clear(y.x, y.y, 7.5)

func torch_post(p: Vector2) -> void:
	var y := height_at(p.x, p.y) + 2.3
	var pm := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.06
	cm.bottom_radius = 0.08
	cm.height = 2.3
	pm.mesh = cm
	pm.material_override = MaterialLibrary.env("BH_WoodDark")
	pm.position = Vector3(p.x, y - 1.15, p.y)
	deco.add_child(pm)
	flame(Vector3(p.x, y + 0.2, p.y), 1.0)
	light(Vector3(p.x, y + 0.6, p.y), FIRE, 2.6, 10.0, false, true)

func _tower_and_overlook() -> void:
	kit("scaffold_platform", Vector3(TOWER.x, 0, TOWER.y), 45.0, 1.0, props, true)
	kit("ladder", Vector3(TOWER.x + 0.9, 0, TOWER.y + 1.2), 45.0, 1.0, deco, true)
	light(Vector3(TOWER.x, height_at(TOWER.x, TOWER.y) + 5.4, TOWER.y), Color(1.0, 0.7, 0.4), 2.4, 10.0, false, true)
	keep_clear(TOWER.x, TOWER.y, 3.0)
	# the Marsh Overlook: two platforms and a brazier looking out over the reeds
	var o := OVERLOOK
	kit("scaffold_platform", Vector3(o.x, 0, o.y - 1.05), 0.0, 1.0, props, true)
	kit("scaffold_platform", Vector3(o.x, 0, o.y + 1.05), 0.0, 1.0, props, true)
	kit("ladder", Vector3(o.x - 1.2, 0, o.y + 0.4), -90.0, 1.0, deco, true)
	var top := height_at(o.x, o.y) + 4.0
	brazier(Vector3(o.x, top, o.y), 3.4, false, false)
	kit("banner_torn", Vector3(o.x - 1.0, top + 2.4, o.y - 2.0), -90.0, 1.0, deco)
	keep_clear(o.x, o.y, 3.5)
	signpost_bed(Vector2(o.x - 3.6, o.y + 3.2), [["Reedwater Marsh (no road yet)", Vector2(1, 0)], ["Bonfire", Vector2(-1, 0)]])

func _shrine() -> void:
	var s := SHRINE
	var sy := height_at(s.x, s.y) + 0.05
	apron(s, sy, 3.6)
	teleporter(&"wyman_shrine", Vector3(s.x, sy, s.y), &"sanctuary", &"waypoint", "Malasugue Town")
	spawn(&"wyman_shrine", Vector3(s.x + 3.2, 0, s.y - 1.6), 110.0, true)
	for a: float in [0.9, 2.5, 4.1]:
		decor("rock_medium", Vector3(s.x + cos(a) * 4.0, 0, s.y + sin(a) * 3.8), rng.randf() * 360.0, rng.randf_range(0.5, 0.7), true, true)
	keep_clear(s.x, s.y, 5.0)

func _herbs() -> void:
	for p: Vector2 in [Vector2(27.0, -12.0), Vector2(27.5, 10.0), Vector2(24.0, 18.0)]:
		herb_patch(&"mirebloom", Vector3(p.x, 0, p.y))
		keep_clear(p.x, p.y, 1.5)
	for p: Vector2 in [Vector2(-25.5, -7.0), Vector2(9.0, -27.0)]:
		herb_patch(&"silverleaf", Vector3(p.x, 0, p.y))
		keep_clear(p.x, p.y, 1.5)
	herb_patch(&"brightcap", Vector3(-17.0, 0, -24.5))
	keep_clear(-17.0, -24.5, 1.5)

func _greenery() -> void:
	var blocked := func(x: float, z: float) -> bool:
		if road_dist(x, z) < 5.5 or not is_clear(x, z, 0.8) or x > MARSH_X - 3.0:
			return true
		return Vector2(x, z).length() < R + 3.0
	var trees := scatter(["tree_pine", "tree_pine", "tree_oak_twisted", "tree_dead_a"], Rect2(-95, -72, MARSH_X + 95.0, 140), 190, 5.0,
		Vector2(0.85, 1.3), blocked, true, true)
	for t in trees:
		if road_dist(t.x, t.z) < 12.0:
			blocker(Vector3(t.x, height_at(t.x, t.z) + 2.0, t.z), Vector3(0.9, 4.0, 0.9))
	scatter(["bush_a", "bush_b", "fern", "rock_small", "stump"], Rect2(-95, -72, MARSH_X + 95.0, 140), 150, 3.0, Vector2(0.7, 1.2), blocked, true, true)
	var camp := func(x: float, z: float) -> bool:
		return road_dist(x, z) < 3.8 or not is_clear(x, z, 0.8) or Vector2(x, z).length() > R - 2.0 or Vector2(x, z).length() < 8.0
	scatter(["bush_a", "fern", "rock_small"], Rect2(-30, -30, 60, 60), 34, 3.0, Vector2(0.6, 0.9), camp, true, true)
	var placed := 0
	var tries := 0
	while placed < 800 and tries < 5000:
		tries += 1
		var x := -68.0 + rng.randf() * (MARSH_X + 60.0)
		var z := -64.0 + rng.randf() * 112.0
		if road_dist(x, z) < 3.2 or not is_clear(x, z) or Vector2(x, z).distance_to(BONFIRE) < 7.0:
			continue
		decor("grass_clump", Vector3(x, 0, z), rng.randf() * 360.0, rng.randf_range(0.8, 1.3))
		placed += 1

# ------------------------------------------------------------------------------------------------------------
# bh-028: the Sand Arena

## The Fen Road's rails, with the south rail open where the arena lane leaves the road.
func _fen_road_rails(wg: Vector2) -> void:
	var a := wg
	var b := Vector2(-46.0, 17.0)
	corridor_rails([b, Vector2(-66.0, 21.2)], 4.6)
	var dir := (b - a).normalized()
	for sgn: float in [-1.0, 1.0]:
		var off := Vector2(-dir.y, dir.x) * 4.6 * sgn
		var ra := a + off
		var rb := b + off
		if off.y < 0.0:
			_rail(ra, rb)
			continue
		# the south rail: two pieces, either side of the lane
		var g1 := ra.lerp(rb, (ra.x - (ARENA.x + ARENA_LANE)) / (ra.x - rb.x))
		var g2 := ra.lerp(rb, (ra.x - (ARENA.x - ARENA_LANE)) / (ra.x - rb.x))
		_rail(ra, g1)
		_rail(g2, rb)
		# the lane's own rails, from the road down to the arena wall
		for top: Vector2 in [g1, g2]:
			var gx := ARENA.x + (ARENA_LANE if top == g1 else -ARENA_LANE)
			var wall_z := ARENA.y - sqrt(ARENA_R * ARENA_R - pow(gx - ARENA.x, 2.0)) + 0.4
			_rail(Vector2(gx, top.y), Vector2(gx, wall_z))

func _rail(p0: Vector2, p1: Vector2) -> void:
	boundary(Vector3(p0.x, ground(p0.x, p0.y) - 2.0, p0.y), Vector3(p1.x, ground(p1.x, p1.y) - 2.0, p1.y), 10.0, 0.6)

func _arena_gap(deg: float) -> bool:
	return absf(wrapf(deg - ARENA_GATE_DEG, -180.0, 180.0)) < ARENA_GATE_HALF or absf(wrapf(deg - ARENA_DOOR_DEG, -180.0, 180.0)) < 4.0

func _arena() -> void:
	var c := ARENA
	var arng := RandomNumberGenerator.new()
	arng.seed = 2804
	# the sand
	apron(c, SAND_Y, ARENA_R + 0.6, "sand_path")
	# the palisade ring, and its collision just outside the stakes
	var n := int(TAU * ARENA_R / 4.0)
	for i in n:
		var a := TAU * (i + 0.5) / n
		var deg := rad_to_deg(a)
		if _arena_gap(deg):
			continue
		var p := c + Vector2(cos(a), sin(a)) * (ARENA_R + 0.4)
		kit("palisade_fence", Vector3(p.x, ARENA_Y, p.y), -deg + 90.0 + 180.0, 1.0, props)
		# a torch on every third post, burning towards the sand
		if i % 3 == 1:
			var tp := c + Vector2(cos(a), sin(a)) * (ARENA_R + 0.05)
			torch(Vector3(tp.x, ARENA_Y + 2.3, tp.y), -deg - 90.0, 2.2)
	var m := 96
	for i in m:
		var a0 := TAU * i / m
		var a1 := TAU * (i + 1) / m
		if absf(wrapf(rad_to_deg((a0 + a1) * 0.5) - ARENA_GATE_DEG, -180.0, 180.0)) < ARENA_GATE_HALF:
			continue
		var p0 := c + Vector2(cos(a0), sin(a0)) * (ARENA_R + 0.9)
		var p1 := c + Vector2(cos(a1), sin(a1)) * (ARENA_R + 0.9)
		boundary(Vector3(p0.x, ARENA_Y - 1.0, p0.y), Vector3(p1.x, ARENA_Y - 1.0, p1.y), 8.0, 0.8)
	# the gate (north, to the lane) and the fighters' door (south, barred: the adventurers come in through it)
	var gate := c + Vector2(cos(deg_to_rad(ARENA_GATE_DEG)), sin(deg_to_rad(ARENA_GATE_DEG))) * (ARENA_R + 0.4)
	gatehouse(gate, rad_to_deg(atan2(gate.x - c.x, gate.y - c.y)))
	var door := c + Vector2(cos(deg_to_rad(ARENA_DOOR_DEG)), sin(deg_to_rad(ARENA_DOOR_DEG))) * (ARENA_R + 0.4)
	var dyaw := rad_to_deg(atan2(door.x - c.x, door.y - c.y))
	kit("gate_iron", Vector3(door.x, ARENA_Y, door.y), dyaw, 1.25, geo)
	for sx: float in [-1.6, 1.6]:
		kit("pillar_quoin", Vector3(door.x + sx, ARENA_Y, door.y), dyaw, 0.85, geo)
	brazier(Vector3(door.x + 2.8, SAND_Y, door.y - 1.6), 2.6)
	brazier(Vector3(door.x - 2.8, SAND_Y, door.y - 1.6), 2.6)
	# the lane from the road: lamps either side, a rack for the last look at a blade
	for gx: float in [ARENA_LANE - 0.6, -(ARENA_LANE - 0.6)]:
		lamp_post(Vector3(c.x + gx, 0, gate.y - 5.5), 180.0 if gx > 0.0 else 0.0)
	kit("weapon_rack", Vector3(c.x + ARENA_LANE - 0.7, ARENA_Y, gate.y - 9.5), -90.0, 1.0, props, true)
	kit("barrel", Vector3(c.x - ARENA_LANE + 0.8, ARENA_Y, gate.y - 9.0), arng.randf() * 360.0, 1.0, props, true)
	# inside: cover to fight around, arms from earlier bouts, braziers
	for k in 3:
		var a := TAU * k / 3.0 + 0.5
		var p := c + Vector2(cos(a), sin(a)) * 8.5
		kit("pillar_broken", Vector3(p.x, SAND_Y - 0.05, p.y), rad_to_deg(a) + arng.randf_range(-30, 30), 0.85, geo)
	for k in 5:
		var a := arng.randf() * TAU
		var p := c + Vector2(cos(a), sin(a)) * arng.randf_range(4.0, ARENA_R - 4.0)
		decor("weapons_discarded", Vector3(p.x, SAND_Y, p.y), arng.randf() * 360.0, arng.randf_range(0.8, 1.1), false)
	for a_deg: float in [-45.0, -135.0, 45.0, 135.0]:
		var a := deg_to_rad(a_deg)
		var p := c + Vector2(cos(a), sin(a)) * (ARENA_R - 2.2)
		brazier(Vector3(p.x, SAND_Y, p.y), 3.2)
	for side: float in [-1.0, 1.0]:
		var p := gate + Vector2(side * 4.6, 4.2)
		kit("armor_stand", Vector3(p.x, SAND_Y, p.y), 0.0, 1.0, props)
		kit("weapon_rack", Vector3(p.x + side * 1.6, SAND_Y, p.y + 0.6), 0.0, 1.0, props)
	# spectator galleries east and west: scaffold platforms with benches on top, stairs up from the outside
	for side: float in [-1.0, 1.0]:
		var base_deg := 0.0 if side > 0.0 else 180.0
		for k in 5:
			var a := deg_to_rad(base_deg + (k - 2) * 11.0)
			var p := c + Vector2(cos(a), sin(a)) * (ARENA_R + 2.3)
			var yaw := -rad_to_deg(a) + 90.0
			kit("scaffold_platform", Vector3(p.x, ARENA_Y, p.y), yaw, 1.0, geo)
			kit("bench", Vector3(p.x, ARENA_Y + 4.0, p.y), yaw + 180.0, 1.0, props)
		var sa := deg_to_rad(base_deg + 36.0)
		var sp := c + Vector2(cos(sa), sin(sa)) * (ARENA_R + 3.2)
		kit("stairs_wood", Vector3(sp.x, ARENA_Y, sp.y), -rad_to_deg(sa) + 180.0, 1.0, geo)
		var lp := c + Vector2(cos(sa + 0.25), sin(sa + 0.25)) * (ARENA_R + 3.0)
		kit("lantern_stand", Vector3(lp.x, ARENA_Y, lp.y), -rad_to_deg(sa), 1.0, props)
		light(Vector3(lp.x, ARENA_Y + 2.0, lp.y), Color(1.0, 0.75, 0.45), 1.4, 7.0, false, true)
	light(Vector3(c.x, SAND_Y + 7.0, c.y), Color(1.0, 0.72, 0.42), 1.6, 26.0)
	# where the fallen stand up again (just inside the gate), and the arena's own logic
	var inward := (c - gate).normalized()
	var stand := gate + inward * 3.0
	spawn(ArenaGrounds.GATE_SPAWN, Vector3(stand.x, SAND_Y, stand.y), rad_to_deg(atan2(inward.x, inward.y)))
	var grounds := ArenaGrounds.new().configure(Vector3(c.x, SAND_Y, c.y), ARENA_R, Vector3(stand.x, SAND_Y, stand.y),
		Vector3(gate.x - c.x, 0, gate.y - c.y), Vector3(door.x, SAND_Y, door.y - 1.0))
	grounds.position = Vector3(c.x, SAND_Y, c.y)
	root.add_child(grounds)
