extends TestCase
## Enemy roster (bh-003): every definition is complete and consistent, every model exists and carries every clip its
## AI plays, the killing blow picks the right death, corpses and ground stains stay bounded, the blood setting is
## honoured, and the signature-trait rules hold (reassembly, devouring, stealth).

const MATERIALS := [&"flesh", &"ichor", &"bone", &"stone", &"aether", &"shadow"]
const STYLES := [&"fall", &"crumple", &"ash", &"collapse", &"implode", &"smoke"]
const TRAITS := [&"reassemble", &"coffin_shield", &"aim_line", &"ash_death", &"devour", &"stealth", &"pickpocket",
	&"core_overload", &"cowardly", &"enrage"]
const ROSTER := [&"hollow_soldier", &"bonewarden", &"grave_archer", &"boss_warden", &"ashen_cultist", &"ashen_acolyte",
	&"ghoul_brute", &"shade_stalker", &"bandit_cutthroat", &"bandit_marksman", &"dire_wolf", &"aether_sentinel",
	&"aether_wisp", &"goblin_skulker", &"orc_reaver", &"ogre_crusher"]

func _init() -> void:
	strict = true

func test_roster_definitions() -> void:
	ok(DB.enemies.size() >= ROSTER.size(), "the original roster remains alongside later additions")
	for id in ROSTER:
		var d: EnemyDef = DB.enemy(id)
		ok(d != null, "%s defined" % id)
		if d == null:
			continue
		ok(MATERIALS.has(d.hit_material), "%s hit material %s" % [id, d.hit_material])
		ok(STYLES.has(d.death_style), "%s death style %s" % [id, d.death_style])
		for t in d.traits:
			ok(TRAITS.has(t), "%s trait %s is implemented" % [id, t])
		ok(d.lore != "", "%s has lore" % id)
		ok(not d.attacks.is_empty(), "%s has attacks" % id)
		for a in d.attacks:
			ok(not DB.anim(a.anim).is_empty(), "%s: timing metadata for %s" % [id, a.anim])
			if a.kind in ["melee", "dash"]:
				ok(not DB.anim(a.anim).get("hits", []).is_empty(), "%s: %s has hit windows (damage only lands inside them)" % [id, a.anim])
	done()

## Every model exists and has the clips the game will ask it to play.
func test_models_have_every_clip() -> void:
	for id in ROSTER:
		var d: EnemyDef = DB.enemy(id)
		ok(ResourceLoader.exists(d.model), "%s model %s exists" % [id, d.model])
		if not ResourceLoader.exists(d.model):
			continue
		var inst: Node = (load(d.model) as PackedScene).instantiate()
		var ap := inst.find_children("*", "AnimationPlayer", true, false)
		if d.body_shape == &"floating":
			ok(inst.find_child("core", true, false) != null, "%s has a core node" % id)
			ok(inst.find_child("ring_1", true, false) != null, "%s has shard rings" % id)
			inst.free()
			continue
		ok(not ap.is_empty(), "%s has an AnimationPlayer" % id)
		if ap.is_empty():
			inst.free()
			continue
		var player: AnimationPlayer = ap[0]
		var need := [&"idle", &"walk", &"run", &"hit_light", &"death"]
		if d.body_shape == &"humanoid":
			need.append_array([&"death_back", &"death_fwd", &"death_crumple", &"hit_front", &"hit_back", &"stagger_small", &"knockback", &"alert"])
		for a in d.attacks:
			need.append(a.anim)
		for ab in d.abilities:
			if ab.has("anim"):
				need.append(ab.anim)
		if d.traits.has(&"devour"):
			need.append(&"devour")
		if d.traits.has(&"reassemble"):
			need.append(&"revive")
		for n in need:
			ok(player.has_animation(n), "%s model has clip %s" % [id, n])
		inst.free()
	done()

func _enemy(id: StringName) -> Enemy:
	var e := Enemy.new()
	e.setup(DB.enemy(id), 3)
	e.ensure_stats()
	e.hp = e.max_hp()
	return e

func test_death_clip_follows_the_killing_blow() -> void:
	var e := _enemy(&"bandit_cutthroat")
	var r := DamageResult.new()
	r.knockback = 12.0
	e._last_res = r
	eq(e._choose_death_clip(null), &"death_back", "heavy knockback throws the body back")
	r.knockback = 0.0
	r.is_crit = true
	eq(e._choose_death_clip(null), &"death_fwd", "a critical blow drops it forward")
	var s := _enemy(&"hollow_soldier")
	s._last_res = r
	eq(s._choose_death_clip(null), &"death_crumple", "skeletons fold down")
	eq(_enemy(&"aether_sentinel")._choose_death_clip(null), &"death_crumple", "constructs collapse")
	e.free()
	s.free()
	done()

func test_reassembly_rules() -> void:
	var s := _enemy(&"hollow_soldier")
	var fire := DamageResult.new()
	fire.components = {Elements.FIRE: 10.0}
	s._last_res = fire
	for i in 20:
		ok(not s._can_reassemble(), "fire ends a hollow soldier for good")
	var crush := DamageResult.new()
	crush.knockback = 15.0
	s._last_res = crush
	ok(not s._can_reassemble(), "a crushing blow ends it")
	var plain := DamageResult.new()
	plain.total = 5
	s._last_res = plain
	var yes := 0
	for i in 400:
		yes += 1 if s._can_reassemble() else 0
	ok(yes > 100 and yes < 220, "a plain death reassembles ~40%% of the time (%d/400)" % yes)
	s.free()
	done()

func test_corpses_and_stains_are_bounded() -> void:
	var holder := Node3D.new()
	host.add_child(holder)
	var old_world := FX.world
	FX.world = holder
	var was_blood := Settings.blood
	Settings.blood = true
	Enemy._corpses.clear()
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	var made := []
	for i in Enemy.MAX_CORPSES + 8:
		var e := Spawner.spawn_enemy(holder, DB.enemy(&"bandit_cutthroat"), 2, [], Vector3(i * 2.0, 0, 0), diff)
		made.append(e)
	await host.get_tree().process_frame
	for e in made:
		e.die(null)
	ok(Enemy._corpses.size() <= Enemy.MAX_CORPSES, "corpse count bounded (%d)" % Enemy._corpses.size())
	await host.get_tree().create_timer(1.6).timeout
	var alive_nodes := made.filter(func(e): return is_instance_valid(e) and not e.is_queued_for_deletion()).size()
	ok(alive_nodes <= Enemy.MAX_CORPSES, "oldest corpses dissolved and were freed (%d left)" % alive_nodes)
	for e in made:
		if is_instance_valid(e):
			ok(e.is_in_group(&"corpse") or e.has_meta(&"dissolving"), "every remaining body is a tracked corpse")
			break
	for i in FX.MAX_STAINS + 40:
		FX.stain(Vector3(i, 0, 0), Color(0.4, 0.02, 0.02), 1.0)
	ok(FX.stain_count() <= FX.MAX_STAINS, "ground stains bounded (%d)" % FX.stain_count())
	Settings.blood = false
	ok(FX.stain(Vector3.ZERO, Color.RED, 1.0) == null, "no stains with blood effects off")
	ok(not Gore.bleeds(&"flesh"), "flesh does not bleed with blood effects off")
	Settings.blood = true
	ok(Gore.bleeds(&"flesh") and Gore.bleeds(&"ichor") and not Gore.bleeds(&"bone"), "only flesh and ichor bleed")
	for m in MATERIALS:
		var n := Gore.hit(Vector3.ZERO, Vector3.FORWARD, m, Color(0.4, 0, 0), 0.8, true)
		ok(n != null and n.get_child_count() > 0, "%s hit burst has effects" % m)
		n.free()
	Settings.blood = was_blood
	FX.world = old_world
	Enemy._corpses.clear()
	holder.queue_free()
	done()

func test_devour_consumes_a_fresh_corpse() -> void:
	var holder := Node3D.new()
	host.add_child(holder)
	var old_world := FX.world
	FX.world = holder
	Enemy._corpses.clear()
	var diff: Dictionary = DataEnemies.DIFFICULTY[1]
	var body := Spawner.spawn_enemy(holder, DB.enemy(&"bandit_cutthroat"), 2, [], Vector3.ZERO, diff)
	await host.get_tree().process_frame
	body.die(null)
	ok(body.is_fresh_corpse(), "a new body is a fresh corpse")
	body.consume()
	ok(not body.is_fresh_corpse(), "consumed bodies cannot be eaten twice")
	ok(not body.is_in_group(&"corpse"), "consumed body leaves the corpse group")
	FX.world = old_world
	Enemy._corpses.clear()
	holder.queue_free()
	done()
