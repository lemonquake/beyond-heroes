class_name TranscendFlow
extends RefCounted
## Class Transcendence, the game side of one advancement: the change itself (ClassTranscendence.transcend, checked
## against the hero's current state), then the save, the notices, the traits and the profile other players see.
##
## Offline and custom games: the save is written at once through the normal durable path (SaveSystem.save_hero).
## Official characters: the save is queued with the account service and the advancement counts as saved only when the
## service acknowledges a save that contains it; until then the window shows it as waiting, and other players keep
## seeing the previous class (Net.profile_path reads the confirmed save). A failed upload retries on its own.

## The class whose official save is still waiting for the server's acknowledgement (&"" = none).
static var pending: StringName = &""
static var _listening := false

## Advance the current hero into `target`. Returns ClassTranscendence.transcend's result plus "saved" (bool) and
## "pending" (an official save still waiting).
static func advance(target: StringName) -> Dictionary:
	var hero: HeroData = Game.hero
	var res := ClassTranscendence.transcend(hero, target)
	if not res.ok:
		return res
	var name := DataTranscendence.name_of(target)
	Events.class_changed.emit(target)
	if Game.player is Player and is_instance_valid(Game.player):
		var p := Game.player as Player
		p.refresh_class_look()
		p.mark_stats_dirty()
		_celebrate(p, target)
	var skills: Array = []
	for sid in res.skills:
		var s := DB.skill(sid)
		skills.append(s.display_name if s else String(sid))
	var bar_note := "They are on your skill bar." if (res.placed as Array).size() == (res.skills as Array).size() else \
		("Assign the rest from Skills (K)." if not (res.placed as Array).is_empty() else "Your skill bar is full: assign them from Skills (K).")
	Events.notify.emit("You are now a %s. New skills: %s. %s New talents are on the %s page of Talents." % [name, ", ".join(skills), bar_note, name], &"info")
	res["saved"] = false
	res["pending"] = false
	if Official.active:
		pending = target
		res["pending"] = true
		_listen()
		Official.queue_save(hero)
		Events.notify.emit("Saving your new class on the official server…", &"info")
	else:
		var ok := SaveSystem.save_hero(hero, Game.save_slot) if Game.save_slot >= 0 else false
		res["saved"] = ok
		if ok:
			Events.notify.emit("Game saved", &"save")
		else:
			Events.notify.emit("The advancement is done, but the save could not be written now. It will be saved with your next save.", &"error")
		Net.update_profile()
	return res

static func _listen() -> void:
	if _listening:
		return
	_listening = true
	Official.save_finished.connect(_on_official_saved)

## Only a save that contains the new class confirms it (an earlier save still in flight can finish first).
static func _on_official_saved(ok: bool) -> void:
	if pending == &"":
		return
	var saved: Variant = Official._confirmed_save.get("hero", {})
	var path: Array = []
	if saved is Dictionary:
		var tr: Variant = (saved as Dictionary).get("transcendence", {})
		if tr is Dictionary:
			path = (tr as Dictionary).get("path", [])
	if ok and path.map(func(x): return StringName(String(x))).has(pending):
		Events.notify.emit("Your %s advancement is saved on the official server." % DataTranscendence.name_of(pending), &"save")
		pending = &""
		Net.update_profile()
	elif not ok:
		Events.notify.emit("The server has not confirmed your new class yet. The game will try again.", &"error")

## A short, themed burst where the hero stands (no lights or shadows of its own).
static func _celebrate(p: Player, target: StringName) -> void:
	var th := ClassTranscendence.class_theme(target)
	var acc: Color = th.accent
	var prim: Color = th.primary if (th.primary as Color).get_luminance() > 0.3 else acc
	FX.spawn(VFXLib.ring_wave(Color(prim, 0.95), 4.5, 0.9, 0.8), p.global_position)
	FX.spawn(VFXLib.beam_flash(Color(acc.r, acc.g, acc.b), 7.0, 1.0, 1.4), p.global_position)
	FX.spawn(VFXLib.particles(Color(acc, 0.9), 40, 1.4, true, 0.12, 3.0, 50.0, Vector3(0, 2.5, 0), 0.6), p.global_position + Vector3.UP * 0.4)
	FX.text_popup(p.center() + Vector3.UP * 0.9, DataTranscendence.name_of(target), prim.lightened(0.2), 2.0)
	Audio.play_ui(&"level_up")
