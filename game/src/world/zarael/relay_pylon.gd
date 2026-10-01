class_name RelayPylon
extends Node3D
## bh-029: one of the three chained relay pylons in the Coilwood (quest "Wire-sick", DataZarael.RELAY_FLAGS). The map
## places the pylon (`zr_relay_pylon`) and the Kharvenn chains (`zr_relay_chains`, hidden by MapBuilder.hide_when once
## this pylon's flag is set); this node is the interactable part. The chain-priests' camp guards it: the chains can
## only be cut once no monster stands within GUARD_RANGE.

const GUARD_RANGE := 14.0
const CUT_TIME := 1.6
const XP := 2500

var index := 1
var interact_range := 3.2
var _plate: Label3D
var _light: OmniLight3D
var _busy := false

func setup(i: int) -> RelayPylon:
	index = i
	name = "RelayPylon_%d" % i
	return self

func flag() -> StringName:
	return DataZarael.RELAY_FLAGS[clampi(index - 1, 0, DataZarael.RELAY_FLAGS.size() - 1)]

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"relay_pylon")
	_light = OmniLight3D.new()
	_light.omni_range = 9.0
	_light.position = Vector3(0, 4.5, 0)
	add_child(_light)
	_plate = Label3D.new()
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
	_plate.position.y = 7.2
	add_child(_plate)
	_refresh()
	Events.world_flag_set.connect(func(f: StringName, _v: Variant) -> void:
		if f == flag():
			_refresh())

func cut() -> bool:
	return Game.has_flag(flag())

func _refresh() -> void:
	var done := cut()
	_light.light_color = Color.WHITE
	_light.light_energy = 1.6 if done else 2.4
	_plate.text = "Relay pylon\n[freed]" if done else "Relay pylon\n[chained by the Kharvenn]"

func _process(_delta: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 14.0

func _guards() -> int:
	var n := 0
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and (e as Enemy).alive and (e as Node3D).global_position.distance_to(global_position) < GUARD_RANGE:
			n += 1
	return n

func can_interact(_p: Node) -> bool:
	return not Game.travelling and not cut() and not _busy

func interact_text() -> String:
	return "Cut the Kharvenn chains"

func interact_anim() -> StringName:
	return &"interact_pickup"

func interact(_p: Node) -> void:
	if cut() or _busy:
		return
	var g := _guards()
	if g > 0:
		Events.notify.emit("The chain-priests' guards are still here (%d). Clear them before you cut the chains." % g, &"warning")
		Audio.play_ui(&"ui_error")
		return
	_busy = true
	Audio.play_at(&"hit_metal_1", global_position)
	FX.spawn(VFXLib.particles(Color(1.0, 1.0, 1.0, 0.9), 26, 0.6, true, 0.4, 3.0, 180.0, Vector3(0, 2, 0), 0.4), global_position + Vector3(0, 2.0, 0))
	await get_tree().create_timer(CUT_TIME).timeout
	if not is_inside_tree():
		return
	Audio.play_at(&"chain_lightning", global_position)
	FX.spawn(VFXLib.ring_wave(Color(1.0, 1.0, 1.0, 0.9), 6.0, 0.7), global_position)
	FX.spawn(VFXLib.particles(Color(1.0, 1.0, 1.0, 0.9), 40, 1.0, true, 0.5, 5.0, 180.0, Vector3(0, 4, 0), 0.6), global_position + Vector3(0, 3.0, 0))
	Game.set_world_flag(flag(), true)
	if Game.hero:
		Game.hero.progress.add_xp(XP)
		Events.xp_gained.emit(XP)
	_busy = false
