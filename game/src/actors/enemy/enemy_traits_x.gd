extends "res://src/actors/enemy/enemy_traits_ext.gd"
## bh-013: the signature mechanics of the twenty-one new monsters (and their bosses). Extends the bh-010 helper, so an
## Enemy holds one `ext` for both; everything that waits is still counted down in tick() (tests step it by hand).
##
##   bound_summoner  Gravecaller: "bone_circle" raises Bone Thralls in a telegraphed ring; they crumble when it dies
##   rift            Riftcaller: "rift" tears open a Void Rift (a destructible structure) that releases shades; bound
##   void_rift       the Rift itself: stationary, releases a minion every RIFT_PERIOD s (capped), closes with its caller
##   hive_nest       Waxen Hive: stationary, releases Hive Drones; bursts into slowing honey when destroyed
##   splitter        Gloam Ooze: splits into two smaller oozes on death (SPLIT_GENERATIONS deep)
##   illusionist     Mirage Weaver: "images" conjures mirror images; struck, it may swap places with one
##   mirror_image    an image: frail, expires after IMAGE_LIFE s
##   burrower        Tunnel Maw: dives (untargetable), travels under the hero, erupts beneath them, surfaces to fight
##   "tether"        Bloodbinder: a channelled beam that drains the hero and heals the caster; breaks on range/sight
##   ward_link       Aegis Acolyte: links an ally, who takes LINK_TAKEN damage until the acolyte falls or the link snaps
##   "strikes"       Storm Herald: runes around the hero, bolts fall after a delay; Static stacks to a stun
##   mirror_stance   Mirror Knight: a mirror guard reflects projectiles and part of frontal blows
##   rally           Warband Chieftain: war cry hastes and empowers allies; its death breaks its band (fear)
##   twin            Soulbound Twin: pairs up; a fallen twin is rekindled by the other unless both fall close together
##   thorn_hide      Briar Lasher: melee attackers take thorns damage
##   parasite_host   Broodhost: sheds Leechlings when badly hurt and when it dies
##   "mines"         Goblin Sapper: plants proximity mines (SapperMine)
##   loot_runner     Treasure Gremlin: never fights, flees, sheds gold when hit, escapes after GREMLIN_ESCAPE s
##   "gaze"          Stonegaze Basilisk: a channelled cone; facing it builds Petrification
##   phase_shift     Gloomwraith: alternates ethereal (immune to physical, weak to elements) and tangible
##   curl            Shellback Grinder: curls into an armored ball for its roll; a poise break flips it, exposed
##   "beam"          Prism Sentinel: a sweeping light beam

const X_TRAITS := [&"bound_summoner", &"void_rift", &"hive_nest", &"splitter", &"illusionist", &"mirror_image", &"burrower",
	&"ward_link", &"mirror_stance", &"rally", &"twin", &"thorn_hide", &"parasite_host", &"loot_runner", &"phase_shift", &"curl"]
const X_KINDS := ["bone_circle", "rift", "tether", "strikes", "mines", "gaze", "beam"]
const X_ABILITIES := ["images", "link", "mirror", "rally"]

const RIFT_PERIOD := 6.0
const HIVE_PERIOD := 5.0
const SPLIT_GENERATIONS := 2
const SPLIT_SCALE := 0.68
const SPLIT_HP := 0.45
const IMAGE_LIFE := 12.0
const SWAP_COOLDOWN := 6.0
const BURROW_EVERY := 7.5
const BURROW_TRAVEL := 4.0
const BURROW_SPEED := 7.5
const ERUPT_RADIUS := 2.6
const ERUPT_WARN := 0.9
const LINK_RANGE := 13.0
const LINK_SNAP := 18.0
const LINK_TAKEN := 0.15
const TETHER_RANGE := 12.0
const TETHER_TICK := 0.5
const STATIC_STACKS := 3
const RALLY_RANGE := 12.0
const TWIN_REKINDLE := 5.0
const GREMLIN_ESCAPE := 25.0
const GAZE_ARC := 70.0
const GAZE_RANGE := 13.0
const GAZE_BUILD := 18.0             # petrification per 0.25 s while you look at it (100 = petrified)
const PHASE_PERIOD := 5.0
const CURL_TAKEN := 0.1
const THORNS := 0.25

var _rift_t := 2.0
var _hive_t := 1.0
var _swap_cd := 0.0
var _burrow_t := BURROW_EVERY
var burrowed := false
var _burrow_left := 0.0
var _erupting := false
var link_to: Enemy = null
var _link_beam: MeshInstance3D
var _tether_beam: MeshInstance3D
var _tether: Dictionary = {}
var twin: Enemy = null
var _rekindle_t := -1.0
var _rekindled := false
var _host_shed := false
var _alerted_t := -1.0
var _gold_cd := 0.0
var escaped := false
var _gaze: Dictionary = {}
var ethereal := false
var _phase_t := PHASE_PERIOD
var curled := false
var _flipped_t := 0.0
var _beam: Dictionary = {}
var mines: Array = []

static func wants_x(d: EnemyDef) -> bool:
	for t in d.traits:
		if X_TRAITS.has(t):
			return true
	for a in d.attacks:
		if X_KINDS.has(String(a.get("kind", ""))):
			return true
	for ab in d.abilities:
		if X_ABILITIES.has(String(ab.get("kind", ""))):
			return true
	return false

# ---- Lifecycle ------------------------------------------------------------------------------------------------

func setup() -> void:
	super.setup()
	if has(&"thorn_hide"):
		e.status.apply(&"aura_thorns", 0.0, THORNS)
	if has(&"void_rift") or has(&"hive_nest"):
		e.patrol_radius = 0.0
		var glow := VFXLib.particles(e.def.tint.lightened(0.3), 16, 1.4, false, 0.3, 0.7, 60.0, Vector3(0, 1.0, 0), 0.5)
		glow.position.y = 1.2
		e.add_child(glow)
	if has(&"mirror_image"):
		if e.visual:
			e.visual.set_rim(Color(0.6, 0.95, 1.0), 0.9)
			e.visual.set_opacity(0.7)
		later(IMAGE_LIFE, func() -> void:
			if e.alive:
				_vanish(e))
	if has(&"phase_shift"):
		_phase_t = PHASE_PERIOD * randf_range(0.5, 1.0)
	if has(&"loot_runner") and e.visual:
		var sparkle := VFXLib.particles(Color(1.0, 0.85, 0.3, 0.9), 12, 0.8, false, 0.12, 0.8, 90.0, Vector3(0, 0.6, 0), 0.4)
		sparkle.position.y = 0.9
		e.add_child(sparkle)

func pre_tick(delta: float) -> bool:
	if super.pre_tick(delta):
		return true
	if has(&"void_rift"):
		_run_jobs(delta)
		e.knock_velocity = Vector3.ZERO
		_rift_t -= delta
		if _rift_t <= 0.0:
			_rift_t = RIFT_PERIOD
			rift_pulse()
		return true
	if has(&"hive_nest"):
		_run_jobs(delta)
		e.knock_velocity = Vector3.ZERO
		_hive_t -= delta
		if _hive_t <= 0.0:
			_hive_t = HIVE_PERIOD
			hive_pulse()
		return true
	if burrowed:
		_run_jobs(delta)
		_burrow_step(delta)
		return true
	if _flipped_t > 0.0:
		_run_jobs(delta)
		_flipped_t -= delta
		if _flipped_t <= 0.0 and e.visual:
			e.visual.stop_action()
			e.visual.play_action(&"shell_uncurl")
		return true
	return false

func tick(delta: float) -> void:
	super.tick(delta)
	if not e.alive:
		return
	_swap_cd = maxf(0.0, _swap_cd - delta)
	_gold_cd = maxf(0.0, _gold_cd - delta)
	if has(&"burrower") and e.brain.is_engaged() and e.action == null and not _erupting:
		_burrow_t -= delta
		if _burrow_t <= 0.0:
			burrow()
	if link_to != null:
		_link_step()
	if not _tether.is_empty():
		_tether_step(delta)
	if not _gaze.is_empty():
		_gaze_step(delta)
	if not _beam.is_empty():
		_beam_step(delta)
	if has(&"twin") and _rekindle_t >= 0.0:
		_rekindle_t -= delta
		if _rekindle_t <= 0.0:
			_rekindle_t = -1.0
			rekindle()
	if has(&"parasite_host") and not _host_shed and e.hp < e.max_hp() * 0.5:
		_host_shed = true
		shed_parasites(2)
	if has(&"phase_shift") and e.brain.is_engaged():
		_phase_t -= delta
		if _phase_t <= 0.0:
			_phase_t = PHASE_PERIOD
			set_ethereal(not ethereal)
	if has(&"curl"):
		var rolling: bool = e.current_attack.get("id", &"") == &"roll" and e.action != null
		if rolling != curled:
			set_curled(rolling)
		if curled and e.status.has(&"staggered"):
			flip()
	if has(&"loot_runner") and _alerted_t >= 0.0:
		_alerted_t += delta
		if _alerted_t >= GREMLIN_ESCAPE and not escaped:
			escape()

func think() -> bool:
	if super.think():
		return true
	if has(&"loot_runner"):
		return _runner_think()
	if not _tether.is_empty() or not _gaze.is_empty() or not _beam.is_empty():
		return true     # channelling
	return false

func on_hit(result: DamageResult, req: DamageRequest, attacker: Node) -> void:
	super.on_hit(result, req, attacker)
	if result.evaded:
		return
	if has(&"mirror_image") and result.total > 0:
		_vanish(e)
		return
	if has(&"illusionist") and _swap_cd <= 0.0 and result.total > 0:
		_try_swap()
	if has(&"loot_runner") and _gold_cd <= 0.0 and result.total > 0:
		_gold_cd = 0.35
		Loot.spawn_gold(e.global_position, 3 + e.level)
		if _alerted_t < 0.0:
			_alerted_t = 0.0
	if req.tags.get(&"mirror_reflect", false) and attacker is Actor and (attacker as Actor).alive and result.total > 0:
		var back := _req(0.0, Elements.LIGHT, 1.0, 0.0, "Mirror")
		back.base_min = float(result.total) * 0.15
		back.base_max = back.base_min
		back.can_crit = false
		back.tags[&"thorns"] = true
		(attacker as Actor).receive_hit(back, e, (attacker as Actor).center())
		FX.spawn(VFXLib.light_flash(Color(0.85, 0.95, 1.0), 3.0, 4.0, 0.2), e.center() + e.forward() * 0.6)

func on_death(killer: Node) -> void:
	super.on_death(killer)
	_end_link()
	_end_tether()
	_end_beam()
	_gaze = {}
	if has(&"bound_summoner") or has(&"rift") or _has_kind("rift") or _has_kind("bone_circle"):
		for m in minions:
			if is_instance_valid(m) and (m as Enemy).alive:
				_crumble(m as Enemy)
	if has(&"splitter"):
		split()
	if has(&"parasite_host"):
		shed_parasites(4)
	if has(&"rally"):
		_break_band()
	if has(&"hive_nest"):
		var req := _req(0.4, Elements.EARTH, 0.5, 0.0, "Honey")
		AreaEffects.hazard(FX.world, e.global_position, 3.2, 6.0, req, null, BH.LAYER_PLAYER, Color(1.0, 0.7, 0.15), 0.5)
	if has(&"twin") and twin and is_instance_valid(twin) and twin.alive and twin.ext and not _rekindled:
		(twin.ext as Object).call(&"start_rekindle", e)

# ---- Stats and incoming damage ----------------------------------------------------------------------------------------

func stat_mods(mods: Array) -> void:
	super.stat_mods(mods)
	var gen := int(e.get_meta(&"split_gen", 0))
	if gen > 0:
		mods.append(StatModifier.more(&"max_hp", pow(SPLIT_HP, gen) - 1.0, "Split"))
		mods.append(StatModifier.more(&"outgoing_damage", pow(0.8, gen) - 1.0, "Split"))
	if has(&"mirror_image"):
		mods.append(StatModifier.more(&"max_hp", -0.92, "Image"))
		mods.append(StatModifier.more(&"outgoing_damage", -0.7, "Image"))

## Before the damage pipeline runs (Enemy._prepare_incoming): ethereal, curled, mirror guard.
func prepare_incoming(req: DamageRequest, attacker: Node) -> void:
	if req.kind == DamageRequest.Kind.DOT:
		return
	if ethereal:
		var elemental := false
		for el in req.conversion:
			if int(el) != Elements.PHYSICAL and float(req.conversion[el]) > 0.0:
				elemental = true
		if elemental:
			req.more.append(["Ethereal", 1.5])
		else:
			req.more.append(["Ethereal", 0.0])
			FX.text_popup(e.center() + Vector3.UP, "Immune", Color(0.7, 0.8, 1.0), 0.7)
	if curled:
		req.more.append(["Curled", CURL_TAKEN])
	if e.status.has(&"mirror_guard") and attacker is Node3D and not req.tags.has(&"thorns") and not req.tags.has(&"proc"):
		var to: Vector3 = ((attacker as Node3D).global_position - e.global_position).slide(Vector3.UP)
		if to.length() > 0.05 and e.forward().angle_to(to.normalized()) < deg_to_rad(75.0):
			req.more.append(["Mirror Guard", 0.4])
			req.tags[&"mirror_reflect"] = true

# ---- Attacks the base AI does not know (Enemy._start_attack falls through to here) ----------------------------------

func start_special(a: Dictionary, act: TimedAction) -> void:
	match String(a.kind):
		"bone_circle":
			act.on_release = func() -> void: bone_circle(a)
		"rift":
			act.on_release = func() -> void: open_rift(a)
		"tether":
			act.on_release = func() -> void: start_tether(a)
		"strikes":
			act.on_release = func() -> void: storm_strikes(a)
		"mines":
			act.on_release = func() -> void: plant_mine(a)
		"gaze":
			act.on_release = func() -> void: start_gaze(a)
		"beam":
			act.on_release = func() -> void: start_beam(a)

func _has_kind(k: String) -> bool:
	for a in e.def.attacks:
		if String(a.get("kind", "")) == k:
			return true
	return false

func try_ability(ab: Dictionary) -> bool:
	match String(ab.kind):
		"images":
			return _try_images(ab)
		"link":
			return _try_link(ab)
		"mirror":
			return _try_mirror(ab)
		"rally":
			return _try_rally(ab)
	return super.try_ability(ab)

# ---- Summoners ------------------------------------------------------------------------------------------------------

## Gravecaller: a ring of grave-light near the hero; when it fills, Bone Thralls claw out of it.
func bone_circle(a: Dictionary) -> void:
	if not e.alive:
		return
	var id := StringName(a.get("summon", &"bone_thrall"))
	var cap := int(a.get("cap", 6))
	if not _can_add(cap, id):
		return
	var spot := _summon_spot(minf(e._dist * 0.6, 5.0))
	var n := mini(int(a.get("count", 3)), cap - alive_minions(id))
	var delay := float(a.get("delay", 1.1))
	_tele("ring", 2.4, delay, Color(0.45, 1.0, 0.6, 0.8), spot)
	var wisps := VFXLib.particles(Color(0.45, 1.0, 0.6, 0.8), 22, 1.0, false, 0.2, 1.4, 50.0, Vector3(0, 1.2, 0), 1.6)
	FX.spawn(wisps, spot + Vector3.UP * 0.1)
	if is_instance_valid(wisps) and wisps.is_inside_tree():
		wisps.get_tree().create_timer(delay + 0.3, false).timeout.connect(wisps.queue_free)
	Audio.play_at(&"dark_cast", e.global_position)
	later(delay, func() -> void:
		if not e.alive:
			return
		for i in mini(n, GLOBAL_MINION_CAP - global_minions(e.get_tree())):
			var ang := TAU * float(i) / float(maxi(n, 1))
			var p := spot + Vector3(cos(ang), 0, sin(ang)) * 1.8
			if e.is_inside_tree():
				p = CombatQuery.reachable_point(e.get_world_3d(), spot, p, 0.3)
			var m := spawn_minion(id, p)
			if m and m.visual:
				m.visual.play_action(&"revive")
		FX.spawn(VFXLib.particles(Color(0.5, 1.0, 0.65, 0.9), 30, 1.0, true, 0.2, 2.5, 180.0, Vector3(0, 1.5, 0), 1.2), spot + Vector3.UP)
		Audio.play_at(&"skeleton_rattle", spot, 2.0))

## A bound minion falls apart when its maker dies.
func _crumble(m: Enemy) -> void:
	FX.spawn(VFXLib.particles(Color(0.6, 0.9, 0.7, 0.8), 16, 0.8, true, 0.4, 1.4, 90.0, Vector3(0, 0.5, 0), 0.5, false), m.center())
	m.set_meta(&"bound_crumble", true)
	m.die(null)

## Riftcaller: tears a Void Rift open a few metres to its side.
func open_rift(a: Dictionary) -> void:
	if not e.alive:
		return
	var cap := int(a.get("cap", 1))
	if not _can_add(cap, &"void_rift"):
		return
	var spot := _summon_spot(3.0, 3.5 * (1.0 if randf() < 0.5 else -1.0))
	_tele("circle", 1.6, 0.9, Color(0.7, 0.35, 1.0, 0.8), spot)
	later(0.9, func() -> void:
		if not e.alive or not _can_add(cap, &"void_rift"):
			return
		var r := spawn_minion(&"void_rift", spot)
		if r:
			r.set_meta(&"rift_spawn", StringName(a.get("summon", &"shade_stalker")))
			r.set_meta(&"rift_cap", int(a.get("rift_cap", 3)))
			FX.spawn(VFXLib.ring_wave(Color(0.7, 0.35, 1.0, 0.9), 3.0, 0.5, 0.8), spot)
			Audio.play_at(&"dark_cast", spot, 2.0))

## The rift releases one minion (capped), a little way out from its mouth.
func rift_pulse() -> Enemy:
	var id := StringName(e.get_meta(&"rift_spawn", &"shade_stalker"))
	if not _can_add(int(e.get_meta(&"rift_cap", 3)), id) or not e.is_inside_tree():
		return null
	if _hero_near(40.0) == null:
		return null
	var p := e.global_position + Vector3(randf_range(-1.0, 1.0), 0, randf_range(-1.0, 1.0)).normalized() * 1.8
	p = CombatQuery.reachable_point(e.get_world_3d(), e.global_position, p, 0.3)
	var m := spawn_minion(id, p)
	if m:
		FX.spawn(VFXLib.particles(Color(0.6, 0.3, 1.0, 0.9), 24, 0.6, true, 0.3, 3.0, 120.0, Vector3(0, 1.0, 0), 0.6), p + Vector3.UP)
	return m

## Waxen Hive: a drone crawls out of the comb (capped).
func hive_pulse() -> Enemy:
	if not _can_add(int(e.get_meta(&"hive_cap", 4)), &"hive_drone") or not e.is_inside_tree() or _hero_near(26.0) == null:
		return null
	var p := e.global_position + Vector3(randf_range(-1.0, 1.0), 0, randf_range(-1.0, 1.0)).normalized() * 1.6
	var m := spawn_minion(&"hive_drone", p)
	if m:
		FX.spawn(VFXLib.particles(Color(1.0, 0.75, 0.25, 0.9), 14, 0.5, true, 0.2, 2.0, 90.0, Vector3(0, 1.0, 0), 0.4), p + Vector3.UP)
	return m

## Broodhost: Leechlings burst out of its sacs.
func shed_parasites(n: int) -> void:
	if not e.is_inside_tree():
		return
	FX.spawn(VFXLib.particles(Color(0.6, 0.2, 0.55, 0.9), 26, 0.7, true, 0.3, 3.0, 160.0, Vector3(0, 1.5, 0), 0.8), e.center())
	FX.text_popup(e.center() + Vector3.UP * 1.2, "Parasites!", Color(0.85, 0.4, 0.8), 0.9)
	var room := mini(n, GLOBAL_MINION_CAP - global_minions(e.get_tree()))
	for i in room:
		var ang := TAU * float(i) / float(maxi(room, 1))
		var p := e.global_position + Vector3(cos(ang), 0, sin(ang)) * (e.body_radius + 0.8)
		p = CombatQuery.reachable_point(e.get_world_3d(), e.global_position, p, 0.2)
		spawn_minion(&"leechling", p)

# ---- Splitter -------------------------------------------------------------------------------------------------------

## Gloam Ooze: two smaller oozes pinch off the dead one (they join its camp, so the camp is only clear when all fall).
func split() -> Array:
	var gen := int(e.get_meta(&"split_gen", 0))
	var out := []
	if gen >= SPLIT_GENERATIONS or not e.is_inside_tree() or e.net_replica:
		return out
	var parent := e.get_parent()
	for i in 2:
		var side := e.forward().cross(Vector3.UP) * (1.0 if i == 0 else -1.0) * (e.body_radius + 0.4)
		var p := CombatQuery.reachable_point(e.get_world_3d(), e.global_position, e.global_position + side, 0.3)
		var m := Enemy.new()
		m.setup(e.def, e.level, e.elite_mods, e.difficulty)
		m.set_meta(&"split_gen", gen + 1)
		m.set_meta(&"size_mult", pow(SPLIT_SCALE, gen + 1))
		m.name = "Split_%s_%d" % [e.def.id, m.get_instance_id()]
		parent.add_child(m)
		m.global_position = p + Vector3.UP * 0.1
		m.home = e.home
		m.zone = e.zone
		m.patrol_radius = 2.0
		if e.target and is_instance_valid(e.target):
			m.alert_to(e.target.global_position)
		_join_camp(m)
		out.append(m)
	FX.spawn(VFXLib.particles(e.def.blood, 26, 0.7, true, 0.3, 3.0, 140.0, Vector3(0, 1.2, 0), 0.7), e.center())
	FX.text_popup(e.center() + Vector3.UP, "Splits!", e.def.tint.lightened(0.4), 0.9)
	return out

## A monster born in a fight joins the camp of the one that made it (the camp clears only when all are down).
func _join_camp(m: Enemy) -> void:
	var sp := Spawner.current()
	if sp == null:
		return
	for k in sp.camps:
		if (sp.camps[k] as Array).has(e):
			(sp.camps[k] as Array).append(m)
			sp.spawned.append(m)
			return

# ---- Illusionist ----------------------------------------------------------------------------------------------------

func _try_images(ab: Dictionary) -> bool:
	if e.target == null or not _can_add(int(ab.get("cap", 2)), &"mirror_image"):
		return false
	var n := mini(int(ab.get("count", 2)), int(ab.get("cap", 2)) - alive_minions(&"mirror_image"))
	var t := _cast(ab, func() -> void: conjure_images(n))
	return t >= 0.0

func conjure_images(n: int) -> Array:
	var out := []
	if not e.alive or not e.is_inside_tree():
		return out
	for i in n:
		var side := e.forward().cross(Vector3.UP) * (2.4 if i % 2 == 0 else -2.4) + e.forward() * randf_range(-1.0, 1.0)
		var p := CombatQuery.reachable_point(e.get_world_3d(), e.global_position, e.global_position + side, 0.3)
		var m := spawn_minion(&"mirror_image", p)
		if m:
			m.display_name = e.display_name
			out.append(m)
			FX.spawn(VFXLib.light_flash(Color(0.8, 0.95, 1.0), 3.0, 4.0, 0.25), p + Vector3.UP)
	Audio.play_at(&"blink", e.global_position)
	return out

## Struck: swap places with one of its images.
func _try_swap() -> bool:
	for m in minions:
		if is_instance_valid(m) and (m as Enemy).alive and (m as Enemy).def.id == &"mirror_image":
			var a := e.global_position
			var b := (m as Enemy).global_position
			e.global_position = b
			(m as Enemy).global_position = a
			_swap_cd = SWAP_COOLDOWN
			FX.spawn(VFXLib.light_flash(Color(0.8, 0.95, 1.0), 3.0, 4.0, 0.25), a + Vector3.UP)
			FX.spawn(VFXLib.light_flash(Color(0.8, 0.95, 1.0), 3.0, 4.0, 0.25), b + Vector3.UP)
			Audio.play_at(&"blink", b)
			return true
	return false

func _vanish(m: Enemy) -> void:
	FX.spawn(VFXLib.particles(Color(0.8, 0.95, 1.0, 0.9), 20, 0.5, true, 0.15, 3.0, 180.0, Vector3.ZERO, 0.4), m.center())
	m.set_meta(&"bound_crumble", true)
	m.die(null)
	if m.visual:
		m.visual.visible = false

# ---- Burrower -------------------------------------------------------------------------------------------------------

## Tunnel Maw: dives. Untargetable while it travels under the hero; erupts beneath them.
func burrow() -> void:
	if burrowed or not e.alive:
		return
	burrowed = true
	_burrow_left = BURROW_TRAVEL
	e.invulnerable = true
	e.remove_from_group(&"enemy")
	e.collision_layer = 0
	if e.bar:
		e.bar.visible = false
	if e.visual:
		e.visual.play_action(&"maw_burrow")
	FX.spawn(VFXLib.dust_puff(1.6), e.global_position)
	FX.spawn(VFXLib.debris(1.0, Color(0.5, 0.42, 0.3)), e.global_position)
	Audio.play_at(&"earth_quake", e.global_position)
	later(0.9, func() -> void:
		if burrowed and e.visual:
			e.visual.visible = false)

func _burrow_step(delta: float) -> void:
	if _erupting:
		return
	_burrow_left -= delta
	var t := e.target
	var goal := t.global_position if t and is_instance_valid(t) and t.alive else e.home
	var to := (goal - e.global_position).slide(Vector3.UP)
	if to.length() > 0.3:
		e.global_position += to.normalized() * minf(BURROW_SPEED * delta, to.length())
	if Engine.get_physics_frames() % 6 == 0:
		FX.spawn(VFXLib.dust_puff(0.6), e.global_position)
	if to.length() < 1.2 or _burrow_left <= 0.0:
		erupt()

func erupt() -> void:
	if _erupting or not e.alive:
		return
	_erupting = true
	var at := e.global_position
	if e.is_inside_tree():
		at = CombatQuery.ground_at(e.get_world_3d(), at)
	var req := _req(1.6, Elements.EARTH, 0.4, 10.0, "Erupt")
	var b := AreaEffects.delayed(FX.world, at, ERUPT_RADIUS, ERUPT_WARN, req, e, BH.LAYER_PLAYER, Color(1.0, 0.55, 0.2, 0.8))
	b.on_blast = func(pos: Vector3, hits: Array) -> void:
		FX.spawn(VFXLib.debris(1.4, Color(0.5, 0.42, 0.3)), pos)
		FX.spawn(VFXLib.dust_puff(1.8), pos)
		Events.camera_shake.emit(0.4)
		Audio.play_at(&"earth_quake", pos, 3.0)
		for h in hits:
			if h is Actor and (h as Actor).alive:
				(h as Actor).apply_knockback(Vector3.UP, 2.0, e.stats, e, 0, 7.0)
	later(ERUPT_WARN, surface)

func surface() -> void:
	burrowed = false
	_erupting = false
	_burrow_t = BURROW_EVERY * randf_range(0.85, 1.25)
	e.invulnerable = false
	if e.alive:
		e.add_to_group(&"enemy")
		e.collision_layer = BH.LAYER_ENEMY
		if e.bar:
			e.bar.visible = true
	if e.visual:
		e.visual.visible = true
		e.visual.play_action(&"maw_emerge")

# ---- Blood tether ---------------------------------------------------------------------------------------------------

func start_tether(a: Dictionary) -> void:
	var t := e.target
	if not e.alive or t == null or not is_instance_valid(t) or not t.alive:
		return
	_tether = {"a": a, "left": float(a.get("duration", 4.0)), "tick": TETHER_TICK, "t": t}
	_tether_beam = _beam_mesh(Color(0.95, 0.12, 0.2), 0.07)
	if e.visual:
		e.visual.hold_action(&"cast_channel")
	t.status.apply(&"blood_tether", float(a.get("duration", 4.0)))
	FX.text_popup(t.center() + Vector3.UP, "Blood Tether! Break away", Color(1.0, 0.35, 0.35), 1.1)

func _tether_step(delta: float) -> void:
	var t: Actor = _tether.get("t")
	if not e.alive or t == null or not is_instance_valid(t) or not t.alive or t.global_position.distance_to(e.global_position) > TETHER_RANGE \
			or (e.is_inside_tree() and CombatQuery.blocked(e.get_world_3d(), e.center(), t.center())):
		if t and is_instance_valid(t) and t.alive:
			FX.text_popup(t.center() + Vector3.UP, "Tether broken", Color(0.9, 0.9, 0.9), 0.8)
		_end_tether()
		return
	_place_beam(_tether_beam, e.center() + e.forward() * 0.4, t.center())
	_tether.tick -= delta
	_tether.left -= delta
	if _tether.tick <= 0.0:
		_tether.tick = TETHER_TICK
		var req := _req(float(_tether.a.get("mult", 0.3)), Elements.DARK, 1.0, 0.0, "Blood Tether")
		req.can_crit = false
		var res := t.receive_hit(req, e, t.center())
		if res and not res.evaded and res.total > 0:
			e.heal(float(res.total) * float(_tether.a.get("heal", 1.5)), true)
	if _tether.left <= 0.0:
		_end_tether()

func _end_tether() -> void:
	if not _tether.is_empty():
		var t: Actor = _tether.get("t")
		if t and is_instance_valid(t):
			t.status.remove(&"blood_tether")
	_tether = {}
	if _tether_beam and is_instance_valid(_tether_beam):
		_tether_beam.queue_free()
	_tether_beam = null
	if e.visual and e.alive and e.visual.current_action() == &"cast_channel":
		e.visual.stop_action()

func tethering() -> bool:
	return not _tether.is_empty()

# ---- Aegis link -----------------------------------------------------------------------------------------------------

func _try_link(ab: Dictionary) -> bool:
	if link_to != null or not e.brain.is_engaged():
		return false
	var best: Enemy = null
	var bd := LINK_RANGE
	for x in e.get_tree().get_nodes_in_group(&"enemy"):
		var o := x as Enemy
		if o == null or o == e or not o.alive or o.status.has(&"aegis_link") or o.has_trait(&"ward_link") or o.has_trait(&"mirror_image"):
			continue
		if o.def.id in [&"void_rift", &"hive_nest", &"war_totem"]:
			continue
		var d := o.global_position.distance_to(e.global_position)
		# prefer the strongest ally close by
		var score := d - (6.0 if o.is_elite or o.is_miniboss() or o.is_boss else 0.0) - o.def.hp * 0.01
		if score < bd:
			bd = score
			best = o
	if best == null:
		return false
	var who := best
	return _cast(ab, func() -> void: link(who)) >= 0.0

func link(o: Enemy) -> void:
	if not e.alive or o == null or not is_instance_valid(o) or not o.alive:
		return
	_end_link()
	link_to = o
	o.status.apply(&"aegis_link", 0.0)
	_link_beam = _beam_mesh(Color(1.0, 0.85, 0.35), 0.06)
	FX.text_popup(o.center() + Vector3.UP, "Aegis Link", Color(1.0, 0.85, 0.4), 1.0)
	Audio.play_at(&"holy_cast", e.global_position, -2.0)

func _link_step() -> void:
	if link_to == null or not is_instance_valid(link_to) or not link_to.alive or not e.alive \
			or link_to.global_position.distance_to(e.global_position) > LINK_SNAP:
		_end_link()
		return
	_place_beam(_link_beam, e.center() + Vector3.UP * 0.3, link_to.center())

func _end_link() -> void:
	if link_to != null and is_instance_valid(link_to):
		link_to.status.remove(&"aegis_link")
		if link_to.alive:
			FX.text_popup(link_to.center() + Vector3.UP, "Link broken", Color(0.9, 0.9, 0.9), 0.8)
	link_to = null
	if _link_beam and is_instance_valid(_link_beam):
		_link_beam.queue_free()
	_link_beam = null

# ---- Storm Herald ---------------------------------------------------------------------------------------------------

func storm_strikes(a: Dictionary) -> void:
	var t := e.target
	if not e.alive or t == null or not is_instance_valid(t):
		return
	var n := int(a.get("count", 4))
	var delay := float(a.get("delay", 1.3))
	var radius := float(a.get("radius", 1.8))
	for i in n:
		var off := Vector3.ZERO if i == 0 else Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized() * randf_range(2.0, 4.5)
		var at := t.global_position + off
		if e.is_inside_tree():
			at = CombatQuery.ground_at(e.get_world_3d(), at)
		var req := e._attack_request(a)
		req.evadable = false
		var d := delay + 0.12 * i
		var b := AreaEffects.delayed(FX.world, at, radius, d, req, e, BH.LAYER_PLAYER, Color(0.5, 0.85, 1.0, 0.8))
		b.on_blast = func(pos: Vector3, hits: Array) -> void:
			FX.spawn(VFXLib.lightning_bolt(pos + Vector3.UP * 12.0, pos, Color(0.7, 0.9, 1.0), 0.35, 0.2), Vector3.ZERO)
			FX.spawn(VFXLib.light_flash(Color(0.6, 0.85, 1.0), 5.0, 6.0, 0.2), pos + Vector3.UP)
			Audio.play_at(&"lightning_zap", pos)
			for h in hits:
				if h is Actor:
					add_static(h as Actor)
	Audio.play_at(&"dark_cast", e.global_position, -3.0)

## Static: three stacks and the hero is Stunned.
func add_static(t: Actor) -> int:
	if t == null or not t.alive:
		return 0
	var n := int(t.get_meta(&"static_stacks", 0)) + 1
	if not t.status.has(&"static_charge"):
		n = 1
	if n >= STATIC_STACKS:
		t.set_meta(&"static_stacks", 0)
		t.status.remove(&"static_charge")
		t.status.apply(&"stunned", 1.2)
		FX.text_popup(t.center() + Vector3.UP, "Overcharged!", Color(0.6, 0.9, 1.0), 1.1)
		return STATIC_STACKS
	t.set_meta(&"static_stacks", n)
	t.status.apply(&"static_charge", 6.0)
	return n

# ---- Goblin Sapper --------------------------------------------------------------------------------------------------

func plant_mine(a: Dictionary) -> Node3D:
	if not e.alive or not e.is_inside_tree():
		return null
	var keep: Array = []
	for m in mines:
		if is_instance_valid(m):
			keep.append(m)
	mines = keep
	if mines.size() >= int(a.get("cap", 4)):
		return null
	var at := e.global_position + e.forward() * 1.2
	if e.target and is_instance_valid(e.target) and e._dist < 6.0:
		at = e.global_position.lerp(e.target.global_position, 0.6)
	at = CombatQuery.ground_at(e.get_world_3d(), CombatQuery.reachable_point(e.get_world_3d(), e.global_position, at, 0.2))
	var req := e._attack_request(a)
	req.evadable = false
	var mine := SapperMine.new().setup(req, e, float(a.get("radius", 2.6)))
	FX.world.add_child(mine)
	mine.global_position = at
	mines.append(mine)
	return mine

# ---- Rally ----------------------------------------------------------------------------------------------------------

func _try_rally(ab: Dictionary) -> bool:
	if not e.brain.is_engaged():
		return false
	var allies := _allies(RALLY_RANGE)
	if allies.is_empty():
		return false
	return _cast(ab, func() -> void: rally(float(ab.get("duration", 8.0)))) >= 0.0

func rally(duration := 8.0) -> int:
	var n := 0
	for o in _allies(RALLY_RANGE) + [e]:
		o.status.apply(&"haste", duration)
		o.status.apply(&"empowered", duration)
		n += 1
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.45, 0.2, 0.9), RALLY_RANGE * 0.6, 0.6), e.global_position)
	FX.text_popup(e.center() + Vector3.UP * 1.4, "Rally!", Color(1.0, 0.55, 0.25), 1.1)
	Audio.play_at(&"boss_roar", e.global_position, -2.0)
	return n

func _break_band() -> void:
	var n := 0
	for o in _allies(RALLY_RANGE):
		if o.is_boss or o.is_miniboss():
			continue
		o.status.apply(&"feared", 3.0)
		n += 1
	if n > 0:
		FX.text_popup(e.center() + Vector3.UP * 1.4, "The band breaks!", Color(1.0, 0.8, 0.5), 1.2)

func _allies(r: float) -> Array:
	var out := []
	if not e.is_inside_tree():
		return out
	for x in e.get_tree().get_nodes_in_group(&"enemy"):
		var o := x as Enemy
		if o and o != e and o.alive and o.global_position.distance_to(e.global_position) <= r:
			out.append(o)
	return out

# ---- Twins ----------------------------------------------------------------------------------------------------------

static func pair(a: Enemy, b: Enemy) -> void:
	if a.ext:
		a.ext.set(&"twin", b)
	if b.ext:
		b.ext.set(&"twin", a)

## The surviving twin starts to rekindle the fallen one; it stands again unless the survivor falls in the meantime.
func start_rekindle(fallen: Enemy) -> void:
	if not e.alive or _rekindle_t >= 0.0:
		return
	_rekindle_t = TWIN_REKINDLE
	fallen.set(&"_reassembling", true)
	FX.text_popup(e.center() + Vector3.UP * 1.3, "Rekindling its twin!", Color(0.55, 0.9, 1.0), 1.2)
	_tele("ring", 1.4, TWIN_REKINDLE, Color(0.5, 0.9, 1.0, 0.7), fallen.global_position)

func rekindle() -> bool:
	if not e.alive or twin == null or not is_instance_valid(twin) or twin.alive:
		return false
	if twin.ext:
		twin.ext.set(&"_rekindled", true)
	twin._reassemble()
	return twin.alive

# ---- Treasure Gremlin -----------------------------------------------------------------------------------------------

func _runner_think() -> bool:
	var h := _hero_near(16.0)
	if h == null:
		return false
	if _alerted_t < 0.0:
		_alerted_t = 0.0
		FX.text_popup(e.center() + Vector3.UP, "A Treasure Gremlin! Catch it!", Color(1.0, 0.85, 0.3), 1.3)
	e.brain.go(EnemyBrain.State.RETREAT)
	var away := (e.global_position - h.global_position).slide(Vector3.UP)
	if away.length() < 0.1:
		away = -e.forward()
	var p := e.global_position + away.normalized().rotated(Vector3.UP, randf_range(-0.7, 0.7)) * 6.0
	e._move_target = CombatQuery.reachable_point(e.get_world_3d(), e.global_position, p, e.body_radius) if e.is_inside_tree() else p
	return true

## Too slow: it slips through a portal with its sack (no reward).
func escape() -> void:
	if escaped or not e.alive:
		return
	escaped = true
	FX.spawn(VFXLib.light_flash(Color(1.0, 0.85, 0.35), 5.0, 6.0, 0.4), e.center())
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.35, 0.9), 2.0, 0.4, 0.6), e.global_position)
	FX.text_popup(e.center() + Vector3.UP, "Escaped with the loot!", Color(1.0, 0.8, 0.35), 1.2)
	Audio.play_at(&"blink", e.global_position)
	e.alive = false
	e.remove_from_group(&"enemy")
	var sp := Spawner.current()
	if sp:
		for k in sp.camps.keys():
			var list: Array = sp.camps[k]
			if list.has(e):
				list.erase(e)
				if list.is_empty():
					sp.camps.erase(k)
	e.queue_free()

# ---- Stonegaze ------------------------------------------------------------------------------------------------------

func start_gaze(a: Dictionary) -> void:
	if not e.alive:
		return
	_gaze = {"a": a, "left": float(a.get("duration", 2.6)), "tick": 0.25}
	if e.visual:
		e.visual.hold_action(StringName(a.get("hold_anim", &"basilisk_gaze")))
	var tl := VFXLib.telegraph("cone", Vector2(GAZE_RANGE, GAZE_RANGE), float(_gaze.left), Color(0.8, 1.0, 0.4, 0.45), GAZE_ARC)
	FX.spawn(tl, e.global_position)
	tl.rotation.y = e.rotation.y + PI
	tl.get_tree().create_timer(float(_gaze.left) + 0.05, false).timeout.connect(tl.queue_free)
	if e.target and is_instance_valid(e.target):
		FX.text_popup(e.target.center() + Vector3.UP, "Look away!", Color(0.85, 1.0, 0.5), 1.1)

func _gaze_step(delta: float) -> void:
	_gaze.left -= delta
	_gaze.tick -= delta
	if _gaze.tick <= 0.0:
		_gaze.tick = 0.25
		for h in _gaze_targets():
			petrify_buildup(h, GAZE_BUILD)
	if _gaze.left <= 0.0 or not e.alive:
		_gaze = {}
		if e.visual and e.alive:
			e.visual.stop_action()

## Heroes and Tempos in the cone, in sight, and facing the basilisk.
func _gaze_targets() -> Array:
	var out := []
	if not e.is_inside_tree():
		return out
	for a: Actor in CombatQuery.actors_in_arc(e.get_world_3d(), e.global_position, e.forward(), GAZE_RANGE, GAZE_ARC, BH.LAYER_PLAYER):
		if not a.alive or CombatQuery.blocked(e.get_world_3d(), e.center(), a.center()):
			continue
		var to_b := (e.global_position - a.global_position).slide(Vector3.UP)
		if to_b.length() > 0.1 and a.forward().dot(to_b.normalized()) > 0.2:
			out.append(a)
	return out

func petrify_buildup(t: Actor, amt: float) -> bool:
	if t == null or not t.alive or t.status.has(&"petrified"):
		return false
	var b := float(t.get_meta(&"petrify", 0.0)) + amt
	if b >= StatusRules.THRESHOLD:
		t.set_meta(&"petrify", 0.0)
		t.status.apply(&"petrified", 2.0)
		FX.text_popup(t.center() + Vector3.UP, "Petrified!", Color(0.75, 0.75, 0.7), 1.2)
		return true
	t.set_meta(&"petrify", b)
	return false

# ---- Phase shift ----------------------------------------------------------------------------------------------------

func set_ethereal(on: bool) -> void:
	ethereal = on
	if on:
		e.status.apply(&"ethereal", 0.0)
	else:
		e.status.remove(&"ethereal")
	if e.visual:
		e.visual.set_opacity(0.38 if on else 1.0)
	FX.text_popup(e.center() + Vector3.UP, "Ethereal: use elements!" if on else "Tangible", Color(0.7, 0.8, 1.0), 0.9)

# ---- Curl -----------------------------------------------------------------------------------------------------------

func set_curled(on: bool) -> void:
	curled = on
	if on:
		e.status.apply(&"curled", 0.0)
	else:
		e.status.remove(&"curled")

## A poise break while rolling flips it onto its back, belly exposed.
func flip() -> void:
	set_curled(false)
	e._interrupt()
	_flipped_t = 3.0
	e.status.apply(&"stagger_window", 4.0)
	if e.visual:
		e.visual.hold_action(&"shell_flipped")
	FX.text_popup(e.center() + Vector3.UP, "Flipped! Belly exposed", Color(1.0, 0.85, 0.4), 1.1)

# ---- Mirror guard ---------------------------------------------------------------------------------------------------

func _try_mirror(ab: Dictionary) -> bool:
	if not e.brain.is_engaged() or e._dist > 9.0:
		return false
	e.cooldowns[ab.id] = float(ab.cooldown)
	e.status.apply(&"mirror_guard", float(ab.get("duration", 3.0)))
	if e.visual:
		e.visual.set_upper(&"block_loop")
		later(float(ab.get("duration", 3.0)), func() -> void:
			if e.alive and e.visual:
				e.visual.set_upper(&""))
	FX.spawn(VFXLib.light_flash(Color(0.85, 0.95, 1.0), 3.0, 5.0, 0.3), e.center() + e.forward() * 0.6)
	FX.text_popup(e.center() + Vector3.UP, "Mirror Guard", Color(0.85, 0.95, 1.0), 0.9)
	return true

# ---- Prism beam -----------------------------------------------------------------------------------------------------

func start_beam(a: Dictionary) -> void:
	var t := e.target
	if not e.alive or t == null or not is_instance_valid(t):
		return
	var to := (t.global_position - e.global_position).slide(Vector3.UP).normalized()
	var sweep := deg_to_rad(float(a.get("sweep", 100.0)))
	var dir := 1.0 if randf() < 0.5 else -1.0
	_beam = {"a": a, "left": float(a.get("duration", 3.0)), "total": float(a.get("duration", 3.0)), "tick": 0.0,
		"from": to.rotated(Vector3.UP, -sweep * 0.5 * dir), "sweep": sweep * dir, "hit": {}}
	_beam["mesh"] = _beam_mesh(Color(1.0, 0.5, 0.9), 0.14)
	if e.visual:
		e.visual.hold_action(StringName(a.get("hold_anim", &"cast_channel")))

func beam_dir() -> Vector3:
	if _beam.is_empty():
		return e.forward()
	var k := 1.0 - float(_beam.left) / float(_beam.total)
	return (_beam.from as Vector3).rotated(Vector3.UP, float(_beam.sweep) * k)

func _beam_step(delta: float) -> void:
	_beam.left -= delta
	var a: Dictionary = _beam.a
	var length := float(a.get("range", 14.0))
	var dir := beam_dir()
	e.rotation.y = atan2(dir.x, dir.z)
	var from := e.center() + dir * 0.6
	var to := from + dir * length
	if e.is_inside_tree():
		var hit := e.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from, to, BH.LAYER_WORLD))
		if not hit.is_empty():
			to = hit.position
	_place_beam(_beam.get("mesh"), from, to)
	_beam.tick -= delta
	if _beam.tick <= 0.0:
		_beam.tick = 0.2
		for x in e.get_tree().get_nodes_in_group(&"player") + e.get_tree().get_nodes_in_group(&"tempo") + e.get_tree().get_nodes_in_group(&"net_hero"):
			var t := x as Actor
			if t == null or not t.alive:
				continue
			var d := _seg_dist(t.global_position + Vector3.UP * 0.9, from, to)
			var id := t.get_instance_id()
			if d < 0.7 + t.body_radius and float((_beam.hit as Dictionary).get(id, -1.0)) < 0.0:
				(_beam.hit as Dictionary)[id] = 0.5
				var req := e._attack_request(a)
				req.evadable = true
				t.receive_hit(req, e, t.center())
		for k in (_beam.hit as Dictionary).keys():
			_beam.hit[k] = float(_beam.hit[k]) - 0.2
			if float(_beam.hit[k]) <= 0.0:
				(_beam.hit as Dictionary).erase(k)
	if _beam.left <= 0.0 or not e.alive:
		_end_beam()

func _end_beam() -> void:
	if not _beam.is_empty():
		var m = _beam.get("mesh")
		if m and is_instance_valid(m):
			m.queue_free()
		if e.visual and e.alive:
			e.visual.stop_action()
	_beam = {}

static func _seg_dist(p: Vector3, a: Vector3, b: Vector3) -> float:
	var ab := b - a
	var t := clampf((p - a).dot(ab) / maxf(ab.length_squared(), 0.0001), 0.0, 1.0)
	return p.distance_to(a + ab * t)

# ---- Beams (tether, link, prism) ------------------------------------------------------------------------------------

func _beam_mesh(c: Color, radius: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cy := CylinderMesh.new()
	cy.top_radius = radius
	cy.bottom_radius = radius
	cy.height = 1.0
	cy.radial_segments = 8
	cy.rings = 1
	mi.mesh = cy
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = c
	mat.emission_enabled = true
	mat.emission = c
	mat.emission_energy_multiplier = 3.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color.a = 0.85
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if FX.world:
		FX.world.add_child(mi)
	return mi

func _place_beam(mi: MeshInstance3D, a: Vector3, b: Vector3) -> void:
	if mi == null or not is_instance_valid(mi) or not mi.is_inside_tree():
		return
	var d := b - a
	var l := d.length()
	if l < 0.05:
		return
	var up := d / l
	var side := up.cross(Vector3.FORWARD if absf(up.dot(Vector3.FORWARD)) < 0.9 else Vector3.RIGHT).normalized()
	var fwd := side.cross(up).normalized()
	mi.global_transform = Transform3D(Basis(side, up * l, fwd), a + d * 0.5)
