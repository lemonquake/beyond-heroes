class_name FlagTrigger
extends Area3D
## Sets a world flag on the hero the first time the player enters (exploration events: "the ritual chamber was
## found", "the seal at the altar was broken"). Flags drive teleporter unlock conditions and are saved.

@export var flag: StringName
@export var message := ""
@export var xp_reward := 0

func _ready() -> void:
	collision_layer = BH.LAYER_INTERACT
	collision_mask = BH.LAYER_PLAYER
	monitorable = false
	body_entered.connect(_on_body)

func _on_body(body: Node3D) -> void:
	if not body.is_in_group(&"player") or Game.hero == null:
		return
	if Game.hero.world_flags.get(flag, false):
		return
	fire()

func fire() -> void:
	if Game.hero:
		Game.hero.world_flags[flag] = true
	if message != "":
		Events.notify.emit(message, &"discovery")
	if xp_reward > 0 and Game.hero:
		var gained := Game.hero.progress.add_xp(xp_reward)
		Events.xp_gained.emit(xp_reward)
		if gained > 0:
			Events.player_leveled.emit(Game.hero.progress.level, gained)
	Audio.play(&"holy_chime", -4.0)
	var map := Game.current_map
	if map:
		map.refresh_teleporters()
		map.apply_flag_visuals(flag, true)
