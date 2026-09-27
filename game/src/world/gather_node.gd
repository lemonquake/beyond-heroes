class_name GatherNode
extends Node3D
## A herb patch (bh-007): Interact picks 1–3 of its herb (Silverleaf, Mirebloom, Emberroot, Brightcap). A picked patch
## shows bare stems and regrows after REGROW seconds of play time; the hero remembers which patches were picked
## (HeroData.gather_log, keyed "map/node name") so leaving and coming back does not refill them.

const REGROW := 300.0
const LOOK := {
	&"silverleaf": {"leaf": Color(0.72, 0.82, 0.74), "flower": Color(0.92, 0.95, 0.9), "label": "Silverleaf"},
	&"mirebloom": {"leaf": Color(0.25, 0.45, 0.3), "flower": Color(0.35, 0.55, 1.0), "label": "Mirebloom"},
	&"emberroot": {"leaf": Color(0.38, 0.3, 0.18), "flower": Color(1.0, 0.36, 0.18), "label": "Emberroot"},
	&"brightcap": {"leaf": Color(0.5, 0.42, 0.32), "flower": Color(0.6, 1.0, 0.75), "label": "Brightcap"},
}

var herb: StringName = &"silverleaf"
var key := ""                       # "map/name", set when placed
var interact_range := 2.2
var _leaves: Node3D
var _glow: MeshInstance3D
var _rng := RandomNumberGenerator.new()

func setup(p_herb: StringName, p_key: String) -> GatherNode:
	herb = p_herb
	key = p_key
	name = "Herb_%s" % p_key.get_file()
	return self

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"gather_node")
	_rng.seed = hash(key)
	var look: Dictionary = LOOK.get(herb, LOOK[&"silverleaf"])
	var stem_mat := StandardMaterial3D.new()
	stem_mat.albedo_color = (look.leaf as Color).darkened(0.3)
	stem_mat.roughness = 0.9
	# stems stay; leaves and flowers (the pickable part) come and go
	for i in 5:
		var st := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.012
		cm.bottom_radius = 0.02
		cm.height = 0.28
		st.mesh = cm
		st.material_override = stem_mat
		var a := TAU * i / 5.0 + _rng.randf() * 0.5
		st.position = Vector3(cos(a) * 0.14, 0.14, sin(a) * 0.14)
		st.rotation = Vector3(_rng.randf_range(-0.3, 0.3), 0, _rng.randf_range(-0.3, 0.3))
		add_child(st)
	_leaves = Node3D.new()
	add_child(_leaves)
	var leaf_mat := StandardMaterial3D.new()
	leaf_mat.albedo_color = look.leaf
	leaf_mat.roughness = 0.8
	var flower_mat := StandardMaterial3D.new()
	flower_mat.albedo_color = look.flower
	flower_mat.emission_enabled = true
	flower_mat.emission = look.flower
	flower_mat.emission_energy_multiplier = 0.9 if herb == &"brightcap" else 0.45
	for i in 9:
		var lf := MeshInstance3D.new()
		var pm: Mesh = PrismMesh.new() if herb != &"brightcap" else SphereMesh.new()
		if pm is PrismMesh:
			(pm as PrismMesh).size = Vector3(0.09, 0.22, 0.02)
		else:
			(pm as SphereMesh).radius = 0.07
			(pm as SphereMesh).height = 0.06
		lf.mesh = pm
		lf.material_override = leaf_mat if i % 3 != 0 else flower_mat
		var a := TAU * i / 9.0 + _rng.randf() * 0.4
		var r := _rng.randf_range(0.05, 0.22)
		lf.position = Vector3(cos(a) * r, 0.2 + _rng.randf() * 0.14, sin(a) * r)
		lf.rotation = Vector3(_rng.randf_range(-0.6, 0.6), a, _rng.randf_range(-0.4, 0.4))
		_leaves.add_child(lf)
	# a soft glow sprite instead of a light (dozens of patches must not add dozens of lights)
	_glow = MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(0.9, 0.9)
	_glow.mesh = qm
	_glow.material_override = VFXLib.glow_material(look.flower, 0.8)
	_glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_glow.rotation.x = -PI * 0.5
	_glow.position.y = 0.05
	add_child(_glow)
	_refresh()

func picked_at() -> float:
	if Game.hero == null:
		return -INF
	return float(Game.hero.gather_log.get(key, -INF))

func is_ready() -> bool:
	return Game.hero == null or Game.hero.play_time >= picked_at() + REGROW

func _process(_d: float) -> void:
	# cheap: only flips when it regrows
	if not _leaves.visible and is_ready():
		_refresh()

func _refresh() -> void:
	var r := is_ready()
	_leaves.visible = r
	_glow.visible = r

func can_interact(_p: Node) -> bool:
	return is_ready() and not Game.travelling

func interact_text() -> String:
	return "Gather %s" % LOOK.get(herb, {}).get("label", String(herb))

func interact_anim() -> StringName:
	return &"interact_pickup"

func interact(_p: Node) -> void:
	gather(Game.hero)

## Pick the patch: returns how many herbs went into the bag (0 when not ready or the bag is full).
func gather(hero: HeroData) -> int:
	if hero == null or not is_ready():
		return 0
	var n := _rng.randi_range(1, 3)
	var it := DB.make_item(herb, BH.Rarity.COMMON, 1, _rng.randi() | 1)
	it.count = n
	if not hero.inventory.can_fit(it):
		Events.notify.emit("Inventory is full", &"error")
		return 0
	hero.inventory.add(it)
	hero.gather_log[key] = hero.play_time
	_refresh()
	Audio.play_at(&"loot_pickup" if Audio.has_sound(&"loot_pickup") else &"ui_click", global_position, -6.0)
	Events.notify.emit("+%d %s" % [n, LOOK.get(herb, {}).get("label", String(herb))], &"loot")
	Events.herb_gathered.emit(herb, n)
	return n
