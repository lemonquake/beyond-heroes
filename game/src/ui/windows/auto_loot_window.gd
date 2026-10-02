class_name AutoLootWindow
extends UIWindow
## Saved auto-loot controls, available from Inventory and Settings > Gameplay.

var _content: VBoxContainer
var _summary: Label
var _preview: Label

func _init() -> void:
	super._init("Auto-Loot Filters", Vector2(1320, 900))
	modal = true

func _build() -> void:
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)
	_content = vbox(14)
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_content)
	var footer := hbox(12)
	body.add_child(footer)
	footer.add_child(_note("Scroll for weapon types, custom names, exceptions and the item preview.", 17))
	footer.add_child(button("Done", close_window, &"PrimaryButton", 140))

func refresh() -> void:
	for child in _content.get_children():
		_content.remove_child(child)
		child.queue_free()
	var top := hbox(16)
	_content.add_child(top)
	var enabled := CheckButton.new()
	enabled.text = "Enable auto-loot"
	enabled.button_pressed = Settings.auto_loot_enabled
	enabled.toggled.connect(func(on: bool) -> void: Settings.set_value("auto_loot_enabled", on))
	top.add_child(enabled)
	var presets := OptionButton.new()
	presets.add_item("Choose a preset...")
	for label in AutoLootRules.PRESETS:
		presets.add_item(label)
	presets.item_selected.connect(func(i: int) -> void:
		if i > 0:
			Settings.set_value("auto_loot_rules", AutoLootRules.preset(i - 1))
			refresh())
	top.add_child(presets)
	top.add_child(button("Reset filters", func() -> void:
		Settings.set_value("auto_loot_rules", {})
		refresh()))
	_summary = _note("", 18)
	_content.add_child(_summary)
	_content.add_child(_note("Changes save immediately. Gold is collected on contact. Skipped drops stay on the ground and can still be picked up manually.", 17))
	var columns := hbox(26)
	_content.add_child(columns)
	var left := vbox(10)
	left.custom_minimum_size.x = 410
	columns.add_child(left)
	left.add_child(section("Item categories"))
	var all := hbox(8)
	left.add_child(all)
	for choice in [["Select all", true], ["Clear all", false]]:
		var on: bool = choice[1]
		all.add_child(button(choice[0], func() -> void:
			var cats := {}
			for key in AutoLootRules.CATEGORIES: cats[key] = on
			_set_rule("categories", cats)
			refresh()))
	for key in AutoLootRules.CATEGORIES:
		_dictionary_check(left, AutoLootRules.CATEGORIES[key], "categories", key)
	left.add_child(section("Weapon types"))
	left.add_child(_note("Applies when Weapons is selected.", 17))
	var types := GridContainer.new()
	types.columns = 2
	left.add_child(types)
	for type in DB.weapon_types.values():
		_dictionary_check(types, type.display_name, "weapon_types", String(type.id))
	var right := vbox(12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	columns.add_child(right)
	right.add_child(section("Rarity & equipment"))
	var rarity := OptionButton.new()
	for name in BH.RARITY_NAMES: rarity.add_item(name + " and better")
	rarity.select(clampi(int(Settings.auto_loot_rules.get("min_rarity", Settings.auto_loot_rarity)), 0, BH.RARITY_COUNT - 1))
	rarity.item_selected.connect(func(i: int) -> void: _set_rule("min_rarity", i))
	_row(right, "Minimum equipment rarity", rarity)
	_number(right, "Minimum equipment level", "min_level", 0, 100, 1, 0)
	_number(right, "Minimum equipment sockets", "min_sockets", 0, 6, 1, 0)
	_check(right, "Only gear meeting my level and attributes", "usable_only")
	right.add_child(section("Value & carrying limits"))
	_number(right, "Minimum value per item", "min_value", 0, 1000000, 1, 0)
	_number(right, "Minimum value per weight", "min_value_weight", 0, 100000, 1, 0)
	_number(right, "Maximum weight per drop (0 = any)", "max_weight", 0, 10000, 0.1, 0)
	_number(right, "Stop at load (%)", "max_load", 1, 100, 1, 100)
	_number(right, "Keep general bag slots free", "reserve_slots", 0, Inventory.BAG_CAPACITY, 1, 0)
	_number(right, "Each consumable limit (0 = unlimited)", "consumable_cap", 0, 9999, 1, 0)
	right.add_child(_note("Consumable limits count all bags. A drop that would exceed the limit is left whole. Belt slots do not count toward reserved general bag space.", 17))
	right.add_child(section("Custom names"))
	_text(right, "Only names containing (blank = any)", "include", "e.g. longsword, silverleaf")
	_text(right, "Never take names containing", "exclude", "e.g. rusted, cracked")
	right.add_child(_note("Separate names with commas. Any matching term counts; capitalization does not matter. Excluded names always win.", 17))
	right.add_child(section("Exceptions"))
	_check(right, "Always take keys and quest items", "always_quest")
	_check(right, "Always take unique and set items", "always_unique")
	right.add_child(_note("Exceptions bypass category, rarity, name inclusion and item limits. Excluded names, bag space and carrying limits still apply.", 17))
	_content.add_child(section("Preview with carried items"))
	_preview = _note("", 17)
	_content.add_child(_preview)
	_update_summary()

func _note(text: String, px: int) -> Label:
	var label := UITheme.label(text, px, UITheme.PARCHMENT, UITheme.body_font())
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return label

func _row(parent: Control, text: String, control: Control) -> void:
	var row := hbox(10)
	parent.add_child(row)
	var label := _note(text, 18)
	label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(label)
	control.custom_minimum_size = Vector2(185, 42)
	row.add_child(control)

func _set_rule(key: String, value: Variant) -> void:
	var rules := Settings.auto_loot_rules.duplicate(true)
	rules[key] = value
	Settings.set_value("auto_loot_rules", rules)
	_update_summary()

func _dictionary_check(parent: Control, text: String, dictionary: String, key: String) -> void:
	var check := CheckBox.new()
	check.text = text
	check.add_theme_font_size_override("font_size", 18)
	check.custom_minimum_size.y = 34
	check.button_pressed = bool((Settings.auto_loot_rules.get(dictionary, {}) as Dictionary).get(key, true))
	check.toggled.connect(func(on: bool) -> void:
		var values: Dictionary = (Settings.auto_loot_rules.get(dictionary, {}) as Dictionary).duplicate()
		values[key] = on
		_set_rule(dictionary, values))
	parent.add_child(check)

func _check(parent: Control, text: String, key: String) -> void:
	var check := CheckBox.new()
	check.text = text
	check.custom_minimum_size.y = 38
	check.button_pressed = bool(Settings.auto_loot_rules.get(key, false))
	check.toggled.connect(func(on: bool) -> void: _set_rule(key, on))
	parent.add_child(check)

func _number(parent: Control, text: String, key: String, low: float, high: float, step: float, fallback: float) -> void:
	var spin := SpinBox.new()
	spin.min_value = low
	spin.max_value = high
	spin.step = step
	spin.value = float(Settings.auto_loot_rules.get(key, fallback))
	spin.value_changed.connect(func(value: float) -> void: _set_rule(key, value))
	_row(parent, text, spin)

func _text(parent: Control, text: String, key: String, hint: String) -> void:
	parent.add_child(_note(text, 18))
	var edit := LineEdit.new()
	edit.placeholder_text = hint
	edit.text = String(Settings.auto_loot_rules.get(key, ""))
	edit.clear_button_enabled = true
	edit.custom_minimum_size.y = 44
	edit.text_changed.connect(func(value: String) -> void: _set_rule(key, value))
	parent.add_child(edit)

func _update_summary() -> void:
	if _summary == null: return
	_summary.text = AutoLootRules.summary(Settings.auto_loot_rules, Settings.auto_loot_rarity)
	if _preview == null: return
	var lines := PackedStringArray()
	if Game.hero:
		for item in Game.hero.inventory.cells:
			if item == null: continue
			# Preview content filters only, without counting an already carried stack twice.
			var rules := Settings.auto_loot_rules.duplicate()
			rules["consumable_cap"] = 0
			var reason := AutoLootRules.item_reason(item, Game.hero, rules, Settings.auto_loot_rarity)
			lines.append("%s — %s" % [item.display_name(), "Take" if reason == "" else "Skip: " + reason])
			if lines.size() >= 12: break
	_preview.text = "Category and item rules only; space, total load and consumable totals are checked at pickup.\n" + ("\n".join(lines) if not lines.is_empty() else "Carry some items to preview the rules here.")
