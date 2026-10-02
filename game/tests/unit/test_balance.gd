extends TestCase
## bh-010 anti-meta balance gate. Every class, with its starting gear and the same skill-point budget spent by the same
## rule, fights neutral training dummies in a real map at levels 1 / 10 / 20 / 30:
##   single  one dummy                        -> sustained single-target damage per second
##   aoe     six dummies in a tight ring      -> area damage per second
##   ehp     max HP x (raw hit / hit taken)   -> effective HP against a standard monster blow (1,000 rolls)
## Power score = sqrt(single x aoe) x sqrt(ehp). Gates (contract bh-010): every class within +-20% of the mean power at
## each level. Results are printed as BALANCE lines and written to work/lemondev/bh-010/evidence/balance.json.
## The bot presses the same controls a player would: skills in priority order (longest cooldown first), otherwise the
## basic attack. Knights switch on their learned offensive aura. Numbers are simulation results, not a player study.

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
const LEVELS := [1, 10, 20, 30]
const SIM_SECONDS := 10.0
const BAND := 0.20
const RANGED := [&"mage", &"ranger"]
const NO_DAMAGE := [&"buff", &"blink", &"vault", &"veil", &"aura", &"mark"]

var _holder: Node3D
var _saved := {}
var _player: Player
var _results := {}

func _init() -> void:
	strict = true

func _tree() -> SceneTree:
	return host.get_tree()

func _frames(n := 1) -> void:
	for i in n:
		await _tree().physics_frame

## The same spending rule for every class: every third point goes to a passive or aura (deepest first), the rest
## deepen the damaging skill with the highest rank that can still grow (tree order breaks ties), so builds focus like
## a player's would instead of spreading one point everywhere.
static func build(h: HeroData, lvl: int) -> void:
	var st := h.skill_tree
	var pts := h.progress.skill_points
	var i := 0
	while pts > 0:
		var want_support := i % 3 == 2
		var best: Dictionary = {}
		var best_rank := -1
		for pass_n in 2:
			for n in st.tree.nodes:
				if st.can_rank_up(n.id, pts, lvl) != "":
					continue
				# bh-016: levels run to 25, but this rule measures the build a player reaches at the old cap
				if st.rank(n.id) >= int(n.get("base_rank", n.get("max_rank", 1))):
					continue
				var kind: String = n.get("kind", "skill")
				var s: SkillDef = DB.skill(n.get("skill", n.id)) if kind == "skill" else null
				var support := kind == "passive" or (s != null and s.is_aura())
				var damaging := kind == "skill" and s != null and not s.behavior in NO_DAMAGE
				if pass_n == 0 and not ((want_support and support) or (not want_support and damaging)):
					continue
				if pass_n == 1 and not (support or damaging):
					continue
				if st.rank(n.id) > best_rank:
					best_rank = st.rank(n.id)
					best = n
			if not best.is_empty():
				break
		if best.is_empty():
			break
		pts -= st.rank_up(best.id, pts, lvl)
		i += 1
	h.progress.skill_points = pts
	h._skills_changed()

func _hero(cls: StringName, lvl: int) -> HeroData:
	var h := Game.new_hero(cls, "BalanceTest")
	if lvl > 1:
		h.progress.add_xp(XpCurve.total_xp_for_level(lvl))
	build(h, lvl)
	return h

func _begin(h: HeroData) -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null, "ts": Engine.time_scale}
	_holder = Node3D.new()
	_holder.name = "BalanceWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = h
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"start")
	_player.bind(h)
	Engine.time_scale = 6.0
	await _frames(2)

func _end() -> void:
	Input.action_release(&"primary")
	Engine.time_scale = float(_saved.get("ts", 1.0))
	for e in _tree().get_nodes_in_group(&"enemy"):
		e.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

## A neutral dummy: no resistances, standing still, a deep HP pool that is topped up every frame (damage is counted).
func _dummy_def() -> EnemyDef:
	var d: EnemyDef = DB.enemy(&"hollow_soldier").duplicate()
	d.hp = 20000.0
	d.can_be_elite = false
	d.resistances = {}
	d.immune = []
	d.traits = []
	d.blocks_front = false
	return d

func _spawn(n: int, lvl: int, at: Vector3) -> Array:
	var out := []
	var d := _dummy_def()
	for i in n:
		var off := Vector3.ZERO if n == 1 else Vector3(cos(TAU * i / n), 0, sin(TAU * i / n)) * 1.4
		var e := Spawner.spawn_enemy(Game.current_map, d, lvl, [], at + off, DataEnemies.DIFFICULTY[1])
		if e:
			e.set_physics_process(false)
			out.append(e)
	return out

## Damage the class deals to `n` dummies in SIM_SECONDS of play, per second.
func _dps(h: HeroData, lvl: int, n: int) -> float:
	await _begin(h)
	# A melee player steps up to the blow: stand where the weapon reaches. The old fixed 2.4 m is out of a dagger's 1.9 m reach, so a
	# Shadowblade bot never landed an attack (0.7 damage a second) and every other class then measured far above the mean.
	var loadout := h.compute_stats().loadout
	var reach: float = loadout.main_type.reach if loadout and loadout.main_type else 2.4
	var dist := 7.0 if h.cls.id in RANGED else (2.4 if reach >= 2.4 else reach * 0.85)
	var fwd := _player.forward()
	var center := _player.global_position + fwd * (dist + (1.4 if n > 1 else 0.0))
	var es := _spawn(n, lvl, center)
	await _frames(2)
	_player.aim_override = center
	_player.aim_point = Vector3(center.x, _player.global_position.y, center.z)
	for sid in h.learned_skills():
		var s := DB.skill(sid)
		if s and s.is_aura() and s.aura_kind == &"offense" and h.active_aura == &"":
			_player.toggle_aura(sid)
	var order: Array = h.learned_skills().filter(func(sid): return DB.skill(sid) and not DB.skill(sid).behavior in NO_DAMAGE)
	order.sort_custom(func(a, b): return DB.skill(a).cooldown > DB.skill(b).cooldown)
	var t := 0.0
	var holding := false
	var dealt := 0.0
	while t < SIM_SECONDS:
		_player.hp = _player.max_hp()
		for e in es:
			if is_instance_valid(e) and e.alive:
				dealt += e.max_hp() - e.hp
				e.hp = e.max_hp()
		if _player.action == null and _player.channel_skill == &"":
			var cast := false
			for sid in order:
				if _player.skill_block_reason(sid) == "":
					if holding:
						Input.action_release(&"primary")
						holding = false
					_player._start_skill(sid)
					cast = true
					break
			if not cast and not holding:
				Input.action_press(&"primary")
				holding = true
		await _tree().physics_frame
		t += Engine.time_scale / Engine.physics_ticks_per_second
	Input.action_release(&"primary")
	for e in es:
		if is_instance_valid(e) and e.alive:
			dealt += e.max_hp() - e.hp
		elif is_instance_valid(e):
			push_warning("balance dummy died")
	_end()
	return dealt / SIM_SECONDS

## Effective HP against a standard level-appropriate physical monster blow (evasion, block and armour all count).
func _ehp(h: HeroData, lvl: int) -> float:
	var st := h.compute_stats()
	var mon := DB.enemy(&"hollow_soldier")
	var atk := DerivedStats.new()
	atk.level = lvl
	var r := rng(lvl)
	var raw := 0.0
	var taken := 0.0
	var base := (mon.damage_min + mon.damage_max) * 0.5 * mon.scaled(lvl) * 2.0
	for i in 1000:
		var req := DamageRequest.new()
		req.kind = DamageRequest.Kind.ATTACK
		req.attacker = atk
		req.target = st
		req.base_min = base
		req.base_max = base
		req.use_weapon = false
		req.can_crit = false
		var res := DamagePipeline.compute(req, r)
		raw += base
		taken += float(res.total)
	return st.get_stat(&"max_hp") * raw / maxf(1.0, taken)

func test_power_is_within_band_at_every_level() -> void:
	for lvl in LEVELS:
		var row := {}
		for cls in CLASSES:
			var single := await _dps(_hero(cls, lvl), lvl, 1)
			var aoe := await _dps(_hero(cls, lvl), lvl, 6)
			var ehp := _ehp(_hero(cls, lvl), lvl)
			var power := sqrt(maxf(single, 0.0) * maxf(aoe, 0.0)) * sqrt(ehp)
			row[cls] = {"single": single, "aoe": aoe, "ehp": ehp, "power": power}
			print("BALANCE L%d %-11s single %7.1f  aoe %7.1f  ehp %7.0f  power %8.1f" % [lvl, cls, single, aoe, ehp, power])
		var mean := 0.0
		for cls in CLASSES:
			mean += row[cls].power
		mean /= CLASSES.size()
		for cls in CLASSES:
			var dev: float = row[cls].power / maxf(mean, 0.001) - 1.0
			row[cls]["dev"] = dev
			ok(absf(dev) <= BAND, "L%d %s power %.1f is within %d%% of the mean %.1f (%+.0f%%)" % [lvl, cls, row[cls].power, roundi(BAND * 100), mean, dev * 100.0])
		_results["L%d" % lvl] = row
	var f := FileAccess.open(ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-010/evidence/balance.json"), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_results, "  "))
	done()
