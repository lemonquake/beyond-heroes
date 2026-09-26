class_name LootDrop
extends Node3D
## An item or a pile of gold on the ground. Arcs out of the corpse, lands with a rarity-graded presentation:
## glow and sound for everything, a light beam from Advanced up, a particle aura from Elite up, and an unmistakable
## prismatic column, orbiting motes, pulsing light and hum for Aether. Ground labels are drawn by the HUD
## (group "loot"), clickable; gold is collected automatically on contact.

const PICKUP_RANGE := 4.0
const GOLD_RANGE := 1.8
const AUTO_RANGE := 1.6

var item: ItemInstance
var gold := 0
var landed := false
var interact_range := 2.2
var _visual: Node3D
var _light: OmniLight3D
var _t := 0.0
var _hum: AudioStreamPlayer3D

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
	tw.tween_method(func(k: float) -> void:
		var a := from.lerp(mid, k)
		var b := mid.lerp(land, k)
		global_position = a.lerp(b, k)
		if _visual:
			_visual.rotation.y += 0.25, 0.0, 1.0, t)
	tw.tween_callback(_on_land)

func _build_visual() -> void:
	_visual = Node3D.new()
	add_child(_visual)
	var c := color()
	if item and (item.base.is_weapon() or item.base.category == &"shield"):
		var path := "res://assets/weapons/shield.glb" if item.base.category == &"shield" else (DB.weapon_type(item.base.weapon_type).model if DB.weapon_type(item.base.weapon_type) else "")
		if path != "" and ResourceLoader.exists(path):
			var w: Node3D = load(path).instantiate()
			w.rotation = Vector3(PI * 0.5, 0, 0)
			w.position.y = 0.08
			_visual.add_child(w)
			var ms: Array[MeshInstance3D] = []
			for n in w.find_children("*", "MeshInstance3D", true, false):
				ms.append(n)
			MaterialLibrary.apply_character(ms, Color(0.6, 0.2, 0.2))
	if _visual.get_child_count() == 0:
		var mi := MeshInstance3D.new()
		if item == null:
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
		else:
			var bm := SphereMesh.new()
			bm.radius = 0.16
			bm.height = 0.26
			bm.radial_segments = 8
			bm.rings = 4
			mi.mesh = bm
			var pm := StandardMaterial3D.new()
			pm.albedo_color = Color(0.3, 0.22, 0.14)
			pm.roughness = 0.8
			pm.rim_enabled = true
			pm.rim = 0.6
			pm.emission_enabled = true
			pm.emission = c * 0.35
			mi.material_override = pm
			mi.position.y = 0.12
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		_visual.add_child(mi)

func _on_land() -> void:
	landed = true
	var c := color()
	var r := rarity()
	if item == null:
		Audio.play_at(&"gold_pickup", global_position, -8.0)
		return
	Audio.play_at(BH.RARITY_DROP_SOUND[r], global_position, -2.0 if r >= BH.Rarity.ELITE else -6.0)
	_light = OmniLight3D.new()
	_light.light_color = c
	_light.light_energy = 0.4 + 0.25 * r
	_light.omni_range = 1.5 + 0.35 * r
	_light.position.y = 0.4
	add_child(_light)
	var beam_h: float = BH.RARITY_BEAM[r]
	if beam_h > 0.0:
		var b := VFXLib.beam(c, beam_h, 0.22 + 0.03 * r)
		add_child(b)
	if r >= BH.Rarity.ELITE:
		var p := VFXLib.particles(Color(c.r, c.g, c.b, 0.9), 10 + 3 * r, 1.4, false, 0.18, 0.9, 25.0, Vector3(0, 1.2, 0), 0.45)
		p.position.y = 0.1
		add_child(p)
	if r >= BH.Rarity.LEGENDARY:
		add_child(VFXLib.ring_wave(c, 2.5, 0.9, 0.5))
		Events.camera_shake.emit(0.08)
	if r == BH.Rarity.AETHER:
		_aether_presentation()
		Events.notify.emit("An Aether item has appeared!", &"aether")

func _aether_presentation() -> void:
	var prism := [Color(0.55, 0.98, 1.0), Color(0.85, 0.7, 1.0), Color(1.0, 0.95, 0.75)]
	for i in 3:
		var ring := VFXLib.particles(Color(prism[i].r, prism[i].g, prism[i].b, 0.9), 16, 2.0, false, 0.14, 0.4, 180.0, Vector3(0, 0.8 + i * 0.3, 0), 0.8)
		ring.position.y = 0.3 + i * 0.5
		add_child(ring)
	var col := VFXLib.beam(Color(0.9, 1.0, 1.0), 14.0, 0.5)
	add_child(col)
	_hum = Audio.make_loop(&"teleporter_hum", self, -10.0, 16.0)
	FX.spawn(VFXLib.light_flash(Color(0.6, 1.0, 1.0), 8.0, 12.0, 0.8), global_position + Vector3.UP)

func _process(delta: float) -> void:
	_t += delta
	if _visual and item != null and landed:
		_visual.position.y = 0.05 + sin(_t * 2.4) * 0.04 if item.rarity >= BH.Rarity.ELITE else 0.0
	if _light and item and item.rarity >= BH.Rarity.MYTHICAL:
		_light.light_energy = (0.4 + 0.25 * item.rarity) * (0.75 + 0.25 * sin(_t * 3.0))
	if not landed:
		return
	var p := Game.player as Player
	if p == null or not p.alive:
		return
	var d := p.global_position.distance_to(global_position)
	if item == null and d < GOLD_RANGE:
		pick_up(p)
	elif item != null and Settings.auto_loot and item.rarity >= Settings.auto_loot_rarity and d < AUTO_RANGE:
		if p.hero.inventory.can_fit(item):
			pick_up(p)

# ---- Interactable -------------------------------------------------------------------------------------------

func can_interact(_p: Node) -> bool:
	return landed and item != null

func interact_text() -> String:
	return "Pick up %s" % label_text()

func interact_anim() -> StringName:
	return &"interact_pickup"

func interact(p: Node) -> void:
	pick_up(p as Player)

## Clicked on the ground label.
func request_pickup(p: Player) -> void:
	if p.global_position.distance_to(global_position) > PICKUP_RANGE:
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
