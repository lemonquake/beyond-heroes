extends TestCase
## bh-037 smoothness pass (Agdao stutter report):
##   - a character is drawn between its body's last two physics steps (60 Hz movement judders on a faster screen), and a
##     jump of more than 2 m snaps instead of sliding; the smoothing offset never leaks into the flinch rest pose
##   - the autosave writes on a worker thread (a 790 KB hero froze the game ~70 ms), a save made meanwhile supersedes it
##   - the follow camera tracks the drawn hero, not the stepping body
##   - spawns mid-fight: one per spawn slot across every caller; every kind a monster can bring in is known (and warmed
##     at map load); see-through copies (mirror images, stealth, corpse decay) find their shader already built; an
##     attack without a "kind" no longer errors; a level-up no longer re-makes the held weapons

const SLOT := 98

var _holder: Node3D

func _init() -> void:
	strict = true

func _rig() -> Array:
	_holder = Node3D.new()
	host.add_child(_holder)
	var body := CharacterBody3D.new()
	_holder.add_child(body)
	var v := CharacterVisual.new()
	body.add_child(v)
	return [body, v]

func test_drawn_between_physics_steps() -> void:
	var r := _rig()
	var body: CharacterBody3D = r[0]
	var v: CharacterVisual = r[1]
	await host.get_tree().physics_frame
	eq(v.smoothed_body_transform().origin, body.global_position, "a body at rest is drawn where it is")
	await host.get_tree().physics_frame
	v.smoothed_body_transform()                       # the step before
	await host.get_tree().physics_frame
	body.global_position = Vector3(0.1, 0.0, 0.0)     # one step of walking (6 m/s)
	var x := v.smoothed_body_transform().origin.x
	ok(x >= 0.0 and x <= 0.1, "drawn between the last two steps (x = %.3f)" % x)
	body.global_position = Vector3(10.0, 0.0, 0.0)    # a teleport / blink
	eq(v.smoothed_body_transform().origin, body.global_position, "a jump of more than 2 m snaps")
	_holder.free()
	done()

func test_smoothing_offset_stays_out_of_the_rest_pose() -> void:
	var r := _rig()
	var v: CharacterVisual = r[1]
	v._sm_applied = Transform3D(Basis.IDENTITY, Vector3(0.05, 0.0, 0.0))
	v.transform = v._sm_applied
	v.flinch(Vector3.FORWARD, 0.5)
	eq(v._rest, Transform3D.IDENTITY, "the flinch layer rests on the unsmoothed transform")
	_holder.free()
	done()

func test_camera_follows_the_drawn_hero() -> void:
	var c := PlayerCamera.new()
	ok(c.has_method(&"_target_pos"), "the camera reads the hero's drawn position")
	c.free()
	done()

func test_background_save() -> void:
	SaveSystem.delete_slot(SLOT)
	var h := Game.new_hero(&"knight", "Backdrop")
	h.inventory.gold = 777
	var got := []
	var cb := func(okk: bool) -> void: got.append(okk)
	SaveSystem.background_saved.connect(cb)
	ok(SaveSystem.save_hero(h, SLOT, true), "a background save starts")
	ok(not FileAccess.file_exists(SaveSystem.slot_path(SLOT)), "nothing is written on the calling frame")
	for i in 120:
		await host.get_tree().process_frame
		if not got.is_empty():
			break
	eq(got, [true], "the worker reports a checked write")
	eq(int(SaveSystem.read_slot(SLOT).hero.gold), 777, "the file holds the hero")
	# a save made while a background save waits for its snapshot frame wins: the staged one never writes over it
	h.inventory.gold = 1
	SaveSystem.save_hero(h, SLOT, true)
	h.inventory.gold = 2
	ok(SaveSystem.save_hero(h, SLOT), "a direct save meanwhile")
	for i in 5:
		await host.get_tree().process_frame
	SaveSystem.finish_pending()
	eq(int(SaveSystem.read_slot(SLOT).hero.gold), 2, "the newer direct save is the one on disk")
	SaveSystem.background_saved.disconnect(cb)
	SaveSystem.delete_slot(SLOT)
	done()

func test_companions_coarsen_only_in_efficiency_mode() -> void:
	var v := CharacterVisual.new()
	ok(not v.ally_lod and not v.crowd_lod, "a plain visual (the hero's) never joins the crowd ranking")
	v.free()
	var src := FileAccess.get_file_as_string("res://src/autoload/perf.gd")
	ok(src.contains("v.crowd_lod or (lite and v.ally_lod)"), "companions are ranked with the crowd only in efficiency mode")
	done()

func test_every_called_kind_is_known() -> void:
	var kinds := func(id: StringName) -> Array: return Enemy.TraitsX.minion_kinds(DB.enemy(id))
	ok(kinds.call(&"mirage_weaver").has(&"mirror_image"), "a weaver's mirror images")
	ok(kinds.call(&"riftcaller").has(&"void_rift") and kinds.call(&"riftcaller").has(&"shade_stalker"), "a rift and the shades it releases")
	ok(kinds.call(&"broodhost").has(&"leechling"), "a broodhost's parasites")
	ok(kinds.call(&"hive_nest").has(&"hive_drone"), "a nest's drones")
	ok(kinds.call(&"gravecaller").has(&"bone_thrall"), "a gravecaller's thralls")
	var missing := []
	for d: EnemyDef in DB.enemies.values():
		for k in Enemy.TraitsX.minion_kinds(d):
			if DB.enemy(k) == null:
				missing.append("%s -> %s" % [d.id, k])
	eq(missing, [], "every kind a monster can call exists")
	done()

func test_see_through_shader_is_built_ahead() -> void:
	var r := _rig()
	var v: CharacterVisual = r[1]
	var mat := StandardMaterial3D.new()
	var mi := MeshInstance3D.new()
	mi.mesh = BoxMesh.new()
	mi.set_surface_override_material(0, mat)
	v.add_child(mi)
	v.adopt_mesh(mi)
	v.warm_see_through()
	ok(MaterialLibrary._faded.has(mat), "the see-through copy is kept for the session")
	v.set_opacity(0.5)
	var local := mi.get_surface_override_material(0) as BaseMaterial3D
	ok(local != mat and local.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_HASH and is_equal_approx(local.albedo_color.a, 0.5),
		"set_opacity still gives the body its own dithered copy")
	_holder.free()
	done()

func test_attack_without_a_kind() -> void:
	var src := FileAccess.get_file_as_string("res://src/actors/enemy/enemy.gd")
	ok(src.contains('String(a.get("kind", "")) in ["melee", "dash", "charge"]'), "an attack request reads its kind safely")
	ok(src.contains('_fire({"id": &"aether_bolt", "kind": "projectile"'), "an elite's aether bolts say what they are")
	done()

func test_spawns_take_turns() -> void:
	Enemy._spawn_slot_ms = 0
	eq(Enemy.spawn_wait(), 0.0, "the first called-in monster comes at once")
	var w2 := Enemy.spawn_wait()
	ok(w2 > 0.0 and w2 <= Enemy.SUMMON_STAGGER + 0.001, "the next waits for its own slot (%.3f s)" % w2)
	for i in 30:
		Enemy.spawn_wait()
	ok(Enemy.spawn_wait() <= Enemy.SPAWN_WAIT_MAX + 0.001, "none waits longer than SPAWN_WAIT_MAX")
	Enemy._spawn_slot_ms = 0
	done()

func test_level_up_keeps_the_weapons() -> void:
	# a level-up or a point spent reports a hero change; the held weapons were torn down and re-made (~40 ms mid-fight)
	var src := FileAccess.get_file_as_string("res://src/actors/player/player.gd")
	ok(src.contains("if wkey == _weapon_key and visual.has_weapon(&\"main\")"), "weapons are re-made only when what is held changes")
	ok(src.contains("str(item.gems), item.sockets, item.rarity"), "crystals and rarity are part of what is held")
	done()
