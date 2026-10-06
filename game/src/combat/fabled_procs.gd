class_name FabledProcs
## bh-039: the signature strikes of the Fabled Arms (DataFabled). A held Fabled arm may answer a hit (not a proc's own
## hit) with its strike: its tier sets the chance, the rest between strikes and the strength (a share of the hit);
## each kind sets its shape, its extra effect and its animation (FabledFx). Main and off hand roll separately.
## Lambdas here are written in static functions (no owner object) and check every node they captured before use.

## kind: mult (share of the tier's strength), radius (m)
const KINDS := {
	&"burst": {"mult": 1.0, "radius": 3.0}, &"wave": {"mult": 0.9, "radius": 9.0}, &"spikes": {"mult": 1.0, "radius": 3.2},
	&"orbs": {"mult": 0.6, "radius": 9.0}, &"chain": {"mult": 0.7, "radius": 8.0}, &"meteor": {"mult": 1.3, "radius": 3.2},
	&"vortex": {"mult": 0.9, "radius": 3.5}, &"blades": {"mult": 1.1, "radius": 3.2}, &"comet": {"mult": 1.25, "radius": 3.0},
	&"echo": {"mult": 0.8, "radius": 0.0},
	# Divine
	&"seraph_wings": {"mult": 1.1, "radius": 4.5}, &"halo_descent": {"mult": 1.4, "radius": 3.0}, &"sun_lance": {"mult": 1.5, "radius": 3.2},
	&"choir_bells": {"mult": 0.9, "radius": 6.0}, &"sword_rain": {"mult": 1.3, "radius": 4.0}, &"feather_storm": {"mult": 1.0, "radius": 4.0},
	&"dawn_pillar": {"mult": 1.4, "radius": 3.0}, &"sanctuary": {"mult": 0.5, "radius": 4.0}, &"aurora_veil": {"mult": 1.1, "radius": 12.0},
	&"starlit_scales": {"mult": 1.2, "radius": 2.5},
	# Primordial
	&"magma_fissure": {"mult": 1.3, "radius": 1.6}, &"world_serpent": {"mult": 1.5, "radius": 3.5}, &"titan_fist": {"mult": 1.6, "radius": 2.8},
	&"primeval_roots": {"mult": 1.1, "radius": 4.0}, &"meteor_swarm": {"mult": 0.8, "radius": 5.0}, &"tidal_maw": {"mult": 1.4, "radius": 4.5},
	&"obsidian_shards": {"mult": 1.3, "radius": 4.0}, &"ashen_tempest": {"mult": 0.45, "radius": 2.6}, &"dragon_breath": {"mult": 1.4, "radius": 9.0},
	&"genesis_bloom": {"mult": 1.5, "radius": 4.0},
}

static func kind_mult(kind: StringName) -> float:
	return float(KINDS.get(kind, {"mult": 1.0}).mult)

static func on_hit(p: Player, target: Actor, res: DamageResult) -> void:
	if p == null or p.hero == null or not is_instance_valid(target) or res == null or res.total <= 0.0:
		return
	var ready: Dictionary = p.get_meta(&"fabled_ready", {})
	for slot in [&"main_weapon", &"sub_weapon"]:
		var it := p.hero.equipment.get_item(slot)
		if it == null or not DataFabled.is_fabled(it.base):
			continue
		var r := DataFabled.row(it.base.id)
		var t: Dictionary = DataFabled.TIER[int(r[2])]
		var key := String(it.base.id) + String(slot)
		if p._time < float(ready.get(key, 0.0)) or p.rng.randf() >= float(t.chance):
			continue
		ready[key] = p._time + float(t.cd)
		strike(p, it.base.id, target, res.total * float(t.power) * kind_mult(StringName(r[5])))
	p.set_meta(&"fabled_ready", ready)

## Run one signature strike of `id` on `target` for `amount` (also used by the Debug console and the capture tools).
static func strike(p: Player, id: StringName, target: Actor, amount: float) -> void:
	var r := DataFabled.row(id)
	if r.is_empty() or not is_instance_valid(p) or not is_instance_valid(target):
		return
	var kind: StringName = r[5]
	var el := int(r[4])
	var cc := DataFabled.colors(id)
	var c1: Color = cc[0]
	var c2: Color = cc[1]
	var rad := float(KINDS.get(kind, {"radius": 3.0}).radius)
	var at := target.global_position
	var from := p.global_position
	var dir := (at - from).slide(Vector3.UP).normalized()
	if dir.length_squared() < 0.01:
		dir = p.forward()
	var label := String(r[8])
	FabledFx.play(kind, p, target, at, dir, c1, c2, rad)
	match kind:
		&"wave", &"aurora_veil", &"dragon_breath":
			var width := 3.0 if kind == &"dragon_breath" else 2.2
			for a: Actor in CombatQuery.actors_in_line(p.get_world_3d(), from, dir, rad, width, BH.LAYER_ENEMY):
				_hit(p, a, amount, el, label)
				if kind == &"dragon_breath" and is_instance_valid(a) and a.alive:
					a.status.apply(&"burning", -1.0, 0.0, maxf(1.0, amount * 0.15), Elements.FIRE)
		&"magma_fissure":
			var length := from.distance_to(at) + 2.0
			for a: Actor in CombatQuery.actors_in_line(p.get_world_3d(), from, dir, length, rad * 2.0, BH.LAYER_ENEMY):
				_later(p, 0.25, func() -> void:
					_hit(p, a, amount, el, label)
					if is_instance_valid(a) and a.alive:
						a.status.apply(&"burning", -1.0, 0.0, maxf(1.0, amount * 0.2), Elements.FIRE))
		&"chain":
			var n := 0
			for a: Actor in CombatQuery.actors_in_radius(p.get_world_3d(), at, rad, BH.LAYER_ENEMY):
				if n >= 5:
					break
				n += 1
				_hit(p, a, amount, el, label)
		&"orbs":
			var n := 0
			for a: Actor in CombatQuery.actors_in_radius(p.get_world_3d(), at, rad, BH.LAYER_ENEMY):
				if n >= 3:
					break
				n += 1
				_later(p, 0.35 + 0.08 * n, func() -> void: _hit(p, a, amount, el, label))
		&"echo":
			_later(p, 0.4, func() -> void:
				_hit(p, target, amount, el, label)
				if is_instance_valid(p):
					for k in p.cooldowns.keys():
						p.cooldowns[k] = maxf(0.0, p.cooldowns[k] - 0.2)
					p.cooldowns_changed.emit())
		&"seraph_wings":
			for a: Actor in CombatQuery.actors_in_radius(p.get_world_3d(), from, rad, BH.LAYER_ENEMY):
				_later(p, 0.3, func() -> void: _hit(p, a, amount, el, label))
			p.heal(p.max_hp() * 0.04)
		&"feather_storm", &"genesis_bloom":
			_area(p, at, rad, amount, el, label, 0.35)
			p.heal(p.max_hp() * 0.03)
		&"sanctuary":
			for i in 5:
				_later(p, 0.2 + 0.6 * i, func() -> void:
					_area(p, at, rad, amount, el, label, 0.0)
					if is_instance_valid(p) and p.alive and p.global_position.distance_to(at) <= rad + 0.5:
						p.heal(p.max_hp() * 0.015))
		&"ashen_tempest":
			for i in 6:
				_later(p, 0.15 + 0.4 * i, func() -> void:
					_area(p, at + dir * 0.6 * i, rad, amount, el, label, 0.0, &"burning"))
		&"starlit_scales":
			var missing := 1.0 - (target.hp / maxf(1.0, target.max_hp())) if target.has_method(&"max_hp") else 0.5
			_later(p, 0.55, func() -> void: _area(p, at, rad, amount * (1.0 + 2.0 * clampf(missing, 0.0, 1.0)), el, label, 0.0))
		&"choir_bells":
			for i in 3:
				_later(p, 0.15 + 0.3 * i, func() -> void: _area(p, from, rad * (0.45 + 0.27 * i), amount / 3.0, el, label, 0.0, &"stunned" if i == 2 else &""))
		&"primeval_roots":
			_area(p, at, rad, amount, el, label, 0.3, &"rooted")
		&"vortex", &"tidal_maw":
			_area(p, at, rad, amount, el, label, 0.45 if kind == &"tidal_maw" else 0.6, &"slowed")
		&"spikes", &"obsidian_shards":
			_area(p, at, rad, amount, el, label, 0.2, &"slowed" if el == Elements.ICE else &"")
		&"titan_fist":
			_area(p, at, rad, amount, el, label, 0.3, &"stunned")
		&"meteor_swarm":
			for i in 5:
				var off := Vector3(p.rng.randf_range(-1, 1), 0, p.rng.randf_range(-1, 1)).normalized() * p.rng.randf_range(0.0, rad * 0.7)
				_later(p, 0.55 + 0.18 * i, func() -> void: _area(p, at + off, 2.4, amount, el, label, 0.0, &"burning"))
		&"meteor", &"comet", &"sun_lance", &"halo_descent", &"dawn_pillar", &"world_serpent", &"sword_rain", &"blades":
			var delay: float = {&"meteor": 0.5, &"comet": 0.4, &"sun_lance": 0.3, &"halo_descent": 0.55, &"dawn_pillar": 0.5, &"world_serpent": 0.8,
				&"sword_rain": 0.3, &"blades": 0.3}.get(kind, 0.4)
			_area(p, at, rad, amount, el, label, float(delay), &"burning" if el == Elements.FIRE else &"")
		_:
			_area(p, at, rad, amount, el, label, 0.0)

static func _area(p: Player, at: Vector3, rad: float, amount: float, el: int, label: String, delay: float, status := &"") -> void:
	var fn := func() -> void:
		if not is_instance_valid(p) or not p.is_inside_tree():
			return
		for a: Actor in CombatQuery.actors_in_radius(p.get_world_3d(), at, rad, BH.LAYER_ENEMY):
			_hit(p, a, amount, el, label)
			if status != &"" and is_instance_valid(a) and a.alive:
				match status:
					&"burning": a.status.apply(&"burning", -1.0, 0.0, maxf(1.0, amount * 0.15), Elements.FIRE)
					&"stunned": a.status.apply(&"stunned", 0.8)
					&"rooted": a.status.apply(&"rooted", 1.5)
					&"slowed": a.status.apply(&"slowed", 2.0, 0.35)
	if delay <= 0.0:
		fn.call()
	else:
		_later(p, delay, fn)

static func _later(p: Player, t: float, fn: Callable) -> void:
	if not is_instance_valid(p) or not p.is_inside_tree():
		return
	p.get_tree().create_timer(t, false).timeout.connect(fn)

static func _hit(p: Player, a: Actor, amount: float, el: int, label: String) -> void:
	if not is_instance_valid(p) or not is_instance_valid(a) or not a.alive:
		return
	p._asc_hit(a, amount, {el: 1.0}, label)
