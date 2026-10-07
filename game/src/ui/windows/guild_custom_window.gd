class_name GuildCustomWindow
extends UIWindow
## Your Guild (bh-017): give the guild you joined any name you like and fly your own banner. The name can be changed as
## often as you please; the banner is any picture (cropped to 2:3 and saved with the hero). Opens after the first
## registration, from the Guild House board and from the Character window.

const PICTURE_FILTERS := ["*.png, *.jpg, *.jpeg, *.webp, *.bmp, *.tga ; Pictures"]
const MAX_PICTURE_BYTES := 24 * 1024 * 1024

var _official: Label
var _name_edit: LineEdit
var _banner_rect: TextureRect
var _banner_frame: PanelContainer
var _banner_name: Label
var _status: Label
var _pick: Button
var _clear: Button
var _dialog: FileDialog

func _init() -> void:
	super._init("Your Guild", Vector2(1220, 700))      # bh-041: its content always needed ~1196

func _build() -> void:
	Events.guild_customised.connect(_on_changed)
	Events.guild_joined.connect(func(_g: StringName, _f: bool) -> void: _on_changed())
	get_window().files_dropped.connect(_on_files_dropped)
	var cols := hbox(30)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	# the banner, hung on a pole
	var left := vbox(10)
	left.custom_minimum_size = Vector2(330, 0)
	left.alignment = BoxContainer.ALIGNMENT_CENTER
	cols.add_child(left)
	_banner_frame = PanelContainer.new()
	_banner_frame.custom_minimum_size = Vector2(300, 452)
	_banner_frame.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	left.add_child(_banner_frame)
	_banner_rect = TextureRect.new()
	_banner_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_banner_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_banner_rect.custom_minimum_size = Vector2(280, 420)
	_banner_frame.add_child(_banner_rect)
	_banner_name = UITheme.title("", 22, UITheme.GOLD)
	_banner_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(_banner_name)
	# the controls
	var right := vbox(12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	right.add_child(section("Guild name"))
	_official = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	right.add_child(_official)
	var row := hbox(10)
	right.add_child(row)
	_name_edit = LineEdit.new()
	_name_edit.max_length = GuildRules.ALIAS_MAX
	_name_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name_edit.custom_minimum_size = Vector2(0, 48)
	_name_edit.add_theme_font_size_override("font_size", 24)
	_name_edit.text_submitted.connect(func(_t: String) -> void: _save_name())
	row.add_child(_name_edit)
	row.add_child(button("Save Name", _save_name, &"PrimaryButton", 170.0))
	var row2 := hbox(10)
	right.add_child(row2)
	row2.add_child(button("Use the Guild's Own Name", func() -> void:
		_name_edit.text = ""
		_save_name(), &"", 300.0))
	right.add_child(UITheme.label("Anything goes: your guild, your name (up to %d characters). Change it whenever you like." % GuildRules.ALIAS_MAX, 16, UITheme.TEXT_DIM, UITheme.body_font()))
	right.add_child(section("Banner"))
	var row3 := hbox(10)
	right.add_child(row3)
	_pick = button("Upload a Picture...", _pick_picture, &"PrimaryButton", 300.0)
	row3.add_child(_pick)
	_clear = button("Remove Picture", func() -> void:
		GuildRules.clear_banner(Game.hero)
		_say("Banner picture removed - the guild's own banner flies again.", false), &"", 220.0)
	row3.add_child(_clear)
	var hint := UITheme.label("Any PNG, JPG or WebP picture works. It is cropped to a tall banner and saved with your hero, so it stays " +
		"after you quit. On a computer you can also drag a picture file onto the game window while this window is open.", 16, UITheme.TEXT_DIM, UITheme.body_font())
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(hint)
	_status = UITheme.label("", 18, UITheme.GOLD, UITheme.body_bold())
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_status)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(spacer)

func refresh() -> void:
	var hero := Game.hero
	if hero == null:
		return
	var member := GuildRules.can_customise(hero)
	var g := GuildRegistry.info(hero, hero.guild)
	var accent: Color = g.color if not g.is_empty() else UITheme.TEXT_DIM
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.1, 0.075, 0.06, 0.95)
	st.set_border_width_all(5)
	st.border_color = accent
	st.set_corner_radius_all(3)
	st.set_content_margin_all(8)
	_banner_frame.add_theme_stylebox_override("panel", st)
	_banner_rect.texture = GuildRules.banner_or_default(hero)
	_banner_name.text = GuildRules.display_name(hero)
	_banner_name.add_theme_color_override("font_color", accent.lightened(0.3))
	var own := hero.guild == GuildRegistry.OWN
	_official.text = ("You lead: %s" % String(g.name) if own else "You joined: %s" % String(g.name)) if member else "You are not in a guild yet. Register at the Guild House, found your own (%s), then come back to name it." % Settings.binding_text(&"guild")
	_name_edit.editable = member
	_name_edit.placeholder_text = String(g.get("name", "Your guild's name")) if member else "Join a guild first"
	var shown := String(hero.own_guild.get("name", "")) if own else hero.guild_alias
	if _name_edit.text != shown and not _name_edit.has_focus():
		_name_edit.text = shown
	_pick.disabled = not member
	_clear.disabled = not member or hero.guild_banner.is_empty()

func _on_changed() -> void:
	if visible:
		refresh()

func _say(text: String, bad: bool) -> void:
	_status.text = text
	_status.add_theme_color_override("font_color", UITheme.BAD if bad else UITheme.GOOD)

func _save_name() -> void:
	var hero := Game.hero
	if hero == null:
		return
	var err := GuildRules.set_alias(hero, _name_edit.text)
	if err != "":
		_say(err, true)
		return
	_name_edit.text = String(hero.own_guild.get("name", "")) if hero.guild == GuildRegistry.OWN else hero.guild_alias
	_say("Your guild is now called \"%s\"." % GuildRules.display_name(hero), false)
	Audio.play_ui(&"ui_open")

# ---- the picture -------------------------------------------------------------------------------------------------

func _pick_picture() -> void:
	if _dialog == null:
		_dialog = FileDialog.new()
		_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
		_dialog.access = FileDialog.ACCESS_FILESYSTEM
		_dialog.use_native_dialog = true
		_dialog.title = "Choose a banner picture"
		_dialog.filters = PackedStringArray(PICTURE_FILTERS)
		_dialog.file_selected.connect(_on_file_picked)
		add_child(_dialog)
	_dialog.popup_centered_ratio(0.7)

func _on_files_dropped(files: PackedStringArray) -> void:
	if visible and not files.is_empty() and GuildRules.can_customise(Game.hero):
		_on_file_picked(files[0])

func _on_file_picked(path: String) -> void:
	var hero := Game.hero
	if hero == null:
		return
	var img := load_picture(path)
	if img == null:
		_say("That file could not be read as a picture.", true)
		return
	var err := GuildRules.set_banner(hero, img)
	if err != "":
		_say(err, true)
		return
	_say("Your banner is up!", false)
	Audio.play_ui(&"ui_open")

## Read a picture file (PNG, JPG, WebP, BMP, TGA), or null when it is missing, huge or not a picture.
static func load_picture(path: String) -> Image:
	if path == "" or not FileAccess.file_exists(path):
		return null
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.is_empty() or bytes.size() > MAX_PICTURE_BYTES:
		return null
	return picture_from_bytes(bytes, path.get_extension().to_lower())

static func picture_from_bytes(bytes: PackedByteArray, ext := "") -> Image:
	var img := Image.new()
	var err := ERR_FILE_UNRECOGNIZED
	match ext:
		"png": err = img.load_png_from_buffer(bytes)
		"jpg", "jpeg": err = img.load_jpg_from_buffer(bytes)
		"webp": err = img.load_webp_from_buffer(bytes)
		"bmp": err = img.load_bmp_from_buffer(bytes)
		"tga": err = img.load_tga_from_buffer(bytes)
	if err != OK:
		# wrong or missing extension: try each format in turn
		for f in ["png", "jpg", "webp", "bmp", "tga"]:
			if f == ext:
				continue
			img = Image.new()
			match f:
				"png": err = img.load_png_from_buffer(bytes)
				"jpg": err = img.load_jpg_from_buffer(bytes)
				"webp": err = img.load_webp_from_buffer(bytes)
				"bmp": err = img.load_bmp_from_buffer(bytes)
				"tga": err = img.load_tga_from_buffer(bytes)
			if err == OK:
				break
	return img if err == OK and not img.is_empty() else null
