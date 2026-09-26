class_name TempoWindow
extends UIWindow
## Tempos (O): the hero's bound spirit companions. One tab per Tempo. Left: the spirit on its plinth with its 13
## equipment slots. Middle: live HP / mana, derived stats (half the hero's, plus its own gear), personality, skills
## with mana costs and cooldowns, and where it fell. Right: the hero's bag — right-click or drag an item onto a slot to
## give it to the Tempo; right-click an equipped piece to take it back. Tempos wear gear one tier below the hero's.

const SLOT_LAYOUT := {
	&"helm": [0, 0], &"inner_garment": [0, 1], &"armor": [0, 2], &"gloves_1": [0, 3], &"boots_1": [0, 4],
	&"accessory_1": [1, 0], &"accessory_2": [1, 1], &"gloves_2": [1, 2], &"boots_2": [1, 3], &"accessory_3": [1, 4],
}
const STAT_ROWS := [[&"max_hp", "Health"], [&"max_mana", "Mana"], [&"defense", "Defense"], [&"phys_res", "Physical Resist"],
	[&"evasion", "Evasion"], [&"accuracy", "Accuracy"], [&"crit_chance", "Critical Chance"], [&"crit_damage", "Critical Damage"],
	[&"attack_speed", "Attack Speed"], [&"move_speed", "Move Speed"], [&"phys_damage", "Physical Damage"], [&"hp_regen", "Health Regen"],
	[&"mana_regen", "Mana Regen"], [&"healing", "Healing Done"]]

var hero: HeroData
var current: TempoData
var preview: CharacterPreview
var equip_slots := {}
var cells: Array[ItemSlot] = []
var _tabs: TabBar
var _empty: Label
var _content: HBoxContainer
var _name: Label
var _class_line: Label
var _hp_bar: ArtBar
var _mp_bar: ArtBar
var _state: Label
var _stats_grid: GridContainer
var _skills_box: VBoxContainer
var _about: Label
var _cap_label: Label
var _weapon_label: Label
var _stats: DerivedStats
var _live_t := 0.0

func _init() -> void:
	super._init("Tempos", Vector2(1640, 900))

func _build() -> void:
	_tabs = TabBar.new()
	_tabs.tab_changed.connect(func(i: int) -> void:
		if hero and i >= 0 and i < hero.tempos.size():
			current = hero.tempos[i]
			refresh())
	body.add_child(_tabs)
	_empty = UITheme.label("", 20, UITheme.TEXT_DIM, UITheme.body_font())
	_empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty.custom_minimum_size = Vector2(1200, 0)
	_empty.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	body.add_child(_empty)
	_content = hbox(18)
	_content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_content)
	_content.add_child(_build_doll())
	_content.add_child(_build_sheet())
	_content.add_child(_build_bag())
	Events.tempo_changed.connect(func(_u): if visible: refresh())

func _build_doll() -> Control:
	var col := vbox(8)
	col.custom_minimum_size = Vector2(500, 0)
	var well := inset(Vector2(500, 560))
	col.add_child(well)
	var doll := Control.new()
	doll.custom_minimum_size = Vector2(470, 540)
	well.add_child(doll)
	preview = CharacterPreview.new(Vector2i(520, 800))
	preview.position = Vector2(110, 6)
	preview.size = Vector2(250, 400)
	preview.custom_minimum_size = Vector2(250, 400)
	doll.add_child(preview)
	for slot in SLOT_LAYOUT:
		var pos: Array = SLOT_LAYOUT[slot]
		var s := _equip_slot(slot)
		s.position = Vector2(14 if pos[0] == 0 else 390, 6 + pos[1] * 80)
		doll.add_child(s)
	var acc4 := _equip_slot(&"accessory_4")
	acc4.position = Vector2(390, 6 + 5 * 80)
	doll.add_child(acc4)
	var main := _equip_slot(&"main_weapon", 84.0)
	main.position = Vector2(140, 420)
	doll.add_child(main)
	var sub := _equip_slot(&"sub_weapon", 84.0)
	sub.position = Vector2(248, 420)
	doll.add_child(sub)
	_weapon_label = UITheme.label("", 14, UITheme.TEXT_DIM, UITheme.body_font())
	_weapon_label.position = Vector2(0, 508)
	_weapon_label.size = Vector2(470, 24)
	_weapon_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	doll.add_child(_weapon_label)
	_cap_label = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_cap_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_cap_label.custom_minimum_size = Vector2(490, 0)
	col.add_child(_cap_label)
	var rel := button("Release this spirit", _release, &"", 240.0)
	rel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	col.add_child(rel)
	return col

func _equip_slot(slot: StringName, px := 68.0) -> ItemSlot:
	var s := ItemSlot.new(ItemSlot.Kind.EQUIPMENT, px)
	s.equip_slot = slot
	s.glyph = UIArt.tex("slots/glyph_%s.png" % InventoryWindow.GLYPH[slot])
	s.size = Vector2(px, px)
	s.clicked.connect(func(sl: ItemSlot, b: int, _s: bool, _c: bool) -> void:
		if b == MOUSE_BUTTON_RIGHT and sl.item:
			_unequip(sl.equip_slot))
	s.double_clicked.connect(func(sl: ItemSlot) -> void: _unequip(sl.equip_slot))
	s.dropped.connect(_on_drop)
	s.hovered.connect(_on_hover)
	equip_slots[slot] = s
	return s

func _build_sheet() -> Control:
	var col := vbox(6)
	col.custom_minimum_size = Vector2(520, 0)
	var head := hbox(10)
	col.add_child(head)
	_name = UITheme.title("", 28, UITheme.PARCHMENT)
	head.add_child(_name)
	_state = UITheme.label("", 16, UITheme.GOOD, UITheme.body_bold())
	_state.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_state)
	_class_line = UITheme.label("", 17, UITheme.GOLD, UITheme.body_bold())
	col.add_child(_class_line)
	_hp_bar = ArtBar.new("hud/bar_frame_target.png", Color(0.3, 0.85, 0.72), 30.0)
	_hp_bar.custom_minimum_size = Vector2(500, 30)
	col.add_child(_hp_bar)
	_mp_bar = ArtBar.new("hud/bar_frame_target.png", Color(0.25, 0.45, 0.95), 24.0)
	_mp_bar.custom_minimum_size = Vector2(500, 24)
	col.add_child(_mp_bar)
	col.add_child(section("Strength (half of yours, plus its gear)"))
	var st := inset(Vector2(500, 0))
	col.add_child(st)
	_stats_grid = GridContainer.new()
	_stats_grid.columns = 4
	_stats_grid.add_theme_constant_override("h_separation", 14)
	_stats_grid.add_theme_constant_override("v_separation", 2)
	st.add_child(_stats_grid)
	col.add_child(section("Skills"))
	_skills_box = vbox(4)
	col.add_child(_skills_box)
	_about = UITheme.label("", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_about.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_about.custom_minimum_size = Vector2(500, 0)
	col.add_child(_about)
	return col

func _build_bag() -> Control:
	var col := vbox(8)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(section("Your bag"))
	var hint := UITheme.label("Right-click an item (or drag it onto a slot) to give it to your Tempo. Right-click an equipped piece to take it back.", 14, UITheme.TEXT_DIM, UITheme.body_font())
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.custom_minimum_size = Vector2(500, 0)
	col.add_child(hint)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.custom_minimum_size = Vector2(540, 640)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	col.add_child(sc)
	var grid := GridContainer.new()
	grid.columns = 8
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	sc.add_child(grid)
	for i in Inventory.COLUMNS * Inventory.ROWS:
		var s := ItemSlot.new(ItemSlot.Kind.INVENTORY, 62.0)
		s.index = i
		s.clicked.connect(func(sl: ItemSlot, b: int, _s: bool, _c: bool) -> void:
			if b == MOUSE_BUTTON_RIGHT and sl.item:
				_equip(sl.item, &""))
		s.double_clicked.connect(func(sl: ItemSlot) -> void:
			if sl.item:
				_equip(sl.item, &""))
		s.dropped.connect(_on_drop)
		s.hovered.connect(_on_hover)
		grid.add_child(s)
		cells.append(s)
	return col

# ---- Refresh -----------------------------------------------------------------------------------------------------------

func refresh() -> void:
	hero = Game.hero
	if hero == null:
		return
	if current == null or not hero.tempos.has(current):
		current = hero.tempos[0] if not hero.tempos.is_empty() else null
	# rebuilding the tabs emits tab_changed, whose handler calls refresh(): keep the bar quiet while it is rebuilt
	_tabs.set_block_signals(true)
	_tabs.clear_tabs()
	for t in hero.tempos:
		_tabs.add_tab("%s%s" % [t.tempo_name, "  (fallen)" if t.fallen else ""], DataTempos.class_icon(t.class_id))
	_tabs.visible = not hero.tempos.is_empty()
	if current:
		_tabs.current_tab = hero.tempos.find(current)
	_tabs.set_block_signals(false)
	_content.visible = current != null
	_empty.visible = current == null
	_empty.text = "You have no Tempos.\n\nVeyra Ashgrave, the Tempo-Caller, keeps the Shrine of the Fallen east of the terrace stair in Malasugue. Spirits of warriors who died fighting monsters answer her call, and she will bind up to two of them to you."
	if current == null:
		return
	var t := current
	var lvl := hero.progress.level
	_stats = TempoRules.compute(t, TempoRules.hero_mirror(hero), lvl, hero.cls)
	preview.show_tempo(t, lvl)
	var td := t.class_def()
	_name.text = t.tempo_name
	_class_line.text = "%s — %s  ·  %s" % [td.name, td.role, t.trait_def().get("name", "")]
	_class_line.add_theme_color_override("font_color", td.get("color", UITheme.GOLD))
	for s in equip_slots:
		var it := t.equipment.get_item(s)
		(equip_slots[s] as ItemSlot).set_item(it)
	var lo := TempoRules.loadout(t, lvl)
	_weapon_label.text = ("Fights with its ghost %s (equip a weapon to hit harder)" % lo.main_type.display_name.to_lower()) if t.equipment.get_item(&"main_weapon") == null and lo.main_type else \
		"Wields: %s" % ", ".join((td.weapons as Array).map(func(w): return DB.weapon_type(w).display_name if DB.weapon_type(w) else String(w)))
	_cap_label.text = "Gear limit: %s rarity (one tier below yours). Level requirements follow your level; spirits ignore attribute requirements." % BH.rarity_name(TempoRules.best_wearable_rarity(hero))
	_refresh_stats()
	_refresh_skills()
	_about.text = "%s\n\"%s\"  %s\nMonsters felled: %d" % [t.trait_def().get("desc", ""), t.origin, "" if t.fallen else "", t.kills]
	for c in cells:
		var it: ItemInstance = hero.inventory.cells[c.index] if c.index < hero.inventory.cells.size() else null
		var usable := it != null and it.is_equipment() and TempoRules.equip_error(hero, t, it) == ""
		c.set_item(it, it != null and it.is_equipment() and not usable)
		c.dim = it != null and not it.is_equipment()
	_update_live()

func _refresh_stats() -> void:
	for c in _stats_grid.get_children():
		c.queue_free()
	for row in STAT_ROWS:
		var k: StringName = row[0]
		var n := UITheme.label(row[1], 15, UITheme.TEXT_DIM, UITheme.body_font())
		n.mouse_filter = Control.MOUSE_FILTER_PASS
		var v := UITheme.label(StatDefs.format_value(k, _stats.get_stat(k)), 15, UITheme.PARCHMENT, UITheme.number_font())
		v.mouse_filter = Control.MOUSE_FILTER_PASS
		var d := _stats
		TooltipLayer.attach(n, func() -> Control: return Tips.stat(k, d))
		TooltipLayer.attach(v, func() -> Control: return Tips.stat(k, d))
		_stats_grid.add_child(n)
		_stats_grid.add_child(v)
	var wr := StatCalculator.weapon_range(_stats, 0)
	var dn := UITheme.label("Weapon Damage", 15, UITheme.TEXT_DIM, UITheme.body_font())
	_stats_grid.add_child(dn)
	_stats_grid.add_child(UITheme.label("%d–%d" % [roundi(wr.x), roundi(wr.y)], 15, UITheme.PARCHMENT, UITheme.number_font()))

func _refresh_skills() -> void:
	for c in _skills_box.get_children():
		c.queue_free()
	for sid in current.skills:
		var sk := DataTempos.skill(sid)
		var row := hbox(10)
		var ic := TextureRect.new()
		ic.texture = DataTempos.skill_icon(sid)
		ic.custom_minimum_size = Vector2(44, 44)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(ic)
		var v := vbox(0)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var heal := DataTempos.is_heal(sid)
		v.add_child(UITheme.label("%s%s" % [sk.name, "  (heals you)" if heal else ""], 16, UITheme.GOOD if heal else UITheme.PARCHMENT, UITheme.body_bold()))
		v.add_child(UITheme.label("%d mana · %d s cooldown" % [roundi(float(sk.mana)), roundi(float(sk.cooldown))], 13, UITheme.MANA.lightened(0.3), UITheme.number_font()))
		row.add_child(v)
		var desc := String(sk.desc)
		TooltipLayer.attach(row, func() -> Control: return Tips.text(desc, sk.name))
		_skills_box.add_child(row)

func _process(delta: float) -> void:
	if not visible:
		return
	_live_t -= delta
	if _live_t <= 0.0:
		_live_t = 0.1
		_update_live()

## HP / mana from the live spirit when it is in the world, else from its saved state.
func _update_live() -> void:
	if current == null or _stats == null:
		return
	var a := TempoParty.actor_for(current.uid)
	var mhp := _stats.get_stat(&"max_hp", 1.0)
	var mmp := _stats.get_stat(&"max_mana", 1.0)
	var hp := a.hp if a and a.alive else mhp * (0.0 if current.fallen else current.hp_frac)
	var mp := a.mana if a and a.alive else mmp * (0.0 if current.fallen else current.mana_frac)
	_hp_bar.set_ratio(hp / maxf(1.0, mhp))
	_hp_bar.text = "%d / %d" % [ceili(hp), roundi(mhp)]
	_mp_bar.set_ratio(mp / maxf(1.0, mmp))
	_mp_bar.text = "%d / %d" % [floori(mp), roundi(mmp)]
	if current.fallen:
		_state.text = "Fallen — Veyra Ashgrave can call it back"
		_state.add_theme_color_override("font_color", UITheme.BAD)
	elif a:
		_state.text = a.mode_name()
		_state.add_theme_color_override("font_color", UITheme.GOOD)
	else:
		_state.text = "Resting"
		_state.add_theme_color_override("font_color", UITheme.TEXT_DIM)

# ---- Actions -------------------------------------------------------------------------------------------------------------

func _equip(it: ItemInstance, slot: StringName) -> void:
	if current == null:
		return
	var err := TempoRules.equip_from_inventory(hero, current, it, slot)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Audio.play_ui(&"ui_equip")
	TooltipLayer.hide_for(null)
	refresh()

func _unequip(slot: StringName) -> void:
	if current == null:
		return
	var err := TempoRules.unequip_to_inventory(hero, current, slot)
	if err != "":
		Events.notify.emit(err, &"error")
		Audio.play_ui(&"ui_error")
	else:
		Audio.play_ui(&"ui_unequip")
	TooltipLayer.hide_for(null)
	refresh()

func _on_drop(from: ItemSlot, to: ItemSlot) -> void:
	if from.item == null or current == null:
		return
	if from.kind == ItemSlot.Kind.INVENTORY and to.kind == ItemSlot.Kind.EQUIPMENT:
		_equip(from.item, to.equip_slot)
	elif from.kind == ItemSlot.Kind.EQUIPMENT and to.kind == ItemSlot.Kind.INVENTORY:
		_unequip(from.equip_slot)
	elif from.kind == ItemSlot.Kind.INVENTORY and to.kind == ItemSlot.Kind.INVENTORY:
		hero.inventory.move(from.index, to.index)
		refresh()

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside:
		TooltipLayer.hide_for(s)
		return
	if s.item == null:
		if s.kind == ItemSlot.Kind.EQUIPMENT:
			TooltipLayer.show_for(s, func() -> Control: return Tips.text("Empty. Drag an item here from your bag.", BH.SLOT_NAMES[s.equip_slot]))
		return
	var equipped := s.kind == ItemSlot.Kind.EQUIPMENT
	var hint := "Right-click to take it back" if equipped else ""
	if not equipped and s.item.is_equipment() and current:
		var err := TempoRules.equip_error(hero, current, s.item)
		hint = ("Right-click to give it to %s" % current.tempo_name) if err == "" else "%s cannot use this: %s" % [current.tempo_name, err]
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(s.item, {"hero": hero, "equipped": equipped, "compare": false, "hint": hint}))

func _release() -> void:
	if current == null:
		return
	var t := current
	Game.ui_root.ask("Release %s" % t.tempo_name, "Let %s's spirit go? It will not return, and its gear comes back to your bag." % t.tempo_name,
		func() -> void:
			var err := TempoRules.release(hero, t)
			if err != "":
				Events.notify.emit(err, &"error")
				return
			current = null
			TempoParty.refresh(hero)
			Events.notify.emit("%s's spirit is at rest." % t.tempo_name, &"info")
			refresh(), "Release", true)
