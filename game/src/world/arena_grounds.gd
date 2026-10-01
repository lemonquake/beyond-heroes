class_name ArenaGrounds
extends Node3D
## bh-028: the Sand Arena at Wyman Outpost: hero against hero, everyone against everyone.
##
## The arena is a ring of sand inside a palisade, with one gate. Inside:
##   - Every hero is fair game. Players hit players, players hit adventurers, adventurers hit everyone. Blows between
##     heroes are scaled and capped (CombatBudget.pvp_mult, PVP_BLOW_CAP; Actor._threat_guard).
##   - Randomised adventurers (ArenaFighter) fight whoever is nearest or weakest. They drink draughts and fall back
##     when hurt, using their escape skills. The world authority runs them: the solo player, or in multiplayer the
##     member running the outpost's combat (Net.is_world_authority). Their level is the highest level in the party.
##   - A hero who falls stands up again at the gate a moment later, with full health and no cost.
##   - Companions do not fight here. Tempos, the Quake Team and guild fighters wait outside the gate while their hero
##     is inside (Tempo._hold_back), and follow again when the hero comes out.

const FIGHTERS := 6
const RESPAWN_DELAY := 3.0          # a fallen hero stands up at the gate
const SPAWN_GUARD := 2.5            # ... untouchable for this long
const REFILL_DELAY := 7.0           # a fallen adventurer's place is taken by a new one
const FIRST_FILL := 0.6             # seconds between the first adventurers walking in
const UID_BASE := 800000
const GATE_SPAWN := &"arena_gate"

static var _active: WeakRef

var radius := 20.0
var center := Vector3.ZERO           # global, on the sand
var gate := Vector3.ZERO             # just inside the gate: where fallen heroes stand up
var gate_out := Vector3.FORWARD      # from the arena out through the gate
var fighter_door := Vector3.ZERO     # where adventurers walk in
var max_fighters := FIGHTERS

var _inside := false
var _respawn_at := -1.0
var _refill_t := 0.0
var _serial := 0
var _time := 0.0
var _rng := RandomNumberGenerator.new()

## Set up by the map (WymanOutpost._arena): everything in global coordinates.
func configure(p_center: Vector3, p_radius: float, p_gate: Vector3, p_gate_out: Vector3, p_door: Vector3) -> ArenaGrounds:
	center = p_center
	radius = p_radius
	gate = p_gate
	gate_out = p_gate_out.slide(Vector3.UP).normalized()
	fighter_door = p_door
	name = "ArenaGrounds"
	return self

func _ready() -> void:
	_active = weakref(self)
	add_to_group(&"arena_grounds")
	_rng.seed = hash(["sand_arena", Time.get_ticks_usec()])
	Events.player_died.connect(_on_player_died)

func _exit_tree() -> void:
	if _active and _active.get_ref() == self:
		_active = null

static func active() -> ArenaGrounds:
	var a: ArenaGrounds = _active.get_ref() if _active else null
	return a if a != null and is_instance_valid(a) and a.is_inside_tree() else null

## Is a point on the sand (inside the palisade)?
func contains(p: Vector3) -> bool:
	return Vector2(p.x - center.x, p.z - center.z).length() < radius - 0.3 and absf(p.y - center.y) < 6.0

## Is this node standing in the arena right now?
static func holds(n: Node3D) -> bool:
	var a := active()
	return a != null and n != null and is_instance_valid(n) and n.is_inside_tree() and a.contains(n.global_position)

## Does a companion stay out of the arena (its hero is inside)?
func holds_back(t: Tempo) -> bool:
	if t is ArenaFighter:
		return false
	var p := t.owner_player
	return p != null and is_instance_valid(p) and p is Player and contains(p.global_position)

## Where a waiting companion stands: along the palisade outside the gate, two to a rank.
func wait_point(t: Node) -> Vector3:
	var waiting := get_tree().get_nodes_in_group(&"tempo").filter(func(n): return n is Tempo and not (n is ArenaFighter))
	waiting.sort_custom(func(a, b): return a.get_instance_id() < b.get_instance_id())
	var i := maxi(0, waiting.find(t))
	var side := gate_out.cross(Vector3.UP).normalized()
	var mouth := center + gate_out * (radius + 4.5)
	var col := float(i / 2) * 1.7 + 2.6
	return mouth + side * (col if i % 2 == 0 else -col)

## Everyone fighting in the arena: this machine's hero, other players' heroes and the adventurers.
func combatants() -> Array:
	var out := []
	var p := Game.player as Actor
	if p != null and is_instance_valid(p) and p.alive and contains(p.global_position) and not p.invulnerable:
		out.append(p)
	for av in Net.avatars():
		var a := av as NetAvatar
		if a != null and a.alive and (a.is_hero or a.arena_fighter) and contains(a.global_position):
			out.append(a)
	for f in get_tree().get_nodes_in_group(&"arena_fighter"):
		if is_instance_valid(f) and f.alive and not f.is_queued_for_deletion():
			out.append(f)
	return out

## Is this machine the one that runs the adventurers?
static func runs_fighters() -> bool:
	return not Net.is_active() or Net.is_world_authority()

## The highest hero level in the party (alone: the hero's own).
static func party_level() -> int:
	var lvl := Game.hero.progress.level if Game.hero != null else 1
	if Net.is_active():
		for id in Net.peers:
			lvl = maxi(lvl, int(Net.peers[id].get("level", 1)))
	return clampi(lvl, 1, BH.LEVEL_CAP)

func fighters() -> Array:
	return get_tree().get_nodes_in_group(&"arena_fighter").filter(func(f): return is_instance_valid(f) and not f.is_queued_for_deletion())

# ---- every frame ------------------------------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	_time += delta
	var p := Game.player as Player
	if p != null and is_instance_valid(p) and p.is_inside_tree():
		_track_player(p)
	_avatar_layers()
	if runs_fighters():
		_keep_fighters(delta)
	else:
		for f in fighters():
			f.queue_free()

func _track_player(p: Player) -> void:
	var now := contains(p.global_position)
	if now != _inside and p.alive:
		_inside = now
		if now:
			Events.notify.emit("You enter the Sand Arena. Every hero here is your rival. Your companions wait outside the gate.", &"info")
			Audio.play_ui(&"war_cry")
		else:
			Events.notify.emit("You leave the Sand Arena. Your companions rejoin you.", &"info")
	if _respawn_at > 0.0 and _time >= _respawn_at:
		_respawn_at = -1.0
		if not p.alive:
			_stand_up(p)

## Other players' heroes inside the arena are targets while this hero is in there too; adventurers always are.
func _avatar_layers() -> void:
	var me := Game.player as Node3D
	var me_in := me != null and is_instance_valid(me) and contains(me.global_position)
	for av in Net.avatars():
		var a := av as NetAvatar
		if a == null:
			continue
		var hostile := a.arena_fighter or (a.is_hero and me_in and a.alive and contains(a.global_position))
		a.set_arena_hostile(hostile)

# ---- the adventurers --------------------------------------------------------------------------------------------------

func _keep_fighters(delta: float) -> void:
	if Game.hero == null or Game.travelling:
		return
	var n := fighters().size()
	if n >= max_fighters:
		_refill_t = REFILL_DELAY
		return
	_refill_t -= delta
	if _refill_t > 0.0:
		return
	_refill_t = FIRST_FILL if n < max_fighters / 2 else REFILL_DELAY * 0.5
	spawn_fighter()

## A new adventurer walks in through the fighters' door. Returns it (tests call this directly).
func spawn_fighter(cls := &"", level := 0) -> ArenaFighter:
	_serial += 1
	var lvl := level if level > 0 else party_level()
	var classes := [&"knight", &"mage", &"ranger", &"shadowblade"]
	var c: StringName = cls if cls != &"" else classes[_rng.randi_range(0, classes.size() - 1)]
	var taken := fighters().map(func(f): return (f as ArenaFighter).mate.display_name())
	if Game.hero:
		taken.append(Game.hero.hero_name)
	var mate := ArenaFighter.make_mate(UID_BASE + _serial, c, lvl, _rng, taken)
	var f := ArenaFighter.new().bind_arena(mate, self)
	get_parent().add_child(f)
	var side := gate_out.cross(Vector3.UP).normalized()
	var spot := fighter_door + side * _rng.randf_range(-2.5, 2.5) - (fighter_door - center).slide(Vector3.UP).normalized() * _rng.randf_range(1.0, 3.0)
	if is_inside_tree():
		spot = CombatQuery.ground_at(get_world_3d(), spot + Vector3.UP * 2.0)
	f.teleport_to(spot)
	f.rotation.y = atan2(center.x - spot.x, center.z - spot.z)
	FX.spawn(VFXLib.dust_puff(0.9), spot)
	return f

## An adventurer fell (ArenaFighter._announce_fall).
func on_fighter_fell(f: ArenaFighter, killer: Node) -> void:
	_refill_t = maxf(_refill_t, REFILL_DELAY)
	var who := _name_of(killer)
	if who != "" and (killer == Game.player or (killer is NetAvatar and (killer as NetAvatar).is_hero)):
		Events.notify.emit("%s defeated %s in the Sand Arena." % [who, f.display_name], &"loot" if killer == Game.player else &"info")

static func _name_of(n: Node) -> String:
	if n == null or not is_instance_valid(n):
		return ""
	if n == Game.player and Game.hero:
		return "You"
	return String(n.get(&"display_name")) if n.get(&"display_name") != null else ""

# ---- falling in the arena ---------------------------------------------------------------------------------------------

## True while this machine's fallen hero will stand up at the gate (no death screen, no cost).
static func handles_death(p: Node) -> bool:
	var a := active()
	return a != null and p is Player and is_instance_valid(p) and (a._respawn_at > 0.0 or a.contains((p as Player).global_position))

func _on_player_died() -> void:
	var p := Game.player as Player
	if p == null or not contains(p.global_position):
		return
	_respawn_at = _time + RESPAWN_DELAY
	var by := _name_of(p.last_attacker)
	Events.notify.emit(("%s bested you in the Sand Arena." % by if by != "" else "You fell in the Sand Arena.") + " You will stand up at the gate.", &"error")

func _stand_up(p: Player) -> void:
	var look := (center - gate).slide(Vector3.UP)
	var spot := CombatQuery.ground_at(get_world_3d(), gate + Vector3.UP * 1.5) if is_inside_tree() else gate
	p.global_transform = Transform3D(Basis(Vector3.UP, atan2(look.x, look.z)), spot + Vector3.UP * 0.05)
	p.velocity = Vector3.ZERO
	p.on_teleported()
	p.respawn()
	p.hp = p.max_hp()
	p.mana = p.max_mana()
	p.health_changed.emit(p.hp, p.max_hp())
	p.mana_changed.emit(p.mana, p.max_mana())
	p.grant_spawn_guard(SPAWN_GUARD)
	_inside = true
	FX.spawn(VFXLib.ring_wave(Color(1.0, 0.85, 0.5, 0.9), 2.2, 0.5, 0.6), spot)
	Events.player_respawned.emit()
