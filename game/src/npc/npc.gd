class_name Npc
extends StaticBody3D
## A townsperson in the world: solid body, animated model, name plate, and the interactable interface the Player uses
## (can_interact / interact / interact_text / interact_anim). Talking turns them toward the hero and plays gestures;
## the conversation itself runs in DialogueSession and is shown by the UI (Events.talk_requested).

const TURN_RATE := 5.0

var def: NpcDef
var visual: CharacterVisual
var interact_range := 2.8
var talking := false
var _home_yaw := 0.0
var _face_target: Node3D
var _plate: Label3D
var _fidget_t := 0.0
var _rng := RandomNumberGenerator.new()

func setup(p_def: NpcDef) -> Npc:
	def = p_def
	name = "Npc_%s" % def.id
	_home_yaw = deg_to_rad(def.yaw)
	_rng.seed = hash(String(def.id))
	return self

func _ready() -> void:
	add_to_group(&"interactable")
	add_to_group(&"npc")
	collision_layer = BH.LAYER_PROPS
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.38
	cap.height = 1.8
	cs.shape = cap
	cs.position.y = 0.9
	add_child(cs)
	rotation.y = _home_yaw
	visual = CharacterVisual.new()
	visual.name = "Visual"
	add_child(visual)
	var personality := &"mage" if def.model.ends_with("mage.glb") else &"knight"
	visual.setup(def.model, def.model_scale, def.tint, personality)
	visual.set_stance(&"idle")
	_plate = Label3D.new()
	_plate.text = "%s\n[%s]" % [def.display_name, def.title] if def.title != "" else def.display_name
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 24
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.GOLD
	_plate.no_depth_test = false
	_plate.position.y = 2.25 * def.model_scale
	_plate.visible = false
	add_child(_plate)
	_fidget_t = _rng.randf_range(4.0, 9.0)

func _process(delta: float) -> void:
	if visual == null:
		return
	visual.update_locomotion(Vector2.ZERO, false, 0.0, delta)
	# turn toward the hero while talking, back to the post afterwards
	var want := _home_yaw
	if _face_target and is_instance_valid(_face_target):
		var d := _face_target.global_position - global_position
		if Vector2(d.x, d.z).length() > 0.2:
			want = atan2(d.x, d.z)
	rotation.y = lerp_angle(rotation.y, want, 1.0 - exp(-TURN_RATE * delta))
	# ambient idles from the NPC's own set
	if not talking:
		_fidget_t -= delta
		if _fidget_t <= 0.0:
			_fidget_t = _rng.randf_range(7.0, 14.0)
			var extra: Array = def.idle_anims.filter(func(a): return a != &"idle" and visual.has_anim(a))
			if not extra.is_empty() and not visual.is_busy():
				visual.play_action(extra[_rng.randi_range(0, extra.size() - 1)], 1.0)
	# the name plate shows when the hero is near
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 9.0

# ---- Interactable ------------------------------------------------------------------------------------------------

func can_interact(_p: Node) -> bool:
	return not talking

func interact_text() -> String:
	return "Talk to %s" % def.display_name

func interact_anim() -> StringName:
	return &""

func interact(p: Node) -> void:
	begin_talk(p as Node3D)
	Events.talk_requested.emit(self)

func begin_talk(p: Node3D) -> void:
	talking = true
	_face_target = p
	if visual.has_anim(&"interact_talk"):
		visual.play_action(&"interact_talk", 1.0)
	if def.greeting_sound != &"":
		Audio.play_at(def.greeting_sound, global_position)

func gesture() -> void:
	if visual.has_anim(&"interact_talk") and not visual.is_busy():
		visual.play_action(&"interact_talk", 1.0)

func end_talk() -> void:
	talking = false
	_face_target = null
