class_name GuildJobs
## Miniquests of the Guild House (bh-016): each guild posts a board of odd jobs that pay gold. Pure rules over
## HeroData.guild_jobs (no nodes): the Guild House window, the dialogue services, the event hooks and the tests all
## call these. State: {"board": {guild: [job]}, "active": [job], "done": int, "earned": int, "serial": int}.
## A job: {id, tpl, guild, kind, title, text, goal, progress, reward, map}.

const BOARD_SIZE := 4
const ACTIVE_MAX := 3
## Gold paid grows with hero level the way monster gold does, and with the hero's guild tier.
const LEVEL_GROWTH := 0.12
const TIER_BONUS := 0.05

static func state(hero: HeroData) -> Dictionary:
	var s: Dictionary = hero.guild_jobs
	if not s.has("board"):
		s["board"] = {}
	if not s.has("active"):
		s["active"] = []
	for k in ["done", "earned", "serial"]:
		if not s.has(k):
			s[k] = 0
	return s

static func active(hero: HeroData) -> Array:
	return state(hero).active

static func board(hero: HeroData, gid: StringName) -> Array:
	var b: Dictionary = state(hero).board
	if not b.has(String(gid)):
		b[String(gid)] = []
	return b[String(gid)]

## Gold before the tier bonus for `goal` units of a template at a hero level.
static func base_reward(tpl: Dictionary, goal: int, level: int) -> int:
	var raw := float(tpl.unit) * float(goal) * (1.0 + LEVEL_GROWTH * float(maxi(level, 1) - 1))
	return maxi(5, int(round(raw / 5.0)) * 5)

static func tier_multiplier(hero: HeroData) -> float:
	return 1.0 + TIER_BONUS * float(hero.tier)

## What the job actually pays this hero today.
static func payout(hero: HeroData, job: Dictionary) -> int:
	return int(round(float(job.reward) * tier_multiplier(hero)))

static func _map_name(id: String) -> String:
	var md := DB.map_def(StringName(id)) if id != "" else null
	return md.display_name if md else id.capitalize()

static func make_job(hero: HeroData, tpl: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var s := state(hero)
	s.serial = int(s.serial) + 1
	var goal := rng.randi_range(int(tpl.goal.x), int(tpl.goal.y))
	var text := String(tpl.text).replace("{n}", str(goal)).replace("{map}", _map_name(String(tpl.get("map", ""))))
	return {"id": int(s.serial), "tpl": String(tpl.id), "guild": String(tpl.guild), "kind": String(tpl.kind), "title": String(tpl.title),
		"text": text, "goal": goal, "progress": 0, "reward": base_reward(tpl, goal, hero.progress.level), "map": String(tpl.get("map", ""))}

static func _eligible(hero: HeroData, gid: StringName) -> Array:
	var used := {}
	for j in board(hero, gid):
		used[j.tpl] = true
	for j in active(hero):
		used[j.tpl] = true
	var lvl := hero.progress.level
	return DataGuildJobs.for_guild(gid).filter(func(t): return not used.has(String(t.id)) and lvl >= int(t.lvl.x) and lvl <= int(t.lvl.y))

## Drops postings the hero has outgrown and pins the board back up to BOARD_SIZE. Returns the board.
static func refresh_board(hero: HeroData, gid: StringName) -> Array:
	if not DataGuilds.GUILDS.has(gid):
		return []
	var b := board(hero, gid)
	var lvl := hero.progress.level
	for i in range(b.size() - 1, -1, -1):
		var t := DataGuildJobs.template(String(b[i].tpl))
		if t.is_empty() or lvl < int(t.lvl.x) or lvl > int(t.lvl.y):
			b.remove_at(i)
	var rng := RandomNumberGenerator.new()
	while b.size() < BOARD_SIZE:
		var pool := _eligible(hero, gid)
		if pool.is_empty():
			break
		rng.seed = hash([hero.hero_name, int(state(hero).serial), String(gid)])
		b.append(make_job(hero, pool[rng.randi() % pool.size()], rng))
	return b

## "" when the hero may take a posting from `gid`'s board now, otherwise why not.
static func accept_error(hero: HeroData, gid: StringName, job_id: int) -> String:
	if hero.guild != gid:
		return "Only registered %s heroes may take these jobs" % DataGuilds.guild(gid).get("short", "guild")
	if active(hero).size() >= ACTIVE_MAX:
		return "You already carry %d jobs" % ACTIVE_MAX
	for j in board(hero, gid):
		if int(j.id) == job_id:
			return ""
	return "That posting is gone"

static func accept(hero: HeroData, gid: StringName, job_id: int) -> String:
	var err := accept_error(hero, gid, job_id)
	if err != "":
		return err
	var b := board(hero, gid)
	for i in b.size():
		if int(b[i].id) == job_id:
			active(hero).append(b[i])
			b.remove_at(i)
			break
	refresh_board(hero, gid)
	Events.guild_jobs_changed.emit()
	return ""

static func find_active(hero: HeroData, job_id: int) -> Dictionary:
	for j in active(hero):
		if int(j.id) == job_id:
			return j
	return {}

static func is_done(job: Dictionary) -> bool:
	return int(job.progress) >= int(job.goal)

static func abandon(hero: HeroData, job_id: int) -> String:
	var a := active(hero)
	for i in a.size():
		if int(a[i].id) == job_id:
			a.remove_at(i)
			Events.guild_jobs_changed.emit()
			return ""
	return "You do not carry that job"

## Hand in a finished job for its gold. Returns "" or why not (nothing changes).
static func claim(hero: HeroData, job_id: int) -> String:
	var j := find_active(hero, job_id)
	if j.is_empty():
		return "You do not carry that job"
	if not is_done(j):
		return "The job is not finished (%d / %d)" % [j.progress, j.goal]
	var gold := payout(hero, j)
	hero.inventory.gold += gold
	hero.inventory.changed.emit()
	var s := state(hero)
	s.done = int(s.done) + 1
	hero.check_promotions()
	s.earned = int(s.earned) + gold
	abandon(hero, job_id)
	Events.gold_picked.emit(gold)
	Events.notify.emit("%s paid: +%d gold" % [j.title, gold], &"loot")
	refresh_board(hero, StringName(j.guild))
	Events.guild_jobs_changed.emit()
	return ""

# ---- progress hooks ----------------------------------------------------------------------------------------------

## Add `n` to every carried job of `kind` (a `map` restriction on the job must match `map_id`). Returns jobs that just finished.
static func progress(hero: HeroData, kind: String, n := 1, map_id := "") -> Array:
	var finished := []
	if hero == null:
		return finished
	for j in active(hero):
		if String(j.kind) != kind or is_done(j):
			continue
		if (kind == "kill_map" or kind == "visit") and String(j.map) != map_id:
			continue
		j.progress = mini(int(j.goal), int(j.progress) + n)
		if is_done(j):
			finished.append(j)
			Events.notify.emit("Job done: %s. Hand it in at the Guild House." % j.title, &"info")
	if not active(hero).is_empty():
		Events.guild_jobs_changed.emit()
	return finished

## A monster died on this map: kills count for "any", "map" and (elites) "elite" jobs.
static func on_kill(hero: HeroData, is_elite: bool, map_id: String) -> void:
	if hero == null or active(hero).is_empty():
		return
	progress(hero, "kill_any", 1)
	progress(hero, "kill_map", 1, map_id)
	if is_elite:
		progress(hero, "kill_elite", 1)

## Wire the world events to the active hero's jobs (called once by Game).
static func connect_events() -> void:
	Events.herb_gathered.connect(func(_b: StringName, c: int) -> void: progress(Game.hero, "herb", c))
	Events.weapon_upgraded.connect(func(_i: ItemInstance, _k: StringName) -> void: progress(Game.hero, "craft", 1))
	Events.item_crafted.connect(func(_r: StringName, _items: Array) -> void: progress(Game.hero, "craft", 1))
	Events.camp_cleared.connect(func(_m: StringName, _z: String, _l: int, _t: int) -> void: progress(Game.hero, "camp", 1))
	Events.stage_cleared.connect(func(_m: StringName) -> void: progress(Game.hero, "stage", 1))
	Events.miniboss_defeated.connect(func(_id: StringName) -> void: progress(Game.hero, "miniboss", 1))
	Events.map_loaded.connect(func(id: StringName) -> void: progress(Game.hero, "visit", 1, String(id)))

# ---- saving ----------------------------------------------------------------------------------------------------

static func job_to_plain(j: Dictionary) -> Dictionary:
	return {"id": int(j.id), "tpl": String(j.tpl), "guild": String(j.guild), "kind": String(j.kind), "title": String(j.title),
		"text": String(j.text), "goal": int(j.goal), "progress": int(j.progress), "reward": int(j.reward), "map": String(j.get("map", ""))}

static func to_dict(hero: HeroData) -> Dictionary:
	var s := state(hero)
	var b := {}
	for g in s.board:
		b[String(g)] = (s.board[g] as Array).map(func(j): return job_to_plain(j))
	return {"board": b, "active": (s.active as Array).map(func(j): return job_to_plain(j)), "done": int(s.done), "earned": int(s.earned), "serial": int(s.serial)}

## Rebuild from a save; malformed or unknown jobs are dropped (old saves have none).
static func from_dict(d) -> Dictionary:
	var out := {"board": {}, "active": [], "done": 0, "earned": 0, "serial": 0}
	if not (d is Dictionary):
		return out
	out.done = maxi(0, int(d.get("done", 0)))
	out.earned = maxi(0, int(d.get("earned", 0)))
	out.serial = maxi(0, int(d.get("serial", 0)))
	var ok_job := func(j) -> bool:
		return j is Dictionary and j.has("id") and j.has("goal") and not DataGuildJobs.template(String(j.get("tpl", ""))).is_empty()
	var ab = d.get("board", {})
	if ab is Dictionary:
		for g in ab:
			if DataGuilds.GUILDS.has(StringName(g)) and ab[g] is Array:
				out.board[String(g)] = (ab[g] as Array).filter(ok_job).map(func(j): return job_to_plain(j))
	var act = d.get("active", [])
	if act is Array:
		out.active = (act as Array).filter(ok_job).map(func(j): return job_to_plain(j))
	return out
