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

## Unmet requirements of `rank` as short lines (next_promotion, auto_promote, the registrars). Derived from
## requirement_steps, so the rank tracker and the promotion rules can never disagree.
static func missing_requirements(hero: HeroData, rank: int) -> PackedStringArray:
	var out := PackedStringArray()
	for s in requirement_steps(hero, rank):
		if not s.done and not out.has(String(s.text)):
			out.append(String(s.text))
	return out

## bh-033: every requirement of `rank` as a checklist step (THE rule set; promotions stay cumulative, including when a
## legacy save is validated). Step: {key, label, done, have, need, hint, detail, story, text}.
## `label` is plain and spoiler-free; a story deed's own wording is kept in `detail` (shown on request).
static func requirement_steps(hero: HeroData, rank: int) -> Array:
	var steps := []
	var t := DataGuilds.tier(rank)
	var lvl := hero.progress.level
	steps.append({"key": "level", "label": "Reach level %d" % int(t.level), "done": lvl >= int(t.level), "have": lvl, "need": int(t.level),
		"hint": "Defeat monsters and finish quests.", "detail": "", "story": false, "text": "level %d (%d / %d)" % [t.level, lvl, t.level]})
	var seen := {}
	for r in range(2, rank + 1):
		var previous := DataGuilds.tier(r)
		if String(previous.flag) == "" or seen.has(String(previous.deed)):
			continue
		seen[String(previous.deed)] = true
		var done := bool(hero.world_flags.get(StringName(previous.flag), false))
		steps.append({"key": "deed:%s" % previous.flag, "label": "Continue the main story", "done": done, "have": 1 if done else 0, "need": 1,
			"hint": _story_hint(hero), "detail": String(previous.deed), "story": true, "text": "a proven deed: %s" % previous.deed})
	if rank >= 2:
		var n := OPENING_DEEDS.filter(func(f): return bool(hero.world_flags.get(f, false))).size()
		steps.append({"key": "opening", "label": "Finish the opening errands", "done": n >= OPENING_DEEDS.size(), "have": n, "need": OPENING_DEEDS.size(),
			"hint": _story_hint(hero), "detail": "Maelis, Captain Hald, Sir Aldric and Paul David", "story": true, "text": "the opening story errands"})
	var a := achievements(hero)
	for k in ["jobs", "champions", "dungeons", "dungeon_tier"]:
		var need := int(t.get(k, 0))
		if need > 0:
			var label := String(ACHIEVEMENT_ONE[k]) if need == 1 else String(ACHIEVEMENT_LABELS[k]) % need
			steps.append({"key": k, "label": label, "done": int(a[k]) >= need, "have": int(a[k]), "need": need,
				"hint": String(ACHIEVEMENT_HINTS[k]), "detail": "", "story": false, "text": "%s (%d / %d)" % [_achievement_name(k), a[k], need]})
	return steps

const ACHIEVEMENT_LABELS := {"jobs": "Hand in %d guild jobs", "champions": "Defeat %d different champions",
	"dungeons": "Clear %d different dungeons", "dungeon_tier": "Clear a tier %d dungeon"}
const ACHIEVEMENT_ONE := {"jobs": "Hand in a guild job", "champions": "Defeat a champion", "dungeons": "Clear a dungeon",
	"dungeon_tier": "Clear a tier 1 dungeon"}
const ACHIEVEMENT_HINTS := {"jobs": "Take jobs from your guild's board and hand them in.",
	"champions": "Champions are named elites: Westreach, the Ruined Forest and the Catacombs each hold some.",
	"dungeons": "Defeat a dungeon's lord. The world map's Underground list shows each dungeon.",
	"dungeon_tier": "The Underground list shows each dungeon's tier."}

## The current story step, as the quest tracker shows it (never a later one).
static func _story_hint(hero: HeroData) -> String:
	var o := Objectives.current(hero)
	return String(o.get("step", "")) if not o.is_empty() else ""

## bh-033: the optional next-rank guide (Character screen and HUD tracker). One rank ahead only:
## {state: "max" | "unranked" | "next", rank, title, steps, ready, done, total, next_action, next_hint, note}.
## Promotion is automatic (auto_promote runs on every progress event), so `ready` means it is about to happen.
static func rank_guide(hero: HeroData) -> Dictionary:
	if hero == null:
		return {"state": "max", "steps": []}
	if hero.tier >= DataGuilds.MAX_RANK:
		return {"state": "max", "rank": hero.tier, "title": DataGuilds.tier_name(hero.tier), "steps": [], "ready": false, "done": 0, "total": 0,
			"next_action": "You hold the highest rank.", "next_hint": "", "note": ""}
	var steps := []
	var state := "next"
	var rank := hero.tier + 1
	var note := "Promotion is automatic once every step is done."
	if hero.tier == 0:
		state = "unranked"
		var n := OPENING_DEEDS.filter(func(f): return bool(hero.world_flags.get(f, false))).size()
		steps.append({"key": "level", "label": "Reach level 2", "done": hero.progress.level >= 2, "have": hero.progress.level, "need": 2,
			"hint": "Defeat monsters and finish quests.", "detail": "", "story": false})
		steps.append({"key": "opening", "label": "Finish the opening errands", "done": n >= OPENING_DEEDS.size(), "have": n, "need": OPENING_DEEDS.size(),
			"hint": _story_hint(hero), "detail": "Maelis, Captain Hald, Sir Aldric and Paul David", "story": true})
		note = "Class E is granted automatically after the opening errands. Registering with a guild (%d gold) also ranks you at once." % int(DataGuilds.tier(1).fee)
	else:
		if hero.guild == &"":
			steps.append({"key": "guild", "label": "Register with a guild", "done": false, "have": 0, "need": 1,
				"hint": "Speak with Dax (Swordfin Company) or Lio (Lantern Covenant) in their Malasugue halls.", "detail": "", "story": false})
		steps.append_array(requirement_steps(hero, rank))
		var fee := int(DataGuilds.tier(rank).fee)
		if fee > 0:
			var gold := hero.inventory.gold
			steps.append({"key": "fee", "label": "Carry the %d gold fee" % fee, "done": gold >= fee, "have": gold, "need": fee,
				"hint": "The fee is taken automatically when you are promoted.", "detail": "", "story": false})
	var done := steps.filter(func(s): return s.done).size()
	var first := {}
	for s in steps:
		if not s.done:
			first = s
			break
	return {"state": state, "rank": rank, "title": DataGuilds.tier_name(rank), "steps": steps, "ready": first.is_empty(),
		"done": done, "total": steps.size(), "next_action": String(first.get("label", "Ready to rank up")),
		"next_hint": String(first.get("hint", note)), "note": note}

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
