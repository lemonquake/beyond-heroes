class_name Hud
extends Control
## The combat HUD. Anchored regions so it holds at any 16:9 (and wider) resolution:
##   top-left     portrait, name, level, buffs / debuffs (hover for details)
##   top-centre   boss bar (name, phase, phase ticks) and the target frame
##   top-right    minimap and the objective tracker
##   bottom       HP orb · class resource · skill bar + potions · Mana orb, XP bar along the bottom edge
##   centre       interact prompt, area / level-up banners, low-HP vignette; right side: notification feed

var player: Player
var _hp_orb: HudOrb
var _mana_orb: HudOrb
var _skills: Array[SkillButton] = []
var _potions: Array[SkillButton] = []
var _xp: ArtBar
var _xp_label: Label
var _resource_bar: ArtBar
var _pips: HBoxContainer
var _resource_label: Label
var _name_label: Label
var _level_label: Label
var _tier_icon: TextureRect
var _tier_label: Label
var _tier_key := ""
var _guild_icon: TextureRect
var _rested_label: Label
var _portrait: TextureRect
var _buffs: HBoxContainer
var _debuffs: HBoxContainer
var _boss_box: VBoxContainer
var _boss_bar: ArtBar
var _boss_name: Label
var _boss_phase: Label
var _boss: Enemy
var _target_box: VBoxContainer
var _target_bar: ArtBar
var _target_name: Label
var _target_sub: Label
var _target_status: HBoxContainer
var _target: Enemy
var _target_t := 0.0
var _minimap: MiniMap
var _objective_title: Label
var _objective_text: Label
var _prompt: Label
var _prompt_panel: PanelContainer
var _feed: VBoxContainer
var _banner: VBoxContainer
var _banner_title: Label
var _banner_sub: Label
var _banner_tw: Tween
var _vignette: TextureRect
var _dodge: TextureProgressBar
# beside the HP orb (bh-006): auto-loot switch, carried load, the open Town Portal
var _side: VBoxContainer
var _auto_loot: CheckBox
var _load_bar: ProgressBar
var _load_label: Label
var _portal_row: HBoxContainer
var _portal_label: Label
var _tick := 0.0
var _status_sig := ""
var tempo_frames: TempoFrames
var party_frames: PartyFrames       # other players in a multiplayer party (bh-011), under the Tempo frames
# touch play (bh-008): the on-screen controls replace the skill plate; these are moved or hidden
var _cluster: HBoxContainer
var _plate: PanelContainer
var _top_right: VBoxContainer
var _top_center: VBoxContainer
var _mobile := false
var _quest_panels: Array[Control] = []  # directions, stage tracker, objective: top right, or the left column in touch play
var _left_col: VBoxContainer

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	_build_vignette()
	add_child(LootLabels.new())       # ground loot name tags, under every HUD panel (bh-007)
	_build_top_left()
	_build_top_center()
	_build_top_right()
	_build_bottom()
	_build_center()
	_build_feed()
	# party frames for the hero's Tempos, under the portrait
	tempo_frames = TempoFrames.new()
	tempo_frames.position = Vector2(24, 150)
	add_child(tempo_frames)
	party_frames = PartyFrames.new()
	add_child(party_frames)
	Events.notify.connect(_on_notify)
	Events.player_spawned.connect(bind)
	Events.player_leveled.connect(_on_leveled)
	Events.loot_picked.connect(_on_loot)
	Events.gold_picked.connect(_on_gold)
	Events.interact_prompt.connect(_on_prompt)
	Events.boss_engaged.connect(_on_boss)
	Events.boss_defeated.connect(_on_boss_defeated)
	Events.damage_dealt.connect(_on_damage)
	Events.map_loaded.connect(_on_map_loaded)
	# bh-007: camps, stages, champions and Olivar's restocks
	Events.camp_cleared.connect(func(_m: StringName, zone: String, left: int, _total: int) -> void:
		_feed_line("Camp cleared: %s%s" % [zone.replace("_", " ").capitalize(), (" (%d left)" % left) if left > 0 else ""], UITheme.GOOD, UIArt.ui_icon("check")))
	Events.stage_cleared.connect(func(m: StringName) -> void:
		var d := DB.map_def(m)
		banner("Stage Cleared", "%s is quiet. Olivar's merchants have new stock." % (d.display_name if d else String(m)), UITheme.GOOD))
	Events.miniboss_defeated.connect(func(id: StringName) -> void:
		banner("Champion Defeated", "%s · Olivar's merchants have new stock" % DataMinibosses.find(id).get("name", String(id)), Color(1.0, 0.7, 0.35)))
	Events.recipe_learned.connect(func(rid: StringName) -> void:
		_feed_line("Recipe learned: %s" % DataCrafting.recipe(rid).get("name", String(rid)), Color(0.6, 1.0, 0.75), UIArt.ui_icon("check")))
	Events.teleporter_discovered.connect(func(_m): banner("Waypoint Awakened", "It will carry you back here", Color(0.55, 0.97, 1.0)))
	if Game.player is Player:
		bind(Game.player)
	Settings.changed.connect(_apply_mode)
	_apply_mode()
	# bh-015: a resize, a minimise / restore or a map load lays the HUD out again from its anchors
	get_viewport().size_changed.connect(_relayout)
	Events.map_loaded.connect(func(_m: StringName) -> void: _relayout.call_deferred())

func bind(p: Node) -> void:
	player = p as Player
	if player == null:
		return
	_portrait.texture = UIArt.portrait(String(player.hero.cls.id))
	_name_label.text = player.hero.hero_name
	var kind := player.hero.cls.resource_kind
	var is_bar := kind in [&"valor", &"focus"]     # Valor and Focus are gauges; Arcane Charge and Combo are pips
	_resource_bar.visible = is_bar
	_pips.visible = not is_bar
	_resource_bar.tick_marks = [ClassResource.STEADY_AT / 100.0] if kind == &"focus" else [0.5]
	_resource_label.text = player.hero.cls.class_resource_name
	_refresh_bar()
	if not player.hero.skills_changed.is_connected(_refresh_bar):
		player.hero.skills_changed.connect(_refresh_bar)

# ---- Build ---------------------------------------------------------------------------------------------------------

func _build_vignette() -> void:
	_vignette = TextureRect.new()
	_vignette.texture = UIArt.tex("hud/vignette_lowhp.png")
	_vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_vignette.stretch_mode = TextureRect.STRETCH_SCALE
	_vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vignette.modulate.a = 0.0
	add_child(_vignette)

func _build_top_left() -> void:
	var root := HBoxContainer.new()
	root.position = Vector2(24, 20)
	root.add_theme_constant_override("separation", 12)
	add_child(root)
	var pf := PanelContainer.new()
	pf.theme_type_variation = &"GlassPanel"
	root.add_child(pf)
	_portrait = TextureRect.new()
	_portrait.custom_minimum_size = Vector2(76, 76)
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pf.add_child(_portrait)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	root.add_child(v)
	var nh := HBoxContainer.new()
	nh.add_theme_constant_override("separation", 10)
	v.add_child(nh)
	_name_label = UITheme.title("", 22, UITheme.PARCHMENT)
	nh.add_child(_name_label)
	_level_label = UITheme.label("", 18, UITheme.GOLD, UITheme.number_font())
	_level_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_level_label.add_theme_constant_override("outline_size", 4)
	nh.add_child(_level_label)
	# hero tier identifier (docs/LORE.md §5): emblem + class letter, guild crest; hover for details
	var th := HBoxContainer.new()
	th.add_theme_constant_override("separation", 6)
	v.add_child(th)
	_tier_icon = TextureRect.new()
	_tier_icon.custom_minimum_size = Vector2(30, 30)
	_tier_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tier_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	th.add_child(_tier_icon)
	_tier_label = UITheme.label("", 16, UITheme.PARCHMENT, UITheme.body_bold())
	_tier_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_tier_label.add_theme_constant_override("outline_size", 4)
	th.add_child(_tier_label)
	_guild_icon = TextureRect.new()
	_guild_icon.custom_minimum_size = Vector2(26, 26)
	_guild_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_guild_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	th.add_child(_guild_icon)
	_rested_label = UITheme.label("Well Rested", 14, Color(0.6, 0.9, 1.0))
	_rested_label.visible = false
	th.add_child(_rested_label)
	TooltipLayer.attach(th, func() -> Control: return Tips.text(_tier_tooltip(), "Hero tier") if player else null)
	_buffs = HBoxContainer.new()
	_buffs.add_theme_constant_override("separation", 4)
	v.add_child(_buffs)
	_debuffs = HBoxContainer.new()
	_debuffs.add_theme_constant_override("separation", 4)
	v.add_child(_debuffs)

func _build_top_center() -> void:
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_CENTER_TOP)
	col.offset_left = -430
	col.offset_right = 430
	col.offset_top = 16
	col.add_theme_constant_override("separation", 6)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(col)
	_top_center = col
	_boss_box = VBoxContainer.new()
	_boss_box.add_theme_constant_override("separation", 0)
	_boss_box.visible = false
	col.add_child(_boss_box)
	var bh := HBoxContainer.new()
	bh.alignment = BoxContainer.ALIGNMENT_CENTER
	bh.add_theme_constant_override("separation", 14)
	_boss_box.add_child(bh)
	_boss_name = UITheme.title("", 26, Color(1.0, 0.82, 0.62))
	bh.add_child(_boss_name)
	_boss_phase = UITheme.label("", 17, Color(0.95, 0.55, 0.45), UITheme.body_bold())
	_boss_phase.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_boss_phase.add_theme_constant_override("outline_size", 4)
	bh.add_child(_boss_phase)
	_boss_bar = ArtBar.new("hud/bar_frame_boss.png", Color(0.78, 0.08, 0.06), 64.0)
	_boss_bar.text_size = 16
	_boss_box.add_child(_boss_bar)
	_target_box = VBoxContainer.new()
	_target_box.add_theme_constant_override("separation", 0)
	_target_box.custom_minimum_size = Vector2(440, 0)
	_target_box.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_target_box.visible = false
	col.add_child(_target_box)
	var th := HBoxContainer.new()
	th.alignment = BoxContainer.ALIGNMENT_CENTER
	th.add_theme_constant_override("separation", 8)
	_target_box.add_child(th)
	_target_name = UITheme.title("", 20, UITheme.PARCHMENT)
	th.add_child(_target_name)
	_target_sub = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_target_sub.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_target_sub.add_theme_constant_override("outline_size", 4)
	th.add_child(_target_sub)
	_target_bar = ArtBar.new("hud/bar_frame_target.png", Color(0.8, 0.14, 0.1), 40.0)
	_target_bar.text_size = 14
	_target_box.add_child(_target_bar)
	_target_status = HBoxContainer.new()
	_target_status.alignment = BoxContainer.ALIGNMENT_CENTER
	_target_status.add_theme_constant_override("separation", 3)
	_target_box.add_child(_target_status)

func _build_top_right() -> void:
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	col.offset_left = -330
	col.offset_right = -24
	col.offset_top = 16
	col.alignment = BoxContainer.ALIGNMENT_BEGIN
	col.add_theme_constant_override("separation", 8)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# bh-015: anything wider than the column grows it toward the screen, never past the right edge (a long dungeon
	# name used to push the whole column, minimap first, off the screen)
	col.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	add_child(col)
	_top_right = col
	_minimap = MiniMap.new(236.0)
	_minimap.size_flags_horizontal = Control.SIZE_SHRINK_END
	col.add_child(_minimap)
	_quest_panels.append(DirectionsPanel.new())
	col.add_child(_quest_panels[0])
	_quest_panels.append(StageTracker.new())
	col.add_child(_quest_panels[1])
	var obj := PanelContainer.new()
	_quest_panels.append(obj)
	obj.theme_type_variation = &"GlassPanel"
	obj.custom_minimum_size = Vector2(300, 0)
	col.add_child(obj)
	var ov := VBoxContainer.new()
	ov.add_theme_constant_override("separation", 2)
	obj.add_child(ov)
	var oh := HBoxContainer.new()
	oh.add_theme_constant_override("separation", 6)
	ov.add_child(oh)
	var qi := TextureRect.new()
	qi.texture = UIArt.ui_icon("quest")
	qi.custom_minimum_size = Vector2(20, 20)
	qi.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	qi.modulate = UITheme.GOLD
	oh.add_child(qi)
	_objective_title = UITheme.label("", 17, UITheme.GOLD, UITheme.title_font())
	UITheme.fit_line(_objective_title)
	oh.add_child(_objective_title)
	_objective_text = UITheme.label("", 15, UITheme.TEXT, UITheme.body_font())
	_objective_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_objective_text.custom_minimum_size = Vector2(270, 0)
	ov.add_child(_objective_text)

func _build_bottom() -> void:
	# XP bar along the bottom edge
	_xp = ArtBar.new("hud/bar_frame_xp.png", Color(0.95, 0.75, 0.3), 18.0)
	_xp.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_xp.offset_left = 360
	_xp.offset_right = -360
	_xp.offset_top = -24
	_xp.offset_bottom = -6
	_xp.lag_color = Color(1, 1, 1, 0.0)
	add_child(_xp)
	_xp_label = UITheme.label("", 14, UITheme.PARCHMENT, UITheme.number_font())
	_xp_label.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_xp_label.offset_left = -200
	_xp_label.offset_right = 200
	_xp_label.offset_top = -46
	_xp_label.offset_bottom = -26
	_xp_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_xp_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	_xp_label.add_theme_constant_override("outline_size", 4)
	_xp_label.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(_xp_label)
	TooltipLayer.attach(_xp_label, _xp_tip)
	# centre cluster: HP orb | resource + skill plate | Mana orb
	var cluster := HBoxContainer.new()
	cluster.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	cluster.offset_left = -520
	cluster.offset_right = 520
	cluster.offset_top = -214
	cluster.offset_bottom = -30
	cluster.alignment = BoxContainer.ALIGNMENT_CENTER
	cluster.add_theme_constant_override("separation", 6)
	cluster.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(cluster)
	_cluster = cluster
	_hp_orb = HudOrb.new(&"hp", 168.0)
	_hp_orb.size_flags_vertical = Control.SIZE_SHRINK_END
	cluster.add_child(_hp_orb)
	TooltipLayer.attach(_hp_orb, func() -> Control: return Tips.stat(&"max_hp", player.stats, "%d / %d" % [ceili(player.hp), roundi(player.max_hp())]) if player else null)
	var mid := VBoxContainer.new()
	mid.add_theme_constant_override("separation", 4)
	mid.size_flags_vertical = Control.SIZE_SHRINK_END
	cluster.add_child(mid)
	var rh := HBoxContainer.new()
	rh.alignment = BoxContainer.ALIGNMENT_CENTER
	rh.add_theme_constant_override("separation", 8)
	mid.add_child(rh)
	_resource_label = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.title_font())
	_resource_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_resource_label.add_theme_constant_override("outline_size", 4)
	rh.add_child(_resource_label)
	_resource_bar = ArtBar.new("hud/bar_frame_resource.png", Color(1.0, 0.5, 0.15), 34.0)
	_resource_bar.custom_minimum_size = Vector2(360, 34)
	_resource_bar.tick_marks = [0.5]
	rh.add_child(_resource_bar)
	_pips = HBoxContainer.new()
	_pips.add_theme_constant_override("separation", 2)
	rh.add_child(_pips)
	TooltipLayer.attach(rh, func() -> Control: return Tips.text(player.hero.cls.resource_desc, player.hero.cls.class_resource_name) if player else null)
	var plate := PanelContainer.new()
	plate.theme_type_variation = &"GlassPanel"
	mid.add_child(plate)
	_plate = plate
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 4)
	plate.add_child(bar)
	for i in HeroData.SKILL_BAR_SIZE:
		var b := SkillButton.new(StringName("skill_%d" % (i + 1)), 66.0)
		b.index = i
		b.activated.connect(_on_slot_clicked)
		b.skill_dropped.connect(_on_skill_dropped)
		TooltipLayer.attach(b, func() -> Control: return Tips.skill(b.skill_id, player.hero, player) if player and b.skill_id != &"" else Tips.text("Empty slot. Drag a skill here from the Skills window (K).") )
		bar.add_child(b)
		_skills.append(b)
	var sep := VSeparator.new()
	bar.add_child(sep)
	for pk in [[&"potion_health", &"health_potion", 0], [&"potion_mana", &"mana_potion", 1]]:
		# the potion belt (bh-011): each key uses whatever the player bound to it; right-click or drop a consumable to change
		var pb := SkillButton.new(pk[0], 58.0)
		pb.set_potion(pk[1])
		pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var slot: int = pk[2]
		pb.set_meta(&"belt_slot", slot)
		pb.activated.connect(func(_s): if player: player.use_belt(slot))
		pb.context.connect(func(b: SkillButton) -> void: if player: BeltPicker.open(b, player.hero, slot))
		pb.item_dropped.connect(func(_b: SkillButton, it: ItemInstance) -> void: if player and it: BeltPicker.bind(player.hero, slot, it.base.id))
		TooltipLayer.attach(pb, func() -> Control: return _belt_tip(slot))
		bar.add_child(pb)
		_potions.append(pb)
	_dodge = TextureProgressBar.new()
	_dodge.texture_progress = UIArt.tex("slots/cooldown_radial.png")
	_dodge.fill_mode = TextureProgressBar.FILL_CLOCKWISE
	_dodge.nine_patch_stretch = true
	_dodge.custom_minimum_size = Vector2(26, 26)
	_dodge.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_dodge.tint_progress = Color(0.6, 0.95, 1.0, 0.9)
	_dodge.max_value = 1.0
	_dodge.step = 0.01
	bar.add_child(_dodge)
	TooltipLayer.attach(_dodge, func() -> Control: return Tips.text("Dodge (%s). Brief invulnerability while rolling." % Settings.binding_text(&"dodge")))
	_build_side()
	_mana_orb = HudOrb.new(&"mana", 168.0)
	_mana_orb.size_flags_vertical = Control.SIZE_SHRINK_END
	cluster.add_child(_mana_orb)
	TooltipLayer.attach(_mana_orb, func() -> Control: return Tips.stat(&"max_mana", player.stats, "%d / %d" % [floori(player.mana), roundi(player.max_mana())]) if player else null)

## Beside the HP orb: the Auto-Loot checkbox (always visible), the carried-load meter and the Town Portal chip.
func _build_side() -> void:
	_side = VBoxContainer.new()
	_side.add_theme_constant_override("separation", 6)
	_side.custom_minimum_size = Vector2(236, 0)
	_side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_side)
	var plate := PanelContainer.new()
	plate.theme_type_variation = &"GlassPanel"
	_side.add_child(plate)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	plate.add_child(v)
	_auto_loot = CheckBox.new()
	_auto_loot.text = "Auto-Loot"
	_auto_loot.focus_mode = Control.FOCUS_NONE
	_auto_loot.add_theme_font_size_override("font_size", 17)
	_auto_loot.button_pressed = Settings.auto_loot_enabled
	_auto_loot.toggled.connect(func(on: bool) -> void:
		if on != Settings.auto_loot_enabled:
			Settings.set_value("auto_loot_enabled", on)
			Events.notify.emit("Auto-Loot %s" % ("on: walk over drops to pick them up (%s)" % AutoLootRules.summary(Settings.auto_loot_rules, Settings.auto_loot_rarity) if on else "off"), &"info"))
	Settings.changed.connect(func() -> void:
		if is_instance_valid(_auto_loot) and _auto_loot.button_pressed != Settings.auto_loot_enabled:
			_auto_loot.set_pressed_no_signal(Settings.auto_loot_enabled))
	TooltipLayer.attach(_auto_loot, func() -> Control: return Tips.text(
		"Walk near matching drops to collect them. %s. Change categories and advanced rules in Inventory > Auto-Loot Filters or Settings > Gameplay. Gold is collected on contact." % AutoLootRules.summary(Settings.auto_loot_rules, Settings.auto_loot_rarity), "Auto-Loot"))
	v.add_child(_auto_loot)
	var lh := HBoxContainer.new()
	lh.add_theme_constant_override("separation", 6)
	v.add_child(lh)
	var li := UITheme.label("Load", 15, UITheme.TEXT_DIM, UITheme.body_bold())
	lh.add_child(li)
	_load_label = UITheme.label("", 15, UITheme.PARCHMENT, UITheme.number_font())
	_load_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_load_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	lh.add_child(_load_label)
	_load_bar = ProgressBar.new()
	_load_bar.show_percentage = false
	_load_bar.custom_minimum_size = Vector2(170, 9)
	_load_bar.max_value = 1.0
	_load_bar.step = 0.001
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.55)
	bg.set_corner_radius_all(3)
	_load_bar.add_theme_stylebox_override("background", bg)
	v.add_child(_load_bar)
	TooltipLayer.attach(lh, func() -> Control: return Tips.stat(&"load", player.stats, "%.1f / %.1f" % [
		player.stats.get_stat(&"carry_weight"), player.stats.get_stat(&"carry_capacity")]) if player and player.stats else null)
	TooltipLayer.attach(_load_bar, func() -> Control: return Tips.stat(&"load", player.stats) if player and player.stats else null)
	_portal_row = HBoxContainer.new()
	_portal_row.add_theme_constant_override("separation", 6)
	_portal_row.visible = false
	v.add_child(_portal_row)
	_portal_label = UITheme.label("", 14, Color(0.8, 0.65, 1.0), UITheme.body_bold())
	_portal_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_portal_label.clip_text = true
	_portal_row.add_child(_portal_label)
	var dispel := Button.new()
	dispel.text = "Dispel"
	dispel.focus_mode = Control.FOCUS_NONE
	dispel.add_theme_font_size_override("font_size", 14)
	dispel.pressed.connect(func() -> void: TownPortal.dispel())
	TooltipLayer.attach(dispel, func() -> Control: return Tips.text("Close your Town Portal (both ends)."))
	_portal_row.add_child(dispel)
	TooltipLayer.attach(_portal_label, func() -> Control: return Tips.text(
		"A Town Portal stands open in %s. Press %s beside it to travel; in Malasugue a return portal waits near the waypoint. It lasts until you die, dispel it, or open another." % [
			_portal_place(), Settings.binding_text(&"interact")], "Town Portal"))

# ---- Touch play layout (bh-008) --------------------------------------------------------------------------------

## Keyboard + mouse: the full skill plate. Touch play: the plate and the load/auto-loot panel give way to the
## on-screen controls (those settings move to the Menu), the orbs shrink a little and the feed moves above the stick.
func _apply_mode() -> void:
	var m := Settings.touch_mode
	if _cluster == null:
		return
	_mobile = m
	_plate.visible = not m
	_side.visible = not m
	_cluster.scale = Vector2.ONE * (0.82 if m else 1.0)
	_cluster.offset_top = -214 if not m else -234
	_cluster.offset_bottom = -30 if not m else -50   # touch play: the XP line sits between the orbs and the edge
	_xp.offset_left = 360 if not m else 470
	_xp.offset_right = -360 if not m else -560
	if m:
		# the feed sits right, between the minimap block and the action buttons
		_feed.set_anchors_preset(Control.PRESET_TOP_RIGHT)
		_feed.offset_left = -760
		_feed.offset_right = -230
		_feed.offset_top = 150
		_feed.offset_bottom = 380
		_top_center.offset_left = -340
		_top_center.offset_right = 340
		_top_right.offset_left = -254
	else:
		_feed.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
		_feed.offset_left = -420
		_feed.offset_right = -24
		_feed.offset_top = -40
		_feed.offset_bottom = 260
		_top_center.offset_left = -430
		_top_center.offset_right = 430
		_top_right.offset_left = -330
	_place_quest_panels(m)

## Re-seat the anchored regions after the window changed size (or came back from minimised) and shrink containers
## back to their content: a container only ever grows by itself.
func _relayout() -> void:
	if _cluster == null or not is_inside_tree():
		return
	_apply_mode()
	_top_right.offset_right = -24
	_top_right.queue_sort()
	_top_center.queue_sort()
	if _left_col and is_instance_valid(_left_col):
		_left_col.reset_size()      # placed by position, not anchors: shrink it back to its content

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_IN or what == NOTIFICATION_WM_WINDOW_FOCUS_IN:
		_relayout.call_deferred()

func _process_cluster_pivot() -> void:
	if _cluster and _cluster.size.x > 0.0:
		_cluster.pivot_offset = Vector2(_cluster.size.x * 0.5, _cluster.size.y)

## Touch play keeps the right side for the thumb: the Tempo frames, route directions, stage tracker and objective
## stack under the portrait instead.
func _place_quest_panels(m: bool) -> void:
	if m:
		if _left_col == null:
			_left_col = VBoxContainer.new()
			_left_col.position = Vector2(24, 134)
			_left_col.add_theme_constant_override("separation", 8)
			_left_col.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(_left_col)
		if tempo_frames.get_parent() != _left_col:
			tempo_frames.reparent(_left_col, false)
		if party_frames.get_parent() != _left_col:
			party_frames.reparent(_left_col, false)
			_left_col.move_child(party_frames, tempo_frames.get_index() + 1)
		for q in _quest_panels:
			if q.get_parent() != _left_col:
				q.reparent(_left_col, false)
	elif _left_col:
		tempo_frames.reparent(self, false)
		tempo_frames.position = Vector2(24, 150)
		party_frames.reparent(self, false)
		for q in _quest_panels:
			q.reparent(_top_right, false)

## Screen rects of the HP and Mana orbs (the touch controls put the draught buttons on them).
func orb_rects() -> Array:
	if _hp_orb == null:
		return []
	var out := []
	for o in [_hp_orb, _mana_orb]:
		var d: float = o.diameter * _cluster.scale.x
		out.append(Rect2(o.global_position, Vector2(d, d)))
	return out

func minimap_rect() -> Rect2:
	return Rect2(_minimap.global_position, Vector2.ONE * _minimap.diameter) if _minimap else Rect2()

func _portal_place() -> String:
	if player == null or player.hero.town_portal.is_empty():
		return ""
	var def := DB.map_def(StringName(player.hero.town_portal.get("map", "")))
	return def.display_name if def else "the wilds"

func _update_side() -> void:
	if _side == null or _hp_orb == null:
		return
	var p := player
	if p.stats:
		var load := p.stats.get_stat(&"load")
		_load_bar.value = clampf(load, 0.0, 1.0)
		_load_label.text = "%.1f / %.0f" % [p.stats.get_stat(&"carry_weight"), p.stats.get_stat(&"carry_capacity")]
		var col := Color(0.45, 0.8, 0.4)
		if load >= 1.0:
			col = Color(0.95, 0.25, 0.2)
		elif load > StatCalculator.LOAD_FREE:
			col = Color(0.95, 0.7, 0.25)
		var fill := _load_bar.get_theme_stylebox("fill") as StyleBoxFlat
		if fill == null or not fill.has_meta(&"own"):
			fill = StyleBoxFlat.new()
			fill.set_meta(&"own", true)
			fill.set_corner_radius_all(3)
			_load_bar.add_theme_stylebox_override("fill", fill)
		fill.bg_color = col
		_load_label.add_theme_color_override("font_color", col.lerp(UITheme.PARCHMENT, 0.4) if load < 1.0 else col)
	if _auto_loot.button_pressed != Settings.auto_loot_enabled:
		_auto_loot.set_pressed_no_signal(Settings.auto_loot_enabled)
	var tp := p.hero.town_portal
	_portal_row.visible = not tp.is_empty()
	if _portal_row.visible:
		_portal_label.text = "Portal: %s" % _portal_place()
	# sit just left of the HP orb, bottoms aligned
	var r := _hp_orb.get_global_rect()
	_side.global_position = Vector2(r.position.x - _side.size.x - 10.0, r.end.y - _side.size.y - 6.0)

func _build_center() -> void:
	_prompt_panel = PanelContainer.new()
	_prompt_panel.theme_type_variation = &"GlassPanel"
	_prompt_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt_panel.offset_left = -300
	_prompt_panel.offset_right = 300
	_prompt_panel.offset_top = -320
	_prompt_panel.offset_bottom = -250
	_prompt_panel.visible = false
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_prompt_panel)
	_prompt = UITheme.label("", 19, UITheme.PARCHMENT, UITheme.body_bold())
	_prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_prompt_panel.add_child(_prompt)
	_banner = VBoxContainer.new()
	_banner.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_banner.offset_left = -600
	_banner.offset_right = 600
	_banner.offset_top = 200
	_banner.offset_bottom = 330
	_banner.alignment = BoxContainer.ALIGNMENT_CENTER
	_banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.modulate.a = 0.0
	add_child(_banner)
	_banner_title = UITheme.title("", 50, UITheme.GOLD)
	_banner_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.add_child(_banner_title)
	var sep := TextureRect.new()
	sep.texture = UIArt.tex("frames/separator_h.png")
	sep.custom_minimum_size = Vector2(520, 16)
	sep.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	sep.stretch_mode = TextureRect.STRETCH_SCALE
	sep.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_banner.add_child(sep)
	_banner_sub = UITheme.label("", 22, UITheme.PARCHMENT, UITheme.body_font())
	_banner_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_sub.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_banner_sub.add_theme_constant_override("outline_size", 5)
	_banner.add_child(_banner_sub)

func _build_feed() -> void:
	_feed = VBoxContainer.new()
	_feed.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	_feed.offset_left = -420
	_feed.offset_right = -24
	_feed.offset_top = -40
	_feed.offset_bottom = 260
	_feed.alignment = BoxContainer.ALIGNMENT_END
	_feed.add_theme_constant_override("separation", 4)
	_feed.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_feed)

# ---- Update --------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if party_frames and party_frames.get_parent() == self:
		party_frames.position = tempo_frames.position + Vector2(0, tempo_frames.size.y + (8.0 if tempo_frames.get_child_count() > 0 else 0.0))
	if player == null or not is_instance_valid(player) or player.hero == null:
		return
	var p := player
	p.ensure_stats()
	_hp_orb.set_value(p.hp, p.max_hp())
	_mana_orb.set_value(p.mana, p.max_mana())
	var hp_frac := p.hp / maxf(1.0, p.max_hp())
	var want_vig := 0.0
	if p.alive and hp_frac < Player.LOW_HP:
		want_vig = (1.0 - hp_frac / Player.LOW_HP) * (0.75 + 0.25 * sin(Time.get_ticks_msec() * 0.006))
	_vignette.modulate.a = lerpf(_vignette.modulate.a, want_vig, 1.0 - exp(-6.0 * delta))
	var prog := p.hero.progress
	_level_label.text = "Level %d" % prog.level
	_update_tier(p.hero)
	var need := XpCurve.xp_to_next(prog.level)
	_xp.set_ratio(float(prog.xp) / float(maxi(1, need)) if need > 0 else 1.0)
	_xp_label.text = ("Level %d · %d / %d XP" % [prog.level, prog.xp, need]) if need > 0 else "Level %d · maximum" % prog.level
	if p.resource:
		if p.resource.kind == &"valor":
			_resource_bar.set_ratio(p.resource.value / maxf(1.0, p.resource.max_value))
			_resource_bar.text = "%d" % roundi(p.resource.value)
			_resource_bar.fill_color = Color(1.0, 0.72, 0.25) if p.resource.is_resolute() else Color(0.95, 0.45, 0.12)
		elif p.resource.kind == &"focus":
			_resource_bar.set_ratio(p.resource.value / maxf(1.0, p.resource.max_value))
			_resource_bar.text = "%d" % roundi(p.resource.value)
			_resource_bar.fill_color = Color(0.62, 1.0, 0.45) if p.resource.is_steady() else Color(0.3, 0.68, 0.3)
		else:
			_update_pips(int(p.resource.value), int(p.resource.max_value))
	var dcd := p.dodge_cd
	var dmax: float = p.stats.get_stat(&"dodge_cooldown", 1.2) if p.stats else 1.2
	_dodge.value = 1.0 - clampf(dcd / maxf(0.01, dmax), 0.0, 1.0)
	_tick -= delta
	if _tick <= 0.0:
		_tick = 0.1
		_refresh_slots()
		_refresh_statuses()
		_refresh_objective()
	if not _mobile:
		_update_side()
	_process_cluster_pivot()
	_update_target(delta)
	_update_boss()

func _refresh_bar() -> void:
	if player == null:
		return
	for i in _skills.size():
		_skills[i].set_skill(player.hero.skill_bar[i])

func _refresh_slots() -> void:
	var p := player
	for i in _skills.size():
		var b := _skills[i]
		if b.skill_id != p.hero.skill_bar[i]:
			b.set_skill(p.hero.skill_bar[i])
		if b.skill_id == &"":
			b.update_state(0.0, 0.0)
			continue
		var cd: float = p.cooldowns.get(b.skill_id, 0.0)
		var total: float = p.cooldown_total.get(b.skill_id, cd)
		b.update_state(cd, total, p.skill_block_reason(b.skill_id), -1, p.mana_cost(b.skill_id))
	for pb in _potions:
		var bp := p.hero.belt_preview(int(pb.get_meta(&"belt_slot")))
		var n: int = bp.count
		if bp.base != pb.potion_base:
			pb.set_potion(bp.base)
		pb.update_state(p.potion_cd, Player.POTION_COOLDOWN, "", n)

## Belt slot tooltip: what the key uses now and how to change it.
func _belt_tip(slot: int) -> Control:
	if player == null or player.hero == null:
		return null
	var id: StringName = player.hero.potion_belt[slot]
	var key := Settings.binding_text(&"potion_health" if slot == 0 else &"potion_mana")
	var what := HeroData.belt_label(id)
	var body := (DB.item_base(id).flavor if DB.item_base(id) else "")
	if HeroData.belt_is_auto(id):
		body = "Drinks your strongest %s draught. Restores over 2 seconds; shared cooldown %.1f s." % [
			"health" if id == HeroData.BELT_AUTO_HEAL else "mana", Player.POTION_COOLDOWN]
	return Tips.text("%s\n\nRight-click to choose what %s uses, or drag a consumable from your bag onto it." % [body, key],
		"%s: %s" % [key, what])

func _update_pips(v: int, m: int) -> void:
	if _pips.get_child_count() != m:
		for c in _pips.get_children():
			c.queue_free()
		for i in m:
			var t := TextureRect.new()
			t.custom_minimum_size = Vector2(26, 26)
			t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			_pips.add_child(t)
	for i in _pips.get_child_count():
		var t := _pips.get_child(i) as TextureRect
		t.texture = UIArt.tex("hud/pip_full.png" if i < v else "hud/pip_empty.png")
		var full := Color(1.3, 1.1, 1.4)
		if player and player.resource and player.resource.kind == &"combo":
			full = Color(1.45, 0.75, 1.6)             # Poised: violet glow at 5 pips
		t.modulate = full if v >= m and i < v else Color.WHITE

func _refresh_statuses() -> void:
	var list := player.status.visible_statuses()
	var sig := ""
	for s in list:
		sig += "%s%d," % [s.id, s.stacks]
	if sig != _status_sig:
		_status_sig = sig
		_rebuild_statuses(list)
	for box in [_buffs, _debuffs]:
		for c in box.get_children():
			c.queue_redraw()

func _rebuild_statuses(list: Array) -> void:
	for c in _buffs.get_children():
		c.queue_free()
	for c in _debuffs.get_children():
		c.queue_free()
	for s in list:
		var icon := StatusIcon.new(player.status, s.id, 34.0)
		(_debuffs if StatusRules.is_debuff(s.id) else _buffs).add_child(icon)

func _refresh_objective() -> void:
	var o := Objectives.current(player.hero)
	_objective_title.get_parent().get_parent().get_parent().visible = not o.is_empty()
	if not o.is_empty():
		_objective_title.text = o.title
		var lv := int(o.get("level", 0))
		# bh-021: a gentle warning when the next step is above the hero's level
		_objective_text.text = o.step + ("  (recommended level %d)" % lv if lv > player.hero.progress.level else "")

func _update_target(delta: float) -> void:
	var t: Enemy = Game.hover_target as Enemy
	if t == null and _target and is_instance_valid(_target) and _target.alive and _target_t > 0.0:
		t = _target
	_target_t -= delta
	if t == null or not is_instance_valid(t) or not t.alive or t.is_boss:
		_target_box.visible = false
		return
	_target_box.visible = true
	_target_name.text = t.display_name
	_target_name.add_theme_color_override("font_color", UITheme.GOLD if t.is_elite else UITheme.PARCHMENT)
	_target_sub.text = "Level %d · %s" % [t.level, t.def.role_name] if t.def.role_name != "" else "Level %d" % t.level
	_target_bar.set_ratio(t.hp / maxf(1.0, t.max_hp()))
	_target_bar.text = "%d / %d" % [ceili(t.hp), roundi(t.max_hp())]
	var sig := ""
	for s in t.status.visible_statuses():
		sig += String(s.id)
	if _target_status.get_meta(&"sig", "") != sig or (_target_status.get_meta(&"who") if _target_status.has_meta(&"who") else null) != t:
		_target_status.set_meta(&"sig", sig)
		_target_status.set_meta(&"who", t)
		for c in _target_status.get_children():
			c.queue_free()
		for s in t.status.visible_statuses():
			_target_status.add_child(StatusIcon.new(t.status, s.id, 26.0))

func _update_boss() -> void:
	if _boss == null or not is_instance_valid(_boss) or not _boss.alive or not _boss.is_inside_tree():
		if _boss_box.visible:
			_boss_box.visible = false
		_boss = null
		return
	_boss_bar.set_ratio(_boss.hp / maxf(1.0, _boss.max_hp()))
	_boss_bar.text = "%d / %d" % [ceili(_boss.hp), roundi(_boss.max_hp())]
	_boss_phase.text = _boss.phase_name()

# ---- Events ----------------------------------------------------------------------------------------------------------

func _on_slot_clicked(b: SkillButton) -> void:
	if player and b.skill_id != &"":
		player._request(&"skill", b.skill_id)

func _on_skill_dropped(b: SkillButton, sid: StringName) -> void:
	if player == null or player.hero.skill_rank(sid) <= 0:
		return
	var bar := player.hero.skill_bar
	var from := bar.find(sid)
	if from >= 0:
		bar[from] = bar[b.index]
	bar[b.index] = sid
	player.hero.skills_changed.emit()
	_refresh_bar()

func _on_prompt(text: String) -> void:
	_prompt_panel.visible = text != "" and not Settings.touch_mode   # touch play: the Interact button carries the verb
	if text != "":
		_prompt.text = "[%s]  %s" % [Settings.binding_text(&"interact"), text]

func _on_boss(b: Node) -> void:
	_boss = b as Enemy
	if _boss == null:
		return
	_boss_box.visible = true
	_boss_name.text = _boss.display_name
	var marks := []
	for ph in _boss.def.phases:
		var h := float(ph.get("hp", 1.0))
		if h < 0.999:
			marks.append(h)
	_boss_bar.tick_marks = marks
	_boss_bar.set_ratio(_boss.hp / maxf(1.0, _boss.max_hp()), true)
	if not _boss.is_miniboss():          # champions are named by the bar and their own plate; no banner over them
		banner(_boss.display_name, "", Color(1.0, 0.45, 0.35))

func _on_boss_defeated(b: Node) -> void:
	banner("Victory", "%s has fallen" % (b as Enemy).display_name if b is Enemy else "", UITheme.GOLD)

func _on_damage(target: Node, _r: DamageResult, _pos: Vector3, attacker: Node) -> void:
	if attacker == player and target is Enemy:
		_target = target
		_target_t = 5.0

func _on_leveled(level: int, gained: int) -> void:
	banner("Level %d" % level, "+%d attribute, +%d skill and +%d talent points" % [
		3 * gained, gained, gained], UITheme.GOLD)

func _on_map_loaded(id: StringName) -> void:
	_on_prompt("")                       # a prompt from the map we just left must not linger (bh-007)
	var def := DB.map_def(id)
	if def:
		banner(def.display_name, def.subtitle, UITheme.PARCHMENT)

func _on_loot(item: ItemInstance) -> void:
	if item:
		_feed_line(("%s x%d" % [item.display_name(), item.count]) if item.count > 1 else item.display_name(), item.color(), item.icon())

func _on_gold(n: int) -> void:
	_feed_line("+%d gold" % n, UITheme.GOLD, UIArt.ui_icon("gold"))

func _on_notify(text: String, kind: StringName) -> void:
	var col := UITheme.TEXT
	var icon := "info"
	match kind:
		&"error": col = Color(1.0, 0.55, 0.45); icon = "warning"
		&"warning": col = Color(1.0, 0.8, 0.5); icon = "warning"
		&"loot": col = UITheme.PARCHMENT; icon = "check"
		&"save": col = UITheme.TEXT_DIM; icon = "save"
		&"discovery": col = Color(0.6, 0.97, 1.0); icon = "map"
		&"aether": col = Color(0.6, 0.97, 1.0); icon = "aether"
		&"locked": col = Color(1.0, 0.75, 0.45); icon = "lock"
	_feed_line(text, col, UIArt.ui_icon(icon))

func _feed_line(text: String, col: Color, icon: Texture2D = null) -> void:
	var p := PanelContainer.new()
	p.theme_type_variation = &"GlassPanel"
	p.size_flags_horizontal = Control.SIZE_SHRINK_END
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	p.add_child(h)
	if icon:
		var t := TextureRect.new()
		t.texture = icon
		t.custom_minimum_size = Vector2(22, 22)
		t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		h.add_child(t)
	var l := UITheme.label(text, 17, col, UITheme.body_bold())
	h.add_child(l)
	_feed.add_child(p)
	while _feed.get_child_count() > 7:
		_feed.get_child(0).queue_free()
		_feed.remove_child(_feed.get_child(0))
	p.modulate.a = 0.0
	var tw := p.create_tween()
	tw.tween_property(p, "modulate:a", 1.0, 0.15)
	tw.tween_interval(4.0)
	tw.tween_property(p, "modulate:a", 0.0, 0.6)
	tw.tween_callback(p.queue_free)

func banner(title: String, sub: String, col := UITheme.GOLD) -> void:
	_banner_title.text = title
	_banner_title.add_theme_color_override("font_color", col)
	_banner_sub.text = sub
	_banner_sub.visible = sub != ""
	if _banner_tw:
		_banner_tw.kill()
	_banner.scale = Vector2(0.94, 0.94)
	_banner.pivot_offset = _banner.size * 0.5
	_banner_tw = create_tween()
	_banner_tw.set_parallel(true)
	_banner_tw.tween_property(_banner, "modulate:a", 1.0, 0.35)
	_banner_tw.tween_property(_banner, "scale", Vector2.ONE, 0.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_banner_tw.chain().tween_interval(2.2)
	_banner_tw.chain().tween_property(_banner, "modulate:a", 0.0, 0.8)

func _xp_tip() -> Control:
	if player == null:
		return null
	var prog := player.hero.progress
	var need := XpCurve.xp_to_next(prog.level)
	return Tips.text("%d / %d experience to level %d (%d%%).\nTotal experience: %d" % [prog.xp, need, prog.level + 1,
		roundi(100.0 * float(prog.xp) / float(maxi(1, need))), prog.total_xp], "Experience")

func _update_tier(h: HeroData) -> void:
	_rested_label.visible = h.is_rested()
	var key := "%d/%s" % [h.tier, h.guild]
	if key == _tier_key:
		return
	_tier_key = key
	var t := DataGuilds.tier(h.tier)
	_tier_icon.texture = UIArt.tex(DataGuilds.emblem_path(h.tier))
	_tier_label.text = "Class %s" % t.letter if h.tier > 0 else "Unranked"
	_tier_label.add_theme_color_override("font_color", t.color)
	var g := DataGuilds.guild(h.guild)
	_guild_icon.texture = UIArt.tex(String(g.crest)) if not g.is_empty() else null
	_guild_icon.visible = not g.is_empty()

func _tier_tooltip() -> String:
	var h := player.hero
	var lines := PackedStringArray()
	lines.append(DataGuilds.tier_name(h.tier))
	if h.guild == &"":
		lines.append("Join the Swordfin Company or the Lantern Covenant in Malasugue to be registered as a Class E hero.")
		lines.append("Licensed items need a guild registration.")
	else:
		var g := DataGuilds.guild(h.guild)
		lines.append("%s — \"%s\"" % [g.name, g.motto])
		for i in g.perk_text.size():
			lines.append("  %s x%d" % [g.perk_text[i], h.tier])
		lines.append("  Accord bonus: +%d%% Maximum HP, +%d%% Damage" % [roundi(DataGuilds.ACCORD_HP * 100 * h.tier), roundi(DataGuilds.ACCORD_DAMAGE * 100 * h.tier)])
		var p := GuildRules.next_promotion(h)
		if int(p.rank) > 0:
			lines.append("Next: Class %s at level %d, %d gold%s." % [DataGuilds.letter(int(p.rank)), p.level, p.fee, (", deed: " + String(p.deed)) if String(p.deed) != "" else ""])
	if h.is_rested():
		lines.append("Well Rested: +%d%% experience (%d min left)" % [roundi(HeroData.RESTED_XP * 100.0), ceili(h.rested_seconds_left() / 60.0)])
	return "\n".join(lines)
