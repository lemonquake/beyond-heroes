class_name OwnGuild
## bh-027: the guild a hero founds and leads. Pure rules over HeroData.own_guild (no nodes): the Guild window, the Guild
## House steward, the multiplayer invites and the tests all call these.
##
##   {name, motto, info (what the founder writes about the guild), style (GuildBannerArt), founded, renown, level,
##    slots, members: [member], passives: {id: rank}, summon: {rank, ready_at, until, called: [member ids]},
##    next_recruit, serial, treasury}
##   member: {id, kind ("npc" | "player"), name, cls, level, trait, joined, loyalty, renown, look}
##
## Adventurers of every class apply from time to time until the guild is full, at levels a little below the
## Guildmaster's (level 20 -> 13..20), and they train as the Guildmaster grows. They earn the guild renown (its level)
## and pay tithes into its treasury. Fellow players join by invitation (Net) and take a slot like anyone else.
## Everything runs on play time, so it waits while the game is closed.

const TICK := 5.0
const INFO_MAX := 400
const MOTTO_MAX := 80
const TREASURY_BASE := 2000.0
const TREASURY_PER_LEVEL := 500.0
## Per member per minute of play.
const TITHE_PER_LEVEL := 0.35
const RENOWN_PER_MEMBER := 0.3
const RENOWN_PER_LEVEL := 0.02
const LOYALTY_PER_MINUTE := 0.5
const TRAIN_EVERY := 300.0
const TRAIN_CHANCE := 0.3

static var _acc := 0.0
static var _connected := false

static func has(hero: HeroData) -> bool:
	return hero != null and not hero.own_guild.is_empty()

## The hero leads the guild they founded (and has not joined another since).
static func is_master(hero: HeroData) -> bool:
	return has(hero) and hero.guild == GuildRegistry.OWN

static func members(hero: HeroData) -> Array:
	return hero.own_guild.get("members", []) if has(hero) else []

static func npc_members(hero: HeroData) -> Array:
	return members(hero).filter(func(m): return String(m.kind) == "npc")

static func slots(hero: HeroData) -> int:
	return int(hero.own_guild.get("slots", DataGuildPassives.BASE_SLOTS)) if has(hero) else 0

static func free_slots(hero: HeroData) -> int:
	return maxi(0, slots(hero) - members(hero).size())

static func level(hero: HeroData) -> int:
	return int(hero.own_guild.get("level", 1)) if has(hero) else 0

static func key(hero: HeroData) -> String:
	return "%s/%s" % [GuildRules.clean_alias(hero.hero_name), String(hero.own_guild.get("name", ""))] if has(hero) else ""

static func rank(hero: HeroData, pid: StringName) -> int:
	return int((hero.own_guild.get("passives", {}) as Dictionary).get(String(pid), 0)) if has(hero) else 0

# ---- founding --------------------------------------------------------------------------------------------------

static func clean_text(text: String, max_len: int) -> String:
	var out := ""
	for i in text.length():
		var c := text.unicode_at(i)
		if (c < 32 and c != 10) or c == 127 or c == 91 or c == 93:
			continue
		out += String.chr(c)
	out = out.strip_edges()
	while out.contains("\n\n\n"):
		out = out.replace("\n\n\n", "\n\n")
	return out.left(max_len)

## "" when the hero may found a guild called `gname` now, else why not.
static func found_error(hero: HeroData, gname: String) -> String:
	if hero == null:
		return "There is no hero"
	if has(hero):
		return "You already lead %s" % String(hero.own_guild.name)
	var clean := GuildRules.clean_alias(gname)
	if clean.length() < 3:
		return "Give your guild a name (at least 3 letters)"
	for id in GuildRegistry.all_ids(hero):
		var g := GuildRegistry.info(hero, id)
		if String(g.get("name", "")).to_lower() == clean.to_lower():
			return "A guild with that name already exists"
	if hero.inventory.gold < DataGuildPassives.FOUND_FEE:
		return "The charter costs %d gold" % DataGuildPassives.FOUND_FEE
	return ""

## Found the guild: the hero leaves any guild they were in (their tier stays theirs) and becomes its Guildmaster.
static func found(hero: HeroData, gname: String, motto: String, info: String, style: Dictionary) -> String:
	var err := found_error(hero, gname)
	if err != "":
		return err
	hero.inventory.gold -= DataGuildPassives.FOUND_FEE
	hero.inventory.changed.emit()
	var nm := GuildRules.clean_alias(gname)
	hero.own_guild = {"name": nm, "motto": clean_text(motto, MOTTO_MAX), "info": clean_text(info, INFO_MAX),
		"style": GuildBannerArt.sanitize(style), "founded": hero.play_time, "renown": 0.0, "level": 1,
		"slots": DataGuildPassives.BASE_SLOTS, "members": [], "passives": {},
		"summon": {"rank": 1, "ready_at": 0.0, "until": 0.0, "called": []},
		"next_recruit": hero.play_time + DataGuildPassives.RECRUIT_FIRST, "serial": 0, "treasury": 0.0}
	var first := hero.guild == &""
	hero.guild = GuildRegistry.OWN
	hero.remote_guild = {}
	if hero.tier < 1:
		hero.set_tier(1)
	else:
		hero.stats_dirty.emit()
	Events.guild_joined.emit(GuildRegistry.OWN, first)
	Events.guild_changed.emit()
	hero.check_promotions()
	return ""

## Edit the founder's words: motto, guild info and banner style ("" on success).
static func set_details(hero: HeroData, motto: String, info: String, style: Variant = null) -> String:
	if not has(hero):
		return "Found a guild first"
	hero.own_guild["motto"] = clean_text(motto, MOTTO_MAX)
	hero.own_guild["info"] = clean_text(info, INFO_MAX)
	if style is Dictionary:
		hero.own_guild["style"] = GuildBannerArt.sanitize(style)
	Events.guild_customised.emit()
	Events.guild_changed.emit()
	return ""

static func rename(hero: HeroData, gname: String) -> String:
	if not has(hero):
		return "Found a guild first"
	var clean := GuildRules.clean_alias(gname)
	if clean.length() < 3:
		return "Give your guild a name (at least 3 letters)"
	hero.own_guild["name"] = clean
	Events.guild_customised.emit()
	Events.guild_changed.emit()
	return ""

## Disband: every adventurer goes their own way; the hero keeps their tier and whatever the treasury held.
static func disband(hero: HeroData) -> void:
	if not has(hero):
		return
	var t := int(hero.own_guild.get("treasury", 0.0))
	hero.inventory.gold += t
	hero.inventory.changed.emit()
	GuildSummons.dismiss(hero)
	hero.own_guild = {}
	if hero.guild == GuildRegistry.OWN:
		hero.guild = &""
	hero.stats_dirty.emit()
	Events.guild_changed.emit()
	Events.guild_customised.emit()

# ---- slots, levels, passives -----------------------------------------------------------------------------------

## [slots after it, gold], or [] at the top.
static func next_slot_upgrade(hero: HeroData) -> Array:
	var now := slots(hero)
	for u in DataGuildPassives.SLOT_UPGRADES:
		if int(u[0]) > now:
			return u
	return []

static func buy_slots(hero: HeroData) -> String:
	if not is_master(hero):
		return "Only the Guildmaster can expand the guild"
	var u := next_slot_upgrade(hero)
	if u.is_empty():
		return "The guild hall holds no more than %d members" % DataGuildPassives.MAX_SLOTS
	if hero.inventory.gold < int(u[1]):
		return "Expanding to %d members costs %d gold" % [u[0], u[1]]
	hero.inventory.gold -= int(u[1])
	hero.inventory.changed.emit()
	hero.own_guild["slots"] = int(u[0])
	Events.guild_changed.emit()
	return ""

## Renown toward the next level: [have, need] (need 0 at the cap).
static func level_progress(hero: HeroData) -> Array:
	if not has(hero):
		return [0.0, 0.0]
	var lvl := level(hero)
	if lvl >= DataGuildPassives.LEVEL_CAP:
		return [0.0, 0.0]
	var spent := 0.0
	for l in range(1, lvl):
		spent += DataGuildPassives.renown_for_level(l)
	return [float(hero.own_guild.renown) - spent, DataGuildPassives.renown_for_level(lvl)]

static func add_renown(hero: HeroData, amount: float) -> void:
	if not has(hero) or amount <= 0.0:
		return
	var og := hero.own_guild
	og["renown"] = float(og.renown) + amount
	var grew := false
	while int(og.level) < DataGuildPassives.LEVEL_CAP:
		var p := level_progress(hero)
		if float(p[0]) < float(p[1]):
			break
		og["level"] = int(og.level) + 1
		grew = true
	if grew:
		Events.notify.emit("%s reached guild level %d!" % [og.name, og.level], &"discovery")
		Audio.play_ui(&"level_up", -4.0)
		Events.guild_changed.emit()

static func upgrade_error(hero: HeroData, pid: StringName) -> String:
	if not is_master(hero):
		return "Only the Guildmaster can train the guild"
	var p := DataGuildPassives.passive(pid)
	if p.is_empty():
		return "Unknown passive"
	var r := rank(hero, pid) + 1
	if r > int(p.max):
		return "%s is at its highest rank" % p.name
	var need := DataGuildPassives.level_req(pid, r)
	if level(hero) < need:
		return "Rank %d needs guild level %d" % [r, need]
	var cost := DataGuildPassives.cost(pid, r)
	if hero.inventory.gold < cost:
		return "Rank %d costs %d gold" % [r, cost]
	return ""

static func upgrade(hero: HeroData, pid: StringName) -> String:
	var err := upgrade_error(hero, pid)
	if err != "":
		return err
	var r := rank(hero, pid) + 1
	hero.inventory.gold -= DataGuildPassives.cost(pid, r)
	hero.inventory.changed.emit()
	(hero.own_guild.passives as Dictionary)[String(pid)] = r
	hero.stats_dirty.emit()
	Events.guild_changed.emit()
	return ""

## Guild passives as stat modifiers (every member, all the time) for a set of ranks {id: rank}.
static func passive_modifiers(ranks: Dictionary, source: String) -> Array:
	var out := []
	for k in ranks:
		var p := DataGuildPassives.passive(StringName(k))
		if p.is_empty() or String(p.kind) != "guild" or int(ranks[k]) <= 0:
			continue
		var v := float(p.per) * float(ranks[k])
		out.append(StatModifier.flat(p.stat, v, source) if String(p.op) == "flat" else StatModifier.inc(p.stat, v, source))
	return out

## Guild War passives for `comrades` guild members fighting beside the hero.
static func war_modifiers(ranks: Dictionary, comrades: int, source := "Guild War") -> Array:
	var out := []
	var n := clampi(comrades, 0, DataGuildPassives.WAR_CAP)
	if n <= 0:
		return out
	for k in ranks:
		var p := DataGuildPassives.passive(StringName(k))
		if p.is_empty() or String(p.kind) != "war" or int(ranks[k]) <= 0:
			continue
		var v := float(p.per) * float(ranks[k]) * float(n)
		out.append(StatModifier.flat(p.stat, v, source) if String(p.op) == "flat" else StatModifier.inc(p.stat, v, source))
	return out

# ---- adventurers -----------------------------------------------------------------------------------------------

## The levels a recruit may arrive at for this hero: [min, max].
static func recruit_range(hero: HeroData) -> Vector2i:
	var l := hero.progress.level
	var narrow := 1.0 - 0.25 * float(rank(hero, &"veteran_training"))
	var spread := int(ceil(float(l) * DataGuildPassives.RECRUIT_SPREAD * narrow))
	return Vector2i(maxi(1, l - spread), l)

static func make_member(hero: HeroData, rng: RandomNumberGenerator) -> Dictionary:
	var og := hero.own_guild
	og["serial"] = int(og.get("serial", 0)) + 1
	var taken: Array = [hero.hero_name]
	for m in members(hero):
		taken.append(String(m.name))
	var nm := NameForge.person(rng, taken)
	if rng.randf() < 0.4:
		nm = "%s of %s" % [nm, GuildNames.place(rng)]
	var cls: StringName = DataGuildPassives.CLASSES[rng.randi_range(0, DataGuildPassives.CLASSES.size() - 1)]
	var traits := DataGuildPassives.TRAITS.keys()
	traits.sort()
	var tr: StringName = traits[rng.randi_range(0, traits.size() - 1)]
	var r := recruit_range(hero)
	var lvl := rng.randi_range(r.x, r.y)
	if tr == &"veteran":
		lvl = mini(lvl + 1, hero.progress.level)
	return {"id": int(og.serial), "kind": "npc", "name": nm, "cls": String(cls), "level": lvl, "trait": String(tr),
		"joined": hero.play_time, "loyalty": float(rng.randi_range(5, 30)), "renown": 0.0, "look": rng.randi()}

## Take on the next applicant now (the recruitment timer calls this; so does the dev panel). Returns the member or {}.
static func recruit(hero: HeroData, rng: RandomNumberGenerator = null) -> Dictionary:
	if not has(hero) or free_slots(hero) <= 0:
		return {}
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.seed = hash("%s/recruit/%d/%d" % [hero.hero_name, int(hero.own_guild.get("serial", 0)), int(hero.play_time)])
	var m := make_member(hero, rng)
	(hero.own_guild.members as Array).append(m)
	var cd := DB.class_def(StringName(m.cls))
	Events.notify.emit("%s, a level %d %s (%s), has joined %s!" % [m.name, m.level, cd.display_name if cd else String(m.cls),
		DataGuildPassives.TRAITS[StringName(m.trait)].name, hero.own_guild.name], &"discovery")
	Events.guild_changed.emit()
	return m

## Seconds until the next applicant arrives (INF when the guild is full).
static func recruit_in(hero: HeroData) -> float:
	if not has(hero) or free_slots(hero) <= 0:
		return INF
	return maxf(0.0, float(hero.own_guild.get("next_recruit", 0.0)) - hero.play_time)

static func _schedule_recruit(hero: HeroData, rng: RandomNumberGenerator) -> void:
	var faster := 1.0 - float(DataGuildPassives.passive(&"open_doors").per) * float(rank(hero, &"open_doors"))
	# a well-known hero and a busy hall draw applicants sooner
	var fame := 1.0 - 0.03 * float(hero.tier) - 0.01 * float(level(hero))
	hero.own_guild["next_recruit"] = hero.play_time + DataGuildPassives.RECRUIT_BASE * faster * clampf(fame, 0.5, 1.0) * rng.randf_range(0.7, 1.3)

static func find_member(hero: HeroData, member_id: int) -> Dictionary:
	for m in members(hero):
		if int(m.id) == member_id:
			return m
	return {}

## Send a member away. A fellow player is told over the network (Net.guild_kick).
static func kick(hero: HeroData, member_id: int) -> String:
	if not is_master(hero):
		return "Only the Guildmaster can dismiss members"
	var list: Array = hero.own_guild.members
	for i in list.size():
		if int(list[i].id) == member_id:
			var m: Dictionary = list[i]
			list.remove_at(i)
			(hero.own_guild.summon.called as Array).erase(member_id)
			GuildSummons.dismiss_member(member_id)
			if String(m.kind) == "player":
				Net.guild_kick_player(String(m.name))
			Events.notify.emit("%s has left %s." % [m.name, hero.own_guild.name], &"info")
			if free_slots(hero) > 0 and float(hero.own_guild.get("next_recruit", 0.0)) < hero.play_time:
				var rng := RandomNumberGenerator.new()
				rng.seed = hash([hero.hero_name, member_id])
				_schedule_recruit(hero, rng)
			Events.guild_changed.emit()
			return ""
	return "No such member"

## A fellow player accepted an invitation: they take a slot like any adventurer.
static func add_player_member(hero: HeroData, pname: String, cls: String, lvl: int) -> String:
	if not is_master(hero):
		return "You do not lead a guild"
	var clean := GuildRules.clean_alias(pname)
	for m in members(hero):
		if String(m.kind) == "player" and String(m.name) == clean:
			m["level"] = lvl
			m["cls"] = cls
			return ""
	if free_slots(hero) <= 0:
		return "%s is full" % hero.own_guild.name
	var og := hero.own_guild
	og["serial"] = int(og.get("serial", 0)) + 1
	(og.members as Array).append({"id": int(og.serial), "kind": "player", "name": clean, "cls": cls if DB.class_def(StringName(cls)) else "knight",
		"level": clampi(lvl, 1, BH.LEVEL_CAP), "trait": "loyal", "joined": hero.play_time, "loyalty": 100.0, "renown": 0.0, "look": 0})
	Events.guild_changed.emit()
	return ""

static func has_player_member(hero: HeroData, pname: String) -> bool:
	for m in members(hero):
		if String(m.kind) == "player" and String(m.name) == GuildRules.clean_alias(pname):
			return true
	return false

static func treasury_cap(hero: HeroData) -> float:
	return TREASURY_BASE + TREASURY_PER_LEVEL * float(level(hero))

## Move the tithes into the Guildmaster's purse. Returns the gold collected.
static func collect_treasury(hero: HeroData) -> int:
	if not is_master(hero):
		return 0
	var g := int(floor(float(hero.own_guild.get("treasury", 0.0))))
	if g <= 0:
		return 0
	hero.own_guild["treasury"] = float(hero.own_guild.treasury) - float(g)
	hero.inventory.gold += g
	hero.inventory.changed.emit()
	Events.gold_picked.emit(g)
	Events.guild_changed.emit()
	return g

## The hero levelled up: members below the recruit range catch up, the rest may train a level.
static func on_hero_level(hero: HeroData) -> void:
	if not has(hero):
		return
	var r := recruit_range(hero)
	for m in npc_members(hero):
		if int(m.level) < r.x:
			m["level"] = r.x
	Events.guild_changed.emit()

# ---- the clock -------------------------------------------------------------------------------------------------

## Called every frame by Game with the frame time; does its work every TICK seconds of play.
static func tick(hero: HeroData, delta: float) -> void:
	if not has(hero):
		return
	_acc += delta
	if _acc < TICK:
		return
	var dt := _acc
	_acc = 0.0
	advance(hero, dt)

## Run the guild forward by `dt` seconds of play (tithes, renown, loyalty, training, recruitment, Call to Arms).
static func advance(hero: HeroData, dt: float) -> void:
	if not has(hero):
		return
	var og := hero.own_guild
	var minutes := dt / 60.0
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%s/tick/%d" % [hero.hero_name, int(hero.play_time * 10.0)])
	var chest := 1.0 + float(DataGuildPassives.passive(&"war_chest").per) * float(rank(hero, &"war_chest"))
	var train := 1.0 + 0.25 * float(rank(hero, &"veteran_training"))
	var renown := 0.0
	var tithe := 0.0
	for m in npc_members(hero):
		var t: Dictionary = DataGuildPassives.TRAITS.get(StringName(m.trait), {})
		tithe += TITHE_PER_LEVEL * float(m.level) * float(t.get("tithe", 1.0)) * chest * minutes
		var r := (RENOWN_PER_MEMBER + RENOWN_PER_LEVEL * float(m.level)) * float(t.get("renown", 1.0)) * minutes
		m["renown"] = float(m.renown) + r
		renown += r
		m["loyalty"] = minf(100.0, float(m.loyalty) + LOYALTY_PER_MINUTE * float(t.get("loyal", 1.0)) * minutes)
		if int(m.level) < hero.progress.level and rng.randf() < TRAIN_CHANCE * train * float(t.get("train", 1.0)) * dt / TRAIN_EVERY:
			m["level"] = int(m.level) + 1
			Events.notify.emit("%s trained up to level %d." % [m.name, m.level], &"info")
	og["treasury"] = minf(treasury_cap(hero), float(og.get("treasury", 0.0)) + tithe)
	add_renown(hero, renown)
	if free_slots(hero) > 0 and hero.play_time >= float(og.get("next_recruit", 0.0)):
		recruit(hero, rng)
		if free_slots(hero) > 0:
			_schedule_recruit(hero, rng)
	GuildSummons.tick(hero)

# ---- renown from deeds -----------------------------------------------------------------------------------------

static func connect_events() -> void:
	if _connected:
		return
	_connected = true
	Events.actor_died.connect(func(actor: Node, _killer: Node) -> void:
		var hero := Game.hero
		if not has(hero) or not (actor is Enemy):
			return
		var e := actor as Enemy
		add_renown(hero, 20.0 if e.is_boss else (10.0 if e.is_miniboss() else (2.0 if e.is_elite else 0.25))))
	Events.stage_cleared.connect(func(_m: StringName) -> void: add_renown(Game.hero, 12.0))
	Events.player_leveled.connect(func(_l: int, _g: int) -> void: on_hero_level(Game.hero))

## A guild job handed in (GuildJobs.claim): the Guildmaster's guild gains renown with it.
static func on_job(hero: HeroData, gold: int) -> void:
	add_renown(hero, 30.0 + float(gold) / 20.0)

# ---- saving ----------------------------------------------------------------------------------------------------

static func to_plain(og: Dictionary) -> Dictionary:
	return og.duplicate(true) if not og.is_empty() else {}

## Rebuild from a save, field by field; a damaged or empty guild loads as none.
static func from_plain(d: Variant) -> Dictionary:
	if not (d is Dictionary) or (d as Dictionary).is_empty():
		return {}
	var nm := GuildRules.clean_alias(String(d.get("name", "")))
	if nm == "":
		return {}
	var slots_n := int(d.get("slots", DataGuildPassives.BASE_SLOTS))
	var allowed := [DataGuildPassives.BASE_SLOTS]
	for u in DataGuildPassives.SLOT_UPGRADES:
		allowed.append(int(u[0]))
	if not allowed.has(slots_n):
		slots_n = DataGuildPassives.BASE_SLOTS
	var passives := {}
	var ps = d.get("passives", {})
	if ps is Dictionary:
		for k in ps:
			var p := DataGuildPassives.passive(StringName(k))
			if not p.is_empty():
				passives[String(k)] = clampi(int(ps[k]), 0, int(p.max))
	var ms := []
	var src = d.get("members", [])
	var serial := maxi(0, int(d.get("serial", 0)))
	if src is Array:
		for m in src:
			if not (m is Dictionary) or ms.size() >= slots_n:
				continue
			var cls := String(m.get("cls", "knight"))
			var tr := String(m.get("trait", "loyal"))
			var mid := int(m.get("id", 0))
			if mid <= 0 or DB.class_def(StringName(cls)) == null or GuildRules.clean_alias(String(m.get("name", ""))) == "":
				continue
			serial = maxi(serial, mid)
			ms.append({"id": mid, "kind": "player" if String(m.get("kind", "npc")) == "player" else "npc",
				"name": GuildRules.clean_alias(String(m.name)), "cls": cls, "level": clampi(int(m.get("level", 1)), 1, BH.LEVEL_CAP),
				"trait": tr if DataGuildPassives.TRAITS.has(StringName(tr)) else "loyal", "joined": float(m.get("joined", 0.0)),
				"loyalty": clampf(float(m.get("loyalty", 0.0)), 0.0, 100.0), "renown": maxf(0.0, float(m.get("renown", 0.0))), "look": int(m.get("look", 0))})
	var sm = d.get("summon", {})
	var summon := {"rank": 1, "ready_at": 0.0, "until": 0.0, "called": []}
	if sm is Dictionary:
		summon.rank = clampi(int(sm.get("rank", 1)), 1, DataGuildPassives.SUMMON_MAX_RANK)
		summon.ready_at = float(sm.get("ready_at", 0.0))
		summon.until = float(sm.get("until", 0.0))
		var called = sm.get("called", [])
		if called is Array:
			summon.called = (called as Array).map(func(x): return int(x))
	return {"name": nm, "motto": clean_text(String(d.get("motto", "")), MOTTO_MAX), "info": clean_text(String(d.get("info", "")), INFO_MAX),
		"style": GuildBannerArt.sanitize(d.get("style", {})), "founded": float(d.get("founded", 0.0)),
		"renown": maxf(0.0, float(d.get("renown", 0.0))), "level": clampi(int(d.get("level", 1)), 1, DataGuildPassives.LEVEL_CAP),
		"slots": slots_n, "members": ms, "passives": passives, "summon": summon, "next_recruit": float(d.get("next_recruit", 0.0)),
		"serial": serial, "treasury": maxf(0.0, float(d.get("treasury", 0.0)))}

## What travels to other players: the guild as they see it (GuildRegistry.clean_remote reads it).
static func snapshot(hero: HeroData, with_banner := true) -> Dictionary:
	if not has(hero):
		return {}
	var og := hero.own_guild
	return {"name": String(og.name), "motto": String(og.motto), "info": String(og.get("info", "")), "master": GuildRules.clean_alias(hero.hero_name),
		"color": Color(String(og.style.field)).to_html(false), "style": og.style, "level": int(og.level), "members": members(hero).size() + 1,
		"passives": (og.passives as Dictionary).duplicate(), "banner": hero.guild_banner if with_banner else PackedByteArray()}
