extends MapBuilder
## MAP — The Sundered Reach (bh-028). "Where the sky came apart."
##
## When Kethrax fell, the seal he had been feeding on broke, and a rift opened above Malasugue's waypoint terrace. It
## leads to a shard of old stone floating in the dark between the stars: a round plaza of a fortress nobody remembers,
## broken off and hung in the void. Five gates stand in a half ring round its north side, each leading down into one
## of the special dungeons (DataDungeonsSpecial): only Class A heroes may pass them. The arrival dais on the south rim
## leads home to the Sanctuary Terrace. No monsters walk the Reach itself.
## Gameplay markers: spawns "arrival"/"start", one dungeon gate per special dungeon, the return teleporter.

const R := 30.0
const RIM := Color(0.62, 0.5, 1.0)
const ARRIVAL := Vector3(0, 0, 22.5)
const RETURN_AT := Vector3(0, 0, 26.5)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.01, 0.008, 0.03), "sky_horizon": Color(0.12, 0.08, 0.2),
		"ambient": Color(0.36, 0.34, 0.46), "ambient_energy": 0.95,
		"fog": Color(0.08, 0.06, 0.14), "fog_density": 0.008, "fog_height": -4.0, "fog_height_density": 0.08,
		"sun": Color(0.75, 0.7, 1.0), "sun_energy": 0.6, "sun_rot": Vector3(-48, 35, 0), "glow": 1.0,
		"exposure": 1.1, "contrast": 1.08, "saturation": 0.95,
	})
	_plaza()
	_rim()
	_void()
	for gid in DataDungeons.gates_on(def.id):
		var gs: Dictionary = DataDungeons.get_def(gid).surface
		dungeon_gate(gid, gs.pos, gs.yaw)
	var back := teleporter(&"reach_return", RETURN_AT, &"sanctuary", &"waypoint", "Malasugue Town", 180.0)
	back.rune_tint = RIM
	spawn(&"arrival", ARRIVAL, 180.0)
	spawn(&"start", ARRIVAL, 180.0)
	signpost(Vector2(3.2, 21.0), [["The Sundered Reach\nFive gates · Class A heroes only", Vector2(0, -1)],
		["Malasugue Town", Vector2(0, 1)]])
	set_bounds(AABB(Vector3(-R - 6.0, -8, -R - 6.0), Vector3((R + 6.0) * 2.0, 22, (R + 6.0) * 2.0)))
	view("overview", Vector3(0, 0, -2), 0.0, 58.0, 76.0, 45.0)
	view("arrival", ARRIVAL, 180.0, 45.0, 22.0)
	view("gates", Vector3(0, 0, -12), 0.0, 48.0, 40.0)

func _plaza() -> void:
	floor_disc(Vector3.ZERO, R + 0.4, 0.0)
	for ii in 15:
		for jj in 15:
			var c := Vector2(-28.0 + ii * 4.0, -28.0 + jj * 4.0)
			if (c.abs() + Vector2(2, 2)).length() < R - 0.6:
				floor_tiles(Rect2(c.x - 2.0, c.y - 2.0, 4, 4))
	# the old fortress's compass in the middle: a ritual ring, a broken monolith and the light that holds the shard up
	kit("ritual_circle", Vector3(0, 0.03, 0), 0.0, 3.0, deco)
	kit("obelisk_corrupted", Vector3(0, 0, -1.0), 15.0, 1.5, props)
	for k in 4:
		var a := TAU * k / 4.0 + 0.4
		kit("pillar_broken", Vector3(cos(a) * 6.5, 0, sin(a) * 6.5), rad_to_deg(a), 1.1, props)
		brazier(Vector3(cos(a + 0.4) * 5.0, 0, sin(a + 0.4) * 5.0), 2.6)
	light(Vector3(0, 3.5, -1.0), RIM, 3.0, 18.0, false, true)
	# a little rubble where the shard tore away from the rest of the fortress
	scatter(["rubble_pile", "rock_small"], Rect2(-26, -26, 52, 52), 18, 6.0, Vector2(0.6, 1.0),
		func(x, z): return Vector2(x, z).length() < 8.0 or Vector2(x, z).length() > 15.0)

func _rim() -> void:
	# a low broken parapet round the edge, open where the arrival path comes in on the south
	var n := 36
	for k in n:
		var a := TAU * (k + 0.5) / n
		var p := Vector3(cos(a) * (R - 0.4), 0, sin(a) * (R - 0.4))
		var deg := rad_to_deg(a)
		if absf(wrapf(deg - 90.0, -180.0, 180.0)) < 9.0:
			continue
		arch("wall_low_broken" if k % 4 == 1 else "wall_low", p, -deg - 90.0)
		if k % 6 == 0:
			arch("pillar_quoin", p * 1.01)
			if k % 12 == 0:
				kit("banner_torn", p * 0.98 + Vector3(0, 3.6, 0), -deg + 90.0, 1.1, deco)
	# nobody walks off the edge into the dark
	var m := 48
	for k in m:
		var a0 := TAU * k / m
		var a1 := TAU * (k + 1) / m
		boundary(Vector3(cos(a0) * (R + 0.4), -2.0, sin(a0) * (R + 0.4)), Vector3(cos(a1) * (R + 0.4), -2.0, sin(a1) * (R + 0.4)), 12.0, 0.8)
	# the shard's broken underside: cliffs hanging into the void
	for k in 14:
		var a := TAU * k / 14.0 + rng.randf_range(-0.1, 0.1)
		kit("rock_large", Vector3(cos(a) * (R + 1.0), -7.0, sin(a) * (R + 1.0)), rng.randf() * 360.0, rng.randf_range(2.2, 3.2), deco)

func _void() -> void:
	mist(Rect2(-140, -140, 280, 280), -6.0, Color(0.32, 0.24, 0.5), 0.5)
	# other shards of the fortress, drifting far out
	for i in 16:
		var a := rng.randf() * TAU
		var d := rng.randf_range(R + 14.0, R + 60.0)
		var p := Vector3(cos(a) * d, rng.randf_range(-8.0, 10.0), sin(a) * d)
		kit("floating_rock", p, rng.randf() * 360.0, rng.randf_range(2.0, 5.0), deco)
	# Aether lights in the dark, like stars that came too close
	for i in 7:
		var a := TAU * i / 7.0 + 0.3
		light(Vector3(cos(a) * (R + 10.0), rng.randf_range(-3.0, 4.0), sin(a) * (R + 10.0)), RIM, 1.6, 14.0, false, true)
