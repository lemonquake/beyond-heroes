extends TestCase
## bh-025: the music system (MusicDirector: the map's track, battle and boss layers, cutscene and conversation
## overrides, the 60 % default) and the recorded weapon and spell sounds.

func _reset() -> void:
	Music._overrides.clear()
	Music._combat = Music.CALM
	Music._victory = false

# ---- Tracks ------------------------------------------------------------------------------------------------------

func test_every_track_has_its_file() -> void:
	for id: StringName in Music.TRACKS:
		ok(ResourceLoader.exists(Music.DIR + String(Music.TRACKS[id].file)), "%s has its file" % id)
	for id in [&"main_theme", &"battle_theme", &"boss_theme", &"dungeon_theme", &"fire_dungeon_theme", &"ice_dungeon_theme", &"aljay_theme"]:
		ok(Music.TRACKS.has(id), "%s is a track" % id)
		ok(load(Music.DIR + String(Music.TRACKS[id].file)) is AudioStreamMP3, "%s is the recorded theme" % id)

func test_main_theme_is_the_default() -> void:
	eq(Music.DEFAULT, &"main_theme", "the default track")
	eq(Music.track_id(&""), &"main_theme", "no music named: the main theme")
	eq(Music.track_id(&"no_such_track"), &"main_theme", "an unknown name: the main theme")
	eq(Music.track_id(&"boss_theme"), &"boss_theme", "a known name stays")
	_reset()
	Music.play(&"")
	eq(Music.wanted(), &"main_theme", "a map without music plays the main theme")

func test_music_volume_defaults_to_60_percent() -> void:
	var fresh = preload("res://src/autoload/settings.gd").new()
	near(fresh.music_volume, 0.6, 0.0001, "music starts at 60 %")
	ok(fresh.combat_music, "battle music starts on")
	ok("combat_music" in Settings.KEYS and "music_volume" in Settings.KEYS, "both are saved")
	fresh.free()
	var bus := AudioServer.get_bus_index("Music")
	ok(bus >= 0, "the Music bus exists")
	near(db_to_linear(AudioServer.get_bus_volume_db(bus)), Settings.music_volume, 0.01, "the bus follows the setting")

func test_every_map_names_a_track() -> void:
	var used := {}
	for id in DB.maps:
		var m: MapDef = DB.maps[id]
		ok(Music.TRACKS.has(m.music), "%s: %s is a track" % [id, m.music])
		used[m.music] = true
	ok(used.has(&"main_theme"), "the towns play the main theme")
	ok(used.has(&"dungeon_theme"), "dungeons play the dungeon theme")
	eq(DB.map_def(&"sanctuary").music, &"main_theme", "Malasugue Town")
	eq(StringName(DataDungeons.get_def(_dungeon_of(&"ember")).music), &"fire_dungeon_theme", "the ember dungeon plays the fire theme")
	eq(StringName(DataDungeons.get_def(_dungeon_of(&"rime")).music), &"ice_dungeon_theme", "the rime dungeon plays the ice theme")

func _dungeon_of(theme: StringName) -> StringName:
	var defs := DataDungeons.defs()
	for id in defs:
		if defs[id].get("theme", &"") == theme:
			return id
	return &""

# ---- Layers ------------------------------------------------------------------------------------------------------

func test_layers() -> void:
	_reset()
	Music.play(&"dungeon_theme")
	eq(Music.wanted(), &"dungeon_theme", "the map's music")
	Music._combat = Music.BATTLE
	eq(Music.wanted(), &"battle_theme", "a fight: the battle theme")
	var was := Settings.combat_music
	Settings.combat_music = false
	eq(Music.wanted(), &"dungeon_theme", "battle music off: the map's music stays")
	Music._combat = Music.BOSS
	eq(Music.wanted(), &"boss_theme", "... but a boss still brings its theme")
	Settings.combat_music = was
	Music.push(&"cutscene", &"aljay_theme")
	eq(Music.wanted(), &"aljay_theme", "a cutscene's music is over everything")
	Music.push(&"dialogue", &"music_legend")
	eq(Music.wanted(), &"music_legend", "the newest override wins")
	Music.pop(&"dialogue")
	eq(Music.wanted(), &"aljay_theme", "and hands back")
	Music.pop(&"cutscene")
	eq(Music.wanted(), &"boss_theme", "back to the fight")
	Music._combat = Music.CALM
	eq(Music.wanted(), &"dungeon_theme", "back to the map")
	Music.pop(&"cutscene")
	eq(Music._overrides.size(), 0, "popping twice is harmless")

func test_a_boss_arena_relaxes_when_its_boss_falls() -> void:
	_reset()
	Music.play(&"boss_theme")
	eq(Music.wanted(), &"boss_theme", "the arena")
	Music._victory = true
	eq(Music.wanted(), &"main_theme", "the boss is down")
	Music.play(&"boss_theme")
	eq(Music.wanted(), &"boss_theme", "the next arena starts fresh")
	Music.play(&"main_theme")

func test_the_wanted_track_plays() -> void:
	_reset()
	Music.play(&"ice_dungeon_theme", 0.05)
	for i in 30:
		await host.get_tree().process_frame
	eq(Music.current(), &"ice_dungeon_theme", "the director switched")
	ok(Music._players.has(&"ice_dungeon_theme") and Music._players[&"ice_dungeon_theme"].playing, "its player is playing")
	eq(Music._players[&"ice_dungeon_theme"].bus, &"Music", "on the Music bus")
	ok((Music._players[&"ice_dungeon_theme"].stream as AudioStreamMP3).loop, "looping")
	Music.play(&"main_theme", 0.05)

func test_monsters_bring_the_battle_theme_only_in_open_country() -> void:
	ok(not Music.DUNGEON_TRACKS.has(&"main_theme"), "the roads are open country")
	for id in [&"dungeon_theme", &"fire_dungeon_theme", &"ice_dungeon_theme"]:
		ok(Music.DUNGEON_TRACKS.has(id), "%s marks a dungeon" % id)

# ---- Aljay's theme -----------------------------------------------------------------------------------------------

func test_pauls_tale_plays_aljays_theme() -> void:
	eq(DataCutscenes.make(&"the_three").music, &"aljay_theme", "the tale of the three")
	eq(DataCutscenes.make(&"chain_breaks").music, &"aljay_theme", "Aljay's chain breaks")
	var nodes: Dictionary = DB.npc(&"paul_david").graph.nodes
	for id in ["shard", "after_tale", "brand", "orders", "aljay", "roydo", "report", "chains", "spire"]:
		eq(StringName(nodes[id].get("music", &"")), &"aljay_theme", "Paul David, '%s'" % id)
	for id in ["stranger", "stranger_hub", "why_here"]:
		ok(not nodes[id].has("music"), "'%s' keeps the town's music" % id)

func test_a_conversation_holds_its_music_until_it_ends() -> void:
	_reset()
	Music.play(&"main_theme")
	var hero := HeroData.new()
	var s := DialogueSession.start(DB.npc(&"paul_david"), hero)
	s.begin("stranger_hub")
	eq(Music.wanted(), &"main_theme", "small talk: the town's music")
	s._enter("roydo")
	eq(Music.wanted(), &"aljay_theme", "he speaks of Roydo")
	s._enter("hub")
	eq(Music.wanted(), &"aljay_theme", "it holds through the conversation")
	s.finish()
	eq(Music.wanted(), &"main_theme", "and ends with it")

# ---- Sounds ------------------------------------------------------------------------------------------------------

func test_every_weapon_has_its_sounds() -> void:
	for id in DB.weapon_types:
		var wt: WeaponTypeDef = DB.weapon_types[id]
		for snd in [wt.swing_sound, wt.hit_sound, wt.heavy_sound]:
			ok(Audio.has_sound(snd), "%s: %s exists" % [id, snd])
	eq(DB.weapon_type(&"sword").hit_sound, &"sword_hit", "swords")
	eq(DB.weapon_type(&"axe").hit_sound, &"axe_hit", "axes")
	eq(DB.weapon_type(&"club").hit_sound, &"hammer_hit", "clubs and hammers")
	eq(DB.weapon_type(&"bow").swing_sound, &"bow_attack", "bows")
	eq(DB.weapon_type(&"staff").swing_sound, &"mage_attack", "staves")
	eq(DB.weapon_type(&"staff").heavy_sound, &"mage_strong_attack", "a staff's heavy attack")
	eq(DB.weapon_type(&"sword").heavy_sound, &"swing_heavy", "other weapons keep the heavy swing")
	eq(Audio._variations(&"sword_hit").size(), 3, "three sword hits")
	eq(Audio._variations(&"bow_attack").size(), 3, "three bow shots")

func test_the_recorded_spells() -> void:
	eq(DB.skill(&"cleave").sound_cast, &"cleave", "Cleave")
	eq(DB.skill(&"firebolt").sound_cast, &"fireball_cast", "Firebolt cast")
	eq(DB.skill(&"firebolt").sound_hit, &"fireball_hit", "Firebolt hit")
	eq(DB.skill(&"meteor").sound_cast, &"meteor_cast", "Meteor cast")
	eq(DB.skill(&"meteor").sound_hit, &"meteor_hit", "Meteor hit")
	eq(DB.skill(&"chain_lightning").sound_cast, &"chain_lightning", "Chain Lightning")
	eq(DB.skill(&"blizzard").sound_cast, &"blizzard_cast", "Blizzard")
	for id in DB.skills:
		var sk: SkillDef = DB.skills[id]
		for snd in [sk.sound_cast, sk.sound_hit]:
			ok(snd == &"" or Audio.has_sound(snd), "%s: %s exists" % [id, snd])

func test_the_made_sounds_exist() -> void:
	for snd in [&"dagger_hit", &"spear_hit", &"claw_hit", &"fist_hit", &"magic_hit", &"crossbow_fire", &"greatsword_hit",
			&"greataxe_hit", &"hit_metal", &"heartbeat", &"ui_buy", &"ui_craft", &"loot_pickup", &"holy_cast", &"sting_victory",
			&"sting_defeat", &"sting_boss"]:
		ok(Audio.has_sound(snd), "%s exists" % snd)
	for id in DB.enemies:
		var sounds: Dictionary = DB.enemies[id].sounds
		for k in sounds:
			ok(Audio.has_sound(sounds[k]), "%s: %s (%s) exists" % [id, sounds[k], k])
