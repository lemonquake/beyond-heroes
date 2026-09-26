class_name Teleporter
extends Node3D
## A runic waypoint dais that transports the player to a named spawn point on another map.
##
## Data: destination map + spawn, display name, locked state and unlock condition (a world flag on the hero).
## Presentation: rune glow that brightens when discovered/active, idle motes, a light, a hum loop, a charge-up
## beam + flash on use. Discovery registers the teleporter on the hero (for the world-map UI).
## The actual map change goes through `Game.travel`, which shows the loading screen.

signal activated(teleporter: Teleporter)

@export var teleporter_id: StringName
@export var destination_map: StringName
@export var destination_spawn: StringName = &"start"
@export var destination_name := ""
@export var locked := false
@export var unlock_flag: StringName = &""       # hero.world_flags key that unlocks this teleporter
@export var locked_hint := "The runes are dark."
@export var charge_time := 0.9

const RUNE_ACTIVE := Color(0.35, 0.85, 1.0)
const RUNE_LOCKED := Color(0.35, 0.3, 0.45)

var _area: Area3D
var _light: OmniLight3D
var _motes: GPUParticles3D
var _rune_mats: Array[StandardMaterial3D] = []
var _busy := false
var _player_inside: Node3D = null
var _hum: AudioStreamPlayer3D

func _ready() -> void:
	add_to_group(&"teleporter")
	_build()
	refresh_state()

func _build() -> void:
	var scene: PackedScene = load("res://assets/environment/teleporter_platform.glb")
	var vis := scene.instantiate()
	add_child(vis)
	MaterialLibrary.apply_environment(vis)
	# Runes get a private material so this teleporter's glow can change independently of others.
	for mi in _meshes(vis):
		for i in mi.mesh.get_surface_count():
			var cur := mi.get_active_material(i)
			if cur and cur.resource_name == "BH_Rune":
				var m: StandardMaterial3D = cur.duplicate()
				mi.set_surface_override_material(i, m)
				_rune_mats.append(m)
	_light = OmniLight3D.new()
	_light.position = Vector3(0, 1.6, 0)
	_light.omni_range = 7.0
	_light.shadow_enabled = false
	add_child(_light)
	_motes = VFXLib.particles(Color(0.45, 0.85, 1.0, 0.8), 24, 2.4, false, 0.18, 0.5, 25.0, Vector3(0, 0.6, 0), 1.2)
	_motes.position = Vector3(0, 0.6, 0)
	add_child(_motes)
	_area = Area3D.new()
	_area.collision_layer = BH.LAYER_INTERACT
	_area.collision_mask = BH.LAYER_PLAYER
	_area.monitorable = false
	var cs := CollisionShape3D.new()
	var shape := CylinderShape3D.new()
	shape.radius = 1.3
	shape.height = 2.5
	cs.shape = shape
	cs.position = Vector3(0, 1.4, 0)
	_area.add_child(cs)
	add_child(_area)
	_area.body_entered.connect(_on_body_entered)
	_area.body_exited.connect(_on_body_exited)
	if Audio.has_sound(&"teleporter_hum"):
		_hum = Audio.make_loop(&"teleporter_hum", self, -14.0, 10.0)

static func _meshes(n: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if n is MeshInstance3D and n.mesh:
		out.append(n)
	for c in n.get_children():
		out.append_array(_meshes(c))
	return out

## The spot the player should stand on / appear at when arriving *at this teleporter's own map*.
func arrival_point() -> Vector3:
	return global_position + Vector3(0, 0.47, 0)

func is_locked() -> bool:
	if not locked:
		return false
	if unlock_flag != &"" and Game.hero and Game.hero.world_flags.get(unlock_flag, false):
		return false
	return true

func refresh_state() -> void:
	var active := not is_locked()
	var c := RUNE_ACTIVE if active else RUNE_LOCKED
	for m in _rune_mats:
		m.emission = c
		m.albedo_color = c
		m.emission_energy_multiplier = 4.0 if active else 0.6
	if _light:
		_light.light_color = c
		_light.light_energy = 1.4 if active else 0.25
	if _motes:
		_motes.emitting = active
	if _hum:
		_hum.volume_db = -14.0 if active else -40.0

func _on_body_entered(body: Node3D) -> void:
	if not body.is_in_group(&"player"):
		return
	_player_inside = body
	discover()
	refresh_state()
	if is_locked():
		Events.notify.emit(locked_hint, &"locked")
		Events.interact_prompt.emit("")
		Audio.play(&"ui_error", -6.0)
		return
	Events.interact_prompt.emit("Travel to %s" % destination_name)

func _on_body_exited(body: Node3D) -> void:
	if body == _player_inside:
		_player_inside = null
		Events.interact_prompt.emit("")

func discover() -> void:
	if Game.hero and not Game.hero.unlocked_teleporters.has(teleporter_id):
		Game.hero.unlocked_teleporters[teleporter_id] = true
		Events.teleporter_discovered.emit(Game.current_map_id)
		Events.notify.emit("Waypoint awakened", &"discovery")

func _unhandled_input(event: InputEvent) -> void:
	if _player_inside and event.is_action_pressed(&"interact"):
		activate()
		get_viewport().set_input_as_handled()

## True when activating now would start travel (not locked, not mid-charge, has a destination).
func activate_would_travel() -> bool:
	return not _busy and not is_locked() and destination_map != &""

## Charge up, flash and travel. Returns false when locked or already travelling.
func activate() -> bool:
	if not activate_would_travel():
		return false
	_busy = true
	activated.emit(self)
	Audio.play_at(&"teleport_charge", global_position, -4.0)
	var beam := VFXLib.beam(RUNE_ACTIVE, 6.0, 1.3)
	add_child(beam)
	var tw := create_tween()
	tw.tween_property(_light, "light_energy", 6.0, charge_time)
	for m in _rune_mats:
		tw.parallel().tween_property(m, "emission_energy_multiplier", 12.0, charge_time)
	await tw.finished
	Audio.play_at(&"teleport_whoosh", global_position)
	add_child(VFXLib.light_flash(RUNE_ACTIVE, 10.0, 10.0, 0.4))
	Game.travel(destination_map, destination_spawn)
	_busy = false
	return true
