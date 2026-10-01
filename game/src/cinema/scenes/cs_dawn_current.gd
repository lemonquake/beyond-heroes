extends Cutscene
## bh-029 — the Dawn Engine wakes. The hero lays a hand on the Wirewrights' engine in the Heart Citadel; the loose
## Kharvenn chains fall away, the three bronze rings spin up, and the stutter in every wire steadies into clean white light
## (`zr_heartwire_restored` is set at the flash, so the whole map brightens in the shot). Far below, something
## enormous sighs, and goes back to sleep.

const GOLD := MaterialLibrary.ZR_GLOW
const BLACKWIRE := MaterialLibrary.ZR_GLOW

var _map := Transform3D.IDENTITY

func _init() -> void:
	title = "The Dawn Current"
	skip_all = true
	music = &"main_theme"

func build(cs: CutscenePlayer) -> Array:
	if Game.current_map:
		_map = Game.current_map.global_transform
	return [
		{"name": "A Hand on the Engine", "length": 7.0, "run": _hand},
		{"name": "The Dawn Current", "length": 9.0, "run": _wake},
		{"name": "Zarael Sleeps", "length": 7.0, "run": _sleep},
	]

func finish(_cs: CutscenePlayer) -> void:
	if not Game.has_flag(DataZarael.F_RESTORED):
		Game.set_world_flag(DataZarael.F_RESTORED, true)

func _cast(cs: CutscenePlayer) -> CutsceneActor:
	cs.use_map(_map)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var e := DataZarael.HC_ENGINE
	var hero := cs.hero(&"hero", e + Vector3(0, 0, 8.5), 180.0)
	hero.play(&"idle", 0.0)
	return hero

func _hand(cs: CutscenePlayer) -> void:
	var hero := _cast(cs)
	var e := DataZarael.HC_ENGINE
	cs.move(hero, 0.2, e + Vector3(0, 0, 7.2), 1.6)
	cs.clip(hero, 0.2, &"walk", 0.2)
	cs.clip(hero, 1.8, &"interact_teleport", 0.25, 0.6)
	cs.camera([[0.0, e + Vector3(-7.0, 3.0, 16.0), e + Vector3(0, 4.0, 0), 44.0], [7.0, e + Vector3(-4.0, 2.6, 12.0), e + Vector3(0, 3.0, 4.0), 38.0]])
	cs.sfx(2.4, &"arcane_charge", 0.0)
	cs.at(2.6, func() -> void:
		cs.fx(VFXLib.ring_wave(GOLD, 5.0, 0.8), e + Vector3(0, 0.2, 5.0))
		cs.flash(cs.t, GOLD, 0.25))
	cs.shake(3.0, 0.4, 3.0)
	cs.caption(4.0, "The Dawn Engine", "The Heart Citadel", 3.0)

func _wake(cs: CutscenePlayer) -> void:
	var hero := _cast(cs)
	hero.play(&"interact_teleport", 0.0, 0.5)
	var e := DataZarael.HC_ENGINE
	var shaft := LegendFX.light_shaft(GOLD, 60.0, 3.0, 5.0)
	cs.fx(shaft, e + Vector3(0, 6.0, 0))
	shaft.visible = false
	cs.camera([[0.0, e + Vector3(14.0, 4.0, 18.0), e + Vector3(0, 6.0, 0), 50.0], [9.0, e + Vector3(22.0, 12.0, 26.0), e + Vector3(0, 10.0, 0), 56.0]])
	cs.sfx(0.5, &"boss_phase", 0.0)
	cs.at(2.2, func() -> void:
		cs.flash(cs.t, Color.WHITE, 0.6)
		shaft.visible = true
		Game.set_world_flag(DataZarael.F_RESTORED, true)
		for i in 3:
			cs.fx(VFXLib.ring_wave(GOLD, 12.0 + i * 8.0, 1.2 + i * 0.4, 0.6), e + Vector3(0, 0.3, 0)))
	cs.sfx(2.2, &"holy_chime", 0.0)
	cs.shake(2.2, 0.9, 2.0)

func _sleep(cs: CutscenePlayer) -> void:
	_cast(cs)
	var e := DataZarael.HC_ENGINE
	cs.camera([[0.0, e + Vector3(0, 40.0, 70.0), e + Vector3(0, 0, -10.0), 50.0], [7.0, e + Vector3(0, 60.0, 95.0), e + Vector3(0, 0, -20.0), 54.0]])
	cs.sfx(1.0, &"earth_quake", -6.0)
	cs.shake(1.0, 0.25, 4.0)
	cs.caption(1.6, "Zarael sleeps", "The Heartwire burns steady again", 4.5)
	cs.fade(6.2, 1.0, 0.8)
