class_name TimedAction
extends RefCounted
## One animation-driven action (attack, cast, skill). Hit windows and release moments come from the animation
## metadata sidecar and are scaled by the playback rate, so damage happens exactly while the weapon visibly
## connects — at any attack speed.

var name: StringName
var anim: StringName
var rate := 1.0
var duration := 0.5
var elapsed := 0.0
var windows: Array = []              # [[start, end], ...] in seconds (already scaled by rate)
var release_t := -1.0                # projectile/spell spawn moment (scaled), -1 = none
var cancel_after := 0.0              # when combos/dodges may interrupt (scaled)
var move_mult := 0.0                 # 0 = rooted during the action
var on_window: Callable              # func(window_index: int, first_frame: bool)
var on_release: Callable             # func()
var on_end: Callable                 # func(completed: bool)
var hit_ids := {}                    # window index -> {instance_id: true}; each target once per window
var released := false
var finished := false
var data := {}                       # free-form payload for the owner

static func from_anim(p_anim: StringName, p_rate: float) -> TimedAction:
	var a := TimedAction.new()
	a.anim = p_anim
	a.name = p_anim
	a.rate = maxf(p_rate, 0.05)
	var meta := DB.anim(p_anim)
	a.duration = float(meta.get("length", 0.7)) / a.rate
	for w in meta.get("hits", []):
		a.windows.append([float(w[0]) / a.rate, float(w[1]) / a.rate])
	if meta.has("release"):
		a.release_t = float(meta["release"]) / a.rate
	elif not a.windows.is_empty():
		a.release_t = a.windows[0][0]
	a.cancel_after = float(meta.get("cancel_after", float(meta.get("length", 0.7)) * 0.75)) / a.rate
	return a

## Advance; returns false once finished.
func step(delta: float) -> bool:
	if finished:
		return false
	var prev := elapsed
	elapsed += delta
	for i in windows.size():
		var w: Array = windows[i]
		if elapsed >= w[0] and prev <= w[1]:
			var first := prev < w[0] or (prev == 0.0 and w[0] == 0.0)
			if on_window.is_valid():
				on_window.call(i, first)
	if not released and release_t >= 0.0 and elapsed >= release_t:
		released = true
		if on_release.is_valid():
			on_release.call()
	if elapsed >= duration:
		finish(true)
		return false
	return true

func finish(completed: bool) -> void:
	if finished:
		return
	finished = true
	if on_end.is_valid():
		on_end.call(completed)

func can_cancel() -> bool:
	return elapsed >= cancel_after

func mark_hit(window: int, target: Object) -> bool:
	## Returns true the first time a target is hit in this window.
	if not hit_ids.has(window):
		hit_ids[window] = {}
	var id := target.get_instance_id()
	if hit_ids[window].has(id):
		return false
	hit_ids[window][id] = true
	return true
