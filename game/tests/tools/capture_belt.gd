extends Node
## Potion belt captures (bh-011): the Inventory's Potion Belt row, its chooser open, and the HUD / touch orbs after
## binding Q to a Swiftfoot Tonic.
##   godot --path game --resolution 1920x1080 res://tests/tools/capture_belt.tscn -- --class=knight --slot=98 [--touch=1] --out=<dir>

var args := {}
var out := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/belt")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.gd").new())
	_run.call_deferred()

func _run() -> void:
	for i in 900:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await get_tree().process_frame
	await _wait(2.0)
	var h := Game.hero
	for pair in [[&"swiftfoot_tonic", 3], [&"frost_flask", 5], [&"rejuvenation_elixir", 2], [&"antidote", 2]]:
		var it := DB.make_item(pair[0], BH.Rarity.COMMON, 1, hash(String(pair[0])))
		it.count = pair[1]
		h.inventory.add(it)
	var tag := "touch_" if Settings.touch_mode else ""
	Game.ui_root.toggle(&"inventory")
	await _wait(0.8)
	var inv: InventoryWindow = Game.ui_root.window(&"inventory")
	for c in inv.cells:
		if c.item and c.item.base.id == &"swiftfoot_tonic":
			inv._select(c)
	await _wait(0.3)
	await _shot(tag + "belt_inventory")
	var menu := BeltPicker.open(inv._belt_slots[0], h, 0)
	await _wait(0.5)
	await _shot(tag + "belt_chooser")
	if menu:
		menu.hide()
	BeltPicker.bind(h, 0, &"swiftfoot_tonic")
	BeltPicker.bind(h, 1, &"frost_flask")
	await _wait(0.4)
	await _shot(tag + "belt_bound")
	Game.ui_root.toggle(&"inventory")
	await _wait(1.0)
	await _shot(tag + "belt_hud")
	get_tree().quit()

func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout

func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("SHOT ", name)
