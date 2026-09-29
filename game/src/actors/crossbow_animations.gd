extends RefCounted
## Anatomical two-hand poses: the prod is level and the muzzle points forward.
## Original rig clips remain intact; local additions serve player, Tempo and previews.
const POSES := preload("res://src/actors/crossbow_pose_data.gd").POSES
const SHOTS := preload("res://src/actors/crossbow_pose_data.gd").SHOTS

static func install(player: AnimationPlayer) -> void:
	if not player.has_animation(&"idle_spear") or player.has_animation(&"idle_crossbow"):
		return
	var library := player.get_animation_library(&"")
	if library == null:
		return
	var source := player.get_animation(&"idle_spear")
	library.add_animation(&"idle_crossbow", _pose_clip(source, "ready"))
	library.add_animation(&"crossbow_aim", _pose_clip(source, "aim"))
	library.add_animation(&"crossbow_fire", _shot(source, 0.85, 0.12))
	library.add_animation(&"crossbow_heavy", _shot(source, 1.0, 0.2))

static func _rotation(source: Animation, track: int, bone: String, pose: String) -> Quaternion:
	var values: Dictionary = POSES[pose].rotations
	if not values.has(bone):
		return source.rotation_track_interpolate(track, 0.0)
	var q: Array = values[bone]
	return Quaternion(float(q[0]), float(q[1]), float(q[2]), float(q[3])).normalized()

static func _position(source: Animation, track: int, bone: String, pose: String) -> Vector3:
	if bone == "hips":
		var p: Array = POSES[pose].hips_position
		return Vector3(float(p[0]), float(p[1]), float(p[2]))
	return source.position_track_interpolate(track, 0.0)

static func _pose_clip(source: Animation, pose: String) -> Animation:
	var clip := Animation.new()
	clip.length = 1.6
	clip.loop_mode = Animation.LOOP_LINEAR
	for track in source.get_track_count():
		var type := source.track_get_type(track)
		if type not in [Animation.TYPE_POSITION_3D, Animation.TYPE_ROTATION_3D, Animation.TYPE_SCALE_3D]:
			continue
		var target := clip.add_track(type)
		var path := source.track_get_path(track)
		clip.track_set_path(target, path)
		var bone := String(path.get_subname(0)) if path.get_subname_count() > 0 else ""
		for time in [0.0, clip.length]:
			if type == Animation.TYPE_ROTATION_3D:
				clip.rotation_track_insert_key(target, time, _rotation(source, track, bone, pose))
			elif type == Animation.TYPE_POSITION_3D:
				clip.position_track_insert_key(target, time, _position(source, track, bone, pose))
			else:
				clip.scale_track_insert_key(target, time, source.scale_track_interpolate(track, 0.0))
	return clip

static func _shot(ready: Animation, duration: float, release: float) -> Animation:
	var clip := Animation.new()
	clip.length = duration
	# Re-solve both arms throughout the motion; interpolating only endpoint bone
	# rotations swings the muzzle away from the target midway through a draw.
	var authored: Dictionary = SHOTS["fire" if release < 0.15 else "heavy"]
	var moments: Array = authored.times
	for track in ready.get_track_count():
		var type := ready.track_get_type(track)
		if type not in [Animation.TYPE_POSITION_3D, Animation.TYPE_ROTATION_3D, Animation.TYPE_SCALE_3D]:
			continue
		var target := clip.add_track(type)
		var path := ready.track_get_path(track)
		clip.track_set_path(target, path)
		var bone := String(path.get_subname(0)) if path.get_subname_count() > 0 else ""
		for i in moments.size():
			var frame: Dictionary = authored.frames[i]
			if type == Animation.TYPE_ROTATION_3D:
				var rotation := ready.rotation_track_interpolate(track, 0.0)
				if frame.rotations.has(bone):
					var q: Array = frame.rotations[bone]
					rotation = Quaternion(float(q[0]),float(q[1]),float(q[2]),float(q[3])).normalized()
				clip.rotation_track_insert_key(target, moments[i], rotation)
			elif type == Animation.TYPE_POSITION_3D:
				var position := ready.position_track_interpolate(track, 0.0)
				if bone == "hips":
					var p: Array = frame.hips_position
					position = Vector3(float(p[0]),float(p[1]),float(p[2]))
				clip.position_track_insert_key(target, moments[i], position)
			else:
				clip.scale_track_insert_key(target, moments[i], ready.scale_track_interpolate(track, 0.0))
	return clip
