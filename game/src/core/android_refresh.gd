extends RefCounted
## Optional Android 11+ Surface hint. A request is not a promise: Android can keep a lower refresh rate for the
## display, battery or temperature. No plugin/Gradle build is required; AndroidRuntime ships with Godot.

static func request(frame_limit: int) -> bool:
	if not OS.has_feature("android") or not Engine.has_singleton("AndroidRuntime") or not Engine.has_singleton("JavaClassWrapper"):
		return false
	var runtime := Engine.get_singleton("AndroidRuntime")
	var java := Engine.get_singleton("JavaClassWrapper")
	if not runtime.has_method("getApplicationContext") or not runtime.has_method("getActivity"):
		return false
	var godot_class = java.wrap("org.godotengine.godot.Godot")
	if java.get_exception() != null:
		return false
	var godot = _call(java, godot_class, &"getInstance", [runtime.getApplicationContext()])
	var render_view = _call(java, godot, &"getRenderView")
	var view = _call(java, render_view, &"getView")
	var holder = _call(java, view, &"getHolder")
	var surface = _call(java, holder, &"getSurface")
	if not bool(_call(java, surface, &"isValid")) or not surface.has_java_method(&"setFrameRate"):
		return false
	var rate := float(maxi(0, frame_limit))
	if frame_limit <= 0:
		# Unlimited asks for the highest supported mode, rather than clearing the hint back to Android's default.
		var manager = _call(java, runtime.getActivity(), &"getWindowManager")
		var display = _call(java, manager, &"getDefaultDisplay")
		var modes = _call(java, display, &"getSupportedModes")
		if modes is Array:
			for mode in modes:
				var hz = _call(java, mode, &"getRefreshRate")
				if hz is float or hz is int:
					rate = maxf(rate, float(hz))
		if rate <= 0.0:
			return false
	# FRAME_RATE_COMPATIBILITY_DEFAULT (0): game content can adapt to the chosen display refresh rate.
	# The two-argument API exists from Android 11; has_java_method leaves older devices untouched.
	surface.setFrameRate(rate, 0)
	return java.get_exception() == null

static func _call(java: Object, target: Variant, method: StringName, values: Array = []) -> Variant:
	if target == null or not target.has_method(&"has_java_method") or not target.has_java_method(method):
		return null
	var result = target.callv(method, values)
	if java.get_exception() != null:
		return null
	return result
