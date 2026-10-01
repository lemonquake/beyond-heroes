class_name WardPylon
extends Node3D
## bh-029: a pair of ward pylons on the Bridge of Death, fed by one of the three Vaults (DataZarael.BR_PYLONS). While
## that Vault's lord lives the pylons flicker and throw telegraphed lightning at any hero on their stretch of
## the span (STRETCH metres either side): the bridge earns its name. Once the Vault is cleared they burn steady and fall
## silent. The bridge map places the pylon models (`zr_bridge_pylon`) and hands them to setup() for the recolour.

const STRETCH := 40.0
const EVERY := Vector2(2.6, 3.8)       # seconds between strikes while a hero is on the stretch
const RADIUS := 2.5
const DELAY := 1.0                     # telegraph time
const HIT := 0.2                       # of a reference hero's HP at the bridge's level (the lethal-blow guard caps it)

var vault: StringName
var arcs: Array[Vector3] = []          # world positions of the coil tops the bolts leave from
var _models: Array[Node3D] = []
var _light: OmniLight3D
var _t := 2.0
var _rng := RandomNumberGenerator.new()

func setup(p_vault: StringName, models: Array, arc_points: Array) -> WardPylon:
	vault = p_vault
	name = "WardPylon_%s" % vault
	for m in models:
		_models.append(m)
	for a in arc_points:
		arcs.append(a)
	return self

func lit() -> bool:
	return Game.has_flag(DataZarael.VAULT_FLAGS.get(vault, &""))

func _ready() -> void:
	add_to_group(&"ward_pylon")
	_rng.seed = hash(vault)
	_light = OmniLight3D.new()
	_light.omni_range = 18.0
	_light.position = Vector3(0, 12.0, 0)
	add_child(_light)
	_refresh()
	Events.world_flag_set.connect(func(f: StringName, _v: Variant) -> void:
		if f == DataZarael.VAULT_FLAGS.get(vault, &""):
			_refresh())

func _refresh() -> void:
	var gold := lit()
	_light.light_color = Color.WHITE
	_light.light_energy = 2.2 if gold else 3.0
	var from := MaterialLibrary.wire_material(not gold)
	var to := MaterialLibrary.wire_material(gold)
	for m in _models:
		if is_instance_valid(m):
			MaterialLibrary.swap_material(m, from, to)

func _process(delta: float) -> void:
	if lit() or Game.travelling or CutscenePlayer.is_playing():
		return
	var p := Game.player as Node3D
	if p == null or not is_instance_valid(p) or not ("alive" in p) or not p.get("alive"):
		return
	if absf(p.global_position.z - global_position.z) > STRETCH:
		return
	_t -= delta
	if _t > 0.0:
		return
	_t = _rng.randf_range(EVERY.x, EVERY.y)
	_strike(p)

func _strike(p: Node3D) -> void:
	var vel: Vector3 = p.get("velocity") if "velocity" in p else Vector3.ZERO
	var at := p.global_position + Vector3(vel.x, 0.0, vel.z) * 0.45
	var level := Game.current_map.def.level_max if Game.current_map and Game.current_map.def else 44
	var dmg := CombatBudget.hero_hp_ref(level) * HIT
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ENVIRONMENT
	req.base_min = dmg * 0.85
	req.base_max = dmg * 1.15
	req.conversion = {Elements.LIGHTNING: 1.0}
	req.knockback = 5.0
	req.poise = 20.0
	req.graze = true
	req.direct_status = {&"shocked": 40.0}
	req.label = "Ward lightning"
	AreaEffects.delayed(FX.world, at, RADIUS, DELAY, req, null, BH.LAYER_PLAYER, Color(1.0, 1.0, 1.0, 0.8))
	var from := arcs[_rng.randi_range(0, arcs.size() - 1)] if not arcs.is_empty() else global_position + Vector3(0, 14, 0)
	var tw := get_tree().create_timer(DELAY)
	tw.timeout.connect(func() -> void:
		if not is_inside_tree():
			return
		FX.spawn(VFXLib.lightning_bolt(from, at + Vector3(0, 0.2, 0), Color(1.0, 1.0, 1.0), 0.25, 0.18), Vector3.ZERO)
		Audio.play_at(&"thunder_strike", at))
	Audio.play_at(&"arcane_charge", from)
