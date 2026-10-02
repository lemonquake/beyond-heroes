class_name PortraitStudio
extends RefCounted
## bh-031: ID portraits of characters on the hero body: head and shoulders, front-lit, on a warm vignette. Used to
## bake every townsperson's dialogue portrait (tests/tools/bake_portraits.tscn) and, live, for the player's own ID
## picture (IdPicture) and the save cards of heroes whose save has none yet.
##
## Renders in its own small world (a SubViewport added under the scene root for a few frames), so it works in the
## menu and in the game alike. Needs a real renderer: headless runs return null.

const SIZE := 256
const BG_INNER := Color("47382c")
const BG_OUTER := Color("0c0a09")

## Render a portrait. `dress` is called with the CharacterVisual (already set up on the hero body) to put the look and
## clothes on it. Returns null when nothing can be drawn (headless, no tree, no model).
static func render(dress: Callable, size := SIZE, yaw_deg := 14.0) -> Image:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null or DisplayServer.get_name() == "headless" or not Persona.available():
		return null
	var vp := SubViewport.new()
	vp.size = Vector2i(size, size)
	vp.own_world_3d = true
	vp.transparent_bg = false
	vp.msaa_3d = Viewport.MSAA_4X
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.62, 0.6, 0.62)
	e.ambient_light_energy = 0.38
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.tonemap_exposure = 0.95
	env.environment = e
	vp.add_child(env)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-22, -32, 0)
	key.light_energy = 1.05
	key.light_color = Color(1.0, 0.95, 0.88)
	vp.add_child(key)
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-10, 150, 0)
	rim.light_energy = 0.8
	rim.light_color = Color(0.75, 0.85, 1.0)
	vp.add_child(rim)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-5, 40, 0)
	fill.light_energy = 0.35
	vp.add_child(fill)
	var v := CharacterVisual.new()
	vp.add_child(v)
	tree.root.add_child(vp)
	v.setup(Persona.MODEL, 1.0, Color.WHITE, &"")
	if v.hero == null:
		vp.queue_free()
		return null
	dress.call(v)
	v.detach_weapon(&"main")
	v.detach_weapon(&"off")
	v.rotation_degrees.y = yaw_deg
	# a still, neutral pose
	v.set_process(false)
	if v.tree:
		v.tree.active = false
	if v.anim_player:
		var idle := v._loco_clip(&"idle")
		v.anim_player.play(idle if v.has_anim(idle) else &"idle")
		v.anim_player.seek(0.4, true)
		v.anim_player.pause()
	var cam := Camera3D.new()
	cam.fov = 24.0
	vp.add_child(cam)
	await tree.process_frame
	var head := Vector3(0, 1.66, 0)
	if v.skeleton:
		var hb := v.skeleton.find_bone("head")
		if hb >= 0:
			head = v.skeleton.global_transform * v.skeleton.get_bone_global_pose(hb).origin
	var focus := head + Vector3(0, 0.0, 0)
	var dist := 1.5 * v.model_scale
	cam.position = focus + Vector3(0, 0.03 * v.model_scale, dist)
	cam.look_at(focus)
	# the backdrop: a quad behind the sitter, a warm-to-dark radial vignette (no per-pixel work on the CPU)
	var bd := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2.ONE * 3.0 * v.model_scale
	bd.mesh = q
	var sm := ShaderMaterial.new()
	sm.shader = _backdrop_shader()
	bd.material_override = sm
	bd.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	vp.add_child(bd)
	bd.position = focus - Vector3(0, 0, 0.9 * v.model_scale)
	await tree.process_frame
	await tree.process_frame
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	vp.queue_free()
	if img == null or img.is_empty():
		return null
	img.convert(Image.FORMAT_RGB8)
	return img

static var _bd_shader: Shader

static func _backdrop_shader() -> Shader:
	if _bd_shader == null:
		_bd_shader = Shader.new()
		_bd_shader.code = """shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;
uniform vec3 inner = vec3(%f, %f, %f);
uniform vec3 outer = vec3(%f, %f, %f);
void fragment() {
	float t = clamp(distance(UV, vec2(0.5, 0.45)) / 0.3, 0.0, 1.0);
	ALBEDO = mix(inner, outer, smoothstep(0.0, 1.0, t));
}
""" % [_lin(BG_INNER).r, _lin(BG_INNER).g, _lin(BG_INNER).b, _lin(BG_OUTER).r, _lin(BG_OUTER).g, _lin(BG_OUTER).b]
	return _bd_shader

## A persona (DataPersonas) as a portrait.
static func render_persona(p: Dictionary, size := SIZE) -> Image:
	var dress := func(v: CharacterVisual) -> void: Persona.apply(v, p)
	return await render(dress, size)

## A hero's look and worn equipment as a portrait (the player's ID picture).
static func render_hero(look: Dictionary, equipment: Equipment, size := SIZE) -> Image:
	var dress := func(v: CharacterVisual) -> void:
		v.set_look(look)
		if equipment:
			v.dress_equipment(equipment)
	return await render(dress, size)

static func _lin(c: Color) -> Color:
	return c.srgb_to_linear()

## bh-031: a Tempo's ID portrait (its face is its own: Persona.tempo_look), taken once per Tempo and kept for the
## session. `rect` shows `fallback` until the shot is ready. Portrait handles "tempo:<uid>" name one in dialogue.
static var _tempo_shots := {}

static func tempo_portrait(uid: int, rect: TextureRect, fallback: Texture2D = null) -> void:
	if _tempo_shots.has(uid):
		rect.texture = _tempo_shots[uid]
		return
	rect.texture = fallback
	var t := _find_tempo(uid)
	if t == null:
		return
	var td := t.class_def()
	var dress := func(v: CharacterVisual) -> void:
		v.set_look(Persona.tempo_look(t.uid, t.class_id, td.get("color", t.tint)))
		v.set_dyes(Persona.TEMPO_DYE)
		v.dress_equipment(Persona.tempo_equipment(t.equipment, t.class_id))
	var img := await render(dress, SIZE)
	if img == null:
		return
	var tex := ImageTexture.create_from_image(img)
	_tempo_shots[uid] = tex
	if is_instance_valid(rect):
		rect.texture = tex

static func _find_tempo(uid: int) -> TempoData:
	var h := Game.hero
	if h == null:
		return null
	for t in h.tempos + h.spirit_hall:
		if t is TempoData and (t as TempoData).uid == uid:
			return t
	return null
