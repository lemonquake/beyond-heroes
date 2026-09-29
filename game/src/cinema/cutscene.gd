class_name Cutscene
extends RefCounted
## bh-021: one cutscene — an ordered list of scenes plus what the story gains when it ends. Subclasses (src/cinema/scenes/)
## override `build` and `finish`. A scene is {"name": String, "length": seconds, "run": Callable(cs: CutscenePlayer)}:
## `run` stages the scene from scratch (world, actors, camera path, lines, effects, timed events), so skipping any
## scene simply starts the next one from its own clean state. `finish` runs exactly once, whether the cutscene played
## through, was skipped scene by scene, or (where allowed) skipped whole.

var id: StringName = &""
var title := ""
## false: the cutscene offers no "Skip all" — only scene-by-scene skipping (the author's rule for the_three).
var skip_all := true
## Music while it plays ("" keeps the map's music).
var music: StringName = &""

func build(_cs: CutscenePlayer) -> Array:
	return []

func finish(_cs: CutscenePlayer) -> void:
	pass
