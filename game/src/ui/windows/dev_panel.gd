class_name DevPanel
extends Control
## Hidden developer panel (F1, debug builds or --dev). Spawn enemies / elites / the boss, give items (chosen or random,
## any rarity), change the hero (XP, level, attributes, god mode, infinite Mana, reset skills/talents, damage, statuses),
## travel and unlock waypoints, and toggle overlays (damage formula, AI states, hitboxes, navmesh, FPS/profiling).

var _panel: PanelContainer
var _enemy: OptionButton
var _enemy_level: SpinBox
var _base: OptionButton
var _rarity: OptionButton
var _xp: SpinBox
var _level: SpinBox
var _dmg: SpinBox
var _status: OptionButton
var _map: OptionButton
var _enemy_ids := []
var _base_ids := []
var _status_ids := []
var _map_ids := []
var _last_item: ItemInstance

func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS

func _ready() -> void:
	_panel = PanelContainer.new()
	_panel.theme_type_variation = &"TooltipFrame"
	_panel.position = Vector2(20, 110)
	_panel.custom_minimum_size = Vector2(560, 0)
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_panel)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(540, 840)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_panel.add_child(scroll)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(v)
	v.add_child(UITheme.title("Developer", 24, Color(0.6, 1.0, 0.7)))
	# enemies
	v.add_child(_head("Enemies"))
	_enemy = OptionButton.new()
	for id in DB.enemies.keys():
		_enemy_ids.append(id)
		_enemy.add_item(DB.enemies[id].display_name)
	_enemy_level = _spin(1, BH.LEVEL_CAP, 5)
	v.add_child(_row([_enemy, _enemy_level]))
	v.add_child(_row([_btn("Spawn Enemy", func(): _spawn(false)), _btn("Spawn Elite", func(): _spawn(true)), _btn("Spawn Boss", _spawn_boss)]))
	v.add_child(_row([_btn("Kill All Enemies", _kill_all)]))
	# items
	v.add_child(_head("Items"))
	_base = OptionButton.new()
	var bases := DB.item_bases.values()
	bases.sort_custom(func(a, b): return a.display_name < b.display_name)
	for b in bases:
		_base_ids.append(b.id)
		_base.add_item("%s (%s)" % [b.unique_name if b.unique_name != "" else b.display_name, b.category])
	_rarity = OptionButton.new()
	for n in BH.RARITY_NAMES:
		_rarity.add_item(n)
	_rarity.selected = BH.Rarity.ELITE
	v.add_child(_row([_base]))
	v.add_child(_row([_rarity, _btn("Give Item", _give_item), _btn("Give Random", _give_random)]))
	v.add_child(_row([_btn("Set Rarity of Last Item", _set_rarity), _btn("+1000 Gold", func(): _gold(1000))]))
	# hero
	v.add_child(_head("Hero"))
	_xp = _spin(1, 1000000, 1000)
	v.add_child(_row([_xp, _btn("Give XP", _give_xp)]))
	_level = _spin(1, BH.LEVEL_CAP, 10)
	v.add_child(_row([_level, _btn("Set Level", _set_level), _btn("+10 Attribute Points", _attr_points)]))
	v.add_child(_row([_check("God Mode", Game.god_mode, func(on): Game.god_mode = on), _check("Infinite Mana", Game.infinite_mana, func(on): Game.infinite_mana = on)]))
	v.add_child(_row([_btn("Reset Skills", _reset_skills), _btn("Reset Talents", _reset_talents), _btn("Full Heal", func(): NpcServices.heal(Game.player))]))
	_dmg = _spin(1, 100000, 50)
	v.add_child(_row([_dmg, _btn("Damage Player", _damage_player)]))
	_status = OptionButton.new()
	for id in StatusRules.DEFS.keys():
		if not StatusRules.is_hidden(id):
			_status_ids.append(id)
			_status.add_item(StatusRules.name_of(id))
	v.add_child(_row([_status, _btn("Apply Status", _apply_status), _btn("Clear", func(): (Game.player as Player).status.clear())]))
	# world
	v.add_child(_head("World"))
	_map = OptionButton.new()
	for id in DB.maps.keys():
		_map_ids.append(id)
		_map.add_item(DB.maps[id].display_name)
	v.add_child(_row([_map, _btn("Teleport", _teleport), _btn("Unlock All Waypoints", _unlock_all)]))
	v.add_child(_row([_btn("Set Ritual Seen", func(): Game.set_world_flag(&"catacombs_ritual_seen")), _btn("Break Seal", func(): Game.set_world_flag(&"temple_seal_broken")),
		_btn("Warden Defeated", func(): Game.set_world_flag(&"boss_warden_defeated"))]))
	# overlays
	v.add_child(_head("Overlays"))
	v.add_child(_row([_check("Damage Formula", Dev.show_formula, func(on): Dev.show_formula = on), _check("AI State", Dev.show_ai, func(on): Dev.show_ai = on)]))
	v.add_child(_row([_check("Hitboxes", Dev.show_hitboxes, func(on): Dev.show_hitboxes = on), _check("Navmesh", Dev.show_navmesh, func(on): Dev.set_navmesh(on)),
		_check("FPS", Dev.show_fps, func(on): Dev.show_fps = on)]))

func toggle() -> void:
	if Official.active:
		return
	visible = not visible

func _head(t: String) -> Control:
	var l := UITheme.label(t, 18, UITheme.GOLD, UITheme.title_font())
	return l

func _row(ctrls: Array) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	for c in ctrls:
		if c is Button or c is OptionButton or c is SpinBox:
			c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(c)
	return h

func _btn(t: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = t
	b.add_theme_font_size_override("font_size", 15)
	b.custom_minimum_size.y = 38
	b.pressed.connect(cb)
	return b

func _check(t: String, on: bool, cb: Callable) -> CheckBox:
	var c := CheckBox.new()
	c.text = t
	c.button_pressed = on
	c.toggled.connect(cb)
	return c

func _spin(lo: float, hi: float, v: float) -> SpinBox:
	var s := SpinBox.new()
	s.min_value = lo
	s.max_value = hi
	s.value = v
	s.custom_minimum_size = Vector2(120, 38)
	return s

func _player() -> Player:
	return Game.player as Player

func _spawn_pos(dist := 6.0) -> Vector3:
	var p := _player()
	return p.global_position + p.forward() * dist if p else Vector3.ZERO

func _spawn(elite: bool) -> void:
	if Game.current_map == null:
		return
	var def: EnemyDef = DB.enemies[_enemy_ids[_enemy.selected]]
	var mods := []
	if elite:
		var keys := DB.elite_mods.keys()
		keys.shuffle()
		mods = keys.slice(0, 2)
	var diff: Dictionary = DataEnemies.DIFFICULTY[clampi(Game.difficulty, 0, DataEnemies.DIFFICULTY.size() - 1)]
	Spawner.spawn_enemy(Game.current_map, def, int(_enemy_level.value), mods, _spawn_pos(), diff)

func _spawn_boss() -> void:
	if Game.current_map == null:
		return
	var diff: Dictionary = DataEnemies.DIFFICULTY[clampi(Game.difficulty, 0, DataEnemies.DIFFICULTY.size() - 1)]
	Spawner.spawn_enemy(Game.current_map, DB.enemy(&"boss_warden"), int(_enemy_level.value), [], _spawn_pos(9.0), diff)

func _kill_all() -> void:
	for e in get_tree().get_nodes_in_group(&"enemy"):
		if e.alive:
			e.die(Game.player)

func _give(it: ItemInstance) -> void:
	if it == null:
		return
	_last_item = it
	if Game.hero.inventory.add(it) > 0:
		Events.notify.emit("Inventory full", &"error")
	else:
		Events.loot_picked.emit(it)

func _give_item() -> void:
	_give(DB.make_item(_base_ids[_base.selected], _rarity.selected, Game.hero.progress.level))

func _give_random() -> void:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var b := ItemGenerator.random_base(rng, Game.hero.progress.level)
	_give(ItemGenerator.generate(b, Game.hero.progress.level, _rarity.selected, rng))

func _set_rarity() -> void:
	if _last_item == null or Game.hero.inventory.index_of(_last_item) < 0:
		Events.notify.emit("Give an item first", &"error")
		return
	var idx := Game.hero.inventory.index_of(_last_item)
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var re := ItemGenerator.generate(_last_item.base, _last_item.ilvl, _rarity.selected, rng)
	Game.hero.inventory.put_at(idx, re)
	_last_item = re

func _gold(n: int) -> void:
	Game.hero.inventory.gold += n
	Game.hero.inventory.changed.emit()

func _give_xp() -> void:
	Game.hero.progress.add_xp(int(_xp.value))

func _set_level() -> void:
	var want := int(_level.value)
	var pr := Game.hero.progress
	if want > pr.level:
		pr.add_xp(XpCurve.total_xp_for_level(want) - XpCurve.total_xp_for_level(pr.level) - pr.xp)
	else:
		Events.notify.emit("Lowering the level needs a new hero", &"info")

func _attr_points() -> void:
	Game.hero.progress.free_points += 10
	Game.hero.progress.points_changed.emit()

func _reset_skills() -> void:
	var h := Game.hero
	var pv := NpcServices.respec_preview(h)
	h.skill_tree.reset()
	for s in h.cls.starting_skills:
		h.skill_tree.ranks[s] = 1
	h.progress.skill_points += int(pv.skill_points)
	for i in h.skill_bar.size():
		if h.skill_bar[i] != &"" and h.skill_rank(h.skill_bar[i]) <= 0:
			h.skill_bar[i] = &""
	h.skill_tree.changed.emit()
	h.progress.points_changed.emit()
	h.skills_changed.emit()

func _reset_talents() -> void:
	var h := Game.hero
	h.progress.talent_points += h.talent_tree.reset()
	h.progress.points_changed.emit()

func _damage_player() -> void:
	var p := _player()
	if p == null:
		return
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.ATTACK
	req.use_weapon = false
	req.base_min = _dmg.value
	req.base_max = _dmg.value
	req.can_crit = false
	req.evadable = false
	req.label = "Developer"
	p.receive_hit(req, null)

func _apply_status() -> void:
	var p := _player()
	if p:
		p.status.apply(_status_ids[_status.selected])

func _teleport() -> void:
	Game.travel(_map_ids[_map.selected], &"start")

func _unlock_all() -> void:
	for id in DB.maps:
		Game.hero.discovered_maps[id] = true
	for t in get_tree().get_nodes_in_group(&"teleporter"):
		t.discover()
	Events.notify.emit("All regions discovered", &"discovery")
