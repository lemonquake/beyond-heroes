extends TestCase
## Source models, real source bow motion, equipment sockets, saves and switching.

func _init() -> void:
	strict = true

func _visual(class_id: StringName, body := "class") -> CharacterVisual:
	var visual := CharacterVisual.new()
	host.add_child(visual)
	visual.setup_hero(class_id, {"body": body}, DB.class_def(class_id).tint)
	return visual

func test_class_selection_keeps_legacy_and_custom_saves() -> void:
	for class_id in HeroModels.MODELS:
		eq(HeroModels.model_for(class_id, {}), HeroLook.MODEL, "legacy %s keeps editable body" % class_id)
		eq(HeroModels.model_for(class_id, {"body": "custom"}), HeroLook.MODEL, "explicit custom body")
		eq(HeroModels.model_for(class_id, {"body": "class"}), HeroModels.MODELS[class_id], "class body is explicit")
		var hero := Game.new_hero(class_id, "Model test")
		hero.look = HeroLook.to_save(HeroLook.sanitize({"body": "class", "nose_long": 1.2}))
		var copy := HeroData.from_dict(JSON.parse_string(JSON.stringify(hero.to_dict())))
		eq(copy.look, hero.look, "class selection and custom sliders survive save round trip")
	eq(HeroLook.sanitize({"body": "remote-file.exe"})["body"], "custom", "unknown model choice is rejected")
	done()

func test_source_bodies_have_all_weapon_clips_and_sockets() -> void:
	for class_id in HeroModels.MODELS:
		var visual := _visual(class_id)
		ok(not visual.fallback and visual.skeleton != null, "%s imports with a real skeleton" % class_id)
		for bone in ["hips", "hand.L", "hand.R", "weapon.L", "weapon.R"]:
			ok(visual.skeleton.find_bone(bone) >= 0, "%s has %s" % [class_id, bone])
		for wt: WeaponTypeDef in DB.weapon_types.values():
			for clip in wt.light_anims + [wt.heavy_anim, wt.idle_anim]:
				if clip != &"":
					ok(visual.has_anim(clip), "%s supports %s with %s" % [class_id, wt.id, clip])
		for clip in HeroAnimations.BOW_NAMES:
			var animation := visual.anim_player.get_animation(clip)
			eq(animation.get_meta("source_clip", &""), HeroAnimations.BOW_NAMES[clip], "%s uses the actual source %s" % [class_id, clip])
			near(animation.length, float(DB.anim(clip).length), 0.0001, "%s preserves %s duration" % [class_id, clip])
			if DB.anim(clip).has("release"):
				near(float(animation.get_meta("release", -1.0)), float(DB.anim(clip).release), 0.0001, "%s preserves %s release metadata" % [class_id, clip])
		var equipment := Equipment.new()
		equipment.slots[&"armor"] = DB.make_item(&"boss_dragonforge_armor", BH.Rarity.MASTER, 30, 1)
		visual.dress_equipment(equipment)
		ok(not visual._set_nodes.is_empty(), "%s retains equipped boss-set regalia" % class_id)
		for node in visual._set_nodes:
			ok(node is BoneAttachment3D and visual.skeleton.find_bone(node.bone_name) >= 0, "%s effect follows an actual model bone" % class_id)
		if class_id == &"ranger":
			ok(visual._role_body != null, "Hunter has the source Blood Ranger body/look/outfit")
			ok(visual._female and visual._loco_clip(&"run") == &"fem_run", "Hunter keeps the source female locomotion clips")
			eq(visual._role_body.look["hair_color"], "861620", "source crimson hair")
			ok(visual._role_body._wear.size() > 0, "source outfit is rendered")
			ok(visual.hero == null, "fixed Hunter outfit is separate from custom equipment dressing")
		visual.free()
	done()

func test_bow_uses_source_motion_with_unchanged_release_and_duration() -> void:
	var source := load(HeroAnimations.BOW) as AnimationLibrary
	ok(source != null, "real source bow resource is installed")
	if source == null:
		done()
		return
	var visual := _visual(&"ranger")
	for name in [&"bow_1", &"bow_2", &"bow_release"]:
		var clip := visual.anim_player.get_animation(name)
		var original := source.get_animation(clip.get_meta("source_clip"))
		var release := float(DB.anim(name).release)
		near(clip.length, float(DB.anim(name).length), 0.0001, "%s keeps original gameplay duration" % name)
		near(float(clip.get_meta("release")), release, 0.0001, "%s keeps gameplay release" % name)
		var source_release := float(clip.get_meta("source_release"))
		near(HeroAnimations.fit_time(source_release, original.length, clip.length, source_release, release), release, 0.000001, "source loose pose lands exactly on release")
		# A genuine port keeps every source rotation, including motion between keys.
		# Compare by bone at matching source/target times throughout the action.
		for track in original.get_track_count():
			if original.track_get_type(track) != Animation.TYPE_ROTATION_3D:
				continue
			for step in 31:
				var source_time := original.length * float(step) / 30.0
				var target_time := HeroAnimations.fit_time(source_time, original.length, clip.length, source_release, release)
				var a := original.rotation_track_interpolate(track, source_time)
				var b := clip.rotation_track_interpolate(track, target_time)
				ok(absf(a.dot(b)) > 0.999, "%s retains source pose at sample %d / bone %d" % [name, step, track])
	visual.attach_weapon(&"main", DB.item_base(&"hunters_bow").model_path())
	eq((visual._weapon_nodes[&"main"] as BoneAttachment3D).bone_name, "weapon.L", "the equipped bow follows the source bow hand")
	visual.detach_weapon(&"main")
	visual.attach_weapon(&"main", DB.item_base(&"ashwood_crossbow").model_path())
	eq((visual._weapon_nodes[&"main"] as BoneAttachment3D).bone_name, "weapon.R", "crossbow socket is preserved")
	visual.free()
	done()

func test_local_and_remote_body_switches_reapply_equipped_weapons_and_gems() -> void:
	var preview := CharacterPreview.new()
	host.add_child(preview)
	var hero := Game.new_hero(&"ranger", "Model test")
	var weapon := hero.equipment.get_item(&"main_weapon")
	weapon.gems = [&"ember_orbital"]
	weapon.sockets = 1
	var avatar := NetAvatar.new().setup(23, "p", {"name": "Model test", "lvl": 1})
	host.add_child(avatar)
	for body in ["class", "custom", "class", "custom"]:
		hero.look = {"body": body, "hair": "long", "nose_long": 0.5}
		preview.show_class(&"ranger", hero)
		preview.set_look(hero.look)
		var visual := preview.visual
		ok(visual.has_weapon(&"main"), "local %s keeps real equipped weapon" % body)
		eq(visual.appearance.weapons[&"main"][0], weapon.base.model_path(), "local real model is preserved")
		ok(visual.appearance.get("gems", {}).has(&"main"), "local crystal presentation remains")
		var local_spirits := visual._weapon_nodes[&"main"].get_node_or_null(^"GemSpirits") as GemSpirits
		ok(local_spirits != null and local_spirits.count() == 1, "local equipped crystal effect is present")
		avatar.set_appearance(visual.appearance.duplicate(true))
		eq(avatar.visual.appearance.model, visual.appearance.model, "remote follows model switch")
		ok(avatar.visual.has_weapon(&"main"), "remote %s keeps equipped weapon" % body)
		var remote_spirits := avatar.visual._weapon_nodes[&"main"].get_node_or_null(^"GemSpirits") as GemSpirits
		ok(remote_spirits != null and remote_spirits.count() == 1, "remote equipped crystal effect is present")
		eq((avatar.visual._weapon_nodes[&"main"] as BoneAttachment3D).bone_name, "weapon.L", "remote bow stays in source hand")
		if body == "custom":
			ok(avatar.visual.hero != null and visual.hero != null, "custom body remains editable locally and remotely")
			near(float(visual.hero.look.nose_long), 0.5, 0.001, "stored sliders are restored")
		await host.get_tree().process_frame
		eq(avatar.find_children("Visual", "Node3D", false, false).size(), 1, "remote switch leaves exactly one visual")
	preview.free()
	avatar.free()
	done()

func test_shield_only_loadout_survives_body_replacement() -> void:
	var hero := Game.new_hero(&"knight", "Shield model test")
	hero.equipment.slots[&"main_weapon"] = null
	var shield := hero.equipment.get_item(&"sub_weapon")
	ok(shield != null and shield.base.category == &"shield", "fixture is shield-only")
	shield.sockets = 1
	shield.gems = [&"ember_orbital"]
	var player := Player.new()
	player.hero = hero
	player.stats = hero.compute_stats()
	player.visual = _visual(&"knight")
	for body in ["class", "custom", "class"]:
		player.visual.set_look({"body": body})
		player.refresh_equipment_visuals()
		ok(not player.visual.has_weapon(&"main"), "empty main hand remains empty")
		ok(player.visual.has_weapon(&"off"), "%s retains the equipped shield" % body)
		var holder: Node3D = player.visual._weapon_nodes[&"off"]
		var spirits := holder.get_node_or_null(^"GemSpirits") as GemSpirits
		ok(spirits != null and spirits.count() == 1, "%s retains shield crystals" % body)
	player.visual.free()
	player.free()
	done()

func test_shared_hunter_and_custom_library_is_independent_of_load_order() -> void:
	var signatures: Array = []
	for order in [[HeroLook.MODEL, HeroModels.HUNTER], [HeroModels.HUNTER, HeroLook.MODEL]]:
		# Ignore the resource cache so both orders begin with the exact imported,
		# unpatched library rather than an earlier test's shared resource.
		var scene := ResourceLoader.load(HeroLook.MODEL, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE_DEEP) as PackedScene
		var model := scene.instantiate() as Node3D
		host.add_child(model)
		var player := model.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
		var skeleton := model.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
		HeroAnimations.install(player, skeleton, order[0])
		var first := _clip_keys(player)
		HeroAnimations.install(player, skeleton, order[1])
		eq(_clip_keys(player), first, "second appearance never mutates an already installed shared library")
		signatures.append(first)
		model.free()
	eq(signatures[0], signatures[1], "Custom-first and Hunter-first produce the same clips")
	done()

func _clip_keys(player: AnimationPlayer) -> Array:
	var out: Array = []
	for name in player.get_animation_list():
		var clip := player.get_animation(name)
		var keys: Array = [name, clip.length, clip.loop_mode]
		for track in clip.get_track_count():
			keys.append([clip.track_get_path(track), clip.track_get_type(track)])
			for key in clip.track_get_key_count(track):
				keys.append([clip.track_get_key_time(track, key), clip.track_get_key_value(track, key)])
		out.append(hash(keys))
	return out
