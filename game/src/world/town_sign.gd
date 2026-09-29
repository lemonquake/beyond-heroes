class_name TownSign
extends Node3D
## A shop sign the way a medieval street has them (bh-017): not a lettered board but the trade's own object - a flask, a
## sword, a ring, an anvil - hung from an iron arm and turning slowly in the breeze, so a hero who cannot read still
## knows a potion seller from a smith. The name of the stand (in the same lettering as the townsfolk's name plates)
## appears when the hero comes within a few steps.

const SHOW_RANGE := 14.0

var model_ref := ""              # "item:<id>" (res://assets/items) or "kit:<name>" (the environment kit) or ""
var title := ""
var sub := ""
var color := Color.WHITE
var target_size := 0.9
var label_height := 1.1
var _holder: Node3D
var _plate: Label3D
var _t := 0.0
var _phase := 0.0
var _always := false

func setup(p_model: String, p_title: String, p_sub: String, p_col: Color, p_size := 0.9, p_always := false) -> TownSign:
	model_ref = p_model
	title = p_title
	sub = p_sub
	color = p_col
	target_size = p_size
	_always = p_always
	name = "Sign_%s" % p_title.replace(" ", "_")
	return self

func _ready() -> void:
	_phase = float(hash(title) % 628) / 100.0
	_holder = Node3D.new()
	add_child(_holder)
	var scene := _scene()
	if scene != null:
		var n: Node3D = scene.instantiate()
		_holder.add_child(n)
		MaterialLibrary.apply_environment(n)
		var bb := _bounds(n, Transform3D.IDENTITY)
		var m := maxf(bb.size.x, maxf(bb.size.y, bb.size.z))
		if m > 0.001:
			n.scale = Vector3.ONE * (target_size / m)
		# centre it on the hook
		n.position = -bb.get_center() * n.scale.x
	_plate = Label3D.new()
	_plate.text = "%s\n[%s]" % [title, sub] if sub != "" else title
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 26 if _always else 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.GOLD.lerp(color, 0.25)
	_plate.position.y = label_height
	_plate.no_depth_test = true
	_plate.visible = _always
	add_child(_plate)

func _scene() -> PackedScene:
	if model_ref.begins_with("item:"):
		var p := "res://assets/items/%s.glb" % model_ref.substr(5)
		return load(p) if ResourceLoader.exists(p) else null
	if model_ref.begins_with("kit:"):
		var p2 := MapBuilder.ENV_DIR % model_ref.substr(4)
		return load(p2) if ResourceLoader.exists(p2) else null
	return null

static func _bounds(n: Node, t: Transform3D) -> AABB:
	var xf := t
	if n is Node3D:
		xf = t * (n as Node3D).transform
	var bb := AABB()
	var first := true
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		bb = xf * (n as MeshInstance3D).mesh.get_aabb()
		first = false
	for c in n.get_children():
		var cb := _bounds(c, xf)
		if cb.size == Vector3.ZERO:
			continue
		bb = cb if first else bb.merge(cb)
		first = false
	return bb

func _process(delta: float) -> void:
	_t += delta
	if _holder:
		_holder.rotation.y = sin(_t * 0.8 + _phase) * 0.55
		_holder.position.y = sin(_t * 1.3 + _phase) * 0.02
	if not _always:
		var p := Game.player as Node3D
		_plate.visible = p != null and is_instance_valid(p) and p.is_inside_tree() and p.global_position.distance_to(global_position) < SHOW_RANGE
