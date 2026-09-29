class_name PracticeDummy
extends Actor
## bh-019: a straw practice dummy in every safe town. Every attack, skill, projectile and damage-over-time lands on it
## like on a monster (it sits on the enemy physics layer), so heroes can try their damage: the usual damage numbers
## pop, the body rocks on its post, and a board over it keeps the last hit, the biggest hit, damage per second over
## the last five seconds and the total of the current bout (a bout ends after 6 s without a hit). It never dies,
## never fights back and is not a monster: it is not in the "enemy" group, so Tempos, allies, the minimap and the
## combat rules ignore it; the hero's auto-aim finds it through the "practice_target" group.
##
## It has no armour and no resistances, so the numbers are the hero's own. The model is the environment kit asset
## `practice_dummy` (base) + its `dummy_body` node (or the separate `practice_dummy_body` asset), which rocks.

const MODEL := "practice_dummy"
const BODY_MODEL := "practice_dummy_body"
const WINDOW := 5.0
const BOUT_END := 6.0
const HUGE := 1.0e9

var _hits: Array = []           # [time, amount]
var _bout_total := 0
var _bout_hits := 0
var _best := 0
var _last := 0
var _last_crit := false
var _t := 0.0
var _last_hit_t := -99.0
var _board: Label3D
var _body: Node3D
var _tilt := Vector2.ZERO       # rocking angle (x, z) and its velocity
var _tilt_v := Vector2.ZERO

func _init() -> void:
	display_name = "Practice Dummy"
	team = BH.Team.ENEMY
	weight = 50.0
	body_radius = 0.4
	body_height = 1.8

func _ready() -> void:
	super._ready()
	name = "PracticeDummy"
	add_to_group(&"practice_target")
	collision_layer = BH.LAYER_ENEMY
	collision_mask = 0
	var shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.36
	cap.height = 1.9
	shape.shape = cap
	shape.position.y = 0.95
	add_child(shape)
	_load_model()
	_board = Label3D.new()
	_board.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_board.no_depth_test = true
	_board.render_priority = 8
	_board.fixed_size = true
	_board.pixel_size = 0.0008
	_board.font = UITheme.body_bold()
	_board.font_size = 22
	_board.outline_size = 8
	_board.outline_modulate = Color(0, 0, 0, 0.85)
	_board.modulate = UITheme.PARCHMENT
	_board.position.y = 2.55
	_board.visible = false
	add_child(_board)
	Events.damage_dealt.connect(_on_damage)
	hp = HUGE

func _load_model() -> void:
	var base_path := MapBuilder.ENV_DIR % MODEL
	if not ResourceLoader.exists(base_path):
		return
	var n: Node3D = (load(base_path) as PackedScene).instantiate()
	add_child(n)
	_strip_collision(n)
	MaterialLibrary.apply_environment(n)
	_body = n.find_child("dummy_body", true, false) as Node3D
	if _body == null and ResourceLoader.exists(MapBuilder.ENV_DIR % BODY_MODEL):
		var b: Node3D = (load(MapBuilder.ENV_DIR % BODY_MODEL) as PackedScene).instantiate()
		add_child(b)
		_strip_collision(b)
		MaterialLibrary.apply_environment(b)
		_body = b
	if _body:
		_body.set_meta(&"rest", _body.transform)

## The dummy's own capsule is its collision; the model's collision copies would block arrows before they land.
static func _strip_collision(n: Node) -> void:
	for c in n.get_children():
		if c is CollisionObject3D:
			c.queue_free()
		else:
			_strip_collision(c)

func rebuild_stats() -> void:
	var d := DerivedStats.new()
	d.set_stat(&"max_hp", HUGE)
	d.set_stat(&"poise", HUGE)
	d.set_stat(&"knockback_res", 1.0)
	stats = d

func is_aggressive() -> bool:
	return false

func in_combat() -> bool:
	return false

func die(_killer: Node) -> void:
	hp = max_hp()

func apply_knockback(dir: Vector3, speed: float, _source: DerivedStats, _source_node: Node, _depth := 0, _launch := 0.0) -> void:
	_rock(dir, clampf(speed / 8.0, 0.2, 1.0))

func _on_damaged(_result: DamageResult, _req: DamageRequest) -> void:
	hp = max_hp()

func _on_damage(target: Node, r: DamageResult, _pos: Vector3, attacker: Node) -> void:
	if target != self:
		return
	hp = max_hp()
	if r.evaded or r.total <= 0:
		return
	_hits.append([_t, r.total])
	if _t - _last_hit_t > BOUT_END:
		_bout_total = 0
		_bout_hits = 0
		_best = 0
	_last_hit_t = _t
	_bout_total += r.total
	_bout_hits += 1
	_last = r.total
	_last_crit = r.is_crit
	_best = maxi(_best, r.total)
	if attacker is Node3D and is_instance_valid(attacker):
		_rock(global_position - (attacker as Node3D).global_position, 0.35 + (0.3 if r.is_crit or r.heavy else 0.0))
	_update_board()

func _rock(dir: Vector3, strength: float) -> void:
	if _body == null:
		return
	var d := dir
	d.y = 0.0
	if d.length_squared() < 0.0001:
		d = -global_transform.basis.z
	d = (global_transform.basis.inverse() * d.normalized())
	# tilt away from the blow: about local X for a push along Z, about Z for a push along X
	_tilt_v += Vector2(d.z, -d.x) * 3.2 * strength

func dps() -> float:
	var sum := 0
	var first := _t
	for h in _hits:
		if _t - float(h[0]) <= WINDOW:
			sum += int(h[1])
			first = minf(first, float(h[0]))
	if sum <= 0:
		return 0.0
	return float(sum) / clampf(_t - first + 0.5, 1.0, WINDOW)

func _update_board() -> void:
	if _board == null:
		return
	if _t - _last_hit_t > BOUT_END:
		_board.text = "Practice Dummy\n[Attack it to test your damage]"
		return
	_board.text = "Practice Dummy\nLast hit %s%s  ·  Best %s\n%s damage per second  ·  %s total in %d hits" % [
		SocketWindow._thousands(_last), " (critical)" if _last_crit else "", SocketWindow._thousands(_best),
		SocketWindow._thousands(roundi(dps())), SocketWindow._thousands(_bout_total), _bout_hits]

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	_t += delta
	ensure_stats()
	status.tick(delta)
	knock_velocity = Vector3.ZERO
	while not _hits.is_empty() and _t - float(_hits[0][0]) > WINDOW:
		_hits.pop_front()
	# a damped spring back to upright
	_tilt_v += (-_tilt * 38.0 - _tilt_v * 5.5) * delta
	_tilt += _tilt_v * delta
	_tilt = _tilt.clamp(Vector2(-0.45, -0.45), Vector2(0.45, 0.45))
	if _body:
		var rest: Transform3D = _body.get_meta(&"rest", Transform3D.IDENTITY)
		_body.transform = rest * Transform3D(Basis.from_euler(Vector3(_tilt.x, 0.0, _tilt.y)), Vector3.ZERO)

func _process(_delta: float) -> void:
	if _board == null:
		return
	var p := Game.player as Node3D
	_board.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 12.0
	if _board.visible and Engine.get_process_frames() % 10 == 0:
		_update_board()
