class_name HeroRosterWindow
extends UIWindow
## The hero register at a camp (bh-007, Wyman Outpost): every hero present with their class, level, tier emblem and
## guild, what they are doing, and where you stand among them. Opened from the register board or from the camp
## commander. Sorted by level (tier breaks ties); your own row is highlighted.

var camp: StringName = &"wyman_outpost"
var _list: VBoxContainer
var _standing: Label
var _promo: Label

func _init() -> void:
	super._init("Hero Register", Vector2(1240, 860))

func open_camp(p_camp: StringName) -> void:
	camp = p_camp
	var md := DB.map_def(camp)
	set_title("Hero Register — %s" % (md.display_name if md else "Camp"))
	Game.ui_root.open(&"hero_roster")

func _build() -> void:
	var intro := UITheme.label("Every hero in camp signs here: class, level, tier, and the guild that vouches for them.", 18, UITheme.TEXT_DIM, UITheme.body_font())
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(intro)
	var head := _row_box(true)
	for col in [["", 56], ["Hero", 330], ["Class", 120], ["Level", 90], ["Tier", 250], ["Guild", 300]]:
		var l := UITheme.label(col[0], 17, UITheme.BRONZE, UITheme.body_bold())
		l.custom_minimum_size.x = col[1]
		head.add_child(l)
	body.add_child(head)
	var w := inset()
	w.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(w)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	w.add_child(scroll)
	_list = vbox(4)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)
	# the footer sits clear of the frame's corner ornaments
	var foot := MarginContainer.new()
	foot.add_theme_constant_override("margin_left", 22)
	foot.add_theme_constant_override("margin_right", 22)
	body.add_child(foot)
	var fv := vbox(2)
	foot.add_child(fv)
	_standing = UITheme.label("", 20, UITheme.GOLD, UITheme.body_bold())
	fv.add_child(_standing)
	_promo = UITheme.label("", 17, UITheme.TEXT, UITheme.body_font())
	_promo.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fv.add_child(_promo)

func _row_box(header := false) -> HBoxContainer:
	var h := hbox(10)
	h.custom_minimum_size.y = 30 if header else 50
	return h

## Heroes present at the camp (NPC definitions with a hero level on this map), plus the player.
static func entries(camp_id: StringName, hero: HeroData) -> Array:
	var out := []
	for d: NpcDef in DB.npcs.values():
		if d.map == camp_id and d.is_hero():
			out.append({"name": d.display_name, "class": d.hero_class, "level": d.hero_level, "tier": d.hero_tier, "guild": d.hero_guild,
				"note": d.hero_note, "you": false})
	if hero:
		out.append({"name": hero.hero_name, "class": hero.cls.id, "level": hero.progress.level, "tier": hero.tier, "guild": hero.guild,
			"note": "You", "you": true})
	out.sort_custom(func(a, b):
		if a.level != b.level:
			return a.level > b.level
		if a.tier != b.tier:
			return a.tier > b.tier
		return String(a.name) < String(b.name))
	return out

func refresh() -> void:
	for c in _list.get_children():
		c.queue_free()
	var hero := Game.hero
	var list := entries(camp, hero)
	var rank := 0
	for i in list.size():
		var e: Dictionary = list[i]
		if e.you:
			rank = i + 1
		var row := PanelContainer.new()
		var st := StyleBoxFlat.new()
		st.bg_color = Color(0.2, 0.15, 0.06, 0.92) if e.you else (Color(1, 1, 1, 0.035) if i % 2 == 0 else Color(0, 0, 0, 0.0))
		st.set_corner_radius_all(3)
		st.content_margin_left = 10
		st.content_margin_right = 10
		st.content_margin_top = 2
		st.content_margin_bottom = 2
		if e.you:
			st.set_border_width_all(2)
			st.border_color = UITheme.GOLD
		row.add_theme_stylebox_override("panel", st)
		var h := _row_box()
		row.add_child(h)
		var em := TextureRect.new()
		em.custom_minimum_size = Vector2(56, 46)
		em.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		em.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		if int(e.tier) > 0:
			em.texture = UIArt.tex(DataGuilds.emblem_path(int(e.tier)))
		h.add_child(em)
		var nv := vbox(0)
		nv.custom_minimum_size.x = 330
		nv.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(nv)
		nv.add_child(UITheme.label(String(e.name), 20, UITheme.GOLD if e.you else UITheme.PARCHMENT, UITheme.body_bold()))
		nv.add_child(UITheme.label("You" if e.you else String(e.note), 15, UITheme.TEXT_DIM, UITheme.body_font()))
		var cd := DB.class_def(StringName(e["class"]))
		_cell(h, cd.display_name if cd else String(e["class"]).capitalize(), 120)
		_cell(h, str(e.level), 90, UITheme.number_font(), 22)
		var t := DataGuilds.tier(int(e.tier))
		var tl := _cell(h, DataGuilds.tier_name(int(e.tier)), 250)
		tl.add_theme_color_override("font_color", t.color)
		var g := DataGuilds.guild(StringName(e.guild))
		var gh := hbox(8)
		gh.custom_minimum_size.x = 300
		gh.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(gh)
		if not g.is_empty():
			var cr := TextureRect.new()
			cr.texture = UIArt.tex(g.crest)
			cr.custom_minimum_size = Vector2(34, 34)
			cr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			cr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			gh.add_child(cr)
		var gl := UITheme.label(String(g.get("name", "Independent")), 18, (g.get("color", UITheme.TEXT_DIM) as Color).lightened(0.25), UITheme.body_font())
		gh.add_child(gl)
		_list.add_child(row)
	_standing.text = "You rank %d of %d heroes at this camp." % [rank, list.size()] if hero else ""
	if hero:
		var p := GuildRules.next_promotion(hero)
		if hero.guild == &"":
			_promo.text = "Complete the opening story errands to earn Class E, or register at Swordfin Hall or Lantern House. Join a guild for further promotions."
		elif p.get("ok", false):
			_promo.text = "You qualify for automatic promotion to %s (%d gold)." % [DataGuilds.tier_name(int(p.rank)), int(p.fee)]
		elif int(p.get("rank", -1)) > 0:
			var need := "Level %d" % int(p.get("level", 0))
			if String(p.get("deed", "")) != "":
				need += " and: " + String(p.deed)
			_promo.text = "Next tier: %s — needs %s." % [DataGuilds.tier_name(int(p.rank)), need]
		else:
			_promo.text = ""

func _cell(h: HBoxContainer, text: String, w: float, font: Font = null, size := 19) -> Label:
	var l := UITheme.label(text, size, UITheme.TEXT, font if font else UITheme.body_font())
	l.custom_minimum_size.x = w
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(l)
	return l
