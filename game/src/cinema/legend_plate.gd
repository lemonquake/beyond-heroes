class_name LegendPlate
extends Node3D
## bh-021: the name plate of a legend (Class SX) standing in the world — the name in large letters whose colour and
## outline breathe between the legend's two colours, a light sweeping across them, the Class SX emblem above turning
## slowly and pulsing, the epithet and "Class SX · Lv 251" beneath, and motes of the legend's light drifting up round
## the whole plate. Shown when the hero is near (like every plate). Label3D + Sprite3D + particles: cheap on phones.

var legend_id: StringName
var _name: Label3D
var _sub: Label3D
var _emblem: Sprite3D
var _motes: GPUParticles3D
var _st: Dictionary
var _t := 0.0

static func make(id: StringName, height: float) -> LegendPlate:
	var p := LegendPlate.new()
	p.legend_id = id
	p.position.y = height
	return p

func _ready() -> void:
	var L := DataLegends.legend(legend_id)
	_st = DataLegends.style(StringName(L.get("style", &"storm")))
	_name = Label3D.new()
	_name.text = String(L.get("name", ""))
	_name.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_name.fixed_size = true
	_name.pixel_size = 0.0008
	_name.font = UITheme.title_font()
	_name.font_size = 38
	_name.outline_size = 12
	_name.no_depth_test = true
	_name.render_priority = 9
	_name.outline_render_priority = 8
	add_child(_name)
	_sub = Label3D.new()
	var line := String(L.get("epithet", ""))
	var rl := DataLegends.rank_line(legend_id)
	_sub.text = "%s\n%s" % [line, rl] if rl != "" else line
	_sub.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_sub.fixed_size = true
	_sub.pixel_size = 0.0008
	_sub.font = UITheme.body_bold()
	_sub.font_size = 20
	_sub.outline_size = 8
	_sub.outline_modulate = Color(0, 0, 0, 0.85)
	_sub.no_depth_test = true
	_sub.render_priority = 9
	_sub.offset = Vector2(0, -44)
	_sub.modulate = (_st.hi as Color).lerp(UITheme.PARCHMENT, 0.4)
	add_child(_sub)
	if String(L.get("rank", "")) != "":
		_emblem = Sprite3D.new()
		_emblem.texture = load(DataLegends.SX_EMBLEM)
		_emblem.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_emblem.fixed_size = true
		_emblem.no_depth_test = true
		_emblem.render_priority = 9
		var th := float(_emblem.texture.get_height()) if _emblem.texture else 128.0
		_emblem.pixel_size = 0.0008 * 58.0 / th
		_emblem.offset = Vector2(0, (58.0 + 44.0) * th / 58.0 * 0.5 + th * 0.12)
		add_child(_emblem)
	_motes = GPUParticles3D.new()
	_motes.amount = Perf.particles(24)
	_motes.lifetime = 2.2
	_motes.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.55, 0.12, 0.3)
	pm.direction = Vector3.UP
	pm.spread = 20.0
	pm.initial_velocity_min = 0.15
	pm.initial_velocity_max = 0.4
	pm.gravity = Vector3(0, 0.1, 0)
	pm.scale_min = 0.05
	pm.scale_max = 0.12
	var g := Gradient.new()
	var c: Color = _st.ember
	g.set_color(0, Color(c.r, c.g, c.b, 0.0))
	g.add_point(0.2, Color(c.r, c.g, c.b, 0.9))
	g.set_color(g.get_point_count() - 1, Color(c.r, c.g, c.b, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	_motes.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2.ONE * 0.5
	q.material = VFXLib.particle_material(true)
	_motes.draw_pass_1 = q
	_motes.position.y = -0.25
	add_child(_motes)

func _process(delta: float) -> void:
	if not visible:
		return
	_t += delta
	var a: Color = _st.a
	var b: Color = _st.b
	var hi: Color = _st.hi
	var w := 0.5 + 0.5 * sin(_t * 2.1)
	# a slow light sweep: the name flares toward the highlight colour for a moment every few seconds
	var sweep := pow(maxf(0.0, sin(_t * 0.9)), 18.0)
	_name.modulate = a.lerp(hi, 0.25 + 0.2 * w + 0.55 * sweep)
	_name.outline_modulate = b.lerp(a, 0.35 * w).darkened(0.25)
	if _emblem:
		var s := 1.0 + 0.06 * sin(_t * 3.0) + 0.12 * sweep
		_emblem.scale = Vector3.ONE * s
		_emblem.modulate = Color.WHITE.lerp(hi, 0.3 * w)

func set_shown(v: bool) -> void:
	visible = v
	_motes.emitting = v
