extends Node
## Session and scene flow (autoload `Game`): owns the hero and the player node, builds and swaps maps, populates them
## with enemies, places the player on named spawn points, runs teleporter travel through the loading screen, and
## tracks session-wide UI/debug state.

signal map_changed(map: MapRoot)
signal session_started
signal session_ended

var hero: HeroData
var save_slot := 0
var difficulty := 1
var current_map: MapRoot
var current_map_id: StringName = &""
var player: Node3D                   # the node in group "player" that is moved between maps
var world_parent: Node               # where maps are parented (main scene sets this; defaults to the tree root)
var ui_root: Node                    # UIRoot (main scene); null in tests
var travelling := false
var in_session := false
var _loading: LoadingScreen
var _autosave_t := 0.0

# UI / interaction state
var ui_blocking := false              # a modal panel is open: gameplay input is ignored
var hover_target: Node                # enemy under the cursor
var hover_loot: Node                  # loot label under the cursor
# Developer toggles (only reachable through the dev panel)
var god_mode := false
var infinite_mana := false

const AUTOSAVE_INTERVAL := 120.0

func _ready() -> void:
	_loading = LoadingScreen.new()
	add_child(_loading)
	Events.world_flag_set.connect(_on_flag)

func _process(delta: float) -> void:
	if hero and in_session:
		hero.play_time += delta
		_autosave_t += delta
		if _autosave_t >= AUTOSAVE_INTERVAL and not travelling and player and (player as Player) and (player as Player).alive:
			_autosave_t = 0.0
			save_now()
		if infinite_mana and player is Player:
			var p := player as Player
			p.mana = p.max_mana()

# ---- Session --------------------------------------------------------------------------------------------------

func new_hero(class_id: StringName, hero_name: String) -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(class_id), hero_name)
	h.init_new()
	return h

func start_new_game(class_id: StringName, hero_name: String, slot: int, diff := 1) -> void:
	hero = new_hero(class_id, hero_name)
	hero.difficulty = diff
	save_slot = slot
	difficulty = diff
	await _begin_session(&"sanctuary", &"start")
	save_now()

func continue_game(slot: int) -> bool:
	var h := SaveSystem.load_hero(slot)
	if h == null:
		return false
	hero = h
	save_slot = slot
	difficulty = h.difficulty
	await _begin_session(h.current_map, h.current_spawn)
	return true

func _begin_session(map_id: StringName, spawn_id: StringName) -> void:
	_end_player()
	var p := Player.new()
	p.name = "Player"
	player = p
	var def := DB.map_def(map_id)
	if def == null:
		map_id = &"sanctuary"
		def = DB.map_def(map_id)
	await _loading.show_for(def)
	await get_tree().process_frame
	load_map(map_id, spawn_id)
	p.bind(hero)
	in_session = true
	_autosave_t = 0.0
	session_started.emit()
	await get_tree().process_frame
	await _loading.hide_screen()

func end_session() -> void:
	if in_session:
		save_now()
	in_session = false
	_end_player()
	if current_map and is_instance_valid(current_map):
		current_map.queue_free()
	current_map = null
	current_map_id = &""
	FX.world = null
	ui_blocking = false
	session_ended.emit()

## Pause menu "Main Menu": save, tear the session down; the boot scene listens to session_ended.
func return_to_menu() -> void:
	get_tree().paused = false
	end_session()

func _end_player() -> void:
	if player and is_instance_valid(player):
		player.queue_free()
	player = null

func save_now() -> bool:
	if hero == null:
		return false
	var ok := SaveSystem.save_hero(hero, save_slot)
	if ok:
		Events.notify.emit("Game saved", &"save")
	return ok

# ---- Maps -----------------------------------------------------------------------------------------------------

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
	hover_target = null
	hover_loot = null
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
	if player is Player:
		Spawner.populate(map, difficulty)
		NpcDirectory.populate(map)
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
	if in_session:
		save_now()
	await _loading.hide_screen()
	travelling = false

func return_to_town() -> void:
	travel(&"sanctuary", &"waypoint")

## After death: respawn at the current map's entry (towns: the plaza). Costs a little gold, never items.
func respawn_player() -> void:
	var p := player as Player
	if p == null:
		return
	var lost := int(hero.inventory.gold * 0.05)
	hero.inventory.gold -= lost
	var map_id := current_map_id
	var spawn := &"start"
	if not DB.map_def(map_id).is_town:
		# dungeons send you back to their entrance
		for s in [&"arrival", &"entrance", &"start"]:
			if current_map.spawns.has(s):
				spawn = s
				break
	await _loading.show_for(DB.map_def(map_id))
	load_map(map_id, spawn)
	p.respawn()
	Events.player_respawned.emit()
	if lost > 0:
		Events.notify.emit("You lost %d gold." % lost, &"info")
	await _loading.hide_screen()

# ---- World state ------------------------------------------------------------------------------------------------

func set_world_flag(flag: StringName, value: Variant = true) -> void:
	if hero == null:
		return
	hero.world_flags[flag] = value
	Events.world_flag_set.emit(flag, value)

func has_flag(flag: StringName) -> bool:
	return hero != null and bool(hero.world_flags.get(flag, false))

func _on_flag(flag: StringName, _v: Variant) -> void:
	if current_map:
		current_map.apply_flag_visuals(flag, true)
		current_map.refresh_teleporters()
