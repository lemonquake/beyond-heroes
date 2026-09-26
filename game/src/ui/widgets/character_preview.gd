class_name CharacterPreview
extends SubViewportContainer
## Live 3D hero on a lit plinth, rendered in its own world: drag to rotate (or auto-turn), idle personality animations,
## equipped weapons shown. Used by Hero Selection, the Character screen and the Inventory paper doll.

var viewport: SubViewport
var visual: CharacterVisual
var pivot: Node3D
var camera: Camera3D
var auto_rotate := false
var zoom := 1.0
var _drag := false
var _yaw := 0.0
var _yaw_vel := 0.0
var _class_id: StringName = &""
var _fidget_t := 6.0
var _pixel := Vector2i(512, 640)

func _init(px := Vector2i(512, 640)) -> void:
	_pixel = px
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(px) * 0.5

func _ready() -> void:
	viewport = SubViewport.new()
	viewport.own_world_3d = true
	viewport.transparent_bg = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	add_child(viewport)
	var world := Node3D.new()
	viewport.add_child(world)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.32, 0.34, 0.45)
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_ACES
	e.tonemap_exposure = 1.05
	e.glow_enabled = true
	e.glow_intensity = 0.6
	e.glow_bloom = 0.05
	env.environment = e
	world.add_child(env)
	# cinematic three-point lighting: warm key, cool aether rim, soft fill
	var key := DirectionalLight3D.new()
	key.light_color = Color(1.0, 0.86, 0.68)
	key.light_energy = 1.25
	key.rotation_degrees = Vector3(-35, 35, 0)
	key.shadow_enabled = true
	world.add_child(key)
	var rim := OmniLight3D.new()
	rim.light_color = Color(0.5, 0.92, 1.0)
	rim.light_energy = 2.4
	rim.omni_range = 6.0
	rim.position = Vector3(-1.2, 2.4, -1.6)
	world.add_child(rim)
	var fill := OmniLight3D.new()
	fill.light_color = Color(0.75, 0.62, 1.0)
	fill.light_energy = 0.8
	fill.omni_range = 7.0
	fill.position = Vector3(1.8, 1.2, 2.2)
	world.add_child(fill)
	var under := OmniLight3D.new()
	under.light_color = Color(0.45, 0.95, 1.0)
	under.light_energy = 0.9
	under.omni_range = 2.2
	under.position = Vector3(0, 0.15, 0.4)
	world.add_child(under)
	# plinth: dark stone disc with an aether ring
	var plinth := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.72
	cyl.bottom_radius = 0.78
	cyl.height = 0.12
	cyl.radial_segments = 48
	plinth.mesh = cyl
	var pm := StandardMaterial3D.new()
	pm.albedo_color = Color(0.09, 0.08, 0.085)
	pm.roughness = 0.55
	pm.metallic = 0.2
	plinth.material_override = pm
	plinth.position.y = -0.06
	world.add_child(plinth)
	var ring := MeshInstance3D.new()
	var tor := TorusMesh.new()
	tor.inner_radius = 0.7
	tor.outer_radius = 0.74
	tor.rings = 64
	ring.mesh = tor
	var rm := StandardMaterial3D.new()
	rm.albedo_color = Color(0.5, 0.95, 1.0)
	rm.emission_enabled = true
	rm.emission = Color(0.45, 0.95, 1.0)
	rm.emission_energy_multiplier = 2.5
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring.material_override = rm
	ring.position.y = 0.005
	world.add_child(ring)
	pivot = Node3D.new()
	world.add_child(pivot)
	camera = Camera3D.new()
	camera.fov = 30.0
	world.add_child(camera)
	_place_camera()
	resized.connect(_on_resized)
	_on_resized()

func _on_resized() -> void:
	if viewport:
		viewport.size = Vector2i(maxi(64, int(size.x * 2.0)), maxi(64, int(size.y * 2.0)))

func _place_camera() -> void:
	var h := 1.02
	var dist := 5.2 / zoom
	camera.position = Vector3(0, h + 0.25, dist)
	camera.look_at(Vector3(0, h - 0.05, 0))

## Show a hero class (hero select) or a live hero (character/inventory). `hero` may be null.
func show_class(class_id: StringName, hero: HeroData = null) -> void:
	var cls := DB.class_def(class_id)
	if cls == null:
		return
	if visual and _class_id == class_id:
		dress(hero)
		return
	_class_id = class_id
	if visual:
		visual.queue_free()
	visual = CharacterVisual.new()
	pivot.add_child(visual)
	visual.setup(cls.model_path, 1.0, cls.tint, cls.id)
	visual.set_stance(&"idle")
	dress(hero)
	_fidget_t = 2.5

## Attach the weapons the hero (or, without a hero, the class's starting kit) holds.
func dress(hero: HeroData) -> void:
	if visual == null:
		return
	visual.detach_weapon(&"main")
	visual.detach_weapon(&"off")
	var eq := hero.equipment if hero else _starting_equipment()
	var lo := eq.loadout()
	var main := eq.get_item(&"main_weapon")
	var sub := eq.get_item(&"sub_weapon")
	if main != null and lo.main_type != null:
		visual.attach_weapon(&"main", _weapon_model(main, lo.main_type), lo.main_type.grip_offset)
	if sub != null:
		if sub.base.category == &"shield":
			visual.attach_weapon(&"off", "res://assets/weapons/shield.glb")
		elif lo.off_type != null:
			visual.attach_weapon(&"off", _weapon_model(sub, lo.off_type), lo.off_type.grip_offset)
	var stance: StringName = &"idle_1h"
	if lo.is_unarmed():
		stance = &"idle"
	elif lo.dual_wield:
		stance = &"idle_dual"
	elif lo.has_shield:
		stance = &"idle_shield"
	elif lo.main_type:
		stance = lo.main_type.idle_anim
	visual.set_stance(stance if visual.has_anim(stance) else &"idle")

func _weapon_model(item: ItemInstance, wt: WeaponTypeDef) -> String:
	if item.rarity == BH.Rarity.AETHER:
		var ae := "res://assets/weapons/%s_aether.glb" % wt.id
		if ResourceLoader.exists(ae):
			return ae
	return wt.model

func _starting_equipment() -> Equipment:
	var eq := Equipment.new()
	var cls := DB.class_def(_class_id)
	for base_id in cls.starting_items:
		var it := DB.make_item(base_id, BH.Rarity.BEGINNER, 1, hash(String(base_id)))
		if it:
			eq.equip(it, eq.auto_slot(it), 99, {&"str": 99, &"agi": 99, &"int": 99, &"wis": 99, &"spi": 99, &"dex": 99})
	return eq

func play(anim: StringName) -> void:
	if visual and visual.has_anim(anim):
		visual.play_action(anim, 1.0)

func _process(delta: float) -> void:
	if visual == null:
		return
	visual.update_locomotion(Vector2.ZERO, false, 0.0, delta)
	if not _drag:
		if auto_rotate:
			_yaw += delta * 0.35
		_yaw += _yaw_vel * delta
		_yaw_vel = lerpf(_yaw_vel, 0.0, 1.0 - exp(-3.0 * delta))
	pivot.rotation.y = _yaw
	_fidget_t -= delta
	if _fidget_t <= 0.0 and not visual.is_busy():
		_fidget_t = randf_range(6.0, 10.0)
		var opts: Array = [&"idle_look", &"idle_adjust", StringName("idle_%s" % _class_id)].filter(func(a): return visual.has_anim(a))
		if not opts.is_empty():
			visual.play_action(opts[randi() % opts.size()], 1.0)

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton:
		if e.button_index == MOUSE_BUTTON_LEFT:
			_drag = e.pressed
		elif e.button_index == MOUSE_BUTTON_WHEEL_UP and e.pressed:
			zoom = clampf(zoom + 0.08, 0.8, 1.6)
			_place_camera()
		elif e.button_index == MOUSE_BUTTON_WHEEL_DOWN and e.pressed:
			zoom = clampf(zoom - 0.08, 0.8, 1.6)
			_place_camera()
	elif e is InputEventMouseMotion and _drag:
		var d: float = e.relative.x * 0.012 * Settings.mouse_sensitivity
		_yaw += d
		_yaw_vel = d * 30.0
