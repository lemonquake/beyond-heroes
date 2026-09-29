class_name VaultPoint
extends Node3D
## bh-019: where a hero opens the Hero's Vault (HeroVault, VaultWindow): in front of the strongroom door of every
## safe town (the `stand_vault` model is placed by TownRowBuilder; this is its interactable part). A soft gold glow
## and a name plate mark it when you come near.

var label := "The Hero's Vault"
var interact_range := 2.6
var _plate: Label3D

func _ready() -> void:
	name = "VaultPoint"
	add_to_group(&"interactable")
	add_to_group(&"vault_point")
	var glow := OmniLight3D.new()
	glow.light_color = Color(1.0, 0.82, 0.45)
	glow.light_energy = 0.9
	glow.omni_range = 3.5
	glow.position = Vector3(0, 1.4, 0)
	add_child(glow)
	_plate = Label3D.new()
	_plate.text = "%s\n[Storage shared by all your heroes]" % label
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.no_depth_test = true
	_plate.render_priority = 8
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.position.y = 2.6
	_plate.visible = false
	add_child(_plate)

func _process(_delta: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 8.0

func can_interact(_p: Node) -> bool:
	return not Game.travelling

func interact_text() -> String:
	return "Open the Vault"

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	Audio.play_ui(&"ui_open" if Audio.has_sound(&"ui_open") else &"ui_click")
	if Game.ui_root:
		Game.ui_root.open(&"vault")
