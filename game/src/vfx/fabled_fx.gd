class_name FabledFx
## bh-039: the look of the Fabled Arms (DataFabled).
##   play()  the animation of a signature strike (FabledProcs): bursts, comets, falling halos, wings sweeping shut, rings
##           of holy swords, a serpent of fire coiling up, a titan's fist from the ground, lava petals opening ...
##   held()  the moving light on the weapon in hand: a surface shader of the arm's own mode and colours, plus its
##           moving pieces (a turning halo, slow wings, orbiting stones, a coiling serpent, drifting feathers ...).
## Every node here frees itself; nothing stores a callable bound to a node that may die first.

# ---- strikes -------------------------------------------------------------------------------------------------------

static func play(kind: StringName, p: Node3D, target: Node3D, at: Vector3, dir: Vector3, c1: Color, c2: Color, rad: float) -> void:
	var up := Vector3.UP
	match kind:
		&"burst":
			FX.spawn(VFXLib.ring_wave(c1, rad, 0.45, 0.5), at + up * 0.05)
			FX.spawn(VFXLib.impact_flash(c2, 2.6, 0.22, 8), at + up)
			FX.spawn(VFXLib.particles(c1, 26, 0.7, true, 0.12, 6.0, 70.0, Vector3(0, -4, 0), 0.3), at + up * 0.6)
			FX.spawn(VFXLib.light_flash(c1, 5.0, 6.0, 0.3), at + up)
		&"wave":
			_travel(VFXLib.slash_arc(c1, 2.2, 160.0, 1.0, 0.7, 0.6), p.global_position + up * 0.2, dir, rad, 0.5)
			FX.spawn(VFXLib.particles(c2, 20, 0.6, true, 0.1, 7.0, 25.0, Vector3.ZERO, 0.4), p.global_position + up + dir)
		&"spikes", &"obsidian_shards":
			var n := 10 if kind == &"spikes" else 12
			for i in n:
				var a := TAU * i / n
				var off := Vector3(cos(a), 0, sin(a)) * rad * (0.55 if kind == &"spikes" else 0.3)
				var sp := _spike(c1 if kind == &"spikes" else Color(0.12, 0.08, 0.14), c2, 1.1 + 0.4 * (i % 2), 0.16)
				FX.spawn(sp, at + off)
				if kind == &"obsidian_shards":
					sp.rotation = Vector3(0, -a, 0)
					var tw := sp.create_tween()
					tw.tween_property(sp, "rotation:z", -0.9, 0.18)
					tw.parallel().tween_property(sp, "position", sp.position + off * 2.0, 0.18)
			FX.spawn(VFXLib.ring_wave(c1, rad, 0.4, 0.3), at + up * 0.05)
		&"orbs":
			for i in 3:
				var o := VFXLib.orb(c1, 0.18, i == 0)
				FX.spawn(o, p.global_position + up * 1.4)
				var to := at + Vector3(randf_range(-2, 2), 1.0, randf_range(-2, 2))
				var tw := o.create_tween()
				tw.tween_property(o, "global_position", p.global_position + up * 2.6 + Vector3(randf_range(-1.5, 1.5), 0, randf_range(-1.5, 1.5)), 0.2)
				tw.tween_property(o, "global_position", to, 0.25 + 0.08 * i).set_ease(Tween.EASE_IN)
				tw.tween_callback(o.queue_free)
		&"chain":
			var prev := p.global_position + up * 1.4
			var n := 0
			for a in CombatQuery.actors_in_radius(p.get_world_3d(), at, rad, BH.LAYER_ENEMY):
				if n >= 5:
					break
				n += 1
				var to: Vector3 = (a as Actor).center()
				FX.spawn(VFXLib.lightning_bolt(prev, to, c1, 0.25, 0.1), Vector3.ZERO)
				FX.spawn(VFXLib.impact_flash(c2, 1.4, 0.15, 6), to)
				prev = to
		&"meteor", &"comet", &"meteor_swarm":
			var count := 5 if kind == &"meteor_swarm" else 1
			for i in count:
				var off := Vector3.ZERO if count == 1 else Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized() * randf_range(0.5, rad * 0.7)
				_fall(at + off, c1, c2, 0.5 + 0.18 * i if kind != &"comet" else 0.4, kind == &"comet")
		&"vortex", &"tidal_maw":
			var disc := _disc(4 if kind == &"vortex" else 5, c1, c2, rad * 2.0, 1.4)
			FX.spawn(disc, at + up * 0.06)
			FX.spawn(VFXLib.particles(c2, 30, 1.2, true, 0.1, 2.5, 180.0, Vector3(0, 1, 0), rad * 0.8), at + up * 0.3)
			if kind == &"tidal_maw":
				var dome := VFXLib.shield_dome(c1, rad, 0.8)
				FX.spawn(dome, at)
				var tw := dome.create_tween()
				tw.tween_property(dome, "scale", Vector3(1.2, 0.05, 1.2), 0.45).set_delay(0.25).set_ease(Tween.EASE_IN)
				_after(dome, 0.45, func() -> void: FX.spawn(VFXLib.ring_wave(c2, rad * 1.3, 0.5, 0.6), at + up * 0.05))
		&"blades", &"sword_rain":
			var n := 5 if kind == &"blades" else 8
			for i in n:
				var a := TAU * i / n
				var sw := VFXLib.light_sword(c1, 2.4 if kind == &"blades" else 3.4, 0.14 + 0.03 * i, 0.4)
				sw.scale = Vector3.ONE * (0.45 if kind == &"blades" else 0.6)
				FX.spawn(sw, at + Vector3(cos(a), 0, sin(a)) * rad * 0.6)
			FX.spawn(VFXLib.ring_wave(c2, rad, 0.5, 0.4), at + up * 0.05)
		&"echo":
			FX.spawn(_disc(3, c1, c2, 2.6, 0.7), at + up * 0.06)
			FX.spawn(VFXLib.ring_wave(c1, 1.8, 0.5, 0.3), at + up)
			_after(p, 0.4, func() -> void: FX.spawn(VFXLib.impact_flash(c2, 2.2, 0.2, 6), at + up))
		&"seraph_wings":
			for side in [-1.0, 1.0]:
				var w := _wing(c1, c2, side)
				FX.spawn(w, p.global_position + up * 1.2)
				w.rotation.y = atan2(dir.x, dir.z) + side * 1.9
				var tw := w.create_tween()
				tw.tween_property(w, "rotation:y", atan2(dir.x, dir.z) + side * 0.15, 0.32).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
			_after(p, 0.32, func() -> void:
				FX.spawn(VFXLib.ring_wave(c1, 4.5, 0.5, 0.6), p.global_position + up * 0.05)
				FX.spawn(VFXLib.particles(c2, 40, 1.2, true, 0.1, 5.0, 180.0, Vector3(0, -1.5, 0), 1.0), p.global_position + up * 1.4))
		&"halo_descent":
			var halo := _halo(c1, 1.4)
			FX.spawn(halo, at + up * 5.0)
			var tw := halo.create_tween()
			tw.tween_property(halo, "position:y", at.y + 0.3, 0.55).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
			tw.tween_callback(func() -> void:
				FX.spawn(VFXLib.light_pillar(c1, 8.0, 1.6, 0.8), at)
				FX.spawn(VFXLib.ring_wave(c2, 3.2, 0.5, 0.6), at + up * 0.05))
			tw.tween_property(halo, "scale", Vector3.ONE * 2.5, 0.3)
			tw.tween_callback(halo.queue_free)
		&"sun_lance":
			var lance := VFXLib.light_sword(c1, 5.0, 0.28, 0.3)
			FX.spawn(lance, at)
			lance.rotation = Vector3(0.0, atan2(dir.x, dir.z), -0.45)
			_after(lance, 0.3, func() -> void:
				FX.spawn(_disc(2, c1, c2, 7.0, 0.8), at + up * 0.06)
				FX.spawn(VFXLib.light_flash(c1, 9.0, 10.0, 0.5), at + up))
		&"choir_bells":
			for i in 3:
				_after(p, 0.15 + 0.3 * i, func() -> void:
					FX.spawn(_disc(1, c1, c2, 3.4 + 2.2 * i, 0.6), p.global_position + up * (0.3 + 0.5 * i))
					FX.spawn(VFXLib.ring_wave(c2, 2.7 + 1.6 * i, 0.4, 0.3), p.global_position + up * 0.05))
		&"feather_storm":
			FX.spawn(_spiral(c1, c2, rad, 2.2, 28), at)
			FX.spawn(VFXLib.particles(c2, 34, 1.6, true, 0.14, 3.0, 180.0, Vector3(0, -1.0, 0), rad * 0.7), at + up * 2.0)
		&"dawn_pillar":
			var sun := _disc(2, c1, c2, 1.0, 1.3)
			FX.spawn(sun, at + up * 0.06)
			var tw := sun.create_tween()
			tw.tween_property(sun, "scale", Vector3.ONE * 6.0, 0.5).set_ease(Tween.EASE_OUT)
			_after(sun, 0.5, func() -> void:
				FX.spawn(VFXLib.light_pillar(c1, 11.0, 2.2, 0.9), at)
				FX.spawn(VFXLib.light_flash(c1, 9.0, 10.0, 0.5), at + up * 2.0))
		&"sanctuary":
			FX.spawn(_disc(0, c1, c2, rad * 2.0, 3.2), at + up * 0.06)
			FX.spawn(VFXLib.beam_flash(c2, 3.0, rad, 3.2), at)
		&"aurora_veil":
			var veil := _curtain(c1, c2)
			FX.spawn(veil, p.global_position)
			veil.rotation.y = atan2(dir.x, dir.z)
			var tw := veil.create_tween()
			tw.tween_property(veil, "global_position", p.global_position + dir * rad, 0.8)
		&"starlit_scales":
			var sc := _scales(c1)
			FX.spawn(sc, at + up * 2.6)
			var tw := sc.create_tween()
			tw.tween_property(sc, "rotation:z", 0.45, 0.35).set_trans(Tween.TRANS_ELASTIC)
			_after(sc, 0.55, func() -> void:
				FX.spawn(VFXLib.beam_flash(c1, 9.0, 0.7, 0.6), at)
				FX.spawn(VFXLib.impact_flash(c2, 3.0, 0.25, 8), at + up))
		&"magma_fissure":
			var length := p.global_position.distance_to(at) + 2.0
			for i in int(length / 0.8):
				var pt := p.global_position + dir * (0.8 * i + 0.6)
				_after(p, 0.03 * i, func() -> void:
					FX.spawn(VFXLib.ground_crack(c1, 0.9, 1.4), pt + up * 0.03)
					FX.spawn(VFXLib.particles(c1, 10, 0.8, true, 0.12, 7.0, 25.0, Vector3(0, -12, 0), 0.25), pt + up * 0.1))
			Events.camera_shake.emit(0.2)
		&"world_serpent":
			FX.spawn(_serpent(c1, c2, rad * 0.45, 4.0), at)
			_after(p, 0.8, func() -> void:
				FX.spawn(VFXLib.ring_wave(c1, rad, 0.5, 0.6), at + up * 0.05)
				FX.spawn(VFXLib.particles(c2, 40, 0.9, true, 0.14, 8.0, 60.0, Vector3(0, -9, 0), 0.6), at + up * 2.0))
		&"titan_fist":
			var fist := _fist(c1)
			FX.spawn(fist, at + up * -1.6)
			var tw := fist.create_tween()
			tw.tween_property(fist, "position:y", at.y + 0.6, 0.18).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
			tw.tween_interval(0.5)
			tw.tween_property(fist, "position:y", at.y - 2.0, 0.4)
			tw.tween_callback(fist.queue_free)
			FX.spawn(VFXLib.heavy_impact(c1, 1.4), at)
			Events.camera_shake.emit(0.35)
		&"primeval_roots":
			for i in 7:
				var a := TAU * i / 7.0
				var root := _root(c1, c2)
				FX.spawn(root, at + Vector3(cos(a), 0, sin(a)) * rad * 0.5)
				root.rotation = Vector3(randf_range(-0.4, 0.4), a, randf_range(-0.3, 0.3))
			FX.spawn(VFXLib.particles(c2, 24, 1.0, true, 0.1, 3.0, 90.0, Vector3(0, -2, 0), rad * 0.6), at + up * 0.4)
		&"ashen_tempest":
			var t := _spiral(c1, Color(0.3, 0.28, 0.27), 1.4, 3.4, 30)
			FX.spawn(t, at)
			var tw := t.create_tween()
			tw.tween_property(t, "global_position", at + dir * 3.0, 2.4)
		&"dragon_breath":
			for i in 7:
				var pt := p.global_position + up * 1.3 + dir * (1.0 + 1.2 * i)
				_after(p, 0.04 * i, func() -> void:
					FX.spawn(VFXLib.particles(c1 if i % 2 else c2, 16, 0.6, true, 0.25 + 0.06 * i, 3.0, 60.0, Vector3(0, 1.5, 0), 0.2 + 0.18 * i), pt)
					FX.spawn(VFXLib.light_flash(c1, 3.0, 4.0, 0.2), pt))
		&"genesis_bloom":
			var fl := _disc(6, c1, c2, rad * 2.0, 1.2)
			FX.spawn(fl, at + up * 0.07)
			_after(fl, 0.35, func() -> void:
				FX.spawn(VFXLib.ring_wave(c1, rad, 0.5, 0.7), at + up * 0.05)
				FX.spawn(VFXLib.particles(c2, 40, 1.0, true, 0.14, 7.0, 50.0, Vector3(0, -8, 0), rad * 0.5), at + up * 0.3))
		_:
			FX.spawn(VFXLib.ring_wave(c1, rad, 0.45, 0.4), at + up * 0.05)

## Runs `fn` after `t` seconds while `holder` lives (a static lambda: no owner of its own).
static func _after(holder: Node, t: float, fn: Callable) -> void:
	if not is_instance_valid(holder) or not holder.is_inside_tree():
		return
	holder.get_tree().create_timer(t, false).timeout.connect(fn)

static func _travel(n: Node3D, from: Vector3, dir: Vector3, dist: float, t: float) -> void:
	FX.spawn(n, from)
	n.rotation.y = atan2(dir.x, dir.z)
	var tw := n.create_tween()
	tw.tween_property(n, "global_position", from + dir * dist, t)
	tw.tween_callback(n.queue_free)

static func _fall(at: Vector3, c1: Color, c2: Color, t: float, comet: bool) -> void:
	var o := VFXLib.orb(c1, 0.45 if not comet else 0.3, true)
	var start := at + Vector3(4.0 if comet else 0.6, 11.0, 2.0 if comet else 0.4)
	FX.spawn(o, start)
	var trail := VFXLib.particles(c2, 30, 0.5, false, 0.22, 0.5, 30.0, Vector3.ZERO, 0.15)
	o.add_child(trail)
	var tw := o.create_tween()
	tw.tween_property(o, "global_position", at + Vector3.UP * 0.3, t).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		FX.spawn(VFXLib.heavy_impact(c1, 1.0), at)
		FX.spawn(VFXLib.ring_wave(c1, 3.0, 0.45, 0.5), at + Vector3.UP * 0.05)
		FX.spawn(VFXLib.light_flash(c1, 7.0, 8.0, 0.35), at + Vector3.UP)
		Events.camera_shake.emit(0.15))
	tw.tween_callback(o.queue_free)

static func _mat(c: Color, energy := 2.5) -> ShaderMaterial:
	return VFXLib.glow_material(c, energy)

static func _spike(c1: Color, c2: Color, h: float, r: float) -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var pm := PrismMesh.new()
	pm.size = Vector3(r * 2.0, h, r * 2.0)
	mi.mesh = pm
	mi.material_override = _mat(c1.lerp(c2, 0.3), 1.6)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position.y = -h * 0.5
	root.add_child(mi)
	var tw := root.create_tween()
	tw.tween_property(mi, "position:y", h * 0.5, 0.12).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_interval(0.6)
	tw.tween_property(mi, "position:y", -h * 0.6, 0.3)
	tw.tween_callback(root.queue_free)
	return root

static func _halo(c: Color, r: float) -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = r * 0.9
	tm.outer_radius = r
	tm.rings = 32
	mi.mesh = tm
	mi.material_override = _mat(c, 3.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)
	root.add_child(FxSpinner.make(mi, Vector3.UP, 2.5))
	return root

static func _wing(c1: Color, c2: Color, side: float, keep := false) -> Node3D:
	var root := Node3D.new()
	for i in 6:
		var f := MeshInstance3D.new()
		var q := PrismMesh.new()
		q.size = Vector3(0.22, 2.2 - i * 0.22, 0.04)
		f.mesh = q
		f.material_override = _mat(c1.lerp(c2, i / 6.0), 2.2)
		f.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		f.position = Vector3(side * (0.3 + i * 0.32), 0.2 + i * 0.1, 0)
		f.rotation.z = side * (-0.6 - i * 0.18)
		root.add_child(f)
	if keep:
		return root
	VFXLib._autofree(root, 1.0)
	var tw := root.create_tween()
	tw.tween_interval(0.45)
	tw.tween_property(root, "scale", Vector3.ONE * 0.01, 0.35)
	return root

static func _spiral(c1: Color, c2: Color, r: float, h: float, n: int) -> Node3D:
	var root := Node3D.new()
	var spin := Node3D.new()
	root.add_child(spin)
	for i in n:
		var u := float(i) / n
		var o := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(0.12, 0.34)
		o.mesh = q
		o.material_override = _mat(c1 if i % 3 else c2, 2.4)
		o.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := u * TAU * 3.0
		o.position = Vector3(cos(a) * r * (0.4 + 0.6 * u), u * h, sin(a) * r * (0.4 + 0.6 * u))
		o.rotation = Vector3(0.4, -a, 0.6)
		spin.add_child(o)
	root.add_child(FxSpinner.make(spin, Vector3.UP, 6.0))
	VFXLib._autofree(root, 2.6)
	return root

static func _serpent(c1: Color, c2: Color, r: float, h: float) -> Node3D:
	var root := Node3D.new()
	var body := Node3D.new()
	root.add_child(body)
	for i in 22:
		var s := MeshInstance3D.new()
		var sm := SphereMesh.new()
		var k := 1.0 - i / 26.0
		sm.radius = 0.2 * k
		sm.height = 0.4 * k
		s.mesh = sm
		s.material_override = _mat(c1.lerp(c2, i / 22.0), 2.6)
		s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var a := i * 0.55
		s.position = Vector3(cos(a) * r, h - i * 0.17, sin(a) * r)
		body.add_child(s)
	body.position.y = -h
	var tw := root.create_tween()
	tw.tween_property(body, "position:y", 0.0, 0.7).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(body, "rotation:y", TAU * 1.5, 0.8)
	tw.tween_property(body, "scale", Vector3(2.0, 0.2, 2.0), 0.15)
	tw.tween_callback(root.queue_free)
	return root

static func _fist(c: Color) -> Node3D:
	var root := Node3D.new()
	var stone := StandardMaterial3D.new()
	stone.albedo_color = Color(0.36, 0.32, 0.29)
	stone.roughness = 0.9
	stone.emission_enabled = true
	stone.emission = c * 0.5
	var arm := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.45
	cm.bottom_radius = 0.6
	cm.height = 1.8
	arm.mesh = cm
	arm.material_override = stone
	root.add_child(arm)
	var hand := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.3, 0.9, 1.0)
	hand.mesh = bm
	hand.position.y = 1.2
	hand.material_override = stone
	root.add_child(hand)
	for i in 4:
		var k := MeshInstance3D.new()
		var km := BoxMesh.new()
		km.size = Vector3(0.26, 0.3, 0.3)
		k.mesh = km
		k.position = Vector3(-0.45 + 0.3 * i, 1.75, 0.2)
		k.material_override = stone
		root.add_child(k)
	return root

static func _root(c1: Color, c2: Color) -> Node3D:
	var root := Node3D.new()
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.22, 0.15, 0.08)
	m.emission_enabled = true
	m.emission = c1 * 0.4
	for i in 4:
		var seg := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.06 * (1.0 - i * 0.22)
		cm.bottom_radius = 0.12 * (1.0 - i * 0.2)
		cm.height = 0.6
		seg.mesh = cm
		seg.material_override = m
		seg.position = Vector3(0.12 * i, 0.3 + 0.5 * i, 0)
		seg.rotation.z = -0.25 * i
		root.add_child(seg)
	var thorn := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.08
	sm.height = 0.16
	thorn.mesh = sm
	thorn.material_override = _mat(c2, 2.5)
	thorn.position = Vector3(0.4, 2.0, 0)
	root.add_child(thorn)
	root.scale = Vector3(1, 0.01, 1)
	var tw := root.create_tween()
	tw.tween_property(root, "scale", Vector3.ONE, 0.25).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_interval(1.2)
	tw.tween_property(root, "scale", Vector3(1, 0.01, 1), 0.3)
	tw.tween_callback(root.queue_free)
	return root

static func _scales(c: Color) -> Node3D:
	var root := Node3D.new()
	var m := _mat(c, 2.4)
	var beam := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(2.2, 0.08, 0.08)
	beam.mesh = bm
	beam.material_override = m
	root.add_child(beam)
	for sx in [-1.0, 1.0]:
		var pan := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.42
		cm.bottom_radius = 0.2
		cm.height = 0.12
		pan.mesh = cm
		pan.material_override = m
		pan.position = Vector3(sx * 1.05, -0.7, 0)
		root.add_child(pan)
	VFXLib._autofree(root, 1.0)
	return root

static func _curtain(c1: Color, c2: Color) -> Node3D:
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(4.5, 3.2)
	mi.mesh = q
	var sm := ShaderMaterial.new()
	sm.shader = _shader("aurora", AURORA_SHADER)
	sm.set_shader_parameter("c1", c1)
	sm.set_shader_parameter("c2", c2)
	mi.material_override = sm
	mi.position.y = 1.6
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)
	var tw := root.create_tween()
	tw.tween_method(func(v: float) -> void: sm.set_shader_parameter("alpha", v), 1.0, 0.0, 0.5).set_delay(0.5)
	tw.tween_callback(root.queue_free)
	return root

## A flat animated disc (ground sigil): 0 sanctuary, 1 bell ring, 2 sunburst, 3 clock, 4 vortex, 5 tide, 6 lava flower.
static func _disc(mode: int, c1: Color, c2: Color, size: float, life: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2.ONE * size
	mi.mesh = pm
	var sm := ShaderMaterial.new()
	sm.shader = _shader("disc", DISC_SHADER)
	sm.set_shader_parameter("mode", mode)
	sm.set_shader_parameter("c1", c1)
	sm.set_shader_parameter("c2", c2)
	sm.render_priority = -10
	mi.material_override = sm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if life <= 0.0:
		sm.set_shader_parameter("prog", 0.4)     # a held piece: shown for good
		return mi
	var tw := mi.create_tween()
	tw.tween_method(func(v: float) -> void: sm.set_shader_parameter("prog", v), 0.0, 1.0, life)
	tw.tween_callback(mi.queue_free)
	return mi

static var _shaders := {}

static func _shader(key: String, code: String) -> Shader:
	if not _shaders.has(key):
		var s := Shader.new()
		s.code = code
		_shaders[key] = s
	return _shaders[key]

const DISC_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform int mode = 0;
uniform vec4 c1 : source_color = vec4(1.0);
uniform vec4 c2 : source_color = vec4(1.0);
uniform float prog = 0.0;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float a = atan(p.y, p.x);
	float fade = smoothstep(1.0, 0.9, r) * (1.0 - smoothstep(0.75, 1.0, prog)) * smoothstep(0.0, 0.08, prog);
	vec3 col = vec3(0.0);
	float ring = exp(-pow((r - 0.9) * 30.0, 2.0)) + exp(-pow((r - 0.7) * 40.0, 2.0)) * 0.6;
	if (mode == 0) {
		float tri1 = 0.0;
		for (int i = 0; i < 6; i++) {
			float ang = float(i) * 1.0472 + TIME * 0.3;
			vec2 d = vec2(cos(ang), sin(ang));
			tri1 += smoothstep(0.03, 0.0, abs(dot(p, d) - 0.32)) * step(r, 0.72);
		}
		float runes = step(0.6, hash(floor(vec2((a + TIME * 0.4) * 6.0, 0.0)))) * smoothstep(0.03, 0.0, abs(r - 0.8));
		col = c1.rgb * (ring + tri1 * 0.9 + runes) + c2.rgb * smoothstep(0.5, 0.0, r) * 0.25;
	} else if (mode == 1) {
		float band = exp(-pow((r - 0.85) * 18.0, 2.0));
		float notes = step(0.8, fract(a * 3.0 / 3.14159 + TIME)) * band;
		col = c1.rgb * band * 1.4 + c2.rgb * notes;
	} else if (mode == 2) {
		float rays = pow(0.5 + 0.5 * cos(a * 18.0 - TIME * 1.5), 8.0) * smoothstep(1.0, 0.15, r);
		col = c1.rgb * (rays * 1.3 + ring) + c2.rgb * smoothstep(0.35, 0.0, r);
	} else if (mode == 3) {
		float marks = step(0.92, fract(a / 6.2832 * 12.0 + 0.04)) * step(0.7, r) * step(r, 0.85);
		float hand1 = smoothstep(0.03, 0.0, abs(sin(a - TIME * 5.0))) * step(r, 0.6) * step(0.0, cos(a - TIME * 5.0));
		col = c1.rgb * (ring + marks * 1.5) + c2.rgb * hand1 * 1.4;
	} else if (mode == 4 || mode == 5) {
		float sw = 0.5 + 0.5 * sin(a * 4.0 + r * 14.0 - TIME * (mode == 4 ? 9.0 : 5.0));
		col = mix(c2.rgb, c1.rgb, sw) * pow(sw, 3.0) * smoothstep(1.0, 0.2, r) * 1.3 + c1.rgb * ring;
	} else {
		float open = clamp(prog * 3.0, 0.0, 1.0);
		float petal = abs(cos(a * 3.0)) * 0.9 * open;
		float in_petal = smoothstep(0.03, 0.0, r - petal);
		float vein = smoothstep(0.04, 0.0, abs(fract(a * 6.0 / 6.2832) - 0.5)) * in_petal;
		col = mix(c2.rgb, c1.rgb, r) * in_petal * 1.2 + c1.rgb * vein + vec3(1.0, 0.9, 0.6) * smoothstep(0.15, 0.0, r);
	}
	ALBEDO = col * fade;
}
"""

const AURORA_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform vec4 c1 : source_color = vec4(1.0);
uniform vec4 c2 : source_color = vec4(1.0);
uniform float alpha = 1.0;
void fragment() {
	vec2 uv = UV;
	float w = sin(uv.x * 9.0 + TIME * 3.0) * 0.08 + sin(uv.x * 23.0 - TIME * 2.0) * 0.03;
	float band = smoothstep(0.0, 0.5, uv.y + w) * smoothstep(1.0, 0.4, uv.y + w);
	float streak = 0.6 + 0.4 * sin(uv.x * 60.0 + TIME * 4.0);
	vec3 col = mix(c1.rgb, c2.rgb, uv.y + w) * band * streak * 1.6;
	ALBEDO = col * alpha * smoothstep(0.0, 0.15, uv.x) * smoothstep(1.0, 0.85, uv.x);
}
"""

# ---- held ----------------------------------------------------------------------------------------------------------

## The moving light of a Fabled arm in hand: tier surface light in the arm's colours, plus its moving pieces.
static func held(id: StringName, length: float) -> Node3D:
	var root := Node3D.new()
	root.name = "Fabled"
	var r := DataFabled.row(id)
	if r.is_empty():
		return root
	var cc := DataFabled.colors(id)
	var c1: Color = cc[0]
	var c2: Color = cc[1]
	var parts: Array = r[6]
	for i in range(1, parts.size()):
		var piece := _piece(StringName(parts[i]), c1, c2, length)
		if piece:
			root.add_child(piece)
	return root

static func _piece(kind: StringName, c1: Color, c2: Color, length: float) -> Node3D:
	var tip := Vector3(0, length * 0.92, 0)
	var mid := Vector3(0, length * 0.55, 0)
	match kind:
		&"motes", &"stars", &"frost":
			return _along(c1, length, 8, 0.05, 0.2, Vector3(0, 0.3, 0))
		&"embers":
			return _along(c1, length, 10, 0.05, 0.5, Vector3(0, 1.2, 0))
		&"drips":
			return _along(c1, length, 8, 0.05, 0.1, Vector3(0, -2.5, 0))
		&"smoke":
			return _along(Color(c2.r * 0.4, c2.g * 0.4, c2.b * 0.4, 0.6), length, 8, 0.12, 0.3, Vector3(0, 0.8, 0), false)
		&"leaves", &"feathers":
			return _orbit(c1, c2, 4, 0.16, mid, Vector2(0.05, 0.12), 1.4)
		&"motes_spiral":
			return _orbit(c1, c2, 6, 0.1, mid, Vector2(0.04, 0.04), 3.0)
		&"rocks", &"shards", &"swords", &"scales", &"seed":
			return _orbit(c1, c2, 3 if kind != &"swords" else 4, 0.17, mid, Vector2(0.06, 0.16) if kind in [&"shards", &"swords"] else Vector2(0.07, 0.07), 1.6)
		&"halo":
			var h := _halo(c1, 0.12)
			h.position = tip + Vector3(0, 0.08, 0)
			return h
		&"wings":
			var w := Node3D.new()
			for side in [-1.0, 1.0]:
				var f := _wing(c1, c2, side, true)
				f.scale = Vector3.ONE * 0.12
				w.add_child(f)
			w.position = Vector3(0, 0.1, 0)
			return w
		&"sunrays", &"runering", &"hexsigil", &"clock", &"flower":
			var mode := int({&"sunrays": 2, &"runering": 1, &"hexsigil": 0, &"clock": 3, &"flower": 6}[kind])
			var d := _disc(mode, c1, c2, 0.4, 0.0)
			var n := Node3D.new()
			n.position = tip if kind != &"clock" else Vector3(0, 0.12, 0)
			d.rotation.x = PI * 0.5
			n.add_child(d)
			n.add_child(FxSpinner.make(d, Vector3.UP, 0.8))
			return n
		&"serpent", &"vortex", &"aurora", &"flames", &"arcs":
			return _orbit(c1, c2, 7, 0.13, mid, Vector2(0.05, 0.05), 4.0, true)
	return null

static func _along(c: Color, length: float, amount: int, size: float, vel: float, grav: Vector3, additive := true) -> GPUParticles3D:
	var p := VFXLib.particles(c, amount, 1.2, false, size, vel, 30.0, grav, 0.0, additive)
	var pm := p.process_material as ParticleProcessMaterial
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.03, length * 0.45, 0.03)
	p.position = Vector3(0, length * 0.55, 0)
	return p

## Small glowing pieces circling the blade axis; `helix` makes them climb in a coil (the serpent).
static func _orbit(c1: Color, c2: Color, n: int, r: float, at: Vector3, size: Vector2, speed: float, helix := false) -> Node3D:
	var root := Node3D.new()
	root.position = at
	var ring := Node3D.new()
	root.add_child(ring)
	for i in n:
		var a := TAU * i / n
		var mi := MeshInstance3D.new()
		var pm: PrimitiveMesh = PrismMesh.new() if size.y > size.x else SphereMesh.new()
		if pm is PrismMesh:
			(pm as PrismMesh).size = Vector3(size.x, size.y, size.x * 0.4)
		else:
			(pm as SphereMesh).radius = size.x * 0.5
			(pm as SphereMesh).height = size.x
		mi.mesh = pm
		mi.material_override = _mat(c1 if i % 2 == 0 else c2, 2.2)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.position = Vector3(cos(a) * r, (float(i) / n - 0.5) * 0.5 if helix else 0.0, sin(a) * r)
		ring.add_child(mi)
	root.add_child(FxSpinner.make(ring, Vector3.UP, speed))
	return root

## Turns `target` round `axis` every frame (frees with its parent).
class FxSpinner extends Node:
	var target: Node3D
	var axis := Vector3.UP
	var speed := 1.0
	static func make(t: Node3D, ax: Vector3, sp: float) -> FxSpinner:
		var s := FxSpinner.new()
		s.target = t
		s.axis = ax
		s.speed = sp
		return s
	func _process(delta: float) -> void:
		if is_instance_valid(target):
			target.rotate_object_local(axis, speed * delta)
