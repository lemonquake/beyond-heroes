extends Node
## bh-042: item tooltips with very long content, measured where they go wrong — Lape the Ancient's table (dishes on the
## left, the offers on the right, the bag below) — and at fixed anchors in every corner of the screen.
##   godot --path game --resolution 1600x900 res://tests/tools/capture_tooltips_bh042.tscn -- --class=mage --slot=97 --out=<dir> [--tag=before]
## Prints one TIP line per tooltip: its final rect, scale, how much of it is off screen, and whether it is readable
## (scale >= 0.8 and wholly on screen). TIPS PASS/FAIL at the end.

var args := {}
var out := ""
var tag := "after"
var fails := 0
var worst: Array = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../output/bh-042/tooltips")))
	tag = String(args.get("tag", "after"))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [tag, label]))
	print("TIP SHOT ", label)

## The longest items the game makes: Eschaton and Primordial pieces with every socket filled, the longest name, a
## Fabled weapon, fully enchanted.
func _long_items(h: HeroData) -> Array:
	var r := RandomNumberGenerator.new()
	r.seed = 4242
	var items := []
	for i in 3:
		items.append(DataEschaton.roll(h.cls.id, r, 165))
	for i in 3:
		items.append(DataAscendant.roll_drop(165, false, h.cls.id, 0.0, r, BH.Rarity.PRIMORDIAL))
	var crystals := []
	for g in DB.item_bases.values():
		if DataCrystals.is_crystal(g.id):
			crystals.append(String(g.id))
	for it: ItemInstance in items:
		if it == null:
			continue
		it.custom_name = "Worldsundering Heirloom of the Last Unremembered Dawn Beyond the Eschaton"
		it.sockets = maxi(6, int(DataCrystals.MAX_SOCKETS[it.rarity]))
		it.gems = []
		for s in it.sockets:
			it.gems.append(crystals[(s * 7) % crystals.size()] if not crystals.is_empty() else "")
	return items.filter(func(x): return x != null)

func _run() -> void:
	for i in 1500:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _frames(90)
	var h := Game.hero
	h.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(165) - h.progress.total_xp))
	QuakeBrain.spend_points(h)
	h.tier = 6
	Game.god_mode = true
	var items := _long_items(h)
	# wear a long piece in each slot they fit, so every tooltip carries the "Equipped" comparison card
	for it: ItemInstance in items:
		var slot: StringName = h.equipment.auto_slot(it)
		if slot != &"" and h.equipment.slots.get(slot) == null:
			h.equipment.slots[slot] = it.clone()
	for it in items:
		h.inventory.add(it)
	h.inventory.gold = maxi(h.inventory.gold, 50000000)
	h.stats_dirty.emit()
	Game.ui_root.close_all()
	# --- Lape's table -------------------------------------------------------------------------------------------------
	var w := Game.ui_root.window(&"lape") as LapeWindow
	w.open_for("Lape the Ancient")
	await _frames(30)
	for i in mini(3, items.size()):
		w._lay(items[i], i)
	await _frames(10)
	w._appraise()
	for k in 30:
		if w.appraisal.get("eschaton", false):
			break
		w._redraw()
		await _frames(2)
	for n in w.get_children():
		if n is EschatonReveal:
			(n as EschatonReveal)._finish()
	await _frames(40)
	await _shot("lape_window")
	var slots := []
	for c in w.find_children("*", "ItemSlot", true, false):
		var s := c as ItemSlot
		if s.item != null and s.is_visible_in_tree():
			slots.append(s)
	print("TIP lape slots ", slots.size())
	var n := 0
	for s: ItemSlot in slots:
		var it := s.item
		TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": h}))
		await _frames(14)
		var ok := _measure("lape %d %s" % [n, it.display_name().left(28)], s)
		if not ok or n < 2:
			await _shot("lape_tip_%02d" % n)
		TooltipLayer.hide_for(null)
		await _frames(2)
		n += 1
	w.close_window()
	await _frames(10)
	# --- fixed anchors round the screen ------------------------------------------------------------------------------
	var vp := get_viewport().get_visible_rect().size
	var layer := CanvasLayer.new()
	add_child(layer)
	var spots := [Vector2(20, 20), Vector2(vp.x - 108, 20), Vector2(vp.x * 0.5, vp.y * 0.5), Vector2(20, vp.y - 108), Vector2(vp.x - 108, vp.y - 108)]
	var k := 0
	for at: Vector2 in spots:
		for it: ItemInstance in items.slice(0, 2):
			var anchor := ItemSlot.new(ItemSlot.Kind.DISPLAY, 88.0)
			anchor.position = at
			layer.add_child(anchor)
			anchor.set_item(it)
			await _frames(2)
			TooltipLayer.show_for(anchor, func() -> Control: return Tips.item(it, {"hero": h}))
			await _frames(14)
			if not _measure("anchor %d at %s" % [k, at], anchor):
				await _shot("anchor_%02d" % k)
			TooltipLayer.hide_for(null)
			anchor.queue_free()
			k += 1
	print("TIPS %s (%d problems)" % ["PASS" if fails == 0 else "FAIL", fails])
	get_tree().quit()

## Readable = wholly on screen, not shrunk below 80%, not covering its own anchor.
func _measure(label: String, anchor: Control) -> bool:
	var tl := TooltipLayer.instance
	var p: Control = tl._panel if tl else null
	if p == null or not is_instance_valid(p):
		fails += 1
		print("TIP FAIL %s: no tooltip" % label)
		return false
	var vp := get_viewport().get_visible_rect()
	var r := Rect2(p.position, p.size * p.scale)
	var off := Vector2(maxf(0.0, vp.position.x - r.position.x) + maxf(0.0, r.end.x - vp.end.x),
		maxf(0.0, vp.position.y - r.position.y) + maxf(0.0, r.end.y - vp.end.y))
	var cover := r.intersects(anchor.get_global_rect())
	var ok := off.length() < 1.0 and p.scale.x >= 0.8 and p.modulate.a > 0.5 and not cover
	if not ok:
		fails += 1
	print("TIP %s %s rect=%s scale=%.2f off=%s covers_anchor=%s alpha=%.2f" % ["ok  " if ok else "FAIL", label, r, p.scale.x, off, cover, p.modulate.a])
	return ok
