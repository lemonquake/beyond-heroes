extends TestCase
## Viewport event regressions for the Android raw-touch + emulated-mouse GUI path.
## These exercise actual GUI routing, not direct calls to the target's _gui_input or action handlers.

var _vp: SubViewport
var _controls: TouchControls
var _saved := {}
var _ui: UIRoot
var _hero: HeroData
var _player: Player
var _clicks: Array = []

class EngineInputBridge extends Node:
	var target: SubViewport
	var target_position := Vector2.ZERO
	var order: Array[String] = []
	func _input(event: InputEvent) -> void:
		if event is InputEventScreenTouch or event is InputEventMouseButton and event.device == InputEvent.DEVICE_ID_EMULATION:
			order.append("touch" if event is InputEventScreenTouch else "mouse")
			# This viewport is not displayed in the root window. Rebase the already
			# synthesized pair to its fixture, retaining the real engine's event order/device.
			var local_event := event.duplicate()
			local_event.position = target_position
			if local_event is InputEventMouseButton:
				local_event.global_position = target_position
			target.push_input(local_event, true)

func _init() -> void:
	strict = true

func _setup() -> void:
	_saved = {"mode": Settings.control_mode, "session": Game.in_session, "blocking": Game.ui_blocking,
		"hero": Game.hero, "player": Game.player, "ui": Game.ui_root}
	Settings.control_mode = "mobile"
	Game.in_session = true
	Game.ui_blocking = true
	_hero = Game.new_hero(&"knight", "Touch Test")
	Game.hero = _hero
	_player = Player.new()
	_player.hero = _hero
	_player.stats = _hero.compute_stats()
	Game.player = _player
	_ui = UIRoot.new() # Only the shared modal registry is needed; avoid creating every game window for each case.
	Game.ui_root = _ui
	_vp = SubViewport.new()
	_vp.size = Vector2i(1920, 1080)
	_vp.handle_input_locally = true
	_vp.gui_embed_subwindows = true
	host.add_child(_vp)
	_controls = TouchControls.new()
	_controls.player = _player
	_vp.add_child(_controls)
	_ui.confirm = ConfirmDialog.new()
	_vp.add_child(_ui.confirm)
	TouchGesture.reset()
	_clicks.clear()
	await _frames()

func _cleanup() -> void:
	TouchGesture.reset()
	_vp.free()
	_ui.free()
	_player.free()
	Settings.control_mode = _saved.mode
	Game.in_session = _saved.session
	Game.ui_blocking = _saved.blocking
	Game.hero = _saved.hero
	Game.player = _saved.player
	Game.ui_root = _saved.ui

func _frames(n := 3) -> void:
	for i in n:
		await host.get_tree().process_frame

func _hold() -> void:
	# Gestures use monotonic wall time. Process timers/physics catch-up can tick
	# differently in an uncapped headless run, especially during tooltip layout.
	var deadline := Time.get_ticks_msec() + 580
	while Time.get_ticks_msec() < deadline:
		await host.get_tree().process_frame
	await _frames()

func _slot(parent: Node = null) -> ItemSlot:
	var slot := ItemSlot.new(ItemSlot.Kind.INVENTORY, 80.0)
	slot.size = Vector2(80, 80)
	slot.position = Vector2(200, 200)
	slot.drag_enabled = false
	slot.set_item(DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 1, 123))
	slot.clicked.connect(func(_s, button, shift, _ctrl): _clicks.append([button, shift]))
	(parent if parent != null else _vp).add_child(slot)
	return slot

func _point(control: Control) -> Vector2:
	return control.get_global_transform_with_canvas() * (control.size * 0.5)

## push_input bypasses Input's OS emulation. Godot 4.7.2 dispatches the synthesized mouse before the raw touch.
func _touch(position: Vector2, down: bool, index := 0, canceled := false, mouse_first := true) -> void:
	var raw := InputEventScreenTouch.new()
	raw.position = position
	raw.index = index
	raw.pressed = down
	raw.canceled = canceled
	var mouse: InputEventMouseButton
	if index == 0:
		mouse = InputEventMouseButton.new()
		mouse.position = position
		mouse.global_position = position
		mouse.device = InputEvent.DEVICE_ID_EMULATION
		mouse.button_index = MOUSE_BUTTON_LEFT
		mouse.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
		mouse.pressed = down
		if mouse_first:
			_vp.push_input(mouse, true)
	_vp.push_input(raw, true)
	if mouse != null and not mouse_first:
		_vp.push_input(mouse, true)

func _drag(position: Vector2, relative := Vector2(40, 0)) -> void:
	var raw := InputEventScreenDrag.new()
	raw.position = position
	raw.relative = relative
	raw.index = 0
	_vp.push_input(raw, true)
	var mouse := InputEventMouseMotion.new()
	mouse.position = position
	mouse.global_position = position
	mouse.relative = relative
	mouse.device = InputEvent.DEVICE_ID_EMULATION
	mouse.button_mask = MOUSE_BUTTON_MASK_LEFT
	_vp.push_input(mouse, true)

func test_a_tap_and_hold_have_one_result_and_mouse_keeps_quick_use() -> void:
	await _setup()
	var slot := _slot()
	await _frames()
	var at := _point(slot)
	_touch(at, true)
	eq(_clicks.size(), 0, "touch press does not perform the primary action")
	_touch(at, false)
	eq(_clicks, [[MOUSE_BUTTON_LEFT, false]], "tap performs one primary action on release")
	_clicks.clear()
	_touch(at, true)
	await _hold()
	eq(_clicks, [[MOUSE_BUTTON_RIGHT, false]], "hold performs only the secondary action")
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 1, "continued hold and release cannot repeat or perform primary")
	var mouse := InputEventMouseButton.new()
	mouse.position = at
	mouse.global_position = at
	mouse.pressed = true
	mouse.button_index = MOUSE_BUTTON_RIGHT
	_vp.push_input(mouse, true)
	eq(_clicks.size(), 2, "real mouse right-click still acts immediately in touch mode")
	_cleanup()
	done()

func test_native_and_raw_first_orders_require_one_matching_contact() -> void:
	await _setup()
	var slot := _slot()
	await _frames()
	var at := _point(slot)
	for mouse_first in [true, false]:
		_clicks.clear()
		_touch(at, true, 0, false, mouse_first)
		eq(_clicks.size(), 0, "neither event order performs an action on press")
		_touch(at, false, 0, false, mouse_first)
		eq(_clicks, [[MOUSE_BUTTON_LEFT, false]], "both event orders tap exactly once on release")
		_clicks.clear()
		_touch(at, true, 0, false, mouse_first)
		await _hold()
		_touch(at, false, 0, false, mouse_first)
		eq(_clicks, [[MOUSE_BUTTON_RIGHT, false]], "both event orders hold exactly once without a primary action")
	# A synthetic GUI press cannot borrow an unrelated or later raw contact.
	_clicks.clear()
	var mouse := InputEventMouseButton.new()
	mouse.position = at
	mouse.global_position = at
	mouse.device = InputEvent.DEVICE_ID_EMULATION
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.button_mask = MOUSE_BUTTON_MASK_LEFT
	mouse.pressed = true
	_vp.push_input(mouse, true)
	await _frames()
	await _hold()
	eq(_clicks.size(), 0, "an emulated mouse press without a raw contact cannot fire")
	var raw := InputEventScreenTouch.new()
	raw.position = at
	raw.index = 0
	raw.pressed = true
	_vp.push_input(raw, true)
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "a later raw contact cannot revive an expired GUI press")
	mouse.pressed = true
	_vp.push_input(mouse, true)
	raw.position = at + Vector2(2, 0)
	raw.pressed = true
	_vp.push_input(raw, true)
	await _hold()
	_touch(raw.position, false)
	eq(_clicks.size(), 0, "a different raw position cannot claim the pending GUI target")
	_cleanup()
	done()

func test_actual_engine_mouse_synthesis_routes_tap_and_hold() -> void:
	await _setup()
	var slot := _slot()
	await _frames()
	var bridge := EngineInputBridge.new()
	bridge.target = _vp
	bridge.target_position = _point(slot)
	host.add_child(bridge)
	var prior_mouse := Input.emulate_mouse_from_touch
	var prior_touch := Input.emulate_touch_from_mouse
	Input.emulate_mouse_from_touch = true
	Input.emulate_touch_from_mouse = false
	var raw := InputEventScreenTouch.new()
	raw.index = 19
	raw.position = _point(slot)
	raw.pressed = true
	Input.parse_input_event(raw)
	Input.flush_buffered_events()
	eq(bridge.order, ["mouse", "touch"], "the installed engine dispatches synthesized mouse before the original touch")
	eq(_clicks.size(), 0, "the real engine pair does not select on press")
	raw = raw.duplicate()
	raw.pressed = false
	Input.parse_input_event(raw)
	Input.flush_buffered_events()
	eq(_clicks, [[MOUSE_BUTTON_LEFT, false]], "actual Input synthesis selects once on release")
	_clicks.clear()
	raw = raw.duplicate()
	raw.pressed = true
	Input.parse_input_event(raw)
	Input.flush_buffered_events()
	await _hold()
	raw = raw.duplicate()
	raw.pressed = false
	Input.parse_input_event(raw)
	Input.flush_buffered_events()
	eq(_clicks, [[MOUSE_BUTTON_RIGHT, false]], "actual Input synthesis holds once without selecting or repeating")
	bridge.free()
	Input.emulate_mouse_from_touch = prior_mouse
	Input.emulate_touch_from_mouse = prior_touch
	_cleanup()
	done()

func test_b_movement_cancellation_and_multitouch_discard_actions() -> void:
	await _setup()
	var slot := _slot()
	await _frames()
	var at := _point(slot)
	_touch(at, true)
	_drag(at + Vector2(30, 0))
	_drag(at, Vector2(-30, 0))
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "moving away and returning never rearms a hold or tap")
	_touch(at, true)
	_touch(at, false, 0, true)
	await _hold()
	eq(_clicks.size(), 0, "Android canceled contact has no action")
	_touch(at, true)
	_touch(at + Vector2(90, 0), true, 1)
	_touch(at + Vector2(90, 0), false, 1)
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "second finger cancels the entire gesture even after it lifts")
	_cleanup()
	done()

func test_c_scaled_gui_scroll_hidden_modal_and_focus_cancel() -> void:
	await _setup()
	var parent := Control.new()
	parent.position = Vector2(120, 70)
	parent.scale = Vector2(0.7, 0.7)
	_vp.add_child(parent)
	var slot := _slot(parent)
	await _frames()
	var at := _point(slot)
	_touch(at, true)
	await _hold()
	_touch(at, false)
	eq(_clicks, [[MOUSE_BUTTON_RIGHT, false]], "GUI hold resolves a scaled and translated target once")
	_clicks.clear()
	_touch(at, true)
	parent.position.y -= 35 # A scroll/layout movement invalidates the original target transform.
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "content moving under a stationary finger cancels")
	at = _point(slot)
	_touch(at, true)
	parent.hide()
	parent.show()
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "hidden then reopened owner cannot retain its hold")
	_touch(at, true)
	_ui.confirm.show()
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "new modal blocks the held target")
	_ui.confirm.hide()
	_touch(at, true)
	_controls.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	_controls.notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	await _hold()
	_touch(at, false)
	eq(_clicks.size(), 0, "focus loss discards the pending action")
	_cleanup()
	done()

func test_d_inventory_hold_shows_options_without_equipping() -> void:
	await _setup()
	var tooltips := TooltipLayer.new()
	_vp.add_child(tooltips)
	var item := DB.make_item(&"iron_longsword", BH.Rarity.COMMON, 1, 456)
	_hero.inventory.add(item)
	var window := InventoryWindow.new()
	_vp.add_child(window)
	_ui.windows[&"inventory"] = window
	window.open()
	window._tw.kill()
	window._root.scale = Vector2.ONE * window.fit_scale()
	await _frames(12)
	var slot := window.cells[_hero.inventory.index_of(item)]
	_touch(_point(slot), true)
	await _frames(2)
	await _hold()
	ok(is_instance_valid(window._touch_menu) and window._touch_menu.visible, "inventory hold opens readable item options")
	ok(tooltips._panel == null, "options hide the comparison tooltip instead of covering the inventory twice")
	ok(_hero.inventory.index_of(item) >= 0, "opening options does not equip the held item")
	eq(window.selected, slot, "options belong to the held item")
	var menu := window._touch_menu
	if is_instance_valid(menu):
		var labels := []
		for i in menu.item_count:
			labels.append(menu.get_item_text(i))
		for label in ["Equip", "Split", "Lock", "Favorite", "Mark to Sell", "Drop", "Destroy"]:
			ok(labels.has(label), "options include " + label)
		ok(menu.is_item_disabled(labels.find("Split")), "single item cannot split")
		_touch(_point(slot), false)
		await _frames()
		ok(is_instance_valid(menu) and menu.visible, "releasing the original hold leaves options open")
		if is_instance_valid(menu) and menu.visible:
			# The menu is an embedded Window. Route the same raw touch/emulated
			# mouse pair through its parent viewport, in window pixel coordinates.
			var panel := menu.get_theme_stylebox("panel")
			var top := panel.get_content_margin(SIDE_TOP)
			var bottom := panel.get_content_margin(SIDE_BOTTOM)
			var row := (float(menu.size.y) - top - bottom) / menu.item_count
			var at := Vector2(menu.position) + Vector2(menu.size.x * 0.5, top + (labels.find("Lock") + 0.5) * row)
			_touch(at, true)
			_touch(at, false)
			await _frames()
		ok(item.locked, "touching context Lock uses the existing action")
		ok(_hero.inventory.index_of(item) >= 0, "popup tap never uses the underlying equipment slot")
		ok(not is_instance_valid(window._touch_menu) or not window._touch_menu.visible, "popup tap closes options")
		await _frames()
		_touch(_point(slot), true)
		await _hold()
		var locked_menu := window._touch_menu
		if is_instance_valid(locked_menu):
			ok(locked_menu.is_item_disabled(5) and locked_menu.is_item_disabled(6), "protected item cannot drop or destroy")
		_touch(_point(slot), false)
	window.close_window()
	ok(not is_instance_valid(window._touch_menu), "closing inventory closes its item menu")
	_cleanup()
	done()

func test_e_skill_and_talent_holds_refund_without_learning() -> void:
	await _setup()
	for talents in [false, true]:
		var tree := TreeView.new()
		tree.position = Vector2(100, 100)
		tree.scale = Vector2(0.8, 0.8)
		_vp.add_child(tree)
		tree.bind(_hero, talents)
		var state := _hero.talent_tree if talents else _hero.skill_tree
		var node: Dictionary = state.tree.nodes.front()
		state.ranks[node.id] = 2
		_hero.progress.skill_points = 20
		_hero.progress.talent_points = 20
		await _frames()
		var at := tree.get_global_transform_with_canvas() * (tree.node_center(node) * tree.zoom)
		_touch(at, true)
		eq(state.rank(node.id), 2, "press does not learn before refund")
		await _hold()
		_touch(at, false)
		eq(state.rank(node.id), 1, "hold refunds exactly one rank")
		tree.free()
	_cleanup()
	done()

func test_f_held_combat_inputs_release_on_pause_focus_restart_and_hidden_ui() -> void:
	await _setup()
	Game.ui_blocking = false
	await _frames()
	var at := _controls.button(&"attack").center()
	_touch(at, true)
	ok(Input.is_action_pressed(&"primary"), "touch holds combat input")
	_touch(at, true, 1)
	_touch(at, false)
	ok(Input.is_action_pressed(&"primary"), "lifting one finger preserves the other holder")
	_touch(at, false, 1)
	ok(not Input.is_action_pressed(&"primary"), "last holder releases combat input")
	for cause in ["modal", "pause", "popup", "focus", "restart", "hidden", "canceled"]:
		_touch(at, true)
		match cause:
			"modal":
				Game.ui_blocking = true
				await _frames()
				Game.ui_blocking = false
			"pause":
				host.get_tree().paused = true
				await _frames()
				host.get_tree().paused = false
			"popup":
				var menu := PopupMenu.new()
				menu.add_item("Choose belt item")
				_vp.add_child(menu)
				menu.popup(Rect2i(100, 100, 300, 120))
				await _frames()
				menu.hide()
				menu.free()
			"focus":
				_controls.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
				_controls.notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
			"restart":
				Events.player_spawned.emit(_player)
			"hidden":
				_controls.hide()
			"canceled":
				_touch(at, false, 0, true)
		ok(not Input.is_action_pressed(&"primary"), cause + " releases held combat input")
		ok(_controls._touches.is_empty() and _controls._taps.is_empty(), cause + " clears touch ownership")
		_touch(at, false)
		await _frames()
	_cleanup()
	done()

func test_g_merchant_hold_chooses_quantity_without_buying_first() -> void:
	await _setup()
	_hero.inventory.gold = 100000
	var shop := ShopWindow.new()
	shop.shop = Shop.open(DB.shop(&"tovin_goods"), _hero)
	_vp.add_child(shop)
	_ui.windows[&"shop"] = shop
	shop.open()
	shop._tw.kill()
	shop._root.scale = Vector2.ONE * shop.fit_scale()
	await _frames(12)
	var slot: ItemSlot
	for control in shop._stock_grid.get_children():
		if control is ItemSlot and control.item.base.is_stackable():
			slot = control
			break
	ok(slot != null, "merchant has a stack with a touch quantity choice")
	if slot != null:
		var base: StringName = slot.item.base.id
		var before_count := _hero.inventory.count_of(base)
		var before_gold := _hero.inventory.gold
		var at := _point(slot)
		_touch(at, true)
		await _hold()
		eq(_hero.inventory.gold, before_gold, "hold does not buy on initial press")
		eq(_hero.inventory.count_of(base), before_count, "hold does not buy before choosing quantity")
		ok(_ui.confirm.visible and _ui.confirm._title.text == "Quantity", "hold opens the existing quantity selector")
		_touch(at, false)
		eq(_hero.inventory.count_of(base), before_count, "release after quantity hold does not buy")
		_ui.confirm.cancel()
		await _frames()
		_touch(at, true)
		_touch(at, false)
		eq(_hero.inventory.count_of(base), before_count + 1, "short tap still buys one")
	_cleanup()
	done()

func test_h_belt_context_and_chat_buttons_receive_gui_touches() -> void:
	await _setup()
	var belt := SkillButton.new(&"potion_health", 80.0)
	belt.position = Vector2(200, 200)
	belt.size = Vector2(80, 80)
	_vp.add_child(belt)
	belt.activated.connect(func(_b): _clicks.append("tap"))
	belt.context.connect(func(_b): _clicks.append("context"))
	await _frames()
	_touch(_point(belt), true)
	await _hold()
	_touch(_point(belt), false)
	eq(_clicks, ["context"], "belt hold invokes its chooser once without using the belt")
	belt.free()
	var chat := ChatBox.new()
	_vp.add_child(chat)
	_ui.chat = chat
	chat.open()
	await _frames(8)
	chat._line.text = "Touch message"
	var send: Button = chat._touch_buttons[0]
	_touch(_point(send), true)
	_touch(_point(send), false)
	await _frames()
	ok(Array(chat.lines()).any(func(line): return str(line).contains("Touch message")), "touch Send submits chat text")
	chat.open()
	await _frames()
	_touch(_point(chat._close_button), true)
	_touch(_point(chat._close_button), false)
	ok(not chat.is_open(), "touch X closes chat")
	var pause := PauseMenu.new()
	_vp.add_child(pause)
	_ui.pause_menu = pause
	pause.open()
	await _frames(8)
	ok(host.get_tree().paused, "pause menu pauses the offline game")
	_touch(_point(pause._buttons[0]), true)
	_touch(_point(pause._buttons[0]), false)
	ok(not host.get_tree().paused and not pause.visible, "touch Resume closes pause and resumes the game")
	_cleanup()
	done()

func test_i_presentation_reuses_belt_previews_until_inventory_or_binding_changes() -> void:
	await _setup()
	Game.ui_blocking = false
	await _frames()
	_controls._refresh()
	var preview: Dictionary = _controls._belt_previews[0]
	var attack_icon := _controls.button(&"attack").icon
	for i in 120:
		_controls._refresh()
	ok(is_same(preview, _controls._belt_previews[0]), "unchanged frames reuse the belt preview instead of rescanning inventory")
	eq(_controls.button(&"attack").icon, attack_icon, "unchanged main weapon keeps its icon")
	_hero.inventory.add(DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 876))
	_controls._refresh()
	ok(not is_same(preview, _controls._belt_previews[0]), "inventory event invalidates belt counts")
	eq(_controls.button(&"potion_health").count, _hero.belt_preview(0).count, "updated count is immediately presented")
	_hero.set_belt(HeroData.ORB_SLOTS, &"health_potion")
	_controls._refresh()
	eq(_controls.button(&"quick_1").get_meta(&"base"), &"health_potion", "changing belt binding updates its icon")
	_cleanup()
	done()

func test_j_shared_skill_button_releases_in_either_finger_order() -> void:
	await _setup()
	Game.ui_blocking = false
	await _frames()
	for sid in [&"whirlwind", _hero.skill_bar[0]]:
		_hero.skill_bar[0] = sid
		_controls._refresh()
		var at := _controls.button(&"skill_1").center()
		var spin: bool = DB.skill(sid).behavior == &"spin"
		for order in [[0, 1], [1, 0]]:
			_touch(at, true, 0)
			_touch(at, true, 1)
			_touch(at, false, order[0])
			ok(_controls._aim_touch == order[1], "remaining finger owns aim after releasing %d first" % order[0])
			if spin:
				ok(Input.is_action_pressed(&"skill_1"), "channel remains held by its remaining finger")
			else:
				ok(not _controls._taps.has(&"skill_1"), "first release cannot cast a shared button early")
			_touch(at, false, order[1])
			if spin:
				ok(not Input.is_action_pressed(&"skill_1"), "last finger stops the channel")
			else:
				ok(_controls._taps.has(&"skill_1"), "last finger casts the skill once")
			eq(_controls._aim_touch, -99, "last release clears aim ownership")
			ok(_controls._touches.is_empty(), "no stale finger remains")
			await host.get_tree().create_timer(0.12, true).timeout
	_cleanup()
	done()
