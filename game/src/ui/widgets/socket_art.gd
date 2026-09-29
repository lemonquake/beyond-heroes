class_name SocketArt
## bh-022: how sockets look on item cells, equipment slots and tooltips. Each socket is a bronze bezel
## (assets/ui/slots/socket_empty.png) or the bezel holding its crystal (socket_<family>_<grade>.png, drawn by
## tools/ui_art/bh022_sockets.py); a piece with crystals set also glows in their blended colour (CrystalNames).

const EMPTY := "slots/socket_empty.png"
const GEM := "slots/socket_%s_%d.png"
const PER_ROW := 4

static var _glow: Texture2D

static func socket_tex(gem_id: String) -> Texture2D:
	if gem_id == "":
		return UIArt.tex(EMPTY)
	var id := StringName(gem_id)
	var f := DataCrystals.family_of(id)
	if f == &"":
		return UIArt.tex(EMPTY)
	return UIArt.tex(GEM % [f, clampi(DataCrystals.grade_of(id), 0, 3)])

## A soft round glow, white; tinted by the caller.
static func glow_tex() -> Texture2D:
	if _glow == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 0.85))
		g.set_color(1, Color(1, 1, 1, 0.0))
		g.add_point(0.45, Color(1, 1, 1, 0.4))
		var t := GradientTexture2D.new()
		t.gradient = g
		t.fill = GradientTexture2D.FILL_RADIAL
		t.fill_from = Vector2(0.5, 0.5)
		t.fill_to = Vector2(1.0, 0.5)
		t.width = 96
		t.height = 96
		_glow = t
	return _glow

## The infusion glow behind an item's icon (nothing when no crystal is set). `t` = seconds, for the slow pulse.
static func draw_infusion(ci: CanvasItem, it: ItemInstance, r: Rect2, t: float, alpha := 1.0) -> void:
	if it == null or it.sockets <= 0:
		return
	var p := CrystalNames.power(it.gems)
	if p <= 0:
		return
	var c := CrystalNames.color_for(it.gems)
	var strength := clampf(0.35 + 0.05 * float(p), 0.35, 0.8)
	var pulse := 0.8 + 0.2 * sin(t * 1.6)
	ci.draw_texture_rect(glow_tex(), r.grow(r.size.x * 0.06), false, Color(c, strength * pulse * alpha))

## The sockets of `it` along the bottom of the cell rect `r` (rows of PER_ROW, bottom row full first).
static func draw_sockets(ci: CanvasItem, it: ItemInstance, r: Rect2, alpha := 1.0) -> void:
	if it == null or it.sockets <= 0:
		return
	var n := it.gems.size()
	var s := r.size.x * 0.21
	var rows := ceili(float(n) / PER_ROW)
	var i := 0
	for row in rows:
		var in_row := mini(PER_ROW, n - row * PER_ROW)
		var w := s * in_row - s * 0.12 * (in_row - 1)
		var x0 := r.position.x + (r.size.x - w) * 0.5
		var y := r.end.y - s * (1.0 + row * 0.9) - r.size.y * 0.07
		for k in in_row:
			var tex := socket_tex(String(it.gems[i]))
			if tex:
				ci.draw_texture_rect(tex, Rect2(Vector2(x0 + k * s * 0.88, y), Vector2(s, s)), false, Color(1, 1, 1, alpha))
			i += 1

## A row of sockets for the tooltip (one per socket, `px` each).
class Strip:
	extends Control
	var item: ItemInstance
	var px := 30.0

	func _init(it: ItemInstance, size_px := 30.0) -> void:
		item = it
		px = size_px
		custom_minimum_size = Vector2(px * maxi(1, it.gems.size()) + 4.0 * (it.gems.size() - 1), px)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		for k in item.gems.size():
			var tex := SocketArt.socket_tex(String(item.gems[k]))
			if tex:
				draw_texture_rect(tex, Rect2(Vector2(k * (px + 4.0), 0), Vector2(px, px)), false)
