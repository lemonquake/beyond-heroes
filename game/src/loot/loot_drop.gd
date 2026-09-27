class_name LootDrop
extends Node3D
## An item or a pile of gold on the ground. Arcs out of the corpse and lands as the item's own 3D model (laid flat for
## weapons and shields), sparkling in its rarity colour: twinkling stars, a soft pulsing ground glow and a glint that
## sweeps over the model. Higher tiers sparkle more, bigger and brighter; Mythical+ breathe rising motes, Legendary+
## land with a shock ring and Aether sparkles cycle through a prism and hum. (No light beams since bh-006.)
## Ground labels are drawn by the HUD (group "loot"), clickable; gold is collected automatically on contact.

const PICKUP_RANGE := 4.0
const GOLD_RANGE := 1.8
const AUTO_RANGE := 2.4
const MAGNET_TIME := 0.22

var item: ItemInstance
var gold := 0
var landed := false
var interact_range := 2.4
var _visual: Node3D
var _model: Node3D
var _light: OmniLight3D
var _t := 0.0
var _hum: AudioStreamPlayer3D
var _collecting := false
var _auto_check := 0.0

func _ready() -> void:
	add_to_group(&"loot")
	add_to_group(&"interactable")

func color() -> Color:
	return BH.rarity_color(item.rarity) if item else Color(1.0, 0.82, 0.3)

func label_text() -> String:
	if item == null:
		return "%d Gold" % gold
	if item.count > 1:
		return "%s (%d)" % [item.display_name(), item.count]
	return item.display_name()

func rarity() -> int:
	return item.rarity if item else -1

func launch(from: Vector3, land: Vector3) -> void:
	global_position = from
	_build_visual()
	var mid := (from + land) * 0.5 + Vector3.UP * 1.6
	var tw := create_tween()
	var t := 0.45
	var spin := randf_range(8.0, 14.0) * (1.0 if randf() < 0.5 else -1.0)
	tw.tween_method(func(k: float) -> void:
		var a := from.lerp(mid, k)
		var b := mid.lerp(land, k)
		global_position = a.lerp(b, k)
		if _visual:
			_visual.rotation.y += spin * 0.016
			_visual.rotation.x = sin(k * PI) * 0.6, 0.0, 1.0, t)
	tw.tween_callback(_on_land)

func _build_visual() -> void:
	_visual = Node3D.new()
	add_child(_visual)
	if item == null:
		_model = ItemModels.gold_instance(randf() * TAU)
		if _model == null:
			_model = _gold_fallback()
		# bigger piles look bigger
		_model.scale = Vector3.ONE * clampf(0.8 + log(1.0 + float(gold)) * 0.08, 0.8, 1.35)
	else:
		_model = ItemModels.ground_instance(item.base, randf() * TAU)
	_visual.add_child(_model)
	for mi in _model.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON

func _gold_fallback() -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.16
	cm.bottom_radius = 0.2
	cm.height = 0.12
	mi.mesh = cm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(1.0, 0.78, 0.25)
	gm.metallic = 1.0
	gm.roughness = 0.25
	gm.emission_enabled = true
	gm.emission = Color(0.6, 0.4, 0.05)
	mi.material_override = gm
	mi.position.y = 0.06
	root.add_child(mi)
	return root

## Footprint radius of the landed model (sparkles and glow are sized to it).
func _footprint() -> float:
	if _model == null:
		return 0.3
	var bb := ItemModels.bounds(_model)
	return clampf(maxf(bb.size.x, bb.size.z) * 0.5, 0.18, 0.9)

func _on_land() -> void:
	landed = true
	if _visual:
		_visual.rotation.x = 0.0
	var r := rarity()
	if item == null:
		Audio.play_at(&"gold_pickup", global_position, -8.0)
		var gs := LootFx.sparkles(BH.Rarity.ELITE, 0.22, 0.25)
		gs.amount = 5
		add_child(gs)
		return
	Audio.play_at(BH.RARITY_DROP_SOUND[r], global_position, -2.0 if r >= BH.Rarity.ELITE else -6.0)
	var rad := _footprint()
	var h := clampf(ItemModels.bounds(_model).size.y + 0.25, 0.3, 0.9)
	add_child(LootFx.ground_glow(r, rad * 0.85 + 0.22 + 0.02 * r))
	add_child(LootFx.sparkles(r, rad + 0.1, h))
	LootFx.add_glint(_model, r)
	if r >= BH.Rarity.ELITE:
		_light = OmniLight3D.new()
		_light.light_color = color()
		_light.light_energy = 0.25 + 0.12 * r
		_light.omni_range = 1.4 + 0.2 * r
		_light.position.y = 0.45
		_light.shadow_enabled = false
		add_child(_light)
	if r >= BH.Rarity.MYTHICAL:
		var m := LootFx.motes(r, rad)
		m.position.y = 0.1
		add_child(m)
	if r >= BH.Rarity.LEGENDARY:
		add_child(VFXLib.ring_wave(color(), 2.5, 0.9, 0.5))
		FX.spawn(VFXLib.particles(color(), 30, 0.7, true, 0.12, 3.5, 70.0, Vector3(0, -3, 0), 0.2), global_position + Vector3.UP * 0.3)
		Events.camera_shake.emit(0.08)
	if r == BH.Rarity.AETHER:
		_aether_presentation()
		Events.notify.emit("An Aether item has appeared!", &"aether")

func _aether_presentation() -> void:
	var prism := [Color(0.55, 0.98, 1.0), Color(0.85, 0.7, 1.0), Color(1.0, 0.95, 0.75)]
	for i in 3:
		var ring := LootFx.small_particles(Color(prism[i].r, prism[i].g, prism[i].b, 0.9), 10, 1.6, 0.08, 0.3, 180.0, Vector3(0, 0.5, 0), 0.6)
		ring.position.y = 0.2 + i * 0.25
		add_child(ring)
	_hum = Audio.make_loop(&"teleporter_hum", self, -14.0, 12.0)
	FX.spawn(VFXLib.light_flash(Color(0.6, 1.0, 1.0), 8.0, 10.0, 0.8), global_position + Vector3.UP)

func _process(delta: float) -> void:
	_t += delta
	if _collecting:
		return
	if _visual and item != null and landed:
		# Elite and above hover a hand's breadth and turn slowly, the rest rest on the ground
		if item.rarity >= BH.Rarity.ELITE:
			_visual.position.y = 0.08 + sin(_t * 2.2) * 0.035
			_visual.rotation.y += delta * 0.5
	if _light and item and item.rarity >= BH.Rarity.MYTHICAL:
		_light.light_energy = (0.25 + 0.12 * item.rarity) * (0.75 + 0.25 * sin(_t * 3.0))
	if not landed:
		return
	var p := Game.player as Player
	if p == null or not p.alive:
		return
	var d := p.interact_distance(self)
	if item == null and d < GOLD_RANGE:
		pick_up(p)
		return
	_auto_check -= delta
	if item != null and _auto_check <= 0.0 and d < AUTO_RANGE:
		_auto_check = 0.25
		if wants_auto_loot(p):
			_magnet(p)

## Auto-loot (HUD checkbox): on, matching the rarity filter, room in the bag and not pushing the hero past full load.
func wants_auto_loot(p: Player) -> bool:
	if item == null or not Settings.auto_loot or item.rarity < Settings.auto_loot_rarity:
		return false
	if not p.hero.inventory.can_fit(item):
		return false
	if p.stats and p.stats.get_stat(&"carry_weight") + item.weight() > p.stats.get_stat(&"carry_capacity"):
		return false
	return true

## The drop flies into the hero, then is picked up (auto-loot).
func _magnet(p: Player) -> void:
	_collecting = true
	remove_from_group(&"interactable")
	var start := global_position
	var tw := create_tween()
	tw.tween_method(func(k: float) -> void:
		if not is_instance_valid(p):
			return
		var target := p.global_position + Vector3.UP * 1.0
		global_position = start.lerp(target, k * k) + Vector3.UP * sin(k * PI) * 0.6
		if _visual:
			_visual.scale = Vector3.ONE * (1.0 - 0.6 * k), 0.0, 1.0, MAGNET_TIME)
	tw.tween_callback(func() -> void:
		if not pick_up(p):
			# the bag filled up in the meantime: drop back where it was
			_collecting = false
			global_position = start
			if _visual:
				_visual.scale = Vector3.ONE
			add_to_group(&"interactable"))

# ---- Interactable -------------------------------------------------------------------------------------------

func can_interact(_p: Node) -> bool:
	return landed and item != null and not _collecting

func interact_text() -> String:
	return "Pick up %s" % label_text()

func interact_anim() -> StringName:
	return &"interact_pickup"

func interact(p: Node) -> void:
	pick_up(p as Player)

## Clicked on the ground label.
func request_pickup(p: Player) -> void:
	if p.interact_distance(self) > PICKUP_RANGE:
		Events.notify.emit("Too far away", &"error")
		return
	p.visual.play_action(&"interact_pickup", 1.4)
	pick_up(p)

func pick_up(p: Player) -> bool:
	if p == null or not landed or is_queued_for_deletion():
		return false
	if item == null:
		p.hero.inventory.gold += gold
		p.hero.inventory.changed.emit()
		Events.gold_picked.emit(gold)
		Audio.play_ui(&"gold_pickup")
		FX.text_popup(global_position + Vector3.UP, "+%d gold" % gold, Color(1.0, 0.82, 0.3), 0.8)
		_remove()
		return true
	var left := p.hero.inventory.add(item)
	if left > 0:
		Events.notify.emit("Inventory is full", &"error")
		Audio.play_ui(&"ui_error")
		return false
	Events.loot_picked.emit(item)
	Audio.play_ui(&"item_pickup")
	_remove()
	return true

func _remove() -> void:
	if Game.hover_loot == self:
		Game.hover_loot = null
	remove_from_group(&"loot")
	remove_from_group(&"interactable")
	queue_free()
