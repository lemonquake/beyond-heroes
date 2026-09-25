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
		_m(&"sanctuary", "Hero Sanctuary", "The last lit hearth", {"is_town": true, "level_min": 1, "level_max": 1, "music": &"music_town",
			"ambience": &"amb_town", "footstep_surface": &"stone", "reverb": 0.1, "world_map_pos": Vector2(0.18, 0.62),
			"loading_hint": "Speak to no one; the Sanctuary remembers. Its waypoint connects every shrine you have awakened."}),
		_m(&"ruined_forest", "Ruined Forest", "Where the village fell", {"level_min": 1, "level_max": 5, "music": &"music_dungeon",
			"ambience": &"amb_forest", "footstep_surface": &"dirt", "reverb": 0.05, "world_map_pos": Vector2(0.38, 0.45),
			"loading_hint": "Throw enemies into walls, trees and each other: impacts deal damage based on how hard they hit."}),
		_m(&"catacombs", "Ancient Catacombs", "Beneath the drowned chapel", {"level_min": 4, "level_max": 8, "music": &"music_dungeon",
			"ambience": &"amb_catacombs", "footstep_surface": &"stone", "reverb": 0.55, "world_map_pos": Vector2(0.55, 0.62),
			"loading_hint": "Wet enemies conduct Lightning and freeze twice as fast."}),
		_m(&"forgotten_temple", "Forgotten Temple", "Halls of the first oath", {"level_min": 7, "level_max": 10, "music": &"music_dungeon",
			"ambience": &"amb_temple", "footstep_surface": &"stone", "reverb": 0.7, "world_map_pos": Vector2(0.72, 0.4),
			"loading_hint": "Elite enemies carry modifiers shown under their name. Warded elites crack faster under Light."}),
		_m(&"boss_arena", "The Hollow Throne", "Morthar awaits", {"level_min": 10, "level_max": 10, "music": &"music_boss",
			"ambience": &"amb_arena", "footstep_surface": &"stone", "reverb": 0.6, "world_map_pos": Vector2(0.86, 0.26), "waypoint": false,
			"loading_hint": "Bait the Warden's charge into a pillar to stun him. His back rune is a weak point."}),
	]
