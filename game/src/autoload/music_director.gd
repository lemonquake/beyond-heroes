extends Node
## Music (autoload `Music`, bh-025): one director decides what plays, from four layers, highest first:
##   override   a cutscene or a conversation asked for a track (`push` / `pop`, e.g. Paul David's tale: aljay_theme)
##   boss       a boss has seen the hero: boss_theme until it falls or loses them
##   battle     monsters are fighting the hero in the open country, or a dungeon's champion is: battle_theme
##   base       the map's own music (`play`, from MapDef.music); anything unknown or unset is main_theme
## Tracks crossfade, each on its own player. The exploring themes remember where they stopped, so the road's music
## carries on after a fight instead of starting over. Stingers (boss seen, boss down, the hero falls) duck the music
## for a moment, and the pause menu puts it behind a low-pass filter.
## The Music bus sits at Settings.music_volume (60 % until the player moves the slider).

const DIR := "res://assets/audio/music/"
const DEFAULT := &"main_theme"

## gain: dB that brings the track to about -18 LUFS (tools/audio/import_pack.py prints each track's loudness).
## resume: coming back to the track within RESUME_WINDOW carries on where it stopped.
const TRACKS := {
	&"main_theme": {"file": "main_theme.mp3", "gain": 3.0, "resume": true},
	&"battle_theme": {"file": "battle_theme.mp3", "gain": -2.0},
	&"boss_theme": {"file": "boss_theme.mp3", "gain": -2.5},
	&"dungeon_theme": {"file": "dungeon_theme1.mp3", "gain": -0.3, "resume": true},
	&"fire_dungeon_theme": {"file": "fire_dungeon_theme.mp3", "gain": -0.5, "resume": true},
	&"ice_dungeon_theme": {"file": "ice_dungeon_theme.mp3", "gain": -1.0, "resume": true},
	&"aljay_theme": {"file": "aljay_theme.mp3", "gain": -2.0},
	&"music_legend": {"file": "music_legend.wav", "gain": 0.0},
}
## Maps with one of these as their base are dungeons: fighting is the whole of them, so only a champion or a boss
## changes the music there. Everywhere else any fight brings the battle theme.
const DUNGEON_TRACKS: Array[StringName] = [&"dungeon_theme", &"fire_dungeon_theme", &"ice_dungeon_theme"]

const CALM := 0
const BATTLE := 1
const BOSS := 2
const SCAN_EVERY := 0.4          # s between looks at who is fighting
const SCAN_RANGE := 45.0         # m: an engaged monster farther than this is someone else's fight
const REPLICA_RANGE := 20.0      # m
const CALM_HOLD := 6.0           # s without a fight before the battle theme lets go
const BOSS_HOLD := 3.0
const SETTLE := 0.15             # s a change waits, so a pop followed by a push of the same track is no change at all
const RESUME_WINDOW := 180.0     # s
const MUFFLE_HZ := 900.0
const OPEN_HZ := 20500.0

var _base: StringName = DEFAULT
var _overrides: Array = []       # [[key, track]], the last one wins
var _combat := CALM
var _calm_t := 0.0
var _scan_t := 0.0
var _dead := false
var _blow_ms := -100000          # when the hero last traded a blow with a monster
var _victory := false            # the boss of this map is down: its arena stops playing the boss theme
var _want: StringName = &""
var _settle_t := -1.0
var _fade_in := 2.0
var _fade_out := 2.0
var _players := {}               # track -> AudioStreamPlayer
var _levels := {}                # track -> 0..1 crossfade level
var _stopped := {}               # track -> [position s, msec when it stopped]
var _duck := 1.0                 # linear gain the stingers pull the music down to
var _duck_target := 1.0
var _duck_hold := 0.0
var _lowpass: AudioEffectLowPassFilter
var _lowpass_idx := -1
var _cutoff := OPEN_HZ
var _bus := -1

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_bus = AudioServer.get_bus_index("Music")
	if _bus >= 0:
		_lowpass = AudioEffectLowPassFilter.new()
		_lowpass.cutoff_hz = OPEN_HZ
		_lowpass.resonance = 0.6
		AudioServer.add_bus_effect(_bus, _lowpass)
		_lowpass_idx = AudioServer.get_bus_effect_count(_bus) - 1
		AudioServer.set_bus_effect_enabled(_bus, _lowpass_idx, false)
	Events.boss_engaged.connect(_on_boss_engaged)
	Events.boss_defeated.connect(_on_boss_defeated)
	Events.player_died.connect(_on_player_died)
	Events.damage_dealt.connect(_on_damage)
	Events.player_respawned.connect(func() -> void: _dead = false)

# ---- What should play ------------------------------------------------------------------------------------------------

## The map's (or the menu's) music. Unknown and empty names play the main theme.
func play(track: StringName, fade := 2.0) -> void:
	_base = track_id(track)
	_victory = false
	_set_combat(CALM)
	_changed(fade, fade)

## A cutscene or a conversation takes the music over until `pop(key)`. One track per key.
func push(key: StringName, track: StringName, fade := 1.5) -> void:
	pop(key, fade)
	_overrides.append([key, track_id(track)])
	_changed(fade, fade)

func pop(key: StringName, fade := 2.0) -> void:
	for i in range(_overrides.size() - 1, -1, -1):
		if _overrides[i][0] == key:
			_overrides.remove_at(i)
			_changed(fade, fade)

## A short fanfare over the music, which steps back for it.
func sting(name: StringName, duck_db := -9.0, hold := 2.5, volume_db := -2.0) -> void:
	if not Audio.has_sound(name):
		return
	Audio.play(name, volume_db, 0.0, "Music")
	_duck_target = db_to_linear(duck_db)
	_duck_hold = hold

static func track_id(track: StringName) -> StringName:
	return track if TRACKS.has(track) else DEFAULT

## The track the layers add up to right now.
func wanted() -> StringName:
	if not _overrides.is_empty():
		return _overrides.back()[1]
	if _combat == BOSS:
		return &"boss_theme"
	if _combat == BATTLE and Settings.combat_music:
		return &"battle_theme"
	if _victory and _base == &"boss_theme":
		return DEFAULT
	return _base

## The track that is playing (or fading in).
func current() -> StringName:
	return _want

func combat_level() -> int:
	return _combat

func _changed(fade_in := 2.0, fade_out := 2.0) -> void:
	_fade_in = fade_in
	_fade_out = fade_out
	if _settle_t < 0.0:
		_settle_t = SETTLE

# ---- Fights ----------------------------------------------------------------------------------------------------------

func _set_combat(level: int) -> void:
	if level == _combat:
		return
	var rising := level > _combat
	_combat = level
	# into a fight quickly, out of it gently
	_changed(0.8 if rising else 3.0, 1.2 if rising else 3.5)

## CALM / BATTLE / BOSS from the monsters that are after the hero right now.
func _scan() -> int:
	var game := get_node_or_null(^"/root/Game")
	if game == null or _dead or game.get(&"in_cutscene"):
		return CALM
	var pl = game.get(&"player")
	if not (pl is Node3D) or not is_instance_valid(pl) or not pl.is_inside_tree():
		return CALM
	var open_country := not DUNGEON_TRACKS.has(_base)
	var here: Vector3 = pl.global_position
	var level := CALM
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if not (e is Enemy) or not e.alive:
			continue
		var d2: float = e.global_position.distance_squared_to(here)
		if d2 > SCAN_RANGE * SCAN_RANGE:
			continue
		# a client's monsters on the host's map are replicas with no mind of their own: there the fight is known by
		# the blows (bh-008)
		if not (e.brain.is_engaged() or (e.net_replica and d2 < REPLICA_RANGE * REPLICA_RANGE and Time.get_ticks_msec() - _blow_ms < 5000)):
			continue
		if e.is_boss:
			return BOSS
		if open_country or e.is_miniboss():
			level = BATTLE
	return level

func _track_fights(delta: float) -> void:
	_scan_t -= delta
	if _scan_t > 0.0:
		return
	_scan_t = SCAN_EVERY
	if _settle_t < 0.0 and wanted() != _want:
		_settle_t = 0.0             # something a layer reads changed without telling (a setting set directly)
	var level := _scan()
	if level >= _combat:
		_calm_t = 0.0
		_set_combat(level)
		return
	_calm_t += SCAN_EVERY
	if _calm_t >= (BOSS_HOLD if _combat == BOSS else CALM_HOLD):
		_calm_t = 0.0
		_set_combat(level)

func _on_boss_engaged(boss: Node) -> void:
	if boss is Enemy and boss.is_boss and _combat != BOSS and _overrides.is_empty():
		sting(&"sting_boss", -7.0, 1.6)
		_scan_t = 0.0

func _on_boss_defeated(boss: Node) -> void:
	if not (boss is Enemy) or not boss.is_boss:
		return
	_victory = true
	sting(&"sting_victory", -14.0, 4.0)
	_set_combat(CALM)
	_calm_t = 0.0
	_scan_t = 2.0

func _on_damage(target: Node, _result: DamageResult, _position: Vector3, attacker: Node) -> void:
	if (target is Player and attacker is Enemy) or (attacker is Player and target is Enemy):
		_blow_ms = Time.get_ticks_msec()

func _on_player_died() -> void:
	_dead = true
	sting(&"sting_defeat", -10.0, 4.5)
	_set_combat(CALM)

# ---- Playback --------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	_track_fights(delta)
	if _settle_t >= 0.0:
		_settle_t -= delta
		if _settle_t < 0.0:
			_switch_to(wanted())
	_mix(delta)
	_muffle(delta)

func _switch_to(track: StringName) -> void:
	if track == _want:
		return
	_want = track
	var p := _player(track)
	if p == null or p.playing:
		return                      # still fading out from last time: it turns around where it is
	var from := 0.0
	if TRACKS[track].get("resume", false) and _stopped.has(track):
		var s: Array = _stopped[track]
		if Time.get_ticks_msec() - int(s[1]) < RESUME_WINDOW * 1000.0 and float(s[0]) < p.stream.get_length() - 5.0:
			from = float(s[0])
	_levels[track] = 0.0
	p.volume_db = -60.0
	p.play(from)

func _player(track: StringName) -> AudioStreamPlayer:
	if _players.has(track):
		return _players[track]
	var path := DIR + String(TRACKS[track].file)
	if not ResourceLoader.exists(path):
		return null
	var st: AudioStream = load(path)
	if st is AudioStreamMP3:
		st.loop = true
	elif st is AudioStreamWAV:
		st.loop_mode = AudioStreamWAV.LOOP_FORWARD
		st.loop_end = int(st.get_length() * st.mix_rate)
	var p := AudioStreamPlayer.new()
	p.stream = st
	p.bus = "Music"
	add_child(p)
	_players[track] = p
	_levels[track] = 0.0
	return p

## Every live track moves toward 1 (the wanted one) or 0, on an equal-power curve, under the stingers' duck.
func _mix(delta: float) -> void:
	if _duck_hold > 0.0:
		_duck_hold -= delta
		if _duck_hold <= 0.0:
			_duck_target = 1.0
	_duck = move_toward(_duck, _duck_target, delta * (4.0 if _duck_target < _duck else 0.5))
	for track: StringName in _players:
		var p: AudioStreamPlayer = _players[track]
		if not p.playing:
			continue
		var lvl: float = _levels[track]
		if track == _want:
			lvl = move_toward(lvl, 1.0, delta / maxf(_fade_in, 0.05))
		else:
			lvl = move_toward(lvl, 0.0, delta / maxf(_fade_out, 0.05))
			if lvl <= 0.0:
				_stopped[track] = [p.get_playback_position(), Time.get_ticks_msec()]
				p.stop()
		_levels[track] = lvl
		p.volume_db = float(TRACKS[track].gain) + linear_to_db(maxf(sin(lvl * PI * 0.5) * _duck, 0.001))

## Paused: the music goes behind a wall.
func _muffle(delta: float) -> void:
	if _lowpass == null:
		return
	var target := MUFFLE_HZ if get_tree().paused else OPEN_HZ
	if is_equal_approx(_cutoff, target):
		return
	# move in octaves, so the sweep sounds even
	_cutoff = clampf(_cutoff * pow(2.0, (9.0 if target > _cutoff else -9.0) * delta), MUFFLE_HZ, OPEN_HZ)
	_lowpass.cutoff_hz = _cutoff
	AudioServer.set_bus_effect_enabled(_bus, _lowpass_idx, _cutoff < OPEN_HZ)
