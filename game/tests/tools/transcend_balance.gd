extends Node
## Class Transcendence balance sheet. The bh-010 combat bot (test_balance.gd: same controls a player uses, skills by
## longest cooldown, finishers on a full bar) fights neutral dummies on a real map, for every family at levels
## 60 / 121 / 180 / 300 and every build of that family:
##   base     the starting class, no advancement
##   first    the first transcendence (its three skills and talents granted)
##   <master> each master class
##   <master>+max  (level 300) every transcendence skill and talent at its highest rank (worst case)
## Every build has the same gear (the family's starting bases made at the hero's level, Elite, fixed seeds), the same
## attribute rule and the same skill/talent point budget spent by test_balance.build() over the hero's own tree.
## Measured, each separately (never summed into one score):
##   single   damage per second to one dummy            aoe   damage per second to six dummies in a ring
##   ehp      effective HP against a standard monster blow (talents included)
##   live_ehp effective HP against that blow sampled during the fight (active buffs, zones and statuses count)
##   sustain  HP the hero restores to itself plus barrier HP it gains, per second, while held at half health
## Dummies never die (topped up every frame), so kill-based traits (Dread, Soul Harvest, Collapse, Blood Price) are not
## in these numbers. Writes output/class-transcendence/balance.csv.
##   godot --headless --path game res://tests/tools/transcend_balance.tscn [-- --levels=60,121 --families=knight]

const SIM_SECONDS := 24.0      # long enough for most transcendence cooldowns to come round once
const RANGED := [&"mage", &"ranger"]
const NO_DAMAGE := [&"buff", &"blink", &"vault", &"veil", &"aura", &"mark"]
const PRIMARY := {&"knight": [&"str", &"spi"], &"ranger": [&"dex", &"agi"], &"mage": [&"int", &"wis"], &"shadowblade": [&"dex", &"agi"]}

var _holder: Node3D
var _player: Player
var _rows: Array = []
var _out := ""

func _ready() -> void:
	var levels := [60, 121, 180, 300]
	var fams := [&"knight", &"ranger", &"mage", &"shadowblade"]
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--levels="):
			levels = Array(a.substr(9).split(",")).map(func(x): return int(x))
		if a.begins_with("--families="):
			fams = Array(a.substr(11).split(",")).map(func(x): return StringName(x))
		if a.begins_with("--out="):
			_out = a.substr(6)
	if _out == "":
		_out = ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence/balance.csv")
	await get_tree().process_frame
	for fam in fams:
		var first: StringName = DataTranscendence.children_of(fam)[0]
		var masters: Array = DataTranscendence.children_of(first)
		for lvl in levels:
			var builds: Array = [["base", []], ["first", [first]]]
			if lvl >= 120:
				for m in masters:
					builds.append([String(m), [first, m]])
			if lvl >= 300:
				for m in masters:
					builds.append([String(m) + "+max", [first, m], true])
			for b in builds:
				var maxed: bool = b.size() > 2 and b[2]
				var single := await _dps(_hero(fam, lvl, b[1], maxed), lvl, 1)
				var aoe := await _dps(_hero(fam, lvl, b[1], maxed), lvl, 6)
				var ehp := _ehp(_hero(fam, lvl, b[1], maxed), lvl)
				var row := {"family": String(fam), "level": lvl, "build": b[0], "class": String((b[1] as Array).back() if not (b[1] as Array).is_empty() else fam),
					"single": single.dps, "aoe": aoe.dps, "ehp": ehp, "live_ehp": single.live_ehp, "sustain": single.sustain, "casts": single.casts}
				_rows.append(row)
				print("TBAL %-11s L%-3d %-22s single %9.1f  aoe %9.1f  ehp %9.0f  live %9.0f  sustain %7.1f  casts %s" % [fam, lvl, b[0], single.dps, aoe.dps, ehp, single.live_ehp, single.sustain, single.casts])
	_write()
	get_tree().quit()

## A hero of `fam` at `lvl` that took `path`, with the shared gear, attribute and point rules.
func _hero(fam: StringName, lvl: int, path: Array, maxed := false) -> HeroData:
	var h := Game.new_hero(fam, "Balance")
	if lvl > 1:
		h.progress.add_xp(XpCurve.total_xp_for_level(lvl))
	# attributes: every free point into the family's two main attributes, alternating
	var attrs: Array = PRIMARY[fam]
	var i := 0
	while h.progress.free_points > 0:
		h.progress.allocated[attrs[i % 2]] = int(h.progress.allocated.get(attrs[i % 2], 0)) + 1
		h.progress.free_points -= 1
		i += 1
	for id in path:
		var r := ClassTranscendence.transcend(h, id)
		if not r.ok:
			push_error("transcend %s failed: %s" % [id, r.error])
	# the same gear for every build of the family: its starting bases, made at the hero's level
	var cls := DB.class_def(fam)
	for slot in h.equipment.slots.keys():
		if h.equipment.get_item(slot) != null:
			h.equipment.unequip(slot)
	var seed_i := 1
	for base_id in cls.starting_items:
		var it := DB.make_item(base_id, BH.Rarity.ELITE, mini(lvl, 300), 7000 + seed_i)
		seed_i += 1
		var slot := h.equipment.auto_slot(it)
		if slot == &"main_weapon" and h.equipment.get_item(&"main_weapon") != null:
			slot = &"off_weapon"
		h.equipment.equip(it, slot, lvl, TempoRules.NO_ATTR)
	preload("res://tests/unit/test_balance.gd").build(h, lvl)
	if maxed:
		for tr in [h.skill_tree, h.talent_tree]:
			for n in tr.tree.nodes:
				if n.has("granted_by"):
					tr.ranks[n.id] = int(n.get("max_rank", 1))
		h._skills_changed()
	return h

func _begin(h: HeroData) -> void:
	_holder = Node3D.new()
	_holder.name = "BalanceWorld"
	add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = h
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"start")
	_player.bind(h)
	Engine.time_scale = 6.0
	for i in 2:
		await get_tree().physics_frame
	_player.first_person = false

func _end() -> void:
	Input.action_release(&"primary")
	Engine.time_scale = 1.0
	for e in get_tree().get_nodes_in_group(&"enemy"):
		e.free()
	for t in TempoParty.actors(get_tree()):
		t.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.player = null
	Game.hero = null

func _dummy_def() -> EnemyDef:
	var d: EnemyDef = DB.enemy(&"hollow_soldier").duplicate()
	d.hp = 2000000.0
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

## {dps, sustain, casts} over SIM_SECONDS against `n` dummies.
func _dps(h: HeroData, lvl: int, n: int) -> Dictionary:
	await _begin(h)
	var loadout := h.compute_stats().loadout
	var reach: float = loadout.main_type.reach if loadout and loadout.main_type else 2.4
	var dist := 7.0 if h.cls.id in RANGED else (2.4 if reach >= 2.4 else reach * 0.85)
	var fwd := _player.forward()
	var center := _player.global_position + fwd * (dist + (1.4 if n > 1 else 0.0))
	var es := _spawn(n, lvl, center)
	for i in 2:
		await get_tree().physics_frame
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
	var restored := 0.0
	var casts := {}
	var half := _player.max_hp() * 0.5
	_player.hp = half
	var shield0 := _player.shield_hp
	# live defense: every half second, a standard monster blow against the hero's current stats (active buffs count)
	var mon := DB.enemy(&"hollow_soldier")
	var blow := (mon.damage_min + mon.damage_max) * 0.5 * mon.scaled(lvl) * 2.0
	var drng := RandomNumberGenerator.new()
	drng.seed = 4242 + lvl
	var raw := 0.0
	var taken := 0.0
	var next_blow := 0.0
	while t < SIM_SECONDS:
		if t >= next_blow:
			next_blow += 0.5
			_player.ensure_stats()
			var atk := DerivedStats.new()
			atk.level = lvl
			for k in 20:
				var req := DamageRequest.new()
				req.kind = DamageRequest.Kind.ATTACK
				req.attacker = atk
				req.target = _player.stats
				req.base_min = blow
				req.base_max = blow
				req.use_weapon = false
				req.can_crit = false
				raw += blow
				taken += float(DamagePipeline.compute(req, drng).total)
		_player.mana = _player.max_mana()     # Mana is not the measured limit (every build gets the same refill)
		restored += maxf(0.0, _player.hp - half)
		_player.hp = half
		restored += maxf(0.0, _player.shield_hp - shield0)
		shield0 = _player.shield_hp
		for e in es:
			if is_instance_valid(e) and e.alive:
				dealt += e.max_hp() - e.hp
				e.hp = e.max_hp()
		if _player.action == null and _player.channel_skill == &"":
			var cast := false
			for sid in order:
				if not _ready_to_spend(sid):
					continue
				if _player.skill_block_reason(sid) == "":
					if holding:
						Input.action_release(&"primary")
						holding = false
					_player._start_skill(sid)
					casts[sid] = int(casts.get(sid, 0)) + 1
					cast = true
					break
			if not cast and not holding:
				Input.action_press(&"primary")
				holding = true
		await get_tree().physics_frame
		t += Engine.time_scale / Engine.physics_ticks_per_second
	Input.action_release(&"primary")
	for e in es:
		if is_instance_valid(e) and e.alive:
			dealt += e.max_hp() - e.hp
	var new_casts := 0
	for sid in casts:
		if DataTranscendence.owner_of(sid) != &"":
			new_casts += casts[sid]
	var live := _player.max_hp() * raw / maxf(1.0, taken) if raw > 0.0 else 0.0
	_end()
	return {"dps": dealt / SIM_SECONDS, "sustain": restored / SIM_SECONDS, "live_ehp": live, "casts": "%d (%d new)" % [casts.values().reduce(func(a, b): return a + b, 0), new_casts]}

func _ready_to_spend(sid: StringName) -> bool:
	var s := DB.skill(sid)
	var res = _player.resource
	if s == null or res == null:
		return true
	if float(s.params.get("consume_combo", 0.0)) > 0.0 and res.kind == &"combo":
		return res.value >= 4.0
	if float(s.params.get("consume_focus", 0.0)) > 0.0 and res.kind == &"focus":
		return res.value >= ClassResource.STEADY_AT
	return true

func _ehp(h: HeroData, lvl: int) -> float:
	var st := h.compute_stats()
	var mon := DB.enemy(&"hollow_soldier")
	var atk := DerivedStats.new()
	atk.level = lvl
	var r := RandomNumberGenerator.new()
	r.seed = 9000 + lvl
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

func _write() -> void:
	var f := FileAccess.open(_out, FileAccess.WRITE)
	if f == null:
		push_error("cannot write %s" % _out)
		return
	f.store_line("family,level,build,class,single_dps,aoe_dps,ehp,live_ehp,sustain_per_s,casts")
	for r in _rows:
		f.store_line("%s,%d,%s,%s,%.1f,%.1f,%.0f,%.0f,%.1f,%s" % [r.family, r.level, r.build, r["class"], r.single, r.aoe, r.ehp, r.live_ehp, r.sustain, r.casts])
	print("WROTE ", _out)
