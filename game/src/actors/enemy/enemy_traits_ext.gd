extends RefCounted
## Signature mechanics of the bh-010 monsters, one helper per enemy that has any (Enemy.ext). Enemy calls in at fixed
## points: setup (end of _ready), pre_tick (may take over the frame: a dormant Mimic, a War Totem), tick (every frame
## while alive), think (combat decisions; the lit powder keg), try_ability (raise / summon / totem / ward), on_hit,
## on_death, stat_mods / post_stats (stat rebuilds) and attack_element (the Rune Golem's attacks follow its core).
##
## Everything that waits is counted down here in tick() (not with SceneTree timers), so a manual step loop in the tests
## drives it exactly like the game does. Visual-only effects may still use timers.
##
##   raise_dead      Necromancer: turns a fresh humanoid corpse into a Risen (a weaker Hollow Soldier), capped per caster
##   summon          Goblin Summoner / Broodmother: a telegraphed burrow or egg clutch, then minions (capped)
##   totem           War Totem: stationary; pulses Empowered onto nearby monsters every PULSE seconds until destroyed
##   chill_aura      Frost Revenant: Chills heroes within AURA_RADIUS every second
##   shatter_death   Frost Revenant: a telegraphed ice burst where it fell
##   death_burst     Plague Bloater: swells (warning) below 35% HP; on death a telegraphed blast and a toxic cloud that
##                   hurts heroes AND monsters
##   powder_keg      Bandit Bombardier: below 30% HP lights its keg, charges, explodes on contact or when the fuse ends
##   troll_regen     Mire Troll: regenerates unless it took Fire damage in the last FIRE_BLOCK seconds
##   rune_shift      Rune Golem: the core cycles Fire -> Ice -> Lightning; immune to it, weak to its opposite
##   mimic           Mimic: a chest until a hero comes within WAKE_RANGE or hits it
##   brood           Broodmother (summon ability with spiderlings)

const NEW_TRAITS := [&"raise_dead", &"chill_aura", &"shatter_death", &"death_burst", &"powder_keg", &"troll_regen",
	&"rune_shift", &"mimic", &"totem", &"brood", &"spore_pop"]
const NEW_ABILITIES := ["raise", "summon", "totem", "ward"]
const NEW_ATTACKS := ["chain", "tongue"]

const GLOBAL_MINION_CAP := 18         # all summoned/raised monsters alive at once, whoever made them
const AURA_RADIUS := 4.0
const AURA_INTERVAL := 1.0
const TOTEM_RADIUS := 8.0
const PULSE := 3.0
const SWELL_AT := 0.35
const KEG_AT := 0.3
const KEG_FUSE := 4.0
const KEG_RADIUS := 3.4
const TROLL_REGEN := 0.02             # of max HP per second
const FIRE_BLOCK := 4.0
const RUNE_PERIOD := 8.0
const RUNE_WARN := 1.4
const RUNE_CYCLE: Array[int] = [Elements.FIRE, Elements.ICE, Elements.LIGHTNING]
const RUNE_OPPOSITE := {Elements.FIRE: Elements.ICE, Elements.ICE: Elements.FIRE, Elements.LIGHTNING: Elements.EARTH}
const RUNE_WEAKNESS := 0.5            # resistance lost to the opposite element
const WAKE_RANGE := 3.5
const RISEN_HP := 0.6                 # Risen are weaker than a fresh Hollow Soldier
const RISEN_DAMAGE := 0.7

var e: Enemy
var jobs: Array = []                  # [[seconds_left, Callable]]
var minions: Array = []               # monsters this one raised / summoned / planted
var dormant := false
var swollen := false
var fuse_lit := false
var fuse_t := 0.0
var exploded := false
var regen_block := 0.0
var rune_idx := 0
var rune_t := 0.0
var _rune_warned := false
var _aura_t := 0.0
var _pulse_t := PULSE - 1.0
var _wake_t := 0.0
var _emissive: Array = []             # [[MeshInstance3D, surface]] of BH_Emissive surfaces
var _rune_light: OmniLight3D
var _keg_ring: Node3D
var raise_cap := 3
var totem_cap := 1

static func wants(d: EnemyDef) -> bool:
	for t in d.traits:
		if NEW_TRAITS.has(t):
			return true
	for ab in d.abilities:
		if NEW_ABILITIES.has(String(ab.get("kind", ""))):
			return true
	for a in d.attacks:
		if NEW_ATTACKS.has(String(a.get("kind", ""))) or a.get("rune", false) or a.has("fuse") or a.has("on_hit_status"):
			return true
	return false

func _init(owner: Enemy) -> void:
	e = owner

func has(t: StringName) -> bool:
	return e.def.traits.has(t)

# ---- Lifecycle ------------------------------------------------------------------------------------------------

func setup() -> void:
	for ab in e.def.abilities:
		if String(ab.get("kind", "")) == "raise":
			raise_cap = int(ab.get("cap", 3))
		elif String(ab.get("kind", "")) == "totem":
			totem_cap = int(ab.get("cap", 1))
	if has(&"mimic"):
		dormant = true
		e.remove_from_group(&"enemy")          # not a target, not on the minimap, not counted as a threat
		if e.visual:
			e.visual.hold_action(&"mimic_dormant")
		_settle_as_chest.call_deferred()
	if has(&"totem") and e.visual:
		e.visual.play_action(&"alert")         # planting
		var glow := VFXLib.particles(Color(1.0, 0.35, 0.2, 0.7), 10, 1.2, false, 0.25, 0.6, 30.0, Vector3(0, 1.0, 0), 0.25)
		glow.position.y = 1.6
		e.add_child(glow)
	if has(&"chill_aura"):
		var mist := VFXLib.particles(Color(0.7, 0.9, 1.0, 0.45), 18, 1.6, false, 0.6, 0.5, 60.0, Vector3(0, 0.3, 0), AURA_RADIUS * 0.6, false)
		mist.position.y = 0.2
		e.add_child(mist)
	if has(&"troll_regen"):
		e.status.apply(&"troll_regen", 0.0)
	if has(&"rune_shift"):
		_find_emissive()
		_apply_rune()

## A Mimic sits square to the room like the real chests do, and never counts as a camp until it wakes (a hidden
## ambusher must not hold up a stage clear).
func _settle_as_chest() -> void:
	if not is_instance_valid(e) or not dormant:
		return
	e.rotation.y = snappedf(e.rotation.y, PI * 0.5)
	var sp := Spawner.current()
	if sp == null:
		return
	for k in sp.camps.keys():
		var list: Array = sp.camps[k]
		if list.has(e):
			list.erase(e)
			if list.is_empty():
				sp.camps.erase(k)

## Returns true when the normal AI must not run this frame (the caller only applies gravity).
func pre_tick(delta: float) -> bool:
	if dormant:
		_wake_t -= delta
		if _wake_t <= 0.0:
			_wake_t = 0.1
			var h := _hero_near(WAKE_RANGE)
			if h:
				wake(h)
		return dormant
	if has(&"totem"):
		_run_jobs(delta)
		e.knock_velocity = Vector3.ZERO
		_pulse_t += delta
		if _pulse_t >= PULSE:
			_pulse_t = 0.0
			pulse()
		return true
	return false

func tick(delta: float) -> void:
	_run_jobs(delta)
	if has(&"chill_aura"):
		_aura_t -= delta
		if _aura_t <= 0.0:
			_aura_t = AURA_INTERVAL
			chill_pulse()
	if has(&"death_burst") and not swollen and e.hp < e.max_hp() * SWELL_AT:
		swell()
	if has(&"powder_keg"):
		if not fuse_lit and e.hp > 0.0 and e.hp < e.max_hp() * KEG_AT:
			light_fuse()
		elif fuse_lit and not exploded:
			fuse_t -= delta
			var t := e.target
			var touching: bool = t != null and is_instance_valid(t) and t.alive \
				and t.global_position.distance_to(e.global_position) < e.body_radius + t.body_radius + 0.7
			if fuse_t <= 0.0 or touching:
				explode()
	if has(&"troll_regen"):
		if regen_block > 0.0:
			regen_block -= delta
			if regen_block <= 0.0:
				e.status.apply(&"troll_regen", 0.0)
				FX.text_popup(e.center() + Vector3.UP, "Regenerating", Color(0.5, 1.0, 0.5), 0.9)
		elif e.hp < e.max_hp() and not e.status.has(&"purged"):
			e.heal(e.max_hp() * TROLL_REGEN * delta, false)
	if has(&"rune_shift") and e.brain.is_engaged():
		rune_t += delta
		if not _rune_warned and rune_t >= RUNE_PERIOD - RUNE_WARN:
			_rune_warned = true
			_rune_warning()
		if rune_t >= RUNE_PERIOD:
			shift_rune()

func _run_jobs(delta: float) -> void:
	if jobs.is_empty():
		return
	var due: Array = []
	for j in jobs:
		j[0] -= delta
		if j[0] <= 0.0:
			due.append(j)
	for j in due:
		jobs.erase(j)
		(j[1] as Callable).call()

func later(seconds: float, fn: Callable) -> void:
	jobs.append([seconds, fn])

## Combat decisions that replace the normal ones. Returns true when it handled this think.
func think() -> bool:
	if fuse_lit and not exploded:
		var t := e.target
		if t and is_instance_valid(t) and t.alive:
			e.brain.go(EnemyBrain.State.CHASE)
			e._move_target = t.global_position
		return true
	return false

func on_hit(result: DamageResult, _req: DamageRequest, attacker: Node) -> void:
	if dormant:
		wake(attacker as Node3D)
	if has(&"troll_regen") and float(result.components.get(Elements.FIRE, 0.0)) > 0.0:
		if regen_block <= 0.0:
			e.status.remove(&"troll_regen")
			FX.text_popup(e.center() + Vector3.UP * 1.2, "Burned! No regeneration", Color(1.0, 0.55, 0.2), 1.0)
			FX.spawn(VFXLib.particles(Color(0.2, 0.2, 0.2, 0.7), 16, 1.2, true, 0.6, 1.2, 60.0, Vector3(0, 1.2, 0), 0.5, false), e.center())
		regen_block = FIRE_BLOCK

func on_death(killer: Node) -> void:
	if has(&"shatter_death"):
		_shatter()
	if has(&"death_burst"):
		_burst()
	if has(&"spore_pop"):
		_spore_pop()
	if has(&"powder_keg") and fuse_lit and not exploded:
		exploded = true
		var at := e.global_position
		var req := _req(2.0, Elements.FIRE, 0.6, 12.0, "Powder keg")
		var b := AreaEffects.delayed(FX.world, at, KEG_RADIUS, 0.35, req, null, BH.LAYER_PLAYER | BH.LAYER_ENEMY, Color(1.0, 0.45, 0.1, 0.8))
		b.on_blast = func(pos: Vector3, _h: Array) -> void: _boom_fx(pos)
	if has(&"mimic"):
		_mimic_loot(killer)
	# minions outlive their maker: a planted War Totem keeps pulsing until it is smashed

# ---- Stats ------------------------------------------------------------------------------------------------------

func stat_mods(mods: Array) -> void:
	if has(&"rune_shift"):
		mods.append(StatModifier.flat(Elements.res_key(RUNE_OPPOSITE[rune_element()]), -RUNE_WEAKNESS, "Rune Shift"))
	if fuse_lit and not exploded:
		mods.append(StatModifier.more(&"move_speed", 0.6, "Lit fuse"))

func post_stats(st: DerivedStats) -> void:
	if has(&"rune_shift"):
		st.immune[rune_element()] = true

func rune_element() -> int:
	return RUNE_CYCLE[rune_idx % RUNE_CYCLE.size()]

## The element of an attack: the Rune Golem's follow its core; everything else uses the data.
func attack_element(a: Dictionary) -> int:
	if a.get("rune", false) and has(&"rune_shift"):
		return rune_element()
	return int(a.get("element", Elements.PHYSICAL))

## A short line under the health bar ("Immune: Fire", "Regeneration stopped", "Lit fuse!"), or "".
func bar_note() -> Array:
	if has(&"rune_shift"):
		return ["Rune: %s (immune)" % Elements.NAMES[rune_element()], Elements.color(rune_element())]
	if has(&"troll_regen") and regen_block > 0.0:
		return ["Burned: no regeneration", Color(1.0, 0.55, 0.2)]
	if fuse_lit and not exploded:
		return ["Lit fuse! %.1f" % maxf(0.0, fuse_t), Color(1.0, 0.4, 0.15)]
	if swollen:
		return ["Swelling!", Color(0.6, 1.0, 0.3)]
	return []

# ---- Minions ------------------------------------------------------------------------------------------------------

func alive_minions(id := &"") -> int:
	var keep: Array = []
	for m in minions:
		if is_instance_valid(m) and (m as Enemy).alive:
			keep.append(m)
	minions = keep
	if id == &"":
		return minions.size()
	return minions.filter(func(m): return (m as Enemy).def.id == id).size()

static func global_minions(tree: SceneTree) -> int:
	var n := 0
	for m in tree.get_nodes_in_group(&"bh_minion"):
		if (m as Enemy).alive:
			n += 1
	return n

func spawn_minion(def_id: StringName, at: Vector3, is_risen := false) -> Enemy:
	var d := DB.enemy(def_id)
	var parent := e.get_parent()
	if d == null or parent == null or not e.is_inside_tree():
		return null
	var m := Enemy.new()
	m.setup(d, maxi(1, e.level - (2 if is_risen else 1)), [], e.difficulty)
	m.risen = is_risen
	if is_risen:
		m.display_name = "Risen"
	m.summoner = e
	m.name = "Minion_%s_%d" % [def_id, m.get_instance_id()]
	parent.add_child(m)
	m.global_position = at + Vector3.UP * 0.1
	m.home = at
	m.patrol_radius = 0.0 if def_id == &"war_totem" else 2.0
	m.add_to_group(&"bh_minion")
	minions.append(m)
	if def_id != &"war_totem" and e.target and is_instance_valid(e.target):
		m.alert_to(e.target.global_position)
	return m

func _can_add(cap: int, id := &"") -> bool:
	return alive_minions(id) < cap and global_minions(e.get_tree()) < GLOBAL_MINION_CAP

# ---- Abilities ---------------------------------------------------------------------------------------------------

func try_ability(ab: Dictionary) -> bool:
	match String(ab.kind):
		"raise":
			return _try_raise(ab)
		"summon":
			return _try_summon(ab)
		"totem":
			return _try_totem(ab)
		"ward":
			return _try_ward(ab)
	return false

func _cast(ab: Dictionary, effect: Callable) -> float:
	if not e._cast_ability(ab, effect):
		return -1.0
	var act := e.action
	return act.release_t if act and act.release_t >= 0.0 else 0.6

## Necromancer: a fresh humanoid body nearby (not a boss, not already Risen) gets up again.
func _try_raise(ab: Dictionary) -> bool:
	if not _can_add(int(ab.get("cap", 3)), &"hollow_soldier"):
		return false
	var corpse := fresh_corpse(float(ab.get("range", 12.0)))
	if corpse == null:
		return false
	var t := _cast(ab, func() -> void: raise(corpse))
	if t < 0.0:
		return false
	corpse.set_meta(&"raising", true)
	_tele("ring", 1.1, t, Color(0.45, 1.0, 0.6, 0.8), corpse.global_position)
	var wisps := VFXLib.particles(Color(0.45, 1.0, 0.6, 0.8), 18, 0.9, false, 0.18, 1.6, 30.0, Vector3(0, 1.5, 0), 0.6)
	FX.spawn(wisps, corpse.global_position + Vector3.UP * 0.2)
	if is_instance_valid(wisps):
		wisps.get_tree().create_timer(t + 0.3, false).timeout.connect(wisps.queue_free)
	return true

func fresh_corpse(radius: float) -> Enemy:
	var best: Enemy = null
	var bd := radius * radius
	for c in e.get_tree().get_nodes_in_group(&"corpse"):
		var ce := c as Enemy
		if ce == null or not ce.is_fresh_corpse() or ce.is_boss or ce.is_miniboss() or ce.has_meta(&"raising"):
			continue
		if ce.def.body_shape != &"humanoid":
			continue
		var d := ce.global_position.distance_squared_to(e.global_position)
		if d < bd:
			bd = d
			best = ce
	return best

## The raise itself (also called directly by the tests): the body dissolves and a Risen stands up in its place.
func raise(corpse: Enemy) -> Enemy:
	if not e.alive or corpse == null or not is_instance_valid(corpse) or not corpse.is_fresh_corpse():
		return null
	if not _can_add(raise_cap, &"hollow_soldier"):
		return null
	var at := corpse.global_position
	corpse._dissolve(0.5)
	var m := spawn_minion(&"hollow_soldier", at, true)
	if m == null:
		return null
	if m.visual:
		m.visual.play_action(&"revive")
	FX.spawn(VFXLib.particles(Color(0.45, 1.0, 0.6, 0.9), 30, 1.0, true, 0.2, 2.5, 180.0, Vector3(0, 1.5, 0), 0.5), at + Vector3.UP)
	FX.text_popup(at + Vector3.UP * 2.0, "Risen!", Color(0.5, 1.0, 0.65), 1.0)
	Audio.play_at(&"skeleton_rattle", at, 2.0)
	return m

## Goblin burrow / spider eggs: a marked spot smokes (or pulses) for `delay` seconds, then the minions come out.
func _try_summon(ab: Dictionary) -> bool:
	var id := StringName(ab.get("summon", &"goblin_skulker"))
	var cap := int(ab.get("cap", 3))
	if not _can_add(cap, id) or e.target == null:
		return false
	var spot := _summon_spot(2.6)
	if _cast(ab, Callable()) < 0.0:
		return false
	summon_at(spot, id, mini(int(ab.get("count", 2)), cap - alive_minions(id)), float(ab.get("delay", 1.2)), String(ab.get("fx", "burrow")), cap)
	return true

## The cap is checked again when the minions come out (another summon may have landed during the telegraph).
func summon_at(spot: Vector3, id: StringName, n: int, delay: float, fx := "burrow", cap := 99) -> void:
	var c := Color(0.45, 0.38, 0.3, 0.8) if fx == "burrow" else Color(0.9, 0.9, 0.8, 0.8)
	_tele("circle", 1.3, delay, Color(1.0, 0.45, 0.15, 0.7), spot)
	var smoke := VFXLib.particles(c, 22, 1.4, false, 0.7 if fx == "burrow" else 0.25, 1.1, 40.0, Vector3(0, 0.8, 0), 0.9, false)
	FX.spawn(smoke, spot + Vector3.UP * 0.1)
	if is_instance_valid(smoke) and smoke.is_inside_tree():
		smoke.get_tree().create_timer(delay + 0.4, false).timeout.connect(smoke.queue_free)
	Audio.play_at(&"earth_quake" if fx == "burrow" else &"shade_hiss", spot, -6.0)
	later(delay, func() -> void:
		if not e.alive:
			return
		var room := mini(cap - alive_minions(id), GLOBAL_MINION_CAP - global_minions(e.get_tree()))
		for i in mini(n, room):
			var ang := TAU * float(i) / float(maxi(n, 1))
			var p := spot + Vector3(cos(ang), 0, sin(ang)) * 0.9
			if e.is_inside_tree():
				p = CombatQuery.reachable_point(e.get_world_3d(), spot, p, 0.3)
			spawn_minion(id, p)
		FX.spawn(VFXLib.dust_puff(1.2), spot)
		if fx == "burrow":
			FX.spawn(VFXLib.debris(0.8, Color(0.4, 0.32, 0.22)), spot))

## Orc Shaman: plants a War Totem a couple of metres to its side.
func _try_totem(ab: Dictionary) -> bool:
	if not _can_add(int(ab.get("cap", 1)), &"war_totem") or e.target == null:
		return false
	var spot := _summon_spot(2.2, 1.6)
	var t := _cast(ab, func() -> void: plant_totem(spot))
	if t < 0.0:
		return false
	_tele("circle", 1.0, t, Color(1.0, 0.4, 0.2, 0.7), spot)
	return true

func plant_totem(spot: Vector3) -> Enemy:
	if not e.alive or not _can_add(totem_cap, &"war_totem"):
		return null
	var m := spawn_minion(&"war_totem", spot)
	if m:
		FX.spawn(VFXLib.dust_puff(1.0), spot)
		Audio.play_at(&"earth_quake", spot, -4.0)
	return m

## Necromancer: a ward of bones on the most hurt monster nearby (or itself).
func _try_ward(ab: Dictionary) -> bool:
	var best: Enemy = null
	var worst := 2.0
	for x in e.get_tree().get_nodes_in_group(&"enemy"):
		var o := x as Enemy
		if o == null or not o.alive or o.status.has(&"bone_ward") or o.def.id == &"war_totem":
			continue
		if o != e and (not o.brain.is_engaged() or o.global_position.distance_to(e.global_position) > float(ab.get("range", 12.0))):
			continue
		var f := o.hp / maxf(1.0, o.max_hp()) + (0.15 if o == e else 0.0)
		if f < worst:
			worst = f
			best = o
	if best == null or not e.brain.is_engaged():
		return false
	var who := best
	var fn := func() -> void:
		if is_instance_valid(who) and who.alive:
			who.apply_bone_ward(who.max_hp() * float(ab.get("amount", 0.3)), float(ab.get("duration", 8.0)))
	return _cast(ab, fn) >= 0.0

func _summon_spot(dist: float, side := 0.0) -> Vector3:
	var to := Vector3.FORWARD
	if e.target and is_instance_valid(e.target):
		to = (e.target.global_position - e.global_position).slide(Vector3.UP)
	if to.length() < 0.1:
		to = e.forward()
	to = to.normalized()
	var p := e.global_position + to * dist + to.cross(Vector3.UP) * side
	if e.is_inside_tree():
		p = CombatQuery.reachable_point(e.get_world_3d(), e.global_position, p, 0.4)
		p = CombatQuery.ground_at(e.get_world_3d(), p)
	return p

# ---- War Totem ----------------------------------------------------------------------------------------------------

func pulse() -> int:
	var n := 0
	if not e.alive or not e.is_inside_tree():
		return 0
	for x in e.get_tree().get_nodes_in_group(&"enemy"):
		var o := x as Enemy
		if o == null or o == e or not o.alive or o.def.id == &"war_totem":
			continue
		if o.global_position.distance_to(e.global_position) <= TOTEM_RADIUS:
			o.status.apply(&"empowered", PULSE + 0.5)
			n += 1
	if e.visual:
		e.visual.play_action(&"totem_pulse")
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.35, 0.2, 0.8), TOTEM_RADIUS, 0.6, 0.3), e.global_position)
	return n

# ---- Frost Revenant -----------------------------------------------------------------------------------------------

func chill_pulse() -> int:
	if not e.is_inside_tree():
		return 0
	var n := 0
	for a: Actor in CombatQuery.actors_in_radius(e.get_world_3d(), e.global_position, AURA_RADIUS, BH.LAYER_PLAYER):
		if not a.alive:
			continue
		a.status.apply(&"chilled", AURA_INTERVAL + 0.6, StatusController.CHILL_SLOW, 0.0, Elements.ICE,
			[StatModifier.more(&"move_speed", -StatusController.CHILL_SLOW), StatModifier.more(&"attack_speed", -StatusController.CHILL_SLOW)])
		n += 1
	return n

func _shatter() -> void:
	var req := _req(1.2, Elements.ICE, 1.0, 6.0, "Shatter")
	req.direct_status[&"chilled"] = 80.0
	var b := AreaEffects.delayed(FX.world, e.global_position, 3.4, 1.1, req, null, BH.LAYER_PLAYER, Color(0.55, 0.9, 1.0, 0.8))
	b.on_blast = func(pos: Vector3, _h: Array) -> void:
		FX.spawn(VFXLib.ring_wave(Color(0.6, 0.92, 1.0), 3.4, 0.4), pos)
		FX.spawn(VFXLib.debris(1.2, Color(0.7, 0.9, 1.0)), pos + Vector3.UP * 0.6)
		FX.spawn(VFXLib.particles(Color(0.75, 0.95, 1.0, 1.0), 40, 0.6, true, 0.16, 7.0, 180.0, Vector3(0, -6, 0), 0.4), pos + Vector3.UP)
		Audio.play_at(&"shatter_ice", pos)
		Events.camera_shake.emit(0.2)

# ---- Plague Bloater -----------------------------------------------------------------------------------------------

func swell() -> void:
	swollen = true
	if e.visual:
		e.visual.set_rim(Color(0.55, 1.0, 0.2), 1.2)
		e.visual.play_action(&"boss_roar")
	var bubbles := VFXLib.particles(Color(0.55, 0.9, 0.2, 0.8), 20, 1.0, false, 0.22, 1.0, 60.0, Vector3(0, 1.0, 0), 0.7)
	bubbles.position.y = e.body_height * 0.5
	e.add_child(bubbles)
	FX.text_popup(e.center() + Vector3.UP * 1.3, "Swelling!", Color(0.6, 1.0, 0.3), 1.2)
	Audio.play_at(&"ghoul_growl", e.global_position, 2.0)

const BURST_RADIUS := 4.2
const BURST_DELAY := 1.4
const CLOUD_RADIUS := 3.6
const CLOUD_TIME := 6.0

## The corpse bulges for a moment (a green circle fills), then bursts: a blast and a toxic cloud that poisons everyone
## standing in it, monsters included.
func _burst() -> void:
	var at := e.global_position
	var mask := BH.LAYER_PLAYER | BH.LAYER_ENEMY
	var blast := _req(1.4, Elements.PHYSICAL, 0.0, 7.0, "Bloater burst")
	blast.direct_status[&"poisoned"] = 100.0
	var cloud := _req(0.3, Elements.PHYSICAL, 0.0, 0.0, "Toxic cloud")
	cloud.direct_status[&"poisoned"] = 45.0
	var b := AreaEffects.delayed(FX.world, at, BURST_RADIUS, BURST_DELAY, blast, null, mask, Color(0.5, 0.95, 0.15, 0.8))
	b.on_blast = func(pos: Vector3, _h: Array) -> void:
		FX.spawn(VFXLib.ring_wave(Color(0.55, 0.95, 0.2), BURST_RADIUS, 0.45), pos)
		FX.spawn(VFXLib.particles(Color(0.45, 0.75, 0.15, 0.9), 40, 1.2, true, 0.5, 5.0, 180.0, Vector3(0, -2, 0), 0.6, false), pos + Vector3.UP)
		AreaEffects.hazard(FX.world, pos, CLOUD_RADIUS, CLOUD_TIME, cloud, null, mask, Color(0.45, 0.8, 0.15))
		Audio.play_at(&"explode", pos, -2.0)
		Events.camera_shake.emit(0.25)
	if e.visual:
		e.visual.set_rim(Color(0.55, 1.0, 0.2), 2.0)

## Sporeling (bh-012): a small puff of spores where it falls — poisons whoever stands in it, monsters included.
func _spore_pop() -> void:
	var at := e.global_position
	var mask := BH.LAYER_PLAYER | BH.LAYER_ENEMY
	var puff := _req(0.5, Elements.PHYSICAL, 0.0, 2.0, "Spore puff")
	puff.direct_status[&"poisoned"] = 55.0
	var b := AreaEffects.delayed(FX.world, at, 2.4, 0.8, puff, null, mask, Color(0.75, 1.0, 0.3, 0.7))
	b.on_blast = func(pos: Vector3, _h: Array) -> void:
		FX.spawn(VFXLib.particles(Color(0.75, 1.0, 0.3, 0.8), 26, 1.0, true, 0.35, 3.0, 180.0, Vector3(0, -1.5, 0), 0.4, false), pos + Vector3.UP * 0.6)
		Audio.play_at(&"ghoul_growl", pos, -8.0)

# ---- Bandit Bombardier --------------------------------------------------------------------------------------------

func light_fuse() -> void:
	fuse_lit = true
	fuse_t = KEG_FUSE
	e.status.apply(&"lit_fuse", 0.0)
	e._interrupt()
	e.mark_stats_dirty()
	FX.text_popup(e.center() + Vector3.UP * 1.2, "Lit fuse!", Color(1.0, 0.45, 0.15), 1.2)
	Audio.play_at(&"cast_fire", e.global_position)
	var sparks := VFXLib.particles(Color(1.0, 0.7, 0.25, 1.0), 24, 0.35, false, 0.08, 3.0, 50.0, Vector3(0, -3, 0), 0.05)
	sparks.position = Vector3(0, e.body_height * 0.8, -0.3)
	e.add_child(sparks)
	_keg_ring = VFXLib.telegraph("circle", Vector2(KEG_RADIUS, KEG_RADIUS), KEG_FUSE, Color(1.0, 0.3, 0.1, 0.55))
	e.add_child(_keg_ring)

func explode() -> void:
	if exploded:
		return
	exploded = true
	var at := e.global_position
	if e.is_inside_tree():
		var req := _req(2.2, Elements.FIRE, 0.6, 12.0, "Powder keg")
		req.direct_status[&"burning"] = 60.0
		AreaEffects.burst(e, at, KEG_RADIUS, BH.LAYER_PLAYER | BH.LAYER_ENEMY, req, e, [e])
	_boom_fx(at)
	if is_instance_valid(_keg_ring):
		_keg_ring.queue_free()
	e.die(e)                                   # the keg takes its bearer with it

func _boom_fx(pos: Vector3) -> void:
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.55, 0.2), KEG_RADIUS, 0.4), pos)
	FX.spawn(VFXLib.light_flash(Color(1.0, 0.6, 0.3), 6.0, 8.0, 0.3), pos + Vector3.UP)
	FX.spawn(VFXLib.particles(Color(1.0, 0.5, 0.15, 1.0), 40, 0.6, true, 0.3, 7.0, 180.0, Vector3(0, -4, 0), 0.5), pos + Vector3.UP)
	Audio.play_at(&"explode", pos)
	Events.camera_shake.emit(0.35)

## A thrown bomb that lies on the ground, sparking, until its telegraph fills.
static func fuse_bomb_body() -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.2
	sph.height = 0.4
	mi.mesh = sph
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.12, 0.11, 0.1)
	m.roughness = 0.5
	m.metallic = 0.4
	mi.material_override = m
	root.add_child(mi)
	var sp := VFXLib.particles(Color(1.0, 0.75, 0.3, 1.0), 16, 0.3, false, 0.06, 2.2, 60.0, Vector3(0, -3, 0), 0.02)
	sp.position.y = 0.25
	root.add_child(sp)
	return root

# ---- Mire Troll / Rune Golem ------------------------------------------------------------------------------------

func shift_rune() -> void:
	rune_idx = (rune_idx + 1) % RUNE_CYCLE.size()
	rune_t = 0.0
	_rune_warned = false
	e.mark_stats_dirty()
	_apply_rune()
	var c := Elements.color(rune_element())
	FX.text_popup(e.center() + Vector3.UP * 1.4, "Immune: %s" % Elements.NAMES[rune_element()], c, 1.1)
	FX.spawn(VFXLib.ring_wave(c, 3.0, 0.5), e.global_position)
	Audio.play_at(&"arcane_surge", e.global_position, -3.0)

func _rune_warning() -> void:
	var nxt := RUNE_CYCLE[(rune_idx + 1) % RUNE_CYCLE.size()]
	var c := Elements.color(nxt)
	FX.text_popup(e.center() + Vector3.UP * 1.4, "Rune shifting...", c, 0.9)
	_tele("ring", 2.2, RUNE_WARN, Color(c.r, c.g, c.b, 0.7), e.global_position, e)
	if e.visual:
		e.visual.flash(c, 1.2, RUNE_WARN)

func _find_emissive() -> void:
	_emissive.clear()
	if e.visual == null:
		return
	for mi: MeshInstance3D in e.visual._meshes:
		if mi == null or mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var mat := mi.mesh.surface_get_material(i)
			if mat and mat.resource_name.get_slice(".", 0).get_slice("__", 0) == "BH_Emissive":
				_emissive.append([mi, i])

func _apply_rune() -> void:
	var el := rune_element()
	var c := Elements.color(el)
	e.status.apply(&"rune_immune", 0.0, float(el))
	for s in _emissive:
		var mi: MeshInstance3D = s[0]
		if not is_instance_valid(mi):
			continue
		var m := StandardMaterial3D.new()
		m.albedo_color = c.darkened(0.35)
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = 3.0
		mi.set_surface_override_material(int(s[1]), m)
	if e.visual and (_emissive.is_empty() or not e.is_elite):
		if not e.is_elite:
			e.visual.set_rim(c, 0.55 if _emissive.is_empty() else 0.25)
	if _rune_light == null:
		_rune_light = OmniLight3D.new()
		_rune_light.light_energy = 1.2
		_rune_light.omni_range = 3.5
		_rune_light.position.y = e.body_height * 0.6
		e.add_child(_rune_light)
	_rune_light.light_color = c

# ---- Mimic ----------------------------------------------------------------------------------------------------------

func _hero_near(r: float) -> Node3D:
	var heroes: Array = []
	if Game.player and is_instance_valid(Game.player):
		heroes.append(Game.player)
	heroes.append_array(e.get_tree().get_nodes_in_group(&"net_hero"))
	for h in heroes:
		var a := h as Actor
		if a and a.alive and a.global_position.distance_to(e.global_position) <= r:
			return a
	return null

func wake(by: Node3D = null) -> void:
	if not dormant:
		return
	dormant = false
	e.add_to_group(&"enemy")
	e.make_bar()
	if e.visual:
		e.visual.stop_action()
	var at := by.global_position if by and is_instance_valid(by) else e.global_position + e.forward() * 2.0
	e.alert_to(at)
	if e.visual:
		e.visual.play_action(&"mimic_wake")
	if by and is_instance_valid(by):
		e._face_now(by.global_position)
	FX.text_popup(e.center() + Vector3.UP * 1.0, "Mimic!", Color(1.0, 0.3, 0.25), 1.3)
	Audio.play_at(&"ghoul_growl", e.global_position, 3.0)
	Events.camera_shake.emit(0.2)

## The tongue: if it connects, the hero is dragged toward the Mimic's mouth.
func tongue(a: Dictionary) -> bool:
	var t := e.target
	if t == null or not is_instance_valid(t) or not t.alive or not e.is_inside_tree():
		return false
	var to := (t.global_position - e.global_position).slide(Vector3.UP)
	var reach := float(a.get("range", 7.0)) + 1.0
	if to.length() > reach or e.forward().angle_to(to.normalized()) > deg_to_rad(40.0):
		_tongue_fx(e.center() + e.forward() * reach * 0.8, a.get("tongue_color", Color(0.9, 0.35, 0.45)))
		return false
	if CombatQuery.blocked(e.get_world_3d(), e.center(), t.center()):
		return false
	_tongue_fx(t.center(), a.get("tongue_color", Color(0.9, 0.35, 0.45)))
	var res := t.receive_hit(e._attack_request(a), e, t.center())
	if res == null or res.evaded or not t.alive:
		return false
	if to.length() > 1.6:
		t.apply_knockback(-to.normalized(), float(a.get("pull", 11.0)), e.stats, e)
	return true

func _tongue_fx(to: Vector3, col := Color(0.9, 0.35, 0.45)) -> void:
	FX.spawn(VFXLib.lightning_bolt(e.center() + e.forward() * 0.5, to, col, 0.3, 0.14), Vector3.ZERO)

## Mimics pay well: an extra purse and one more item of Advanced quality or better.
func _mimic_loot(_killer: Node) -> void:
	if e.net_replica or Game.player == null or not is_instance_valid(Game.player) or Game.hero == null or FX.world == null:
		return
	var r := RandomNumberGenerator.new()
	r.seed = hash(e.get_instance_id()) ^ Time.get_ticks_usec()
	Loot.spawn_gold(e.global_position, 20 + 8 * e.level)
	var base := ItemGenerator.random_base(r, e.level + 1, [], Game.hero.cls.id)
	if base:
		var rarity := maxi(ItemGenerator.roll_rarity(r, 0.0, 0.6, e.level + 1), BH.Rarity.ADVANCED)
		Loot.spawn_item(ItemGenerator.generate(base, e.level + 1, rarity, r), e.global_position, r.randf() * TAU, 1.4)

# ---- Orc Shaman ---------------------------------------------------------------------------------------------------

## Chain lightning: strikes the target, then jumps to up to `jumps` more heroes / Tempos within `jump_range`.
func chain(a: Dictionary) -> int:
	var first := e.target
	if first == null or not is_instance_valid(first) or not first.alive or not e.is_inside_tree():
		return 0
	if first.global_position.distance_to(e.global_position) > float(a.get("range", 12.0)) + e.body_radius + 1.5:
		return 0
	if CombatQuery.blocked(e.get_world_3d(), e.center(), first.center()):
		return 0
	var hit: Array = [first]
	var from := e.center() + e.forward() * 0.5 + Vector3.UP * 0.3
	_zap(from, first, a, 1.0)
	var cur: Actor = first
	for j in int(a.get("jumps", 2)):
		var best: Actor = null
		var bd := float(a.get("jump_range", 6.0))
		for o: Actor in CombatQuery.actors_in_radius(e.get_world_3d(), cur.global_position, bd, BH.LAYER_PLAYER):
			if hit.has(o) or not o.alive:
				continue
			var d := o.global_position.distance_to(cur.global_position)
			if d < bd:
				bd = d
				best = o
		if best == null:
			break
		_zap(cur.center(), best, a, pow(0.7, j + 1))
		hit.append(best)
		cur = best
	Audio.play_at(&"lightning_zap", e.global_position)
	return hit.size()

func _zap(from: Vector3, to: Actor, a: Dictionary, mult: float) -> void:
	FX.spawn(VFXLib.lightning_bolt(from, to.center(), Color(1.0, 0.95, 0.5), 0.22, 0.12), Vector3.ZERO)
	var req := e._attack_request(a)
	req.base_min *= mult
	req.base_max *= mult
	to.receive_hit(req, e, to.center())

# ---- helpers --------------------------------------------------------------------------------------------------------

func _req(mult: float, element: int, conv: float, knock: float, label: String) -> DamageRequest:
	var req := DamageRequest.new()
	req.kind = DamageRequest.Kind.SPELL
	req.attacker = e.stats
	var rr := EnemyStats.attack_range(e.def, e.stats, mult)
	req.base_min = rr.x
	req.base_max = rr.y
	if element != Elements.PHYSICAL and conv > 0.0:
		req.conversion = {element: conv}
	req.knockback = knock
	req.graze = true          # bh-028: trait blasts can be grazed like any area hit
	req.label = label
	return req

func _tele(shape: String, radius: float, t: float, c: Color, at: Vector3, parent: Node3D = null) -> void:
	var tl := VFXLib.telegraph(shape, Vector2(radius, radius), maxf(t, 0.05), c, 360.0, radius * 0.75 if shape == "ring" else 0.0)
	if parent and is_instance_valid(parent):
		parent.add_child(tl)
	else:
		FX.spawn(tl, at)
	if is_instance_valid(tl) and tl.is_inside_tree():
		tl.get_tree().create_timer(t + 0.05, false).timeout.connect(tl.queue_free)
