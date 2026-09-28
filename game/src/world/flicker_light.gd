class_name FlickerLight
extends OmniLight3D
## Fire light with layered-noise flicker (energy + a few cm of positional wobble). Deterministic per light seed so
## neighbouring torches never pulse in sync. Stops animating when far from the camera to save CPU. Shadow casters
## never wobble (bh-014: moving a shadowed light re-renders its shadow map every frame).

@export var base_energy := 1.6
@export var flicker := 0.22          # fraction of base energy
@export var speed := 1.0
@export var wobble := 0.03

var _t := 0.0
var _origin := Vector3.ZERO
var _noise := FastNoiseLite.new()

func _ready() -> void:
	_origin = position
	_noise.seed = int(hash(get_path()) & 0xffff)
	_noise.frequency = 1.0
	_t = float(_noise.seed % 100)
	light_energy = base_energy

func _process(delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam and cam.global_position.distance_squared_to(global_position) > 3600.0:
		return
	_t += delta * speed
	var n := _noise.get_noise_1d(_t * 6.0) * 0.6 + _noise.get_noise_1d(_t * 17.0 + 40.0) * 0.4
	light_energy = base_energy * (1.0 + n * flicker)
	# a light that moves must redraw its whole shadow cube map that frame; energy alone never does (bh-014). Shadowed
	# fires keep the flicker and hold still; the shadowless torches keep their few centimetres of wobble.
	if not shadow_enabled:
		position = _origin + Vector3(_noise.get_noise_1d(_t * 3.0 + 7.0), _noise.get_noise_1d(_t * 3.0 + 13.0) * 0.5,
			_noise.get_noise_1d(_t * 3.0 + 29.0)) * wobble
