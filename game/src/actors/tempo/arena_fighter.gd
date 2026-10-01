class_name ArenaFighter
extends QuakeAlly
## bh-028: an adventurer fighting in the Sand Arena (ArenaGrounds). A whole hero (class, level, gear, draughts) on the
## Quake Team's fighting AI, but sworn to nobody. It picks the rival it likes best (nearest, weakest, whoever hurt it
## last), roams the sand when nobody is in reach, drinks when hurt and falls back below its nerve, using its escape
## skills and dodge rolls to get clear. It never leaves the arena and nothing it does reaches outside the palisade.

const ROAM_EVERY := 4.0
const TAG_COLOR := Color(1.0, 0.55, 0.42)

var arena: ArenaGrounds
var rivalry := {}                     # instance id -> grudge (damage taken from them, fades)
var _roam_t := 0.0
var _roam_goal := Vector3.INF

## A random adventurer's hero sheet: their class at `level`, gear of that level (Advanced to Master), a few draughts.
static func make_mate(uid: int, cls: StringName, level: int, rng: RandomNumberGenerator, taken: Array = []) -> QuakeMate:
	var m := QuakeMate.new()
	m.uid = uid
	m.hero = Game.new_hero(cls, NameForge.person(rng, taken))
	m.hero.progress.add_xp(maxi(0, XpCurve.total_xp_for_level(level) - m.hero.progress.total_xp))
	QuakeBrain.spend_points(m.hero)
	if Game.hero:
		m.hero.difficulty = Game.hero.difficulty
		m.hero.tier = Game.hero.tier
		m.hero.equipment.tier_rank = Game.hero.tier
	m.hero.look = HeroLook.to_save(HeroLook.random(rng, 0.1))
	GuildSummons._gear_up(m.hero, level, rng)
	var hp := DB.make_item(&"health_potion", BH.Rarity.COMMON, level, rng.randi())
	hp.count = rng.randi_range(2, 3)
	m.hero.inventory.add(hp)
	m.tdata = TempoData.new()
	m.tdata.uid = uid
	m._build_tempo_data(rng)
	# arena regulars are bolder than the average companion, but every one of them still values their skin
	return m

func bind_arena(m: QuakeMate, p_arena: ArenaGrounds) -> ArenaFighter:
	arena = p_arena
	bind_mate(m, p_arena, 0)
	tdef["color"] = TAG_COLOR
	name = "ArenaFighter_%d" % m.uid
	display_name = m.display_name()
	return self

func _ready() -> void:
	super._ready()
	for g in [&"tempo", &"ally", &"quake_ally"]:
		remove_from_group(g)
	add_to_group(&"arena_fighter")
	add_to_group(&"arena_target")
	team = BH.Team.ENEMY
	collision_layer = BH.LAYER_ENEMY
	collision_mask = BH.LAYER_WORLD | BH.LAYER_GROUND | BH.LAYER_PROPS | BH.LAYER_PLAYER | BH.LAYER_ENEMY
	# a quarter of them stand their ground longer, a quarter run sooner
	personality = personality.duplicate()
	personality["retreat"] = [0.22, 0.3, 0.3, 0.4][rng.randi_range(0, 3)]

func _announced() -> bool:
	return false

func _online_ok() -> bool:
	return true

func _in_town() -> bool:
	return false

func is_arena_hero() -> bool:
	return true

func _hit_mask() -> int:
	return BH.LAYER_ENEMY | BH.LAYER_PLAYER

func _danger_layer() -> int:
	return BH.LAYER_ENEMY

## Resting out of reach mends far slower than a companion's: a fight here is meant to end.
func _rest_regen() -> float:
	return 0.012

func _spirit_look() -> void:
	visual.set_rim(Color(1.0, 0.45, 0.3), 0.2)
	visual.set_opacity(1.0)

func _update_plate() -> void:
	if _plate == null:
		return
	_plate_level = hero.progress.level
	_plate.text = "%s  Lv %d\n%s" % [mate.display_name(), _plate_level, hero.cls.display_name]
	_plate.modulate = TAG_COLOR

# ---- thinking -------------------------------------------------------------------------------------------------------

func _think() -> void:
	if arena == null or not is_instance_valid(arena):
		return
	for k in rivalry.keys():
		rivalry[k] = float(rivalry[k]) * 0.92
		if rivalry[k] < 1.0:
			rivalry.erase(k)
	if not arena.contains(global_position):
		# knocked out through the gate: straight back in
		_move_goal = arena.center
		if _flat(arena.center) > arena.radius + 6.0 or _stuck_t > 2.0:
			_rejoin_hero()
		return
	if mode == Mode.EVADE:
		if _evade_t > 0.0:
			return
		mode = Mode.ENGAGE if target else Mode.FOLLOW
	var busy := action != null and not action.can_cancel()
	if not busy and _try_heal():
		return
	if _retreat_logic():
		return
	target = _choose_target()
	if target == null:
		if mode != Mode.FOLLOW:
			_log("roam")
		mode = Mode.FOLLOW
		_move_goal = _formation_point()
		return
	mode = Mode.ENGAGE
	if busy:
		return
	if _try_skill():
		return
	_engage()
	_move_goal = _inside(_move_goal)

## The rival worth fighting: close, hurt, the one who hurt me, the one I am already on; heroes a little preferred.
func _choose_target() -> Actor:
	var best: Actor = null
	var best_s := -INF
	for c in arena.combatants():
		var a := c as Actor
		if a == self or a == null:
			continue
		var d := _flat(a.global_position)
		if d > 26.0:
			continue
		var s := -d * 0.4
		s += (1.0 - a.hp / maxf(1.0, a.max_hp())) * 4.0
		s += minf(6.0, float(rivalry.get(a.get_instance_id(), 0.0)) / maxf(1.0, max_hp()) * 30.0)
		if a == target:
			s += 3.0
		if a == last_attacker:
			s += 2.5
		if a is Player or (a is NetAvatar and (a as NetAvatar).is_hero):
			s += 1.0
		# someone running away is less worth chasing than someone standing in reach
		if a is ArenaFighter and (a as ArenaFighter).mode == Mode.RETREAT and d > 6.0:
			s -= 2.5
		if ai in ["marksman", "caster"] and CombatQuery.blocked(get_world_3d(), center(), a.center()):
			s -= 3.0
		if s > best_s:
			best_s = s
			best = a
	if best != target and best != null:
		_log("target %s" % best.display_name)
	return best

func _enemies(r: float, around := Vector3.INF) -> Array:
	if arena == null or not is_instance_valid(arena):
		return []
	var c := global_position if around == Vector3.INF else around
	var out := []
	for a in arena.combatants():
		if a != self and Vector2(a.global_position.x - c.x, a.global_position.z - c.z).length() < r:
			out.append(a)
	return out

func _nearest_enemy() -> Actor:
	var best: Actor = null
	var bd := INF
	for a in _enemies(40.0):
		var d := _flat(a.global_position)
		if d < bd:
			bd = d
			best = a
	return best

## Fall back away from every rival, staying on the sand.
func _retreat_point() -> Vector3:
	var away := Vector3.ZERO
	for e in _enemies(16.0):
		var d: Vector3 = (global_position - e.global_position).slide(Vector3.UP)
		away += d.normalized() / maxf(1.0, d.length())
	if away.length() < 0.01:
		away = (global_position - arena.center).slide(Vector3.UP)
	var dir := away.normalized() if away.length() > 0.01 else Vector3.BACK
	return _inside(global_position + dir * 9.0)

## Somewhere on the sand to wander to; a new place every few seconds.
func _formation_point() -> Vector3:
	_roam_t -= THINK
	if _roam_goal == Vector3.INF or _roam_t <= 0.0 or _flat(_roam_goal) < 1.5:
		_roam_t = ROAM_EVERY + rng.randf() * 3.0
		var a := rng.randf() * TAU
		var r := sqrt(rng.randf()) * (arena.radius - 4.0)
		_roam_goal = arena.center + Vector3(cos(a), 0, sin(a)) * r
	return _roam_goal

## A point pulled back inside the palisade (and off the gate's mouth).
func _inside(p: Vector3) -> Vector3:
	if arena == null or p == Vector3.INF:
		return p
	var off := (p - arena.center).slide(Vector3.UP)
	var lim := arena.radius - 2.0
	if off.length() > lim:
		off = off.normalized() * lim
	return arena.center + off + Vector3.UP * (p.y - arena.center.y)

## Stuck, or thrown out: back onto the sand.
func _rejoin_hero() -> void:
	var a := rng.randf() * TAU
	var spot := arena.center + Vector3(cos(a), 0, sin(a)) * rng.randf() * (arena.radius * 0.5)
	teleport_to(CombatQuery.ground_at(get_world_3d(), spot + Vector3.UP * 1.5))
	FX.spawn(VFXLib.dust_puff(0.8), global_position)
	_stuck_t = 0.0
	_cancel_action()
	mode = Mode.FOLLOW
	_log("back onto the sand")

func _fell_out() -> void:
	_rejoin_hero()

# ---- damage -----------------------------------------------------------------------------------------------------------

## Only a hero fighting on the sand can hurt an adventurer (no arrows through the gate from outside).
func receive_hit(req: DamageRequest, attacker: Node = null, hit_point := Vector3.INF) -> DamageResult:
	if attacker is Node3D and attacker != self and is_instance_valid(attacker) and not arena_contains(attacker as Node3D):
		var r0 := DamageResult.new()
		r0.evaded = true
		return r0
	var res := super.receive_hit(req, attacker, hit_point)
	if attacker is Actor and res and res.total > 0:
		var k := (attacker as Actor).get_instance_id()
		rivalry[k] = float(rivalry.get(k, 0.0)) + float(res.total)
	return res

func arena_contains(n: Node3D) -> bool:
	return arena != null and is_instance_valid(arena) and arena.contains(n.global_position)

func _announce_fall(killer: Node) -> void:
	if arena and is_instance_valid(arena):
		arena.on_fighter_fell(self, killer)

func _fall_notice() -> void:
	pass

## The arena's sand is not a shop: no errands (QuakeAlly), no gear changes after the walk-in.
func debug_text() -> String:
	return "[arena] " + super.debug_text()
