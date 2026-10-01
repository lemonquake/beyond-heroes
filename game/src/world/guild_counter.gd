class_name GuildCounter
extends Node3D
## bh-027: one guild's place in the Guild House — its banner on a carved stand (or hung on the wall), a name plate,
## a lamp in its colour. Interact to read the guild's page (GuildDetailWindow): its banner up close, its words, what it
## grants, and Register / Transfer for the guilds that take members at the counter.
##
## `slot` picks the guild: a fixed id ("swordfin", "npc_2") or "imported:<n>" for the n-th fellow hero's guild the hero
## has met (hidden while there is none).

const SIZE := Vector2(1.3, 1.95)

var slot := "swordfin"
var on_wall := false
var interact_range := 3.0
var _root: Node3D
var _mat: StandardMaterial3D
var _name: Label3D
var _plate: Label3D
var _light: OmniLight3D
var _gid: StringName = &""

func _ready() -> void:
	add_to_group(&"interactable")
	_root = Node3D.new()
	add_child(_root)
	var y := 0.0 if on_wall else 2.35
	if not on_wall:
		for sx in [-1.0, 1.0]:
			var pole := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.045
			cm.bottom_radius = 0.06
			cm.height = 3.4
			pole.mesh = cm
			pole.position = Vector3(sx * (SIZE.x * 0.5 + 0.12), 1.7, 0)
			pole.material_override = _flat(Color(0.28, 0.18, 0.1), 0.0)
			_root.add_child(pole)
	var rod := MeshInstance3D.new()
	var rm := CylinderMesh.new()
	rm.top_radius = 0.04
	rm.bottom_radius = 0.04
	rm.height = SIZE.x + 0.4
	rod.mesh = rm
	rod.rotation.z = PI * 0.5
	rod.position = Vector3(0, y + SIZE.y * 0.5 + 0.06, 0.03)
	rod.material_override = _flat(Color(0.75, 0.57, 0.24), 0.85)
	_root.add_child(rod)
	var cloth := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = SIZE
	cloth.mesh = qm
	cloth.position = Vector3(0, y, 0.02)
	_mat = StandardMaterial3D.new()
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	cloth.material_override = _mat
	_root.add_child(cloth)
	_name = Label3D.new()
	_name.font = UITheme.title_font()
	_name.font_size = 30
	_name.pixel_size = 0.0052
	_name.width = 380.0
	_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_name.outline_size = 10
	_name.outline_modulate = Color(0.05, 0.03, 0.02, 0.95)
	_name.position = Vector3(0, y - SIZE.y * 0.5 - 0.24, 0.05)
	_root.add_child(_name)
	_light = OmniLight3D.new()
	_light.omni_range = 4.0
	_light.light_energy = 0.8
	_light.position = Vector3(0, y + 0.4, 0.9)
	_root.add_child(_light)
	_plate = Label3D.new()
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.position.y = y + SIZE.y * 0.5 + 0.7
	_plate.visible = false
	add_child(_plate)
	Events.guild_changed.connect(_refresh)
	Events.guild_customised.connect(_refresh)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _refresh())
	_refresh()

static func _flat(c: Color, metal: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = metal
	m.roughness = 0.6
	return m

func guild_id() -> StringName:
	return _gid

func _refresh() -> void:
	var hero := Game.hero
	_gid = StringName(slot)
	if slot.begins_with("imported:"):
		_gid = StringName("imp_%d" % int(slot.get_slice(":", 1)))
	var g := GuildRegistry.info(hero, _gid) if hero else {}
	_root.visible = not g.is_empty()
	if g.is_empty():
		return
	_mat.albedo_texture = GuildRegistry.banner(hero, _gid)
	var col: Color = g.color
	_name.text = String(g.name)
	_name.modulate = col.lightened(0.45)
	_light.light_color = col.lightened(0.2)
	var member := hero != null and hero.guild == _gid
	_plate.text = "%s%s\n[Read the guild's terms]" % [String(g.name), "  (your guild)" if member else ""]

func _process(_d: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = _root.visible and p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 6.5

func can_interact(_p: Node) -> bool:
	return _root.visible and not Game.travelling

func interact_text() -> String:
	var g := GuildRegistry.info(Game.hero, _gid)
	return "Read the terms of %s" % String(g.get("name", "the guild"))

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	var hero := Game.hero
	var g := GuildRegistry.info(hero, _gid)
	if g.is_empty() or Game.ui_root == null:
		return
	var w := Game.ui_root.window(&"guild_detail") as GuildDetailWindow
	if w:
		w.show_guild(g, GuildRegistry.banner(hero, _gid))
