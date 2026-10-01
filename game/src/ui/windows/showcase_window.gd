class_name ShowcaseWindow
extends UIWindow
## bh-027: Showcase. After a player agrees to show their gear (Net.request_showcase), both heroes stand side by side:
## each on a turning plinth wearing what they wear, with every equipped piece and weapon laid out beside them (hover for
## the item's card). No stats — only what they wear. Each side shows the hero's guild; click it for the guild up close.

const SLOTS := [&"main_weapon", &"sub_weapon", &"helm", &"inner_garment", &"armor", &"leggings", &"gloves_1", &"gloves_2",
	&"boots_1", &"boots_2", &"accessory_1", &"accessory_2", &"accessory_3", &"accessory_4"]
const CELL := 58.0

var _mine := {}
var _theirs := {}
var _cols: HBoxContainer

func _init() -> void:
	super._init("Showcase", Vector2(1640, 960))

func show_pair(mine: Dictionary, theirs: Dictionary) -> void:
	_mine = mine
	_theirs = theirs
	if Game.ui_root:
		Game.ui_root.open(&"showcase")

func _build() -> void:
	_cols = hbox(26)
	_cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_cols)

func refresh() -> void:
	for c in _cols.get_children():
		_cols.remove_child(c)
		c.queue_free()
	_cols.add_child(_side(_mine, true))
	var sep := VSeparator.new()
	_cols.add_child(sep)
	_cols.add_child(_side(_theirs, false))

## A hero rebuilt from a Showcase pack: class, level, look and equipped gear, nothing else.
static func hero_from_pack(pack: Dictionary) -> HeroData:
	var cls := DB.class_def(StringName(pack.get("cls", "knight")))
	if cls == null:
		cls = DB.class_def(&"knight")
	var h := HeroData.new()
	h.setup(cls, GuildRules.clean_alias(String(pack.get("name", "Hero"))))
	var lk = pack.get("look", {})
	h.look = HeroLook.to_save(HeroLook.sanitize(lk)) if lk is Dictionary else {}
	var eq = pack.get("equipment", {})
	if eq is Dictionary:
		h.equipment.from_dict(eq)
	return h

func _side(pack: Dictionary, mine: bool) -> Control:
	var col := vbox(10)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var h := hero_from_pack(pack)
	var cd := DB.class_def(StringName(pack.get("cls", "knight")))
	var head := hbox(12)
	col.add_child(head)
	var nm := UITheme.title("%s%s" % [h.hero_name, "  (you)" if mine else ""], 30, UITheme.GOLD)
	nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(nm)
	col.add_child(UITheme.label("Level %d %s · %s" % [int(pack.get("level", 1)), cd.display_name if cd else "Hero", DataGuilds.tier_name(int(pack.get("tier", 0)))],
		17, UITheme.TEXT_DIM, UITheme.body_bold()))
	col.add_child(_guild_row(pack.get("guild", {})))
	var row := hbox(16)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(row)
	var pv := CharacterPreview.new(Vector2i(380, 600))
	pv.custom_minimum_size = Vector2(290, 540)
	pv.auto_rotate = true
	row.add_child(pv)
	pv.ready.connect(func() -> void: pv.show_class(h.cls.id, h), CONNECT_ONE_SHOT)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 8)
	row.add_child(grid)
	for slot in SLOTS:
		var it := h.equipment.get_item(slot)
		var cell := hbox(8)
		var s := ItemSlot.new(ItemSlot.Kind.DISPLAY, CELL)
		s.custom_minimum_size = Vector2(CELL, CELL)
		s.drag_enabled = false
		s.glyph = UIArt.tex("slots/glyph_%s.png" % InventoryWindow.GLYPH[slot])
		s.set_item(it)
		if it != null:
			TooltipLayer.attach(s, func() -> Control: return Tips.item(it))
		cell.add_child(s)
		var l := UITheme.label(it.display_name() if it else "—", 14, BH.rarity_color(it.rarity) if it else UITheme.TEXT_DIM, UITheme.body_bold())
		l.custom_minimum_size = Vector2(150, 0)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		cell.add_child(l)
		grid.add_child(cell)
	return col

func _guild_row(g: Variant) -> Control:
	var row := hbox(10)
	var d: Dictionary = g if g is Dictionary else {}
	if d.is_empty():
		row.add_child(UITheme.label("Not in a guild", 18, UITheme.TEXT_DIM, UITheme.body_font()))
		return row
	var tex := _banner_of(d)
	var b := Button.new()
	b.text = "  %s  ›" % String(d.get("name", "Guild"))
	b.icon = tex
	b.expand_icon = true
	b.add_theme_constant_override("icon_max_width", 34)
	b.custom_minimum_size = Vector2(0, 54)
	b.add_theme_font_size_override("font_size", 20)
	b.tooltip_text = "Click to see the guild's banner and info"
	b.pressed.connect(func() -> void:
		Audio.play_ui(&"ui_click")
		var w := Game.ui_root.window(&"guild_detail") as GuildDetailWindow
		if w:
			w.show_guild(_as_info(d), tex))
	row.add_child(b)
	return row

## A guild profile from a Showcase pack, in GuildRegistry.info() shape.
static func _as_info(d: Dictionary) -> Dictionary:
	var hero := Game.hero
	var gid := StringName(String(d.get("id", "")))
	if hero and DataGuilds.GUILDS.has(gid):
		var canon := GuildRegistry.info(hero, gid)
		canon["name"] = String(d.get("name", canon.name))
		return canon
	return {"id": "", "name": String(d.get("name", "Guild")), "motto": String(d.get("motto", "")), "master": String(d.get("master", "")),
		"level": int(d.get("level", 1)), "members": int(d.get("members", 1)), "info": String(d.get("info", "")),
		"color": Color(String(d.get("color", "c9a24a"))) if Color.html_is_valid(String(d.get("color", ""))) else UITheme.GOLD,
		"passives": d.get("passives", {}), "perk_text": [], "features": []}

static func _banner_of(d: Dictionary) -> Texture2D:
	var t := GuildRegistry.bytes_texture(d.get("banner", PackedByteArray()))
	if t != null:
		return t
	var gid := StringName(String(d.get("id", "")))
	if DataGuilds.GUILDS.has(gid):
		return UIArt.tex(String(DataGuilds.guild(gid).banner))
	return GuildBannerArt.texture(d.get("style", {}))
