class_name GuildBannerArt
## bh-027: heraldic banners painted in code for guilds without a picture of their own — the rolled guilds of the Guild
## House, a hero's own guild before they upload one, and other players' guilds whose picture has not arrived yet.
## A banner is a field in the guild's colour, a division (chevron, pale, fess, saltire, quarters or plain) in a second
## tint, a gold or silver frame, a pointed foot and a crest. Polygons are filled by scanline spans (Image.fill_rect), so a
## 240 x 360 banner paints in a few milliseconds; textures are cached by their style.

const W := 240
const H := 360

const CRESTS := ["star", "sun", "moon", "cross", "diamond", "tower", "sword", "crown", "shield", "tree", "flame", "key", "anchor", "chevron"]
const DIVISIONS := ["plain", "chevron", "pale", "fess", "saltire", "quarterly", "bend"]
## Guild colours: deep enough for gold to read against.
const FIELDS := [Color(0.55, 0.12, 0.12), Color(0.12, 0.24, 0.55), Color(0.1, 0.38, 0.22), Color(0.36, 0.16, 0.5), Color(0.1, 0.36, 0.42),
	Color(0.5, 0.3, 0.08), Color(0.2, 0.2, 0.24), Color(0.44, 0.08, 0.28), Color(0.16, 0.3, 0.12), Color(0.6, 0.36, 0.1),
	Color(0.08, 0.16, 0.34), Color(0.38, 0.1, 0.06)]
const METALS := [Color(0.93, 0.76, 0.34), Color(0.86, 0.88, 0.92)]

## Emblem words (GuildNames) that have a crest of their own.
const EMBLEM_CRESTS := {"Star": "star", "Sun": "sun", "Moon": "moon", "Tower": "tower", "Blade": "sword", "Spear": "sword",
	"Crown": "crown", "Shield": "shield", "Oak": "tree", "Thorn": "tree", "Rose": "tree", "Flame": "flame", "Key": "key",
	"Anchor": "anchor", "Oar": "anchor", "Tide": "moon", "Arrow": "chevron", "Hammer": "cross", "Compass": "star", "Bell": "shield"}

static var _cache := {}

## A style for a guild name: the crest from its emblem word when it has one, colours and division from `seed`.
static func style_for(guild_name: String, seed: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var crest := ""
	for w in guild_name.replace("-", " ").split(" ", false):
		var k := String(w).trim_suffix("s")
		if EMBLEM_CRESTS.has(String(w)):
			crest = EMBLEM_CRESTS[String(w)]
		elif EMBLEM_CRESTS.has(k):
			crest = EMBLEM_CRESTS[k]
	if crest == "":
		crest = CRESTS[rng.randi_range(0, CRESTS.size() - 1)]
	var field: Color = FIELDS[rng.randi_range(0, FIELDS.size() - 1)]
	return {"field": field.to_html(false), "metal": rng.randi_range(0, 1), "crest": crest,
		"division": DIVISIONS[rng.randi_range(0, DIVISIONS.size() - 1)]}

static func sanitize(st: Variant) -> Dictionary:
	var d: Dictionary = st if st is Dictionary else {}
	var crest := String(d.get("crest", "star"))
	var div := String(d.get("division", "plain"))
	var field := String(d.get("field", "8c1f1f"))
	return {"field": field if Color.html_is_valid(field) else "8c1f1f", "metal": clampi(int(d.get("metal", 0)), 0, 1),
		"crest": crest if CRESTS.has(crest) else "star", "division": div if DIVISIONS.has(div) else "plain"}

static func texture(style: Dictionary) -> Texture2D:
	var st := sanitize(style)
	var key := "%s/%d/%s/%s" % [st.field, st.metal, st.crest, st.division]
	if _cache.has(key):
		return _cache[key]
	var tex := ImageTexture.create_from_image(paint(st))
	_cache[key] = tex
	return tex

static func paint(style: Dictionary) -> Image:
	var st := sanitize(style)
	var field := Color(String(st.field))
	var metal: Color = METALS[int(st.metal)]
	var second := field.darkened(0.45) if field.get_luminance() > 0.25 else field.lightened(0.28)
	var img := Image.create(W, H, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	# the field, lit a little from above
	for y in H:
		img.fill_rect(Rect2i(0, y, W, 1), field.lerp(field.darkened(0.35), float(y) / float(H)))
	_division(img, String(st.division), second, metal)
	# frame
	var fr := 9
	var dark := metal.darkened(0.55)
	for r in [[Rect2i(0, 0, W, fr), metal], [Rect2i(0, 0, fr, H), metal], [Rect2i(W - fr, 0, fr, H), metal],
			[Rect2i(fr, fr, W - 2 * fr, 2), dark], [Rect2i(fr, fr, 2, H - 2 * fr), dark], [Rect2i(W - fr - 2, fr, 2, H - 2 * fr), dark]]:
		img.fill_rect(r[0], r[1])
	# the pointed foot: trimmed in metal, everything below the point cut away
	var notch := 64
	fill_poly(img, [Vector2(0, H - notch - 8), Vector2(W / 2.0, H - 8), Vector2(W, H - notch - 8), Vector2(W, H - notch), Vector2(W / 2.0, H), Vector2(0, H - notch)], metal)
	fill_poly(img, [Vector2(-1, H - notch), Vector2(W / 2.0, H), Vector2(W + 1, H - notch), Vector2(W + 1, H + 2), Vector2(-1, H + 2)], Color(0, 0, 0, 0))
	# crest: a dark shadow first, then the metal
	var c := Vector2(W / 2.0, H * 0.42)
	_crest(img, String(st.crest), c + Vector2(3, 4), 64.0, Color(0, 0, 0, 0.55), Color(0, 0, 0, 0.55))
	_crest(img, String(st.crest), c, 64.0, metal, field)
	return img

static func _division(img: Image, div: String, col: Color, metal: Color) -> void:
	match div:
		"chevron":
			fill_poly(img, [Vector2(0, 250), Vector2(W / 2.0, 150), Vector2(W, 250), Vector2(W, 300), Vector2(W / 2.0, 200), Vector2(0, 300)], col)
		"pale":
			img.fill_rect(Rect2i(W / 2 - 34, 0, 68, H), col)
			img.fill_rect(Rect2i(W / 2 - 38, 0, 4, H), metal.darkened(0.2))
			img.fill_rect(Rect2i(W / 2 + 34, 0, 4, H), metal.darkened(0.2))
		"fess":
			img.fill_rect(Rect2i(0, 110, W, 90), col)
		"saltire":
			fill_poly(img, [Vector2(0, 0), Vector2(30, 0), Vector2(W, 300), Vector2(W - 30, 300)], col)
			fill_poly(img, [Vector2(W, 0), Vector2(W - 30, 0), Vector2(0, 300), Vector2(30, 300)], col)
		"quarterly":
			img.fill_rect(Rect2i(W / 2, 0, W / 2, 150), col)
			img.fill_rect(Rect2i(0, 150, W / 2, H - 150), col)
		"bend":
			fill_poly(img, [Vector2(0, 40), Vector2(40, 0), Vector2(W, 250), Vector2(W, 320)], col)

## Fill a polygon (any simple outline) by scanline spans.
static func fill_poly(img: Image, pts: Array, col: Color) -> void:
	var n := pts.size()
	if n < 3:
		return
	var y0 := H
	var y1 := 0
	for p: Vector2 in pts:
		y0 = mini(y0, int(floor(p.y)))
		y1 = maxi(y1, int(ceil(p.y)))
	y0 = clampi(y0, 0, img.get_height() - 1)
	y1 = clampi(y1, 0, img.get_height() - 1)
	for y in range(y0, y1 + 1):
		var fy := float(y) + 0.5
		var xs: Array[float] = []
		for i in n:
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[(i + 1) % n]
			if (a.y <= fy and b.y > fy) or (b.y <= fy and a.y > fy):
				xs.append(a.x + (fy - a.y) / (b.y - a.y) * (b.x - a.x))
		xs.sort()
		for k in range(0, xs.size() - 1, 2):
			var xa := clampi(int(round(xs[k])), 0, img.get_width())
			var xb := clampi(int(round(xs[k + 1])), 0, img.get_width())
			if xb > xa:
				img.fill_rect(Rect2i(xa, y, xb - xa, 1), col)

static func _circle(img: Image, c: Vector2, r: float, col: Color, seg := 28) -> void:
	var pts := []
	for i in seg:
		var a := TAU * float(i) / float(seg)
		pts.append(c + Vector2(cos(a), sin(a)) * r)
	fill_poly(img, pts, col)

static func _star(c: Vector2, r_out: float, r_in: float, points: int, rot := -PI / 2.0) -> Array:
	var pts := []
	for i in points * 2:
		var a := rot + PI * float(i) / float(points)
		pts.append(c + Vector2(cos(a), sin(a)) * (r_out if i % 2 == 0 else r_in))
	return pts

static func _rect(c: Vector2, half: Vector2) -> Array:
	return [c + Vector2(-half.x, -half.y), c + Vector2(half.x, -half.y), c + Vector2(half.x, half.y), c + Vector2(-half.x, half.y)]

static func _crest(img: Image, kind: String, c: Vector2, s: float, col: Color, field: Color) -> void:
	match kind:
		"star":
			fill_poly(img, _star(c, s, s * 0.42, 5), col)
		"sun":
			fill_poly(img, _star(c, s, s * 0.62, 12), col)
			_circle(img, c, s * 0.5, field)
			_circle(img, c, s * 0.4, col)
		"moon":
			_circle(img, c, s * 0.82, col)
			_circle(img, c + Vector2(s * 0.34, -s * 0.12), s * 0.68, field)
		"cross":
			fill_poly(img, _rect(c, Vector2(s * 0.18, s * 0.9)), col)
			fill_poly(img, _rect(c + Vector2(0, -s * 0.2), Vector2(s * 0.62, s * 0.18)), col)
		"diamond":
			fill_poly(img, [c + Vector2(0, -s), c + Vector2(s * 0.62, 0), c + Vector2(0, s), c + Vector2(-s * 0.62, 0)], col)
			fill_poly(img, [c + Vector2(0, -s * 0.5), c + Vector2(s * 0.3, 0), c + Vector2(0, s * 0.5), c + Vector2(-s * 0.3, 0)], field)
		"tower":
			fill_poly(img, _rect(c + Vector2(0, s * 0.2), Vector2(s * 0.42, s * 0.72)), col)
			for dx in [-0.42, -0.14, 0.14, 0.42]:
				fill_poly(img, _rect(c + Vector2(s * dx, -s * 0.6), Vector2(s * 0.09, s * 0.14)), col)
			fill_poly(img, [c + Vector2(-s * 0.14, s * 0.92), c + Vector2(-s * 0.14, s * 0.5), c + Vector2(0, s * 0.36),
				c + Vector2(s * 0.14, s * 0.5), c + Vector2(s * 0.14, s * 0.92)], field)
		"sword":
			fill_poly(img, [c + Vector2(-s * 0.1, s * 0.4), c + Vector2(-s * 0.1, -s * 0.7), c + Vector2(0, -s * 1.0), c + Vector2(s * 0.1, -s * 0.7), c + Vector2(s * 0.1, s * 0.4)], col)
			fill_poly(img, _rect(c + Vector2(0, s * 0.45), Vector2(s * 0.46, s * 0.07)), col)
			fill_poly(img, _rect(c + Vector2(0, s * 0.68), Vector2(s * 0.07, s * 0.2)), col)
			_circle(img, c + Vector2(0, s * 0.94), s * 0.11, col, 14)
		"crown":
			fill_poly(img, [c + Vector2(-s * 0.7, s * 0.4), c + Vector2(-s * 0.7, -s * 0.5), c + Vector2(-s * 0.35, -s * 0.05), c + Vector2(0, -s * 0.7),
				c + Vector2(s * 0.35, -s * 0.05), c + Vector2(s * 0.7, -s * 0.5), c + Vector2(s * 0.7, s * 0.4)], col)
			fill_poly(img, _rect(c + Vector2(0, s * 0.55), Vector2(s * 0.7, s * 0.1)), col)
			for dx in [-0.7, 0.0, 0.7]:
				_circle(img, c + Vector2(s * dx, -s * (0.7 if dx == 0.0 else 0.5) - s * 0.1), s * 0.1, col, 12)
		"shield":
			fill_poly(img, [c + Vector2(-s * 0.62, -s * 0.72), c + Vector2(s * 0.62, -s * 0.72), c + Vector2(s * 0.62, s * 0.05), c + Vector2(0, s * 0.9), c + Vector2(-s * 0.62, s * 0.05)], col)
			fill_poly(img, [c + Vector2(-s * 0.46, -s * 0.56), c + Vector2(s * 0.46, -s * 0.56), c + Vector2(s * 0.46, s * 0.02), c + Vector2(0, s * 0.68), c + Vector2(-s * 0.46, s * 0.02)], field)
			fill_poly(img, _rect(c + Vector2(0, -s * 0.05), Vector2(s * 0.08, s * 0.5)), col)
			fill_poly(img, _rect(c + Vector2(0, -s * 0.2), Vector2(s * 0.36, s * 0.08)), col)
		"tree":
			for k in 3:
				var y := -s * 0.85 + float(k) * s * 0.42
				var w := s * (0.38 + 0.2 * float(k))
				fill_poly(img, [c + Vector2(0, y), c + Vector2(w, y + s * 0.55), c + Vector2(-w, y + s * 0.55)], col)
			fill_poly(img, _rect(c + Vector2(0, s * 0.72), Vector2(s * 0.1, s * 0.2)), col)
		"flame":
			fill_poly(img, [c + Vector2(0, -s), c + Vector2(s * 0.28, -s * 0.45), c + Vector2(s * 0.2, -s * 0.62), c + Vector2(s * 0.58, s * 0.05),
				c + Vector2(s * 0.5, s * 0.55), c + Vector2(0, s * 0.85), c + Vector2(-s * 0.5, s * 0.55), c + Vector2(-s * 0.58, s * 0.05),
				c + Vector2(-s * 0.3, -s * 0.3), c + Vector2(-s * 0.2, -s * 0.1)], col)
			fill_poly(img, [c + Vector2(0, -s * 0.2), c + Vector2(s * 0.26, s * 0.3), c + Vector2(0, s * 0.62), c + Vector2(-s * 0.26, s * 0.3)], field)
		"key":
			_circle(img, c + Vector2(0, -s * 0.55), s * 0.34, col)
			_circle(img, c + Vector2(0, -s * 0.55), s * 0.16, field)
			fill_poly(img, _rect(c + Vector2(0, s * 0.25), Vector2(s * 0.08, s * 0.56)), col)
			fill_poly(img, _rect(c + Vector2(s * 0.16, s * 0.62), Vector2(s * 0.14, s * 0.07)), col)
			fill_poly(img, _rect(c + Vector2(s * 0.12, s * 0.38), Vector2(s * 0.1, s * 0.06)), col)
		"anchor":
			_circle(img, c + Vector2(0, -s * 0.78), s * 0.16, col)
			_circle(img, c + Vector2(0, -s * 0.78), s * 0.07, field)
			fill_poly(img, _rect(c + Vector2(0, 0.0), Vector2(s * 0.08, s * 0.66)), col)
			fill_poly(img, _rect(c + Vector2(0, -s * 0.42), Vector2(s * 0.44, s * 0.07)), col)
			var arc := []
			for i in 13:
				var a := PI * float(i) / 12.0
				arc.append(c + Vector2(cos(a) * s * 0.66, sin(a) * s * 0.42 + s * 0.28))
			for i in range(12, -1, -1):
				var a := PI * float(i) / 12.0
				arc.append(c + Vector2(cos(a) * s * 0.5, sin(a) * s * 0.28 + s * 0.28))
			fill_poly(img, arc, col)
		_:  # chevron
			fill_poly(img, [c + Vector2(-s * 0.8, s * 0.5), c + Vector2(0, -s * 0.6), c + Vector2(s * 0.8, s * 0.5), c + Vector2(s * 0.5, s * 0.5),
				c + Vector2(0, -s * 0.15), c + Vector2(-s * 0.5, s * 0.5)], col)
