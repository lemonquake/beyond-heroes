extends Cutscene
## bh-021 — Kethrax falls. On one knee in the Legion's circle he spends his last breath on a threat; his chains
## shatter. Far across the sea, in the Black Spire, Aljay hangs in three chains — and one of them snaps. The wrath
## flares, the helm lifts, and for the first time in three winters he speaks. Back on the causeway the shard burns hot
## in the hero's hand.

const C_KX := Color(0.75, 0.55, 1.0)

var _at := Transform3D.IDENTITY

func _init() -> void:
	title = "A Chain Breaks"
	skip_all = true
	music = &"music_legend"

func build(cs: CutscenePlayer) -> Array:
	if has_meta(&"at"):
		_at = get_meta(&"at")
	elif Game.current_map:
		_at = Game.current_map.global_transform * Transform3D(Basis(Vector3.UP, deg_to_rad(-90.0)), Vector3(6, 0, 0))
	# the real body (and anything the Legion left standing) steps out of the shot
	for n in cs.get_tree().get_nodes_in_group(&"enemy"):
		if n is Node3D and (n as Node3D).global_position.distance_to(_at.origin) < 30.0:
			cs.hide_node(n as Node3D)
	return [
		{"name": "Last Words", "length": 11.0, "run": _last_words},
		{"name": "The Black Spire", "length": 12.0, "run": _spire, "fade_in": 0.0},
		{"name": "The Shard Burns", "length": 5.0, "run": _shard},
	]

func finish(_cs: CutscenePlayer) -> void:
	Game.set_world_flag(&"chain_breaks_seen")

func _cast(cs: CutscenePlayer) -> CutsceneActor:
	cs.use_map(_at)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var hero := cs.hero(&"hero", Vector3(0, 0, 3.4), 180.0)
	hero.play(&"idle", 0.0)
	return hero

func _last_words(cs: CutscenePlayer) -> void:
	_cast(cs)
	var kx := cs.legend(&"kethrax", &"kethrax", Vector3.ZERO, 0.0)
	kx.play(&"cs_kx_kneel", 0.0)
	var key := OmniLight3D.new()
	key.light_color = Color(0.8, 0.75, 1.0)
	key.light_energy = 1.8
	key.omni_range = 6.0
	cs.fx(key, Vector3(1.2, 2.4, 2.0))
	var soul := LegendFX.soulfire(0.5)
	cs.attach_fx(kx, soul)
	var chains := []
	for i in 3:
		var ch := LegendFX.ChainFX.new(CSKit.LEGION_EYES, 0.022)
		ch.from_node = kx.follow(["hand.L", "hand.R", "chest"][i])
		var a := TAU * (i + 0.3) / 3.0
		ch.to = _at * Vector3(cos(a) * 3.5, 0.0, sin(a) * 3.5 - 0.5)
		ch.extend = 1.0
		cs.fx(ch)
		chains.append(ch)
	var c1 := Vector3(1.6, 1.3, 2.6)
	cs.camera([[0.0, c1, Vector3(0.0, 1.5, 0.0), 36.0], [8.0, Vector3(1.1, 1.2, 2.0), Vector3(0.0, 1.6, 0.0), 30.0],
		[11.0, Vector3(1.8, 2.2, 3.4), Vector3(0.0, 0.8, 0.0), 40.0]])
	cs.say(1.6, "Kethrax", "You think he waits for rescue? He breaks our chains every night.", 3.4, C_KX)
	cs.say(5.2, "Kethrax", "And every night we forge more. The Spire will hold him until the Tyrants wake...", 3.4, C_KX)
	cs.at(8.8, func() -> void:
		cs.flash(cs.t, CSKit.LEGION_EYES, 0.4)
		for ch in chains:
			var tw := cs.tween(ch)
			tw.tween_property(ch, "extend", 0.0, 0.25)
		soul.fade_to(0.0, 0.6)
		var tw2 := cs.tween(kx)
		tw2.tween_property(kx, "scale", Vector3(1.0, 0.02, 1.0), 0.9).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
		cs.fx(VFXLib.ring_wave(CSKit.LEGION_EYES, 6.0, 0.9, 0.8), Vector3(0, 0.1, 0)))
	cs.sfx(8.8, &"break_stone", 2.0)
	cs.shake(8.8, 0.7, 0.8)
	cs.fade(10.2, 1.0, 0.8)

func _spire(cs: CutscenePlayer) -> void:
	cs.use_flashback("spire", CSKit.spire_set)
	cs.vignette(true, 0.4)
	var aj := cs.legend(&"aljay", &"aljay", Vector3.ZERO, 180.0, false)
	aj.play(&"cs_aj_chained", 0.0, 0.5)
	var aura := LegendFX.wrath_aura(0.3)
	cs.attach_fx(aj, aura)
	var chains := []
	for i in 3:
		var a := TAU * i / 3.0 + 0.5
		var ch := LegendFX.ChainFX.new([CSKit.LEGION_EYES, Color(0.9, 0.5, 0.2), CSKit.SEAL][i], 0.026)
		ch.from = cs.stage().global_transform * Vector3(cos(a) * 4.2, 3.6, sin(a) * 4.2)
		ch.to_node = aj.follow(["hand.L", "neck", "hand.R"][i])
		ch.extend = 1.0
		ch.sag = 0.1
		cs.fx(ch)
		chains.append(ch)
	cs.caption(0.3, "The Black Spire", "Far across the sea", 3.0)
	cs.fade(0.0, 1.0, 0.0)
	cs.fade(2.8, 0.0, 1.6)
	cs.camera([[0.0, Vector3(0.0, 2.2, -5.6), Vector3(0.0, 1.8, 0.0), 44.0], [5.0, Vector3(0.6, 1.9, -3.8), Vector3(0.0, 1.8, 0.0), 38.0],
		[5.1, Vector3(0.0, 1.9, -1.3), Vector3(0.0, 1.95, 0.0), 30.0, true], [12.0, Vector3(0.0, 1.8, -1.0), Vector3(0.0, 1.95, 0.0), 26.0]])
	cs.at(4.6, func() -> void:
		var ch: LegendFX.ChainFX = chains[0]
		var tw := cs.tween(ch)
		tw.tween_property(ch, "extend", 0.0, 0.2)
		cs.flash(cs.t, CSKit.LEGION_EYES, 0.5)
		aura.fade_to(1.5, 0.6))
	cs.sfx(4.6, &"break_stone", 3.0)
	cs.shake(4.6, 1.0, 0.9)
	cs.at(5.2, func() -> void: aj.play(&"cs_aj_stand", 0.8, 0.6))
	cs.sfx(6.0, &"boss_roar", -4.0)
	cs.say(6.6, "Aljay", "...Paul. Roydo.", 2.4, CSKit.WRATH)
	cs.say(9.2, "Aljay", "I am still here.", 2.6, CSKit.WRATH)
	cs.fade(11.0, 1.0, 1.0)

func _shard(cs: CutscenePlayer) -> void:
	cs.vignette(false, 0.4)
	var hero := _cast(cs)
	hero.detach(&"main")
	hero.play(&"interact_teleport", 0.2, 0.6)
	CSKit.shard_in_hand(hero, "weapon.R", 4.0)
	var h := Vector3(0, 1.75, 3.4)
	cs.camera([[0.0, Vector3(1.8, 1.9, 1.8), h, 44.0], [5.0, Vector3(1.5, 1.85, 2.0), h, 38.0]])
