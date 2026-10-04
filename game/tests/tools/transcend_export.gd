extends Node
## Class Transcendence catalogues for review, written from the live registry and item data (never by hand):
##   output/class-transcendence/class_catalogue.json   all sixteen identities: lineage, themes, signature traits, the
##                                                     36 skills (cost, cooldown, rank 1 / 5 / 25 / 25+5 numbers, text)
##                                                     and the 36 talents (rank 1 / 25 text, mods, flags, caps), gear
##   output/class-transcendence/gear_requirements.json every equipment base: requirement kind / ids / text, levels,
##                                                     story wearers, Tempo permission and sources (ClassRequirements)
##   godot --headless --path game res://tests/tools/transcend_export.tscn

func _ready() -> void:
	await get_tree().process_frame
	var dir := ProjectSettings.globalize_path("res://").path_join("../output/class-transcendence")
	DirAccess.make_dir_recursive_absolute(dir)
	_save(dir.path_join("class_catalogue.json"), _catalogue())
	var gear := ClassRequirements.manifest()
	var counts := {}
	for g in gear:
		counts[g.kind] = int(counts.get(g.kind, 0)) + 1
	_save(dir.path_join("gear_requirements.json"), {"bases": gear.size(), "by_kind": counts,
		"new_pieces": gear.filter(func(g): return String(g.id).begins_with("tc_")).size(), "items": gear})
	print("EXPORT done: %d bases %s" % [gear.size(), counts])
	get_tree().quit()

func _save(path: String, data: Variant) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(data, "  ", false))
	print("WROTE ", path)

func _catalogue() -> Dictionary:
	var ids: Array = DataTranscendence.FAMILIES.keys()
	for fam in DataTranscendence.FAMILIES:
		for c in DataTranscendence.family_members(fam).slice(1):
			ids.append(c)
	var out := []
	for id in ids:
		var d := DataTranscendence.info(id)
		var th := ClassTranscendence.class_theme(id)
		var e := {"id": String(id), "name": DataTranscendence.name_of(id), "family": String(DataTranscendence.family_of(id)),
			"stage": DataTranscendence.stage_of(id), "parent": String(DataTranscendence.parent_of(id)),
			"lineage": DataTranscendence.ancestry(id).map(func(x): return String(x)),
			"level": 1 if DataTranscendence.stage_of(id) == 0 else DataTranscendence.level_for_stage(DataTranscendence.stage_of(id)),
			"primary": "#" + (th.primary as Color).to_html(false), "accent": "#" + (th.accent as Color).to_html(false),
			"label_color": "#" + ClassTranscendence.label_color(id).to_html(false)}
		if DataTranscendence.is_advanced(id):
			e["role"] = d.role
			e["desc"] = d.desc
			e["limit"] = d.limit
			var sg: Dictionary = DataTranscendence.SIGNATURES[id]
			e["signature"] = {"name": sg.name, "text": DataTranscendence.signature_text(id), "values": sg.nums}
			e["armor_look"] = d.get("armor_look", "")
			e["skills"] = (d.skills as Array).map(func(sid): return _skill(sid))
			e["talents"] = (d.talents as Array).map(func(tid): return _talent(tid))
			e["gear"] = (d.gear as Array).map(func(gid): return _gear(gid))
		out.append(e)
	return {"identities": out, "talent_tail": DataTranscendence.TAIL, "flag_caps": DataTranscendence.CAPS}

func _skill(sid: StringName) -> Dictionary:
	var s := DB.skill(sid)
	var at := {}
	for r in [1, 5, 25, 30]:
		var p := s.resolve(r)
		var nums := {}
		for k in p:
			if p[k] is float or p[k] is int:
				nums[k] = snappedf(float(p[k]), 0.01)
		at[str(r)] = {"mana": snappedf(s.mana_at(mini(r, 25)), 0.1), "params": nums, "text": TranscendWindow._fill(s.description, p)}
	return {"id": String(sid), "name": s.display_name, "behavior": String(s.behavior), "kind": "spell" if s.kind == DamageRequest.Kind.SPELL else "attack",
		"cooldown": s.cooldown, "requires": String(s.requires), "conversion": s.conversion, "element": s.element,
		"per_rank": s.per_rank, "anim": String(s.anim), "sound_cast": String(s.sound_cast), "sound_hit": String(s.sound_hit), "vfx": String(s.vfx),
		"ranks": at, "note": "rank 30 = level 25 plus +5 item skill levels"}

func _talent(tid: StringName) -> Dictionary:
	var t: Dictionary = DataTranscendence.TALENTS[tid]
	var mods := []
	for m in t.get("mods", []):
		mods.append({"stat": String(m[0]), "op": ["flat", "inc", "more"][int(m[1])] if int(m[1]) < 3 else str(m[1]), "rank1": m[2]})
	var flags := {}
	for f in t.get("flags", {}):
		flags[String(f)] = {"rank1": t.flags[f], "cap": DataTranscendence.CAPS.get(f, null)}
	return {"id": String(tid), "name": t.name, "kind": t.kind, "max_rank": 1 if t.kind == "major" else 25,
		"rank1": DataTranscendence.talent_text(tid, 1), "rank25": DataTranscendence.talent_text(tid, 25), "mods": mods, "flags": flags}

func _gear(gid: StringName) -> Dictionary:
	var b := DB.item_base(gid)
	if b == null:
		return {"id": String(gid), "missing": true}
	return {"id": String(gid), "name": b.display_name, "category": String(b.category), "weapon_type": String(b.weapon_type),
		"requirement": ClassRequirements.of(b), "text": ClassRequirements.text(b), "level": b.level_req, "drop_level": b.drop_level,
		"sources": DataTranscendenceGear.sources(gid)}
