class_name DialogueBox
extends Control
## NPC conversation panel: portrait, name and title on an ornate plate, text that types out (click / Space / Enter
## completes the line, again advances; Tab fast-forwards through lines), highlighted keywords, numbered choice buttons
## (1-9), disabled choices shown when the graph wants them visible. Voice-ready: plays a line's "voice" id if present.

const CPS := 55.0             # characters per second
## Every {"service": ...} action a dialogue graph may use (the data tests check graphs against this list).
const SERVICES := [&"respec", &"rest", &"mystic_heal", &"promote", &"join_swordfin", &"join_lantern", &"tempo_hire",
	&"tempo_revive", &"tempo_renowned", &"field_guide", &"craft_forge", &"craft_alchemy", &"craft_workbench", &"hero_roster", &"camp_rest",
	&"guild_jobs", &"guild_jobs_swordfin", &"guild_jobs_lantern", &"socketing", &"lape_trade", &"guild_window", &"found_guild",
	&"sail_zarael", &"sail_wyman"]

var session: DialogueSession
var npc: Npc
var _panel: PanelContainer
var _portrait: TextureRect
var _name: Label
var _title: Label
var _text: RichTextLabel
var _choices: VBoxContainer
var _choice_scroll: ScrollContainer
const MAX_CHOICE_ROWS := 7
const CHOICE_ROW_H := 42.0
var _more: Label
var _typing := false
var _chars := 0.0
var _skip_held := false

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	_panel = PanelContainer.new()
	_panel.theme_type_variation = &"DialoguePanel"
	_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_panel.offset_left = -640
	_panel.offset_right = 640
	_panel.offset_top = -370
	_panel.offset_bottom = -40
	# bh-029: a long list of choices grows the panel upward (it used to push the last choices off the bottom of the
	# screen), and past MAX_CHOICE_ROWS rows the list scrolls
	_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_panel.gui_input.connect(_on_panel_input)
	add_child(_panel)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 22)
	_panel.add_child(h)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 4)
	h.add_child(pv)
	_portrait = TextureRect.new()
	_portrait.custom_minimum_size = Vector2(190, 190)
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pv.add_child(_portrait)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	h.add_child(v)
	var nh := HBoxContainer.new()
	nh.add_theme_constant_override("separation", 12)
	v.add_child(nh)
	_name = UITheme.title("", 28, UITheme.GOLD)
	nh.add_child(_name)
	_title = UITheme.label("", 17, UITheme.TEXT_DIM, UITheme.body_font())
	_title.size_flags_vertical = Control.SIZE_SHRINK_END
	nh.add_child(_title)
	_text = RichTextLabel.new()
	_text.bbcode_enabled = true
	_text.fit_content = true
	_text.scroll_active = false
	_text.custom_minimum_size = Vector2(0, 110)
	_text.add_theme_font_size_override("normal_font_size", 21)
	_text.add_theme_font_size_override("bold_font_size", 21)
	_text.add_theme_color_override("default_color", UITheme.PARCHMENT)
	_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_text)
	_choice_scroll = ScrollContainer.new()
	_choice_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_choice_scroll.follow_focus = true
	v.add_child(_choice_scroll)
	_choices = VBoxContainer.new()
	_choices.add_theme_constant_override("separation", 4)
	_choices.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_choice_scroll.add_child(_choices)
	_more = UITheme.label("", 14, UITheme.TEXT_MUTED, UITheme.body_font())
	_more.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	v.add_child(_more)

func start(p_npc: Npc, at := "") -> void:
	npc = p_npc
	_open(npc.def, at)

## A conversation with no one standing in the world (the new-game guide).
func start_def(def: NpcDef) -> void:
	npc = null
	_open(def)

func _open(def: NpcDef, at := "") -> void:
	session = DialogueSession.start(def, Game.hero)
	session.line_shown.connect(_on_line)
	session.choices_shown.connect(_on_choices)
	session.request.connect(_on_request)
	session.ended.connect(_on_ended)
	_name.text = def.display_name
	_title.text = def.title
	visible = true
	Game.ui_blocking = true
	_panel.modulate.a = 0.0
	create_tween().tween_property(_panel, "modulate:a", 1.0, 0.18)
	Audio.play_ui(&"ui_open")
	session.begin(at)

func _on_line(speaker: String, portrait: String, bb: String, index: int, count: int) -> void:
	_portrait.texture = UIArt.tex(portrait) if portrait != "" else null
	if speaker != "":
		_name.text = speaker
	for c in _choices.get_children():
		c.queue_free()
	_choice_scroll.custom_minimum_size.y = 0.0
	_text.text = bb
	_text.visible_characters = 0
	_chars = 0.0
	_typing = true
	_more.text = ("Tap to continue" if Settings.touch_mode else "Click or Space to continue") if index < count - 1 else ""
	if npc and is_instance_valid(npc):
		npc.gesture()

func _on_choices(choices: Array) -> void:
	for c in _choices.get_children():
		c.queue_free()
	var i := 0
	for ch in choices:
		var idx := i
		var b := Button.new()
		b.theme_type_variation = &"FlatButton"
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.text = "%d.  %s" % [i + 1, Dialogue.plain(Dialogue.fill(String(ch.text), Game.hero))]
		b.add_theme_font_size_override("font_size", 19)
		b.add_theme_color_override("font_color", UITheme.PARCHMENT)
		b.add_theme_color_override("font_hover_color", UITheme.GOLD)
		b.add_theme_color_override("font_disabled_color", UITheme.TEXT_MUTED)
		b.disabled = not ch.get("enabled", true)
		b.pressed.connect(func() -> void:
			Audio.play_ui(&"ui_click")
			session.choose(idx))
		b.mouse_entered.connect(func() -> void: Audio.play_ui(&"ui_hover"))
		_choices.add_child(b)
		i += 1
	_fit_choices(choices.size())
	_choices.visible = not _typing
	_more.text = ""

## Room for every choice up to MAX_CHOICE_ROWS rows (and no more than the screen allows); beyond that the list scrolls.
func _fit_choices(n: int) -> void:
	var rows := mini(n, MAX_CHOICE_ROWS)
	var room := get_viewport_rect().size.y - 40.0 - 330.0 - 40.0
	_choice_scroll.custom_minimum_size.y = minf(rows * (CHOICE_ROW_H + 4.0), maxf(CHOICE_ROW_H * 2.0, room))

func _process(delta: float) -> void:
	if not visible or not _typing:
		return
	var speed := CPS * (4.0 if _skip_held else 1.0)
	_chars += delta * speed
	var total := _text.get_total_character_count()
	_text.visible_characters = int(_chars)
	if _chars >= total:
		_finish_typing()

func _finish_typing() -> void:
	_typing = false
	_text.visible_characters = -1
	_choices.visible = true
	if _choices.get_child_count() > 0:
		(_choices.get_child(0) as Button).grab_focus.call_deferred()

func _advance() -> void:
	if session == null:
		return
	if _typing:
		_finish_typing()
		return
	if _choices.get_child_count() > 0:
		return
	session.advance()

func _on_panel_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
		_advance()

func _unhandled_input(e: InputEvent) -> void:
	if not visible:
		return
	if e is InputEventKey and e.pressed and not e.echo:
		if e.keycode in [KEY_SPACE, KEY_ENTER, KEY_KP_ENTER]:
			_advance()
			get_viewport().set_input_as_handled()
		elif e.keycode >= KEY_1 and e.keycode <= KEY_9 and not _typing:
			session.choose(e.keycode - KEY_1)
			get_viewport().set_input_as_handled()
		elif e.keycode == KEY_TAB:
			# fast-forward: finish this line and the next ones until a choice appears
			for i in 20:
				if _choices.get_child_count() > 0 or session.finished:
					break
				_finish_typing()
				session.advance()
			if visible:
				_finish_typing()
			get_viewport().set_input_as_handled()
	if e is InputEventKey and e.keycode == KEY_SHIFT:
		_skip_held = e.pressed

func _on_request(kind: StringName, arg: Variant) -> void:
	match kind:
		&"open_shop":
			var shop_id := StringName(arg)
			_open_shop_after_end.call_deferred(shop_id)
		&"heal":
			NpcServices.heal(Game.player)
		&"cutscene":
			# bh-021: the conversation steps aside for a cutscene and picks up again at `resume` afterwards
			var d: Dictionary = arg
			_play_cutscene.call_deferred(StringName(d.id), npc, String(d.get("resume", "")), session.npc if session else null)
		&"service":
			match StringName(arg):
				&"respec": _respec()
				&"rest": _rest()
				&"mystic_heal": _mystic_heal()
				&"promote": _promote()
				&"join_swordfin": _join(&"swordfin")
				&"join_lantern": _join(&"lantern")
				&"tempo_hire", &"tempo_revive", &"tempo_renowned": _open_tempo_caller.call_deferred(StringName(arg))
				&"field_guide": _open_field_guide.call_deferred()
				&"craft_forge", &"craft_alchemy", &"craft_workbench": _open_crafting.call_deferred(StringName(String(arg).trim_prefix("craft_")))
				&"hero_roster": _open_roster.call_deferred()
				&"guild_jobs", &"guild_jobs_swordfin", &"guild_jobs_lantern": _open_guild_jobs.call_deferred(StringName(String(arg).trim_prefix("guild_jobs").trim_prefix("_")))
				&"camp_rest": _camp_rest.call_deferred()
				&"socketing":
					# The choice ends the dialogue synchronously and clears npc/session.
					# Capture the definition before opening the next window deferred.
					_open_socketing.call_deferred(session.npc.display_name, session.npc.shop)
				&"lape_trade": _open_lape.call_deferred()
				&"guild_window": (func() -> void: Game.ui_root.open_guild("guilds")).call_deferred()
				&"found_guild": (func() -> void: Game.ui_root.open_guild("found" if not OwnGuild.has(Game.hero) else "overview")).call_deferred()
				# bh-029: Agdao's ship between Wyman Outpost and Zarael
				&"sail_zarael": (func() -> void: ZaraelVoyage.sail(true)).call_deferred()
				&"sail_wyman": (func() -> void: ZaraelVoyage.sail(false)).call_deferred()

func _play_cutscene(id: StringName, who: Npc, resume: String, def: NpcDef) -> void:
	close()
	if who and is_instance_valid(who):
		who.begin_talk(Game.player as Node3D)
	CutscenePlayer.play(id, func() -> void:
		if resume == "":
			if who and is_instance_valid(who):
				who.end_talk()
			return
		if who and is_instance_valid(who):
			start(who, resume)
		elif def:
			npc = null
			_open(def, resume))

func _open_crafting(station: StringName) -> void:
	# the name of that station on this map ("Angkol Les' Alchemy Table", "Field Forge", "Brannoc's Anvil"), else the generic one
	var label := String(DataCrafting.STATIONS.get(station, {}).get("name", ""))
	for s in get_tree().get_nodes_in_group(&"crafting_station"):
		if s is CraftingStation and s.station == station:
			label = s.label
			break
	close()
	Game.ui_root.open_crafting(station, label)

## bh-018: a Socket Specialist's work on your gear (SocketWindow), under their name.
func _open_socketing(who: String, shop: StringName) -> void:
	close()
	Game.ui_root.open_socketing(who, shop)

## bh-019: Lape the Ancient's trading table (LapeWindow).
func _open_lape() -> void:
	var who := npc.def.display_name if npc and npc.def else "Lape the Ancient"
	close()
	Game.ui_root.open_lape(who)

func _open_guild_jobs(gid: StringName) -> void:
	close()
	Game.ui_root.open_guild_jobs(gid)

func _open_roster() -> void:
	var camp := Game.current_map_id
	close()
	Game.ui_root.open_roster(camp)

## Rest at a camp's bonfire from a conversation (the camp healer offers it): free, sets the checkpoint.
func _camp_rest() -> void:
	close()
	var fires := get_tree().get_nodes_in_group(&"checkpoint")
	if fires.is_empty():
		Events.notify.emit("There is no bonfire here.", &"error")
		return
	(fires[0] as CampBonfire).interact(Game.player)

func _open_field_guide() -> void:
	close()
	Game.ui_root.open(&"guide")

## Veyra Ashgrave's services open the Tempo-Caller window (binding spirits, calling fallen ones back).
func _open_tempo_caller(which: StringName) -> void:
	close()
	var w := Game.ui_root.window(&"tempo_caller") as TempoCallerWindow
	if w:
		w.open_on({&"tempo_revive": &"fallen", &"tempo_renowned": &"renowned"}.get(which, &"roster"))

func _open_shop_after_end(shop_id: StringName) -> void:
	var w := Game.ui_root.window(&"shop") as ShopWindow
	if w:
		w.open_shop(shop_id)

func _respec() -> void:
	var h := Game.hero
	var pv := NpcServices.respec_preview(h)
	var cost := NpcServices.respec_cost(h.progress.level)
	Game.ui_root.ask("Unweave Your Paths", "Refund %d skill points and %d talent points for %d gold?" % [pv.skill_points, pv.talent_points, cost],
		func() -> void:
			var err := NpcServices.respec(h)
			Events.notify.emit("Your skills and talents are unwoven." if err == "" else err, &"info" if err == "" else &"error"),
		"Unweave (%d gold)" % cost)

## The Salted Marlin: pay, fade out, wake restored and Well Rested.
func _rest() -> void:
	var h := Game.hero
	var fee := NpcServices.rest_cost(h)
	var disc := GuildRules.inn_discount(h)
	var note := " (Lantern Covenant discount)" if disc > 0.0 else ""
	Game.ui_root.ask("Rest at the Salted Marlin", "Take a room for the night for %d gold%s?\nYou wake fully restored and Well Rested (+%d%% experience for %d minutes)." % [
			fee, note, roundi(HeroData.RESTED_XP * 100.0), roundi(NpcServices.REST_DURATION / 60.0)],
		func() -> void:
			var err := NpcServices.can_rest(h)
			if err != "":
				Events.notify.emit(err, &"error")
				return
			close()
			Game.ui_root.fade_rest("You rest at the Salted Marlin...", func() -> void:
				var err2 := NpcServices.rest(h, Game.player)
				if err2 != "":
					Events.notify.emit(err2, &"error")),
		"Rest (%d gold)" % fee)

func _mystic_heal() -> void:
	var h := Game.hero
	var fee := NpcServices.mystic_heal_cost(h)
	Game.ui_root.ask("Aether Mending", "Seris mends your wounds on the spot for %d gold." % fee,
		func() -> void:
			var err := NpcServices.mystic_heal(h, Game.player)
			if err != "":
				Events.notify.emit(err, &"error"),
		"Mend (%d gold)" % fee)

func _join(gid: StringName) -> void:
	var h := Game.hero
	var g := DataGuilds.guild(gid)
	var fee := GuildRules.join_fee(h, gid)
	var what := "Register as a Class E hero of %s" % g.name if h.guild == &"" else "Transfer to %s (you keep your Class %s tier)" % [g.name, DataGuilds.letter(h.tier)]
	Game.ui_root.ask(String(g.name), "%s for %d gold?" % [what, fee],
		func() -> void:
			var err := GuildRules.join(h, gid)
			if err != "":
				Events.notify.emit(err, &"error")
			else:
				Game.ui_root.show_tier_award(h.tier, "You joined %s" % g.name),
		"Join (%d gold)" % fee)

func _promote() -> void:
	var h := Game.hero
	var p := GuildRules.next_promotion(h)
	if not p.ok:
		Events.notify.emit(String(p.error), &"error")
		return
	var t := DataGuilds.tier(int(p.rank))
	Game.ui_root.ask("Promotion", "Register your promotion to Class %s — %s for %d gold?" % [t.letter, t.title, p.fee],
		func() -> void:
			var err := GuildRules.promote(h)
			if err != "":
				Events.notify.emit(err, &"error")
			else:
				Game.ui_root.show_tier_award(h.tier, "Promoted"),
		"Promote (%d gold)" % p.fee)

func _on_ended() -> void:
	close()

func close() -> void:
	if session and not session.finished:
		session.finish()
	if npc and is_instance_valid(npc):
		npc.end_talk()
	npc = null
	session = null
	visible = false
	Game.ui_blocking = false
