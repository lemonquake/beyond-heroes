extends MapBuilder
## MAP 3 — Ancient Catacombs, "Beneath the drowned chapel".
##
## Direction (user references 1 + 2): a crypt of distinct purposeful rooms joined by 4 m corridors, and a flooded
## cistern hall lit from below by luminous teal water with arches standing in it, a stone bridge, a dock, a moored
## boat, scaffolding climbing the tall back wall and warm torchlight against the cool water glow.
##
## Flow: Entrance (arrival from the Ruined Forest) → Guard Hall crossroads → either north through the Sarcophagus
## Hall, or west through Barracks → Storage → Ossuary, both reaching the Ritual Chamber. East of the Guard Hall is
## the Flooded Cistern. The Ritual Chamber's circle breaks the seal on the exit waypoint to the Forgotten Temple;
## a Treasure Alcove hides behind the chamber's east door.
##
##            [Exit ]
##              |
##   Ossuary-[ Ritual Chamber ]-[Treasure]
##     |          |
##  [Storage] [Sarcophagus Hall]
##     |          |
##  [Barracks]-[ Guard Hall ]-[   Flooded Cistern   ]
##                |
##            [Entrance]

const ROOMS := {
	"entrance": Rect2(-10, 16, 20, 12),
	"guard_hall": Rect2(-14, -4, 28, 12),
	"sarcophagi": Rect2(-10, -24, 20, 16),
	"ritual": Rect2(-14, -48, 28, 20),
	"exit": Rect2(-6, -60, 12, 8),
	"treasure": Rect2(18, -44, 8, 8),
	"barracks": Rect2(-34, -8, 16, 16),
	"storage": Rect2(-34, -24, 12, 12),
	"cistern": Rect2(18, -20, 28, 28),
}
const POOL := Rect2(26, -16, 12, 20)
const WATER_Y := -2.4
const POOL_FLOOR := -4.1
const BRIDGE_Z := -10.0

func compose() -> void:
	environment({
		"bg": Color(0.01, 0.012, 0.018), "ambient": Color(0.24, 0.26, 0.4), "ambient_energy": 1.0,
		"fog": Color(0.06, 0.09, 0.12), "fog_density": 0.005, "fog_height": 0.3, "fog_height_density": 0.1,
		"sun": Color(0.5, 0.6, 0.9), "sun_energy": 0.4, "sun_rot": Vector3(-62, 20, 0), "glow": 0.85,
		"exposure": 1.05, "contrast": 1.1, "saturation": 0.9,
	})
	_layout()
	_entrance()
	_guard_hall()
	_sarcophagus_hall()
	_ritual_chamber()
	_exit_sanctum()
	_treasure()
	_barracks()
	_storage()
	_ossuary()
	_cistern()
	set_bounds(AABB(Vector3(-36, -6, -62), Vector3(84, 16, 92)))
	view("overview", Vector3(4, 0, -16), 0.0, 78.0, 118.0, 45.0)
	view("entrance", Vector3(0, 0, 21), 0.0, 52.0, 24.0)
	view("guard_hall", Vector3(0, 0, 2), 0.0, 52.0, 28.0)
	view("cistern", Vector3(32, -1, -7), 0.0, 50.0, 36.0)
	view("cistern_dock", Vector3(33, -2, -3), 20.0, 38.0, 16.0)
	view("ritual", Vector3(0, 0, -39), 0.0, 55.0, 30.0)
	view("sarcophagi", Vector3(0, 0, -16), 0.0, 52.0, 24.0)
	view("west_wing", Vector3(-27, 0, -12), 0.0, 62.0, 40.0)

# ------------------------------------------------------------------------------------------------------------
func _layout() -> void:
	room(ROOMS.entrance, {"doors": {"north": [2]}, "swap": {"north": {2: "arch_quoin"}}})
	corridor(Rect2(-2, 8, 4, 8), "z")
	room(ROOMS.guard_hall, {"doors": {"south": [3], "west": [1], "east": [1]}, "swap": {"north": {3: "arch_quoin"}},
		"gaps": {"north": []}})
	# north door of the guard hall as an arch
	corridor(Rect2(-2, -8, 4, 4), "z")
	room(ROOMS.sarcophagi, {"doors": {"south": [2]}, "swap": {"north": {2: "arch_quoin"}}})
	corridor(Rect2(-2, -28, 4, 4), "z")
	room(ROOMS.ritual, {"doors": {"south": [3], "east": [2], "west": [3]}, "swap": {"north": {3: "arch_quoin"}}})
	corridor(Rect2(-2, -52, 4, 4), "z")
	room(ROOMS.exit, {"doors": {"south": [1]}})
	corridor(Rect2(14, -40, 4, 4), "x")
	room(ROOMS.treasure, {"doors": {"west": [1]}})
	corridor(Rect2(-18, 0, 4, 4), "x")
	room(ROOMS.barracks, {"doors": {"east": [2], "north": [1]}})
	corridor(Rect2(-30, -12, 4, 4), "z")
	room(ROOMS.storage, {"doors": {"south": [1], "north": [1]}})
	# ossuary: a north-south run from the storage, turning east into the ritual chamber's west door
	corridor(Rect2(-30, -36, 4, 12), "z", {"gaps": {"east": [0]}})
	wall_run(Vector3(-30, 0, -36), Vector3(-26, 0, -36))
	corridor(Rect2(-26, -36, 12, 4), "x")
	corridor(Rect2(14, 0, 4, 4), "x")
	_cistern_shell()

# ------------------------------------------------------------------------------------------------------------
func _north_torches(r: Rect2, xs: Array, y := 0.0, h := 2.7) -> void:
	for x in xs:
		torch(Vector3(x, y + h, r.position.y + 0.42), 0.0)

func _side_torch(x: float, z: float, facing_east: bool, y := 0.0) -> void:
	torch(Vector3(x + (0.42 if facing_east else -0.42), y + 2.7, z), 90.0 if facing_east else -90.0)

func _cobwebs(r: Rect2, y := 3.9) -> void:
	decor("cobweb", Vector3(r.position.x + 0.45, y, r.position.y + 0.45), -90.0, rng.randf_range(0.8, 1.3), false)
	decor("cobweb", Vector3(r.end.x - 0.45, y, r.position.y + 0.45), 180.0, rng.randf_range(0.8, 1.3), false)

func _bones(r: Rect2, n: int) -> void:
	scatter(["bones_scatter"], r.grow(-1.5), n, 2.5, Vector2(0.7, 1.0))

func _entrance() -> void:
	var r: Rect2 = ROOMS.entrance
	teleporter(&"catacombs_entrance", Vector3(0, 0, 22.5), &"ruined_forest", &"catacomb_gate", "Ruined Forest")
	spawn(&"start", Vector3(0, 0, 18.6), 180.0)
	spawn(&"entrance", Vector3(0, 0, 18.6), 180.0)
	kit("statue_knight", Vector3(-7.2, 0, 18.6), 0.0)
	kit("statue_knight", Vector3(7.2, 0, 18.6), 0.0)
	brazier(Vector3(-4.2, 0, 25.4), 2.0, true)
	brazier(Vector3(4.2, 0, 25.4), 2.0)
	for x in [-6.0, 6.0]:
		kit("banner_torn", Vector3(x, 3.75, 16.5), 0.0, 1.0, deco)
	_north_torches(r, [-3.2, 3.2])
	kit("rubble_spill", Vector3(-7.5, 0, 26.2), 160.0)
	kit("pillar_broken", Vector3(8.0, 0, 25.0), 30.0)
	_cobwebs(r)
	_bones(r, 3)
	decor("skull_pile", Vector3(8.3, 0, 21.0), 40.0, 0.8, false)
	kit("gate_iron", Vector3(1.4, 0, 15.2), 75.0)  # the old gate stands open, swung against the corridor wall

func _guard_hall() -> void:
	var r: Rect2 = ROOMS.guard_hall
	_north_torches(r, [-9.0, -5.0, 5.0, 9.0])
	kit("table", Vector3(-7.0, 0, 3.2), 8.0)
	kit("table", Vector3(-6.0, 0, -0.2), -12.0)
	kit("table", Vector3(7.0, 0, 2.0), 95.0)
	for p in [Vector3(-8.4, 0, 4.3), Vector3(-5.6, 0, 4.4), Vector3(-7.4, 0, 1.4)]:
		kit("chair", p, rng.randf() * 360.0)
	var fallen := kit("chair", Vector3(-4.2, 0.25, 2.2), 30.0)
	fallen.rotation_degrees.x = 88.0
	kit("bookshelf", Vector3(-12.6, 0, -2.6), 0.0)
	kit("bookshelf", Vector3(11.6, 0, -3.2), 0.0)
	kit("weapon_rack", Vector3(3.6, 0, -3.25), 0.0)
	kit("rug", Vector3(0, 0.005, 2.0), 0.0, 1.0, deco)
	kit("chest", Vector3(12.4, 0, 6.8), -90.0)
	candles(Vector3(-7.0, 0.92, 3.3))
	candles(Vector3(6.8, 0.92, 1.8))
	for p in [Vector3(12.6, 0, -1.9), Vector3(12.9, 0, -0.8), Vector3(-12.6, 0, 6.6)]:
		breakable("barrel", p, rng.randf() * 360.0)
	for p in [Vector3(11.3, 0, -1.5), Vector3(-12.3, 0, 1.0)]:
		breakable("crate", p, rng.randf() * 90.0)
	decor("weapons_discarded", Vector3(1.5, 0, 5.5), 30.0)
	_cobwebs(r)
	_bones(r, 2)
	enemy_zone("guard_hall", Vector3(0, 0, 1), 7.0, [&"hollow_soldier", &"grave_archer"], 6, 0.0)

func _sarcophagus_hall() -> void:
	var r: Rect2 = ROOMS.sarcophagi
	for z in [-19.0, -13.0]:
		for x in [-5.0, 0.0, 5.0]:
			if x == 0.0 and z == -13.0:
				continue  # keep the central aisle clear from the door
			kit("sarcophagus", Vector3(x, 0, z), 90.0 + rng.randf_range(-3, 3))
			candles(Vector3(x + 1.6, 0, z + 0.2), 0.55)
	for x in [-7.5, 7.5]:
		kit("statue_knight", Vector3(x, 0, -22.6), 0.0)
	_north_torches(r, [-3.0, 3.0])
	_side_torch(-10.0, -16.0, true)
	_side_torch(10.0, -12.0, false)
	for p in [Vector3(-8.8, 0, -9.6), Vector3(8.6, 0, -9.4), Vector3(9.0, 0, -18.0)]:
		breakable("urn", p, rng.randf() * 360.0, 10.0)
	decor("skull_pile", Vector3(-8.6, 0, -18.5), 0.0, 0.9, false)
	_cobwebs(r)
	_bones(r, 3)
	enemy_zone("sarcophagi", Vector3(0, 0, -16), 6.0, [&"bonewarden", &"hollow_soldier"], 5, 0.1)

func _ritual_chamber() -> void:
	var r: Rect2 = ROOMS.ritual
	var c := Vector3(0, 0, -38.5)
	kit("ritual_circle", c + Vector3(0, 0.01, 0), 0.0, 1.0, deco)
	for i in 6:
		var a := TAU * i / 6.0 + PI / 6.0
		arch("pillar_quoin", c + Vector3(cos(a) * 7.0, 0, sin(a) * 6.2))
	kit("altar", Vector3(0, 0, -43.8), 0.0)  # leaves a clear walk round either side to the exit arch
	for p in [Vector3(-10.5, 0, -44.5), Vector3(10.5, 0, -44.5)]:
		kit("sarcophagus", p, 0.0)
	kit("statue_collapsed", Vector3(9.0, 0, -32.0), -30.0)
	kit("statue_knight", Vector3(-10.8, 0, -31.0), 0.0)
	kit("chains_hanging", Vector3(-4.0, 1.0, -47.0), 0.0, 1.0, deco)
	kit("chains_hanging", Vector3(4.5, 1.0, -47.2), 20.0, 1.0, deco)
	for i in 5:
		var a := TAU * i / 5.0 + PI / 2.0
		candles(c + Vector3(cos(a) * 3.3, 0.03, sin(a) * 3.3), 0.7)
	# the circle's rune light
	light(c + Vector3(0, 1.2, 0), Color(0.35, 0.8, 1.0), 2.4, 10.0, true, true)
	brazier(Vector3(-3.8, 0, -43.4), 2.2)
	brazier(Vector3(3.8, 0, -43.4), 2.2)
	_north_torches(r, [-9.0, 9.0])
	_side_torch(-14.0, -42.0, true)
	_side_torch(14.0, -32.0, false)
	for i in 3:
		kit("banner_torn", Vector3(-8.0 + i * 8.0, 3.75, -47.5), 0.0, 1.0, deco)
	_cobwebs(r)
	_bones(r, 4)
	decor("skull_pile", Vector3(-12.3, 0, -46.4), 30.0, 1.0, false)
	flag_trigger(&"catacombs_ritual_seen", c + Vector3(0, 1, 0), Vector3(6, 2, 6),
		"The circle flares — far above, a seal cracks open.", 120)
	enemy_zone("ritual", c, 8.0, [&"ashen_cultist", &"ghoul_brute", &"hollow_soldier"], 7, 0.35)

func _exit_sanctum() -> void:
	var r: Rect2 = ROOMS.exit
	teleporter(&"catacombs_exit", Vector3(0, 0, -56.6), &"forgotten_temple", &"arrival", "Forgotten Temple", 0.0, true,
		&"catacombs_ritual_seen", "Sealed. The ritual chamber holds the seal.")
	spawn(&"exit", Vector3(0, 0, -53.4), 180.0)
	brazier(Vector3(-4.4, 0, -58.6), 2.0)
	brazier(Vector3(4.4, 0, -58.6), 2.0)
	kit("gravestone_b", Vector3(-4.8, 0, -53.6), 10.0)
	_cobwebs(r)

func _treasure() -> void:
	var r: Rect2 = ROOMS.treasure
	kit("chest", Vector3(22.0, 0, -42.6), 0.0)
	kit("spikes_trap_plate", Vector3(15.9, 0.0, -38.0), 0.0, 0.9, deco)
	kit("weapon_rack", Vector3(24.6, 0, -40.0), -90.0)
	breakable("urn", Vector3(20.4, 0, -43.1), 0.0, 10.0)
	breakable("urn", Vector3(24.8, 0, -37.4), 0.0, 10.0)
	breakable("statue_small", Vector3(19.1, 0, -43.1), 150.0, 40.0)
	decor("skull_pile", Vector3(24.6, 0, -42.6), 200.0, 0.8, false)
	candles(Vector3(20.2, 0, -42.8), 0.9)
	candles(Vector3(23.9, 0, -42.9), 0.9)
	_cobwebs(r, 3.8)
	enemy_zone("treasure", Vector3(22, 0, -40), 2.5, [&"bonewarden"], 1, 1.0)

func _barracks() -> void:
	var r: Rect2 = ROOMS.barracks
	for i in 4:
		kit("bed", Vector3(-32.4, 0, -5.4 + i * 3.4), 0.0)
	kit("bedroll", Vector3(-23.0, 0, 5.8), 10.0, 1.0, deco)
	kit("bedroll", Vector3(-21.0, 0, 6.0), -8.0, 1.0, deco)
	kit("table", Vector3(-26.0, 0, -3.8), 90.0)
	kit("chair", Vector3(-24.8, 0, -3.0), 200.0)
	kit("weapon_rack", Vector3(-20.0, 0, -7.25), 0.0)
	kit("chest", Vector3(-19.4, 0, -4.6), -90.0)
	brazier(Vector3(-26.0, 0, 2.0), 2.2, true)
	for p in [Vector3(-19.5, 0, 6.6), Vector3(-20.6, 0, 6.8), Vector3(-33.0, 0, 6.8)]:
		breakable("barrel", p, rng.randf() * 360.0)
	_north_torches(r, [-30.0, -22.0])
	_cobwebs(r)
	_bones(r, 2)
	enemy_zone("barracks", Vector3(-26, 0, 0), 6.0, [&"hollow_soldier", &"grave_archer"], 5, 0.0)

func _storage() -> void:
	var r: Rect2 = ROOMS.storage
	var i := 0
	for p in [Vector3(-33.0, 0, -22.9), Vector3(-32.0, 0, -22.8), Vector3(-33.1, 0, -21.8), Vector3(-23.2, 0, -22.9),
			Vector3(-23.0, 0, -21.9), Vector3(-24.1, 0, -22.8)]:
		breakable("crate" if i % 2 == 0 else "barrel", p, rng.randf() * 360.0)
		i += 1
	kit("crate", Vector3(-33.0, 0.95, -22.9), 12.0)
	kit("cart_hay", Vector3(-24.2, 0, -15.8), 70.0)
	for p in [Vector3(-33.2, 0, -14.0), Vector3(-33.2, 0, -15.0)]:
		breakable("urn", p, 0.0, 10.0)
	_north_torches(r, [-26.0])
	_cobwebs(r)
	enemy_zone("storage", Vector3(-28, 0, -18), 4.0, [&"ghoul_brute"], 1, 0.2)

func _ossuary() -> void:
	# coffins laid along the walls, skulls piled in the corners, candles guttering
	for z in [-34.0, -29.5]:
		kit("coffin", Vector3(-29.2, 0, z), 90.0 + rng.randf_range(-4, 4))
	for x in [-22.0, -17.0]:
		kit("coffin", Vector3(x, 0, -35.2), rng.randf_range(-4, 4))
	decor("skull_pile", Vector3(-26.8, 0, -35.0), 0.0, 1.0, false)
	decor("skull_pile", Vector3(-15.2, 0, -32.8), 90.0, 0.8, false)
	candles(Vector3(-27.0, 0, -26.0), 0.9)
	candles(Vector3(-19.5, 0, -32.9), 0.9)
	torch(Vector3(-20.0, 2.7, -35.58), 0.0)
	scatter(["bones_scatter"], Rect2(-29.5, -35.5, 3, 10), 3, 2.5, Vector2(0.6, 0.9))
	decor("cobweb", Vector3(-29.55, 3.9, -35.55), -90.0, 1.1, false)
	enemy_zone("ossuary", Vector3(-24, 0, -34), 4.0, [&"shade_stalker"], 3, 0.15)

# ------------------------------------------------------------------------------------------------------------
# flooded cistern (reference 1): ledges around a sunken pool, tall back wall with a second storey

func _cistern_shell() -> void:
	var r: Rect2 = ROOMS.cistern
	# ledge floor (every 4 m cell outside the pool)
	for i in int(r.size.x / WALL):
		for j in int(r.size.y / WALL):
			var cell := Rect2(r.position.x + i * WALL, r.position.y + j * WALL, WALL, WALL)
			if POOL.encloses(cell):
				continue
			floor_tiles(cell)
	room(r, {"floor": false, "doors": {"west": [5]}, "swap": {"north": {1: "wall_window", 5: "wall_window"}}})
	# second storey on the north and east walls: the tall back wall of the cutaway
	wall_run(Vector3(r.position.x, 4.0, r.position.y), Vector3(r.end.x, 4.0, r.position.y), "wall_stone_capped", [],
		{2: "wall_window", 4: "wall_window"})
	wall_run(Vector3(r.end.x, 4.0, r.position.y), Vector3(r.end.x, 4.0, r.position.y + 12.0), "wall_stone_capped", [], {}, true)
	arch("pillar_quoin", Vector3(r.end.x, 4.0, r.position.y))
	arch("pillar_quoin", Vector3(r.position.x, 4.0, r.position.y))
	# pit: retaining walls below the ledge, pool floor, parapets with gaps for the bridge and the dock stair
	var p := POOL
	floor_tiles(p, POOL_FLOOR)
	wall_run(Vector3(p.position.x, -4.1, p.position.y), Vector3(p.end.x, -4.1, p.position.y))
	wall_run(Vector3(p.position.x, -4.1, p.end.y), Vector3(p.end.x, -4.1, p.end.y), "wall_stone_capped", [1])  # stair gap: no lip on the ramp
	wall_run(Vector3(p.position.x, -4.1, p.position.y), Vector3(p.position.x, -4.1, p.end.y))
	wall_run(Vector3(p.end.x, -4.1, p.position.y), Vector3(p.end.x, -4.1, p.end.y))
	var bridge_seg := int((BRIDGE_Z - 2.0 - p.position.y) / WALL)
	wall_run(Vector3(p.position.x, 0, p.position.y), Vector3(p.end.x, 0, p.position.y), "wall_low", [], {1: "wall_low_broken"})
	wall_run(Vector3(p.position.x, 0, p.end.y), Vector3(p.end.x, 0, p.end.y), "wall_low", [1], {}, true)
	wall_run(Vector3(p.position.x, 0, p.position.y), Vector3(p.position.x, 0, p.end.y), "wall_low", [bridge_seg])
	wall_run(Vector3(p.end.x, 0, p.position.y), Vector3(p.end.x, 0, p.end.y), "wall_low", [bridge_seg], {3: "wall_low_broken"}, true)
	for c in [p.position, Vector2(p.end.x, p.position.y), Vector2(p.position.x, p.end.y), p.end]:
		arch("pillar", Vector3(c.x, 0, c.y)).scale = Vector3(1, 0.36, 1)
	arch("bridge_stone", Vector3(p.get_center().x, 0, BRIDGE_Z))
	# dock stair: down from the south ledge to a landing and two jetty sections at the water line
	arch("stairs", Vector3(32, -2.0, 2.0), 180.0)
	floor_tiles(Rect2(30, -4, 4, 4), -2.0)
	for x in [31.0, 33.0]:
		arch("dock_planks", Vector3(x, -2.0, -6.0))
	# keep the player on the landing/jetty: thin invisible rails over the water edges
	boundary(Vector3(30, -2.0, -8.0), Vector3(30, -2.0, 0.0), 1.4, 0.2)
	boundary(Vector3(34, -2.0, -8.0), Vector3(34, -2.0, 0.0), 1.4, 0.2)
	boundary(Vector3(30, -2.0, -8.0), Vector3(34, -2.0, -8.0), 1.4, 0.2)

func _cistern() -> void:
	var r: Rect2 = ROOMS.cistern
	var p := POOL
	water(p.grow(0.4), WATER_Y, Color(0.08, 0.55, 0.55), Color(0.01, 0.06, 0.09), 0.6, 1.4)
	mist(p.grow(-1.0), WATER_Y + 0.35, Color(0.4, 0.75, 0.75), 0.25)
	# arches and pillars standing in the water (tops just above the ledge)
	for x in [30.0, 34.0]:
		arch("arch_quoin", Vector3(x, POOL_FLOOR, -14.0))
	arch("pillar_quoin", Vector3(28.0, POOL_FLOOR, -14.0))
	arch("pillar_quoin", Vector3(36.0, POOL_FLOOR, -14.0))
	arch("pillar_broken", Vector3(28.4, POOL_FLOOR, 0.6), 40.0)
	# water-borne storytelling: moored boat, drifting coffins and crates
	kit("boat_rowing", Vector3(35.6, WATER_Y - 0.3, -5.2), 92.0, 1.0, deco)
	kit("coffin", Vector3(28.4, WATER_Y - 0.25, -3.4), 25.0, 1.0, deco)
	kit("coffin", Vector3(36.0, WATER_Y - 0.28, 1.2), -40.0, 1.0, deco)
	kit("crate", Vector3(29.0, WATER_Y - 0.5, -8.2), 33.0, 1.0, deco).rotation_degrees.z = 12.0
	kit("barrel", Vector3(36.4, WATER_Y - 0.45, -12.0), 0.0, 1.0, deco).rotation_degrees.x = 80.0
	kit("rubble_pile", Vector3(37.0, POOL_FLOOR, -15.0), 20.0, 1.0, deco)
	# scaffolding climbing the back wall, ladders, a winch over the pool
	kit("scaffold_platform", Vector3(21.2, 0, -18.7), 0.0)
	kit("scaffold_platform", Vector3(21.2, 3.0, -18.7), 0.0, 1.0, deco)
	kit("ladder", Vector3(22.5, 0, -17.55), 0.0).rotation_degrees.x = -12.0
	kit("ladder", Vector3(20.0, 3.05, -17.6), 0.0, 1.0, deco).rotation_degrees.x = -12.0
	kit("winch", Vector3(32.0, 0, -18.0), 90.0)
	kit("chains_hanging", Vector3(44.6, 3.0, -8.0), 90.0, 1.0, deco)
	kit("crate", Vector3(20.2, 0, -14.5), 10.0)
	breakable("barrel", Vector3(19.3, 0, -12.8), 0.0)
	breakable("barrel", Vector3(44.7, 0, -18.8), 0.0)
	breakable("crate", Vector3(44.6, 0, 6.6), 20.0)
	kit("table", Vector3(42.5, 0, -17.8), 0.0)
	candles(Vector3(42.0, 0.92, -17.8), 0.8)
	kit("bedroll", Vector3(44.2, 0, 1.5), 90.0, 1.0, deco)
	# light: teal from the water, warm torches on the walls, cold shafts through the high windows
	for z in [-13.0, -6.0, 1.0]:
		light(Vector3(32, WATER_Y + 0.6, z), Color(0.2, 0.85, 0.8), 2.6, 11.0, false, false)
	light(Vector3(32, WATER_Y + 1.2, BRIDGE_Z + 3.0), Color(0.25, 0.9, 0.85), 1.6, 9.0, true)
	_north_torches(r, [26.0, 38.0], 0.0, 2.7)
	_north_torches(r, [24.0, 32.0, 40.0], 4.0, 2.2)
	for z in [-14.0, -2.0, 5.0]:
		_side_torch(r.end.x, z, false)
	_side_torch(r.position.x, -12.0, true)
	_cobwebs(r, 7.8)
	enemy_zone("cistern_ledge_w", Vector3(21, 0, -6), 3.5, [&"grave_archer", &"hollow_soldier"], 4, 0.0)
	enemy_zone("cistern_ledge_e", Vector3(43, 0, -6), 3.5, [&"shade_stalker", &"grave_archer"], 4, 0.25)
	enemy_zone("cistern_bridge", Vector3(32, 0, BRIDGE_Z), 3.0, [&"bonewarden"], 1, 0.5)
