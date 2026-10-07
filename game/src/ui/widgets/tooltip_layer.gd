class_name TooltipLayer
extends CanvasLayer
## The one tooltip surface. Controls call TooltipLayer.show_for(anchor, builder) on hover and hide_for(anchor) on exit;
## the builder returns the content Control. The tooltip sits beside the anchor (right, else left, else above) and is
## clamped to the screen. Holding Shift while hovering an item keeps the comparison; content can be rebuilt live.

static var instance: TooltipLayer

var _panel: Control
var _anchor: Control
var _builder: Callable
var _fade: Tween
var _gen := 0
const SETTLE_FRAMES := 5
const MIN_SIDE_SCALE := 0.8

func _init() -> void:
	layer = 80
	process_mode = Node.PROCESS_MODE_ALWAYS

func _enter_tree() -> void:
	instance = self

func _exit_tree() -> void:
	if instance == self:
		instance = null

static func show_for(anchor: Control, builder: Callable) -> void:
	if instance:
		instance._show(anchor, builder)

static func hide_for(anchor: Control) -> void:
	if instance and (anchor == null or instance._anchor == anchor):
		instance._clear()

static func refresh() -> void:
	if instance and instance._anchor and is_instance_valid(instance._anchor):
		instance._show(instance._anchor, instance._builder)

func _show(anchor: Control, builder: Callable) -> void:
	_clear()
	if anchor == null or not is_instance_valid(anchor) or not anchor.is_visible_in_tree():
		return
	var content: Control = builder.call()
	if content == null:
		return
	_gen += 1
	_anchor = anchor
	_builder = builder
	_panel = content
	_panel.theme = UITheme.theme()
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for c in _panel.find_children("*", "Control", true, false):
		(c as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_panel)
	_panel.modulate.a = 0.0
	_panel.reset_size()
	_place.call_deferred(_gen)

## bh-042: still the tooltip this placement was started for (hovering from slot to slot quickly started a second
## placement while the first was waiting a frame, and both then worked on the new tooltip: split into columns twice).
func _current(gen: int) -> bool:
	return gen == _gen and _panel != null and is_instance_valid(_panel) and _anchor != null and is_instance_valid(_anchor)

func _place(gen: int) -> void:
	# wrapped labels and rich text know their height only after a layout pass, sometimes two: wait until the size
	# stops changing (bh-042: a long description placed by its first, too-short size ran off the bottom of the screen)
	var last := Vector2(-1, -1)
	for i in SETTLE_FRAMES:
		await get_tree().process_frame
		if not _current(gen):
			return
		_panel.reset_size()
		var ms := _panel.get_combined_minimum_size()
		if ms.is_equal_approx(last):
			break
		last = ms
	_panel.scale = Vector2.ONE
	var vp := _panel.get_viewport_rect().size
	var max_h := vp.y - 16.0
	var max_w := vp.x - 16.0
	# bh-041: a tooltip taller than the screen flows into more columns. bh-042: never wider than the screen — when an
	# item and the piece it would replace do not both fit side by side, the equipped card steps aside (a line says so)
	if _panel.size.y > max_h and fit_columns(_panel, max_h):
		await get_tree().process_frame
		if not _current(gen):
			return
		_panel.reset_size()
	if (_panel.size.x > max_w or _panel.size.x * MIN_SIDE_SCALE > _side_room()) and _drop_comparison():
		await get_tree().process_frame
		if not _current(gen):
			return
		_panel.reset_size()
		if _panel.size.y > max_h and fit_columns(_panel, max_h):
			await get_tree().process_frame
			if not _current(gen):
				return
			_panel.reset_size()
	_reposition()
	if not _panel.resized.is_connected(_reposition):
		_panel.resized.connect(_reposition)
	_fade = _panel.create_tween()
	_fade.tween_property(_panel, "modulate:a", 1.0, 0.08)

## Scale (only as a last resort) and place beside the anchor: right, else left, else above or below; always on screen.
func _reposition() -> void:
	if _panel == null or not is_instance_valid(_panel) or _anchor == null or not is_instance_valid(_anchor):
		return
	var vp := _panel.get_viewport_rect().size
	var s := _panel.size
	var k := minf(1.0, minf((vp.y - 16.0) / maxf(1.0, s.y), (vp.x - 16.0) / maxf(1.0, s.x)))
	# bh-042: rather than lie over the slot it describes, a wide tooltip shrinks a little to fit beside it
	var room := _side_room()
	if s.x * k > room and s.x * MIN_SIDE_SCALE <= room:
		k = minf(k, room / s.x)
	_panel.scale = Vector2(k, k)
	s *= k
	var a := _anchor.get_global_rect()
	var p := Vector2(a.end.x + 10.0, a.position.y)
	if p.x + s.x > vp.x - 8.0:
		p.x = a.position.x - s.x - 10.0
	if p.x < 8.0:
		p = Vector2(clampf(a.get_center().x - s.x * 0.5, 8.0, vp.x - s.x - 8.0), a.position.y - s.y - 10.0)
		if p.y < 8.0:
			p.y = a.end.y + 10.0
	p.x = clampf(p.x, 8.0, maxf(8.0, vp.x - s.x - 8.0))
	p.y = clampf(p.y, 8.0, maxf(8.0, vp.y - s.y - 8.0))
	_panel.position = p.round()

## The widest room beside the anchor (left or right of it), less the gaps.
func _side_room() -> float:
	if _anchor == null or not is_instance_valid(_anchor) or _panel == null:
		return 0.0
	var vp := _panel.get_viewport_rect().size
	var a := _anchor.get_global_rect()
	return maxf(a.position.x - 18.0, vp.x - a.end.x - 18.0)

## The item / equipped pair (Tips.item): keep the item, set the equipped card aside with a line pointing to it.
func _drop_comparison() -> bool:
	if not _panel is HBoxContainer or _panel.get_child_count() < 2:
		return false
	var main := _panel.get_child(0) as PanelContainer
	var eq := _panel.get_child(1) as PanelContainer
	if main == null or eq == null:
		return false
	_panel.remove_child(eq)
	eq.queue_free()
	var v := main.get_child(0) as Container
	if v:
		var note := Tips.lbl("Your equipped piece is not shown: no room beside this one.", 14, UITheme.TEXT_MUTED)
		note.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(note)
	return true

## Split every tooltip card (a TooltipFrame panel holding a column of lines) that is taller than `max_h` into side-by-side
## columns, keeping the reading order. Returns whether anything moved. Also used by windows that show tooltip cards inline.
static func fit_columns(root: Control, max_h: float) -> bool:
	var cards: Array = root.find_children("*", "PanelContainer", true, false)
	if root is PanelContainer:
		cards.push_front(root)
	var moved := false
	for card: PanelContainer in cards:
		if card.theme_type_variation != &"TooltipFrame" or card.get_child_count() == 0 or not card.get_child(0) is VBoxContainer:
			continue
		var v := card.get_child(0) as VBoxContainer
		if card.size.y <= max_h or v.get_child_count() < 4:
			continue
		var limit := max_h - (card.size.y - v.size.y) - 8.0
		var sep := float(v.get_theme_constant("separation"))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 18)
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", int(sep))
		var used := 0.0
		for kid in v.get_children():
			var h := (kid as Control).size.y + sep
			if used + h > limit and col.get_child_count() > 0:
				row.add_child(col)
				col = VBoxContainer.new()
				col.add_theme_constant_override("separation", int(sep))
				used = 0.0
			v.remove_child(kid)
			col.add_child(kid)
			used += h
		row.add_child(col)
		v.add_child(row)
		moved = true
	return moved

func _clear() -> void:
	_gen += 1
	if _panel and is_instance_valid(_panel):
		_panel.queue_free()
	_panel = null
	_anchor = null

func _process(_d: float) -> void:
	if _anchor != null and (not is_instance_valid(_anchor) or not _anchor.is_visible_in_tree()):
		_clear()

## Attach a hover tooltip to any control.
static func attach(c: Control, builder: Callable) -> void:
	c.mouse_entered.connect(func() -> void: TooltipLayer.show_for(c, builder))
	c.mouse_exited.connect(func() -> void: TooltipLayer.hide_for(c))
