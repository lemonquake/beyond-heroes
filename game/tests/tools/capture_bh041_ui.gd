extends Node
## bh-041: the Inventory, Skills and Talents windows under the heaviest load the game can produce — a fully transcended
## hero (both advancements) with every skill and talent ranked, and items with the longest descriptions (Ascendant set
## pieces, Fabled Arms, every socket filled, runes, Fore-Tech, licenses, long names) — on a full-HD and a small screen.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_bh041_ui.tscn -- --class=mage --out=<dir> [--tag=after]
## Prints UI_FIT lines: whether each window and the tallest tooltip fit the screen.

var args := {}
var out := ""
var tag := "now"
var fails := 0

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/bh-041/ui")))
	tag = String(args.get("tag", "now"))
	DirAccess.make_dir_recursive_absolute(out)
	_run.call_deferred()

func _shot(label: String) -> void:
	for i in 20:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var vp := get_viewport().get_visible_rect().size
	get_viewport().get_texture().get_image().save_png(out.path_join("%s_%dx%d_%s.png" % [tag, int(vp.x), int(vp.y), label]))
	print("CAPTURE ", label)

func _fit(label: String, c: Control) -> void:
	var vp := get_viewport().get_visible_rect()
	var r := c.get_global_rect()
	var ok := vp.encloses(r.grow(-1.0))
	if not ok:
		fails += 1
	print("UI_FIT %s %s rect=%s screen=%s" % ["ok  " if ok else "FAIL", label, r, vp.size])

func _hero() -> HeroData:
	var fam := StringName(String(args.get("class", "mage")))
	var h := Game.new_hero(fam, "Hehe")
	h.progress.level = 141
	h.tier = 8
	var first: StringName = DataTranscendence.children_of(fam)[0]
	var master: StringName = DataTranscendence.children_of(first)[0]
	h.transcendence_path.assign([first, master] if args.get("stage", "2") == "2" else ([first] if args.get("stage") == "1" else []))
	if args.get("stage", "2") != "2":
		h.progress.level = 119
	h.apply_identity()
	for n in h.skill_tree.tree.nodes:
		h.skill_tree.ranks[n.id] = int(n.get("max_rank", 1))
	for n in h.talent_tree.tree.nodes:
		h.talent_tree.ranks[n.id] = int(n.get("max_rank", 1))
	h._skills_changed()
	return h

## The wordiest items there are, all fully socketed and upgraded.
func _long_items(h: HeroData) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = 41
	var out_items := []
	for r in [BH.Rarity.PRIMORDIAL, BH.Rarity.ETERNAL]:
		for i in 3:
			var it = DataAscendant.roll_drop(120, false, h.cls.id, 0.0, rng, r)
			if it:
				out_items.append(it)
	for id in DataFabled.ids().slice(0, 4):
		var b := DB.item_base(id)
		if b:
			out_items.append(ItemGenerator.generate(b, 120, BH.Rarity.PRIMORDIAL, rng, true))
	var crystals := []
	for g in DB.item_bases.values():
		if DataCrystals.is_crystal(g.id):
			crystals.append(String(g.id))
	for it: ItemInstance in out_items:
		it.custom_name = "Worldsundering Heirloom of the Last Unremembered Dawn"
		it.sockets = DataCrystals.MAX_SOCKETS[it.rarity] if DataCrystals.MAX_SOCKETS[it.rarity] > 0 else 6
		it.gems = []
		for s in it.sockets:
			it.gems.append(crystals[(s * 7) % crystals.size()] if not crystals.is_empty() else "")
		if it.base.is_weapon():
			it.enchant = DataUpgrades.ENCHANTS.keys()[0]
			it.enchant_rank = DataUpgrades.ENCHANT_MAX
			it.foretech = DataUpgrades.TECHS.keys()[0]
			it.foretech_rank = DataUpgrades.TECH_MAX
	return out_items

func _run() -> void:
	Settings.control_mode = "mobile" if args.get("touch", "0") == "1" else "pc"
	Game.hero = _hero()
	var h := Game.hero
	var items := _long_items(h)
	for i in items.size():
		h.inventory.cells[i] = items[i]
	# wear one of each slot so the tooltips also show the comparison column
	for it: ItemInstance in items.slice(0, 3):
		var slot: StringName = h.equipment.auto_slot(it)
		if slot != &"":
			h.equipment.slots[slot] = it.clone()
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.025, 0.03)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var tl := TooltipLayer.new()
	add_child(tl)
	# --- Inventory and its tallest tooltip
	var inv := InventoryWindow.new()
	inv.theme = UITheme.theme()
	add_child(inv)
	inv.open()
	await _shot("inventory")
	_fit("inventory window", inv._frame_rect() if inv.has_method(&"_frame_rect") else inv)
	var tallest: Control = null
	var tallest_h := 0.0
	var tallest_slot: ItemSlot = null
	for c in inv.find_children("*", "ItemSlot", true, false):
		var s := c as ItemSlot
		if s.item == null or s.kind != ItemSlot.Kind.INVENTORY or not s.is_visible_in_tree():
			continue
		var tip := Tips.item(s.item, {"hero": h})
		add_child(tip)
		tip.reset_size()
		await get_tree().process_frame
		var th := tip.get_combined_minimum_size().y
		tip.queue_free()
		if th > tallest_h:
			tallest_h = th
			tallest_slot = s
	if tallest_slot:
		var it := tallest_slot.item
		TooltipLayer.show_for(tallest_slot, func() -> Control: return Tips.item(it, {"hero": h}))
		await _shot("inventory_tooltip_tallest")
		_fit("tallest item tooltip (%s, %d px of content)" % [it.display_name(), roundi(tallest_h)], tl._panel)
		TooltipLayer.hide_for(null)
	inv.hide()
	# --- Skills: every page, the learned list and the detail panel
	var skills := SkillsWindow.new()
	skills.theme = UITheme.theme()
	add_child(skills)
	skills.open()
	await _shot("skills_page0")
	var previews := TranscendPages.preview_ids(h)
	if not previews.is_empty():
		skills.tree.bind_preview(h, false, previews[0])
		skills._build_tabs()
		await _shot("skills_preview")
		_fit("skills window (preview)", skills._tabs.get_parent())
		skills.tree.end_preview()
		skills._build_tabs()
	_fit("skills window", skills)
	for page in range(1, h.skill_tree.tree.page_count()):
		skills.tree.set_page(page)
		skills._build_tabs()
		await _shot("skills_page%d" % page)
	_fit("skills window (last page)", skills)
	skills.hide()
	# --- Talents
	var talents := TalentsWindow.new()
	talents.theme = UITheme.theme()
	add_child(talents)
	talents.open()
	await _shot("talents")
	_fit("talents window", talents)
	if talents.get(&"tree") != null and talents.tree.has_method(&"set_page"):
		for page in range(1, h.talent_tree.tree.page_count()):
			talents.tree.set_page(page)
			if talents.has_method(&"_build_tabs"):
				talents._build_tabs()
			await _shot("talents_page%d" % page)
		_fit("talents window (last page)", talents)
	talents.hide()
	_fit_overflow("skills window", skills)
	_fit_overflow("talents window", talents)
	if args.get("sweep", "0") == "1":
		await _sweep()
	print("UI_FIT %s (%d problems)" % ["PASS" if fails == 0 else "FAIL", fails])
	get_tree().quit(0)

func _fit_overflow(label: String, w: UIWindow) -> void:
	var o := w.overflow()
	var ok := o.x <= 1.0 and o.y <= 1.0
	if not ok:
		fails += 1
	print("UI_FIT %s %s content past the window by %s" % ["ok  " if ok else "FAIL", label, o])

## Every window in the game: open it for this hero and report content that wants more room than the window has.
func _sweep() -> void:
	var skip := ["ShopWindow", "DialogueBox"]
	for g in ProjectSettings.get_global_class_list():
		if String(g.base) != "UIWindow" or String(g["class"]) in skip:
			continue
		var w = load(String(g.path)).new()
		if not w is UIWindow:
			continue
		(w as UIWindow).theme = UITheme.theme()
		add_child(w)
		w.open()
		for i in 6:
			await get_tree().process_frame
		var o: Vector2 = w.overflow()
		var bad := o.x > 1.0 or o.y > 1.0
		print("UI_SWEEP %s %s overflow=%s" % ["FAIL" if bad else "ok  ", g["class"], o])
		if bad:
			for c in (w as UIWindow).body.get_children():
				print("    body child %s min=%s" % [c.get_class(), (c as Control).get_combined_minimum_size()])
				for cc in c.get_children():
					if cc is Control:
						print("      %s min=%s" % [cc.get_class(), (cc as Control).get_combined_minimum_size()])
			fails += 1
			await _shot("sweep_" + String(g["class"]))
		w.queue_free()
		await get_tree().process_frame

