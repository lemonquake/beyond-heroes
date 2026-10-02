extends Node
## Map-design pass (2026-10-03) probes, run with autoloads:
##   godot --headless --path game res://tests/tools/map_design_probe.tscn -- --cmd=dungeons
## --cmd=dungeons   the registered dungeon definitions, themes and floor counts (JSON to stdout and --out)
## --cmd=build --maps=a,b   build each map (not added to the tree) and report its vignettes, skipped groups and census

var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	Game.save_slot = 97
	_run.call_deferred()

func _run() -> void:
	var res := {}
	match String(args.get("cmd", "dungeons")):
		"dungeons": res = _dungeons()
		"build": res = _build()
		"sizes": res = _sizes()
		"rooms": res = _rooms()
		"check": res = _check()
		"split": res = _split()
		"colinfo": res = _colinfo()
	var txt := JSON.stringify(res, " ")
	print("RESULT ", txt)
	if args.has("out"):
		var f := FileAccess.open(String(args.out), FileAccess.WRITE)
		f.store_string(txt)
		f.close()
	get_tree().quit()

func _dungeons() -> Dictionary:
	var out := {}
	var d := DataDungeons.defs()
	for id in d:
		var x: Dictionary = d[id]
		out[String(id)] = {"name": x.get("name", ""), "theme": String(x.theme), "floors": DataDungeons.floor_count(id),
			"special": DataDungeons.is_special(id), "surface": String(x.surface.map), "boss": String(x.get("boss", ""))}
	return {"count": d.size(), "dungeons": out}

func _hero() -> void:
	if Game.hero == null:
		Game.hero = Game.new_hero(&"knight", "Probe")

func _census(map: Node) -> Dictionary:
	var kinds := {}
	var mm := 0
	var mi := 0
	var tris := 0
	for n in map.find_children("*", "", true, false):
		if n is MeshInstance3D and (n as MeshInstance3D).mesh:
			mi += 1
			var nm := String(n.get_parent().name).get_slice("_", 0) if String(n.get_parent().name).begins_with("kd") else ""
			if String(n.get_parent().name).begins_with("kd_"):
				var k := String(n.get_parent().name).rsplit("_", true, 1)[0]
				kinds[k] = int(kinds.get(k, 0)) + 1
		elif n is MultiMeshInstance3D:
			mm += 1
			var b := String(n.name)
			if b.begins_with("Batch_kd_"):
				var k := b.trim_prefix("Batch_").rsplit("_", true, 2)[0].get_slice("~", 0)
				kinds[k] = int(kinds.get(k, 0)) + (n as MultiMeshInstance3D).multimesh.instance_count
	return {"mesh_instances": mi, "multimeshes": mm, "kd_kinds": kinds.size(), "kd": kinds}

func _build() -> Dictionary:
	_hero()
	var out := {}
	for id in String(args.get("maps", "sanctuary")).split(","):
		var t0 := Time.get_ticks_msec()
		var map: MapRoot = Game.build_map(StringName(id))
		var ms := Time.get_ticks_msec() - t0
		var v: Array = map.get_meta(&"vignettes", [])
		out[id] = {"build_ms": ms, "vignettes": v.map(func(x): return "%s@(%.1f,%.1f)" % [x.name, x.origin.x, x.origin.z]),
			"skipped": map.get_meta(&"vignettes_skipped", []), "dressing_skipped": map.get_meta(&"dressing_skipped", []),
			"census": _census(map)}
		map.free()
	return out

## Local bounds (x, y, z size and centre) of named kit pieces: --names=a,b
func _sizes() -> Dictionary:
	var out := {}
	for nm in String(args.get("names", "")).split(",", false):
		if not ResourceLoader.exists(MapBuilder.ENV_DIR % nm):
			out[nm] = "missing"
			continue
		var n: Node3D = MapBuilder.scene(nm).instantiate()
		var b := MapBuilder._local_box(nm, n)
		out[nm] = "size %.2f x %.2f x %.2f  min (%.2f, %.2f, %.2f)" % [b.size.x, b.size.y, b.size.z, b.position.x, b.position.y, b.position.z]
		n.free()
	return out

## Every dungeon's first, middle and last authored floor (or --floors=all): rooms, roles and motifs.
func _rooms() -> Dictionary:
	_hero()
	var out := {}
	var only: Array = String(args.get("dungeons", "")).split(",", false)
	for id in DataDungeons.defs():
		if not only.is_empty() and not only.has(String(id)):
			continue
		var nf := DataDungeons.floor_count(id)
		var floors: Array = range(1, nf + 1) if args.get("floors", "") == "all" else [1, maxi(1, (nf + 1) / 2), nf]
		for f in floors:
			var mid := DataDungeons.map_id(id, f)
			if out.has(String(mid)):
				continue
			var map: MapRoot = Game.build_map(mid)
			var rooms: Array = map.get_meta(&"rooms", [])
			var roles := {}
			var motifs := 0
			for r in rooms:
				roles[r.role] = int(roles.get(r.role, 0)) + 1
				motifs += (r.groups as Array).size()
			out[String(mid)] = {"theme": String(DataDungeons.get_def(id).theme), "rooms": rooms.size(), "roles": roles, "motifs": motifs,
				"groups": rooms.map(func(r): return "%s:%s" % [r.role, ",".join(r.groups.map(func(g): return g.motif))])}
			map.free()
	return out

## Compile scripts with the autoloads present (--scripts=res://a.gd,res://b.gd): real type errors surface, unlike
## --check-only, which stops at the autoload names. Errors print as SCRIPT ERROR lines; the result lists each load.
func _check() -> Dictionary:
	var out := {}
	for p in String(args.get("scripts", "")).split(",", false):
		var s = ResourceLoader.load(p, "", ResourceLoader.CACHE_MODE_IGNORE)
		out[p] = s != null and (s as GDScript).can_instantiate()
	return out

## Debug: the arena's split damage path against the one-machine pipeline (test_bh028_arena), with both step logs.
func _split() -> Dictionary:
	var T = load("res://tests/unit/test_bh028_arena.gd")
	var a: DerivedStats = T.geared(&"ranger", 50).compute_stats()
	var b: DerivedStats = T.geared(&"knight", 50).compute_stats()
	var out := {}
	for kind in [DamageRequest.Kind.ATTACK, DamageRequest.Kind.SPELL]:
		var req := DamageRequest.new()
		req.kind = kind
		req.attacker = a
		req.target = b
		req.can_crit = false
		req.evadable = false
		req.blockable = false
		if kind == DamageRequest.Kind.SPELL:
			req.use_weapon = false
			req.base_min = 400.0
			req.base_max = 400.0
			req.conversion = {Elements.FIRE: 0.7, Elements.LIGHTNING: 0.3}
		var r1 := RandomNumberGenerator.new()
		r1.seed = 7
		var whole := DamagePipeline.compute(req, r1)
		var r2 := RandomNumberGenerator.new()
		r2.seed = 7
		var d := Net.offense_pack(req, b.level, r2)
		var back := Net.defense_request(d)
		back.target = b
		var r3 := RandomNumberGenerator.new()
		r3.seed = 7
		var split := DamagePipeline.compute(back, r3)
		out[str(kind)] = {"whole": whole.total, "split": split.total, "whole_log": whole.steps, "split_log": split.steps, "pack": d}
	return out

func _colinfo() -> Dictionary:
	var out := {}
	for nm in String(args.get("names", "kd_crate")).split(","):
		var inst: Node = MapBuilder.scene(nm).instantiate()
		var arr := []
		for b in inst.find_children("*", "CollisionObject3D", true, false):
			for cs in b.find_children("*", "CollisionShape3D", true, false):
				arr.append("%s layer=%d mask=%d shape=%s" % [b.get_class(), b.collision_layer, b.collision_mask, (cs as CollisionShape3D).shape.get_class()])
		out[nm] = arr
		inst.free()
	return out
