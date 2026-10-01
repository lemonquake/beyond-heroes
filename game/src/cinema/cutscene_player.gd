class_name CutscenePlayer
extends CanvasLayer
## bh-021: plays a Cutscene. It owns the letterbox, subtitles, captions, legend cards, fades and the skip controls, and
## two worlds a scene can stage itself in:
##   map        the live map, seen through a cutscene camera placed relative to an anchor transform (use_map)
##   flashback  a separate World3D inside a full-screen SubViewport (use_flashback) — a past place with its own
##              environment, built once per cutscene by a builder callable and reused by every flashback scene
## Gameplay stops while it runs (input blocked, HUD hidden, the hero cannot be hurt); in single player the world keeps
## running (towns are safe), so NPCs and effects stay alive.
##
## Skipping: Space / Enter / a tap on "Skip scene" ends the current scene (never within 0.35 s of its start); Esc or
## "Skip all" ends the cutscene — only when the Cutscene allows it. The Cutscene's finish() always runs once.
##
##   CutscenePlayer.play(&"the_three", func(): ...)

signal finished(id: StringName)

const BAR := 0.11                 # letterbox bar height (fraction of the screen)
const SKIP_GUARD := 0.35
const SCENE_FADE := 0.35

static var active: CutscenePlayer

var cutscene: Cutscene
var scenes: Array = []
var index := -1
var t := 0.0
var length := 0.0
var skipped_scenes := 0
var time_scale := 1.0             # tests fast-forward
var world := "map"
var anchor := Transform3D.IDENTITY
var actors := {}                  # key -> CutsceneActor (per world; cleared when the world changes)
var cam: Camera3D
var _on_done: Callable
var _events: Array = []           # [time, Callable]
var _lines: Array = []            # [start, end, speaker, text, color]
var _cam_keys: Array = []         # [time, pos (global), look (global), fov]
var _shakes: Array = []           # [start, end, amp]
var _scene_nodes: Array = []
var _tweens: Array = []
var _cards: Array = []
var _done := false
var _started := false
var _fade_t := 0.0
var _fade_tw: Tween
var _flash_tw: Tween
var _cap_tw: Tween
var _saved := {}
var _frozen: Array = []
var _hidden: Array = []
var _labels: Array = []           # [Node3D, was_visible]: world text kept out of the shot
var _prev_cam: Camera3D
# worlds
var _map_set: Node3D
var _map_cam: Camera3D
var _fb_box: SubViewportContainer
var _fb_vp: SubViewport
var _fb_root: Node3D
var _fb_cam: Camera3D
var _fb_key := ""
# ui
var _ui: Control
var _top: ColorRect
var _bottom: ColorRect
var _fade: ColorRect
var _vignette: TextureRect
var _flash: ColorRect
var _sub_name: Label
var _sub_text: Label
var _caption: Label
var _caption_sub: Label
var _skip_btn: Button
var _skip_all_btn: Button
var _progress: Label

static func play(id: StringName, on_done := Callable(), parent: Node = null) -> CutscenePlayer:
	var c := DataCutscenes.make(id)
	if c == null:
		push_warning("Unknown cutscene %s" % id)
		if on_done.is_valid():
			on_done.call()
		return null
	return play_cutscene(c, on_done, parent)

static func play_cutscene(c: Cutscene, on_done := Callable(), parent: Node = null) -> CutscenePlayer:
	if active and is_instance_valid(active):
		active._finish()
	var p := CutscenePlayer.new()
	p.cutscene = c
	p._on_done = on_done
	var host: Node = parent
	if host == null:
		host = Game.ui_root if Game.ui_root and is_instance_valid(Game.ui_root) else Game.get_tree().root
	host.add_child(p)
	active = p
	return p

static func is_playing() -> bool:
	return active != null and is_instance_valid(active) and not active._done

func _init() -> void:
	layer = 40
	process_mode = Node.PROCESS_MODE_ALWAYS
	process_priority = 1000         # after every plate and sign has decided to show itself: _hide_labels wins

func _ready() -> void:
	_build_ui()
	_take_over()
	scenes = cutscene.build(self)
	if cutscene.music != &"":
		Music.push(&"cutscene", cutscene.music, 1.5)
	_next_scene(false)
	_started = true

func _exit_tree() -> void:
	Music.pop(&"cutscene")           # however the player ends, the map gets its music back

# ---------------------------------------------------------------------------------------------------------------- ui

func _build_ui() -> void:
	_ui = Control.new()
	_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ui.mouse_filter = Control.MOUSE_FILTER_STOP     # the world never gets a click while a cutscene plays
	add_child(_ui)
	_fb_box = SubViewportContainer.new()
	_fb_box.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fb_box.stretch = true
	_fb_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fb_box.visible = false
	_ui.add_child(_fb_box)
	_vignette = TextureRect.new()
	var vg := Gradient.new()
	vg.set_color(0, Color(0, 0, 0, 0))
	vg.add_point(0.55, Color(0, 0, 0, 0.1))
	vg.set_color(vg.get_point_count() - 1, Color(0.03, 0.0, 0.0, 0.82))
	var vt := GradientTexture2D.new()
	vt.gradient = vg
	vt.fill = GradientTexture2D.FILL_RADIAL
	vt.fill_from = Vector2(0.5, 0.5)
	vt.fill_to = Vector2(1.05, 0.5)
	vt.width = 256
	vt.height = 256
	_vignette.texture = vt
	_vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_vignette.stretch_mode = TextureRect.STRETCH_SCALE
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vignette.modulate.a = 0.0
	_ui.add_child(_vignette)
	_fade = _rect(Color(0, 0, 0, 1))
	_flash = _rect(Color(1, 1, 1, 0))
	_top = ColorRect.new()
	_top.color = Color.BLACK
	_top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_top)
	_bottom = ColorRect.new()
	_bottom.color = Color.BLACK
	_bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_bottom)
	_sub_name = UITheme.label("", 22, UITheme.GOLD, UITheme.title_font())
	_sub_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub_name.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_sub_name)
	_sub_text = UITheme.label("", 27, UITheme.PARCHMENT, UITheme.body_font())
	_sub_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_sub_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for l in [_sub_name, _sub_text]:
		(l as Label).add_theme_constant_override("outline_size", 8)
		(l as Label).add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_ui.add_child(_sub_text)
	_caption = UITheme.label("", 54, UITheme.PARCHMENT, UITheme.title_font())
	_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_caption.modulate.a = 0.0
	_ui.add_child(_caption)
	_caption_sub = UITheme.label("", 26, UITheme.TEXT_DIM, UITheme.body_font())
	_caption_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caption_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_caption_sub.modulate.a = 0.0
	_ui.add_child(_caption_sub)
	_skip_btn = _button("Skip scene  ›", func() -> void: skip_scene())
	_skip_all_btn = _button("Skip all  »", func() -> void: skip_all())
	_skip_all_btn.visible = cutscene.skip_all
	_progress = UITheme.label("", 16, UITheme.TEXT_MUTED, UITheme.body_font())
	_progress.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(_progress)
	_layout()
	get_viewport().size_changed.connect(_layout)

func _rect(c: Color) -> ColorRect:
	var r := ColorRect.new()
	r.color = c
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(r)
	return r

func _button(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_override("font", UITheme.body_bold())
	b.add_theme_font_size_override("font_size", 18)
	b.add_theme_color_override("font_color", UITheme.PARCHMENT)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.08, 0.07, 0.06, 0.7)
	sb.border_color = Color(UITheme.GOLD, 0.55)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	b.add_theme_stylebox_override("normal", sb)
	var sh := sb.duplicate() as StyleBoxFlat
	sh.bg_color = Color(0.2, 0.16, 0.1, 0.85)
	b.add_theme_stylebox_override("hover", sh)
	b.add_theme_stylebox_override("pressed", sh)
	b.pressed.connect(cb)
	_ui.add_child(b)
	return b

func _layout() -> void:
	var vs := get_viewport().get_visible_rect().size
	var bh := vs.y * BAR
	_top.position = Vector2.ZERO
	_top.size = Vector2(vs.x, bh)
	_bottom.position = Vector2(0, vs.y - bh)
	_bottom.size = Vector2(vs.x, bh)
	var w := minf(vs.x * 0.72, 1300.0)
	_sub_name.position = Vector2((vs.x - w) * 0.5, vs.y - bh - 118)
	_sub_name.size = Vector2(w, 30)
	_sub_text.position = Vector2((vs.x - w) * 0.5, vs.y - bh - 88)
	_sub_text.size = Vector2(w, 80)
	_caption.position = Vector2(0, vs.y * 0.42)
	_caption.size = Vector2(vs.x, 70)
	_caption_sub.position = Vector2(0, vs.y * 0.42 + 76)
	_caption_sub.size = Vector2(vs.x, 40)
	var bsz := _skip_btn.get_combined_minimum_size()
	_skip_btn.position = Vector2(vs.x - bsz.x - 28, vs.y - bh * 0.5 - bsz.y * 0.5)
	if _skip_all_btn.visible:
		var asz := _skip_all_btn.get_combined_minimum_size()
		_skip_all_btn.position = Vector2(_skip_btn.position.x - asz.x - 12, _skip_btn.position.y)
	_progress.position = Vector2(28, vs.y - bh * 0.5 - 11)

# ---------------------------------------------------------------------------------------------------------------- takeover

func _take_over() -> void:
	_saved = {"blocking": Game.ui_blocking, "god": Game.god_mode}
	Game.ui_blocking = true
	Game.god_mode = true
	Game.in_cutscene = true
	var ui := Game.ui_root
	if ui and is_instance_valid(ui):
		if ui.has_method(&"close_all"):
			ui.close_all()
		for n in ["hud", "chat", "touch"]:
			var c = ui.get(n)
			if c is CanvasItem:
				_saved["vis_" + n] = (c as CanvasItem).visible
				(c as CanvasItem).visible = false
	var vp := get_viewport()
	_prev_cam = vp.get_camera_3d() if vp else null
	# the world holds its breath: monsters stop where they stand until the cutscene hands the screen back
	_frozen.clear()
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e is Node and (e as Node).process_mode != Node.PROCESS_MODE_DISABLED:
			_frozen.append([e, (e as Node).process_mode])
			(e as Node).process_mode = Node.PROCESS_MODE_DISABLED
	_collect_labels(Game.current_map)
	Events.cutscene_started.emit(cutscene.id)

## Name plates, signposts and station labels would float in the middle of a shot: hide them while the cutscene runs.
func _collect_labels(root: Node) -> void:
	if root == null or not is_instance_valid(root):
		return
	for n in root.find_children("*", "Label3D", true, false):
		_labels.append([n, (n as Node3D).visible])
	for n in root.find_children("*", "Sprite3D", true, false):
		_labels.append([n, (n as Node3D).visible])
	for n in root.find_children("*", "LegendPlate", true, false):
		_labels.append([n, (n as Node3D).visible])

func _hide_labels() -> void:
	for l in _labels:
		if is_instance_valid(l[0]):
			(l[0] as Node3D).visible = false

func _restore() -> void:
	for l in _labels:
		if is_instance_valid(l[0]):
			(l[0] as Node3D).visible = bool(l[1])
	_labels.clear()
	for n in _hidden:
		if is_instance_valid(n):
			(n as Node3D).visible = true
	_hidden.clear()
	for f in _frozen:
		if is_instance_valid(f[0]):
			(f[0] as Node).process_mode = f[1]
	_frozen.clear()
	Game.ui_blocking = bool(_saved.get("blocking", false))
	Game.god_mode = bool(_saved.get("god", false))
	Game.in_cutscene = false
	var ui := Game.ui_root
	if ui and is_instance_valid(ui):
		for n in ["hud", "chat", "touch"]:
			var c = ui.get(n)
			if c is CanvasItem and _saved.has("vis_" + n):
				(c as CanvasItem).visible = bool(_saved["vis_" + n])
	if Game.player and is_instance_valid(Game.player):
		Game.player.visible = true
		var pc = Game.player.get(&"camera")
		if pc is Camera3D and (pc as Camera3D).is_inside_tree():
			(pc as Camera3D).make_current()
	elif _prev_cam and is_instance_valid(_prev_cam) and _prev_cam.is_inside_tree():
		_prev_cam.make_current()
	get_tree().root.disable_3d = false
	Music.pop(&"cutscene", 2.0)

# ---------------------------------------------------------------------------------------------------------------- flow

func _next_scene(with_fade := true) -> void:
	_clear_scene()
	index += 1
	if index >= scenes.size():
		_finish()
		return
	var sc: Dictionary = scenes[index]
	t = 0.0
	length = float(sc.get("length", 5.0))
	_progress.text = "%s   %d / %d" % [cutscene.title, index + 1, scenes.size()]
	var run: Callable = sc.get("run", Callable())
	if run.is_valid():
		run.call(self)
	_apply_camera(0.0)
	# every scene opens out of black unless it asks for a hard cut (or stages its own fades: fade_in 0)
	var fin := float(sc.get("fade_in", 0.6))
	if not bool(sc.get("cut", false)) and fin > 0.0:
		_fade.color.a = 1.0
		fade(0.0, 0.0, fin)
	_fire(0.0)

func _clear_scene() -> void:
	for tw in _tweens:
		if tw and (tw as Tween).is_valid():
			(tw as Tween).kill()
	_tweens.clear()
	_events.clear()
	_lines.clear()
	_cam_keys.clear()
	_shakes.clear()
	for n in _scene_nodes:
		if is_instance_valid(n):
			(n as Node).queue_free()
	_scene_nodes.clear()
	for c in _cards:
		if is_instance_valid(c):
			(c as LegendCard).queue_free()
	_cards.clear()
	_sub_name.text = ""
	_sub_text.text = ""
	for tw in [_cap_tw, _flash_tw]:
		if tw:
			tw.kill()
	_caption.modulate.a = 0.0
	_caption_sub.modulate.a = 0.0
	_flash.color.a = 0.0

## Tests and captures: start at scene `i` (0-based) as if the ones before had been skipped.
func jump_to(i: int) -> void:
	index = clampi(i, 0, scenes.size()) - 1
	_next_scene(false)

func skip_scene() -> void:
	if _done or not _started or t < SKIP_GUARD:
		return
	skipped_scenes += 1
	_next_scene(true)

func skip_all() -> void:
	if _done or not cutscene.skip_all:
		return
	_finish()

func _finish() -> void:
	if _done:
		return
	_done = true
	_clear_scene()
	cutscene.finish(self)
	for k in actors.keys():
		drop(k)
	if _map_set and is_instance_valid(_map_set):
		_map_set.queue_free()
	if _map_cam and is_instance_valid(_map_cam):
		_map_cam.queue_free()
	if _fb_vp and is_instance_valid(_fb_vp):
		_fb_box.queue_free()
	_restore()
	if active == self:
		active = null
	Events.cutscene_finished.emit(cutscene.id)
	finished.emit(cutscene.id)
	if _on_done.is_valid():
		_on_done.call()
	queue_free()

func _process(delta: float) -> void:
	if _done or index < 0 or index >= scenes.size():
		return
	var d := delta * time_scale
	_hide_labels()
	t += d
	_fire(t)
	_apply_camera(d)
	_apply_lines()
	if t >= length:
		_next_scene(true)

func _fire(now: float) -> void:
	while not _events.is_empty() and float(_events[0][0]) <= now:
		var e: Array = _events.pop_front()
		(e[1] as Callable).call()
		if _done or _events.is_empty() and index >= scenes.size():
			return

func _input(e: InputEvent) -> void:
	if _done:
		return
	if e is InputEventKey and e.pressed and not e.echo:
		match (e as InputEventKey).keycode:
			KEY_SPACE, KEY_ENTER, KEY_KP_ENTER:
				skip_scene()
			KEY_ESCAPE:
				if cutscene.skip_all:
					skip_all()
				else:
					skip_scene()
		get_viewport().set_input_as_handled()
	elif e is InputEventJoypadButton and e.pressed:
		skip_scene()
		get_viewport().set_input_as_handled()

# ---------------------------------------------------------------------------------------------------------------- worlds

## Stage the scene in the live map; local coordinates are relative to `at` (e.g. Paul David's post).
func use_map(at := Transform3D.IDENTITY) -> void:
	if world != "map":
		_clear_actors()
	world = "map"
	anchor = at
	_fb_box.visible = false
	get_tree().root.disable_3d = false
	var map: Node = Game.current_map if Game.current_map and is_instance_valid(Game.current_map) else self
	if _map_set == null or not is_instance_valid(_map_set):
		_map_set = Node3D.new()
		_map_set.name = "CutsceneSet"
		_map_set.process_mode = Node.PROCESS_MODE_ALWAYS
		map.add_child(_map_set)
		_map_cam = Camera3D.new()
		_map_cam.name = "CutsceneCamera"
		_map_cam.fov = 45.0
		_map_cam.far = 400.0
		_map_set.add_child(_map_cam)
	_map_cam.make_current()
	cam = _map_cam

## Stage the scene in the flashback world. `key` names the set: the builder runs once per key (the same set is reused
## by consecutive scenes). builder(root: Node3D) adds the environment, lights and scenery.
func use_flashback(key: String, builder: Callable, at := Transform3D.IDENTITY) -> void:
	if world != "flashback" or key != _fb_key:
		_clear_actors()
	world = "flashback"
	anchor = at
	if _fb_vp == null or key != _fb_key:
		if _fb_vp:
			_fb_vp.queue_free()
		_fb_vp = SubViewport.new()
		_fb_vp.own_world_3d = true
		_fb_vp.world_3d = World3D.new()
		_fb_vp.msaa_3d = get_viewport().msaa_3d
		_fb_vp.screen_space_aa = get_viewport().screen_space_aa
		_fb_vp.scaling_3d_scale = get_viewport().scaling_3d_scale
		_fb_vp.audio_listener_enable_3d = false
		_fb_vp.process_mode = Node.PROCESS_MODE_ALWAYS
		_fb_box.add_child(_fb_vp)
		_fb_root = Node3D.new()
		_fb_root.name = "Flashback_" + key
		_fb_vp.add_child(_fb_root)
		_fb_cam = Camera3D.new()
		_fb_cam.fov = 45.0
		_fb_cam.far = 500.0
		_fb_root.add_child(_fb_cam)
		_fb_key = key
		if builder.is_valid():
			builder.call(_fb_root)
		_collect_labels(_fb_root)
	_fb_box.visible = true
	_fb_cam.make_current()
	cam = _fb_cam
	get_tree().root.disable_3d = true

func stage() -> Node3D:
	return _fb_root if world == "flashback" else _map_set

func _clear_actors() -> void:
	for k in actors.keys():
		drop(k)

## Local (anchor) -> global.
func g(p: Vector3) -> Vector3:
	var base := stage().global_transform if world == "flashback" and stage() else Transform3D.IDENTITY
	return base * (anchor * p)

# ---------------------------------------------------------------------------------------------------------------- actors

## A persistent actor (kept across scenes in the same world until dropped). pos is local; yaw in degrees (local).
func actor(key: StringName, model: String, scale := 1.0, pos := Vector3.ZERO, yaw := 0.0) -> CutsceneActor:
	var a: CutsceneActor = actors.get(key)
	if a == null or not is_instance_valid(a):
		a = CutsceneActor.make(model, scale)
		stage().add_child(a)
		actors[key] = a
	place(a, pos, yaw)
	return a

## A legend (DataLegends id) with its weapon in hand.
func legend(key: StringName, id: StringName, pos := Vector3.ZERO, yaw := 0.0, armed := true) -> CutsceneActor:
	var L := DataLegends.legend(id)
	var fresh: bool = not actors.has(key) or not is_instance_valid(actors[key])
	var a := actor(key, String(L.get("model", id)), float(L.get("scale", 1.0)), pos, yaw)
	if fresh and armed and String(L.get("weapon", "")) != "":
		a.attach(&"main", String(L.weapon))
		if id == &"paul_david":
			a.hide_surfaces("BH_Hilt")
	return a

## The hero as they look right now (the player's model, tint and weapons).
func hero(key: StringName = &"hero", pos := Vector3.ZERO, yaw := 0.0) -> CutsceneActor:
	return copy(key, Game.player, pos, yaw)

## An actor that looks exactly like a live character (the player, an NPC): same model, tint and weapons.
func copy(key: StringName, who: Node, pos := Vector3.ZERO, yaw := 0.0) -> CutsceneActor:
	var p := who
	var app := {}
	if p and is_instance_valid(p) and p.get(&"visual") and "appearance" in p.get(&"visual"):
		app = (p.get(&"visual") as CharacterVisual).appearance
	var path := String(app.get("model", "res://assets/characters/knight.glb"))
	var fresh: bool = not actors.has(key) or not is_instance_valid(actors[key])
	var a: CutsceneActor = actors.get(key)
	if fresh:
		var vis = p.get(&"visual") if p and is_instance_valid(p) else null
		if vis is CharacterVisual and (vis as CharacterVisual).hero != null:
			# bh-029: the hero's body with their look and worn gear, not the bare base model
			var eq: Equipment = null
			if p.get(&"hero") is HeroData:
				eq = (p.get(&"hero") as HeroData).equipment
			elif p.get(&"equipment") is Equipment:
				eq = p.get(&"equipment")
			var lk: Dictionary = (vis as CharacterVisual).hero.look if (vis as CharacterVisual).hero.look is Dictionary else {}
			a = CutsceneActor.make_hero(app, lk, eq)
		else:
			a = CutsceneActor.make(path, float(app.get("scale", 1.0)), app.get("tint", Color.WHITE))
		stage().add_child(a)
		actors[key] = a
		var wp: Dictionary = app.get("weapons", {})
		for hand in wp:
			var pair: Array = wp[hand]
			a.attach(StringName(hand), String(pair[0]), "weapon.R" if hand == &"main" else "weapon.L", pair[1])
	place(a, pos, yaw)
	return a

func place(a: Node3D, pos: Vector3, yaw := 0.0) -> void:
	var tr := anchor * Transform3D(Basis(Vector3.UP, deg_to_rad(yaw)), pos)
	if world == "flashback":
		a.transform = tr
	else:
		a.global_transform = tr

func drop(key: StringName) -> void:
	var a = actors.get(key)
	if a and is_instance_valid(a):
		(a as Node).queue_free()
	actors.erase(key)

## Add an effect node for this scene only (freed when the scene ends). pos is local unless `global` is set.
func fx(n: Node3D, pos := Vector3.ZERO, parent: Node3D = null) -> Node3D:
	n.process_mode = Node.PROCESS_MODE_ALWAYS
	(parent if parent else stage()).add_child(n)
	if parent == null:
		place(n, pos)
	else:
		n.position = pos
	_scene_nodes.append(n)
	return n

## A tween owned by the current scene: killed when the scene ends or is skipped, so nothing keeps moving into the
## next scene. Bind it to the node it animates.
func tween(bind: Node = null) -> Tween:
	var tw := create_tween()
	if bind:
		tw.bind_node(bind)
	tw.set_speed_scale(time_scale)
	_tweens.append(tw)
	return tw

## Parent an effect to an actor (or a bone follower) for this scene only.
func attach_fx(parent: Node3D, n: Node3D, pos := Vector3.ZERO) -> Node3D:
	parent.add_child(n)
	n.position = pos
	_scene_nodes.append(n)
	return n

## Move an actor from a to b (local) over `dur` seconds starting at `at` (ease out).
func move(a: Node3D, at: float, to: Vector3, dur: float, yaw := INF) -> void:
	self.at(at, func() -> void:
		if not is_instance_valid(a):
			return
		var goal := anchor * to
		var tw := tween(a)
		var prop := "position" if world == "flashback" else "global_position"
		tw.tween_property(a, prop, goal, dur).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		if yaw != INF:
			a.rotation.y = (anchor.basis * Basis(Vector3.UP, deg_to_rad(yaw))).get_euler().y)

# ---------------------------------------------------------------------------------------------------------------- timeline

func at(time: float, fn: Callable) -> void:
	# keep the list sorted: events may be added while a scene runs (a strike schedules its own flash)
	var i := _events.size()
	while i > 0 and float(_events[i - 1][0]) > time:
		i -= 1
	_events.insert(i, [time, fn])

## Hide a node of the live world (the NPC or hero an actor stands in for) until the cutscene ends.
func hide_node(n: Node3D) -> void:
	if n and is_instance_valid(n) and n.visible:
		_hidden.append(n)
		n.visible = false

## The NPC with this id on the current map, if any.
func npc(id: StringName) -> Node3D:
	for n in get_tree().get_nodes_in_group(&"npc"):
		if "def" in n and n.def and n.def.id == id:
			return n as Node3D
	return null

func clip(a: CutsceneActor, time: float, name: StringName, blend := 0.25, speed := 1.0) -> void:
	at(time, func() -> void:
		if is_instance_valid(a):
			a.play(name, blend, speed))

## A subtitle line. dur defaults to reading time (~15 characters a second, at least 2.5 s).
func say(time: float, speaker: String, text: String, dur := -1.0, color := Color(0, 0, 0, 0)) -> void:
	if dur < 0.0:
		dur = maxf(2.5, text.length() / 15.0 + 1.0)
	_lines.append([time, time + dur, speaker, text, color])

## Camera path: keys [[t, pos, look, fov(, cut)], ...] in local coordinates; smooth between keys. A key marked cut
## (5th value true) is a hard cut: the camera holds the previous key until that time, then jumps.
func camera(keys: Array) -> void:
	for k in keys:
		_cam_keys.append([float(k[0]), g(k[1]), g(k[2]), float(k[3]) if k.size() > 3 else 45.0, k.size() > 4 and bool(k[4])])
	_cam_keys.sort_custom(func(a, b): return a[0] < b[0])

func shake(time: float, amp: float, dur: float) -> void:
	_shakes.append([time, time + dur, amp])

func card(time: float, id: StringName, life := 4.6) -> void:
	at(time, func() -> void:
		_cards.append(LegendCard.show_card(_ui, id, life))
		_ui.move_child(_cards[-1], _top.get_index()))

## A centred caption (place and time: "Three winters ago").
func caption(time: float, text: String, sub := "", dur := 3.5) -> void:
	at(time, func() -> void:
		_caption.text = text
		_caption_sub.text = sub
		if _cap_tw:
			_cap_tw.kill()
		var tw := create_tween()
		_cap_tw = tw
		tw.tween_property(_caption, "modulate:a", 1.0, 0.6)
		tw.parallel().tween_property(_caption_sub, "modulate:a", 1.0, 0.9)
		tw.tween_interval(maxf(0.1, dur - 1.4))
		tw.tween_property(_caption, "modulate:a", 0.0, 0.8)
		tw.parallel().tween_property(_caption_sub, "modulate:a", 0.0, 0.8))

func fade(time: float, alpha: float, dur: float, c := Color.BLACK) -> void:
	at(time, func() -> void:
		var from := _fade.color.a
		_fade.color = Color(c.r, c.g, c.b, from)
		if _fade_tw:
			_fade_tw.kill()
		_fade_tw = create_tween()
		_fade_tw.tween_property(_fade, "color:a", alpha, maxf(0.01, dur / time_scale)))

func flash(time: float, c := Color.WHITE, dur := 0.35) -> void:
	at(time, func() -> void:
		_flash.color = Color(c.r, c.g, c.b, 0.9)
		if _flash_tw:
			_flash_tw.kill()
		_flash_tw = create_tween()
		_flash_tw.tween_property(_flash, "color:a", 0.0, maxf(0.01, dur / time_scale)))

## The flashback look: dark, reddened edges.
func vignette(on: bool, dur := 0.8) -> void:
	var tw := create_tween()
	tw.tween_property(_vignette, "modulate:a", 1.0 if on else 0.0, dur)

func sfx(time: float, id: StringName, vol := 0.0) -> void:
	at(time, func() -> void: Audio.play(id, vol, 0.04))

# ---------------------------------------------------------------------------------------------------------------- camera

func _apply_camera(_d: float) -> void:
	if cam == null or _cam_keys.is_empty():
		return
	var k0: Array = _cam_keys[0]
	var k1: Array = k0
	for i in _cam_keys.size():
		if float(_cam_keys[i][0]) <= t:
			k0 = _cam_keys[i]
			k1 = _cam_keys[mini(i + 1, _cam_keys.size() - 1)]
	var u := 0.0
	if k1 != k0 and float(k1[0]) > float(k0[0]) and not bool(k1[4]):
		u = clampf((t - float(k0[0])) / (float(k1[0]) - float(k0[0])), 0.0, 1.0)
		u = u * u * (3.0 - 2.0 * u)
	var pos: Vector3 = (k0[1] as Vector3).lerp(k1[1], u)
	var look: Vector3 = (k0[2] as Vector3).lerp(k1[2], u)
	var amp := 0.0
	for s in _shakes:
		if t >= float(s[0]) and t <= float(s[1]):
			amp = maxf(amp, float(s[2]) * (1.0 - (t - float(s[0])) / maxf(0.01, float(s[1]) - float(s[0]))))
	if amp > 0.0:
		pos += Vector3(sin(t * 53.0), sin(t * 47.0 + 1.3), cos(t * 59.0)) * amp * 0.12
	if world == "flashback":
		var inv := stage().global_transform.affine_inverse()
		pos = inv * pos
		look = inv * look
		cam.position = pos
		if pos.distance_to(look) > 0.01:
			cam.look_at(stage().global_transform * look, Vector3.UP)
	else:
		cam.global_position = pos
		if pos.distance_to(look) > 0.01:
			cam.look_at(look, Vector3.UP)
	cam.fov = lerpf(float(k0[3]), float(k1[3]), u)

func _apply_lines() -> void:
	var cur: Array = []
	for l in _lines:
		if t >= float(l[0]) and t < float(l[1]):
			cur = l
	if cur.is_empty():
		_sub_text.modulate.a = move_toward(_sub_text.modulate.a, 0.0, 0.08)
		_sub_name.modulate.a = _sub_text.modulate.a
		return
	if _sub_text.text != String(cur[3]):
		_sub_text.text = String(cur[3])
		_sub_name.text = String(cur[2]).to_upper()
		var c: Color = cur[4]
		_sub_name.add_theme_color_override("font_color", c if c.a > 0.0 else UITheme.GOLD)
		_sub_text.modulate.a = 0.0
	var fade_in := clampf((t - float(cur[0])) / 0.25, 0.0, 1.0)
	var fade_out := clampf((float(cur[1]) - t) / 0.3, 0.0, 1.0)
	_sub_text.modulate.a = minf(fade_in, fade_out)
	_sub_name.modulate.a = _sub_text.modulate.a
