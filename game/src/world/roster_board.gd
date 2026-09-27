class_name RosterBoard
extends Node3D
## The hero register board at a camp (bh-007): Interact opens HeroRosterWindow for this map.

var interact_range := 2.6
var _plate: Label3D

func _ready() -> void:
	add_to_group(&"interactable")
	_plate = Label3D.new()
	_plate.text = "Hero Register\n[Levels · Tiers · Guilds]"
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.position.y = 3.0
	_plate.visible = false
	add_child(_plate)
	var glow := OmniLight3D.new()
	glow.light_color = Color(1.0, 0.75, 0.45)
	glow.light_energy = 0.9
	glow.omni_range = 4.0
	glow.position = Vector3(0, 2.2, 0.8)
	add_child(glow)

func _process(_d: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 8.0

func can_interact(_p: Node) -> bool:
	return not Game.travelling

func interact_text() -> String:
	return "Read the Hero Register"

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	if Game.ui_root and Game.ui_root.has_method(&"open_roster"):
		Game.ui_root.open_roster(Game.current_map_id)
