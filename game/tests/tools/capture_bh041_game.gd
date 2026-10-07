extends Node
## bh-041 captures in the real game, on a hero loaded from a hidden slot (copy a save to slot_97.json first):
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_bh041_game.tscn -- --load --slot=97 --phase=tempo [--out=<dir>]
## Phases: tempo (the Aggro / Defend / Passive toggle over the Tempo frames and in the Tempo window), wear (a full
## Eschaton collection and weapon worn: the chrome), lape (Lape's table with three Primordial pieces laid down, the
## Eschaton reveal frame by frame, the offers, then taking the last work), debug (the Debug button is gone).

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/bh-041/shots")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("CAPTURE ", label)

func _run() -> void:
	for i in 1200:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(2.5)
	Game.god_mode = true
	match String(args.get("phase", "tempo")):
		"tempo": await _tempo()
		"wear": await _wear()
		"lape": await _lape()
		"debug": await _debug()
	get_tree().quit()

func _debug() -> void:
	print("DEBUG_UNLOCKED ", Game.hero.debug_unlocked, " button_visible ", Game.ui_root.hud._debug_btn.visible)
	await _shot("debug_swept_hud")

func _tempo() -> void:
	await _shot("tempo_hud_defend")
	TempoRules.set_command(Game.hero, &"aggro")
	await _wait(0.8)
	await _shot("tempo_hud_aggro")
	TempoRules.set_command(Game.hero, &"passive")
	await _wait(0.4)
	Game.ui_root.open(&"tempos")
	await _wait(1.0)
	await _shot("tempo_window_passive")
	Game.ui_root.window(&"tempos").close_window()
	TempoRules.set_command(Game.hero, &"defend")
	await _wait(0.5)

## A full mage collection and an Eschaton staff, worn in town; then the inventory with them.
func _wear() -> void:
	var h := Game.hero
	var p := Game.player as Player
	var sid := String(args.get("set", "void_unwritten"))
	var r := RandomNumberGenerator.new()
	r.seed = 41
	var row := DataEschaton.row(StringName(sid))
	for piece in DataEschaton.pieces_of(row):
		var it := DB.make_item(DataEschaton.piece_id(StringName(sid), piece), BH.Rarity.COMMON, 141, r.randi())
		var slot: StringName = h.equipment.auto_slot(it)
		h.equipment.slots[slot] = it
		if piece in ["gloves", "boots"]:
			h.equipment.slots[StringName(String(slot).left(-1) + "2")] = it.clone()
	var wcls := StringName(row[2])
	var weapon := DB.make_item(DataEschaton.weapon_id(wcls, DataEschaton.WEAPONS[wcls][0], int(args.get("weapon", "0"))), BH.Rarity.COMMON, 141, r.randi())
	h.equipment.slots[&"main_weapon"] = weapon
	h.equipment.changed.emit()
	p.refresh_equipment_visuals()
	await _wait(2.5)
	p.set_first_person(false)
	var cam := p.camera
	await _shot("eschaton_worn_town_" + sid)
	if cam:
		for z in 6:
			cam.zoom(-1)
	await _wait(1.5)
	await _shot("eschaton_worn_close")
	Game.ui_root.open(&"inventory")
	await _wait(1.5)
	await _shot("eschaton_inventory_" + sid)
	var inv := Game.ui_root.window(&"inventory") as InventoryWindow
	for c in inv.find_children("*", "ItemSlot", true, false):
		var s := c as ItemSlot
		if s.item and s.item.base.id == weapon.base.id:
			var w := weapon
			TooltipLayer.show_for(s, func() -> Control: return Tips.item(w, {"hero": h, "equipped": true}))
			break
	await _wait(1.0)
	await _shot("eschaton_tooltip")

## Lape's table: three Primordial pieces; the first look that holds the last work is revealed frame by frame.
func _lape() -> void:
	var h := Game.hero
	if Game.current_map_id != &"sanctuary":
		Game.travel(&"sanctuary", &"waypoint")
		await _wait(1.0)
		for i in 1200:
			if not Game.travelling and Game.current_map_id == &"sanctuary":
				break
			await get_tree().process_frame
		await _wait(3.0)
	var p := Game.player as Player
	var lape := NpcDirectory.find(&"lape")
	if lape:
		p.teleport_to(lape.global_position + lape.global_transform.basis.z * 2.4)
		p.face_toward(lape.global_position)
	await _wait(1.5)
	var cls: StringName = h.cls.id
	var lot := []
	var r := RandomNumberGenerator.new()
	r.seed = 77
	for i in 3:
		var it := DataAscendant.roll_drop(141, false, cls, 0.0, r, BH.Rarity.PRIMORDIAL)
		h.inventory.add(it)
		lot.append(it)
	h.inventory.gold = maxi(h.inventory.gold, 5000000)
	var w := Game.ui_root.window(&"lape") as LapeWindow
	w.open_for("Lape the Ancient")
	await _wait(1.0)
	for i in lot.size():
		w._lay(lot[i], i)
	await _wait(0.6)
	await _shot("lape_three_primordial")
	# the first look, then paid looks until the last work is on the table
	w._appraise()
	await _wait(0.2)
	for k in 12:
		if w.appraisal.get("eschaton", false):
			break
		for n in w.get_children():
			if n is EschatonReveal:
				n.queue_free()
		w._redraw()
		await _wait(0.2)
	var rev: EschatonReveal = null
	for n in w.get_children():
		if n is EschatonReveal:
			rev = n
	if rev:
		await _wait(0.75)
		await _shot("lape_reveal_1_eclipse")
		await _wait(0.75)
		await _shot("lape_reveal_2_burst")
		await _wait(0.5)
		await _shot("lape_reveal_3_word")
		await _wait(1.6)
		await _shot("lape_reveal_4_named")
		rev._finish()
		await _wait(0.8)
	await _shot("lape_offers")
	print("LAPE overflow ", w.overflow())
	var at: int = (w.appraisal.get("kinds", []) as Array).find(&"eschaton")
	print("LAPE eschaton=", w.appraisal.get("eschaton", false), " draw=", w.appraisal.get("draw", 0), " kinds=", w.appraisal.get("kinds", []))
	if at >= 0:
		var res := LapeTrade.accept(h, w._laid(), w.appraisal, at)
		print("LAPE took ", res.ok, " ", (res.item as ItemInstance).display_name() if res.item else "")
		EschatonReveal.play(w, res.item, Callable(), true)
		await _wait(0.7)
		await _shot("lape_taken")
		await _wait(2.5)
