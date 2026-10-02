class_name AmbientAccents
extends Node3D
## Map-design pass (2026-10-03): occasional quiet sounds at authored spots — fire at a forge or a fire basket, water at
## a quay or a basin, wind on the bridge. One node per map (MapBuilder.accent registers the spots), one timer, no
## player per object: every few seconds it may play one spot near the hero through Audio.play_at_if_free, which never
## takes a voice from combat. Low quality plays them half as often. The map's ambience bed and reverb are unchanged.

const RANGE := 20.0          # only spots this close to the hero are candidates
const GAP := Vector2(3.5, 8.0)
var spots: Array = []        # [Vector3 (map-local), StringName sound, float volume_db]
var _t := 4.0
var _rng := RandomNumberGenerator.new()
var plays := 0               # tests and probes

func _ready() -> void:
	_rng.seed = hash(get_parent().name)

func add(pos: Vector3, sound: StringName, volume_db := -14.0) -> void:
	spots.append([pos, sound, volume_db])

func _process(delta: float) -> void:
	_t -= delta
	if _t > 0.0:
		return
	_t = _rng.randf_range(GAP.x, GAP.y) * (2.0 if Perf.lite else 1.0)
	var hero := Game.player as Node3D
	if hero == null or not is_instance_valid(hero) or spots.is_empty():
		return
	var near: Array = []
	for s in spots:
		var wp: Vector3 = to_global(s[0])
		if wp.distance_to(hero.global_position) < RANGE:
			near.append([wp, s[1], s[2]])
	if near.is_empty():
		return
	var pick: Array = near[_rng.randi() % near.size()]
	if Audio.play_at_if_free(pick[1], pick[0], pick[2]):
		plays += 1
