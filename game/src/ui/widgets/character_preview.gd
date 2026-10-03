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
## bh-023: the look shown when no live hero is given (hero selection, the creator).
var look := {}
## bh-023: dress nothing (the creator's "gear off" view), and hold still while the creator plays a pose.
var bare := false
var hold_fidgets := false
## The creator's close-up: leave the helm off so the face can be seen (the hero's own "show helm" choice is kept).
var no_helm := false
var _hero: HeroData
var _key: DirectionalLight3D
var _rim: OmniLight3D
var _fill: OmniLight3D
var _under: OmniLight3D

## bh-023: bare skin under the plinth's strong aether rim reads as glass; a hero's own body gets a softer rig.
func _light_for_hero(on: bool) -> void:
	if _rim == null:
		return
	_rim.light_energy = 1.0 if on else 2.4
	_under.light_energy = 0.3 if on else 0.9
	_fill.light_energy = 1.0 if on else 0.8
	_fill.light_color = Color(1.0, 0.86, 0.74) if on else Color(0.75, 0.62, 1.0)
	_key.light_energy = 1.15 if on else 1.25
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
	_key = key
	var rim := OmniLight3D.new()
	rim.light_color = Color(0.5, 0.92, 1.0)
	rim.light_energy = 2.4
	rim.omni_range = 6.0
	rim.position = Vector3(-1.2, 2.4, -1.6)
	world.add_child(rim)
	_rim = rim
	var fill := OmniLight3D.new()
	fill.light_color = Color(0.75, 0.62, 1.0)
	fill.light_energy = 0.8
	fill.omni_range = 7.0
	fill.position = Vector3(1.8, 1.2, 2.2)
	world.add_child(fill)
	_fill = fill
	var under := OmniLight3D.new()
	under.light_color = Color(0.45, 0.95, 1.0)
	under.light_energy = 0.9
	under.omni_range = 2.2
	under.position = Vector3(0, 0.15, 0.4)
	world.add_child(under)
	_under = under
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
	if viewport and not stretch:
		viewport.size = Vector2i(maxi(64, int(size.x * 2.0)), maxi(64, int(size.y * 2.0)))

## bh-023: what the camera frames: the height it looks at and how far back it stands (the creator moves in on the
## face). `focus()` glides there.
var focus_height := 1.02
var focus_dist := 5.2
var _focus_tw: Tween

func _place_camera() -> void:
	var h := focus_height
	var dist := focus_dist / zoom
	camera.position = Vector3(0, h + 0.25 * focus_dist / 5.2, dist)
	camera.look_at(Vector3(0, h - 0.05 * focus_dist / 5.2, 0))

func focus(height: float, dist: float, time := 0.35) -> void:
	if _focus_tw:
		_focus_tw.kill()
	if time <= 0.0 or not is_inside_tree():
		focus_height = height
		focus_dist = dist
		_place_camera()
		return
	_focus_tw = create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_focus_tw.tween_method(func(v: float) -> void:
		focus_height = v
		_place_camera(), focus_height, height, time)
	_focus_tw.tween_property(self, "focus_dist", dist, time)

## Show a hero class (hero select) or a live hero (character/inventory). `hero` may be null.
func show_class(class_id: StringName, hero: HeroData = null) -> void:
	var cls := DB.class_def(class_id)
	if cls == null:
		return
	if hero:
		look = hero.look
	if visual and _class_id == class_id:
		visual.set_look(look)
		dress(hero)
		return
	_class_id = class_id
	if visual:
		visual.queue_free()
	visual = CharacterVisual.new()
	pivot.add_child(visual)
	visual.setup(HeroLook.MODEL if ResourceLoader.exists(HeroLook.MODEL) else cls.model_path, 1.0, cls.tint, cls.id)
	visual.set_look(look)
	_light_for_hero(visual.hero != null)
	visual.set_stance(&"idle")
	dress(hero)
	_fidget_t = 2.5

## bh-023: change the look of the hero on the plinth (the creator calls this on every slider movement).
func set_look(p_look: Dictionary) -> void:
	look = p_look
	if visual:
		var helm_before := bool(visual.hero.look.get("show_helm", true)) if visual.hero else true
		visual.set_look(look)
		if visual.hero and bool(visual.hero.look.get("show_helm", true)) != helm_before:
			dress(_hero)

## Attach the weapons the hero (or, without a hero, the class's starting kit) holds.
func dress(hero: HeroData) -> void:
	if visual == null:
		return
	_hero = hero
	visual.detach_weapon(&"main")
	visual.detach_weapon(&"off")
	var eq := Equipment.new() if bare else (hero.equipment if hero else _starting_equipment())
	if no_helm and eq.get_item(&"helm") != null:
		var shown := Equipment.new()
		for s in eq.slots:
			shown.slots[s] = eq.slots[s] if s != &"helm" else null
		eq = shown
	visual.dress_equipment(eq)
	var lo := eq.loadout()
	var main := eq.get_item(&"main_weapon")
	var sub := eq.get_item(&"sub_weapon")
	if main != null and lo.main_type != null:
		visual.attach_weapon(&"main", _weapon_model(main, lo.main_type), lo.main_type.grip_offset)
	if sub != null:
		if sub.base.category == &"shield":
			visual.attach_weapon(&"off", sub.base.model_path())
		elif lo.off_type != null:
			visual.attach_weapon(&"off", _weapon_model(sub, lo.off_type), lo.off_type.grip_offset)
	for pair in [[&"main", main], [&"off", sub]]:
		if pair[1] != null and visual.has_weapon(pair[0]):
			visual.set_weapon_ascendant(pair[0], (pair[1] as ItemInstance).rarity, 0.45 if (pair[1] as ItemInstance).base.category == &"shield" else 0.9)
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

## Show a Tempo (spirit companion): its class body in its spectral tint, holding what it wears (or its ghost blade).
func show_tempo(t: TempoData, level := 1) -> void:
	if t == null:
		return
	var key := StringName("tempo_%d_%s" % [t.uid, t.class_id])
	if visual == null or _class_id != key:
		_class_id = key
		if visual:
			visual.queue_free()
		visual = CharacterVisual.new()
		pivot.add_child(visual)
		var td := t.class_def()
		if not Persona.setup_tempo(visual, t.uid, t.class_id, t.tint, td.get("color", t.tint), &"knight" if t.class_id == &"swordsman" else &"mage"):
			visual.setup(String(td.get("model", "res://assets/characters/knight.glb")), 1.0, t.tint, &"knight" if t.class_id == &"swordsman" else &"mage")
		visual.set_rim(DataTempos.SPIRIT_TINT, 0.75)
		_fidget_t = 2.5
	visual.detach_weapon(&"main")
	visual.detach_weapon(&"off")
	var lo := TempoRules.loadout(t, level)
	visual.dress_equipment(Persona.tempo_equipment(t.equipment, t.class_id) if visual.hero else t.equipment)
	var main := t.equipment.get_item(&"main_weapon")
	var sub := t.equipment.get_item(&"sub_weapon")
	if lo.main_type != null:
		visual.attach_weapon(&"main", _weapon_model(main, lo.main_type) if main else lo.main_type.model, lo.main_type.grip_offset)
	if sub != null and sub.base.category == &"shield":
		visual.attach_weapon(&"off", sub.base.model_path())
	elif lo.off_type != null:
		visual.attach_weapon(&"off", _weapon_model(sub, lo.off_type) if sub else lo.off_type.model, lo.off_type.grip_offset)
	var stance: StringName = &"idle_dual" if lo.dual_wield else (&"idle_shield" if lo.has_shield else (lo.main_type.idle_anim if lo.main_type else &"idle"))
	visual.set_stance(stance if visual.has_anim(stance) else &"idle")
	visual.set_opacity(0.9)

func _weapon_model(item: ItemInstance, wt: WeaponTypeDef) -> String:
	return Player.weapon_model_for(item, wt)

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
	if _fidget_t <= 0.0 and not visual.is_busy() and not hold_fidgets:
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
