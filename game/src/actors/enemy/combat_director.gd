class_name CombatDirector
extends Node
## Group coordination for enemies engaged with the player (one per map).
##
## * Attack tokens: at most `melee_tokens` melee attackers and `ranged_tokens` shooters act at the same moment, so a
##   crowd takes turns instead of hitting simultaneously from the same spot. Tokens are held for one attack and have a
##   short per-enemy cooldown after release.
## * Ring slots: melee enemies are assigned distinct positions on rings around the player (spread out, circle while
##   waiting); flankers prefer slots behind the player; tanks take slots between the player and engaged casters.
## Pure bookkeeping — enemies ask, the director answers. Everything is deterministic given the same queries.

static var current: CombatDirector

const SLOT_COUNT := 10
const TOKEN_COOLDOWN := 0.6

var melee_tokens := 2
var ranged_tokens := 2
var _holders := {}          # enemy instance id -> kind (&"melee"/&"ranged")
var _token_cd := {}         # enemy instance id -> time when it may ask again
var _slots := {}            # enemy instance id -> slot index
var _time := 0.0

func _enter_tree() -> void:
	current = self

func _exit_tree() -> void:
	if current == self:
		current = null

func configure(difficulty: Dictionary) -> void:
	melee_tokens = int(difficulty.get("tokens", 2))
	ranged_tokens = 2 + (1 if melee_tokens >= 3 else 0)

func _physics_process(delta: float) -> void:
	_time += delta
	for id in _holders.keys():
		var e = instance_from_id(id)
		if e == null or not is_instance_valid(e) or not e.alive:
			_holders.erase(id)
			_slots.erase(id)

func holders(kind: StringName) -> int:
	var n := 0
	for id in _holders:
		if _holders[id] == kind:
			n += 1
	return n

func has_token(enemy: Node) -> bool:
	return _holders.has(enemy.get_instance_id())

## Ask for the right to attack now. Bosses and special cases (`force`) always get one.
func request_token(enemy: Node, kind: StringName, force := false) -> bool:
	var id := enemy.get_instance_id()
	if _holders.has(id):
		return true
	if not force:
		if _token_cd.get(id, 0.0) > _time:
			return false
		var cap := melee_tokens if kind == &"melee" else ranged_tokens
		if holders(kind) >= cap:
			return false
	_holders[id] = kind
	return true

func release_token(enemy: Node) -> void:
	var id := enemy.get_instance_id()
	if _holders.has(id):
		_holders.erase(id)
		_token_cd[id] = _time + TOKEN_COOLDOWN

func forget(enemy: Node) -> void:
	var id := enemy.get_instance_id()
	_holders.erase(id)
	_slots.erase(id)
	_token_cd.erase(id)

## A position around `player` for `enemy` at distance `radius`. Keeps the enemy's slot stable once assigned.
func slot_position(enemy: Actor, player: Node3D, radius: float, prefer_behind := false, guard_of: Node3D = null) -> Vector3:
	var id := enemy.get_instance_id()
	var pf: Vector3 = player.global_transform.basis.z
	pf.y = 0.0
	pf = pf.normalized() if pf.length() > 0.01 else Vector3.FORWARD
	if guard_of != null and is_instance_valid(guard_of):
		var to_c := guard_of.global_position - player.global_position
		to_c.y = 0.0
		if to_c.length() > 0.5:
			return player.global_position + to_c.normalized() * minf(radius, to_c.length() * 0.5)
	if not _slots.has(id):
		_slots[id] = _best_free_slot(enemy, player, pf, prefer_behind)
	var ang := TAU * float(_slots[id]) / SLOT_COUNT
	var dir := pf.rotated(Vector3.UP, ang)
	return player.global_position + dir * radius

func _best_free_slot(enemy: Actor, player: Node3D, pf: Vector3, prefer_behind: bool) -> int:
	var taken := {}
	for other in _slots:
		taken[_slots[other]] = true
	var best := 0
	var best_score := INF
	var to_e := enemy.global_position - player.global_position
	to_e.y = 0.0
	for i in SLOT_COUNT:
		var ang := TAU * float(i) / SLOT_COUNT
		var dir := pf.rotated(Vector3.UP, ang)
		var score := dir.angle_to(to_e.normalized()) if to_e.length() > 0.1 else 0.0
		if prefer_behind:
			score += dir.angle_to(-pf) * 1.5
		if taken.has(i):
			score += 10.0
		if score < best_score:
			best_score = score
			best = i
	return best

func release_slot(enemy: Node) -> void:
	_slots.erase(enemy.get_instance_id())

## Nearest engaged caster/support ally the tank should shield (or null).
static func caster_to_protect(enemy: Actor, allies: Array) -> Actor:
	var best: Actor = null
	var bd := 14.0 * 14.0
	for a in allies:
		if a == enemy or not a.alive or not (a.def.archetype in [&"caster", &"support", &"ranged"]):
			continue
		var d: float = a.global_position.distance_squared_to(enemy.global_position)
		if d < bd:
			bd = d
			best = a
	return best
