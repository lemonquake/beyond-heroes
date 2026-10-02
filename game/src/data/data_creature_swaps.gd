class_name CreatureSwaps
## bh-033: downloaded CC0 creature models standing in for older ones (provenance: docs/ASSET_SOURCES.md and
## assets_src/bh033/sources.json; converters: tests/tools/convert_creature.gd with assets_src/bh033/creatures/spec_*.json).
## Every enemy that used the old model gets the new one. Delete a line to restore the original model; the old files stay.
const SWAPS := {
	"res://assets/characters/gloomwraith.glb": "res://assets/characters/bh033/gloomwraith_q.scn",   # Quaternius Ghost_Skull
	"res://assets/characters/hive_drone.glb": "res://assets/characters/bh033/hive_drone_q.scn",     # Quaternius Easy Enemy Wasp
	"res://assets/characters/sporeling.glb": "res://assets/characters/bh033/sporeling_q.scn",       # Quaternius Mushnub
}

## The swapped models carry the common creature clips; a boss built on one asks for heavier ones. Those resolve to the
## closest pose the model has (a wind-up reads as an area cast, a roar as the alert rear-up) instead of standing idle.
const CLIP_ALIASES := {
	&"cast_heavy": &"cast_area", &"cast_channel": &"cast_area", &"cast_ultimate": &"cast_area", &"boss_summon": &"cast_area",
	&"boss_slam": &"cast_area", &"boss_sweep": &"cast_area", &"boss_charge": &"run_combat", &"boss_roar": &"alert",
	&"cast_weapon": &"cast_quick", &"war_cry": &"alert", &"taunt": &"alert",
}

## Clip aliases for a model that is swapped (empty when the original model is used).
static func aliases(path: String) -> Dictionary:
	return CLIP_ALIASES if model(path) != path else {}

static func model(path: String) -> String:
	var to: String = SWAPS.get(path, "")
	return to if to != "" and ResourceLoader.exists(to) else path
