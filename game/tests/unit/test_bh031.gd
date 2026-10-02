extends TestCase
## bh-031: one body for everyone. The female figure (fitted from models/female_generic.obj) with her own clips, every
## townsperson / humanoid monster / Tempo drawn on the hero body (Persona, DataPersonas), the baked NPC ID portraits
## and the player's ID picture.

func _init() -> void:
	strict = true

func _ids_exist(p: Dictionary, who: String) -> void:
	for id in p.get("wear", []):
		ok(DB.item_base(StringName(id)) != null, "%s wears a real item (%s)" % [who, id])
	for k in ["main", "off"]:
		var id := String(p.get(k, ""))
		if id != "":
			ok(DB.item_base(StringName(id)) != null, "%s holds a real item (%s)" % [who, id])
	var sid := String(p.get("set", ""))
	if sid != "":
		ok(BossSetVisuals.has_theme(StringName(sid)), "%s wears a real boss collection (%s)" % [who, sid])
	var lk: Dictionary = p.get("look", {})
	for k in lk:
		ok(HeroLook.SLIDERS.has(k) or HeroLook.COLORS.has(k) or HeroLook.CHOICES.has(k) or HeroLook.FLAGS.has(k),
			"%s's look key %s is a HeroLook key" % [who, k])
		if HeroLook.CHOICES.has(k):
			ok(HeroLook.choice_ids(k).has(lk[k]), "%s's %s %s is a real style" % [who, k, lk[k]])
		if HeroLook.COLORS.has(k):
			ok(String(lk[k]).length() == 6 and String(lk[k]).is_valid_hex_number(), "%s's %s is a hex colour" % [who, k])

func test_female_figure_in_the_model() -> void:
	var n: Node = (load(HeroLook.MODEL) as PackedScene).instantiate()
	var body: MeshInstance3D
	var ap: AnimationPlayer
	for c in n.find_children("*", "", true, false):
		if c is MeshInstance3D and (c as MeshInstance3D).mesh.get_blend_shape_count() > 10:
			body = c
		if c is AnimationPlayer:
			ap = c
	ok(body != null and body.find_blend_shape_by_name(&"female") >= 0, "hero.glb carries the female shape key")
	for clip in [&"fem_idle", &"fem_walk", &"fem_stroll", &"fem_run"]:
		ok(ap != null and ap.has_animation(clip), "hero.glb carries %s" % clip)
		ok(DB.anim(clip).get("loop", false), "%s loops (hero_meta.json)" % clip)
	ok(float(DB.anim(&"fem_walk").get("ground_speed", 0.0)) > 1.0, "fem_walk has a measured ground speed")
	n.free()
	# clothing follows her: every worn model carries the key too
	var missing := []
	for id in ["iron_hauberk", "sage_robe", "traveler_coat", "brigandine", "linen_trousers", "_under_body", "_breeches"]:
		var w: Node = (load(HeroWear.DIR + id + ".glb") as PackedScene).instantiate()
		var has := false
		for m in w.find_children("*", "MeshInstance3D", true, false):
			has = has or (m as MeshInstance3D).find_blend_shape_by_name(&"female") >= 0
		if not has:
			missing.append(id)
		w.free()
	ok(missing.is_empty(), "worn pieces follow the female figure (missing: %s)" % [missing])
	done()

func test_female_look_rules() -> void:
	ok(HeroLook.SLIDERS.has("female") and HeroLook.BODY_KEYS.has("female") and HeroLook.SHAPE_KEYS.has("female"), "female is a body slider")
	var d := HeroLook.defaults()
	HeroLook.feminize(d)
	eq(float(d["female"]), 1.0, "feminize sets the figure")
	eq(String(d["beard"]), "none", "no beard on a woman by default")
	ok(HeroLook.to_save(HeroLook.sanitize(d)).has("female"), "the figure is saved (an optional key)")
	ok(not HeroLook.to_save(HeroLook.defaults()).has("female"), "an old save stays as it was")
	for id in ["shieldmaiden", "huntress", "matron"]:
		eq(float(HeroLook.preset(id)["female"]), 1.0, "preset %s is a woman" % id)
	var women := 0
	var rng := RandomNumberGenerator.new()
	rng.seed = 31
	for i in 200:
		if float(HeroLook.random(rng, 0.0)["female"]) > 0.5:
			women += 1
	ok(women > 60 and women < 140, "random looks are women about half the time (%d / 200)" % women)
	done()

func test_every_townsperson_has_a_persona() -> void:
	var missing := []
	for d: NpcDef in DB.npcs.values():
		var p := Persona.for_npc(d)
		if p.is_empty():
			missing.append(String(d.id))
			continue
		_ids_exist(p, String(d.id))
	ok(missing.is_empty(), "every NPC is drawn on the hero body (missing: %s)" % [missing])
	done()

func test_townsfolk_are_distinct() -> void:
	var seen := {}
	for id in DataPersonas.NPCS:
		var p: Dictionary = DataPersonas.NPCS[id]
		var key := str([Persona.look_of(p), p.get("wear", []), p.get("dye", {})])
		ok(not seen.has(key), "%s does not look exactly like %s" % [id, seen.get(key, "")])
		seen[key] = id
	done()

func test_npc_portraits_are_baked() -> void:
	for d: NpcDef in DB.npcs.values():
		ok(d.portrait.begins_with(DataPersonas.PORTRAIT_DIR) and ResourceLoader.exists(d.portrait),
			"%s's portrait is the baked ID shot (%s)" % [d.id, d.portrait])
	done()

func test_humanoid_monsters_have_personas() -> void:
	var drawn := 0
	for e: EnemyDef in DB.enemies.values():
		var p := Persona.for_enemy(e)
		if e.body_shape != &"humanoid" or DataPersonas.NOT_PEOPLE.has(String(e.id)):
			ok(p.is_empty(), "%s keeps its own model" % e.id)
			continue
		ok(not p.is_empty(), "%s is drawn on the hero body" % e.id)
		if p.is_empty():
			continue
		drawn += 1
		_ids_exist(p, String(e.id))
		var s := float(p.get("size", 0.0))
		ok(s >= 0.55 and s <= 2.6, "%s has a sensible size (%.2f)" % [e.id, s])
		if DataPersonas.ZARAEL.has(String(e.family)):
			eq(String(Persona.look_of(p)["eye_color"]), "ffffff", "%s's glow is Zarael white" % e.id)
	ok(drawn >= 60, "most humanoid monsters are people on the hero body (%d)" % drawn)
	done()

func test_persona_equipment() -> void:
	var eq_ := Persona.equipment_of({"wear": ["iron_gauntlet", "wayfarer_boot", "silver_ring", "copper_ring", "sage_robe"]})
	ok(eq_.get_item(&"gloves_1") != null and eq_.get_item(&"gloves_2") != null, "gloves go on both hands")
	ok(eq_.get_item(&"boots_1") != null and eq_.get_item(&"boots_2") != null, "boots go on both feet")
	ok(eq_.get_item(&"accessory_1") != null and eq_.get_item(&"accessory_2") != null, "two rings take two accessory slots")
	eq(String(eq_.get_item(&"armor").base.id), "sage_robe", "the robe is the armour")
	var set_eq := Persona.equipment_of({"set": "crimson_glory"})
	ok(set_eq.get_item(&"helm") != null and String(set_eq.get_item(&"helm").base.set_id) == "crimson_glory", "a boss collection is worn whole")
	ok(set_eq.get_item(&"main_weapon") == null, "a worn collection leaves the hands to the persona")
	done()

func test_dyes() -> void:
	eq(HeroWear.dye_key("BH_Cloth_Secondary__it_hw_crimson"), "cloth", "coloured cloth takes the cloth dye")
	eq(HeroWear.dye_key("BH_Cloth_Secondary__it_hw_black"), "trim", "dark cloth takes the trim dye")
	eq(HeroWear.dye_key("BH_Leather__it_hw_leather"), "leather", "leather takes the leather dye")
	eq(HeroWear.dye_key("BH_Mail__it_hw_mail_shirt"), "metal", "mail takes the metal tint")
	eq(HeroWear.dye_key("BH_Gem__it_hw_ruby"), "", "gems keep their colour")
	var d := {"cloth": "7a1a1a"}
	ok(HeroBody.layer_dye(d, "leggings").cloth != d.cloth, "the legs are a different shade")
	ok(HeroBody.layer_dye(d, "inner_garment").cloth != d.cloth, "the shirt is a different shade")
	eq(HeroBody.layer_dye(d, "armor").cloth, d.cloth, "the outer garment takes the cloth dye")
	eq(HeroBody.layer_dye({"cloth": "7a1a1a", "legs": "101010"}, "leggings").cloth, "101010", "legs can be set")
	done()

func test_dressed_persona_visual() -> void:
	var v := CharacterVisual.new()
	host.add_child(v)
	v.setup(Persona.MODEL, 1.0, Color.WHITE, &"")
	ok(v.hero != null, "the persona body is the hero body")
	var eq_ := Persona.apply(v, DataPersonas.npc(&"hald"))
	ok(eq_ != null and eq_.get_item(&"armor") != null, "Captain Hald wears his plate")
	eq(String(v.appearance.get("dye", {}).get("cloth", "")), "7a1a1a", "his colours travel with his appearance")
	ok((v.appearance.get("weapons", {}) as Dictionary).has(&"main"), "he holds his sword")
	# a female persona stands in her own idle
	var w := CharacterVisual.new()
	host.add_child(w)
	w.setup(Persona.MODEL, 1.0, Color.WHITE, &"")
	Persona.apply(w, DataPersonas.npc(&"hesta"))
	eq(w._loco_clip(&"idle"), &"fem_idle", "a woman's relaxed idle is fem_idle")
	eq(w._loco_clip(&"walk"), &"fem_walk", "and she walks in fem_walk")
	v.queue_free()
	w.queue_free()
	done()

func test_tempos_wear_class_garb() -> void:
	var eq_ := Persona.tempo_equipment(Equipment.new(), &"mystic")
	ok(eq_.get_item(&"armor") != null, "a Tempo with no armour is drawn in its class garb")
	var own := Equipment.new()
	var it := DB.make_item(&"iron_hauberk", BH.Rarity.COMMON, 5, 1)
	own.slots[&"armor"] = it
	eq(Persona.tempo_equipment(own, &"mystic").get_item(&"armor"), it, "its own armour wins over the garb")
	var a := Persona.tempo_look(7, &"archer", Color(0.6, 1.0, 0.7))
	var b := Persona.tempo_look(7, &"archer", Color(0.6, 1.0, 0.7))
	eq(a, b, "a Tempo's face is stable for its uid")
	ok(Persona.tempo_look(8, &"archer", Color.WHITE).has("skin"), "every Tempo has a face")
	done()

func test_id_picture_save_field() -> void:
	var h := Game.new_hero(&"knight", "IdPic")
	var img := Image.create(8, 8, false, Image.FORMAT_RGB8)
	img.fill(Color(0.4, 0.3, 0.2))
	h.id_pic = img.save_jpg_to_buffer(0.9)
	var back := HeroData.from_dict(h.to_dict())
	eq(back.id_pic, h.id_pic, "the ID picture survives a save")
	eq(ProfilePicture.shown_bytes(back), back.id_pic, "without a profile picture the ID picture is shown")
	back.profile_pic = h.id_pic.duplicate()
	back.profile_pic.append(0)
	eq(ProfilePicture.shown_bytes(back), back.profile_pic, "a chosen profile picture wins")
	var plain := HeroData.from_dict(Game.new_hero(&"mage", "Old").to_dict())
	ok(plain.id_pic.is_empty(), "an old save loads without one")
	ok(not ProfilePicture.bytes_of_save({"id_pic": Marshalls.raw_to_base64(h.id_pic)}).is_empty(), "a save card finds it")
	ok(IdPicture.signature(h) != IdPicture.signature(Game.new_hero(&"mage", "Other")), "another kit is another picture")
	done()

func test_cutscene_extras_are_people() -> void:
	ok(not DataPersonas.for_model("res://assets/characters/mage.glb").is_empty(), "the Registry's sealers are people")
	ok(not DataPersonas.for_model("hollow_soldier").is_empty(), "the Legion's soldiers are people")
	ok(DataPersonas.for_model("rune_golem").is_empty(), "a golem keeps its model")
	ok(not DataPersonas.npc(&"paul_david").is_empty(), "Paul David is drawn like in Olivar")
	# his cinematic clips come along onto the hero rig, and they move the hero's bones
	var a := CutsceneActor.make_persona(DataPersonas.npc(&"paul_david"), "paul_david")
	host.add_child(a)
	ok(a.has_clip(&"cs_pd_idle") and a.has_clip(&"cs_pd_shard"), "Paul David keeps his cutscene clips on the hero body")
	ok(a.has_clip(&"idle") and a.has_clip(&"fem_walk"), "and every hero clip")
	var anim := a.anim.get_animation(&"cs_pd_idle")
	var hits := 0
	for t in anim.get_track_count():
		var np := anim.track_get_path(t)
		if a.anim.get_node(a.anim.root_node).get_node_or_null(NodePath(String(np).get_slice(":", 0))) == a.skeleton:
			hits += 1
	ok(hits > 10, "the copied tracks point at the hero's skeleton (%d)" % hits)
	var kx := Persona.for_enemy(DB.enemy(&"kethrax"))
	var b := CutsceneActor.make_persona(kx, "kethrax")
	host.add_child(b)
	ok(b.has_clip(&"cs_kx_pull"), "Kethrax keeps his cutscene clips")
	a.queue_free()
	b.queue_free()
	done()
