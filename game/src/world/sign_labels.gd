class_name SignLabels
extends Node3D
## The painted names on a signpost's arms, as native text: readable at the isometric camera's distance and shown only
## while the hero is close enough to read them.

const SHOW_RANGE := 16.0
var _arms: Array = []           # [text, local position]
var _labels: Array[Label3D] = []
var _t := 0.0

func add_arm(text: String, pos: Vector3) -> void:
	_arms.append([text, pos])

func _ready() -> void:
	add_to_group(&"signpost")
	for a in _arms:
		var l := Label3D.new()
		l.text = a[0]
		l.position = a[1]
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		l.fixed_size = true
		l.pixel_size = 0.0008
		l.font = UITheme.body_bold()
		l.font_size = 24
		l.outline_size = 8
		l.outline_modulate = Color(0.05, 0.03, 0.02, 0.9)
		l.modulate = UITheme.PARCHMENT
		l.visible = false
		add_child(l)
		_labels.append(l)

func arm_texts() -> Array:
	return _arms.map(func(a): return a[0])

func _process(delta: float) -> void:
	_t -= delta
	if _t > 0.0:
		return
	_t = 0.25
	var p := Game.player as Node3D
	var near := p != null and is_instance_valid(p) and p.is_inside_tree() and p.global_position.distance_to(global_position) < SHOW_RANGE
	for l in _labels:
		l.visible = near
