class_name CraftingStation
extends Node3D
## A place to craft (bh-007): an anvil, an alchemy table or a workbench. Interact opens the crafting window on this
## station's recipes. A warm glow, a name plate and a slow icon mote mark it from a distance.

var station: StringName = &"workbench"
var label := ""
var interact_range := 2.6
var _plate: Label3D
var _mote: MeshInstance3D
var _t := 0.0

const COLORS := {&"forge": Color(1.0, 0.55, 0.25), &"alchemy": Color(0.5, 1.0, 0.7), &"workbench": Color(1.0, 0.82, 0.5)}

func setup(p_station: StringName, p_label := "") -> CraftingStation:
	station = p_station
	label = p_label if p_label != "" else String(DataCrafting.STATIONS.get(station, {}).get("name", "Crafting"))
	name = "Station_%s" % station
	return self

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"crafting_station")
	var c: Color = COLORS.get(station, Color(1, 0.8, 0.5))
	var glow := OmniLight3D.new()
	glow.light_color = c
	glow.light_energy = 1.1
	glow.omni_range = 4.0
	glow.position = Vector3(0, 1.6, 0)
	add_child(glow)
	_mote = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.08
	sm.height = 0.16
	_mote.mesh = sm
	_mote.material_override = VFXLib.glow_material(c, 3.0)
	_mote.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mote.position = Vector3(0, 2.1, 0)
	add_child(_mote)
	_plate = Label3D.new()
	_plate.text = "%s\n[%s]" % [label, "Crafting"]
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
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

func _process(delta: float) -> void:
	_t += delta
	_mote.position.y = 2.1 + sin(_t * 1.7) * 0.08
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 8.0

func can_interact(_p: Node) -> bool:
	return not Game.travelling

func interact_text() -> String:
	return "Use the %s" % label

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	Audio.play_ui(&"ui_open" if Audio.has_sound(&"ui_open") else &"ui_click")
	if Game.ui_root and Game.ui_root.has_method(&"open_crafting"):
		Game.ui_root.open_crafting(station, label)
