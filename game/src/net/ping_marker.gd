class_name PingMarker
extends Node3D
## A party ping (bh-011): a beam of the pinging player's colour with a pulsing ground ring and their name, seen by
## everyone on the map for a few seconds, then it fades. Pure presentation (no collision, no gameplay).

var _life := 5.0
var _t := 0.0
var _col := Color.WHITE
var _beam_mat: StandardMaterial3D
var _ring: MeshInstance3D
var _ring_mat: StandardMaterial3D
var _label: Label3D

func setup(who: String, col: Color, life: float) -> void:
	_col = col
	_life = life
	name = "Ping"
	_beam_mat = _unshaded(Color(col, 0.55))
	var beam := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.03
	cyl.bottom_radius = 0.14
	cyl.height = 4.0
	cyl.radial_segments = 12
	cyl.rings = 1
	beam.mesh = cyl
	beam.material_override = _beam_mat
	beam.position.y = 2.0
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(beam)
	_ring = MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.8
	tm.outer_radius = 1.0
	tm.rings = 36
	tm.ring_segments = 6
	_ring.mesh = tm
	_ring_mat = _unshaded(Color(col, 0.9))
	_ring.material_override = _ring_mat
	_ring.scale = Vector3(1, 0.12, 1)
	_ring.position.y = 0.08
	_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_ring)
	_label = Label3D.new()
	_label.text = "◆ %s" % who
	_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_label.no_depth_test = true
	_label.fixed_size = true
	_label.pixel_size = 0.0007
	_label.font_size = 30
	_label.outline_size = 12
	_label.modulate = col.lightened(0.3)
	_label.outline_modulate = Color(0.05, 0.03, 0.02, 0.95)
	_label.position.y = 4.4
	add_child(_label)

static func _unshaded(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = c
	m.no_depth_test = false
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m

func _process(delta: float) -> void:
	_t += delta
	var fade := clampf((_life - _t) / 0.8, 0.0, 1.0)
	var pulse := fmod(_t * 1.4, 1.0)
	if _ring:
		_ring.scale = Vector3(0.6 + pulse * 1.6, 0.12, 0.6 + pulse * 1.6)
		_ring_mat.albedo_color = Color(_col, (1.0 - pulse) * 0.9 * fade)
	if _beam_mat:
		_beam_mat.albedo_color = Color(_col, (0.45 + 0.15 * sin(_t * 8.0)) * fade)
	if _label:
		_label.modulate.a = fade
	if _t >= _life:
		queue_free()
