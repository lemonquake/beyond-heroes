class_name LootLabels
extends Control
## Name tags over items lying on the ground (bh-007; the LootDrop comment always promised them): rarity-coloured text
## on a dark tag, stacked so neighbours never overlap, nearest first. Shown always (Settings.loot_labels_always) or
## while the Show Loot key is held. Hovering a tag highlights it and sets Game.hover_loot, so a click picks the item up
## (Player handles the click). Gold piles are collected on contact and get no tag.

const MAX_TAGS := 40
const RANGE := 26.0
const PAD := Vector2(8, 3)

var _tags: Array = []          # [{drop, rect: Rect2, text, color}]
var _font: Font
var _fs := 16

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	_font = UITheme.body_bold()

func _shown() -> bool:
	return Settings.loot_labels_always or Input.is_action_pressed(&"show_loot")

func _process(_d: float) -> void:
	_tags.clear()
	var p := Game.player as Node3D
	var cam := get_viewport().get_camera_3d()
	if not _shown() or p == null or not is_instance_valid(p) or cam == null:
		if Game.hover_loot != null and not is_instance_valid(Game.hover_loot):
			Game.hover_loot = null
		queue_redraw()
		return
	var drops := []
	for n in get_tree().get_nodes_in_group(&"loot"):
		var d := n as LootDrop
		if d == null or d.item == null or not d.landed or d.is_queued_for_deletion():
			continue
		var dist := d.global_position.distance_to(p.global_position)
		if dist > RANGE or cam.is_position_behind(d.global_position):
			continue
		drops.append([dist, d])
	drops.sort_custom(func(a, b): return a[0] < b[0])
	var taken: Array[Rect2] = []
	var vp := get_viewport_rect().size
	var scale_ui := size.x / maxf(1.0, vp.x) if size.x > 0.0 else 1.0
	for e in drops.slice(0, MAX_TAGS):
		var d: LootDrop = e[1]
		var sp := cam.unproject_position(d.global_position + Vector3.UP * 0.55) * scale_ui
		var text := d.label_text()
		var tw := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, _fs).x
		var r := Rect2(sp - Vector2(tw * 0.5 + PAD.x, _fs + PAD.y * 2.0), Vector2(tw + PAD.x * 2.0, _fs + PAD.y * 2.0 + 2.0))
		# push up until it no longer overlaps a nearer tag
		for i in 12:
			var hit := false
			for t in taken:
				if t.grow(1.0).intersects(r):
					r.position.y = t.position.y - r.size.y - 2.0
					hit = true
			if not hit:
				break
		if r.end.y < 0.0 or r.position.y > size.y or r.end.x < 0.0 or r.position.x > size.x:
			continue
		# never under the HUD's own panels: the minimap / stage / objective column and the bottom bar
		if r.intersects(Rect2(size.x - 340.0, 0.0, 340.0, 560.0)) or r.intersects(Rect2(250.0, size.y - 150.0, size.x - 500.0, 150.0)):
			continue
		taken.append(r)
		_tags.append({"drop": d, "rect": r, "text": text, "color": d.color()})
	# hover: the tag under the mouse becomes the click target
	var m := get_local_mouse_position()
	var hover: LootDrop = null
	for t in _tags:
		if (t.rect as Rect2).has_point(m):
			hover = t.drop
	if hover != Game.hover_loot and (hover != null or Game.hover_loot is LootDrop):
		Game.hover_loot = hover
	queue_redraw()

func _draw() -> void:
	for t in _tags:
		var r: Rect2 = t.rect
		var hovered: bool = Game.hover_loot == t.drop
		var c: Color = t.color
		draw_rect(r, Color(0.02, 0.02, 0.025, 0.86 if not hovered else 0.95))
		draw_rect(r, Color(c.r, c.g, c.b, 0.9 if hovered else 0.45), false, 1.5 if hovered else 1.0)
		var base := Vector2(r.position.x + PAD.x, r.position.y + PAD.y + _fs - 2.0)
		draw_string(_font, base, String(t.text), HORIZONTAL_ALIGNMENT_LEFT, -1, _fs, c.lightened(0.15) if hovered else c)
