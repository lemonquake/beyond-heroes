class_name Teleporter
extends Node3D
## A runic waypoint dais that transports the player to a named spawn point on another map.
##
## Data: destination map + spawn, display name, locked state and unlock condition (a world flag on the hero).
## Presentation: rune glow that brightens when discovered/active, idle motes, a light, a hum loop, a charge-up
## beam + flash on use. Discovery registers the teleporter on the hero (for the world-map UI).
## The actual map change goes through `Game.travel`, which shows the loading screen.
## Using it goes through the player's interact system like a door or an NPC (group "interactable"): the R key, a pad
## and the touch Interact button all press the same action the player polls. (It used to listen for a key *event* in
## _unhandled_input, which a touch button never sends — waypoints could not be used on phones, bh-011.)
## Network shrines (DataIsland.NETWORK: the town terrace, the forest glade, Tideglass Cove) also reach every other
## shrine the hero has awakened: with more than one destination, activating asks where to go. "Discovered" (stepped
## on, recorded in unlocked_teleporters even while locked) and "awakened" (a usable network destination) are separate.

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

var interact_range := 2.1
var rune_tint := RUNE_ACTIVE                    # dungeon portals glow in their theme's colour (bh-012)
var dungeon_gate: StringName = &""             # a dungeon's surface gate: also offers every floor the hero has reached                       # flat metres from the dais centre (the dais is 1.3 m across the runes)

var _area: Area3D
var _light: OmniLight3D
var _motes: GPUParticles3D
var _rune_mats: Array[StandardMaterial3D] = []
var _busy := false
var _player_inside: Node3D = null
var _hum: AudioStreamPlayer3D

func _ready() -> void:
	add_to_group(&"teleporter")
	add_to_group(&"interactable")
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
	var c := rune_tint if active else RUNE_LOCKED
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
		Audio.play(&"ui_error", -6.0)

func _on_body_exited(body: Node3D) -> void:
	if body == _player_inside:
		_player_inside = null

func discover() -> void:
	if Game.hero == null:
		return
	var first := not Game.hero.unlocked_teleporters.has(teleporter_id)
	if first:
		Game.hero.unlocked_teleporters[teleporter_id] = true
		Events.teleporter_discovered.emit(Game.current_map_id)
	if is_network() and not is_locked() and not Game.hero.awakened_shrines.has(teleporter_id):
		Game.hero.awakened_shrines[teleporter_id] = true
		Events.notify.emit("Waypoint awakened: %s" % DataIsland.NETWORK[teleporter_id].name, &"discovery")
	elif first:
		Events.notify.emit("Waypoint found. The runes are dark." if is_locked() else "Waypoint awakened", &"discovery")

func is_network() -> bool:
	return DataIsland.NETWORK.has(teleporter_id)

## Where activating can take the hero: this dais's own destination first, then every other awakened network shrine.
func destinations() -> Array:
	var out := []
	if dungeon_gate != &"":
		return DataDungeons.gate_destinations(Game.hero, dungeon_gate)
	if destination_map != &"":
		out.append({"map": destination_map, "spawn": destination_spawn, "name": destination_name})
	if has_meta(&"dungeon_up") and String(destination_map).begins_with("dg_"):
		# deeper floors can also leave the dungeon at once
		var dg: StringName = get_meta(&"dungeon_up")
		var sf: Dictionary = DataDungeons.get_def(dg).get("surface", {})
		if not sf.is_empty():
			out.append({"map": sf.map, "spawn": DataDungeons.gate_id(dg), "name": "Leave the dungeon"})
	if is_network() and Game.hero:
		for id in DataIsland.NETWORK_SHRINES:
			if id == teleporter_id or not Game.hero.awakened_shrines.has(id):
				continue
			var n: Dictionary = DataIsland.NETWORK[id]
			if out.any(func(o): return o.map == n.map and o.spawn == n.spawn):
				continue
			out.append({"map": n.map, "spawn": n.spawn, "name": n.name})
	return out

# ---- Interactable -----------------------------------------------------------------------------------------------

func can_interact(_p: Node) -> bool:
	return not _busy and not is_locked() and destination_map != &"" and not Game.travelling

func interact_text() -> String:
	var dests := destinations()
	if dungeon_gate != &"":
		return "Enter %s" % DataDungeons.get_def(dungeon_gate).get("name", "the dungeon") if dests.size() == 1 else "Descend (%d floors reached)" % dests.size()
	if dests.size() == 1:
		return "Travel to %s" % dests[0].name
	return "Use Waypoint (%d places)" % dests.size()

func interact_anim() -> StringName:
	return &"interact_teleport"

func interact(_p: Node) -> void:
	activate()          # a client's travel becomes a request to the host (Game.travel, bh-011)

## True when activating now would start travel (not locked, not mid-charge, has a destination).
func activate_would_travel() -> bool:
	return not _busy and not is_locked() and destination_map != &""

## Charge up, flash and travel. Returns false when locked or already travelling. A network shrine with several
## destinations asks the hero to choose first (the choice then calls travel_to).
func activate() -> bool:
	if not activate_would_travel():
		return false
	var dests := destinations()
	if dests.size() > 1 and Game.ui_root and Game.ui_root.has_method(&"choose_waypoint"):
		Game.ui_root.choose_waypoint(self, dests)
		return true
	return await travel_to(dests[0].map, dests[0].spawn)

func travel_to(map_id: StringName, spawn: StringName) -> bool:
	if _busy or is_locked():
		return false
	_busy = true
	activated.emit(self)
	Audio.play_at(&"teleport_charge", global_position, -4.0)
	var beam := VFXLib.beam(rune_tint, 6.0, 1.3)
	add_child(beam)
	var tw := create_tween()
	tw.tween_property(_light, "light_energy", 6.0, charge_time)
	for m in _rune_mats:
		tw.parallel().tween_property(m, "emission_energy_multiplier", 12.0, charge_time)
	await tw.finished
	Audio.play_at(&"teleport_whoosh", global_position)
	add_child(VFXLib.light_flash(rune_tint, 10.0, 10.0, 0.4))
	Game.travel(map_id, spawn)
	_busy = false
	return true
