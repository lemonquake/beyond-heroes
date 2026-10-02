extends TestCase
## bh-023: the hero's own body. Looks (data rules, saves old and new, look codes), the body model (every class's clips,
## the player's own clips, shape keys), the look on a CharacterVisual (shader, shape keys, sizes, hair), worn equipment
## (every wearable has a fitted model, cut-outs, helms and hair, budgets), other players' heroes, and the creator.

const SLOT := 98

func _init() -> void:
	strict = true

func _visual(look := {}) -> CharacterVisual:
	var v := CharacterVisual.new()
	host.add_child(v)
	v.setup(HeroLook.MODEL, 1.0, Color(0.7, 0.2, 0.2), &"knight")
	v.set_look(look)
	return v

# ---- Looks ------------------------------------------------------------------------------------------------------

func test_defaults_are_complete_and_plain() -> void:
	var d := HeroLook.defaults()
	for k in HeroLook.SLIDERS:
		ok(d.has(k), "default has slider %s" % k)
		var s: Array = HeroLook.SLIDERS[k]
		ok(float(s[1]) <= float(s[0]) and float(s[0]) <= float(s[2]), "slider %s default inside its range" % k)
	for k in HeroLook.CHOICES:
		ok(HeroLook.choice_ids(k).has(d[k]), "default %s is a listed style" % k)
	ok(HeroLook.is_plain(d), "defaults are the plain hero")
	ok(HeroLook.is_plain({}), "an empty look is the plain hero")
	eq(HeroLook.to_save(d).size(), 0, "the plain hero stores nothing")
	for k in HeroLook.SHAPE_KEYS:
		ok(HeroLook.SLIDERS.has(k), "shape key %s has a slider" % k)
	done()

func test_sanitize_clamps_and_drops_junk() -> void:
	var d := HeroLook.sanitize({"nose_long": 99.0, "height": -5, "skin": "zzzzzz", "hair": "laser_mullet", "eye_color": "FF0000",
		"evil": "payload", "show_helm": "yes", "eye_size": NAN, "brow_color": ""})
	eq(d["nose_long"], HeroLook.SLIDERS["nose_long"][2], "slider clamped to its top")
	eq(d["height"], HeroLook.SLIDERS["height"][1], "slider clamped to its bottom")
	eq(d["skin"], HeroLook.COLORS["skin"], "a bad colour falls back")
	eq(d["hair"], "shaved", "an unknown style falls back")
	eq(d["eye_color"], "ff0000", "colours are lower-cased")
	ok(not d.has("evil"), "unknown keys are dropped")
	eq(d["show_helm"], true, "a non-boolean flag falls back")
	eq(d["eye_size"], 1.0, "a non-finite slider falls back")
	eq(d["brow_color"], "", "an empty follow-the-hair colour is kept")
	eq(HeroLook.sanitize("not a dictionary"), HeroLook.defaults(), "anything that is not a dictionary is the plain hero")
	var saved := HeroLook.to_save(d)
	ok(saved.has("nose_long") and saved.has("eye_color") and not saved.has("skin"), "only the differences are stored")
	eq(HeroLook.sanitize(saved)["nose_long"], d["nose_long"], "a stored look reads back the same")
	done()

func test_presets_and_random_looks_are_valid() -> void:
	for p in HeroLook.PRESETS:
		var d := HeroLook.preset(p[0])
		eq(HeroLook.sanitize(d), d, "preset %s is already clean" % p[0])
		for k in p[2]:
			eq(d[k], HeroLook.sanitize(p[2])[k], "preset %s keeps %s" % [p[0], k])
	var r := rng(7)
	for i in 40:
		var d := HeroLook.random(r, float(i % 3) * 0.5)
		eq(HeroLook.sanitize(d), d, "random look %d is clean" % i)
	eq(HeroLook.signature(HeroLook.preset("goblin")), HeroLook.signature(HeroLook.preset("goblin")), "signature is stable")
	ok(HeroLook.signature(HeroLook.preset("goblin")) != HeroLook.signature({}), "signature tells looks apart")
	done()

func test_look_code_round_trip() -> void:
	var look := HeroLook.preset("fey")
	var code := HeroCreator.CODE_PREFIX + Marshalls.utf8_to_base64(JSON.stringify(HeroLook.to_save(look)))
	eq(HeroCreator.decode(code), look, "a look code restores the look")
	eq(HeroCreator.decode("  " + code + "\n"), look, "spaces around a code are ignored")
	ok(HeroCreator.decode("hello") == null, "plain text is not a look code")
	ok(HeroCreator.decode(HeroCreator.CODE_PREFIX + "%%%") == null, "a broken code is refused")
	done()

# ---- Saves -------------------------------------------------------------------------------------------------------

func test_old_saves_load_as_the_plain_hero() -> void:
	var h := Game.new_hero(&"mage", "Elder")
	var d := h.to_dict()
	d.erase("look")                                  # a save written before bh-023
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(d)))
	ok(back != null, "an old save loads")
	ok(back.look.is_empty(), "an old save has no look")
	ok(HeroLook.is_plain(back.look), "which is the plain hero")
	eq(String(back.cls.id), "mage", "class kept")
	done()

func test_look_survives_a_save() -> void:
	var h := Game.new_hero(&"ranger", "Styled")
	h.look = HeroLook.to_save(HeroLook.preset("goblin"))
	var back := HeroData.from_dict(JSON.parse_string(JSON.stringify(h.to_dict())))
	eq(HeroLook.sanitize(back.look), HeroLook.preset("goblin"), "the look comes back from JSON")
	var junk := h.to_dict()
	junk["look"] = {"nose_long": "huge", "hair": 12, "x": [1, 2]}
	var safe := HeroData.from_dict(JSON.parse_string(JSON.stringify(junk)))
	ok(safe != null and HeroLook.is_plain(safe.look), "a damaged look loads as the plain hero")
	ok(SaveSystem.save_hero(h, SLOT), "a styled hero saves")
	var disk := SaveSystem.load_hero(SLOT)
	eq(HeroLook.sanitize(disk.look), HeroLook.preset("goblin"), "and loads from disk")
	SaveSystem.delete_slot(SLOT)
	done()

# ---- The body model ----------------------------------------------------------------------------------------------

func test_hero_model_has_every_class_clip() -> void:
	ok(ResourceLoader.exists(HeroLook.MODEL), "hero.glb is imported")
	var v := _visual()
	ok(v.hero != null, "the hero body is recognised")
	ok(not v.fallback, "no fallback capsule")
	# every clip of the shared library (so any class, weapon and skill animates on the hero)
	var knight: Node = load(DB.class_def(&"knight").model_path).instantiate()
	var kap: AnimationPlayer = knight.find_children("*", "AnimationPlayer", true, false)[0]
	var missing := []
	for n in kap.get_animation_list():
		if not v.has_anim(n):
			missing.append(n)
	knight.free()
	eq(missing.size(), 0, "clips the class models have and the hero lacks: %s" % str(missing))
	for c in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		ok(v.has_anim(StringName("idle_%s" % c)), "%s idle" % c)
	for wt: WeaponTypeDef in DB.weapon_types.values():
		for a in wt.light_anims + [wt.heavy_anim]:
			if a != &"" and not String(a).begins_with("crossbow"):
				ok(v.has_anim(a), "%s attack clip %s" % [wt.id, a])
	# the player's own five clips, with their timing
	for n in [&"hero_walk", &"hero_run", &"hero_stroll", &"hero_alert", &"hero_axe_smash"]:
		ok(v.has_anim(n), "own clip %s" % n)
		ok(DB.anim(n).has("length"), "own clip %s has metadata" % n)
	ok(float(DB.anim(&"hero_walk").get("ground_speed", 0.0)) > 1.0, "walk ground speed measured")
	ok(float(DB.anim(&"hero_run").get("ground_speed", 0.0)) > 4.0, "run ground speed measured")
	near(v.ground_speed_run, float(DB.anim(&"hero_run").ground_speed), 0.001, "the hero runs at its own clip's pace")
	near(float(DB.anim(&"hero_axe_smash").length), float(DB.anim(&"gs_heavy").length), 0.04, "the smash lasts as long as the clip it replaces")
	eq(DB.anim(&"hero_axe_smash").hits, DB.anim(&"gs_heavy").hits, "and strikes at the same moment")
	ok(v.has_anim(&"block") and v._clip(&"block_loop") == &"block", "the guard pose resolves")
	v.clip_alias = {&"gs_heavy": &"hero_axe_smash"}
	eq(v._clip(&"gs_heavy"), &"hero_axe_smash", "a great axe's heavy is the player's smash")
	v.free()
	done()

func test_look_reaches_the_model() -> void:
	var v := _visual(HeroLook.preset("goblin"))
	var hb := v.hero
	var look := HeroLook.preset("goblin")
	for k in HeroLook.SHAPE_KEYS:
		var i := hb.body.find_blend_shape_by_name(StringName(k))
		ok(i >= 0, "body has shape key %s" % k)
		near(hb.body.get_blend_shape_value(i), float(look[k]), 0.0001, "shape key %s set" % k)
	eq(hb.skin.get_shader_parameter(&"eye_style"), HeroLook.choice_index("eye", "cat"), "eye style in the shader")
	near(float(hb.skin.get_shader_parameter(&"eye_size")), 1.9, 0.0001, "eye size in the shader")
	var sc: Vector3 = hb.skin.get_shader_parameter(&"skin_color")
	near(sc.y, Color.html("5f8f4e").g, 0.001, "skin colour in the shader")
	var sk := v.skeleton
	near(sk.get_bone_pose_scale(sk.find_bone("head")).x, 1.45, 0.0001, "head size on the head bone")
	near(sk.get_bone_pose_scale(sk.find_bone("hand.R")).x, 1.5, 0.0001, "hand size on the hand bone")
	near(sk.get_bone_pose_scale(sk.find_bone("weapon.R")).x, 1.0 / 1.5, 0.0001, "the weapon keeps its size in a big fist")
	near(v.model.scale.y, 0.84, 0.0001, "height scales the model")
	eq(HeroLook.sanitize(v.appearance["look"]), look, "the look travels in the appearance")
	if ResourceLoader.exists(HeroLook.HAIR_MODEL % "mohawk"):
		ok(hb._hair != null and hb._hair.visible, "the modelled hair is on the head")
		var li := hb._hair.find_blend_shape_by_name(&"length")
		ok(li >= 0, "hair has a length key")
		near(hb._hair.get_blend_shape_value(li), 1.0, 0.0001, "hair length set")
		ok(v._meshes.has(hb._hair), "hair joins the hit flash")
	# the animation does not undo the sizes
	v.update_locomotion(Vector2(0, 3), false, 0.0, 0.1)
	for f in 4:
		await host.get_tree().process_frame
	near(sk.get_bone_pose_scale(sk.find_bone("head")).x, 1.45, 0.0001, "head size survives the animation")
	v.set_look({})
	near(sk.get_bone_pose_scale(sk.find_bone("head")).x, 1.0, 0.0001, "the plain look resets the head")
	ok(hb._hair == null, "and removes the hair model")
	ok(not v.appearance["look"].size() > 0, "and sends nothing")
	v.set_opacity(0.4)
	near(float(hb.skin.get_shader_parameter(&"opacity")), 0.4, 0.0001, "stealth reaches the skin")
	v.set_opacity(1.0)
	v.free()
	done()

# ---- Worn equipment ----------------------------------------------------------------------------------------------

func _wearables() -> Array:
	var out := []
	for b: ItemBaseDef in DB.item_bases.values():
		if b.category in [&"helm", &"inner_garment", &"armor", &"gloves", &"boots", &"accessory"]:
			out.append(b)
	return out

func test_every_wearable_has_a_worn_model() -> void:
	var own := 0
	for b: ItemBaseDef in _wearables():
		if BossSetVisuals.has_theme(b.set_id):
			ok(b.model_path() != "", "boss piece %s keeps its regalia" % b.id)
			continue
		ok(HeroWear.has_model(String(b.id)), "%s has its own worn model" % b.id)
		own += 1
	ok(own >= 58, "all plain wearables counted (%d)" % own)
	for id in [HeroWear.UNDER_BODY, HeroWear.UNDER_HANDS, HeroWear.UNDER_FEET, HeroWear.SHOES]:
		ok(HeroWear.has_model(id), "shared piece %s" % id)
	done()

func test_worn_models_fit_the_skeleton_and_the_budget() -> void:
	var v := _visual()
	var limits := {&"helm": 1600, &"inner_garment": 5600, &"armor": 8400, &"gloves": 1800, &"boots": 1600, &"accessory": 300}   # bh-031: the refined chest (female bust) adds ~1,100 to plate coats
	for b: ItemBaseDef in _wearables():
		if not HeroWear.has_model(String(b.id)):
			continue
		var sided := b.category in [&"gloves", &"boots", &"accessory"]
		var meshes := HeroWear.build({"id": String(b.id), "side": "L" if sided else ""}, v.skeleton)
		ok(not meshes.is_empty(), "%s builds" % b.id)
		var tris := 0
		for m in meshes:
			ok(m.skin != null, "%s is skinned" % b.id)
			for s in m.mesh.get_surface_count():
				tris += m.mesh.surface_get_array_index_len(s) / 3
			ok(m.mesh.get_surface_count() <= 5, "%s uses at most five materials (%d)" % [b.id, m.mesh.get_surface_count()])
			if b.category in [&"inner_garment", &"armor"]:
				for k in HeroLook.BODY_KEYS:
					ok(m.find_blend_shape_by_name(StringName(k)) >= 0, "%s follows the %s slider" % [b.id, k])
			for k in HeroLook.BODY_KEYS:
				var i := m.find_blend_shape_by_name(StringName(k))
				if i >= 0:
					near(m.get_blend_shape_value(i), 0.0, 0.0001, "%s starts with %s at rest" % [b.id, k])
			m.free()
		ok(tris <= int(limits[b.category]), "%s within its triangle budget (%d of %d)" % [b.id, tris, limits[b.category]])
	v.free()
	done()

func test_dressing_the_hero() -> void:
	var h := Game.new_hero(&"knight", "Dresser")
	var v := _visual()
	v.dress_equipment(h.equipment)
	var hb := v.hero
	ok(hb._wear.size() >= 3, "the knight's starting kit is worn (%d pieces)" % hb._wear.size())
	for m in hb._wear:
		eq(m.get_parent(), v.skeleton, "a worn piece hangs on the skeleton")
		ok(v._meshes.has(m), "and joins the hit flash")
	ok(hb._wear.any(func(m): return String(m.name).begins_with("Wear_" + HeroWear.SHOES)), "no boots: plain shoes")
	var hide1: Vector2 = hb.skin.get_shader_parameter(&"hide_z1")
	ok(hide1.x < 0.5 and hide1.y > 1.3, "the covered trunk and legs are cut from the skin (%s)" % hide1)
	var count := hb._wear.size()
	v.dress_equipment(h.equipment)
	eq(hb._wear.size(), count, "dressing again changes nothing")
	# a build slider reaches the clothes
	v.set_look({"belly": 1.5})
	var armor: MeshInstance3D = null
	for m in hb._wear:
		if String(m.name) == "Wear_iron_hauberk":
			armor = m
	ok(armor != null, "the hauberk is worn")
	if armor:
		near(armor.get_blend_shape_value(armor.find_blend_shape_by_name(&"belly")), 1.5, 0.0001, "the hauberk follows the belly")
	# helm and hair
	v.set_look({"hair": "long"})
	if hb._hair:
		ok(not hb._hair.visible, "a helm hides the hair")
	v.set_look({"hair": "long", "show_helm": false})
	v.dress_equipment(h.equipment)
	ok(not hb._wear.any(func(m): return String(m.name) == "Wear_iron_helm"), "the helm can be left off")
	if hb._hair:
		ok(hb._hair.visible, "and the hair shows again")
	# boots replace the shoes on that foot only
	h.equipment.slots[&"boots_1"] = DB.make_item(&"iron_sabaton", BH.Rarity.COMMON, 1, 3)
	v.dress_equipment(h.equipment)
	ok(hb._wear.any(func(m): return String(m.name) == "Wear_iron_sabaton_L"), "the left boot is worn on the left")
	ok(not hb._wear.any(func(m): return String(m.name) == "Wear_iron_sabaton_R"), "and not on the right")
	ok(hb._wear.any(func(m): return String(m.name) == "Wear_%s_R" % HeroWear.SHOES), "the right foot keeps its shoe")
	# nothing on: nothing worn, nothing cut
	var bare := Equipment.new()
	v.dress_equipment(bare)
	eq(hb._wear.size(), 0, "bare: no pieces")
	eq(hb.skin.get_shader_parameter(&"hide_z1"), HeroBody.NO_HIDE, "bare: no cut-outs")
	v.free()
	done()

func test_boss_regalia_on_the_hero() -> void:
	var h := Game.new_hero(&"knight", "Regal")
	for slot in h.equipment.slots:
		var base := DB.item_base(StringName("boss_dragonforge_%s" % slot))
		h.equipment.slots[slot] = DB.make_item(base.id, BH.Rarity.MASTER, 30, 5) if base else null
	var v := _visual()
	v.dress_equipment(h.equipment)
	ok(v._set_nodes.size() >= 7, "the regalia is attached (%d nodes)" % v._set_nodes.size())
	ok(v.hero._wear.any(func(m): return String(m.name) == "Wear_" + HeroWear.UNDER_BODY), "with a plain under-layer beneath the plates")
	ok(v.hero._hide_hair, "a great helm hides the hair")
	var plan := HeroWear.plan(h.equipment)
	ok(not plan.pieces.any(func(p): return p.id == HeroWear.SHOES), "regalia greaves need no shoes")
	v.free()
	done()

func test_full_outfit_stays_in_budget() -> void:
	# the heaviest plain outfit: what one hero costs the renderer
	var h := Game.new_hero(&"knight", "Heavy")
	for id in [&"visored_greathelm", &"chain_shirt", &"warden_plate", &"spiked_gauntlet", &"spiked_gauntlet", &"warden_greave", &"warden_greave",
			&"gold_amulet", &"silver_ring"]:
		var it := DB.make_item(id, BH.Rarity.COMMON, 1, 3)
		if it:
			h.equipment.slots[h.equipment.auto_slot(it)] = it
	var v := _visual(HeroLook.preset("veteran"))
	v.dress_equipment(h.equipment)
	var tris := 0
	var surfaces := 0
	for m in v._meshes:
		if is_instance_valid(m) and m.mesh:
			for s in m.mesh.get_surface_count():
				surfaces += 1
				tris += (m.mesh.surface_get_array_index_len(s) if m.mesh.surface_get_array_index_len(s) > 0 else m.mesh.surface_get_array_len(s)) / 3
	ok(tris <= 48000, "a fully dressed hero is at most 48k triangles (%d)" % tris)
	ok(surfaces <= 40, "and at most 40 draw surfaces (%d)" % surfaces)
	v.free()
	done()

# ---- Other players ---------------------------------------------------------------------------------------------

func test_remote_hero_wears_their_look_and_gear() -> void:
	var avatar := NetAvatar.new().setup(23, "p", {"name": "Friend", "lvl": 5})
	host.add_child(avatar)
	var look := HeroLook.to_save(HeroLook.preset("fey"))
	var app := {"model": HeroLook.MODEL, "scale": 1.0, "pers": "mage", "weapons": {}, "look": look,
		"set_gear": {"armor": "iron_hauberk", "helm": "iron_helm", "boots_1": "iron_hauberk"}}
	avatar.set_appearance(JSON.parse_string(JSON.stringify(app)))
	ok(avatar.visual.hero != null, "the remote hero has the hero body")
	eq(HeroLook.sanitize(avatar.visual.hero.look), HeroLook.preset("fey"), "with the sender's look")
	ok(avatar.visual.hero._wear.any(func(m): return String(m.name) == "Wear_iron_hauberk"), "and their armour")
	ok(not avatar.visual.hero._wear.any(func(m): return String(m.name).begins_with("Wear_iron_hauberk_")), "an item in the wrong slot is ignored")
	app["look"] = {"nose_long": 1e9, "hair": {"bad": true}}
	avatar.set_appearance(app)
	near(float(avatar.visual.hero.look["nose_long"]), HeroLook.SLIDERS["nose_long"][2], 0.0001, "a hostile look is clamped")
	app.erase("look")
	avatar.set_appearance(app)
	ok(HeroLook.is_plain(avatar.visual.hero.look), "no look means the plain hero")
	avatar.queue_free()
	await host.get_tree().process_frame
	done()

# ---- The creator -------------------------------------------------------------------------------------------------

func test_creator_pages_cover_the_look() -> void:
	var seen := {}
	for page in HeroCreator.PAGES:
		for ctl in page[3]:
			match String(ctl[0]):
				"slider":
					ok(HeroLook.SLIDERS.has(ctl[1]), "slider %s exists" % ctl[1])
					seen[ctl[1]] = true
				"choice":
					ok(HeroLook.CHOICES.has(ctl[1]), "style list %s exists" % ctl[1])
					seen[ctl[1]] = true
				"color":
					ok(HeroLook.COLORS.has(ctl[1]), "colour %s exists" % ctl[1])
					ok(HeroCreator.TONES.has(ctl[3]), "swatches %s exist" % ctl[3])
					seen[ctl[1]] = true
				"flag":
					ok(HeroLook.FLAGS.has(ctl[1]), "flag %s exists" % ctl[1])
					seen[ctl[1]] = true
	for k in HeroLook.defaults():
		if k != "v":
			ok(seen.has(k), "the creator has a control for %s" % k)
	eq(HeroCreator._percent("nose_long", HeroLook.SLIDERS["nose_long"][2]), "+100", "a slider's top reads +100")
	eq(HeroCreator._percent("nose_long", 0.0), "0", "its usual value reads 0")
	eq(HeroCreator._percent("height", HeroLook.SLIDERS["height"][1]), "-100", "its bottom reads -100")
	done()

func test_creator_edits_and_returns_a_look() -> void:
	var c := HeroCreator.new()
	c.class_id = &"mage"
	c.look = HeroLook.preset("scholar")
	host.add_child(c)
	await host.get_tree().process_frame
	ok(c.preview.visual != null and c.preview.visual.hero != null, "the creator shows the hero body")
	var got := [null]
	c.done.connect(func(l: Dictionary) -> void: got[0] = l)
	for i in HeroCreator.PAGES.size():
		c._show_page(i)
	c._change("nose_long", 2.0)
	c._change("hair", "bald")
	near(float(c.preview.visual.hero.look["nose_long"]), 2.0, 0.0001, "a change reaches the preview")
	eq(c._undo.size(), 2, "two edits, two undo steps")
	c._change("nose_long", 2.5)
	eq(c._undo.size(), 3, "a new control is a new undo step")
	c._undo_last()
	near(float(c.look["nose_long"]), 2.0, 0.0001, "undo steps back")
	c._random(1.0)
	eq(HeroLook.sanitize(c.look), c.look, "a wild roll is still a valid look")
	c._set_look(HeroLook.preset("golem"), "t")
	c.done.emit(HeroLook.to_save(c.look))
	eq(HeroLook.sanitize(got[0]), HeroLook.preset("golem"), "done hands back the look")
	c.queue_free()
	await host.get_tree().process_frame
	done()
