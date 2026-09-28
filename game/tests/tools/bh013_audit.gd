extends SceneTree
## bh-013: data audit — dungeon enemy references resolve, attack/ability anims exist in each model, floors have plans.
##   godot --headless --path game -s res://tests/tools/bh013_audit.gd

var db: Node
var problems := []
var _clips := {}

func _initialize() -> void:
	db = root.get_node_or_null("DB")
	await process_frame
	db = root.get_node("DB")
	var defs := DataDungeons.defs()
	print("DUNGEONS %d" % defs.size())
	for id in DataDungeons.order():
		var d: Dictionary = defs[id]
		var n := DataDungeons.floor_count(id)
		if n < 2 or n > 5:
			problems.append("%s floors %d" % [id, n])
		for k in d.get("pools", {}):
			for eid in d.pools[k]:
				_need(eid, "%s pool %s" % [id, k])
		_need(d.get("boss", &""), "%s boss" % id)
		for key in ["miniboss", "usurper"]:
			var m = d.get(key, null)
			if m == null:
				m = DataDungeons.USURPERS.get(id, null) if key == "usurper" else null
			if m == null:
				problems.append("%s has no %s" % [id, key])
			else:
				_need(m.enemy, "%s %s" % [id, key])
		print("  %-12s tier %d floors %d levels %s gate %s" % [id, DataDungeons.tier(id), n, DataDungeons.level_range(id), d.get("surface", {}).get("map", "?")])
	var n_en := 0
	for eid in db.enemies:
		var e: EnemyDef = db.enemies[eid]
		n_en += 1
		for a in e.attacks:
			_anim(e, a.get("anim", &""), "attack %s" % a.id)
			if a.has("hold_anim"):
				_anim(e, a.hold_anim, "hold %s" % a.id)
			if a.has("summon"):
				_need(a.summon, "%s summon" % eid)
		for ab in e.abilities:
			if ab.has("anim"):
				_anim(e, ab.anim, "ability %s" % ab.id)
			if ab.has("summon"):
				_need(ab.summon, "%s ability summon" % eid)
	print("ENEMIES %d" % n_en)
	for p in problems:
		print("  PROBLEM ", p)
	print("AUDIT problems=%d" % problems.size())
	quit()

func _need(eid, where: String) -> void:
	if db.enemy(StringName(eid)) == null:
		problems.append("%s: missing enemy %s" % [where, eid])

func _anim(e: EnemyDef, n, where: String) -> void:
	if n == null or String(n) == "":
		return
	if not ResourceLoader.exists(e.model):
		problems.append("%s: model missing %s" % [e.id, e.model.get_file()])
		return
	if not _clips.has(e.model):
		var inst: Node = (load(e.model) as PackedScene).instantiate()
		var ap := _find(inst)
		_clips[e.model] = ap.get_animation_list() if ap else PackedStringArray()
		inst.free()
	var list: PackedStringArray = _clips[e.model]
	if list.is_empty():
		return   # static model animated by the game
	if not list.has(String(n)):
		problems.append("%s %s: clip %s not in %s" % [e.id, where, n, e.model.get_file()])

func _find(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var r := _find(c)
		if r:
			return r
	return null
