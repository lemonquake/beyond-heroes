extends Cutscene
## bh-021 — the prologue of a new game: Jre and the Age of Wrath, the Binding, the Holy War coming over the sea,
## Malasugue's hearth, and the waypoint on the Sanctuary Terrace waking after three dark winters. The hero is thrown
## out of the light onto the terrace and gets up; a spirit takes shape beside them (the starter Tempo, whose
## conversation begins as the prologue ends). Can be skipped whole.

const N := ""
const C_N := Color(0.85, 0.8, 0.7)

var _map := Transform3D.IDENTITY
var _spot := Transform3D.IDENTITY

func _init() -> void:
	title = "Beyond Heroes"
	skip_all = true
	music = &"music_legend"

func build(_cs: CutscenePlayer) -> Array:
	if Game.current_map:
		_map = Game.current_map.global_transform
		# the anchor stands on the waypoint dais and looks toward the spot where the hero lands (local +Z)
		var sp := Game.current_map.spawn_transform(&"waypoint").origin
		var tp: Teleporter = Game.current_map.teleporter(&"sanctuary_waypoint")
		var dais := tp.global_position if tp else sp + Vector3(0, 0, -3.9)
		var d := sp - dais
		d.y = 0.0
		_spot = Transform3D(Basis(Vector3.UP, atan2(d.x, d.z)), dais)
	return [
		{"name": "Jre", "length": 9.0, "run": _jre, "fade_in": 0.0},
		{"name": "Malasugue", "length": 8.5, "run": _town},
		{"name": "The Waypoint Wakes", "length": 7.5, "run": _wake},
		{"name": "The Chosen", "length": 9.0, "run": _arrival},
	]

func finish(_cs: CutscenePlayer) -> void:
	Game.set_world_flag(&"prologue_seen")

func _jre(cs: CutscenePlayer) -> void:
	cs.use_map(_map)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	cs.fade(0.0, 1.0, 0.0)
	cs.caption(0.3, "Jre", "", 3.2)
	cs.say(1.2, N, "Jre remembers the Age of Wrath: Gigas that walked like mountains, Tyrants that ruled the sky, Oros coiled beneath the sea.", 4.4, C_N)
	cs.fade(4.6, 0.0, 2.4)
	cs.say(5.8, N, "The first heroes bound them to sleep, and swore oaths to keep them sleeping.", 3.2, C_N)
	cs.camera([[0.0, Vector3(-60.0, 46.0, 90.0), Vector3(0.0, 0.0, -10.0), 50.0], [9.0, Vector3(-42.0, 34.0, 66.0), Vector3(0.0, 2.0, -10.0), 46.0]])

func _town(cs: CutscenePlayer) -> void:
	cs.use_map(_map)
	cs.camera([[0.0, Vector3(24.0, 16.0, 34.0), Vector3(0.0, 2.0, 4.0), 48.0], [8.5, Vector3(9.0, 8.0, 10.0), Vector3(0.0, 3.0, -16.0), 44.0]])
	cs.say(0.4, N, "A thousand years later the oaths are breaking. Beyond the sea, three nations have sworn a Holy War to wake the old things.", 4.2, C_N)
	cs.say(4.8, N, "On Salmonan, one town still keeps its hearth lit.", 3.2, C_N)

func _wake(cs: CutscenePlayer) -> void:
	cs.use_map(_spot)
	var dais := Vector3.ZERO
	var sh := cs.fx(LegendFX.light_shaft(Color(0.6, 0.9, 1.0), 40.0, 0.6, 1.6), dais) as MeshInstance3D
	sh.visible = false
	cs.camera([[0.0, Vector3(-3.0, 2.4, 7.5), dais + Vector3(0, 1.6, 0), 46.0], [7.5, Vector3(-1.8, 1.4, 5.6), dais + Vector3(0, 3.2, 0), 44.0]])
	cs.say(0.4, N, "Three winters ago the dead came up its roads, and the waypoint on the Sanctuary Terrace went dark.", 3.6, C_N)
	cs.say(4.4, N, "Tonight, it woke.", 2.6, C_N)
	cs.at(4.2, func() -> void:
		sh.visible = true
		cs.flash(cs.t, Color(0.7, 0.95, 1.0), 0.6)
		cs.fx(VFXLib.ring_wave(Color(0.55, 0.9, 1.0), 7.0, 0.9, 0.8), dais + Vector3(0, 0.1, 0)))
	cs.shake(4.2, 0.6, 1.0)
	cs.sfx(4.2, &"arcane_surge", 0.0)
	cs.sfx(4.4, &"blink", 0.0)

func _arrival(cs: CutscenePlayer) -> void:
	cs.use_map(_spot)
	var hero := cs.hero(&"hero", Vector3(0, 0, 3.0), 180.0)
	hero.play(&"getup", 0.0, 0.0)
	var spirit := cs.actor(&"spirit", "res://assets/characters/knight.glb", 1.0, Vector3(1.4, 0, 4.2), -120.0)
	var ghost := CSKit.ghost_material()
	ghost.set_shader_parameter("power", 0.0)
	spirit.set_override(ghost)
	spirit.play(&"idle", 0.0)
	var dais := Vector3.ZERO
	var sh := cs.fx(LegendFX.light_shaft(Color(0.6, 0.9, 1.0), 40.0, 0.6, 1.6), dais) as MeshInstance3D
	cs.camera([[0.0, Vector3(-1.4, 0.5, 4.4), Vector3(0.0, 0.3, 2.8), 44.0], [3.2, Vector3(-1.9, 1.0, 5.2), Vector3(0.1, 0.9, 3.0), 44.0],
		[6.0, Vector3(-2.2, 1.8, 6.4), Vector3(0.6, 1.2, 3.2), 46.0], [9.0, Vector3(-2.6, 2.2, 7.4), Vector3(0.6, 1.2, 3.0), 48.0]])
	cs.at(1.0, func() -> void: hero.play(&"getup", 0.0, 0.62))
	cs.sfx(1.0, &"body_fall", -4.0)
	cs.at(2.2, func() -> void:
		var tw := cs.tween(sh)
		tw.tween_method(func(v: float) -> void: (sh.material_override as ShaderMaterial).set_shader_parameter("power", v), 1.0, 0.0, 4.0))
	cs.at(3.6, func() -> void:
		cs.fx(VFXLib.ring_wave(Color(0.55, 0.9, 1.0), 2.5, 0.6, 0.4), Vector3(1.5, 0.1, 2.2))
		var tw := cs.tween(spirit)
		tw.tween_method(func(v: float) -> void: ghost.set_shader_parameter("power", v), 0.0, 1.0, 2.0))
	cs.sfx(3.6, &"heal", -2.0)
	cs.say(5.6, Dialogue.starter_name(Game.hero) if Game.hero else "Tobren", "Easy. Easy. The waypoint threw you harder than it threw me.", 3.0, Color(0.6, 0.85, 1.0))
	cs.fade(8.2, 1.0, 0.8)
