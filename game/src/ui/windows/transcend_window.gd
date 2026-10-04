class_name TranscendWindow
extends UIWindow
## The Grand Master's window (Class Transcendence), opened from any Guild House Grand Master.
##
## Top: the hero's class, starting class, level, advancements done and what the next one needs.
## Below, by stage:
##   no advancement  the first transcendence: role, its three skills and three talents, colours, its gear, and
##                   Transcend (or why not yet). The two master classes can be previewed (locked).
##   first done      the two master classes side by side; choose one, review, then Confirm or Cancel. Permanent.
##   master          the master class and the whole lineage; both advancements are complete.
## Every action re-checks the hero's current state (ClassTranscendence.can_transcend), never what the window last drew.

var hero: HeroData
var _head: VBoxContainer
var _content: VBoxContainer
var _status: Label
var _selected: StringName = &""
var _preview_masters := false
var _busy := false

func _init() -> void:
	super._init("Class", Vector2(1500, 900))
	modal = true

func _build() -> void:
	_head = vbox(4)
	body.add_child(_head)
	_status = UITheme.label("", 16, UITheme.TEXT_DIM, UITheme.body_font())
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(_status)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(sc)
	_content = vbox(14)
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(_content)
	var foot := hbox(12)
	body.add_child(foot)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(spacer)
	foot.add_child(button("Skills", func() -> void: Game.ui_root.open(&"skills"), &"", 140.0))
	foot.add_child(button("Talents", func() -> void: Game.ui_root.open(&"talents"), &"", 140.0))
	foot.add_child(button("Close", close_window, &"", 140.0))

func open() -> void:
	_selected = &""
	_preview_masters = false
	_busy = false
	super.open()

func refresh() -> void:
	hero = Game.hero
	if hero == null or _head == null:
		return
	_clear(_head)
	_clear(_content)
	var cid := ClassTranscendence.current_class_id(hero)
	var done := ClassTranscendence.completed_steps(hero)
	_head.add_child(UITheme.title("Class: %s" % ClassTranscendence.current_class_name(hero), 34, ClassTranscendence.label_color(cid)))
	var line: Array[String] = []
	for id in ClassTranscendence.lineage(hero):
		line.append(DataTranscendence.name_of(id))
	_head.add_child(UITheme.label("Starting class: %s   ·   Level %d   ·   Advancements: %d of 2   ·   Path: %s" % [
		DataTranscendence.name_of(hero.cls.id), hero.progress.level, done, "  >  ".join(line)], 18, UITheme.PARCHMENT, UITheme.body_bold()))
	var nl := ClassTranscendence.next_level(hero)
	var next_txt := "Both advancements are complete." if nl == 0 else (
		"Next advancement: available now." if hero.progress.level >= nl else "Next advancement: requires level %d (you are %d)." % [nl, hero.progress.level])
	_head.add_child(UITheme.label(next_txt, 17, UITheme.GOOD if nl != 0 and hero.progress.level >= nl else UITheme.TEXT, UITheme.body_font()))
	_status.text = _pending_text()
	match done:
		0:
			_stage_first()
		1:
			_stage_master()
		_:
			_stage_complete()

func _pending_text() -> String:
	if Official.active and TranscendFlow.pending != &"":
		return "Waiting for the official server to confirm your %s save. Other players see your new class once it is confirmed." % DataTranscendence.name_of(TranscendFlow.pending)
	return ""

# ---- Stages -----------------------------------------------------------------------------------------------------

func _stage_first() -> void:
	var choices := ClassTranscendence.valid_next_choices(hero)
	if choices.is_empty():
		return
	var first: StringName = choices[0]
	var why := ClassTranscendence.can_transcend(hero, first)
	# the action first, so it is never below the fold on a small screen
	var row := hbox(12)
	_content.add_child(row)
	var b := button("Transcend to %s" % DataTranscendence.name_of(first), func() -> void: _do_first(first), &"PrimaryButton", 320.0)
	b.disabled = why != "" or _busy
	row.add_child(b)
	if why != "":
		row.add_child(UITheme.label(why, 17, UITheme.BAD, UITheme.body_bold()))
	else:
		row.add_child(UITheme.label("You keep your level, points, skills, talents, gear and progress.", 16, UITheme.TEXT_DIM, UITheme.body_font()))
	_content.add_child(_card(first, why == "", false))
	var pv := button("Hide the master classes" if _preview_masters else "Preview the master classes", func() -> void:
		_preview_masters = not _preview_masters
		refresh(), &"", 300.0)
	_content.add_child(pv)
	if _preview_masters:
		var masters := hbox(14)
		_content.add_child(masters)
		for m in DataTranscendence.children_of(first):
			var c := _card(m, false, true)
			c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			masters.add_child(c)
		_content.add_child(UITheme.label("Requires level 120 and %s." % DataTranscendence.name_of(first), 16, UITheme.TEXT_DIM, UITheme.body_font()))

func _stage_master() -> void:
	var choices := ClassTranscendence.valid_next_choices(hero)
	_content.add_child(UITheme.label("Choose one master class. The choice is permanent in this update; resetting skills or talents does not change it.",
		17, UITheme.PARCHMENT, UITheme.body_bold()))
	if _selected != &"":
		_content.add_child(_review(_selected))
	var row := hbox(14)
	_content.add_child(row)
	for m in choices:
		var ok := ClassTranscendence.can_transcend(hero, m) == ""
		var col := vbox(8)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(col)
		var target: StringName = m
		var b := button("Choose %s" % DataTranscendence.name_of(m), func() -> void:
			_selected = target
			refresh(), &"PrimaryButton" if _selected == m else &"", 280.0)
		b.disabled = not ok or _busy
		col.add_child(b)
		col.add_child(_card(m, ok, false, _selected == m))
	var why := ClassTranscendence.can_transcend(hero, choices[0]) if not choices.is_empty() else ""
	if why != "":
		var wl := UITheme.label(why, 18, UITheme.BAD, UITheme.body_bold())
		_content.add_child(wl)
		_content.move_child(wl, 1)

func _review(target: StringName) -> Control:
	var p := inset()
	var v := vbox(8)
	p.add_child(v)
	v.add_child(UITheme.title("Review: %s" % DataTranscendence.name_of(target), 24, ClassTranscendence.label_color(target)))
	var other: Array = DataTranscendence.children_of(DataTranscendence.parent_of(target)).filter(func(x): return x != target)
	var lines := [
		"You become a %s. Your path will be %s > %s > %s." % [DataTranscendence.name_of(target), DataTranscendence.name_of(hero.cls.id),
			DataTranscendence.name_of(DataTranscendence.parent_of(target)), DataTranscendence.name_of(target)],
		"You gain three skills and three talents at level 1, and the %s trait." % String(DataTranscendence.SIGNATURES.get(target, {}).get("name", "")),
		"%s will no longer be available to this hero." % (DataTranscendence.name_of(other[0]) if not other.is_empty() else "The other master class"),
		"This choice is permanent."]
	for l in lines:
		var lb := UITheme.label(l, 17, UITheme.PARCHMENT, UITheme.body_font())
		lb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(lb)
	var row := hbox(12)
	v.add_child(row)
	var ok := button("Confirm", func() -> void: _do_master(target), &"PrimaryButton", 200.0)
	ok.disabled = _busy or ClassTranscendence.can_transcend(hero, target) != ""
	row.add_child(ok)
	row.add_child(button("Cancel", func() -> void:
		_selected = &""
		refresh(), &"", 200.0))
	return p

func _stage_complete() -> void:
	var cid := ClassTranscendence.current_class_id(hero)
	_content.add_child(_card(cid, true, false, true))
	_content.add_child(UITheme.label("Both available advancements are complete.", 18, UITheme.GOOD, UITheme.body_bold()))

# ---- Actions -----------------------------------------------------------------------------------------------------

func _do_first(target: StringName) -> void:
	if _busy:
		return
	_busy = true
	var res := TranscendFlow.advance(target)
	_busy = false
	if not res.ok:
		Events.notify.emit(String(res.error), &"error")
		Audio.play_ui(&"ui_error")
	refresh()      # a level-120 hero goes straight on to the master choice

func _do_master(target: StringName) -> void:
	if _busy:
		return
	_busy = true
	var res := TranscendFlow.advance(target)
	_busy = false
	_selected = &""
	if not res.ok:
		Events.notify.emit(String(res.error), &"error")
		Audio.play_ui(&"ui_error")
	refresh()

# ---- Cards ------------------------------------------------------------------------------------------------------

## One class card: name and role in its colours, what it does and what it gives up, the three skills and talents,
## its gear. `locked` marks a preview the hero cannot take yet.
func _card(id: StringName, available: bool, locked: bool, selected := false) -> PanelContainer:
	var d := DataTranscendence.info(id)
	var th := ClassTranscendence.class_theme(id)
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	var prim: Color = th.primary
	sb.bg_color = Color(prim.darkened(0.75), 0.92)
	sb.border_color = (th.accent as Color) if selected else prim.lerp(UITheme.BRONZE, 0.4)
	sb.set_border_width_all(4 if selected else 2)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 12
	sb.content_margin_bottom = 12
	p.add_theme_stylebox_override("panel", sb)
	var v := vbox(6)
	p.add_child(v)
	var head := hbox(10)
	v.add_child(head)
	var sw := ColorRect.new()
	sw.color = prim if prim.get_luminance() > 0.12 else prim.lightened(0.2)
	sw.custom_minimum_size = Vector2(26, 26)
	head.add_child(sw)
	var sw2 := ColorRect.new()
	sw2.color = th.accent
	sw2.custom_minimum_size = Vector2(26, 26)
	head.add_child(sw2)
	var stage := DataTranscendence.stage_of(id)
	head.add_child(UITheme.title(DataTranscendence.name_of(id), 28, ClassTranscendence.label_color(id)))
	var tag := "Master class (level 120)" if stage >= 2 else "First advancement (level 60)"
	if locked:
		tag += " · preview"
	head.add_child(UITheme.label(tag, 16, UITheme.TEXT_DIM, UITheme.body_font()))
	_para(v, String(d.get("role", "")), 18, UITheme.GOLD, true)
	_para(v, String(d.get("desc", "")), 16, UITheme.TEXT)
	_para(v, "Trade-off: " + String(d.get("limit", "")), 15, UITheme.TEXT_DIM)
	if DataTranscendence.SIGNATURES.has(id):
		var sg: Dictionary = DataTranscendence.SIGNATURES[id]
		v.add_child(section("Signature trait"))
		_para(v, String(sg.name), 17, ClassTranscendence.label_color(id), true)
		_para(v, DataTranscendence.signature_text(id), 15, UITheme.TEXT)
		if stage >= 2:
			_para(v, "You keep %s from your first advancement." % String(DataTranscendence.SIGNATURES.get(DataTranscendence.parent_of(id), {}).get("name", "its trait")), 14, UITheme.TEXT_DIM)
	v.add_child(section("Skills"))
	for sid in d.get("skills", []):
		var s := DB.skill(sid)
		if s == null:
			continue
		var r := hbox(8)
		v.add_child(r)
		var ic := TextureRect.new()
		ic.texture = UIArt.skill_icon(sid)
		ic.custom_minimum_size = Vector2(40, 40)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		r.add_child(ic)
		var col := vbox(1)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(col)
		col.add_child(UITheme.label("%s  ·  %s cooldown%s" % [s.display_name, _secs(s.cooldown), "  ·  needs a %s" % _req(s.requires) if s.requires != &"" else ""],
			16, UITheme.PARCHMENT, UITheme.body_bold()))
		_para(col, Tips.skill_text(s, s.resolve(1)), 14, UITheme.TEXT_DIM)
		TooltipLayer.attach(r, func() -> Control: return Tips.skill(sid, hero, Game.player as Player, true))
	v.add_child(section("Talents"))
	for tid in d.get("talents", []):
		var t: Dictionary = DataTranscendence.TALENTS[tid]
		var col2 := vbox(1)
		v.add_child(col2)
		col2.add_child(UITheme.label("%s  ·  %s" % [t.name, "one level" if t.kind == "major" else "up to level 25"], 16, UITheme.PARCHMENT, UITheme.body_bold()))
		_para(col2, DataTranscendence.talent_text(tid, 1), 14, UITheme.TEXT_DIM)
	v.add_child(section("Class gear"))
	if d.has("armor_look"):
		_para(v, "Class armour: " + String(d.armor_look), 15, UITheme.PARCHMENT)
	var gear: Array[String] = []
	for gid in d.get("gear", []):
		var b := DB.item_base(gid)
		if b:
			gear.append(b.display_name)
	_para(v, "%s. %s; from the Grand Master's armory or as loot from level %d." % [", ".join(gear),
		"For %s and its master classes" % DataTranscendence.name_of(id) if stage == 1 else "For %s only" % DataTranscendence.name_of(id),
		DataTranscendence.level_for_stage(stage)], 15, UITheme.TEXT)
	if not available and not locked and stage >= 1:
		_para(v, ClassTranscendence.can_transcend(hero, id), 15, UITheme.BAD)
	return p

func _para(parent: Control, text: String, size: int, color: Color, bold := false) -> void:
	var l := UITheme.label(text, size, color, UITheme.body_bold() if bold else UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 200
	parent.add_child(l)

static func _secs(v: float) -> String:
	return "%s s" % StatDefs._num(v)

static func _req(r: StringName) -> String:
	match r:
		&"shield": return "shield"
		&"bow": return "bow, crossbow or javelin"
		&"melee": return "melee weapon"
	return String(r)

## A skill description with its rank-1 numbers filled in ({weapon_pct} -> 210).
static func _fill(text: String, p: Dictionary) -> String:
	for k in p:
		var v = p[k]
		if v is float or v is int:
			text = text.replace("{%s}" % k, StatDefs._num(float(v)))
	return text

static func _clear(c: Control) -> void:
	for ch in c.get_children():
		c.remove_child(ch)
		ch.queue_free()
