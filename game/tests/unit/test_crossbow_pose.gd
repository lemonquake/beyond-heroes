extends TestCase
## Validate the visible muzzle throughout the authored clip, not only at keyframes.
func test_two_hand_contact_and_forward_muzzle_throughout_crossbow_clips() -> void:
	var visual := CharacterVisual.new()
	host.add_child(visual)
	visual.setup("res://assets/characters/ranger.glb", 1.0, Color.WHITE, &"ranger")
	visual.tree.active = false
	var skeleton := visual.skeleton
	var main := skeleton.find_bone("weapon.R")
	var support := skeleton.find_bone("weapon.L")
	for name in [&"idle_crossbow", &"crossbow_aim", &"crossbow_fire", &"crossbow_heavy"]:
		var clip := visual.anim_player.get_animation(name)
		visual.anim_player.play(name)
		for step in 101:
			visual.anim_player.seek(clip.length * float(step) / 100.0, true)
			visual.anim_player.advance(0)
			skeleton.force_update_all_bone_transforms()
			var right := skeleton.get_bone_global_pose(main)
			var left := skeleton.get_bone_global_pose(support)
			var axis := right.basis.y.normalized()
			var separation := left.origin - right.origin
			var lateral := separation - axis * separation.dot(axis)
			ok(axis.z > 0.975 and absf(axis.x) < 0.04, "%s stays aimed forward at sample %d" % [name, step])
			ok(lateral.length() < 0.02, "%s support hand stays on stock at sample %d" % [name, step])
			if name == &"crossbow_aim":
				ok(absf(axis.y) < 0.02, "aimed muzzle is level")
	visual.free()
	done()
