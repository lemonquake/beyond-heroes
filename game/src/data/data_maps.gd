class_name DataMaps

static func _m(id: StringName, name: String, sub: String, d: Dictionary) -> MapDef:
	var m := MapDef.new()
	m.id = id
	m.display_name = name
	m.subtitle = sub
	m.builder = "res://src/world/maps/%s.gd" % id
	for k in d:
		m.set(k, d[k])
	return m

static func build() -> Array:
	return [
		# id stays "sanctuary" for save compatibility; the waypoint terrace keeps the old name "Sanctuary Terrace"
		_m(&"sanctuary", "Malasugue Town", "The last lit hearth on Salmonan", {"is_town": true, "level_min": 1, "level_max": 1, "music": &"main_theme",
			"ambience": &"amb_town", "footstep_surface": &"stone", "reverb": 0.1, "world_map_pos": Vector2(0.18, 0.62),
			"loading_hint": "Malasugue remembers every face. The waypoint on the Sanctuary Terrace connects every shrine you have awakened; the guild halls register heroes, the Guild House posts paid odd jobs, and the Salted Marlin lets rooms by the night."}),
		# provisional district (LORE §6b): the roads below the South Gate — Old Mill Crossroads, Lantern Fields, Tideglass Cove
		_m(&"westreach", "Westreach", "The roads below the South Gate", {"level_min": 1, "level_max": 4, "music": &"main_theme",
			"ambience": &"amb_forest", "footstep_surface": &"dirt", "reverb": 0.04, "world_map_pos": Vector2(0.4, 0.64),
			"loading_hint": "Roads rejoin. Leave by the mill, come home along the coast: the signposts and the map (M) name every road."}),
		# bh-007 (provisional, LORE §6b): the lake-trade town east of the mill and the hero camp above Reedwater Marsh
		_m(&"olivar", "Olivar", "A trading town on Stillwater Lake", {"is_town": true, "level_min": 1, "level_max": 1, "music": &"main_theme",
			"ambience": &"amb_town", "footstep_surface": &"stone", "reverb": 0.08, "world_map_pos": Vector2(0.6, 0.6),
			"loading_hint": "Olivar's merchants sell advanced gear at a premium. Their stock changes every time you clear a stage or defeat a miniboss."}),
		_m(&"wyman_outpost", "Wyman Outpost", "The hero camp above Reedwater Marsh", {"is_town": true, "level_min": 1, "level_max": 1,
			"music": &"main_theme", "ambience": &"amb_forest", "footstep_surface": &"dirt", "reverb": 0.04, "world_map_pos": Vector2(0.62, 0.8),
			"loading_hint": "Rest at the bonfire to set your checkpoint: if you fall, you can wake beside it. The Hero Register lists every hero in camp."}),
		_m(&"ruined_forest", "Ruined Forest", "Where the village fell", {"level_min": 1, "level_max": 5, "music": &"dungeon_theme",
			"ambience": &"amb_forest", "footstep_surface": &"dirt", "reverb": 0.05, "world_map_pos": Vector2(0.38, 0.45),
			"loading_hint": "Throw enemies into walls, trees and each other: impacts deal damage based on how hard they hit."}),
		_m(&"catacombs", "Ancient Catacombs", "Beneath the drowned chapel", {"level_min": 4, "level_max": 8, "music": &"dungeon_theme",
			"ambience": &"amb_catacombs", "footstep_surface": &"stone", "reverb": 0.55, "world_map_pos": Vector2(0.55, 0.62),
			"loading_hint": "Wet enemies conduct Lightning and freeze twice as fast."}),
		_m(&"forgotten_temple", "Forgotten Temple", "Halls of the first oath", {"level_min": 7, "level_max": 10, "music": &"dungeon_theme",
			"ambience": &"amb_temple", "footstep_surface": &"stone", "reverb": 0.7, "world_map_pos": Vector2(0.72, 0.4),
			"loading_hint": "Elite enemies carry modifiers shown under their name. Warded elites crack faster under Light."}),
		_m(&"boss_arena", "The Hollow Throne", "Morthar awaits", {"level_min": 10, "level_max": 10, "music": &"boss_theme",
			"ambience": &"amb_arena", "footstep_surface": &"stone", "reverb": 0.6, "world_map_pos": Vector2(0.86, 0.26), "waypoint": false,
			"loading_hint": "Bait the Warden's charge into a pillar to stun him. His back rune is a weak point."}),
		# bh-021: the boss causeway in Reedwater Marsh, through Wyman Outpost's Marsh Gate (docs/LORE.md §10)
		_m(&"weeping_causeway", "The Weeping Causeway", "Where the Dawnbreakers were betrayed", {"level_min": 5, "level_max": 7,
			"music": &"boss_theme", "ambience": &"amb_arena", "footstep_surface": &"stone", "reverb": 0.2,
			"world_map_pos": Vector2(0.78, 0.8), "waypoint": false,
			"loading_hint": "Kethrax's chain drags you to him: dodge when he draws it back. Light burns the Legion; fire does not touch his stolen wrath."}),
	] + interiors() + DataDungeons.map_defs()

## The buildings of Malasugue you can walk into (doors in sanctuary.gd, rooms in interior.gd).
static func interiors() -> Array:
	var out := []
	for d in [
		[&"int_tavern", "The Salted Marlin", "Tavern and inn", &"dirt", "Rest here for a fee: you wake fully restored and Well Rested."],
		[&"int_guildhouse", "The Guild House", "Swordfin and Lantern job boards", &"stone", "Both guilds keep a counter here. Register with one, then take its jobs from the board: miniquests that pay gold."],
		[&"int_swordfin", "Swordfin Hall", "The Swordfin Company", &"stone", "Strike first. Strike true. Register with Quartermaster Dax to join the Company."],
		[&"int_lantern", "Lantern House", "The Lantern Covenant", &"stone", "We keep the light between things. Scribe Lio keeps the Covenant's register."],
		[&"int_netmender", "The Net-mender's House", "Home of Tessaly Grane", &"dirt", "Fishers of Malasugue read the tides the way heroes read the Aether."],
		[&"int_cartographer", "The Cartographer's House", "Home of Aurand Quell", &"dirt", "Four islands, three outside nations, and one map that is never finished."],
		[&"int_widow", "The Hald House", "Home of Ilvena Hald", &"dirt", "The first raid took the forest garrison. Malasugue has not forgotten them."],
		[&"int_keeper", "The Keeper's House", "Home of Keeper Thadric Moll", &"dirt", "Gigas, Tyrants and Oros: the keeper writes down what nobody alive has seen."],
		[&"int_refugee", "The Refugee's House", "Home of Zerin Ven", &"dirt", "News from Emberhal travels with those who flee it."],
	]:
		out.append(_interior(d[0], d[1], d[2], d[3], d[4]))
	return out

static func _interior(id: StringName, name: String, sub: String, floor_sound: StringName, hint: String) -> MapDef:
	var m := _m(id, name, sub, {"is_town": true, "interior": true, "parent_map": &"sanctuary", "waypoint": false,
		"level_min": 1, "level_max": 1, "music": &"main_theme", "ambience": &"amb_town", "footstep_surface": floor_sound,
		"reverb": 0.3, "world_map_pos": Vector2(0.18, 0.62), "loading_hint": hint})
	m.builder = "res://src/world/maps/interior.gd"
	return m
