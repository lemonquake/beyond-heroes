extends Node
## Real-renderer regression capture for role portraits, the HUD ID picture and
## missing-picture save cards. godot --path game res://tests/tools/capture_hero_portraits.tscn
## -- --out=<absolute path>. Also captures the legacy render_hero API and personas.

const CLASSES := [&"knight", &"mage", &"ranger", &"shadowblade"]
var out := ""
var failures := 0

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	out = ProjectSettings.globalize_path("res://../output/hero-portraits")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			out = arg.substr(6)
	DirAccess.make_dir_recursive_absolute(out)
	if DisplayServer.get_name() == "headless":
		_fail("A real renderer is required for portrait capture.")
		get_tree().quit(1)
		return
	var signatures := {}
	for class_id in CLASSES:
		var hero := Game.new_hero(class_id, "Portrait test")
		hero.look = {"body": "class"}
		# Equal looks/equipment exercise the class portion of both cache signatures.
		hero.equipment = Equipment.new()
		var sig := IdPicture.signature(hero)
		if signatures.has(sig):
			_fail("ID picture cache shares a signature across classes: %s" % class_id)
		signatures[sig] = true
		var img := await PortraitStudio.render_hero(hero.look, hero.equipment, ProfilePicture.SIZE, class_id)
		_save(img, String(class_id) + "_class")
		var custom := await PortraitStudio.render_hero({}, hero.equipment, ProfilePicture.SIZE, class_id)
		_save(custom, String(class_id) + "_custom")
		if img != null and custom != null and img.get_data() == custom.get_data():
			_fail("Class and custom portraits are identical: %s" % class_id)
		await IdPicture.refresh(hero, true)
		var id_img := Image.new()
		if id_img.load_jpg_from_buffer(hero.id_pic) == OK:
			_save(id_img, String(class_id) + "_hud")
			if img != null:
				var expected_id := Image.new()
				if expected_id.load_jpg_from_buffer(img.save_jpg_to_buffer(0.88)) != OK or not _same_portrait(id_img, expected_id):
					_fail("HUD ID picture differs from the selected class render: %s" % class_id)
		else:
			_fail("HUD ID picture is missing: %s" % class_id)
		var card := TextureRect.new()
		add_child(card)
		var saved := hero.to_dict()
		saved.erase("id_pic")
		var fallback := UIArt.portrait(String(class_id))
		MainMenu.hero_picture(card, saved, String(class_id))
		for frame in 120:
			if card.texture != fallback:
				break
			await get_tree().process_frame
		if card.texture != null and card.texture != fallback:
			var card_img := card.texture.get_image()
			_save(card_img, String(class_id) + "_card")
			if img != null and not _same_portrait(card_img, img):
				_fail("Save card differs from the selected class render: %s" % class_id)
		else:
			_fail("Save card never received its portrait: %s" % class_id)
		card.queue_free()
	_save(await PortraitStudio.render_hero({}, Equipment.new(), ProfilePicture.SIZE), "legacy_api")
	_save(await PortraitStudio.render_persona({"look": HeroLook.preset("scholar")}, ProfilePicture.SIZE), "persona")
	await get_tree().process_frame
	print("HERO_PORTRAIT_CAPTURE_DONE failures=", failures, " ", out)
	get_tree().quit(0 if failures == 0 else 1)

func _save(img: Image, label: String) -> void:
	if img == null or img.is_empty():
		_fail("Portrait is empty: " + label)
	elif img.get_size() != Vector2i(ProfilePicture.SIZE, ProfilePicture.SIZE):
		_fail("Portrait has unexpected dimensions: " + label)
	elif img.save_png(out.path_join(label + ".png")) != OK:
		_fail("Cannot save portrait: " + label)

func _fail(message: String) -> void:
	failures += 1
	push_error(message)

func _same_portrait(actual: Image, expected: Image) -> bool:
	if actual.get_size() != expected.get_size() or actual.get_format() != expected.get_format():
		return false
	var a := actual.get_data()
	var b := expected.get_data()
	var difference := 0
	for i in a.size():
		difference += absi(int(a[i]) - int(b[i]))
	# Hair moves with shader TIME, and ID pictures use JPEG. Compare rendered
	# pixels with a two-level (2/255) mean RGB allowance rather than byte equality.
	return float(difference) / maxf(1.0, a.size()) <= 2.0
