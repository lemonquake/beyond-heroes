class_name TouchGesture
extends RefCounted
## A touch on a GUI target has one result: tap on release, or secondary action after a still hold.
## TouchControls observes raw contacts; participating controls supply their existing click handler in GUI input.
## Mouse input remains on the control's normal path. No mouse button is injected into an unrelated/covered target.

const HOLD_SECONDS := 0.5
const MOVE_CANCEL := 24.0

static var _contacts := {}
static var _pointer := -1
static var _owner: WeakRef
static var _callback: Callable
static var _start := Vector2.ZERO
static var _local_start := Vector2.ZERO
static var _transform := Transform2D.IDENTITY
static var _started := 0.0
static var _finger := -1
static var _fired := false
static var _double := false
static var _modal := ""

static func register(control: Control) -> void:
	control.visibility_changed.connect(func() -> void:
		if not control.is_visible_in_tree():
			cancel_for(control))
	control.tree_exiting.connect(func() -> void: cancel_for(control))

## Called before a control's normal mouse handler. GUI event positions are already local to that control.
static func consume(control: Control, event: InputEvent, callback: Callable) -> bool:
	if not Settings.touch_mode or not event is InputEventMouseButton \
			or event.device != InputEvent.DEVICE_ID_EMULATION or event.button_index != MOUSE_BUTTON_LEFT:
		return false
	if event.pressed:
		cancel()
		if _contacts.size() == 1 and _pointer >= 0:
			_owner = weakref(control)
			_callback = callback
			_local_start = event.position
			_transform = control.get_global_transform_with_canvas()
			_start = _transform * event.position
			_started = _now()
			_finger = _pointer
			_double = event.double_click
			_modal = _modal_signature()
	# The raw release finishes the gesture even if it is outside the original GUI control.
	control.accept_event()
	return true

static func observe(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and not event.canceled:
			if _contacts.is_empty():
				_pointer = event.index
			_contacts[event.index] = event.position
			if _contacts.size() > 1:
				cancel()
		else:
			if event.index == _finger:
				if event.canceled:
					cancel()
				else:
					_finish(event.position)
			_contacts.erase(event.index)
			if _contacts.is_empty():
				_pointer = -1
	elif event is InputEventScreenDrag:
		if _contacts.has(event.index):
			_contacts[event.index] = event.position
		if event.index == _finger and event.position.distance_to(_start) > MOVE_CANCEL:
			cancel()

static func update() -> void:
	var control := _control()
	if control == null:
		cancel()
		return
	if not _valid(control):
		cancel()
		return
	if not _fired and _now() - _started >= HOLD_SECONDS:
		_fired = true # Set this before the callback: its refresh may replace or hide the target.
		_callback.call(MOUSE_BUTTON_RIGHT, _local_start, false)
		Input.vibrate_handheld(35)

static func _finish(position: Vector2) -> void:
	var control := _control()
	if control != null and _valid(control) and not _fired and position.distance_to(_start) <= MOVE_CANCEL \
			and Rect2(Vector2.ZERO, control.size).has_point(_transform.affine_inverse() * position):
		var callback := _callback
		var local := _local_start
		var double := _double
		var held := _now() - _started >= HOLD_SECONDS
		cancel()
		callback.call(MOUSE_BUTTON_RIGHT if held else MOUSE_BUTTON_LEFT, local, double and not held)
	else:
		cancel()

static func _valid(control: Control) -> bool:
	return Settings.touch_mode and control.is_visible_in_tree() and not control.get_viewport().gui_is_dragging() \
		and control.get_global_transform_with_canvas().is_equal_approx(_transform) and _modal_signature() == _modal

static func _control() -> Control:
	return _owner.get_ref() as Control if _owner != null else null

static func cancel_for(control: Control) -> void:
	if _control() == control:
		cancel()

static func cancel() -> void:
	_owner = null
	_callback = Callable()
	_finger = -1
	_fired = false

static func reset() -> void:
	cancel()
	_contacts.clear()
	_pointer = -1

static func has_popup(viewport: Viewport) -> bool:
	for window in viewport.get_embedded_subwindows():
		if window is Popup and window.visible:
			return true
	return false

static func _modal_signature() -> String:
	var ui := Game.ui_root
	var ids := PackedStringArray()
	if is_instance_valid(ui):
		for window in ui.windows.values():
			if is_instance_valid(window) and window.visible:
				ids.append(str(window.get_instance_id()))
		for control in [ui.confirm, ui.request_box, ui.dialogue, ui.pause_menu, ui.creator]:
			if is_instance_valid(control) and control.visible:
				ids.append(str(control.get_instance_id()))
		if is_instance_valid(ui.chat) and ui.chat.is_open():
			ids.append(str(ui.chat.get_instance_id()))
	var owner := _control()
	if owner:
		for window in owner.get_viewport().get_embedded_subwindows():
			if window is Popup and window.visible:
				ids.append(str(window.get_instance_id()))
	return ",".join(ids)

static func _now() -> float:
	return Time.get_ticks_msec() * 0.001
