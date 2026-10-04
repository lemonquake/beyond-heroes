extends TestCase

var world: Node3D
var player: Player
var old_fx: Node3D

func _init() -> void:
	strict = true

func setup(cls := &"shadowblade") -> void:
	old_fx = FX.world
	world = Node3D.new()
	host.add_child(world)
	FX.world = world
	player = Player.new()
	world.add_child(player)
	player.bind(Game.new_hero(cls, "Class test"))
	player.set_physics_process(false)
	player.stats.set_stat(&"max_hp", 10000.0)
	player.stats.set_stat(&"max_mana", 1000.0)
	player.hp = 5000.0
	player.mana = 0.0
	player._stats_dirty = false

func cleanup() -> void:
	world.free()
	FX.world = old_fx if is_instance_valid(old_fx) else null

func target(at := Vector3(0, 0, 2)) -> Actor:
	var a := Actor.new()
	a.stats = blank_stats()
	a.stats.set_stat(&"max_mana", 100.0)
	a.stats.set_stat(&"max_hp", 100000.0)
	a.hp = 100000.0
	a.mana = 100.0
	a.collision_layer = BH.LAYER_ENEMY
	a.collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.8
	capsule.radius = 0.4
	shape.shape = capsule
	shape.position.y = 0.9
	a.add_child(shape)
	world.add_child(a)
	a.position = at
	a._stats_dirty = false
	return a

func attack(serial: int) -> DamageRequest:
	var req := DamageRequest.new()
	req.attacker = player.stats
	req.use_weapon = false
	req.base_min = 100.0
	req.base_max = 100.0
	req.evadable = false
	req.can_crit = false
	req.tags = {&"weapon": true, &"attack_id": serial}
	return req

func frames(n: int) -> void:
	for i in n:
		await host.get_tree().physics_frame

func proc_seed(chance: float) -> int:
	for i in 1000:
		if rng(i).randf() < chance:
			return i
	return 0

func test_eight_slots_and_save_roundtrip() -> void:
	eq(SaveSystem.SLOTS, 8, "eight hero slots")
	var paths := {}
	for slot in SaveSystem.SLOTS:
		paths[SaveSystem.slot_path(slot)] = true
	eq(paths.size(), 8, "each slot has an independent path")
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := Game.new_hero(cls, "Saved")
		for n in DataClassRework.nodes(cls):
			h.skill_tree.ranks[n.id] = 25
		var back := HeroData.from_dict(h.to_dict())
		for n in DataClassRework.nodes(cls):
			eq(back.skill_tree.rank(n.id), 25, "%s survives saving" % n.id)
	done()

func test_load_menu_lists_all_eight_slots_in_scroll_container() -> void:
	var menu := MainMenu.new()
	menu._load_panel = menu._build_load()
	menu._credits = PanelContainer.new()
	host.add_child(menu._load_panel)
	menu._show_load()
	var scroll: ScrollContainer = menu._load_panel.get_child(0).get_child(2)
	eq(scroll.get_child(0).get_child_count(), 8, "load menu contains all eight cards")
	ok(scroll.size_flags_vertical & Control.SIZE_EXPAND_FILL != 0, "slot list fills remaining panel space")
	menu._load_panel.free()
	menu._credits.free()
	menu.free()
	done()

func test_rank_endpoints() -> void:
	for row in [[&"shadowblade", &"paralyzing_attack", 0.30, 0.85], [&"shadowblade", &"bloodcurse", 0.20, 0.70], [&"ranger", &"knee_shot", 0.10, 0.40], [&"ranger", &"split_shot", 0.50, 0.75], [&"mage", &"arcane_arts", 0.10, 0.50]]:
		var h := Game.new_hero(row[0], "Ranks")
		for rank in [1, 25]:
			h.skill_tree.ranks[row[1]] = rank
			h._skills_changed()
			near(h.compute_stats().flag(row[1]), float(row[2] if rank == 1 else row[3]), 0.0001, "%s rank %d" % [row[1], rank])
	eq(ClassPassives.split_count(0.50), 3, "three arrows at level one")
	eq(ClassPassives.split_count(0.75), 8, "eight arrows at level 25")
	near(DB.skill(&"spike_tentacle").resolve(1).stun_duration, 0.2, 0.0001, "base tentacle stun")
	near(DB.skill(&"spike_tentacle").resolve(25).stun_duration, 1.6, 0.0001, "maximum tentacle stun")
	var meteor := DB.skill(&"meteor")
	ok(meteor.cooldown >= 20.0 and meteor.mana_cost >= 40.0 and meteor.params.radius >= 7.0, "Meteor Strike has a large area, cost and cooldown")
	done()

func test_bloodsucker_counts_attacks_and_bloodcurse_reduces_healing() -> void:
	setup()
	player.stats.flags = {&"bloodsucker": 0.35, &"bloodcurse": 0.70, &"paralyzing_attack": 0.85}
	var a := target()
	var first := a.receive_hit(attack(1), player)
	near(player.hp, 5000.0, 0.001, "first attack does not steal life")
	a.receive_hit(attack(1), player)
	near(player.hp, 5000.0, 0.001, "same swing does not count twice")
	var second := a.receive_hit(attack(2), player)
	near(player.hp, 5000.0 + second.total * 0.35, 0.01, "second attack heals for dealt damage")
	near(a.status.heal_taken_mult(), 0.30, 0.001, "all restoration reduced by 70 percent")
	var before := a.hp
	a.heal(100.0, false)
	near(a.hp - before, 30.0, 0.01, "direct healing respects Bloodcurse")
	near(a.status.remaining(&"paralyzed"), 0.1, 0.001, "brief paralysis duration")
	near(a.status.magnitude(&"paralyzed"), 0.85, 0.001, "85 percent slow")
	a.status.tick(0.11)
	ok(not a.status.has(&"paralyzed"), "brief slow expires")
	ok(first.total > 0, "first attack lands")
	cleanup()
	done()

func test_double_attack_cooldown_and_no_recursion() -> void:
	setup()
	player.stats.flags = {&"double_attack": 0.65, &"bloodsucker": 0.35}
	var a := target()
	a.receive_hit(attack(1), player)
	var hp0 := a.hp
	near(player.class_passives.double_cd, 1.2, 0.001, "repeat starts cooldown immediately")
	await frames(15)
	ok(a.hp < hp0, "delayed second hit lands")
	eq(player.class_passives.landed_attacks, 1, "repeat does not count for Bloodsucker")
	var repeat_hp := a.hp
	await frames(15)
	near(a.hp, repeat_hp, 0.001, "repeat does not recurse")
	a.receive_hit(attack(2), player)
	var hp1 := a.hp
	await frames(15)
	near(a.hp, hp1, 0.001, "no repeat during cooldown")
	player.class_passives.tick(1.2)
	a.receive_hit(attack(3), player)
	var hp2 := a.hp
	await frames(15)
	ok(a.hp < hp2, "repeat is ready after cooldown")
	cleanup()
	done()

func test_knight_regen_return_and_proc_guard() -> void:
	setup(&"knight")
	player.stats.flags = {&"debuff_regen": 0.005, &"damage_return": 0.4}
	player.status.apply(&"weakened", 5.0)
	player.status.apply(&"bloodcurse", 4.0, 0.70)
	player.status.apply(&"haste", 5.0)
	near(player.class_passives.debuff_regen(), 100.0, 0.001, "two debuffs add one percent max HP per second")
	var a := target()
	var result := DamageResult.new()
	result.total = 100
	player.class_passives.return_damage(a, attack(1), result)
	near(a.hp, 99960.0, 0.01, "returns 40 percent hit damage")
	var proc := attack(2)
	proc.tags[&"proc"] = true
	player.class_passives.return_damage(a, proc, result)
	near(a.hp, 99960.0, 0.01, "cannot return proc damage")
	cleanup()
	done()

func test_arcane_refund_and_siphon_conserve_mana() -> void:
	setup(&"mage")
	player.stats.flags = {&"arcane_arts": 0.9}
	player.rng.seed = proc_seed(0.30)
	player.class_passives.refund(DB.skill(&"firebolt"), 40.0)
	near(player.mana, 20.0, 0.001, "refund capped at half actual cost")
	var a := target()
	a.mana = 5.0
	await frames(2)
	ClassSpells.cast(player.runner, DB.skill(&"mana_siphon"), DB.skill(&"mana_siphon").resolve(25), a.position)
	near(player.mana, 25.0, 0.001, "recover only actual enemy mana")
	near(a.mana, 0.0, 0.001, "enemy pool drained")
	ClassSpells.cast(player.runner, DB.skill(&"mana_siphon"), DB.skill(&"mana_siphon").resolve(25), a.position)
	near(player.mana, 25.0, 0.001, "empty pool cannot generate mana")
	cleanup()
	done()

func test_counterattack_cooldown() -> void:
	setup(&"knight")
	player.stats.flags = {&"retaliation": 1.0}
	var a := target()
	var blocked := DamageResult.new()
	blocked.blocked = true
	blocked.total = 10
	player._on_blocked(blocked, a)
	var after_first := a.hp
	ok(after_first < a.max_hp(), "block triggers a counterattack")
	player._on_blocked(blocked, a)
	near(a.hp, after_first, 0.001, "another block cannot bypass cooldown")
	player._tick_timers(2.0)
	player._on_blocked(blocked, a)
	ok(a.hp < after_first, "counterattack ready after two seconds")
	cleanup()
	done()

func test_knee_shot_and_split_volley() -> void:
	setup(&"ranger")
	player.stats.flags = {&"knee_shot": 0.40}
	var a := target(Vector3(0, 0, 6))
	player.rng.seed = proc_seed(0.25)
	var arrow := attack(1)
	arrow.tags[&"projectile"] = true
	var result := a.receive_hit(arrow, player)
	ok(result.total > 100, "Knee Shot adds damage")
	near(a.status.remaining(&"stunned"), 0.4, 0.001, "Knee Shot stuns for 0.4 seconds")
	a.status.remove(&"stunned")
	player.rng.seed = proc_seed(0.25)
	a.receive_hit(arrow.clone(), player)
	ok(not a.status.has(&"stunned"), "Knee Shot respects stun immunity")
	player.stats.flags = {&"split_shot": 0.75}
	player.rng.seed = proc_seed(0.30)
	player.aim_point = a.position
	Game.hover_target = null
	var hits := [0]
	var shot := Projectile.spawn(world, player.cast_point(), player.projectile_dir(), 30.0, attack(2), player, BH.LAYER_ENEMY, Elements.PHYSICAL, "none")
	shot.on_hit = func(_a: Actor, _r: DamageResult, _pt: Vector3) -> void: hits[0] += 1
	player.class_passives.split_shot(shot)
	var count := 0
	for child in world.get_children():
		if child is Projectile:
			count += 1
	eq(count, 8, "maximum split produces eight arrows total")
	near(shot.request.skill_mult, 0.75, 0.001, "each split arrow uses 75 percent damage")
	await frames(25)
	eq(hits[0], 1, "one target is hit once by the volley")
	cleanup()
	done()

func test_gravity_tentacle_curses_and_control_immunity() -> void:
	setup(&"mage")
	var a := target(Vector3(3, 0, 4))
	await frames(2)
	var gravity := DB.skill(&"gravity_pull")
	ClassSpells.cast(player.runner, gravity, gravity.resolve(1), Vector3(0, 0, 4))
	ok(a.position.x < 2.0, "gravity pulls into the selected center instantly")
	ok(a.hp < a.max_hp(), "gravity also deals damage")
	var tentacle := DB.skill(&"spike_tentacle")
	ClassSpells.cast(player.runner, tentacle, tentacle.resolve(30), a.position)
	near(a.status.remaining(&"stunned"), 1.6, 0.001, "bonus ranks cannot exceed 1.6 second stun")
	a.status.remove(&"stunned")
	a.status.immunities[&"stunned"] = true
	ClassSpells.cast(player.runner, tentacle, tentacle.resolve(25), a.position)
	ok(not a.status.has(&"stunned"), "immune target cannot be stunned")
	a.status.clear()
	var dark := DB.skill(&"dark_arts")
	ClassSpells.cast(player.runner, dark, dark.resolve(1), a.position)
	var curses := 0
	for id in [&"weakened", &"armor_broken", &"silenced", &"bloodcurse"]:
		if a.status.has(id):
			curses += 1
	eq(curses, 1, "Dark Arts applies one random curse")
	cleanup()
	done()

func box(at: Vector3, size: Vector3) -> void:
	var body := StaticBody3D.new()
	body.collision_layer = BH.LAYER_WORLD
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	cs.shape = shape
	body.add_child(cs)
	world.add_child(body)
	body.position = at

func test_projectiles_cross_stairs_both_directions_and_walls_still_block() -> void:
	setup(&"ranger")
	Game.hover_target = null
	for i in range(1, 5):
		box(Vector3(10 + i * 2, i * 0.25 - 0.1, 0), Vector3(2, i * 0.5, 4))
	var a := target(Vector3(20, 2, 0))
	player.aim_point = a.position
	var dir := player.projectile_dir()
	ok(dir.y > 0.0 and dir.y < 0.2, "shallow uphill aim is preserved")
	await frames(2)
	var p := Projectile.spawn(world, player.cast_point(), dir, 45.0, attack(1), player, BH.LAYER_ENEMY, Elements.PHYSICAL, "none")
	p.max_range = 30.0
	await frames(45)
	ok(a.hp < a.max_hp(), "arrow reaches elevated target across steps")
	a.position = Vector3.ZERO
	a.hp = a.max_hp()
	player.position = Vector3(20, 2, 0)
	player.aim_point = a.position
	await frames(2)
	p = Projectile.spawn(world, player.cast_point(), player.projectile_dir(), 45.0, attack(2), player, BH.LAYER_ENEMY, Elements.FIRE, "none")
	p.max_range = 30.0
	await frames(45)
	ok(a.hp < a.max_hp(), "spell reaches lower target across steps")
	a.hp = a.max_hp()
	box(Vector3(7, 3, 0), Vector3(0.1, 8, 4))
	await frames(2)
	p = Projectile.spawn(world, player.cast_point(), player.projectile_dir(), 90.0, attack(3), player, BH.LAYER_ENEMY, Elements.FIRE, "none")
	p.max_range = 30.0
	await frames(25)
	near(a.hp, a.max_hp(), 0.001, "thin wall still stops projectile")
	cleanup()
	done()

func test_orb_and_sentinel_keep_elevation_and_manual_aim() -> void:
	setup(&"mage")
	var a := target(Vector3(10, 2, 0))
	player.aim_point = a.position
	var orb := FrostOrb.create(world, player.cast_point(), player.projectile_dir(), attack(1), player, BH.LAYER_ENEMY)
	ok(orb.dir.y > 0.0, "Frost Orb keeps upward aim")
	orb.free()
	var sentry := SkillSentry.create(world, Vector3.ZERO, "turret", attack(2), player, BH.LAYER_ENEMY, 8.0, 0.8, 14.0, Elements.FIRE)
	sentry.set_physics_process(false)
	await frames(2)
	sentry._shoot()
	var found := false
	for child in world.get_children():
		if child is Projectile:
			found = true
			ok(child.velocity.y > 0.0, "Flame Sentinel aims at the elevated target")
	ok(found, "sentinel fires at visible target")
	Game.hover_target = a
	player.first_person = false          # the player's own camera setting (settings.cfg) turns it on after spawning
	player.aim_point = Vector3(-10, 0, 0)
	ok(player.projectile_dir().x < 0.0, "manual aim overrides an older hovered enemy")
	Game.hover_target = null
	cleanup()
	done()
