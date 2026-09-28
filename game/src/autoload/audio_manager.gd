extends Node
## Audio playback (autoload `Audio`): buses, pooled 2D/3D SFX with random variations, music and ambience crossfades,
## environment reverb per map.

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const POOL_2D := 16
const POOL_3D := 32

var _cache := {}                 # name -> Array[AudioStream] (variations)
var _pool2d: Array[AudioStreamPlayer] = []
var _pool3d: Array[AudioStreamPlayer3D] = []
var _music_a: AudioStreamPlayer
var _music_b: AudioStreamPlayer
var _music_current: StringName = &""
var _amb: AudioStreamPlayer
var _amb_current: StringName = &""
var _last_play := {}             # name -> msec, throttles identical sounds in the same frame burst
var _reverb: AudioEffectReverb

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_make_buses()
	for i in POOL_2D:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_pool2d.append(p)
	for i in POOL_3D:
		var p3 := AudioStreamPlayer3D.new()
		p3.bus = "SFX"
		p3.unit_size = 8.0
		p3.max_distance = 45.0
		p3.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		add_child(p3)
		_pool3d.append(p3)
	_music_a = _mk_stream_player("Music")
	_music_b = _mk_stream_player("Music")
	_amb = _mk_stream_player("Ambience")
	Settings.apply()
	_start_prefetch()

func _mk_stream_player(bus: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = bus
	add_child(p)
	return p

func _make_buses() -> void:
	for n in ["Music", "SFX", "Voice", "Ambience", "UI"]:
		if AudioServer.get_bus_index(n) < 0:
			var i := AudioServer.bus_count
			AudioServer.add_bus(i)
			AudioServer.set_bus_name(i, n)
			AudioServer.set_bus_send(i, "Master")
	var sfx := AudioServer.get_bus_index("SFX")
	if AudioServer.get_bus_effect_count(sfx) == 0:
		_reverb = AudioEffectReverb.new()
		_reverb.room_size = 0.6
		_reverb.damping = 0.5
		_reverb.wet = 0.0
		_reverb.dry = 1.0
		AudioServer.add_bus_effect(sfx, _reverb)
		var comp := AudioEffectCompressor.new()
		comp.threshold = -10.0
		comp.ratio = 4.0
		AudioServer.add_bus_effect(sfx, comp)
	var master := AudioServer.get_bus_index("Master")
	if AudioServer.get_bus_effect_count(master) == 0:
		var lim := AudioEffectHardLimiter.new()
		AudioServer.add_bus_effect(master, lim)
	Settings._apply_audio()

## Environment response: more reverb in catacombs/temple, almost none outdoors.
func set_environment_reverb(amount: float) -> void:
	if _reverb:
		_reverb.wet = clampf(amount, 0.0, 1.0) * 0.35
		_reverb.room_size = lerpf(0.3, 0.9, amount)

## SFX prefetch (bh-014): every sound effect (15 MB) is read on a loader thread at startup instead of from disk on the
## game thread the first time it plays (the first blow of a session waited ~15 ms for its hurt and hit sounds). The
## streams are held here so they stay in the resource cache; `load()` then returns them at once.
var _prefetch: Array[String] = []
var _prefetched := {}               # path -> AudioStream (keeps the cache entry alive)

func _start_prefetch() -> void:
	var files: PackedStringArray
	if ResourceLoader.has_method(&"list_directory"):
		files = ResourceLoader.call(&"list_directory", SFX_DIR)
	else:
		files = DirAccess.get_files_at(SFX_DIR)
	for f in files:
		var fn := f.trim_suffix(".import").trim_suffix(".remap")
		if not fn.ends_with(".wav"):
			continue
		var path := SFX_DIR + fn
		if _prefetch.has(path) or not ResourceLoader.exists(path):
			continue
		if ResourceLoader.load_threaded_request(path, "AudioStream") == OK:
			_prefetch.append(path)
	set_process(not _prefetch.is_empty())

func _process(_d: float) -> void:
	var i := 0
	while i < _prefetch.size():
		var path := _prefetch[i]
		var st := ResourceLoader.load_threaded_get_status(path)
		if st == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			i += 1
			continue
		if st == ResourceLoader.THREAD_LOAD_LOADED:
			_prefetched[path] = ResourceLoader.load_threaded_get(path)
		_prefetch.remove_at(i)
	if _prefetch.is_empty():
		set_process(false)

func _variations(name: StringName) -> Array:
	if _cache.has(name):
		return _cache[name]
	var out := []
	var base := SFX_DIR + String(name)
	if ResourceLoader.exists(base + ".wav"):
		out.append(load(base + ".wav"))
	var i := 1
	while ResourceLoader.exists("%s_%d.wav" % [base, i]):
		out.append(load("%s_%d.wav" % [base, i]))
		i += 1
	_cache[name] = out
	return out

func has_sound(name: StringName) -> bool:
	return not _variations(name).is_empty()

func _throttled(name: StringName) -> bool:
	var now := Time.get_ticks_msec()
	if now - int(_last_play.get(name, -1000)) < 35:
		return true
	_last_play[name] = now
	return false

func play(name: StringName, volume_db := 0.0, pitch_var := 0.06, bus := "SFX") -> void:
	if name == &"" or _throttled(name):
		return
	var v := _variations(name)
	if v.is_empty():
		return
	var p: AudioStreamPlayer = null
	for q in _pool2d:
		if not q.playing:
			p = q
			break
	if p == null:
		p = _pool2d[0]
	p.stream = v[randi() % v.size()]
	p.volume_db = volume_db
	p.pitch_scale = 1.0 + randf_range(-pitch_var, pitch_var)
	p.bus = bus
	p.play()

## UI / non-positional feedback sound.
func play_ui(name: StringName, volume_db := 0.0) -> void:
	play(name, volume_db, 0.02, "UI")

var _loops := {}   # owner instance id -> AudioStreamPlayer3D

## A looping positional sound owned by a node (whirlwind, channels). One loop per owner.
func play_loop(name: StringName, owner: Node3D, volume_db := -4.0) -> void:
	stop_loop(owner)
	var p := make_loop(name, owner, volume_db)
	if p:
		_loops[owner.get_instance_id()] = p

func stop_loop(owner: Node) -> void:
	var id := owner.get_instance_id()
	if _loops.has(id):
		var p = _loops[id]
		if is_instance_valid(p):
			p.queue_free()
		_loops.erase(id)

func ui(name: StringName) -> void:
	play(name, -4.0, 0.02, "UI")

func play_at(name: StringName, pos: Vector3, volume_db := 0.0, pitch_var := 0.08) -> void:
	if name == &"" or _throttled(name):
		return
	var v := _variations(name)
	if v.is_empty():
		return
	var p: AudioStreamPlayer3D = null
	for q in _pool3d:
		if not q.playing:
			p = q
			break
	if p == null:
		p = _pool3d[0]
	p.stream = v[randi() % v.size()]
	p.global_position = pos
	p.volume_db = volume_db
	p.pitch_scale = 1.0 + randf_range(-pitch_var, pitch_var)
	p.play()

## Looping 3D emitter owned by the caller (torches, teleporter hum, whirlwind).
func make_loop(name: StringName, parent: Node3D, volume_db := -6.0, max_distance := 18.0) -> AudioStreamPlayer3D:
	var v := _variations(name)
	if v.is_empty():
		return null
	var p := AudioStreamPlayer3D.new()
	var st: AudioStream = v[0].duplicate()
	if st is AudioStreamWAV:
		st.loop_mode = AudioStreamWAV.LOOP_FORWARD
		st.loop_begin = 0
		st.loop_end = int(st.get_length() * st.mix_rate)
	p.stream = st
	p.bus = "SFX"
	p.volume_db = volume_db
	p.max_distance = max_distance
	p.unit_size = 4.0
	parent.add_child(p)
	p.play()
	return p

func play_music(name: StringName, fade := 2.0) -> void:
	if name == _music_current:
		return
	_music_current = name
	var path := MUSIC_DIR + String(name) + ".wav"
	var incoming := _music_b if _music_a.playing else _music_a
	var outgoing := _music_a if incoming == _music_b else _music_b
	var tw := create_tween().set_parallel(true)
	if ResourceLoader.exists(path):
		var st: AudioStream = load(path)
		if st is AudioStreamWAV:
			st.loop_mode = AudioStreamWAV.LOOP_FORWARD
			st.loop_end = int(st.get_length() * st.mix_rate)
		incoming.stream = st
		incoming.volume_db = -40.0
		incoming.play()
		tw.tween_property(incoming, "volume_db", 0.0, fade)
	if outgoing.playing:
		tw.tween_property(outgoing, "volume_db", -40.0, fade)
		tw.chain().tween_callback(outgoing.stop)

func play_ambience(name: StringName) -> void:
	if name == _amb_current:
		return
	_amb_current = name
	var path := SFX_DIR + String(name) + ".wav"
	if not ResourceLoader.exists(path):
		path = MUSIC_DIR + String(name) + ".wav"
	if not ResourceLoader.exists(path):
		_amb.stop()
		return
	var st: AudioStream = load(path)
	if st is AudioStreamWAV:
		st.loop_mode = AudioStreamWAV.LOOP_FORWARD
		st.loop_end = int(st.get_length() * st.mix_rate)
	_amb.stream = st
	_amb.volume_db = -30.0
	_amb.play()
	create_tween().tween_property(_amb, "volume_db", -4.0, 2.0)
