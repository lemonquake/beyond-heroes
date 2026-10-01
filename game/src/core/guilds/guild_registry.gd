class_name GuildRegistry
## bh-027: every guild a hero knows, in one shape. HeroData.guild names the hero's membership:
##
##   swordfin, lantern   the two old guilds of Malasugue (DataGuilds)
##   npc_0 .. npc_3      guilds that set up in the Guild House, rolled once per hero (GuildNames) and saved with them
##   own                 the guild the hero founded and leads (OwnGuild, HeroData.own_guild)
##   remote              another player's guild the hero joined in multiplayer (HeroData.remote_guild: a snapshot)
##
## Other players' guilds seen in multiplayer are imported (`imp_<n>`) with their names, mottos and banners, so they hang
## in the Guild House afterwards. info() returns the same keys for every kind, so rules and windows never care which.

const NPC_COUNT := 4
const IMPORT_MAX := 8
const OWN := &"own"
const REMOTE := &"remote"

## Perks a rolled guild may grant, per tier step (like the old guilds' three): [stat, op, value per tier, words].
const NPC_PERKS := [
	[&"crit_chance", "flat", 0.004, "+0.4% Critical Chance"], [&"max_hp", "inc", 0.015, "+1.5% Maximum HP"],
	[&"elemental_damage", "inc", 0.02, "+2% Elemental Damage"], [&"phys_damage", "inc", 0.02, "+2% Physical Damage"],
	[&"magic_damage", "inc", 0.02, "+2% Magic Damage"], [&"move_speed", "inc", 0.008, "+0.8% Movement Speed"],
	[&"gold_find", "inc", 0.03, "+3% Gold Find"], [&"xp_gain", "inc", 0.015, "+1.5% Experience Gain"],
	[&"status_res", "flat", 0.01, "+1% Status Resistance"], [&"projectile_damage", "inc", 0.025, "+2.5% Projectile Damage"],
	[&"dot_damage", "inc", 0.03, "+3% Damage over Time"], [&"defense", "inc", 0.02, "+2% Defense"],
	[&"healing", "inc", 0.02, "+2% Healing Effectiveness"], [&"tempo_damage", "inc", 0.025, "+2.5% Tempo Damage"],
	[&"elite_damage", "inc", 0.02, "+2% Damage to Champions"], [&"max_mana", "inc", 0.02, "+2% Maximum Mana"],
]
## One house rule each rolled guild keeps: [key, value, words].
const NPC_FEATURES := [
	["elite_gold", 0.08, "Bounty pay: +8% gold from elites and bosses"], ["potion_healing", 0.08, "Potions heal 8% more"],
	["inn_discount", 0.2, "20% off rest at the Salted Marlin"], ["elite_gold", 0.05, "Bounty pay: +5% gold from elites and bosses"],
]
const MASTER_TITLES := ["Captain", "Marshal", "Warden", "Seneschal", "Loremaster", "Guildmaster", "Commander", "Steward", "Provost"]
const HALLS := ["Lodge", "Hall", "Chapterhouse", "Barracks", "Longhouse", "Counting House", "Watchtower"]

# ---- the rolled guilds ---------------------------------------------------------------------------------------------

## The hero's guild world ({seed, npc: [...], imported: [...]}), rolled on first use.
static func world(hero: HeroData) -> Dictionary:
	var w: Dictionary = hero.guild_world
	if not w.has("npc") or (w.npc as Array).size() < NPC_COUNT:
		var seed := int(w.get("seed", 0))
		if seed == 0:
			seed = absi(hash("%s/guilds/%d" % [hero.hero_name, Time.get_ticks_usec()])) + 1
		w["seed"] = seed
		w["npc"] = roll_npc_guilds(seed)
	if not w.has("imported"):
		w["imported"] = []
	return w

static func roll_npc_guilds(seed: int) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var out := []
	var taken := ["Swordfin Company", "Lantern Covenant"]
	var masters := []
	for i in NPC_COUNT:
		var nm := GuildNames.roll_name(rng, taken)
		taken.append(nm)
		var perks := []
		var texts := []
		var pool := range(NPC_PERKS.size())
		for k in 3:
			var pick: int = pool[rng.randi_range(0, pool.size() - 1)]
			pool.erase(pick)
			var p: Array = NPC_PERKS[pick]
			perks.append([String(p[0]), String(p[1]), float(p[2])])
			texts.append(String(p[3]))
		var feat: Array = NPC_FEATURES[rng.randi_range(0, NPC_FEATURES.size() - 1)]
		var master := NameForge.person(rng, masters)
		masters.append(master)
		var style := GuildBannerArt.style_for(nm, rng.randi())
		out.append({"id": "npc_%d" % i, "name": nm, "short": GuildNames.short(nm), "motto": GuildNames.motto(rng),
			"master": "%s %s" % [MASTER_TITLES[rng.randi_range(0, MASTER_TITLES.size() - 1)], master],
			"hall": "%s %s" % [GuildNames.short(nm), HALLS[rng.randi_range(0, HALLS.size() - 1)]],
			"style": style, "perks": perks, "perk_text": texts, "feature": [String(feat[0]), float(feat[1]), String(feat[2])],
			"members": rng.randi_range(14, 64), "level": rng.randi_range(3, 12)})
	return out

## One saved rolled guild, checked field by field (a hand-edited or damaged save cannot break the Guild House).
static func _clean_npc(d: Variant, i: int) -> Dictionary:
	if not (d is Dictionary):
		return {}
	var perks := []
	var texts := []
	for p in d.get("perks", []):
		if p is Array and (p as Array).size() == 3 and StatDefs.DEFS.has(StringName(p[0])):
			perks.append([String(p[0]), "flat" if String(p[1]) == "flat" else "inc", clampf(float(p[2]), 0.0, 0.05)])
	for t in d.get("perk_text", []):
		texts.append(GuildRules.clean_alias(String(t)))
	var f = d.get("feature", [])
	var feat := ["elite_gold", 0.0, ""]
	if f is Array and (f as Array).size() == 3 and String(f[0]) in ["elite_gold", "potion_healing", "inn_discount"]:
		feat = [String(f[0]), clampf(float(f[1]), 0.0, 0.25), String(f[2])]
	var nm := GuildRules.clean_alias(String(d.get("name", "")))
	if nm == "":
		return {}
	return {"id": "npc_%d" % i, "name": nm, "short": GuildRules.clean_alias(String(d.get("short", GuildNames.short(nm)))),
		"motto": String(d.get("motto", "")).left(80), "master": GuildRules.clean_alias(String(d.get("master", ""))),
		"hall": GuildRules.clean_alias(String(d.get("hall", ""))), "style": GuildBannerArt.sanitize(d.get("style", {})),
		"perks": perks, "perk_text": texts, "feature": feat, "members": clampi(int(d.get("members", 20)), 1, 999),
		"level": clampi(int(d.get("level", 1)), 1, DataGuildPassives.LEVEL_CAP)}

static func world_from_plain(d: Variant) -> Dictionary:
	var out := {}
	if not (d is Dictionary) or (d as Dictionary).is_empty():
		return out
	out["seed"] = maxi(0, int(d.get("seed", 0)))
	var npc := []
	var src = d.get("npc", [])
	if src is Array:
		for i in mini((src as Array).size(), NPC_COUNT):
			var g := _clean_npc(src[i], i)
			if g.is_empty():
				return {"seed": out.seed}       # a damaged roster is rolled again from its seed
			npc.append(g)
	if npc.size() == NPC_COUNT:
		out["npc"] = npc
	var imp := []
	var src2 = d.get("imported", [])
	if src2 is Array:
		for g in src2:
			var c := clean_remote(g)
			if not c.is_empty() and imp.size() < IMPORT_MAX:
				imp.append(c)
	out["imported"] = imp
	return out

static func world_to_plain(hero: HeroData) -> Dictionary:
	if hero.guild_world.is_empty():
		return {}
	var w := world(hero)
	return {"seed": int(w.seed), "npc": (w.npc as Array).duplicate(true),
		"imported": (w.imported as Array).map(func(g): return remote_to_plain(g))}

static func npc_guild(hero: HeroData, gid: StringName) -> Dictionary:
	if not String(gid).begins_with("npc_"):
		return {}
	for g in world(hero).npc:
		if String(g.id) == String(gid):
			return g
	return {}

## A line about a rolled guild for its page: who leads it, how many answer its banner, what it is known for.
static func npc_blurb(g: Dictionary) -> String:
	var perks: Array = g.get("perk_text", [])
	return "%s leads %d sworn members from %s. Known for: %s." % [String(g.master), int(g.members), String(g.hall),
		", ".join(perks.map(func(t): return String(t).to_lower())) if not perks.is_empty() else "odd jobs and honest pay"]

# ---- other players' guilds (snapshots) -----------------------------------------------------------------------------

## A guild snapshot as it travels between players: {key, name, motto, master, color, style, level, members, passives,
## banner (JPEG bytes, may be empty)}. `key` is "<master hero name>/<guild name>" — how a guild is recognised.
static func clean_remote(d: Variant) -> Dictionary:
	if not (d is Dictionary):
		return {}
	var nm := GuildRules.clean_alias(String(d.get("name", "")))
	var master := GuildRules.clean_alias(String(d.get("master", "")))
	if nm == "" or master == "":
		return {}
	var passives := {}
	var src = d.get("passives", {})
	if src is Dictionary:
		for k in src:
			if DataGuildPassives.PASSIVES.has(StringName(k)):
				passives[String(k)] = clampi(int(src[k]), 0, int(DataGuildPassives.passive(StringName(k)).max))
	var banner = d.get("banner", PackedByteArray())
	if banner is String:
		banner = GuildRules.load_banner_bytes(banner)
	elif banner is PackedByteArray and not (banner as PackedByteArray).is_empty():
		var probe := Image.new()
		if (banner as PackedByteArray).size() > GuildRules.BANNER_MAX_BYTES or probe.load_jpg_from_buffer(banner) != OK:
			banner = PackedByteArray()
	else:
		banner = PackedByteArray()
	var col := String(d.get("color", "8c1f1f"))
	return {"key": "%s/%s" % [master, nm], "name": nm, "motto": OwnGuild.clean_text(String(d.get("motto", "")), OwnGuild.MOTTO_MAX),
		"info": OwnGuild.clean_text(String(d.get("info", "")), OwnGuild.INFO_MAX), "master": master,
		"color": col if Color.html_is_valid(col) else "8c1f1f", "style": GuildBannerArt.sanitize(d.get("style", {})),
		"level": clampi(int(d.get("level", 1)), 1, DataGuildPassives.LEVEL_CAP), "members": clampi(int(d.get("members", 1)), 1, DataGuildPassives.MAX_SLOTS + 1),
		"passives": passives, "banner": banner}

static func remote_to_plain(g: Dictionary) -> Dictionary:
	var out := g.duplicate(true)
	var b = g.get("banner", PackedByteArray())
	out["banner"] = Marshalls.raw_to_base64(b) if b is PackedByteArray and not (b as PackedByteArray).is_empty() else ""
	return out

## Remember another player's guild (newest first; the same guild replaces its older snapshot).
static func import_remote(hero: HeroData, snapshot: Dictionary) -> void:
	var g := clean_remote(snapshot)
	if g.is_empty() or hero == null:
		return
	if OwnGuild.has(hero) and g.key == OwnGuild.key(hero):
		return
	var imp: Array = world(hero).imported
	for i in range(imp.size() - 1, -1, -1):
		if String(imp[i].key) == String(g.key):
			if (g.banner as PackedByteArray).is_empty():
				g.banner = imp[i].banner
			if _same_snapshot(imp[i], g):
				return                     # nothing new: no event (profiles arrive often in multiplayer)
			imp.remove_at(i)
	imp.push_front(g)
	while imp.size() > IMPORT_MAX:
		imp.pop_back()
	Events.guild_changed.emit()

static func _same_snapshot(a: Dictionary, b: Dictionary) -> bool:
	for k in ["name", "motto", "info", "master", "color", "level", "members"]:
		if a.get(k) != b.get(k):
			return false
	return a.get("style") == b.get("style") and a.get("passives") == b.get("passives") and hash(a.get("banner")) == hash(b.get("banner"))

# ---- one shape for all ---------------------------------------------------------------------------------------------

## Every guild id the hero knows, in display order (the hero's own guild first when they lead one).
static func all_ids(hero: HeroData) -> Array:
	var out := []
	if hero == null:
		return [&"swordfin", &"lantern"]
	if OwnGuild.has(hero):
		out.append(OWN)
	if hero.guild == REMOTE and not hero.remote_guild.is_empty():
		out.append(REMOTE)
	out.append_array([&"swordfin", &"lantern"])
	for g in world(hero).npc:
		out.append(StringName(g.id))
	for i in (world(hero).imported as Array).size():
		out.append(StringName("imp_%d" % i))
	return out

## A guild any hero may register with at a counter (the old guilds and the rolled ones).
static func joinable(hero: HeroData, gid: StringName) -> bool:
	return DataGuilds.GUILDS.has(gid) or not npc_guild(hero, gid).is_empty()

## Whether `gid` is a guild the hero can belong to right now (save loading).
static func valid_membership(hero: HeroData, gid: StringName) -> bool:
	if gid == &"":
		return true
	if gid == OWN:
		return OwnGuild.has(hero)
	if gid == REMOTE:
		return not hero.remote_guild.is_empty()
	return joinable(hero, gid)

static func _imported(hero: HeroData, gid: StringName) -> Dictionary:
	if not String(gid).begins_with("imp_"):
		return {}
	var i := int(String(gid).substr(4))
	var imp: Array = world(hero).imported
	return imp[i] if i >= 0 and i < imp.size() else {}

## {id, kind, name, short, hall, motto, master, color, perks: [[stat, op, per tier]], perk_text, features, shop_discount,
## inn_discount, elite_gold, potion_healing, members, level, joinable, passives (own / remote / imported)}. {} = unknown.
static func info(hero: HeroData, gid: StringName) -> Dictionary:
	if gid == &"":
		return {}
	if DataGuilds.GUILDS.has(gid):
		var g: Dictionary = DataGuilds.guild(gid).duplicate()
		g["id"] = gid
		g["kind"] = "canon"
		g["perks"] = (g.perks as Array).map(func(p): return [p[0], "inc", float(p[1])])
		g["members"] = 120 if gid == &"swordfin" else 85
		g["level"] = 14 if gid == &"swordfin" else 12
		g["joinable"] = true
		g["passives"] = {}
		g["info"] = String(g.motto) + " " + ("The oldest company in Malasugue: steel for hire, bounties paid promptly, and a hall on the east road." if gid == &"swordfin" \
			else "Archivists, healers and lamp-keepers who map the dark places of Salmonan and keep the roads lit.")
		return g
	if hero == null:
		return {}
	var npc := npc_guild(hero, gid)
	if not npc.is_empty():
		var f: Array = npc.feature
		var out := {"id": gid, "kind": "npc", "name": npc.name, "short": npc.short, "hall": npc.hall, "motto": npc.motto,
			"master": npc.master, "color": Color(String(npc.style.field)).lightened(0.15), "perks": npc.perks, "perk_text": npc.perk_text,
			"features": [String(f[2])], "shop_discount": {}, "inn_discount": 0.0, "elite_gold": 0.0, "potion_healing": 0.0,
			"members": int(npc.members), "level": int(npc.level), "joinable": true, "passives": {}, "style": npc.style,
			"info": npc_blurb(npc)}
		out[String(f[0])] = float(f[1])
		return out
	if gid == OWN and OwnGuild.has(hero):
		var og: Dictionary = hero.own_guild
		return {"id": OWN, "kind": "own", "name": String(og.name), "short": GuildNames.short(String(og.name)), "hall": "%s Hall" % GuildNames.short(String(og.name)),
			"motto": String(og.motto), "master": hero.hero_name, "color": Color(String(og.style.field)).lightened(0.15), "perks": [], "perk_text": [],
			"features": ["Guildmaster: %s" % hero.hero_name], "shop_discount": {}, "inn_discount": 0.0, "elite_gold": 0.0, "potion_healing": 0.0,
			"members": OwnGuild.members(hero).size() + 1, "level": OwnGuild.level(hero), "joinable": false, "passives": og.passives, "style": og.style,
			"info": String(og.get("info", "")), "key": OwnGuild.key(hero)}
	var snap := hero.remote_guild if gid == REMOTE else _imported(hero, gid)
	if not snap.is_empty():
		return {"id": gid, "kind": "remote" if gid == REMOTE else "imported", "name": String(snap.name), "short": GuildNames.short(String(snap.name)),
			"hall": "%s's guild" % String(snap.master), "motto": String(snap.motto), "master": String(snap.master), "color": Color(String(snap.color)),
			"perks": [], "perk_text": [], "features": ["Led by %s, a fellow hero" % String(snap.master)], "shop_discount": {}, "inn_discount": 0.0,
			"elite_gold": 0.0, "potion_healing": 0.0, "members": int(snap.members), "level": int(snap.level), "joinable": false,
			"passives": snap.passives, "style": snap.style, "key": String(snap.key), "info": String(snap.get("info", ""))}
	return {}

## The banner a guild flies: its picture (the hero's upload for a guild they lead or renamed, a fellow hero's upload for
## theirs), the old guilds' painted banners, else a banner painted from the guild's style.
static func banner(hero: HeroData, gid: StringName) -> Texture2D:
	if hero != null and gid == hero.guild and gid != REMOTE:
		var own := GuildRules.banner_texture(hero)
		if own != null:
			return own
	if DataGuilds.GUILDS.has(gid):
		return UIArt.tex(String(DataGuilds.guild(gid).banner))
	var snap: Dictionary = {}
	if hero != null:
		snap = hero.remote_guild if gid == REMOTE else _imported(hero, gid)
	if not snap.is_empty():
		var t := bytes_texture(snap.get("banner", PackedByteArray()))
		if t != null:
			return t
	var g := info(hero, gid)
	return GuildBannerArt.texture(g.get("style", {})) if not g.is_empty() else null

static var _bytes_cache := {}

static func bytes_texture(bytes: Variant) -> Texture2D:
	if not (bytes is PackedByteArray) or (bytes as PackedByteArray).is_empty():
		return null
	var k := hash(bytes)
	if _bytes_cache.has(k):
		return _bytes_cache[k]
	var img := Image.new()
	if img.load_jpg_from_buffer(bytes) != OK:
		return null
	var t := ImageTexture.create_from_image(img)
	if _bytes_cache.size() > 24:
		_bytes_cache.clear()
	_bytes_cache[k] = t
	return t
