class_name GuildRules
## Joining a guild, transfers, tier promotion, and every bonus a guild or tier grants. Pure rules over HeroData
## (no nodes): registrars' dialogue actions, the UI and the tests all call these.

## "" when the hero may join `gid` now, otherwise the reason.
static func join_error(hero: HeroData, gid: StringName) -> String:
	if not DataGuilds.GUILDS.has(gid):
		return "Unknown guild"
	if hero.guild == gid:
		return "You already carry the %s's seal" % DataGuilds.guild(gid).short
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
	if hero.tier < 1:
		hero.set_tier(1)
	else:
		hero.stats_dirty.emit()
	Events.guild_joined.emit(gid, first)
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
	if hero.progress.level < int(t.level):
		out.error = "Class %s needs level %d" % [t.letter, t.level]
	elif String(t.flag) != "" and not bool(hero.world_flags.get(StringName(t.flag), false)):
		out.error = "Class %s needs a proven deed: %s" % [t.letter, t.deed]
	elif hero.inventory.gold < int(t.fee):
		out.error = "The Class %s registration costs %d gold" % [t.letter, t.fee]
	else:
		out.ok = true
	return out

static func promote(hero: HeroData) -> String:
	var p := next_promotion(hero)
	if not p.ok:
		return String(p.error)
	hero.inventory.gold -= int(p.fee)
	hero.inventory.changed.emit()
	hero.set_tier(int(p.rank))
	return ""

## Persistent stat modifiers from the Accord tier bonus and the guild's perks (scale with tier rank).
static func modifiers(hero: HeroData) -> Array:
	var out := []
	var r := hero.tier
	if r <= 0:
		return out
	var src := "Class %s" % DataGuilds.letter(r)
	out.append(StatModifier.inc(&"max_hp", DataGuilds.ACCORD_HP * r, src))
	out.append(StatModifier.inc(&"damage", DataGuilds.ACCORD_DAMAGE * r, src))
	var g := DataGuilds.guild(hero.guild)
	for p in g.get("perks", []):
		out.append(StatModifier.inc(p[0], float(p[1]) * r, g.short))
	return out

static func shop_discount(hero: HeroData, shop_id: StringName) -> float:
	if hero == null:
		return 0.0
	return float(DataGuilds.guild(hero.guild).get("shop_discount", {}).get(shop_id, 0.0))

static func inn_discount(hero: HeroData) -> float:
	return float(DataGuilds.guild(hero.guild).get("inn_discount", 0.0)) if hero else 0.0

static func elite_gold_bonus(hero: HeroData) -> float:
	return float(DataGuilds.guild(hero.guild).get("elite_gold", 0.0)) if hero else 0.0

static func potion_healing_bonus(hero: HeroData) -> float:
	return float(DataGuilds.guild(hero.guild).get("potion_healing", 0.0)) if hero else 0.0
