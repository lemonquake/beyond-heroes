class_name MapExplorer
extends CharacterBody3D
## Temporary map-testing pawn used until the real player controller (Phase 2) lands: WASD (camera-relative) and
## click-to-move over the navmesh, an isometric follow camera with smoothing and wheel zoom, a hand lantern, and
## interact (R) for teleporters. It joins group "player" so teleporters, triggers and Game.place_player treat it
## exactly like the future hero.

const SPEED := 6.0
const ACCEL := 40.0
const GRAVITY := 24.0

var cam_yaw := 0.0
var cam_pitch := 52.0
var cam_dist := 17.0
var camera: Camera3D
var agent: NavigationAgent3D
var _click_target := Vector3.INF
var _hud: CanvasLayer
var _prompt: Label
var _notice: Label
var _notice_tw: Tween

func _ready() -> void:
	add_to_group(&"player")
	collision_layer = BH.LAYER_PLAYER
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS
	floor_max_angle = deg_to_rad(46.0)
	floor_snap_length = 0.4
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.4
	cap.height = 1.8
	cs.shape = cap
	cs.position.y = 0.9
	add_child(cs)
	var body := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.36
	cm.height = 1.75
	body.mesh = cm
	body.position.y = 0.88
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.55, 0.5, 0.42)
	mat.roughness = 0.8
	body.material_override = mat
	add_child(body)
	var lantern := OmniLight3D.new()
	lantern.light_color = Color(1.0, 0.8, 0.55)
	lantern.light_energy = 0.9
	lantern.omni_range = 6.5
	lantern.position = Vector3(0.35, 1.3, 0.2)
	add_child(lantern)
	agent = NavigationAgent3D.new()
	# the navmesh surface sits up to ~0.5 m above sloped terrain (cell-height quantisation); waypoint tolerances are
	# 3D, so they must exceed that or the agent never advances past a waypoint directly overhead
	agent.path_desired_distance = 1.0
	agent.target_desired_distance = 0.8
	agent.path_height_offset = 0.3
	agent.radius = 0.45
	add_child(agent)
	camera = Camera3D.new()
	camera.fov = 42.0
	camera.far = 400.0
	camera.top_level = true
	add_child(camera)
	camera.make_current()
	_build_hud()
	Events.interact_prompt.connect(_on_prompt)
	Events.notify.connect(_on_notify)
	_snap_camera()

func _build_hud() -> void:
	_hud = CanvasLayer.new()
	_hud.layer = 20
	add_child(_hud)
	_prompt = UITheme.label("", 22, UITheme.GOLD, UITheme.body_bold())
	_prompt.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt.position.y -= 140
	_prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt.add_theme_color_override("font_outline_color", Color.BLACK)
	_prompt.add_theme_constant_override("outline_size", 8)
	_hud.add_child(_prompt)
	_notice = UITheme.label("", 26, UITheme.PARCHMENT, UITheme.title_font())
	_notice.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	_notice.position.y += 90
	_notice.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_notice.add_theme_color_override("font_outline_color", Color.BLACK)
	_notice.add_theme_constant_override("outline_size", 8)
	_hud.add_child(_notice)

func _on_prompt(text: String) -> void:
	_prompt.text = ("[%s]  %s" % [InputSetup.key_label("interact"), text]) if text != "" else ""

func _on_notify(text: String, _kind: StringName) -> void:
	_notice.text = text
	_notice.modulate.a = 1.0
	if _notice_tw:
		_notice_tw.kill()
	_notice_tw = create_tween()
	_notice_tw.tween_interval(2.5)
	_notice_tw.tween_property(_notice, "modulate:a", 0.0, 0.8)

## Walk to a point along the navmesh (click-to-move without the click). Used by the automated playtest.
func walk_to(p: Vector3) -> void:
	_click_target = p
	agent.target_position = p

func is_walking() -> bool:
	return _click_target != Vector3.INF and not agent.is_navigation_finished()

func on_teleported() -> void:
	_click_target = Vector3.INF
	_snap_camera()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"zoom_in"):
		cam_dist = clampf(cam_dist - 1.5, 8.0, 34.0)
	elif event.is_action_pressed(&"zoom_out"):
		cam_dist = clampf(cam_dist + 1.5, 8.0, 34.0)
	elif event.is_action_pressed(&"interact"):
		# waypoints are interactables now (the hero's interact scan uses them); this pawn has no scan of its own
		for t in get_tree().get_nodes_in_group(&"teleporter"):
			if t._player_inside == self:
				t.activate()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var from := camera.project_ray_origin(event.position)
		var to := from + camera.project_ray_normal(event.position) * 300.0
		var q := PhysicsRayQueryParameters3D.create(from, to, BH.LAYER_WORLD | BH.LAYER_GROUND)
		var hit := get_world_3d().direct_space_state.intersect_ray(q)
		if hit:
			_click_target = hit.position
			agent.target_position = hit.position

func _physics_process(delta: float) -> void:
	var input := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	var want := Vector3.ZERO
	if input.length() > 0.05:
		_click_target = Vector3.INF
		want = Vector3(input.x, 0, input.y).rotated(Vector3.UP, deg_to_rad(cam_yaw)) * SPEED
	elif _click_target != Vector3.INF and not agent.is_navigation_finished():
		var nxt := agent.get_next_path_position()
		var d := nxt - global_position
		d.y = 0.0
		if d.length() > 0.05:
			want = d.normalized() * SPEED
	var hv := Vector3(velocity.x, 0, velocity.z).move_toward(want, ACCEL * delta)
	velocity.x = hv.x
	velocity.z = hv.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - GRAVITY * delta
	move_and_slide()
	if global_position.y < -40.0 and Game.current_map:  # safety net: never lose the player below the map
		Game.place_player(Game.hero.current_spawn if Game.hero else &"start")

func _process(delta: float) -> void:
	var target := global_position + Vector3.UP * 1.2
	var off := Vector3(0, 0, cam_dist).rotated(Vector3.RIGHT, -deg_to_rad(cam_pitch)).rotated(Vector3.UP, deg_to_rad(cam_yaw))
	var want := target + off
	camera.global_position = camera.global_position.lerp(want, 1.0 - exp(-8.0 * delta))
	camera.look_at(camera.global_position - off, Vector3.UP)

func _snap_camera() -> void:
	if camera == null:
		return
	var off := Vector3(0, 0, cam_dist).rotated(Vector3.RIGHT, -deg_to_rad(cam_pitch)).rotated(Vector3.UP, deg_to_rad(cam_yaw))
	camera.global_position = global_position + Vector3.UP * 1.2 + off
	camera.look_at(global_position + Vector3.UP * 1.2, Vector3.UP)
