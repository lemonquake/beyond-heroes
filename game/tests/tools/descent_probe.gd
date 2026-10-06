extends Node
## bh-040 (The Descent): measures the late game the way a player meets it.
##   --mode=curves                   level table: experience per level, kills per level, monster health and blows, and the
##                                   reference heroes' best hits against them (stat math, no map)
##   --mode=hero --save=<file.json>  a saved hero's sheet and every learned skill's hit against monsters of its level
##   --mode=live --save=<file.json> [--map=<id>] [--spawn=<id>] [--seconds=180] [--boss=<enemy id>] [--solo]
##                                   the hero clears the map's camps with a bot (real AI, real damage both ways), then a
##                                   boss of its level is called in front of it
## The hero always plays in hidden slot 97 (slots 0-2 are the player's). Writes <out>/descent_<mode>.json
## (default out: output/bh-040).
##   Godot --headless --path game --fixed-fps 60 res://tests/tools/descent_probe.tscn -- --mode=live --save=C:/x/slot_1.json

const BudgetTest = preload("res://tests/unit/test_bh028_arena.gd")
const BalanceTest = preload("res://tests/unit/test_balance.gd")
const LEVELS := [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 141, 160, 180, 200, 250, 300]
const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
const NO_DAMAGE := [&"buff", &"blink", &"vault", &"veil", &"aura", &"mark"]

var args := {}
var out_dir := ""
var player: Player
var _press := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
		elif a.begins_with("--"):
			args[a.substr(2)] = "1"
	out_dir = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/bh-040")))
	DirAccess.make_dir_recursive_absolute(out_dir)
	Game.save_slot = 97
	# --descent=off measures the game as it was before bh-040 on the same build (Descent.enabled)
	Descent.enabled = String(args.get("descent", "on")) != "off"
	var mode := String(args.get("mode", "curves"))
	var report := {}
	match mode:
		"curves": report = _curves()
		"hero": report = _hero_sheet(_load_hero())
		"decompose": report = _decompose(_load_hero())
		"calibrate": report = await _calibrate()
		"live": report = await _live(_load_hero())
	var f := FileAccess.open(out_dir.path_join("descent_%s%s.json" % [mode, String(args.get("tag", ""))]), FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("DESCENT PROBE DONE ", mode)
	for a in _press.keys():
		Input.action_release(a)
	Game.in_session = false
	get_tree().quit(0)

func _load_hero() -> HeroData:
	if args.has("class"):
		# a synthetic committed hero (endgame_hero) with a belt of draughts, on --map
		var eh := endgame_hero(StringName(args["class"]), int(args.get("level", "100")), int(args.get("rarity", str(BH.Rarity.MASTER))))
		for pid in [&"superior_health_potion", &"superior_mana_potion"]:
			var it := DB.make_item(pid, BH.Rarity.COMMON, eh.progress.level, 7)
			if it:
				it.count = 30
				eh.inventory.add(it)
		eh.current_map = StringName(args.get("map", "zr_barrens"))
		eh.current_spawn = StringName(args.get("spawn", "start"))
		return eh
	var path := String(args.get("save", ""))
	var txt := FileAccess.get_file_as_string(path)
	var d = JSON.parse_string(txt)
	if not (d is Dictionary) or not d.has("hero"):
		push_error("descent_probe: cannot read %s" % path)
		get_tree().quit(1)
		return null
	var h := HeroData.from_dict(d.hero)
	if args.has("solo"):
		h.tempos.clear()
		h.quake_team.clear()
	if args.has("level"):
		var want := clampi(int(args.level), 1, BH.LEVEL_CAP)
		h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(want) - XpCurve.total_xp_for_level(h.progress.level) - h.progress.xp))
	return h

# ---- static tables ---------------------------------------------------------------------------------------------------

static func monster_level(hero_level: int) -> int:
	return maxi(1, CombatGrowth.encounter_level(1, hero_level)) if hero_level >= CombatBudget.ENCOUNTER_FROM else hero_level

## Average no-crit hit and the best sustained single-target rate of every damaging skill the hero knows (and the basic
## attack), against `target`.
static func skill_rows(h: HeroData, st: DerivedStats, target: DerivedStats) -> Array:
	var rows := []
	ItemCompare._add_weapon_rows(st)
	var req0 := DamageRequest.new()
	req0.kind = DamageRequest.Kind.ATTACK
	req0.attacker = st
	req0.target = target
	var basic := float(DamagePipeline.preview(req0).total)
	var aps := maxf(0.3, st.get_stat(&"attacks_per_second"))
	rows.append({"skill": "basic attack", "hit": basic, "per_s": basic * aps, "interval": 1.0 / aps})
	for id in h.learned_skills():
		var skill := DB.skill(id)
		if skill == null or skill.behavior in NO_DAMAGE:
			continue
		var p := h.resolved_skill(id)
		if not p.has("damage_min"):
			continue
		var req := DamageRequest.new()
		req.kind = skill.kind
		req.attacker = st
		req.target = target
		req.use_weapon = false
		req.base_min = float(p.damage_min)
		req.base_max = float(p.get("damage_max", req.base_min))
		if skill.kind == DamageRequest.Kind.SPELL:
			req.conversion = {skill.element: 1.0}
		else:
			req.use_weapon = skill.kind == DamageRequest.Kind.ATTACK and float(p.get("weapon_mult", 0.0)) > 0.0
			req.weapon_mult = float(p.get("weapon_mult", 1.0))
		var hit := float(DamagePipeline.preview(req).total)
		var speed := st.get_stat(&"cast_speed", 1.0) if skill.kind == DamageRequest.Kind.SPELL else st.get_stat(&"attack_speed", 1.0)
		var interval := maxf(1.0 / maxf(0.2, speed), skill.cooldown * (1.0 - st.get_stat(&"cdr")))
		var n := maxf(1.0, float(p.get("count", p.get("projectiles", 1.0))))
		rows.append({"skill": String(id), "rank": h.skill_rank(id), "hit": hit, "count": n, "interval": interval, "per_s": hit * n / interval})
	return rows

static func best(rows: Array, key: String) -> float:
	var b := 0.0
	for r in rows:
		b = maxf(b, float(r[key]))
	return b

static func blow(att: DerivedStats, def: EnemyDef, mult: float, target: DerivedStats) -> float:
	return BudgetTest.blow(att, def, mult, target)

func _curves() -> Dictionary:
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	var soldier := DB.enemy(&"hollow_soldier")
	var boss_def := DB.enemy(&"astrarch")
	var rows := []
	for L in LEVELS:
		var ml := monster_level(L)
		var xp_kill := float(XpCurve.monster_xp(ml, 1.0)) * XpCurve.level_diff_mult(L, ml)
		var normal := EnemyStats.build(soldier, ml, diff, [])
		var elite := EnemyStats.build(soldier, ml, diff, [], true)
		var row := {"level": L, "monster_level": ml, "xp_to_next": XpCurve.xp_to_next(L), "xp_per_kill": xp_kill,
			"kills_per_level": XpCurve.xp_to_next(L) / maxf(1.0, xp_kill), "normal_hp": normal.get_stat(&"max_hp"),
			"elite_hp": elite.get_stat(&"max_hp"), "normal_defense": normal.get_stat(&"defense"), "classes": {}}
		for cid in CLASSES:
			var h: HeroData = BudgetTest.geared(cid, L)
			BalanceTest.build(h, L)
			var st := h.compute_stats()
			var hp := st.get_stat(&"max_hp")
			var sk := skill_rows(h, st, normal)
			var top_hit := best(sk, "hit")
			var top_rate := best(sk, "per_s")
			var baseline := EnemyStats.build(boss_def, L, diff, [], false, true)
			var boss_hp := EnemyStats.boss_health(h, baseline)
			var bst := EnemyStats.build(boss_def, L, diff, [StatModifier.more(&"max_hp", boss_hp / baseline.get_stat(&"max_hp") - 1.0)], false, true)
			var boss_rate := best(skill_rows(h, h.compute_stats(), bst), "per_s")
			row.classes[String(cid)] = {"hp": hp, "best_hit": top_hit, "best_rate": top_rate,
				"hits_to_kill_normal": normal.get_stat(&"max_hp") / maxf(1.0, top_hit),
				"hits_to_kill_elite": elite.get_stat(&"max_hp") / maxf(1.0, top_hit),
				"normal_blow_pct": 100.0 * blow(normal, soldier, 1.0, st) / hp,
				"boss_hp": boss_hp, "boss_seconds_est": boss_hp / maxf(1.0, boss_rate)}
		rows.append(row)
		print("CURVE L%d mL%d next %d xp/kill %d kills/lvl %.0f | soldier hp %d elite %d | %s" % [L, ml, row.xp_to_next, xp_kill,
			row.kills_per_level, row.normal_hp, row.elite_hp, " ".join(CLASSES.map(func(c):
				var r: Dictionary = row.classes[String(c)]
				return "%s hp %d hit %d ->%.1f hits, blow %.1f%%, boss %.0fs" % [String(c).substr(0, 4), r.hp, r.best_hit, r.hits_to_kill_normal, r.normal_blow_pct, r.boss_seconds_est]))])
	return {"rows": rows}

# ---- a saved hero ------------------------------------------------------------------------------------------------

func _hero_sheet(h: HeroData) -> Dictionary:
	var L := h.progress.level
	var ml := monster_level(L)
	var diff: Dictionary = DataEnemies.DIFFICULTY[clampi(h.difficulty, 0, 3)]
	var st := h.compute_stats()
	var sheet := {}
	for k in [&"max_hp", &"max_mana", &"defense", &"evasion", &"spell_power", &"magic_damage", &"elemental_damage", &"damage",
			&"crit_chance", &"crit_damage", &"cast_speed", &"attack_speed", &"cdr", &"life_leech", &"xp_gain", &"int", &"wis", &"str"]:
		sheet[String(k)] = st.get_stat(k)
	var out := {"name": h.hero_name, "class": String(h.cls.id), "level": L, "path": h.transcendence_path.map(func(x): return String(x)),
		"stats": sheet, "targets": {}}
	for id in [&"hollow_soldier", &"glyphbound_warrior", &"coil_shaman"]:
		var def := DB.enemy(id)
		if def == null:
			continue
		var n := EnemyStats.build(def, ml, diff, [])
		var e := EnemyStats.build(def, ml, diff, [], true)
		var rows := skill_rows(h, h.compute_stats(), n)
		out.targets[String(id)] = {"hp": n.get_stat(&"max_hp"), "elite_hp": e.get_stat(&"max_hp"), "skills": rows,
			"hits_to_kill": n.get_stat(&"max_hp") / maxf(1.0, best(rows, "hit")), "elite_hits": e.get_stat(&"max_hp") / maxf(1.0, best(rows, "hit"))}
	var bdef := DB.enemy(StringName(args.get("boss", "astrarch")))
	var baseline := EnemyStats.build(bdef, L, diff, [], false, true)
	var bhp := EnemyStats.boss_health(h, baseline)
	out["boss"] = {"id": String(bdef.id), "hp": bhp, "hit_limit": minf(bhp * CombatGrowth.BOSS_HIT_SHARE, CombatGrowth.boss_hit_ceiling(L))}
	# what monster blows do to this hero (average roll, no evasion or block; crit where named), % of Maximum HP
	var hp := st.get_stat(&"max_hp")
	var mon := DB.enemy(&"glyphbound_warrior")
	var n0 := EnemyStats.build(mon, ml, diff, [])
	var ch := EnemyStats.build(mon, ml, diff, [StatModifier.flat(&"threat_rank", CombatBudget.Rank.CHAMPION), StatModifier.more(&"outgoing_damage", 0.25)], true)
	var bs := EnemyStats.build(bdef, L, diff, [], false, true)
	var raw := DerivedStats.new()
	raw.level = L
	raw.loadout = WeaponLoadout.new()
	out["blows_pct"] = {"normal_plain": 100.0 * BudgetTest.blow(n0, mon, 1.0, st) / hp,
		"normal_plain_unarmoured": 100.0 * BudgetTest.blow(n0, mon, 1.0, raw) / hp,
		"champion_heavy_crit": 100.0 * BudgetTest.blow(ch, mon, BudgetTest.heaviest(mon), st, true) / hp,
		"boss_plain": 100.0 * BudgetTest.blow(bs, bdef, 1.0, st) / hp,
		"boss_heavy_crit": 100.0 * BudgetTest.blow(bs, bdef, BudgetTest.heaviest(bdef), st, true) / hp,
		"boss_heavy_crit_unarmoured": 100.0 * BudgetTest.blow(bs, bdef, BudgetTest.heaviest(bdef), raw, true) / hp,
		"armor_dr": StatCalculator.armor_reduction(st.get_stat(&"defense"), ml), "evasion": st.get_stat(&"evasion"),
		"boss_accuracy": bs.get_stat(&"accuracy"), "evade_vs_boss": DamagePipeline.evade_chance(st.get_stat(&"evasion"), bs.get_stat(&"accuracy")),
		"boss_attacks": bdef.attacks.map(func(a): return "%s x%.2f %s" % [a.get("id", "?"), float(a.get("mult", 1.0)), a.get("kind", "")])}
	print("BLOWS ", JSON.stringify(out.blows_pct))
	print("HERO ", JSON.stringify(out))
	return out

## Where a saved hero's power comes from: the same hero with reference gear, with its points re-spent along the class
## build, and the reference hero of its level, each against the same normal monster (no crits, no player-only "more").
func _decompose(h: HeroData) -> Dictionary:
	var L := h.progress.level
	var target := EnemyStats.build(DB.enemy(&"glyphbound_warrior"), monster_level(L), DataEnemies.DIFFICULTY[1], [])
	var variants := {}
	variants["as saved"] = h
	var ref: HeroData = BudgetTest.geared(h.cls.id, L)
	var g := HeroData.from_dict(h.to_dict())
	for slot in BH.SLOTS:
		g.equipment.slots[slot] = ref.equipment.slots.get(slot)
	variants["reference gear"] = g
	var b := HeroData.from_dict(h.to_dict())
	b.progress.reset_attributes()
	b.progress.allocate_along_build(b.progress.free_points)
	variants["points along class build"] = b
	var bg := HeroData.from_dict(g.to_dict())
	for slot in BH.SLOTS:
		bg.equipment.slots[slot] = ref.equipment.slots.get(slot)
	bg.progress.reset_attributes()
	var majors: Array = bg.cls.major_attributes
	bg.progress.allocate_along_build(bg.progress.free_points)
	variants["reference gear + class build"] = bg
	BalanceTest.build(ref, L)
	variants["reference hero"] = ref
	var out := {}
	for k in variants:
		var hv: HeroData = variants[k]
		var st := hv.compute_stats()
		var rows := skill_rows(hv, st, target)
		var by := {}
		for r in rows:
			by[r.skill] = roundi(r.hit)
		out[k] = {"int": st.get_stat(&"int"), "spell_power": st.get_stat(&"spell_power"), "magic_damage": st.get_stat(&"magic_damage"),
			"max_mana": st.get_stat(&"max_mana"), "max_hp": st.get_stat(&"max_hp"), "best_hit": best(rows, "hit"), "hits": by}
		print("DECOMP %-30s INT %5d SP %6.1f MD %5.2f mana %6d hp %6d best %8d meteor %s" % [k, st.get_stat(&"int"), st.get_stat(&"spell_power"),
			st.get_stat(&"magic_damage"), st.get_stat(&"max_mana"), st.get_stat(&"max_hp"), best(rows, "hit"), by.get("meteor", "-")])
	out["target_hp"] = target.get_stat(&"max_hp")
	return out

# ---- calibration: realistic late-game heroes -------------------------------------------------------------------------

const PATHS := {&"knight": [&"royal_guard", &"dark_general"], &"mage": [&"arcanist", &"archmage"],
	&"ranger": [&"tracker", &"starstrider"], &"shadowblade": [&"nightstalker", &"phantom_reaper"]}

## The hero a committed player has at `level`: points along the class build, gear of that level at `rarity`, both
## advancements once allowed, skill points spent like a player (the damaging skill closest to its cap first, every
## third point into a passive or aura, all the way to rank 25) and talent points spent keystone and majors first.
static func endgame_hero(cid: StringName, level: int, rarity := BH.Rarity.MASTER) -> HeroData:
	var h: HeroData = BudgetTest.geared(cid, level, rarity)
	for t in PATHS[cid]:
		if ClassTranscendence.can_transcend(h, t) == "":
			ClassTranscendence.transcend(h, t)
	focus_skills(h, level)
	var tt := h.talent_tree
	var pts := h.progress.talent_points
	for pass_kind in ["keystone", "major", "minor"]:
		for n in tt.tree.nodes:
			var kind := String(n.get("kind", "minor"))
			if pass_kind != "minor" and kind != pass_kind:
				continue
			while pts > 0 and tt.can_rank_up(n.id, pts, level) == "":
				pts -= tt.rank_up(n.id, pts, level)
	h.progress.talent_points = pts
	h.stats_dirty.emit()
	return h

static func focus_skills(h: HeroData, lvl: int) -> void:
	var st := h.skill_tree
	var pts := h.progress.skill_points
	var i := 0
	while pts > 0:
		var want_support := i % 3 == 2
		var pick: Dictionary = {}
		var pick_rank := -1
		for pass_n in 2:
			for n in st.tree.nodes:
				if st.can_rank_up(n.id, pts, lvl) != "":
					continue
				var kind: String = n.get("kind", "skill")
				var s: SkillDef = DB.skill(n.get("skill", n.id)) if kind == "skill" else null
				var support := kind == "passive" or (s != null and s.is_aura())
				var damaging := kind == "skill" and s != null and not s.behavior in NO_DAMAGE
				if pass_n == 0 and not ((want_support and support) or (not want_support and damaging)):
					continue
				if pass_n == 1 and not (support or damaging or kind == "upgrade"):
					continue
				if st.rank(n.id) > pick_rank:
					pick_rank = st.rank(n.id)
					pick = n
			if not pick.is_empty():
				break
		if pick.is_empty():
			break
		pts -= st.rank_up(pick.id, pts, lvl)
		i += 1
	h.progress.skill_points = pts
	h._skills_changed()
	# the bar: the six damaging skills with the most damage per cast (a player's bar)
	var learned: Array = h.learned_skills().filter(func(sid): return DB.skill(sid) != null and not DB.skill(sid).behavior in NO_DAMAGE and not DB.skill(sid).is_aura())
	learned.sort_custom(func(a, b): return float(h.resolved_skill(a).get("damage_max", 0.0)) > float(h.resolved_skill(b).get("damage_max", 0.0)))
	for k in h.skill_bar.size():
		h.skill_bar[k] = learned[k] if k < learned.size() else &""

var _holder: Node3D

## Sustained damage per second of `h` against `n` monsters of `def` at monster level `ml` (topped up, so they never die):
## the real Player, the real pipeline, every player-only bonus. Measured over `seconds` of game time.
func measure_dps(h: HeroData, def: EnemyDef, ml: int, n: int, seconds := 12.0) -> float:
	Game.hero = h
	if _holder == null:
		# the town is loaded once; every measurement gets a fresh Player bound to its hero
		_holder = Node3D.new()
		_holder.name = "CalWorld"
		add_child(_holder)
		Game.world_parent = _holder
		Game.current_map = null
		player = Player.new()
		player.name = "Player"
		Game.player = player
		Game.load_map(&"sanctuary", &"start")
		player.bind(h)
	else:
		player = Player.new()
		player.name = "Player"
		Game.player = player
		Game.current_map.add_child(player)
		Game.place_player(&"start")
		player.bind(h)
	Engine.time_scale = 6.0
	await _frames(2)
	var dist := 7.0 if _ranged() else 1.9
	var center := player.global_position + player.forward() * (dist + (1.4 if n > 1 else 0.0))
	var d: EnemyDef = def.duplicate()
	d.can_be_elite = false
	d.attacks = []
	var es := []
	for i in n:
		var off := Vector3.ZERO if n == 1 else Vector3(cos(TAU * i / n), 0, sin(TAU * i / n)) * 1.4
		var e := Spawner.spawn_enemy(Game.current_map, d, ml, [], center + off, DataEnemies.DIFFICULTY[1])
		e.set_physics_process(false)
		es.append(e)
	await _frames(2)
	player.aim_override = center
	player.aim_point = Vector3(center.x, player.global_position.y, center.z)
	for sid in h.learned_skills():
		var s := DB.skill(sid)
		if s and s.is_aura() and s.aura_kind == &"offense" and h.active_aura == &"":
			player.toggle_aura(sid)
	var t := 0.0
	var dealt := 0.0
	var home := player.global_position
	while t < seconds:
		player.hp = player.max_hp()
		# dashes and leaps carry a melee bot past the dummy: between actions it steps back to its spot, as a player would
		if player.action == null and player.global_position.distance_to(home) > 1.5:
			player.global_position = home
			player.velocity = Vector3.ZERO
		player.aim_override = center
		for e in es:
			if is_instance_valid(e) and e.alive:
				dealt += e.max_hp() - e.hp
				e.hp = e.max_hp()
		var cast := false
		if player.action == null and player.channel_skill == &"":
			for sid in h.skill_bar:
				if sid == &"" or DB.skill(sid) == null or player.skill_block_reason(sid) != "":
					continue
				player._start_skill(sid)
				cast = true
				break
		# otherwise the attack is "held": the same request the Player's own input makes every frame
		if not cast and (player.action == null or player.action_kind == &"light"):
			player._request(&"light")
		await get_tree().physics_frame
		t += Engine.time_scale / Engine.physics_ticks_per_second
	for e in es:
		if is_instance_valid(e) and e.alive:
			dealt += e.max_hp() - e.hp
	Engine.time_scale = 1.0
	player.aim_override = Vector3.INF
	for e in get_tree().get_nodes_in_group(&"enemy"):
		e.free()
	for tm in get_tree().get_nodes_in_group(&"tempo"):
		tm.free()
	player.free()
	player = null
	Game.player = null
	await _frames(1)
	return dealt / seconds

func _calibrate() -> Dictionary:
	var levels: Array = String(args.get("levels", "60,80,100,120,141,200,300")).split(",")
	var classes: Array = String(args.get("classes", "knight,mage,ranger,shadowblade")).split(",")
	var rarity := int(args.get("rarity", str(BH.Rarity.MASTER)))
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	var mon := DB.enemy(&"glyphbound_warrior")
	var boss_def := DB.enemy(&"astrarch")
	var rows := []
	for ls in levels:
		var L := int(ls)
		var ml := monster_level(L)
		var normal := EnemyStats.build(mon, ml, diff, [])
		var elite := EnemyStats.build(mon, ml, diff, [], true)
		var champ_hp := elite.get_stat(&"max_hp") * 2.2
		for cs in classes:
			var cid := StringName(cs)
			var h := endgame_hero(cid, L, rarity)
			var st := h.compute_stats()
			var single := await measure_dps(h, mon, ml, 1)
			var aoe := await measure_dps(h, mon, ml, 5)
			var baseline := EnemyStats.build(boss_def, L, diff, [], false, true)
			var boss_hp := EnemyStats.boss_health(h, baseline)
			var hp := st.get_stat(&"max_hp")
			var es := EnemyStats.build(mon, ml, diff, [StatModifier.flat(&"threat_rank", CombatBudget.Rank.CHAMPION), StatModifier.more(&"outgoing_damage", 0.25)], true)
			var heavy := BudgetTest.blow(es, mon, BudgetTest.heaviest(mon), st, true)
			var bs := EnemyStats.build(boss_def, L, diff, [], false, true)
			var boss_blow := BudgetTest.blow(bs, boss_def, BudgetTest.heaviest(boss_def), st, true)
			var plain := BudgetTest.blow(normal, mon, 1.0, st)
			var row := {"level": L, "class": cs, "path": h.transcendence_path.map(func(x): return String(x)), "hp": hp,
				"single_dps": single, "aoe_dps": aoe, "normal_hp": normal.get_stat(&"max_hp"),
				"ttk_normal": normal.get_stat(&"max_hp") / maxf(1.0, single), "ttk_pack5": 5.0 * normal.get_stat(&"max_hp") / maxf(1.0, aoe),
				"ttk_elite": elite.get_stat(&"max_hp") / maxf(1.0, single), "ttk_champion": champ_hp / maxf(1.0, single),
				"boss_hp": boss_hp, "ttk_boss_uncapped": boss_hp / maxf(1.0, single),
				"plain_pct": 100.0 * plain / hp, "champion_heavy_pct": 100.0 * heavy / hp, "boss_heavy_pct": 100.0 * boss_blow / hp,
				"mana": st.get_stat(&"max_mana"), "bar": h.skill_bar.map(func(x): return String(x))}
			rows.append(row)
			print("CAL L%d %-11s hp %6d dps %9d aoe %9d | ttk normal %5.2fs pack5 %5.2fs elite %5.2fs champ %5.2fs boss %6.1fs | blow %.2f%% champ %.1f%% boss %.1f%%" % [
				L, cs, hp, single, aoe, row.ttk_normal, row.ttk_pack5, row.ttk_elite, row.ttk_champion, row.ttk_boss_uncapped,
				row.plain_pct, row.champion_heavy_pct, row.boss_heavy_pct])
	return {"rarity": rarity, "rows": rows}

# ---- live ------------------------------------------------------------------------------------------------------------

func _live(h: HeroData) -> Dictionary:
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	Game.hero = h
	Game.difficulty = h.difficulty
	var map_id := StringName(args.get("map", String(h.current_map)))
	var spawn := StringName(args.get("spawn", String(h.current_spawn) if map_id == h.current_map else "start"))
	await Game._begin_session(map_id, spawn)
	player = Game.player as Player
	player.input_enabled = true
	await _frames(20)
	var out := {"hero": h.hero_name, "level0": h.progress.level, "map": String(map_id), "max_hp": player.max_hp()}
	out["camps"] = await _fight_camps(float(args.get("seconds", "180")))
	out["boss"] = await _fight_boss(StringName(args.get("boss", "astrarch")), float(args.get("boss_seconds", "120")))
	out["level1"] = h.progress.level
	print("LIVE ", JSON.stringify(out))
	return out

func _fight_camps(seconds: float) -> Dictionary:
	var h := Game.hero
	var xp0 := h.progress.total_xp
	var lvl0 := h.progress.level
	var r := {"kills": 0, "elite_kills": 0, "ttk": [], "elite_ttk": [], "damage_taken": 0.0, "hits_taken": 0, "hp_min_frac": 1.0,
		"deaths": 0, "biggest_hit_taken_pct": 0.0, "biggest_hit_dealt": 0.0, "monster_levels": {}, "casts": 0, "potions": 0,
		"first_kill_s": -1.0}
	var first_hit := {}
	var t := [0.0]
	var on_dmg := func(target: Node, res: DamageResult, _pos: Vector3, attacker: Node) -> void:
		if target == player and not res.evaded:
			r.damage_taken += float(res.total)
			r.hits_taken += 1
			r.biggest_hit_taken_pct = maxf(r.biggest_hit_taken_pct, 100.0 * float(res.total) / player.max_hp())
		elif target is Enemy and attacker == player:
			r.biggest_hit_dealt = maxf(r.biggest_hit_dealt, float(res.total))
			_note_hit(res, target as Enemy)
			if not first_hit.has(target.get_instance_id()):
				first_hit[target.get_instance_id()] = t[0]
	var on_die := func(actor: Node, _k: Node) -> void:
		if actor == player:
			r.deaths += 1
		elif actor is Enemy:
			var e := actor as Enemy
			r.kills += 1
			if r.first_kill_s < 0.0:
				r.first_kill_s = t[0]
			r.monster_levels[str(e.level)] = int(r.monster_levels.get(str(e.level), 0)) + 1
			var since: float = t[0] - float(first_hit.get(e.get_instance_id(), t[0]))
			if e.is_elite or e.is_miniboss():
				r.elite_kills += 1
				r.elite_ttk.append(snappedf(since, 0.01))
			else:
				r.ttk.append(snappedf(since, 0.01))
	Events.damage_dealt.connect(on_dmg)
	Events.actor_died.connect(on_die)
	var dt := 1.0 / Engine.physics_ticks_per_second
	var active := 0.0
	while t[0] < seconds:
		await get_tree().physics_frame
		t[0] += dt
		_release_expired(t[0])
		if not player.alive:
			await _frames(30)
			player.respawn()
			continue
		r.hp_min_frac = minf(r.hp_min_frac, player.hp / player.max_hp())
		var target := _nearest_enemy(160.0)
		if target == null:
			break
		active += dt
		r.casts += _engage(target, t[0])
		if player.hp < player.max_hp() * 0.4 and player.potion_cd <= 0.0 and player.use_potion(&"heal"):
			r.potions += 1
	_stop_move()
	Events.damage_dealt.disconnect(on_dmg)
	Events.actor_died.disconnect(on_die)
	r["seconds"] = snappedf(t[0], 0.1)
	r["xp"] = h.progress.total_xp - xp0
	r["levels_gained"] = h.progress.level - lvl0
	r["xp_per_min"] = float(r.xp) / maxf(0.1, t[0] / 60.0)
	r["minutes_per_level"] = float(XpCurve.xp_to_next(h.progress.level)) / maxf(1.0, r.xp_per_min)
	r["kills_per_min"] = float(r.kills) / maxf(0.1, t[0] / 60.0)
	r["damage_taken_per_min_pct"] = 100.0 * r.damage_taken / player.max_hp() / maxf(0.1, t[0] / 60.0)
	r["median_ttk"] = _median(r.ttk)
	r["median_elite_ttk"] = _median(r.elite_ttk)
	r["top_hits"] = _top_hits.duplicate(true)
	_top_hits.clear()
	r["left_alive"] = get_tree().get_nodes_in_group(&"enemy").filter(func(e): return e is Enemy and e.alive).size()
	print("CAMPS ", JSON.stringify(r))
	return r

func _fight_boss(id: StringName, seconds: float) -> Dictionary:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.alive and e.global_position.distance_to(player.global_position) < 40.0:
			e.queue_free()
	await _frames(5)
	player.hp = player.max_hp()
	player.mana = player.max_mana()
	player.cooldowns.clear()
	var def := DB.enemy(id)
	var at := player.global_position + player.forward() * 9.0
	var boss := Spawner.spawn_enemy(Game.current_map, def, Game.hero.progress.level, [], at, Game.current_map.get_node("Spawner").difficulty if Game.current_map.has_node("Spawner") else DataEnemies.DIFFICULTY[1])
	await _frames(3)
	var r := {"id": String(id), "level": boss.level, "max_hp": boss.max_hp(), "hit_limit": boss.stats.get_stat(&"boss_hit_limit"),
		"damage_taken": 0.0, "hp_min_frac": 1.0, "deaths": 0, "hits": 0, "capped_hits": 0, "biggest_hit_taken_pct": 0.0}
	var on_dmg := func(target: Node, res: DamageResult, _pos: Vector3, attacker: Node) -> void:
		if target == player:
			var src := "%s:%s" % [attacker.name if attacker else "?", String(res.skill) if res.skill != &"" else res.skill_name]
			var row: Dictionary = r.get_or_add("sources", {}).get_or_add(src, {"n": 0, "evaded": 0, "sum": 0.0, "max_pct": 0.0})
			row.n += 1
			if res.evaded:
				row.evaded += 1
			else:
				row.sum += float(res.total)
				row.max_pct = maxf(float(row.max_pct), 100.0 * float(res.total) / player.max_hp())
		if target == player and not res.evaded:
			r.damage_taken += float(res.total)
			r.biggest_hit_taken_pct = maxf(r.biggest_hit_taken_pct, 100.0 * float(res.total) / player.max_hp())
		elif target == boss and attacker == player:
			r.hits += 1
			if float(res.total) >= r.hit_limit * 0.98:
				r.capped_hits += 1
	var on_die := func(actor: Node, _k: Node) -> void:
		if actor == player:
			r.deaths += 1
	Events.damage_dealt.connect(on_dmg)
	Events.actor_died.connect(on_die)
	var t := 0.0
	var dt := 1.0 / Engine.physics_ticks_per_second
	while t < seconds and is_instance_valid(boss) and boss.alive:
		await get_tree().physics_frame
		t += dt
		_release_expired(t)
		if not player.alive:
			await _frames(30)
			player.respawn()
			continue
		r.hp_min_frac = minf(r.hp_min_frac, player.hp / player.max_hp())
		if boss.alive:
			var sn := String(boss.brain.state_name())
			r["states"] = r.get("states", {})
			r.states[sn] = float(r.states.get(sn, 0.0)) + dt
			for sid in [&"staggered", &"frozen", &"stunned", &"chilled", &"stagger_window", &"knocked"]:
				if boss.status.has(sid):
					r["status_s"] = r.get("status_s", {})
					r.status_s[String(sid)] = float(r.status_s.get(String(sid), 0.0)) + dt
			if boss.status.is_disabled():
				r["disabled_s"] = float(r.get("disabled_s", 0.0)) + dt
		_engage(boss, t)
		if player.hp < player.max_hp() * 0.4 and player.potion_cd <= 0.0:
			player.use_potion(&"heal")
	_stop_move()
	Events.damage_dealt.disconnect(on_dmg)
	Events.actor_died.disconnect(on_die)
	r["killed"] = not (is_instance_valid(boss) and boss.alive)
	r["seconds"] = snappedf(t, 0.01)
	r["boss_hp_left_frac"] = boss.hp / boss.max_hp() if is_instance_valid(boss) else 0.0
	print("BOSS ", JSON.stringify(r))
	return r

## Step to casting range and cast: the bar's skills in order of longest cooldown first, otherwise the basic attack.
## Returns 1 when a skill was cast this frame.
func _engage(target: Enemy, t: float) -> int:
	var d := player.global_position.distance_to(target.global_position)
	player.aim_override = target.global_position + Vector3.UP * 0.8
	player.aim_point = target.global_position
	var reach := 11.0 if _ranged() else 2.0
	if d > reach or not _sees(target):
		_move_toward(target.global_position, t)
		return 0
	_stop_move()
	if player.action != null or player.channel_skill != &"":
		return 0
	var order: Array = Game.hero.skill_bar.filter(func(sid): return sid != &"" and DB.skill(sid) != null and not DB.skill(sid).behavior in NO_DAMAGE)
	order.sort_custom(func(a, b): return DB.skill(a).cooldown > DB.skill(b).cooldown)
	for sid in order:
		if player.skill_block_reason(sid) == "":
			_press.erase(&"primary")
			Input.action_release(&"primary")
			player._start_skill(sid)
			return 1
	_tap(&"primary", t, 0.12)
	return 0

var _top_hits := {}

## The biggest hit of each skill (with the pipeline's breakdown) and how often each skill landed.
func _note_hit(res: DamageResult, target: Enemy) -> void:
	var k := String(res.skill) if res.skill != &"" else ("basic" if res.skill_name == "" else res.skill_name)
	var row: Dictionary = _top_hits.get_or_add(k, {"n": 0, "sum": 0.0, "max": 0.0, "target_hp": 0.0, "steps": ""})
	row.n += 1
	row.sum += float(res.total)
	if float(res.total) > float(row.max):
		row.max = float(res.total)
		row.target_hp = target.max_hp()
		row.steps = res.breakdown()

func _sees(target: Node3D) -> bool:
	var space := player.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(player.global_position + Vector3.UP * 1.2, target.global_position + Vector3.UP * 1.0, BH.LAYER_WORLD)
	return space.intersect_ray(q).is_empty()

func _ranged() -> bool:
	var lo := Game.hero.equipment.loadout()
	return Game.hero.cls.id == &"mage" or (lo.main_type != null and lo.main_type.ranged)

func _nearest_enemy(max_d: float) -> Enemy:
	var best_e: Enemy = null
	var bd := max_d * max_d
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Enemy and e.alive and not e.net_replica:
			var dd: float = e.global_position.distance_squared_to(player.global_position)
			if dd < bd:
				bd = dd
				best_e = e
	return best_e

func _move_toward(p: Vector3, _t: float) -> void:
	var nm := player.get_world_3d().navigation_map
	var path := NavigationServer3D.map_get_path(nm, player.global_position, p, true)
	var goal := p
	for q in path:
		if Vector2(q.x - player.global_position.x, q.z - player.global_position.z).length() > 0.8:
			goal = q
			break
	var dir := goal - player.global_position
	dir.y = 0.0
	if dir.length() < 0.1:
		_stop_move()
		return
	dir = dir.normalized()
	var cam := player.camera.global_basis
	var right := Vector3(cam.x.x, 0, cam.x.z).normalized()
	var fwd := Vector3(-cam.z.x, 0, -cam.z.z).normalized()
	var x := dir.dot(right)
	var y := dir.dot(fwd)
	_hold(&"move_right", x > 0.3)
	_hold(&"move_left", x < -0.3)
	_hold(&"move_up", y > 0.3)
	_hold(&"move_down", y < -0.3)

func _stop_move() -> void:
	for a in [&"move_right", &"move_left", &"move_up", &"move_down"]:
		if _press.has(a):
			Input.action_release(a)
			_press.erase(a)

func _hold(a: StringName, on: bool) -> void:
	if on and not _press.has(a):
		Input.action_press(a)
		_press[a] = INF
	elif not on and _press.has(a):
		Input.action_release(a)
		_press.erase(a)

func _tap(a: StringName, t: float, dur: float) -> void:
	if _press.has(a):
		return
	Input.action_press(a)
	_press[a] = t + dur

func _release_expired(t: float) -> void:
	for a in _press.keys():
		if _press[a] <= t:
			Input.action_release(a)
			_press.erase(a)

func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

static func _median(a: Array) -> float:
	if a.is_empty():
		return -1.0
	var s := a.duplicate()
	s.sort()
	return float(s[s.size() / 2])
