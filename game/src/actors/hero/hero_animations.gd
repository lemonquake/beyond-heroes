class_name HeroAnimations
extends RefCounted
## Source Blood Ranger motion, fitted to each hero rig and time-warped around
## the existing release timestamp. Simulation still uses the unchanged DB data.

const BOW := "res://assets/characters/roles/blood_ranger_bow.res"
const FIXED := "res://assets/characters/roles/hero_anims_fixed.res"
const BOW_NAMES := {&"idle_bow": &"bow_idle", &"bow_1": &"bow_shoot", &"bow_2": &"bow_shoot",
	&"bow_draw_hold": &"bow_hold", &"bow_release": &"bow_loose"}
const RELEASES := {&"bow_shoot": 0.8, &"bow_loose": 0.07}
static var _bow: AnimationLibrary
static var _fixed: AnimationLibrary
static var _tried := false

static func install(player: AnimationPlayer, sk: Skeleton3D, path: String) -> void:
	if sk == null or not HeroModels.fits(path):
		return
	var library := player.get_animation_library(&"")
	if library == null or library.has_meta(&"woa_bow"):
		return
	if not _tried:
		_tried = true
		_bow = load(BOW) as AnimationLibrary if ResourceLoader.exists(BOW) else null
		_fixed = load(FIXED) as AnimationLibrary if ResourceLoader.exists(FIXED) else null
	# The Hunter scene and Custom hero share hero.glb's animation library. Apply
	# the same source arm repairs to every compatible hero, regardless of which
	# appearance loads first; the selected body must never change another hero's poses.
	if _fixed != null:
		for name in _fixed.get_animation_list():
			if library.has_animation(name):
				_patch(_fixed.get_animation(name), library.get_animation(name))
		var collision_path := HeroModels.DIR + path.get_file().get_basename() + "_collide.res"
		if ResourceLoader.exists(collision_path):
			var collision := load(collision_path) as AnimationLibrary
			for name in collision.get_animation_list():
				if library.has_animation(name):
					_patch(collision.get_animation(name), library.get_animation(name))
	if _bow == null:
		push_error("Blood Ranger bow animations are missing. Run tests/tools/port_hero_animations.gd with the local Warriors of Aether project before playing or exporting; see assets/characters/roles/CREDITS.md.")
		return
	var hips := sk.find_bone("hips")
	if hips < 0:
		return
	var rest := sk.get_bone_rest(hips).origin
	var source_rest: Vector3 = _bow.get_meta("hips_rest", rest)
	var leg_scale := clampf(rest.y / maxf(source_rest.y, 0.01), 0.5, 1.6)
	var prefix := String(player.get_node(player.root_node).get_path_to(sk))
	for target in BOW_NAMES:
		var source: StringName = BOW_NAMES[target]
		var original := _bow.get_animation(source)
		var clip := original.duplicate(true) as Animation
		var meta := DB.anim(target)
		var duration := float(meta.get("length", clip.length))
		var source_release := float(RELEASES.get(source, -1.0))
		var release := float(meta.get("release", -1.0))
		for track in clip.get_track_count():
			var bone := String(clip.track_get_path(track)).get_slice(":", 1)
			clip.track_set_path(track, NodePath(prefix + ":" + bone))
			for key in clip.track_get_key_count(track):
				var time := clip.track_get_key_time(track, key)
				clip.track_set_key_time(track, key, fit_time(time, original.length, duration, source_release, release))
				if clip.track_get_type(track) == Animation.TYPE_POSITION_3D and bone == "hips":
					clip.track_set_key_value(track, key, rest + (clip.track_get_key_value(track, key) as Vector3) * leg_scale)
		clip.length = duration
		clip.loop_mode = Animation.LOOP_LINEAR if bool(meta.get("loop", false)) else Animation.LOOP_NONE
		clip.set_meta("source_clip", source)
		clip.set_meta("source_release", source_release)
		clip.set_meta("release", release)
		if library.has_animation(target):
			library.remove_animation(target)
		library.add_animation(target, clip)
	library.set_meta(&"woa_bow", true)

static func fit_time(time: float, source_length: float, duration: float, source_release: float, release: float) -> float:
	if source_release > 0.0 and release > 0.0:
		if time <= source_release:
			return time * release / source_release
		return release + (time - source_release) * (duration - release) / (source_length - source_release)
	return time * duration / source_length

static func _patch(source: Animation, target: Animation) -> void:
	for st in source.get_track_count():
		var bone := String(source.track_get_path(st)).get_slice(":", 1)
		for dt in target.get_track_count():
			if target.track_get_type(dt) != source.track_get_type(st) or String(target.track_get_path(dt)).get_slice(":", 1) != bone:
				continue
			while target.track_get_key_count(dt) > 0:
				target.track_remove_key(dt, 0)
			for key in source.track_get_key_count(st):
				target.track_insert_key(dt, source.track_get_key_time(st, key), source.track_get_key_value(st, key))
