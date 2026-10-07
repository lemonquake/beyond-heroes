class_name UIWindow
extends Control
## A framed game window: painted panel, ornate title banner with crest, close button, open/close animation.
## Subclasses build their content into `body` in _build() and refresh it in refresh() (called on open).
## Windows are anchored to the screen centre and sized in logical 1920x1080 units, so they scale with the viewport.

signal closed

var title := ""
var window_size := Vector2(1100, 720)
var modal := false                 # darkens the world and blocks gameplay input while open
var body: VBoxContainer
var _frame: PanelContainer
var _root: Control
var _title_label: Label
var _dim: ColorRect
var _tw: Tween
var _built := false
var _outer: VBoxContainer

## How far the content asks to reach past the window (0, 0 = it fits). Tests and the UI capture sweep read it.
func overflow() -> Vector2:
	if _outer == null or _outer.get_parent() == null:
		return Vector2.ZERO
	var room := (_outer.get_parent() as Control).size
	var want := _outer.get_combined_minimum_size()
	return Vector2(maxf(0.0, want.x - room.x), maxf(0.0, want.y - room.y))

func _init(p_title := "", p_size := Vector2(1100, 720)) -> void:
	title = p_title
	window_size = p_size
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false

func _ready() -> void:
	if not _built:
		_make_frame()
		_build()
		_built = true

func _make_frame() -> void:
	_dim = ColorRect.new()
	_dim.color = Color(0, 0, 0, 0.45)
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP if modal else Control.MOUSE_FILTER_IGNORE
	_dim.visible = modal
	add_child(_dim)
	# _root is centred on screen; it holds the frame and the overlay (banner, crest, close) and is what animates
	_root = Control.new()
	_root.anchor_left = 0.5
	_root.anchor_right = 0.5
	_root.anchor_top = 0.5
	_root.anchor_bottom = 0.5
	_root.offset_left = -window_size.x * 0.5
	_root.offset_right = window_size.x * 0.5
	_root.offset_top = -window_size.y * 0.5
	_root.offset_bottom = window_size.y * 0.5
	_root.pivot_offset = window_size * 0.5
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_frame = PanelContainer.new()
	_frame.position = Vector2.ZERO
	_frame.size = window_size
	_frame.custom_minimum_size = window_size
	_frame.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.add_child(_frame)
	# bh-041: the content sits in a clipping holder, so it can never stretch the frame past its size (an over-long row of
	# tabs once pushed the Skills window's right half off the screen); each window still lays its content out to fit
	var holder := Control.new()
	holder.clip_contents = true
	holder.mouse_filter = Control.MOUSE_FILTER_PASS
	_frame.add_child(holder)
	_outer = VBoxContainer.new()
	var outer := _outer
	outer.add_theme_constant_override("separation", 6)
	holder.add_child(outer)
	outer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 22)
	outer.add_child(spacer)
	body = VBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 10)
	outer.add_child(body)
	# title banner straddling the top edge
	var bw := clampf(title.length() * 20.0 + 260.0, 420.0, window_size.x - 120.0)
	var banner := PanelContainer.new()
	banner.theme_type_variation = &"HeaderPanel"
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	banner.position = Vector2((window_size.x - bw) * 0.5, -34)
	banner.size = Vector2(bw, 64)
	banner.custom_minimum_size = Vector2(bw, 64)
	_root.add_child(banner)
	_title_label = UITheme.title(title, 26, UITheme.GOLD)
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	banner.add_child(_title_label)
	var crest := UIArt.image("frames/panel_header_crest.png")
	if crest.texture:
		var cs := crest.custom_minimum_size
		crest.position = Vector2((window_size.x - cs.x) * 0.5, -34 - cs.y * 0.62)
		crest.size = cs
		_root.add_child(crest)
	var close := TextureButton.new()
	close.texture_normal = UIArt.tex("frames/close_x.png")
	close.texture_hover = UIArt.tex("frames/close_x_hover.png")
	close.ignore_texture_size = true
	close.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	var cs2 := 56.0 if Settings.touch_mode else 36.0     # a thumb needs a bigger target
	close.custom_minimum_size = Vector2(cs2, cs2)
	close.size = Vector2(cs2, cs2)
	close.position = Vector2(window_size.x - 24 - cs2, 16 - (cs2 - 36.0) * 0.5)
	close.pressed.connect(close_window)
	_root.add_child(close)

func set_title(t: String) -> void:
	title = t
	if _title_label:
		_title_label.text = t

## Override: build the window's content into `body`.
func _build() -> void:
	pass

## Override: refresh content from the current game state.
func refresh() -> void:
	pass

func is_open() -> bool:
	return visible

func open() -> void:
	if not _built:
		_make_frame()
		_build()
		_built = true
	visible = true
	refresh()
	Audio.play_ui(&"ui_open")
	if _tw:
		_tw.kill()
	var fit := fit_scale()
	_root.scale = Vector2(0.96, 0.96) * fit
	_root.modulate.a = 0.0
	_tw = create_tween().set_parallel(true)
	_tw.tween_property(_root, "scale", Vector2.ONE * fit, 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_tw.tween_property(_root, "modulate:a", 1.0, 0.1)

func close_window() -> void:
	if not visible:
		return
	TooltipLayer.hide_for(null)
	Audio.play_ui(&"ui_close")
	if _tw:
		_tw.kill()
	_tw = create_tween().set_parallel(true)
	_tw.tween_property(_root, "scale", Vector2(0.97, 0.97) * fit_scale(), 0.08)
	_tw.tween_property(_root, "modulate:a", 0.0, 0.08)
	_tw.chain().tween_callback(func() -> void:
		visible = false
		closed.emit())

## Windows are laid out at a fixed logical size; on a small canvas (a phone with a larger Interface Scale) the whole
## window shrinks to fit, title banner and crest included, instead of running off the screen.
func fit_scale() -> float:
	var vp := get_viewport_rect().size
	if vp.x <= 0.0:
		return 1.0
	return minf(1.0, minf((vp.x - 24.0) / window_size.x, (vp.y - 80.0) / (window_size.y + 40.0)))

func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED and _root and visible and (_tw == null or not _tw.is_running()):
		_root.scale = Vector2.ONE * fit_scale()

func toggle() -> void:
	if visible:
		close_window()
	else:
		open()

# ---- small layout helpers for subclasses ----

static func hbox(sep := 10) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h

static func vbox(sep := 8) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v

static func inset(min_size := Vector2.ZERO) -> PanelContainer:
	var p := PanelContainer.new()
	p.theme_type_variation = &"InsetPanel"
	p.custom_minimum_size = min_size
	return p

static func section(text: String) -> Control:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	var l := UITheme.title(text, 20, UITheme.GOLD)
	v.add_child(l)
	var s := HSeparator.new()
	v.add_child(s)
	return v

static func button(text: String, cb: Callable, variation := &"", min_w := 0.0) -> Button:
	var b := Button.new()
	b.text = text
	if variation != &"":
		b.theme_type_variation = variation
	if min_w > 0.0:
		b.custom_minimum_size.x = min_w
	b.focus_mode = Control.FOCUS_ALL
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		cb.call())
	b.mouse_entered.connect(func() -> void: Audio.play_ui(&"ui_hover"))
	return b

static func icon_button(icon_id: String, tip: String, cb: Callable, size_px := 34.0) -> Button:
	var b := Button.new()
	b.theme_type_variation = &"IconButton"
	b.icon = UIArt.ui_icon(icon_id)
	b.expand_icon = true
	b.custom_minimum_size = Vector2(size_px + 18.0, size_px + 10.0)
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.add_theme_color_override("icon_normal_color", UITheme.PARCHMENT)
	b.add_theme_color_override("icon_hover_color", UITheme.GOLD)
	if tip != "":
		TooltipLayer.attach(b, func() -> Control: return Tips.text(tip))
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		cb.call())
	return b
