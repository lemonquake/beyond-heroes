class_name ClassPassives
extends RefCounted
## Combat state belongs to the hero, never to a shared skill definition.

var owner: Player
var double_cd := 0.0
var landed_attacks := 0
var last_attack := -1

func _init(player: Player) -> void:
	owner = player

func tick(delta: float) -> void:
	double_cd = maxf(0.0, double_cd - delta)

func basic(req: DamageRequest) -> bool:
	return req.kind == DamageRequest.Kind.ATTACK and req.tags.has(&"weapon") and not req.tags.has(&"proc")

func before_hit(req: DamageRequest) -> void:
	if not basic(req) or not req.tags.has(&"projectile"):
		return
	var knee := owner.stats.flag(&"knee_shot")
	if knee > 0.0 and owner.rng.randf() < 0.25:
		req.more.append(["Knee Shot", 1.0 + minf(0.40, knee)])
		req.tags[&"knee_shot"] = true

func after_hit(target: Actor, req: DamageRequest, result: DamageResult) -> void:
	if not owner.alive or not basic(req) or result.evaded or result.total <= 0:
		return
	if req.tags.has(&"knee_shot") and target.alive:
		target.status.apply(&"stunned", 0.4)
	if req.tags.has(&"projectile"):
		return
	var st := owner.stats
	if target.alive:
		if st.has_flag(&"paralyzing_attack"):
			var slow := minf(0.85, st.flag(&"paralyzing_attack"))
			target.status.apply(&"paralyzed", 0.1, slow, 0.0, Elements.PHYSICAL, [StatModifier.more(&"move_speed", -slow, "Paralyzing Attack")])
		if st.has_flag(&"bloodcurse"):
			target.status.apply(&"bloodcurse", 4.0, minf(0.70, st.flag(&"bloodcurse")))
	# A wide swing counts once, regardless of how many targets it catches.
	var attack_id := int(req.tags.get(&"attack_id", -1))
	if attack_id != last_attack:
		last_attack = attack_id
		landed_attacks += 1
		if landed_attacks % 2 == 0 and st.has_flag(&"bloodsucker"):
			owner.heal(result.total * minf(0.35, st.flag(&"bloodsucker")), false)
	if target.alive and double_cd <= 0.0 and st.has_flag(&"double_attack"):
		double_cd = 1.2
		var repeat := DamageRequest.new()
		repeat.attacker = st
		repeat.use_weapon = true
		repeat.hand = req.hand
		repeat.weapon_mult = minf(0.65, st.flag(&"double_attack"))
		repeat.label = "Double Attack"
		repeat.tags[&"proc"] = true
		owner.get_tree().create_timer(0.12, false).timeout.connect(func() -> void:
			if not is_instance_valid(owner) or not owner.alive or owner.is_disabled() or not is_instance_valid(target) or not target.alive:
				return
			if owner.global_position.distance_to(target.global_position) > 4.0 or CombatQuery.blocked(owner.get_world_3d(), owner.center(), target.center()):
				return
			target.receive_hit(repeat, owner, target.center())
			FX.spawn_facing(VFXLib.slash_arc(Color(0.8, 0.3, 0.45), 2.0, 90.0, 1.0, 0.15, 0.4), owner.global_position, owner.forward()))

func debuff_regen() -> float:
	var count := 0
	for id in owner.status.statuses:
		if StatusRules.is_debuff(id) and id != &"badly_hurt":
			count += 1
	return owner.max_hp() * minf(0.005, owner.stats.flag(&"debuff_regen")) * count

func return_damage(attacker: Node, req: DamageRequest, result: DamageResult) -> void:
	if result.evaded or result.total <= 0 or not attacker is Actor or attacker == owner or not attacker.alive:
		return
	if req.kind not in [DamageRequest.Kind.ATTACK, DamageRequest.Kind.SPELL] or req.tags.has(&"proc") or req.tags.has(&"thorns"):
		return
	var amount := owner.stats.flag(&"damage_return")
	if amount <= 0.0:
		return
	var reflected := DamageRequest.new()
	reflected.kind = DamageRequest.Kind.SPELL
	reflected.use_weapon = false
	# Fixed returned damage; no offensive scaling, crits, leech or recursive procs.
	reflected.base_min = result.total * minf(0.40, amount)
	reflected.base_max = reflected.base_min
	reflected.can_crit = false
	reflected.evadable = false
	reflected.blockable = false
	reflected.tags[&"proc"] = true
	reflected.label = "Damage Return"
	attacker.receive_hit(reflected, owner, attacker.center())

func refund(skill: SkillDef, paid: float) -> void:
	var fraction := owner.stats.flag(&"arcane_arts")
	if skill.kind == DamageRequest.Kind.SPELL and paid > 0.0 and fraction > 0.0 and owner.rng.randf() < 0.30:
		owner.restore_mana(paid * minf(0.50, fraction))

static func split_count(fraction: float) -> int:
	return clampi(3 + floori((fraction - 0.50) / 0.25 * 5.0 + 0.0001), 3, 8)

func split_shot(original: Projectile) -> void:
	var fraction := minf(0.75, owner.stats.flag(&"split_shot"))
	if fraction <= 0.0 or owner.rng.randf() >= 0.30:
		return
	var count := split_count(fraction)
	var shared_hits := {}
	original.volley_hits = shared_hits
	original.request = original.request.clone()
	original.request.skill_mult *= fraction
	# Keep the aimed arrow; additional arrows alternate left and right.
	for i in range(1, count):
		var angle := deg_to_rad(6.0 * ceilf(float(i) / 2.0) * (1.0 if i % 2 else -1.0))
		var p := Projectile.spawn(original.get_parent(), original.global_position, original.velocity.normalized().rotated(Vector3.UP, angle), original.velocity.length(), original.request.clone(), owner, original.target_mask, original.element, original.projectile_look)
		p.volley_hits = shared_hits
		p.max_range = original.max_range
		p.pierce = original.pierce
		p.radius = original.radius
		p.hit_sound = original.hit_sound
		p.on_hit = original.on_hit
