extends TestCase
## bh-032 (beta readiness): readable interface at any window size, plain connection and version messages, and the minimap render
## that used to be redrawn on every frame at its Wide zoom.

func _init() -> void:
	strict = true

func test_interface_grows_in_small_windows_only() -> void:
	var saved := [Settings.ui_scale, Settings.ui_auto, Settings.control_mode]
	Settings.ui_scale = 1.0
	Settings.ui_auto = true
	Settings.control_mode = "pc"
	near(Settings.effective_ui_scale(Vector2i(1920, 1080)), 1.0, 0.001, "1080p: no enlargement")
	near(Settings.effective_ui_scale(Vector2i(2560, 1440)), 1.0, 0.001, "a larger window never shrinks the interface")
	near(Settings.effective_ui_scale(Vector2i(1600, 900)), 1.2, 0.01, "900p: 1.2")
	near(Settings.effective_ui_scale(Vector2i(1280, 720)), 1.5, 0.001, "720p: 1.5, so a 15 px label stays about 15 px on screen")
	near(Settings.effective_ui_scale(Vector2i(800, 450)), 1.5, 0.001, "never beyond the 1.5 the Interface Scale slider allows")
	Settings.ui_scale = 1.25
	near(Settings.effective_ui_scale(Vector2i(1280, 720)), 1.5, 0.001, "the player's own scale multiplies, still capped at 1.5")
	Settings.ui_scale = 0.75
	near(Settings.effective_ui_scale(Vector2i(1280, 720)), 1.125, 0.001, "a smaller own scale is respected")
	Settings.ui_scale = 1.0
	Settings.ui_auto = false
	near(Settings.effective_ui_scale(Vector2i(1280, 720)), 1.0, 0.001, "with the option off only Interface Scale counts")
	Settings.ui_auto = true
	Settings.control_mode = "mobile"
	near(Settings.effective_ui_scale(Vector2i(1920, 864)), 1.0, 0.001, "touch play keeps the scale its layout was drawn for")
	Settings.control_mode = "pc"
	Settings.hold_design_scale(true)
	near(Settings.effective_ui_scale(Vector2i(1280, 720)), 1.0, 0.001, "a pixel-placed full-screen menu keeps the design scale")
	Settings.hold_design_scale(false)
	near(Settings.effective_ui_scale(Vector2i(1280, 720)), 1.5, 0.001, "and gives it back")
	Settings.ui_scale = saved[0]
	Settings.ui_auto = saved[1]
	Settings.control_mode = saved[2]
	Settings._on_window_resized()
	done()

func test_touch_text_raises_small_labels_only() -> void:
	var saved: String = Settings.control_mode
	var holder := Control.new()
	host.add_child(holder)
	var reading := UITheme.label("Speak with Elder Maelis by the hearth.", 15)
	var badge := UITheme.label("Alt+Q", 11)
	var already := UITheme.label("A larger heading", 30)
	for l in [reading, badge, already]:
		holder.add_child(l)
	Settings.control_mode = "pc"
	TouchText.enlarge(reading)
	eq(reading.get_theme_font_size(&"font_size"), 15, "keyboard and mouse play leaves text alone")
	Settings.control_mode = "mobile"
	TouchText.enlarge(reading)
	TouchText.enlarge(badge)
	TouchText.enlarge(already)
	eq(reading.get_theme_font_size(&"font_size"), TouchText.MIN_SIZE, "reading text is raised in touch play")
	eq(badge.get_theme_font_size(&"font_size"), 11, "a short key badge sits inside art and is left alone")
	eq(already.get_theme_font_size(&"font_size"), 30, "text already large is untouched")
	Settings.control_mode = saved
	holder.free()
	done()

func test_connection_messages_say_what_to_do() -> void:
	var cant := Official.describe_failure(HTTPRequest.RESULT_CANT_RESOLVE, "https://play.example.com", false)
	ok(cant.contains("play.example.com") and cant.contains("typing") , "a name that does not resolve points at the address: " + cant)
	var refused := Official.describe_failure(HTTPRequest.RESULT_CANT_CONNECT, "https://203.0.113.5:8443", false)
	ok(refused.contains("203.0.113.5:8443") and refused.contains("turned off") and refused.contains("firewall"), "a refused connection says server or firewall: " + refused)
	var tls := Official.describe_failure(HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR, "https://play.example.com", false)
	ok(tls.contains("certificate file") and tls.contains("Advanced"), "a trust failure points at Server Settings > Advanced: " + tls)
	var pinned := Official.describe_failure(HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR, "https://home.example.com:8443", true)
	ok(pinned.contains("does not match"), "with a certificate file chosen the message says it does not match: " + pinned)
	var slow := Official.describe_failure(HTTPRequest.RESULT_TIMEOUT, "https://play.example.com", false)
	ok(slow.contains("did not answer in time"), "a time-out says so: " + slow)
	for code in [HTTPRequest.RESULT_CANT_RESOLVE, HTTPRequest.RESULT_CANT_CONNECT, HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR, HTTPRequest.RESULT_TIMEOUT, 99]:
		ok(not Official.describe_failure(code, "https://x.example", false).contains("verified encrypted"), "no jargon in the message for code %d" % code)
	done()

func test_version_messages_say_who_is_older() -> void:
	var newer := Official.describe_version_mismatch(17, 16, "abc123")
	ok(newer.contains("Update the game") and newer.contains("abc123"), "a newer server asks the player to update: " + newer)
	var older := Official.describe_version_mismatch(15, 16)
	ok(older.contains("server owner") and older.contains("offline"), "an older server asks its owner to update: " + older)
	var theirs := Net.version_refusal(16, 15)
	ok(theirs.contains("older") and theirs.contains("16") and theirs.contains("15") and theirs.contains("Update your game"), "an older client is told to update: " + theirs)
	var ours := Net.version_refusal(16, 17)
	ok(ours.contains("16") and ours.contains("17") and ours.contains("host or server owner"), "a newer client is told the host is behind: " + ours)
	done()

func test_minimap_render_covers_its_widest_zoom() -> void:
	# at Wide (42 m) the visible disc is 42 / MASK_R = 55 m across from the centre; the render has to be larger than that or the
	# "disc about to slide off the render" test is true on every frame and the whole map is redrawn 60 times a second
	var mm := MiniMap.new()
	host.add_child(mm)
	var widest: float = MiniMap.ZOOMS[MiniMap.ZOOMS.size() - 1] / MiniMap.MASK_R
	ok(mm._render_r - widest - 1.0 >= 2.0, "the render radius %.1f m leaves at least 2 m of slack beyond the Wide disc (%.1f m)" % [mm._render_r, widest])
	ok(MiniMap.PC_HZ <= 30.0 and MiniMap.PC_HZ > MiniMap.LITE_HZ, "the icon layers are redrawn at a fixed rate, not every frame")
	mm.queue_free()
	done()
