class_name GuildHallBanner
extends Node3D
## bh-027: the great banner outside the Guild House. Once the hero joins a guild or founds one, their guild's banner
## flies here — 4 m wide and 6 m long between two 9 m poles, rippling in the wind — with the guild's name across the
## top and its motto across the foot (painted into the cloth, so the words ripple with it). Hidden while the hero has no
## guild.

const CLOTH := Vector2(3.6, 4.8)
const POLE_H := 6.2
const TEX := Vector2i(512, 768)

const SHADER := """
shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha;
uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_disable;
uniform float wind = 1.0;
varying float shade;
void vertex() {
	float hang = UV.y;                                   // 0 at the rod, 1 at the foot
	float t = TIME;
	float a = UV.x * 5.0 + t * 2.1 + UV.y * 1.7;
	float w = sin(a) * 0.22 + sin(UV.x * 11.0 - t * 3.3 + UV.y * 4.0) * 0.07;
	VERTEX.z += w * hang * wind;
	VERTEX.x += sin(t * 0.9 + UV.y * 3.0) * 0.06 * hang * wind;
	shade = 0.8 + 0.2 * cos(a);
}
void fragment() {
	vec4 c = texture(tex, UV);
	if (c.a < 0.5) {
		discard;
	}
	ALBEDO = c.rgb * shade;
	ROUGHNESS = 0.92;
	EMISSION = c.rgb * 0.28;                             // readable by lamplight at night
}
"""

var _root: Node3D
var _vp: SubViewport
var _art: TextureRect
var _title: Label
var _motto: Label
var _mat: ShaderMaterial
var _key := ""

func _ready() -> void:
	add_to_group(&"guild_hall_banner")
	_root = Node3D.new()
	add_child(_root)
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color(0.24, 0.15, 0.08)
	wood.roughness = 0.8
	var brass := StandardMaterial3D.new()
	brass.albedo_color = Color(0.82, 0.62, 0.26)
	brass.metallic = 0.9
	brass.roughness = 0.35
	for sx in [-1.0, 1.0]:
		var pole := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.09
		cm.bottom_radius = 0.13
		cm.height = POLE_H
		pole.mesh = cm
		pole.material_override = wood
		pole.position = Vector3(sx * (CLOTH.x * 0.5 + 0.3), POLE_H * 0.5, 0)
		_root.add_child(pole)
		var cap := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.2
		sm.height = 0.4
		cap.mesh = sm
		cap.material_override = brass
		cap.position = Vector3(pole.position.x, POLE_H + 0.12, 0)
		_root.add_child(cap)
		var foot := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.6, 0.35, 0.6)
		foot.mesh = bm
		foot.material_override = wood
		foot.position = Vector3(pole.position.x, 0.17, 0)
		_root.add_child(foot)
		var body := StaticBody3D.new()
		body.collision_layer = BH.LAYER_PROPS
		var cs := CollisionShape3D.new()
		var cyl := CylinderShape3D.new()
		cyl.radius = 0.3
		cyl.height = 3.0
		cs.shape = cyl
		cs.position = Vector3(pole.position.x, 1.5, 0)
		body.add_child(cs)
		_root.add_child(body)
	var bar := MeshInstance3D.new()
	var bcm := CylinderMesh.new()
	bcm.top_radius = 0.07
	bcm.bottom_radius = 0.07
	bcm.height = CLOTH.x + 0.9
	bar.mesh = bcm
	bar.rotation.z = PI * 0.5
	bar.material_override = brass
	bar.position = Vector3(0, POLE_H - 0.6, 0.05)
	_root.add_child(bar)
	# the cloth: a finely divided sheet hanging from the bar, its words painted in a little viewport
	_vp = SubViewport.new()
	_vp.size = TEX
	_vp.transparent_bg = true
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(_vp)
	var c := Control.new()
	c.size = Vector2(TEX)
	_vp.add_child(c)
	_art = TextureRect.new()
	_art.size = Vector2(TEX)
	_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_art.stretch_mode = TextureRect.STRETCH_SCALE
	c.add_child(_art)
	_title = _cloth_label(54, Vector2(24, 26), Vector2(TEX.x - 48, 150))
	c.add_child(_title)
	_motto = _cloth_label(30, Vector2(40, TEX.y - 270), Vector2(TEX.x - 80, 110))
	c.add_child(_motto)
	var sheet := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = CLOTH
	pm.orientation = PlaneMesh.FACE_Z
	pm.subdivide_width = 24
	pm.subdivide_depth = 36
	sheet.mesh = pm
	sheet.position = Vector3(0, POLE_H - 0.6 - CLOTH.y * 0.5, 0.1)
	_mat = ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = SHADER
	_mat.shader = sh
	_mat.set_shader_parameter("tex", _vp.get_texture())
	sheet.material_override = _mat
	sheet.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	_root.add_child(sheet)
	var lamp := OmniLight3D.new()
	lamp.light_color = Color(1.0, 0.82, 0.55)
	lamp.light_energy = 1.6
	lamp.omni_range = 9.0
	lamp.position = Vector3(0, 3.0, 3.0)
	_root.add_child(lamp)
	Events.guild_customised.connect(_refresh)
	Events.guild_changed.connect(_refresh)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _refresh())
	_refresh()

func _cloth_label(size: int, pos: Vector2, box: Vector2) -> Label:
	var l := Label.new()
	l.position = pos
	l.size = box
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", UITheme.title_font())
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color(1.0, 0.93, 0.74))
	l.add_theme_color_override("font_outline_color", Color(0.06, 0.035, 0.02, 1.0))
	l.add_theme_constant_override("outline_size", 14)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	l.add_theme_constant_override("shadow_offset_y", 4)
	return l

## Is the banner flying (the hero belongs to a guild)?
func flying() -> bool:
	return _root.visible

func shown_name() -> String:
	return _title.text

func _refresh() -> void:
	var hero := Game.hero
	var on := hero != null and hero.guild != &""
	_root.visible = on
	if not on:
		return
	var g := GuildRegistry.info(hero, hero.guild)
	var tex := GuildRegistry.banner(hero, hero.guild)
	var key := "%s|%s|%s" % [GuildRules.display_name(hero), g.get("motto", ""), tex.get_rid() if tex else ""]
	if key == _key:
		return
	_key = key
	_art.texture = tex
	_title.text = GuildRules.display_name(hero).to_upper()
	_motto.text = String(g.get("motto", ""))
	_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
