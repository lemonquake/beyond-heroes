extends TestCase
## bh-038 Zarael pass:
##   - Zarael is for strong heroes: its surface monsters are 20 levels higher, its three Vaults 40 levels higher
##   - every world texture has mipmaps (the ground shimmered and crawled while the camera moved) and is VRAM compressed
##   - obsidian and basalt no longer draw as untextured black (the Barrens' glass growths and Obsidian Engine gate)
##   - each crystal set in a held weapon circles it as its own spirit, drawn and moving its family's way (GemSpirits)

func _init() -> void:
	strict = true

func test_zarael_levels() -> void:
	var want := {&"zr_coilwood": Vector2i(50, 56), &"zr_barrens": Vector2i(56, 62), &"bridge_of_death": Vector2i(62, 66),
		&"zr_citadel": Vector2i(66, 72)}
	for id in want:
		var d := DB.map_def(id)
		eq(Vector2i(d.level_min, d.level_max), want[id], "%s monsters are 20 levels higher" % id)
	eq(DataDungeons.level_range(&"jade_sepulchre"), Vector2i(73, 80), "the Jade Sepulchre is 40 levels higher")
	eq(DataDungeons.level_range(&"obsidian_engine"), Vector2i(79, 86), "the Obsidian Engine is 40 levels higher")
	eq(DataDungeons.level_range(&"veinworks"), Vector2i(85, 93), "the Veinworks is 40 levels higher")
	# every camp stays inside its map's band
	for path in ["zr_coilwood", "zr_barrens", "bridge_of_death", "zr_citadel"]:
		var s: GDScript = load("res://src/world/maps/%s.gd" % path)
		var d := DB.map_def(StringName(path))
		for c: Array in s.get_script_constant_map()["CAMPS"]:
			var lv: Vector2i = c[5] if c.size() > 6 else c[4]
			ok(lv.x >= d.level_min and lv.y <= d.level_max, "%s camp %s within %d-%d (%s)" % [path, c[0], d.level_min, d.level_max, lv])
	var lv_of := {}
	for o in Objectives.ZARAEL:
		lv_of[o.id] = int(o.get("level", 0))
	eq(lv_of["zr_ship"], 50, "the ship calls for a level-50 hero")
	eq(lv_of["zr_vault_jade"], 76, "the first Vault is recommended at 76")
	eq(Objectives.ZARAEL_LEVEL, 48, "a hero still on Salmonan is pointed at Zarael from level 48")
	done()

func test_world_textures_have_mipmaps() -> void:
	var bad := []
	for dir in ["res://assets/textures/", "res://assets/textures/legend/"]:
		for f in DirAccess.get_files_at(dir):
			if not (f.ends_with("_albedo.png.import") or f.ends_with("_normal.png.import") or f.ends_with("_rough.png.import")):
				continue
			var txt := FileAccess.get_file_as_string(dir + f)
			if not txt.contains("mipmaps/generate=true") or not txt.contains("compress/mode=2"):
				bad.append(f)
	eq(bad, [], "every world texture set is mipmapped and VRAM compressed")
	var t: Texture2D = load("res://assets/textures/terrace_paving_albedo.png")
	ok(t != null and t.get_image() != null and t.get_image().has_mipmaps(), "Agdao's paving loads with mipmaps")
	done()

func test_obsidian_is_not_black() -> void:
	for key in ["BH_Obsidian", "BH_Basalt"]:
		var m := MaterialLibrary.env(key) as StandardMaterial3D
		ok(m.albedo_texture != null, "%s is textured" % key)
		ok(m.albedo_color.get_luminance() >= 0.7, "%s keeps its texture's detail (tint %.2f)" % [key, m.albedo_color.get_luminance()])
	var img: Image = (load("res://assets/textures/obsidian_albedo.png") as Texture2D).get_image()
	img.decompress()
	img.resize(32, 32)
	var sum := 0.0
	for y in 32:
		for x in 32:
			sum += img.get_pixel(x, y).get_luminance()
	ok(sum / 1024.0 > 0.12, "the obsidian texture is a dark grey glass, not black (%.3f)" % (sum / 1024.0))
	done()

func test_gem_spirits() -> void:
	var g := GemSpirits.make([&"ember_orbital", "", &"nova_shard", &"sora_fragment", &"not_a_gem"], 0.9)
	eq(g.count(), 3, "one spirit per crystal (empty sockets and unknown ids skipped)")
	eq(g.families(), [&"ember", &"nova", &"sora"] as Array[StringName], "in socket order")
	var modes := {}
	for fam in DataCrystals.ORDER:
		ok(GemSpirits.LOOK.has(fam), "%s has a spirit" % fam)
		modes[int(GemSpirits.LOOK[fam][0])] = true
	eq(modes.size(), DataCrystals.ORDER.size(), "every family is drawn its own way")
	ok(GemSpirits.material(&"ember", 3) == GemSpirits.material(&"ember", 3), "materials are shared")
	ok(GemSpirits.material(&"ember", 3).shader == GemSpirits.material(&"luna", 0).shader, "one shader for every spirit")
	var two := GemSpirits.make([&"ember_orbital", &"ember_shard"])
	eq(two.count(), 2, "two crystals of a family make two spirits")
	host.add_child(g)
	await host.get_tree().process_frame
	await host.get_tree().process_frame
	var spread := []
	for c in g.get_children():
		spread.append((c as Node3D).position)
	ok(spread[0].distance_to(spread[1]) > 0.1 and spread[1].distance_to(spread[2]) > 0.1, "the spirits are spread round the blade")
	for p: Vector3 in spread:
		ok(p.y > 0.1 and p.y < 1.0, "each circles along the weapon (y %.2f)" % p.y)
	ok(g.get_child(0).get_node_or_null(^"Trail") != null, "hero spirits leave a trail")
	ok(GemSpirits.make([&"luna_orbital"], 0.9, false).get_child(0).get_node_or_null(^"Trail") == null, "companions' do not")
	g.queue_free()
	two.free()
	done()

func test_weapon_gems_on_visuals() -> void:
	var v := CharacterVisual.new()
	host.add_child(v)
	var holder := Node3D.new()
	v.add_child(holder)
	v._weapon_nodes[&"main"] = holder
	v.appearance = {"weapons": {}}
	v.set_weapon_gems(&"main", [&"ember_orbital", &"vipera_shard", &"airah_crystalline"])
	var s := holder.get_node_or_null(^"GemSpirits") as GemSpirits
	ok(s != null and s.count() == 3, "three crystals circle the held weapon")
	eq((v.appearance.gems as Dictionary).get(&"main", [[]])[0], ["ember_orbital", "vipera_shard", "airah_crystalline"],
		"other players are told which crystals (synced appearance)")
	v.set_weapon_gems(&"main", [&"sol_orbital"])
	await host.get_tree().process_frame
	eq(holder.find_children("GemSpirits", "", false, false).size(), 1, "re-set replaces the spirits")
	v.set_weapon_gems(&"main", [])
	await host.get_tree().process_frame
	ok(holder.get_node_or_null(^"GemSpirits") == null, "no crystals, no spirits")
	var src := FileAccess.get_file_as_string("res://src/actors/player/player.gd")
	ok(src.contains("visual.set_weapon_gems(pair[0], w.gems"), "the hero's held weapons show their crystals")
	ok(not src.contains("set_weapon_infusion"), "the old mixed-colour motes are gone")
	v.queue_free()
	done()
