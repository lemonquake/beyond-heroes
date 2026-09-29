extends Cutscene
## bh-021 — the hero steps into the Drowned Tollhouse. Kethrax is waiting in the Legion's circle, dragging his chains
## over the stones; he smells the shard, rises, throws his chains down and names himself. The real boss waits unseen
## (frozen and hidden) while his actor has the stage, and takes it back when the cutscene ends.

const C_KX := Color(0.75, 0.55, 1.0)
const BOSS := Vector3(6.0, 0, 0)

var _map := Transform3D.IDENTITY

func _init() -> void:
	title = "The Chain-Marshal"
	skip_all = true
	music = &"music_boss"

func build(cs: CutscenePlayer) -> Array:
	if Game.current_map:
		_map = Game.current_map.global_transform
	cs.hide_node(StoryDirector.map_boss(&"kethrax"))
	return [
		{"name": "The Drowned Tollhouse", "length": 7.5, "run": _waiting},
		{"name": "Kethrax", "length": 7.5, "run": _rise},
	]

func _cast(cs: CutscenePlayer) -> Array:
	cs.use_map(_map)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var hero := cs.hero(&"hero", Vector3(-12.2, 0, 0), 90.0)
	hero.play(&"idle", 0.0)
	var kx := cs.legend(&"kethrax", &"kethrax", BOSS, -90.0)
	var key := OmniLight3D.new()
	key.light_color = Color(0.8, 0.75, 1.0)
	key.light_energy = 3.6
	key.omni_range = 8.0
	cs.fx(key, BOSS + Vector3(-2.6, 2.8, 1.2))
	return [hero, kx]

func _waiting(cs: CutscenePlayer) -> void:
	var c := _cast(cs)
	var kx: CutsceneActor = c[1]
	kx.play(&"cs_kx_pull", 0.0, 0.6)
	cs.attach_fx(kx, LegendFX.soulfire(0.6))
	cs.camera([[0.0, Vector3(-14.0, 2.3, 1.9), BOSS + Vector3(0, 1.6, 0), 26.0], [7.5, Vector3(-12.6, 2.0, 1.5), BOSS + Vector3(0, 1.9, 0), 20.0]])
	cs.sfx(0.4, &"cultist_chant", -8.0)
	cs.say(1.0, "Kethrax", "The waypoint's pup. And you are carrying something of his. I can smell it burning from here.", 4.2, C_KX)

func _rise(cs: CutscenePlayer) -> void:
	var c := _cast(cs)
	var kx: CutsceneActor = c[1]
	kx.play(&"cs_kx_emerge", 0.0)
	var soul := LegendFX.soulfire(0.6)
	cs.attach_fx(kx, soul)
	var c1 := Vector3(1.6, 0.8, 2.6)
	var c2 := Vector3(0.9, 1.0, 3.2)
	cs.camera([[0.0, c1, CSKit.off(c1, BOSS + Vector3(0, 2.2, 0), 0.5), 46.0], [7.5, c2, CSKit.off(c2, BOSS + Vector3(0, 2.4, 0), 0.5), 44.0]])
	cs.at(2.0, func() -> void:
		soul.fade_to(1.4, 0.8)
		cs.flash(cs.t, CSKit.LEGION_EYES, 0.3)
		cs.fx(VFXLib.ring_wave(CSKit.LEGION_EYES, 8.0, 0.8, 0.9), BOSS + Vector3(0, 0.1, 0))
		for i in 4:
			var ch := LegendFX.ChainFX.new(CSKit.LEGION_EYES, 0.022)
			ch.from_node = kx.follow("hand.L" if i % 2 == 0 else "hand.R")
			var a := TAU * (i + 0.5) / 4.0
			ch.to = _map * (BOSS + Vector3(cos(a) * 4.5, 0.0, sin(a) * 4.5))
			cs.fx(ch)
			var tw := cs.tween(ch)
			tw.tween_property(ch, "extend", 1.0, 0.35))
	cs.sfx(2.0, &"boss_roar", 0.0)
	cs.shake(2.0, 0.8, 0.8)
	cs.card(2.3, &"kethrax", 4.8)
	cs.say(3.0, "Kethrax", "Give me the Tyrant's tooth, and I will let you drown quickly.", 3.4, C_KX)
