extends TestCase
## The extra character draw pass exists only during a flash/rim or the bounded loading warmup.

func _init() -> void:
	strict = true

func _visual(hero := false) -> CharacterVisual:
	var v := CharacterVisual.new()
	host.add_child(v)
	if hero:
		v.setup_hero(&"knight", {"body": "custom"})
	else:
		v.setup("")   # procedural fallback makes basic overlay lifetime checks independent of imported models
	return v

func _meshes_have(v: CharacterVisual, expected: Material, description: String) -> void:
	var checked := 0
	for mesh in v._meshes:
		if is_instance_valid(mesh):
			checked += 1
			eq(mesh.material_overlay, expected, description)
	ok(checked > 0, "the fixture has meshes")

func _advance_flash(v: CharacterVisual, seconds: float) -> void:
	v._flash_tw.pause()
	v._flash_tw.custom_step(seconds)

func test_idle_flash_and_rim_overlap() -> void:
	var v := _visual()
	_meshes_have(v, null, "idle body has no overlay pass")
	v.flash(Color.RED, 0.8, 0.2)
	_meshes_have(v, v._overlay, "flash attaches its pass immediately")
	near(float(v._overlay.get_shader_parameter("flash")), 0.8, 0.001, "flash intensity is preserved")
	v.set_rim(Color.BLUE, 0.6)
	_advance_flash(v, 0.3)
	near(float(v._overlay.get_shader_parameter("flash")), 0.0, 0.001, "flash reaches zero")
	_meshes_have(v, v._overlay, "ending a flash keeps an active rim")
	v.set_rim(Color.BLACK, 0.0)
	_meshes_have(v, null, "last visible contribution ending removes the pass")
	v.flash(Color.GREEN, 0.7, 0.2)
	v.set_rim(Color.BLUE, 0.5)
	v.set_rim(Color.BLACK, 0.0)
	_meshes_have(v, v._overlay, "ending a rim keeps an active flash")
	_advance_flash(v, 0.3)
	_meshes_have(v, null, "flash completion removes the pass when no rim remains")
	v.free()
	done()

func test_interrupted_flash_does_not_end_replacement() -> void:
	var v := _visual()
	v.flash(Color.RED, 1.0, 0.2)
	var old := v._flash_tw
	_advance_flash(v, 0.05)
	v.flash(Color.BLUE, 0.5, 0.4)
	ok(not old.is_valid(), "a replacement flash kills its previous tween")
	_advance_flash(v, 0.25)
	_meshes_have(v, v._overlay, "the replacement lasts beyond the original end time")
	eq(v._overlay.get_shader_parameter("flash_color"), Color.BLUE, "replacement flash uses its own color")
	_advance_flash(v, 0.3)
	_meshes_have(v, null, "replacement completion releases the pass")
	v.free()
	done()

func test_mesh_adoption_and_release_follow_state() -> void:
	var v := _visual()
	var hair := MeshInstance3D.new()
	hair.mesh = BoxMesh.new()
	v.add_child(hair)
	v.adopt_mesh(hair)
	eq(hair.material_overlay, null, "idle adopted mesh does not add a pass")
	v.set_rim(Color.BLUE, 0.5)
	eq(hair.material_overlay, v._overlay, "an adopted mesh receives the active rim")
	var sleeve := MeshInstance3D.new()
	sleeve.mesh = BoxMesh.new()
	v.add_child(sleeve)
	v.adopt_mesh(sleeve)
	eq(sleeve.material_overlay, v._overlay, "a mesh adopted during a rim gets the active pass")
	v.release_mesh(sleeve)
	eq(sleeve.material_overlay, null, "released mesh no longer owns the character overlay")
	ok(not v._meshes.has(sleeve), "released mesh leaves the registry")
	hair.free()   # a freed tracked mesh does not break later state transitions
	v.set_rim(Color.BLACK, 0.0)
	v.free()
	done()

func test_equipment_and_weapon_changes_keep_overlay_state() -> void:
	var v := _visual(true)
	var hero := Game.new_hero(&"knight", "Overlay check")
	v.dress_equipment(hero.equipment)
	_meshes_have(v, null, "idle worn equipment has no extra pass")
	v.set_rim(Color.BLUE, 0.6)
	v.set_look({"body": "custom", "hair": "long", "show_helm": false})
	v.dress_equipment(hero.equipment)
	_meshes_have(v, v._overlay, "new hair and worn equipment share the active rim")
	v.attach_weapon(&"main", DB.item_base(&"iron_longsword").model_path())
	var weapon_meshes: Array[MeshInstance3D] = []
	v._collect_into(v._weapon_nodes[&"main"], weapon_meshes)
	ok(not weapon_meshes.is_empty(), "a real weapon is attached")
	for mesh in weapon_meshes:
		eq(mesh.material_overlay, v._overlay, "equipped weapon receives the active rim")
	v.detach_weapon(&"main")
	for mesh in weapon_meshes:
		ok(not v._meshes.has(mesh), "unequipped weapon leaves the overlay registry")
		eq(mesh.material_overlay, null, "unequipped weapon releases the pass")
	v.dress_equipment(Equipment.new())
	v.set_rim(Color.BLACK, 0.0)
	_meshes_have(v, null, "undressing and ending a rim leave no extra pass")
	v.free()
	done()

func test_model_switch_keeps_live_flash_and_status_material() -> void:
	var v := _visual(true)
	var status := Node3D.new()
	v.add_child(status)
	v._status_nodes[&"wet"] = status
	v._refresh_rim()
	v.flash(Color.RED, 0.8, 0.4)
	var material := v._overlay
	_advance_flash(v, 0.1)
	var flash_before := v._flash_amount
	v.set_look({"body": "class"})
	eq(v._overlay, material, "model replacement keeps the material and compiled shader resource alive")
	near(v._flash_amount, flash_before, 0.001, "replacement keeps current flash intensity")
	eq(v._overlay.get_shader_parameter("flash_color"), Color.RED, "replacement keeps flash color")
	_meshes_have(v, material, "replacement body receives the flash and status rim")
	v.set_look({"body": "custom"})
	_advance_flash(v, 0.5)
	_meshes_have(v, material, "status rim remains after the flash ends on the replaced body")
	v._status_nodes.erase(&"wet")
	v._refresh_rim()
	_meshes_have(v, null, "removing the status releases the replacement body's pass")
	v.free()
	done()

func test_loading_warmup_is_bounded_and_preserves_visible_state() -> void:
	var v := _visual()
	v.warm_overlay(true)
	v.warm_overlay(true)
	_meshes_have(v, v._overlay, "loading warmup attaches the black pass")
	near(v._flash_amount, 0.0, 0.001, "warmup does not create a visible flash")
	near(v._rim_amount, 0.0, 0.001, "warmup does not create a visible rim")
	v.warm_overlay(false)
	_meshes_have(v, v._overlay, "one overlapping warmup remains")
	v.set_rim(Color.BLUE, 0.5)
	v.warm_overlay(false)
	_meshes_have(v, v._overlay, "ending loading warmup keeps a visible rim")
	v.set_rim(Color.BLACK, 0.0)
	_meshes_have(v, null, "warmup returns to no pass after visible effects end")
	v.warm_overlay(false)
	eq(v._overlay_warmups, 0, "extra cleanup cannot make the warmup counter negative")
	v.flash(Color.RED, 1.0, 1.0)
	v.free()
	await host.get_tree().process_frame
	ok(true, "freeing a visual during its bound tween completes without an orphan callback")
	done()
