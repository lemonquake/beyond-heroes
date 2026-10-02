extends MapBuilder
## MAP — The Weeping Causeway, Reedwater Marsh (bh-021; boss, levels 5–7). "Where the Dawnbreakers were betrayed."
##
## Three winters ago the Accord sent Aljay, Roydo and Paul David here to meet an orc war-host that never existed; the
## Accord's own knights turned their sealing bolts on Aljay, and Kethrax rose out of the marsh with the Forsaken Legion.
## A raised stone causeway (8 m wide) runs east from the Marsh Gate of Wyman Outpost (arrival at the west end) over
## black water, past drowned statues of the old garrison and the rusting leavings of that battle, into the ring of the
## Drowned Tollhouse: a round flagged platform (r 16.5) inside broken walls, chain-hung pillars and Legion banners, violet
## soulfire in the braziers. Kethrax waits in the ring; two Legion packs hold the causeway. Entering the ring plays
## the kethrax_intro cutscene (Trigger_kethrax_intro_seen). The cutscene flashback builds this same map as its set.
## Gameplay markers: group "boss_spawn" (meta boss = kethrax, flag = boss_kethrax_defeated), "summons_*" zones.

const R := 16.5
const WATER_Y := -0.9
const WEST := -66.0
const EAST := -15.0
const HALF := 4.0
const SOUL := Color(0.62, 0.32, 1.0)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.02, 0.03, 0.035), "sky_horizon": Color(0.1, 0.13, 0.13),
		"ambient": Color(0.26, 0.3, 0.32), "ambient_energy": 0.75,
		"fog": Color(0.1, 0.13, 0.13), "fog_density": 0.02, "fog_height": 0.6, "fog_height_density": 0.2,
		"sun": Color(0.55, 0.62, 0.8), "sun_energy": 0.55, "sun_rot": Vector3(-42, 30, 0), "glow": 0.9,
		"exposure": 1.1, "contrast": 1.1, "saturation": 0.85,
	})
	_water()
	_causeway()
	_ring()
	_battlefield()
	_map_design()
	spawn(&"arrival", Vector3(WEST + 5.0, 0, 0), 90.0)
	spawn(&"start", Vector3(WEST + 5.0, 0, 0), 90.0)
	exit_zone(&"causeway_marsh_gate", Vector3(WEST - 0.5, 0, 0), Vector3(2.0, 4.0, HALF * 2.0), &"wyman_outpost", &"marsh_gate",
		"Wyman Outpost")
	set_bounds(AABB(Vector3(WEST - 4.0, -2, -R - 4.0), Vector3(-WEST + R + 8.0, 14, (R + 4.0) * 2.0)))
	view("overview", Vector3(-20, 0, 0), 90.0, 60.0, 80.0, 45.0)
	view("arrival", Vector3(WEST + 6.0, 0, 0), 90.0, 45.0, 24.0)
	view("causeway", Vector3(-38, 0, 0), 60.0, 45.0, 30.0)
	view("ring", Vector3(0, 0, 0), 90.0, 52.0, 36.0)

func _water() -> void:
	water(Rect2(-160, -120, 320, 240), WATER_Y, Color(0.08, 0.16, 0.14), Color(0.01, 0.03, 0.03), 0.2, 2.2, 0.08)
	mist(Rect2(-160, -120, 320, 240), WATER_Y + 0.9, Color(0.2, 0.25, 0.26), 0.45)
	for i in 60:
		var x := rng.randf_range(-150.0, 60.0)
		var z := rng.randf_range(-90.0, 90.0)
		if absf(z) < HALF + 5.0 and x < EAST + 2.0 or Vector2(x, z).length() < R + 6.0:
			continue
		decor("tree_dead_a" if i % 2 else "tree_dead_b", Vector3(x, WATER_Y, z), rng.randf() * 360.0, rng.randf_range(0.9, 1.6), false, true, 8.0)
	for i in 140:
		var x := rng.randf_range(WEST, 20.0)
		var z := rng.randf_range(-30.0, 30.0)
		var edge := absf(absf(z) - HALF - 1.2) < 1.4 and x < EAST or absf(Vector2(x, z).length() - R - 1.3) < 1.4
		if not edge:
			continue
		decor("grass_clump", Vector3(x, WATER_Y + 0.3, z), rng.randf() * 360.0, rng.randf_range(1.0, 1.6), false)
	# drowned statues of the old garrison, half sunk
	for p: Vector3 in [Vector3(-52, WATER_Y - 0.6, 9), Vector3(-36, WATER_Y - 0.9, -10), Vector3(-24, WATER_Y - 0.5, 11)]:
		kit("statue_knight", p, rng.randf() * 360.0, 1.1, deco).rotation.z = deg_to_rad(rng.randf_range(-14, 14))
	kit("statue_collapsed", Vector3(-44, WATER_Y, -9), 40.0, 1.0, deco)
	# soulfire will-o'-lights far out on the water
	for i in 5:
		var a := rng.randf() * TAU
		light(Vector3(cos(a) * 40.0 - 10.0, WATER_Y + 1.3, sin(a) * 34.0), SOUL, 1.4, 8.0, false, true)

func _causeway() -> void:
	floor_tiles(Rect2(WEST - 2.0, -HALF, EAST - WEST + 4.0, HALF * 2.0))
	# the stone sides of the causeway down into the water
	for x in range(int(WEST) - 2, int(EAST) + 2, 4):
		for side: float in [-1.0, 1.0]:
			arch("wall_low", Vector3(x + 2.0, -1.6, side * (HALF + 0.1)), 0.0)
	# broken parapet with gaps, pillar stumps every 8 m, chains slung from some
	var i := 0
	for x in range(int(WEST) + 2, int(EAST) - 2, 4):
		i += 1
		for side: float in [-1.0, 1.0]:
			if (i + int(side)) % 3 == 0:
				continue
			arch("wall_low_broken" if (i * 7 + int(side * 3)) % 4 == 0 else "wall_low", Vector3(x + 2.0, 0, side * (HALF - 0.2)), 0.0)
		if i % 2 == 0:
			for side: float in [-1.0, 1.0]:
				var p := Vector3(x, 0, side * (HALF - 0.3))
				arch("pillar_broken", p, rng.randf() * 360.0, 0.9)
				if i % 4 == 0:
					kit("chains_hanging", p + Vector3(0, 1.4, 0), 90.0, 1.0, deco)
	# rails: nobody walks off into the marsh
	boundary(Vector3(WEST - 2.0, -2.0, HALF + 0.3), Vector3(EAST + 1.0, -2.0, HALF + 0.3), 10.0)
	boundary(Vector3(WEST - 2.0, -2.0, -HALF - 0.3), Vector3(EAST + 1.0, -2.0, -HALF - 0.3), 10.0)
	boundary(Vector3(WEST - 2.2, -2.0, -HALF), Vector3(WEST - 2.2, -2.0, HALF), 10.0)
	# the Legion's watch on the causeway: two packs
	enemy_zone("causeway_west", Vector3(-45, 0, 0), 3.5, [&"forsaken_legionnaire", &"forsaken_chainguard"], 3, 0.15)
	enemy_zone("causeway_east", Vector3(-27, 0, 0), 3.5, [&"forsaken_legionnaire", &"forsaken_legionnaire", &"forsaken_chainguard"], 4, 0.2)
	for x: float in [-52.0, -34.0, -20.0]:
		brazier(Vector3(x, 0, HALF - 1.2 if int(x) % 2 == 0 else -HALF + 1.2), 2.6)
		light(Vector3(x, 1.6, HALF - 1.2 if int(x) % 2 == 0 else -HALF + 1.2), SOUL, 1.6, 7.0, false, true)

func _ring() -> void:
	floor_disc(Vector3.ZERO, R + 0.3, -0.02)
	for ii in 9:
		for jj in 9:
			var c := Vector2(-16.0 + ii * 4.0, -16.0 + jj * 4.0)
			if (c.abs() + Vector2(2, 2)).length() < R - 0.4:
				floor_tiles(Rect2(c.x - 2.0, c.y - 2.0, 4, 4))
	kit("ritual_circle", Vector3(0, 0.03, 0), 0.0, 2.2, deco)
	light(Vector3(0, 1.2, 0), SOUL, 2.2, 14.0)
	# the tollhouse's broken ring wall; a gap on the west where the causeway comes in
	var n := 28
	for k in n:
		var a := TAU * (k + 0.5) / n
		var p := Vector3(cos(a) * R, 0, sin(a) * R)
		var deg := rad_to_deg(a)
		if absf(wrapf(deg - 180.0, -180.0, 180.0)) < 16.0:
			continue
		var south := sin(a) > 0.3
		arch("wall_low" if south else ("wall_broken" if k % 5 == 2 else "wall_stone_capped"), p, -deg - 90.0)
		if k % 4 == 0 and not south:
			arch("pillar_quoin", p * 1.02)
	for side: float in [-1.0, 1.0]:
		var a := deg_to_rad(180.0 + side * 16.0)
		arch("pillar_quoin", Vector3(cos(a) * R, 0, sin(a) * R))
	# ring boundary (the gap stays open to the causeway)
	var m := 48
	for k in m:
		var a0 := TAU * k / m
		var a1 := TAU * (k + 1) / m
		var mid := rad_to_deg((a0 + a1) * 0.5)
		if absf(wrapf(mid - 180.0, -180.0, 180.0)) < 14.5:
			continue
		boundary(Vector3(cos(a0) * (R + 0.8), -2.0, sin(a0) * (R + 0.8)), Vector3(cos(a1) * (R + 0.8), -2.0, sin(a1) * (R + 0.8)), 10.0, 0.8)
	# the tollhouse itself: a ruined tower on the north-east rim
	kit("ruin_tower", Vector3(9.5, 0, -10.5), -40.0, 1.0, geo)
	# six chain pillars round the centre, the Legion's banners between them
	for k in 6:
		var a := TAU * (k + 0.5) / 6.0
		var p := Vector3(cos(a) * 9.5, 0, sin(a) * 9.5)
		var pil := arch("pillar_quoin", p, rad_to_deg(a))
		pil.add_to_group(&"arena_pillar")
		kit("chains_hanging", p + Vector3(0, 1.2, 0), rad_to_deg(a), 1.2, deco)
	for k in 5:
		var a := TAU * k / 5.0 + 0.3
		if absf(wrapf(rad_to_deg(a) - 180.0, -180.0, 180.0)) < 25.0:
			continue
		var p := Vector3(cos(a) * (R - 1.4), 0, sin(a) * (R - 1.4))
		kit("banner_torn", p + Vector3(0, 4.0, 0), -rad_to_deg(a) + 90.0, 1.3, deco)
		brazier(p * 0.86, 2.4)
		light(p * 0.86 + Vector3(0, 1.6, 0), SOUL, 2.0, 9.0, false, true)
	var bm := Marker3D.new()
	bm.name = "BossSpawn"
	bm.position = Vector3(6.0, 0, 0)
	bm.set_meta(&"boss", &"kethrax")
	bm.set_meta(&"flag", &"boss_kethrax_defeated")
	bm.add_to_group(&"boss_spawn")
	markers.add_child(bm)
	enemy_zone("summons_n", Vector3(2, 0, -8), 3.5, [&"forsaken_legionnaire"], 3, 0.0)
	enemy_zone("summons_s", Vector3(2, 0, 8), 3.5, [&"forsaken_chainguard"], 3, 0.0)
	flag_trigger(&"kethrax_intro_seen", Vector3(-13.0, 1.0, 0.0), Vector3(2.0, 3.0, HALF * 2.0))

func _battlefield() -> void:
	# what the battle left: broken arms, bones, a shattered cart, an Accord standard trodden into the stones
	for p: Vector3 in [Vector3(-40, 0, 2.4), Vector3(-31, 0, -2.6), Vector3(-6, 0, 6), Vector3(4, 0, -9), Vector3(-9, 0, -4)]:
		decor("weapons_discarded", p, rng.randf() * 360.0, 1.0)
	for p: Vector3 in [Vector3(-48, 0, -2), Vector3(-18, 0, 2.5), Vector3(7, 0, 7), Vector3(-3, 0, 10), Vector3(11, 0, 3)]:
		decor("bones_scatter", p, rng.randf() * 360.0, 1.0)
	decor("skull_pile", Vector3(12.5, 0, 6.0), 200.0, 0.8)
	kit("wagon_broken", Vector3(-58, 0, 2.2), 20.0, 0.9, props)
	kit("banner_torn", Vector3(-14.0, 0.2, 3.0), 10.0, 1.0, deco).rotation.x = deg_to_rad(80.0)
	scatter(["rubble_pile", "rock_small"], Rect2(-60, -3.4, 44, 6.8), 10, 5.0, Vector2(0.5, 0.9),
		func(x, z): return absf(z) < 2.0)

# ------------------------------------------------------------------------------------------------------------
# Map-design pass (2026-10-03): the route's length told by its edges — waterlogged timber and broken cargo drifting
# against the causeway's sides, eroded stone at the water line, reeds — and the drowned tollhouse's own leavings by the
# ring. Nothing stands on the 8 m deck or inside the ring: every encounter keeps its ground.

func _map_design() -> void:
	var dr := RandomNumberGenerator.new()
	dr.seed = hash("causeway_edges")
	var x := WEST + 4.0
	while x < EAST - 2.0:
		var side := -1.0 if dr.randf() < 0.5 else 1.0
		var z := side * (HALF + dr.randf_range(1.4, 3.6))
		match int(dr.randi() % 4):
			0: kit("kd_debris_wood", Vector3(x, WATER_Y - 0.05, z), dr.randf() * 360.0, dr.randf_range(1.0, 1.4), deco)
			1: kit("kd_barrel", Vector3(x, WATER_Y - 0.45, z), dr.randf() * 360.0, 0.9, deco).rotation.z = deg_to_rad(dr.randf_range(50, 80))
			2: kit("kd_crate", Vector3(x, WATER_Y - 0.4, z), dr.randf() * 360.0, 0.9, deco).rotation.x = deg_to_rad(dr.randf_range(-15, 15))
			_: decor("kd_rock_flat", Vector3(x, WATER_Y - 0.08, side * (HALF + 0.9)), dr.randf() * 360.0, dr.randf_range(1.0, 1.5), false)
		if dr.randf() < 0.6:
			decor("kd_grass_large", Vector3(x + dr.randf_range(-1.5, 1.5), WATER_Y + 0.05, side * (HALF + dr.randf_range(2.0, 4.0))),
				dr.randf() * 360.0, dr.randf_range(1.2, 1.8), false)
		x += dr.randf_range(3.5, 6.5)
	# the drowned tollhouse: its goods spilled where the north-east wall fell into the marsh
	for c in [[Vector3(13.5, WATER_Y - 0.3, -15.0), "kd_debris_stone", 1.6], [Vector3(16.0, WATER_Y - 0.5, -12.5), "kd_crate", 1.0],
			[Vector3(18.5, WATER_Y - 0.1, -10.0), "kd_debris_wood", 1.5], [Vector3(-12.0, WATER_Y - 0.5, 15.5), "kd_barrel", 1.0],
			[Vector3(-15.5, WATER_Y - 0.3, 13.0), "kd_debris_wood", 1.3]]:
		kit(c[1], c[0], rng.randf() * 360.0, c[2], deco)
	# and the long view toward it: two leaning dead trees closer to the deck mark the approach
	for c in [Vector3(-30.0, WATER_Y, -9.5), Vector3(-22.0, WATER_Y, 9.0)]:
		decor("kd_log", c, rng.randf() * 360.0, 1.2, false, false, 10.0)
	# ambient accents: black water against the causeway's sides
	for ax in [-58.0, -40.0, -24.0]:
		accent(Vector3(ax, WATER_Y + 0.3, HALF + 2.0), &"water_splash", -18.0)
