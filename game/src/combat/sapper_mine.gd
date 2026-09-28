class_name SapperMine
extends Node3D
## bh-013: a Goblin Sapper's proximity mine. Arms after ARM_TIME, then blows (a short telegraphed blast) when a hero or
## Tempo steps within TRIGGER of it, or on its own after LIFE seconds. Outlives the sapper that planted it. Counts down
## in _physics_process so a paused world pauses it too.

const ARM_TIME := 1.0
const TRIGGER := 1.7
const LIFE := 18.0
const FUSE := 0.4

var req: DamageRequest
var owner_node: Node
var radius := 2.6
var _t := 0.0
var _check := 0.0
var _blowing := false
var _light: OmniLight3D

func setup(p_req: DamageRequest, p_owner: Node, p_radius: float) -> SapperMine:
	req = p_req
	owner_node = p_owner
	radius = p_radius
	name = "SapperMine"
	return self

func _ready() -> void:
	add_to_group(&"sapper_mine")
	var mi := MeshInstance3D.new()
	var cy := CylinderMesh.new()
	cy.top_radius = 0.22
	cy.bottom_radius = 0.28
	cy.height = 0.12
	mi.mesh = cy
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.18, 0.16, 0.14)
	mat.metallic = 0.6
	mat.roughness = 0.5
	mi.material_override = mat
	mi.position.y = 0.06
	add_child(mi)
	var pip := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 0.06
	s.height = 0.12
	pip.mesh = s
	var pm := StandardMaterial3D.new()
	pm.albedo_color = Color(1.0, 0.25, 0.1)
	pm.emission_enabled = true
	pm.emission = Color(1.0, 0.3, 0.1)
	pm.emission_energy_multiplier = 3.0
	pip.material_override = pm
	pip.position.y = 0.16
	add_child(pip)
	_light = OmniLight3D.new()
	_light.light_color = Color(1.0, 0.35, 0.15)
	_light.light_energy = 0.0
	_light.omni_range = 2.0
	_light.position.y = 0.4
	add_child(_light)

func armed() -> bool:
	return _t >= ARM_TIME

func _physics_process(delta: float) -> void:
	if _blowing:
		return
	_t += delta
	if armed():
		_light.light_energy = 0.8 + 0.8 * absf(sin(_t * 6.0))
	if _t >= LIFE:
		blow()
		return
	_check -= delta
	if _check > 0.0 or not armed():
		return
	_check = 0.1
	for g in [&"player", &"tempo", &"net_hero"]:
		for x in get_tree().get_nodes_in_group(g):
			var a := x as Actor
			if a and a.alive and a.global_position.distance_to(global_position) < TRIGGER:
				blow()
				return

func blow() -> void:
	if _blowing:
		return
	_blowing = true
	var at := global_position
	var src: Node = owner_node if owner_node and is_instance_valid(owner_node) else null
	var b := AreaEffects.delayed(FX.world, at, radius, FUSE, req, src, BH.LAYER_PLAYER, Color(1.0, 0.4, 0.1, 0.85))
	b.on_blast = func(pos: Vector3, _h: Array) -> void:
		FX.spawn(VFXLib.ring_wave(Color(1.0, 0.55, 0.2), radius, 0.4), pos)
		FX.spawn(VFXLib.light_flash(Color(1.0, 0.6, 0.3), 6.0, 7.0, 0.3), pos + Vector3.UP)
		Audio.play_at(&"explode", pos)
		Events.camera_shake.emit(0.25)
	Audio.play_at(&"swing_light", at, -6.0)
	get_tree().create_timer(FUSE + 0.05, false).timeout.connect(queue_free)
