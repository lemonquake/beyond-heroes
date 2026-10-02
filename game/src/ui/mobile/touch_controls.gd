class_name TouchControls
extends Control
## On-screen controls for touch play (Settings.control_mode == "mobile"). Several fingers at once: this control reads
## the raw screen touches itself (the GUI only ever sees the first finger, as an emulated mouse) and presses the same
## input actions a keyboard would, so the hero code does not know the difference.
##
##   left thumb    movement stick: appears where the thumb lands in the lower left (or stays put, see Settings)
##   right thumb   Attack (hold to keep swinging) ringed by Skills 1-4, an outer ring with Dodge, Skills 5-6, Heavy
##                 and Guard. Tap a skill to cast at the nearest enemy; drag it to aim, release to cast.
##   orbs          tap the HP / Mana orb to use its potion belt slot (a health / mana draught unless changed in the Bag)
##   context       an Interact button appears with the verb ("Talk to Hesta", "Pick up") when something is in reach
##   top right     Bag, Chat, Menu (every window) and Pause; tap the minimap for the world map; in a multiplayer
##                 party also Ping (mark the aimed spot for everyone) and Regroup (clients: back to the host, bh-011)
##   free screen   tap a loot label to pick it up; pinch to zoom the camera

const STICK_RADIUS := 125.0
const STICK_DEADZONE := 0.12
const DRAG_AIM_MIN := 26.0          # px a skill must be dragged before it aims by hand
const DRAG_AIM_FULL := 170.0        # px of drag for the skill's full range
const TAP_TIME := 0.09              # how long a tapped action is held down
const AIM_HOLD := 0.45              # the hand-aimed direction outlives the tap (the skill may wait in the input buffer)

var player: Player
var hud: Hud
var _k := 1.0                        # Settings.touch_size
var _stick_home := Vector2.ZERO
var _stick_base := Vector2.ZERO
var _stick_knob := Vector2.ZERO
var _stick_touch := -99
var _stick_vec := Vector2.ZERO
var _buttons: Array[TouchButton] = []
var _by_id := {}
var _touches := {}                   # touch index -> {btn, start, pos, t0}
var _taps := {}                      # action -> release time
var _aim_touch := -99                # touch dragging a skill
var _aim_clear_at := 0.0
var _pinch_d := -1.0
var _was_active := false
var _interact_text := ""
var _attack_center := Vector2.ZERO
var _layout_size := Vector2.ZERO
var _long := {}                      # windows open: a held first finger becomes a right-click (use, equip, sell, refund)
const LONG_PRESS := 0.5

func _init() -> void:
	name = "TouchControls"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	_make(&"attack", 86.0)
	for i in HeroData.SKILL_BAR_SIZE:
		_make(StringName("skill_%d" % (i + 1)), 52.0)
	_make(&"dodge", 50.0).glyph = "dodge"
	_make(&"roll", 50.0).glyph = "roll"     # always a forward roll: along the stick, or the way the hero faces
	var heavy := _make(&"heavy", 48.0)
	heavy.icon = UIArt.icon("items", "greatsword")
	heavy.caption = ""
	var guard := _make(&"guard", 48.0)
	guard.icon = UIArt.icon("items", "shield")
	var hp := _make(&"potion_health", 60.0)
	hp.style = &"badge"
	hp.hit_scale = 1.0
	var mp := _make(&"potion_mana", 60.0)
	mp.style = &"badge"
	mp.hit_scale = 1.0
	# bh-030: the four quick belt slots, between the orbs
	for q in range(HeroData.ORB_SLOTS, HeroData.BELT_SIZE):
		var qb := _make(HeroData.belt_action(q), 34.0)
		qb.style = &"badge"
		qb.hit_scale = 1.2
	var it := _make(&"interact", 56.0)
	it.icon = UIArt.ui_icon("talk")
	it.accent = UITheme.GOLD
	it.visible = false
	for pair in [[&"bag", "shop"], [&"chat", "talk"], [&"menu", ""], [&"pause", ""]]:
		var b := _make(pair[0], 34.0)
		if pair[1] != "":
			b.icon = UIArt.ui_icon(pair[1])
		else:
			b.glyph = String(pair[0])
		b.hit_scale = 1.25
	var pg := _make(&"ping", 34.0)
	pg.icon = UIArt.ui_icon("warning")
	pg.hit_scale = 1.25
	var rg := _make(&"regroup", 34.0)
	rg.icon = UIArt.ui_icon("teleport")
	rg.hit_scale = 1.25
	var mm := _make(&"minimap", 80.0)
	mm.style = &"area"
	mm.hit_scale = 1.0
	Events.player_spawned.connect(func(p: Node) -> void: player = p as Player)
	Events.interact_prompt.connect(func(t: String) -> void: _interact_text = t)
	Settings.changed.connect(_on_settings)
	get_viewport().size_changed.connect(_layout)
	if Game.player is Player:
		player = Game.player
	_on_settings()

func _make(id: StringName, r: float) -> TouchButton:
	var b := TouchButton.new(id, r)
	b.set_meta(&"base_radius", r)
	add_child(b)
	_buttons.append(b)
	_by_id[id] = b
	return b

func button(id: StringName) -> TouchButton:
	return _by_id.get(id)

func _on_settings() -> void:
	_k = clampf(Settings.touch_size, 0.7, 1.4)
	modulate.a = clampf(Settings.touch_opacity, 0.25, 1.0)
	_layout_size = Vector2.ZERO
	_layout()

# ---- Layout -------------------------------------------------------------------------------------------------------

## Where the controls sit for the current screen. Angles are measured like a clock face turned to maths (0° = right,
## 90° = up); the right thumb's cluster is two rings around the Attack button.
func _layout() -> void:
	var s := size
	if s.x < 10.0:
		return
	_layout_size = s
	var k := _k
	for b in _buttons:
		b.place(b.position + Vector2(b.radius, b.radius), float(b.get_meta(&"base_radius")) * k)
	var m := 40.0
	_attack_center = Vector2(s.x - m - 96.0 * k, s.y - m * 0.75 - 96.0 * k)
	var c := _attack_center
	button(&"attack").place(c)
	var inner := 205.0 * k
	var inner_angles := [184.0, 150.0, 116.0, 82.0]
	for i in 4:
		button(StringName("skill_%d" % (i + 1))).place(c + _polar(inner_angles[i], inner))
	var outer := 328.0 * k
	button(&"dodge").place(c + _polar(192.0, outer))
	button(&"roll").place(c + _polar(186.0, 452.0 * k))
	button(&"skill_5").place(c + _polar(164.0, outer))
	button(&"skill_6").place(c + _polar(136.0, outer))
	button(&"heavy").place(c + _polar(108.0, outer))
	button(&"guard").place(c + _polar(81.0, outer))
	button(&"interact").place(c + _polar(146.0, 490.0 * k))
	_stick_home = Vector2(m + 30.0 + STICK_RADIUS * k, s.y - m - 20.0 - STICK_RADIUS * k)
	if _stick_touch == -99:
		_stick_base = _stick_home
		_stick_knob = _stick_home
	# utility buttons: a 2 x 2 block left of the minimap
	var mm := _minimap_rect()
	var ur := 34.0 * k
	var gx := mm.position.x - 18.0 - ur
	var gy := mm.position.y + ur + 4.0
	var gap := ur * 2.0 + 14.0
	button(&"menu").place(Vector2(gx, gy))
	button(&"pause").place(Vector2(gx - gap, gy))
	button(&"bag").place(Vector2(gx, gy + gap))
	button(&"chat").place(Vector2(gx - gap, gy + gap))
	button(&"ping").place(Vector2(gx - gap * 2.0, gy))
	button(&"regroup").place(Vector2(gx - gap * 2.0, gy + gap))
	var mmb := button(&"minimap")
	mmb.place(mm.get_center(), mm.size.x * 0.5)
	queue_redraw()

func _minimap_rect() -> Rect2:
	if hud and hud.has_method(&"minimap_rect"):
		var r: Rect2 = hud.minimap_rect()
		if r.size.x > 10.0:
			return Rect2(r.position - global_position, r.size)
	return Rect2(Vector2(size.x - 24.0 - 180.0, 16.0), Vector2(180, 180))

static func _polar(deg: float, r: float) -> Vector2:
	var a := deg_to_rad(deg)
	return Vector2(cos(a), -sin(a)) * r

# ---- State --------------------------------------------------------------------------------------------------------

## Touch play, in a session, hero alive, nothing modal open.
func is_active() -> bool:
	return Settings.touch_mode and Game.in_session and player != null and is_instance_valid(player) and player.alive \
		and not Game.ui_blocking and not get_tree().paused

func _process(_delta: float) -> void:
	var on := Settings.touch_mode and Game.in_session
	visible = on
	if not on:
		if _was_active:
			_release_all()
		_was_active = false
		return
	var active := is_active()
	_sync_active(active)
	if size != _layout_size:
		_layout()
	var now := Time.get_ticks_msec() * 0.001
	for a in _taps.keys():
		if now >= _taps[a]:
			Input.action_release(a)
			_taps.erase(a)
	if _aim_clear_at > 0.0 and now >= _aim_clear_at and _aim_touch == -99:
		_aim_clear_at = 0.0
		if player:
			player.touch_aim_dir = Vector3.ZERO
	if active:
		_refresh()
	elif not _long.is_empty() and not _long.fired and now - _long.t0 >= LONG_PRESS:
		_long.fired = true
		for down in [true, false]:
			var mb := InputEventMouseButton.new()
			mb.button_index = MOUSE_BUTTON_RIGHT
			mb.pressed = down
			mb.position = _long.pos
			mb.global_position = _long.pos
			mb.device = InputEvent.DEVICE_ID_EMULATION
			Input.parse_input_event(mb)
		Input.vibrate_handheld(35)
	queue_redraw()

## Keyboard + mouse windows read right-clicks (use, equip, unequip, sell, salvage, refund a point). With a window open
## in touch play, holding a finger still on something for half a second sends that right-click.
func _track_long_press(e: InputEvent) -> void:
	if is_active() or not Game.ui_blocking:
		_long = {}
		return
	if e is InputEventScreenTouch and e.index == 0:
		_long = {"pos": e.position, "t0": _now(), "fired": false} if e.pressed else {}
	elif e is InputEventScreenDrag and e.index == 0 and not _long.is_empty() and e.position.distance_to(_long.pos) > 24.0:
		_long = {}
	elif e is InputEventScreenTouch and e.index != 0:
		_long = {}

func _sync_active(active: bool) -> void:
	if active != _was_active:
		if not active:
			_release_all()
		_was_active = active
	for b in _buttons:
		b.visible = active
	# party-only buttons
	button(&"ping").visible = active and Net.is_active()
	button(&"regroup").visible = active and (Net.is_client() or Net.is_host() and Net.player_count() > 1)   # the host: Summon

func _refresh() -> void:
	var p := player
	var hero := p.hero
	if hero == null:
		return
	# attack shows the main weapon
	var main := hero.equipment.get_item(&"main_weapon")
	button(&"attack").set_icon(main.icon() if main else UIArt.icon("items", "sword"))
	for i in HeroData.SKILL_BAR_SIZE:
		var b := button(StringName("skill_%d" % (i + 1)))
		var sid: StringName = hero.skill_bar[i]
		b.set_icon(UIArt.skill_icon(sid) if sid != &"" else null)
		b.set_meta(&"skill", sid)
		if sid == &"":
			b.set_state(0.0, 0.0, true)
			b.modulate.a = 0.35
			continue
		b.modulate.a = 1.0
		var cdv: float = p.cooldowns.get(sid, 0.0)
		var why := p.skill_block_reason(sid)
		b.set_state(cdv, p.cooldown_total.get(sid, cdv), why != "" and why != "Cooldown" and why != "Not enough Mana", -1, why == "Not enough Mana")
	var dmax: float = p.stats.get_stat(&"dodge_cooldown", 1.0) if p.stats else 1.0
	button(&"dodge").set_state(p.dodge_cd, dmax)
	button(&"roll").set_state(p.dodge_cd, dmax)
	for i in HeroData.ORB_SLOTS:
		# the orbs use whatever the potion belt holds (bh-011: any consumable, chosen in the Bag)
		var pb := button(&"potion_health" if i == 0 else &"potion_mana")
		var bp := hero.belt_preview(i)
		var best: StringName = bp.base
		var base := DB.item_base(best)
		if base and pb.get_meta(&"base", &"") != best:
			pb.set_meta(&"base", best)
			pb.set_icon(load(base.icon_path()) if ResourceLoader.exists(base.icon_path()) else null)
		pb.set_state(p.potion_cd, Player.POTION_COOLDOWN, false, int(bp.count))
	for q in range(HeroData.ORB_SLOTS, HeroData.BELT_SIZE):
		var qb := button(HeroData.belt_action(q))
		var qp := hero.belt_preview(q)
		var qbase := DB.item_base(qp.base)
		if qb.get_meta(&"base", &"-") != qp.base:
			qb.set_meta(&"base", qp.base)
			qb.set_icon(load(qbase.icon_path()) if qbase and ResourceLoader.exists(qbase.icon_path()) else UIArt.ui_icon("plus"))
		qb.set_state(0.0, 1.0, false, int(qp.count) if qp.base != &"" else -1)
	_place_potions()
	var it := button(&"interact")
	it.visible = _interact_text != ""
	if it.visible:
		it.caption = _short(_interact_text)
		it.icon = UIArt.ui_icon(_interact_icon(_interact_text))
		it.queue_redraw()

## The Interact button's picture for the verb on offer.
static func _interact_icon(t: String) -> String:
	if t.begins_with("Pick up"):
		return "check"
	if t.begins_with("Talk"):
		return "talk"
	if t.begins_with("Travel") or t.begins_with("Use Waypoint") or t.contains("Portal"):
		return "teleport"
	return "info"

static func _short(t: String) -> String:
	return t if t.length() <= 26 else t.substr(0, 24) + "…"

## The potion buttons sit on the HUD orbs: the whole orb is the button, the draught icon is a small badge on its rim.
func _place_potions() -> void:
	if hud == null or not hud.has_method(&"orb_rects"):
		return
	var rs: Array = hud.orb_rects()
	if rs.size() < 2:
		return
	for i in 2:
		var r: Rect2 = rs[i]
		var b := button(&"potion_health" if i == 0 else &"potion_mana")
		var rad := r.size.x * 0.5
		b.place(r.get_center() - global_position, rad)
		b.badge_radius = 30.0 * _k
		b.badge_offset = Vector2(-rad * 0.72 if i == 0 else rad * 0.72, -rad * 0.72)
	# the quick slots in a row between the orbs, a little above their centres
	var r0: Rect2 = rs[0]
	var r1: Rect2 = rs[1]
	var mid := (r0.get_center() + r1.get_center()) * 0.5 - global_position
	# fitted to the gap between the orbs (each orb keeps its own rim clear)
	var gap := maxf(120.0, r1.position.x - r0.end.x - 12.0 * _k)
	var step := minf(84.0 * _k, gap / 4.0)
	var qr := minf(34.0 * _k, step * 0.46)
	for q in range(HeroData.ORB_SLOTS, HeroData.BELT_SIZE):
		var off := float(q - HeroData.ORB_SLOTS) - 1.5
		button(HeroData.belt_action(q)).place(mid + Vector2(off * step, 18.0 * _k), qr)

# ---- Touches ------------------------------------------------------------------------------------------------------

func _input(e: InputEvent) -> void:
	if not visible:
		return
	_track_long_press(e)
	# a real mouse (not the one emulated from touches) drives the controls too, for testing touch play on a PC
	if e is InputEventMouseButton and e.device != InputEvent.DEVICE_ID_EMULATION and e.button_index == MOUSE_BUTTON_LEFT \
			and not DisplayServer.is_touchscreen_available():
		_touch(100, e.position, e.pressed)
	elif e is InputEventMouseMotion and e.device != InputEvent.DEVICE_ID_EMULATION and _touches.has(100):
		_drag(100, e.position)
	elif e is InputEventScreenTouch:
		_touch(e.index, e.position, e.pressed)
	elif e is InputEventScreenDrag:
		_drag(e.index, e.position)

func _touch(idx: int, pos: Vector2, pressed: bool) -> void:
	if pressed:
		if not is_active():
			return
		_sync_active(true)     # a window may have closed earlier this frame
		var hit: TouchButton = null
		for b in _buttons:
			if b.hit(pos) and (hit == null or b.radius < hit.radius):
				hit = b
		if hit:
			_touches[idx] = {"btn": hit, "start": pos, "pos": pos, "t0": _now()}
			_press(hit, idx)
			get_viewport().set_input_as_handled()
		elif _in_stick_zone(pos) and _stick_touch == -99:
			_stick_touch = idx
			_stick_base = _stick_home if Settings.touch_fixed_stick else pos
			_touches[idx] = {"btn": null, "stick": true, "start": pos, "pos": pos, "t0": _now()}
			_drag(idx, pos)
			get_viewport().set_input_as_handled()
		else:
			_touches[idx] = {"btn": null, "free": true, "start": pos, "pos": pos, "t0": _now()}
			_pinch_d = -1.0
		return
	if not _touches.has(idx):
		return
	var t: Dictionary = _touches[idx]
	_touches.erase(idx)
	if t.get("stick", false):
		_stick_touch = -99
		_set_stick(Vector2.ZERO)
		_stick_base = _stick_home
		_stick_knob = _stick_home
	elif t.btn:
		_release(t.btn, idx, pos)
	elif t.get("free", false):
		_pinch_d = -1.0
		if _now() - t.t0 < 0.35 and pos.distance_to(t.start) < 30.0:
			_free_tap()

func _drag(idx: int, pos: Vector2) -> void:
	if not _touches.has(idx):
		return
	var t: Dictionary = _touches[idx]
	t.pos = pos
	if t.get("stick", false):
		var r := STICK_RADIUS * _k
		var v := pos - _stick_base
		if v.length() > r and not Settings.touch_fixed_stick:
			_stick_base += v.normalized() * (v.length() - r)     # the stick follows a thumb that slides past its rim
			v = pos - _stick_base
		v = v.limit_length(r)
		_stick_knob = _stick_base + v
		var n := v / r
		_set_stick(n if n.length() > STICK_DEADZONE else Vector2.ZERO)
		get_viewport().set_input_as_handled()
	elif t.btn and String(t.btn.id).begins_with("skill_") and idx == _aim_touch:
		_update_drag_aim(t)
		get_viewport().set_input_as_handled()
	elif t.get("free", false):
		_pinch()

func _in_stick_zone(p: Vector2) -> bool:
	return p.x < size.x * 0.42 and p.y > size.y * 0.32

func _set_stick(v: Vector2) -> void:
	_stick_vec = v
	for pair in [[&"move_left", -v.x], [&"move_right", v.x], [&"move_up", -v.y], [&"move_down", v.y]]:
		if pair[1] > 0.0:
			Input.action_press(pair[0], clampf(pair[1], 0.0, 1.0))
		else:
			Input.action_release(pair[0])

func _press(b: TouchButton, idx: int) -> void:
	b.set_held(true)
	Audio.play_ui(&"ui_hover")
	match b.id:
		&"attack": Input.action_press(&"primary")
		&"heavy": Input.action_press(&"secondary")
		&"guard": Input.action_press(&"guard")
		&"dodge":
			if player:
				player.request_roll_forward(false)
			_tap(&"dodge")
		&"roll":
			if player:
				player.request_roll_forward()
			_tap(&"dodge")
		&"potion_health", &"potion_mana", &"interact": _tap(b.id)
		&"quick_1", &"quick_2", &"quick_3", &"quick_4":
			# an empty slot opens the chooser; a filled one uses it
			var slot := HeroData.BELT_ACTIONS.find(b.id)
			if player and player.hero.potion_belt[slot] == &"":
				BeltPicker.open(b, player.hero, slot)
			elif player:
				player.use_belt(slot)
		_:
			if String(b.id).begins_with("skill_"):
				var sid: StringName = b.get_meta(&"skill", &"")
				if sid == &"":
					return
				_aim_touch = idx
				if player:
					player.touch_aim_dir = Vector3.ZERO
				var s := DB.skill(sid)
				if s and s.behavior == &"spin":      # channelled: held down for as long as the finger stays
					Input.action_press(b.id)

func _release(b: TouchButton, idx: int, pos: Vector2) -> void:
	b.set_held(false)
	match b.id:
		&"attack": Input.action_release(&"primary")
		&"heavy": Input.action_release(&"secondary")
		&"guard": Input.action_release(&"guard")
		&"bag": _open_window(&"inventory")
		&"menu": _open_window(&"mobile_menu")
		&"minimap": _open_window(&"world_map")
		&"chat":
			if Game.ui_root:
				Game.ui_root.chat.open()
		&"pause":
			if Game.ui_root:
				Game.ui_root.back()
		&"ping":
			if player:
				player.ping_here()
		&"regroup":
			Net.open_team_portal()
		_:
			if String(b.id).begins_with("skill_") and idx == _aim_touch:
				_aim_touch = -99
				var sid: StringName = b.get_meta(&"skill", &"")
				var s := DB.skill(sid) if sid != &"" else null
				if s and s.behavior == &"spin":
					Input.action_release(b.id)
				elif sid != &"":
					if pos.distance_to(b.center()) < DRAG_AIM_MIN and player:
						player.touch_aim_dir = Vector3.ZERO           # a tap: auto-aim
					_tap(b.id)
				_aim_clear_at = _now() + AIM_HOLD

func _open_window(id: StringName) -> void:
	if Game.ui_root:
		Game.ui_root.toggle(id)

## Tap an action: pressed now, released a few frames later so the physics step sees it.
func _tap(action: StringName) -> void:
	Input.action_press(action)
	_taps[action] = _now() + TAP_TIME

func _update_drag_aim(t: Dictionary) -> void:
	var b: TouchButton = t.btn
	var v: Vector2 = t.pos - b.center()
	if v.length() < DRAG_AIM_MIN or player == null or player.camera == null:
		if player:
			player.touch_aim_dir = Vector3.ZERO
		return
	var s := DB.skill(b.get_meta(&"skill", &""))
	var reach := 10.0
	if s:
		reach = float(s.params.get("range", s.params.get("distance", s.params.get("max_range", 10.0))))
	var w := player.camera.ground_basis() * Vector3(v.x, 0.0, v.y)
	w.y = 0.0
	player.touch_aim_dir = w.normalized()
	player.touch_aim_dist = clampf(v.length() / (DRAG_AIM_FULL * _k), 0.15, 1.0) * clampf(reach, 3.0, 18.0)

func _free_tap() -> void:
	# a tap on a ground loot label (LootLabels tracks the emulated mouse) picks the drop up
	if Game.hover_loot and is_instance_valid(Game.hover_loot) and player and Game.hover_loot.has_method(&"request_pickup"):
		Game.hover_loot.request_pickup(player)

func _pinch() -> void:
	var free := []
	for i in _touches:
		if _touches[i].get("free", false):
			free.append(_touches[i].pos)
	if free.size() != 2 or player == null or player.camera == null:
		_pinch_d = -1.0
		return
	var d: float = (free[0] as Vector2).distance_to(free[1])
	if _pinch_d < 0.0:
		_pinch_d = d
		return
	if absf(d - _pinch_d) > 70.0:
		player.camera.zoom(-1 if d > _pinch_d else 1)
		_pinch_d = d

func _release_all() -> void:
	for a in [&"primary", &"secondary", &"guard", &"move_left", &"move_right", &"move_up", &"move_down", &"dodge",
			&"potion_health", &"potion_mana", &"interact"]:
		Input.action_release(a)
	for i in HeroData.SKILL_BAR_SIZE:
		Input.action_release(StringName("skill_%d" % (i + 1)))
	for b in _buttons:
		b.set_held(false)
	_touches.clear()
	_taps.clear()
	_stick_touch = -99
	_stick_vec = Vector2.ZERO
	_stick_base = _stick_home
	_stick_knob = _stick_home
	_aim_touch = -99
	if player and is_instance_valid(player):
		player.touch_aim_dir = Vector3.ZERO

static func _now() -> float:
	return Time.get_ticks_msec() * 0.001

# ---- Drawing: the stick and the aim guide -------------------------------------------------------------------------

func _draw() -> void:
	if not _was_active:
		return
	var r := STICK_RADIUS * _k
	var live := _stick_touch != -99
	draw_circle(_stick_base, r, Color(0.03, 0.03, 0.04, 0.34 if live else 0.2))
	draw_arc(_stick_base, r, 0.0, TAU, 72, Color(UITheme.BRONZE, 0.75 if live else 0.45), 3.0, true)
	for i in 4:     # direction ticks
		var a := i * PI * 0.5
		var dv := Vector2(cos(a), sin(a))
		draw_line(_stick_base + dv * (r - 16.0), _stick_base + dv * (r - 6.0), Color(UITheme.PARCHMENT, 0.4), 3.0, true)
	var kr := r * 0.42
	draw_circle(_stick_knob, kr, Color(0.12, 0.1, 0.09, 0.75 if live else 0.45))
	draw_arc(_stick_knob, kr, 0.0, TAU, 48, Color(UITheme.GOLD if live else UITheme.BRONZE, 0.9), 3.0, true)
	# hand aim: a line from the hero to the aim point, with a ring where it lands
	if _aim_touch != -99 and player and player.touch_aim_dir.length() > 0.1 and player.camera:
		var cam := player.camera
		var from3 := player.global_position + Vector3.UP * 0.2
		var to3 := player.global_position + player.touch_aim_dir * player.touch_aim_dist + Vector3.UP * 0.2
		if not cam.is_position_behind(from3) and not cam.is_position_behind(to3):
			var a2 := cam.unproject_position(from3)
			var b2 := cam.unproject_position(to3)
			var col := Color(1.0, 0.85, 0.45, 0.85)
			draw_line(a2, b2, Color(0, 0, 0, 0.5), 9.0, true)
			draw_line(a2, b2, col, 5.0, true)
			draw_arc(b2, 30.0, 0.0, TAU, 40, Color(0, 0, 0, 0.5), 7.0, true)
			draw_arc(b2, 30.0, 0.0, TAU, 40, col, 4.0, true)
