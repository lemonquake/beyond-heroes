class_name ProfilePicture
## bh-030: a hero's own profile picture. Any PNG / JPG / WebP / BMP / TGA the player picks is cropped to a square, scaled
## to SIZE and kept as a JPEG in the save (HeroData.profile_pic). It replaces the class portrait on the HUD, the
## Character window and the hero cards; in multiplayer it travels once per player and per change (Net, like guild
## banners), so everyone sees everyone's picture on the party frames and the player menu.

const SIZE := 192
const MAX_BYTES := 160000

static var _cache := {}             # hash of the bytes -> ImageTexture

## The stored picture: the centre square of `img`, SIZE x SIZE, as a JPEG. Empty when `img` is unusable.
static func bytes_from_image(img: Image) -> PackedByteArray:
	if img == null or img.is_empty():
		return PackedByteArray()
	var sq := img.duplicate() as Image
	if sq.is_compressed():
		sq.decompress()
	var side := mini(sq.get_width(), sq.get_height())
	sq = sq.get_region(Rect2i((sq.get_width() - side) / 2, (sq.get_height() - side) / 2, side, side))
	sq.convert(Image.FORMAT_RGBA8)
	sq.resize(SIZE, SIZE, Image.INTERPOLATE_LANCZOS)
	var flat := Image.create(SIZE, SIZE, false, Image.FORMAT_RGBA8)
	flat.fill(Color(0.08, 0.06, 0.05))
	flat.blend_rect(sq, Rect2i(0, 0, SIZE, SIZE), Vector2i.ZERO)
	var bytes := flat.save_jpg_to_buffer(0.9)
	return bytes if bytes.size() <= MAX_BYTES else flat.save_jpg_to_buffer(0.6)

## Set the hero's picture ("" on success). Shares it with the party right away.
static func set_picture(hero: HeroData, img: Image) -> String:
	if hero == null:
		return "No hero."
	var bytes := bytes_from_image(img)
	if bytes.is_empty():
		return "That picture could not be used."
	hero.profile_pic = bytes
	_changed(hero)
	return ""

static func clear(hero: HeroData) -> void:
	if hero != null and not hero.profile_pic.is_empty():
		hero.profile_pic = PackedByteArray()
		_changed(hero)

static func _changed(hero: HeroData) -> void:
	Events.profile_picture_changed.emit(0)
	if hero == Game.hero and Net.is_active():
		Net.send_profile_picture_all()

## Save-file side: base64 -> JPEG bytes, or empty when missing, oversized or not a picture.
static func load_bytes(b64: String) -> PackedByteArray:
	if b64 == "" or b64.length() > MAX_BYTES * 2:
		return PackedByteArray()
	var bytes := Marshalls.base64_to_raw(b64)
	return bytes if valid(bytes) else PackedByteArray()

static func valid(bytes: PackedByteArray) -> bool:
	if bytes.is_empty() or bytes.size() > MAX_BYTES:
		return false
	var probe := Image.new()
	return probe.load_jpg_from_buffer(bytes) == OK

## A texture of picture bytes (cached), or null.
static func texture_of(bytes: PackedByteArray) -> Texture2D:
	if bytes.is_empty():
		return null
	var k := hash(bytes)
	if _cache.has(k):
		return _cache[k]
	var img := Image.new()
	if img.load_jpg_from_buffer(bytes) != OK:
		return null
	var tex := ImageTexture.create_from_image(img)
	if _cache.size() > 64:
		_cache.clear()
	_cache[k] = tex
	return tex

## The hero's face on screen: their own picture, else the ID shot of their model (bh-031), else the class portrait.
static func portrait(hero: HeroData) -> Texture2D:
	if hero == null:
		return null
	var t := texture_of(shown_bytes(hero))
	return t if t != null else UIArt.portrait(String(hero.cls.id))

## The picture this hero shows (and shares in multiplayer): the profile picture, else the ID picture.
static func shown_bytes(hero: HeroData) -> PackedByteArray:
	if hero == null:
		return PackedByteArray()
	return hero.profile_pic if not hero.profile_pic.is_empty() else hero.id_pic

## A save's (or a server character's) picture from its hero Dictionary: profile picture, else ID picture.
static func bytes_of_save(hero: Dictionary) -> PackedByteArray:
	var b := load_bytes(String(hero.get("profile_pic", "")))
	return b if not b.is_empty() else load_bytes(String(hero.get("id_pic", hero.get("pic", ""))))

## Another player's face: the picture they shared, or their class portrait.
static func peer_portrait(peer: int, cls: String) -> Texture2D:
	var t := texture_of(Net.profile_pictures.get(peer, PackedByteArray()))
	return t if t != null else UIArt.portrait(cls)
