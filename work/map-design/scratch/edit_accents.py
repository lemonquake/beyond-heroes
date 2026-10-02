import re


def edit(path, old, new, count=1):
    s = open(path, encoding='utf-8').read()
    assert s.count(old) >= 1, (path, old[:60])
    s = s.replace(old, new, count)
    open(path, 'w', encoding='utf-8').write(s)


def append_to_func(path, func_header, lines):
    """Append lines at the end of a function body (before the next top-level func or EOF)."""
    s = open(path, encoding='utf-8').read()
    i = s.index(func_header)
    j = s.find('\nfunc ', i + len(func_header))
    k = s.find('\n# ----', i + len(func_header))
    ends = [x for x in (j, k) if x != -1]
    end = min(ends) if ends else len(s)
    body = s[i:end].rstrip('\n')
    s = s[:i] + body + '\n' + lines + s[end:]
    open(path, 'w', encoding='utf-8').write(s)


M = 'game/src/world/maps/'
append_to_func(M + 'sanctuary.gd', 'func _map_design() -> void:', '''	# ambient accents: the forge, the fountain, the gate's braziers
	accent(Vector3(22.6, 1.0, 21.6), &"torch_crackle", -12.0)
	accent(PLAZA + Vector3(0, 0.8, 0), &"water_splash", -20.0)
	accent(Vector3(0, 1.0, FENCE_R - 2.2), &"torch_crackle", -16.0)
''')
append_to_func(M + 'westreach.gd', 'func _map_design() -> void:', '''	# ambient accents: the mill race, the cove's surf, the coast road's fires
	accent(Vector3(15.6, -3.0, MILL_HOUSE.y), &"water_splash", -12.0)
	for p in [Vector3(-176.0, -12.5, 106.0), Vector3(-160.0, -12.5, 108.0)]:
		accent(p, &"water_wave", -16.0)
	accent(Vector3(-170.0, -12.0, 97.5), &"fire_campfire", -14.0)
''')
append_to_func(M + 'olivar.gd', 'func _map_design() -> void:', '''	# ambient accents: water at the pier and the quiet bay
	for p in [Vector3(PIER_X, LAKE_Y + 0.5, -46.0), Vector3(-20.0, LAKE_Y + 0.5, -44.0)]:
		accent(p, &"water_wave", -18.0)
''')
append_to_func(M + 'wyman_outpost.gd', 'func _map_design() -> void:', '''	# ambient accents: the bonfire, the marsh at the jetty, the field forge
	accent(Vector3(BONFIRE.x, 1.0, BONFIRE.y), &"fire_campfire", -12.0)
	accent(Vector3(DataZarael.WY_JETTY_ROOT.x + 6.0, MARSH_Y + 0.5, DataZarael.WY_JETTY_ROOT.y), &"water_wave", -18.0)
	accent(Vector3(FORGE.x, 1.0, FORGE.y), &"torch_crackle", -14.0)
''')
append_to_func(M + 'agdao.gd', 'func _map_design() -> void:', '''	# ambient accents: the quay, the Wire Market's fountain, the harbour brazier
	for x in [-34.0, 0.0, 26.0]:
		accent(Vector3(x, tier_y(0), 49.0), &"water_wave", -18.0)
	accent(Vector3(FOUNTAIN.x, tier_y(1) + 0.8, FOUNTAIN.y), &"water_splash", -20.0)
	accent(Vector3(30.0, tier_y(0) + 1.2, 40.0), &"torch_crackle", -16.0)
''')
append_to_func(M + 'bridge_of_death.gd', 'func _map_design() -> void:', '''	# ambient accents: wind across the span (rare and quiet: the fights carry their own sound)
	for z in [100.0, 30.0, -50.0]:
		accent(Vector3(0, 2.0, z), &"wind_gust", -18.0)
''')
append_to_func(M + 'weeping_causeway.gd', 'func _map_design() -> void:', '''	# ambient accents: black water against the causeway's sides
	for x in [-58.0, -40.0, -24.0]:
		accent(Vector3(x, WATER_Y + 0.3, HALF + 2.0), &"water_splash", -18.0)
''')
append_to_func(M + 'catacombs.gd', 'func _map_design() -> void:', '''	# ambient accents: the cistern's water
	accent(Vector3(32.0, WATER_Y + 0.3, -6.0), &"water_wave", -18.0)
''')
# dungeons: a crackle at every motif fire, water where basins are
edit(M + 'dungeon.gd', '''			if nm == "@fire":
				flame(pos, float(pc[3]))
				light(pos + Vector3(0, 0.5, 0), FIRE, 2.0, 7.0, false, true)''', '''			if nm == "@fire":
				flame(pos, float(pc[3]))
				light(pos + Vector3(0, 0.5, 0), FIRE, 2.0, 7.0, false, true)
				accent(pos, &"torch_crackle", -14.0)''')
edit(M + 'dungeon.gd', '''			if is_basin(c):
				n += 1
				if n % 3 == 0:''', '''			if is_basin(c):
				n += 1
				if n % 4 == 1:
					accent(Vector3(p.x, LIQUID_Y + 0.3, p.z), &"water_wave", -20.0)
				if n % 3 == 0:''')
print("ok")
