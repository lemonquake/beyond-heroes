class_name MapExit
extends Area3D
## A walk-through boundary between two bounded districts (the road out of Malasugue's South Gate, the Forest Road):
## walking into it travels to `destination_map` / `destination_spawn` through the loading screen. The runtime still has
## explicit loading boundaries; the island atlas draws the districts as one continuous geography.
## An optional `require_flag` keeps the exit shut (the barred South Gate) and explains why.
## The threshold shows: a pale band of light on the ground across the road with a thin shimmering veil over it, faint
## from afar and pulsing harder and brighter the nearer the hero walks, plus a "To <place>" plate up close. Every road
## out has its twin on the other side, so the way back glows where the hero arrives.

var exit_id: StringName
var destination_map: StringName
var destination_spawn: StringName
var label := ""                        # "Malasugue", "Westreach", "the Ruined Forest"
var require_flag: StringName = &""
var locked_hint := ""
var _armed_at := 0
var _mats: Array[ShaderMaterial] = []
var _light: OmniLight3D
var _plate: Label3D
var _near := -1.0
var _size := Vector3.ONE
var _open := true

const GLOW_TINT := Color(0.86, 0.9, 1.0)
const NEAR_FAR := 22.0                 # metres from the threshold where the glow starts to wake
const BAND_EXTRA := 5.0                # the ground band reaches this far past the trigger box on each side
static var _ground_shader: Shader
static var _veil_shader: Shader

func setup(p_id: StringName, p_map: StringName, p_spawn: StringName, p_label: String, p_flag := &"", p_hint := "") -> MapExit:
	exit_id = p_id
	destination_map = p_map
	destination_spawn = p_spawn
	label = p_label
	require_flag = p_flag
	locked_hint = p_hint
	name = "Exit_%s" % p_id
	return self

func _ready() -> void:
	collision_layer = BH.LAYER_INTERACT
	collision_mask = BH.LAYER_PLAYER
	monitorable = false
	add_to_group(&"map_exit")
	# a hero placed on a spawn inside the volume (or teleported next to it) must step out and back in to travel
	_armed_at = Time.get_ticks_msec() + 600
	body_entered.connect(_on_body)
	if DisplayServer.get_name() != "headless":
		_build_threshold.call_deferred()

func is_open() -> bool:
	return require_flag == &"" or (Game.hero != null and bool(Game.hero.world_flags.get(require_flag, false)))

func _on_body(body: Node3D) -> void:
	if not body.is_in_group(&"player") or Game.travelling or Time.get_ticks_msec() < _armed_at:
		return
	if not is_open():
		if locked_hint != "":
			Events.notify.emit(locked_hint, &"locked")
		return
	Game.travel(destination_map, destination_spawn)

# ---- the visible threshold ----------------------------------------------------------------------------------------------

func _box() -> Vector3:
	for c in get_children():
		if c is CollisionShape3D and (c as CollisionShape3D).shape is BoxShape3D:
			return ((c as CollisionShape3D).shape as BoxShape3D).size
	return Vector3(4, 4, 2)

## Builds the ground band (draped on whatever ground is under it: terrain, apron, bridge deck), the veil and the light.
## Waits two physics frames so the map's ground bodies are in the space before the rays go down.
func _build_threshold() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame
	if not is_inside_tree():
		return
	_size = _box()
	var along_x := _size.x < _size.z         # the road runs along the box's thin axis
	var long_len := maxf(_size.x, _size.z)
	var depth := minf(_size.x, _size.z) + BAND_EXTRA * 2.0
	# u runs across the road, v along it (the light is the same on both sides, so which way is "out" doesn't matter)
	var out_dir := Vector3(1, 0, 0) if along_x else Vector3(0, 0, 1)
	var c := global_position
	var across_dir := Vector3.UP.cross(out_dir).normalized()
	var space := get_world_3d().direct_space_state
	var nu := clampi(int(long_len / 0.8), 6, 24)
	var nv := clampi(int(depth / 0.8), 6, 20)
	var base := Vector3(c.x, 0, c.z)
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	var floor_y := c.y - _size.y * 0.5          # the road's own height (exit_zone stands the box on the ground)
	for j in nv + 1:
		for i in nu + 1:
			var u := float(i) / nu
			var v := float(j) / nv
			var w := base + across_dir * (u - 0.5) * long_len + out_dir * (v - 0.5) * depth
			var q := PhysicsRayQueryParameters3D.create(Vector3(w.x, c.y + _size.y + 4.0, w.z), Vector3(w.x, c.y - 24.0, w.z), BH.LAYER_GROUND)
			var r := space.intersect_ray(q)
			var gy: float = r.position.y if r else floor_y
			# a cliff or wall beside a cut road: the light stays on the road and dies out before climbing it
			var keep := 1.0 - smoothstep(0.35, 0.8, absf(gy - floor_y))
			verts.append(Vector3(w.x, gy + 0.06, w.z) - c)
			uvs.append(Vector2(u, v))
			cols.append(Color(1, 1, 1, keep))
	var idx := PackedInt32Array()
	for j in nv:
		for i in nu:
			var a := j * (nu + 1) + i
			idx.append_array([a, a + 1, a + nu + 1, a + 1, a + nu + 2, a + nu + 1])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_COLOR] = cols
	arr[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var band := MeshInstance3D.new()
	band.name = "ThresholdBand"
	band.mesh = am
	band.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var gm := ShaderMaterial.new()
	gm.shader = _shader_ground()
	gm.set_shader_parameter(&"tint", GLOW_TINT)
	gm.set_shader_parameter(&"band_depth", depth)
	gm.set_shader_parameter(&"band_width", long_len)
	band.material_override = gm
	add_child(band)
	_mats.append(gm)
	# the veil: a tall thin sheet standing on the threshold line, across the road
	var mid := Vector3(0, verts[(nv / 2) * (nu + 1) + nu / 2].y, 0)
	var vq := QuadMesh.new()
	vq.size = Vector2(long_len, 3.4)
	var veil := MeshInstance3D.new()
	veil.name = "ThresholdVeil"
	veil.mesh = vq
	veil.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	veil.position = mid + Vector3.UP * 1.7
	veil.basis = Basis(across_dir, Vector3.UP, out_dir)
	var vm := ShaderMaterial.new()
	vm.shader = _shader_veil()
	vm.set_shader_parameter(&"tint", GLOW_TINT)
	veil.material_override = vm
	add_child(veil)
	_mats.append(vm)
	_light = OmniLight3D.new()
	_light.light_color = GLOW_TINT
	_light.omni_range = 7.0
	_light.light_energy = 0.0
	_light.shadow_enabled = false
	_light.light_volumetric_fog_energy = 0.0     # lit fog read as a white cloud swallowing the road
	_light.position = mid + Vector3.UP * 1.0
	add_child(_light)
	_plate = Label3D.new()
	_plate.text = "To %s" % label
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.no_depth_test = true
	_plate.position = mid + Vector3.UP * 3.0
	_plate.visible = false
	add_child(_plate)
	_near = -1.0

func _process(_d: float) -> void:
	if _mats.is_empty():
		return
	var open := is_open()
	var near := 0.0
	var pl := Game.player as Node3D
	if open and pl != null and is_instance_valid(pl):
		# distance to the trigger box, not its centre: a wide road reads the same along its whole width
		var local := pl.global_position - global_position
		var half := _size * 0.5
		var outside := Vector3(maxf(absf(local.x) - half.x, 0.0), 0.0, maxf(absf(local.z) - half.z, 0.0))
		near = 1.0 - smoothstep(1.0, NEAR_FAR, outside.length())
	if absf(near - _near) < 0.004 and open == _open:
		return
	_near = near
	_open = open
	for m in _mats:
		m.set_shader_parameter(&"near", near)
		m.set_shader_parameter(&"strength", 1.0 if open else 0.0)
	_light.light_energy = (0.15 + 1.5 * near * near) if open else 0.0
	_plate.visible = open and near > 0.45

static func _shader_ground() -> Shader:
	if _ground_shader == null:
		_ground_shader = Shader.new()
		_ground_shader.code = GROUND_SHADER
	return _ground_shader

static func _shader_veil() -> Shader:
	if _veil_shader == null:
		_veil_shader = Shader.new()
		_veil_shader.code = VEIL_SHADER
	return _veil_shader

const GROUND_SHADER := "
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
uniform vec3 tint : source_color = vec3(0.86, 0.9, 1.0);
uniform float near = 0.0;
uniform float strength = 1.0;
uniform float band_depth = 12.0;
uniform float band_width = 8.0;
uniform float gain = 0.25;           // night scenes are exposed up several times: additive light must start small
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y);
}
void fragment() {
	float x = (UV.x - 0.5) * band_width;            // metres across the road from its middle
	float m = (UV.y - 0.5) * band_depth;            // metres from the threshold line
	float half_w = band_width * 0.5;
	float side = 1.0 - smoothstep(half_w * 0.55, half_w, abs(x));
	float rate = 1.3 + near * 3.2;
	float pulse = 0.6 + 0.4 * sin(TIME * rate);
	// the seam: a thin wavering crack of light across the road
	float wob = (vn(vec2(x * 1.3, TIME * 0.7)) - 0.5) * 0.45;
	float sd = abs(m - wob);
	float seam = (exp(-sd * sd * 30.0) + 0.35 * exp(-sd * sd * 3.0)) * side;
	// ripples run out from the seam's middle in widening arcs, sharper, faster and brighter up close
	float r = length(vec2(x * 0.55, m));
	float reach = band_depth * 0.5;
	float fade = 1.0 - smoothstep(reach * 0.35, reach, r);
	float rings = pow(0.5 + 0.5 * sin(r * 3.2 - TIME * rate * 2.2), 22.0) * fade * side;
	float mist = vn(vec2(x * 1.6 + TIME * 0.15, m * 1.1 - TIME * 0.4)) * fade * side;
	float k = seam * (0.9 + 1.3 * near) * pulse + rings * (0.3 + 0.65 * near) + mist * (0.04 + 0.08 * near);
	ALBEDO = tint * k * gain * strength * COLOR.a;
}
"

const VEIL_SHADER := "
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
uniform vec3 tint : source_color = vec3(0.86, 0.9, 1.0);
uniform float near = 0.0;
uniform float strength = 1.0;
uniform float gain = 0.25;
float h(float x) { return fract(sin(x * 127.1) * 43758.5453); }
float n1(float x) { float i = floor(x); float f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h(i), h(i + 1.0), f); }
void fragment() {
	float across = UV.x;
	float up = 1.0 - UV.y;                         // 0 at the ground, 1 at the top
	float edge = smoothstep(0.0, 0.2, across) * smoothstep(1.0, 0.8, across);
	float fall = pow(1.0 - up, 2.2);
	// thin threads of light rising off the seam, wavering: the air is torn there
	float x = across * 30.0 + sin(up * 4.0 - TIME * 1.1 + across * 9.0) * 0.7;
	float threads = pow(n1(x), 10.0) + 0.6 * pow(n1(x * 2.3 + 17.0), 12.0);
	float flow = 0.4 + 0.6 * pow(0.5 + 0.5 * sin(up * 9.0 - TIME * (1.8 + near * 3.0) + across * 23.0), 3.0);
	float lvl = 0.08 + 1.4 * near * near;
	ALBEDO = tint * edge * fall * strength * lvl * threads * flow * gain;
}
"
