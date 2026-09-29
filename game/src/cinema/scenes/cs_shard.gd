extends Cutscene
## bh-021 — the reliquary at Wyman Outpost: Sir Aldric sets down the iron casket, the hero opens it, and the broken
## tip of a black lance lifts out of its oilcloth burning red. For a heartbeat the hero sees something else: a horned
## dragon helm in the dark, its eyes lighting, and a voice. Then the shard is only warm in their hand.

const C_AL := Color(0.55, 0.7, 1.0)

var _at := Transform3D.IDENTITY

func _init() -> void:
	title = "The Sealed Reliquary"
	skip_all = true

func build(cs: CutscenePlayer) -> Array:
	var n := cs.npc(&"aldric")
	if n:
		_at = n.global_transform.orthonormalized()
	elif Game.player:
		_at = (Game.player as Node3D).global_transform
	return [
		{"name": "The Casket", "length": 8.0, "run": _casket},
		{"name": "A Glimpse", "length": 6.0, "run": _vision, "fade_in": 0.0},
		{"name": "Warm in the Hand", "length": 4.5, "run": _hand, "fade_in": 0.3},
	]

func _cast(cs: CutscenePlayer) -> Array:
	cs.use_map(_at)
	var al_node := cs.npc(&"aldric")
	cs.hide_node(al_node)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var al := cs.copy(&"aldric", al_node, Vector3(-0.9, 0, 0.3), 30.0)
	al.play(&"idle", 0.0)
	var hero := cs.hero(&"hero", Vector3(0.3, 0, 2.6), 180.0)
	hero.play(&"idle", 0.0)
	return [al, hero]

func _casket(cs: CutscenePlayer) -> void:
	var c := _cast(cs)
	var hero: CutsceneActor = c[1]
	var box: Node3D = MapBuilder.scene("chest").instantiate()
	cs.fx(box, Vector3(0.3, 0, 1.55))
	MaterialLibrary.apply_environment(box)
	box.rotation.y = _at.basis.get_euler().y + PI
	var shard: Node3D = (load("res://assets/weapons/legend/dusk_piercer_tip.glb") as PackedScene).instantiate()
	var ms: Array[MeshInstance3D] = []
	for m in shard.find_children("*", "MeshInstance3D", true, false):
		ms.append(m)
	MaterialLibrary.apply_character(ms, Color.WHITE)
	cs.fx(shard, Vector3(0.3, 0.45, 1.55))
	shard.rotation = Vector3(deg_to_rad(90), 0, 0)
	shard.scale = Vector3.ONE * 0.5
	shard.visible = false
	var glow := OmniLight3D.new()
	glow.light_color = CSKit.WRATH
	glow.light_energy = 0.0
	glow.omni_range = 4.0
	cs.fx(glow, Vector3(0.3, 0.7, 1.55))
	var aura := LegendFX.wrath_aura(0.0)
	cs.fx(aura, Vector3(0.3, 0.2, 1.55))
	aura.scale = Vector3.ONE * 0.4
	cs.camera([[0.0, Vector3(3.2, 1.9, -0.4), Vector3(-0.2, 1.1, 1.6), 44.0], [2.3, Vector3(2.9, 1.7, 0.0), Vector3(0.2, 0.8, 1.6), 40.0],
		[2.4, Vector3(2.5, 1.45, 1.9), Vector3(0.3, 0.9, 1.55), 38.0, true], [8.0, Vector3(2.1, 1.3, 1.8), Vector3(0.3, 1.05, 1.55), 32.0]])
	cs.say(0.3, "Sir Aldric Vane", "Gently. It bites the ones it does not like.", 2.6, C_AL)
	cs.at(1.2, func() -> void: hero.play(&"interact_chest", 0.2))
	cs.sfx(2.0, &"chest_open", 0.0)
	cs.at(2.4, func() -> void:
		shard.visible = true
		cs.flash(cs.t, CSKit.WRATH, 0.35)
		var tw := cs.tween(shard)
		tw.tween_property(shard, "position", shard.position + Vector3(0, 0.55, 0), 2.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		var tw2 := cs.tween(glow)
		tw2.tween_property(glow, "light_energy", 1.6, 1.2)
		aura.fade_to(0.8, 1.5))
	cs.sfx(2.4, &"dark_cast", 0.0)
	cs.at(4.0, func() -> void:
		var tw := cs.tween(shard)
		tw.tween_property(shard, "rotation:y", TAU, 4.0))
	cs.shake(5.4, 0.4, 2.6)
	cs.fade(7.2, 1.0, 0.7, Color(0.35, 0.0, 0.0))

func _vision(cs: CutscenePlayer) -> void:
	cs.use_flashback("vision", func(root: Node3D) -> void: CSKit.void_set(root))
	cs.vignette(true, 0.2)
	var aj := cs.legend(&"aljay", &"aljay", Vector3.ZERO, 180.0, false)
	aj.play(&"cs_aj_stand", 0.0)
	for p: Array in [[Vector3(-1.2, 1.6, -0.6), 1.2], [Vector3(1.0, 2.2, 0.8), 2.4]]:
		var l := OmniLight3D.new()
		l.light_color = CSKit.WRATH
		l.light_energy = float(p[1])
		l.omni_range = 3.0
		cs.fx(l, p[0])
	cs.fade(0.0, 0.9, 0.0, Color(0.35, 0.0, 0.0))
	cs.fade(0.1, 0.0, 1.4, Color(0.35, 0.0, 0.0))
	cs.camera([[0.0, Vector3(0.35, 1.55, -1.7), Vector3(0.0, 1.95, 0.0), 34.0], [6.0, Vector3(0.25, 1.65, -1.25), Vector3(0.0, 1.98, 0.0), 28.0]])
	cs.at(2.0, func() -> void: cs.flash(cs.t, CSKit.WRATH, 0.4))
	cs.sfx(2.0, &"boss_roar", -6.0)
	cs.say(2.4, "???", "...Malasugue...", 2.4, CSKit.WRATH)
	cs.shake(2.0, 0.5, 2.0)
	cs.fade(4.8, 1.0, 1.0, Color.WHITE)

func _hand(cs: CutscenePlayer) -> void:
	cs.vignette(false, 0.2)
	var c := _cast(cs)
	var hero: CutsceneActor = c[1]
	hero.detach(&"main")
	hero.play(&"interact_teleport", 0.2, 0.6)
	CSKit.shard_in_hand(hero, "weapon.R", 3.0)
	cs.fade(0.0, 1.0, 0.0, Color.WHITE)
	cs.fade(0.0, 0.0, 1.0, Color.WHITE)
	var h := Vector3(0.3, 1.5, 2.6)
	cs.camera([[0.0, Vector3(2.4, 1.7, 0.7), h, 42.0], [4.5, Vector3(2.0, 1.65, 1.0), h, 36.0]])
