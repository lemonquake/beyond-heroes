class_name NecroKnight
extends RefCounted
## bh-042: the Fallen Necro-Knight's brain (docs/PLAN_bh-042.md, boss 1). A hero who fell in the Abyss and got up
## again, drawn on the hero body in black Eschaton plate with a pulsing teal aura (DataPersonas "fallen_necro_knight").
## He is always five levels above the hero (Spawner.spawn_enemy) and fights the way a player does, on top of the boss
## attack table in DataEnemiesAbyss:
##   * rolls out of telegraphed blows and incoming shots (invulnerable for the roll), never twice in a row too soon
##   * raises his shield when the hero winds up a heavy blow in front of him (frontal damage x0.3 while it is up)
##   * chains his sword attacks into a three-hit combo when the first one lands in reach
##   * drinks Soul Draughts when hurt (three, each 22% of his health over a second), and backs off to drink
##   * when he is low and out of draughts he kites: keeps his distance and casts (barrage, curse, soul bolts)
## Hooked in through EnemyTraitsX (trait &"player_like"): setup, tick, think, prepare_incoming, on_death.

const TEAL := Color(0.22, 0.95, 0.88)
const ROLL_TIME := 0.42
const ROLL_SPEED := 13.0
const ROLL_COOLDOWN := 2.2
const BLOCK_TIME := 1.1
const BLOCK_TAKEN := 0.3
const DRAUGHTS := 3
const DRAUGHT_HEAL := 0.22
const DRAUGHT_BELOW := 0.42
const COMBO := [&"nk_cut_1", &"nk_cut_2", &"nk_cut_3"]
const COMBO_WINDOW := 0.55
const MUSIC_KEY := &"necro_knight"

var e: Enemy
var draughts := DRAUGHTS
var _roll_t := 0.0
var _roll_cd := 0.0
var _block_t := 0.0
var _draught_cd := 0.0
var _combo_i := -1
var _combo_t := 0.0
var _kite_t := 0.0
var _music := false
var _light: OmniLight3D
var _aura: GPUParticles3D
var _t := 0.0

## His level: five above the strongest hero here (the host's own hero and every guest on this map).
static func level_for(hero_level: int) -> int:
	var top := hero_level
	if Net.is_active():
		for pid in Net.peers:
			var p: Dictionary = Net.peers[pid]
			if String(p.get("map", "")) == String(Game.current_map_id) or not p.has("map"):
				top = maxi(top, int(p.get("level", 0)))
	return clampi(top + DataEnemiesAbyss.NECRO_LEVELS_ABOVE, 1, BH.LEVEL_CAP)

func _init(enemy: Enemy) -> void:
	e = enemy

func setup() -> void:
	# the aura: teal motes rising round him, a light that breathes, a teal rim on the plate
	_aura = VFXLib.particles(Color(TEAL.r, TEAL.g, TEAL.b, 0.75), 46, 1.5, false, 0.16, 0.9, 25.0, Vector3(0, 1.4, 0), 0.75)
	_aura.position.y = 0.4
	e.add_child(_aura)
	var wisps := VFXLib.particles(Color(0.1, 0.6, 0.55, 0.45), 18, 2.2, false, 0.45, 0.35, 40.0, Vector3(0, 0.8, 0), 0.5)
	wisps.position.y = 1.2
	e.add_child(wisps)
	_light = OmniLight3D.new()
	_light.light_color = TEAL
	_light.omni_range = 7.0
	_light.light_energy = 1.6
	_light.shadow_enabled = false
	_light.position.y = 1.4
	e.add_child(_light)
	if e.visual:
		e.visual.set_rim(TEAL, 0.25)
	# the pulse runs on a looping tween so a multiplayer guest's copy (which never ticks) pulses too
	var tw := e.create_tween().set_loops()
	tw.tween_method(_pulse, 0.0, 1.0, 1.6).set_trans(Tween.TRANS_SINE)
	tw.tween_method(_pulse, 1.0, 0.0, 1.6).set_trans(Tween.TRANS_SINE)

func _pulse(v: float) -> void:
	if not is_instance_valid(e) or not e.alive:
		return
	if _light:
		_light.light_energy = 0.9 + 1.9 * v
	if _aura:
		_aura.amount_ratio = 0.55 + 0.45 * v
	if e.visual:
		e.visual.set_rim(TEAL, 0.12 + 0.3 * v)

# ---- every frame (owner only) -----------------------------------------------------------------------------------------

func tick(delta: float) -> void:
	_t += delta
	_roll_cd = maxf(0.0, _roll_cd - delta)
	_draught_cd = maxf(0.0, _draught_cd - delta)
	_kite_t = maxf(0.0, _kite_t - delta)
	if _roll_t > 0.0:
		_roll_t -= delta
	if _block_t > 0.0:
		_block_t -= delta
		if _block_t <= 0.0 and e.visual:
			e.visual.set_upper(&"")
	if _combo_t > 0.0:
		_combo_t -= delta
		if _combo_t <= 0.0:
			_combo_i = -1
	if not _music and e.brain.is_engaged() and e.target is Player:
		_music = true
		Music.push(MUSIC_KEY, &"boss_theme")
		Events.notify.emit("The Fallen Necro-Knight has found you.", &"danger")
	elif _music and not e.brain.is_engaged():
		_music = false
		Music.pop(MUSIC_KEY)

# ---- decisions (called from Enemy._combat_think through EnemyTraitsX.think) -----------------------------------------

## True when he did something a player would do instead of the plain boss attack choice.
func think() -> bool:
	if e.target == null or not e.target.alive:
		return false
	if _roll_t > 0.0:
		return true
	var busy := e.action != null
	var hpf := e.hp / maxf(1.0, e.max_hp())
	# 1. dodge what is coming
	if not busy and _roll_cd <= 0.0 and (_threatened() or (hpf < 0.6 and e.rng.randf() < 0.06)):
		roll(_roll_dir())
		return true
	# 2. a draught when hurt, from a little distance if he can get it
	if not busy and draughts > 0 and _draught_cd <= 0.0 and hpf < DRAUGHT_BELOW:
		drink()
		return true
	# 3. shield up against a heavy wind-up in front of him
	if not busy and _block_t <= 0.0 and e._dist < 5.0 and e._target_winding_up() and e.rng.randf() < 0.55:
		_block_t = BLOCK_TIME
		if e.visual:
			e.visual.set_upper(&"block_loop")
		return true
	if _block_t > 0.0:
		return true
	# 4. carry a combo on while the window is open
	if not busy and _combo_i >= 0 and _combo_i < COMBO.size() - 1 and _combo_t > 0.0 and e._dist < 4.0:
		var nxt := _attack(COMBO[_combo_i + 1])
		if not nxt.is_empty():
			e.cooldowns.erase(nxt.id)
			_combo_i += 1
			_combo_t = COMBO_WINDOW + 0.6
			e._start_attack(nxt)
			return true
	# 5. low and out of draughts: keep away and cast
	if hpf < 0.3 and draughts <= 0 and not busy:
		if e._dist < 7.0 and _kite_t <= 0.0:
			_kite_t = 1.2
			e.brain.go(EnemyBrain.State.RETREAT)
			e._move_target = e._retreat_point()
			return true
	return false

## The plain attack choice picked `a`: the first cut of the combo opens the combo window.
func on_attack(a: Dictionary) -> void:
	if a.get("id", &"") == COMBO[0]:
		_combo_i = 0
		_combo_t = COMBO_WINDOW + 0.6

func _attack(id: StringName) -> Dictionary:
	for a in e.def.attacks:
		if a.id == id:
			return a
	return {}

## Something dangerous is about to land on him: a hero swinging or casting close by, a shot flying at him, a blast marker
## under his feet.
func _threatened() -> bool:
	if e._dist < 4.5 and e._target_winding_up() and e.rng.randf() < 0.7:
		return true
	for p in e.get_tree().get_nodes_in_group(&"projectile"):
		var pr := p as Projectile
		if pr == null or pr.source == e or not is_instance_valid(pr) or pr.request == null:
			continue
		var to := e.global_position - pr.global_position
		if to.length() < 6.0 and pr.velocity.normalized().dot(to.normalized()) > 0.85:
			return e.rng.randf() < 0.6
	return false

func _roll_dir() -> Vector3:
	var away := (e.global_position - e.target.global_position).slide(Vector3.UP)
	if away.length() < 0.1:
		away = -e.forward()
	away = away.normalized()
	var side := away.cross(Vector3.UP) * (1.0 if e.rng.randf() < 0.5 else -1.0)
	# sideways out of the line most of the time, straight back when hurt
	return (side * 0.8 + away * 0.6).normalized() if e.hp > e.max_hp() * 0.4 else (away * 0.8 + side * 0.4).normalized()

func roll(dir: Vector3) -> void:
	_roll_t = ROLL_TIME
	_roll_cd = ROLL_COOLDOWN * e.rng.randf_range(0.85, 1.3)
	e._charge = {"dir": dir, "speed": ROLL_SPEED, "left": ROLL_TIME, "delay": 0.0, "hit": true, "a": {}, "lunge": true}
	if e.visual:
		e.visual.play_action(&"dodge_roll", 1.2)
	e._face_now(e.global_position - dir)
	FX.spawn(VFXLib.dust_puff(0.7), e.global_position)

func drink() -> void:
	draughts -= 1
	_draught_cd = 6.0
	if e.visual:
		e.visual.play_action(&"interact_pickup", 1.4)
	var heal := e.max_hp() * DRAUGHT_HEAL
	for i in 5:
		e.get_tree().create_timer(0.2 * i, false).timeout.connect(func() -> void:
			if is_instance_valid(e) and e.alive:
				e.heal(heal / 5.0, i == 4))
	FX.spawn(VFXLib.ring_wave(TEAL, 2.0, 0.6, 0.4), e.global_position)
	FX.text_popup(e.center() + Vector3.UP * 1.2, "Soul Draught (%d left)" % draughts, TEAL, 1.2)
	Audio.play_at(&"potion_drink" if Audio.has_sound(&"potion_drink") else &"arcane_surge", e.global_position)

# ---- incoming damage ----------------------------------------------------------------------------------------------------

func prepare_incoming(req: DamageRequest, attacker: Node) -> void:
	if req.kind == DamageRequest.Kind.DOT:
		return
	if _roll_t > 0.0:
		req.more.append(["Rolled", 0.0])
		FX.text_popup(e.center() + Vector3.UP, "Rolled", Color(0.7, 0.95, 0.9), 0.6)
		return
	if _block_t > 0.0 and attacker is Node3D:
		var to: Vector3 = ((attacker as Node3D).global_position - e.global_position).slide(Vector3.UP)
		if to.length() > 0.05 and e.forward().angle_to(to.normalized()) < deg_to_rad(70.0):
			req.more.append(["Shield", BLOCK_TAKEN])
			FX.text_popup(e.center() + Vector3.UP, "Blocked", Color(0.8, 0.85, 0.9), 0.6)

func on_death() -> void:
	if _music:
		_music = false
		Music.pop(MUSIC_KEY)
	if _light:
		var tw := _light.create_tween()
		tw.tween_property(_light, "light_energy", 0.0, 1.5)
