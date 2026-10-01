class_name GuildDetailWindow
extends UIWindow
## bh-027: one guild up close — its banner enlarged, its name, motto and the words its founder wrote (Guild info), who
## leads it, its level and members, and what it grants. Opened from a Showcase, the Guild window's Guilds page and the
## Guild House counters. A guild the hero may register with offers Register / Transfer here too.

var _banner: TextureRect
var _bframe: PanelContainer
var _name: Label
var _motto: Label
var _facts: Label
var _info: Label
var _grants: Label
var _actions: HBoxContainer
var _info_dict := {}
var _tex: Texture2D

func _init() -> void:
	super._init("Guild", Vector2(1180, 820))
	modal = true

## `g` is a GuildRegistry.info() dictionary (or a guild profile from another player); `tex` its banner.
func show_guild(g: Dictionary, tex: Texture2D) -> void:
	_info_dict = g
	_tex = tex
	if Game.ui_root:
		Game.ui_root.open(&"guild_detail")

func _build() -> void:
	var cols := hbox(34)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	_bframe = PanelContainer.new()
	_bframe.custom_minimum_size = Vector2(400, 600)
	_bframe.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	cols.add_child(_bframe)
	_banner = TextureRect.new()
	_banner.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_banner.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_banner.custom_minimum_size = Vector2(380, 570)
	_bframe.add_child(_banner)
	var right := vbox(12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(right)
	_name = UITheme.title("", 36, UITheme.GOLD)
	_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_name)
	_motto = UITheme.label("", 20, UITheme.PARCHMENT, UITheme.body_font())
	_motto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_motto)
	_facts = UITheme.label("", 18, UITheme.TEXT, UITheme.body_bold())
	_facts.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_facts)
	right.add_child(section("Guild Info"))
	_info = UITheme.label("", 18, UITheme.TEXT, UITheme.body_font())
	_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_info)
	right.add_child(section("What it grants"))
	_grants = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	_grants.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(_grants)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(spacer)
	_actions = hbox(12)
	right.add_child(_actions)

func refresh() -> void:
	var g := _info_dict
	var col: Color = g.get("color", UITheme.GOLD) if g.get("color") is Color else Color(String(g.get("color", "c9a24a")))
	set_title(String(g.get("name", "Guild")))
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.08, 0.06, 0.05, 0.96)
	st.set_border_width_all(6)
	st.border_color = col
	st.set_corner_radius_all(4)
	st.set_content_margin_all(10)
	st.shadow_color = Color(col, 0.35)
	st.shadow_size = 14
	_bframe.add_theme_stylebox_override("panel", st)
	_banner.texture = _tex
	_name.text = String(g.get("name", "Guild"))
	_name.add_theme_color_override("font_color", col.lightened(0.35))
	var motto := String(g.get("motto", ""))
	_motto.text = "“%s”" % motto if motto != "" else ""
	var lines := PackedStringArray()
	if String(g.get("master", "")) != "":
		lines.append("Guildmaster: %s" % g.master)
	lines.append("Guild level %d   ·   %d members" % [int(g.get("level", 1)), int(g.get("members", 1))])
	if String(g.get("hall", "")) != "":
		lines.append(String(g.hall))
	_facts.text = "\n".join(lines)
	var info := String(g.get("info", ""))
	_info.text = info if info != "" else "Its founder has not written about it yet."
	var grants := PackedStringArray()
	for t in g.get("perk_text", []):
		grants.append("• %s per tier" % t)
	for f in g.get("features", []):
		grants.append("• %s" % f)
	var ranks: Dictionary = g.get("passives", {})
	for id in DataGuildPassives.ORDER:
		var r := int(ranks.get(String(id), 0))
		if r > 0:
			var p := DataGuildPassives.passive(id)
			grants.append("• %s %s (rank %d): %s" % ["Guild War —" if String(p.kind) == "war" else "", p.name, r, DataGuildPassives.describe(id, r)])
	_grants.text = "\n".join(grants) if not grants.is_empty() else "Fellowship, and a banner to fight under."
	for c in _actions.get_children():
		c.queue_free()
	var hero := Game.hero
	var gid := StringName(String(g.get("id", "")))
	if hero and GuildRegistry.joinable(hero, gid) and hero.guild != gid:
		var fee := GuildRules.join_fee(hero, gid)
		var verb := "Register" if hero.guild == &"" else "Transfer"
		var b := button("%s (%d gold)" % [verb, fee], func() -> void:
			var err := GuildRules.join(hero, gid)
			if err != "":
				Events.notify.emit(err, &"error")
			else:
				close_window()
				Game.ui_root.show_tier_award(hero.tier, "You joined %s" % g.name), &"PrimaryButton", 300.0)
		var err := GuildRules.join_error(hero, gid)
		b.disabled = err != ""
		b.tooltip_text = err
		_actions.add_child(b)
	_actions.add_child(button("Close", close_window, &"", 160.0))
