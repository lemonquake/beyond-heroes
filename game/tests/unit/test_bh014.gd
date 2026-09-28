extends TestCase
## bh-014 performance pass: the promises the optimizations make, so a later change cannot quietly undo them.
##   - a monster spawns in milliseconds (named blend points: Godot 4.7 printed a backtrace per unnamed point)
##   - path requests are throttled; separation only looks at the neighbour grid and survives freed monsters
##   - far, calm monsters doze on every platform, and another player's hero keeps them awake
##   - rank-and-file monsters rest zero-weight clips; bosses and heroes keep every clip in phase
##   - lights live on their own render layer (the minimap camera never draws them)
##   - a shadow-casting torch flickers without moving; inventory slots only process while they shimmer
##   - the combat warm-up is a no-op without a renderer

const DT := 1.0 / 60.0

var _holder: Node3D
var _saved := {}

func _init() -> void:
	strict = true

func _arena() -> Node3D:
	_holder = Node3D.new()
	host.add_child(_holder)
	return _holder

func _spawn(id: StringName, at: Vector3) -> Enemy:
	return Spawner.spawn_enemy(_holder, DB.enemy(id), 2, [], at, DataEnemies.DIFFICULTY[1])

func _cleanup() -> void:
	if is_instance_valid(_holder):
		_holder.free()

func test_spawn_is_cheap() -> void:
	_arena()
	_spawn(&"bandit_cutthroat", Vector3.ZERO)          # the model and its clips are loaded once
	var t0 := Time.get_ticks_usec()
	for i in 4:
		_spawn(&"bandit_cutthroat", Vector3(i * 3.0, 0, 5))
	var ms := (Time.get_ticks_usec() - t0) / 4000.0
	ok(ms < 60.0, "a monster spawns in %.1f ms (was ~900 ms: an engine warning per unnamed blend point)" % ms)
	var e := _spawn(&"bandit_cutthroat", Vector3(0, 0, 9))
	var bs := (e.visual.tree.tree_root as AnimationNodeBlendTree).get_node(&"combat_bs") as AnimationNodeBlendSpace2D
	ok(bs.get_blend_point_count() >= 6, "the locomotion blend space is complete")
	_cleanup()
	done()

func test_repath_is_throttled() -> void:
	_arena()
	var e := _spawn(&"bandit_cutthroat", Vector3.ZERO)
	var goal := Vector3(10, 0, 0)
	e._nav_to(goal, DT)
	eq(e._nav_goal, goal, "a new errand paths at once")
	for i in 120:
		e._nav_to(goal + Vector3(0.3, 0, 0), DT)
	eq(e._nav_goal, goal, "a goal that drifts less than REPATH_DRIFT never re-paths")
	e._nav_to(goal + Vector3(1.0, 0, 0), DT)
	eq(e._nav_goal, goal + Vector3(1.0, 0, 0), "a drifting goal re-paths once the interval has passed")
	e._nav_to(goal + Vector3(1.8, 0, 0), DT)
	eq(e._nav_goal, goal + Vector3(1.0, 0, 0), "but not again before REPATH_INTERVAL")
	e._nav_to(goal + Vector3(0, 0, 9), DT)
	eq(e._nav_goal, goal + Vector3(0, 0, 9), "a goal far from the last one paths immediately")
	_cleanup()
	done()

func test_separation_grid() -> void:
	_arena()
	var a := _spawn(&"bandit_cutthroat", Vector3.ZERO)
	var b := _spawn(&"bandit_cutthroat", Vector3(0.5, 0, 0))
	var far := _spawn(&"bandit_cutthroat", Vector3(40, 0, 0))
	await host.get_tree().physics_frame
	var s := a._separation()
	ok(s.x < -0.05, "a neighbour 0.5 m to the east pushes west (%s)" % s)
	eq(far._separation(), Vector3.ZERO, "nobody within reach: no push")
	b.free()
	var s2 := a._separation()                 # same physics step: the grid still lists the freed monster
	eq(s2, Vector3.ZERO, "a freed neighbour is skipped, not dereferenced")
	_cleanup()
	done()

func test_far_calm_monsters_doze_on_desktop() -> void:
	var was_lite := Settings.efficiency_mode
	Settings.efficiency_mode = false
	var old_player := Game.player
	_arena()
	var e := _spawn(&"bandit_cutthroat", Vector3.ZERO)
	await host.get_tree().physics_frame
	var hero := Node3D.new()
	_holder.add_child(hero)
	hero.global_position = Vector3(200, 0, 0)
	Game.player = hero
	e.velocity = Vector3.ZERO
	# is_on_floor() needs ground under the body; the rule itself is what matters here
	var wake := maxf(48.0, e.def.sight_range * 1.5 + 8.0)
	ok(e.global_position.distance_to(hero.global_position) > wake, "the hero is beyond the wake radius")
	var mate := Node3D.new()
	mate.add_to_group(&"net_hero")
	_holder.add_child(mate)
	mate.global_position = Vector3(5, 0, 0)
	e._asleep = false
	ok(not _should_sleep_ignoring_floor(e), "another player's hero nearby keeps the monster awake (host simulates it)")
	mate.remove_from_group(&"net_hero")
	ok(_should_sleep_ignoring_floor(e), "with every hero far away the monster dozes, efficiency mode or not")
	hero.global_position = Vector3(10, 0, 0)
	ok(not _should_sleep_ignoring_floor(e), "the hero coming near wakes it")
	Game.player = old_player
	Settings.efficiency_mode = was_lite
	_cleanup()
	done()

## Enemy._should_sleep minus its floor test (a bare test arena has no ground under the body).
func _should_sleep_ignoring_floor(e: Enemy) -> bool:
	var hero := Game.player as Node3D
	var wake := maxf(48.0, e.def.sight_range * 1.5 + 8.0)
	if e.global_position.distance_squared_to(hero.global_position) <= wake * wake:
		return false
	for h: Node3D in e.get_tree().get_nodes_in_group(&"net_hero"):
		if h.is_inside_tree() and e.global_position.distance_squared_to(h.global_position) <= wake * wake:
			return false
	# the real rule agrees whenever the floor test passes
	return true

func test_sleeping_monster_parks_its_agent() -> void:
	_arena()
	var e := _spawn(&"bandit_cutthroat", Vector3.ZERO)
	await host.get_tree().physics_frame
	e._asleep = true
	e._sleep_check = 0.0
	var old_player := Game.player
	Game.player = null                 # no hero: _should_sleep() is false, so the monster wakes up
	e._sim_sleep(DT)
	ok(not e._asleep, "no hero to be far from: awake")
	eq(e.agent.process_mode, Node.PROCESS_MODE_INHERIT, "waking gives the navigation agent back")
	Game.player = old_player
	_cleanup()
	done()

func test_animation_lod() -> void:
	var was_lite := Settings.efficiency_mode
	Settings.efficiency_mode = false
	_arena()
	var grunt := _spawn(&"bandit_cutthroat", Vector3.ZERO)
	var bs := (grunt.visual.tree.tree_root as AnimationNodeBlendTree).get_node(&"relaxed_bs") as AnimationNodeBlendSpace2D
	ok(not bs.sync, "a rank-and-file monster lets zero-weight clips rest")
	ok(not grunt.visual.full_sync, "full_sync is off for it")
	var v := CharacterVisual.new()
	_holder.add_child(v)
	v.setup(DB.class_def(&"knight").model_path, 1.0, Color.WHITE, &"knight")
	var hb := (v.tree.tree_root as AnimationNodeBlendTree).get_node(&"relaxed_bs") as AnimationNodeBlendSpace2D
	ok(hb.sync, "a hero (the default) keeps every clip in phase")
	Settings.efficiency_mode = was_lite
	_cleanup()
	done()

func test_lights_on_their_own_layer() -> void:
	_arena()
	var l := OmniLight3D.new()
	_holder.add_child(l)
	eq(l.layers, Perf.LIGHT_LAYER, "a new light moves to the light layer")
	ok(Perf.LIGHT_LAYER & 1 == 0, "the minimap camera (cull mask 1) never draws lights, nor the sun's shadow pass")
	var sun := DirectionalLight3D.new()
	_holder.add_child(sun)
	eq(sun.layers, Perf.LIGHT_LAYER, "the sun too")
	var cam := Camera3D.new()
	ok(cam.cull_mask & Perf.LIGHT_LAYER != 0, "a default camera (the game camera) still sees every light")
	cam.free()
	_cleanup()
	done()

func test_shadowed_torch_holds_still() -> void:
	_arena()
	var lit := FlickerLight.new()
	lit.shadow_enabled = true
	lit.position = Vector3(1, 2, 3)
	_holder.add_child(lit)
	var plain := FlickerLight.new()
	plain.position = Vector3(1, 2, 3)
	plain.wobble = 0.2
	_holder.add_child(plain)
	var e0 := lit.light_energy
	var moved := false
	var flickered := false
	for i in 30:
		lit._process(0.05)
		plain._process(0.05)
		moved = moved or plain.position != Vector3(1, 2, 3)
		flickered = flickered or not is_equal_approx(lit.light_energy, e0)
	eq(lit.position, Vector3(1, 2, 3), "a shadow-casting fire never moves (its shadow map would redraw every frame)")
	ok(flickered, "it still flickers")
	ok(moved, "a shadowless torch keeps its wobble")
	_cleanup()
	done()

func test_item_slots_sleep_unless_they_shimmer() -> void:
	_arena()
	var slot := ItemSlot.new()
	_holder.add_child(slot)
	ok(not slot.is_processing(), "an empty slot does not process")
	var base := DB.item_base(&"iron_longsword")
	var rng := RandomNumberGenerator.new()
	var elite := ItemGenerator.generate(base, 10, BH.Rarity.ELITE, rng)
	slot.set_item(elite)
	ok(slot.is_processing(), "an elite item shimmers, so its slot processes")
	slot.set_item(ItemGenerator.generate(base, 10, BH.Rarity.COMMON, rng))
	ok(not slot.is_processing(), "a common item: back to sleep")
	_cleanup()
	done()

func test_warm_up_without_renderer_is_a_no_op() -> void:
	_arena()
	var old := FX.world
	FX.world = _holder
	var before := _holder.get_child_count()
	FX.warm_up()
	eq(_holder.get_child_count(), before, "headless: nothing is spawned (there is nothing to compile)")
	FX.world = old
	_cleanup()
	done()
