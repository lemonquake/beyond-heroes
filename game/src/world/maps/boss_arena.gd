extends MapBuilder
## MAP 5 — The Hollow Throne, "Morthar awaits" (boss arena, level 10).
##
## The player arrives on a ledge, crosses a bridge over a glowing abyss of corruption and enters a walled circular
## arena. Eight pillars stand in a ring: the Warden's charge can be baited into them to stun him (loading hint).
## The throne sits on a raised dais at the north under a tall wall of banners; a binding circle is inlaid in the
## floor. The return waypoint on the ledge stays sealed until the Warden falls (world flag boss_warden_defeated).
## Gameplay markers: group "arena_pillar" (8), group "boss_spawn" (1), enemy zones for the boss and his summons.

const R := 20.0
const PILLAR_R := 12.0
const DAIS := Rect2(-6, -20, 12, 8)
const DAIS_Y := 2.0
const LEDGE := Rect2(-8, 30, 16, 10)

func compose() -> void:
	environment({
		"sky": true, "sky_top": Color(0.03, 0.01, 0.05), "sky_horizon": Color(0.2, 0.06, 0.16),
		"ambient": Color(0.34, 0.24, 0.44), "ambient_energy": 0.8,
		"fog": Color(0.16, 0.06, 0.16), "fog_density": 0.008, "fog_height": -6.0, "fog_height_density": 0.1,
		"sun": Color(0.8, 0.5, 0.75), "sun_energy": 0.45, "sun_rot": Vector3(-60, -20, 0), "glow": 1.0,
		"exposure": 1.05, "contrast": 1.12, "saturation": 0.95,
	})
	_arena()
	_dais()
	_approach()
	_abyss()
	set_bounds(AABB(Vector3(-22, -2, -22), Vector3(44, 12, 64)))
	view("overview", Vector3(0, 0, 6), 0.0, 72.0, 85.0, 45.0)
	view("arrival", Vector3(0, 0, 30), 0.0, 45.0, 26.0)
	view("arena", Vector3(0, 0, 0), 0.0, 52.0, 36.0)
	view("throne", Vector3(0, DAIS_Y, -15), 0.0, 40.0, 20.0)

func _arena() -> void:
	# floor: flagstone tiles wherever a whole tile fits inside the wall, a stone disc underneath fills the rim
	floor_disc(Vector3.ZERO, R + 0.2, -0.02)
	for i in 10:
		for j in 10:
			var c := Vector2(-18.0 + i * 4.0, -18.0 + j * 4.0)
			var far := (c.abs() + Vector2(2, 2)).length()
			if far < R - 0.3:
				floor_tiles(Rect2(c.x - 2.0, c.y - 2.0, 4, 4))
	kit("ritual_circle", Vector3(0, 0.02, 0), 0.0, 2.0, deco)
	light(Vector3(0, 1.0, 0), Color(0.35, 0.8, 1.0), 2.0, 12.0)
	# ring wall: cutaway on the camera (south) side, a gate gap for the bridge, full height elsewhere
	var n := 32
	for i in n:
		var a := TAU * (i + 0.5) / n
		var p := Vector3(cos(a) * R, 0, sin(a) * R)
		var deg := rad_to_deg(a)
		var yaw := -deg - 90.0
		if absf(deg - 90.0) < 6.0:
			continue
		var south := sin(a) > 0.35
		arch("wall_low" if south else ("wall_broken" if i % 9 == 4 else "wall_stone_capped"), p, yaw)
		if sin(a) < -0.55:
			arch("wall_stone_capped", p + Vector3(0, 4.0, 0), yaw)  # the tall north wall behind the throne
		if i % 4 == 0:
			var pp := Vector3(cos(TAU * i / n) * R, 0, sin(TAU * i / n) * R)
			arch("pillar_quoin" if not south else "pillar", pp).scale = Vector3(1, 1.0 if not south else 0.36, 1)
	for sx in [-2.3, 2.3]:
		arch("pillar_quoin", Vector3(sx, 0, R - 0.2))
	# the eight impact pillars
	for i in 8:
		var a := TAU * (i + 0.5) / 8.0
		var p := Vector3(cos(a) * PILLAR_R, 0, sin(a) * PILLAR_R)
		var pil := arch("pillar_quoin", p, rad_to_deg(a))
		pil.add_to_group(&"arena_pillar")
		if i % 2 == 0:
			kit("chains_hanging", p + Vector3(0, 0.8, 0), rad_to_deg(a), 1.0, deco)
	# braziers between the pillars and the wall
	for i in 6:
		var a := TAU * i / 6.0 + PI / 6.0
		if sin(a) > 0.9:
			continue
		brazier(Vector3(cos(a) * 16.5, 0, sin(a) * 16.5), 3.6, i % 2 == 0)
	for i in 5:
		var a := PI + PI * (i + 0.5) / 5.0
		torch(Vector3(cos(a) * (R - 0.45), 2.7, sin(a) * (R - 0.45)), rad_to_deg(atan2(-cos(a), -sin(a))))
	scatter(["bones_scatter"], Rect2(-14, -12, 28, 26), 6, 5.0, Vector2(0.7, 1.0), func(x, z): return Vector2(x, z).length() < 7.0)
	decor("skull_pile", Vector3(-9.0, 0, -8.0), 20.0)
	decor("skull_pile", Vector3(10.5, 0, -5.0), 200.0, 0.8)
	enemy_zone("boss", Vector3(0, DAIS_Y, -14.5), 3.0, [&"boss_warden"], 1, 0.0)
	enemy_zone("summons_w", Vector3(-9, 0, 2), 4.0, [&"hollow_soldier", &"bonewarden"], 4, 0.0)
	enemy_zone("summons_e", Vector3(9, 0, 2), 4.0, [&"hollow_soldier", &"grave_archer"], 4, 0.0)

func _dais() -> void:
	var r := DAIS
	var y := DAIS_Y
	floor_tiles(r, y)
	wall_run(Vector3(r.position.x, y - 4.0, r.end.y), Vector3(r.end.x, y - 4.0, r.end.y), "wall_stone_capped", [1], {}, true)
	wall_run(Vector3(r.position.x, y - 4.0, r.position.y), Vector3(r.position.x, y - 4.0, r.end.y))
	wall_run(Vector3(r.end.x, y - 4.0, r.position.y), Vector3(r.end.x, y - 4.0, r.end.y), "wall_stone_capped", [], {}, true)
	arch("stairs", Vector3(0, 0, r.end.y + 2.0))
	var th := kit("throne", Vector3(0, y, -17.6), 0.0)
	light(socket_pos(th, "light") + Vector3(0, 0, 1.2), Color(0.65, 0.2, 1.0), 3.6, 12.0, true, true)
	var m := Marker3D.new()
	m.name = "BossSpawn"
	m.position = Vector3(0, y, -14.2)
	m.add_to_group(&"boss_spawn")
	markers.add_child(m)
	for sx in [-4.6, 4.6]:
		brazier(Vector3(sx, y, -13.2), 3.2)
		kit("statue_knight", Vector3(sx * 1.05, y, -18.6), 0.0)
	for x in [-10.0, -4.0, 4.0, 10.0]:
		var p := Vector3(x, 6.6, -sqrt(R * R - x * x) + 0.6)
		kit("banner_torn", p, rad_to_deg(atan2(-p.x, -p.z)), 1.2, deco)

func _approach() -> void:
	var l := LEDGE
	floor_tiles(l)
	arch("bridge_stone", Vector3(0, 0, (R + l.position.y) * 0.5), 90.0)
	wall_run(Vector3(l.position.x, 0, l.end.y), Vector3(l.end.x, 0, l.end.y), "wall_low", [], {1: "wall_low_broken"}, true)
	wall_run(Vector3(l.position.x, 0, l.position.y), Vector3(l.position.x, 0, l.end.y), "wall_low")
	wall_run(Vector3(l.end.x, 0, l.position.y), Vector3(l.end.x, 0, l.end.y), "wall_low", [], {}, true)
	wall_run(Vector3(l.position.x, 0, l.position.y), Vector3(l.end.x, 0, l.position.y), "wall_low", [1, 2])
	teleporter(&"arena_return", Vector3(0, 0, 36.0), &"sanctuary", &"waypoint", "Hero Sanctuary", 0.0, true,
		&"boss_warden_defeated", "The Warden's will binds this waypoint.")
	spawn(&"arrival", Vector3(0, 0, 31.6), 180.0)
	spawn(&"start", Vector3(0, 0, 31.6), 180.0)
	brazier(Vector3(-6.0, 0, 32.0), 3.0)
	brazier(Vector3(6.0, 0, 32.0), 3.0, true)
	decor("weapons_discarded", Vector3(-5.0, 0, 37.5), 40.0)
	decor("bones_scatter", Vector3(4.8, 0, 37.8), 10.0)
	kit("statue_collapsed", Vector3(5.5, 0, 34.5), 240.0, 0.7)
	# hard edges over the drop
	boundary(Vector3(-2.0, 0, 30.0), Vector3(-2.0, 0, R - 0.5), 4.0, 0.3)
	boundary(Vector3(2.0, 0, 30.0), Vector3(2.0, 0, R - 0.5), 4.0, 0.3)

func _abyss() -> void:
	# a glowing sea of corruption far below, cliffs dropping into it, drifting violet haze
	water(Rect2(-120, -120, 240, 240), -26.0, Color(0.5, 0.12, 0.7), Color(0.08, 0.02, 0.12), 1.2, 30.0, 0.0)
	mist(Rect2(-120, -120, 240, 240), -14.0, Color(0.3, 0.12, 0.34), 0.5)
	cliff_ring(Vector3.ZERO, R + 4.5, -2.5, 18, Vector2(2.0, 2.6))
	cliff_ring(Vector3(0, 0, 35), 11.0, -2.0, 8, Vector2(1.6, 2.0))
	for i in 4:
		var a := TAU * i / 4.0 + PI / 4.0
		var p := Vector3(cos(a) * (R + 5.0), -2.0, sin(a) * (R + 5.0))
		kit("obelisk_corrupted", p, rng.randf() * 360.0, 1.4, deco)
		light(p + Vector3(0, 5.0, 0), Color(0.65, 0.2, 1.0), 3.0, 14.0, false, true)
	for i in 3:
		var a := TAU * i / 3.0 + 0.8
		var p := Vector3(cos(a) * 110.0, -60.0, sin(a) * 110.0)
		decor("cliff_b", p, rng.randf() * 360.0, 10.0, false)
