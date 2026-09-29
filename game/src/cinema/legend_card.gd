class_name LegendCard
extends Control
## bh-021: the name card that slams in when a legend is introduced in a cutscene — a dark band across the lower third,
## the epithet, the name in huge letters burning in the legend's colours (a shader: flame noise, a light sweep), the
## Class SX emblem shimmering, the level, and embers drifting up through it all. Plays itself and frees itself.
##   LegendCard.show_card(parent, &"aljay", 4.6)

const NAME_SHADER := """
shader_type canvas_item;
uniform vec4 c_a : source_color = vec4(1.0, 0.2, 0.1, 1.0);
uniform vec4 c_b : source_color = vec4(0.3, 0.0, 0.0, 1.0);
uniform vec4 c_hi : source_color = vec4(1.0, 0.9, 0.7, 1.0);
uniform vec2 size = vec2(800.0, 160.0);
uniform float sweep = -1.0;
uniform float flash = 0.0;
varying vec2 lp;
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
void vertex() { lp = VERTEX; }
void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	vec2 l = lp / max(size, vec2(1.0));
	float fl = n(vec2(l.x * 14.0, l.y * 5.0 + TIME * 2.2)) * 0.6 + n(vec2(l.x * 31.0, l.y * 11.0 + TIME * 3.7)) * 0.4;
	float g = clamp(1.0 - l.y + (fl - 0.5) * 0.55, 0.0, 1.0);
	vec3 c = mix(c_b.rgb, c_a.rgb, g);
	c = mix(c, c_hi.rgb, smoothstep(0.62, 1.0, g) * 0.55);
	float sw = exp(-pow((l.x - sweep) * 7.0 - l.y * 1.5, 2.0));
	c += c_hi.rgb * sw * 1.2 + vec3(flash);
	COLOR = vec4(c * COLOR.rgb, tex.a * COLOR.a);
}
"""

const EMBLEM_SHADER := """
shader_type canvas_item;
uniform float sweep = -1.0;
uniform vec4 glow : source_color = vec4(1.0, 0.3, 0.1, 1.0);
void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float sw = exp(-pow((UV.x + UV.y * 0.6 - sweep) * 6.0, 2.0));
	float pulse = 0.85 + 0.15 * sin(TIME * 4.0);
	COLOR = vec4(t.rgb * pulse + glow.rgb * sw * 0.9, t.a * COLOR.a);
}
"""

var legend_id: StringName
var life := 4.6
var _t := 0.0
var _band: TextureRect
var _epithet: Label
var _name: Label
var _rank: HBoxContainer
var _emblem: TextureRect
var _slash: ColorRect
var _embers: GPUParticles2D
var _name_mat: ShaderMaterial
var _emb_mat: ShaderMaterial
var _st: Dictionary

static func show_card(parent: Node, id: StringName, p_life := 4.6) -> LegendCard:
	var c := LegendCard.new()
	c.legend_id = id
	c.life = p_life
	parent.add_child(c)
	return c

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS
	var L := DataLegends.legend(legend_id)
	_st = DataLegends.style(StringName(L.get("style", &"holy")))
	var vs := get_viewport_rect().size
	var k := vs.y / 1080.0
	# the band
	_band = TextureRect.new()
	var g := Gradient.new()
	g.set_color(0, Color(0, 0, 0, 0))
	g.add_point(0.18, Color(0, 0, 0, 0.72))
	g.add_point(0.62, Color(0, 0, 0, 0.55))
	g.set_color(g.get_point_count() - 1, Color(0, 0, 0, 0))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.width = 256
	gt.height = 8
	_band.texture = gt
	_band.stretch_mode = TextureRect.STRETCH_SCALE
	_band.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_band.position = Vector2(0, vs.y * 0.56)
	_band.size = Vector2(vs.x, vs.y * 0.3)
	_band.modulate.a = 0.0
	add_child(_band)
	# a tinted glow under the name
	var gl := TextureRect.new()
	gl.texture = VFXLib.soft_texture()
	gl.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	gl.stretch_mode = TextureRect.STRETCH_SCALE
	gl.position = Vector2(vs.x * 0.02, vs.y * 0.6)
	gl.size = Vector2(vs.x * 0.55, vs.y * 0.22)
	gl.modulate = Color(_st.glow.r, _st.glow.g, _st.glow.b, 0.35)
	_band.add_child(gl)
	gl.position -= _band.position
	var x0 := vs.x * 0.075
	_epithet = _label(String(L.get("epithet", "")).to_upper(), int(34 * k), _st.a.lerp(Color.WHITE, 0.35), UITheme.title_font())
	_epithet.add_theme_constant_override("outline_size", int(6 * k))
	_epithet.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	_epithet.position = Vector2(x0 - 80 * k, vs.y * 0.605)
	_epithet.modulate.a = 0.0
	add_child(_epithet)
	_name = _label(String(L.get("name", "")).to_upper(), int(150 * k), Color.WHITE, UITheme.title_font())
	_name.add_theme_constant_override("outline_size", int(14 * k))
	_name.add_theme_color_override("font_outline_color", Color(0.02, 0.0, 0.0, 0.9))
	_name.position = Vector2(x0, vs.y * 0.64)
	_name.modulate.a = 0.0
	_name_mat = ShaderMaterial.new()
	_name_mat.shader = _shader(NAME_SHADER)
	_name_mat.set_shader_parameter("c_a", _st.a)
	_name_mat.set_shader_parameter("c_b", _st.b)
	_name_mat.set_shader_parameter("c_hi", _st.hi)
	_name.material = _name_mat
	add_child(_name)
	_slash = ColorRect.new()
	_slash.color = _st.hi
	_slash.position = Vector2(x0, vs.y * 0.64 + 168 * k)
	_slash.size = Vector2(0, 3 * k)
	add_child(_slash)
	_rank = HBoxContainer.new()
	_rank.add_theme_constant_override("separation", int(16 * k))
	_rank.position = Vector2(x0, vs.y * 0.64 + 182 * k)
	_rank.modulate.a = 0.0
	add_child(_rank)
	if String(L.get("rank", "")) != "":
		_emblem = TextureRect.new()
		_emblem.texture = load(DataLegends.SX_EMBLEM)
		_emblem.custom_minimum_size = Vector2(74, 74) * k
		_emblem.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_emblem.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		_emb_mat = ShaderMaterial.new()
		_emb_mat.shader = _shader(EMBLEM_SHADER)
		_emb_mat.set_shader_parameter("glow", _st.glow)
		_emblem.material = _emb_mat
		_rank.add_child(_emblem)
		var cls := _label("CLASS %s" % L.rank, int(46 * k), _st.hi, UITheme.title_font())
		cls.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_rank.add_child(cls)
		var sub := _label("·  %s  ·" % DataLegends.SX_TITLE.to_upper(), int(26 * k), _st.a.lerp(Color.WHITE, 0.4), UITheme.title_font())
		sub.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_rank.add_child(sub)
	if int(L.get("level", 0)) > 0:
		var lv := _label("LV %d" % int(L.level), int(46 * k), _st.hi, UITheme.title_font())
		lv.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_rank.add_child(lv)
	for c in _rank.get_children():
		if c is Label:
			(c as Label).add_theme_constant_override("outline_size", int(6 * k))
			(c as Label).add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	_embers = GPUParticles2D.new()
	_embers.amount = 70
	_embers.lifetime = 2.6
	_embers.position = Vector2(vs.x * 0.3, vs.y * 0.88)
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(vs.x * 0.3, 20, 0)
	pm.direction = Vector3(0.2, -1, 0)
	pm.spread = 25.0
	pm.initial_velocity_min = 60.0 * k
	pm.initial_velocity_max = 180.0 * k
	pm.gravity = Vector3(0, -30, 0)
	pm.scale_min = 2.0 * k
	pm.scale_max = 5.0 * k
	pm.turbulence_enabled = true
	pm.turbulence_noise_strength = 3.0
	var cg := Gradient.new()
	cg.set_color(0, Color(_st.ember.r, _st.ember.g, _st.ember.b, 0.0))
	cg.add_point(0.15, Color(_st.ember.r, _st.ember.g, _st.ember.b, 1.0))
	cg.set_color(cg.get_point_count() - 1, Color(_st.ember.r, _st.ember.g, _st.ember.b, 0.0))
	var cgt := GradientTexture1D.new()
	cgt.gradient = cg
	pm.color_ramp = cgt
	_embers.process_material = pm
	var pt := GradientTexture2D.new()
	var pg := Gradient.new()
	pg.set_color(0, Color.WHITE)
	pg.set_color(1, Color(1, 1, 1, 0))
	pt.gradient = pg
	pt.fill = GradientTexture2D.FILL_RADIAL
	pt.fill_from = Vector2(0.5, 0.5)
	pt.fill_to = Vector2(1.0, 0.5)
	pt.width = 16
	pt.height = 16
	_embers.texture = pt
	var cm := CanvasItemMaterial.new()
	cm.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_embers.material = cm
	add_child(_embers)
	move_child(_embers, 1)
	Audio.play(&"boss_phase", -4.0, 0.0)

static var _shaders := {}

static func _shader(code: String) -> Shader:
	if not _shaders.has(code):
		var s := Shader.new()
		s.code = code
		_shaders[code] = s
	return _shaders[code]

func _label(text: String, size: int, col: Color, font: Font) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	return l

func _process(delta: float) -> void:
	_t += delta
	var vs := get_viewport_rect().size
	var k := vs.y / 1080.0
	var t := _t
	_band.modulate.a = clampf(t / 0.3, 0.0, 1.0)
	var ep := clampf((t - 0.1) / 0.45, 0.0, 1.0)
	_epithet.modulate.a = ep
	_epithet.position.x = vs.x * 0.075 - 80.0 * k * (1.0 - _ease(ep))
	var nm := clampf((t - 0.3) / 0.22, 0.0, 1.0)
	_name.modulate.a = nm
	var s := 1.0 + 0.3 * (1.0 - _ease(nm))
	_name.pivot_offset = _name.size * Vector2(0.1, 0.5)
	_name.scale = Vector2(s, s)
	_name_mat.set_shader_parameter("flash", maxf(0.0, 1.0 - (t - 0.45) * 3.0) * float(t > 0.4))
	_name_mat.set_shader_parameter("size", _name.size)
	_name_mat.set_shader_parameter("sweep", (t - 0.8) * 0.9 - 0.2)
	_slash.size.x = vs.x * 0.5 * _ease(clampf((t - 0.45) / 0.4, 0.0, 1.0))
	_rank.modulate.a = clampf((t - 0.75) / 0.35, 0.0, 1.0)
	if _emb_mat:
		_emb_mat.set_shader_parameter("sweep", fmod(t * 0.8, 2.4) - 0.4)
	var out := clampf((life - t) / 0.55, 0.0, 1.0)
	modulate.a = out
	if t >= life:
		queue_free()

func _ease(x: float) -> float:
	return 1.0 - pow(1.0 - x, 3.0)

## End early (a skipped scene).
func dismiss() -> void:
	life = minf(life, _t + 0.3)
