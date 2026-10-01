extends Cutscene
## bh-029 — the hero lands at Agdao. The Sunwake comes in under the terraces, every lamp on them stuttering;
## the hero steps down onto the pier where Terax, Warden of Agdao, is waiting. Terax tells of the man who came over the
## same water two winters ago — Aljay, broken chain links hanging from his wrists — and of the three Vaults they cleared
## together so that people could cross the Bridge of Death; then of the chain-priests' return, and where to begin.
## Map-local coordinates (DataZarael): the pier runs north-south at x = -20, the ship lies east of it.

const C_TX := Color(0.95, 0.78, 0.4)
const C_IL := Color(0.55, 0.75, 0.9)
const BLACKWIRE := Color(1.0, 1.0, 1.0)

var _map := Transform3D.IDENTITY
var _deck := DataZarael.AG_DECK_Y

func _init() -> void:
	title = "Agdao"
	skip_all = true
	music = &"aljay_theme"

func build(cs: CutscenePlayer) -> Array:
	if Game.current_map:
		_map = Game.current_map.global_transform
	for n in cs.get_tree().get_nodes_in_group(&"zr_ship_model"):
		cs.hide_node(n as Node3D)
	return [
		{"name": "Zarael", "length": 8.0, "run": _arrive},
		{"name": "The Pier", "length": 10.0, "run": _pier},
		{"name": "Two Winters Ago", "length": 11.0, "run": _aljay, "fade_in": 0.0},
		{"name": "The Three Vaults", "length": 9.0, "run": _vaults},
		{"name": "The Crown of Steps", "length": 10.0, "run": _crown},
	]

func finish(_cs: CutscenePlayer) -> void:
	Game.set_world_flag(DataZarael.F_TERAX, true)

func _ship(cs: CutscenePlayer, from: Vector3, to: Vector3, dur: float) -> Node3D:
	if not ResourceLoader.exists("res://assets/environment/zr_ship.glb"):
		return null
	var s: Node3D = MapBuilder.scene("zr_ship").instantiate()
	MaterialLibrary.apply_environment(s)
	cs.fx(s, from)
	if dur > 0.0:
		var tw := cs.tween(s)
		tw.tween_property(s, "global_position", cs.g(to), dur).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	return s

func _cast(cs: CutscenePlayer) -> Array:
	cs.use_map(_map)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var tx_node := cs.npc(&"terax")
	cs.hide_node(tx_node)
	var il_node := cs.npc(&"ilsa_agdao")
	cs.hide_node(il_node)
	var tx := cs.copy(&"terax", tx_node, DataZarael.AG_TERAX + Vector3(0, _deck, 0), 0.0) if tx_node else null   # facing the hero coming up the pier
	var hero := cs.hero(&"hero", DataZarael.AG_SPAWN + Vector3(0, _deck, 0), 180.0)
	return [tx, hero, il_node]

func _arrive(cs: CutscenePlayer) -> void:
	cs.use_map(_map)
	if Game.player:
		cs.hide_node(Game.player as Node3D)
	var berth := DataZarael.AG_SHIP
	_ship(cs, berth + Vector3(14.0, 0, 46.0), berth, 7.5)
	cs.camera([[0.0, Vector3(38.0, 9.0, 128.0), Vector3(-4.0, 14.0, 10.0), 50.0],
		[8.0, Vector3(22.0, 7.0, 100.0), Vector3(-6.0, 18.0, -20.0), 46.0]])
	cs.caption(0.6, "Zarael", "Agdao, the terraced harbour", 5.5)
	cs.sfx(0.2, &"water_wave", -6.0)
	cs.say(4.4, "Captain Ilsa Rhondar", "There she is. Look at the lamps: see how they stutter? That is what I warned you about.", 3.4, C_IL)
	cs.fade(7.3, 1.0, 0.6)

func _pier(cs: CutscenePlayer) -> void:
	var c := _cast(cs)
	_ship(cs, DataZarael.AG_SHIP, DataZarael.AG_SHIP, 0.0)
	var tx: CutsceneActor = c[0]
	var hero: CutsceneActor = c[1]
	cs.fade(0.0, 0.0, 0.8)
	hero.play(&"walk", 0.0)
	cs.move(hero, 0.0, DataZarael.AG_TERAX + Vector3(0, _deck, 3.2), 3.4, 180.0)
	cs.clip(hero, 3.4, &"idle", 0.3)
	if tx:
		tx.play(&"idle", 0.0)
	var t := DataZarael.AG_TERAX + Vector3(0, _deck, 0)
	cs.camera([[0.0, t + Vector3(-3.2, 2.4, -3.0), t + Vector3(0, 1.4, 6.0), 40.0],
		[3.6, t + Vector3(-2.6, 2.0, -2.2), t + Vector3(0, 1.5, 3.2), 36.0],
		[3.7, t + Vector3(1.4, 1.75, 2.0), t + Vector3(0, 1.7, 0), 32.0, true],
		[10.0, t + Vector3(1.1, 1.7, 1.6), t + Vector3(0, 1.75, 0), 28.0]])
	cs.say(3.8, "Terax", "So you are the one who broke a Kharvenn-made chain. Terax, Warden of Agdao. I sent Ilsa for you.", 3.6, C_TX)
	cs.say(7.4, "Terax", "Walk with me. I will tell you why, and who came before you.", 2.6, C_TX)
	cs.fade(9.4, 1.0, 0.6)

func _aljay(cs: CutscenePlayer) -> void:
	cs.use_flashback("agdao_memory", func(root: Node3D) -> void: CSKit.void_set(root, Color(0.05, 0.02, 0.05), Color(0.16, 0.05, 0.12)))
	cs.vignette(true, 0.4)
	var aj := cs.legend(&"aljay", &"aljay", Vector3.ZERO, 180.0, false)
	aj.play(&"cs_aj_stand", 0.0)
	# broken chain links hanging from both wrists
	for hand in ["hand.L", "hand.R"]:
		var ch := LegendFX.ChainFX.new(CSKit.LEGION_EYES, 0.02)
		ch.from_node = aj.follow(hand)
		ch.to = cs.g(Vector3(0.45 if hand == "hand.R" else -0.45, 0.35, 0.2))
		ch.extend = 1.0
		ch.sag = 0.12
		cs.fx(ch)
	cs.attach_fx(aj, LegendFX.wrath_aura(0.45))
	for p: Array in [[Vector3(-1.4, 1.8, -0.8), 1.4], [Vector3(1.2, 2.4, 1.0), 2.2]]:
		var l := OmniLight3D.new()
		l.light_color = CSKit.WRATH
		l.light_energy = float(p[1])
		l.omni_range = 3.5
		cs.fx(l, p[0])
	cs.fade(0.0, 0.0, 1.2)
	cs.caption(0.4, "Two winters ago", "Agdao's pier", 3.4)
	cs.camera([[0.0, Vector3(0.6, 1.4, -3.6), Vector3(0.0, 1.6, 0.0), 40.0], [11.0, Vector3(0.35, 1.7, -2.1), Vector3(0.0, 1.95, 0.0), 30.0]])
	cs.say(1.6, "Terax", "Two winters ago a man came over that same water. Black dragon-scale. Red eyes.", 3.6, C_TX)
	cs.say(5.4, "Terax", "Broken chain links hanging from his wrists, like bracelets. He did not give his name. He did not have to.", 3.8, C_TX)
	cs.at(9.2, func() -> void: cs.flash(cs.t, CSKit.WRATH, 0.4))
	cs.sfx(9.2, &"boss_roar", -8.0)
	cs.say(9.3, "Terax", "Aljay.", 1.6, CSKit.WRATH)

func _vaults(cs: CutscenePlayer) -> void:
	cs.use_flashback("agdao_memory", Callable())
	var aj := cs.legend(&"aljay", &"aljay", Vector3(-0.8, 0, 0), 160.0, false)
	aj.play(&"walk", 0.0)
	cs.move(aj, 0.0, Vector3(-0.8, 0, -4.0), 8.5)
	var tx_model := DataNpcsZarael._m("terax", "officer")
	var tx := cs.actor(&"terax_fb", tx_model, 1.0, Vector3(0.9, 0, 0.4), 160.0)
	tx.play(&"walk", 0.0)
	cs.move(tx, 0.0, Vector3(0.9, 0, -3.6), 8.5)
	cs.camera([[0.0, Vector3(2.6, 1.6, 3.4), Vector3(0.0, 1.3, -1.0), 44.0], [9.0, Vector3(1.4, 2.2, 1.0), Vector3(0.0, 1.0, -4.0), 48.0]])
	cs.say(0.6, "Terax", "He went down into the three Vaults with me, where no one had come back from. The Jade Sepulchre. The Obsidian Engine. The Veinworks.", 4.4, C_TX)
	cs.say(5.2, "Terax", "We cleared them. For the first time in five years, people crossed the Bridge of Death.", 3.4, C_TX)
	cs.at(3.0, func() -> void: cs.flash(cs.t, Color(0.5, 1.0, 0.6), 0.25))
	cs.at(4.6, func() -> void: cs.flash(cs.t, Color(1.0, 0.55, 0.2), 0.25))
	cs.at(6.2, func() -> void: cs.flash(cs.t, BLACKWIRE, 0.25))
	cs.shake(3.0, 0.3, 3.5)
	cs.fade(8.3, 1.0, 0.7)

func _crown(cs: CutscenePlayer) -> void:
	cs.vignette(false, 0.3)
	var c := _cast(cs)
	_ship(cs, DataZarael.AG_SHIP, DataZarael.AG_SHIP, 0.0)
	var tx: CutsceneActor = c[0]
	var hero: CutsceneActor = c[1]
	cs.place(hero, DataZarael.AG_TERAX + Vector3(0, _deck, 3.2), 180.0)
	hero.play(&"idle", 0.0)
	if tx:
		tx.play(&"idle", 0.0)
	cs.fade(0.0, 0.0, 0.8)
	var crown := DataZarael.AG_WIREKEEPER + Vector3(0, 30.0, 0)
	cs.camera([[0.0, Vector3(-30.0, 12.0, 70.0), Vector3(-10.0, 10.0, 10.0), 44.0],
		[7.0, Vector3(-12.0, 24.0, 40.0), crown, 42.0],
		[7.1, DataZarael.AG_TERAX + Vector3(1.9, _deck + 1.9, 2.2), DataZarael.AG_TERAX + Vector3(0, _deck + 1.6, 0), 34.0, true],
		[10.0, DataZarael.AG_TERAX + Vector3(1.4, _deck + 1.8, 1.7), DataZarael.AG_TERAX + Vector3(0, _deck + 1.7, 0), 30.0]])
	cs.say(0.4, "Terax", "Last winter the chain-priests came back under a new master. The Vaults woke again, worse. The Blackwire is in our streets now.", 4.2, C_TX)
	cs.say(4.8, "Terax", "Climb the Crown of Steps. Wirekeeper Halvessa Orn keeps the last working conduit at the top.", 3.0, C_TX)
	cs.say(7.4, "Terax", "She can tell you what the wire is doing. I can only tell you who to hit.", 2.4, C_TX)
