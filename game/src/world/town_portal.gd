class_name TownPortal
extends Node3D
## Town Portal (bh-006). Reading a Town Portal Scroll rips space open in front of the hero: a jagged tear of light
## splits the air, then widens into a violent spinning vortex that drags dust and sparks into itself. Interact (R)
## steps through to Malasugue, where a matching return portal stands beside the waypoint and leads back to the exact
## spot. The portal lasts until the hero dies, dispels it (HUD) or opens another one, which replaces it.
## State lives in HeroData.town_portal (saved); the nodes are rebuilt whenever either end's map is loaded.

const TOWN := &"sanctuary"
const TOWN_SPAWN := &"waypoint"
const OPEN_TIME := 1.25
const HEIGHT := 2.6
const WIDTH := 1.5
const CENTER_Y := 1.75             # the vortex's centre above the ground
const CLEAR_RADIUS := 1.15         # nothing solid may stand inside this column around the portal ...
const CLEAR_BOTTOM := 0.55         # ... from knee height ...
const CLEAR_HEIGHT := 2.6          # ... to above the vortex
const KEEP_AWAY := 3.2             # and it keeps this far from waypoints, doors and people
const TOWN_MARKER := &"town_portal" # the designed spot for the return portal (sanctuary.gd)

var is_return := false            # the Malasugue end
var interact_range := 2.6
var _open := 0.0                  # 0 = a hairline tear, 1 = fully open
var _closing := false
var _t := 0.0
var _mat: ShaderMaterial
var _ground_mat: ShaderMaterial
var _light: OmniLight3D
var _loop: AudioStreamPlayer3D
var _hum: AudioStreamPlayer3D
var _plate: Label3D

# ---- Lifecycle (static API) -----------------------------------------------------------------------------------

## Read a scroll: open a portal in front of the hero. False (scroll kept) when that is not possible here.
static func open_for(p: Player) -> bool:
	var def := DB.map_def(Game.current_map_id)
	if def == null or Game.current_map == null:
		return false
	if def.is_town or def.interior:
		Events.notify.emit("You are already in town.", &"error")
		Audio.play_ui(&"ui_error")
		return false
	var fwd := p.forward()
	var found = find_clear_spot(p.get_world_3d(), p.global_position, fwd)
	if found == null:
		Events.notify.emit("There is no room to open a portal here.", &"error")
		Audio.play_ui(&"ui_error")
		return false
	var spot: Vector3 = found
	var to_hero := p.global_position - spot
	_close_all(true)
	p.hero.town_portal = {"map": String(Game.current_map_id), "pos": [spot.x, spot.y, spot.z], "yaw": atan2(to_hero.x, to_hero.z)}
	var tp := _make(false)
	Game.current_map.add_child(tp)
	tp.global_position = spot
	tp.rotation.y = p.hero.town_portal.yaw
	tp.begin_open(true)
	p.visual.play_action(&"cast_area", 1.0)
	Events.notify.emit("You tear open a Town Portal.", &"info")
	Events.town_portal_changed.emit()
	return true

## Close the hero's portal (both ends). Quiet when there is none.
static func dispel(message := "The Town Portal collapses.") -> void:
	var h := Game.hero
	if h == null or h.town_portal.is_empty():
		return
	h.town_portal = {}
	_close_all(false)
	if message != "":
		Events.notify.emit(message, &"info")
	Events.town_portal_changed.emit()

## The hero died: the portal expires.
static func expire(message: String) -> void:
	dispel(message)

## Map loaded: rebuild whichever end belongs here (no tearing animation, it is already open).
static func spawn_for(map: Node3D, map_id: StringName) -> void:
	var h := Game.hero
	if h == null or h.town_portal.is_empty() or map == null:
		return
	var tp: TownPortal = null
	if StringName(h.town_portal.get("map", "")) == map_id:
		tp = _make(false)
		map.add_child(tp)
		var pos: Array = h.town_portal.pos
		tp.global_position = Vector3(pos[0], pos[1], pos[2])
		tp.rotation.y = float(h.town_portal.get("yaw", 0.0))
	elif map_id == TOWN and map.has_method(&"spawn_transform"):
		tp = _make(true)
		map.add_child(tp)
		var spawns = map.get(&"spawns")
		if spawns is Dictionary and (spawns as Dictionary).has(TOWN_MARKER):
			# the designed spot on the waypoint terrace
			var mk: Transform3D = map.call(&"spawn_transform", TOWN_MARKER)
			tp.global_position = mk.origin
			tp.rotation.y = mk.basis.get_euler().y
		else:
			var sp: Transform3D = map.call(&"spawn_transform", TOWN_SPAWN)
			var found = find_clear_spot(map.get_world_3d(), sp.origin, sp.basis.z)
			tp.global_position = found if found != null else sp.origin + sp.basis.x * 3.6
			tp.rotation.y = sp.basis.get_euler().y
	if tp:
		tp.begin_open(false)

## A spot near `origin` where the whole vortex fits: walkable floor at about the same height, nothing solid (walls,
## pillars, trees, props) inside a CLEAR_RADIUS column from knee height to above the vortex, in sight from `origin`,
## and at least KEEP_AWAY from waypoints, doors and people. Tries in front first, then fans out to the sides and back.
## Null when there is no such spot (a cramped corridor): the scroll is then not used up.
static func find_clear_spot(world: World3D, origin: Vector3, forward: Vector3) -> Variant:
	var space := world.direct_space_state
	var shape := CylinderShape3D.new()
	shape.radius = CLEAR_RADIUS
	shape.height = CLEAR_HEIGHT
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.collision_mask = BH.LAYER_WORLD | BH.LAYER_PROPS
	var f := forward.slide(Vector3.UP)
	var yaw := atan2(f.x, f.z) if f.length() > 0.01 else 0.0
	for dist: float in [2.8, 3.6, 2.2, 4.6]:
		for off: float in [0.0, 35.0, -35.0, 70.0, -70.0, 110.0, -110.0, 150.0, -150.0, 180.0]:
			var a := yaw + deg_to_rad(off)
			var cand := origin + Vector3(sin(a), 0.0, cos(a)) * dist
			var g = Loot.floor_under(space, cand, origin.y)
			if g == null:
				continue
			var spot: Vector3 = g
			if absf(spot.y - origin.y) > 1.2:
				continue
			var los := PhysicsRayQueryParameters3D.create(origin + Vector3.UP, spot + Vector3.UP, BH.LAYER_WORLD | BH.LAYER_PROPS)
			if not space.intersect_ray(los).is_empty():
				continue
			if not is_clear(space, q, spot) or _near_landmark(spot):
				continue
			return spot
	return null

## Nothing solid inside the portal's column at `spot` (floors and terrain do not count).
static func is_clear(space: PhysicsDirectSpaceState3D, q: PhysicsShapeQueryParameters3D, spot: Vector3) -> bool:
	q.transform = Transform3D(Basis(), spot + Vector3.UP * (CLEAR_BOTTOM + CLEAR_HEIGHT * 0.5))
	for hit in space.intersect_shape(q, 16):
		var col = hit.get("collider")
		if col is CollisionObject3D and ((col as CollisionObject3D).collision_layer & BH.LAYER_GROUND) != 0:
			continue
		return false
	return true

static func _near_landmark(spot: Vector3) -> bool:
	var tree := Engine.get_main_loop() as SceneTree
	for grp in [&"teleporter", &"door", &"npc"]:
		for n in tree.get_nodes_in_group(grp):
			var n3 := n as Node3D
			if n3 and Vector2(n3.global_position.x - spot.x, n3.global_position.z - spot.z).length() < KEEP_AWAY:
				return true
	return false

static func _make(p_return: bool) -> TownPortal:
	var tp := TownPortal.new()
	tp.is_return = p_return
	tp.name = "TownPortalReturn" if p_return else "TownPortal"
	return tp

static func _close_all(instant: bool) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return
	for n in tree.get_nodes_in_group(&"town_portal"):
		if n is TownPortal:
			if instant:
				(n as TownPortal).collapse(0.35)
			else:
				(n as TownPortal).collapse(0.6)

# ---- Node ------------------------------------------------------------------------------------------------------

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"town_portal")
	_build()

func _build() -> void:
	# the vortex: a camera-facing (Y-billboard) oval of swirling, torn space that bends the scene behind its rim
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(WIDTH * 2.2, HEIGHT * 1.35)
	mi.mesh = q
	_mat = ShaderMaterial.new()
	_mat.shader = _shader("vortex", VORTEX_SHADER)
	_mat.set_shader_parameter("open", 0.0)
	_mat.set_shader_parameter("aspect", (WIDTH * 2.2) / (HEIGHT * 1.35))
	mi.material_override = _mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = CENTER_Y
	mi.extra_cull_margin = 2.0
	add_child(mi)
	# a scorched, swirling ring on the ground so it reads from the high camera too
	var gm := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(4.2, 4.2)
	gm.mesh = pm
	_ground_mat = ShaderMaterial.new()
	_ground_mat.shader = _shader("ground", GROUND_SHADER)
	_ground_mat.set_shader_parameter("open", 0.0)
	gm.material_override = _ground_mat
	gm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	gm.position.y = 0.04
	add_child(gm)
	# debris and sparks spiralling into the eye
	add_child(_inflow())
	var sparks := LootFx.small_particles(Color(0.85, 0.7, 1.0, 0.95), 26, 0.5, 0.06, 4.0, 80.0, Vector3(0, -3.0, 0), 0.5)
	sparks.position.y = CENTER_Y
	add_child(sparks)
	_light = OmniLight3D.new()
	_light.light_color = Color(0.62, 0.35, 1.0)
	_light.light_energy = 0.0
	_light.omni_range = 7.0
	_light.position = Vector3(0, 1.5, 0.4)
	add_child(_light)
	_plate = Label3D.new()
	_plate.text = "Town Portal — Malasugue" if not is_return else _return_label()
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = Color(0.85, 0.72, 1.0)
	_plate.position.y = CENTER_Y + 2.0     # above the vortex's torn top edge
	_plate.visible = false
	add_child(_plate)

func _return_label() -> String:
	var h := Game.hero
	var def := DB.map_def(StringName(h.town_portal.get("map", ""))) if h and not h.town_portal.is_empty() else null
	return "Portal — back to %s" % (def.display_name if def else "the wilds")

func _inflow() -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = Perf.particles(48)
	p.lifetime = 1.1
	p.preprocess = 1.0
	p.local_coords = true
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
	pm.emission_ring_axis = Vector3(0, 0, 1)
	pm.emission_ring_radius = 2.6
	pm.emission_ring_inner_radius = 1.6
	pm.emission_ring_height = 0.6
	pm.gravity = Vector3.ZERO
	pm.radial_accel_min = -9.0
	pm.radial_accel_max = -6.0
	pm.tangential_accel_min = 7.0
	pm.tangential_accel_max = 11.0
	pm.damping_min = 0.5
	pm.damping_max = 1.0
	pm.scale_min = 0.4
	pm.scale_max = 1.0
	var g := Gradient.new()
	g.set_color(0, Color(0.55, 0.9, 1.0, 0.0))
	g.add_point(0.3, Color(0.75, 0.55, 1.0, 0.9))
	g.set_color(g.get_point_count() - 1, Color(1.0, 0.5, 0.9, 0.0))
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2.ONE * 0.12
	q.material = LootFx.soft_material()
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-4, -3, -4), Vector3(8, 8, 8))
	p.position.y = CENTER_Y
	return p

## Tear -> vortex. `dramatic`: the first opening (flash, lightning, shake, rip sound); map reloads open quickly.
func begin_open(dramatic: bool) -> void:
	_loop = Audio.make_loop(&"whirlwind_loop", self, -7.0, 16.0)
	if _loop:
		_loop.pitch_scale = 0.7
	_hum = Audio.make_loop(&"teleporter_hum", self, -9.0, 14.0)
	if _hum:
		_hum.pitch_scale = 0.55
	if not dramatic:
		_open = 1.0
		_apply_open()
		return
	Audio.play_at(&"teleport_charge", global_position, 2.0)
	var tw := create_tween()
	# 1. a hairline rip crackles into existence
	tw.tween_method(_set_open, 0.0, 0.06, 0.35)
	tw.tween_callback(func() -> void:
		Audio.play_at(&"thunder_strike", global_position, -2.0)
		Audio.play_at(&"wind_gust", global_position, 2.0)
		FX.spawn(VFXLib.light_flash(Color(0.75, 0.5, 1.0), 10.0, 10.0, 0.35), global_position + Vector3.UP * 1.5)
		Events.camera_shake.emit(0.35)
		for i in 5:
			var a := randf() * TAU
			var from := global_position + Vector3.UP * (0.6 + randf() * 2.0)
			FX.spawn(VFXLib.lightning_bolt(from, from + Vector3(cos(a), randf_range(-0.6, 0.8), sin(a)) * randf_range(1.2, 2.4),
				Color(0.8, 0.6, 1.0), 0.25, 0.08), Vector3.ZERO))
	# 2. it is wrenched open into a spinning vortex
	tw.tween_method(_set_open, 0.06, 1.0, OPEN_TIME - 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func() -> void:
		FX.spawn(VFXLib.ring_wave(Color(0.7, 0.45, 1.0, 0.9), 3.5, 0.5, 0.6), global_position)
		Audio.play_at(&"teleport_whoosh", global_position, 0.0))

func collapse(time := 0.6) -> void:
	if _closing:
		return
	_closing = true
	remove_from_group(&"interactable")
	remove_from_group(&"town_portal")
	if is_inside_tree():
		Audio.play_at(&"teleport_whoosh", global_position, -2.0)
	var tw := create_tween()
	tw.tween_method(_set_open, _open, 0.0, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		if is_inside_tree():
			FX.spawn(VFXLib.light_flash(Color(0.75, 0.5, 1.0), 6.0, 6.0, 0.2), global_position + Vector3.UP * 1.5)
		queue_free())

func _set_open(v: float) -> void:
	_open = v
	_apply_open()

func _apply_open() -> void:
	if _mat:
		_mat.set_shader_parameter("open", _open)
	if _ground_mat:
		_ground_mat.set_shader_parameter("open", _open)

func _process(delta: float) -> void:
	_t += delta
	if _light:
		_light.light_energy = _open * (2.2 + 0.6 * sin(_t * 11.0) + 0.4 * sin(_t * 23.0))
	if _plate:
		var p := Game.player as Node3D
		_plate.visible = not _closing and _open > 0.9 and p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 8.0

# ---- Interactable -----------------------------------------------------------------------------------------------

func can_interact(_p: Node) -> bool:
	return not _closing and _open > 0.8 and not Game.travelling

func interact_text() -> String:
	return _return_label() if is_return else "Enter the Town Portal (to Malasugue)"

func interact_anim() -> StringName:
	return &"interact_teleport"

func interact(_p: Node) -> void:
	var h := Game.hero
	if h == null or h.town_portal.is_empty():
		return
	Audio.play_at(&"teleport_whoosh", global_position, 2.0)
	FX.spawn(VFXLib.light_flash(Color(0.75, 0.5, 1.0), 8.0, 8.0, 0.4), global_position + Vector3.UP * 1.5)
	if is_return:
		var pos: Array = h.town_portal.pos
		var yaw := float(h.town_portal.get("yaw", 0.0))
		# arrive just in front of the far end, facing away from it
		var front := Vector3(-sin(yaw), 0.0, -cos(yaw))
		Game.travel_to_point(StringName(h.town_portal.map), Vector3(pos[0], pos[1], pos[2]) - front * 1.8, yaw + PI)
	else:
		Game.travel(TOWN, TOWN_SPAWN)

# ---- Shaders ------------------------------------------------------------------------------------------------------

static var _shaders := {}

static func _shader(key: String, code: String) -> Shader:
	if not _shaders.has(key):
		var sh := Shader.new()
		sh.code = code
		_shaders[key] = sh
	return _shaders[key]

const VORTEX_SHADER := """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float open = 1.0;
uniform float aspect = 0.8;
uniform vec4 deep : source_color = vec4(0.05, 0.0, 0.12, 1.0);
uniform vec4 violet : source_color = vec4(0.5, 0.18, 1.0, 1.0);
uniform vec4 cyan : source_color = vec4(0.3, 0.9, 1.0, 1.0);
uniform vec4 magenta : source_color = vec4(1.0, 0.3, 0.8, 1.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
	float v = 0.0; float a = 0.5;
	for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
	return v;
}

void vertex() {
	// faces the camera: the tear in space reads at full size from the high isometric view
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
		vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0), vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	p.y = -p.y;
	p.x *= aspect;
	// the oval: 0.62 wide x 0.74 tall at full opening; a thin tall slit while the tear forms
	float w = mix(0.012, 0.6, smoothstep(0.0, 1.0, open));
	float h = mix(0.25, 0.74, smoothstep(0.0, 0.25, open));
	vec2 q = vec2(p.x / w, p.y / h);
	float r = length(q);
	float ang = atan(q.y, q.x);
	vec2 dir = vec2(cos(ang), sin(ang));      // noise is sampled on the circle: periodic, no seam where atan wraps
	// torn, flickering rim
	float tear = (fbm(dir * 1.2 + vec2(TIME * 1.1, TIME * 0.7)) - 0.5) * 0.34 + (noise(dir * 3.5 + vec2(TIME * 3.5, -TIME * 2.9)) - 0.5) * 0.12;
	float edge = 1.0 + tear;
	float inside = 1.0 - smoothstep(edge - 0.06, edge, r);
	// violent spiral: angle advected by time and twisted harder toward the eye
	float swirl = ang + TIME * 4.2 + 2.6 / (r + 0.18);
	vec2 sd = vec2(cos(swirl), sin(swirl));
	float n1 = fbm(sd * 1.4 + vec2(r * 3.0 - TIME * 3.4, 0.0));
	float n2 = fbm(sd * 2.6 + vec2(3.0, r * 5.0 - TIME * 5.0));
	vec3 col = mix(deep.rgb, violet.rgb, smoothstep(0.25, 0.75, n1));
	col = mix(col, cyan.rgb, smoothstep(0.55, 0.85, n2) * 0.8);
	col = mix(col, magenta.rgb, smoothstep(0.62, 0.9, n1 * n2 * 1.8) * 0.6);
	// arms of light spiralling in, the black eye at the centre
	float arms = pow(0.5 + 0.5 * sin(swirl * 3.0 + n1 * 4.0), 6.0);
	col += violet.rgb * arms * 0.9 * smoothstep(0.1, 0.9, r);
	col *= smoothstep(0.0, 0.35, r) * 0.9 + 0.1;
	col += vec3(1.0, 0.95, 1.0) * exp(-r * r * 40.0) * 0.4;
	// the white-hot torn rim
	float rim = exp(-pow((r - edge) * 14.0, 2.0));
	col += mix(magenta.rgb, vec3(1.0), 0.55) * rim * 2.2;
	// outside the rim space is bent: the scene behind is dragged around the vortex, with crackling fractures
	float ring = smoothstep(edge + 0.3, edge, r) * (1.0 - inside);
	// never let the bent-space halo reach the quad's border (a visible rectangle)
	vec2 uvc = abs(UV * 2.0 - 1.0);
	ring *= smoothstep(0.98, 0.8, max(uvc.x, uvc.y));
	vec2 tang = vec2(-dir.y, dir.x);
	vec2 off = (tang * 0.035 + dir * -0.02) * ring * open;
	vec3 bent = texture(screen_tex, SCREEN_UV + off).rgb;
	float crack = pow(1.0 - abs(noise(dir * 4.0 + vec2(r * 3.0 - TIME * 1.5, 0.0)) * 2.0 - 1.0), 18.0) * ring;
	bent += violet.rgb * (crack * 1.6 + ring * 0.12) + magenta.rgb * rim * 0.5;
	ALBEDO = mix(bent, col * 1.6, inside);
	ALPHA = clamp(max(inside, ring * 0.999), 0.0, 1.0) * smoothstep(0.0, 0.02, open);
}
"""

const GROUND_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform float open = 1.0;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float ang = atan(p.y, p.x);
	float swirl = ang - TIME * 2.5 + 3.0 / (r + 0.25);
	float arms = pow(0.5 + 0.5 * sin(swirl * 4.0 + noise(vec2(cos(ang), sin(ang)) * 2.5 + vec2(TIME, 0.0)) * 3.0), 4.0);
	float disk = smoothstep(1.0, 0.3, r) * smoothstep(0.0, 0.15, r);
	float ring = exp(-pow((r - 0.62 - 0.03 * sin(TIME * 5.0)) * 10.0, 2.0));
	vec3 c = mix(vec3(0.45, 0.2, 1.0), vec3(0.3, 0.9, 1.0), arms) * (arms * disk * 0.55 + ring * 0.8);
	ALBEDO = c * open;
}
"""
