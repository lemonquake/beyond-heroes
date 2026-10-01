class_name ZaraelStory
## bh-029: Zarael's story events (StoryDirector forwards to this). docs/LORE.md §11, DataZarael.
##   Kethrax falls, or an old save that already killed him loads any map -> once: "a ship waits at Wyman's Marsh Jetty"
##   the hero lands at Agdao for the first time                          -> Terax's welcome (cutscene terax_welcome)
##   the third relay pylon is cut                                        -> zr_relays_cut
##   a Vault's lord falls                                                -> its ward pylon on the Bridge burns steady
##   the Leash-Abbot falls                                               -> wake the Dawn Engine
##   the Dawn Engine wakes                                               -> every Heartwire surface burns bright

const SHIP_NOTE := "A ship from Zarael has put in at Wyman Outpost's Marsh Jetty. Its captain is asking for the hero who killed Kethrax."

static func on_map(map_id: StringName) -> void:
	var hero := Game.hero
	if hero == null:
		return
	if DataZarael.ship_ready(hero) and not DataZarael.has(hero, DataZarael.F_SHIP_TOLD):
		_tell_ship.call_deferred()
	if map_id == &"agdao" and not DataZarael.has(hero, DataZarael.F_TERAX):
		_welcome(hero)

static func _tell_ship() -> void:
	if Game.hero == null or DataZarael.has(Game.hero, DataZarael.F_SHIP_TOLD):
		return
	Game.set_world_flag(DataZarael.F_SHIP_TOLD, true)
	Events.notify.emit(SHIP_NOTE, &"quest")

## Terax's welcome plays once the loading screen has gone (the hero has stepped off the ship onto the pier).
static func _welcome(hero: HeroData) -> void:
	var tree := Game.get_tree()
	var map := Game.current_map
	var wait := func() -> void:
		for i in 60:
			if not Game.travelling:
				break
			await tree.create_timer(0.1).timeout
		await tree.create_timer(0.6).timeout
		if Game.hero != hero or Game.current_map != map or DataZarael.has(hero, DataZarael.F_TERAX) or CutscenePlayer.is_playing():
			return
		CutscenePlayer.play(&"terax_welcome", func() -> void:
			if Game.hero == hero:
				Game.set_world_flag(DataZarael.F_TERAX, true))
	wait.call()

static func on_flag(flag: StringName, v: Variant) -> void:
	if not bool(v) or Game.hero == null:
		return
	var hero := Game.hero
	if DataZarael.RELAY_FLAGS.has(flag):
		var n := DataZarael.relays_cut(hero)
		if n >= DataZarael.RELAY_FLAGS.size() and not DataZarael.has(hero, DataZarael.F_RELAYS):
			Game.set_world_flag(DataZarael.F_RELAYS, true)
			Events.notify.emit("The three relay pylons are free of their chains. Agdao's lamps steady. Return to Wirekeeper Halvessa Orn.", &"quest")
		elif n < DataZarael.RELAY_FLAGS.size():
			Events.notify.emit("Relay pylon freed (%d of %d)." % [n, DataZarael.RELAY_FLAGS.size()], &"quest")
		return
	for d in DataZarael.VAULT_FLAGS:
		if DataZarael.VAULT_FLAGS[d] == flag:
			var left := DataZarael.VAULT_FLAGS.size() - DataZarael.vaults_cleared(hero)
			var name := String(DataDungeons.get_def(d).get("name", "The Vault"))
			Events.notify.emit("%s is quiet. Its ward pylon on the Bridge of Death burns steady.%s" % [name,
				" %d Vault%s still chained." % [left, "" if left == 1 else "s"] if left > 0 else " The Bridge of Death is safe to cross."], &"quest")
			return
	if flag == DataZarael.F_ABBOT:
		Events.notify.emit("The Leash-Abbot is dead and his chains fall slack. Wake the Dawn Engine.", &"quest")
	elif flag == DataZarael.F_RESTORED:
		if Game.current_map:
			MaterialLibrary.swap_wire(Game.current_map, true)
		Events.notify.emit("The Dawn Engine wakes. Clean current runs through every line of the Heartwire.", &"quest")

static func on_boss(boss: Node) -> void:
	if boss == null or not is_instance_valid(boss) or not ("def" in boss) or boss.def == null:
		return
	if boss.def.id == &"kethrax":
		var hero := Game.hero
		Game.get_tree().create_timer(14.0).timeout.connect(func() -> void:
			if Game.hero == hero and not DataZarael.has(hero, DataZarael.F_SHIP_TOLD) and not CutscenePlayer.is_playing():
				_tell_ship())
