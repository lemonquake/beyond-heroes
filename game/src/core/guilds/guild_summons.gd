class_name GuildSummons
extends RefCounted
## bh-027: Call to Arms, the Guildmaster's active guild skill. The strongest members answer (one at rank 1, one more
## per rank), fight beside the Guildmaster for DataGuildPassives.SUMMON_DURATION seconds of play and can be called again
## SUMMON_COOLDOWN seconds after the call. They follow through doors and waypoints (they are spawned again beside the
## hero on every map until the call ends), come back on their feet a little after falling, and leave when time is up.
## In multiplayer they fight too, and every other player sees them (Net sends them like Tempos).
##
## Their hero sheets (QuakeMate) are built on demand and kept while the call lasts; nothing but the call itself is saved.

const RESPAWN_DELAY := 18.0
const MATE_UID := 700000

static var _mates := {}          # member id -> QuakeMate

static func state(hero: HeroData) -> Dictionary:
	return hero.own_guild.get("summon", {}) if OwnGuild.has(hero) else {}

static func rank(hero: HeroData) -> int:
	return int(state(hero).get("rank", 1)) if OwnGuild.has(hero) else 0

static func active(hero: HeroData) -> bool:
	return OwnGuild.has(hero) and hero.play_time < float(state(hero).get("until", 0.0))

static func time_left(hero: HeroData) -> float:
	return maxf(0.0, float(state(hero).get("until", 0.0)) - hero.play_time) if OwnGuild.has(hero) else 0.0

static func cooldown_left(hero: HeroData) -> float:
	return maxf(0.0, float(state(hero).get("ready_at", 0.0)) - hero.play_time) if OwnGuild.has(hero) else 0.0

## Who would answer a call now: the strongest adventurers (fellow players fight for themselves), up to the rank.
static func answering(hero: HeroData) -> Array:
	var list := OwnGuild.npc_members(hero).duplicate()
	list.sort_custom(func(a, b): return int(a.level) > int(b.level) or (int(a.level) == int(b.level) and float(a.loyalty) > float(b.loyalty)))
	return list.slice(0, rank(hero))

static func call_error(hero: HeroData) -> String:
	if not OwnGuild.is_master(hero):
		return "Only a Guildmaster can call their guild to arms"
	if active(hero):
		return "Your guild is already fighting beside you (%s left)" % clock(time_left(hero))
	if cooldown_left(hero) > 0.0:
		return "Call to Arms is ready again in %s" % clock(cooldown_left(hero))
	if OwnGuild.npc_members(hero).is_empty():
		return "Nobody in your guild can answer yet: wait for adventurers to join"
	if Game.travelling:
		return "Not while travelling"
	return ""

## Call the guild to arms. Returns {ok, text}.
static func call_to_arms(hero: HeroData, player: Node3D) -> Dictionary:
	var err := call_error(hero)
	if err != "":
		return {"ok": false, "text": err}
	var st := state(hero)
	var who := answering(hero)
	st["until"] = hero.play_time + DataGuildPassives.SUMMON_DURATION
	st["ready_at"] = hero.play_time + DataGuildPassives.SUMMON_COOLDOWN
	st["called"] = who.map(func(m): return int(m.id))
	_mates.clear()
	if player != null and is_instance_valid(player) and Game.current_map != null and is_instance_valid(Game.current_map):
		spawn_for(Game.current_map, player, hero)
	Audio.play_ui(&"level_up")
	Events.camera_shake.emit(0.12)
	Events.guild_changed.emit()
	var names := who.map(func(m): return String(m.name))
	return {"ok": true, "text": "Call to Arms! %s answer%s the banner of %s for %s." % [", ".join(names), "s" if names.size() == 1 else "",
		hero.own_guild.name, clock(DataGuildPassives.SUMMON_DURATION)]}

static func upgrade_cost(hero: HeroData) -> int:
	var r := rank(hero)
	return int(DataGuildPassives.SUMMON_COSTS[r - 1]) if r >= 1 and r < DataGuildPassives.SUMMON_MAX_RANK else 0

static func upgrade_error(hero: HeroData) -> String:
	if not OwnGuild.is_master(hero):
		return "Only the Guildmaster can train Call to Arms"
	var r := rank(hero)
	if r >= DataGuildPassives.SUMMON_MAX_RANK:
		return "Call to Arms is at its highest rank"
	var need := int(DataGuildPassives.SUMMON_LEVELS[r - 1])
	if OwnGuild.level(hero) < need:
		return "Rank %d needs guild level %d" % [r + 1, need]
	if hero.inventory.gold < upgrade_cost(hero):
		return "Rank %d costs %d gold" % [r + 1, upgrade_cost(hero)]
	return ""

static func upgrade(hero: HeroData) -> String:
	var err := upgrade_error(hero)
	if err != "":
		return err
	hero.inventory.gold -= upgrade_cost(hero)
	hero.inventory.changed.emit()
	state(hero)["rank"] = rank(hero) + 1
	Events.guild_changed.emit()
	return ""

static func clock(sec: float) -> String:
	var s := int(ceil(sec))
	return "%d:%02d" % [s / 60, s % 60]

# ---- in the world ----------------------------------------------------------------------------------------------

static func fighters(tree: SceneTree = null) -> Array:
	var t := tree if tree else Engine.get_main_loop() as SceneTree
	if t == null:
		return []
	return t.get_nodes_in_group(&"guild_fighter").filter(func(n): return is_instance_valid(n) and not n.is_queued_for_deletion())

static func fighter_for(member_id: int) -> GuildFighter:
	for f in fighters():
		if (f as GuildFighter).member_id == member_id:
			return f
	return null

## The hero sheet of a member answering the call: their class and level, gear of their level (Advanced to Master by
## level, never set pieces), a few draughts; built once per call.
static func mate_for(hero: HeroData, member: Dictionary) -> QuakeMate:
	var mid := int(member.id)
	if _mates.has(mid):
		return _mates[mid]
	var cls := StringName(member.cls)
	var lvl := clampi(int(member.level), 1, BH.LEVEL_CAP)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash([hero.hero_name, mid, lvl])
	var m := QuakeMate.new()
	m.uid = mid
	m.hero = Game.new_hero(cls, String(member.name))
	m.hero.difficulty = hero.difficulty
	m.hero.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(lvl) - m.hero.progress.total_xp))
	QuakeBrain.spend_points(m.hero)
	m.hero.guild = hero.guild
	m.hero.tier = hero.tier
	m.hero.equipment.tier_rank = hero.tier
	m.hero.world_flags = hero.world_flags.duplicate()
	m.hero.look = HeroLook.to_save(HeroLook.random(_look_rng(member), 0.1))
	_gear_up(m.hero, lvl, rng)
	var hp := DB.make_item(&"health_potion", BH.Rarity.COMMON, lvl, rng.randi())
	hp.count = 4
	m.hero.inventory.add(hp)
	m.tdata = TempoData.new()
	m.tdata.uid = MATE_UID + mid
	m._build_tempo_data(rng)
	_mates[mid] = m
	return m

static func _look_rng(member: Dictionary) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = int(member.get("look", 1))
	return r

static func _gear_up(h: HeroData, lvl: int, rng: RandomNumberGenerator) -> void:
	var rarity := BH.Rarity.ADVANCED if lvl < 15 else (BH.Rarity.ELITE if lvl < 35 else BH.Rarity.MASTER)
	var cats := [&"weapon", &"armor", &"helm", &"leggings", &"gloves", &"boots", &"inner_garment", &"accessory"]
	if h.cls.id == &"knight":
		cats.append(&"shield")
	for cat in cats:
		var base := ItemGenerator.random_base(rng, lvl, [cat], h.cls.id, 1.0)
		if base == null:
			continue
		var it := ItemGenerator.generate(base, lvl, rarity, rng)
		var slot := h.equipment.auto_slot(it)
		if slot == &"":
			continue
		var res := h.equipment.equip(it, slot, h.progress.level, h.progress.base_attributes())
		if not bool(res.get("ok", false)):
			continue

## Put everyone answering the call into the world beside `player` (Game.load_map calls this; so does the call).
static func spawn_for(map: Node3D, player: Node3D, hero: HeroData) -> void:
	if map == null or player == null or hero == null or not active(hero):
		return
	var info := GuildRegistry.info(hero, GuildRegistry.OWN)
	var called: Array = state(hero).get("called", [])
	var slot := 0
	for mid in called:
		var member := OwnGuild.find_member(hero, int(mid))
		if member.is_empty():
			continue
		if fighter_for(int(mid)) == null:
			_spawn_one(map, player, hero, member, slot, info)
		slot += 1

static func _spawn_one(map: Node3D, player: Node3D, hero: HeroData, member: Dictionary, slot: int, info: Dictionary) -> GuildFighter:
	var mate := mate_for(hero, member)
	mate.tdata.fallen = false
	var a := GuildFighter.new().bind_member(mate, member, player, slot, String(info.get("short", "Guild")), info.get("color", Color(1.0, 0.86, 0.5)))
	map.add_child(a)
	var f: Vector3 = player.global_transform.basis.z.slide(Vector3.UP).normalized()
	if f.length() < 0.1:
		f = Vector3.BACK
	var o: Vector2 = GuildFighter.RANKS[slot % GuildFighter.RANKS.size()]
	var spot := player.global_position - f * o.y + f.cross(Vector3.UP) * o.x
	if map.is_inside_tree():
		spot = CombatQuery.reachable_point(map.get_world_3d(), player.global_position, spot, 0.4)
		spot = CombatQuery.ground_at(map.get_world_3d(), spot + Vector3.UP * 1.5)
	a.global_position = spot + Vector3.UP * 0.05
	a.rotation.y = player.rotation.y
	FX.spawn(VFXLib.particles(Color(a.guild_color, 0.85), 30, 0.9, true, 0.1, 2.4, 180.0, Vector3(0, 1.8, 0), 0.5), spot + Vector3.UP)
	return a

## A fighter fell: back on their feet beside the Guildmaster a little later, if the call still holds.
static func on_fighter_fell(a: GuildFighter) -> void:
	var tree := a.get_tree()
	var mid := a.member_id
	if tree == null:
		return
	tree.create_timer(RESPAWN_DELAY).timeout.connect(func() -> void:
		var hero := Game.hero
		var player := Game.player as Node3D
		var map := Game.current_map
		if hero == null or not active(hero) or player == null or not is_instance_valid(player) or map == null or not is_instance_valid(map):
			return
		if fighter_for(mid) != null:
			return
		var member := OwnGuild.find_member(hero, mid)
		var called: Array = state(hero).get("called", [])
		if member.is_empty() or not called.has(mid):
			return
		var m: QuakeMate = _mates.get(mid)
		if m:
			m.tdata.hp_frac = 0.6
			m.tdata.mana_frac = 0.6
		_spawn_one(map, player, hero, member, called.find(mid), GuildRegistry.info(hero, GuildRegistry.OWN)))

## The call ran out (OwnGuild.advance checks every few seconds).
static func tick(hero: HeroData) -> void:
	if not OwnGuild.has(hero):
		return
	var st := state(hero)
	if not (st.get("called", []) as Array).is_empty() and not active(hero):
		st["called"] = []
		_mates.clear()
		var left := fighters()
		for f in left:
			(f as GuildFighter).depart()
		if not left.is_empty():
			Events.notify.emit("The call is over: your guild returns to its hall.", &"info")
		Events.guild_changed.emit()

static func dismiss(_hero: HeroData = null) -> void:
	for f in fighters():
		(f as GuildFighter).depart()
	_mates.clear()

static func dismiss_member(member_id: int) -> void:
	var f := fighter_for(member_id)
	if f:
		f.depart()
	_mates.erase(member_id)
