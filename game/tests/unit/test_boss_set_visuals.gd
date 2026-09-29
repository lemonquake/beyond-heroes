extends TestCase
const Art = preload("res://src/actors/boss_set_visuals.gd")

func _init() -> void:
	strict = true

func test_authored_geometry_is_bounded_indexed_and_cached() -> void:
	for id in Art.THEMES:
		for slot in Art.SLOTS:
			if slot == "main_weapon": continue
			var piece := Art.create_piece(id,slot)
			ok(piece.get_child_count() > 0 and piece.get_child_count() <= 4, "%s/%s has <=4 material draws" % [id,slot])
			for mesh in piece.get_children():
				var aabb: AABB = mesh.mesh.get_aabb()
				ok(aabb.size.is_finite() and aabb.size.length() < 4.0, "%s/%s geometry stays finite and character-sized" % [id,slot])
				var arrays: Array = mesh.mesh.surface_get_arrays(0)
				ok(arrays[Mesh.ARRAY_INDEX].size() > 0, "combined surfaces preserve indexed ornament triangles")
			var duplicate := Art.create_piece(id,slot)
			eq(piece.get_child(0).mesh,duplicate.get_child(0).mesh,"repeated outfits share cached mesh resources")
			piece.free()
			duplicate.free()
	done()

func test_bone_attachments_follow_equipment_and_teardown() -> void:
	for cls_id in [&"knight",&"mage",&"ranger",&"shadowblade"]:
		var v := CharacterVisual.new()
		host.add_child(v)
		var cls := DB.class_def(cls_id)
		v.setup(cls.model_path,1.0,cls.tint,cls_id)
		var eqp := Equipment.new()
		for slot in Art.SLOTS:
			if slot != "main_weapon": eqp.slots[StringName(slot)] = DB.make_item(StringName("boss_dragonforge_"+slot),BH.Rarity.MASTER,30,1)
		v.dress_equipment(eqp)
		eq(v._set_nodes.size(),11,"all non-weapon slots have independent worn geometry on "+String(cls_id))
		var first_id: int = v._set_nodes[0].get_instance_id()
		v.dress_equipment(eqp)
		eq(v._set_nodes[0].get_instance_id(),first_id,"unchanged equipment does not rebuild bones")
		for node in v._set_nodes:
			ok(node is BoneAttachment3D and v.skeleton.find_bone(node.bone_name)>=0,"gear follows a real skeleton bone")
		eqp.slots[&"helm"] = null
		v.dress_equipment(eqp)
		eq(v._set_nodes.size(),10,"removing helmet preserves other pieces")
		for slot in eqp.slots: eqp.slots[slot] = null
		v.dress_equipment(eqp)
		eq(v._set_nodes.size(),0,"removing set clears every worn attachment")
		ok(v.appearance.get("set_gear",{}).is_empty(),"network appearance clears removed gear")
		v.free()
	done()
