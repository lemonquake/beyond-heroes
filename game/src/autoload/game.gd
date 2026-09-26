extends Node
## Session and scene flow (autoload `Game`): owns the hero, builds and swaps maps, places the player on named
## spawn points and runs teleporter travel through the loading screen.

signal map_changed(map: MapRoot)

var hero: HeroData
var save_slot := 0
var current_map: MapRoot
var current_map_id: StringName = &""
var player: Node3D                   # the node in group "player" that is moved between maps
var world_parent: Node               # where maps are parented (main scene sets this; defaults to the tree root)
var travelling := false
var _loading: LoadingScreen

func _ready() -> void:
	_loading = LoadingScreen.new()
	add_child(_loading)

## Build a map scene from its definition without adding it to the tree (used by loading and by tests).
func build_map(id: StringName) -> MapRoot:
	var def := DB.map_def(id)
	if def == null:
		push_error("Unknown map %s" % id)
		return null
	var script: GDScript = load(def.builder)
	var builder: MapBuilder = script.new()
	return builder.build(def)

## Replace the current map immediately and put the player on `spawn_id`.
func load_map(id: StringName, spawn_id: StringName = &"start") -> MapRoot:
	var map := build_map(id)
	if map == null:
		return null
	if current_map and is_instance_valid(current_map):
		if player and player.get_parent() == current_map:
			current_map.remove_child(player)
		current_map.queue_free()
	var parent := world_parent if world_parent and is_instance_valid(world_parent) else get_tree().root
	parent.add_child(map)
	MapBuilder.bake_navigation(map)
	current_map = map
	current_map_id = id
	FX.world = map
	map.apply_flag_visuals()
	if player and is_instance_valid(player):
		if player.get_parent() == null:
			map.add_child(player)
		place_player(spawn_id)
	var def := map.def
	if hero:
		hero.current_map = id
		hero.current_spawn = spawn_id
		hero.discovered_maps[id] = true
		# arriving beside a waypoint (travelling in through it) registers it, as stepping onto it would
		var sp := map.spawn_transform(spawn_id).origin
		for t in map.teleporters():
			if t.global_position.distance_to(sp) < 6.0:
				t.discover()
	Audio.play_music(def.music)
	Audio.play_ambience(def.ambience)
	Audio.set_environment_reverb(def.reverb)
	Events.map_loaded.emit(id)
	map_changed.emit(map)
	return map

func place_player(spawn_id: StringName) -> void:
	if player == null or current_map == null:
		return
	var t := current_map.spawn_transform(spawn_id)
	player.global_transform = Transform3D(t.basis.orthonormalized(), t.origin + Vector3.UP * 0.05)
	if player is CharacterBody3D:
		(player as CharacterBody3D).velocity = Vector3.ZERO
	if player.has_method(&"on_teleported"):
		player.call(&"on_teleported")

## Teleporter travel with the loading screen. Same-map travel just relocates the player.
func travel(id: StringName, spawn_id: StringName) -> void:
	if travelling:
		return
	travelling = true
	if id == current_map_id and current_map:
		place_player(spawn_id)
		travelling = false
		return
	var def := DB.map_def(id)
	await _loading.show_for(def)
	await get_tree().process_frame
	load_map(id, spawn_id)
	await get_tree().process_frame
	await _loading.hide_screen()
	travelling = false
