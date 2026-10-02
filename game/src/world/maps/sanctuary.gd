extends MapBuilder
## MAP 1 — Malasugue Town, "The last lit hearth" (town hub, no enemies; map id kept as `sanctuary` for saves).
##
## A palisaded village on a plateau at night. Lamp-lit paths run from the barred south gate to the fountain plaza
## (the landmark visible on arrival), and up a stair to the waypoint terrace where two knight statues guard the
## teleporter to the Ruined Forest. Houses with warm windows, a market, a smithy yard and a well make the hub feel
## lived in (reference 3: every lot furnished, trees and hedges framing the space); beyond the palisade the
## plateau breaks into cliffs above a misty valley, with mountains as background silhouettes.
## The South Gate was barred for three winters; once Captain Hald opens it (world flag `south_gate_open`) its bar and
## iron leaves are gone and the road runs down out of the gate into Westreach (a walk-through boundary).

const PLAZA := Vector3(0, 0, 4)
const TERRACE := Rect2(-10, -30, 20, 12)
const TERRACE_Y := 2.0
const FENCE_R := 40.0
const RIM_R := 47.0
## Houses you can enter: (position, yaw so the door faces the plaza, interior map id, door label).
const HOUSE_LOTS := [
	[Vector3(-25, 0, 2), 90.0, &"int_netmender", "Tessaly's house"],
	[Vector3(25, 0, 6), -90.0, &"int_cartographer", "the cartographer's house"],
	[Vector3(-17, 0, 23), 150.0, &"int_widow", "the Hald house"],
	[Vector3(23, 0, -14), -60.0, &"int_keeper", "the keeper's house"],
	[Vector3(-21, 0, -19), 55.0, &"int_refugee", "Zerin's house"],
]
## The tavern and the two guild halls: (asset, position, yaw, interior map id, door label).
const HALLS := [
	["tavern_exterior", Vector3(-28.8, 0, 13.5), 90.0, &"int_tavern", "the Salted Marlin"],
	["guild_hall_swordfin", Vector3(32, 0, -4.8), -90.0, &"int_swordfin", "Swordfin Hall"],
	["guild_house", Vector3(-11, 0, -10), 0.0, &"int_guildhouse", "the Guild House"],
	["guild_hall_lantern", Vector3(-30, 0, -9.5), 90.0, &"int_lantern", "Lantern House"],
]
## bh-027: where the great guild banner stands, in front of the Guild House beside its door, facing the plaza.
const GUILD_BANNER_AT := Vector3(-5.6, 0, -2.2)
const GUILD_BANNER_YAW := 18.0
## Footprints kept clear of grass, bushes and trees: (centre x, z, yaw, half size x, half size z).
const FOOTPRINTS := [
	[-25, 2, 90, 4.3, 3.8], [25, 6, -90, 4.3, 3.8], [-17, 23, 150, 4.3, 3.8], [23, -14, -60, 4.3, 3.8], [-21, -19, 55, 4.3, 3.8],
	[-28.8, 13.5, 90, 6.3, 4.9], [32, -4.8, -90, 5.7, 5.2], [-30, -9.5, 90, 4.9, 5.4], [-11, -9.6, 0, 8.2, 5.6],
]
## bh-018: the Merchant Quarter (DataTownRows) south-east of the plaza — every shopkeeper's own stand around a cobbled square,
## Brannoc's smithy with the town forge, the lapidary, the stranger's wagon, the crafting stations and the Shrine of the
## Fallen (the Tempo-Caller's spirit shrine, LORE §9).

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.02, 0.035, 0.08), "sky_horizon": Color(0.12, 0.14, 0.24),
		"ambient": Color(0.3, 0.34, 0.5), "ambient_energy": 0.75,
		"fog": Color(0.14, 0.17, 0.26), "fog_density": 0.006, "fog_height": -3.0, "fog_height_density": 0.06,
		"sun": Color(0.55, 0.65, 0.95), "sun_energy": 0.55, "sun_rot": Vector3(-48, -30, 0), "glow": 0.8,
		"exposure": 1.1, "contrast": 1.06, "saturation": 0.92,
	})
	terrain(Vector2i(150, 150), Vector3.ZERO, _height, _splat, {"moss": "forest_floor", "path": "cobblestone", "dirt": "dirt"})
	_perimeter()
	_plaza()
	_terrace()
	_houses()
	_merchant_row()
	_halls()
	_greenery()
	_background()
	_bh033_dressing()
	spawn(&"start", Vector3(0, 0, 14.5), 180.0, true)
	spawn(&"gate", Vector3(0, 0, 30.0), 180.0, true)
	set_bounds(AABB(Vector3(-42, -2, -42), Vector3(84, 12, 84)))
	view("overview", Vector3(0, 0, 0), 0.0, 72.0, 105.0, 45.0)
	view("arrival", Vector3(0, 0, 10), 0.0, 48.0, 30.0)
	view("plaza", PLAZA, 0.0, 52.0, 26.0)
	view("terrace", Vector3(0, TERRACE_Y, -23), 0.0, 45.0, 26.0)
	view("market", Vector3(14.8, 0, 20), 0.0, 50.0, 30.0)
	view("row_gate", Vector3(14.8, 0, 14), 0.0, 40.0, 22.0)
	view("row_south", Vector3(14.8, 0, 26), 0.0, 46.0, 24.0)
	view("gate", Vector3(0, 0, 30), 0.0, 40.0, 24.0)
	view("tavern", Vector3(-22, 0, 13.5), 30.0, 50.0, 30.0)
	view("guild_halls", Vector3(0, 0, -6), 0.0, 60.0, 66.0)
	view("guild_house", Vector3(-11, 0, -8), 0.0, 40.0, 30.0)
	view("shrine", Vector3(8.2, 0, 30), 0.0, 45.0, 16.0)
	view("topdown", Vector3(0, 0, 0), 0.0, 89.5, 105.0, 50.0)

# ------------------------------------------------------------------------------------------------------------
func _rim_noise(a: float) -> float:
	return sin(a * 3.0 + 0.7) * 2.2 + sin(a * 7.0 + 2.1) * 1.1

func _height(x: float, z: float) -> float:
	var d := Vector2(x, z).length()
	var a := atan2(z, x)
	var rim := RIM_R + _rim_noise(a)
	var h := 0.0
	# gentle undulation away from the built-up centre
	var outer := smoothstep(26.0, 38.0, d)
	h += (sin(x * 0.21) * cos(z * 0.17) * 0.35 + sin(x * 0.07 + z * 0.05) * 0.4) * outer
	var drop := smoothstep(rim - 1.0, rim + 6.0, d) * 16.0
	# the south road leaves the gate on an embankment that runs gently down toward Westreach
	var road := (1.0 - smoothstep(3.6, 7.5, absf(x))) * smoothstep(34.0, 38.0, z)
	h -= lerpf(drop, smoothstep(44.0, 75.0, z) * 6.0, road)
	return h

func _splat(x: float, z: float) -> Color:
	var d := Vector2(x - PLAZA.x, z - PLAZA.z).length()
	var cobble := 1.0 - smoothstep(12.5, 14.0, d)
	# the Merchant Quarter (bh-017/bh-018) is cobbled end to end
	var rw := Rect2(6.4, 10.5, 17.0, 23.0)
	var rdx := maxf(maxf(rw.position.x - x, x - rw.end.x), 0.0)
	var rdz := maxf(maxf(rw.position.y - z, z - rw.end.y), 0.0)
	cobble = maxf(cobble, 1.0 - smoothstep(0.4, 2.2, Vector2(rdx, rdz).length()))
	# paths: gate -> plaza -> terrace stair, plaza -> houses
	var path := 0.0
	path = maxf(path, 1.0 - smoothstep(1.8, 3.2, absf(x)) * 1.0 if z > 12.0 and z < 75.0 else 0.0)
	path = maxf(path, 1.0 - smoothstep(1.8, 3.0, absf(x)) if z < -8.0 and z > -16.0 else path)
	for t in [Vector2(-20.6, 2), Vector2(20.6, 6), Vector2(-15, 19.5), Vector2(19.5, -12), Vector2(-17.7, -16.7),
			Vector2(-23.5, 13.5), Vector2(26.4, -4.8), Vector2(-24.9, -9.5)]:
		var dd := _seg_dist(Vector2(x, z), Vector2(PLAZA.x, PLAZA.z), t)
		path = maxf(path, 1.0 - smoothstep(1.3, 2.6, dd))
	var forest := smoothstep(34.0, 42.0, Vector2(x, z).length())
	var n := sin(x * 0.37 + z * 0.23) * 0.5 + 0.5
	return Color(clampf(path * 0.9 + n * 0.1 * (1.0 - cobble), 0, 1), clampf(forest * 0.8 + n * 0.25, 0, 1), clampf(cobble + path * 0.35, 0, 1))

static func _seg_dist(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return p.distance_to(a + ab * t)

# ------------------------------------------------------------------------------------------------------------
func _perimeter() -> void:
	# palisade ring with the south gate; the north arc is replaced by the terrace's back wall
	var n := int(TAU * FENCE_R / 4.0)
	for i in n:
		var a := TAU * (i + 0.5) / n
		var p := Vector3(cos(a) * FENCE_R, 0, sin(a) * FENCE_R)
		var deg := rad_to_deg(a)
		if absf(deg - 90.0) < 6.5:
			continue  # gate gap (south, +Z)
		kit("palisade_fence", p, -deg + 90.0 + 180.0, 1.0, props, true)
	# gatehouse: quoined pillars, an arch and a barred gate — the road south is overrun
	var gz := FENCE_R - 0.6
	for sx in [-3.2, 3.2]:
		kit("pillar_quoin", Vector3(sx, 0, gz), 0.0, 1.0, geo, true)
	kit("arch_quoin", Vector3(0, 0, gz), 0.0, 1.0, geo, true)
	hide_when(kit("gate_iron", Vector3(0, 0, gz + 0.1), 0.0, 1.0, props, true), &"south_gate_open")
	hide_when(bar(Vector3(0, 1.5 + ground(0, gz), gz), Vector3(2.4, 3.0, 0.6)), &"south_gate_open")
	brazier(Vector3(-5.2, 0, gz - 1.6), 3.0, true, true)
	brazier(Vector3(5.2, 0, gz - 1.6), 3.0, false, true)
	kit("banner_torn", Vector3(-3.2, 3.6 + ground(-3.2, gz), gz - 0.75), 0.0, 1.0, deco)
	kit("banner_torn", Vector3(3.2, 3.6 + ground(3.2, gz), gz - 0.75), 0.0, 1.0, deco)
	kit("cart_hay", Vector3(-7.5, 0, gz - 4.0), 12.0, 1.0, props, true)
	breakable("crate", Vector3(6.8, 0, gz - 3.5), 20.0, 20.0, true)
	breakable("barrel", Vector3(7.8, 0, gz - 3.0), 0.0, 20.0, true)
	# lamps along the road from the gate to the plaza
	for z in [30.0, 22.0]:
		lamp_post(Vector3(-3.4, 0, z), 180.0)
		lamp_post(Vector3(3.4, 0, z), 0.0)
	# hard boundary just outside the fence line (the palisade already blocks), open only where the road leaves the gate
	var m := 24
	var gap := asin(2.6 / (FENCE_R + 1.5))
	for i in m:
		var a0 := TAU * i / m
		var a1 := TAU * (i + 1) / m
		if a0 < PI * 0.5 and a1 > PI * 0.5 - 0.001:
			a1 = PI * 0.5 - gap
		elif a0 > PI * 0.5 - 0.001 and a0 < PI * 0.5 + 0.001:
			a0 = PI * 0.5 + gap
		boundary(Vector3(cos(a0), 0, sin(a0)) * (FENCE_R + 1.5), Vector3(cos(a1), 0, sin(a1)) * (FENCE_R + 1.5), 8.0)
	# the road beyond the gate: rails on the embankment, the walk-through into Westreach and a cap behind it
	for sx: float in [-2.8, 2.8]:
		boundary(Vector3(sx, -4.0, FENCE_R + 1.2), Vector3(sx, -4.0, FENCE_R + 12.0), 12.0, 0.5)
	boundary(Vector3(-3.2, -4.0, FENCE_R + 11.0), Vector3(3.2, -4.0, FENCE_R + 11.0), 12.0)
	exit_zone(&"sanctuary_south_gate", Vector3(0, 0, FENCE_R + 7.0), Vector3(5.6, 4.0, 3.0), &"westreach", &"town_gate", "Westreach",
		&"south_gate_open", "The South Gate is barred. Captain Hald keeps the key.")
	signpost(Vector2(5.2, 33.0), [["Westreach roads", Vector2(0, 1)], ["Fountain Plaza", Vector2(0, -1)]])

func _plaza() -> void:
	var fnt := kit("fountain", PLAZA, 0.0, 1.0, props, true)
	light(socket_pos(fnt, "light") + Vector3(0, 0.5, 0), Color(0.95, 0.85, 0.6), 1.6, 9.0, true)
	light(PLAZA + Vector3(0, 1.0, 0), Color(0.3, 0.8, 0.8), 1.0, 6.0)
	for i in 6:
		var a := TAU * i / 6.0 + PI / 6.0
		lamp_post(PLAZA + Vector3(cos(a) * 11.0, 0, sin(a) * 11.0), rad_to_deg(-a) + 90.0)
	# the stash and a notice board corner
	kit("chest", PLAZA + Vector3(-6.5, 0, -6.0), 30.0, 1.0, props, true)
	kit("table", PLAZA + Vector3(7.0, 0, -6.5), -25.0, 1.0, props, true)
	candles(PLAZA + Vector3(7.0, 0.92 + ground(7.0, PLAZA.z - 6.5), -6.5))
	kit("chair", PLAZA + Vector3(8.2, 0, -7.4), 160.0, 1.0, props, true)
	for p in [Vector3(-8.8, 0, 7.0), Vector3(-9.4, 0, 8.0)]:
		breakable("barrel", PLAZA + p, rng.randf() * 360.0, 20.0, true)

func _terrace() -> void:
	var r := TERRACE
	var y := TERRACE_Y
	floor_tiles(r, y)
	# retaining walls: sunk so their capstones sit at the terrace edge
	wall_run(Vector3(r.position.x, y - 4.0, r.end.y), Vector3(r.end.x, y - 4.0, r.end.y), "wall_stone_capped", [2], {}, true)
	wall_run(Vector3(r.position.x, y - 4.0, r.position.y), Vector3(r.position.x, y - 4.0, r.end.y))
	wall_run(Vector3(r.end.x, y - 4.0, r.position.y), Vector3(r.end.x, y - 4.0, r.end.y), "wall_stone_capped", [], {}, true)
	# the back: a tall wall with windows behind the waypoint, closing the plateau's north side
	wall_run(Vector3(r.position.x, y, r.position.y), Vector3(r.end.x, y, r.position.y), "wall_stone_capped", [], {1: "wall_window", 3: "wall_window"})
	wall_run(Vector3(r.position.x, y - 4.0, r.position.y), Vector3(r.end.x, y - 4.0, r.position.y))
	for c in [r.position, Vector2(r.end.x, r.position.y)]:
		arch("pillar_quoin", Vector3(c.x, y, c.y))
	for c in [Vector2(r.position.x, r.end.y), r.end]:
		arch("pillar", Vector3(c.x, y - 4.0, c.y)).scale = Vector3(1, 1.02, 1)
	# grand stair up from the plaza path (climbs north)
	arch("stairs", Vector3(0, 0, r.end.y + 2.0))
	wall_run(Vector3(r.position.x, y, r.end.y), Vector3(r.end.x, y, r.end.y), "wall_low", [2], {}, true)
	# waypoint and its guardians
	teleporter(&"sanctuary_waypoint", Vector3(0, y, -24.5), &"ruined_forest", &"arrival", "Ruined Forest")
	spawn(&"waypoint", Vector3(0, y, -20.6), 180.0)
	# bh-028: the rift Kethrax's fall tore open, to The Sundered Reach (read live: old saves with Kethrax dead see it open)
	var rift := teleporter(&"sanctuary_rift", Vector3(7.4, y, -26.2), &"sundered_reach", &"arrival", "The Sundered Reach", 0.0, true,
		&"boss_kethrax_defeated", "A rift hangs over the dais, sealed shut. It will open once Kethrax falls.")
	rift.rune_tint = Color(0.62, 0.5, 1.0)
	# where a Town Portal's return end stands: the open west half of the terrace, clear of the statue and braziers
	spawn(&"town_portal", Vector3(-8.0, y, -24.8), 90.0)
	for sx in [-6.8, 6.8]:
		kit("statue_knight", Vector3(sx, y, -21.0), 0.0)
		brazier(Vector3(sx * 0.62, y, -20.2), 3.0, sx < 0.0)
	for x in [-6.0, 6.0]:
		kit("banner_torn", Vector3(x, y + 3.75, r.position.y + 0.5), 0.0, 1.0, deco)
	torch(Vector3(-2.0, y + 2.7, r.position.y + 0.42), 0.0)
	torch(Vector3(2.0, y + 2.7, r.position.y + 0.42), 0.0)
	kit("candles_cluster", Vector3(-8.6, y, -28.6), 0.0, 1.0, deco)
	kit("altar", Vector3(3.8, y, -28.6), 0.0)                  # bh-028: moved west for the rift
	decor("cobweb", Vector3(r.position.x + 0.45, y + 3.9, r.position.y + 0.45), -90.0, 0.9, false)

func _houses() -> void:
	for lot in HOUSE_LOTS:
		var p: Vector3 = lot[0]
		var yaw: float = lot[1]
		var h := kit("house_intact_door", p, yaw, 1.0, props, true)
		light(socket_pos(h, "door_light"), Color(1.0, 0.68, 0.35), 2.2, 7.0, false, true)
		# window glow spilling outside
		var fwd := Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(yaw))
		light(p + Vector3(0, 1.6 + ground(p.x, p.z), 0) + fwd * 3.6, Color(1.0, 0.62, 0.3), 1.2, 5.0)
		# yard clutter beside each house
		var side := fwd.cross(Vector3.UP)
		breakable("barrel", p + side * 4.8 + fwd * 2.0, rng.randf() * 360.0, 20.0, true)
		kit("wood_fence", p + side * -5.2 + fwd * 1.0, yaw + 90.0, 1.0, props, true)
		decor("bush_a", p + side * 5.2 - fwd * 2.5, rng.randf() * 360.0, 0.8, true, true)
		door(h, yaw, lot[2], lot[3])
	kit("house_destroyed", Vector3(-26.0, 0, 27.5), 40.0, 1.0, props, true)  # burnt last winter — the first raid (moved west for the Merchant Quarter)
	kit("well", Vector3(7.4, 0, -10.4), 20.0, 1.0, props, true)   # bh-016: moved from (-11, -7) for the Guild House lot

## A solid invisible bar (the South Gate's crossbar) that a flag can lift: registered with hide_when, it stops
## colliding once hidden (MapRoot.apply_flag_visuals).
func bar(center: Vector3, size: Vector3) -> StaticBody3D:
	var sb := StaticBody3D.new()
	sb.name = "GateBar"
	sb.collision_layer = BH.LAYER_WORLD
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	sb.add_child(cs)
	sb.position = center
	geo.add_child(sb)
	return sb

## A walk-in door on a building: the portal at its `door` socket, and the `door_<interior>` spawn 1.6 m outside it
## (facing out) where the hero reappears when leaving the interior.
func door(building: Node3D, yaw: float, interior: StringName, label: String) -> DoorPortal:
	var dp := socket_pos(building, "door")
	var fwd := Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(yaw))
	var portal := DoorPortal.new().setup(interior, &"start", label, true)
	portal.position = dp + fwd * 0.3
	portal.rotation.y = deg_to_rad(yaw)
	markers.add_child(portal)
	var sp := dp + fwd * 1.6
	spawn(StringName("door_%s" % interior), Vector3(sp.x, 0, sp.z), yaw, true)
	return portal

## bh-017: the town's trade street (DataTownRows): a signed gateway on the plaza's south-east edge, then a stand for each
## merchant, crafting station and the Tempo-Caller's shrine along both sides.
func _merchant_row() -> void:
	TownRowBuilder.build(self, def.id)
	# a couple of crates and barrels stacked out of the way at the south end of the square
	for p in [Vector3(11.2, 0, 32.4), Vector3(18.2, 0, 32.6)]:
		breakable("crate" if p.x < 15.0 else "barrel", p, rng.randf() * 90.0, 20.0, true)

func _halls() -> void:
	for hd in HALLS:
		var p: Vector3 = hd[1]
		var yaw: float = hd[2]
		var b := kit(hd[0], p, yaw, 1.0, props, true)
		light(socket_pos(b, "door_light"), Color(1.0, 0.7, 0.4), 2.6, 8.0, false, true)
		var fwd := Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(yaw))
		match String(hd[0]):
			"tavern_exterior":
				light(socket_pos(b, "sign_light"), Color(1.0, 0.72, 0.42), 1.4, 5.0, false, true)
				# warm windows and a bench for the evening drinkers
				light(p + Vector3(0, 1.8 + ground(p.x, p.z), 0) + fwd * 5.6, Color(1.0, 0.6, 0.28), 1.6, 7.0)
				kit("bench", p + fwd * 6.4 + fwd.cross(Vector3.UP) * 3.6, yaw + 90.0, 1.0, props, true)
			"guild_hall_swordfin":
				for sk in ["banner_l", "banner_r"]:
					light(socket_pos(b, sk) + Vector3(0, -1.6, 0) + fwd * 0.6, Color(0.55, 0.7, 1.0), 1.0, 4.0)
			"guild_house":
				light(socket_pos(b, "sign_light"), Color(1.0, 0.78, 0.5), 1.6, 6.0, false, true)
				# bh-027: the great banner of the hero's guild, flying beside the door once they join or found one
				var gh := GuildHallBanner.new()
				gh.position = Vector3(GUILD_BANNER_AT.x, ground(GUILD_BANNER_AT.x, GUILD_BANNER_AT.z), GUILD_BANNER_AT.z)
				gh.rotation.y = deg_to_rad(GUILD_BANNER_YAW)
				markers.add_child(gh)
				for sk in ["banner_l", "banner_r"]:
					light(socket_pos(b, sk) + Vector3(0, -1.6, 0) + fwd * 0.6, Color(0.55, 0.7, 1.0) if sk == "banner_l" else Color(0.75, 0.55, 1.0), 0.9, 4.0)
			"guild_hall_lantern":
				light(socket_pos(b, "lantern_light"), Color(1.0, 0.8, 0.45), 2.4, 8.0, false, true)
				light(socket_pos(b, "lantern_light") + Vector3(0, 1.0, 0), Color(0.72, 0.5, 0.95), 0.9, 6.0)
		door(b, yaw, hd[3], hd[4])

func _greenery() -> void:
	var avoid := func(x: float, z: float) -> bool:
		var d := Vector2(x, z).length()
		if d < 14.5 or absf(x) < 4.0 and z > 0.0:
			return true
		if TERRACE.grow(3.0).has_point(Vector2(x, z)):
			return true
		for f in FOOTPRINTS:
			var local := Vector2(x - f[0], z - f[1]).rotated(deg_to_rad(f[2]))
			if absf(local.x) < f[3] + 1.5 and absf(local.y) < f[4] + 1.5:
				return true
		for lot in [Vector2(-11, -7)]:
			if Vector2(x, z).distance_to(lot) < 7.5:
				return true
		if Rect2(4.0, 9.0, 22.0, 26.0).has_point(Vector2(x, z)):
			return true
		return d > FENCE_R - 1.5
	scatter(["grass_clump"], Rect2(-40, -40, 80, 80), 520, 1.1, Vector2(0.8, 1.3), avoid)
	scatter(["fern", "mushrooms", "rock_small"], Rect2(-40, -40, 80, 80), 70, 2.5, Vector2(0.7, 1.1), avoid, true, true)
	scatter(["bush_a", "bush_b"], Rect2(-40, -40, 80, 80), 26, 4.0, Vector2(0.7, 1.1), avoid, true, true)
	# a few trees inside the walls for silhouette, the rest ring the palisade
	# (the trees at (-31, -4), (31, -6) and (-30, 18) made way for the guild halls and the Salted Marlin)
	for p in [Vector3(9, 0, -34), Vector3(-15, 0, -33), Vector3(-36, 0, 2.5), Vector3(36, 0, 9)]:
		kit("tree_oak_twisted", p, rng.randf() * 360.0, rng.randf_range(0.8, 1.0), props, true)
	var outside := func(x: float, z: float) -> bool:
		var d := Vector2(x, z).length()
		return d < FENCE_R + 2.0 or d > RIM_R + _rim_noise(atan2(z, x)) - 1.0 or (absf(x) < 5.0 and z > 0.0)
	scatter(["tree_pine"], Rect2(-50, -50, 100, 100), 70, 4.2, Vector2(0.8, 1.25), outside, true, true)
	scatter(["tree_dead_a", "tree_oak_twisted"], Rect2(-50, -50, 100, 100), 10, 6.0, Vector2(0.8, 1.1), outside, true, true)

func _background() -> void:
	# escarpment faces below the rim and distant mountains; low mist in the valley
	cliff_ring(Vector3.ZERO, RIM_R + 4.0, -5.0, 24, Vector2(1.4, 1.9))
	for i in 10:
		var a := TAU * i / 10.0 + 0.3
		var p := Vector3(cos(a) * 140.0, -40.0, sin(a) * 140.0)
		decor("cliff_b", p, rng.randf() * 360.0, rng.randf_range(6.0, 9.0), false, false)
	mist(Rect2(-160, -160, 320, 320), -9.0, Color(0.25, 0.3, 0.42), 0.55)
	# moonlit fill so the valley edge reads against the sky
	light(Vector3(0, 12, 36), Color(0.45, 0.55, 0.9), 0.8, 30.0)

# ------------------------------------------------------------------------------------------------------------
# bh-033: the route dressed for daily life (Poly Haven CC0 props, ph_*, docs/ASSET_SOURCES.md) and readable signage.
# Every placement is checked against the town's walking lines, building footprints and shop customer spots; one that
# would block is skipped and reported (`dressing_skipped` on the map root), never forced in.

## Walking lines: gate -> plaza -> terrace stair, and the plaza to every door (the same lines the ground paint uses).
func _walk_lines() -> Array:
	var out := [[Vector2(0, 38), Vector2(0, 12)], [Vector2(0, -4), Vector2(0, -16)]]
	for t in [Vector2(-20.6, 2), Vector2(20.6, 6), Vector2(-15, 19.5), Vector2(19.5, -12), Vector2(-17.7, -16.7),
			Vector2(-23.5, 13.5), Vector2(26.4, -4.8), Vector2(-24.9, -9.5)]:
		# people walk round the fountain: a door's line starts at the plaza ring, not at the basin
		var c := Vector2(PLAZA.x, PLAZA.z)
		out.append([c + (t - c).normalized() * 8.5, t])
	return out

func _clear_spot(p: Vector3, radius: float) -> bool:
	var q := Vector2(p.x, p.z)
	for l in _walk_lines():
		if _seg_dist(q, l[0], l[1]) < radius + 1.3:
			return false
	for f in FOOTPRINTS:
		var local := Vector2(p.x - f[0], p.z - f[1]).rotated(deg_to_rad(f[2]))
		if absf(local.x) < f[3] + radius + 0.6 and absf(local.y) < f[4] + radius + 0.6:
			return false
	for st in DataTownRows.row(def.id).get("stands", []):
		var cw3 := DataTownRows.customer_spot(st)
		if q.distance_to(Vector2(cw3.x, cw3.z)) < radius + 1.4 or q.distance_to(Vector2(st.pos.x, st.pos.z)) < radius + 1.8:
			return false
	return q.length() < FENCE_R - 1.5

var _skipped: Array = []

## A prop if its spot is clear (radius = its footprint), else nothing.
func _dress(name: String, p: Vector3, yaw: float, radius := 0.5, check := true) -> Node3D:
	if check and not _clear_spot(p, radius):
		_skipped.append("%s at (%.1f, %.1f)" % [name, p.x, p.z])
		return null
	return kit(name, p, yaw, 1.0, props, true)

func _bh033_dressing() -> void:
	clear_fn = func(x: float, z: float, r: float) -> bool: return _clear_spot(Vector3(x, 0, z), r)
	# ---- fountain plaza: benches facing the water in three uneven groups, a planted bed beside each ----------------
	# (map-design pass: real benches instead of tables, and soil beds that break the paving at the ring's edge)
	var placed := []
	for i in 36:
		var a := TAU * (i + 0.5) / 36.0
		var at := PLAZA + Vector3(cos(a) * 7.6, 0, sin(a) * 7.6)
		if placed.size() >= 3 or placed.any(func(b): return absf(angle_difference(b, a)) < 1.5) or not _clear_spot(at, 1.4):
			continue
		if vignette("bench_view", at, rad_to_deg(atan2(-cos(a), -sin(a))), {"check": false}):
			placed.append(a)
			for da in [0.36, -0.36, 0.6]:
				var pl := PLAZA + Vector3(cos(a + da) * 10.2, 0, sin(a + da) * 10.2)
				if _clear_spot(pl, 1.35):
					vignette("garden_bed", pl, rad_to_deg(-a) + 90.0, {"scale": 0.9, "check": false})
					break
	root.set_meta(&"plaza_benches", placed.size())
	# ---- the fishmonger's corner by the netmender's house: racks, nets, the morning's catch in crates and baskets -----
	# the clear 3 m spot nearest the netmender's house (Tessaly mends the nets; the catch is sold by her door)
	var fish := Vector3.INF
	var best := INF
	for r in [12.5, 14.0, 16.0, 18.0, 20.0]:
		for deg in range(0, 360, 5):
			var cand := PLAZA + Vector3(cos(deg_to_rad(deg)) * r, 0, sin(deg_to_rad(deg)) * r)
			if Rect2(4.0, 9.0, 24.0, 26.0).has_point(Vector2(cand.x, cand.z)) or not _clear_spot(cand, 2.4):
				continue
			var dd := Vector2(cand.x, cand.z).distance_to(Vector2(-20.6, 2.0))
			if dd < best:
				best = dd
				fish = cand
	if fish == Vector3.INF:
		fish = Vector3(-14.5, 0, -1.0)
	root.set_meta(&"fish_corner", fish)
	_dress("fish_rack", fish + Vector3(-1.4, 0, -1.2), 75.0, 0.9)
	_dress("fishing_nets", fish + Vector3(1.0, 0, -2.4), 20.0, 0.8)
	_dress("ph_wooden_crate_01", fish + Vector3(1.6, 0, 0.2), 15.0, 0.5)
	_dress("ph_wooden_crate_01", fish + Vector3(2.5, 0, -0.6), -20.0, 0.5)
	_dress("ph_wicker_basket_01", fish + Vector3(0.6, 0, 1.0), 40.0, 0.3)
	_dress("ph_wooden_bucket_02", fish + Vector3(-0.6, 0, 0.9), 0.0, 0.4)
	_dress("ph_folding_wooden_stool", fish + Vector3(-0.2, 0, -0.4), 160.0, 0.35)
	# ---- signs at the plaza's edges: every service named once, pointing the way ----------------------------------
	signpost(Vector2(3.4, 13.5), [["Merchant Quarter", Vector2(1, 0.6)], ["South Gate", Vector2(0, 1)], ["Waypoint Terrace", Vector2(0, -1)]])
	signpost(Vector2(-3.4, -5.5), [["Waypoint Terrace", Vector2(0, -1)], ["Guild House", Vector2(-0.6, -0.4)], ["Swordfin Hall", Vector2(1, -0.3)]])
	signpost(Vector2(-11.0, 10.5), [["The Salted Marlin", Vector2(-1, 0.4)], ["Lantern House", Vector2(-1, -0.7)]])
	# ---- the south gate: the watch's post, and a trader's cart once Captain Hald opens the gate -----------------
	var gz := FENCE_R - 0.6
	_dress("ph_woodentable_01", Vector3(-6.8, 0, gz - 6.5), 90.0, 0.7)
	_dress("ph_wine_barrel_01", Vector3(-6.4, 0, gz - 8.4), 30.0, 0.5)
	_dress("ph_wooden_lantern_01", Vector3(-6.0, 0, gz - 5.4), 0.0, 0.3)
	var cart := _dress("cart_hay", Vector3(6.2, 0, gz - 7.2), -15.0, 1.4)
	if cart:
		show_when(cart, &"south_gate_open")
		for d in [[Vector3(4.6, 0, gz - 8.6), "ph_wooden_crate_02", 80.0], [Vector3(5.0, 0, gz - 9.6), "ph_wicker_basket_02", 0.0]]:
			var n := _dress(d[1], d[0], d[2], 0.4)
			if n:
				show_when(n, &"south_gate_open")
	# ---- the waypoint terrace: benches looking out over the plaza, planters on the parapet -----------------------
	for sx in [-5.0, 5.0]:
		vignette("bench_view", Vector3(sx - 0.5, TERRACE_Y, -19.4), 0.0, {"on_ground": false, "check": false})
		kit("ph_planter_box_01", Vector3(sx * 1.6, TERRACE_Y, -18.7), 0.0, 1.0, props)
		decor("kd_flower_purple" if sx < 0 else "kd_flower_yellow", Vector3(sx * 1.6 - 0.2, TERRACE_Y + 0.35, -18.7), 0.0, 0.9, false)
		decor("bush_a", Vector3(sx * 1.6 + 0.3, TERRACE_Y + 0.35, -18.7), 30.0, 0.45, false)
	# ---- Brannoc's smithy: quench tub, the chopping stump with its axe, stock in crates ---------------------------
	var smithy := Vector3(21.2, 0, 22.4)
	_dress("ph_wooden_bucket_02", smithy + Vector3(1.8, 0, -2.6), 0.0, 0.4)
	_dress("ph_tree_stump_01", smithy + Vector3(2.8, 0, -3.6), 30.0, 0.7)
	var axe := _dress("ph_wooden_axe", smithy + Vector3(2.7, 0.3, -3.6), 60.0, 0.1, false)
	if axe:
		axe.rotation_degrees.z = 25.0
	_dress("ph_wooden_crate_02", smithy + Vector3(4.0, 0, -1.2), 90.0, 0.6)
	_dress("ph_wine_barrel_01", smithy + Vector3(4.4, 0, 0.2), 0.0, 0.5)
	# ---- the market square: goods waiting by the stalls -------------------------------------------------------------
	for d in [[Vector3(12.3, 0, 12.6), "ph_wicker_basket_02"], [Vector3(13.1, 0, 12.4), "ph_wicker_basket_01"], [Vector3(18.6, 0, 12.2), "ph_wooden_crate_01"],
			[Vector3(7.4, 0, 24.2), "ph_wooden_bucket_01"], [Vector3(7.8, 0, 18.4), "ph_wooden_crate_02"], [Vector3(23.0, 0, 30.6), "ph_wooden_bucket_02"]]:
		_dress(d[1], d[0], rng.randf() * 360.0, 0.4)
	# ---- the shrine of the fallen: an offering once the Warden is laid to rest -------------------------------------
	var token := _dress("ph_ceramic_pot", Vector3(10.6, 0, 27.4), 0.0, 0.3, false)
	if token:
		show_when(token, &"boss_warden_defeated")
	root.set_meta(&"dressing_skipped", _skipped)
	_map_design()

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the fishing town's working corners, yards and edges, with the prepared Kenney pieces
# (kd_*, DataVignettes). Every group has a purpose and sits at an edge; the walking lines, door approaches and shop
# customer spots stay clear (clear_fn), and a group that would block is skipped and reported, not forced in.

## The first candidate spot that is clear gets the group.
func _first_clear(vname: String, cands: Array, yaw: float, opts := {}) -> Node3D:
	for c: Vector3 in cands:
		var n := vignette(vname, c, yaw, opts)
		if n:
			return n
	return null

func _map_design() -> void:
	var gz := FENCE_R - 0.6
	# ---- south-gate arrival: the watch's woodpile and stores west of the road, planted road edges ----------------
	_first_clear("woodpile", [Vector3(-11.5, 0, 33.0), Vector3(-12.5, 0, 30.5), Vector3(-10.5, 0, 28.0)], -25.0)
	_first_clear("supply_corner", [Vector3(-9.4, 0, 27.4), Vector3(-11.0, 0, 25.0)], 15.0)
	for z in [25.5, 18.0]:
		vignette("flower_border", Vector3(-5.6, 0, z), 90.0)
		vignette("flower_border", Vector3(5.4, 0, z + 1.5), -90.0)
	# ---- Merchant Quarter: produce by the provisioner, fuel by the forge, deliveries waiting at the south end ------
	_first_clear("produce_display", [Vector3(6.4, 0, 12.6), Vector3(6.0, 0, 15.5)], 20.0)
	var fuel := Vector3(24.4, 0, 17.4)
	if _clear_spot(fuel, 0.9):
		kit("kd_log_stack", fuel, 90.0, 0.9, props, true)
	place_near("cargo_stack", Vector3(12.0, 0, 35.0), Vector3(14.0, 0, 33.0), 0.0, 6.0, 8.0)
	# ---- houses and the tavern: each yard does what its household does -----------------------------------------
	# (Tessaly's yard already has the fishmonger's corner with her racks and nets, bh-033)
	var yard := {&"int_netmender": "", &"int_cartographer": "book_corner", &"int_widow": "kitchen_garden",
		&"int_keeper": "woodpile", &"int_refugee": "supply_corner"}
	for lot in HOUSE_LOTS:
		var p: Vector3 = lot[0]
		var yaw: float = lot[1]
		var fwd := Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(yaw))
		var side := fwd.cross(Vector3.UP)
		var vn: String = yard[lot[2]]
		if vn == "":
			continue
		place_near(vn, p + side * 6.5 + fwd * 1.0, p, 5.5, 10.5, yaw)
	var tv: Array = HALLS[0]
	var tfwd := Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(tv[2]))
	var tside := tfwd.cross(Vector3.UP)
	place_near("tavern_stock", tv[1] - tside * 7.0 + tfwd * 1.0, tv[1], 6.0, 11.0, tv[2])
	# ---- greenery: grouped trees inside the walls where lots leave room, pine stands outside the palisade --------
	for c in [Vector3(-34.5, 0, -1.0), Vector3(33.5, 0, 12.5), Vector3(-6.0, 0, -33.5), Vector3(14.0, 0, -31.0)]:
		if _clear_spot(c, 2.0):
			vignette("tree_group", c, rng.randf() * 360.0, {"scale": 0.85, "check": false})
	for i in 7:
		var a := TAU * (i + 0.3) / 7.0
		if sin(a) > 0.2:
			continue          # nothing tall south of the town: the camera looks north over it (and the road stays open)
		vignette("pine_group", Vector3(cos(a) * 44.0, 0, sin(a) * 44.0), rad_to_deg(a), {"check": false})
	vignette("rock_cluster_l", Vector3(-41.0, 0, 20.0), 30.0, {"check": false})
	# one focal tree in the open lot between the Guild House and Swordfin Hall
	for c in [Vector3(18.0, 0, -6.0), Vector3(16.0, 0, -9.0), Vector3(-36.0, 0, 10.0)]:
		if _clear_spot(c, 1.6) and not touches_solid(c, 1.6):
			kit("kd_tree_detailed", c, rng.randf() * 360.0, 0.95, props, true)
			break
	vignette("rock_tall", Vector3(38.5, 0, -24.0), 200.0, {"check": false})
	# ambient accents: the forge, the fountain, the gate's braziers
	accent(Vector3(22.6, 1.0, 21.6), &"torch_crackle", -12.0)
	accent(PLAZA + Vector3(0, 0.8, 0), &"water_splash", -20.0)
	accent(Vector3(0, 1.0, FENCE_R - 2.2), &"torch_crackle", -16.0)
