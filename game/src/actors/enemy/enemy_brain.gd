class_name EnemyBrain
extends RefCounted
## Enemy AI state machine: the states, the legal transitions between them, awareness, and a transition log.
## The Enemy node supplies perception and executes the behaviour of the current state; this class guarantees the
## machine can never enter an illegal state (tests assert `invalid_transitions == 0` over long soaks).

enum State { IDLE, PATROL, SUSPICIOUS, ALERT, CHASE, POSITION, ATTACK, SPECIAL, RETREAT, DEFEND, CAST, STAGGER, KNOCKBACK, DEAD }

const NAMES := ["Idle", "Patrol", "Suspicious", "Alert", "Chase", "Position", "Attack", "Special", "Retreat", "Defend",
	"Cast", "Stagger", "Knockback", "Dead"]

## Interrupt states reachable from anything alive.
const INTERRUPTS := [State.STAGGER, State.KNOCKBACK, State.DEAD]

const ALLOWED := {
	State.IDLE: [State.PATROL, State.SUSPICIOUS, State.ALERT, State.CHASE],
	State.PATROL: [State.IDLE, State.SUSPICIOUS, State.ALERT, State.CHASE],
	State.SUSPICIOUS: [State.IDLE, State.PATROL, State.ALERT, State.CHASE],
	State.ALERT: [State.CHASE, State.POSITION, State.RETREAT],
	State.CHASE: [State.POSITION, State.ATTACK, State.SPECIAL, State.CAST, State.RETREAT, State.DEFEND, State.IDLE, State.PATROL, State.SUSPICIOUS],
	State.POSITION: [State.CHASE, State.ATTACK, State.SPECIAL, State.CAST, State.RETREAT, State.DEFEND, State.IDLE, State.PATROL],
	State.ATTACK: [State.POSITION, State.CHASE, State.RETREAT, State.DEFEND],
	State.SPECIAL: [State.POSITION, State.CHASE, State.RETREAT],
	State.CAST: [State.POSITION, State.CHASE, State.RETREAT],
	State.RETREAT: [State.POSITION, State.CHASE, State.CAST, State.ATTACK, State.IDLE, State.PATROL],
	State.DEFEND: [State.POSITION, State.CHASE, State.ATTACK, State.SPECIAL],
	State.STAGGER: [State.POSITION, State.CHASE, State.KNOCKBACK, State.RETREAT],
	State.KNOCKBACK: [State.POSITION, State.CHASE, State.STAGGER, State.RETREAT],
	State.DEAD: [],
}

var state: State = State.IDLE
var time_in_state := 0.0
var awareness := 0.0                  # 0 unaware .. 1 fully alert
var last_known := Vector3.INF         # last seen / heard player position
var invalid_transitions := 0
var transitions := 0
var history: Array = []               # last N [from, to] for the debug overlay

func can_go(to: State) -> bool:
	if state == State.DEAD:
		return false
	if to == state:
		return true
	if INTERRUPTS.has(to):
		return true
	return ALLOWED[state].has(to)

## Change state; illegal requests are refused and counted. Returns true on success.
func go(to: State) -> bool:
	if to == state:
		return true
	if not can_go(to):
		invalid_transitions += 1
		return false
	history.append([state, to])
	if history.size() > 12:
		history.pop_front()
	state = to
	time_in_state = 0.0
	transitions += 1
	return true

func tick(delta: float) -> void:
	time_in_state += delta

func is_engaged() -> bool:
	return state >= State.ALERT and state != State.DEAD

func is_busy() -> bool:
	return state in [State.ATTACK, State.SPECIAL, State.CAST]

func state_name() -> String:
	return NAMES[state]

## Awareness model: seeing the player raises it (faster when close), losing sight decays it.
func perceive(sees: bool, dist: float, sight_range: float, delta: float, heard := false) -> void:
	if heard:
		awareness = maxf(awareness, 0.75)
	if sees:
		var closeness := 1.0 - clampf(dist / maxf(sight_range, 0.1), 0.0, 1.0)
		awareness = minf(1.0, awareness + delta * (0.6 + 3.0 * closeness))
	elif not is_engaged():
		awareness = maxf(0.0, awareness - delta * 0.25)
