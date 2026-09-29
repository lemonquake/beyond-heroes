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

## Any registered hero may rename their guild and fly their own banner, any number of times.
static func can_customise(hero: HeroData) -> bool:
	return hero != null and hero.guild != &""

## What the hero calls their guild: their own name if they gave one, else the guild's.
static func display_name(hero: HeroData) -> String:
	if hero == null or hero.guild == &"":
		return "No guild"
	if hero.guild_alias != "":
		return hero.guild_alias
	return String(DataGuilds.guild(hero.guild).get("name", "Guild"))

## "" on success, else why not. An empty name goes back to the guild's own.
static func set_alias(hero: HeroData, text: String) -> String:
	if not can_customise(hero):
		return "Join a guild first"
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
	var t := banner_texture(hero)
	if t != null:
		return t
	if hero != null and hero.guild != &"":
		return UIArt.tex(String(DataGuilds.guild(hero.guild).banner))
	return null
