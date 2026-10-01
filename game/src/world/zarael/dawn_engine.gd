class_name DawnEngine
extends Node3D
## bh-029: the Dawn Engine in the Heart Citadel (DataZarael.HC_ENGINE). The map places the model (`zr_dawn_engine`, with
## child rings `ring_1..3`) and hands it to setup(); this node spins the rings (slow and dim while chained, fast and
## bright once woken) and is the interactable that ends the quest: once the Leash-Abbot has fallen the hero lays a hand on
## it — cutscene `dawn_current` — and the Heartwire burns bright all over Zarael (`zr_heartwire_restored`).

var interact_range := 6.5
var _rings: Array[Node3D] = []
var _axes: Array[Vector3] = []
var _light: OmniLight3D
var _plate: Label3D
var _busy := false

func setup(model: Node3D) -> DawnEngine:
	name = "DawnEngine"
	if model:
		for i in 3:
			var r := model.find_child("ring_%d" % (i + 1), true, false) as Node3D
			if r:
				_rings.append(r)
				_axes.append(r.transform.basis.y.normalized())
	return self

func woken() -> bool:
	return Game.has_flag(DataZarael.F_RESTORED)

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"dawn_engine")
	_light = OmniLight3D.new()
	_light.omni_range = 22.0
	_light.position = Vector3(0, 7.0, 0)
	add_child(_light)
	_plate = Label3D.new()
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.no_depth_test = true
	_plate.render_priority = 8
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.PARCHMENT
	_plate.position.y = 13.5
	add_child(_plate)
	_refresh()
	Events.world_flag_set.connect(func(f: StringName, _v: Variant) -> void:
		if f == DataZarael.F_RESTORED or f == DataZarael.F_ABBOT:
			_refresh())

func _refresh() -> void:
	var gold := woken()
	_light.light_color = Color.WHITE
	_light.light_energy = 3.6 if gold else 2.6
	if gold:
		_plate.text = "The Dawn Engine\n[awake]"
	elif Game.has_flag(DataZarael.F_ABBOT):
		_plate.text = "The Dawn Engine\n[its chains hang loose]"
	else:
		_plate.text = "The Dawn Engine\n[chained by the Leash-Abbot]"

func _process(delta: float) -> void:
	var speed := 0.9 if woken() else 0.18
	for i in _rings.size():
		if is_instance_valid(_rings[i]):
			_rings[i].rotate(_axes[i], delta * speed * (1.0 + 0.35 * i) * (1.0 if i % 2 == 0 else -1.0))
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 24.0

func can_interact(_p: Node) -> bool:
	return not Game.travelling and not woken() and not _busy and Game.has_flag(DataZarael.F_ABBOT)

func interact_text() -> String:
	return "Wake the Dawn Engine"

func interact_anim() -> StringName:
	return &"interact_teleport"

func interact(_p: Node) -> void:
	if not can_interact(_p):
		if not Game.has_flag(DataZarael.F_ABBOT):
			Events.notify.emit("The Leash-Abbot's chains hold the Engine. End him first.", &"warning")
		return
	_busy = true
	var hero := Game.hero
	CutscenePlayer.play(&"dawn_current", func() -> void:
		_busy = false
		if Game.hero == hero and not DataZarael.has(hero, DataZarael.F_RESTORED):
			Game.set_world_flag(DataZarael.F_RESTORED, true)
			hero.progress.add_xp(20000)
			Events.xp_gained.emit(20000))
