class_name GuildRules
## Joining a guild, transfers, tier promotion, and every bonus a guild or tier grants. Pure rules over HeroData
## (no nodes): registrars' dialogue actions, the UI and the tests all call these.

## "" when the hero may join `gid` now, otherwise the reason.
static func join_error(hero: HeroData, gid: StringName) -> String:
	if not GuildRegistry.joinable(hero, gid):
		return "Unknown guild"
	if hero.guild == gid:
		return "You already carry the %s's seal" % GuildRegistry.info(hero, gid).short
	if OwnGuild.is_master(hero):
		return "You lead %s. Disband it before you join another guild" % hero.own_guild.name
	var fee := join_fee(hero, gid)
	if hero.inventory.gold < fee:
		return "Not enough gold (%d needed)" % fee
	return ""

## First registration costs the Class E fee; changing guild costs the transfer fee (the tier is kept).
static func join_fee(hero: HeroData, gid: StringName) -> int:
	if hero.guild == gid:
		return 0
	return DataGuilds.TRANSFER_FEE if hero.guild != &"" else int(DataGuilds.tier(1).fee)

static func join(hero: HeroData, gid: StringName) -> String:
	var err := join_error(hero, gid)
	if err != "":
		return err
	var fee := join_fee(hero, gid)
	hero.inventory.gold -= fee
	hero.inventory.changed.emit()
	var first := hero.guild == &""
	hero.guild = gid
	hero.remote_guild = {}
	if hero.tier < 1:
		hero.set_tier(1)
	else:
		hero.stats_dirty.emit()
	Events.guild_joined.emit(gid, first)
	hero.check_promotions()
	return ""

## Next promotion: {rank, fee, level, flag, deed, ok, error}. rank = -1 at the top.
static func next_promotion(hero: HeroData) -> Dictionary:
	if hero.guild == &"":
		return {"rank": -1, "ok": false, "error": "Join a guild to be registered as a hero"}
	var r := hero.tier + 1
	if r > DataGuilds.MAX_RANK:
		return {"rank": -1, "ok": false, "error": "There is no tier above Class SSS"}
	var t := DataGuilds.tier(r)
	var out := {"rank": r, "fee": int(t.fee), "level": int(t.level), "flag": String(t.flag), "deed": String(t.deed), "ok": false, "error": ""}
	var missing := missing_requirements(hero, r)
	out.deed = requirements_text(hero, r)
	out["requirements"] = missing
	if not missing.is_empty():
		out.error = "Class %s needs %s" % [t.letter, missing[0]]
	elif hero.inventory.gold < int(t.fee):
		out.error = "The Class %s registration costs %d gold" % [t.letter, t.fee]
	else:
		out.ok = true
	return out

## Count distinct victories, so farming one easy boss never earns a high rank.
static func achievements(hero: HeroData) -> Dictionary:
	var dungeons := 0
	var hardest := 0
	for id in DataDungeons.order():
		if DataDungeons.boss_gone(hero, id):
			dungeons += 1
			hardest = maxi(hardest, DataDungeons.tier(id))
	var champions := 0
	for id in hero.miniboss_log:
		if int(hero.miniboss_log[id].get("kills", 0)) > 0:
			champions += 1
	return {"jobs": maxi(0, int(hero.guild_jobs.get("done", 0))), "dungeons": dungeons, "champions": champions, "dungeon_tier": hardest}

static func missing_requirements(hero: HeroData, rank: int) -> PackedStringArray:
	var out := PackedStringArray()
	var t := DataGuilds.tier(rank)
	if hero.progress.level < int(t.level):
		out.append("level %d (%d / %d)" % [t.level, hero.progress.level, t.level])
	# Promotions remain cumulative, including when validating a legacy save.
	for r in range(2, rank + 1):
		var previous := DataGuilds.tier(r)
		if String(previous.flag) != "" and not bool(hero.world_flags.get(StringName(previous.flag), false)):
			var line := "a proven deed: %s" % previous.deed
			if not out.has(line):
				out.append(line)
	if rank >= 2:
		for flag in OPENING_DEEDS:
			if not bool(hero.world_flags.get(flag, false)):
				out.append("the opening story errands")
				break
	var a := achievements(hero)
	for k in ["jobs", "champions", "dungeons", "dungeon_tier"]:
		if int(a[k]) < int(t.get(k, 0)):
			out.append("%s (%d / %d)" % [_achievement_name(k), a[k], t[k]])
	return out

static func _achievement_name(key: String) -> String:
	return {"jobs": "guild jobs handed in", "champions": "different champions defeated", "dungeons": "different dungeons cleared", "dungeon_tier": "highest dungeon tier cleared"}.get(key, key)

static func requirements_text(hero: HeroData, rank: int) -> String:
	var t := DataGuilds.tier(rank)
	var a := achievements(hero)
	var lines := PackedStringArray()
	for r in range(2, rank + 1):
		var previous := DataGuilds.tier(r)
		if String(previous.flag) != "":
			var line := "%s: %s" % [previous.deed, "done" if bool(hero.world_flags.get(StringName(previous.flag), false)) else "needed"]
			if not lines.has(line):
				lines.append(line)
	for k in ["jobs", "champions", "dungeons", "dungeon_tier"]:
		if int(t.get(k, 0)) > 0:
			lines.append("%s: %d / %d" % [_achievement_name(k).capitalize(), a[k], t[k]])
	return "; ".join(lines)

## Reassess old level-and-gold ranks once. Refund removed promotion fees;
## never remove equipment, items, experience or recorded victories.
static func migrate_legacy_rank(hero: HeroData) -> void:
	if hero.guild == &"" or hero.tier <= 1:
		return
	var earned := 1
	for r in range(2, hero.tier + 1):
		if not missing_requirements(hero, r).is_empty():
			break
		earned = r
	for r in range(earned + 1, hero.tier + 1):
		hero.inventory.gold += 150 if r == 2 else int(DataGuilds.tier(r).fee)
	hero.tier = earned
	hero.equipment.tier_rank = earned

static func promote(hero: HeroData) -> String:
	var p := next_promotion(hero)
	if not p.ok:
		return String(p.error)
	hero.inventory.gold -= int(p.fee)
	hero.set_tier(int(p.rank))
	var checking := hero._checking_promotions
	hero._checking_promotions = true
	hero.inventory.changed.emit()
	hero._checking_promotions = checking
	return ""

## Persistent stat modifiers from the Accord tier bonus, the guild's perks (scale with tier rank) and — for a guild of a
## hero's own or a fellow hero's (bh-027) — its guild passives.
static func modifiers(hero: HeroData) -> Array:
	var out := []
	var g := GuildRegistry.info(hero, hero.guild)
	if not g.is_empty() and not (g.passives as Dictionary).is_empty():
		out.append_array(OwnGuild.passive_modifiers(g.passives, String(g.short)))
	var r := hero.tier
	if r <= 0:
		return out
	var src := "Class %s" % DataGuilds.letter(r)
	out.append(StatModifier.inc(&"max_hp", DataGuilds.ACCORD_HP * r, src))
	out.append(StatModifier.inc(&"damage", DataGuilds.ACCORD_DAMAGE * r, src))
	for p in g.get("perks", []):
		var v := float(p[2]) * r
		out.append(StatModifier.flat(StringName(p[0]), v, g.short) if String(p[1]) == "flat" else StatModifier.inc(StringName(p[0]), v, g.short))
	return out

## bh-027: the ranks of the hero's guild's passives ({} for the old and the rolled guilds).
static func passive_ranks(hero: HeroData) -> Dictionary:
	var g := GuildRegistry.info(hero, hero.guild) if hero else {}
	return g.get("passives", {}) if not g.is_empty() else {}

## bh-027: Guild War modifiers for `comrades` members of the hero's guild fighting beside them.
static func war_modifiers(hero: HeroData, comrades: int) -> Array:
	return OwnGuild.war_modifiers(passive_ranks(hero), comrades)

## How a guild is recognised between players: the same key on two heroes means the same guild.
static func guild_key(hero: HeroData) -> String:
	if hero == null or hero.guild == &"":
		return ""
	if hero.guild == GuildRegistry.OWN:
		return OwnGuild.key(hero)
	if hero.guild == GuildRegistry.REMOTE:
		return String(hero.remote_guild.get("key", ""))
	if DataGuilds.GUILDS.has(hero.guild):
		return "canon/%s" % hero.guild
	return ""                              # a rolled guild lives in one hero's world only

## Guild members fighting beside `player` right now: Call to Arms fighters and, in multiplayer, fellow players of the
## same guild on this map, within DataGuildPassives.WAR_RANGE.
static func comrades(player: Node3D, hero: HeroData) -> int:
	if player == null or hero == null or hero.guild == &"":
		return 0
	var n := 0
	var r2 := DataGuildPassives.WAR_RANGE * DataGuildPassives.WAR_RANGE
	for f in GuildSummons.fighters(player.get_tree()):
		if (f as Actor).alive and (f as Node3D).global_position.distance_squared_to(player.global_position) < r2:
			n += 1
	var key := guild_key(hero)
	if key != "" and Net.is_active():
		for av in player.get_tree().get_nodes_in_group(&"net_hero"):
			var a := av as NetAvatar
			if a and a.alive and String(Net.peers.get(a.owner_peer, {}).get("guild", {}).get("key", "")) == key \
					and a.global_position.distance_squared_to(player.global_position) < r2:
				n += 1
	return n

static func has_war_passives(hero: HeroData) -> bool:
	var ranks := passive_ranks(hero)
	for k in ranks:
		if int(ranks[k]) > 0 and String(DataGuildPassives.passive(StringName(k)).get("kind", "")) == "war":
			return true
	return false

## Leave the guild (not one the hero leads: that is disbanded). The tier stays the hero's.
static func leave(hero: HeroData) -> String:
	if hero == null or hero.guild == &"":
		return "You are not in a guild"
	if OwnGuild.is_master(hero):
		return "You lead %s: disband it instead" % hero.own_guild.name
	var was := display_name(hero)
	if hero.guild == GuildRegistry.REMOTE:
		Net.guild_left(String(hero.remote_guild.get("master", "")))
	hero.guild = &""
	hero.remote_guild = {}
	hero.guild_alias = ""
	hero.stats_dirty.emit()
	Events.notify.emit("You left %s." % was, &"info")
	Events.guild_changed.emit()
	Events.guild_customised.emit()
	return ""

static func _g(hero: HeroData) -> Dictionary:
	return GuildRegistry.info(hero, hero.guild) if hero else {}

static func shop_discount(hero: HeroData, shop_id: StringName) -> float:
	if hero == null:
		return 0.0
	return float(_g(hero).get("shop_discount", {}).get(shop_id, 0.0))

static func inn_discount(hero: HeroData) -> float:
	return float(_g(hero).get("inn_discount", 0.0)) if hero else 0.0

static func elite_gold_bonus(hero: HeroData) -> float:
	return float(_g(hero).get("elite_gold", 0.0)) if hero else 0.0

static func potion_healing_bonus(hero: HeroData) -> float:
	return float(_g(hero).get("potion_healing", 0.0)) if hero else 0.0

# ---- bh-017: the hero's own guild name and banner ------------------------------------------------------------------

const ALIAS_MAX := 32
const BANNER_W := 240
const BANNER_H := 360
const BANNER_MAX_BYTES := 400000

static var _banner_tex: ImageTexture
static var _banner_key := 0

## A guild name as typed: no control characters or brackets (the UI renders rich text in places), one space between
## words, at most ALIAS_MAX characters.
static func clean_alias(text: String) -> String:
	var out := ""
	var last_space := true
	for i in text.length():
		var c := text.unicode_at(i)
		if c < 32 or c == 127 or c == 91 or c == 93:
			continue
		if c == 32:
			if last_space:
				continue
			last_space = true
		else:
			last_space = false
		out += String.chr(c)
		if out.length() >= ALIAS_MAX:
			break
	return out.strip_edges()

## Any registered hero may rename their guild and fly their own banner, any number of times (bh-027: not another
## player's guild — its Guildmaster names it).
static func can_customise(hero: HeroData) -> bool:
	return hero != null and hero.guild != &"" and hero.guild != GuildRegistry.REMOTE

## What the hero calls their guild: their own name if they gave one, else the guild's.
static func display_name(hero: HeroData) -> String:
	if hero == null or hero.guild == &"":
		return "No guild"
	if hero.guild == GuildRegistry.OWN or hero.guild == GuildRegistry.REMOTE:
		return String(GuildRegistry.info(hero, hero.guild).get("name", "Guild"))
	if hero.guild_alias != "":
		return hero.guild_alias
	return String(GuildRegistry.info(hero, hero.guild).get("name", "Guild"))

## "" on success, else why not. An empty name goes back to the guild's own.
static func set_alias(hero: HeroData, text: String) -> String:
	if not can_customise(hero):
		return "Join a guild first"
	if hero.guild == GuildRegistry.OWN:
		return OwnGuild.rename(hero, text) if clean_alias(text) != "" else ""
	var clean := clean_alias(text)
	if clean == hero.guild_alias:
		return ""
	hero.guild_alias = clean
	Events.guild_customised.emit()
	return ""

## The stored banner: the picture cropped to 2:3, scaled to BANNER_W x BANNER_H and saved as a JPEG. Empty when `img`
## is unusable.
static func banner_bytes_from_image(img: Image) -> PackedByteArray:
	if img == null or img.is_empty() or img.get_width() < 8 or img.get_height() < 8:
		return PackedByteArray()
	var src := img.duplicate() as Image
	if src.is_compressed():
		src.decompress()
	src.convert(Image.FORMAT_RGBA8)
	var w := src.get_width()
	var h := src.get_height()
	var want := float(BANNER_W) / float(BANNER_H)
	var cw := w
	var ch := h
	if float(w) / float(h) > want:
		cw = maxi(8, int(round(float(h) * want)))
	else:
		ch = maxi(8, int(round(float(w) / want)))
	var crop := src.get_region(Rect2i((w - cw) / 2, (h - ch) / 2, cw, ch))
	crop.resize(BANNER_W, BANNER_H, Image.INTERPOLATE_LANCZOS)
	var flat := Image.create(BANNER_W, BANNER_H, false, Image.FORMAT_RGBA8)
	flat.fill(Color(0.08, 0.06, 0.05, 1.0))
	flat.blend_rect(crop, Rect2i(0, 0, BANNER_W, BANNER_H), Vector2i.ZERO)
	flat.convert(Image.FORMAT_RGB8)
	var bytes := flat.save_jpg_to_buffer(0.88)
	return bytes if bytes.size() <= BANNER_MAX_BYTES else flat.save_jpg_to_buffer(0.6)

## "" on success, else why not.
static func set_banner(hero: HeroData, img: Image) -> String:
	if not can_customise(hero):
		return "Join a guild first"
	var bytes := banner_bytes_from_image(img)
	if bytes.is_empty():
		return "That picture could not be used"
	hero.guild_banner = bytes
	Events.guild_customised.emit()
	return ""

static func clear_banner(hero: HeroData) -> void:
	if hero != null and not hero.guild_banner.is_empty():
		hero.guild_banner = PackedByteArray()
		Events.guild_customised.emit()

## Save-file side: base64 text -> the JPEG bytes, or empty when it is missing, oversized or not a picture.
static func load_banner_bytes(b64: String) -> PackedByteArray:
	if b64 == "" or b64.length() > BANNER_MAX_BYTES * 2:
		return PackedByteArray()
	var bytes := Marshalls.base64_to_raw(b64)
	if bytes.is_empty() or bytes.size() > BANNER_MAX_BYTES:
		return PackedByteArray()
	var probe := Image.new()
	return bytes if probe.load_jpg_from_buffer(bytes) == OK else PackedByteArray()

## The hero's uploaded banner as a texture (cached), or null when they have none.
static func banner_texture(hero: HeroData) -> Texture2D:
	if hero == null or hero.guild_banner.is_empty():
		return null
	var k := hash(hero.guild_banner)
	if _banner_tex != null and _banner_key == k:
		return _banner_tex
	var img := Image.new()
	if img.load_jpg_from_buffer(hero.guild_banner) != OK:
		return null
	_banner_tex = ImageTexture.create_from_image(img)
	_banner_key = k
	return _banner_tex

## The banner to fly for the hero: the uploaded picture, else the guild's own banner art (null without a guild).
static func banner_or_default(hero: HeroData) -> Texture2D:
	if hero != null and hero.guild != &"":
		return GuildRegistry.banner(hero, hero.guild)
	return banner_texture(hero)

const OPENING_DEEDS := [&"mq_maelis_orders", &"south_gate_open", &"mq_shard_taken", &"mq_three_told"]

## No guild is chosen for the player. The opening story earns Class E even
## without membership; registered heroes qualify for D at level 2 instead.
static func auto_promote(hero: HeroData) -> int:
	var before := hero.tier
	if hero.tier == 0 and hero.progress.level >= 2 and OPENING_DEEDS.all(func(flag): return bool(hero.world_flags.get(flag, false))):
		hero.set_tier(1)
	while bool(next_promotion(hero).ok):
		if promote(hero) != "":
			break
	return hero.tier - before
