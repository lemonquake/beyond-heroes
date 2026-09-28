class_name TreasureChest
extends Node3D
## A dungeon treasure chest (bh-012). Interact opens it: the lid swings up, gold and gear burst out (Loot.drop_chest),
## a Relic Cache sometimes among them. The hero remembers when each chest was opened (HeroData.chest_log, keyed
## "map/n"), and a looted chest refills after `respawn` seconds of play time.
## Tiers: 0 = a plain coffer, 1 = a gilded chest (upper galleries), 2 = the hoard behind a dungeon boss.

const LOOK := [
	{"tint": Color(0.62, 0.48, 0.32), "glow": Color(1.0, 0.8, 0.45), "name": "Coffer"},
	{"tint": Color(0.85, 0.66, 0.3), "glow": Color(1.0, 0.75, 0.3), "name": "Gilded Chest"},
	{"tint": Color(0.75, 0.55, 1.0), "glow": Color(0.8, 0.55, 1.0), "name": "Hoard"},
]

var tier := 0
var key := ""
var level := 1
var respawn := 1800.0
var interact_range := 2.2
var _lid: Node3D
var _glow: OmniLight3D
var _motes: GPUParticles3D
var _busy := false

func setup(p_tier: int, p_key: String, p_level: int, p_respawn: float) -> TreasureChest:
	tier = clampi(p_tier, 0, LOOK.size() - 1)
	key = p_key
	level = p_level
	respawn = p_respawn
	name = "Chest_%s" % p_key.get_file()
	return self

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"treasure_chest")
	var look: Dictionary = LOOK[tier]
	var scene: PackedScene = load("res://assets/environment/chest.glb")
	var body := scene.instantiate()
	add_child(body)
	MaterialLibrary.apply_environment(body)
	# the chest model is one piece: the lid is a box that swings on the back edge
	var sc := 1.0 + 0.18 * tier
	body.scale = Vector3.ONE * sc
	var hinge := Node3D.new()
	hinge.position = Vector3(0, 0.62 * sc, -0.34 * sc)
	add_child(hinge)
	_lid = MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.02, 0.14, 0.7) * sc
	(_lid as MeshInstance3D).mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = look.tint
	m.metallic = 0.6 if tier > 0 else 0.2
	m.roughness = 0.45
	(_lid as MeshInstance3D).material_override = m
	_lid.position = Vector3(0, 0.07 * sc, 0.34 * sc)
	hinge.add_child(_lid)
	_lid = hinge
	_glow = OmniLight3D.new()
	_glow.light_color = look.glow
	_glow.light_energy = 1.2 + 0.4 * tier
	_glow.omni_range = 4.0
	_glow.position = Vector3(0, 1.1, 0.4)
	add_child(_glow)
	_motes = VFXLib.particles(Color(look.glow.r, look.glow.g, look.glow.b, 0.8), 10 + 6 * tier, 1.6, false, 0.12, 0.6, 30.0,
		Vector3(0, 0.5, 0), 0.5)
	_motes.position = Vector3(0, 0.8, 0)
	add_child(_motes)
	_refresh()

func opened_at() -> float:
	if Game.hero == null:
		return -INF
	return float(Game.hero.chest_log.get(key, -INF))

func is_ready() -> bool:
	return Game.hero == null or Game.hero.play_time >= opened_at() + respawn

func _process(_d: float) -> void:
	if not _busy and _lid.rotation.x < -0.1 and is_ready():
		_refresh()

func _refresh() -> void:
	var r := is_ready()
	_lid.rotation.x = 0.0 if r else -1.9
	_glow.visible = r
	_motes.emitting = r

func can_interact(_p: Node) -> bool:
	return is_ready() and not _busy and not Game.travelling

func interact_text() -> String:
	return "Open the %s" % LOOK[tier].name

func interact_anim() -> StringName:
	return &"interact_chest"

func interact(_p: Node) -> void:
	open(Game.hero)

## Open the chest: remember it, animate the lid, throw out the loot. Returns false when it is still empty.
func open(hero: HeroData) -> bool:
	if hero == null or not is_ready() or _busy:
		return false
	_busy = true
	hero.chest_log[key] = hero.play_time
	Audio.play_at(&"chest_open" if Audio.has_sound(&"chest_open") else &"break_wood", global_position, -2.0)
	var tw := create_tween()
	tw.tween_property(_lid, "rotation:x", -1.9, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if is_inside_tree():
		add_child(VFXLib.light_flash(LOOK[tier].glow, 6.0 + 3.0 * tier, 8.0, 0.5))
	Loot.drop_chest(tier, level, global_position + Vector3(0, 0.3, 0) + global_basis.z * 0.9, hero)
	_glow.visible = false
	_motes.emitting = false
	_busy = false
	return true
