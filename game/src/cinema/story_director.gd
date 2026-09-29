class_name StoryDirector
## bh-021: starts the main story's cutscenes from game events (Game._ready connects it once).
##   kethrax_intro_seen (the Drowned Tollhouse trigger)  -> kethrax_intro; Kethrax waits, unseen, until it ends
##   Kethrax dies                                          -> chain_breaks (after his death animation)
## The prologue and the Tempo guide are chained in Game.start_new_game; conversations start the rest (the
## "cutscene" dialogue action).

static func connect_events() -> void:
	Events.world_flag_set.connect(_on_flag)
	Events.boss_defeated.connect(_on_boss)

static func _on_flag(flag: StringName, v: Variant) -> void:
	if flag == &"kethrax_intro_seen" and bool(v) and not Game.has_flag(&"boss_kethrax_defeated"):
		CutscenePlayer.play(&"kethrax_intro")

static func _on_boss(boss: Node) -> void:
	if boss == null or not is_instance_valid(boss) or not ("def" in boss) or boss.def == null:
		return
	if boss.def.id != &"kethrax":
		return
	var pos: Vector3 = (boss as Node3D).global_position
	var yaw: float = (boss as Node3D).rotation.y
	var map := Game.current_map
	var hero := Game.hero
	var tree := Game.get_tree()
	tree.create_timer(2.6).timeout.connect(func() -> void:
		if Game.in_session and Game.hero == hero and is_instance_valid(map) and Game.current_map == map:
			var c := DataCutscenes.make(&"chain_breaks")
			if c:
				c.set_meta(&"at", Transform3D(Basis(Vector3.UP, yaw), pos))
				CutscenePlayer.play_cutscene(c))

## The boss of this map (Kethrax) — the intro hides the real one while its actor takes the stage.
static func map_boss(id: StringName) -> Node3D:
	for b in Game.get_tree().get_nodes_in_group(&"boss"):
		if "def" in b and b.def and b.def.id == id and Game.current_map and Game.current_map.is_ancestor_of(b):
			return b as Node3D
	return null
