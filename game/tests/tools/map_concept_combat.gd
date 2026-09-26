extends "res://tests/tools/combat_bot.gd"
## Reuse the existing combat bot with an isolated review save slot before combat starts.
func _fight_map(id: StringName, seconds: float) -> void:
	Game.save_slot = 98
	await super._fight_map(id, seconds)
