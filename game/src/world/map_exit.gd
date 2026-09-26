class_name MapExit
extends Area3D
## A walk-through boundary between two bounded districts (the road out of Malasugue's South Gate, the Forest Road):
## walking into it travels to `destination_map` / `destination_spawn` through the loading screen. The runtime still has
## explicit loading boundaries; the island atlas draws the districts as one continuous geography.
## An optional `require_flag` keeps the exit shut (the barred South Gate) and explains why.

var exit_id: StringName
var destination_map: StringName
var destination_spawn: StringName
var label := ""                        # "Malasugue", "Westreach", "the Ruined Forest"
var require_flag: StringName = &""
var locked_hint := ""
var _armed_at := 0

func setup(p_id: StringName, p_map: StringName, p_spawn: StringName, p_label: String, p_flag := &"", p_hint := "") -> MapExit:
	exit_id = p_id
	destination_map = p_map
	destination_spawn = p_spawn
	label = p_label
	require_flag = p_flag
	locked_hint = p_hint
	name = "Exit_%s" % p_id
	return self

func _ready() -> void:
	collision_layer = BH.LAYER_INTERACT
	collision_mask = BH.LAYER_PLAYER
	monitorable = false
	add_to_group(&"map_exit")
	# a hero placed on a spawn inside the volume (or teleported next to it) must step out and back in to travel
	_armed_at = Time.get_ticks_msec() + 600
	body_entered.connect(_on_body)

func is_open() -> bool:
	return require_flag == &"" or (Game.hero != null and bool(Game.hero.world_flags.get(require_flag, false)))

func _on_body(body: Node3D) -> void:
	if not body.is_in_group(&"player") or Game.travelling or Time.get_ticks_msec() < _armed_at:
		return
	if not is_open():
		if locked_hint != "":
			Events.notify.emit(locked_hint, &"locked")
		return
	Game.travel(destination_map, destination_spawn)
