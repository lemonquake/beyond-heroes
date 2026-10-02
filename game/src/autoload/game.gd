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
var _was_rested := false
var _ending := false

# UI / interaction state
var ui_blocking := false              # a modal panel is open: gameplay input is ignored
var hover_target: Node                # enemy under the cursor
var hover_loot: Node                  # loot label under the cursor
var hover_ally: Node                  # another player's hero under the cursor (click = Trade Request, bh-016)
# Developer toggles (only reachable through the dev panel)
var god_mode := false
var in_cutscene := false             # bh-021: a CutscenePlayer owns the screen
var infinite_mana := false

const AUTOSAVE_INTERVAL := 120.0

func _ready() -> void:
	_loading = LoadingScreen.new()
	add_child(_loading)
	Events.world_flag_set.connect(_on_flag)
	Events.player_leveled.connect(func(_l: int, _g: int) -> void: _check_tempo_grade())
	Events.player_leveled.connect(func(level: int, gained: int) -> void:
		var notice := DungeonGrowth.level_notice(level, gained)
		if notice != "":
			Events.notify.emit(notice, &"discovery"))
	GuildJobs.connect_events()
	QuakeTeam.connect_events()
	OwnGuild.connect_events()
	StoryDirector.connect_events()

func _process(delta: float) -> void:
	if hero and in_session:
		hero.play_time += delta
		OwnGuild.tick(hero, delta)
		_autosave_t += delta
		if _autosave_t >= AUTOSAVE_INTERVAL and not travelling and player and (player as Player) and (player as Player).alive:
			_autosave_t = 0.0
			save_now()
		# the inn's Well Rested bonus ends: refresh derived stats once
		var r := hero.is_rested()
		if r != _was_rested:
			_was_rested = r
			hero.stats_dirty.emit()
		if infinite_mana and player is Player:
			var p := player as Player
			p.mana = p.max_mana()

# ---- Session --------------------------------------------------------------------------------------------------

func new_hero(class_id: StringName, hero_name: String) -> HeroData:
	var h := HeroData.new()
	h.setup(DB.class_def(class_id), hero_name)
	h.init_new()
	return h

## A new hero: the prologue cutscene (bh-021) shows the waypoint waking and the hero arriving on the Sanctuary
## Terrace; Tobren, the starter Tempo, comes through with them, and once the prologue ends he walks them through Tempos
## and the controls (DataGuide; skipped if that conversation already ended for this hero).
func start_new_game(class_id: StringName, hero_name: String, slot: int, diff := 1, look := {}) -> void:
	hero = new_hero(class_id, hero_name)
	hero.look = HeroLook.to_save(HeroLook.sanitize(look))
	TempoRules.grant_starter(hero)
	hero.difficulty = diff
	save_slot = slot
	difficulty = diff
	await _begin_session(&"sanctuary", &"waypoint")
	save_now()
	play_prologue()

## The prologue, then the Tempo guide (headless runs skip straight to the guide).
func play_prologue() -> void:
	if DisplayServer.get_name() == "headless" or has_flag(&"prologue_seen"):
		open_intro()
		return
	CutscenePlayer.play(&"prologue", open_intro)

## Open the new-game guide unless this hero has already heard it.
func open_intro() -> void:
	if hero == null or has_flag(DataGuide.DONE_FLAG):
		return
	if ui_root and is_instance_valid(ui_root) and ui_root.has_method(&"start_intro"):
		ui_root.start_intro()

func continue_game(slot: int) -> bool:
	var h := SaveSystem.load_hero(slot)
	if h == null:
		return false
	hero = h
	save_slot = slot
	difficulty = h.difficulty
	await _begin_session(h.current_map, h.current_spawn)
	_rebalance_notice(h)
	return true

## bh-027: an old save was brought up to the survival rebalance on load: say so once, with the new pools.
func _rebalance_notice(h: HeroData) -> void:
	if h == null or h.progress.auto_allocated <= 0:
		return
	var s := h.compute_stats()
	Events.notify.emit("Your hero was updated to the new balance: %d attribute points from the new level rewards were spent along your build. Maximum HP %d, Maximum Mana %d.%s" % [
		h.progress.auto_allocated, roundi(s.get_stat(&"max_hp")), roundi(s.get_stat(&"max_mana")),
		" You also have %d skill points to spend." % h.progress.skill_points if h.progress.skill_points > 0 else ""], &"discovery")
	h.progress.auto_allocated = 0
	save_now()

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

func end_session(discard_official := false) -> void:
	if _ending:
		return
	_ending = true
	var was_official := Official.active
	if was_official:
		get_tree().paused = true
		if not discard_official and not await Official.flush():
			_ending = false
			if ui_root:
				var extra := UIWindow.button("Return Using Last Server Save", func() -> void:
					ui_root.confirm.cancel()
					end_session(true), &"", 400.0)
				ui_root.confirm.ask("Progress Not Yet Saved", "The server has not confirmed your latest progress. Retry after restoring the connection, or return using your last confirmed save and discard the unconfirmed changes.", func() -> void: end_session(), "Retry Save", false, extra)
			return
		await Official.release_character()
	if in_session and not was_official:
		save_now()
	in_session = false
	_end_player()
	if current_map and is_instance_valid(current_map):
		current_map.queue_free()
	current_map = null
	current_map_id = &""
	FX.world = null
	ui_blocking = false
	_ending = false
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
	TempoParty.sync_all()
	if Official.active:
		Official.queue_save(hero)
		return false # Server acknowledgement arrives asynchronously; never report a queued save as durable.
	var ok := SaveSystem.save_hero(hero, save_slot)
	if ok:
		Events.notify.emit("Game saved", &"save")
	return ok

# ---- Maps -----------------------------------------------------------------------------------------------------

## Build a map scene from its definition without adding it to the tree (used by loading and by tests).
func build_map(id: StringName, saved_visit := false) -> MapRoot:
	var def := DB.map_def(id)
	if def == null:
		push_error("Unknown map %s" % id)
		return null
	# bh-029: Zarael's Heartwire burns bright once this hero has woken the Dawn Engine
	MaterialLibrary.wire_restored = DataZarael.has(hero, DataZarael.F_RESTORED)
	var parsed := DataDungeons.parse(id)
	if parsed[0] != &"":
		def = def.duplicate()
		var growth := DungeonGrowth.for_hero(hero, parsed[0])
		if saved_visit and hero:
			growth = DungeonGrowth.profile(int(hero.world_flags.get(DungeonGrowth.visit_key(parsed[0]), hero.progress.level)))
		def.set_meta(&"dungeon_growth", growth)
		var lv := DungeonGrowth.levels(parsed[0], parsed[1], growth)
		def.level_min = lv.x
		def.level_max = lv.y
		def.subtitle += " · " + DungeonGrowth.describe(growth)
	var script: GDScript = load(def.builder)
	var builder: MapBuilder = script.new()
	return builder.build(def)

## Replace the current map immediately and put the player on `spawn_id`.
func load_map(id: StringName, spawn_id: StringName = &"start") -> MapRoot:
	DungeonGrowth.enter(hero, id)
	var map := build_map(id, true)
	if map == null:
		return null
	if current_map and is_instance_valid(current_map):
		TempoParty.sync_all()
		Net.map_unloading()
		if player and player.get_parent() == current_map:
			current_map.remove_child(player)
		# Take the old map out of the tree now, not at the end of the frame: its colliders would otherwise still be in
		# the physics space while the new map is populated, and ground rays (NPC placement, spawns) land on the old
		# map's terrain — townspeople floating metres above the plaza after returning from the forest.
		if current_map.get_parent():
			current_map.get_parent().remove_child(current_map)
		current_map.queue_free()
	var parent := world_parent if world_parent and is_instance_valid(world_parent) else get_tree().root
	parent.add_child(map)
	# flags first: an opened gate or broken seal must not be baked into the navmesh as a wall
	map.apply_flag_visuals()
	MapBuilder.bake_navigation(map)
	current_map = map
	current_map_id = id
	FX.world = map
	hover_target = null
	hover_loot = null
	hover_ally = null
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
		# a client's monsters are replicas of the host's on the host's map (bh-008); anywhere else a client explores
		# its own world with its own monsters (bh-015)
		if not Net.host_on(id):
			Spawner.populate(map, difficulty)
		NpcDirectory.populate(map)
		TempoParty.spawn_for(map, player, hero)
		QuakeTeam.spawn_for(map, player, hero)
		GuildSummons.spawn_for(map, player, hero)
	TownPortal.spawn_for(map, id)
	Audio.play_music(def.music)
	Audio.play_ambience(def.ambience)
	Audio.set_environment_reverb(def.reverb)
	Events.map_loaded.emit(id)
	map_changed.emit(map)
	Net.on_local_map_loaded(id)
	FX.warm_up()     # behind the loading screen: compile the combat effects now, not on the first blow (bh-014)
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
	TempoParty.regroup(player)

## Teleporter travel with the loading screen. Same-map travel just relocates the player.
func travel(id: StringName, spawn_id: StringName) -> void:
	if travelling or not Net.may_travel():
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

## Travel through a Town Portal: loading screen, then the hero stands at `pos` on map `id` (not at a named spawn).
func travel_to_point(id: StringName, pos: Vector3, yaw := 0.0) -> void:
	if travelling or not Net.may_travel():
		return
	travelling = true
	await _loading.show_for(DB.map_def(id))
	await get_tree().process_frame
	if id != current_map_id or current_map == null:
		load_map(id, &"start")
	if player and is_instance_valid(player):
		player.global_transform = Transform3D(Basis(Vector3.UP, yaw), pos + Vector3.UP * 0.05)
		if player is CharacterBody3D:
			(player as CharacterBody3D).velocity = Vector3.ZERO
		if player.has_method(&"on_teleported"):
			player.call(&"on_teleported")
		TempoParty.regroup(player)
	await get_tree().process_frame
	if in_session:
		save_now()
	await _loading.hide_screen()
	travelling = false

## Walk through a door: fade to black, swap maps, fade back in (interiors are small, no loading screen).
func door_travel(id: StringName, spawn_id: StringName) -> void:
	if travelling or not Net.may_travel():
		return
	travelling = true
	var cover := _fade_cover()
	var tw := cover.create_tween()
	tw.tween_property(cover, "color:a", 1.0, 0.28)
	await tw.finished
	load_map(id, spawn_id)
	await get_tree().process_frame
	await get_tree().process_frame
	if in_session:
		save_now()
	var tw2 := cover.create_tween()
	tw2.tween_property(cover, "color:a", 0.0, 0.35)
	await tw2.finished
	travelling = false

var _fade_layer: CanvasLayer
var _fade_rect: ColorRect

func _fade_cover() -> ColorRect:
	if _fade_rect == null or not is_instance_valid(_fade_rect):
		_fade_layer = CanvasLayer.new()
		_fade_layer.layer = 90
		add_child(_fade_layer)
		_fade_rect = ColorRect.new()
		_fade_rect.color = Color(0.01, 0.008, 0.012, 0.0)
		_fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_fade_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
		_fade_layer.add_child(_fade_rect)
	return _fade_rect

func return_to_town() -> void:
	travel(&"sanctuary", &"waypoint")

## The checkpoint the hero may wake at after a fall (a camp bonfire they rested at), or "".
func checkpoint_name() -> String:
	if hero == null or hero.checkpoint.is_empty() or DB.map_def(StringName(hero.checkpoint.get("map", ""))) == null:
		return ""
	return String(hero.checkpoint.get("name", "your checkpoint"))

## After death: respawn at the current map's entry (towns: the plaza), or at the checkpoint bonfire when asked (bh-007).
## Costs a little gold, never items.
func respawn_player(at_checkpoint := false) -> void:
	var p := player as Player
	if p == null:
		return
	var lost := int(hero.inventory.gold * 0.05)
	hero.inventory.gold -= lost
	if Net.is_client():
		# in someone else's world: get up at this map's entrance, the party's map stays loaded
		place_player(&"start")
		p.respawn()
		Events.player_respawned.emit()
		if lost > 0:
			Events.notify.emit("You lost %d gold." % lost, &"info")
		return
	var map_id := current_map_id
	var spawn := &"start"
	if Net.is_host() and not (at_checkpoint and checkpoint_name() != "" and StringName(hero.checkpoint.map) != current_map_id):
		# hosting: the world (and everyone in it) stays; rebuilding the map would drag every client through a loading
		# screen and reset the monsters they are fighting (bh-011). Get up at this map's entrance (or its checkpoint).
		for s in ([StringName(hero.checkpoint.get("spawn", "start"))] if at_checkpoint and checkpoint_name() != "" else []) + [&"arrival", &"entrance", &"start"]:
			if current_map.spawns.has(s):
				spawn = s
				break
		place_player(spawn)
		p.respawn()
		Events.player_respawned.emit()
		if lost > 0:
			Events.notify.emit("You lost %d gold." % lost, &"info")
		return
	if at_checkpoint and checkpoint_name() != "":
		map_id = StringName(hero.checkpoint.map)
		spawn = StringName(hero.checkpoint.get("spawn", "start"))
	elif not DB.map_def(map_id).is_town:
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

# ---- Multiplayer (bh-008) ---------------------------------------------------------------------------------------

## A client goes to the host (joining, Regroup, a summons answered Go): load the host's map (its monsters come from
## the host) and stand beside the host.
func net_follow(id: StringName, pos: Vector3, yaw: float) -> void:
	if DB.map_def(id) == null:
		return
	travelling = true
	await _loading.show_for(DB.map_def(id))
	await get_tree().process_frame
	load_map(id, &"start")
	if player and is_instance_valid(player):
		var spot := Net.portal_arrival(pos, yaw)
		player.global_transform = Transform3D(Basis(Vector3.UP, yaw), spot + Vector3.UP * 0.05)
		if player is CharacterBody3D:
			(player as CharacterBody3D).velocity = Vector3.ZERO
		if player.has_method(&"on_teleported"):
			player.call(&"on_teleported")
		TempoParty.regroup(player)
	await get_tree().process_frame
	await _loading.hide_screen()
	travelling = false

## Rebuild the current map where the hero stands (leaving someone's world: the map gets its own monsters back).
func reload_current_map() -> void:
	if current_map == null or player == null:
		return
	var t := (player as Node3D).global_transform
	travelling = true
	await _loading.show_for(DB.map_def(current_map_id))
	await get_tree().process_frame
	load_map(current_map_id, hero.current_spawn if hero else &"start")
	if player and is_instance_valid(player):
		player.global_transform = t
		if player.has_method(&"on_teleported"):
			player.call(&"on_teleported")
		TempoParty.regroup(player)
	await get_tree().process_frame
	await _loading.hide_screen()
	travelling = false

# ---- World state ------------------------------------------------------------------------------------------------

func set_world_flag(flag: StringName, value: Variant = true) -> void:
	if hero == null:
		return
	hero.world_flags[flag] = value
	hero.check_promotions()
	Events.world_flag_set.emit(flag, value)

func has_flag(flag: StringName) -> bool:
	return hero != null and bool(hero.world_flags.get(flag, false))

func _on_flag(flag: StringName, _v: Variant) -> void:
	if current_map:
		current_map.apply_flag_visuals(flag, true)
		current_map.refresh_teleporters()
	_check_tempo_grade()

## A level or a deed may raise the grade of the spirits answering the Tempo-Caller: the old offers fade at once.
func _check_tempo_grade() -> void:
	if hero == null or not in_session:
		return
	var g := TempoRules.check_grade(hero)
	if g > 0:
		Events.notify.emit("Stronger spirits answer at the Shrine of the Fallen: %s grade." % DataTempos.grade_def(g).name, &"info")
