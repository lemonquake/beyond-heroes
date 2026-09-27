class_name CampBonfire
extends Node3D
## A camp checkpoint (bh-007, Wyman Outpost): resting here is free — full HP and Mana, harmful effects cleansed,
## Tempos restored — and makes this camp the hero's checkpoint. After a death the hero may choose to wake here
## instead of at the entrance of the map they fell on (PauseMenu / Game.respawn_at_checkpoint).

var camp_name := "Wyman Outpost"
var spawn_id: StringName = &"bonfire"
var interact_range := 3.4
var _plate: Label3D

func setup(p_name: String, p_spawn: StringName) -> CampBonfire:
	camp_name = p_name
	spawn_id = p_spawn
	name = "Bonfire_%s" % p_spawn
	return self

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"checkpoint")
	_plate = Label3D.new()
	_plate.text = "%s Bonfire\n[Rest · Checkpoint]" % camp_name
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 24
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.GOLD
	_plate.position.y = 3.0
	_plate.visible = false
	add_child(_plate)

func _process(_d: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 10.0

func is_current() -> bool:
	return Game.hero != null and String(Game.hero.checkpoint.get("map", "")) == String(Game.current_map_id) \
		and String(Game.hero.checkpoint.get("spawn", "")) == String(spawn_id)

func can_interact(p: Node) -> bool:
	return not Game.travelling and p is Player and (p as Player).alive

func interact_text() -> String:
	return "Rest at the bonfire" + (" (your checkpoint)" if is_current() else " · set checkpoint")

func interact_anim() -> StringName:
	return &""

func interact(p: Node) -> void:
	if Game.ui_root == null:
		rest(Game.hero, p)
		return
	Game.ui_root.fade_rest("You rest by the fire at %s..." % camp_name, func() -> void: rest(Game.hero, p), 0.7)

## Restore, cleanse, restore Tempos and set the checkpoint (free). Returns "".
func rest(hero: HeroData, p: Node) -> String:
	if hero == null:
		return "No hero"
	var first := not is_current()
	hero.checkpoint = {"map": String(Game.current_map_id), "spawn": String(spawn_id), "name": camp_name}
	if p is Player and (p as Player).alive:
		NpcServices.heal(p)
	TempoRules.restore_all(hero)
	for t in TempoParty.actors():
		if t is Tempo and t.alive:
			t.hp = t.max_hp()
			t.mana = t.max_mana()
			t.status.cleanse_harmful()
	if first:
		Events.notify.emit("Checkpoint set: %s" % camp_name, &"info")
	Game.save_now()
	return ""
