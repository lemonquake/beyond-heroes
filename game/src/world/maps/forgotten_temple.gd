extends MapBuilder
## MAP 4 — Forgotten Temple, "Halls of the first oath" (levels 7–10).
##
## A temple of the knightly order clinging to a mountain ledge. Arrival courtyard (corrupted obelisks, the dead
## garden) → the roofless Hall of Oaths: a colonnaded nave lined with knight statues, moonlight falling where the
## roof used to be → a flooded west chapel and a collapsed east library → up the grand stair into the raised
## sanctum, where the temple's facade stands as the backdrop. Its door is sealed by a violet membrane; the altar of
## the first oath on the portico breaks the seal, which also wakes the waypoint to the Hollow Throne.

const COURT := Rect2(-14, 8, 28, 16)
const NAVE := Rect2(-10, -24, 20, 32)
const WEST_CHAPEL := Rect2(-22, -12, 12, 12)
const EAST_CHAPEL := Rect2(10, -20, 12, 12)
const SANCTUM := Rect2(-14, -44, 28, 20)
const SY := 2.0
const FACADE := Vector3(0, SY, -40)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.03, 0.03, 0.08), "sky_horizon": Color(0.14, 0.12, 0.22),
		"ambient": Color(0.3, 0.3, 0.46), "ambient_energy": 0.85,
		"fog": Color(0.12, 0.11, 0.2), "fog_density": 0.006, "fog_height": -4.0, "fog_height_density": 0.08,
		"sun": Color(0.6, 0.68, 1.0), "sun_energy": 0.7, "sun_rot": Vector3(-58, 25, 0), "glow": 0.85,
		"exposure": 1.05, "contrast": 1.1, "saturation": 0.9,
	})
	_courtyard()
	_nave()
	_chapels()
	_sanctum()
	_surroundings()
	set_bounds(AABB(Vector3(-24, -2, -46), Vector3(48, 14, 72)))
	view("overview", Vector3(0, 0, -12), 0.0, 75.0, 95.0, 45.0)
	view("courtyard", Vector3(0, 0, 16), 0.0, 48.0, 26.0)
	view("nave", Vector3(0, 0, -8), 0.0, 52.0, 34.0)
	view("sanctum", Vector3(0, SY, -31), 0.0, 45.0, 30.0)
	view("chapels", Vector3(0, 0, -10), 0.0, 62.0, 46.0)

# ------------------------------------------------------------------------------------------------------------
func _courtyard() -> void:
	var r := COURT
	room(r, {"north": "wall_low", "west": "wall_broken", "east": "wall_broken", "gaps": {"north": [3]},
		"swap": {"west": {1: "wall_low_broken"}, "east": {2: "wall_low_broken"}, "south": {1: "wall_low_broken", 5: "wall_low_broken"}}})
	teleporter(&"temple_arrival", Vector3(0, 0, 18.5), &"catacombs", &"exit", "Ancient Catacombs")
	spawn(&"arrival", Vector3(0, 0, 14.2), 180.0)
	spawn(&"start", Vector3(0, 0, 14.2), 180.0)
	for x in [-2.6, 2.6]:
		arch("pillar_quoin", Vector3(x, 0, 8.0))
	brazier(Vector3(-3.6, 0, 21.6), 3.2, true)
	brazier(Vector3(3.6, 0, 21.6), 3.2)
	for p in [Vector3(-10.5, 0, 12.0), Vector3(10.5, 0, 19.5)]:
		kit("obelisk_corrupted", p, rng.randf() * 360.0)
		light(p + Vector3(0, 2.5, 0), Color(0.62, 0.22, 1.0), 2.8, 10.0, false, true)
	kit("tree_dead_a", Vector3(-11.0, 0, 21.0), 40.0, 0.8)
	kit("tree_dead_b", Vector3(11.5, 0, 11.5), 200.0, 0.8)
	kit("statue_collapsed", Vector3(7.0, 0, 13.0), 160.0)
	for i in 5:
		kit("gravestone_a" if i % 2 else "gravestone_b", Vector3(-12.0 + i * 1.6, 0, 16.0 + (i % 2) * 0.8), rng.randf_range(-12, 12))
	scatter(["rubble_pile", "rock_medium"], r.grow(-2.5), 5, 5.0, Vector2(0.6, 0.9), func(x, z): return absf(x) < 5.0, true, true)
	scatter(["bones_scatter"], r.grow(-3.0), 3, 4.0, Vector2(0.7, 1.0), func(x, z): return absf(x) < 3.0)
	enemy_zone("courtyard", Vector3(0, 0, 14), 8.0, [&"ashen_cultist", &"ashen_acolyte", &"hollow_soldier", &"necromancer"], 6, 0.2)

func _nave() -> void:
	var r := NAVE
	room(r, {"south": "", "north": "", "doors": {"west": [4], "east": [2]},
		"swap": {"west": {1: "wall_window", 6: "wall_window"}, "east": {0: "wall_window", 5: "wall_broken", 6: "wall_window"}}})
	for z in [4.0, -2.0, -8.0, -14.0, -20.0]:
		for x in [-5.5, 5.5]:
			if x > 0.0 and z == -8.0:
				arch("pillar_broken", Vector3(x, 0, z), 70.0)
				kit("rubble_spill", Vector3(x + 1.0, 0, z + 1.5), 200.0)
				continue
			arch("pillar_quoin", Vector3(x, 0, z))
	for z in [1.0, -11.0, -17.0]:
		kit("statue_knight", Vector3(-8.4, 0, z), 90.0)
		kit("statue_knight", Vector3(8.4, 0, z), -90.0)
	for i in 8:
		kit("rug", Vector3(0, 0.01, 6.0 - i * 3.05), 90.0, 1.0, deco)
	for z in [-5.0, -17.0]:
		brazier(Vector3(-3.2, 0, z), 3.4, z < -10.0)
		brazier(Vector3(3.2, 0, z), 3.4)
	for z in [-3.0, -19.0]:
		kit("banner_torn", Vector3(-9.5, 3.7, z), 90.0, 1.0, deco)
		kit("banner_torn", Vector3(9.5, 3.7, z), -90.0, 1.0, deco)
	_side_torch(-10.0, -1.0, true)
	_side_torch(10.0, 4.0, false)
	# moonlight through the missing roof
	for p in [Vector3(-3.0, 13.0, -2.0), Vector3(2.5, 13.0, -14.0)]:
		shaft(p, Vector3(0.18, -1, 0.25), 14.0, 2.2, Color(0.55, 0.65, 1.0), 0.07)
		light(p + Vector3(2.0, -12.0, 2.8), Color(0.55, 0.65, 1.0), 1.6, 8.0)
	scatter(["bones_scatter"], r.grow(-2.0), 4, 4.0, Vector2(0.7, 1.0), func(x, z): return absf(x) < 2.0)
	for p in [Vector3(-9.0, 0, 6.8), Vector3(8.9, 0, -22.8), Vector3(-8.8, 0, -23.0)]:
		breakable("urn", p, 0.0, 10.0)
	decor("cobweb", Vector3(r.position.x + 0.45, 3.9, r.position.y + 0.45), -90.0, 1.2, false)
	enemy_zone("nave_south", Vector3(0, 0, 0), 6.0, [&"bonewarden", &"hollow_soldier", &"grave_archer", &"rune_golem"], 7, 0.15)
	enemy_zone("nave_north", Vector3(0, 0, -16), 6.0, [&"aether_wisp", &"ashen_cultist", &"grave_archer"], 5, 0.25)

func _side_torch(x: float, z: float, facing_east: bool, y := 0.0) -> void:
	torch(Vector3(x + (0.42 if facing_east else -0.42), y + 2.7, z), 90.0 if facing_east else -90.0)

func _chapels() -> void:
	# west: the flooded chapel — a sarcophagus in shallow water, candles on the ledge
	var w := WEST_CHAPEL
	room(w, {"east": "", "swap": {"north": {1: "wall_window"}}})
	water(w.grow(-0.5), 0.14, Color(0.05, 0.2, 0.24), Color(0.02, 0.07, 0.09), 0.12, 0.25, 0.05)
	kit("sarcophagus", Vector3(-16.0, 0, -7.0), 0.0)
	candles(Vector3(-16.0, 1.36, -7.0), 1.0)
	kit("coffin", Vector3(-20.6, 0.05, -2.2), 80.0)
	breakable("statue_small", Vector3(-20.5, 0, -10.6), 30.0, 40.0)
	for p in [Vector3(-12.0, 0, -10.8), Vector3(-20.8, 0, -8.0)]:
		candles(p, 1.0)
	kit("banner_torn", Vector3(-19.0, 3.7, -11.5), 0.0, 1.0, deco)
	decor("cobweb", Vector3(w.position.x + 0.45, 3.9, w.position.y + 0.45), -90.0, 1.0, false)
	enemy_zone("west_chapel", Vector3(w.get_center().x, 0, w.get_center().y), 4.0, [&"shade_stalker", &"shade_stalker", &"frost_revenant"], 3, 0.2)
	# east: the library, half its outer wall fallen away
	var e := EAST_CHAPEL
	room(e, {"west": "", "swap": {"east": {1: "wall_broken"}, "north": {0: "wall_window"}}})
	for x in [12.2, 15.4]:
		kit("bookshelf", Vector3(x, 0, e.position.y + 0.85), 0.0)
	kit("bookshelf", Vector3(20.9, 0, -18.2), -90.0)
	kit("table", Vector3(15.0, 0, -13.5), 10.0)
	kit("chair", Vector3(14.0, 0, -12.5), 200.0)
	var ch := kit("chair", Vector3(16.6, 0.25, -12.4), 60.0)
	ch.rotation_degrees.x = 88.0
	candles(Vector3(15.0, 0.92, -13.5), 1.2)
	kit("chest", Vector3(20.6, 0, -9.4), -90.0)
	decor("rubble_spill", Vector3(21.5, 0, -14.0), -90.0, 0.9, true, true)
	torch(Vector3(18.5, 2.7, e.position.y + 0.42), 0.0)
	enemy_zone("library", Vector3(e.get_center().x, 0, e.get_center().y), 4.0, [&"aether_wisp", &"shade_stalker"], 3, 0.3)
	enemy_zone("library_chest", Vector3(20.6, 0, -11.3), 0.9, [&"treasure_mimic"], 1, 0.0)

func _sanctum() -> void:
	var r := SANCTUM
	floor_tiles(r, SY)
	# retaining wall facing the nave, with the grand stair; parapet on top
	wall_run(Vector3(r.position.x, SY - 4.0, r.end.y), Vector3(r.end.x, SY - 4.0, r.end.y), "wall_stone_capped", [3], {}, true)
	wall_run(Vector3(r.position.x, SY, r.end.y), Vector3(r.end.x, SY, r.end.y), "wall_low", [3], {}, true)
	arch("stairs", Vector3(0, 0, r.end.y + 2.0))
	for s in ["west", "east", "north"]:
		var a: Vector3
		var b: Vector3
		match s:
			"west":
				a = Vector3(r.position.x, 0, r.position.y)
				b = Vector3(r.position.x, 0, r.end.y)
			"east":
				a = Vector3(r.end.x, 0, r.position.y)
				b = Vector3(r.end.x, 0, r.end.y)
			_:
				a = Vector3(r.position.x, 0, r.position.y)
				b = Vector3(r.end.x, 0, r.position.y)
		wall_run(a + Vector3(0, SY - 4.0, 0), b + Vector3(0, SY - 4.0, 0), "wall_stone_capped", [], {}, s == "east")
		wall_run(a + Vector3(0, SY, 0), b + Vector3(0, SY, 0), "wall_stone_capped", [], {} if s != "west" else {2: "wall_window"}, s == "east")
	for c in [r.position, Vector2(r.end.x, r.position.y)]:
		arch("pillar_quoin", Vector3(c.x, SY, c.y))
	# the facade and its sealed door
	arch("temple_facade", FACADE)
	blocker(FACADE + Vector3(0, 1.0 + 2.0, -1.0), Vector3(2.8, 4.0, 0.8))
	var seal := MeshInstance3D.new()
	seal.name = "DoorSeal"
	var qm := QuadMesh.new()
	qm.size = Vector2(2.8, 4.6)
	seal.mesh = qm
	var sm := VFXLib.glow_material(Color(0.55, 0.15, 0.9), 1.4)
	sm.set_shader_parameter("alpha", 0.85)
	seal.material_override = sm
	seal.position = FACADE + Vector3(0, 1.0 + 2.3, -0.45)
	deco.add_child(seal)
	hide_when(seal, &"temple_seal_broken")
	var seal_light := light(FACADE + Vector3(0, 3.2, 0.6), Color(0.6, 0.2, 1.0), 3.0, 10.0, true, true)
	hide_when(seal_light, &"temple_seal_broken")
	# the altar of the first oath stands at the foot of the temple steps, facing the stair
	kit("altar", Vector3(0, SY, -33.1), 0.0)
	flag_trigger(&"temple_seal_broken", Vector3(0, SY + 1.0, -31.6), Vector3(3.6, 2.0, 1.8),
		"The seal of the first oath shatters. The way to the Hollow Throne lies open.", 400)
	# waypoint to the boss arena on the west side of the sanctum, locked until the seal is broken
	kit("ritual_circle", Vector3(-7.0, SY + 0.01, -30.0), 0.0, 1.0, deco)
	teleporter(&"temple_throne_gate", Vector3(-7.0, SY, -30.0), &"boss_arena", &"arrival", "The Hollow Throne", 90.0, true,
		&"temple_seal_broken", "Sealed. Break the seal at the altar of the first oath, before the temple steps.")
	spawn(&"sanctum", Vector3(0, SY, -25.8), 180.0)
	for sx in [-8.8, 8.8]:
		kit("statue_knight", Vector3(sx, SY, -35.2), 0.0)
	for sx in [-3.4, 3.4]:
		brazier(Vector3(sx, SY, -26.4), 3.4, sx < 0.0)
	kit("statue_collapsed", Vector3(8.0, SY, -29.0), 200.0)
	candles(Vector3(-1.6, SY, -31.9), 1.0)
	candles(Vector3(1.6, SY, -31.9), 1.0)
	for p in [Vector3(-11.0, SY, -40.0), Vector3(11.0, SY, -38.0)]:
		kit("obelisk_corrupted", p, rng.randf() * 360.0)
		light(p + Vector3(0, 2.5, 0), Color(0.62, 0.22, 1.0), 2.6, 9.0, false, true)
	for z in [-30.0, -38.0]:
		kit("banner_torn", Vector3(r.position.x + 0.5, SY + 3.7, z), 90.0, 1.0, deco)
		kit("banner_torn", Vector3(r.end.x - 0.5, SY + 3.7, z), -90.0, 1.0, deco)
	_side_torch(r.position.x, -34.0, true, SY)
	_side_torch(r.end.x, -34.0, false, SY)
	enemy_zone("sanctum", Vector3(0, SY, -32), 7.0, [&"aether_sentinel", &"ghoul_brute", &"ashen_acolyte", &"ashen_cultist", &"rune_golem"], 5, 0.5)

func _surroundings() -> void:
	# the ledge falls away into cloud; mountains hang in the fog
	cliff_ring(Vector3(0, 0, -10), 28.0, -1.5, 20, Vector2(1.6, 2.2), 38.0)
	for i in 8:
		var a := TAU * i / 8.0 + 0.4
		decor("cliff_b", Vector3(cos(a) * 130.0, -45.0, -10.0 + sin(a) * 130.0), rng.randf() * 360.0, rng.randf_range(6.0, 9.0), false)
	mist(Rect2(-150, -160, 300, 300), -8.0, Color(0.22, 0.2, 0.34), 0.6)
	# the space outside the built area is a sheer drop: keep the player inside the walls
	boundary(Vector3(-14, 0, 24.4), Vector3(14, 0, 24.4), 6.0)
