class_name ClassSpells
## Gravity and dark spells share the same damage, status and visibility rules as other skills.

static func cast(runner: SkillRunner, skill: SkillDef, p: Dictionary, aim: Vector3) -> void:
	var caster := runner.caster
	var world := caster.get_world_3d()
	var req := runner.make_request(skill, p)
	var color := Color(0.65, 0.3, 0.9)
	match skill.behavior:
		&"gravity_pull":
			var at := runner._ground_target(aim, float(p.range))
			for target: Actor in CombatQuery.actors_in_radius(world, at, float(p.radius), runner.mask()):
				if CombatQuery.blocked(world, caster.center(), target.center()) or CombatQuery.blocked(world, at + Vector3.UP, target.center()):
					continue
				target.ensure_stats()
				var offset := (target.global_position - at).slide(Vector3.UP)
				var distance := maxf(0.0, offset.length() - target.body_radius - 0.5) * (1.0 - clampf(target.stats.get_stat(&"knockback_res"), 0.0, 1.0))
				# Sweep the actual body so instant movement cannot cross walls or terrain.
				target.move_and_collide(-offset.normalized() * distance)
				runner._hit(skill, target, target.receive_hit(req.clone(), caster, target.center()))
			FX.spawn(VFXLib.ring_wave(color, float(p.radius), 0.4, 0.8), at)
			FX.spawn(VFXLib.light_pillar(color, 4.0, 0.6, 0.4), at)
		&"spike_tentacle":
			var dir := (aim - caster.global_position).slide(Vector3.UP).normalized()
			for target: Actor in CombatQuery.actors_in_line(world, caster.global_position, dir, float(p.length), float(p.width), runner.mask()):
				if CombatQuery.blocked(world, caster.center(), target.center()):
					continue
				var result := target.receive_hit(req.clone(), caster, target.center())
				if not result.evaded and target.alive:
					target.status.apply(&"stunned", minf(1.6, float(p.stun_duration)))
				runner._hit(skill, target, result)
			for i in 8:
				var pos := CombatQuery.ground_at(world, caster.global_position + dir * float(p.length) * float(i + 1) / 8.0)
				if not CombatQuery.blocked(world, caster.center(), pos + Vector3.UP):
					FX.spawn(VFXLib.light_pillar(color, 2.4, 0.22, 0.45), pos)
		&"mana_siphon":
			for target: Actor in CombatQuery.actors_in_radius(world, caster.global_position, float(p.radius), runner.mask()):
				if CombatQuery.blocked(world, caster.center(), target.center()):
					continue
				var drained := minf(target.mana, float(p.drain))
				if drained > 0.0 and target.spend_mana(drained):
					caster.restore_mana(drained)
					FX.spawn(VFXLib.lightning_bolt(target.center(), caster.center(), color), Vector3.ZERO)
			FX.spawn(VFXLib.ring_wave(color, float(p.radius), 0.5, 0.6), caster.global_position)
		&"dark_arts":
			var target := runner._step_target(aim, float(p.range))
			if target != null:
				var result := target.receive_hit(req, caster, target.center())
				if not result.evaded and target.alive:
					var curses := [&"weakened", &"armor_broken", &"silenced", &"bloodcurse"]
					var curse: StringName = curses[caster.rng.randi_range(0, curses.size() - 1)]
					target.status.apply(curse, float(p.duration), 0.35 if curse == &"bloodcurse" else 0.0)
				runner._hit(skill, target, result)
				FX.spawn(VFXLib.hit_burst(target.center(), Elements.DARK, 0.8, false), target.center())
	Audio.play_at(skill.sound_cast, caster.global_position)
