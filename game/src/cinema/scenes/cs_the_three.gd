extends Cutscene
## bh-021 — "The Dawnbreakers": Paul David's tale by the lake in Olivar. It flashes back three winters to the Weeping
## Causeway: the Forsaken Legion waiting in the storm, Roydo's arrival (the Righteous Hammer), Paul David himself (the
## Tempest Blade), Aljay rising out of the dark with the Dusk Tyrant's wrath (the Forsaken Hero), the three holding
## the causeway, the Accord's betrayal, Kethrax rising out of the Legion's circle with his chains, the last blow, the
## black water — and back to the lake. The author's rule: no "Skip all"; every scene can be skipped on its own.
## Flashback coordinates are the Weeping Causeway map's: the Drowned Tollhouse ring is centred on the origin, the
## causeway comes in from the west (-X); the Legion stands in the east half of the ring.

const PD := "Paul David"
const C_PD := Color(0.6, 0.85, 1.0)
const C_KX := Color(0.75, 0.55, 1.0)
const C_AC := Color(0.8, 0.84, 0.95)
const HOST := Vector3(5.0, 0, 0)

var _lake := Transform3D.IDENTITY

func _init() -> void:
	title = "The Dawnbreakers"
	skip_all = false
	music = &"music_legend"

func build(cs: CutscenePlayer) -> Array:
	var n := cs.npc(&"paul_david")
	if n:
		_lake = n.global_transform.orthonormalized()
	elif Game.current_map:
		_lake = Game.current_map.global_transform * Transform3D(Basis(Vector3.UP, deg_to_rad(200.0)), DataNpcsLegend.LAKESIDE)
	return [
		{"name": "The Lakeside", "length": 11.0, "run": _lakeside},
		{"name": "Three Winters Ago", "length": 9.5, "run": _host, "fade_in": 0.0},
		{"name": "The Righteous Hammer", "length": 11.5, "run": _roydo},
		{"name": "The Tempest Blade", "length": 7.5, "run": _paul},
		{"name": "The Forsaken Hero", "length": 14.0, "run": _aljay, "fade_in": 0.0},
		{"name": "The Dusk Tyrant's Wrath", "length": 13.0, "run": _wrath},
		{"name": "The Dawnbreakers", "length": 10.0, "run": _stand},
		{"name": "The Betrayal", "length": 11.0, "run": _betrayal},
		{"name": "The Chain-Marshal", "length": 13.0, "run": _chains},
		{"name": "The Last Blow", "length": 10.0, "run": _last_blow},
		{"name": "The Lake Again", "length": 13.0, "run": _lake_again},
	]

func finish(_cs: CutscenePlayer) -> void:
	Game.set_world_flag(&"the_three_seen")

## A look-at point that puts `subject` on the right (side > 0) or left (side < 0) third of a shot from `cam`.
static func off(cam: Vector3, subject: Vector3, side: float) -> Vector3:
	var f := subject - cam
	f.y = 0.0
	var right := f.normalized().cross(Vector3.UP)
	return subject - right * side * f.length() * 0.28

# ---------------------------------------------------------------------------------------------------------------- the lake

func _lake_cast(cs: CutscenePlayer) -> Array:
	cs.use_map(_lake)
	cs.hide_node(cs.npc(&"paul_david"))
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var pd := cs.legend(&"pd", &"paul_david", Vector3.ZERO, 0.0, false)
	var hero := cs.hero(&"hero", Vector3(1.3, 0, -1.7), -38.0)
	hero.play(&"idle", 0.0)
	return [pd, hero]

func _lakeside(cs: CutscenePlayer) -> void:
	var c := _lake_cast(cs)
	var pd: CutsceneActor = c[0]
	pd.play(&"cs_pd_shard", 0.0)
	CSKit.shard_in_hand(pd)
	# over his shoulder at the lake, then round to his face
	var f1 := Vector3(2.0, 1.66, 2.0)
	var f2 := Vector3(1.35, 1.63, 1.4)
	cs.camera([[0.0, Vector3(-0.9, 1.95, -2.9), Vector3(0.3, 1.2, 6.0), 50.0], [5.4, Vector3(-1.2, 1.85, -2.2), Vector3(0.2, 1.3, 5.0), 46.0],
		[5.5, f1, off(f1, Vector3(0, 1.58, 0), 0.5), 34.0, true], [11.0, f2, off(f2, Vector3(0, 1.57, 0.05), 0.5), 30.0]])
	cs.say(0.8, PD, "Three winters ago the Accord sent the three of us to Reedwater Marsh.", 3.6, C_PD)
	cs.say(4.6, PD, "An orc war-host, the Registry said. Burning the reed villages. Come at once.", 3.6, C_PD)
	cs.say(8.4, PD, "There were no orcs.", 2.4, C_PD)
	cs.fade(9.8, 1.0, 1.2)

# ---------------------------------------------------------------------------------------------------------------- flashback

func _flash(cs: CutscenePlayer) -> void:
	cs.use_flashback("causeway", CSKit.causeway_set)
	cs.vignette(true)

func _host(cs: CutscenePlayer) -> void:
	_flash(cs)
	CSKit.legion(cs, HOST, 3, 7, Vector2(1.7, 1.9), -90.0)
	cs.caption(0.2, "Three winters ago", "The Weeping Causeway, Reedwater Marsh", 3.8)
	cs.fade(0.0, 1.0, 0.0)
	cs.fade(3.4, 0.0, 1.6)
	cs.camera([[0.0, Vector3(-40.0, 14.0, 14.0), Vector3(-4.0, 1.0, 0.0), 50.0], [9.5, Vector3(-21.0, 5.0, 7.0), Vector3(5.0, 1.4, 0.0), 42.0]])
	CSKit.storm(cs, [3.8, 6.9, 8.6], Vector3(0, 0, 0), 35.0)
	cs.say(4.6, PD, "The Legion was waiting. The Forsaken: knights who broke the oath of the Binding and sold their swords to the Pact of Wrath.", 4.6, C_PD)
	cs.sfx(3.5, &"cultist_chant", -8.0)

func _roydo(cs: CutscenePlayer) -> void:
	_flash(cs)
	CSKit.legion(cs, HOST, 3, 7, Vector2(1.7, 1.9), -90.0)
	var R := Vector3(-9.5, 0, -1.6)
	var ro := cs.legend(&"roydo", &"roydo", R, 90.0)
	ro.visible = false
	ro.play(&"cs_ro_land", 0.0)
	var shaft := cs.fx(LegendFX.light_shaft(Color(1.0, 0.85, 0.5), 40.0, 1.2, 2.4), R) as MeshInstance3D
	shaft.visible = false
	var aura := LegendFX.holy_aura(0.0, false)
	cs.attach_fx(ro, aura)
	var head := R + Vector3(0, 2.0, 0)
	var c1 := Vector3(-15.0, 1.0, 4.5)
	var c2 := Vector3(-13.3, 0.7, 1.9)
	var c3 := Vector3(-12.0, 1.3, -4.9)
	cs.camera([[0.0, c1, R + Vector3(0, 8.0, 0), 55.0], [1.4, c1, off(c1, head, 0.4), 48.0],
		[5.0, c2, off(c2, head, 0.55), 40.0], [11.5, c3, off(c3, head, 0.55), 36.0]])
	cs.say(0.3, PD, "Roydo went first. He always did.", 2.4, C_PD)
	cs.at(1.2, func() -> void:
		shaft.visible = true
		cs.flash(cs.t, Color(1.0, 0.9, 0.7), 0.5))
	cs.at(1.5, func() -> void:
		ro.visible = true
		ro.play(&"cs_ro_land", 0.0)
		cs.fx(VFXLib.ring_wave(CSKit.HOLY, 9.0, 0.7, 0.8), R + Vector3(0, 0.1, 0))
		cs.fx(VFXLib.ground_crack(CSKit.HOLY, 3.5, 2.5), R + Vector3(0, 0.05, 0))
		aura.fade_to(1.0, 1.2))
	cs.shake(1.5, 1.0, 0.8)
	cs.sfx(1.5, &"boss_slam", 2.0)
	cs.sfx(1.4, &"arcane_surge", -2.0)
	cs.at(2.4, func() -> void:
		var tw := cs.tween(shaft)
		tw.tween_method(func(v: float) -> void: (shaft.material_override as ShaderMaterial).set_shader_parameter("power", v), 1.0, 0.25, 3.0))
	cs.card(3.4, &"roydo", 5.2)
	cs.say(8.6, PD, "The Righteous Hammer. There was never a wall in Jre he could not become.", 2.9, C_PD)

func _paul(cs: CutscenePlayer) -> void:
	_flash(cs)
	CSKit.legion(cs, HOST, 3, 7, Vector2(1.7, 1.9), -90.0)
	var P := Vector3(-10.0, 0, 2.2)
	var pd := cs.legend(&"pd_past", &"paul_david", P, 95.0)
	pd.play(&"cs_pd_ready", 0.0)
	cs.attach_fx(pd.follow("weapon.R"), LegendFX.storm_aura(1.2), Vector3(0, 0.6, 0))
	var head := P + Vector3(0, 1.65, 0)
	var c1 := Vector3(-7.4, 1.5, 4.2)
	var c2 := Vector3(-7.7, 1.8, 0.9)
	cs.camera([[0.0, c1, off(c1, head, 0.5), 40.0], [7.5, c2, off(c2, head, 0.5), 34.0]])
	cs.at(0.6, func() -> void:
		LegendFX.lightning_strike(cs.stage(), P + Vector3(-0.4, 0, 0.4), Color(0.5, 0.8, 1.0))
		cs.flash(cs.t, Color(0.6, 0.85, 1.0), 0.25))
	cs.sfx(0.6, &"cast_lightning", 0.0)
	cs.say(0.2, PD, "And me: the fool with the sword, who thought he could keep up with them.", 3.2, C_PD)
	cs.card(2.0, &"paul_david", 5.0)

func _aljay(cs: CutscenePlayer) -> void:
	_flash(cs)
	cs.drop(&"roydo")
	cs.drop(&"pd_past")
	CSKit.legion(cs, HOST, 3, 7, Vector2(1.7, 1.9), -90.0)
	var A := Vector3(-7.0, 0, 0)
	var aj := cs.legend(&"aljay", &"aljay", A, 90.0)
	aj.play(&"cs_aj_kneel", 0.0)
	var aura := LegendFX.wrath_aura(0.12)
	cs.attach_fx(aj, aura)
	# the stage goes dark round him; the helm first, the eyes light, he rises and the camera falls back
	cs.fade(0.0, 1.0, 0.0)
	cs.fade(0.2, 0.3, 1.8)
	var c3 := Vector3(-3.5, 0.5, 3.1)
	var c4 := Vector3(-3.0, 0.8, 3.6)
	cs.camera([[0.0, Vector3(-5.1, 1.28, 0.95), A + Vector3(0, 1.22, 0), 30.0], [3.6, Vector3(-5.55, 1.3, 0.55), A + Vector3(0, 1.26, 0), 26.0],
		[5.4, Vector3(-5.1, 1.7, 1.3), A + Vector3(0, 1.95, 0), 36.0], [8.0, c3, off(c3, A + Vector3(0, 2.1, 0), 0.5), 46.0],
		[14.0, c4, off(c4, A + Vector3(0, 2.0, 0), 0.5), 44.0]])
	cs.say(0.6, PD, "And Aljay.", 2.2, C_PD)
	cs.sfx(3.2, &"dark_curse", 0.0)
	cs.at(3.4, func() -> void:
		cs.flash(cs.t, CSKit.WRATH, 0.3)
		cs.fade(cs.t, 0.0, 1.0)
		aura.fade_to(0.6, 2.2))
	cs.at(4.6, func() -> void: aj.play(&"cs_aj_rise", 0.3))
	cs.shake(4.6, 0.35, 2.4)
	cs.sfx(5.0, &"boss_roar", -2.0)
	cs.at(7.4, func() -> void:
		aura.fade_to(1.25, 0.8)
		cs.fx(VFXLib.ring_wave(CSKit.WRATH, 11.0, 0.8, 1.0), A + Vector3(0, 0.1, 0))
		cs.fx(VFXLib.ground_crack(CSKit.WRATH, 4.5, 3.5), A + Vector3(0, 0.05, 0))
		cs.flash(cs.t, Color(1.0, 0.3, 0.2), 0.3))
	cs.sfx(7.4, &"fire_explode", 0.0)
	cs.shake(7.4, 1.2, 0.8)
	cs.card(7.8, &"aljay", 5.6)
	cs.say(11.2, PD, "The Forsaken Hero, the Registry calls him now. That name is a lie.", 2.8, C_PD)

func _wrath(cs: CutscenePlayer) -> void:
	_flash(cs)
	cs.drop(&"roydo")
	cs.drop(&"pd_past")
	var A := Vector3(-7.0, 0, 0)
	var aj := cs.legend(&"aljay", &"aljay", A, 90.0)
	aj.play(&"cs_aj_clutch", 0.0)
	var aura := LegendFX.wrath_aura(0.6)
	cs.attach_fx(aj, aura)
	var heart := OmniLight3D.new()
	heart.light_color = CSKit.WRATH
	heart.light_energy = 2.0
	heart.omni_range = 3.0
	cs.attach_fx(aj.follow("chest"), heart, Vector3(0, 0.05, -0.2))
	var c1 := Vector3(-4.3, 2.0, 2.0)
	var c2 := Vector3(-4.6, 1.5, -2.2)
	var c3 := Vector3(-3.6, 2.3, -3.2)
	var h := A + Vector3(0, 1.7, 0)
	cs.camera([[0.0, c1, off(c1, h, -0.4), 34.0], [6.0, c2, off(c2, h, -0.4), 36.0], [13.0, c3, off(c3, h, -0.3), 40.0]])
	cs.at(0.5, func() -> void: aura.fade_to(1.1, 1.5))
	cs.at(6.5, func() -> void: aura.fade_to(0.7, 2.5))
	cs.shake(0.6, 0.3, 5.0)
	cs.sfx(0.6, &"burn_loop", -6.0)
	cs.say(0.4, PD, "Twelve winters ago a Sulvane war-Tyrant fell on Malasugue. Aljay put his lance through its heart.", 3.6, C_PD)
	cs.say(4.2, PD, "Its wrath poured into him. The armour grew over him like scales. The darkness wanted him to burn the world.", 4.0, C_PD)
	cs.say(8.4, PD, "He used it to guard Malasugue instead. Nine winters. His heart never faltered.", 4.2, C_PD)

func _stand(cs: CutscenePlayer) -> void:
	_flash(cs)
	var host := CSKit.legion(cs, HOST, 3, 7, Vector2(1.7, 1.9), -90.0, &"walk")
	var aj := cs.legend(&"aljay", &"aljay", Vector3(-7.0, 0, 0), 90.0)
	var ro := cs.legend(&"roydo", &"roydo", Vector3(-8.6, 0, -2.4), 90.0)
	var pd := cs.legend(&"pd_past", &"paul_david", Vector3(-8.6, 0, 2.4), 90.0)
	aj.play(&"cs_aj_point", 0.0)
	ro.play(&"cs_ro_shoulder", 0.0)
	pd.play(&"cs_pd_ready", 0.0)
	cs.attach_fx(aj, LegendFX.wrath_aura(0.8))
	cs.attach_fx(ro, LegendFX.holy_aura(0.7, false))
	cs.camera([[0.0, Vector3(-14.5, 0.9, 0.2), Vector3(-4.0, 2.0, 0.0), 46.0], [4.4, Vector3(-12.6, 1.0, 0.3), Vector3(-4.0, 2.2, 0.0), 42.0],
		[4.5, Vector3(-3.5, 2.4, 8.5), Vector3(-1.5, 1.2, 0.0), 50.0, true], [10.0, Vector3(2.5, 3.2, 9.0), Vector3(3.0, 1.0, 0.0), 50.0]])
	cs.say(0.4, PD, "We held that causeway until the water ran black with them. We would have won.", 3.8, C_PD)
	cs.at(4.8, func() -> void:
		aj.play(&"cs_aj_charge", 0.1)
		var tw := cs.tween(aj)
		tw.tween_property(aj, "position", Vector3(7.0, 0, 0), 1.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.tween_callback(func() -> void: aj.play(&"cs_aj_point", 0.2)))
	cs.sfx(4.8, &"boss_charge", 0.0)
	cs.at(5.5, func() -> void:
		for a in host:
			if is_instance_valid(a) and absf((a as Node3D).position.z) < 3.2:
				CSKit.blast(cs, a, Vector3(1.0, 0, signf((a as Node3D).position.z + 0.01) * 0.8), 4.0, 0.5)
		cs.fx(VFXLib.ring_wave(CSKit.WRATH, 6.0, 0.4, 0.6), Vector3(2.0, 0.2, 0.0)))
	cs.shake(5.5, 0.8, 0.6)
	cs.at(6.4, func() -> void:
		ro.play(&"cs_ro_slam", 0.1)
		var tw := cs.tween(ro)
		tw.tween_property(ro, "position", Vector3(-3.0, 0, -3.6), 0.8))
	cs.at(7.4, func() -> void:
		cs.fx(VFXLib.ring_wave(CSKit.HOLY, 8.0, 0.6, 0.9), Vector3(-1.5, 0.1, -3.6))
		cs.fx(VFXLib.ground_crack(CSKit.HOLY, 3.0, 2.0), Vector3(-1.5, 0.05, -3.6))
		for a in host:
			if is_instance_valid(a) and (a as Node3D).position.z < -1.5 and (a as Node3D).position.x < 9.0:
				CSKit.blast(cs, a, Vector3(1.0, 0, -0.6), 3.0, 0.45))
	cs.sfx(7.4, &"boss_slam", 2.0)
	cs.shake(7.4, 1.0, 0.6)

func _betrayal(cs: CutscenePlayer) -> void:
	_flash(cs)
	var A := Vector3(-2.0, 0, 0.4)
	var aj := cs.legend(&"aljay", &"aljay", A, 90.0)
	var ro := cs.legend(&"roydo", &"roydo", Vector3(-3.4, 0, -3.0), 90.0)
	var pd := cs.legend(&"pd_past", &"paul_david", Vector3(-4.2, 0, 2.4), 90.0)
	aj.play(&"cs_aj_point", 0.0)
	ro.play(&"cs_ro_brace", 0.0)
	pd.play(&"cs_pd_ready", 0.0)
	var aura := LegendFX.wrath_aura(0.8)
	cs.attach_fx(aj, aura)
	CSKit.legion(cs, Vector3(6.0, 0, 0), 2, 7, Vector2(1.7, 1.9), -90.0)
	var S := Vector3(-12.5, 0, 0)
	var seal := CSKit.sealers(cs, S, 5, 1.6, 90.0)
	var c3 := Vector3(-8.8, 2.3, 4.6)
	var c4 := Vector3(-7.0, 1.6, 3.2)
	cs.camera([[0.0, Vector3(-1.0, 2.1, 2.4), S + Vector3(0, 1.4, 0), 40.0], [3.0, Vector3(-3.4, 1.8, 2.6), S + Vector3(0, 1.6, 0), 30.0],
		[5.6, c3, off(c3, A + Vector3(0, 1.6, 0), 0.4), 44.0, true], [11.0, c4, off(c4, A + Vector3(0, 1.7, 0), 0.4), 38.0]])
	cs.say(0.3, PD, "Then the Accord's knights came up the causeway behind us. Not for the Legion.", 3.2, C_PD)
	cs.say(3.8, "Accord Knight-Captain", "By order of the High Registrar: the wrath-bearer is to be delivered. Seal him!", 3.2, C_AC)
	cs.at(4.0, func() -> void:
		for s in seal:
			if is_instance_valid(s):
				(s as CutsceneActor).play(&"cast_channel" if (s as CutsceneActor).has_clip(&"cast_channel") else &"cast_quick", 0.15))
	cs.at(5.8, func() -> void:
		var i := 0
		for s in seal:
			if not is_instance_valid(s):
				continue
			var ch := LegendFX.ChainFX.new(CSKit.SEAL, 0.016)
			ch.from_node = (s as CutsceneActor).follow("hand.R")
			ch.to_node = aj.follow(["chest", "upper_arm.L", "upper_arm.R", "thigh.L", "thigh.R"][i % 5])
			ch.set_glow(3.0)
			cs.fx(ch)
			var tw := cs.tween(ch)
			tw.tween_property(ch, "extend", 1.0, 0.45 + 0.08 * i)
			i += 1
		cs.flash(cs.t + 0.45, CSKit.SEAL, 0.3))
	cs.sfx(5.8, &"arcane_charge", 0.0)
	cs.at(6.3, func() -> void:
		aj.play(&"cs_aj_chained", 0.15)
		aura.fade_to(1.4, 0.4))
	cs.shake(6.3, 0.6, 1.2)
	cs.say(7.4, PD, "For him.", 2.4, C_PD)

func _chains(cs: CutscenePlayer) -> void:
	_flash(cs)
	var A := Vector3(-5.0, 0, 0.4)
	var K := Vector3(0.0, 0, 0.0)
	var aj := cs.legend(&"aljay", &"aljay", A, 90.0)
	aj.play(&"cs_aj_chained", 0.0)
	cs.attach_fx(aj, LegendFX.wrath_aura(1.2))
	var ro := cs.legend(&"roydo", &"roydo", Vector3(-1.5, 0, -4.2), 60.0)
	ro.play(&"cs_ro_brace", 0.0)
	cs.attach_fx(ro, LegendFX.holy_aura(0.9, false))
	var pd := cs.legend(&"pd_past", &"paul_david", Vector3(-8.2, 0, 2.6), 80.0)
	pd.play(&"cs_pd_ready", 0.0)
	CSKit.legion(cs, Vector3(5.5, 0, 0), 3, 7, Vector2(1.7, 1.9), -90.0, &"walk")
	var kx := cs.legend(&"kethrax", &"kethrax", K + Vector3(0, -3.6, 0), -90.0)
	kx.play(&"cs_kx_emerge", 0.0)
	cs.attach_fx(kx, LegendFX.soulfire(0.9))
	var kl := OmniLight3D.new()
	kl.light_color = CSKit.LEGION_EYES
	kl.light_energy = 3.0
	kl.omni_range = 8.0
	cs.attach_fx(kx, kl, Vector3(-1.2, 2.4, 0.0))
	var c2 := Vector3(-3.3, 0.5, 2.9)
	var c3 := Vector3(-11.5, 2.6, 1.2)
	cs.camera([[0.0, Vector3(-4.2, 0.9, 3.6), K + Vector3(0, 0.4, 0), 44.0], [3.0, c2, off(c2, K + Vector3(0, 2.6, 0), 0.45), 40.0],
		[6.3, c3, off(c3, Vector3(-2.5, 1.5, 0.2), 0.2), 48.0, true], [13.0, Vector3(-12.6, 2.2, 2.4), Vector3(-3.0, 1.4, 0.2), 44.0]])
	cs.at(0.2, func() -> void:
		cs.fx(VFXLib.ring_wave(CSKit.LEGION_EYES, 7.0, 0.8, 0.9), K + Vector3(0, 0.1, 0))
		cs.flash(cs.t, CSKit.LEGION_EYES, 0.3)
		var tw := cs.tween(kx)
		tw.tween_property(kx, "position", K, 2.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT))
	cs.sfx(0.3, &"boss_roar", 0.0)
	cs.card(2.2, &"kethrax", 4.6)
	cs.say(2.4, "Kethrax", "The wrath-bearer comes with me. The Legion has need of a Tyrant's heart.", 3.6, C_KX)
	cs.at(6.4, func() -> void:
		kx.play(&"cs_kx_bind", 0.2)
		for i in 3:
			var ch := LegendFX.ChainFX.new(CSKit.LEGION_EYES, 0.024)
			ch.from_node = kx.follow(["hand.L", "hand.R", "chest"][i])
			ch.to_node = aj.follow(["hand.L", "hand.R", "neck"][i])
			ch.set_glow(2.2)
			cs.fx(ch)
			var tw := cs.tween(ch)
			tw.tween_interval(0.25)
			tw.tween_property(ch, "extend", 1.0, 0.5))
	cs.at(7.4, func() -> void: kx.play(&"cs_kx_pull", 0.2))
	cs.sfx(6.8, &"dark_curse", 0.0)
	cs.say(7.2, PD, "Roydo turned to face the host alone. I ran for Aljay.", 2.6, C_PD)
	cs.at(8.0, func() -> void: pd.play(&"cs_pd_reach", 0.2))
	cs.at(9.6, func() -> void:
		pd.play(&"cs_pd_branded", 0.1)
		var l := OmniLight3D.new()
		l.light_color = CSKit.LEGION_EYES
		l.light_energy = 3.0
		l.omni_range = 2.0
		cs.attach_fx(pd.follow("hand.R"), l)
		cs.flash(cs.t, CSKit.LEGION_EYES, 0.25))
	cs.sfx(9.6, &"drain", 0.0)
	cs.say(10.0, PD, "Kethrax put his mark on my hand before I was halfway there.", 2.9, C_PD)

func _last_blow(cs: CutscenePlayer) -> void:
	_flash(cs)
	var A := Vector3(-5.0, 0, 0.4)
	var K := Vector3(0.0, 0, 0.0)
	var aj := cs.legend(&"aljay", &"aljay", A, 90.0)
	aj.play(&"cs_aj_chained", 0.0)
	var aura := LegendFX.wrath_aura(1.2)
	cs.attach_fx(aj, aura)
	var kx := cs.legend(&"kethrax", &"kethrax", K, -90.0)
	kx.play(&"cs_kx_pull", 0.0)
	cs.attach_fx(kx, LegendFX.soulfire(0.8))
	var ro := cs.legend(&"roydo", &"roydo", Vector3(-1.5, 0, -4.2), 60.0)
	ro.play(&"cs_ro_brace", 0.0)
	var hol := LegendFX.holy_aura(0.9, false)
	cs.attach_fx(ro, hol)
	cs.drop(&"pd_past")
	for i in 3:
		var ch := LegendFX.ChainFX.new(CSKit.LEGION_EYES, 0.024)
		ch.from_node = kx.follow(["hand.L", "hand.R", "chest"][i])
		ch.to_node = aj.follow(["hand.L", "hand.R", "neck"][i])
		ch.extend = 1.0
		ch.set_glow(2.2)
		cs.fx(ch)
	var c1 := Vector3(-3.0, 1.6, 3.4)
	var c3 := Vector3(-6.0, 3.6, 4.5)
	cs.camera([[0.0, c1, Vector3(-2.5, 1.8, 0.2), 38.0], [3.2, Vector3(-2.2, 1.5, 3.0), Vector3(-1.2, 1.9, 0.1), 32.0],
		[3.3, c3, Vector3(-0.5, 0.2, 0.0), 44.0, true], [10.0, Vector3(-7.5, 4.2, 5.5), Vector3(0.0, -0.8, 0.0), 48.0]])
	cs.at(0.8, func() -> void:
		aura.fade_to(1.8, 0.5)
		aj.play(&"cs_aj_charge", 0.1)
		var tw := cs.tween(aj)
		tw.tween_property(aj, "position", Vector3(-1.6, 0, 0.2), 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN))
	cs.sfx(0.8, &"boss_charge", 0.0)
	cs.at(1.4, func() -> void:
		aj.play(&"cs_aj_point", 0.05)
		aj.detach(&"main")
		aj.attach(&"main", "dusk_piercer_broken")
		kx.play(&"hit_heavy", 0.05)
		cs.fx(VFXLib.impact_flash(CSKit.WRATH, 3.0, 0.4, 6), K + Vector3(-0.3, 2.3, 0.0))
		cs.flash(cs.t, Color(1.0, 0.25, 0.15), 0.4))
	cs.sfx(1.4, &"crit_hit", 3.0)
	cs.shake(1.4, 1.4, 0.7)
	cs.say(1.8, PD, "He broke his lance in Kethrax's chest. They dragged him under anyway.", 3.4, C_PD)
	cs.at(3.4, func() -> void:
		kx.play(&"cs_kx_pull", 0.2)
		aj.play(&"cs_aj_dragged", 0.1)
		var tw := cs.tween(aj)
		tw.tween_property(aj, "position", Vector3(-0.4, -0.3, 0.1), 1.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
		tw.tween_property(aj, "position", Vector3(-0.2, -3.2, 0.0), 1.6).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		aura.fade_to(0.0, 3.6)
		cs.fx(VFXLib.ring_wave(CSKit.WRATH, 5.0, 1.2, 0.8), K + Vector3(0, 0.1, 0)))
	cs.sfx(5.6, &"body_fall", 0.0)
	cs.at(6.2, func() -> void:
		ro.play(&"cs_ro_fall", 0.2)
		hol.fade_to(0.0, 2.6))
	cs.say(6.0, PD, "Roydo's light went down into the black water. And then there was only the rain.", 3.6, C_PD)
	cs.fade(8.6, 1.0, 1.3)

# ---------------------------------------------------------------------------------------------------------------- the lake again

func _lake_again(cs: CutscenePlayer) -> void:
	cs.vignette(false)
	var c := _lake_cast(cs)
	var pd: CutsceneActor = c[0]
	pd.play(&"cs_pd_shard", 0.0)
	CSKit.shard_in_hand(pd)
	var c1 := Vector3(2.1, 1.68, 2.6)
	var c2 := Vector3(-1.3, 1.62, 2.0)
	var c3 := Vector3(-1.7, 1.8, 2.9)
	var h := Vector3(0, 1.55, 0)
	cs.camera([[0.0, c1, off(c1, h, 0.5), 36.0], [6.5, c2, off(c2, h, -0.5), 32.0], [13.0, c3, off(c3, h, -0.4), 38.0]])
	cs.say(0.6, PD, "The Registry wrote that Aljay turned: that he went over to the Forsaken of his own will. They struck all three of us from the books and burned the songs.", 4.6, C_PD)
	cs.at(5.2, func() -> void:
		pd.detach(&"shard")
		pd.play(&"cs_pd_hand", 0.3))
	cs.say(5.4, PD, "I have not closed this hand on a hilt since. His brand forbids it while he lives.", 3.6, C_PD)
	cs.at(9.2, func() -> void:
		pd.play(&"cs_pd_shard", 0.4)
		CSKit.shard_in_hand(pd, "weapon.L", 1.6))
	cs.say(9.4, PD, "But that shard is warm. Aljay is alive.", 3.2, C_PD)
