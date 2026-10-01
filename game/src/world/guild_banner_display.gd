class_name GuildBannerDisplay
extends Node3D
## Your guild's banner (bh-017), hung in the Guild House: the picture the hero uploaded (or their guild's own banner) and
## the name they gave the guild. Interact to change either. Hidden until the hero has joined a guild.
## bh-027: a guild the hero founded is the House's featured guild — the banner hangs larger at the head of the hall with
## the town's plaque beneath it.

const SIZE := Vector2(1.5, 2.25)

var interact_range := 3.0
var _cloth: MeshInstance3D
var _mat: StandardMaterial3D
var _plate: Label3D
var _name: Label3D
var _root: Node3D
var _feature: Label3D

func _ready() -> void:
	add_to_group(&"interactable")
	_root = Node3D.new()
	add_child(_root)
	var rod := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.05
	cm.bottom_radius = 0.05
	cm.height = SIZE.x + 0.5
	rod.mesh = cm
	rod.rotation.z = PI * 0.5
	rod.position = Vector3(0, SIZE.y * 0.5 + 0.08, 0.04)
	rod.material_override = _flat(Color(0.72, 0.55, 0.22), 0.8)
	_root.add_child(rod)
	var back := MeshInstance3D.new()
	var bm := QuadMesh.new()
	bm.size = SIZE + Vector2(0.16, 0.16)
	back.mesh = bm
	back.position = Vector3(0, 0, 0.0)
	back.material_override = _flat(Color(0.16, 0.11, 0.07), 0.0)
	_root.add_child(back)
	_cloth = MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = SIZE
	_cloth.mesh = qm
	_cloth.position = Vector3(0, 0, 0.012)
	_mat = StandardMaterial3D.new()
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_cloth.material_override = _mat
	_root.add_child(_cloth)
	_name = Label3D.new()
	_name.font = UITheme.title_font()
	_name.font_size = 36
	_name.pixel_size = 0.0058
	_name.width = 480.0
	_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_name.modulate = Color(1.0, 0.94, 0.78)
	_name.outline_size = 12
	_name.outline_modulate = Color(0.05, 0.03, 0.02, 0.95)
	_name.position = Vector3(0, -SIZE.y * 0.5 - 0.28, 0.03)
	_root.add_child(_name)
	_plate = Label3D.new()
	_plate.text = "Your guild banner\n[Change name or picture]"
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.position.y = SIZE.y * 0.5 + 0.9
	_plate.visible = false
	add_child(_plate)
	_feature = Label3D.new()
	_feature.font = UITheme.body_bold()
	_feature.font_size = 26
	_feature.pixel_size = 0.0058
	_feature.width = 1000.0
	_feature.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_feature.modulate = Color(1.0, 0.86, 0.5)
	_feature.outline_size = 10
	_feature.outline_modulate = Color(0.05, 0.03, 0.02, 0.95)
	_feature.position = Vector3(0, -SIZE.y * 0.5 - 0.72, 0.04)
	_root.add_child(_feature)
	Events.guild_customised.connect(_refresh)
	Events.guild_changed.connect(_refresh)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _refresh())
	_refresh()

static func _flat(c: Color, metal: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = metal
	m.roughness = 0.6
	return m

func _refresh() -> void:
	var hero := Game.hero
	var on := hero != null and hero.guild != &""
	_root.visible = on
	if not on:
		return
	var tex := GuildRules.banner_or_default(hero)
	_mat.albedo_texture = tex
	_mat.albedo_color = Color.WHITE if tex != null else Color(0.3, 0.3, 0.35)
	_name.text = GuildRules.display_name(hero)
	var featured := hero.guild == GuildRegistry.OWN
	_root.scale = Vector3.ONE * (1.3 if featured else 1.0)
	_feature.visible = featured
	_feature.text = "★ FEATURED GUILD ★\nGuildmaster %s — the town of Malasugue believes you can rescue its hometown heroes, Aljay and Roydo, together with Paul David." % hero.hero_name if featured else ""

## The words under the banner (tests read them).
func feature_text() -> String:
	return _feature.text if _feature and _feature.visible else ""

func _process(_d: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = _root.visible and p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 7.0

func can_interact(_p: Node) -> bool:
	return _root.visible and not Game.travelling

func interact_text() -> String:
	return "Name your guild and choose its banner"

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	if Game.ui_root:
		Game.ui_root.open(&"guild_custom")
