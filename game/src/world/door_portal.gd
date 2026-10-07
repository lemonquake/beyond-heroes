class_name DoorPortal
extends Node3D
## A doorway the hero walks through with Interact: into a building interior, or back out to the street. Travel uses
## a short fade (Game.door_travel), not the loading screen. A warm glow and a name plate mark the door.

var destination_map: StringName
var destination_spawn: StringName
var label := ""                     # "the Salted Marlin", "Swordfin Hall", "Malasugue"
var entering := true                # false: this is an exit back outside
var interact_range := 2.4
var plate_at := Vector3(0, 2.7, 0)  # local: a door under a deep arch sets it out in front, clear of the stone
var _plate: Label3D

func setup(p_map: StringName, p_spawn: StringName, p_label: String, p_entering := true) -> DoorPortal:
	destination_map = p_map
	destination_spawn = p_spawn
	label = p_label
	entering = p_entering
	name = "Door_%s_%s" % [p_map, p_spawn]
	return self

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"door")
	var glow := OmniLight3D.new()
	glow.light_color = Color(1.0, 0.7, 0.4)
	glow.light_energy = 0.8
	glow.omni_range = 3.0
	glow.position = Vector3(0, 1.4, 0)
	add_child(glow)
	_plate = Label3D.new()
	_plate.text = label
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.no_depth_test = true          # a lintel or eave in front never cuts the name in half
	_plate.position = plate_at
	_plate.visible = false
	add_child(_plate)

func _process(_d: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 7.0

func can_interact(_p: Node) -> bool:
	return not Game.travelling

func interact_text() -> String:
	return ("Enter %s" % label) if entering else ("Leave for %s" % label)

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	Audio.play_at(&"door_gate", global_position, -4.0)
	Game.door_travel(destination_map, destination_spawn)
