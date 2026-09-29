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
# bh-007 hero NPCs: activity state
var _act_t := 0.0
var _pace_dir := 1.0
var _pace_wait := 0.0
var _home := Vector3.ZERO
var _emblem: Sprite3D

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
	# fidget set from the body: the hero models carry class idles; townsfolk only have idle_look / idle_adjust
	var personality := &"townsfolk"
	if def.model.ends_with("mage.glb"):
		personality = &"mage"
	elif def.model.ends_with("knight.glb"):
		personality = &"knight"
	visual.setup(def.model, def.model_scale, def.tint, personality)
	visual.set_stance(&"idle")
	_arm()
	_plate = Label3D.new()
	_plate.text = plate_text()
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 24
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = UITheme.GOLD
	_plate.no_depth_test = true
	_plate.render_priority = 8
	_plate.position.y = 2.25 * def.model_scale
	_plate.visible = false
	add_child(_plate)
	if def.is_hero():
		_plate.modulate = (DataGuilds.tier(def.hero_tier).color as Color).lerp(UITheme.GOLD, 0.35)
		_emblem = Sprite3D.new()
		_emblem.texture = UIArt.tex(DataGuilds.emblem_path(def.hero_tier)) if def.hero_tier > 0 else null
		_emblem.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_emblem.no_depth_test = true
		_emblem.fixed_size = true
		# about 40 px tall on screen, sitting just above the plate's two lines (the plate uses 0.0008 per font pixel)
		var th := float(_emblem.texture.get_height()) if _emblem.texture else 64.0
		_emblem.pixel_size = 0.0008 * 40.0 / th
		_emblem.offset = Vector2(0, (40.0 + 34.0) * th / 40.0 * 0.5 + th * 0.5)
		_emblem.position.y = _plate.position.y
		_emblem.visible = false
		add_child(_emblem)
	_fidget_t = _rng.randf_range(4.0, 9.0)
	_act_t = _rng.randf_range(0.5, 3.0)
	_settle.call_deferred()

## Safety net: once the physics space has stepped, stand exactly on this map's ground (never on a neighbour's).
func _settle() -> void:
	if not is_inside_tree():
		return
	await get_tree().physics_frame
	var map := _map_root()
	if map == null or not is_inside_tree() or def == null:
		return
	global_position.y = map.global_position.y + NpcDirectory.ground_height(map, def.position)
	_home = global_position

## Name plate: townsfolk show their title; heroes show level, tier and guild (bh-007).
func plate_text() -> String:
	if def.is_hero():
		var g := DataGuilds.guild(def.hero_guild)
		var tier := ("Class %s" % DataGuilds.letter(def.hero_tier)) if def.hero_tier > 0 else "Unranked"
		return "%s\nLv %d · %s · %s" % [def.display_name, def.hero_level, tier, String(g.get("short", "Independent")) if not g.is_empty() else "Independent"]
	return "%s\n[%s]" % [def.display_name, def.title] if def.title != "" else def.display_name

## Heroes carry their weapons (item models in the hand sockets) and stand in that weapon's stance.
func _arm() -> void:
	for pair in [[&"main", def.weapon], [&"off", def.offhand]]:
		if pair[1] == &"":
			continue
		var b := DB.item_base(pair[1])
		if b and b.model_path() != "":
			visual.attach_weapon(pair[0], b.model_path())
	if def.weapon != &"":
		var b2 := DB.item_base(def.weapon)
		if b2:
			var stance: StringName = {&"staff": &"idle_staff", &"wand": &"idle_wand", &"bow": &"idle_bow", &"spear": &"idle_spear",
				&"greatsword": &"idle_2h", &"greataxe": &"idle_2h", &"dagger": &"idle_dagger"}.get(b2.weapon_type, &"idle_1h")
			if visual.has_anim(stance):
				visual.set_stance(stance)

## Camp activities (hero NPCs): swing at a dummy, practise a spell, or pace a patrol line.
func _activity(delta: float) -> void:
	match def.activity:
		&"spar", &"cast":
			_act_t -= delta
			if _act_t <= 0.0 and not visual.is_busy():
				var b := DB.item_base(def.weapon) if def.weapon != &"" else null
				var wt: StringName = b.weapon_type if b else &"sword"
				var pre: String = {&"greatsword": "gs", &"greataxe": "gs", &"axe": "axe", &"club": "axe", &"spear": "spear", &"javelin": "spear",
					&"dagger": "dagger", &"claw": "dagger", &"knuckles": "dagger", &"staff": "staff", &"wand": "wand", &"bow": "bow"}.get(wt, "sword")
				var clip := StringName("%s_%d" % [pre, _rng.randi_range(1, 2 if pre == "bow" else 4)])
				if def.activity == &"cast":
					clip = [&"cast_quick", &"cast_area", &"cast_weapon"][_rng.randi_range(0, 2)]
				if visual.has_anim(clip):
					visual.play_action(clip, 1.0)
				_act_t = _rng.randf_range(1.4, 3.2)
		&"pace":
			if _pace_wait > 0.0:
				_pace_wait -= delta
				visual.update_locomotion(Vector2.ZERO, false, 0.0, delta)
				return
			var map := _map_root()
			var target := _home if _pace_dir < 0.0 else (map.to_global(def.pace_to) if map else _home)
			var d := target - global_position
			d.y = 0.0
			if d.length() < 0.3:
				_pace_dir = -_pace_dir
				_pace_wait = _rng.randf_range(2.0, 5.0)
				visual.update_locomotion(Vector2.ZERO, false, 0.0, delta)
				return
			global_position += d.normalized() * 1.3 * delta
			if map:
				global_position.y = map.global_position.y + NpcDirectory.ground_height(map, map.to_local(global_position))
			rotation.y = lerp_angle(rotation.y, atan2(d.x, d.z), 1.0 - exp(-6.0 * delta))
			visual.update_locomotion(Vector2(0, 1.3), false, 1.3, delta)

func _map_root() -> MapRoot:
	var n := get_parent()
	while n != null and not (n is MapRoot):
		n = n.get_parent()
	return n as MapRoot

func _process(delta: float) -> void:
	if visual == null:
		return
	var pacing := not talking and def.activity == &"pace" and _home != Vector3.ZERO and def.pace_to != Vector3.ZERO
	if pacing:
		_activity(delta)
	else:
		visual.update_locomotion(Vector2.ZERO, false, 0.0, delta)
		if not talking and (def.activity == &"spar" or def.activity == &"cast"):
			_activity(delta)
	# turn toward the hero while talking, back to the post afterwards
	var want := _home_yaw if not pacing else rotation.y
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
	if _emblem:
		_emblem.visible = _plate.visible

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
